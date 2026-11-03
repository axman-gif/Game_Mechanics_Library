# -*- coding: utf-8 -*-
"""
Orbital Siege 2D - Multi-Pattern Newtonian Space Defense
========================================================
Section          : 3.0 Core Multi-Pattern Prototypes
Pattern Category : Core Multi-Pattern (Physics, Memory, AI, Spatial)
Dimension        : 2D

Problem Solved:
  In arcade space simulations, naive entity iteration, quadratic O(N^2) collision checks,
  dynamic heap allocations during heavy bullet storms, and simplistic linear AI cause severe
  framerate jitter, garbage collector spikes, and flat, unengaging combat without orbital physics.

How the Pattern Works:
  1. N-Body Gravitational Well: A central celestial body exerts continuous Newtonian gravity
     F = G*(m1*m2)/(r^2 + eps^2) with gravitational softening (epsilon) to avoid singular forces,
     enabling realistic orbital slingshots, inertia conservation, and curved ballistic flak arcs.
  2. Object Pool: Pre-allocated contiguous arrays of kinetic flak rounds, guided micro-missiles,
     and thruster particles maintain active flags and reuse memory slots with zero frame-time allocations.
  3. Spatial Partitioning: SpatialGrid2D divides the orbital theater into 64-pixel spatial buckets,
     reducing broadphase collision queries between ships, asteroids, and munitions from O(N^2) to O(N).
  4. Finite State Machine (FSM): Drone raiders dynamically cycle through STATE_ORBIT, STATE_SLINGSHOT_DIVE,
     STATE_ATTACK_RUN, and STATE_DISENGAGE based on orbital altitude, player proximity, and hull integrity.
  5. Wave Director: Manages systemic threat budgets, spawn pacing intervals, and escalating raider tiers.

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - WASD / Left Stick / D-Pad     : Main thrusters (W/Up), Retro thrusters (S/Down), RCS Torque (A/D/Left/Right)
  - Mouse Move / Right Stick      : Aim kinetic cannon & missile lock reticle
  - Left Click / Space / RT / [X] : Fire Kinetic Flak Cannon (rapid-fire pool)
  - Right Click / LT / RB / [B]   : Launch Guided Micro-Missile (tracking pool)
  - [Tab] / Gamepad Y             : Toggle X-Ray Telemetry Overlay (SpatialGrid, Pools, FSM, Gravity Field)
  - [F1]  / Gamepad LB            : Toggle Planetary Gravity Well (Newtonian Gravity vs Zero-G Flat Space)
  - [Ctrl +/-]                    : Increase / Decrease UI Font Size
  - [F11]                         : Toggle Fullscreen
  - [R]   / Gamepad Start         : Reset Simulation
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
WINDOW_TITLE = "Orbital Siege 2D - Core Multi-Pattern Prototype (Raylib Pattern Lab)"

# Arena & Celestial Parameters
PLANET_CENTER_X = 640.0
PLANET_CENTER_Y = 360.0
PLANET_RADIUS = 52.0
PLANET_ATMOSPHERE_RADIUS = 115.0
GRAVITATIONAL_CONSTANT_GM = 280000.0
GRAVITATIONAL_SOFTENING_SQ = 2250.0  # eps^2 (eps = 47.43 px) avoids singular infinite forces

# Object Pool Capacities
CAPACITY_FLAK = 200
CAPACITY_MISSILES = 48
CAPACITY_PARTICLES = 360
CAPACITY_DRONES = 28
CAPACITY_ASTEROIDS = 6

# Drone FSM State Enumeration (Maps to explicit C++ enum class DroneState : uint8_t)
STATE_ORBIT = 0
STATE_SLINGSHOT_DIVE = 1
STATE_ATTACK_RUN = 2
STATE_DISENGAGE = 3

# Drone Archetype Enumeration (Maps to explicit C++ enum class DroneType : uint8_t)
DRONE_SCOUT = 0
DRONE_INTERCEPTOR = 1
DRONE_HEAVY_BOMBER = 2

# Wave Director State Enumeration
WAVE_STATE_SPAWNING = 0
WAVE_STATE_COMBAT = 1
WAVE_STATE_INTERMISSION = 2


# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATION
# ==============================================================================

class GravityWell:
    """
    Pattern: N-Body Gravitational Well with Softened Point-Mass Potential.
    
    C++ / Architectural Mapping:
      struct CelestialBody {
          float cx, cy;
          float gm;           // Gravitational parameter (G * Mass)
          float softening_sq; // Epsilon squared to prevent infinite singularity
          float radius;       // Solid core collision radius
      };
    
    Why it works:
      Newtonian gravitational force is F = G * (M * m) / r^2.
      In discrete numerical integration (Euler or Verlet), when r -> 0, acceleration
      approaches infinity, causing severe numeric blow-ups and ships rocketing off to NaN.
      Plummer softening adds an epsilon parameter:
        acc = (G * M) / (r^2 + eps^2)
      This guarantees smooth, bounded accelerations even if an entity passes near the planetary core.
    """
    def __init__(self, cx: float, cy: float, gm: float, softening_sq: float, radius: float):
        self.cx = float(cx)
        self.cy = float(cy)
        self.gm = float(gm)
        self.softening_sq = float(softening_sq)
        self.radius = float(radius)
        self.atmosphere_radius = float(PLANET_ATMOSPHERE_RADIUS)

    def compute_acceleration(self, px: float, py: float) -> tuple:
        """Calculates 2D gravitational acceleration vector (ax, ay) acting on an entity at (px, py)."""
        dx = self.cx - float(px)
        dy = self.cy - float(py)
        dist_sq = dx * dx + dy * dy
        eff_dist_sq = dist_sq + self.softening_sq
        eff_dist = math.sqrt(eff_dist_sq)

        # Acceleration magnitude: a = GM / (r^2 + eps^2)
        acc_mag = self.gm / eff_dist_sq
        ax = acc_mag * (dx / eff_dist)
        ay = acc_mag * (dy / eff_dist)
        return ax, ay

    def predict_orbit(self, start_x: float, start_y: float, start_vx: float, start_vy: float,
                      steps: int = 42, step_dt: float = 0.07, gravity_enabled: bool = True) -> list:
        """Predictive Keplerian Trajectory Projection using forward Euler-Cromer integration."""
        points = []
        cx = float(start_x)
        cy = float(start_y)
        cvx = float(start_vx)
        cvy = float(start_vy)

        for step in range(steps):
            if gravity_enabled:
                ax, ay = self.compute_acceleration(cx, cy)
                cvx = cvx + ax * step_dt
                cvy = cvy + ay * step_dt
            cx = cx + cvx * step_dt
            cy = cy + cvy * step_dt
            points.append((cx, cy))

            # Stop prediction if trajectory impacts planetary core
            dx = cx - self.cx
            dy = cy - self.cy
            if (dx * dx + dy * dy) <= (self.radius * self.radius):
                break
        return points


class FlakBullet:
    """Plain struct-like projectile slot for the Object Pool."""
    def __init__(self):
        self.active = False
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.life = 0.0
        self.max_life = 1.0
        self.radius = 3.2
        self.damage = 18.0
        self.is_enemy = False


class FlakPool:
    """
    Pattern: Object Pool for Kinetic Flak Cannon Projectiles.
    Pre-allocates contiguous array at startup ensuring zero per-frame allocation.
    """
    def __init__(self, capacity: int = CAPACITY_FLAK):
        self.capacity = capacity
        self.slots = []
        for i in range(capacity):
            self.slots.append(FlakBullet())
        self.active_count = 0
        self.high_water_mark = 0

    def spawn(self, x: float, y: float, vx: float, vy: float, is_enemy: bool = False,
              life: float = 2.4, damage: float = 18.0) -> bool:
        for slot in self.slots:
            if not slot.active:
                slot.active = True
                slot.x = float(x)
                slot.y = float(y)
                slot.vx = float(vx)
                slot.vy = float(vy)
                slot.life = float(life)
                slot.max_life = float(life)
                slot.is_enemy = is_enemy
                slot.damage = float(damage)
                slot.radius = 3.8 if is_enemy else 3.2
                self.active_count += 1
                if self.active_count > self.high_water_mark:
                    self.high_water_mark = self.active_count
                return True
        return False

    def update(self, dt: float, gravity_well: GravityWell, gravity_enabled: bool):
        count = 0
        for slot in self.slots:
            if not slot.active:
                continue

            if gravity_enabled:
                ax, ay = gravity_well.compute_acceleration(slot.x, slot.y)
                slot.vx += ax * dt
                slot.vy += ay * dt

            slot.x += slot.vx * dt
            slot.y += slot.vy * dt
            slot.life -= dt

            if slot.life <= 0.0:
                slot.active = False
                continue

            pdx = slot.x - gravity_well.cx
            pdy = slot.y - gravity_well.cy
            if (pdx * pdx + pdy * pdy) <= (gravity_well.radius * gravity_well.radius):
                slot.active = False
                continue

            if slot.x < -150.0 or slot.x > SCREEN_WIDTH + 150.0 or slot.y < -150.0 or slot.y > SCREEN_HEIGHT + 150.0:
                slot.active = False
                continue
            count += 1
        self.active_count = count

    def draw(self):
        for slot in self.slots:
            if not slot.active:
                continue
            v_len = math.sqrt(slot.vx * slot.vx + slot.vy * slot.vy)
            tail_scale = 0.04
            tx = slot.x - slot.vx * tail_scale if v_len > 1.0 else slot.x
            ty = slot.y - slot.vy * tail_scale if v_len > 1.0 else slot.y
            core_col = Color(255, 120, 60, 255) if slot.is_enemy else Color(110, 230, 255, 255)
            trail_col = Color(220, 50, 30, 180) if slot.is_enemy else Color(40, 140, 240, 180)
            draw_line_ex(Vector2(float(tx), float(ty)), Vector2(float(slot.x), float(slot.y)), 2.5, trail_col)
            draw_circle(int(slot.x), int(slot.y), slot.radius, core_col)


class GuidedMissile:
    """Plain struct-like missile slot for guided micro-missiles."""
    def __init__(self):
        self.active = False
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.angle = 0.0
        self.speed = 280.0
        self.turn_rate = 4.2
        self.life = 0.0
        self.max_life = 3.5
        self.radius = 4.5
        self.damage = 65.0
        self.target_drone = None


class MissilePool:
    """Pattern: Object Pool for Guided Micro-Missiles."""
    def __init__(self, capacity: int = CAPACITY_MISSILES):
        self.capacity = capacity
        self.slots = []
        for i in range(capacity):
            self.slots.append(GuidedMissile())
        self.active_count = 0
        self.high_water_mark = 0

    def spawn(self, x: float, y: float, angle: float, initial_speed: float, target_drone=None) -> bool:
        for slot in self.slots:
            if not slot.active:
                slot.active = True
                slot.x = float(x)
                slot.y = float(y)
                slot.angle = float(angle)
                slot.speed = float(initial_speed)
                slot.vx = math.cos(angle) * initial_speed
                slot.vy = math.sin(angle) * initial_speed
                slot.life = 3.6
                slot.max_life = 3.6
                slot.target_drone = target_drone
                self.active_count += 1
                if self.active_count > self.high_water_mark:
                    self.high_water_mark = self.active_count
                return True
        return False

    def update(self, dt: float, gravity_well: GravityWell, gravity_enabled: bool, particle_pool):
        count = 0
        for slot in self.slots:
            if not slot.active:
                continue

            if slot.target_drone is not None and slot.target_drone.active:
                tdx = slot.target_drone.x - slot.x
                tdy = slot.target_drone.y - slot.y
                desired_angle = math.atan2(tdy, tdx)
                diff = (desired_angle - slot.angle + math.pi) % (2.0 * math.pi) - math.pi
                max_turn = slot.turn_rate * dt
                if diff > max_turn:
                    slot.angle += max_turn
                elif diff < -max_turn:
                    slot.angle -= max_turn
                else:
                    slot.angle = desired_angle

            slot.speed = min(slot.speed + 160.0 * dt, 360.0)
            thrust_vx = math.cos(slot.angle) * slot.speed
            thrust_vy = math.sin(slot.angle) * slot.speed
            slot.vx = approach(slot.vx, thrust_vx, 420.0 * dt)
            slot.vy = approach(slot.vy, thrust_vy, 420.0 * dt)

            if gravity_enabled:
                ax, ay = gravity_well.compute_acceleration(slot.x, slot.y)
                slot.vx += ax * dt
                slot.vy += ay * dt

            slot.x += slot.vx * dt
            slot.y += slot.vy * dt
            slot.life -= dt

            tail_x = slot.x - math.cos(slot.angle) * 7.0
            tail_y = slot.y - math.sin(slot.angle) * 7.0
            particle_pool.spawn(tail_x, tail_y, -slot.vx * 0.15, -slot.vy * 0.15, 0.35, 2.5, 255, 180, 50, 180)

            if slot.life <= 0.0:
                slot.active = False
                continue

            pdx = slot.x - gravity_well.cx
            pdy = slot.y - gravity_well.cy
            if (pdx * pdx + pdy * pdy) <= (gravity_well.radius * gravity_well.radius):
                slot.active = False
                continue

            if slot.x < -150.0 or slot.x > SCREEN_WIDTH + 150.0 or slot.y < -150.0 or slot.y > SCREEN_HEIGHT + 150.0:
                slot.active = False
                continue
            count += 1
        self.active_count = count

    def draw(self):
        for slot in self.slots:
            if not slot.active:
                continue
            fx = slot.x + math.cos(slot.angle) * 7.0
            fy = slot.y + math.sin(slot.angle) * 7.0
            bx = slot.x - math.cos(slot.angle) * 5.0
            by = slot.y - math.sin(slot.angle) * 5.0
            nx = -math.sin(slot.angle) * 3.0
            ny = math.cos(slot.angle) * 3.0
            v1 = Vector2(float(fx), float(fy))
            v2 = Vector2(float(bx + nx), float(by + ny))
            v3 = Vector2(float(bx - nx), float(by - ny))
            draw_triangle(v1, v3, v2, Color(245, 245, 255, 255))
            draw_circle(int(slot.x), int(slot.y), slot.radius, Color(255, 200, 60, 140))


class Particle:
    """Plain particle struct for thruster exhaust, explosions, and sparks."""
    def __init__(self):
        self.active = False
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.life = 0.0
        self.max_life = 1.0
        self.size = 2.0
        self.r = 255
        self.g = 255
        self.b = 255
        self.a = 255


class ParticlePool:
    """Pattern: Object Pool for High-Volume Visual FX Particles."""
    def __init__(self, capacity: int = CAPACITY_PARTICLES):
        self.capacity = capacity
        self.slots = []
        for i in range(capacity):
            self.slots.append(Particle())
        self.active_count = 0
        self.high_water_mark = 0

    def spawn(self, x: float, y: float, vx: float, vy: float, life: float, size: float,
              r: int, g: int, b: int, a: int) -> bool:
        for slot in self.slots:
            if not slot.active:
                slot.active = True
                slot.x = float(x)
                slot.y = float(y)
                slot.vx = float(vx)
                slot.vy = float(vy)
                slot.life = float(life)
                slot.max_life = float(life)
                slot.size = float(size)
                slot.r = int(clamp(r, 0, 255))
                slot.g = int(clamp(g, 0, 255))
                slot.b = int(clamp(b, 0, 255))
                slot.a = int(clamp(a, 0, 255))
                self.active_count += 1
                if self.active_count > self.high_water_mark:
                    self.high_water_mark = self.active_count
                return True
        return False

    def spawn_burst(self, x: float, y: float, count: int, speed_min: float, speed_max: float,
                    r: int, g: int, b: int):
        for i in range(count):
            angle = random.uniform(0.0, 6.28318)
            speed = random.uniform(speed_min, speed_max)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            life = random.uniform(0.25, 0.7)
            size = random.uniform(2.0, 4.5)
            self.spawn(x, y, vx, vy, life, size, r, g, b, 240)

    def update(self, dt: float, gravity_well: GravityWell, gravity_enabled: bool):
        count = 0
        for slot in self.slots:
            if not slot.active:
                continue

            if gravity_enabled:
                ax, ay = gravity_well.compute_acceleration(slot.x, slot.y)
                slot.vx += ax * dt * 0.4
                slot.vy += ay * dt * 0.4

            slot.x += slot.vx * dt
            slot.y += slot.vy * dt
            slot.vx *= 0.96
            slot.vy *= 0.96
            slot.life -= dt

            if slot.life <= 0.0:
                slot.active = False
                continue
            count += 1
        self.active_count = count

    def draw(self):
        for slot in self.slots:
            if not slot.active:
                continue
            fade = max(0.0, min(1.0, slot.life / slot.max_life))
            alpha = int(slot.a * fade)
            col = Color(slot.r, slot.g, slot.b, alpha)
            cur_size = max(1.0, slot.size * fade)
            draw_circle(int(slot.x), int(slot.y), cur_size, col)


class WaveDirector:
    """Pattern: Wave Director (Pacing, Systemic Threat Economy, Escalating Compositions)."""
    def __init__(self):
        self.wave_index = 1
        self.state = WAVE_STATE_SPAWNING
        self.threat_budget = 60.0
        self.max_threat_budget = 60.0
        self.spawn_timer = 1.0
        self.spawn_interval = 2.2
        self.intermission_timer = 0.0
        self.total_kills = 0

    def start_next_wave(self):
        self.wave_index += 1
        self.state = WAVE_STATE_SPAWNING
        self.max_threat_budget = 60.0 + (self.wave_index - 1) * 35.0
        self.threat_budget = self.max_threat_budget
        self.spawn_interval = max(0.8, 2.2 - (self.wave_index - 1) * 0.2)
        self.spawn_timer = 0.8
        self.intermission_timer = 0.0

    def get_next_drone_type(self) -> int:
        if self.wave_index >= 3 and self.threat_budget >= 65.0 and random.random() < 0.35:
            self.threat_budget -= 65.0
            return DRONE_HEAVY_BOMBER
        elif self.wave_index >= 2 and self.threat_budget >= 28.0 and random.random() < 0.55:
            self.threat_budget -= 28.0
            return DRONE_INTERCEPTOR
        else:
            self.threat_budget = max(0.0, self.threat_budget - 12.0)
            return DRONE_SCOUT


# ==============================================================================
# BLOCK 2: WORLD SIMULATION & ENTITIES
# ==============================================================================

class OrbitalAsteroid:
    """Kinematic Keplerian Obstacle in stable orbit around the celestial core."""
    def __init__(self, orbit_radius: float, speed: float, radius: float, angle: float = 0.0):
        self.active = True
        self.orbit_radius = float(orbit_radius)
        self.speed = float(speed)
        self.radius = float(radius)
        self.angle = float(angle)
        self.x = PLANET_CENTER_X + math.cos(self.angle) * self.orbit_radius
        self.y = PLANET_CENTER_Y + math.sin(self.angle) * self.orbit_radius
        self.vx = -math.sin(self.angle) * self.speed
        self.vy = math.cos(self.angle) * self.speed
        self.hp = 120.0
        self.max_hp = 120.0
        self.spin = 0.0
        self.spin_rate = random.uniform(-0.8, 0.8)

    def update(self, dt: float, gravity_well: GravityWell, gravity_enabled: bool):
        if not self.active:
            return

        if gravity_enabled:
            ax, ay = gravity_well.compute_acceleration(self.x, self.y)
            self.vx += ax * dt
            self.vy += ay * dt
            self.x += self.vx * dt
            self.y += self.vy * dt
            dx = self.x - gravity_well.cx
            dy = self.y - gravity_well.cy
            self.orbit_radius = math.sqrt(dx * dx + dy * dy)
            self.angle = math.atan2(dy, dx)
        else:
            self.angle += (self.speed / max(10.0, self.orbit_radius)) * dt
            self.x = gravity_well.cx + math.cos(self.angle) * self.orbit_radius
            self.y = gravity_well.cy + math.sin(self.angle) * self.orbit_radius
            self.vx = -math.sin(self.angle) * self.speed
            self.vy = math.cos(self.angle) * self.speed

        self.spin += self.spin_rate * dt

    def draw(self):
        if not self.active:
            return
        segments = 8
        pts = []
        for i in range(segments):
            theta = self.spin + (i * 2.0 * math.pi / segments)
            var = 1.0 + 0.18 * math.sin(i * 3.5 + self.orbit_radius)
            rx = self.x + math.cos(theta) * (self.radius * var)
            ry = self.y + math.sin(theta) * (self.radius * var)
            pts.append(Vector2(float(rx), float(ry)))

        for i in range(segments):
            p1 = pts[i]
            p2 = pts[(i + 1) % segments]
            draw_triangle(Vector2(float(self.x), float(self.y)), p2, p1, Color(75, 82, 102, 255))
            draw_line_ex(p1, p2, 1.8, Color(120, 132, 158, 255))
        draw_circle(int(self.x), int(self.y), self.radius * 0.4, Color(55, 60, 78, 255))


class PlayerShip:
    """Player-Controlled Orbital Defense Fighter with Newtonian momentum and RCS torque."""
    def __init__(self, x: float, y: float):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.angle = -math.pi / 2.0
        self.angular_vel = 0.0
        self.radius = 16.0
        self.thrust_power = 270.0
        self.turn_speed = 4.8
        self.rcs_damping = 0.91
        self.linear_inertia = 0.9985

        self.hp = 100.0
        self.max_hp = 100.0
        self.shield = 100.0
        self.max_shield = 100.0
        self.shield_regen_rate = 14.0
        self.shield_regen_cooldown = 0.0
        self.primary_cooldown = 0.0
        self.secondary_cooldown = 0.0
        self.missiles_ammo = 10
        self.score = 0

    def reset(self, x: float, y: float):
        self.x = float(x)
        self.y = float(y)
        dist = math.sqrt((x - PLANET_CENTER_X)**2 + (y - PLANET_CENTER_Y)**2)
        if dist > 10.0:
            v_orb = math.sqrt(GRAVITATIONAL_CONSTANT_GM / dist)
            self.vx = 0.0
            self.vy = -v_orb * 0.95
        else:
            self.vx = 0.0
            self.vy = 0.0
        self.angle = -math.pi / 2.0
        self.angular_vel = 0.0
        self.hp = 100.0
        self.shield = 100.0
        self.shield_regen_cooldown = 0.0
        self.primary_cooldown = 0.0
        self.secondary_cooldown = 0.0
        self.missiles_ammo = 10
        self.score = 0

    def apply_inputs(self, move_x: float, move_y: float, dt: float, particle_pool: ParticlePool):
        if abs(move_x) > 0.15:
            self.angular_vel += move_x * self.turn_speed * dt
        self.angle += self.angular_vel * dt
        self.angular_vel *= self.rcs_damping

        if move_y < -0.2:
            thrust_acc = abs(move_y) * self.thrust_power
            self.vx += math.cos(self.angle) * thrust_acc * dt
            self.vy += math.sin(self.angle) * thrust_acc * dt
            for offset in [-6.0, 6.0]:
                nx = -math.sin(self.angle) * offset
                ny = math.cos(self.angle) * offset
                ex = self.x - math.cos(self.angle) * 14.0 + nx
                ey = self.y - math.sin(self.angle) * 14.0 + ny
                evx = -math.cos(self.angle) * random.uniform(80.0, 160.0) + random.uniform(-15.0, 15.0)
                evy = -math.sin(self.angle) * random.uniform(80.0, 160.0) + random.uniform(-15.0, 15.0)
                particle_pool.spawn(ex, ey, evx, evy, 0.28, 3.2, 80, 200, 255, 230)
        elif move_y > 0.2:
            retro_acc = move_y * (self.thrust_power * 0.6)
            self.vx -= math.cos(self.angle) * retro_acc * dt
            self.vy -= math.sin(self.angle) * retro_acc * dt
            fx = self.x + math.cos(self.angle) * 10.0
            fy = self.y + math.sin(self.angle) * 10.0
            fvx = math.cos(self.angle) * random.uniform(50.0, 110.0)
            fvy = math.sin(self.angle) * random.uniform(50.0, 110.0)
            particle_pool.spawn(fx, fy, fvx, fvy, 0.18, 2.4, 255, 180, 70, 200)

    def update_physics(self, dt: float, gravity_well: GravityWell, gravity_enabled: bool, particle_pool):
        if gravity_enabled:
            ax, ay = gravity_well.compute_acceleration(self.x, self.y)
            self.vx += ax * dt
            self.vy += ay * dt

        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= self.linear_inertia
        self.vy *= self.linear_inertia

        # Screen boundary elastic containment ring
        margin = 30.0
        if self.x < margin:
            self.x = margin
            self.vx = abs(self.vx) * 0.6
        elif self.x > SCREEN_WIDTH - margin:
            self.x = SCREEN_WIDTH - margin
            self.vx = -abs(self.vx) * 0.6
        if self.y < margin:
            self.y = margin
            self.vy = abs(self.vy) * 0.6
        elif self.y > SCREEN_HEIGHT - margin:
            self.y = SCREEN_HEIGHT - margin
            self.vy = -abs(self.vy) * 0.6

        pdx = self.x - gravity_well.cx
        pdy = self.y - gravity_well.cy
        pdist = math.sqrt(pdx * pdx + pdy * pdy)

        # Atmosphere friction zone
        if pdist < gravity_well.atmosphere_radius and pdist > gravity_well.radius:
            density = (gravity_well.atmosphere_radius - pdist) / (gravity_well.atmosphere_radius - gravity_well.radius)
            drag_factor = 1.0 - (0.85 * density * dt)
            self.vx *= drag_factor
            self.vy *= drag_factor
            if random.random() < 0.35:
                particle_pool.spawn(self.x, self.y, random.uniform(-20.0, 20.0), random.uniform(-20.0, 20.0),
                                    0.25, 2.5, 255, 140, 40, 180)

        # Planet Core Hard Surface Impact
        min_dist = gravity_well.radius + self.radius
        if pdist < min_dist:
            norm_x = pdx / max(0.001, pdist)
            norm_y = pdy / max(0.001, pdist)
            self.x = gravity_well.cx + norm_x * min_dist
            self.y = gravity_well.cy + norm_y * min_dist
            dot = self.vx * norm_x + self.vy * norm_y
            if dot < 0:
                self.vx = (self.vx - 1.5 * dot * norm_x) * 0.65
                self.vy = (self.vy - 1.5 * dot * norm_y) * 0.65
            self.take_damage(16.0 * dt * 60.0, particle_pool)

        # Shield recharge
        if self.shield_regen_cooldown > 0.0:
            self.shield_regen_cooldown -= dt
        else:
            self.shield = min(self.max_shield, self.shield + self.shield_regen_rate * dt)

        if self.primary_cooldown > 0.0:
            self.primary_cooldown -= dt
        if self.secondary_cooldown > 0.0:
            self.secondary_cooldown -= dt

    def fire_primary(self, flak_pool: FlakPool, sfx: SoundLibrary, aim_angle: float) -> bool:
        if self.primary_cooldown <= 0.0:
            self.primary_cooldown = 0.11
            mx = self.x + math.cos(aim_angle) * 18.0
            my = self.y + math.sin(aim_angle) * 18.0
            spread = random.uniform(-0.04, 0.04)
            muzzle_speed = 640.0
            b_vx = self.vx + math.cos(aim_angle + spread) * muzzle_speed
            b_vy = self.vy + math.sin(aim_angle + spread) * muzzle_speed
            if flak_pool.spawn(mx, my, b_vx, b_vy, is_enemy=False, life=2.2, damage=18.0):
                sfx.play("laser", 0.45)
                return True
        return False

    def fire_secondary(self, missile_pool: MissilePool, target_drone, sfx: SoundLibrary, aim_angle: float) -> bool:
        if self.secondary_cooldown <= 0.0 and self.missiles_ammo > 0:
            self.secondary_cooldown = 0.65
            self.missiles_ammo -= 1
            mx = self.x + math.cos(aim_angle) * 16.0
            my = self.y + math.sin(aim_angle) * 16.0
            if missile_pool.spawn(mx, my, aim_angle, 140.0, target_drone):
                sfx.play("heavy_laser", 0.7)
                return True
        return False

    def take_damage(self, amount: float, particle_pool: ParticlePool):
        self.shield_regen_cooldown = 2.8
        if self.shield > 0.0:
            if self.shield >= amount:
                self.shield -= amount
                amount = 0.0
            else:
                amount -= self.shield
                self.shield = 0.0

        if amount > 0.0:
            self.hp = max(0.0, self.hp - amount)
            particle_pool.spawn_burst(self.x, self.y, 4, 30.0, 90.0, 255, 60, 50)

    def draw(self, aim_angle: float):
        if self.shield > 5.0:
            s_alpha = int(35 + (self.shield / self.max_shield) * 45)
            draw_circle(int(self.x), int(self.y), self.radius + 6.0, Color(60, 180, 255, s_alpha))
            draw_circle_lines(int(self.x), int(self.y), self.radius + 6.0, Color(100, 220, 255, s_alpha + 30))

        nose_x = self.x + math.cos(self.angle) * 18.0
        nose_y = self.y + math.sin(self.angle) * 18.0
        left_x = self.x + math.cos(self.angle + 2.45) * 16.0
        left_y = self.y + math.sin(self.angle + 2.45) * 16.0
        right_x = self.x + math.cos(self.angle - 2.45) * 16.0
        right_y = self.y + math.sin(self.angle - 2.45) * 16.0
        notch_x = self.x - math.cos(self.angle) * 8.0
        notch_y = self.y - math.sin(self.angle) * 8.0

        p_nose = Vector2(float(nose_x), float(nose_y))
        p_left = Vector2(float(left_x), float(left_y))
        p_right = Vector2(float(right_x), float(right_y))
        p_notch = Vector2(float(notch_x), float(notch_y))

        draw_triangle(p_nose, p_notch, p_left, Color(35, 95, 160, 255))
        draw_triangle(p_nose, p_right, p_notch, Color(45, 125, 205, 255))
        draw_line_ex(p_nose, p_left, 2.0, Color(120, 210, 255, 255))
        draw_line_ex(p_nose, p_right, 2.0, Color(120, 210, 255, 255))
        draw_line_ex(p_left, p_notch, 1.8, Color(70, 160, 240, 255))
        draw_line_ex(p_right, p_notch, 1.8, Color(70, 160, 240, 255))

        cx = self.x + math.cos(self.angle) * 4.0
        cy = self.y + math.sin(self.angle) * 4.0
        draw_circle(int(cx), int(cy), 4.2, Color(220, 245, 255, 255))

        aim_x = self.x + math.cos(aim_angle) * 36.0
        aim_y = self.y + math.sin(aim_angle) * 36.0
        draw_line_ex(Vector2(float(self.x), float(self.y)), Vector2(float(aim_x), float(aim_y)), 1.4, Color(70, 210, 255, 130))


class DroneRaider:
    """Pattern: Finite State Machine (FSM) Autonomous Raider AI."""
    def __init__(self):
        self.active = False
        self.type = DRONE_SCOUT
        self.state = STATE_ORBIT
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.angle = 0.0
        self.hp = 30.0
        self.max_hp = 30.0
        self.radius = 14.0
        self.state_timer = 0.0
        self.fire_cooldown = 1.0
        self.orbit_radius = 320.0
        self.orbit_direction = 1.0
        self.speed = 180.0

    def spawn(self, drone_type: int, orbit_rad: float, angle_rad: float, direction: float = 1.0):
        self.active = True
        self.type = drone_type
        self.state = STATE_ORBIT
        self.state_timer = random.uniform(3.0, 6.0)
        self.orbit_radius = float(orbit_rad)
        self.orbit_direction = 1.0 if direction >= 0 else -1.0
        self.x = PLANET_CENTER_X + math.cos(angle_rad) * self.orbit_radius
        self.y = PLANET_CENTER_Y + math.sin(angle_rad) * self.orbit_radius

        v_orb = math.sqrt(GRAVITATIONAL_CONSTANT_GM / max(20.0, self.orbit_radius))
        self.vx = -math.sin(angle_rad) * v_orb * self.orbit_direction
        self.vy = math.cos(angle_rad) * v_orb * self.orbit_direction
        self.angle = math.atan2(self.vy, self.vx)

        if self.type == DRONE_SCOUT:
            self.max_hp = 25.0
            self.hp = 25.0
            self.radius = 12.0
            self.speed = 220.0
            self.fire_cooldown = 0.8
        elif self.type == DRONE_INTERCEPTOR:
            self.max_hp = 55.0
            self.hp = 55.0
            self.radius = 15.0
            self.speed = 175.0
            self.fire_cooldown = 1.2
        else:
            self.max_hp = 135.0
            self.hp = 135.0
            self.radius = 21.0
            self.speed = 115.0
            self.fire_cooldown = 1.8

    def enter_state(self, new_state: int):
        self.state = new_state
        if new_state == STATE_ORBIT:
            self.state_timer = random.uniform(3.5, 6.5)
        elif new_state == STATE_SLINGSHOT_DIVE:
            self.state_timer = random.uniform(2.5, 4.0)
        elif new_state == STATE_ATTACK_RUN:
            self.state_timer = random.uniform(3.0, 4.5)
        elif new_state == STATE_DISENGAGE:
            self.state_timer = random.uniform(3.0, 5.0)

    def update(self, dt: float, player: PlayerShip, gravity_well: GravityWell, gravity_enabled: bool,
               flak_pool: FlakPool, particle_pool: ParticlePool, sfx: SoundLibrary):
        if not self.active:
            return

        self.state_timer -= dt
        if self.fire_cooldown > 0.0:
            self.fire_cooldown -= dt

        pdx = self.x - gravity_well.cx
        pdy = self.y - gravity_well.cy
        pdist = math.sqrt(pdx * pdx + pdy * pdy)

        tdx = player.x - self.x
        tdy = player.y - self.y
        player_dist = math.sqrt(tdx * tdx + tdy * tdy)

        # FSM Transition Logic
        if self.state == STATE_ORBIT:
            theta = math.atan2(pdy, pdx)
            tangent_angle = theta + (math.pi / 2.0) * self.orbit_direction
            v_target_x = math.cos(tangent_angle) * self.speed
            v_target_y = math.sin(tangent_angle) * self.speed
            self.vx = approach(self.vx, v_target_x, 180.0 * dt)
            self.vy = approach(self.vy, v_target_y, 180.0 * dt)

            if self.state_timer <= 0.0:
                if player_dist < 460.0:
                    self.enter_state(STATE_SLINGSHOT_DIVE)
                else:
                    self.enter_state(STATE_ATTACK_RUN)

        elif self.state == STATE_SLINGSHOT_DIVE:
            dive_angle = math.atan2(-pdy, -pdx) + (0.35 * self.orbit_direction)
            self.vx += math.cos(dive_angle) * (self.speed * 1.4) * dt
            self.vy += math.sin(dive_angle) * (self.speed * 1.4) * dt
            if pdist < (gravity_well.radius + 65.0) or self.state_timer <= 0.0:
                self.enter_state(STATE_ATTACK_RUN)

        elif self.state == STATE_ATTACK_RUN:
            intercept_angle = math.atan2(tdy, tdx)
            self.vx = approach(self.vx, math.cos(intercept_angle) * (self.speed * 1.2), 240.0 * dt)
            self.vy = approach(self.vy, math.sin(intercept_angle) * (self.speed * 1.2), 240.0 * dt)

            facing_diff = abs((intercept_angle - self.angle + math.pi) % (2.0 * math.pi) - math.pi)
            if facing_diff < 0.45 and self.fire_cooldown <= 0.0 and player_dist < 480.0:
                if self.type == DRONE_SCOUT:
                    self.fire_cooldown = 0.75
                    flak_pool.spawn(self.x, self.y, math.cos(self.angle) * 440.0, math.sin(self.angle) * 440.0,
                                    is_enemy=True, life=1.8, damage=14.0)
                    sfx.play("laser", 0.3)
                elif self.type == DRONE_INTERCEPTOR:
                    self.fire_cooldown = 1.1
                    for offset in [-6.0, 6.0]:
                        bx = self.x - math.sin(self.angle) * offset
                        by = self.y + math.cos(self.angle) * offset
                        flak_pool.spawn(bx, by, math.cos(self.angle) * 460.0, math.sin(self.angle) * 460.0,
                                        is_enemy=True, life=1.9, damage=16.0)
                    sfx.play("laser", 0.4)
                else:
                    self.fire_cooldown = 1.9
                    for spread_ang in [-0.28, 0.0, 0.28]:
                        sa = self.angle + spread_ang
                        flak_pool.spawn(self.x, self.y, math.cos(sa) * 380.0, math.sin(sa) * 380.0,
                                        is_enemy=True, life=2.4, damage=24.0)
                    sfx.play("heavy_laser", 0.55)

            if self.hp < (self.max_hp * 0.35) or self.state_timer <= 0.0:
                self.enter_state(STATE_DISENGAGE)

        elif self.state == STATE_DISENGAGE:
            flee_angle = math.atan2(pdy, pdx) + (0.5 * self.orbit_direction)
            self.vx = approach(self.vx, math.cos(flee_angle) * (self.speed * 1.3), 220.0 * dt)
            self.vy = approach(self.vy, math.sin(flee_angle) * (self.speed * 1.3), 220.0 * dt)
            if pdist > 380.0 or self.state_timer <= 0.0:
                self.enter_state(STATE_ORBIT)

        if gravity_enabled:
            ax, ay = gravity_well.compute_acceleration(self.x, self.y)
            self.vx += ax * dt
            self.vy += ay * dt

        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= 0.994
        self.vy *= 0.994

        v_speed = math.sqrt(self.vx * self.vx + self.vy * self.vy)
        if v_speed > 10.0:
            target_heading = math.atan2(self.vy, self.vx)
            self.angle = approach(self.angle, target_heading, 5.0 * dt)

        if pdist < (gravity_well.radius + self.radius):
            self.active = False
            particle_pool.spawn_burst(self.x, self.y, 14, 40.0, 120.0, 255, 120, 40)
            sfx.play("explosion", 0.6)

    def take_damage(self, amount: float, particle_pool: ParticlePool, sfx: SoundLibrary) -> bool:
        self.hp -= amount
        particle_pool.spawn_burst(self.x, self.y, 3, 20.0, 70.0, 255, 180, 60)
        sfx.play("hit", 0.4)
        if self.hp <= 0.0:
            self.active = False
            particle_pool.spawn_burst(self.x, self.y, 16, 40.0, 150.0, 255, 100, 30)
            sfx.play("explosion", 0.75)
            return True
        return False

    def draw(self):
        if not self.active:
            return

        if self.type == DRONE_SCOUT:
            fx = self.x + math.cos(self.angle) * 14.0
            fy = self.y + math.sin(self.angle) * 14.0
            lx = self.x + math.cos(self.angle + 2.5) * 11.0
            ly = self.y + math.sin(self.angle + 2.5) * 11.0
            rx = self.x + math.cos(self.angle - 2.5) * 11.0
            ry = self.y + math.sin(self.angle - 2.5) * 11.0
            draw_triangle(Vector2(float(fx), float(fy)), Vector2(float(lx), float(ly)),
                          Vector2(float(rx), float(ry)), Color(60, 220, 210, 255))
            draw_circle(int(self.x), int(self.y), 3.0, Color(255, 255, 255, 255))

        elif self.type == DRONE_INTERCEPTOR:
            fx1 = self.x + math.cos(self.angle) * 16.0 + (-math.sin(self.angle) * 6.0)
            fy1 = self.y + math.sin(self.angle) * 16.0 + (math.cos(self.angle) * 6.0)
            fx2 = self.x + math.cos(self.angle) * 16.0 + (math.sin(self.angle) * 6.0)
            fy2 = self.y + math.sin(self.angle) * 16.0 + (-math.cos(self.angle) * 6.0)
            bx = self.x - math.cos(self.angle) * 10.0
            by = self.y - math.sin(self.angle) * 10.0
            p_b = Vector2(float(bx), float(by))
            draw_triangle(Vector2(float(fx1), float(fy1)), p_b, Vector2(float(self.x), float(self.y)), Color(245, 150, 40, 255))
            draw_triangle(Vector2(float(fx2), float(fy2)), Vector2(float(self.x), float(self.y)), p_b, Color(180, 80, 20, 255))
            draw_circle(int(self.x), int(self.y), 4.5, Color(255, 60, 40, 255))

        else:
            draw_circle(int(self.x), int(self.y), self.radius, Color(140, 25, 45, 255))
            draw_circle(int(self.x), int(self.y), self.radius - 3.5, Color(230, 45, 75, 255))
            for i in range(4):
                ang = self.angle + (i * math.pi / 2.0)
                px = self.x + math.cos(ang) * (self.radius + 2.0)
                py = self.y + math.sin(ang) * (self.radius + 2.0)
                draw_circle(int(px), int(py), 3.5, Color(255, 190, 70, 255))

        bar_w = 24
        bar_h = 3
        bx = int(self.x - bar_w // 2)
        by = int(self.y - self.radius - 8)
        hp_ratio = max(0.0, min(1.0, self.hp / self.max_hp))
        draw_rectangle(bx, by, bar_w, bar_h, Color(30, 30, 40, 200))
        draw_rectangle(bx, by, int(bar_w * hp_ratio), bar_h, Color(60, 230, 90, 230))


class WorldSimulation:
    """Coordinates physics, Object Pools, SpatialGrid2D broadphase, and collisions."""
    def __init__(self, sfx: SoundLibrary):
        self.sfx = sfx
        self.gravity_well = GravityWell(PLANET_CENTER_X, PLANET_CENTER_Y,
                                        GRAVITATIONAL_CONSTANT_GM,
                                        GRAVITATIONAL_SOFTENING_SQ,
                                        PLANET_RADIUS)
        self.gravity_enabled = True

        self.flak_pool = FlakPool(CAPACITY_FLAK)
        self.missile_pool = MissilePool(CAPACITY_MISSILES)
        self.particle_pool = ParticlePool(CAPACITY_PARTICLES)
        self.spatial_grid = SpatialGrid2D(cell_size=64.0)
        self.wave_director = WaveDirector()

        self.drones = []
        for i in range(CAPACITY_DRONES):
            self.drones.append(DroneRaider())

        self.asteroids = []
        ast_radii = [185.0, 250.0, 315.0, 385.0, 455.0, 520.0]
        ast_sizes = [18.0, 24.0, 16.0, 28.0, 20.0, 22.0]
        ast_speeds = [75.0, 62.0, 54.0, 48.0, 42.0, 38.0]
        for i in range(CAPACITY_ASTEROIDS):
            ang = (i * 2.0 * math.pi) / CAPACITY_ASTEROIDS
            self.asteroids.append(OrbitalAsteroid(ast_radii[i], ast_speeds[i], ast_sizes[i], ang))

        self.player = PlayerShip(PLANET_CENTER_X, PLANET_CENTER_Y - 260.0)
        self.player.reset(PLANET_CENTER_X, PLANET_CENTER_Y - 260.0)

        self.stars = []
        for i in range(120):
            sx = random.uniform(0.0, SCREEN_WIDTH)
            sy = random.uniform(0.0, SCREEN_HEIGHT)
            sb = random.uniform(0.3, 1.0)
            self.stars.append((sx, sy, sb))

        self.game_over = False

    def reset(self):
        self.player.reset(PLANET_CENTER_X, PLANET_CENTER_Y - 260.0)
        self.wave_director = WaveDirector()
        for d in self.drones:
            d.active = False
        for s in self.flak_pool.slots:
            s.active = False
        for m in self.missile_pool.slots:
            m.active = False
        for p in self.particle_pool.slots:
            p.active = False
        self.flak_pool.active_count = 0
        self.missile_pool.active_count = 0
        self.particle_pool.active_count = 0
        self.game_over = False

    def update(self, dt: float, move_x: float, move_y: float, aim_angle: float,
               is_firing_primary: bool, is_firing_secondary: bool):
        if self.game_over:
            return

        self.player.apply_inputs(move_x, move_y, dt, self.particle_pool)
        self.player.update_physics(dt, self.gravity_well, self.gravity_enabled, self.particle_pool)

        if is_firing_primary:
            self.player.fire_primary(self.flak_pool, self.sfx, aim_angle)

        if is_firing_secondary:
            best_target = None
            best_dist = 999999.0
            for d in self.drones:
                if d.active:
                    dist = math.sqrt((d.x - self.player.x)**2 + (d.y - self.player.y)**2)
                    if dist < best_dist:
                        best_dist = dist
                        best_target = d
            self.player.fire_secondary(self.missile_pool, best_target, self.sfx, aim_angle)

        for ast in self.asteroids:
            ast.update(dt, self.gravity_well, self.gravity_enabled)

        self._update_wave_director(dt)

        for drone in self.drones:
            if drone.active:
                drone.update(dt, self.player, self.gravity_well, self.gravity_enabled,
                             self.flak_pool, self.particle_pool, self.sfx)

        self.flak_pool.update(dt, self.gravity_well, self.gravity_enabled)
        self.missile_pool.update(dt, self.gravity_well, self.gravity_enabled, self.particle_pool)
        self.particle_pool.update(dt, self.gravity_well, self.gravity_enabled)

        # Spatial Partitioning Broadphase Population
        self.spatial_grid.clear()
        self.spatial_grid.insert(self.player, self.player.x, self.player.y, self.player.radius)
        for drone in self.drones:
            if drone.active:
                self.spatial_grid.insert(drone, drone.x, drone.y, drone.radius)
        for ast in self.asteroids:
            if ast.active:
                self.spatial_grid.insert(ast, ast.x, ast.y, ast.radius)

        self._resolve_collisions()

        if self.player.hp <= 0.0:
            self.game_over = True
            self.particle_pool.spawn_burst(self.player.x, self.player.y, 35, 40.0, 220.0, 255, 80, 40)
            self.sfx.play("explosion", 0.95)

    def _update_wave_director(self, dt: float):
        wd = self.wave_director
        if wd.state == WAVE_STATE_SPAWNING:
            wd.spawn_timer -= dt
            if wd.spawn_timer <= 0.0 and wd.threat_budget > 0.0:
                wd.spawn_timer = wd.spawn_interval
                for drone in self.drones:
                    if not drone.active:
                        drone_type = wd.get_next_drone_type()
                        orbit_r = random.uniform(280.0, 460.0)
                        ang = random.uniform(0.0, 6.28318)
                        direction = 1.0 if random.random() < 0.5 else -1.0
                        drone.spawn(drone_type, orbit_r, ang, direction)
                        break

            if wd.threat_budget <= 0.0:
                wd.state = WAVE_STATE_COMBAT

        elif wd.state == WAVE_STATE_COMBAT:
            any_active = False
            for drone in self.drones:
                if drone.active:
                    any_active = True
                    break

            if not any_active:
                wd.state = WAVE_STATE_INTERMISSION
                wd.intermission_timer = 3.5
                self.sfx.play("powerup", 0.8)
                self.player.missiles_ammo = min(16, self.player.missiles_ammo + 4)
                self.player.score += 250 * wd.wave_index

        elif wd.state == WAVE_STATE_INTERMISSION:
            wd.intermission_timer -= dt
            if wd.intermission_timer <= 0.0:
                wd.start_next_wave()

    def _resolve_collisions(self):
        # 1. Flak Bullets vs Broadphase Grid
        for bullet in self.flak_pool.slots:
            if not bullet.active:
                continue

            query_rad = bullet.radius + 26.0
            candidates = self.spatial_grid.query_radius(bullet.x, bullet.y, query_rad)

            for entity in candidates:
                if not bullet.active:
                    break

                if not bullet.is_enemy and isinstance(entity, DroneRaider) and entity.active:
                    dx = entity.x - bullet.x
                    dy = entity.y - bullet.y
                    hit_dist = entity.radius + bullet.radius
                    if (dx * dx + dy * dy) <= (hit_dist * hit_dist):
                        bullet.active = False
                        if entity.take_damage(bullet.damage, self.particle_pool, self.sfx):
                            self.player.score += 40 + entity.type * 30
                            self.wave_director.total_kills += 1
                        break

                elif bullet.is_enemy and isinstance(entity, PlayerShip):
                    dx = entity.x - bullet.x
                    dy = entity.y - bullet.y
                    hit_dist = entity.radius + bullet.radius
                    if (dx * dx + dy * dy) <= (hit_dist * hit_dist):
                        bullet.active = False
                        entity.take_damage(bullet.damage, self.particle_pool)
                        self.sfx.play("shield_block" if entity.shield > 0 else "hit", 0.6)
                        break

                elif isinstance(entity, OrbitalAsteroid) and entity.active:
                    dx = entity.x - bullet.x
                    dy = entity.y - bullet.y
                    hit_dist = entity.radius + bullet.radius
                    if (dx * dx + dy * dy) <= (hit_dist * hit_dist):
                        bullet.active = False
                        entity.hp -= bullet.damage
                        self.particle_pool.spawn_burst(bullet.x, bullet.y, 2, 20.0, 50.0, 140, 150, 170)
                        self.sfx.play("hit", 0.3)
                        break

        # 2. Guided Missiles vs Broadphase Grid
        for missile in self.missile_pool.slots:
            if not missile.active:
                continue

            query_rad = missile.radius + 28.0
            candidates = self.spatial_grid.query_radius(missile.x, missile.y, query_rad)

            for entity in candidates:
                if not missile.active:
                    break

                if isinstance(entity, DroneRaider) and entity.active:
                    dx = entity.x - missile.x
                    dy = entity.y - missile.y
                    hit_dist = entity.radius + missile.radius
                    if (dx * dx + dy * dy) <= (hit_dist * hit_dist):
                        missile.active = False
                        self.particle_pool.spawn_burst(missile.x, missile.y, 22, 60.0, 180.0, 255, 160, 40)
                        if entity.take_damage(missile.damage, self.particle_pool, self.sfx):
                            self.player.score += 60 + entity.type * 40
                            self.wave_director.total_kills += 1
                        break

                elif isinstance(entity, OrbitalAsteroid) and entity.active:
                    dx = entity.x - missile.x
                    dy = entity.y - missile.y
                    hit_dist = entity.radius + missile.radius
                    if (dx * dx + dy * dy) <= (hit_dist * hit_dist):
                        missile.active = False
                        self.particle_pool.spawn_burst(missile.x, missile.y, 18, 50.0, 160.0, 255, 140, 40)
                        self.sfx.play("explosion", 0.7)
                        break

        # 3. Player vs Drones & Asteroids (Direct Hull Ramming)
        player_candidates = self.spatial_grid.query_radius(self.player.x, self.player.y, self.player.radius + 32.0)
        for entity in player_candidates:
            if isinstance(entity, DroneRaider) and entity.active:
                dx = entity.x - self.player.x
                dy = entity.y - self.player.y
                ram_dist = entity.radius + self.player.radius
                if (dx * dx + dy * dy) <= (ram_dist * ram_dist):
                    self.player.take_damage(28.0, self.particle_pool)
                    entity.take_damage(50.0, self.particle_pool, self.sfx)
                    self.sfx.play("shield_block", 0.8)

            elif isinstance(entity, OrbitalAsteroid) and entity.active:
                dx = entity.x - self.player.x
                dy = entity.y - self.player.y
                ram_dist = entity.radius + self.player.radius
                dist = math.sqrt(max(0.01, dx * dx + dy * dy))
                if dist <= ram_dist:
                    nx = dx / dist
                    ny = dy / dist
                    self.player.x = entity.x - nx * ram_dist
                    self.player.y = entity.y - ny * ram_dist
                    self.player.vx = -nx * 140.0
                    self.player.vy = -ny * 140.0
                    self.player.take_damage(20.0, self.particle_pool)
                    self.sfx.play("shield_block", 0.75)

    def draw_world(self, aim_angle: float):
        for sx, sy, sb in self.stars:
            val = int(sb * 220)
            draw_circle(int(sx), int(sy), 1.2 if sb > 0.6 else 0.8, Color(val, val, val, 220))

        self._draw_celestial_planet()

        traj_points = self.gravity_well.predict_orbit(self.player.x, self.player.y,
                                                      self.player.vx, self.player.vy,
                                                      steps=42, step_dt=0.08,
                                                      gravity_enabled=self.gravity_enabled)
        for i in range(len(traj_points) - 1):
            p1 = traj_points[i]
            p2 = traj_points[i + 1]
            fade = 1.0 - (i / float(len(traj_points)))
            alpha = int(clamp(fade * 180, 20, 180))
            draw_line_ex(Vector2(float(p1[0]), float(p1[1])), Vector2(float(p2[0]), float(p2[1])),
                         1.8, Color(40, 220, 180, alpha))
            if i % 3 == 0:
                draw_circle(int(p1[0]), int(p1[1]), 2.2, Color(80, 255, 210, alpha + 30))

        for ast in self.asteroids:
            ast.draw()

        for drone in self.drones:
            drone.draw()

        if not self.game_over:
            self.player.draw(aim_angle)

        self.flak_pool.draw()
        self.missile_pool.draw()
        self.particle_pool.draw()

        ret_dist = 60.0
        rx = self.player.x + math.cos(aim_angle) * ret_dist
        ry = self.player.y + math.sin(aim_angle) * ret_dist
        draw_circle_lines(int(rx), int(ry), 8.0, Color(70, 215, 255, 200))
        draw_circle(int(rx), int(ry), 1.8, Color(255, 255, 255, 255))

    def _draw_celestial_planet(self):
        gw = self.gravity_well
        pcx = int(gw.cx)
        pcy = int(gw.cy)

        draw_circle(pcx, pcy, gw.atmosphere_radius, Color(30, 75, 140, 35))
        draw_circle(pcx, pcy, gw.atmosphere_radius * 0.75, Color(40, 110, 190, 55))
        draw_circle(pcx, pcy, gw.atmosphere_radius * 0.55, Color(60, 140, 220, 85))
        draw_circle_lines(pcx, pcy, gw.atmosphere_radius, Color(70, 150, 240, 75))
        draw_circle_lines(pcx, pcy, gw.radius + 12.0, Color(90, 180, 255, 110))

        draw_circle(pcx, pcy, gw.radius, Color(24, 38, 68, 255))
        draw_circle(pcx, pcy, gw.radius * 0.85, Color(18, 30, 54, 255))
        draw_circle_lines(pcx, pcy, gw.radius, Color(110, 190, 255, 230))

        for offset_y in [-24, -10, 8, 22]:
            rad_slice = math.sqrt(max(1.0, gw.radius * gw.radius - offset_y * offset_y)) * 0.95
            draw_line(int(gw.cx - rad_slice), int(gw.cy + offset_y),
                      int(gw.cx + rad_slice), int(gw.cy + offset_y), Color(42, 65, 110, 255))


# ==============================================================================
# BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY
# ==============================================================================

class OrbitalXRayTelemetry:
    """
    Pattern: Telemetry & Pattern Inspection X-Ray Overlay ([Tab] & [F1]).
    Visualizes internal pattern metrics: vector fields, spatial grids, pool gauges, and FSM states.
    """
    def __init__(self):
        pass

    def draw_gravity_vector_field(self, sim: WorldSimulation):
        gw = sim.gravity_well
        step = 85
        cols = SCREEN_WIDTH // step + 1
        rows = SCREEN_HEIGHT // step + 1

        for c in range(cols):
            for r in range(rows):
                sx = float(c * step + step // 2)
                sy = float(r * step + step // 2)

                dx = gw.cx - sx
                dy = gw.cy - sy
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < gw.radius + 10.0:
                    continue

                if sim.gravity_enabled:
                    ax, ay = gw.compute_acceleration(sx, sy)
                    mag = math.sqrt(ax * ax + ay * ay)
                    arrow_len = min(22.0, max(4.0, mag * 0.16))
                    ndx = ax / max(0.001, mag)
                    ndy = ay / max(0.001, mag)
                    color = Color(60, 190, 240, int(clamp(mag * 0.9 + 25, 30, 160)))
                else:
                    draw_circle(int(sx), int(sy), 1.2, Color(80, 95, 120, 60))
                    continue

                ex = sx + ndx * arrow_len
                ey = sy + ndy * arrow_len
                draw_line(int(sx), int(sy), int(ex), int(ey), color)
                draw_circle(int(ex), int(ey), 1.5, color)

    def draw_spatial_grid_overlay(self, sim: WorldSimulation):
        grid = sim.spatial_grid
        cell_size = int(grid.cell_size)
        cols = SCREEN_WIDTH // cell_size + 1
        rows = SCREEN_HEIGHT // cell_size + 1

        for c in range(cols):
            x = c * cell_size
            draw_line(x, 0, x, SCREEN_HEIGHT, Color(40, 60, 95, 35))
        for r in range(rows):
            y = r * cell_size
            draw_line(0, y, SCREEN_WIDTH, y, Color(40, 60, 95, 35))

        for coord, entities in grid.grid.items():
            count = len(entities)
            if count <= 0:
                continue

            cx, cy = coord
            px = cx * cell_size
            py = cy * cell_size
            if px < -cell_size or px > SCREEN_WIDTH or py < -cell_size or py > SCREEN_HEIGHT:
                continue

            alpha = min(110, count * 28 + 20)
            draw_rectangle(px, py, cell_size, cell_size, Color(50, 140, 220, alpha))
            draw_rectangle_lines(px, py, cell_size, cell_size, Color(90, 200, 255, alpha + 40))
            draw_text(str(count), px + 4, py + 4, 10, Color(180, 230, 255, 220))

    def draw_dashboard(self, sim: WorldSimulation):
        # LEFT HUD PANEL: Physics & Object Pool Metrics (x = 18..405)
        panel_x = 18
        panel_y = 65
        panel_w = 385
        panel_h = 425

        draw_rectangle(panel_x, panel_y, panel_w, panel_h, Color(10, 16, 28, 225))
        draw_rectangle_lines(panel_x, panel_y, panel_w, panel_h, Color(45, 75, 125, 255))
        draw_text("X-RAY TELEMETRY & SYSTEM METRICS", panel_x + 14, panel_y + 12, 13, Color(70, 215, 255, 255))
        draw_line(panel_x + 14, panel_y + 32, panel_x + panel_w - 14, panel_y + 32, Color(45, 75, 125, 200))

        grav_text = "NEWTONIAN (1/r^2 SOFTENED)" if sim.gravity_enabled else "MUTED (ZERO-G FLAT SPACE)"
        grav_color = Color(80, 240, 160, 255) if sim.gravity_enabled else Color(255, 180, 60, 255)
        draw_text("Celestial Gravity [F1]:", panel_x + 14, panel_y + 42, 11, Color(160, 185, 220, 255))
        draw_text(grav_text, panel_x + 155, panel_y + 42, 11, grav_color)

        gm_str = f"G*M: {int(sim.gravity_well.gm)} | Softening eps: 47.4 px"
        draw_text(gm_str, panel_x + 14, panel_y + 58, 10, Color(120, 145, 180, 255))
        draw_text("PRE-ALLOCATED OBJECT POOLS (ZERO HEAP CHURN):", panel_x + 14, panel_y + 80, 11, Color(245, 210, 70, 255))

        self._draw_pool_gauge(panel_x + 14, panel_y + 100, "Flak Rounds Pool",
                              sim.flak_pool.active_count, sim.flak_pool.capacity,
                              sim.flak_pool.high_water_mark, Color(70, 190, 255, 255))

        self._draw_pool_gauge(panel_x + 14, panel_y + 150, "Micro-Missiles Pool",
                              sim.missile_pool.active_count, sim.missile_pool.capacity,
                              sim.missile_pool.high_water_mark, Color(255, 160, 60, 255))

        self._draw_pool_gauge(panel_x + 14, panel_y + 200, "Visual Particles Pool",
                              sim.particle_pool.active_count, sim.particle_pool.capacity,
                              sim.particle_pool.high_water_mark, Color(180, 120, 255, 255))

        draw_text("SPATIALGRID2D PARTITIONING (BROADPHASE):", panel_x + 14, panel_y + 260, 11, Color(70, 215, 255, 255))
        grid_info = f"Cell Size: 64x64 px | Entities Tracked: {sim.spatial_grid.entity_count}"
        draw_text(grid_info, panel_x + 14, panel_y + 280, 10, Color(170, 195, 230, 255))
        occ_cells = len(sim.spatial_grid.grid)
        draw_text(f"Active Occupied Buckets: {occ_cells} cells", panel_x + 14, panel_y + 296, 10, Color(130, 160, 195, 255))

        draw_text("C++ ARCHITECTURAL NOTE:", panel_x + 14, panel_y + 325, 10, Color(255, 215, 0, 255))
        note1 = "Pre-allocated std::array<T, N> contiguous memory pools"
        note2 = "Euler-Cromer orbital symplectic phase-space preservation"
        note3 = "O(N) Spatial Hash Grid drops quadratic O(N^2) pairwise checks"
        draw_text(note1, panel_x + 14, panel_y + 342, 9, Color(140, 165, 195, 255))
        draw_text(note2, panel_x + 14, panel_y + 356, 9, Color(140, 165, 195, 255))
        draw_text(note3, panel_x + 14, panel_y + 370, 9, Color(140, 165, 195, 255))
        draw_text("[Tab] Toggle Telemetry | [F1] Toggle Planet Gravity", panel_x + 14, panel_y + 398, 10, Color(90, 225, 170, 255))

        # RIGHT HUD PANEL: Raider FSM & Wave Director Metrics (x = 990..1262)
        r_x = 990
        r_y = 65
        r_w = 272
        r_h = 390

        draw_rectangle(r_x, r_y, r_w, r_h, Color(10, 16, 28, 225))
        draw_rectangle_lines(r_x, r_y, r_w, r_h, Color(45, 75, 125, 255))
        draw_text("RAIDER AI & WAVE DIRECTOR", r_x + 14, r_y + 12, 12, Color(255, 175, 70, 255))
        draw_line(r_x + 14, r_y + 30, r_x + r_w - 14, r_y + 30, Color(45, 75, 125, 200))

        wd = sim.wave_director
        wd_state_name = "SPAWNING RAIDS" if wd.state == WAVE_STATE_SPAWNING else (
            "ENGAGED COMBAT" if wd.state == WAVE_STATE_COMBAT else "INTERMISSION")
        draw_text(f"Wave Sector: {wd.wave_index}", r_x + 14, r_y + 40, 11, Color(245, 245, 255, 255))
        draw_text(f"Pacing State: {wd_state_name}", r_x + 14, r_y + 56, 10, Color(160, 210, 255, 255))
        draw_text(f"Threat Budget: {int(wd.threat_budget)} / {int(wd.max_threat_budget)} pts", r_x + 14, r_y + 72, 10, Color(150, 180, 215, 255))
        draw_text(f"Raiders Neutralized: {wd.total_kills}", r_x + 14, r_y + 88, 10, Color(150, 180, 215, 255))
        draw_text("DRONE FSM STATE MATRIX:", r_x + 14, r_y + 115, 11, Color(255, 205, 60, 255))

        counts = [0, 0, 0, 0]
        total_active_drones = 0
        for d in sim.drones:
            if d.active:
                total_active_drones += 1
                if 0 <= d.state <= 3:
                    counts[d.state] += 1

        state_names = ["0: STATE_ORBIT", "1: SLINGSHOT_DIVE", "2: ATTACK_RUN", "3: DISENGAGE"]
        state_colors = [
            Color(70, 190, 255, 255),
            Color(255, 140, 50, 255),
            Color(255, 70, 70, 255),
            Color(180, 120, 255, 255)
        ]

        for i in range(4):
            sy = r_y + 138 + i * 26
            c_val = counts[i]
            pct = int((c_val / max(1, total_active_drones)) * 100) if total_active_drones > 0 else 0
            draw_text(state_names[i], r_x + 14, sy, 10, state_colors[i])
            draw_text(f"{c_val} ({pct}%)", r_x + 195, sy, 10, Color(220, 230, 245, 255))
            draw_rectangle(r_x + 14, sy + 14, 240, 3, Color(25, 35, 55, 255))
            bar_fill = int(240 * (pct / 100.0))
            if bar_fill > 0:
                draw_rectangle(r_x + 14, sy + 14, bar_fill, 3, state_colors[i])

        draw_text(f"Total Active Raiders: {total_active_drones} / {CAPACITY_DRONES}", r_x + 14, r_y + 258, 10, Color(180, 200, 230, 255))
        scouts = 0
        interceptors = 0
        bombers = 0
        for d in sim.drones:
            if d.active:
                if d.type == DRONE_SCOUT:
                    scouts += 1
                elif d.type == DRONE_INTERCEPTOR:
                    interceptors += 1
                elif d.type == DRONE_HEAVY_BOMBER:
                    bombers += 1

        draw_text(f"  Scouts: {scouts}", r_x + 14, r_y + 276, 9, Color(60, 220, 210, 255))
        draw_text(f"  Interceptors: {interceptors}", r_x + 14, r_y + 292, 9, Color(245, 150, 40, 255))
        draw_text(f"  Heavy Bombers: {bombers}", r_x + 14, r_y + 308, 9, Color(230, 45, 75, 255))
        draw_text(f"Player Score: {sim.player.score} pts", r_x + 14, r_y + 340, 11, Color(255, 225, 70, 255))
        draw_text(f"Micro-Missiles: {sim.player.missiles_ammo} remaining", r_x + 14, r_y + 358, 10, Color(160, 210, 255, 255))

    def _draw_pool_gauge(self, x: int, y: int, label: str, active: int, capacity: int, high_water: int, color: Color):
        ratio = max(0.0, min(1.0, active / float(capacity)))
        hw_ratio = max(0.0, min(1.0, high_water / float(capacity)))
        bar_w = 355
        bar_h = 10

        draw_text(f"{label}: {active} / {capacity} (Peak: {high_water})", x, y, 10, Color(200, 220, 245, 255))
        draw_rectangle(x, y + 16, bar_w, bar_h, Color(25, 38, 60, 255))
        fill_w = int(bar_w * ratio)
        if fill_w > 0:
            draw_rectangle(x, y + 16, fill_w, bar_h, color)
        hw_x = x + int(bar_w * hw_ratio)
        draw_line(hw_x, y + 14, hw_x, y + 16 + bar_h + 2, Color(255, 80, 80, 255))
        draw_rectangle_lines(x, y + 16, bar_w, bar_h, Color(55, 80, 120, 255))


# ==============================================================================
# BLOCK 4: MAIN GAME LOOP & AUTOMATED SMOKE TEST
# ==============================================================================

class OrbitalSiegeGame:
    """
    Main Application & Loop Runner.
    Multiplexes simultaneous Keyboard/Mouse and Gamepad controls,
    clears top HUD space for the Global Settings Bar, and guarantees clean teardown.
    """
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()

        self.sfx = SoundLibrary()
        self.sfx.init_defaults()

        self.sim = WorldSimulation(self.sfx)
        self.telemetry = OrbitalXRayTelemetry()
        self.show_xray = True

    def handle_input(self) -> tuple:
        move_vec = get_dual_move_2d()
        move_x = move_vec.x
        move_y = move_vec.y

        look_vec = get_dual_look_2d()
        look_x = look_vec.x
        look_y = look_vec.y
        stick_mag = math.sqrt(look_x * look_x + look_y * look_y)
        if stick_mag > 0.25:
            aim_angle = math.atan2(look_y, look_x)
        else:
            mouse_pos = get_mouse_position()
            aim_angle = math.atan2(mouse_pos.y - self.sim.player.y, mouse_pos.x - self.sim.player.x)

        is_firing_primary = is_dual_primary_fire_down()
        is_firing_secondary = is_dual_secondary_fire_pressed()

        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
            self.sfx.play("click", 0.6)

        if is_dual_pattern_toggle_pressed():
            self.sim.gravity_enabled = not self.sim.gravity_enabled
            self.sfx.play("confirm" if self.sim.gravity_enabled else "cancel", 0.7)

        if is_dual_reset_pressed():
            self.sim.reset()
            self.sfx.play("confirm", 0.8)

        return move_x, move_y, aim_angle, is_firing_primary, is_firing_secondary

    def update(self):
        dt = min(get_frame_time(), 0.05)
        move_x, move_y, aim_angle, fire_p, fire_s = self.handle_input()
        self.sim.update(dt, move_x, move_y, aim_angle, fire_p, fire_s)
        self.last_aim_angle = aim_angle

    def draw(self):
        begin_drawing()
        clear_background(Color(8, 12, 20, 255))

        self.sim.draw_world(getattr(self, "last_aim_angle", -math.pi / 2.0))

        if self.show_xray:
            self.telemetry.draw_gravity_vector_field(self.sim)
            self.telemetry.draw_spatial_grid_overlay(self.sim)
            self.telemetry.draw_dashboard(self.sim)

        # Player Vital HUD (x = 20..230)
        p = self.sim.player
        draw_rectangle(20, 16, 210, 40, Color(12, 18, 30, 210))
        draw_rectangle_lines(20, 16, 210, 40, Color(45, 75, 120, 255))

        draw_text("SHIELD", 28, 22, 10, Color(100, 210, 255, 255))
        draw_rectangle(75, 23, 145, 8, Color(25, 40, 65, 255))
        s_fill = int(145 * max(0.0, min(1.0, p.shield / p.max_shield)))
        draw_rectangle(75, 23, s_fill, 8, Color(60, 190, 255, 255))

        draw_text("HULL", 28, 38, 10, Color(255, 130, 100, 255))
        draw_rectangle(75, 39, 145, 8, Color(60, 25, 25, 255))
        h_fill = int(145 * max(0.0, min(1.0, p.hp / p.max_hp)))
        draw_rectangle(75, 39, h_fill, 8, Color(245, 70, 70, 255))

        if self.sim.game_over:
            draw_rectangle(SCREEN_WIDTH // 2 - 220, SCREEN_HEIGHT // 2 - 60, 440, 120, Color(15, 10, 20, 240))
            draw_rectangle_lines(SCREEN_WIDTH // 2 - 220, SCREEN_HEIGHT // 2 - 60, 440, 120, Color(255, 60, 60, 255))
            draw_text("DEFENSE FIGHTER DESTROYED", SCREEN_WIDTH // 2 - 165, SCREEN_HEIGHT // 2 - 35, 18, Color(255, 80, 80, 255))
            draw_text("Press [R] or Gamepad Start to Re-enter Orbit", SCREEN_WIDTH // 2 - 170, SCREEN_HEIGHT // 2 + 10, 12, Color(220, 230, 250, 255))

        # Top-Bar UI Clearance & Settings Dropdown Hook
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
    OrbitalSiegeGame().run(smoke_test=is_smoke)
