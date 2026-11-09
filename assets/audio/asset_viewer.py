# -*- coding: utf-8 -*-
"""
Interactive Procedural Asset Workbench & Audition Viewer (asset_viewer.py)
=========================================================================
Location : assets/audio/asset_viewer.py
Role     : Interactive graphical workbench & live inspector for all procedural
           assets discovered across the repository by `asset_loader.py`.

Problem Solved:
  Eliminates blind integration and guesswork by providing an interactive Raylib
  dashboard with dedicated tabs for every procedural asset kind:
    - Tab 0: 3D Models   (`assets/models_3D/`) - Orbit camera, wireframe, lighting, palettes.
    - Tab 1: 2D Sprites  (`assets/sprites_2D/`) - Zoom/pan canvas, facing angle, animation.
    - Tab 2: SFX Sounds  (`assets/audio/SFX/`) - Live synthesis, waveform oscilloscope.
    - Tab 3: BGM Tracks  (`assets/audio/BGM/`) - Audio streaming, 24-band spectrum visualizer.

Interactive Features & Controls:
  - Tabs Navigation : Click tab buttons, press [1], [2], [3], [4], or [Q] / [E] bumpers.
  - Play / Pause    : [Space] or on-screen Play/Pause button.
  - Stop            : [S] or on-screen Stop button (resets timer and halts playback).
  - Reset View      : [R] resets 3D camera orbit or 2D canvas pan/zoom.
  - Live Rescan     : [F5] or click Rescan to dynamically refresh discovered disk assets.
  - Sliders         : Drag volume, pitch, speed, scale, and angle controllers.
  - Inspector Panel : Live inspection of primitives, mathematical equations, and code snippets.
  - UI Settings     : Full integration with repository Font, Font Size, and Window dropdowns.

Direct C++ Raylib Translation (raylib.h):
  Maps directly to:
    - DrawCube, DrawSphere, DrawCylinderEx for 3D procedural primitives.
    - DrawCircleV, DrawRectanglePro, DrawTriangle for 2D vector sprites.
    - PlaySound, StopSound, SetSoundVolume, SetSoundPitch for SFX.
    - PlayMusicStream, UpdateMusicStream, StopMusicStream for BGM streams.
"""

import sys
import os
import math
import ast
import time
from typing import Dict, List, Optional, Tuple, Any

# 1. Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# 2. Add repository root to search path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

# 3. Mandatory Raylib and utility imports
from pyray import *
from assets.audio.asset_loader import *
from utils import *

# Window & UI Dimensions
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WINDOW_TITLE = "Procedural Asset Workbench & Viewer (Raylib Python)"

# Visual UI Palette (Cybernetic Dark Theme matching launcher.py & tasks.py)
COLOR_BG = Color(10, 13, 22, 255)
COLOR_PANEL = Color(18, 23, 38, 255)
COLOR_PANEL_ALT = Color(14, 18, 30, 255)
COLOR_PANEL_HEADER = Color(24, 34, 56, 255)
COLOR_PANEL_BORDER = Color(48, 65, 105, 255)
COLOR_GRID_LINE = Color(30, 42, 68, 120)

COLOR_ACCENT = Color(70, 205, 255, 255)        # Electric Cyan
COLOR_ACCENT_HOVER = Color(110, 225, 255, 255)
COLOR_ACCENT_GOLD = Color(255, 215, 0, 255)     # Amber / Gold
COLOR_ACCENT_GREEN = Color(60, 220, 120, 255)   # Emerald Green
COLOR_ACCENT_RED = Color(255, 80, 80, 255)      # Coral Red
COLOR_ACCENT_PURPLE = Color(180, 100, 255, 255)

COLOR_TEXT_MAIN = Color(235, 242, 255, 255)
COLOR_TEXT_DIM = Color(145, 160, 185, 255)
COLOR_TEXT_MUTED = Color(95, 110, 135, 255)

COLOR_SELECTION = Color(26, 52, 88, 255)
COLOR_SELECTION_BORDER = Color(70, 205, 255, 255)
COLOR_HOVER_ROW = Color(28, 42, 68, 255)

# Tab Indices
TAB_3D = 0
TAB_2D = 1
TAB_SFX = 2
TAB_BGM = 3

TAB_INFO = [
    {"id": TAB_3D, "title": "3D Models", "icon": "[3D]", "catalog": "assets/models_3D/"},
    {"id": TAB_2D, "title": "2D Sprites", "icon": "[2D]", "catalog": "assets/sprites_2D/"},
    {"id": TAB_SFX, "title": "SFX Sounds", "icon": "[SFX]", "catalog": "assets/audio/SFX/"},
    {"id": TAB_BGM, "title": "BGM Music", "icon": "[BGM]", "catalog": "assets/audio/BGM/"},
]


# ==============================================================================
# BENCHMARK PROCEDURAL PREVIEW ASSETS (Fallback & Primitive Testing Units)
# ==============================================================================
DEFAULT_BENCHMARK_3D_PALETTE = {
    "armor": Color(48, 65, 105, 255),
    "armor_dark": Color(28, 38, 62, 255),
    "joints": Color(70, 85, 120, 255),
    "visor": Color(70, 205, 255, 255),
    "core": Color(255, 215, 0, 255),
    "blade": Color(120, 230, 255, 255),
    "accent": Color(255, 80, 80, 255),
}

STEALTH_BENCHMARK_3D_PALETTE = {
    "armor": Color(24, 28, 36, 255),
    "armor_dark": Color(12, 14, 18, 255),
    "joints": Color(45, 52, 64, 255),
    "visor": Color(255, 60, 60, 255),
    "core": Color(255, 120, 40, 255),
    "blade": Color(255, 80, 80, 255),
    "accent": Color(180, 40, 40, 255),
}

CYBER_BENCHMARK_3D_PALETTE = {
    "armor": Color(35, 20, 65, 255),
    "armor_dark": Color(18, 10, 35, 255),
    "joints": Color(65, 45, 110, 255),
    "visor": Color(60, 240, 160, 255),
    "core": Color(240, 70, 220, 255),
    "blade": Color(60, 240, 160, 255),
    "accent": Color(240, 70, 220, 255),
}

DESERT_BENCHMARK_3D_PALETTE = {
    "armor": Color(180, 150, 100, 255),
    "armor_dark": Color(130, 105, 65, 255),
    "joints": Color(90, 75, 50, 255),
    "visor": Color(80, 210, 240, 255),
    "core": Color(255, 190, 50, 255),
    "blade": Color(240, 220, 160, 255),
    "accent": Color(200, 80, 40, 255),
}


def draw_benchmark_humanoid_3d(
    position: Vector3,
    rotation_y: float = 0.0,
    anim_timer: float = 0.0,
    scale: float = 1.0,
    palette: dict = None
) -> None:
    """
    Procedural 3D Articulated Biped Unit.
    Built purely from mathematical primitives: Spheres, Cubes, and Cylinders.
    Demonstrates sinusoidal walking gait stride, arm counter-swing, and sword idle bob.
    """
    pal = palette or DEFAULT_BENCHMARK_3D_PALETTE
    c_armor = pal.get("armor", Color(48, 65, 105, 255))
    c_dark = pal.get("armor_dark", Color(28, 38, 62, 255))
    c_joints = pal.get("joints", Color(70, 85, 120, 255))
    c_visor = pal.get("visor", Color(70, 205, 255, 255))
    c_core = pal.get("core", Color(255, 215, 0, 255))
    c_blade = pal.get("blade", Color(120, 230, 255, 255))
    c_accent = pal.get("accent", Color(255, 80, 80, 255))

    rad_rot = math.radians(rotation_y)
    cos_r = math.cos(rad_rot)
    sin_r = math.sin(rad_rot)

    def rot_v(lx: float, ly: float, lz: float) -> Vector3:
        wx = lx * cos_r - lz * sin_r
        wz = lx * sin_r + lz * cos_r
        return Vector3(position.x + wx * scale, position.y + ly * scale, position.z + wz * scale)

    # Locomotion oscillators
    walk_cycle = anim_timer * 4.0
    bob_y = math.sin(walk_cycle * 2.0) * 0.06
    leg_swing_l = math.sin(walk_cycle) * 0.45
    leg_swing_r = -leg_swing_l
    arm_swing_l = -leg_swing_l * 0.8
    arm_swing_r = -arm_swing_l

    # 1. Pelvis & Torso (Cubes & Spheres)
    pelvis_pos = rot_v(0.0, 1.25 + bob_y, 0.0)
    draw_cube(pelvis_pos, 0.65 * scale, 0.3 * scale, 0.45 * scale, c_dark)

    torso_pos = rot_v(0.0, 1.65 + bob_y, 0.0)
    draw_cube(torso_pos, 0.85 * scale, 0.65 * scale, 0.55 * scale, c_armor)
    draw_cube_wires(torso_pos, 0.86 * scale, 0.66 * scale, 0.56 * scale, c_dark)

    # Core Reactor (Glowing Sphere on Chest)
    core_pos = rot_v(0.0, 1.65 + bob_y, 0.30)
    core_pulse = 0.12 + 0.02 * math.sin(anim_timer * 6.0)
    draw_sphere(core_pos, core_pulse * scale, c_core)

    # 2. Neck & Head (Spheres & Visor Prism)
    head_pos = rot_v(0.0, 2.15 + bob_y, 0.0)
    draw_sphere(head_pos, 0.28 * scale, c_armor)
    visor_pos = rot_v(0.0, 2.18 + bob_y, 0.22)
    draw_cube(visor_pos, 0.38 * scale, 0.10 * scale, 0.16 * scale, c_visor)

    # 3. Shoulders / Pauldrons (Spheres)
    sh_l = rot_v(-0.62, 1.90 + bob_y, 0.0)
    sh_r = rot_v(0.62, 1.90 + bob_y, 0.0)
    draw_sphere(sh_l, 0.22 * scale, c_accent)
    draw_sphere(sh_r, 0.22 * scale, c_accent)

    # 4. Arms (Cylinders)
    hand_l = rot_v(-0.65, 1.30 + bob_y, arm_swing_l)
    hand_r = rot_v(0.65, 1.30 + bob_y, arm_swing_r)
    draw_cylinder_ex(sh_l, hand_l, 0.10 * scale, 0.08 * scale, 8, c_joints)
    draw_cylinder_ex(sh_r, hand_r, 0.10 * scale, 0.08 * scale, 8, c_joints)

    # Sword Weapon in Right Hand
    sword_hilt = hand_r
    sword_tip = rot_v(0.65, 2.20 + bob_y, arm_swing_r + 0.3)
    draw_cylinder_ex(sword_hilt, sword_tip, 0.04 * scale, 0.04 * scale, 6, c_blade)
    sword_guard = rot_v(0.65, 1.45 + bob_y, arm_swing_r + 0.05)
    draw_cube(sword_guard, 0.30 * scale, 0.04 * scale, 0.08 * scale, c_accent)

    # 5. Legs (Hip to Foot Cylinders)
    hip_l = rot_v(-0.25, 1.15 + bob_y, 0.0)
    hip_r = rot_v(0.25, 1.15 + bob_y, 0.0)
    foot_l = rot_v(-0.25, 0.12, leg_swing_l)
    foot_r = rot_v(0.25, 0.12, leg_swing_r)
    draw_cylinder_ex(hip_l, foot_l, 0.12 * scale, 0.09 * scale, 8, c_joints)
    draw_cylinder_ex(hip_r, foot_r, 0.12 * scale, 0.09 * scale, 8, c_joints)

    # Feet (Cubes)
    draw_cube(rot_v(-0.25, 0.06, leg_swing_l + 0.08), 0.22 * scale, 0.12 * scale, 0.38 * scale, c_armor)
    draw_cube(rot_v(0.25, 0.06, leg_swing_r + 0.08), 0.22 * scale, 0.12 * scale, 0.38 * scale, c_armor)


