import math
import pygame

from Classes.Character.Armed import Armed
from Classes.Character.UtilityAI import UtilityAI, Action
from Utils.Utils import scale, characterColours


class Enemy(Armed):
    def __init__(self, x, y, assets, game, traits=None):
        img = scale(assets["Enemy"], 0.15, smooth=True)
        super().__init__(x, y, img, characterColours["Enemy"], game)

        self.can_shoot = True
        self.ai = UtilityAI(traits)
        
        self.cover_target = None
        self.current_action = None
        self.move_target = None
        self.move_cooldown = 0
        self.stuck_timer = 0

    def update_ai(self, enemies, walls):
        if not self.alive:
            return

        self.move_cooldown -= 1/60

        if self._is_stuck(walls):
            self.stuck_timer += 1/60
            if self.stuck_timer > 0.5:
                self._unstuck(walls)
                self.stuck_timer = 0
            return
        else:
            self.stuck_timer = 0

        action = self.ai.decide(self, enemies, walls)
        action_changed = action != self.current_action
        self.current_action = action

        if action_changed or self.move_cooldown <= 0:
            self._execute_action(action, enemies, walls)

    def _execute_action(self, action, enemies, walls):
        match action:
            case Action.ATTACK:
                self._do_attack(enemies, walls)
            case Action.RETREAT:
                self._do_retreat(enemies, walls)
            case Action.CHARGE:
                self._do_charge(enemies, walls)
            case Action.SEEK_COVER:
                self._do_seek_cover(walls, enemies)
            case Action.STRAFE:
                self._do_strafe(enemies, walls)
            case Action.PATROL:
                self._do_patrol()

    def _do_attack(self, enemies, walls):
        self.can_shoot = True
        self.cover_target = None

    def _do_retreat(self, enemies, walls):
        self.can_shoot = False
        
        nearest = self._find_nearest_enemy(enemies)
        if not nearest:
            return

        enemy_cx = nearest.x + nearest.rect.width / 2
        enemy_cy = nearest.y + nearest.rect.height / 2
        
        dx = self.rect.centerx - enemy_cx
        dy = self.rect.centery - enemy_cy
        dist = math.hypot(dx, dy)
        
        if dist > 0:
            dx /= dist
            dy /= dist
        
        for retreat_dist in [120, 80, 40]:
            target_x = self.rect.centerx + dx * retreat_dist
            target_y = self.rect.centery + dy * retreat_dist
            
            if not self._position_in_wall(target_x, target_y, walls):
                new_target = self._quantize_target(target_x, target_y)
                if new_target != self.move_target:
                    self.move_target = new_target
                    self.move_to(target_x, target_y, walls)
                    self.move_cooldown = 0.3
                return

        self._find_safe_retreat(dx, dy, walls)

    def _find_safe_retreat(self, preferred_dx, preferred_dy, walls):
        cx = self.rect.centerx
        cy = self.rect.centery
        
        for angle_offset in [0, 45, -45, 90, -90, 135, -135, 180]:
            angle = math.atan2(preferred_dy, preferred_dx) + math.radians(angle_offset)
            
            for dist in [100, 70, 40]:
                test_x = cx + math.cos(angle) * dist
                test_y = cy + math.sin(angle) * dist
                
                if not self._position_in_wall(test_x, test_y, walls):
                    new_target = self._quantize_target(test_x, test_y)
                    if new_target != self.move_target:
                        self.move_target = new_target
                        self.move_to(test_x, test_y, walls)
                        self.move_cooldown = 0.3
                        return

    def _do_charge(self, enemies, walls):
        self.can_shoot = True
        
        nearest = self._find_nearest_enemy(enemies)
        if not nearest:
            return

        target_x = nearest.x + nearest.rect.width / 2
        target_y = nearest.y + nearest.rect.height / 2
        
        new_target = self._quantize_target(target_x, target_y)
        if new_target != self.move_target:
            self.move_target = new_target
            self.move_to(target_x, target_y, walls)
            self.move_cooldown = 0.2

    def _do_seek_cover(self, walls, enemies):
        self.can_shoot = False
        
        if not self.cover_target or self._at_cover():
            self.cover_target = self._find_cover_position(walls, enemies)
        
        if self.cover_target:
            new_target = self._quantize_target(self.cover_target[0], self.cover_target[1])
            if new_target != self.move_target:
                self.move_target = new_target
                self.move_to(self.cover_target[0], self.cover_target[1], walls)
                self.move_cooldown = 0.3

    def _do_strafe(self, enemies, walls):
        self.can_shoot = True
        
        offset_x, offset_y = self.ai.get_strafe_offset(self, 1/60)
        
        target_x = self.rect.centerx + offset_x
        target_y = self.rect.centery + offset_y
        
        if not self._position_in_wall(target_x, target_y, walls):
            new_target = self._quantize_target(target_x, target_y)
            if new_target != self.move_target:
                self.move_target = new_target
                self.move_to(target_x, target_y, walls)
                self.move_cooldown = 0.1

    def _do_patrol(self):
        self.can_shoot = False
        self.move_target = None
        self.cover_target = None

    def _quantize_target(self, x, y):
        return (int(x // 32), int(y // 32))

    def _find_nearest_enemy(self, enemies):
        nearest = None
        min_dist = float('inf')
        
        for e in enemies.values():
            if e.alive:
                dist = math.hypot(e.x - self.x, e.y - self.y)
                if dist < min_dist:
                    min_dist = dist
                    nearest = e
        
        return nearest

    def _at_cover(self):
        if not self.cover_target:
            return False
        dist = math.hypot(self.cover_target[0] - self.rect.centerx, 
                         self.cover_target[1] - self.rect.centery)
        return dist < 24

    def _find_cover_position(self, walls, enemies):
        nearest_enemy = self._find_nearest_enemy(enemies)
        if not nearest_enemy or not walls:
            return None

        best_pos = None
        best_score = -float('inf')

        enemy_cx = nearest_enemy.x + nearest_enemy.rect.width / 2
        enemy_cy = nearest_enemy.y + nearest_enemy.rect.height / 2

        for wall in walls.values():
            wall_x = wall.x
            wall_y = wall.y
            wall_w = wall.rect.width
            wall_h = wall.rect.height
            wall_cx = wall_x + wall_w / 2
            wall_cy = wall_y + wall_h / 2

            dx_to_enemy = enemy_cx - wall_cx
            dy_to_enemy = enemy_cy - wall_cy
            dist_to_enemy = math.hypot(dx_to_enemy, dy_to_enemy)

            if dist_to_enemy < 60:
                continue

            margin = 35
            
            candidate_positions = [
                (wall_x - margin, wall_y + wall_h / 2),
                (wall_x + wall_w + margin, wall_y + wall_h / 2),
                (wall_x + wall_w / 2, wall_y - margin),
                (wall_x + wall_w / 2, wall_y + wall_h + margin),
                (wall_x - margin, wall_y - margin),
                (wall_x + wall_w + margin, wall_y - margin),
                (wall_x - margin, wall_y + wall_h + margin),
                (wall_x + wall_w + margin, wall_y + wall_h + margin)
            ]

            for pos_x, pos_y in candidate_positions:
                if self._position_in_wall(pos_x, pos_y, walls):
                    continue

                dist_to_wall = math.hypot(pos_x - wall_cx, pos_y - wall_cy)
                if dist_to_wall > 150:
                    continue

                cover_angle = math.atan2(wall_cy - pos_y, wall_cx - pos_x)
                angle_to_enemy = math.atan2(enemy_cy - pos_y, enemy_cx - pos_x)
                angle_diff = abs(cover_angle - angle_to_enemy)
                if angle_diff > math.pi:
                    angle_diff = 2 * math.pi - angle_diff
                
                angle_score = 1.0 - (angle_diff / math.pi)
                dist_score = 1.0 - (dist_to_wall / 150)
                enemy_dist_score = 1.0 - (dist_to_enemy / 400)
                
                score = angle_score * 2 + dist_score + enemy_dist_score

                if score > best_score:
                    best_score = score
                    best_pos = (pos_x, pos_y)

        return best_pos

    def _position_in_wall(self, x, y, walls):
        margin = 20
        test_rect = pygame.Rect(x - margin, y - margin, margin * 2, margin * 2)
        for wall in walls.values():
            wall_rect = wall.img.get_rect(topleft=(wall.x, wall.y))
            if test_rect.colliderect(wall_rect):
                return True
        return False

    def _is_stuck(self, walls):
        return self._position_in_wall(self.rect.centerx, self.rect.centery, walls)

    def _unstuck(self, walls):
        cx = self.rect.centerx
        cy = self.rect.centery
        
        for dist in [48, 72, 96]:
            for angle_deg in range(0, 360, 30):
                angle = math.radians(angle_deg)
                test_x = cx + math.cos(angle) * dist
                test_y = cy + math.sin(angle) * dist
                
                if not self._position_in_wall(test_x, test_y, walls):
                    new_target = self._quantize_target(test_x, test_y)
                    self.move_target = new_target
                    self.move_to(test_x, test_y, walls)
                    return

    def draw(self, surf):
        super().draw(surf)

        health_pct = max(0, self.health) / 120
        health_rad = 30 * 0.15 * (1 - health_pct)
        pygame.draw.aacircle(surf, (0, 0, 90), self.rect.center, health_rad)

        if not self.can_shoot:
            pygame.draw.aacircle(surf, self.colour, self.rect.center, 30*0.15, 2)

        # self._draw_ai_indicator(surf)

    def _draw_ai_indicator(self, surf):
        colors = {
            Action.ATTACK: (255, 0, 0),
            Action.RETREAT: (0, 255, 0),
            Action.CHARGE: (255, 165, 0),
            Action.SEEK_COVER: (0, 0, 255),
            Action.STRAFE: (255, 255, 0),
            Action.PATROL: (128, 128, 128)
        }
        
        color = colors.get(self.current_action, (255, 255, 255))
        offset_y = -25
        
        pygame.draw.circle(surf, color, 
                          (int(self.rect.centerx), int(self.rect.centery + offset_y)), 
                          4)
