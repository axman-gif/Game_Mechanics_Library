# -*- coding: utf-8 -*-
"""
Hotbar - Quick Slot Bar, Cooldown Sweeps & Dynamic Item Dispatch
================================================================
Section          : 3.1 Menus & UI
Pattern Category : Menus & User Interface, Combat & Quick Actions
Dimension        : 2D

Problem Solved:
  In action RPGs, MMOs, survival titles, and sandbox games (World of Warcraft,
  Minecraft, Diablo, Terraria, Valheim), players need instantaneous access to 8-10
  abilities, consumables, and weapons during frantic real-time combat. Naive hotbar
  implementations suffer from button-mashing race conditions, lack of Global Cooldown
  (GCD) pacing (allowing players to spam 5 items in the exact same frame), missing visual
  recharge wipes (leaving players guessing when an item is ready), and rigid key mappings
  that fail on gamepads or prevent inventory re-binding.

How the Pattern Works:
  1. Fixed-Capacity Hotbar Array (std::array<HotbarSlot, N> in C++):
     Pre-allocates $N = 8$ contiguous slots indexed 0 .. 7. Each slot tracks its
     bound item data, stack count, current cooldown timer, and elastic bounce animation.
  2. Two-Tier Cooldown Synchronization (GCD + Per-Item Timers):
     - Global Cooldown (GCD): A short shared lockout window (e.g. 0.75s) triggered on
       any ability use, preventing burst macro exploits and pacing combat rhythm.
     - Per-Slot Cooldown: An independent timer per item (e.g. Health Potion: 6.0s,
       EMP Blast: 5.0s, Shield: 8.0s) rendered with a translucent downward vertical wipe.
  3. Seamless Input Multiplexing (Bumper Cycling + Direct Number Keys):
     - Keyboard: Direct numeric keys [1] through [8].
     - Mouse: Scroll wheel cycles active slot; left-click activates or selects.
     - Gamepad: Bumpers [LB] / [RB] cycle slot selection; Gamepad A activates the slot.
  4. Decoupled Action Dispatch & Backpack Re-assignment:
     Slots produce an executable `ActionToken` consumed by the simulation. Pressing [B]
     opens a reserve supply bag allowing quick drag-and-drop or cursor slot re-binding.

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - 1 .. 8 / Mouse Wheel / Gamepad LB/RB : Select active Hotbar slot (0 .. 7)
  - Space / Enter / Left Click / Gamepad A: Use item in currently active slot
  - WASD / Left Stick / D-Pad            : Move Player combat avatar around arena
  - Mouse Cursor / Gamepad Right Stick   : Aim targeting reticle
  - B / Gamepad Y (Triangle)             : Open/Close Reserve Supply Bag (Backpack)
  - [Tab] / Gamepad View (Select)        : Toggle X-Ray Cooldown & Dispatch Telemetry
  - [F1]  / Gamepad R3                   : Toggle GCD: [Enforced Global Cooldown] vs [No GCD / Instant Spam]
  - [F2]  / Gamepad L3                   : Toggle Cooldown Visual: [Tactile Sweep Wipe] vs [Binary Dimming]
  - [Ctrl +/-]                           : Increase / Decrease UI Font Size
  - [F11]                                : Toggle Fullscreen
  - [R]   / Gamepad Start                : Reset simulation state, HP, and cooldowns
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
WINDOW_TITLE = "Hotbar - Quick Slot Bar & Cooldown Sweeps (Raylib Pattern Lab)"

# Color Palette (High-Energy Sci-Fi Combat UI)
COLOR_BG_DARK           = Color(10, 14, 24, 255)
COLOR_ARENA_BORDER      = Color(38, 55, 88, 255)
COLOR_GRID_LINES        = Color(18, 26, 42, 255)
COLOR_SLOT_BG           = Color(18, 25, 42, 240)
COLOR_SLOT_BORDER       = Color(45, 68, 105, 255)
COLOR_SLOT_ACTIVE_BDR   = Color(0, 225, 255, 255)
COLOR_COOLDOWN_OVERLAY  = Color(5, 8, 16, 200)
COLOR_TEXT_WHITE        = Color(235, 245, 255, 255)
COLOR_TEXT_DIM          = Color(120, 145, 180, 255)
COLOR_GOLD_ACCENT       = Color(255, 205, 55, 255)
COLOR_GREEN_ACCENT      = Color(65, 240, 130, 255)
COLOR_RED_ACCENT        = Color(255, 75, 75, 255)
COLOR_CYAN_ACCENT       = Color(0, 225, 255, 255)
COLOR_PURPLE_ACCENT     = Color(180, 100, 255, 255)

HOTBAR_SLOT_COUNT       = 8
GLOBAL_COOLDOWN_TIME    = 0.75  # Standard MMO/ARPG GCD

# Item Type IDs (C++ Enum equivalent)
ITEM_BLASTER            = 1
ITEM_HEAL_FLASK         = 2
ITEM_SHIELD_BARRIER     = 3
ITEM_EMP_SHOCKWAVE      = 4
ITEM_BLINK_THRUST       = 5
ITEM_SENTRY_TURRET      = 6
ITEM_SPEED_BOOST        = 7
ITEM_LIGHT_FLARE        = 8

# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATION (HOTBAR & COOLDOWN ENGINE)
# ==============================================================================

class ItemDefinition:
    """
    Static metadata defining an item archetype and its cooldown behavior.
    C++ Equivalent:
      struct ItemDefinition {
          int item_id;
          std::string name;
          std::string description;
          float max_cooldown;
          bool triggers_gcd;
          Color icon_color;
      };
    """
    def __init__(self, item_id: int, name: str, description: str, max_cooldown: float, triggers_gcd: bool, icon_color: Color):
        self.item_id = item_id
        self.name = name
        self.description = description
        self.max_cooldown = max_cooldown
        self.triggers_gcd = triggers_gcd
        self.icon_color = icon_color


class HotbarSlot:
    """
    A single interactive quick slot in the hotbar array.
    C++ Equivalent:
      struct HotbarSlot {
          int slot_index;
          int item_id;
          int quantity;
          float current_cooldown;
          float max_cooldown;
          float bounce_scale;
          int total_activations;
      };
    """
    def __init__(self, slot_index: int, item_id: int, quantity: int = 1, max_cooldown: float = 3.0):
        self.slot_index = slot_index
        self.item_id = item_id
        self.quantity = quantity
        self.current_cooldown = 0.0
        self.max_cooldown = max_cooldown
        self.bounce_scale = 1.0
        self.total_activations = 0

    def trigger(self, duration: float):
        self.current_cooldown = duration
        self.max_cooldown = duration
        self.bounce_scale = 1.28
        self.total_activations += 1

    def is_ready(self, gcd_active: bool) -> bool:
        if self.item_id == 0:
            return False
        if self.current_cooldown > 0.0:
            return False
        if gcd_active:
            return False
        return True


class HotbarSystem:
    """
    Manages the 8-slot array, active slot pointer, and GCD timer.
    C++ Equivalent:
      class HotbarSystem {
      public:
          std::array<HotbarSlot, 8> slots;
          int active_slot_index;
          float visual_indicator_x;
          float gcd_timer;
          float gcd_max;
          bool gcd_enforced;
          bool sweep_wipe_enabled;
          // ... methods
      };
    """
    def __init__(self):
        self.slots = []
        for i in range(HOTBAR_SLOT_COUNT):
            self.slots.append(HotbarSlot(i, 0, 0, 1.0))

        self.active_slot_index = 0
        self.visual_indicator_x = 0.0
        self.gcd_timer = 0.0
        self.gcd_max = GLOBAL_COOLDOWN_TIME
        self.gcd_enforced = True          # [F1] Toggle
        self.sweep_wipe_enabled = True     # [F2] Toggle
        self.slot_width = 64.0
        self.slot_spacing = 10.0
        self.total_actions_fired = 0

    def select_slot(self, index: int):
        self.active_slot_index = max(0, min(HOTBAR_SLOT_COUNT - 1, index))

    def cycle_slot(self, delta: int):
        self.active_slot_index = (self.active_slot_index + delta + HOTBAR_SLOT_COUNT) % HOTBAR_SLOT_COUNT

    def update(self, dt: float):
        # Update Global Cooldown
        if self.gcd_timer > 0.0:
            self.gcd_timer -= dt
            if self.gcd_timer < 0.0:
                self.gcd_timer = 0.0

        # Update Slot Cooldowns & Elastic Bounces
        for slot in self.slots:
            if slot.current_cooldown > 0.0:
                slot.current_cooldown -= dt
                if slot.current_cooldown < 0.0:
                    slot.current_cooldown = 0.0

            # Damp bounce scale back to 1.0
            slot.bounce_scale = damp(slot.bounce_scale, 1.0, 14.0, dt)

        # Smoothly glide active selection indicator
        target_indicator_x = float(self.active_slot_index * (self.slot_width + self.slot_spacing))
        self.visual_indicator_x = damp(self.visual_indicator_x, target_indicator_x, 18.0, dt)

    def can_trigger_slot(self, index: int) -> bool:
        if index < 0 or index >= len(self.slots):
            return False
        slot = self.slots[index]
        gcd_blocking = (self.gcd_enforced and self.gcd_timer > 0.0)
        return slot.is_ready(gcd_blocking)

    def fire_slot(self, index: int, defs_table: dict) -> int:
        """
        Attempts to activate the item in slot `index`.
        Returns item_id if triggered successfully, or 0 if rejected.
        """
        if not self.can_trigger_slot(index):
            return 0

        slot = self.slots[index]
        item_id = slot.item_id
        if item_id in defs_table:
            idef = defs_table[item_id]
            slot.trigger(idef.max_cooldown)
            if self.gcd_enforced and idef.triggers_gcd:
                self.gcd_timer = self.gcd_max
            self.total_actions_fired += 1
            return item_id
        return 0


# ==============================================================================
# BLOCK 2: WORLD SIMULATION & ENTITIES (COMBAT SANDBOX)
# ==============================================================================

class PlasmaProjectile:
    """Projectile fired by slot 1 (Blaster)."""
    def __init__(self, x: float, y: float, vx: float, vy: float):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = 1.2
        self.radius = 5.0


class ArenaDummy:
    """Target practice dummy in the combat arena."""
    def __init__(self, x: float, y: float, name: str):
        self.x = x
        self.y = y
        self.name = name
        self.radius = 24.0
        self.hp = 100
        self.max_hp = 100
        self.hit_flash = 0.0

    def take_damage(self, amount: int):
        self.hp = max(0, self.hp - amount)
        self.hit_flash = 0.25
        if self.hp <= 0:
            self.hp = self.max_hp  # Respawn dummy


class CombatArenaSimulation:
    """
    Interactive combat playground to test items activated from the hotbar.
    """
    def __init__(self):
        self.player_x = 380.0
        self.player_y = 330.0
        self.player_hp = 85
        self.player_max_hp = 100
        self.player_speed_base = 230.0
        self.speed_boost_timer = 0.0
        self.shield_timer = 0.0
        self.shield_radius = 42.0
        self.emp_ring_timer = 0.0
        self.emp_ring_radius = 0.0
        self.turret_active = False
        self.turret_x = 0.0
        self.turret_y = 0.0
        self.turret_life = 0.0

        # Projectiles
        self.projectiles = []

        # Target Dummies
        self.dummies = [
            ArenaDummy(640.0, 220.0, "Dummy Alpha"),
            ArenaDummy(720.0, 360.0, "Dummy Beta"),
            ArenaDummy(640.0, 500.0, "Dummy Gamma"),
        ]

        # Flares
        self.flares = []

        # Reticle
        self.aim_world_x = 640.0
        self.aim_world_y = 360.0

    def update(self, dt: float, move_vec: Vector2):
        # Speed boost decay
        cur_speed = self.player_speed_base
        if self.speed_boost_timer > 0.0:
            self.speed_boost_timer -= dt
            cur_speed *= 1.75

        # Move player
        self.player_x += move_vec.x * cur_speed * dt
        self.player_y += move_vec.y * cur_speed * dt
        self.player_x = max(70.0, min(800.0, self.player_x))
        self.player_y = max(90.0, min(560.0, self.player_y))

        # Shield decay
        if self.shield_timer > 0.0:
            self.shield_timer -= dt

        # EMP Shockwave expansion
        if self.emp_ring_timer > 0.0:
            self.emp_ring_timer -= dt
            self.emp_ring_radius += 400.0 * dt
            # Damage dummies inside expanding shock ring
            for d in self.dummies:
                dist = math.sqrt((d.x - self.player_x)**2 + (d.y - self.player_y)**2)
                if abs(dist - self.emp_ring_radius) < 25.0:
                    d.take_damage(2)

        # Turret tick
        if self.turret_active:
            self.turret_life -= dt
            if self.turret_life <= 0.0:
                self.turret_active = False

        # Projectiles update
        active_projs = []
        for p in self.projectiles:
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.life -= dt
            hit_something = False
            for d in self.dummies:
                dist = math.sqrt((p.x - d.x)**2 + (p.y - d.y)**2)
                if dist <= d.radius + p.radius:
                    d.take_damage(25)
                    hit_something = True
                    break
            if p.life > 0.0 and not hit_something:
                active_projs.append(p)
        self.projectiles = active_projs

        # Update dummies
        for d in self.dummies:
            if d.hit_flash > 0.0:
                d.hit_flash -= dt

    def fire_blaster(self):
        dx = self.aim_world_x - self.player_x
        dy = self.aim_world_y - self.player_y
        mag = math.sqrt(dx * dx + dy * dy)
        if mag > 0.001:
            vx = (dx / mag) * 650.0
            vy = (dy / mag) * 650.0
            self.projectiles.append(PlasmaProjectile(self.player_x, self.player_y, vx, vy))

    def activate_heal(self):
        self.player_hp = min(self.player_max_hp, self.player_hp + 35)

    def activate_shield(self):
        self.shield_timer = 5.0

    def activate_emp(self):
        self.emp_ring_timer = 0.65
        self.emp_ring_radius = 10.0

    def activate_blink(self):
        dx = self.aim_world_x - self.player_x
        dy = self.aim_world_y - self.player_y
        mag = math.sqrt(dx * dx + dy * dy)
        if mag > 0.001:
            blink_dist = min(150.0, mag)
            self.player_x += (dx / mag) * blink_dist
            self.player_y += (dy / mag) * blink_dist
            self.player_x = max(70.0, min(800.0, self.player_x))
            self.player_y = max(90.0, min(560.0, self.player_y))

    def activate_turret(self):
        self.turret_active = True
        self.turret_x = self.player_x + 35.0
        self.turret_y = self.player_y
        self.turret_life = 8.0

    def activate_speed(self):
        self.speed_boost_timer = 4.5

    def draw(self):
        # Arena floor & grid lines
        for gx in range(60, 840, 60):
            draw_line(gx, 80, gx, 580, COLOR_GRID_LINES)
        for gy in range(80, 600, 60):
            draw_line(60, gy, 840, gy, COLOR_GRID_LINES)
        draw_rectangle_lines(60, 80, 780, 500, COLOR_ARENA_BORDER)
        draw_text("SECTOR-4 TARGET COMBAT PROVING GROUNDS", 75, 92, 13, COLOR_TEXT_DIM)

        # Dummies
        for d in self.dummies:
            d_col = Color(255, 120, 120, 255) if d.hit_flash > 0.0 else Color(180, 70, 70, 255)
            draw_circle(int(d.x), int(d.y), d.radius, d_col)
            draw_circle_lines(int(d.x), int(d.y), d.radius, COLOR_TEXT_WHITE)
            draw_text(d.name, int(d.x - 38), int(d.y + 28), 10, COLOR_TEXT_DIM)

            # Dummy HP bar
            bar_w = 46
            bar_h = 6
            hp_w = int(bar_w * (d.hp / float(d.max_hp)))
            draw_rectangle(int(d.x - 23), int(d.y - 36), bar_w, bar_h, Color(30, 40, 55, 255))
            draw_rectangle(int(d.x - 23), int(d.y - 36), hp_w, bar_h, COLOR_GREEN_ACCENT)
            draw_rectangle_lines(int(d.x - 23), int(d.y - 36), bar_w, bar_h, COLOR_SLOT_BORDER)

        # EMP Shockwave Ring
        if self.emp_ring_timer > 0.0:
            draw_circle_lines(int(self.player_x), int(self.player_y), self.emp_ring_radius, COLOR_CYAN_ACCENT)

        # Deployed Sentry Turret
        if self.turret_active:
            draw_circle(int(self.turret_x), int(self.turret_y), 16.0, Color(45, 75, 120, 255))
            draw_circle_lines(int(self.turret_x), int(self.turret_y), 16.0, COLOR_CYAN_ACCENT)
            draw_text("TURRET", int(self.turret_x - 18), int(self.turret_y + 20), 10, COLOR_CYAN_ACCENT)

        # Projectiles
        for p in self.projectiles:
            draw_circle(int(p.x), int(p.y), p.radius, COLOR_CYAN_ACCENT)
            draw_circle(int(p.x), int(p.y), p.radius * 0.5, COLOR_TEXT_WHITE)

        # Player Avatar
        p_col = COLOR_GREEN_ACCENT if self.speed_boost_timer > 0.0 else COLOR_CYAN_ACCENT
        draw_circle(int(self.player_x), int(self.player_y), 18.0, p_col)
        draw_circle_lines(int(self.player_x), int(self.player_y), 18.0, COLOR_TEXT_WHITE)

        # Shield Ring
        if self.shield_timer > 0.0:
            draw_circle_lines(int(self.player_x), int(self.player_y), self.shield_radius, COLOR_CYAN_ACCENT)
            draw_circle_lines(int(self.player_x), int(self.player_y), self.shield_radius + 2.0, Color(0, 225, 255, 100))

        # Player HP Mini Bar
        hp_bar_w = 50
        cur_hp_w = int(hp_bar_w * (self.player_hp / float(self.player_max_hp)))
        draw_rectangle(int(self.player_x - 25), int(self.player_y - 30), hp_bar_w, 6, Color(25, 35, 50, 255))
        draw_rectangle(int(self.player_x - 25), int(self.player_y - 30), cur_hp_w, 6, COLOR_GREEN_ACCENT)
        draw_rectangle_lines(int(self.player_x - 25), int(self.player_y - 30), hp_bar_w, 6, COLOR_SLOT_BORDER)

        # Crosshair Reticle
        rx = int(self.aim_world_x)
        ry = int(self.aim_world_y)
        draw_circle_lines(rx, ry, 8.0, COLOR_GOLD_ACCENT)
        draw_line(rx - 12, ry, rx + 12, ry, COLOR_GOLD_ACCENT)
        draw_line(rx, ry - 12, rx, ry + 12, COLOR_GOLD_ACCENT)


# ==============================================================================
# BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY ([Tab] & [F1])
# ==============================================================================

def draw_xray_hotbar_inspector(hotbar: HotbarSystem, defs_table: dict, sim: CombatArenaSimulation, x: int, y: int, w: int, h: int):
    """
    Renders live telemetry of slot memory states, cooldown progress, and GCD locks.
    """
    draw_rectangle(x, y, w, h, Color(14, 20, 32, 245))
    draw_rectangle_lines(x, y, w, h, COLOR_CYAN_ACCENT)

    # Title Banner
    draw_rectangle(x, y, w, 28, Color(22, 36, 60, 255))
    draw_text("HOTBAR & COOLDOWN X-RAY TELEMETRY", x + 10, y + 7, 13, COLOR_CYAN_ACCENT)

    cy = y + 36

    # 1. Active Slot Pointer
    active_str = "ACTIVE SLOT: #" + str(hotbar.active_slot_index + 1) + " (Array Index: " + str(hotbar.active_slot_index) + ")"
    draw_text(active_str, x + 12, cy, 13, COLOR_TEXT_WHITE)
    cy += 18

    # 2. GCD Telemetry Bar
    gcd_col = COLOR_RED_ACCENT if hotbar.gcd_timer > 0.0 else COLOR_GREEN_ACCENT
    draw_text("GLOBAL COOLDOWN (GCD):", x + 12, cy, 11, COLOR_TEXT_DIM)
    cy += 15
    draw_rectangle(x + 14, cy, 220, 10, Color(25, 35, 55, 255))
    if hotbar.gcd_max > 0.0:
        gcd_fill = int(220 * (hotbar.gcd_timer / hotbar.gcd_max))
        draw_rectangle(x + 14, cy, gcd_fill, 10, gcd_col)
    draw_rectangle_lines(x + 14, cy, 220, 10, COLOR_SLOT_BORDER)

    gcd_status = "LOCKED (" + str(round(hotbar.gcd_timer, 2)) + "s)" if hotbar.gcd_timer > 0.0 else "READY"
    draw_text(gcd_status, x + 245, cy - 1, 11, gcd_col)
    cy += 18

    # 3. Architecture Toggles
    gcd_mode = "ENFORCED [0.75s GCD]" if hotbar.gcd_enforced else "DISABLED [SPAM BURST]"
    draw_text("GCD Rule: " + gcd_mode, x + 12, cy, 11, COLOR_GOLD_ACCENT if hotbar.gcd_enforced else COLOR_RED_ACCENT)
    cy += 15

    wipe_mode = "TACTILE VERTICAL WIPE" if hotbar.sweep_wipe_enabled else "BINARY DIMMING"
    draw_text("Wipe Style: " + wipe_mode, x + 12, cy, 11, COLOR_TEXT_DIM)
    cy += 20

    draw_line(x + 10, cy, x + w - 10, cy, Color(35, 50, 75, 255))
    cy += 12

    # 4. Slot Array Table
    draw_text("SLOT CONTIGUOUS MEMORY ARRAY (8 SLOTS):", x + 12, cy, 11, COLOR_CYAN_ACCENT)
    cy += 16

    for i in range(len(hotbar.slots)):
        slot = hotbar.slots[i]
        is_sel = (i == hotbar.active_slot_index)
        row_bg = Color(28, 44, 70, 255) if is_sel else Color(18, 25, 38, 255)
        draw_rectangle(x + 12, cy, w - 24, 22, row_bg)

        # Slot tag
        tag = "[" + str(i + 1) + "]"
        draw_text(tag, x + 16, cy + 4, 11, COLOR_GOLD_ACCENT if is_sel else COLOR_TEXT_DIM)

        # Name
        item_name = defs_table[slot.item_id].name if slot.item_id in defs_table else "Empty"
        draw_text(item_name[:16], x + 44, cy + 4, 11, COLOR_TEXT_WHITE if slot.current_cooldown <= 0.0 else COLOR_TEXT_DIM)

        # Cooldown timer
        if slot.current_cooldown > 0.0:
            cd_str = str(round(slot.current_cooldown, 1)) + "s / " + str(int(slot.max_cooldown)) + "s"
            draw_text(cd_str, x + 210, cy + 4, 11, COLOR_RED_ACCENT)
        else:
            draw_text("READY", x + 210, cy + 4, 11, COLOR_GREEN_ACCENT)

        # Total fired
        act_str = "#" + str(slot.total_activations)
        draw_text(act_str, x + w - 60, cy + 4, 11, COLOR_TEXT_DIM)

        cy += 24

    cy += 10
    draw_line(x + 10, cy, x + w - 10, cy, Color(35, 50, 75, 255))
    cy += 12

    # 5. Combat State Cache
    draw_text("ACTIVE PLAYER COMBAT ATTRIBUTES:", x + 12, cy, 11, COLOR_CYAN_ACCENT)
    cy += 16
    draw_text("Player HP: " + str(sim.player_hp) + " / " + str(sim.player_max_hp), x + 18, cy, 11, COLOR_TEXT_WHITE)
    cy += 15
    s_tag = "ACTIVE (" + str(round(sim.shield_timer, 1)) + "s)" if sim.shield_timer > 0.0 else "OFFLINE"
    draw_text("Energy Shield: " + s_tag, x + 18, cy, 11, COLOR_CYAN_ACCENT if sim.shield_timer > 0.0 else COLOR_TEXT_DIM)
    cy += 15
    b_tag = "BOOSTED (" + str(round(sim.speed_boost_timer, 1)) + "s)" if sim.speed_boost_timer > 0.0 else "NORMAL"
    draw_text("Kinetic Thruster: " + b_tag, x + 18, cy, 11, COLOR_GREEN_ACCENT if sim.speed_boost_timer > 0.0 else COLOR_TEXT_DIM)
    cy += 15
    t_tag = "DEPLOYED (" + str(round(sim.turret_life, 1)) + "s)" if sim.turret_active else "IDLE"
    draw_text("Sentry Turret: " + t_tag, x + 18, cy, 11, COLOR_GOLD_ACCENT if sim.turret_active else COLOR_TEXT_DIM)


# ==============================================================================
# BLOCK 4: MAIN GAME LOOP & AUTOMATED SMOKE TEST
# ==============================================================================

class HotbarGame:
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()
        self.sfx = SoundLibrary()
        self.sfx.init_defaults()

        # Telemetry & Pattern Toggles
        self.show_xray = True

        # Pre-populate Item Definitions Table
        self.item_defs = {
            ITEM_BLASTER:        ItemDefinition(ITEM_BLASTER, "Plasma Blaster", "Fires rapid kinetic laser bolt toward crosshair", 0.35, True, COLOR_CYAN_ACCENT),
            ITEM_HEAL_FLASK:     ItemDefinition(ITEM_HEAL_FLASK, "Nanite Stimpak", "Instantly restores +35 health points", 5.0, True, COLOR_GREEN_ACCENT),
            ITEM_SHIELD_BARRIER: ItemDefinition(ITEM_SHIELD_BARRIER, "Reflector Barrier", "Deploys energy shield deflecting incoming impacts", 8.0, True, COLOR_CYAN_ACCENT),
            ITEM_EMP_SHOCKWAVE:  ItemDefinition(ITEM_EMP_SHOCKWAVE, "EMP Pulse Bomb", "Emits circular shockwave damaging nearby targets", 4.0, True, COLOR_PURPLE_ACCENT),
            ITEM_BLINK_THRUST:   ItemDefinition(ITEM_BLINK_THRUST, "Warp Phase Blink", "Teleports avatar instantaneously toward reticle", 3.5, False, COLOR_GOLD_ACCENT),
            ITEM_SENTRY_TURRET:  ItemDefinition(ITEM_SENTRY_TURRET, "Deployable Turret", "Deploys automated companion turret", 10.0, True, COLOR_GOLD_ACCENT),
            ITEM_SPEED_BOOST:    ItemDefinition(ITEM_SPEED_BOOST, "Overdrive Thruster", "Increases movement velocity by 75% for 4.5s", 7.0, True, COLOR_GREEN_ACCENT),
            ITEM_LIGHT_FLARE:    ItemDefinition(ITEM_LIGHT_FLARE, "Signal Illuminator", "Launches high-intensity area lighting flare", 2.0, False, COLOR_TEXT_WHITE),
        }

        # Initialize Simulation & Hotbar
        self.simulation = CombatArenaSimulation()
        self.hotbar = HotbarSystem()

        # Bind starting loadout into hotbar slots 0..7
        for i in range(HOTBAR_SLOT_COUNT):
            item_id = i + 1
            max_cd = self.item_defs[item_id].max_cooldown
            self.hotbar.slots[i] = HotbarSlot(i, item_id, 1, max_cd)

        # Backpack bag (Reserve Inventory)
        self.backpack_open = False
        self.dragged_item_id = 0

        # Toast
        self.toast_msg = "Press [1..8], scroll wheel, or Gamepad LB/RB to select. Space / Gamepad A to use."
        self.toast_timer = 4.5

    def _trigger_active_slot(self):
        fired_id = self.hotbar.fire_slot(self.hotbar.active_slot_index, self.item_defs)
        if fired_id > 0:
            self._dispatch_item_effect(fired_id)
        else:
            self.sfx.play("hit", 0.4)  # Cooldown reject blip

    def _dispatch_item_effect(self, item_id: int):
        if item_id == ITEM_BLASTER:
            self.simulation.fire_blaster()
            self.sfx.play("laser", 0.7)
            self.toast_msg = "Dispatched: Plasma Blaster Fired!"
            self.toast_timer = 1.5

        elif item_id == ITEM_HEAL_FLASK:
            self.simulation.activate_heal()
            self.sfx.play("pickup", 0.8)
            self.toast_msg = "Dispatched: Nanite Stimpak Consumed (+35 HP)."
            self.toast_timer = 2.0

        elif item_id == ITEM_SHIELD_BARRIER:
            self.simulation.activate_shield()
            self.sfx.play("click", 0.9)
            self.toast_msg = "Dispatched: Barrier Field Online (5.0s)."
            self.toast_timer = 2.0

        elif item_id == ITEM_EMP_SHOCKWAVE:
            self.simulation.activate_emp()
            self.sfx.play("explosion", 0.7)
            self.toast_msg = "Dispatched: EMP Shockwave Detonated!"
            self.toast_timer = 2.0

        elif item_id == ITEM_BLINK_THRUST:
            self.simulation.activate_blink()
            self.sfx.play("laser", 0.6)
            self.toast_msg = "Dispatched: Warp Blink Teleport Executed."
            self.toast_timer = 1.5

        elif item_id == ITEM_SENTRY_TURRET:
            self.simulation.activate_turret()
            self.sfx.play("click", 0.8)
            self.toast_msg = "Dispatched: Sentry Turret Deployed (8.0s)."
            self.toast_timer = 2.5

        elif item_id == ITEM_SPEED_BOOST:
            self.simulation.activate_speed()
            self.sfx.play("laser", 0.5)
            self.toast_msg = "Dispatched: Overdrive Thrusters Engaged!"
            self.toast_timer = 2.0

        elif item_id == ITEM_LIGHT_FLARE:
            self.sfx.play("click", 0.5)
            self.toast_msg = "Dispatched: Signal Illuminator Launched."
            self.toast_timer = 1.5

    def update(self):
        dt = min(get_frame_time(), 0.05)

        # X-Ray Toggle ([Tab] / Gamepad View)
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
            self.sfx.play("click", 0.5)

        # Pattern Toggle ([F1] / Gamepad R3): Enforced GCD vs No GCD Spam
        if is_dual_pattern_toggle_pressed():
            self.hotbar.gcd_enforced = not self.hotbar.gcd_enforced
            self.sfx.play("click", 0.6)
            g_name = "Enforced 0.75s GCD" if self.hotbar.gcd_enforced else "No GCD / Instant Spam"
            self.toast_msg = "GCD Rule Toggled: " + g_name
            self.toast_timer = 3.0

        # Secondary Toggle ([F2] / Gamepad L3): Tactile Sweep Wipe vs Binary Dim
        if is_dual_secondary_toggle_pressed():
            self.hotbar.sweep_wipe_enabled = not self.hotbar.sweep_wipe_enabled
            self.sfx.play("click", 0.5)
            w_name = "Tactile Sweep Wipe" if self.hotbar.sweep_wipe_enabled else "Binary Dimming"
            self.toast_msg = "Cooldown Overlay Style: " + w_name
            self.toast_timer = 3.0

        # Toggle Backpack ([B] / Gamepad Y)
        pad_id = get_active_gamepad_id()
        pad_y_pressed = (pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_FACE_UP))
        if is_key_pressed(KEY_B) or pad_y_pressed:
            self.backpack_open = not self.backpack_open
            self.sfx.play("click", 0.5)

        # Reset Simulation ([R] / Gamepad Start)
        if is_dual_reset_pressed():
            self.simulation = CombatArenaSimulation()
            self.hotbar = HotbarSystem()
            for i in range(HOTBAR_SLOT_COUNT):
                item_id = i + 1
                max_cd = self.item_defs[item_id].max_cooldown
                self.hotbar.slots[i] = HotbarSlot(i, item_id, 1, max_cd)
            self.sfx.play("pickup", 0.8)
            self.toast_msg = "Hotbar & Arena Simulation Reset."
            self.toast_timer = 2.5

        # Update toast timer
        if self.toast_timer > 0.0:
            self.toast_timer -= dt

        # Simultaneous Reticle Aiming (Mouse or Gamepad Right Stick)
        mx = get_mouse_x()
        my = get_mouse_y()
        if mx >= 0 and mx <= SCREEN_WIDTH and my >= 0 and my <= SCREEN_HEIGHT:
            self.simulation.aim_world_x = float(mx)
            self.simulation.aim_world_y = float(my)

        pad_look = get_gamepad_right_stick(deadzone=0.18)
        if abs(pad_look.x) > 0.01 or abs(pad_look.y) > 0.01:
            self.simulation.aim_world_x += pad_look.x * 500.0 * dt
            self.simulation.aim_world_y += pad_look.y * 500.0 * dt
            self.simulation.aim_world_x = max(20.0, min(SCREEN_WIDTH - 20.0, self.simulation.aim_world_x))
            self.simulation.aim_world_y = max(20.0, min(SCREEN_HEIGHT - 20.0, self.simulation.aim_world_y))

        # Direct Number Key Input [1..8]
        if is_key_pressed(KEY_ONE):
            self.hotbar.select_slot(0)
            self.sfx.play("click", 0.3)
        elif is_key_pressed(KEY_TWO):
            self.hotbar.select_slot(1)
            self.sfx.play("click", 0.3)
        elif is_key_pressed(KEY_THREE):
            self.hotbar.select_slot(2)
            self.sfx.play("click", 0.3)
        elif is_key_pressed(KEY_FOUR):
            self.hotbar.select_slot(3)
            self.sfx.play("click", 0.3)
        elif is_key_pressed(KEY_FIVE):
            self.hotbar.select_slot(4)
            self.sfx.play("click", 0.3)
        elif is_key_pressed(KEY_SIX):
            self.hotbar.select_slot(5)
            self.sfx.play("click", 0.3)
        elif is_key_pressed(KEY_SEVEN):
            self.hotbar.select_slot(6)
            self.sfx.play("click", 0.3)
        elif is_key_pressed(KEY_EIGHT):
            self.hotbar.select_slot(7)
            self.sfx.play("click", 0.3)

        # Mouse Wheel Slot Cycling
        wheel = get_mouse_wheel_move()
        if wheel > 0.5:
            self.hotbar.cycle_slot(-1)
            self.sfx.play("click", 0.3)
        elif wheel < -0.5:
            self.hotbar.cycle_slot(1)
            self.sfx.play("click", 0.3)

        # Gamepad Bumper Slot Cycling (LB / RB)
        if pad_id >= 0:
            if is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_LEFT_TRIGGER_1):
                self.hotbar.cycle_slot(-1)
                self.sfx.play("click", 0.3)
            elif is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_TRIGGER_1):
                self.hotbar.cycle_slot(1)
                self.sfx.play("click", 0.3)

        # Trigger Active Slot Action (Space / Enter / Left Click / Gamepad A)
        pad_a_pressed = (pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_FACE_DOWN))
        trigger_pressed = (is_key_pressed(KEY_SPACE) or is_key_pressed(KEY_ENTER) or pad_a_pressed)

        # Also support clicking directly on a hotbar slot
        if is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            clicked_slot = self._get_hovered_hotbar_slot()
            if clicked_slot >= 0:
                self.hotbar.select_slot(clicked_slot)
                self._trigger_active_slot()
            elif not self.backpack_open and my < 580:
                # Left clicking in arena triggers active slot toward aim crosshair
                self._trigger_active_slot()
        elif trigger_pressed:
            self._trigger_active_slot()

        # Update hotbar animations and cooldowns
        self.hotbar.update(dt)

        # Update combat simulation
        move_vec = get_dual_move_2d()
        self.simulation.update(dt, move_vec)

    def _get_hovered_hotbar_slot(self) -> int:
        mx = get_mouse_x()
        my = get_mouse_y()
        bar_w = HOTBAR_SLOT_COUNT * self.hotbar.slot_width + (HOTBAR_SLOT_COUNT - 1) * self.hotbar.slot_spacing
        start_x = 440.0 - bar_w * 0.5
        start_y = 615.0

        for i in range(HOTBAR_SLOT_COUNT):
            sx = start_x + i * (self.hotbar.slot_width + self.hotbar.slot_spacing)
            if mx >= sx and mx <= sx + self.hotbar.slot_width and my >= start_y and my <= start_y + self.hotbar.slot_width:
                return i
        return -1

    def draw(self):
        begin_drawing()
        clear_background(COLOR_BG_DARK)

        # 1. World Simulation
        self.simulation.draw()

        # 2. Draw Hotbar Dock at bottom center
        self._draw_hotbar_dock()

        # 3. Draw Backpack Reserve Inventory (if toggled open)
        if self.backpack_open:
            self._draw_backpack_tray()

        # 4. Telemetry Overlay ([Tab])
        if self.show_xray:
            draw_xray_hotbar_inspector(self.hotbar, self.item_defs, self.simulation, 860, 68, 400, 630)

        # 5. Toast Notification
        if self.toast_timer > 0.0:
            self._draw_toast()

        # 6. Top-bar HUD (Font size, window dropdown, gamepad badge)
        self._draw_top_hud()

        # Mandatory repo dropdowns and badges
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)

        end_drawing()

    def _draw_hotbar_dock(self):
        bar_w = HOTBAR_SLOT_COUNT * self.hotbar.slot_width + (HOTBAR_SLOT_COUNT - 1) * self.hotbar.slot_spacing
        start_x = 440.0 - bar_w * 0.5
        start_y = 615.0

        # Background Dock Panel
        dock_padding = 10.0
        draw_rectangle(int(start_x - dock_padding), int(start_y - dock_padding), int(bar_w + dock_padding * 2.0), int(self.hotbar.slot_width + dock_padding * 2.0), Color(14, 20, 32, 230))
        draw_rectangle_lines(int(start_x - dock_padding), int(start_y - dock_padding), int(bar_w + dock_padding * 2.0), int(self.hotbar.slot_width + dock_padding * 2.0), COLOR_SLOT_BORDER)

        # Draw Animated Selection Glide Box
        ind_x = int(start_x + self.hotbar.visual_indicator_x)
        draw_rectangle_lines(ind_x - 3, int(start_y - 3), int(self.hotbar.slot_width + 6), int(self.hotbar.slot_width + 6), COLOR_SLOT_ACTIVE_BDR)
        draw_rectangle_lines(ind_x - 4, int(start_y - 4), int(self.hotbar.slot_width + 8), int(self.hotbar.slot_width + 8), Color(0, 225, 255, 120))

        # Draw 8 Slots
        for i in range(HOTBAR_SLOT_COUNT):
            slot = self.hotbar.slots[i]
            sx = int(start_x + i * (self.hotbar.slot_width + self.hotbar.slot_spacing))
            sy = int(start_y)
            sw = int(self.hotbar.slot_width)

            # Slot base box
            draw_rectangle(sx, sy, sw, sw, COLOR_SLOT_BG)
            draw_rectangle_lines(sx, sy, sw, sw, COLOR_SLOT_BORDER)

            # Item Icon and Graphic
            if slot.item_id in self.item_defs:
                idef = self.item_defs[slot.item_id]
                icon_cx = sx + sw // 2
                icon_cy = sy + sw // 2
                icon_r = int(16.0 * slot.bounce_scale)

                # Procedural icon glyphs
                draw_circle(icon_cx, icon_cy, icon_r, idef.icon_color)
                draw_circle_lines(icon_cx, icon_cy, icon_r, COLOR_TEXT_WHITE)

                # Cooldown Wipe Overlay
                if slot.current_cooldown > 0.0:
                    if self.hotbar.sweep_wipe_enabled:
                        # Downward vertical wipe progress
                        ratio = slot.current_cooldown / slot.max_cooldown
                        wipe_h = int(sw * ratio)
                        draw_rectangle(sx, sy, sw, wipe_h, COLOR_COOLDOWN_OVERLAY)
                        draw_line(sx, sy + wipe_h, sx + sw, sy + wipe_h, COLOR_CYAN_ACCENT)
                        # Text timer
                        cd_str = str(round(slot.current_cooldown, 1))
                        tw = measure_text(cd_str, 13)
                        draw_text(cd_str, icon_cx - tw // 2, icon_cy - 6, 13, COLOR_TEXT_WHITE)
                    else:
                        # Binary dimming
                        draw_rectangle(sx, sy, sw, sw, Color(10, 15, 25, 180))

            # Slot Numeric Hotkey Badge (Top-Left)
            key_tag = str(i + 1)
            draw_text(key_tag, sx + 5, sy + 4, 11, COLOR_GOLD_ACCENT)

        # Global Cooldown Indicator Pip
        if self.hotbar.gcd_enforced and self.hotbar.gcd_timer > 0.0:
            gcd_pct = self.hotbar.gcd_timer / self.hotbar.gcd_max
            draw_rectangle(int(start_x - dock_padding), int(start_y + self.hotbar.slot_width + dock_padding), int((bar_w + dock_padding * 2.0) * gcd_pct), 3, COLOR_RED_ACCENT)

    def _draw_backpack_tray(self):
        bx = 200
        by = 480
        bw = 480
        bh = 110

        draw_rectangle(bx, by, bw, bh, Color(16, 24, 40, 245))
        draw_rectangle_lines(bx, by, bw, bh, COLOR_GOLD_ACCENT)
        draw_text("RESERVE SUPPLY BACKPACK (CLICK TO RE-ASSIGN ACTIVE SLOT)", bx + 16, by + 10, 11, COLOR_GOLD_ACCENT)

        start_x = bx + 20
        start_y = by + 34
        slot_size = 50

        # Render available archetypes in backpack
        for i in range(1, 9):
            if i in self.item_defs:
                idef = self.item_defs[i]
                sx = start_x + (i - 1) * (slot_size + 8)
                sy = start_y

                draw_rectangle(sx, sy, slot_size, slot_size, Color(24, 34, 54, 255))
                draw_rectangle_lines(sx, sy, slot_size, slot_size, COLOR_SLOT_BORDER)
                draw_circle(sx + slot_size // 2, sy + slot_size // 2, 12, idef.icon_color)

                # Click to bind into active hotbar slot
                mx = get_mouse_x()
                my = get_mouse_y()
                if mx >= sx and mx <= sx + slot_size and my >= sy and my <= sy + slot_size:
                    draw_rectangle_lines(sx, sy, slot_size, slot_size, COLOR_CYAN_ACCENT)
                    if is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
                        # Re-bind to active hotbar slot
                        act_idx = self.hotbar.active_slot_index
                        self.hotbar.slots[act_idx].item_id = i
                        self.hotbar.slots[act_idx].max_cooldown = idef.max_cooldown
                        self.hotbar.slots[act_idx].current_cooldown = 0.0
                        self.sfx.play("pickup", 0.7)
                        self.toast_msg = "Slot #" + str(act_idx + 1) + " Re-bound to " + idef.name
                        self.toast_timer = 2.5

    def _draw_toast(self):
        tw = measure_text(self.toast_msg, 12) + 32
        tx = 440 - (tw // 2)
        ty = 575
        draw_rectangle(tx, ty, tw, 26, Color(18, 26, 42, 240))
        draw_rectangle_lines(tx, ty, tw, 26, COLOR_CYAN_ACCENT)
        draw_text(self.toast_msg, tx + 16, ty + 6, 12, COLOR_TEXT_WHITE)

    def _draw_top_hud(self):
        draw_text("HOTBAR & QUICK SLOT BAR LAB", 24, 18, 16, COLOR_TEXT_WHITE)
        draw_text("Section 3.1: Menus & UI  |  Global Cooldown, Tactile Wipes & Dispatch", 24, 38, 11, COLOR_TEXT_DIM)

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
    HotbarGame().run(smoke_test=is_smoke)
