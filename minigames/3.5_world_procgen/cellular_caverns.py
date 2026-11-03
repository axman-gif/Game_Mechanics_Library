# -*- coding: utf-8 -*-
"""
Cellular Automata Caverns - 4-5 Rule Smoothing & Flood-Fill Connectivity
========================================================================
Section          : 3.5 World & Procedural Generation
Pattern Category : World & Procedural Generation (Cellular Automata & Flood-Fill)
Dimension        : 2D

Problem Solved:
  In procedural generation, generating organic subterranean cavern systems using pure random noise
  produces chaotic, static-filled scatter grids filled with disconnected 1-tile holes, impassable
  bottle-necks, and jagged clutter. Conversely, simple noise thresholds either seal off all pathways
  or create open voids devoid of natural subterranean choke points. Crucially, even when smoothed,
  procedural cave generators frequently produce isolated, inaccessible dead-end chambers that trap
  players, items, and objectives behind impassable rock walls, rendering procedural levels unplayable
  without topological connectivity validation.

How the Pattern Works:
  1. Discrete 2D Occupancy Grid (1D Flat Array Layout):
     The cavern is modeled as a discrete 2D grid stored in a contiguous 1D flat array:
       index(x, y) = y * grid_width + x
     In C++, this maps directly to `std::vector<uint8_t>` or a fixed-capacity flat buffer
     `uint8_t grid[HEIGHT * WIDTH]`, ensuring cache locality, O(1) random indexing, and zero
     pointer-chasing overhead across thousands of cells.

  2. Double-Buffered Ping-Pong State Stepping:
     Cellular automata update synchronously. Updating cells in-place causes subsequent neighbor
     evaluations in the same generation to read partially updated states, introducing severe
     directional bias (diagonal slanting streaks). By allocating two buffers (Buffer A and Buffer B)
     and ping-ponging the active pointer each generation:
       next_buffer[idx] = evaluate_rules(current_buffer, x, y)
     All state transitions depend strictly on snapshot t, exactly mirroring GPU compute shaders
     and C++ double-buffering architectures.

  3. 4-5 Smoothing Rule (Moore Neighborhood):
     For each cell (x, y), evaluate its 8 surrounding neighbors (Moore Neighborhood). Cells outside
     map boundaries are evaluated as solid rock to enforce natural subterranean perimeter containment:
       - If Wall Neighbor Count >= 5: Cell becomes SOLID WALL (rock clumping / accretion).
       - If Wall Neighbor Count <= 3: Cell becomes OPEN AIR (rock erosion / tunnel carving).
       - If Wall Neighbor Count == 4: Cell RETAINS PREVIOUS STATE (hysteresis stability).
     Iterating this rule 3 to 5 times rapidly transforms static random noise into smooth, organic
     cavern walls, wide chambers, and winding subterranean passages.

  4. Queue-Based Breadth-First Search (BFS) Flood-Fill Connectivity:
     To guarantee topological navigability, a queue-based flood-fill scans every unvisited open tile,
     assigning a distinct integer Region ID (1, 2, 3...) to each disconnected cavern pocket.
     The algorithm records the exact tile count of each chamber, identifying the Primary Navigable
     Chamber (the region with the maximum tile count) and quantifying map connectivity:
       Connectivity % = (Largest Chamber Tiles / Total Open Tiles) * 100.0

  5. Disconnected Pocket Culling (Topology Enforcement):
     All secondary cavern pockets that do not match the Primary Region ID are filled back in with
     solid rock (`TILE_WALL`). After culling, 100% of open subterranean space is guaranteed to be
     fully traversable from any point, eliminating soft-locks and stranded objectives.

  6. Dynamic Spelunker Avatar & Dual Subterranean Lighting:
     Features a responsive kinematic character controller equipped with a directional mining
     flashlight (cone beam falloff) and ambient lantern halo, exploring dark subterranean caverns.
     Players can dig out rock walls, extract embedded glowing mineral crystals, or place reinforced
     scaffold blocks with live automated connectivity re-analysis.

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - Spelunker Movement          : WASD / Left Stick / D-Pad
  - Flashlight Aim / Cursor     : Mouse Position OR Gamepad Right Stick
  - Dig / Mine Wall at Reticle  : Space / Left Mouse Button / RT / Gamepad A
  - Place Reinforced Block      : Right Mouse Button / K / LT / Gamepad X
  - Step 1 Automata Iteration   : E / Gamepad X
  - Generate Fresh Noise Map    : Q / Gamepad Y
  - Execute Flood-Fill & Cull   : F / Gamepad B
  - Toggle Culling / Raw Noise  : [F1] / Gamepad LB (Compare raw noise vs smoothed vs culled)
  - Toggle X-Ray Overlay        : [Tab] / Gamepad View (Select) (Color-coded region visualizer)
  - [Ctrl +/-]                  : Increase / Decrease UI Font Size
  - [F11]                       : Toggle Fullscreen
  - [R] / Gamepad Start         : Reset Simulation (Generate fresh map & reposition avatar)
"""

import sys
import os
import math
import random

# 1. Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# 2. Add repository root to search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# 3. Mandatory Raylib & modular imports
from pyray import *
from assets import *
from utils import *

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WINDOW_TITLE = "Cellular Automata Caverns - 4-5 Rule Smoothing & Flood-Fill Connectivity (Raylib)"

# Grid Layout Geometry
GRID_COLS = 80
GRID_ROWS = 40
CELL_SIZE = 16
GRID_OFFSET_X = 0
GRID_OFFSET_Y = 56
TOTAL_CELLS = GRID_COLS * GRID_ROWS

# Subterranean Cell Types (C++: enum class TileType : uint8_t)
TILE_OPEN = 0        # Hollow cavern floor / breathable tunnel
TILE_WALL = 1        # Solid subterranean rock
TILE_CRYSTAL = 2     # Valuable gleaming mineral vein embedded in rock
TILE_REINFORCED = 3  # Reinforced scaffold timber/metal block placed by spelunker

# Color Palette for High-Contrast Rendering
COLOR_BG_DARK = Color(10, 12, 18, 255)
COLOR_ROCK_SOLID = Color(38, 44, 58, 255)
COLOR_ROCK_HIGHLIGHT = Color(62, 72, 94, 255)
COLOR_ROCK_BORDER = Color(24, 28, 38, 255)
COLOR_CAVERN_FLOOR = Color(18, 22, 32, 255)
COLOR_CRYSTAL_CYAN = Color(65, 230, 245, 255)
COLOR_CRYSTAL_GLOW = Color(140, 245, 255, 180)
COLOR_REINFORCED = Color(195, 135, 60, 255)
COLOR_REINFORCED_TRIM = Color(240, 180, 95, 255)

