# -*- coding: utf-8 -*-
"""
Platformer Forgiveness Lab - Coyote Time, Jump Buffering & Corner Assist
=======================================================================
Section          : 3.6 Movement & Camera
Pattern Category : Movement & Camera (Kinematic Platformer Game Feel)
Dimension        : 2D

Problem Solved:
  In platformer games, strict rigid-body Newtonian physics (jumping only when strictly
  touching the ground, fixed impulse jumps, and instant velocity cancellation on corner clips)
  feels stiff, unresponsive, and punishing to human players. Visual reaction latency causes
  players to press jump 16-50ms after stepping off a ledge, dropping the input and plummeting.
  Similarly, pressing jump 30-100ms before touching a platform is discarded by strict physics.
  Furthermore, fixed jump heights prevent micro-hops under low hazards, constant gravity produces
  floaty parabolic arcs, and clipping an overhead ceiling corner by a few pixels kills all
  vertical momentum with a frustrating head-bonk.

How the Pattern Works:
  1. Coyote Time (Hang-Time Forgiveness):
     Maintains a grace timer (0.12s / ~7 frames) starting the exact frame the character steps
     off a platform into air. If the jump input arrives while the timer is active, the engine
     executes a full jump as if the player were still on solid ground.
  2. Jump Buffering (Pre-Input Queue):
     Stores jump inputs in an input memory cache (0.14s / ~8 frames) while airborne. If the
     character touches down while the buffer is active, the jump executes on the exact touchdown
     frame, enabling fluid, uninterrupted bunny-hopping rhythm.
  3. Variable Jump Height (Early Cutoff):
     When the player releases the jump button early during ascent (vy < 0), upward velocity is
     immediately scaled down (vy = max(vy * 0.45, -120.0)). This allows tapping the key for
     a low micro-hop while holding it executes a full high arc.
  4. Apex Float & Asymmetric Gravity:
     Near the peak of the jump (|vy| < 90 px/s), gravity is reduced by 50% and horizontal
     acceleration is boosted by 30%, giving the character satisfying hang-time control at the
     crest before heavy falling gravity kicks in for a snappy descent.
  5. Corner Ledge Nudge (Head Collision Assist):
     When the character's head clips an overhead ceiling corner by <= 8 pixels, upward feeler
     raycasts detect the narrow overlap and smoothly slide the character horizontally around
     the obstruction, preserving vertical momentum without head-bonking.

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - Movement (Run)                : A/D or Left/Right Arrow / Gamepad Left Stick / D-Pad
  - Jump                          : Space / Gamepad A (Cross) / RT / Up Arrow
  - Air Dash                      : Left/Right Shift / Gamepad X (Square) / LB
  - Toggle ALL Forgiveness (F1)   : [F1] / Gamepad R3 (Compare Commercial Feel vs Brutal Physics)
  - Toggle Coyote Time [1]        : [1] (Toggle 120ms ledge grace)
  - Toggle Jump Buffer [2]        : [2] (Toggle 140ms pre-landing buffer)
  - Toggle Variable Jump [3]      : [3] (Toggle early release velocity cutoff)
  - Toggle Apex Float [4]         : [4] (Toggle 50% gravity hang-time at peak)
  - Toggle Corner Nudge [5]       : [5] (Toggle 8px overhead corner assist)
  - Warp Sector [T]               : [T] / Gamepad D-Pad Left/Right (Jump to test zones 1-5)
  - Toggle X-Ray Overlay [Tab]    : [Tab] / Gamepad View (Select)
  - Reset / Respawn [R]           : [R] / Gamepad Start
  - [Ctrl +/-]                    : Increase / Decrease UI Font Size
  - [F11]                         : Toggle Fullscreen
"""

import sys
import os
import math
import random

# 1. Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# 2. Add repository root to search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# 3. Mandatory Raylib & modular imports
from pyray import *
from assets import *
from utils import *

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WINDOW_TITLE = "Platformer Forgiveness Lab - Coyote Time, Jump Buffering & Corner Assist (Raylib)"

# Palette Definitions for High-Contrast Pedagogical UI
COLOR_BG_DARK           = Color(11, 14, 23, 255)
COLOR_PANEL_BG          = Color(17, 23, 38, 235)
COLOR_PANEL_BORDER      = Color(42, 60, 95, 255)
COLOR_PANEL_HEADER      = Color(25, 36, 58, 255)

COLOR_TEXT_MAIN         = Color(235, 242, 255, 255)
COLOR_TEXT_DIM          = Color(140, 160, 190, 255)
COLOR_TEXT_HIGHLIGHT    = Color(255, 215, 65, 255)

COLOR_PLATFORM_SOLID    = Color(50, 65, 92, 255)
COLOR_PLATFORM_TRIM     = Color(90, 120, 165, 255)
COLOR_HAZARD_FILL       = Color(190, 45, 45, 255)
COLOR_HAZARD_TRIM       = Color(255, 80, 80, 255)
COLOR_BOUNCE_FILL       = Color(40, 175, 120, 255)
COLOR_BOUNCE_TRIM       = Color(80, 235, 165, 255)
COLOR_GOAL_FILL         = Color(215, 170, 35, 255)
COLOR_GOAL_TRIM         = Color(255, 225, 95, 255)

COLOR_PLAYER_BODY       = Color(65, 185, 255, 255)
COLOR_PLAYER_EYE        = Color(255, 255, 255, 255)
COLOR_PLAYER_OUTLINE    = Color(25, 110, 180, 255)

COLOR_METER_BG          = Color(22, 28, 42, 255)
COLOR_COYOTE_ACTIVE     = Color(65, 230, 130, 255)
COLOR_BUFFER_ACTIVE     = Color(65, 210, 255, 255)
COLOR_APEX_ACTIVE       = Color(255, 205, 55, 255)
COLOR_NUDGE_ACTIVE      = Color(245, 120, 220, 255)


# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATION
# ==============================================================================

class PlatformerForgivenessSettings:
    """
    Encapsulates all 5 forgiveness mechanics and their live tuning parameters.
    
    C++ Equivalent:
      struct PlatformerForgivenessSettings {
          bool coyote_enabled = true;
          bool jump_buffer_enabled = true;
          bool variable_jump_enabled = true;
          bool apex_float_enabled = true;
          bool corner_nudge_enabled = true;
          float coyote_time_max = 0.12f;
          float jump_buffer_max = 0.14f;
          float variable_jump_cutoff = 0.45f;
          float apex_vy_threshold = 90.0f;
          float apex_gravity_mult = 0.50f;
          float apex_accel_mult = 1.30f;
          float corner_nudge_dist = 8.0f;
      };
    """
    def __init__(self):
        # 1. Coyote Time: Allows jumping shortly after leaving a ledge
        self.coyote_enabled = True
        self.coyote_time_max = 0.12  # seconds (~7.2 frames at 60 FPS)

        # 2. Jump Buffering: Caches jump input shortly before touching ground
        self.jump_buffer_enabled = True
        self.jump_buffer_max = 0.14  # seconds (~8.4 frames at 60 FPS)

        # 3. Variable Jump Height: Scales upward velocity when button released early
        self.variable_jump_enabled = True
        self.variable_jump_cutoff = 0.45  # Velocity multiplier on early release

        # 4. Apex Float: Reduces gravity and boosts agility near arc peak
        self.apex_float_enabled = True
        self.apex_vy_threshold = 90.0  # px/s threshold for apex crest window
        self.apex_gravity_mult = 0.50  # 50% gravity reduction
        self.apex_accel_mult = 1.30    # 30% air steering boost

        # 5. Corner Ledge Nudge: Slides character around overhead ceiling corners
        self.corner_nudge_enabled = True
        self.corner_nudge_dist = 8.0   # Max pixels of corner overlap to assist

    def toggle_all(self, enabled: bool):
        """Sets all forgiveness mechanics ON or OFF simultaneously."""
        self.coyote_enabled = enabled
        self.jump_buffer_enabled = enabled
        self.variable_jump_enabled = enabled
        self.apex_float_enabled = enabled
        self.corner_nudge_enabled = enabled

    def are_all_enabled(self) -> bool:
        """Returns True if every forgiveness mechanic is currently enabled."""
        if not self.coyote_enabled:
            return False
        if not self.jump_buffer_enabled:
            return False
        if not self.variable_jump_enabled:
            return False
        if not self.apex_float_enabled:
            return False
        if not self.corner_nudge_enabled:
            return False
        return True

    def are_all_disabled(self) -> bool:
        """Returns True if every forgiveness mechanic is currently disabled."""
        if self.coyote_enabled:
            return False
        if self.jump_buffer_enabled:
            return False
        if self.variable_jump_enabled:
            return False
        if self.apex_float_enabled:
            return False
        if self.corner_nudge_enabled:
            return False
        return True

    def toggle_mechanic(self, index: int):
        """Toggles an individual forgiveness mechanic by 1-based index (1 to 5)."""
        if index == 1:
            self.coyote_enabled = not self.coyote_enabled
        elif index == 2:
            self.jump_buffer_enabled = not self.jump_buffer_enabled
        elif index == 3:
            self.variable_jump_enabled = not self.variable_jump_enabled
        elif index == 4:
            self.apex_float_enabled = not self.apex_float_enabled
        elif index == 5:
            self.corner_nudge_enabled = not self.corner_nudge_enabled


