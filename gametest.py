import pygame
from game.wall import Wall
from game.player import Player
import threading
import time

pygame.init()

TILESIZE = 50
WALLSIZE = 8
BOARDSIZE = 9
PLAYER_COLORS = ('forestgreen', 'firebrick', 'gold2', 'royalblue')
PLAYER_SIZE = TILESIZE/2 - 2

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
    global my_turn
    while True:
        time.sleep(5)
        my_turn = not my_turn

def main():
    global my_turn
    my_turn = True
    check_turn = threading.Thread(target=runGame)
    check_turn.start()
    run_game = threading.Thread(target=checkTurn)
    run_game.start()

def runGame():
    resolution = (900, 720)
    
    screen = pygame.display.set_mode(resolution)
    clock = pygame.time.Clock()

    board_surface = create_board_surf()
    board_pos = (resolution[0] - board_surface.get_size()[0]) / 2, 100

    current_player = 'P1'
    player_id = 'P1'
    wall_orientation = 'h'

    wall_positions = [(1,1,'h'), (5,2,'v'), (5,8,'h')]
    player_positions = {
        "P1": (5, 2),
        "P2": (5, 9),
        "P3": (1, 6),
        "P4": (9, 5)
    }

    global my_turn
    font = pygame.font.Font(None, 36)
    black = (0, 0, 0)

    running = True
    while running:
        events = pygame.event.get()
        if my_turn:
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
                
        
        screen.fill(pygame.Color('grey'))
        walls = create_walls(wall_positions, board_pos)
        players = create_players(player_positions, board_pos)
        walls.draw(screen)
        players.draw(screen)
        if my_turn:
            pygame.draw.rect(screen, (255, 0, 0, 50), rect, 2)
        else:
            text_surface = font.render("Please wait for your turn", True, black)
            screen.blit(text_surface, (300, 50))
        screen.blit(board_surface, (board_pos))
        pygame.display.flip()
        clock.tick(60)


if __name__ == '__main__':
    main()
