# -*- coding: utf-8 -*-
"""
Three-Headed Hydra Serpent - 3D Procedural Primitive Model
==========================================================
Category         : beast
Target File      : assets/models_3D/beast/hydra_serpent.py
Concept Name     : Three-Headed Hydra Serpent
Primitives Used  : Tapered Cylinders (helical base coil, segmented neck stalks, fangs),
                   Prisms/Cubes (viper head wedges, articulated lower jaws, dorsal crest spines),
                   Spheres (articulating neck vertebrae, jaw hinge pivots, venomous eye beads)
Animation Loop   : Asynchronous 3-neck weaving kinematics, snapping viper jaws,
                   flaring dorsal crest spines, heave breath on coiled foundation

Problem Solved:
  Eliminates bulky 3D mesh files (.obj/.fbx) and external texture dependencies by
  synthesizing a legendary mythic apex beast—a three-headed hydra serpent—purely from
  Raylib geometric primitives and trigonometric transforms in real time.

How the Procedural Articulation Works:
  - Ground anchor at (0, 0, 0); coiled body mass anchored from y=0 to y=0.50.
  - Coiled foundation wraps in a 1.6m diameter ring (BASE_COIL_RADIUS = 0.80) with
    heavy body thickness (BODY_THICKNESS = 0.40) and breathes with heave:
    y_heave = 0.04 * math.sin(anim_timer * 1.2).
  - Central trunk junction centered at (0, 0.45, 0) anchors 3 flexible neck stalks
    branching at x = -0.35, x = 0.0, and x = +0.35.
  - Each neck stalk (NECK_LENGTH = 1.10) consists of 5 articulated sleeve segments
    and 5 spherical vertebrae ball joints (r=0.11), hovering heads at nominal elevation y=1.40.
  - Three necks weave asynchronously via compound sinusoidal kinematics:
    neck_yaw = math.sin(anim_timer * 2.2 + neck_idx * 1.4) * 0.35
    neck_pitch = math.cos(anim_timer * 1.8 + neck_idx * 2.1) * 0.20
  - Viper maws snap open and closed in threatening predatory strikes:
    jaw_open = abs(math.sin(anim_timer * 3.0 + neck_idx * 0.8)) * 0.45 rad (clamped to JAW_ANGLE_MAX = 0.52).
  - Dorsal crest spines flare outwards during strikes, and open maws reveal gory crimson interiors.

C++ Raylib Equivalent:
  struct HydraSerpentPalette {
      Color scales_abyssal;
      Color underbelly_pale;
      Color maw_crimson;
      Color eye_venom;
      Color crest_toxic;
  };
  void DrawHydraSerpent3D(Vector3 position, float rotation_y, float anim_timer, float scale, const HydraSerpentPalette* palette, bool show_wireframe);
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
# const HydraSerpentPalette DEFAULT_HYDRA_PALETTE = { ... };

DEFAULT_HYDRA_PALETTE = {
    "scales_abyssal": Color(25, 75, 55, 255),      # Deep serpentine jade green
    "underbelly_pale": Color(210, 220, 160, 255),  # Creamy venomous yellow
    "maw_crimson": Color(185, 30, 45, 255),        # Gory carnivorous crimson
    "eye_venom": Color(245, 230, 40, 255),         # Phosphorescent toxic yellow
    "crest_toxic": Color(80, 215, 110, 255),       # Translucent bioluminescent lime
}

BLOOD_HYDRA_PALETTE = {
    "scales_abyssal": Color(70, 20, 25, 255),      # Abyssal blood scale
    "underbelly_pale": Color(200, 160, 150, 255),  # Pale sinew flesh
    "maw_crimson": Color(240, 40, 40, 255),        # Flaming gore crimson
    "eye_venom": Color(255, 140, 0, 255),          # Amber predator eye
    "crest_toxic": Color(160, 40, 70, 255),        # Coagulated spines
}

# Named geometric proportions (replaces magic numbers)
BASE_COIL_RADIUS = 0.80
BODY_THICKNESS = 0.40
NECK_LENGTH = 1.10
NECK_SEGMENTS = 5
HEAD_LENGTH = 0.38
JAW_ANGLE_MAX = 0.52

# Additional anatomical proportions
HEAD_WIDTH = 0.22
HEAD_HEIGHT = 0.16
SPINE_WIDTH = 0.06
SPINE_HEIGHT = 0.12
SPINE_LENGTH = 0.10
VERTEBRA_RADIUS = 0.11
EYE_RADIUS = 0.035
JAW_HINGE_RADIUS = 0.04
TRUNK_ELEVATION = 0.45
NOMINAL_HEAD_ELEVATION = 1.40

# Kinematics tuning constants
BREATH_SPEED = 1.2
NECK_YAW_SPEED = 2.2
NECK_PITCH_SPEED = 1.8
JAW_SNAP_SPEED = 3.0


# ==============================================================================
# PART 4: CANONICAL 3D PROCEDURAL DRAWING FUNCTION
# ==============================================================================
def draw_hydra_serpent_3d(
    position: Vector3,
    rotation_y: float = 0.0,
    anim_timer: float = 0.0,
    scale: float = 1.0,
    palette: dict = None,
    show_wireframe: bool = False
) -> None:
    """
    Renders an articulated 3D Three-Headed Hydra Serpent with asynchronous neck weaving,
    snapping fanged viper maws, flaring dorsal crests, and breathing serpentine foundation.
    Must be called between begin_mode_3d(camera) and end_mode_3d().

    Parameters:
      position       : World-space base root location (ground center anchor).
      rotation_y     : Heading angle in DEGREES around Y axis (0 deg = facing +Z).
      anim_timer     : Elapsed seconds driving weave kinematics, jaw strikes, and breath heave.
      scale          : Geometric scaling factor (1.0 = standard beast scale ~2.5m foundation).
      palette        : Optional dictionary or palette name overriding DEFAULT_HYDRA_PALETTE.
      show_wireframe : Boolean flag toggling primitive wireframe overlay.
    """
    # Palette resolution
    if isinstance(palette, str):
        pal = BLOOD_HYDRA_PALETTE if palette in ("blood", "blood_hydra") else DEFAULT_HYDRA_PALETTE
    elif palette is not None:
        pal = palette
    else:
        pal = DEFAULT_HYDRA_PALETTE

    c_scales = pal["scales_abyssal"]
    c_underbelly = pal["underbelly_pale"]
    c_maw = pal["maw_crimson"]
    c_eyes = pal["eye_venom"]
    c_crest = pal["crest_toxic"]

    # Subtle or prominent wireframe color
    wire_col = Color(180, 240, 200, 220) if pal == DEFAULT_HYDRA_PALETTE else Color(255, 180, 180, 220)

    # Base world transform
    rad_y = rotation_y * (math.pi / 180.0)
    cos_r = math.cos(rad_y)
    sin_r = math.sin(rad_y)

    bx = position.x
    by = position.y
    bz = position.z

    # Helper: rotate local model coordinates to world space
    def transform_pt(lx: float, ly: float, lz: float) -> Vector3:
        wx = bx + (lx * cos_r + lz * sin_r) * scale
        wy = by + ly * scale
        wz = bz + (-lx * sin_r + lz * cos_r) * scale
        return Vector3(wx, wy, wz)

    # --------------------------------------------------------------------------
    # 1. HEAVY HELICAL COILED SERPENTINE BASE RING
    # Wrapped in a 1.6m diameter foundation (radius 0.80) with heave breathing
    # --------------------------------------------------------------------------
    y_heave = 0.04 * math.sin(anim_timer * BREATH_SPEED)

    coil_steps = 12
    coil_nodes = []
    coil_radii = []

    for i in range(coil_steps + 1):
        u = i / float(coil_steps)
        phi = -0.5 * math.pi + u * (2.2 * math.pi)
        r_coil = BASE_COIL_RADIUS * (1.05 - 0.22 * u)
        node_x = r_coil * math.cos(phi)
        node_z = r_coil * math.sin(phi)
        node_y = 0.16 + 0.28 * u + (y_heave * u)
        t_rad = BODY_THICKNESS * (0.65 + 0.35 * u)

        coil_nodes.append((node_x, node_y, node_z))
        coil_radii.append(t_rad)

    # Render coiled foundation segments
    for i in range(coil_steps):
        p0 = coil_nodes[i]
        p1 = coil_nodes[i + 1]
        r0 = coil_radii[i]
        r1 = coil_radii[i + 1]

        pt_a = transform_pt(p0[0], p0[1], p0[2])
        pt_b = transform_pt(p1[0], p1[1], p1[2])

        draw_cylinder_ex(pt_a, pt_b, r0 * scale, r1 * scale, 8, c_scales)
        if show_wireframe:
            draw_cylinder_wires_ex(pt_a, pt_b, r0 * scale, r1 * scale, 8, wire_col)

        # Underbelly ventral highlight along inner rim of coil
        ub_a = transform_pt(p0[0] * 0.86, p0[1] - 0.05, p0[2] * 0.86)
        ub_b = transform_pt(p1[0] * 0.86, p1[1] - 0.05, p1[2] * 0.86)
        draw_cylinder_ex(ub_a, ub_b, (r0 * 0.45) * scale, (r1 * 0.45) * scale, 6, c_underbelly)

        # Vertebra node ball between coil sleeves
        draw_sphere(pt_b, r1 * scale, c_scales)
        if show_wireframe:
            draw_sphere_wires(pt_b, r1 * scale, 6, 6, wire_col)

    # Central Trunk Junction at (0, 0.45, 0)
    trunk_pt = transform_pt(0.0, TRUNK_ELEVATION + y_heave, 0.0)
    draw_sphere(trunk_pt, (BODY_THICKNESS * 0.95) * scale, c_scales)
    if show_wireframe:
        draw_sphere_wires(trunk_pt, (BODY_THICKNESS * 0.95) * scale, 8, 8, wire_col)

    # Ventral chest plate on trunk
    trunk_belly = transform_pt(0.0, TRUNK_ELEVATION - 0.08 + y_heave, 0.14)
    draw_sphere(trunk_belly, (BODY_THICKNESS * 0.65) * scale, c_underbelly)

    # --------------------------------------------------------------------------
    # 2. THREE ARTICULATED SEGMENTED NECK STALKS & VIPER HEADS
    # Branches at x = -0.35, x = 0.0, and x = +0.35
    # --------------------------------------------------------------------------
    neck_branch_configs = [
        # (neck_idx, base_x, base_z, base_yaw)
        (0, -0.35, -0.05, -0.32),  # Left neck
        (1,  0.00,  0.10,  0.00),  # Center neck
        (2,  0.35, -0.05,  0.32),  # Right neck
    ]

    seg_length = NECK_LENGTH / float(NECK_SEGMENTS)

    for neck_idx, base_x, base_z, base_yaw in neck_branch_configs:
        # Asynchronous serpentine kinematics
        neck_yaw = math.sin(anim_timer * NECK_YAW_SPEED + neck_idx * 1.4) * 0.35
        neck_pitch = math.cos(anim_timer * NECK_PITCH_SPEED + neck_idx * 2.1) * 0.20
        jaw_open = abs(math.sin(anim_timer * JAW_SNAP_SPEED + neck_idx * 0.8)) * 0.45
        if jaw_open > JAW_ANGLE_MAX:
            jaw_open = JAW_ANGLE_MAX

        # Flare factor for dorsal crest spines during strikes
        flare = (jaw_open / JAW_ANGLE_MAX) * 0.06

        cur_x = base_x
        cur_y = TRUNK_ELEVATION + y_heave
        cur_z = base_z

        cur_yaw_acc = base_yaw
        cur_pitch_acc = 1.34  # Nominal upright serpentine elevation (~77 degrees)

        # 5 Interconnected sleeve segments + 5 articulating ball joints per neck
        for seg in range(NECK_SEGMENTS):
            t_seg = (seg + 1.0) / float(NECK_SEGMENTS)
            cur_yaw_acc = base_yaw + neck_yaw * t_seg
            cur_pitch_acc = 1.34 + neck_pitch * t_seg - 0.10 * seg

            # Segment step vector
            dx = seg_length * math.sin(cur_yaw_acc) * math.cos(cur_pitch_acc)
            dy = seg_length * math.sin(cur_pitch_acc)
            dz = seg_length * math.cos(cur_yaw_acc) * math.cos(cur_pitch_acc)

            next_x = cur_x + dx
            next_y = cur_y + dy
            next_z = cur_z + dz

            joint_a = transform_pt(cur_x, cur_y, cur_z)
            joint_b = transform_pt(next_x, next_y, next_z)

            # Neck vertebra ball joint (15 total: 5 joints * 3 necks)
            draw_sphere(joint_a, VERTEBRA_RADIUS * scale, c_scales)
            if show_wireframe:
                draw_sphere_wires(joint_a, VERTEBRA_RADIUS * scale, 6, 6, wire_col)

            # Tapered sleeve cylinder (r=0.10 nominal)
            rad_start = 0.125 - 0.006 * seg
            rad_end = 0.125 - 0.006 * (seg + 1)
            draw_cylinder_ex(joint_a, joint_b, rad_start * scale, rad_end * scale, 8, c_scales)
            if show_wireframe:
                draw_cylinder_wires_ex(joint_a, joint_b, rad_start * scale, rad_end * scale, 8, wire_col)

            # Ventral throat stripe
            v_offset_z = 0.02 * math.cos(cur_yaw_acc)
            v_offset_x = 0.02 * math.sin(cur_yaw_acc)
            throat_a = transform_pt(cur_x + v_offset_x, cur_y - 0.015, cur_z + v_offset_z)
            throat_b = transform_pt(next_x + v_offset_x, next_y - 0.015, next_z + v_offset_z)
            draw_cylinder_ex(throat_a, throat_b, (rad_start * 0.45) * scale, (rad_end * 0.45) * scale, 6, c_underbelly)

            # Triangular dorsal crest spine (18 total: 6 spines * 3 necks)
            # Dorsal normal points backward and slightly upward
            dorsal_nx = -math.sin(cur_yaw_acc) * 0.12
            dorsal_ny = 0.05
            dorsal_nz = -math.cos(cur_yaw_acc) * 0.12

            spine_x = (cur_x + next_x) * 0.5 + dorsal_nx * (1.0 + flare * 2.5)
            spine_y = (cur_y + next_y) * 0.5 + dorsal_ny * (1.0 + flare * 2.5)
            spine_z = (cur_z + next_z) * 0.5 + dorsal_nz * (1.0 + flare * 2.5)

            spine_pt = transform_pt(spine_x, spine_y, spine_z)
            draw_cube(spine_pt, SPINE_WIDTH * scale, (SPINE_HEIGHT + flare) * scale, SPINE_LENGTH * scale, c_crest)
            if show_wireframe:
                draw_cube_wires(spine_pt, SPINE_WIDTH * scale, (SPINE_HEIGHT + flare) * scale, SPINE_LENGTH * scale, wire_col)

            cur_x = next_x
            cur_y = next_y
            cur_z = next_z

        # 6th dorsal crest spine at cranial nape
        nape_x = cur_x - math.sin(cur_yaw_acc) * 0.14 * (1.0 + flare * 2.5)
        nape_y = cur_y + 0.07 * (1.0 + flare * 2.5)
        nape_z = cur_z - math.cos(cur_yaw_acc) * 0.14 * (1.0 + flare * 2.5)
        nape_pt = transform_pt(nape_x, nape_y, nape_z)
        draw_cube(nape_pt, SPINE_WIDTH * scale, (SPINE_HEIGHT * 1.25 + flare) * scale, SPINE_LENGTH * scale, c_crest)
        if show_wireframe:
            draw_cube_wires(nape_pt, SPINE_WIDTH * scale, (SPINE_HEIGHT * 1.25 + flare) * scale, SPINE_LENGTH * scale, wire_col)

        # ----------------------------------------------------------------------
        # VIPER HEAD WEDGE, CRANIUM, MAW & FANGS
        # Nominal head elevation y=1.40
        # ----------------------------------------------------------------------
        head_yaw = cur_yaw_acc
        head_pitch = 0.12 + neck_pitch * 0.40

        # Construct orthonormal head orientation basis (F, U, R)
        f_x = math.sin(head_yaw) * math.cos(head_pitch)
        f_y = -math.sin(head_pitch)
        f_z = math.cos(head_yaw) * math.cos(head_pitch)

        # Right vector perpendicular to F and global Up
        r_x = -f_z
        r_y = 0.0
        r_z = f_x
        r_len = math.sqrt(r_x * r_x + r_z * r_z)
        if r_len > 0.0001:
            r_x /= r_len
            r_z /= r_len

        # Orthonormal Up vector: U = R x F
        u_x = -r_z * f_y
        u_y = r_z * f_x - r_x * f_z
        u_z = r_x * f_y

        # Helper: convert head-local (u, v, w) to transformed world coordinates
        def head_pt(lu: float, lv: float, lw: float) -> Vector3:
            gx = cur_x + lu * r_x + lv * u_x + lw * f_x
            gy = cur_y + lu * r_y + lv * u_y + lw * f_y
            gz = cur_z + lu * r_z + lv * u_z + lw * f_z
            return transform_pt(gx, gy, gz)

        # 1. Cranium & Upper Maxilla (0.22 x 0.16 x 0.38)
        cranium_center = head_pt(0.0, 0.05, HEAD_LENGTH * 0.5)
        draw_cube(cranium_center, HEAD_WIDTH * scale, HEAD_HEIGHT * scale, HEAD_LENGTH * scale, c_scales)
        if show_wireframe:
            draw_cube_wires(cranium_center, HEAD_WIDTH * scale, HEAD_HEIGHT * scale, HEAD_LENGTH * scale, wire_col)

        # Tapered Snout Wedge
        snout_center = head_pt(0.0, 0.02, HEAD_LENGTH + 0.07)
        draw_cube(snout_center, (HEAD_WIDTH * 0.65) * scale, (HEAD_HEIGHT * 0.65) * scale, 0.14 * scale, c_scales)
        if show_wireframe:
            draw_cube_wires(snout_center, (HEAD_WIDTH * 0.65) * scale, (HEAD_HEIGHT * 0.65) * scale, 0.14 * scale, wire_col)

        # 2. Jaw Hinge Pivot Nodes (6 total: 2 per head * 3 heads, r=0.04)
        hinge_lw = 0.06
        hinge_lv = -0.02
        hinge_lu = HEAD_WIDTH * 0.5 + 0.015

        hinge_l = head_pt(-hinge_lu, hinge_lv, hinge_lw)
        hinge_r = head_pt( hinge_lu, hinge_lv, hinge_lw)
        draw_sphere(hinge_l, JAW_HINGE_RADIUS * scale, c_underbelly)
        draw_sphere(hinge_r, JAW_HINGE_RADIUS * scale, c_underbelly)
        if show_wireframe:
            draw_sphere_wires(hinge_l, JAW_HINGE_RADIUS * scale, 6, 6, wire_col)
            draw_sphere_wires(hinge_r, JAW_HINGE_RADIUS * scale, 6, 6, wire_col)

        # 3. Articulated Lower Jaw Wedge (opens with jaw_open angle)
        # Hinged at (0, hinge_lv, hinge_lw), rotating down around R axis
        jaw_len = 0.34
        jaw_wid = 0.18
        jaw_hgt = 0.08
        jaw_lw = hinge_lw + math.cos(jaw_open) * (jaw_len * 0.5)
        jaw_lv = hinge_lv - math.sin(jaw_open) * (jaw_len * 0.5) - 0.03

        jaw_center = head_pt(0.0, jaw_lv, jaw_lw)
        draw_cube(jaw_center, jaw_wid * scale, jaw_hgt * scale, jaw_len * scale, c_underbelly)
        if show_wireframe:
            draw_cube_wires(jaw_center, jaw_wid * scale, jaw_hgt * scale, jaw_len * scale, wire_col)

        # 4. Carnivorous Crimson Maw Interior
        # Palate on upper maxilla
        palate_center = head_pt(0.0, -0.015, 0.20)
        draw_cube(palate_center, 0.15 * scale, 0.03 * scale, 0.24 * scale, c_maw)

        # Tongue / lower jaw bed opening with strike
        tongue_center = head_pt(0.0, jaw_lv + 0.035, jaw_lw)
        draw_cube(tongue_center, 0.13 * scale, 0.02 * scale, 0.22 * scale, c_maw)

        # 5. Twin Ivory Viper Fangs
        fang_col = Color(245, 245, 240, 255)
        for fang_sign in (-1.0, 1.0):
            fang_u = fang_sign * 0.065
            fang_root = head_pt(fang_u, -0.02, 0.26)
            fang_tip  = head_pt(fang_u, -0.15, 0.24)
            draw_cylinder_ex(fang_root, fang_tip, 0.022 * scale, 0.005 * scale, 6, fang_col)
            if show_wireframe:
                draw_cylinder_wires_ex(fang_root, fang_tip, 0.022 * scale, 0.005 * scale, 6, wire_col)

        # 6. Venomous Optical Sensory Beads (6 total: 2 per head * 3 heads, r=0.035)
        eye_lu = HEAD_WIDTH * 0.5 + 0.01
        eye_lv = 0.07
        eye_lw = 0.24

        eye_l = head_pt(-eye_lu, eye_lv, eye_lw)
        eye_r = head_pt( eye_lu, eye_lv, eye_lw)
        draw_sphere(eye_l, EYE_RADIUS * scale, c_eyes)
        draw_sphere(eye_r, EYE_RADIUS * scale, c_eyes)
        if show_wireframe:
            draw_sphere_wires(eye_l, EYE_RADIUS * scale, 6, 6, wire_col)
            draw_sphere_wires(eye_r, EYE_RADIUS * scale, 6, 6, wire_col)


# ==============================================================================
# PART 5: STANDALONE TURNTABLE WORKBENCH & SMOKE TEST
# ==============================================================================
class ModelViewerApp:
    """
    Interactive 3D Turntable Workbench for inspecting the Three-Headed Hydra Serpent.
    Features orbit controls, animation pause, palette toggle, wireframe toggle,
    and non-blocking 3-frame smoke testing.
    """
    def __init__(self):
        init_window(1280, 720, "3D Model Inspector - Three-Headed Hydra Serpent")
        set_target_fps(60)

        # 3D Turntable Camera
        self.camera = Camera3D()
        self.camera.position = Vector3(0.0, 2.2, 3.8)
        self.camera.target = Vector3(0.0, 1.0, 0.0)
        self.camera.up = Vector3(0.0, 1.0, 0.0)
        self.camera.fovy = 45.0
        self.camera.projection = CAMERA_PERSPECTIVE

        # State variables
        self.rotation_y = 20.0
        self.anim_timer = 0.0
        self.anim_playing = True
        self.show_wireframe = False
        self.active_palette_idx = 0

        self.palettes = [DEFAULT_HYDRA_PALETTE, BLOOD_HYDRA_PALETTE]
        self.palette_names = ["Abyssal Jade (Default)", "Blood Hydra"]

    def update(self):
        dt = min(get_frame_time(), 0.05)
        if self.anim_playing:
            self.anim_timer += dt

        # Orbit Controls: Drag mouse left-click or use arrow keys
        if is_mouse_button_down(MOUSE_BUTTON_LEFT):
            delta = get_mouse_delta()
            self.rotation_y += delta.x * 0.5
            self.camera.position.y = clamp(self.camera.position.y - delta.y * 0.01, 0.5, 4.5)

        if is_key_down(KEY_LEFT):
            self.rotation_y -= 60.0 * dt
        if is_key_down(KEY_RIGHT):
            self.rotation_y += 60.0 * dt
        if is_key_down(KEY_UP):
            self.camera.position.y = clamp(self.camera.position.y + 1.5 * dt, 0.5, 4.5)
        if is_key_down(KEY_DOWN):
            self.camera.position.y = clamp(self.camera.position.y - 1.5 * dt, 0.5, 4.5)

        # Toggle Animation Play/Pause
        if is_key_pressed(KEY_SPACE):
            self.anim_playing = not self.anim_playing

        # Cycle Palettes [P] or [1]
        if is_key_pressed(KEY_P) or is_key_pressed(KEY_ONE):
            self.active_palette_idx = (self.active_palette_idx + 1) % len(self.palettes)

        # Toggle Wireframe [W]
        if is_key_pressed(KEY_W):
            self.show_wireframe = not self.show_wireframe

        # Reset camera and timer [R]
        if is_key_pressed(KEY_R):
            self.rotation_y = 20.0
            self.anim_timer = 0.0
            self.camera.position = Vector3(0.0, 2.2, 3.8)

        # Zoom via Mouse Wheel
        wheel = get_mouse_wheel_move()
        if wheel != 0.0:
            cam_dist = math.sqrt(self.camera.position.x * self.camera.position.x + self.camera.position.z * self.camera.position.z)
            cam_dist = clamp(cam_dist - wheel * 0.6, 1.8, 8.0)
            self.camera.position.z = cam_dist

    def draw(self):
        begin_drawing()
        clear_background(Color(16, 20, 24, 255))

        # 3D Scene Rendering
        begin_mode_3d(self.camera)
        draw_grid(10, 1.0)
        draw_hydra_serpent_3d(
            Vector3(0.0, 0.0, 0.0),
            rotation_y=self.rotation_y,
            anim_timer=self.anim_timer,
            scale=1.0,
            palette=self.palettes[self.active_palette_idx],
            show_wireframe=self.show_wireframe
        )
        end_mode_3d()

        # HUD & Telemetry Overlay (Keeps x=450..980 clear for global bar)
        draw_text("3D MODEL INSPECTOR: Three-Headed Hydra Serpent", 24, 20, 20, RAYWHITE)
        draw_text("[L-Drag / Left-Right] Rotate | [Space] Play/Pause | [P] Cycle Palette | [W] Wireframe", 24, 52, 14, LIGHTGRAY)
        draw_text(f"Palette: {self.palette_names[self.active_palette_idx]} | Wireframe: {'ON' if self.show_wireframe else 'OFF'}", 24, 76, 14, YELLOW)
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
