import pygame

from Classes.Character.Armed import Armed
from Utils.Utils import scale, characterColours


class Enemy(Armed):
    def __init__(self, x, y, assets, game):
        img = scale(assets["Enemy"], 0.15, smooth=True)
        super().__init__(x, y, img, characterColours["Enemy"], game)

    def draw(self, surf):
        super().draw(surf)

        health_pct = max(0, self.health) / 120
        health_rad = 30 * 0.15 * (1 - health_pct)
        pygame.draw.aacircle(surf, (0, 0, 90), self.rect.center, health_rad)
