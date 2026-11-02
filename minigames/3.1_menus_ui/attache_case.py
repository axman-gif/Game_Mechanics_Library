# -*- coding: utf-8 -*-
"""
Attaché Case - Resident Evil Grid Inventory Architecture & Item Combination
==========================================================================
Section          : 3.1 Menus & UI
Pattern Category : Menus & User Interface, Spatial Inventory Management
Dimension        : 2D

Problem Solved:
  Linear list inventories in action and survival horror games lack spatial management,
  tactile weight, and immediate visual recognition. Players spend excessive time scrolling
  through text lists instead of judging their supplies at a glance. Furthermore, naive
  inventory implementations tightly couple UI dragging with item storage, causing item
  duplication bugs, lost items on cancel, and convoluted multi-item combination edge cases.
  The Grid Inventory pattern solves this by separating storage into a fixed-capacity 2D
  cell array, managing discrete cursor navigation, decoupled hand-slot state machines, and
  a declarative pair-combination recipe engine.

How the Pattern Works:
  1. Discrete 2D Cell Matrix (Fixed Capacity Storage):
     The inventory briefcase is modeled as a 2D matrix of W x H discrete cells (e.g. 8x5 = 40).
     In C++, this maps to a flat array:
       ItemSlot slots[GRID_COLS * GRID_ROWS];
     accessed via flat index:
       index = row * GRID_COLS + col;
  2. Decoupled Hand Slot State Machine:
     Picking up an item removes it from its origin slot and places it in a temporary
     floating HandSlot (`hand_item`). Releasing onto an empty cell commits the item;
     releasing onto an occupied cell triggers either:
       - Recipe Engine check (if combinable -> craft result).
       - Slot Swap (exchange hand item with target cell item).
       - Slot Reject (bounce back to origin cell with error feedback).
  3. Declarative Pair-Combination Engine:
     Crafting recipes are declared as unordered pairs of Item IDs mapping to result items:
       (Green Herb + Green Herb) -> Mixed Herb (G+G)
       (Green Herb + Red Herb)   -> Mixed Herb (G+R) [Full Heal]
       (Green Herb + Yellow Herb)-> Mixed Herb (G+Y) [Heal + Max HP Up]
       (Handgun Ammo + Handgun)  -> Reload magazine
  4. Item Examine Rig (Procedural 3D Wireframe Inspection):
     Selecting an item opens an inspect modal rendering a real-time rotating 3D wireframe
     mesh of the item (pot, ammo box, firearm silhouette) with lore, stats, and dimensions.
  5. ECG Condition Monitor (Resident Evil Vital Sign Feedback):
     Tracks player health (FINE / CAUTION / DANGER) with an animated electrocardiogram
     waveform reacting in real time to healing items and test damage.

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - WASD / Arrow Keys / Left Stick / D-Pad : Move 2D Grid Cursor
  - Mouse Move / Hover                     : Direct Point & Hover selection
  - Enter / Space / Gamepad A              : Pick Up Item / Place / Swap
  - C / Gamepad X                          : Combine with Target Slot
  - E / Gamepad Y                          : Examine Item (3D Wireframe Inspection)
  - U / Gamepad B                          : Use / Consume Item (Heal / Reload)
  - K / Gamepad Right Stick Click          : Take Test Damage (Tests ECG & Healing)
  - [Tab] / Gamepad View (Select)          : Toggle X-Ray Telemetry & Memory Matrix
  - [F1]  / Gamepad LB                     : Toggle Drop Mode: [Swap] vs [Reject]
  - [F2]  / Gamepad RB                     : Toggle Recipe Combinable Glow Highlights
  - [Ctrl +/-]                             : Increase / Decrease UI Font Size
  - [F11]                                  : Toggle Fullscreen
  - [R]   / Gamepad Start                  : Reset Case to Default Supplies
"""

import sys
import os
import math
import random

# 1. Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# 2. Add repository root to search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# 3. Mandatory Raylib & modular workspace imports
from pyray import *
from assets import *
from utils import *

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WINDOW_TITLE = "Attaché Case - Resident Evil Grid Inventory (Raylib Pattern Lab)"

# Grid Dimensions
GRID_COLS = 8
GRID_ROWS = 5
TOTAL_CELLS = GRID_COLS * GRID_ROWS
CELL_SIZE = 76
CELL_GAP = 6

# Briefcase Layout
CASE_X = 64
CASE_Y = 110
CASE_WIDTH = GRID_COLS * CELL_SIZE + (GRID_COLS + 1) * CELL_GAP
CASE_HEIGHT = GRID_ROWS * CELL_SIZE + (GRID_ROWS + 1) * CELL_GAP

# Color Palette
COLOR_BG_DARK           = Color(10, 13, 20, 255)
COLOR_CASE_METAL_OUTER  = Color(42, 48, 62, 255)
COLOR_CASE_METAL_INNER  = Color(20, 24, 34, 255)
COLOR_CASE_RIVET        = Color(80, 92, 116, 255)
COLOR_CELL_EMPTY        = Color(14, 18, 26, 255)
COLOR_CELL_BORDER       = Color(32, 42, 60, 255)
COLOR_CELL_HOVER        = Color(60, 85, 125, 255)
COLOR_CELL_COMBINABLE   = Color(240, 200, 50, 255)
COLOR_TEXT_MAIN         = Color(230, 240, 255, 255)
COLOR_TEXT_DIM          = Color(130, 150, 180, 255)
COLOR_ACCENT_CYAN       = Color(0, 225, 255, 255)
COLOR_ACCENT_GOLD       = Color(255, 210, 60, 255)
COLOR_ACCENT_GREEN      = Color(60, 240, 120, 255)
COLOR_ACCENT_RED        = Color(255, 70, 70, 255)

# Item ID Constants (Equivalent to C++ enum ItemID)
ITEM_NONE             = 0
ITEM_GREEN_HERB       = 1
ITEM_RED_HERB         = 2
ITEM_YELLOW_HERB      = 3
ITEM_MIXED_HERB_GG    = 4
ITEM_MIXED_HERB_GR    = 5
ITEM_MIXED_HERB_GY    = 6
ITEM_MIXED_HERB_GGG   = 7
ITEM_MIXED_HERB_GRY   = 8
ITEM_FIRST_AID_SPRAY  = 9
ITEM_HANDGUN          = 10
ITEM_HANDGUN_AMMO     = 11
ITEM_SHOTGUN          = 12
ITEM_SHOTGUN_SHELLS   = 13
ITEM_COMBAT_KNIFE     = 14
ITEM_GOLD_EGG         = 15

# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATION (GRID INVENTORY & COMBINE ENGINE)
# ==============================================================================

class ItemDefinition:
    """
    Static blueprint metadata for an item archetype.
    C++ Equivalent:
      struct ItemDefinition {
          int id;
          const char* name;
          const char* category;
          int max_stack;
          int heal_amount;
          int max_hp_bonus;
          int ammo_capacity;
          const char* description;
          Color color_badge;
      };
    """
    def __init__(self, item_id: int, name: str, category: str, max_stack: int,
                 heal_amount: int, max_hp_bonus: int, ammo_capacity: int,
                 description: str, color_badge: Color):
        self.id = item_id
        self.name = name
        self.category = category
        self.max_stack = max_stack
        self.heal_amount = heal_amount
        self.max_hp_bonus = max_hp_bonus
        self.ammo_capacity = ammo_capacity
        self.description = description
        self.color_badge = color_badge


class ItemInstance:
    """
    Dynamic state of a physical item inhabiting a grid slot or hand slot.
    C++ Equivalent:
      struct ItemInstance {
          int def_id;
          int count;
          int current_ammo;
          bool is_examined;
      };
    """
    def __init__(self, def_id: int, count: int = 1, current_ammo: int = 0):
        self.def_id = def_id
        self.count = count
        self.current_ammo = current_ammo

    def clone(self):
        """Creates an independent copy for swap/undo buffers."""
        copy_inst = ItemInstance(self.def_id, self.count, self.current_ammo)
        return copy_inst


