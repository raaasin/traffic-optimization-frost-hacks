import gym
from gym import spaces
import numpy as np
import time
import socket
import threading
import json
from stable_baselines3 import PPO
from tqdm import tqdm
import warnings
warnings.filterwarnings("ignore")
client_sockets = []
lock = threading.Lock()

class TrafficSignalEnv(gym.Env):
    def __init__(self):
        super(TrafficSignalEnv, self).__init__()

        self.action_space = spaces.Discrete(5)  # Including the "wait" action

        # Flatten the observation space
        self.observation_space = spaces.Box(low=0, high=101, shape=(9,), dtype=np.float32)

        self.state = np.zeros(9)  # Adjust the size to 9
        self.score_threshold = -199
        self.wait_threshold = 20  # Adjust the wait threshold as needed
        self.current_episode = 0


    def reset(self):
        # Inform the agent that a new episode is starting
        self.state = np.zeros(9)
        #print(f"Episode {self.current_episode} Reset")
        self.current_episode += 1  # Increment the episode counter
        return self.state.copy()  # Ensure the shape is (8,)

    def step(self, action):

        if action < 4:  # Ignore invalid actions
            set_signal(action)

        wait_times = [
            max(0, self.state[1] - 1),
            max(0, self.state[3] - 1),
            max(0, self.state[5] - 1),
            max(0, self.state[7] - 1)
        ]

        total_wait_time = sum(wait_times)
        reward = -total_wait_time

        bonus_threshold = 10
        for i, wait_time in enumerate(wait_times):
            if wait_time < bonus_threshold:
                reward += 5
            self.state[2 * i] = wait_time  # Update the wait times in the state

        self.state[-1] += reward  # Update the score in the state

        # Check for the episode termination condition
        done = self.state[-1] < self.score_threshold

        #print(f"Reward: {reward}, Done: {done}")

        return self.state, reward, done, {}

def reinforcement(data, env):
    A_cars, B_cars, C_cars, D_cars = data['A'][0], data['B'][0], data['C'][0], data['D'][0]
    A_wait, B_wait, C_wait, D_wait = data['A'][1], data['B'][1], data['C'][1], data['D'][1]
    score = data['S']

    env.state = np.array([A_cars, A_wait, B_cars, B_wait, C_cars, C_wait, D_cars, D_wait, score])
    
    
    action = np.random.choice([4, env.action_space.sample()], p=[0.995, 0.005])

    return action

def handle_client(client_socket, env):
    global data
    while True:
        # Clear the previous data
        data = None

        received_data = client_socket.recv(1024).decode('utf-8')
        with lock:
            try:
                data = json.loads(received_data)

                # Continue with reinforcement logic
                action = reinforcement(data, env)

                if action < 4:  # Ignore invalid actions
                    set_signal(action)

            except json.JSONDecodeError:
                try:
                    data = eval(received_data)
                    if not isinstance(data, dict):
                        #print("Data is not a dictionary. Skipping iteration.")
                        continue
                except Exception as e:
                    #print(f"Error processing received data: {e}")
                    continue
def set_signal(x):
    x = str(x)
    for client_socket in client_sockets:
        client_socket.sendall(x.encode('utf-8'))

def main():
    env = TrafficSignalEnv()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', 12345)
    server_socket.bind(server_address)
    server_socket.listen(5)
    print('Server is listening for connections...')
    client_socket, client_address = server_socket.accept()
    print('Accepted connection from', client_address)
    client_sockets.append(client_socket)
    client_handler = threading.Thread(target=handle_client, args=(client_socket, env))
    client_handler.start()

    # Training parameters
    total_episodes = 1000

    # Training loop with progress bar
    for episode in tqdm(range(1, total_episodes + 1), desc="Training Progress"):
        env.reset()
        # Add your training logic here
        
        # For example, you can call PPO's `learn` method with appropriate parameters
        model = PPO("MlpPolicy", env, verbose=0)
        model.learn(total_timesteps=1000)

    # After training is complete, you can save the model if needed
    model.save("trained_model")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
