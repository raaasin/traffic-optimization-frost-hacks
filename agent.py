import socket
import threading
import json
import numpy as np
from tqdm import tqdm

client_sockets = []
lock = threading.Lock()

def rule_based_logic(data, max_wait_threshold=35):
    A_cars, B_cars, C_cars, D_cars = data['A'][0], data['B'][0], data['C'][0], data['D'][0]
    A_wait, B_wait, C_wait, D_wait = data['A'][1], data['B'][1], data['C'][1], data['D'][1]

    # Check if the total wait time is critical
    if A_wait + B_wait + C_wait + D_wait >= max_wait_threshold:
        return np.argmax([A_cars, B_cars, C_cars, D_cars])  # Prioritize the lane with the highest car density

    # Regular traffic management based on car density and wait times
    if A_cars + B_cars > C_cars + D_cars:
        return np.argmax([A_cars, B_cars])  # Set signal for the lane with the highest car density between A and B
    else:
        return np.argmax([C_cars, D_cars]) + 2  # Set signal for the lane with the highest car density between C and D


def handle_client(client_socket):
    global data
    while True:
        data = None
        received_data = client_socket.recv(1024).decode('utf-8')
        with lock:
            try:
                data = json.loads(received_data)
                action = rule_based_logic(data)
                set_signal(action)
            except json.JSONDecodeError:
                try:
                    data = eval(received_data)
                    if not isinstance(data, dict):
                        continue
                except Exception as e:
                    continue

def set_signal(x):
    x = str(x)
    for client_socket in client_sockets:
        client_socket.sendall(x.encode('utf-8'))

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', 12345)
    server_socket.bind(server_address)
    server_socket.listen(5)
    print('Server is listening for connections...')
    client_socket, client_address = server_socket.accept()
    print('Accepted connection from', client_address)
    client_sockets.append(client_socket)
    client_handler = threading.Thread(target=handle_client, args=(client_socket,))
    client_handler.start()

    while True:
        pass

if __name__ == "__main__":
    main()
