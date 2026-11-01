# -*- coding: utf-8 -*-
"""
Tetris Backpack - Shape-Packing Inventory & Polyomino Grid Storage
==================================================================
Section          : 3.1 Menus & UI
Pattern Category : Menus & User Interface, Spatial Inventory Management
Dimension        : 2D

Problem Solved:
  In survival, tactical, and RPG titles (such as Diablo, Resident Evil 4, Escape
  from Tarkov, and Backpack Hero), inventory items are not uniform 1x1 tokens;
  they inhabit multi-cell geometric shapes (polyominoes: 1x1, 1x2, 2x2, 2x3, L, T,
  and Z footprints). Naive implementations that treat multi-cell items as floating
  sprites or loose lists suffer from boundary clipping, ghost data corruption
  (where only the root cell is updated while orphan cells remain locked), overlap
  bugs upon 90-degree rotation, and convoluted item-swapping logic.
  The Shape-Packing Inventory pattern solves this through discrete 2D spatial
  matrix occupancy, canonical polyomino rotation transforms, atomic transactional
  placement validation, and decoupled hand-slot state machines.

How the Pattern Works:
  1. Polyomino Mask Representation & Discrete 90° Clockwise Rotation:
     Each item archetype defines a set of local cell offsets [(col, row)] relative
     to an anchor origin (0, 0). Discrete 90° clockwise rotation transforms coordinates:
       col' = -row
       row' = col
     Followed by translation normalization so the bounding box min(col', row') snaps to (0, 0):
       col_norm = col' - min(col')
       row_norm = row' - min(row')
     In C++, these 4 orientations are precomputed at startup into fixed-size arrays:
       struct CellOffset { int col; int row; };
       struct PolyominoVariant { CellOffset cells[MAX_CELLS]; int count; int width; int height; };
  2. Flat Spatial Grid Storage & Instance Mapping:
     The container grid is represented as a contiguous 1D array of integers:
       int grid[GRID_ROWS * GRID_COLS];  // stores instance_id or EMPTY (-1)
     Cell access uses flat indexing: index = row * GRID_COLS + col.
  3. Atomic Transaction & Single-Item Swap:
     Placement validation iterates over each transformed cell offset in O(K) time:
       - Bounds Check: 0 <= root_col + c < COLS and 0 <= root_row + r < ROWS.
       - Occupancy Check: Must be empty OR belong to a single candidate swap item.
     If candidate placement overlaps exactly one existing item, the engine initiates
     an atomic swap (the existing item is returned into the hand slot).
  4. First-Fit Decreasing (FFD) Greedy Auto-Pack Solver:
     Sorts unplaced items by cell area descending and tests positions and rotations
     top-left to bottom-right, demonstrating combinatorial 2D bin-packing heuristics.
  5. Adjacency Synergy Pipeline (Backpack Hero Mechanics):
     Scans orthogonal neighbor cells (Up, Down, Left, Right) to award equipment
     synergy bonuses (e.g., Weapons adjacent to Relics gain +25% ATK; Shields adjacent
     to Helmets gain +20% DEF).

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - WASD / Arrow Keys / Left Stick / D-Pad : Move 2D Grid Selection Cursor
  - Mouse Move / Hover                     : Direct Point & Hover selection
  - Space / Enter / LMB / Gamepad A        : Pick Up Item / Place / Single-Item Swap
  - R / Mouse Wheel / Gamepad X / RB       : Rotate Held Item 90° Clockwise
  - Esc / RMB / Gamepad B                  : Cancel Held Item (Snap-Back to Origin)
  - P / Gamepad Y                          : Run First-Fit Decreasing Auto-Pack Heuristic
  - N / Gamepad R3                         : Spawn Random Equipment into Staging Tray
  - [Tab] / Gamepad View (Select)          : Toggle X-Ray Telemetry & Memory Matrix
  - [F1]  / Gamepad LB                     : Toggle Shape Collision: [Strict] vs [Permissive Overlap]
  - [Ctrl +/-]                             : Increase / Decrease UI Font Size
  - [F11]                                  : Toggle Fullscreen
  - Backspace / Gamepad Start              : Reset Backpack to Default Layout
"""

import sys
import os
import math
import random

# 1. Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# 2. Add repository root to search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 3. Mandatory Raylib & modular workspace imports
from pyray import *
from assets import *
from utils import *

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WINDOW_TITLE = "Tetris Backpack - Shape-Packing Inventory (Raylib Pattern Lab)"

# Grid Configuration
BACKPACK_COLS = 10
BACKPACK_ROWS = 7
TOTAL_BACKPACK_CELLS = BACKPACK_COLS * BACKPACK_ROWS

TRAY_COLS = 4
TRAY_ROWS = 7
TOTAL_TRAY_CELLS = TRAY_COLS * TRAY_ROWS

CELL_SIZE = 44
CELL_GAP = 4

# Layout Coordinates
BACKPACK_X = 50
BACKPACK_Y = 115
BACKPACK_W = BACKPACK_COLS * CELL_SIZE + (BACKPACK_COLS - 1) * CELL_GAP
BACKPACK_H = BACKPACK_ROWS * CELL_SIZE + (BACKPACK_ROWS - 1) * CELL_GAP

TRAY_X = 556
TRAY_Y = 115
TRAY_W = TRAY_COLS * CELL_SIZE + (TRAY_COLS - 1) * CELL_GAP
TRAY_H = TRAY_ROWS * CELL_SIZE + (TRAY_ROWS - 1) * CELL_GAP

STATS_PANEL_X = 50
STATS_PANEL_Y = 475
STATS_PANEL_W = 694
STATS_PANEL_H = 225

TELEMETRY_X = 766
TELEMETRY_Y = 66
TELEMETRY_W = 484
TELEMETRY_H = 634

# Visual Palette
COLOR_BG               = Color(11, 14, 22, 255)
COLOR_PANEL_BG         = Color(18, 23, 35, 255)
COLOR_PANEL_BORDER     = Color(42, 54, 82, 255)
COLOR_CELL_EMPTY       = Color(14, 18, 28, 255)
COLOR_CELL_BORDER      = Color(30, 39, 60, 255)
COLOR_CELL_HOVER       = Color(65, 88, 130, 255)
COLOR_TEXT_MAIN        = Color(230, 240, 255, 255)
COLOR_TEXT_DIM         = Color(135, 155, 185, 255)
COLOR_ACCENT_CYAN      = Color(0, 225, 255, 255)
COLOR_ACCENT_GOLD      = Color(255, 210, 60, 255)
COLOR_ACCENT_GREEN     = Color(60, 240, 120, 255)
COLOR_ACCENT_RED       = Color(255, 70, 70, 255)

# Container IDs
CONTAINER_BACKPACK = 0
CONTAINER_TRAY     = 1

# Item Archetype Identifiers (Equivalent to C++ enum ItemID)
ITEM_CLAYMORE       = 1
ITEM_BASTION_SHIELD = 2
ITEM_WAR_AXE        = 3
ITEM_WARHAMMER      = 4
ITEM_KNIGHT_HELM    = 5
ITEM_SHADOW_DIRK    = 6
ITEM_POTION         = 7
ITEM_MANA_GEM       = 8
ITEM_COSMIC_RELIC   = 9
ITEM_UTILITY_BELT   = 10


# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATION (SHAPE-PACKING INVENTORY)
# ==============================================================================

def compute_rotation_90_cw(offsets):
    """
    Rotates a set of 2D cell offsets 90 degrees clockwise and normalizes
    coordinates so the top-left corner starts at (0, 0).
    C++ Equivalent:
      for (int i = 0; i < count; i++) {
          int c = offsets[i].col;
          int r = offsets[i].row;
          rot_c[i] = -r;
          rot_r[i] = c;
          if (rot_c[i] < min_c) min_c = rot_c[i];
          if (rot_r[i] < min_r) min_r = rot_r[i];
      }
    """
    min_c = 999999
    min_r = 999999
    rotated = []
    for pair in offsets:
        c = pair[0]
        r = pair[1]
        new_c = -r
        new_r = c
        rotated.append((new_c, new_r))
        if new_c < min_c:
            min_c = new_c
        if new_r < min_r:
            min_r = new_r

    normalized = []
    for pair in rotated:
        norm_c = pair[0] - min_c
        norm_r = pair[1] - min_r
        normalized.append((norm_c, norm_r))

    # Sort canonically (row-first, then col) for deterministic matching
    for i in range(len(normalized)):
        for j in range(i + 1, len(normalized)):
            p1 = normalized[i]
            p2 = normalized[j]
            if (p2[1] < p1[1]) or (p2[1] == p1[1] and p2[0] < p1[0]):
                normalized[i] = p2
                normalized[j] = p1

    return normalized


