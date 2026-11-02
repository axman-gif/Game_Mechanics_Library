# -*- coding: utf-8 -*-
"""
Gear Compare - Stat Comparison Tooltip & Delta Evaluation Architecture
======================================================================
Section          : 3.1 Menus & UI
Pattern Category : Menus & User Interface, RPG Progression & Economy
Dimension        : 2D

Problem Solved:
  In loot-driven RPGs, action games, and MMOs (Diablo, Borderlands, Destiny, World
  of Warcraft, Cyberpunk 2077), players collect hundreds of weapons, armor pieces,
  and trinkets. Without contextual comparison, players are forced to memorize stats
  and repeatedly toggle between inventory screens, causing severe decision fatigue
  and frequent gear mistakes. Naive implementations either show only raw stats without
  context, recompute diff strings every frame causing memory churn, or fail to clamp
  tooltips within screen boundaries, causing text clipping and cursor occlusion.

How the Pattern Works:
  1. Side-by-Side Dual Tooltip Architecture:
     Hovering or focusing an inventory item dynamically resolves its target equipment
     slot. The UI simultaneously renders the [Currently Equipped Item] and the
     [Inventory Candidate Item] side-by-side, providing an immediate 1-to-1 baseline.
  2. Delta Evaluation Pipeline (Color-Coded Upgrades & Downgrades):
     For every primary and secondary attribute (ATK, DEF, HP, CRIT, SPD, Power Score):
       Delta = Candidate_Stat - Equipped_Stat
     Visual directional indicators display the exact contrast:
       - Delta > 0: Bright Green Up Arrow (▲ +X) indicating an upgrade.
       - Delta < 0: Radiant Red Down Arrow (▼ -X) indicating a downgrade.
       - Delta == 0: Muted Neutral Tag (= 0) indicating identical performance.
  3. Smart Viewport Clamping & Cursor Avoidance:
     The dual-card layout calculates bounding extents and dynamically flips horizontal
     and vertical anchor axes when approaching screen margins, ensuring comparison cards
     never clip off-screen or obscure the hovered cursor slot.
  4. Multi-Slot Comparison Resolution:
     For multi-slot item archetypes (e.g. Ring 1 vs Ring 2), the system automatically
     targets the slot yielding the greatest relative upgrade, while allowing the player
     to cycle comparison target slots live ([Alt] or Gamepad Y).
  5. Interactive Combat Testing Sandbox:
     An interactive Training Dummy allows players to test damage output, strike DPS,
     and critical hits immediately after swapping gear.

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - Mouse Move / Hover                     : Inspect inventory items with Side-by-Side Comparison
  - Left Click / Enter / Gamepad A         : Equip hovered item / Unequip gear slot / Strike Dummy
  - [Alt] / Gamepad Y                      : Cycle comparison target slot (e.g. Ring 1 vs Ring 2)
  - [Tab] / Gamepad View (Select)          : Toggle X-Ray Telemetry & Viewport Clamping Math
  - [F1]  / Gamepad R3                     : Toggle Pattern ON/OFF (Side-by-Side Comparison vs Raw Tooltip)
  - [F2]  / Gamepad L3                     : Auto-Equip Optimal Best-in-Slot loadout
  - [Space] / Right Click / Gamepad RT     : Attack Training Dummy (Test DPS & Mitigation)
  - [Ctrl +/-]                             : Increase / Decrease UI Font Size
  - [F11]                                  : Toggle Fullscreen
  - [R]   / Gamepad Start                  : Reset inventory to default stock
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
WINDOW_TITLE = "Gear Compare - Stat Comparison Tooltip (Raylib Pattern Lab)"

# Palette Constants
COLOR_BG               = Color(10, 13, 22, 255)
COLOR_PANEL_BG         = Color(16, 21, 34, 250)
COLOR_PANEL_BORDER     = Color(42, 58, 90, 255)
COLOR_SLOT_EMPTY       = Color(14, 18, 28, 255)
COLOR_SLOT_BORDER      = Color(35, 48, 76, 255)
COLOR_SLOT_HOVER       = Color(65, 95, 145, 255)
COLOR_SLOT_EQUIPPED    = Color(22, 34, 54, 255)
COLOR_TEXT_MAIN        = Color(235, 242, 255, 255)
COLOR_TEXT_DIM         = Color(140, 160, 190, 255)
COLOR_GOLD_ACCENT      = Color(255, 205, 55, 255)
COLOR_CYAN_ACCENT      = Color(0, 225, 255, 255)
COLOR_GREEN_ACCENT     = Color(65, 245, 130, 255)
COLOR_RED_ACCENT       = Color(255, 75, 75, 255)
COLOR_PURPLE_ACCENT    = Color(195, 85, 255, 255)
COLOR_WHITE            = Color(255, 255, 255, 255)

# Rarity Color Palette
COLOR_RARITY_COMMON    = Color(160, 175, 195, 255)  # Silver/Grey
COLOR_RARITY_RARE      = Color(55, 165, 255, 255)   # Sapphire Blue
COLOR_RARITY_EPIC      = Color(185, 80, 255, 255)   # Mystic Purple
COLOR_RARITY_LEGENDARY = Color(255, 195, 45, 255)   # Radiant Gold

RARITY_NAMES = ["Common", "Rare", "Epic", "Legendary"]

# Slot Constants (C++ Enum equivalent)
SLOT_HEAD       = 0
SLOT_AMULET     = 1
SLOT_CHEST      = 2
SLOT_MAIN_HAND  = 3
SLOT_OFF_HAND   = 4
SLOT_HANDS      = 5
SLOT_LEGS       = 6
SLOT_FEET       = 7
SLOT_RING_1     = 8
SLOT_RING_2     = 9
SLOT_COUNT      = 10

SLOT_NAMES = [
    "Head", "Amulet", "Chest", "Main Hand", "Off Hand",
    "Hands", "Legs", "Feet", "Ring 1", "Ring 2"
]

# Item Type Constants
TYPE_HEAD      = 0
TYPE_AMULET    = 1
TYPE_CHEST     = 2
TYPE_MAIN_HAND = 3
TYPE_OFF_HAND  = 4
TYPE_HANDS     = 5
TYPE_LEGS      = 6
TYPE_FEET      = 7
TYPE_RING      = 8

TYPE_NAMES = [
    "Helmet", "Amulet", "Chest Armor", "Main Hand Weapon", "Off Hand Shield/Focus",
    "Gauntlets", "Greaves", "Boots", "Finger Ring"
]

RARITY_COMMON    = 0
RARITY_RARE      = 1
RARITY_EPIC      = 2
RARITY_LEGENDARY = 3

# UI Layout Geometry
LEFT_PANEL_X  = 35
LEFT_PANEL_Y  = 65
LEFT_PANEL_W  = 335
LEFT_PANEL_H  = 635

CENTER_PANEL_X = 390
CENTER_PANEL_Y = 65
CENTER_PANEL_W = 310
CENTER_PANEL_H = 635

RIGHT_PANEL_X  = 720
RIGHT_PANEL_Y  = 65
RIGHT_PANEL_W  = 525
RIGHT_PANEL_H  = 635

INVENTORY_COLS = 6
INVENTORY_ROWS = 4
INVENTORY_SLOT_COUNT = 24


# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATION (STAT COMPARISON TOOLTIP PIPELINE)
# ==============================================================================

class EquipmentItem:
    """
    Plain struct representing an equippable item instance.
    C++ Equivalent:
      struct EquipmentItem {
          int item_id;
          char name[48];
          int item_type;      // TYPE_HEAD, TYPE_CHEST, etc.
          int rarity;         // RARITY_COMMON..LEGENDARY
          int atk, defense, hp, spd;
          float crit;
          bool is_two_handed;
          Color color_primary, color_secondary;
          char icon_glyph[16];
          char flavor[64];
          int get_power_score() const;
      };
    """
    def __init__(
        self,
        item_id: int,
        name: str,
        item_type: int,
        rarity: int,
        atk: int,
        defense: int,
        hp: int,
        crit: float,
        spd: int,
        is_two_handed: bool = False,
        color_primary: Color = None,
        color_secondary: Color = None,
        icon_glyph: str = "",
        flavor: str = ""
    ):
        self.item_id = item_id
        self.name = name
        self.item_type = item_type
        self.rarity = rarity
        self.atk = atk
        self.defense = defense
        self.hp = hp
        self.crit = crit
        self.spd = spd
        self.is_two_handed = is_two_handed
        self.color_primary = color_primary or Color(200, 210, 225, 255)
        self.color_secondary = color_secondary or Color(100, 120, 150, 255)
        self.icon_glyph = icon_glyph
        self.flavor = flavor

    def get_power_score(self) -> int:
        """Computes a weighted composite item rating for quick appraisal."""
        return int(
            self.atk * 2.2 +
            self.defense * 1.8 +
            self.hp * 0.45 +
            self.crit * 4.5 +
            self.spd * 0.8
        )


class StatDelta:
    """
    Computed contrast difference between candidate item and currently equipped item.
    C++ Equivalent:
      struct StatDelta {
          int d_atk, d_def, d_hp, d_spd, d_power;
          float d_crit;
          float pct_power;
          bool is_upgrade;
          bool is_equal;
          bool is_downgrade;
      };
    """
    def __init__(self):
        self.d_atk = 0
        self.d_def = 0
        self.d_hp = 0
        self.d_crit = 0.0
        self.d_spd = 0
        self.d_power = 0
        self.pct_power = 0.0
        self.is_upgrade = False
        self.is_equal = True
        self.is_downgrade = False


def compute_stat_delta(candidate: EquipmentItem, equipped: EquipmentItem) -> StatDelta:
    """
    Evaluates the exact mathematical contrast between candidate and equipped gear.
    C++ Equivalent:
      StatDelta compute_stat_delta(const EquipmentItem* cand, const EquipmentItem* eq);
    """
    delta = StatDelta()

    c_atk = candidate.atk if candidate is not None else 0
    c_def = candidate.defense if candidate is not None else 0
    c_hp = candidate.hp if candidate is not None else 0
    c_crit = candidate.crit if candidate is not None else 0.0
    c_spd = candidate.spd if candidate is not None else 0
    c_power = candidate.get_power_score() if candidate is not None else 0

    e_atk = equipped.atk if equipped is not None else 0
    e_def = equipped.defense if equipped is not None else 0
    e_hp = equipped.hp if equipped is not None else 0
    e_crit = equipped.crit if equipped is not None else 0.0
    e_spd = equipped.spd if equipped is not None else 0
    e_power = equipped.get_power_score() if equipped is not None else 0

    delta.d_atk = c_atk - e_atk
    delta.d_def = c_def - e_def
    delta.d_hp = c_hp - e_hp
    delta.d_crit = c_crit - e_crit
    delta.d_spd = c_spd - e_spd
    delta.d_power = c_power - e_power

    if e_power > 0:
        delta.pct_power = (float(delta.d_power) / float(e_power)) * 100.0
    elif c_power > 0:
        delta.pct_power = 100.0
    else:
        delta.pct_power = 0.0

    if delta.d_power > 0:
        delta.is_upgrade = True
        delta.is_equal = False
        delta.is_downgrade = False
    elif delta.d_power < 0:
        delta.is_upgrade = False
        delta.is_equal = False
        delta.is_downgrade = True
    else:
        delta.is_upgrade = False
        delta.is_equal = True
        delta.is_downgrade = False

    return delta


def calculate_clamped_tooltip_rect(
    mouse_x: int,
    mouse_y: int,
    total_w: int,
    total_h: int,
    screen_w: int,
    screen_h: int
) -> tuple:
    """
    Calculates screen-clamped coordinates for comparison cards, flipping horizontal
    and vertical axes when the tooltip approaches screen borders.
    Returns: (final_x, final_y, flipped_x_bool, flipped_y_bool)
    """
    offset_x = 22
    offset_y = 12

    target_x = mouse_x + offset_x
    target_y = mouse_y + offset_y

    flipped_x = False
    flipped_y = False

    # Horizontal boundary check (flip left of cursor if overflowing right)
    if target_x + total_w > screen_w - 20:
        target_x = mouse_x - total_w - 18
        flipped_x = True

    # Clamp left bound
    if target_x < 20:
        target_x = 20

    # Vertical boundary check (flip above cursor if overflowing bottom)
    if target_y + total_h > screen_h - 20:
        target_y = mouse_y - total_h - 14
        flipped_y = True

    # Clamp top bound
    if target_y < 55:
        target_y = 55

    return (int(target_x), int(target_y), flipped_x, flipped_y)


def draw_up_arrow(x: int, y: int, size: int, color: Color):
    """Draws a crisp procedural triangle pointing upward (Upgrade)."""
    half = size // 2
    p1 = Vector2(float(x), float(y - half))
    p2 = Vector2(float(x - half), float(y + half))
    p3 = Vector2(float(x + half), float(y + half))
    draw_triangle(p1, p2, p3, color)


def draw_down_arrow(x: int, y: int, size: int, color: Color):
    """Draws a crisp procedural triangle pointing downward (Downgrade)."""
    half = size // 2
    p1 = Vector2(float(x - half), float(y - half))
    p2 = Vector2(float(x + half), float(y - half))
    p3 = Vector2(float(x), float(y + half))
    draw_triangle(p1, p2, p3, color)


# ==============================================================================
# BLOCK 2: WORLD SIMULATION & ENTITIES
# ==============================================================================

class FloatingDamageNumber:
    """Struct for combat text floating numbers above the training dummy."""
    def __init__(self):
        self.active = False
        self.x = 0.0
        self.y = 0.0
        self.vy = -60.0
        self.text = ""
        self.color = COLOR_WHITE
        self.timer = 0.0
        self.max_life = 0.85
        self.scale = 1.0


class TrainingDummy:
    """Combat target dummy providing real-time tactile validation of gear stats."""
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.base_armor = 25  # Dummy armor rating
        self.hit_timer = 0.0
        self.shake_x = 0.0
        self.last_damage_dealt = 0
        self.total_damage_dealt = 0
        self.total_strikes = 0
        self.was_last_crit = False

    def take_hit(self, effective_atk: int, effective_crit: float) -> tuple:
        self.hit_timer = 0.28
        self.total_strikes += 1

        variance = random.uniform(0.92, 1.08)
        raw_damage = max(1, effective_atk) * variance

        crit_roll = random.uniform(0.0, 100.0)
        is_crit = crit_roll < effective_crit
        crit_multiplier = 2.0 if is_crit else 1.0

        armor_factor = 50.0 / (50.0 + self.base_armor)
        final_damage = max(1, int(raw_damage * crit_multiplier * armor_factor))

        self.last_damage_dealt = final_damage
        self.total_damage_dealt += final_damage
        self.was_last_crit = is_crit
        return (final_damage, is_crit)

    def update(self, dt: float):
        if self.hit_timer > 0.0:
            self.hit_timer -= dt
            if self.hit_timer < 0.0:
                self.hit_timer = 0.0
            self.shake_x = math.sin(self.hit_timer * 38.0) * (self.hit_timer / 0.28) * 14.0
        else:
            self.shake_x = 0.0

    def draw(self):
        cx = int(self.x + self.shake_x)
        cy = int(self.y)

        # Base Pedestal
        draw_rectangle(cx - 35, cy + 130, 70, 14, Color(75, 45, 25, 255))
        draw_line_ex(Vector2(cx - 35, cy + 130), Vector2(cx, cy + 80), 4.0, Color(95, 60, 35, 255))
        draw_line_ex(Vector2(cx + 35, cy + 130), Vector2(cx, cy + 80), 4.0, Color(95, 60, 35, 255))
        draw_rectangle(cx - 8, cy + 20, 16, 110, Color(110, 70, 40, 255))

        # Straw Torso with Target Rings
        draw_circle(cx, cy + 45, 34, Color(185, 145, 85, 255))
        draw_circle_lines(cx, cy + 45, 34, Color(140, 105, 55, 255))
        draw_circle(cx, cy + 45, 24, Color(220, 60, 60, 255))
        draw_circle(cx, cy + 45, 16, Color(245, 245, 245, 255))
        draw_circle(cx, cy + 45, 8, Color(220, 60, 60, 255))

        # Wooden Outstretched Arms
        draw_rectangle(cx - 52, cy + 30, 104, 10, Color(125, 80, 45, 255))
        draw_circle(cx - 52, cy + 35, 6, Color(90, 55, 30, 255))
        draw_circle(cx + 52, cy + 35, 6, Color(90, 55, 30, 255))

        # Iron Training Helmet
        draw_circle(cx, cy - 8, 16, Color(135, 145, 165, 255))
        draw_rectangle(cx - 14, cy - 8, 28, 14, Color(105, 115, 135, 255))
        draw_rectangle(cx - 10, cy - 2, 20, 4, Color(25, 30, 40, 255))

        if self.hit_timer > 0.15:
            draw_circle(cx, cy + 45, 38, Color(255, 255, 255, 80))


class CharacterEquipment:
    """Manages active equipment slots and overall combat attribute calculation."""
    def __init__(self):
        self.slots = [None] * SLOT_COUNT
        self.base_hp = 300
        self.base_atk = 25
        self.base_def = 15
        self.base_crit = 5.0
        self.base_spd = 180

        self.effective_hp = 300
        self.effective_atk = 25
        self.effective_def = 15
        self.effective_crit = 5.0
        self.effective_spd = 180
        self.total_power_score = 0
        self.recalculate()

    def recalculate(self):
        gear_hp = 0
        gear_atk = 0
        gear_def = 0
        gear_crit = 0.0
        gear_spd = 0
        total_pwr = 0

        for item in self.slots:
            if item is not None:
                gear_hp += item.hp
                gear_atk += item.atk
                gear_def += item.defense
                gear_crit += item.crit
                gear_spd += item.spd
                total_pwr += item.get_power_score()

        self.effective_hp = self.base_hp + gear_hp
        self.effective_atk = self.base_atk + gear_atk
        self.effective_def = self.base_def + gear_def
        self.effective_crit = self.base_crit + gear_crit
        self.effective_spd = max(60, self.base_spd + gear_spd)
        self.total_power_score = total_pwr


# ==============================================================================
# BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY ([Tab] & [F1])
# ==============================================================================

def draw_xray_overlay(
    candidate: EquipmentItem,
    equipped: EquipmentItem,
    delta: StatDelta,
    pattern_enabled: bool,
    active_ring_slot: int,
    x: int,
    y: int,
    w: int,
    h: int
):
    """
    Renders live educational telemetry explaining the stat comparison pipeline,
    delta vectors, multi-slot targeting, and screen bounds math.
    """
    draw_rectangle(x, y, w, h, Color(14, 18, 30, 245))
    draw_rectangle_lines(x, y, w, h, COLOR_CYAN_ACCENT)

    # Header
    draw_rectangle(x, y, w, 28, Color(20, 32, 54, 255))
    draw_text("X-RAY INSPECTOR: STAT COMPARISON PIPELINE", x + 12, y + 7, 13, COLOR_CYAN_ACCENT)
    draw_text("[Tab] Close", x + w - 85, y + 7, 11, COLOR_TEXT_DIM)

    cur_y = y + 36

    # 1. Delta Pipeline Vector State
    draw_text("1. DELTA VECTOR PIPELINE", x + 12, cur_y, 11, COLOR_GOLD_ACCENT)
    cur_y += 16
    cand_name = candidate.name if candidate else "(None)"
    eq_name = equipped.name if equipped else "(Empty Slot)"
    draw_text(f"Candidate: {cand_name[:24]}", x + 18, cur_y, 11, COLOR_TEXT_MAIN)
    cur_y += 14
    draw_text(f"Equipped : {eq_name[:24]}", x + 18, cur_y, 11, COLOR_TEXT_DIM)
    cur_y += 18

    # Vector Delta Line
    vec_str = (
        f"Delta Vector: [dATK:{delta.d_atk:+d}, dDEF:{delta.d_def:+d}, "
        f"dHP:{delta.d_hp:+d}, dCRIT:{delta.d_crit:+.1f}%, dSPD:{delta.d_spd:+d}]"
    )
    draw_text(vec_str, x + 18, cur_y, 10, COLOR_CYAN_ACCENT)
    cur_y += 15

    score_str = f"Composite Power Score Delta: {delta.d_power:+d} ({delta.pct_power:+.1f}%)"
    score_col = COLOR_GREEN_ACCENT if delta.is_upgrade else (COLOR_RED_ACCENT if delta.is_downgrade else COLOR_TEXT_DIM)
    draw_text(score_str, x + 18, cur_y, 11, score_col)
    cur_y += 22

    # 2. Multi-Slot Target Resolution (e.g. Ring 1 vs Ring 2)
    draw_text("2. MULTI-SLOT RESOLUTION LOGIC", x + 12, cur_y, 11, COLOR_GOLD_ACCENT)
    cur_y += 16
    ring_target_str = f"Active Comparison Target: {SLOT_NAMES[active_ring_slot]} ([Alt] / Gamepad Y to Toggle)"
    draw_text(ring_target_str, x + 18, cur_y, 10, COLOR_TEXT_MAIN)
    cur_y += 14
    draw_text("Rule: Rings can fit either Ring 1 or Ring 2. System compares against toggled slot.", x + 18, cur_y, 9, COLOR_TEXT_DIM)
    cur_y += 22

    # 3. Viewport Clamping & Collision Rig
    draw_text("3. SMART VIEWPORT BOUNDS CLAMPING", x + 12, cur_y, 11, COLOR_GOLD_ACCENT)
    cur_y += 16
    draw_text("Geometry: Dual Cards (Width: 460px, Height: 260px)", x + 18, cur_y, 10, COLOR_TEXT_MAIN)
    cur_y += 14
    draw_text("Math: if (mx + W > SCREEN_W - 20) -> tx = mx - W - offset (Horizontal Flip)", x + 18, cur_y, 9, COLOR_TEXT_DIM)
    cur_y += 14
    draw_text("Math: if (my + H > SCREEN_H - 20) -> ty = my - H - offset (Vertical Flip)", x + 18, cur_y, 9, COLOR_TEXT_DIM)
    cur_y += 22

    # 4. Pattern Mode Inspection
    draw_text("4. PATTERN COMPARISON AUDIT", x + 12, cur_y, 11, COLOR_GOLD_ACCENT)
    cur_y += 16
    if pattern_enabled:
        draw_text("MODE: SIDE-BY-SIDE DUAL TOOLTIP (ACTIVE)", x + 18, cur_y, 11, COLOR_GREEN_ACCENT)
        cur_y += 14
        draw_text("Instant visual appraisal: green/red directional indicators, side-by-side cards.", x + 18, cur_y, 9, COLOR_TEXT_DIM)
    else:
        draw_text("MODE: NAIVE SINGLE-ITEM RAW TOOLTIP (INACTIVE)", x + 18, cur_y, 11, COLOR_RED_ACCENT)
        cur_y += 14
        draw_text("Cognitive strain: No context, player must memorize numbers across menus.", x + 18, cur_y, 9, COLOR_TEXT_DIM)


# ==============================================================================
# BLOCK 4: MAIN GAME LOOP & AUTOMATED SMOKE TEST
# ==============================================================================

class GearCompareLabGame:
    """
    Interactive Stat Comparison Tooltip Pattern Lab.
    """
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()

        self.sfx = SoundLibrary()
        self.sfx.init_defaults()

        self.equipment = CharacterEquipment()
        self.training_dummy = TrainingDummy(CENTER_PANEL_X + 155, CENTER_PANEL_Y + 115)

        # 24 inventory stash slots (6 cols x 4 rows)
        self.inventory = [None] * INVENTORY_SLOT_COUNT

        # UI hover and focus state
        self.hovered_inventory_slot = -1
        self.hovered_equipped_slot = -1
        self.active_ring_slot = SLOT_RING_1  # Toggled via [Alt] or Gamepad Y

        # Interactive toggles
        self.show_xray = True
        self.pattern_enabled = True

        # Procedural animation timers
        self.anim_timer = 0.0
        self.attack_anim_timer = 0.0

        # Floating combat damage pool (24 instances)
        self.floating_numbers = []
        for _ in range(24):
            self.floating_numbers.append(FloatingDamageNumber())

        # Status notification banner
        self.status_message = "Hover an inventory item to compare stats side-by-side against equipped gear."
        self.status_message_timer = 4.0

        # Populate starter loadout and rich stash loot
        self._populate_initial_gear_and_stash()

    def _populate_initial_gear_and_stash(self):
        """Initializes character with baseline gear and fills inventory with upgrades and sidegrades."""
        # 1. Equipped Starter Items
        starter_helm = EquipmentItem(1, "Iron Bascinet", TYPE_HEAD, RARITY_COMMON,
                                     atk=0, defense=12, hp=25, crit=0.0, spd=0,
                                     color_primary=Color(150, 160, 180, 255), color_secondary=Color(80, 90, 110, 255),
                                     icon_glyph="HELM", flavor="Standard infantry helmet offering modest protection.")
        starter_chest = EquipmentItem(2, "Riveted Chainmail", TYPE_CHEST, RARITY_COMMON,
                                      atk=0, defense=22, hp=40, crit=0.0, spd=-5,
                                      color_primary=Color(140, 150, 170, 255), color_secondary=Color(70, 80, 100, 255),
                                      icon_glyph="CHEST", flavor="Linked steel rings designed to deflect glancing blade cuts.")
        starter_sword = EquipmentItem(3, "Steel Longsword", TYPE_MAIN_HAND, RARITY_COMMON,
                                      atk=32, defense=0, hp=0, crit=4.0, spd=0,
                                      color_primary=Color(200, 205, 220, 255), color_secondary=Color(100, 110, 130, 255),
                                      icon_glyph="1H-SWORD", flavor="Reliable straight sword standard among royal guards.")
        starter_shield = EquipmentItem(4, "Wooden Roundshield", TYPE_OFF_HAND, RARITY_COMMON,
                                       atk=0, defense=14, hp=20, crit=0.0, spd=0,
                                       color_primary=Color(140, 100, 60, 255), color_secondary=Color(80, 50, 25, 255),
                                       icon_glyph="SHIELD", flavor="Oak planks reinforced with an iron center boss.")
        starter_gauntlets = EquipmentItem(5, "Leather Bracers", TYPE_HANDS, RARITY_COMMON,
                                          atk=4, defense=8, hp=0, crit=2.0, spd=5,
                                          color_primary=Color(130, 90, 55, 255), color_secondary=Color(70, 45, 25, 255),
                                          icon_glyph="GLOVES", flavor="Supple cowhide wristguards enabling quick hand movement.")
        starter_boots = EquipmentItem(6, "Worn Marching Boots", TYPE_FEET, RARITY_COMMON,
                                      atk=0, defense=6, hp=15, crit=0.0, spd=20,
                                      color_primary=Color(115, 80, 50, 255), color_secondary=Color(60, 40, 20, 255),
                                      icon_glyph="BOOTS", flavor="Tough leather boots broken in over hundreds of road leagues.")
        starter_ring1 = EquipmentItem(7, "Pewter Band", TYPE_RING, RARITY_COMMON,
                                      atk=5, defense=0, hp=10, crit=1.5, spd=0,
                                      color_primary=Color(165, 175, 190, 255), color_secondary=Color(90, 100, 115, 255),
                                      icon_glyph="RING", flavor="Simple pewter ring passed down through generations.")

        self.equipment.slots[SLOT_HEAD] = starter_helm
        self.equipment.slots[SLOT_CHEST] = starter_chest
        self.equipment.slots[SLOT_MAIN_HAND] = starter_sword
        self.equipment.slots[SLOT_OFF_HAND] = starter_shield
        self.equipment.slots[SLOT_HANDS] = starter_gauntlets
        self.equipment.slots[SLOT_FEET] = starter_boots
        self.equipment.slots[SLOT_RING_1] = starter_ring1
        self.equipment.slots[SLOT_AMULET] = None
        self.equipment.slots[SLOT_LEGS] = None
        self.equipment.slots[SLOT_RING_2] = None

        self.equipment.recalculate()

        # 2. Rich Inventory Stash Loot (Varied Rarities, Upgrades, Downgrades, Sidegrades)
        stash_catalog = [
            # Rare / Epic Weapons
            EquipmentItem(8, "Sunsteel Broadsword", TYPE_MAIN_HAND, RARITY_RARE,
                          atk=48, defense=0, hp=0, crit=8.0, spd=5,
                          color_primary=Color(245, 215, 100, 255), color_secondary=Color(150, 110, 40, 255),
                          icon_glyph="1H-SWORD", flavor="Forged in solar flame. Swings with brilliant blinding speed."),
            EquipmentItem(9, "Titan's Earthshaker", TYPE_MAIN_HAND, RARITY_EPIC,
                          atk=95, defense=15, hp=0, crit=0.0, spd=-20, is_two_handed=True,
                          color_primary=Color(225, 150, 70, 255), color_secondary=Color(120, 70, 30, 255),
                          icon_glyph="2H-HAMMER", flavor="Colossal warhammer that pulverizes granite and plate armor alike."),
            EquipmentItem(10, "Shadow Twin Daggers", TYPE_MAIN_HAND, RARITY_RARE,
                          atk=36, defense=0, hp=0, crit=16.0, spd=25,
                          color_primary=Color(180, 110, 240, 255), color_secondary=Color(90, 40, 140, 255),
                          icon_glyph="DAGGER", flavor="Matched pair of serrated daggers striking fatal pressure points."),
            EquipmentItem(11, "Aetheric Scepter", TYPE_MAIN_HAND, RARITY_EPIC,
                          atk=62, defense=0, hp=35, crit=6.0, spd=0,
                          color_primary=Color(70, 200, 255, 255), color_secondary=Color(20, 100, 160, 255),
                          icon_glyph="1H-STAFF", flavor="Focusing crystal channeling raw arcane lightning bolts."),

            # Shields & Off-Hand
            EquipmentItem(12, "Bulwark Tower Shield", TYPE_OFF_HAND, RARITY_EPIC,
                          atk=0, defense=36, hp=75, crit=0.0, spd=-12,
                          color_primary=Color(190, 205, 235, 255), color_secondary=Color(90, 110, 150, 255),
                          icon_glyph="SHIELD", flavor="Impenetrable wall of layered steel sealing defensive ranks."),
            EquipmentItem(13, "Dragonscale Buckler", TYPE_OFF_HAND, RARITY_RARE,
                          atk=6, defense=22, hp=35, crit=5.0, spd=8,
                          color_primary=Color(90, 170, 220, 255), color_secondary=Color(40, 90, 140, 255),
                          icon_glyph="SHIELD", flavor="Crafted from young azure dragon scales. Light and buoyant."),

            # Armor Upgrades
            EquipmentItem(14, "Vanguard Greathelm", TYPE_HEAD, RARITY_EPIC,
                          atk=0, defense=26, hp=55, crit=0.0, spd=-4,
                          color_primary=Color(180, 195, 225, 255), color_secondary=Color(85, 105, 140, 255),
                          icon_glyph="HELM", flavor="Heavy steel helm adorned with royal paladin sigils."),
            EquipmentItem(15, "Crown of the Archmage", TYPE_HEAD, RARITY_LEGENDARY,
                          atk=32, defense=8, hp=50, crit=7.0, spd=0,
                          color_primary=Color(255, 215, 60, 255), color_secondary=Color(0, 180, 230, 255),
                          icon_glyph="CROWN", flavor="Radiant coronal circlet that enhances cognitive spellcraft."),
            EquipmentItem(16, "Aegis Cuirass", TYPE_CHEST, RARITY_EPIC,
                          atk=0, defense=42, hp=90, crit=0.0, spd=-8,
                          color_primary=Color(175, 190, 220, 255), color_secondary=Color(80, 100, 135, 255),
                          icon_glyph="CHEST", flavor="High-tempered breastplate engineered to withstand siege ballistae."),
            EquipmentItem(17, "Astral Silk Robes", TYPE_CHEST, RARITY_LEGENDARY,
                          atk=38, defense=16, hp=60, crit=5.0, spd=12,
                          color_primary=Color(60, 150, 255, 255), color_secondary=Color(20, 70, 150, 255),
                          icon_glyph="ROBES", flavor="Woven from night sky threads humming with abjuration wards."),
            EquipmentItem(18, "Greaves of Fortitude", TYPE_LEGS, RARITY_RARE,
                          atk=0, defense=20, hp=45, crit=0.0, spd=-4,
                          color_primary=Color(160, 175, 205, 255), color_secondary=Color(75, 90, 125, 255),
                          icon_glyph="LEGS", flavor="Articulated shin guards providing steady balance in melee."),
            EquipmentItem(19, "Boots of the Windrunner", TYPE_FEET, RARITY_RARE,
                          atk=0, defense=10, hp=20, crit=4.0, spd=55,
                          color_primary=Color(90, 210, 160, 255), color_secondary=Color(35, 115, 80, 255),
                          icon_glyph="BOOTS", flavor="Enchanted soles leaving glowing gust wisps in their wake."),

            # Rings & Jewelry (Multi-slot comparison targets!)
            EquipmentItem(20, "Ruby Signet of Fury", TYPE_RING, RARITY_RARE,
                          atk=24, defense=-6, hp=0, crit=6.0, spd=8,
                          color_primary=Color(245, 75, 75, 255), color_secondary=Color(130, 25, 25, 255),
                          icon_glyph="RING", flavor="Infuses attacks with fiery wrath at the expense of guard stance."),
            EquipmentItem(21, "Band of the Bastion", TYPE_RING, RARITY_RARE,
                          atk=0, defense=18, hp=50, crit=0.0, spd=-5,
                          color_primary=Color(160, 190, 240, 255), color_secondary=Color(70, 95, 140, 255),
                          icon_glyph="RING", flavor="Solid platinum band granting fortress-like composure."),
            EquipmentItem(22, "Emerald Loop of Agility", TYPE_RING, RARITY_RARE,
                          atk=10, defense=4, hp=20, crit=5.0, spd=25,
                          color_primary=Color(60, 235, 120, 255), color_secondary=Color(25, 120, 55, 255),
                          icon_glyph="RING", flavor="Honed by elven fletchers to sharpen reflexes and sprint bursts."),
            EquipmentItem(23, "Nexus Ring of Omnipotence", TYPE_RING, RARITY_LEGENDARY,
                          atk=35, defense=15, hp=65, crit=8.0, spd=15,
                          color_primary=Color(255, 215, 60, 255), color_secondary=Color(0, 220, 255, 255),
                          icon_glyph="RING", flavor="A legendary celestial relic radiating harmonic elemental power."),
            EquipmentItem(24, "Heart of Vitality", TYPE_AMULET, RARITY_EPIC,
                          atk=0, defense=14, hp=120, crit=0.0, spd=0,
                          color_primary=Color(255, 80, 110, 255), color_secondary=Color(140, 30, 50, 255),
                          icon_glyph="AMULET", flavor="Pulsates with ancient dragon blood, heavily boosting constitution."),
            EquipmentItem(25, "Berserker's Torc", TYPE_AMULET, RARITY_RARE,
                          atk=28, defense=-8, hp=0, crit=7.5, spd=10,
                          color_primary=Color(235, 95, 60, 255), color_secondary=Color(120, 35, 20, 255),
                          icon_glyph="AMULET", flavor="Braided copper torc stoking relentless battle bloodlust.")
        ]

        for i in range(min(INVENTORY_SLOT_COUNT, len(stash_catalog))):
            self.inventory[i] = stash_catalog[i]

    def spawn_floating_damage(self, text: str, x: float, y: float, is_crit: bool):
        target_num = None
        for num in self.floating_numbers:
            if not num.active:
                target_num = num
                break

        if target_num is None:
            min_timer = 999.0
            for num in self.floating_numbers:
                if num.timer < min_timer:
                    min_timer = num.timer
                    target_num = num

        if target_num is not None:
            target_num.active = True
            target_num.x = x + random.uniform(-16.0, 16.0)
            target_num.y = y + random.uniform(-8.0, 8.0)
            target_num.vy = -75.0 if is_crit else -50.0
            target_num.text = text
            target_num.color = COLOR_GOLD_ACCENT if is_crit else COLOR_WHITE
            target_num.timer = 0.85
            target_num.max_life = 0.85
            target_num.scale = 1.35 if is_crit else 1.0

    def perform_dummy_strike(self):
        dmg, is_crit = self.training_dummy.take_hit(
            self.equipment.effective_atk,
            self.equipment.effective_crit
        )
        self.attack_anim_timer = 0.25

        txt = f"CRIT! {dmg}" if is_crit else str(dmg)
        dummy_top_x = self.training_dummy.x
        dummy_top_y = self.training_dummy.y + 10
        self.spawn_floating_damage(txt, dummy_top_x, dummy_top_y, is_crit)

        if is_crit:
            self.sfx.play("explosion", 0.75)
        else:
            self.sfx.play("hit", 0.70)

        self.status_message = f"Struck Target Dummy for {dmg} damage ({'CRITICAL HIT!' if is_crit else 'Normal Hit'})."
        self.status_message_timer = 2.5

    def resolve_target_slot(self, item: EquipmentItem) -> int:
        """Determines matching equipment slot, respecting the active ring toggle."""
        if item is None:
            return -1
        itype = item.item_type
        if itype == TYPE_HEAD:
            return SLOT_HEAD
        elif itype == TYPE_AMULET:
            return SLOT_AMULET
        elif itype == TYPE_CHEST:
            return SLOT_CHEST
        elif itype == TYPE_MAIN_HAND:
            return SLOT_MAIN_HAND
        elif itype == TYPE_OFF_HAND:
            return SLOT_OFF_HAND
        elif itype == TYPE_HANDS:
            return SLOT_HANDS
        elif itype == TYPE_LEGS:
            return SLOT_LEGS
        elif itype == TYPE_FEET:
            return SLOT_FEET
        elif itype == TYPE_RING:
            return self.active_ring_slot
        return -1

    def equip_item(self, item: EquipmentItem, target_slot: int = -1):
        if item is None:
            return

        if target_slot < 0:
            target_slot = self.resolve_target_slot(item)

        if target_slot < 0 or target_slot >= SLOT_COUNT:
            return

        old_item = self.equipment.slots[target_slot]
        self.equipment.slots[target_slot] = item
        self.equipment.recalculate()
        self.sfx.play("coin", 0.8)
        self.status_message = f"Equipped {item.name} into {SLOT_NAMES[target_slot]} slot."
        self.status_message_timer = 2.5
        return old_item

    def unequip_slot(self, slot_idx: int):
        if slot_idx < 0 or slot_idx >= SLOT_COUNT:
            return
        item = self.equipment.slots[slot_idx]
        if item is not None:
            # Place into first free inventory slot
            for i in range(INVENTORY_SLOT_COUNT):
                if self.inventory[i] is None:
                    self.inventory[i] = item
                    self.equipment.slots[slot_idx] = None
                    self.equipment.recalculate()
                    self.sfx.play("click", 0.7)
                    self.status_message = f"Unequipped {item.name} to inventory."
                    self.status_message_timer = 2.5
                    break

    def auto_equip_optimal(self):
        """Greedily equips the highest power score item for every slot."""
        all_gear = []
        for i in range(SLOT_COUNT):
            if self.equipment.slots[i] is not None:
                all_gear.append(self.equipment.slots[i])
                self.equipment.slots[i] = None

        for i in range(INVENTORY_SLOT_COUNT):
            if self.inventory[i] is not None:
                all_gear.append(self.inventory[i])
                self.inventory[i] = None

        # Sort by power score descending
        n = len(all_gear)
        for i in range(n):
            for j in range(0, n - i - 1):
                if all_gear[j].get_power_score() < all_gear[j + 1].get_power_score():
                    temp = all_gear[j]
                    all_gear[j] = all_gear[j + 1]
                    all_gear[j + 1] = temp

        unplaced = []
        for item in all_gear:
            placed = False
            best_slot = self.resolve_target_slot(item)
            if best_slot >= 0 and self.equipment.slots[best_slot] is None:
                self.equipment.slots[best_slot] = item
                placed = True
            elif item.item_type == TYPE_RING:
                # Ring fallback check for other slot
                other_ring = SLOT_RING_2 if best_slot == SLOT_RING_1 else SLOT_RING_1
                if self.equipment.slots[other_ring] is None:
                    self.equipment.slots[other_ring] = item
                    placed = True

            if not placed:
                unplaced.append(item)

        for i in range(min(INVENTORY_SLOT_COUNT, len(unplaced))):
            self.inventory[i] = unplaced[i]

        self.equipment.recalculate()
        self.sfx.play("coin", 0.8)
        self.status_message = "Auto-Equipped Optimal Best-in-Slot loadout!"
        self.status_message_timer = 3.0

    def update(self):
        dt = min(get_frame_time(), 0.05)
        self.anim_timer += dt

        if self.attack_anim_timer > 0.0:
            self.attack_anim_timer -= dt
            if self.attack_anim_timer < 0.0:
                self.attack_anim_timer = 0.0

        if self.status_message_timer > 0.0:
            self.status_message_timer -= dt

        self.training_dummy.update(dt)

        for num in self.floating_numbers:
            if num.active:
                num.y += num.vy * dt
                num.vy = damp(num.vy, 10.0, 3.5, dt)
                num.timer -= dt
                if num.timer <= 0.0:
                    num.active = False

        # Toggles & Shortcuts
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
            self.sfx.play("click", 0.6)

        if is_dual_pattern_toggle_pressed():
            self.pattern_enabled = not self.pattern_enabled
            mode_name = "SIDE-BY-SIDE DUAL CARDS & STAT DELTAS" if self.pattern_enabled else "NAIVE RAW TOOLTIP (NO COMPARISON)"
            self.status_message = f"Pattern Mode: {mode_name}"
            self.status_message_timer = 3.5
            self.sfx.play("powerup", 0.7)

        # Toggle comparison ring ([Alt] or Gamepad Y)
        if (
            is_key_pressed(KEY_LEFT_ALT)
            or is_key_pressed(KEY_RIGHT_ALT)
            or (is_any_gamepad_connected() and is_gamepad_button_pressed(get_active_gamepad_id(), GAMEPAD_BUTTON_RIGHT_FACE_UP))
        ):
            self.active_ring_slot = SLOT_RING_2 if self.active_ring_slot == SLOT_RING_1 else SLOT_RING_1
            self.status_message = f"Comparison Ring Switched: Now comparing against {SLOT_NAMES[self.active_ring_slot]}."
            self.status_message_timer = 2.5
            self.sfx.play("click", 0.6)

        # [F2] / Gamepad L3: Auto-Equip Optimal
        if is_key_pressed(KEY_F2) or is_dual_secondary_toggle_pressed():
            self.auto_equip_optimal()

        # [R] / Gamepad Start: Reset All
        if is_dual_reset_pressed():
            self._populate_initial_gear_and_stash()
            self.sfx.play("powerup", 0.6)
            self.status_message = "Reset gear loadout and inventory supplies."
            self.status_message_timer = 3.0

        # Strike Dummy via Space, Right Click, or Gamepad RT / A
        if is_key_pressed(KEY_SPACE) or is_mouse_button_pressed(MOUSE_BUTTON_RIGHT):
            self.perform_dummy_strike()
        elif is_any_gamepad_connected():
            pad_id = get_active_gamepad_id()
            if is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_TRIGGER_1):
                self.perform_dummy_strike()

        # Mouse Interactions
        mx, my = get_mouse_x(), get_mouse_y()
        clicked_left = is_mouse_button_pressed(MOUSE_BUTTON_LEFT)
        self._update_mouse_interactions(mx, my, clicked_left)

    def _update_mouse_interactions(self, mx: int, my: int, clicked_left: bool):
        self.hovered_inventory_slot = -1
        self.hovered_equipped_slot = -1

        # 1. Check Inventory Grid
        inv_rects = self._get_inventory_slot_rects()
        for i in range(INVENTORY_SLOT_COUNT):
            rx, ry, rw, rh = inv_rects[i]
            if rx <= mx <= rx + rw and ry <= my <= ry + rh:
                self.hovered_inventory_slot = i
                if clicked_left:
                    candidate = self.inventory[i]
                    if candidate is not None:
                        target_slot = self.resolve_target_slot(candidate)
                        old_item = self.equip_item(candidate, target_slot)
                        self.inventory[i] = old_item
                break

        # 2. Check Equipped Slots
        eq_rects = self._get_equipped_slot_rects()
        for i in range(SLOT_COUNT):
            rx, ry, rw, rh = eq_rects[i]
            if rx <= mx <= rx + rw and ry <= my <= ry + rh:
                self.hovered_equipped_slot = i
                if clicked_left:
                    self.unequip_slot(i)
                break

        # 3. Check Attack Dummy Click
        if (
            CENTER_PANEL_X + 90 <= mx <= CENTER_PANEL_X + 220
            and CENTER_PANEL_Y + 40 <= my <= CENTER_PANEL_Y + 185
            and clicked_left
        ):
            self.perform_dummy_strike()

        # 4. Check Lab Action Buttons in Center Panel
        btn_y = CENTER_PANEL_Y + 415
        btn_w = CENTER_PANEL_W - 24
        btn_h = 34
        btn_x = CENTER_PANEL_X + 12

        # Button 1: Attack Dummy
        if btn_x <= mx <= btn_x + btn_w and btn_y <= my <= btn_y + btn_h and clicked_left:
            self.perform_dummy_strike()

        # Button 2: Toggle Pattern
        btn_y += 42
        if btn_x <= mx <= btn_x + btn_w and btn_y <= my <= btn_y + btn_h and clicked_left:
            self.pattern_enabled = not self.pattern_enabled
            self.sfx.play("powerup", 0.7)

        # Button 3: Toggle Ring Slot
        btn_y += 42
        if btn_x <= mx <= btn_x + btn_w and btn_y <= my <= btn_y + btn_h and clicked_left:
            self.active_ring_slot = SLOT_RING_2 if self.active_ring_slot == SLOT_RING_1 else SLOT_RING_1
            self.sfx.play("click", 0.6)

        # Button 4: Auto-Equip Optimal
        btn_y += 42
        if btn_x <= mx <= btn_x + btn_w and btn_y <= my <= btn_y + btn_h and clicked_left:
            self.auto_equip_optimal()

        # Button 5: Reset All
        btn_y += 42
        if btn_x <= mx <= btn_x + btn_w and btn_y <= my <= btn_y + btn_h and clicked_left:
            self._populate_initial_gear_and_stash()

    def _get_equipped_slot_rects(self) -> list:
        px = LEFT_PANEL_X + 14
        py = LEFT_PANEL_Y + 40
        w = 148
        h = 48
        gap_x = 10
        gap_y = 8
        rects = []
        for i in range(SLOT_COUNT):
            row = i // 2
            col = i % 2
            rx = px + col * (w + gap_x)
            ry = py + row * (h + gap_y)
            rects.append((rx, ry, w, h))
        return rects

    def _get_inventory_slot_rects(self) -> list:
        px = RIGHT_PANEL_X + 18
        py = RIGHT_PANEL_Y + 48
        w = 75
        h = 75
        gap_x = 8
        gap_y = 8
        rects = []
        for r in range(INVENTORY_ROWS):
            for c in range(INVENTORY_COLS):
                rx = px + c * (w + gap_x)
                ry = py + r * (h + gap_y)
                rects.append((rx, ry, w, h))
        return rects

    def draw(self):
        begin_drawing()
        clear_background(COLOR_BG)

        # 1. Top HUD Title & Controls Bar
        draw_text("GEAR COMPARE - STAT COMPARISON TOOLTIP", 35, 18, 17, COLOR_GOLD_ACCENT)
        draw_text("Section 3.1: Menus & UI | Side-by-Side Gear Evaluation Architecture", 35, 38, 11, COLOR_TEXT_DIM)

        # Top-Bar Settings Dropdown & Gamepad status
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)

        # 2. Left Panel: Equipped Loadout & Live Stats
        self._draw_left_panel()

        # 3. Center Panel: Combat Target Dummy & Controls
        self._draw_center_panel()

        # 4. Right Panel: Inventory Stash Grid
        self._draw_right_panel()

        # 5. Floating Damage Numbers
        for num in self.floating_numbers:
            if num.active:
                alpha = max(0, min(255, int(255 * (num.timer / num.max_life))))
                nr = getattr(num.color, "r", 255)
                ng = getattr(num.color, "g", 255)
                nb = getattr(num.color, "b", 255)
                col = Color(int(nr), int(ng), int(nb), alpha)
                fsize = int(14 * num.scale)
                draw_text(num.text, int(num.x), int(num.y), fsize, col)

        # 6. Side-by-Side Gear Comparison Tooltip (Rendered on top layer)
        self._draw_comparison_tooltips()

        # 7. Status Message Toast Bar (Bottom Center)
        if self.status_message_timer > 0.0:
            alpha = max(0, min(255, int(255 * min(1.0, self.status_message_timer))))
            draw_rectangle(SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT - 32, 600, 24, Color(16, 24, 40, alpha))
            draw_rectangle_lines(SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT - 32, 600, 24, Color(0, 225, 255, alpha))
            draw_text(self.status_message, SCREEN_WIDTH // 2 - 285, SCREEN_HEIGHT - 26, 11, Color(240, 245, 255, alpha))

        # 8. X-Ray Overlay Drawer ([Tab])
        if self.show_xray:
            candidate = None
            if self.hovered_inventory_slot >= 0:
                candidate = self.inventory[self.hovered_inventory_slot]
            target_slot = self.resolve_target_slot(candidate) if candidate else -1
            equipped = self.equipment.slots[target_slot] if target_slot >= 0 else None
            delta = compute_stat_delta(candidate, equipped)

            draw_xray_overlay(
                candidate,
                equipped,
                delta,
                self.pattern_enabled,
                self.active_ring_slot,
                RIGHT_PANEL_X - 10,
                RIGHT_PANEL_Y,
                RIGHT_PANEL_W + 10,
                RIGHT_PANEL_H
            )

        end_drawing()

    def _draw_left_panel(self):
        """Renders the currently equipped loadout and overall character attributes."""
        px = LEFT_PANEL_X
        py = LEFT_PANEL_Y
        pw = LEFT_PANEL_W
        ph = LEFT_PANEL_H

        draw_rectangle(px, py, pw, ph, COLOR_PANEL_BG)
        draw_rectangle_lines(px, py, pw, ph, COLOR_PANEL_BORDER)

        draw_rectangle(px, py, pw, 26, Color(22, 30, 48, 255))
        draw_text("ACTIVE CHARACTER LOADOUT (10 SLOTS)", px + 14, py + 6, 11, COLOR_CYAN_ACCENT)

        # Draw 10 Equipped Slots
        eq_rects = self._get_equipped_slot_rects()
        for i in range(SLOT_COUNT):
            rx, ry, rw, rh = eq_rects[i]
            is_hovered = (i == self.hovered_equipped_slot)
            item = self.equipment.slots[i]

            bg_col = COLOR_SLOT_HOVER if is_hovered else COLOR_SLOT_EQUIPPED
            border_col = COLOR_CYAN_ACCENT if is_hovered else COLOR_SLOT_BORDER
            draw_rectangle(rx, ry, rw, rh, bg_col)
            draw_rectangle_lines(rx, ry, rw, rh, border_col)

            # Slot anatomical label
            sname = SLOT_NAMES[i].upper()
            draw_text(sname, rx + 6, ry + 4, 8, COLOR_TEXT_DIM)

            if item is not None:
                rarity_col = self._get_rarity_color(item.rarity)
                draw_rectangle_lines(rx + 1, ry + 1, rw - 2, rh - 2, rarity_col)
                disp_name = item.name if len(item.name) <= 14 else item.name[:12] + ".."
                draw_text(disp_name, rx + 6, ry + 16, 10, rarity_col)

                # Stat Chip
                stat_chip = f"Pwr {item.get_power_score()}"
                draw_text(stat_chip, rx + 6, ry + 30, 9, COLOR_GOLD_ACCENT)
                if item.is_two_handed:
                    draw_text("2H", rx + rw - 22, ry + 30, 9, COLOR_RED_ACCENT)
            else:
                draw_text("(Empty)", rx + 8, ry + 20, 10, Color(80, 95, 120, 255))

        # Bottom Sub-Panel: Overall Derived Attributes
        sheet_y = py + 335
        sheet_h = ph - 345
        draw_rectangle(px + 10, sheet_y, pw - 20, sheet_h, Color(12, 16, 26, 255))
        draw_rectangle_lines(px + 10, sheet_y, pw - 20, sheet_h, COLOR_PANEL_BORDER)

        draw_rectangle(px + 10, sheet_y, pw - 20, 22, Color(20, 28, 44, 255))
        draw_text("OVERALL COMBAT ATTRIBUTES", px + 18, sheet_y + 5, 10, COLOR_GOLD_ACCENT)

        sy = sheet_y + 32
        eq = self.equipment

        draw_text("HEALTH POINTS (HP):", px + 20, sy, 11, COLOR_TEXT_MAIN)
        draw_text(f"{eq.effective_hp}", px + 210, sy, 11, COLOR_GREEN_ACCENT)
        sy += 24

        draw_text("ATTACK POWER (ATK):", px + 20, sy, 11, COLOR_TEXT_MAIN)
        draw_text(f"{eq.effective_atk}", px + 210, sy, 12, COLOR_GOLD_ACCENT)
        sy += 24

        draw_text("DEFENSE RATING (DEF):", px + 20, sy, 11, COLOR_TEXT_MAIN)
        draw_text(f"{eq.effective_def}", px + 210, sy, 12, COLOR_CYAN_ACCENT)
        sy += 24

        draw_text("CRITICAL CHANCE:", px + 20, sy, 11, COLOR_TEXT_MAIN)
        draw_text(f"{eq.effective_crit:.1f}%", px + 210, sy, 11, COLOR_PURPLE_ACCENT)
        sy += 24

        draw_text("SPEED RATING (SPD):", px + 20, sy, 11, COLOR_TEXT_MAIN)
        draw_text(f"{eq.effective_spd} px/s", px + 210, sy, 11, COLOR_WHITE)
        sy += 28

        draw_line_ex(Vector2(px + 18, sy), Vector2(px + pw - 18, sy), 1.0, COLOR_PANEL_BORDER)
        sy += 12

        draw_text("TOTAL GEAR POWER:", px + 20, sy, 11, COLOR_TEXT_DIM)
        draw_text(f"{eq.total_power_score} pts", px + 200, sy, 13, COLOR_GOLD_ACCENT)
        sy += 22

        ring_hint = f"Active Compare Ring: {SLOT_NAMES[self.active_ring_slot]} [Alt/Y]"
        draw_text(ring_hint, px + 20, sy, 9, COLOR_CYAN_ACCENT)

    def _draw_center_panel(self):
        """Renders the combat dummy sandbox, dps metrics, and action buttons."""
        cx = CENTER_PANEL_X
        cy = CENTER_PANEL_Y
        cw = CENTER_PANEL_W
        ch = CENTER_PANEL_H

        draw_rectangle(cx, cy, cw, ch, COLOR_PANEL_BG)
        draw_rectangle_lines(cx, cy, cw, ch, COLOR_PANEL_BORDER)

        draw_rectangle(cx, cy, cw, 26, Color(22, 30, 48, 255))
        draw_text("COMBAT TRAINING DUMMY", cx + 14, cy + 6, 12, COLOR_CYAN_ACCENT)

        # Arena
        arena_y = cy + 34
        arena_h = 240
        draw_rectangle(cx + 12, arena_y, cw - 24, arena_h, Color(14, 18, 28, 255))
        draw_rectangle_lines(cx + 12, arena_y, cw - 24, arena_h, COLOR_PANEL_BORDER)

        for gx in range(cx + 25, cx + cw - 20, 35):
            draw_line(gx, arena_y + 1, gx, arena_y + arena_h - 1, Color(22, 30, 46, 255))
        for gy in range(arena_y + 20, arena_y + arena_h, 30):
            draw_line(cx + 13, gy, cx + cw - 13, gy, Color(22, 30, 46, 255))

        self.training_dummy.draw()
        draw_text("Target Dummy (Armor: 25)", cx + 20, arena_y + 10, 10, COLOR_TEXT_DIM)

        # Telemetry
        stats_y = arena_y + arena_h + 12
        draw_rectangle(cx + 12, stats_y, cw - 24, 110, Color(12, 16, 26, 255))
        draw_rectangle_lines(cx + 12, stats_y, cw - 24, 110, COLOR_PANEL_BORDER)

        draw_text("COMBAT TELEMETRY", cx + 20, stats_y + 8, 10, COLOR_GOLD_ACCENT)
        last_hit = self.training_dummy.last_damage_dealt
        last_col = COLOR_GOLD_ACCENT if self.training_dummy.was_last_crit else COLOR_WHITE
        draw_text(f"Last Hit Damage: {last_hit}", cx + 20, stats_y + 28, 12, last_col)

        strikes = self.training_dummy.total_strikes
        total_dmg = self.training_dummy.total_damage_dealt
        avg_dmg = (total_dmg / float(max(1, strikes))) if strikes > 0 else 0.0
        draw_text(f"Total Strikes: {strikes}  |  Avg: {avg_dmg:.1f}", cx + 20, stats_y + 48, 10, COLOR_TEXT_DIM)
        draw_text(f"Cumulative Dmg: {total_dmg}", cx + 20, stats_y + 66, 11, COLOR_CYAN_ACCENT)
        draw_text("Dummy Mitigation: -33.3% damage", cx + 20, stats_y + 86, 9, Color(130, 150, 180, 255))

        # Lab Buttons
        btn_y = cy + 415
        btn_w = cw - 24
        btn_h = 34
        btn_x = cx + 12

        # 1. Attack Dummy
        draw_rectangle(btn_x, btn_y, btn_w, btn_h, Color(30, 75, 125, 255))
        draw_rectangle_lines(btn_x, btn_y, btn_w, btn_h, COLOR_CYAN_ACCENT)
        draw_text("[SPACE / CLICK] TEST STRIKE", btn_x + 35, btn_y + 10, 11, COLOR_WHITE)

        # 2. Toggle Pattern Mode
        btn_y += 42
        pat_bg = Color(20, 80, 45, 255) if self.pattern_enabled else Color(90, 25, 30, 255)
        pat_border = COLOR_GREEN_ACCENT if self.pattern_enabled else COLOR_RED_ACCENT
        draw_rectangle(btn_x, btn_y, btn_w, btn_h, pat_bg)
        draw_rectangle_lines(btn_x, btn_y, btn_w, btn_h, pat_border)
        pat_title = "[F1] COMPARE: SIDE-BY-SIDE" if self.pattern_enabled else "[F1] COMPARE: RAW SINGLE"
        draw_text(pat_title, btn_x + 30, btn_y + 10, 11, pat_border)

        # 3. Toggle Ring Slot
        btn_y += 42
        draw_rectangle(btn_x, btn_y, btn_w, btn_h, Color(24, 34, 54, 255))
        draw_rectangle_lines(btn_x, btn_y, btn_w, btn_h, COLOR_PANEL_BORDER)
        draw_text(f"[ALT / Y] RING: {SLOT_NAMES[self.active_ring_slot]}", btn_x + 45, btn_y + 10, 11, COLOR_CYAN_ACCENT)

        # 4. Auto-Equip Optimal
        btn_y += 42
        draw_rectangle(btn_x, btn_y, btn_w, btn_h, Color(24, 34, 54, 255))
        draw_rectangle_lines(btn_x, btn_y, btn_w, btn_h, COLOR_PANEL_BORDER)
        draw_text("[F2] AUTO-EQUIP BEST", btn_x + 48, btn_y + 10, 11, COLOR_GOLD_ACCENT)

        # 5. Reset All
        btn_y += 42
        draw_rectangle(btn_x, btn_y, btn_w, btn_h, Color(18, 24, 38, 255))
        draw_rectangle_lines(btn_x, btn_y, btn_w, btn_h, COLOR_PANEL_BORDER)
        draw_text("[R] RESET INVENTORY", btn_x + 48, btn_y + 10, 11, COLOR_TEXT_DIM)

    def _draw_right_panel(self):
        """Renders the 24-slot inventory stash grid."""
        rx = RIGHT_PANEL_X
        ry = RIGHT_PANEL_Y
        rw = RIGHT_PANEL_W
        rh = RIGHT_PANEL_H

        draw_rectangle(rx, ry, rw, rh, COLOR_PANEL_BG)
        draw_rectangle_lines(rx, ry, rw, rh, COLOR_PANEL_BORDER)

        draw_rectangle(rx, ry, rw, 26, Color(22, 30, 48, 255))
        draw_text("LOOT STASH INVENTORY (24 SLOTS)", rx + 14, ry + 6, 12, COLOR_CYAN_ACCENT)
        draw_text("Hover to Compare | Click to Equip", rx + rw - 225, ry + 7, 10, COLOR_TEXT_DIM)

        inv_rects = self._get_inventory_slot_rects()
        for i in range(INVENTORY_SLOT_COUNT):
            bx, by, bw, bh = inv_rects[i]
            is_hovered = (i == self.hovered_inventory_slot)
            item = self.inventory[i]

            bg_col = COLOR_SLOT_HOVER if is_hovered else COLOR_SLOT_EMPTY
            border_col = COLOR_CYAN_ACCENT if is_hovered else COLOR_SLOT_BORDER
            draw_rectangle(bx, by, bw, bh, bg_col)
            draw_rectangle_lines(bx, by, bw, bh, border_col)

            if item is not None:
                rarity_col = self._get_rarity_color(item.rarity)
                draw_rectangle_lines(bx + 1, by + 1, bw - 2, bh - 2, rarity_col)

                draw_text(item.icon_glyph[:7], bx + 6, by + 6, 9, COLOR_TEXT_DIM)

                short_name = item.name if len(item.name) <= 10 else item.name[:9] + "."
                draw_text(short_name, bx + 6, by + 22, 10, rarity_col)

                pwr_tag = f"Pwr {item.get_power_score()}"
                draw_text(pwr_tag, bx + 6, by + 42, 9, COLOR_GOLD_ACCENT)

                if item.is_two_handed:
                    draw_text("2H", bx + bw - 18, by + 58, 9, COLOR_RED_ACCENT)

        # Bottom Instructions & Tips
        info_y = ry + 395
        info_h = rh - 405
        draw_rectangle(rx + 14, info_y, rw - 28, info_h, Color(12, 16, 26, 255))
        draw_rectangle_lines(rx + 14, info_y, rw - 28, info_h, COLOR_PANEL_BORDER)

        draw_rectangle(rx + 14, info_y, rw - 28, 22, Color(20, 28, 44, 255))
        draw_text("HOW STAT COMPARISON WORKS", rx + 22, info_y + 5, 10, COLOR_GOLD_ACCENT)

        iy = info_y + 30
        draw_text("1. Hover any stash item to open the Side-by-Side Comparison.", rx + 22, iy, 10, COLOR_TEXT_MAIN)
        iy += 18
        draw_text("2. The Equipped Card (Left) shows what you are currently wearing.", rx + 22, iy, 10, COLOR_TEXT_DIM)
        iy += 18
        draw_text("3. The Candidate Card (Right) shows dynamic delta contrasts:", rx + 22, iy, 10, COLOR_TEXT_MAIN)
        iy += 16
        draw_text("   - Green Up Arrow (▲ +X): Stat Upgrade", rx + 22, iy, 10, COLOR_GREEN_ACCENT)
        iy += 16
        draw_text("   - Red Down Arrow (▼ -X): Stat Downgrade", rx + 22, iy, 10, COLOR_RED_ACCENT)
        iy += 16
        draw_text("   - Muted Tag (= 0): Stat Identical / Neutral", rx + 22, iy, 10, COLOR_TEXT_DIM)
        iy += 20
        draw_text("4. Press [Alt] or Gamepad Y to switch comparison between Ring 1 & Ring 2.", rx + 22, iy, 10, COLOR_CYAN_ACCENT)
        iy += 18
        draw_text("5. Left-Click or press Enter to swap candidate directly into the slot.", rx + 22, iy, 10, COLOR_GOLD_ACCENT)

    def _draw_comparison_tooltips(self):
        """
        Renders the floating side-by-side comparison cards (Equipped vs Candidate)
        or raw candidate card based on pattern toggle, with smart viewport clamping.
        """
        if self.hovered_inventory_slot < 0:
            return

        candidate = self.inventory[self.hovered_inventory_slot]
        if candidate is None:
            return

        target_slot = self.resolve_target_slot(candidate)
        equipped = self.equipment.slots[target_slot] if target_slot >= 0 else None
        delta = compute_stat_delta(candidate, equipped)

        mx = get_mouse_x()
        my = get_mouse_y()

        card_w = 220
        card_h = 245
        gap = 12

        total_w = (card_w * 2 + gap) if self.pattern_enabled else card_w
        total_h = card_h

        tx, ty, flipped_x, flipped_y = calculate_clamped_tooltip_rect(
            mx, my, total_w, total_h, SCREEN_WIDTH, SCREEN_HEIGHT
        )

        if self.pattern_enabled:
            # Side-by-Side Dual Cards
            # Card 1: Currently Equipped
            self._render_single_card(
                tx, ty, card_w, card_h,
                item=equipped,
                title_badge=f"[EQUIPPED: {SLOT_NAMES[target_slot].upper()}]",
                is_equipped_card=True,
                delta=None
            )

            # Card 2: Inventory Candidate
            self._render_single_card(
                tx + card_w + gap, ty, card_w, card_h,
                item=candidate,
                title_badge="[INVENTORY CANDIDATE]",
                is_equipped_card=False,
                delta=delta
            )
        else:
            # Pattern OFF: Naive Single-Item Tooltip (No Comparison)
            self._render_single_card(
                tx, ty, card_w, card_h,
                item=candidate,
                title_badge="[ITEM DETAILS]",
                is_equipped_card=False,
                delta=None
            )

    def _render_single_card(
        self,
        cx: int,
        cy: int,
        cw: int,
        ch: int,
        item: EquipmentItem,
        title_badge: str,
        is_equipped_card: bool,
        delta: StatDelta
    ):
        """Renders an individual tooltip card with attributes and delta arrows."""
        # Backdrop & Border
        bg_color = Color(16, 22, 36, 250) if is_equipped_card else Color(18, 25, 42, 252)
        border_color = Color(60, 80, 120, 255) if is_equipped_card else COLOR_CYAN_ACCENT

        draw_rectangle(cx, cy, cw, ch, bg_color)
        draw_rectangle_lines(cx, cy, cw, ch, border_color)

        # Header Badge
        header_bg = Color(24, 34, 54, 255) if is_equipped_card else Color(30, 48, 78, 255)
        draw_rectangle(cx, cy, cw, 22, header_bg)
        badge_col = COLOR_TEXT_DIM if is_equipped_card else COLOR_CYAN_ACCENT
        draw_text(title_badge, cx + 10, cy + 5, 9, badge_col)

        iy = cy + 28

        if item is None:
            # Empty Slot Card
            draw_text("(Empty Slot)", cx + 14, iy + 20, 12, COLOR_TEXT_DIM)
            draw_text("Any equipped gear will be", cx + 14, iy + 45, 10, COLOR_TEXT_DIM)
            draw_text("a 100% pure stat upgrade.", cx + 14, iy + 60, 10, COLOR_GREEN_ACCENT)
            return

        rarity_col = self._get_rarity_color(item.rarity)
        rarity_str = RARITY_NAMES[item.rarity]

        # Item Title & Rarity Type
        draw_text(item.name, cx + 12, iy, 12, rarity_col)
        draw_text(f"{rarity_str} {TYPE_NAMES[item.item_type]}", cx + 12, iy + 16, 9, COLOR_TEXT_DIM)
        iy += 34

        # Overall Power Score Banner
        power_str = f"Item Power: {item.get_power_score()}"
        draw_text(power_str, cx + 12, iy, 10, COLOR_GOLD_ACCENT)

        if delta is not None and not is_equipped_card:
            pwr_diff = delta.d_power
            pct_diff = delta.pct_power
            if pwr_diff > 0:
                draw_up_arrow(cx + cw - 70, iy + 6, 8, COLOR_GREEN_ACCENT)
                draw_text(f"+{pct_diff:.1f}%", cx + cw - 60, iy, 10, COLOR_GREEN_ACCENT)
            elif pwr_diff < 0:
                draw_down_arrow(cx + cw - 70, iy + 6, 8, COLOR_RED_ACCENT)
                draw_text(f"{pct_diff:.1f}%", cx + cw - 60, iy, 10, COLOR_RED_ACCENT)
            else:
                draw_text("(=)", cx + cw - 45, iy, 10, COLOR_TEXT_DIM)
        iy += 20

        draw_line_ex(Vector2(cx + 10, iy), Vector2(cx + cw - 10, iy), 1.0, Color(40, 55, 85, 255))
        iy += 8

        # Attribute lines with delta markers
        iy = self._draw_stat_line("Attack (ATK)", item.atk, delta.d_atk if delta else None, cx + 12, iy, cw - 24, COLOR_GOLD_ACCENT)
        iy = self._draw_stat_line("Defense (DEF)", item.defense, delta.d_def if delta else None, cx + 12, iy, cw - 24, COLOR_CYAN_ACCENT)
        iy = self._draw_stat_line("Health (HP)", item.hp, delta.d_hp if delta else None, cx + 12, iy, cw - 24, COLOR_GREEN_ACCENT)
        iy = self._draw_stat_line("Critical Strike", f"{item.crit:.1f}%", f"{delta.d_crit:+.1f}%" if delta else None, cx + 12, iy, cw - 24, COLOR_PURPLE_ACCENT, is_crit=True)
        iy = self._draw_stat_line("Speed (SPD)", f"{item.spd:+d}", delta.d_spd if delta else None, cx + 12, iy, cw - 24, COLOR_WHITE)

        # Flavor / Footer
        iy += 6
        flavor_str = f'"{item.flavor}"' if len(item.flavor) <= 32 else f'"{item.flavor[:30]}.."'
        draw_text(flavor_str, cx + 12, iy, 8, Color(125, 145, 175, 255))

    def _draw_stat_line(
        self,
        stat_name: str,
        value,
        diff,
        x: int,
        y: int,
        line_w: int,
        base_color: Color,
        is_crit: bool = False
    ) -> int:
        """Draws an individual stat entry with value and green/red contrast delta arrow."""
        draw_text(stat_name, x, y, 9, COLOR_TEXT_DIM)
        draw_text(str(value), x + 90, y, 9, base_color)

        if diff is not None:
            # Contrast Delta Evaluation
            val_num = 0.0
            if is_crit:
                try:
                    val_num = float(str(diff).replace("%", ""))
                except ValueError:
                    val_num = 0.0
            else:
                try:
                    val_num = float(diff)
                except ValueError:
                    val_num = 0.0

            arrow_x = x + line_w - 45
            if val_num > 0.0:
                draw_up_arrow(arrow_x, y + 5, 7, COLOR_GREEN_ACCENT)
                draw_text(f"+{diff}" if not str(diff).startswith("+") else str(diff), arrow_x + 8, y, 9, COLOR_GREEN_ACCENT)
            elif val_num < 0.0:
                draw_down_arrow(arrow_x, y + 5, 7, COLOR_RED_ACCENT)
                draw_text(str(diff), arrow_x + 8, y, 9, COLOR_RED_ACCENT)
            else:
                draw_text("=", arrow_x + 8, y, 9, COLOR_TEXT_DIM)

        return y + 16

    def _get_rarity_color(self, rarity: int) -> Color:
        if rarity == RARITY_LEGENDARY:
            return COLOR_RARITY_LEGENDARY
        elif rarity == RARITY_EPIC:
            return COLOR_RARITY_EPIC
        elif rarity == RARITY_RARE:
            return COLOR_RARITY_RARE
        return COLOR_RARITY_COMMON

    def run(self, smoke_test: bool = False):
        frame_count = 0
        while not window_should_close():
            if smoke_test and frame_count == 1:
                # Exercise test strike option during smoke test
                self.perform_dummy_strike()
                # Exercise inventory hover
                self.hovered_inventory_slot = 0
            self.update()
            self.draw()
            frame_count += 1
            if smoke_test and frame_count >= 5:
                break
        self.sfx.unload_all()
        close_audio_device()
        close_window()


if __name__ == "__main__":
    is_smoke = "--smoke-test" in sys.argv
    GearCompareLabGame().run(smoke_test=is_smoke)

