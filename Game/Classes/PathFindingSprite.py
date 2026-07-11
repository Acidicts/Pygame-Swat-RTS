import heapq
import math
import random
import pygame

from Classes.Sprite import Sprite


class PathFindingSprite(Sprite):
    CELL_SIZE = 32

    def __init__(self, img, x, y, z):
        super().__init__(img, x, y, z)
        self.path = []
        self.target_x = x
        self.target_y = y
        self.speed = 100
        self._current_speed = 0
        self._acceleration = 400
        self._deceleration = 300
        self._obstacles = {}
        self._path_valid = True
        self._repath_threshold = 64

    def move_to(self, target_x, target_y, obstacles):
        self._obstacles = obstacles
        
        dist = math.hypot(target_x - self.x, target_y - self.y)
        if dist < 16:
            self.path = []
            return

        screen = pygame.display.get_surface()
        screen_w, screen_h = screen.get_size()

        grid_w = screen_w // self.CELL_SIZE
        grid_h = screen_h // self.CELL_SIZE

        sprite_cells_x = max(1, self.rect.width // self.CELL_SIZE)
        sprite_cells_y = max(1, self.rect.height // self.CELL_SIZE)
        pad_x = sprite_cells_x // 2
        pad_y = sprite_cells_y // 2

        blocked = self._build_blocked_set(obstacles, grid_w, grid_h, pad_x, pad_y)

        start = self._pixel_to_grid(self.x, self.y)
        goal = self._pixel_to_grid(target_x, target_y)

        start = self._clamp_to_grid(start, grid_w, grid_h)
        goal = self._clamp_to_grid(goal, grid_w, grid_h)

        if start == goal:
            self.path = []
            return

        if start in blocked:
            start = self._find_nearest_free(start, blocked, grid_w, grid_h)
        if goal in blocked:
            goal = self._find_nearest_free(goal, blocked, grid_w, grid_h)

        grid_path = self._astar(start, goal, blocked, grid_w, grid_h)
        
        if not grid_path:
            return

        self.path = self._smooth_path(grid_path, blocked)
        self.target_x = target_x
        self.target_y = target_y
        self._path_valid = True

    def _build_blocked_set(self, obstacles, grid_w, grid_h, pad_x, pad_y):
        blocked = set()
        for obs in obstacles.values():
            rect = obs.img.get_rect(topleft=(obs.x, obs.y))
            left = max(0, rect.left // self.CELL_SIZE - pad_x)
            right = min(grid_w - 1, rect.right // self.CELL_SIZE + pad_x)
            top = max(0, rect.top // self.CELL_SIZE - pad_y)
            bottom = min(grid_h - 1, rect.bottom // self.CELL_SIZE + pad_y)
            for gx in range(left, right + 1):
                for gy in range(top, bottom + 1):
                    blocked.add((gx, gy))
        return blocked

    def _pixel_to_grid(self, px, py):
        return (int(px) // self.CELL_SIZE, int(py) // self.CELL_SIZE)

    def _grid_to_pixel(self, gx, gy):
        return (gx * self.CELL_SIZE + self.CELL_SIZE // 2,
                gy * self.CELL_SIZE + self.CELL_SIZE // 2)

    def _clamp_to_grid(self, pos, grid_w, grid_h):
        gx, gy = pos
        return (max(0, min(gx, grid_w - 1)), max(0, min(gy, grid_h - 1)))

    def _find_nearest_free(self, pos, blocked, grid_w, grid_h):
        gx, gy = pos
        
        for radius in range(1, 5):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if abs(dx) != radius and abs(dy) != radius:
                        continue
                    nx, ny = gx + dx, gy + dy
                    if 0 <= nx < grid_w and 0 <= ny < grid_h:
                        if (nx, ny) not in blocked:
                            return (nx, ny)
        return pos

    def _smooth_path(self, grid_path, blocked):
        if not grid_path:
            return []

        pixel_path = [self._grid_to_pixel(gx, gy) for gx, gy in grid_path]
        
        if len(pixel_path) <= 2:
            return pixel_path

        smoothed = [pixel_path[0]]
        i = 0

        while i < len(pixel_path) - 1:
            farthest = i + 1
            
            for j in range(len(pixel_path) - 1, i + 1, -1):
                if self._has_clear_line(pixel_path[i], pixel_path[j], blocked):
                    farthest = j
                    break
            
            smoothed.append(pixel_path[farthest])
            i = farthest

        return smoothed

    def _has_clear_line(self, p0, p1, blocked):
        x0, y0 = p0
        x1, y1 = p1
        
        dx = x1 - x0
        dy = y1 - y0
        dist = math.hypot(dx, dy)
        
        if dist < 1:
            return True

        steps = max(int(dist / (self.CELL_SIZE * 0.4)), 1)
        
        for i in range(1, steps):
            t = i / steps
            px = x0 + dx * t
            py = y0 + dy * t
            gx = int(px) // self.CELL_SIZE
            gy = int(py) // self.CELL_SIZE
            if (gx, gy) in blocked:
                return False
        return True

    def _astar(self, start, goal, blocked, grid_w, grid_h):
        open_set = [(0, start)]
        came_from = {}
        g_score = {start: 0}
        closed_set = set()

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == goal:
                return self._reconstruct_path(came_from, current)

            if current in closed_set:
                continue
            closed_set.add(current)

            cx, cy = current
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0),
                           (1, 1), (1, -1), (-1, 1), (-1, -1)):
                nx, ny = cx + dx, cy + dy
                
                if not (0 <= nx < grid_w and 0 <= ny < grid_h):
                    continue
                
                neighbor = (nx, ny)
                
                if neighbor in blocked or neighbor in closed_set:
                    continue

                if dx != 0 and dy != 0:
                    if (cx + dx, cy) in blocked or (cx, cy + dy) in blocked:
                        continue

                move_cost = 1.414 if (dx != 0 and dy != 0) else 1.0
                
                tentative_g = g_score[current] + move_cost
                
                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    
                    h = self._heuristic(neighbor, goal)
                    f = tentative_g + h
                    heapq.heappush(open_set, (f, neighbor))

        return []

    def _heuristic(self, a, b):
        ax, ay = a
        bx, by = b
        dx = abs(ax - bx)
        dy = abs(ay - by)
        return max(dx, dy) + (1.414 - 1) * min(dx, dy)

    def _reconstruct_path(self, came_from, current):
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

    def _collides_at(self, x, y):
        margin = 4
        test_rect = pygame.Rect(x - margin, y - margin, 
                               self.rect.width + margin * 2, 
                               self.rect.height + margin * 2)
        for obs in self._obstacles.values():
            obs_rect = obs.img.get_rect(topleft=(obs.x, obs.y))
            if test_rect.colliderect(obs_rect):
                return True
        return False

    def _validate_path(self):
        if not self.path:
            return True
        
        for px, py in self.path:
            if self._collides_at(px, py):
                return False
        return True

    def update(self, dt):
        if not self.path:
            self._current_speed = max(0, self._current_speed - self._deceleration * dt)
            return

        if not self._validate_path():
            self.path = []
            return

        target_px, target_py = self.path[0]

        dx = target_px - self.x
        dy = target_py - self.y
        dist = math.hypot(dx, dy)

        if dist < 4:
            self.x = target_px
            self.y = target_py
            self.rect.topleft = (self.x, self.y)
            self.path.pop(0)
            return

        target_speed = self.speed
        self._current_speed = min(self._current_speed + self._acceleration * dt, target_speed)

        move_dist = self._current_speed * dt
        
        if move_dist >= dist:
            new_x = target_px
            new_y = target_py
        else:
            ratio = move_dist / dist
            new_x = self.x + dx * ratio
            new_y = self.y + dy * ratio

        if not self._collides_at(new_x, new_y):
            self.x = new_x
            self.y = new_y
            self.rect.topleft = (self.x, self.y)
        else:
            alt_x = self.x + dx * 0.5
            alt_y = self.y + dy * 0.5
            if not self._collides_at(alt_x, alt_y):
                self.x = alt_x
                self.y = alt_y
                self.rect.topleft = (self.x, self.y)
            else:
                self.path = []
                self._current_speed = 0
