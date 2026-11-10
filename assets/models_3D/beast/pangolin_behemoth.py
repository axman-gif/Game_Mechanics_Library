# -*- coding: utf-8 -*-
"""
Armored Pangolin Behemoth - 3D Procedural Primitive Model
=========================================================
Category         : beast
Target File      : assets/models_3D/beast/pangolin_behemoth.py
Primitives Used  : Stepped Prisms/Cubes (segmented dorsal plates), Cylinders (thick column legs, curled tail), Spheres (head, snout, claws)
Animation Loop   : Heavy low-slung trotting gait, clacking peristaltic dorsal plate wave, balancing tail sweep

Problem Solved:
  Eliminates bulky 3D mesh files (.obj/.fbx) and external texture dependencies by
  synthesizing a heavily armored quadruped pangolin behemoth with multi-segmented
  articulated dorsal scales purely from Raylib geometric primitives in real time.

How the Procedural Articulation Works:
  - The model hierarchy is computed relative to a base 'position' (Vector3) at ground level.
  - Low-slung gait uses 4 thick pillar legs swinging in alternating crawl pairs.
  - 6 overlapping dorsal shell plates flex and clack in a peristaltic wave:
    plate_lift = 0.04 * math.sin(anim_timer * 4.5 - plate_idx * 0.6).
  - Thick segmented tail sweeps left/right for dynamic counterbalance.
  - Excavation claws and armored ocular cowls reinforce the subterranean tank silhouette.

C++ Raylib Equivalent:
  struct PangolinPalette { Color carapace; Color underbelly; Color plates; Color claws; Color eyes; };
  void DrawPangolinBehemoth3D(Vector3 position, float rotation_y, float anim_timer, float scale, const PangolinPalette* palette);
  Mapped directly to DrawCube, DrawCubeWires, DrawSphere, and DrawCylinderEx from raylib.h.
"""

# ==============================================================================
# PART 2: ZERO BYTECODE, SYS.PATH & MANDATORY RAYLIB IMPORTS
# ==============================================================================
import sys
import os
import math

# Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# Add repository root to search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

# Mandatory Raylib and utility imports
from pyray import *
from utils import *

# ==============================================================================
# PART 3: PALETTES & NAMED GEOMETRIC CONSTANTS (Zero Magic Numbers)
# ==============================================================================
# Semantic body color mapping for C++ struct parity:
# const PangolinPalette DEFAULT_PANGOLIN_PALETTE = { ... };

DEFAULT_PANGOLIN_PALETTE = {
    "carapace": Color(165, 95, 50, 255),    # Hardened chitin copper
    "underbelly": Color(190, 160, 120, 255),# Leathery tan ventral hide
    "plates": Color(135, 110, 75, 255),     # Weathered bronze dorsal scales
    "claws": Color(32, 32, 36, 255),        # Obsidian black excavation talons
    "eyes": Color(255, 190, 30, 255),       # Glowing amber sensor eyes
}

VOLCANIC_PANGOLIN_PALETTE = {
    "carapace": Color(48, 42, 45, 255),     # Basalt magma rock
    "underbelly": Color(85, 80, 82, 255),   # Cool volcanic ash
    "plates": Color(195, 65, 30, 255),      # Magma-infused crust scales
    "claws": Color(55, 55, 60, 255),        # Tempered obsidian iron
    "eyes": Color(255, 220, 20, 255),       # Blazing sulfur glow
}

# Named geometric proportions (replaces magic numbers)
UNDERBELLY_WIDTH = 0.70
UNDERBELLY_HEIGHT = 0.40
UNDERBELLY_LENGTH = 1.10
UNDERBELLY_ELEVATION = 0.45

SCALE_COUNT = 6
BASE_SCALE_WIDTH = 0.85
BASE_SCALE_HEIGHT = 0.20
BASE_SCALE_LENGTH = 0.45

LEG_WIDTH_OFFSET = 0.42
LEG_RADIUS = 0.12
LEG_LENGTH = 0.45
PISTON_RADIUS = 0.08
FOOT_WIDTH = 0.26
FOOT_HEIGHT = 0.12
FOOT_LENGTH = 0.28
CLAW_RADIUS = 0.05
CLAW_LENGTH = 0.14

