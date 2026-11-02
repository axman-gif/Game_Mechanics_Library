# -*- coding: utf-8 -*-
"""
Guard Route - Waypoint Patrol & Observation Scan Systems
========================================================
Section          : 3.3 Enemies & AI
Pattern Category : Artificial Intelligence & Navigation
Dimension        : 2D

Problem Solved:
  In stealth, tactical, and action games (Metal Gear Solid, Commandos, Hitman,
  Thief, Dishonored), autonomous enemy guards must move with believable purpose.
  Without structured waypoint patrolling, enemies either stand frozen or wander
  randomly, creating erratic, unreadable patterns that break stealth gameplay.
  Furthermore, naive waypoint systems suffer from destination jitter (failing
  arrival hysteresis), snap headings unnaturally without angular acceleration,
  and lack inspection dwell pauses to monitor doorways, blind spots, and corridors.

How the Patterns Work:
  1. Waypoint Patrol Graph & Traversal Modes:
     An ordered sequence of nodes Waypoint[N] with coordinates, dwell durations,
     and sector inspection angles. Traversal is controlled via:
       - Loop / Circuit Mode    : 0 -> 1 -> 2 -> ... -> N-1 -> 0 (endless loop)
       - Ping-Pong / Reverse Mode: 0 -> 1 -> 2 -> ... -> N-1 -> N-2 -> ... -> 0
     Arrival uses distance thresholding (||pos - wp|| <= r_arrival) with hysteresis
     to eliminate oscillation around target coordinates.
  2. Multi-Phase Node State Machine (Advance -> Arrive -> Dwell/Scan -> Depart):
     - STATE_MOVING  : Steers toward current waypoint; heading follows velocity.
     - STATE_WAITING : Upon arrival, halts translation and executes sequential
                       angular observation sweeps (e.g., checking left 45 deg,
                       right 45 deg) with configurable dwell timers.
     - STATE_ALERT   : If the player breaches the sensory vision cone, the guard
                       halts the patrol to investigate, resuming once suspicion clears.
  3. Continuous Angular Damping:
     Avoids instantaneous snap rotation by wrapping angular deltas to [-pi, pi]
     and smoothly interpolating orientation toward the target heading.

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - [W][A][S][D] / Gamepad Left Stick     : Sneak Player Operative through compound
  - [Shift] / Gamepad B                   : Sprint (faster movement, but raises alert if heard)
  - [E] / Gamepad X                       : Hack Data Terminals (hold near terminal)
  - [Tab] / Gamepad View (Select)         : Toggle X-Ray Telemetry & Waypoint Graph Overlay
  - [F1]  / Gamepad LB                    : Toggle Patrol Traversal: [LOOP / CIRCUIT] vs [PING-PONG / REVERSE]
  - [F2]  / Gamepad RB                    : Toggle Guard Speed: [PATROL WALK (65 px/s)] vs [ALERT JOG (125 px/s)]
  - [1] / [2] / [3]                       : Toggle Vision Cone Visualization Style
  - [Ctrl +/-]                            : Increase / Decrease UI Font Size
  - [F11]                                 : Toggle Fullscreen
  - [R]   / Gamepad Start                 : Reset simulation & terminals
"""

import sys
import os
import math
import random

# 1. Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# 2. Add repository root to search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# 3. Mandatory Raylib & modular workspace imports
from pyray import *
from assets import *
from utils import *

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WINDOW_TITLE = "Guard Route - Waypoint Patrol Systems (Raylib Pattern Lab)"

# Traversal Modes
TRAVERSAL_LOOP = 0       # 0 -> 1 -> 2 -> 3 -> 0 ...
TRAVERSAL_PING_PONG = 1  # 0 -> 1 -> 2 -> 3 -> 2 -> 1 -> 0 ...

# Guard FSM States
STATE_MOVING = 0
STATE_WAITING = 1
STATE_INVESTIGATING = 2
STATE_RETURNING = 3

STATE_NAMES = {
    STATE_MOVING: "MOVING",
    STATE_WAITING: "LOOK-AROUND",
    STATE_INVESTIGATING: "ALERT-INVESTIGATE",
    STATE_RETURNING: "LEASH-RETURN"
}


# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATION (WAYPOINT PATROL & SCAN ENGINE)
# ==============================================================================

class Waypoint:
    """
    Struct representing an individual patrol node in a route graph.

    C++ Equivalent:
      struct Waypoint {
          Vector2 pos;
          float wait_time;
          float scan_angles[4];
          int scan_count;
          float arrival_radius;
      };
    """
    def __init__(self, x: float, y: float, wait_time: float = 1.6,
                 scan_angles: list = None, arrival_radius: float = 20.0):
        self.pos = Vector2(float(x), float(y))
        self.wait_time = float(wait_time)
        self.scan_angles = scan_angles if scan_angles is not None else []
        self.arrival_radius = float(arrival_radius)


