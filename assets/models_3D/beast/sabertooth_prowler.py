# -*- coding: utf-8 -*-
"""
Cybernetic Sabertooth Prowler - 3D Procedural Primitive Model
============================================================
Category         : beast
Target File      : assets/models_3D/beast/sabertooth_prowler.py
Primitives Used  : Prisms/Cubes (predatory skull, rib cage, scapula), Cylinders (fang blades, legs, counter tail), Spheres (joints, eyes)
Animation Loop   : Low stalk prowl with alternating scapula shoulder shrugs, spine flex, dynamic tail lash

Problem Solved:
  Eliminates bulky 3D mesh files (.obj/.fbx) and external texture dependencies by
  synthesizing an apex cybernetic feline predator with deadly sabertooth fangs,
  articulated shoulder scapulae, and stalking gait purely from Raylib geometric primitives.

How the Procedural Articulation Works:
  - The model hierarchy is computed relative to a base 'position' (Vector3) at ground level.
  - Alternating scapula shrugs: shoulder blades elevate and depress out-of-phase during feline crawl:
    y_shrug = 0.08 * math.sin(anim_timer * 5.0 + phase).
  - Streamlined predator skull carries twin deadly curved sabertooth fangs extruded via angled cylinders.
  - Spine flexes dynamically in pitch while counterweight tail lashes in compound yaw and pitch.
  - Crimson ocular sensors and thermal exhaust vents provide striking cybernetic contrast.

C++ Raylib Equivalent:
  struct SabertoothPalette { Color chassis; Color muscles; Color fangs; Color eyes; Color exhaust; Color joints; };
  void DrawSabertoothProwler3D(Vector3 position, float rotation_y, float anim_timer, float scale, const SabertoothPalette* palette);
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
# const SabertoothPalette DEFAULT_SABERTOOTH_PALETTE = { ... };

DEFAULT_SABERTOOTH_PALETTE = {
    "chassis": Color(55, 60, 68, 255),       # Brushed gunmetal cyber-armor
    "muscles": Color(30, 32, 36, 255),       # Synthetic carbon fiber musculature
    "fangs": Color(240, 245, 250, 255),      # Polished chrome ivory sabertooth fangs
    "eyes": Color(255, 30, 30, 255),         # Predator crimson ocular optics
    "exhaust": Color(255, 130, 0, 255),      # Thermal orange spinal vent glow
    "joints": Color(90, 95, 105, 255),       # Dark titanium reinforced servos
}

NIGHT_STALKER_PALETTE = {
    "chassis": Color(22, 24, 28, 255),       # Matte stealth black plating
    "muscles": Color(14, 15, 17, 255),       # Obsidian nano-fiber weave
    "fangs": Color(180, 210, 230, 255),      # Tempered plasma-cut alloy fangs
    "eyes": Color(0, 255, 150, 255),         # Luminescent toxic neon green optics
    "exhaust": Color(180, 50, 255, 255),     # Violet plasma heatsink exhaust
    "joints": Color(48, 52, 60, 255),        # Midnight carbon titanium
}

# Named geometric proportions (replaces magic numbers)
THORAX_WIDTH = 0.65
THORAX_HEIGHT = 0.55
THORAX_LENGTH = 0.95
THORAX_ELEVATION = 0.78

HINDQUARTERS_WIDTH = 0.58
HINDQUARTERS_HEIGHT = 0.50
HINDQUARTERS_LENGTH = 0.70
HINDQUARTERS_OFFSET_Z = -0.55
HINDQUARTERS_ELEVATION = 0.76

SCAPULA_WIDTH = 0.18
SCAPULA_HEIGHT = 0.40
SCAPULA_LENGTH = 0.35
SCAPULA_SPREAD_X = 0.34
SCAPULA_ELEVATION = 0.92

SKULL_WIDTH = 0.42
SKULL_HEIGHT = 0.36
SKULL_LENGTH = 0.62
NECK_OFFSET_Z = 0.60
NECK_ELEVATION = 0.85

JAW_WIDTH = 0.32
JAW_HEIGHT = 0.16
JAW_LENGTH = 0.44

FANG_RADIUS = 0.04
FANG_LENGTH = 0.48
FANG_OFFSET_X = 0.12
FANG_OFFSET_Y = -0.10
FANG_OFFSET_Z = 0.22

LEG_SPREAD_X = 0.32
LEG_RADIUS = 0.08
LEG_LENGTH = 0.60
SOCKET_RADIUS = 0.10
PAW_WIDTH = 0.20
PAW_HEIGHT = 0.10
PAW_LENGTH = 0.25

TAIL_LENGTH = 1.05
TAIL_RADIUS = 0.05
TAIL_SEGMENTS = 4

STALK_SPEED = 5.0
TAIL_LASH_SPEED = 3.5


# ==============================================================================
# PART 4: CANONICAL 3D PROCEDURAL DRAWING FUNCTION
# ==============================================================================
def draw_sabertooth_prowler_3d(
    position: Vector3,
    rotation_y: float = 0.0,
    anim_timer: float = 0.0,
    scale: float = 1.0,
    palette: dict = None
) -> None:
    """
    Renders an articulated 3D Cybernetic Sabertooth Prowler with procedural predatory stalking,
    alternating scapula shrugging, spine flex, and dynamic counterweight tail lashing.
    Must be called between begin_mode_3d(camera) and end_mode_3d().

    Parameters:
      position   : World-space base root location (ground level beneath chest).
      rotation_y : Heading angle in DEGREES around Y axis (0 deg = facing +Z).
      anim_timer : Elapsed seconds driving creeping stride, scapula shrugs, and tail lash.
      scale      : Geometric scaling factor (1.0 = standard feline predator ~2.3m length).
      palette    : Optional dictionary overriding DEFAULT_SABERTOOTH_PALETTE colors.
    """
    pal = palette if palette is not None else DEFAULT_SABERTOOTH_PALETTE

    c_chassis = pal["chassis"]
    c_muscles = pal["muscles"]
    c_fangs = pal["fangs"]
    c_eyes = pal["eyes"]
    c_exhaust = pal["exhaust"]
    c_joints = pal["joints"]

    rad_y = rotation_y * (math.pi / 180.0)
    cos_r = math.cos(rad_y)
    sin_r = math.sin(rad_y)

    # Dynamic predatory spine flex and stalking micro-elevation
    spine_flex_pitch = 0.06 * math.sin(anim_timer * STALK_SPEED)
    stalk_bob = 0.04 * abs(math.sin(anim_timer * STALK_SPEED)) * scale

    bx = position.x
    by = position.y + stalk_bob
    bz = position.z

    # Helper: rotate local model coordinates to world space
    def transform_pt(lx: float, ly: float, lz: float) -> Vector3:
        wx = bx + (lx * cos_r + lz * sin_r) * scale
        wy = by + ly * scale
        wz = bz + (-lx * sin_r + lz * cos_r) * scale
        return Vector3(wx, wy, wz)

    # 1. Articulated Thoracic Rib Cage (Main Forward Chassis)
    thorax_pos = transform_pt(0.0, THORAX_ELEVATION, 0.0)
    draw_cube(thorax_pos, THORAX_WIDTH * scale, THORAX_HEIGHT * scale, THORAX_LENGTH * scale, c_chassis)
    draw_cube_wires(thorax_pos, THORAX_WIDTH * scale, THORAX_HEIGHT * scale, THORAX_LENGTH * scale, c_muscles)

    # Thermal Spinal Exhaust Vents (3 dorsal glowing radiator vents)
    for v in range(3):
        vz = -0.25 + v * 0.25
        vent_pos = transform_pt(0.0, THORAX_ELEVATION + (THORAX_HEIGHT * 0.5) + 0.04, vz)
        draw_cube(vent_pos, 0.20 * scale, 0.06 * scale, 0.15 * scale, c_exhaust)
        draw_cube_wires(vent_pos, 0.22 * scale, 0.07 * scale, 0.17 * scale, c_joints)

    # 2. Elevated Scapula Blades (Shoulder Shrug Mechanism)
    # Left and right scapulae shrug vertically in opposition during the stalk
    shrug_l = 0.08 * math.sin(anim_timer * STALK_SPEED) * scale
    shrug_r = 0.08 * math.sin(anim_timer * STALK_SPEED + math.pi) * scale

    scap_l_pos = transform_pt(-SCAPULA_SPREAD_X, SCAPULA_ELEVATION + (shrug_l / scale), 0.10)
    scap_r_pos = transform_pt( SCAPULA_SPREAD_X, SCAPULA_ELEVATION + (shrug_r / scale), 0.10)
    draw_cube(scap_l_pos, SCAPULA_WIDTH * scale, SCAPULA_HEIGHT * scale, SCAPULA_LENGTH * scale, c_chassis)
    draw_cube(scap_r_pos, SCAPULA_WIDTH * scale, SCAPULA_HEIGHT * scale, SCAPULA_LENGTH * scale, c_chassis)
    draw_cube_wires(scap_l_pos, SCAPULA_WIDTH * scale, SCAPULA_HEIGHT * scale, SCAPULA_LENGTH * scale, c_joints)
    draw_cube_wires(scap_r_pos, SCAPULA_WIDTH * scale, SCAPULA_HEIGHT * scale, SCAPULA_LENGTH * scale, c_joints)

    # 3. High-Power Hindquarters & Pelvic Chassis
    pelvis_pos = transform_pt(0.0, HINDQUARTERS_ELEVATION, HINDQUARTERS_OFFSET_Z)
    draw_cube(pelvis_pos, HINDQUARTERS_WIDTH * scale, HINDQUARTERS_HEIGHT * scale, HINDQUARTERS_LENGTH * scale, c_muscles)
    draw_cube_wires(pelvis_pos, HINDQUARTERS_WIDTH * scale, HINDQUARTERS_HEIGHT * scale, HINDQUARTERS_LENGTH * scale, c_joints)

    # Pelvic Armored Crest
    pelvis_crest = transform_pt(0.0, HINDQUARTERS_ELEVATION + (HINDQUARTERS_HEIGHT * 0.5) + 0.04, HINDQUARTERS_OFFSET_Z)
    draw_cube(pelvis_crest, 0.38 * scale, 0.06 * scale, 0.45 * scale, c_chassis)

    # Spinal Actuator Coupler (Connects thorax and hindquarters)
    coupler_front = transform_pt(0.0, THORAX_ELEVATION - 0.06, -0.30)
    coupler_back = transform_pt(0.0, HINDQUARTERS_ELEVATION - 0.06, HINDQUARTERS_OFFSET_Z + 0.20)
    draw_cylinder_ex(coupler_front, coupler_back, 0.12 * scale, 0.10 * scale, 6, c_joints)

    # 4. Streamlined Predator Skull, Jaw & Deadly Curved Sabertooth Fangs
    skull_ly = NECK_ELEVATION + math.sin(spine_flex_pitch) * 0.06
    skull_lz = NECK_OFFSET_Z
    skull_pos = transform_pt(0.0, skull_ly, skull_lz)
    draw_cube(skull_pos, SKULL_WIDTH * scale, SKULL_HEIGHT * scale, SKULL_LENGTH * scale, c_chassis)
    draw_cube_wires(skull_pos, SKULL_WIDTH * scale, SKULL_HEIGHT * scale, SKULL_LENGTH * scale, c_joints)

    # Deep predatory lower jaw socket
    jaw_pos = transform_pt(0.0, skull_ly - (SKULL_HEIGHT * 0.40), skull_lz + 0.08)
    draw_cube(jaw_pos, JAW_WIDTH * scale, JAW_HEIGHT * scale, JAW_LENGTH * scale, c_muscles)

    # Glowing Feline Predator Ocular Sensors (Twin Crimson Optics)
    eye_lx = 0.14
    eye_ly = skull_ly + 0.08
    eye_lz = skull_lz + 0.18
    eye_l_pt = transform_pt(-eye_lx, eye_ly, eye_lz)
    eye_r_pt = transform_pt( eye_lx, eye_ly, eye_lz)
    draw_sphere(eye_l_pt, 0.04 * scale, c_eyes)
    draw_sphere(eye_r_pt, 0.04 * scale, c_eyes)

    # Aerodynamic Cranial Ear Fins
    ear_l_base = transform_pt(-0.16, skull_ly + 0.14, skull_lz - 0.12)
    ear_l_tip = transform_pt(-0.22, skull_ly + 0.30, skull_lz - 0.24)
    ear_r_base = transform_pt( 0.16, skull_ly + 0.14, skull_lz - 0.12)
    ear_r_tip = transform_pt( 0.22, skull_ly + 0.30, skull_lz - 0.24)
    draw_cylinder_ex(ear_l_base, ear_l_tip, 0.04 * scale, 0.01 * scale, 4, c_chassis)
    draw_cylinder_ex(ear_r_base, ear_r_tip, 0.04 * scale, 0.01 * scale, 4, c_chassis)

    # Twin Deadly Curved Sabertooth Fangs (Attached to maxilla, curving downwards & slightly backwards)
    for fx_sign in (-1.0, 1.0):
        fx = fx_sign * FANG_OFFSET_X
        # Upper root
        fang_root = transform_pt(fx, skull_ly + FANG_OFFSET_Y, skull_lz + FANG_OFFSET_Z)
        # Midpoint curve
        fang_mid = transform_pt(fx, skull_ly + FANG_OFFSET_Y - (FANG_LENGTH * 0.55), skull_lz + FANG_OFFSET_Z - 0.04)
        # Sharp predatory tip
        fang_tip = transform_pt(fx, skull_ly + FANG_OFFSET_Y - FANG_LENGTH, skull_lz + FANG_OFFSET_Z - 0.09)

        draw_cylinder_ex(fang_root, fang_mid, FANG_RADIUS * scale, (FANG_RADIUS * 0.7) * scale, 6, c_fangs)
        draw_cylinder_ex(fang_mid, fang_tip, (FANG_RADIUS * 0.7) * scale, 0.008 * scale, 6, c_fangs)

    # 5. Four Carbon-Reinforced Feline Limbs (Creeping Stalk Stride)
    leg_stalk_configs = [
        # (name, lx, lz, phase)
        ("FL", -LEG_SPREAD_X,  0.30, 0.0),
        ("FR",  LEG_SPREAD_X,  0.30, math.pi),
        ("HL", -LEG_SPREAD_X, HINDQUARTERS_OFFSET_Z - 0.05, math.pi),
        ("HR",  LEG_SPREAD_X, HINDQUARTERS_OFFSET_Z - 0.05, 0.0),
    ]

    for name, lx, lz, phase in leg_stalk_configs:
        stride_rot = math.sin(anim_timer * STALK_SPEED + phase) * 0.50
        hip_ly = THORAX_ELEVATION - 0.08 if "F" in name else HINDQUARTERS_ELEVATION - 0.08

        hip_pt = transform_pt(lx, hip_ly, lz)
        draw_sphere(hip_pt, SOCKET_RADIUS * scale, c_joints)

        # Femur / Upper limb
        knee_lx = lx
        knee_ly = hip_ly - math.cos(stride_rot) * (LEG_LENGTH * 0.55)
        knee_lz = lz + math.sin(stride_rot) * (LEG_LENGTH * 0.55)
        knee_pt = transform_pt(knee_lx, knee_ly, knee_lz)

        draw_cylinder_ex(hip_pt, knee_pt, LEG_RADIUS * scale, (LEG_RADIUS * 0.85) * scale, 6, c_chassis)
        draw_sphere(knee_pt, (SOCKET_RADIUS * 0.75) * scale, c_joints)

        # Tibia / Shin to ground paw
        foot_lx = knee_lx
        foot_ly = 0.0
        foot_lz = knee_lz + math.sin(stride_rot * 0.6) * (LEG_LENGTH * 0.50)
        foot_pt = transform_pt(foot_lx, foot_ly + (PAW_HEIGHT * 0.5), foot_lz)

        draw_cylinder_ex(knee_pt, foot_pt, (LEG_RADIUS * 0.8) * scale, (LEG_RADIUS * 0.65) * scale, 6, c_muscles)

        # Prowler Clawed Paw
        draw_cube(foot_pt, PAW_WIDTH * scale, PAW_HEIGHT * scale, PAW_LENGTH * scale, c_chassis)
        # Claws
        for c in range(3):
            c_offset = (c - 1) * 0.06
            c_tip = transform_pt(foot_lx + c_offset, foot_ly, foot_lz + (PAW_LENGTH * 0.5) + 0.08)
            draw_sphere(c_tip, 0.025 * scale, c_fangs)

    # 6. Counterweight Balance Tail (Lashing Compound Wave)
    curr_lx = 0.0
    curr_ly = HINDQUARTERS_ELEVATION + 0.05
    curr_lz = HINDQUARTERS_OFFSET_Z - (HINDQUARTERS_LENGTH * 0.5)

    seg_len = TAIL_LENGTH / float(TAIL_SEGMENTS)
    for s in range(TAIL_SEGMENTS):
        yaw = math.sin(anim_timer * TAIL_LASH_SPEED - s * 0.7) * 0.35
        pitch = 0.12 * math.cos(anim_timer * TAIL_LASH_SPEED - s * 0.5) + (s * 0.08)

        next_lx = curr_lx + math.sin(yaw) * seg_len
        next_ly = curr_ly + math.sin(pitch) * seg_len
        next_lz = curr_lz - math.cos(yaw) * seg_len

        t_start = transform_pt(curr_lx, curr_ly, curr_lz)
        t_end = transform_pt(next_lx, next_ly, next_lz)

        r_start = (TAIL_RADIUS * (1.0 - s * 0.18)) * scale
        r_end = (TAIL_RADIUS * (0.85 - s * 0.18)) * scale

        draw_cylinder_ex(t_start, t_end, r_start, r_end, 5, c_chassis)
        draw_sphere(t_start, r_start * 1.1, c_joints)

        curr_lx = next_lx
        curr_ly = next_ly
        curr_lz = next_lz

    # Terminal counterweight barb
    tail_tip_pt = transform_pt(curr_lx, curr_ly, curr_lz)
    draw_cube(tail_tip_pt, 0.08 * scale, 0.08 * scale, 0.16 * scale, c_fangs)


# ==============================================================================
# PART 5: C++ MAPPING & MEMORY LAYOUT (Zero "Pythonic Magic")
# ==============================================================================
# In C++ (raylib.h), this procedural model requires zero dynamic memory allocation:
#
# struct SabertoothPalette {
#     Color chassis;
#     Color muscles;
#     Color fangs;
#     Color eyes;
#     Color exhaust;
#     Color joints;
# };
#
# static const SabertoothPalette DEFAULT_SABERTOOTH_PALETTE = {
#     (Color){55, 60, 68, 255},
#     (Color){30, 32, 36, 255},
#     (Color){240, 245, 250, 255},
#     (Color){255, 30, 30, 255},
#     (Color){255, 130, 0, 255},
#     (Color){90, 95, 105, 255}
# };
#
# void DrawSabertoothProwler3D(Vector3 position, float rotation_y, float anim_timer, float scale, const SabertoothPalette* palette);
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
        init_window(self.screen_width, self.screen_height, "3D Model Inspector - Cybernetic Sabertooth Prowler")
        set_target_fps(60)

        # 3D Orbit Camera Setup
        self.camera = Camera3D(
            Vector3(0.0, 3.0, 5.2),   # Position
            Vector3(0.0, 0.8, 0.0),   # Target
            Vector3(0.0, 1.0, 0.0),   # Up vector
            45.0,                     # FOV
            CAMERA_PERSPECTIVE
        )

        self.anim_timer = 0.0
        self.anim_playing = True
        self.rotation_y = 30.0
        self.active_palette_idx = 0
        self.palettes = [DEFAULT_SABERTOOTH_PALETTE, NIGHT_STALKER_PALETTE]
        self.palette_names = ["Gunmetal Predator", "Night Stalker"]

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
            cam_dist = max(2.0, min(14.0, cam_dist - wheel * 0.8))
            self.camera.position.z = cam_dist

    def draw(self):
        begin_drawing()
        clear_background(Color(18, 20, 26, 255))

        # 3D Scene Rendering
        begin_mode_3d(self.camera)
        draw_grid(10, 1.0)
        draw_sabertooth_prowler_3d(
            Vector3(0.0, 0.0, 0.0),
            rotation_y=self.rotation_y,
            anim_timer=self.anim_timer,
            scale=1.0,
            palette=self.palettes[self.active_palette_idx]
        )
        end_mode_3d()

        # HUD & Telemetry Overlay (Keeps x=450..980 clear for global bar)
        draw_text("3D MODEL INSPECTOR: Cybernetic Sabertooth Prowler", 24, 20, 20, RAYWHITE)
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
