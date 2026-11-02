# -*- coding: utf-8 -*-
"""
Loot Piñata - Weighted Loot Tables, Rarity Tiers & Live Drop Histogram
======================================================================
Section          : 3.4 Progression & Economy
Pattern Category : Progression & Economy Loops
Dimension        : 2D

Problem Solved:
  In RPGs, looter-shooters, and MMOs (Diablo, Borderlands, Destiny, Path of Exile,
  Monster Hunter), naively generating item drops with hardcoded if/else ladders
  causes probability skew, makes adjusting rarity distributions error-prone,
  and complicates dynamic Luck / Magic Find (MF) scaling. Furthermore, players
  frequently misinterpret random drop streaks (the Gambler's Fallacy) without
  understanding the Law of Large Numbers and how empirical frequencies converge
  onto theoretical probabilities over high sample volumes.

How the Patterns Work:
  1. Weighted Probability Table & Cumulative Distribution Function (CDF):
     Each loot item entry holds an immutable base weight w_i. The total table
     weight is W = sum(w_i). The theoretical drop rate is P_i = w_i / W.
     Random sampling generates a uniform real number R in [0, W) and evaluates
     the CDF:
       k = argmin_k { R < sum_{j=0}^k w_j }
     This guarantees exact mathematical proportionality with O(N) or O(log N)
     selection.
  2. Rarity Tier Hierarchy (World of Warcraft / Diablo Standard):
     - Common    (Grey/White) : 60.0% base probability
     - Uncommon  (Green)      : 25.0% base probability
     - Rare      (Blue)       : 10.0% base probability
     - Epic      (Purple)     :  4.0% base probability
     - Legendary (Gold/Orange):  1.0% base probability
  3. Dynamic Magic Find (MF) & Luck Modulation:
     Luck scales high-tier weights by (1 + MF * tier_boost) while compressing
     common junk weights, allowing live tuning of drop distributions.
  4. Empirical Convergence & Real-Time Histogram:
     Tracks actual drop counts N_actual and renders live dual-bar histograms
     contrasting theoretical expectations (P_theory) against empirical outcomes
     (N_actual / N_total), proving how variance diminishes as sample size grows.

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - [W][A][S][D] / Gamepad Left Stick     : Move Player Fighter around piñata arena
  - Left Mouse / [J] / Gamepad RT / X     : Attack Piñata (whack for tactile drops)
  - [Space] / Gamepad RB                  : Burst Hit (pop 20 physical items at once)
  - [F1]  / Gamepad LB                    : Cycle Magic Find (MF): [0% Normal] -> [+100% Luck] -> [+300% God Tier]
  - [F2]  / Gamepad Y                     : Batch Simulation (+100 items rolled instantly)
  - [Tab] / Gamepad View (Select)         : Toggle X-Ray Telemetry & Drop Rate Inspector
  - [Ctrl +/-]                            : Increase / Decrease UI Font Size
  - [F11]                                 : Toggle Fullscreen
  - [R]   / Gamepad Start                 : Reset simulation, histogram stats & piñata
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
WINDOW_TITLE = "Loot Piñata - Weighted Loot Tables & Rarity Tiers (Raylib Pattern Lab)"

# Rarity Tiers
RARITY_COMMON = 0
RARITY_UNCOMMON = 1
RARITY_RARE = 2
RARITY_EPIC = 3
RARITY_LEGENDARY = 4

RARITY_NAMES = {
    RARITY_COMMON: "COMMON",
    RARITY_UNCOMMON: "UNCOMMON",
    RARITY_RARE: "RARE",
    RARITY_EPIC: "EPIC",
    RARITY_LEGENDARY: "LEGENDARY"
}

RARITY_COLORS = {
    RARITY_COMMON: Color(175, 185, 200, 255),       # Weathered Steel / Grey
    RARITY_UNCOMMON: Color(50, 225, 90, 255),       # Radiant Emerald Green
    RARITY_RARE: Color(45, 160, 255, 255),          # Arcane Cobalt Blue
    RARITY_EPIC: Color(195, 75, 255, 255),          # Mystical Amethyst Purple
    RARITY_LEGENDARY: Color(255, 185, 25, 255)      # Celestial Solar Gold
}


# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATION (WEIGHTED LOOT TABLE & CDF)
# ==============================================================================

class LootItemDef:
    """
    Immutable blueprint definition for a droppable item.

    C++ Equivalent:
      struct LootItemDef {
          int id;
          char name[32];
          int rarity;
          float base_weight;
          int score_value;
      };
    """
    def __init__(self, item_id: int, name: str, rarity: int, base_weight: float, score_value: int):
        self.id = item_id
        self.name = name
        self.rarity = rarity
        self.base_weight = float(base_weight)
        self.score_value = score_value


class WeightedLootTable:
    """
    Weighted Random Selection engine utilizing Cumulative Distribution Functions (CDF).
    Supports dynamic Luck / Magic Find (MF) scaling.

    C++ Equivalent:
      class WeightedLootTable {
          std::vector<LootItemDef> items;
          std::vector<float> active_weights;
          std::vector<float> cdf;
          float total_weight;
      };
    """
    def __init__(self):
        self.items = []
        self.active_weights = []
        self.cdf = []
        self.total_weight = 0.0
        self.magic_find = 0.0  # 0.0 = 0%, 1.0 = +100%, 3.0 = +300%

    def add_item(self, item_def: LootItemDef):
        self.items.append(item_def)
        self.rebuild_cdf()

    def set_magic_find(self, mf: float):
        """Updates Magic Find multiplier and rebuilds cumulative weight thresholds."""
        self.magic_find = max(0.0, float(mf))
        self.rebuild_cdf()

    def rebuild_cdf(self):
        """
        Recomputes effective weights and constructs Cumulative Distribution Function (CDF).
        Higher rarity tiers receive quadratic or exponential scaling from Magic Find.
        """
        self.active_weights = []
        self.cdf = []
        running_total = 0.0

        for item in self.items:
            # Magic Find Scaling:
            # Common items receive no bonus; higher tiers receive multiplicative boosts.
            tier_mult = 1.0
            if item.rarity == RARITY_UNCOMMON:
                tier_mult = 1.0 + self.magic_find * 0.45
            elif item.rarity == RARITY_RARE:
                tier_mult = 1.0 + self.magic_find * 1.10
            elif item.rarity == RARITY_EPIC:
                tier_mult = 1.0 + self.magic_find * 2.20
            elif item.rarity == RARITY_LEGENDARY:
                tier_mult = 1.0 + self.magic_find * 4.50

            w = item.base_weight * tier_mult
            self.active_weights.append(w)
            running_total += w
            self.cdf.append(running_total)

        self.total_weight = running_total

    def roll(self) -> LootItemDef:
        """
        Samples an item using the Cumulative Distribution Function (CDF).
        Generates uniform random value R in [0, total_weight) and finds first
        bracket where R < CDF[k].
        """
        if self.total_weight <= 0.0 or not self.items:
            return None

        r = random.random() * self.total_weight

        # Binary search or sequential scan through CDF
        for i in range(len(self.cdf)):
            if r < self.cdf[i]:
                return self.items[i]

        return self.items[-1]

    def get_theoretical_rarity_probabilities(self) -> dict:
        """Returns theoretical probability [0.0..1.0] per rarity tier under current MF."""
        probs = {
            RARITY_COMMON: 0.0,
            RARITY_UNCOMMON: 0.0,
            RARITY_RARE: 0.0,
            RARITY_EPIC: 0.0,
            RARITY_LEGENDARY: 0.0
        }
        if self.total_weight <= 0.0:
            return probs

        for i, item in enumerate(self.items):
            probs[item.rarity] += self.active_weights[i] / self.total_weight

        return probs


# ==============================================================================
# BLOCK 2: WORLD SIMULATION & ENTITIES
# ==============================================================================

class PhysicalLootItem:
    """
    Physical dropped item entity with 2D parabolic ejection physics,
    ground bouncing, and lingering rarity light pillars.
    """
    def __init__(self):
        self.active = False
        self.pos = Vector2(0.0, 0.0)
        self.vel = Vector2(0.0, 0.0)
        self.ground_y = 0.0
        self.item_def = None
        self.bounce_count = 0
        self.life = 0.0
        self.max_life = 8.0
        self.anim_timer = 0.0

    def spawn(self, start_pos: Vector2, item_def: LootItemDef):
        self.active = True
        self.pos.x = start_pos.x
        self.pos.y = start_pos.y
        self.item_def = item_def

        # Ejection velocity in random radial fan with upward bias
        angle = random.uniform(-math.pi * 0.85, -math.pi * 0.15)
        speed = random.uniform(180.0, 360.0)
        self.vel.x = math.cos(angle) * speed
        self.vel.y = math.sin(angle) * speed

        # Rest on ground at random position near bottom of piñata ring
        self.ground_y = random.uniform(480.0, 610.0)
        self.bounce_count = 0
        self.life = 8.0
        self.max_life = 8.0
        self.anim_timer = random.uniform(0.0, 10.0)

    def update(self, dt: float, player_pos: Vector2) -> bool:
        """Returns True if collected by player."""
        if not self.active:
            return False

        self.anim_timer += dt
        self.life -= dt
        if self.life <= 0.0:
            self.active = False
            return False

        # Apply gravity if airborne
        if self.pos.y < self.ground_y or self.vel.y < 0.0:
            self.vel.y += 680.0 * dt  # Gravity
            self.pos.x += self.vel.x * dt
            self.pos.y += self.vel.y * dt

            # Ground bounce collision
            if self.pos.y >= self.ground_y:
                self.pos.y = self.ground_y
                if self.bounce_count < 2:
                    self.bounce_count += 1
                    self.vel.y = -abs(self.vel.y) * 0.42
                    self.vel.x *= 0.65
                else:
                    self.vel.x = 0.0
                    self.vel.y = 0.0

        # Player magnet attraction vacuum when nearby
        dx = player_pos.x - self.pos.x
        dy = player_pos.y - self.pos.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < 42.0:
            self.active = False
            return True
        elif dist < 120.0:
            # Vacuum pull
            pull_spd = (120.0 - dist) * 4.5
            self.pos.x += (dx / dist) * pull_spd * dt
            self.pos.y += (dy / dist) * pull_spd * dt

        return False


class PinataDummy:
    """
    Interactive hanging festive piñata with swinging pendulum physics,
    wobble damping, and procedural festoon ribbons.
    """
    def __init__(self, anchor_x: float, anchor_y: float):
        self.anchor = Vector2(anchor_x, anchor_y)
        self.rope_length = 170.0
        self.pos = Vector2(anchor_x, anchor_y + self.rope_length)
        self.wobble_angle = 0.0
        self.wobble_vel = 0.0
        self.hp = 100
        self.max_hp = 100
        self.flash_timer = 0.0
        self.respawn_timer = 0.0
        self.active = True

    def update(self, dt: float):
        if self.flash_timer > 0.0:
            self.flash_timer = max(0.0, self.flash_timer - dt * 5.0)

        if not self.active:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0.0:
                self.active = True
                self.hp = self.max_hp
                self.wobble_angle = 0.0
                self.wobble_vel = 0.0
            return

        # Damped spring pendulum physics
        spring_k = 24.0
        damping = 3.2
        angular_acc = -spring_k * self.wobble_angle - damping * self.wobble_vel
        self.wobble_vel += angular_acc * dt
        self.wobble_angle += self.wobble_vel * dt

        # Update position along arc
        self.pos.x = self.anchor.x + math.sin(self.wobble_angle) * self.rope_length
        self.pos.y = self.anchor.y + math.cos(self.wobble_angle) * self.rope_length

    def hit(self, damage: int, push_dir_x: float) -> bool:
        """Applies damage and returns True if piñata burst open (0 HP)."""
        if not self.active:
            return False

        self.hp = max(0, self.hp - damage)
        self.flash_timer = 1.0
        self.wobble_vel += push_dir_x * 8.5

        if self.hp <= 0:
            self.active = False
            self.respawn_timer = 1.4
            return True
        return False


class PlayerFighter:
    """Player avatar moving in the 2D arena and whacking the piñata."""
    def __init__(self, x: float, y: float):
        self.pos = Vector2(x, y)
        self.vel = Vector2(0.0, 0.0)
        self.heading = 0.0
        self.speed = 220.0
        self.radius = 18.0
        self.is_attacking = False
        self.attack_timer = 0.0
        self.anim_timer = 0.0

    def update(self, dt: float, move_vec: Vector2, attack_requested: bool):
        self.anim_timer += dt

        if self.attack_timer > 0.0:
            self.attack_timer = max(0.0, self.attack_timer - dt * 4.0)
            if self.attack_timer <= 0.0:
                self.is_attacking = False

        if attack_requested and self.attack_timer <= 0.0:
            self.is_attacking = True
            self.attack_timer = 0.22

        input_len = math.sqrt(move_vec.x * move_vec.x + move_vec.y * move_vec.y)
        if input_len > 0.001:
            dir_x = move_vec.x / input_len
            dir_y = move_vec.y / input_len
            self.vel.x = dir_x * self.speed
            self.vel.y = dir_y * self.speed
            self.heading = math.atan2(dir_y, dir_x)
        else:
            self.vel.x = 0.0
            self.vel.y = 0.0

        self.pos.x += self.vel.x * dt
        self.pos.y += self.vel.y * dt

        # Clamp in left arena zone
        self.pos.x = max(40.0, min(770.0, self.pos.x))
        self.pos.y = max(80.0, min(650.0, self.pos.y))


# ==============================================================================
# BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY ([Tab] & [F1])
# ==============================================================================

def draw_xray_histogram(panel_x: int, panel_y: int, panel_w: int, panel_h: int,
                        loot_table: WeightedLootTable, drop_counts: dict,
                        total_drops: int, total_score: int):
    """
    Renders pedagogical mathematical telemetry overlay contrasting theoretical
    probabilities against real sampled empirical frequencies.
    """
    draw_rectangle(panel_x, panel_y, panel_w, panel_h, Color(10, 14, 24, 240))
    draw_rectangle_lines(panel_x, panel_y, panel_w, panel_h, Color(45, 75, 125, 255))
    draw_rectangle(panel_x, panel_y, panel_w, 28, Color(22, 34, 58, 255))
    draw_text("LOOT TABLE & EMPIRICAL PROBABILITY CDF", panel_x + 12, panel_y + 7, 12, Color(0, 225, 255, 255))

    y = panel_y + 36
    lh = 16

    # 1. Magic Find / Luck Status Banner
    mf_pct = int(loot_table.magic_find * 100)
    mf_name = "NORMAL (0% MF)" if mf_pct == 0 else (
        "HIGH LUCK (+100% MF)" if mf_pct == 100 else "GOD TIER (+300% MF)"
    )
    mf_col = Color(0, 240, 255, 255) if mf_pct == 0 else (
        Color(255, 200, 50, 255) if mf_pct == 100 else Color(255, 80, 220, 255)
    )
    draw_text(f"[F1] Magic Find Level : {mf_name}", panel_x + 12, y, 11, mf_col); y += lh
    draw_text(f"Total Drops Sampled  : {total_drops:,} items | Score: {total_score:,} pts", panel_x + 12, y, 10, Color(200, 225, 255, 255)); y += lh

    draw_line(panel_x + 10, y + 2, panel_x + panel_w - 10, y + 2, Color(40, 65, 105, 200)); y += 8

    # 2. Dual-Bar Rarity Histogram (Theory vs Empirical)
    draw_text("RARITY DISTRIBUTION (THEORY vs SAMPLED):", panel_x + 12, y, 11, Color(245, 210, 80, 255)); y += lh + 2

    theory_probs = loot_table.get_theoretical_rarity_probabilities()
    bar_max_w = 175

    for tier in [RARITY_COMMON, RARITY_UNCOMMON, RARITY_RARE, RARITY_EPIC, RARITY_LEGENDARY]:
        name = RARITY_NAMES[tier]
        col = RARITY_COLORS[tier]
        count = drop_counts[tier]
        p_theory = theory_probs[tier] * 100.0
        p_actual = (count / max(1, total_drops)) * 100.0

        # Rarity label and count
        draw_text(f"{name:<9} : {count:>5} dropped ({p_actual:5.1f}%)", panel_x + 12, y, 10, col)
        y += 14

        # Bar 1: Theoretical Probability
        th_w = max(2, int((p_theory / 100.0) * bar_max_w))
        draw_text("  Theory", panel_x + 14, y, 9, Color(160, 180, 205, 200))
        draw_rectangle(panel_x + 65, y, bar_max_w, 6, Color(20, 28, 42, 255))
        draw_rectangle(panel_x + 65, y, th_w, 6, Color(col.r, col.g, col.b, 120))
        draw_text(f"{p_theory:4.1f}%", panel_x + 65 + bar_max_w + 8, y - 1, 9, Color(170, 195, 225, 200))
        y += 9

        # Bar 2: Empirical Sampled Frequency
        ac_w = max(2, int((p_actual / 100.0) * bar_max_w))
        draw_text("  Sample", panel_x + 14, y, 9, Color(255, 220, 80, 200))
        draw_rectangle(panel_x + 65, y, bar_max_w, 6, Color(20, 28, 42, 255))
        draw_rectangle(panel_x + 65, y, ac_w, 6, col)

        # Delta variance indicator
        delta = p_actual - p_theory
        delta_str = f"{delta:+.1f}%"
        delta_col = Color(80, 255, 120, 255) if abs(delta) < 1.5 else (
            Color(255, 200, 40, 255) if abs(delta) < 3.5 else Color(255, 80, 80, 255)
        )
        draw_text(delta_str, panel_x + 65 + bar_max_w + 8, y - 1, 9, delta_col)
        y += 16

    draw_line(panel_x + 10, y + 2, panel_x + panel_w - 10, y + 2, Color(40, 65, 105, 200)); y += 8

    # 3. Mathematical Principle & Law of Large Numbers Note
    draw_text("THE LAW OF LARGE NUMBERS IN GAME DESIGN:", panel_x + 12, y, 10, Color(140, 185, 235, 255)); y += lh
    draw_text(" * Small Samples (N < 20) : High variance, random streaks", panel_x + 14, y, 9, Color(200, 220, 245, 200)); y += lh
    draw_text(" * Large Samples (N > 500): Empirical bar converges onto Theory", panel_x + 14, y, 9, Color(200, 220, 245, 200)); y += lh
    draw_text(" * CDF Sampling Equation : R in [0, W), find R < CDF[k]", panel_x + 14, y, 9, Color(0, 220, 255, 200)); y += lh
    draw_text(" * Press [F2] / Pad Y     : Batch-roll 100 items instantly", panel_x + 14, y, 9, Color(255, 215, 0, 255)); y += lh


# ==============================================================================
# BLOCK 4: MAIN GAME LOOP & AUTOMATED SMOKE TEST
# ==============================================================================

class LootPinataLab:
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()

        self.sfx = SoundLibrary()
        self.sfx.init_defaults()

        self.show_xray = True
        self.mf_mode_idx = 0
        self.mf_presets = [0.0, 1.0, 3.0]  # 0% Normal, 100% Luck, 300% God

        # 1. Build Weighted Loot Table
        self.loot_table = WeightedLootTable()
        self._init_loot_table()

        # 2. World Simulation Entities
        self.pinata = PinataDummy(anchor_x=420.0, anchor_y=80.0)
        self.player = PlayerFighter(x=320.0, y=420.0)

        # Pre-allocated physical dropped items pool (zero garbage collection)
        self.loot_pool = [PhysicalLootItem() for _ in range(150)]

        # Statistics & Histogram Tracking
        self.drop_counts = {
            RARITY_COMMON: 0,
            RARITY_UNCOMMON: 0,
            RARITY_RARE: 0,
            RARITY_EPIC: 0,
            RARITY_LEGENDARY: 0
        }
        self.total_drops = 0
        self.total_score = 0
        self.last_item_name = "None"
        self.last_item_rarity = RARITY_COMMON

    def _init_loot_table(self):
        # Tier 0: Common (Base Weight: 600.0)
        self.loot_table.add_item(LootItemDef(1, "Rusty Iron Scrap", RARITY_COMMON, base_weight=320.0, score_value=10))
        self.loot_table.add_item(LootItemDef(2, "Cracked Flint Stone", RARITY_COMMON, base_weight=280.0, score_value=15))

        # Tier 1: Uncommon (Base Weight: 250.0)
        self.loot_table.add_item(LootItemDef(3, "Health Draught", RARITY_UNCOMMON, base_weight=140.0, score_value=50))
        self.loot_table.add_item(LootItemDef(4, "Refined Steel Ingot", RARITY_UNCOMMON, base_weight=110.0, score_value=65))

        # Tier 2: Rare (Base Weight: 100.0)
        self.loot_table.add_item(LootItemDef(5, "Arcane Focus Crystal", RARITY_RARE, base_weight=60.0, score_value=150))
        self.loot_table.add_item(LootItemDef(6, "Knight's Crest Shield", RARITY_RARE, base_weight=40.0, score_value=200))

        # Tier 3: Epic (Base Weight: 40.0)
        self.loot_table.add_item(LootItemDef(7, "Voidwalker Grim Tome", RARITY_EPIC, base_weight=24.0, score_value=500))
        self.loot_table.add_item(LootItemDef(8, "Dragon Scale Cuirass", RARITY_EPIC, base_weight=16.0, score_value=650))

        # Tier 4: Legendary (Base Weight: 10.0)
        self.loot_table.add_item(LootItemDef(9, "Solaris Divine Blade", RARITY_LEGENDARY, base_weight=6.0, score_value=2000))
        self.loot_table.add_item(LootItemDef(10, "Phoenix Heart Relic", RARITY_LEGENDARY, base_weight=4.0, score_value=2500))

    def spawn_loot_drop(self, spawn_pos: Vector2):
        """Rolls an item from the weighted table and activates a physical drop."""
        item_def = self.loot_table.roll()
        if not item_def:
            return

        # Record in empirical statistics
        self.drop_counts[item_def.rarity] += 1
        self.total_drops += 1
        self.last_item_name = item_def.name
        self.last_item_rarity = item_def.rarity

        # Play rarity-specific audio chime
        if item_def.rarity == RARITY_LEGENDARY:
            self.sfx.play("powerup", 0.9)
        elif item_def.rarity == RARITY_EPIC:
            self.sfx.play("coin", 0.85)

        # Spawn physical bouncing entity from pool
        for drop in self.loot_pool:
            if not drop.active:
                drop.spawn(spawn_pos, item_def)
                break

    def batch_roll_simulation(self, count: int = 100):
        """Instantly rolls items mathematically to demonstrate Law of Large Numbers."""
        for _ in range(count):
            item_def = self.loot_table.roll()
            if item_def:
                self.drop_counts[item_def.rarity] += 1
                self.total_drops += 1
                self.last_item_name = item_def.name
                self.last_item_rarity = item_def.rarity
                self.total_score += item_def.score_value
        self.sfx.play("coin", 0.7)

    def handle_input(self, dt: float):
        # Pattern & X-Ray Toggles
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
            self.sfx.play("click", 0.6)

        if is_dual_pattern_toggle_pressed():
            # Cycle Magic Find / Luck preset
            self.mf_mode_idx = (self.mf_mode_idx + 1) % len(self.mf_presets)
            new_mf = self.mf_presets[self.mf_mode_idx]
            self.loot_table.set_magic_find(new_mf)
            self.sfx.play("coin", 0.75)

        # Batch Simulation Roll ([F2] / Gamepad Y)
        if is_dual_secondary_toggle_pressed() or is_key_pressed(KEY_F2) or is_dual_secondary_fire_pressed():
            self.batch_roll_simulation(100)

        # Reset Simulation & Stats ([R] / Gamepad Start)
        if is_dual_reset_pressed():
            for k in self.drop_counts:
                self.drop_counts[k] = 0
            self.total_drops = 0
            self.total_score = 0
            for drop in self.loot_pool:
                drop.active = False
            self.pinata.active = True
            self.pinata.hp = self.pinata.max_hp
            self.pinata.wobble_angle = 0.0
            self.pinata.wobble_vel = 0.0
            self.sfx.play("powerup", 0.7)

        # Player Movement (WASD + Gamepad Left Stick)
        move_input = get_dual_move_2d(deadzone=0.18, use_arrow_keys=True)
        attack_pressed = is_dual_primary_fire_pressed()
        self.player.update(dt, move_input, attack_pressed)

        # Attack Whack Collision against Piñata
        if self.player.is_attacking and self.pinata.active:
            dx = self.pinata.pos.x - self.player.pos.x
            dy = self.pinata.pos.y - self.player.pos.y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist <= 95.0:
                push_dir = 1.0 if self.player.pos.x < self.pinata.pos.x else -1.0
                burst = self.pinata.hit(damage=25, push_dir_x=push_dir)
                self.sfx.play("hit", 0.8)

                # Spawn loot drops on impact
                num_drops = 22 if burst else random.randint(2, 4)
                for _ in range(num_drops):
                    self.spawn_loot_drop(self.pinata.pos)

                if burst:
                    self.sfx.play("explosion", 0.75)

        # Super Burst Fast-Pop Button ([Space] / Gamepad Jump)
        if is_key_pressed(KEY_SPACE) or is_dual_jump_pressed():
            if self.pinata.active:
                self.pinata.hit(damage=100, push_dir_x=1.2)
                self.sfx.play("explosion", 0.75)
                for _ in range(25):
                    self.spawn_loot_drop(self.pinata.pos)

    def update(self):
        dt = min(get_frame_time(), 0.05)
        self.handle_input(dt)
        self.pinata.update(dt)

        # Update physical loot drops & vacuum collection
        for drop in self.loot_pool:
            collected = drop.update(dt, self.player.pos)
            if collected and drop.item_def:
                self.total_score += drop.item_def.score_value
                self.sfx.play("coin", 0.5)

    def draw_pinata_arena(self):
        """Renders 2D festive wooden floor, festoon rope, piñata dummy, and loot."""
        # Arena floor & festoon borders
        draw_rectangle(20, 56, 780, 654, Color(18, 22, 34, 255))
        draw_rectangle_lines(20, 56, 780, 654, Color(45, 60, 95, 255))

        # Arena target boundary markings
        draw_circle_lines(420, 540, 160.0, Color(35, 48, 75, 255))
        draw_circle_lines(420, 540, 240.0, Color(28, 38, 60, 255))

        # 1. Hanging Cable / Rope
        draw_line(int(self.pinata.anchor.x), int(self.pinata.anchor.y),
                  int(self.pinata.pos.x), int(self.pinata.pos.y), Color(160, 140, 110, 255))
        draw_circle(int(self.pinata.anchor.x), int(self.pinata.anchor.y), 5.0, Color(200, 175, 130, 255))

        # 2. Piñata Dummy Body (Festive Multi-Colored Stripes)
        if self.pinata.active:
            px = int(self.pinata.pos.x)
            py = int(self.pinata.pos.y)

            # Health bar above piñata
            bar_w = 64
            bar_h = 6
            hp_ratio = self.pinata.hp / float(self.pinata.max_hp)
            draw_rectangle(px - bar_w // 2, py - 46, bar_w, bar_h, Color(30, 35, 50, 255))
            draw_rectangle(px - bar_w // 2, py - 46, int(bar_w * hp_ratio), bar_h, Color(255, 60, 60, 255))

            # Hit flash color
            col_flash = Color(255, 255, 255, 255) if self.pinata.flash_timer > 0.0 else None

            # Multi-layer festoon body
            stripes = [
                Color(255, 50, 120, 255),  # Hot Magenta
                Color(0, 220, 255, 255),   # Bright Cyan
                Color(255, 220, 40, 255),  # Golden Yellow
                Color(80, 240, 90, 255)    # Emerald Green
            ]
            sh = 9
            sw = 44
            for s_idx, scol in enumerate(stripes):
                c = col_flash or scol
                draw_rectangle(px - sw // 2, py - 20 + s_idx * sh, sw, sh, c)

            # Festive ears / horns
            draw_triangle(
                Vector2(float(px - 16), float(py - 20)),
                Vector2(float(px - 6), float(py - 20)),
                Vector2(float(px - 14), float(py - 34)),
                col_flash or Color(255, 50, 120, 255)
            )
            draw_triangle(
                Vector2(float(px + 6), float(py - 20)),
                Vector2(float(px + 16), float(py - 20)),
                Vector2(float(px + 14), float(py - 34)),
                col_flash or Color(0, 220, 255, 255)
            )
        else:
            draw_text("PIÑATA BURST! RESPAWNING...", int(self.pinata.anchor.x) - 100, 240, 13, Color(255, 215, 0, 200))

        # 3. Physical Dropped Loot Items
        for drop in self.loot_pool:
            if not drop.active or not drop.item_def:
                continue

            dx = int(drop.pos.x)
            dy = int(drop.pos.y)
            r_col = RARITY_COLORS[drop.item_def.rarity]

            # Vertical rarity light pillar for Rare, Epic, and Legendary
            if drop.item_def.rarity >= RARITY_RARE:
                pillar_h = 45 if drop.item_def.rarity == RARITY_RARE else (65 if drop.item_def.rarity == RARITY_EPIC else 95)
                beam_col = Color(r_col.r, r_col.g, r_col.b, 65)
                draw_rectangle(dx - 3, dy - pillar_h, 6, pillar_h, beam_col)

            # Item gem core
            bob_y = dy + int(math.sin(drop.anim_timer * 6.0) * 3.0)
            draw_circle(dx, bob_y, 7.0, r_col)
            draw_circle_lines(dx, bob_y, 7.0, Color(255, 255, 255, 200))

            # Legendary spark glint
            if drop.item_def.rarity == RARITY_LEGENDARY:
                draw_circle(dx, bob_y, 2.5, Color(255, 255, 255, 255))

        # 4. Player Fighter
        draw_humanoid_enemy_2d(
            self.player.pos,
            facing_angle_rad=self.player.heading,
            anim_timer=self.player.anim_timer,
            scale=1.1,
            is_attacking=self.player.is_attacking
        )

    def draw_hud(self):
        # Top-Left Pattern Banner
        banner_x = 24
        banner_y = 16
        draw_rectangle(banner_x, banner_y, 400, 40, Color(14, 18, 30, 230))
        draw_rectangle_lines(banner_x, banner_y, 400, 40, Color(45, 65, 105, 255))

        draw_text("PATTERN: WEIGHTED LOOT TABLE & RARITY TIERS", banner_x + 12, banner_y + 6, 12, Color(0, 240, 255, 255))
        draw_text("Cumulative Distribution Function (CDF) | Magic Find | Histogram", banner_x + 12, banner_y + 22, 10, Color(180, 215, 245, 255))

        # Bottom-Left Control Quick-Reference
        ctl_w = 360
        ctl_h = 105
        ctl_x = 24
        ctl_y = SCREEN_HEIGHT - ctl_h - 18
        draw_rectangle(ctl_x, ctl_y, ctl_w, ctl_h, Color(12, 16, 26, 225))
        draw_rectangle_lines(ctl_x, ctl_y, ctl_w, ctl_h, Color(45, 65, 100, 255))

        cy = ctl_y + 8
        draw_text("INTERACTIVE LOOT LAB CONTROLS:", ctl_x + 10, cy, 11, Color(0, 220, 255, 255)); cy += 16
        draw_text("Left Click / [J] / Pad RT : Attack Piñata Dummy", ctl_x + 10, cy, 10, Color(200, 220, 245, 255)); cy += 14
        draw_text("[Space] / Gamepad RB    : Burst Pop (+20 Physical Drops)", ctl_x + 10, cy, 10, Color(200, 220, 245, 255)); cy += 14
        draw_text("[F1] / Gamepad LB       : Cycle Magic Find (0% / 100% / 300%)", ctl_x + 10, cy, 10, Color(200, 220, 245, 255)); cy += 14
        draw_text("[F2] / Gamepad Y        : Batch Simulation (+100 Drops)", ctl_x + 10, cy, 10, Color(200, 220, 245, 255)); cy += 14
        draw_text("[Tab] / Pad Select      : Toggle X-Ray Telemetry Overlay", ctl_x + 10, cy, 10, Color(255, 215, 0, 255))

        # Right-Hand Telemetry & Histogram Panel
        if self.show_xray:
            draw_xray_histogram(
                panel_x=814, panel_y=56, panel_w=446, panel_h=654,
                loot_table=self.loot_table, drop_counts=self.drop_counts,
                total_drops=self.total_drops, total_score=self.total_score
            )

    def draw(self):
        begin_drawing()
        clear_background(Color(10, 13, 22, 255))

        self.draw_pinata_arena()
        self.draw_hud()

        # Global Top-Bar Settings & Gamepad Badge
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
    LootPinataLab().run(smoke_test=is_smoke)