class PolyominoVariant:
    """
    Precomputed geometric footprint of a polyomino at a specific 90° rotation.
    C++ Equivalent:
      struct PolyominoVariant {
          CellOffset cells[MAX_CELLS];
          int count;
          int width;
          int height;
      };
    """
    def __init__(self, offsets):
        self.offsets = offsets
        self.count = len(offsets)
        max_c = 0
        max_r = 0
        for pair in offsets:
            if pair[0] > max_c:
                max_c = pair[0]
            if pair[1] > max_r:
                max_r = pair[1]
        self.width = max_c + 1
        self.height = max_r + 1


class ItemArchetype:
    """
    Static blueprint metadata for an item polyomino archetype.
    C++ Equivalent:
      struct ItemArchetype {
          int id;
          const char* name;
          const char* category;
          PolyominoVariant rotations[4];
          int atk;
          int defense;
          int heal;
          int mana;
          int gold;
          Color color_main;
          Color color_accent;
      };
    """
    def __init__(self, item_id: int, name: str, category: str, base_offsets,
                 atk: int, defense: int, heal: int, mana: int, gold: int,
                 color_main: Color, color_accent: Color):
        self.id = item_id
        self.name = name
        self.category = category
        self.atk = atk
        self.defense = defense
        self.heal = heal
        self.mana = mana
        self.gold = gold
        self.color_main = color_main
        self.color_accent = color_accent

        # Precompute the 4 discrete rotations (0°, 90°, 180°, 270°)
        self.rotations = []
        cur_offsets = base_offsets
        for _ in range(4):
            variant = PolyominoVariant(cur_offsets)
            self.rotations.append(variant)
            cur_offsets = compute_rotation_90_cw(cur_offsets)

    def get_variant(self, rotation: int) -> PolyominoVariant:
        rot_idx = rotation % 4
        return self.rotations[rot_idx]


class ItemInstance:
    """
    Dynamic state of a physical item inhabiting a grid or held in the hand slot.
    C++ Equivalent:
      struct ItemInstance {
          int instance_id;
          int archetype_id;
          int root_col;
          int root_row;
          int rotation;
          int container_id;
      };
    """
    def __init__(self, instance_id: int, archetype_id: int,
                 root_col: int = 0, root_row: int = 0, rotation: int = 0,
                 container_id: int = CONTAINER_BACKPACK):
        self.instance_id = instance_id
        self.archetype_id = archetype_id
        self.root_col = root_col
        self.root_row = root_row
        self.rotation = rotation
        self.container_id = container_id

    def clone(self):
        copy_inst = ItemInstance(
            self.instance_id,
            self.archetype_id,
            self.root_col,
            self.root_row,
            self.rotation,
            self.container_id
        )
        return copy_inst


class GridContainer:
    """
    Discrete 2D spatial grid storage backed by a contiguous 1D array.
    C++ Equivalent:
      class GridContainer {
          int cols;
          int rows;
          int cells[MAX_CELLS];
          ItemInstance items[MAX_ITEMS];
          int item_count;
      };
    """
    def __init__(self, cols: int, rows: int, container_id: int):
        self.cols = cols
        self.rows = rows
        self.container_id = container_id
        self.total_cells = cols * rows
        # Flat occupancy buffer: stores instance_id or -1 (EMPTY)
        self.cells = [-1] * self.total_cells
        self.items = []

    def get_flat_index(self, col: int, row: int) -> int:
        return row * self.cols + col

    def clear(self):
        for i in range(self.total_cells):
            self.cells[i] = -1
        self.items = []

    def can_place(self, archetype: ItemArchetype, root_col: int, root_row: int,
                  rotation: int, ignore_instance_id: int = -1,
                  strict_mode: bool = True) -> bool:
        """
        Tests whether a polyomino can inhabit (root_col, root_row) with rotation.
        Returns False if any cell falls out of bounds, or if occupied and strict_mode is True.
        """
        variant = archetype.get_variant(rotation)
        for pair in variant.offsets:
            c = root_col + pair[0]
            r = root_row + pair[1]

            # 1. Bounds Check
            if c < 0 or c >= self.cols or r < 0 or r >= self.rows:
                return False

            # 2. Occupancy Check
            if strict_mode:
                idx = self.get_flat_index(c, r)
                occ = self.cells[idx]
                if occ != -1 and occ != ignore_instance_id:
                    return False

        return True

    def get_overlapping_instances(self, archetype: ItemArchetype, root_col: int,
                                  root_row: int, rotation: int,
                                  ignore_instance_id: int = -1):
        """
        Collects unique item instance IDs obstructed by this candidate placement.
        If exactly 1 unique instance is obstructed, a Single-Item Swap is permissible.
        """
        variant = archetype.get_variant(rotation)
        overlapping = []

        for pair in variant.offsets:
            c = root_col + pair[0]
            r = root_row + pair[1]
            if c < 0 or c >= self.cols or r < 0 or r >= self.rows:
                # Out of bounds cannot be resolved by item swapping
                return [-999]

            idx = self.get_flat_index(c, r)
            occ = self.cells[idx]
            if occ != -1 and occ != ignore_instance_id:
                if occ not in overlapping:
                    overlapping.append(occ)

        return overlapping

    def place_item(self, item: ItemInstance, archetype: ItemArchetype,
                   root_col: int, root_row: int, rotation: int):
        """Commits an item into the grid, stamping its instance_id into all cells."""
        # Clear any prior cells inhabited by this instance
        self.remove_item(item)

        item.root_col = root_col
        item.root_row = root_row
        item.rotation = rotation
        item.container_id = self.container_id

        variant = archetype.get_variant(rotation)
        for pair in variant.offsets:
            c = root_col + pair[0]
            r = root_row + pair[1]
            if 0 <= c < self.cols and 0 <= r < self.rows:
                idx = self.get_flat_index(c, r)
                self.cells[idx] = item.instance_id

        # Register in item array if not already tracked
        found = False
        for it in self.items:
            if it.instance_id == item.instance_id:
                found = True
                break
        if not found:
            self.items.append(item)

    def remove_item(self, item: ItemInstance):
        """Clears all grid cells inhabited by this instance."""
        target_id = item.instance_id
        for i in range(self.total_cells):
            if self.cells[i] == target_id:
                self.cells[i] = -1

        new_items = []
        for it in self.items:
            if it.instance_id != target_id:
                new_items.append(it)
        self.items = new_items

    def get_item_by_instance_id(self, instance_id: int):
        for it in self.items:
            if it.instance_id == instance_id:
                return it
        return None

    def get_occupied_count(self) -> int:
        count = 0
        for i in range(self.total_cells):
            if self.cells[i] != -1:
                count += 1
        return count


class HandSlot:
    """
    Decoupled hand slot state machine holding floating items during transactions.
    Ensures atomic pick, swap, and cancel-to-origin guarantees.
    """
    def __init__(self):
        self.item = None
        self.origin_container = CONTAINER_BACKPACK
        self.origin_col = 0
        self.origin_row = 0
        self.origin_rot = 0
        self.is_holding = False

    def pick_up(self, item: ItemInstance, origin_container: int):
        self.item = item
        self.origin_container = origin_container
        self.origin_col = item.root_col
        self.origin_row = item.root_row
        self.origin_rot = item.rotation
        self.is_holding = True

    def clear(self):
        self.item = None
        self.is_holding = False


# ==============================================================================
# BLOCK 2: WORLD SIMULATION & ENTITIES
# ==============================================================================