class CombineRecipe:
    """
    Declarative pair combination mapping item_a + item_b -> result.
    C++ Equivalent:
      struct CombineRecipe {
          int item_a;
          int item_b;
          int result_id;
          const char* result_name;
      };
    """
    def __init__(self, item_a: int, item_b: int, result_id: int, result_name: str):
        self.item_a = item_a
        self.item_b = item_b
        self.result_id = result_id
        self.result_name = result_name

    def matches(self, id_1: int, id_2: int) -> bool:
        """Symmetric matching: order does not matter (A+B == B+A)."""
        match_direct = (self.item_a == id_1 and self.item_b == id_2)
        match_reverse = (self.item_a == id_2 and self.item_b == id_1)
        return match_direct or match_reverse


class RecipeDatabase:
    """
    Global table of item combination rules.
    Decoupled from inventory rendering and slot storage.
    """
    def __init__(self):
        self.recipes = []
        # Herb Combinations (Classic RE4 Alchemy)
        self.recipes.append(CombineRecipe(ITEM_GREEN_HERB, ITEM_GREEN_HERB, ITEM_MIXED_HERB_GG, "Mixed Herb (G+G)"))
        self.recipes.append(CombineRecipe(ITEM_GREEN_HERB, ITEM_RED_HERB, ITEM_MIXED_HERB_GR, "Mixed Herb (G+R)"))
        self.recipes.append(CombineRecipe(ITEM_GREEN_HERB, ITEM_YELLOW_HERB, ITEM_MIXED_HERB_GY, "Mixed Herb (G+Y)"))
        self.recipes.append(CombineRecipe(ITEM_MIXED_HERB_GG, ITEM_GREEN_HERB, ITEM_MIXED_HERB_GGG, "Mixed Herb (G+G+G)"))
        self.recipes.append(CombineRecipe(ITEM_MIXED_HERB_GR, ITEM_YELLOW_HERB, ITEM_MIXED_HERB_GRY, "Mixed Herb (G+R+Y)"))

    def find_recipe(self, id_1: int, id_2: int):
        """Returns matching CombineRecipe or None if items cannot combine."""
        for recipe in self.recipes:
            if recipe.matches(id_1, id_2):
                return recipe
        return None


class GridInventory:
    """
    2D Matrix storage representing the attaché case interior.
    C++ Equivalent:
      class GridInventory {
          ItemInstance slots[GRID_ROWS * GRID_COLS];
          ItemInstance* hand_slot;
          int hand_origin_index;
      };
    """
    def __init__(self, cols: int, rows: int):
        self.cols = cols
        self.rows = rows
        self.total_cells = cols * rows
        # Fixed capacity array (pre-allocated with None)
        self.slots = []
        for _ in range(self.total_cells):
            self.slots.append(None)

        # Hand Slot (floating dragged or held item)
        self.hand_item = None
        self.hand_origin_idx = -1

    def to_index(self, col: int, row: int) -> int:
        """Maps 2D matrix coordinates (col, row) to 1D flat index."""
        return row * self.cols + col

    def to_coords(self, index: int):
        """Maps 1D flat index back to (col, row)."""
        col = index % self.cols
        row = index // self.cols
        return col, row

    def get_slot(self, col: int, row: int):
        """Safely fetches item at grid cell, or None if empty or out of bounds."""
        if col < 0 or col >= self.cols or row < 0 or row >= self.rows:
            return None
        idx = self.to_index(col, row)
        return self.slots[idx]

    def set_slot(self, col: int, row: int, item: ItemInstance):
        """Assigns item to grid cell."""
        if 0 <= col < self.cols and 0 <= row < self.rows:
            idx = self.to_index(col, row)
            self.slots[idx] = item

    def pick_up(self, col: int, row: int) -> bool:
        """Picks up an item from cell (col, row) into hand slot."""
        if self.hand_item is not None:
            return False  # Hand is already full
        idx = self.to_index(col, row)
        item = self.slots[idx]
        if item is None:
            return False
        self.hand_item = item
        self.hand_origin_idx = idx
        self.slots[idx] = None
        return True

    def cancel_hand(self):
        """Returns hand item to its original origin slot if space exists."""
        if self.hand_item is None:
            return
        if 0 <= self.hand_origin_idx < self.total_cells:
            if self.slots[self.hand_origin_idx] is None:
                self.slots[self.hand_origin_idx] = self.hand_item
                self.hand_item = None
                self.hand_origin_idx = -1
                return
        # Origin occupied: find first available free cell
        for i in range(self.total_cells):
            if self.slots[i] is None:
                self.slots[i] = self.hand_item
                self.hand_item = None
                self.hand_origin_idx = -1
                return

    def place_or_swap(self, col: int, row: int, allow_swap: bool, recipe_db: RecipeDatabase, registry) -> str:
        """
        Attempts to deposit hand item into cell (col, row).
        Returns action result token: 'placed', 'swapped', 'combined', 'reloaded', 'rejected'.
        """
        if self.hand_item is None:
            return "none"
        if col < 0 or col >= self.cols or row < 0 or row >= self.rows:
            return "rejected"

        target_idx = self.to_index(col, row)
        target_item = self.slots[target_idx]

        # Case 1: Empty target slot -> simple place
        if target_item is None:
            self.slots[target_idx] = self.hand_item
            self.hand_item = None
            self.hand_origin_idx = -1
            return "placed"

        # Case 2: Target slot occupied -> Check for firearm reload
        # Handgun + Handgun Ammo
        is_gun_and_ammo = (
            (self.hand_item.def_id == ITEM_HANDGUN_AMMO and target_item.def_id == ITEM_HANDGUN) or
            (self.hand_item.def_id == ITEM_HANDGUN and target_item.def_id == ITEM_HANDGUN_AMMO)
        )
        if is_gun_and_ammo:
            gun = target_item if target_item.def_id == ITEM_HANDGUN else self.hand_item
            ammo = self.hand_item if target_item.def_id == ITEM_HANDGUN else target_item
            gun_def = registry[ITEM_HANDGUN]
            needed = gun_def.ammo_capacity - gun.current_ammo
            if needed > 0 and ammo.count > 0:
                transfer = min(needed, ammo.count)
                gun.current_ammo += transfer
                ammo.count -= transfer
                if ammo.count <= 0:
                    if self.hand_item == ammo:
                        self.hand_item = None
                        self.hand_origin_idx = -1
                    else:
                        self.slots[target_idx] = self.hand_item
                        self.hand_item = None
                        self.hand_origin_idx = -1
                return "reloaded"

        # Shotgun + Shotgun Shells
        is_shotgun_and_shells = (
            (self.hand_item.def_id == ITEM_SHOTGUN_SHELLS and target_item.def_id == ITEM_SHOTGUN) or
            (self.hand_item.def_id == ITEM_SHOTGUN and target_item.def_id == ITEM_SHOTGUN_SHELLS)
        )
        if is_shotgun_and_shells:
            shotgun = target_item if target_item.def_id == ITEM_SHOTGUN else self.hand_item
            shells = self.hand_item if target_item.def_id == ITEM_SHOTGUN else target_item
            sg_def = registry[ITEM_SHOTGUN]
            needed = sg_def.ammo_capacity - shotgun.current_ammo
            if needed > 0 and shells.count > 0:
                transfer = min(needed, shells.count)
                shotgun.current_ammo += transfer
                shells.count -= transfer
                if shells.count <= 0:
                    if self.hand_item == shells:
                        self.hand_item = None
                        self.hand_origin_idx = -1
                    else:
                        self.slots[target_idx] = self.hand_item
                        self.hand_item = None
                        self.hand_origin_idx = -1
                return "reloaded"

        # Case 3: Target slot occupied -> Check for Alchemy Recipe Combination
        recipe = recipe_db.find_recipe(self.hand_item.def_id, target_item.def_id)
        if recipe is not None:
            # Successfully crafted new combined item
            new_item = ItemInstance(recipe.result_id, count=1)
            self.slots[target_idx] = new_item
            self.hand_item = None
            self.hand_origin_idx = -1
            return "combined"

        # Case 4: Target occupied with stackable identical item
        if self.hand_item.def_id == target_item.def_id:
            item_def = registry[self.hand_item.def_id]
            if item_def.max_stack > 1 and target_item.count < item_def.max_stack:
                space = item_def.max_stack - target_item.count
                transfer = min(space, self.hand_item.count)
                target_item.count += transfer
                self.hand_item.count -= transfer
                if self.hand_item.count <= 0:
                    self.hand_item = None
                    self.hand_origin_idx = -1
                return "placed"

        # Case 5: Target slot occupied and not combinable
        if allow_swap:
            # Swap hand item with target item
            temp = target_item
            self.slots[target_idx] = self.hand_item
            self.hand_item = temp
            self.hand_origin_idx = target_idx
            return "swapped"
        else:
            return "rejected"