class PatrolRoute:
    """
    Manages an ordered sequence of waypoints and traversal progression rules.
    """
    def __init__(self, waypoints: list, traversal_mode: int = TRAVERSAL_LOOP):
        self.waypoints = waypoints
        self.traversal_mode = traversal_mode

    def get_count(self) -> int:
        return len(self.waypoints)

    def get_waypoint(self, index: int) -> Waypoint:
        if not self.waypoints:
            return Waypoint(0.0, 0.0)
        idx = max(0, min(len(self.waypoints) - 1, index))
        return self.waypoints[idx]

    def advance_index(self, current_index: int, direction: int) -> tuple:
        """
        Advances to the next waypoint index based on traversal mode.
        Returns: (next_index: int, new_direction: int)
        """
        count = len(self.waypoints)
        if count <= 1:
            return (0, 1)

        if self.traversal_mode == TRAVERSAL_LOOP:
            # Circuit: Wrap around modulo count
            next_idx = (current_index + 1) % count
            return (next_idx, 1)
        else:
            # Ping-Pong: Reverse direction when reaching endpoints
            next_idx = current_index + direction
            new_dir = direction

            if next_idx >= count:
                next_idx = count - 2
                new_dir = -1
            elif next_idx < 0:
                next_idx = 1
                new_dir = 1

            return (next_idx, new_dir)


def wrap_angle_rad(angle: float) -> float:
    """Wraps an arbitrary angle in radians to [-pi, +pi]."""
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


def smooth_rotate_rad(current: float, target: float, turn_speed: float, dt: float) -> float:
    """
    Interpolates orientation angle along the shortest circular arc.
    Guarantees natural turning without snapping or 360-degree backflips.
    """
    diff = wrap_angle_rad(target - current)
    max_step = turn_speed * dt
    if abs(diff) <= max_step:
        return target
    return wrap_angle_rad(current + (max_step if diff > 0.0 else -max_step))


def segment_intersects_aabb_2d(p1: Vector2, p2: Vector2, box_min: Vector2, box_max: Vector2) -> bool:
    """
    Tests if line segment P1->P2 intersects a 2D Axis-Aligned Bounding Box (AABB).
    Used for line-of-sight raycasts through obstacle crates.
    """
    dx = p2.x - p1.x
    dy = p2.y - p1.y

    t_min = 0.0
    t_max = 1.0

    # X axis
    if abs(dx) > 0.00001:
        tx1 = (box_min.x - p1.x) / dx
        tx2 = (box_max.x - p1.x) / dx
        if tx1 > tx2:
            tx1, tx2 = tx2, tx1
        t_min = max(t_min, tx1)
        t_max = min(t_max, tx2)
        if t_min > t_max:
            return False
    else:
        if p1.x < box_min.x or p1.x > box_max.x:
            return False

    # Y axis
    if abs(dy) > 0.00001:
        ty1 = (box_min.y - p1.y) / dy
        ty2 = (box_max.y - p1.y) / dy
        if ty1 > ty2:
            ty1, ty2 = ty2, ty1
        t_min = max(t_min, ty1)
        t_max = min(t_max, ty2)
        if t_min > t_max:
            return False
    else:
        if p1.y < box_min.y or p1.y > box_max.y:
            return False

    return True


# ==============================================================================
# BLOCK 2: WORLD SIMULATION & ENTITIES
# ==============================================================================

