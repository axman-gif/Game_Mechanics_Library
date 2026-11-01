# -*- coding: utf-8 -*-
"""
Procedural 3D Humanoid Enemy Model
-----------------------------------
Renders an articulated humanoid enemy built purely from 3D geometric primitives:
  - Head: Sphere with rectangular glowing visor
  - Torso: Rectangular prisms (chest and abdomen)
  - Joints (shoulders, elbows, knees): Spheres
  - Limbs (arms and legs): Cylinders and prisms
  - Weapon: Long cylinder staff with a glowing energy sphere tip

Includes natural walking/idle animation controlled by a single anim_timer parameter.
"""

import math
from pyray import (
    Vector3, Color,
    rl_push_matrix, rl_pop_matrix, rl_translatef, rl_rotatef, rl_scalef,
    draw_cube, draw_cube_wires, draw_sphere, draw_sphere_wires, draw_cylinder
)

# Default Sci-Fi / Cyber Humanoid Palette
DEFAULT_PALETTE = {
    "armor": Color(45, 52, 71, 255),       # Deep steel blue
    "chest": Color(85, 95, 120, 255),     # Lighter armor plate
    "joints": Color(30, 30, 35, 255),     # Dark carbon joint
    "visor": Color(255, 50, 80, 255),      # Glowing crimson visor
    "weapon": Color(180, 190, 205, 255),  # Metallic silver
    "energy": Color(255, 180, 0, 255)     # Glowing energy tip
}

