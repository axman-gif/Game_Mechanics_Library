# -*- coding: utf-8 -*-
"""
Drone Defense 3D - Rotated Capsule Collisions, State Machine (FSM) & Camera Rig
=============================================================================
Section          : 3.0 Core Multi-Pattern Prototypes
Pattern Category : Collision / Physics, Behavioral (FSM), Presentation (Camera Rig)
Dimension        : 3D

Problem Solved:
  In 3D combat games, naive bounding spheres or axis-aligned bounding boxes (AABB)
  fail drastically for articulated or elongated targets like flying drones with
  outstretched wings, walking humanoids, or high-velocity laser beams. Shots passing
  cleanly through wide wing spans either pass through without dealing damage (false
  negatives) or, if the sphere is enlarged, register hits in empty air (phantom hits).
  Furthermore, managing multi-stage enemy behaviors (approach, orbit, dive, retreat)
  via ad-hoc boolean flags creates state corruption, while rigidly locking the camera
  to the player's weapon causes jarring, nauseating jitter during recoil and tracking.

How the Patterns Work:
  1. Rotated Capsule Collisions: Represents articulated geometry (drone core, wing spans,
     humanoid torso/limbs, and laser tracer bolts) as 3D line segments extruded by radius r.
     Collision testing computes the shortest distance between two arbitrary 3D line segments
     (L1 and L2). If distance <= r1 + r2, an exact intersection is guaranteed regardless
     of object yaw, pitch, or bank angle.
  2. Finite State Machine (FSM): Drones and ground troops run explicit, C++-transferable
     state machines (Approach -> Orbit -> Dive-Bomb -> Evasive Retreat -> Crashing) with
     strict enter(), update(), and exit() transitions.
  3. Spring-Damped Camera Rig & Screen Shake: Provides smooth third-person and cockpit
     camera tracking using framerate-independent exponential damping (damp), dynamic
     Aim-Down-Sights (ADS) zoom, and quadratic trauma-based camera shake (TraumaShake).
  4. Object Pool: High-speed plasma projectiles and 3D hit particles are pre-allocated
     at startup, eliminating garbage collection hitches during heavy combat.

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - Mouse Move / Right Stick           : Aim Turret Barrels (Yaw & Pitch)
  - Left Mouse / Space / Gamepad RT/X  : Twin Heavy Plasma Cannons (Hold for continuous fire)
  - Right Mouse / L-Shift / Gamepad LT : Aim Down Sights (ADS Precision Zoom)
  - Gamepad Left Stick / WASD          : Fine-tune Turret Yaw & Elevation
  - [Tab] / Gamepad View (Select)      : Toggle X-Ray Telemetry & 3D Capsule Wireframe Overlay
  - [F1]  / Gamepad LB                 : Toggle Pattern: [Rotated Capsules (Exact)] vs [Naive Spheres]
  - [F2]  / Gamepad RB                 : Toggle Camera Rig: [Spring Damped + Trauma] vs [Rigid Snap]
  - [V]   / Gamepad D-Pad Up           : Switch Camera View: [3rd-Person Turret] vs [Cockpit Sights]
  - [Ctrl +/-]                         : Increase / Decrease UI Font Size
  - [F11]                              : Toggle Fullscreen
  - [R]   / Gamepad Start              : Reset Defense Simulation / Restart Wave
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

# Window & Screen Configuration
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WINDOW_TITLE = "Drone Defense 3D - Rotated Capsule Collisions & FSM (Raylib Pattern Lab)"

# Arena & Combat Palette
COLOR_DESERT_SAND     = Color(38, 32, 28, 255)
COLOR_DESERT_GRID     = Color(65, 54, 45, 255)
COLOR_BASE_CONCRETE   = Color(50, 55, 65, 255)
COLOR_BASE_BORDER     = Color(240, 160, 30, 255)
COLOR_SHIELD_RING     = Color(0, 190, 255, 120)
COLOR_RING_MARKER     = Color(70, 95, 130, 200)

COLOR_CAPSULE_CORE    = Color(0, 220, 255, 255)
COLOR_CAPSULE_WING    = Color(255, 140, 20, 255)
COLOR_CAPSULE_BULLET  = Color(255, 40, 100, 255)
COLOR_NAIVE_SPHERE    = Color(255, 230, 0, 255)
COLOR_COLLISION_LINE  = Color(255, 255, 255, 255)

# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATIONS
# ==============================================================================

# ------------------------------------------------------------------------------
# PATTERN 1: ROTATED 3D CAPSULE COLLISION SYSTEM
# ------------------------------------------------------------------------------
# A 3D capsule is defined mathematically as a line segment between points P1 and P2
# extruded outward by radius r.
#
# In C++:
#   struct Capsule3D {
#       Vector3 start;
#       Vector3 end;
#       float radius;
#   };
#
# To test if two arbitrary 3D capsules intersect, we find the two closest points
# on their respective central axis segments (P on seg1, Q on seg2).
# If the Euclidean distance between P and Q is <= (r1 + r2), they intersect!
# This handles all arbitrary 3D rotations, yaw, pitch, and banking.

def draw_capsule_wireframe_3d(start_pos: Vector3, end_pos: Vector3, radius: float, color: Color):
    """
    Renders a 3D wireframe capsule:
      - Central segment line connecting start and end
      - Wireframe spherical cap at start_pos
      - Wireframe spherical cap at end_pos
      - Translucent cylindrical shell connecting the caps
    """
    # 1. Central core axis
    draw_line_3d(start_pos, end_pos, color)
    
    # 2. End sphere caps
    draw_sphere_wires(start_pos, radius, 6, 6, color)
    draw_sphere_wires(end_pos, radius, 6, 6, color)
    
    # 3. Translucent connecting hull cylinder
    faded_col = Color(color.r, color.g, color.b, 35)
    draw_cylinder_ex(start_pos, end_pos, radius, radius, 8, faded_col)


# ------------------------------------------------------------------------------
# PATTERN 2: FINITE STATE MACHINE (FSM) ENGINE
# ------------------------------------------------------------------------------
# Explicit, language-agnostic state definitions.
# Each state encapsulates autonomous behaviors without nested boolean flags.

# Drone FSM States
STATE_DRONE_APPROACH = 0  # Inbound from perimeter spawn towards orbit distance
STATE_DRONE_ORBIT    = 1  # Circling base, assessing defenses, evasive swaying
STATE_DRONE_DIVE     = 2  # High-speed attack run diving directly at turret
STATE_DRONE_RETREAT  = 3  # Pulling up into high altitude, banking away
STATE_DRONE_CRASHING = 4  # 0 HP: flaming spiral descent until ground impact

DRONE_STATE_NAMES = {
    STATE_DRONE_APPROACH: "APPROACH",
    STATE_DRONE_ORBIT:    "ORBITING",
    STATE_DRONE_DIVE:     "DIVE-BOMB",
    STATE_DRONE_RETREAT:  "RETREATING",
    STATE_DRONE_CRASHING: "CRASHING"
}

# Ground Trooper FSM States
STATE_WALKER_MARCH   = 0  # Advancing in column towards perimeter barricade
STATE_WALKER_DEPLOY  = 1  # Deployed frontal energy barrier
STATE_WALKER_FIRE    = 2  # Firing plasma mortar at defensive turret
STATE_WALKER_FALL    = 3  # Destroyed knockdown

WALKER_STATE_NAMES = {
    STATE_WALKER_MARCH:  "MARCH",
    STATE_WALKER_DEPLOY: "SHIELDED",
    STATE_WALKER_FIRE:   "FIRE-MORTAR",
    STATE_WALKER_FALL:   "FALLEN"
}


# ------------------------------------------------------------------------------
# PATTERN 3: SPRING-DAMPED CAMERA RIG WITH TRAUMA SHAKE
# ------------------------------------------------------------------------------
# Solves camera jitter, disorientation, and recoil nausea.
# The rig interpolates both rotation and position using framerate-independent
# exponential damping: damp(curr, target, smoothing, dt).
# Features dynamic Aim-Down-Sights (ADS) zoom and quadratic trauma screen shake.

class CameraRig3D:
    """
    3D Camera Rig supporting third-person follow and cockpit sights,
    spring-damped yaw/pitch tracking, ADS zoom, and trauma screen shake.
    """
    def __init__(self):
        self.camera = Camera3D(
            Vector3(0.0, 5.0, -9.0),
            Vector3(0.0, 2.0, 10.0),
            Vector3(0.0, 1.0, 0.0),
            65.0,
            CAMERA_PERSPECTIVE
        )
        self.view_mode = 0         # 0 = Third-Person Turret Cam, 1 = Cockpit Sights
        self.yaw = 0.0             # Smoothed aim yaw (radians)
        self.pitch = 0.15          # Smoothed aim pitch (radians)
        self.target_yaw = 0.0      # Raw input target yaw
        self.target_pitch = 0.15   # Raw input target pitch
        self.fov = 65.0            # Current smoothed FOV
        self.target_fov = 65.0     # Target FOV (65 hipfire, 36 ADS)
        self.smoothing = 14.0      # Spring damping factor
        self.is_ads = False        # Aim Down Sights active flag
        self.trauma_shake = TraumaShake(max_offset_px=0.45, max_angle_deg=2.5, decay_rate=1.8)

    def add_trauma(self, amount: float):
        """Injects screen shake energy into the camera rig."""
        self.trauma_shake.add_trauma(amount)

    def update(self, turret_pos: Vector3, dt: float, apply_damping: bool = True):
        # 1. Update ADS target FOV
        self.target_fov = 36.0 if self.is_ads else 65.0

        # 2. Smoothly damp or rigidly snap orientation and zoom
        if apply_damping:
            self.yaw = damp(self.yaw, self.target_yaw, self.smoothing, dt)
            self.pitch = damp(self.pitch, self.target_pitch, self.smoothing, dt)
            self.fov = damp(self.fov, self.target_fov, 12.0, dt)
        else:
            self.yaw = self.target_yaw
            self.pitch = self.target_pitch
            self.fov = self.target_fov

        self.camera.fovy = self.fov

        # 3. Calculate forward, right, and up aiming basis vectors
        cos_p = math.cos(self.pitch)
        sin_p = math.sin(self.pitch)
        cos_y = math.cos(self.yaw)
        sin_y = math.sin(self.yaw)

        # Forward aim direction
        dir_x = sin_y * cos_p
        dir_y = sin_p
        dir_z = cos_y * cos_p

        # 4. Position camera based on view mode
        if self.view_mode == 0:
            # Mode 0: Third-Person Turret View (behind and above turret)
            cam_dist = 6.2
            cam_height = 2.4
            desired_pos = Vector3(
                turret_pos.x - dir_x * cam_dist,
                turret_pos.y + cam_height - dir_y * 1.5,
                turret_pos.z - dir_z * cam_dist
            )
            desired_target = Vector3(
                turret_pos.x + dir_x * 40.0,
                turret_pos.y + dir_y * 40.0 + 1.2,
                turret_pos.z + dir_z * 40.0
            )
        else:
            # Mode 1: Cockpit / Sights View (over the turret barrels)
            desired_pos = Vector3(
                turret_pos.x + dir_x * 1.2,
                turret_pos.y + 0.65 + dir_y * 0.4,
                turret_pos.z + dir_z * 1.2
            )
            desired_target = Vector3(
                desired_pos.x + dir_x * 50.0,
                desired_pos.y + dir_y * 50.0,
                desired_pos.z + dir_z * 50.0
            )

        # 5. Apply trauma screen shake offsets
        if apply_damping:
            ox, oy, o_angle = self.trauma_shake.update(dt)
            desired_pos.x += ox * 0.5
            desired_pos.y += oy * 0.5
            desired_target.x += ox * 1.2
            desired_target.y += oy * 1.2
        else:
            self.trauma_shake.trauma = 0.0

        self.camera.position = desired_pos
        self.camera.target = desired_target
        self.camera.up = Vector3(0.0, 1.0, 0.0)


# ==============================================================================
# BLOCK 2: WORLD SIMULATION & ENTITIES
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. PRE-ALLOCATED PROJECTILES & 3D PARTICLES
# ------------------------------------------------------------------------------

class Projectile3D:
    """Pre-allocated plasma projectile tested as a swept 3D capsule."""
    def __init__(self):
        self.active = False
        self.pos = Vector3(0.0, 0.0, 0.0)
        self.vel = Vector3(0.0, 0.0, 0.0)
        self.dir = Vector3(0.0, 0.0, 1.0)
        self.length = 1.4      # Visual and collision segment length
        self.radius = 0.16      # Capsule collision radius
        self.lifetime = 0.0
        self.is_player = True
        self.color = COLOR_CAPSULE_BULLET

    def spawn(self, start_pos: Vector3, direction: Vector3, speed: float, is_player: bool, color: Color):
        self.active = True
        self.pos = Vector3(start_pos.x, start_pos.y, start_pos.z)
        self.dir = Vector3(direction.x, direction.y, direction.z)
        self.vel = Vector3(direction.x * speed, direction.y * speed, direction.z * speed)
        self.length = 1.6 if is_player else 1.1
        self.radius = 0.18 if is_player else 0.22
        self.lifetime = 3.5
        self.is_player = is_player
        self.color = color

    def update(self, dt: float):
        if not self.active:
            return
        self.pos.x += self.vel.x * dt
        self.pos.y += self.vel.y * dt
        self.pos.z += self.vel.z * dt
        self.lifetime -= dt
        if self.lifetime <= 0.0:
            self.active = False

    def get_capsule(self) -> Capsule3D:
        """Returns the swept 3D capsule line segment from rear to head."""
        p1 = Vector3(
            self.pos.x - self.dir.x * self.length * 0.5,
            self.pos.y - self.dir.y * self.length * 0.5,
            self.pos.z - self.dir.z * self.length * 0.5
        )
        p2 = Vector3(
            self.pos.x + self.dir.x * self.length * 0.5,
            self.pos.y + self.dir.y * self.length * 0.5,
            self.pos.z + self.dir.z * self.length * 0.5
        )
        return Capsule3D(p1, p2, self.radius)


class Particle3D:
    """Pre-allocated 3D spark / explosion particle."""
    def __init__(self):
        self.active = False
        self.pos = Vector3(0.0, 0.0, 0.0)
        self.vel = Vector3(0.0, 0.0, 0.0)
        self.color = Color(255, 255, 255, 255)
        self.size = 0.1
        self.life = 0.0
        self.max_life = 1.0

    def spawn(self, pos: Vector3, vel: Vector3, color: Color, size: float, life: float):
        self.active = True
        self.pos = Vector3(pos.x, pos.y, pos.z)
        self.vel = Vector3(vel.x, vel.y, vel.z)
        self.color = color
        self.size = size
        self.life = life
        self.max_life = life

    def update(self, dt: float):
        if not self.active:
            return
        self.pos.x += self.vel.x * dt
        self.pos.y += self.vel.y * dt
        self.pos.z += self.vel.z * dt
        self.vel.y -= 9.8 * dt * 0.5  # Subtle gravity
        self.life -= dt
        if self.life <= 0.0 or self.pos.y < 0.0:
            self.active = False


# ------------------------------------------------------------------------------
# 2. ARTICULATED DRONE ENTITY (MULTI-CAPSULE RIG)
# ------------------------------------------------------------------------------

class DroneEnemy:
    """
    Articulated 3D Drone with a Multi-Capsule Collision Rig:
      - 1 Vertical Core Capsule (cockpit and engine pod)
      - 2 Rotated Wing Capsules (horizontal wing span and cross fins)
    Also stores a Naive Bounding Sphere for [F1] pedagogical comparison.
    """
    def __init__(self):
        self.active = False
        self.pos = Vector3(0.0, 10.0, 0.0)
        self.vel = Vector3(0.0, 0.0, 0.0)
        self.yaw = 0.0               # Facing heading (degrees)
        self.tilt_pitch = 0.0        # Forward/backward pitch tilt (degrees)
        self.tilt_roll = 0.0         # Banking roll tilt (degrees)
        self.hp = 3
        self.max_hp = 3
        self.state = STATE_DRONE_APPROACH
        self.state_timer = 0.0
        self.orbit_angle = 0.0       # Angle in horizontal orbit (radians)
        self.orbit_radius = 22.0     # Radius of orbiting circle
        self.orbit_speed = 0.45      # Angular speed
        self.altitude = 7.5          # Base flight altitude
        self.dive_target = Vector3(0.0, 1.8, 0.0)
        self.anim_timer = 0.0
        self.shot_cooldown = 0.0
        self.scale = 1.0

        # Collision dimensions
        self.core_radius = 0.38
        self.core_height = 0.90
        self.wing_radius = 0.22
        self.wing_span = 1.85        # Total wing span tip-to-tip
        self.naive_sphere_radius = 0.45  # Covers only center core!

    def spawn(self, start_pos: Vector3):
        self.active = True
        self.pos = Vector3(start_pos.x, start_pos.y, start_pos.z)
        self.vel = Vector3(0.0, 0.0, 0.0)
        self.hp = 3
        self.max_hp = 3
        self.state = STATE_DRONE_APPROACH
        self.state_timer = 0.0
        self.orbit_angle = math.atan2(self.pos.x, self.pos.z)
        self.orbit_radius = random.uniform(19.0, 25.0)
        self.orbit_speed = random.choice([-0.45, 0.45])
        self.altitude = random.uniform(6.5, 9.5)
        self.anim_timer = random.uniform(0.0, 10.0)
        self.shot_cooldown = random.uniform(1.2, 2.5)
        self.scale = 1.0

    def get_capsules(self):
        """
        Calculates world-space capsules by rotating the local offsets according
        to the drone's current yaw and banking angles.
        Returns: [core_capsule, lateral_wings_capsule, cross_fins_capsule]
        """
        yaw_rad = math.radians(self.yaw)
        cos_y = math.cos(yaw_rad)
        sin_y = math.sin(yaw_rad)

        # 1. Central Core Capsule (vertical axis)
        c_top = Vector3(self.pos.x, self.pos.y + 0.48, self.pos.z)
        c_bot = Vector3(self.pos.x, self.pos.y - 0.42, self.pos.z)
        core_cap = Capsule3D(c_bot, c_top, self.core_radius)

        # 2. Lateral Wing Span Capsule (rotated in world XZ)
        half_span = self.wing_span * 0.5
        w1_x = self.pos.x - cos_y * half_span
        w1_z = self.pos.z + sin_y * half_span
        w2_x = self.pos.x + cos_y * half_span
        w2_z = self.pos.z - sin_y * half_span
        wing_cap = Capsule3D(Vector3(w1_x, self.pos.y, w1_z), Vector3(w2_x, self.pos.y, w2_z), self.wing_radius)

        # 3. Longitudinal / Cross Fin Capsule (along local Z)
        half_fin = 0.65
        f1_x = self.pos.x - sin_y * half_fin
        f1_z = self.pos.z - cos_y * half_fin
        f2_x = self.pos.x + sin_y * half_fin
        f2_z = self.pos.z + cos_y * half_fin
        fin_cap = Capsule3D(Vector3(f1_x, self.pos.y, f1_z), Vector3(f2_x, self.pos.y, f2_z), self.wing_radius)

        return [core_cap, wing_cap, fin_cap]

    def update_fsm(self, turret_pos: Vector3, dt: float, sfx: SoundLibrary, enemy_pool):
        """Executes the drone's Finite State Machine transitions."""
        if not self.active:
            return

        self.anim_timer += dt
        self.state_timer += dt

        # Current distance to defensive turret
        dx = turret_pos.x - self.pos.x
        dz = turret_pos.z - self.pos.z
        dist_2d = math.sqrt(dx * dx + dz * dz)

        # =====================================================================
        # STATE 0: APPROACH (Inbound flight from perimeter spawn)
        # =====================================================================
        if self.state == STATE_DRONE_APPROACH:
            # Fly inward toward designated orbit radius
            target_x = math.sin(self.orbit_angle) * self.orbit_radius
            target_z = math.cos(self.orbit_angle) * self.orbit_radius
            step_x = target_x - self.pos.x
            step_z = target_z - self.pos.z
            step_dist = math.sqrt(step_x * step_x + step_z * step_z)

            approach_speed = 14.0
            if step_dist > 1.0:
                self.vel.x = (step_x / step_dist) * approach_speed
                self.vel.z = (step_z / step_dist) * approach_speed
            else:
                self.vel.x = 0.0
                self.vel.z = 0.0
                # Transition: Enter Orbit
                self.state = STATE_DRONE_ORBIT
                self.state_timer = 0.0

            # Smoothly damp altitude toward flight corridor
            self.pos.y = damp(self.pos.y, self.altitude, 4.0, dt)
            self.yaw = math.degrees(math.atan2(self.vel.x, self.vel.z)) if abs(self.vel.x) + abs(self.vel.z) > 0.1 else self.yaw

        # =====================================================================
        # STATE 1: ORBIT (Circling base perimeter and scanning for dive opening)
        # =====================================================================
        elif self.state == STATE_DRONE_ORBIT:
            self.orbit_angle += self.orbit_speed * dt
            target_x = math.sin(self.orbit_angle) * self.orbit_radius
            target_z = math.cos(self.orbit_angle) * self.orbit_radius

            # Natural altitude sway
            target_y = self.altitude + math.sin(self.anim_timer * 1.8) * 1.2
            self.pos.x = damp(self.pos.x, target_x, 8.0, dt)
            self.pos.z = damp(self.pos.z, target_z, 8.0, dt)
            self.pos.y = damp(self.pos.y, target_y, 4.0, dt)

            # Face tangent to circle
            tangent_angle = self.orbit_angle + (math.pi * 0.5 if self.orbit_speed > 0 else -math.pi * 0.5)
            self.yaw = math.degrees(tangent_angle)

            # Random attack dive trigger after orbiting for a bit
            self.shot_cooldown -= dt
            if self.state_timer > 4.5 and random.random() < 0.015:
                # Transition: Dive-bomb attack
                self.state = STATE_DRONE_DIVE
                self.state_timer = 0.0
                self.dive_target = Vector3(turret_pos.x, turret_pos.y + 0.8, turret_pos.z)
                sfx.play("laser", 0.45)

        # =====================================================================
        # STATE 2: DIVE-BOMB (High-speed attack run diving directly at turret)
        # =====================================================================
        elif self.state == STATE_DRONE_DIVE:
            dive_dx = self.dive_target.x - self.pos.x
            dive_dy = self.dive_target.y - self.pos.y
            dive_dz = self.dive_target.z - self.pos.z
            dive_dist = math.sqrt(dive_dx * dive_dx + dive_dy * dive_dy + dive_dz * dive_dz)

            dive_speed = 22.0
            if dive_dist > 4.5:
                self.vel.x = (dive_dx / dive_dist) * dive_speed
                self.vel.y = (dive_dy / dive_dist) * dive_speed
                self.vel.z = (dive_dz / dive_dist) * dive_speed

                # Fire plasma burst at halfway point
                self.shot_cooldown -= dt
                if self.shot_cooldown <= 0.0:
                    self.shot_cooldown = 0.4
                    # Spawn enemy projectile from underside pod
                    for proj in enemy_pool:
                        if not proj.active:
                            fire_dir = Vector3(dive_dx / dive_dist, dive_dy / dive_dist, dive_dz / dive_dist)
                            proj.spawn(self.pos, fire_dir, speed=35.0, is_player=False, color=Color(255, 60, 40, 255))
                            sfx.play("laser", 0.55)
                            break
            else:
                # Close enough: Pull out and retreat
                self.state = STATE_DRONE_RETREAT
                self.state_timer = 0.0
                sfx.play("jump", 0.5)

            self.yaw = math.degrees(math.atan2(self.vel.x, self.vel.z))

        # =====================================================================
        # STATE 3: RETREAT (Pulling up into high altitude evasive climb)
        # =====================================================================
        elif self.state == STATE_DRONE_RETREAT:
            # Climb high and push outward
            outward_x = -dx
            outward_z = -dz
            out_dist = math.sqrt(outward_x * outward_x + outward_z * outward_z)
            retreat_speed = 16.0

            if out_dist > 0.1:
                self.vel.x = (outward_x / out_dist) * retreat_speed
                self.vel.z = (outward_z / out_dist) * retreat_speed
            self.vel.y = 8.5  # Climb upward

            if self.pos.y >= 11.0 or self.state_timer > 3.0:
                # Transition back to Orbit
                self.state = STATE_DRONE_ORBIT
                self.state_timer = 0.0
                self.altitude = random.uniform(7.0, 10.0)
                self.orbit_angle = math.atan2(self.pos.x, self.pos.z)

            self.yaw = math.degrees(math.atan2(self.vel.x, self.vel.z))

        # =====================================================================
        # STATE 4: CRASHING (Destroyed spiral descent)
        # =====================================================================
        elif self.state == STATE_DRONE_CRASHING:
            self.vel.y -= 14.0 * dt
            self.yaw += 480.0 * dt
            self.pos.x += self.vel.x * dt
            self.pos.y += self.vel.y * dt
            self.pos.z += self.vel.z * dt

            if self.pos.y <= 0.4:
                # Impact with ground: explode
                self.active = False
                sfx.play("explosion", 0.85)
                return

        # Integrate velocity for active states
        if self.state != STATE_DRONE_ORBIT and self.state != STATE_DRONE_CRASHING:
            self.pos.x += self.vel.x * dt
            self.pos.y += self.vel.y * dt
            self.pos.z += self.vel.z * dt


