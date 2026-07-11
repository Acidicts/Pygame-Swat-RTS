"""
CoverGeometry.py

Raycast-based cover/visibility system for SwatRTS.

Drop this file in Classes/ (next to Sprite.py) and import it as:
    from Classes.CoverGeometry import evaluate_cover

Works directly with the wall-rect convention already used across the
codebase: obs.img.get_rect(topleft=(obs.x, obs.y))
"""

import pygame


# ---------- Core segment-vs-rect raycasting ----------

def _ccw(a, b, c):
    return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])


def segment_intersect(p1, p2, p3, p4):
    """True if segment p1-p2 intersects segment p3-p4."""
    return (_ccw(p1, p3, p4) != _ccw(p2, p3, p4)) and \
           (_ccw(p1, p2, p3) != _ccw(p1, p2, p4))


def ray_blocked_by_rect(origin, target, rect: pygame.Rect):
    """True if the segment origin->target is blocked by rect's edges."""
    corners = [
        (rect.left, rect.top), (rect.right, rect.top),
        (rect.right, rect.bottom), (rect.left, rect.bottom),
    ]
    edges = list(zip(corners, corners[1:] + corners[:1]))
    for a, b in edges:
        if segment_intersect(origin, target, a, b):
            return True
    return False


def is_visible(shooter_pos, point, wall_rects):
    """
    wall_rects: iterable of pygame.Rect. Pass already-computed rects,
    not raw wall objects, so this stays decoupled from Sprite internals.
    """
    for rect in wall_rects:
        if ray_blocked_by_rect(shooter_pos, point, rect):
            return False
    return True


def _lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


# ---------- Recursive binary search for the visibility boundary ----------

DEFAULT_MAX_DEPTH = 6


def _recursive_boundary_search(shooter_pos, point_a, point_b, vis_a,
                                wall_rects, depth, max_depth):
    mid = _lerp(point_a, point_b, 0.5)

    if depth >= max_depth:
        return mid

    vis_mid = is_visible(shooter_pos, mid, wall_rects)

    if vis_mid == vis_a:
        return _recursive_boundary_search(
            shooter_pos, mid, point_b, vis_mid, wall_rects, depth + 1, max_depth
        )
    else:
        return _recursive_boundary_search(
            shooter_pos, point_a, mid, vis_a, wall_rects, depth + 1, max_depth
        )


def find_visibility_boundary(shooter_pos, point_a, point_b, wall_rects,
                              max_depth=DEFAULT_MAX_DEPTH):
    """
    point_a/point_b must be on opposite sides of visibility.
    Recursively bisects a->b, max_depth levels deep, converging on the
    exact point where visibility flips. Returns None if a and b are on
    the same side (no transition to find).
    """
    vis_a = is_visible(shooter_pos, point_a, wall_rects)
    vis_b = is_visible(shooter_pos, point_b, wall_rects)

    if vis_a == vis_b:
        return None

    return _recursive_boundary_search(
        shooter_pos, point_a, point_b, vis_a, wall_rects, 0, max_depth
    )


# ---------- Sweep an enemy's rect for visibility boundaries ----------

def _wall_rects_from_walls(walls):
    """Converts your {id: wall_obj} dict into plain pygame.Rects,
    matching the obs.img.get_rect(topleft=(obs.x, obs.y)) convention
    used elsewhere in the codebase (Enemy.py, PathFindingSprite.py)."""
    return [w.img.get_rect(topleft=(w.x, w.y)) for w in walls.values()]


def find_cover_boundaries(shooter_pos, hitbox: pygame.Rect, wall_rects,
                           samples_per_edge=8, max_depth=DEFAULT_MAX_DEPTH):
    """
    Sweeps the left and right edges of hitbox top->bottom looking for
    visible/blocked transitions (the common peek-around-cover case),
    then binary-searches each transition to a precise point.
    """
    boundaries = []

    edges = [
        [(hitbox.left, hitbox.top + hitbox.height * i / samples_per_edge)
         for i in range(samples_per_edge + 1)],
        [(hitbox.right, hitbox.top + hitbox.height * i / samples_per_edge)
         for i in range(samples_per_edge + 1)],
    ]

    for edge_points in edges:
        vis_flags = [is_visible(shooter_pos, p, wall_rects) for p in edge_points]
        for i in range(len(edge_points) - 1):
            if vis_flags[i] != vis_flags[i + 1]:
                boundary = find_visibility_boundary(
                    shooter_pos, edge_points[i], edge_points[i + 1],
                    wall_rects, max_depth
                )
                if boundary:
                    boundaries.append(boundary)

    return boundaries


def evaluate_cover(shooter_pos, hitbox: pygame.Rect, walls,
                    samples_per_edge=8, max_depth=DEFAULT_MAX_DEPTH):
    """
    Main entry point. `walls` is the same dict Enemy/Armed already pass
    around (id -> wall object with .img/.x/.y).

    Returns a dict:
        fully_in_cover   - bool, no part of the hitbox is visible
        fully_exposed    - bool, entire hitbox is visible
        boundaries       - list of (x, y) points where visibility flips
        corner_visibility- [bool, bool, bool, bool] for TL, TR, BR, BL
    """
    wall_rects = _wall_rects_from_walls(walls)

    corners = [
        (hitbox.left, hitbox.top), (hitbox.right, hitbox.top),
        (hitbox.right, hitbox.bottom), (hitbox.left, hitbox.bottom),
    ]
    corner_vis = [is_visible(shooter_pos, c, wall_rects) for c in corners]

    boundaries = find_cover_boundaries(
        shooter_pos, hitbox, wall_rects, samples_per_edge, max_depth
    )

    fully_in_cover = (not any(corner_vis)) and len(boundaries) == 0
    fully_exposed = all(corner_vis) and len(boundaries) == 0

    return {
        "fully_in_cover": fully_in_cover,
        "fully_exposed": fully_exposed,
        "boundaries": boundaries,
        "corner_visibility": corner_vis,
    }