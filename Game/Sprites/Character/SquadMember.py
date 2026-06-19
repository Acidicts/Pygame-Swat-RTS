from Sprites.Character.Controllable import Controllable
from Utils.Utils import scale, characterColours


class SquadMember(Controllable):
    def __init__(self, x, y, assets):
        img = scale(assets["Squad"], 0.15, smooth=True)
        super().__init__(x, y, img, characterColours["Squad"])
