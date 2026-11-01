# -*- coding: utf-8 -*-
"""
Artificial Intelligence, Steering Behaviors & Pathfinding for Raylib Python
----------------------------------------------------------------------------
Provides modular enemy AI behaviors and pathfinding:
  - Steering Behaviors: Seek, Flee, Predictive Interception (Lead Target), Wander, Flocking
  - Pathfinding: A* (A-Star) and BFS (Breadth-First Search) on 2D grids
  - Sensory: Line of sight (LOS) raycast against grid obstacles

Designed for game development beginners: simple inputs, clean returns, zero complex dependencies.
"""

import math
import heapq
from collections import deque
from typing import List, Tuple, Optional
from pyray import Vector2, Vector3

# ==============================================================================
# STEERING BEHAVIORS (REYNOLDS MODEL)
# ==============================================================================

def seek_2d(current_pos: Vector2, target_pos: Vector2, speed: float) -> Vector2:
    """
    Computes a velocity vector moving directly toward target_pos at constant speed.
    """
    dx = target_pos.x - current_pos.x
    dy = target_pos.y - current_pos.y
    dist = math.sqrt(dx * dx + dy * dy)
    if dist < 0.001:
        return Vector2(0.0, 0.0)
    return Vector2((dx / dist) * speed, (dy / dist) * speed)


def flee_2d(current_pos: Vector2, threat_pos: Vector2, speed: float) -> Vector2:
    """
    Computes a velocity vector moving directly away from threat_pos at constant speed.
    """
    s = seek_2d(threat_pos, current_pos, speed)
    return s


def arrive_2d(current_pos: Vector2, target_pos: Vector2, max_speed: float, slowing_radius: float = 80.0) -> Vector2:
    """
    Steers toward target, smoothly decelerating as it gets inside the slowing radius.
    Prevents jittering when reaching the destination.
    """
    dx = target_pos.x - current_pos.x
    dy = target_pos.y - current_pos.y
    dist = math.sqrt(dx * dx + dy * dy)
    if dist < 0.001:
        return Vector2(0.0, 0.0)
        
    if dist < slowing_radius:
        desired_speed = max_speed * (dist / slowing_radius)
    else:
        desired_speed = max_speed
        
    return Vector2((dx / dist) * desired_speed, (dy / dist) * desired_speed)


def predict_intercept_2d(chaser_pos: Vector2, target_pos: Vector2, target_velocity: Vector2, chaser_speed: float) -> Vector2:
    """
    Predicts where a moving target will be in the future (lead targeting) and
    steers toward that intercept point.
    """
    to_target_x = target_pos.x - chaser_pos.x
    to_target_y = target_pos.y - chaser_pos.y
    dist = math.sqrt(to_target_x * to_target_x + to_target_y * to_target_y)
    
    # Estimate look-ahead time based on distance and chaser speed
    if chaser_speed <= 0.001:
        look_ahead = 0.0
    else:
        look_ahead = dist / chaser_speed
        
    # Cap look-ahead to avoid wildly projecting across the screen
    look_ahead = min(look_ahead, 2.0)
    
    predicted_target = Vector2(
        target_pos.x + target_velocity.x * look_ahead,
        target_pos.y + target_velocity.y * look_ahead
    )
    
    return seek_2d(chaser_pos, predicted_target, chaser_speed)


def wander_2d(current_angle: float, wander_jitter: float = 0.3) -> float:
    """
    Smoothly changes a wandering heading angle by applying a small random angular perturbation.
    Returns the new angle in radians.
    """
    import random
    delta = (random.random() * 2.0 - 1.0) * wander_jitter
    return current_angle + delta


def seek_3d(current_pos: Vector3, target_pos: Vector3, speed: float) -> Vector3:
    """Computes a 3D velocity vector heading directly towards target_pos."""
    dx = target_pos.x - current_pos.x
    dy = target_pos.y - current_pos.y
    dz = target_pos.z - current_pos.z
    dist = math.sqrt(dx * dx + dy * dy + dz * dz)
    if dist < 0.001:
        return Vector3(0.0, 0.0, 0.0)
    return Vector3((dx / dist) * speed, (dy / dist) * speed, (dz / dist) * speed)


