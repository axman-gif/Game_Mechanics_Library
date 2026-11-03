# -*- coding: utf-8 -*-
"""
Ballistic Mortar Arc - Parabolic Kinematics & Closed-Form Trajectory Solver
===========================================================================
Section          : 3.2 Combat & Weapons
Pattern Category : Combat & Weapons (Ballistics & Kinematics)
Dimension        : 2D

Problem Solved:
  In artillery combat and long-range ballistic targeting, naive manual aiming or iterative
  brute-force raymarching is computationally slow and fails to guarantee on-target impacts across
  varying elevations. Without an exact closed-form trajectory solver, game systems cannot determine
  in O(1) time whether target coordinates are reachable, nor can they calculate the two distinct
  physical firing solutions (the flat, direct-fire howitzer low arc versus the steep, plunging mortar
  high arc) under gravitational acceleration.

How the Pattern Works:
  1. Parabolic Kinematics:
     In a uniform downward gravitational field g (where screen y increases downwards):
       x(t) = x_0 + v_0 * cos(theta) * t
       y(t) = y_0 - (v_0 * sin(theta) * t - 0.5 * g * t^2)
  2. Closed-Form Ballistic Solver:
     Eliminating time t yields a quadratic equation in tan(theta):
       (g * x^2 / (2 * v^2)) * tan^2(theta) - x * tan(theta) + (y_phys + (g * x^2 / (2 * v^2))) = 0
     Solving via the quadratic formula gives the exact launch angles:
       tan(theta) = (v^2 +/- sqrt(D)) / (g * x)
     where the ballistic discriminant D is:
       D = v^4 - g * (g * x^2 + 2 * y_phys * v^2)
  3. Discriminant Evaluation & Reachability:
     - D < 0: Target is physically out of reach for muzzle speed v. The solver reports failure and
              calculates the minimum required velocity v_min = sqrt(g * (y_phys + sqrt(x^2 + y_phys^2))).
     - D = 0: Target lies at the exact parabolic envelope boundary (single unique launch angle).
     - D > 0: Two valid launch angles exist:
         * Low Arc (Howitzer): tan(theta) = (v^2 - sqrt(D)) / (g * x)  [Fast flight, flat trajectory]
         * High Arc (Mortar):   tan(theta) = (v^2 + sqrt(D)) / (g * x)  [Plunging arc over terrain cover]
  4. Atmospheric Drag & Numerical Comparison:
     The lab simulates ideal closed-form vacuum trajectories alongside a numerical integrator
     modeling atmospheric drag:
       a_drag = -k_d * |v| * v
     allowing real-time side-by-side comparison of range decay, flight time, and apex reduction.

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - Reticle Aim                   : Mouse Cursor OR Gamepad Right Stick (aim target point across proving ground)
  - Cannon Elevation (Manual)     : A / D OR Gamepad Left Stick X (manual barrel angle when pattern is OFF)
  - Muzzle Velocity / Propellant  : W / S OR Gamepad Left Stick Y (increase/decrease charge velocity v_0)
  - Solution Mode Toggle          : Q / E OR Gamepad LB / RB (toggle between High-Arc Mortar vs Low-Arc Howitzer)
  - Atmospheric Drag Toggle       : D OR F2 (toggle air resistance model ON / OFF)
  - Fire Artillery Shell          : Space / Left Mouse Button / RT / Gamepad A (launch physical shell)
  - [Tab] / Gamepad Y (Select)    : Toggle X-Ray Telemetry Overlay (Discriminant, Solver, Flight Times, Drag Loss)
  - [F1]  / Gamepad LB            : Toggle Pattern ON/OFF (Predictive Arc & Auto-Aim Guidance vs Manual Gunnery)
  - [Ctrl +/-]                    : Increase / Decrease UI Font Size
  - [F11]                         : Toggle Fullscreen
  - [R]   / Gamepad Start         : Reset Simulation (rebuild targets, clear craters, reset score)
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
WINDOW_TITLE = "Ballistic Mortar Arc - Parabolic Kinematics & Closed-Form Solver (Raylib)"

# Global Physics Constants
GRAVITY_DEFAULT = 360.0        # Constant gravitational acceleration downward (pixels/sec^2)
DRAG_COEFFICIENT_DEFAULT = 0.0014 # Atmospheric aerodynamic velocity-squared drag coefficient
CANNON_BASE_X = 140.0         # Artillery chassis horizontal placement
BARREL_LENGTH = 58.0          # Artillery barrel length in pixels
MIN_MUZZLE_VELOCITY = 220.0   # Minimum propellant charge speed
MAX_MUZZLE_VELOCITY = 750.0   # Maximum propellant charge speed
TERRAIN_SEGMENTS = 64         # Number of terrain vertices across the screen width

# Solution Type Enum (C++ equivalent: enum class BallisticMode : uint8_t { HighArc = 0, LowArc = 1 })
MODE_HIGH_ARC = 0
MODE_LOW_ARC = 1

# Target Type Enum
TARGET_BUNKER = 0
TARGET_FUEL_DEPOT = 1
TARGET_CONVOY = 2


# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATION
# ==============================================================================

class BallisticSolution:
    """
    Pure data structure representing the analytical output of the Closed-Form Ballistic Solver.
    
    C++ Equivalent:
      struct BallisticSolution {
          bool valid;
          bool in_range;
          float discriminant;
          float theta_high_rad;
          float theta_low_rad;
          float theta_high_deg;
          float theta_low_deg;
          float time_flight_high;
          float time_flight_low;
          float v_min_required;
          float apex_x_high;
          float apex_y_high;
          float apex_x_low;
          float apex_y_low;
          float r_max_flat;
      };
    """
    def __init__(self):
        self.valid = False
        self.in_range = False
        self.discriminant = 0.0
        self.theta_high_rad = 0.0
        self.theta_low_rad = 0.0
        self.theta_high_deg = 0.0
        self.theta_low_deg = 0.0
        self.time_flight_high = 0.0
        self.time_flight_low = 0.0
        self.v_min_required = 0.0
        self.apex_x_high = 0.0
        self.apex_y_high = 0.0
        self.apex_x_low = 0.0
        self.apex_y_low = 0.0
        self.r_max_flat = 0.0


class BallisticSolver:
    """
    Pattern: Closed-Form Ballistic Trajectory Solver.
    
    Why it works:
      Standard ballistic equations express x(t) and y(t) parametrically with respect to time t:
        x = v * cos(theta) * t  =>  t = x / (v * cos(theta))
        y = v * sin(theta) * t - 0.5 * g * t^2
      
      Substituting t into y produces:
        y = x * tan(theta) - (g * x^2) / (2 * v^2 * cos^2(theta))
      
      Using the trigonometric identity 1 / cos^2(theta) = 1 + tan^2(theta):
        y = x * tan(theta) - (g * x^2 / (2 * v^2)) * (1 + tan^2(theta))
      
      Multiplying by (2 * v^2 / (g * x^2)) yields a clean quadratic in tan(theta):
        tan^2(theta) - (2 * v^2 / (g * x)) * tan(theta) + (1 + 2 * v^2 * y / (g * x^2)) = 0
      
      Applying the quadratic formula yields the exact closed-form equation:
        tan(theta) = (v^2 +/- sqrt(v^4 - g * (g * x^2 + 2 * y * v^2))) / (g * x)
      
      where:
        - Discriminant D = v^4 - g * (g * x^2 + 2 * y * v^2)
        - D < 0  => Out of reach (no real firing angle can hit target)
        - D == 0 => Target lies exactly on maximum parabolic reach boundary
        - D > 0  => Two physical solutions:
                    (+) High Arc (plunging mortar shell)
                    (-) Low Arc (direct-fire flat trajectory howitzer)
    """
    def __init__(self, gravity: float = GRAVITY_DEFAULT):
        self.gravity = float(gravity)

    def solve(self, x0: float, y0: float, xt: float, yt: float, v0: float) -> BallisticSolution:
        """
        Solves closed-form launch angles and trajectory telemetry for target coordinates.
        In screen space, y0 and yt increase downwards, so physical delta y is (y0 - yt).
        """
        sol = BallisticSolution()
        dx = float(xt - x0)
        # Avoid singular divide-by-zero if target is directly on or behind muzzle
        if dx < 10.0:
            dx = 10.0
        
        # Physical vertical delta: positive when target is higher in sky (smaller screen y)
        y_phys = float(y0 - yt)
        v = float(max(v0, 10.0))
        g = float(self.gravity)

        v2 = v * v
        v4 = v2 * v2
        dx2 = dx * dx

        # Minimum launch speed required to hit coordinate (x, y_phys)
        hypot_dist = math.sqrt(dx2 + y_phys * y_phys)
        v_min_sq = g * (y_phys + hypot_dist)
        if v_min_sq > 0.0:
            sol.v_min_required = math.sqrt(v_min_sq)
        else:
            sol.v_min_required = 0.0

        # Maximum theoretical flat-ground range R_max = v^2 / g
        sol.r_max_flat = v2 / g

        # Discriminant calculation
        bracket = g * dx2 + 2.0 * y_phys * v2
        disc = v4 - g * bracket
        sol.discriminant = disc

        if disc < 0.0:
            # Physically out of reach
            sol.in_range = False
            sol.valid = False
            return sol

        sol.in_range = True
        sol.valid = True
        sqrt_disc = math.sqrt(max(disc, 0.0))
        denom = g * dx

        # Low Arc: Howitzer direct-fire solution (minus branch)
        tan_low = (v2 - sqrt_disc) / denom
        theta_low = math.atan(tan_low)
        sol.theta_low_rad = theta_low
        sol.theta_low_deg = math.degrees(theta_low)

        # High Arc: Mortar plunging solution (plus branch)
        tan_high = (v2 + sqrt_disc) / denom
        theta_high = math.atan(tan_high)
        sol.theta_high_rad = theta_high
        sol.theta_high_deg = math.degrees(theta_high)

        # Time of flight for both solutions: t = x / (v * cos(theta))
        cos_low = math.cos(theta_low)
        if abs(cos_low) > 0.0001:
            sol.time_flight_low = dx / (v * cos_low)
        else:
            sol.time_flight_low = 0.0

        cos_high = math.cos(theta_high)
        if abs(cos_high) > 0.0001:
            sol.time_flight_high = dx / (v * cos_high)
        else:
            sol.time_flight_high = 0.0

        # Apex calculations: vertical velocity vy = 0 => t_apex = (v * sin(theta)) / g
        # High Arc Apex:
        sin_high = math.sin(theta_high)
        if sin_high > 0.0:
            t_apex_high = (v * sin_high) / g
            sol.apex_x_high = x0 + v * cos_high * t_apex_high
            sol.apex_y_high = y0 - (v * sin_high * t_apex_high - 0.5 * g * t_apex_high * t_apex_high)
        else:
            sol.apex_x_high = x0
            sol.apex_y_high = y0

        # Low Arc Apex:
        sin_low = math.sin(theta_low)
        if sin_low > 0.0:
            t_apex_low = (v * sin_low) / g
            sol.apex_x_low = x0 + v * cos_low * t_apex_low
            sol.apex_y_low = y0 - (v * sin_low * t_apex_low - 0.5 * g * t_apex_low * t_apex_low)
        else:
            sol.apex_x_low = x0
            sol.apex_y_low = y0

        return sol

    def sample_vacuum_points(self, x0: float, y0: float, v0: float, theta_rad: float, t_total: float, sample_count: int):
        """
        Generates discrete Vector2 coordinates along the exact analytical vacuum parabola.
        """
        pts = []
        if sample_count < 2 or t_total <= 0.0:
            return pts

        v = float(v0)
        theta = float(theta_rad)
        vx = v * math.cos(theta)
        vy_phys = v * math.sin(theta)
        g = float(self.gravity)

        step_t = t_total / float(sample_count - 1)
        for i in range(sample_count):
            t = float(i) * step_t
            px = x0 + vx * t
            py = y0 - (vy_phys * t - 0.5 * g * t * t)
            pts.append(Vector2(float(px), float(py)))
        return pts

    def sample_drag_points(self, x0: float, y0: float, v0: float, theta_rad: float, kd: float, terrain_func, max_time: float = 6.0, dt: float = 0.016):
        """
        Runs numerical Euler integration with aerodynamic velocity-squared drag:
          a_drag = -k_d * |v| * v
        Stops when ground is hit or out of bounds.
        """
        pts = []
        pts.append(Vector2(float(x0), float(y0)))

        px = float(x0)
        py = float(y0)
        v = float(v0)
        theta = float(theta_rad)
        vx = v * math.cos(theta)
        vy = -v * math.sin(theta)  # Screen space downward is positive
        g = float(self.gravity)
        drag_k = float(kd)

        t = 0.0
        while t < max_time and px < 1300.0 and py < 750.0:
            speed = math.sqrt(vx * vx + vy * vy)
            ax_drag = -drag_k * speed * vx
            ay_drag = -drag_k * speed * vy

            ax = ax_drag
            ay = g + ay_drag

            px = px + vx * dt
            py = py + vy * dt
            vx = vx + ax * dt
            vy = vy + ay * dt
            t = t + dt

            ground_y = terrain_func(px)
            if py >= ground_y:
                pts.append(Vector2(float(px), float(ground_y)))
                break
            pts.append(Vector2(float(px), float(py)))

        return pts


# ==============================================================================
# BLOCK 2: WORLD SIMULATION & ENTITIES
# ==============================================================================

class TerrainMap:
    """
    Destructible 2D Heightfield Terrain with Localized Blast Crater Deformation.
    C++ Equivalent:
      struct TerrainMap {
          float heights[TERRAIN_SEGMENTS + 1];
          float segment_width;
      };
    """
    def __init__(self, segments: int = TERRAIN_SEGMENTS, width: float = float(SCREEN_WIDTH)):
        self.segments = segments
        self.width = width
        self.segment_width = width / float(segments)
        self.heights = []
        self.init_terrain()

    def init_terrain(self):
        """Initializes rolling hills across the proving ground."""
        self.heights = []
        for i in range(self.segments + 1):
            x = float(i) * self.segment_width
            # Compound sinusoidal rolling hill formula
            base_y = 575.0 + 35.0 * math.sin(x * 0.0052) + 22.0 * math.cos(x * 0.0135) - 14.0 * math.sin(x * 0.0028)
            # Flatten artillery launch plateau on left
            if x < 260.0:
                blend = x / 260.0
                base_y = 560.0 * (1.0 - blend) + base_y * blend
            self.heights.append(float(base_y))

    def get_height(self, world_x: float) -> float:
        """Interpolates terrain height at an arbitrary continuous x coordinate."""
        clamped_x = float(clamp(world_x, 0.0, self.width))
        idx_float = clamped_x / self.segment_width
        idx = int(idx_float)
        if idx >= self.segments:
            return float(self.heights[self.segments])
        t = idx_float - float(idx)
        y1 = self.heights[idx]
        y2 = self.heights[idx + 1]
        return float(y1 + (y2 - y1) * t)

    def apply_crater(self, cx: float, cy: float, radius: float, depth: float):
        """Deforms terrain nodes downwards within the explosive blast radius."""
        r = float(radius)
        d = float(depth)
        for i in range(len(self.heights)):
            x = float(i) * self.segment_width
            dist_x = abs(x - cx)
            if dist_x < r:
                # Hemispherical indentation curve
                factor = math.cos((dist_x / r) * (math.pi * 0.5))
                indent = d * factor
                # Lower the ground (increase screen y), clamped to avoid piercing the screen bottom
                self.heights[i] = min(680.0, self.heights[i] + indent)

    def draw(self):
        """Renders solid terrain with earth strata and grass surface band."""
        color_grass = Color(65, 145, 75, 255)
        color_subsoil = Color(72, 54, 40, 255)
        color_deep_earth = Color(38, 28, 22, 255)

        for i in range(self.segments):
            x1 = float(i) * self.segment_width
            x2 = float(i + 1) * self.segment_width
            y1 = self.heights[i]
            y2 = self.heights[i + 1]
            bottom = float(SCREEN_HEIGHT)

            # Draw deep earth foundation quads as two triangles
            v_tl = Vector2(x1, y1)
            v_tr = Vector2(x2, y2)
            v_br = Vector2(x2, bottom)
            v_bl = Vector2(x1, bottom)

            draw_triangle(v_tl, v_bl, v_tr, color_subsoil)
            draw_triangle(v_tr, v_bl, v_br, color_deep_earth)

            # Draw surface grass border
            draw_line_ex(v_tl, v_tr, 4.0, color_grass)


class ArtilleryCannon:
    """
    Articulated Artillery Cannon with Adjustable Elevation, Propellant Power, and Recoil Damping.
    """
    def __init__(self, x: float, y: float):
        self.x = float(x)
        self.y = float(y)
        self.angle_deg = 45.0
        self.v0 = 480.0
        self.recoil_offset = 0.0
        self.barrel_length = float(BARREL_LENGTH)

    def update(self, dt: float):
        # Smooth exponential spring recovery for barrel recoil
        self.recoil_offset = damp(self.recoil_offset, 0.0, 16.0, dt)

    def trigger_recoil(self):
        self.recoil_offset = 14.0

    def get_muzzle_pos(self) -> Vector2:
        rad = math.radians(self.angle_deg)
        effective_len = self.barrel_length - self.recoil_offset
        pivot_x = self.x
        pivot_y = self.y - 18.0
        mx = pivot_x + math.cos(rad) * effective_len
        my = pivot_y - math.sin(rad) * effective_len
        return Vector2(float(mx), float(my))

    def draw(self):
        pivot_x = int(self.x)
        pivot_y = int(self.y - 18)
        rad = math.radians(self.angle_deg)

        # 1. Concrete ground anchoring pad & stabilizer spade
        draw_rectangle(pivot_x - 38, int(self.y - 6), 76, 12, Color(45, 52, 60, 255))
        draw_rectangle_lines(pivot_x - 38, int(self.y - 6), 76, 12, Color(85, 95, 108, 255))
        draw_line_ex(Vector2(float(pivot_x - 28), float(self.y)), Vector2(float(pivot_x - 44), float(self.y + 10)), 5.0, Color(30, 36, 42, 255))

        # 2. Heavy artillery carriage chassis
        draw_rectangle(pivot_x - 22, pivot_y - 2, 44, 18, Color(55, 68, 58, 255))
        draw_rectangle_lines(pivot_x - 22, pivot_y - 2, 44, 18, Color(95, 115, 100, 255))

        # 3. Rotating articulated gun barrel
        eff_len = self.barrel_length - self.recoil_offset
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        start_v = Vector2(float(pivot_x), float(pivot_y))
        end_v = Vector2(float(pivot_x + cos_a * eff_len), float(pivot_y - sin_a * eff_len))

        # Heavy steel barrel tube
        draw_line_ex(start_v, end_v, 11.0, Color(40, 48, 54, 255))
        draw_line_ex(start_v, end_v, 7.0, Color(75, 88, 96, 255))

        # Muzzle brake collar at tip
        muzzle_v = self.get_muzzle_pos()
        draw_circle(int(muzzle_v.x), int(muzzle_v.y), 6.0, Color(110, 125, 138, 255))
        draw_circle_lines(int(muzzle_v.x), int(muzzle_v.y), 6.0, Color(25, 30, 35, 255))

        # 4. Central elevation trunnion pivot hub & dial
        draw_circle(pivot_x, pivot_y, 13.0, Color(42, 50, 56, 255))
        draw_circle(pivot_x, pivot_y, 9.0, Color(88, 102, 112, 255))
        draw_circle(pivot_x, pivot_y, 4.0, Color(220, 180, 60, 255))

        # Angle indicator line on trunnion hub
        hub_ind = Vector2(float(pivot_x + cos_a * 9.0), float(pivot_y - sin_a * 9.0))
        draw_line_ex(Vector2(float(pivot_x), float(pivot_y)), hub_ind, 2.5, Color(255, 230, 110, 255))


class Shell:
    """
    Pre-allocated Physical Shell Munition.
    """
    def __init__(self):
        self.active = False
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.has_drag = False
        self.trail_timer = 0.0
        self.age = 0.0
        self.arc_type = MODE_HIGH_ARC

    def launch(self, start_pos: Vector2, v0: float, angle_deg: float, has_drag: bool, arc_type: int):
        self.active = True
        self.x = float(start_pos.x)
        self.y = float(start_pos.y)
        rad = math.radians(angle_deg)
        self.vx = v0 * math.cos(rad)
        self.vy = -v0 * math.sin(rad)  # Screen y negative upward
        self.has_drag = has_drag
        self.trail_timer = 0.0
        self.age = 0.0
        self.arc_type = arc_type


class ShellPool:
    """
    Fixed-Capacity Object Pool for Mortar Munitions (Zero Frame Allocations).
    """
    def __init__(self, capacity: int = 32):
        self.capacity = capacity
        self.shells = []
        for i in range(capacity):
            self.shells.append(Shell())

    def spawn(self, start_pos: Vector2, v0: float, angle_deg: float, has_drag: bool, arc_type: int) -> bool:
        for i in range(self.capacity):
            s = self.shells[i]
            if not s.active:
                s.launch(start_pos, v0, angle_deg, has_drag, arc_type)
                return True
        return False

    def update(self, dt: float, gravity: float, kd: float, terrain: TerrainMap, particle_pool, sfx, shake, targets):
        g = float(gravity)
        drag_k = float(kd)

        for i in range(self.capacity):
            s = self.shells[i]
            if not s.active:
                continue

            s.age += dt
            s.trail_timer += dt

            # Physics integration
            if s.has_drag:
                speed = math.sqrt(s.vx * s.vx + s.vy * s.vy)
                ax = -drag_k * speed * s.vx
                ay = g - drag_k * speed * s.vy
            else:
                ax = 0.0
                ay = g

            s.x += s.vx * dt
            s.y += s.vy * dt
            s.vx += ax * dt
            s.vy += ay * dt

            # Trailing smoke particle emission
            if s.trail_timer >= 0.022:
                s.trail_timer = 0.0
                particle_pool.spawn_trail(s.x, s.y, s.arc_type)

            # Check collision with ground terrain
            ground_y = terrain.get_height(s.x)
            impact = False
            if s.y >= ground_y:
                impact = True
                s.y = ground_y

            # Check bounds
            if s.x > 1290.0 or s.x < -20.0 or s.y > 730.0:
                s.active = False
                continue

            # Check impact against combat targets
            if not impact:
                for t_idx in range(len(targets.list)):
                    t = targets.list[t_idx]
                    if t.is_alive and t.check_point_collision(s.x, s.y):
                        impact = True
                        break

            if impact:
                s.active = False
                sfx.play("explosion", 0.75)
                shake.add_trauma(0.55)
                # Apply blast damage to targets and terrain crater
                targets.apply_blast_damage(s.x, s.y, 55.0, 85.0, particle_pool, sfx, shake)
                terrain.apply_crater(s.x, s.y, 40.0, 18.0)
                particle_pool.spawn_explosion(s.x, s.y, 28)

    def draw(self):
        for i in range(self.capacity):
            s = self.shells[i]
            if not s.active:
                continue

            angle = math.atan2(s.vy, s.vx)
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)

            # Projectile casing drawn along direction of travel
            tail = Vector2(float(s.x - cos_a * 8.0), float(s.y - sin_a * 8.0))
            head = Vector2(float(s.x + cos_a * 5.0), float(s.y + sin_a * 5.0))

            color_core = Color(255, 230, 80, 255) if s.arc_type == MODE_HIGH_ARC else Color(80, 220, 255, 255)
            draw_line_ex(tail, head, 4.0, color_core)
            draw_circle(int(head.x), int(head.y), 3.0, Color(255, 255, 255, 255))


class Particle:
    """Particle entity for smoke plumes, fiery shrapnel, and explosive blast shockwaves."""
    def __init__(self):
        self.active = False
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.life = 0.0
        self.max_life = 1.0
        self.size = 2.0
        self.p_type = 0  # 0: Smoke, 1: Fire, 2: Debris Chunk
        self.r = 255
        self.g = 255
        self.b = 255


class ParticlePool:
    """Pre-allocated pool of 240 particles with zero runtime heap churn."""
    def __init__(self, capacity: int = 240):
        self.capacity = capacity
        self.particles = []
        for i in range(capacity):
            self.particles.append(Particle())

    def spawn_trail(self, x: float, y: float, arc_type: int):
        for i in range(self.capacity):
            p = self.particles[i]
            if not p.active:
                p.active = True
                p.x = x + random.uniform(-1.5, 1.5)
                p.y = y + random.uniform(-1.5, 1.5)
                p.vx = random.uniform(-10.0, 10.0)
                p.vy = random.uniform(-10.0, 5.0)
                p.life = 0.0
                p.max_life = random.uniform(0.35, 0.65)
                p.size = random.uniform(3.0, 5.5)
                p.p_type = 0
                if arc_type == MODE_HIGH_ARC:
                    p.r = 230
                    p.g = 190
                    p.b = 100
                else:
                    p.r = 100
                    p.g = 200
                    p.b = 240
                return

    def spawn_explosion(self, x: float, y: float, count: int = 25):
        spawned = 0
        for i in range(self.capacity):
            if spawned >= count:
                break
            p = self.particles[i]
            if not p.active:
                p.active = True
                p.x = x
                p.y = y
                angle = random.uniform(0.0, math.pi * 2.0)
                speed = random.uniform(40.0, 260.0)
                p.vx = math.cos(angle) * speed
                p.vy = math.sin(angle) * speed - random.uniform(20.0, 80.0)
                p.life = 0.0
                p.max_life = random.uniform(0.45, 1.1)
                p.size = random.uniform(3.5, 8.0)
                # Randomize between fire spark and dirt chunk
                if random.random() < 0.65:
                    p.p_type = 1
                    p.r = 255
                    p.g = random.randint(120, 230)
                    p.b = 40
                else:
                    p.p_type = 2
                    p.r = random.randint(70, 110)
                    p.g = random.randint(55, 85)
                    p.b = random.randint(35, 55)
                spawned += 1

    def update(self, dt: float, terrain: TerrainMap):
        for i in range(self.capacity):
            p = self.particles[i]
            if not p.active:
                continue

            p.life += dt
            if p.life >= p.max_life:
                p.active = False
                continue

            p.x += p.vx * dt
            p.y += p.vy * dt

            if p.p_type == 2:  # Debris gravity and bounce
                p.vy += 380.0 * dt
                ground_y = terrain.get_height(p.x)
                if p.y >= ground_y:
                    p.y = ground_y
                    p.vy = -p.vy * 0.35
                    p.vx *= 0.6
            elif p.p_type == 0:  # Smoke drag and expansion
                p.size += dt * 5.0
                p.vx *= 0.95
                p.vy *= 0.95

    def draw(self):
        for i in range(self.capacity):
            p = self.particles[i]
            if not p.active:
                continue

            progress = p.life / p.max_life
            alpha_val = int(255.0 * (1.0 - progress))
            if alpha_val < 0:
                alpha_val = 0
            if alpha_val > 255:
                alpha_val = 255

            col = Color(p.r, p.g, p.b, alpha_val)
            draw_circle(int(p.x), int(p.y), float(p.size * (1.0 - progress * 0.4)), col)


class CombatTarget:
    """Destructible combat proving ground entity (Bunker, Fuel Depot, or Mobile Convoy)."""
    def __init__(self, target_type: int, x: float, max_hp: float, width: float, height: float):
        self.type = target_type
        self.x = float(x)
        self.y = 0.0
        self.max_hp = float(max_hp)
        self.hp = float(max_hp)
        self.width = float(width)
        self.height = float(height)
        self.is_alive = True
        self.respawn_timer = 0.0
        self.vx = 32.0 if target_type == TARGET_CONVOY else 0.0
        self.score_value = 150 if target_type == TARGET_BUNKER else (300 if target_type == TARGET_FUEL_DEPOT else 200)

    def update(self, dt: float, terrain: TerrainMap):
        if not self.is_alive:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0.0:
                self.is_alive = True
                self.hp = self.max_hp
            return

        # Mobile convoy vehicle patrols along terrain
        if self.type == TARGET_CONVOY:
            self.x += self.vx * dt
            if self.x > 750.0:
                self.x = 750.0
                self.vx = -abs(self.vx)
            elif self.x < 380.0:
                self.x = 380.0
                self.vx = abs(self.vx)

        self.y = terrain.get_height(self.x)

    def check_point_collision(self, px: float, py: float) -> bool:
        if not self.is_alive:
            return False
        half_w = self.width * 0.5
        top = self.y - self.height
        return (self.x - half_w <= px <= self.x + half_w) and (top <= py <= self.y)

    def take_damage(self, amount: float) -> bool:
        if not self.is_alive:
            return False
        self.hp -= amount
        if self.hp <= 0.0:
            self.hp = 0.0
            self.is_alive = False
            self.respawn_timer = 5.0
            return True  # Destroyed
        return False

    def draw(self):
        cx = int(self.x)
        ground_y = int(self.y)
        half_w = int(self.width * 0.5)
        top = int(ground_y - self.height)

        if not self.is_alive:
            # Draw ruined, smoking debris footprint
            draw_rectangle(cx - half_w, ground_y - 6, int(self.width), 8, Color(30, 25, 25, 255))
            draw_text("WRECK", cx - 18, ground_y - 18, 10, Color(180, 80, 80, 200))
            return

        if self.type == TARGET_BUNKER:
            # Concrete reinforced bunker pillbox
            draw_rectangle(cx - half_w, top, int(self.width), int(self.height), Color(70, 78, 85, 255))
            draw_rectangle_lines(cx - half_w, top, int(self.width), int(self.height), Color(130, 142, 155, 255))
            # Observation slit
            draw_rectangle(cx - 16, top + 8, 32, 6, Color(20, 22, 26, 255))
            draw_rectangle(cx - 14, top + 9, 28, 4, Color(70, 210, 255, 220))
            # Antenna
            draw_line(cx + 12, top, cx + 12, top - 14, Color(180, 190, 200, 255))
            draw_circle(cx + 12, top - 14, 2.5, Color(255, 60, 60, 255))

        elif self.type == TARGET_FUEL_DEPOT:
            # High-explosive dual cylindrical fuel tanks
            tank_w = int(self.width * 0.44)
            # Left tank
            draw_rectangle(cx - half_w, top, tank_w, int(self.height), Color(180, 45, 45, 255))
            draw_rectangle_lines(cx - half_w, top, tank_w, int(self.height), Color(240, 100, 100, 255))
            # Right tank
            draw_rectangle(cx + 2, top, tank_w, int(self.height), Color(180, 45, 45, 255))
            draw_rectangle_lines(cx + 2, top, tank_w, int(self.height), Color(240, 100, 100, 255))
            # Yellow hazard stripe across tanks
            draw_rectangle(cx - half_w, top + 12, int(self.width), 6, Color(245, 210, 40, 255))
            draw_text("FUEL", cx - 14, top + 20, 10, Color(255, 255, 255, 255))

        elif self.type == TARGET_CONVOY:
            # Armored transport vehicle with wheels
            draw_rectangle(cx - half_w, top + 8, int(self.width), int(self.height - 8), Color(88, 105, 75, 255))
            draw_rectangle_lines(cx - half_w, top + 8, int(self.width), int(self.height - 8), Color(135, 160, 115, 255))
            # Cab cabin
            cab_dir = 1 if self.vx >= 0 else -1
            cab_x = cx + 8 if cab_dir == 1 else cx - half_w
            draw_rectangle(cab_x, top + 2, 14, 8, Color(65, 80, 55, 255))
            # Wheels
            draw_circle(cx - half_w + 6, ground_y, 4.0, Color(25, 25, 25, 255))
            draw_circle(cx, ground_y, 4.0, Color(25, 25, 25, 255))
            draw_circle(cx + half_w - 6, ground_y, 4.0, Color(25, 25, 25, 255))

        # Health Bar over target
        bar_w = int(self.width)
        bar_h = 4
        bar_x = cx - half_w
        bar_y = top - 8
        pct = clamp(self.hp / self.max_hp, 0.0, 1.0)
        draw_rectangle(bar_x, bar_y, bar_w, bar_h, Color(35, 35, 35, 220))
        draw_rectangle(bar_x, bar_y, int(float(bar_w) * pct), bar_h, Color(80, 240, 110, 255) if pct > 0.4 else Color(240, 70, 70, 255))


class TargetManager:
    """Coordinates active combat targets, damage propagation, and scoring."""
    def __init__(self, terrain: TerrainMap):
        self.list = []
        self.list.append(CombatTarget(TARGET_CONVOY, 520.0, 50.0, 48.0, 22.0))
        self.list.append(CombatTarget(TARGET_BUNKER, 840.0, 100.0, 54.0, 32.0))
        self.list.append(CombatTarget(TARGET_FUEL_DEPOT, 1080.0, 70.0, 62.0, 40.0))

        for i in range(len(self.list)):
            self.list[i].y = terrain.get_height(self.list[i].x)

    def update(self, dt: float, terrain: TerrainMap):
        for i in range(len(self.list)):
            self.list[i].update(dt, terrain)

    def apply_blast_damage(self, blast_x: float, blast_y: float, radius: float, max_dmg: float, particle_pool, sfx, shake):
        r = float(radius)
        for i in range(len(self.list)):
            t = self.list[i]
            if not t.is_alive:
                continue

            dx = t.x - blast_x
            dy = (t.y - t.height * 0.5) - blast_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist <= r:
                falloff = 1.0 - (dist / r)
                dmg = max_dmg * falloff
                destroyed = t.take_damage(dmg)
                sfx.play("hit", 0.6)

                if destroyed:
                    sfx.play("coin", 0.8)
                    if t.type == TARGET_FUEL_DEPOT:
                        # Massive secondary chain explosion from fuel depot
                        sfx.play("explosion", 0.95)
                        shake.add_trauma(0.8)
                        particle_pool.spawn_explosion(t.x, t.y - 15.0, 48)

    def draw(self):
        for i in range(len(self.list)):
            self.list[i].draw()


# ==============================================================================
# BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY
# ==============================================================================

def draw_trajectory_prediction(solver: BallisticSolver, cannon: ArtilleryCannon, sol: BallisticSolution,
                               target_x: float, target_y: float, mode: int, drag_enabled: bool,
                               kd: float, terrain: TerrainMap, pattern_enabled: bool):
    """
    Renders the predictive analytical trajectory curves, apex markers, and ground impact points.
    """
    if not pattern_enabled:
        return

    muzzle = cannon.get_muzzle_pos()
    active_rad = sol.theta_high_rad if mode == MODE_HIGH_ARC else sol.theta_low_rad
    active_t = sol.time_flight_high if mode == MODE_HIGH_ARC else sol.time_flight_low
    apex_x = sol.apex_x_high if mode == MODE_HIGH_ARC else sol.apex_x_low
    apex_y = sol.apex_y_high if mode == MODE_HIGH_ARC else sol.apex_y_low

    # 1. Closed-Form Analytical Vacuum Trajectory (Cyan dotted curve)
    if sol.in_range and active_t > 0.0:
        pts = solver.sample_vacuum_points(muzzle.x, muzzle.y, cannon.v0, active_rad, active_t, 48)
        color_arc = Color(70, 220, 255, 230) if mode == MODE_LOW_ARC else Color(255, 215, 80, 230)

        for i in range(len(pts) - 1):
            p1 = pts[i]
            p2 = pts[i + 1]
            if i % 2 == 0:  # Dotted pattern
                draw_line_ex(p1, p2, 2.5, color_arc)

        # Draw Apex Marker
        draw_circle(int(apex_x), int(apex_y), 5.0, Color(255, 255, 255, 255))
        draw_circle_lines(int(apex_x), int(apex_y), 8.0, color_arc)
        alt_px = int(muzzle.y - apex_y)
        draw_text(f"APEX (+{alt_px}px)", int(apex_x - 36), int(apex_y - 20), 10, Color(255, 255, 255, 220))

        # Projected impact point crosshair
        imp_x = int(target_x)
        imp_y = int(target_y)
        draw_circle_lines(imp_x, imp_y, 10.0, color_arc)
        draw_line(imp_x - 12, imp_y, imp_x + 12, imp_y, color_arc)
        draw_line(imp_x, imp_y - 12, imp_x, imp_y + 12, color_arc)

    # 2. Atmospheric Drag Curve (Amber dashed line when Drag is toggled ON)
    if drag_enabled:
        pts_drag = solver.sample_drag_points(muzzle.x, muzzle.y, cannon.v0, active_rad, kd, terrain.get_height, 6.0, 0.02)
        color_drag = Color(255, 120, 50, 220)
        for i in range(len(pts_drag) - 1):
            if i % 3 != 0:
                draw_line_ex(pts_drag[i], pts_drag[i + 1], 2.0, color_drag)

        if len(pts_drag) > 0:
            last_pt = pts_drag[len(pts_drag) - 1]
            draw_circle(int(last_pt.x), int(last_pt.y), 4.5, Color(255, 100, 40, 255))
            draw_text("DRAG IMPACT", int(last_pt.x - 30), int(last_pt.y + 10), 10, color_drag)


def draw_target_crosshair(tx: float, ty: float, in_range: bool, pattern_enabled: bool):
    """Draws responsive tactical crosshair with range bracket indicators."""
    cx = int(tx)
    cy = int(ty)
    col = Color(80, 240, 120, 255) if in_range else Color(255, 70, 70, 255)
    if not pattern_enabled:
        col = Color(200, 210, 220, 180)

    # Crosshair central reticle
    draw_circle_lines(cx, cy, 14.0, col)
    draw_circle(cx, cy, 2.5, col)
    draw_line(cx - 20, cy, cx - 8, cy, col)
    draw_line(cx + 8, cy, cx + 20, cy, col)
    draw_line(cx, cy - 20, cx, cy - 8, col)
    draw_line(cx, cy + 8, cx, cy + 20, col)

    # Range readouts below crosshair
    if pattern_enabled:
        if in_range:
            draw_text("IN RANGE", cx - 22, cy + 18, 10, Color(80, 240, 120, 255))
        else:
            draw_text("OUT OF REACH", cx - 34, cy + 18, 10, Color(255, 80, 80, 255))


def draw_xray_telemetry_panel(sol: BallisticSolution, cannon: ArtilleryCannon, solver: BallisticSolver,
                              tx: float, ty: float, mode: int, drag_enabled: bool, kd: float,
                              pattern_enabled: bool):
    """
    Renders comprehensive educational X-Ray Telemetry Overlay exposing internal closed-form math.
    """
    panel_x = 24
    panel_y = 68
    panel_w = 405
    panel_h = 420

    # Semi-transparent high-contrast dashboard background
    draw_rectangle(panel_x, panel_y, panel_w, panel_h, Color(12, 16, 26, 235))
    draw_rectangle_lines(panel_x, panel_y, panel_w, panel_h, Color(45, 75, 115, 255))

    # Header
    draw_rectangle(panel_x, panel_y, panel_w, 26, Color(20, 32, 54, 255))
    draw_text("X-RAY TELEMETRY: BALLISTIC TRAJECTORY SOLVER", panel_x + 10, panel_y + 7, 12, Color(90, 215, 255, 255))

    curr_y = panel_y + 34
    spacing = 16

    # SECTION 1: KINEMATIC CONSTANTS & MUZZLE STATE
    draw_text("[1] Kinematics & Atmosphere", panel_x + 12, curr_y, 11, Color(255, 215, 80, 255))
    curr_y += spacing
    draw_text(f"  Muzzle Speed (V0)  : {cannon.v0:.1f} px/s", panel_x + 12, curr_y, 10, Color(220, 230, 245, 255))
    curr_y += spacing
    draw_text(f"  Barrel Elevation   : {cannon.angle_deg:.1f} deg", panel_x + 12, curr_y, 10, Color(220, 230, 245, 255))
    curr_y += spacing
    draw_text(f"  Gravity (g)        : {solver.gravity:.1f} px/s^2", panel_x + 12, curr_y, 10, Color(220, 230, 245, 255))
    curr_y += spacing
    drag_str = f"ON (k={kd:.5f})" if drag_enabled else "OFF (Vacuum Ideal)"
    draw_text(f"  Atmospheric Drag   : {drag_str}", panel_x + 12, curr_y, 10, Color(255, 150, 70, 255) if drag_enabled else Color(150, 165, 185, 255))
    curr_y += spacing
    draw_text(f"  Max Range (Flat)   : {sol.r_max_flat:.1f} px  (V^2 / g)", panel_x + 12, curr_y, 10, Color(175, 205, 235, 255))
    curr_y += spacing + 4

    # SECTION 2: CLOSED-FORM BALLISTIC MATH & DISCRIMINANT
    draw_text("[2] Closed-Form Solver Equation", panel_x + 12, curr_y, 11, Color(255, 215, 80, 255))
    curr_y += spacing
    draw_text("  tan(th) = (v^2 +/- sqrt(D)) / (g * x)", panel_x + 12, curr_y, 10, Color(100, 230, 255, 255))
    curr_y += spacing
    draw_text("  D = v^4 - g * (g*x^2 + 2*y*v^2)", panel_x + 12, curr_y, 10, Color(140, 175, 215, 255))
    curr_y += spacing

    muzzle = cannon.get_muzzle_pos()
    dx = tx - muzzle.x
    dy_phys = muzzle.y - ty
    draw_text(f"  Target Delta (dx, dy): dx={dx:.1f}px, dy={dy_phys:.1f}px", panel_x + 12, curr_y, 10, Color(220, 230, 245, 255))
    curr_y += spacing

    disc_col = Color(80, 240, 120, 255) if sol.discriminant >= 0.0 else Color(255, 75, 75, 255)
    disc_text = f"D = {sol.discriminant:+.1e}"
    draw_text(f"  Discriminant (D)   : {disc_text}", panel_x + 12, curr_y, 10, disc_col)
    curr_y += spacing

    if sol.in_range:
        draw_text("  Solver Status      : REACHABLE (Real Roots)", panel_x + 12, curr_y, 10, Color(80, 240, 120, 255))
    else:
        draw_text("  Solver Status      : OUT OF RANGE (D < 0)", panel_x + 12, curr_y, 10, Color(255, 75, 75, 255))
        curr_y += spacing
        draw_text(f"  Min Required V0    : {sol.v_min_required:.1f} px/s (+{sol.v_min_required - cannon.v0:.1f})", panel_x + 12, curr_y, 10, Color(255, 180, 80, 255))
    curr_y += spacing + 4

    # SECTION 3: HIGH-ARC VS LOW-ARC SOLUTIONS
    draw_text("[3] Dual Solution Angles (Q / E)", panel_x + 12, curr_y, 11, Color(255, 215, 80, 255))
    curr_y += spacing

    high_tag = " [ACTIVE]" if mode == MODE_HIGH_ARC else ""
    low_tag = " [ACTIVE]" if mode == MODE_LOW_ARC else ""

    col_high = Color(255, 220, 90, 255) if mode == MODE_HIGH_ARC else Color(160, 175, 190, 255)
    col_low = Color(90, 220, 255, 255) if mode == MODE_LOW_ARC else Color(160, 175, 190, 255)

    draw_text(f"  High Arc (Mortar)  : {sol.theta_high_deg:.1f} deg  (t={sol.time_flight_high:.2f}s){high_tag}", panel_x + 12, curr_y, 10, col_high)
    curr_y += spacing
    draw_text(f"  Low Arc (Howitzer) : {sol.theta_low_deg:.1f} deg  (t={sol.time_flight_low:.2f}s){low_tag}", panel_x + 12, curr_y, 10, col_low)
    curr_y += spacing + 4

    # SECTION 4: PATTERN COMPARISON & GUIDANCE
    draw_text("[4] Design Pattern State [F1]", panel_x + 12, curr_y, 11, Color(255, 215, 80, 255))
    curr_y += spacing
    if pattern_enabled:
        draw_text("  Auto-Aim Solver    : ENABLED (Closed-Form Lock)", panel_x + 12, curr_y, 10, Color(80, 240, 120, 255))
        curr_y += spacing
        draw_text("  Predictive Arc     : VISIBLE (Real-Time Parabola)", panel_x + 12, curr_y, 10, Color(80, 240, 120, 255))
    else:
        draw_text("  Auto-Aim Solver    : DISABLED [F1] (Manual Gunnery)", panel_x + 12, curr_y, 10, Color(255, 90, 90, 255))
        curr_y += spacing
        draw_text("  Predictive Arc     : HIDDEN (Manual Estimate)", panel_x + 12, curr_y, 10, Color(255, 90, 90, 255))


# ==============================================================================
# BLOCK 4: MAIN GAME LOOP & AUTOMATED SMOKE TEST
# ==============================================================================

class BallisticMortarGame:
    """
    Main interactive showcase lab demonstrating Parabolic Kinematics & Closed-Form Ballistic Solver.
    """
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()

        # Procedural Audio & Screen Shake
        self.sfx = SoundLibrary()
        self.sfx.init_defaults()
        self.shake = TraumaShake(max_offset_px=14.0, max_angle_deg=2.2, decay_rate=1.35)

        # Environment & Simulation Systems
        self.terrain = TerrainMap(TERRAIN_SEGMENTS, float(SCREEN_WIDTH))
        cannon_y = self.terrain.get_height(CANNON_BASE_X)
        self.cannon = ArtilleryCannon(CANNON_BASE_X, cannon_y)

        self.solver = BallisticSolver(GRAVITY_DEFAULT)
        self.shell_pool = ShellPool(32)
        self.particle_pool = ParticlePool(240)
        self.targets = TargetManager(self.terrain)

        # Gunnery & Lab States
        self.reticle_x = 840.0
        self.reticle_y = 480.0
        self.solution_mode = MODE_HIGH_ARC  # Default to high plunging mortar arc
        self.show_xray = True               # Default ON in single-pattern labs
        self.pattern_enabled = True         # Toggle with [F1]
        self.drag_enabled = False           # Atmospheric drag comparison toggle [D/F2]
        self.kd = DRAG_COEFFICIENT_DEFAULT

        # Gunnery Score Metrics
        self.score = 0
        self.shots_fired = 0
        self.current_solution = BallisticSolution()

    def reset_simulation(self):
        """Restores proving ground, clears craters, resets targets and shells."""
        self.terrain.init_terrain()
        self.cannon.y = self.terrain.get_height(self.cannon.x)
        self.targets = TargetManager(self.terrain)
        self.shell_pool = ShellPool(32)
        self.particle_pool = ParticlePool(240)
        self.score = 0
        self.shots_fired = 0
        self.sfx.play("click", 0.6)

    def update(self):
        dt = min(get_frame_time(), 0.05)

        # 1. Hotkey & Dual Input Toggles
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
            self.sfx.play("click", 0.6)

        if is_dual_pattern_toggle_pressed():
            self.pattern_enabled = not self.pattern_enabled
            self.sfx.play("click", 0.7)

        if is_dual_reset_pressed():
            self.reset_simulation()

        # Toggle Atmospheric Drag with [D] or [F2]
        if is_key_pressed(KEY_D) or is_key_pressed(KEY_F2) or is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_FACE_LEFT):
            self.drag_enabled = not self.drag_enabled
            self.sfx.play("click", 0.6)

        # Toggle High-Arc vs Low-Arc with [Q] / [E] / Gamepad Bumpers
        if is_key_pressed(KEY_Q) or is_key_pressed(KEY_E) or is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_TRIGGER_1) or is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_TRIGGER_1):
            self.solution_mode = MODE_LOW_ARC if self.solution_mode == MODE_HIGH_ARC else MODE_HIGH_ARC
            self.sfx.play("click", 0.6)

        # 2. Reticle Navigation (Mouse + Gamepad Right Stick)
        m_delta = get_mouse_delta()
        if abs(m_delta.x) > 0.4 or abs(m_delta.y) > 0.4:
            m_pos = get_mouse_position()
            self.reticle_x = float(clamp(m_pos.x, 260.0, 1260.0))
            self.reticle_y = float(clamp(m_pos.y, 80.0, 680.0))

        look_vec = get_dual_look_2d()
        look_x = look_vec.x
        look_y = look_vec.y
        if abs(look_x) > 0.05 or abs(look_y) > 0.05:
            self.reticle_x = float(clamp(self.reticle_x + look_x * 480.0 * dt, 260.0, 1260.0))
            self.reticle_y = float(clamp(self.reticle_y + look_y * 480.0 * dt, 80.0, 680.0))

        # 3. Muzzle Velocity / Propellant Charge Adjustments (W/S or Left Stick Y)
        move_vec = get_dual_move_2d()
        move_x = move_vec.x
        move_y = move_vec.y
        if is_key_down(KEY_W) or is_key_down(KEY_UP) or move_y < -0.2:
            self.cannon.v0 = float(clamp(self.cannon.v0 + 130.0 * dt, MIN_MUZZLE_VELOCITY, MAX_MUZZLE_VELOCITY))
        elif is_key_down(KEY_S) or is_key_down(KEY_DOWN) or move_y > 0.2:
            self.cannon.v0 = float(clamp(self.cannon.v0 - 130.0 * dt, MIN_MUZZLE_VELOCITY, MAX_MUZZLE_VELOCITY))

        # 4. Closed-Form Ballistic Solver Evaluation
        muzzle = self.cannon.get_muzzle_pos()
        self.current_solution = self.solver.solve(muzzle.x, muzzle.y, self.reticle_x, self.reticle_y, self.cannon.v0)

        # 5. Cannon Elevation Control:
        # If Pattern is ON: Auto-aim guidance automatically damps barrel elevation to solved angle!
        # If Pattern is OFF: Player manually adjusts elevation with A / D or Left Stick X
        if self.pattern_enabled and self.current_solution.in_range:
            target_angle = self.current_solution.theta_high_deg if self.solution_mode == MODE_HIGH_ARC else self.current_solution.theta_low_deg
            self.cannon.angle_deg = damp(self.cannon.angle_deg, target_angle, 14.0, dt)
        else:
            if is_key_down(KEY_A) or is_key_down(KEY_LEFT) or move_x < -0.2:
                self.cannon.angle_deg = float(clamp(self.cannon.angle_deg + 45.0 * dt, -10.0, 88.0))
            elif is_key_down(KEY_D) or is_key_down(KEY_RIGHT) or move_x > 0.2:
                self.cannon.angle_deg = float(clamp(self.cannon.angle_deg - 45.0 * dt, -10.0, 88.0))

        self.cannon.update(dt)

        # 6. Firing Action
        if is_dual_primary_fire_pressed():
            fired = self.shell_pool.spawn(
                self.cannon.get_muzzle_pos(),
                self.cannon.v0,
                self.cannon.angle_deg,
                self.drag_enabled,
                self.solution_mode
            )
            if fired:
                self.shots_fired += 1
                self.cannon.trigger_recoil()
                self.shake.add_trauma(0.32)
                self.sfx.play("sniper", 0.7)
                self.particle_pool.spawn_explosion(muzzle.x, muzzle.y, 8)

        # 7. Update Simulation Entities
        self.shell_pool.update(dt, self.solver.gravity, self.kd, self.terrain, self.particle_pool, self.sfx, self.shake, self.targets)
        self.particle_pool.update(dt, self.terrain)
        self.targets.update(dt, self.terrain)

    def draw(self):
        begin_drawing()
        clear_background(Color(14, 18, 28, 255))

        # Camera Trauma Screen Shake
        dt = get_frame_time()
        dx, dy, rot = self.shake.update(dt)

        # 1. Background Grid & Proving Ground Backdrop
        for grid_x in range(0, SCREEN_WIDTH, 80):
            draw_line(grid_x, 0, grid_x, SCREEN_HEIGHT, Color(22, 28, 42, 120))
        for grid_y in range(0, SCREEN_HEIGHT, 60):
            draw_line(0, grid_y, SCREEN_WIDTH, grid_y, Color(22, 28, 42, 120))

        # 2. Predictive Trajectory Curves & Analytical Arcs
        draw_trajectory_prediction(
            self.solver, self.cannon, self.current_solution,
            self.reticle_x, self.reticle_y, self.solution_mode,
            self.drag_enabled, self.kd, self.terrain, self.pattern_enabled
        )

        # 3. World Entities (Terrain, Targets, Cannon, Shells, Particles)
        self.terrain.draw()
        self.targets.draw()
        self.cannon.draw()
        self.shell_pool.draw()
        self.particle_pool.draw()

        # 4. Interactive Target Reticle
        draw_target_crosshair(self.reticle_x, self.reticle_y, self.current_solution.in_range, self.pattern_enabled)

        # 5. Top Status HUD Bar (Clearance x=450..980, y=14..48 for settings dropdowns)
        draw_rectangle(0, 0, SCREEN_WIDTH, 52, Color(10, 14, 22, 220))
        draw_line(0, 52, SCREEN_WIDTH, 52, Color(35, 48, 72, 255))

        # Left Title & Badges
        draw_text("BALLISTIC MORTAR ARC", 24, 14, 16, Color(235, 245, 255, 255))
        draw_text("Parabolic Kinematics & Closed-Form Trajectory Solver", 24, 32, 10, Color(125, 155, 185, 255))

        # Pattern Mode Indicator Badge
        badge_pat_col = Color(40, 140, 80, 255) if self.pattern_enabled else Color(160, 45, 45, 255)
        badge_pat_txt = "PATTERN [F1]: AUTO-AIM ON" if self.pattern_enabled else "PATTERN [F1]: MANUAL GUNNERY"
        draw_rectangle(270, 16, 165, 20, badge_pat_col)
        draw_text(badge_pat_txt, 276, 21, 10, Color(255, 255, 255, 255))

        # Solution Mode Badge (High-Arc vs Low-Arc)
        arc_txt = "HIGH ARC (MORTAR) [Q/E]" if self.solution_mode == MODE_HIGH_ARC else "LOW ARC (HOWITZER) [Q/E]"
        arc_col = Color(220, 175, 40, 255) if self.solution_mode == MODE_HIGH_ARC else Color(60, 175, 220, 255)
        draw_rectangle(270, 38, 165, 12, Color(25, 32, 45, 255))
        draw_text(arc_txt, 276, 39, 9, arc_col)

        # Top-Right Gamepad Badge & Mandatory UI Settings Bar Clearance
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)

        # 6. Bottom Controls Reference Strip
        draw_rectangle(0, SCREEN_HEIGHT - 26, SCREEN_WIDTH, 26, Color(10, 14, 22, 240))
        draw_line(0, SCREEN_HEIGHT - 26, SCREEN_WIDTH, SCREEN_HEIGHT - 26, Color(35, 48, 72, 255))
        controls_msg = "Reticle: Mouse/Right Stick | Charge: W/S | Mode: Q/E | Fire: Space/LClick/RT | Drag: D/F2 | Telemetry: [Tab] | Pattern: [F1] | Reset: [R]"
        draw_text(controls_msg, 24, SCREEN_HEIGHT - 18, 11, Color(175, 190, 210, 255))

        # 7. Telemetry & X-Ray Overlay ([Tab])
        if self.show_xray:
            draw_xray_telemetry_panel(
                self.current_solution, self.cannon, self.solver,
                self.reticle_x, self.reticle_y, self.solution_mode,
                self.drag_enabled, self.kd, self.pattern_enabled
            )

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
    BallisticMortarGame().run(smoke_test=is_smoke)