class ForgivenessEvent:
    """
    Struct representing a recorded forgiveness activation event for telemetry logging.
    """
    def __init__(self, message: str, color: Color):
        self.message = message
        self.color = color
        self.timer = 3.5  # Display duration in seconds
        self.max_timer = 3.5


class ForgivenessTelemetry:
    """
    Tracks live timing countdowns, kinematic meters, and recent activation events.
    
    C++ Equivalent:
      struct ForgivenessTelemetry {
          float coyote_timer = 0.0f;
          float jump_buffer_timer = 0.0f;
          bool is_in_apex = false;
          float apex_timer = 0.0f;
          float last_nudge_offset = 0.0f;
          int last_nudge_dir = 0;
          float nudge_visual_timer = 0.0f;
          std::vector<ForgivenessEvent> recent_events;
      };
    """
    def __init__(self):
        self.coyote_timer = 0.0
        self.jump_buffer_timer = 0.0
        self.is_in_apex = False
        self.apex_timer = 0.0
        self.last_nudge_offset = 0.0
        self.last_nudge_dir = 0  # -1 = slid left, +1 = slid right, 0 = none
        self.nudge_visual_timer = 0.0
        self.recent_events = []

    def log_event(self, message: str, color: Color):
        """Appends a new event and keeps the log bounded to the 4 most recent."""
        ev = ForgivenessEvent(message, color)
        self.recent_events.insert(0, ev)
        while len(self.recent_events) > 4:
            self.recent_events.pop()

    def update(self, dt: float):
        """Advances telemetry timers and cleans up expired log events."""
        if self.nudge_visual_timer > 0.0:
            self.nudge_visual_timer -= dt
            if self.nudge_visual_timer < 0.0:
                self.nudge_visual_timer = 0.0

        for ev in self.recent_events:
            ev.timer -= dt

        # Remove expired events
        survivors = []
        for ev in self.recent_events:
            if ev.timer > 0.0:
                survivors.append(ev)
        self.recent_events = survivors