class TetrisBackpackSimulation:
    """
    Coordinates item archetypes, backpack & tray containers, cursor navigation,
    equipment stats calculation, and adjacency synergies.
    """
    def __init__(self):
        self.archetypes = {}
        self._init_archetypes()

        self.backpack = GridContainer(BACKPACK_COLS, BACKPACK_ROWS, CONTAINER_BACKPACK)
        self.tray = GridContainer(TRAY_COLS, TRAY_ROWS, CONTAINER_TRAY)
        self.hand = HandSlot()

        self.next_instance_id = 1
        self.strict_shape_mode = True   # [F1] Toggle: Strict vs Permissive Overlap

        # Cursor navigation state
        self.active_container = CONTAINER_BACKPACK
        self.cursor_col = 0
        self.cursor_row = 0
        self.mouse_inside_backpack = False
        self.mouse_inside_tray = False

        # Visual feedback timers
        self.error_shake_timer = 0.0
        self.feedback_banner = "Welcome to Tetris Backpack! Grab and pack polyomino items."
        self.banner_timer = 5.0

        # Metrics
        self.total_atk = 0
        self.total_def = 0
        self.total_heal = 0
        self.total_mana = 0
        self.total_gold = 0
        self.active_synergies = []

        self.reset_default_loadout()

    def _init_archetypes(self):
        """Defines all polyomino equipment archetypes with geometric cell masks."""
        # 1. Great Claymore: 1x4 vertical bar (I-Tetromino)
        claymore_cells = [(0, 0), (0, 1), (0, 2), (0, 3)]
        self.archetypes[ITEM_CLAYMORE] = ItemArchetype(
            ITEM_CLAYMORE, "Great Claymore", "Weapon", claymore_cells,
            atk=35, defense=0, heal=0, mana=0, gold=140,
            color_main=Color(80, 200, 240, 255), color_accent=Color(180, 240, 255, 255)
        )

        # 2. Bastion Shield: 2x3 solid rectangle (Hexomino)
        shield_cells = [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2)]
        self.archetypes[ITEM_BASTION_SHIELD] = ItemArchetype(
            ITEM_BASTION_SHIELD, "Bastion Shield", "Armor", shield_cells,
            atk=0, defense=45, heal=0, mana=0, gold=160,
            color_main=Color(70, 115, 180, 255), color_accent=Color(135, 185, 245, 255)
        )

        # 3. Battleaxe: L-shape polyomino (4 cells: vertical shaft 3 cells + blade 1 cell)
        axe_cells = [(0, 0), (0, 1), (0, 2), (1, 0)]
        self.archetypes[ITEM_WAR_AXE] = ItemArchetype(
            ITEM_WAR_AXE, "Battleaxe", "Weapon", axe_cells,
            atk=26, defense=0, heal=0, mana=0, gold=110,
            color_main=Color(235, 90, 60, 255), color_accent=Color(255, 175, 120, 255)
        )

        # 4. Thunder Maul: T-shape polyomino (5 cells: 3 hammerhead + 2 handle)
        maul_cells = [(0, 0), (1, 0), (2, 0), (1, 1), (1, 2)]
        self.archetypes[ITEM_WARHAMMER] = ItemArchetype(
            ITEM_WARHAMMER, "Thunder Maul", "Weapon", maul_cells,
            atk=42, defense=0, heal=0, mana=0, gold=180,
            color_main=Color(175, 90, 235, 255), color_accent=Color(230, 170, 255, 255)
        )

        # 5. Knight Helm: 2x2 square (O-Tetromino)
        helm_cells = [(0, 0), (1, 0), (0, 1), (1, 1)]
        self.archetypes[ITEM_KNIGHT_HELM] = ItemArchetype(
            ITEM_KNIGHT_HELM, "Knight Helm", "Armor", helm_cells,
            atk=0, defense=22, heal=0, mana=0, gold=90,
            color_main=Color(225, 180, 50, 255), color_accent=Color(255, 230, 140, 255)
        )

        # 6. Shadow Dirk: 1x2 bar (Domino)
        dirk_cells = [(0, 0), (0, 1)]
        self.archetypes[ITEM_SHADOW_DIRK] = ItemArchetype(
            ITEM_SHADOW_DIRK, "Shadow Dirk", "Weapon", dirk_cells,
            atk=14, defense=0, heal=0, mana=0, gold=50,
            color_main=Color(45, 210, 120, 255), color_accent=Color(140, 255, 190, 255)
        )

        # 7. Elixir of Life: 1x1 cell (Monomino)
        potion_cells = [(0, 0)]
        self.archetypes[ITEM_POTION] = ItemArchetype(
            ITEM_POTION, "Elixir of Life", "Consumable", potion_cells,
            atk=0, defense=0, heal=60, mana=0, gold=35,
            color_main=Color(245, 60, 75, 255), color_accent=Color(255, 160, 170, 255)
        )

        # 8. Arcane Core: 1x1 cell (Monomino)
        gem_cells = [(0, 0)]
        self.archetypes[ITEM_MANA_GEM] = ItemArchetype(
            ITEM_MANA_GEM, "Arcane Core", "Consumable", gem_cells,
            atk=0, defense=0, heal=0, mana=50, gold=40,
            color_main=Color(40, 175, 255, 255), color_accent=Color(160, 225, 255, 255)
        )

        # 9. Cosmic Relic: Z-shape polyomino (Z-Tetromino)
        relic_cells = [(0, 0), (1, 0), (1, 1), (2, 1)]
        self.archetypes[ITEM_COSMIC_RELIC] = ItemArchetype(
            ITEM_COSMIC_RELIC, "Cosmic Relic", "Artifact", relic_cells,
            atk=0, defense=0, heal=0, mana=20, gold=210,
            color_main=Color(240, 65, 160, 255), color_accent=Color(255, 165, 220, 255)
        )

        # 10. Adventurer Belt: 3x1 horizontal bar (Triomino)
        belt_cells = [(0, 0), (1, 0), (2, 0)]
        self.archetypes[ITEM_UTILITY_BELT] = ItemArchetype(
            ITEM_UTILITY_BELT, "Utility Belt", "Utility", belt_cells,
            atk=0, defense=6, heal=15, mana=0, gold=75,
            color_main=Color(215, 140, 45, 255), color_accent=Color(255, 200, 120, 255)
        )

    def reset_default_loadout(self):
        """Configures a showcase backpack with neatly packed items and loot in tray."""
        self.backpack.clear()
        self.tray.clear()
        self.hand.clear()

        # Place Claymore vertically on the left
        i1 = ItemInstance(1, ITEM_CLAYMORE, root_col=0, root_row=0, rotation=0)
        self.backpack.place_item(i1, self.archetypes[ITEM_CLAYMORE], 0, 0, 0)

        # Place Bastion Shield in upper middle
        i2 = ItemInstance(2, ITEM_BASTION_SHIELD, root_col=2, root_row=0, rotation=0)
        self.backpack.place_item(i2, self.archetypes[ITEM_BASTION_SHIELD], 2, 0, 0)

        # Place Knight Helm next to shield
        i3 = ItemInstance(3, ITEM_KNIGHT_HELM, root_col=4, root_row=0, rotation=0)
        self.backpack.place_item(i3, self.archetypes[ITEM_KNIGHT_HELM], 4, 0, 0)

        # Place Battleaxe
        i4 = ItemInstance(4, ITEM_WAR_AXE, root_col=7, root_row=0, rotation=0)
        self.backpack.place_item(i4, self.archetypes[ITEM_WAR_AXE], 7, 0, 0)

        # Place Utility Belt horizontally at bottom
        i5 = ItemInstance(5, ITEM_UTILITY_BELT, root_col=2, root_row=4, rotation=0)
        self.backpack.place_item(i5, self.archetypes[ITEM_UTILITY_BELT], 2, 4, 0)

        # Place Potions & Gems
        i6 = ItemInstance(6, ITEM_POTION, root_col=5, root_row=4, rotation=0)
        self.backpack.place_item(i6, self.archetypes[ITEM_POTION], 5, 4, 0)

        i7 = ItemInstance(7, ITEM_MANA_GEM, root_col=0, root_row=4, rotation=0)
        self.backpack.place_item(i7, self.archetypes[ITEM_MANA_GEM], 0, 4, 0)

        # Populate Staging Tray with unplaced loot items
        t1 = ItemInstance(8, ITEM_WARHAMMER, root_col=0, root_row=0, rotation=0, container_id=CONTAINER_TRAY)
        self.tray.place_item(t1, self.archetypes[ITEM_WARHAMMER], 0, 0, 0)

        t2 = ItemInstance(9, ITEM_COSMIC_RELIC, root_col=0, root_row=3, rotation=0, container_id=CONTAINER_TRAY)
        self.tray.place_item(t2, self.archetypes[ITEM_COSMIC_RELIC], 0, 3, 0)

        t3 = ItemInstance(10, ITEM_SHADOW_DIRK, root_col=3, root_row=3, rotation=0, container_id=CONTAINER_TRAY)
        self.tray.place_item(t3, self.archetypes[ITEM_SHADOW_DIRK], 3, 3, 0)

        self.next_instance_id = 11
        self.update_stats()

    def spawn_random_loot(self) -> bool:
        """Spawns a random equipment item into the first available space in the Staging Tray."""
        available_ids = [
            ITEM_CLAYMORE, ITEM_BASTION_SHIELD, ITEM_WAR_AXE, ITEM_WARHAMMER,
            ITEM_KNIGHT_HELM, ITEM_SHADOW_DIRK, ITEM_POTION, ITEM_MANA_GEM,
            ITEM_COSMIC_RELIC, ITEM_UTILITY_BELT
        ]
        chosen_id = random.choice(available_ids)
        archetype = self.archetypes[chosen_id]

        # First-fit search in Tray
        placed = False
        for rot in range(4):
            if placed:
                break
            for r in range(self.tray.rows):
                if placed:
                    break
                for c in range(self.tray.cols):
                    if self.tray.can_place(archetype, c, r, rot, strict_mode=True):
                        new_inst = ItemInstance(
                            self.next_instance_id, chosen_id,
                            root_col=c, root_row=r, rotation=rot,
                            container_id=CONTAINER_TRAY
                        )
                        self.next_instance_id += 1
                        self.tray.place_item(new_inst, archetype, c, r, rot)
                        placed = True
                        break

        if placed:
            self.feedback_banner = f"Spawned loot: {archetype.name} into Staging Tray!"
            self.banner_timer = 3.0
            return True
        else:
            self.feedback_banner = "Staging Tray is full! Move items to backpack first."
            self.banner_timer = 3.0
            return False

    def run_auto_pack(self) -> int:
        """
        Executes First-Fit Decreasing (FFD) polyomino packing to pack items from Tray into Backpack.
        Sorts candidate items by cell area descending and searches positions (c, r) and rotations.
        """
        # Collect items from tray
        tray_items = []
        for it in self.tray.items:
            tray_items.append(it.clone())

        # Sort descending by cell count, then archetype ID
        for i in range(len(tray_items)):
            for j in range(i + 1, len(tray_items)):
                a1 = self.archetypes[tray_items[i].archetype_id]
                a2 = self.archetypes[tray_items[j].archetype_id]
                c1 = a1.get_variant(0).count
                c2 = a2.get_variant(0).count
                if c2 > c1:
                    temp = tray_items[i]
                    tray_items[i] = tray_items[j]
                    tray_items[j] = temp

        packed_count = 0
        for it in tray_items:
            archetype = self.archetypes[it.archetype_id]
            placed = False
            for rot in range(4):
                if placed:
                    break
                for r in range(self.backpack.rows):
                    if placed:
                        break
                    for c in range(self.backpack.cols):
                        if self.backpack.can_place(archetype, c, r, rot, strict_mode=True):
                            # Remove original from tray
                            tray_orig = self.tray.get_item_by_instance_id(it.instance_id)
                            if tray_orig is not None:
                                self.tray.remove_item(tray_orig)

                            # Place in backpack
                            it.container_id = CONTAINER_BACKPACK
                            self.backpack.place_item(it, archetype, c, r, rot)
                            placed = True
                            packed_count += 1
                            break

        self.update_stats()
        if packed_count > 0:
            self.feedback_banner = f"Auto-Pack complete! Packed {packed_count} item(s) into backpack."
        else:
            self.feedback_banner = "Auto-Pack could not fit remaining tray items."
        self.banner_timer = 4.0
        return packed_count

    def update_stats(self):
        """Calculates combined equipment stats and detects adjacency synergies."""
        base_atk = 0
        base_def = 0
        base_heal = 0
        base_mana = 0
        base_gold = 0

        for it in self.backpack.items:
            arch = self.archetypes[it.archetype_id]
            base_atk += arch.atk
            base_def += arch.defense
            base_heal += arch.heal
            base_mana += arch.mana
            base_gold += arch.gold

        # Scan for orthogonal adjacency synergies in Backpack
        synergies = []
        bonus_atk_pct = 0.0
        bonus_def_pct = 0.0
        bonus_heal_flat = 0

        checked_pairs = []

        for it in self.backpack.items:
            arch = self.archetypes[it.archetype_id]
            variant = arch.get_variant(it.rotation)

            for pair in variant.offsets:
                c = it.root_col + pair[0]
                r = it.root_row + pair[1]

                # 4 orthogonal neighbors
                neighbors = [(c + 1, r), (c - 1, r), (c, r + 1), (c, r - 1)]
                for nc, nr in neighbors:
                    if 0 <= nc < self.backpack.cols and 0 <= nr < self.backpack.rows:
                        n_idx = self.backpack.get_flat_index(nc, nr)
                        neighbor_id = self.backpack.cells[n_idx]
                        if neighbor_id != -1 and neighbor_id != it.instance_id:
                            neighbor_item = self.backpack.get_item_by_instance_id(neighbor_id)
                            if neighbor_item is not None:
                                pair_key = tuple(sorted([it.instance_id, neighbor_item.instance_id]))
                                if pair_key not in checked_pairs:
                                    checked_pairs.append(pair_key)
                                    n_arch = self.archetypes[neighbor_item.archetype_id]

                                    # Synergy 1: Weapon + Cosmic Relic -> Cosmic Resonance (+25% ATK)
                                    if (arch.category == "Weapon" and n_arch.id == ITEM_COSMIC_RELIC) or \
                                       (n_arch.category == "Weapon" and arch.id == ITEM_COSMIC_RELIC):
                                        bonus_atk_pct += 0.25
                                        synergies.append("Cosmic Resonance (+25% Weapon ATK)")

                                    # Synergy 2: Shield + Helm -> Fortified Phalanx (+20% DEF)
                                    if (arch.id == ITEM_BASTION_SHIELD and n_arch.id == ITEM_KNIGHT_HELM) or \
                                       (n_arch.id == ITEM_BASTION_SHIELD and arch.id == ITEM_KNIGHT_HELM):
                                        bonus_def_pct += 0.20
                                        synergies.append("Fortified Phalanx (+20% Shield DEF)")

                                    # Synergy 3: Potion + Belt -> Quick Holster (+15 Heal)
                                    if (arch.id == ITEM_POTION and n_arch.id == ITEM_UTILITY_BELT) or \
                                       (n_arch.id == ITEM_POTION and arch.id == ITEM_UTILITY_BELT):
                                        bonus_heal_flat += 15
                                        synergies.append("Quick Holster (+15 Potion Heal)")

        self.total_atk = int(base_atk * (1.0 + bonus_atk_pct))
        self.total_def = int(base_def * (1.0 + bonus_def_pct))
        self.total_heal = base_heal + bonus_heal_flat
        self.total_mana = base_mana
        self.total_gold = base_gold
        self.active_synergies = synergies

    def count_dead_fragments(self) -> int:
        """Counts isolated 1x1 empty holes in the backpack (packing fragmentation)."""
        dead_holes = 0
        for r in range(self.backpack.rows):
            for c in range(self.backpack.cols):
                idx = self.backpack.get_flat_index(c, r)
                if self.backpack.cells[idx] == -1:
                    # Check 4 neighbors
                    neighbors = [(c + 1, r), (c - 1, r), (c, r + 1), (c, r - 1)]
                    free_neighbors = 0
                    for nc, nr in neighbors:
                        if 0 <= nc < self.backpack.cols and 0 <= nr < self.backpack.rows:
                            n_idx = self.backpack.get_flat_index(nc, nr)
                            if self.backpack.cells[n_idx] == -1:
                                free_neighbors += 1
                    if free_neighbors == 0:
                        dead_holes += 1
        return dead_holes


