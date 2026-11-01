# -*- coding: utf-8 -*-
"""
Minimap & Compass - HUD Navigation Radar & Bearing Compass Tape
==============================================================
Section          : 3.1 Menus & UI
Pattern Category : Menus & User Interface, Presentation (Navigation HUD)
Dimension        : 3D

Problem Solved:
  In 3D games (RPGs, open worlds, action-adventures), restricted screen field-of-view
  (60°-90°) creates spatial disorientation and tunnel vision. Players lose track of
  where they are relative to distant landmarks, active mission objectives, and true
  cardinal directions. Furthermore, naive 2D overlays that do not handle coordinate
  transformations, heading rotations, or out-of-range edge-pinning result in blips
  vanishing off-screen or pointing in inverted, misleading directions when the camera turns.

How the Patterns Work:
  1. Coordinate Transformation Pipeline (World Space -> Radar Space):
     Calculates horizontal relative offset (dx = Mx - Px, dz = Mz - Pz).
     In Heading-Up Mode, rotates (dx, dz) by -cam_yaw using standard 2D rotation:
       rx = dx * cos(-yaw) - dz * sin(-yaw)
       ry = dx * sin(-yaw) + dz * cos(-yaw)
     In North-Up Mode, (rx, ry) = (dx, dz). Translates by radar center (Cx, Cy) scaled
     by (radar_radius / radar_range_units).
  2. Edge Pinning & Boundary Clamping:
     When target distance in radar pixels exceeds radar radius R, edge-pinning projects
     the blip onto the circular perimeter:
       clamped = center + (delta / length) * (R - margin)
     and draws an outward-pointing chevron arrow showing the exact direction to turn.
  3. Seamless Compass Strip / Heading Tape:
     Computes target true bearing beta = atan2(dx, -dz) and camera heading psi = atan2(fx, -fz).
     The angular difference delta = wrap_angle(beta - psi) maps onto a horizontal tape:
       screen_x = center_x + (delta / (fov / 2)) * (tape_width / 2)
     Smooth edge-fade alpha ensures markers and 360° cardinal ticks enter and exit elegantly.

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - [W][A][S][D] / Gamepad Left Stick     : Move character in camera-relative directions
  - Directional Arrows / Right Stick      : Rotate camera (Left/Right = Yaw, Up/Down = Pitch)
  - [Tab] / Gamepad View (Select)         : Toggle X-Ray Telemetry & Math Inspector Overlay
  - [F1]  / Gamepad LB                    : Toggle Minimap Mode: [Heading-Up (Rotating)] vs [North-Up (Fixed)]
  - [F2]  / Gamepad RB                    : Toggle Edge Pinning: [Edge Pinning ON (Clamp)] vs [OFF (Cull)]
  - [1] / [2] / [3] / Gamepad D-Pad       : Switch Radar Zoom Range (40m / 80m / 140m)
  - [Ctrl +/-]                            : Increase / Decrease UI Font Size
  - [F11]                                 : Toggle Fullscreen
  - [R]   / Gamepad Start                 : Reset simulation & spawn new objective sequence
"""

import sys
import os
import math
import random

# 1. Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# 2. Add repository root to search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 3. Mandatory Raylib & modular workspace imports
from pyray import *
from assets import *
from utils import *

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WINDOW_TITLE = "Minimap & Compass - HUD Navigation Systems (Raylib Pattern Lab)"

# Arena Palette
COLOR_GROUND_BASE      = Color(20, 24, 36, 255)
COLOR_GRID_PRIMARY     = Color(38, 48, 72, 255)
COLOR_GRID_ACCENT      = Color(65, 85, 125, 255)
COLOR_BOUNDARY_PYLON   = Color(255, 90, 40, 255)
COLOR_CARDINAL_TOWER   = Color(90, 160, 255, 255)

# HUD & Radar Palette
COLOR_RADAR_BG         = Color(10, 14, 24, 230)
COLOR_RADAR_RIM        = Color(60, 90, 140, 255)
COLOR_RADAR_RIM_GLOW   = Color(80, 170, 255, 80)
COLOR_RADAR_GRID       = Color(30, 50, 80, 180)
COLOR_RADAR_SWEEP      = Color(0, 230, 255, 35)
COLOR_FRUSTUM_CONE     = Color(0, 200, 255, 30)

COLOR_COMPASS_BG       = Color(12, 16, 28, 220)
COLOR_COMPASS_BORDER   = Color(50, 75, 115, 255)
COLOR_COMPASS_TICK     = Color(140, 170, 215, 255)
COLOR_COMPASS_NORTH    = Color(255, 70, 70, 255)
COLOR_COMPASS_TEXT     = Color(210, 230, 255, 255)
COLOR_COMPASS_RETICLE  = Color(255, 215, 0, 255)

# Marker Category Enums (C++ Enum equivalent)
MARKER_PRIMARY_BEACON  = 0
MARKER_COMMS_RELAY     = 1
MARKER_SUPPLY_CACHE    = 2
MARKER_PATROL_DRONE    = 3
MARKER_CARDINAL_TOWER  = 4

# Minimap Orientation Modes
MODE_HEADING_UP        = 0
MODE_NORTH_UP          = 1


# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATION (MINIMAP & COMPASS RADAR)
# ==============================================================================

class MapMarker:
    """
    Struct representing an interactive point-of-interest (POI) or entity
    registered in the world navigation system.
    
    C++ Equivalent:
      struct MapMarker {
          int id;
          Vector3 pos;
          char label[32];
          int marker_type;
          Color color;
          bool is_objective;
          bool active;
      };
    """
    def __init__(self, marker_id: int, pos: Vector3, label: str, marker_type: int, color: Color, is_objective: bool = False):
        self.id = marker_id
        self.pos = pos
        self.label = label
        self.marker_type = marker_type
        self.color = color
        self.is_objective = is_objective
        self.active = True
        self.pulse_timer = 0.0


def normalize_angle_rad(angle: float) -> float:
    """
    Wraps an arbitrary angle in radians to the canonical interval [-pi, +pi].
    Essential for compass difference calculation without multi-turn wrap glitches.
    C++ Equivalent:
      float normalize_angle_rad(float a) {
          return fmodf(a + PI, 2.0f * PI) - PI;
      }
    """
    two_pi = 2.0 * math.pi
    a = (angle + math.pi) % two_pi
    if a < 0.0:
        a += two_pi
    return a - math.pi


