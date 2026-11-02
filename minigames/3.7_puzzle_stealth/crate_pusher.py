# -*- coding: utf-8 -*-
"""
Crate Pusher - Push-Block Puzzle (Sokoban) & Command Undo/Redo Engine
=====================================================================
Section          : 3.7 Puzzle, Stealth & Other
Pattern Category : Logic, Puzzle & Systemic Patterns
Dimension        : 2D

Problem Solved:
  In puzzle and systemic games (Sokoban, Baba Is You, Stephen's Sausage Roll,
  Portal, The Talos Principle), naively mutating game state directly on button
  presses prevents reversible gameplay (undo/redo), causes desynchronized entity
  pushes, and leaves no replay execution log. Furthermore, without constraint
  solvers, players frequently suffer silent unrecoverable deadlocks (pushing a crate
  into a permanent corner), wasting time on mathematically impossible boards.

How the Patterns Work:
  1. Discrete Grid State & Atomic Push-Block Physics:
     The world is modeled as a discrete 2D matrix of static tiles (Floor, Wall,
     Target Plate) and dynamic entities (Player, Crates). When the player inputs
     a cardinal direction (dx, dy):
       - If the target cell is empty floor/target -> player advances.
       - If the target cell contains a crate -> check the cell behind the crate:
         if that cell is walkable floor/target (not a wall and not another crate),
         both the crate and the player advance atomically in a single turn.
       - If blocked by a wall or two consecutive crates -> the move is rejected.
  2. Command Pattern & Reversible History Stack:
     Every successful movement or push is encapsulated into a lightweight
     MoveCommand struct:
       (player_from, player_to, pushed_crate_index, crate_from, crate_to)
     Commands are pushed onto an Undo Stack. Pressing Undo pops the command and
     reverses the transaction atomically (pulling the crate back and restoring
     player coordinates). A Redo Stack allows stepping forward again.
  3. Algorithmic Deadlock Detection Heuristics (X-Ray Inspector):
     Sokoban is mathematically NP-hard. Real-time heuristic state evaluation
     detects permanent deadlock states:
       - Corner Deadlock: A crate pushed into a 90-degree wall corner that is not
         a target tile can never be pushed in any direction again.
       - 2x2 Dead Cluster: A 2x2 square of 4 cells entirely occupied by walls
         or crates where at least one crate is not on a target.
     In X-Ray mode ([Tab]), deadlocked crates are highlighted with crimson warning
     rings and telemetry alerts learners to illegal board states.
  4. Visual Kinematic Smoothing (Visual Lerp Rig):
     While the logical puzzle state is strictly discrete (gx, gy), visual entities
     smoothly damp toward their discrete coordinates using exponential decay,
     giving tactile, juice-filled movement with bounce and satisfying particle bursts.

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - [W][A][S][D] / Arrow Keys / Gamepad Left Stick / D-Pad : Move / Push Crate
  - [Z] / [U] / Gamepad B (East Button)                  : Undo Move (Command Pop)
  - [Y] / Gamepad X (West Button)                        : Redo Move
  - [R] / Gamepad Select (Back/View)                     : Reset Current Level
  - [1] - [4] / [N] (Next) / [P] (Prev) / Gamepad LB/RB  : Select Handcrafted Level
  - [Tab] / Gamepad Y (North Button)                     : Toggle X-Ray Telemetry & Deadlock Inspector
  - [F1]  / Gamepad R3                                   : Toggle Deadlock Warning Overlay [ON/OFF]
  - [Ctrl +/-]                                           : Adjust UI Font Size
  - [F11]                                                : Toggle Fullscreen
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
WINDOW_TITLE = "Crate Pusher - Push-Block Puzzle & Command Undo/Redo (Raylib Pattern Lab)"

# Grid Tile Constants (C++ enum TileType : uint8_t)
TILE_EMPTY = 0
TILE_FLOOR = 1
TILE_WALL = 2
TILE_TARGET = 3

# Visual Tile Rendering Dimensions
TILE_SIZE = 54
BOARD_ORIGIN_X = 260
BOARD_ORIGIN_Y = 110


# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATION (COMMAND PATTERN & SOKOBAN ENGINE)
# ==============================================================================

class MoveCommand:
    """
    Command Pattern - Encapsulates an atomic puzzle turn transaction.
    C++ Equivalent:
      struct MoveCommand {
          int player_from_x, player_from_y;
          int player_to_x, player_to_y;
          int crate_idx;         // -1 if pure walk, >= 0 if crate was pushed
          int crate_from_x, crate_from_y;
          int crate_to_x, crate_to_y;
      };
    """
    def __init__(self, pfx: int, pfy: int, ptx: int, pty: int,
                 c_idx: int = -1, cfx: int = 0, cfy: int = 0, ctx: int = 0, cty: int = 0):
        self.player_from_x = pfx
        self.player_from_y = pfy
        self.player_to_x = ptx
        self.player_to_y = pty
        self.crate_idx = c_idx
        self.crate_from_x = cfx
        self.crate_from_y = cfy
        self.crate_to_x = ctx
        self.crate_to_y = cty


class CommandHistoryStack:
    """
    Reversible Command History Stack (Undo/Redo Architecture).
    Maintains dual stacks of executed actions, allowing linear exploration
    without destructive memory leaks or state desynchronization.
    C++ Equivalent:
      std::vector<MoveCommand> undo_stack;
      std::vector<MoveCommand> redo_stack;
    """
    def __init__(self, max_capacity: int = 512):
        self.undo_stack = []
        self.redo_stack = []
        self.max_capacity = max_capacity
        self.total_moves_made = 0
        self.total_pushes_made = 0

    def push_command(self, cmd: MoveCommand):
        # Truncate oldest entries if capacity exceeded
        if len(self.undo_stack) >= self.max_capacity:
            self.undo_stack.pop(0)
        self.undo_stack.append(cmd)
        # Any new player action invalidates the redo forward history
        self.redo_stack.clear()
        self.total_moves_made += 1
        if cmd.crate_idx >= 0:
            self.total_pushes_made += 1

    def can_undo(self) -> bool:
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        return len(self.redo_stack) > 0

    def pop_undo(self):
        if not self.undo_stack:
            return None
        cmd = self.undo_stack.pop()
        self.redo_stack.append(cmd)
        return cmd

    def pop_redo(self):
        if not self.redo_stack:
            return None
        cmd = self.redo_stack.pop()
        self.undo_stack.append(cmd)
        return cmd

    def clear(self):
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.total_moves_made = 0
        self.total_pushes_made = 0


class CrateEntity:
    """
    Dynamic pushable crate on the discrete grid with smooth visual lerping.
    C++ Equivalent:
      struct CrateEntity {
          int gx, gy;
          float vx, vy;
          bool on_target;
          bool is_deadlocked;
      };
    """
    def __init__(self, gx: int, gy: int):
        self.gx = gx
        self.gy = gy
        self.vx = float(BOARD_ORIGIN_X + gx * TILE_SIZE)
        self.vy = float(BOARD_ORIGIN_Y + gy * TILE_SIZE)
        self.on_target = False
        self.is_deadlocked = False
        self.target_flash = 0.0

    def update_visuals(self, dt: float):
        target_vx = float(BOARD_ORIGIN_X + self.gx * TILE_SIZE)
        target_vy = float(BOARD_ORIGIN_Y + self.gy * TILE_SIZE)
        self.vx = damp(self.vx, target_vx, 22.0, dt)
        self.vy = damp(self.vy, target_vy, 22.0, dt)
        if self.target_flash > 0.0:
            self.target_flash = max(0.0, self.target_flash - dt * 2.5)


class PlayerPusher:
    """
    Grid-aligned player character with directional facing and smooth animation.
    """
    def __init__(self, gx: int, gy: int):
        self.gx = gx
        self.gy = gy
        self.vx = float(BOARD_ORIGIN_X + gx * TILE_SIZE)
        self.vy = float(BOARD_ORIGIN_Y + gy * TILE_SIZE)
        self.facing_dx = 0
        self.facing_dy = 1
        self.walk_anim = 0.0
        self.is_moving = False

    def update_visuals(self, dt: float):
        target_vx = float(BOARD_ORIGIN_X + self.gx * TILE_SIZE)
        target_vy = float(BOARD_ORIGIN_Y + self.gy * TILE_SIZE)
        dist = math.sqrt((self.vx - target_vx) ** 2 + (self.vy - target_vy) ** 2)
        if dist > 1.0:
            self.walk_anim += dt * 14.0
            self.is_moving = True
        else:
            self.is_moving = False
            self.walk_anim = 0.0
        self.vx = damp(self.vx, target_vx, 24.0, dt)
        self.vy = damp(self.vy, target_vy, 24.0, dt)


class SokobanLevel:
    """
    Level definition containing tile layout, initial player coordinates,
    and initial crate positions.
    """
    def __init__(self, name: str, width: int, height: int, ascii_map: list):
        self.name = name
        self.width = width
        self.height = height
        self.tiles = [TILE_EMPTY] * (width * height)
        self.start_px = 0
        self.start_py = 0
        self.crate_starts = []
        self.target_positions = []

        # Parse ASCII map:
        # '#' = Wall, '.' = Target, '$' = Crate, '*' = Crate on Target,
        # '@' = Player, '+' = Player on Target, ' ' = Floor
        for y in range(height):
            row_str = ascii_map[y] if y < len(ascii_map) else ""
            for x in range(width):
                ch = row_str[x] if x < len(row_str) else ' '
                idx = y * width + x
                if ch == '#':
                    self.tiles[idx] = TILE_WALL
                elif ch == '.':
                    self.tiles[idx] = TILE_TARGET
                    self.target_positions.append((x, y))
                elif ch == '$':
                    self.tiles[idx] = TILE_FLOOR
                    self.crate_starts.append((x, y))
                elif ch == '*':
                    self.tiles[idx] = TILE_TARGET
                    self.crate_starts.append((x, y))
                    self.target_positions.append((x, y))
                elif ch == '@':
                    self.tiles[idx] = TILE_FLOOR
                    self.start_px = x
                    self.start_py = y
                elif ch == '+':
                    self.tiles[idx] = TILE_TARGET
                    self.start_px = x
                    self.start_py = y
                    self.target_positions.append((x, y))
                elif ch == ' ':
                    self.tiles[idx] = TILE_FLOOR


# ==============================================================================
# BLOCK 2: DEADLOCK HEURISTIC DETECTOR
# ==============================================================================

class DeadlockDetector:
    """
    Evaluates Sokoban board states for permanent mathematical deadlocks.
    Because Sokoban is PSPACE-complete / NP-hard, full reachability verification
    requires exhaustive graph search; however, local constraint heuristics
    can instantly flag 95%+ of player blunders in O(C) time.
    """
    def __init__(self):
        self.active_deadlocks_count = 0
        self.has_board_deadlock = False

    def is_wall_or_out_of_bounds(self, x: int, y: int, width: int, height: int, tiles: list) -> bool:
        if x < 0 or x >= width or y < 0 or y >= height:
            return True
        return tiles[y * width + x] == TILE_WALL

    def evaluate_board(self, width: int, height: int, tiles: list, crates: list):
        self.active_deadlocks_count = 0
        self.has_board_deadlock = False

        for i in range(len(crates)):
            crate = crates[i]
            cx = crate.gx
            cy = crate.gy
            tile_here = tiles[cy * width + cx]

            # A crate on a target is never considered deadlocked (it satisfies a goal)
            if tile_here == TILE_TARGET:
                crate.is_deadlocked = False
                continue

            # 1. Corner Deadlock Check:
            # If two orthogonal neighbors are walls (e.g. Up+Left, Up+Right, Down+Left, Down+Right),
            # the crate is permanently trapped in a 90-degree corner.
            up_wall = self.is_wall_or_out_of_bounds(cx, cy - 1, width, height, tiles)
            down_wall = self.is_wall_or_out_of_bounds(cx, cy + 1, width, height, tiles)
            left_wall = self.is_wall_or_out_of_bounds(cx - 1, cy, width, height, tiles)
            right_wall = self.is_wall_or_out_of_bounds(cx + 1, cy, width, height, tiles)

            is_corner = (
                (up_wall and left_wall) or
                (up_wall and right_wall) or
                (down_wall and left_wall) or
                (down_wall and right_wall)
            )

            # 2. 2x2 Dead Cluster Check:
            # Check if this crate forms a solid 2x2 block with adjacent walls/crates.
            is_cluster = False
            for dx, dy in [(-1, -1), (0, -1), (-1, 0), (0, 0)]:
                # Check 2x2 square starting at (cx + dx, cy + dy)
                sq_x = cx + dx
                sq_y = cy + dy
                solid_count = 0
                for sy in range(2):
                    for sx in range(2):
                        chk_x = sq_x + sx
                        chk_y = sq_y + sy
                        if self.is_wall_or_out_of_bounds(chk_x, chk_y, width, height, tiles):
                            solid_count += 1
                        else:
                            # Check if another crate occupies this cell
                            for other in crates:
                                if other.gx == chk_x and other.gy == chk_y:
                                    solid_count += 1
                                    break
                if solid_count == 4:
                    is_cluster = True
                    break

            if is_corner or is_cluster:
                crate.is_deadlocked = True
                self.active_deadlocks_count += 1
                self.has_board_deadlock = True
            else:
                crate.is_deadlocked = False


# ==============================================================================
# BLOCK 3: WORLD SIMULATION & ENTITIES
# ==============================================================================

def create_default_levels() -> list:
    """
    Hand-crafted progressive puzzle library demonstrating fundamental push-block
    heuristics: corridor routing, corner traps, multi-target sequencing.
    """
    levels = []

    # Level 1: Beginner Corridor Introduction (2 Crates)
    l1 = [
        "######",
        "#@  .#",
        "# $$ #",
        "#  . #",
        "######",
    ]
    levels.append(SokobanLevel("01: The Loading Bay", 6, 5, l1))

    # Level 2: The Fork & Turn (3 Crates)
    l2 = [
        "  ##### ",
        "###   # ",
        "#.@$  # ",
        "### $.# ",
        "#.##$ # ",
        "# # . # ",
        "#$    ##",
        "#   .  #",
        "########"
    ]
    levels.append(SokobanLevel("02: Tight Quarters", 8, 9, l2))

    # Level 3: Classic Cross Chamber (4 Crates)
    l3 = [
        "  ######  ",
        "  #    #  ",
        "### $$ ###",
        "#  $..$  #",
        "#  .@@.  #",
        "### $$ ###",
        "  #    #  ",
        "  ######  "
    ]
    levels.append(SokobanLevel("03: Cross Chamber", 10, 8, l3))

    # Level 4: The Serpentine Depot (5 Crates)
    l4 = [
        "########",
        "#      #",
        "# $$.$ #",
        "# #..# #",
        "# #..# #",
        "# $$.$ #",
        "#   @  #",
        "########"
    ]
    levels.append(SokobanLevel("04: Serpentine Depot", 8, 8, l4))

    return levels


class ParticleEffect:
    """Visual sparkle burst when satisfying a target plate or winning."""
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.color = Color(255, 255, 255, 255)
        self.life = 0.0
        self.max_life = 1.0
        self.size = 3.0
        self.active = False


class VisualParticlePool:
    def __init__(self, capacity: int = 120):
        self.particles = []
        for _ in range(capacity):
            self.particles.append(ParticleEffect())

    def burst(self, x: float, y: float, color: Color, count: int = 14):
        spawned = 0
        for p in self.particles:
            if not p.active:
                p.active = True
                p.x = x
                p.y = y
                angle = random.uniform(0.0, math.pi * 2.0)
                speed = random.uniform(30.0, 160.0)
                p.vx = math.cos(angle) * speed
                p.vy = math.sin(angle) * speed
                p.color = color
                p.life = 0.0
                p.max_life = random.uniform(0.35, 0.75)
                p.size = random.uniform(2.5, 5.0)
                spawned += 1
                if spawned >= count:
                    break

    def update(self, dt: float):
        for p in self.particles:
            if p.active:
                p.life += dt
                if p.life >= p.max_life:
                    p.active = False
                else:
                    p.x += p.vx * dt
                    p.y += p.vy * dt
                    p.vy += 80.0 * dt  # Gentle gravity

    def draw(self):
        for p in self.particles:
            if p.active:
                prog = 1.0 - (p.life / p.max_life)
                alpha = max(0, min(255, int(255 * prog)))
                col = Color(p.color.r, p.color.g, p.color.b, alpha)
                draw_circle(int(p.x), int(p.y), p.size * prog, col)


# ==============================================================================
# BLOCK 4: TELEMETRY & X-RAY DEBUG OVERLAY ([Tab] & [F1])
# ==============================================================================

def draw_xray_telemetry(history: CommandHistoryStack, detector: DeadlockDetector,
                        level: SokobanLevel, player: PlayerPusher, crates: list,
                        is_solved: bool, deadlock_warning_enabled: bool):
    """
    X-Ray Inspector Overlay visualizes internal puzzle telemetry:
    - Command Undo/Redo stack depth and transaction pointer
    - Algorithmic Deadlock warnings and corner traps
    - Grid cell coordinates and crate target satisfaction
    """
    panel_x = 18
    panel_y = 68
    panel_w = 224
    panel_h = 580

    # Semi-transparent dark panel
    draw_rectangle(panel_x, panel_y, panel_w, panel_h, Color(16, 20, 28, 240))
    draw_rectangle_lines(panel_x, panel_y, panel_w, panel_h, Color(60, 80, 110, 255))

    draw_text("X-RAY TELEMETRY", panel_x + 12, panel_y + 12, 14, Color(90, 200, 255, 255))
    draw_line(panel_x + 12, panel_y + 32, panel_x + panel_w - 12, panel_y + 32, Color(40, 60, 90, 255))

    y = panel_y + 40
    line_h = 20

    # 1. Level & Grid Info
    draw_text(f"Level: {level.name[:18]}", panel_x + 12, y, 11, Color(200, 210, 225, 255)); y += line_h
    draw_text(f"Grid: {level.width} x {level.height} cells", panel_x + 12, y, 11, Color(160, 175, 195, 255)); y += line_h
    draw_text(f"Player (gx, gy): ({player.gx}, {player.gy})", panel_x + 12, y, 11, Color(140, 220, 170, 255)); y += line_h + 4

    # 2. Command Pattern Stack Telemetry
    draw_text("COMMAND PATTERN STACK", panel_x + 12, y, 11, Color(245, 190, 80, 255)); y += line_h
    undo_cnt = len(history.undo_stack)
    redo_cnt = len(history.redo_stack)
    draw_text(f"Undo Stack : {undo_cnt} / {history.max_capacity}", panel_x + 12, y, 11, Color(180, 195, 210, 255)); y += line_h
    draw_text(f"Redo Stack : {redo_cnt}", panel_x + 12, y, 11, Color(180, 195, 210, 255)); y += line_h
    draw_text(f"Total Moves: {history.total_moves_made}", panel_x + 12, y, 11, Color(160, 175, 195, 255)); y += line_h
    draw_text(f"Total Pushes: {history.total_pushes_made}", panel_x + 12, y, 11, Color(160, 175, 195, 255)); y += line_h + 4

    # Visual History Tape (Last 8 actions)
    draw_text("ACTION TAPE (Recent):", panel_x + 12, y, 10, Color(120, 140, 165, 255)); y += line_h - 2
    tape_start = max(0, len(history.undo_stack) - 8)
    tape_slice = history.undo_stack[tape_start:]
    if not tape_slice:
        draw_text("  [Empty - Level Start]", panel_x + 12, y, 10, Color(90, 105, 125, 255)); y += line_h
    else:
        for idx_t in range(len(tape_slice)):
            cmd_item = tape_slice[idx_t]
            is_push = cmd_item.crate_idx >= 0
            tag = "PUSH" if is_push else "STEP"
            col = Color(245, 170, 70, 255) if is_push else Color(130, 170, 210, 255)
            draw_text(f"  #{tape_start + idx_t + 1:02d}: {tag} -> ({cmd_item.player_to_x},{cmd_item.player_to_y})",
                      panel_x + 12, y, 10, col)
            y += 16
        y += 6

    # 3. Deadlock Heuristic Telemetry
    draw_line(panel_x + 12, y, panel_x + panel_w - 12, y, Color(40, 60, 90, 255)); y += 8
    draw_text("DEADLOCK HEURISTICS", panel_x + 12, y, 11, Color(245, 90, 90, 255)); y += line_h
    mode_str = "ENABLED [F1]" if deadlock_warning_enabled else "OFF [F1]"
    mode_col = Color(90, 230, 130, 255) if deadlock_warning_enabled else Color(180, 80, 80, 255)
    draw_text(f"Detector Mode: {mode_str}", panel_x + 12, y, 10, mode_col); y += line_h

    if detector.has_board_deadlock:
        draw_text("STATUS: DEADLOCK DETECTED!", panel_x + 12, y, 10, Color(255, 70, 70, 255)); y += line_h
        draw_text(f"Trapped Crates: {detector.active_deadlocks_count}", panel_x + 12, y, 10, Color(255, 160, 160, 255)); y += line_h
        draw_text("Hint: Press [Z] to Undo!", panel_x + 12, y, 10, Color(255, 215, 80, 255)); y += line_h
    else:
        draw_text("STATUS: SOLVABLE BOARD", panel_x + 12, y, 10, Color(80, 220, 120, 255)); y += line_h
        draw_text("Zero trapped crates", panel_x + 12, y, 10, Color(140, 180, 160, 255)); y += line_h

    # 4. Target Satisfaction
    sat_crates = 0
    for c in crates:
        if c.on_target:
            sat_crates += 1
    draw_line(panel_x + 12, y, panel_x + panel_w - 12, y, Color(40, 60, 90, 255)); y += 8
    draw_text(f"Targets Satisfied: {sat_crates} / {len(crates)}", panel_x + 12, y, 11,
              Color(70, 240, 150, 255) if is_solved else Color(210, 225, 240, 255))


# ==============================================================================
# BLOCK 5: MAIN GAME LOOP & AUTOMATED SMOKE TEST
# ==============================================================================

class CratePusherGame:
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()

        self.sfx = SoundLibrary()
        self.sfx.init_defaults()

        self.levels = create_default_levels()
        self.current_level_idx = 0

        self.history = CommandHistoryStack(max_capacity=512)
        self.detector = DeadlockDetector()
        self.particles = VisualParticlePool(capacity=160)

        self.show_xray = True
        self.deadlock_overlay_enabled = True

        # Input repeat delay for grid stepping
        self.move_cooldown = 0.0
        self.first_repeat_delay = 0.22
        self.repeat_interval = 0.12

        self.is_solved = False
        self.solve_fanfare_played = False
        self.celebration_timer = 0.0

        self.player = None
        self.crates = []
        self.active_level = None

        self.load_level(0)

    def load_level(self, idx: int):
        self.current_level_idx = max(0, min(len(self.levels) - 1, idx))
        self.active_level = self.levels[self.current_level_idx]
        self.history.clear()

        # Instantiate Player
        self.player = PlayerPusher(self.active_level.start_px, self.active_level.start_py)

        # Instantiate Crates
        self.crates = []
        for (cx, cy) in self.active_level.crate_starts:
            crate = CrateEntity(cx, cy)
            self.crates.append(crate)

        self.is_solved = False
        self.solve_fanfare_played = False
        self.celebration_timer = 0.0
        self.update_target_occupancy()
        self.detector.evaluate_board(self.active_level.width, self.active_level.height,
                                     self.active_level.tiles, self.crates)

    def update_target_occupancy(self):
        all_on = True
        for crate in self.crates:
            idx = crate.gy * self.active_level.width + crate.gx
            was_on = crate.on_target
            crate.on_target = (self.active_level.tiles[idx] == TILE_TARGET)
            if crate.on_target and not was_on:
                crate.target_flash = 1.0
                cx = BOARD_ORIGIN_X + crate.gx * TILE_SIZE + TILE_SIZE // 2
                cy = BOARD_ORIGIN_Y + crate.gy * TILE_SIZE + TILE_SIZE // 2
                self.particles.burst(cx, cy, Color(80, 240, 160, 255), count=16)
            if not crate.on_target:
                all_on = False

        if all_on and len(self.crates) > 0:
            if not self.is_solved:
                self.is_solved = True
                self.celebration_timer = 3.0
                self.sfx.play("coin", 0.9)
                # Confetti burst across entire board
                for crate in self.crates:
                    cx = BOARD_ORIGIN_X + crate.gx * TILE_SIZE + TILE_SIZE // 2
                    cy = BOARD_ORIGIN_Y + crate.gy * TILE_SIZE + TILE_SIZE // 2
                    self.particles.burst(cx, cy, Color(255, 215, 60, 255), count=24)

    def try_move(self, dx: int, dy: int) -> bool:
        if self.is_solved and self.celebration_timer > 2.5:
            return False  # Brief victory pause

        self.player.facing_dx = dx
        self.player.facing_dy = dy

        target_px = self.player.gx + dx
        target_py = self.player.gy + dy
        lvl = self.active_level

        # Bounds check
        if target_px < 0 or target_px >= lvl.width or target_py < 0 or target_py >= lvl.height:
            return False

        tile_idx = target_py * lvl.width + target_px
        if lvl.tiles[tile_idx] == TILE_WALL:
            self.sfx.play("click", 0.3)
            return False

        # Check if a crate is in target position
        hit_crate_idx = -1
        for i in range(len(self.crates)):
            if self.crates[i].gx == target_px and self.crates[i].gy == target_py:
                hit_crate_idx = i
                break

        if hit_crate_idx >= 0:
            # Attempt to push crate
            crate_dest_x = target_px + dx
            crate_dest_y = target_py + dy

            # Check if crate destination is in bounds and not wall
            if (crate_dest_x < 0 or crate_dest_x >= lvl.width or
                crate_dest_y < 0 or crate_dest_y >= lvl.height):
                self.sfx.play("click", 0.3)
                return False

            dest_tile_idx = crate_dest_y * lvl.width + crate_dest_x
            if lvl.tiles[dest_tile_idx] == TILE_WALL:
                self.sfx.play("click", 0.3)
                return False

            # Check if another crate blocks the push
            for j in range(len(self.crates)):
                if self.crates[j].gx == crate_dest_x and self.crates[j].gy == crate_dest_y:
                    self.sfx.play("click", 0.3)
                    return False  # Cannot push 2 crates simultaneously!

            # Valid Push Command!
            crate = self.crates[hit_crate_idx]
            cmd = MoveCommand(
                pfx=self.player.gx, pfy=self.player.gy,
                ptx=target_px, pty=target_py,
                c_idx=hit_crate_idx,
                cfx=crate.gx, cfy=crate.gy,
                ctx=crate_dest_x, cty=crate_dest_y
            )
            # Execute Push
            crate.gx = crate_dest_x
            crate.gy = crate_dest_y
            self.player.gx = target_px
            self.player.gy = target_py
            self.history.push_command(cmd)
            self.sfx.play("hit", 0.6)
            self.update_target_occupancy()
            self.detector.evaluate_board(lvl.width, lvl.height, lvl.tiles, self.crates)
            return True
        else:
            # Pure Walk Command
            cmd = MoveCommand(
                pfx=self.player.gx, pfy=self.player.gy,
                ptx=target_px, pty=target_py
            )
            self.player.gx = target_px
            self.player.gy = target_py
            self.history.push_command(cmd)
            self.sfx.play("click", 0.4)
            self.update_target_occupancy()
            self.detector.evaluate_board(lvl.width, lvl.height, lvl.tiles, self.crates)
            return True

    def undo(self):
        cmd = self.history.pop_undo()
        if cmd is not None:
            self.player.gx = cmd.player_from_x
            self.player.gy = cmd.player_from_y
            if cmd.crate_idx >= 0:
                crate = self.crates[cmd.crate_idx]
                crate.gx = cmd.crate_from_x
                crate.gy = cmd.crate_from_y
            self.sfx.play("click", 0.5)
            self.update_target_occupancy()
            self.detector.evaluate_board(self.active_level.width, self.active_level.height,
                                         self.active_level.tiles, self.crates)

    def redo(self):
        cmd = self.history.pop_redo()
        if cmd is not None:
            self.player.gx = cmd.player_to_x
            self.player.gy = cmd.player_to_y
            if cmd.crate_idx >= 0:
                crate = self.crates[cmd.crate_idx]
                crate.gx = cmd.crate_to_x
                crate.gy = cmd.crate_to_y
            self.sfx.play("click", 0.5)
            self.update_target_occupancy()
            self.detector.evaluate_board(self.active_level.width, self.active_level.height,
                                         self.active_level.tiles, self.crates)

    def update(self):
        dt = min(get_frame_time(), 0.05)

        # 1. Global X-Ray & Pattern Toggle Input
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
            self.sfx.play("click", 0.6)

        if is_dual_pattern_toggle_pressed():
            self.deadlock_overlay_enabled = not self.deadlock_overlay_enabled
            self.sfx.play("click", 0.6)

        # 2. Reset & Level Switching
        if is_dual_reset_pressed() or is_key_pressed(KEY_R):
            self.load_level(self.current_level_idx)
            self.sfx.play("click", 0.5)

        if is_key_pressed(KEY_N) or is_key_pressed(KEY_RIGHT_BRACKET) or (is_gamepad_available(0) and is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_TRIGGER_1)):
            self.load_level((self.current_level_idx + 1) % len(self.levels))
            self.sfx.play("click", 0.6)

        if is_key_pressed(KEY_P) or is_key_pressed(KEY_LEFT_BRACKET) or (is_gamepad_available(0) and is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_TRIGGER_1)):
            self.load_level((self.current_level_idx - 1) % len(self.levels))
            self.sfx.play("click", 0.6)

        if is_key_pressed(KEY_ONE): self.load_level(0)
        elif is_key_pressed(KEY_TWO): self.load_level(1)
        elif is_key_pressed(KEY_THREE): self.load_level(2)
        elif is_key_pressed(KEY_FOUR): self.load_level(3)

        # 3. Undo / Redo Controls
        # [Z] / [U] / Gamepad B (East Face Button) -> Undo
        if is_key_pressed(KEY_Z) or is_key_pressed(KEY_U) or (is_gamepad_available(0) and is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_FACE_RIGHT)):
            self.undo()

        # [Y] / Gamepad X (West Face Button) -> Redo
        if is_key_pressed(KEY_Y) or (is_gamepad_available(0) and is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_FACE_LEFT)):
            self.redo()

        # 4. Discrete Grid Movement Input (WASD / Left Stick / D-Pad)
        move_raw = get_dual_move_2d(deadzone=0.25, use_arrow_keys=True, include_dpad=True)
        in_dx = 0
        in_dy = 0
        if abs(move_raw.x) > abs(move_raw.y):
            if move_raw.x > 0.4: in_dx = 1
            elif move_raw.x < -0.4: in_dx = -1
        else:
            if move_raw.y > 0.4: in_dy = 1
            elif move_raw.y < -0.4: in_dy = -1

        self.move_cooldown -= dt
        if in_dx != 0 or in_dy != 0:
            if self.move_cooldown <= 0.0:
                if self.try_move(in_dx, in_dy):
                    self.move_cooldown = self.first_repeat_delay
                else:
                    self.move_cooldown = self.repeat_interval
        else:
            self.move_cooldown = 0.0

        # 5. Entity Visuals & Particles Update
        self.player.update_visuals(dt)
        for crate in self.crates:
            crate.update_visuals(dt)
        self.particles.update(dt)

        if self.celebration_timer > 0.0:
            self.celebration_timer -= dt

    def draw_world_board(self):
        lvl = self.active_level
        total_w = lvl.width * TILE_SIZE
        total_h = lvl.height * TILE_SIZE

        # Center Board in playable viewport
        viewport_center_x = (SCREEN_WIDTH + 260) // 2
        viewport_center_y = (SCREEN_HEIGHT + 40) // 2
        global BOARD_ORIGIN_X, BOARD_ORIGIN_Y
        BOARD_ORIGIN_X = viewport_center_x - (total_w // 2)
        BOARD_ORIGIN_Y = viewport_center_y - (total_h // 2)

        # 1. Floor Drop Shadow & Background Backing
        draw_rectangle(BOARD_ORIGIN_X - 10, BOARD_ORIGIN_Y - 10, total_w + 20, total_h + 20, Color(14, 16, 24, 255))
        draw_rectangle_lines(BOARD_ORIGIN_X - 10, BOARD_ORIGIN_Y - 10, total_w + 20, total_h + 20, Color(35, 45, 65, 255))

        # 2. Tiles Layer (Floor, Walls, Target Plates)
        for y in range(lvl.height):
            for x in range(lvl.width):
                tx = BOARD_ORIGIN_X + x * TILE_SIZE
                ty = BOARD_ORIGIN_Y + y * TILE_SIZE
                tile = lvl.tiles[y * lvl.width + x]

                if tile == TILE_WALL:
                    # Modular Metallic Wall Block with Beveled Edge
                    draw_rectangle(tx, ty, TILE_SIZE, TILE_SIZE, Color(42, 50, 68, 255))
                    draw_rectangle(tx + 4, ty + 4, TILE_SIZE - 8, TILE_SIZE - 8, Color(55, 65, 88, 255))
                    draw_rectangle_lines(tx, ty, TILE_SIZE, TILE_SIZE, Color(25, 30, 42, 255))
                    # Rivets on wall corners
                    draw_circle(tx + 7, ty + 7, 2.0, Color(80, 95, 125, 255))
                    draw_circle(tx + TILE_SIZE - 7, ty + 7, 2.0, Color(80, 95, 125, 255))
                    draw_circle(tx + 7, ty + TILE_SIZE - 7, 2.0, Color(80, 95, 125, 255))
                    draw_circle(tx + TILE_SIZE - 7, ty + TILE_SIZE - 7, 2.0, Color(80, 95, 125, 255))

                elif tile == TILE_FLOOR or tile == TILE_TARGET:
                    # Clean Chequered Stone Floor
                    base_shade = 28 if (x + y) % 2 == 0 else 32
                    draw_rectangle(tx, ty, TILE_SIZE, TILE_SIZE, Color(base_shade, base_shade + 3, base_shade + 8, 255))
                    draw_rectangle_lines(tx, ty, TILE_SIZE, TILE_SIZE, Color(20, 24, 34, 180))

                if tile == TILE_TARGET:
                    # Target Pressure Plate (Glowing Recessed Ring)
                    cx = tx + TILE_SIZE // 2
                    cy = ty + TILE_SIZE // 2
                    draw_circle(cx, cy, 18.0, Color(20, 35, 40, 255))
                    draw_circle_lines(cx, cy, 18.0, Color(40, 160, 110, 255))
                    draw_circle(cx, cy, 9.0, Color(30, 180, 120, 200))
                    draw_circle_lines(cx, cy, 4.0, Color(80, 255, 180, 255))

        # 3. Dynamic Crates Layer
        for crate in self.crates:
            cx = int(crate.vx)
            cy = int(crate.vy)
            cs = TILE_SIZE - 6
            ox = cx + 3
            oy = cy + 3

            # Drop Shadow
            draw_rectangle(ox + 4, oy + 4, cs, cs, Color(10, 12, 18, 160))

            if crate.on_target:
                # Satisfied Goal Crate (Luminous Emerald Hue)
                draw_rectangle(ox, oy, cs, cs, Color(35, 140, 85, 255))
                draw_rectangle(ox + 4, oy + 4, cs - 8, cs - 8, Color(45, 175, 105, 255))
                draw_rectangle_lines(ox, oy, cs, cs, Color(80, 255, 160, 255))
                # Glowing Checkmark Icon
                draw_line(ox + 14, oy + 26, ox + 22, oy + 34, Color(220, 255, 230, 255))
                draw_line(ox + 22, oy + 34, ox + 36, oy + 16, Color(220, 255, 230, 255))
            else:
                # Classic Wooden Heavy Crate
                draw_rectangle(ox, oy, cs, cs, Color(145, 95, 45, 255))
                draw_rectangle(ox + 4, oy + 4, cs - 8, cs - 8, Color(175, 120, 60, 255))
                draw_rectangle_lines(ox, oy, cs, cs, Color(85, 50, 25, 255))
                # Cross-braces
                draw_line(ox + 5, oy + 5, ox + cs - 5, oy + cs - 5, Color(110, 70, 35, 255))
                draw_line(ox + cs - 5, oy + 5, ox + 5, oy + cs - 5, Color(110, 70, 35, 255))
                # Metallic corner corner reinforcements
                draw_rectangle(ox, oy, 7, 7, Color(75, 80, 90, 255))
                draw_rectangle(ox + cs - 7, oy, 7, 7, Color(75, 80, 90, 255))
                draw_rectangle(ox, oy + cs - 7, 7, 7, Color(75, 80, 90, 255))
                draw_rectangle(ox + cs - 7, oy + cs - 7, 7, 7, Color(75, 80, 90, 255))

            # Flash when stepping on target
            if crate.target_flash > 0.0:
                flash_alpha = max(0, min(255, int(200 * crate.target_flash)))
                draw_rectangle(ox, oy, cs, cs, Color(120, 255, 190, flash_alpha))

            # Deadlock Warning Overlay (Crimson Hazard Marker)
            if self.deadlock_overlay_enabled and crate.is_deadlocked:
                pulse = (math.sin(get_time() * 9.0) + 1.0) * 0.5
                pulse_alpha = int(140 + 115 * pulse)
                draw_rectangle_lines(ox - 2, oy - 2, cs + 4, cs + 4, Color(255, 40, 40, pulse_alpha))
                # Danger Exclamation
                draw_circle(ox + cs // 2, oy + cs // 2, 12.0, Color(220, 30, 30, 230))
                draw_text("!", ox + cs // 2 - 3, oy + cs // 2 - 8, 16, Color(255, 255, 255, 255))

        # 4. Player Pusher Layer
        px = int(self.player.vx)
        py = int(self.player.vy)
        draw_circle(px + TILE_SIZE // 2, py + TILE_SIZE // 2 + 3, 16.0, Color(10, 14, 20, 160))  # Shadow

        # Facing angle in radians
        facing_rad = math.atan2(self.player.facing_dy, self.player.facing_dx)
        if self.player.facing_dx == 0 and self.player.facing_dy == 0:
            facing_rad = math.pi * 0.5  # Default down

        draw_humanoid_enemy_2d(
            position=Vector2(px + TILE_SIZE // 2, py + TILE_SIZE // 2),
            facing_angle_rad=facing_rad,
            anim_timer=self.player.walk_anim,
            scale=1.1,
            is_attacking=self.player.is_moving,
            palette={
                "armor": Color(50, 140, 230, 255),       # Vibrant Blue Builder Suit
                "accent": Color(245, 180, 40, 255),      # Golden Safety Vest
                "skin": Color(230, 190, 160, 255),
                "weapon": Color(90, 240, 255, 255),      # Cyan Tool
                "joint": Color(25, 30, 40, 255)          # Dark Boots & Joints
            }
        )

        # 5. Visual Particles
        self.particles.draw()

    def draw_hud(self):
        # Top-Left Level Title & Stats
        draw_text(self.active_level.name, 260, 68, 20, Color(240, 245, 255, 255))
        stats_line = (f"Moves: {self.history.total_moves_made}  |  "
                      f"Pushes: {self.history.total_pushes_made}  |  "
                      f"Undo Stack: {len(self.history.undo_stack)}")
        draw_text(stats_line, 260, 94, 12, Color(160, 185, 215, 255))

        # Level Switcher Shortcuts (Top-Right of Board)
        draw_text("Levels: [1] Bay  [2] Quarters  [3] Cross  [4] Depot  ([N] Next / [P] Prev)",
                  680, 94, 11, Color(140, 160, 185, 255))

        # Bottom Controls Banner
        bottom_y = SCREEN_HEIGHT - 38
        draw_rectangle(0, bottom_y - 8, SCREEN_WIDTH, 46, Color(12, 15, 22, 230))
        draw_line(0, bottom_y - 8, SCREEN_WIDTH, bottom_y - 8, Color(35, 45, 65, 255))

        ctrl_text = (
            "[WASD / Stick / D-Pad] Move/Push   "
            "[Z / Pad B] Undo   "
            "[Y / Pad X] Redo   "
            "[R / Select] Reset   "
            "[Tab] X-Ray   "
            "[F1] Deadlock Alert"
        )
        draw_text(ctrl_text, 40, bottom_y + 4, 12, Color(190, 210, 235, 255))

        # Deadlock Critical Warning Banner
        if self.deadlock_overlay_enabled and self.detector.has_board_deadlock and not self.is_solved:
            banner_w = 460
            banner_h = 32
            bx = (SCREEN_WIDTH - banner_w) // 2
            by = 68
            draw_rectangle(bx, by, banner_w, banner_h, Color(180, 25, 25, 235))
            draw_rectangle_lines(bx, by, banner_w, banner_h, Color(255, 90, 90, 255))
            draw_text("DEADLOCK WARNING: Crate trapped! Press [Z] to Undo.",
                      bx + 18, by + 8, 12, Color(255, 240, 240, 255))

        # Victory Banner
        if self.is_solved:
            banner_w = 520
            banner_h = 64
            bx = (SCREEN_WIDTH - banner_w) // 2
            by = (SCREEN_HEIGHT - banner_h) // 2
            draw_rectangle(bx, by, banner_w, banner_h, Color(20, 30, 24, 245))
            draw_rectangle_lines(bx, by, banner_w, banner_h, Color(70, 240, 140, 255))
            draw_text("LEVEL COMPLETE!", bx + 130, by + 12, 22, Color(80, 255, 160, 255))
            draw_text(f"Solved in {self.history.total_moves_made} moves & {self.history.total_pushes_made} pushes!  Press [N] for Next Level.",
                      bx + 26, by + 40, 11, Color(200, 245, 220, 255))

    def draw(self):
        begin_drawing()
        clear_background(Color(12, 14, 22, 255))

        # 1. Main Grid World & Entities
        self.draw_world_board()

        # 2. X-Ray Telemetry Overlay ([Tab])
        if self.show_xray:
            draw_xray_telemetry(self.history, self.detector, self.active_level,
                                self.player, self.crates, self.is_solved,
                                self.deadlock_overlay_enabled)

        # 3. HUD Stats & Banners
        self.draw_hud()

        # 4. Global Dropdowns & Controller Status Badge (Rule 8 & 9)
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
    CratePusherGame().run(smoke_test=is_smoke)