HEAD_WIDTH = 0.40
HEAD_HEIGHT = 0.32
HEAD_LENGTH = 0.48
SNOUT_WIDTH = 0.35
SNOUT_HEIGHT = 0.25
SNOUT_LENGTH = 0.45
EYE_RADIUS = 0.04
EYE_COWL_RADIUS = 0.06

TAIL_LENGTH = 0.90
TAIL_BASE_RADIUS = 0.14
TAIL_SEGMENTS = 4

CRAWL_SPEED = 4.5
SCALE_WAVE_SPEED = 4.5
TAIL_SWEEP_SPEED = 3.0


# ==============================================================================
# PART 4: CANONICAL 3D PROCEDURAL DRAWING FUNCTION
# ==============================================================================
def draw_pangolin_behemoth_3d(
    position: Vector3,
    rotation_y: float = 0.0,
    anim_timer: float = 0.0,
    scale: float = 1.0,
    palette: dict = None
) -> None:
    """
    Renders an articulated 3D Armored Pangolin Behemoth with procedural crawl gait,
    peristaltic dorsal scale wave, and balance tail sweep.
    Must be called between begin_mode_3d(camera) and end_mode_3d().

    Parameters:
      position   : World-space base root location (ground level beneath belly).
      rotation_y : Heading angle in DEGREES around Y axis (0 deg = facing +Z).
      anim_timer : Elapsed seconds driving crawl stride, dorsal wave, and tail sweep.
      scale      : Geometric scaling factor (1.0 = standard behemoth ~2.4m length).
      palette    : Optional dictionary overriding DEFAULT_PANGOLIN_PALETTE colors.
    """
    pal = palette if palette is not None else DEFAULT_PANGOLIN_PALETTE

    c_carapace = pal["carapace"]
    c_underbelly = pal["underbelly"]
    c_plates = pal["plates"]
    c_claws = pal["claws"]
    c_eyes = pal["eyes"]

    rad_y = rotation_y * (math.pi / 180.0)
    cos_r = math.cos(rad_y)
    sin_r = math.sin(rad_y)

    # Low-slung crawl vertical micro-bob
    crawl_bob = 0.03 * abs(math.sin(anim_timer * CRAWL_SPEED)) * scale

    bx = position.x
    by = position.y + crawl_bob
    bz = position.z

    # Helper: transform local model coordinates to world space
    def transform_pt(lx: float, ly: float, lz: float) -> Vector3:
        wx = bx + (lx * cos_r + lz * sin_r) * scale
        wy = by + ly * scale
        wz = bz + (-lx * sin_r + lz * cos_r) * scale
        return Vector3(wx, wy, wz)

    # 1. Armored Undercarriage (Main low-slung chassis)
    belly_pos = transform_pt(0.0, UNDERBELLY_ELEVATION, 0.0)
    draw_cube(belly_pos, UNDERBELLY_WIDTH * scale, UNDERBELLY_HEIGHT * scale, UNDERBELLY_LENGTH * scale, c_underbelly)
    draw_cube_wires(belly_pos, UNDERBELLY_WIDTH * scale, UNDERBELLY_HEIGHT * scale, UNDERBELLY_LENGTH * scale, c_claws)

    # 2. Six Articulated Dorsal Carapace Scale Plates (Stepped, overlapping)
    # Scaled from neck (z = +0.50) to sacrum (z = -0.55)
    for i in range(SCALE_COUNT):
        # Progress from front (0) to back (5)
        t = i / float(SCALE_COUNT - 1)
        plate_lz = 0.50 - t * 1.05
        # Peristaltic wave lift
        plate_wave = 0.04 * math.sin(anim_timer * SCALE_WAVE_SPEED - i * 0.60) * scale
        plate_ly = UNDERBELLY_ELEVATION + (UNDERBELLY_HEIGHT * 0.5) + (BASE_SCALE_HEIGHT * 0.45) + plate_wave

        # Scale width and length taper slightly toward the rear
        w_factor = 1.0 - t * 0.25
        h_factor = 1.0 - t * 0.15
        l_factor = 0.95

        p_w = BASE_SCALE_WIDTH * w_factor * scale
        p_h = BASE_SCALE_HEIGHT * h_factor * scale
        p_l = BASE_SCALE_LENGTH * l_factor * scale

        plate_pos = transform_pt(0.0, plate_ly, plate_lz)
        draw_cube(plate_pos, p_w, p_h, p_l, c_carapace)
        draw_cube_wires(plate_pos, p_w, p_h, p_l, c_plates)

        # Scale ridge trim (lateral bevels)
        trim_pos = transform_pt(0.0, plate_ly + (p_h * 0.5), plate_lz - 0.02)
        draw_cube(trim_pos, p_w * 0.75, 0.04 * scale, p_l * 0.6, c_plates)

    # 3. Armored Digging Head & Snout
    head_lz = 0.65
    head_ly = UNDERBELLY_ELEVATION + 0.08
    head_pos = transform_pt(0.0, head_ly, head_lz)
    draw_cube(head_pos, HEAD_WIDTH * scale, HEAD_HEIGHT * scale, HEAD_LENGTH * scale, c_carapace)
    draw_cube_wires(head_pos, HEAD_WIDTH * scale, HEAD_HEIGHT * scale, HEAD_LENGTH * scale, c_claws)

    # Wedge-shaped excavating snout
    snout_lz = head_lz + 0.32
    snout_ly = head_ly - 0.06
    snout_pos = transform_pt(0.0, snout_ly, snout_lz)
    draw_cube(snout_pos, SNOUT_WIDTH * scale, SNOUT_HEIGHT * scale, SNOUT_LENGTH * scale, c_underbelly)

    # Armored Cranial Shield Brow
    brow_pos = transform_pt(0.0, head_ly + 0.16, head_lz + 0.10)
    draw_cube(brow_pos, 0.42 * scale, 0.08 * scale, 0.35 * scale, c_plates)

    # Armored Ocular Cowls & Glowing Amber Sensor Eyes
    eye_lx = 0.18
    eye_lz = head_lz + 0.12
    eye_ly = head_ly + 0.06

    eye_l_pos = transform_pt(-eye_lx, eye_ly, eye_lz)
    eye_r_pos = transform_pt(eye_lx, eye_ly, eye_lz)

    draw_sphere(eye_l_pos, EYE_COWL_RADIUS * scale, c_carapace)
    draw_sphere(eye_r_pos, EYE_COWL_RADIUS * scale, c_carapace)
    draw_sphere(eye_l_pos, EYE_RADIUS * scale, c_eyes)
    draw_sphere(eye_r_pos, EYE_RADIUS * scale, c_eyes)

    # 4. Four Heavy Pillar Legs & Excavation Claws
    leg_coords = [
        # (name, lx, lz, phase)
        ("FL", -LEG_WIDTH_OFFSET,  0.35, 0.0),
        ("FR",  LEG_WIDTH_OFFSET,  0.35, math.pi),
        ("HL", -LEG_WIDTH_OFFSET, -0.40, math.pi),
        ("HR",  LEG_WIDTH_OFFSET, -0.40, 0.0),
    ]

    for name, lx, lz, phase in leg_coords:
        stride = math.sin(anim_timer * CRAWL_SPEED + phase) * 0.35
        hip_pt = transform_pt(lx, UNDERBELLY_ELEVATION, lz)

        # Foot target on ground
        foot_lz = lz + math.sin(stride) * LEG_LENGTH
        foot_ly = 0.0
        foot_pt = transform_pt(lx, foot_ly + (FOOT_HEIGHT * 0.5), foot_lz)

        # Draw heavy column leg cylinder
        draw_cylinder_ex(hip_pt, foot_pt, LEG_RADIUS * scale, (LEG_RADIUS * 1.1) * scale, 6, c_carapace)

        # Hydraulic gait piston detail
        piston_top = transform_pt(lx * 1.12, UNDERBELLY_ELEVATION - 0.05, lz)
        piston_bot = transform_pt(lx * 1.12, foot_ly + 0.12, foot_lz)
        draw_cylinder_ex(piston_top, piston_bot, PISTON_RADIUS * scale, (PISTON_RADIUS * 0.8) * scale, 4, c_claws)

        # Heavy clawed foot
        draw_cube(foot_pt, FOOT_WIDTH * scale, FOOT_HEIGHT * scale, FOOT_LENGTH * scale, c_plates)

        # Excavation Claw Tips (3 curved digging claws per foot)
        for c in range(3):
            c_offset = (c - 1) * 0.08
            claw_base = transform_pt(lx + c_offset, foot_ly + 0.03, foot_lz + (FOOT_LENGTH * 0.5))
            claw_tip = transform_pt(lx + c_offset, foot_ly, foot_lz + (FOOT_LENGTH * 0.5) + CLAW_LENGTH)
            draw_cylinder_ex(claw_base, claw_tip, CLAW_RADIUS * scale, 0.01 * scale, 4, c_claws)

    # 5. Thick Segmented Curled Tail (Dynamic Balance Sweep)
    tail_yaw_angle = 0.22 * math.sin(anim_timer * TAIL_SWEEP_SPEED)
    curr_lx = 0.0
    curr_ly = UNDERBELLY_ELEVATION - 0.05
    curr_lz = -0.55

    for seg in range(TAIL_SEGMENTS):
        seg_progress = seg / float(TAIL_SEGMENTS)
        seg_len = (TAIL_LENGTH / float(TAIL_SEGMENTS))

        # Tail curls downwards and sweeps horizontally
        yaw = tail_yaw_angle * (1.0 + seg * 0.4)
        pitch = -0.15 - seg * 0.10

        next_lx = curr_lx + math.sin(yaw) * seg_len
        next_ly = curr_ly + math.sin(pitch) * seg_len
        next_lz = curr_lz - math.cos(yaw) * seg_len

        t_start = transform_pt(curr_lx, curr_ly, curr_lz)
        t_end = transform_pt(next_lx, next_ly, next_lz)

        r_start = (TAIL_BASE_RADIUS * (1.0 - seg_progress * 0.55)) * scale
        r_end = (TAIL_BASE_RADIUS * (1.0 - (seg_progress + 0.25) * 0.55)) * scale

        draw_cylinder_ex(t_start, t_end, r_start, r_end, 6, c_carapace)

        # Ring shield plates on each tail segment
        ring_pos = transform_pt(curr_lx, curr_ly + (r_start * 0.5), curr_lz)
        draw_cube(ring_pos, (r_start * 2.2) * scale, 0.05 * scale, (seg_len * 0.8) * scale, c_plates)

        curr_lx = next_lx
        curr_ly = next_ly
        curr_lz = next_lz

    # Armored tail club bulb
    club_pt = transform_pt(curr_lx, curr_ly, curr_lz)
    draw_sphere(club_pt, (TAIL_BASE_RADIUS * 0.75) * scale, c_claws)


