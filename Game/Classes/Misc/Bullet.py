import math
import pygame

from Classes.Sprite import Sprite
from Utils.Utils import zIndex, scale


# Penetration is .cal

class Bullet(Sprite):
    def __init__(self, x, y, bearing, vel, penetration, game, ttl=10):
        # Bearing is a bearing angle in deg 000 to 359
        self.bearing = bearing
        self.velocity = vel
        self.penetration = penetration
        self.game = game

        self.ttl = ttl
        self.alive = True

        assets = game.assets

        z = zIndex["Bullets"]
        img = scale(assets["Misc"]["Bullet"], 1, smooth=True)

        img = pygame.transform.rotate(img, bearing)

        super().__init__(img, x, y, z)

    def move(self, dt):
        rad = math.radians(self.bearing)
        dx = self.velocity * math.sin(rad)
        dy = -self.velocity * math.cos(rad)

        self.x += dx * dt
        self.y += dy * dt
        self.rect.topleft = (self.x, self.y)

    def move_with_collision(self, dt):
        rad = math.radians(self.bearing)
        dx = self.velocity * math.sin(rad)
        dy = -self.velocity * math.cos(rad)

        dist = self.velocity * dt
        step = 2
        steps = max(1, int(dist / step))

        step_x = dx * dt / steps
        step_y = dy * dt / steps

        for _ in range(steps):
            self.x += step_x
            self.y += step_y
            self.rect.topleft = (self.x, self.y)

            if self.check_collision():
                return True
        return False

    def get_penetrable_walls(self):
        walls = self.game.levelManager.level.sprites["Walls"].sprites
        return {
            k: v for k, v in walls.items()
            if v.strength <= self.penetration
        }

    def get_impenetrable_walls(self):
        walls = self.game.levelManager.level.sprites["Walls"].sprites
        return {
            k: v for k, v in walls.items()
            if v.strength > self.penetration
        }

    def get_enemies(self):
        return self.game.levelManager.level.sprites["Enemies"].sprites.values()

    def check_collision(self):
        impenetrable = self.get_impenetrable_walls()
        penetrable = self.get_penetrable_walls()
        for obstacle in impenetrable.values():
            if self.rect.colliderect(obstacle.rect):
                self.destroy()
                return True

        for obstacle in penetrable.values():
            if self.rect.colliderect(obstacle.rect):
                return True

        for enemy in self.get_enemies():
            if self.rect.colliderect(enemy.rect):
                enemy.take_damage(self.penetration*self.velocity*0.3)
                self.destroy()
                return True

        return False

    def destroy(self):
        self.alive = False
        bullets = self.game.levelManager.level.sprites["Bullets"]
        for k, v in list(bullets.sprites.items()):
            if v is self:
                del bullets.sprites[k]
                break

    def update(self, dt):
        if not self.alive:
            return
        self.move_with_collision(dt)
        self.ttl -= dt
        if self.ttl <= 0:
            self.destroy()
