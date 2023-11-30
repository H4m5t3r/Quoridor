PORT = 5050
FORMAT = 'utf-8'
MSG_LEN = 64
DISCONNECT_MESSAGE = '!DISCONNECT'

import socket
import threading
from collections import deque

class Connection:
    def __init__(self, host):
        self.host = host
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connections = []
        self.messages = deque()
        self.running = True

    def connect_to_game(self, host):
        try:
            print(f'Attempting connection to {host}')
            connection = socket.create_connection((host, PORT), timeout=10)
            self.connections.append(connection)
            print(f"Connection created to {host}:{PORT}")
        except ConnectionRefusedError:
            print(f'Connection to {host} refused')
        except TimeoutError:
            print(f'Connection to {host} timed out')

    # iterates through a list and tries to connect to games on different computers
    def connect_to_peers(self, peers):
        for p in peers:
             self.connect_to_game(socket.gethostbyname(p))

    # Function for accepting new connections and creating threads for them
    def listen_for_connections(self):
        self.socket.bind((self.host, PORT))
        self.socket.listen(4)
        print(f"Listening for connections on {self.host}:{PORT}")

        while self.running:
            try: 
                connection, address = self.socket.accept()
                self.connections.append(connection)
                print(f"Accepted connection from {address}")
                threading.Thread(target=self.handle_client, args=(connection, address)).start()
            except ConnectionAbortedError:
                return
        print('Stop listening for new connections')

    # Sends a message to all contacts
    def send_message(self, msg):
        message = msg.encode(FORMAT)
        if len(message) > 1024:
            print('message too long')

        for connection in self.connections:
            try:
                connection.send(message)
            except socket.error as e:
                print(f"Failed to send message. Error: {e}")

    # Returns a message from the message queue. 
    # Called by the game loop to check for network events.
    def read_message(self):
        if len(self.messages) > 0:
            return self.messages.popleft()
        else:
            return None

    # Handles a connection from another computer
    def handle_client(self, connection, address):
        while self.running:
            try:
                msg = connection.recv(1024).decode(FORMAT)
                print(msg)
                self.messages.append(msg)
            except socket.error:
                break

        print(f"Connection from {address} closed.")
        self.connections.remove(connection)
        connection.close()

    # Starts a thread that listens to new connections
    def start(self):
        listen_thread = threading.Thread(target=self.listen_for_connections)
        listen_thread.start()

    # Closes socket and other connections
    def close(self):
        self.running = False
        for connection in self.connections:
            connection.close()
        self.socket.close()
