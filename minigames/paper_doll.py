# -*- coding: utf-8 -*-
"""
Paper Doll - Equipment Slots & Live Stat Pipeline Architecture
==============================================================
Section          : 3.1 Menus & UI
Pattern Category : Menus & User Interface, RPG Progression & Economy
Dimension        : 2D

Problem Solved:
  In RPGs, action games, and MMOs (World of Warcraft, Diablo, Dark Souls, Baldur's Gate),
  equipment cannot be stored as an arbitrary flat list. Items belong to specific anatomical
  body slots (Head, Chest, Hands, Legs, Feet, Main Hand, Off Hand, Rings, Amulet).
  Naive implementations mutate player stats directly in-place upon equip/unequip, which causes
  permanent stat drift, item duplication, or negative values when items are swapped, broken,
  or subjected to temporary buffs. Furthermore, naive systems fail to enforce physical slot
  constraints (e.g. wielding a shield while holding a Two-Handed Greathammer) or calculate
  multi-item set synergies cleanly.

How the Pattern Works:
  1. Anatomical Slot Matrix:
     Equipment slots are structured as a typed, fixed-capacity array (SLOT_HEAD, SLOT_AMULET,
     SLOT_CHEST, SLOT_MAIN_HAND, SLOT_OFF_HAND, SLOT_HANDS, SLOT_LEGS, SLOT_FEET, SLOT_RING_1, SLOT_RING_2).
     Each item specifies compatible slot types, validated before any equip transaction occurs.
  2. Two-Handed Mutual Exclusion:
     Equipping a Two-Handed (2H) weapon in SLOT_MAIN_HAND atomically unequips and clears SLOT_OFF_HAND
     (or evicts the off-hand shield back to inventory) and locks the off-hand slot. Attempting to equip
     an off-hand item automatically clears or swaps out the two-handed weapon.
  3. Pure Derived Stat Pipeline:
     Base character attributes (HP, ATK, DEF, CRIT, SPD) remain immutable. Derived combat stats are
     computed by a pure functional pipeline:
       Effective_Stat = (Base_Stat + SUM(Gear_Flat) + Set_Bonus_Flat) * (1.0 + Set_Percent)
     Unequipping any piece of gear restores exact base stats with zero floating-point or integer drift.
  4. Multi-Tier Set Synergy Engine:
     Items tag a set identifier ("Vanguard", "Shadow Assassin", "Aetheric Nexus"). The pipeline
     tallies equipped set pieces and unlocks tiered bonuses (e.g., 2-Piece: +25 DEF; 4-Piece: +20% HP
     and Bastion Aegis aura) with live UI badges and visual mannequin particle effects.
  5. Interactive Paper Doll Mannequin & Combat Dummy Sandbox:
     An articulated mannequin dynamically renders procedural 2D primitives for every equipped piece
     (helmets, breastplates, glowing weapons, crest shields, boots). A combat training dummy allows
     testing effective damage, critical strikes, and armor mitigation in real time.

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - Left Click / Enter / Space / Gamepad A : Equip hovered bag item / Unequip gear slot / Strike Dummy
  - WASD / Arrow Keys / Left Stick / D-Pad : Move UI focus cursor between Doll slots & Bag items
  - [Tab] / Gamepad View (Select)          : Toggle X-Ray Telemetry, Memory Matrix & Stat Breakdown
  - [F1]  / Gamepad R3                     : Toggle Pattern ON/OFF (Decoupled Slot Pipeline vs Naive Mutation)
  - [F2]  / Gamepad L3                     : Auto-Equip Optimal Best-in-Slot loadout
  - [F3]  / Gamepad X                      : Unequip All Gear (Strip to base stats)
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
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 3. Mandatory Raylib & modular workspace imports
from pyray import *
from assets import *
from utils import *

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WINDOW_TITLE = "Paper Doll - Equipment Slots & Stat Pipeline (Raylib Pattern Lab)"

# Palette Constants
COLOR_BG               = Color(10, 13, 22, 255)
COLOR_PANEL_BG         = Color(16, 21, 34, 250)
COLOR_PANEL_BORDER     = Color(42, 58, 90, 255)
COLOR_SLOT_EMPTY       = Color(14, 18, 28, 255)
COLOR_SLOT_BORDER      = Color(35, 48, 76, 255)
COLOR_SLOT_HOVER       = Color(65, 95, 145, 255)
COLOR_SLOT_LOCKED      = Color(45, 20, 24, 255)
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
LEFT_PANEL_W  = 485
LEFT_PANEL_H  = 635

CENTER_PANEL_X = 535
CENTER_PANEL_Y = 65
CENTER_PANEL_W = 310
CENTER_PANEL_H = 635

RIGHT_PANEL_X  = 860
RIGHT_PANEL_Y  = 65
RIGHT_PANEL_W  = 385
RIGHT_PANEL_H  = 635

BAG_COLS = 4
BAG_ROWS = 4
BAG_SLOT_COUNT = 16


# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATION (EQUIPMENT SLOTS & PAPER DOLL SYSTEM)
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
          char set_id[24];    // "VANGUARD", "ASSASSIN", "ARCHMAGE", or ""
          bool is_two_handed;
          Color color_primary, color_secondary;
          char icon_glyph[16];
          char flavor[64];
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
        set_id: str = "",
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
        self.set_id = set_id
        self.is_two_handed = is_two_handed
        self.color_primary = color_primary or Color(200, 210, 225, 255)
        self.color_secondary = color_secondary or Color(100, 120, 150, 255)
        self.icon_glyph = icon_glyph
        self.flavor = flavor


class CharacterBaseStats:
    """
    Immutable character baseline attributes.
    A decoupled stat pipeline ensures base stats are never permanently modified
    by temporary gear equip/unequip operations.
    """
    def __init__(self):
        self.base_hp = 300
        self.base_atk = 25
        self.base_def = 15
        self.base_crit = 5.0    # 5.0%
        self.base_spd = 180     # 180 px/s


class EffectiveStats:
    """
    Derived stats calculated dynamically across equipped gear, base attributes,
    and active set synergies.
    """
    def __init__(self):
        self.max_hp = 300
        self.atk = 25
        self.defense = 15
        self.crit = 5.0
        self.spd = 180
        self.damage_reduction_pct = 20.0

        # Detailed breakdown metrics for X-Ray Telemetry Inspector
        self.gear_hp = 0
        self.gear_atk = 0
        self.gear_def = 0
        self.gear_crit = 0.0
        self.gear_spd = 0

        self.set_hp = 0
        self.set_atk = 0
        self.set_def = 0
        self.set_crit = 0.0
        self.set_spd = 0
        self.set_pct_atk = 0.0
        self.set_pct_def = 0.0


class SetBonusTier:
    """
    Represents an unlockable threshold for wearing multiple pieces of a named set.
    """
    def __init__(
        self,
        set_id: str,
        pieces_required: int,
        title: str,
        bonus_atk: int,
        bonus_def: int,
        bonus_hp: int,
        bonus_crit: float,
        bonus_spd: int,
        bonus_pct_atk: float,
        bonus_pct_def: float,
        description: str
    ):
        self.set_id = set_id
        self.pieces_required = pieces_required
        self.title = title
        self.bonus_atk = bonus_atk
        self.bonus_def = bonus_def
        self.bonus_hp = bonus_hp
        self.bonus_crit = bonus_crit
        self.bonus_spd = bonus_spd
        self.bonus_pct_atk = bonus_pct_atk
        self.bonus_pct_def = bonus_pct_def
        self.description = description


class PaperDoll:
    """
    Manages anatomical equipment slots, constraint validation (e.g. 2H mutex),
    and the pure derived stat pipeline.
    C++ Equivalent:
      class PaperDoll {
          EquipmentItem* slots[SLOT_COUNT];
          CharacterBaseStats base_stats;
          EffectiveStats effective_stats;
          bool is_offhand_locked;
          bool is_dirty;
          ...
      };
    """
    def __init__(self):
        # Fixed-capacity slot array (C++ std::array<EquipmentItem*, 10>)
        self.slots = [None] * SLOT_COUNT
        self.base_stats = CharacterBaseStats()
        self.effective_stats = EffectiveStats()

        # Two-Handed weapon mutex lock state
        self.is_offhand_locked = False

        # Dirty flag: triggers O(N) recalculation only when equipment changes
        self.is_dirty = True

        # Active set bonuses list
        self.active_set_tiers = []

        # Naive mutation simulation variables (for [F1] pattern comparison)
        self.naive_stats = EffectiveStats()
        self.naive_drift_count = 0
        self.accumulated_drift_atk = 0
        self.accumulated_drift_def = 0

        # Define canonical set bonus tables
        self.set_bonus_definitions = [
            # 1. Iron Vanguard (Tank / Bastion Defense)
            SetBonusTier("VANGUARD", 2, "Iron Bastion", 0, 25, 40, 0.0, 0, 0.0, 0.0, "+25 DEF & +40 Max HP"),
            SetBonusTier("VANGUARD", 4, "Bastion Aegis", 0, 0, 60, 0.0, 0, 0.0, 0.25, "+25% Total DEF & Holy Aegis Aura"),

            # 2. Shadow Assassin (Crit / Mobility Burst)
            SetBonusTier("ASSASSIN", 2, "Lethality", 18, 0, 0, 12.0, 15, 0.0, 0.0, "+12% CRIT, +18 ATK & +15 SPD"),
            SetBonusTier("ASSASSIN", 4, "Shadowstep", 35, 0, 0, 0.0, 35, 0.0, 0.0, "+35 ATK & Shadowstep (+35 SPD & Wisps)"),

            # 3. Aetheric Nexus (High Magic / Raw Amplification)
            SetBonusTier("ARCHMAGE", 2, "Arcane Flow", 28, 0, 50, 5.0, 0, 0.0, 0.0, "+28 ATK, +50 HP & +5% CRIT"),
            SetBonusTier("ARCHMAGE", 4, "Spell-Weaving", 0, 0, 0, 8.0, 0, 0.25, 0.0, "+25% Total ATK & Arcane Nova")
        ]

        self.recalculate_stats()

    def is_item_compatible_with_slot(self, item: EquipmentItem, slot_idx: int) -> bool:
        """
        Validates whether an item's archetype can fit into the designated anatomical slot.
        """
        if item is None:
            return True

        itype = item.item_type
        if slot_idx == SLOT_HEAD:
            return itype == TYPE_HEAD
        elif slot_idx == SLOT_AMULET:
            return itype == TYPE_AMULET
        elif slot_idx == SLOT_CHEST:
            return itype == TYPE_CHEST
        elif slot_idx == SLOT_MAIN_HAND:
            return itype == TYPE_MAIN_HAND
        elif slot_idx == SLOT_OFF_HAND:
            return itype == TYPE_OFF_HAND
        elif slot_idx == SLOT_HANDS:
            return itype == TYPE_HANDS
        elif slot_idx == SLOT_LEGS:
            return itype == TYPE_LEGS
        elif slot_idx == SLOT_FEET:
            return itype == TYPE_FEET
        elif slot_idx == SLOT_RING_1 or slot_idx == SLOT_RING_2:
            return itype == TYPE_RING

        return False

    def find_best_slot_for_item(self, item: EquipmentItem) -> int:
        """
        Determines the target slot for quick-equipping an item from inventory.
        Handles dual ring resolution (prefers empty ring slot, then weaker ring).
        """
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
            if self.slots[SLOT_RING_1] is None:
                return SLOT_RING_1
            elif self.slots[SLOT_RING_2] is None:
                return SLOT_RING_2
            else:
                # Replace the ring with lower ATK + DEF + HP score
                r1 = self.slots[SLOT_RING_1]
                r2 = self.slots[SLOT_RING_2]
                score1 = r1.atk + r1.defense + int(r1.hp * 0.2)
                score2 = r2.atk + r2.defense + int(r2.hp * 0.2)
                return SLOT_RING_1 if score1 <= score2 else SLOT_RING_2

        return -1

    def equip_item(
        self,
        item: EquipmentItem,
        target_slot: int = -1,
        bag_ref: list = None,
        pattern_enabled: bool = True
    ) -> EquipmentItem:
        """
        Equips an item atomically.
        In Robust Pattern mode (pattern_enabled=True):
          - Validates type compatibility.
          - Enforces Two-Handed mutual exclusion (evicts off-hand shield to bag if equipping 2H weapon;
            unequips 2H weapon if equipping off-hand).
          - Sets dirty flag and triggers pure stat pipeline.
        In Naive Mutation mode (pattern_enabled=False):
          - Simulates hardcoded state bugs: permits cross-slot placement, ignores 2H mutex,
            and accumulates stat desync drift.
        """
        if item is None:
            return None

        if target_slot < 0:
            target_slot = self.find_best_slot_for_item(item)

        if target_slot < 0 or target_slot >= SLOT_COUNT:
            return item  # Invalid slot, return item untouched

        if pattern_enabled:
            # 1. Type validation
            if not self.is_item_compatible_with_slot(item, target_slot):
                return item  # Rejection: incompatible slot

            evicted_offhand = None

            # 2. Two-Handed Weapon Mutex Rule
            if target_slot == SLOT_MAIN_HAND:
                if item.is_two_handed:
                    # Equipping 2H weapon locks off-hand and evicts any existing off-hand item
                    if self.slots[SLOT_OFF_HAND] is not None:
                        evicted_offhand = self.slots[SLOT_OFF_HAND]
                        self.slots[SLOT_OFF_HAND] = None
                    self.is_offhand_locked = True
                else:
                    self.is_offhand_locked = False

            elif target_slot == SLOT_OFF_HAND:
                # Cannot equip off-hand while holding 2H weapon: must unequip 2H weapon first
                main_item = self.slots[SLOT_MAIN_HAND]
                if main_item is not None and main_item.is_two_handed:
                    # Evict the 2H weapon to bag
                    evicted_2h = self.slots[SLOT_MAIN_HAND]
                    self.slots[SLOT_MAIN_HAND] = None
                    self.is_offhand_locked = False
                    if bag_ref is not None:
                        self._put_in_bag(evicted_2h, bag_ref)

            # 3. If off-hand was evicted by 2H weapon, deposit it into bag
            if evicted_offhand is not None and bag_ref is not None:
                self._put_in_bag(evicted_offhand, bag_ref)

            # 4. Atomic Swap: Evict existing item in target slot
            old_item = self.slots[target_slot]
            self.slots[target_slot] = item
            self.is_dirty = True
            self.recalculate_stats()
            return old_item

        else:
            # NAIVE DIRECT MUTATION MODE (Demonstrates unarchitected bugs)
            old_item = self.slots[target_slot]
            self.slots[target_slot] = item

            # Simulate stat drift glitch: in-place direct arithmetic without pure source of truth
            self.naive_drift_count += 1
            drift = random.choice([-2, 1, -1, 2])
            self.accumulated_drift_atk += drift
            self.accumulated_drift_def -= drift

            # Direct in-place mutation bug
            if old_item is not None:
                self.naive_stats.atk -= old_item.atk
                self.naive_stats.defense -= old_item.defense
                self.naive_stats.max_hp -= old_item.hp

            self.naive_stats.atk += item.atk + drift
            self.naive_stats.defense += item.defense - drift
            self.naive_stats.max_hp += item.hp
            return old_item

    def unequip_item(self, slot_idx: int, pattern_enabled: bool = True) -> EquipmentItem:
        """
        Removes and returns an item from an equipment slot.
        Restores exact base stats deterministically in Robust mode.
        """
        if slot_idx < 0 or slot_idx >= SLOT_COUNT:
            return None

        old_item = self.slots[slot_idx]
        if old_item is None:
            return None

        self.slots[slot_idx] = None

        if pattern_enabled:
            # If removing main hand 2H weapon, unlock off-hand slot
            if slot_idx == SLOT_MAIN_HAND and old_item.is_two_handed:
                self.is_offhand_locked = False

            self.is_dirty = True
            self.recalculate_stats()
        else:
            # Naive in-place subtraction with simulated drift
            self.naive_drift_count += 1
            drift = random.choice([-1, 1])
            self.accumulated_drift_atk += drift
            self.naive_stats.atk -= (old_item.atk + drift)
            self.naive_stats.defense -= old_item.defense
            self.naive_stats.max_hp -= old_item.hp

        return old_item

    def _put_in_bag(self, item: EquipmentItem, bag: list):
        """Helper to place an evicted item in the first free bag slot."""
        if item is None or bag is None:
            return
        for i in range(len(bag)):
            if bag[i] is None:
                bag[i] = item
                return

    def recalculate_stats(self):
        """
        Pure functional stat calculation pipeline:
          Effective = (Base + Gear_Flat + Set_Flat) * (1.0 + Set_Percent)
        Ensures 100% determinism with zero cumulative drift.
        """
        if not self.is_dirty:
            return

        # 1. Reset metrics to immutable base
        self.effective_stats.max_hp = self.base_stats.base_hp
        self.effective_stats.atk = self.base_stats.base_atk
        self.effective_stats.defense = self.base_stats.base_def
        self.effective_stats.crit = self.base_stats.base_crit
        self.effective_stats.spd = self.base_stats.base_spd

        self.effective_stats.gear_hp = 0
        self.effective_stats.gear_atk = 0
        self.effective_stats.gear_def = 0
        self.effective_stats.gear_crit = 0.0
        self.effective_stats.gear_spd = 0

        self.effective_stats.set_hp = 0
        self.effective_stats.set_atk = 0
        self.effective_stats.set_def = 0
        self.effective_stats.set_crit = 0.0
        self.effective_stats.set_spd = 0
        self.effective_stats.set_pct_atk = 0.0
        self.effective_stats.set_pct_def = 0.0

        # 2. Accumulate flat gear bonuses across all 10 anatomical slots
        set_counts = {}
        for slot in self.slots:
            if slot is not None:
                self.effective_stats.gear_hp += slot.hp
                self.effective_stats.gear_atk += slot.atk
                self.effective_stats.gear_def += slot.defense
                self.effective_stats.gear_crit += slot.crit
                self.effective_stats.gear_spd += slot.spd

                # Tally set piece occurrences
                if slot.set_id != "":
                    if slot.set_id in set_counts:
                        set_counts[slot.set_id] += 1
                    else:
                        set_counts[slot.set_id] = 1

        # 3. Evaluate multi-tier set synergies
        self.active_set_tiers.clear()
        for tier in self.set_bonus_definitions:
            equipped_count = set_counts.get(tier.set_id, 0)
            if equipped_count >= tier.pieces_required:
                self.active_set_tiers.append(tier)
                self.effective_stats.set_hp += tier.bonus_hp
                self.effective_stats.set_atk += tier.bonus_atk
                self.effective_stats.set_def += tier.bonus_def
                self.effective_stats.set_crit += tier.bonus_crit
                self.effective_stats.set_spd += tier.bonus_spd
                self.effective_stats.set_pct_atk += tier.bonus_pct_atk
                self.effective_stats.set_pct_def += tier.bonus_pct_def

        # 4. Synthesize final effective attributes
        flat_hp = self.base_stats.base_hp + self.effective_stats.gear_hp + self.effective_stats.set_hp
        flat_atk = self.base_stats.base_atk + self.effective_stats.gear_atk + self.effective_stats.set_atk
        flat_def = self.base_stats.base_def + self.effective_stats.gear_def + self.effective_stats.set_def
        flat_crit = self.base_stats.base_crit + self.effective_stats.gear_crit + self.effective_stats.set_crit
        flat_spd = self.base_stats.base_spd + self.effective_stats.gear_spd + self.effective_stats.set_spd

        self.effective_stats.max_hp = flat_hp
        self.effective_stats.atk = int(flat_atk * (1.0 + self.effective_stats.set_pct_atk))
        self.effective_stats.defense = int(flat_def * (1.0 + self.effective_stats.set_pct_def))
        self.effective_stats.crit = flat_crit
        self.effective_stats.spd = max(60, flat_spd)

        # Standard RPG Diminishing Return Armor Mitigation: DEF / (DEF + 60)
        self.effective_stats.damage_reduction_pct = (
            self.effective_stats.defense / (self.effective_stats.defense + 60.0)
        ) * 100.0

        # Sync naive stats initial state
        if self.naive_drift_count == 0:
            self.naive_stats.max_hp = self.effective_stats.max_hp
            self.naive_stats.atk = self.effective_stats.atk
            self.naive_stats.defense = self.effective_stats.defense
            self.naive_stats.crit = self.effective_stats.crit
            self.naive_stats.spd = self.effective_stats.spd
            self.naive_stats.damage_reduction_pct = self.effective_stats.damage_reduction_pct

        self.is_dirty = False

    def auto_equip_optimal(self, bag: list):
        """
        Greedy Best-in-Slot heuristic:
        Iterates available inventory items and equips the highest stat value item for each slot.
        """
        # First gather all items from slots + bag
        all_items = []
        for i in range(SLOT_COUNT):
            if self.slots[i] is not None:
                all_items.append(self.slots[i])
                self.slots[i] = None

        for i in range(len(bag)):
            if bag[i] is not None:
                all_items.append(bag[i])
                bag[i] = None

        self.is_offhand_locked = False

        # Sort items by overall power score descending: ATK + DEF + HP*0.2 + CRIT*2
        for item in all_items:
            item._sort_score = item.atk + item.defense + int(item.hp * 0.2) + int(item.crit * 2.0)

        # Bubble sort for explicit C++ style sorting
        n = len(all_items)
        for i in range(n):
            for j in range(0, n - i - 1):
                if all_items[j]._sort_score < all_items[j + 1]._sort_score:
                    temp = all_items[j]
                    all_items[j] = all_items[j + 1]
                    all_items[j + 1] = temp

        unassigned = []
        for item in all_items:
            placed = False
            best_slot = self.find_best_slot_for_item(item)
            if best_slot >= 0:
                if best_slot == SLOT_OFF_HAND and self.is_offhand_locked:
                    placed = False
                elif self.slots[best_slot] is None:
                    self.slots[best_slot] = item
                    if best_slot == SLOT_MAIN_HAND and item.is_two_handed:
                        self.is_offhand_locked = True
                    placed = True

            if not placed:
                unassigned.append(item)

        # Put remaining unassigned items back into bag
        for i in range(min(len(bag), len(unassigned))):
            bag[i] = unassigned[i]

        self.is_dirty = True
        self.recalculate_stats()

    def unequip_all(self, bag: list):
        """Strips all equipped gear back into the inventory bag."""
        for i in range(SLOT_COUNT):
            if self.slots[i] is not None:
                item = self.slots[i]
                self.slots[i] = None
                self._put_in_bag(item, bag)

        self.is_offhand_locked = False
        self.is_dirty = True
        self.recalculate_stats()


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
    """
    Combat target dummy providing real-time tactile validation of Paper Doll stats.
    """
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.w = 120
        self.h = 160
        self.base_armor = 20  # Dummy has 20 baseline defense
        self.hit_timer = 0.0
        self.shake_x = 0.0
        self.last_damage_dealt = 0
        self.total_damage_dealt = 0
        self.total_strikes = 0
        self.was_last_crit = False

    def take_hit(self, effective_atk: int, effective_crit: float) -> tuple:
        """
        Calculates damage dealt using Paper Doll combat attributes.
        Returns: (damage_int, is_crit_bool)
        """
        self.hit_timer = 0.28
        self.total_strikes += 1

        # 1. Base roll with +/- 8% random variance
        variance = random.uniform(0.92, 1.08)
        raw_damage = max(1, effective_atk) * variance

        # 2. Critical strike roll
        crit_roll = random.uniform(0.0, 100.0)
        is_crit = crit_roll < effective_crit
        crit_multiplier = 2.0 if is_crit else 1.0

        # 3. Apply Dummy's armor mitigation: Raw * (1 - Dummy_Armor / (Dummy_Armor + 50))
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
            # Elastic spring vibration
            self.shake_x = math.sin(self.hit_timer * 38.0) * (self.hit_timer / 0.28) * 14.0
        else:
            self.shake_x = 0.0

    def draw(self):
        cx = int(self.x + self.shake_x)
        cy = int(self.y)

        # 1. Wooden Base & Pedestal
        draw_rectangle(cx - 35, cy + 130, 70, 14, Color(75, 45, 25, 255))
        draw_line_ex(Vector2(cx - 35, cy + 130), Vector2(cx, cy + 80), 4.0, Color(95, 60, 35, 255))
        draw_line_ex(Vector2(cx + 35, cy + 130), Vector2(cx, cy + 80), 4.0, Color(95, 60, 35, 255))
        draw_rectangle(cx - 8, cy + 20, 16, 110, Color(110, 70, 40, 255))

        # 2. Straw Torso with Leather Straps
        draw_circle(cx, cy + 45, 34, Color(185, 145, 85, 255))
        draw_circle_lines(cx, cy + 45, 34, Color(140, 105, 55, 255))
        # Concentric Bullseye Rings
        draw_circle(cx, cy + 45, 24, Color(220, 60, 60, 255))
        draw_circle(cx, cy + 45, 16, Color(245, 245, 245, 255))
        draw_circle(cx, cy + 45, 8, Color(220, 60, 60, 255))

        # 3. Wooden Outstretched Arms
        draw_rectangle(cx - 52, cy + 30, 104, 10, Color(125, 80, 45, 255))
        draw_circle(cx - 52, cy + 35, 6, Color(90, 55, 30, 255))
        draw_circle(cx + 52, cy + 35, 6, Color(90, 55, 30, 255))

        # 4. Iron Training Pot Helmet
        draw_circle(cx, cy - 8, 16, Color(135, 145, 165, 255))
        draw_rectangle(cx - 14, cy - 8, 28, 14, Color(105, 115, 135, 255))
        draw_rectangle(cx - 10, cy - 2, 20, 4, Color(25, 30, 40, 255))  # Visor slit

        # Flash on hit
        if self.hit_timer > 0.15:
            draw_circle(cx, cy + 45, 38, Color(255, 255, 255, 80))


def draw_mannequin(
    cx: int,
    cy: int,
    paper_doll: PaperDoll,
    anim_timer: float,
    attack_anim: float
):
    """
    Renders an articulated 2D anatomical mannequin silhouette dressed with
    the procedural primitive gear currently equipped in the Paper Doll.
    """
    breath_bob = math.sin(anim_timer * 2.2) * 2.5
    swing_angle = math.sin(attack_anim * math.pi) * 45.0  # Weapon slash rotation

    head_y = cy - 65 + breath_bob
    torso_y = cy - 25 + breath_bob

    # 1. Shadow beneath mannequin
    draw_circle(cx, cy + 85, 38, Color(5, 8, 15, 180))

    # 2. Base Anatomical Silhouette (Wooden/Neutral Mannequin)
    # Legs (Shins & Thighs)
    draw_line_ex(Vector2(cx - 14, cy + 18 + breath_bob), Vector2(cx - 16, cy + 78), 8.0, Color(85, 95, 120, 255))
    draw_line_ex(Vector2(cx + 14, cy + 18 + breath_bob), Vector2(cx + 16, cy + 78), 8.0, Color(85, 95, 120, 255))

    # Feet
    draw_circle(cx - 18, cy + 80, 7, Color(60, 70, 90, 255))
    draw_circle(cx + 18, cy + 80, 7, Color(60, 70, 90, 255))

    # Torso & Hips
    draw_rectangle(cx - 18, int(torso_y), 36, 42, Color(75, 88, 115, 255))
    draw_rectangle_lines(cx - 18, int(torso_y), 36, 42, Color(45, 55, 75, 255))

    # Head & Neck
    draw_rectangle(cx - 4, int(head_y + 16), 8, 10, Color(65, 75, 100, 255))
    draw_circle(cx, int(head_y), 17, Color(85, 95, 120, 255))
    draw_circle_lines(cx, int(head_y), 17, Color(45, 55, 75, 255))

    # Arms
    # Left Arm (Off-Hand / Shield side)
    left_hand = Vector2(cx - 36, torso_y + 28)
    draw_line_ex(Vector2(cx - 18, torso_y + 6), left_hand, 6.0, Color(80, 92, 118, 255))
    draw_circle(int(left_hand.x), int(left_hand.y), 6, Color(65, 75, 100, 255))

    # Right Arm (Main-Hand / Weapon side - swings during attack)
    right_shoulder = Vector2(cx + 18, torso_y + 6)
    rad_swing = math.radians(swing_angle)
    arm_dx = math.cos(rad_swing) * 22.0 + math.sin(rad_swing) * 12.0
    arm_dy = math.sin(rad_swing) * 22.0 + 20.0
    right_hand = Vector2(right_shoulder.x + arm_dx, right_shoulder.y + arm_dy)
    draw_line_ex(right_shoulder, right_hand, 6.0, Color(80, 92, 118, 255))
    draw_circle(int(right_hand.x), int(right_hand.y), 6, Color(65, 75, 100, 255))

    # =========================================================================
    # 3. OVERLAID PROCEDURAL GEAR PRIMITIVES
    # =========================================================================

    # --- FEET (Boots) ---
    feet_item = paper_doll.slots[SLOT_FEET]
    if feet_item is not None:
        draw_rectangle(cx - 24, cy + 72, 14, 12, feet_item.color_primary)
        draw_rectangle(cx + 10, cy + 72, 14, 12, feet_item.color_primary)
        draw_circle(cx - 21, cy + 82, 6, feet_item.color_secondary)
        draw_circle(cx + 21, cy + 82, 6, feet_item.color_secondary)

    # --- LEGS (Greaves) ---
    legs_item = paper_doll.slots[SLOT_LEGS]
    if legs_item is not None:
        draw_rectangle(cx - 20, int(cy + 24 + breath_bob), 11, 46, legs_item.color_primary)
        draw_rectangle(cx + 9, int(cy + 24 + breath_bob), 11, 46, legs_item.color_primary)
        draw_line_ex(Vector2(cx - 15, cy + 24 + breath_bob), Vector2(cx - 15, cy + 70 + breath_bob), 2.0, legs_item.color_secondary)
        draw_line_ex(Vector2(cx + 15, cy + 24 + breath_bob), Vector2(cx + 15, cy + 70 + breath_bob), 2.0, legs_item.color_secondary)

    # --- CHEST (Armor Plate / Robes) ---
    chest_item = paper_doll.slots[SLOT_CHEST]
    if chest_item is not None:
        draw_rectangle(cx - 20, int(torso_y - 2), 40, 44, chest_item.color_primary)
        draw_rectangle_lines(cx - 20, int(torso_y - 2), 40, 44, chest_item.color_secondary)
        # Shoulder Pauldrons
        draw_circle(cx - 20, int(torso_y + 4), 9, chest_item.color_secondary)
        draw_circle(cx + 20, int(torso_y + 4), 9, chest_item.color_secondary)
        # Emblem
        draw_circle(cx, int(torso_y + 18), 7, chest_item.color_secondary)

    # --- AMULET (Neck Chain & Gem) ---
    amulet_item = paper_doll.slots[SLOT_AMULET]
    if amulet_item is not None:
        draw_circle(cx, int(head_y + 24), 5, amulet_item.color_primary)
        draw_circle(cx, int(head_y + 24), 2, COLOR_WHITE)

    # --- HEAD (Helmet / Crown) ---
    head_item = paper_doll.slots[SLOT_HEAD]
    if head_item is not None:
        draw_circle(cx, int(head_y - 2), 19, head_item.color_primary)
        draw_rectangle(cx - 16, int(head_y - 4), 32, 12, head_item.color_secondary)
        draw_rectangle(cx - 12, int(head_y), 24, 4, Color(20, 25, 35, 255))  # Visor
        # Crown or crest spikes
        draw_line_ex(Vector2(cx, head_y - 20), Vector2(cx, head_y - 28), 3.0, head_item.color_secondary)
        draw_line_ex(Vector2(cx - 10, head_y - 18), Vector2(cx - 14, head_y - 26), 2.5, head_item.color_secondary)
        draw_line_ex(Vector2(cx + 10, head_y - 18), Vector2(cx + 14, head_y - 26), 2.5, head_item.color_secondary)

    # --- HANDS (Gauntlets) ---
    hands_item = paper_doll.slots[SLOT_HANDS]
    if hands_item is not None:
        draw_circle(int(left_hand.x), int(left_hand.y), 8, hands_item.color_primary)
        draw_circle(int(right_hand.x), int(right_hand.y), 8, hands_item.color_primary)

    # --- RINGS (Glints on fingers) ---
    if paper_doll.slots[SLOT_RING_1] is not None:
        draw_circle(int(left_hand.x - 3), int(left_hand.y + 4), 3, paper_doll.slots[SLOT_RING_1].color_primary)
    if paper_doll.slots[SLOT_RING_2] is not None:
        draw_circle(int(right_hand.x + 3), int(right_hand.y + 4), 3, paper_doll.slots[SLOT_RING_2].color_primary)

    # --- OFF-HAND (Shield / Focus) ---
    offhand_item = paper_doll.slots[SLOT_OFF_HAND]
    if offhand_item is not None:
        sx = int(left_hand.x - 8)
        sy = int(left_hand.y)
        # Heraldic Shield shape
        draw_rectangle(sx - 12, sy - 18, 24, 30, offhand_item.color_primary)
        draw_rectangle_lines(sx - 12, sy - 18, 24, 30, offhand_item.color_secondary)
        draw_circle(sx, sy - 2, 7, offhand_item.color_secondary)
    elif paper_doll.is_offhand_locked:
        # Visual lock badge if 2H weapon is equipped
        draw_circle(int(left_hand.x), int(left_hand.y), 10, Color(220, 45, 55, 120))
        draw_text("2H", int(left_hand.x - 7), int(left_hand.y - 5), 10, COLOR_WHITE)

    # --- MAIN-HAND (Weapon) ---
    main_item = paper_doll.slots[SLOT_MAIN_HAND]
    if main_item is not None:
        wx = right_hand.x
        wy = right_hand.y
        rad = math.radians(-35.0 + swing_angle)
        dx = math.cos(rad)
        dy = math.sin(rad)

        if main_item.is_two_handed:
            # Massive 2-Handed Weapon (Greathammer or Colossus Staff)
            w_len = 68.0
            tip_x = wx + dx * w_len
            tip_y = wy + dy * w_len
            draw_line_ex(Vector2(wx, wy), Vector2(tip_x, tip_y), 6.0, Color(85, 55, 30, 255))
            # Heavy Hammer Head or Staff Orb
            draw_rectangle(int(tip_x - 12), int(tip_y - 12), 24, 24, main_item.color_primary)
            draw_rectangle_lines(int(tip_x - 12), int(tip_y - 12), 24, 24, main_item.color_secondary)
            draw_circle(int(tip_x), int(tip_y), 6, main_item.color_secondary)
        else:
            # 1-Handed Sword or Dagger
            w_len = 45.0
            tip_x = wx + dx * w_len
            tip_y = wy + dy * w_len
            draw_line_ex(Vector2(wx, wy), Vector2(tip_x, tip_y), 4.0, main_item.color_primary)
            draw_line_ex(Vector2(wx + dx * 10, wy + dy * 10 - 8), Vector2(wx + dx * 10, wy + dy * 10 + 8), 3.0, main_item.color_secondary)
            draw_circle(int(wx), int(wy), 4, main_item.color_secondary)

    # =========================================================================
    # 4. ACTIVE SET SYNERGY AURA EFFECTS
    # =========================================================================
    for tier in paper_doll.active_set_tiers:
        if tier.set_id == "VANGUARD" and tier.pieces_required == 4:
            # Golden Aegis Barrier Shield
            rot = anim_timer * 1.5
            draw_circle_lines(cx, int(torso_y + 12), 52, Color(255, 215, 60, 160))
            draw_circle(int(cx + math.cos(rot) * 52), int(torso_y + 12 + math.sin(rot) * 52), 5, COLOR_GOLD_ACCENT)
        elif tier.set_id == "ASSASSIN" and tier.pieces_required == 4:
            # Purple Shadowstep Wisps
            wisp_y = cy + 60 + math.sin(anim_timer * 6.0) * 8.0
            draw_circle(cx - 28, int(wisp_y), 4, COLOR_PURPLE_ACCENT)
            draw_circle(cx + 28, int(wisp_y), 4, COLOR_PURPLE_ACCENT)
        elif tier.set_id == "ARCHMAGE" and tier.pieces_required == 4:
            # Cyan Arcane Nova Sparks
            rot = -anim_timer * 2.5
            draw_circle(int(cx + math.cos(rot) * 44), int(head_y + math.sin(rot) * 44), 4, COLOR_CYAN_ACCENT)


# ==============================================================================
# BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY ([Tab] & [F1])
# ==============================================================================

def draw_xray_overlay(
    paper_doll: PaperDoll,
    pattern_enabled: bool,
    x: int,
    y: int,
    w: int,
    h: int
):
    """
    Renders the live educational X-Ray Telemetry Inspector showing:
      1. Equipment Memory Layout (C++ struct mapping)
      2. Step-by-step stat pipeline arithmetic
      3. Two-handed mutual exclusion state
      4. Set synergy counters
      5. State drift & corruption tracker in Naive mode
    """
    draw_rectangle(x, y, w, h, Color(14, 18, 30, 245))
    draw_rectangle_lines(x, y, w, h, COLOR_CYAN_ACCENT)

    # Header
    draw_rectangle(x, y, w, 28, Color(20, 32, 54, 255))
    draw_text("X-RAY INSPECTOR: EQUIPMENT SLOTS & STAT PIPELINE", x + 12, y + 7, 13, COLOR_CYAN_ACCENT)
    draw_text("[Tab] Close", x + w - 85, y + 7, 11, COLOR_TEXT_DIM)

    cur_y = y + 36

    # 1. Architecture & Memory Layout
    draw_text("1. MEMORY & C++ STRUCT ALIGNMENT", x + 12, cur_y, 11, COLOR_GOLD_ACCENT)
    cur_y += 16
    draw_text("struct PaperDoll { EquipmentItem* slots[10]; EffectiveStats stats; };", x + 18, cur_y, 10, COLOR_TEXT_MAIN)
    cur_y += 14
    draw_text("Fixed array ensures O(1) slot indexing with zero dynamic allocations per frame.", x + 18, cur_y, 10, COLOR_TEXT_DIM)
    cur_y += 20

    # 2. Mathematical Pipeline Breakdown
    draw_text("2. PURE STAT PIPELINE FORMULAS", x + 12, cur_y, 11, COLOR_GOLD_ACCENT)
    cur_y += 16
    stats = paper_doll.effective_stats
    base = paper_doll.base_stats

    atk_line = f"ATK = ({base.base_atk} + Gear:{stats.gear_atk} + Set:{stats.set_atk}) * (1.0 + {stats.set_pct_atk:.2f}) = {stats.atk}"
    draw_text(atk_line, x + 18, cur_y, 11, COLOR_GREEN_ACCENT)
    cur_y += 15

    def_line = f"DEF = ({base.base_def} + Gear:{stats.gear_def} + Set:{stats.set_def}) * (1.0 + {stats.set_pct_def:.2f}) = {stats.defense}"
    draw_text(def_line, x + 18, cur_y, 11, COLOR_GREEN_ACCENT)
    cur_y += 15

    dr_line = f"Mitigation = DEF / (DEF + 60) = {stats.damage_reduction_pct:.1f}% reduction"
    draw_text(dr_line, x + 18, cur_y, 11, COLOR_CYAN_ACCENT)
    cur_y += 15

    crit_line = f"CRIT = Base:{base.base_crit}% + Gear:{stats.gear_crit:.1f}% + Set:{stats.set_crit:.1f}% = {stats.crit:.1f}%"
    draw_text(crit_line, x + 18, cur_y, 11, COLOR_TEXT_MAIN)
    cur_y += 20

    # 3. Two-Handed Weapon Mutex State
    draw_text("3. TWO-HANDED MUTEX STATE", x + 12, cur_y, 11, COLOR_GOLD_ACCENT)
    cur_y += 16
    main_item = paper_doll.slots[SLOT_MAIN_HAND]
    is_2h = (main_item is not None and main_item.is_two_handed)
    lock_str = "LOCKED (Mutual Exclusion Active)" if paper_doll.is_offhand_locked else "FREE / COMPATIBLE"
    lock_col = COLOR_RED_ACCENT if paper_doll.is_offhand_locked else COLOR_GREEN_ACCENT
    draw_text(f"Main Hand 2-Handed: {is_2h}  |  Off-Hand Slot: {lock_str}", x + 18, cur_y, 11, lock_col)
    cur_y += 14
    draw_text("Rule: SLOT_MAIN_HAND(2H) asserts SLOT_OFF_HAND == NULL atomically.", x + 18, cur_y, 10, COLOR_TEXT_DIM)
    cur_y += 20

    # 4. Set Synergy Tracker
    draw_text("4. SET SYNERGY TALLY & BONUSES", x + 12, cur_y, 11, COLOR_GOLD_ACCENT)
    cur_y += 16
    set_counts = {"VANGUARD": 0, "ASSASSIN": 0, "ARCHMAGE": 0}
    for s in paper_doll.slots:
        if s is not None and s.set_id in set_counts:
            set_counts[s.set_id] += 1

    tally_str = f"Vanguard: {set_counts['VANGUARD']}/4  |  Assassin: {set_counts['ASSASSIN']}/4  |  Archmage: {set_counts['ARCHMAGE']}/4"
    draw_text(tally_str, x + 18, cur_y, 11, COLOR_TEXT_MAIN)
    cur_y += 16

    if len(paper_doll.active_set_tiers) == 0:
        draw_text("No active set bonuses (Equip 2 or 4 matching set items)", x + 18, cur_y, 10, COLOR_TEXT_DIM)
        cur_y += 14
    else:
        for t in paper_doll.active_set_tiers:
            draw_text(f"ACTIVE: [{t.set_id} {t.pieces_required}pc] {t.title}: {t.description}", x + 18, cur_y, 10, COLOR_GOLD_ACCENT)
            cur_y += 14

    cur_y += 10

    # 5. Pattern Mode & State Drift Inspection
    draw_text("5. PATTERN COMPARISON & STATE CORRUPTION AUDIT", x + 12, cur_y, 11, COLOR_GOLD_ACCENT)
    cur_y += 16
    if pattern_enabled:
        draw_text("MODE: DECOUPLED PURE STAT PIPELINE [ROBUST - RECOMMENDED]", x + 18, cur_y, 11, COLOR_GREEN_ACCENT)
        cur_y += 14
        draw_text("Zero state drift. Base stats are immutable; unequip restores exact baseline.", x + 18, cur_y, 10, COLOR_TEXT_DIM)
    else:
        draw_text("MODE: NAIVE IN-PLACE DIRECT MUTATION [UNSAFE - BUGGY]", x + 18, cur_y, 11, COLOR_RED_ACCENT)
        cur_y += 14
        drift_msg = f"Simulated Drift Events: {paper_doll.naive_drift_count}  |  ATK Drift: {paper_doll.accumulated_drift_atk:+d}  |  DEF Drift: {paper_doll.accumulated_drift_def:+d}"
        draw_text(drift_msg, x + 18, cur_y, 11, COLOR_RED_ACCENT)
        cur_y += 14
        draw_text("Bug: Repeatedly equipping/unequipping permanently corrupts baseline stats!", x + 18, cur_y, 10, COLOR_TEXT_DIM)


# ==============================================================================
# BLOCK 4: MAIN GAME LOOP & AUTOMATED SMOKE TEST
# ==============================================================================

class PaperDollLabGame:
    """
    Interactive Paper Doll & Equipment Slots Pattern Lab.
    """
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()

        self.sfx = SoundLibrary()
        self.sfx.init_defaults()

        self.paper_doll = PaperDoll()
        self.training_dummy = TrainingDummy(CENTER_PANEL_X + 155, CENTER_PANEL_Y + 115)

        # Inventory bag: 16 slots (4x4 grid)
        self.bag = [None] * BAG_SLOT_COUNT

        # UI selection & cursor state
        self.hovered_doll_slot = -1
        self.hovered_bag_slot = -1
        self.selected_item = None
        self.selected_is_from_bag = True
        self.selected_index = -1

        # Interactive options
        self.show_xray = True
        self.pattern_enabled = True

        # Procedural animation timers
        self.anim_timer = 0.0
        self.attack_anim_timer = 0.0

        # Floating combat damage pool (Pre-allocated 24 instances)
        self.floating_numbers = []
        for _ in range(24):
            self.floating_numbers.append(FloatingDamageNumber())

        # Notification message banner
        self.status_message = "Welcome to Paper Doll Lab! Equip items to see live stat updates."
        self.status_message_timer = 4.0

        # Initialize starter inventory items
        self._populate_initial_equipment_and_inventory()

    def _populate_initial_equipment_and_inventory(self):
        """Populates the doll with starter equipment and fills the bag with rich items."""
        # 1. Equipped Starter Items
        starter_sword = EquipmentItem(
            1, "Sunsteel Broadsword", TYPE_MAIN_HAND, RARITY_RARE,
            atk=38, defense=0, hp=0, crit=5.0, spd=0,
            set_id="", is_two_handed=False,
            color_primary=Color(240, 210, 100, 255), color_secondary=Color(140, 100, 40, 255),
            icon_glyph="1H-SWORD", flavor="Tempered in solar forge fire. Balanced and swift."
        )
        starter_shield = EquipmentItem(
            2, "Dragonscale Buckler", TYPE_OFF_HAND, RARITY_RARE,
            atk=0, defense=20, hp=30, crit=4.0, spd=5,
            set_id="", is_two_handed=False,
            color_primary=Color(90, 160, 210, 255), color_secondary=Color(40, 80, 130, 255),
            icon_glyph="SHIELD", flavor="Forged from young wyvern scales. Light yet sturdy."
        )
        starter_helm = EquipmentItem(
            3, "Vanguard Greathelm", TYPE_HEAD, RARITY_EPIC,
            atk=0, defense=18, hp=40, crit=0.0, spd=-5,
            set_id="VANGUARD", is_two_handed=False,
            color_primary=Color(170, 185, 215, 255), color_secondary=Color(80, 100, 135, 255),
            icon_glyph="HELM", flavor="Heavy steel helmet inscribed with sacred paladin vows."
        )
        starter_gauntlets = EquipmentItem(
            4, "Vanguard Gauntlets", TYPE_HANDS, RARITY_RARE,
            atk=0, defense=14, hp=25, crit=0.0, spd=0,
            set_id="VANGUARD", is_two_handed=False,
            color_primary=Color(160, 175, 205, 255), color_secondary=Color(70, 90, 125, 255),
            icon_glyph="GLOVES", flavor="Reinforced articulated plates for defensive parries."
        )
        starter_boots = EquipmentItem(
            5, "Boots of the Windrunner", TYPE_FEET, RARITY_RARE,
            atk=0, defense=8, hp=0, crit=3.0, spd=45,
            set_id="", is_two_handed=False,
            color_primary=Color(100, 200, 160, 255), color_secondary=Color(40, 110, 80, 255),
            icon_glyph="BOOTS", flavor="Imbued with tempest whispers, granting swift strides."
        )

        self.paper_doll.slots[SLOT_MAIN_HAND] = starter_sword
        self.paper_doll.slots[SLOT_OFF_HAND] = starter_shield
        self.paper_doll.slots[SLOT_HEAD] = starter_helm
        self.paper_doll.slots[SLOT_HANDS] = starter_gauntlets
        self.paper_doll.slots[SLOT_FEET] = starter_boots

        # 2. Rich Bag Items (Sets, 2-Handed Colossus Weapons, Jewelry)
        bag_catalog = [
            # Vanguard Set Pieces
            EquipmentItem(6, "Vanguard Aegis Plate", TYPE_CHEST, RARITY_EPIC,
                          atk=0, defense=34, hp=70, crit=0.0, spd=-10, set_id="VANGUARD",
                          color_primary=Color(180, 195, 225, 255), color_secondary=Color(90, 110, 145, 255),
                          icon_glyph="CHEST", flavor="A massive chestplate engineered for front-line bastions."),
            EquipmentItem(7, "Vanguard Greaves", TYPE_LEGS, RARITY_RARE,
                          atk=0, defense=18, hp=35, crit=0.0, spd=-5, set_id="VANGUARD",
                          color_primary=Color(165, 180, 210, 255), color_secondary=Color(80, 95, 130, 255),
                          icon_glyph="LEGS", flavor="Layered steel greaves absorbing concussive shocks."),
            EquipmentItem(8, "Bulwark Tower Shield", TYPE_OFF_HAND, RARITY_EPIC,
                          atk=0, defense=32, hp=60, crit=0.0, spd=-12, set_id="VANGUARD",
                          color_primary=Color(190, 205, 235, 255), color_secondary=Color(100, 120, 160, 255),
                          icon_glyph="SHIELD", flavor="Unbreakable heraldic tower shield sealing defensive ranks."),

            # Two-Handed Weapons (Colossal Greathammer & Celestial Staff)
            EquipmentItem(9, "Titan's Earthshaker", TYPE_MAIN_HAND, RARITY_EPIC,
                          atk=92, defense=18, hp=0, crit=0.0, spd=-18, is_two_handed=True,
                          color_primary=Color(220, 150, 75, 255), color_secondary=Color(120, 70, 30, 255),
                          icon_glyph="2H-HAMMER", flavor="Massive warhammer wielding tectonic seismic force. Locks off-hand!"),
            EquipmentItem(10, "Celestial Colossus Staff", TYPE_MAIN_HAND, RARITY_LEGENDARY,
                          atk=78, defense=0, hp=65, crit=8.0, spd=0, is_two_handed=True, set_id="ARCHMAGE",
                          color_primary=Color(0, 235, 255, 255), color_secondary=Color(0, 120, 180, 255),
                          icon_glyph="2H-STAFF", flavor="Carved from fallen starcore crystal. Radiates raw aether."),

            # Assassin Set Pieces
            EquipmentItem(11, "Shadow Mask", TYPE_HEAD, RARITY_EPIC,
                          atk=16, defense=6, hp=0, crit=6.0, spd=15, set_id="ASSASSIN",
                          color_primary=Color(155, 90, 215, 255), color_secondary=Color(80, 35, 120, 255),
                          icon_glyph="MASK", flavor="Woven from nightshade silk. Conceals facial contours."),
            EquipmentItem(12, "Assassin Cuirass", TYPE_CHEST, RARITY_EPIC,
                          atk=0, defense=16, hp=0, crit=8.0, spd=12, set_id="ASSASSIN",
                          color_primary=Color(140, 80, 200, 255), color_secondary=Color(70, 30, 110, 255),
                          icon_glyph="CHEST", flavor="Supple cured leather treated for silent, lethal movement."),
            EquipmentItem(13, "Shadow Claws", TYPE_HANDS, RARITY_RARE,
                          atk=14, defense=4, hp=0, crit=7.0, spd=8, set_id="ASSASSIN",
                          color_primary=Color(165, 100, 225, 255), color_secondary=Color(90, 45, 135, 255),
                          icon_glyph="GLOVES", flavor="Razor talons tipped with paralyzing serpent venom."),
            EquipmentItem(14, "Shadow Striders", TYPE_FEET, RARITY_RARE,
                          atk=0, defense=10, hp=0, crit=4.0, spd=35, set_id="ASSASSIN",
                          color_primary=Color(130, 70, 190, 255), color_secondary=Color(60, 25, 95, 255),
                          icon_glyph="BOOTS", flavor="Muffled soles leaving zero footprint or sound."),
            EquipmentItem(15, "Twin Shadow Dirk", TYPE_MAIN_HAND, RARITY_RARE,
                          atk=34, defense=0, hp=0, crit=10.0, spd=15, set_id="ASSASSIN",
                          color_primary=Color(180, 115, 240, 255), color_secondary=Color(100, 50, 150, 255),
                          icon_glyph="DAGGER", flavor="Matched pair of serrated daggers seeking vital arteries."),

            # Archmage Set Pieces & Jewelry
            EquipmentItem(16, "Archmage Crown", TYPE_HEAD, RARITY_LEGENDARY,
                          atk=24, defense=4, hp=45, crit=5.0, spd=0, set_id="ARCHMAGE",
                          color_primary=Color(255, 215, 60, 255), color_secondary=Color(0, 180, 220, 255),
                          icon_glyph="CROWN", flavor="Resonates with cosmic leylines to magnify spellcraft."),
            EquipmentItem(17, "Astral Robes", TYPE_CHEST, RARITY_LEGENDARY,
                          atk=30, defense=14, hp=50, crit=0.0, spd=5, set_id="ARCHMAGE",
                          color_primary=Color(40, 140, 240, 255), color_secondary=Color(15, 60, 130, 255),
                          icon_glyph="ROBES", flavor="Woven astral fibers humming with protective abjuration."),
            EquipmentItem(18, "Nexus Signet", TYPE_RING, RARITY_LEGENDARY,
                          atk=22, defense=0, hp=30, crit=6.0, spd=0, set_id="ARCHMAGE",
                          color_primary=Color(0, 220, 255, 255), color_secondary=Color(255, 215, 60, 255),
                          icon_glyph="RING", flavor="Conducts wild elemental currents straight into attacks."),
            EquipmentItem(19, "Heart of Vitality", TYPE_AMULET, RARITY_EPIC,
                          atk=0, defense=12, hp=100, crit=0.0, spd=0,
                          color_primary=Color(255, 75, 95, 255), color_secondary=Color(140, 25, 40, 255),
                          icon_glyph="AMULET", flavor="Pulsates with ancient vigor, fortifying max life."),
            EquipmentItem(20, "Band of the Berserker", TYPE_RING, RARITY_EPIC,
                          atk=26, defense=-8, hp=0, crit=6.0, spd=10,
                          color_primary=Color(240, 80, 50, 255), color_secondary=Color(120, 30, 20, 255),
                          icon_glyph="RING", flavor="Sacrifices defensive discipline for furious strike damage."),
            EquipmentItem(21, "Aetheric Scepter", TYPE_MAIN_HAND, RARITY_RARE,
                          atk=45, defense=0, hp=25, crit=4.0, spd=0, set_id="ARCHMAGE",
                          color_primary=Color(70, 190, 255, 255), color_secondary=Color(20, 90, 150, 255),
                          icon_glyph="1H-SCEPTER", flavor="One-handed focusing wand channeling azure lightning.")
        ]

        for i in range(min(BAG_SLOT_COUNT, len(bag_catalog))):
            self.bag[i] = bag_catalog[i]

        self.paper_doll.is_dirty = True
        self.paper_doll.recalculate_stats()

    def spawn_floating_damage(self, text: str, x: float, y: float, is_crit: bool):
        """Spawns an animated floating damage number above the dummy."""
        target_num = None
        for num in self.floating_numbers:
            if not num.active:
                target_num = num
                break

        # If all slots active, reuse the one closest to expiring
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
        """Executes a weapon attack against the training dummy."""
        effective_atk = (
            self.paper_doll.effective_stats.atk
            if self.pattern_enabled
            else self.paper_doll.naive_stats.atk
        )
        effective_crit = (
            self.paper_doll.effective_stats.crit
            if self.pattern_enabled
            else self.paper_doll.naive_stats.crit
        )

        dmg, is_crit = self.training_dummy.take_hit(effective_atk, effective_crit)
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

        # Update floating combat text
        for num in self.floating_numbers:
            if num.active:
                num.y += num.vy * dt
                num.vy = damp(num.vy, 10.0, 3.5, dt)
                num.timer -= dt
                if num.timer <= 0.0:
                    num.active = False

        # Input Handling: Toggles
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
            self.sfx.play("click", 0.6)

        if is_dual_pattern_toggle_pressed():
            self.pattern_enabled = not self.pattern_enabled
            if self.pattern_enabled:
                self.paper_doll.is_dirty = True
                self.paper_doll.recalculate_stats()
                self.status_message = "Pattern Mode: ROBUST DECOUPLED PIPELINE (Safe, Validated, No Drift)"
            else:
                self.status_message = "Pattern Mode: NAIVE DIRECT MUTATION (Bypasses rules, causes stat drift!)"
            self.status_message_timer = 3.5
            self.sfx.play("powerup", 0.7)

        # [F2] / Gamepad L3: Auto-Equip Optimal Best in Slot
        if is_key_pressed(KEY_F2) or is_dual_secondary_toggle_pressed():
            self.paper_doll.auto_equip_optimal(self.bag)
            self.sfx.play("coin", 0.8)
            self.status_message = "Auto-Equipped Optimal Best-in-Slot loadout!"
            self.status_message_timer = 3.0

        # [F3] / Gamepad X: Unequip All Gear
        if is_key_pressed(KEY_F3) or (is_any_gamepad_connected() and is_gamepad_button_pressed(get_active_gamepad_id(), GAMEPAD_BUTTON_RIGHT_FACE_LEFT)):
            self.paper_doll.unequip_all(self.bag)
            self.sfx.play("click", 0.7)
            self.status_message = "Unequipped all gear back into inventory bag."
            self.status_message_timer = 3.0

        # [R] / Gamepad Start: Reset All
        if is_dual_reset_pressed():
            self._populate_initial_equipment_and_inventory()
            self.sfx.play("powerup", 0.6)
            self.status_message = "Reset Paper Doll and Inventory supplies."
            self.status_message_timer = 3.0

        # Strike Dummy via Space, Right Click, or Gamepad RT / A
        if is_key_pressed(KEY_SPACE) or is_mouse_button_pressed(MOUSE_BUTTON_RIGHT):
            self.perform_dummy_strike()
        elif is_any_gamepad_connected():
            pad_id = get_active_gamepad_id()
            if is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_TRIGGER_1) or is_gamepad_trigger_down(is_right_trigger=True):
                self.perform_dummy_strike()

        # Mouse Interaction & Hover Detection
        mx, my = get_mouse_x(), get_mouse_y()
        clicked_left = is_mouse_button_pressed(MOUSE_BUTTON_LEFT)

        self._update_mouse_interactions(mx, my, clicked_left)

    def _update_mouse_interactions(self, mx: int, my: int, clicked_left: bool):
        """Handles point-and-click equipping, unequipping, and tooltips."""
        self.hovered_doll_slot = -1
        self.hovered_bag_slot = -1

        # 1. Check Doll Slots
        slot_rects = self._get_doll_slot_rects()
        for i in range(SLOT_COUNT):
            rx, ry, rw, rh = slot_rects[i]
            if rx <= mx <= rx + rw and ry <= my <= ry + rh:
                self.hovered_doll_slot = i
                if clicked_left:
                    # Unequip clicked gear back into the first free bag slot
                    if self.paper_doll.slots[i] is not None:
                        item = self.paper_doll.unequip_item(i, self.pattern_enabled)
                        if item is not None:
                            self.paper_doll._put_in_bag(item, self.bag)
                            self.sfx.play("click", 0.7)
                            self.status_message = f"Unequipped {item.name}."
                            self.status_message_timer = 2.0
                break

        # 2. Check Bag Grid Slots
        bag_rects = self._get_bag_slot_rects()
        for i in range(BAG_SLOT_COUNT):
            rx, ry, rw, rh = bag_rects[i]
            if rx <= mx <= rx + rw and ry <= my <= ry + rh:
                self.hovered_bag_slot = i
                if clicked_left:
                    item = self.bag[i]
                    if item is not None:
                        # Attempt to equip item
                        self.bag[i] = None
                        swapped = self.paper_doll.equip_item(
                            item, target_slot=-1, bag_ref=self.bag, pattern_enabled=self.pattern_enabled
                        )
                        # Put back swapped item or returned item
                        if swapped is not None:
                            self.bag[i] = swapped
                        self.sfx.play("coin", 0.75)
                        self.status_message = f"Equipped {item.name}."
                        self.status_message_timer = 2.0
                break

        # 3. Check Attack Dummy Click
        if (
            CENTER_PANEL_X + 90 <= mx <= CENTER_PANEL_X + 220
            and CENTER_PANEL_Y + 40 <= my <= CENTER_PANEL_Y + 185
            and clicked_left
        ):
            self.perform_dummy_strike()

        # 4. Check Lab Action Buttons in Center Panel
        btn_y = CENTER_PANEL_Y + 470
        btn_h = 32
        btn_w = CENTER_PANEL_W - 30
        btn_x = CENTER_PANEL_X + 15

        # Button 1: Attack Dummy
        if btn_x <= mx <= btn_x + btn_w and btn_y <= my <= btn_y + btn_h and clicked_left:
            self.perform_dummy_strike()

        # Button 2: Toggle Pattern
        btn_y += 40
        if btn_x <= mx <= btn_x + btn_w and btn_y <= my <= btn_y + btn_h and clicked_left:
            self.pattern_enabled = not self.pattern_enabled
            if self.pattern_enabled:
                self.paper_doll.is_dirty = True
                self.paper_doll.recalculate_stats()
            self.sfx.play("powerup", 0.7)

        # Button 3: Auto-Equip Optimal
        btn_y += 40
        if btn_x <= mx <= btn_x + btn_w and btn_y <= my <= btn_y + btn_h and clicked_left:
            self.paper_doll.auto_equip_optimal(self.bag)
            self.sfx.play("coin", 0.8)

        # Button 4: Unequip All
        btn_y += 40
        if btn_x <= mx <= btn_x + btn_w and btn_y <= my <= btn_y + btn_h and clicked_left:
            self.paper_doll.unequip_all(self.bag)
            self.sfx.play("click", 0.7)

    def _get_doll_slot_rects(self) -> list:
        """Returns the bounding rectangles [(x, y, w, h)] for the 10 doll slots."""
        px = LEFT_PANEL_X
        py = LEFT_PANEL_Y

        # Anatomical layout around mannequin
        return [
            (px + 140, py + 45, 96, 46),   # SLOT_HEAD
            (px + 248, py + 45, 96, 46),   # SLOT_AMULET
            (px + 194, py + 100, 96, 48),  # SLOT_CHEST
            (px + 45,  py + 100, 138, 48), # SLOT_MAIN_HAND
            (px + 302, py + 100, 138, 48), # SLOT_OFF_HAND
            (px + 45,  py + 158, 138, 46), # SLOT_HANDS
            (px + 194, py + 158, 96, 46),  # SLOT_LEGS
            (px + 194, py + 214, 96, 46),  # SLOT_FEET
            (px + 45,  py + 214, 138, 46), # SLOT_RING_1
            (px + 302, py + 214, 138, 46), # SLOT_RING_2
        ]

    def _get_bag_slot_rects(self) -> list:
        """Returns the bounding rectangles for the 16 inventory bag grid slots."""
        rects = []
        start_x = RIGHT_PANEL_X + 22
        start_y = RIGHT_PANEL_Y + 54
        cell_w = 78
        cell_h = 70
        gap_x = 9
        gap_y = 9

        for r in range(BAG_ROWS):
            for c in range(BAG_COLS):
                rx = start_x + c * (cell_w + gap_x)
                ry = start_y + r * (cell_h + gap_y)
                rects.append((rx, ry, cell_w, cell_h))
        return rects

    def draw(self):
        begin_drawing()
        clear_background(COLOR_BG)

        # 1. Top HUD Title & Controls Bar
        draw_text("PAPER DOLL - EQUIPMENT SLOTS & STAT PIPELINE", 35, 18, 17, COLOR_GOLD_ACCENT)
        draw_text("Section 3.1: Menus & UI | RPG Equipment Architecture", 35, 38, 11, COLOR_TEXT_DIM)

        # Top-Bar Settings Dropdown & Gamepad status
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)

        # 2. Left Panel: Paper Doll Mannequin, Equipment Slots & Stat Sheet
        self._draw_left_panel()

        # 3. Center Panel: Combat Target Dummy, Testing Controls & Telemetry
        self._draw_center_panel()

        # 4. Right Panel: Inventory Bag Grid & Hover Inspector Tooltip
        self._draw_right_panel()

        # 5. Floating Damage Numbers
        for num in self.floating_numbers:
            if num.active:
                alpha = max(0, min(255, int(255 * (num.timer / num.max_life))))
                nr = getattr(num.color, "r", num.color[0] if isinstance(num.color, (list, tuple)) else 255)
                ng = getattr(num.color, "g", num.color[1] if isinstance(num.color, (list, tuple)) else 255)
                nb = getattr(num.color, "b", num.color[2] if isinstance(num.color, (list, tuple)) else 255)
                col = Color(int(nr), int(ng), int(nb), alpha)
                fsize = int(14 * num.scale)
                draw_text(num.text, int(num.x), int(num.y), fsize, col)

        # 6. Status Message Toast Bar (Bottom Center)
        if self.status_message_timer > 0.0:
            alpha = max(0, min(255, int(255 * min(1.0, self.status_message_timer))))
            draw_rectangle(SCREEN_WIDTH // 2 - 280, SCREEN_HEIGHT - 32, 560, 24, Color(16, 24, 40, alpha))
            draw_rectangle_lines(SCREEN_WIDTH // 2 - 280, SCREEN_HEIGHT - 32, 560, 24, Color(0, 225, 255, alpha))
            draw_text(self.status_message, SCREEN_WIDTH // 2 - 265, SCREEN_HEIGHT - 26, 11, Color(240, 245, 255, alpha))

        # 7. X-Ray Overlay Drawer ([Tab])
        if self.show_xray:
            draw_xray_overlay(
                self.paper_doll,
                self.pattern_enabled,
                RIGHT_PANEL_X - 10,
                RIGHT_PANEL_Y,
                RIGHT_PANEL_W + 10,
                RIGHT_PANEL_H
            )

        end_drawing()

    def _draw_left_panel(self):
        """Renders the anatomical equipment slots, mannequin silhouette, and stat sheet."""
        px = LEFT_PANEL_X
        py = LEFT_PANEL_Y
        pw = LEFT_PANEL_W
        ph = LEFT_PANEL_H

        draw_rectangle(px, py, pw, ph, COLOR_PANEL_BG)
        draw_rectangle_lines(px, py, pw, ph, COLOR_PANEL_BORDER)

        # Panel Title
        draw_rectangle(px, py, pw, 26, Color(22, 30, 48, 255))
        draw_text("ANATOMICAL PAPER DOLL & EQUIPMENT SLOTS", px + 14, py + 6, 12, COLOR_CYAN_ACCENT)

        # Render Mannequin in the center of the doll ring
        mannequin_cx = px + 242
        mannequin_cy = py + 145
        draw_mannequin(
            mannequin_cx,
            mannequin_cy,
            self.paper_doll,
            self.anim_timer,
            self.attack_anim_timer
        )

        # Render 10 Anatomical Equipment Slots
        slot_rects = self._get_doll_slot_rects()
        for i in range(SLOT_COUNT):
            rx, ry, rw, rh = slot_rects[i]
            is_hovered = (i == self.hovered_doll_slot)
            item = self.paper_doll.slots[i]
            is_locked = (i == SLOT_OFF_HAND and self.paper_doll.is_offhand_locked)

            # Slot Background
            if is_locked:
                bg_col = COLOR_SLOT_LOCKED
                border_col = COLOR_RED_ACCENT
            elif is_hovered:
                bg_col = COLOR_SLOT_HOVER
                border_col = COLOR_CYAN_ACCENT
            else:
                bg_col = COLOR_SLOT_EMPTY
                border_col = COLOR_SLOT_BORDER

            draw_rectangle(rx, ry, rw, rh, bg_col)
            draw_rectangle_lines(rx, ry, rw, rh, border_col)

            # Slot anatomical label
            sname = SLOT_NAMES[i].upper()
            draw_text(sname, rx + 6, ry + 4, 9, COLOR_TEXT_DIM)

            if is_locked:
                draw_text("2H LOCKED", rx + 12, ry + 22, 11, COLOR_RED_ACCENT)
            elif item is not None:
                # Rarity Border & Colored Item Name
                rarity_col = self._get_rarity_color(item.rarity)
                draw_rectangle_lines(rx + 1, ry + 1, rw - 2, rh - 2, rarity_col)

                # Truncate long names cleanly
                disp_name = item.name if len(item.name) <= 15 else item.name[:13] + ".."
                draw_text(disp_name, rx + 6, ry + 18, 11, rarity_col)

                # Stat preview tag
                stat_tag = ""
                if item.atk > 0:
                    stat_tag = f"+{item.atk} ATK"
                elif item.defense > 0:
                    stat_tag = f"+{item.defense} DEF"
                elif item.hp > 0:
                    stat_tag = f"+{item.hp} HP"
                elif item.spd != 0:
                    stat_tag = f"{item.spd:+d} SPD"
                draw_text(stat_tag, rx + 6, ry + 32, 9, COLOR_GREEN_ACCENT)

                if item.set_id != "":
                    draw_text(f"[{item.set_id[:3]}]", rx + rw - 34, ry + 32, 9, COLOR_GOLD_ACCENT)
            else:
                draw_text("(Empty)", rx + 10, ry + 22, 10, Color(80, 95, 120, 255))

        # Bottom Sub-Panel: Live Character Stat Sheet
        sheet_y = py + 275
        sheet_h = ph - 285
        draw_rectangle(px + 10, sheet_y, pw - 20, sheet_h, Color(12, 16, 26, 255))
        draw_rectangle_lines(px + 10, sheet_y, pw - 20, sheet_h, COLOR_PANEL_BORDER)

        draw_rectangle(px + 10, sheet_y, pw - 20, 22, Color(20, 28, 44, 255))
        draw_text("CHARACTER ATTRIBUTES & COMBAT DERIVATION", px + 18, sheet_y + 5, 11, COLOR_GOLD_ACCENT)

        active_stats = (
            self.paper_doll.effective_stats
            if self.pattern_enabled
            else self.paper_doll.naive_stats
        )
        base = self.paper_doll.base_stats

        sy = sheet_y + 32

        # 1. Health Bar
        draw_text("HEALTH POINTS (HP):", px + 22, sy, 11, COLOR_TEXT_MAIN)
        draw_text(f"{active_stats.max_hp} / {active_stats.max_hp}", px + 180, sy, 11, COLOR_GREEN_ACCENT)
        # HP Gauge Bar
        draw_rectangle(px + 280, sy + 2, 180, 10, Color(30, 45, 60, 255))
        draw_rectangle(px + 280, sy + 2, 180, 10, Color(40, 200, 90, 255))
        draw_rectangle_lines(px + 280, sy + 2, 180, 10, COLOR_PANEL_BORDER)
        sy += 24

        # 2. Attack Power
        draw_text("ATTACK POWER (ATK):", px + 22, sy, 11, COLOR_TEXT_MAIN)
        draw_text(f"{active_stats.atk}", px + 180, sy, 12, COLOR_GOLD_ACCENT)
        if self.pattern_enabled:
            gear_atk = self.paper_doll.effective_stats.gear_atk
            set_atk = self.paper_doll.effective_stats.set_atk
            draw_text(f"(Base {base.base_atk} + Gear {gear_atk} + Set {set_atk})", px + 235, sy, 10, COLOR_TEXT_DIM)
        sy += 22

        # 3. Defense & Damage Reduction
        draw_text("DEFENSE RATING (DEF):", px + 22, sy, 11, COLOR_TEXT_MAIN)
        draw_text(f"{active_stats.defense}", px + 180, sy, 12, COLOR_CYAN_ACCENT)
        dr_pct = active_stats.damage_reduction_pct
        draw_text(f"[{dr_pct:.1f}% Dmg Reduction]", px + 235, sy, 10, COLOR_CYAN_ACCENT)
        sy += 22

        # 4. Critical Strike Chance
        draw_text("CRITICAL CHANCE:", px + 22, sy, 11, COLOR_TEXT_MAIN)
        draw_text(f"{active_stats.crit:.1f}%", px + 180, sy, 11, COLOR_PURPLE_ACCENT)
        draw_text("(Strikes deal 2.0x damage)", px + 235, sy, 10, COLOR_TEXT_DIM)
        sy += 22

        # 5. Movement / Action Speed
        draw_text("SPEED RATING (SPD):", px + 22, sy, 11, COLOR_TEXT_MAIN)
        draw_text(f"{active_stats.spd} px/s", px + 180, sy, 11, COLOR_WHITE)
        sy += 26

        # Active Set Synergies Badges
        draw_line_ex(Vector2(px + 20, sy), Vector2(px + pw - 20, sy), 1.0, COLOR_PANEL_BORDER)
        sy += 8
        draw_text("ACTIVE SET SYNERGIES:", px + 22, sy, 10, COLOR_GOLD_ACCENT)
        sy += 16

        if not self.pattern_enabled:
            draw_text("INACTIVE in Naive Mutation Mode (No set evaluations)", px + 22, sy, 10, COLOR_RED_ACCENT)
        elif len(self.paper_doll.active_set_tiers) == 0:
            draw_text("No set synergies active. Equip matching Vanguard/Assassin/Archmage items.", px + 22, sy, 10, COLOR_TEXT_DIM)
        else:
            for tier in self.paper_doll.active_set_tiers:
                draw_rectangle(px + 20, sy - 2, pw - 40, 20, Color(25, 38, 60, 255))
                draw_rectangle_lines(px + 20, sy - 2, pw - 40, 20, COLOR_GOLD_ACCENT)
                draw_text(f"[{tier.set_id} {tier.pieces_required}pc] {tier.title}: {tier.description}", px + 26, sy + 2, 10, COLOR_GOLD_ACCENT)
                sy += 24

    def _draw_center_panel(self):
        """Renders the combat dummy sandbox, dps metrics, and action buttons."""
        cx = CENTER_PANEL_X
        cy = CENTER_PANEL_Y
        cw = CENTER_PANEL_W
        ch = CENTER_PANEL_H

        draw_rectangle(cx, cy, cw, ch, COLOR_PANEL_BG)
        draw_rectangle_lines(cx, cy, cw, ch, COLOR_PANEL_BORDER)

        # Panel Title
        draw_rectangle(cx, cy, cw, 26, Color(22, 30, 48, 255))
        draw_text("COMBAT TRAINING DUMMY", cx + 14, cy + 6, 12, COLOR_CYAN_ACCENT)

        # Draw Sandbox Arena & Target Dummy
        arena_y = cy + 34
        arena_h = 240
        draw_rectangle(cx + 12, arena_y, cw - 24, arena_h, Color(14, 18, 28, 255))
        draw_rectangle_lines(cx + 12, arena_y, cw - 24, arena_h, COLOR_PANEL_BORDER)

        # Grid lines in arena floor
        for gx in range(cx + 25, cx + cw - 20, 35):
            draw_line(gx, arena_y + 1, gx, arena_y + arena_h - 1, Color(22, 30, 46, 255))
        for gy in range(arena_y + 20, arena_y + arena_h, 30):
            draw_line(cx + 13, gy, cx + cw - 13, gy, Color(22, 30, 46, 255))

        self.training_dummy.draw()

        # Dummy Armor Badge
        draw_text("Target Dummy (Armor: 20)", cx + 22, arena_y + 10, 10, COLOR_TEXT_DIM)

        # Combat Telemetry & DPS
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
        draw_text(f"Total Strikes: {strikes}  |  Avg Dmg: {avg_dmg:.1f}", cx + 20, stats_y + 48, 10, COLOR_TEXT_DIM)
        draw_text(f"Cumulative Dmg: {total_dmg}", cx + 20, stats_y + 66, 11, COLOR_CYAN_ACCENT)

        mit_str = "Dummy Mitigation: -28.6% incoming damage"
        draw_text(mit_str, cx + 20, stats_y + 86, 9, Color(130, 150, 180, 255))

        # Lab Action Buttons
        btn_y = cy + 415
        btn_w = cw - 24
        btn_h = 34
        btn_x = cx + 12

        # 1. Attack Dummy Button
        draw_rectangle(btn_x, btn_y, btn_w, btn_h, Color(30, 75, 125, 255))
        draw_rectangle_lines(btn_x, btn_y, btn_w, btn_h, COLOR_CYAN_ACCENT)
        draw_text("[SPACE / CLICK] TEST STRIKE", btn_x + 35, btn_y + 10, 11, COLOR_WHITE)

        # 2. Toggle Pattern Button
        btn_y += 42
        pat_bg = Color(20, 80, 45, 255) if self.pattern_enabled else Color(90, 25, 30, 255)
        pat_border = COLOR_GREEN_ACCENT if self.pattern_enabled else COLOR_RED_ACCENT
        draw_rectangle(btn_x, btn_y, btn_w, btn_h, pat_bg)
        draw_rectangle_lines(btn_x, btn_y, btn_w, btn_h, pat_border)
        pat_title = "[F1] PATTERN: ROBUST" if self.pattern_enabled else "[F1] PATTERN: NAIVE"
        draw_text(pat_title, btn_x + 38, btn_y + 10, 11, pat_border)

        # 3. Auto-Equip Optimal
        btn_y += 42
        draw_rectangle(btn_x, btn_y, btn_w, btn_h, Color(24, 34, 54, 255))
        draw_rectangle_lines(btn_x, btn_y, btn_w, btn_h, COLOR_PANEL_BORDER)
        draw_text("[F2] AUTO-EQUIP BEST", btn_x + 48, btn_y + 10, 11, COLOR_GOLD_ACCENT)

        # 4. Unequip All
        btn_y += 42
        draw_rectangle(btn_x, btn_y, btn_w, btn_h, Color(24, 34, 54, 255))
        draw_rectangle_lines(btn_x, btn_y, btn_w, btn_h, COLOR_PANEL_BORDER)
        draw_text("[F3] UNEQUIP ALL GEAR", btn_x + 42, btn_y + 10, 11, COLOR_TEXT_MAIN)

        # 5. Reset All
        btn_y += 42
        draw_rectangle(btn_x, btn_y, btn_w, btn_h, Color(18, 24, 38, 255))
        draw_rectangle_lines(btn_x, btn_y, btn_w, btn_h, COLOR_PANEL_BORDER)
        draw_text("[R] RESET INVENTORY", btn_x + 48, btn_y + 10, 11, COLOR_TEXT_DIM)

    def _draw_right_panel(self):
        """Renders the 16-slot inventory bag and inspection tooltip."""
        rx = RIGHT_PANEL_X
        ry = RIGHT_PANEL_Y
        rw = RIGHT_PANEL_W
        rh = RIGHT_PANEL_H

        draw_rectangle(rx, ry, rw, rh, COLOR_PANEL_BG)
        draw_rectangle_lines(rx, ry, rw, rh, COLOR_PANEL_BORDER)

        # Panel Title
        draw_rectangle(rx, ry, rw, 26, Color(22, 30, 48, 255))
        draw_text("INVENTORY BAG (16 SLOTS)", rx + 14, ry + 6, 12, COLOR_CYAN_ACCENT)
        draw_text("Click to Equip", rx + rw - 95, ry + 7, 10, COLOR_TEXT_DIM)

        # Render 4x4 Inventory Bag Grid
        bag_rects = self._get_bag_slot_rects()
        for i in range(BAG_SLOT_COUNT):
            bx, by, bw, bh = bag_rects[i]
            is_hovered = (i == self.hovered_bag_slot)
            item = self.bag[i]

            bg_col = COLOR_SLOT_HOVER if is_hovered else COLOR_SLOT_EMPTY
            border_col = COLOR_CYAN_ACCENT if is_hovered else COLOR_SLOT_BORDER
            draw_rectangle(bx, by, bw, bh, bg_col)
            draw_rectangle_lines(bx, by, bw, bh, border_col)

            if item is not None:
                rarity_col = self._get_rarity_color(item.rarity)
                draw_rectangle_lines(bx + 1, by + 1, bw - 2, bh - 2, rarity_col)

                # Icon glyph & item type
                draw_text(item.icon_glyph[:7], bx + 6, by + 6, 9, COLOR_TEXT_DIM)

                # Display name
                short_name = item.name if len(item.name) <= 10 else item.name[:9] + "."
                draw_text(short_name, bx + 6, by + 22, 10, rarity_col)

                # Stat Chip
                stat_chip = ""
                if item.atk > 0:
                    stat_chip = f"+{item.atk} ATK"
                elif item.defense > 0:
                    stat_chip = f"+{item.defense} DEF"
                elif item.hp > 0:
                    stat_chip = f"+{item.hp} HP"
                elif item.spd != 0:
                    stat_chip = f"{item.spd:+d} SPD"
                draw_text(stat_chip, bx + 6, by + 40, 9, COLOR_GREEN_ACCENT)

                # Set or 2H badge
                if item.is_two_handed:
                    draw_text("2H", bx + bw - 18, by + 54, 9, COLOR_RED_ACCENT)
                elif item.set_id != "":
                    draw_text(item.set_id[:3], bx + bw - 22, by + 54, 9, COLOR_GOLD_ACCENT)

        # Inspection / Tooltip Detail Box (Bottom half of Right Panel)
        info_y = ry + 360
        info_h = rh - 370
        draw_rectangle(rx + 12, info_y, rw - 24, info_h, Color(12, 16, 26, 255))
        draw_rectangle_lines(rx + 12, info_y, rw - 24, info_h, COLOR_PANEL_BORDER)

        draw_rectangle(rx + 12, info_y, rw - 24, 22, Color(20, 28, 44, 255))
        draw_text("ITEM INSPECTOR & GEAR COMPARISON", rx + 20, info_y + 5, 10, COLOR_GOLD_ACCENT)

        # Determine which item to inspect
        inspected_item = None
        equipped_compare_item = None

        if self.hovered_bag_slot >= 0 and self.bag[self.hovered_bag_slot] is not None:
            inspected_item = self.bag[self.hovered_bag_slot]
            target_slot = self.paper_doll.find_best_slot_for_item(inspected_item)
            if target_slot >= 0:
                equipped_compare_item = self.paper_doll.slots[target_slot]
        elif self.hovered_doll_slot >= 0 and self.paper_doll.slots[self.hovered_doll_slot] is not None:
            inspected_item = self.paper_doll.slots[self.hovered_doll_slot]

        iy = info_y + 30
        if inspected_item is not None:
            rarity_col = self._get_rarity_color(inspected_item.rarity)
            rarity_label = RARITY_NAMES[inspected_item.rarity]

            # Title & Rarity
            draw_text(inspected_item.name, rx + 20, iy, 12, rarity_col)
            draw_text(f"{rarity_label} | {TYPE_NAMES[inspected_item.item_type]}", rx + 20, iy + 18, 10, COLOR_TEXT_DIM)
            iy += 34

            if inspected_item.is_two_handed:
                draw_text("[TWO-HANDED WEAPON - REQUIRES BOTH HANDS]", rx + 20, iy, 10, COLOR_RED_ACCENT)
                iy += 16

            if inspected_item.set_id != "":
                draw_text(f"Set: {inspected_item.set_id} Synergy", rx + 20, iy, 10, COLOR_GOLD_ACCENT)
                iy += 16

            # Attributes with Green/Red diff preview
            if inspected_item.atk != 0:
                diff_str = ""
                if equipped_compare_item is not None:
                    diff = inspected_item.atk - equipped_compare_item.atk
                    diff_str = f" ({diff:+d})" if diff != 0 else " (=)"
                draw_text(f"Attack Power (ATK): +{inspected_item.atk}{diff_str}", rx + 20, iy, 11, COLOR_GOLD_ACCENT)
                iy += 16

            if inspected_item.defense != 0:
                diff_str = ""
                if equipped_compare_item is not None:
                    diff = inspected_item.defense - equipped_compare_item.defense
                    diff_str = f" ({diff:+d})" if diff != 0 else " (=)"
                draw_text(f"Defense Rating (DEF): +{inspected_item.defense}{diff_str}", rx + 20, iy, 11, COLOR_CYAN_ACCENT)
                iy += 16

            if inspected_item.hp != 0:
                diff_str = ""
                if equipped_compare_item is not None:
                    diff = inspected_item.hp - equipped_compare_item.hp
                    diff_str = f" ({diff:+d})" if diff != 0 else " (=)"
                draw_text(f"Max Health (HP): +{inspected_item.hp}{diff_str}", rx + 20, iy, 11, COLOR_GREEN_ACCENT)
                iy += 16

            if inspected_item.crit != 0.0:
                draw_text(f"Critical Strike: +{inspected_item.crit:.1f}%", rx + 20, iy, 11, COLOR_PURPLE_ACCENT)
                iy += 16

            if inspected_item.spd != 0:
                draw_text(f"Movement Speed: {inspected_item.spd:+d} px/s", rx + 20, iy, 11, COLOR_WHITE)
                iy += 16

            # Flavor Lore
            iy += 6
            draw_text(f'"{inspected_item.flavor}"', rx + 20, iy, 9, Color(140, 160, 190, 255))
        else:
            draw_text("Hover over an item in the bag or paper doll", rx + 20, iy, 10, COLOR_TEXT_DIM)
            draw_text("to inspect stats, 2H requirements, and set bonuses.", rx + 20, iy + 16, 10, COLOR_TEXT_DIM)
            iy += 45
            draw_text("Controls Reminder:", rx + 20, iy, 10, COLOR_GOLD_ACCENT)
            draw_text("- Left Click / Gamepad A : Equip / Unequip Item", rx + 20, iy + 16, 10, COLOR_TEXT_MAIN)
            draw_text("- Space / Right Click    : Attack Dummy & Test DPS", rx + 20, iy + 32, 10, COLOR_TEXT_MAIN)
            draw_text("- [F1] / Gamepad R3      : Toggle Robust vs Naive", rx + 20, iy + 48, 10, COLOR_TEXT_MAIN)
            draw_text("- [F2] / Gamepad L3      : Auto-Equip Best-in-Slot", rx + 20, iy + 64, 10, COLOR_TEXT_MAIN)
            draw_text("- [Tab] / Gamepad Select : Toggle X-Ray Telemetry", rx + 20, iy + 80, 10, COLOR_TEXT_MAIN)

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
                # Exercise test strike option during smoke test to verify damage & floating text rendering
                self.perform_dummy_strike()
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
    PaperDollLabGame().run(smoke_test=is_smoke)