class GuardAgent:
    """
    Autonomous patrolling enemy guard driven by the Waypoint Patrol Pattern.
    """
    def __init__(self, guard_id: int, name: str, route: PatrolRoute,
                 start_wp_idx: int = 0, walk_speed: float = 65.0):
        self.id = guard_id
        self.name = name
        self.route = route
        self.current_wp_idx = start_wp_idx
        self.direction = 1
        self.walk_speed = walk_speed
        self.turn_speed = 3.6  # rad/s

        wp = route.get_waypoint(start_wp_idx)
        self.pos = Vector2(wp.pos.x, wp.pos.y)
        self.vel = Vector2(0.0, 0.0)
        self.heading = 0.0
        self.target_heading = 0.0

        # State Machine
        self.state = STATE_MOVING
        self.state_timer = 0.0
        self.scan_idx = 0
        self.anim_timer = random.uniform(0.0, 5.0)

        # Sensory Perception (Vision Cone)
        self.vision_range = 190.0
        self.vision_fov_rad = math.radians(72.0)
        self.alert_level = 0.0  # 0.0 to 1.0 (Alert meter)
        self.investigate_pos = Vector2(0.0, 0.0)

    def update(self, dt: float, speed_multiplier: float, player_pos: Vector2,
               obstacles: list, is_player_sprinting: bool):
        self.anim_timer += dt
        effective_speed = self.walk_speed * speed_multiplier

        # ----------------------------------------------------------------------
        # 1. Sensory Perception (Line of Sight & Hearing)
        # ----------------------------------------------------------------------
        can_see_player = self._check_vision(player_pos, obstacles)

        # Hearing check: Sprinting player nearby creates footstep sound
        dx_p = player_pos.x - self.pos.x
        dy_p = player_pos.y - self.pos.y
        dist_p = math.sqrt(dx_p * dx_p + dy_p * dy_p)
        can_hear_player = is_player_sprinting and (dist_p < 220.0)

        if can_see_player:
            # Alert fills quickly in direct line of sight
            self.alert_level = min(1.0, self.alert_level + dt * 1.8)
            self.investigate_pos = Vector2(player_pos.x, player_pos.y)
            if self.alert_level >= 0.65 and self.state != STATE_INVESTIGATING:
                self.state = STATE_INVESTIGATING
                self.state_timer = 3.0
        elif can_hear_player:
            # Sound triggers suspicion
            self.alert_level = min(0.6, self.alert_level + dt * 1.0)
            if self.state == STATE_MOVING:
                self.target_heading = math.atan2(dy_p, dx_p)
        else:
            # Alert decays when out of sight
            self.alert_level = max(0.0, self.alert_level - dt * 0.65)

        # ----------------------------------------------------------------------
        # 2. State Machine Execution
        # ----------------------------------------------------------------------
        if self.state == STATE_MOVING:
            # Step A: Steer toward target waypoint
            target_wp = self.route.get_waypoint(self.current_wp_idx)
            dx = target_wp.pos.x - self.pos.x
            dy = target_wp.pos.y - self.pos.y
            dist_to_wp = math.sqrt(dx * dx + dy * dy)

            if dist_to_wp > 0.001:
                dir_x = dx / dist_to_wp
                dir_y = dy / dist_to_wp
                self.vel.x = dir_x * effective_speed
                self.vel.y = dir_y * effective_speed
                self.target_heading = math.atan2(dir_y, dir_x)
            else:
                self.vel.x = 0.0
                self.vel.y = 0.0

            # Step B: Check Arrival Threshold (Hysteresis)
            if dist_to_wp <= target_wp.arrival_radius:
                self.pos.x = target_wp.pos.x
                self.pos.y = target_wp.pos.y
                self.vel.x = 0.0
                self.vel.y = 0.0

                # Transition to WAITING / SCANNING
                self.state = STATE_WAITING
                self.state_timer = target_wp.wait_time
                self.scan_idx = 0
                if target_wp.scan_angles:
                    self.target_heading = target_wp.scan_angles[0]

        elif self.state == STATE_WAITING:
            self.vel.x = 0.0
            self.vel.y = 0.0
            self.state_timer -= dt

            target_wp = self.route.get_waypoint(self.current_wp_idx)
            scans = target_wp.scan_angles

            # Rotate through inspection angles if provided
            if scans and len(scans) > 1:
                interval = target_wp.wait_time / float(len(scans))
                idx = int((target_wp.wait_time - self.state_timer) / interval)
                idx = max(0, min(len(scans) - 1, idx))
                self.target_heading = scans[idx]

            # Wait completed -> Depart to next waypoint
            if self.state_timer <= 0.0:
                next_idx, new_dir = self.route.advance_index(self.current_wp_idx, self.direction)
                self.current_wp_idx = next_idx
                self.direction = new_dir
                self.state = STATE_MOVING

        elif self.state == STATE_INVESTIGATING:
            # Halt and face last known disturbance
            self.vel.x = 0.0
            self.vel.y = 0.0
            dx = self.investigate_pos.x - self.pos.x
            dy = self.investigate_pos.y - self.pos.y
            if math.sqrt(dx * dx + dy * dy) > 1.0:
                self.target_heading = math.atan2(dy, dx)

            self.state_timer -= dt
            if self.state_timer <= 0.0 and self.alert_level < 0.2:
                # Return to patrol route
                self.state = STATE_MOVING

        # Smooth orientation interpolation
        self.heading = smooth_rotate_rad(self.heading, self.target_heading, self.turn_speed, dt)

        # Integrate translation
        self.pos.x += self.vel.x * dt
        self.pos.y += self.vel.y * dt

    def _check_vision(self, target_pos: Vector2, obstacles: list) -> bool:
        """Evaluates whether target_pos is inside vision cone and unobstructed."""
        dx = target_pos.x - self.pos.x
        dy = target_pos.y - self.pos.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist > self.vision_range or dist < 0.001:
            return False

        angle_to_target = math.atan2(dy, dx)
        angle_diff = abs(wrap_angle_rad(angle_to_target - self.heading))

        if angle_diff > (self.vision_fov_rad * 0.5):
            return False

        # Raycast against obstacle AABB crates
        for obs in obstacles:
            if segment_intersects_aabb_2d(self.pos, target_pos, obs.min_pos, obs.max_pos):
                return False

        return True


class ObstacleCrate:
    """Solid cover obstacle blocking movement and line of sight."""
    def __init__(self, x: float, y: float, w: float, h: float, label: str = "Crate"):
        self.min_pos = Vector2(x, y)
        self.max_pos = Vector2(x + w, y + h)
        self.w = w
        self.h = h
        self.label = label


class DataTerminal:
    """Interactive objective terminal that the operative must hack."""
    def __init__(self, x: float, y: float, label: str):
        self.pos = Vector2(x, y)
        self.label = label
        self.download_progress = 0.0  # 0.0 to 1.0
        self.is_hacked = False


