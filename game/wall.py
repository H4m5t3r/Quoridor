import pygame.sprite

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