def compute_target_bearing_rad(from_x: float, from_z: float, to_x: float, to_z: float) -> float:
    """
    Computes standard navigational world bearing where:
      North (-Z) = 0 rad (0 deg)
      East  (+X) = +pi/2 rad (+90 deg)
      South (+Z) = pi rad (180 deg)
      West  (-X) = -pi/2 rad (-90 deg / 270 deg)
    
    Equation:
      dx = to_x - from_x
      dz = to_z - from_z
      bearing = atan2(dx, -dz)
    """
    dx = to_x - from_x
    dz = to_z - from_z
    return math.atan2(dx, -dz)


def compute_camera_heading_rad(cam_forward_x: float, cam_forward_z: float) -> float:
    """
    Computes camera view heading angle in navigation coordinates where North is 0 rad.
    cam_forward is the normalized horizontal look direction of the camera.
    """
    return math.atan2(cam_forward_x, -cam_forward_z)


class MinimapSystem:
    """
    Corner Minimap Radar implementing both Heading-Up (Rotating Map) and
    North-Up (Fixed Map) coordinate projections with edge-pinning clamping.
    """
    def __init__(self, center_x: int, center_y: int, radius: float):
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        self.radar_range = 80.0     # World distance units mapped to radar outer radius
        self.mode = MODE_HEADING_UP
        self.edge_pinning = True
        self.sweep_angle = 0.0

    def update(self, dt: float):
        # Update aesthetic radar sweep beam
        self.sweep_angle += 2.2 * dt
        if self.sweep_angle >= 2.0 * math.pi:
            self.sweep_angle -= 2.0 * math.pi

    def world_to_radar(self, marker_x: float, marker_z: float, player_x: float, player_z: float, cam_heading_rad: float):
        """
        Transforms 3D world coordinates (X, Z) into 2D Radar screen coordinates (screen_x, screen_y).
        
        Mathematical Pipeline:
          1. Delta in World Space:
               dx = marker_x - player_x
               dz = marker_z - player_z
          2. Orientation Transformation:
               If Heading-Up:
                 Rotate (dx, dz) by -cam_heading_rad so player's line-of-sight points straight UP.
                   rx = dx * cos(-heading) - dz * sin(-heading)
                   ry = dx * sin(-heading) + dz * cos(-heading)
               If North-Up:
                 rx = dx
                 ry = dz
          3. Scaling to Radar Pixels:
               scale = self.radius / self.radar_range
               px_x = rx * scale
               px_y = ry * scale
          4. Clamping / Edge Pinning:
               dist_px = sqrt(px_x^2 + px_y^2)
               If dist_px > (radius - margin):
                 if edge_pinning:
                   px_x = (px_x / dist_px) * (radius - margin)
                   px_y = (px_y / dist_px) * (radius - margin)
                   is_clamped = True
                 else:
                   is_visible = False
        """
        dx = marker_x - player_x
        dz = marker_z - player_z
        world_dist = math.sqrt(dx * dx + dz * dz)

        if self.mode == MODE_HEADING_UP:
            rot = -cam_heading_rad
            c = math.cos(rot)
            s = math.sin(rot)
            # In screen space, UP is -Y. Since North is -Z, dz maps directly to screen Y when facing North.
            rx = dx * c - dz * s
            ry = dx * s + dz * c
        else:
            rx = dx
            ry = dz

        scale = self.radius / max(1.0, self.radar_range)
        px_x = rx * scale
        px_y = ry * scale
        dist_px = math.sqrt(px_x * px_x + px_y * px_y)

        margin = 12.0
        max_r = self.radius - margin
        is_clamped = False
        is_visible = True

        if dist_px > max_r:
            if self.edge_pinning:
                px_x = (px_x / dist_px) * max_r
                px_y = (px_y / dist_px) * max_r
                is_clamped = True
            else:
                is_visible = False

        screen_x = self.center_x + px_x
        screen_y = self.center_y + px_y
        return screen_x, screen_y, is_visible, is_clamped, world_dist

    def draw(self, player_x: float, player_z: float, cam_heading_rad: float, cam_fov_deg: float, markers: list):
        cx = self.center_x
        cy = self.center_y
        r = self.radius

        # 1. Radar Circular Background & Outer Glow
        draw_circle(cx, cy, int(r + 4.0), COLOR_RADAR_RIM_GLOW)
        draw_circle(cx, cy, int(r), COLOR_RADAR_BG)
        draw_circle_lines(cx, cy, r, COLOR_RADAR_RIM)
        draw_circle_lines(cx, cy, r - 2.0, Color(40, 60, 95, 255))

        # 2. Concentric Range Rings (25%, 50%, 75%, 100%)
        fractions = [0.25, 0.50, 0.75]
        for f in fractions:
            rr = r * f
            draw_circle_lines(cx, cy, rr, COLOR_RADAR_GRID)
            # Range label in meters
            dist_val = int(self.radar_range * f)
            draw_text(f"{dist_val}m", cx + 4, int(cy - rr - 10), 9, Color(90, 130, 175, 200))

        # 3. Crosshair Axes
        draw_line(int(cx - r), cy, int(cx + r), cy, Color(30, 50, 80, 120))
        draw_line(cx, int(cy - r), cx, int(cy + r), Color(30, 50, 80, 120))

        # 4. Animated Radar Sweep Scan Line
        sweep_x = cx + math.cos(self.sweep_angle) * (r - 4.0)
        sweep_y = cy + math.sin(self.sweep_angle) * (r - 4.0)
        draw_line(cx, cy, int(sweep_x), int(sweep_y), Color(0, 220, 255, 120))

        # 5. Camera View Frustum Cone (FOV Projection)
        half_fov_rad = math.radians(cam_fov_deg * 0.5)
        if self.mode == MODE_HEADING_UP:
            # Looking straight UP (-Y on screen)
            base_angle = -math.pi * 0.5
        else:
            # Looking along cam_heading_rad: 0 rad (North) = -Y (-pi/2)
            base_angle = cam_heading_rad - math.pi * 0.5

        cone_len = r * 0.88
        p1 = Vector2(cx, cy)
        p2 = Vector2(cx + math.cos(base_angle - half_fov_rad) * cone_len, cy + math.sin(base_angle - half_fov_rad) * cone_len)
        p3 = Vector2(cx + math.cos(base_angle + half_fov_rad) * cone_len, cy + math.sin(base_angle + half_fov_rad) * cone_len)
        draw_triangle(p1, p3, p2, COLOR_FRUSTUM_CONE)
        draw_line(int(p1.x), int(p1.y), int(p2.x), int(p2.y), Color(0, 200, 255, 90))
        draw_line(int(p1.x), int(p1.y), int(p3.x), int(p3.y), Color(0, 200, 255, 90))

        # 6. Cardinal Direction Notches along the Radar Rim (N, E, S, W)
        cardinals = [
            ("N", 0.0, COLOR_COMPASS_NORTH),
            ("E", math.pi * 0.5, COLOR_COMPASS_TEXT),
            ("S", math.pi, COLOR_COMPASS_TEXT),
            ("W", -math.pi * 0.5, COLOR_COMPASS_TEXT)
        ]
        for label, card_angle, col in cardinals:
            if self.mode == MODE_HEADING_UP:
                # Cardinal positions rotate opposite to camera heading
                rel_card_angle = card_angle - cam_heading_rad - math.pi * 0.5
            else:
                rel_card_angle = card_angle - math.pi * 0.5

            nx = cx + math.cos(rel_card_angle) * (r - 12.0)
            ny = cy + math.sin(rel_card_angle) * (r - 12.0)
            draw_text(label, int(nx - 4), int(ny - 6), 11, col)

        # 7. Draw Markers & Blips on Radar
        for m in markers:
            if not m.active:
                continue

            sx, sy, is_vis, is_clamped, w_dist = self.world_to_radar(
                m.pos.x, m.pos.z, player_x, player_z, cam_heading_rad
            )
            if not is_vis:
                continue

            ix = int(sx)
            iy = int(sy)

            if is_clamped:
                # Out-of-range edge-pinned marker: draw directional chevron pointing outward
                dx = sx - cx
                dy = sy - cy
                angle = math.atan2(dy, dx)
                tip_x = cx + math.cos(angle) * (r - 4.0)
                tip_y = cy + math.sin(angle) * (r - 4.0)
                side1_x = tip_x - math.cos(angle - 0.5) * 10.0
                side1_y = tip_y - math.sin(angle - 0.5) * 10.0
                side2_x = tip_x - math.cos(angle + 0.5) * 10.0
                side2_y = tip_y - math.sin(angle + 0.5) * 10.0

                draw_triangle(Vector2(tip_x, tip_y), Vector2(side1_x, side1_y), Vector2(side2_x, side2_y), m.color)
                draw_circle(int(tip_x), int(tip_y), 3.0, Color(255, 255, 255, 200))
            else:
                # In-range marker: draw distinct shape based on marker type
                pulse = 1.0 + 0.25 * math.sin(m.pulse_timer * 6.0) if m.is_objective else 1.0
                sz = 4.0 * pulse

                if m.marker_type == MARKER_PRIMARY_BEACON:
                    # Diamond with golden halo
                    draw_circle(ix, iy, int(sz + 3.0), Color(255, 215, 0, 70))
                    draw_line(ix, int(iy - sz * 1.5), int(ix + sz * 1.5), iy, m.color)
                    draw_line(int(ix + sz * 1.5), iy, ix, int(iy + sz * 1.5), m.color)
                    draw_line(ix, int(iy + sz * 1.5), int(ix - sz * 1.5), iy, m.color)
                    draw_line(int(ix - sz * 1.5), iy, ix, int(iy - sz * 1.5), m.color)
                    draw_circle(ix, iy, 2.5, m.color)
                elif m.marker_type == MARKER_COMMS_RELAY:
                    # Concentric rings
                    draw_circle_lines(ix, iy, sz + 2.0, m.color)
                    draw_circle(ix, iy, 2.0, m.color)
                elif m.marker_type == MARKER_SUPPLY_CACHE:
                    # Small green square
                    draw_rectangle(int(ix - sz), int(iy - sz), int(sz * 2), int(sz * 2), m.color)
                    draw_rectangle_lines(int(ix - sz), int(iy - sz), int(sz * 2), int(sz * 2), Color(255, 255, 255, 180))
                elif m.marker_type == MARKER_PATROL_DRONE:
                    # Pulsing orange triangle
                    draw_circle(ix, iy, int(sz + 2.0), Color(255, 80, 40, 80))
                    draw_circle(ix, iy, sz, m.color)
                else:
                    draw_circle(ix, iy, sz, m.color)

        # 8. Center Player Icon
        if self.mode == MODE_HEADING_UP:
            # Player arrow points straight up
            tip = Vector2(cx, cy - 8.0)
            l_wing = Vector2(cx - 5.0, cy + 6.0)
            r_wing = Vector2(cx + 5.0, cy + 6.0)
        else:
            # Player arrow rotates to match heading
            rot = cam_heading_rad - math.pi * 0.5
            tip = Vector2(cx + math.cos(rot) * 8.0, cy + math.sin(rot) * 8.0)
            l_wing = Vector2(cx + math.cos(rot + 2.4) * 6.0, cy + math.sin(rot + 2.4) * 6.0)
            r_wing = Vector2(cx + math.cos(rot - 2.4) * 6.0, cy + math.sin(rot - 2.4) * 6.0)

        draw_triangle(tip, l_wing, r_wing, Color(0, 240, 255, 255))
        draw_circle(cx, cy, 2.0, Color(255, 255, 255, 255))

        # 9. Mode & Range Badge
        mode_str = "HEAD-UP [F1]" if self.mode == MODE_HEADING_UP else "NORTH-UP [F1]"
        draw_text(mode_str, int(cx - r + 8), int(cy + r - 18), 10, Color(0, 220, 255, 220))
        draw_text(f"{int(self.radar_range)}m [1/2/3]", int(cx + r - 64), int(cy + r - 18), 10, Color(200, 220, 255, 200))