# ------------------------------------------------------------------------------
# 3. GROUND TROOPER ENTITY (WALKING CYBER-HUMANOID)
# ------------------------------------------------------------------------------

class WalkerTrooper:
    """Ground humanoid trooper marching toward defensive barricade with energy shield."""
    def __init__(self):
        self.active = False
        self.pos = Vector3(0.0, 0.0, 0.0)
        self.vel = Vector3(0.0, 0.0, 0.0)
        self.yaw = 0.0
        self.hp = 4
        self.max_hp = 4
        self.state = STATE_WALKER_MARCH
        self.state_timer = 0.0
        self.fire_cooldown = 2.0
        self.anim_timer = 0.0
        self.has_shield = True

    def spawn(self, start_pos: Vector3):
        self.active = True
        self.pos = Vector3(start_pos.x, 0.0, start_pos.z)
        self.vel = Vector3(0.0, 0.0, 0.0)
        self.hp = 4
        self.max_hp = 4
        self.state = STATE_WALKER_MARCH
        self.state_timer = 0.0
        self.fire_cooldown = random.uniform(2.5, 4.0)
        self.anim_timer = random.uniform(0.0, 5.0)
        self.has_shield = True

    def get_capsules(self):
        """Returns the vertical body capsule and frontal shield capsule if active."""
        # 1. Humanoid body capsule
        b_bot = Vector3(self.pos.x, self.pos.y + 0.35, self.pos.z)
        b_top = Vector3(self.pos.x, self.pos.y + 1.75, self.pos.z)
        body_cap = Capsule3D(b_bot, b_top, 0.42)
        caps = [body_cap]

        # 2. Frontal Energy Shield (when deployed)
        if self.has_shield and self.state == STATE_WALKER_DEPLOY:
            yaw_rad = math.radians(self.yaw)
            sin_y = math.sin(yaw_rad)
            cos_y = math.cos(yaw_rad)
            # Shield capsule across front
            s_center_x = self.pos.x + sin_y * 0.75
            s_center_z = self.pos.z + cos_y * 0.75
            s1 = Vector3(s_center_x - cos_y * 0.7, self.pos.y + 1.0, s_center_z + sin_y * 0.7)
            s2 = Vector3(s_center_x + cos_y * 0.7, self.pos.y + 1.0, s_center_z - sin_y * 0.7)
            shield_cap = Capsule3D(s1, s2, 0.35)
            caps.append(shield_cap)

        return caps

    def update_fsm(self, turret_pos: Vector3, dt: float, sfx: SoundLibrary, enemy_pool):
        if not self.active:
            return

        self.anim_timer += dt
        self.state_timer += dt

        dx = turret_pos.x - self.pos.x
        dz = turret_pos.z - self.pos.z
        dist_2d = math.sqrt(dx * dx + dz * dz)

        # Always face toward central turret
        self.yaw = math.degrees(math.atan2(dx, dz))

        # =====================================================================
        # STATE 0: MARCH (Advancing toward perimeter wall)
        # =====================================================================
        if self.state == STATE_WALKER_MARCH:
            march_speed = 3.5
            if dist_2d > 14.0:
                self.pos.x += (dx / dist_2d) * march_speed * dt
                self.pos.z += (dz / dist_2d) * march_speed * dt
            else:
                # Reached siege distance: Deploy shield
                self.state = STATE_WALKER_DEPLOY
                self.state_timer = 0.0

        # =====================================================================
        # STATE 1: DEPLOY SHIELD (Holding ground, bracing behind energy barrier)
        # =====================================================================
        elif self.state == STATE_WALKER_DEPLOY:
            if self.state_timer > 3.0:
                # Transition: Fire mortar
                self.state = STATE_WALKER_FIRE
                self.state_timer = 0.0

        # =====================================================================
        # STATE 2: FIRE MORTAR (Launching energy shell at turret)
        # =====================================================================
        elif self.state == STATE_WALKER_FIRE:
            if self.state_timer > 0.8:
                # Launch energy projectile
                for proj in enemy_pool:
                    if not proj.active:
                        mortar_dir = Vector3(dx / dist_2d, 0.22, dz / dist_2d)
                        proj.spawn(Vector3(self.pos.x, self.pos.y + 1.5, self.pos.z), mortar_dir, speed=26.0, is_player=False, color=Color(255, 130, 0, 255))
                        sfx.play("laser", 0.6)
                        break
                # Loop back to Deploy Shield
                self.state = STATE_WALKER_DEPLOY
                self.state_timer = 0.0

        # =====================================================================
        # STATE 3: FALLEN (Destroyed)
        # =====================================================================
        elif self.state == STATE_WALKER_FALL:
            if self.state_timer > 1.2:
                self.active = False


