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
        self.awaiting_agreement = "agree_players"
        self.agreements = {}
        self.players = {}
        self.state = {
            "agree_players": False,
            "agree_pawns": False,
            "agree_walls": False
            }
        self.i_am_oldest = False
        self.player_ids = {}

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
            self.player_ids["P" + str(len(self.player_ids) + 1)] = host
            Logger.log(f"Connection created to {host}:{PORT}")

            self.send_known_connections()
            if host != socket.gethostname():
                self.send_player_ids()

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

    def send_player_ids(self):
        self.send_message(MessageTypes.PLAYERS, self.player_ids)

    # Function for accepting new connections and creating threads for them
    def listen_for_connections(self):
        # self.player_ids = {"P1": socket.gethostname()}
        self.socket.bind((self.host, PORT))
        self.i_am_oldest = True
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
                Logger.log(f"Sent message to {connection.getpeername()}: {message}")
            except socket.error as e:
                Logger.log(f"Failed to send message. Error: {e}")

    # Returns a message from the message queue. 
    # Called by the game loop to check for network events.
    def read_message(self):
        if len(self.messages) > 0:
            return self.messages.popleft()
        else:
            return None
        
    def agree(self, variable, state):
        if variable == "agree_players":
            if len(self.players) == 0:
                self.players = state
                return True
            if self.players == state:
                return True
            return False

    def get_agreement(self, variable, state):
        self.awaiting_agreement = True
        self.agreements[self.my_ip] = True
        agreement = {"variable": variable, "data": state}
        self.send_message(MessageTypes.DOYOUAGREE, agreement)

    def __generate_playerlist(self):
        adds = self.addresses.copy()
        adds.append(self.my_ip)
        adds.sort()
        pdict = {}
        for i in range(0, len(adds)):
            pdict[f"P{i}"] = adds[i]
        self.players = pdict
    
    def __all_agree(self, dict):
        for value in dict.values():
            if value == False:
                return False
        return True

    def start_game(self):
        if self.state["agree_players"] == False:
            self.__generate_playerlist()
            self.get_agreement("agree_players", self.players)
        else:
            Logger.log("Agreed on player list and order")
        
    def get_connected_peers(self):
        return self.connections

    def get_player_ids(self):
        return self.player_ids

    # Handles a connection from another computer
    def handle_client(self, connection, address):
        while self.running:
            try:
                msg = connection.recv(1024)
                dict = json.loads(msg.decode(FORMAT))
                message_type = dict["type"]
                Logger.log(f"Received message from {connection.getpeername()}: {msg}")

                if message_type == MessageTypes.MESSAGE:
                    self.messages.append(dict["data"])
                
                if message_type == MessageTypes.CONNECTIONS:
                    Logger.log(f"received connections from' {connection.getpeername()}: {dict['data']}")
                    for conn in dict["data"]:
                        self.potential_connections.append(conn)

                if message_type == MessageTypes.DISCONNECT:
                    for conn in self.connections:
                        if conn.getpeername()[0] == connection.getpeername()[0]:
                            conn.close()
                            self.addresses.remove(connection.getpeername()[0])
                    connection.close()
                    self.running = False
                    Logger.log(f"Connection from {address} closed.")

                if message_type == MessageTypes.DOYOUAGREE:
                    answer = self.agree(dict["data"]["variable"], dict["data"]["data"])
                    print(answer)
                    data = {"ip": self.my_ip, "answer": answer}
                    self.send_message(MessageTypes.AGREE, data)

                if message_type == MessageTypes.AGREE:
                    if not self.awaiting_agreement == None:
                        self.agreements[dict["data"]["ip"]] = dict["data"]["answer"]
                        if len(self.agreements) == len(self.addresses) + 1:
                            if self.__all_agree(self.agreements):
                                print("all agree")
                                self.state[self.awaiting_agreement] = True
                                self.awaiting_agreement = None
                            else:
                                print("no agreement")
                    else:
                        pass

                if message_type == MessageTypes.PLAYERS:
                    # if not self.i_am_host:?
                    for player in dict["data"].keys():
                        if not player in self.player_ids.keys():
                            self.player_ids[player] = dict["data"][player]
                    print("Updated players to", self.player_ids)

            except socket.error:
                break

    # Starts a thread that listens to new connections
    def start(self):
        listen_thread = threading.Thread(target=self.listen_for_connections)
        listen_thread.start()

        # peers = ['Juha-Air', 'Juhas-Mac-mini']
        peers = ['lx9-fuxi101-Wireless', 'anton-msb08911-Ethernet']

        for p in peers:
            peerip = socket.gethostbyname(p)
            self.potential_connections.append(peerip)

    # Closes socket and other connections
    def close(self):
        self.running = False
        self.send_message(MessageTypes.DISCONNECT, " ")
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
    DOYOUAGREE = "youagree"
    AGREE = "agree"
    PLAYERS = "players"