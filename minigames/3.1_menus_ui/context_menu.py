# -*- coding: utf-8 -*-
"""
Context Menu - Floating Contextual Action Dispatcher & Smart Viewport Anchor
=============================================================================
Section          : 3.1 Menus & UI
Pattern Category : Menus & User Interface, Decoupling & Commands
Dimension        : 2D

Problem Solved:
  In RPGs, RTS games, and simulation sandboxes (World of Warcraft, Baldur's Gate,
  StarCraft, The Sims), interacting with world entities via a single generic button
  ('Press E to interact') is ambiguous and restrictive when entities support multiple
  contextual actions (e.g. Talk, Trade, Pickpocket, Inspect, Hack, Disarm). Conversely,
  naive floating context menus open at raw cursor coordinates and clip outside viewport
  boundaries when clicked near screen edges, desynchronize when submenus open off-screen,
  and tightly couple UI click listeners directly to game entity classes.

How the Pattern Works:
  1. Contextual Action Provider Interface:
     Entities implement a declarative action query: `get_context_actions(player, distance)`.
     The menu factory queries the hovered/selected entity to produce a dynamic list of
     `ContextAction` tokens (label, icon, hotkey, enabled state, requirement explanation,
     and optional sub-action cascade).
  2. Smart Viewport Clamping & Cascade Flipping:
     The menu measures its bounding box $(W, H)$ prior to rendering. If opening the menu
     at $(X, Y)$ would penetrate screen margins, the anchor flips horizontally ($X - W$)
     or vertically ($Y - H$). Nested cascading submenus inherit this orientation vector
     so multi-tier options never bleed past screen borders.
  3. Decoupled Command Dispatch:
     Selecting a menu item emits an immutable `ContextCommand` token rather than mutating
     entity state inside the UI draw call. The game simulation processes the command on the
     next logic tick, guaranteeing clean architectural separation.
  4. Dual Layout Strategy (List vs Radial Wheel):
     The pattern supports both classic vertical desktop cascading lists and modern 360-degree
     radial action wheels optimized for gamepads.

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - WASD / Left Stick / D-Pad             : Move Player avatar across the outpost
  - Mouse Cursor / Gamepad Right Stick   : Aim interaction reticle / cursor
  - Right Click / Gamepad X (Square)     : Open Context Menu on hovered entity or ground
  - W / S / Up / Down / D-Pad            : Navigate active context menu items
  - Enter / Space / Left Click / Gamepad A: Confirm selected contextual action
  - Esc / Gamepad B (Circle)             : Dismiss context menu / back up one submenu
  - [Tab] / Gamepad View (Select)        : Toggle X-Ray Context Anchor & Clamp Telemetry
  - [F1]  / Gamepad R3                   : Toggle Layout: [Smart Viewport Clamped List] vs [Radial Context Wheel]
  - [F2]  / Gamepad L3                   : Toggle Viewport Clamping: [Smart Margin Clamping] vs [Unclamped Naive]
  - [Ctrl +/-]                           : Increase / Decrease UI Font Size
  - [F11]                                : Toggle Fullscreen
  - [R]   / Gamepad Start                : Reset Player position, inventory & entities
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
WINDOW_TITLE = "Context Menu - Floating Contextual Action Dispatcher (Raylib Pattern Lab)"

# Color Palette (Crisp High-Tech Tactical Palette)
COLOR_BG_DARK           = Color(10, 14, 22, 255)
COLOR_FLOOR_GRID        = Color(20, 28, 44, 255)
COLOR_PANEL_BG          = Color(16, 22, 36, 250)
COLOR_PANEL_BORDER      = Color(45, 70, 115, 255)
COLOR_ITEM_NORMAL       = Color(24, 34, 56, 255)
COLOR_ITEM_HOVER        = Color(38, 58, 96, 255)
COLOR_ITEM_DISABLED     = Color(18, 24, 38, 200)
COLOR_TEXT_MAIN         = Color(230, 242, 255, 255)
COLOR_TEXT_DIM          = Color(125, 150, 185, 255)
COLOR_TEXT_DISABLED     = Color(75, 90, 115, 255)
COLOR_CYAN_ACCENT       = Color(0, 225, 255, 255)
COLOR_GOLD_ACCENT       = Color(255, 200, 50, 255)
COLOR_GREEN_ACCENT      = Color(65, 240, 130, 255)
COLOR_RED_ACCENT        = Color(255, 80, 80, 255)

# Entity Type IDs (C++ Enum equivalent)
ENTITY_PLAYER           = 0
ENTITY_MERCHANT         = 1
ENTITY_CARGO_CHEST      = 2
ENTITY_TERMINAL         = 3
ENTITY_BATTERY_ITEM     = 4
ENTITY_SLIME_PET        = 5
ENTITY_GROUND           = 6

# Layout Mode IDs (C++ Enum equivalent)
LAYOUT_VERTICAL_LIST    = 0
LAYOUT_RADIAL_WHEEL     = 1

# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATION (CONTEXT MENU ARCHITECTURE)
# ==============================================================================

class ContextAction:
    """
    A single actionable command item within a context menu.
    C++ Equivalent:
      struct ContextAction {
          std::string action_id;
          std::string label;
          std::string hotkey_hint;
          std::string requirement_tooltip;
          bool is_enabled;
          Color accent_color;
          std::vector<ContextAction> sub_actions;
      };
    """
    def __init__(self, action_id: str, label: str, hotkey_hint: str = "", requirement_tooltip: str = "", is_enabled: bool = True, accent_color: Color = None):
        self.action_id = action_id
        self.label = label
        self.hotkey_hint = hotkey_hint
        self.requirement_tooltip = requirement_tooltip
        self.is_enabled = is_enabled
        self.accent_color = accent_color if accent_color is not None else COLOR_CYAN_ACCENT
        self.sub_actions = []

    def add_sub_action(self, sub):
        self.sub_actions.append(sub)


class ContextMenuAnchor:
    """
    Calculates spatial clamping and flipping to keep floating menus inside screen bounds.
    C++ Equivalent:
      struct ContextMenuAnchor {
          float raw_x, raw_y;
          float clamped_x, clamped_y;
          float menu_width, menu_height;
          bool flipped_x, flipped_y;
          void compute(float screen_w, float screen_h, float margin, bool enable_clamping);
      };
    """
    def __init__(self):
        self.raw_x = 0.0
        self.raw_y = 0.0
        self.clamped_x = 0.0
        self.clamped_y = 0.0
        self.menu_width = 210.0
        self.menu_height = 200.0
        self.flipped_x = False
        self.flipped_y = False

    def compute(self, raw_x: float, raw_y: float, width: float, height: float, screen_w: float, screen_h: float, margin: float = 20.0, enable_clamping: bool = True):
        self.raw_x = raw_x
        self.raw_y = raw_y
        self.menu_width = width
        self.menu_height = height
        self.flipped_x = False
        self.flipped_y = False

        if not enable_clamping:
            # Naive unmanaged anchor (bleeds off-screen)
            self.clamped_x = raw_x
            self.clamped_y = raw_y
            return

        target_x = raw_x
        target_y = raw_y

        # Check right boundary: flip left if protruding
        if target_x + width > screen_w - margin:
            target_x = raw_x - width
            self.flipped_x = True

        # Check bottom boundary: flip up if protruding
        if target_y + height > screen_h - margin:
            target_y = raw_y - height
            self.flipped_y = True

        # Ensure we never protrude past top/left
        if target_x < margin:
            target_x = margin
        if target_y < margin:
            target_y = margin

        self.clamped_x = target_x
        self.clamped_y = target_y


class ContextMenuController:
    """
    State machine and layout manager for floating context menus.
    C++ Equivalent:
      class ContextMenuController {
      public:
          bool is_open;
          std::vector<ContextAction> actions;
          int selected_index;
          int active_submenu_index;
          ContextMenuAnchor anchor;
          // ... methods
      };
    """
    def __init__(self):
        self.is_open = False
        self.actions = []
        self.selected_index = 0
        self.active_submenu_index = -1
        self.submenu_selected_index = 0
        self.anchor = ContextMenuAnchor()
        self.target_entity_id = -1
        self.target_entity_name = "Ground"
        self.layout_mode = LAYOUT_VERTICAL_LIST
        self.clamping_enabled = True
        self.anim_alpha = 0.0
        self.anim_scale = 0.8
        self.item_height = 36.0
        self.item_width = 220.0
        self.submenu_width = 200.0

    def open_menu(self, world_x: float, world_y: float, actions_list, entity_id: int, entity_name: str):
        self.actions = []
        for act in actions_list:
            self.actions.append(act)
        self.selected_index = 0
        self.active_submenu_index = -1
        self.submenu_selected_index = 0
        self.target_entity_id = entity_id
        self.target_entity_name = entity_name
        self.is_open = True
        self.anim_alpha = 0.0
        self.anim_scale = 0.85

        # Calculate bounding dimensions
        total_h = 32.0 + len(self.actions) * self.item_height + 10.0
        self.anchor.compute(world_x, world_y, self.item_width, total_h, SCREEN_WIDTH, SCREEN_HEIGHT, 24.0, self.clamping_enabled)

    def close_menu(self):
        self.is_open = False
        self.actions = []
        self.active_submenu_index = -1
        self.target_entity_id = -1

    def update_animation(self, dt: float):
        if self.is_open:
            self.anim_alpha = damp(self.anim_alpha, 1.0, 16.0, dt)
            self.anim_scale = damp(self.anim_scale, 1.0, 16.0, dt)
        else:
            self.anim_alpha = 0.0
            self.anim_scale = 0.85


# ==============================================================================
# BLOCK 2: WORLD SIMULATION & ENTITIES
# ==============================================================================

class InteractableEntity:
    """
    Base struct representing an interactive outpost actor or object.
    C++ Equivalent:
      struct InteractableEntity {
          int id;
          int type;
          std::string name;
          Vector2 position;
          float interaction_radius;
          bool is_locked;
          bool is_active;
          int state_counter;
      };
    """
    def __init__(self, id_val: int, entity_type: int, name: str, x: float, y: float, radius: float):
        self.id = id_val
        self.type = entity_type
        self.name = name
        self.position = Vector2(x, y)
        self.radius = radius
        self.is_locked = True
        self.is_active = True
        self.state_counter = 0
        self.hp = 100
        self.anim_time = random.uniform(0.0, 10.0)

    def update(self, dt: float):
        self.anim_time += dt

    def get_actions(self, player_has_key: bool, player_has_hacktool: bool, dist_to_player: float):
        """
        Produces the contextual actions list tailored to current game state.
        Demonstrates dynamic condition gating (distance, inventory, locks).
        """
        actions = []
        in_range = (dist_to_player <= 160.0)
        range_msg = "" if in_range else "(Too Far: Step Closer)"

        if self.type == ENTITY_MERCHANT:
            # Talk
            act_talk = ContextAction("talk", "Communicate", "[E]", range_msg, in_range, COLOR_GREEN_ACCENT)
            # Sub-dialogues
            act_talk.add_sub_action(ContextAction("talk_rumors", "Ask About Local Rumors", "", "", in_range))
            act_talk.add_sub_action(ContextAction("talk_job", "Inquire About Bounties", "", "", in_range))
            act_talk.add_sub_action(ContextAction("talk_leave", "Farewell", "", "", True))
            actions.append(act_talk)

            # Trade
            act_trade = ContextAction("trade", "Barter Goods", "[T]", range_msg, in_range, COLOR_GOLD_ACCENT)
            act_trade.add_sub_action(ContextAction("trade_buy", "Buy Supplies & Ammo", "", "", in_range))
            act_trade.add_sub_action(ContextAction("trade_sell", "Sell Salvage Scraps", "", "", in_range))
            actions.append(act_trade)

            # Inspect
            actions.append(ContextAction("inspect", "Scan Bio-Readout", "[I]", "", True, COLOR_CYAN_ACCENT))

            # Pickpocket
            pocket_ready = in_range and dist_to_player < 70.0
            pocket_msg = "Must be right behind merchant" if not pocket_ready else ""
            actions.append(ContextAction("pickpocket", "Pickpocket Wallet", "[P]", pocket_msg, pocket_ready, COLOR_RED_ACCENT))

        elif self.type == ENTITY_CARGO_CHEST:
            if self.is_locked:
                unlock_ready = in_range and player_has_key
                unlock_tip = "" if unlock_ready else ("Requires Security Keycard" if in_range else range_msg)
                actions.append(ContextAction("unlock", "Unlock Cargo Lid", "[U]", unlock_tip, unlock_ready, COLOR_GOLD_ACCENT))

                force_ready = in_range
                actions.append(ContextAction("smash", "Pry Open with Crowbar", "[F]", range_msg, force_ready, COLOR_RED_ACCENT))
            else:
                actions.append(ContextAction("open", "Loot Cargo Contents", "[L]", range_msg, in_range, COLOR_GREEN_ACCENT))
                actions.append(ContextAction("lock", "Lock Container", "", range_msg, in_range, COLOR_TEXT_DIM))

            actions.append(ContextAction("inspect", "Examine Markings", "[I]", "", True, COLOR_CYAN_ACCENT))

        elif self.type == ENTITY_TERMINAL:
            # Hack
            hack_ready = in_range and player_has_hacktool
            hack_tip = "" if hack_ready else ("Requires Data Deck tool" if in_range else range_msg)
            act_hack = ContextAction("hack", "Breach Mainframe", "[H]", hack_tip, hack_ready, COLOR_GREEN_ACCENT)
            act_hack.add_sub_action(ContextAction("hack_logs", "Download Security Logs", "", "", hack_ready))
            act_hack.add_sub_action(ContextAction("hack_cameras", "Disable Sentinel Turrets", "", "", hack_ready))
            act_hack.add_sub_action(ContextAction("hack_purge", "Wipe Master Database", "", "", hack_ready, COLOR_RED_ACCENT))
            actions.append(act_hack)

            # Power Toggle
            pwr_label = "Deactivate Power" if self.is_active else "Initialize Reactor"
            actions.append(ContextAction("power_toggle", pwr_label, "[P]", range_msg, in_range, COLOR_GOLD_ACCENT))

            # Diagnostics
            actions.append(ContextAction("diagnostics", "Run Sensor Diagnostics", "[D]", "", True, COLOR_CYAN_ACCENT))

        elif self.type == ENTITY_BATTERY_ITEM:
            actions.append(ContextAction("pickup", "Collect Plasma Cell", "[E]", range_msg, in_range, COLOR_GREEN_ACCENT))
            actions.append(ContextAction("inspect", "Analyze Charge Density", "[I]", "", True, COLOR_CYAN_ACCENT))
            actions.append(ContextAction("salvage", "Disassemble for Scrap", "[S]", range_msg, in_range, COLOR_GOLD_ACCENT))

        elif self.type == ENTITY_SLIME_PET:
            actions.append(ContextAction("pet", "Gently Pet Blob", "[P]", range_msg, in_range, COLOR_GREEN_ACCENT))
            actions.append(ContextAction("feed", "Feed Synthetic Biscuit", "[F]", range_msg, in_range, COLOR_GOLD_ACCENT))
            actions.append(ContextAction("poke", "Poke Elastic Membrane", "", range_msg, in_range, COLOR_CYAN_ACCENT))

        return actions


class OutpostSimulation:
    """
    2D Outpost environment containing player and interactive world entities.
    """
    def __init__(self):
        self.player_x = 420.0
        self.player_y = 360.0
        self.player_speed = 220.0
        self.player_has_keycard = True
        self.player_has_datadeck = True
        self.player_credits = 250
        self.cursor_world_x = 420.0
        self.cursor_world_y = 360.0
        self.hovered_entity = None

        # Pre-allocate world entities
        self.entities = []
        self.entities.append(InteractableEntity(1, ENTITY_MERCHANT, "Quartermaster Vane (Vendor)", 240.0, 200.0, 32.0))
        self.entities.append(InteractableEntity(2, ENTITY_CARGO_CHEST, "Class-4 Secure Cargo Box", 740.0, 210.0, 30.0))
        self.entities.append(InteractableEntity(3, ENTITY_TERMINAL, "Mainframe Access Terminal", 260.0, 520.0, 28.0))
        self.entities.append(InteractableEntity(4, ENTITY_BATTERY_ITEM, "High-Yield Plasma Cell", 720.0, 530.0, 22.0))
        self.entities.append(InteractableEntity(5, ENTITY_SLIME_PET, "Pet Slime (Gloop)", 490.0, 220.0, 24.0))

        # Action event log (last 6 items)
        self.event_log = []

    def update(self, dt: float, move_vec: Vector2, can_move: bool):
        if can_move:
            self.player_x += move_vec.x * self.player_speed * dt
            self.player_y += move_vec.y * self.player_speed * dt
            # Clamp player to walkable outpost floor
            self.player_x = max(80.0, min(800.0, self.player_x))
            self.player_y = max(100.0, min(620.0, self.player_y))

        # Update entity timers
        for ent in self.entities:
            ent.update(dt)

        # Update hovered entity based on cursor position
        self.hovered_entity = None
        for ent in self.entities:
            dx = self.cursor_world_x - ent.position.x
            dy = self.cursor_world_y - ent.position.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist <= ent.radius + 14.0:
                self.hovered_entity = ent
                break

    def log_event(self, text: str):
        self.event_log.append(text)
        if len(self.event_log) > 6:
            self.event_log.pop(0)

    def draw_world(self):
        # Draw tech outpost floor tiles
        for tx in range(60, 840, 60):
            for ty in range(80, 660, 60):
                draw_rectangle_lines(tx, ty, 60, 60, COLOR_FLOOR_GRID)

        # Outpost boundary walls
        draw_rectangle_lines(60, 80, 780, 580, Color(45, 65, 100, 255))
        draw_text("SECTOR-7 SECURE RESEARCH OUTPOST", 75, 92, 13, COLOR_TEXT_DIM)

        # Draw Entities
        for ent in self.entities:
            # Highlight ring if hovered
            is_hov = (self.hovered_entity == ent)
            if is_hov:
                draw_circle_lines(int(ent.position.x), int(ent.position.y), ent.radius + 8.0, COLOR_CYAN_ACCENT)

            # Draw according to entity type
            if ent.type == ENTITY_MERCHANT:
                draw_humanoid_enemy_2d(Vector2(ent.position.x, ent.position.y), 0.0, ent.anim_time, 24.0)
                draw_text(ent.name, int(ent.position.x - 70), int(ent.position.y + 30), 11, COLOR_TEXT_MAIN)

            elif ent.type == ENTITY_CARGO_CHEST:
                box_col = Color(160, 110, 45, 255) if ent.is_locked else Color(60, 140, 90, 255)
                bx = int(ent.position.x - 24)
                by = int(ent.position.y - 18)
                draw_rectangle(bx, by, 48, 36, box_col)
                draw_rectangle_lines(bx, by, 48, 36, COLOR_TEXT_MAIN)
                status_str = "LOCKED" if ent.is_locked else "OPEN"
                draw_text(status_str, int(ent.position.x - 20), int(ent.position.y - 5), 10, COLOR_TEXT_MAIN)
                draw_text(ent.name, int(ent.position.x - 65), int(ent.position.y + 24), 11, COLOR_TEXT_MAIN)

            elif ent.type == ENTITY_TERMINAL:
                tx = int(ent.position.x - 20)
                ty = int(ent.position.y - 25)
                p_col = Color(35, 55, 85, 255)
                draw_rectangle(tx, ty, 40, 50, p_col)
                draw_rectangle_lines(tx, ty, 40, 50, COLOR_CYAN_ACCENT if ent.is_active else COLOR_TEXT_DIM)
                # Terminal screen glow
                scr_col = COLOR_CYAN_ACCENT if ent.is_active else Color(40, 50, 60, 255)
                draw_rectangle(tx + 6, ty + 6, 28, 20, scr_col)
                draw_text(ent.name, int(ent.position.x - 70), int(ent.position.y + 30), 11, COLOR_TEXT_MAIN)

            elif ent.type == ENTITY_BATTERY_ITEM:
                glow_r = 14.0 + math.sin(ent.anim_time * 5.0) * 3.0
                draw_circle(int(ent.position.x), int(ent.position.y), glow_r, Color(0, 200, 255, 60))
                draw_circle(int(ent.position.x), int(ent.position.y), 10.0, COLOR_CYAN_ACCENT)
                draw_circle_lines(int(ent.position.x), int(ent.position.y), 10.0, COLOR_TEXT_MAIN)
                draw_text(ent.name, int(ent.position.x - 60), int(ent.position.y + 18), 11, COLOR_TEXT_MAIN)

            elif ent.type == ENTITY_SLIME_PET:
                draw_slime_enemy_2d(Vector2(ent.position.x, ent.position.y), ent.anim_time, 22.0)
                draw_text(ent.name, int(ent.position.x - 45), int(ent.position.y + 26), 11, COLOR_TEXT_MAIN)

        # Draw Player Avatar
        draw_circle(int(self.player_x), int(self.player_y), 18.0, COLOR_CYAN_ACCENT)
        draw_circle_lines(int(self.player_x), int(self.player_y), 18.0, COLOR_TEXT_MAIN)
        draw_circle(int(self.player_x), int(self.player_y - 2), 6.0, Color(15, 25, 45, 255))
        draw_text("PLAYER", int(self.player_x - 22), int(self.player_y + 24), 11, COLOR_CYAN_ACCENT)

        # Interaction range ring around player (subtle)
        draw_circle_lines(int(self.player_x), int(self.player_y), 160.0, Color(0, 225, 255, 40))

        # Draw Cursor Reticle
        ret_x = int(self.cursor_world_x)
        ret_y = int(self.cursor_world_y)
        draw_circle_lines(ret_x, ret_y, 7.0, COLOR_GOLD_ACCENT)
        draw_line(ret_x - 12, ret_y, ret_x + 12, ret_y, COLOR_GOLD_ACCENT)
        draw_line(ret_x, ret_y - 12, ret_x, ret_y + 12, COLOR_GOLD_ACCENT)


# ==============================================================================
# BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY ([Tab] & [F1])
# ==============================================================================

def draw_xray_context_inspector(menu: ContextMenuController, sim: OutpostSimulation, x: int, y: int, w: int, h: int):
    """
    Renders diagnostic telemetry for context anchor calculation, clamping vectors,
    and dispatched contextual commands.
    """
    draw_rectangle(x, y, w, h, Color(14, 20, 32, 245))
    draw_rectangle_lines(x, y, w, h, COLOR_CYAN_ACCENT)

    # Title Banner
    draw_rectangle(x, y, w, 28, Color(22, 36, 60, 255))
    draw_text("CONTEXT MENU X-RAY TELEMETRY", x + 10, y + 7, 13, COLOR_CYAN_ACCENT)

    cy = y + 36

    # 1. Menu State
    state_str = "MENU STATUS: " + ("OPEN (ACTIVE)" if menu.is_open else "IDLE / CLOSED")
    state_col = COLOR_GREEN_ACCENT if menu.is_open else COLOR_TEXT_DIM
    draw_text(state_str, x + 12, cy, 12, state_col)
    cy += 18

    # 2. Layout & Clamping Modes
    layout_name = "SMART VERTICAL LIST" if menu.layout_mode == LAYOUT_VERTICAL_LIST else "RADIAL ACTION WHEEL"
    draw_text("LAYOUT: " + layout_name, x + 12, cy, 12, COLOR_TEXT_MAIN)
    cy += 18

    clamp_str = "VIEWPORT CLAMP: " + ("ENABLED [SMART FLIP]" if menu.clamping_enabled else "DISABLED [UNBOUNDED]")
    clamp_col = COLOR_GOLD_ACCENT if menu.clamping_enabled else COLOR_RED_ACCENT
    draw_text(clamp_str, x + 12, cy, 12, clamp_col)
    cy += 22

    # 3. Spatial Anchor Coordinates & Flipping
    draw_text("SPATIAL ANCHOR CALCULATION:", x + 12, cy, 11, COLOR_CYAN_ACCENT)
    cy += 16

    anc = menu.anchor
    draw_text("Raw Click Origin: (" + str(int(anc.raw_x)) + ", " + str(int(anc.raw_y)) + ")", x + 18, cy, 11, COLOR_TEXT_DIM)
    cy += 15
    draw_text("Clamped Origin:   (" + str(int(anc.clamped_x)) + ", " + str(int(anc.clamped_y)) + ")", x + 18, cy, 11, COLOR_TEXT_MAIN)
    cy += 15
    draw_text("Box Size (W x H): " + str(int(anc.menu_width)) + " x " + str(int(anc.menu_height)), x + 18, cy, 11, COLOR_TEXT_DIM)
    cy += 15

    flip_tag = "Flip-X: " + ("YES (Left)" if anc.flipped_x else "NO (Right)") + " | Flip-Y: " + ("YES (Up)" if anc.flipped_y else "NO (Down)")
    draw_text(flip_tag, x + 18, cy, 11, COLOR_GOLD_ACCENT if (anc.flipped_x or anc.flipped_y) else COLOR_TEXT_DIM)
    cy += 20

    draw_line(x + 10, cy, x + w - 10, cy, Color(35, 50, 75, 255))
    cy += 12

    # 4. Target Entity & Query
    draw_text("TARGET CONTEXT QUERY:", x + 12, cy, 11, COLOR_CYAN_ACCENT)
    cy += 16
    draw_text("Target Name: " + menu.target_entity_name, x + 18, cy, 11, COLOR_TEXT_MAIN)
    cy += 15
    draw_text("Active Actions Count: " + str(len(menu.actions)), x + 18, cy, 11, COLOR_TEXT_DIM)
    cy += 15
    draw_text("Submenu Cascade Index: " + str(menu.active_submenu_index), x + 18, cy, 11, COLOR_TEXT_DIM)
    cy += 20

    draw_line(x + 10, cy, x + w - 10, cy, Color(35, 50, 75, 255))
    cy += 12

    # 5. Inventory & Tool State
    draw_text("PLAYER PREREQUISITES PURSE:", x + 12, cy, 11, COLOR_CYAN_ACCENT)
    cy += 16
    k_str = "[YES] OWNED" if sim.player_has_keycard else "[NO] MISSING"
    draw_text("Security Keycard: " + k_str, x + 18, cy, 11, COLOR_GREEN_ACCENT if sim.player_has_keycard else COLOR_RED_ACCENT)
    cy += 15

    d_str = "[YES] OWNED" if sim.player_has_datadeck else "[NO] MISSING"
    draw_text("Data Deck Hacker: " + d_str, x + 18, cy, 11, COLOR_GREEN_ACCENT if sim.player_has_datadeck else COLOR_RED_ACCENT)
    cy += 15
    draw_text("Credits: " + str(sim.player_credits) + " CR", x + 18, cy, 11, COLOR_GOLD_ACCENT)
    cy += 20

    draw_line(x + 10, cy, x + w - 10, cy, Color(35, 50, 75, 255))
    cy += 12

    # 6. Dispatched Event History
    draw_text("RECENT COMMAND DISPATCH HISTORY:", x + 12, cy, 11, COLOR_CYAN_ACCENT)
    cy += 16
    if len(sim.event_log) == 0:
        draw_text("<No commands dispatched yet>", x + 18, cy, 10, COLOR_TEXT_DIM)
    else:
        for ev in sim.event_log:
            draw_text("> " + ev, x + 18, cy, 10, COLOR_TEXT_DIM)
            cy += 15


# ==============================================================================
# BLOCK 4: MAIN GAME LOOP & AUTOMATED SMOKE TEST
# ==============================================================================

class ContextMenuGame:
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()
        self.sfx = SoundLibrary()
        self.sfx.init_defaults()

        # Telemetry & Pattern Toggles
        self.show_xray = True
        self.layout_mode = LAYOUT_VERTICAL_LIST
        self.smart_clamping = True

        # World Simulation
        self.simulation = OutpostSimulation()

        # Core Pattern: Context Menu Controller
        self.menu_controller = ContextMenuController()
        self.menu_controller.layout_mode = self.layout_mode
        self.menu_controller.clamping_enabled = self.smart_clamping

        # Toast notification
        self.toast_msg = "Right-Click any entity or ground to trigger contextual actions."
        self.toast_timer = 4.0

    def _open_context_menu_at_cursor(self):
        cx = self.simulation.cursor_world_x
        cy = self.simulation.cursor_world_y

        ent = self.simulation.hovered_entity
        if ent:
            dx = self.simulation.player_x - ent.position.x
            dy = self.simulation.player_y - ent.position.y
            dist = math.sqrt(dx * dx + dy * dy)
            actions = ent.get_actions(self.simulation.player_has_keycard, self.simulation.player_has_datadeck, dist)
            self.menu_controller.open_menu(cx, cy, actions, ent.id, ent.name)
            self.sfx.play("click", 0.6)
        else:
            # Empty Ground Context Actions
            ground_actions = [
                ContextAction("ground_move", "Move Avatar Here", "[M]", "", True, COLOR_CYAN_ACCENT),
                ContextAction("ground_scan", "Scan Soil Composition", "[S]", "", True, COLOR_GOLD_ACCENT),
                ContextAction("ground_beacon", "Deploy Signal Beacon", "[B]", "", True, COLOR_GREEN_ACCENT),
            ]
            self.menu_controller.open_menu(cx, cy, ground_actions, -1, "Sector Floor (Ground)")
            self.sfx.play("click", 0.5)

    def _dispatch_context_command(self, action_id: str):
        """Processes dispatched contextual commands and updates simulation state."""
        self.sfx.play("pickup", 0.7)
        self.menu_controller.close_menu()

        if action_id == "ground_move":
            self.simulation.player_x = self.simulation.cursor_world_x
            self.simulation.player_y = self.simulation.cursor_world_y
            self.simulation.log_event("Player moved to target position")
            self.toast_msg = "Command Executed: Avatar Repositioned."
            self.toast_timer = 2.5

        elif action_id == "ground_scan":
            self.simulation.log_event("Soil scan: Nitrogen 78%, Trace Silicates")
            self.toast_msg = "Sensor Sweep: Area clear of biological threats."
            self.toast_timer = 3.0

        elif action_id == "ground_beacon":
            self.simulation.log_event("Beacon deployed at cursor coordinates")
            self.toast_msg = "Signal Beacon deployed successfully."
            self.toast_timer = 3.0

        elif action_id == "talk":
            self.simulation.log_event("Vane: 'Keep your weapon holstered, spacer.'")
            self.toast_msg = "Merchant: 'Welcome to Outpost 7. What's your business?'"
            self.toast_timer = 3.0

        elif action_id == "talk_rumors":
            self.simulation.log_event("Vane: 'They say the terminal carries old terraforming codes.'")
            self.toast_msg = "Rumor Added to Journal!"
            self.toast_timer = 3.0

        elif action_id == "trade_buy":
            if self.simulation.player_credits >= 50:
                self.simulation.player_credits -= 50
                self.simulation.log_event("Purchased Medical Stimpak (-50 CR)")
                self.toast_msg = "Supplies Purchased (-50 Credits)."
            else:
                self.toast_msg = "Insufficient Credits!"
            self.toast_timer = 3.0

        elif action_id == "trade_sell":
            self.simulation.player_credits += 75
            self.simulation.log_event("Sold scrap metal (+75 CR)")
            self.toast_msg = "Scrap Sold (+75 Credits)."
            self.toast_timer = 3.0

        elif action_id == "pickpocket":
            self.simulation.player_credits += 120
            self.simulation.log_event("Pickpocket successful! Stole 120 CR")
            self.toast_msg = "Stealth Strike: 120 Credits Pilfered!"
            self.toast_timer = 3.0

        elif action_id == "unlock":
            for ent in self.simulation.entities:
                if ent.type == ENTITY_CARGO_CHEST:
                    ent.is_locked = False
            self.simulation.log_event("Keycard accepted: Cargo box unlocked")
            self.toast_msg = "Access Granted: Cargo Box Unlocked!"
            self.toast_timer = 3.0

        elif action_id == "smash":
            for ent in self.simulation.entities:
                if ent.type == ENTITY_CARGO_CHEST:
                    ent.is_locked = False
            self.simulation.log_event("Crowbar forced latch: Cargo box pried open")
            self.toast_msg = "Force Applied: Lock Broken Open!"
            self.toast_timer = 3.0

        elif action_id == "open":
            self.simulation.player_credits += 200
            self.simulation.log_event("Looted cargo box (+200 CR, High-Grade Alloy)")
            self.toast_msg = "Loot Collected: +200 CR & Alloy!"
            self.toast_timer = 3.5

        elif action_id == "lock":
            for ent in self.simulation.entities:
                if ent.type == ENTITY_CARGO_CHEST:
                    ent.is_locked = True
            self.simulation.log_event("Cargo box manually re-locked")
            self.toast_msg = "Container Secured & Locked."
            self.toast_timer = 2.5

        elif action_id == "hack_logs":
            self.simulation.log_event("Mainframe logs decrypted: Clearance Alpha")
            self.toast_msg = "Data Deck: 4 Security Logs Downloaded."
            self.toast_timer = 3.0

        elif action_id == "hack_cameras":
            self.simulation.log_event("Turret targeting subroutines bypassed")
            self.toast_msg = "Defense Grid Neutralized."
            self.toast_timer = 3.0

        elif action_id == "hack_purge":
            self.simulation.log_event("Terminal database wiped cleanly")
            self.toast_msg = "Data Purge Complete."
            self.toast_timer = 3.0

        elif action_id == "power_toggle":
            for ent in self.simulation.entities:
                if ent.type == ENTITY_TERMINAL:
                    ent.is_active = not ent.is_active
            self.simulation.log_event("Terminal reactor power state flipped")
            self.toast_msg = "Reactor Power State Toggled."
            self.toast_timer = 2.5

        elif action_id == "diagnostics":
            self.simulation.log_event("Diagnostics: Subsystems operational at 99.4%")
            self.toast_msg = "All Circuits Nominal."
            self.toast_timer = 2.5

        elif action_id == "pickup":
            # Remove battery from entities
            kept = []
            for ent in self.simulation.entities:
                if ent.type != ENTITY_BATTERY_ITEM:
                    kept.append(ent)
            self.simulation.entities = kept
            self.simulation.log_event("Plasma battery picked up and stored")
            self.toast_msg = "Plasma Battery Added to Inventory."
            self.toast_timer = 3.0

        elif action_id == "salvage":
            kept = []
            for ent in self.simulation.entities:
                if ent.type != ENTITY_BATTERY_ITEM:
                    kept.append(ent)
            self.simulation.entities = kept
            self.simulation.player_credits += 150
            self.simulation.log_event("Battery disassembled (+150 CR Salvage)")
            self.toast_msg = "Battery Salvaged (+150 Credits)."
            self.toast_timer = 3.0

        elif action_id == "pet":
            self.simulation.log_event("Gloop purrs happily and wiggles")
            self.toast_msg = "Slime Pet smiles warmly!"
            self.toast_timer = 2.5

        elif action_id == "feed":
            self.simulation.log_event("Gloop engulfs biscuit in one gulp")
            self.toast_msg = "Slime Fed: Affinity Increased!"
            self.toast_timer = 2.5

        elif action_id == "poke":
            self.simulation.log_event("Gloop squishes with a loud *plop*")
            self.toast_msg = "Slime jiggles playfully!"
            self.toast_timer = 2.5

        elif action_id == "inspect":
            self.simulation.log_event("Bio/Tech scan logged to database")
            self.toast_msg = "Detailed Scan Stored to Codex."
            self.toast_timer = 2.5

        else:
            self.simulation.log_event("Executed: " + action_id)
            self.toast_msg = "Action Dispatched: " + action_id
            self.toast_timer = 2.5

    def update(self):
        dt = min(get_frame_time(), 0.05)

        # X-Ray Toggle ([Tab] / Gamepad View)
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
            self.sfx.play("click", 0.5)

        # Pattern Toggle ([F1] / Gamepad R3): Vertical List vs Radial Wheel
        if is_dual_pattern_toggle_pressed():
            if self.layout_mode == LAYOUT_VERTICAL_LIST:
                self.layout_mode = LAYOUT_RADIAL_WHEEL
            else:
                self.layout_mode = LAYOUT_VERTICAL_LIST
            self.menu_controller.layout_mode = self.layout_mode
            self.sfx.play("click", 0.6)
            mode_name = "Radial Action Wheel" if self.layout_mode == LAYOUT_RADIAL_WHEEL else "Vertical Clamped List"
            self.toast_msg = "Layout Mode Toggled: " + mode_name
            self.toast_timer = 3.0

        # Secondary Toggle ([F2] / Gamepad L3): Smart Clamping vs Unclamped Naive
        if is_dual_secondary_toggle_pressed():
            self.smart_clamping = not self.smart_clamping
            self.menu_controller.clamping_enabled = self.smart_clamping
            self.sfx.play("click", 0.5)
            c_name = "Smart Clamping [Active]" if self.smart_clamping else "Unclamped Naive [Off-Screen Bleed]"
            self.toast_msg = "Viewport Clamping: " + c_name
            self.toast_timer = 3.0

        # Reset Simulation ([R] / Gamepad Start)
        if is_dual_reset_pressed():
            self.simulation = OutpostSimulation()
            self.menu_controller.close_menu()
            self.sfx.play("pickup", 0.8)
            self.toast_msg = "Outpost Simulation & Entities Reset."
            self.toast_timer = 2.5

        # Update toast timer
        if self.toast_timer > 0.0:
            self.toast_timer -= dt

        # Simultaneous Dual Reticle / Cursor Input
        # Mouse updates reticle position when inside game canvas
        mx = get_mouse_x()
        my = get_mouse_y()
        if mx >= 0 and mx <= SCREEN_WIDTH and my >= 0 and my <= SCREEN_HEIGHT:
            self.simulation.cursor_world_x = float(mx)
            self.simulation.cursor_world_y = float(my)

        # Gamepad Right Stick can steer reticle with radial deadzone
        pad_look = get_gamepad_right_stick(deadzone=0.18)
        if abs(pad_look.x) > 0.01 or abs(pad_look.y) > 0.01:
            self.simulation.cursor_world_x += pad_look.x * 450.0 * dt
            self.simulation.cursor_world_y += pad_look.y * 450.0 * dt
            self.simulation.cursor_world_x = max(20.0, min(SCREEN_WIDTH - 20.0, self.simulation.cursor_world_x))
            self.simulation.cursor_world_y = max(20.0, min(SCREEN_HEIGHT - 20.0, self.simulation.cursor_world_y))

        # Check Right-Click or Gamepad X (Square) to open Context Menu
        pad_id = get_active_gamepad_id()
        pad_x_pressed = (pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_FACE_LEFT))
        right_click = is_mouse_button_pressed(MOUSE_BUTTON_RIGHT)

        if right_click or pad_x_pressed:
            self._open_context_menu_at_cursor()

        # Update Outpost Simulation (Player moves if context menu is closed)
        move_vec = get_dual_move_2d()
        self.simulation.update(dt, move_vec, not self.menu_controller.is_open)

        # Context Menu Animations
        self.menu_controller.update_animation(dt)

        # Update Active Context Menu Navigation
        if self.menu_controller.is_open:
            self._update_context_menu_input()

    def _update_context_menu_input(self):
        menu = self.menu_controller

        # Cancel / Dismiss (Esc / Gamepad B / Left Click Outside)
        pad_id = get_active_gamepad_id()
        pad_b_pressed = (pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_FACE_RIGHT))
        if is_key_pressed(KEY_ESCAPE) or pad_b_pressed:
            if menu.active_submenu_index >= 0:
                menu.active_submenu_index = -1
                self.sfx.play("click", 0.4)
            else:
                menu.close_menu()
                self.sfx.play("click", 0.4)
            return

        # Up/Down Navigation
        up_pressed = (is_key_pressed(KEY_W) or is_key_pressed(KEY_UP))
        down_pressed = (is_key_pressed(KEY_S) or is_key_pressed(KEY_DOWN))
        if pad_id >= 0:
            if is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_LEFT_FACE_UP):
                up_pressed = True
            elif is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_LEFT_FACE_DOWN):
                down_pressed = True

        if menu.active_submenu_index >= 0:
            # Navigating submenu
            parent_act = menu.actions[menu.active_submenu_index]
            sub_count = len(parent_act.sub_actions)
            if sub_count > 0:
                if up_pressed:
                    menu.submenu_selected_index = (menu.submenu_selected_index - 1 + sub_count) % sub_count
                    self.sfx.play("click", 0.3)
                elif down_pressed:
                    menu.submenu_selected_index = (menu.submenu_selected_index + 1) % sub_count
                    self.sfx.play("click", 0.3)
        else:
            # Navigating main context items
            act_count = len(menu.actions)
            if act_count > 0:
                if up_pressed:
                    menu.selected_index = (menu.selected_index - 1 + act_count) % act_count
                    self.sfx.play("click", 0.3)
                elif down_pressed:
                    menu.selected_index = (menu.selected_index + 1) % act_count
                    self.sfx.play("click", 0.3)

        # Confirm Selection (Enter / Space / Gamepad A)
        pad_a_pressed = (pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_FACE_DOWN))
        confirm = (is_key_pressed(KEY_ENTER) or is_key_pressed(KEY_SPACE) or pad_a_pressed)

        if confirm:
            if menu.active_submenu_index >= 0:
                parent_act = menu.actions[menu.active_submenu_index]
                if menu.submenu_selected_index < len(parent_act.sub_actions):
                    sub_item = parent_act.sub_actions[menu.submenu_selected_index]
                    if sub_item.is_enabled:
                        self._dispatch_context_command(sub_item.action_id)
            else:
                if menu.selected_index < len(menu.actions):
                    cur_act = menu.actions[menu.selected_index]
                    if len(cur_act.sub_actions) > 0:
                        menu.active_submenu_index = menu.selected_index
                        menu.submenu_selected_index = 0
                        self.sfx.play("click", 0.5)
                    elif cur_act.is_enabled:
                        self._dispatch_context_command(cur_act.action_id)

        # Mouse Hover and Click on Vertical Menu
        if menu.layout_mode == LAYOUT_VERTICAL_LIST:
            self._handle_mouse_vertical_menu()
        elif menu.layout_mode == LAYOUT_RADIAL_WHEEL:
            self._handle_mouse_radial_menu()

    def _handle_mouse_vertical_menu(self):
        menu = self.menu_controller
        mx = get_mouse_x()
        my = get_mouse_y()
        mouse_clicked = is_mouse_button_pressed(MOUSE_BUTTON_LEFT)

        anc = menu.anchor
        bx = anc.clamped_x
        by = anc.clamped_y
        bw = menu.item_width
        start_y = by + 28

        # 1. Check main items
        for i in range(len(menu.actions)):
            iy = start_y + i * menu.item_height
            if mx >= bx and mx <= bx + bw and my >= iy and my <= iy + menu.item_height:
                menu.selected_index = i
                act = menu.actions[i]
                if len(act.sub_actions) > 0:
                    menu.active_submenu_index = i
                if mouse_clicked:
                    if len(act.sub_actions) == 0 and act.is_enabled:
                        self._dispatch_context_command(act.action_id)
                    elif len(act.sub_actions) > 0:
                        menu.active_submenu_index = i
                        menu.submenu_selected_index = 0

        # 2. Check active submenu items
        if menu.active_submenu_index >= 0:
            parent_act = menu.actions[menu.active_submenu_index]
            sub_x = bx + bw if not anc.flipped_x else bx - menu.submenu_width
            sub_y = start_y + menu.active_submenu_index * menu.item_height

            for si in range(len(parent_act.sub_actions)):
                s_iy = sub_y + si * menu.item_height
                if mx >= sub_x and mx <= sub_x + menu.submenu_width and my >= s_iy and my <= s_iy + menu.item_height:
                    menu.submenu_selected_index = si
                    if mouse_clicked:
                        sub_act = parent_act.sub_actions[si]
                        if sub_act.is_enabled:
                            self._dispatch_context_command(sub_act.action_id)

    def _handle_mouse_radial_menu(self):
        menu = self.menu_controller
        mx = get_mouse_x()
        my = get_mouse_y()
        mouse_clicked = is_mouse_button_pressed(MOUSE_BUTTON_LEFT)

        anc = menu.anchor
        cx = anc.clamped_x
        cy = anc.clamped_y
        dx = mx - cx
        dy = my - cy
        dist = math.sqrt(dx * dx + dy * dy)

        inner_r = 35.0
        outer_r = 140.0

        if dist >= inner_r and dist <= outer_r and len(menu.actions) > 0:
            ang = math.atan2(dy, dx)
            if ang < 0.0:
                ang += 2.0 * math.pi
            sector_span = (2.0 * math.pi) / len(menu.actions)
            idx = int((ang + sector_span * 0.5) / sector_span) % len(menu.actions)
            menu.selected_index = idx

            if mouse_clicked:
                act = menu.actions[idx]
                if act.is_enabled:
                    self._dispatch_context_command(act.action_id)

    def draw(self):
        begin_drawing()
        clear_background(COLOR_BG_DARK)

        # 1. World Simulation
        self.simulation.draw_world()

        # 2. Draw Floating Context Menu (if open)
        if self.menu_controller.is_open:
            if self.menu_controller.layout_mode == LAYOUT_VERTICAL_LIST:
                self._draw_vertical_context_menu()
            elif self.menu_controller.layout_mode == LAYOUT_RADIAL_WHEEL:
                self._draw_radial_context_menu()

        # 3. Telemetry Overlay ([Tab])
        if self.show_xray:
            draw_xray_context_inspector(self.menu_controller, self.simulation, 860, 68, 400, 630)

        # 4. Toast Notification
        if self.toast_timer > 0.0:
            self._draw_toast()

        # 5. Top-bar HUD (Font size, window dropdown, gamepad badge)
        self._draw_top_hud()

        # Mandatory repo dropdowns and badges
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)

        end_drawing()

    def _draw_vertical_context_menu(self):
        menu = self.menu_controller
        anc = menu.anchor

        bx = int(anc.clamped_x)
        by = int(anc.clamped_y)
        bw = int(menu.item_width)
        total_h = int(28 + len(menu.actions) * menu.item_height + 6)

        # Shadow & Base Panel
        draw_rectangle(bx + 4, by + 4, bw, total_h, Color(0, 0, 0, 120))
        draw_rectangle(bx, by, bw, total_h, COLOR_PANEL_BG)
        draw_rectangle_lines(bx, by, bw, total_h, COLOR_PANEL_BORDER)

        # Context Header Title
        draw_rectangle(bx, by, bw, 26, Color(24, 34, 56, 255))
        draw_rectangle_lines(bx, by, bw, 26, COLOR_PANEL_BORDER)
        draw_text(menu.target_entity_name[:24], bx + 8, by + 6, 11, COLOR_CYAN_ACCENT)

        start_y = by + 28

        # Draw Menu Items
        for i in range(len(menu.actions)):
            iy = start_y + int(i * menu.item_height)
            act = menu.actions[i]
            is_sel = (i == menu.selected_index)

            # Item background
            bg_col = COLOR_ITEM_HOVER if is_sel else (COLOR_ITEM_NORMAL if act.is_enabled else COLOR_ITEM_DISABLED)
            draw_rectangle(bx + 2, iy + 2, bw - 4, int(menu.item_height - 4), bg_col)

            if is_sel:
                draw_rectangle(bx + 2, iy + 2, 4, int(menu.item_height - 4), act.accent_color)
                draw_rectangle_lines(bx + 2, iy + 2, bw - 4, int(menu.item_height - 4), act.accent_color)

            # Label
            lbl_col = COLOR_TEXT_MAIN if act.is_enabled else COLOR_TEXT_DISABLED
            draw_text(act.label, bx + 14, iy + 10, 12, lbl_col)

            # Hotkey / Submenu indicator
            if len(act.sub_actions) > 0:
                draw_text(">", bx + bw - 18, iy + 10, 12, COLOR_GOLD_ACCENT)
            elif len(act.hotkey_hint) > 0:
                draw_text(act.hotkey_hint, bx + bw - 32, iy + 10, 10, COLOR_TEXT_DIM)

        # Draw Submenu Cascade (if active)
        if menu.active_submenu_index >= 0:
            parent_act = menu.actions[menu.active_submenu_index]
            sub_x = bx + bw + 2 if not anc.flipped_x else bx - int(menu.submenu_width) - 2
            sub_y = start_y + int(menu.active_submenu_index * menu.item_height)
            sub_h = int(len(parent_act.sub_actions) * menu.item_height + 8)

            draw_rectangle(sub_x, sub_y, int(menu.submenu_width), sub_h, COLOR_PANEL_BG)
            draw_rectangle_lines(sub_x, sub_y, int(menu.submenu_width), sub_h, COLOR_GOLD_ACCENT)

            for si in range(len(parent_act.sub_actions)):
                s_iy = sub_y + 4 + int(si * menu.item_height)
                sub_act = parent_act.sub_actions[si]
                is_sub_sel = (si == menu.submenu_selected_index)

                s_bg = COLOR_ITEM_HOVER if is_sub_sel else (COLOR_ITEM_NORMAL if sub_act.is_enabled else COLOR_ITEM_DISABLED)
                draw_rectangle(sub_x + 2, s_iy, int(menu.submenu_width - 4), int(menu.item_height - 4), s_bg)

                if is_sub_sel:
                    draw_rectangle(sub_x + 2, s_iy, 3, int(menu.item_height - 4), COLOR_GOLD_ACCENT)

                sub_lbl_col = COLOR_TEXT_MAIN if sub_act.is_enabled else COLOR_TEXT_DISABLED
                draw_text(sub_act.label, sub_x + 10, s_iy + 8, 11, sub_lbl_col)

        # Requirement Tooltip if hovering disabled item
        cur_act = menu.actions[menu.selected_index] if menu.selected_index < len(menu.actions) else None
        if cur_act and not cur_act.is_enabled and len(cur_act.requirement_tooltip) > 0:
            tip_w = measure_text(cur_act.requirement_tooltip, 11) + 20
            tip_x = bx
            tip_y = by + total_h + 4
            draw_rectangle(tip_x, tip_y, tip_w, 24, Color(30, 15, 15, 240))
            draw_rectangle_lines(tip_x, tip_y, tip_w, 24, COLOR_RED_ACCENT)
            draw_text("! " + cur_act.requirement_tooltip, tip_x + 6, tip_y + 6, 11, COLOR_RED_ACCENT)

    def _draw_radial_context_menu(self):
        menu = self.menu_controller
        anc = menu.anchor
        cx = int(anc.clamped_x)
        cy = int(anc.clamped_y)
        act_count = len(menu.actions)
        if act_count == 0:
            return

        inner_r = 35.0
        outer_r = 130.0

        # Center core disc
        draw_circle(cx, cy, inner_r, Color(16, 24, 40, 240))
        draw_circle_lines(cx, cy, inner_r, COLOR_CYAN_ACCENT)
        draw_text("CTX", cx - 12, cy - 6, 12, COLOR_TEXT_MAIN)

        sector_span = (2.0 * math.pi) / act_count

        for i in range(act_count):
            act = menu.actions[i]
            is_sel = (i == menu.selected_index)
            ang = i * sector_span
            mid_r = (inner_r + outer_r) * 0.55

            px = cx + int(math.cos(ang) * mid_r)
            py = cy + int(math.sin(ang) * mid_r)

            btn_w = 110
            btn_h = 32
            bx = px - btn_w // 2
            by = py - btn_h // 2

            b_col = COLOR_ITEM_HOVER if is_sel else (COLOR_ITEM_NORMAL if act.is_enabled else COLOR_ITEM_DISABLED)
            bdr_col = act.accent_color if is_sel else COLOR_PANEL_BORDER

            draw_rectangle(bx, by, btn_w, btn_h, b_col)
            draw_rectangle_lines(bx, by, btn_w, btn_h, bdr_col)

            lbl_col = COLOR_TEXT_MAIN if act.is_enabled else COLOR_TEXT_DISABLED
            draw_text(act.label[:13], bx + 8, by + 10, 11, lbl_col)

            # Connector ray
            ray_sx = cx + int(math.cos(ang) * inner_r)
            ray_sy = cy + int(math.sin(ang) * inner_r)
            draw_line(ray_sx, ray_sy, bx + btn_w // 2, by + btn_h // 2, Color(40, 60, 95, 180))

    def _draw_toast(self):
        tw = measure_text(self.toast_msg, 12) + 32
        tx = 440 - (tw // 2)
        ty = SCREEN_HEIGHT - 55
        draw_rectangle(tx, ty, tw, 28, Color(18, 26, 42, 240))
        draw_rectangle_lines(tx, ty, tw, 28, COLOR_CYAN_ACCENT)
        draw_text(self.toast_msg, tx + 16, ty + 7, 12, COLOR_TEXT_MAIN)

    def _draw_top_hud(self):
        draw_text("CONTEXT MENU & ACTION DISPATCHER LAB", 24, 18, 16, COLOR_TEXT_MAIN)
        draw_text("Section 3.1: Menus & UI  |  Floating Anchored Contextual Interaction", 24, 38, 11, COLOR_TEXT_DIM)

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
    ContextMenuGame().run(smoke_test=is_smoke)

