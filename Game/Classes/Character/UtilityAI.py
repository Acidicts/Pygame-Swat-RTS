import math
from enum import Enum, auto


class Action(Enum):
    PATROL = auto()
    ATTACK = auto()
    RETREAT = auto()
    CHARGE = auto()
    SEEK_COVER = auto()
    STRAFE = auto()


class UtilityAI:
    def __init__(self, traits=None):
        self.traits = traits or {
            "aggression": 0.5,
            "caution": 0.5,
            "discipline": 0.5
        }
        
        self.current_action = Action.PATROL
        self.last_action = None
        self.action_cooldown = 0
        self.min_action_time = 1.0
        
        self.target_enemy = None
        self.strafe_direction = 1
        self.strafe_timer = 0

    def decide(self, enemy, enemies, walls):
        if not enemy.alive:
            return self.current_action

        self.action_cooldown -= 1/60
        
        if self.action_cooldown > 0:
            return self.current_action

        scores = {
            Action.ATTACK: self._attack_score(enemy, enemies),
            Action.RETREAT: self._retreat_score(enemy, enemies),
            Action.CHARGE: self._charge_score(enemy, enemies),
            Action.SEEK_COVER: self._cover_score(enemy, walls, enemies),
            Action.STRAFE: self._strafe_score(enemy, enemies),
            Action.PATROL: self._patrol_score(enemy)
        }

        best_action = max(scores, key=scores.get)
        
        if best_action != self.current_action:
            if self.current_action != Action.PATROL:
                self.last_action = self.current_action
            self.current_action = best_action
            self.action_cooldown = self.min_action_time

        return self.current_action

    def get_strafe_offset(self, enemy, dt):
        if self.current_action != Action.STRAFE:
            return 0, 0
            
        self.strafe_timer += dt
        if self.strafe_timer > 2.0:
            self.strafe_direction *= -1
            self.strafe_timer = 0
        
        speed = 60
        offset_x = self.strafe_direction * speed * dt
        
        return offset_x, 0

    def _attack_score(self, enemy, enemies):
        if not enemy.sees_enemy:
            return 0.0

        dist = self._distance_to_nearest_enemy(enemy, enemies)
        if dist > 500:
            return 0.0

        health_score = enemy.health / 120
        aggression = self.traits["aggression"]
        
        optimal_dist = 250
        dist_factor = 1.0 - abs(dist - optimal_dist) / optimal_dist
        
        return 0.3 + (health_score * aggression * dist_factor * 0.4)

    def _retreat_score(self, enemy, enemies):
        if not enemy.sees_enemy:
            return 0.0

        health_score = 1 - (enemy.health / 120)
        caution = self.traits["caution"]
        
        dist = self._distance_to_nearest_enemy(enemy, enemies)
        proximity = max(0, 1 - dist / 300)
        
        base_score = 0.2 * caution
        health_factor = health_score * 0.4 * caution
        proximity_factor = proximity * 0.3 * caution
        
        return base_score + health_factor + proximity_factor

    def _charge_score(self, enemy, enemies):
        if not enemy.sees_enemy:
            return 0.0

        dist = self._distance_to_nearest_enemy(enemy, enemies)
        if dist > 300:
            return 0.0

        health_score = enemy.health / 120
        aggression = self.traits["aggression"]
        
        close_bonus = 0.3 if dist < 150 else 0.0
        
        return close_bonus + (health_score * aggression * 0.3)

    def _cover_score(self, enemy, walls, enemies):
        if not walls or not enemy.sees_enemy:
            return 0.0

        caution = self.traits["caution"]
        health_score = 1 - (enemy.health / 120)
        
        has_cover = self._has_nearby_cover(enemy, walls)
        if not has_cover:
            return 0.0
        
        base_score = 0.25 * caution
        health_factor = health_score * 0.3 * caution
        
        return base_score + health_factor

    def _strafe_score(self, enemy, enemies):
        if not enemy.sees_enemy:
            return 0.0

        dist = self._distance_to_nearest_enemy(enemy, enemies)
        if dist > 400 or dist < 100:
            return 0.0

        health_score = enemy.health / 120
        aggression = self.traits["aggression"]
        
        return 0.2 + (health_score * aggression * 0.2)

    def _patrol_score(self, enemy):
        if enemy.sees_enemy:
            return 0.0
        
        discipline = self.traits["discipline"]
        return 0.4 + (discipline * 0.2)

    def _distance_to_nearest_enemy(self, enemy, enemies):
        min_dist = float('inf')
        for e in enemies.values():
            if e.alive:
                dist = math.hypot(e.x - enemy.x, e.y - enemy.y)
                min_dist = min(min_dist, dist)
        return min_dist if min_dist != float('inf') else 1000

    def _has_nearby_cover(self, enemy, walls):
        for wall in walls.values():
            dist = math.hypot(wall.x - enemy.x, wall.y - enemy.y)
            if dist < 120:
                return True
        return False
