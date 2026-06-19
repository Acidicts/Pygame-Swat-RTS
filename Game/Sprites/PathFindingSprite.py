import heapq
import random
import pygame

from Sprites.Sprite import Sprite


class PathFindingSprite(Sprite):
    CELL_SIZE = 32

    def __init__(self, img, x, y, z):
        super().__init__(img, x, y, z)
        self.path = []
        self.target_x = x
        self.target_y = y
        self.speed = 100
        self.speed_var = 0.3
        self._step_timer = 0
        self._step_interval = 0.3
        self._current_speed = self.speed

    def move_to(self, target_x, target_y, obstacles):
        screen = pygame.display.get_surface()
        screen_w, screen_h = screen.get_size()

        grid_w = screen_w // self.CELL_SIZE
        grid_h = screen_h // self.CELL_SIZE

        blocked = set()
        for obs in obstacles.values():
            rect = obs.img.get_rect(topleft=(obs.x, obs.y))
            left = max(0, rect.left // self.CELL_SIZE)
            right = min(grid_w - 1, rect.right // self.CELL_SIZE)
            top = max(0, rect.top // self.CELL_SIZE)
            bottom = min(grid_h - 1, rect.bottom // self.CELL_SIZE)
            for gx in range(left, right + 1):
                for gy in range(top, bottom + 1):
                    blocked.add((gx, gy))

        start = (int(self.x) // self.CELL_SIZE, int(self.y) // self.CELL_SIZE)
        goal = (int(target_x) // self.CELL_SIZE, int(target_y) // self.CELL_SIZE)

        grid_path = self._astar(start, goal, blocked, grid_w, grid_h)
        self.path = self._smooth_path(grid_path, blocked)
        self.target_x = target_x
        self.target_y = target_y

    def _grid_to_pixel(self, gx, gy):
        return (gx * self.CELL_SIZE + self.CELL_SIZE // 2,
                gy * self.CELL_SIZE + self.CELL_SIZE // 2)

    def _smooth_path(self, grid_path, blocked):
        if not grid_path:
            return []

        pixel_path = [self._grid_to_pixel(gx, gy) for gx, gy in grid_path]
        smoothed = [pixel_path[0]]

        i = 0
        while i < len(pixel_path) - 1:
            j = len(pixel_path) - 1
            while j > i + 1:
                if self._has_line_of_sight(pixel_path[i], pixel_path[j], blocked):
                    break
                j -= 1
            smoothed.append(pixel_path[j])
            i = j

        return smoothed

    def _has_line_of_sight(self, p0, p1, blocked):
        x0, y0 = p0
        x1, y1 = p1
        dx = x1 - x0
        dy = y1 - y0
        steps = max(abs(dx), abs(dy)) // (self.CELL_SIZE // 2)
        if steps == 0:
            return True

        for i in range(int(steps) + 1):
            t = i / steps
            px = x0 + dx * t
            py = y0 + dy * t
            gx = int(px) // self.CELL_SIZE
            gy = int(py) // self.CELL_SIZE
            if (gx, gy) in blocked:
                return False
        return True

    def _astar(self, start, goal, blocked, grid_w, grid_h):
        if start in blocked or goal in blocked:
            return []

        open_set = [(0, start)]
        came_from = {}
        g_score = {start: 0}

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == goal:
                return self._reconstruct_path(came_from, current)

            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0),
                           (1, 1), (1, -1), (-1, 1), (-1, -1)):
                nx, ny = current[0] + dx, current[1] + dy
                if 0 <= nx < grid_w and 0 <= ny < grid_h:
                    if (nx, ny) in blocked:
                        continue
                    if abs(dx) + abs(dy) == 2:
                        if (current[0] + dx, current[1]) in blocked or \
                           (current[0], current[1] + dy) in blocked:
                            continue
                    move_cost = 1.414 if (dx != 0 and dy != 0) else 1
                    tentative = g_score[current] + move_cost
                    if tentative < g_score.get((nx, ny), float('inf')):
                        came_from[(nx, ny)] = current
                        g_score[(nx, ny)] = tentative
                        h = ((nx - goal[0]) ** 2 + (ny - goal[1]) ** 2) ** 0.5
                        heapq.heappush(open_set, (tentative + h, (nx, ny)))

        return []

    def _reconstruct_path(self, came_from, current):
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

    def update(self, dt):
        if not self.path:
            return

        self._step_timer += dt
        if self._step_timer >= self._step_interval:
            self._step_timer -= self._step_interval
            self._current_speed = self.speed * random.uniform(1 - self.speed_var, 1 + self.speed_var)

        target_px, target_py = self.path[0]

        dx = target_px - self.x
        dy = target_py - self.y
        dist = (dx ** 2 + dy ** 2) ** 0.5

        if dist < self._current_speed * dt:
            self.x = target_px
            self.y = target_py
            self.path.pop(0)
        else:
            self.x += (dx / dist) * self._current_speed * dt
            self.y += (dy / dist) * self._current_speed * dt

        self.rect.topleft = (self.x, self.y)

