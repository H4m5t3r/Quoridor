import socket
import threading

HEADER = 64
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = '!DISCONNECT'

def handleClient(conn, addr):
    print(f'[NEW CONNECTION] {addr} connected')
    global connections
    connections[addr] = conn
    connected = True
    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)
            if msg == DISCONNECT_MESSAGE:
                connected = False
                # conn.send('Disconnect received'.encode(FORMAT))
                for client in connections.values():
                    client.send(f'{addr} disconnected'.encode(FORMAT))
                del connections[addr]
            else:
                conn.send('Message received'.encode(FORMAT))
                for client in connections.values():
                    client.send(f'[{addr}] {msg}'.encode(FORMAT))
            print(f'[{addr}] {msg}')

    conn.close()
        

def start():
    global connections
    connections = {}
    global server
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handleClient, args=(conn, addr))
        thread.start()
        print(f'[ACTIVE CONNECTIONS] {threading.active_count() - 1}')


if __name__ == '__main__':
    global server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    print('[STARTING] The server is starting')
    start()

