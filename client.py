import socket
import threading
import sys

HEADER = 64
PORT = 5050
SERVER = '192.168.100.16'
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'

# server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# server.connect(ADDR)

def send(server, msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    server.send(send_length)
    server.send(message)
    print(server.recv(2048))

def fetchIncoming():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect(ADDR)
    global active
    while active:
        print(server.recv(2048))
    send(server, "!DISCONNECT")
    

def performTasks():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect(ADDR)
    send(server, 'Hello world!')
    input()
    send(server, 'Hello again!')
    input()
    send(server, 'Gotta go eat')
    input()
    send(server, "!DISCONNECT")
    global active
    active = False


global active
active = True

msg_check_thread = threading.Thread(target=fetchIncoming)
msg_check_thread.start()

msg_check_thread = threading.Thread(target=performTasks)
msg_check_thread.start()

# if __name__ == '__main__':
    # input()