def draw_humanoid_enemy_3d(
    position: Vector3,
    rotation_y: float = 0.0,
    anim_timer: float = 0.0,
    scale: float = 1.0,
    is_attacking: bool = False,
    palette: dict = None
):
    """
    Renders an articulated 3D humanoid enemy using primitive shapes.
    
    Parameters:
      position: Vector3 world position (feet level on ground)
      rotation_y: Facing direction in degrees (0 = facing forward +Z)
      anim_timer: Elapsed time in seconds used for procedural walking/breathing cycles
      scale: Overall scale multiplier (1.0 = standard 2.0 unit tall humanoid)
      is_attacking: If True, raises weapon in attack stance
      palette: Optional dict of Colors overriding DEFAULT_PALETTE
    """
    p = palette or DEFAULT_PALETTE
    
    # Procedural motion cycles
    walk_swing = math.sin(anim_timer * 6.0) * 28.0  # Leg/arm swing in degrees
    bob = abs(math.sin(anim_timer * 6.0)) * 0.1     # Footstep vertical bounce
    breath = math.sin(anim_timer * 2.5) * 0.03       # Chest breathing expansion

    rl_push_matrix()
    
    # 1. Translate to base position and apply facing rotation
    rl_translatef(position.x, position.y + bob, position.z)
    rl_rotatef(rotation_y, 0.0, 1.0, 0.0)
    rl_scalef(scale, scale, scale)
    
    # =========================================================================
    # LEGS (Pelvis at Y = 0.95)
    # =========================================================================
    leg_l_angle = walk_swing
    leg_r_angle = -walk_swing
    
    # Left Leg
    rl_push_matrix()
    rl_translatef(-0.25, 0.95, 0.0)
    rl_rotatef(leg_l_angle, 1.0, 0.0, 0.0)
    draw_sphere(Vector3(0.0, 0.0, 0.0), 0.12, p["joints"])
    draw_cylinder(Vector3(0.0, -0.45, 0.0), 0.10, 0.08, 0.45, 8, p["armor"]) # Thigh
    draw_sphere(Vector3(0.0, -0.45, 0.0), 0.10, p["joints"])                  # Knee
    draw_cylinder(Vector3(0.0, -0.90, 0.0), 0.08, 0.09, 0.45, 8, p["armor"]) # Shin
    draw_cube(Vector3(0.0, -0.92, 0.08), 0.18, 0.08, 0.28, p["joints"])      # Foot
    rl_pop_matrix()
    
    # Right Leg
    rl_push_matrix()
    rl_translatef(0.25, 0.95, 0.0)
    rl_rotatef(leg_r_angle, 1.0, 0.0, 0.0)
    draw_sphere(Vector3(0.0, 0.0, 0.0), 0.12, p["joints"])
    draw_cylinder(Vector3(0.0, -0.45, 0.0), 0.10, 0.08, 0.45, 8, p["armor"])
    draw_sphere(Vector3(0.0, -0.45, 0.0), 0.10, p["joints"])
    draw_cylinder(Vector3(0.0, -0.90, 0.0), 0.08, 0.09, 0.45, 8, p["armor"])
    draw_cube(Vector3(0.0, -0.92, 0.08), 0.18, 0.08, 0.28, p["joints"])
    rl_pop_matrix()

    # =========================================================================
    # PELVIS & TORSO
    # =========================================================================
    # Pelvis
    draw_cube(Vector3(0.0, 1.05, 0.0), 0.65, 0.22, 0.35, p["joints"])
    
    # Lower Abdomen
    draw_cylinder(Vector3(0.0, 1.15, 0.0), 0.22, 0.25, 0.25, 10, p["joints"])
    
    # Chest Armor (Prism/Box)
    chest_scale = 1.0 + breath
    draw_cube(Vector3(0.0, 1.48, 0.0), 0.75 * chest_scale, 0.48, 0.42 * chest_scale, p["chest"])
    draw_cube_wires(Vector3(0.0, 1.48, 0.0), 0.76 * chest_scale, 0.49, 0.43 * chest_scale, p["joints"])
    
    # Glowing Chest Core
    draw_sphere(Vector3(0.0, 1.50, 0.22), 0.08, p["visor"])

    # =========================================================================
    # HEAD & VISOR
    # =========================================================================
    # Neck
    draw_cylinder(Vector3(0.0, 1.72, 0.0), 0.12, 0.12, 0.15, 8, p["joints"])
    
    # Head (Sphere)
    draw_sphere(Vector3(0.0, 1.95, 0.0), 0.26, p["armor"])
    
    # Glowing Cyber Visor (Rectangular prism on front of face)
    draw_cube(Vector3(0.0, 1.96, 0.22), 0.34, 0.10, 0.12, p["visor"])

    # =========================================================================
    # ARMS & WEAPON
    # =========================================================================
    arm_l_angle = -walk_swing * 0.8
    arm_r_angle = (walk_swing * 0.8) if not is_attacking else -65.0
    
    # Left Arm
    rl_push_matrix()
    rl_translatef(-0.46, 1.62, 0.0)
    rl_rotatef(arm_l_angle, 1.0, 0.0, 0.0)
    draw_sphere(Vector3(0.0, 0.0, 0.0), 0.12, p["joints"])                    # Shoulder
    draw_cylinder(Vector3(0.0, -0.32, 0.0), 0.08, 0.08, 0.32, 8, p["armor"]) # Bicep
    draw_sphere(Vector3(0.0, -0.32, 0.0), 0.09, p["joints"])                  # Elbow
    draw_cylinder(Vector3(0.0, -0.62, 0.0), 0.08, 0.07, 0.30, 8, p["armor"]) # Forearm
    draw_sphere(Vector3(0.0, -0.66, 0.0), 0.08, p["joints"])                  # Hand
    rl_pop_matrix()

    # Right Arm + Weapon
    rl_push_matrix()
    rl_translatef(0.46, 1.62, 0.0)
    rl_rotatef(arm_r_angle, 1.0, 0.0, 0.0)
    draw_sphere(Vector3(0.0, 0.0, 0.0), 0.12, p["joints"])
    draw_cylinder(Vector3(0.0, -0.32, 0.0), 0.08, 0.08, 0.32, 8, p["armor"])
    draw_sphere(Vector3(0.0, -0.32, 0.0), 0.09, p["joints"])
    draw_cylinder(Vector3(0.0, -0.62, 0.0), 0.08, 0.07, 0.30, 8, p["armor"])
    draw_sphere(Vector3(0.0, -0.66, 0.0), 0.08, p["joints"])
    
    # Weapon: Energy Halberd / Staff
    rl_push_matrix()
    rl_translatef(0.0, -0.66, 0.0)
    rl_rotatef(15.0 if not is_attacking else 45.0, 1.0, 0.0, 0.0)
    # Staff pole (Cylinder)
    draw_cylinder(Vector3(0.0, -0.4, 0.0), 0.03, 0.03, 1.5, 6, p["weapon"])
    # Energy Sphere Head
    draw_sphere(Vector3(0.0, 1.15, 0.0), 0.16, p["energy"])
    # Blade Prism
    draw_cube(Vector3(0.0, 1.15, 0.18), 0.04, 0.40, 0.15, p["visor"])
    rl_pop_matrix()
    
    rl_pop_matrix()

    rl_pop_matrix()

