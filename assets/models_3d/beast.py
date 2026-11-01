# -*- coding: utf-8 -*-
"""
Procedural 3D Quadruped Beast / Mecha Golem Model
--------------------------------------------------
Renders a quadruped monster built from geometric primitives:
  - Torso: Elongated rectangular prism and cylindrical armor plates
  - 4 Articulated Legs: Cylinders and sphere knee joints trotting rhythmically
  - Head: Heavy angular box with dual pointed horn prisms and glowing sphere eyes
  - Tail: Segmented swinging cylinders

Designed for Raylib Python with customizable scale and colors.
"""

import math
from pyray import (
    Vector3, Color,
    rl_push_matrix, rl_pop_matrix, rl_translatef, rl_rotatef, rl_scalef,
    draw_cube, draw_cube_wires, draw_sphere, draw_cylinder
)

DEFAULT_BEAST_PALETTE = {
    "body": Color(60, 45, 35, 255),       # Dark earthy chitin
    "plates": Color(100, 75, 55, 255),    # Carapace plates
    "joints": Color(35, 25, 20, 255),     # Dark biomech joints
    "horns": Color(210, 190, 160, 255),   # Bone ivory
    "eyes": Color(255, 60, 20, 255)       # Glowing orange/red eyes
}

def draw_quadruped_beast_3d(
    position: Vector3,
    rotation_y: float = 0.0,
    anim_timer: float = 0.0,
    scale: float = 1.0,
    palette: dict = None
):
    """
    Renders an articulated 4-legged beast enemy in 3D.
    """
    p = palette or DEFAULT_BEAST_PALETTE
    
    # Trotting gait animation
    trot_freq = anim_timer * 8.0
    leg_fl = math.sin(trot_freq) * 25.0
    leg_br = leg_fl
    leg_fr = -math.sin(trot_freq) * 25.0
    leg_bl = leg_fr
    
    body_bob = abs(math.sin(trot_freq)) * 0.08
    tail_swing = math.sin(anim_timer * 5.0) * 20.0

    rl_push_matrix()
    rl_translatef(position.x, position.y + body_bob, position.z)
    rl_rotatef(rotation_y, 0.0, 1.0, 0.0)
    rl_scalef(scale, scale, scale)

    # =========================================================================
    # MAIN BODY / CARAPACE (Height off ground ~ 0.8)
    # =========================================================================
    # Main Torso Prism
    draw_cube(Vector3(0.0, 0.85, 0.0), 0.9, 0.55, 1.6, p["body"])
    # Upper Armor Carapace
    draw_cube(Vector3(0.0, 1.15, -0.1), 0.95, 0.20, 1.4, p["plates"])
    draw_cube_wires(Vector3(0.0, 1.15, -0.1), 0.96, 0.21, 1.41, p["joints"])
    
    # Spine spikes (Series of small prisms)
    for z_off in [-0.5, -0.2, 0.1, 0.4]:
        draw_cube(Vector3(0.0, 1.30, z_off), 0.12, 0.20, 0.12, p["horns"])

    # =========================================================================
    # LEGS (Front at Z = 0.55, Back at Z = -0.55)
    # =========================================================================
    legs = [
        (-0.48, 0.55, leg_fl),  # Front-Left
        (0.48, 0.55, leg_fr),   # Front-Right
        (-0.48, -0.55, leg_bl), # Back-Left
        (0.48, -0.55, leg_br)   # Back-Right
    ]

    for lx, lz, angle in legs:
        rl_push_matrix()
        rl_translatef(lx, 0.80, lz)
        rl_rotatef(angle, 1.0, 0.0, 0.0)
        # Hip joint
        draw_sphere(Vector3(0.0, 0.0, 0.0), 0.14, p["joints"])
        # Upper Leg
        draw_cylinder(Vector3(0.0, -0.38, 0.0), 0.11, 0.09, 0.38, 8, p["body"])
        # Knee
        draw_sphere(Vector3(0.0, -0.38, 0.0), 0.10, p["joints"])
        # Lower Leg
        draw_cylinder(Vector3(0.0, -0.76, 0.0), 0.09, 0.07, 0.38, 8, p["plates"])
        # Paw / Claw
        draw_cube(Vector3(0.0, -0.78, 0.08), 0.16, 0.08, 0.22, p["horns"])
        rl_pop_matrix()

    # =========================================================================
    # HEAD & HORNS (At Z = 0.95)
    # =========================================================================
    head_bob = math.sin(trot_freq) * 4.0
    rl_push_matrix()
    rl_translatef(0.0, 0.92, 0.85)
    rl_rotatef(head_bob, 1.0, 0.0, 0.0)
    # Neck
    draw_cylinder(Vector3(0.0, 0.0, 0.0), 0.22, 0.24, 0.3, 8, p["joints"])
    # Head block
    draw_cube(Vector3(0.0, 0.15, 0.30), 0.65, 0.45, 0.60, p["body"])
    # Glowing Eyes
    draw_sphere(Vector3(-0.20, 0.22, 0.58), 0.08, p["eyes"])
    draw_sphere(Vector3(0.20, 0.22, 0.58), 0.08, p["eyes"])
    # Snout / Jaw
    draw_cube(Vector3(0.0, 0.02, 0.55), 0.45, 0.20, 0.40, p["plates"])
    # Horns (Ivory angled prisms)
    rl_push_matrix()
    rl_translatef(-0.30, 0.40, 0.20)
    rl_rotatef(-25.0, 0.0, 0.0, 1.0)
    draw_cube(Vector3(0.0, 0.15, 0.0), 0.08, 0.35, 0.08, p["horns"])
    rl_pop_matrix()
    
    rl_push_matrix()
    rl_translatef(0.30, 0.40, 0.20)
    rl_rotatef(25.0, 0.0, 0.0, 1.0)
    draw_cube(Vector3(0.0, 0.15, 0.0), 0.08, 0.35, 0.08, p["horns"])
    rl_pop_matrix()
    rl_pop_matrix()

    # =========================================================================
    # TAIL (At Z = -0.85)
    # =========================================================================
    rl_push_matrix()
    rl_translatef(0.0, 0.90, -0.85)
    rl_rotatef(tail_swing, 0.0, 1.0, 0.0)
    draw_cylinder(Vector3(0.0, -0.15, -0.30), 0.08, 0.05, 0.55, 6, p["body"])
    draw_sphere(Vector3(0.0, -0.20, -0.60), 0.12, p["horns"]) # Tail mace/ball
    rl_pop_matrix()

    rl_pop_matrix()

