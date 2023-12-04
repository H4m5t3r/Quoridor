PORT = 5050
FORMAT = 'utf-8'

import socket
import threading
import json
from collections import deque
from enum import Enum

class Connection:
    def __init__(self, host):
        self.host = host
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connections = []
        self.addresses = []
        self.potential_connections = []
        self.messages = deque()
        self.running = True
        self.my_ip = self.get_my_ip()

    def get_my_ip(self):
        localname = socket.gethostname()
        IP = socket.gethostbyname(localname)
        return IP
    
        # s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # s.connect(("8.8.8.8", 80))
        # IP = s.getsockname()[0]
        # s.close()
        # return IP

    def connect_to_node(self, host):
        try:
            Logger.log(f'Attempting connection to {host}')
            connection = socket.create_connection((host, PORT), timeout=10)
            self.connections.append(connection)
            self.addresses.append(host)
            Logger.log(f"Connection created to {host}:{PORT}")

            self.send_known_connections()
        except ConnectionRefusedError:
            Logger.log(f'Connection to {host} refused')
        except TimeoutError:
            Logger.log(f'Connection to {host} timed out')

    def connect_to_peers(self):
        while len(self.potential_connections) > 0:
            conn = self.potential_connections.pop()
            if not (conn == self.my_ip or conn in self.addresses):
                self.connect_to_node(socket.gethostbyname(conn))
        
    def send_known_connections(self):
        self.send_message(MessageTypes.CONNECTIONS, self.addresses)

    # Function for accepting new connections and creating threads for them
    def listen_for_connections(self):
        self.socket.bind((self.host, PORT))
        self.socket.listen(4)
        Logger.log(f"Listening for connections on {self.host}:{PORT}")

        while self.running:
            try: 
                connection, address = self.socket.accept()
                Logger.log(f"Accepted connection from {address}")
                self.potential_connections.append(address[0])
                threading.Thread(target=self.handle_client, args=(connection, address)).start()
            except ConnectionAbortedError:
                return
        Logger.log('Stopped listening for new connections')

    # Sends a message to all connections
    def send_message(self, type, data):
        dict = {"type": type, "data": data}
        message = json.dumps(dict).encode(FORMAT)

        if len(message) > 1024:
            Logger.log('message too long')

        for connection in self.connections:
            try:
                connection.send(message)
            except socket.error as e:
                Logger.log(f"Failed to send message. Error: {e}")

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
                msg = connection.recv(1024)
                dict = json.loads(msg.decode(FORMAT))
                message_type = dict["type"]

                if message_type == MessageTypes.MESSAGE:
                    self.messages.append(dict["data"])
                
                if message_type == MessageTypes.CONNECTIONS:
                    Logger.log('received connections')
                    for conn in dict["data"]:
                        self.potential_connections.append(conn)

            except socket.error:
                break

        Logger.log(f"Connection from {address} closed.")
        self.connections.remove(connection)
        connection.close()

    # Starts a thread that listens to new connections
    def start(self):
        listen_thread = threading.Thread(target=self.listen_for_connections)
        listen_thread.start()

        peers = ['Juha-Air', 'Juhas-Mac-mini']

        for p in peers:
            peerip = socket.gethostbyname(p)
            self.potential_connections.append(peerip)

    # Closes socket and other connections
    def close(self):
        self.running = False
        self.send_message(MessageTypes.DISCONNECT, "")
        for connection in self.connections:
            connection.close()
        self.socket.close()

class Logger():
    def log(message):
        print(message)

class MessageTypes(str, Enum):
    MESSAGE = "msg"
    CONNECTIONS = "connections"
    DISCONNECT = "!disconnect"