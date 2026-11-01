# -*- coding: utf-8 -*-
"""
Procedural 2D Non-Humanoid Enemy Renderers
------------------------------------------
Provides procedural 2D enemy creatures drawn entirely with 2D primitive shapes:
  - Slime Enemy: Gelatinous squashing/stretching blob with shiny eyes and bubbles
  - Flying Drone/Bat: Floating mechanical eye with animated fluttering wings
  - Crawler/Spider: Multi-jointed arachnid with 6 animated walking legs

Completely self-contained, lightweight, and easy to use.
"""

import math
from pyray import (
    Vector2, Color,
    draw_circle, draw_circle_lines, draw_triangle, draw_line_ex,
    draw_rectangle_pro
)

# ==============================================================================
# SLIME / BLOB ENEMY
# ==============================================================================

DEFAULT_SLIME_PALETTE = {
    "body": Color(46, 204, 113, 230),     # Toxic translucent green
    "outline": Color(39, 174, 96, 255),   # Darker edge rim
    "highlight": Color(180, 255, 200, 220),# Specular bounce shine
    "eye": Color(255, 255, 255, 255),     # Eye white
    "pupil": Color(20, 20, 30, 255)       # Black pupil
}

def draw_slime_enemy_2d(
    position: Vector2,
    anim_timer: float = 0.0,
    radius: float = 24.0,
    palette: dict = None
):
    """
    Renders a squishy, bouncing 2D slime blob.
    Uses squash & stretch animation to give weight and life.
    """
    p = palette or DEFAULT_SLIME_PALETTE
    
    # Squash & stretch breathing cycle
    bounce = math.sin(anim_timer * 6.0)
    scale_x = 1.0 + 0.18 * bounce
    scale_y = 1.0 - 0.15 * bounce
    
    cx = position.x
    cy = position.y - (bounce * 4.0) # slight vertical hopping
    
    # Layered concentric circles to simulate an elastic droplet
    draw_circle(int(cx), int(cy), radius * ((scale_x + scale_y) * 0.5), p["body"])
    draw_circle_lines(int(cx), int(cy), radius * ((scale_x + scale_y) * 0.5), p["outline"])

    # Shiny specular bubble highlight (top-left)
    draw_circle(int(cx - radius * 0.35 * scale_x), int(cy - radius * 0.35 * scale_y), radius * 0.22, p["highlight"])
    draw_circle(int(cx - radius * 0.15 * scale_x), int(cy - radius * 0.50 * scale_y), radius * 0.10, p["highlight"])

    # Eyes (Left & Right)
    eye_offset_x = radius * 0.35 * scale_x
    eye_y = cy - radius * 0.1 * scale_y
    eye_r = radius * 0.22
    
    for side in [-1, 1]:
        ex = cx + side * eye_offset_x
        draw_circle(int(ex), int(eye_y), eye_r, p["eye"])
        # Dilating pupil
        draw_circle(int(ex + side * 1.5), int(eye_y + 1.0), eye_r * 0.55, p["pupil"])


# ==============================================================================
# FLYING SENTINEL / BAT ENEMY
# ==============================================================================

DEFAULT_FLYING_PALETTE = {
    "body": Color(70, 60, 90, 255),       # Deep shadow violet
    "wing": Color(140, 100, 180, 255),    # Vibrant purple wing
    "eye": Color(255, 40, 70, 255),       # Menacing red cyclops eye
    "pupil": Color(255, 200, 50, 255)     # Inner yellow slit
}