class CompassStripSystem:
    """
    Horizontal Skyrim/Horizon-style Compass Tape spanning top-center.
    Displays continuous 360° heading tape with degree notches, cardinal marks,
    and objective icons positioned by relative bearing with smooth edge-fade alpha.
    """
    def __init__(self, center_x: int, top_y: int, width: int, height: int):
        self.center_x = center_x
        self.top_y = top_y
        self.width = width
        self.height = height
        self.fov_deg = 120.0        # Angular span of the visible compass strip in degrees

    def draw(self, player_x: float, player_z: float, cam_heading_rad: float, markers: list):
        cx = self.center_x
        cy = self.top_y
        w = self.width
        h = self.height
        half_w = w * 0.5
        half_fov_rad = math.radians(self.fov_deg * 0.5)

        # 1. Sleek Compass Tape Background with Gradient Border
        left_x = int(cx - half_w)
        draw_rectangle(left_x, cy, w, h, COLOR_COMPASS_BG)
        draw_rectangle_lines(left_x, cy, w, h, COLOR_COMPASS_BORDER)
        draw_line(left_x, cy + h - 1, left_x + w, cy + h - 1, Color(30, 50, 80, 255))

        # 2. Draw Graduations Every 15 Degrees across 360°
        # We loop through all 24 15-degree steps and map their relative bearing
        for deg in range(0, 360, 15):
            rad = math.radians(deg)
            # Angular offset relative to current camera heading
            delta = normalize_angle_rad(rad - cam_heading_rad)

            if abs(delta) <= half_fov_rad:
                # Map delta onto horizontal tape
                ratio = delta / half_fov_rad
                tick_x = cx + ratio * half_w

                # Smooth edge alpha attenuation
                edge_factor = 1.0 - abs(ratio)
                alpha = max(0, min(255, int(255.0 * min(1.0, edge_factor * 2.5))))
                if alpha <= 0:
                    continue

                is_major = (deg % 30 == 0)
                tick_h = 10 if is_major else 5
                draw_line(int(tick_x), cy + h - tick_h, int(tick_x), cy + h, Color(140, 175, 220, alpha))

                # Cardinal Labels or Degree Numbers on Major Ticks
                label = None
                col = Color(200, 220, 250, alpha)
                if deg == 0:
                    label = "N"
                    col = Color(255, 75, 75, alpha)
                elif deg == 45:
                    label = "NE"
                elif deg == 90:
                    label = "E"
                elif deg == 135:
                    label = "SE"
                elif deg == 180:
                    label = "S"
                elif deg == 225:
                    label = "SW"
                elif deg == 270:
                    label = "W"
                elif deg == 315:
                    label = "NW"
                elif is_major:
                    label = str(deg)
                    col = Color(120, 150, 190, alpha)

                if label:
                    text_len = len(label) * 4
                    draw_text(label, int(tick_x - text_len), cy + 4, 11, col)

        # 3. Draw Markers on the Compass Tape
        for m in markers:
            if not m.active:
                continue

            target_bearing = compute_target_bearing_rad(player_x, player_z, m.pos.x, m.pos.z)
            delta = normalize_angle_rad(target_bearing - cam_heading_rad)

            if abs(delta) <= half_fov_rad:
                ratio = delta / half_fov_rad
                marker_x = cx + ratio * half_w

                edge_factor = 1.0 - abs(ratio)
                alpha = max(0, min(255, int(255.0 * min(1.0, edge_factor * 2.8))))
                if alpha <= 0:
                    continue

                dx = m.pos.x - player_x
                dz = m.pos.z - player_z
                dist_m = int(math.sqrt(dx * dx + dz * dz))

                m_col = Color(m.color.r, m.color.g, m.color.b, alpha)
                ix = int(marker_x)

                # Procedural Icon on Tape
                if m.is_objective:
                    # Golden Diamond with pulsing aura
                    pulse = 1.0 + 0.3 * math.sin(m.pulse_timer * 6.0)
                    sz = 6.0 * pulse
                    draw_line(ix, int(cy + 18 - sz), int(ix + sz), cy + 18, m_col)
                    draw_line(int(ix + sz), cy + 18, ix, int(cy + 18 + sz), m_col)
                    draw_line(ix, int(cy + 18 + sz), int(ix - sz), cy + 18, m_col)
                    draw_line(int(ix - sz), cy + 18, ix, int(cy + 18 - sz), m_col)
                    draw_circle(ix, cy + 18, 2.0, Color(255, 255, 255, alpha))

                    # Distance indicator beneath objective marker
                    dist_text = f"{dist_m}m"
                    draw_text(dist_text, int(ix - len(dist_text) * 3), cy + h + 2, 10, Color(255, 215, 0, alpha))
                else:
                    # Subtle pip marker
                    draw_circle(ix, cy + 18, 3.5, m_col)
                    draw_circle_lines(ix, cy + 18, 4.5, Color(255, 255, 255, int(alpha * 0.7)))

        # 4. Central Reticle Indicator (Heading Caret)
        reticle_col = COLOR_COMPASS_RETICLE
        draw_line(cx, cy, cx, cy + 8, reticle_col)
        draw_line(cx - 5, cy, cx, cy + 6, reticle_col)
        draw_line(cx + 5, cy, cx, cy + 6, reticle_col)

        # Current Heading Degree Text Badge
        heading_deg = int((math.degrees(cam_heading_rad) + 360.0) % 360.0)
        heading_str = f"{heading_deg}°"
        draw_text(heading_str, int(cx - len(heading_str) * 3 - 1), cy + h + 2, 10, Color(255, 215, 0, 220))