# ==============================================================================
# BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY ([Tab] & [F1])
# ==============================================================================

def draw_xray_telemetry(sim: TetrisBackpackSimulation, sfx: SoundLibrary):
    """
    Renders internal data structures: flat memory buffers, polyomino coordinate
    matrices, 90° clockwise rotation equations, and packing metrics.
    """
    draw_rectangle(TELEMETRY_X, TELEMETRY_Y, TELEMETRY_W, TELEMETRY_H, COLOR_PANEL_BG)
    draw_rectangle_lines(TELEMETRY_X, TELEMETRY_Y, TELEMETRY_W, TELEMETRY_H, COLOR_PANEL_BORDER)

    # Header
    draw_rectangle(TELEMETRY_X, TELEMETRY_Y, TELEMETRY_W, 32, Color(26, 34, 52, 255))
    draw_text("X-RAY SHAPE-PACKING TELEMETRY [Tab]", TELEMETRY_X + 14, TELEMETRY_Y + 8, 16, COLOR_ACCENT_CYAN)

    y = TELEMETRY_Y + 44

    # 1. Memory Buffer Array Visualization (10x7 Flat Array)
    draw_text("1. Spatial Memory Matrix (int cells[70]):", TELEMETRY_X + 14, y, 13, COLOR_TEXT_MAIN)
    y += 20

    mini_cell_w = 40
    mini_cell_h = 16
    start_mini_x = TELEMETRY_X + 14

    for r in range(BACKPACK_ROWS):
        for c in range(BACKPACK_COLS):
            f_idx = sim.backpack.get_flat_index(c, r)
            val = sim.backpack.cells[f_idx]
            cx = start_mini_x + c * (mini_cell_w + 3)
            cy = y + r * (mini_cell_h + 3)

            if val == -1:
                col_box = Color(14, 18, 28, 255)
                txt_str = "-1"
                txt_col = Color(80, 95, 120, 255)
            else:
                col_box = Color(35, 65, 110, 255)
                txt_str = f"#{val}"
                txt_col = Color(160, 220, 255, 255)

            draw_rectangle(cx, cy, mini_cell_w, mini_cell_h, col_box)
            draw_rectangle_lines(cx, cy, mini_cell_w, mini_cell_h, Color(40, 52, 75, 255))
            draw_text(txt_str, cx + 4, cy + 2, 11, txt_col)

    y += BACKPACK_ROWS * (mini_cell_h + 3) + 14

    # 2. Packing Density & Fragmentation Metrics
    occ = sim.backpack.get_occupied_count()
    total = TOTAL_BACKPACK_CELLS
    pct = (occ / float(total)) * 100.0
    dead_holes = sim.count_dead_fragments()

    draw_text("2. Packing Efficiency & Fragmentation:", TELEMETRY_X + 14, y, 13, COLOR_TEXT_MAIN)
    y += 18

    # Progress bar
    bar_w = TELEMETRY_W - 28
    bar_h = 16
    draw_rectangle(TELEMETRY_X + 14, y, bar_w, bar_h, Color(16, 20, 30, 255))
    fill_w = int((occ / float(total)) * bar_w)
    draw_rectangle(TELEMETRY_X + 14, y, fill_w, bar_h, Color(45, 180, 100, 255))
    draw_rectangle_lines(TELEMETRY_X + 14, y, bar_w, bar_h, COLOR_PANEL_BORDER)
    draw_text(f"{pct:.1f}% Density", TELEMETRY_X + 22, y + 2, 11, COLOR_TEXT_MAIN)
    y += 22

    draw_text(f"Occupied: {occ} / {total} cells | Free: {total - occ} cells", TELEMETRY_X + 14, y, 12, COLOR_TEXT_DIM)
    y += 16
    frag_col = COLOR_ACCENT_RED if dead_holes > 0 else COLOR_ACCENT_GREEN
    draw_text(f"Dead Fragments (Isolated 1x1 Holes): {dead_holes}", TELEMETRY_X + 14, y, 12, frag_col)
    y += 24

    # 3. Active Polyomino Transform Inspector
    draw_text("3. Active Polyomino Inspector & Rotation Math:", TELEMETRY_X + 14, y, 13, COLOR_TEXT_MAIN)
    y += 18

    held_item = sim.hand.item
    if held_item is not None:
        arch = sim.archetypes[held_item.archetype_id]
        var = arch.get_variant(held_item.rotation)
        deg = (held_item.rotation % 4) * 90

        draw_text(f"Target: {arch.name} ({arch.category})", TELEMETRY_X + 14, y, 12, COLOR_ACCENT_GOLD)
        y += 16
        draw_text(f"Rotation: {deg}° (Variant {held_item.rotation % 4}/4) | Box: {var.width}x{var.height}", TELEMETRY_X + 14, y, 12, COLOR_TEXT_DIM)
        y += 16

        # Print coordinate offsets
        offset_strs = []
        for pair in var.offsets:
            offset_strs.append(f"({pair[0]},{pair[1]})")
        draw_text(f"Cell Offsets: {', '.join(offset_strs)}", TELEMETRY_X + 14, y, 11, COLOR_ACCENT_CYAN)
        y += 18
    else:
        draw_text("No item held. Hover and press Space/A to inspect.", TELEMETRY_X + 14, y, 12, COLOR_TEXT_DIM)
        y += 34

    # Mathematical Formula Explanation
    draw_rectangle(TELEMETRY_X + 14, y, TELEMETRY_W - 28, 54, Color(14, 18, 28, 255))
    draw_rectangle_lines(TELEMETRY_X + 14, y, TELEMETRY_W - 28, 54, Color(35, 48, 72, 255))
    draw_text("Discrete 90° Clockwise Rotation Formula:", TELEMETRY_X + 22, y + 6, 11, COLOR_ACCENT_GOLD)
    draw_text("col' = -row,  row' = col", TELEMETRY_X + 22, y + 20, 11, COLOR_TEXT_MAIN)
    draw_text("col_norm = col' - min(col'),  row_norm = row' - min(row')", TELEMETRY_X + 22, y + 34, 11, COLOR_TEXT_DIM)
    y += 66

    # 4. Pattern Comparison Toggle [F1]
    draw_text("4. Pattern Comparison Mode ([F1]):", TELEMETRY_X + 14, y, 13, COLOR_TEXT_MAIN)
    y += 18
    if sim.strict_shape_mode:
        mode_str = "STRICT SHAPE COLLISION (ACTIVE)"
        mode_col = COLOR_ACCENT_GREEN
        mode_desc = "Multi-cell bounds & overlap checks enforced. Clean transactions."
    else:
        mode_str = "PERMISSIVE OVERLAP (DEMO - BROKEN INVENTORY)"
        mode_col = COLOR_ACCENT_RED
        mode_desc = "Simulates naive games: overlaps allowed, causing cell corruption."

    draw_text(mode_str, TELEMETRY_X + 14, y, 12, mode_col)
    y += 16
    draw_text(mode_desc, TELEMETRY_X + 14, y, 11, COLOR_TEXT_DIM)
    y += 24

    # 5. Algorithmic Complexity Benchmark
    draw_text("5. Algorithmic Complexity:", TELEMETRY_X + 14, y, 13, COLOR_TEXT_MAIN)
    y += 16
    draw_text("- Collision Test: O(K) where K <= 6 cells (Constant Time)", TELEMETRY_X + 14, y, 11, COLOR_TEXT_DIM)
    y += 14
    draw_text("- Memory Footprint: 70 x 4 bytes = 280 bytes (Zero GC)", TELEMETRY_X + 14, y, 11, COLOR_TEXT_DIM)
    y += 14
    draw_text("- Greedy Auto-Pack: O(N * R * W * H) First-Fit Decreasing", TELEMETRY_X + 14, y, 11, COLOR_TEXT_DIM)