# X-Ray Disconnected Region Palette (Distinct vibrant hues for multi-chamber visualizer)
REGION_PALETTE = [
    Color(255, 215, 50, 240),   # Region 1 (Golden Yellow - Largest Primary Navigable Chamber)
    Color(60, 220, 255, 230),   # Region 2 (Cyan)
    Color(255, 85, 95, 230),    # Region 3 (Coral Red)
    Color(115, 245, 75, 230),   # Region 4 (Lime Green)
    Color(205, 100, 255, 230),  # Region 5 (Vivid Purple)
    Color(255, 120, 190, 230),  # Region 6 (Hot Pink)
    Color(255, 160, 45, 230),   # Region 7 (Electric Orange)
    Color(80, 145, 255, 230),   # Region 8 (Sky Blue)
    Color(75, 245, 185, 230),   # Region 9 (Mint Teal)
    Color(240, 235, 100, 230),  # Region 10 (Lemon Yellow)
    Color(190, 145, 255, 230),  # Region 11 (Lavender)
    Color(255, 105, 140, 230),  # Region 12 (Rose)
]


# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATION
# ==============================================================================

class CellularAutomataCavern:
    """
    Core Procedural Cavern Generator implementing 4-5 Rule Cellular Automata Smoothing
    with Double-Buffered Ping-Pong Buffering and Queue-Based BFS Flood-Fill Connectivity.

    C++ Architectural Mapping:
      - Memory Layout: Two flat continuous arrays `uint8_t buffer_a[3200]` and `buffer_b[3200]`.
      - Indexing: `idx = y * width + x` (zero dynamic pointer overhead, optimal CPU L1 cache).
      - Ping-Pong Pointer: `uint8_t* p_curr = buffer_a; uint8_t* p_next = buffer_b;` swapped each step.
      - BFS Queue: Ring-buffer queue `int q[3200]` with `head` and `tail` index offsets.
    """
    def __init__(self, cols: int = GRID_COLS, rows: int = GRID_ROWS, initial_fill: int = 46):
        self.cols = cols
        self.rows = rows
        self.total_cells = cols * rows

        # Double-buffered state arrays (Buffer A and Buffer B)
        self.buffer_a = [TILE_WALL] * self.total_cells
        self.buffer_b = [TILE_WALL] * self.total_cells
        self.raw_backup = [TILE_WALL] * self.total_cells
        self.using_buffer_a = True

        # Automata parameters (Standard 4-5 Rule)
        self.birth_threshold = 5   # If solid neighbor count >= 5 -> Wall
        self.death_threshold = 3   # If solid neighbor count <= 3 -> Open Air
        self.initial_fill_percent = initial_fill
        self.generation_count = 0
        self.is_culled = False

        # Connectivity analysis data structures
        self.region_map = [0] * self.total_cells
        self.region_sizes = {}
        self.largest_region_id = 0
        self.largest_region_size = 0
        self.total_open_cells = 0
        self.total_wall_cells = 0
        self.connectivity_ratio = 0.0

        # Initial random noise generation
        self.generate_random_noise(self.initial_fill_percent)

    def get_active_buffer(self) -> list:
        """Returns the current read snapshot buffer."""
        if self.using_buffer_a:
            return self.buffer_a
        return self.buffer_b

    def get_inactive_buffer(self) -> list:
        """Returns the target write buffer for synchronous generation stepping."""
        if self.using_buffer_a:
            return self.buffer_b
        return self.buffer_a

    def swap_buffers(self):
        """Swaps active and inactive buffer roles (Ping-Pong pointer flip)."""
        self.using_buffer_a = not self.using_buffer_a

    def get_cell(self, gx: int, gy: int) -> int:
        """
        Retrieves cell state with perimeter boundary protection.
        Any coordinate outside map bounds is strictly treated as solid rock (TILE_WALL)
        to prevent procedural caves from leaking beyond the world boundaries.
        """
        if gx < 0 or gx >= self.cols or gy < 0 or gy >= self.rows:
            return TILE_WALL
        buf = self.get_active_buffer()
        return buf[gy * self.cols + gx]

    def set_cell(self, gx: int, gy: int, tile_type: int):
        """Sets a cell state inside world bounds in the active buffer."""
        if gx >= 0 and gx < self.cols and gy >= 0 and gy < self.rows:
            buf = self.get_active_buffer()
            buf[gy * self.cols + gx] = tile_type

    def count_wall_neighbors(self, src_buf: list, gx: int, gy: int) -> int:
        """
        Evaluates the 8 adjacent neighbors in the Moore Neighborhood.
        Out-of-bounds neighbors are counted as solid wall to produce sealed borders.

        C++: Explicit 3x3 loop with center cell exclusion:
          for (int dy = -1; dy <= 1; ++dy) {
              for (int dx = -1; dx <= 1; ++dx) { ... }
          }
        """
        wall_count = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx = gx + dx
                ny = gy + dy
                if nx < 0 or nx >= self.cols or ny < 0 or ny >= self.rows:
                    wall_count += 1
                else:
                    val = src_buf[ny * self.cols + nx]
                    if val != TILE_OPEN:
                        wall_count += 1
        return wall_count

    def generate_random_noise(self, fill_percent: int = 46, seed_val: int = -1):
        """
        Fills the grid with raw Bernoulli noise at the specified fill percentage.
        Perimeter boundary tiles are permanently anchored as TILE_WALL.
        """
        if seed_val >= 0:
            random.seed(seed_val)

        self.initial_fill_percent = fill_percent
        self.generation_count = 0
        self.is_culled = False

        buf = self.get_active_buffer()
        for gy in range(self.rows):
            for gx in range(self.cols):
                idx = gy * self.cols + gx
                # Enforce solid stone perimeter boundary
                if gx == 0 or gx == self.cols - 1 or gy == 0 or gy == self.rows - 1:
                    buf[idx] = TILE_WALL
                else:
                    roll = random.randint(0, 99)
                    if roll < fill_percent:
                        buf[idx] = TILE_WALL
                    else:
                        buf[idx] = TILE_OPEN

        # Store pristine raw noise backup for live [F1] comparison toggle
        for i in range(self.total_cells):
            self.raw_backup[i] = buf[i]

        self.analyze_connectivity()

    def step_automata(self):
        """
        Executes exactly one synchronous 4-5 rule smoothing iteration across the entire grid.
        Reads from current buffer and writes into the inactive buffer to guarantee zero
        read-during-write corruption.
        """
        src = self.get_active_buffer()
        dst = self.get_inactive_buffer()

        for gy in range(self.rows):
            for gx in range(self.cols):
                idx = gy * self.cols + gx

                # Keep borders permanently sealed
                if gx == 0 or gx == self.cols - 1 or gy == 0 or gy == self.rows - 1:
                    dst[idx] = TILE_WALL
                    continue

                walls = self.count_wall_neighbors(src, gx, gy)
                current_state = src[idx]

                # 4-5 Rule Evaluation:
                # - If 5 or more neighbors are rock -> become rock
                # - If 3 or fewer neighbors are rock -> erode to open cavern
                # - If exactly 4 neighbors are rock -> maintain previous state (hysteresis)
                if walls >= self.birth_threshold:
                    dst[idx] = TILE_WALL
                elif walls <= self.death_threshold:
                    dst[idx] = TILE_OPEN
                else:
                    dst[idx] = current_state

        self.swap_buffers()
        self.generation_count += 1
        self.is_culled = False

        # On the 4th generation step, spawn natural mineral veins along cave wall fringes
        if self.generation_count == 4:
            self.seed_mineral_veins()

        self.analyze_connectivity()

    def auto_smooth(self, passes: int = 4):
        """Executes multiple automated smoothing passes in sequence."""
        for _ in range(passes):
            self.step_automata()

    def seed_mineral_veins(self):
        """
        Procedurally scatters gleaming cyan mineral crystals along the boundaries
        where solid rock meets open cavern air.
        """
        buf = self.get_active_buffer()
        for gy in range(1, self.rows - 1):
            for gx in range(1, self.cols - 1):
                idx = gy * self.cols + gx
                if buf[idx] == TILE_WALL:
                    # Check if adjacent to at least one open air tile
                    has_air_neighbor = False
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            nx = gx + dx
                            ny = gy + dy
                            if buf[ny * self.cols + nx] == TILE_OPEN:
                                has_air_neighbor = True
                                break
                        if has_air_neighbor:
                            break
                    if has_air_neighbor and random.randint(0, 99) < 6:
                        buf[idx] = TILE_CRYSTAL

    def analyze_connectivity(self):
        """
        Executes Queue-Based Breadth-First Search (BFS) Flood-Fill.
        Labels every distinct open cavern chamber with an integer Region ID (1, 2, 3...)
        and identifies the largest primary navigable chamber.

        C++ Mapping:
          std::vector<int> region_map(cols * rows, 0);
          std::queue<std::pair<int, int>> q;
        """
        buf = self.get_active_buffer()

        for i in range(self.total_cells):
            self.region_map[i] = 0

        self.region_sizes.clear()
        self.total_open_cells = 0
        self.total_wall_cells = 0

        current_region_id = 0
        queue = []

        for gy in range(self.rows):
            for gx in range(self.cols):
                idx = gy * self.cols + gx
                val = buf[idx]

                if val == TILE_WALL or val == TILE_CRYSTAL or val == TILE_REINFORCED:
                    self.total_wall_cells += 1
                elif val == TILE_OPEN:
                    self.total_open_cells += 1
                    # If this open cell hasn't been assigned a region yet, launch new BFS flood
                    if self.region_map[idx] == 0:
                        current_region_id += 1
                        region_tile_count = 0

                        # Initialize BFS queue with seed tile
                        queue.clear()
                        queue.append((gx, gy))
                        self.region_map[idx] = current_region_id
                        q_head = 0

                        # BFS Traversal (4 cardinal directions for clean tile graph reachability)
                        while q_head < len(queue):
                            cx, cy = queue[q_head]
                            q_head += 1
                            region_tile_count += 1

                            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                                nx = cx + dx
                                ny = cy + dy
                                if nx >= 0 and nx < self.cols and ny >= 0 and ny < self.rows:
                                    n_idx = ny * self.cols + nx
                                    if buf[n_idx] == TILE_OPEN and self.region_map[n_idx] == 0:
                                        self.region_map[n_idx] = current_region_id
                                        queue.append((nx, ny))

                        self.region_sizes[current_region_id] = region_tile_count

        # Identify the largest primary navigable chamber
        self.largest_region_id = 0
        self.largest_region_size = 0

        for r_id, r_size in self.region_sizes.items():
            if r_size > self.largest_region_size:
                self.largest_region_size = r_size
                self.largest_region_id = r_id

        if self.total_open_cells > 0:
            self.connectivity_ratio = (self.largest_region_size / float(self.total_open_cells)) * 100.0
        else:
            self.connectivity_ratio = 0.0

    def cull_disconnected_pockets(self):
        """
        Topology Enforcement:
        Fills all secondary cavern pockets that do not match the Primary Region ID
        with solid rock (TILE_WALL). Guarantees 100% interconnected navigability.
        """
        if self.largest_region_id <= 0:
            return

        buf = self.get_active_buffer()
        culled_count = 0

        for gy in range(self.rows):
            for gx in range(self.cols):
                idx = gy * self.cols + gx
                if buf[idx] == TILE_OPEN:
                    if self.region_map[idx] != self.largest_region_id:
                        buf[idx] = TILE_WALL
                        culled_count += 1

        self.is_culled = True
        self.analyze_connectivity()

    def restore_raw_noise(self):
        """Restores the pristine raw noise state to visually study un-smoothed noise."""
        buf = self.get_active_buffer()
        for i in range(self.total_cells):
            buf[i] = self.raw_backup[i]
        self.generation_count = 0
        self.is_culled = False
        self.analyze_connectivity()

    def find_safe_spawn_tile(self) -> tuple:
        """
        Finds a guaranteed valid open tile near the centroid of the largest
        navigable chamber to safely place the spelunker avatar.
        """
        if self.largest_region_id <= 0:
            return (self.cols // 2, self.rows // 2)

        # Collect candidate coordinates belonging to the primary chamber
        candidates = []
        for gy in range(self.rows):
            for gx in range(self.cols):
                idx = gy * self.cols + gx
                if self.region_map[idx] == self.largest_region_id:
                    candidates.append((gx, gy))

        if not candidates:
            return (self.cols // 2, self.rows // 2)

        # Compute centroid
        sum_x = 0
        sum_y = 0
        for cx, cy in candidates:
            sum_x += cx
            sum_y += cy
        avg_x = sum_x / float(len(candidates))
        avg_y = sum_y / float(len(candidates))

        # Select tile closest to centroid with maximum open neighbor clearance
        best_tile = candidates[0]
        min_dist_sq = 9999999.0

        for cx, cy in candidates:
            dx = cx - avg_x
            dy = cy - avg_y
            d_sq = dx * dx + dy * dy
            if d_sq < min_dist_sq:
                min_dist_sq = d_sq
                best_tile = (cx, cy)

        return best_tile


# ==============================================================================
# BLOCK 2: WORLD SIMULATION & ENTITIES
# ==============================================================================

class RockParticle:
    """Lightweight debris particle spawned during excavation and mining."""
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.lifetime = 0.0
        self.max_lifetime = 0.4
        self.radius = 2.0
        self.color = COLOR_ROCK_HIGHLIGHT
        self.active = False

    def spawn(self, x: float, y: float, vx: float, vy: float, color: Color, radius: float = 2.0, life: float = 0.4):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.radius = radius
        self.lifetime = life
        self.max_lifetime = life
        self.active = True

    def update(self, dt: float):
        if not self.active:
            return
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 220.0 * dt  # Subterranean gravity
        self.lifetime -= dt
        if self.lifetime <= 0.0:
            self.active = False

    def draw(self):
        if not self.active:
            return
        alpha = int(255.0 * (self.lifetime / self.max_lifetime))
        if alpha < 0:
            alpha = 0
        if alpha > 255:
            alpha = 255
        c = Color(self.color.r, self.color.g, self.color.b, alpha)
        draw_circle(int(self.x), int(self.y), int(self.radius), c)


class SpelunkerAvatar:
    """
    Subterranean Spelunker character controller with continuous kinematic physics,
    AABB wall collision sliding, dynamic flashlight beam, and mining laser tools.
    """
    def __init__(self, gx: int, gy: int):
        self.x = float(GRID_OFFSET_X + gx * CELL_SIZE + CELL_SIZE // 2)
        self.y = float(GRID_OFFSET_Y + gy * CELL_SIZE + CELL_SIZE // 2)
        self.vx = 0.0
        self.vy = 0.0
        self.radius = 5.5
        self.speed = 135.0
        self.aim_angle = 0.0
        self.facing_dx = 1.0
        self.walk_phase = 0.0
        self.is_moving = False

        # Equipment & Mining
        self.flashlight_length = 200.0
        self.flashlight_spread_deg = 36.0
        self.ambient_lantern_radius = 54.0
        self.mine_cooldown = 0.0
        self.crystals_collected = 0
        self.blocks_placed = 0

    def reposition(self, gx: int, gy: int):
        """Snaps avatar to a designated grid tile center."""
        self.x = float(GRID_OFFSET_X + gx * CELL_SIZE + CELL_SIZE // 2)
        self.y = float(GRID_OFFSET_Y + gy * CELL_SIZE + CELL_SIZE // 2)
        self.vx = 0.0
        self.vy = 0.0

    def update_aim(self, look_vec: Vector2, mouse_pos: Vector2):
        """Updates flashlight direction from Mouse position or Gamepad Right Stick."""
        if abs(look_vec.x) > 0.15 or abs(look_vec.y) > 0.15:
            self.aim_angle = math.atan2(look_vec.y, look_vec.x)
        else:
            dx = mouse_pos.x - self.x
            dy = mouse_pos.y - self.y
            if dx * dx + dy * dy > 16.0:
                self.aim_angle = math.atan2(dy, dx)

        self.facing_dx = math.cos(self.aim_angle)

    def update(self, dt: float, move_vec: Vector2, cavern: CellularAutomataCavern):
        """
        Updates kinematic movement with axis-independent sliding collision
        resolution against solid rock grid cells.
        """
        if self.mine_cooldown > 0.0:
            self.mine_cooldown -= dt

        # Apply desired acceleration
        target_vx = move_vec.x * self.speed
        target_vy = move_vec.y * self.speed

        # Smooth velocity response
        self.vx = damp(self.vx, target_vx, 16.0, dt)
        self.vy = damp(self.vy, target_vy, 16.0, dt)

        speed_sq = self.vx * self.vx + self.vy * self.vy
        if speed_sq > 4.0:
            self.is_moving = True
            self.walk_phase += dt * 10.0
        else:
            self.is_moving = False
            self.walk_phase = 0.0

        # Axis-independent continuous collision detection
        new_x = self.x + self.vx * dt
        if not self.check_wall_collision(new_x, self.y, cavern):
            self.x = new_x
        else:
            self.vx = 0.0

        new_y = self.y + self.vy * dt
        if not self.check_wall_collision(self.x, new_y, cavern):
            self.y = new_y
        else:
            self.vy = 0.0

        # Clamp inside grid perimeter
        min_x = float(GRID_OFFSET_X + CELL_SIZE + 6)
        max_x = float(GRID_OFFSET_X + (cavern.cols - 1) * CELL_SIZE - 6)
        min_y = float(GRID_OFFSET_Y + CELL_SIZE + 6)
        max_y = float(GRID_OFFSET_Y + (cavern.rows - 1) * CELL_SIZE - 6)

        self.x = clamp(self.x, min_x, max_x)
        self.y = clamp(self.y, min_y, max_y)

    def check_wall_collision(self, px: float, py: float, cavern: CellularAutomataCavern) -> bool:
        """
        Tests whether a circular bounding disk at (px, py) intersects any solid tile.
        Only inspects immediate adjacent grid cells for O(1) performance.
        """
        left_gx = int((px - self.radius - GRID_OFFSET_X) // CELL_SIZE)
        right_gx = int((px + self.radius - GRID_OFFSET_X) // CELL_SIZE)
        top_gy = int((py - self.radius - GRID_OFFSET_Y) // CELL_SIZE)
        bottom_gy = int((py + self.radius - GRID_OFFSET_Y) // CELL_SIZE)

        for gy in range(top_gy, bottom_gy + 1):
            for gx in range(left_gx, right_gx + 1):
                cell_type = cavern.get_cell(gx, gy)
                if cell_type != TILE_OPEN:
                    tile_min_x = float(GRID_OFFSET_X + gx * CELL_SIZE)
                    tile_max_x = tile_min_x + float(CELL_SIZE)
                    tile_min_y = float(GRID_OFFSET_Y + gy * CELL_SIZE)
                    tile_max_y = tile_min_y + float(CELL_SIZE)

                    # Closest point on tile rectangle to avatar circle
                    closest_x = clamp(px, tile_min_x, tile_max_x)
                    closest_y = clamp(py, tile_min_y, tile_max_y)

                    dx = px - closest_x
                    dy = py - closest_y
                    if (dx * dx + dy * dy) < (self.radius * self.radius):
                        return True
        return False

    def draw(self):
        """Renders the detailed procedural spelunker avatar with equipment and mining helmet."""
        ix = int(self.x)
        iy = int(self.y)

        # Walking bob animation
        bob_y = math.sin(self.walk_phase) * 1.5 if self.is_moving else 0.0
        draw_y = iy + int(bob_y)

        # Backpack (Leather Dark Brown)
        bp_x = ix - int(math.copysign(4.0, self.facing_dx))
        draw_rectangle(bp_x - 3, draw_y - 2, 6, 8, Color(85, 55, 30, 255))

        # Suit Body (High-Visibility Mining Orange)
        draw_rectangle(ix - 4, draw_y - 3, 8, 10, Color(245, 125, 35, 255))
        # Reflective high-vis silver stripe across chest
        draw_rectangle(ix - 4, draw_y, 8, 2, Color(225, 235, 250, 255))

        # Spelunker Mining Helmet (Cyan Protective Hardhat)
        draw_circle(ix, draw_y - 6, 5, Color(45, 175, 225, 255))
        draw_rectangle(ix - 5, draw_y - 5, 10, 2, Color(25, 125, 175, 255))

        # Helmet Headlight Bulb & Directional Lens
        lamp_dx = math.cos(self.aim_angle) * 4.5
        lamp_dy = math.sin(self.aim_angle) * 4.5
        lamp_x = ix + int(lamp_dx)
        lamp_y = (draw_y - 6) + int(lamp_dy)

        draw_circle(lamp_x, lamp_y, 3, Color(255, 255, 190, 255))
        draw_circle(lamp_x, lamp_y, 5, Color(255, 240, 120, 110))

        # Handheld Mining Laser / Pickaxe Pointer
        beam_start_x = float(lamp_x)
        beam_start_y = float(lamp_y)
        beam_end_x = beam_start_x + math.cos(self.aim_angle) * 14.0
        beam_end_y = beam_start_y + math.sin(self.aim_angle) * 14.0
        draw_line_ex(
            Vector2(beam_start_x, beam_start_y),
            Vector2(beam_end_x, beam_end_y),
            2.0,
            Color(255, 220, 90, 255)
        )


class CavernParticleSystem:
    """Manages pre-allocated particle pools for mining debris and crystal sparkle feedback."""
    def __init__(self, capacity: int = 64):
        self.particles = []
        for _ in range(capacity):
            self.particles.append(RockParticle())

    def emit_debris(self, x: float, y: float, color: Color, count: int = 8, speed: float = 120.0):
        spawned = 0
        for p in self.particles:
            if not p.active:
                angle = random.uniform(0.0, math.pi * 2.0)
                mag = random.uniform(speed * 0.4, speed)
                vx = math.cos(angle) * mag
                vy = math.sin(angle) * mag - 40.0
                radius = random.uniform(1.5, 3.2)
                lifetime = random.uniform(0.25, 0.45)
                p.spawn(x, y, vx, vy, color, radius, lifetime)
                spawned += 1
                if spawned >= count:
                    break

    def update(self, dt: float):
        for p in self.particles:
            if p.active:
                p.update(dt)

    def draw(self):
        for p in self.particles:
            if p.active:
                p.draw()


# ==============================================================================
# BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY
# ==============================================================================

class CavernTelemetry:
    """
    Renders pedagogical X-Ray telemetry, color-coded disconnected chamber visualizer,
    neighbor-count tile inspector, and interactive algorithmic controls.
    """
    def __init__(self):
        pass

    def draw_region_overlay(self, cavern: CellularAutomataCavern):
        """
        Visualizes disconnected cavern pockets by color-coding each independent BFS chamber
        with a distinct high-contrast palette color.
        """
        buf = cavern.get_active_buffer()
        palette_len = len(REGION_PALETTE)

        for gy in range(cavern.rows):
            for gx in range(cavern.cols):
                idx = gy * cavern.cols + gx
                if buf[idx] == TILE_OPEN:
                    r_id = cavern.region_map[idx]
                    if r_id > 0:
                        # Golden Yellow for largest primary chamber, varied hues for secondary pockets
                        if r_id == cavern.largest_region_id:
                            col = REGION_PALETTE[0]
                        else:
                            palette_idx = 1 + ((r_id - 1) % (palette_len - 1))
                            col = REGION_PALETTE[palette_idx]

                        px = GRID_OFFSET_X + gx * CELL_SIZE
                        py = GRID_OFFSET_Y + gy * CELL_SIZE
                        draw_rectangle(px, py, CELL_SIZE, CELL_SIZE, col)

    def draw_subterranean_lighting(self, cavern: CellularAutomataCavern, avatar: SpelunkerAvatar):
        """
        Simulates realistic dynamic subterranean darkness and dual lighting
        (ambient lantern halo + directional flashlight beam).
        """
        flashlight_rad = math.radians(avatar.flashlight_spread_deg * 0.5)
        cos_cutoff = math.cos(flashlight_rad)
        reach_sq = avatar.flashlight_length * avatar.flashlight_length
        ambient_sq = avatar.ambient_lantern_radius * avatar.ambient_lantern_radius

        aim_dir_x = math.cos(avatar.aim_angle)
        aim_dir_y = math.sin(avatar.aim_angle)

        buf = cavern.get_active_buffer()

        for gy in range(cavern.rows):
            for gx in range(cavern.cols):
                idx = gy * cavern.cols + gx
                cell_type = buf[idx]

                cx = float(GRID_OFFSET_X + gx * CELL_SIZE + CELL_SIZE // 2)
                cy = float(GRID_OFFSET_Y + gy * CELL_SIZE + CELL_SIZE // 2)

                dx = cx - avatar.x
                dy = cy - avatar.y
                d_sq = dx * dx + dy * dy

                illumination = 0.0

                # 1. Ambient lantern halo around spelunker
                if d_sq < ambient_sq:
                    halo_dist = math.sqrt(d_sq)
                    illumination = max(illumination, 1.0 - (halo_dist / avatar.ambient_lantern_radius))

                # 2. Directional flashlight cone beam
                if d_sq < reach_sq and d_sq > 0.01:
                    beam_dist = math.sqrt(d_sq)
                    inv_dist = 1.0 / beam_dist
                    ndx = dx * inv_dist
                    ndy = dy * inv_dist

                    dot = ndx * aim_dir_x + ndy * aim_dir_y
                    if dot > cos_cutoff:
                        angular_falloff = (dot - cos_cutoff) / (1.0 - cos_cutoff)
                        distance_falloff = 1.0 - (beam_dist / avatar.flashlight_length)
                        beam_strength = angular_falloff * distance_falloff * 1.25
                        illumination = max(illumination, beam_strength)

                illumination = clamp(illumination, 0.0, 1.0)

                # Darkness overlay: unlit cells are cast into deep subterranean shadow
                if illumination < 0.98:
                    shadow_alpha = int(245.0 * (1.0 - illumination))
                    shadow_alpha = clamp(shadow_alpha, 0, 245)
                    px = GRID_OFFSET_X + gx * CELL_SIZE
                    py = GRID_OFFSET_Y + gy * CELL_SIZE
                    draw_rectangle(px, py, CELL_SIZE, CELL_SIZE, Color(6, 8, 14, shadow_alpha))

    def draw_hover_inspector(self, cavern: CellularAutomataCavern, mouse_pos: Vector2):
        """
        Inspects the grid tile beneath the cursor, highlighting its 8-neighbor Moore
        neighborhood and showing real-time wall counts and region data.
        """
        gx = int((mouse_pos.x - GRID_OFFSET_X) // CELL_SIZE)
        gy = int((mouse_pos.y - GRID_OFFSET_Y) // CELL_SIZE)

        if gx >= 0 and gx < cavern.cols and gy >= 0 and gy < cavern.rows:
            tx = GRID_OFFSET_X + gx * CELL_SIZE
            ty = GRID_OFFSET_Y + gy * CELL_SIZE

            # Highlight 8-neighbor bounding box
            nb_x = GRID_OFFSET_X + (gx - 1) * CELL_SIZE
            nb_y = GRID_OFFSET_Y + (gy - 1) * CELL_SIZE
            draw_rectangle_lines(nb_x, nb_y, CELL_SIZE * 3, CELL_SIZE * 3, Color(255, 215, 60, 120))

            # Highlight focused tile
            draw_rectangle_lines(tx, ty, CELL_SIZE, CELL_SIZE, Color(255, 80, 80, 255))

            # Tile metrics tooltip card
            src = cavern.get_active_buffer()
            wall_neighbors = cavern.count_wall_neighbors(src, gx, gy)
            tile_val = cavern.get_cell(gx, gy)
            r_id = cavern.region_map[gy * cavern.cols + gx]

            type_name = "OPEN AIR"
            if tile_val == TILE_WALL:
                type_name = "SOLID ROCK"
            elif tile_val == TILE_CRYSTAL:
                type_name = "MINERAL CRYSTAL"
            elif tile_val == TILE_REINFORCED:
                type_name = "REINFORCED BLOCK"

            # Anchor tooltip card safely within screen
            card_x = tx + 20
            card_y = ty - 45
            if card_x + 190 > SCREEN_WIDTH - 20:
                card_x = tx - 205
            if card_y < 65:
                card_y = ty + 25

            draw_rectangle(card_x, card_y, 195, 62, Color(16, 20, 32, 235))
            draw_rectangle_lines(card_x, card_y, 195, 62, Color(65, 95, 145, 255))

            draw_text(f"Tile ({gx}, {gy}): {type_name}", card_x + 8, card_y + 6, 11, Color(235, 242, 255, 255))
            draw_text(f"8-Neighbors: {wall_neighbors}/8 Rock Walls", card_x + 8, card_y + 22, 11, Color(255, 215, 75, 255))

            if tile_val == TILE_OPEN:
                is_main = (r_id == cavern.largest_region_id)
                reg_status = "PRIMARY" if is_main else "ISOLATED POCKET"
                reg_color = Color(85, 245, 125, 255) if is_main else Color(255, 115, 115, 255)
                draw_text(f"Region: #{r_id} [{reg_status}]", card_x + 8, card_y + 38, 11, reg_color)
            else:
                next_rule = "Becomes Wall" if wall_neighbors >= 5 else ("Becomes Open" if wall_neighbors <= 3 else "No Change")
                draw_text(f"Next Step: {next_rule}", card_x + 8, card_y + 38, 11, Color(155, 175, 205, 255))

    def draw_telemetry_hud(self, cavern: CellularAutomataCavern, avatar: SpelunkerAvatar, show_xray: bool, pattern_enabled: bool):
        """
        Draws the main top telemetry dashboard showing automata generation step,
        connectivity ratio, chamber counts, and active buffer information.
        """
        # Top HUD Banner Background (y = 0..54)
        draw_rectangle(0, 0, SCREEN_WIDTH, 54, Color(12, 16, 26, 245))
        draw_line(0, 54, SCREEN_WIDTH, 54, Color(40, 55, 85, 255))

        # Title & Generation Metrics
        draw_text("CELLULAR CAVERNS", 14, 10, 16, Color(75, 215, 255, 255))

        gen_txt = f"Passes: {cavern.generation_count}"
        draw_text(gen_txt, 14, 30, 12, Color(255, 225, 80, 255))

        # Fill & Wall Ratio metrics
        total_open = cavern.total_open_cells
        total_wall = cavern.total_wall_cells
        total = cavern.total_cells
        wall_pct = (total_wall / float(total)) * 100.0 if total > 0 else 0.0
        open_pct = (total_open / float(total)) * 100.0 if total > 0 else 0.0

        draw_text(f"Rock: {wall_pct:.1f}%", 120, 10, 12, Color(195, 205, 225, 255))
        draw_text(f"Cavity: {open_pct:.1f}%", 120, 30, 12, Color(105, 215, 255, 255))

        # Connectivity & Chamber Counts
        num_chambers = len(cavern.region_sizes)
        draw_text(f"Chambers: {num_chambers}", 215, 10, 12, Color(245, 140, 255, 255))
        draw_text(f"Largest: {cavern.largest_region_size} tiles", 215, 30, 12, Color(110, 245, 140, 255))

        # Topological Connectivity Status
        con_col = Color(75, 245, 115, 255) if cavern.connectivity_ratio >= 99.9 else Color(255, 105, 105, 255)
        draw_text(f"Connectivity: {cavern.connectivity_ratio:.1f}%", 325, 10, 12, con_col)

        cull_status = "POCKETS CULLED (100% Path)" if cavern.is_culled else ("RAW NOISE" if cavern.generation_count == 0 else "UNCULLED (Pockets Exist)")
        draw_text(cull_status, 325, 30, 11, con_col)

        # Avatar inventory stats
        draw_text(f"Crystals: {avatar.crystals_collected}", 1140, 10, 12, Color(65, 230, 245, 255))
        draw_text(f"Blocks: {avatar.blocks_placed}", 1140, 30, 12, Color(240, 180, 95, 255))

        # Bottom hotkey guidance ribbon (y = 696..720)
        draw_rectangle(0, 696, SCREEN_WIDTH, 24, Color(12, 15, 24, 255))
        draw_line(0, 696, SCREEN_WIDTH, 696, Color(35, 48, 75, 255))

        legend = "[E/PadX] Step Automata  |  [F/PadB] Cull Pockets  |  [Q/PadY] New Map  |  [L-Click/Space] Mine  |  [R-Click/K] Place  |  [F1/LB] Toggle Cull  |  [Tab] X-Ray  |  [R] Reset"
        draw_text(legend, 14, 702, 11, Color(165, 180, 205, 255))

        # Mode Indicator Pill
        xray_tag = "X-RAY: ON (Chambers)" if show_xray else "LIGHTING: ON (Darkness)"
        xray_color = Color(255, 215, 50, 255) if show_xray else Color(80, 210, 255, 255)
        draw_text(xray_tag, 985, 702, 11, xray_color)


# ==============================================================================
# BLOCK 4: MAIN GAME LOOP & AUTOMATED SMOKE TEST
# ==============================================================================

class PatternLabGame:
    """
    Main interactive learning game combining 4-5 rule cellular automata,
    double-buffered ping-pong updates, BFS connectivity culling, and spelunker sandbox.
    """
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()

        self.sfx = SoundLibrary()
        self.sfx.init_defaults()

        # Core simulation systems
        self.cavern = CellularAutomataCavern(GRID_COLS, GRID_ROWS, initial_fill=47)
        # Pre-smooth 4 passes to begin in a rich organic cavern state
        self.cavern.auto_smooth(4)

        # Avatar spawn
        spawn_gx, spawn_gy = self.cavern.find_safe_spawn_tile()
        self.avatar = SpelunkerAvatar(spawn_gx, spawn_gy)

        self.telemetry = CavernTelemetry()
        self.particle_system = CavernParticleSystem(capacity=64)

        # Single-pattern lab defaults: X-Ray ON so learners immediately see internal state
        self.show_xray = True
        self.pattern_enabled = True  # True = Smoothed/Culled active, False = Raw Noise comparison

    def handle_inputs(self, dt: float):
        """Processes dual inputs (Keyboard/Mouse + Gamepad) simultaneously."""
        # 1. Toggles
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
            self.sfx.play("select", 0.6)

        if is_dual_pattern_toggle_pressed():
            self.pattern_enabled = not self.pattern_enabled
            if not self.pattern_enabled:
                self.cavern.restore_raw_noise()
            else:
                self.cavern.auto_smooth(4)
                self.cavern.cull_disconnected_pockets()
            spawn_gx, spawn_gy = self.cavern.find_safe_spawn_tile()
            self.avatar.reposition(spawn_gx, spawn_gy)
            self.sfx.play("click", 0.7)

        if is_dual_reset_pressed():
            self.cavern.generate_random_noise(47)
            self.cavern.auto_smooth(4)
            spawn_gx, spawn_gy = self.cavern.find_safe_spawn_tile()
            self.avatar.reposition(spawn_gx, spawn_gy)
            self.sfx.play("confirm", 0.8)

        # Hotkeys for Step, Cull, and Fresh Map
        # Key E / Gamepad X: Step 1 Automata Generation
        pad_id = get_active_gamepad_id()
        pad_x_pressed = (pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_FACE_LEFT))
        if is_key_pressed(KEY_E) or pad_x_pressed:
            self.cavern.step_automata()
            self.sfx.play("hit", 0.5)

        # Key F / Gamepad B: Execute Flood-Fill & Cull Pockets
        pad_b_pressed = (pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_FACE_RIGHT))
        if is_key_pressed(KEY_F) or pad_b_pressed:
            self.cavern.cull_disconnected_pockets()
            self.sfx.play("powerup", 0.6)

        # Key Q / Gamepad Y: Generate Fresh Noise Map
        pad_y_pressed = (pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_FACE_UP))
        if is_key_pressed(KEY_Q) or pad_y_pressed:
            self.cavern.generate_random_noise(47)
            spawn_gx, spawn_gy = self.cavern.find_safe_spawn_tile()
            self.avatar.reposition(spawn_gx, spawn_gy)
            self.sfx.play("click", 0.7)

        # 2. Spelunker Movement & Aim
        move_vec = get_dual_move_2d(deadzone=0.18, use_arrow_keys=True)
        look_vec = get_dual_look_2d(deadzone=0.18, use_arrow_keys=False)
        mouse_pos = get_mouse_position()

        self.avatar.update_aim(look_vec, mouse_pos)
        self.avatar.update(dt, move_vec, self.cavern)

        # 3. Interactive Mining & Block Placement
        # Primary Action: Mine wall at reticle / cursor
        if is_dual_primary_fire_pressed() and self.avatar.mine_cooldown <= 0.0:
            target_gx = int((mouse_pos.x - GRID_OFFSET_X) // CELL_SIZE)
            target_gy = int((mouse_pos.y - GRID_OFFSET_Y) // CELL_SIZE)

            # If aim is driven by gamepad stick, target tile 1 unit ahead in aim direction
            if abs(look_vec.x) > 0.3 or abs(look_vec.y) > 0.3:
                aim_front_x = self.avatar.x + math.cos(self.avatar.aim_angle) * (CELL_SIZE * 1.5)
                aim_front_y = self.avatar.y + math.sin(self.avatar.aim_angle) * (CELL_SIZE * 1.5)
                target_gx = int((aim_front_x - GRID_OFFSET_X) // CELL_SIZE)
                target_gy = int((aim_front_y - GRID_OFFSET_Y) // CELL_SIZE)

            if target_gx > 0 and target_gx < self.cavern.cols - 1 and target_gy > 0 and target_gy < self.cavern.rows - 1:
                cur_val = self.cavern.get_cell(target_gx, target_gy)
                if cur_val != TILE_OPEN:
                    tile_cx = float(GRID_OFFSET_X + target_gx * CELL_SIZE + CELL_SIZE // 2)
                    tile_cy = float(GRID_OFFSET_Y + target_gy * CELL_SIZE + CELL_SIZE // 2)

                    if cur_val == TILE_CRYSTAL:
                        self.avatar.crystals_collected += 1
                        self.particle_system.emit_debris(tile_cx, tile_cy, COLOR_CRYSTAL_CYAN, count=14, speed=160.0)
                        self.sfx.play("gem", 0.8)
                    else:
                        self.particle_system.emit_debris(tile_cx, tile_cy, COLOR_ROCK_HIGHLIGHT, count=9, speed=130.0)
                        self.sfx.play("hit", 0.6)

                    self.cavern.set_cell(target_gx, target_gy, TILE_OPEN)
                    self.cavern.analyze_connectivity()
                    self.avatar.mine_cooldown = 0.18

        # Secondary Action: Place reinforced block
        right_click = is_mouse_button_pressed(MOUSE_BUTTON_RIGHT)
        pad_lt_pressed = (pad_id >= 0 and is_gamepad_trigger_down(is_right_trigger=False, threshold=0.5))
        if (right_click or is_key_pressed(KEY_K) or pad_lt_pressed) and self.avatar.mine_cooldown <= 0.0:
            target_gx = int((mouse_pos.x - GRID_OFFSET_X) // CELL_SIZE)
            target_gy = int((mouse_pos.y - GRID_OFFSET_Y) // CELL_SIZE)

            if abs(look_vec.x) > 0.3 or abs(look_vec.y) > 0.3:
                aim_front_x = self.avatar.x + math.cos(self.avatar.aim_angle) * (CELL_SIZE * 1.5)
                aim_front_y = self.avatar.y + math.sin(self.avatar.aim_angle) * (CELL_SIZE * 1.5)
                target_gx = int((aim_front_x - GRID_OFFSET_X) // CELL_SIZE)
                target_gy = int((aim_front_y - GRID_OFFSET_Y) // CELL_SIZE)

            if target_gx > 0 and target_gx < self.cavern.cols - 1 and target_gy > 0 and target_gy < self.cavern.rows - 1:
                cur_val = self.cavern.get_cell(target_gx, target_gy)
                if cur_val == TILE_OPEN:
                    tile_cx = float(GRID_OFFSET_X + target_gx * CELL_SIZE + CELL_SIZE // 2)
                    tile_cy = float(GRID_OFFSET_Y + target_gy * CELL_SIZE + CELL_SIZE // 2)

                    # Ensure not placing block right on top of spelunker
                    dx = tile_cx - self.avatar.x
                    dy = tile_cy - self.avatar.y
                    if (dx * dx + dy * dy) > (CELL_SIZE * CELL_SIZE * 0.75):
                        self.cavern.set_cell(target_gx, target_gy, TILE_REINFORCED)
                        self.particle_system.emit_debris(tile_cx, tile_cy, COLOR_REINFORCED, count=6, speed=80.0)
                        self.avatar.blocks_placed += 1
                        self.cavern.analyze_connectivity()
                        self.avatar.mine_cooldown = 0.2
                        self.sfx.play("craft", 0.7)

    def update(self):
        """Simulation tick."""
        dt = min(get_frame_time(), 0.05)
        self.handle_inputs(dt)
        self.particle_system.update(dt)

    def draw_cavern_world(self):
        """Renders discrete subterranean rock tiles, mineral veins, and reinforced blocks."""
        buf = self.cavern.get_active_buffer()

        for gy in range(self.cavern.rows):
            for gx in range(self.cavern.cols):
                idx = gy * self.cavern.cols + gx
                cell_type = buf[idx]
                px = GRID_OFFSET_X + gx * CELL_SIZE
                py = GRID_OFFSET_Y + gy * CELL_SIZE

                if cell_type == TILE_WALL:
                    # Solid subterranean rock with 3D bevel shading
                    draw_rectangle(px, py, CELL_SIZE, CELL_SIZE, COLOR_ROCK_SOLID)
                    draw_rectangle(px, py, CELL_SIZE, 2, COLOR_ROCK_HIGHLIGHT)
                    draw_rectangle(px, py, 2, CELL_SIZE, COLOR_ROCK_HIGHLIGHT)
                    draw_rectangle(px + CELL_SIZE - 2, py, 2, CELL_SIZE, COLOR_ROCK_BORDER)
                    draw_rectangle(px, py + CELL_SIZE - 2, CELL_SIZE, 2, COLOR_ROCK_BORDER)

                elif cell_type == TILE_CRYSTAL:
                    # Gleaming cyan mineral embedded in rock
                    draw_rectangle(px, py, CELL_SIZE, CELL_SIZE, COLOR_ROCK_SOLID)
                    draw_circle(px + CELL_SIZE // 2, py + CELL_SIZE // 2, 4, COLOR_CRYSTAL_CYAN)
                    draw_circle(px + CELL_SIZE // 2, py + CELL_SIZE // 2, 6, COLOR_CRYSTAL_GLOW)

                elif cell_type == TILE_REINFORCED:
                    # Timber scaffold reinforcement block
                    draw_rectangle(px, py, CELL_SIZE, CELL_SIZE, COLOR_REINFORCED)
                    draw_rectangle_lines(px, py, CELL_SIZE, CELL_SIZE, COLOR_REINFORCED_TRIM)
                    draw_line(px, py, px + CELL_SIZE, py + CELL_SIZE, COLOR_REINFORCED_TRIM)
                    draw_line(px + CELL_SIZE, py, px, py + CELL_SIZE, COLOR_REINFORCED_TRIM)

                else:
                    # Open breathable cavern tunnel floor
                    draw_rectangle(px, py, CELL_SIZE, CELL_SIZE, COLOR_CAVERN_FLOOR)

    def draw(self):
        """Master render function integrating world, X-Ray overlay, lighting, and HUD."""
        begin_drawing()
        clear_background(COLOR_BG_DARK)

        # 1. Base Cavern World Tiles
        self.draw_cavern_world()

        # 2. X-Ray Chamber Visualizer Overlay ([Tab])
        if self.show_xray:
            self.telemetry.draw_region_overlay(self.cavern)

        # 3. Particle Systems (Excavation Debris & Sparkles)
        self.particle_system.draw()

        # 4. Spelunker Character Controller
        self.avatar.draw()

        # 5. Dynamic Subterranean Lighting & Flashlight Beam (Active when X-Ray is OFF)
        if not self.show_xray:
            self.telemetry.draw_subterranean_lighting(self.cavern, self.avatar)

        # 6. Interactive Cursor Hover Inspector
        mouse_pos = get_mouse_position()
        if mouse_pos.y > 54 and mouse_pos.y < 696:
            self.telemetry.draw_hover_inspector(self.cavern, mouse_pos)

        # 7. Telemetry HUD Dashboard & Controls Ribbon
        self.telemetry.draw_telemetry_hud(self.cavern, self.avatar, self.show_xray, self.pattern_enabled)

        # 8. Mandatory Global HUD Elements
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)

        end_drawing()

    def run(self, smoke_test: bool = False):
        """Main game loop with headless automated smoke test support."""
        frame_count = 0
        while not window_should_close():
            self.update()
            self.draw()
            frame_count += 1
            if smoke_test and frame_count >= 3:
                break

        self.sfx.unload_all()
        close_audio_device()
        close_window()


if __name__ == "__main__":
    is_smoke = "--smoke-test" in sys.argv
    PatternLabGame().run(smoke_test=is_smoke)