# ==============================================================================
# BLOCK 2: WORLD SIMULATION & ENTITIES
# ==============================================================================

class ArenaWorld:
    """
    3D Arena environment containing ground terrain, boundary hazard pylons,
    ancient cardinal monoliths, communication relays, supply crates, and a patrolling drone.
    """
    def __init__(self):
        self.arena_radius = 78.0
        self.markers = []
        self.active_objective_idx = 0
        self.drone_pos = Vector3(0.0, 6.0, 0.0)
        self.drone_angle = 0.0
        self.objective_score = 0
        self.init_world()

    def init_world(self):
        self.markers = []

        # 1. Four Cardinal Monoliths (N, E, S, W) at arena boundaries to visually verify bearing
        dist = 65.0
        self.markers.append(MapMarker(10, Vector3(0.0, 0.0, -dist), "NORTH MONOLITH", MARKER_CARDINAL_TOWER, Color(255, 80, 80, 255)))
        self.markers.append(MapMarker(11, Vector3(dist, 0.0, 0.0), "EAST MONOLITH", MARKER_CARDINAL_TOWER, Color(80, 160, 255, 255)))
        self.markers.append(MapMarker(12, Vector3(0.0, 0.0, dist), "SOUTH MONOLITH", MARKER_CARDINAL_TOWER, Color(200, 200, 255, 255)))
        self.markers.append(MapMarker(13, Vector3(-dist, 0.0, 0.0), "WEST MONOLITH", MARKER_CARDINAL_TOWER, Color(255, 200, 80, 255)))

        # 2. Communications Relays (Cyan)
        self.markers.append(MapMarker(20, Vector3(32.0, 0.0, -28.0), "RELAY ALPHA", MARKER_COMMS_RELAY, Color(0, 220, 255, 255)))
        self.markers.append(MapMarker(21, Vector3(-35.0, 0.0, 30.0), "RELAY BETA", MARKER_COMMS_RELAY, Color(0, 220, 255, 255)))

        # 3. Supply Pods (Green)
        self.markers.append(MapMarker(30, Vector3(-25.0, 0.0, -35.0), "SUPPLY POD 1", MARKER_SUPPLY_CACHE, Color(80, 240, 120, 255)))
        self.markers.append(MapMarker(31, Vector3(40.0, 0.0, 25.0), "SUPPLY POD 2", MARKER_SUPPLY_CACHE, Color(80, 240, 120, 255)))
        self.markers.append(MapMarker(32, Vector3(10.0, 0.0, 48.0), "SUPPLY POD 3", MARKER_SUPPLY_CACHE, Color(80, 240, 120, 255)))

        # 4. Recon Patrol Drone (Orange/Red)
        self.drone_marker = MapMarker(40, self.drone_pos, "RECON DRONE", MARKER_PATROL_DRONE, Color(255, 120, 40, 255))
        self.markers.append(self.drone_marker)

        # 5. Mission Objectives Sequence (Golden Beacons)
        self.objective_locations = [
            Vector3(20.0, 0.0, -45.0),
            Vector3(-45.0, 0.0, -15.0),
            Vector3(-30.0, 0.0, 42.0),
            Vector3(45.0, 0.0, 35.0),
            Vector3(0.0, 0.0, 0.0)
        ]
        self.active_objective_idx = 0
        self.primary_objective = MapMarker(
            1, self.objective_locations[self.active_objective_idx], "WAYPOINT BEACON", MARKER_PRIMARY_BEACON, Color(255, 215, 0, 255), is_objective=True
        )
        self.markers.append(self.primary_objective)

    def advance_objective(self):
        self.objective_score += 1
        self.active_objective_idx = (self.active_objective_idx + 1) % len(self.objective_locations)
        self.primary_objective.pos = self.objective_locations[self.active_objective_idx]
        self.primary_objective.pulse_timer = 0.0

    def update(self, dt: float):
        # Update Recon Drone orbital flight
        self.drone_angle += 0.45 * dt
        drone_r = 42.0
        self.drone_pos = Vector3(
            math.cos(self.drone_angle) * drone_r,
            5.5 + 1.2 * math.sin(self.drone_angle * 2.0),
            math.sin(self.drone_angle) * drone_r
        )
        self.drone_marker.pos = self.drone_pos

        # Update pulsing beacon animation
        for m in self.markers:
            m.pulse_timer += dt

    def draw_3d(self, anim_timer: float):
        # 1. Ground Circular Platform & Sector Radial Lines
        draw_circle_3d = True
        grid_slices = 24
        grid_radius = self.arena_radius

        # Ground grid rings
        for r_step in range(15, int(grid_radius) + 1, 15):
            # Draw ground circles using line segments
            pts = 48
            for i in range(pts):
                a1 = (i / float(pts)) * 2.0 * math.pi
                a2 = ((i + 1) / float(pts)) * 2.0 * math.pi
                p1 = Vector3(math.cos(a1) * r_step, 0.02, math.sin(a1) * r_step)
                p2 = Vector3(math.cos(a2) * r_step, 0.02, math.sin(a2) * r_step)
                draw_line_3d(p1, p2, COLOR_GRID_PRIMARY)

        # Radial spokes
        for s in range(grid_slices):
            ang = (s / float(grid_slices)) * 2.0 * math.pi
            p_end = Vector3(math.cos(ang) * grid_radius, 0.02, math.sin(ang) * grid_radius)
            draw_line_3d(Vector3(0.0, 0.02, 0.0), p_end, COLOR_GRID_PRIMARY)

        # Center Arena Ring
        draw_cube(Vector3(0.0, 0.05, 0.0), 3.0, 0.1, 3.0, Color(45, 65, 100, 255))
        draw_cube_wires(Vector3(0.0, 0.05, 0.0), 3.0, 0.1, 3.0, Color(80, 160, 255, 255))

        # 2. Boundary Hazard Pylons around perimeter
        num_pylons = 16
        for p in range(num_pylons):
            pang = (p / float(num_pylons)) * 2.0 * math.pi
            px = math.cos(pang) * grid_radius
            pz = math.sin(pang) * grid_radius
            draw_cylinder(Vector3(px, 1.8, pz), 0.4, 0.4, 3.6, 6, COLOR_BOUNDARY_PYLON)
            draw_sphere(Vector3(px, 3.8, pz), 0.5, Color(255, 180, 50, 255))

        # 3. Cardinal Monoliths
        for m in self.markers:
            if m.marker_type == MARKER_CARDINAL_TOWER:
                # Tall obelisk
                draw_cube(Vector3(m.pos.x, 6.0, m.pos.z), 2.5, 12.0, 2.5, Color(35, 45, 65, 255))
                draw_cube_wires(Vector3(m.pos.x, 6.0, m.pos.z), 2.5, 12.0, 2.5, m.color)
                draw_sphere(Vector3(m.pos.x, 12.8, m.pos.z), 1.2, m.color)
            elif m.marker_type == MARKER_COMMS_RELAY:
                # Communications Antenna Dish
                draw_cylinder(Vector3(m.pos.x, 3.0, m.pos.z), 0.6, 0.6, 6.0, 8, Color(40, 55, 80, 255))
                draw_cylinder(Vector3(m.pos.x, 6.2, m.pos.z), 2.2, 0.2, 0.8, 8, m.color)
                draw_sphere(Vector3(m.pos.x, 7.0, m.pos.z), 0.7, Color(0, 255, 255, 255))
            elif m.marker_type == MARKER_SUPPLY_CACHE:
                # Supply Container
                draw_cube(Vector3(m.pos.x, 1.0, m.pos.z), 2.2, 2.0, 2.2, Color(25, 45, 30, 255))
                draw_cube_wires(Vector3(m.pos.x, 1.0, m.pos.z), 2.2, 2.0, 2.2, m.color)
                draw_cube(Vector3(m.pos.x, 2.2, m.pos.z), 0.8, 0.4, 0.8, Color(100, 255, 150, 255))

        # 4. Primary Objective Beacon Pillar & Ascending Energy Rings
        obj = self.primary_objective
        pulse = 0.5 + 0.5 * math.sin(obj.pulse_timer * 5.0)
        beacon_col = Color(255, 215, 0, 180)
        draw_cylinder(Vector3(obj.pos.x, 12.0, obj.pos.z), 0.8, 0.8, 24.0, 10, Color(255, 200, 40, 90))
        draw_cylinder(Vector3(obj.pos.x, 0.5, obj.pos.z), 3.2, 3.2, 1.0, 8, Color(60, 50, 20, 255))
        draw_cylinder_wires(Vector3(obj.pos.x, 0.5, obj.pos.z), 3.2, 3.2, 1.0, 8, Color(255, 215, 0, 255))

        # Ascending energy rings
        for ring_idx in range(4):
            ring_y = ((anim_timer * 3.0 + ring_idx * 3.5) % 14.0) + 0.5
            ring_rad = 1.6 + 0.4 * math.sin(ring_y * 0.8)
            draw_cylinder(Vector3(obj.pos.x, ring_y, obj.pos.z), ring_rad, ring_rad, 0.25, 8, Color(255, 230, 80, 160))

        # 5. Recon Drone Model (reusing procedural drone asset)
        draw_drone_enemy_3d(
            self.drone_pos,
            rotation_y=math.degrees(self.drone_angle + math.pi * 0.5),
            anim_timer=anim_timer,
            scale=1.2
        )