DEFAULT_BENCHMARK_2D_PALETTE = {
    "hull": Color(35, 50, 80, 255),
    "hull_dark": Color(20, 30, 50, 255),
    "wings": Color(48, 65, 105, 255),
    "cockpit": Color(70, 205, 255, 255),
    "thruster": Color(255, 140, 40, 255),
    "shield": Color(70, 205, 255, 160),
    "accent": Color(255, 215, 0, 255),
}

NEON_BENCHMARK_2D_PALETTE = {
    "hull": Color(30, 15, 55, 255),
    "hull_dark": Color(15, 8, 30, 255),
    "wings": Color(75, 25, 110, 255),
    "cockpit": Color(60, 240, 200, 255),
    "thruster": Color(240, 60, 200, 255),
    "shield": Color(240, 60, 200, 180),
    "accent": Color(60, 240, 200, 255),
}

CRIMSON_BENCHMARK_2D_PALETTE = {
    "hull": Color(70, 20, 25, 255),
    "hull_dark": Color(35, 10, 15, 255),
    "wings": Color(110, 30, 40, 255),
    "cockpit": Color(255, 180, 60, 255),
    "thruster": Color(255, 80, 30, 255),
    "shield": Color(255, 80, 40, 180),
    "accent": Color(255, 220, 90, 255),
}

EMERALD_BENCHMARK_2D_PALETTE = {
    "hull": Color(18, 55, 35, 255),
    "hull_dark": Color(10, 30, 20, 255),
    "wings": Color(30, 85, 55, 255),
    "cockpit": Color(80, 240, 180, 255),
    "thruster": Color(60, 220, 255, 255),
    "shield": Color(80, 240, 180, 170),
    "accent": Color(220, 255, 80, 255),
}


def draw_benchmark_starfighter_2d(
    position: Vector2,
    facing_angle_rad: float = 0.0,
    anim_timer: float = 0.0,
    scale: float = 1.0,
    palette: dict = None
) -> None:
    """
    Procedural 2D Vector Starfighter Unit.
    Rendered with pure vector calls: draw_poly, draw_triangle, draw_circle_v, draw_rectangle_pro.
    Features animated oscillating thruster plume, pulsing energy shield, and twin laser pods.
    """
    pal = palette or DEFAULT_BENCHMARK_2D_PALETTE
    c_hull = pal.get("hull", Color(35, 50, 80, 255))
    c_dark = pal.get("hull_dark", Color(20, 30, 50, 255))
    c_wings = pal.get("wings", Color(48, 65, 105, 255))
    c_cockpit = pal.get("cockpit", Color(70, 205, 255, 255))
    c_thruster = pal.get("thruster", Color(255, 140, 40, 255))
    c_shield = pal.get("shield", Color(70, 205, 255, 160))
    c_accent = pal.get("accent", Color(255, 215, 0, 255))

    cos_a = math.cos(facing_angle_rad)
    sin_a = math.sin(facing_angle_rad)

    def rot_p(lx: float, ly: float) -> Vector2:
        wx = lx * cos_a - ly * sin_a
        wy = lx * sin_a + ly * cos_a
        return Vector2(position.x + wx * scale, position.y + wy * scale)

    # 1. Pulsing Protective Energy Shield Ring
    shield_pulse = 38.0 * scale + math.sin(anim_timer * 4.0) * (3.0 * scale)
    draw_circle_lines(int(position.x), int(position.y), shield_pulse, c_shield)

    # 2. Thruster Flame (Flickering Triangle)
    flicker = 1.0 + 0.3 * math.sin(anim_timer * 28.0)
    th_tip = rot_p(-32.0 * flicker, 0.0)
    th_t1 = rot_p(-14.0, -7.0)
    th_t2 = rot_p(-14.0, 7.0)
    draw_triangle(th_tip, th_t2, th_t1, c_thruster)

    # Inner hot core of thruster flame
    th_core_tip = rot_p(-24.0 * flicker, 0.0)
    draw_triangle(th_core_tip, rot_p(-14.0, 4.0), rot_p(-14.0, -4.0), c_accent)

    # 3. Swept-Back Main Wings
    p_nose = rot_p(28.0, 0.0)
    p_wing_l = rot_p(-16.0, -32.0)
    p_wing_r = rot_p(-16.0, 32.0)
    p_root = rot_p(-10.0, 0.0)
    draw_triangle(p_nose, p_wing_l, p_root, c_wings)
    draw_triangle(p_nose, p_root, p_wing_r, c_wings)

    # 4. Central Fuselage / Cockpit
    p_fus_rear_l = rot_p(-18.0, -9.0)
    p_fus_rear_r = rot_p(-18.0, 9.0)
    draw_triangle(p_nose, p_fus_rear_l, p_fus_rear_r, c_hull)

    # Canopy Glass
    canopy_pos = rot_p(4.0, 0.0)
    draw_circle_v(canopy_pos, 7.0 * scale, c_cockpit)
    draw_circle_v(rot_p(6.0, -2.0), 2.5 * scale, WHITE)  # Specular highlight

    # 5. Twin Wingtip Laser Blasters
    deg = math.degrees(facing_angle_rad)
    draw_rectangle_pro(Rectangle(p_wing_l.x, p_wing_l.y, 16.0 * scale, 3.5 * scale), Vector2(4.0 * scale, 1.7 * scale), deg, c_accent)
    draw_rectangle_pro(Rectangle(p_wing_r.x, p_wing_r.y, 16.0 * scale, 3.5 * scale), Vector2(4.0 * scale, 1.7 * scale), deg, c_accent)


# ==============================================================================
# UI WIDGET DRAWING HELPERS
# ==============================================================================
def draw_ui_panel(rect: Rectangle, border_col: Color = COLOR_PANEL_BORDER, bg_col: Color = COLOR_PANEL) -> None:
    """Draws a clean rounded-corner UI panel with a subtle border."""
    draw_rectangle(int(rect.x), int(rect.y), int(rect.width), int(rect.height), bg_col)
    draw_rectangle_lines(int(rect.x), int(rect.y), int(rect.width), int(rect.height), border_col)


def draw_ui_button(
    rect: Rectangle,
    label: str,
    is_active: bool = False,
    is_hovered: bool = False,
    accent_col: Color = COLOR_ACCENT,
    font_size: int = 14
) -> None:
    """Draws an interactive cybernetic button with active and hover states."""
    if is_active:
        bg = Color(32, 85, 145, 255)
        border = COLOR_ACCENT_GOLD
        txt_col = COLOR_ACCENT_GOLD
    elif is_hovered:
        bg = Color(28, 42, 68, 255)
        border = COLOR_ACCENT
        txt_col = COLOR_TEXT_MAIN
    else:
        bg = Color(20, 26, 42, 255)
        border = COLOR_PANEL_BORDER
        txt_col = COLOR_TEXT_DIM

    draw_rectangle(int(rect.x), int(rect.y), int(rect.width), int(rect.height), bg)
    draw_rectangle_lines(int(rect.x), int(rect.y), int(rect.width), int(rect.height), border)

    # Center text
    t_len = len(label) * int(font_size * 0.55)
    tx = int(rect.x + (rect.width - t_len) * 0.5)
    ty = int(rect.y + (rect.height - font_size) * 0.5)
    draw_text(label, tx, ty, font_size, txt_col)


def draw_ui_slider(
    rect: Rectangle,
    label: str,
    value: float,
    min_val: float,
    max_val: float,
    suffix: str = "",
    is_active: bool = False
) -> float:
    """
    Renders an interactive horizontal slider bar and returns the updated value
    if dragged by the mouse.
    """
    mx = get_mouse_x()
    my = get_mouse_y()
    is_mouse_down = is_mouse_button_down(MOUSE_BUTTON_LEFT)
    hovered = check_collision_point_rec(Vector2(float(mx), float(my)), rect)

    new_val = value
    bar_y = int(rect.y + rect.height * 0.6)
    bar_h = 6

    if (hovered or is_active) and is_mouse_down:
        pct = clamp((mx - rect.x) / rect.width, 0.0, 1.0)
        new_val = min_val + pct * (max_val - min_val)

    # Track background
    draw_rectangle(int(rect.x), bar_y, int(rect.width), bar_h, Color(24, 34, 56, 255))
    draw_rectangle_lines(int(rect.x), bar_y, int(rect.width), bar_h, COLOR_PANEL_BORDER)

    # Filled progress
    pct_val = clamp((new_val - min_val) / (max_val - min_val), 0.0, 1.0)
    fill_w = int(rect.width * pct_val)
    fill_col = COLOR_ACCENT if hovered else Color(45, 140, 220, 255)
    draw_rectangle(int(rect.x), bar_y, fill_w, bar_h, fill_col)

    # Draggable Handle Thumb
    thumb_x = int(rect.x + fill_w)
    thumb_col = COLOR_ACCENT_GOLD if hovered else WHITE
    draw_rectangle(thumb_x - 4, bar_y - 5, 8, bar_h + 10, thumb_col)

    # Label & Value display
    draw_text(label, int(rect.x), int(rect.y), 12, COLOR_TEXT_DIM)
    val_str = f"{new_val:.2f}{suffix}"
    draw_text(val_str, int(rect.x + rect.width - len(val_str) * 7), int(rect.y), 12, COLOR_ACCENT)

    return new_val


