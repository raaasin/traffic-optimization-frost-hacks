import numpy as np
import time
import socket
import threading
import json
client_sockets = []
lock = threading.Lock() 
def reinforcement(data):
    #Total number of cars in each lane/road
    A_cars = data['A'][0]
    B_cars = data['B'][0]
    C_cars = data['C'][0]
    D_cars = data['D'][0]

    #Max waiting time from each lane/road, that means the max time a car has been waiting in the lane/road
    A_wait = data['A'][1]
    B_wait = data['B'][1]
    C_wait = data['C'][1]
    D_wait = data['D'][1]

    #The live score of the game
    Score=data['S']

    #use the data to calculate the reinforcement learning

    """ you have two options,
    1. you can set any signal green 0,1,2,3
    2. you can just wait and do nothing"""

    #expecting to follow the game score as a parameter of the reinforcement learning

    #to set any signal to green use the following command"

    set_signal(0) #set signal 0 to green

def handle_client(client_socket):
    global data
    while True:
        received_data = client_socket.recv(1024).decode('utf-8')
        with lock:
            try:
                data = json.loads(received_data)

                reinforcement(data)
            except json.JSONDecodeError:
                try:
                    data = eval(received_data)
                    if not isinstance(data, dict):
                        print("data is not a dictionary. Skipping iteration.")
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



if __name__ == "__main__":
    main()