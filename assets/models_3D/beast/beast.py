# -*- coding: utf-8 -*-
"""
Quadruped Beast 3D - 3D Procedural Primitive Model
==================================================
Category         : beast
Target File      : assets/models_3D/beast/beast.py
Primitives Used  : Cylinders (spine, legs, tail), Prisms/Cubes (torso, carapace, head, claws), Spheres (joints, eyes)
Animation Loop   : Synchronized 4-leg trotting gait, vertical body bounce, swinging segmented tail, head bob

Problem Solved:
  Eliminates bulky 3D mesh files (.obj/.fbx) and external texture dependencies by
  synthesizing an articulated predatory quadruped beast purely from Raylib geometric
  primitives and trigonometric transforms in real time.

How the Procedural Articulation Works:
  - The model hierarchy is computed relative to a base 'position' (Vector3) at ground level.
  - Synchronized diagonal-trot gait: diagonal pairs (FL+HR, FR+HL) oscillate in anti-phase (phase offset pi).
  - Upper limbs (femur) swing via sinusoidal pitch, while lower limbs (tibia) flex via delayed knee angles.
  - Vertical spine bounce uses rectified sine: dy = 0.05 * abs(sin(anim_timer * 6.0)).
  - Segmented tail propagates a travelling sin wave along 3 articulated cylinder segments.
  - Predatory skull bobs rhythmically and features glowing amber sensory eyes.

C++ Raylib Equivalent:
  struct BeastPalette { Color body; Color plates; Color joints; Color horns; Color eyes; };
  void DrawQuadrupedBeast3D(Vector3 position, float rotation_y, float anim_timer, float scale, const BeastPalette* palette);
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
# const BeastPalette DEFAULT_BEAST_PALETTE = { ... };

DEFAULT_BEAST_PALETTE = {
    "body": Color(115, 75, 45, 255),        # Deep leathery predator hide
    "plates": Color(205, 195, 175, 255),    # Weathered bone carapace plates
    "joints": Color(65, 70, 75, 255),       # Dark iron reinforced pivots
    "horns": Color(35, 30, 28, 255),        # Dark horn / chitin crest
    "eyes": Color(255, 175, 25, 255),       # Glowing amber predatory eyes
}

ARCTIC_BEAST_PALETTE = {
    "body": Color(210, 225, 240, 255),      # Frostbitten white fur/hide
    "plates": Color(130, 155, 180, 255),    # Glacial slate bone armor
    "joints": Color(90, 110, 130, 255),     # Chilled steel joints
    "horns": Color(45, 60, 80, 255),        # Deep glacier horn
    "eyes": Color(0, 230, 255, 255),        # Luminescent cyan predator gaze
}

# Named geometric proportions (replaces magic numbers)
CHEST_WIDTH = 0.70
CHEST_HEIGHT = 0.55
CHEST_LENGTH = 1.10
CHEST_ELEVATION = 0.75

PELVIS_WIDTH = 0.60
PELVIS_HEIGHT = 0.45
PELVIS_LENGTH = 0.65
PELVIS_OFFSET_Z = -0.65
PELVIS_ELEVATION = 0.70

SPINE_LENGTH = 1.20
SPINE_RADIUS = 0.10

SKULL_WIDTH = 0.45
SKULL_HEIGHT = 0.38
SKULL_LENGTH = 0.58
NECK_OFFSET_Z = 0.55
NECK_ELEVATION = 0.85

LEG_SPREAD_X = 0.32
LEG_FEMUR_LEN = 0.55
LEG_TIBIA_LEN = 0.50
LEG_RADIUS = 0.08
BALL_JOINT_RADIUS = 0.11
KNEE_RADIUS = 0.07
EYE_RADIUS = 0.04

PAW_WIDTH = 0.18
PAW_HEIGHT = 0.10
PAW_LENGTH = 0.24
CLAW_WIDTH = 0.04
CLAW_HEIGHT = 0.05
CLAW_LENGTH = 0.12

TAIL_SEG_COUNT = 3
TAIL_SEG_LEN = 0.40
TAIL_RADIUS = 0.06

TROTTING_SPEED = 6.0
TAIL_WAVE_SPEED = 5.0
HEAD_BOB_SPEED = 3.0


# ==============================================================================
# PART 4: CANONICAL 3D PROCEDURAL DRAWING FUNCTION
# ==============================================================================
def draw_quadruped_beast_3d(
    position: Vector3,
    rotation_y: float = 0.0,
    anim_timer: float = 0.0,
    scale: float = 1.0,
    palette: dict = None
) -> None:
    """
    Renders an articulated 3D Quadruped Beast at position with procedural walking,
    segmented tail propagation, and head bobbing animation.
    Must be called between begin_mode_3d(camera) and end_mode_3d().

    Parameters:
      position   : World-space base root location (ground level beneath chest).
      rotation_y : Heading angle in DEGREES around Y axis (0 deg = facing +Z).
      anim_timer : Elapsed seconds driving trotting stride, tail wave, and breath.
      scale      : Geometric scaling factor (1.0 = standard beast scale ~2.2m long).
      palette    : Optional dictionary overriding DEFAULT_BEAST_PALETTE colors.
    """
    pal = palette if palette is not None else DEFAULT_BEAST_PALETTE

    c_body = pal["body"]
    c_plates = pal["plates"]
    c_joints = pal["joints"]
    c_horns = pal["horns"]
    c_eyes = pal["eyes"]

    # Kinematics & Wave Calculations
    bounce_y = 0.05 * abs(math.sin(anim_timer * TROTTING_SPEED)) * scale
    head_bob_pitch = 0.08 * math.sin(anim_timer * HEAD_BOB_SPEED)
    
    rad_y = rotation_y * (math.pi / 180.0)
    cos_r = math.cos(rad_y)
    sin_r = math.sin(rad_y)

    bx = position.x
    by = position.y + bounce_y
    bz = position.z

    # Helper: rotate local model-space coordinates around Y axis into world space
    def transform_pt(lx: float, ly: float, lz: float) -> Vector3:
        wx = bx + (lx * cos_r + lz * sin_r) * scale
        wy = by + ly * scale
        wz = bz + (-lx * sin_r + lz * cos_r) * scale
        return Vector3(wx, wy, wz)

    # 1. Torso Carapace (Chest & Ribcage)
    chest_pos = transform_pt(0.0, CHEST_ELEVATION, 0.0)
    draw_cube(chest_pos, CHEST_WIDTH * scale, CHEST_HEIGHT * scale, CHEST_LENGTH * scale, c_body)
    draw_cube_wires(chest_pos, CHEST_WIDTH * scale, CHEST_HEIGHT * scale, CHEST_LENGTH * scale, c_horns)

    # Stepped Dorsal Carapace Plates (3 bone crests along upper ribcage)
    for i in range(3):
        pz = -0.30 + i * 0.30
        plate_h = (0.12 - abs(i - 1) * 0.03) * scale
        plate_pos = transform_pt(0.0, CHEST_ELEVATION + (CHEST_HEIGHT * 0.5) + plate_h * 0.5, pz)
        draw_cube(plate_pos, 0.32 * scale, plate_h, 0.22 * scale, c_plates)

    # 2. Pelvic Hindquarter Mass
    pelvis_pos = transform_pt(0.0, PELVIS_ELEVATION, PELVIS_OFFSET_Z)
    draw_cube(pelvis_pos, PELVIS_WIDTH * scale, PELVIS_HEIGHT * scale, PELVIS_LENGTH * scale, c_body)
    draw_cube_wires(pelvis_pos, PELVIS_WIDTH * scale, PELVIS_HEIGHT * scale, PELVIS_LENGTH * scale, c_horns)

    # Pelvic bone shield
    pelvis_shield_pos = transform_pt(0.0, PELVIS_ELEVATION + (PELVIS_HEIGHT * 0.5) + 0.05, PELVIS_OFFSET_Z)
    draw_cube(pelvis_shield_pos, 0.45 * scale, 0.08 * scale, 0.50 * scale, c_plates)

    # Flexible Spine Connector (Cylinder linking chest and pelvis)
    spine_front = transform_pt(0.0, CHEST_ELEVATION - 0.05, -0.30)
    spine_back = transform_pt(0.0, PELVIS_ELEVATION - 0.05, PELVIS_OFFSET_Z + 0.25)
    draw_cylinder_ex(spine_front, spine_back, SPINE_RADIUS * scale, (SPINE_RADIUS * 0.85) * scale, 6, c_joints)

    # 3. Predatory Skull, Horns & Glowing Amber Eyes
    skull_ly = NECK_ELEVATION + math.sin(head_bob_pitch) * 0.05
    skull_lz = NECK_OFFSET_Z + 0.25
    skull_pos = transform_pt(0.0, skull_ly, skull_lz)
    draw_cube(skull_pos, SKULL_WIDTH * scale, SKULL_HEIGHT * scale, SKULL_LENGTH * scale, c_body)
    draw_cube_wires(skull_pos, SKULL_WIDTH * scale, SKULL_HEIGHT * scale, SKULL_LENGTH * scale, c_horns)

    # Snout Wedge
    snout_pos = transform_pt(0.0, skull_ly - 0.06, skull_lz + 0.26)
    draw_cube(snout_pos, 0.30 * scale, 0.22 * scale, 0.28 * scale, c_plates)

    # Cranial Horns (Twin angular spikes sloping backwards)
    horn_l_base = transform_pt(-0.16, skull_ly + 0.16, skull_lz - 0.05)
    horn_l_tip = transform_pt(-0.24, skull_ly + 0.38, skull_lz - 0.22)
    draw_cylinder_ex(horn_l_base, horn_l_tip, 0.05 * scale, 0.015 * scale, 5, c_horns)

    horn_r_base = transform_pt(0.16, skull_ly + 0.16, skull_lz - 0.05)
    horn_r_tip = transform_pt(0.24, skull_ly + 0.38, skull_lz - 0.22)
    draw_cylinder_ex(horn_r_base, horn_r_tip, 0.05 * scale, 0.015 * scale, 5, c_horns)

    # Glowing Amber Sensory Eyes
    eye_l_pos = transform_pt(-0.19, skull_ly + 0.06, skull_lz + 0.15)
    eye_r_pos = transform_pt(0.19, skull_ly + 0.06, skull_lz + 0.15)
    draw_sphere(eye_l_pos, EYE_RADIUS * scale, c_eyes)
    draw_sphere(eye_r_pos, EYE_RADIUS * scale, c_eyes)

    # 4. Synchronized Quadruped Trotting Legs (FL, FR, HL, HR)
    # Diagonal pairs swing together: FL & HR (phase = 0), FR & HL (phase = pi)
    leg_configs = [
        # (name, hip_lx, hip_ly, hip_lz, phase)
        ("FL", -LEG_SPREAD_X, CHEST_ELEVATION - 0.05, 0.35, 0.0),
        ("FR",  LEG_SPREAD_X, CHEST_ELEVATION - 0.05, 0.35, math.pi),
        ("HL", -LEG_SPREAD_X, PELVIS_ELEVATION - 0.05, PELVIS_OFFSET_Z - 0.10, math.pi),
        ("HR",  LEG_SPREAD_X, PELVIS_ELEVATION - 0.05, PELVIS_OFFSET_Z - 0.10, 0.0),
    ]

    for name, hx, hy, hz, phase in leg_configs:
        swing = math.sin(anim_timer * TROTTING_SPEED + phase)
        thigh_rot = swing * 0.48  # Radians pitch
        knee_flex = max(0.0, math.sin(anim_timer * TROTTING_SPEED + phase + 0.4)) * 0.55

        hip_pt = transform_pt(hx, hy, hz)
        draw_sphere(hip_pt, BALL_JOINT_RADIUS * scale, c_joints)

        # Knee position (femur segment swinging forward/backwards)
        knee_lx = hx
        knee_ly = hy - math.cos(thigh_rot) * LEG_FEMUR_LEN
        knee_lz = hz + math.sin(thigh_rot) * LEG_FEMUR_LEN
        knee_pt = transform_pt(knee_lx, knee_ly, knee_lz)

        draw_cylinder_ex(hip_pt, knee_pt, LEG_RADIUS * scale, (LEG_RADIUS * 0.9) * scale, 6, c_body)
        draw_sphere(knee_pt, KNEE_RADIUS * scale, c_joints)

        # Ankle / Paw position (tibia segment flexing)
        shin_rot = thigh_rot - knee_flex
        foot_lx = knee_lx
        foot_ly = max(0.0, knee_ly - math.cos(shin_rot) * LEG_TIBIA_LEN)
        foot_lz = knee_lz + math.sin(shin_rot) * LEG_TIBIA_LEN
        foot_pt = transform_pt(foot_lx, foot_ly + (PAW_HEIGHT * 0.5), foot_lz)

        draw_cylinder_ex(knee_pt, foot_pt, (LEG_RADIUS * 0.85) * scale, (LEG_RADIUS * 0.75) * scale, 6, c_body)

        # Paw block
        draw_cube(foot_pt, PAW_WIDTH * scale, PAW_HEIGHT * scale, PAW_LENGTH * scale, c_plates)

        # Claws (3 predatory toe claws)
        for c in range(3):
            c_offset_x = (c - 1) * 0.06
            claw_pt = transform_pt(foot_lx + c_offset_x, foot_ly + 0.02, foot_lz + (PAW_LENGTH * 0.5) + (CLAW_LENGTH * 0.5))
            draw_cube(claw_pt, CLAW_WIDTH * scale, CLAW_HEIGHT * scale, CLAW_LENGTH * scale, c_horns)

    # 5. Articulated 3-Segment Tail (Compound Wave Propagation)
    tail_base_lx = 0.0
    tail_base_ly = PELVIS_ELEVATION + 0.08
    tail_base_lz = PELVIS_OFFSET_Z - (PELVIS_LENGTH * 0.5)

    curr_lx = tail_base_lx
    curr_ly = tail_base_ly
    curr_lz = tail_base_lz

    for seg in range(TAIL_SEG_COUNT):
        wave_yaw = math.sin(anim_timer * TAIL_WAVE_SPEED - seg * 0.75) * 0.28
        wave_pitch = math.cos(anim_timer * TAIL_WAVE_SPEED - seg * 0.6) * 0.15 - 0.10

        next_lx = curr_lx + math.sin(wave_yaw) * TAIL_SEG_LEN
        next_ly = curr_ly + math.sin(wave_pitch) * TAIL_SEG_LEN
        next_lz = curr_lz - math.cos(wave_yaw) * TAIL_SEG_LEN

        p_start = transform_pt(curr_lx, curr_ly, curr_lz)
        p_end = transform_pt(next_lx, next_ly, next_lz)

        r_start = (TAIL_RADIUS * (1.0 - seg * 0.22)) * scale
        r_end = (TAIL_RADIUS * (0.8 - seg * 0.22)) * scale

        draw_cylinder_ex(p_start, p_end, r_start, r_end, 5, c_body)
        draw_sphere(p_start, (r_start * 1.15), c_joints)

        curr_lx = next_lx
        curr_ly = next_ly
        curr_lz = next_lz

    # Tail terminal barb
    tail_tip = transform_pt(curr_lx, curr_ly, curr_lz)
    draw_sphere(tail_tip, (TAIL_RADIUS * 0.8) * scale, c_horns)


# ==============================================================================
# PART 5: C++ MAPPING & MEMORY LAYOUT (Zero "Pythonic Magic")
# ==============================================================================
# In C++ (raylib.h), this procedural model requires zero dynamic memory allocation:
#
# struct BeastPalette {
#     Color body;
#     Color plates;
#     Color joints;
#     Color horns;
#     Color eyes;
# };
#
# static const BeastPalette DEFAULT_BEAST_PALETTE = {
#     (Color){115, 75, 45, 255},
#     (Color){205, 195, 175, 255},
#     (Color){65, 70, 75, 255},
#     (Color){35, 30, 28, 255},
#     (Color){255, 175, 25, 255}
# };
#
# void DrawQuadrupedBeast3D(Vector3 position, float rotation_y, float anim_timer, float scale, const BeastPalette* palette);
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
        init_window(self.screen_width, self.screen_height, "3D Model Inspector - Quadruped Beast")
        set_target_fps(60)

        # 3D Orbit Camera Setup
        self.camera = Camera3D(
            Vector3(0.0, 3.2, 5.5),   # Position
            Vector3(0.0, 0.8, 0.0),   # Target
            Vector3(0.0, 1.0, 0.0),   # Up vector
            45.0,                     # FOV
            CAMERA_PERSPECTIVE
        )

        self.anim_timer = 0.0
        self.anim_playing = True
        self.rotation_y = 35.0
        self.active_palette_idx = 0
        self.palettes = [DEFAULT_BEAST_PALETTE, ARCTIC_BEAST_PALETTE]
        self.palette_names = ["Savage Savannah", "Arctic Frost"]

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
            cam_dist = max(2.5, min(14.0, cam_dist - wheel * 0.8))
            self.camera.position.z = cam_dist

    def draw(self):
        begin_drawing()
        clear_background(Color(20, 24, 30, 255))

        # 3D Scene Rendering
        begin_mode_3d(self.camera)
        draw_grid(10, 1.0)
        draw_quadruped_beast_3d(
            Vector3(0.0, 0.0, 0.0),
            rotation_y=self.rotation_y,
            anim_timer=self.anim_timer,
            scale=1.0,
            palette=self.palettes[self.active_palette_idx]
        )
        end_mode_3d()

        # HUD & Telemetry Overlay (Keeps x=450..980 clear for global bar)
        draw_text("3D MODEL INSPECTOR: Quadruped Beast 3D", 24, 20, 20, RAYWHITE)
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
