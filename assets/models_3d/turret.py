# -*- coding: utf-8 -*-
"""
Procedural 3D Heavy Turret / Boss Model
----------------------------------------
Renders a stationary or boss turret built purely from primitives:
  - Base: Stepped concentric cylinders anchoring to ground
  - Pivot: Yaw/Pitch articulated gimbal joint
  - Cannons: Dual heavy rectangular and cylindrical barrels
  - Beacon: Rotating flashing dome sphere

Ideal for fortress defense, bullet hell minigames, and boss encounters.
"""

import math
from pyray import (
    Vector3, Color,
    rl_push_matrix, rl_pop_matrix, rl_translatef, rl_rotatef, rl_scalef,
    draw_cube, draw_cube_wires, draw_sphere, draw_cylinder
)

DEFAULT_TURRET_PALETTE = {
    "base": Color(50, 50, 55, 255),        # Heavy industrial dark gray
    "armor": Color(80, 85, 95, 255),       # Armor gunmetal
    "trim": Color(255, 170, 0, 255),       # Industrial hazard orange
    "barrel": Color(25, 25, 30, 255),      # Charcoal blackened steel
    "beacon": Color(255, 30, 30, 255)      # Flashing alarm red
}

def draw_turret_boss_3d(
    position: Vector3,
    yaw_deg: float = 0.0,
    pitch_deg: float = 0.0,
    anim_timer: float = 0.0,
    scale: float = 1.0,
    palette: dict = None
):
    """
    Renders an articulated 3D Heavy Turret.
    
    Parameters:
      position: Ground position
      yaw_deg: Horizontal swivel angle in degrees (around Y)
      pitch_deg: Elevation barrel pitch angle in degrees (around X)
      anim_timer: Animation time for warning beacon pulse
      scale: Overall size multiplier
      palette: Color scheme dictionary
    """
    p = palette or DEFAULT_TURRET_PALETTE
    beacon_pulse = abs(math.sin(anim_timer * 6.0))

    rl_push_matrix()
    rl_translatef(position.x, position.y, position.z)
    rl_scalef(scale, scale, scale)

    # =========================================================================
    # STATIC BASE (Concentric stepped cylinders)
    # =========================================================================
    # Ground Anchor Ring
    draw_cylinder(Vector3(0.0, 0.0, 0.0), 1.2, 1.3, 0.2, 16, p["base"])
    # Mid-Tier Ring
    draw_cylinder(Vector3(0.0, 0.2, 0.0), 0.9, 1.0, 0.25, 16, p["armor"])
    # Hazard Ring
    draw_cube(Vector3(0.0, 0.45, 0.0), 1.6, 0.08, 0.3, p["trim"])
    draw_cube(Vector3(0.0, 0.45, 0.0), 0.3, 0.08, 1.6, p["trim"])
    # Turret Bearing Collar
    draw_cylinder(Vector3(0.0, 0.45, 0.0), 0.7, 0.75, 0.25, 16, p["base"])

    # =========================================================================
    # ROTATING YAW TURRET HOUSING
    # =========================================================================
    rl_push_matrix()
    rl_translatef(0.0, 0.70, 0.0)
    rl_rotatef(yaw_deg, 0.0, 1.0, 0.0)
    
    # Turret Core Body (Heavy Prism)
    draw_cube(Vector3(0.0, 0.35, 0.0), 1.1, 0.7, 1.3, p["armor"])
    draw_cube_wires(Vector3(0.0, 0.35, 0.0), 1.12, 0.72, 1.32, p["base"])

    # Top Warning Beacon
    draw_cylinder(Vector3(0.0, 0.70, 0.0), 0.20, 0.22, 0.15, 10, p["base"])
    beacon_color = Color(
        int(p["beacon"].r * (0.4 + 0.6 * beacon_pulse)),
        int(p["beacon"].g * (0.4 + 0.6 * beacon_pulse)),
        int(p["beacon"].b * (0.4 + 0.6 * beacon_pulse)),
        255
    )
    draw_sphere(Vector3(0.0, 0.88, 0.0), 0.16, beacon_color)

    # Rear Ammo Bunker / Cooling Vents
    draw_cube(Vector3(0.0, 0.35, -0.75), 0.8, 0.5, 0.4, p["base"])

    # =========================================================================
    # ELEVATING BARREL ASSEMBLY (Pitch articulation)
    # =========================================================================
    rl_push_matrix()
    rl_translatef(0.0, 0.35, 0.35)
    rl_rotatef(pitch_deg, 1.0, 0.0, 0.0)
    
    # Mantlet Pivot Cylinder
    draw_cylinder(Vector3(0.0, 0.0, 0.0), 0.35, 0.35, 0.35, 12, p["base"])
    
    # Twin Heavy Cannon Barrels (+Z forward)
    for bx in [-0.28, 0.28]:
        # Barrel Base Shroud (Prism)
        draw_cube(Vector3(bx, 0.0, 0.3), 0.22, 0.22, 0.6, p["armor"])
        # Main Barrel (Long Cylinder)
        draw_cylinder(Vector3(bx, 0.0, 0.6), 0.08, 0.08, 1.2, 8, p["barrel"])
        # Muzzle Brake (Wider tip)
        draw_cylinder(Vector3(bx, 0.0, 1.7), 0.12, 0.12, 0.2, 8, p["base"])

    rl_pop_matrix() # Pop Pitch

    rl_pop_matrix() # Pop Yaw

    rl_pop_matrix() # Pop Root

