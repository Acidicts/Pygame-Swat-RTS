import pygame
import os
from Utils.Utils import json_to_dict, BASE_PATH
from LevelManager.Level import Level


class LevelManager:
    def __init__(self, game):
        self.screen = pygame.display.get_surface()
        self.game = game

        self.level = None
        self.levels = {}
        self.load_levels()

    def load_level(self, name):
        self.level = self.levels[name]

        if type(self.level) != Level:
            raise TypeError

        self.level.load()

    def draw(self):
        if type(self.level) != Level:
            pass
        self.level.draw()

    def update(self, dt):
        if type(self.level) != Level:
            pass
        self.level.update(dt)

    def load_levels(self, path=os.path.join(BASE_PATH, "Assets", "Levels")):
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                if filename.endswith(".json"):
                    file_path = os.path.join(dirpath, filename)
                    data = json_to_dict(file_path)
                    self.levels[data["name"]] = Level(file_path, self.game.assets)
