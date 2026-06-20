import pygame

from .Armed import Armed
from Utils.Utils import zIndex


class Controllable(Armed):
    def __init__(self, x, y, img, colour, game):
        z = zIndex["Characters"]
        super().__init__(x, y, img, colour, game)

        self.selected = False
        self.colour = colour

    def draw(self, surf):
        super().draw(surf)

        if self.selected:
            pygame.draw.aacircle(surf, self.colour, self.rect.center, 150*0.15, 2)