class KinematicCharacterController:
    """
    Responsive 2D kinematic platformer character implementing all 5 forgiveness mechanics.
    
    Architectural Highlights:
      - Separate Horizontal / Vertical axis collision sweeps prevent corner tunneling.
      - Coyote Time window preserves ledge jump capability for human reaction tolerance.
      - Jump Buffer caches jump taps during airborne descent for rhythmic landing jumps.
      - Variable Jump Height cuts upward velocity on early button release for micro-hops.
      - Apex Float halves gravity and boosts horizontal agility near jump crest.
      - Corner Ledge Nudge casts upward feelers and smoothly slides around ceiling corners.
    """
    def __init__(self, start_x: float, start_y: float):
        # Position & Kinematic Vectors
        self.x = start_x
        self.y = start_y
        self.vx = 0.0
        self.vy = 0.0
        self.width = 24.0
        self.height = 36.0

        # Physical Constants (tuned for crisp commercial platformer feel)
        self.run_speed = 280.0
        self.ground_accel = 1900.0
        self.ground_friction = 2400.0
        self.air_accel = 1200.0
        self.air_friction = 350.0
        self.gravity_rise = 1350.0
        self.gravity_fall = 1950.0
        self.jump_impulse = -540.0
        self.max_fall_speed = 700.0

        # Air Dash Parameters
        self.dash_speed = 620.0
        self.dash_duration = 0.14
        self.dash_cooldown = 0.50
        self.dash_timer = 0.0
        self.dash_cooldown_timer = 0.0
        self.dash_dir_x = 1.0
        self.is_dashing = False

        # State Variables
        self.is_grounded = False
        self.was_grounded = False
        self.is_jumping = False
        self.facing_right = True
        self.air_time = 0.0
        self.jump_count = 0

        # Forgiveness Timers
        self.coyote_timer = 0.0
        self.jump_buffer_timer = 0.0

        # Visual Telemetry Markers
        self.coyote_ghost_x = 0.0
        self.coyote_ghost_y = 0.0
        self.coyote_ghost_active = False
        self.coyote_ghost_timer = 0.0

        # Feeler Offsets for Corner Nudge Visualizer
        self.feeler_left_hit = False
        self.feeler_right_hit = False
        self.nudge_marker_x = 0.0
        self.nudge_marker_y = 0.0

    def reset_position(self, spawn_x: float, spawn_y: float):
        """Resets kinematic state and teleports character to spawn."""
        self.x = spawn_x
        self.y = spawn_y
        self.vx = 0.0
        self.vy = 0.0
        self.is_grounded = True
        self.was_grounded = True
        self.is_jumping = False
        self.is_dashing = False
        self.dash_timer = 0.0
        self.dash_cooldown_timer = 0.0
        self.coyote_timer = 0.0
        self.jump_buffer_timer = 0.0
        self.air_time = 0.0
        self.coyote_ghost_active = False

    def handle_input(
        self,
        move_x: float,
        jump_pressed: bool,
        jump_held: bool,
        dash_pressed: bool,
        settings: PlatformerForgivenessSettings,
        telemetry: ForgivenessTelemetry,
        sfx: SoundLibrary
    ):
        """
        Processes controller/keyboard inputs, buffering jumps and initiating dashes.
        """
        # Update facing direction
        if move_x > 0.05:
            self.facing_right = True
        elif move_x < -0.05:
            self.facing_right = False

        # Update Dash Cooldown
        if self.dash_cooldown_timer > 0.0:
            self.dash_cooldown_timer -= get_frame_time()
            if self.dash_cooldown_timer < 0.0:
                self.dash_cooldown_timer = 0.0

        # Initiate Air Dash
        if dash_pressed and not self.is_dashing and self.dash_cooldown_timer <= 0.0:
            self.is_dashing = True
            self.dash_timer = self.dash_duration
            self.dash_cooldown_timer = self.dash_cooldown
            self.dash_dir_x = 1.0 if self.facing_right else -1.0
            self.vy = 0.0
            sfx.play("dash", 0.7)
            telemetry.log_event("Air Dash Burst Executed", Color(120, 210, 255, 255))

        # Handle Jump Input & Jump Buffering (Pattern 2)
        if jump_pressed:
            if settings.jump_buffer_enabled:
                self.jump_buffer_timer = settings.jump_buffer_max
            else:
                # Without jump buffering, jump press is only valid on this exact frame
                self.jump_buffer_timer = 0.001

        # Variable Jump Cutoff (Pattern 3): Early button release cuts ascent
        if not jump_held and self.is_jumping and self.vy < -120.0:
            if settings.variable_jump_enabled:
                # Clamp upward velocity smoothly to reduce arc height
                self.vy = max(self.vy * settings.variable_jump_cutoff, -120.0)
                self.is_jumping = False
                telemetry.log_event("Variable Cutoff Applied (Vy clamped)", Color(255, 185, 60, 255))

    def execute_jump(
        self,
        settings: PlatformerForgivenessSettings,
        telemetry: ForgivenessTelemetry,
        sfx: SoundLibrary,
        reason: str
    ):
        """Executes the vertical jump impulse and triggers audio/telemetry."""
        self.vy = self.jump_impulse
        self.is_grounded = False
        self.was_grounded = False
        self.is_jumping = True
        self.jump_buffer_timer = 0.0
        self.coyote_timer = 0.0
        self.coyote_ghost_active = False
        self.jump_count += 1
        sfx.play("jump", 0.7)

        if reason == "coyote":
            telemetry.log_event("Coyote Jump Executed! (Grace used)", COLOR_COYOTE_ACTIVE)
        elif reason == "buffered":
            telemetry.log_event("Buffered Touchdown Jump Executed!", COLOR_BUFFER_ACTIVE)
        else:
            telemetry.log_event("Standard Grounded Jump Executed", COLOR_TEXT_MAIN)

    def check_corner_nudge(
        self,
        plat,
        settings: PlatformerForgivenessSettings,
        telemetry: ForgivenessTelemetry
    ) -> bool:
        """
        Pattern 5: Corner Ledge Nudge.
        Checks if the character's head is clipping the bottom corner of an overhead platform
        by <= corner_nudge_dist (8 px). If so, nudges the character horizontally past the corner.
        
        Returns True if a nudge was successfully performed, preserving upward momentum.
        """
        if not settings.corner_nudge_enabled:
            return False

        # Only assist when moving upward into a ceiling
        if self.vy >= 0.0:
            return False

        player_left = self.x
        player_right = self.x + self.width
        plat_left = plat.x
        plat_right = plat.x + plat.w

        # Check Right Corner Clip (Jumping up past the platform's bottom-left edge)
        overlap_right = player_right - plat_left
        if 0.0 < overlap_right <= settings.corner_nudge_dist:
            # Shift character to the left so right edge clears platform left edge
            shift = overlap_right + 1.0
            self.x -= shift
            telemetry.last_nudge_offset = shift
            telemetry.last_nudge_dir = -1
            telemetry.nudge_visual_timer = 0.6
            self.nudge_marker_x = plat_left
            self.nudge_marker_y = plat.y + plat.h
            telemetry.log_event(f"Corner Nudge: Slid Left {int(shift)}px", COLOR_NUDGE_ACTIVE)
            return True

        # Check Left Corner Clip (Jumping up past the platform's bottom-right edge)
        overlap_left = plat_right - player_left
        if 0.0 < overlap_left <= settings.corner_nudge_dist:
            # Shift character to the right so left edge clears platform right edge
            shift = overlap_left + 1.0
            self.x += shift
            telemetry.last_nudge_offset = shift
            telemetry.last_nudge_dir = 1
            telemetry.nudge_visual_timer = 0.6
            self.nudge_marker_x = plat_right
            self.nudge_marker_y = plat.y + plat.h
            telemetry.log_event(f"Corner Nudge: Slid Right {int(shift)}px", COLOR_NUDGE_ACTIVE)
            return True

        return False

    def update_kinematics(
        self,
        dt: float,
        move_x: float,
        platforms: list,
        settings: PlatformerForgivenessSettings,
        telemetry: ForgivenessTelemetry,
        sfx: SoundLibrary
    ):
        """
        Advances kinematic simulation, integrates forces, and handles collision passes.
        """
        # Update Coyote Ghost Visual Timer
        if self.coyote_ghost_active:
            self.coyote_ghost_timer -= dt
            if self.coyote_ghost_timer <= 0.0:
                self.coyote_ghost_active = False

        # ----------------------------------------------------------------------
        # 1. Dash Kinematics Override
        # ----------------------------------------------------------------------
        if self.is_dashing:
            self.dash_timer -= dt
            self.vx = self.dash_dir_x * self.dash_speed
            self.vy = 0.0
            if self.dash_timer <= 0.0:
                self.is_dashing = False
                self.vx = self.dash_dir_x * self.run_speed
        else:
            # ------------------------------------------------------------------
            # 2. Horizontal Acceleration & Friction
            # ------------------------------------------------------------------
            # Determine air vs ground acceleration
            is_apex = (not self.is_grounded) and (abs(self.vy) < settings.apex_vy_threshold)
            telemetry.is_in_apex = is_apex

            if self.is_grounded:
                accel = self.ground_accel
                friction = self.ground_friction
            else:
                # Pattern 4: Apex Float horizontal agility boost
                if is_apex and settings.apex_float_enabled:
                    accel = self.air_accel * settings.apex_accel_mult
                else:
                    accel = self.air_accel
                friction = self.air_friction

            target_vx = move_x * self.run_speed
            if abs(move_x) > 0.05:
                # Accelerate toward target speed
                if self.vx < target_vx:
                    self.vx += accel * dt
                    if self.vx > target_vx:
                        self.vx = target_vx
                elif self.vx > target_vx:
                    self.vx -= accel * dt
                    if self.vx < target_vx:
                        self.vx = target_vx
            else:
                # Apply ground / air friction decay
                if self.vx > 0.0:
                    self.vx -= friction * dt
                    if self.vx < 0.0:
                        self.vx = 0.0
                elif self.vx < 0.0:
                    self.vx += friction * dt
                    if self.vx > 0.0:
                        self.vx = 0.0

            # ------------------------------------------------------------------
            # 3. Vertical Gravity Integration & Apex Float (Pattern 4)
            # ------------------------------------------------------------------
            if not self.is_grounded:
                self.air_time += dt

                # Select base gravity: lighter when rising, heavier when falling
                if self.vy < 0.0:
                    base_grav = self.gravity_rise
                else:
                    base_grav = self.gravity_fall

                # Pattern 4: Apex Float reduces gravity at peak
                if is_apex and settings.apex_float_enabled:
                    effective_grav = base_grav * settings.apex_gravity_mult
                    telemetry.apex_timer += dt
                else:
                    effective_grav = base_grav
                    telemetry.apex_timer = 0.0

                self.vy += effective_grav * dt
                if self.vy > self.max_fall_speed:
                    self.vy = self.max_fall_speed
            else:
                self.air_time = 0.0
                telemetry.apex_timer = 0.0

        # ----------------------------------------------------------------------
        # 4. Jump Buffer Processing (Pattern 2) & Coyote Time (Pattern 1)
        # ----------------------------------------------------------------------
        if self.jump_buffer_timer > 0.0:
            self.jump_buffer_timer -= dt
            if self.jump_buffer_timer < 0.0:
                self.jump_buffer_timer = 0.0

        # Check if buffered jump can execute on ground
        if self.jump_buffer_timer > 0.0 and self.is_grounded:
            self.execute_jump(settings, telemetry, sfx, "buffered")

        # Check if jump can execute via Coyote Time while airborne
        if self.jump_buffer_timer > 0.0 and (not self.is_grounded) and settings.coyote_enabled:
            if self.coyote_timer > 0.0:
                self.execute_jump(settings, telemetry, sfx, "coyote")

        # ----------------------------------------------------------------------
        # 5. Horizontal Collision Sweep
        # ----------------------------------------------------------------------
        self.x += self.vx * dt
        for plat in platforms:
            if not plat.active or plat.ptype == 1 or plat.ptype == 3:
                continue  # Skip hazards and goals in solid collision check

            # AABB Overlap check
            if (
                self.x < plat.x + plat.w and
                self.x + self.width > plat.x and
                self.y < plat.y + plat.h and
                self.y + self.height > plat.y
            ):
                if self.vx > 0.0:
                    self.x = plat.x - self.width
                    self.vx = 0.0
                elif self.vx < 0.0:
                    self.x = plat.x + plat.w
                    self.vx = 0.0

        # ----------------------------------------------------------------------
        # 6. Vertical Collision Sweep & Corner Ledge Nudge (Pattern 5)
        # ----------------------------------------------------------------------
        # Upward collision & Corner Nudge Check
        if self.vy < 0.0:
            nudged = False
            for plat in platforms:
                if not plat.active or plat.ptype == 1 or plat.ptype == 3:
                    continue

                # Projected overlap in next step
                next_y = self.y + self.vy * dt
                if (
                    self.x < plat.x + plat.w and
                    self.x + self.width > plat.x and
                    next_y < plat.y + plat.h and
                    self.y >= plat.y + plat.h - 8.0
                ):
                    # Test Corner Nudge
                    if self.check_corner_nudge(plat, settings, telemetry):
                        nudged = True
                        break
                    else:
                        # Solid ceiling collision (Head Bonk)
                        self.y = plat.y + plat.h
                        self.vy = 0.0
                        self.is_jumping = False
                        break

            if not nudged:
                self.y += self.vy * dt
        else:
            # Downward movement
            self.y += self.vy * dt

        # ----------------------------------------------------------------------
        # 7. Ground Landing Detection
        # ----------------------------------------------------------------------
        was_on_ground = self.is_grounded
        self.is_grounded = False

        for plat in platforms:
            if not plat.active:
                continue

            # Check overlap
            if (
                self.x < plat.x + plat.w and
                self.x + self.width > plat.x and
                self.y + self.height >= plat.y and
                self.y + self.height <= plat.y + 16.0 and
                self.vy >= 0.0
            ):
                if plat.ptype == 2:
                    # Bounce Pad: Elastic rebound
                    self.y = plat.y - self.height
                    self.vy = -720.0
                    self.is_grounded = False
                    self.is_jumping = True
                    sfx.play("bounce", 0.8)
                    telemetry.log_event("Bounce Pad Rebound Triggered!", COLOR_BOUNCE_TRIM)
                    break
                elif plat.ptype == 0:
                    # Solid platform landing
                    self.y = plat.y - self.height
                    self.vy = 0.0
                    self.is_grounded = True
                    self.is_jumping = False
                    break

        # ----------------------------------------------------------------------
        # 8. Coyote Time Triggering (Pattern 1)
        # ----------------------------------------------------------------------
        if was_on_ground and not self.is_grounded and self.vy >= 0.0:
            # Walked off a ledge into the air! Arm Coyote Time
            self.coyote_timer = settings.coyote_time_max
            self.coyote_ghost_x = self.x
            self.coyote_ghost_y = self.y
            self.coyote_ghost_active = True
            self.coyote_ghost_timer = 0.50
        elif not self.is_grounded:
            # Decrement active coyote timer
            if self.coyote_timer > 0.0:
                self.coyote_timer -= dt
                if self.coyote_timer < 0.0:
                    self.coyote_timer = 0.0
        else:
            # On ground: fully armed
            self.coyote_timer = settings.coyote_time_max
            self.coyote_ghost_active = False

        # Landed sound effect
        if not was_on_ground and self.is_grounded:
            sfx.play("land", 0.5)

        # Update was_grounded state
        self.was_grounded = was_on_ground

        # Sync telemetry timers
        telemetry.coyote_timer = self.coyote_timer
        telemetry.jump_buffer_timer = self.jump_buffer_timer