class PlayerOperative:
    """The stealth operative sneaking through the compound."""
    def __init__(self, x: float, y: float):
        self.pos = Vector2(x, y)
        self.vel = Vector2(0.0, 0.0)
        self.heading = -math.pi * 0.5  # Facing North
        self.sneak_speed = 125.0
        self.sprint_speed = 210.0
        self.is_sprinting = False
        self.anim_timer = 0.0
        self.radius = 16.0

    def update(self, dt: float, move_vec: Vector2, sprint_held: bool, obstacles: list):
        self.is_sprinting = sprint_held and (abs(move_vec.x) > 0.1 or abs(move_vec.y) > 0.1)
        speed = self.sprint_speed if self.is_sprinting else self.sneak_speed

        input_len = math.sqrt(move_vec.x * move_vec.x + move_vec.y * move_vec.y)
        if input_len > 0.001:
            self.anim_timer += dt
            dir_x = move_vec.x / input_len
            dir_y = move_vec.y / input_len
            self.vel.x = dir_x * speed
            self.vel.y = dir_y * speed
            self.heading = math.atan2(dir_y, dir_x)
        else:
            self.vel.x = 0.0
            self.vel.y = 0.0

        # Collision & movement resolution against obstacles
        new_x = self.pos.x + self.vel.x * dt
        new_y = self.pos.y + self.vel.y * dt

        # Resolve X axis
        blocked_x = False
        for obs in obstacles:
            if (new_x + self.radius > obs.min_pos.x and new_x - self.radius < obs.max_pos.x and
                self.pos.y + self.radius > obs.min_pos.y and self.pos.y - self.radius < obs.max_pos.y):
                blocked_x = True
                break
        if not blocked_x:
            self.pos.x = new_x

        # Resolve Y axis
        blocked_y = False
        for obs in obstacles:
            if (self.pos.x + self.radius > obs.min_pos.x and self.pos.x - self.radius < obs.max_pos.x and
                new_y + self.radius > obs.min_pos.y and new_y - self.radius < obs.max_pos.y):
                blocked_y = True
                break
        if not blocked_y:
            self.pos.y = new_y

        # Clamp inside compound boundary
        self.pos.x = max(36.0, min(1244.0, self.pos.x))
        self.pos.y = max(72.0, min(692.0, self.pos.y))


# ==============================================================================
# BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY ([Tab] & [F1])
# ==============================================================================

def draw_xray_hud(guards: list, traversal_mode: int, speed_mode: float,
                  show_vision_style: int, terminals_hacked: int, total_terminals: int):
    """
    Renders pedagogical mathematical telemetry overlay breaking down waypoint
    indices, traversal topology, arrival hysteresis, and observation scan states.
    """
    panel_x = 24
    panel_y = 65
    panel_w = 380
    panel_h = 490

    draw_rectangle(panel_x, panel_y, panel_w, panel_h, Color(10, 14, 24, 235))
    draw_rectangle_lines(panel_x, panel_y, panel_w, panel_h, Color(45, 75, 125, 255))
    draw_rectangle(panel_x, panel_y, panel_w, 28, Color(22, 34, 58, 255))
    draw_text("X-RAY TELEMETRY & PATROL INSPECTOR [Tab]", panel_x + 12, panel_y + 7, 12, Color(0, 225, 255, 255))

    y = panel_y + 36
    lh = 16

    # 1. Traversal Mode & Global Parameters
    trav_name = "LOOP / CIRCUIT (Wrap 0..N-1)" if traversal_mode == TRAVERSAL_LOOP else "PING-PONG (Reverse at Ends)"
    trav_col = Color(0, 240, 255, 255) if traversal_mode == TRAVERSAL_LOOP else Color(255, 180, 50, 255)
    draw_text(f"[F1] Traversal Mode : {trav_name}", panel_x + 12, y, 11, trav_col); y += lh

    spd_name = "PATROL WALK (65 px/s)" if speed_mode <= 1.1 else "ALERT JOG (125 px/s)"
    draw_text(f"[F2] Guard Velocity : {spd_name}", panel_x + 12, y, 11, Color(200, 225, 255, 255)); y += lh
    draw_text(f"Mission Progress    : {terminals_hacked} / {total_terminals} Terminals Secured", panel_x + 12, y, 11, Color(255, 215, 0, 255)); y += lh

    draw_line(panel_x + 10, y + 2, panel_x + panel_w - 10, y + 2, Color(40, 65, 105, 200)); y += 8

    # 2. Guard Agent States
    draw_text("ACTIVE GUARD WAYPOINT AGENTS:", panel_x + 12, y, 11, Color(245, 210, 80, 255)); y += lh

    for g in guards:
        wp_target = g.route.get_waypoint(g.current_wp_idx)
        dx = wp_target.pos.x - g.pos.x
        dy = wp_target.pos.y - g.pos.y
        dist = math.sqrt(dx * dx + dy * dy)

        draw_text(f">> {g.name}:", panel_x + 12, y, 11, Color(225, 235, 255, 255)); y += lh

        state_col = Color(80, 255, 140, 255) if g.state == STATE_MOVING else (
            Color(255, 200, 50, 255) if g.state == STATE_WAITING else Color(255, 70, 70, 255)
        )
        draw_text(f"   State        : {STATE_NAMES[g.state]} (Timer: {g.state_timer:.1f}s)", panel_x + 14, y, 10, state_col); y += lh
        draw_text(f"   Target Node  : WP #{g.current_wp_idx} (Dist: {dist:.1f}px / Rad: {int(wp_target.arrival_radius)}px)",
                  panel_x + 14, y, 10, Color(175, 205, 235, 255)); y += lh
        draw_text(f"   Heading/Yaw  : {math.degrees(g.heading):+.0f} deg (Target: {math.degrees(g.target_heading):+.0f} deg)",
                  panel_x + 14, y, 10, Color(175, 205, 235, 255)); y += lh

        # Alert level progress bar
        alert_col = Color(80, 255, 120, 255) if g.alert_level < 0.4 else (
            Color(255, 200, 40, 255) if g.alert_level < 0.7 else Color(255, 50, 50, 255)
        )
        bar_w = 120
        draw_text(f"   Alert Meter  : {int(g.alert_level * 100)}%", panel_x + 14, y, 10, alert_col)
        draw_rectangle(panel_x + 150, y + 2, bar_w, 8, Color(20, 30, 45, 255))
        draw_rectangle(panel_x + 150, y + 2, int(bar_w * g.alert_level), 8, alert_col)
        y += lh + 2

    draw_line(panel_x + 10, y + 2, panel_x + panel_w - 10, y + 2, Color(40, 65, 105, 200)); y += 8

    # 3. Core Equations Reference
    draw_text("CORE PATTERN FORMULAS (C++ TRANSFERABLE):", panel_x + 12, y, 10, Color(140, 180, 230, 255)); y += lh
    draw_text("1. Arrival Test : ||Pos - WP[idx]|| <= ArrivalRadius", panel_x + 14, y, 9, Color(200, 225, 255, 200)); y += lh
    draw_text("2. Next (Loop)  : next_idx = (idx + 1) % NodeCount", panel_x + 14, y, 9, Color(200, 225, 255, 200)); y += lh
    draw_text("3. Angular Damping: diff = wrap_rad(target - current)", panel_x + 14, y, 9, Color(200, 225, 255, 200)); y += lh


