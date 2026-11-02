# -*- coding: utf-8 -*-
"""
Platformer Feel - Coyote Time, Jump Buffering & Variable Jump Height
====================================================================
Section          : 3.6 Movement & Camera
Pattern Category : Movement & Camera
Dimension        : 2D

Problem Solved:
  Pure Newtonian physics in platformer games feels stiff, unresponsive, and unfair.
  Human reaction times mean players frequently press the jump button a fraction of a
  second after running off a cliff (falling without jumping) or a fraction of a second
  before their feet touch the ground (input dropped). Furthermore, fixed jump impulses
  prevent micro-adjustments under low ceilings, constant gravity creates floaty/sluggish
  parabolic arcs, and clipping a ceiling corner by a few pixels kills all vertical momentum.

How the Patterns Work:
  1. Coyote Time (Hang-Time Forgiveness):
     When the player leaves a ledge without jumping, a countdown timer (COYOTE_DURATION = 120ms)
     grants a brief grace period. A jump press inside this window executes a normal jump,
     preventing the dreaded "I pressed jump!" fall into a pit.
  2. Jump Buffering (Pre-Input Memory):
     Pressing jump while falling in mid-air stores the input in a buffer timer (BUFFER_DURATION = 140ms).
     If the player lands while the buffer is active, the jump executes instantly on the exact
     touchdown frame, chaining momentum seamlessly.
  3. Variable Jump Height (Early Release Cutoff):
     When releasing the jump button early during ascent (vy < 0), upward velocity is scaled down
     by a damping factor (e.g. vy *= 0.45). A light tap yields a low hop; holding grants full arc.
  4. Apex Float & Asymmetric Snappy Gravity:
     Gravity is split into 3 distinct phases: rising gravity (standard), apex float gravity
     (cut in half near peak |vy| < 90 px/s with a 1.25x horizontal control boost), and falling
     gravity (1.46x heavier for snappy, responsive descents instead of balloon floating).
  5. Corner Nudge / Ledge Assist:
     If the player's head clips the corner edge of an overhead ceiling by <= 10 pixels, the
     character is gently shifted horizontally around the obstacle, preserving upward momentum.

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - [A][D] / [Left][Right] / Gamepad Left Stick / D-Pad : Run left and right
  - [Space] / [W] / [Up] / Gamepad A                    : Jump (Tap for hop, Hold for full jump)
  - [M] / Gamepad Y                                     : Master Toggle: [MODERN RESPONSIVE] vs [RAW RIGID PHYSICS]
  - [F1] / [1] / Gamepad LB                             : Toggle Coyote Time: [ON (120ms)] vs [OFF]
  - [F2] / [2] / Gamepad RB                             : Toggle Jump Buffering: [ON (140ms)] vs [OFF]
  - [F3] / [3]                                          : Toggle Variable Jump Height: [ON] vs [OFF (Fixed Impulse)]
  - [F4] / [4]                                          : Toggle Apex Float & Asymmetric Gravity: [ON] vs [OFF (Constant)]
  - [F5] / [5]                                          : Toggle Corner Nudge / Ledge Assist: [ON] vs [OFF (Hard Bonk)]
  - [Tab] / Gamepad View (Select)                       : Toggle X-Ray Telemetry & Input Timeline Overlay
  - [Ctrl +/-]                                          : Increase / Decrease UI Font Size
  - [F11]                                               : Toggle Fullscreen
  - [R] / Gamepad Start                                 : Reset Player Position to Current Checkpoint
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
WINDOW_TITLE = "Platformer Feel - Jump Forgiveness & Kinematics (Raylib Pattern Lab)"

# Kinematic Movement Tuning Constants
WALK_SPEED = 300.0           # Maximum running speed (px/s)
ACCEL_GROUND = 2200.0        # Ground acceleration rate (px/s^2)
FRICTION_GROUND = 2600.0     # Ground stopping deceleration (px/s^2)
ACCEL_AIR = 1500.0           # Air control acceleration (px/s^2)
DRAG_AIR = 600.0             # Air control deceleration (px/s^2)

# Jump Kinematics Constants
JUMP_IMPULSE = -540.0        # Initial vertical launch speed (px/s, negative = upward)
MIN_JUMP_IMPULSE = -200.0    # Minimum vertical speed for short hop cutoff
GRAVITY_UP = 1500.0          # Standard ascent gravity (px/s^2)
GRAVITY_FALL = 2200.0        # Snappy descent gravity (1.46x heavier)
GRAVITY_APEX = 750.0         # Floating apex gravity (0.5x lighter)
APEX_VELOCITY_THRESH = 95.0  # Vertical velocity threshold for apex hang (|vy| < 95)
MAX_FALL_SPEED = 850.0       # Terminal fall velocity clamp

# Forgiveness Window Durations
COYOTE_DURATION = 0.12       # 120ms coyote window (~7.2 frames at 60fps)
JUMP_BUFFER_DURATION = 0.14  # 140ms jump buffer window (~8.4 frames at 60fps)
CORNER_NUDGE_DIST = 10.0     # Maximum ceiling corner overlap to auto-nudge (pixels)


# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATION (KINEMATIC CONTROLLER & FORGIVENESS)
# ==============================================================================

class JumpGhost:
    """
    Echo silhouette particle spawned along the jump trajectory.
    Visualizes the jump arc and apex hang time.
    """
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.w = 24.0
        self.h = 36.0
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.alpha = 0.0
        self.color = Color(0, 220, 255, 255)
        self.active = False


class TimelineRecord:
    """
    A single frame record in the scrolling input & forgiveness history graph.
    """
    def __init__(self):
        self.time = 0.0
        self.is_grounded = False
        self.jump_pressed = False
        self.coyote_active = False
        self.buffer_active = False
        self.jump_executed = False
        self.save_type = 0  # 0: None, 1: Coyote Save, 2: Buffer Save, 3: Corner Nudge Save


class PlatformerFeelController:
    """
    Core Kinematic 2D Platformer Character Controller with live-tunable forgiveness mechanics.
    All physics and forgiveness math are written in explicit, C++-transferable style.
    """
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.width = 24.0
        self.height = 36.0

        # State flags
        self.is_grounded = False
        self.was_grounded = False
        self.facing_right = True
        self.anim_timer = 0.0
        self.is_jumping = False

        # Forgiveness Timers
        self.coyote_timer = 0.0
        self.jump_buffer_timer = 0.0

        # Mechanic Toggles (Configurable live via F1-F5 or Master Preset)
        self.coyote_enabled = True
        self.jump_buffer_enabled = True
        self.variable_jump_enabled = True
        self.apex_float_enabled = True
        self.corner_nudge_enabled = True

        # Squash & Stretch Animation Rig
        self.scale_x = 1.0
        self.scale_y = 1.0

        # Jump Trail Ghost Pool (16 slots)
        self.ghost_pool = [JumpGhost() for _ in range(16)]
        self.ghost_timer = 0.0

        # Forgiveness Telemetry Counters (The "Aha!" metric)
        self.coyote_saves = 0
        self.buffer_saves = 0
        self.nudge_saves = 0
        self.total_jumps = 0

    def trigger_jump(self, was_coyote: bool, was_buffered: bool):
        """Executes jump launch and applies visual stretch."""
        self.vy = JUMP_IMPULSE
        self.is_grounded = False
        self.is_jumping = True
        self.coyote_timer = 0.0
        self.jump_buffer_timer = 0.0

        # Squash on launch: tall & thin
        self.scale_x = 0.72
        self.scale_y = 1.38

        self.total_jumps += 1
        if was_coyote:
            self.coyote_saves += 1
        if was_buffered:
            self.buffer_saves += 1

    def spawn_ghost(self):
        """Spawns an echo silhouette in the jump trail pool."""
        for g in self.ghost_pool:
            if not g.active:
                g.active = True
                g.x = self.x
                g.y = self.y
                g.w = self.width
                g.h = self.height
                g.scale_x = self.scale_x
                g.scale_y = self.scale_y
                g.alpha = 0.55
                # Color changes at apex to highlight apex hang time
                if abs(self.vy) < APEX_VELOCITY_THRESH:
                    g.color = Color(255, 215, 60, 255)  # Gold at apex
                elif self.vy < 0.0:
                    g.color = Color(0, 230, 255, 255)   # Cyan on ascent
                else:
                    g.color = Color(255, 120, 80, 255)  # Orange on descent
                break

    def update_ghosts(self, dt: float):
        for g in self.ghost_pool:
            if g.active:
                g.alpha -= dt * 2.8
                if g.alpha <= 0.0:
                    g.active = False

    def update_physics(self, dt: float, move_x: float, jump_pressed: bool,
                       jump_down: bool, platforms: list) -> int:
        """
        Advances the kinematic simulation by dt seconds.
        Returns a save_type code: 0=None, 1=Coyote Save, 2=Buffer Save, 3=Nudge Save.
        """
        save_type = 0
        jump_executed = False

        # ----------------------------------------------------------------------
        # 1. Update Forgiveness Timers
        # ----------------------------------------------------------------------
        # Jump Buffer: Remembers pre-landing button presses
        if jump_pressed:
            self.jump_buffer_timer = JUMP_BUFFER_DURATION if self.jump_buffer_enabled else 0.0
        elif self.jump_buffer_timer > 0.0:
            self.jump_buffer_timer = max(0.0, self.jump_buffer_timer - dt)

        # Coyote Time: Grants jump window after walking off ledges
        if self.is_grounded:
            self.coyote_timer = COYOTE_DURATION if self.coyote_enabled else 0.0
        elif self.coyote_timer > 0.0:
            self.coyote_timer = max(0.0, self.coyote_timer - dt)

        # ----------------------------------------------------------------------
        # 2. Evaluate Jump Execution (Standard vs Coyote vs Buffered)
        # ----------------------------------------------------------------------
        can_coyote_jump = (not self.is_grounded) and self.coyote_enabled and (self.coyote_timer > 0.0)
        has_jump_demand = jump_pressed or (self.jump_buffer_enabled and self.jump_buffer_timer > 0.0)

        if has_jump_demand:
            if self.is_grounded:
                # Normal jump from ground or Buffered jump landing
                is_buffered = (not jump_pressed) and (self.jump_buffer_timer > 0.0)
                self.trigger_jump(was_coyote=False, was_buffered=is_buffered)
                jump_executed = True
                if is_buffered:
                    save_type = 2
            elif can_coyote_jump:
                # Coyote jump: airborne off a ledge!
                self.trigger_jump(was_coyote=True, was_buffered=False)
                jump_executed = True
                save_type = 1

        # ----------------------------------------------------------------------
        # 3. Variable Jump Height: Early Cutoff on Button Release
        # ----------------------------------------------------------------------
        if self.variable_jump_enabled and self.is_jumping:
            if (not jump_down) and self.vy < 0.0:
                if self.vy < MIN_JUMP_IMPULSE:
                    # Cut upward momentum smoothly
                    self.vy = max(self.vy * 0.48, MIN_JUMP_IMPULSE)
                self.is_jumping = False

        # ----------------------------------------------------------------------
        # 4. Asymmetric Gravity & Apex Float
        # ----------------------------------------------------------------------
        horiz_speed_mult = 1.0
        if self.apex_float_enabled and abs(self.vy) < APEX_VELOCITY_THRESH:
            # Apex Float: Cut gravity in half at peak, grant extra air agility
            current_grav = GRAVITY_APEX
            horiz_speed_mult = 1.25
        elif self.vy > 0.0:
            # Snappy Fall: Heavy gravity on descent
            current_grav = GRAVITY_FALL
        else:
            # Standard Rise
            current_grav = GRAVITY_UP

        self.vy += current_grav * dt
        self.vy = min(self.vy, MAX_FALL_SPEED)

        # ----------------------------------------------------------------------
        # 5. Horizontal Running & Acceleration
        # ----------------------------------------------------------------------
        target_vx = move_x * WALK_SPEED * horiz_speed_mult
        if move_x != 0.0:
            self.facing_right = (move_x > 0.0)
            self.anim_timer += dt * 12.0
            accel = ACCEL_GROUND if self.is_grounded else ACCEL_AIR
            self.vx = approach(self.vx, target_vx, accel * dt)
        else:
            decel = FRICTION_GROUND if self.is_grounded else DRAG_AIR
            self.vx = approach(self.vx, 0.0, decel * dt)

        # ----------------------------------------------------------------------
        # 6. Axis X Collision & Corner Nudge Evaluation
        # ----------------------------------------------------------------------
        self.x += self.vx * dt
        p_left = self.x
        p_right = self.x + self.width
        p_top = self.y
        p_bot = self.y + self.height

        for plat in platforms:
            if plat.is_solid and not plat.is_hazard:
                # Check AABB overlap on X
                if (p_right > plat.x and p_left < plat.x + plat.w and
                    p_bot > plat.y and p_top < plat.y + plat.h):
                    if self.vx > 0.0:
                        self.x = plat.x - self.width
                        self.vx = 0.0
                    elif self.vx < 0.0:
                        self.x = plat.x + plat.w
                        self.vx = 0.0
                    p_left = self.x
                    p_right = self.x + self.width

        # ----------------------------------------------------------------------
        # 7. Axis Y Collision & Ceiling Corner Nudging
        # ----------------------------------------------------------------------
        self.y += self.vy * dt
        p_left = self.x
        p_right = self.x + self.width
        p_top = self.y
        p_bot = self.y + self.height
        self.was_grounded = self.is_grounded
        self.is_grounded = False

        for plat in platforms:
            if not plat.is_solid or plat.is_hazard:
                continue

            # Check AABB overlap
            if (p_right > plat.x and p_left < plat.x + plat.w and
                p_bot > plat.y and p_top < plat.y + plat.h):

                if self.vy > 0.0:
                    # Landing on platform top surface
                    self.y = plat.y - self.height
                    self.vy = 0.0
                    self.is_grounded = True
                    self.is_jumping = False

                    # Squash on landing
                    if not self.was_grounded:
                        self.scale_x = 1.35
                        self.scale_y = 0.65

                elif self.vy < 0.0:
                    # Rising into a ceiling block
                    nudged = False
                    if self.corner_nudge_enabled:
                        # Test if clipping left corner of ceiling obstacle
                        overlap_left = p_right - plat.x
                        overlap_right = (plat.x + plat.w) - p_left

                        if 0.0 < overlap_left <= CORNER_NUDGE_DIST:
                            # Nudge player left around the obstacle!
                            self.x = plat.x - self.width - 0.5
                            self.nudge_saves += 1
                            save_type = 3
                            nudged = True
                        elif 0.0 < overlap_right <= CORNER_NUDGE_DIST:
                            # Nudge player right around the obstacle!
                            self.x = plat.x + plat.w + 0.5
                            self.nudge_saves += 1
                            save_type = 3
                            nudged = True

                    if not nudged:
                        # Hard head bonk on ceiling
                        self.y = plat.y + plat.h
                        self.vy = 0.0
                        self.is_jumping = False

        # ----------------------------------------------------------------------
        # 8. Squash & Stretch Damping & Trail Spawn
        # ----------------------------------------------------------------------
        self.scale_x = damp(self.scale_x, 1.0, 16.0, dt)
        self.scale_y = damp(self.scale_y, 1.0, 16.0, dt)

        # Spawn ghost silhouette during jump flight
        if not self.is_grounded:
            self.ghost_timer += dt
            if self.ghost_timer >= 0.05:
                self.ghost_timer = 0.0
                self.spawn_ghost()

        self.update_ghosts(dt)
        return save_type


# ==============================================================================
# BLOCK 2: WORLD SIMULATION & ENTITIES (LEVEL OBSTACLE COURSE)
# ==============================================================================

class LevelPlatform:
    """
    2D level geometry element with color and pedagogical purpose tag.
    """
    def __init__(self, x: float, y: float, w: float, h: float,
                 label: str = "", is_hazard: bool = False, is_solid: bool = True):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.label = label
        self.is_hazard = is_hazard
        self.is_solid = is_solid
        self.color = Color(38, 52, 78, 255)
        self.wire_color = Color(75, 110, 165, 255)


def build_obstacle_course() -> tuple:
    """
    Constructs an interactive pedagogical testing obstacle course:
    - Zone 1: Low-Ceiling Tunnel (Tests Variable Jump Height cutoff)
    - Zone 2: The Coyote Chasm (Tests Coyote Time ledge forgiveness)
    - Zone 3: Rapid Hurdle Rhythm (Tests Jump Buffering on consecutive landings)
    - Zone 4: Corner Nudge Shaft (Tests Ledge Assist around ceiling blocks)
    - Zone 5: Apex Float Canyon (Tests Apex Hang & Asymmetric Gravity)
    """
    platforms = []
    checkpoints = [
        Vector2(80.0, 480.0),    # Zone 1 Start
        Vector2(680.0, 480.0),   # Zone 2 Coyote Chasm
        Vector2(1380.0, 480.0),  # Zone 3 Hurdle Rhythm
        Vector2(2080.0, 480.0),  # Zone 4 Corner Nudge
        Vector2(2720.0, 480.0),  # Zone 5 Apex Canyon
    ]

    # Ground Baseline (Starting Platform)
    platforms.append(LevelPlatform(40.0, 520.0, 560.0, 60.0, "Zone 1: Variable Jump Range"))

    # Zone 1: Low Ceiling Overhang (Forces tap hop vs full jump)
    platforms.append(LevelPlatform(240.0, 390.0, 240.0, 24.0, "Low Ceiling [Tap to Hop]"))
    platforms.append(LevelPlatform(320.0, 492.0, 40.0, 28.0, "Hurdle"))

    # Zone 2: Coyote Chasm (Ledge gap test)
    # Ledge A -> 145px gap -> Ledge B
    platforms.append(LevelPlatform(660.0, 520.0, 260.0, 60.0, "Zone 2: Coyote Ledge"))
    platforms.append(LevelPlatform(1065.0, 520.0, 260.0, 60.0, "Coyote Landing Ledge"))
    # Safety Spring net below chasm
    platforms.append(LevelPlatform(660.0, 640.0, 665.0, 30.0, "Safety Spring Net", is_hazard=True))

    # Zone 3: Rapid Hurdle Rhythm (3 stepped pillars over gap)
    platforms.append(LevelPlatform(1360.0, 520.0, 180.0, 60.0, "Zone 3: Buffer Range"))
    platforms.append(LevelPlatform(1580.0, 490.0, 60.0, 90.0, "Pillar 1"))
    platforms.append(LevelPlatform(1700.0, 460.0, 60.0, 120.0, "Pillar 2"))
    platforms.append(LevelPlatform(1820.0, 430.0, 60.0, 150.0, "Pillar 3"))
    platforms.append(LevelPlatform(1940.0, 520.0, 180.0, 60.0, "Buffer Landing"))
    platforms.append(LevelPlatform(1360.0, 640.0, 760.0, 30.0, "Safety Net", is_hazard=True))

    # Zone 4: Corner Nudge Vertical Shaft
    platforms.append(LevelPlatform(2060.0, 520.0, 220.0, 60.0, "Zone 4: Corner Shaft"))
    # Overhead ceiling block with exact 10px overhang corners
    platforms.append(LevelPlatform(2340.0, 340.0, 120.0, 50.0, "Ceiling Block [Corner Nudge]"))
    platforms.append(LevelPlatform(2310.0, 440.0, 50.0, 20.0, "Step 1"))
    platforms.append(LevelPlatform(2450.0, 410.0, 50.0, 20.0, "Step 2"))
    platforms.append(LevelPlatform(2560.0, 520.0, 200.0, 60.0, "Nudge Landing"))

    # Zone 5: Apex Float Canyon (Long chasm reachable with apex hang)
    platforms.append(LevelPlatform(2700.0, 520.0, 240.0, 60.0, "Zone 5: Apex Chasm"))
    platforms.append(LevelPlatform(3140.0, 520.0, 360.0, 60.0, "Goal Platform"))
    platforms.append(LevelPlatform(2700.0, 640.0, 800.0, 30.0, "Safety Net", is_hazard=True))

    return platforms, checkpoints


# ==============================================================================
# BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY ([Tab] & [F1]-[F5])
# ==============================================================================

def draw_xray_hud(player: PlatformerFeelController, sample: TimelineRecord,
                  current_zone: str):
    """
    Renders live pedagogical telemetry comparing Modern Responsive feel vs Raw Rigid physics.
    """
    panel_x = 24
    panel_y = 65
    panel_w = 405
    panel_h = 495

    draw_rectangle(panel_x, panel_y, panel_w, panel_h, Color(10, 14, 24, 235))
    draw_rectangle_lines(panel_x, panel_y, panel_w, panel_h, Color(45, 75, 125, 255))
    draw_rectangle(panel_x, panel_y, panel_w, 28, Color(22, 34, 58, 255))
    draw_text("X-RAY FORGIVENESS & KINEMATICS [Tab]", panel_x + 12, panel_y + 7, 12, Color(0, 225, 255, 255))

    y = panel_y + 36
    lh = 16

    # 1. Master Preset Status
    all_on = (player.coyote_enabled and player.jump_buffer_enabled and
              player.variable_jump_enabled and player.apex_float_enabled and player.corner_nudge_enabled)
    all_off = (not player.coyote_enabled and not player.jump_buffer_enabled and
               not player.variable_jump_enabled and not player.apex_float_enabled and not player.corner_nudge_enabled)

    preset_name = "MODERN RESPONSIVE (Celeste/Mario)" if all_on else ("RAW RIGID (Stiff Physics)" if all_off else "CUSTOM MIXED")
    preset_col = Color(0, 240, 255, 255) if all_on else (Color(255, 120, 60, 255) if all_off else Color(255, 215, 60, 255))
    draw_text(f"[M] Master Preset   : {preset_name}", panel_x + 12, y, 11, preset_col); y += lh

    draw_line(panel_x + 10, y + 2, panel_x + panel_w - 10, y + 2, Color(40, 65, 105, 200)); y += 8

    # 2. Individual Mechanics Toggles
    draw_text("INDIVIDUAL FORGIVENESS MECHANICS:", panel_x + 12, y, 11, Color(245, 210, 80, 255)); y += lh

    c_stat = "ON (120ms)" if player.coyote_enabled else "OFF (0ms)"
    c_col = Color(100, 255, 160, 255) if player.coyote_enabled else Color(150, 165, 185, 255)
    draw_text(f"[F1]/[1] Coyote Time   : {c_stat}", panel_x + 12, y, 10, c_col); y += lh

    b_stat = "ON (140ms)" if player.jump_buffer_enabled else "OFF (0ms)"
    b_col = Color(100, 255, 160, 255) if player.jump_buffer_enabled else Color(150, 165, 185, 255)
    draw_text(f"[F2]/[2] Jump Buffer   : {b_stat}", panel_x + 12, y, 10, b_col); y += lh

    v_stat = "ON (Cutoff 48%)" if player.variable_jump_enabled else "OFF (Fixed Impulse)"
    v_col = Color(100, 255, 160, 255) if player.variable_jump_enabled else Color(150, 165, 185, 255)
    draw_text(f"[F3]/[3] Variable Jump : {v_stat}", panel_x + 12, y, 10, v_col); y += lh

    a_stat = "ON (0.5x Grav at Peak)" if player.apex_float_enabled else "OFF (Constant Grav)"
    a_col = Color(100, 255, 160, 255) if player.apex_float_enabled else Color(150, 165, 185, 255)
    draw_text(f"[F4]/[4] Apex Float    : {a_stat}", panel_x + 12, y, 10, a_col); y += lh

    n_stat = "ON (10px Assist)" if player.corner_nudge_enabled else "OFF (Hard Bonk)"
    n_col = Color(100, 255, 160, 255) if player.corner_nudge_enabled else Color(150, 165, 185, 255)
    draw_text(f"[F5]/[5] Corner Nudge  : {n_stat}", panel_x + 12, y, 10, n_col); y += lh

    draw_line(panel_x + 10, y + 2, panel_x + panel_w - 10, y + 2, Color(40, 65, 105, 200)); y += 8

    # 3. Live State Gauges
    draw_text("LIVE KINEMATIC STATE GAUGES:", panel_x + 12, y, 11, Color(245, 210, 80, 255)); y += lh

    ground_str = "GROUNDED (Solid Footing)" if player.is_grounded else "AIRBORNE (In Flight)"
    ground_col = Color(100, 255, 150, 255) if player.is_grounded else Color(255, 165, 60, 255)
    draw_text(f"Ground Contact      : {ground_str}", panel_x + 12, y, 10, ground_col); y += lh

    # Coyote Bar
    c_pct = min(1.0, player.coyote_timer / COYOTE_DURATION) if COYOTE_DURATION > 0 else 0.0
    c_bar_w = int(c_pct * 14)
    c_bar = "[" + "=" * c_bar_w + " " * (14 - c_bar_w) + "]"
    c_ms = int(player.coyote_timer * 1000.0)
    c_active = (player.coyote_timer > 0.0 and not player.is_grounded)
    c_label_col = Color(0, 240, 255, 255) if c_active else Color(160, 180, 200, 255)
    draw_text(f"Coyote Window       : {c_bar} {c_ms:3d}ms {'[ACTIVE!]' if c_active else ''}",
              panel_x + 12, y, 10, c_label_col); y += lh

    # Buffer Bar
    b_pct = min(1.0, player.jump_buffer_timer / JUMP_BUFFER_DURATION) if JUMP_BUFFER_DURATION > 0 else 0.0
    b_bar_w = int(b_pct * 14)
    b_bar = "[" + "=" * b_bar_w + " " * (14 - b_bar_w) + "]"
    b_ms = int(player.jump_buffer_timer * 1000.0)
    b_active = (player.jump_buffer_timer > 0.0)
    b_label_col = Color(255, 120, 240, 255) if b_active else Color(160, 180, 200, 255)
    draw_text(f"Jump Buffer Memory  : {b_bar} {b_ms:3d}ms {'[STORED!]' if b_active else ''}",
              panel_x + 12, y, 10, b_label_col); y += lh

    # Vertical Velocity & Gravity Mode
    grav_mode = "APEX FLOAT (750)" if (player.apex_float_enabled and abs(player.vy) < APEX_VELOCITY_THRESH) else (
        "SNAPPY FALL (2200)" if player.vy > 0.0 else "RISING (1500)")
    draw_text(f"Velocities (vx, vy) : vx = {player.vx:+.1f} | vy = {player.vy:+.1f} px/s",
              panel_x + 12, y, 10, Color(200, 225, 255, 255)); y += lh
    draw_text(f"Active Gravity Mode : {grav_mode}", panel_x + 12, y, 10, Color(255, 215, 100, 255)); y += lh

    draw_line(panel_x + 10, y + 2, panel_x + panel_w - 10, y + 2, Color(40, 65, 105, 200)); y += 8

    # 4. Forgiveness Saves (The "Aha!" Metric)
    draw_text("LIFETIME FORGIVENESS SAVES (The 'Aha!' Proof):", panel_x + 12, y, 11, Color(245, 210, 80, 255)); y += lh
    draw_text(f" * Coyote Ledge Saves  : {player.coyote_saves} jumps saved from falling into pits!",
              panel_x + 12, y, 10, Color(0, 240, 255, 255)); y += lh
    draw_text(f" * Pre-Landing Buffers : {player.buffer_saves} early inputs executed on touchdown!",
              panel_x + 12, y, 10, Color(255, 130, 240, 255)); y += lh
    draw_text(f" * Corner Nudge Saves  : {player.nudge_saves} head bonks converted to smooth climbs!",
              panel_x + 12, y, 10, Color(100, 255, 160, 255)); y += lh
    draw_text(f" * Total Jumps Launched: {player.total_jumps} jumps",
              panel_x + 12, y, 10, Color(220, 235, 255, 255)); y += lh


def draw_timeline(history: list, screen_w: int, screen_h: int):
    """
    Renders scrolling 4-second input and forgiveness timeline tape at the bottom of the screen.
    Visualizes Ground Contact, Jump Input, Coyote Windows, and Buffer Windows side-by-side.
    """
    tl_w = 640
    tl_h = 62
    tl_x = (screen_w - tl_w) // 2
    tl_y = screen_h - tl_h - 18

    # Panel frame
    draw_rectangle(tl_x, tl_y, tl_w, tl_h, Color(12, 16, 26, 235))
    draw_rectangle_lines(tl_x, tl_y, tl_w, tl_h, Color(45, 75, 125, 255))
    draw_text("INPUT & FORGIVENESS TIMELINE (Live 4-Second History)", tl_x + 10, tl_y - 16, 11, Color(255, 220, 80, 255))

    # Lane labels on left
    draw_text("JUMP", tl_x + 8, tl_y + 8, 9, Color(255, 215, 60, 255))
    draw_text("BUF", tl_x + 8, tl_y + 22, 9, Color(255, 120, 240, 255))
    draw_text("COY", tl_x + 8, tl_y + 34, 9, Color(0, 230, 255, 255))
    draw_text("GND", tl_x + 8, tl_y + 48, 9, Color(100, 255, 140, 255))

    tape_x = tl_x + 36
    tape_w = tl_w - 44
    num_samples = len(history)
    if num_samples < 2:
        return

    step_w = tape_w / max(1, num_samples - 1)

    # Draw timeline samples
    for i in range(num_samples):
        rec = history[i]
        sx = int(tape_x + i * step_w)

        # Ground lane
        if rec.is_grounded:
            draw_line(sx, tl_y + 52, sx + int(step_w) + 1, tl_y + 52, Color(80, 240, 120, 220))

        # Coyote lane
        if rec.coyote_active:
            draw_rectangle(sx, tl_y + 36, max(1, int(step_w)), 6, Color(0, 220, 255, 180))

        # Buffer lane
        if rec.buffer_active:
            draw_rectangle(sx, tl_y + 22, max(1, int(step_w)), 6, Color(240, 90, 220, 180))

        # Jump press marker (Yellow vertical tick)
        if rec.jump_pressed:
            draw_line(sx, tl_y + 6, sx, tl_y + 18, Color(255, 225, 40, 255))
            draw_circle(sx, tl_y + 8, 2.0, Color(255, 255, 100, 255))

        # Successful jump event star/circle
        if rec.jump_executed:
            draw_circle(sx, tl_y + 46, 3.5, Color(255, 255, 255, 255))
            if rec.save_type == 1:    # Coyote Save!
                draw_circle(sx, tl_y + 39, 4.0, Color(0, 240, 255, 255))
            elif rec.save_type == 2:  # Buffer Save!
                draw_circle(sx, tl_y + 25, 4.0, Color(255, 120, 240, 255))
            elif rec.save_type == 3:  # Nudge Save!
                draw_circle(sx, tl_y + 12, 4.0, Color(100, 255, 140, 255))


def draw_player_hero(player: PlatformerFeelController):
    """
    Renders geometric 2D platformer hero with dynamic squash-and-stretch.
    """
    # Echo ghosts
    for g in player.ghost_pool:
        if g.active:
            gw = int(g.w * g.scale_x)
            gh = int(g.h * g.scale_y)
            gx = int(g.x + (g.w - gw) * 0.5)
            gy = int(g.y + (g.h - gh))
            draw_rectangle_lines(gx, gy, gw, gh, Color(g.color.r, g.color.g, g.color.b, int(g.alpha * 255)))

    # Scaled dimensions anchored to feet
    w = player.width * player.scale_x
    h = player.height * player.scale_y
    draw_x = player.x + (player.width - w) * 0.5
    draw_y = player.y + (player.height - h)

    ix = int(draw_x)
    iy = int(draw_y)
    iw = int(w)
    ih = int(h)

    # Torso (Navy / Indigo hero armor)
    draw_rectangle(ix, iy, iw, ih, Color(35, 65, 120, 255))
    draw_rectangle_lines(ix, iy, iw, ih, Color(75, 135, 225, 255))

    # Glowing Headband / Visor slit facing look direction
    visor_w = int(iw * 0.55)
    visor_h = int(ih * 0.18)
    vx = ix + (int(iw * 0.4) if player.facing_right else int(iw * 0.05))
    vy = iy + int(ih * 0.18)
    draw_rectangle(vx, vy, visor_w, visor_h, Color(0, 240, 255, 255))

    # Headband scarf trail
    scarf_dir = -1 if player.facing_right else 1
    scarf_len = int(14.0 * player.scale_x)
    draw_line_ex(Vector2(vx + visor_w * 0.5, vy + visor_h * 0.5),
                 Vector2(vx + visor_w * 0.5 + scarf_dir * scarf_len, vy + visor_h * 0.5 + math.sin(player.anim_timer) * 3.0),
                 3.0, Color(0, 200, 240, 220))


# ==============================================================================
# BLOCK 4: MAIN GAME LOOP & AUTOMATED SMOKE TEST
# ==============================================================================

class PlatformerFeelLab:
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()

        self.sfx = SoundLibrary()
        self.sfx.init_defaults()

        self.show_xray = True

        # Build Obstacle Testing Course & Checkpoints
        self.platforms, self.checkpoints = build_obstacle_course()
        self.current_checkpoint_idx = 0

        # Initialize Player Controller at Checkpoint 1
        start_pt = self.checkpoints[0]
        self.player = PlatformerFeelController(start_pt.x, start_pt.y)

        # 2D Camera Follow Rig
        self.camera = Camera2D()
        self.camera.target = Vector2(self.player.x, self.player.y)
        self.camera.offset = Vector2(SCREEN_WIDTH * 0.38, SCREEN_HEIGHT * 0.58)
        self.camera.rotation = 0.0
        self.camera.zoom = 1.0

        # Live 4-Second Timeline History (240 samples at 60Hz)
        self.history_capacity = 240
        self.timeline_history = []

        # Current Zone Label
        self.current_zone = "Zone 1: Variable Jump Range"

    def handle_input(self):
        # 1. Master Preset Toggle ([M] / Gamepad Y)
        if is_key_pressed(KEY_M) or (is_gamepad_available(0) and is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_FACE_UP)):
            all_on = (self.player.coyote_enabled and self.player.jump_buffer_enabled and
                      self.player.variable_jump_enabled and self.player.apex_float_enabled and self.player.corner_nudge_enabled)
            new_state = not all_on
            self.player.coyote_enabled = new_state
            self.player.jump_buffer_enabled = new_state
            self.player.variable_jump_enabled = new_state
            self.player.apex_float_enabled = new_state
            self.player.corner_nudge_enabled = new_state
            self.sfx.play("powerup" if new_state else "hit", 0.7)

        # 2. Individual Mechanic Toggles ([F1]-[F5] or [1]-[5] or Gamepad LB/RB)
        if is_dual_pattern_toggle_pressed() or is_key_pressed(KEY_ONE):
            self.player.coyote_enabled = not self.player.coyote_enabled
            self.sfx.play("click", 0.5)

        if is_dual_secondary_toggle_pressed() or is_key_pressed(KEY_TWO):
            self.player.jump_buffer_enabled = not self.player.jump_buffer_enabled
            self.sfx.play("click", 0.5)

        if is_key_pressed(KEY_F3) or is_key_pressed(KEY_THREE):
            self.player.variable_jump_enabled = not self.player.variable_jump_enabled
            self.sfx.play("click", 0.5)

        if is_key_pressed(KEY_F4) or is_key_pressed(KEY_FOUR):
            self.player.apex_float_enabled = not self.player.apex_float_enabled
            self.sfx.play("click", 0.5)

        if is_key_pressed(KEY_F5) or is_key_pressed(KEY_FIVE):
            self.player.corner_nudge_enabled = not self.player.corner_nudge_enabled
            self.sfx.play("click", 0.5)

        # 3. X-Ray Toggle
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
            self.sfx.play("click", 0.6)

        # 4. Reset to Checkpoint ([R] / Gamepad Start)
        if is_dual_reset_pressed():
            cp = self.checkpoints[self.current_checkpoint_idx]
            self.player.x = cp.x
            self.player.y = cp.y
            self.player.vx = 0.0
            self.player.vy = 0.0
            self.sfx.play("coin", 0.6)

    def update(self):
        dt = min(get_frame_time(), 0.05)
        self.handle_input()

        # Movement Inputs (Dual Keyboard/Mouse + Gamepad)
        move_vec = get_dual_move_2d(deadzone=0.18, use_arrow_keys=True)
        jump_pressed = is_dual_jump_pressed()
        jump_down = is_dual_jump_down()

        # Update Kinematics & Forgiveness
        save_type = self.player.update_physics(dt, move_vec.x, jump_pressed, jump_down, self.platforms)
        if save_type == 1:
            self.sfx.play("jump", 0.75)  # Coyote Save!
        elif save_type == 2:
            self.sfx.play("jump", 0.75)  # Buffer Save!

        # Check Hazard Respawn (Falling into pit)
        for plat in self.platforms:
            if plat.is_hazard:
                p_r = self.player.x + self.player.width
                p_b = self.player.y + self.player.height
                if (p_r > plat.x and self.player.x < plat.x + plat.w and
                    p_b > plat.y and self.player.y < plat.y + plat.h):
                    # Bounce player back up to current checkpoint
                    cp = self.checkpoints[self.current_checkpoint_idx]
                    self.player.x = cp.x
                    self.player.y = cp.y
                    self.player.vx = 0.0
                    self.player.vy = -380.0
                    self.sfx.play("jump", 0.8)

        # Update Active Checkpoint
        for i, cp in enumerate(self.checkpoints):
            if abs(self.player.x - cp.x) < 90.0 and self.player.is_grounded:
                if i != self.current_checkpoint_idx:
                    self.current_checkpoint_idx = i
                    self.sfx.play("powerup", 0.5)

        # Record Timeline Sample
        rec = TimelineRecord()
        rec.time = get_time()
        rec.is_grounded = self.player.is_grounded
        rec.jump_pressed = jump_pressed
        rec.coyote_active = (self.player.coyote_timer > 0.0 and not self.player.is_grounded)
        rec.buffer_active = (self.player.jump_buffer_timer > 0.0)
        rec.jump_executed = (save_type > 0 or (jump_pressed and self.player.is_grounded))
        rec.save_type = save_type

        self.timeline_history.append(rec)
        if len(self.timeline_history) > self.history_capacity:
            self.timeline_history.pop(0)

        # Smooth Camera Follow with Damping
        target_cam_x = self.player.x + self.player.width * 0.5 + self.player.vx * 0.25
        target_cam_y = self.player.y - 40.0
        self.camera.target.x = damp(self.camera.target.x, target_cam_x, 8.0, dt)
        self.camera.target.y = damp(self.camera.target.y, target_cam_y, 6.0, dt)

    def draw(self):
        begin_drawing()
        # Dark slate atmospheric background
        clear_background(Color(14, 18, 28, 255))

        # 1. World Simulation inside Camera2D
        begin_mode_2d(self.camera)

        # Draw Level Platforms
        for plat in self.platforms:
            ix = int(plat.x)
            iy = int(plat.y)
            iw = int(plat.w)
            ih = int(plat.h)

            if plat.is_hazard:
                # Hazard Safety Spring Net
                draw_rectangle(ix, iy, iw, ih, Color(60, 25, 35, 230))
                draw_rectangle_lines(ix, iy, iw, ih, Color(220, 60, 70, 200))
                draw_text("[SAFETY NET]", ix + iw // 2 - 40, iy + 8, 10, Color(255, 120, 130, 200))
            else:
                draw_rectangle(ix, iy, iw, ih, plat.color)
                draw_rectangle_lines(ix, iy, iw, ih, plat.wire_color)
                # Platform header label
                if plat.label:
                    draw_text(plat.label, ix + 8, iy - 16, 11, Color(175, 200, 240, 230))

        # Draw Checkpoint Flags
        for i, cp in enumerate(self.checkpoints):
            is_active = (i == self.current_checkpoint_idx)
            flag_col = Color(0, 240, 255, 255) if is_active else Color(90, 115, 145, 180)
            cx = int(cp.x)
            cy = int(cp.y)
            draw_line(cx, cy + 36, cx, cy - 20, Color(180, 200, 225, 255))
            draw_triangle(
                Vector2(cx, cy - 20),
                Vector2(cx, cy - 6),
                Vector2(cx + 16, cy - 13),
                flag_col
            )
            draw_text(f"CP {i+1}", cx - 8, cy + 40, 9, flag_col)

        # Draw Player Hero
        draw_player_hero(self.player)

        end_mode_2d()

        # 2. Scrolling Input & Forgiveness Timeline Tape
        draw_timeline(self.timeline_history, SCREEN_WIDTH, SCREEN_HEIGHT)

        # 3. Top HUD Header & Controls (Keep x=450..980 clear for dropdowns)
        draw_rectangle(0, 0, SCREEN_WIDTH, 48, Color(12, 16, 26, 230))
        draw_rectangle(0, 48, SCREEN_WIDTH, 2, Color(40, 65, 105, 255))

        draw_text("PLATFORMER FEEL - Coyote Time, Jump Buffer & Variable Jump (2D)", 24, 12, 13, Color(240, 245, 255, 255))
        draw_text("A/D: Run | Space: Jump | [M]: Master Preset | [1]-[5]: Mechanics | [R]: Reset", 24, 28, 10, Color(150, 175, 205, 255))

        # Global Top-Bar UI Settings Bar & Gamepad Badge
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)

        # 4. X-Ray Telemetry Overlay ([Tab])
        if self.show_xray:
            sample = self.timeline_history[-1] if self.timeline_history else TimelineRecord()
            draw_xray_hud(self.player, sample, self.current_zone)

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
    PlatformerFeelLab().run(smoke_test=is_smoke)

