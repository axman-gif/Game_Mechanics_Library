# -*- coding: utf-8 -*-
"""
Tabbed Status Menu - Tabbed Menu Architecture & Dynamic Sub-View Layouts
========================================================================
Section          : 3.1 Menus & UI
Pattern Category : Menus & User Interface, State Management (Sub-View Strategy)
Dimension        : 2D

Problem Solved:
  Monolithic RPG character menus attempt to cram inventory bags, equipment dolls,
  skill trees, and character attributes onto a single cluttered screen, causing visual
  overload and navigation confusion on controllers. Conversely, separating them into
  distinct full-screen scenes requires clunky push/pop transitions and loses immediate
  stat feedback. The Tabbed Menu pattern solves this by providing a unified master frame
  with an active tab index, swapping lightweight sub-view panels (Items, Equipment,
  Skills, Status) while preserving a single shared character model and enabling crisp
  bumper-driven (Q/E or Gamepad LB/RB) cycling.

How the Pattern Works:
  1. Tab Controller (Master-Detail Architecture):
     Maintains a list of Tab headers and an active_tab_index. Bumper inputs (Q/E or
     Gamepad LB/RB) cycle tabs with modulo wrap-around ((idx + delta) % N).
  2. Animated Indicator Rig:
     The active tab indicator smoothly glides along the header bar toward the target
     tab position using framerate-independent exponential damping (damp), giving tactile
     arcade feedback.
  3. Dynamic Sub-View Layouts (Strategy Pattern):
     Each tab renders a dedicated layout while reading from a single shared RPG
     character model:
       - Tab 0 [ITEMS]     : Consumable bag with quantities, descriptions, and use actions.
       - Tab 1 [EQUIPMENT] : 5-slot equipment doll (Helm, Armor, Weapon, Shield, Amulet).
       - Tab 2 [SKILLS]    : Allocatable talent tree with skill point budget and stat perks.
       - Tab 3 [STATUS]    : Full RPG attribute card (STR/AGI/INT/VIT) and animated 2D mascot.
  4. Reactive Stat Calculation Pipeline:
     Actions taken in one tab (e.g. consuming a potion, equipping gear, or spending
     skill points) immediately propagate to the character's derived stats (HP, MP, ATK,
     DEF, Crit Rate) in real time.

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - Q / E / Gamepad LB / RB            : Cycle Tabs Left / Right (Bumper Navigation)
  - Up/Down / W/S / Left Stick / D-Pad : Navigate internal items / slots / skills in current tab
  - Enter / Space / Gamepad A (Cross)  : Use Item / Equip Gear / Learn Skill
  - Mouse Click on Tab Headers / Items : Point and click direct selection (Dual Input)
  - [Tab] / Gamepad View (Select)      : Toggle X-Ray Telemetry & Stat Pipeline Overlay
  - [F1]  / Gamepad LB (Toggle Mode)   : Toggle Tab Indicator: [Spring Damped Slider] vs [Instant Snap]
  - [F2]  / Gamepad RB                 : Toggle Stat Pipeline: [Live Dynamic Calc] vs [Frozen Cache]
  - [Ctrl +/-]                         : Increase / Decrease UI Font Size
  - [F11]                              : Toggle Fullscreen
  - [R]   / Gamepad Start              : Reset Character Stats & Inventory
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
WINDOW_TITLE = "Tabbed Status Menu - RPG Sub-View Architecture (Raylib Pattern Lab)"

# Palette
COLOR_BG_DARK          = Color(10, 13, 22, 255)
COLOR_PANEL_BG         = Color(16, 22, 38, 245)
COLOR_PANEL_BORDER     = Color(45, 68, 108, 255)
COLOR_TAB_INACTIVE     = Color(22, 32, 54, 255)
COLOR_TAB_ACTIVE       = Color(35, 55, 92, 255)
COLOR_TEXT_MAIN        = Color(230, 240, 255, 255)
COLOR_TEXT_DIM         = Color(135, 160, 195, 255)
COLOR_CYAN_ACCENT      = Color(0, 225, 255, 255)
COLOR_GOLD_ACCENT      = Color(255, 205, 60, 255)
COLOR_GREEN_ACCENT     = Color(70, 255, 140, 255)

# Tab Indices (C++ Enum equivalent)
TAB_ITEMS      = 0
TAB_EQUIPMENT  = 1
TAB_SKILLS     = 2
TAB_STATUS     = 3
TAB_COUNT      = 4

TAB_NAMES = ["ITEMS", "EQUIPMENT", "SKILLS", "STATUS"]

# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATION
# ==============================================================================

class RPGCharacterModel:
    """
    Shared source of truth for all RPG sub-views.
    C++ Equivalent:
      struct RPGCharacterModel {
          std::string name;
          int level, hp, max_hp, mp, max_mp;
          int strength, agility, intellect, vitality;
          int base_atk, base_def;
          ...
      };
    """
    def __init__(self):
        self.name = "CYBER VANGUARD"
        self.level = 14
        self.xp = 3850
        self.xp_next = 5000

        # Base Attributes
        self.base_vitality = 18
        self.base_strength = 24
        self.base_agility = 16
        self.base_intellect = 12

        # Derived Combat Stats (Recalculated from gear + skills)
        self.max_hp = 320
        self.hp = 275
        self.max_mp = 120
        self.mp = 90
        self.atk = 58
        self.defense = 42
        self.crit_rate = 12.5

        # Available Skill Points
        self.skill_points = 3

        # Consumable Inventory Slots
        self.inventory = [
            {"name": "Nano Repair Kit",   "count": 4, "type": "heal_hp", "val": 65, "desc": "Restores 65 Hit Points instantly via micro-drones."},
            {"name": "Energy Cell Flacon","count": 3, "type": "heal_mp", "val": 45, "desc": "Recharges 45 Mana/Energy points for special abilities."},
            {"name": "Hyper-Overdrive",   "count": 2, "type": "buff_atk", "val": 15, "desc": "Temporary combat stimulant granting +15 Attack power."},
            {"name": "Hardened Shell Pill","count": 1, "type": "buff_def", "val": 20, "desc": "Hardens dermal plating, granting +20 Defense rating."}
        ]

        # Equipment Slots
        self.equipment = {
            "HEAD":  {"name": "Titanium Targeting Visor", "def": 12, "atk": 4,  "icon": "HELM"},
            "CHEST": {"name": "Composite Reactive Plate", "def": 32, "hp": 50,  "icon": "ARMOR"},
            "HANDS": {"name": "Vibro-Katana Saber",       "atk": 48, "crit": 8, "icon": "WEAPON"},
            "SHIELD":{"name": "Aegis Kinetic Barrier",    "def": 22, "hp": 25,  "icon": "SHIELD"},
            "AMULET":{"name": "Overclocking Matrix",      "atk": 12, "crit": 5, "icon": "RELIC"}
        }

        # Skill Allocations (Name, current rank, max rank, description)
        self.skills = [
            {"name": "Kinetic Overload", "rank": 2, "max_rank": 3, "desc": "+12% Physical Attack Damage per rank."},
            {"name": "Dermal Armor",     "rank": 1, "max_rank": 3, "desc": "+15 Armor and Damage Reduction per rank."},
            {"name": "Neural Reflexes",  "rank": 1, "max_rank": 3, "desc": "+4.0% Critical Strike Chance per rank."},
            {"name": "Reactor Surge",    "rank": 0, "max_rank": 3, "desc": "+25 Maximum Energy/MP capacity per rank."}
        ]

        self.recalculate_stats()

    def recalculate_stats(self):
        """Calculates derived stats from base attributes, equipped gear, and talent perks."""
        # 1. Base attribute contributions
        self.max_hp = 120 + self.base_vitality * 12
        self.max_mp = 50 + self.base_intellect * 8
        base_atk = 15 + self.base_strength * 2 + int(self.base_agility * 0.5)
        base_def = 10 + self.base_vitality * 1 + int(self.base_agility * 0.8)
        base_crit = 5.0 + self.base_agility * 0.4

        # 2. Equipment contributions
        for slot, gear in self.equipment.items():
            base_def += gear.get("def", 0)
            base_atk += gear.get("atk", 0)
            self.max_hp += gear.get("hp", 0)
            base_crit += gear.get("crit", 0.0)

        # 3. Skill perks
        atk_mult = 1.0 + (self.skills[0]["rank"] * 0.12)
        base_def += self.skills[1]["rank"] * 15
        base_crit += self.skills[2]["rank"] * 4.0
        self.max_mp += self.skills[3]["rank"] * 25

        self.atk = int(base_atk * atk_mult)
        self.defense = base_def
        self.crit_rate = base_crit

        # Clamp current health/mp
        self.hp = min(self.hp, self.max_hp)
        self.mp = min(self.mp, self.max_mp)


class TabController:
    """
    Manages active tab switching, modulo wrap-around, and animated sliding bar.
    """
    def __init__(self, tab_count: int, header_x: float, header_y: float, header_w: float, header_h: float):
        self.tab_count = tab_count
        self.active_tab = 0
        self.header_x = header_x
        self.header_y = header_y
        self.header_w = header_w
        self.header_h = header_h
        self.tab_w = header_w / float(tab_count)

        # Animated Indicator Rig
        self.indicator_x = header_x
        self.target_x = header_x
        self.smoothing = 18.0
        self.is_damped = True              # [F1] Toggle

        # State Telemetry Counters
        self.total_switches = 0

    def cycle_tab(self, delta: int):
        """Switches active tab using modulo wrap-around ((idx + delta) % N)."""
        prev = self.active_tab
        self.active_tab = ((self.active_tab + delta) % self.tab_count + self.tab_count) % self.tab_count
        if self.active_tab != prev:
            self.total_switches += 1
            self.target_x = self.header_x + self.active_tab * self.tab_w

    def set_tab(self, index: int):
        if 0 <= index < self.tab_count and index != self.active_tab:
            self.active_tab = index
            self.total_switches += 1
            self.target_x = self.header_x + self.active_tab * self.tab_w

    def update(self, dt: float):
        self.target_x = self.header_x + self.active_tab * self.tab_w
        if self.is_damped:
            self.indicator_x = damp(self.indicator_x, self.target_x, self.smoothing, dt)
        else:
            self.indicator_x = self.target_x

    def draw_headers(self, sfx: SoundLibrary):
        """Renders the top tab bar with clickable header buttons and the sliding indicator."""
        mx, my = get_mouse_x(), get_mouse_y()
        clicked = is_mouse_button_pressed(MOUSE_BUTTON_LEFT)

        # Tab Background Bar
        draw_rectangle(int(self.header_x), int(self.header_y), int(self.header_w), int(self.header_h), Color(14, 18, 30, 240))
        draw_rectangle_lines(int(self.header_x), int(self.header_y), int(self.header_w), int(self.header_h), COLOR_PANEL_BORDER)

        for i in range(self.tab_count):
            tx = self.header_x + i * self.tab_w
            is_active = (i == self.active_tab)
            hovered = (tx <= mx <= tx + self.tab_w) and (self.header_y <= my <= self.header_y + self.header_h)

            bg_col = COLOR_TAB_ACTIVE if is_active else (Color(28, 42, 68, 255) if hovered else COLOR_TAB_INACTIVE)
            draw_rectangle(int(tx), int(self.header_y), int(self.tab_w), int(self.header_h), bg_col)
            draw_rectangle_lines(int(tx), int(self.header_y), int(self.tab_w), int(self.header_h), COLOR_PANEL_BORDER)

            # Click direct tab selection
            if hovered and clicked:
                self.set_tab(i)
                sfx.play("click", 0.5)

            # Tab Label & Hotkey reminder
            label = TAB_NAMES[i]
            txt_col = COLOR_CYAN_ACCENT if is_active else (WHITE if hovered else COLOR_TEXT_DIM)
            draw_text(label, int(tx + self.tab_w * 0.5 - len(label) * 4.6), int(self.header_y + 16), 15, txt_col)

        # Sliding Underline Indicator (Spring-damped or snapped)
        draw_rectangle(int(self.indicator_x), int(self.header_y + self.header_h - 4), int(self.tab_w), 4, COLOR_CYAN_ACCENT)


# ==============================================================================
# BLOCK 2: WORLD SIMULATION & ENTITIES
# ==============================================================================

class TabbedStatusMenuGame:
    """Master controller managing the 4 RPG sub-views and shared character model."""

    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()

        self.sfx = SoundLibrary()
        self.sfx.init_defaults()

        # Shared RPG Character Model
        self.character = RPGCharacterModel()

        # Master Tab Controller
        header_x = 180.0
        header_y = 75.0
        header_w = 920.0
        header_h = 48.0
        self.tab_controller = TabController(TAB_COUNT, header_x, header_y, header_w, header_h)

        # Sub-view Internal Selection Indices
        self.selected_item_idx = 0
        self.selected_equip_slot = 0
        self.selected_skill_idx = 0

        # Pattern Toggles
        self.show_xray = True
        self.live_stat_calc = True          # [F2] Toggle: Live recalculation vs cached
        self.cached_atk = self.character.atk
        self.cached_def = self.character.defense

        self.action_message = "Welcome to Cyber Vanguard Status Interface."
        self.action_timer = 0.0

    def show_feedback(self, text: str):
        self.action_message = text
        self.action_timer = 3.0

    def update(self):
        dt = min(get_frame_time(), 0.05)
        self.action_timer = max(0.0, self.action_timer - dt)

        # ----------------------------------------------------------------------
        # 1. GLOBAL PATTERN TOGGLES
        # ----------------------------------------------------------------------
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
            self.sfx.play("click", 0.6)

        if is_dual_pattern_toggle_pressed():
            self.tab_controller.is_damped = not self.tab_controller.is_damped
            self.sfx.play("coin", 0.65)

        if is_dual_secondary_toggle_pressed():
            self.live_stat_calc = not self.live_stat_calc
            if not self.live_stat_calc:
                self.cached_atk = self.character.atk
                self.cached_def = self.character.defense
            else:
                self.character.recalculate_stats()
            self.sfx.play("click", 0.6)

        if is_dual_reset_pressed():
            self.character = RPGCharacterModel()
            self.selected_item_idx = 0
            self.selected_equip_slot = 0
            self.selected_skill_idx = 0
            self.show_feedback("Character model & inventory reset to default.")
            self.sfx.play("powerup", 0.7)

        # ----------------------------------------------------------------------
        # 2. BUMPER TAB CYCLING (Q/E or Gamepad LB/RB)
        # ----------------------------------------------------------------------
        pad_id = get_active_gamepad_id()
        bumper_left = is_key_pressed(KEY_Q) or (pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_LEFT_TRIGGER_1))
        bumper_right = is_key_pressed(KEY_E) or (pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_TRIGGER_1))

        if bumper_left:
            self.tab_controller.cycle_tab(-1)
            self.sfx.play("click", 0.45)
        elif bumper_right:
            self.tab_controller.cycle_tab(1)
            self.sfx.play("click", 0.45)

        self.tab_controller.update(dt)

        # ----------------------------------------------------------------------
        # 3. INTERNAL SUB-VIEW NAVIGATION & ACTIONS
        # ----------------------------------------------------------------------
        nav_y = 0
        if is_key_pressed(KEY_UP) or is_key_pressed(KEY_W):
            nav_y = -1
        elif is_key_pressed(KEY_DOWN) or is_key_pressed(KEY_S):
            nav_y = 1

        if pad_id >= 0:
            if is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_LEFT_FACE_UP):
                nav_y = -1
            elif is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_LEFT_FACE_DOWN):
                nav_y = 1

        active = self.tab_controller.active_tab

        # --- SUB-VIEW 0: ITEMS INVENTORY ---
        if active == TAB_ITEMS:
            item_count = len(self.character.inventory)
            if nav_y != 0:
                self.selected_item_idx = (self.selected_item_idx + nav_y + item_count) % item_count
                self.sfx.play("click", 0.35)

            # Use Item action
            if is_dual_primary_fire_pressed() or is_key_pressed(KEY_ENTER) or is_key_pressed(KEY_SPACE):
                item = self.character.inventory[self.selected_item_idx]
                if item["count"] > 0:
                    item["count"] -= 1
                    if item["type"] == "heal_hp":
                        self.character.hp = min(self.character.max_hp, self.character.hp + item["val"])
                        self.show_feedback(f"Consumed {item['name']}: Restored +{item['val']} HP!")
                        self.sfx.play("powerup", 0.7)
                    elif item["type"] == "heal_mp":
                        self.character.mp = min(self.character.max_mp, self.character.mp + item["val"])
                        self.show_feedback(f"Consumed {item['name']}: Recharged +{item['val']} MP!")
                        self.sfx.play("coin", 0.7)
                    elif item["type"] == "buff_atk":
                        self.character.base_strength += 2
                        self.show_feedback(f"Overdrive injected: Permanent +2 STR (+4 ATK)!")
                        self.sfx.play("jump", 0.7)
                    elif item["type"] == "buff_def":
                        self.character.base_vitality += 2
                        self.show_feedback(f"Hardened shell applied: Permanent +2 VIT (+24 HP, +2 DEF)!")
                        self.sfx.play("jump", 0.7)

                    if self.live_stat_calc:
                        self.character.recalculate_stats()
                else:
                    self.show_feedback("Item slot depleted! None remaining.")
                    self.sfx.play("hurt", 0.5)

        # --- SUB-VIEW 1: EQUIPMENT DOLL ---
        elif active == TAB_EQUIPMENT:
            slots = list(self.character.equipment.keys())
            if nav_y != 0:
                self.selected_equip_slot = (self.selected_equip_slot + nav_y + len(slots)) % len(slots)
                self.sfx.play("click", 0.35)

            # Cycle / Upgrade Gear tier on slot
            if is_dual_primary_fire_pressed() or is_key_pressed(KEY_ENTER) or is_key_pressed(KEY_SPACE):
                slot_key = slots[self.selected_equip_slot]
                gear = self.character.equipment[slot_key]
                if "def" in gear:
                    gear["def"] += 5
                if "atk" in gear:
                    gear["atk"] += 6
                self.show_feedback(f"Upgraded {slot_key} [{gear['name']}] +Tier!")
                self.sfx.play("powerup", 0.75)
                if self.live_stat_calc:
                    self.character.recalculate_stats()

        # --- SUB-VIEW 2: SKILLS & TALENTS ---
        elif active == TAB_SKILLS:
            skill_count = len(self.character.skills)
            if nav_y != 0:
                self.selected_skill_idx = (self.selected_skill_idx + nav_y + skill_count) % skill_count
                self.sfx.play("click", 0.35)

            # Spend Skill Point (Enter / Confirm)
            if is_dual_primary_fire_pressed() or is_key_pressed(KEY_ENTER) or is_key_pressed(KEY_SPACE):
                skill = self.character.skills[self.selected_skill_idx]
                if self.character.skill_points > 0 and skill["rank"] < skill["max_rank"]:
                    skill["rank"] += 1
                    self.character.skill_points -= 1
                    self.show_feedback(f"Upgraded {skill['name']} to Rank {skill['rank']}/{skill['max_rank']}!")
                    self.sfx.play("powerup", 0.75)
                    if self.live_stat_calc:
                        self.character.recalculate_stats()
                elif skill["rank"] >= skill["max_rank"]:
                    self.show_feedback(f"{skill['name']} is already MAX RANK!")
                    self.sfx.play("hurt", 0.5)
                else:
                    self.show_feedback("No Skill Points available! Level up to gain more.")
                    self.sfx.play("hurt", 0.5)

        # --- SUB-VIEW 3: STATUS & CHARACTER INSPECTION ---
        elif active == TAB_STATUS:
            # Grant free XP/Level on confirm to test dynamic leveling
            if is_dual_primary_fire_pressed() or is_key_pressed(KEY_ENTER):
                self.character.level += 1
                self.character.skill_points += 1
                self.character.base_strength += 2
                self.character.base_vitality += 2
                self.character.base_agility += 1
                self.show_feedback(f"LEVEL UP! Reached Level {self.character.level} (+1 Skill Point, +Stats)!")
                self.sfx.play("powerup", 0.85)
                if self.live_stat_calc:
                    self.character.recalculate_stats()

    # ==========================================================================
    # BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY ([Tab], [F1], [F2])
    # ==========================================================================
    def draw_xray_overlay(self):
        """Displays internal tab indices, damping error, and stat dependency graph."""
        panel_x = 750
        panel_y = 140
        panel_w = 490
        panel_h = 510

        draw_rectangle(panel_x, panel_y, panel_w, panel_h, Color(14, 18, 30, 245))
        draw_rectangle_lines(panel_x, panel_y, panel_w, panel_h, Color(45, 75, 120, 255))

        draw_text("X-RAY TABBED MENU TELEMETRY [Tab]", panel_x + 16, panel_y + 14, 15, COLOR_CYAN_ACCENT)
        draw_line(panel_x + 16, panel_y + 36, panel_x + panel_w - 16, panel_y + 36, Color(45, 75, 120, 255))

        y = panel_y + 46

        # Pattern 1: Indicator Rig Damping
        damp_col = COLOR_GREEN_ACCENT if self.tab_controller.is_damped else Color(255, 120, 120, 255)
        damp_mode = "SPRING DAMPED SLIDER" if self.tab_controller.is_damped else "INSTANT RIGID SNAP"
        draw_text(f"[F1] Tab Indicator: {damp_mode}", panel_x + 16, y, 13, damp_col)
        y += 18
        err = abs(self.tab_controller.indicator_x - self.tab_controller.target_x)
        draw_text(f" * Target X: {self.tab_controller.target_x:.1f}px | Current: {self.tab_controller.indicator_x:.1f}px (Lag: {err:.2f}px)", panel_x + 16, y, 11, COLOR_TEXT_DIM)
        y += 15
        draw_text(f" * Total Bumper Switches: {self.tab_controller.total_switches}", panel_x + 16, y, 11, COLOR_TEXT_DIM)

        # Pattern 2: Stat Pipeline Mode
        y += 22
        stat_col = COLOR_GREEN_ACCENT if self.live_stat_calc else Color(255, 180, 80, 255)
        stat_mode = "LIVE DYNAMIC RECALCULATION" if self.live_stat_calc else "FROZEN CACHE (MANUAL REFRESH)"
        draw_text(f"[F2] Stat Propagation: {stat_mode}", panel_x + 16, y, 13, stat_col)
        y += 18
        draw_text(" * Derived stats update synchronously when gear/talents change", panel_x + 16, y, 11, COLOR_TEXT_DIM)

        # Active Sub-View Memory Map
        y += 24
        draw_text("SUB-VIEW ALLOCATION & ROUTING TABLE:", panel_x + 16, y, 13, COLOR_GOLD_ACCENT)
        y += 18
        for i, name in enumerate(TAB_NAMES):
            is_active = (i == self.tab_controller.active_tab)
            slot_bg = Color(24, 45, 75, 255) if is_active else Color(18, 24, 38, 255)
            draw_rectangle(panel_x + 16, y, panel_w - 32, 22, slot_bg)
            if is_active:
                draw_rectangle_lines(panel_x + 16, y, panel_w - 32, 22, COLOR_CYAN_ACCENT)

            status = ">> ACTIVE SUB-VIEW" if is_active else "   STANDBY IN MEMORY"
            col = COLOR_CYAN_ACCENT if is_active else COLOR_TEXT_DIM
            draw_text(f"Slot [{i}] {name:<12} {status}", panel_x + 22, y + 4, 11, col)
            y += 24

        # Real-time Stat Formula Breakdown
        y += 12
        draw_text("DERIVED COMBAT STAT CALCULATION FORMULAS:", panel_x + 16, y, 13, COLOR_GOLD_ACCENT)
        y += 18
        c = self.character
        draw_text(f" * Max HP = 120 + (VIT * 12) + Gear HP = {c.max_hp} HP", panel_x + 20, y, 11, Color(170, 210, 245, 255))
        y += 16
        draw_text(f" * Physical ATK = (15 + STR*2 + AGI*0.5 + Gear) * SkillMult = {c.atk} ATK", panel_x + 20, y, 11, Color(170, 210, 245, 255))
        y += 16
        draw_text(f" * Armor DEF = 10 + VIT*1 + AGI*0.8 + Gear DEF + Perk = {c.defense} DEF", panel_x + 20, y, 11, Color(170, 210, 245, 255))
        y += 16
        draw_text(f" * Crit Rate = 5.0% + (AGI * 0.4%) + Gear + Perk = {c.crit_rate:.1f}%", panel_x + 20, y, 11, Color(170, 210, 245, 255))

    # ==========================================================================
    # BLOCK 4: MAIN GAME LOOP & AUTOMATED SMOKE TEST
    # ==========================================================================
    def draw_subview_items(self, rx: int, ry: int, rw: int, rh: int):
        """Tab 0: Consumables & Bag Inventory Sub-view."""
        draw_text("CONSUMABLE SUPPLIES & NANO-INVENTORY", rx + 24, ry + 20, 16, COLOR_CYAN_ACCENT)
        draw_text("Select an item and press [Enter / Gamepad A] to consume and restore stats live:", rx + 24, ry + 42, 12, COLOR_TEXT_DIM)

        list_y = ry + 70
        for i, item in enumerate(self.character.inventory):
            is_sel = (i == self.selected_item_idx)
            item_h = 44
            bg_col = Color(30, 52, 88, 255) if is_sel else Color(18, 26, 44, 255)
            draw_rectangle(rx + 24, list_y, rw - 48, item_h, bg_col)
            if is_sel:
                draw_rectangle_lines(rx + 24, list_y, rw - 48, item_h, COLOR_CYAN_ACCENT)

            # Item details
            txt_col = WHITE if is_sel else COLOR_TEXT_MAIN
            draw_text(f"{i + 1}. {item['name']}", rx + 38, list_y + 13, 15, txt_col)
            qty_col = COLOR_GOLD_ACCENT if item["count"] > 0 else Color(255, 80, 80, 255)
            draw_text(f"Qty: x{item['count']:02d}", rx + rw - 130, list_y + 13, 14, qty_col)
            list_y += item_h + 10

        # Description Card for selected item
        cur = self.character.inventory[self.selected_item_idx]
        card_y = ry + rh - 130
        draw_rectangle(rx + 24, card_y, rw - 48, 110, Color(14, 20, 34, 255))
        draw_rectangle_lines(rx + 24, card_y, rw - 48, 110, COLOR_PANEL_BORDER)
        draw_text(f"ITEM SPECS: {cur['name']}", rx + 38, card_y + 14, 15, COLOR_GOLD_ACCENT)
        draw_text(cur["desc"], rx + 38, card_y + 40, 13, COLOR_TEXT_DIM)
        draw_text(f"Action Payload: {cur['type'].upper()} (+{cur['val']})", rx + 38, card_y + 70, 12, COLOR_GREEN_ACCENT)

    def draw_subview_equipment(self, rx: int, ry: int, rw: int, rh: int):
        """Tab 1: 5-Slot Equipment Doll Sub-view."""
        draw_text("ACTIVE COMBAT LOADOUT & GEAR SLOTS", rx + 24, ry + 20, 16, COLOR_CYAN_ACCENT)
        draw_text("Equipped weapons and armor contribute directly to the character stat pipeline:", rx + 24, ry + 42, 12, COLOR_TEXT_DIM)

        slots = list(self.character.equipment.keys())
        list_y = ry + 70
        for i, slot_name in enumerate(slots):
            gear = self.character.equipment[slot_name]
            is_sel = (i == self.selected_equip_slot)
            slot_h = 50
            bg_col = Color(30, 52, 88, 255) if is_sel else Color(18, 26, 44, 255)
            draw_rectangle(rx + 24, list_y, rw - 48, slot_h, bg_col)
            if is_sel:
                draw_rectangle_lines(rx + 24, list_y, rw - 48, slot_h, COLOR_CYAN_ACCENT)

            # Slot name badge
            draw_rectangle(rx + 36, list_y + 10, 85, 30, Color(12, 18, 30, 255))
            draw_text(slot_name, rx + 44, list_y + 18, 12, COLOR_GOLD_ACCENT)

            # Gear name & stats
            txt_col = WHITE if is_sel else COLOR_TEXT_MAIN
            draw_text(gear["name"], rx + 135, list_y + 16, 15, txt_col)

            stat_str = ""
            if "atk" in gear: stat_str += f"+{gear['atk']} ATK  "
            if "def" in gear: stat_str += f"+{gear['def']} DEF  "
            if "hp" in gear: stat_str += f"+{gear['hp']} HP  "
            if "crit" in gear: stat_str += f"+{gear['crit']}% CRIT"
            draw_text(stat_str, rx + rw - 220, list_y + 17, 13, COLOR_GREEN_ACCENT)

            list_y += slot_h + 10

        # Upgrade tip
        tip_y = ry + rh - 65
        draw_rectangle(rx + 24, tip_y, rw - 48, 45, Color(14, 20, 34, 255))
        draw_text("Press [Enter / Space / Gamepad A] to Upgrade selected slot (+ATK/+DEF live)", rx + 38, tip_y + 15, 13, COLOR_CYAN_ACCENT)

    def draw_subview_skills(self, rx: int, ry: int, rw: int, rh: int):
        """Tab 2: Talent Tree & Skill Point Budget Sub-view."""
        draw_text("CYBERNETIC TALENTS & SPECIALIZATION TREE", rx + 24, ry + 20, 16, COLOR_CYAN_ACCENT)
        sp_text = f"AVAILABLE TALENT POINTS: {self.character.skill_points}"
        draw_text(sp_text, rx + rw - len(sp_text) * 8 - 30, ry + 20, 14, COLOR_GOLD_ACCENT)

        list_y = ry + 65
        for i, skill in enumerate(self.character.skills):
            is_sel = (i == self.selected_skill_idx)
            card_h = 68
            bg_col = Color(30, 52, 88, 255) if is_sel else Color(18, 26, 44, 255)
            draw_rectangle(rx + 24, list_y, rw - 48, card_h, bg_col)
            if is_sel:
                draw_rectangle_lines(rx + 24, list_y, rw - 48, card_h, COLOR_CYAN_ACCENT)

            # Skill name & rank indicator
            txt_col = WHITE if is_sel else COLOR_TEXT_MAIN
            draw_text(skill["name"], rx + 38, list_y + 14, 16, txt_col)
            draw_text(skill["desc"], rx + 38, list_y + 40, 12, COLOR_TEXT_DIM)

            # Rank pips (e.g. [X] [X] [ ])
            pip_x = rx + rw - 130
            for r in range(skill["max_rank"]):
                is_filled = (r < skill["rank"])
                pip_col = COLOR_GOLD_ACCENT if is_filled else Color(50, 65, 90, 255)
                draw_rectangle(pip_x + r * 24, list_y + 22, 18, 18, pip_col)
                draw_rectangle_lines(pip_x + r * 24, list_y + 22, 18, 18, Color(120, 150, 190, 255))

            list_y += card_h + 10

        tip_y = ry + rh - 65
        draw_rectangle(rx + 24, tip_y, rw - 48, 45, Color(14, 20, 34, 255))
        draw_text("Press [Enter / Space / Gamepad A] to allocate talent point into selected perk", rx + 38, tip_y + 15, 13, COLOR_CYAN_ACCENT)

    def draw_subview_status(self, rx: int, ry: int, rw: int, rh: int):
        """Tab 3: Full Attribute Grid & 2D Animated Character Mascot."""
        c = self.character

        # Left Column: Animated Character Mascot
        doll_w = 260
        draw_rectangle(rx + 24, ry + 20, doll_w, rh - 40, Color(14, 20, 32, 255))
        draw_rectangle_lines(rx + 24, ry + 20, doll_w, rh - 40, COLOR_PANEL_BORDER)

        draw_text(c.name, rx + 45, ry + 36, 16, COLOR_CYAN_ACCENT)
        draw_text(f"CLASS: COMBAT MECHA PILOT", rx + 45, ry + 58, 11, COLOR_TEXT_DIM)

        # Draw 2D Character Mascot in idle stance
        char_center = Vector2(rx + 24 + doll_w * 0.5, ry + 250)
        draw_humanoid_enemy_2d(char_center, facing_angle_rad=0.0, anim_timer=get_time(), scale=2.2, is_attacking=False)

        draw_text("Press [Enter / A] to Grant XP", rx + 45, ry + rh - 45, 12, COLOR_GOLD_ACCENT)

        # Right Column: Attribute Grid & Health Bars
        grid_x = rx + doll_w + 44
        grid_w = rw - doll_w - 68

        draw_text(f"LEVEL {c.level} VANGUARD", grid_x, ry + 24, 19, GOLD)

        # HP Bar
        draw_text(f"HEALTH: {c.hp} / {c.max_hp}", grid_x, ry + 56, 13, WHITE)
        draw_rectangle(grid_x, ry + 74, grid_w, 14, Color(30, 40, 50, 255))
        hp_ratio = max(0.0, min(1.0, c.hp / float(c.max_hp)))
        draw_rectangle(grid_x, ry + 74, int(grid_w * hp_ratio), 14, Color(0, 220, 120, 255))
        draw_rectangle_lines(grid_x, ry + 74, grid_w, 14, Color(100, 140, 180, 255))

        # MP Bar
        draw_text(f"ENERGY: {c.mp} / {c.max_mp}", grid_x, ry + 98, 13, WHITE)
        draw_rectangle(grid_x, ry + 116, grid_w, 14, Color(30, 40, 50, 255))
        mp_ratio = max(0.0, min(1.0, c.mp / float(c.max_mp)))
        draw_rectangle(grid_x, ry + 116, int(grid_w * mp_ratio), 14, Color(0, 180, 255, 255))
        draw_rectangle_lines(grid_x, ry + 116, grid_w, 14, Color(100, 140, 180, 255))

        # Core Attributes
        attr_y = ry + 155
        draw_text("PRIMARY SYSTEM ATTRIBUTES:", grid_x, attr_y, 14, COLOR_GOLD_ACCENT)
        attr_y += 24
        draw_text(f" * VITALITY   : {c.base_vitality:<4} (+{c.base_vitality * 12} HP pool)", grid_x, attr_y, 13, COLOR_TEXT_MAIN)
        attr_y += 20
        draw_text(f" * STRENGTH   : {c.base_strength:<4} (+{c.base_strength * 2} Melee ATK)", grid_x, attr_y, 13, COLOR_TEXT_MAIN)
        attr_y += 20
        draw_text(f" * AGILITY    : {c.base_agility:<4} (+{c.base_agility * 0.4:.1f}% Crit)", grid_x, attr_y, 13, COLOR_TEXT_MAIN)
        attr_y += 20
        draw_text(f" * INTELLECT  : {c.base_intellect:<4} (+{c.base_intellect * 8} Energy)", grid_x, attr_y, 13, COLOR_TEXT_MAIN)

        # Derived Combat Ratings
        attr_y += 32
        draw_text("FINAL DERIVED COMBAT RATINGS:", grid_x, attr_y, 14, COLOR_GOLD_ACCENT)
        attr_y += 24
        atk_val = c.atk if self.live_stat_calc else self.cached_atk
        def_val = c.defense if self.live_stat_calc else self.cached_def
        draw_text(f" * TOTAL ATTACK POWER : {atk_val} ATK", grid_x, attr_y, 14, Color(255, 120, 120, 255))
        attr_y += 22
        draw_text(f" * TOTAL ARMOR RATING : {def_val} DEF", grid_x, attr_y, 14, Color(100, 220, 255, 255))
        attr_y += 22
        draw_text(f" * CRIT STRIKE CHANCE : {c.crit_rate:.1f}%", grid_x, attr_y, 14, Color(255, 220, 80, 255))

    def draw(self):
        begin_drawing()
        clear_background(COLOR_BG_DARK)

        # Background Sci-Fi Grid Lines
        for gy in range(0, SCREEN_HEIGHT, 48):
            draw_line(0, gy, SCREEN_WIDTH, gy, Color(18, 24, 38, 120))
        for gx in range(0, SCREEN_WIDTH, 48):
            draw_line(gx, 0, gx, SCREEN_HEIGHT, Color(18, 24, 38, 120))

        # Title Screen Header
        draw_rectangle(0, 0, SCREEN_WIDTH, 60, Color(12, 16, 26, 240))
        draw_line(0, 60, SCREEN_WIDTH, 60, COLOR_PANEL_BORDER)
        draw_text("CYBER VANGUARD - TABBED STATUS INTERFACE", 35, 18, 20, COLOR_CYAN_ACCENT)

        # Top-Bar Dropdowns & Gamepad Badge
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)

        # Render Tab Headers Bar
        self.tab_controller.draw_headers(self.sfx)

        # Main Sub-view Panel
        panel_x = 180
        panel_y = 135
        panel_w = 920
        panel_h = 515

        draw_rectangle(panel_x, panel_y, panel_w, panel_h, COLOR_PANEL_BG)
        draw_rectangle_lines(panel_x, panel_y, panel_w, panel_h, COLOR_PANEL_BORDER)

        # Dispatch Active Sub-View
        active = self.tab_controller.active_tab
        if active == TAB_ITEMS:
            self.draw_subview_items(panel_x, panel_y, panel_w, panel_h)
        elif active == TAB_EQUIPMENT:
            self.draw_subview_equipment(panel_x, panel_y, panel_w, panel_h)
        elif active == TAB_SKILLS:
            self.draw_subview_skills(panel_x, panel_y, panel_w, panel_h)
        elif active == TAB_STATUS:
            self.draw_subview_status(panel_x, panel_y, panel_w, panel_h)

        # Action Feedback Banner
        if self.action_timer > 0.05:
            alpha = max(0, min(255, int(255 * (self.action_timer / 3.0))))
            draw_rectangle(panel_x, panel_y + panel_h - 32, panel_w, 32, Color(10, 30, 50, alpha))
            draw_text(self.action_message, panel_x + 20, panel_y + panel_h - 24, 13, Color(0, 240, 255, alpha))

        # X-Ray Telemetry Overlay
        if self.show_xray:
            self.draw_xray_overlay()

        # Footer Control Guide
        draw_rectangle(0, SCREEN_HEIGHT - 44, SCREEN_WIDTH, 44, Color(12, 16, 26, 240))
        draw_line(0, SCREEN_HEIGHT - 44, SCREEN_WIDTH, SCREEN_HEIGHT - 44, COLOR_PANEL_BORDER)
        draw_text(
            "[Q/E/LB/RB] Switch Tabs   [Up/Down/WASD] Navigate   [Enter/A/Click] Action   [Tab] X-Ray   [F1] Slider Damping   [F2] Stat Calc   [R] Reset",
            24, SCREEN_HEIGHT - 28, 12, Color(180, 205, 235, 255)
        )

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
    TabbedStatusMenuGame().run(smoke_test=is_smoke)