# ==============================================================================
# BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY ([Tab] & [F1], [F2])
# ==============================================================================

def draw_xray_overlay(
    player_pos: Vector3,
    cam_heading_rad: float,
    cam_yaw: float,
    cam_pitch: float,
    minimap: MinimapSystem,
    active_obj: MapMarker
):
    """
    Renders pedagogical mathematical telemetry overlay breaking down coordinate
    transformations, bearing calculations, and edge-pinning vector projections.
    """
    panel_x = 24
    panel_y = 60
    panel_w = 350
    panel_h = 420

    draw_rectangle(panel_x, panel_y, panel_w, panel_h, Color(10, 14, 24, 235))
    draw_rectangle_lines(panel_x, panel_y, panel_w, panel_h, Color(45, 75, 120, 255))
    draw_rectangle(panel_x, panel_y, panel_w, 28, Color(20, 32, 55, 255))
    draw_text("X-RAY TELEMETRY & RADAR MATH", panel_x + 12, panel_y + 7, 12, Color(0, 225, 255, 255))

    y = panel_y + 36
    lh = 17

    # Player Position & Camera Heading
    heading_deg = (math.degrees(cam_heading_rad) + 360.0) % 360.0
    draw_text(f"Player Pos      : ({player_pos.x:+.1f}, {player_pos.z:+.1f})", panel_x + 12, y, 11, Color(200, 220, 245, 255)); y += lh
    draw_text(f"Camera Heading  : {heading_deg:.1f}° ({math.degrees(cam_heading_rad):+.1f} rad)", panel_x + 12, y, 11, Color(255, 215, 0, 255)); y += lh
    draw_text(f"Camera Orbit    : Yaw={math.degrees(cam_yaw):.1f}° Pitch={math.degrees(cam_pitch):.1f}°", panel_x + 12, y, 11, Color(160, 190, 225, 255)); y += lh
    draw_line(panel_x + 10, y + 2, panel_x + panel_w - 10, y + 2, Color(40, 60, 95, 200)); y += 8

    # Navigation Modes
    mode_name = "Heading-Up (Rotating Map)" if minimap.mode == MODE_HEADING_UP else "North-Up (Fixed Map)"
    pin_name = "ON (Clamped to Rim)" if minimap.edge_pinning else "OFF (Culled Outside)"
    draw_text(f"Minimap Mode    : {mode_name}", panel_x + 12, y, 11, Color(0, 240, 255, 255)); y += lh
    draw_text(f"Edge Pinning    : {pin_name}", panel_x + 12, y, 11, Color(120, 255, 140, 255)); y += lh
    draw_text(f"Radar Range     : {int(minimap.radar_range)}m (R={int(minimap.radius)}px)", panel_x + 12, y, 11, Color(200, 220, 245, 255)); y += lh
    draw_line(panel_x + 10, y + 2, panel_x + panel_w - 10, y + 2, Color(40, 60, 95, 200)); y += 8

    # Active Objective Nav Math
    dx = active_obj.pos.x - player_pos.x
    dz = active_obj.pos.z - player_pos.z
    dist_m = math.sqrt(dx * dx + dz * dz)
    target_bearing = compute_target_bearing_rad(player_pos.x, player_pos.z, active_obj.pos.x, active_obj.pos.z)
    rel_angle = normalize_angle_rad(target_bearing - cam_heading_rad)

    draw_text(f"ACTIVE OBJECTIVE: {active_obj.label}", panel_x + 12, y, 11, Color(255, 200, 60, 255)); y += lh
    draw_text(f"Target World Pos: ({active_obj.pos.x:+.1f}, {active_obj.pos.z:+.1f})", panel_x + 12, y, 10, Color(180, 205, 235, 255)); y += lh
    draw_text(f"Distance        : {dist_m:.1f} meters", panel_x + 12, y, 10, Color(180, 205, 235, 255)); y += lh
    draw_text(f"True Bearing (B): {math.degrees(target_bearing):.1f}° [atan2(dx, -dz)]", panel_x + 12, y, 10, Color(180, 205, 235, 255)); y += lh
    draw_text(f"Rel Angle (dA)  : {math.degrees(rel_angle):+.1f}° [B - Heading]", panel_x + 12, y, 10, Color(255, 215, 0, 255)); y += lh
    draw_line(panel_x + 10, y + 2, panel_x + panel_w - 10, y + 2, Color(40, 60, 95, 200)); y += 8

    # Math Formulas Reference
    draw_text("CORE ALGORITHMS (C++ TRANSFERABLE):", panel_x + 12, y, 10, Color(140, 175, 225, 255)); y += lh
    draw_text("1. Bearing : atan2(target.x - p.x, -(target.z - p.z))", panel_x + 14, y, 9, Color(200, 220, 255, 200)); y += lh
    draw_text("2. Compass : x = cx + (wrap(B - Head) / fov_half) * w_half", panel_x + 14, y, 9, Color(200, 220, 255, 200)); y += lh
    draw_text("3. Head-Up : rx = dx*cos(-H) - dz*sin(-H)", panel_x + 14, y, 9, Color(200, 220, 255, 200)); y += lh
    draw_text("             ry = dx*sin(-H) + dz*cos(-H)", panel_x + 14, y, 9, Color(200, 220, 255, 200)); y += lh
    draw_text("4. Edge-Pin: p_clamp = center + norm(p) * (R - margin)", panel_x + 14, y, 9, Color(200, 220, 255, 200)); y += lh

    # Controls guide
    draw_text("[Tab] Overlay | [F1] Mode | [F2] Pinning | [R] Reset", panel_x + 12, panel_y + panel_h - 18, 10, Color(0, 220, 255, 220))