# ==============================================================================
# BLOCK 2: WORLD SIMULATION & ENTITIES
# ==============================================================================

# Platform Types
PLAT_SOLID  = 0
PLAT_HAZARD = 1
PLAT_BOUNCE = 2
PLAT_GOAL   = 3

class Platform:
    """
    World-space platform or hazard bounding block.
    
    C++ Equivalent:
      struct Platform {
          float x, y, w, h;
          int ptype;
          char label[32];
          bool active;
      };
    """
    def __init__(self, x: float, y: float, w: float, h: float, ptype: int, label: str):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.ptype = ptype
        self.label = label
        self.active = True


class Sector:
    """
    Obstacle course sector designed to isolate and test a specific forgiveness mechanic.
    """
    def __init__(
        self,
        sector_id: int,
        name: str,
        mechanic_name: str,
        checkpoint_x: float,
        checkpoint_y: float,
        bounds_min_x: float,
        bounds_max_x: float,
        description: str
    ):
        self.sector_id = sector_id
        self.name = name
        self.mechanic_name = mechanic_name
        self.checkpoint_x = checkpoint_x
        self.checkpoint_y = checkpoint_y
        self.bounds_min_x = bounds_min_x
        self.bounds_max_x = bounds_max_x
        self.description = description


class Particle:
    """Pre-allocated visual effect particle."""
    def __init__(self):
        self.active = False
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.life = 0.0
        self.max_life = 1.0
        self.size = 3.0
        self.color = Color(255, 255, 255, 255)


class ParticlePool:
    """
    Fixed-capacity zero-allocation particle pool for dust, apex sparks, and confetti.
    """
    def __init__(self, capacity: int = 160):
        self.capacity = capacity
        self.particles = []
        for _ in range(capacity):
            self.particles.append(Particle())

    def spawn(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        life: float,
        size: float,
        color: Color
    ):
        for p in self.particles:
            if not p.active:
                p.active = True
                p.x = x
                p.y = y
                p.vx = vx
                p.vy = vy
                p.life = life
                p.max_life = life
                p.size = size
                p.color = color
                break

    def spawn_burst(self, x: float, y: float, count: int, color: Color):
        for _ in range(count):
            ang = random.uniform(0.0, 6.28318)
            spd = random.uniform(40.0, 180.0)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd
            life = random.uniform(0.3, 0.7)
            size = random.uniform(2.5, 5.0)
            self.spawn(x, y, vx, vy, life, size, color)

    def update(self, dt: float):
        for p in self.particles:
            if p.active:
                p.life -= dt
                if p.life <= 0.0:
                    p.active = False
                else:
                    p.x += p.vx * dt
                    p.y += p.vy * dt
                    p.vy += 280.0 * dt  # Gravity decay

    def draw(self):
        for p in self.particles:
            if p.active:
                alpha = int(255 * (p.life / p.max_life))
                if alpha < 0:
                    alpha = 0
                elif alpha > 255:
                    alpha = 255
                col = Color(p.color.r, p.color.g, p.color.b, alpha)
                draw_rectangle(int(p.x), int(p.y), int(p.size), int(p.size), col)


