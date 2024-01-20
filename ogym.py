import gym
from gym import spaces
import numpy as np
import time
import socket
import threading
import json
from stable_baselines3 import PPO

client_sockets = []
lock = threading.Lock()

class TrafficSignalEnv(gym.Env):
    def __init__(self):
        super(TrafficSignalEnv, self).__init__()

        # Define action and observation space
        self.action_space = spaces.Discrete(4)

        self.observation_space = spaces.Dict({
            'A': spaces.Tuple([spaces.Discrete(11), spaces.Discrete(101)]),
            'B': spaces.Tuple([spaces.Discrete(11), spaces.Discrete(101)]),
            'C': spaces.Tuple([spaces.Discrete(11), spaces.Discrete(101)]),
            'D': spaces.Tuple([spaces.Discrete(11), spaces.Discrete(101)]),
            'Score': spaces.Discrete(1001)
        })

        self.state = {
            'A': (0, 0),
            'B': (0, 0),
            'C': (0, 0),
            'D': (0, 0),
            'Score': 0
        }

        self.score_threshold = 25

    def reset(self):
        self.state = {
            'A': (0, 0),
            'B': (0, 0),
            'C': (0, 0),
            'D': (0, 0),
            'Score': 0
        }
        return self.state

    def step(self, action):
        set_signal(action)

        wait_times = {
            'A': max(0, self.state['A'][1] - 1),
            'B': max(0, self.state['B'][1] - 1),
            'C': max(0, self.state['C'][1] - 1),
            'D': max(0, self.state['D'][1] - 1)
        }

        total_wait_time = sum(wait_times.values())
        reward = -total_wait_time

        bonus_threshold = 10
        for road, wait_time in wait_times.items():
            if wait_time < bonus_threshold:
                reward += 5

        self.state['Score'] += reward
        done = self.state['Score'] < -200

        return self.state, reward, done, {}

def reinforcement(data, env):
    A_cars, B_cars, C_cars, D_cars = data['A'][0], data['B'][0], data['C'][0], data['D'][0]
    A_wait, B_wait, C_wait, D_wait = data['A'][1], data['B'][1], data['C'][1], data['D'][1]
    score = data['S']

    env.state = {
        'A': (A_cars, A_wait),
        'B': (B_cars, B_wait),
        'C': (C_cars, C_wait),
        'D': (D_cars, D_wait),
        'Score': score
    }

    # In reinforcement, you should ideally return the action chosen by the agent, not a random action
    action = env.action_space.sample()
    return action

def handle_client(client_socket, env):
    global data
    while True:
        received_data = client_socket.recv(1024).decode('utf-8')
        with lock:
            try:
                data = json.loads(received_data)
                action = reinforcement(data, env)
                set_signal(action)
            except json.JSONDecodeError:
                try:
                    data = eval(received_data)
                    if not isinstance(data, dict):
                        print("Data is not a dictionary. Skipping iteration.")
                        continue
                except Exception as e:
                    print(f"Error processing received data: {e}")
                    continue

def set_signal(x):
    x = str(x)
    with lock:
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

if __name__ == "__main__":
    main()

# Create an instance of the Gym environment
env = TrafficSignalEnv()

# Create the PPO agent
model = PPO("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=10000)

# Save the trained model
model.save("traffic_signal_ppo")
