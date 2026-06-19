import pygame

from LevelManager.Level import Level
from LevelManager.Manager import LevelManager
from Utils.Utils import create_character, characterColours


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

    def load_assets(self):
        self.generate_character_sprites()

    def generate_character_sprites(self):
        self.assets["Commander"] = create_character(characterColours["Commander"])
        self.assets["Squad"] = create_character(characterColours["Squad"])
        self.assets["Enemy"] = create_character(characterColours["Enemy"])

    def inputs(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update(self, dt):
        self.levelManager.level.update(dt)

    def draw(self):
        self.screen.fill((0, 0, 0))
        self.levelManager.level.draw()

    def run(self):
        while self.running:
            self.screen.fill((0,0,0))

            dt = self.clock.tick(60) / 1000

            self.inputs()
            self.update(dt)
            self.draw()

            pygame.display.flip()