class ObstacleCourse:
    """
    Constructs the 5 distinct pedagogical obstacle sectors across a 5,500px course.
    """
    def __init__(self):
        self.platforms = []
        self.sectors = []
        self._build_sectors()
        self._build_platforms()

    def _build_sectors(self):
        self.sectors.append(Sector(
            1,
            "1. The Coyote Chasm",
            "Coyote Time (120ms)",
            200.0, 480.0,
            50.0, 1050.0,
            "Run off the ledge and press Jump in mid-air. Coyote Time catches the leap!"
        ))
        self.sectors.append(Sector(
            2,
            "2. The Buffer Gauntlet",
            "Jump Buffering (140ms)",
            1200.0, 480.0,
            1100.0, 2150.0,
            "High-speed consecutive pillars. Press Jump pre-emptively before touching down!"
        ))
        self.sectors.append(Sector(
            3,
            "3. The Low Spike Tunnel",
            "Variable Jump Cutoff",
            2300.0, 480.0,
            2200.0, 3250.0,
            "Light taps execute short hops beneath ceiling spikes; holding jumps bonks hazards!"
        ))
        self.sectors.append(Sector(
            4,
            "4. The Apex Float Island",
            "Apex Float Boost (50% Grav)",
            3400.0, 480.0,
            3300.0, 4350.0,
            "Wide chasm requiring float hang-time and boosted air agility at the crest!"
        ))
        self.sectors.append(Sector(
            5,
            "5. The Overhang Corner",
            "Corner Ledge Nudge (8px)",
            4500.0, 520.0,
            4400.0, 5450.0,
            "Jump upward clipping the ceiling corner. Feelers slide character smoothly around it!"
        ))

    def _build_platforms(self):
        # ----------------------------------------------------------------------
        # SECTOR 1: THE COYOTE CHASM (x: 100 to 1050)
        # ----------------------------------------------------------------------
        # Start Ledge A
        self.platforms.append(Platform(100.0, 520.0, 320.0, 40.0, PLAT_SOLID, "S1_Ledge_A"))
        # Wide Chasm Gap (width 220px: 420 to 640)
        # Landing Ledge B
        self.platforms.append(Platform(640.0, 520.0, 380.0, 40.0, PLAT_SOLID, "S1_Ledge_B"))
        # Below: Safety Net & Bounce Spring Pad
        self.platforms.append(Platform(100.0, 670.0, 920.0, 30.0, PLAT_SOLID, "S1_Floor"))
        self.platforms.append(Platform(420.0, 655.0, 220.0, 15.0, PLAT_BOUNCE, "S1_Bounce"))

        # ----------------------------------------------------------------------
        # SECTOR 2: THE BUFFER GAUNTLET (x: 1100 to 2150)
        # ----------------------------------------------------------------------
        self.platforms.append(Platform(1120.0, 520.0, 140.0, 40.0, PLAT_SOLID, "S2_Start"))
        # 4 Consecutive Stepping Pillars
        self.platforms.append(Platform(1340.0, 520.0, 60.0, 40.0, PLAT_SOLID, "S2_Pillar_1"))
        self.platforms.append(Platform(1520.0, 520.0, 60.0, 40.0, PLAT_SOLID, "S2_Pillar_2"))
        self.platforms.append(Platform(1700.0, 520.0, 60.0, 40.0, PLAT_SOLID, "S2_Pillar_3"))
        self.platforms.append(Platform(1880.0, 520.0, 60.0, 40.0, PLAT_SOLID, "S2_Pillar_4"))
        self.platforms.append(Platform(2020.0, 520.0, 140.0, 40.0, PLAT_SOLID, "S2_Goal"))
        # Hazard Pit below
        self.platforms.append(Platform(1260.0, 660.0, 760.0, 20.0, PLAT_HAZARD, "S2_Spikes"))

        # ----------------------------------------------------------------------
        # SECTOR 3: THE LOW SPIKE TUNNEL (x: 2200 to 3250)
        # ----------------------------------------------------------------------
        # Floor
        self.platforms.append(Platform(2240.0, 520.0, 980.0, 40.0, PLAT_SOLID, "S3_Floor"))
        # Solid Ceiling
        self.platforms.append(Platform(2400.0, 360.0, 800.0, 30.0, PLAT_SOLID, "S3_Ceiling"))
        # Low Hanging Ceiling Spikes (height 415px)
        self.platforms.append(Platform(2520.0, 390.0, 50.0, 25.0, PLAT_HAZARD, "S3_Spike_1"))
        self.platforms.append(Platform(2720.0, 390.0, 50.0, 25.0, PLAT_HAZARD, "S3_Spike_2"))
        self.platforms.append(Platform(2920.0, 390.0, 50.0, 25.0, PLAT_HAZARD, "S3_Spike_3"))

        # ----------------------------------------------------------------------
        # SECTOR 4: THE APEX FLOAT ISLAND (x: 3300 to 4350)
        # ----------------------------------------------------------------------
        # Start Platform
        self.platforms.append(Platform(3340.0, 520.0, 180.0, 40.0, PLAT_SOLID, "S4_Start"))
        # Long Gap (width 340px: 3520 to 3860)
        # Elevated Float Island
        self.platforms.append(Platform(3860.0, 490.0, 180.0, 40.0, PLAT_SOLID, "S4_Island"))
        self.platforms.append(Platform(4120.0, 520.0, 200.0, 40.0, PLAT_SOLID, "S4_End"))
        # Below: Hazard Bed
        self.platforms.append(Platform(3520.0, 670.0, 600.0, 20.0, PLAT_HAZARD, "S4_Pit"))

        # ----------------------------------------------------------------------
        # SECTOR 5: THE OVERHANG CORNER (x: 4400 to 5450)
        # ----------------------------------------------------------------------
        # Lower Floor
        self.platforms.append(Platform(4440.0, 560.0, 400.0, 40.0, PLAT_SOLID, "S5_Floor"))
        # Overhead Overhang Block (Left Corner at x=4690)
        self.platforms.append(Platform(4690.0, 420.0, 180.0, 30.0, PLAT_SOLID, "S5_Overhang"))
        # Upper Stepping Ledge
        self.platforms.append(Platform(4940.0, 350.0, 160.0, 30.0, PLAT_SOLID, "S5_Upper_Ledge"))
        # Victory Pedestal
        self.platforms.append(Platform(5180.0, 290.0, 140.0, 30.0, PLAT_SOLID, "S5_Pedestal"))
        # Victory Gem Trophy Pickup
        self.platforms.append(Platform(5235.0, 255.0, 30.0, 30.0, PLAT_GOAL, "S5_Trophy"))

    def get_sector_at(self, x: float) -> Sector:
        """Finds which sector the player is currently inside."""
        for s in self.sectors:
            if s.bounds_min_x <= x <= s.bounds_max_x:
                return s
        return self.sectors[0]

    def get_sector_by_id(self, sec_id: int) -> Sector:
        """Retrieves sector by 1-based index (1 to 5)."""
        for s in self.sectors:
            if s.sector_id == sec_id:
                return s
        return self.sectors[0]


# ==============================================================================
# BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY
# ==============================================================================

def draw_timing_bar(
    x: int,
    y: int,
    w: int,
    h: int,
    current_val: float,
    max_val: float,
    active_color: Color,
    label: str
):
    """Renders a calibrated timing window bar with glowing fill ratio."""
    # Background
    draw_rectangle(x, y, w, h, COLOR_METER_BG)
    draw_rectangle_lines(x, y, w, h, Color(45, 60, 85, 255))

    # Fill ratio
    ratio = current_val / max(0.001, max_val)
    if ratio > 1.0:
        ratio = 1.0
    elif ratio < 0.0:
        ratio = 0.0

    fill_w = int(w * ratio)
    if fill_w > 0:
        draw_rectangle(x, y, fill_w, h, active_color)

    # Label text & millisecond readout
    ms_text = f"{int(current_val * 1000)}ms" if current_val > 0.0 else "OFF / 0ms"
    draw_text(label, x + 6, y + 3, 11, COLOR_TEXT_MAIN)
    draw_text(ms_text, x + w - 75, y + 3, 11, active_color if current_val > 0.0 else COLOR_TEXT_DIM)


