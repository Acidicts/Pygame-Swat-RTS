import pygame
import os

from LevelManager.Manager import LevelManager
from Utils.Utils import create_character, characterColours, create_from_bitmap, json_to_dict


class Game:
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode((800, 600))
        self.clock = pygame.time.Clock()

        self.running = True

        self.assets = {}
        self.load_assets()

        self.levelManager = LevelManager(self)

        # remove L8tr
        self.levelManager.load_level("test")

        self.weapons = {
            "Guns" : {
                "Primary": {},
                "Secondary": {}
            },
            "Melee" : {},
            "Special" : {},
            "Throwable" : {}
        }

    def load_assets(self):
        self.generate_character_sprites()
        self.load_misc()

    def load_weapon_files(self):
        for dirpath, dirnames, filenames in os.walk("Game/Assets/Weapons/"):
            for filename in filenames:
                if filename.endswith(".json"):
                    # Raw File
                    file_path = os.path.join(dirpath, filename)
                    data = json_to_dict(file_path)
                    self.load_weapon_file(data)

    def load_misc(self):
        self.assets["Misc"] = {
            "Bullet": create_from_bitmap([[(228, 223, 84) for _ in range(6)] for _ in range(2)]),
            "Casing": ""
        }

    def load_weapon_file(self, data):
        for cata in data.values():
            for weapon in cata.values():
                self.create_weapon(weapon)

    def create_weapon(self, data):
        self.weapons[data["Type"]][data["Category"]][data["Name"]] = data

    def generate_character_sprites(self):
        self.assets["Commander"] = create_character(characterColours["Commander"])
        self.assets["Squad"] = create_character(characterColours["Squad"])
        self.assets["Enemy"] = create_character(characterColours["Enemy"])

    def inputs(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update(self, dt):
        if self.levelManager.level:
            self.levelManager.level.update(dt)

    def draw(self):
        self.screen.fill((0, 0, 0))
        if self.levelManager.level:
            self.levelManager.level.draw()

    def run(self):
        while self.running:
            self.screen.fill((0,0,0))

            dt = self.clock.tick(60) / 1000

            self.inputs()
            self.update(dt)
            self.draw()

            pygame.display.flip()
