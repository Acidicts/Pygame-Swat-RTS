import pygame

from Classes.SolidSprite import SolidSprite
from Utils.Utils import zIndex


class Wall(SolidSprite):
    def __init__(self, x, y, w, h, strength, sig_blocking=0.1):
        img = pygame.Surface((w, h))
        img.fill((0, 0, 150))

        z = zIndex["Walls"]
        super().__init__(img, x, y, z)

        self.strength = strength
        self.signal_blocking = sig_blocking
