# -*- coding: utf-8 -*-
"""
Spore-Spitting Quadruped Bull - 3D Procedural Primitive Model
=============================================================
Category         : beast
Target File      : assets/models_3D/beast/spore_bull.py
Primitives Used  : Prisms/Cubes (hunchbacked muscular neck hump, armored frontal skull plate, rear hip block),
                   Cylinders (twisted spiral fungal horns, heavy pillar legs, dorsal spore chimney vents),
                   Spheres (pulsing flank spore pustule sacs, glowing infected eyes, spore cloud motes)
Animation Loop   : 4-leg stampede gallop stride, forward charging torso pitch, head bob/sway,
                   expanding dorsal spore chimneys, pulsing fungal pustule sacs, floating toxic spores

Problem Solved:
  Eliminates bulky 3D mesh files (.obj/.fbx) and external texture dependencies by
  synthesizing a heavily infected fungal quadruped brute purely from Raylib geometric
  primitives and trigonometric articulation in real time.

How the Procedural Articulation Works:
  - The model hierarchy is anchored relative to a base 'position' (Vector3) at ground level (y=0).
  - Main torso chest center sits at y=0.85, with a massive muscular neck hump elevated to y=1.25.
  - Charging stampede gallop: 4 pillar legs oscillate with high-impact sinusoidal stride:
    leg_angle = math.sin(anim_timer * 5.5 + phase) * 0.45 rad.
  - Forward charge pitch: torso tilts forward dynamically:
    pitch_hump = 0.15 * math.sin(anim_timer * 5.5).
  - Periodic fungal expansion: dorsal chimneys and flank sacs expand via:
    sac_scale = 1.0 + 0.22 * math.sin(anim_timer * 4.0).
  - Lowered armored skull plate at (0, 0.70, 0.75) bobs and sways with charging rhythm.
  - Dual twisted horns project forward at (+/-35 deg yaw, +15 deg pitch) with spiral segmentation.
  - Swirling toxic spore motes drift continuously upward from chimney vents.

C++ Raylib Equivalent:
  struct SporeBullPalette {
      Color flesh;
      Color fungal_plates;
      Color spore_sac;
      Color horns;
      Color spores;
  };

  void DrawSporeBull3D(Vector3 position, float rotation_y, float anim_timer, float scale, const SporeBullPalette* palette, bool show_wireframe);
  Mapped directly to DrawCube, DrawCubeWires, DrawSphere, DrawSphereWires, and DrawCylinderEx from raylib.h.
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
# const SporeBullPalette DEFAULT_SPORE_BULL_PALETTE = { ... };

DEFAULT_SPORE_BULL_PALETTE = {
    "flesh": Color(70, 95, 60, 255),           # Rotten moss green
    "fungal_plates": Color(215, 210, 185, 255),# Calcified fungal ivory
    "spore_sac": Color(160, 240, 40, 255),     # Pulsing neon chartreuse
    "horns": Color(60, 48, 38, 255),           # Lichen encrusted bark
    "spores": Color(230, 220, 60, 255),        # Toxic spore cloud yellow
}

CRIMSON_MYCELIUM_PALETTE = {
    "flesh": Color(95, 40, 45, 255),           # Decaying crimson sinew
    "fungal_plates": Color(185, 170, 160, 255),# Ash bone carapace
    "spore_sac": Color(255, 60, 40, 255),      # Bloody pustule red
    "horns": Color(45, 30, 35, 255),           # Charred fungal root
    "spores": Color(255, 140, 50, 255),        # Cauterizing orange spores
}

# Mandatory named geometric constants
HUMP_HEIGHT = 0.90
SKULL_WIDTH = 0.55
HORN_LENGTH = 0.85
LEG_RADIUS = 0.15
LEG_LENGTH = 0.65
SAC_RADIUS = 0.16

# Additional structural proportions
HUMP_WIDTH = 0.85
HUMP_LENGTH = 1.00
SKULL_HEIGHT = 0.45
SKULL_LENGTH = 0.60
HIP_WIDTH = 0.75
HIP_HEIGHT = 0.65
HIP_LENGTH = 0.80
CHEST_WIDTH = 0.80
CHEST_HEIGHT = 0.75
CHEST_LENGTH = 0.85

CHIMNEY_RADIUS = 0.08
CHIMNEY_LENGTH = 0.35
EYE_RADIUS = 0.05
HOOF_RADIUS = 0.18
HOOF_HEIGHT = 0.14
LEG_X_OFFSET = 0.38

STAMPEDE_SPEED = 5.5
PULSE_SPEED = 4.0


# ==============================================================================
# PART 4: CANONICAL 3D PROCEDURAL DRAWING FUNCTION
# ==============================================================================
def draw_spore_bull_3d(
    position: Vector3,
    rotation_y: float = 0.0,
    anim_timer: float = 0.0,
    scale: float = 1.0,
    palette: dict = None,
    show_wireframe: bool = False
) -> None:
    """
    Renders an articulated 3D Spore-Spitting Quadruped Bull with stampede gallop gait,
    charging torso pitch, head sway, expanding chimneys/sacs, and swirling spore cloud.
    Must be called between begin_mode_3d(camera) and end_mode_3d().

    Parameters:
      position       : World-space base root location (ground level beneath beast).
      rotation_y     : Heading angle in DEGREES around Y axis (0 deg = facing +Z).
      anim_timer     : Elapsed seconds driving stampede locomotion and spore pulsing.
      scale          : Geometric scaling factor (1.0 = standard bull ~3.0m length).
      palette        : Optional dictionary overriding DEFAULT_SPORE_BULL_PALETTE colors.
      show_wireframe : If True, renders explicit structural wireframe contours.
    """
    pal = palette if palette is not None else DEFAULT_SPORE_BULL_PALETTE

    c_flesh = pal["flesh"]
    c_plates = pal["fungal_plates"]
    c_sac = pal["spore_sac"]
    c_horns = pal["horns"]
    c_spores = pal["spores"]

    # Heading angle in radians
    rad_y = rotation_y * (math.pi / 180.0)
    cos_r = math.cos(rad_y)
    sin_r = math.sin(rad_y)

    # Aggressive gallop body kinematics
    pitch_hump = 0.15 * math.sin(anim_timer * STAMPEDE_SPEED)
    cos_p = math.cos(pitch_hump)
    sin_p = math.sin(pitch_hump)

    torso_bounce = 0.06 * abs(math.sin(anim_timer * STAMPEDE_SPEED)) * scale
    sac_scale = 1.0 + 0.22 * math.sin(anim_timer * PULSE_SPEED)

    bx = position.x
    by = position.y + torso_bounce
    bz = position.z

    # Torso pivot point in local coordinates (around chest center y=0.85, z=0.10)
    piv_y = 0.85
    piv_z = 0.10

    # Helper: transforms local unpitched point to world space
    def transform_pt(lx: float, ly: float, lz: float) -> Vector3:
        wx = bx + (lx * cos_r + lz * sin_r) * scale
        wy = by + ly * scale
        wz = bz + (-lx * sin_r + lz * cos_r) * scale
        return Vector3(wx, wy, wz)

    # Helper: transforms torso-anchored local point (with charging pitch) to world space
    def transform_torso_pt(lx: float, ly: float, lz: float) -> Vector3:
        dy = ly - piv_y
        dz = lz - piv_z
        pitched_y = piv_y + (dy * cos_p - dz * sin_p)
        pitched_z = piv_z + (dy * sin_p + dz * cos_p)
        return transform_pt(lx, pitched_y, pitched_z)

    # --------------------------------------------------------------------------
    # 1. MAIN TORSO & HUNCHBACK MUSCULAR NECK HUMP
    # --------------------------------------------------------------------------
    # Muscular chest block centered at (0, 0.85, 0.15)
    chest_pos = transform_torso_pt(0.0, 0.85, 0.15)
    draw_cube(chest_pos, CHEST_WIDTH * scale, CHEST_HEIGHT * scale, CHEST_LENGTH * scale, c_flesh)
    if show_wireframe:
        draw_cube_wires(chest_pos, CHEST_WIDTH * scale, CHEST_HEIGHT * scale, CHEST_LENGTH * scale, c_plates)

    # Massive hunchbacked muscular neck hump (0.85 x 0.90 x 1.00) elevated to y=1.25
    hump_pos = transform_torso_pt(0.0, 1.25, 0.25)
    draw_cube(hump_pos, HUMP_WIDTH * scale, HUMP_HEIGHT * scale, HUMP_LENGTH * scale, c_flesh)
    if show_wireframe:
        draw_cube_wires(hump_pos, HUMP_WIDTH * scale, HUMP_HEIGHT * scale, HUMP_LENGTH * scale, c_plates)

    # Calcified fungal carapace armor plates across dorsal hump
    plate_elevations = [
        (0.0, 1.62, 0.45, 0.75, 0.14, 0.32),
        (0.0, 1.66, 0.18, 0.82, 0.16, 0.36),
        (0.0, 1.58, -0.10, 0.78, 0.14, 0.30),
    ]
    for px, py, pz, pw, ph, pl in plate_elevations:
        plate_pos = transform_torso_pt(px, py, pz)
        draw_cube(plate_pos, pw * scale, ph * scale, pl * scale, c_plates)
        if show_wireframe:
            draw_cube_wires(plate_pos, pw * scale, ph * scale, pl * scale, c_horns)

    # Rear hip block (0.75 x 0.65 x 0.80) anchored at z=-0.45, y=0.80
    hip_pos = transform_torso_pt(0.0, 0.80, -0.45)
    draw_cube(hip_pos, HIP_WIDTH * scale, HIP_HEIGHT * scale, HIP_LENGTH * scale, c_flesh)
    if show_wireframe:
        draw_cube_wires(hip_pos, HIP_WIDTH * scale, HIP_HEIGHT * scale, HIP_LENGTH * scale, c_plates)

    # Sacral crest armor plate on hip
    sacral_pos = transform_torso_pt(0.0, 1.12, -0.42)
    draw_cube(sacral_pos, 0.65 * scale, 0.14 * scale, 0.50 * scale, c_plates)

    # Short muscular fungal tail with club
    tail_base = transform_torso_pt(0.0, 0.85, -0.85)
    tail_tip = transform_torso_pt(0.0, 0.45, -1.25)
    draw_cylinder_ex(tail_base, tail_tip, 0.10 * scale, 0.05 * scale, 6, c_flesh)
    draw_sphere(tail_tip, 0.12 * sac_scale * scale, c_plates)

    # --------------------------------------------------------------------------
    # 2. DORSAL SPORE CHIMNEY VENTS (Cylinders r=0.08, l=0.35)
    # --------------------------------------------------------------------------
    # Chimney specifications: (base_x, base_y, base_z, tip_x, tip_y, tip_z, r_mult)
    chimney_specs = [
        (-0.20, 1.60, 0.38, -0.26, 1.60 + CHIMNEY_LENGTH * sac_scale, 0.44, 1.0),
        ( 0.20, 1.60, 0.38,  0.26, 1.60 + CHIMNEY_LENGTH * sac_scale, 0.44, 1.0),
        ( 0.00, 1.68, 0.12,  0.00, 1.68 + CHIMNEY_LENGTH * 1.15 * sac_scale, 0.08, 1.1),
        (-0.16, 1.58, -0.16, -0.22, 1.58 + CHIMNEY_LENGTH * 0.90 * sac_scale, -0.22, 0.85),
        ( 0.16, 1.58, -0.16,  0.22, 1.58 + CHIMNEY_LENGTH * 0.90 * sac_scale, -0.22, 0.85),
    ]

    for bx_c, by_c, bz_c, tx_c, ty_c, tz_c, r_mult in chimney_specs:
        c_base = transform_torso_pt(bx_c, by_c, bz_c)
        c_tip = transform_torso_pt(tx_c, ty_c, tz_c)
        r_base = (CHIMNEY_RADIUS * 1.25 * r_mult) * scale
        r_tip = (CHIMNEY_RADIUS * 0.85 * r_mult) * scale
        draw_cylinder_ex(c_base, c_tip, r_base, r_tip, 6, c_plates)
        # Inner vent orifice glow
        draw_sphere(c_tip, (CHIMNEY_RADIUS * 0.70 * r_mult) * sac_scale * scale, c_sac)
        if show_wireframe:
            draw_sphere_wires(c_tip, (CHIMNEY_RADIUS * 0.85 * r_mult) * scale, 6, 6, c_horns)

    # --------------------------------------------------------------------------
    # 3. PULSING FUNGAL PUSTULE SPORE SACS ON FLANKS (Spheres r=0.16)
    # --------------------------------------------------------------------------
    flank_sac_specs = [
        # (side_mult, lx, ly, lz, base_radius, phase_offset)
        ( 1.0,  0.44, 1.15,  0.30, SAC_RADIUS, 0.0),
        (-1.0, -0.44, 1.15,  0.30, SAC_RADIUS, 0.0),
        ( 1.0,  0.46, 0.95, -0.05, SAC_RADIUS * 0.90, 1.2),
        (-1.0, -0.46, 0.95, -0.05, SAC_RADIUS * 0.90, 1.2),
        ( 1.0,  0.42, 1.22, -0.12, SAC_RADIUS * 1.10, 2.1),
        (-1.0, -0.42, 1.22, -0.12, SAC_RADIUS * 1.10, 2.1),
        ( 1.0,  0.40, 0.85,  0.15, SAC_RADIUS * 0.80, 0.7),
        (-1.0, -0.40, 0.85,  0.15, SAC_RADIUS * 0.80, 0.7),
        ( 1.0,  0.41, 0.82, -0.45, SAC_RADIUS * 0.85, 2.8),
        (-1.0, -0.41, 0.82, -0.45, SAC_RADIUS * 0.85, 2.8),
    ]

    for side, lx, ly, lz, base_r, p_off in flank_sac_specs:
        cur_pulse = 1.0 + 0.22 * math.sin(anim_timer * PULSE_SPEED + p_off)
        sac_pt = transform_torso_pt(lx, ly, lz)
        draw_sphere(sac_pt, base_r * cur_pulse * scale, c_sac)
        # Lichen base collar anchoring the sac to hide
        collar_pt = transform_torso_pt(lx * 0.92, ly, lz)
        draw_sphere(collar_pt, (base_r * 0.80) * scale, c_flesh)
        if show_wireframe:
            draw_sphere_wires(sac_pt, base_r * cur_pulse * scale, 6, 6, c_plates)

    # --------------------------------------------------------------------------
    # 4. LOWERED HEAD & TWISTED SPIRAL FUNGAL HORNS
    # --------------------------------------------------------------------------
    # Charging head rhythm: bobbing and horizontal sway
    head_bob_y = 0.05 * math.sin(anim_timer * STAMPEDE_SPEED + 0.5)
    head_sway_x = 0.04 * math.sin(anim_timer * (STAMPEDE_SPEED * 0.5))

    # Base skull location anchored forward at (0, 0.70, 0.75) with head bob/sway
    head_lx = head_sway_x
    head_ly = 0.70 + head_bob_y
    head_lz = 0.75

    # Skull center transformed via torso pitch
    skull_pt = transform_torso_pt(head_lx, head_ly, head_lz)

    # Frontal low-slung skull plate block (0.55 x 0.45 x 0.60)
    draw_cube(skull_pt, SKULL_WIDTH * scale, SKULL_HEIGHT * scale, SKULL_LENGTH * scale, c_flesh)
    if show_wireframe:
        draw_cube_wires(skull_pt, SKULL_WIDTH * scale, SKULL_HEIGHT * scale, SKULL_LENGTH * scale, c_plates)

    # Heavy frontal armor battering plate across the brow/forehead
    forehead_pt = transform_torso_pt(head_lx, head_ly + 0.16, head_lz + 0.12)
    draw_cube(forehead_pt, (SKULL_WIDTH * 1.08) * scale, 0.20 * scale, (SKULL_LENGTH * 0.75) * scale, c_plates)
    if show_wireframe:
        draw_cube_wires(forehead_pt, (SKULL_WIDTH * 1.08) * scale, 0.20 * scale, (SKULL_LENGTH * 0.75) * scale, c_horns)

    # Low-slung snout / jaws
    snout_pt = transform_torso_pt(head_lx, head_ly - 0.10, head_lz + 0.32)
    draw_cube(snout_pt, 0.42 * scale, 0.25 * scale, 0.35 * scale, c_flesh)

    # Spore-spitting mouth orifice
    mouth_pt = transform_torso_pt(head_lx, head_ly - 0.14, head_lz + 0.48)
    draw_cube(mouth_pt, 0.26 * scale, 0.10 * scale, 0.12 * scale, c_horns)
    # Toxic spore drool / gland in mouth
    draw_sphere(mouth_pt, 0.07 * sac_scale * scale, c_sac)

    # Glowing infected sensor eyes (r = 0.05)
    eye_x_off = 0.25
    eye_l_pt = transform_torso_pt(head_lx - eye_x_off, head_ly + 0.08, head_lz + 0.18)
    eye_r_pt = transform_torso_pt(head_lx + eye_x_off, head_ly + 0.08, head_lz + 0.18)
    draw_sphere(eye_l_pt, EYE_RADIUS * scale, c_sac)
    draw_sphere(eye_r_pt, EYE_RADIUS * scale, c_sac)
    # Eye cowls
    draw_sphere(eye_l_pt, (EYE_RADIUS * 1.35) * scale, c_plates)
    draw_sphere(eye_r_pt, (EYE_RADIUS * 1.35) * scale, c_plates)

    # Twisted spiral fungal horns (r=0.10, l=0.85) projecting at (+/-35 deg yaw, +15 deg pitch)
    # Each horn is constructed from 4 tapered articulating cylinder segments with calcified rings
    horn_segments = 4
    horn_sides = [(-1.0, -0.18), (1.0, 0.18)]  # (sign, base_x_offset)

    for sign, x_base in horn_sides:
        curr_hx = head_lx + x_base
        curr_hy = head_ly + 0.18
        curr_hz = head_lz + 0.18

        # Base orientation angles
        base_yaw = sign * (35.0 * (math.pi / 180.0))
        base_pitch = 15.0 * (math.pi / 180.0)

        seg_len = HORN_LENGTH / float(horn_segments)

        for s in range(horn_segments):
            s_prog = s / float(horn_segments)
            # Spiral curvature: flares outward, forward, and curves gently upwards
            cur_yaw = base_yaw + sign * (0.12 * math.sin(s * 1.4) + s * 0.08)
            cur_pitch = base_pitch + s * 0.08

            next_hx = curr_hx + math.sin(cur_yaw) * seg_len
            next_hy = curr_hy + math.sin(cur_pitch) * seg_len
            next_hz = curr_hz + math.cos(cur_yaw) * seg_len

            start_w = transform_torso_pt(curr_hx, curr_hy, curr_hz)
            end_w = transform_torso_pt(next_hx, next_hy, next_hz)

            r_start = (0.10 * (1.0 - s_prog * 0.70)) * scale
            r_end = (0.10 * (1.0 - (s_prog + 0.25) * 0.70)) * scale

            draw_cylinder_ex(start_w, end_w, r_start, r_end, 7, c_horns)

            # Calcified fungal nodule rings along the horns
            if s > 0:
                draw_sphere(start_w, (r_start * 1.30) * scale, c_plates)

            if show_wireframe:
                draw_sphere_wires(end_w, r_end * scale, 4, 4, c_plates)

            curr_hx = next_hx
            curr_hy = next_hy
            curr_hz = next_hz

        # Sharp horn tip
        tip_w = transform_torso_pt(curr_hx, curr_hy, curr_hz)
        draw_sphere(tip_w, 0.035 * scale, c_plates)

    # --------------------------------------------------------------------------
    # 5. FOUR HEAVY PILLAR LEGS & STOMPING HOOVES
    # --------------------------------------------------------------------------
    # 4 pillar legs at x = +/-0.38 with high-impact gallop stride
    leg_coords = [
        # (name, lx, lz, phase)
        ("FL", -LEG_X_OFFSET,  0.42, 0.0),
        ("FR",  LEG_X_OFFSET,  0.42, 0.9),
        ("HL", -LEG_X_OFFSET, -0.45, 2.7),
        ("HR",  LEG_X_OFFSET, -0.45, 3.6),
    ]

    for name, lx, lz, phase in leg_coords:
        # High-impact stampede stride angle: leg_angle = sin(anim_timer * 5.5 + phase) * 0.45 rad
        leg_angle = math.sin(anim_timer * STAMPEDE_SPEED + phase) * 0.45

        # Hip socket anchored to torso
        hip_ly = 0.75
        hip_w = transform_torso_pt(lx, hip_ly, lz)

        # Muscular shoulder/hip ball joint
        draw_sphere(hip_w, (LEG_RADIUS * 1.45) * scale, c_flesh)
        if show_wireframe:
            draw_sphere_wires(hip_w, (LEG_RADIUS * 1.45) * scale, 6, 6, c_plates)

        # Dynamic foot ground placement
        # Foot swings along Z axis and lifts when swinging forward
        foot_lz = lz + math.sin(leg_angle) * LEG_LENGTH
        foot_lift = max(0.0, -math.sin(leg_angle) * 0.18)
        foot_ly = foot_lift

        hoof_w = transform_pt(lx, foot_ly + (HOOF_HEIGHT * 0.5), foot_lz)

        # Heavy pillar leg column cylinder (r=0.15, l=0.65)
        draw_cylinder_ex(hip_w, hoof_w, LEG_RADIUS * scale, (LEG_RADIUS * 1.20) * scale, 8, c_flesh)

        # Armored calcified knee/hock shield plate
        mid_ly = foot_ly + (hip_ly - foot_ly) * 0.48
        mid_lz = (lz + foot_lz) * 0.50
        knee_w = transform_pt(lx, mid_ly, mid_lz + 0.08)
        draw_cube(knee_w, 0.28 * scale, 0.22 * scale, 0.16 * scale, c_plates)
        if show_wireframe:
            draw_cube_wires(knee_w, 0.28 * scale, 0.22 * scale, 0.16 * scale, c_horns)

        # Heavy stomping hoof block (0.34 x 0.14 x 0.36)
        hoof_block_pos = transform_pt(lx, foot_ly + (HOOF_HEIGHT * 0.5), foot_lz)
        draw_cube(hoof_block_pos, (HOOF_RADIUS * 2.0) * scale, HOOF_HEIGHT * scale, (HOOF_RADIUS * 2.1) * scale, c_horns)
        if show_wireframe:
            draw_cube_wires(hoof_block_pos, (HOOF_RADIUS * 2.0) * scale, HOOF_HEIGHT * scale, (HOOF_RADIUS * 2.1) * scale, c_plates)

        # Cloven fungal hoof claws (2 front spurs per hoof)
        for claw_idx in (-1, 1):
            claw_base = transform_pt(lx + claw_idx * 0.08, foot_ly + 0.04, foot_lz + HOOF_RADIUS * 0.85)
            claw_tip = transform_pt(lx + claw_idx * 0.09, foot_ly, foot_lz + HOOF_RADIUS * 1.55)
            draw_cylinder_ex(claw_base, claw_tip, 0.045 * scale, 0.015 * scale, 4, c_plates)

    # --------------------------------------------------------------------------
    # 6. SWIRLING TOXIC SPORE CLOUD MOTES (Spheres in c_spores)
    # --------------------------------------------------------------------------
    # Deterministic animated particle motes drifting upward from chimneys
    spore_particle_count = 8
    for i in range(spore_particle_count):
        # Time-based rising cycle
        p_cycle = (anim_timer * 1.8 + i * 0.42) % 2.0
        p_t = p_cycle / 2.0  # 0.0 to 1.0

        drift_x = math.sin(i * 1.85 + anim_timer * 3.2) * (0.35 + p_t * 0.45)
        drift_y = 1.65 + p_t * 0.85
        drift_z = 0.20 + math.cos(i * 1.45 + anim_timer * 2.8) * (0.30 + p_t * 0.40)

        spore_pt = transform_torso_pt(drift_x, drift_y, drift_z)
        spore_radius = (0.042 * (1.0 - p_t * 0.55)) * scale

        draw_sphere(spore_pt, spore_radius, c_spores)


# ==============================================================================
# PART 5: STANDALONE 3D ORBIT VIEWER (ModelViewerApp)
# ==============================================================================
class ModelViewerApp:
    """
    Interactive 3D previewer allowing inspection, rotation, zooming,
    wireframe toggle, palette swapping, and automated 3-frame smoke testing.
    """
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        init_window(self.screen_width, self.screen_height, "3D Model Inspector - Spore-Spitting Quadruped Bull")
        set_target_fps(60)

        # 3D Orbit Camera Setup
        self.camera = Camera3D(
            Vector3(3.5, 2.5, 4.2),   # Camera position
            Vector3(0.0, 0.9, 0.1),   # Target focus point
            Vector3(0.0, 1.0, 0.0),   # Up vector
            45.0,                     # FOV
            CAMERA_PERSPECTIVE
        )

        self.anim_timer = 0.0
        self.anim_playing = True
        self.rotation_y = 45.0
        self.show_wireframe = False
        self.active_palette_idx = 0
        self.palettes = [DEFAULT_SPORE_BULL_PALETTE, CRIMSON_MYCELIUM_PALETTE]
        self.palette_names = ["Toxic Moss Green", "Crimson Mycelium"]

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
        clear_background(Color(20, 24, 28, 255))

        # 3D Scene Rendering
        begin_mode_3d(self.camera)
        draw_grid(12, 1.0)
        draw_spore_bull_3d(
            Vector3(0.0, 0.0, 0.0),
            rotation_y=self.rotation_y,
            anim_timer=self.anim_timer,
            scale=1.0,
            palette=self.palettes[self.active_palette_idx],
            show_wireframe=self.show_wireframe
        )
        end_mode_3d()

        # HUD & Telemetry Overlay (Keeps x=450..980 clear for global bar)
        draw_text("3D MODEL INSPECTOR: Spore-Spitting Quadruped Bull", 24, 20, 20, RAYWHITE)
        draw_text("[L-Drag / Left-Right] Orbit | [Space] Play/Pause | [P] Palette | [W] Wireframe", 24, 52, 14, LIGHTGRAY)
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
