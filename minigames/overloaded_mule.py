# -*- coding: utf-8 -*-
"""
Overloaded Mule - Weight-Based Inventory & Dynamic Encumbrance Physics
=====================================================================
Section          : 3.1 Menus & UI
Pattern Category : Menus & User Interface, RPG Progression & Economy
Dimension        : 2D

Problem Solved:
  In open-world RPGs, dungeon crawlers, and survival games (such as Skyrim,
  Fallout, The Witcher 3, Death Stranding, and Dark Souls), infinite carry
  inventories destroy economy balance, survival tension, and risk-reward loot
  decisions. However, naive encumbrance implementations use hard-stop binary
  lockouts (e.g., if weight > max: cannot_move()) scattered across input and
  movement code, causing jarring player frustration and buggy exploits.
  The Weight-Based Inventory pattern solves this through an explicit, decoupled
  encumbrance aggregation pipeline that classifies total carried mass into discrete
  load tiers (Light, Medium, Heavy, Overencumbered, Crushed). This pipeline
  continuously scales movement velocity, sprint availability, and stamina drain,
  while offering tactical companion offloading to a Pack Mule.

How the Pattern Works:
  1. Weight Aggregation Pipeline:
     Every item archetype defines a unit_weight (in kg). The total mass is aggregated
     in O(N) time across all item stacks:
       Total_Weight = SUM(stack.count * archetype.unit_weight)
     Magical artifacts (such as Feather Charms) can provide negative weight modifiers,
     demonstrating modular stat pipeline integration.
  2. Encumbrance Ratio & Discrete Load Tiers:
     Encumbrance Ratio R = Current_Weight / Max_Capacity:
       - Light Load (R <= 0.50)    : 100% velocity (220 px/s), fast sprint, 1.0x stamina drain.
       - Medium Load (0.50 < R <= 0.75): 85% velocity (187 px/s), normal sprint, 1.35x stamina drain.
       - Heavy Load (0.75 < R <= 1.00) : 60% velocity (132 px/s), heavy stride, 2.0x stamina drain.
       - Overencumbered (1.00 < R <= 1.50): 28% velocity (62 px/s), sprint locked out, stamina halted.
       - Crushed (R > 1.50)        : 10% velocity (22 px/s crawl), severe physical strain.
  3. Dynamic Movement Modifier Curve:
     Instead of sudden stops, velocity modulates smoothly along an evaluation curve:
       V(R) = V_base * max(0.10, 1.0 - 0.75 * min(1.0, R))  for R <= 1.0
       V(R) = V_base * max(0.08, 0.28 - 0.15 * (R - 1.0))   for R > 1.0
  4. Companion Mule Storage & Offload Architecture:
     A companion Pack Mule follows the player with a leash-following steering behavior
     and high carry capacity (200 kg). Heavy cargo bulges the mule's procedural saddlebags.
     Players can transfer items individually or invoke a greedy Quick-Offload heuristic
     ([F2]) that moves heaviest items until the player returns to an agile load.

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - WASD / Arrow Keys / Left Stick / D-Pad : Move Adventurer in 2D Arena
  - Shift / Gamepad B                      : Sprint / Dash (Drains Stamina; Locked if Overencumbered)
  - E / Left Click / Gamepad A             : Pick Up Nearby Ground Loot / Select Item
  - T / Gamepad X                          : Transfer Selected Item between Player & Mule
  - X / Gamepad Y                          : Drop Selected Item onto Ground
  - [Tab] / Gamepad View (Select)          : Toggle X-Ray Telemetry & Encumbrance Curve Inspector
  - [F1]  / Gamepad LB                     : Toggle Weight Penalty ON/OFF (Realistic vs Infinite Carry)
  - [F2]  / Gamepad RB                     : Quick Offload Heaviest Items to Pack Mule
  - [Ctrl +/-]                             : Increase / Decrease UI Font Size
  - [F11]                                  : Toggle Fullscreen
  - R / Gamepad Start                      : Reset Arena Simulation & Loot Piles
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
WINDOW_TITLE = "Overloaded Mule - Weight-Based Inventory & Encumbrance Physics (Raylib Pattern Lab)"

# Arena Layout Dimensions
ARENA_X = 40
ARENA_Y = 68
ARENA_W = 760
ARENA_H = 430

# Inventory & Management Panel Dimensions
PANEL_X = 40
PANEL_Y = 510
PANEL_W = 760
PANEL_H = 190

# Right Telemetry Inspector Dimensions
TELEMETRY_X = 818
TELEMETRY_Y = 68
TELEMETRY_W = 422
TELEMETRY_H = 632

# Visual Palette
COLOR_BG               = Color(12, 15, 24, 255)
COLOR_ARENA_GROUND     = Color(24, 30, 44, 255)
COLOR_ARENA_BORDER     = Color(50, 68, 102, 255)
COLOR_PANEL_BG         = Color(18, 23, 36, 255)
COLOR_PANEL_BORDER     = Color(44, 58, 88, 255)
COLOR_SLOT_EMPTY       = Color(14, 18, 28, 255)
COLOR_SLOT_BORDER      = Color(32, 42, 64, 255)
COLOR_SLOT_SELECTED    = Color(0, 180, 240, 255)

COLOR_TIER_LIGHT       = Color(50, 220, 110, 255)
COLOR_TIER_MEDIUM      = Color(240, 210, 50, 255)
COLOR_TIER_HEAVY       = Color(245, 130, 40, 255)
COLOR_TIER_OVERLOADED  = Color(245, 55, 55, 255)
COLOR_TIER_CRUSHED     = Color(180, 20, 20, 255)

COLOR_TEXT_MAIN        = Color(230, 240, 255, 255)
COLOR_TEXT_DIM         = Color(140, 158, 188, 255)
COLOR_ACCENT_CYAN      = Color(0, 225, 255, 255)
COLOR_ACCENT_GOLD      = Color(255, 210, 60, 255)
COLOR_ACCENT_GREEN     = Color(60, 240, 120, 255)

# Item Archetype Identifiers (C++ enum ItemID)
ITEM_ANVIL         = 1
ITEM_DRAGON_BONE   = 2
ITEM_STEEL_ARMOR   = 3
ITEM_METEOR_ORE    = 4
ITEM_GOLD_BAR      = 5
ITEM_GREATSWORD    = 6
ITEM_CAMPING_GEAR  = 7
ITEM_BREAD_LOAF    = 8
ITEM_HEALTH_POTION = 9
ITEM_FEATHER_CHARM = 10

# Encumbrance Tier Constants
TIER_LIGHT       = 0
TIER_MEDIUM      = 1
TIER_HEAVY       = 2
TIER_OVERLOADED  = 3
TIER_CRUSHED     = 4


# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATION (WEIGHT AGGREGATION & ENCUMBRANCE PIPELINE)
# ==============================================================================

class ItemArchetype:
    """
    Static metadata archetype for an inventory item.
    C++ Equivalent:
      struct ItemArchetype {
          int id;
          const char* name;
          const char* category;
          float unit_weight; // in kg
          int gold_value;
          Color badge_color;
      };
    """
    def __init__(self, item_id: int, name: str, category: str,
                 unit_weight: float, gold_value: int, badge_color: Color):
        self.id = item_id
        self.name = name
        self.category = category
        self.unit_weight = unit_weight
        self.gold_value = gold_value
        self.badge_color = badge_color


class ItemStack:
    """
    Dynamic stack instance in an inventory.
    C++ Equivalent:
      struct ItemStack {
          int archetype_id;
          int count;
      };
    """
    def __init__(self, archetype_id: int, count: int = 1):
        self.archetype_id = archetype_id
        self.count = count


class InventoryContainer:
    """
    Discrete fixed-capacity item container (Player Backpack or Mule Saddlebags).
    C++ Equivalent:
      class InventoryContainer {
          int max_slots;
          float max_capacity;
          ItemStack slots[MAX_SLOTS];
          int count;
      };
    """
    def __init__(self, max_slots: int, max_capacity: float):
        self.max_slots = max_slots
        self.max_capacity = max_capacity
        self.items = []  # list of ItemStack

    def clear(self):
        self.items = []

    def get_total_weight(self, archetypes: dict) -> float:
        """
        Aggregates total mass across all item stacks.
        Supports negative weights (magical weight-reduction charms).
        """
        total = 0.0
        for stack in self.items:
            arch = archetypes.get(stack.archetype_id)
            if arch is not None:
                total += arch.unit_weight * float(stack.count)
        return max(0.0, total)

    def add_item(self, archetype_id: int, count: int = 1) -> bool:
        """Adds to an existing stack or appends a new stack if slots are available."""
        # Try stacking first
        for stack in self.items:
            if stack.archetype_id == archetype_id:
                stack.count += count
                return True

        if len(self.items) < self.max_slots:
            self.items.append(ItemStack(archetype_id, count))
            return True
        return False

    def remove_item(self, archetype_id: int, count: int = 1) -> bool:
        """Removes count items from the matching stack."""
        for i in range(len(self.items)):
            if self.items[i].archetype_id == archetype_id:
                if self.items[i].count > count:
                    self.items[i].count -= count
                    return True
                else:
                    self.items.pop(i)
                    return True
        return False


class EncumbranceState:
    """
    Computed telemetry snapshot representing load tier, speed, and stamina multipliers.
    C++ Equivalent:
      struct EncumbranceState {
          float current_weight;
          float max_capacity;
          float ratio;
          int tier;
          const char* tier_name;
          float speed_multiplier;
          float stamina_drain_multiplier;
          bool can_sprint;
      };
    """
    def __init__(self, current_weight: float, max_capacity: float,
                 ratio: float, tier: int, tier_name: str,
                 speed_multiplier: float, stamina_drain_multiplier: float,
                 can_sprint: bool):
        self.current_weight = current_weight
        self.max_capacity = max_capacity
        self.ratio = ratio
        self.tier = tier
        self.tier_name = tier_name
        self.speed_multiplier = speed_multiplier
        self.stamina_drain_multiplier = stamina_drain_multiplier
        self.can_sprint = can_sprint


class EncumbrancePipeline:
    """
    Mathematical evaluation engine mapping carried weight to physical penalties.
    Decoupled from input and character rendering.
    """
    def __init__(self):
        pass

    def evaluate(self, current_weight: float, max_capacity: float,
                 penalty_enabled: bool = True) -> EncumbranceState:
        ratio = current_weight / max(1.0, max_capacity)

        if not penalty_enabled:
            # Infinite Carry Mode (Comparison demo)
            return EncumbranceState(
                current_weight, max_capacity, ratio,
                TIER_LIGHT, "UNRESTRICTED (PENALTY OFF)",
                1.0, 1.0, True
            )

        # Standard Realistic Encumbrance Evaluation
        if ratio <= 0.50:
            tier = TIER_LIGHT
            tier_name = "LIGHT LOAD (Agile)"
            speed_mult = 1.0
            stamina_mult = 1.0
            can_sprint = True
        elif ratio <= 0.75:
            tier = TIER_MEDIUM
            tier_name = "MEDIUM LOAD (Normal)"
            # Linear curve from 1.0 down to 0.85
            t = (ratio - 0.50) / 0.25
            speed_mult = 1.0 - 0.15 * t
            stamina_mult = 1.0 + 0.35 * t
            can_sprint = True
        elif ratio <= 1.00:
            tier = TIER_HEAVY
            tier_name = "HEAVY LOAD (Encumbered)"
            # Linear curve from 0.85 down to 0.60
            t = (ratio - 0.75) / 0.25
            speed_mult = 0.85 - 0.25 * t
            stamina_mult = 1.35 + 0.65 * t
            can_sprint = True
        elif ratio <= 1.50:
            tier = TIER_OVERLOADED
            tier_name = "OVERENCUMBERED! (Cannot Sprint)"
            # Sharp drop from 0.60 down to 0.28
            t = (ratio - 1.00) / 0.50
            speed_mult = max(0.25, 0.45 - 0.17 * t)
            stamina_mult = 2.5
            can_sprint = False
        else:
            tier = TIER_CRUSHED
            tier_name = "CRUSHED UNDER WEIGHT! (Crawl)"
            speed_mult = 0.10
            stamina_mult = 3.0
            can_sprint = False

        return EncumbranceState(
            current_weight, max_capacity, ratio,
            tier, tier_name, speed_mult, stamina_mult, can_sprint
        )


# ==============================================================================
# BLOCK 2: WORLD SIMULATION & ENTITIES
# ==============================================================================

class GroundPickup:
    """An item resting in the 2D world arena ready to be collected."""
    def __init__(self, archetype_id: int, x: float, y: float, count: int = 1):
        self.archetype_id = archetype_id
        self.pos = Vector2(x, y)
        self.count = count
        self.bob_timer = random.uniform(0.0, math.pi * 2.0)


class PlayerCharacter:
    """The adventurer subject to encumbrance physics and stamina drain."""
    def __init__(self, x: float, y: float):
        self.pos = Vector2(x, y)
        self.vel = Vector2(0.0, 0.0)
        self.facing_angle = 0.0
        self.walk_timer = 0.0

        self.base_speed = 220.0       # pixels per second
        self.sprint_bonus = 130.0     # extra sprint speed

        self.stamina = 100.0
        self.max_stamina = 100.0
        self.is_sprinting = False

        self.inventory = InventoryContainer(max_slots=12, max_capacity=60.0)

    def update(self, move_dir: Vector2, want_sprint: bool,
               enc: EncumbranceState, dt: float):
        # 1. Determine Effective Speed
        effective_base_speed = self.base_speed * enc.speed_multiplier
        self.is_sprinting = False

        move_len = math.sqrt(move_dir.x * move_dir.x + move_dir.y * move_dir.y)

        if move_len > 0.01:
            self.walk_timer += dt * (effective_base_speed / 100.0)
            self.facing_angle = math.atan2(move_dir.y, move_dir.x)

            # Sprinting check
            if want_sprint and enc.can_sprint and self.stamina > 5.0:
                self.is_sprinting = True
                effective_speed = effective_base_speed + self.sprint_bonus * enc.speed_multiplier
                stamina_cost = 18.0 * enc.stamina_drain_multiplier * dt
                self.stamina = max(0.0, self.stamina - stamina_cost)
            else:
                effective_speed = effective_base_speed
                if enc.tier <= TIER_HEAVY:
                    # Regenerate stamina while walking if not overencumbered
                    self.stamina = min(self.max_stamina, self.stamina + 12.0 * dt)

            # Dampen velocity
            target_vel_x = (move_dir.x / move_len) * effective_speed
            target_vel_y = (move_dir.y / move_len) * effective_speed
            self.vel.x = damp(self.vel.x, target_vel_x, 14.0, dt)
            self.vel.y = damp(self.vel.y, target_vel_y, 14.0, dt)
        else:
            self.vel.x = damp(self.vel.x, 0.0, 16.0, dt)
            self.vel.y = damp(self.vel.y, 0.0, 16.0, dt)
            # Faster stamina regeneration while standing still
            self.stamina = min(self.max_stamina, self.stamina + 28.0 * dt)

        # Move and clamp within arena bounds
        self.pos.x += self.vel.x * dt
        self.pos.y += self.vel.y * dt

        padding = 24.0
        self.pos.x = max(ARENA_X + padding, min(ARENA_X + ARENA_W - padding, self.pos.x))
        self.pos.y = max(ARENA_Y + padding, min(ARENA_Y + ARENA_H - padding, self.pos.y))


class PackMuleCompanion:
    """
    Companion beast with high cargo capacity following the player.
    Saddlebags visually expand as cargo weight increases.
    """
    def __init__(self, x: float, y: float):
        self.pos = Vector2(x, y)
        self.vel = Vector2(0.0, 0.0)
        self.facing_angle = 0.0
        self.walk_timer = 0.0
        self.speed = 180.0
        self.inventory = InventoryContainer(max_slots=16, max_capacity=200.0)

    def update(self, player_pos: Vector2, dt: float):
        dx = player_pos.x - self.pos.x
        dy = player_pos.y - self.pos.y
        dist = math.sqrt(dx * dx + dy * dy)

        # Follow leashing behavior: follow if dist > 95px, stop if dist < 70px
        if dist > 85.0:
            self.facing_angle = math.atan2(dy, dx)
            # Speed up if falling far behind
            cur_speed = self.speed * (1.5 if dist > 200.0 else 1.0)
            target_vx = (dx / dist) * cur_speed
            target_vy = (dy / dist) * cur_speed
            self.vel.x = damp(self.vel.x, target_vx, 6.0, dt)
            self.vel.y = damp(self.vel.y, target_vy, 6.0, dt)
            self.walk_timer += dt * 4.0
        else:
            self.vel.x = damp(self.vel.x, 0.0, 10.0, dt)
            self.vel.y = damp(self.vel.y, 0.0, 10.0, dt)

        self.pos.x += self.vel.x * dt
        self.pos.y += self.vel.y * dt

        padding = 28.0
        self.pos.x = max(ARENA_X + padding, min(ARENA_X + ARENA_W - padding, self.pos.x))
        self.pos.y = max(ARENA_Y + padding, min(ARENA_Y + ARENA_H - padding, self.pos.y))


class OverloadedMuleSimulation:
    """
    Coordinates player, pack mule, ground pickups, and encumbrance evaluations.
    """
    def __init__(self):
        self.archetypes = {}
        self._init_archetypes()

        self.player = PlayerCharacter(ARENA_X + 220, ARENA_Y + 220)
        self.mule = PackMuleCompanion(ARENA_X + 150, ARENA_Y + 240)
        self.pickups = []
        self.pipeline = EncumbrancePipeline()

        self.penalty_enabled = True      # [F1] Toggle: Realistic vs Infinite Carry
        self.selected_player_slot = 0
        self.selected_mule_slot = 0
        self.active_panel_focus = 0       # 0 = Player, 1 = Mule

        self.feedback_banner = "Welcome to Overloaded Mule! Gather heavy loot and test encumbrance."
        self.banner_timer = 5.0

        self.reset_simulation()

    def _init_archetypes(self):
        """Initializes diverse item mass profiles: from feathers to anvils."""
        self.archetypes[ITEM_ANVIL] = ItemArchetype(
            ITEM_ANVIL, "Blacksmith Anvil", "Heavy Metal", 45.0, 150, Color(160, 175, 195, 255)
        )
        self.archetypes[ITEM_DRAGON_BONE] = ItemArchetype(
            ITEM_DRAGON_BONE, "Dragon Femur", "Monster Trophy", 32.0, 280, Color(230, 225, 205, 255)
        )
        self.archetypes[ITEM_STEEL_ARMOR] = ItemArchetype(
            ITEM_STEEL_ARMOR, "Steel Cuirass", "Heavy Armor", 22.0, 190, Color(110, 140, 185, 255)
        )
        self.archetypes[ITEM_METEOR_ORE] = ItemArchetype(
            ITEM_METEOR_ORE, "Meteorite Ore", "Dense Mineral", 16.0, 130, Color(180, 95, 230, 255)
        )
        self.archetypes[ITEM_GOLD_BAR] = ItemArchetype(
            ITEM_GOLD_BAR, "Gold Bullion", "Valuable Metal", 12.0, 320, Color(245, 210, 50, 255)
        )
        self.archetypes[ITEM_GREATSWORD] = ItemArchetype(
            ITEM_GREATSWORD, "Executioner Blade", "Weapon", 7.5, 95, Color(130, 210, 240, 255)
        )
        self.archetypes[ITEM_CAMPING_GEAR] = ItemArchetype(
            ITEM_CAMPING_GEAR, "Iron Cookpot", "Supplies", 4.0, 25, Color(185, 130, 85, 255)
        )
        self.archetypes[ITEM_BREAD_LOAF] = ItemArchetype(
            ITEM_BREAD_LOAF, "Ration Loaf", "Food", 0.6, 5, Color(225, 170, 95, 255)
        )
        self.archetypes[ITEM_HEALTH_POTION] = ItemArchetype(
            ITEM_HEALTH_POTION, "Healing Elixir", "Potion", 0.3, 30, Color(245, 60, 75, 255)
        )
        self.archetypes[ITEM_FEATHER_CHARM] = ItemArchetype(
            ITEM_FEATHER_CHARM, "Feather Talisman", "Artifact", -15.0, 220, Color(60, 240, 180, 255)
        )

    def reset_simulation(self):
        """Restores starting loadouts and scatters diverse loot across the arena."""
        self.player.pos = Vector2(ARENA_X + 220, ARENA_Y + 220)
        self.player.vel = Vector2(0.0, 0.0)
        self.player.stamina = 100.0
        self.player.inventory.clear()

        self.mule.pos = Vector2(ARENA_X + 140, ARENA_Y + 240)
        self.mule.vel = Vector2(0.0, 0.0)
        self.mule.inventory.clear()

        # Initial player load (Light: ~16 kg / 60 kg)
        self.player.inventory.add_item(ITEM_GREATSWORD, 1)    # 7.5 kg
        self.player.inventory.add_item(ITEM_CAMPING_GEAR, 1)  # 4.0 kg
        self.player.inventory.add_item(ITEM_BREAD_LOAF, 4)    # 2.4 kg
        self.player.inventory.add_item(ITEM_HEALTH_POTION, 5) # 1.5 kg

        # Initial mule load (Moderate: ~40 kg / 200 kg)
        self.mule.inventory.add_item(ITEM_STEEL_ARMOR, 1)     # 22.0 kg
        self.mule.inventory.add_item(ITEM_METEOR_ORE, 1)      # 16.0 kg

        # Scatter loot pickups around the arena
        self.pickups = []
        scatter_defs = [
            (ITEM_ANVIL, 1, ARENA_X + 480, ARENA_Y + 120),
            (ITEM_DRAGON_BONE, 1, ARENA_X + 620, ARENA_Y + 250),
            (ITEM_STEEL_ARMOR, 1, ARENA_X + 380, ARENA_Y + 320),
            (ITEM_METEOR_ORE, 2, ARENA_X + 540, ARENA_Y + 340),
            (ITEM_GOLD_BAR, 2, ARENA_X + 300, ARENA_Y + 110),
            (ITEM_ANVIL, 1, ARENA_X + 160, ARENA_Y + 110),
            (ITEM_FEATHER_CHARM, 1, ARENA_X + 670, ARENA_Y + 130),
            (ITEM_HEALTH_POTION, 3, ARENA_X + 440, ARENA_Y + 220),
            (ITEM_BREAD_LOAF, 2, ARENA_X + 240, ARENA_Y + 350)
        ]
        for aid, count, px, py in scatter_defs:
            self.pickups.append(GroundPickup(aid, px, py, count))

        self.feedback_banner = "Arena reset: Fresh loot spawned! Walk up and press E/A to grab."
        self.banner_timer = 4.0

    def get_player_encumbrance(self) -> EncumbranceState:
        w = self.player.inventory.get_total_weight(self.archetypes)
        return self.pipeline.evaluate(w, self.player.inventory.max_capacity, self.penalty_enabled)

    def get_mule_encumbrance(self) -> EncumbranceState:
        w = self.mule.inventory.get_total_weight(self.archetypes)
        return self.pipeline.evaluate(w, self.mule.inventory.max_capacity, penalty_enabled=False)

    def pick_up_nearby_loot(self) -> bool:
        """Picks up the closest ground loot item within 50 pixels."""
        closest_idx = -1
        min_dist = 52.0

        for i in range(len(self.pickups)):
            p = self.pickups[i]
            dx = self.player.pos.x - p.pos.x
            dy = self.player.pos.y - p.pos.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < min_dist:
                min_dist = dist
                closest_idx = i

        if closest_idx >= 0:
            p = self.pickups.pop(closest_idx)
            arch = self.archetypes[p.archetype_id]
            added = self.player.inventory.add_item(p.archetype_id, p.count)
            if added:
                w_added = arch.unit_weight * p.count
                sign_str = f"+{w_added:.1f}" if w_added >= 0 else f"{w_added:.1f}"
                self.feedback_banner = f"Picked up {p.count}x {arch.name} ({sign_str} kg)!"
                self.banner_timer = 3.0
                return True
        return False

    def drop_selected_player_item(self) -> bool:
        """Drops 1 count of the selected item from the player inventory onto the ground."""
        if 0 <= self.selected_player_slot < len(self.player.inventory.items):
            stack = self.player.inventory.items[self.selected_player_slot]
            arch = self.archetypes[stack.archetype_id]

            # Spawn ground pickup near player with slight offset
            offset_x = random.uniform(-25.0, 25.0)
            offset_y = random.uniform(-25.0, 25.0)
            self.pickups.append(GroundPickup(stack.archetype_id, self.player.pos.x + offset_x, self.player.pos.y + offset_y, 1))

            self.player.inventory.remove_item(stack.archetype_id, 1)
            self.selected_player_slot = max(0, min(self.selected_player_slot, len(self.player.inventory.items) - 1))
            self.feedback_banner = f"Dropped 1x {arch.name} ({arch.unit_weight:.1f} kg) onto ground."
            self.banner_timer = 2.5
            return True
        return False

    def transfer_player_to_mule(self) -> bool:
        """Transfers 1 count of the selected player item into the Mule's saddlebags."""
        if 0 <= self.selected_player_slot < len(self.player.inventory.items):
            stack = self.player.inventory.items[self.selected_player_slot]
            arch = self.archetypes[stack.archetype_id]

            added = self.mule.inventory.add_item(stack.archetype_id, 1)
            if added:
                self.player.inventory.remove_item(stack.archetype_id, 1)
                self.selected_player_slot = max(0, min(self.selected_player_slot, len(self.player.inventory.items) - 1))
                self.feedback_banner = f"Transferred 1x {arch.name} ({arch.unit_weight:.1f} kg) to Mule saddlebags!"
                self.banner_timer = 2.5
                return True
            else:
                self.feedback_banner = "Mule saddlebags are completely full!"
                self.banner_timer = 2.5
        return False

    def transfer_mule_to_player(self) -> bool:
        """Retrieves 1 count of the selected item from the Mule to the Player."""
        if 0 <= self.selected_mule_slot < len(self.mule.inventory.items):
            stack = self.mule.inventory.items[self.selected_mule_slot]
            arch = self.archetypes[stack.archetype_id]

            added = self.player.inventory.add_item(stack.archetype_id, 1)
            if added:
                self.mule.inventory.remove_item(stack.archetype_id, 1)
                self.selected_mule_slot = max(0, min(self.selected_mule_slot, len(self.mule.inventory.items) - 1))
                self.feedback_banner = f"Retrieved 1x {arch.name} ({arch.unit_weight:.1f} kg) from Mule!"
                self.banner_timer = 2.5
                return True
            else:
                self.feedback_banner = "Player backpack slots are full!"
                self.banner_timer = 2.5
        return False

    def quick_offload_to_mule(self) -> int:
        """
        Greedy offload heuristic: moves the heaviest items from Player to Mule
        until the player returns to Light Load (<= 50% capacity).
        """
        transferred = 0
        while True:
            enc = self.get_player_encumbrance()
            if enc.tier == TIER_LIGHT or len(self.player.inventory.items) == 0:
                break

            # Find heaviest stack in player inventory
            heaviest_idx = -1
            max_unit_w = -999.0
            for i in range(len(self.player.inventory.items)):
                stack = self.player.inventory.items[i]
                arch = self.archetypes[stack.archetype_id]
                if arch.unit_weight > max_unit_w:
                    max_unit_w = arch.unit_weight
                    heaviest_idx = i

            if heaviest_idx >= 0 and max_unit_w > 0:
                stack = self.player.inventory.items[heaviest_idx]
                added = self.mule.inventory.add_item(stack.archetype_id, 1)
                if added:
                    self.player.inventory.remove_item(stack.archetype_id, 1)
                    transferred += 1
                else:
                    break
            else:
                break

        if transferred > 0:
            self.feedback_banner = f"Quick-Offload: Transferred {transferred} heavy item(s) to Mule! Regained agility."
        else:
            self.feedback_banner = "Quick-Offload: Already at light load or Mule is full."
        self.banner_timer = 3.5
        return transferred


