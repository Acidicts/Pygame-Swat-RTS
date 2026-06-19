import pygame

from Sprites.PathFindingSprite import PathFindingSprite
from Utils.Utils import zIndex, scale


class Enemy(PathFindingSprite):
    def __init__(self, x, y, assets):
        img = scale(assets["Enemy"], 0.15, smooth=True)
        z = zIndex["Characters"]
        super().__init__(img, x, y, z)
