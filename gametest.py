TILESIZE = 50
WALLSIZE = 8
BOARDSIZE = 9
PLAYER_COLORS = ('forestgreen', 'firebrick', 'gold2', 'royalblue')
STARTING_POSITIONS = {"P1": (5, 1), "P2": (5, 9), "P3": (1, 5), "P4": (9, 5)}
WINNING_POSITIONS = {"P1": ("row", 9), "P2": ("row", 1), "P3": ("col", 9), "P4": ("col", 1)}
PLAYER_SIZE = TILESIZE/2 - 2
MIN_NUM_OF_PLAYERS = 2


# Import game stuff
import pygame
from game.wall import Wall
from game.player import Player
import json

# Import network stuff
from communication.connection import Connection

# Pulse for alive checking
import time

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
        self.player_id = None
        self.current_player = None
        self.turn_index = 0
        self.player_positions = {}
        self.wall_positions = []
        self.turn_alive = None
        self.last_heartbeat = time.time()
        self.winning_player = None
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

            if self.status == 'starting':
                self.connection.start_game()
                if connection.ready_to_start:
                    self.populate_playerlist(num_connected)
                    self.player_id = connection.player_id
                    self.current_player = 'P1'
                    self.status = "playing"
                    
            if self.current_player and self.current_player == self.player_id:
                current_time = time.time()
                if current_time - self.last_heartbeat > 5:
                    self.last_heartbeat = time.time()
                    connection.send_message('msg', 'STILL_AWAKE')

            num_connected = len(self.joined_players) + 1
    
            # Check for events
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.connection.close()
                    running = False

                if self.current_player == self.player_id:
                    if event.type == pygame.KEYDOWN:
                        new_pos = None
                        if event.key == pygame.K_UP:
                            new_pos = (self.player_positions[self.player_id][0], self.player_positions[self.player_id][1] - 1)

                        if event.key == pygame.K_DOWN:
                            new_pos = (self.player_positions[self.player_id][0], self.player_positions[self.player_id][1] + 1)

                        if event.key == pygame.K_LEFT:
                            new_pos = (self.player_positions[self.player_id][0] - 1, self.player_positions[self.player_id][1])

                        if event.key == pygame.K_RIGHT:
                            new_pos = (self.player_positions[self.player_id][0] + 1, self.player_positions[self.player_id][1])
                        
                        if new_pos:
                            if self.valid_move(self.player_positions[self.player_id], new_pos):
                                self.player_positions[self.player_id] = new_pos
                                x, y = self.player_positions[self.player_id]
                                self.connection.send_message('msg', f'PAWN,{self.player_id},{x},{y}')
                                self.check_for_win()
                                if self.winning_player:
                                    self.connection.send_message('msg', 'WIN')
                                else:
                                    self.current_player = self.next_player()
                                    self.connection.send_message('msg', f'CURRENT_PLAYER,{self.current_player}')

                        if event.key == pygame.K_o:
                            if wall_orientation == 'h':
                                wall_orientation = 'v'
                            else:
                                wall_orientation = 'h'

                    mousex, mousey = pygame.mouse.get_pos()
                    wall_pos_x = (round((mousex - board_pos[0] + (WALLSIZE / 2)) / (TILESIZE + WALLSIZE)))
                    wall_pos_y = (round((mousey - board_pos[1] + (WALLSIZE / 2)) / (TILESIZE + WALLSIZE)))

                    x, y = self.get_wall_coordinates((wall_pos_x, wall_pos_y), board_pos)

                    if wall_orientation == 'h':
                        rect = (x-(TILESIZE), y-(WALLSIZE/2), TILESIZE*2, WALLSIZE)
                    else:
                        rect = (x-(WALLSIZE/2), y-(TILESIZE), WALLSIZE, TILESIZE*2)

                    if event.type == pygame.MOUSEBUTTONDOWN:
                        wall = (wall_pos_x, wall_pos_y, wall_orientation)
                        if self.valid_wall_pos(wall):
                            self.wall_positions.append(wall)
                            self.connection.send_message('msg', f'WALL,{wall_pos_x},{wall_pos_y},{wall_orientation}')
                            self.current_player = self.next_player()
                            self.connection.send_message('msg', f'CURRENT_PLAYER,{self.current_player}')
                    
            # Drawing graphics
            screen.fill(pygame.Color('grey'))
            if self.status == "connecting":
                text_title = font.render("Multiplayer Quoridor", True, black)
                text_subtitle = font.render("Waiting for players", True, black)
                text_status = font.render(f"{num_connected} players joined", True, black)
                screen.blit(text_title, (300, 250))
                screen.blit(text_subtitle, (310, 280))
                screen.blit(text_status, (320, 320))

                if num_connected >= MIN_NUM_OF_PLAYERS:
                    text_start = font.render("Press enter to start", True, black)
                    screen.blit(text_start, (300, 350))
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            print('starting game')
                            self.status = "starting"
                
            if self.status == "playing": 
                walls = self.create_walls(self.wall_positions, board_pos)
                players = self.create_players(self.player_positions, board_pos)
                walls.draw(screen)
                players.draw(screen)
                if self.winning_player:
                    text_won = font.render(f"Player {self.winning_player} won!", True, black)
                    screen.blit(text_won, (350, 50))
                else:
                    if not self.current_player == self.player_id:
                        if time.time() - self.last_heartbeat > 10:
                            text_surface = font.render("Waiting for current player to reconnect", True, black)
                            screen.blit(text_surface, (230, 50))
                        else:
                            text_surface = font.render("Please wait for your turn", True, black)
                            screen.blit(text_surface, (300, 50))
                    else:
                        text_surface = font.render(f"Your turn {self.player_id}", True, black)
                        screen.blit(text_surface, (350, 50))

                if self.current_player == self.player_id:
                    pygame.draw.rect(screen, (255, 0, 0, 50), rect, 2)
                screen.blit(board_surface, (board_pos))
                
            pygame.display.flip()
            clock.tick(60)


    # Check if pawn move is possible
    def valid_move(self, startpos, endpos):
        # check other pawns
        for playerpos in self.player_positions.values():
            if endpos == playerpos:
                return False
            
        # check for board edges
        for value in endpos:
            if value < 1 or value > BOARDSIZE:
                return False
            
        # check for walls
        deltax = endpos[0] - startpos[0]
        deltay = endpos[1] - startpos[1]

        # horizontal moves
        if not deltax == 0:
            blocking_wall1 = (min(startpos[0], endpos[0]), startpos[1], 'v')
            blocking_wall2 = (min(startpos[0], endpos[0]), startpos[1] - 1, 'v')
            if blocking_wall1 in self.wall_positions or blocking_wall2 in self.wall_positions:
                return False
        
        # vertical moves
        if not deltay == 0:
            blocking_wall1 = (startpos[0], min(startpos[1], endpos[1]), 'h')
            blocking_wall2 = (startpos[0] - 1, min(startpos[1], endpos[1]), 'h')
            if blocking_wall1 in self.wall_positions or blocking_wall2 in self.wall_positions:
                return False   
        return True
    

    # check if wall position is possible
    def valid_wall_pos(self, pos):
        # check for board edges
        if pos[0] < 1 or pos[0] > BOARDSIZE - 1 or pos[1] < 1 or pos[1] > BOARDSIZE - 1:
            return False
        
        if len(self.wall_positions) == 0:
            return True

        # check if there is already a wall in the pos
        for wall in self.wall_positions:
            if (wall[0], wall[1]) == (pos[0], pos[1]):
                return False
        
        # check for overlapping horizontal walls
        if wall[2] == 'h':
            hpos1 = (pos[0] - 1, pos[1], 'h')
            hpos2 = (pos[0] + 1, pos[1], 'h')
            if hpos1 in self.wall_positions or hpos2 in self.wall_positions:
                return False
        
        # check for overlapping vertical walls
        if wall[2] == 'v':
            vpos1 = (pos[0], pos[1] - 1, 'v')
            vpos2 = (pos[0], pos[1] + 1, 'v')
            if vpos1 in self.wall_positions or vpos2 in self.wall_positions:
                return False 
        return True
    
    
    # Check if a player has won
    def check_for_win(self):
        for player in self.player_positions:
            ppos = self.player_positions[player]
            colrow, wpos = WINNING_POSITIONS[player]
            if colrow == "col" and ppos[0] == wpos:
                self.winning_player = player
            elif colrow == "row" and ppos[1] == wpos:
                self.winning_player = player
    

    # Returns the id of the next player
    def next_player(self):
        pindex = int(self.current_player[1])
        next_player = (pindex) % (len(self.joined_players) + 1)
        return f'P{next_player + 1}'
    

    # Sets the pawns of the players to the starting positions
    def populate_playerlist(self, numplayers):
        for i in range(1, numplayers+1):
            id = f"P{i}"
            self.player_positions[id] = STARTING_POSITIONS[id]


    # Creates the game board graphics
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


    # Creates the wall graphics
    def create_walls(self, wall_positions, board_pos):
        walls = pygame.sprite.Group()
        for i in range(len(wall_positions)):
            pos = self.get_wall_coordinates((wall_positions[i][0], wall_positions[i][1]), board_pos)
            orientation = wall_positions[i][2]
            wall = Wall(pos, WALLSIZE, (TILESIZE * 2 + WALLSIZE) , pygame.Color('black'), orientation)
            walls.add(wall)
        return walls


    # Creates the player pawn graphics
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
                self.turn_index = int(parts[1])

            case 'CURRENT_PLAYER':
                self.current_player = parts[1]
                print('current player is', self.current_player)
            
            case 'START':
                print('start message received')
                self.player_id = self.connection.player_id
                self.populate_playerlist(len(self.joined_players) + 1)
                self.status = "playing"
                self.connection.set_playing(True)
                
            case 'STILL_AWAKE':
                print('heartbeat received')
                self.last_heartbeat = time.time()
                
            case 'WIN':
                print('winning message received')
                self.check_for_win()
            
            case 'START_SYNC':
                print('start sync message received')
                state = {
                    "status": self.status,
                    "playerpos": self.player_positions,
                    "walls": self.wall_positions,
                    "currentplayer": self.current_player
                    }

                data = json.dumps(state)
                self.connection.send_message('msg', f'SYNC,{data}')
            
            case 'SYNC':
                if self.status == "playing":
                    pass

                jsonstr = msg[5:]
                data = json.loads(jsonstr)
                self.player_positions = data["playerpos"]
                self.wall_positions = data["walls"]
                self.current_player = data["currentplayer"]
                self.status = data["status"]
                self.connection.get_my_id()
                self.player_id = self.connection.player_id


            case _:
                print('unknown message')


if __name__ == '__main__':
    connection = Connection("0.0.0.0")
    connection.start()
    GameMain(connection)
