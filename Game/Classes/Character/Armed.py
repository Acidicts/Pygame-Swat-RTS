import math
import pygame

from Classes.PathFindingSprite import PathFindingSprite
from Classes.Misc.CoverGeometry import evaluate_cover
from Utils.Utils import zIndex, scale


class Armed(PathFindingSprite):
    def __init__(self, x, y, img, colour, game):
        z = zIndex["Characters"]
        super().__init__(img, x, y, z)
        self.colour = colour
        self.angle = 0.0
        self.sees_enemy = False
        self.target_enemy = None
        self.game = game

        self.vision_range = 350
        self.vision_angle = 90

        self.cone_range = 180
        self.cone_angle = 45

        self.gun_width = 8
        self.gun_length = 30
        self.spm = 30

        self.shot_interval = 60 / self.spm
        self.shot_timer = None

        self.can_shoot = False
        self.in_range = False

        self.alive = True
        self.health = 120

        self.weapons = {
            "Primary" : None,
            "Secondary" : None,
            "Melee" : None
        }

    def equip(self):
        pass

    def die(self):
        self.can_shoot = False
        self.alive = False
        self.img = scale(self.game.assets["Dead"], 0.15, smooth=True)

    def take_damage(self, damage):
        self.health -= damage

    def _get_vision_cone(self):
        half = math.radians(self.vision_angle / 2)
        rad = math.radians(self.angle)
        cx = self.x + self.rect.width / 2
        cy = self.y + self.rect.height / 2

        p0 = (cx, cy)
        p1 = (cx + self.vision_range * math.cos(rad - half),
              cy + self.vision_range * math.sin(rad - half))
        p2 = (cx + self.vision_range * math.cos(rad + half),
              cy + self.vision_range * math.sin(rad + half))
        return [p0, p1, p2]

    def _get_gun_cone(self):
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

    def _point_in_vision_cone(self, px, py):
        cone = self._get_vision_cone()
        cx, cy = cone[0]
        dx = px - cx
        dy = py - cy
        dist = math.hypot(dx, dy)
        if dist > self.vision_range:
            return False

        angle_to = math.degrees(math.atan2(dy, dx)) % 360
        diff = (angle_to - self.angle) % 360
        if diff > 180:
            diff -= 360
        return abs(diff) <= self.vision_angle / 2

    def _point_in_gun_cone(self, px, py):
        cone = self._get_gun_cone()
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

    # ---------- Cover / precise visibility (CoverGeometry integration) ----------

    def cover_exposure(self, shooter, walls, samples_per_edge=6, max_depth=6):
        """
        Full cover-evaluation result for THIS sprite as seen from `shooter`.
        Returns dict: fully_in_cover, fully_exposed, boundaries, corner_visibility.

        This is more expensive than _check_line_of_sight (recursive boundary
        search per edge sample) so don't call it every frame for every pair -
        use it when an Enemy is deciding if its current cover spot still
        holds, not in the per-frame update_enemies vision loop.
        """
        shooter_eye = (shooter.x + shooter.rect.width / 2,
                       shooter.y + shooter.rect.height / 2)
        return evaluate_cover(shooter_eye, self.rect, walls,
                               samples_per_edge, max_depth)

    def is_fully_covered_from(self, shooter, walls, samples_per_edge=6, max_depth=6):
        """True if `shooter` cannot see any part of this sprite's hitbox."""
        return self.cover_exposure(shooter, walls, samples_per_edge, max_depth)["fully_in_cover"]

    def update_enemies(self, enemies, obstacles):
        self.sees_enemy = False
        self.target_enemy = None
        self.in_range = False

        cx = self.x + self.rect.width / 2
        cy = self.y + self.rect.height / 2

        best_dist = float('inf')
        best_enemy = None
        for enemy in enemies.values():
            if enemy.alive is False:
                continue

            ex = enemy.x + enemy.rect.width / 2
            ey = enemy.y + enemy.rect.height / 2
            dist = math.hypot(ex - cx, ey - cy)

            if dist > self.vision_range:
                continue

            if not self._check_line_of_sight(ex, ey, obstacles):
                continue

            if not self._point_in_vision_cone(ex, ey):
                continue

            if dist < best_dist:
                best_dist = dist
                best_enemy = enemy

        if best_enemy:
            ex = best_enemy.x + best_enemy.rect.width / 2
            ey = best_enemy.y + best_enemy.rect.height / 2
            self.angle = math.degrees(math.atan2(ey - cy, ex - cx))

            self.target_enemy = best_enemy
            self.sees_enemy = True
            self.in_range = self._point_in_gun_cone(ex, ey)

    def draw(self, surf):
        super().draw(surf)

        if self.sees_enemy and self.alive:
            gun_points = self._get_gun_rect()[1]
            pygame.draw.polygon(surf, self.colour, gun_points)

            vision_cone = self._get_vision_cone()
            cone_color = (255, 255, 0, 30) if self.in_range else (255, 255, 0, 15)
            cone_surf = pygame.Surface((800, 600), pygame.SRCALPHA)
            pygame.draw.polygon(cone_surf, cone_color, vision_cone)
            surf.blit(cone_surf, (0, 0))

        if self.can_shoot:
            pygame.draw.aacircle(surf, (120, 6, 6), self.rect.center, 30*0.15)
            pygame.draw.aacircle(surf, (0, 0, 0), self.rect.center, 30*0.15, 2)

    def shoot(self):
        if self.shot_timer is not None:
            return

        self.shot_timer = 0
        self.game.levelManager.level.create_bullet(self.rect.centerx, self.rect.centery, self.angle+90.0, 100, 2, self.game, self)

    def update(self, dt):
        if not self.alive:
            return

        super().update(dt)

        if self.sees_enemy and self.in_range and self.can_shoot and self.alive:
            self.shoot()

        if self.health <= 0:
            self.die()

        if self.shot_timer is not None:
            self.shot_timer += dt
            if self.shot_timer >= self.shot_interval:
                self.shot_timer = None