def draw_vision_cone(guard: GuardAgent, style: int):
    """Renders the guard's field-of-view sensory cone."""
    if style == 0:
        return

    cx = int(guard.pos.x)
    cy = int(guard.pos.y)
    r = guard.vision_range
    fov = guard.vision_fov_rad
    half_fov = fov * 0.5

    # Cone color shifts with suspicion
    if guard.alert_level >= 0.7:
        cone_col = Color(255, 50, 50, 65)
        wire_col = Color(255, 70, 70, 200)
    elif guard.alert_level >= 0.3:
        cone_col = Color(255, 200, 40, 50)
        wire_col = Color(255, 215, 60, 180)
    else:
        cone_col = Color(0, 210, 255, 35)
        wire_col = Color(0, 230, 255, 140)

    # Arc slice vertices
    segments = 14
    pts = [Vector2(float(cx), float(cy))]
    for i in range(segments + 1):
        ang = guard.heading - half_fov + (fov * (i / float(segments)))
        px = cx + math.cos(ang) * r
        py = cy + math.sin(ang) * r
        pts.append(Vector2(px, py))

    # Draw shaded vision fan
    if style >= 1:
        for i in range(1, len(pts) - 1):
            draw_triangle(pts[0], pts[i + 1], pts[i], cone_col)

    # Outline whiskers
    p_left = pts[1]
    p_right = pts[-1]
    draw_line(cx, cy, int(p_left.x), int(p_left.y), wire_col)
    draw_line(cx, cy, int(p_right.x), int(p_right.y), wire_col)


# ==============================================================================
# BLOCK 4: MAIN GAME LOOP & AUTOMATED SMOKE TEST
# ==============================================================================

