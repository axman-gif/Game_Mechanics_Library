# -*- coding: utf-8 -*-
"""
Crystalline Sand Wyrm - 3D Procedural Primitive Model
======================================================
Category         : beast
Target File      : assets/models_3D/beast/sand_wyrm.py
Primitives Used  : 6 Segmented Tapered Prisms/Cubes (head carapace segment 0.70x0.65x0.80 tapering
                   to razor snout, followed by 5 telescoping articulated armored body segments
                   scaling from 0.75x0.70x0.85 down to tail tip 0.30x0.28x0.55), Spheres (dorsal
                   crystal sensory spike nodes r=0.08, triangular burrowing mandible hinges r=0.09),
                   and Cylinders (inter-segment ball/socket flexible spine bellows r=0.28 l=0.30).
Animation Loop   : Serpentine 3D sinusoidal undulating spine wave propagation, 3-part triangular
                   mandibles clamping open and shut, and vertical burrowing heave with sand friction.

Problem Solved:
  Eliminates bulky 3D mesh files (.obj/.fbx) and external texture dependencies by
  synthesizing a subterranean crystalline sand wyrm with segmented articulated armor
  plating, dynamic 3D undulating kinematics, and clamping triangular mandibles purely
  from Raylib geometric primitives in real time.

How the Procedural Articulation Works:
  - The model hierarchy is computed relative to a base 'position' (Vector3) at ground level.
  - Ground tracking anchor at (0,0,0); segment 0 (head) leads world trajectory.
  - Successive segments 1 through 5 parent to preceding segments with longitudinal offset
    z_step = -0.75 along path tangent history.
  - anim_timer drives serpentine 3D sinusoidal undulating spine wave propagation:
      Lateral slither: x_offset = 0.45 * math.sin(anim_timer * 4.0 - seg_idx * 0.85)
      Vertical burrowing heave: y_offset = 0.25 * math.cos(anim_timer * 4.0 - seg_idx * 0.85)
      Mandible clamp: clamp_angle = 0.35 * (0.5 + 0.5 * math.sin(anim_timer * 3.0))
  - Dive state / subterranean dipping: head pitches and heaves naturally with the wave.

C++ Raylib Equivalent:
  struct SandWyrmPalette {
      Color crystal_shell;
      Color body_core;
      Color jaw_edge;
      Color glow_nodes;
      Color sand_dust;
  };
  void DrawSandWyrm3D(Vector3 position, float rotation_y, float anim_timer, float scale,
                      const SandWyrmPalette* palette, bool show_wireframe);
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
# const SandWyrmPalette DEFAULT_SAND_WYRM_PALETTE = { ... };

DEFAULT_SAND_WYRM_PALETTE = {
    "crystal_shell": Color(225, 175, 75, 255),    # quartz amber
    "body_core":     Color(45, 40, 42, 255),       # obsidian rock
    "jaw_edge":      Color(180, 160, 140, 255),    # chiseled flint
    "glow_nodes":    Color(0, 220, 210, 255),      # bioluminescent teal
    "sand_dust":     Color(210, 190, 140, 255),    # desert dune sand
}

OBSIDIAN_WYRM_PALETTE = {
    "crystal_shell": Color(160, 40, 220, 255),    # void amethyst
    "body_core":     Color(20, 20, 25, 255),       # deep basalt
    "jaw_edge":      Color(80, 80, 95, 255),       # dark iron
    "glow_nodes":    Color(255, 60, 140, 255),     # plasma magenta
    "sand_dust":     Color(100, 90, 120, 255),     # ash dust
}

# Named geometric constants for anatomy and kinematics (replaces magic numbers)
SEGMENT_COUNT = 6
HEAD_LENGTH = 0.80
HEAD_WIDTH = 0.70
HEAD_HEIGHT = 0.65
SNOUT_LENGTH = 0.45
SNOUT_WIDTH = 0.40
SNOUT_HEIGHT = 0.30

BODY_SEG_LEN = 0.85
MAX_BODY_WIDTH = 0.75
MAX_BODY_HEIGHT = 0.70

TAIL_SEG_LEN = 0.55
TAIL_MIN_WIDTH = 0.30
TAIL_MIN_HEIGHT = 0.28

TOTAL_LENGTH = 4.80
LONGITUDINAL_STEP = 0.75
BASE_ELEVATION = 0.85

SLITHER_AMP_X = 0.45
BURROW_HEAVE_AMP_Y = 0.25
WAVE_SPEED = 4.0
WAVE_SPATIAL_LAG = 0.85

BELLOWS_RADIUS = 0.28
BELLOWS_LENGTH = 0.30

CRYSTAL_NODE_RADIUS = 0.08
MANDIBLE_HINGE_RADIUS = 0.09
MANDIBLE_CLAMP_SPEED = 3.0
MANDIBLE_CLAMP_MAX = 0.35


# ==============================================================================
# PART 4: CANONICAL 3D PROCEDURAL DRAWING FUNCTION
# ==============================================================================
def draw_sand_wyrm_3d(
    position: Vector3,
    rotation_y: float = 0.0,
    anim_timer: float = 0.0,
    scale: float = 1.0,
    palette: dict = None,
    show_wireframe: bool = False
) -> None:
    """
    Renders an articulated 3D Crystalline Sand Wyrm with procedural serpentine
    undulation, 3-part clamping mandibles, and flexible spine bellows.
    Must be called between begin_mode_3d(camera) and end_mode_3d().

    Parameters:
      position       : World-space base root location (ground level beneath wyrm).
      rotation_y     : Heading angle in DEGREES around Y axis (0 deg = facing +Z).
      anim_timer     : Elapsed seconds driving serpentine slither, heave, and mandibles.
      scale          : Geometric scaling factor (1.0 = standard wyrm ~4.8m length).
      palette        : Optional dictionary overriding DEFAULT_SAND_WYRM_PALETTE colors.
      show_wireframe : Boolean flag toggling geometric wireframe diagnostic overlays.
    """
    pal = palette if palette is not None else DEFAULT_SAND_WYRM_PALETTE

    c_shell = pal["crystal_shell"]
    c_core = pal["body_core"]
    c_jaw = pal["jaw_edge"]
    c_nodes = pal["glow_nodes"]
    c_dust = pal["sand_dust"]

    # Overall heading rotation in radians
    rad_r = rotation_y * (math.pi / 180.0)
    cos_r = math.cos(rad_r)
    sin_r = math.sin(rad_r)

    # Compute unrotated local centers for all 6 segments along the undulating wave
    # lx, ly, lz are in wyrm-local coordinates before rotation_y
    seg_lx = [0.0] * SEGMENT_COUNT
    seg_ly = [0.0] * SEGMENT_COUNT
    seg_lz = [0.0] * SEGMENT_COUNT

    for i in range(SEGMENT_COUNT):
        wave_phase = anim_timer * WAVE_SPEED - i * WAVE_SPATIAL_LAG
        seg_lx[i] = SLITHER_AMP_X * math.sin(wave_phase)
        seg_ly[i] = BASE_ELEVATION + BURROW_HEAVE_AMP_Y * math.cos(wave_phase)
        seg_lz[i] = -i * LONGITUDINAL_STEP

    # Compute tangent directions, yaw and pitch for each segment
    seg_yaw_rad = [0.0] * SEGMENT_COUNT
    seg_pitch_rad = [0.0] * SEGMENT_COUNT
    seg_yaw_deg = [0.0] * SEGMENT_COUNT
    seg_pitch_deg = [0.0] * SEGMENT_COUNT

    for i in range(SEGMENT_COUNT):
        if i == 0:
            dx = seg_lx[0] - seg_lx[1]
            dy = seg_ly[0] - seg_ly[1]
            dz = seg_lz[0] - seg_lz[1]
        else:
            dx = seg_lx[i - 1] - seg_lx[i]
            dy = seg_ly[i - 1] - seg_ly[i]
            dz = seg_lz[i - 1] - seg_lz[i]

        dist_h = math.sqrt(dx * dx + dz * dz)
        if dist_h < 0.0001:
            dist_h = 0.0001
        yaw = math.atan2(dx, dz)
        pitch = -math.atan2(dy, dist_h)

        seg_yaw_rad[i] = yaw
        seg_pitch_rad[i] = pitch
        seg_yaw_deg[i] = yaw * (180.0 / math.pi)
        seg_pitch_deg[i] = pitch * (180.0 / math.pi)

    # Local-to-world coordinate transformation helper for segment offsets
    def transform_seg_pt(seg_idx: int, ox: float, oy: float, oz: float) -> Vector3:
        p_rad = seg_pitch_rad[seg_idx]
        y_rad = seg_yaw_rad[seg_idx]

        # Pitch around local X
        oy1 = oy * math.cos(p_rad) - oz * math.sin(p_rad)
        oz1 = oy * math.sin(p_rad) + oz * math.cos(p_rad)
        ox1 = ox

        # Yaw around local Y
        ox2 = ox1 * math.cos(y_rad) + oz1 * math.sin(y_rad)
        oz2 = -ox1 * math.sin(y_rad) + oz1 * math.cos(y_rad)
        oy2 = oy1

        # Add segment local center
        wyrm_x = seg_lx[seg_idx] + ox2
        wyrm_y = seg_ly[seg_idx] + oy2
        wyrm_z = seg_lz[seg_idx] + oz2

        # Transform to world space by rotation_y and position
        wx = position.x + (wyrm_x * cos_r + wyrm_z * sin_r) * scale
        wy = position.y + wyrm_y * scale
        wz = position.z + (-wyrm_x * sin_r + wyrm_z * cos_r) * scale
        return Vector3(wx, wy, wz)

    # Helper: draw an oriented cube conforming to segment yaw and pitch
    def draw_oriented_cube(seg_idx: int, ox: float, oy: float, oz: float,
                           w: float, h: float, l: float, fill_col: Color, wire_col: Color = None):
        center = transform_seg_pt(seg_idx, ox, oy, oz)
        tot_yaw = rotation_y + seg_yaw_deg[seg_idx]
        pitch = seg_pitch_deg[seg_idx]

        rl_push_matrix()
        rl_translatef(center.x, center.y, center.z)
        rl_rotatef(tot_yaw, 0.0, 1.0, 0.0)
        rl_rotatef(pitch, 1.0, 0.0, 0.0)
        draw_cube(Vector3(0.0, 0.0, 0.0), w * scale, h * scale, l * scale, fill_col)
        if show_wireframe:
            draw_cube_wires(Vector3(0.0, 0.0, 0.0), w * scale, h * scale, l * scale, c_nodes)
        elif wire_col is not None:
            draw_cube_wires(Vector3(0.0, 0.0, 0.0), w * scale, h * scale, l * scale, wire_col)
        rl_pop_matrix()

    # --------------------------------------------------------------------------
    # 1. GROUND CONTACT SAND DUST PUFFS (subterranean burrowing friction)
    # --------------------------------------------------------------------------
    for i in range(SEGMENT_COUNT):
        if seg_ly[i] < BASE_ELEVATION - 0.08:
            dust_center = transform_seg_pt(i, 0.0, -0.25, 0.0)
            dust_base = Vector3(dust_center.x, position.y + 0.015, dust_center.z)
            dust_top = Vector3(dust_center.x, position.y + 0.035 * scale, dust_center.z)
            dust_radius = (0.48 - i * 0.04) * scale
            draw_cylinder_ex(dust_base, dust_top, dust_radius, dust_radius * 1.15, 8, c_dust)

    # --------------------------------------------------------------------------
    # 2. INTER-SEGMENT FLEXIBLE SPINE BELLOWS & BALL/SOCKET JOINTS
    # --------------------------------------------------------------------------
    for i in range(1, SEGMENT_COUNT):
        t = (i - 1) / 4.0
        bellows_r = (BELLOWS_RADIUS * (1.0 - t * 0.40)) * scale

        prev_len = HEAD_LENGTH if i == 1 else (BODY_SEG_LEN * (1.0 - (i - 2) * 0.15))
        curr_len = (BODY_SEG_LEN * (1.0 - t * 0.35))

        p_back = transform_seg_pt(i - 1, 0.0, 0.0, -prev_len * 0.35)
        p_front = transform_seg_pt(i, 0.0, 0.0, curr_len * 0.35)

        # Flexible accordion bellows cylinder
        draw_cylinder_ex(p_back, p_front, bellows_r, bellows_r * 0.95, 8, c_core)

        # Inter-segment spherical ball socket joint
        mid_x = (p_back.x + p_front.x) * 0.5
        mid_y = (p_back.y + p_front.y) * 0.5
        mid_z = (p_back.z + p_front.z) * 0.5
        mid_joint = Vector3(mid_x, mid_y, mid_z)
        draw_sphere(mid_joint, bellows_r * 1.05, c_core)
        if show_wireframe:
            draw_sphere_wires(mid_joint, bellows_r * 1.10, 6, 6, c_nodes)
        else:
            draw_sphere_wires(mid_joint, bellows_r * 1.08, 6, 6, c_jaw)

    # --------------------------------------------------------------------------
    # 3. SEGMENT 0: HEAD CARAPACE, RAZOR SNOUT & 3-PART TRIANGULAR MANDIBLES
    # --------------------------------------------------------------------------
    # A. Inner Cranial Core
    draw_oriented_cube(0, 0.0, -0.04, 0.0, HEAD_WIDTH * 0.85, HEAD_HEIGHT * 0.82, HEAD_LENGTH * 0.95, c_core, None)

    # B. Armored Carapace Segment (0.70 x 0.65 x 0.80)
    draw_oriented_cube(0, 0.0, 0.0, 0.0, HEAD_WIDTH, HEAD_HEIGHT, HEAD_LENGTH, c_shell, c_jaw)

    # C. Tapered Razor Snout Wedge
    snout_z = HEAD_LENGTH * 0.5 + SNOUT_LENGTH * 0.40
    draw_oriented_cube(0, 0.0, -0.06, snout_z, SNOUT_WIDTH, SNOUT_HEIGHT, SNOUT_LENGTH, c_shell, c_jaw)

    # D. Chiseled Snout Cutting Tip
    chisel_z = snout_z + SNOUT_LENGTH * 0.45
    draw_oriented_cube(0, 0.0, -0.08, chisel_z, SNOUT_WIDTH * 0.65, SNOUT_HEIGHT * 0.50, 0.22, c_jaw, None)

    # E. 3-Part Triangular Clamping Mandibles
    # Mandible clamp angle oscillates with anim_timer
    clamp_angle = MANDIBLE_CLAMP_MAX * (0.5 + 0.5 * math.sin(anim_timer * MANDIBLE_CLAMP_SPEED))

    # 1) Top Dorsal Rostrum Mandible (Hinged at top-center, clamps downward)
    top_hinge_pos = transform_seg_pt(0, 0.0, 0.22, 0.38)
    draw_sphere(top_hinge_pos, MANDIBLE_HINGE_RADIUS * scale, c_core)
    top_tip_y = 0.22 - math.sin(clamp_angle) * 0.44
    top_tip_z = 0.38 + math.cos(clamp_angle) * 0.50
    top_tip_pos = transform_seg_pt(0, 0.0, top_tip_y, top_tip_z)
    draw_cylinder_ex(top_hinge_pos, top_tip_pos, 0.075 * scale, 0.015 * scale, 5, c_jaw)
    draw_sphere(top_tip_pos, 0.035 * scale, c_nodes)

    # 2) Left Ventrolateral Mandible (Hinged lower-left, clamps inward and upward)
    left_hinge_pos = transform_seg_pt(0, -0.25, -0.15, 0.38)
    draw_sphere(left_hinge_pos, MANDIBLE_HINGE_RADIUS * scale, c_core)
    left_tip_x = -0.25 + math.sin(clamp_angle) * 0.26
    left_tip_y = -0.15 + math.sin(clamp_angle) * 0.18
    left_tip_z = 0.38 + math.cos(clamp_angle) * 0.50
    left_tip_pos = transform_seg_pt(0, left_tip_x, left_tip_y, left_tip_z)
    draw_cylinder_ex(left_hinge_pos, left_tip_pos, 0.075 * scale, 0.015 * scale, 5, c_jaw)
    draw_sphere(left_tip_pos, 0.035 * scale, c_nodes)

    # 3) Right Ventrolateral Mandible (Hinged lower-right, clamps inward and upward)
    right_hinge_pos = transform_seg_pt(0, 0.25, -0.15, 0.38)
    draw_sphere(right_hinge_pos, MANDIBLE_HINGE_RADIUS * scale, c_core)
    right_tip_x = 0.25 - math.sin(clamp_angle) * 0.26
    right_tip_y = -0.15 + math.sin(clamp_angle) * 0.18
    right_tip_z = 0.38 + math.cos(clamp_angle) * 0.50
    right_tip_pos = transform_seg_pt(0, right_tip_x, right_tip_y, right_tip_z)
    draw_cylinder_ex(right_hinge_pos, right_tip_pos, 0.075 * scale, 0.015 * scale, 5, c_jaw)
    draw_sphere(right_tip_pos, 0.035 * scale, c_nodes)

    # F. Cranial Dorsal Sensor Node & Twin Backward Horn Spires
    cranial_node_pos = transform_seg_pt(0, 0.0, HEAD_HEIGHT * 0.52 + 0.06, 0.05)
    draw_sphere(cranial_node_pos, CRYSTAL_NODE_RADIUS * scale, c_nodes)
    if show_wireframe:
        draw_sphere_wires(cranial_node_pos, (CRYSTAL_NODE_RADIUS * 1.15) * scale, 6, 6, c_nodes)

    horn_l_base = transform_seg_pt(0, -0.20, HEAD_HEIGHT * 0.50, -0.05)
    horn_l_tip = transform_seg_pt(0, -0.32, HEAD_HEIGHT * 0.50 + 0.24, -0.32)
    draw_cylinder_ex(horn_l_base, horn_l_tip, 0.045 * scale, 0.012 * scale, 4, c_shell)

    horn_r_base = transform_seg_pt(0, 0.20, HEAD_HEIGHT * 0.50, -0.05)
    horn_r_tip = transform_seg_pt(0, 0.32, HEAD_HEIGHT * 0.50 + 0.24, -0.32)
    draw_cylinder_ex(horn_r_base, horn_r_tip, 0.045 * scale, 0.012 * scale, 4, c_shell)

    # G. Faceted Lateral Sensory Eyes
    eye_l = transform_seg_pt(0, -HEAD_WIDTH * 0.48, 0.10, 0.16)
    eye_r = transform_seg_pt(0, HEAD_WIDTH * 0.48, 0.10, 0.16)
    draw_sphere(eye_l, 0.065 * scale, c_nodes)
    draw_sphere(eye_r, 0.065 * scale, c_nodes)

    # --------------------------------------------------------------------------
    # 4. SEGMENTS 1 THROUGH 5: TELESCOPING ARMORED BODY SEGMENTS
    # --------------------------------------------------------------------------
    for i in range(1, SEGMENT_COUNT):
        t = (i - 1) / 4.0  # 0.0 at segment 1, 1.0 at segment 5 (tail)

        w_i = (1.0 - t) * MAX_BODY_WIDTH + t * TAIL_MIN_WIDTH
        h_i = (1.0 - t) * MAX_BODY_HEIGHT + t * TAIL_MIN_HEIGHT
        l_i = (1.0 - t) * BODY_SEG_LEN + t * TAIL_SEG_LEN

        # A. Inner Core
        draw_oriented_cube(i, 0.0, -0.04, 0.0, w_i * 0.82, h_i * 0.80, l_i * 0.95, c_core, None)

        # B. Articulated Carapace Shell
        draw_oriented_cube(i, 0.0, 0.0, 0.0, w_i, h_i * 0.85, l_i * 0.88, c_shell, c_jaw)

        # C. Flared Dorsal Crest Ridge
        draw_oriented_cube(i, 0.0, h_i * 0.44, 0.0, w_i * 0.55, h_i * 0.24, l_i * 0.70, c_shell, c_jaw)

        # D. Dorsal Crystal Sensory Spike Node (Spheres r=0.08 scaling rearward)
        node_pos = transform_seg_pt(i, 0.0, h_i * 0.58, 0.0)
        node_r = (CRYSTAL_NODE_RADIUS * (1.0 - t * 0.35)) * scale
        draw_sphere(node_pos, node_r, c_nodes)
        if show_wireframe:
            draw_sphere_wires(node_pos, node_r * 1.15, 6, 6, c_nodes)

        # E. Twin Lateral Crystal Needles Flanking the Dorsal Node
        needle_l_base = transform_seg_pt(i, -w_i * 0.24, h_i * 0.42, 0.05)
        needle_l_tip = transform_seg_pt(i, -w_i * 0.52, h_i * 0.72, -0.08)
        draw_cylinder_ex(needle_l_base, needle_l_tip, 0.035 * scale, 0.008 * scale, 4, c_shell)

        needle_r_base = transform_seg_pt(i, w_i * 0.24, h_i * 0.42, 0.05)
        needle_r_tip = transform_seg_pt(i, w_i * 0.52, h_i * 0.72, -0.08)
        draw_cylinder_ex(needle_r_base, needle_r_tip, 0.035 * scale, 0.008 * scale, 4, c_shell)

        # F. Lateral Sand Skimmer Skirts
        skirt_w = 0.10 * w_i
        skirt_h = 0.18 * h_i
        skirt_l = 0.75 * l_i
        draw_oriented_cube(i, -w_i * 0.52, -h_i * 0.15, 0.0, skirt_w, skirt_h, skirt_l, c_jaw, None)
        draw_oriented_cube(i, w_i * 0.52, -h_i * 0.15, 0.0, skirt_w, skirt_h, skirt_l, c_jaw, None)

    # --------------------------------------------------------------------------
    # 5. SEGMENT 5: TAIL TIP EXCAVATING SPADE & STINGER
    # --------------------------------------------------------------------------
    l_tail = TAIL_SEG_LEN
    p_tail_base = transform_seg_pt(5, 0.0, 0.0, -l_tail * 0.45)
    p_tail_tip = transform_seg_pt(5, 0.0, 0.05, -l_tail * 0.45 - 0.35)
    draw_cylinder_ex(p_tail_base, p_tail_tip, 0.085 * scale, 0.012 * scale, 4, c_jaw)

    p_tail_node = transform_seg_pt(5, 0.0, 0.10, -l_tail * 0.45 - 0.15)
    draw_sphere(p_tail_node, 0.055 * scale, c_nodes)


# ==============================================================================
# PART 5: C++ MAPPING & MEMORY LAYOUT (Zero "Pythonic Magic")
# ==============================================================================
# In C++ (raylib.h), this procedural model requires zero dynamic memory allocation:
#
# struct SandWyrmPalette {
#     Color crystal_shell;
#     Color body_core;
#     Color jaw_edge;
#     Color glow_nodes;
#     Color sand_dust;
# };
#
# static const SandWyrmPalette DEFAULT_SAND_WYRM_PALETTE = {
#     (Color){225, 175, 75, 255},
#     (Color){45, 40, 42, 255},
#     (Color){180, 160, 140, 255},
#     (Color){0, 220, 210, 255},
#     (Color){210, 190, 140, 255}
# };
#
# void DrawSandWyrm3D(Vector3 position, float rotation_y, float anim_timer, float scale,
#                     const SandWyrmPalette* palette, bool show_wireframe);
#
# Memory Layout & Performance Notes:
# - Zero heap allocations: all coordinates and kinematic wave joints are computed on the CPU stack.
# - Immediate GPU buffers: primitives map directly to DrawCube, DrawSphere, DrawCylinderEx, and rlPushMatrix/rlPopMatrix.
# - C++ Transferability: Replace math.sin/cos with sinf/cosf from <math.h>. Replace Vector3 with raylib::Vector3.


# ==============================================================================
# PART 6: STANDALONE 3D ORBIT VIEWER (ModelViewerApp)
# ==============================================================================
class ModelViewerApp:
    """
    Interactive 3D previewer allowing inspection, rotation, zooming,
    wireframe toggling, palette swapping, and automated 3-frame smoke testing.
    """
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        init_window(self.screen_width, self.screen_height, "3D Model Inspector - Crystalline Sand Wyrm")
        set_target_fps(60)

        # 3D Orbit Camera Setup (Positioned to frame 4.8m wyrm length)
        self.camera = Camera3D(
            Vector3(0.0, 3.8, 6.8),   # Position
            Vector3(0.0, 0.8, -1.8),  # Target (wyrm center)
            Vector3(0.0, 1.0, 0.0),   # Up vector
            45.0,                     # FOV
            CAMERA_PERSPECTIVE
        )

        self.anim_timer = 0.0
        self.anim_playing = True
        self.rotation_y = 35.0
        self.show_wireframe = False
        self.active_palette_idx = 0
        self.palettes = [DEFAULT_SAND_WYRM_PALETTE, OBSIDIAN_WYRM_PALETTE]
        self.palette_names = ["Quartz Amber", "Void Obsidian"]

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

        # Toggle Wireframe Overlay
        if is_key_pressed(KEY_W):
            self.show_wireframe = not self.show_wireframe

        # Reset View
        if is_key_pressed(KEY_R):
            self.rotation_y = 35.0
            self.camera.position = Vector3(0.0, 3.8, 6.8)

        # Zoom via Mouse Wheel
        wheel = get_mouse_wheel_move()
        if wheel != 0.0:
            cam_dist = math.sqrt(self.camera.position.x**2 + (self.camera.position.z - (-1.8))**2)
            cam_dist = max(3.0, min(15.0, cam_dist - wheel * 0.8))
            self.camera.position.z = -1.8 + cam_dist

    def draw(self):
        begin_drawing()
        clear_background(Color(20, 24, 28, 255))

        # 3D Scene Rendering
        begin_mode_3d(self.camera)
        draw_grid(14, 1.0)
        draw_sand_wyrm_3d(
            Vector3(0.0, 0.0, 0.0),
            rotation_y=self.rotation_y,
            anim_timer=self.anim_timer,
            scale=1.0,
            palette=self.palettes[self.active_palette_idx],
            show_wireframe=self.show_wireframe
        )
        end_mode_3d()

        # HUD & Telemetry Overlay (Keeps x=450..980 clear for global bar)
        draw_text("3D MODEL INSPECTOR: Crystalline Sand Wyrm", 24, 20, 20, RAYWHITE)
        draw_text("[L-Drag / Left-Right] Rotate | [Space] Play/Pause | [P] Cycle Palette | [W] Wireframe", 24, 52, 14, LIGHTGRAY)
        draw_text(f"Palette: {self.palette_names[self.active_palette_idx]}", 24, 76, 14, YELLOW)
        wire_status = "ON" if self.show_wireframe else "OFF"
        draw_text(f"Anim Timer: {self.anim_timer:.2f}s | Rotation: {self.rotation_y:.1f} deg | Wireframe: {wire_status}", 24, 98, 14, SKYBLUE)
        draw_text(f"Segments: {SEGMENT_COUNT} | Length: {TOTAL_LENGTH:.2f}m | Primitives: Prisms, Spheres, Cylinders", 24, 120, 14, GREEN)

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
