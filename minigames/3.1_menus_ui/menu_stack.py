# -*- coding: utf-8 -*-
"""
Menu Stack - Push/Pop Modal Navigation Architecture
===================================================
Section          : 3.1 Menus & UI
Pattern Category : Menus & User Interface, State Management (Stack-Based FSM)
Dimension        : 2D

Problem Solved:
  Complex game menu hierarchies (Pause -> Options -> Audio / Graphics / Controls ->
  Confirmation Dialogs) often degenerate into an unmaintainable tangle of boolean flags
  (in_pause, in_options, in_audio, confirm_quit) and brittle conditional ladders.
  Submenu back-navigation breaks, cursor memory across parent screens is lost, and
  underlying UI components mistakenly receive inputs. The Menu Stack pattern (LIFO Stack
  of Menu Views / Command Nodes) treats the UI hierarchy as a formal push-down automaton:
  pushing a new menu pushes a state frame onto the stack; popping restores the exact parent
  state, cursor position, and breadcrumb path cleanly without coupling child views to parents.

How the Pattern Works:
  1. LIFO Stack Container (std::vector<MenuFrame> in C++):
     The stack holds active menu frames. Only the top frame receives user input and is drawn
     as the active interactive layer. Lower frames remain suspended underneath with their
     cursor indices and scroll positions preserved intact.
  2. Modal Dialog Interception:
     Destructive operations (e.g. 'Reset Defaults', 'Quit to Title') push a modal dialog frame
     onto the top of the stack. This intercepts all controller and keyboard inputs until the
     user explicitly confirms or cancels, after which the modal pops and resumes the parent.
  3. Dynamic Breadcrumb Trail:
     The stack hierarchy generates a breadcrumb path (e.g. 'PAUSE > OPTIONS > AUDIO') by
     iterating frames from index 0 to top. Clicking any breadcrumb pops down to that exact depth.
  4. Damped Visual Transition Rig:
     When frames are pushed or popped, the menu panel glides into view using exponential
     damping (damp), giving tactile visual weight without blocking immediate input response.

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - W / S / Up / Down / Left Stick / D-Pad : Navigate menu items / buttons
  - A / D / Left / Right / Left Stick     : Adjust sliders (volume, sensitivity) & steppers
  - Enter / Space / Gamepad A (Cross)     : Select option / Push submenu / Confirm
  - Esc / Backspace / Gamepad B (Circle)  : Pop one menu level / Close dialog
  - Mouse Left Click / Hover              : Direct point-and-click selection & breadcrumb jump
  - [Tab] / Gamepad View (Select)         : Toggle X-Ray LIFO Stack Telemetry Overlay
  - [F1]  / Gamepad R3                    : Toggle Architecture: [LIFO Menu Stack] vs [Flat Monolithic]
  - [F2]  / Gamepad L3                    : Toggle Motion: [Spring Damped Slide] vs [Instant Snap]
  - [Ctrl +/-]                            : Increase / Decrease UI Font Size
  - [F11]                                 : Toggle Fullscreen
  - [R]   / Gamepad Start                 : Reset Settings & Clear Stack to Root Pause
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
WINDOW_TITLE = "Menu Stack - Push/Pop Modal Navigation Architecture (Raylib Pattern Lab)"

# Color Palette (Dark Cyber-Industrial Aesthetic)
COLOR_BG_DARK           = Color(12, 16, 26, 255)
COLOR_PANEL_BG          = Color(18, 24, 40, 248)
COLOR_PANEL_BORDER      = Color(42, 65, 105, 255)
COLOR_ITEM_NORMAL       = Color(25, 35, 58, 255)
COLOR_ITEM_HOVER        = Color(38, 56, 92, 255)
COLOR_ITEM_BORDER       = Color(55, 82, 130, 255)
COLOR_ITEM_ACCENT       = Color(0, 220, 255, 255)
COLOR_TEXT_WHITE        = Color(235, 245, 255, 255)
COLOR_TEXT_MUTED        = Color(130, 155, 190, 255)
COLOR_TEXT_GOLD         = Color(255, 205, 55, 255)
COLOR_MODAL_SCRIM       = Color(5, 8, 14, 200)
COLOR_MODAL_BG          = Color(22, 28, 46, 255)
COLOR_MODAL_BORDER      = Color(255, 90, 90, 255)
COLOR_SLIDER_BG         = Color(28, 38, 62, 255)
COLOR_SLIDER_FILL       = Color(0, 200, 240, 255)

# Frame IDs (C++ Enum equivalent)
FRAME_PAUSE_ROOT        = 0
FRAME_OPTIONS_ROOT      = 1
FRAME_AUDIO_SETTINGS    = 2
FRAME_DISPLAY_SETTINGS  = 3
FRAME_GAMEPLAY_SETTINGS = 4
FRAME_CONFIRM_MODAL     = 5

# Control Types (C++ Enum equivalent)
ITEM_ACTION             = 0  # Executes a command or pushes a child frame
ITEM_SLIDER             = 1  # Continuous numeric slider (0.0 to 1.0)
ITEM_STEPPER            = 2  # Discrete choice carousel
ITEM_TOGGLE             = 3  # Binary ON/OFF switch

# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATION (MENU STACK ARCHITECTURE)
# ==============================================================================

class MenuItem:
    """
    Represents an interactive control element inside a MenuFrame.
    C++ Equivalent:
      struct MenuItem {
          int control_type;
          std::string label;
          std::string description;
          float slider_val;
          int step_index;
          std::vector<std::string> step_options;
          bool toggle_val;
          std::string action_id;
      };
    """
    def __init__(self, control_type: int, label: str, description: str, action_id: str = ""):
        self.control_type = control_type
        self.label = label
        self.description = description
        self.action_id = action_id
        self.slider_val = 0.5
        self.step_index = 0
        self.step_options = []
        self.toggle_val = True
        self.hover_anim = 0.0

    def set_slider(self, val: float):
        self.slider_val = max(0.0, min(1.0, val))

    def set_stepper(self, options, default_idx: int = 0):
        self.step_options = []
        for opt in options:
            self.step_options.append(opt)
        self.step_index = default_idx

    def set_toggle(self, val: bool):
        self.toggle_val = val


class MenuFrame:
    """
    A single modal/sub-view layer in the LIFO Menu Stack.
    C++ Equivalent:
      struct MenuFrame {
          int frame_id;
          std::string title;
          std::string breadcrumb;
          std::vector<MenuItem> items;
          int selected_index;
          float visual_offset_x;
          float alpha;
      };
    """
    def __init__(self, frame_id: int, title: str, breadcrumb: str):
        self.frame_id = frame_id
        self.title = title
        self.breadcrumb = breadcrumb
        self.items = []
        self.selected_index = 0
        self.visual_offset_x = 100.0  # Slide-in transition offset
        self.alpha = 0.0              # Fade-in opacity
        self.is_modal = False
        self.modal_message = ""
        self.modal_on_confirm_action = ""

    def add_item(self, item: MenuItem):
        self.items.append(item)

    def get_selected_item(self):
        if len(self.items) == 0:
            return None
        if self.selected_index < 0:
            self.selected_index = 0
        if self.selected_index >= len(self.items):
            self.selected_index = len(self.items) - 1
        return self.items[self.selected_index]


class MenuStack:
    """
    Core Push/Pop Modal State Machine.
    Manages a Last-In, First-Out (LIFO) stack of active menu frames.
    C++ Equivalent:
      class MenuStack {
      private:
          std::vector<MenuFrame> m_stack;
          std::vector<std::string> m_history_log;
      public:
          void push(const MenuFrame& frame);
          void pop();
          void pop_to_depth(int target_depth);
          void clear();
          MenuFrame* top();
          size_t depth() const;
      };
    """
    def __init__(self):
        self.stack = []
        self.history_log = []
        self.pop_count = 0
        self.push_count = 0
        self.damped_motion_enabled = True
        self.use_true_stack = True  # Pattern toggle: True = LIFO Stack, False = Flat Monolithic
        self.max_history = 8

    def push(self, frame: MenuFrame):
        """Pushes a new frame onto the stack, preserving previous frame underneath."""
        if not self.use_true_stack:
            # Monolithic fallback: discard entire history and replace top
            self.stack = []
        self.stack.append(frame)
        self.push_count += 1
        self._log_event("PUSH -> " + frame.breadcrumb)

    def pop(self) -> bool:
        """Pops the top frame. Returns True if a frame was removed, False if at root."""
        if len(self.stack) <= 1:
            return False
        popped = self.stack.pop()
        self.pop_count += 1
        self._log_event("POP <- " + popped.breadcrumb)
        return True

    def pop_to_depth(self, target_depth: int):
        """Pops frames until the stack reaches the target depth (for breadcrumb jump)."""
        while len(self.stack) > target_depth and len(self.stack) > 1:
            popped = self.stack.pop()
            self.pop_count += 1
            self._log_event("JUMP-POP <- " + popped.breadcrumb)

    def top(self):
        """Returns the active topmost frame."""
        if len(self.stack) == 0:
            return None
        return self.stack[len(self.stack) - 1]

    def depth(self) -> int:
        return len(self.stack)

    def clear(self):
        self.stack = []

    def _log_event(self, text: str):
        self.history_log.append(text)
        if len(self.history_log) > self.max_history:
            self.history_log.pop(0)


# ==============================================================================
# BLOCK 2: WORLD SIMULATION & ENTITIES (BACKGROUND LIVING GAMEPLAY)
# ==============================================================================

class AmbientStar:
    """Simple 2D scrolling starfield for background parallax."""
    def __init__(self, x: float, y: float, speed: float, radius: float):
        self.x = x
        self.y = y
        self.speed = speed
        self.radius = radius
        self.brightness = random.uniform(140, 255)


class LivingWorldSimulation:
    """
    Provides an active, animated 2D space hangar simulation in the background.
    Learners can observe the live game pausing or running in the backdrop.
    """
    def __init__(self):
        self.player_x = 240.0
        self.player_y = 360.0
        self.player_angle = 0.0
        self.sim_time = 0.0
        self.is_game_paused = True
        self.stars = []
        for _ in range(70):
            sx = random.uniform(0, SCREEN_WIDTH)
            sy = random.uniform(0, SCREEN_HEIGHT)
            spd = random.uniform(15.0, 70.0)
            rad = random.uniform(1.0, 2.5)
            self.stars.append(AmbientStar(sx, sy, spd, rad))

        # Patrol crawler drone in lower background
        self.crawler_x = 180.0
        self.crawler_dir = 1.0

    def update(self, dt: float, paused: bool):
        self.is_game_paused = paused
        if not paused:
            self.sim_time += dt
            # Subtle floating drone drift
            self.player_x = 240.0 + math.cos(self.sim_time * 1.5) * 25.0
            self.player_y = 360.0 + math.sin(self.sim_time * 2.0) * 18.0
            self.player_angle = math.sin(self.sim_time * 1.2) * 0.15

            # Move stars
            for star in self.stars:
                star.x -= star.speed * dt
                if star.x < 0:
                    star.x = SCREEN_WIDTH + 10.0
                    star.y = random.uniform(0, SCREEN_HEIGHT)

            # Patrol crawler
            self.crawler_x += self.crawler_dir * 80.0 * dt
            if self.crawler_x > 450.0:
                self.crawler_dir = -1.0
            elif self.crawler_x < 80.0:
                self.crawler_dir = 1.0

    def draw(self):
        # Draw starfield
        for star in self.stars:
            col = Color(200, 220, 255, int(star.brightness))
            draw_circle(int(star.x), int(star.y), star.radius, col)

        # Draw decorative hangar grid lines
        grid_col = Color(25, 35, 55, 100)
        for gy in range(0, SCREEN_HEIGHT, 40):
            draw_line(0, gy, SCREEN_WIDTH, gy, grid_col)
        for gx in range(0, SCREEN_WIDTH, 60):
            draw_line(gx, 0, gx, SCREEN_HEIGHT, grid_col)

        # Draw 2D crawler patrol in world
        draw_crawler_enemy_2d(Vector2(self.crawler_x, 620.0), 0.0, self.sim_time, 24.0)
        draw_text("PATROL DRONE [ACTIVE]", int(self.crawler_x - 55), 645, 11, COLOR_TEXT_MUTED)

        # Draw 2D floating player drone
        draw_flying_drone_2d(Vector2(self.player_x, self.player_y), self.sim_time, 32.0)
        draw_text("PLAYER SHIP: ORBITAL DEFENDER", int(self.player_x - 70), int(self.player_y + 44), 12, COLOR_TEXT_WHITE)


# ==============================================================================
# BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY ([Tab] & [F1])
# ==============================================================================

def draw_xray_stack_inspector(stack: MenuStack, active_settings: dict, x: int, y: int, w: int, h: int):
    """
    Renders an in-depth visual telemetry panel showing the internal memory layout
    and state of the LIFO Menu Stack.
    """
    draw_rectangle(x, y, w, h, Color(14, 18, 30, 240))
    draw_rectangle_lines(x, y, w, h, COLOR_ITEM_ACCENT)

    # Header
    draw_rectangle(x, y, w, 28, Color(22, 34, 58, 255))
    draw_text("LIFO MENU STACK X-RAY TELEMETRY", x + 10, y + 7, 13, COLOR_ITEM_ACCENT)

    cy = y + 36

    # Stack Depth Indicator
    depth_str = "STACK DEPTH: " + str(stack.depth()) + " / 6"
    draw_text(depth_str, x + 12, cy, 13, COLOR_TEXT_WHITE)
    cy += 20

    # Architecture Mode
    arch_str = "ARCHITECTURE: " + ("LIFO STACK [TRUE]" if stack.use_true_stack else "FLAT MONOLITHIC [NAIVE]")
    arch_col = COLOR_TEXT_GOLD if stack.use_true_stack else Color(255, 100, 100, 255)
    draw_text(arch_str, x + 12, cy, 12, arch_col)
    cy += 20

    # Push / Pop Counters
    stat_str = "PUSHES: " + str(stack.push_count) + "   POPS: " + str(stack.pop_count)
    draw_text(stat_str, x + 12, cy, 12, COLOR_TEXT_MUTED)
    cy += 24

    # Visual Stack Frame Ladder (Drawn bottom-to-top)
    draw_text("ACTIVE STACK FRAMES (BOTTOM -> TOP):", x + 12, cy, 11, COLOR_ITEM_ACCENT)
    cy += 16

    ladder_x = x + 14
    ladder_w = w - 28
    frame_h = 26

    if stack.depth() == 0:
        draw_rectangle(ladder_x, cy, ladder_w, frame_h, Color(25, 30, 45, 180))
        draw_rectangle_lines(ladder_x, cy, ladder_w, frame_h, Color(50, 60, 80, 255))
        draw_text("<STACK EMPTY / RESUMED>", ladder_x + 10, cy + 6, 12, COLOR_TEXT_MUTED)
        cy += frame_h + 8
    else:
        for i in range(len(stack.stack)):
            frm = stack.stack[i]
            is_top = (i == len(stack.stack) - 1)
            f_col = Color(35, 60, 95, 255) if is_top else Color(20, 28, 44, 255)
            b_col = COLOR_ITEM_ACCENT if is_top else Color(45, 65, 95, 255)

            draw_rectangle(ladder_x, cy, ladder_w, frame_h, f_col)
            draw_rectangle_lines(ladder_x, cy, ladder_w, frame_h, b_col)

            # Slot label
            slot_tag = "[" + str(i) + "] " + frm.breadcrumb
            if is_top:
                slot_tag += "  <-- ACTIVE TOP"
            draw_text(slot_tag, ladder_x + 8, cy + 6, 11, COLOR_TEXT_WHITE if is_top else COLOR_TEXT_MUTED)

            # Cursor memory indicator
            cursor_tag = "Idx: " + str(frm.selected_index)
            draw_text(cursor_tag, ladder_x + ladder_w - 60, cy + 6, 11, COLOR_TEXT_GOLD)

            cy += frame_h + 4

    cy += 10
    draw_line(x + 10, cy, x + w - 10, cy, Color(35, 50, 75, 255))
    cy += 12

    # Live Settings State Cache
    draw_text("LIVE SETTINGS MODEL CACHE:", x + 12, cy, 11, COLOR_ITEM_ACCENT)
    cy += 16

    s_items = [
        ("Master Vol", str(int(active_settings["master_vol"] * 100)) + "%"),
        ("SFX Vol", str(int(active_settings["sfx_vol"] * 100)) + "%"),
        ("Music Vol", str(int(active_settings["music_vol"] * 100)) + "%"),
        ("Mute Audio", "YES" if active_settings["mute_all"] else "NO"),
        ("Display Mode", str(active_settings["display_mode"])),
        ("Target FPS", str(active_settings["target_fps"])),
        ("Difficulty", str(active_settings["difficulty"])),
        ("Sensitivity", str(active_settings["sensitivity"])),
        ("Shake Trauma", str(int(active_settings["trauma_scale"] * 100)) + "%"),
    ]

    for label, val in s_items:
        draw_text(label + ":", x + 16, cy, 11, COLOR_TEXT_MUTED)
        draw_text(val, x + 180, cy, 11, COLOR_TEXT_WHITE)
        cy += 15

    cy += 8
    draw_line(x + 10, cy, x + w - 10, cy, Color(35, 50, 75, 255))
    cy += 10

    # Push/Pop Event History Log
    draw_text("EVENT DISPATCH HISTORY:", x + 12, cy, 11, COLOR_ITEM_ACCENT)
    cy += 16
    for ev in stack.history_log:
        draw_text(ev, x + 16, cy, 10, COLOR_TEXT_MUTED)
        cy += 14


# ==============================================================================
# BLOCK 4: MAIN GAME LOOP & AUTOMATED SMOKE TEST
# ==============================================================================

class MenuStackGame:
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()
        self.sfx = SoundLibrary()
        self.sfx.init_defaults()

        # Telemetry & Pattern State
        self.show_xray = True
        self.pattern_enabled = True      # [F1] True = LIFO Stack, False = Flat Monolithic
        self.damped_transitions = True   # [F2] True = Smooth Damped Slide, False = Instant Snap

        # Active Settings Storage (Source of Truth)
        self.settings = {
            "master_vol": 0.85,
            "sfx_vol": 0.90,
            "music_vol": 0.70,
            "mute_all": False,
            "audio_device": "Studio Monitors (24-bit/48kHz)",
            "resolution": "1920x1080 (16:9)",
            "display_mode": "Borderless Fullscreen",
            "target_fps": "60 FPS (V-Sync)",
            "color_filter": "Standard (RGB)",
            "difficulty": "Normal (Standard Combat)",
            "sensitivity": 6,
            "invert_y": False,
            "trauma_scale": 0.80,
            "damage_numbers": True,
        }

        # Background World Simulation
        self.world = LivingWorldSimulation()

        # Core Pattern: Menu Stack Container
        self.menu_stack = MenuStack()
        self.menu_stack.use_true_stack = self.pattern_enabled
        self.menu_stack.damped_motion_enabled = self.damped_transitions

        # Push initial root Pause frame
        self._push_pause_root()

        # Toast notification banner
        self.toast_msg = "Game Paused. Press Esc to pop or resume."
        self.toast_timer = 3.0

        # Input repeat timer for analog/key navigation
        self.input_repeat_cooldown = 0.0

    def _create_pause_root_frame(self) -> MenuFrame:
        frm = MenuFrame(FRAME_PAUSE_ROOT, "SYSTEM PAUSE", "PAUSE")
        frm.add_item(MenuItem(ITEM_ACTION, "Resume Game", "Return to active spacecraft flight simulation", "action_resume"))
        frm.add_item(MenuItem(ITEM_ACTION, "Options & Configuration", "Configure Audio, Display, and Gameplay parameters", "action_push_options"))
        frm.add_item(MenuItem(ITEM_ACTION, "Quick Save Checkpoint", "Serialize simulation state to local snapshot storage", "action_save"))
        frm.add_item(MenuItem(ITEM_ACTION, "Reset All Settings", "Revert all settings to standard factory defaults", "action_push_reset_confirm"))
        frm.add_item(MenuItem(ITEM_ACTION, "Quit to Desktop", "Terminate application and release all resources", "action_push_quit_confirm"))
        return frm

    def _create_options_root_frame(self) -> MenuFrame:
        frm = MenuFrame(FRAME_OPTIONS_ROOT, "CONFIGURATION", "OPTIONS")
        frm.add_item(MenuItem(ITEM_ACTION, "Audio & Acoustics", "Volume balances, output hardware, and acoustic filtering", "action_push_audio"))
        frm.add_item(MenuItem(ITEM_ACTION, "Display & Graphics", "Resolution, frame pacing, sync modes, and visual accessibility", "action_push_display"))
        frm.add_item(MenuItem(ITEM_ACTION, "Gameplay & Controls", "Difficulty tier, analog sensitivity, and screen shake trauma", "action_push_gameplay"))
        frm.add_item(MenuItem(ITEM_ACTION, "Back to Pause Menu", "Pop back to the root pause screen", "action_pop"))
        return frm

    def _create_audio_settings_frame(self) -> MenuFrame:
        frm = MenuFrame(FRAME_AUDIO_SETTINGS, "AUDIO CONFIGURATION", "AUDIO")
        # Master Vol
        item_master = MenuItem(ITEM_SLIDER, "Master Volume", "Overall game sound attenuation scale")
        item_master.set_slider(self.settings["master_vol"])
        frm.add_item(item_master)

        # SFX Vol
        item_sfx = MenuItem(ITEM_SLIDER, "SFX Volume", "Weapon blasts, engine hums, and UI feedback sound level")
        item_sfx.set_slider(self.settings["sfx_vol"])
        frm.add_item(item_sfx)

        # Music Vol
        item_mus = MenuItem(ITEM_SLIDER, "Music Volume", "Dynamic soundtrack and orchestral accompaniment level")
        item_mus.set_slider(self.settings["music_vol"])
        frm.add_item(item_mus)

        # Mute
        item_mute = MenuItem(ITEM_TOGGLE, "Mute All Audio", "Instantly silence all master audio output channels")
        item_mute.set_toggle(self.settings["mute_all"])
        frm.add_item(item_mute)

        # Device
        item_dev = MenuItem(ITEM_STEPPER, "Output Device", "Hardware audio rendering endpoint")
        item_dev.set_stepper(["Studio Monitors (24-bit/48kHz)", "7.1 Spatial Headset", "TV Speakers (Dolby Audio)", "Basic Stereo Direct"], 0)
        frm.add_item(item_dev)

        frm.add_item(MenuItem(ITEM_ACTION, "Back to Options", "Return to primary configuration hub", "action_pop"))
        return frm

    def _create_display_settings_frame(self) -> MenuFrame:
        frm = MenuFrame(FRAME_DISPLAY_SETTINGS, "DISPLAY CONFIGURATION", "DISPLAY")
        # Resolution
        item_res = MenuItem(ITEM_STEPPER, "Resolution", "Canvas render resolution and aspect ratio")
        item_res.set_stepper(["1280x720 (16:9)", "1920x1080 (16:9)", "2560x1440 (16:9)", "3840x2160 (4K UHD)"], 1)
        frm.add_item(item_res)

        # Mode
        item_mode = MenuItem(ITEM_STEPPER, "Window Mode", "Display Presentation Mode")
        item_mode.set_stepper(["Windowed", "Borderless Fullscreen", "Exclusive Fullscreen"], 1)
        frm.add_item(item_mode)

        # FPS
        item_fps = MenuItem(ITEM_STEPPER, "Framerate Cap", "Maximum target render frequency")
        item_fps.set_stepper(["30 FPS (Power Save)", "60 FPS (V-Sync)", "120 FPS (High Refresh)", "144 FPS (Ultra Low Latency)", "Uncapped"], 1)
        frm.add_item(item_fps)

        # Accessibility Color Filter
        item_filt = MenuItem(ITEM_STEPPER, "Color Blind Assist", "Spectral correction matrix for color vision deficiency")
        item_filt.set_stepper(["Standard (RGB)", "Protanopia (Red Weak)", "Deuteranopia (Green Weak)", "Tritanopia (Blue Weak)", "Monochrome High Contrast"], 0)
        frm.add_item(item_filt)

        frm.add_item(MenuItem(ITEM_ACTION, "Back to Options", "Return to primary configuration hub", "action_pop"))
        return frm

    def _create_gameplay_settings_frame(self) -> MenuFrame:
        frm = MenuFrame(FRAME_GAMEPLAY_SETTINGS, "GAMEPLAY CONFIGURATION", "GAMEPLAY")
        # Difficulty
        item_diff = MenuItem(ITEM_STEPPER, "Difficulty Tier", "Damage multipliers, enemy AI aggression, and resource abundance")
        item_diff.set_stepper(["Story (Relaxed Exploration)", "Normal (Standard Combat)", "Hardcore (Aggressive Flanking)", "Nightmare (Permadeath)"], 1)
        frm.add_item(item_diff)

        # Sensitivity
        item_sens = MenuItem(ITEM_SLIDER, "Look Sensitivity", "Angular turn rate for mouse cursor and gamepad right stick")
        item_sens.set_slider(self.settings["sensitivity"] / 10.0)
        frm.add_item(item_sens)

        # Invert Y
        item_inv = MenuItem(ITEM_TOGGLE, "Invert Pitch Axis", "Invert vertical look direction for flight yoke navigation")
        item_inv.set_toggle(self.settings["invert_y"])
        frm.add_item(item_inv)

        # Screen Shake
        item_shk = MenuItem(ITEM_SLIDER, "Trauma Screen Shake", "Camera shake intensity during kinetic impacts and orbital explosions")
        item_shk.set_slider(self.settings["trauma_scale"])
        frm.add_item(item_shk)

        # Damage Numbers
        item_dmg = MenuItem(ITEM_TOGGLE, "Floating Damage Numbers", "Display kinetic damage numbers on enemy hit impacts")
        item_dmg.set_toggle(self.settings["damage_numbers"])
        frm.add_item(item_dmg)

        frm.add_item(MenuItem(ITEM_ACTION, "Back to Options", "Return to primary configuration hub", "action_pop"))
        return frm

    def _create_confirm_modal_frame(self, title: str, message: str, confirm_action_id: str) -> MenuFrame:
        frm = MenuFrame(FRAME_CONFIRM_MODAL, title, "CONFIRM")
        frm.is_modal = True
        frm.modal_message = message
        frm.modal_on_confirm_action = confirm_action_id
        frm.add_item(MenuItem(ITEM_ACTION, "Confirm & Proceed", "Execute this action and apply changes", "action_modal_confirm"))
        frm.add_item(MenuItem(ITEM_ACTION, "Cancel & Dismiss", "Discard action and safely pop back to previous menu", "action_pop"))
        return frm

    def _push_pause_root(self):
        self.menu_stack.push(self._create_pause_root_frame())

    def _dispatch_action(self, action_id: str):
        """Executes a command dispatched by a menu button or modal."""
        if action_id == "action_resume":
            self.menu_stack.clear()
            self.sfx.play("click", 0.7)
            self.toast_msg = "Resumed! Press [Esc] or [P] or [Gamepad Start] to open Pause Menu."
            self.toast_timer = 3.5

        elif action_id == "action_push_options":
            self.menu_stack.push(self._create_options_root_frame())
            self.sfx.play("click", 0.7)

        elif action_id == "action_push_audio":
            self.menu_stack.push(self._create_audio_settings_frame())
            self.sfx.play("click", 0.7)

        elif action_id == "action_push_display":
            self.menu_stack.push(self._create_display_settings_frame())
            self.sfx.play("click", 0.7)

        elif action_id == "action_push_gameplay":
            self.menu_stack.push(self._create_gameplay_settings_frame())
            self.sfx.play("click", 0.7)

        elif action_id == "action_save":
            self.sfx.play("pickup", 0.8)
            self.toast_msg = "State Serialized! Checkpoint successfully written to memory."
            self.toast_timer = 3.0

        elif action_id == "action_push_reset_confirm":
            modal = self._create_confirm_modal_frame(
                "RESET SETTINGS?",
                "Are you sure you want to revert all audio, display, and gameplay settings to factory defaults?",
                "action_do_reset_defaults"
            )
            self.menu_stack.push(modal)
            self.sfx.play("hit", 0.6)

        elif action_id == "action_push_quit_confirm":
            modal = self._create_confirm_modal_frame(
                "QUIT TO DESKTOP?",
                "Are you sure you want to terminate this simulation session?",
                "action_do_quit"
            )
            self.menu_stack.push(modal)
            self.sfx.play("hit", 0.6)

        elif action_id == "action_modal_confirm":
            top_frame = self.menu_stack.top()
            if top_frame and top_frame.is_modal:
                target_act = top_frame.modal_on_confirm_action
                self.menu_stack.pop()  # Pop the modal first
                self._dispatch_action(target_act)

        elif action_id == "action_do_reset_defaults":
            self.settings["master_vol"] = 0.85
            self.settings["sfx_vol"] = 0.90
            self.settings["music_vol"] = 0.70
            self.settings["mute_all"] = False
            self.settings["audio_device"] = "Studio Monitors (24-bit/48kHz)"
            self.settings["resolution"] = "1920x1080 (16:9)"
            self.settings["display_mode"] = "Borderless Fullscreen"
            self.settings["target_fps"] = "60 FPS (V-Sync)"
            self.settings["color_filter"] = "Standard (RGB)"
            self.settings["difficulty"] = "Normal (Standard Combat)"
            self.settings["sensitivity"] = 6
            self.settings["invert_y"] = False
            self.settings["trauma_scale"] = 0.80
            self.settings["damage_numbers"] = True
            self.sfx.play("pickup", 0.9)
            self.toast_msg = "Factory Defaults Restored across all subsystems."
            self.toast_timer = 3.0

        elif action_id == "action_do_quit":
            self.sfx.play("laser", 0.8)
            self.toast_msg = "Session Finished. (In a full game, close_window() is called)."
            self.toast_timer = 3.5

        elif action_id == "action_pop":
            if not self.menu_stack.pop():
                # If popped from root, resume game
                self.menu_stack.clear()
            self.sfx.play("click", 0.5)

    def update(self):
        dt = min(get_frame_time(), 0.05)

        # X-Ray Toggle ([Tab] / Gamepad View)
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
            self.sfx.play("click", 0.5)

        # Pattern Toggle ([F1] / Gamepad R3): LIFO Stack vs Flat Monolithic
        if is_dual_pattern_toggle_pressed():
            self.pattern_enabled = not self.pattern_enabled
            self.menu_stack.use_true_stack = self.pattern_enabled
            self.sfx.play("click", 0.6)
            mode_name = "LIFO Menu Stack" if self.pattern_enabled else "Flat Monolithic Menu"
            self.toast_msg = "Architecture Toggled: " + mode_name
            self.toast_timer = 3.0

        # Motion Toggle ([F2] / Gamepad L3): Damped Slide vs Instant Snap
        if is_dual_secondary_toggle_pressed():
            self.damped_transitions = not self.damped_transitions
            self.menu_stack.damped_motion_enabled = self.damped_transitions
            self.sfx.play("click", 0.5)
            t_mode = "Damped Smooth Slide" if self.damped_transitions else "Instant Snap"
            self.toast_msg = "Transition Mode: " + t_mode
            self.toast_timer = 3.0

        # Reset Simulation ([R] / Gamepad Start)
        if is_dual_reset_pressed():
            self.menu_stack.clear()
            self._push_pause_root()
            self.sfx.play("pickup", 0.8)
            self.toast_msg = "Menu Stack Reinitialized to Root Pause."
            self.toast_timer = 2.5

        # Toggle Pause with [P] or [Esc] when gameplay is active
        if self.menu_stack.depth() == 0:
            if is_key_pressed(KEY_P) or is_key_pressed(KEY_ESCAPE):
                self._push_pause_root()
                self.sfx.play("click", 0.6)

        # Update toast timer
        if self.toast_timer > 0.0:
            self.toast_timer -= dt

        # Update background world simulation
        is_paused = (self.menu_stack.depth() > 0)
        self.world.update(dt, is_paused)

        # If stack is active, process top menu frame inputs
        top_frame = self.menu_stack.top()
        if top_frame:
            self._update_top_frame(top_frame, dt)

    def _update_top_frame(self, frame: MenuFrame, dt: float):
        # Update visual transitions
        if self.damped_transitions:
            frame.visual_offset_x = damp(frame.visual_offset_x, 0.0, 14.0, dt)
            frame.alpha = damp(frame.alpha, 1.0, 12.0, dt)
        else:
            frame.visual_offset_x = 0.0
            frame.alpha = 1.0

        if self.input_repeat_cooldown > 0.0:
            self.input_repeat_cooldown -= dt

        # Read simultaneous dual inputs
        move_vec = get_dual_move_2d()
        up_pressed = (is_key_pressed(KEY_W) or is_key_pressed(KEY_UP))
        down_pressed = (is_key_pressed(KEY_S) or is_key_pressed(KEY_DOWN))
        left_pressed = (is_key_pressed(KEY_A) or is_key_pressed(KEY_LEFT))
        right_pressed = (is_key_pressed(KEY_D) or is_key_pressed(KEY_RIGHT))

        # Check analog stick tilt if cooldown elapsed
        if self.input_repeat_cooldown <= 0.0:
            if move_vec.y < -0.5:
                up_pressed = True
                self.input_repeat_cooldown = 0.22
            elif move_vec.y > 0.5:
                down_pressed = True
                self.input_repeat_cooldown = 0.22

            if move_vec.x < -0.5:
                left_pressed = True
                self.input_repeat_cooldown = 0.18
            elif move_vec.x > 0.5:
                right_pressed = True
                self.input_repeat_cooldown = 0.18

        # Vertical Cursor Navigation (Wrapped mod N)
        if len(frame.items) > 0:
            if up_pressed:
                frame.selected_index = (frame.selected_index - 1 + len(frame.items)) % len(frame.items)
                self.sfx.play("click", 0.4)
            elif down_pressed:
                frame.selected_index = (frame.selected_index + 1) % len(frame.items)
                self.sfx.play("click", 0.4)

        # Selected Item Interaction
        cur_item = frame.get_selected_item()
        if cur_item:
            # Sliders (Left/Right to adjust continuous value)
            if cur_item.control_type == ITEM_SLIDER:
                step_delta = 0.05
                if left_pressed:
                    cur_item.slider_val = max(0.0, cur_item.slider_val - step_delta)
                    self._apply_slider_change(cur_item)
                    self.sfx.play("click", 0.3)
                elif right_pressed:
                    cur_item.slider_val = min(1.0, cur_item.slider_val + step_delta)
                    self._apply_slider_change(cur_item)
                    self.sfx.play("click", 0.3)

            # Steppers (Left/Right to cycle options)
            elif cur_item.control_type == ITEM_STEPPER and len(cur_item.step_options) > 0:
                if left_pressed:
                    cur_item.step_index = (cur_item.step_index - 1 + len(cur_item.step_options)) % len(cur_item.step_options)
                    self._apply_stepper_change(cur_item)
                    self.sfx.play("click", 0.4)
                elif right_pressed:
                    cur_item.step_index = (cur_item.step_index + 1) % len(cur_item.step_options)
                    self._apply_stepper_change(cur_item)
                    self.sfx.play("click", 0.4)

            # Toggles (Enter, Space, or Left/Right to flip)
            elif cur_item.control_type == ITEM_TOGGLE:
                if left_pressed or right_pressed:
                    cur_item.toggle_val = not cur_item.toggle_val
                    self._apply_toggle_change(cur_item)
                    self.sfx.play("click", 0.4)

        # Confirm / Activate Action (Enter / Space / Gamepad A)
        pad_id = get_active_gamepad_id()
        pad_a_pressed = (pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_FACE_DOWN))
        confirm_pressed = (is_key_pressed(KEY_ENTER) or is_key_pressed(KEY_SPACE) or pad_a_pressed)

        if confirm_pressed and cur_item:
            if cur_item.control_type == ITEM_ACTION:
                self._dispatch_action(cur_item.action_id)
            elif cur_item.control_type == ITEM_TOGGLE:
                cur_item.toggle_val = not cur_item.toggle_val
                self._apply_toggle_change(cur_item)
                self.sfx.play("click", 0.5)

        # Pop / Cancel (Esc / Backspace / Gamepad B)
        pad_b_pressed = (pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_FACE_RIGHT))
        cancel_pressed = (is_key_pressed(KEY_ESCAPE) or is_key_pressed(KEY_BACKSPACE) or pad_b_pressed)
        if cancel_pressed:
            self._dispatch_action("action_pop")

        # Mouse direct point-and-click integration
        self._handle_mouse_interactions(frame)

    def _handle_mouse_interactions(self, frame: MenuFrame):
        mx = get_mouse_x()
        my = get_mouse_y()
        mouse_clicked = is_mouse_button_pressed(MOUSE_BUTTON_LEFT)

        # Check breadcrumb bar clicks
        breadcrumb_h = 32
        bx = 200
        by = 80
        for i in range(len(self.menu_stack.stack)):
            f_crumb = self.menu_stack.stack[i]
            crumb_text = f_crumb.breadcrumb
            tw = measure_text(crumb_text, 14) + 24
            if mx >= bx and mx <= bx + tw and my >= by and my <= by + breadcrumb_h:
                if mouse_clicked:
                    self.menu_stack.pop_to_depth(i + 1)
                    self.sfx.play("click", 0.5)
                    return
            bx += tw + 18

        # Check menu item clicks and hovers
        panel_x = 200 + int(frame.visual_offset_x)
        panel_y = 130
        item_w = 520
        item_h = 54
        start_y = panel_y + 60

        for idx in range(len(frame.items)):
            iy = start_y + idx * (item_h + 10)
            if mx >= panel_x + 20 and mx <= panel_x + 20 + item_w and my >= iy and my <= iy + item_h:
                frame.selected_index = idx
                if mouse_clicked:
                    item = frame.items[idx]
                    if item.control_type == ITEM_ACTION:
                        self._dispatch_action(item.action_id)
                    elif item.control_type == ITEM_TOGGLE:
                        item.toggle_val = not item.toggle_val
                        self._apply_toggle_change(item)
                        self.sfx.play("click", 0.5)
                    elif item.control_type == ITEM_SLIDER:
                        # Direct drag / click on slider bar
                        slider_box_x = panel_x + 20 + item_w - 180
                        if mx >= slider_box_x and mx <= slider_box_x + 160:
                            rel = (mx - slider_box_x) / 160.0
                            item.slider_val = max(0.0, min(1.0, rel))
                            self._apply_slider_change(item)
                            self.sfx.play("click", 0.3)
                    elif item.control_type == ITEM_STEPPER and len(item.step_options) > 0:
                        item.step_index = (item.step_index + 1) % len(item.step_options)
                        self._apply_stepper_change(item)
                        self.sfx.play("click", 0.4)

    def _apply_slider_change(self, item: MenuItem):
        if "Master" in item.label:
            self.settings["master_vol"] = item.slider_val
        elif "SFX" in item.label:
            self.settings["sfx_vol"] = item.slider_val
        elif "Music" in item.label:
            self.settings["music_vol"] = item.slider_val
        elif "Sensitivity" in item.label:
            self.settings["sensitivity"] = max(1, int(item.slider_val * 10))
        elif "Trauma" in item.label:
            self.settings["trauma_scale"] = item.slider_val

    def _apply_stepper_change(self, item: MenuItem):
        opt = item.step_options[item.step_index]
        if "Device" in item.label:
            self.settings["audio_device"] = opt
        elif "Resolution" in item.label:
            self.settings["resolution"] = opt
        elif "Window" in item.label:
            self.settings["display_mode"] = opt
        elif "Framerate" in item.label:
            self.settings["target_fps"] = opt
        elif "Color" in item.label:
            self.settings["color_filter"] = opt
        elif "Difficulty" in item.label:
            self.settings["difficulty"] = opt

    def _apply_toggle_change(self, item: MenuItem):
        if "Mute" in item.label:
            self.settings["mute_all"] = item.toggle_val
        elif "Invert" in item.label:
            self.settings["invert_y"] = item.toggle_val
        elif "Damage" in item.label:
            self.settings["damage_numbers"] = item.toggle_val

    def draw(self):
        begin_drawing()
        clear_background(COLOR_BG_DARK)

        # 1. Background living simulation
        self.world.draw()

        # 2. Draw Menu Stack UI if paused
        if self.menu_stack.depth() > 0:
            # Frosted dark backdrop scrim
            draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, Color(10, 14, 24, 210))

            # Breadcrumb navigation bar at top
            self._draw_breadcrumbs()

            # Top frame render
            top_frame = self.menu_stack.top()
            if top_frame:
                if top_frame.is_modal:
                    self._draw_modal_frame(top_frame)
                else:
                    self._draw_standard_frame(top_frame)

        # 3. Telemetry Overlay ([Tab])
        if self.show_xray:
            draw_xray_stack_inspector(self.menu_stack, self.settings, 810, 68, 450, 630)

        # 4. Toast Notification
        if self.toast_timer > 0.0:
            self._draw_toast()

        # 5. Safe Top-bar HUD (Font size, window dropdown, gamepad status badge)
        self._draw_top_hud()

        # Mandatory repo dropdowns and badges
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)

        end_drawing()

    def _draw_breadcrumbs(self):
        bx = 200
        by = 78
        draw_text("NAVIGATION PATH:", bx - 145, by + 5, 11, COLOR_ITEM_ACCENT)

        for i in range(len(self.menu_stack.stack)):
            f = self.menu_stack.stack[i]
            is_active = (i == len(self.menu_stack.stack) - 1)
            text_str = f.breadcrumb
            tw = measure_text(text_str, 13) + 20

            # Breadcrumb pill button
            bg_col = Color(35, 58, 95, 255) if is_active else Color(20, 28, 46, 230)
            bdr_col = COLOR_ITEM_ACCENT if is_active else Color(45, 65, 100, 255)
            draw_rectangle(bx, by, tw, 26, bg_col)
            draw_rectangle_lines(bx, by, tw, 26, bdr_col)

            draw_text(text_str, bx + 10, by + 6, 12, COLOR_TEXT_WHITE if is_active else COLOR_TEXT_MUTED)
            bx += tw + 6

            if i < len(self.menu_stack.stack) - 1:
                draw_text(">", bx, by + 6, 12, COLOR_TEXT_GOLD)
                bx += 14

    def _draw_standard_frame(self, frame: MenuFrame):
        panel_x = 200 + int(frame.visual_offset_x)
        panel_y = 120
        panel_w = 580
        panel_h = 560

        alpha_int = max(0, min(255, int(frame.alpha * 255)))
        p_bg = Color(COLOR_PANEL_BG.r, COLOR_PANEL_BG.g, COLOR_PANEL_BG.b, alpha_int)
        p_bdr = Color(COLOR_PANEL_BORDER.r, COLOR_PANEL_BORDER.g, COLOR_PANEL_BORDER.b, alpha_int)

        draw_rectangle(panel_x, panel_y, panel_w, panel_h, p_bg)
        draw_rectangle_lines(panel_x, panel_y, panel_w, panel_h, p_bdr)

        # Header Title Banner
        draw_rectangle(panel_x, panel_y, panel_w, 48, Color(24, 35, 60, alpha_int))
        draw_rectangle_lines(panel_x, panel_y, panel_w, 48, p_bdr)
        draw_text(frame.title, panel_x + 24, panel_y + 14, 18, COLOR_TEXT_WHITE)

        # Stack Depth Badge in Header
        depth_tag = "LIFO LEVEL: " + str(self.menu_stack.depth())
        draw_text(depth_tag, panel_x + panel_w - 130, panel_y + 16, 12, COLOR_TEXT_GOLD)

        # Items List
        item_w = panel_w - 48
        item_h = 54
        start_y = panel_y + 66

        for idx in range(len(frame.items)):
            iy = start_y + idx * (item_h + 10)
            item = frame.items[idx]
            is_sel = (idx == frame.selected_index)

            # Item card background
            card_col = COLOR_ITEM_HOVER if is_sel else COLOR_ITEM_NORMAL
            card_bdr = COLOR_ITEM_ACCENT if is_sel else COLOR_ITEM_BORDER
            draw_rectangle(panel_x + 24, iy, item_w, item_h, card_col)
            draw_rectangle_lines(panel_x + 24, iy, item_w, item_h, card_bdr)

            # Selection marker pip
            if is_sel:
                draw_rectangle(panel_x + 24, iy, 5, item_h, COLOR_ITEM_ACCENT)

            # Label & Description
            draw_text(item.label, panel_x + 40, iy + 8, 15, COLOR_TEXT_WHITE if is_sel else COLOR_TEXT_MUTED)
            draw_text(item.description, panel_x + 40, iy + 30, 10, COLOR_TEXT_MUTED)

            # Control-Specific Widgets on the right side
            widget_x = panel_x + 24 + item_w - 190
            widget_y = iy + 14

            if item.control_type == ITEM_ACTION:
                arrow = ">" if is_sel else ""
                draw_text(arrow, panel_x + 24 + item_w - 30, iy + 16, 16, COLOR_ITEM_ACCENT)

            elif item.control_type == ITEM_SLIDER:
                # Slider track
                draw_rectangle(widget_x, widget_y + 6, 160, 10, COLOR_SLIDER_BG)
                draw_rectangle(widget_x, widget_y + 6, int(160 * item.slider_val), 10, COLOR_SLIDER_FILL)
                draw_rectangle_lines(widget_x, widget_y + 6, 160, 10, COLOR_ITEM_BORDER)
                # Numeric percentage label
                pct_str = str(int(item.slider_val * 100)) + "%"
                draw_text(pct_str, widget_x - 42, widget_y + 4, 11, COLOR_TEXT_WHITE)

            elif item.control_type == ITEM_STEPPER:
                if len(item.step_options) > 0:
                    opt_text = item.step_options[item.step_index]
                    draw_rectangle(widget_x - 20, widget_y, 180, 24, Color(16, 22, 36, 255))
                    draw_rectangle_lines(widget_x - 20, widget_y, 180, 24, COLOR_ITEM_BORDER)
                    draw_text("<", widget_x - 14, widget_y + 5, 12, COLOR_ITEM_ACCENT)
                    draw_text(">", widget_x + 150, widget_y + 5, 12, COLOR_ITEM_ACCENT)
                    draw_text(opt_text[:17], widget_x + 4, widget_y + 5, 11, COLOR_TEXT_GOLD)

            elif item.control_type == ITEM_TOGGLE:
                tg_col = COLOR_ITEM_ACCENT if item.toggle_val else Color(80, 95, 120, 255)
                draw_rectangle(widget_x + 70, widget_y, 75, 24, Color(18, 24, 38, 255))
                draw_rectangle_lines(widget_x + 70, widget_y, 75, 24, tg_col)
                status_txt = "ON" if item.toggle_val else "OFF"
                draw_text(status_txt, widget_x + 95, widget_y + 5, 12, tg_col)

        # Footer Legend inside panel
        foot_y = panel_y + panel_h - 34
        draw_line(panel_x + 24, foot_y - 6, panel_x + panel_w - 24, foot_y - 6, Color(40, 60, 95, 255))
        draw_text("NAV: [W/S] or D-Pad   ADJUST: [A/D]   CONFIRM: [Enter/A]   POP: [Esc/B]", panel_x + 36, foot_y, 11, COLOR_TEXT_MUTED)

    def _draw_modal_frame(self, frame: MenuFrame):
        # Full Modal Backdrop Scrim
        draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_MODAL_SCRIM)

        modal_w = 540
        modal_h = 280
        mx = (SCREEN_WIDTH - modal_w) // 2
        my = (SCREEN_HEIGHT - modal_h) // 2

        draw_rectangle(mx, my, modal_w, modal_h, COLOR_MODAL_BG)
        draw_rectangle_lines(mx, my, modal_w, modal_h, COLOR_MODAL_BORDER)

        # Header Warning
        draw_rectangle(mx, my, modal_w, 42, Color(80, 25, 25, 255))
        draw_rectangle_lines(mx, my, modal_w, 42, COLOR_MODAL_BORDER)
        draw_text("! " + frame.title, mx + 20, my + 12, 16, COLOR_TEXT_WHITE)

        # Body Message Text
        draw_text(frame.modal_message, mx + 24, my + 64, 13, COLOR_TEXT_WHITE)

        # Interactive Modal Buttons
        btn_y = my + 160
        btn_w = 492
        btn_h = 42

        for idx in range(len(frame.items)):
            by = btn_y + idx * (btn_h + 12)
            item = frame.items[idx]
            is_sel = (idx == frame.selected_index)

            b_col = Color(120, 35, 35, 255) if (is_sel and "Confirm" in item.label) else (COLOR_ITEM_HOVER if is_sel else COLOR_ITEM_NORMAL)
            bdr_col = COLOR_MODAL_BORDER if is_sel else COLOR_ITEM_BORDER

            draw_rectangle(mx + 24, by, btn_w, btn_h, b_col)
            draw_rectangle_lines(mx + 24, by, btn_w, btn_h, bdr_col)
            draw_text(item.label, mx + 44, by + 12, 14, COLOR_TEXT_WHITE)
            draw_text(item.description, mx + 220, by + 14, 10, COLOR_TEXT_MUTED)

    def _draw_toast(self):
        tw = measure_text(self.toast_msg, 13) + 36
        tx = (SCREEN_WIDTH - tw) // 2
        ty = SCREEN_HEIGHT - 60
        draw_rectangle(tx, ty, tw, 30, Color(20, 28, 48, 240))
        draw_rectangle_lines(tx, ty, tw, 30, COLOR_ITEM_ACCENT)
        draw_text(self.toast_msg, tx + 18, ty + 8, 13, COLOR_TEXT_WHITE)

    def _draw_top_hud(self):
        # Left HUD banner
        draw_text("MENU STACK ARCHITECTURE LAB", 24, 18, 16, COLOR_TEXT_WHITE)
        draw_text("Section 3.1: Menus & UI  |  Push/Pop LIFO Modal Navigation Pattern", 24, 38, 11, COLOR_TEXT_MUTED)

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
    MenuStackGame().run(smoke_test=is_smoke)