def draw_flying_drone_2d(
    position: Vector2,
    anim_timer: float = 0.0,
    radius: float = 18.0,
    palette: dict = None
):
    """
    Renders an aerial fluttering enemy with flapping triangular wings and glowing eye.
    """
    p = palette or DEFAULT_FLYING_PALETTE
    
    # Wing flap frequency and body levitation
    flap = math.sin(anim_timer * 14.0) * 16.0
    levitate = math.cos(anim_timer * 4.0) * 5.0
    
    cx = position.x
    cy = position.y + levitate

    # Left & Right Flapping Wings (Triangles)
    # Left Wing
    v1_l = Vector2(cx - radius * 0.6, cy)
    v2_l = Vector2(cx - radius * 2.2, cy - radius * 0.4 + flap)
    v3_l = Vector2(cx - radius * 1.6, cy + radius * 0.8 + flap * 0.5)
    draw_triangle(v1_l, v2_l, v3_l, p["wing"])

    # Right Wing
    v1_r = Vector2(cx + radius * 0.6, cy)
    v2_r = Vector2(cx + radius * 1.6, cy + radius * 0.8 + flap * 0.5)
    v3_r = Vector2(cx + radius * 2.2, cy - radius * 0.4 + flap)
    draw_triangle(v1_r, v2_r, v3_r, p["wing"])

    # Central Sphere / Body
    draw_circle(int(cx), int(cy), radius, p["body"])
    
    # Cyclops Eye
    draw_circle(int(cx), int(cy), radius * 0.55, p["eye"])
    draw_circle(int(cx), int(cy), radius * 0.25, p["pupil"])


# ==============================================================================
# ARACHNID / CRAWLER ENEMY
# ==============================================================================

DEFAULT_CRAWLER_PALETTE = {
    "carapace": Color(40, 40, 45, 255),   # Obsidian carapace
    "head": Color(65, 65, 75, 255),       # Chitin head
    "legs": Color(200, 50, 50, 255),      # Blood red legs
    "eyes": Color(255, 200, 0, 255)       # Cluster of yellow eyes
}

def draw_crawler_enemy_2d(
    position: Vector2,
    facing_angle_rad: float = 0.0,
    anim_timer: float = 0.0,
    radius: float = 16.0,
    palette: dict = None
):
    """
    Renders a multi-legged crawling insect/spider with animated articulated legs.
    """
    p = palette or DEFAULT_CRAWLER_PALETTE
    
    cos_a = math.cos(facing_angle_rad)
    sin_a = math.sin(facing_angle_rad)
    perp_x = -sin_a
    perp_y = cos_a
    
    cx, cy = position.x, position.y

    # =========================================================================
    # 6 ARTICULATED WALKING LEGS (3 on left, 3 on right)
    # =========================================================================
    leg_offsets = [-0.5, 0.0, 0.5] # Rear, middle, front along body axis
    for i, longitudinal in enumerate(leg_offsets):
        # Phase shift between legs for a convincing wave gait
        phase = anim_timer * 12.0 + i * 1.5
        leg_step = math.sin(phase) * 8.0
        
        for side in [-1, 1]:
            root = Vector2(
                cx + (cos_a * longitudinal * radius * 1.2) + (perp_x * side * radius * 0.8),
                cy + (sin_a * longitudinal * radius * 1.2) + (perp_y * side * radius * 0.8)
            )
            # Knee joint (bending out and up)
            knee = Vector2(
                root.x + perp_x * side * (radius * 1.4) + cos_a * leg_step,
                root.y + perp_y * side * (radius * 1.4) + sin_a * leg_step
            )
            # Foot tip (touching ground)
            foot = Vector2(
                knee.x + perp_x * side * (radius * 0.6) - cos_a * (leg_step * 0.5),
                knee.y + perp_y * side * (radius * 0.6) - sin_a * (leg_step * 0.5)
            )
            draw_line_ex(root, knee, 3.0, p["legs"])
            draw_line_ex(knee, foot, 2.2, p["legs"])
            draw_circle(int(foot.x), int(foot.y), 2.5, p["legs"])

    # =========================================================================
    # ABDOMEN & CEPHALOTHORAX (Carapace)
    # =========================================================================
    # Abdomen (Rear)
    ab_x = cx - cos_a * radius * 0.6
    ab_y = cy - sin_a * radius * 0.6
    draw_circle(int(ab_x), int(ab_y), radius * 1.1, p["carapace"])
    
    # Head (Front)
    head_x = cx + cos_a * radius * 0.7
    head_y = cy + sin_a * radius * 0.7
    draw_circle(int(head_x), int(head_y), radius * 0.75, p["head"])

    # Cluster of multiple glowing spider eyes
    for eye_ang in [-0.25, 0.0, 0.25]:
        ex = head_x + math.cos(facing_angle_rad + eye_ang) * (radius * 0.6)
        ey = head_y + math.sin(facing_angle_rad + eye_ang) * (radius * 0.6)
        draw_circle(int(ex), int(ey), 2.2, p["eyes"])