# ==============================================================================
# BLOCK 4: MAIN GAME LOOP & AUTOMATED SMOKE TEST
# ==============================================================================

class MinimapCompassGame:
    """
    Standalone interactive single-pattern lab demonstrating 3D Minimap Radar
    and Compass Strip navigation HUD architecture.
    """
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()

        self.sfx = SoundLibrary()
        self.sfx.init_defaults()

        # World Simulation & Navigation Systems
        self.world = ArenaWorld()
        self.minimap = MinimapSystem(center_x=1120, center_y=560, radius=110.0)
        self.compass = CompassStripSystem(center_x=640, top_y=58, width=540, height=36)

        # Player State
        self.player_pos = Vector3(0.0, 0.0, 15.0)
        self.player_vel = Vector3(0.0, 0.0, 0.0)
        self.player_yaw_deg = 0.0
        self.player_speed = 18.0
        self.anim_timer = 0.0

        # Orbital Camera Follow Rig
        self.cam_yaw = 0.0          # Radians around player
        self.cam_pitch = 0.45       # Radians above horizontal plane (~25 deg)
        self.cam_dist = 11.0
        self.cam_fov_deg = 62.0

        self.camera = Camera3D(
            Vector3(0.0, 5.0, 25.0),
            Vector3(0.0, 1.5, 15.0),
            Vector3(0.0, 1.0, 0.0),
            self.cam_fov_deg,
            CAMERA_PERSPECTIVE
        )

        # Lab Inspection Toggles
        self.show_xray = True

    def handle_input(self, dt: float):
        # 1. Lab Mode Toggles
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray

        if is_dual_pattern_toggle_pressed():
            # Toggle Minimap: Heading-Up vs North-Up
            if self.minimap.mode == MODE_HEADING_UP:
                self.minimap.mode = MODE_NORTH_UP
            else:
                self.minimap.mode = MODE_HEADING_UP
            self.sfx.play("click", 0.6)

        if is_dual_secondary_toggle_pressed():
            # Toggle Edge-Pinning Clamping
            self.minimap.edge_pinning = not self.minimap.edge_pinning
            self.sfx.play("click", 0.6)

        if is_dual_reset_pressed():
            self.player_pos = Vector3(0.0, 0.0, 15.0)
            self.player_vel = Vector3(0.0, 0.0, 0.0)
            self.cam_yaw = 0.0
            self.cam_pitch = 0.45
            self.world.init_world()
            self.sfx.play("powerup", 0.7)

        # Zoom level presets [1], [2], [3]
        if is_key_pressed(KEY_ONE):
            self.minimap.radar_range = 40.0
            self.sfx.play("blip", 0.5)
        elif is_key_pressed(KEY_TWO):
            self.minimap.radar_range = 80.0
            self.sfx.play("blip", 0.5)
        elif is_key_pressed(KEY_THREE):
            self.minimap.radar_range = 140.0
            self.sfx.play("blip", 0.5)

        # 2. Camera Rotation with Directional Arrow Keys & Gamepad Right Stick
        # Left/Right Arrows rotate horizontal Yaw; Up/Down Arrows adjust Pitch elevation
        look_vec = get_dual_look_2d(deadzone=0.18, use_arrow_keys=True)
        rot_speed = 2.4
        pitch_speed = 1.8

        self.cam_yaw -= look_vec.x * rot_speed * dt
        self.cam_pitch += look_vec.y * pitch_speed * dt
        # Clamp pitch to prevent gimbal lock or flipping upside-down
        self.cam_pitch = max(0.12, min(1.35, self.cam_pitch))

        # 3. Player Movement with WASD & Gamepad Left Stick (Camera-Relative)
        # Note: use_arrow_keys=False ensures Arrow Keys only rotate the camera without conflict!
        move_input = get_dual_move_2d(deadzone=0.18, use_arrow_keys=False)

        # Camera horizontal forward & right vectors
        # Looking from camera to target:
        f_x = -math.sin(self.cam_yaw)
        f_z = -math.cos(self.cam_yaw)
        # Perpendicular right vector:
        r_x = -f_z
        r_z = f_x

        # W/S move along forward/back; A/D strafe along right/left
        # In move_input: W is -Y, S is +Y, A is -X, D is +X
        move_dir_x = f_x * (-move_input.y) + r_x * move_input.x
        move_dir_z = f_z * (-move_input.y) + r_z * move_input.x
        input_len = math.sqrt(move_dir_x * move_dir_x + move_dir_z * move_dir_z)

        if input_len > 0.001:
            move_dir_x /= input_len
            move_dir_z /= input_len
            target_vel_x = move_dir_x * self.player_speed
            target_vel_z = move_dir_z * self.player_speed

            # Smoothly face movement direction
            target_yaw = math.degrees(math.atan2(move_dir_x, move_dir_z))
            self.player_yaw_deg = target_yaw
        else:
            target_vel_x = 0.0
            target_vel_z = 0.0

        # Exponential velocity damping
        self.player_vel.x = damp(self.player_vel.x, target_vel_x, 14.0, dt)
        self.player_vel.z = damp(self.player_vel.z, target_vel_z, 14.0, dt)

        # Integrate displacement
        self.player_pos.x += self.player_vel.x * dt
        self.player_pos.z += self.player_vel.z * dt

        # Arena boundary clamp
        dist_from_origin = math.sqrt(self.player_pos.x * self.player_pos.x + self.player_pos.z * self.player_pos.z)
        if dist_from_origin > self.world.arena_radius - 2.0:
            scale = (self.world.arena_radius - 2.0) / dist_from_origin
            self.player_pos.x *= scale
            self.player_pos.z *= scale

    def update(self):
        dt = min(get_frame_time(), 0.05)
        self.anim_timer += dt

        self.handle_input(dt)
        self.world.update(dt)
        self.minimap.update(dt)

        # Check Beacon Arrival Proximity
        active_obj = self.world.primary_objective
        dx = active_obj.pos.x - self.player_pos.x
        dz = active_obj.pos.z - self.player_pos.z
        if math.sqrt(dx * dx + dz * dz) < 3.8:
            self.world.advance_objective()
            self.sfx.play("powerup", 0.8)

        # Update Orbital Camera Rig to follow player smoothly
        cam_target = Vector3(self.player_pos.x, 1.5, self.player_pos.z)
        cam_off_x = math.sin(self.cam_yaw) * math.cos(self.cam_pitch) * self.cam_dist
        cam_off_y = math.sin(self.cam_pitch) * self.cam_dist
        cam_off_z = math.cos(self.cam_yaw) * math.cos(self.cam_pitch) * self.cam_dist

        desired_pos = Vector3(
            self.player_pos.x + cam_off_x,
            self.player_pos.y + cam_off_y,
            self.player_pos.z + cam_off_z
        )

        self.camera.position = damp_v3(self.camera.position, desired_pos, 14.0, dt)
        self.camera.target = damp_v3(self.camera.target, cam_target, 16.0, dt)

    def draw(self):
        begin_drawing()
        clear_background(Color(10, 13, 22, 255))

        # =====================================================================
        # 1. 3D WORLD RENDERING PASS
        # =====================================================================
        begin_mode_3d(self.camera)

        # Render 3D Environment & Landmarks
        self.world.draw_3d(self.anim_timer)

        # Render 3D Humanoid Player Model (reusing procedural humanoid asset)
        draw_humanoid_enemy_3d(
            self.player_pos,
            rotation_y=self.player_yaw_deg,
            anim_timer=self.anim_timer if (abs(self.player_vel.x) > 0.5 or abs(self.player_vel.z) > 0.5) else 0.0,
            scale=1.0,
            palette={
                "armor": Color(45, 110, 190, 255),
                "chest": Color(80, 145, 230, 255),
                "joints": Color(25, 30, 45, 255),
                "visor": Color(0, 240, 255, 255),
                "weapon": Color(160, 175, 195, 255),
                "energy": Color(0, 230, 255, 255)
            }
        )

        end_mode_3d()

        # =====================================================================
        # 2. 2D HUD & NAVIGATION OVERLAYS
        # =====================================================================
        # Compute horizontal camera heading
        cam_forward_x = -math.sin(self.cam_yaw)
        cam_forward_z = -math.cos(self.cam_yaw)
        cam_heading_rad = compute_camera_heading_rad(cam_forward_x, cam_forward_z)

        # Top-Center Compass Strip (Horizon/Skyrim Style)
        self.compass.draw(self.player_pos.x, self.player_pos.z, cam_heading_rad, self.world.markers)

        # Bottom-Right Minimap Radar
        self.minimap.draw(
            self.player_pos.x, self.player_pos.z,
            cam_heading_rad, self.cam_fov_deg,
            self.world.markers
        )

        # Top-Left Mission Objective HUD Card
        active_obj = self.world.primary_objective
        dx = active_obj.pos.x - self.player_pos.x
        dz = active_obj.pos.z - self.player_pos.z
        dist_m = int(math.sqrt(dx * dx + dz * dz))

        card_x = 24
        card_y = 60 if not self.show_xray else 490
        draw_rectangle(card_x, card_y, 280, 68, Color(12, 16, 28, 220))
        draw_rectangle_lines(card_x, card_y, 280, 68, Color(45, 75, 115, 255))
        draw_circle(card_x + 18, card_y + 22, 6.0, Color(255, 215, 0, 255))
        draw_text("PRIMARY MISSION OBJECTIVE", card_x + 32, card_y + 12, 10, Color(255, 215, 0, 255))
        draw_text(f"{active_obj.label} ({self.world.objective_score} Cleared)", card_x + 32, card_y + 28, 12, Color(240, 245, 255, 255))
        draw_text(f"Distance: {dist_m}m | Follow Compass Reticle", card_x + 32, card_y + 46, 10, Color(140, 175, 225, 255))

        # Controls Hint Bar (Bottom Left)
        draw_text("MOVE: [W][A][S][D] / Left Stick | ROTATE CAM: [Arrows] / Right Stick", 24, SCREEN_HEIGHT - 32, 11, Color(180, 205, 235, 255))
        draw_text("[Tab] X-Ray | [F1] Map Mode | [F2] Edge Pin | [1/2/3] Zoom | [R] Reset", 24, SCREEN_HEIGHT - 16, 10, Color(100, 140, 190, 255))

        # X-Ray Telemetry Overlay ([Tab])
        if self.show_xray:
            draw_xray_overlay(
                self.player_pos,
                cam_heading_rad,
                self.cam_yaw,
                self.cam_pitch,
                self.minimap,
                active_obj
            )

        # Standard repository header widgets
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

        self.sfx.unload_all()
        close_audio_device()
        close_window()


if __name__ == "__main__":
    is_smoke = "--smoke-test" in sys.argv
    MinimapCompassGame().run(smoke_test=is_smoke)