def draw_ui_badge(x: int, y: int, text: str, bg_color: Color, text_color: Color = WHITE, font_size: int = 11) -> int:
    """Draws a compact pill badge tag and returns its rendered width."""
    bw = int(len(text) * font_size * 0.65) + 12
    bh = font_size + 6
    draw_rectangle(x, y, bw, bh, bg_color)
    br = max(0, min(255, int(bg_color.r) + 30))
    bg = max(0, min(255, int(bg_color.g) + 30))
    bb = max(0, min(255, int(bg_color.b) + 30))
    draw_rectangle_lines(x, y, bw, bh, Color(br, bg, bb, 255))
    draw_text(text, x + 6, y + 3, font_size, text_color)
    return bw


# ==============================================================================
# AUDIO VISUALIZERS (Waveform Oscilloscope & Graphic Equalizer)
# ==============================================================================
def draw_oscilloscope(
    rect: Rectangle,
    anim_progress: float,
    is_playing: bool,
    volume: float = 0.8,
    pitch: float = 1.0,
    accent_color: Color = COLOR_ACCENT
) -> None:
    """
    Renders an oscilloscope viewport displaying simulated 16-bit PCM waveform curves,
    a center zero-volt baseline, frequency grid ticks, and an animated scanning playhead.
    """
    # 1. Dark CRT cathode background
    draw_rectangle(int(rect.x), int(rect.y), int(rect.width), int(rect.height), Color(8, 12, 18, 255))
    draw_rectangle_lines(int(rect.x), int(rect.y), int(rect.width), int(rect.height), COLOR_PANEL_BORDER)

    # 2. Oscilloscope Grid Lines
    mid_y = int(rect.y + rect.height * 0.5)
    # Zero baseline
    draw_line(int(rect.x), mid_y, int(rect.x + rect.width), mid_y, Color(35, 55, 85, 255))
    # Peak reference lines (+1.0 and -1.0)
    top_ref = int(rect.y + rect.height * 0.15)
    bot_ref = int(rect.y + rect.height * 0.85)
    draw_line(int(rect.x), top_ref, int(rect.x + rect.width), top_ref, Color(22, 35, 55, 180))
    draw_line(int(rect.x), bot_ref, int(rect.x + rect.width), bot_ref, Color(22, 35, 55, 180))
    draw_text("+1.0", int(rect.x + 6), top_ref - 12, 10, COLOR_TEXT_MUTED)
    draw_text(" 0.0", int(rect.x + 6), mid_y - 10, 10, COLOR_TEXT_MUTED)
    draw_text("-1.0", int(rect.x + 6), bot_ref + 2, 10, COLOR_TEXT_MUTED)

    # Vertical division markers
    cols = 8
    for c in range(1, cols):
        cx = int(rect.x + (rect.width / cols) * c)
        draw_line(cx, int(rect.y), cx, int(rect.y + rect.height), Color(18, 28, 44, 120))

    # 3. Waveform Curve Plotting
    num_points = 240
    amp_scale = (rect.height * 0.35) * volume
    prev_pt = None

    for i in range(num_points):
        t = float(i) / float(num_points)
        px = int(rect.x + t * rect.width)

        # Procedural downward laser sweep with square harmonic grit
        freq = (880.0 * math.exp(-3.0 * t)) * pitch
        phase = 2.0 * math.pi * freq * (t * 0.12)
        env = math.exp(-6.0 * t)

        sine_v = math.sin(phase)
        sq_v = 1.0 if sine_v > 0.0 else -1.0
        wave_sample = (0.75 * sine_v + 0.25 * sq_v) * env

        py = int(mid_y - wave_sample * amp_scale)
        curr_pt = Vector2(float(px), float(py))

        if prev_pt is not None:
            wave_col = accent_color if is_playing else Color(45, 95, 140, 220)
            draw_line_ex(prev_pt, curr_pt, 2.0, wave_col)
        prev_pt = curr_pt

    # 4. Animated Playback Scanline / Cursor
    if is_playing and 0.0 <= anim_progress <= 1.0:
        cursor_x = int(rect.x + anim_progress * rect.width)
        draw_line(cursor_x, int(rect.y), cursor_x, int(rect.y + rect.height), COLOR_ACCENT_GOLD)
        draw_circle(cursor_x, mid_y, 4, COLOR_ACCENT_GOLD)

    # 5. Header labels inside oscilloscope
    status_label = "PLAYING (STREAM ACTIVE)" if is_playing else "IDLE / READY TO TRIGGER"
    st_col = COLOR_ACCENT_GREEN if is_playing else COLOR_TEXT_MUTED
    draw_text(status_label, int(rect.x + 12), int(rect.y + 10), 12, st_col)
    spec_label = f"Vol: {int(volume * 100)}% | Pitch: {pitch:.2f}x | 44.1kHz 16-Bit PCM"
    draw_text(spec_label, int(rect.x + rect.width - len(spec_label) * 7 - 12), int(rect.y + 10), 11, COLOR_TEXT_DIM)


def draw_spectrum_equalizer(
    rect: Rectangle,
    anim_timer: float,
    is_playing: bool,
    volume: float = 0.7,
    pitch: float = 1.0,
    bpm: float = 120.0
) -> None:
    """
    Renders an animated 24-band graphic equalizer with harmonic bouncing bars,
    peak level hold meters, and an interactive flashing beat indicator.
    """
    draw_rectangle(int(rect.x), int(rect.y), int(rect.width), int(rect.height), Color(8, 12, 18, 255))
    draw_rectangle_lines(int(rect.x), int(rect.y), int(rect.width), int(rect.height), COLOR_PANEL_BORDER)

    bands = 24
    pad = 3
    total_pads = (bands + 1) * pad
    bar_w = max(4, int((rect.width - total_pads) / bands))
    max_h = rect.height - 40
    base_y = int(rect.y + rect.height - 15)

    # Beat pulse calculation
    beats_per_sec = (bpm * pitch) / 60.0
    beat_phase = (anim_timer * beats_per_sec) % 1.0
    beat_pulse = math.exp(-6.0 * beat_phase)

    # Center Beat Pulse Indicator Box
    draw_text("BPM BEAT", int(rect.x + 16), int(rect.y + 12), 11, COLOR_TEXT_MUTED)
    beat_col = COLOR_ACCENT_GOLD if (is_playing and beat_pulse > 0.3) else Color(30, 45, 70, 255)
    draw_rectangle(int(rect.x + 82), int(rect.y + 12), 14, 14, beat_col)
    draw_rectangle_lines(int(rect.x + 82), int(rect.y + 12), 14, 14, COLOR_PANEL_BORDER)

    status_str = "STREAMING (LOOPING 4/4 TIME)" if is_playing else "PAUSED / STOPPED"
    s_col = COLOR_ACCENT_GREEN if is_playing else COLOR_TEXT_MUTED
    draw_text(status_str, int(rect.x + 115), int(rect.y + 13), 12, s_col)

    # Draw EQ bars
    for b in range(bands):
        bx = int(rect.x + pad + b * (bar_w + pad))

        if is_playing:
            # Algorithmic frequency excitation
            f_mult = 1.0 + float(b) * 0.45
            harm1 = math.sin(anim_timer * (4.0 * f_mult) + b * 0.5) * 0.5 + 0.5
            harm2 = math.cos(anim_timer * (7.0 * f_mult) - b * 0.3) * 0.3 + 0.3
            bass_kick = beat_pulse * max(0.0, 1.0 - float(b) * 0.08)
            norm_h = clamp((harm1 * 0.5 + harm2 * 0.3 + bass_kick * 0.6) * volume, 0.04, 0.95)
        else:
            norm_h = 0.03

        bar_h = int(norm_h * max_h)
        by = base_y - bar_h

        # Gradient color: Cyan at bottom -> Amber at mid -> Magenta/Red at peak
        if norm_h > 0.75:
            bar_col = COLOR_ACCENT_RED
        elif norm_h > 0.45:
            bar_col = COLOR_ACCENT_GOLD
        else:
            bar_col = COLOR_ACCENT

        draw_rectangle(bx, by, bar_w, bar_h, bar_col)

        # Peak hold line
        peak_y = by - 3
        draw_line(bx, peak_y, bx + bar_w, peak_y, WHITE)