# ==============================================================================
# BLOCK 2: WORLD SIMULATION & ENTITIES (ECG, INSPECTION, AUDIO)
# ==============================================================================

class ECGMonitor:
    """
    Resident Evil vital sign electrocardiogram monitor.
    Simulates a running oscilloscope heartbeat pulse.
    """
    def __init__(self):
        self.time = 0.0
        self.buffer = []
        self.buffer_size = 120
        for _ in range(self.buffer_size):
            self.buffer.append(0.0)

    def update(self, dt: float, condition: str):
        self.time += dt
        speed = 4.0 if condition == "DANGER" else (2.8 if condition == "CAUTION" else 2.0)
        t = (self.time * speed) % (2.0 * math.pi)

        # Heartbeat spike simulation (P-Q-R-S-T wave)
        pulse = 0.0
        if 1.0 <= t <= 1.4:
            phase = (t - 1.0) / 0.4
            pulse = math.sin(phase * math.pi * 2.0) * 0.25
        elif 1.6 <= t <= 1.8:
            # Sharp R peak
            phase = (t - 1.6) / 0.2
            pulse = math.sin(phase * math.pi) * 1.0
        elif 1.85 <= t <= 2.1:
            phase = (t - 1.85) / 0.25
            pulse = -math.sin(phase * math.pi) * 0.35

        # Shift buffer
        self.buffer.pop(0)
        self.buffer.append(pulse)

    def get_color(self, condition: str) -> Color:
        if condition == "DANGER":
            return COLOR_ACCENT_RED
        elif condition == "CAUTION":
            return COLOR_ACCENT_GOLD
        else:
            return COLOR_ACCENT_GREEN


class CharacterCondition:
    """
    Player health status and vitals pipeline.
    """
    def __init__(self):
        self.max_hp = 100
        self.hp = 65  # Starts in Caution to demonstrate healing

    def get_status_label(self) -> str:
        ratio = self.hp / float(self.max_hp)
        if ratio <= 0.25:
            return "DANGER"
        elif ratio <= 0.65:
            return "CAUTION"
        else:
            return "FINE"

    def heal(self, amount: int, max_hp_bonus: int = 0):
        self.max_hp += max_hp_bonus
        self.hp = min(self.max_hp, self.hp + amount)

    def damage(self, amount: int):
        self.hp = max(1, self.hp - amount)


# Item Database Registry Builder
def build_item_registry():
    reg = {}
    reg[ITEM_GREEN_HERB] = ItemDefinition(
        ITEM_GREEN_HERB, "Green Herb", "Herb / Recovery", 1, 30, 0, 0,
        "A medicinal herb native to the Arklay Mountains.\nRestores small amount of health (+30 HP).",
        Color(40, 210, 80, 255)
    )
    reg[ITEM_RED_HERB] = ItemDefinition(
        ITEM_RED_HERB, "Red Herb", "Herb / Catalyst", 1, 0, 0, 0,
        "A rare regional herb with potent alkaloid compounds.\nHas no effect alone. Combine with Green Herb.",
        Color(235, 50, 50, 255)
    )
    reg[ITEM_YELLOW_HERB] = ItemDefinition(
        ITEM_YELLOW_HERB, "Yellow Herb", "Herb / Tonic", 1, 0, 15, 0,
        "A nourishing herb found in Iberian valleys.\nCombine with Green Herb to boost maximum health.",
        Color(240, 210, 40, 255)
    )
    reg[ITEM_MIXED_HERB_GG] = ItemDefinition(
        ITEM_MIXED_HERB_GG, "Mixed Herb (G+G)", "Herbal Medicine", 1, 65, 0, 0,
        "Refined mixture of two Green Herbs.\nRestores moderate amount of health (+65 HP).",
        Color(70, 230, 100, 255)
    )
    reg[ITEM_MIXED_HERB_GR] = ItemDefinition(
        ITEM_MIXED_HERB_GR, "Mixed Herb (G+R)", "Herbal Medicine", 1, 999, 0, 0,
        "Potent elixir of Green and Red Herbs.\nCompletely restores all health (100% Full Heal).",
        Color(220, 110, 80, 255)
    )
    reg[ITEM_MIXED_HERB_GY] = ItemDefinition(
        ITEM_MIXED_HERB_GY, "Mixed Herb (G+Y)", "Herbal Medicine", 1, 35, 15, 0,
        "Nutritious blend of Green and Yellow Herbs.\nRestores +35 HP and permanently boosts Max HP (+15).",
        Color(190, 230, 60, 255)
    )
    reg[ITEM_MIXED_HERB_GGG] = ItemDefinition(
        ITEM_MIXED_HERB_GGG, "Mixed Herb (G+G+G)", "Herbal Medicine", 1, 999, 0, 0,
        "Concentrated triple green distillation.\nCompletely restores all health (100% Full Heal).",
        Color(90, 255, 130, 255)
    )
    reg[ITEM_MIXED_HERB_GRY] = ItemDefinition(
        ITEM_MIXED_HERB_GRY, "Mixed Herb (G+R+Y)", "Miracle Medicine", 1, 999, 25, 0,
        "The ultimate apothecary mixture.\nFull Heal (100%) and major permanent Max HP bonus (+25).",
        Color(255, 235, 90, 255)
    )
    reg[ITEM_FIRST_AID_SPRAY] = ItemDefinition(
        ITEM_FIRST_AID_SPRAY, "First Aid Spray", "Medical Supply", 1, 999, 0, 0,
        "Standardized medical aerosol compound.\nInstantly and fully restores player health to 100%.",
        Color(240, 240, 250, 255)
    )
    reg[ITEM_HANDGUN] = ItemDefinition(
        ITEM_HANDGUN, "Handgun (Silver Ghost)", "Handgun / 9mm", 1, 0, 0, 15,
        "Custom 9mm service pistol engineered by Kendo.\nPrecision accuracy and crisp ergonomic handling.",
        Color(160, 180, 210, 255)
    )
    reg[ITEM_HANDGUN_AMMO] = ItemDefinition(
        ITEM_HANDGUN_AMMO, "Handgun Ammo", "Ammunition / 9mm", 50, 0, 0, 0,
        "Standard 9x19mm Parabellum hollow-point rounds.\nCombine with Handgun to reload the magazine.",
        Color(255, 190, 60, 255)
    )
    reg[ITEM_SHOTGUN] = ItemDefinition(
        ITEM_SHOTGUN, "Shotgun (W-870)", "Shotgun / 12 Gauge", 1, 0, 0, 8,
        "Pump-action 12-gauge tactical shotgun.\nDevastating stopping power in tight corridor breaches.",
        Color(180, 150, 120, 255)
    )
    reg[ITEM_SHOTGUN_SHELLS] = ItemDefinition(
        ITEM_SHOTGUN_SHELLS, "Shotgun Shells", "Ammunition / 12GA", 20, 0, 0, 0,
        "Heavy red plastic 12-gauge 00 buckshot shells.\nCombine with Shotgun to reload the chamber.",
        Color(230, 70, 70, 255)
    )
    reg[ITEM_COMBAT_KNIFE] = ItemDefinition(
        ITEM_COMBAT_KNIFE, "Combat Knife", "Melee Weapon", 1, 0, 0, 0,
        "High-carbon hardened steel survival blade.\nReliable close-quarters defense that never jams.",
        Color(170, 190, 205, 255)
    )
    reg[ITEM_GOLD_EGG] = ItemDefinition(
        ITEM_GOLD_EGG, "Golden Egg", "Delicacy / Cure", 1, 999, 0, 0,
        "An extremely rare, shimmering golden poultry egg.\nRestores full health and fetches a fortune at shops.",
        Color(255, 215, 0, 255)
    )
    return reg


