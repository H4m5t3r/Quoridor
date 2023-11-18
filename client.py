import socket

HEADER = 64
PORT = 5050
SERVER = '192.168.100.16'
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# input()
server.connect(ADDR)

def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    server.send(send_length)
    server.send(message)
    print(server.recv(2048))

send('Hello world!')
input()
send('Hello again!')
input()
send('Gotta go eat')
input()
send("!DISCONNECT")

# if __name__ == '__main__':
    # input()