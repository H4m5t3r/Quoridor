PORT = 5050
FORMAT = 'utf-8'
DEBUG = True
HEADER = 64

import socket
import threading
import json
from collections import deque
from enum import Enum
import time


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
        self.awaiting_agreement_on = None
        self.agreements = {}
        self.players = {}
        self.state = {
            "agree_players": False,
            "playing": False,
            }
        self.player_id = None
        self.ready_to_start = False


    def get_my_ip(self):
        localname = socket.gethostname()
        # Dummy fix for home network
        if localname in ['lx9-fuxi101', 'anton-msb08911']:
            localname = localname + "-Ethernet"
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
            print(f"Connecting to possible peers {self.potential_connections}")
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
                # Check if node is reconnecting
                if address[0] in self.addresses:
                    Logger.log('Node reconnecting')
                    if self.state["playing"]:
                        # if playing and reconnecting, reconnect and send state
                        self.potential_connections.append(address[0])
                        self.addresses.remove(address[0])
                        self.connect_to_peers()
                        self.send_known_connections()
                        self.send_message(MessageTypes.PLAYER_IDS, self.players)
                        self.messages.append('START_SYNC')

                self.potential_connections.append(address[0])
                threading.Thread(target=self.handle_client, args=(connection, address)).start()
            except ConnectionAbortedError:
                return
        Logger.log('Stopped listening for new connections')


    # Sends a message to all connections
    def send_message(self, type, data):
        dict = {"type": type, "data": data}
        message = json.dumps(dict).encode(FORMAT)

        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))

        if len(message) > 1024:
            Logger.log('message too long')

        for connection in self.connections:
            try:
                connection.send(send_length+message)
                Logger.log(f"Sent message to {connection.getpeername()}: {message}")
            except socket.error as e:
                Logger.log(f"Failed to send message. Error: {e}")
                self.connections.remove(connection)
                Logger.debug(f"Removed connection {connection} from connections")
                Logger.debug(f"Remaining connections {self.connections}")


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
        Logger.debug(f'get agreement on {variable}')
        self.awaiting_agreement_on = variable
        self.agreements[self.my_ip] = True
        agreement = {"variable": variable, "data": state}
        self.send_message(MessageTypes.DOYOUAGREE, agreement)


    def __generate_playerlist(self):
        Logger.debug('generating playerlist')
        adds = self.addresses.copy()
        adds.append(self.my_ip)
        adds.sort()
        pdict = {}
        for i in range(0, len(adds)):
            pdict[f"P{i+1}"] = adds[i]
        self.players = pdict
  
    def __all_agree(self, dict):
        for value in dict.values():
            if value == False:
                return False
        return True


    def start_game(self):
        if self.state["agree_players"] == False and self.awaiting_agreement_on == None:
            self.__generate_playerlist()
            self.get_agreement("agree_players", self.players)
        if self.ready_to_start == False and self.state["agree_players"]:
            self.ready_to_start = True
            self.send_message(MessageTypes.MESSAGE, "CURRENT_PLAYER,P1")
            self.send_message(MessageTypes.MESSAGE, "START")
            self.state["playing"] = True
      

    def get_connected_peers(self):
        return self.connections


    # Handles a connection from another computer
    def handle_client(self, connection, address):
        connected = True
        while connected:
            try:
                msg_length = connection.recv(HEADER).decode(FORMAT)
                msg_length = int(msg_length)

                msg = connection.recv(msg_length)
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
                    remaining_players = []
                    for conn in self.connections:
                        if conn.getpeername()[0] == connection.getpeername()[0]:
                            conn.close()
                            if not self.state["playing"]:
                                self.addresses.remove(connection.getpeername()[0])
                        else:
                            remaining_players.append(conn)
                    connection.close()
                    self.connections = remaining_players
                    connected = False

                if message_type == MessageTypes.DOYOUAGREE:
                    answer = self.agree(dict["data"]["variable"], dict["data"]["data"])
                    data = {"ip": self.my_ip, "answer": answer}
                    self.send_message(MessageTypes.AGREE, data)

                if message_type == MessageTypes.AGREE:
                    if not self.awaiting_agreement_on == None:
                        self.agreements[dict["data"]["ip"]] = dict["data"]["answer"]
                        if len(self.agreements) == len(self.addresses) + 1:
                            if self.__all_agree(self.agreements):
                                Logger.debug(f"all nodes agreed on {self.awaiting_agreement_on}")
                                if self.awaiting_agreement_on == "agree_players":
                                    self.send_message(MessageTypes.PLAYER_IDS, self.players)
                                    self.get_my_id()
                                self.state[self.awaiting_agreement_on] = True
                                self.awaiting_agreement_on = None
                            else:
                                print("no agreement")
                    else:
                        pass

                if message_type == MessageTypes.PLAYER_IDS:
                    self.players = dict["data"]
                    Logger.log(f"Set player list to {self.players}")
                    self.get_my_id()

            except socket.error:
                break
            except json.JSONDecodeError:
                    Logger.debug(f"Error parsing json: {msg}")
        Logger.log(f"Connection from {address} closed.")


    def get_my_id(self):
        for id in self.players:
            if self.players[id] == self.my_ip:
                self.player_id = id
                print('set my id to ', self.player_id)
    
    def set_playing(self, value):
        self.state["playing"] = value


    # Starts a thread that listens to new connections
    def start(self):
        listen_thread = threading.Thread(target=self.listen_for_connections)
        listen_thread.start()

        peers = ['Juha-Air', 'Juhas-Mac-mini']
        # peers = ['lx9-fuxi101-Ethernet', 'anton-msb08911-Ethernet']

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


    def debug(message):
        if DEBUG:
            print(message)


class MessageTypes(str, Enum):
    MESSAGE = "msg"
    CONNECTIONS = "connections"
    DISCONNECT = "!disconnect"
    DOYOUAGREE = "youagree"
    AGREE = "agree"
    PLAYER_IDS = "playerids"
    STILL_AWAKE = "stillawake"