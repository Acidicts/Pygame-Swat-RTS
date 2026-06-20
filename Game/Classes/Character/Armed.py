import math
import pygame

from Classes.PathFindingSprite import PathFindingSprite
from Utils.Utils import zIndex


class Armed(PathFindingSprite):
    def __init__(self, x, y, img, colour, game):
        z = zIndex["Characters"]
        super().__init__(img, x, y, z)
        self.colour = colour
        self.angle = 0.0
        self.sees_enemy = False
        self.target_enemy = None
        self.game = game

        self.cone_range = 200
        self.cone_angle = 60

        self.gun_width = 8
        self.gun_length = 30
        self.spm = 30

        self.shot_interval = 60 / self.spm
        self.shot_timer = None

        self.can_shoot = False

        self.health = 120

        self.weapons = {
            "Primary" : None,
            "Secondary" : None,
            "Melee" : None
        }

    def equip(self):
        pass

    def take_damage(self, damage):
        self.health -= damage

    def _get_cone_poly(self):
        half = math.radians(self.cone_angle / 2)
        rad = math.radians(self.angle)
        cx = self.x + self.rect.width / 2
        cy = self.y + self.rect.height / 2

        p0 = (cx, cy)
        p1 = (cx + self.cone_range * math.cos(rad - half),
              cy + self.cone_range * math.sin(rad - half))
        p2 = (cx + self.cone_range * math.cos(rad + half),
              cy + self.cone_range * math.sin(rad + half))
        return [p0, p1, p2]

    def _get_gun_rect(self):
        cx = self.x + self.rect.width / 2
        cy = self.y + self.rect.height / 2
        rad = math.radians(self.angle)

        tip_x = cx + self.gun_length * math.cos(rad)
        tip_y = cy + self.gun_length * math.sin(rad)

        perp_x = -math.sin(rad) * self.gun_width / 2
        perp_y = math.cos(rad) * self.gun_width / 2

        return pygame.Rect(0, 0, 0, 0), [
            (tip_x + perp_x, tip_y + perp_y),
            (tip_x - perp_x, tip_y - perp_y),
            (cx - perp_x, cy - perp_y),
            (cx + perp_x, cy + perp_y)
        ]

    def _point_in_cone(self, px, py):
        cone = self._get_cone_poly()
        cx, cy = cone[0]
        dx = px - cx
        dy = py - cy
        dist = math.hypot(dx, dy)
        if dist > self.cone_range:
            return False

        angle_to = math.degrees(math.atan2(dy, dx)) % 360
        diff = (angle_to - self.angle) % 360
        if diff > 180:
            diff -= 360
        return abs(diff) <= self.cone_angle / 2

    def _check_line_of_sight(self, tx, ty, obstacles):
        cx = self.x + self.rect.width / 2
        cy = self.y + self.rect.height / 2
        dx = tx - cx
        dy = ty - cy
        dist = math.hypot(dx, dy)
        steps = int(dist / 10)

        for i in range(steps + 1):
            t = i / max(steps, 1)
            px = cx + dx * t
            py = cy + dy * t
            for obs in obstacles.values():
                obs_rect = obs.img.get_rect(topleft=(obs.x, obs.y))
                if obs_rect.collidepoint(px, py):
                    return False
        return True

    def update_enemies(self, enemies, obstacles):
        self.sees_enemy = False
        self.target_enemy = None

        cx = self.x + self.rect.width / 2
        cy = self.y + self.rect.height / 2

        best_dist = float('inf')
        best_enemy = None
        for enemy in enemies.values():
            ex = enemy.x + enemy.rect.width / 2
            ey = enemy.y + enemy.rect.height / 2

            if self._check_line_of_sight(ex, ey, obstacles):
                dist = math.hypot(ex - cx, ey - cy)
                if dist < best_dist:
                    best_dist = dist
                    best_enemy = enemy

        if best_enemy:
            ex = best_enemy.x + best_enemy.rect.width / 2
            ey = best_enemy.y + best_enemy.rect.height / 2
            self.angle = math.degrees(math.atan2(ey - cy, ex - cx))

            if self._point_in_cone(ex, ey):
                self.target_enemy = best_enemy
                self.sees_enemy = True

    def draw(self, surf):
        super().draw(surf)

        if self.sees_enemy:
            gun_points = self._get_gun_rect()[1]
            pygame.draw.polygon(surf, self.colour, gun_points)

        if self.can_shoot:
            pygame.draw.aacircle(surf, (120, 6, 6), self.rect.center, 30*0.15)
            pygame.draw.aacircle(surf, (0, 0, 0), self.rect.center, 30*0.15, 2)

    def shoot(self):
        if self.shot_timer is not None:
            return

        self.shot_timer = 0
        self.game.levelManager.level.create_bullet(self.rect.centerx, self.rect.centery, self.angle+90.0, 100, 2, self.game)

    def die(self):
        pass

    def update(self, dt):
        super().update(dt)

        if self.sees_enemy and self.can_shoot:
            self.shoot()

        if self.health <= 0:
            self.die()

        if self.shot_timer is not None:
            self.shot_timer += dt
            if self.shot_timer >= self.shot_interval:
                self.shot_timer = None
