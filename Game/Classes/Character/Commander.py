from Classes.Character.Controllable import Controllable
from Utils.Utils import scale, characterColours


class Commander(Controllable):
    def __init__(self, x, y, assets, game):
        img = scale(assets["Commander"], 0.15, smooth=True)
        super().__init__(x, y, img, characterColours["Commander"], game)

