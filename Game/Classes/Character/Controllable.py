import math
import pygame

from .Armed import Armed
from Utils.Utils import zIndex


class Controllable(Armed):
    def __init__(self, x, y, img, colour, game):
        z = zIndex["Characters"]
        super().__init__(x, y, img, colour, game)

        self.selected = False
        self.colour = colour

    def move_to(self, target_x, target_y, obstacles):
        dx = target_x - self.rect.centerx
        dy = target_y - self.rect.centery
        if abs(dx) > 0.1 or abs(dy) > 0.1:
            self.angle = math.degrees(math.atan2(dy, dx))
        super().move_to(target_x, target_y, obstacles)

    def draw(self, surf):
        super().draw(surf)

        if self.selected:
            pygame.draw.aacircle(surf, self.colour, self.rect.center, 150*0.15, 2)
