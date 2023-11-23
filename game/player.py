import pygame

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, radius, color, id) -> None:
        pygame.font.init()
        super().__init__()
        self.id = id
        self.radius = radius
        FONT = pygame.font.SysFont('Arial', 20)
        FONT_COLOR = pygame.Color('black')

        # Draw circle
        self.image = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA, 32)
        self.rect  = self.image.get_rect(center=pos)
        pygame.draw.circle(self.image, color, (self.radius, self.radius), self.radius)

        # Add text
        textsurface = FONT.render(id, True, FONT_COLOR)
        textrect = textsurface.get_rect(center=self.image.get_rect().center)
        self.image.blit(textsurface, textrect)
        self.rect = self.image.get_rect(center=pos)