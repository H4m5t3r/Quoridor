import pygame
from game.wall import Wall
from game.player import Player
import threading
import time
import socket
import select
import pickle

pygame.init()

TILESIZE = 50
WALLSIZE = 8
BOARDSIZE = 9
PLAYER_COLORS = ('forestgreen', 'firebrick', 'gold2', 'royalblue')
PLAYER_SIZE = TILESIZE/2 - 2

PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
MSG_LEN = 64
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = '!DISCONNECT'

def create_board_surf():
    board_surf = pygame.Surface(((TILESIZE + WALLSIZE) * BOARDSIZE - WALLSIZE, 
                                 (TILESIZE + WALLSIZE) * BOARDSIZE - WALLSIZE), pygame.SRCALPHA, 32)
    color = pygame.Color('black')
    wall_thickness = 1

    for y in range(BOARDSIZE):
        for x in range(BOARDSIZE):
            rect = pygame.Rect(x * (TILESIZE+WALLSIZE), y * (TILESIZE+WALLSIZE), TILESIZE, TILESIZE)
            pygame.draw.rect(board_surf, color, rect, wall_thickness)
    return board_surf

# Convert board tile coordinates to pixel coordinates
def get_player_coordinates(pos, offset):
    x = pos[0] * (TILESIZE + WALLSIZE) - (TILESIZE / 2) - WALLSIZE + offset[0]
    y = pos[1] * (TILESIZE + WALLSIZE) - (TILESIZE / 2) - WALLSIZE + offset[1]
    return (x, y)

# Convert board groove coordinates to pixel coordinates
def get_wall_coordinates(pos, offset):
    x = pos[0] * (TILESIZE + WALLSIZE) - (WALLSIZE / 2) + offset[0]
    y = pos[1] * (TILESIZE + WALLSIZE) - (WALLSIZE / 2) + offset[1]
    return (x, y)

def create_walls(wall_positions, board_pos):
    walls = pygame.sprite.Group()
    for i in range(len(wall_positions)):
        pos = get_wall_coordinates((wall_positions[i][0], wall_positions[i][1]), board_pos)
        orientation = wall_positions[i][2]
        wall = Wall(pos, WALLSIZE, (TILESIZE * 2 + WALLSIZE) , pygame.Color('black'), orientation)
        walls.add(wall)
    return walls

def create_players(player_positions, board_pos):
    players = pygame.sprite.Group()
    i = 0
    for p_id, pos in player_positions.items():
        pos = get_player_coordinates(pos, board_pos)
        color = pygame.Color(PLAYER_COLORS[i])
        i+=1
        player = Player(pos, PLAYER_SIZE, color, p_id)
        players.add(player)
    return players

def checkTurn():
    global game_paused
    game_paused = True
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind(ADDR)
        host(server_socket)
    except:
        joined(server_socket)

    global current_player
    while True:
        time.sleep(5)
        current_player = 'P2'
        time.sleep(5)
        current_player = 'P1'

def host(server_socket):
    server_socket.listen(4)
    inputs = [server_socket]
    outputs = []
    global player_id
    player_id = "P1"

    global turn_index
    while True:
        readable, writable, exceptional = select.select(
        inputs, outputs, inputs, 1)
        for s in readable:
            if s is server_socket:
                connection, client_address = s.accept()
                connection.setblocking(0)
                inputs.append(connection)
                threading.Thread(target=handle_client, args=(connection, client_address)).start()
                print(turn_index)


def handle_client(client, address):
    msg_length = client.recv(MSG_LEN).decode(FORMAT)
    msg_length = int(msg_length)
    msg = client.recv(msg_length).decode(FORMAT)
    print(msg)
    # global commands
    # print(commands[msg])
    passTurn()
    commands[msg](client, address)
    # joinGame(client, address)

    # request_bytes = b"" + client.recv(1024)

    # if not request_bytes:
    #     print("Connection closed")
    #     client.close()
    # request_str = request_bytes.decode()
    # print(request_str)

def joined(server_socket):
    server_socket.connect(ADDR)
    
    inputs = [server_socket]
    outputs = []

    global turn_index
    print(turn_index)
    passTurn()
    send(server_socket, "join")
    print(turn_index)
    # msg_len = int(server_socket.recv(MSG_LEN).decode(FORMAT))
    # msg = server_socket.recv(msg_len)
    # print(msg)

    while True:
        readable, writable, exceptional = select.select(
        inputs, outputs, inputs, 1)
        for s in readable:
            if s is server_socket:
                connection, client_address = s.accept()
                connection.setblocking(0)
                inputs.append(connection)
                threading.Thread(target=handle_client, args=(connection, client_address)).start()