# ------------------------------------------------------------------------------
# 4. PLAYER TURRET & DEFENSE BASE
# ------------------------------------------------------------------------------

class PlayerTurret:
    """Central heavy defensive turret controlled by the player."""
    def __init__(self):
        self.pos = Vector3(0.0, 1.4, 0.0)
        self.yaw = 0.0                # Yaw angle in radians
        self.pitch = 0.15             # Pitch elevation in radians
        self.hp = 100
        self.max_hp = 100
        self.fire_rate = 0.11         # Seconds between twin shots
        self.fire_timer = 0.0
        self.barrel_recoil_left = 0.0
        self.barrel_recoil_right = 0.0
        self.barrel_toggle = 0        # 0 = Left barrel, 1 = Right barrel
        self.score = 0
        self.shots_fired = 0
        self.hits_registered = 0
        self.shield_flash = 0.0

    def update(self, dt: float):
        self.fire_timer = max(0.0, self.fire_timer - dt)
        self.shield_flash = max(0.0, self.shield_flash - dt * 3.0)
        # Damping recoil recovery
        self.barrel_recoil_left = damp(self.barrel_recoil_left, 0.0, 15.0, dt)
        self.barrel_recoil_right = damp(self.barrel_recoil_right, 0.0, 15.0, dt)

    def fire_cannons(self, pool, sfx: SoundLibrary, camera_rig: CameraRig3D, is_camera_damped: bool):
        if self.fire_timer > 0.0:
            return

        self.fire_timer = self.fire_rate
        self.shots_fired += 1

        # Calculate forward aim direction vector
        cos_p = math.cos(self.pitch)
        sin_p = math.sin(self.pitch)
        cos_y = math.cos(self.yaw)
        sin_y = math.sin(self.yaw)

        dir_vec = Vector3(sin_y * cos_p, sin_p, cos_y * cos_p)
        right_vec = Vector3(cos_y, 0.0, -sin_y)

        # Alternate barrels for authentic twin-cannon recoil
        barrel_offset = 0.42 if self.barrel_toggle == 1 else -0.42
        if self.barrel_toggle == 1:
            self.barrel_recoil_right = 0.35
            self.barrel_toggle = 0
        else:
            self.barrel_recoil_left = 0.35
            self.barrel_toggle = 1

        muzzle_pos = Vector3(
            self.pos.x + dir_vec.x * 2.3 + right_vec.x * barrel_offset,
            self.pos.y + 0.65 + dir_vec.y * 2.3,
            self.pos.z + dir_vec.z * 2.3 + right_vec.z * barrel_offset
        )

        # Spawn high-speed plasma tracer projectile
        for proj in pool:
            if not proj.active:
                proj.spawn(muzzle_pos, dir_vec, speed=85.0, is_player=True, color=Color(0, 240, 255, 255))
                break

        # Camera trauma kickback
        if is_camera_damped:
            camera_rig.add_trauma(0.08)

        # Procedural audio blast
        sfx.play("laser", 0.70)


