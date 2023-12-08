TILESIZE = 50
WALLSIZE = 8
BOARDSIZE = 9
PLAYER_COLORS = ('forestgreen', 'firebrick', 'gold2', 'royalblue')
PLAYER_SIZE = TILESIZE/2 - 2

# Import game stuff
import pygame
from game.wall import Wall
from game.player import Player

# Import network stuff
from communication.connection import Connection

# Init game and window
pygame.init()
resolution = (900, 720)
screen = pygame.display.set_mode(resolution)

# Game clock
clock = pygame.time.Clock()

class GameMain(object):
    def __init__(self, connection) -> None:
        self.connection = connection
        self.game_started = False
        self.status = 'connecting'
        self.joined_players = []
        self.player_ids = []
        self.player_id = None
        self.current_player = None
        self.turn_index = 0
        self. player_positions = {
            "P1": (5, 2),
            "P2": (5, 9),
            "P3": (1, 6),
            "P4": (9, 5)
        }
        self.wall_positions = [(1,1,'h'), (5,2,'v'), (5,8,'h')]

        self.runGame()
    
    def runGame(self):
        board_surface = self.create_board_surf()
        board_pos = (resolution[0] - board_surface.get_size()[0]) / 2, 100

        wall_orientation = 'h'

        font = pygame.font.Font(None, 36)
        black = (0, 0, 0)

        running = True

        while running:
            # Check for network messages
            msg = self.connection.read_message()
            if msg:
                self.handle_network_message(msg)

            if self.status == 'connecting':
                self.connection.connect_to_peers()
                self.joined_players = connection.get_connected_peers()
                self.player_ids = connection.get_players()

            num_connected = len(self.joined_players) + 1
    
            # print(num_connected)
            # print(self.joined_players)
            # Check for events
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.connection.close()
                    running = False

                if True: #current_player == player_id:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_UP:
                            self.player_positions['P1'] = (self.player_positions['P1'][0], self.player_positions['P1'][1] - 1)
                            x, y = self.player_positions['P1']
                            self.connection.send_message('msg', f'PAWN,P1,{x},{y}')

                        if event.key == pygame.K_DOWN:
                            self.player_positions['P1'] = (self.player_positions['P1'][0], self.player_positions['P1'][1] + 1)
                            x, y = self.player_positions['P1']
                            self.connection.send_message('msg', f'PAWN,P1,{x},{y}')

                        if event.key == pygame.K_LEFT:
                            self.player_positions['P1'] = (self.player_positions['P1'][0] - 1, self.player_positions['P1'][1])
                            x, y = self.player_positions['P1']
                            self.connection.send_message('msg', f'PAWN,P1,{x},{y}')

                        if event.key == pygame.K_RIGHT:
                            self.player_positions['P1'] = (self.player_positions['P1'][0] + 1, self.player_positions['P1'][1])
                            x, y = self.player_positions['P1']
                            self.connection.send_message('msg', f'PAWN,P1,{x},{y}')

                        if event.key == pygame.K_o:
                            if wall_orientation == 'h':
                                wall_orientation = 'v'
                            else:
                                wall_orientation = 'h'

                    mousex, mousey = pygame.mouse.get_pos()
                    board_pos_x = (round((mousex - board_pos[0] + (WALLSIZE / 2)) / (TILESIZE + WALLSIZE)))
                    board_pos_y = (round((mousey - board_pos[1] + (WALLSIZE / 2)) / (TILESIZE + WALLSIZE)))

                    x, y = self.get_wall_coordinates((board_pos_x, board_pos_y), board_pos)

                    if wall_orientation == 'h':
                        rect = (x-(TILESIZE), y-(WALLSIZE/2), TILESIZE*2, WALLSIZE)
                    else:
                        rect = (x-(WALLSIZE/2), y-(TILESIZE), WALLSIZE, TILESIZE*2)

                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.wall_positions.append((board_pos_x, board_pos_y, wall_orientation))
                        self.connection.send_message('msg', f'WALL,{board_pos_x},{board_pos_y},{wall_orientation}')
                    
            # Drawing graphics
            screen.fill(pygame.Color('grey'))
            if self.status == "connecting":
                text_title = font.render("Multiplayer Quoridor", True, black)
                text_subtitle = font.render("Waiting for players", True, black)
                text_status = font.render(f"{num_connected} players joined", True, black)
                screen.blit(text_title, (300, 250))
                screen.blit(text_subtitle, (310, 280))
                screen.blit(text_status, (320, 320))

                if num_connected > 1:
                    text_start = font.render("Press enter to start", True, black)
                    screen.blit(text_start, (300, 350))
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            print('starting game')
                            self.status = 'starting'
                            connection.start_game()
                            self.status = "playing"
                
            if self.status == "playing": 
                walls = self.create_walls(self.wall_positions, board_pos)
                players = self.create_players(self.player_positions, board_pos)
                walls.draw(screen)
                players.draw(screen)
                if not self.current_player == self.player_id:
                    text_surface = font.render("Please wait for your turn", True, black)
                    screen.blit(text_surface, (300, 50))
                if self.current_player == self.player_id:
                    pygame.draw.rect(screen, (255, 0, 0, 50), rect, 2)
                screen.blit(board_surface, (board_pos))
            pygame.display.flip()
            clock.tick(60)

    def create_board_surf(self):
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
    def get_player_coordinates(self, pos, offset):
        x = pos[0] * (TILESIZE + WALLSIZE) - (TILESIZE / 2) - WALLSIZE + offset[0]
        y = pos[1] * (TILESIZE + WALLSIZE) - (TILESIZE / 2) - WALLSIZE + offset[1]
        return (x, y)

    # Convert board groove coordinates to pixel coordinates
    def get_wall_coordinates(self, pos, offset):
        x = pos[0] * (TILESIZE + WALLSIZE) - (WALLSIZE / 2) + offset[0]
        y = pos[1] * (TILESIZE + WALLSIZE) - (WALLSIZE / 2) + offset[1]
        return (x, y)

    def create_walls(self, wall_positions, board_pos):
        walls = pygame.sprite.Group()
        for i in range(len(wall_positions)):
            pos = self.get_wall_coordinates((wall_positions[i][0], wall_positions[i][1]), board_pos)
            orientation = wall_positions[i][2]
            wall = Wall(pos, WALLSIZE, (TILESIZE * 2 + WALLSIZE) , pygame.Color('black'), orientation)
            walls.add(wall)
        return walls

    def create_players(self, player_positions, board_pos):
        players = pygame.sprite.Group()
        i = 0
        for p_id, pos in player_positions.items():
            pos = self.get_player_coordinates(pos, board_pos)
            color = pygame.Color(PLAYER_COLORS[i])
            i+=1
            player = Player(pos, PLAYER_SIZE, color, p_id)
            players.add(player)
        return players
    
    def handle_network_message(self, msg):
        parts = msg.split(',')
        command = parts[0]
        
        match command:
            case 'PAWN':
                print('pawn message received')
                playerid = parts[1]
                self.player_positions[playerid] = (int(parts[2]),int(parts[3]))

            case 'WALL':
                print('wall message received')
                self.wall_positions.append((int(parts[1]),int(parts[2]),parts[3]))

            case 'TURN':
                print('turn message received')
            
            case 'START':
                print('start message received')

            case _:
                print('unknown message')

    # def joinGame(client, address):
    #     global player_id_to_address
    #     player_id_to_address["P2"] = address
    #     print("P2", address, "joined")

    # def passTurn(client=None):
    #     global current_player
    #     if current_player == 'P1':
    #         current_player = 'P2'
    #     elif current_player == 'P2':
    #         current_player = 'P1'
    #     else:
    #         current_player = 'P1'
    #     # global turn_index
    #     # turn_index += 1
    #     # global joined_players
    #     # if turn_index >= len(joined_players):
    #     #     turn_index = 0

if __name__ == '__main__':
    connection = Connection("0.0.0.0")
    connection.start()
    # wait for socket to be created
    # and for other games to start
    # import time
    # time.sleep(5)

    # # try to connect to nodes on other computers on the list
    # peers = ['Juha-Air']
    # connection.connect_to_peers(peers)
    GameMain(connection)