# ==============================================================================
# PART 5: C++ MAPPING & MEMORY LAYOUT (Zero "Pythonic Magic")
# ==============================================================================
# In C++ (raylib.h), this procedural model requires zero dynamic memory allocation:
#
# struct PangolinPalette {
#     Color carapace;
#     Color underbelly;
#     Color plates;
#     Color claws;
#     Color eyes;
# };
#
# static const PangolinPalette DEFAULT_PANGOLIN_PALETTE = {
#     (Color){165, 95, 50, 255},
#     (Color){190, 160, 120, 255},
#     (Color){135, 110, 75, 255},
#     (Color){32, 32, 36, 255},
#     (Color){255, 190, 30, 255}
# };
#
# void DrawPangolinBehemoth3D(Vector3 position, float rotation_y, float anim_timer, float scale, const PangolinPalette* palette);
#
# Memory Layout & Performance Notes:
# - Zero heap allocations: all coordinates and kinematic joints are computed on the CPU stack.
# - Immediate GPU buffers: primitives map directly to DrawCube, DrawSphere, and DrawCylinderEx.
# - C++ Transferability: Replace math.sin/cos with sinf/cosf from <math.h>. Replace Vector3 with raylib::Vector3.


# ==============================================================================
# PART 6: STANDALONE 3D ORBIT VIEWER (ModelViewerApp)
# ==============================================================================
class ModelViewerApp:
    """
    Interactive 3D previewer allowing inspection, rotation, zooming,
    palette swapping, and automated 3-frame smoke testing.
    """
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        init_window(self.screen_width, self.screen_height, "3D Model Inspector - Armored Pangolin Behemoth")
        set_target_fps(60)

        # 3D Orbit Camera Setup
        self.camera = Camera3D(
            Vector3(0.0, 2.8, 5.0),   # Position
            Vector3(0.0, 0.5, 0.0),   # Target
            Vector3(0.0, 1.0, 0.0),   # Up vector
            45.0,                     # FOV
            CAMERA_PERSPECTIVE
        )

        self.anim_timer = 0.0
        self.anim_playing = True
        self.rotation_y = 45.0
        self.active_palette_idx = 0
        self.palettes = [DEFAULT_PANGOLIN_PALETTE, VOLCANIC_PANGOLIN_PALETTE]
        self.palette_names = ["Hardened Chitin", "Volcanic Basalt"]

    def update(self):
        dt = min(get_frame_time(), 0.05)
        if self.anim_playing:
            self.anim_timer += dt

        # Orbit Controls: Drag mouse left-click or use arrow keys
        if is_mouse_button_down(MOUSE_BUTTON_LEFT):
            delta = get_mouse_delta()
            self.rotation_y += delta.x * 0.5

        if is_key_down(KEY_LEFT):
            self.rotation_y -= 60.0 * dt
        if is_key_down(KEY_RIGHT):
            self.rotation_y += 60.0 * dt

        # Toggle Animation Play/Pause
        if is_key_pressed(KEY_SPACE):
            self.anim_playing = not self.anim_playing

        # Cycle Palettes
        if is_key_pressed(KEY_P) or is_key_pressed(KEY_ONE):
            self.active_palette_idx = (self.active_palette_idx + 1) % len(self.palettes)

        # Zoom via Mouse Wheel
        wheel = get_mouse_wheel_move()
        if wheel != 0.0:
            cam_dist = math.sqrt(self.camera.position.x**2 + self.camera.position.z**2)
            cam_dist = max(2.0, min(12.0, cam_dist - wheel * 0.8))
            self.camera.position.z = cam_dist

    def draw(self):
        begin_drawing()
        clear_background(Color(22, 26, 32, 255))

        # 3D Scene Rendering
        begin_mode_3d(self.camera)
        draw_grid(10, 1.0)
        draw_pangolin_behemoth_3d(
            Vector3(0.0, 0.0, 0.0),
            rotation_y=self.rotation_y,
            anim_timer=self.anim_timer,
            scale=1.0,
            palette=self.palettes[self.active_palette_idx]
        )
        end_mode_3d()

        # HUD & Telemetry Overlay (Keeps x=450..980 clear for global bar)
        draw_text("3D MODEL INSPECTOR: Armored Pangolin Behemoth", 24, 20, 20, RAYWHITE)
        draw_text("[L-Drag / Left-Right] Rotate | [Space] Play/Pause | [P] Cycle Palette", 24, 52, 14, LIGHTGRAY)
        draw_text(f"Palette: {self.palette_names[self.active_palette_idx]}", 24, 76, 14, YELLOW)
        draw_text(f"Anim Timer: {self.anim_timer:.2f}s | Rotation: {self.rotation_y:.1f} deg", 24, 98, 14, SKYBLUE)

        # Global Top-Bar Integration
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
        close_window()


if __name__ == "__main__":
    is_smoke = "--smoke-test" in sys.argv
    ModelViewerApp().run(smoke_test=is_smoke)
