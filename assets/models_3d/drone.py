# -*- coding: utf-8 -*-
"""
Procedural 3D Floating Drone / Sentinel Model
----------------------------------------------
Renders a flying sci-fi drone composed of primitives:
  - Core: High-tech sphere with glowing eye sensor
  - Wings: 4 symmetrical hovering rectangular fins / thrusters
  - Weapon: Underside rotary laser cylinder
  - Propulsion: Pulsing energy rings

Features floating levitation and thruster bobbing animation.
"""

import math
from pyray import (
    Vector3, Color,
    rl_push_matrix, rl_pop_matrix, rl_translatef, rl_rotatef, rl_scalef,
    draw_cube, draw_cube_wires, draw_sphere, draw_cylinder
)

DEFAULT_DRONE_PALETTE = {
    "hull": Color(30, 35, 45, 255),       # Matte dark alloy
    "trim": Color(0, 168, 255, 255),      # Neon cyan energy
    "thruster": Color(70, 75, 85, 255),   # Engine metallic gray
    "core": Color(0, 240, 255, 255),      # Pulsing cyan core lens
    "laser": Color(255, 50, 50, 255)      # Red targeting beam diode
}

def draw_drone_enemy_3d(
    position: Vector3,
    rotation_y: float = 0.0,
    anim_timer: float = 0.0,
    scale: float = 1.0,
    palette: dict = None
):
    """
    Renders a hovering 3D sentinel drone enemy.
    """
    p = palette or DEFAULT_DRONE_PALETTE
    
    # Hovering levitation animation
    hover_bob = math.sin(anim_timer * 3.5) * 0.18
    hover_tilt = math.cos(anim_timer * 2.5) * 5.0
    pulse = 0.85 + 0.15 * math.sin(anim_timer * 8.0)

    rl_push_matrix()
    rl_translatef(position.x, position.y + hover_bob, position.z)
    rl_rotatef(rotation_y, 0.0, 1.0, 0.0)
    rl_rotatef(hover_tilt, 1.0, 0.0, 0.0)
    rl_scalef(scale, scale, scale)

    # =========================================================================
    # CENTRAL CORE SPHERE
    # =========================================================================
    # Outer armored sphere shell
    draw_sphere(Vector3(0.0, 0.0, 0.0), 0.45, p["hull"])
    
    # Glowing Cyclops Sensor / Eye in front (+Z)
    draw_sphere(Vector3(0.0, 0.0, 0.38), 0.18 * pulse, p["core"])
    draw_sphere(Vector3(0.0, 0.0, 0.44), 0.06, p["laser"])

    # Upper Sensor Dome (Cylinder & Sphere)
    draw_cylinder(Vector3(0.0, 0.35, 0.0), 0.20, 0.22, 0.18, 12, p["thruster"])
    draw_sphere(Vector3(0.0, 0.52, 0.0), 0.14, p["trim"])

    # =========================================================================
    # 4 HOVERING THRUSTER WINGS / FINS (Cross formation)
    # =========================================================================
    fin_angles = [0.0, 90.0, 180.0, 270.0]
    for angle in fin_angles:
        rl_push_matrix()
        rl_rotatef(angle, 0.0, 0.0, 1.0) # Rotate around Z axis to form X-wing
        
        # Wing Strut
        draw_cylinder(Vector3(0.35, 0.0, 0.0), 0.04, 0.04, 0.35, 6, p["thruster"])
        
        # Wing Fin (Rectangular Prism)
        draw_cube(Vector3(0.68, 0.0, 0.0), 0.32, 0.06, 0.55, p["hull"])
        draw_cube_wires(Vector3(0.68, 0.0, 0.0), 0.33, 0.07, 0.56, p["trim"])
        
        # Outer Glowing Energy Vent
        draw_cube(Vector3(0.85, 0.0, 0.0), 0.04, 0.04, 0.40, p["trim"])
        rl_pop_matrix()

    # =========================================================================
    # UNDERSIDE WEAPON POD
    # =========================================================================
    # Turret Mount (Cylinder hanging below)
    draw_cylinder(Vector3(0.0, -0.42, 0.0), 0.18, 0.15, 0.20, 10, p["thruster"])
    # Twin Laser Barrels (Small Cylinders pointing +Z)
    draw_cylinder(Vector3(-0.08, -0.48, 0.12), 0.03, 0.03, 0.35, 6, p["hull"])
    draw_cylinder(Vector3(0.08, -0.48, 0.12), 0.03, 0.03, 0.35, 6, p["hull"])

    rl_pop_matrix()

