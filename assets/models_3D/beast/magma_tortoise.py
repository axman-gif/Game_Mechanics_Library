# -*- coding: utf-8 -*-
"""
Volcanic Magma Tortoise - 3D Procedural Primitive Model
=======================================================
Category         : beast
Target File      : assets/models_3D/beast/magma_tortoise.py
Primitives Used  : Stepped Prisms (octagonal multi-tiered basalt dome carapace 1.20x0.55x1.40,
                   flat armored ventral plastron plate 1.00x0.15x1.20, heavy horned cranial skull wedge 0.35x0.28x0.45),
                   Cylinders (4 massive stumpy armored column legs r=0.18 l=0.40,
                   2 conical dorsal magma chimney vents r1=0.14 r2=0.09 l=0.35, stubby tail stub r=0.10 l=0.30),
                   Spheres (central pulsating lava magma chamber sphere r=0.22 visible through carapace fissures,
                   glowing vent eruption nodes r=0.06, recessed magma eyes r=0.045)
Animation Loop   : Deliberate heavy plodding crawl gait with crawl cycle leg_angle=sin(anim_timer*1.8 + phase)*0.25 rad,
                   periodic thermal glow vent flare emission glow_int=0.7 + 0.3*sin(anim_timer*4.0),
                   pulsating molten magma chamber breathing cycle, defensive head swivel and retraction tuck.

Problem Solved:
  Eliminates external 3D mesh files (.obj/.fbx) and texture maps by procedurally
  synthesizing a heavily armored volcanic quadruped tortoise purely from Raylib geometric
  primitives and real-time trigonometric articulation.

How the Procedural Articulation Works:
  - Model anchored at ground level (y=0) beneath ventral plastron.
  - Plastron base suspended at y=0.25; carapace dome centered at y=0.55.
  - Four stumpy column legs plod in alternating diagonal pairs (FL+HR, FR+HL) with phase offsets.
  - Twin conical dorsal chimneys atop carapace at (+/-0.25, 0.85, -0.15) flare with thermal glow.
  - Incandescent molten magma chamber breathes beneath cracked basalt carapace fissures.
  - Heavy armored skull wedge bobs gently, swivels, and retracts defensively under the carapace rim.

C++ Raylib Equivalent:
  struct MagmaTortoisePalette {
      Color shell_basalt;
      Color plastron_rock;
      Color magma_core;
      Color vent_glow;
      Color horn_obsidian;
  };

  void DrawMagmaTortoise3D(Vector3 position, float rotation_y, float anim_timer, float scale, const MagmaTortoisePalette* palette, bool show_wireframe);
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
# const MagmaTortoisePalette DEFAULT_MAGMA_TORTOISE_PALETTE = { ... };

DEFAULT_MAGMA_TORTOISE_PALETTE = {
    "shell_basalt": Color(55, 52, 58, 255),    # Cracked volcanic basalt dark grey
    "plastron_rock": Color(85, 70, 60, 255),   # Scorched bedrock brown
    "magma_core": Color(255, 110, 20, 255),    # Incandescent molten orange
    "vent_glow": Color(255, 215, 60, 255),     # Flaring solar yellow
    "horn_obsidian": Color(25, 22, 28, 255),   # Cooled glossy black obsidian
}

TOXIC_SULFUR_PALETTE = {
    "shell_basalt": Color(45, 55, 48, 255),    # Sulfuric slate
    "plastron_rock": Color(70, 80, 65, 255),   # Corroded limestone
    "magma_core": Color(120, 240, 50, 255),    # Boiling acid green
    "vent_glow": Color(230, 255, 90, 255),     # Sulfur vapor yellow
    "horn_obsidian": Color(20, 30, 25, 255),   # Deep toxic mineral
}

# Mandatory named geometric constants from specification
CARAPACE_WIDTH = 1.20
CARAPACE_HEIGHT = 0.55
CARAPACE_LENGTH = 1.40
CHIMNEY_HEIGHT = 0.35
LEG_RADIUS = 0.18
LEG_LENGTH = 0.40
CORE_RADIUS = 0.22

# Additional structural proportions
PLASTRON_WIDTH = 1.00
PLASTRON_HEIGHT = 0.15
PLASTRON_LENGTH = 1.20
PLASTRON_ELEVATION = 0.25

SKULL_WIDTH = 0.35
SKULL_HEIGHT = 0.28
SKULL_LENGTH = 0.45

CHIMNEY_R_BOTTOM = 0.14
CHIMNEY_R_TOP = 0.09
TAIL_RADIUS = 0.10
TAIL_LENGTH = 0.30
VENT_NODE_RADIUS = 0.06
EYE_RADIUS = 0.045
HORN_RADIUS = 0.05
HORN_LENGTH = 0.20

CRAWL_CYCLE_SPEED = 1.8
VENT_PULSE_SPEED = 4.0
CORE_BREATHE_SPEED = 3.0


# ==============================================================================
# PART 4: CANONICAL 3D PROCEDURAL DRAWING FUNCTION
# ==============================================================================
def draw_magma_tortoise_3d(
    position: Vector3,
    rotation_y: float = 0.0,
    anim_timer: float = 0.0,
    scale: float = 1.0,
    palette: dict = None,
    show_wireframe: bool = False
) -> None:
    """
    Renders an articulated 3D Volcanic Magma Tortoise with plodding crawl stride,
    pulsating dorsal chimney flares, glowing core fissures, and defensive head tuck.
    Must be called between begin_mode_3d(camera) and end_mode_3d().

    Parameters:
      position       : World-space base root location (ground level beneath plastron).
      rotation_y     : Heading angle in DEGREES around Y axis (0 deg = facing +Z).
      anim_timer     : Elapsed seconds driving crawl stride, vent flares, and core pulse.
      scale          : Geometric scaling factor (1.0 = standard siege tortoise ~2.6m length).
      palette        : Optional dictionary overriding DEFAULT_MAGMA_TORTOISE_PALETTE colors.
      show_wireframe : If True, renders structural wireframe overlays.
    """
    pal = palette if palette is not None else DEFAULT_MAGMA_TORTOISE_PALETTE

    c_shell = pal["shell_basalt"]
    c_plastron = pal["plastron_rock"]
    c_magma = pal["magma_core"]
    c_vent = pal["vent_glow"]
    c_horn = pal["horn_obsidian"]

    # Thermal glow multiplier for dorsal chimney emissions
    glow_int = 0.7 + 0.3 * math.sin(anim_timer * VENT_PULSE_SPEED)
    g_r = max(0, min(255, int(c_vent.r * glow_int)))
    g_g = max(0, min(255, int(c_vent.g * glow_int)))
    g_b = max(0, min(255, int(c_vent.b * glow_int)))
    dynamic_vent_glow = Color(g_r, g_g, g_b, 255)

    # Core breathing intensity
    core_breath = 1.0 + 0.10 * math.sin(anim_timer * CORE_BREATHE_SPEED)

    # Heavy quadruped crawl micro-heave
    crawl_heave = 0.015 * math.cos(anim_timer * (CRAWL_CYCLE_SPEED * 2.0)) * scale

    # Tortoise body yaw sway
    sway_yaw = 1.6 * math.sin(anim_timer * CRAWL_CYCLE_SPEED)
    total_rot_deg = rotation_y + sway_yaw
    rad_y = total_rot_deg * (math.pi / 180.0)
    cos_r = math.cos(rad_y)
    sin_r = math.sin(rad_y)

    bx = position.x
    by = position.y + crawl_heave
    bz = position.z

    # Helper: transforms model-local coordinates (lx, ly, lz) to world space
    def transform_pt(lx: float, ly: float, lz: float) -> Vector3:
        wx = bx + (lx * cos_r + lz * sin_r) * scale
        wy = by + ly * scale
        wz = bz + (-lx * sin_r + lz * cos_r) * scale
        return Vector3(wx, wy, wz)

    # --------------------------------------------------------------------------
    # 1. VENTRAL PLASTRON PLATE (Flat Armored Underbelly)
    # --------------------------------------------------------------------------
    plastron_pos = transform_pt(0.0, PLASTRON_ELEVATION, 0.0)
    draw_cube(plastron_pos, PLASTRON_WIDTH * scale, PLASTRON_HEIGHT * scale, PLASTRON_LENGTH * scale, c_plastron)
    if show_wireframe:
        draw_cube_wires(plastron_pos, PLASTRON_WIDTH * scale, PLASTRON_HEIGHT * scale, PLASTRON_LENGTH * scale, c_horn)

    # Transverse abdominal armored scutes on ventral base
    scute_offsets_z = [0.38, 0.00, -0.38]
    for sz in scute_offsets_z:
        scute_pos = transform_pt(0.0, PLASTRON_ELEVATION - (PLASTRON_HEIGHT * 0.45), sz)
        draw_cube(scute_pos, (PLASTRON_WIDTH * 0.92) * scale, 0.04 * scale, 0.32 * scale, c_plastron)
        if show_wireframe:
            draw_cube_wires(scute_pos, (PLASTRON_WIDTH * 0.92) * scale, 0.04 * scale, 0.32 * scale, c_horn)

    # --------------------------------------------------------------------------
    # 2. CENTRAL LAVA MAGMA CHAMBER SPHERE & FISSURE GLOW
    # --------------------------------------------------------------------------
    # Molten core sphere suspended at (0.0, 0.55, 0.0)
    core_pos = transform_pt(0.0, 0.55, 0.0)
    draw_sphere(core_pos, (CORE_RADIUS * core_breath) * scale, c_magma)
    # Incandescent inner thermal kernel
    draw_sphere(core_pos, (CORE_RADIUS * 0.65 * core_breath) * scale, dynamic_vent_glow)
    if show_wireframe:
        draw_sphere_wires(core_pos, (CORE_RADIUS * core_breath) * scale, 8, 8, dynamic_vent_glow)

    # Molten lava fissure channels running beneath cracked basalt plates
    fissure_pos_mid = transform_pt(0.0, 0.56, 0.0)
    draw_cube(fissure_pos_mid, 0.16 * scale, 0.14 * scale, 1.25 * scale, c_magma)
    fissure_pos_lat1 = transform_pt(0.0, 0.56, 0.22)
    draw_cube(fissure_pos_lat1, 0.85 * scale, 0.12 * scale, 0.12 * scale, c_magma)
    fissure_pos_lat2 = transform_pt(0.0, 0.56, -0.18)
    draw_cube(fissure_pos_lat2, 0.88 * scale, 0.12 * scale, 0.12 * scale, c_magma)

    # --------------------------------------------------------------------------
    # 3. STEPPED OCTAGONAL BASALT DOME CARAPACE (Multi-Tiered Prisms)
    # --------------------------------------------------------------------------
    # Tier 1: Basalt Skirt / Carapace Rim (centered at y=0.46)
    skirt_pos = transform_pt(0.0, 0.46, 0.0)
    draw_cube(skirt_pos, 1.18 * scale, 0.14 * scale, 1.36 * scale, c_shell)
    if show_wireframe:
        draw_cube_wires(skirt_pos, 1.18 * scale, 0.14 * scale, 1.36 * scale, c_horn)

    # Flared lateral marginal scutes
    left_skirt = transform_pt(-0.56, 0.44, 0.0)
    right_skirt = transform_pt(0.56, 0.44, 0.0)
    draw_cube(left_skirt, 0.14 * scale, 0.10 * scale, 1.18 * scale, c_shell)
    draw_cube(right_skirt, 0.14 * scale, 0.10 * scale, 1.18 * scale, c_shell)

    # Octagonal corner chamfer bevels
    corner_coords = [
        (-0.48, 0.45,  0.52),
        ( 0.48, 0.45,  0.52),
        (-0.48, 0.45, -0.52),
        ( 0.48, 0.45, -0.52)
    ]
    for cx, cy, cz in corner_coords:
        corner_pos = transform_pt(cx, cy, cz)
        draw_cube(corner_pos, 0.22 * scale, 0.11 * scale, 0.22 * scale, c_shell)
        if show_wireframe:
            draw_cube_wires(corner_pos, 0.22 * scale, 0.11 * scale, 0.22 * scale, c_horn)

    # Tier 2: Mid Costal Basalt Armor Plates (centered at y=0.62)
    # Anterior dorsal plate
    front_plate_pos = transform_pt(0.0, 0.62, 0.38)
    draw_cube(front_plate_pos, 0.96 * scale, 0.18 * scale, 0.38 * scale, c_shell)
    if show_wireframe:
        draw_cube_wires(front_plate_pos, 0.96 * scale, 0.18 * scale, 0.38 * scale, c_horn)

    # Split central dorsal plates (separated to expose lava fissure channel)
    c_left_plate = transform_pt(-0.28, 0.62, 0.0)
    c_right_plate = transform_pt(0.28, 0.62, 0.0)
    draw_cube(c_left_plate, 0.42 * scale, 0.18 * scale, 0.42 * scale, c_shell)
    draw_cube(c_right_plate, 0.42 * scale, 0.18 * scale, 0.42 * scale, c_shell)
    if show_wireframe:
        draw_cube_wires(c_left_plate, 0.42 * scale, 0.18 * scale, 0.42 * scale, c_horn)
        draw_cube_wires(c_right_plate, 0.42 * scale, 0.18 * scale, 0.42 * scale, c_horn)

    # Posterior dorsal plate
    rear_plate_pos = transform_pt(0.0, 0.62, -0.38)
    draw_cube(rear_plate_pos, 0.94 * scale, 0.18 * scale, 0.38 * scale, c_shell)
    if show_wireframe:
        draw_cube_wires(rear_plate_pos, 0.94 * scale, 0.18 * scale, 0.38 * scale, c_horn)

    # Lateral costal scutes
    lat_left = transform_pt(-0.46, 0.58, 0.0)
    lat_right = transform_pt(0.46, 0.58, 0.0)
    draw_cube(lat_left, 0.22 * scale, 0.16 * scale, 0.90 * scale, c_shell)
    draw_cube(lat_right, 0.22 * scale, 0.16 * scale, 0.90 * scale, c_shell)

    # Tier 3: Upper Basalt Caldera Dome & Dorsal Crown (centered at y=0.74)
    crown_pos = transform_pt(0.0, 0.74, 0.10)
    draw_cube(crown_pos, 0.68 * scale, 0.16 * scale, 0.62 * scale, c_shell)
    if show_wireframe:
        draw_cube_wires(crown_pos, 0.68 * scale, 0.16 * scale, 0.62 * scale, c_horn)

    # Volcanic caldera collars supporting chimney mounts
    caldera_l = transform_pt(-0.25, 0.80, -0.15)
    caldera_r = transform_pt(0.25, 0.80, -0.15)
    draw_cube(caldera_l, 0.36 * scale, 0.12 * scale, 0.36 * scale, c_shell)
    draw_cube(caldera_r, 0.36 * scale, 0.12 * scale, 0.36 * scale, c_shell)

    # --------------------------------------------------------------------------
    # 4. CONICAL DORSAL MAGMA CHIMNEY VENTS & ERUPTION NODES
    # --------------------------------------------------------------------------
    # Twin dorsal chimneys mounted atop shell at x=+/-0.25, z=-0.15, y=0.85
    chimney_mounts = [
        (-0.25, -0.15),
        ( 0.25, -0.15)
    ]

    for ch_x, ch_z in chimney_mounts:
        ch_base = transform_pt(ch_x, 0.85, ch_z)
        ch_top = transform_pt(ch_x, 0.85 + CHIMNEY_HEIGHT, ch_z)
        r_bot = CHIMNEY_R_BOTTOM * scale
        r_top = CHIMNEY_R_TOP * scale

        # Conical basalt chimney column
        draw_cylinder_ex(ch_base, ch_top, r_bot, r_top, 8, c_shell)
        if show_wireframe:
            draw_cylinder_wires_ex(ch_base, ch_top, r_bot, r_top, 8, c_horn)

        # Flaring volcanic vent eruption node at chimney mouth
        draw_sphere(ch_top, VENT_NODE_RADIUS * scale, dynamic_vent_glow)
        # Inner molten core droplet
        draw_sphere(ch_top, (VENT_NODE_RADIUS * 0.60) * scale, c_magma)
        if show_wireframe:
            draw_sphere_wires(ch_top, VENT_NODE_RADIUS * scale, 6, 6, c_vent)

        # Drifting volcanic ember droplet particles bobbing above vent
        for e in range(2):
            ember_phase = anim_timer * 4.5 + e * 3.14
            ember_elev = (ember_phase % 1.0) * 0.22
            ember_drift_x = math.sin(ember_phase * 2.0) * 0.03
            ember_drift_z = math.cos(ember_phase * 1.8) * 0.03
            ember_pt = transform_pt(ch_x + ember_drift_x, 0.85 + CHIMNEY_HEIGHT + 0.05 + ember_elev, ch_z + ember_drift_z)
            draw_sphere(ember_pt, 0.02 * scale, c_magma)

    # --------------------------------------------------------------------------
    # 5. FOUR MASSIVE STUMPY COLUMN LEGS & ELEPHANTINE PADS
    # --------------------------------------------------------------------------
    # Leg layout: corners x=+/-0.52, z=+/-0.50
    leg_coords = [
        # (name, lx, lz, phase)
        ("FL", -0.52,  0.50, 0.0),
        ("FR",  0.52,  0.50, math.pi),
        ("HL", -0.52, -0.50, math.pi),
        ("HR",  0.52, -0.50, 0.0),
    ]

    for name, lx, lz, phase in leg_coords:
        # Deliberate heavy crawl cycle
        leg_angle = math.sin(anim_timer * CRAWL_CYCLE_SPEED + phase) * 0.25
        hip_pt = transform_pt(lx, 0.35, lz)

        # Plodding ground stride
        foot_lz = lz + math.sin(leg_angle) * LEG_LENGTH
        foot_lift = max(0.0, math.cos(anim_timer * CRAWL_CYCLE_SPEED + phase)) * 0.04
        foot_ly = foot_lift
        foot_pt = transform_pt(lx, foot_ly + 0.06, foot_lz)

        # Stumpy column leg cylinder
        draw_cylinder_ex(hip_pt, foot_pt, LEG_RADIUS * scale, (LEG_RADIUS * 1.15) * scale, 8, c_shell)
        if show_wireframe:
            draw_cylinder_wires_ex(hip_pt, foot_pt, LEG_RADIUS * scale, (LEG_RADIUS * 1.15) * scale, 8, c_horn)

        # Armored knee guard ring
        knee_pt = transform_pt(lx, 0.20 + foot_lift * 0.5, (lz + foot_lz) * 0.5)
        knee_top = transform_pt(lx, 0.25 + foot_lift * 0.5, (lz + foot_lz) * 0.5)
        draw_cylinder_ex(knee_pt, knee_top, (LEG_RADIUS * 1.25) * scale, (LEG_RADIUS * 1.25) * scale, 8, c_plastron)

        # Broad elephantine tortoise foot pad
        foot_base_pt = transform_pt(lx, foot_ly, foot_lz)
        draw_cylinder_ex(foot_pt, foot_base_pt, (LEG_RADIUS * 1.25) * scale, (LEG_RADIUS * 1.35) * scale, 8, c_plastron)

        # Three blunt basalt digging claw talons per foot
        for c in range(3):
            c_angle = (c - 1) * 0.35
            talon_base = transform_pt(lx + math.sin(c_angle) * (LEG_RADIUS * 1.10), foot_ly + 0.02, foot_lz + math.cos(c_angle) * (LEG_RADIUS * 1.10))
            talon_tip = transform_pt(lx + math.sin(c_angle) * (LEG_RADIUS * 1.45), foot_ly, foot_lz + math.cos(c_angle) * (LEG_RADIUS * 1.45))
            draw_cylinder_ex(talon_base, talon_tip, 0.045 * scale, 0.015 * scale, 6, c_horn)

    # --------------------------------------------------------------------------
    # 6. HEAVY HORNED CRANIAL SKULL WEDGE & RECESS MAGMA EYES
    # --------------------------------------------------------------------------
    # Neck socket extends forward from (0, 0.38, 0.70)
    neck_socket_pt = transform_pt(0.0, 0.38, 0.65)

    # Defensive head swivel and periodic retraction under carapace rim
    retract_dist = max(0.0, math.sin(anim_timer * 1.2)) * 0.18
    head_swivel = math.sin(anim_timer * 0.9) * 0.14
    head_lz = 0.70 + 0.24 - retract_dist
    head_lx = math.sin(head_swivel) * 0.12
    head_ly = 0.38 + math.sin(anim_timer * CRAWL_CYCLE_SPEED) * 0.02

    head_base_pt = transform_pt(head_lx, head_ly, head_lz - 0.15)
    # Heavy muscular neck cylinder
    draw_cylinder_ex(neck_socket_pt, head_base_pt, 0.15 * scale, 0.13 * scale, 6, c_plastron)

    # Cranial skull wedge block (0.35 x 0.28 x 0.45)
    skull_pos = transform_pt(head_lx, head_ly, head_lz)
    draw_cube(skull_pos, SKULL_WIDTH * scale, SKULL_HEIGHT * scale, SKULL_LENGTH * scale, c_shell)
    if show_wireframe:
        draw_cube_wires(skull_pos, SKULL_WIDTH * scale, SKULL_HEIGHT * scale, SKULL_LENGTH * scale, c_horn)

    # Heavy armored brow plate ridge
    brow_pos = transform_pt(head_lx, head_ly + 0.12, head_lz + 0.05)
    draw_cube(brow_pos, (SKULL_WIDTH * 1.08) * scale, 0.08 * scale, 0.30 * scale, c_shell)

    # Beveled snout wedge
    snout_pos = transform_pt(head_lx, head_ly - 0.05, head_lz + 0.22)
    draw_cube(snout_pos, (SKULL_WIDTH * 0.80) * scale, 0.16 * scale, 0.22 * scale, c_plastron)

    # Obsidian brow horns (curving forward/upward)
    horn_specs = [
        (-0.14, 0.10, 0.05, -0.20, 0.26, 0.18),
        ( 0.14, 0.10, 0.05,  0.20, 0.26, 0.18),
        # Lateral temporal horns sweeping rearward
        (-0.16, 0.08, -0.10, -0.25, 0.12, -0.24),
        ( 0.16, 0.08, -0.10,  0.25, 0.12, -0.24)
    ]
    for hx1, hy1, hz1, hx2, hy2, hz2 in horn_specs:
        h_base = transform_pt(head_lx + hx1, head_ly + hy1, head_lz + hz1)
        h_tip = transform_pt(head_lx + hx2, head_ly + hy2, head_lz + hz2)
        draw_cylinder_ex(h_base, h_tip, HORN_RADIUS * scale, 0.015 * scale, 6, c_horn)
        if show_wireframe:
            draw_cylinder_wires_ex(h_base, h_tip, HORN_RADIUS * scale, 0.015 * scale, 6, c_shell)

    # Recessed magma eyes with glowing core
    eye_lx = 0.16
    eye_ly = head_ly + 0.04
    eye_lz = head_lz + 0.10

    eye_l_pos = transform_pt(head_lx - eye_lx, eye_ly, eye_lz)
    eye_r_pos = transform_pt(head_lx + eye_lx, eye_ly, eye_lz)
    draw_sphere(eye_l_pos, EYE_RADIUS * scale, c_magma)
    draw_sphere(eye_r_pos, EYE_RADIUS * scale, c_magma)
    draw_sphere(eye_l_pos, (EYE_RADIUS * 0.55) * scale, dynamic_vent_glow)
    draw_sphere(eye_r_pos, (EYE_RADIUS * 0.55) * scale, dynamic_vent_glow)

    # --------------------------------------------------------------------------
    # 7. STUBBY TAIL STUB & REAR BASALT SPUR
    # --------------------------------------------------------------------------
    tail_yaw = math.sin(anim_timer * CRAWL_CYCLE_SPEED) * 0.18
    tail_base = transform_pt(0.0, 0.32, -0.65)
    tail_tip = transform_pt(math.sin(tail_yaw) * 0.08, 0.24, -0.65 - TAIL_LENGTH)
    draw_cylinder_ex(tail_base, tail_tip, TAIL_RADIUS * scale, (TAIL_RADIUS * 0.55) * scale, 6, c_shell)
    if show_wireframe:
        draw_cylinder_wires_ex(tail_base, tail_tip, TAIL_RADIUS * scale, (TAIL_RADIUS * 0.55) * scale, 6, c_horn)

    # Obsidian tail club spur
    draw_sphere(tail_tip, (TAIL_RADIUS * 0.65) * scale, c_horn)


# ==============================================================================
# PART 5: C++ MAPPING & MEMORY LAYOUT (Zero "Pythonic Magic")
# ==============================================================================
# In C++ (raylib.h), this procedural model executes with zero heap allocations:
#
# struct MagmaTortoisePalette {
#     Color shell_basalt;
#     Color plastron_rock;
#     Color magma_core;
#     Color vent_glow;
#     Color horn_obsidian;
# };
#
# static const MagmaTortoisePalette DEFAULT_MAGMA_TORTOISE_PALETTE = {
#     (Color){55, 52, 58, 255},
#     (Color){85, 70, 60, 255},
#     (Color){255, 110, 20, 255},
#     (Color){255, 215, 60, 255},
#     (Color){25, 22, 28, 255}
# };
#
# void DrawMagmaTortoise3D(Vector3 position, float rotation_y, float anim_timer, float scale, const MagmaTortoisePalette* palette, bool show_wireframe);
#
# Memory Layout & Performance Notes:
# - Zero heap allocations: all coordinates and kinematic joints compute on CPU stack frames.
# - Direct GPU primitive streaming: calls map 1-to-1 to DrawCube, DrawSphere, DrawCylinderEx.
# - C++ Transferability: Replace math.sin/cos with sinf/cosf from <math.h>.


# ==============================================================================
# PART 6: STANDALONE 3D ORBIT VIEWER (ModelViewerApp)
# ==============================================================================
class ModelViewerApp:
    """
    Interactive 3D previewer allowing inspection, rotation, zooming,
    wireframe toggle, palette swapping, and automated 3-frame smoke testing.
    """
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        init_window(self.screen_width, self.screen_height, "3D Model Inspector - Volcanic Magma Tortoise")
        set_target_fps(60)

        # 3D Orbit Camera Setup
        self.camera = Camera3D(
            Vector3(0.0, 3.0, 5.2),   # Position
            Vector3(0.0, 0.55, 0.0),  # Target centered on tortoise carapace
            Vector3(0.0, 1.0, 0.0),   # Up vector
            45.0,                     # FOV
            CAMERA_PERSPECTIVE
        )

        self.anim_timer = 0.0
        self.anim_playing = True
        self.rotation_y = 45.0
        self.show_wireframe = False
        self.active_palette_idx = 0
        self.palettes = [DEFAULT_MAGMA_TORTOISE_PALETTE, TOXIC_SULFUR_PALETTE]
        self.palette_names = ["Cracked Basalt & Magma", "Toxic Sulfur Caldera"]

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

        # Toggle Wireframe mode
        if is_key_pressed(KEY_W) or is_key_pressed(KEY_TAB):
            self.show_wireframe = not self.show_wireframe

        # Cycle Palettes
        if is_key_pressed(KEY_P) or is_key_pressed(KEY_ONE):
            self.active_palette_idx = (self.active_palette_idx + 1) % len(self.palettes)

        # Zoom via Mouse Wheel
        wheel = get_mouse_wheel_move()
        if wheel != 0.0:
            cam_dist = math.sqrt(self.camera.position.x**2 + self.camera.position.z**2)
            cam_dist = max(2.0, min(14.0, cam_dist - wheel * 0.8))
            angle = math.atan2(self.camera.position.z, self.camera.position.x)
            self.camera.position.x = math.cos(angle) * cam_dist
            self.camera.position.z = math.sin(angle) * cam_dist

    def draw(self):
        begin_drawing()
        clear_background(Color(20, 22, 26, 255))

        # 3D Scene Rendering
        begin_mode_3d(self.camera)
        draw_grid(12, 1.0)
        draw_magma_tortoise_3d(
            Vector3(0.0, 0.0, 0.0),
            rotation_y=self.rotation_y,
            anim_timer=self.anim_timer,
            scale=1.0,
            palette=self.palettes[self.active_palette_idx],
            show_wireframe=self.show_wireframe
        )
        end_mode_3d()

        # HUD & Telemetry Overlay (Keeps x=450..980 clear for global bar)
        draw_text("3D MODEL INSPECTOR: Volcanic Magma Tortoise", 24, 20, 20, RAYWHITE)
        draw_text("[L-Drag / Left-Right] Orbit | [Space] Play/Pause | [P] Palette | [W/Tab] Wireframe", 24, 52, 14, LIGHTGRAY)
        draw_text(f"Palette: {self.palette_names[self.active_palette_idx]}", 24, 76, 14, YELLOW)
        draw_text(f"Anim Timer: {self.anim_timer:.2f}s | Rotation: {self.rotation_y:.1f} deg | Wireframe: {self.show_wireframe}", 24, 98, 14, SKYBLUE)

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