def draw_xray_overlay(
    player: KinematicCharacterController,
    settings: PlatformerForgivenessSettings,
    telemetry: ForgivenessTelemetry,
    current_sector: Sector
):
    """
    Renders the live telemetry inspector panel showing internal counters,
    meters, toggle states, and kinematic physics readouts.
    """
    panel_x = 880
    panel_y = 60
    panel_w = 380
    panel_h = 635

    # Panel Body & Border
    draw_rectangle(panel_x, panel_y, panel_w, panel_h, COLOR_PANEL_BG)
    draw_rectangle_lines(panel_x, panel_y, panel_w, panel_h, COLOR_PANEL_BORDER)

    # Header Bar
    draw_rectangle(panel_x, panel_y, panel_w, 32, COLOR_PANEL_HEADER)
    draw_text("X-RAY FORGIVENESS TELEMETRY", panel_x + 12, panel_y + 8, 14, COLOR_TEXT_HIGHLIGHT)

    curr_y = panel_y + 42

    # Master Mode Banner
    if settings.are_all_enabled():
        draw_rectangle(panel_x + 10, curr_y, panel_w - 20, 24, Color(24, 75, 45, 255))
        draw_rectangle_lines(panel_x + 10, curr_y, panel_w - 20, 24, COLOR_COYOTE_ACTIVE)
        draw_text("MODE: COMMERCIAL FEEL (All Forgiveness ON)", panel_x + 16, curr_y + 5, 11, COLOR_COYOTE_ACTIVE)
    elif settings.are_all_disabled():
        draw_rectangle(panel_x + 10, curr_y, panel_w - 20, 24, Color(85, 24, 24, 255))
        draw_rectangle_lines(panel_x + 10, curr_y, panel_w - 20, 24, COLOR_HAZARD_TRIM)
        draw_text("MODE: BRUTAL RIGID PHYSICS (Zero Forgiveness)", panel_x + 16, curr_y + 5, 11, COLOR_HAZARD_TRIM)
    else:
        draw_rectangle(panel_x + 10, curr_y, panel_w - 20, 24, Color(75, 60, 24, 255))
        draw_rectangle_lines(panel_x + 10, curr_y, panel_w - 20, 24, COLOR_TEXT_HIGHLIGHT)
        draw_text("MODE: CUSTOM FORGIVENESS MIX", panel_x + 16, curr_y + 5, 11, COLOR_TEXT_HIGHLIGHT)

    curr_y += 34

    # 1. Coyote Time Meter
    coy_status = "ENABLED" if settings.coyote_enabled else "DISABLED"
    coy_col = COLOR_COYOTE_ACTIVE if settings.coyote_enabled else COLOR_TEXT_DIM
    draw_text(f"[1] Coyote Time: {coy_status}", panel_x + 12, curr_y, 12, coy_col)
    curr_y += 18
    draw_timing_bar(
        panel_x + 12, curr_y, panel_w - 24, 18,
        telemetry.coyote_timer, settings.coyote_time_max,
        COLOR_COYOTE_ACTIVE, "Airborne Ledge Grace Window"
    )
    curr_y += 26

    # 2. Jump Buffer Meter
    buf_status = "ENABLED" if settings.jump_buffer_enabled else "DISABLED"
    buf_col = COLOR_BUFFER_ACTIVE if settings.jump_buffer_enabled else COLOR_TEXT_DIM
    draw_text(f"[2] Jump Buffering: {buf_status}", panel_x + 12, curr_y, 12, buf_col)
    curr_y += 18
    draw_timing_bar(
        panel_x + 12, curr_y, panel_w - 24, 18,
        telemetry.jump_buffer_timer, settings.jump_buffer_max,
        COLOR_BUFFER_ACTIVE, "Pre-Landing Queue Window"
    )
    curr_y += 26

    # 3. Variable Jump Cutoff
    var_status = "ENABLED (0.45x)" if settings.variable_jump_enabled else "DISABLED (Fixed Max)"
    var_col = COLOR_TEXT_HIGHLIGHT if settings.variable_jump_enabled else COLOR_TEXT_DIM
    draw_text(f"[3] Variable Jump Height: {var_status}", panel_x + 12, curr_y, 12, var_col)
    curr_y += 16
    draw_text("    Early button release cuts upward velocity", panel_x + 12, curr_y, 10, COLOR_TEXT_DIM)
    curr_y += 20

    # 4. Apex Float Hang-Time
    apx_status = "ENABLED (0.50x Grav)" if settings.apex_float_enabled else "DISABLED"
    apx_col = COLOR_APEX_ACTIVE if settings.apex_float_enabled else COLOR_TEXT_DIM
    draw_text(f"[4] Apex Float Boost: {apx_status}", panel_x + 12, curr_y, 12, apx_col)
    curr_y += 16
    beacon_text = "APEX WINDOW: ACTIVE!" if telemetry.is_in_apex else "APEX WINDOW: Inactive"
    beacon_col = COLOR_APEX_ACTIVE if telemetry.is_in_apex else COLOR_TEXT_DIM
    draw_text(f"    {beacon_text} (|Vy| < 90 px/s)", panel_x + 12, curr_y, 10, beacon_col)
    curr_y += 20

    # 5. Corner Ledge Nudge
    nud_status = "ENABLED (<= 8px)" if settings.corner_nudge_enabled else "DISABLED"
    nud_col = COLOR_NUDGE_ACTIVE if settings.corner_nudge_enabled else COLOR_TEXT_DIM
    draw_text(f"[5] Corner Ledge Nudge: {nud_status}", panel_x + 12, curr_y, 12, nud_col)
    curr_y += 16
    if telemetry.nudge_visual_timer > 0.0:
        dir_str = "Left" if telemetry.last_nudge_dir == -1 else "Right"
        draw_text(f"    ASSIST ACTIVATED: Slid {int(telemetry.last_nudge_offset)}px {dir_str}", panel_x + 12, curr_y, 10, COLOR_NUDGE_ACTIVE)
    else:
        draw_text("    Overhead feelers: Ready (slides past corners)", panel_x + 12, curr_y, 10, COLOR_TEXT_DIM)
    curr_y += 26

    # Kinematics Diagnostics Box
    draw_rectangle(panel_x + 10, curr_y, panel_w - 20, 96, Color(16, 21, 33, 255))
    draw_rectangle_lines(panel_x + 10, curr_y, panel_w - 20, 96, Color(35, 48, 75, 255))
    draw_text("KINEMATIC STATE", panel_x + 18, curr_y + 6, 11, COLOR_TEXT_HIGHLIGHT)

    pos_txt = f"Pos: ({int(player.x)}, {int(player.y)})"
    vel_txt = f"Vx: {player.vx:+.1f} | Vy: {player.vy:+.1f} px/s"
    draw_text(pos_txt, panel_x + 18, curr_y + 24, 11, COLOR_TEXT_MAIN)
    draw_text(vel_txt, panel_x + 18, curr_y + 40, 11, COLOR_TEXT_MAIN)

    ground_str = "GROUNDED" if player.is_grounded else "AIRBORNE"
    ground_col = COLOR_COYOTE_ACTIVE if player.is_grounded else Color(255, 160, 60, 255)
    draw_text(f"State: {ground_str}", panel_x + 18, curr_y + 56, 11, ground_col)
    draw_text(f"Air Time: {player.air_time:.2f}s | Jumps: {player.jump_count}", panel_x + 18, curr_y + 72, 11, COLOR_TEXT_DIM)

    curr_y += 106

    # Recent Activation Events Log
    draw_text("RECENT FORGIVENESS EVENTS", panel_x + 12, curr_y, 11, COLOR_TEXT_HIGHLIGHT)
    curr_y += 16
    if len(telemetry.recent_events) == 0:
        draw_text("  No events logged yet. Try jumping off ledges!", panel_x + 12, curr_y, 10, COLOR_TEXT_DIM)
    else:
        for ev in telemetry.recent_events:
            alpha = int(255 * (ev.timer / ev.max_timer))
            if alpha < 40:
                alpha = 40
            elif alpha > 255:
                alpha = 255
            col = Color(ev.color.r, ev.color.g, ev.color.b, alpha)
            draw_text(f"> {ev.message}", panel_x + 14, curr_y, 10, col)
            curr_y += 16


def draw_world_debug_visuals(
    player: KinematicCharacterController,
    settings: PlatformerForgivenessSettings,
    telemetry: ForgivenessTelemetry
):
    """
    Draws in-world X-Ray halos, feeler rays, and coyote ghost silhouettes.
    """
    # 1. Coyote Ledge Ghost (Shows exact spot player ran off ledge)
    if player.coyote_ghost_active and settings.coyote_enabled:
        ghost_x = int(player.coyote_ghost_x)
        ghost_y = int(player.coyote_ghost_y)
        draw_rectangle_lines(ghost_x, ghost_y, int(player.width), int(player.height), COLOR_COYOTE_ACTIVE)
        draw_text("COYOTE ORIGIN", ghost_x - 16, ghost_y - 14, 10, COLOR_COYOTE_ACTIVE)

    # 2. Apex Float Golden Halo / Aura
    if telemetry.is_in_apex and settings.apex_float_enabled:
        cx = int(player.x + player.width * 0.5)
        cy = int(player.y + player.height * 0.5)
        draw_circle_lines(cx, cy, 26, COLOR_APEX_ACTIVE)
        draw_circle_lines(cx, cy, 30, Color(255, 230, 110, 150))
        draw_text("APEX FLOAT", cx - 32, cy - 38, 10, COLOR_APEX_ACTIVE)

    # 3. Corner Nudge Feelers (Upward probe rays from player's head)
    if settings.corner_nudge_enabled:
        head_y = int(player.y)
        left_x = int(player.x)
        right_x = int(player.x + player.width)
        feeler_len = 8

        # Left feeler ray
        draw_line(left_x, head_y, left_x, head_y - feeler_len, COLOR_NUDGE_ACTIVE)
        draw_line(left_x - 2, head_y - feeler_len, left_x + 2, head_y - feeler_len, COLOR_NUDGE_ACTIVE)

        # Right feeler ray
        draw_line(right_x, head_y, right_x, head_y - feeler_len, COLOR_NUDGE_ACTIVE)
        draw_line(right_x - 2, head_y - feeler_len, right_x + 2, head_y - feeler_len, COLOR_NUDGE_ACTIVE)

    # 4. Corner Nudge Deflection Marker
    if telemetry.nudge_visual_timer > 0.0:
        mx = int(player.nudge_marker_x)
        my = int(player.nudge_marker_y)
        draw_circle(mx, my, 5, COLOR_NUDGE_ACTIVE)
        draw_circle_lines(mx, my, 9, COLOR_TEXT_HIGHLIGHT)


