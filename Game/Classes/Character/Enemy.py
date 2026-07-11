import math
import pygame

from Classes.Character.Armed import Armed
from Classes.Character.UtilityAI import UtilityAI, Action
from Classes.Misc.CoverGeometry import evaluate_cover, find_cover_boundaries, is_visible, _wall_rects_from_walls
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

        self.debug_mode = False
        self._debug_cover_result = None
        self._debug_boundaries = []
        self._debug_shooter_pos = None

    def update_ai(self, enemies, walls):
        if not self.alive:
            return

        self.move_cooldown -= 1 / 60

        if self._is_stuck(walls):
            self.stuck_timer += 1 / 60
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

        if not self.cover_target or not self._at_cover(enemies, walls):
            self.cover_target = self._find_cover_position(walls, enemies)
            if self.cover_target:
                new_target = self._quantize_target(self.cover_target[0], self.cover_target[1])
                if new_target != self.move_target:
                    self.move_target = new_target
                    self.move_to(self.cover_target[0], self.cover_target[1], walls)
                    self.move_cooldown = 0.3

    def _do_strafe(self, enemies, walls):
        self.can_shoot = True

        offset_x, offset_y = self.ai.get_strafe_offset(self, 1 / 60)

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

    def _at_cover(self, enemies=None, walls=None):
        """
        True only when we've reached our cover_target AND are fully hidden
        from the nearest enemy. Uses CoverGeometry raycast to verify.
        """
        if not self.cover_target:
            return False
        dist = math.hypot(self.cover_target[0] - self.rect.centerx,
                          self.cover_target[1] - self.rect.centery)
        if dist >= 24:
            return False

        if enemies is not None and walls is not None:
            nearest = self._find_nearest_enemy(enemies)
            if nearest:
                return self.is_fully_covered_from(nearest, walls)

        return False

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
            pygame.draw.aacircle(surf, self.colour, self.rect.center, 30 * 0.15, 2)

        self._draw_debug_hitbox(surf)

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

    def _draw_debug_hitbox(self, surf):
        if not self.debug_mode:
            return

        squad = self.game.levelManager.level.sprites["Squad"].sprites
        walls = self.game.levelManager.level.sprites["Walls"].sprites
        nearest = self._find_nearest_enemy(squad)

        if not nearest:
            return

        shooter_pos = (nearest.x + nearest.rect.width / 2,
                       nearest.y + nearest.rect.height / 2)
        self._debug_shooter_pos = shooter_pos

        cover_result = self.cover_exposure(nearest, walls)
        self._debug_cover_result = cover_result

        hitbox_color = self._get_cover_color(cover_result)
        pygame.draw.rect(surf, hitbox_color, self.rect, 2)

        hitbox_surf = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        fill_color = self._get_cover_fill_color(cover_result)
        pygame.draw.rect(hitbox_surf, fill_color, hitbox_surf.get_rect())
        surf.blit(hitbox_surf, self.rect.topleft)

        wall_rects = _wall_rects_from_walls(walls)
        self._debug_boundaries = find_cover_boundaries(
            shooter_pos, self.rect, wall_rects
        )

        for boundary in self._debug_boundaries:
            bx, by = int(boundary[0]), int(boundary[1])
            pygame.draw.circle(surf, (255, 255, 0), (bx, by), 5)
            pygame.draw.circle(surf, (0, 0, 0), (bx, by), 5, 1)

        can_see = is_visible(
            (self.rect.centerx, self.rect.centery),
            shooter_pos,
            wall_rects
        )
        line_color = (0, 255, 0) if can_see else (255, 0, 0)
        pygame.draw.line(surf, line_color,
                        (int(self.rect.centerx), int(self.rect.centery)),
                        (int(shooter_pos[0]), int(shooter_pos[1])), 1)

        if self.cover_target:
            tx, ty = int(self.cover_target[0]), int(self.cover_target[1])
            pygame.draw.circle(surf, (0, 150, 255), (tx, ty), 6)
            pygame.draw.circle(surf, (0, 0, 0), (tx, ty), 6, 1)

        self._draw_debug_status(surf)

    def _get_cover_color(self, cover_result):
        if cover_result["fully_in_cover"]:
            return (0, 200, 0)
        elif cover_result["fully_exposed"]:
            return (200, 0, 0)
        else:
            visible = sum(cover_result["corner_visibility"])
            if visible <= 1:
                return (200, 200, 0)
            else:
                return (200, 100, 0)

    def _get_cover_fill_color(self, cover_result):
        if cover_result["fully_in_cover"]:
            return (0, 200, 0, 50)
        elif cover_result["fully_exposed"]:
            return (200, 0, 0, 50)
        else:
            return (200, 200, 0, 50)

    def _draw_debug_status(self, surf):
        font = pygame.font.Font(None, 20)
        status_parts = []

        if self._debug_cover_result:
            if self._debug_cover_result["fully_in_cover"]:
                status_parts.append("COVER")
            elif self._debug_cover_result["fully_exposed"]:
                status_parts.append("EXPOSED")
            else:
                visible = sum(self._debug_cover_result["corner_visibility"])
                status_parts.append(f"PARTIAL({visible}/4)")

        if self.current_action:
            status_parts.append(self.current_action.name)

        status_parts.append(f"HP:{int(self.health)}")

        status_text = " | ".join(status_parts)
        text_surface = font.render(status_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(centerx=int(self.rect.centerx),
                                           bottom=int(self.rect.top - 5))

        bg_rect = text_rect.inflate(4, 2)
        pygame.draw.rect(surf, (0, 0, 0), bg_rect)
        pygame.draw.rect(surf, (100, 100, 100), bg_rect, 1)

        surf.blit(text_surface, text_rect)

    def update(self, dt):
        super().update(dt)