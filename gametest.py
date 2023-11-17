import pygame

pygame.init()
pygame.font.init()

TILESIZE = 50
WALLSIZE = 8
BOARDSIZE = 9
FONT = pygame.font.SysFont('Arial', 20)
FONT_COLOR = pygame.Color('black')
PLAYER_COLORS = ('forestgreen', 'firebrick', 'gold2', 'royalblue')
PLAYER_SIZE = TILESIZE/2 - 2

class Wall(pygame.sprite.Sprite):
    def __init__(self, pos, width, height, color, orientation) -> None:
        super().__init__()
        # flip width and height for vertical wall
        if orientation == 'h':
            self.width = height
            self.height = width
        else:
            self.width = width
            self.height = height

        self.image = pygame.Surface([self.width, self.height])
        self.image.fill(color)
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.center = pos

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, radius, color, id) -> None:
        super().__init__()
        self.id = id
        self.radius = radius

        # Draw circle
        self.image = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA, 32)
        self.rect  = self.image.get_rect(center=pos)
        pygame.draw.circle(self.image, color, (self.radius, self.radius), self.radius)

        # Add text
        textsurface = FONT.render(id, True, FONT_COLOR)
        textrect = textsurface.get_rect(center=self.image.get_rect().center)
        self.image.blit(textsurface, textrect)
        self.rect = self.image.get_rect(center=pos)


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

def get_player_coordinates(pos, offset):
    x = pos[0] * (TILESIZE + WALLSIZE) - (TILESIZE / 2) - WALLSIZE + offset[0]
    y = pos[1] * (TILESIZE + WALLSIZE) - (TILESIZE / 2) - WALLSIZE + offset[1]
    return (x, y)

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
    for i in range(len(player_positions)):
        pos = get_player_coordinates(player_positions[i], board_pos)
        color = pygame.Color(PLAYER_COLORS[i])
        player_text = f"P{i+1}"
        player = Player(pos, PLAYER_SIZE, color, player_text)
        players.add(player)
    return players

def main():
    resolution = (900, 720)
    
    screen = pygame.display.set_mode(resolution)
    clock = pygame.time.Clock()

    board_surface = create_board_surf()
    board_pos = (resolution[0] - board_surface.get_size()[0]) / 2, 100

    wall_positions = [(1,1,'h'), (5,2,'v'), (5,8,'h')]
    player_positions = [(5, 2), (5, 9), (1, 6), (9,5)]

    while True:
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                return
        screen.fill(pygame.Color('grey'))
        walls = create_walls(wall_positions, board_pos)
        players = create_players(player_positions, board_pos)
        walls.draw(screen)
        players.draw(screen)
        screen.blit(board_surface, (board_pos))
        pygame.display.flip()
        clock.tick(60)

if __name__ == '__main__':
    main()