# ==============================================================================
# BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY ([Tab] & [F1])
# ==============================================================================

def draw_xray_telemetry(sim: OverloadedMuleSimulation):
    """
    Renders internal pipeline metrics: dynamic velocity curve evaluation,
    encumbrance tier thresholds, stamina drain scaling, and memory structs.
    """
    draw_rectangle(TELEMETRY_X, TELEMETRY_Y, TELEMETRY_W, TELEMETRY_H, COLOR_PANEL_BG)
    draw_rectangle_lines(TELEMETRY_X, TELEMETRY_Y, TELEMETRY_W, TELEMETRY_H, COLOR_PANEL_BORDER)

    # Header
    draw_rectangle(TELEMETRY_X, TELEMETRY_Y, TELEMETRY_W, 32, Color(24, 32, 50, 255))
    draw_text("X-RAY ENCUMBRANCE INSPECTOR [Tab]", TELEMETRY_X + 14, TELEMETRY_Y + 8, 15, COLOR_ACCENT_CYAN)

    y = TELEMETRY_Y + 44
    enc = sim.get_player_encumbrance()

    # 1. Real-Time Velocity vs Weight Evaluation Curve
    draw_text("1. Velocity Modulator Curve V(R):", TELEMETRY_X + 14, y, 13, COLOR_TEXT_MAIN)
    y += 18

    graph_x = TELEMETRY_X + 14
    graph_y = y
    graph_w = TELEMETRY_W - 28
    graph_h = 105

    draw_rectangle(graph_x, graph_y, graph_w, graph_h, Color(14, 18, 28, 255))
    draw_rectangle_lines(graph_x, graph_y, graph_w, graph_h, COLOR_PANEL_BORDER)

    # Draw tier background bands on graph
    # 0..50% (Light)
    x_50 = graph_x + int(graph_w * (0.50 / 1.60))
    x_75 = graph_x + int(graph_w * (0.75 / 1.60))
    x_100 = graph_x + int(graph_w * (1.00 / 1.60))

    draw_rectangle(graph_x, graph_y, x_50 - graph_x, graph_h, Color(40, 180, 80, 25))
    draw_rectangle(x_50, graph_y, x_75 - x_50, graph_h, Color(220, 190, 40, 25))
    draw_rectangle(x_75, graph_y, x_100 - x_75, graph_h, Color(240, 120, 30, 30))
    draw_rectangle(x_100, graph_y, (graph_x + graph_w) - x_100, graph_h, Color(240, 40, 40, 40))

    # Threshold divider lines
    draw_line(x_50, graph_y, x_50, graph_y + graph_h, Color(60, 180, 90, 120))
    draw_line(x_75, graph_y, x_75, graph_y + graph_h, Color(220, 190, 40, 120))
    draw_line(x_100, graph_y, x_100, graph_y + graph_h, Color(240, 60, 60, 180))

    draw_text("50%", x_50 - 10, graph_y + graph_h - 14, 10, Color(160, 180, 200, 200))
    draw_text("75%", x_75 - 10, graph_y + graph_h - 14, 10, Color(160, 180, 200, 200))
    draw_text("100% (MAX)", x_100 - 24, graph_y + 4, 10, COLOR_TIER_OVERLOADED)

    # Plot velocity curve points
    steps = 40
    prev_px = graph_x
    prev_py = graph_y + int((1.0 - 1.0) * (graph_h - 16)) + 12

    for s in range(steps + 1):
        ratio_eval = (s / float(steps)) * 1.60
        sim_state = sim.pipeline.evaluate(ratio_eval * 60.0, 60.0, sim.penalty_enabled)
        cx = graph_x + int((s / float(steps)) * graph_w)
        cy = graph_y + int((1.0 - sim_state.speed_multiplier) * (graph_h - 24)) + 10
        if s > 0:
            draw_line(prev_px, prev_py, cx, cy, COLOR_ACCENT_CYAN)
        prev_px = cx
        prev_py = cy

    # Draw current operating point dot
    cur_plot_ratio = min(1.60, enc.ratio)
    cur_dot_x = graph_x + int((cur_plot_ratio / 1.60) * graph_w)
    cur_dot_y = graph_y + int((1.0 - enc.speed_multiplier) * (graph_h - 24)) + 10
    draw_circle(cur_dot_x, cur_dot_y, 5, COLOR_ACCENT_GOLD)
    draw_circle_lines(cur_dot_x, cur_dot_y, 7, Color(255, 255, 255, 220))

    y += graph_h + 14

    # 2. Mathematical Pipeline Equation
    draw_rectangle(TELEMETRY_X + 14, y, TELEMETRY_W - 28, 52, Color(14, 18, 28, 255))
    draw_rectangle_lines(TELEMETRY_X + 14, y, TELEMETRY_W - 28, 52, Color(35, 48, 72, 255))
    draw_text("Continuous Speed Modulator Formula:", TELEMETRY_X + 20, y + 6, 11, COLOR_ACCENT_GOLD)
    draw_text("V(R) = V_base * max(0.10, 1.0 - 0.75 * R)  [R <= 1.0]", TELEMETRY_X + 20, y + 20, 11, COLOR_TEXT_MAIN)
    draw_text("V(R) = V_base * max(0.08, 0.28 - 0.15*(R-1)) [R > 1.0]", TELEMETRY_X + 20, y + 34, 11, COLOR_TEXT_DIM)
    y += 64

    # 3. Encumbrance Tier Breakdown
    draw_text("2. Encumbrance Tier Classification:", TELEMETRY_X + 14, y, 13, COLOR_TEXT_MAIN)
    y += 18

    tier_cols = [COLOR_TIER_LIGHT, COLOR_TIER_MEDIUM, COLOR_TIER_HEAVY, COLOR_TIER_OVERLOADED, COLOR_TIER_CRUSHED]
    tier_labels = [
        "Light Load (0 - 50%)    : 100% Speed, 1.0x Stamina Drain",
        "Medium Load (50 - 75%) : 85% Speed, 1.35x Stamina Drain",
        "Heavy Load (75 - 100%) : 60% Speed, 2.0x Stamina Drain",
        "Overencumbered (100%+) : 28% Speed, Sprint Disabled!",
        "Crushed (> 150%)       : 10% Speed Crawl, Severe Strain"
    ]
    for i in range(5):
        is_cur = (enc.tier == i)
        prefix = "> " if is_cur else "  "
        col = tier_cols[i] if is_cur else Color(130, 145, 175, 255)
        draw_text(prefix + tier_labels[i], TELEMETRY_X + 14, y, 11, col)
        y += 15
    y += 10

    # 4. Live Multiplier Telemetry
    draw_text("3. Active Physics Telemetry:", TELEMETRY_X + 14, y, 13, COLOR_TEXT_MAIN)
    y += 18
    draw_text(f"Effective Velocity : {sim.player.base_speed * enc.speed_multiplier:.1f} px/s (x{enc.speed_multiplier:.2f})", TELEMETRY_X + 14, y, 12, COLOR_ACCENT_CYAN)
    y += 16
    draw_text(f"Stamina Drain Rate : x{enc.stamina_drain_multiplier:.2f} multiplier", TELEMETRY_X + 14, y, 12, COLOR_ACCENT_GOLD)
    y += 16
    sprint_status = "ENABLED (Agile)" if enc.can_sprint else "DISABLED (Overloaded)"
    sprint_col = COLOR_TIER_LIGHT if enc.can_sprint else COLOR_TIER_OVERLOADED
    draw_text(f"Sprint Capability  : {sprint_status}", TELEMETRY_X + 14, y, 12, sprint_col)
    y += 24

    # 5. Pack Mule Leash Dynamics
    draw_text("4. Pack Mule Companion Telemetry:", TELEMETRY_X + 14, y, 13, COLOR_TEXT_MAIN)
    y += 18
    dx = sim.player.pos.x - sim.mule.pos.x
    dy = sim.player.pos.y - sim.mule.pos.y
    mule_dist = math.sqrt(dx * dx + dy * dy)
    mule_enc = sim.get_mule_encumbrance()

    draw_text(f"Mule Cargo Mass   : {mule_enc.current_weight:.1f} / {mule_enc.max_capacity:.1f} kg ({mule_enc.ratio*100.0:.1f}%)", TELEMETRY_X + 14, y, 12, COLOR_TEXT_MAIN)
    y += 16
    draw_text(f"Distance to Player: {mule_dist:.1f} px (Leash Target: 85 px)", TELEMETRY_X + 14, y, 12, COLOR_TEXT_DIM)
    y += 24

    # 6. Pattern Comparison Toggle [F1]
    draw_text("5. Pattern Comparison Mode ([F1]):", TELEMETRY_X + 14, y, 13, COLOR_TEXT_MAIN)
    y += 18
    if sim.penalty_enabled:
        mode_str = "REALISTIC WEIGHT PENALTIES (ACTIVE)"
        mode_col = COLOR_TIER_LIGHT
        mode_desc = "Mass directly modulates speed, sprint, and stamina."
    else:
        mode_str = "INFINITE CARRY CAPACITY (OFF - ARCADE)"
        mode_col = COLOR_TIER_OVERLOADED
        mode_desc = "Zero penalties: 500kg moves at full sprint speed."
    draw_text(mode_str, TELEMETRY_X + 14, y, 12, mode_col)
    y += 16
    draw_text(mode_desc, TELEMETRY_X + 14, y, 11, COLOR_TEXT_DIM)