# ==============================================================================
# BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY ([Tab], [F1], [F2])
# ==============================================================================

class XRayTelemetry:
    """Manages 3D wireframe capsule visualizations and 2D telemetry panels."""
    def __init__(self):
        self.recent_hit_p1 = Vector3(0.0, 0.0, 0.0)
        self.recent_hit_p2 = Vector3(0.0, 0.0, 0.0)
        self.recent_hit_timer = 0.0
        self.collision_checks_frame = 0
        self.false_negatives_avoided = 0

    def record_hit(self, p1: Vector3, p2: Vector3):
        self.recent_hit_p1 = Vector3(p1.x, p1.y, p1.z)
        self.recent_hit_p2 = Vector3(p2.x, p2.y, p2.z)
        self.recent_hit_timer = 0.65

    def update(self, dt: float):
        self.recent_hit_timer = max(0.0, self.recent_hit_timer - dt)

    def draw_3d(self, drones, walkers, projectiles, pattern_capsules_on: bool):
        """Renders 3D wireframe capsules, swept projectile segments, and hit vectors."""
        # 1. Draw Drone Hitboxes
        for drone in drones:
            if not drone.active:
                continue

            if pattern_capsules_on:
                # ROTATED CAPSULES: Render the 3 articulated capsules
                caps = drone.get_capsules()
                # Core capsule
                draw_capsule_wireframe_3d(caps[0].start, caps[0].end, caps[0].radius, COLOR_CAPSULE_CORE)
                # Wing span capsule (highlighted in orange)
                draw_capsule_wireframe_3d(caps[1].start, caps[1].end, caps[1].radius, COLOR_CAPSULE_WING)
                # Cross fin capsule
                draw_capsule_wireframe_3d(caps[2].start, caps[2].end, caps[2].radius, COLOR_CAPSULE_WING)
            else:
                # NAIVE SPHERE: Render single bounding sphere at center
                draw_sphere_wires(drone.pos, drone.naive_sphere_radius, 8, 8, COLOR_NAIVE_SPHERE)

        # 2. Draw Ground Trooper Hitboxes
        for walker in walkers:
            if not walker.active:
                continue
            caps = walker.get_capsules()
            for c in caps:
                draw_capsule_wireframe_3d(c.start, c.end, c.radius, COLOR_CAPSULE_CORE)

        # 3. Draw Active Projectile Capsules
        for proj in projectiles:
            if not proj.active:
                continue
            cap = proj.get_capsule()
            draw_capsule_wireframe_3d(cap.start, cap.end, cap.radius, COLOR_CAPSULE_BULLET)

        # 4. Draw Recent Hit Contact Vector (Segment Distance)
        if self.recent_hit_timer > 0.0:
            draw_line_3d(self.recent_hit_p1, self.recent_hit_p2, COLOR_COLLISION_LINE)
            draw_sphere(self.recent_hit_p1, 0.12, COLOR_COLLISION_LINE)
            draw_sphere(self.recent_hit_p2, 0.12, COLOR_CAPSULE_BULLET)

    def draw_2d(self, turret: PlayerTurret, drones, camera_rig: CameraRig3D,
                pattern_capsules_on: bool, is_camera_damped: bool):
        """Renders the comprehensive X-Ray Telemetry HUD panel."""
        panel_w = 410
        panel_h = 320
        panel_x = 20
        panel_y = 65

        # Background container
        draw_rectangle(panel_x, panel_y, panel_w, panel_h, Color(16, 20, 32, 230))
        draw_rectangle_lines(panel_x, panel_y, panel_w, panel_h, Color(45, 75, 120, 255))

        # Header
        draw_text("X-RAY TELEMETRY & PATTERN INSPECTOR [Tab]", panel_x + 14, panel_y + 12, 14, Color(0, 220, 255, 255))
        draw_line(panel_x + 14, panel_y + 32, panel_x + panel_w - 14, panel_y + 32, Color(45, 75, 120, 255))

        # Pattern 1 Status
        y_cursor = panel_y + 40
        pat_status = "ROTATED 3D CAPSULES (EXACT)" if pattern_capsules_on else "NAIVE BOUNDING SPHERES (FLAWED)"
        pat_col = Color(80, 255, 140, 255) if pattern_capsules_on else Color(255, 90, 90, 255)
        draw_text(f"[F1] Collision Rig: {pat_status}", panel_x + 14, y_cursor, 12, pat_col)

        y_cursor += 18
        if pattern_capsules_on:
            draw_text(" * 3 Rotated Capsules per Drone (Core + Wings)", panel_x + 14, y_cursor, 11, Color(180, 210, 240, 255))
            y_cursor += 15
            draw_text(" * Exact segment distance math: 0% false misses", panel_x + 14, y_cursor, 11, Color(180, 210, 240, 255))
        else:
            draw_text(" * Single sphere (r=0.45m). Wing shots PASS THROUGH!", panel_x + 14, y_cursor, 11, Color(255, 180, 180, 255))
            y_cursor += 15
            draw_text(" * Notice shots through wings miss without dealing damage", panel_x + 14, y_cursor, 11, Color(255, 180, 180, 255))

        # Pattern 2 Status (Camera Rig)
        y_cursor += 22
        rig_status = "SPRING DAMPED + TRAUMA SHAKE" if is_camera_damped else "RIGID SNAP (ZERO DAMPING)"
        rig_col = Color(80, 255, 140, 255) if is_camera_damped else Color(255, 90, 90, 255)
        draw_text(f"[F2] Camera Rig: {rig_status}", panel_x + 14, y_cursor, 12, rig_col)

        y_cursor += 18
        cam_view_name = "3RD PERSON TURRET" if camera_rig.view_mode == 0 else "COCKPIT SIGHTS"
        draw_text(f" * View Mode [V]: {cam_view_name} | FOV: {int(camera_rig.fov)} deg", panel_x + 14, y_cursor, 11, Color(180, 210, 240, 255))
        y_cursor += 15
        draw_text(f" * Trauma Energy: {camera_rig.trauma_shake.trauma:.2f} | ADS Zoom: {camera_rig.is_ads}", panel_x + 14, y_cursor, 11, Color(180, 210, 240, 255))

        # Pattern 3 Status (FSM Counts)
        y_cursor += 22
        draw_text("ENEMY FINITE STATE MACHINE (FSM) SPECTRUM:", panel_x + 14, y_cursor, 12, Color(240, 200, 80, 255))

        fsm_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
        for d in drones:
            if d.active:
                fsm_counts[d.state] += 1

        y_cursor += 18
        fsm_str = (f"Appr: {fsm_counts[0]} | Orbit: {fsm_counts[1]} | Dive: {fsm_counts[2]} | "
                   f"Retreat: {fsm_counts[3]} | Crash: {fsm_counts[4]}")
        draw_text(fsm_str, panel_x + 14, y_cursor, 11, Color(200, 220, 240, 255))

        # Collision & Combat Metrics
        y_cursor += 24
        draw_text(f"Checks this frame: {self.collision_checks_frame} pairwise tests", panel_x + 14, y_cursor, 11, Color(150, 180, 210, 255))
        y_cursor += 16
        draw_text(f"Turret Yaw: {math.degrees(turret.yaw):.1f}° | Elevation Pitch: {math.degrees(turret.pitch):.1f}°", panel_x + 14, y_cursor, 11, Color(150, 180, 210, 255))
        y_cursor += 16
        draw_text(f"Base Integrity: {turret.hp}% | Total Score: {turret.score}", panel_x + 14, y_cursor, 12, Color(255, 220, 100, 255))