class GuardRouteLab:
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()

        self.sfx = SoundLibrary()
        self.sfx.init_defaults()

        self.show_xray = True
        self.traversal_mode = TRAVERSAL_LOOP
        self.speed_multiplier = 1.0
        self.vision_cone_style = 2  # 0: Off, 1: Solid Fan, 2: Fan + Outlines

        # World Entities
        self.player = PlayerOperative(640.0, 660.0)
        self.obstacles = []
        self._init_compound_layout()

        # Build Guard Patrol Routes
        self.guards = []
        self._init_patrol_guards()

        # Mission Objectives (Data Terminals)
        self.terminals = []
        self._init_terminals()

    def _init_compound_layout(self):
        """Constructs security compound warehouse crates and interior partitions."""
        # Perimeter Border Walls
        self.obstacles.append(ObstacleCrate(20.0, 56.0, 1240.0, 14.0, "North Perimeter Wall"))
        self.obstacles.append(ObstacleCrate(20.0, 696.0, 1240.0, 14.0, "South Perimeter Wall"))
        self.obstacles.append(ObstacleCrate(18.0, 56.0, 14.0, 654.0, "West Perimeter Wall"))
        self.obstacles.append(ObstacleCrate(1248.0, 56.0, 14.0, 654.0, "East Perimeter Wall"))

        # Sector Partition Crate Stacks
        # West Courtyard Partition
        self.obstacles.append(ObstacleCrate(240.0, 200.0, 70.0, 180.0, "Cargo Stack West A"))
        self.obstacles.append(ObstacleCrate(120.0, 480.0, 140.0, 60.0, "Supply Pallet West B"))

        # Central Divider & Hallway Columns
        self.obstacles.append(ObstacleCrate(440.0, 70.0, 40.0, 280.0, "Security Barrier Central N"))
        self.obstacles.append(ObstacleCrate(440.0, 450.0, 40.0, 250.0, "Security Barrier Central S"))

        # East High-Security Vault Walls
        self.obstacles.append(ObstacleCrate(680.0, 220.0, 160.0, 50.0, "Server Rack East A"))
        self.obstacles.append(ObstacleCrate(960.0, 220.0, 160.0, 50.0, "Server Rack East B"))
        self.obstacles.append(ObstacleCrate(820.0, 420.0, 180.0, 70.0, "Vault Crate Central East"))

    def _init_patrol_guards(self):
        # ----------------------------------------------------------------------
        # ROUTE 1: West Courtyard Perimeter Circuit (4-Node Loop)
        # ----------------------------------------------------------------------
        wp_list_1 = [
            Waypoint(90.0, 130.0, wait_time=1.4, scan_angles=[0.0, math.pi * 0.5]),
            Waypoint(370.0, 130.0, wait_time=1.8, scan_angles=[math.pi * 0.5, math.pi]),
            Waypoint(370.0, 440.0, wait_time=1.5, scan_angles=[math.pi, -math.pi * 0.5]),
            Waypoint(90.0, 440.0, wait_time=2.0, scan_angles=[-math.pi * 0.5, 0.0])
        ]
        route_1 = PatrolRoute(wp_list_1, self.traversal_mode)
        guard_1 = GuardAgent(1, "Courtyard Sentinel", route_1, start_wp_idx=0, walk_speed=65.0)
        self.guards.append(guard_1)

        # ----------------------------------------------------------------------
        # ROUTE 2: Central Corridor Inspection (3-Node Ping-Pong Patrol)
        # ----------------------------------------------------------------------
        wp_list_2 = [
            Waypoint(540.0, 120.0, wait_time=1.8, scan_angles=[math.pi * 0.5, 0.0]),
            Waypoint(540.0, 370.0, wait_time=0.8, scan_angles=[math.pi, 0.0]),
            Waypoint(540.0, 620.0, wait_time=2.2, scan_angles=[-math.pi * 0.5, -math.pi * 0.25])
        ]
        route_2 = PatrolRoute(wp_list_2, self.traversal_mode)
        guard_2 = GuardAgent(2, "Corridor Officer", route_2, start_wp_idx=1, walk_speed=72.0)
        self.guards.append(guard_2)

        # ----------------------------------------------------------------------
        # ROUTE 3: East Vault Perimeter (4-Node Tactical Sweep)
        # ----------------------------------------------------------------------
        wp_list_3 = [
            Waypoint(720.0, 140.0, wait_time=1.2, scan_angles=[0.0, math.pi * 0.5]),
            Waypoint(1180.0, 140.0, wait_time=1.5, scan_angles=[math.pi * 0.5, math.pi]),
            Waypoint(1180.0, 580.0, wait_time=2.0, scan_angles=[math.pi, -math.pi * 0.5]),
            Waypoint(720.0, 580.0, wait_time=1.6, scan_angles=[-math.pi * 0.5, 0.0])
        ]
        route_3 = PatrolRoute(wp_list_3, self.traversal_mode)
        guard_3 = GuardAgent(3, "Vault Enforcer", route_3, start_wp_idx=2, walk_speed=68.0)
        self.guards.append(guard_3)

    def _init_terminals(self):
        self.terminals.append(DataTerminal(140.0, 120.0, "Terminal Alpha (Courtyard)"))
        self.terminals.append(DataTerminal(540.0, 360.0, "Terminal Bravo (Corridor Relay)"))
        self.terminals.append(DataTerminal(900.0, 140.0, "Terminal Gamma (Master Vault)"))

    def handle_input(self, dt: float):
        # Pattern & Inspector Toggles
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
            self.sfx.play("click", 0.6)

        if is_dual_pattern_toggle_pressed():
            self.traversal_mode = TRAVERSAL_PING_PONG if self.traversal_mode == TRAVERSAL_LOOP else TRAVERSAL_LOOP
            for g in self.guards:
                g.route.traversal_mode = self.traversal_mode
            self.sfx.play("coin" if self.traversal_mode == TRAVERSAL_LOOP else "powerup", 0.7)

        if is_dual_secondary_toggle_pressed():
            self.speed_multiplier = 1.9 if self.speed_multiplier <= 1.1 else 1.0
            self.sfx.play("click", 0.6)

        if is_key_pressed(KEY_ONE):
            self.vision_cone_style = 0
            self.sfx.play("click", 0.5)
        elif is_key_pressed(KEY_TWO):
            self.vision_cone_style = 1
            self.sfx.play("click", 0.5)
        elif is_key_pressed(KEY_THREE):
            self.vision_cone_style = 2
            self.sfx.play("click", 0.5)

        # Reset Simulation
        if is_dual_reset_pressed():
            self.player.pos = Vector2(640.0, 660.0)
            self.player.vel = Vector2(0.0, 0.0)
            for t in self.terminals:
                t.download_progress = 0.0
                t.is_hacked = False
            for g in self.guards:
                g.current_wp_idx = 0
                g.alert_level = 0.0
                g.state = STATE_MOVING
                wp = g.route.get_waypoint(0)
                g.pos = Vector2(wp.pos.x, wp.pos.y)
            self.sfx.play("powerup", 0.7)

        # Player Movement (WASD + Gamepad Left Stick)
        move_input = get_dual_move_2d(deadzone=0.18, use_arrow_keys=True)
        sprint_held = is_key_down(KEY_LEFT_SHIFT) or is_key_down(KEY_RIGHT_SHIFT) or is_gamepad_button_down(0, GAMEPAD_BUTTON_RIGHT_FACE_RIGHT)
        self.player.update(dt, move_input, sprint_held, self.obstacles)

        # Objective Hacking Interaction ([E] / Gamepad X)
        is_interact_held = is_key_down(KEY_E) or is_gamepad_button_down(0, GAMEPAD_BUTTON_RIGHT_FACE_LEFT)
        for term in self.terminals:
            if not term.is_hacked:
                dx = term.pos.x - self.player.pos.x
                dy = term.pos.y - self.player.pos.y
                if math.sqrt(dx * dx + dy * dy) <= 48.0:
                    if is_interact_held:
                        term.download_progress = min(1.0, term.download_progress + dt * 0.75)
                        if term.download_progress >= 1.0:
                            term.is_hacked = True
                            self.sfx.play("coin", 0.85)

    def update(self):
        dt = min(get_frame_time(), 0.05)
        self.handle_input(dt)

        # Update Guard AI Agents
        for g in self.guards:
            prev_alert = g.alert_level
            g.update(dt, self.speed_multiplier, self.player.pos, self.obstacles, self.player.is_sprinting)
            # Alarm chime when a guard hits maximum alert
            if prev_alert < 0.95 and g.alert_level >= 0.95:
                self.sfx.play("hurt", 0.75)

    def draw_world(self):
        """Renders compound floor, cover crates, waypoint paths, vision cones, and actors."""
        # 1. Floor & Grid Background
        draw_rectangle(20, 56, 1240, 654, Color(16, 20, 30, 255))

        # Subtle tactical tile lines
        for x in range(60, 1240, 60):
            draw_line(x, 56, x, 710, Color(24, 30, 44, 255))
        for y in range(80, 710, 60):
            draw_line(20, y, 1260, y, Color(24, 30, 44, 255))

        # 2. X-Ray Waypoint Paths & Arrival Rings
        if self.show_xray:
            route_colors = [
                Color(0, 220, 255, 180),
                Color(255, 180, 50, 180),
                Color(180, 120, 255, 180)
            ]
            for r_idx, g in enumerate(self.guards):
                col = route_colors[r_idx % len(route_colors)]
                wps = g.route.waypoints
                count = len(wps)

                # Draw connecting route lines
                for i in range(count):
                    p1 = wps[i].pos
                    if g.route.traversal_mode == TRAVERSAL_LOOP:
                        p2 = wps[(i + 1) % count].pos
                    else:
                        if i < count - 1:
                            p2 = wps[i + 1].pos
                        else:
                            continue
                    draw_line_ex(p1, p2, 2.0, Color(col.r, col.g, col.b, 75))

                # Draw waypoint nodes and arrival threshold circles
                for i, wp in enumerate(wps):
                    is_active = (g.current_wp_idx == i)
                    node_col = Color(255, 220, 40, 255) if is_active else col

                    # Arrival threshold ring
                    draw_circle_lines(int(wp.pos.x), int(wp.pos.y), wp.arrival_radius, Color(node_col.r, node_col.g, node_col.b, 60))
                    # Center waypoint bead
                    draw_circle(int(wp.pos.x), int(wp.pos.y), 6.0, node_col)
                    # Node label
                    draw_text(f"W{i}", int(wp.pos.x) - 7, int(wp.pos.y) - 18, 10, Color(220, 235, 255, 200))

                    # Observation scan angle indicator whiskers
                    for scan_a in wp.scan_angles:
                        sx = wp.pos.x + math.cos(scan_a) * 22.0
                        sy = wp.pos.y + math.sin(scan_a) * 22.0
                        draw_line(int(wp.pos.x), int(wp.pos.y), int(sx), int(sy), Color(node_col.r, node_col.g, node_col.b, 120))

        # 3. Vision Cones
        for g in self.guards:
            draw_vision_cone(g, self.vision_cone_style)

        # 4. Obstacle Crates & Walls
        for obs in self.obstacles:
            bx = int(obs.min_pos.x)
            by = int(obs.min_pos.y)
            bw = int(obs.w)
            bh = int(obs.h)
            draw_rectangle(bx, by, bw, bh, Color(35, 42, 58, 255))
            draw_rectangle_lines(bx, by, bw, bh, Color(60, 75, 105, 255))
            # Diagonal crate bracing
            if bw > 30 and bh > 30:
                draw_line(bx, by, bx + bw, by + bh, Color(25, 30, 42, 255))
                draw_line(bx + bw, by, bx, by + bh, Color(25, 30, 42, 255))

        # 5. Data Terminals
        for term in self.terminals:
            tx = int(term.pos.x)
            ty = int(term.pos.y)
            t_col = Color(80, 255, 140, 255) if term.is_hacked else Color(0, 200, 255, 255)

            draw_circle(tx, ty, 14.0, Color(20, 32, 50, 255))
            draw_circle_lines(tx, ty, 14.0, t_col)
            draw_rectangle(tx - 6, ty - 6, 12, 12, t_col)

            # Download progress circle ring
            if term.download_progress > 0.0 and not term.is_hacked:
                pct = int(term.download_progress * 100)
                draw_text(f"{pct}%", tx - 12, ty - 24, 10, Color(255, 215, 0, 255))
            elif term.is_hacked:
                draw_text("HACKED", tx - 18, ty - 24, 10, Color(80, 255, 140, 255))
            else:
                draw_text("[E] HACK", tx - 20, ty - 24, 10, Color(160, 210, 255, 200))

        # 6. Guard Agents
        for g in self.guards:
            draw_humanoid_enemy_2d(g.pos, facing_angle_rad=g.heading, anim_timer=g.anim_timer, scale=1.1)

            # Alert status icon above head
            if g.alert_level >= 0.7:
                draw_text("!", int(g.pos.x) - 4, int(g.pos.y) - 34, 18, Color(255, 60, 60, 255))
            elif g.alert_level >= 0.3:
                draw_text("?", int(g.pos.x) - 4, int(g.pos.y) - 34, 16, Color(255, 200, 40, 255))

        # 7. Player Operative
        px = int(self.player.pos.x)
        py = int(self.player.pos.y)
        draw_circle(px, py, self.player.radius, Color(30, 85, 140, 255))
        draw_circle_lines(px, py, self.player.radius, Color(70, 185, 255, 255))

        # Direction indicator nose
        nx = px + math.cos(self.player.heading) * (self.player.radius + 6.0)
        ny = py + math.sin(self.player.heading) * (self.player.radius + 6.0)
        draw_line(px, py, int(nx), int(ny), Color(255, 255, 255, 255))

        # Footstep noise circle when sprinting
        if self.player.is_sprinting:
            draw_circle_lines(px, py, 110.0, Color(255, 200, 50, 45))

    def draw_hud(self):
        # Top-Left Pattern Banner
        banner_x = 24
        banner_y = 16
        draw_rectangle(banner_x, banner_y, 400, 40, Color(14, 18, 30, 230))
        draw_rectangle_lines(banner_x, banner_y, 400, 40, Color(45, 65, 105, 255))

        trav_str = "LOOP / CIRCUIT" if self.traversal_mode == TRAVERSAL_LOOP else "PING-PONG REVERSAL"
        draw_text(f"PATTERN: WAYPOINT PATROL [{trav_str}]", banner_x + 12, banner_y + 6, 12, Color(0, 240, 255, 255))
        draw_text("Graph Traversal | Arrival Hysteresis | Look-Around Sweeps", banner_x + 12, banner_y + 22, 10, Color(180, 215, 245, 255))

        # Bottom-Right Control Quick-Reference
        ctl_w = 340
        ctl_h = 105
        ctl_x = SCREEN_WIDTH - ctl_w - 24
        ctl_y = SCREEN_HEIGHT - ctl_h - 18
        draw_rectangle(ctl_x, ctl_y, ctl_w, ctl_h, Color(12, 16, 26, 225))
        draw_rectangle_lines(ctl_x, ctl_y, ctl_w, ctl_h, Color(45, 65, 100, 255))

        cy = ctl_y + 8
        draw_text("INTERACTIVE LAB CONTROLS:", ctl_x + 10, cy, 11, Color(0, 220, 255, 255)); cy += 16
        draw_text("[F1] / Gamepad LB : Toggle Mode (Loop vs Ping-Pong)", ctl_x + 10, cy, 10, Color(200, 220, 245, 255)); cy += 14
        draw_text("[F2] / Gamepad RB : Toggle Guard Speed (Walk vs Jog)", ctl_x + 10, cy, 10, Color(200, 220, 245, 255)); cy += 14
        draw_text("[E] / Gamepad X   : Hold to Hack Nearby Terminal", ctl_x + 10, cy, 10, Color(200, 220, 245, 255)); cy += 14
        draw_text("[Shift] / Pad B   : Sprint (Fast, but creates sound)", ctl_x + 10, cy, 10, Color(200, 220, 245, 255)); cy += 14
        draw_text("[Tab] / Pad Select: Toggle X-Ray Telemetry Overlay", ctl_x + 10, cy, 10, Color(255, 215, 0, 255))

        # X-Ray Overlay Panel
        if self.show_xray:
            hacked_count = sum(1 for t in self.terminals if t.is_hacked)
            draw_xray_hud(self.guards, self.traversal_mode, self.speed_multiplier,
                          self.vision_cone_style, hacked_count, len(self.terminals))

    def draw(self):
        begin_drawing()
        clear_background(Color(10, 13, 22, 255))

        self.draw_world()
        self.draw_hud()

        # Global Top-Bar Settings & Gamepad Badge
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
    GuardRouteLab().run(smoke_test=is_smoke)

