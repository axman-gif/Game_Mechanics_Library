# -*- coding: utf-8 -*-
"""
Spatial Partitioning & Grid Utilities for Raylib Python
-------------------------------------------------------
Provides high-performance spatial partitioning structures and tile grids:
  - SpatialGrid2D: Fast 2D spatial hash grid for querying nearby entities (O(1) lookups).
  - SpatialGrid3D: Fast 3D spatial hash grid for 3D broadphase collision / proximity checks.
  - TileGrid2D: Grid-based map representation for labyrinths, walls, and pathfinding.

Written for beginners with clear docstrings and easy methods.
"""

import math
from collections import defaultdict
from typing import List, Tuple, Any, Optional

# ==============================================================================
# 2D SPATIAL HASH GRID
# ==============================================================================

class SpatialGrid2D:
    """
    A 2D Spatial Hash Grid partitions continuous 2D space into discrete square cells.
    Instead of checking every entity against every other entity (O(N^2)), you only check
    entities located in the same or adjacent cells (O(N) on average).
    """
    def __init__(self, cell_size: float = 64.0):
        self.cell_size = float(cell_size)
        # Maps (cell_x, cell_y) -> list of (entity, x, y, radius)
        self.grid = defaultdict(list)
        self.entity_count = 0

    def _hash_coords(self, x: float, y: float) -> Tuple[int, int]:
        """Converts world coordinates into cell integer coordinates."""
        return int(math.floor(x / self.cell_size)), int(math.floor(y / self.cell_size))

    def clear(self):
        """Clears all entities from the spatial grid. Call this at the start of each frame."""
        self.grid.clear()
        self.entity_count = 0

    def insert(self, entity: Any, x: float, y: float, radius: float = 0.0):
        """
        Inserts an entity into the grid. If radius > 0, the entity is placed in all cells
        overlapping its circular bounding area.
        """
        self.entity_count += 1
        if radius <= 0.0:
            cx, cy = self._hash_coords(x, y)
            self.grid[(cx, cy)].append((entity, x, y, radius))
        else:
            min_cx, min_cy = self._hash_coords(x - radius, y - radius)
            max_cx, max_cy = self._hash_coords(x + radius, y + radius)
            entry = (entity, x, y, radius)
            for cx in range(min_cx, max_cx + 1):
                for cy in range(min_cy, max_cy + 1):
                    self.grid[(cx, cy)].append(entry)

    def query_radius(self, x: float, y: float, radius: float) -> List[Any]:
        """
        Finds all unique entities within a circular radius of (x, y).
        """
        min_cx, min_cy = self._hash_coords(x - radius, y - radius)
        max_cx, max_cy = self._hash_coords(x + radius, y + radius)
        
        found = set()
        r_sq = radius * radius
        
        for cx in range(min_cx, max_cx + 1):
            for cy in range(min_cy, max_cy + 1):
                cell_entries = self.grid.get((cx, cy))
                if cell_entries:
                    for entity, ex, ey, erad in cell_entries:
                        if entity in found:
                            continue
                        # Distance check (taking entity radius into account)
                        dx = ex - x
                        dy = ey - y
                        dist_sq = dx * dx + dy * dy
                        max_allowed_dist = radius + erad
                        if dist_sq <= (max_allowed_dist * max_allowed_dist):
                            found.add(entity)
                            
        return list(found)


# ==============================================================================
# 3D SPATIAL HASH GRID
# ==============================================================================