# ==============================================================================
# BLOCK 4: MAIN GAME LOOP & AUTOMATED SMOKE TEST
# ==============================================================================

class TetrisBackpackGame:
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()

        self.sfx = SoundLibrary()
        self.sfx.init_defaults()

        self.sim = TetrisBackpackSimulation()
        self.show_xray = True

        # Smooth mouse position tracking
        self.mouse_pos = Vector2(0, 0)
        self.cursor_flash_timer = 0.0

    def handle_input(self, dt: float):
        # 1. Dual X-Ray Toggle [Tab] / Gamepad Select
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
            self.sfx.play("click", 0.6)

        # 2. Dual Pattern Mode Toggle [F1] / Gamepad LB
        if is_dual_pattern_toggle_pressed():
            self.sim.strict_shape_mode = not self.sim.strict_shape_mode
            self.sfx.play("click", 0.7)
            if self.sim.strict_shape_mode:
                self.sim.feedback_banner = "Mode changed: STRICT Polyomino Shape-Packing (Standard)"
            else:
                self.sim.feedback_banner = "Mode changed: PERMISSIVE OVERLAP (Naive Collision Demo)"
            self.sim.banner_timer = 3.5

        # 3. Dual Auto-Pack Heuristic [P] / [F2] / Gamepad Y
        if is_key_pressed(KEY_P) or is_dual_secondary_toggle_pressed() or is_key_pressed(KEY_F2):
            packed = self.sim.run_auto_pack()
            if packed > 0:
                self.sfx.play("powerup", 0.8)
            else:
                self.sfx.play("hit", 0.7)

        # 4. Spawn Random Loot [N] / Gamepad R3
        pad_id = get_active_gamepad_id()
        gamepad_r3 = (pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_THUMB))
        if is_key_pressed(KEY_N) or gamepad_r3:
            spawned = self.sim.spawn_random_loot()
            if spawned:
                self.sfx.play("coin", 0.7)
            else:
                self.sfx.play("hit", 0.6)

        # 5. Reset Loadout [R] (with no item held) or Gamepad Start
        gamepad_start = (pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_MIDDLE_RIGHT))
        if (is_key_pressed(KEY_BACKSPACE) or (is_key_pressed(KEY_R) and not self.sim.hand.is_holding) or gamepad_start):
            self.sim.reset_default_loadout()
            self.sfx.play("laser", 0.6)
            self.sim.feedback_banner = "Backpack reset to default loadout!"
            self.sim.banner_timer = 3.0

        # 6. Rotate Held Item: [R] (when holding) / Mouse Wheel / Gamepad X / Gamepad RB
        wheel_move = get_mouse_wheel_move()
        gamepad_rotate = False
        if pad_id >= 0:
            if is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_FACE_LEFT) or \
               is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_TRIGGER_1):
                gamepad_rotate = True

        if self.sim.hand.is_holding:
            if is_key_pressed(KEY_R) or abs(wheel_move) > 0.1 or gamepad_rotate:
                self.sim.hand.item.rotation = (self.sim.hand.item.rotation + 1) % 4
                self.sfx.play("jump", 0.7)

        # 7. Cancel / Snap-Back Held Item: [Esc] / RMB / Gamepad B
        gamepad_b = (pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_FACE_RIGHT))
        if self.sim.hand.is_holding and (is_key_pressed(KEY_ESCAPE) or is_mouse_button_pressed(MOUSE_BUTTON_RIGHT) or gamepad_b):
            self._cancel_hand_item()

        # 8. Mouse Coordinate Resolution
        m_x = get_mouse_x()
        m_y = get_mouse_y()
        self.mouse_pos = Vector2(float(m_x), float(m_y))

        # Check if mouse is hovering over Backpack Grid
        if BACKPACK_X <= m_x < BACKPACK_X + BACKPACK_W and BACKPACK_Y <= m_y < BACKPACK_Y + BACKPACK_H:
            self.sim.mouse_inside_backpack = True
            self.sim.mouse_inside_tray = False
            self.sim.active_container = CONTAINER_BACKPACK
            cell_stride = CELL_SIZE + CELL_GAP
            col = int((m_x - BACKPACK_X) / cell_stride)
            row = int((m_y - BACKPACK_Y) / cell_stride)
            self.sim.cursor_col = max(0, min(BACKPACK_COLS - 1, col))
            self.sim.cursor_row = max(0, min(BACKPACK_ROWS - 1, row))

        # Check if mouse is hovering over Staging Tray
        elif TRAY_X <= m_x < TRAY_X + TRAY_W and TRAY_Y <= m_y < TRAY_Y + TRAY_H:
            self.sim.mouse_inside_tray = True
            self.sim.mouse_inside_backpack = False
            self.sim.active_container = CONTAINER_TRAY
            cell_stride = CELL_SIZE + CELL_GAP
            col = int((m_x - TRAY_X) / cell_stride)
            row = int((m_y - TRAY_Y) / cell_stride)
            self.sim.cursor_col = max(0, min(TRAY_COLS - 1, col))
            self.sim.cursor_row = max(0, min(TRAY_ROWS - 1, row))
        else:
            self.sim.mouse_inside_backpack = False
            self.sim.mouse_inside_tray = False

        # 9. Discrete Keyboard / Gamepad D-Pad Stepping
        move_step_x = 0
        move_step_y = 0
        if is_key_pressed(KEY_A) or is_key_pressed(KEY_LEFT):
            move_step_x -= 1
        if is_key_pressed(KEY_D) or is_key_pressed(KEY_RIGHT):
            move_step_x += 1
        if is_key_pressed(KEY_W) or is_key_pressed(KEY_UP):
            move_step_y -= 1
        if is_key_pressed(KEY_S) or is_key_pressed(KEY_DOWN):
            move_step_y += 1

        if pad_id >= 0:
            if is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_LEFT_FACE_LEFT):
                move_step_x -= 1
            if is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_LEFT_FACE_RIGHT):
                move_step_x += 1
            if is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_LEFT_FACE_UP):
                move_step_y -= 1
            if is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_LEFT_FACE_DOWN):
                move_step_y += 1

        if move_step_x != 0 or move_step_y != 0:
            self.sfx.play("click", 0.4)
            if self.sim.active_container == CONTAINER_BACKPACK:
                new_col = self.sim.cursor_col + move_step_x
                if new_col >= BACKPACK_COLS:
                    # Hop from Backpack to Tray
                    self.sim.active_container = CONTAINER_TRAY
                    self.sim.cursor_col = 0
                elif new_col < 0:
                    self.sim.cursor_col = 0
                else:
                    self.sim.cursor_col = new_col
                self.sim.cursor_row = max(0, min(BACKPACK_ROWS - 1, self.sim.cursor_row + move_step_y))
            else:
                new_col = self.sim.cursor_col + move_step_x
                if new_col < 0:
                    # Hop from Tray to Backpack
                    self.sim.active_container = CONTAINER_BACKPACK
                    self.sim.cursor_col = BACKPACK_COLS - 1
                elif new_col >= TRAY_COLS:
                    self.sim.cursor_col = TRAY_COLS - 1
                else:
                    self.sim.cursor_col = new_col
                self.sim.cursor_row = max(0, min(TRAY_ROWS - 1, self.sim.cursor_row + move_step_y))

        # 10. Primary Action: Pick Up / Place / Swap (Space / Enter / LMB / Gamepad A)
        action_pressed = is_dual_primary_fire_pressed() or is_key_pressed(KEY_SPACE) or is_key_pressed(KEY_ENTER)
        if action_pressed:
            self._handle_primary_action()

    def _cancel_hand_item(self):
        """Returns held item to its origin slot and container."""
        item = self.sim.hand.item
        if item is None:
            return

        arch = self.sim.archetypes[item.archetype_id]
        orig_container = self.sim.backpack if self.sim.hand.origin_container == CONTAINER_BACKPACK else self.sim.tray

        # Snap back
        orig_container.place_item(item, arch, self.sim.hand.origin_col, self.sim.hand.origin_row, self.sim.hand.origin_rot)
        self.sim.hand.clear()
        self.sim.update_stats()
        self.sfx.play("hurt", 0.6)
        self.sim.feedback_banner = f"Cancelled move: {arch.name} returned to origin."
        self.sim.banner_timer = 2.5

    def _handle_primary_action(self):
        """Executes pick up, placement, or atomic single-item swap."""
        active_container = self.sim.backpack if self.sim.active_container == CONTAINER_BACKPACK else self.sim.tray
        c_col = self.sim.cursor_col
        c_row = self.sim.cursor_row

        if not self.sim.hand.is_holding:
            # 1. PICK UP ITEM
            f_idx = active_container.get_flat_index(c_col, c_row)
            occ_id = active_container.cells[f_idx]
            if occ_id != -1:
                item = active_container.get_item_by_instance_id(occ_id)
                if item is not None:
                    active_container.remove_item(item)
                    self.sim.hand.pick_up(item, self.sim.active_container)
                    self.sim.update_stats()
                    self.sfx.play("click", 0.7)
                    arch = self.sim.archetypes[item.archetype_id]
                    self.sim.feedback_banner = f"Holding {arch.name}. Press R / Wheel to rotate."
                    self.sim.banner_timer = 3.0
            else:
                self.sfx.play("hit", 0.4)
        else:
            # 2. PLACE OR SWAP ITEM
            held_item = self.sim.hand.item
            arch = self.sim.archetypes[held_item.archetype_id]
            rot = held_item.rotation

            # Check bounds and overlaps
            if active_container.can_place(arch, c_col, c_row, rot, strict_mode=self.sim.strict_shape_mode):
                # Clean placement
                active_container.place_item(held_item, arch, c_col, c_row, rot)
                self.sim.hand.clear()
                self.sim.update_stats()
                self.sfx.play("coin", 0.8)
                self.sim.feedback_banner = f"Placed {arch.name}."
                self.sim.banner_timer = 2.5
            else:
                # Check for Single-Item Swap
                overlapping = active_container.get_overlapping_instances(arch, c_col, c_row, rot)
                if len(overlapping) == 1 and overlapping[0] != -999:
                    swap_target_id = overlapping[0]
                    target_item = active_container.get_item_by_instance_id(swap_target_id)
                    if target_item is not None:
                        # Remove swap target from grid
                        active_container.remove_item(target_item)
                        # Place held item
                        active_container.place_item(held_item, arch, c_col, c_row, rot)
                        # Pick up swap target into hand slot
                        self.sim.hand.pick_up(target_item, self.sim.active_container)
                        self.sim.update_stats()
                        self.sfx.play("coin", 0.8)
                        t_arch = self.sim.archetypes[target_item.archetype_id]
                        self.sim.feedback_banner = f"Swapped {arch.name} with {t_arch.name}!"
                        self.sim.banner_timer = 3.0
                        return

                # Placement Rejected
                self.sfx.play("hit", 0.8)
                self.sim.error_shake_timer = 0.25
                self.sim.feedback_banner = "Placement rejected: shape overlaps or falls outside bounds!"
                self.sim.banner_timer = 2.5

    def update(self):
        dt = min(get_frame_time(), 0.05)
        self.cursor_flash_timer += dt
        if self.sim.banner_timer > 0:
            self.sim.banner_timer -= dt
        if self.sim.error_shake_timer > 0:
            self.sim.error_shake_timer -= dt

        self.handle_input(dt)

    def draw(self):
        begin_drawing()
        clear_background(COLOR_BG)

        # 1. Top HUD Header
        draw_rectangle(0, 0, SCREEN_WIDTH, 52, Color(16, 21, 32, 255))
        draw_line(0, 52, SCREEN_WIDTH, 52, COLOR_PANEL_BORDER)

        draw_text("TETRIS BACKPACK", 32, 16, 20, COLOR_ACCENT_GOLD)
        draw_text("[Shape-Packing Inventory & Polyomino Storage]", 225, 20, 13, COLOR_TEXT_DIM)

        # Top-bar utilities (Reserved x = 450..980 for UI dropdowns)
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)

        # 2. Main Containers
        self._draw_container_grid(self.sim.backpack, BACKPACK_X, BACKPACK_Y, "ADVENTURER'S BACKPACK (10x7 Grid)")
        self._draw_container_grid(self.sim.tray, TRAY_X, TRAY_Y, "LOOT STAGING TRAY (4x7 Ground)")

        # 3. Ghost Placement Preview (if holding an item)
        if self.sim.hand.is_holding:
            self._draw_ghost_preview()

        # 4. Floating Hand Slot Item (follows mouse or discrete cursor)
        if self.sim.hand.is_holding:
            self._draw_held_item()

        # 5. Stats & Synergy Panel
        self._draw_stats_and_synergy_panel()

        # 6. Interactive Controls & Action Prompts
        self._draw_controls_footer()

        # 7. X-Ray Telemetry Overlay ([Tab])
        if self.show_xray:
            draw_xray_telemetry(self.sim, self.sfx)

        # 8. Feedback Notification Banner
        if self.sim.banner_timer > 0:
            self._draw_feedback_banner()

        end_drawing()

    def _draw_container_grid(self, container: GridContainer, start_x: int, start_y: int, title: str):
        """Renders grid cells, container border, title bar, and placed polyomino items."""
        grid_w = container.cols * CELL_SIZE + (container.cols - 1) * CELL_GAP
        grid_h = container.rows * CELL_SIZE + (container.rows - 1) * CELL_GAP

        # Container Frame
        draw_rectangle(start_x - 10, start_y - 32, grid_w + 20, grid_h + 42, COLOR_PANEL_BG)
        draw_rectangle_lines(start_x - 10, start_y - 32, grid_w + 20, grid_h + 42, COLOR_PANEL_BORDER)

        # Title
        is_active = (self.sim.active_container == container.container_id)
        title_col = COLOR_ACCENT_CYAN if is_active else COLOR_TEXT_DIM
        draw_text(title, start_x, start_y - 24, 13, title_col)

        # Background Cells
        for r in range(container.rows):
            for c in range(container.cols):
                cx = start_x + c * (CELL_SIZE + CELL_GAP)
                cy = start_y + r * (CELL_SIZE + CELL_GAP)
                draw_rectangle(cx, cy, CELL_SIZE, CELL_SIZE, COLOR_CELL_EMPTY)
                draw_rectangle_lines(cx, cy, CELL_SIZE, CELL_SIZE, COLOR_CELL_BORDER)

        # Placed Items
        for it in container.items:
            self._draw_placed_item(it, start_x, start_y)

        # Active Grid Cursor (if not holding or for navigation highlight)
        if self.sim.active_container == container.container_id:
            cur_cx = start_x + self.sim.cursor_col * (CELL_SIZE + CELL_GAP)
            cur_cy = start_y + self.sim.cursor_row * (CELL_SIZE + CELL_GAP)
            pulse_alpha = int(180 + 75 * math.sin(self.cursor_flash_timer * 6.0))
            cursor_col = Color(0, 225, 255, max(0, min(255, pulse_alpha)))
            draw_rectangle_lines(cur_cx - 2, cur_cy - 2, CELL_SIZE + 4, CELL_SIZE + 4, cursor_col)

    def _draw_placed_item(self, item: ItemInstance, start_x: int, start_y: int):
        """Renders all multi-cell blocks of a polyomino item with procedural icons."""
        arch = self.sim.archetypes[item.archetype_id]
        variant = arch.get_variant(item.rotation)

        stride = CELL_SIZE + CELL_GAP

        # 1. Fill Cells
        for pair in variant.offsets:
            cx = start_x + (item.root_col + pair[0]) * stride
            cy = start_y + (item.root_row + pair[1]) * stride

            # Cell body
            draw_rectangle(cx, cy, CELL_SIZE, CELL_SIZE, arch.color_main)

            # Inner subtle bevel
            draw_rectangle_lines(cx + 1, cy + 1, CELL_SIZE - 2, CELL_SIZE - 2, arch.color_accent)

        # 2. Draw Procedural Icon at visual centroid
        center_c = item.root_col + (variant.width - 1) * 0.5
        center_r = item.root_row + (variant.height - 1) * 0.5
        icon_x = start_x + int(center_c * stride) + CELL_SIZE // 2
        icon_y = start_y + int(center_r * stride) + CELL_SIZE // 2

        self._draw_item_glyph(arch.id, icon_x, icon_y)

    def _draw_ghost_preview(self):
        """Renders real-time placement feedback: Green (Valid), Gold (Swap), Red (Invalid)."""
        held_item = self.sim.hand.item
        if held_item is None:
            return

        active_container = self.sim.backpack if self.sim.active_container == CONTAINER_BACKPACK else self.sim.tray
        start_x = BACKPACK_X if self.sim.active_container == CONTAINER_BACKPACK else TRAY_X
        start_y = BACKPACK_Y if self.sim.active_container == CONTAINER_BACKPACK else TRAY_Y

        arch = self.sim.archetypes[held_item.archetype_id]
        rot = held_item.rotation
        variant = arch.get_variant(rot)

        c_col = self.sim.cursor_col
        c_row = self.sim.cursor_row
        stride = CELL_SIZE + CELL_GAP

        # Test validity
        is_valid = active_container.can_place(arch, c_col, c_row, rot, strict_mode=self.sim.strict_shape_mode)
        overlapping = active_container.get_overlapping_instances(arch, c_col, c_row, rot)
        is_swap = (not is_valid and len(overlapping) == 1 and overlapping[0] != -999)

        if is_valid:
            fill_col = Color(40, 220, 90, 130)
            border_col = Color(80, 255, 140, 255)
        elif is_swap:
            fill_col = Color(240, 200, 40, 130)
            border_col = Color(255, 230, 80, 255)
        else:
            fill_col = Color(240, 50, 50, 130)
            border_col = Color(255, 80, 80, 255)

        for pair in variant.offsets:
            gx = start_x + (c_col + pair[0]) * stride
            gy = start_y + (c_row + pair[1]) * stride

            draw_rectangle(gx, gy, CELL_SIZE, CELL_SIZE, fill_col)
            draw_rectangle_lines(gx, gy, CELL_SIZE, CELL_SIZE, border_col)

            if not is_valid and not is_swap:
                # Draw X inside invalid cell
                draw_line(gx + 6, gy + 6, gx + CELL_SIZE - 6, gy + CELL_SIZE - 6, border_col)
                draw_line(gx + CELL_SIZE - 6, gy + 6, gx + 6, gy + CELL_SIZE - 6, border_col)

    def _draw_held_item(self):
        """Draws the floating item following mouse or keyboard cursor."""
        held_item = self.sim.hand.item
        if held_item is None:
            return

        arch = self.sim.archetypes[held_item.archetype_id]
        variant = arch.get_variant(held_item.rotation)
        stride = CELL_SIZE + CELL_GAP

        # Anchor floating coordinates to mouse cursor
        fx = int(self.mouse_pos.x) - (variant.width * stride) // 2
        fy = int(self.mouse_pos.y) - (variant.height * stride) // 2

        # Shadow
        for pair in variant.offsets:
            cx = fx + pair[0] * stride + 6
            cy = fy + pair[1] * stride + 6
            draw_rectangle(cx, cy, CELL_SIZE, CELL_SIZE, Color(0, 0, 0, 120))

        # Floating item body
        for pair in variant.offsets:
            cx = fx + pair[0] * stride
            cy = fy + pair[1] * stride
            draw_rectangle(cx, cy, CELL_SIZE, CELL_SIZE, arch.color_main)
            draw_rectangle_lines(cx, cy, CELL_SIZE, CELL_SIZE, arch.color_accent)

        # Center icon
        center_x = fx + (variant.width * stride) // 2
        center_y = fy + (variant.height * stride) // 2
        self._draw_item_glyph(arch.id, center_x, center_y)

    def _draw_item_glyph(self, archetype_id: int, cx: int, cy: int):
        """Renders procedural primitive icons for each equipment category."""
        glyph_col = Color(245, 250, 255, 240)

        if archetype_id == ITEM_CLAYMORE:
            # Sword blade + crossguard
            draw_line(cx, cy - 14, cx, cy + 12, glyph_col)
            draw_line(cx - 7, cy + 4, cx + 7, cy + 4, glyph_col)
        elif archetype_id == ITEM_BASTION_SHIELD:
            # Shield crest
            draw_rectangle_lines(cx - 10, cy - 12, 20, 24, glyph_col)
            draw_circle(cx, cy, 3, glyph_col)
        elif archetype_id == ITEM_WAR_AXE:
            # Axe shaft + blade arc
            draw_line(cx - 4, cy - 10, cx - 4, cy + 12, glyph_col)
            draw_circle_lines(cx + 3, cy - 6, 7, glyph_col)
        elif archetype_id == ITEM_WARHAMMER:
            # Hammerhead + shaft
            draw_rectangle(cx - 9, cy - 12, 18, 8, glyph_col)
            draw_line(cx, cy - 4, cx, cy + 12, glyph_col)
        elif archetype_id == ITEM_KNIGHT_HELM:
            # Visor slit
            draw_rectangle(cx - 8, cy - 6, 16, 4, glyph_col)
            draw_circle_lines(cx, cy - 2, 9, glyph_col)
        elif archetype_id == ITEM_SHADOW_DIRK:
            # Short blade
            draw_line(cx, cy - 8, cx, cy + 8, glyph_col)
            draw_circle(cx, cy + 8, 2, glyph_col)
        elif archetype_id == ITEM_POTION:
            # Flask
            draw_circle(cx, cy + 2, 7, glyph_col)
            draw_rectangle(cx - 2, cy - 8, 4, 6, glyph_col)
        elif archetype_id == ITEM_MANA_GEM:
            # Diamond
            draw_line(cx, cy - 8, cx + 7, cy, glyph_col)
            draw_line(cx + 7, cy, cx, cy + 8, glyph_col)
            draw_line(cx, cy + 8, cx - 7, cy, glyph_col)
            draw_line(cx - 7, cy, cx, cy - 8, glyph_col)
        elif archetype_id == ITEM_COSMIC_RELIC:
            # Star cross
            draw_line(cx - 8, cy, cx + 8, cy, glyph_col)
            draw_line(cx, cy - 8, cx, cy + 8, glyph_col)
            draw_circle(cx, cy, 3, glyph_col)
        elif archetype_id == ITEM_UTILITY_BELT:
            # Belt strap + buckle
            draw_line(cx - 12, cy, cx + 12, cy, glyph_col)
            draw_rectangle_lines(cx - 5, cy - 4, 10, 8, glyph_col)

    def _draw_stats_and_synergy_panel(self):
        """Displays total equipment stats, value, and active adjacency bonuses."""
        draw_rectangle(STATS_PANEL_X, STATS_PANEL_Y, STATS_PANEL_W, STATS_PANEL_H, COLOR_PANEL_BG)
        draw_rectangle_lines(STATS_PANEL_X, STATS_PANEL_Y, STATS_PANEL_W, STATS_PANEL_H, COLOR_PANEL_BORDER)

        draw_rectangle(STATS_PANEL_X, STATS_PANEL_Y, STATS_PANEL_W, 28, Color(22, 28, 44, 255))
        draw_text("BACKPACK EQUIPMENT STATS & SYNERGY PIPELINE", STATS_PANEL_X + 14, STATS_PANEL_Y + 7, 13, COLOR_ACCENT_GOLD)

        y = STATS_PANEL_Y + 40

        # Stats Column 1
        draw_text(f"ATTACK POWER  : {self.sim.total_atk} ATK", STATS_PANEL_X + 20, y, 14, COLOR_ACCENT_RED)
        draw_text(f"ARMOR DEFENSE : {self.sim.total_def} DEF", STATS_PANEL_X + 20, y + 22, 14, COLOR_ACCENT_CYAN)
        draw_text(f"HEALING POWER : +{self.sim.total_heal} HP", STATS_PANEL_X + 20, y + 44, 14, COLOR_ACCENT_GREEN)

        # Stats Column 2
        draw_text(f"MANA CAPACITY : +{self.sim.total_mana} MP", STATS_PANEL_X + 250, y, 14, Color(160, 200, 255, 255))
        draw_text(f"NET GOLD VALUE: {self.sim.total_gold} Gold", STATS_PANEL_X + 250, y + 22, 14, COLOR_ACCENT_GOLD)
        draw_text(f"PACKED ITEMS  : {len(self.sim.backpack.items)} items", STATS_PANEL_X + 250, y + 44, 14, COLOR_TEXT_MAIN)

        # Adjacency Synergies Box (Backpack Hero Mechanics)
        box_x = STATS_PANEL_X + 460
        box_y = STATS_PANEL_Y + 36
        draw_rectangle(box_x, box_y, 218, 175, Color(14, 18, 28, 255))
        draw_rectangle_lines(box_x, box_y, 218, 175, COLOR_PANEL_BORDER)
        draw_text("Adjacency Synergies:", box_x + 10, box_y + 8, 12, COLOR_ACCENT_CYAN)

        sy = box_y + 26
        if len(self.sim.active_synergies) > 0:
            for syn in self.sim.active_synergies:
                draw_text(f"• {syn}", box_x + 10, sy, 11, COLOR_ACCENT_GREEN)
                sy += 16
        else:
            draw_text("No adjacent synergies.", box_x + 10, sy, 11, COLOR_TEXT_DIM)
            draw_text("Place matching gear", box_x + 10, sy + 16, 11, COLOR_TEXT_DIM)
            draw_text("adjacent in the grid!", box_x + 10, sy + 32, 11, COLOR_TEXT_DIM)

    def _draw_controls_footer(self):
        """Renders input reminders at the bottom of the screen."""
        foot_y = STATS_PANEL_Y + 125
        draw_text("CONTROLS:", STATS_PANEL_X + 20, foot_y, 12, COLOR_ACCENT_GOLD)
        draw_text("• [LMB / Space / Gamepad A]  : Pick Up / Place / Swap", STATS_PANEL_X + 20, foot_y + 18, 11, COLOR_TEXT_MAIN)
        draw_text("• [R / Wheel / Gamepad X/RB] : Rotate 90° Clockwise", STATS_PANEL_X + 20, foot_y + 34, 11, COLOR_TEXT_MAIN)
        draw_text("• [RMB / Esc / Gamepad B]    : Cancel & Return to Origin", STATS_PANEL_X + 20, foot_y + 50, 11, COLOR_TEXT_MAIN)

        draw_text("• [P / Gamepad Y]  : Auto-Pack Heuristic", STATS_PANEL_X + 250, foot_y + 18, 11, COLOR_ACCENT_CYAN)
        draw_text("• [N / Gamepad R3] : Spawn Random Loot", STATS_PANEL_X + 250, foot_y + 34, 11, COLOR_ACCENT_GREEN)
        draw_text("• [F1 / Gamepad LB]: Toggle Strict Collision", STATS_PANEL_X + 250, foot_y + 50, 11, COLOR_ACCENT_GOLD)

    def _draw_feedback_banner(self):
        """Displays transient top-center confirmation notifications."""
        alpha = min(1.0, self.sim.banner_timer)
        col_alpha = max(0, min(255, int(255 * alpha)))
        bg_col = Color(24, 32, 50, col_alpha)
        border_col = Color(70, 140, 220, col_alpha)
        text_col = Color(240, 245, 255, col_alpha)

        bw = 640
        bh = 30
        bx = (SCREEN_WIDTH - bw) // 2
        by = 58
        draw_rectangle(bx, by, bw, bh, bg_col)
        draw_rectangle_lines(bx, by, bw, bh, border_col)
        draw_text(self.sim.feedback_banner, bx + 14, by + 8, 13, text_col)

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
    TetrisBackpackGame().run(smoke_test=is_smoke)

