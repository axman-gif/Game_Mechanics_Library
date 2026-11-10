# -*- coding: utf-8 -*-
"""
Bionic Glacier Bear - 3D Procedural Primitive Model
===================================================
Category         : beast
Target File      : assets/models_3D/beast/glacier_bear.py
Primitives Used  : Prisms/Cubes (heavy barrel chest torso, armored dorsal hump, skull wedge), Cylinders (4 hydraulic pillar legs, neck sleeve collar, 10 tungsten claws), Spheres (shoulder armor caps, rounded snout muzzle, dual optical lenses)
Animation Loop   : Heavy lumbering quadruped plantigrade stride, lateral shoulder roll, deep ribcage expansion, counter-balance head sway & snorting jaw

Problem Solved:
  Eliminates bulky 3D mesh files (.obj/.fbx) and external texture dependencies by
  synthesizing a heavy cybernetic arctic predator purely from Raylib geometric
  primitives, hierarchical kinematics, and procedural articulation in real time.

How the Procedural Articulation Works:
  - Ground anchor at (0, 0, 0); massive torso chassis centered at y = 0.70.
  - Alternating diagonal leg pairs step with sinusoidal swing:
    leg_rot = math.sin(anim_timer * 3.0 + phase) * 0.40 rad
  - Vertical plantigrade foot lifting:
    lift = max(0.0, math.sin(anim_timer * 3.0 + phase)) * 0.14
  - Massive torso oscillates with heavy lateral shoulder roll:
    roll = 0.08 * math.sin(anim_timer * 3.0)
  - Ribcage expands in deep breathing cadence:
    breath_scale = 1.0 + 0.03 * math.cos(anim_timer * 1.4)
  - Cranial skull socket articulates with counter-balance sway, pitch, and snorting jaw breathing.

C++ Raylib Equivalent:
  struct GlacierBearPalette {
      Color fur_frost;
      Color armor_carbon;
      Color cyber_ice;
      Color optic_blue;
      Color claw_titanium;
  };
  void DrawGlacierBear3D(Vector3 position, float rotation_y, float anim_timer, float scale, const GlacierBearPalette* palette, bool show_wireframe);
  Mapped directly to DrawCube, DrawCubeWires, DrawSphere, DrawSphereWires, DrawCylinderEx, and DrawCylinderWiresEx from raylib.h.
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
# const GlacierBearPalette DEFAULT_GLACIER_BEAR_PALETTE = { ... };

DEFAULT_GLACIER_BEAR_PALETTE = {
    "fur_frost": Color(230, 240, 250, 255),       # Weathered polar off-white
    "armor_carbon": Color(45, 50, 58, 255),       # Dark tungsten chassis plating
    "cyber_ice": Color(100, 210, 255, 255),       # Translucent glacial cyan crystal
    "optic_blue": Color(0, 180, 255, 255),        # Illuminated cerulean scanner
    "claw_titanium": Color(190, 200, 215, 255),   # Metallic titanium alloy
}

VOLCANIC_BEAR_PALETTE = {
    "fur_frost": Color(60, 55, 50, 255),          # Charred volcanic fur
    "armor_carbon": Color(30, 28, 26, 255),       # Scorched iron chassis
    "cyber_ice": Color(255, 120, 30, 255),        # Molten magma conduits
    "optic_blue": Color(255, 50, 20, 255),        # Warning flare red optic
    "claw_titanium": Color(140, 110, 90, 255),    # Heat-treated bronze talons
}

# Named geometric proportions (Zero magic numbers)
TORSO_WIDTH = 0.90
TORSO_HEIGHT = 0.75
TORSO_LENGTH = 1.35
TORSO_ELEVATION = 0.70

HUMP_WIDTH = 0.65
HUMP_HEIGHT = 0.35
HUMP_LENGTH = 0.50
HUMP_OFFSET_Z = 0.18

SKULL_WIDTH = 0.42
SKULL_HEIGHT = 0.38
SKULL_LENGTH = 0.55
SKULL_SOCKET_Y = 0.90
SKULL_SOCKET_Z = 0.85

JAW_WIDTH = 0.34
JAW_HEIGHT = 0.16
JAW_LENGTH = 0.44

NECK_RADIUS = 0.30
NECK_LENGTH = 0.35

SHOULDER_SPREAD_X = 0.48
SHOULDER_ELEVATION = 0.75
SHOULDER_OFFSET_Z = 0.45
SHOULDER_CAP_RADIUS = 0.22

HIP_SPREAD_X = 0.42
HIP_ELEVATION = 0.68
HIP_OFFSET_Z = -0.48
HIP_CAP_RADIUS = 0.19

LEG_RADIUS = 0.16
LEG_LENGTH = 0.65
PAW_WIDTH = 0.32
PAW_HEIGHT = 0.12
PAW_LENGTH = 0.36

CLAW_RADIUS = 0.025
CLAW_LENGTH = 0.18
CLAW_COUNT_PER_FRONT_PAW = 5

SNOUT_RADIUS = 0.14
OPTIC_RADIUS = 0.05
OPTIC_OFFSET_X = 0.15
OPTIC_OFFSET_Y = 0.07
OPTIC_OFFSET_Z = 0.14

GAIT_SPEED = 3.0
BREATH_SPEED = 1.4


# ==============================================================================
# PART 4: CANONICAL 3D PROCEDURAL DRAWING FUNCTION
# ==============================================================================
def draw_glacier_bear_3d(
    position: Vector3,
    rotation_y: float = 0.0,
    anim_timer: float = 0.0,
    scale: float = 1.0,
    palette: dict = None,
    show_wireframe: bool = False
) -> None:
    """
    Renders an articulated 3D Bionic Glacier Bear with heavy quadruped plantigrade gait,
    lateral shoulder roll, ribcage breathing expansion, snorting jaw, and 10 tungsten claws.
    Must be called between begin_mode_3d(camera) and end_mode_3d().

    Parameters:
      position       : World-space base root location (ground level beneath chassis).
      rotation_y     : Heading angle in DEGREES around Y axis (0 deg = facing +Z).
      anim_timer     : Elapsed seconds driving lumbering stride, roll, and breathing.
      scale          : Geometric scaling factor (1.0 = standard polar titan ~2.8m length).
      palette        : Optional dictionary overriding DEFAULT_GLACIER_BEAR_PALETTE colors.
      show_wireframe : Boolean flag toggling wireframe topology rendering.
    """
    pal = palette if palette is not None else DEFAULT_GLACIER_BEAR_PALETTE

    c_fur = pal["fur_frost"]
    c_armor = pal["armor_carbon"]
    c_ice = pal["cyber_ice"]
    c_optic = pal["optic_blue"]
    c_claw = pal["claw_titanium"]

    # Kinematics calculations
    roll = 0.08 * math.sin(anim_timer * GAIT_SPEED)
    body_heave = 0.025 * math.cos(anim_timer * (GAIT_SPEED * 2.0))
    breath_scale = 1.0 + 0.03 * math.cos(anim_timer * BREATH_SPEED)
    head_bob_y = 0.035 * math.sin(anim_timer * GAIT_SPEED + 0.6)
    head_sway_x = 0.025 * math.sin(anim_timer * GAIT_SPEED)
    jaw_drop = max(0.0, math.sin(anim_timer * 1.5)) * 0.06

    rad_y = rotation_y * (math.pi / 180.0)
    cos_r = math.cos(rad_y)
    sin_r = math.sin(rad_y)

    bx = position.x
    by = position.y
    bz = position.z

    # Transform local model space to world space
    def transform_pt(lx: float, ly: float, lz: float) -> Vector3:
        wx = bx + (lx * cos_r + lz * sin_r) * scale
        wy = by + ly * scale
        wz = bz + (-lx * sin_r + lz * cos_r) * scale
        return Vector3(wx, wy, wz)

    # Transform torso-relative coordinates incorporating lateral shoulder roll
    cos_roll = math.cos(roll)
    sin_roll = math.sin(roll)
    torso_cy = TORSO_ELEVATION + body_heave

    def roll_torso_pt(tx: float, ty: float, tz: float) -> Vector3:
        lx = tx * cos_roll - ty * sin_roll
        ly = torso_cy + tx * sin_roll + ty * cos_roll
        lz = tz
        return transform_pt(lx, ly, lz)

    # --------------------------------------------------------------------------
    # 1. Main Barrel Chest Torso & Cyber Chassis Plating
    # --------------------------------------------------------------------------
    t_width = TORSO_WIDTH * breath_scale * scale
    t_height = TORSO_HEIGHT * breath_scale * scale
    t_length = TORSO_LENGTH * scale

    torso_pos = roll_torso_pt(0.0, 0.0, 0.0)
    draw_cube(torso_pos, t_width, t_height, t_length, c_fur)
    if show_wireframe:
        draw_cube_wires(torso_pos, t_width, t_height, t_length, c_ice)
    else:
        draw_cube_wires(torso_pos, t_width, t_height, t_length, c_armor)

    # Flank armor plating (Left & Right tungsten chassis slabs)
    flank_w = 0.08 * scale
    flank_h = (t_height * 0.70)
    flank_l = (t_length * 0.75)
    flank_l_pos = roll_torso_pt(-TORSO_WIDTH * 0.50 * breath_scale - 0.02, -0.04, 0.0)
    flank_r_pos = roll_torso_pt( TORSO_WIDTH * 0.50 * breath_scale + 0.02, -0.04, 0.0)
    draw_cube(flank_l_pos, flank_w, flank_h, flank_l, c_armor)
    draw_cube(flank_r_pos, flank_w, flank_h, flank_l, c_armor)
    if show_wireframe:
        draw_cube_wires(flank_l_pos, flank_w, flank_h, flank_l, c_ice)
        draw_cube_wires(flank_r_pos, flank_w, flank_h, flank_l, c_ice)

    # Ventral underbelly keel plate
    belly_pos = roll_torso_pt(0.0, -TORSO_HEIGHT * 0.50 * breath_scale - 0.02, -0.05)
    draw_cube(belly_pos, 0.62 * scale, 0.08 * scale, 1.05 * scale, c_armor)

    # Dorsal cyber-ice energy spine crystals (4 illuminated nodes)
    for i in range(4):
        cz = -0.42 + i * 0.28
        cry_pos = roll_torso_pt(0.0, (TORSO_HEIGHT * 0.50 * breath_scale) + 0.04, cz)
        draw_cube(cry_pos, 0.14 * scale, 0.09 * scale, 0.16 * scale, c_ice)
        if show_wireframe:
            draw_cube_wires(cry_pos, 0.15 * scale, 0.10 * scale, 0.17 * scale, c_optic)

    # --------------------------------------------------------------------------
    # 2. Armored Dorsal Muscle Hump
    # --------------------------------------------------------------------------
    hump_pos = roll_torso_pt(0.0, (TORSO_HEIGHT * 0.50 * breath_scale) + (HUMP_HEIGHT * 0.40), HUMP_OFFSET_Z)
    draw_cube(hump_pos, HUMP_WIDTH * scale, HUMP_HEIGHT * scale, HUMP_LENGTH * scale, c_fur)
    if show_wireframe:
        draw_cube_wires(hump_pos, HUMP_WIDTH * scale, HUMP_HEIGHT * scale, HUMP_LENGTH * scale, c_ice)
    else:
        draw_cube_wires(hump_pos, HUMP_WIDTH * scale, HUMP_HEIGHT * scale, HUMP_LENGTH * scale, c_armor)

    # Hump reinforced dorsal armor cowl
    hump_cowl_pos = roll_torso_pt(0.0, (TORSO_HEIGHT * 0.50 * breath_scale) + HUMP_HEIGHT + 0.02, HUMP_OFFSET_Z)
    draw_cube(hump_cowl_pos, 0.52 * scale, 0.08 * scale, 0.44 * scale, c_armor)

    # Dual cryo-exhaust vent ports on dorsal hump
    vent_l = roll_torso_pt(-0.16, (TORSO_HEIGHT * 0.50 * breath_scale) + HUMP_HEIGHT * 0.65, HUMP_OFFSET_Z - 0.12)
    vent_r = roll_torso_pt( 0.16, (TORSO_HEIGHT * 0.50 * breath_scale) + HUMP_HEIGHT * 0.65, HUMP_OFFSET_Z - 0.12)
    draw_cube(vent_l, 0.08 * scale, 0.06 * scale, 0.12 * scale, c_ice)
    draw_cube(vent_r, 0.08 * scale, 0.06 * scale, 0.12 * scale, c_ice)

    # --------------------------------------------------------------------------
    # 3. Shoulder Sockets & Massive Ball-and-Socket Armor Caps
    # --------------------------------------------------------------------------
    sh_y_rel = SHOULDER_ELEVATION - TORSO_ELEVATION
    sh_l_pos = roll_torso_pt(-SHOULDER_SPREAD_X, sh_y_rel, SHOULDER_OFFSET_Z)
    sh_r_pos = roll_torso_pt( SHOULDER_SPREAD_X, sh_y_rel, SHOULDER_OFFSET_Z)

    draw_sphere(sh_l_pos, SHOULDER_CAP_RADIUS * scale, c_armor)
    draw_sphere(sh_r_pos, SHOULDER_CAP_RADIUS * scale, c_armor)
    if show_wireframe:
        draw_sphere_wires(sh_l_pos, SHOULDER_CAP_RADIUS * scale, 8, 8, c_ice)
        draw_sphere_wires(sh_r_pos, SHOULDER_CAP_RADIUS * scale, 8, 8, c_ice)

    # Concentric cyber-ice emitter core on shoulder caps
    draw_sphere(sh_l_pos, (SHOULDER_CAP_RADIUS * 0.55) * scale, c_ice)
    draw_sphere(sh_r_pos, (SHOULDER_CAP_RADIUS * 0.55) * scale, c_ice)

    # --------------------------------------------------------------------------
    # 4. Hip Sockets & Pelvic Joint Caps
    # --------------------------------------------------------------------------
    hip_y_rel = HIP_ELEVATION - TORSO_ELEVATION
    hip_l_pos = roll_torso_pt(-HIP_SPREAD_X, hip_y_rel, HIP_OFFSET_Z)
    hip_r_pos = roll_torso_pt( HIP_SPREAD_X, hip_y_rel, HIP_OFFSET_Z)

    draw_sphere(hip_l_pos, HIP_CAP_RADIUS * scale, c_armor)
    draw_sphere(hip_r_pos, HIP_CAP_RADIUS * scale, c_armor)
    if show_wireframe:
        draw_sphere_wires(hip_l_pos, HIP_CAP_RADIUS * scale, 8, 8, c_ice)
        draw_sphere_wires(hip_r_pos, HIP_CAP_RADIUS * scale, 8, 8, c_ice)

    # --------------------------------------------------------------------------
    # 5. Thick Neck Sleeve Collar
    # --------------------------------------------------------------------------
    neck_start = roll_torso_pt(0.0, 0.12, 0.50)
    neck_end = transform_pt(head_sway_x, SKULL_SOCKET_Y + head_bob_y - 0.05, SKULL_SOCKET_Z - 0.12)
    draw_cylinder_ex(neck_start, neck_end, NECK_RADIUS * scale, (NECK_RADIUS * 0.88) * scale, 8, c_armor)
    if show_wireframe:
        draw_cylinder_wires_ex(neck_start, neck_end, NECK_RADIUS * scale, (NECK_RADIUS * 0.88) * scale, 8, c_ice)

    # Glowing glacial sleeve ring
    mid_neck = transform_pt(
        head_sway_x * 0.5,
        ((TORSO_ELEVATION + body_heave + 0.12) + (SKULL_SOCKET_Y + head_bob_y - 0.05)) * 0.5,
        (0.50 + SKULL_SOCKET_Z - 0.12) * 0.5
    )
    draw_sphere(mid_neck, (NECK_RADIUS * 0.95) * scale, c_ice)

    # --------------------------------------------------------------------------
    # 6. Angular Cybernetic Skull Wedge, Rounded Snout Muzzle & Dual Optics
    # --------------------------------------------------------------------------
    skull_cy = SKULL_SOCKET_Y + head_bob_y
    skull_cz = SKULL_SOCKET_Z
    skull_pos = transform_pt(head_sway_x, skull_cy, skull_cz)

    # Main cranial skull prism
    draw_cube(skull_pos, SKULL_WIDTH * scale, SKULL_HEIGHT * scale, SKULL_LENGTH * scale, c_fur)
    if show_wireframe:
        draw_cube_wires(skull_pos, SKULL_WIDTH * scale, SKULL_HEIGHT * scale, SKULL_LENGTH * scale, c_ice)
    else:
        draw_cube_wires(skull_pos, SKULL_WIDTH * scale, SKULL_HEIGHT * scale, SKULL_LENGTH * scale, c_armor)

    # Armored cranial brow plate
    brow_pos = transform_pt(head_sway_x, skull_cy + (SKULL_HEIGHT * 0.50) + 0.03, skull_cz)
    draw_cube(brow_pos, (SKULL_WIDTH * 0.85) * scale, 0.07 * scale, (SKULL_LENGTH * 0.80) * scale, c_armor)

    # Rounded snout muzzle
    snout_pos = transform_pt(head_sway_x, skull_cy - 0.06, skull_cz + (SKULL_LENGTH * 0.50) + 0.06)
    draw_sphere(snout_pos, SNOUT_RADIUS * scale, c_armor)
    if show_wireframe:
        draw_sphere_wires(snout_pos, SNOUT_RADIUS * scale, 8, 8, c_ice)

    # Dual cybernetic sensory optical lenses
    eye_l_pos = transform_pt(head_sway_x - OPTIC_OFFSET_X, skull_cy + OPTIC_OFFSET_Y, skull_cz + OPTIC_OFFSET_Z)
    eye_r_pos = transform_pt(head_sway_x + OPTIC_OFFSET_X, skull_cy + OPTIC_OFFSET_Y, skull_cz + OPTIC_OFFSET_Z)
    draw_sphere(eye_l_pos, OPTIC_RADIUS * scale, c_optic)
    draw_sphere(eye_r_pos, OPTIC_RADIUS * scale, c_optic)
    if show_wireframe:
        draw_sphere_wires(eye_l_pos, OPTIC_RADIUS * scale, 6, 6, WHITE)
        draw_sphere_wires(eye_r_pos, OPTIC_RADIUS * scale, 6, 6, WHITE)

    # Articulated snorting lower cyber jaw wedge
    jaw_pos = transform_pt(head_sway_x, skull_cy - (SKULL_HEIGHT * 0.48) - jaw_drop, skull_cz + 0.08)
    draw_cube(jaw_pos, JAW_WIDTH * scale, JAW_HEIGHT * scale, JAW_LENGTH * scale, c_armor)
    if show_wireframe:
        draw_cube_wires(jaw_pos, JAW_WIDTH * scale, JAW_HEIGHT * scale, JAW_LENGTH * scale, c_ice)

    # Cyber acoustic sensor ears
    ear_l_base = transform_pt(head_sway_x - 0.18, skull_cy + (SKULL_HEIGHT * 0.42), skull_cz - 0.12)
    ear_l_tip  = transform_pt(head_sway_x - 0.24, skull_cy + (SKULL_HEIGHT * 0.70), skull_cz - 0.18)
    ear_r_base = transform_pt(head_sway_x + 0.18, skull_cy + (SKULL_HEIGHT * 0.42), skull_cz - 0.12)
    ear_r_tip  = transform_pt(head_sway_x + 0.24, skull_cy + (SKULL_HEIGHT * 0.70), skull_cz - 0.18)
    draw_cylinder_ex(ear_l_base, ear_l_tip, 0.05 * scale, 0.02 * scale, 6, c_armor)
    draw_cylinder_ex(ear_r_base, ear_r_tip, 0.05 * scale, 0.02 * scale, 6, c_armor)

    # --------------------------------------------------------------------------
    # 7. Four Heavy Plantigrade Hydraulic Pillar Legs & 10 Tungsten Claws
    # --------------------------------------------------------------------------
    # Diagonal phase pairing: Front-Left & Hind-Right, Front-Right & Hind-Left
    leg_configs = [
        # (name, lx, lz, phase, is_front)
        ("FL", -SHOULDER_SPREAD_X, SHOULDER_OFFSET_Z, 0.0, True),
        ("FR",  SHOULDER_SPREAD_X, SHOULDER_OFFSET_Z, math.pi, True),
        ("HL", -HIP_SPREAD_X,      HIP_OFFSET_Z,      math.pi, False),
        ("HR",  HIP_SPREAD_X,      HIP_OFFSET_Z,      0.0, False),
    ]

    for name, lx, lz, phase, is_front in leg_configs:
        leg_rot = math.sin(anim_timer * GAIT_SPEED + phase) * 0.40
        lift = max(0.0, math.sin(anim_timer * GAIT_SPEED + phase)) * 0.14
        pivot_y = SHOULDER_ELEVATION if is_front else HIP_ELEVATION

        root_pt = transform_pt(lx, pivot_y, lz)

        # Hydraulic knee / hock pivot joint
        knee_y = pivot_y - (LEG_LENGTH * 0.50) + lift * 0.55
        knee_z = lz + math.sin(leg_rot) * (LEG_LENGTH * 0.45)
        knee_pt = transform_pt(lx, knee_y, knee_z)

        # Upper leg pillar cylinder
        draw_cylinder_ex(root_pt, knee_pt, LEG_RADIUS * scale, (LEG_RADIUS * 0.90) * scale, 8, c_armor)
        draw_sphere(knee_pt, (LEG_RADIUS * 0.88) * scale, c_armor)
        if show_wireframe:
            draw_cylinder_wires_ex(root_pt, knee_pt, LEG_RADIUS * scale, (LEG_RADIUS * 0.90) * scale, 8, c_ice)

        # Lower leg hydraulic pillar down to ankle
        foot_y = lift
        foot_z = lz + math.sin(leg_rot) * (LEG_LENGTH * 0.88)
        ankle_pt = transform_pt(lx, foot_y + (PAW_HEIGHT * 0.50), foot_z)

        draw_cylinder_ex(knee_pt, ankle_pt, (LEG_RADIUS * 0.85) * scale, (LEG_RADIUS * 0.80) * scale, 8, c_fur)
        if show_wireframe:
            draw_cylinder_wires_ex(knee_pt, ankle_pt, (LEG_RADIUS * 0.85) * scale, (LEG_RADIUS * 0.80) * scale, 8, c_ice)

        # Plantigrade heavy paw pad
        paw_center = transform_pt(lx, foot_y + (PAW_HEIGHT * 0.50), foot_z + 0.05)
        draw_cube(paw_center, PAW_WIDTH * scale, PAW_HEIGHT * scale, PAW_LENGTH * scale, c_armor)
        if show_wireframe:
            draw_cube_wires(paw_center, PAW_WIDTH * scale, PAW_HEIGHT * scale, PAW_LENGTH * scale, c_ice)

        # 10 Tungsten Talon Claws (5 claws on Front-Left, 5 claws on Front-Right)
        if is_front:
            for claw_idx in range(CLAW_COUNT_PER_FRONT_PAW):
                # Spread claws symmetrically across front curved rim of paw
                spread = -0.11 + claw_idx * 0.055
                claw_lx = lx + spread
                claw_root_y = foot_y + 0.03
                claw_root_z = foot_z + (PAW_LENGTH * 0.50) + 0.04

                c_root = transform_pt(claw_lx, claw_root_y, claw_root_z)
                c_tip  = transform_pt(claw_lx + spread * 0.3, claw_root_y - 0.08, claw_root_z + CLAW_LENGTH)

                draw_cylinder_ex(c_root, c_tip, CLAW_RADIUS * scale, (CLAW_RADIUS * 0.30) * scale, 6, c_claw)
                if show_wireframe:
                    draw_cylinder_wires_ex(c_root, c_tip, CLAW_RADIUS * scale, (CLAW_RADIUS * 0.30) * scale, 6, c_ice)
        else:
            # Hind traction cleats (3 rear ground anchors per hind foot)
            for cleat_idx in range(3):
                c_spread = -0.08 + cleat_idx * 0.08
                cleat_root = transform_pt(lx + c_spread, foot_y + 0.02, foot_z + (PAW_LENGTH * 0.50))
                cleat_tip  = transform_pt(lx + c_spread, foot_y - 0.04, foot_z + (PAW_LENGTH * 0.50) + 0.08)
                draw_cylinder_ex(cleat_root, cleat_tip, (CLAW_RADIUS * 0.8) * scale, (CLAW_RADIUS * 0.2) * scale, 4, c_claw)

    # --------------------------------------------------------------------------
    # 8. Stubby Armored Polar Tail
    # --------------------------------------------------------------------------
    tail_root = roll_torso_pt(0.0, 0.06, -TORSO_LENGTH * 0.50)
    tail_tip  = roll_torso_pt(0.0, -0.06, -TORSO_LENGTH * 0.50 - 0.18)
    draw_cylinder_ex(tail_root, tail_tip, 0.11 * scale, 0.05 * scale, 6, c_fur)
    if show_wireframe:
        draw_cylinder_wires_ex(tail_root, tail_tip, 0.11 * scale, 0.05 * scale, 6, c_ice)


# ==============================================================================
# PART 5: STANDALONE 3D ORBIT VIEWER (ModelViewerApp)
# ==============================================================================
class ModelViewerApp:
    """
    Interactive 3D previewer allowing inspection, turntable rotation, zooming,
    wireframe toggling, palette swapping, and automated 3-frame smoke testing.
    """
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        init_window(self.screen_width, self.screen_height, "3D Model Inspector - Bionic Glacier Bear")
        set_target_fps(60)

        # 3D Orbit Camera Setup
        self.camera = Camera3D(
            Vector3(0.0, 2.6, 5.0),   # Position
            Vector3(0.0, 0.75, 0.0),  # Target
            Vector3(0.0, 1.0, 0.0),   # Up vector
            45.0,                     # FOV
            CAMERA_PERSPECTIVE
        )

        self.anim_timer = 0.0
        self.anim_playing = True
        self.rotation_y = 25.0
        self.show_wireframe = False
        self.active_palette_idx = 0
        self.palettes = [DEFAULT_GLACIER_BEAR_PALETTE, VOLCANIC_BEAR_PALETTE]
        self.palette_names = ["Frost Glacier (Default)", "Volcanic Magma"]

    def update(self):
        dt = min(get_frame_time(), 0.05)
        if self.anim_playing:
            self.anim_timer += dt

        # Orbit Controls: Drag mouse left-click or use arrow keys
        if is_mouse_button_down(MOUSE_BUTTON_LEFT):
            delta = get_mouse_delta()
            self.rotation_y += delta.x * 0.5
            self.camera.position.y = max(0.5, min(7.0, self.camera.position.y - delta.y * 0.01))

        if is_key_down(KEY_LEFT):
            self.rotation_y -= 60.0 * dt
        if is_key_down(KEY_RIGHT):
            self.rotation_y += 60.0 * dt
        if is_key_down(KEY_UP):
            self.camera.position.y = min(7.0, self.camera.position.y + 2.0 * dt)
        if is_key_down(KEY_DOWN):
            self.camera.position.y = max(0.5, self.camera.position.y - 2.0 * dt)

        # Toggle Animation Play/Pause
        if is_key_pressed(KEY_SPACE):
            self.anim_playing = not self.anim_playing

        # Cycle Palettes
        if is_key_pressed(KEY_P) or is_key_pressed(KEY_ONE):
            self.active_palette_idx = (self.active_palette_idx + 1) % len(self.palettes)

        # Toggle Wireframe Mode
        if is_key_pressed(KEY_W):
            self.show_wireframe = not self.show_wireframe

        # Zoom via Mouse Wheel
        wheel = get_mouse_wheel_move()
        if wheel != 0.0:
            cam_dist = math.sqrt(self.camera.position.x**2 + self.camera.position.z**2)
            cam_dist = max(2.2, min(14.0, cam_dist - wheel * 0.8))
            self.camera.position.z = cam_dist

    def draw(self):
        begin_drawing()
        clear_background(Color(16, 20, 28, 255))

        # 3D Scene Rendering
        begin_mode_3d(self.camera)
        draw_grid(10, 1.0)
        draw_glacier_bear_3d(
            Vector3(0.0, 0.0, 0.0),
            rotation_y=self.rotation_y,
            anim_timer=self.anim_timer,
            scale=1.0,
            palette=self.palettes[self.active_palette_idx],
            show_wireframe=self.show_wireframe
        )
        end_mode_3d()

        # HUD & Telemetry Overlay (Keeps x=450..980 clear for global bar)
        draw_text("3D MODEL INSPECTOR: Bionic Glacier Bear", 24, 20, 20, RAYWHITE)
        draw_text("[L-Drag / Left-Right] Rotate | [Space] Play/Pause | [P] Palette | [W] Wireframe", 24, 52, 14, LIGHTGRAY)
        wire_status = "ON" if self.show_wireframe else "OFF"
        draw_text(f"Palette: {self.palette_names[self.active_palette_idx]} | Wireframe: {wire_status}", 24, 76, 14, YELLOW)
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
