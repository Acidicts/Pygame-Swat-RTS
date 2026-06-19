from operator import truediv

import pygame.display

from Sprites.Character.Commander import Commander
from Sprites.Character.Enemy import Enemy
from Sprites.Character.SquadMember import SquadMember
from Sprites.Obstacle.Wall import Wall
from Utils.SpriteGroup import SpriteGroup
from Utils.Utils import json_to_dict


class Level:
    def __init__(self, path, assets):
        self.path = path
        self.assets = assets

        self.sprites = {
            "Walls" : SpriteGroup(),
            "Enemies" : SpriteGroup(),
            "Squad" : SpriteGroup()
        }

        self.selected = None

    def inputs(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_just_pressed()

        if self.selected:
            self.selected.selected = True

        if mouse_click[0] and self.selected is None:
            for sprite in self.sprites["Squad"].sprites.values():
                if sprite.rect.collidepoint(mouse_pos[0], mouse_pos[1]):
                    self.selected = sprite
                else:
                    sprite.selected = False
        elif mouse_click[0] and self.selected is not None:
            self.selected.move_to(mouse_pos[0], mouse_pos[1], self.sprites["Walls"].sprites)
        elif mouse_click[2]:
            self.selected.selected = False
            self.selected = None



    def load(self):
        self.unload()

        data = json_to_dict(self.path)
        for group in self.sprites.keys():
            for obj in data[group.lower()].values():
                match group:
                    case "Enemies":
                        self.sprites["Enemies"].add(Enemy(obj[0], obj[1], self.assets))
                    case "Walls":
                        self.sprites["Walls"].add(Wall(obj[0], obj[1], obj[2], obj[3], obj[4]))
                    case "Squad":
                        if len(self.sprites["Squad"].sprites) == 0:
                            self.sprites["Squad"].add(Commander(obj[0], obj[1], self.assets))
                        else:
                            self.sprites["Squad"].add(SquadMember(obj[0], obj[1], self.assets))

    def unload(self):
        for group in self.sprites.values():
            group.clear()

    def draw(self):
        surf = pygame.display.get_surface()
        all_sprites = []
        for group in self.sprites.values():
            all_sprites.extend(group.sprites.values())
        for sprite in sorted(all_sprites, key=lambda s: s.z_level):
            sprite.draw(surf)

    def update(self, dt):
        self.inputs()

        for group in self.sprites.values():
            group.update(dt)
