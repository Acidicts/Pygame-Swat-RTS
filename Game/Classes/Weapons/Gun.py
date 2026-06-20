import pygame

from Classes.Sprite import Sprite


class Gun(Sprite):
    def __init__(self, x, y, game, attributes:dict, img):
        super().__init__(img, x, y)
        self.game = game
        self.attributes = {
            "penetration": attributes["penetration"],
            "velocity": attributes["velocity"],
        }

    def bullet_attributes(self):
        return self.attributes
