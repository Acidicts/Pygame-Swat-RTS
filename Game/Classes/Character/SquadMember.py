import random
import pygame

from Classes.Character.Controllable import Controllable
from Utils.Utils import scale, characterColours


class SquadMember(Controllable):
    def __init__(self, x, y, assets, game, commander):
        img = scale(assets["Squad"], 0.15, smooth=True)
        super().__init__(x, y, img, characterColours["Squad"], game)

        self.commander = commander

    def has_connection(self):
        x1, y1 = self.rect.center
        x2, y2 = self.commander.rect.center

        walls = self.game.levelManager.level.sprites["Walls"].sprites.values()
        signal_strength = 1

        for wall in walls:
            if self._line_intersects_rect(x1, y1, x2, y2, wall.rect):
                signal_strength -= wall.signal_blocking

        if signal_strength > 0.3:
            return True
        elif signal_strength > 0:
            return random.random() < 0.5
        else:
            return False

    def _line_intersects_rect(self, x1, y1, x2, y2, rect):
        left = self._line_intersects_line(x1, y1, x2, y2, rect.left, rect.top, rect.left, rect.bottom)
        right = self._line_intersects_line(x1, y1, x2, y2, rect.right, rect.top, rect.right, rect.bottom)
        top = self._line_intersects_line(x1, y1, x2, y2, rect.left, rect.top, rect.right, rect.top)
        bottom = self._line_intersects_line(x1, y1, x2, y2, rect.left, rect.bottom, rect.right, rect.bottom)

        return left or right or top or bottom

    def _line_intersects_line(self, x1, y1, x2, y2, x3, y3, x4, y4):
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if denom == 0:
            return False

        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

        return 0 <= t <= 1 and 0 <= u <= 1

