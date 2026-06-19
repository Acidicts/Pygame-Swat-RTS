import pygame

from Sprites.PathFindingSprite import PathFindingSprite
from Utils.Utils import zIndex


class Controllable(PathFindingSprite):
    def __init__(self, x, y, img, colour):
        z = zIndex["Characters"]
        super().__init__(img, x, y, z)

        self.selected = False
        self.colour = colour

    def draw(self, surf):
        surf.blit(self.img, (self.x, self.y))
        if self.selected:
            pygame.draw.aacircle(surf, self.colour, self.rect.center, 150*0.15, 2)