# Procedural Icon Renderer for Attaché Case Grid Cells
def draw_item_icon(item_def: ItemDefinition, item_inst: ItemInstance, cx: int, cy: int, size: int):
    """
    Renders pure procedural geometric icons inside grid cells.
    No external sprites required.
    """
    half = size // 2
    item_id = item_def.id

    if item_id in (ITEM_GREEN_HERB, ITEM_RED_HERB, ITEM_YELLOW_HERB):
        # Herb Pot & Leaves
        pot_w = int(size * 0.44)
        pot_h = int(size * 0.28)
        pot_col = Color(85, 55, 35, 255)
        draw_rectangle(cx - pot_w // 2, cy + 4, pot_w, pot_h, pot_col)
        draw_rectangle_lines(cx - pot_w // 2, cy + 4, pot_w, pot_h, Color(40, 25, 15, 255))
        # Herb foliage
        leaf_col = item_def.color_badge
        draw_circle(cx, cy - 6, int(size * 0.22), leaf_col)
        draw_circle(cx - 9, cy - 1, int(size * 0.16), leaf_col)
        draw_circle(cx + 9, cy - 1, int(size * 0.16), leaf_col)

    elif item_id in (ITEM_MIXED_HERB_GG, ITEM_MIXED_HERB_GR, ITEM_MIXED_HERB_GY,
                     ITEM_MIXED_HERB_GGG, ITEM_MIXED_HERB_GRY):
        # Dual/Triple Herb Flask with Ribbon
        draw_circle(cx - 7, cy - 3, int(size * 0.20), item_def.color_badge)
        draw_circle(cx + 7, cy - 3, int(size * 0.20), Color(230, 80, 80, 255) if "R" in item_def.name else Color(240, 210, 40, 255))
        # Ribbon binding
        draw_rectangle(cx - 16, cy + 6, 32, 6, Color(220, 200, 160, 255))

    elif item_id == ITEM_FIRST_AID_SPRAY:
        # White Aerosol Canister
        can_w = int(size * 0.35)
        can_h = int(size * 0.60)
        draw_rectangle(cx - can_w // 2, cy - can_h // 2, can_w, can_h, Color(240, 240, 245, 255))
        draw_rectangle(cx - can_w // 2, cy - can_h // 2, can_w, 6, Color(50, 180, 90, 255))
        # Red Cross
        draw_rectangle(cx - 2, cy - 4, 4, 14, COLOR_ACCENT_RED)
        draw_rectangle(cx - 7, cy + 1, 14, 4, COLOR_ACCENT_RED)
        draw_rectangle_lines(cx - can_w // 2, cy - can_h // 2, can_w, can_h, Color(160, 170, 180, 255))

    elif item_id == ITEM_HANDGUN:
        # Silver Ghost Handgun silhouette
        # Slide
        draw_rectangle(cx - 18, cy - 8, 36, 10, Color(190, 205, 220, 255))
        # Frame & Grip
        draw_rectangle(cx - 10, cy + 2, 12, 18, Color(45, 48, 55, 255))
        draw_rectangle(cx - 16, cy - 2, 18, 6, Color(130, 140, 155, 255))
        # Trigger guard
        draw_rectangle_lines(cx - 4, cy + 3, 10, 8, Color(120, 130, 140, 255))

    elif item_id == ITEM_HANDGUN_AMMO:
        # Blue & Gold Ammo Box
        box_w = int(size * 0.52)
        box_h = int(size * 0.44)
        draw_rectangle(cx - box_w // 2, cy - box_h // 2, box_w, box_h, Color(35, 75, 145, 255))
        draw_rectangle(cx - box_w // 2, cy - box_h // 2, box_w, 8, COLOR_ACCENT_GOLD)
        draw_rectangle_lines(cx - box_w // 2, cy - box_h // 2, box_w, box_h, Color(20, 45, 90, 255))
        draw_text("9mm", cx - 12, cy - 1, 11, COLOR_TEXT_MAIN)

    elif item_id == ITEM_SHOTGUN:
        # Shotgun with long barrel and wooden stock
        draw_rectangle(cx - 24, cy - 5, 48, 6, Color(75, 80, 90, 255))
        draw_rectangle(cx - 24, cy + 1, 26, 4, Color(50, 55, 60, 255))
        draw_rectangle(cx + 8, cy - 3, 16, 12, Color(110, 65, 35, 255))

    elif item_id == ITEM_SHOTGUN_SHELLS:
        # Red Shells Box
        box_w = int(size * 0.52)
        box_h = int(size * 0.44)
        draw_rectangle(cx - box_w // 2, cy - box_h // 2, box_w, box_h, Color(185, 35, 35, 255))
        draw_rectangle(cx - box_w // 2, cy + box_h // 2 - 8, box_w, 8, Color(210, 175, 60, 255))
        draw_rectangle_lines(cx - box_w // 2, cy - box_h // 2, box_w, box_h, Color(100, 20, 20, 255))
        draw_text("12G", cx - 12, cy - 4, 11, COLOR_TEXT_MAIN)

    elif item_id == ITEM_COMBAT_KNIFE:
        # Steel Tactical Knife
        draw_line_ex(Vector2(float(cx - 16), float(cy + 12)), Vector2(float(cx + 16), float(cy - 12)), 4.0, Color(200, 215, 230, 255))
        draw_line_ex(Vector2(float(cx - 16), float(cy + 12)), Vector2(float(cx - 6), float(cy + 2)), 6.0, Color(40, 45, 55, 255))

    elif item_id == ITEM_GOLD_EGG:
        # Shimmering Gold Egg
        draw_circle(cx, cy, int(size * 0.28), Color(255, 215, 0, 255))
        draw_circle(cx - 3, cy - 3, int(size * 0.12), Color(255, 250, 160, 255))


# Procedural 3D Wireframe Inspect Mesh Renderer
def draw_3d_inspect_mesh(item_id: int, center_x: int, center_y: int, yaw: float, pitch: float):
    """
    Projects and rotates a 3D wireframe mesh in real-time.
    Demonstrates Resident Evil's classic item examine screen without external 3D models.
    """
    cos_y = math.cos(yaw)
    sin_y = math.sin(yaw)
    cos_p = math.cos(pitch)
    sin_p = math.sin(pitch)

    def project_pt(vx: float, vy: float, vz: float, scale: float = 75.0):
        # Rotate Yaw (around Y axis)
        rx1 = vx * cos_y - vz * sin_y
        rz1 = vx * sin_y + vz * cos_y
        # Rotate Pitch (around X axis)
        ry2 = vy * cos_p - rz1 * sin_p
        rz2 = vy * sin_p + rz1 * cos_p
        # Perspective projection
        fov = 300.0
        persp = fov / max(50.0, fov + rz2)
        sx = center_x + int(rx1 * scale * persp)
        sy = center_y + int(ry2 * scale * persp)
        return sx, sy

    mesh_col = Color(0, 225, 255, 220)

    # Box-like items (Ammo, Briefcase, First Aid)
    box_half_x = 0.8
    box_half_y = 0.9
    box_half_z = 0.5
    if item_id in (ITEM_HANDGUN_AMMO, ITEM_SHOTGUN_SHELLS):
        box_half_x, box_half_y, box_half_z = 0.9, 0.7, 0.6
    elif item_id == ITEM_HANDGUN:
        box_half_x, box_half_y, box_half_z = 1.3, 0.7, 0.25

    vertices = [
        (-box_half_x, -box_half_y, -box_half_z),
        ( box_half_x, -box_half_y, -box_half_z),
        ( box_half_x,  box_half_y, -box_half_z),
        (-box_half_x,  box_half_y, -box_half_z),
        (-box_half_x, -box_half_y,  box_half_z),
        ( box_half_x, -box_half_y,  box_half_z),
        ( box_half_x,  box_half_y,  box_half_z),
        (-box_half_x,  box_half_y,  box_half_z),
    ]

    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),
        (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7)
    ]

    # Draw wireframe edges
    for edge in edges:
        p1 = vertices[edge[0]]
        p2 = vertices[edge[1]]
        x1, y1 = project_pt(p1[0], p1[1], p1[2])
        x2, y2 = project_pt(p2[0], p2[1], p2[2])
        draw_line_ex(Vector2(float(x1), float(y1)), Vector2(float(x2), float(y2)), 2.0, mesh_col)

    # Corner nodes
    for v in vertices:
        vx, vy = project_pt(v[0], v[1], v[2])
        draw_circle(vx, vy, 3, Color(255, 255, 255, 255))


# ==============================================================================
# BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY ([Tab] & [F1] / [F2])
# ==============================================================================

def draw_xray_telemetry(inventory: GridInventory, registry, recipe_db: RecipeDatabase,
                        drop_mode_swap: bool, show_hints: bool, cursor_col: int, cursor_row: int):
    """
    Renders underlying grid memory buffer, bitmask occupancy, and craft graphs.
    """
    panel_w = 420
    panel_h = 600
    panel_x = SCREEN_WIDTH - panel_w - 20
    panel_y = 65

    draw_rectangle(panel_x, panel_y, panel_w, panel_h, Color(12, 16, 26, 245))
    draw_rectangle_lines(panel_x, panel_y, panel_w, panel_h, COLOR_ACCENT_CYAN)

    draw_text("X-RAY GRID INVENTORY TELEMETRY", panel_x + 16, panel_y + 14, 15, COLOR_ACCENT_CYAN)
    draw_line(panel_x + 16, panel_y + 36, panel_x + panel_w - 16, panel_y + 36, Color(50, 75, 110, 255))

    ty = panel_y + 46
    # Cursor Matrix Info
    draw_text(f"Grid Size: {inventory.cols}x{inventory.rows} ({inventory.total_cells} total memory slots)", panel_x + 16, ty, 13, COLOR_TEXT_MAIN)
    ty += 20
    cursor_idx = inventory.to_index(cursor_col, cursor_row)
    draw_text(f"Active Cursor: Col {cursor_col}, Row {cursor_row} (Index [{cursor_idx:02d}])", panel_x + 16, ty, 13, COLOR_ACCENT_GOLD)
    ty += 24

    # Drop Mode & Behavior Config
    mode_str = "SWAP ON COLLISION" if drop_mode_swap else "REJECT / SNAP BACK"
    mode_col = COLOR_ACCENT_GREEN if drop_mode_swap else COLOR_ACCENT_RED
    draw_text(f"[F1] Drop Mode: {mode_str}", panel_x + 16, ty, 13, mode_col)
    ty += 20
    hint_str = "ENABLED (Cyan/Gold Ring)" if show_hints else "DISABLED"
    draw_text(f"[F2] Recipe Hints: {hint_str}", panel_x + 16, ty, 13, COLOR_TEXT_DIM)
    ty += 26

    # Hand Slot Memory
    draw_text("HAND SLOT FLOATING STATE:", panel_x + 16, ty, 13, COLOR_ACCENT_CYAN)
    ty += 20
    if inventory.hand_item is not None:
        item_def = registry[inventory.hand_item.def_id]
        draw_text(f"Holding: {item_def.name} (x{inventory.hand_item.count})", panel_x + 24, ty, 13, COLOR_ACCENT_GOLD)
        ty += 18
        draw_text(f"Origin Cell: Index [{inventory.hand_origin_idx:02d}]", panel_x + 24, ty, 12, COLOR_TEXT_DIM)
    else:
        draw_text("Holding: [EMPTY / NULL_PTR]", panel_x + 24, ty, 13, Color(100, 120, 140, 255))
    ty += 28

    # Live Occupancy Bitmask Mini-Map
    draw_text("GRID OCCUPANCY MATRIX (Bitmask):", panel_x + 16, ty, 13, COLOR_ACCENT_CYAN)
    ty += 22
    cell_mini_w = 40
    cell_mini_h = 24
    grid_start_x = panel_x + 24
    for r in range(inventory.rows):
        for c in range(inventory.cols):
            idx = inventory.to_index(c, r)
            slot = inventory.slots[idx]
            bx = grid_start_x + c * (cell_mini_w + 3)
            by = ty + r * (cell_mini_h + 3)

            # Cell mini-rect
            is_active = (slot is not None)
            is_curs = (c == cursor_col and r == cursor_row)
            cell_bg = Color(30, 60, 100, 255) if is_active else Color(18, 24, 34, 255)
            draw_rectangle(bx, by, cell_mini_w, cell_mini_h, cell_bg)
            border_col = COLOR_ACCENT_GOLD if is_curs else Color(45, 60, 80, 255)
            draw_rectangle_lines(bx, by, cell_mini_w, cell_mini_h, border_col)

            # Mini text label (1 or 0)
            flag_str = f"#{slot.def_id:02d}" if is_active else "."
            txt_col = COLOR_TEXT_MAIN if is_active else Color(80, 95, 115, 255)
            draw_text(flag_str, bx + 6, by + 5, 11, txt_col)
    ty += inventory.rows * (cell_mini_h + 3) + 20

    # Recipe Database Matrix
    draw_text("REGISTERED COMBINATION RECIPES:", panel_x + 16, ty, 13, COLOR_ACCENT_CYAN)
    ty += 20
    for rec in recipe_db.recipes:
        name_a = registry[rec.item_a].name.split(" ")[0]
        name_b = registry[rec.item_b].name.split(" ")[0]
        draw_text(f"- {name_a} + {name_b} -> {rec.result_name}", panel_x + 20, ty, 11, COLOR_TEXT_DIM)
        ty += 16


# ==============================================================================
# BLOCK 4: MAIN GAME LOOP & AUTOMATED SMOKE TEST
# ==============================================================================

class PatternLabGame:
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()

        # Audio synthesizer
        self.sfx = SoundLibrary()
        self.sfx.init_defaults()

        # Database and Inventory
        self.registry = build_item_registry()
        self.recipe_db = RecipeDatabase()
        self.inventory = GridInventory(GRID_COLS, GRID_ROWS)

        # Character condition & ECG
        self.character = CharacterCondition()
        self.ecg = ECGMonitor()

        # Interaction State
        self.cursor_col = 0
        self.cursor_row = 0
        self.cursor_anim_x = float(CASE_X + CELL_GAP)
        self.cursor_anim_y = float(CASE_Y + CELL_GAP)

        # Pattern Toggles
        self.show_xray = True
        self.drop_mode_swap = True     # True: Swap on collision, False: Reject
        self.show_recipe_hints = True  # Highlights valid combinables when holding item

        # Examine Modal State
        self.is_examining = False
        self.examine_item_id = ITEM_NONE
        self.examine_yaw = 0.0
        self.examine_pitch = 0.35

        # Notification Toast
        self.toast_msg = "ATTACHÉ CASE READY"
        self.toast_timer = 3.0
        self.toast_color = COLOR_ACCENT_CYAN

        # Populate initial Resident Evil loadout
        self.populate_default_supplies()

    def populate_default_supplies(self):
        """Sets up a classic survival inventory layout with herbs and weapons."""
        for i in range(self.inventory.total_cells):
            self.inventory.slots[i] = None
        self.inventory.hand_item = None
        self.inventory.hand_origin_idx = -1

        # Handgun & Ammo
        self.inventory.set_slot(0, 0, ItemInstance(ITEM_HANDGUN, count=1, current_ammo=10))
        self.inventory.set_slot(1, 0, ItemInstance(ITEM_HANDGUN_AMMO, count=30))
        self.inventory.set_slot(2, 0, ItemInstance(ITEM_COMBAT_KNIFE, count=1))

        # Shotgun & Shells
        self.inventory.set_slot(0, 1, ItemInstance(ITEM_SHOTGUN, count=1, current_ammo=5))
        self.inventory.set_slot(1, 1, ItemInstance(ITEM_SHOTGUN_SHELLS, count=12))

        # Medical Herbs
        self.inventory.set_slot(0, 3, ItemInstance(ITEM_GREEN_HERB, count=1))
        self.inventory.set_slot(1, 3, ItemInstance(ITEM_GREEN_HERB, count=1))
        self.inventory.set_slot(2, 3, ItemInstance(ITEM_RED_HERB, count=1))
        self.inventory.set_slot(3, 3, ItemInstance(ITEM_YELLOW_HERB, count=1))

        # First Aid Spray & Golden Egg
        self.inventory.set_slot(4, 0, ItemInstance(ITEM_FIRST_AID_SPRAY, count=1))
        self.inventory.set_slot(5, 0, ItemInstance(ITEM_GOLD_EGG, count=1))

        self.character.hp = 55
        self.character.max_hp = 100

    def trigger_toast(self, text: str, color: Color = COLOR_ACCENT_CYAN):
        self.toast_msg = text
        self.toast_timer = 2.5
        self.toast_color = color

    def update(self):
        dt = min(get_frame_time(), 0.05)

        # Update ECG Monitor
        self.ecg.update(dt, self.character.get_status_label())

        # Update Toasts
        if self.toast_timer > 0.0:
            self.toast_timer -= dt

        # Global Hotkey Toggles
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
            self.sfx.play("click", 0.5)

        if is_dual_pattern_toggle_pressed():
            self.drop_mode_swap = not self.drop_mode_swap
            mode_label = "DROP: SWAP" if self.drop_mode_swap else "DROP: REJECT"
            self.trigger_toast(mode_label, COLOR_ACCENT_GREEN if self.drop_mode_swap else COLOR_ACCENT_RED)
            self.sfx.play("click", 0.6)

        if is_dual_secondary_toggle_pressed():
            self.show_recipe_hints = not self.show_recipe_hints
            hint_label = "RECIPE HINTS: ON" if self.show_recipe_hints else "RECIPE HINTS: OFF"
            self.trigger_toast(hint_label, COLOR_ACCENT_GOLD)
            self.sfx.play("click", 0.6)

        if is_dual_reset_pressed():
            self.populate_default_supplies()
            self.trigger_toast("BRIEFCASE RESET TO DEFAULT SUPPLIES", COLOR_ACCENT_CYAN)
            self.sfx.play("coin", 0.7)

        # Test Damage trigger [K] or Gamepad Right Stick Click
        if is_key_pressed(KEY_K) or is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_THUMB):
            self.character.damage(25)
            self.sfx.play("hurt", 0.7)
            self.trigger_toast(f"DAMAGE TAKEN! HP: {self.character.hp}/{self.character.max_hp}", COLOR_ACCENT_RED)

        # If in Examine Modal
        if self.is_examining:
            self.examine_yaw += dt * 0.8
            # Exit examine with E, Space, Enter, Esc, or Gamepad B/Y
            if is_key_pressed(KEY_ESCAPE) or is_key_pressed(KEY_E) or is_key_pressed(KEY_SPACE) or \
               is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_FACE_RIGHT) or \
               is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_FACE_UP):
                self.is_examining = False
                self.sfx.play("click", 0.5)
            return

        # 2D Grid Cursor Navigation (Discrete Arrow / D-Pad + Analog Left Stick)
        nav_x = 0
        nav_y = 0
        if is_key_pressed(KEY_RIGHT) or is_key_pressed(KEY_D) or is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_RIGHT):
            nav_x += 1
        if is_key_pressed(KEY_LEFT) or is_key_pressed(KEY_A) or is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_LEFT):
            nav_x -= 1
        if is_key_pressed(KEY_DOWN) or is_key_pressed(KEY_S) or is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_DOWN):
            nav_y += 1
        if is_key_pressed(KEY_UP) or is_key_pressed(KEY_W) or is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_UP):
            nav_y -= 1

        if nav_x != 0 or nav_y != 0:
            self.cursor_col = ((self.cursor_col + nav_x) % GRID_COLS + GRID_COLS) % GRID_COLS
            self.cursor_row = ((self.cursor_row + nav_y) % GRID_ROWS + GRID_ROWS) % GRID_ROWS
            self.sfx.play("click", 0.4)

        # Mouse direct hover selection
        mouse_pos = get_mouse_position()
        if (CASE_X <= mouse_pos.x <= CASE_X + CASE_WIDTH) and (CASE_Y <= mouse_pos.y <= CASE_Y + CASE_HEIGHT):
            rel_x = mouse_pos.x - (CASE_X + CELL_GAP)
            rel_y = mouse_pos.y - (CASE_Y + CELL_GAP)
            stride = CELL_SIZE + CELL_GAP
            m_col = int(rel_x // stride)
            m_row = int(rel_y // stride)
            if 0 <= m_col < GRID_COLS and 0 <= m_row < GRID_ROWS:
                if m_col != self.cursor_col or m_row != self.cursor_row:
                    self.cursor_col = m_col
                    self.cursor_row = m_row

        # Smooth Cursor Rig damping
        target_cx = CASE_X + CELL_GAP + self.cursor_col * (CELL_SIZE + CELL_GAP)
        target_cy = CASE_Y + CELL_GAP + self.cursor_row * (CELL_SIZE + CELL_GAP)
        self.cursor_anim_x = damp(self.cursor_anim_x, target_cx, 24.0, dt)
        self.cursor_anim_y = damp(self.cursor_anim_y, target_cy, 24.0, dt)

        # Interaction: Primary Action (Pick Up / Place / Swap)
        primary_press = is_dual_primary_fire_pressed() or is_mouse_button_pressed(MOUSE_BUTTON_LEFT)
        if primary_press:
            if self.inventory.hand_item is None:
                # Attempt Pick Up
                success = self.inventory.pick_up(self.cursor_col, self.cursor_row)
                if success:
                    self.sfx.play("hit", 0.5)
            else:
                # Attempt Place or Swap or Combine
                result = self.inventory.place_or_swap(
                    self.cursor_col, self.cursor_row,
                    self.drop_mode_swap, self.recipe_db, self.registry
                )
                if result == "placed":
                    self.sfx.play("hit", 0.6)
                elif result == "swapped":
                    self.sfx.play("click", 0.6)
                    self.trigger_toast("ITEMS SWAPPED", COLOR_ACCENT_CYAN)
                elif result == "combined":
                    self.sfx.play("coin", 0.8)
                    self.trigger_toast("HERBS COMBINED!", COLOR_ACCENT_GOLD)
                elif result == "reloaded":
                    self.sfx.play("powerup", 0.7)
                    self.trigger_toast("FIREARM RELOADED!", COLOR_ACCENT_GREEN)
                elif result == "rejected":
                    self.sfx.play("hurt", 0.5)
                    self.trigger_toast("SLOT OCCUPIED! DROP REJECTED", COLOR_ACCENT_RED)
                    # Snap back to origin
                    self.inventory.cancel_hand()

        # Interaction: Secondary Action (Combine explicitly with hand item)
        if is_key_pressed(KEY_C) or is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_FACE_LEFT):
            if self.inventory.hand_item is not None:
                target_slot = self.inventory.get_slot(self.cursor_col, self.cursor_row)
                if target_slot is not None:
                    result = self.inventory.place_or_swap(
                        self.cursor_col, self.cursor_row,
                        self.drop_mode_swap, self.recipe_db, self.registry
                    )
                    if result == "combined":
                        self.sfx.play("coin", 0.8)
                        self.trigger_toast("ALCHEMY CRAFT SUCCESSFUL!", COLOR_ACCENT_GOLD)
                    elif result == "reloaded":
                        self.sfx.play("powerup", 0.7)
                        self.trigger_toast("FIREARM RELOADED!", COLOR_ACCENT_GREEN)

        # Interaction: Use / Consume Item (U key or Gamepad B)
        if is_key_pressed(KEY_U) or is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_FACE_RIGHT):
            item = self.inventory.hand_item or self.inventory.get_slot(self.cursor_col, self.cursor_row)
            if item is not None:
                item_def = self.registry[item.def_id]
                if item_def.heal_amount > 0 or item_def.max_hp_bonus > 0:
                    self.character.heal(item_def.heal_amount, item_def.max_hp_bonus)
                    self.sfx.play("powerup", 0.8)
                    self.trigger_toast(f"USED {item_def.name}! HP RESTORED", COLOR_ACCENT_GREEN)
                    # Consume item
                    item.count -= 1
                    if item.count <= 0:
                        if self.inventory.hand_item == item:
                            self.inventory.hand_item = None
                            self.inventory.hand_origin_idx = -1
                        else:
                            self.inventory.set_slot(self.cursor_col, self.cursor_row, None)

        # Interaction: Examine Item (E key or Gamepad Y)
        if is_key_pressed(KEY_E) or is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_FACE_UP):
            item = self.inventory.hand_item or self.inventory.get_slot(self.cursor_col, self.cursor_row)
            if item is not None:
                self.is_examining = True
                self.examine_item_id = item.def_id
                self.examine_yaw = 0.0
                self.sfx.play("click", 0.6)

    def draw(self):
        begin_drawing()
        clear_background(COLOR_BG_DARK)

        # 1. Briefcase Outer Metallic Frame
        draw_rectangle(CASE_X - 12, CASE_Y - 12, CASE_WIDTH + 24, CASE_HEIGHT + 24, COLOR_CASE_METAL_OUTER)
        draw_rectangle(CASE_X, CASE_Y, CASE_WIDTH, CASE_HEIGHT, COLOR_CASE_METAL_INNER)
        draw_rectangle_lines(CASE_X - 12, CASE_Y - 12, CASE_WIDTH + 24, CASE_HEIGHT + 24, Color(80, 95, 120, 255))
        draw_rectangle_lines(CASE_X - 1, CASE_Y - 1, CASE_WIDTH + 2, CASE_HEIGHT + 2, Color(50, 65, 85, 255))

        # Metallic rivets on briefcase corners
        rivet_offsets = [
            (CASE_X - 6, CASE_Y - 6),
            (CASE_X + CASE_WIDTH + 6, CASE_Y - 6),
            (CASE_X - 6, CASE_Y + CASE_HEIGHT + 6),
            (CASE_X + CASE_WIDTH + 6, CASE_Y + CASE_HEIGHT + 6)
        ]
        for rx, ry in rivet_offsets:
            draw_circle(rx, ry, 4, COLOR_CASE_RIVET)
            draw_circle(rx - 1, ry - 1, 2, Color(160, 180, 210, 255))

        # Briefcase Header Label
        draw_text("TYPE-40 TACTICAL ATTACHÉ CASE", CASE_X + 16, CASE_Y - 32, 16, COLOR_TEXT_DIM)

        # 2. Draw 2D Grid Cells & Occupants
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                cx = CASE_X + CELL_GAP + c * (CELL_SIZE + CELL_GAP)
                cy = CASE_Y + CELL_GAP + r * (CELL_SIZE + CELL_GAP)

                # Cell velvet background
                draw_rectangle(cx, cy, CELL_SIZE, CELL_SIZE, COLOR_CELL_EMPTY)
                draw_rectangle_lines(cx, cy, CELL_SIZE, CELL_SIZE, COLOR_CELL_BORDER)

                # Check if this cell is combinable with current hand item (Recipe Hint feature)
                slot_item = self.inventory.get_slot(c, r)
                is_combinable = False
                if self.show_recipe_hints and self.inventory.hand_item is not None and slot_item is not None:
                    if self.recipe_db.find_recipe(self.inventory.hand_item.def_id, slot_item.def_id) is not None:
                        is_combinable = True
                    # Firearm reload match
                    elif (self.inventory.hand_item.def_id == ITEM_HANDGUN_AMMO and slot_item.def_id == ITEM_HANDGUN) or \
                         (self.inventory.hand_item.def_id == ITEM_SHOTGUN_SHELLS and slot_item.def_id == ITEM_SHOTGUN):
                        is_combinable = True

                if is_combinable:
                    pulse_alpha = int(140 + 100 * math.sin(get_time() * 8.0))
                    draw_rectangle_lines(cx, cy, CELL_SIZE, CELL_SIZE, Color(255, 215, 60, pulse_alpha))
                    draw_rectangle(cx + 2, cy + 2, CELL_SIZE - 4, CELL_SIZE - 4, Color(255, 215, 60, 30))

                # Draw Item in slot
                if slot_item is not None:
                    item_def = self.registry[slot_item.def_id]
                    draw_item_icon(item_def, slot_item, cx + CELL_SIZE // 2, cy + CELL_SIZE // 2, CELL_SIZE)

                    # Quantity or Ammo badge
                    if item_def.ammo_capacity > 0:
                        ammo_str = f"{slot_item.current_ammo}/{item_def.ammo_capacity}"
                        draw_text(ammo_str, cx + 6, cy + CELL_SIZE - 16, 11, COLOR_ACCENT_CYAN)
                    elif slot_item.count > 1:
                        draw_text(f"x{slot_item.count}", cx + CELL_SIZE - 24, cy + CELL_SIZE - 16, 12, COLOR_TEXT_MAIN)

        # 3. Damped Cursor Selection Border
        cur_ix = int(self.cursor_anim_x)
        cur_iy = int(self.cursor_anim_y)
        cursor_pulse = int(190 + 65 * math.sin(get_time() * 6.0))
        cursor_col = Color(0, 225, 255, cursor_pulse)
        draw_rectangle_lines(cur_ix - 2, cur_iy - 2, CELL_SIZE + 4, CELL_SIZE + 4, cursor_col)
        draw_rectangle_lines(cur_ix - 1, cur_iy - 1, CELL_SIZE + 2, CELL_SIZE + 2, COLOR_TEXT_MAIN)

        # 4. Floating Hand Slot Item (Follows cursor smoothly or mouse)
        if self.inventory.hand_item is not None:
            hand_def = self.registry[self.inventory.hand_item.def_id]
            hx = cur_ix + CELL_SIZE // 2
            hy = cur_iy + CELL_SIZE // 2
            # Glow shadow
            draw_circle(hx, hy, int(CELL_SIZE * 0.45), Color(0, 225, 255, 40))
            draw_item_icon(hand_def, self.inventory.hand_item, hx, hy, CELL_SIZE)
            draw_text("[HOLDING]", cur_ix + 6, cur_iy - 16, 11, COLOR_ACCENT_GOLD)

        # 5. Right Sidebar: ECG Heartbeat Monitor & Item Inspect Card
        side_x = CASE_X + CASE_WIDTH + 36
        side_y = CASE_Y - 12
        side_w = SCREEN_WIDTH - side_x - 36
        if self.show_xray:
            side_w = 480  # Keep clean layout

        # ECG Vital Monitor Box
        ecg_h = 130
        draw_rectangle(side_x, side_y, side_w, ecg_h, Color(16, 22, 34, 255))
        draw_rectangle_lines(side_x, side_y, side_w, ecg_h, Color(45, 60, 85, 255))

        cond_label = self.character.get_status_label()
        cond_color = self.ecg.get_color(cond_label)

        draw_text("VITAL SIGNS (ECG)", side_x + 14, side_y + 12, 12, COLOR_TEXT_DIM)
        draw_text(f"CONDITION: {cond_label}", side_x + side_w - 180, side_y + 10, 16, cond_color)
        draw_text(f"HP: {self.character.hp} / {self.character.max_hp}", side_x + 14, side_y + 32, 14, COLOR_TEXT_MAIN)

        # Draw Oscilloscope Heartbeat Graph
        graph_x = side_x + 14
        graph_y = side_y + 80
        graph_w = side_w - 28
        step = graph_w / float(self.ecg.buffer_size)
        for i in range(len(self.ecg.buffer) - 1):
            px1 = graph_x + int(i * step)
            py1 = graph_y - int(self.ecg.buffer[i] * 28.0)
            px2 = graph_x + int((i + 1) * step)
            py2 = graph_y - int(self.ecg.buffer[i + 1] * 28.0)
            draw_line_ex(Vector2(float(px1), float(py1)), Vector2(float(px2), float(py2)), 2.0, cond_color)

        # Selected Item Details Card
        info_y = side_y + ecg_h + 16
        info_h = 240
        draw_rectangle(side_x, info_y, side_w, info_h, Color(16, 22, 34, 255))
        draw_rectangle_lines(side_x, info_y, side_w, info_h, Color(45, 60, 85, 255))

        cur_item = self.inventory.hand_item or self.inventory.get_slot(self.cursor_col, self.cursor_row)
        if cur_item is not None:
            cur_def = self.registry[cur_item.def_id]
            draw_text("SELECTED ITEM", side_x + 14, info_y + 12, 12, COLOR_TEXT_DIM)
            draw_text(cur_def.name, side_x + 14, info_y + 30, 18, COLOR_TEXT_MAIN)
            draw_text(f"Class: {cur_def.category}", side_x + 14, info_y + 54, 13, cur_def.color_badge)

            # Details & Attributes
            ty = info_y + 80
            if cur_def.heal_amount > 0:
                draw_text(f"+ Restores {cur_def.heal_amount} HP", side_x + 14, ty, 13, COLOR_ACCENT_GREEN)
                ty += 18
            if cur_def.max_hp_bonus > 0:
                draw_text(f"+ Max Health Bonus: +{cur_def.max_hp_bonus} HP", side_x + 14, ty, 13, COLOR_ACCENT_GOLD)
                ty += 18
            if cur_def.ammo_capacity > 0:
                draw_text(f"+ Loaded: {cur_item.current_ammo} / {cur_def.ammo_capacity} Rounds", side_x + 14, ty, 13, COLOR_ACCENT_CYAN)
                ty += 18

            # Description (wrapped text)
            desc_lines = cur_def.description.split("\n")
            for line in desc_lines:
                draw_text(line, side_x + 14, ty, 12, COLOR_TEXT_DIM)
                ty += 16
        else:
            draw_text("EMPTY SLOT", side_x + 14, info_y + 12, 14, Color(100, 120, 140, 255))
            draw_text("Navigate with D-Pad/WASD/Mouse to inspect items.", side_x + 14, info_y + 36, 12, COLOR_TEXT_DIM)

        # Quick Control Help Box
        ctrl_y = info_y + info_h + 16
        ctrl_h = 100
        draw_rectangle(side_x, ctrl_y, side_w, ctrl_h, Color(14, 18, 28, 255))
        draw_rectangle_lines(side_x, ctrl_y, side_w, ctrl_h, Color(35, 45, 65, 255))
        draw_text("CONTROLS & SHORTCUTS", side_x + 14, ctrl_y + 10, 11, COLOR_ACCENT_CYAN)
        draw_text("[Enter / Space / Gamepad A] : Pick Up / Place / Swap Item", side_x + 14, ctrl_y + 28, 12, COLOR_TEXT_MAIN)
        draw_text("[C / Gamepad X]             : Combine with Target Cell", side_x + 14, ctrl_y + 44, 12, COLOR_TEXT_MAIN)
        draw_text("[E / Gamepad Y]             : Examine 3D Wireframe Mesh", side_x + 14, ctrl_y + 60, 12, COLOR_TEXT_MAIN)
        draw_text("[U / Gamepad B]             : Use / Consume Item", side_x + 14, ctrl_y + 76, 12, COLOR_ACCENT_GREEN)

        # 6. Toast Notification Banner
        if self.toast_timer > 0.0:
            toast_alpha = min(255, int(self.toast_timer * 200))
            draw_rectangle(CASE_X, SCREEN_HEIGHT - 54, CASE_WIDTH, 34, Color(14, 20, 32, toast_alpha))
            draw_rectangle_lines(CASE_X, SCREEN_HEIGHT - 54, CASE_WIDTH, 34, Color(self.toast_color.r, self.toast_color.g, self.toast_color.b, toast_alpha))
            draw_text(self.toast_msg, CASE_X + 16, SCREEN_HEIGHT - 44, 14, Color(self.toast_color.r, self.toast_color.g, self.toast_color.b, toast_alpha))

        # 7. Item Examine Modal (Resident Evil Inspect View)
        if self.is_examining:
            # Full-screen dark tint
            draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, Color(0, 0, 0, 210))
            modal_w = 640
            modal_h = 480
            modal_x = (SCREEN_WIDTH - modal_w) // 2
            modal_y = (SCREEN_HEIGHT - modal_h) // 2
            draw_rectangle(modal_x, modal_y, modal_w, modal_h, Color(14, 18, 30, 255))
            draw_rectangle_lines(modal_x, modal_y, modal_w, modal_h, COLOR_ACCENT_CYAN)

            ex_def = self.registry[self.examine_item_id]
            draw_text(f"EXAMINE: {ex_def.name}", modal_x + 24, modal_y + 20, 18, COLOR_TEXT_MAIN)
            draw_text(f"Category: {ex_def.category}", modal_x + 24, modal_y + 44, 13, ex_def.color_badge)

            # Center 3D Wireframe projection
            draw_3d_inspect_mesh(self.examine_item_id, modal_x + modal_w // 2, modal_y + 200, self.examine_yaw, self.examine_pitch)

            # Description
            draw_text(ex_def.description, modal_x + 24, modal_y + 350, 14, COLOR_TEXT_MAIN)
            draw_text("Press [E], [Space], [Esc] or Gamepad (B/Y) to close inspect view.", modal_x + 24, modal_y + modal_h - 36, 12, COLOR_TEXT_DIM)

        # 8. X-Ray Telemetry Overlay ([Tab])
        if self.show_xray and not self.is_examining:
            draw_xray_telemetry(self.inventory, self.registry, self.recipe_db,
                                self.drop_mode_swap, self.show_recipe_hints,
                                self.cursor_col, self.cursor_row)

        # Top Bar HUD & Badges (Keeps x=450..980 clear for dropdowns)
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