# ==============================================================================
# BLOCK 4: MAIN GAME LOOP & AUTOMATED SMOKE TEST
# ==============================================================================

class DroneDefenseGame:
    """Complete Drone Defense 3D Simulation & Pedagogical Lab."""

    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()

        # Procedural audio library
        self.sfx = SoundLibrary()
        self.sfx.init_defaults()

        # Camera Rig & Telemetry
        self.camera_rig = CameraRig3D()
        self.telemetry = XRayTelemetry()

        # Pedagogical Pattern Toggles
        self.pattern_capsules_on = True    # [F1] Rotated Capsules (True) vs Naive Spheres (False)
        self.is_camera_damped = True       # [F2] Spring Damped (True) vs Rigid Snap (False)
        self.show_xray = True              # [Tab] X-Ray Overlay

        # World Entities
        self.turret = PlayerTurret()

        # Pre-allocated object pools
        self.player_bullets = [Projectile3D() for _ in range(120)]
        self.enemy_bullets = [Projectile3D() for _ in range(60)]
        self.particles = [Particle3D() for _ in range(200)]
        self.drones = [DroneEnemy() for _ in range(16)]
        self.walkers = [WalkerTrooper() for _ in range(10)]

        # Spawner Director
        self.wave_timer = 0.0
        self.spawn_cooldown = 1.8
        self.wave_number = 1

        # Populate initial wave
        self._spawn_wave_enemies(4, 2)

    def _spawn_wave_enemies(self, drone_count: int, walker_count: int):
        """Spawns wave units at circular perimeter positions."""
        # Spawn Drones
        d_spawned = 0
        for drone in self.drones:
            if not drone.active and d_spawned < drone_count:
                angle = random.uniform(0.0, math.pi * 2.0)
                r = random.uniform(34.0, 42.0)
                drone.spawn(Vector3(math.sin(angle) * r, random.uniform(8.0, 12.0), math.cos(angle) * r))
                d_spawned += 1

        # Spawn Ground Troopers
        w_spawned = 0
        for walker in self.walkers:
            if not walker.active and w_spawned < walker_count:
                angle = random.uniform(0.0, math.pi * 2.0)
                r = random.uniform(32.0, 38.0)
                walker.spawn(Vector3(math.sin(angle) * r, 0.0, math.cos(angle) * r))
                w_spawned += 1

    def spawn_hit_particles(self, pos: Vector3, count: int, color: Color):
        """Emits spark and debris particles from a collision point."""
        spawned = 0
        for p in self.particles:
            if not p.active and spawned < count:
                vel = Vector3(
                    random.uniform(-4.0, 4.0),
                    random.uniform(1.0, 6.0),
                    random.uniform(-4.0, 4.0)
                )
                p.spawn(pos, vel, color, random.uniform(0.08, 0.16), random.uniform(0.35, 0.75))
                spawned += 1

    def update(self):
        dt = min(get_frame_time(), 0.05)

        # ----------------------------------------------------------------------
        # 1. INPUT PROCESSING & PATTERN TOGGLES
        # ----------------------------------------------------------------------
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
            self.sfx.play("click", 0.6)

        if is_dual_pattern_toggle_pressed():
            self.pattern_capsules_on = not self.pattern_capsules_on
            self.sfx.play("coin", 0.7)

        if is_dual_secondary_toggle_pressed():
            self.is_camera_damped = not self.is_camera_damped
            self.sfx.play("click", 0.6)

        if is_key_pressed(KEY_V):
            self.camera_rig.view_mode = 1 if self.camera_rig.view_mode == 0 else 0
            self.sfx.play("click", 0.6)

        if is_dual_reset_pressed():
            # Reset defense match
            self.turret.hp = 100
            self.turret.score = 0
            for d in self.drones:
                d.active = False
            for w in self.walkers:
                w.active = False
            for b in self.player_bullets:
                b.active = False
            for b in self.enemy_bullets:
                b.active = False
            self._spawn_wave_enemies(4, 2)
            self.sfx.play("powerup", 0.7)

        # Aim Down Sights (ADS Zoom)
        ads_pressed = (is_mouse_button_down(MOUSE_BUTTON_RIGHT) or
                       is_key_down(KEY_LEFT_SHIFT) or
                       is_gamepad_trigger_down(is_right_trigger=False))
        self.camera_rig.is_ads = ads_pressed

        # Aim Look (Mouse Delta + Dual Analog Stick)
        sens = 0.0032 if not ads_pressed else 0.0016
        m_delta = get_mouse_delta()
        self.camera_rig.target_yaw -= m_delta.x * sens
        self.camera_rig.target_pitch = max(-0.15, min(1.15, self.camera_rig.target_pitch - m_delta.y * sens))

        look_analog = get_dual_look_2d(deadzone=0.18, use_arrow_keys=True)
        stick_sens = 2.2 if not ads_pressed else 1.1
        self.camera_rig.target_yaw -= look_analog.x * stick_sens * dt
        self.camera_rig.target_pitch = max(-0.15, min(1.15, self.camera_rig.target_pitch - look_analog.y * stick_sens * dt))

        # Turret yaw and pitch follow camera target
        self.turret.yaw = self.camera_rig.yaw
        self.turret.pitch = self.camera_rig.pitch
        self.turret.update(dt)

        # Primary Cannons Fire
        if is_dual_primary_fire_down():
            self.turret.fire_cannons(self.player_bullets, self.sfx, self.camera_rig, self.is_camera_damped)

        # ----------------------------------------------------------------------
        # 2. UPDATE CAMERA RIG
        # ----------------------------------------------------------------------
        self.camera_rig.update(self.turret.pos, dt, apply_damping=self.is_camera_damped)
        self.telemetry.update(dt)

        # ----------------------------------------------------------------------
        # 3. UPDATE PROJECTILES & PARTICLES
        # ----------------------------------------------------------------------
        for b in self.player_bullets:
            b.update(dt)
        for b in self.enemy_bullets:
            b.update(dt)
        for p in self.particles:
            p.update(dt)

        # ----------------------------------------------------------------------
        # 4. UPDATE ENEMY FSMs
        # ----------------------------------------------------------------------
        for drone in self.drones:
            drone.update_fsm(self.turret.pos, dt, self.sfx, self.enemy_bullets)
        for walker in self.walkers:
            walker.update_fsm(self.turret.pos, dt, self.sfx, self.enemy_bullets)

        # ----------------------------------------------------------------------
        # 5. EXACT COLLISION RESOLUTION PIPELINE (THE CORE LESSON)
        # ----------------------------------------------------------------------
        collision_count = 0

        # A. Player Projectiles vs Drones
        for proj in self.player_bullets:
            if not proj.active:
                continue

            proj_cap = proj.get_capsule()

            for drone in self.drones:
                if not drone.active or drone.state == STATE_DRONE_CRASHING:
                    continue

                collision_count += 1
                hit_detected = False

                if self.pattern_capsules_on:
                    # PATTERN ON: Test against all rotated capsules (Core + Wings)
                    drone_caps = drone.get_capsules()
                    for d_cap in drone_caps:
                        if check_collision_capsules_3d(proj_cap.start, proj_cap.end, proj_cap.radius,
                                                       d_cap.start, d_cap.end, d_cap.radius):
                            hit_detected = True
                            # Record segment hit for X-Ray visualization
                            c1, c2, _ = closest_points_between_segments_3d(proj_cap.start, proj_cap.end, d_cap.start, d_cap.end)
                            self.telemetry.record_hit(c1, c2)
                            break
                else:
                    # PATTERN OFF (NAIVE SPHERE): Test only single center sphere
                    if check_collision_capsule_sphere_3d(proj_cap.start, proj_cap.end, proj_cap.radius,
                                                          drone.pos, drone.naive_sphere_radius):
                        hit_detected = True
                        self.telemetry.record_hit(proj.pos, drone.pos)

                if hit_detected:
                    proj.active = False
                    drone.hp -= 1
                    self.turret.hits_registered += 1
                    self.turret.score += 150
                    self.spawn_hit_particles(proj.pos, 14, Color(0, 240, 255, 255))
                    self.sfx.play("hit", 0.65)

                    if drone.hp <= 0:
                        # Enter Crashing state
                        drone.state = STATE_DRONE_CRASHING
                        drone.state_timer = 0.0
                        drone.vel = Vector3(random.uniform(-3.0, 3.0), -2.0, random.uniform(-3.0, 3.0))
                        self.turret.score += 400
                        self.sfx.play("explosion", 0.75)
                        if self.is_camera_damped:
                            self.camera_rig.add_trauma(0.18)
                    break

            # B. Player Projectiles vs Ground Walkers
            if proj.active:
                for walker in self.walkers:
                    if not walker.active or walker.state == STATE_WALKER_FALL:
                        continue

                    collision_count += 1
                    walker_caps = walker.get_capsules()
                    for w_cap in walker_caps:
                        if check_collision_capsules_3d(proj_cap.start, proj_cap.end, proj_cap.radius,
                                                       w_cap.start, w_cap.end, w_cap.radius):
                            proj.active = False
                            walker.hp -= 1
                            self.turret.hits_registered += 1
                            self.spawn_hit_particles(proj.pos, 12, Color(255, 180, 50, 255))
                            self.sfx.play("hit", 0.65)

                            if walker.hp <= 0:
                                walker.state = STATE_WALKER_FALL
                                walker.state_timer = 0.0
                                self.turret.score += 300
                                self.sfx.play("hurt", 0.7)
                            break
                    if not proj.active:
                        break

        # C. Enemy Projectiles vs Player Turret Base
        for e_proj in self.enemy_bullets:
            if not e_proj.active:
                continue

            # Base collision: Cylinder / Sphere around turret platform
            dx = self.turret.pos.x - e_proj.pos.x
            dy = (self.turret.pos.y + 0.8) - e_proj.pos.y
            dz = self.turret.pos.z - e_proj.pos.z
            dist_sq = dx * dx + dy * dy + dz * dz

            if dist_sq <= (1.8 * 1.8):
                e_proj.active = False
                self.turret.hp = max(0, self.turret.hp - 8)
                self.turret.shield_flash = 1.0
                self.spawn_hit_particles(e_proj.pos, 16, Color(255, 60, 40, 255))
                self.sfx.play("hurt", 0.8)
                if self.is_camera_damped:
                    self.camera_rig.add_trauma(0.35)

        self.telemetry.collision_checks_frame = collision_count

        # ----------------------------------------------------------------------
        # 6. SPAWN DIRECTOR & WAVE PACING
        # ----------------------------------------------------------------------
        self.wave_timer += dt
        active_enemies = sum(1 for d in self.drones if d.active) + sum(1 for w in self.walkers if w.active)
        if active_enemies == 0 and self.wave_timer > 3.0:
            self.wave_number += 1
            self.wave_timer = 0.0
            drone_spawns = min(12, 3 + self.wave_number * 2)
            walker_spawns = min(8, 2 + self.wave_number)
            self._spawn_wave_enemies(drone_spawns, walker_spawns)
            self.sfx.play("powerup", 0.8)

    def draw_environment_3d(self):
        """Renders the desert arena, defensive bunker, and perimeter rings."""
        # 1. Desert Terrain Grid Floor
        draw_grid(50, 2.0)

        # 2. Concentric Defense Range Rings
        ring_radii = [14.0, 22.0, 36.0]
        for r in ring_radii:
            segments = 48
            for i in range(segments):
                a1 = (i / segments) * math.pi * 2.0
                a2 = ((i + 1) / segments) * math.pi * 2.0
                p1 = Vector3(math.sin(a1) * r, 0.05, math.cos(a1) * r)
                p2 = Vector3(math.sin(a2) * r, 0.05, math.cos(a2) * r)
                draw_line_3d(p1, p2, COLOR_RING_MARKER)

        # 3. Central Bunker Concrete Foundation Platform
        draw_cylinder(Vector3(0.0, 0.0, 0.0), 3.4, 3.8, 1.2, 16, COLOR_BASE_CONCRETE)
        draw_cylinder_wires(Vector3(0.0, 0.0, 0.0), 3.41, 3.81, 1.2, 16, COLOR_BASE_BORDER)

        # 4. Energy Shield Dome flash when turret takes damage
        if self.turret.shield_flash > 0.05:
            alpha = int(120 * self.turret.shield_flash)
            draw_sphere(Vector3(0.0, 1.2, 0.0), 3.8, Color(0, 180, 255, alpha))

        # 5. Perimeter Light Pillars
        pillar_angles = [0.0, 1.57, 3.14, 4.71]
        for pa in pillar_angles:
            px = math.sin(pa) * 14.0
            pz = math.cos(pa) * 14.0
            draw_cylinder(Vector3(px, 0.0, pz), 0.35, 0.45, 2.8, 8, Color(70, 75, 85, 255))
            draw_sphere(Vector3(px, 2.8, pz), 0.28, Color(0, 240, 255, 255))

    def draw_reticle_2d(self):
        """Draws the dynamic crosshair, ADS zoom sights, and lead reticle."""
        cx = int(SCREEN_WIDTH * 0.5)
        cy = int(SCREEN_HEIGHT * 0.5)

        if self.camera_rig.is_ads:
            # ADS Sniper / Precision Crosshair
            draw_line(cx - 30, cy, cx - 8, cy, Color(0, 255, 200, 220))
            draw_line(cx + 8, cy, cx + 30, cy, Color(0, 255, 200, 220))
            draw_line(cx, cy - 30, cx, cy - 8, Color(0, 255, 200, 220))
            draw_line(cx, cy + 8, cx, cy + 30, Color(0, 255, 200, 220))
            draw_circle_lines(cx, cy, 18, Color(0, 255, 200, 180))
            draw_circle_lines(cx, cy, 4, Color(255, 50, 80, 240))
            draw_text("ADS PRECISION ZOOM [36° FOV]", cx - 85, cy + 36, 11, Color(0, 255, 200, 200))
        else:
            # Hipfire Dynamic Crosshair with Recoil Bloom
            bloom = int(self.turret.barrel_recoil_left * 25 + self.turret.barrel_recoil_right * 25)
            gap = 10 + bloom
            length = 12
            col = Color(240, 240, 255, 210)
            draw_line(cx - gap - length, cy, cx - gap, cy, col)
            draw_line(cx + gap, cy, cx + gap + length, cy, col)
            draw_line(cx, cy - gap - length, cx, cy - gap, col)
            draw_line(cx, cy + gap, cx, cy + gap + length, col)
            draw_circle(cx, cy, 2, Color(0, 240, 255, 240))

    def draw(self):
        begin_drawing()
        clear_background(Color(10, 12, 18, 255))

        # =====================================================================
        # 1. 3D WORLD RENDERING
        # =====================================================================
        begin_mode_3d(self.camera_rig.camera)

        # Environment & base bunker
        self.draw_environment_3d()

        # Player Defensive Turret Model
        yaw_deg = math.degrees(self.turret.yaw)
        pitch_deg = math.degrees(self.turret.pitch)
        draw_turret_boss_3d(self.turret.pos, yaw_deg, pitch_deg, get_time(), scale=1.0)

        # Drones
        for drone in self.drones:
            if drone.active:
                draw_drone_enemy_3d(drone.pos, drone.yaw, drone.anim_timer, drone.scale)

        # Ground Troopers
        for walker in self.walkers:
            if walker.active:
                is_firing = (walker.state == STATE_WALKER_FIRE)
                draw_humanoid_enemy_3d(walker.pos, walker.yaw, walker.anim_timer, scale=1.0, is_attacking=is_firing)
                # Frontal energy barrier visualization
                if walker.has_shield and walker.state == STATE_WALKER_DEPLOY:
                    yaw_rad = math.radians(walker.yaw)
                    sx = walker.pos.x + math.sin(yaw_rad) * 0.75
                    sz = walker.pos.z + math.cos(yaw_rad) * 0.75
                    draw_cube(Vector3(sx, 1.0, sz), 1.4, 1.2, 0.08, Color(0, 220, 255, 140))
                    draw_cube_wires(Vector3(sx, 1.0, sz), 1.41, 1.21, 0.09, Color(0, 255, 255, 220))

        # Projectiles
        for b in self.player_bullets:
            if b.active:
                draw_cylinder_ex(
                    Vector3(b.pos.x - b.dir.x * b.length * 0.5, b.pos.y - b.dir.y * b.length * 0.5, b.pos.z - b.dir.z * b.length * 0.5),
                    Vector3(b.pos.x + b.dir.x * b.length * 0.5, b.pos.y + b.dir.y * b.length * 0.5, b.pos.z + b.dir.z * b.length * 0.5),
                    b.radius, b.radius, 6, b.color
                )
        for b in self.enemy_bullets:
            if b.active:
                draw_sphere(b.pos, b.radius * 1.5, b.color)

        # 3D Particles
        for p in self.particles:
            if p.active:
                draw_sphere(p.pos, p.size, p.color)

        # X-Ray 3D Overlays (Wireframe Capsules & Hit Vectors)
        if self.show_xray:
            self.telemetry.draw_3d(self.drones, self.walkers, self.player_bullets, self.pattern_capsules_on)

        end_mode_3d()

        # =====================================================================
        # 2. 2D HUD, RETICLE, SETTINGS BAR & X-RAY OVERLAY
        # =====================================================================
        # Dynamic Crosshair & Sights
        self.draw_reticle_2d()

        # HUD Top Banner: Title & Controls
        draw_rectangle(0, 0, SCREEN_WIDTH, 48, Color(12, 16, 26, 240))
        draw_line(0, 48, SCREEN_WIDTH, 48, Color(35, 55, 85, 255))
        draw_text("DRONE DEFENSE 3D - ROTATED CAPSULE COLLISIONS & FSM", 20, 16, 16, Color(240, 245, 255, 255))

        # Gamepad status badge & UI dropdown bar
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)

        # Bottom HUD: Turret Base Health, Score, Wave
        hud_y = SCREEN_HEIGHT - 48
        draw_rectangle(0, hud_y, SCREEN_WIDTH, 48, Color(12, 16, 26, 240))
        draw_line(0, hud_y, SCREEN_WIDTH, hud_y, Color(35, 55, 85, 255))

        # Base HP Bar
        draw_text("BASE INTEGRITY:", 20, hud_y + 16, 13, Color(180, 200, 230, 255))
        bar_w = 220
        bar_h = 16
        bar_x = 145
        bar_y = hud_y + 16
        draw_rectangle(bar_x, bar_y, bar_w, bar_h, Color(35, 40, 50, 255))
        hp_ratio = self.turret.hp / float(self.turret.max_hp)
        fill_col = Color(0, 220, 120, 255) if hp_ratio > 0.35 else Color(255, 60, 60, 255)
        draw_rectangle(bar_x, bar_y, int(bar_w * hp_ratio), bar_h, fill_col)
        draw_rectangle_lines(bar_x, bar_y, bar_w, bar_h, Color(120, 150, 190, 255))
        draw_text(f"{self.turret.hp}%", bar_x + bar_w + 10, hud_y + 16, 13, Color(240, 245, 255, 255))

        # Wave & Score Counters
        draw_text(f"WAVE: {self.wave_number}", 520, hud_y + 16, 14, Color(0, 240, 255, 255))
        draw_text(f"SCORE: {self.turret.score}", 660, hud_y + 16, 14, Color(255, 220, 80, 255))
        draw_text(f"HITS: {self.turret.hits_registered}/{self.turret.shots_fired}", 820, hud_y + 16, 13, Color(180, 210, 240, 255))

        # Control Reminders
        draw_text("[Tab] X-Ray | [F1] Colliders | [F2] Camera Rig | [V] Sights | [R] Reset", 985, hud_y + 16, 11, Color(140, 165, 195, 255))

        # 2D Telemetry Panel
        if self.show_xray:
            self.telemetry.draw_2d(self.turret, self.drones, self.camera_rig,
                                   self.pattern_capsules_on, self.is_camera_damped)

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
    DroneDefenseGame().run(smoke_test=is_smoke)