# ==============================================================================
# BLOCK 4: MAIN GAME LOOP & AUTOMATED SMOKE TEST
# ==============================================================================

class PatternLabGame:
    """
    Main orchestration class managing window, input loop, camera follow,
    and automated headless smoke test verification.
    """
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()

        # Procedural Audio Cache
        self.sfx = SoundLibrary()
        self.sfx.init_defaults()

        # Core Patterns & Settings
        self.settings = PlatformerForgivenessSettings()
        self.telemetry = ForgivenessTelemetry()

        # Obstacle Course & World Simulation
        self.course = ObstacleCourse()
        self.particles = ParticlePool(160)

        # Player Avatar Spawn in Sector 1
        sec1 = self.course.get_sector_by_id(1)
        self.player = KinematicCharacterController(sec1.checkpoint_x, sec1.checkpoint_y)
        self.current_sector = sec1

        # Interactive Toggles
        self.show_xray = True
        self.last_t_pressed = False

        # 2D Camera Follow Rig
        self.camera = Camera2D(
            Vector2(SCREEN_WIDTH * 0.40, SCREEN_HEIGHT * 0.65),
            Vector2(self.player.x, self.player.y),
            0.0,
            1.0
        )

    def warp_to_sector(self, sector_id: int):
        """Teleports the character to a specified sector checkpoint."""
        sec = self.course.get_sector_by_id(sector_id)
        self.current_sector = sec
        self.player.reset_position(sec.checkpoint_x, sec.checkpoint_y)
        self.particles.spawn_burst(sec.checkpoint_x, sec.checkpoint_y, 25, COLOR_TEXT_HIGHLIGHT)
        self.sfx.play("select", 0.7)
        self.telemetry.log_event(f"Warped to {sec.name}", COLOR_TEXT_HIGHLIGHT)

    def update(self):
        dt = min(get_frame_time(), 0.05)

        # ----------------------------------------------------------------------
        # 1. Input Polling (Simultaneous KB/M + Gamepad)
        # ----------------------------------------------------------------------
        # Move vector (WASD / Left Stick / D-Pad)
        move_vec = get_dual_move_2d()
        move_x = move_vec.x

        # Jump Actions
        jump_pressed = is_dual_jump_pressed()
        jump_held = is_dual_jump_down()

        # Air Dash Action (Shift / Gamepad X)
        dash_pressed = is_dual_dash_pressed()

        # Master Toggle [F1]: Commercial Forgiveness vs Raw Rigid Physics
        if is_dual_pattern_toggle_pressed():
            if self.settings.are_all_enabled():
                self.settings.toggle_all(False)
                self.sfx.play("error", 0.6)
                self.telemetry.log_event("ALL FORGIVENESS OFF (Brutal Rigid Physics)", COLOR_HAZARD_TRIM)
            else:
                self.settings.toggle_all(True)
                self.sfx.play("confirm", 0.7)
                self.telemetry.log_event("ALL FORGIVENESS ON (Commercial Feel)", COLOR_COYOTE_ACTIVE)

        # Individual Toggles [1] through [5]
        if is_key_pressed(KEY_ONE):
            self.settings.toggle_mechanic(1)
            self.sfx.play("click", 0.6)
            st = "ON" if self.settings.coyote_enabled else "OFF"
            self.telemetry.log_event(f"Coyote Time toggled {st}", COLOR_COYOTE_ACTIVE)
        elif is_key_pressed(KEY_TWO):
            self.settings.toggle_mechanic(2)
            self.sfx.play("click", 0.6)
            st = "ON" if self.settings.jump_buffer_enabled else "OFF"
            self.telemetry.log_event(f"Jump Buffer toggled {st}", COLOR_BUFFER_ACTIVE)
        elif is_key_pressed(KEY_THREE):
            self.settings.toggle_mechanic(3)
            self.sfx.play("click", 0.6)
            st = "ON" if self.settings.variable_jump_enabled else "OFF"
            self.telemetry.log_event(f"Variable Jump toggled {st}", COLOR_TEXT_HIGHLIGHT)
        elif is_key_pressed(KEY_FOUR):
            self.settings.toggle_mechanic(4)
            self.sfx.play("click", 0.6)
            st = "ON" if self.settings.apex_float_enabled else "OFF"
            self.telemetry.log_event(f"Apex Float toggled {st}", COLOR_APEX_ACTIVE)
        elif is_key_pressed(KEY_FIVE):
            self.settings.toggle_mechanic(5)
            self.sfx.play("click", 0.6)
            st = "ON" if self.settings.corner_nudge_enabled else "OFF"
            self.telemetry.log_event(f"Corner Nudge toggled {st}", COLOR_NUDGE_ACTIVE)

        # Sector Warp [T]
        if is_key_pressed(KEY_T):
            next_id = (self.current_sector.sector_id % 5) + 1
            self.warp_to_sector(next_id)

        # Reset / Respawn [R]
        if is_dual_reset_pressed():
            self.player.reset_position(self.current_sector.checkpoint_x, self.current_sector.checkpoint_y)
            self.sfx.play("select", 0.6)
            self.telemetry.log_event(f"Respawned at {self.current_sector.name}", COLOR_TEXT_MAIN)

        # Toggle X-Ray Overlay [Tab]
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
            self.sfx.play("click", 0.5)

        # ----------------------------------------------------------------------
        # 2. Player Input & Kinematics Processing
        # ----------------------------------------------------------------------
        self.player.handle_input(
            move_x, jump_pressed, jump_held, dash_pressed,
            self.settings, self.telemetry, self.sfx
        )

        self.player.update_kinematics(
            dt, move_x, self.course.platforms,
            self.settings, self.telemetry, self.sfx
        )

        # ----------------------------------------------------------------------
        # 3. Hazard & Goal Trigger Checks
        # ----------------------------------------------------------------------
        for plat in self.course.platforms:
            if not plat.active:
                continue

            # Overlap check
            if (
                self.player.x < plat.x + plat.w and
                self.player.x + self.player.width > plat.x and
                self.player.y < plat.y + plat.h and
                self.player.y + self.player.height > plat.y
            ):
                if plat.ptype == PLAT_HAZARD:
                    # Touched hazard spike: hurt and respawn
                    self.sfx.play("hurt", 0.8)
                    self.particles.spawn_burst(self.player.x, self.player.y, 20, COLOR_HAZARD_TRIM)
                    self.telemetry.log_event("Hazard Struck! Respawned", COLOR_HAZARD_TRIM)
                    self.player.reset_position(self.current_sector.checkpoint_x, self.current_sector.checkpoint_y)
                    break
                elif plat.ptype == PLAT_GOAL:
                    # Collected trophy!
                    self.sfx.play("powerup", 0.9)
                    self.particles.spawn_burst(plat.x + 15, plat.y + 15, 45, COLOR_TEXT_HIGHLIGHT)
                    self.telemetry.log_event("COURSE COMPLETE! Trophy Collected!", COLOR_TEXT_HIGHLIGHT)
                    plat.active = False
                    break

        # Pit fall out of bounds reset
        if self.player.y > 800.0:
            self.sfx.play("hurt", 0.6)
            self.player.reset_position(self.current_sector.checkpoint_x, self.current_sector.checkpoint_y)

        # Update current sector tracking
        self.current_sector = self.course.get_sector_at(self.player.x)

        # ----------------------------------------------------------------------
        # 4. Particle Pool & Telemetry Update
        # ----------------------------------------------------------------------
        self.telemetry.update(dt)
        self.particles.update(dt)

        # Jump & Dash Footstep Particles
        if abs(self.player.vx) > 40.0 and self.player.is_grounded and random.random() < 0.25:
            self.particles.spawn(
                self.player.x + self.player.width * 0.5,
                self.player.y + self.player.height,
                -self.player.vx * 0.15,
                random.uniform(-10.0, -30.0),
                0.25, 2.5, Color(130, 150, 180, 180)
            )

        # ----------------------------------------------------------------------
        # 5. Smooth Camera Follow
        # ----------------------------------------------------------------------
        target_cam_x = self.player.x + self.player.vx * 0.20
        target_cam_y = self.player.y - 40.0
        # Exponential spring damping
        cam_speed = 7.0
        self.camera.target.x += (target_cam_x - self.camera.target.x) * min(1.0, dt * cam_speed)
        self.camera.target.y += (target_cam_y - self.camera.target.y) * min(1.0, dt * cam_speed)

    def draw(self):
        begin_drawing()
        clear_background(COLOR_BG_DARK)

        # ======================================================================
        # 1. 2D WORLD RENDERING
        # ======================================================================
        begin_mode_2d(self.camera)

        # World Grid Backdrop
        grid_w = 5600
        grid_h = 800
        for gx in range(0, grid_w, 80):
            draw_line(gx, 0, gx, grid_h, Color(18, 24, 38, 255))
        for gy in range(0, grid_h, 80):
            draw_line(0, gy, grid_w, gy, Color(18, 24, 38, 255))

        # Sector Overhead Banners
        for s in self.course.sectors:
            bx = int(s.bounds_min_x + 30)
            draw_rectangle(bx, 140, 360, 48, Color(20, 28, 45, 200))
            draw_rectangle_lines(bx, 140, 360, 48, Color(50, 75, 115, 255))
            draw_text(s.name, bx + 12, 146, 14, COLOR_TEXT_HIGHLIGHT)
            draw_text(s.description, bx + 12, 166, 10, COLOR_TEXT_DIM)

        # Draw Platforms & Hazards
        for plat in self.course.platforms:
            if not plat.active:
                continue

            px = int(plat.x)
            py = int(plat.y)
            pw = int(plat.w)
            ph = int(plat.h)

            if plat.ptype == PLAT_SOLID:
                draw_rectangle(px, py, pw, ph, COLOR_PLATFORM_SOLID)
                draw_rectangle(px, py, pw, 4, COLOR_PLATFORM_TRIM)
                draw_rectangle_lines(px, py, pw, ph, Color(30, 40, 60, 255))
            elif plat.ptype == PLAT_HAZARD:
                draw_rectangle(px, py, pw, ph, COLOR_HAZARD_FILL)
                draw_rectangle(px, py, pw, 3, COLOR_HAZARD_TRIM)
                # Hazard teeth spikes
                for sx in range(px, px + pw, 16):
                    draw_line(sx, py + ph, sx + 8, py, COLOR_HAZARD_TRIM)
                    draw_line(sx + 8, py, sx + 16, py + ph, COLOR_HAZARD_TRIM)
            elif plat.ptype == PLAT_BOUNCE:
                draw_rectangle(px, py, pw, ph, COLOR_BOUNCE_FILL)
                draw_rectangle(px, py, pw, 4, COLOR_BOUNCE_TRIM)
                draw_text("BOUNCE SPRING", px + 15, py + 2, 10, COLOR_TEXT_MAIN)
            elif plat.ptype == PLAT_GOAL:
                draw_rectangle(px, py, pw, ph, COLOR_GOAL_FILL)
                draw_rectangle_lines(px, py, pw, ph, COLOR_GOAL_TRIM)
                draw_text("GOAL", px + 4, py + 8, 10, COLOR_TEXT_MAIN)

        # Draw Particles
        self.particles.draw()

        # Draw In-World X-Ray Telemetry Halos and Feelers
        if self.show_xray:
            draw_world_debug_visuals(self.player, self.settings, self.telemetry)

        # Draw Player Avatar
        pl_x = int(self.player.x)
        pl_y = int(self.player.y)
        pl_w = int(self.player.width)
        pl_h = int(self.player.height)

        # Main Body
        draw_rectangle(pl_x, pl_y, pl_w, pl_h, COLOR_PLAYER_BODY)
        draw_rectangle_lines(pl_x, pl_y, pl_w, pl_h, COLOR_PLAYER_OUTLINE)

        # Visor / Eye showing facing direction
        eye_w = 6
        eye_h = 6
        eye_y = pl_y + 8
        if self.player.facing_right:
            eye_x = pl_x + pl_w - 8
        else:
            eye_x = pl_x + 2
        draw_rectangle(eye_x, eye_y, eye_w, eye_h, COLOR_PLAYER_EYE)

        end_mode_2d()

        # ======================================================================
        # 2. SCREEN-SPACE HUD RENDERING
        # ======================================================================
        # Top Header Bar (Region x=450..980 is strictly clear for UI settings bar)
        draw_rectangle(0, 0, SCREEN_WIDTH, 54, Color(14, 18, 28, 240))
        draw_line(0, 54, SCREEN_WIDTH, 54, Color(35, 48, 75, 255))

        # Title & Subtitle
        draw_text("PLATFORMER FORGIVENESS LAB", 20, 10, 16, COLOR_TEXT_HIGHLIGHT)
        mode_desc = "[F1] Forgiveness: ON" if self.settings.are_all_enabled() else "[F1] Forgiveness: OFF (Rigid)"
        mode_col = COLOR_COYOTE_ACTIVE if self.settings.are_all_enabled() else COLOR_HAZARD_TRIM
        draw_text(f"2D Kinematic Feel Sandbox | {mode_desc}", 20, 30, 11, mode_col)

        # Sector Quick-Select Bar (y: 60)
        draw_text("SECTORS:", 20, 64, 11, COLOR_TEXT_DIM)
        sec_names = ["1. Coyote", "2. Buffer", "3. Low Spikes", "4. Apex Float", "5. Corner Ledge"]
        for i in range(5):
            sx = 80 + i * 115
            is_active = (self.current_sector.sector_id == i + 1)
            btn_col = Color(35, 65, 110, 240) if is_active else Color(22, 30, 46, 220)
            line_col = COLOR_TEXT_HIGHLIGHT if is_active else Color(45, 60, 85, 255)
            draw_rectangle(sx, 60, 110, 20, btn_col)
            draw_rectangle_lines(sx, 60, 110, 20, line_col)
            draw_text(sec_names[i], sx + 8, 64, 10, COLOR_TEXT_MAIN if is_active else COLOR_TEXT_DIM)

        # Controls Footer Bar
        draw_rectangle(0, SCREEN_HEIGHT - 32, SCREEN_WIDTH, 32, Color(14, 18, 28, 245))
        draw_line(0, SCREEN_HEIGHT - 32, SCREEN_WIDTH, SCREEN_HEIGHT - 32, Color(35, 48, 75, 255))
        ctrls_txt = (
            "A/D: Move | Space: Jump | Shift: Dash | [1-5]: Toggle Mechanics | "
            "[F1]: Toggle Master Forgiveness | [T]: Warp Sector | [Tab]: X-Ray Inspector | [R]: Respawn"
        )
        draw_text(ctrls_txt, 20, SCREEN_HEIGHT - 22, 11, COLOR_TEXT_DIM)

        # Telemetry & X-Ray Inspector Overlay
        if self.show_xray:
            draw_xray_overlay(self.player, self.settings, self.telemetry, self.current_sector)
        else:
            # Small pill prompt
            draw_rectangle(SCREEN_WIDTH - 220, 60, 200, 24, Color(18, 24, 38, 220))
            draw_rectangle_lines(SCREEN_WIDTH - 220, 60, 200, 24, Color(45, 60, 85, 255))
            draw_text("[Tab] Show X-Ray Telemetry", SCREEN_WIDTH - 205, 66, 11, COLOR_TEXT_HIGHLIGHT)

        # Mandatory Global Top-Bar Clearance & Gamepad Badge
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)

        end_drawing()

    def run(self, smoke_test: bool = False):
        """Main game loop with automated headless verification."""
        frame_count = 0
        while not window_should_close():
            self.update()
            self.draw()
            frame_count += 1
            if smoke_test and frame_count >= 3:
                break

        # Cleanup audio resources
        self.sfx.unload_all()
        close_audio_device()
        close_window()


if __name__ == "__main__":
    is_smoke = "--smoke-test" in sys.argv
    PatternLabGame().run(smoke_test=is_smoke)
