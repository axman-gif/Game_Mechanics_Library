# -*- coding: utf-8 -*-
"""
Title Screen Cursor - Vertical Menu with Cursor Navigation & Command Dispatch
=============================================================================
Section          : 3.1 Menus & UI
Pattern Category : Menus & User Interface, Decoupling (Command Pattern)
Dimension        : 2D

Problem Solved:
  Hardcoding menu navigation directly into game loops with ad-hoc if/else ladders
  leads to state desynchronization, lack of wrap-around bounds checking, missing
  gamepad auto-repeat timers, and tightly coupling menu button presses to immediate
  gameplay logic rather than dispatching decoupled Command tokens.

How the Pattern Works:
  1. Menu Navigation Model: An explicit array of MenuItem structs holding labels,
     action IDs, and enabled states. Navigation updates selected_index using mathematical
     modulo wrap-around (idx = (idx + delta) % N) or clamped boundaries.
  2. Cursor Rig & Damped Interpolation: The cursor Y coordinate smoothly pursues
     the target item Y coordinate via framerate-independent spring damping (damp),
     giving crisp, responsive arcade feel with pulsing procedural chevron primitives.
  3. Decoupled Action Dispatcher (Command Pattern): Confirming an item produces
     a discrete Action Event with parameters, notifying subscriber systems without
     the menu needing to know game scene internals.

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - Up/Down / W/S / Left Stick / D-Pad : Navigate vertical menu options
  - Enter / Space / Gamepad A (Cross)  : Confirm / Dispatch selected command
  - Mouse Hover & Left Click           : Select and confirm items directly with mouse
  - [Tab] / Gamepad View (Select)      : Toggle X-Ray Telemetry & Math Inspector Overlay
  - [F1]  / Gamepad LB                 : Toggle Navigation Mode: [Wrap-Around (% N)] vs [Clamp (0..N-1)]
  - [F2]  / Gamepad RB                 : Toggle Cursor Rig: [Spring Damped Cursor] vs [Rigid Snap]
  - [Ctrl +/-]                         : Increase / Decrease UI Font Size
  - [F11]                              : Toggle Fullscreen
  - [R]   / Gamepad Start              : Reset Menu State & Dispatch Log
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
WINDOW_TITLE = "Title Screen Cursor - Vertical Menu (Raylib Pattern Lab)"

# Menu Theme Palette
COLOR_BG_DARK          = Color(10, 13, 22, 255)
COLOR_PANEL_BG         = Color(16, 22, 36, 240)
COLOR_PANEL_BORDER     = Color(40, 60, 95, 255)
COLOR_ITEM_NORMAL      = Color(180, 205, 235, 255)
COLOR_ITEM_HOVER       = Color(255, 255, 255, 255)
COLOR_ITEM_DISABLED    = Color(90, 105, 130, 255)
COLOR_CURSOR_CYAN      = Color(0, 225, 255, 255)
COLOR_CURSOR_GLOW      = Color(0, 225, 255, 35)
COLOR_ACCENT_GOLD      = Color(255, 200, 60, 255)

# Action Command Constants (C++ Enum equivalent)
ACTION_START_MISSION   = 0
ACTION_DIFFICULTY      = 1
ACTION_AUDIO_TOGGLE    = 2
ACTION_GRAPHICS_MODE   = 3
ACTION_DIAGNOSTICS     = 4
ACTION_ABORT_RUN       = 5

ACTION_NAMES = {
    ACTION_START_MISSION: "START_MISSION",
    ACTION_DIFFICULTY:    "CYCLE_DIFFICULTY",
    ACTION_AUDIO_TOGGLE:  "TOGGLE_AUDIO",
    ACTION_GRAPHICS_MODE: "CYCLE_GRAPHICS",
    ACTION_DIAGNOSTICS:   "RUN_DIAGNOSTICS",
    ACTION_ABORT_RUN:     "ABORT_RUN"
}

# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATION
# ==============================================================================

class MenuItem:
    """
    Data model representing a single navigable option.
    C++ Equivalent:
      struct MenuItem {
          std::string label;
          int action_id;
          std::string description;
          std::string value_text;
          bool is_enabled;
      };
    """
    def __init__(self, label: str, action_id: int, description: str, value_text: str = "", is_enabled: bool = True):
        self.label = label
        self.action_id = action_id
        self.description = description
        self.value_text = value_text
        self.is_enabled = is_enabled


class MenuNavigationModel:
    """
    Manages selection index state, bounds math, and option collections.
    Demonstrates modulo wrap-around vs hard boundary clamping.
    """
    def __init__(self):
        self.items = []
        self.selected_index = 0
        self.wrap_around_enabled = True   # [F1] Toggle
        self.total_movements = 0
        self.wraps_triggered = 0

    def add_item(self, label: str, action_id: int, description: str, value_text: str = "", is_enabled: bool = True):
        self.items.append(MenuItem(label, action_id, description, value_text, is_enabled))

    def move_selection(self, delta: int) -> bool:
        """
        Moves the cursor by delta (+1 down, -1 up).
        Returns True if selection index actually changed (to trigger audio blips).
        """
        if not self.items:
            return False

        n = len(self.items)
        prev_idx = self.selected_index

        if self.wrap_around_enabled:
            # Mathematical Modulo Wrap-Around:
            # In Python (-1 % 5) == 4 automatically.
            # In C++: ((idx + delta) % n + n) % n ensures non-negative results.
            new_idx = ((self.selected_index + delta) % n + n) % n
            if (delta > 0 and new_idx < prev_idx) or (delta < 0 and new_idx > prev_idx):
                self.wraps_triggered += 1
            self.selected_index = new_idx
        else:
            # Hard Boundary Clamping
            self.selected_index = max(0, min(n - 1, self.selected_index + delta))

        if self.selected_index != prev_idx:
            self.total_movements += 1
            return True
        return False

    def get_selected_item(self) -> MenuItem:
        if 0 <= self.selected_index < len(self.items):
            return self.items[self.selected_index]
        return None


class CursorRig2D:
    """
    Animates the menu cursor with spring damping and pulsing visual chevrons.
    """
    def __init__(self):
        self.current_y = 200.0
        self.target_y = 200.0
        self.current_width = 380.0
        self.target_width = 380.0
        self.smoothing = 18.0              # Damping speed
        self.anim_timer = 0.0
        self.is_damped = True              # [F2] Toggle: Spring Damped vs Rigid Snap

    def update(self, target_y: float, target_w: float, dt: float):
        self.anim_timer += dt
        self.target_y = target_y
        self.target_width = target_w

        if self.is_damped:
            self.current_y = damp(self.current_y, self.target_y, self.smoothing, dt)
            self.current_width = damp(self.current_width, self.target_width, self.smoothing, dt)
        else:
            self.current_y = self.target_y
            self.current_width = self.target_width

    def draw(self, x: float, height: float):
        """Renders the animated sci-fi cursor brackets and pulsing chevron."""
        pulse = 0.5 + 0.5 * math.sin(self.anim_timer * 8.0)
        chevron_offset = math.sin(self.anim_timer * 6.0) * 3.0

        cy = int(self.current_y)
        cw = int(self.current_width)
        ch = int(height)
        cx = int(x)

        # 1. Subtle selection highlight pill behind item
        draw_rectangle(cx, cy, cw, ch, Color(0, 220, 255, int(20 + 15 * pulse)))
        draw_rectangle_lines(cx, cy, cw, ch, Color(0, 220, 255, int(120 + 80 * pulse)))

        # 2. Left Chevron Indicator (Triangle pointing right)
        tip_x = cx - 14 + chevron_offset
        p_top = Vector2(tip_x - 10, cy + ch * 0.25)
        p_tip = Vector2(tip_x, cy + ch * 0.5)
        p_bot = Vector2(tip_x - 10, cy + ch * 0.75)
        draw_triangle(p_top, p_bot, p_tip, COLOR_CURSOR_CYAN)

        # 3. Right Bracket
        draw_line(cx + cw + 8, cy + 4, cx + cw + 14, cy + 4, COLOR_CURSOR_CYAN)
        draw_line(cx + cw + 14, cy + 4, cx + cw + 14, cy + ch - 4, COLOR_CURSOR_CYAN)
        draw_line(cx + cw + 8, cy + ch - 4, cx + cw + 14, cy + ch - 4, COLOR_CURSOR_CYAN)


class ActionDispatcher:
    """
    Decoupled Command Receiver logging dispatched actions and game state alterations.
    """
    def __init__(self):
        self.history = []
        self.difficulty_names = ["EASY (RECON)", "NORMAL (COMBAT)", "HARD (NIGHTMARE)"]
        self.difficulty_idx = 1
        self.audio_enabled = True
        self.graphics_names = ["RETRO CRT", "HD SHARP", "CYBER NEON"]
        self.graphics_idx = 1
        self.diagnostics_run_count = 0

    def dispatch(self, action_id: int, sfx: SoundLibrary):
        """Executes the action and logs event."""
        log_entry = ""
        if action_id == ACTION_START_MISSION:
            log_entry = f"MISSION LAUNCHED! Diff: {self.difficulty_names[self.difficulty_idx]}"
            sfx.play("powerup", 0.75)
        elif action_id == ACTION_DIFFICULTY:
            self.difficulty_idx = (self.difficulty_idx + 1) % len(self.difficulty_names)
            log_entry = f"DIFFICULTY SET TO: {self.difficulty_names[self.difficulty_idx]}"
            sfx.play("click", 0.65)
        elif action_id == ACTION_AUDIO_TOGGLE:
            self.audio_enabled = not self.audio_enabled
            log_entry = f"AUDIO SYSTEM: {'ENABLED' if self.audio_enabled else 'MUTED'}"
            sfx.play("coin", 0.65)
        elif action_id == ACTION_GRAPHICS_MODE:
            self.graphics_idx = (self.graphics_idx + 1) % len(self.graphics_names)
            log_entry = f"GRAPHICS PIPELINE: {self.graphics_names[self.graphics_idx]}"
            sfx.play("click", 0.65)
        elif action_id == ACTION_DIAGNOSTICS:
            self.diagnostics_run_count += 1
            log_entry = f"DIAGNOSTIC TEST #{self.diagnostics_run_count} PASSED (0 ERRORS)"
            sfx.play("jump", 0.65)
        elif action_id == ACTION_ABORT_RUN:
            log_entry = "SIMULATION REBOOT INITIATED"
            sfx.play("hurt", 0.65)

        self.history.insert(0, log_entry)
        if len(self.history) > 8:
            self.history.pop()


# ==============================================================================
# BLOCK 2: WORLD SIMULATION & ENTITIES
# ==============================================================================

class TitleScreenCursorGame:
    """Interactive Title Screen Cursor sandbox and telemetry lab."""

    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()

        self.sfx = SoundLibrary()
        self.sfx.init_defaults()

        # Core Pattern Components
        self.menu = MenuNavigationModel()
        self.cursor = CursorRig2D()
        self.dispatcher = ActionDispatcher()

        # Build Menu Options
        self.menu.add_item("START MISSION", ACTION_START_MISSION, "Initiate defense simulation sortie against aerial drone wave")
        self.menu.add_item("DIFFICULTY LEVEL", ACTION_DIFFICULTY, "Toggle combat parameters, AI aggression, and spawn budgets", "NORMAL")
        self.menu.add_item("AUDIO ENGINE", ACTION_AUDIO_TOGGLE, "Toggle procedural synthesizer sound playback", "ENABLED")
        self.menu.add_item("GRAPHICS PROFILE", ACTION_GRAPHICS_MODE, "Cycle between rendering post-process aesthetics", "HD SHARP")
        self.menu.add_item("SYSTEM DIAGNOSTICS", ACTION_DIAGNOSTICS, "Verify internal bus communication and memory pools")
        self.menu.add_item("ABORT OPERATION", ACTION_ABORT_RUN, "Reboot menu session to default parameters")

        # Layout Geometry
        self.menu_x = 220
        self.menu_y = 190
        self.item_height = 54
        self.item_gap = 14
        self.item_width = 410

        # Input repeat cooldown (prevents runaway scrolling on analog sticks)
        self.repeat_timer = 0.0
        self.initial_delay = 0.28
        self.repeat_tick = 0.11

        # Interactive Toggles
        self.show_xray = True

    def update(self):
        dt = min(get_frame_time(), 0.05)

        # 1. Global Pattern Toggles
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
            self.sfx.play("click", 0.6)

        if is_dual_pattern_toggle_pressed():
            self.menu.wrap_around_enabled = not self.menu.wrap_around_enabled
            self.sfx.play("coin", 0.65)

        if is_dual_secondary_toggle_pressed():
            self.cursor.is_damped = not self.cursor.is_damped
            self.sfx.play("click", 0.6)

        if is_dual_reset_pressed():
            self.menu.selected_index = 0
            self.menu.total_movements = 0
            self.menu.wraps_triggered = 0
            self.dispatcher.history.clear()
            self.sfx.play("powerup", 0.7)

        # 2. Analog Stick & Keyboard Menu Navigation with Auto-Repeat
        pad_move = get_dual_move_2d(deadzone=0.25, use_arrow_keys=True)
        nav_delta = 0

        # Check discrete single-frame button presses
        if is_key_pressed(KEY_UP) or is_key_pressed(KEY_W):
            nav_delta = -1
        elif is_key_pressed(KEY_DOWN) or is_key_pressed(KEY_S):
            nav_delta = 1

        pad_id = get_active_gamepad_id()
        if pad_id >= 0:
            if is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_LEFT_FACE_UP):
                nav_delta = -1
            elif is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_LEFT_FACE_DOWN):
                nav_delta = 1

        # Check sustained analog deflection with auto-repeat timing
        if abs(pad_move.y) > 0.45:
            if self.repeat_timer <= 0.0:
                nav_delta = 1 if pad_move.y > 0 else -1
                self.repeat_timer = self.initial_delay
            else:
                self.repeat_timer -= dt
                if self.repeat_timer <= self.initial_delay - self.repeat_tick:
                    nav_delta = 1 if pad_move.y > 0 else -1
                    self.repeat_timer = self.initial_delay
        else:
            self.repeat_timer = 0.0

        # Mouse wheel support
        wheel = get_mouse_wheel_move()
        if wheel < 0:
            nav_delta = 1
        elif wheel > 0:
            nav_delta = -1

        # Apply movement
        if nav_delta != 0:
            if self.menu.move_selection(nav_delta):
                self.sfx.play("click", 0.5)

        # Mouse Hover selection over menu items
        mx, my = get_mouse_x(), get_mouse_y()
        for idx in range(len(self.menu.items)):
            iy = self.menu_y + idx * (self.item_height + self.item_gap)
            if (self.menu_x <= mx <= self.menu_x + self.item_width) and (iy <= my <= iy + self.item_height):
                if self.menu.selected_index != idx:
                    self.menu.selected_index = idx
                    self.menu.total_movements += 1
                    self.sfx.play("click", 0.4)
                # Direct mouse click confirmation
                if is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
                    item = self.menu.get_selected_item()
                    if item and item.is_enabled:
                        self.dispatcher.dispatch(item.action_id, self.sfx)
                break

        # Confirm / Dispatch selection (Keyboard / Gamepad)
        if is_dual_primary_fire_pressed() or is_key_pressed(KEY_ENTER) or is_key_pressed(KEY_SPACE):
            item = self.menu.get_selected_item()
            if item and item.is_enabled:
                self.dispatcher.dispatch(item.action_id, self.sfx)

        # 3. Synchronize Dynamic Option Value Labels
        self.menu.items[1].value_text = self.dispatcher.difficulty_names[self.dispatcher.difficulty_idx].split()[0]
        self.menu.items[2].value_text = "ON" if self.dispatcher.audio_enabled else "MUTED"
        self.menu.items[3].value_text = self.dispatcher.graphics_names[self.dispatcher.graphics_idx]

        # 4. Update Cursor Rig Position
        target_y = self.menu_y + self.menu.selected_index * (self.item_height + self.item_gap)
        self.cursor.update(target_y, self.item_width, dt)

    # ==========================================================================
    # BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY ([Tab], [F1], [F2])
    # ==========================================================================
    def draw_xray_overlay(self):
        """Visualizes the underlying array, modulo wrap math, and cursor damping error."""
        panel_x = 730
        panel_y = 110
        panel_w = 510
        panel_h = 540

        draw_rectangle(panel_x, panel_y, panel_w, panel_h, Color(14, 18, 30, 240))
        draw_rectangle_lines(panel_x, panel_y, panel_w, panel_h, Color(45, 75, 120, 255))

        draw_text("X-RAY TELEMETRY & CURSOR INTERNALS [Tab]", panel_x + 16, panel_y + 14, 15, COLOR_CURSOR_CYAN)
        draw_line(panel_x + 16, panel_y + 36, panel_x + panel_w - 16, panel_y + 36, Color(45, 75, 120, 255))

        y = panel_y + 46
        # Pattern 1 Mode (Wrap-around vs Clamp)
        wrap_col = Color(80, 255, 140, 255) if self.menu.wrap_around_enabled else Color(255, 120, 120, 255)
        wrap_mode = "MODULO WRAP-AROUND (% N)" if self.menu.wrap_around_enabled else "CLAMPED BOUNDS (0..N-1)"
        draw_text(f"[F1] Boundary Math: {wrap_mode}", panel_x + 16, y, 13, wrap_col)
        y += 18
        if self.menu.wrap_around_enabled:
            draw_text(" * Equation: idx = ((idx + delta) % N + N) % N", panel_x + 16, y, 11, Color(170, 200, 235, 255))
            y += 15
            draw_text(" * Top wraps to Bottom and vice-versa seamlessly", panel_x + 16, y, 11, Color(170, 200, 235, 255))
        else:
            draw_text(" * Equation: idx = clamp(idx + delta, 0, N - 1)", panel_x + 16, y, 11, Color(245, 180, 180, 255))
            y += 15
            draw_text(" * Cursor hard-stops at first and last options", panel_x + 16, y, 11, Color(245, 180, 180, 255))

        # Pattern 2 Mode (Cursor Damping)
        y += 22
        damp_col = Color(80, 255, 140, 255) if self.cursor.is_damped else Color(255, 120, 120, 255)
        damp_mode = "SPRING DAMPED (EXPONENTIAL LERP)" if self.cursor.is_damped else "RIGID SNAP (ZERO DAMPING)"
        draw_text(f"[F2] Cursor Rig: {damp_mode}", panel_x + 16, y, 13, damp_col)
        y += 18
        error_px = abs(self.cursor.current_y - self.cursor.target_y)
        draw_text(f" * Target Y: {self.cursor.target_y:.1f}px | Current Y: {self.cursor.current_y:.1f}px", panel_x + 16, y, 11, Color(170, 200, 235, 255))
        y += 15
        draw_text(f" * Damping Lag / Error: {error_px:.2f}px (Smooth pursuit curve)", panel_x + 16, y, 11, Color(170, 200, 235, 255))

        # Array Memory Map
        y += 24
        draw_text("ARRAY SLOTS & SELECTION INDEX:", panel_x + 16, y, 13, COLOR_ACCENT_GOLD)
        y += 18
        for i, item in enumerate(self.menu.items):
            is_active = (i == self.menu.selected_index)
            slot_bg = Color(24, 45, 75, 255) if is_active else Color(18, 24, 38, 255)
            draw_rectangle(panel_x + 16, y, panel_w - 32, 22, slot_bg)
            if is_active:
                draw_rectangle_lines(panel_x + 16, y, panel_w - 32, 22, COLOR_CURSOR_CYAN)

            prefix = ">> [SEL]" if is_active else "   [   ]"
            txt_col = Color(0, 225, 255, 255) if is_active else Color(160, 185, 215, 255)
            draw_text(f"{prefix} [{i}] {item.label}", panel_x + 22, y + 4, 11, txt_col)
            draw_text(f"Cmd: #{item.action_id} {ACTION_NAMES.get(item.action_id, '')}", panel_x + panel_w - 190, y + 4, 11, txt_col)
            y += 24

        # Decoupled Action Dispatch History (Command Pattern Log)
        y += 12
        draw_text("DISPATCHED ACTION EVENT QUEUE:", panel_x + 16, y, 13, COLOR_ACCENT_GOLD)
        y += 18
        if not self.dispatcher.history:
            draw_text("(Press [Enter / Space / Gamepad A] to dispatch actions)", panel_x + 20, y, 11, Color(120, 140, 170, 255))
        else:
            for log in self.dispatcher.history[:6]:
                draw_text(f"> {log}", panel_x + 20, y, 11, Color(100, 235, 160, 255))
                y += 16

    # ==========================================================================
    # BLOCK 4: MAIN GAME LOOP & AUTOMATED SMOKE TEST
    # ==========================================================================
    def draw(self):
        begin_drawing()
        clear_background(COLOR_BG_DARK)

        # Subtle background grid & decorative cyber borders
        for gy in range(0, SCREEN_HEIGHT, 40):
            draw_line(0, gy, SCREEN_WIDTH, gy, Color(18, 24, 36, 120))
        for gx in range(0, SCREEN_WIDTH, 40):
            draw_line(gx, 0, gx, SCREEN_HEIGHT, Color(18, 24, 36, 120))

        # Title Screen Header
        draw_rectangle(0, 0, SCREEN_WIDTH, 70, Color(12, 16, 26, 240))
        draw_line(0, 70, SCREEN_WIDTH, 70, COLOR_PANEL_BORDER)
        draw_text("NEXUS CORE SYSTEM", 45, 18, 22, COLOR_CURSOR_CYAN)
        draw_text("Pattern: Vertical Menu with Modulo Wrap & Damped Cursor", 45, 44, 13, Color(140, 165, 200, 255))

        # Dropdowns and Badges
        draw_gamepad_status_badge(985, 24, 11)
        draw_ui_settings_bar(450, 18)

        # Menu Panel Container
        panel_pad = 20
        container_h = len(self.menu.items) * (self.item_height + self.item_gap) + panel_pad * 2 - self.item_gap
        draw_rectangle(self.menu_x - panel_pad, self.menu_y - panel_pad, self.item_width + panel_pad * 2, container_h, COLOR_PANEL_BG)
        draw_rectangle_lines(self.menu_x - panel_pad, self.menu_y - panel_pad, self.item_width + panel_pad * 2, container_h, COLOR_PANEL_BORDER)

        # Draw the animated cursor rig
        self.cursor.draw(self.menu_x, self.item_height)

        # Render Vertical Menu Items
        for idx, item in enumerate(self.menu.items):
            iy = self.menu_y + idx * (self.item_height + self.item_gap)
            is_sel = (idx == self.menu.selected_index)

            # Label text
            label_col = COLOR_ITEM_HOVER if is_sel else COLOR_ITEM_NORMAL
            font_sz = 17 if is_sel else 16
            draw_text(item.label, self.menu_x + 22, iy + 16, font_sz, label_col)

            # Value text badge on right side of button
            if item.value_text:
                val_col = COLOR_ACCENT_GOLD if is_sel else Color(130, 160, 200, 255)
                draw_text(f"[{item.value_text}]", self.menu_x + self.item_width - 120, iy + 17, 13, val_col)

        # Tooltip bar below menu
        cur_item = self.menu.get_selected_item()
        if cur_item:
            tip_y = self.menu_y + container_h + 10
            draw_rectangle(self.menu_x - panel_pad, tip_y, self.item_width + panel_pad * 2, 42, Color(12, 16, 26, 230))
            draw_rectangle_lines(self.menu_x - panel_pad, tip_y, self.item_width + panel_pad * 2, 42, COLOR_PANEL_BORDER)
            draw_text(f"INFO: {cur_item.description}", self.menu_x - 6, tip_y + 13, 12, Color(170, 210, 255, 255))

        # Mascot Avatar (reactive to selection)
        draw_humanoid_enemy_2d(
            Vector2(110.0, float(self.cursor.current_y + 24)),
            facing_angle_rad=0.0,
            anim_timer=get_time(),
            scale=1.2,
            is_attacking=is_dual_primary_fire_down()
        )

        # X-Ray Telemetry Overlay
        if self.show_xray:
            self.draw_xray_overlay()

        # Footer Bar with Controls
        draw_rectangle(0, SCREEN_HEIGHT - 44, SCREEN_WIDTH, 44, Color(12, 16, 26, 240))
        draw_line(0, SCREEN_HEIGHT - 44, SCREEN_WIDTH, SCREEN_HEIGHT - 44, COLOR_PANEL_BORDER)
        draw_text(
            "[Up/Down/WASD/L-Stick] Navigate   [Enter/A/Click] Confirm   [Tab] X-Ray   [F1] Wrap-Around   [F2] Damped Cursor   [R] Reset",
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
    TitleScreenCursorGame().run(smoke_test=is_smoke)