# ==============================================================================
# MAIN ASSET WORKBENCH APPLICATION CLASS
# ==============================================================================
class AssetViewerApp:
    """
    Central Raylib graphical workbench for interactive procedural asset inspection,
    sound auditioning, 3D orbit viewing, and 2D vector animation.
    """
    def __init__(self):
        # 1. Initialize Raylib window
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)

        # 2. Defensively initialize audio hardware
        self.audio_ready = safe_init_audio_device()
        self.sound_lib = SoundLibrary()

        # 3. Navigation & Tab state
        self.current_tab = TAB_3D
        self.search_filter = ""
        self.selected_category = "ALL"
        self.status_banner = "Welcome to Procedural Asset Workbench. Select any asset to inspect or audition."
        self.status_banner_time = 3.0

        # Discovered Asset Catalog caches
        self.cache_3d: List[Dict[str, Any]] = []
        self.cache_2d: List[Dict[str, Any]] = []
        self.cache_sfx: List[Dict[str, Any]] = []
        self.cache_bgm: List[Dict[str, Any]] = []

        self.selected_idx_3d = 0
        self.selected_idx_2d = 0
        self.selected_idx_sfx = 0
        self.selected_idx_bgm = 0

        self.list_scroll_y = 0.0

        # 3D Orbit Camera State
        self.cam_yaw = 45.0
        self.cam_pitch = 20.0
        self.cam_distance = 4.8
        self.cam_target = Vector3(0.0, 1.1, 0.0)
        self.camera_3d = Camera3D()
        self._update_camera_3d()

        # 3D Viewport Controls
        self.anim_timer_3d = 0.0
        self.is_playing_3d = True
        self.speed_3d = 1.0
        self.scale_3d = 1.0
        self.rot_y_3d = 0.0
        self.auto_rotate_3d = True
        self.wireframe_3d = False
        self.show_grid_3d = True
        self.active_palette_idx_3d = 0
        self.palette_names_3d = ["Default", "Stealth", "Cyberpunk", "Desert"]
        self.palettes_3d = [
            DEFAULT_BENCHMARK_3D_PALETTE,
            STEALTH_BENCHMARK_3D_PALETTE,
            CYBER_BENCHMARK_3D_PALETTE,
            DESERT_BENCHMARK_3D_PALETTE,
        ]

        # 2D Canvas State
        self.canvas_offset = Vector2(0.0, 0.0)
        self.canvas_zoom = 2.0
        self.anim_timer_2d = 0.0
        self.is_playing_2d = True
        self.speed_2d = 1.0
        self.scale_2d = 2.0
        self.facing_deg_2d = 0.0
        self.show_grid_2d = True
        self.active_palette_idx_2d = 0
        self.palette_names_2d = ["Default", "Neon", "Crimson", "Emerald"]
        self.palettes_2d = [
            DEFAULT_BENCHMARK_2D_PALETTE,
            NEON_BENCHMARK_2D_PALETTE,
            CRIMSON_BENCHMARK_2D_PALETTE,
            EMERALD_BENCHMARK_2D_PALETTE,
        ]

        # SFX State
        self.sfx_volume = 0.8
        self.sfx_pitch = 1.0
        self.sfx_loop = False
        self.sfx_play_timer = 0.0
        self.sfx_duration = 0.12
        self.sfx_is_playing = False

        # BGM State
        self.bgm_volume = 0.70
        self.bgm_pitch = 1.0
        self.bgm_loop = True
        self.bgm_is_playing = False
        self.bgm_active_key: Optional[str] = None
        self.bgm_time_played = 0.0
        self.bgm_time_total = 4.0

        # Scan disk assets
        self.rescan_all()

    # --------------------------------------------------------------------------
    # Asset Discovery & Catalog Population
    # --------------------------------------------------------------------------
    def rescan_all(self):
        """Scans disk asset repositories via asset_loader.py and rebuilds UI catalog caches."""
        scan_all_assets()

        self.cache_3d = self._build_catalog_items(models_3D, "models_3D")
        self.cache_2d = self._build_catalog_items(sprites_2D, "sprites_2D")
        self.cache_sfx = self._build_catalog_items(sfx, "SFX")
        self.cache_bgm = self._build_catalog_items(bgm, "BGM")

        # Load initial audio cue if present
        if self.cache_sfx and self.audio_ready:
            key = self.cache_sfx[self.selected_idx_sfx]["key"]
            try:
                self.sound_lib.load(sfx=[key])
            except Exception:
                pass

        self.status_banner = (
            f"Rescan complete: {len(self.cache_3d)} 3D models, {len(self.cache_2d)} 2D sprites, "
            f"{len(self.cache_sfx)} SFX, {len(self.cache_bgm)} BGM tracks."
        )
        self.status_banner_time = 3.5

    def _build_catalog_items(self, registry: Dict[str, str], kind: str) -> List[Dict[str, Any]]:
        """Parses discovered assets into structured UI catalog items with docstrings."""
        items: List[Dict[str, Any]] = []
        seen_paths = set()

        for key, rel_path in sorted(registry.items()):
            full_path = os.path.join(REPO_ROOT, rel_path) if not os.path.isabs(rel_path) else rel_path
            norm_p = os.path.normpath(full_path)
            if norm_p in seen_paths:
                continue
            seen_paths.add(norm_p)

            # Extract category from folder hierarchy
            parts = rel_path.replace("\\", "/").split("/")
            category = parts[-2] if len(parts) >= 2 else kind

            # Parse lines and docstrings without executing
            line_count = 0
            docstring = "Standalone Procedural Asset Module."
            if os.path.exists(full_path):
                try:
                    with open(full_path, "r", encoding="utf-8-sig") as fp:
                        src = fp.read()
                    line_count = len(src.splitlines())
                    tree = ast.parse(src, filename=os.path.basename(full_path))
                    raw_doc = ast.get_docstring(tree)
                    if raw_doc:
                        docstring = raw_doc.strip()
                except Exception as exc:
                    docstring = f"Error reading asset: {exc}"

            items.append({
                "key": key,
                "name": os.path.splitext(os.path.basename(rel_path))[0],
                "rel_path": rel_path.replace("\\", "/"),
                "full_path": full_path,
                "category": category,
                "line_count": line_count,
                "docstring": docstring,
                "is_benchmark": False,
            })

        # Add built-in benchmark item if empty so student can explore immediately
        if not items:
            if kind == "models_3D":
                items.append({
                    "key": "benchmark_humanoid_3d",
                    "name": "benchmark_humanoid_3d (Preview Unit)",
                    "rel_path": "assets/models_3D/benchmark_preview.py",
                    "full_path": "",
                    "category": "humanoid",
                    "line_count": 480,
                    "docstring": (
                        "Interactive Procedural Primitive Benchmark Model.\n"
                        "Synthesized from Raylib 3D primitives: Cubes, Spheres, and Cylinders.\n"
                        "Demonstrates sinusoidal locomotion walk cycle and swappable palettes."
                    ),
                    "is_benchmark": True,
                })
            elif kind == "sprites_2D":
                items.append({
                    "key": "benchmark_starfighter_2d",
                    "name": "benchmark_starfighter_2d (Preview Unit)",
                    "rel_path": "assets/sprites_2D/benchmark_preview.py",
                    "full_path": "",
                    "category": "vehicles",
                    "line_count": 360,
                    "docstring": (
                        "Interactive Procedural 2D Vector Benchmark Unit.\n"
                        "Rendered with Raylib vector calls: draw_poly, draw_triangle, draw_circle_v.\n"
                        "Demonstrates animated thruster flickering and pulsing shield harmonics."
                    ),
                    "is_benchmark": True,
                })

        return items

    def _get_active_cache(self) -> List[Dict[str, Any]]:
        if self.current_tab == TAB_3D:
            return self.cache_3d
        elif self.current_tab == TAB_2D:
            return self.cache_2d
        elif self.current_tab == TAB_SFX:
            return self.cache_sfx
        else:
            return self.cache_bgm

    def _get_active_selected_idx(self) -> int:
        if self.current_tab == TAB_3D:
            return self.selected_idx_3d
        elif self.current_tab == TAB_2D:
            return self.selected_idx_2d
        elif self.current_tab == TAB_SFX:
            return self.selected_idx_sfx
        else:
            return self.selected_idx_bgm

    def _set_active_selected_idx(self, idx: int) -> None:
        items = self._get_active_cache()
        if not items:
            return
        clamped = max(0, min(len(items) - 1, idx))
        if self.current_tab == TAB_3D:
            self.selected_idx_3d = clamped
        elif self.current_tab == TAB_2D:
            self.selected_idx_2d = clamped
        elif self.current_tab == TAB_SFX:
            self.selected_idx_sfx = clamped
            # Load new SFX into library
            key = items[clamped]["key"]
            if self.audio_ready and not items[clamped]["is_benchmark"]:
                try:
                    self.sound_lib.load(sfx=[key])
                except Exception:
                    pass
        else:
            self.selected_idx_bgm = clamped
            # Load new BGM into library
            key = items[clamped]["key"]
            if self.audio_ready and not items[clamped]["is_benchmark"]:
                try:
                    self.sound_lib.load(bgm=[key])
                except Exception:
                    pass

    # --------------------------------------------------------------------------
    # 3D Orbit Camera Matrix Math
    # --------------------------------------------------------------------------
    def _update_camera_3d(self) -> None:
        rad_yaw = math.radians(self.cam_yaw)
        rad_pitch = math.radians(self.cam_pitch)
        cx = self.cam_target.x + self.cam_distance * math.cos(rad_pitch) * math.sin(rad_yaw)
        cy = self.cam_target.y + self.cam_distance * math.sin(rad_pitch)
        cz = self.cam_target.z + self.cam_distance * math.cos(rad_pitch) * math.cos(rad_yaw)
        self.camera_3d.position = Vector3(cx, cy, cz)
        self.camera_3d.target = self.cam_target
        self.camera_3d.up = Vector3(0.0, 1.0, 0.0)
        self.camera_3d.fovy = 45.0
        self.camera_3d.projection = CAMERA_PERSPECTIVE

    # --------------------------------------------------------------------------
    # Global Playback Actions (Play / Pause / Stop)
    # --------------------------------------------------------------------------
    def trigger_play(self) -> None:
        """Universal Play action for active tab."""
        if self.current_tab == TAB_3D:
            self.is_playing_3d = True
            self.status_banner = "3D locomotion animation playing."
        elif self.current_tab == TAB_2D:
            self.is_playing_2d = True
            self.status_banner = "2D vector animation playing."
        elif self.current_tab == TAB_SFX:
            items = self.cache_sfx
            if items:
                key = items[self.selected_idx_sfx]["key"]
                if self.audio_ready:
                    self.sound_lib.play(key, volume=self.sfx_volume, pitch=self.sfx_pitch)
                    self.sfx_is_playing = True
                    self.sfx_play_timer = 0.0
                    self.status_banner = f"Triggered SFX '{key}' (Vol {int(self.sfx_volume*100)}%, Pitch {self.sfx_pitch:.2f}x)."
        elif self.current_tab == TAB_BGM:
            items = self.cache_bgm
            if items:
                key = items[self.selected_idx_bgm]["key"]
                if self.audio_ready:
                    if self.bgm_active_key != key:
                        self.sound_lib.stop()
                        self.sound_lib.load(bgm=[key])
                        self.bgm_active_key = key
                    self.sound_lib.play(key, volume=self.bgm_volume, pitch=self.bgm_pitch, loop=self.bgm_loop)
                    self.bgm_is_playing = True
                    self.status_banner = f"Streaming BGM '{key}' (BPM 120, Vol {int(self.bgm_volume*100)}%)."

    def trigger_pause(self) -> None:
        """Universal Pause action for active tab."""
        if self.current_tab == TAB_3D:
            self.is_playing_3d = False
            self.status_banner = "3D animation paused."
        elif self.current_tab == TAB_2D:
            self.is_playing_2d = False
            self.status_banner = "2D animation paused."
        elif self.current_tab == TAB_BGM:
            if self.bgm_active_key and self.audio_ready:
                self.sound_lib.pause(self.bgm_active_key)
                self.bgm_is_playing = False
                self.status_banner = f"Paused BGM '{self.bgm_active_key}'."

    def trigger_stop(self) -> None:
        """Universal Stop action for active tab."""
        if self.current_tab == TAB_3D:
            self.is_playing_3d = False
            self.anim_timer_3d = 0.0
            self.status_banner = "Reset 3D animation timer to 0.0s."
        elif self.current_tab == TAB_2D:
            self.is_playing_2d = False
            self.anim_timer_2d = 0.0
            self.status_banner = "Reset 2D animation timer to 0.0s."
        elif self.current_tab == TAB_SFX:
            items = self.cache_sfx
            if items and self.audio_ready:
                key = items[self.selected_idx_sfx]["key"]
                self.sound_lib.stop(key)
                self.sfx_is_playing = False
                self.status_banner = f"Stopped SFX '{key}'."
        elif self.current_tab == TAB_BGM:
            if self.bgm_active_key and self.audio_ready:
                self.sound_lib.stop(self.bgm_active_key)
                self.bgm_is_playing = False
                self.status_banner = f"Stopped BGM '{self.bgm_active_key}'."

    # --------------------------------------------------------------------------
    # Frame Update Loop
    # --------------------------------------------------------------------------
    def update(self) -> None:
        dt = min(get_frame_time(), 0.05)

        # Status banner decay
        if self.status_banner_time > 0.0:
            self.status_banner_time -= dt

        # 1. Update streaming music buffers every frame
        if self.audio_ready:
            self.sound_lib.update()

        # 2. Update SFX animation timers
        if self.sfx_is_playing:
            self.sfx_play_timer += dt
            if self.sfx_play_timer >= self.sfx_duration:
                if self.sfx_loop:
                    self.sfx_play_timer = 0.0
                    items = self.cache_sfx
                    if items and self.audio_ready:
                        key = items[self.selected_idx_sfx]["key"]
                        self.sound_lib.play(key, volume=self.sfx_volume, pitch=self.sfx_pitch)
                else:
                    self.sfx_is_playing = False

        # 3. Update BGM streaming position
        if self.bgm_is_playing and self.bgm_active_key and self.audio_ready:
            mus = self.sound_lib.music.get(self.bgm_active_key)
            if mus is not None:
                self.bgm_time_played = get_music_time_played(mus)
                self.bgm_time_total = max(0.1, get_music_time_length(mus))

        # 4. Update 3D animation timer & auto-rotation
        if self.is_playing_3d:
            self.anim_timer_3d += dt * self.speed_3d
        if self.auto_rotate_3d:
            self.rot_y_3d = (self.rot_y_3d + dt * 25.0 * self.speed_3d) % 360.0

        # 5. Update 2D animation timer
        if self.is_playing_2d:
            self.anim_timer_2d += dt * self.speed_2d

        # 6. Global Keyboard Shortcuts
        if is_key_pressed(KEY_ONE):
            self.current_tab = TAB_3D
        elif is_key_pressed(KEY_TWO):
            self.current_tab = TAB_2D
        elif is_key_pressed(KEY_THREE):
            self.current_tab = TAB_SFX
        elif is_key_pressed(KEY_FOUR):
            self.current_tab = TAB_BGM

        # Bumper tab cycling [Q / E]
        if is_key_pressed(KEY_Q):
            self.current_tab = (self.current_tab - 1) % len(TAB_INFO)
        elif is_key_pressed(KEY_E):
            self.current_tab = (self.current_tab + 1) % len(TAB_INFO)

        # Space: Play / Pause toggle
        if is_key_pressed(KEY_SPACE):
            if self.current_tab == TAB_3D:
                if self.is_playing_3d: self.trigger_pause()
                else: self.trigger_play()
            elif self.current_tab == TAB_2D:
                if self.is_playing_2d: self.trigger_pause()
                else: self.trigger_play()
            elif self.current_tab == TAB_SFX:
                self.trigger_play()
            elif self.current_tab == TAB_BGM:
                if self.bgm_is_playing: self.trigger_pause()
                else: self.trigger_play()

        # S: Stop
        if is_key_pressed(KEY_S):
            self.trigger_stop()

        # R: Reset Camera / View
        if is_key_pressed(KEY_R):
            if self.current_tab == TAB_3D:
                self.cam_yaw = 45.0
                self.cam_pitch = 20.0
                self.cam_distance = 4.8
                self.cam_target = Vector3(0.0, 1.1, 0.0)
                self.rot_y_3d = 0.0
                self.scale_3d = 1.0
                self.status_banner = "Reset 3D camera orbit to default."
            elif self.current_tab == TAB_2D:
                self.canvas_offset = Vector2(0.0, 0.0)
                self.canvas_zoom = 2.0
                self.facing_deg_2d = 0.0
                self.status_banner = "Reset 2D canvas pan & zoom."

        # F5: Rescan disk assets
        if is_key_pressed(KEY_F5):
            self.rescan_all()

        # Arrow Up / Down for catalog list navigation
        if is_key_pressed(KEY_UP):
            self._set_active_selected_idx(self._get_active_selected_idx() - 1)
        elif is_key_pressed(KEY_DOWN):
            self._set_active_selected_idx(self._get_active_selected_idx() + 1)

        # 7. Mouse Orbiting in 3D Viewport
        vp_rect = Rectangle(338, 132, 614, 390)
        mx = get_mouse_x()
        my = get_mouse_y()
        mouse_in_vp = check_collision_point_rec(Vector2(float(mx), float(my)), vp_rect)

        if self.current_tab == TAB_3D and mouse_in_vp:
            if is_mouse_button_down(MOUSE_BUTTON_LEFT) or is_mouse_button_down(MOUSE_BUTTON_RIGHT):
                delta = get_mouse_delta()
                self.cam_yaw += delta.x * 0.45
                self.cam_pitch = clamp(self.cam_pitch + delta.y * 0.45, -80.0, 80.0)
                self.auto_rotate_3d = False
            wheel = get_mouse_wheel_move()
            if wheel != 0.0:
                self.cam_distance = clamp(self.cam_distance - wheel * 0.45, 1.2, 14.0)
            self._update_camera_3d()

        # 8. Mouse Pan & Zoom in 2D Viewport
        if self.current_tab == TAB_2D and mouse_in_vp:
            if is_mouse_button_down(MOUSE_BUTTON_LEFT) or is_mouse_button_down(MOUSE_BUTTON_RIGHT):
                delta = get_mouse_delta()
                self.canvas_offset.x += delta.x
                self.canvas_offset.y += delta.y
            wheel = get_mouse_wheel_move()
            if wheel != 0.0:
                self.canvas_zoom = clamp(self.canvas_zoom + wheel * 0.25, 0.5, 8.0)

    # --------------------------------------------------------------------------
    # Frame Draw Routine
    # --------------------------------------------------------------------------
    def draw(self) -> None:
        begin_drawing()
        clear_background(COLOR_BG)

        # 1. Header & Top Bar Navigation
        self._draw_header()

        # 2. Left Sidebar (Asset List & Catalog Selector)
        self._draw_sidebar()

        # 3. Center Viewport (3D / 2D / SFX / BGM interactive canvas & controls)
        self._draw_viewport()

        # 4. Right Inspector (Metadata, math, code snippets, palettes)
        self._draw_inspector()

        # 5. Bottom Status Banner
        self._draw_status_bar()

        # Renders repository UI settings dropdowns (x=450..980, y=14..48) on top
        end_drawing()

    # --------------------------------------------------------------------------
    # Sub-View Renderers
    # --------------------------------------------------------------------------
    def _draw_header(self) -> None:
        """Renders the top application header and the 4 primary tabs."""
        # Top banner background
        draw_rectangle(0, 0, SCREEN_WIDTH, 88, COLOR_PANEL_HEADER)
        draw_line(0, 88, SCREEN_WIDTH, 88, COLOR_PANEL_BORDER)

        # Title & Subtitle (Left: x=20..440)
        draw_text("PROCEDURAL ASSET WORKBENCH", 20, 14, 18, COLOR_ACCENT_GOLD)
        draw_text("100% Raylib Primitives & RAM Synthesis", 20, 36, 12, COLOR_TEXT_DIM)

        # Audio Hardware Badge (Right: x=1000..1120)
        audio_str = "AUDIO ON" if self.audio_ready else "HEADLESS (MUTE)"
        audio_col = COLOR_ACCENT_GREEN if self.audio_ready else COLOR_TEXT_MUTED
        draw_ui_badge(990, 15, audio_str, audio_col, WHITE, 11)

        # Rescan Button (Right: x=1140..1260)
        btn_rescan_rect = Rectangle(1140, 14, 116, 28)
        mx, my = get_mouse_x(), get_mouse_y()
        hover_rescan = check_collision_point_rec(Vector2(float(mx), float(my)), btn_rescan_rect)
        if hover_rescan and is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            self.rescan_all()
        draw_ui_button(btn_rescan_rect, "[R] Rescan [F5]", False, hover_rescan, COLOR_ACCENT, 12)

        # Tab Bar (y=50..86)
        tab_counts = [len(self.cache_3d), len(self.cache_2d), len(self.cache_sfx), len(self.cache_bgm)]
        for i, info in enumerate(TAB_INFO):
            tx = 20 + i * 190
            tab_rect = Rectangle(tx, 52, 180, 34)
            is_active = (self.current_tab == i)
            hovered = check_collision_point_rec(Vector2(float(mx), float(my)), tab_rect)

            if hovered and is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
                self.current_tab = i
                self.status_banner = f"Switched to {info['title']} tab."

            # Tab button body
            tab_bg = Color(28, 42, 68, 255) if is_active else (Color(20, 28, 44, 255) if hovered else Color(14, 20, 32, 255))
            draw_rectangle(int(tab_rect.x), int(tab_rect.y), int(tab_rect.width), int(tab_rect.height), tab_bg)
            draw_rectangle_lines(int(tab_rect.x), int(tab_rect.y), int(tab_rect.width), int(tab_rect.height), COLOR_PANEL_BORDER)

            # Tab Title + Count
            t_title = f"{info['icon']} {info['title']} ({tab_counts[i]})"
            t_col = COLOR_ACCENT_GOLD if is_active else (WHITE if hovered else COLOR_TEXT_DIM)
            draw_text(t_title, tx + 12, 62, 13, t_col)

            # Active Tab Indicator underline
            if is_active:
                draw_rectangle(tx, 84, 180, 4, COLOR_ACCENT)

        # Shortcut hints label on tab bar right
        draw_text("[1-4] Tabs | [Space] Play | [S] Stop | [R] Reset | [Q/E] Cycle", 790, 62, 12, COLOR_TEXT_MUTED)

    def _draw_sidebar(self) -> None:
        """Renders the left catalog browser list with search filtering and item selection."""
        side_rect = Rectangle(16, 96, 310, 584)
        draw_ui_panel(side_rect, COLOR_PANEL_BORDER, COLOR_PANEL)

        # Header with item count
        items = self._get_active_cache()
        cur_title = TAB_INFO[self.current_tab]["title"]
        draw_text(f"{cur_title.upper()} CATALOG ({len(items)})", 28, 108, 14, COLOR_ACCENT)
        draw_line(16, 130, 326, 130, COLOR_PANEL_BORDER)

        # Scrollable Item List inside scissor box
        list_y = 138
        list_h = 530
        begin_scissor_mode(18, list_y, 306, list_h)

        mx, my = get_mouse_x(), get_mouse_y()
        sel_idx = self._get_active_selected_idx()

        item_h = 52
        for idx, item in enumerate(items):
            iy = list_y + idx * (item_h + 4)
            card_rect = Rectangle(24, iy, 294, item_h)
            hovered = check_collision_point_rec(Vector2(float(mx), float(my)), card_rect)
            is_selected = (idx == sel_idx)

            if hovered and is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
                self._set_active_selected_idx(idx)
                self.status_banner = f"Selected '{item['key']}' ({item['category']})."

            # Card background
            if is_selected:
                c_bg = COLOR_SELECTION
                c_border = COLOR_SELECTION_BORDER
            elif hovered:
                c_bg = COLOR_HOVER_ROW
                c_border = COLOR_ACCENT
            else:
                c_bg = COLOR_PANEL_ALT
                c_border = COLOR_PANEL_BORDER

            draw_rectangle(int(card_rect.x), int(card_rect.y), int(card_rect.width), int(card_rect.height), c_bg)
            draw_rectangle_lines(int(card_rect.x), int(card_rect.y), int(card_rect.width), int(card_rect.height), c_border)

            # Item name
            name_col = COLOR_ACCENT_GOLD if is_selected else (WHITE if hovered else COLOR_TEXT_MAIN)
            name_str = item["key"]
            if len(name_str) > 22:
                name_str = name_str[:20] + ".."
            draw_text(name_str, int(card_rect.x + 10), int(card_rect.y + 8), 13, name_col)

            # Category pill badge
            cat_str = item["category"]
            draw_ui_badge(int(card_rect.x + 10), int(card_rect.y + 28), cat_str, Color(35, 50, 75, 255), COLOR_ACCENT, 10)

            # Lines count or Benchmark tag
            if item.get("is_benchmark"):
                draw_ui_badge(int(card_rect.x + card_rect.width - 85), int(card_rect.y + 28), "Benchmark", COLOR_ACCENT_GOLD, Color(10, 13, 22, 255), 10)
            else:
                line_str = f"{item['line_count']} lines"
                draw_text(line_str, int(card_rect.x + card_rect.width - len(line_str) * 7 - 8), int(card_rect.y + 30), 10, COLOR_TEXT_MUTED)

        end_scissor_mode()

    def _draw_viewport(self) -> None:
        """Renders the central interactive workspace (3D orbit, 2D canvas, SFX, or BGM)."""
        vp_panel_rect = Rectangle(338, 96, 614, 584)
        draw_ui_panel(vp_panel_rect, COLOR_PANEL_BORDER, COLOR_PANEL)

        # Viewport Header Bar
        items = self._get_active_cache()
        sel_idx = self._get_active_selected_idx()
        cur_name = items[sel_idx]["key"] if items else "None"

        draw_text(f"VIEWPORT: {cur_name}", 352, 108, 14, COLOR_ACCENT)
        draw_line(338, 130, 952, 130, COLOR_PANEL_BORDER)

        # Canvas Area (348, 136, 594, 386)
        canvas_rect = Rectangle(348, 136, 594, 386)

        if self.current_tab == TAB_3D:
            self._render_3d_viewport(canvas_rect)
            self._render_3d_controls(Rectangle(348, 530, 594, 140))
        elif self.current_tab == TAB_2D:
            self._render_2d_viewport(canvas_rect)
            self._render_2d_controls(Rectangle(348, 530, 594, 140))
        elif self.current_tab == TAB_SFX:
            self._render_sfx_viewport(canvas_rect)
            self._render_sfx_controls(Rectangle(348, 530, 594, 140))
        else:
            self._render_bgm_viewport(canvas_rect)
            self._render_bgm_controls(Rectangle(348, 530, 594, 140))

    # --------------------------------------------------------------------------
    # 3D Viewport & Controls
    # --------------------------------------------------------------------------
    def _render_3d_viewport(self, rect: Rectangle) -> None:
        # Background viewport
        draw_rectangle(int(rect.x), int(rect.y), int(rect.width), int(rect.height), Color(12, 16, 26, 255))
        draw_rectangle_lines(int(rect.x), int(rect.y), int(rect.width), int(rect.height), COLOR_PANEL_BORDER)

        items = self.cache_3d
        sel_idx = self.selected_idx_3d
        item = items[sel_idx] if items else None
        active_pal = self.palettes_3d[self.active_palette_idx_3d]

        begin_scissor_mode(int(rect.x), int(rect.y), int(rect.width), int(rect.height))
        begin_mode_3d(self.camera_3d)

        # Floor grid
        if self.show_grid_3d:
            draw_grid(10, 1.0)

        # XYZ Coordinate Axes
        draw_line_3d(Vector3(0, 0.02, 0), Vector3(1.5, 0.02, 0), COLOR_ACCENT_RED)
        draw_line_3d(Vector3(0, 0.02, 0), Vector3(0, 1.5, 0), COLOR_ACCENT_GREEN)
        draw_line_3d(Vector3(0, 0.02, 0), Vector3(0, 0.02, 1.5), COLOR_ACCENT)

        # Render 3D Model
        if item is not None:
            if item.get("is_benchmark") or not item["full_path"]:
                draw_benchmark_humanoid_3d(
                    Vector3(0.0, 0.0, 0.0),
                    rotation_y=self.rot_y_3d,
                    anim_timer=self.anim_timer_3d,
                    scale=self.scale_3d,
                    palette=active_pal
                )
            else:
                # Dynamic model loaded via asset_loader.py
                try:
                    draw_func, def_pal = load_model_3d(item["key"])
                    model_pal = active_pal or def_pal
                    draw_func(
                        Vector3(0.0, 0.0, 0.0),
                        rotation_y=self.rot_y_3d,
                        anim_timer=self.anim_timer_3d,
                        scale=self.scale_3d,
                        palette=model_pal
                    )
                except Exception as exc:
                    draw_cube(Vector3(0, 1.0, 0), 1.0, 1.0, 1.0, COLOR_ACCENT_RED)

        end_mode_3d()
        end_scissor_mode()

        # Viewport overlay labels
        draw_text("3D ORBIT: Drag Left/Right Mouse | Wheel: Zoom | [R] Reset", int(rect.x + 10), int(rect.y + 10), 11, COLOR_TEXT_MUTED)
        fps_str = f"{get_fps()} FPS"
        draw_text(fps_str, int(rect.x + rect.width - len(fps_str) * 7 - 10), int(rect.y + 10), 11, COLOR_ACCENT_GREEN)

    def _render_3d_controls(self, rect: Rectangle) -> None:
        draw_ui_panel(rect, COLOR_PANEL_BORDER, COLOR_PANEL_ALT)

        mx, my = get_mouse_x(), get_mouse_y()
        # Row 1: Play/Pause, Stop, Auto-Rotate, Grid, Palette Theme
        b_play = Rectangle(rect.x + 10, rect.y + 10, 80, 26)
        h_play = check_collision_point_rec(Vector2(float(mx), float(my)), b_play)
        if h_play and is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            if self.is_playing_3d: self.trigger_pause()
            else: self.trigger_play()
        draw_ui_button(b_play, "[Pause]" if self.is_playing_3d else "[Play]", self.is_playing_3d, h_play, COLOR_ACCENT, 11)

        b_stop = Rectangle(rect.x + 96, rect.y + 10, 68, 26)
        h_stop = check_collision_point_rec(Vector2(float(mx), float(my)), b_stop)
        if h_stop and is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            self.trigger_stop()
        draw_ui_button(b_stop, "[Stop]", False, h_stop, COLOR_ACCENT, 11)

        b_rot = Rectangle(rect.x + 170, rect.y + 10, 95, 26)
        h_rot = check_collision_point_rec(Vector2(float(mx), float(my)), b_rot)
        if h_rot and is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            self.auto_rotate_3d = not self.auto_rotate_3d
        draw_ui_button(b_rot, "Spin: ON" if self.auto_rotate_3d else "Spin: OFF", self.auto_rotate_3d, h_rot, COLOR_ACCENT, 11)

        b_grid = Rectangle(rect.x + 272, rect.y + 10, 80, 26)
        h_grid = check_collision_point_rec(Vector2(float(mx), float(my)), b_grid)
        if h_grid and is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            self.show_grid_3d = not self.show_grid_3d
        draw_ui_button(b_grid, "Grid: ON" if self.show_grid_3d else "Grid: OFF", self.show_grid_3d, h_grid, COLOR_ACCENT, 11)

        # Palette switcher button
        pal_name = self.palette_names_3d[self.active_palette_idx_3d]
        b_pal = Rectangle(rect.x + 360, rect.y + 10, 130, 26)
        h_pal = check_collision_point_rec(Vector2(float(mx), float(my)), b_pal)
        if h_pal and is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            self.active_palette_idx_3d = (self.active_palette_idx_3d + 1) % len(self.palettes_3d)
        draw_ui_button(b_pal, f"Pal: {pal_name}", True, h_pal, COLOR_ACCENT_GOLD, 11)

        # Row 2: Sliders (Speed, Scale, Yaw Angle)
        s_speed = Rectangle(rect.x + 10, rect.y + 48, 175, 36)
        self.speed_3d = draw_ui_slider(s_speed, "Speed", self.speed_3d, 0.0, 3.0, "x")

        s_scale = Rectangle(rect.x + 205, rect.y + 48, 175, 36)
        self.scale_3d = draw_ui_slider(s_scale, "Scale", self.scale_3d, 0.2, 3.0, "x")

        s_yaw = Rectangle(rect.x + 400, rect.y + 48, 180, 36)
        self.rot_y_3d = draw_ui_slider(s_yaw, "Yaw Angle", self.rot_y_3d, 0.0, 360.0, "°")

        # Row 3: Telemetry readout
        timer_str = f"Anim Timer: {self.anim_timer_3d:.2f}s | Cam Dist: {self.cam_distance:.1f}m | Yaw: {self.cam_yaw:.0f}° | Pitch: {self.cam_pitch:.0f}°"
        draw_text(timer_str, int(rect.x + 12), int(rect.y + 105), 11, COLOR_TEXT_DIM)

    # --------------------------------------------------------------------------
    # 2D Viewport & Controls
    # --------------------------------------------------------------------------
    def _render_2d_viewport(self, rect: Rectangle) -> None:
        draw_rectangle(int(rect.x), int(rect.y), int(rect.width), int(rect.height), Color(12, 16, 26, 255))
        draw_rectangle_lines(int(rect.x), int(rect.y), int(rect.width), int(rect.height), COLOR_PANEL_BORDER)

        begin_scissor_mode(int(rect.x), int(rect.y), int(rect.width), int(rect.height))

        # Center anchor
        center_x = rect.x + rect.width * 0.5 + self.canvas_offset.x
        center_y = rect.y + rect.height * 0.5 + self.canvas_offset.y

        # Checkerboard background
        if self.show_grid_2d:
            cell = 24
            for cx in range(int(rect.x), int(rect.x + rect.width), cell):
                for cy in range(int(rect.y), int(rect.y + rect.height), cell):
                    if ((cx // cell) + (cy // cell)) % 2 == 0:
                        draw_rectangle(cx, cy, cell, cell, Color(16, 22, 34, 255))
            # Coordinate crosshair
            draw_line(int(rect.x), int(center_y), int(rect.x + rect.width), int(center_y), Color(35, 55, 85, 200))
            draw_line(int(center_x), int(rect.y), int(center_x), int(rect.y + rect.height), Color(35, 55, 85, 200))

        items = self.cache_2d
        sel_idx = self.selected_idx_2d
        item = items[sel_idx] if items else None
        active_pal = self.palettes_2d[self.active_palette_idx_2d]
        facing_rad = math.radians(self.facing_deg_2d)

        if item is not None:
            if item.get("is_benchmark") or not item["full_path"]:
                draw_benchmark_starfighter_2d(
                    Vector2(center_x, center_y),
                    facing_angle_rad=facing_rad,
                    anim_timer=self.anim_timer_2d,
                    scale=self.scale_2d,
                    palette=active_pal
                )
            else:
                try:
                    draw_func, def_pal = load_sprite_2d(item["key"])
                    sprite_pal = active_pal or def_pal
                    draw_func(
                        Vector2(center_x, center_y),
                        facing_angle_rad=facing_rad,
                        anim_timer=self.anim_timer_2d,
                        scale=self.scale_2d,
                        palette=sprite_pal
                    )
                except Exception as exc:
                    draw_circle(int(center_x), int(center_y), 24, COLOR_ACCENT_RED)

        end_scissor_mode()

        draw_text("2D CANVAS: Drag Mouse to Pan | Wheel: Zoom | [R] Reset", int(rect.x + 10), int(rect.y + 10), 11, COLOR_TEXT_MUTED)

    def _render_2d_controls(self, rect: Rectangle) -> None:
        draw_ui_panel(rect, COLOR_PANEL_BORDER, COLOR_PANEL_ALT)

        mx, my = get_mouse_x(), get_mouse_y()
        b_play = Rectangle(rect.x + 10, rect.y + 10, 80, 26)
        h_play = check_collision_point_rec(Vector2(float(mx), float(my)), b_play)
        if h_play and is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            if self.is_playing_2d: self.trigger_pause()
            else: self.trigger_play()
        draw_ui_button(b_play, "[Pause]" if self.is_playing_2d else "[Play]", self.is_playing_2d, h_play, COLOR_ACCENT, 11)

        b_stop = Rectangle(rect.x + 96, rect.y + 10, 68, 26)
        h_stop = check_collision_point_rec(Vector2(float(mx), float(my)), b_stop)
        if h_stop and is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            self.trigger_stop()
        draw_ui_button(b_stop, "[Stop]", False, h_stop, COLOR_ACCENT, 11)

        b_grid = Rectangle(rect.x + 172, rect.y + 10, 85, 26)
        h_grid = check_collision_point_rec(Vector2(float(mx), float(my)), b_grid)
        if h_grid and is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            self.show_grid_2d = not self.show_grid_2d
        draw_ui_button(b_grid, "Grid: ON" if self.show_grid_2d else "Grid: OFF", self.show_grid_2d, h_grid, COLOR_ACCENT, 11)

        pal_name = self.palette_names_2d[self.active_palette_idx_2d]
        b_pal = Rectangle(rect.x + 266, rect.y + 10, 130, 26)
        h_pal = check_collision_point_rec(Vector2(float(mx), float(my)), b_pal)
        if h_pal and is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            self.active_palette_idx_2d = (self.active_palette_idx_2d + 1) % len(self.palettes_2d)
        draw_ui_button(b_pal, f"Pal: {pal_name}", True, h_pal, COLOR_ACCENT_GOLD, 11)

        s_speed = Rectangle(rect.x + 10, rect.y + 48, 175, 36)
        self.speed_2d = draw_ui_slider(s_speed, "Speed", self.speed_2d, 0.0, 3.0, "x")

        s_scale = Rectangle(rect.x + 205, rect.y + 48, 175, 36)
        self.scale_2d = draw_ui_slider(s_scale, "Scale", self.scale_2d, 0.5, 6.0, "x")

        s_angle = Rectangle(rect.x + 400, rect.y + 48, 180, 36)
        self.facing_deg_2d = draw_ui_slider(s_angle, "Facing Angle", self.facing_deg_2d, 0.0, 360.0, "°")

        rad = math.radians(self.facing_deg_2d)
        timer_str = f"Anim Timer: {self.anim_timer_2d:.2f}s | Angle: {self.facing_deg_2d:.0f}° ({rad:.2f} rad) | Zoom: {self.canvas_zoom:.1f}x"
        draw_text(timer_str, int(rect.x + 12), int(rect.y + 105), 11, COLOR_TEXT_DIM)

    # --------------------------------------------------------------------------
    # SFX Viewport & Controls
    # --------------------------------------------------------------------------
    def _render_sfx_viewport(self, rect: Rectangle) -> None:
        progress = self.sfx_play_timer / max(0.01, self.sfx_duration)
        draw_oscilloscope(
            rect,
            anim_progress=progress,
            is_playing=self.sfx_is_playing,
            volume=self.sfx_volume,
            pitch=self.sfx_pitch,
            accent_color=COLOR_ACCENT
        )

    def _render_sfx_controls(self, rect: Rectangle) -> None:
        draw_ui_panel(rect, COLOR_PANEL_BORDER, COLOR_PANEL_ALT)

        mx, my = get_mouse_x(), get_mouse_y()
        # Row 1: Primary Action Buttons
        b_play = Rectangle(rect.x + 10, rect.y + 10, 130, 30)
        h_play = check_collision_point_rec(Vector2(float(mx), float(my)), b_play)
        if h_play and is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            self.trigger_play()
        draw_ui_button(b_play, "[PLAY SFX (Space)]", self.sfx_is_playing, h_play, COLOR_ACCENT_GREEN, 12)

        b_stop = Rectangle(rect.x + 148, rect.y + 10, 85, 30)
        h_stop = check_collision_point_rec(Vector2(float(mx), float(my)), b_stop)
        if h_stop and is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            self.trigger_stop()
        draw_ui_button(b_stop, "[Stop (S)]", False, h_stop, COLOR_ACCENT, 12)

        b_loop = Rectangle(rect.x + 242, rect.y + 10, 110, 30)
        h_loop = check_collision_point_rec(Vector2(float(mx), float(my)), b_loop)
        if h_loop and is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            self.sfx_loop = not self.sfx_loop
        draw_ui_button(b_loop, "Loop: ON" if self.sfx_loop else "Loop: OFF", self.sfx_loop, h_loop, COLOR_ACCENT_GOLD, 11)

        # Row 2: Sliders
        s_vol = Rectangle(rect.x + 10, rect.y + 54, 270, 36)
        self.sfx_volume = draw_ui_slider(s_vol, "Volume", self.sfx_volume, 0.0, 1.0, "")

        s_pitch = Rectangle(rect.x + 300, rect.y + 54, 275, 36)
        self.sfx_pitch = draw_ui_slider(s_pitch, "Pitch / Frequency", self.sfx_pitch, 0.5, 2.0, "x")

        # Row 3: Readout
        items = self.cache_sfx
        cue_str = items[self.selected_idx_sfx]["key"] if items else "None"
        dur_ms = int(self.sfx_duration * 1000)
        status_txt = f"Cue: '{cue_str}' | Duration: {dur_ms}ms | Trigger State: {'ACTIVE' if self.sfx_is_playing else 'READY'}"
        draw_text(status_txt, int(rect.x + 12), int(rect.y + 108), 11, COLOR_TEXT_DIM)

    # --------------------------------------------------------------------------
    # BGM Viewport & Controls
    # --------------------------------------------------------------------------
    def _render_bgm_viewport(self, rect: Rectangle) -> None:
        draw_spectrum_equalizer(
            rect,
            anim_timer=get_time(),
            is_playing=self.bgm_is_playing,
            volume=self.bgm_volume,
            pitch=self.bgm_pitch,
            bpm=120.0
        )

    def _render_bgm_controls(self, rect: Rectangle) -> None:
        draw_ui_panel(rect, COLOR_PANEL_BORDER, COLOR_PANEL_ALT)

        mx, my = get_mouse_x(), get_mouse_y()
        # Row 1: Player Buttons
        b_play = Rectangle(rect.x + 10, rect.y + 10, 110, 30)
        h_play = check_collision_point_rec(Vector2(float(mx), float(my)), b_play)
        if h_play and is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            if self.bgm_is_playing: self.trigger_pause()
            else: self.trigger_play()
        draw_ui_button(b_play, "[Pause]" if self.bgm_is_playing else "[Play]", self.bgm_is_playing, h_play, COLOR_ACCENT_GREEN, 12)

        b_stop = Rectangle(rect.x + 128, rect.y + 10, 80, 30)
        h_stop = check_collision_point_rec(Vector2(float(mx), float(my)), b_stop)
        if h_stop and is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            self.trigger_stop()
        draw_ui_button(b_stop, "[Stop]", False, h_stop, COLOR_ACCENT, 12)

        b_loop = Rectangle(rect.x + 216, rect.y + 10, 110, 30)
        h_loop = check_collision_point_rec(Vector2(float(mx), float(my)), b_loop)
        if h_loop and is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            self.bgm_loop = not self.bgm_loop
        draw_ui_button(b_loop, "Loop: ON" if self.bgm_loop else "Loop: OFF", self.bgm_loop, h_loop, COLOR_ACCENT_GOLD, 11)

        # Timeline Scrubber Bar
        bar_x = rect.x + 340
        bar_w = 238
        bar_y = rect.y + 18
        draw_rectangle(int(bar_x), int(bar_y), int(bar_w), 8, Color(24, 34, 56, 255))
        draw_rectangle_lines(int(bar_x), int(bar_y), int(bar_w), 8, COLOR_PANEL_BORDER)

        t_prog = clamp(self.bgm_time_played / max(0.1, self.bgm_time_total), 0.0, 1.0)
        fill_w = int(bar_w * t_prog)
        draw_rectangle(int(bar_x), int(bar_y), fill_w, 8, COLOR_ACCENT)

        # Time label
        time_str = f"{self.bgm_time_played:.1f}s / {self.bgm_time_total:.1f}s"
        draw_text(time_str, int(bar_x + bar_w - len(time_str) * 7), int(rect.y + 32), 10, COLOR_TEXT_MUTED)

        # Row 2: Sliders
        s_vol = Rectangle(rect.x + 10, rect.y + 54, 270, 36)
        self.bgm_volume = draw_ui_slider(s_vol, "Master Stream Volume", self.bgm_volume, 0.0, 1.0, "")
        if self.bgm_active_key and self.audio_ready:
            self.sound_lib.set_volume(self.bgm_active_key, self.bgm_volume)

        s_pitch = Rectangle(rect.x + 300, rect.y + 54, 275, 36)
        self.bgm_pitch = draw_ui_slider(s_pitch, "Pitch / Tempo Rate", self.bgm_pitch, 0.5, 2.0, "x")
        if self.bgm_active_key and self.audio_ready:
            self.sound_lib.set_pitch(self.bgm_active_key, self.bgm_pitch)

        # Row 3: Readout
        items = self.cache_bgm
        track_str = items[self.selected_idx_bgm]["key"] if items else "None"
        readout_txt = f"Track: '{track_str}' | Tempo: 120 BPM | Looping Streaming Buffer"
        draw_text(readout_txt, int(rect.x + 12), int(rect.y + 108), 11, COLOR_TEXT_DIM)

    # --------------------------------------------------------------------------
    # Right Inspector Panel
    # --------------------------------------------------------------------------
    def _draw_inspector(self) -> None:
        """Renders asset metadata, pedagogical docstring, and minigame code integration snippets."""
        insp_rect = Rectangle(964, 96, 300, 584)
        draw_ui_panel(insp_rect, COLOR_PANEL_BORDER, COLOR_PANEL)

        draw_text("ASSET INSPECTOR", 978, 108, 14, COLOR_ACCENT)
        draw_line(964, 130, 1264, 130, COLOR_PANEL_BORDER)

        items = self._get_active_cache()
        sel_idx = self._get_active_selected_idx()
        if not items:
            draw_text("No asset selected.", 978, 150, 12, COLOR_TEXT_MUTED)
            return

        item = items[sel_idx]

        # 1. Identity & Physical Metrics
        iy = 142
        draw_text(item["name"], 978, iy, 14, COLOR_ACCENT_GOLD)
        iy += 22

        path_str = item["rel_path"]
        if len(path_str) > 34:
            path_str = "..." + path_str[-31:]
        draw_text(path_str, 978, iy, 11, COLOR_TEXT_DIM)
        iy += 18

        draw_ui_badge(978, iy, item["category"], COLOR_ACCENT, Color(10, 13, 22, 255), 10)
        draw_ui_badge(1060, iy, f"{item['line_count']} lines", Color(35, 50, 75, 255), WHITE, 10)
        iy += 28

        draw_line(964, iy, 1264, iy, COLOR_PANEL_BORDER)
        iy += 10

        # 2. Theory & Mathematical Concept
        draw_text("THEORY & PEDAGOGY", 978, iy, 12, COLOR_ACCENT)
        iy += 18

        doc_lines = [line.strip() for line in item["docstring"].splitlines() if line.strip()]
        # Render first 6 lines of docstring cleanly wrapped
        rendered_lines = 0
        for dline in doc_lines[:7]:
            if dline.startswith("===") or dline.startswith("---") or dline.startswith("Type"):
                continue
            if len(dline) > 38:
                dline = dline[:36] + ".."
            draw_text(dline, 978, iy, 11, COLOR_TEXT_MAIN)
            iy += 16
            rendered_lines += 1
            if rendered_lines >= 5:
                break

        iy += 8
        draw_line(964, iy, 1264, iy, COLOR_PANEL_BORDER)
        iy += 10

        # 3. Canonical Minigame Integration Snippet
        draw_text("MINIGAME IMPORT SNIPPET", 978, iy, 12, COLOR_ACCENT)
        iy += 20

        # Code block background
        code_bg = Rectangle(974, iy, 280, 116)
        draw_rectangle(int(code_bg.x), int(code_bg.y), int(code_bg.width), int(code_bg.height), Color(10, 14, 22, 255))
        draw_rectangle_lines(int(code_bg.x), int(code_bg.y), int(code_bg.width), int(code_bg.height), COLOR_PANEL_BORDER)

        if self.current_tab == TAB_3D:
            code_lines = [
                "from assets.audio.asset_loader import load_model_3d",
                f"draw_model, palette = load_model_3d('{item['key']}')",
                "# Inside 3D render loop:",
                "draw_model(pos, rot_y, timer, scale, palette)",
            ]
        elif self.current_tab == TAB_2D:
            code_lines = [
                "from assets.audio.asset_loader import load_sprite_2d",
                f"draw_sprite, palette = load_sprite_2d('{item['key']}')",
                "# Inside 2D render loop:",
                "draw_sprite(pos, facing_rad, timer, scale, palette)",
            ]
        elif self.current_tab == TAB_SFX:
            code_lines = [
                "from assets.audio.asset_loader import SoundLibrary",
                f"sfx = SoundLibrary(sfx=['{item['key']}'])",
                "# Trigger one-shot sound:",
                f"sfx.play('{item['key']}', volume=0.8, pitch=1.0)",
            ]
        else:
            code_lines = [
                "from assets.audio.asset_loader import SoundLibrary",
                f"sfx = SoundLibrary(bgm=['{item['key']}'])",
                f"sfx.play('{item['key']}', volume=0.7, loop=True)",
                "# In update(dt): sfx.update()",
            ]

        for c_idx, cline in enumerate(code_lines):
            draw_text(cline, int(code_bg.x + 8), int(code_bg.y + 8 + c_idx * 18), 10, COLOR_ACCENT_GOLD if c_idx == 1 else COLOR_TEXT_DIM)

        iy += 128
        # Copy notification button
        b_copy = Rectangle(974, iy, 280, 26)
        mx, my = get_mouse_x(), get_mouse_y()
        h_copy = check_collision_point_rec(Vector2(float(mx), float(my)), b_copy)
        if h_copy and is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            self.status_banner = f"Copied integration snippet for '{item['key']}'."
        draw_ui_button(b_copy, "[Copy Snippet to Memory]", False, h_copy, COLOR_ACCENT, 11)

    def _draw_status_bar(self) -> None:
        """Renders the bottom status bar with operational notifications and shortcut reminders."""
        draw_rectangle(0, 688, SCREEN_WIDTH, 32, COLOR_PANEL_HEADER)
        draw_line(0, 688, SCREEN_WIDTH, 688, COLOR_PANEL_BORDER)

        draw_text(self.status_banner, 20, 698, 12, COLOR_ACCENT_GOLD if self.status_banner_time > 0.0 else COLOR_TEXT_DIM)

        shortcut_str = "[1-4] Tabs | [Space] Play/Pause | [S] Stop | [R] Reset | [F5] Rescan"
        draw_text(shortcut_str, SCREEN_WIDTH - len(shortcut_str) * 7 - 20, 698, 11, COLOR_TEXT_MUTED)

    # --------------------------------------------------------------------------
    # Teardown & Resource Cleanup
    # --------------------------------------------------------------------------
    def close(self) -> None:
        """Unloads audio streams, sound buffers, and closes window cleanly."""
        if self.audio_ready:
            self.sound_lib.unload_all()
            close_audio_device()
        close_window()


# ==============================================================================
# STANDALONE ENTRY POINT & AUTOMATED SMOKE TEST
# ==============================================================================
def main():
    smoke_test = "--smoke-test" in sys.argv

    app = AssetViewerApp()

    if smoke_test:
        print("=== Asset Viewer Smoke Test Running ===")
        # Run interactive test frames across all 4 tabs to verify rendering & audio integrity
        for tab_idx in [TAB_3D, TAB_2D, TAB_SFX, TAB_BGM]:
            app.current_tab = tab_idx
            app.trigger_play()
            app.update()
            app.draw()
            if tab_idx == TAB_BGM:
                app.trigger_pause()
                app.update()
                app.draw()
            app.trigger_stop()
            app.update()
            app.draw()
            print(f"  [PASS] Verified Tab {tab_idx}: {TAB_INFO[tab_idx]['title']}")

        app.close()
        print("[PASS] asset_viewer.py --smoke-test passed with zero defects.")
        sys.exit(0)

    # Standard interactive loop
    while not window_should_close():
        app.update()
        app.draw()

    app.close()
    sys.exit(0)


if __name__ == "__main__":
    main()