# ==============================================================================
# BLOCK 4: MAIN GAME LOOP & AUTOMATED SMOKE TEST
# ==============================================================================

class OverloadedMuleGame:
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()

        self.sfx = SoundLibrary()
        self.sfx.init_defaults()

        self.sim = OverloadedMuleSimulation()
        self.show_xray = True
        self.cursor_flash_timer = 0.0

    def handle_input(self, dt: float):
        # 1. Dual X-Ray Toggle [Tab] / Gamepad Select
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
            self.sfx.play("click", 0.6)

        # 2. Dual Pattern Mode Toggle [F1] / Gamepad LB
        if is_dual_pattern_toggle_pressed():
            self.sim.penalty_enabled = not self.sim.penalty_enabled
            self.sfx.play("click", 0.7)
            if self.sim.penalty_enabled:
                self.sim.feedback_banner = "Encumbrance Penalties ENABLED: Realistic mass physics."
            else:
                self.sim.feedback_banner = "Encumbrance Penalties DISABLED: Infinite carry demo."
            self.sim.banner_timer = 3.5

        # 3. Dual Quick Offload Heuristic [F2] / Gamepad RB
        if is_dual_secondary_toggle_pressed() or is_key_pressed(KEY_F2):
            count = self.sim.quick_offload_to_mule()
            if count > 0:
                self.sfx.play("powerup", 0.8)
            else:
                self.sfx.play("hit", 0.5)

        # 4. Reset Simulation [R] / Gamepad Start
        if is_dual_reset_pressed():
            self.sim.reset_simulation()
            self.sfx.play("laser", 0.6)

        # 5. Adventurer Movement Input
        move_vec = get_dual_move_2d()
        want_sprint = is_dual_dash_down()
        enc = self.sim.get_player_encumbrance()
        self.sim.player.update(move_vec, want_sprint, enc, dt)
        self.sim.mule.update(self.sim.player.pos, dt)

        # 6. Interact / Pick Up Loot: [E] / Space / Gamepad A
        pad_id = get_active_gamepad_id()
        gamepad_a = (pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_FACE_DOWN))
        if is_key_pressed(KEY_E) or is_key_pressed(KEY_SPACE) or gamepad_a:
            picked = self.sim.pick_up_nearby_loot()
            if picked:
                self.sfx.play("coin", 0.7)
            else:
                self.sfx.play("hit", 0.3)

        # 7. Drop Item onto Ground: [X] / Gamepad Y
        gamepad_y = (pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_FACE_UP))
        if is_key_pressed(KEY_X) or gamepad_y:
            dropped = self.sim.drop_selected_player_item()
            if dropped:
                self.sfx.play("hit", 0.8)

        # 8. Transfer between Player & Mule: [T] / Gamepad X
        gamepad_x = (pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_FACE_LEFT))
        if is_key_pressed(KEY_T) or gamepad_x:
            if self.sim.active_panel_focus == 0:
                transferred = self.sim.transfer_player_to_mule()
            else:
                transferred = self.sim.transfer_mule_to_player()

            if transferred:
                self.sfx.play("coin", 0.8)
            else:
                self.sfx.play("hurt", 0.5)

        # 9. Mouse Selection in Inventory Panel
        if is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            m_x = get_mouse_x()
            m_y = get_mouse_y()
            # Check player slot clicks
            p_start_x = PANEL_X + 20
            p_start_y = PANEL_Y + 54
            slot_w = 44
            slot_h = 44
            stride = slot_w + 6

            for i in range(self.sim.player.inventory.max_slots):
                sx = p_start_x + (i % 6) * stride
                sy = p_start_y + (i // 6) * stride
                if sx <= m_x <= sx + slot_w and sy <= m_y <= sy + slot_h:
                    self.sim.active_panel_focus = 0
                    self.sim.selected_player_slot = i
                    self.sfx.play("click", 0.4)
                    break

            # Check mule slot clicks
            m_start_x = PANEL_X + 400
            m_start_y = PANEL_Y + 54
            for j in range(self.sim.mule.inventory.max_slots):
                sx = m_start_x + (j % 8) * stride
                sy = m_start_y + (j // 8) * stride
                if sx <= m_x <= sx + slot_w and sy <= m_y <= sy + slot_h:
                    self.sim.active_panel_focus = 1
                    self.sim.selected_mule_slot = j
                    self.sfx.play("click", 0.4)
                    break

    def update(self):
        dt = min(get_frame_time(), 0.05)
        self.cursor_flash_timer += dt
        if self.sim.banner_timer > 0:
            self.sim.banner_timer -= dt

        # Update ground pickups floating bob
        for p in self.sim.pickups:
            p.bob_timer += dt * 3.5

        self.handle_input(dt)

    def draw(self):
        begin_drawing()
        clear_background(COLOR_BG)

        # 1. Top HUD Bar
        draw_rectangle(0, 0, SCREEN_WIDTH, 52, Color(16, 21, 32, 255))
        draw_line(0, 52, SCREEN_WIDTH, 52, COLOR_PANEL_BORDER)
        draw_text("OVERLOADED MULE", 32, 16, 20, COLOR_ACCENT_GOLD)
        draw_text("[Weight-Based Inventory & Dynamic Encumbrance Physics]", 245, 20, 13, COLOR_TEXT_DIM)

        # Top-bar dropdowns & Gamepad status
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)

        # 2. Main World Arena
        self._draw_world_arena()

        # 3. Inventory & Encumbrance Manager Panel (Bottom)
        self._draw_management_panel()

        # 4. X-Ray Telemetry Inspector ([Tab])
        if self.show_xray:
            draw_xray_telemetry(self.sim)

        # 5. Feedback Banner
        if self.sim.banner_timer > 0:
            self._draw_feedback_banner()

        end_drawing()

    def _draw_world_arena(self):
        """Renders the top-down 2D terrain, companion mule, adventurer, and ground loot."""
        # Arena Floor
        draw_rectangle(ARENA_X, ARENA_Y, ARENA_W, ARENA_H, COLOR_ARENA_GROUND)
        draw_rectangle_lines(ARENA_X, ARENA_Y, ARENA_W, ARENA_H, COLOR_ARENA_BORDER)

        # Decorative ground grid marks
        for gx in range(ARENA_X + 60, ARENA_X + ARENA_W, 60):
            draw_line(gx, ARENA_Y, gx, ARENA_Y + ARENA_H, Color(30, 38, 56, 120))
        for gy in range(ARENA_Y + 60, ARENA_Y + ARENA_H, 60):
            draw_line(ARENA_X, gy, ARENA_X + ARENA_W, gy, Color(30, 38, 56, 120))

        # Ground Loot Pickups
        for p in self.sim.pickups:
            arch = self.sim.archetypes[p.archetype_id]
            bob = math.sin(p.bob_timer) * 3.0
            cx = int(p.pos.x)
            cy = int(p.pos.y + bob)

            # Shadow
            draw_ellipse(int(p.pos.x), int(p.pos.y + 12), 12, 6, Color(0, 0, 0, 90))

            # Item Box
            draw_rectangle(cx - 10, cy - 10, 20, 20, arch.badge_color)
            draw_rectangle_lines(cx - 10, cy - 10, 20, 20, Color(245, 250, 255, 220))

            # Weight Tag above item
            weight_total = arch.unit_weight * float(p.count)
            tag_str = f"{weight_total:.1f}kg"
            draw_text(tag_str, cx - 14, cy - 24, 10, COLOR_TEXT_MAIN)

        # Pack Mule Companion
        self._draw_pack_mule(self.sim.mule)

        # Player Adventurer
        self._draw_player(self.sim.player)

        # Proximity interaction prompt if near loot
        for p in self.sim.pickups:
            dx = self.sim.player.pos.x - p.pos.x
            dy = self.sim.player.pos.y - p.pos.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 45.0:
                arch = self.sim.archetypes[p.archetype_id]
                draw_rectangle(int(p.pos.x - 55), int(p.pos.y - 44), 110, 18, Color(16, 22, 34, 220))
                draw_rectangle_lines(int(p.pos.x - 55), int(p.pos.y - 44), 110, 18, COLOR_ACCENT_CYAN)
                draw_text(f"[E / A] Grab {arch.name}", int(p.pos.x - 50), int(p.pos.y - 40), 10, COLOR_TEXT_MAIN)
                break

    def _draw_player(self, player: PlayerCharacter):
        """Renders the player character with encumbrance strain badges."""
        px = int(player.pos.x)
        py = int(player.pos.y)

        # Shadow
        draw_ellipse(px, py + 14, 16, 8, Color(0, 0, 0, 120))

        # Humanoid Body
        draw_humanoid_enemy_2d(
            player.pos,
            player.facing_angle,
            player.walk_timer,
            scale=0.95,
            palette={
                "armor": Color(45, 95, 160, 255),
                "accent": Color(0, 225, 255, 255),
                "skin": Color(230, 195, 165, 255),
                "weapon": Color(210, 220, 235, 255),
                "joint": Color(25, 30, 40, 255)
            }
        )

        # Stamina Bar above head
        bar_w = 40
        bar_h = 5
        bar_x = px - bar_w // 2
        bar_y = py - 32
        draw_rectangle(bar_x, bar_y, bar_w, bar_h, Color(15, 20, 30, 220))
        stamina_pct = player.stamina / player.max_stamina
        fill_w = int(bar_w * stamina_pct)
        draw_rectangle(bar_x, bar_y, fill_w, bar_h, Color(50, 220, 110, 255))
        draw_rectangle_lines(bar_x, bar_y, bar_w, bar_h, Color(40, 60, 90, 255))

        # Encumbrance Warning icon if overloaded
        enc = self.sim.get_player_encumbrance()
        if enc.tier >= TIER_OVERLOADED:
            pulse = math.sin(self.cursor_flash_timer * 8.0)
            if pulse > 0.0:
                draw_rectangle(px - 35, py - 48, 70, 14, Color(220, 40, 40, 230))
                draw_text("OVERLOADED", px - 32, py - 46, 9, Color(255, 255, 255, 255))

    def _draw_pack_mule(self, mule: PackMuleCompanion):
        """Renders the companion Pack Mule with procedurally bulging saddlebags."""
        mx = int(mule.pos.x)
        my = int(mule.pos.y)

        # Shadow
        draw_ellipse(mx, my + 14, 22, 10, Color(0, 0, 0, 110))

        # Mule Torso
        body_col = Color(135, 90, 50, 255)
        draw_ellipse(mx, my, 22, 13, body_col)

        # Head & Long Ears (facing direction)
        hx = mx + int(math.cos(mule.facing_angle) * 20.0)
        hy = my + int(math.sin(mule.facing_angle) * 20.0)
        draw_ellipse(hx, hy, 11, 8, Color(120, 80, 45, 255))

        # Mule Ears
        draw_line_ex(Vector2(float(hx - 4), float(hy - 4)), Vector2(float(hx - 8), float(hy - 14)), 3.0, Color(105, 70, 40, 255))
        draw_line_ex(Vector2(float(hx + 4), float(hy - 4)), Vector2(float(hx + 8), float(hy - 14)), 3.0, Color(105, 70, 40, 255))

        # Mule Eye
        draw_circle(hx + 2, hy - 2, 2, Color(20, 20, 25, 255))

        # Bulging Cargo Saddlebags (scale size with cargo weight!)
        mule_w = mule.inventory.get_total_weight(self.sim.archetypes)
        cargo_ratio = min(1.0, mule_w / mule.inventory.max_capacity)
        bag_radius = 8 + int(8 * cargo_ratio)

        # Left & Right Saddlebags
        perp_x = -math.sin(mule.facing_angle)
        perp_y = math.cos(mule.facing_angle)
        bag1_x = mx + int(perp_x * 12.0)
        bag1_y = my + int(perp_y * 12.0)
        bag2_x = mx - int(perp_x * 12.0)
        bag2_y = my - int(perp_y * 12.0)

        bag_col = Color(195, 160, 105, 255)
        draw_circle(bag1_x, bag1_y, bag_radius, bag_col)
        draw_circle_lines(bag1_x, bag1_y, bag_radius, Color(90, 60, 30, 255))
        draw_circle(bag2_x, bag2_y, bag_radius, bag_col)
        draw_circle_lines(bag2_x, bag2_y, bag_radius, Color(90, 60, 30, 255))

        # Cargo Straps
        draw_line(bag1_x, bag1_y, bag2_x, bag2_y, Color(80, 50, 25, 255))

        # Mule Status Tag
        draw_text("PACK MULE", mx - 26, my - 28, 10, COLOR_ACCENT_GOLD)
        draw_text(f"{mule_w:.1f}kg", mx - 14, my - 16, 9, COLOR_TEXT_DIM)

    def _draw_management_panel(self):
        """Displays Player vs Mule inventories, encumbrance bars, and actions."""
        draw_rectangle(PANEL_X, PANEL_Y, PANEL_W, PANEL_H, COLOR_PANEL_BG)
        draw_rectangle_lines(PANEL_X, PANEL_Y, PANEL_W, PANEL_H, COLOR_PANEL_BORDER)

        enc_p = self.sim.get_player_encumbrance()
        enc_m = self.sim.get_mule_encumbrance()

        # 1. Player Section (Left)
        is_p_active = (self.sim.active_panel_focus == 0)
        p_title_col = COLOR_ACCENT_CYAN if is_p_active else COLOR_TEXT_MAIN
        draw_text("ADVENTURER BACKPACK (Capacity: 60.0 kg)", PANEL_X + 20, PANEL_Y + 12, 13, p_title_col)

        # Player Encumbrance Bar
        bar_w = 340
        bar_h = 14
        bar_x = PANEL_X + 20
        bar_y = PANEL_Y + 32

        draw_rectangle(bar_x, bar_y, bar_w, bar_h, Color(14, 18, 28, 255))
        fill_w = int(bar_w * min(1.0, enc_p.ratio))

        tier_cols = [COLOR_TIER_LIGHT, COLOR_TIER_MEDIUM, COLOR_TIER_HEAVY, COLOR_TIER_OVERLOADED, COLOR_TIER_CRUSHED]
        draw_rectangle(bar_x, bar_y, fill_w, bar_h, tier_cols[enc_p.tier])
        draw_rectangle_lines(bar_x, bar_y, bar_w, bar_h, COLOR_PANEL_BORDER)

        draw_text(f"{enc_p.current_weight:.1f} / {enc_p.max_capacity:.1f} kg ({enc_p.ratio*100.0:.1f}%) - {enc_p.tier_name}",
                  bar_x + 6, bar_y + 1, 10, Color(245, 250, 255, 255))

        # Player Inventory Slots (2 rows of 6 slots)
        slot_w = 44
        slot_h = 44
        stride = slot_w + 6
        p_slot_start_x = PANEL_X + 20
        p_slot_start_y = PANEL_Y + 54

        for i in range(self.sim.player.inventory.max_slots):
            sx = p_slot_start_x + (i % 6) * stride
            sy = p_slot_start_y + (i // 6) * stride

            is_sel = (self.sim.active_panel_focus == 0 and self.sim.selected_player_slot == i)
            slot_bg = Color(24, 32, 48, 255) if is_sel else COLOR_SLOT_EMPTY
            draw_rectangle(sx, sy, slot_w, slot_h, slot_bg)
            border_col = COLOR_SLOT_SELECTED if is_sel else COLOR_SLOT_BORDER
            draw_rectangle_lines(sx, sy, slot_w, slot_h, border_col)

            if i < len(self.sim.player.inventory.items):
                stack = self.sim.player.inventory.items[i]
                arch = self.sim.archetypes[stack.archetype_id]
                draw_rectangle(sx + 6, sy + 6, slot_w - 12, slot_h - 12, arch.badge_color)
                draw_text(f"x{stack.count}", sx + 4, sy + slot_h - 13, 10, COLOR_TEXT_MAIN)
                w_str = f"{arch.unit_weight * stack.count:.1f}"
                draw_text(w_str, sx + 4, sy + 3, 9, Color(240, 240, 255, 220))

        # 2. Mule Section (Right)
        is_m_active = (self.sim.active_panel_focus == 1)
        m_title_col = COLOR_ACCENT_GOLD if is_m_active else COLOR_TEXT_MAIN
        draw_text("PACK MULE SADDLEBAGS (Capacity: 200.0 kg)", PANEL_X + 400, PANEL_Y + 12, 13, m_title_col)

        # Mule Capacity Bar
        m_bar_x = PANEL_X + 400
        m_bar_y = PANEL_Y + 32
        m_bar_w = 340
        draw_rectangle(m_bar_x, m_bar_y, m_bar_w, bar_h, Color(14, 18, 28, 255))
        m_fill_w = int(m_bar_w * min(1.0, enc_m.ratio))
        draw_rectangle(m_bar_x, m_bar_y, m_fill_w, bar_h, COLOR_ACCENT_GOLD)
        draw_rectangle_lines(m_bar_x, m_bar_y, m_bar_w, bar_h, COLOR_PANEL_BORDER)
        draw_text(f"{enc_m.current_weight:.1f} / {enc_m.max_capacity:.1f} kg ({enc_m.ratio*100.0:.1f}%)",
                  m_bar_x + 6, m_bar_y + 1, 10, Color(245, 250, 255, 255))

        # Mule Inventory Slots (2 rows of 8 slots)
        m_slot_start_x = PANEL_X + 400
        m_slot_start_y = PANEL_Y + 54

        for j in range(self.sim.mule.inventory.max_slots):
            sx = m_slot_start_x + (j % 8) * stride
            sy = m_slot_start_y + (j // 8) * stride

            is_sel = (self.sim.active_panel_focus == 1 and self.sim.selected_mule_slot == j)
            slot_bg = Color(36, 32, 24, 255) if is_sel else COLOR_SLOT_EMPTY
            draw_rectangle(sx, sy, slot_w, slot_h, slot_bg)
            border_col = COLOR_ACCENT_GOLD if is_sel else COLOR_SLOT_BORDER
            draw_rectangle_lines(sx, sy, slot_w, slot_h, border_col)

            if j < len(self.sim.mule.inventory.items):
                stack = self.sim.mule.inventory.items[j]
                arch = self.sim.archetypes[stack.archetype_id]
                draw_rectangle(sx + 6, sy + 6, slot_w - 12, slot_h - 12, arch.badge_color)
                draw_text(f"x{stack.count}", sx + 4, sy + slot_h - 13, 10, COLOR_TEXT_MAIN)
                w_str = f"{arch.unit_weight * stack.count:.1f}"
                draw_text(w_str, sx + 4, sy + 3, 9, Color(240, 240, 255, 220))

        # 3. Quick Action Buttons / Controls Footer
        foot_y = PANEL_Y + 160
        draw_text("[E / A] Grab Nearby Loot", PANEL_X + 20, foot_y, 11, COLOR_ACCENT_CYAN)
        draw_text("[T / X] Transfer to Mule/Player", PANEL_X + 175, foot_y, 11, COLOR_ACCENT_GOLD)
        draw_text("[X / Y] Drop Item", PANEL_X + 375, foot_y, 11, COLOR_TIER_OVERLOADED)
        draw_text("[F2 / RB] Quick Offload Heaviest", PANEL_X + 510, foot_y, 11, COLOR_ACCENT_GREEN)

    def _draw_feedback_banner(self):
        """Displays transient top confirmation banners."""
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
    OverloadedMuleGame().run(smoke_test=is_smoke)
