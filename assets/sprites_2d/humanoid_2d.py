# -*- coding: utf-8 -*-
"""
Procedural 2D Humanoid Enemy Renderer
-------------------------------------
Renders a stylized 2D humanoid enemy using Raylib 2D primitive shapes:
  - Head: Circle with glowing slit visor
  - Torso: Angled rectangle and armor plate
  - Limbs: Articulated jointed lines/capsules with walking swing
  - Weapon: Angled blade / blaster

Provides complete directional rotation and smooth procedural animation.
"""

import math
from pyray import (
    Vector2, Color,
    draw_circle, draw_circle_lines, draw_rectangle, draw_rectangle_pro,
    draw_line_ex, draw_triangle
)

DEFAULT_HUMANOID_2D_PALETTE = {
    "armor": Color(45, 52, 71, 255),       # Deep navy steel
    "accent": Color(255, 60, 60, 255),     # Glowing red visor
    "skin": Color(220, 180, 150, 255),     # Warm neutral
    "weapon": Color(190, 200, 215, 255),   # Steel silver
    "joint": Color(25, 25, 30, 255)        # Dark carbon
}

def draw_humanoid_enemy_2d(
    position: Vector2,
    facing_angle_rad: float = 0.0,
    anim_timer: float = 0.0,
    scale: float = 1.0,
    is_attacking: bool = False,
    palette: dict = None
):
    """
    Renders an articulated 2D humanoid enemy with top-down or side facing angle.
    
    Parameters:
      position: Center Vector2 position on screen
      facing_angle_rad: Rotation angle in radians (0 = facing Right)
      anim_timer: Elapsed time in seconds for walking animation
      scale: Size multiplier (1.0 = approx 40px tall)
      is_attacking: Triggers a forward weapon thrust
      palette: Optional color scheme dictionary
    """
    p = palette or DEFAULT_HUMANOID_2D_PALETTE
    
    cos_a = math.cos(facing_angle_rad)
    sin_a = math.sin(facing_angle_rad)
    
    # Perpendicular unit vector (left of forward direction)
    perp_x = -sin_a
    perp_y = cos_a
    
    # Procedural swing for walking
    walk_swing = math.sin(anim_timer * 10.0) * 12.0 * scale
    attack_thrust = 14.0 * scale if is_attacking else 0.0

    cx, cy = position.x, position.y

    # =========================================================================
    # FEET / LEGS (Drawn behind body)
    # =========================================================================
    left_foot = Vector2(
        cx + perp_x * 8.0 * scale + cos_a * (-walk_swing),
        cy + perp_y * 8.0 * scale + sin_a * (-walk_swing)
    )
    right_foot = Vector2(
        cx - perp_x * 8.0 * scale + cos_a * walk_swing,
        cy - perp_y * 8.0 * scale + sin_a * walk_swing
    )
    draw_circle(int(left_foot.x), int(left_foot.y), 5.0 * scale, p["joint"])
    draw_circle(int(right_foot.x), int(right_foot.y), 5.0 * scale, p["joint"])

    # =========================================================================
    # TORSO & SHOULDERS
    # =========================================================================
    draw_circle(int(cx), int(cy), 12.0 * scale, p["armor"])
    draw_circle_lines(int(cx), int(cy), 12.0 * scale, p["joint"])

    # Shoulder Pauldrons
    s_left = Vector2(cx + perp_x * 12.0 * scale, cy + perp_y * 12.0 * scale)
    s_right = Vector2(cx - perp_x * 12.0 * scale, cy - perp_y * 12.0 * scale)
    draw_circle(int(s_left.x), int(s_left.y), 6.0 * scale, p["armor"])
    draw_circle(int(s_right.x), int(s_right.y), 6.0 * scale, p["armor"])

    # =========================================================================
    # HEAD & VISOR
    # =========================================================================
    head_x = cx + cos_a * 4.0 * scale
    head_y = cy + sin_a * 4.0 * scale
    draw_circle(int(head_x), int(head_y), 8.5 * scale, p["skin"])
    
    # Glowing Cyber Visor Slit
    visor_start = Vector2(head_x + cos_a * 4.0 * scale - perp_x * 5.0 * scale,
                          head_y + sin_a * 4.0 * scale - perp_y * 5.0 * scale)
    visor_end = Vector2(head_x + cos_a * 4.0 * scale + perp_x * 5.0 * scale,
                        head_y + sin_a * 4.0 * scale + perp_y * 5.0 * scale)
    draw_line_ex(visor_start, visor_end, 3.5 * scale, p["accent"])

    # =========================================================================
    # WEAPON / BLADE (Held by right hand)
    # =========================================================================
    hand_pos = Vector2(
        cx - perp_x * 14.0 * scale + cos_a * (8.0 * scale + attack_thrust),
        cy - perp_y * 14.0 * scale + sin_a * (8.0 * scale + attack_thrust)
    )
    draw_circle(int(hand_pos.x), int(hand_pos.y), 4.5 * scale, p["joint"])
    
    # Sword blade pointing forward
    blade_tip = Vector2(
        hand_pos.x + cos_a * 22.0 * scale,
        hand_pos.y + sin_a * 22.0 * scale
    )
    draw_line_ex(hand_pos, blade_tip, 4.0 * scale, p["weapon"])
    draw_circle(int(blade_tip.x), int(blade_tip.y), 2.5 * scale, p["accent"])