def predict_intercept_3d(chaser_pos: Vector3, target_pos: Vector3, target_velocity: Vector3, chaser_speed: float) -> Vector3:
    """Predicts a 3D lead intercept point and returns the velocity to reach it."""
    dx = target_pos.x - chaser_pos.x
    dy = target_pos.y - chaser_pos.y
    dz = target_pos.z - chaser_pos.z
    dist = math.sqrt(dx * dx + dy * dy + dz * dz)
    
    look_ahead = dist / max(0.001, chaser_speed)
    look_ahead = min(look_ahead, 2.5)
    
    predicted = Vector3(
        target_pos.x + target_velocity.x * look_ahead,
        target_pos.y + target_velocity.y * look_ahead,
        target_pos.z + target_velocity.z * look_ahead
    )
    return seek_3d(chaser_pos, predicted, chaser_speed)


# ==============================================================================
# SENSORY PERCEPTION (LINE OF SIGHT)
# ==============================================================================

def has_line_of_sight_grid(tile_grid, start_pos: Vector2, target_pos: Vector2) -> bool:
    """
    Uses Bresenham / DDA raycasting across a TileGrid2D to check if a clear,
    unobstructed line of sight exists between start_pos and target_pos.
    Returns True if visible, False if blocked by any wall tile.
    """
    x0, y0 = tile_grid.world_to_grid(start_pos.x, start_pos.y)
    x1, y1 = tile_grid.world_to_grid(target_pos.x, target_pos.y)
    
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    
    curr_x, curr_y = x0, y0
    while True:
        # If we hit a wall tile before reaching target, LOS is blocked
        if not tile_grid.is_walkable(curr_x, curr_y):
            return False
            
        if curr_x == x1 and curr_y == y1:
            break
            
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            curr_x += sx
        if e2 < dx:
            err += dx
            curr_y += sy
            
    return True


# ==============================================================================
# GRID PATHFINDING (A* & BFS)
# ==============================================================================

def find_path_astar(tile_grid, start_gx_gy: Tuple[int, int], target_gx_gy: Tuple[int, int],
                    allow_diagonals: bool = False) -> List[Tuple[int, int]]:
    """
    Finds the shortest obstacle-free path on a TileGrid2D using the A* algorithm.
    Returns: A list of grid coordinates [(gx, gy), ...] from start to target.
             Returns empty list if no valid path exists.
    """
    start = start_gx_gy
    goal = target_gx_gy
    
    if not tile_grid.is_walkable(start[0], start[1]) or not tile_grid.is_walkable(goal[0], goal[1]):
        return []
        
    def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> float:
        # Manhattan or Octile heuristic
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])
        if allow_diagonals:
            return (dx + dy) + (1.414 - 2.0) * min(dx, dy)
        return dx + dy

    frontier = []
    # (priority, cost_so_far, node)
    heapq.heappush(frontier, (0.0, 0.0, start))
    came_from = {start: None}
    cost_so_far = {start: 0.0}

    while frontier:
        _, current_cost, current = heapq.heappop(frontier)

        if current == goal:
            break

        for next_node in tile_grid.get_neighbors(current[0], current[1], allow_diagonals=allow_diagonals):
            is_diag = (next_node[0] != current[0]) and (next_node[1] != current[1])
            step_cost = 1.414 if is_diag else 1.0
            new_cost = current_cost + step_cost
            
            if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                cost_so_far[next_node] = new_cost
                priority = new_cost + heuristic(next_node, goal)
                heapq.heappush(frontier, (priority, new_cost, next_node))
                came_from[next_node] = current

    # Reconstruct path
    if goal not in came_from:
        return []
        
    path = []
    curr = goal
    while curr is not None:
        path.append(curr)
        curr = came_from[curr]
    path.reverse()
    return path


def find_path_bfs(tile_grid, start_gx_gy: Tuple[int, int], target_gx_gy: Tuple[int, int]) -> List[Tuple[int, int]]:
    """
    Breadth-First Search (BFS) pathfinder for unweighted 2D tile grids.
    Simple, reliable, and guarantees shortest path on uniform grids.
    """
    start = start_gx_gy
    goal = target_gx_gy
    
    if not tile_grid.is_walkable(start[0], start[1]) or not tile_grid.is_walkable(goal[0], goal[1]):
        return []
        
    queue = deque([start])
    came_from = {start: None}
    
    while queue:
        current = queue.popleft()
        if current == goal:
            break
            
        for next_node in tile_grid.get_neighbors(current[0], current[1], allow_diagonals=False):
            if next_node not in came_from:
                came_from[next_node] = current
                queue.append(next_node)
                
    if goal not in came_from:
        return []
        
    path = []
    curr = goal
    while curr is not None:
        path.append(curr)
        curr = came_from[curr]
    path.reverse()
    return path

