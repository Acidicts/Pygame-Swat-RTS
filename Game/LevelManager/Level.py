import math

import pygame
import pygame.display

from Classes.Character.Commander import Commander
from Classes.Character.Enemy import Enemy
from Classes.Character.SquadMember import SquadMember
from Classes.Misc.Bullet import Bullet
from Classes.Obstacle.Wall import Wall
from Utils.SpriteGroup import SpriteGroup
from Utils.Utils import json_to_dict


class Level:
    def __init__(self, path, game):
        self.path = path
        self.assets = game.assets
        self.game = game

        self.sprites = {
            "Walls" : SpriteGroup(),
            "Enemies" : SpriteGroup(),
            "Squad" : SpriteGroup(),
            "Bullets" : SpriteGroup()
        }

        self.selected = []
        self.drag_start = None
        self.dragging = False
        self.drag_rect = None

    def create_bullet(self, x, y, bearing, vel, penetration, game):
        return self.sprites["Bullets"].add(Bullet(x, y, bearing, vel, penetration, game))


    @staticmethod
    def _get_formation_positions(center_x, center_y, count):
        if count == 1:
            return [(center_x, center_y)]

        spacing = 80
        positions = []

        if count <= 3:
            for i in range(count):
                x = center_x + (i - count // 2) * spacing
                positions.append((x, center_y))
        elif count <= 6:
            rows = 2
            cols = math.ceil(count / rows)
            for r in range(rows):
                for c in range(cols):
                    if len(positions) >= count:
                        break
                    x = center_x + (c - cols // 2) * spacing
                    y = center_y + (r - rows // 2) * spacing
                    positions.append((x, y))
        else:
            rings = 1
            placed = 1
            positions.append((center_x, center_y))
            while placed < count:
                ring = rings
                ring_spacing = spacing
                circumference = 2 * math.pi * ring * ring_spacing
                ring_count = min(int(circumference / ring_spacing), count - placed)
                for i in range(ring_count):
                    angle = (2 * math.pi * i) / ring_count
                    x = center_x + ring * ring_spacing * math.cos(angle)
                    y = center_y + ring * ring_spacing * math.sin(angle)
                    positions.append((x, y))
                    placed += 1
                    if placed >= count:
                        break
                rings += 1

        return positions

    def inputs(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_just_pressed()
        mouse_held = pygame.mouse.get_pressed()

        keys = pygame.key.get_just_pressed()

        if keys[pygame.K_x]:
            for s in self.selected:
                s.can_shoot = not s.can_shoot

        if mouse_click[0]:
            clicked_on_unit = False
            for sprite in self.sprites["Squad"].sprites.values():
                if sprite.rect.collidepoint(mouse_pos[0], mouse_pos[1]):
                    clicked_on_unit = True
                    break

            if clicked_on_unit or not self.selected:
                self.drag_start = mouse_pos
                self.dragging = True

        if self.dragging and mouse_held[0]:
            if self.drag_start is not None and isinstance(self.drag_start, tuple):
                x1 = min(self.drag_start[0], mouse_pos[0])
                y1 = min(self.drag_start[1], mouse_pos[1])
                x2 = max(self.drag_start[0], mouse_pos[0])
                y2 = max(self.drag_start[1], mouse_pos[1])
                self.drag_rect = pygame.Rect(x1, y1, x2 - x1, y2 - y1)

        if not mouse_held[0] and self.dragging:
            self.dragging = False
            if self.drag_rect and self.drag_rect.width > 5 and self.drag_rect.height > 5:
                self.selected = []
                for sprite in self.sprites["Squad"].sprites.values():
                    if self.drag_rect.collidepoint(sprite.rect.center):
                        self.selected.append(sprite)
                        sprite.selected = True
                    else:
                        sprite.selected = False
            else:
                clicked = False
                for sprite in self.sprites["Squad"].sprites.values():
                    if sprite.rect.collidepoint(mouse_pos[0], mouse_pos[1]):
                        self.selected = [sprite]
                        sprite.selected = True
                        clicked = True
                    else:
                        sprite.selected = False
                if not clicked:
                    for s in self.selected:
                        s.selected = False
                    self.selected = []
            self.drag_rect = None

        if mouse_click[0] and self.selected and not self.dragging:
            count = len(self.selected)
            positions = self._get_formation_positions(mouse_pos[0], mouse_pos[1], count)
            for i, sprite in enumerate(self.selected):
                sprite.move_to(positions[i][0], positions[i][1], self.sprites["Walls"].sprites)

        if mouse_click[2]:
            for s in self.selected:
                s.selected = False
            self.selected = []

    def draw(self):
        surf = pygame.display.get_surface()
        if not isinstance(surf, pygame.Surface):
            raise TypeError
        all_sprites = []
        for group in self.sprites.values():
            all_sprites.extend(group.sprites.values())
        for sprite in sorted(all_sprites, key=lambda s: s.z_level):
            sprite.draw(surf)

        if self.dragging and self.drag_rect:
            pygame.draw.rect(surf, (0, 255, 0), self.drag_rect, 1)



    def load(self):
        self.unload()

        data = json_to_dict(self.path)
        for group in self.sprites.keys():
            try:
                for obj in data[group.lower()].values():
                    match group:
                        case "Enemies":
                            self.sprites["Enemies"].add(Enemy(obj[0], obj[1], self.assets, self.game))
                        case "Walls":
                            self.sprites["Walls"].add(Wall(obj[0], obj[1], obj[2], obj[3], obj[4]))
                        case "Squad":
                            if len(self.sprites["Squad"].sprites) == 0:
                                self.sprites["Squad"].add(Commander(obj[0], obj[1], self.assets, self.game))
                            else:
                                self.sprites["Squad"].add(SquadMember(obj[0], obj[1], self.assets, self.game))
            except KeyError:
                pass

    def unload(self):
        for group in self.sprites.values():
            group.clear()

    def update(self, dt):
        self.inputs()

        walls = self.sprites["Walls"].sprites
        enemies = self.sprites["Enemies"].sprites
        squad = self.sprites["Squad"].sprites

        for sprite in enemies.values():
            if hasattr(sprite, 'update_enemies'):
                sprite.update_enemies(squad, walls)

        for sprite in squad.values():
            if hasattr(sprite, 'update_enemies'):
                sprite.update_enemies(enemies, walls)

        for group in self.sprites.values():
            group.update(dt)