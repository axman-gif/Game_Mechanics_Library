# -*- coding: utf-8 -*-
"""
Sokoban Deadlock Solver - Command Pattern Undo/Redo & Heuristic Deadlock Detection
==================================================================================
Section          : 3.7 Puzzle, Stealth & Other
Pattern Category : Puzzle, Stealth & Systemic Interactions (Command Pattern & Heuristic Traps)
Dimension        : 2D

Problem Solved:
  In discrete grid-based puzzle games like Sokoban, players frequently make fatal moves that render
  the puzzle mathematically unsolvable (deadlocked) long before they realize it. Without an undo
  system, a single mistake forces the player to restart the entire level from scratch, creating
  infuriating trial-and-error frustration. Furthermore, without real-time topological analysis,
  players waste dozens of moves pushing boxes in an already doomed state, unable to pinpoint where
  their reasoning failed.

How the Pattern Works:
  1. Command Pattern (Action Encapsulation & Reversible History):
     Every discrete player movement and crate push is reified into an immutable `MoveCommand` struct.
     The command records the exact delta (`dx, dy`), the previous player coordinates, whether a box
     was pushed, and the original and new coordinates of the pushed box.
     Two stacks govern time traversal:
       - `undo_stack`: Holds commands executed forward. Popping a command and calling `undo()`
         restores the previous game state in O(1) time without re-simulating from frame 0.
       - `redo_stack`: Holds commands that were undone. Calling `redo()` advances state forward.
         Pushing a fresh command clears the redo stack, establishing a new timeline branch.
     In C++, this maps directly to `std::vector<MoveCommand>` with `push_back()` and `pop_back()`,
     guaranteeing zero dynamic memory fragmentation and deterministic rollback.

  2. Heuristic Deadlock Detection (Mathematical Grid Topology):
     The engine combines static precomputation with dynamic runtime evaluation across three
     fundamental Sokoban deadlock theorems:
       - Theorem 1 (Corner Deadlock): Any non-goal tile bounded by two orthogonal impassable
         walls (e.g. North and East) is a static sink. A box placed here cannot be pushed along
         either axis and is permanently stuck.
       - Theorem 2 (Wall / Line Deadlock): Any continuous wall-hugging line segment bounded at
         both ends by corners or obstacles that contains ZERO goal tiles is a static deadlock zone.
         A box pushed against this wall can only slide parallel to it, but can never escape or score.
       - Theorem 3 (2x2 Freeze Deadlock): Any 2x2 cluster of tiles composed entirely of walls and
         boxes that contains at least one non-goal box is irrevocably frozen. No box in the cluster
         can be pushed outward because all adjacent push vectors are obstructed.
     When a box enters a deadlocked state, the solver immediately triggers a visual alert and
     pulsing hazard aura, allowing learners to immediately understand *why* the move failed.

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - Warehouse Keeper Movement     : WASD / Arrow Keys / Left Stick / D-Pad (Discrete tap or repeat)
  - Undo Step (Rewind History)    : Z / U / Gamepad LB / Gamepad B
  - Redo Step (Advance History)   : Y / Gamepad RB / Gamepad X
  - Level Select (1 to 4)         : [1], [2], [3], [4] / N (Next) / P (Previous)
  - Toggle Deadlock Assist ([F1]) : [F1] / Gamepad R3 (Compare assisted vs raw unassisted mode)
  - Toggle X-Ray Overlay ([Tab])  : [Tab] / Gamepad View (Inspect live danger map & command timeline)
  - Reset Current Level ([R])     : [R] / Gamepad Start
  - UI Settings Bar               : Click top bar dropdowns (Font, Font Size [Ctrl +/-], Fullscreen [F11])
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
WINDOW_TITLE = "Sokoban Deadlock Solver - Command Pattern & Heuristic Traps (Raylib)"

# Tile Dimensions & Layout
TILE_SIZE = 56
GRID_AREA_LEFT = 40
GRID_AREA_TOP = 80
GRID_AREA_WIDTH = 680
GRID_AREA_HEIGHT = 600

# Tile Codes (C++: enum class TileType : uint8_t)
TILE_FLOOR = 0
TILE_WALL = 1
TILE_GOAL = 2

# Static Deadlock Codes (C++: enum class StaticDeadlock : uint8_t)
DEADLOCK_NONE = 0
DEADLOCK_CORNER = 1
DEADLOCK_WALL = 2

# Dynamic Deadlock Types
DEADLOCK_STR_NONE = "NONE"
DEADLOCK_STR_CORNER = "CORNER DEADLOCK"
DEADLOCK_STR_WALL = "WALL LINE DEADLOCK"
DEADLOCK_STR_FREEZE = "2x2 FREEZE DEADLOCK"

# Visual Theme Palette (High-Contrast Clean Engineering)
COLOR_BG_DARK = Color(14, 16, 24, 255)
COLOR_PANEL_BG = Color(20, 24, 36, 255)
COLOR_PANEL_BORDER = Color(38, 46, 68, 255)

COLOR_FLOOR = Color(28, 32, 46, 255)
COLOR_FLOOR_LINE = Color(36, 42, 60, 255)
COLOR_WALL_BASE = Color(65, 75, 98, 255)
COLOR_WALL_TOP = Color(85, 98, 126, 255)
COLOR_WALL_SHADOW = Color(40, 46, 62, 255)

COLOR_GOAL_PAD = Color(42, 54, 52, 255)
COLOR_GOAL_RING = Color(60, 185, 150, 255)
COLOR_GOAL_CORE = Color(80, 240, 190, 255)

COLOR_CRATE_BASE = Color(190, 125, 55, 255)
COLOR_CRATE_TRIM = Color(225, 160, 85, 255)
COLOR_CRATE_RIVET = Color(110, 70, 30, 255)

COLOR_CRATE_GOAL_BASE = Color(35, 140, 95, 255)
COLOR_CRATE_GOAL_TRIM = Color(60, 205, 145, 255)

COLOR_DEADLOCK_PULSE = Color(235, 45, 65, 255)
COLOR_DEADLOCK_FILL = Color(235, 45, 65, 55)
COLOR_DEADLOCK_TEXT = Color(255, 100, 115, 255)

COLOR_TEXT_WHITE = Color(240, 245, 255, 255)
COLOR_TEXT_MUTED = Color(135, 148, 175, 255)
COLOR_TEXT_CYAN = Color(75, 215, 240, 255)
COLOR_TEXT_GOLD = Color(245, 195, 65, 255)
COLOR_TEXT_GREEN = Color(80, 235, 130, 255)

# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATION
# ==============================================================================
# 1. Action Reification: MoveCommand encapsulates discrete transitions.
# 2. Command History: Undo/Redo dual stack with zero dynamic heap churn.
# 3. Heuristic Deadlock Detector: Corner, Wall/Line, and 2x2 Freeze theorems.

class MoveCommand:
    """
    Encapsulates a single atomic state transition in the Sokoban world.
    
    C++ Translation:
      struct MoveCommand {
          int32_t dx;
          int32_t dy;
          int32_t player_old_x;
          int32_t player_old_y;
          bool box_pushed;
          int32_t box_id;
          int32_t box_old_x;
          int32_t box_old_y;
          int32_t box_new_x;
          int32_t box_new_y;
      };
    """
    def __init__(
        self,
        dx: int,
        dy: int,
        player_old_x: int,
        player_old_y: int,
        box_pushed: bool,
        box_id: int,
        box_old_x: int,
        box_old_y: int,
        box_new_x: int,
        box_new_y: int,
    ):
        self.dx = dx
        self.dy = dy
        self.player_old_x = player_old_x
        self.player_old_y = player_old_y
        self.box_pushed = box_pushed
        self.box_id = box_id
        self.box_old_x = box_old_x
        self.box_old_y = box_old_y
        self.box_new_x = box_new_x
        self.box_new_y = box_new_y

    def execute(self, world):
        """
        Executes the command forward, updating player and crate coordinates.
        Advances simulation step counter.
        """
        world.player.grid_x = self.player_old_x + self.dx
        world.player.grid_y = self.player_old_y + self.dy
        world.player.facing_dx = self.dx
        world.player.facing_dy = self.dy

        if self.box_pushed:
            box = world.get_box_by_id(self.box_id)
            if box is not None:
                box.grid_x = self.box_new_x
                box.grid_y = self.box_new_y
            world.push_count += 1

        world.move_count += 1

    def undo(self, world):
        """
        Reverses the command backward, perfectly restoring previous state.
        Decrements simulation step counter.
        """
        world.player.grid_x = self.player_old_x
        world.player.grid_y = self.player_old_y
        world.player.facing_dx = -self.dx
        world.player.facing_dy = -self.dy

        if self.box_pushed:
            box = world.get_box_by_id(self.box_id)
            if box is not None:
                box.grid_x = self.box_old_x
                box.grid_y = self.box_old_y
            world.push_count -= 1

        world.move_count -= 1

    def redo(self, world):
        """Re-applies the command forward."""
        self.execute(world)

    def get_description(self) -> str:
        """Returns a concise pedagogical label for telemetry timelines."""
        direction_name = "STILL"
        if self.dx == 1:
            direction_name = "RIGHT"
        elif self.dx == -1:
            direction_name = "LEFT"
        elif self.dy == 1:
            direction_name = "DOWN"
        elif self.dy == -1:
            direction_name = "UP"

        if self.box_pushed:
            return f"PUSH {direction_name} [Box #{self.box_id + 1}]"
        else:
            return f"STEP {direction_name}"


class CommandHistory:
    """
    Manages the two reversible stacks (Undo Stack and Redo Stack).
    
    C++ Translation:
      class CommandHistory {
          std::vector<MoveCommand> undo_stack;
          std::vector<MoveCommand> redo_stack;
          size_t max_capacity;
      };
    """
    def __init__(self, max_capacity: int = 1000):
        self.undo_stack = []
        self.redo_stack = []
        self.max_capacity = max_capacity

    def push_executed(self, cmd: MoveCommand):
        """
        Pushes a newly executed command onto the undo stack.
        Clears the redo stack because a new timeline branch has been taken.
        """
        self.undo_stack.append(cmd)
        self.redo_stack.clear()
        if len(self.undo_stack) > self.max_capacity:
            self.undo_stack.pop(0)

    def undo(self, world) -> bool:
        """Pops the top command from undo stack, reverses it, pushes to redo."""
        if len(self.undo_stack) == 0:
            return False
        cmd = self.undo_stack.pop()
        cmd.undo(world)
        self.redo_stack.append(cmd)
        return True

    def redo(self, world) -> bool:
        """Pops the top command from redo stack, reapplies it, pushes to undo."""
        if len(self.redo_stack) == 0:
            return False
        cmd = self.redo_stack.pop()
        cmd.redo(world)
        self.undo_stack.append(cmd)
        return True

    def can_undo(self) -> bool:
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        return len(self.redo_stack) > 0

    def clear(self):
        self.undo_stack.clear()
        self.redo_stack.clear()

    def get_recent_history(self, count: int = 7):
        """
        Returns up to `count` recent commands from the undo stack for timeline display.
        Uses an explicit for loop to comply with C++ transferable rules.
        """
        recent = []
        total = len(self.undo_stack)
        start_idx = max(0, total - count)
        for i in range(start_idx, total):
            recent.append(self.undo_stack[i])
        return recent


class DeadlockDetector:
    """
    Mathematical Heuristic Deadlock Detection Engine for Sokoban.
    
    Analyzes grid topology to detect non-recoverable puzzle states:
      1. Corner Deadlock (Static): Box pushed into orthogonal wall intersection.
      2. Wall Line Deadlock (Static): Box pushed onto wall segment with no goals.
      3. 2x2 Freeze Deadlock (Dynamic): 2x2 cluster of solid blocks containing >= 1 non-goal box.
    """
    def __init__(self):
        self.static_map = []  # 2D grid [y][x] of DEADLOCK_NONE, CORNER, or WALL
        self.grid_width = 0
        self.grid_height = 0
        self.deadlocked_box_ids = []
        self.deadlock_reasons = []

    def build_static_map(self, width: int, height: int, is_wall_grid, is_goal_grid):
        """
        Precomputes static deadlock zones across the entire board.
        Static deadlocks depend purely on the wall geometry and goal placements.
        """
        self.grid_width = width
        self.grid_height = height
        self.static_map = []
        for y in range(height):
            row = []
            for x in range(width):
                row.append(DEADLOCK_NONE)
            self.static_map.append(row)

        # ----------------------------------------------------------------------
        # Step 1: Detect Corner Deadlocks
        # A floor tile that is NOT a goal is a corner deadlock if it has walls
        # in at least two orthogonal directions (e.g. North & West).
        # ----------------------------------------------------------------------
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                if not is_wall_grid[y][x] and not is_goal_grid[y][x]:
                    wall_n = is_wall_grid[y - 1][x]
                    wall_s = is_wall_grid[y + 1][x]
                    wall_w = is_wall_grid[y][x - 1]
                    wall_e = is_wall_grid[y][x + 1]

                    is_corner = (
                        (wall_n and wall_w) or
                        (wall_n and wall_e) or
                        (wall_s and wall_w) or
                        (wall_s and wall_e)
                    )
                    if is_corner:
                        self.static_map[y][x] = DEADLOCK_CORNER

        # ----------------------------------------------------------------------
        # Step 2: Detect Wall / Line Deadlocks
        # If a floor tile is against a flat continuous wall (e.g. North wall),
        # a box pushed there can only move horizontally. If the entire segment
        # terminates in walls at both ends and contains ZERO goals, any box pushed
        # anywhere on that line is permanently stuck!
        # ----------------------------------------------------------------------
        # Scan along Horizontal Walls (North Wall & South Wall)
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                if not is_wall_grid[y][x] and not is_goal_grid[y][x]:
                    if self.static_map[y][x] == DEADLOCK_NONE:
                        # Case A: North Wall
                        if is_wall_grid[y - 1][x]:
                            has_goal = False
                            # Scan west along wall
                            can_escape_west = False
                            wx = x
                            while wx >= 0 and not is_wall_grid[y][wx] and is_wall_grid[y - 1][wx]:
                                if is_goal_grid[y][wx]:
                                    has_goal = True
                                wx -= 1
                            if wx < 0 or not is_wall_grid[y][wx]:
                                can_escape_west = True

                            # Scan east along wall
                            can_escape_east = False
                            ex = x
                            while ex < width and not is_wall_grid[y][ex] and is_wall_grid[y - 1][ex]:
                                if is_goal_grid[y][ex]:
                                    has_goal = True
                                ex += 1
                            if ex >= width or not is_wall_grid[y][ex]:
                                can_escape_east = True

                            if not has_goal and not can_escape_west and not can_escape_east:
                                self.static_map[y][x] = DEADLOCK_WALL

                        # Case B: South Wall
                        if is_wall_grid[y + 1][x] and self.static_map[y][x] == DEADLOCK_NONE:
                            has_goal = False
                            can_escape_west = False
                            wx = x
                            while wx >= 0 and not is_wall_grid[y][wx] and is_wall_grid[y + 1][wx]:
                                if is_goal_grid[y][wx]:
                                    has_goal = True
                                wx -= 1
                            if wx < 0 or not is_wall_grid[y][wx]:
                                can_escape_west = True

                            can_escape_east = False
                            ex = x
                            while ex < width and not is_wall_grid[y][ex] and is_wall_grid[y + 1][ex]:
                                if is_goal_grid[y][ex]:
                                    has_goal = True
                                ex += 1
                            if ex >= width or not is_wall_grid[y][ex]:
                                can_escape_east = True

                            if not has_goal and not can_escape_west and not can_escape_east:
                                self.static_map[y][x] = DEADLOCK_WALL

        # Scan along Vertical Walls (West Wall & East Wall)
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                if not is_wall_grid[y][x] and not is_goal_grid[y][x]:
                    if self.static_map[y][x] == DEADLOCK_NONE:
                        # Case C: West Wall
                        if is_wall_grid[y][x - 1]:
                            has_goal = False
                            can_escape_north = False
                            ny = y
                            while ny >= 0 and not is_wall_grid[ny][x] and is_wall_grid[ny][x - 1]:
                                if is_goal_grid[ny][x]:
                                    has_goal = True
                                ny -= 1
                            if ny < 0 or not is_wall_grid[ny][x]:
                                can_escape_north = True

                            can_escape_south = False
                            sy = y
                            while sy < height and not is_wall_grid[sy][x] and is_wall_grid[sy][x - 1]:
                                if is_goal_grid[sy][x]:
                                    has_goal = True
                                sy += 1
                            if sy >= height or not is_wall_grid[sy][x]:
                                can_escape_south = True

                            if not has_goal and not can_escape_north and not can_escape_south:
                                self.static_map[y][x] = DEADLOCK_WALL

                        # Case D: East Wall
                        if is_wall_grid[y][x + 1] and self.static_map[y][x] == DEADLOCK_NONE:
                            has_goal = False
                            can_escape_north = False
                            ny = y
                            while ny >= 0 and not is_wall_grid[ny][x] and is_wall_grid[ny][x + 1]:
                                if is_goal_grid[ny][x]:
                                    has_goal = True
                                ny -= 1
                            if ny < 0 or not is_wall_grid[ny][x]:
                                can_escape_north = True

                            can_escape_south = False
                            sy = y
                            while sy < height and not is_wall_grid[sy][x] and is_wall_grid[sy][x + 1]:
                                if is_goal_grid[sy][x]:
                                    has_goal = True
                                sy += 1
                            if sy >= height or not is_wall_grid[sy][x]:
                                can_escape_south = True

                            if not has_goal and not can_escape_north and not can_escape_south:
                                self.static_map[y][x] = DEADLOCK_WALL

    def evaluate_live_deadlocks(self, boxes, is_wall_grid, is_goal_grid):
        """
        Evaluates dynamic deadlocks on the current game frame.
        Identifies active deadlocks (Static Corner/Wall or 2x2 Square Freeze).
        """
        self.deadlocked_box_ids.clear()
        self.deadlock_reasons.clear()

        # Build box spatial lookup
        box_coords = set()
        coord_to_box = {}
        for b in boxes:
            box_coords.add((b.grid_x, b.grid_y))
            coord_to_box[(b.grid_x, b.grid_y)] = b
            b.is_deadlocked = False
            b.deadlock_type = DEADLOCK_STR_NONE

        # ----------------------------------------------------------------------
        # Test 1 & 2: Static Corner and Wall Deadlocks
        # ----------------------------------------------------------------------
        for b in boxes:
            bx = b.grid_x
            by = b.grid_y
            # If the box is already resting on a valid goal, it is safe from static deadlocks
            if is_goal_grid[by][bx]:
                continue

            static_code = self.static_map[by][bx]
            if static_code == DEADLOCK_CORNER:
                b.is_deadlocked = True
                b.deadlock_type = DEADLOCK_STR_CORNER
                self.deadlocked_box_ids.append(b.id)
                self.deadlock_reasons.append(
                    f"Box #{b.id + 1} trapped in CORNER at ({bx}, {by})."
                )
            elif static_code == DEADLOCK_WALL:
                b.is_deadlocked = True
                b.deadlock_type = DEADLOCK_STR_WALL
                self.deadlocked_box_ids.append(b.id)
                self.deadlock_reasons.append(
                    f"Box #{b.id + 1} trapped on WALL LINE at ({bx}, {by}) with no reachable goal."
                )

        # ----------------------------------------------------------------------
        # Test 3: 2x2 Square Freeze Deadlock
        # Any 2x2 cluster of solid blocks (walls or boxes) containing at least
        # one non-goal box cannot be pushed or separated.
        # ----------------------------------------------------------------------
        # Define 4 quadrant 2x2 square offsets surrounding any coordinate (bx, by)
        square_quadrants = [
            [(0, 0), (1, 0), (0, 1), (1, 1)],     # Top-Left anchor
            [(-1, 0), (0, 0), (-1, 1), (0, 1)],   # Top-Right anchor
            [(0, -1), (1, -1), (0, 0), (1, 0)],   # Bottom-Left anchor
            [(-1, -1), (0, -1), (-1, 0), (0, 0)]  # Bottom-Right anchor
        ]

        for b in boxes:
            bx = b.grid_x
            by = b.grid_y

            for quad in square_quadrants:
                all_solid = True
                has_non_goal_box = False
                quad_boxes = []

                for ox, oy in quad:
                    tx = bx + ox
                    ty = by + oy
                    if tx < 0 or tx >= self.grid_width or ty < 0 or ty >= self.grid_height:
                        all_solid = False
                        break

                    is_w = is_wall_grid[ty][tx]
                    is_b = (tx, ty) in box_coords

                    if not is_w and not is_b:
                        all_solid = False
                        break

                    if is_b:
                        qb = coord_to_box[(tx, ty)]
                        quad_boxes.append(qb)
                        if not is_goal_grid[ty][tx]:
                            has_non_goal_box = True

                # If all 4 tiles in the 2x2 are solid and at least one box is off-goal:
                if all_solid and has_non_goal_box and len(quad_boxes) > 0:
                    for qb in quad_boxes:
                        qb.is_deadlocked = True
                        qb.deadlock_type = DEADLOCK_STR_FREEZE
                        # Add to list if not already present
                        already_in = False
                        for did in self.deadlocked_box_ids:
                            if did == qb.id:
                                already_in = True
                                break
                        if not already_in:
                            self.deadlocked_box_ids.append(qb.id)
                            self.deadlock_reasons.append(
                                f"Box #{qb.id + 1} frozen in 2x2 BLOCK CLUSTER at ({qb.grid_x}, {qb.grid_y})."
                            )


# ==============================================================================
# BLOCK 2: WORLD SIMULATION & ENTITIES
# ==============================================================================
# Entities, grid environment, level definitions, and smooth visual dampening.

class GoalEntity:
    """Represents a designated storage goal tile in the warehouse."""
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.covered = False


class BoxEntity:
    """Represents a pushable wooden crate with smooth visual interpolation."""
    def __init__(self, box_id: int, grid_x: int, grid_y: int):
        self.id = box_id
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.visual_x = float(grid_x)
        self.visual_y = float(grid_y)
        self.on_goal = False
        self.is_deadlocked = False
        self.deadlock_type = DEADLOCK_STR_NONE
        self.pulse_timer = 0.0

    def update(self, dt: float):
        # Exponential smoothing towards grid target
        self.visual_x = damp(self.visual_x, float(self.grid_x), 18.0, dt)
        self.visual_y = damp(self.visual_y, float(self.grid_y), 18.0, dt)
        self.pulse_timer += dt * 4.0


class PlayerEntity:
    """Represents the warehouse keeper character."""
    def __init__(self, grid_x: int, grid_y: int):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.visual_x = float(grid_x)
        self.visual_y = float(grid_y)
        self.facing_dx = 0
        self.facing_dy = 1
        self.walk_anim_timer = 0.0

    def update(self, dt: float):
        # Smooth interpolation
        dist_x = abs(self.visual_x - float(self.grid_x))
        dist_y = abs(self.visual_y - float(self.grid_y))
        if dist_x > 0.01 or dist_y > 0.01:
            self.walk_anim_timer += dt * 10.0
        self.visual_x = damp(self.visual_x, float(self.grid_x), 20.0, dt)
        self.visual_y = damp(self.visual_y, float(self.grid_y), 20.0, dt)


class SokobanWorld:
    """
    Simulates the discrete grid puzzle and coordinates command history.
    Contains 4 curated, mathematically verified solvable levels.
    """
    def __init__(self):
        self.width = 0
        self.height = 0
        self.is_wall_grid = []
        self.is_goal_grid = []
        self.goals = []
        self.boxes = []
        self.player = PlayerEntity(0, 0)
        self.history = CommandHistory()
        self.detector = DeadlockDetector()

        self.move_count = 0
        self.push_count = 0
        self.active_level_idx = 0
        self.is_puzzle_won = False
        self.level_names = [
            "Level 1: Micro-Tutorial (Corner Deadlock Trap)",
            "Level 2: Classic Squeeze (Interior Wall Obstacles)",
            "Level 3: Warehouse Central (Coordination & Flow)",
            "Level 4: Complex Deadlock Arena (Symmetric Barrier)"
        ]

        # 4 Verified classic levels (100% solvable with exact solutions)
        self.raw_levels = [
            # Level 1: 7x7 (1 box, 1 goal, 4 corner traps)
            (
                "#######\n"
                "#     #\n"
                "#  $  #\n"
                "#  .  #\n"
                "#  @  #\n"
                "#     #\n"
                "#######"
            ),
            # Level 2: 8x8 (2 boxes, 2 goals)
            (
                "########\n"
                "#  .   #\n"
                "#  #$  #\n"
                "#  $   #\n"
                "#  #   #\n"
                "#  .   #\n"
                "#  @   #\n"
                "########"
            ),
            # Level 3: 8x7 (3 boxes, 3 goals)
            (
                "########\n"
                "# .    #\n"
                "# $ $  #\n"
                "#  #   #\n"
                "# .$.  #\n"
                "#   @  #\n"
                "########"
            ),
            # Level 4: 9x8 (3 boxes, 3 goals around central barrier)
            (
                "#########\n"
                "#       #\n"
                "# . $ . #\n"
                "#  ###  #\n"
                "#  $@$  #\n"
                "#   .   #\n"
                "#       #\n"
                "#########"
            )
        ]

        self.load_level(0)

    def load_level(self, level_idx: int):
        """Parses an ASCII level layout into discrete grid entities."""
        self.active_level_idx = max(0, min(level_idx, len(self.raw_levels) - 1))
        raw_str = self.raw_levels[self.active_level_idx]
        lines = []
        for l in raw_str.strip().split("\n"):
            if len(l) > 0:
                lines.append(l)

        self.height = len(lines)
        self.width = 0
        for l in lines:
            if len(l) > self.width:
                self.width = len(l)

        # Build grids
        self.is_wall_grid = []
        self.is_goal_grid = []
        for y in range(self.height):
            wall_row = []
            goal_row = []
            for x in range(self.width):
                wall_row.append(False)
                goal_row.append(False)
            self.is_wall_grid.append(wall_row)
            self.is_goal_grid.append(goal_row)

        self.goals.clear()
        self.boxes.clear()
        self.history.clear()
        self.move_count = 0
        self.push_count = 0
        self.is_puzzle_won = False

        box_counter = 0
        for y in range(self.height):
            line_str = lines[y].ljust(self.width)
            for x in range(self.width):
                c = line_str[x]
                if c == "#":
                    self.is_wall_grid[y][x] = True
                elif c == ".":
                    self.is_goal_grid[y][x] = True
                    self.goals.append(GoalEntity(x, y))
                elif c == "$":
                    box = BoxEntity(box_counter, x, y)
                    self.boxes.append(box)
                    box_counter += 1
                elif c == "*":
                    self.is_goal_grid[y][x] = True
                    self.goals.append(GoalEntity(x, y))
                    box = BoxEntity(box_counter, x, y)
                    box.on_goal = True
                    self.boxes.append(box)
                    box_counter += 1
                elif c == "@":
                    self.player = PlayerEntity(x, y)
                elif c == "+":
                    self.is_goal_grid[y][x] = True
                    self.goals.append(GoalEntity(x, y))
                    self.player = PlayerEntity(x, y)

        # Precalculate Static Deadlock Map
        self.detector.build_static_map(
            self.width,
            self.height,
            self.is_wall_grid,
            self.is_goal_grid
        )

        # Initial validation of dynamic state
        self.update_goal_status()
        self.detector.evaluate_live_deadlocks(
            self.boxes,
            self.is_wall_grid,
            self.is_goal_grid
        )

    def reset_level(self):
        """Reloads the current level from scratch."""
        self.load_level(self.active_level_idx)

    def get_box_at(self, x: int, y: int):
        """Returns the box at (x, y) or None."""
        for b in self.boxes:
            if b.grid_x == x and b.grid_y == y:
                return b
        return None

    def get_box_by_id(self, box_id: int):
        """Returns the box with specific id or None."""
        for b in self.boxes:
            if b.id == box_id:
                return b
        return None

    def try_move(self, dx: int, dy: int) -> bool:
        """
        Attempts to move player in direction (dx, dy).
        If unobstructed: produces and executes a MoveCommand.
        If facing a box: checks if the tile behind the box is open. If so, pushes.
        Returns True if a move or push occurred.
        """
        if dx == 0 and dy == 0:
            return False

        target_x = self.player.grid_x + dx
        target_y = self.player.grid_y + dy

        # Check bounds
        if target_x < 0 or target_x >= self.width or target_y < 0 or target_y >= self.height:
            return False

        # Check wall collision
        if self.is_wall_grid[target_y][target_x]:
            return False

        # Check box collision
        box = self.get_box_at(target_x, target_y)
        if box is not None:
            # Box push destination
            box_dest_x = target_x + dx
            box_dest_y = target_y + dy

            # Check bounds for pushed box
            if (
                box_dest_x < 0 or box_dest_x >= self.width or
                box_dest_y < 0 or box_dest_y >= self.height
            ):
                return False

            # Check if destination tile is blocked by wall or another box
            if self.is_wall_grid[box_dest_y][box_dest_x]:
                return False
            if self.get_box_at(box_dest_x, box_dest_y) is not None:
                return False

            # Valid Push Command!
            cmd = MoveCommand(
                dx,
                dy,
                self.player.grid_x,
                self.player.grid_y,
                True,
                box.id,
                box.grid_x,
                box.grid_y,
                box_dest_x,
                box_dest_y
            )
            self.history.push_executed(cmd)
            cmd.execute(self)
            self.update_goal_status()
            self.detector.evaluate_live_deadlocks(
                self.boxes,
                self.is_wall_grid,
                self.is_goal_grid
            )
            return True

        else:
            # Valid Walk Command!
            cmd = MoveCommand(
                dx,
                dy,
                self.player.grid_x,
                self.player.grid_y,
                False,
                -1,
                0,
                0,
                0,
                0
            )
            self.history.push_executed(cmd)
            cmd.execute(self)
            self.update_goal_status()
            self.detector.evaluate_live_deadlocks(
                self.boxes,
                self.is_wall_grid,
                self.is_goal_grid
            )
            return True

    def undo_step(self) -> bool:
        """Pops command from undo stack and reverses state."""
        success = self.history.undo(self)
        if success:
            self.update_goal_status()
            self.detector.evaluate_live_deadlocks(
                self.boxes,
                self.is_wall_grid,
                self.is_goal_grid
            )
        return success

    def redo_step(self) -> bool:
        """Pops command from redo stack and reapplies state."""
        success = self.history.redo(self)
        if success:
            self.update_goal_status()
            self.detector.evaluate_live_deadlocks(
                self.boxes,
                self.is_wall_grid,
                self.is_goal_grid
            )
        return success

    def update_goal_status(self):
        """Checks which goal tiles are covered by boxes and evaluates victory."""
        all_covered = True
        for g in self.goals:
            b = self.get_box_at(g.x, g.y)
            if b is not None:
                g.covered = True
                b.on_goal = True
            else:
                g.covered = False
                all_covered = False

        # Reset on_goal flags for boxes not on any goal
        for b in self.boxes:
            if not self.is_goal_grid[b.grid_y][b.grid_x]:
                b.on_goal = False

        self.is_puzzle_won = all_covered and len(self.goals) > 0

    def update(self, dt: float):
        """Updates entity smooth visual positions and animations."""
        self.player.update(dt)
        for b in self.boxes:
            b.update(dt)


# ==============================================================================
# BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY
# ==============================================================================
# High-contrast warehouse visualizer, live deadlock danger maps,
# and visual command history timeline scrubbers.

def draw_warehouse_tile_floor(px: int, py: int, size: int):
    """Renders a beveled slate floor tile."""
    draw_rectangle(px, py, size, size, COLOR_FLOOR)
    draw_rectangle_lines(px, py, size, size, COLOR_FLOOR_LINE)


def draw_warehouse_tile_wall(px: int, py: int, size: int):
    """Renders a solid brick wall block with 3D beveling."""
    draw_rectangle(px, py, size, size, COLOR_WALL_BASE)
    draw_rectangle(px + 4, py + 4, size - 8, size - 8, COLOR_WALL_TOP)
    draw_line(px, py + size - 1, px + size - 1, py + size - 1, COLOR_WALL_SHADOW)
    draw_line(px + size - 1, py, px + size - 1, py + size - 1, COLOR_WALL_SHADOW)
    draw_rectangle_lines(px, py, size, size, COLOR_PANEL_BORDER)


def draw_warehouse_goal(px: int, py: int, size: int, covered: bool):
    """Renders a glowing goal storage pad."""
    cx = px + size // 2
    cy = py + size // 2
    radius = size // 3

    draw_circle(cx, cy, float(radius + 2), COLOR_GOAL_PAD)
    if covered:
        draw_circle(cx, cy, float(radius), Color(40, 160, 110, 140))
        draw_circle(cx, cy, float(radius // 2), COLOR_GOAL_CORE)
    else:
        draw_circle_lines(cx, cy, float(radius), COLOR_GOAL_RING)
        draw_circle_lines(cx, cy, float(radius // 2), COLOR_GOAL_CORE)
        draw_circle(cx, cy, 3.0, COLOR_GOAL_CORE)


def draw_crate(box: BoxEntity, px: int, py: int, size: int, deadlock_active: bool):
    """Renders a wooden warehouse crate with steel rivets and warning aura."""
    inset = 4
    crate_x = px + inset
    crate_y = py + inset
    crate_size = size - inset * 2

    base_col = COLOR_CRATE_BASE
    trim_col = COLOR_CRATE_TRIM
    if box.on_goal:
        base_col = COLOR_CRATE_GOAL_BASE
        trim_col = COLOR_CRATE_GOAL_TRIM

    # Draw crate body
    draw_rectangle(crate_x, crate_y, crate_size, crate_size, base_col)
    draw_rectangle_lines(crate_x, crate_y, crate_size, crate_size, trim_col)

    # Diagonal bracing
    draw_line(crate_x, crate_y, crate_x + crate_size, crate_y + crate_size, trim_col)
    draw_line(crate_x + crate_size, crate_y, crate_x, crate_y + crate_size, trim_col)

    # Rivets
    r_off = 5
    draw_rectangle(crate_x + r_off, crate_y + r_off, 4, 4, COLOR_CRATE_RIVET)
    draw_rectangle(crate_x + crate_size - r_off - 4, crate_y + r_off, 4, 4, COLOR_CRATE_RIVET)
    draw_rectangle(crate_x + r_off, crate_y + crate_size - r_off - 4, 4, 4, COLOR_CRATE_RIVET)
    draw_rectangle(crate_x + crate_size - r_off - 4, crate_y + crate_size - r_off - 4, 4, 4, COLOR_CRATE_RIVET)

    # Box number badge
    label = f"#{box.id + 1}"
    draw_text(label, crate_x + 8, crate_y + 6, 12, Color(255, 255, 255, 220))

    # Deadlock warning aura and badge (Only when deadlock detection pattern is ON)
    if box.is_deadlocked and deadlock_active:
        pulse_alpha = int(140 + 115 * math.sin(box.pulse_timer))
        pulse_alpha = clamp(pulse_alpha, 50, 255)
        warn_color = Color(240, 40, 50, pulse_alpha)

        # Pulsing outer hazard border
        draw_rectangle_lines_ex(
            Rectangle(float(crate_x - 3), float(crate_y - 3), float(crate_size + 6), float(crate_size + 6)),
            3.0,
            warn_color
        )

        # Warning icon badge in center
        badge_cx = crate_x + crate_size // 2
        badge_cy = crate_y + crate_size // 2
        draw_circle(badge_cx, badge_cy, 12.0, Color(220, 20, 30, 240))
        draw_circle_lines(badge_cx, badge_cy, 12.0, Color(255, 255, 255, 255))
        draw_text("!", badge_cx - 3, badge_cy - 7, 16, COLOR_TEXT_WHITE)


def draw_warehouse_player(player: PlayerEntity, px: int, py: int, size: int):
    """Renders the warehouse keeper with hard-hat and directional facing."""
    cx = px + size // 2
    cy = py + size // 2

    # Body torso
    body_width = size // 2
    body_height = size // 2
    bx = cx - body_width // 2
    by = cy - body_height // 2 + 4
    draw_rectangle(bx, by, body_width, body_height, Color(45, 110, 195, 255))
    draw_rectangle_lines(bx, by, body_width, body_height, Color(75, 150, 245, 255))

    # Head / Hard hat (Safety Yellow)
    head_radius = size // 4
    head_cy = cy - 6
    draw_circle(cx, head_cy, float(head_radius), Color(245, 190, 40, 255))
    draw_circle_lines(cx, head_cy, float(head_radius), Color(255, 230, 120, 255))

    # Directional facing visor / visor beam
    eye_dx = player.facing_dx * 5
    eye_dy = player.facing_dy * 5
    draw_circle(cx + eye_dx, head_cy + eye_dy, 4.0, Color(20, 24, 32, 255))


def draw_static_deadlock_overlay(x: int, y: int, size: int, deadlock_code: int):
    """Draws danger zone telemetry on the grid (Corner 'C' or Wall 'W')."""
    if deadlock_code == DEADLOCK_CORNER:
        draw_rectangle(x + 2, y + 2, size - 4, size - 4, Color(230, 40, 60, 45))
        draw_rectangle_lines(x + 2, y + 2, size - 4, size - 4, Color(230, 40, 60, 120))
        draw_text("CORNER", x + 6, y + 6, 10, Color(255, 120, 130, 200))
        draw_text("TRAP", x + 12, y + 18, 10, Color(255, 120, 130, 200))

    elif deadlock_code == DEADLOCK_WALL:
        draw_rectangle(x + 2, y + 2, size - 4, size - 4, Color(240, 140, 40, 35))
        draw_rectangle_lines(x + 2, y + 2, size - 4, size - 4, Color(240, 140, 40, 100))
        draw_text("DEAD", x + 12, y + 6, 10, Color(255, 180, 90, 180))
        draw_text("WALL", x + 12, y + 18, 10, Color(255, 180, 90, 180))


def draw_telemetry_panel(
    world: SokobanWorld,
    x: int,
    y: int,
    w: int,
    h: int,
    pattern_enabled: bool,
    show_xray: bool
):
    """
    Renders the right-hand HUD telemetry inspector:
      - Goal progress meter
      - Command History timeline scrubber (Undo/Redo stacks)
      - Live Deadlock Status diagnosis
      - Architectural C++ patterns & heuristic proofs
    """
    draw_rectangle(x, y, w, h, COLOR_PANEL_BG)
    draw_rectangle_lines(x, y, w, h, COLOR_PANEL_BORDER)

    cursor_y = y + 14

    # 1. Level Title & Progress
    level_name = world.level_names[world.active_level_idx]
    draw_text(level_name, x + 16, cursor_y, 16, COLOR_TEXT_WHITE)
    cursor_y += 24

    goals_solved = 0
    for g in world.goals:
        if g.covered:
            goals_solved += 1
    total_goals = len(world.goals)

    stat_line = f"GOALS COVERED: {goals_solved}/{total_goals}   |   MOVES: {world.move_count}   |   PUSHES: {world.push_count}"
    draw_text(stat_line, x + 16, cursor_y, 13, COLOR_TEXT_MUTED)
    cursor_y += 20

    # Solved Progress Bar
    bar_width = w - 32
    bar_height = 8
    draw_rectangle(x + 16, cursor_y, bar_width, bar_height, Color(35, 42, 58, 255))
    if total_goals > 0:
        fill_w = int(bar_width * (goals_solved / float(total_goals)))
        draw_rectangle(x + 16, cursor_y, fill_w, bar_height, COLOR_TEXT_GREEN)
    cursor_y += 18

    # --------------------------------------------------------------------------
    # 2. Live Heuristic Deadlock Analyzer Card
    # --------------------------------------------------------------------------
    card_h = 104
    draw_rectangle(x + 16, cursor_y, bar_width, card_h, Color(25, 30, 44, 255))
    draw_rectangle_lines(x + 16, cursor_y, bar_width, card_h, COLOR_PANEL_BORDER)

    num_deadlocks = len(world.detector.deadlocked_box_ids)

    if not pattern_enabled:
        # Pattern OFF state
        draw_text(
            "HEURISTIC DEADLOCK ASSIST: [OFF] (Raw Unassisted)",
            x + 26,
            cursor_y + 10,
            13,
            Color(160, 165, 180, 255)
        )
        draw_text(
            "Press [F1] / Gamepad R3 to enable live deadlock prediction.",
            x + 26,
            cursor_y + 32,
            12,
            COLOR_TEXT_MUTED
        )
        draw_text(
            "In raw mode, fatal pushes provide zero warning to the player.",
            x + 26,
            cursor_y + 52,
            12,
            COLOR_TEXT_MUTED
        )
        draw_text(
            "Status: DETECTION SILENCED",
            x + 26,
            cursor_y + 76,
            13,
            COLOR_TEXT_GOLD
        )
    else:
        if num_deadlocks > 0:
            # Fatal deadlock active
            draw_text(
                "⚠️ DEADLOCK DETECTED! PUZZLE STATE UNSOLVABLE!",
                x + 26,
                cursor_y + 10,
                14,
                COLOR_DEADLOCK_PULSE
            )
            # Display first 2 reasons
            reason_line = world.detector.deadlock_reasons[0]
            if len(reason_line) > 60:
                reason_line = reason_line[:60] + "..."
            draw_text(reason_line, x + 26, cursor_y + 34, 12, COLOR_DEADLOCK_TEXT)

            if len(world.detector.deadlock_reasons) > 1:
                reason_line2 = world.detector.deadlock_reasons[1]
                if len(reason_line2) > 60:
                    reason_line2 = reason_line2[:60] + "..."
                draw_text(reason_line2, x + 26, cursor_y + 52, 12, COLOR_DEADLOCK_TEXT)
            else:
                draw_text("Box cannot reach any goal. Undo to recover!", x + 26, cursor_y + 52, 12, COLOR_TEXT_MUTED)

            draw_text("ACTION REQUIRED: Press [Z] or Gamepad LB to UNDO move", x + 26, cursor_y + 76, 12, COLOR_TEXT_CYAN)

        elif world.is_puzzle_won:
            draw_text(
                "🎉 LEVEL COMPLETE! ALL STORAGE GOALS SECURED!",
                x + 26,
                cursor_y + 10,
                14,
                COLOR_TEXT_GREEN
            )
            draw_text(
                f"Finished in {world.move_count} moves and {world.push_count} pushes.",
                x + 26,
                cursor_y + 34,
                13,
                COLOR_TEXT_WHITE
            )
            draw_text(
                "Press [N] or [1]-[4] to select the next puzzle challenge.",
                x + 26,
                cursor_y + 58,
                12,
                COLOR_TEXT_CYAN
            )
        else:
            draw_text(
                "STATUS: PUZZLE TOPOLOGY SOLVABLE (NO DEADLOCKS)",
                x + 26,
                cursor_y + 10,
                13,
                COLOR_TEXT_GREEN
            )
            draw_text(
                "Grid is free of Corner sinks, Dead Walls, and 2x2 Clumps.",
                x + 26,
                cursor_y + 34,
                12,
                COLOR_TEXT_MUTED
            )
            draw_text(
                f"Remaining goals: {total_goals - goals_solved}   |   Uncovered crates: {total_goals - goals_solved}",
                x + 26,
                cursor_y + 54,
                12,
                COLOR_TEXT_WHITE
            )
            draw_text(
                "Tip: Push boxes into open interior spaces, never into corners.",
                x + 26,
                cursor_y + 76,
                11,
                COLOR_TEXT_MUTED
            )

    cursor_y += card_h + 16

    # --------------------------------------------------------------------------
    # 3. Command History Timeline & Reversible Stack Scrubber
    # --------------------------------------------------------------------------
    undo_len = len(world.history.undo_stack)
    redo_len = len(world.history.redo_stack)

    draw_text(
        f"COMMAND PATTERN TIMELINE (Undo: {undo_len} | Redo: {redo_len})",
        x + 16,
        cursor_y,
        14,
        COLOR_TEXT_CYAN
    )
    cursor_y += 20

    # Scrubber Box
    scrub_h = 138
    draw_rectangle(x + 16, cursor_y, bar_width, scrub_h, Color(22, 26, 38, 255))
    draw_rectangle_lines(x + 16, cursor_y, bar_width, scrub_h, COLOR_PANEL_BORDER)

    recent_cmds = world.history.get_recent_history(5)
    item_y = cursor_y + 8

    if len(recent_cmds) == 0:
        draw_text(
            "[Stack Empty: No moves executed yet]",
            x + 26,
            item_y + 8,
            12,
            COLOR_TEXT_MUTED
        )
        item_y += 24
    else:
        for idx, cmd in enumerate(recent_cmds):
            cmd_index = undo_len - len(recent_cmds) + idx + 1
            desc = cmd.get_description()

            # Highlight the most recent command
            is_latest = (idx == len(recent_cmds) - 1)
            row_col = COLOR_TEXT_MUTED
            if is_latest:
                row_col = COLOR_TEXT_WHITE
                draw_rectangle(x + 20, item_y - 2, bar_width - 8, 20, Color(45, 60, 90, 160))
                draw_text(f"#{cmd_index:03d} -> {desc} [CURRENT]", x + 24, item_y + 2, 12, COLOR_TEXT_CYAN)
            else:
                draw_text(f"#{cmd_index:03d} -> {desc}", x + 24, item_y + 2, 12, row_col)
            item_y += 22

    # Undo/Redo action hints
    hint_y = cursor_y + scrub_h - 22
    draw_text(
        "[Z] / Gamepad LB: Undo Step   |   [Y] / Gamepad RB: Redo Step",
        x + 24,
        hint_y,
        11,
        COLOR_TEXT_GOLD
    )

    cursor_y += scrub_h + 16

    # --------------------------------------------------------------------------
    # 4. Pedagogical Theory & Mathematical Proofs Card
    # --------------------------------------------------------------------------
    theory_h = 140
    draw_rectangle(x + 16, cursor_y, bar_width, theory_h, Color(18, 22, 32, 255))
    draw_rectangle_lines(x + 16, cursor_y, bar_width, theory_h, COLOR_PANEL_BORDER)

    draw_text("MATHEMATICAL DEADLOCK THEOREMS & C++ ARCHITECTURE", x + 26, cursor_y + 10, 12, COLOR_TEXT_GOLD)
    draw_text("1. Corner Sink: Non-goal tile with 2 orthogonal walls -> Permanently stuck.", x + 26, cursor_y + 30, 11, COLOR_TEXT_WHITE)
    draw_text("2. Dead Wall: Closed wall segment with zero goals -> Box cannot escape.", x + 26, cursor_y + 48, 11, COLOR_TEXT_WHITE)
    draw_text("3. 2x2 Freeze: 2x2 square of solid blocks with >=1 non-goal box -> Locked.", x + 26, cursor_y + 66, 11, COLOR_TEXT_WHITE)
    draw_text("4. C++ Transfer: std::vector<MoveCommand> undo_stack; O(1) push/pop rollback.", x + 26, cursor_y + 84, 11, COLOR_TEXT_CYAN)
    draw_text("[Tab] Toggle X-Ray Danger Map   |   [F1] Toggle Deadlock Assist", x + 26, cursor_y + 112, 11, COLOR_TEXT_MUTED)


# ==============================================================================
# BLOCK 4: MAIN GAME LOOP & AUTOMATED SMOKE TEST
# ==============================================================================
class PatternLabGame:
    """
    Main Sokoban Deadlock Solver Game Application.
    Provides simultaneous Dual Input (KB/M + Gamepad), sound synthesis,
    dynamic grid rendering, and automated smoke testing.
    """
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()

        self.sfx = SoundLibrary()
        self.sfx.init_defaults()

        self.world = SokobanWorld()
        self.show_xray = True
        self.pattern_enabled = True

        # Input timing for discrete repeat
        self.move_repeat_timer = 0.0
        self.initial_repeat_delay = 0.22
        self.continuous_repeat_rate = 0.12
        self.last_input_dx = 0
        self.last_input_dy = 0

        # Undo repeat timer
        self.undo_repeat_timer = 0.0

        # Play victory sound guard
        self.victory_sound_played = False

    def handle_inputs(self, dt: float):
        """Processes dual input for movement, undo/redo, levels, and toggles."""
        # ----------------------------------------------------------------------
        # 1. Toggles: Pattern ([F1]) & X-Ray ([Tab]) & Reset ([R])
        # ----------------------------------------------------------------------
        if is_dual_pattern_toggle_pressed():
            self.pattern_enabled = not self.pattern_enabled
            self.sfx.play("click", 0.7)

        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
            self.sfx.play("click", 0.7)

        if is_dual_reset_pressed():
            self.world.reset_level()
            self.victory_sound_played = False
            self.sfx.play("click", 0.8)

        # ----------------------------------------------------------------------
        # 2. Level Selection ([1]..[4] and N/P)
        # ----------------------------------------------------------------------
        if is_key_pressed(KEY_ONE):
            self.world.load_level(0)
            self.victory_sound_played = False
            self.sfx.play("click", 0.7)
        elif is_key_pressed(KEY_TWO):
            self.world.load_level(1)
            self.victory_sound_played = False
            self.sfx.play("click", 0.7)
        elif is_key_pressed(KEY_THREE):
            self.world.load_level(2)
            self.victory_sound_played = False
            self.sfx.play("click", 0.7)
        elif is_key_pressed(KEY_FOUR):
            self.world.load_level(3)
            self.victory_sound_played = False
            self.sfx.play("click", 0.7)
        elif is_key_pressed(KEY_N):
            next_lvl = (self.world.active_level_idx + 1) % len(self.world.raw_levels)
            self.world.load_level(next_lvl)
            self.victory_sound_played = False
            self.sfx.play("click", 0.7)
        elif is_key_pressed(KEY_P):
            prev_lvl = (self.world.active_level_idx - 1 + len(self.world.raw_levels)) % len(self.world.raw_levels)
            self.world.load_level(prev_lvl)
            self.victory_sound_played = False
            self.sfx.play("click", 0.7)

        # ----------------------------------------------------------------------
        # 3. Undo / Redo Dual Input
        # ----------------------------------------------------------------------
        pad_id = get_active_gamepad_id()
        undo_pressed = (
            is_key_pressed(KEY_Z) or
            is_key_pressed(KEY_U) or
            (pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_LEFT_TRIGGER_1)) or
            (pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_FACE_RIGHT))
        )
        undo_held = (
            is_key_down(KEY_Z) or
            is_key_down(KEY_U) or
            (pad_id >= 0 and is_gamepad_button_down(pad_id, GAMEPAD_BUTTON_LEFT_TRIGGER_1))
        )

        redo_pressed = (
            is_key_pressed(KEY_Y) or
            (pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_TRIGGER_1)) or
            (pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_FACE_LEFT))
        )

        if undo_pressed:
            if self.world.undo_step():
                self.sfx.play("cancel", 0.6)
            self.undo_repeat_timer = 0.28
        elif undo_held:
            self.undo_repeat_timer -= dt
            if self.undo_repeat_timer <= 0.0:
                if self.world.undo_step():
                    self.sfx.play("cancel", 0.5)
                self.undo_repeat_timer = 0.10

        if redo_pressed:
            if self.world.redo_step():
                self.sfx.play("confirm", 0.6)

        # ----------------------------------------------------------------------
        # 4. Warehouse Keeper Movement (Dual Move with Repeat Delay)
        # ----------------------------------------------------------------------
        raw_move = get_dual_move_2d(deadzone=0.25)
        input_dx = 0
        input_dy = 0

        # Discretize continuous vector into primary cardinal axis
        if abs(raw_move.x) > abs(raw_move.y):
            if raw_move.x > 0.35:
                input_dx = 1
            elif raw_move.x < -0.35:
                input_dx = -1
        else:
            if raw_move.y > 0.35:
                input_dy = 1
            elif raw_move.y < -0.35:
                input_dy = -1

        # Check for discrete direction transitions
        if input_dx != 0 or input_dy != 0:
            if input_dx != self.last_input_dx or input_dy != self.last_input_dy:
                # Fresh press in new direction
                moved = self.world.try_move(input_dx, input_dy)
                if moved:
                    self.play_move_sfx()
                self.last_input_dx = input_dx
                self.last_input_dy = input_dy
                self.move_repeat_timer = self.initial_repeat_delay
            else:
                # Sustained hold in same direction
                self.move_repeat_timer -= dt
                if self.move_repeat_timer <= 0.0:
                    moved = self.world.try_move(input_dx, input_dy)
                    if moved:
                        self.play_move_sfx()
                    self.move_repeat_timer = self.continuous_repeat_rate
        else:
            self.last_input_dx = 0
            self.last_input_dy = 0
            self.move_repeat_timer = 0.0

    def play_move_sfx(self):
        """Plays appropriate feedback audio on move, push, or deadlock alert."""
        if len(self.world.detector.deadlocked_box_ids) > 0 and self.pattern_enabled:
            self.sfx.play("error", 0.8)
        else:
            # Check if any box was pushed onto a goal
            any_on_goal = False
            for b in self.world.boxes:
                if b.on_goal:
                    any_on_goal = True
                    break
            if any_on_goal:
                self.sfx.play("pickup", 0.7)
            else:
                self.sfx.play("footstep", 0.5)

    def update(self):
        dt = min(get_frame_time(), 0.05)
        self.handle_inputs(dt)
        self.world.update(dt)

        if self.world.is_puzzle_won and not self.victory_sound_played:
            self.sfx.play("level_up", 0.9)
            self.victory_sound_played = True

    def draw(self):
        begin_drawing()
        clear_background(COLOR_BG_DARK)

        # ----------------------------------------------------------------------
        # Top Header Bar (Keeping x = 450..980, y = 14..48 clear for UI bar)
        # ----------------------------------------------------------------------
        draw_text("SOKOBAN DEADLOCK SOLVER", 24, 18, 18, COLOR_TEXT_CYAN)
        draw_text("Command Pattern (Undo/Redo) & Heuristic Deadlocks", 24, 40, 12, COLOR_TEXT_MUTED)

        # ----------------------------------------------------------------------
        # Warehouse Grid View (Centered on left half of screen)
        # ----------------------------------------------------------------------
        grid_w_px = self.world.width * TILE_SIZE
        grid_h_px = self.world.height * TILE_SIZE
        origin_x = GRID_AREA_LEFT + (GRID_AREA_WIDTH - grid_w_px) // 2
        origin_y = GRID_AREA_TOP + (GRID_AREA_HEIGHT - grid_h_px) // 2

        # Draw Grid Backdrop
        draw_rectangle(
            origin_x - 12,
            origin_y - 12,
            grid_w_px + 24,
            grid_h_px + 24,
            Color(18, 22, 32, 255)
        )
        draw_rectangle_lines(
            origin_x - 12,
            origin_y - 12,
            grid_w_px + 24,
            grid_h_px + 24,
            COLOR_PANEL_BORDER
        )

        # Layer 1: Floor and Wall Tiles
        for y in range(self.world.height):
            for x in range(self.world.width):
                px = origin_x + x * TILE_SIZE
                py = origin_y + y * TILE_SIZE
                if self.world.is_wall_grid[y][x]:
                    draw_warehouse_tile_wall(px, py, TILE_SIZE)
                else:
                    draw_warehouse_tile_floor(px, py, TILE_SIZE)

        # Layer 2: Goal Markers
        for g in self.world.goals:
            px = origin_x + g.x * TILE_SIZE
            py = origin_y + g.y * TILE_SIZE
            draw_warehouse_goal(px, py, TILE_SIZE, g.covered)

        # Layer 3: Static Deadlock Danger Overlay ([Tab] X-Ray Mode)
        if self.show_xray and self.pattern_enabled:
            for y in range(self.world.height):
                for x in range(self.world.width):
                    if not self.world.is_wall_grid[y][x] and not self.world.is_goal_grid[y][x]:
                        d_code = self.world.detector.static_map[y][x]
                        if d_code != DEADLOCK_NONE:
                            px = origin_x + x * TILE_SIZE
                            py = origin_y + y * TILE_SIZE
                            draw_static_deadlock_overlay(px, py, TILE_SIZE, d_code)

        # Layer 4: Boxes / Crates (Rendered at smooth visual coordinates)
        for b in self.world.boxes:
            px = origin_x + int(b.visual_x * TILE_SIZE)
            py = origin_y + int(b.visual_y * TILE_SIZE)
            draw_crate(b, px, py, TILE_SIZE, self.pattern_enabled)

        # Layer 5: Warehouse Keeper Avatar (Smooth visual coordinates)
        pl_x = origin_x + int(self.world.player.visual_x * TILE_SIZE)
        pl_y = origin_y + int(self.world.player.visual_y * TILE_SIZE)
        draw_warehouse_player(self.world.player, pl_x, pl_y, TILE_SIZE)

        # ----------------------------------------------------------------------
        # Right Side Telemetry & Command History Panel
        # ----------------------------------------------------------------------
        panel_x = 740
        panel_y = GRID_AREA_TOP
        panel_w = 510
        panel_h = GRID_AREA_HEIGHT
        draw_telemetry_panel(
            self.world,
            panel_x,
            panel_y,
            panel_w,
            panel_h,
            self.pattern_enabled,
            self.show_xray
        )

        # ----------------------------------------------------------------------
        # Mandatory Global Badges & Top Dropdown Bar
        # ----------------------------------------------------------------------
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)

        end_drawing()

    def run(self, smoke_test: bool = False):
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
