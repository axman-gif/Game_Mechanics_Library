# -*- coding: utf-8 -*-
"""
Apex Mantis Stalker - 3D Procedural Primitive Model
===================================================
ID               : m3d_beast_mantis_stalker
Category         : beast
Concept Name     : Apex Mantis Stalker
Target File      : assets/models_3D/beast/mantis_stalker.py
Primitives Used  : Tapered Prisms (slender prothoracic stalk 0.22x0.70x0.24, segmented abdomen pod
                   0.40x0.35x1.10 tapering to a caudal point, triangular cranial wedge 0.28x0.24x0.26),
                   Cylinders (4 slender multi-jointed cursorial walking legs r=0.04 l=0.85, 2 raptorial
                   folded scythe arm femora r=0.06 l=0.65, 2 serrated folding tibiae r=0.045 l=0.75),
                   Spheres (dual faceted hemispherical compound eyes r=0.08, spherical thoracic ball
                   joints r=0.07, antennal bead bases r=0.02).
Animation Loop   : 4-legged alternating tripod gait stride, swaying predatory stalk poise, oscillating
                   raptorial forelimb scythes with periodic rapid snapping strike, sinusoidal abdomen
                   breathing volume pulsing, swiveling triangular cranium.

Problem Solved:
  Eliminates static, resource-heavy 3D mesh files (.obj/.fbx) and complex skeletal animation
  rigs by synthesizing an apex predatory mantis stalker purely from Raylib geometric primitives
  and trigonometric inverse-kinematic chains in real time.

How the Procedural Articulation Works:
  - Ground anchor at (0, 0, 0) with central thoracic core anchored at y = 0.95 (STALK_ELEVATION).
  - Slender prothoracic stalk arches upward and forward to the upper prothorax collar at (0, 1.25, 0.26).
  - Triangular cranial head sits at (0, 1.30, 0.35), swiveling dynamically (yaw, pitch, tilt) to track prey.
  - Abdomen pod suspends rearward from (0, 0.95, -0.15) angling down to (0, 0.70, -0.90), pulsing with
    sinusoidal respiratory volume dilation (scale_z = 1.0 + 0.05 * sin(anim_timer * 1.6)).
  - Raptorial scythe arms hinge at upper prothorax (x = +/-0.18, y = 1.20, z = 0.25), oscillating in poised
    hunting stance and executing periodic rapid forward snapping strikes.
  - 4 cursorial walking legs execute an alternating diagonal tripod gait (leg_swing = sin(anim_timer * 3.8 + phase) * 0.30 rad).

C++ Raylib Equivalent:
  struct MantisStalkerPalette {
      Color chitin_emerald;
      Color abdomen_under;
      Color scythe_edge;
      Color compound_eyes;
      Color joint_connectors;
  };

  void DrawMantisStalker3D(Vector3 position, float rotation_y, float anim_timer, float scale, const MantisStalkerPalette* palette, bool show_wireframe);
  Mapped directly to DrawCube, DrawCubeWires, DrawSphere, DrawSphereWires, DrawCylinderEx, and DrawLine3D from raylib.h.
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
# const MantisStalkerPalette DEFAULT_MANTIS_PALETTE = { ... };

DEFAULT_MANTIS_PALETTE = {
    "chitin_emerald": Color(35, 120, 65, 255),      # Iridescent deep green exoskeleton
    "abdomen_under": Color(180, 205, 140, 255),     # Pale ventral segmentation
    "scythe_edge": Color(240, 240, 220, 255),       # Razor-sharp chitin ivory
    "compound_eyes": Color(220, 30, 45, 255),       # Faceted ruby red sensory orbs
    "joint_connectors": Color(50, 75, 45, 255),     # Flexible dark olive cuticle
}

PHANTOM_GHOST_PALETTE = {
    "chitin_emerald": Color(200, 220, 215, 255),    # Ghostly translucent mantis white
    "abdomen_under": Color(160, 185, 190, 255),     # Chilled mist pale
    "scythe_edge": Color(80, 210, 225, 255),        # Cyan razor glaze
    "compound_eyes": Color(120, 40, 200, 255),      # Violet sensory orbs
    "joint_connectors": Color(110, 130, 135, 255),  # Pale tendon grey
}

# Named geometric proportions
THORAX_LENGTH = 0.70
ABDOMEN_LENGTH = 1.10
SCYTHE_LENGTH = 0.75
LEG_SPAN = 0.60
EYE_RADIUS = 0.08
STALK_ELEVATION = 0.95

PROTHORAX_WIDTH = 0.22
PROTHORAX_HEIGHT = 0.70
PROTHORAX_DEPTH = 0.24

ABDOMEN_WIDTH = 0.40
ABDOMEN_HEIGHT = 0.35

CRANIAL_WIDTH = 0.28
CRANIAL_HEIGHT = 0.24
CRANIAL_DEPTH = 0.26

WALKING_LEG_RADIUS = 0.04
WALKING_LEG_LENGTH = 0.85
SCYTHE_FEMUR_RADIUS = 0.06
SCYTHE_FEMUR_LENGTH = 0.65
SCYTHE_TIBIA_RADIUS = 0.045
THORACIC_BALL_RADIUS = 0.07
ANTENNA_BEAD_RADIUS = 0.02

# Animation timing rates
GAIT_CYCLE_RATE = 3.8
SCYTHE_CYCLE_RATE = 2.2
BREATHING_RATE = 1.6
HEAD_SWIVEL_RATE = 1.8


# ==============================================================================
# PART 4: CANONICAL 3D PROCEDURAL DRAWING FUNCTION
# ==============================================================================
def draw_mantis_stalker_3d(
    position: Vector3,
    rotation_y: float = 0.0,
    anim_timer: float = 0.0,
    scale: float = 1.0,
    palette: dict = None,
    show_wireframe: bool = False
) -> None:
    """
    Renders an articulated 3D Apex Mantis Stalker with procedural cursorial tripod gait,
    swiveling triangular cranium, breathing abdomen pod, and poised raptorial scythes.
    Must be called between begin_mode_3d(camera) and end_mode_3d().
    """
    pal = palette if palette is not None else DEFAULT_MANTIS_PALETTE

    c_chitin = pal.get("chitin_emerald", DEFAULT_MANTIS_PALETTE["chitin_emerald"])
    c_under = pal.get("abdomen_under", DEFAULT_MANTIS_PALETTE["abdomen_under"])
    c_scythe = pal.get("scythe_edge", DEFAULT_MANTIS_PALETTE["scythe_edge"])
    c_eyes = pal.get("compound_eyes", DEFAULT_MANTIS_PALETTE["compound_eyes"])
    c_joints = pal.get("joint_connectors", DEFAULT_MANTIS_PALETTE["joint_connectors"])

    # Rotation matrix components for Y-axis orientation
    rad_y = rotation_y * (math.pi / 180.0)
    cos_r = math.cos(rad_y)
    sin_r = math.sin(rad_y)

    bx, by, bz = position.x, position.y, position.z

    # Predatory stalking micro-sway and breathing bob
    stalk_sway = math.sin(anim_timer * (GAIT_CYCLE_RATE * 0.5)) * 0.02
    stalk_bob = math.cos(anim_timer * GAIT_CYCLE_RATE) * 0.015

    # Transform local model coordinates to world space
    def transform_pt(lx: float, ly: float, lz: float) -> Vector3:
        wx = bx + (lx * cos_r + lz * sin_r) * scale
        wy = by + ly * scale
        wz = bz + (-lx * sin_r + lz * cos_r) * scale
        return Vector3(wx, wy, wz)

    # 1. PTEROTHORAX CORE (Suspension Hub & Metapleuron)
    pt_core = transform_pt(stalk_sway, STALK_ELEVATION + stalk_bob, -0.05)
    draw_sphere(pt_core, THORACIC_BALL_RADIUS * 1.25 * scale, c_joints)
    draw_cube(pt_core, 0.22 * scale, 0.20 * scale, 0.28 * scale, c_chitin)
    if show_wireframe:
        draw_cube_wires(pt_core, 0.23 * scale, 0.21 * scale, 0.29 * scale, c_scythe)
        draw_sphere_wires(pt_core, THORACIC_BALL_RADIUS * 1.28 * scale, 6, 6, c_joints)

    # 2. SLENDER PROTHORACIC STALK (Tapered Pronotum 0.22 x 0.70 x 0.24)
    p_stalk_bot = transform_pt(stalk_sway, STALK_ELEVATION + stalk_bob + 0.02, 0.02)
    p_stalk_mid = transform_pt(stalk_sway * 1.2, STALK_ELEVATION + stalk_bob + 0.16, 0.14)
    p_stalk_top = transform_pt(stalk_sway * 1.4, STALK_ELEVATION + stalk_bob + 0.30, 0.26)

    draw_cylinder_ex(p_stalk_bot, p_stalk_mid, 0.10 * scale, 0.09 * scale, 8, c_chitin)
    draw_cylinder_ex(p_stalk_mid, p_stalk_top, 0.09 * scale, 0.075 * scale, 8, c_chitin)

    # Lateral pronotal flanges (tapered prisms/cubes)
    p_flange_low = transform_pt(stalk_sway * 1.1, STALK_ELEVATION + stalk_bob + 0.10, 0.08)
    p_flange_up = transform_pt(stalk_sway * 1.3, STALK_ELEVATION + stalk_bob + 0.23, 0.20)
    draw_cube(p_flange_low, PROTHORAX_WIDTH * scale, 0.18 * scale, 0.22 * scale, c_chitin)
    draw_cube(p_flange_up, (PROTHORAX_WIDTH * 0.90) * scale, 0.16 * scale, 0.20 * scale, c_chitin)

    # Dorsal spine ridge along the prothorax
    p_ridge = transform_pt(stalk_sway * 1.2, STALK_ELEVATION + stalk_bob + 0.18, 0.14)
    draw_cube(p_ridge, 0.04 * scale, 0.32 * scale, 0.26 * scale, c_joints)
    if show_wireframe:
        draw_cube_wires(p_flange_low, (PROTHORAX_WIDTH + 0.01) * scale, 0.19 * scale, 0.23 * scale, c_joints)
        draw_cube_wires(p_flange_up, (PROTHORAX_WIDTH * 0.90 + 0.01) * scale, 0.17 * scale, 0.21 * scale, c_joints)

    # Collar knuckle ball joint (Neck Socket at (0, 1.30, 0.35))
    p_collar = transform_pt(stalk_sway * 1.4, 1.25 + stalk_bob, 0.26)
    draw_sphere(p_collar, THORACIC_BALL_RADIUS * scale, c_joints)

    # 3. TRIANGULAR CRANIAL WEDGE & COMPOUND OPTICS (0.28 x 0.24 x 0.26)
    head_yaw = math.sin(anim_timer * HEAD_SWIVEL_RATE) * 0.18
    head_pitch = math.sin(anim_timer * 2.5) * 0.10
    head_tilt = math.cos(anim_timer * 1.4) * 0.08

    cos_hy, sin_hy = math.cos(head_yaw), math.sin(head_yaw)
    cos_hp, sin_hp = math.cos(head_pitch), math.sin(head_pitch)
    cos_ht, sin_ht = math.cos(head_tilt), math.sin(head_tilt)

    def transform_head_pt(lx: float, ly: float, lz: float) -> Vector3:
        x1 = lx * cos_hy + lz * sin_hy
        z1 = -lx * sin_hy + lz * cos_hy
        y2 = ly * cos_hp - z1 * sin_hp
        z2 = ly * sin_hp + z1 * cos_hp
        x3 = x1 * cos_ht - y2 * sin_ht
        y3 = x1 * sin_ht + y2 * cos_ht
        return transform_pt(stalk_sway * 1.5 + x3, 1.30 + stalk_bob + y3, 0.35 + z2)

    # Neck hinge joint
    draw_sphere(transform_head_pt(0.0, -0.02, -0.03), 0.05 * scale, c_joints)

    # Inverted triangular cranium
    head_center = transform_head_pt(0.0, 0.06, 0.06)
    draw_cube(head_center, CRANIAL_WIDTH * scale, 0.16 * scale, 0.22 * scale, c_chitin)
    clypeus_pt = transform_head_pt(0.0, -0.05, 0.08)
    draw_cube(clypeus_pt, 0.14 * scale, 0.12 * scale, 0.14 * scale, c_chitin)
    if show_wireframe:
        draw_cube_wires(head_center, (CRANIAL_WIDTH + 0.01) * scale, 0.17 * scale, 0.23 * scale, c_scythe)

    # Chewing mandibles with predatory twitch
    mandible_twitch = math.sin(anim_timer * 8.5) * 0.015
    m_base_l = transform_head_pt(0.045, -0.10, 0.08)
    m_tip_l = transform_head_pt(0.015 + mandible_twitch, -0.16, 0.09)
    m_base_r = transform_head_pt(-0.045, -0.10, 0.08)
    m_tip_r = transform_head_pt(-0.015 - mandible_twitch, -0.16, 0.09)
    draw_cylinder_ex(m_base_l, m_tip_l, 0.024 * scale, 0.006 * scale, 4, c_scythe)
    draw_cylinder_ex(m_base_r, m_tip_r, 0.024 * scale, 0.006 * scale, 4, c_scythe)

    # Dual faceted hemispherical compound eyes (r = EYE_RADIUS = 0.08)
    eye_pos_l = transform_head_pt(0.13, 0.08, 0.06)
    eye_pos_r = transform_head_pt(-0.13, 0.08, 0.06)
    draw_sphere(eye_pos_l, EYE_RADIUS * scale, c_eyes)
    draw_sphere(eye_pos_r, EYE_RADIUS * scale, c_eyes)
    draw_sphere_wires(eye_pos_l, (EYE_RADIUS * 1.03) * scale, 6, 6, c_joints)
    draw_sphere_wires(eye_pos_r, (EYE_RADIUS * 1.03) * scale, 6, 6, c_joints)

    # Compound eye tracking pseudopupils (dark optical focus spots)
    pupil_l = transform_head_pt(0.135, 0.08, 0.135)
    pupil_r = transform_head_pt(-0.135, 0.08, 0.135)
    draw_sphere(pupil_l, 0.022 * scale, Color(24, 24, 28, 255))
    draw_sphere(pupil_r, 0.022 * scale, Color(24, 24, 28, 255))

    # Antennal bead bases (r = 0.02) and arching feelers
    ant_base_l = transform_head_pt(0.05, 0.16, 0.11)
    ant_base_r = transform_head_pt(-0.05, 0.16, 0.11)
    draw_sphere(ant_base_l, ANTENNA_BEAD_RADIUS * scale, c_joints)
    draw_sphere(ant_base_r, ANTENNA_BEAD_RADIUS * scale, c_joints)

    ant_twitch_x = math.sin(anim_timer * 5.0) * 0.025
    ant_twitch_y = math.cos(anim_timer * 4.2) * 0.025
    ant_mid_l = transform_head_pt(0.09 + ant_twitch_x, 0.30 + ant_twitch_y, 0.20)
    ant_tip_l = transform_head_pt(0.14 + ant_twitch_x * 1.5, 0.44 + ant_twitch_y * 1.5, 0.30)
    ant_mid_r = transform_head_pt(-0.09 - ant_twitch_x, 0.30 + ant_twitch_y, 0.20)
    ant_tip_r = transform_head_pt(-0.14 - ant_twitch_x * 1.5, 0.44 + ant_twitch_y * 1.5, 0.30)

    draw_cylinder_ex(ant_base_l, ant_mid_l, 0.014 * scale, 0.008 * scale, 4, c_joints)
    draw_cylinder_ex(ant_mid_l, ant_tip_l, 0.008 * scale, 0.003 * scale, 4, c_joints)
    draw_cylinder_ex(ant_base_r, ant_mid_r, 0.014 * scale, 0.008 * scale, 4, c_joints)
    draw_cylinder_ex(ant_mid_r, ant_tip_r, 0.008 * scale, 0.003 * scale, 4, c_joints)

    # 4. SEGMENTED ABDOMEN POD (0.40 x 0.35 x 1.10 Tapering Pod)
    breathe_scale_z = 1.0 + 0.05 * math.sin(anim_timer * BREATHING_RATE)
    breathe_radial = 1.0 + 0.04 * math.sin(anim_timer * BREATHING_RATE + 0.4)

    # Petiole pedicel connector
    p_petiole = transform_pt(stalk_sway * 0.5, 0.93 + stalk_bob, -0.15)
    draw_sphere(p_petiole, 0.085 * scale, c_joints)

    # 5 articulated abdominal segments tapering to caudal point at (0, 0.70, -0.90)
    seg_offsets = [
        (-0.27, 0.91, 0.32, 0.28, 0.18),
        (-0.43, 0.86, 0.40, 0.35, 0.20),
        (-0.59, 0.80, 0.36, 0.31, 0.19),
        (-0.73, 0.75, 0.28, 0.24, 0.17),
        (-0.86, 0.70, 0.18, 0.15, 0.15),
    ]

    for z_base, y_base, seg_w, seg_h, seg_l in seg_offsets:
        curr_z = -0.15 + (z_base + 0.15) * breathe_scale_z
        p_dorsal = transform_pt(stalk_sway * 0.4, y_base + stalk_bob + 0.03, curr_z)
        p_ventral = transform_pt(stalk_sway * 0.4, y_base + stalk_bob - 0.04, curr_z)

        w_scaled = seg_w * breathe_radial * scale
        h_dorsal = seg_h * 0.55 * breathe_radial * scale
        h_ventral = seg_h * 0.45 * breathe_radial * scale
        l_scaled = seg_l * scale

        draw_cube(p_dorsal, w_scaled, h_dorsal, l_scaled, c_chitin)
        draw_cube(p_ventral, w_scaled * 0.92, h_ventral, l_scaled, c_under)

        p_ring = transform_pt(stalk_sway * 0.4, y_base + stalk_bob, curr_z)
        draw_sphere(p_ring, (seg_w * 0.38) * breathe_radial * scale, c_joints)

        if show_wireframe:
            draw_cube_wires(p_dorsal, w_scaled + 0.01 * scale, h_dorsal + 0.01 * scale, l_scaled, c_joints)

    # Dorsal folded elytra / tegmina wing covers
    p_wing_l = transform_pt(0.08, 0.88 + stalk_bob, -0.46 * breathe_scale_z)
    p_wing_r = transform_pt(-0.08, 0.88 + stalk_bob, -0.46 * breathe_scale_z)
    draw_cube(p_wing_l, 0.15 * scale, 0.024 * scale, 0.54 * scale, c_chitin)
    draw_cube(p_wing_r, 0.15 * scale, 0.024 * scale, 0.54 * scale, c_chitin)
    if show_wireframe:
        draw_cube_wires(p_wing_l, 0.155 * scale, 0.028 * scale, 0.545 * scale, c_scythe)
        draw_cube_wires(p_wing_r, 0.155 * scale, 0.028 * scale, 0.545 * scale, c_scythe)

    # Caudal sensory cerci at terminal tip
    caudal_z = -0.15 - 0.76 * breathe_scale_z
    cercus_base_l = transform_pt(0.05, 0.70 + stalk_bob, caudal_z)
    cercus_tip_l = transform_pt(0.11, 0.72 + stalk_bob, caudal_z - 0.14)
    cercus_base_r = transform_pt(-0.05, 0.70 + stalk_bob, caudal_z)
    cercus_tip_r = transform_pt(-0.11, 0.72 + stalk_bob, caudal_z - 0.14)
    draw_cylinder_ex(cercus_base_l, cercus_tip_l, 0.015 * scale, 0.003 * scale, 4, c_scythe)
    draw_cylinder_ex(cercus_base_r, cercus_tip_r, 0.015 * scale, 0.003 * scale, 4, c_scythe)

    # 5. RAPTORIAL SCYTHE FOREARMS (Hinged at (x=+/-0.18, y=1.20, z=0.25))
    scythe_poise = 0.20 + 0.15 * math.sin(anim_timer * SCYTHE_CYCLE_RATE)
    strike_cycle = (anim_timer * 0.75) % 3.6
    strike_snap = 0.0
    if strike_cycle < 0.22:
        strike_snap = math.sin((strike_cycle / 0.22) * math.pi) * 0.68
    elif strike_cycle < 0.36:
        recoil = (strike_cycle - 0.22) / 0.14
        strike_snap = (1.0 - recoil) * 0.22

    effective_flex = scythe_poise + strike_snap

    for side in [1.0, -1.0]:
        p_sh = transform_pt(side * 0.18 + stalk_sway * 1.4, 1.20 + stalk_bob, 0.25)
        draw_sphere(p_sh, THORACIC_BALL_RADIUS * scale, c_joints)

        # Coxa (shoulder stem)
        coxa_end = transform_pt(
            side * 0.21 + stalk_sway * 1.4,
            1.04 + stalk_bob - effective_flex * 0.08,
            0.43 + effective_flex * 0.09
        )
        draw_cylinder_ex(p_sh, coxa_end, 0.052 * scale, 0.046 * scale, 6, c_chitin)
        draw_sphere(coxa_end, 0.052 * scale, c_joints)

        # Femur (spined raptorial thigh, r=0.06, l=0.65)
        fem_pitch = -0.70 + effective_flex * 1.05
        fem_dy = -SCYTHE_FEMUR_LENGTH * math.cos(fem_pitch)
        fem_dz = SCYTHE_FEMUR_LENGTH * math.sin(fem_pitch)
        fem_dx = side * (0.05 - effective_flex * 0.03)

        knee_end = transform_pt(
            side * 0.21 + fem_dx + stalk_sway * 1.4,
            1.04 + stalk_bob - effective_flex * 0.08 + fem_dy,
            0.43 + effective_flex * 0.09 + fem_dz
        )
        draw_cylinder_ex(coxa_end, knee_end, SCYTHE_FEMUR_RADIUS * scale, (SCYTHE_FEMUR_RADIUS * 0.85) * scale, 6, c_chitin)
        draw_sphere(knee_end, 0.056 * scale, c_joints)

        # Grasping spines along the ventral groove of the femur
        for sp_frac in [0.25, 0.45, 0.65, 0.85]:
            sb_x = coxa_end.x + (knee_end.x - coxa_end.x) * sp_frac
            sb_y = coxa_end.y + (knee_end.y - coxa_end.y) * sp_frac
            sb_z = coxa_end.z + (knee_end.z - coxa_end.z) * sp_frac
            sp_base = Vector3(sb_x, sb_y, sb_z)
            sp_tip = Vector3(sb_x - side * 0.04 * scale, sb_y - 0.06 * scale, sb_z + 0.03 * scale)
            draw_cylinder_ex(sp_base, sp_tip, 0.016 * scale, 0.003 * scale, 4, c_scythe)

        # Tibia (serrated folding scythe, r=0.045, l=0.75)
        fold_angle = 2.30 - effective_flex * 1.80
        tib_pitch = fem_pitch + fold_angle
        tib_dy = SCYTHE_LENGTH * math.cos(tib_pitch)
        tib_dz = SCYTHE_LENGTH * math.sin(tib_pitch)
        tib_dx = side * 0.03

        tibia_tip = Vector3(knee_end.x + tib_dx * scale, knee_end.y + tib_dy * scale, knee_end.z + tib_dz * scale)
        draw_cylinder_ex(knee_end, tibia_tip, SCYTHE_TIBIA_RADIUS * scale, 0.018 * scale, 6, c_chitin)

        # Ivory razor cutting edge along inner margin
        blade_start = Vector3(knee_end.x - side * 0.015 * scale, knee_end.y + 0.03 * scale, knee_end.z)
        blade_end = Vector3(tibia_tip.x - side * 0.015 * scale, tibia_tip.y, tibia_tip.z)
        draw_cylinder_ex(blade_start, blade_end, 0.020 * scale, 0.006 * scale, 4, c_scythe)

        # Terminal hooked unguis talon at scythe tip
        talon_tip = Vector3(tibia_tip.x - side * 0.04 * scale, tibia_tip.y - 0.06 * scale, tibia_tip.z + 0.04 * scale)
        draw_cylinder_ex(tibia_tip, talon_tip, 0.016 * scale, 0.003 * scale, 4, c_scythe)

        # Serrated needle teeth along the tibia
        for t_frac in [0.20, 0.38, 0.56, 0.74, 0.90]:
            tb_x = knee_end.x + (tibia_tip.x - knee_end.x) * t_frac
            tb_y = knee_end.y + (tibia_tip.y - knee_end.y) * t_frac
            tb_z = knee_end.z + (tibia_tip.z - knee_end.z) * t_frac
            draw_cylinder_ex(Vector3(tb_x, tb_y, tb_z), Vector3(tb_x - side * 0.03 * scale, tb_y - 0.04 * scale, tb_z + 0.01 * scale), 0.010 * scale, 0.002 * scale, 4, c_scythe)

        if show_wireframe:
            draw_line_3d(coxa_end, knee_end, c_scythe)
            draw_line_3d(knee_end, tibia_tip, c_scythe)
            draw_line_3d(tibia_tip, talon_tip, c_eyes)

    # 6. CURSORIAL WALKING LEGS (4 Slender Stilt Legs, r=0.04, l=0.85)
    leg_configs = [
        (1.0, 0.15, 0.92, -0.05, 0.0),                  # Mid-Left
        (-1.0, -0.15, 0.92, -0.05, math.pi),            # Mid-Right
        (1.0, 0.17, 0.88, -0.28, math.pi),              # Hind-Left
        (-1.0, -0.17, 0.88, -0.28, 0.0),                # Hind-Right
    ]

    for side, h_x, h_y, h_z, phase in leg_configs:
        leg_swing = math.sin(anim_timer * GAIT_CYCLE_RATE + phase) * 0.30
        leg_lift = max(0.0, math.sin(anim_timer * GAIT_CYCLE_RATE + phase)) * 0.10

        p_hip = transform_pt(h_x + stalk_sway, h_y + stalk_bob, h_z)
        draw_sphere(p_hip, THORACIC_BALL_RADIUS * scale, c_joints)

        # High elevated knee (stilt-like cursorial geometry)
        knee_lx = side * (0.32 + LEG_SPAN * 0.35)
        knee_ly = 1.05 + leg_lift * 0.5
        knee_lz = h_z + leg_swing * 0.12
        p_knee = transform_pt(knee_lx, knee_ly, knee_lz)

        # Planted foot contacting ground plane (y = 0.0 + leg_lift)
        foot_lx = side * (0.28 + LEG_SPAN * 0.55)
        foot_ly = 0.0 + leg_lift
        foot_lz = h_z + leg_swing * 0.26
        p_foot = transform_pt(foot_lx, foot_ly, foot_lz)

        # Femur (hip to knee)
        draw_cylinder_ex(p_hip, p_knee, WALKING_LEG_RADIUS * scale, (WALKING_LEG_RADIUS * 0.85) * scale, 5, c_chitin)
        draw_sphere(p_knee, (WALKING_LEG_RADIUS * 1.15) * scale, c_joints)

        # Tibia (knee to foot)
        draw_cylinder_ex(p_knee, p_foot, (WALKING_LEG_RADIUS * 0.85) * scale, 0.016 * scale, 5, c_chitin)
        draw_sphere(p_foot, 0.024 * scale, c_joints)

        # Tibial spur thorns near the knee
        spur_base = Vector3(
            p_knee.x + (p_foot.x - p_knee.x) * 0.12,
            p_knee.y + (p_foot.y - p_knee.y) * 0.12,
            p_knee.z + (p_foot.z - p_knee.z) * 0.12
        )
        spur_tip = Vector3(spur_base.x + side * 0.04 * scale, spur_base.y + 0.03 * scale, spur_base.z)
        draw_cylinder_ex(spur_base, spur_tip, 0.012 * scale, 0.002 * scale, 4, c_scythe)

        if show_wireframe:
            draw_line_3d(p_hip, p_knee, c_joints)
            draw_line_3d(p_knee, p_foot, c_joints)
            draw_sphere_wires(p_knee, (WALKING_LEG_RADIUS * 1.2) * scale, 4, 4, c_scythe)


# ==============================================================================
# PART 5: C++ MAPPING & MEMORY LAYOUT (Zero "Pythonic Magic")
# ==============================================================================
# In C++ (raylib.h), this procedural model requires zero dynamic memory allocation:
#
# struct MantisStalkerPalette {
#     Color chitin_emerald;
#     Color abdomen_under;
#     Color scythe_edge;
#     Color compound_eyes;
#     Color joint_connectors;
# };
#
# static const MantisStalkerPalette DEFAULT_MANTIS_PALETTE = {
#     (Color){35, 120, 65, 255},
#     (Color){180, 205, 140, 255},
#     (Color){240, 240, 220, 255},
#     (Color){220, 30, 45, 255},
#     (Color){50, 75, 45, 255}
# };
#
# void DrawMantisStalker3D(Vector3 position, float rotation_y, float anim_timer, float scale, const MantisStalkerPalette* palette, bool show_wireframe);
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
    wireframe toggle, palette swapping, and automated 3-frame smoke testing.
    """
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        init_window(self.screen_width, self.screen_height, "3D Model Inspector - Apex Mantis Stalker")
        set_target_fps(60)

        # 3D Orbit Camera Setup
        self.camera = Camera3D(
            Vector3(2.8, 2.2, 3.6),   # Camera position
            Vector3(0.0, 0.95, 0.0),  # Target focus point
            Vector3(0.0, 1.0, 0.0),   # Up vector
            45.0,                     # FOV
            CAMERA_PERSPECTIVE
        )

        self.anim_timer = 0.0
        self.anim_playing = True
        self.rotation_y = 45.0
        self.show_wireframe = False
        self.active_palette_idx = 0
        self.palettes = [DEFAULT_MANTIS_PALETTE, PHANTOM_GHOST_PALETTE]
        self.palette_names = ["Apex Emerald", "Phantom Ghost"]

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
        clear_background(Color(18, 22, 20, 255))

        # 3D Scene Rendering
        begin_mode_3d(self.camera)
        draw_grid(12, 1.0)
        draw_mantis_stalker_3d(
            Vector3(0.0, 0.0, 0.0),
            rotation_y=self.rotation_y,
            anim_timer=self.anim_timer,
            scale=1.0,
            palette=self.palettes[self.active_palette_idx],
            show_wireframe=self.show_wireframe
        )
        end_mode_3d()

        # HUD & Telemetry Overlay (Keeps x=450..980 clear for global settings bar)
        draw_text("3D MODEL INSPECTOR: Apex Mantis Stalker", 24, 20, 20, RAYWHITE)
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