class SpatialGrid3D:
    """
    A 3D Spatial Hash Grid partitions 3D space into cubic cells for broadphase
    collision testing and fast proximity queries.
    """
    def __init__(self, cell_size: float = 4.0):
        self.cell_size = float(cell_size)
        self.grid = defaultdict(list)
        self.entity_count = 0

    def _hash_coords(self, x: float, y: float, z: float) -> Tuple[int, int, int]:
        return (
            int(math.floor(x / self.cell_size)),
            int(math.floor(y / self.cell_size)),
            int(math.floor(z / self.cell_size))
        )

    def clear(self):
        """Clears all entities from the 3D grid."""
        self.grid.clear()
        self.entity_count = 0

    def insert(self, entity: Any, x: float, y: float, z: float, radius: float = 0.0):
        """Inserts an entity with optional spherical bounding radius."""
        self.entity_count += 1
        if radius <= 0.0:
            key = self._hash_coords(x, y, z)
            self.grid[key].append((entity, x, y, z, radius))
        else:
            min_k = self._hash_coords(x - radius, y - radius, z - radius)
            max_k = self._hash_coords(x + radius, y + radius, z + radius)
            entry = (entity, x, y, z, radius)
            for cx in range(min_k[0], max_k[0] + 1):
                for cy in range(min_k[1], max_k[1] + 1):
                    for cz in range(min_k[2], max_k[2] + 1):
                        self.grid[(cx, cy, cz)].append(entry)

    def query_sphere(self, x: float, y: float, z: float, radius: float) -> List[Any]:
        """Finds all unique entities within a sphere of radius centered at (x, y, z)."""
        min_k = self._hash_coords(x - radius, y - radius, z - radius)
        max_k = self._hash_coords(x + radius, y + radius, z + radius)
        
        found = set()
        r_sq = radius * radius
        
        for cx in range(min_k[0], max_k[0] + 1):
            for cy in range(min_k[1], max_k[1] + 1):
                for cz in range(min_k[2], max_k[2] + 1):
                    cell = self.grid.get((cx, cy, cz))
                    if cell:
                        for entity, ex, ey, ez, erad in cell:
                            if entity in found:
                                continue
                            dx = ex - x
                            dy = ey - y
                            dz = ez - z
                            dist_sq = dx * dx + dy * dy + dz * dz
                            max_dist = radius + erad
                            if dist_sq <= (max_dist * max_dist):
                                found.add(entity)
        return list(found)


# ==============================================================================
# 2D TILE NAVIGATION GRID
# ==============================================================================

class TileGrid2D:
    """
    A 2D discrete tile map grid designed for mazes, arenas, terrain, and pathfinding.
    Cell values typically: 0 = Empty/Walkable, 1 = Wall/Blocked.
    """
    def __init__(self, cols: int, rows: int, cell_size: float = 32.0, default_val: int = 0):
        self.cols = cols
        self.rows = rows
        self.cell_size = float(cell_size)
        self.cells = [[default_val for _ in range(cols)] for _ in range(rows)]

    def is_valid(self, gx: int, gy: int) -> bool:
        """Returns True if the grid coordinate is inside bounds."""
        return 0 <= gx < self.cols and 0 <= gy < self.rows

    def get_cell(self, gx: int, gy: int) -> int:
        """Gets the value at (gx, gy). Returns 1 (wall) if out of bounds."""
        if not self.is_valid(gx, gy):
            return 1
        return self.cells[gy][gx]

    def set_cell(self, gx: int, gy: int, value: int):
        """Sets the value at (gx, gy)."""
        if self.is_valid(gx, gy):
            self.cells[gy][gx] = value

    def is_walkable(self, gx: int, gy: int) -> bool:
        """Checks if a tile is free to traverse (value == 0)."""
        return self.is_valid(gx, gy) and self.cells[gy][gx] == 0

    def world_to_grid(self, wx: float, wy: float) -> Tuple[int, int]:
        """Converts continuous world space (x, y) to grid coordinates (gx, gy)."""
        return int(math.floor(wx / self.cell_size)), int(math.floor(wy / self.cell_size))

    def grid_to_world(self, gx: int, gy: int, center: bool = True) -> Tuple[float, float]:
        """
        Converts grid coordinates to world coordinates.
        If center is True, returns the center point of the cell.
        """
        if center:
            return (gx + 0.5) * self.cell_size, (gy + 0.5) * self.cell_size
        return gx * self.cell_size, gy * self.cell_size

    def get_neighbors(self, gx: int, gy: int, allow_diagonals: bool = False) -> List[Tuple[int, int]]:
        """Returns adjacent walkable grid neighbor coordinates."""
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        if allow_diagonals:
            dirs += [(-1, -1), (1, -1), (-1, 1), (1, 1)]
            
        neighbors = []
        for dx, dy in dirs:
            nx, ny = gx + dx, gy + dy
            if self.is_walkable(nx, ny):
                neighbors.append((nx, ny))
        return neighbors