def send(server, msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (MSG_LEN - len(send_length))
    server.send(send_length)
    server.send(message)
    print(server.recv(2048))

def joinGame(client, address):
    global player_id_to_address
    player_id_to_address["P2"] = address
    print("P2", address, "joined")

def passTurn(client=None):
    global current_player
    if current_player == 'P1':
        current_player = 'P2'
    elif current_player == 'P2':
        current_player = 'P1'
    else:
        current_player = 'P1'
    # global turn_index
    # turn_index += 1
    # global joined_players
    # if turn_index >= len(joined_players):
    #     turn_index = 0

def main():
    createGlobalVariables()
    check_turn = threading.Thread(target=runGame)
    check_turn.start()
    run_game = threading.Thread(target=checkTurn)
    run_game.start()

def createGlobalVariables():
    global game_started
    game_started = False
    global joined_players
    joined_players = ['P1', 'P2']
    global current_player
    current_player = 'pause'
    global player_id
    player_id = 'init'
    global commands
    commands = {
        "join": joinGame,
        "pass": passTurn
    }
    global player_id_to_address
    player_id_to_address = {}
    global turn_index
    turn_index = 99999999

def runGame():
    resolution = (900, 720)
    
    screen = pygame.display.set_mode(resolution)
    clock = pygame.time.Clock()

    board_surface = create_board_surf()
    board_pos = (resolution[0] - board_surface.get_size()[0]) / 2, 100

    global current_player
    global player_id
    wall_orientation = 'h'

    global wall_positions
    wall_positions = [(1,1,'h'), (5,2,'v'), (5,8,'h')]
    player_positions = {
        "P1": (5, 2),
        "P2": (5, 9),
        "P3": (1, 6),
        "P4": (9, 5)
    }

    font = pygame.font.Font(None, 36)
    black = (0, 0, 0)

    global turn_index
    global joined_players
    running = True
    while running:
        events = pygame.event.get()
        screen.fill(pygame.Color('grey'))
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            
            if current_player == player_id:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        player_positions['P1'] = (player_positions['P1'][0], player_positions['P1'][1] - 1)
                    if event.key == pygame.K_DOWN:
                        player_positions['P1'] = (player_positions['P1'][0], player_positions['P1'][1] + 1)
                    if event.key == pygame.K_LEFT:
                        player_positions['P1'] = (player_positions['P1'][0] - 1, player_positions['P1'][1])
                    if event.key == pygame.K_RIGHT:
                        player_positions['P1'] = (player_positions['P1'][0] + 1, player_positions['P1'][1])
                    if event.key == pygame.K_o:
                        if wall_orientation == 'h':
                            wall_orientation = 'v'
                        else:
                            wall_orientation = 'h'

                mousex, mousey = pygame.mouse.get_pos()
                board_pos_x = (round((mousex - board_pos[0] + (WALLSIZE / 2)) / (TILESIZE + WALLSIZE)))
                board_pos_y = (round((mousey - board_pos[1] + (WALLSIZE / 2)) / (TILESIZE + WALLSIZE)))

                x, y = get_wall_coordinates((board_pos_x, board_pos_y), board_pos)

                if wall_orientation == 'h':
                    rect = (x-(TILESIZE), y-(WALLSIZE/2), TILESIZE*2, WALLSIZE)
                else:
                    rect = (x-(WALLSIZE/2), y-(TILESIZE), WALLSIZE, TILESIZE*2)

                if event.type == pygame.MOUSEBUTTONDOWN:
                        wall_positions.append((board_pos_x, board_pos_y, wall_orientation))
                
                if current_player == player_id:
                    pygame.draw.rect(screen, (255, 0, 0, 50), rect, 2)
                

        walls = create_walls(wall_positions, board_pos)
        players = create_players(player_positions, board_pos)
        walls.draw(screen)
        players.draw(screen)
        if not current_player == player_id:
            text_surface = font.render("Please wait for your turn", True, black)
            screen.blit(text_surface, (300, 50))
        screen.blit(board_surface, (board_pos))
        pygame.display.flip()
        clock.tick(60)


if __name__ == '__main__':
    main()
