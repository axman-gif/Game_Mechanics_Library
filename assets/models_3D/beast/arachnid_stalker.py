# -*- coding: utf-8 -*-
"""
Arachnid Stalker Drone - 3D Procedural Primitive Model
======================================================
Category         : beast
Target File      : assets/models_3D/beast/arachnid_stalker.py
Primitives Used  : Spheres (cephalothorax, opisthosoma abdomen, eye cluster), Cylinders (8 3-segment articulating spider legs, mandibles)
Animation Loop   : Alternating 8-legged quadruped-pair wave gait, chassis altitude stabilization, twitching chelicerae mandibles

Problem Solved:
  Eliminates bulky 3D mesh files (.obj/.fbx) and complex skeletal rigging rigs by
  synthesizing an 8-legged articulated arachnid predator purely from Raylib geometric
  primitives and trigonometric multi-segment inverse-kinematic chains in real time.

How the Procedural Articulation Works:
  - The model hierarchy is computed relative to a base 'position' (Vector3) at ground level.
  - 8 multi-jointed legs each contain 3 articulated segments: coxa (hip), femur (thigh), and tibia (needle talon).
  - Wave gait divides the 8 legs into two alternating sets of four (tetrad gait) with phase offsets:
    step_cycle = math.sin(anim_timer * 7.0 + leg_phase).
  - The coxa elevates with vertical lift while the tibia reaches out to plant on the ground plane.
  - Central cephalothorax and bulbous opisthosoma abdomen maintain high-clearance stabilization.
  - Six-eye ruby optical cluster and twin grasping chelicerae twitch aggressively.

C++ Raylib Equivalent:
  struct ArachnidPalette { Color hull; Color chitin; Color optics; Color leg_joints; Color mandibles; };
  void DrawArachnidStalker3D(Vector3 position, float rotation_y, float anim_timer, float scale, const ArachnidPalette* palette);
  Mapped directly to DrawCube, DrawSphere, and DrawCylinderEx from raylib.h.
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
# const ArachnidPalette DEFAULT_ARACHNID_PALETTE = { ... };

DEFAULT_ARACHNID_PALETTE = {
    "hull": Color(38, 42, 48, 255),          # Gloss dark chitin exoskeleton
    "chitin": Color(60, 68, 76, 255),        # Armored carapace dorsal slate
    "optics": Color(255, 20, 40, 255),       # Ruby red multi-eye optical cluster
    "leg_joints": Color(185, 145, 60, 255),  # Brass servo bearing knuckles
    "mandibles": Color(220, 230, 240, 255),  # Razor-sharp steel chelicerae fangs
}

CYBER_ARACHNID_PALETTE = {
    "hull": Color(20, 22, 26, 255),          # Matte tactical stealth black
    "chitin": Color(40, 44, 52, 255),        # High-modulus carbon fiber shell
    "optics": Color(0, 240, 255, 255),       # Electric cyan multi-spectral sensors
    "leg_joints": Color(70, 110, 190, 255),  # Anodized cobalt alloy servos
    "mandibles": Color(255, 200, 50, 255),   # Plasma-tempered titanium blades
}

# Named geometric proportions (replaces magic numbers)
BODY_SUSPENSION_HEIGHT = 0.55
CEPHALOTHORAX_RAD = 0.32
ABDOMEN_RAD_X = 0.45
ABDOMEN_RAD_Y = 0.38
ABDOMEN_RAD_Z = 0.60
ABDOMEN_OFFSET_Z = -0.45
ABDOMEN_ELEVATION = 0.62

COXA_LEN = 0.25
COXA_RAD = 0.06
FEMUR_LEN = 0.65
FEMUR_RAD = 0.05
TIBIA_LEN = 0.75
TIBIA_RAD = 0.04
JOINT_RAD = 0.07

CHELICERAE_LEN = 0.30
CHELICERAE_RAD = 0.05
EYE_RADIUS = 0.035

WAVE_GAIT_SPEED = 7.0
STABILIZATION_SPEED = 14.0


# ==============================================================================
# PART 4: CANONICAL 3D PROCEDURAL DRAWING FUNCTION
# ==============================================================================
def draw_arachnid_stalker_3d(
    position: Vector3,
    rotation_y: float = 0.0,
    anim_timer: float = 0.0,
    scale: float = 1.0,
    palette: dict = None
) -> None:
    """
    Renders an articulated 3D Arachnid Stalker Drone with procedural 8-legged wave gait,
    chassis stabilization damping, and twitching chelicerae mandibles.
    Must be called between begin_mode_3d(camera) and end_mode_3d().

    Parameters:
      position   : World-space base root location (ground level beneath central thorax).
      rotation_y : Heading angle in DEGREES around Y axis (0 deg = facing +Z).
      anim_timer : Elapsed seconds driving alternating tetrad stride, micro-bob, and fangs.
      scale      : Geometric scaling factor (1.0 = standard drone ~2.6m leg span).
      palette    : Optional dictionary overriding DEFAULT_ARACHNID_PALETTE colors.
    """
    pal = palette if palette is not None else DEFAULT_ARACHNID_PALETTE

    c_hull = pal["hull"]
    c_chitin = pal["chitin"]
    c_optics = pal["optics"]
    c_leg_joints = pal["leg_joints"]
    c_mandibles = pal["mandibles"]

    rad_y = rotation_y * (math.pi / 180.0)
    cos_r = math.cos(rad_y)
    sin_r = math.sin(rad_y)

    # Stabilized suspension micro-bob
    chassis_bob = 0.02 * math.cos(anim_timer * STABILIZATION_SPEED) * scale

    bx = position.x
    by = position.y + (BODY_SUSPENSION_HEIGHT * scale) + chassis_bob
    bz = position.z

    # Helper: rotate local model coordinates to world space
    def transform_pt(lx: float, ly: float, lz: float) -> Vector3:
        wx = bx + (lx * cos_r + lz * sin_r) * scale
        wy = by + ly * scale
        wz = bz + (-lx * sin_r + lz * cos_r) * scale
        return Vector3(wx, wy, wz)

    # 1. Flattened Armored Cephalothorax (Head / Front Thorax)
    ceph_pos = transform_pt(0.0, 0.0, 0.15)
    draw_sphere(ceph_pos, CEPHALOTHORAX_RAD * scale, c_chitin)
    # Dorsal armor plate crest on cephalothorax
    crest_pos = transform_pt(0.0, 0.12, 0.15)
    draw_cube(crest_pos, 0.38 * scale, 0.08 * scale, 0.40 * scale, c_hull)
    draw_cube_wires(crest_pos, 0.40 * scale, 0.09 * scale, 0.42 * scale, c_leg_joints)

    # 2. Six-Eye Ocular Optical Array (Ruby Sensor Cluster)
    eye_offsets = [
        (-0.10, 0.08, 0.38), (0.10, 0.08, 0.38),   # Central primary oculars
        (-0.18, 0.05, 0.34), (0.18, 0.05, 0.34),   # Lateral forward sensors
        (-0.22, 0.02, 0.28), (0.22, 0.02, 0.28),   # Peripheral horizon sensors
    ]
    for ex, ey, ez in eye_offsets:
        eye_pt = transform_pt(ex, ey, ez)
        draw_sphere(eye_pt, EYE_RADIUS * scale, c_optics)

    # 3. Twin Grasping Chelicerae Mandibles (Fangs that twitch and snap)
    mandible_twitch = 0.12 * math.sin(anim_timer * 8.0)
    for m_sign in (-1.0, 1.0):
        mx = m_sign * 0.10
        m_base = transform_pt(mx, -0.08, 0.38)
        # Articulated tip reaching forward and inward
        m_tip = transform_pt(
            mx + (m_sign * -0.04) + (m_sign * mandible_twitch * 0.03),
            -0.22,
            0.38 + CHELICERAE_LEN + (mandible_twitch * 0.04)
        )
        draw_cylinder_ex(m_base, m_tip, CHELICERAE_RAD * scale, 0.01 * scale, 6, c_mandibles)
        draw_sphere(m_base, (CHELICERAE_RAD * 1.1) * scale, c_leg_joints)

    # 4. Swollen Rear Opisthosoma Abdomen (trailing rear chassis)
    ab_pos = transform_pt(0.0, 0.07, ABDOMEN_OFFSET_Z)
    draw_sphere(ab_pos, ABDOMEN_RAD_X * scale, c_hull)

    # Segmented Chitin Ribs on Abdomen (4 dorsal rings)
    for r in range(4):
        rz = ABDOMEN_OFFSET_Z + 0.20 - (r * 0.15)
        ring_pos = transform_pt(0.0, 0.15, rz)
        draw_cube(ring_pos, (0.50 - r * 0.06) * scale, 0.04 * scale, 0.08 * scale, c_chitin)

    # Pedicel Waist Connector (Cylinder linking head and abdomen)
    ped_front = transform_pt(0.0, 0.0, 0.02)
    ped_back = transform_pt(0.0, 0.04, ABDOMEN_OFFSET_Z + 0.25)
    draw_cylinder_ex(ped_front, ped_back, 0.14 * scale, 0.12 * scale, 6, c_leg_joints)

    # 5. Eight Multi-Jointed Articulating Spider Legs (4 Left, 4 Right)
    # Legs: L1..L4, R1..R4 with alternating tetrad wave gait
    leg_coords = [
        # (side, index, base_lx, base_lz, angle_deg, phase)
        # Left side
        (-1.0, 1, -0.22,  0.22,  45.0,  0.0),
        (-1.0, 2, -0.25,  0.08,  80.0,  math.pi),
        (-1.0, 3, -0.25, -0.08, 110.0,  0.0),
        (-1.0, 4, -0.20, -0.22, 145.0,  math.pi),
        # Right side
        ( 1.0, 1,  0.22,  0.22, -45.0,  math.pi),
        ( 1.0, 2,  0.25,  0.08, -80.0,  0.0),
        ( 1.0, 3,  0.25, -0.08, -110.0, math.pi),
        ( 1.0, 4,  0.20, -0.22, -145.0, 0.0),
    ]

    for side, idx, lx, lz, base_angle_deg, phase in leg_coords:
        cycle = math.sin(anim_timer * WAVE_GAIT_SPEED + phase)

        # Dynamic leg swing and lift
        lift_y = 0.18 * max(0.0, cycle) * scale
        reach = 0.15 * cycle

        rad_leg = base_angle_deg * (math.pi / 180.0)
        cos_leg = math.cos(rad_leg)
        sin_leg = math.sin(rad_leg)

        # 1. Coxa (Root hip segment extending horizontally outwards)
        coxa_base = transform_pt(lx, -0.05, lz)
        draw_sphere(coxa_base, JOINT_RAD * scale, c_leg_joints)

        coxa_end_lx = lx + sin_leg * COXA_LEN
        coxa_end_lz = lz + cos_leg * COXA_LEN
        coxa_end_ly = -0.02 + (lift_y / scale) * 0.4
        coxa_end = transform_pt(coxa_end_lx, coxa_end_ly, coxa_end_lz)

        draw_cylinder_ex(coxa_base, coxa_end, COXA_RAD * scale, (COXA_RAD * 0.9) * scale, 5, c_chitin)
        draw_sphere(coxa_end, (JOINT_RAD * 0.9) * scale, c_leg_joints)

        # 2. Femur (Upper thigh segment arching sharply upwards & outwards)
        femur_elev = 0.32 + (lift_y / scale)
        femur_end_lx = coxa_end_lx + sin_leg * (FEMUR_LEN * 0.65)
        femur_end_lz = coxa_end_lz + cos_leg * (FEMUR_LEN * 0.65) + reach * 0.5
        femur_end_ly = coxa_end_ly + femur_elev
        femur_end = transform_pt(femur_end_lx, femur_end_ly, femur_end_lz)

        draw_cylinder_ex(coxa_end, femur_end, FEMUR_RAD * scale, (FEMUR_RAD * 0.8) * scale, 5, c_hull)
        draw_sphere(femur_end, (JOINT_RAD * 0.8) * scale, c_leg_joints)

        # 3. Tibia (Needle shin segment plunging downwards to the ground plane)
        # Target foot contact is pinned to the ground (wy = position.y)
        foot_lx = femur_end_lx + sin_leg * (TIBIA_LEN * 0.55)
        foot_lz = femur_end_lz + cos_leg * (TIBIA_LEN * 0.55) + reach
        foot_ly = -(BODY_SUSPENSION_HEIGHT + (chassis_bob / scale)) + (lift_y / scale) * 0.2
        foot_pt = transform_pt(foot_lx, foot_ly, foot_lz)

        draw_cylinder_ex(femur_end, foot_pt, TIBIA_RAD * scale, 0.012 * scale, 4, c_chitin)
        # Needle talon point
        draw_sphere(foot_pt, 0.02 * scale, c_mandibles)


# ==============================================================================
# PART 5: C++ MAPPING & MEMORY LAYOUT (Zero "Pythonic Magic")
# ==============================================================================
# In C++ (raylib.h), this procedural model requires zero dynamic memory allocation:
#
# struct ArachnidPalette {
#     Color hull;
#     Color chitin;
#     Color optics;
#     Color leg_joints;
#     Color mandibles;
# };
#
# static const ArachnidPalette DEFAULT_ARACHNID_PALETTE = {
#     (Color){38, 42, 48, 255},
#     (Color){60, 68, 76, 255},
#     (Color){255, 20, 40, 255},
#     (Color){185, 145, 60, 255},
#     (Color){220, 230, 240, 255}
# };
#
# void DrawArachnidStalker3D(Vector3 position, float rotation_y, float anim_timer, float scale, const ArachnidPalette* palette);
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
        init_window(self.screen_width, self.screen_height, "3D Model Inspector - Arachnid Stalker Drone")
        set_target_fps(60)

        # 3D Orbit Camera Setup
        self.camera = Camera3D(
            Vector3(0.0, 3.2, 5.2),   # Position
            Vector3(0.0, 0.6, 0.0),   # Target
            Vector3(0.0, 1.0, 0.0),   # Up vector
            45.0,                     # FOV
            CAMERA_PERSPECTIVE
        )

        self.anim_timer = 0.0
        self.anim_playing = True
        self.rotation_y = 40.0
        self.active_palette_idx = 0
        self.palettes = [DEFAULT_ARACHNID_PALETTE, CYBER_ARACHNID_PALETTE]
        self.palette_names = ["Abyssal Chitin", "Cyber Infiltrator"]

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
        clear_background(Color(18, 20, 24, 255))

        # 3D Scene Rendering
        begin_mode_3d(self.camera)
        draw_grid(10, 1.0)
        draw_arachnid_stalker_3d(
            Vector3(0.0, 0.0, 0.0),
            rotation_y=self.rotation_y,
            anim_timer=self.anim_timer,
            scale=1.0,
            palette=self.palettes[self.active_palette_idx]
        )
        end_mode_3d()

        # HUD & Telemetry Overlay (Keeps x=450..980 clear for global bar)
        draw_text("3D MODEL INSPECTOR: Arachnid Stalker Drone", 24, 20, 20, RAYWHITE)
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
