# -*- coding: utf-8 -*-
"""
Hitscan Range - Instant Raycast vs Travel Projectile Weapon Systems
===================================================================
Section          : 3.2 Combat & Weapons
Pattern Category : Combat & Weapons
Dimension        : 3D

Problem Solved:
  In 3D shooters and combat games, choosing between Hitscan and Travel Projectiles
  fundamentally alters weapon feel, network replication, and skill expression.
  Without hitscan, responsive point-and-click shooting (snipers, lasers, revolvers)
  feels sluggish due to projectile travel latency. Conversely, naively using hitscan
  for all weapons eliminates the tactical skill of leading distant moving targets
  and makes ballistics (rockets, arrows, grenade arcs) impossible. Furthermore,
  fast travel projectiles suffer from "bullet-through-paper" tunneling without
  Continuous Collision Detection (CCD).

How the Patterns Work:
  1. Hitscan (Instant Raycast):
     Casts a mathematical ray R(t) = Origin + t * Dir (t in [0, max_dist]).
     Finds the closest intersection (t_min >= 0) across all scene colliders in the
     exact frame of trigger pull. Effective velocity is infinite (v = infinity),
     travel time is zero (t_impact = 0.0 ms), and zero leading is required.
  2. Ballistic / Travel Projectile with Swept CCD:
     Spawns a physical projectile entity with velocity V = v * Dir. Time to impact
     is t_impact = distance / v. Moving targets travel delta_x = v_target * t_impact,
     requiring players to lead their aim ahead of the target. Swept segment CCD
     between previous and current positions guarantees zero tunneling through thin plates.
  3. Lead Aim Vector Math:
     Predicts future intercept: P_lead = P_target + V_target * (distance / v_proj).

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - [W][A][S][D] / Gamepad Left Stick     : Walk around the shooting booth / gallery
  - Mouse Move / Gamepad Right Stick      : Aim crosshair (Yaw & Pitch look)
  - Left Mouse Button / Gamepad RT        : Fire Weapon (Primary Trigger)
  - Right Mouse Button / [C]              : Toggle Mouse Cursor Lock (FPS Free-Look)
  - [Tab] / Gamepad View (Select)         : Toggle X-Ray Telemetry & Math Inspector Overlay
  - [F1]  / Gamepad LB                    : Toggle Weapon Mode: [HITSCAN (Instant)] vs [PROJECTILE (Travel Time)]
  - [F2]  / Gamepad RB                    : Toggle Target Movement: [MOVING RAILS] vs [STATIONARY]
  - [1] / [2] / [3]                       : Set Projectile Velocity: [1] Slow (25 m/s) | [2] Med (50 m/s) | [3] Fast (100 m/s)
  - [Ctrl +/-]                            : Increase / Decrease UI Font Size
  - [F11]                                 : Toggle Fullscreen
  - [R]   / Gamepad Start                 : Reset targets & accuracy statistics
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
WINDOW_TITLE = "Hitscan Range - Instant Raycast vs Travel Projectile (Raylib Pattern Lab)"

# Weapon Modes
MODE_HITSCAN = 0
MODE_PROJECTILE = 1

# Target Types
TARGET_TYPE_BULLSEYE = 0
TARGET_TYPE_RAIL = 1
TARGET_TYPE_DRONE = 2
TARGET_TYPE_OBSTACLE = 3


# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATION (HITSCAN & SWEPT CCD PROJECTILES)
# ==============================================================================

class Ray3D:
    """
    Mathematical 3D Ray defined by an origin point and a unit direction vector.
    R(t) = origin + t * dir,  where t >= 0.

    C++ Equivalent:
      struct Ray3D {
          Vector3 origin;
          Vector3 dir;
      };
    """
    def __init__(self, origin: Vector3, direction: Vector3):
        self.origin = Vector3(origin.x, origin.y, origin.z)
        dx = direction.x
        dy = direction.y
        dz = direction.z
        length = math.sqrt(dx * dx + dy * dy + dz * dz)
        if length > 0.00001:
            self.dir = Vector3(dx / length, dy / length, dz / length)
        else:
            self.dir = Vector3(0.0, 0.0, 1.0)


class RayHit:
    """
    Stores the result of a geometric raycast intersection query.

    C++ Equivalent:
      struct RayHit {
          bool hit;
          float distance;
          Vector3 point;
          Vector3 normal;
          int target_id;
          char target_name[32];
          bool is_bullseye;
          int score_value;
      };
    """
    def __init__(self):
        self.hit = False
        self.distance = 999999.0
        self.point = Vector3(0.0, 0.0, 0.0)
        self.normal = Vector3(0.0, 1.0, 0.0)
        self.target_id = -1
        self.target_name = "None"
        self.is_bullseye = False
        self.score_value = 0


def intersect_ray_sphere(ray: Ray3D, center: Vector3, radius: float) -> tuple:
    """
    Computes exact geometric intersection between a 3D ray and a sphere.
    Solves quadratic: ||(O + t*D) - C||^2 = r^2
    Returns: (hit: bool, t: float, hit_point: Vector3, normal: Vector3)
    """
    ox = ray.origin.x - center.x
    oy = ray.origin.y - center.y
    oz = ray.origin.z - center.z

    b = ray.dir.x * ox + ray.dir.y * oy + ray.dir.z * oz
    c = (ox * ox + oy * oy + oz * oz) - (radius * radius)

    discriminant = b * b - c
    if discriminant < 0.0:
        return (False, 0.0, Vector3(0.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0))

    sqrt_disc = math.sqrt(discriminant)
    t = -b - sqrt_disc
    if t < 0.0:
        t = -b + sqrt_disc
        if t < 0.0:
            return (False, 0.0, Vector3(0.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0))

    px = ray.origin.x + ray.dir.x * t
    py = ray.origin.y + ray.dir.y * t
    pz = ray.origin.z + ray.dir.z * t
    hit_pt = Vector3(px, py, pz)

    nx = (px - center.x) / radius
    ny = (py - center.y) / radius
    nz = (pz - center.z) / radius
    normal = Vector3(nx, ny, nz)

    return (True, t, hit_pt, normal)


def intersect_ray_aabb(ray: Ray3D, box_min: Vector3, box_max: Vector3) -> tuple:
    """
    Computes ray vs Axis-Aligned Bounding Box (AABB) intersection using the
    standard slab method (Kay-Kajiya).
    Returns: (hit: bool, t: float, hit_point: Vector3, normal: Vector3)
    """
    t_min = 0.0
    t_max = 999999.0
    normal_axis = 0
    normal_sign = 1.0

    # Test X slab
    if abs(ray.dir.x) > 0.000001:
        inv_d = 1.0 / ray.dir.x
        t1 = (box_min.x - ray.origin.x) * inv_d
        t2 = (box_max.x - ray.origin.x) * inv_d
        if t1 > t2:
            t1, t2 = t2, t1
        if t1 > t_min:
            t_min = t1
            normal_axis = 0
            normal_sign = -1.0 if ray.dir.x > 0.0 else 1.0
        if t2 < t_max:
            t_max = t2
        if t_min > t_max:
            return (False, 0.0, Vector3(0.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0))
    else:
        if ray.origin.x < box_min.x or ray.origin.x > box_max.x:
            return (False, 0.0, Vector3(0.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0))

    # Test Y slab
    if abs(ray.dir.y) > 0.000001:
        inv_d = 1.0 / ray.dir.y
        t1 = (box_min.y - ray.origin.y) * inv_d
        t2 = (box_max.y - ray.origin.y) * inv_d
        if t1 > t2:
            t1, t2 = t2, t1
        if t1 > t_min:
            t_min = t1
            normal_axis = 1
            normal_sign = -1.0 if ray.dir.y > 0.0 else 1.0
        if t2 < t_max:
            t_max = t2
        if t_min > t_max:
            return (False, 0.0, Vector3(0.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0))
    else:
        if ray.origin.y < box_min.y or ray.origin.y > box_max.y:
            return (False, 0.0, Vector3(0.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0))

    # Test Z slab
    if abs(ray.dir.z) > 0.000001:
        inv_d = 1.0 / ray.dir.z
        t1 = (box_min.z - ray.origin.z) * inv_d
        t2 = (box_max.z - ray.origin.z) * inv_d
        if t1 > t2:
            t1, t2 = t2, t1
        if t1 > t_min:
            t_min = t1
            normal_axis = 2
            normal_sign = -1.0 if ray.dir.z > 0.0 else 1.0
        if t2 < t_max:
            t_max = t2
        if t_min > t_max:
            return (False, 0.0, Vector3(0.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0))
    else:
        if ray.origin.z < box_min.z or ray.origin.z > box_max.z:
            return (False, 0.0, Vector3(0.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0))

    if t_min < 0.0:
        t_min = t_max
        if t_min < 0.0:
            return (False, 0.0, Vector3(0.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0))

    hit_pt = Vector3(
        ray.origin.x + ray.dir.x * t_min,
        ray.origin.y + ray.dir.y * t_min,
        ray.origin.z + ray.dir.z * t_min
    )

    norm = Vector3(0.0, 0.0, 0.0)
    if normal_axis == 0:
        norm.x = normal_sign
    elif normal_axis == 1:
        norm.y = normal_sign
    else:
        norm.z = normal_sign

    return (True, t_min, hit_pt, norm)


def compute_lead_intercept(target_pos: Vector3, target_vel: Vector3,
                           shooter_pos: Vector3, projectile_speed: float) -> Vector3:
    """
    Calculates future predicted target intercept position based on projectile travel time.
    First-order approximation: t = distance / projectile_speed
    P_lead = P_target + V_target * t
    """
    dx = target_pos.x - shooter_pos.x
    dy = target_pos.y - shooter_pos.y
    dz = target_pos.z - shooter_pos.z
    dist = math.sqrt(dx * dx + dy * dy + dz * dz)

    if projectile_speed <= 0.001:
        return Vector3(target_pos.x, target_pos.y, target_pos.z)

    time_to_impact = dist / projectile_speed
    lead_x = target_pos.x + target_vel.x * time_to_impact
    lead_y = target_pos.y + target_vel.y * time_to_impact
    lead_z = target_pos.z + target_vel.z * time_to_impact
    return Vector3(lead_x, lead_y, lead_z)


# ==============================================================================
# BLOCK 2: WORLD SIMULATION & ENTITIES
# ==============================================================================

class Target3D:
    """
    Interactive target in the firing range.
    Can be stationary, moving along a rail, or an evasive flying drone.
    Supports spring-loaded mechanical knockdown and recovery animation.
    """
    def __init__(self, target_id: int, name: str, target_type: int,
                 base_pos: Vector3, radius: float = 0.8,
                 rail_min_x: float = 0.0, rail_max_x: float = 0.0, speed: float = 0.0):
        self.id = target_id
        self.name = name
        self.type = target_type
        self.base_pos = Vector3(base_pos.x, base_pos.y, base_pos.z)
        self.pos = Vector3(base_pos.x, base_pos.y, base_pos.z)
        self.vel = Vector3(speed, 0.0, 0.0)
        self.radius = radius
        self.rail_min_x = rail_min_x
        self.rail_max_x = rail_max_x
        self.speed = speed
        self.active = True
        self.hp = 3 if target_type == TARGET_TYPE_DRONE else 1
        self.max_hp = self.hp

        # Mechanical spring knockdown state
        self.knockdown_angle = 0.0
        self.knockdown_timer = 0.0
        self.flash_timer = 0.0
        self.respawn_timer = 0.0
        self.anim_timer = random.uniform(0.0, 10.0)

    def update(self, dt: float, movement_enabled: bool):
        self.anim_timer += dt
        if self.flash_timer > 0.0:
            self.flash_timer = max(0.0, self.flash_timer - dt * 4.0)

        # Handle respawn after destruction (for drones)
        if not self.active:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0.0:
                self.active = True
                self.hp = self.max_hp
                self.knockdown_angle = 0.0
            return

        # Mechanical knockdown spring recovery
        if self.knockdown_timer > 0.0:
            self.knockdown_timer -= dt
            if self.knockdown_timer <= 0.0:
                self.knockdown_angle = 0.0
            else:
                # Smooth spring bounce back upright
                ratio = self.knockdown_timer / 1.6
                self.knockdown_angle = 85.0 * ratio

        # Rail movement
        if movement_enabled and self.type == TARGET_TYPE_RAIL:
            self.pos.x += self.vel.x * dt
            if self.pos.x > self.rail_max_x:
                self.pos.x = self.rail_max_x
                self.vel.x = -abs(self.vel.x)
            elif self.pos.x < self.rail_min_x:
                self.pos.x = self.rail_min_x
                self.vel.x = abs(self.vel.x)

        # Drone evasive flight movement
        elif movement_enabled and self.type == TARGET_TYPE_DRONE:
            # Figure-eight path in front of range backstop
            w_x = (self.rail_max_x - self.rail_min_x) * 0.5
            center_x = (self.rail_max_x + self.rail_min_x) * 0.5
            target_x = center_x + math.sin(self.anim_timer * 1.2) * w_x
            target_y = self.base_pos.y + math.cos(self.anim_timer * 2.4) * 1.8
            self.vel.x = (target_x - self.pos.x) * 4.0
            self.vel.y = (target_y - self.pos.y) * 4.0
            self.pos.x = target_x
            self.pos.y = target_y
        else:
            self.vel.x = 0.0
            self.vel.y = 0.0

    def trigger_hit(self, is_bullseye: bool):
        self.flash_timer = 1.0
        self.hp -= 1
        if self.type != TARGET_TYPE_OBSTACLE:
            self.knockdown_angle = 85.0
            self.knockdown_timer = 1.6
        if self.hp <= 0:
            if self.type == TARGET_TYPE_DRONE:
                self.active = False
                self.respawn_timer = 2.4


class Obstacle3D:
    """Solid cover barrier demonstrating raycast occlusion / early termination."""
    def __init__(self, min_pos: Vector3, max_pos: Vector3, label: str):
        self.min_pos = min_pos
        self.max_pos = max_pos
        self.label = label
        self.flash_timer = 0.0

    def update(self, dt: float):
        if self.flash_timer > 0.0:
            self.flash_timer = max(0.0, self.flash_timer - dt * 4.0)


class Projectile3D:
    """
    Physical travel projectile entity with Continuous Collision Detection (CCD).
    Sweeps a segment each frame to guarantee hitting thin plates at high speed.
    """
    def __init__(self):
        self.active = False
        self.pos = Vector3(0.0, 0.0, 0.0)
        self.prev_pos = Vector3(0.0, 0.0, 0.0)
        self.vel = Vector3(0.0, 0.0, 0.0)
        self.speed = 45.0
        self.lifetime = 0.0
        self.radius = 0.16
        self.travel_distance = 0.0


class TracerBeam3D:
    """Instant visual line connecting weapon muzzle to raycast impact point."""
    def __init__(self):
        self.active = False
        self.start_pos = Vector3(0.0, 0.0, 0.0)
        self.end_pos = Vector3(0.0, 0.0, 0.0)
        self.life = 0.0
        self.max_life = 0.12
        self.color = Color(0, 240, 255, 255)


class SparkParticle3D:
    """Pre-allocated 3D particle for impact sparks."""
    def __init__(self):
        self.active = False
        self.pos = Vector3(0.0, 0.0, 0.0)
        self.vel = Vector3(0.0, 0.0, 0.0)
        self.life = 0.0
        self.max_life = 0.4
        self.size = 0.08
        self.color = Color(255, 220, 80, 255)


class WeaponRig:
    """Manages weapon firing state, pools, and ballistic calculations."""
    def __init__(self):
        self.mode = MODE_HITSCAN
        self.projectile_speed = 50.0  # m/s
        self.fire_cooldown = 0.0
        self.fire_rate = 0.18  # seconds between shots
        self.recoil_kick = 0.0

        # Pre-allocated pools (zero garbage collection)
        self.projectiles = [Projectile3D() for _ in range(40)]
        self.tracers = [TracerBeam3D() for _ in range(25)]
        self.sparks = [SparkParticle3D() for _ in range(250)]

        # Statistics
        self.shots_fired = 0
        self.hits_registered = 0
        self.bullseyes = 0
        self.total_score = 0
        self.last_hit_name = "None"
        self.last_hit_distance = 0.0
        self.last_hit_score = 0
        self.hitmarker_timer = 0.0

    def spawn_spark_burst(self, pos: Vector3, normal: Vector3, count: int, color: Color):
        spawned = 0
        for s in self.sparks:
            if not s.active:
                s.active = True
                s.pos.x = pos.x
                s.pos.y = pos.y
                s.pos.z = pos.z
                # Bounce primarily along normal with radial spread
                rx = (random.random() - 0.5) * 8.0
                ry = (random.random() - 0.5) * 8.0
                rz = (random.random() - 0.5) * 8.0
                spd = 6.0 + random.random() * 8.0
                s.vel.x = normal.x * spd + rx
                s.vel.y = normal.y * spd + ry + 2.0
                s.vel.z = normal.z * spd + rz
                s.life = 0.25 + random.random() * 0.35
                s.max_life = s.life
                s.size = 0.07 + random.random() * 0.08
                s.color = color
                spawned += 1
                if spawned >= count:
                    break

    def spawn_tracer(self, start_pos: Vector3, end_pos: Vector3, color: Color):
        for t in self.tracers:
            if not t.active:
                t.active = True
                t.start_pos.x = start_pos.x
                t.start_pos.y = start_pos.y
                t.start_pos.z = start_pos.z
                t.end_pos.x = end_pos.x
                t.end_pos.y = end_pos.y
                t.end_pos.z = end_pos.z
                t.life = 0.12
                t.max_life = 0.12
                t.color = color
                break

    def spawn_projectile(self, muzzle_pos: Vector3, dir_vec: Vector3):
        for p in self.projectiles:
            if not p.active:
                p.active = True
                p.pos.x = muzzle_pos.x
                p.pos.y = muzzle_pos.y
                p.pos.z = muzzle_pos.z
                p.prev_pos.x = muzzle_pos.x
                p.prev_pos.y = muzzle_pos.y
                p.prev_pos.z = muzzle_pos.z
                p.speed = self.projectile_speed
                p.vel.x = dir_vec.x * self.projectile_speed
                p.vel.y = dir_vec.y * self.projectile_speed
                p.vel.z = dir_vec.z * self.projectile_speed
                p.lifetime = 4.0
                p.travel_distance = 0.0
                break

    def update(self, dt: float):
        if self.fire_cooldown > 0.0:
            self.fire_cooldown = max(0.0, self.fire_cooldown - dt)
        if self.recoil_kick > 0.0:
            self.recoil_kick = max(0.0, self.recoil_kick - dt * 14.0)
        if self.hitmarker_timer > 0.0:
            self.hitmarker_timer = max(0.0, self.hitmarker_timer - dt * 3.5)

        # Update active tracers
        for t in self.tracers:
            if t.active:
                t.life -= dt
                if t.life <= 0.0:
                    t.active = False

        # Update active sparks
        for s in self.sparks:
            if s.active:
                s.pos.x += s.vel.x * dt
                s.pos.y += s.vel.y * dt
                s.pos.z += s.vel.z * dt
                s.vel.y -= 18.0 * dt  # Gravity on sparks
                s.life -= dt
                if s.life <= 0.0 or s.pos.y < 0.0:
                    s.active = False


def raycast_world(ray: Ray3D, targets: list, obstacles: list, max_dist: float = 160.0) -> RayHit:
    """
    Core hitscan evaluation routine:
    Tests ray against all potential colliders in the world and returns the closest
    intersection (minimum positive distance t_min).
    """
    closest_hit = RayHit()
    closest_hit.distance = max_dist

    # 1. Test against scene obstacle barricades (Slab AABB)
    for obs in obstacles:
        hit, t, hit_pt, norm = intersect_ray_aabb(ray, obs.min_pos, obs.max_pos)
        if hit and t < closest_hit.distance:
            closest_hit.hit = True
            closest_hit.distance = t
            closest_hit.point.x = hit_pt.x
            closest_hit.point.y = hit_pt.y
            closest_hit.point.z = hit_pt.z
            closest_hit.normal.x = norm.x
            closest_hit.normal.y = norm.y
            closest_hit.normal.z = norm.z
            closest_hit.target_id = -99
            closest_hit.target_name = obs.label
            closest_hit.is_bullseye = False
            closest_hit.score_value = 0

    # 2. Test against all targets (Bullseyes, Rails, Drones)
    for tgt in targets:
        if not tgt.active or tgt.knockdown_angle > 45.0:
            continue

        # Test outer target hull (Sphere approximation)
        hit, t, hit_pt, norm = intersect_ray_sphere(ray, tgt.pos, tgt.radius)
        if hit and t < closest_hit.distance:
            # Check for inner bullseye accuracy
            bullseye_r = tgt.radius * 0.32
            dx = hit_pt.x - tgt.pos.x
            dy = hit_pt.y - tgt.pos.y
            dz = hit_pt.z - tgt.pos.z
            dist_from_center = math.sqrt(dx * dx + dy * dy + dz * dz)

            closest_hit.hit = True
            closest_hit.distance = t
            closest_hit.point.x = hit_pt.x
            closest_hit.point.y = hit_pt.y
            closest_hit.point.z = hit_pt.z
            closest_hit.normal.x = norm.x
            closest_hit.normal.y = norm.y
            closest_hit.normal.z = norm.z
            closest_hit.target_id = tgt.id
            closest_hit.target_name = tgt.name

            if dist_from_center <= bullseye_r:
                closest_hit.is_bullseye = True
                closest_hit.score_value = 100
            elif dist_from_center <= tgt.radius * 0.65:
                closest_hit.is_bullseye = False
                closest_hit.score_value = 50
            else:
                closest_hit.is_bullseye = False
                closest_hit.score_value = 25

    return closest_hit


# ==============================================================================
# BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY ([Tab] & [F1])
# ==============================================================================

def draw_xray_hud(weapon: WeaponRig, player_pos: Vector3, cam_forward: Vector3,
                  aim_hit: RayHit, active_target: Target3D, movement_enabled: bool):
    """
    Pedagogical X-Ray telemetry panel contrasting Hitscan vs Travel Projectile mechanics.
    """
    panel_x = 24
    panel_y = 65
    panel_w = 400
    panel_h = 490

    # Semitransparent dark tactical panel
    draw_rectangle(panel_x, panel_y, panel_w, panel_h, Color(10, 14, 24, 235))
    draw_rectangle_lines(panel_x, panel_y, panel_w, panel_h, Color(45, 75, 125, 255))
    draw_rectangle(panel_x, panel_y, panel_w, 28, Color(22, 34, 58, 255))
    draw_text("X-RAY TELEMETRY & BALLISTICS INSPECTOR [Tab]", panel_x + 12, panel_y + 7, 12, Color(0, 225, 255, 255))

    y = panel_y + 36
    lh = 16

    # 1. Weapon Pattern Toggle Status
    mode_name = "HITSCAN (INSTANT RAY)" if weapon.mode == MODE_HITSCAN else "TRAVEL PROJECTILE (SIMULATED)"
    mode_col = Color(0, 240, 255, 255) if weapon.mode == MODE_HITSCAN else Color(255, 160, 40, 255)
    draw_text(f"[F1] Weapon Mode    : {mode_name}", panel_x + 12, y, 11, mode_col); y += lh

    if weapon.mode == MODE_HITSCAN:
        draw_text(" * Velocity (v)     : INFINITE (Speed of Light)", panel_x + 12, y, 10, Color(180, 215, 250, 255)); y += lh
        draw_text(" * Travel Latency   : 0.00 ms (Frame-Instant)", panel_x + 12, y, 10, Color(180, 215, 250, 255)); y += lh
        draw_text(" * Lead Required    : 0.00 meters (Point-and-Click)", panel_x + 12, y, 10, Color(120, 255, 140, 255)); y += lh
    else:
        draw_text(f" * Velocity (v)     : {weapon.projectile_speed:.1f} m/s [Keys 1/2/3 to tune]", panel_x + 12, y, 10, Color(255, 200, 100, 255)); y += lh
        t_est = aim_hit.distance / weapon.projectile_speed if aim_hit.hit else 0.0
        draw_text(f" * Flight Time (t)  : d / v = {t_est:.2f} seconds", panel_x + 12, y, 10, Color(255, 200, 100, 255)); y += lh
        draw_text(" * CCD Collision    : Swept line segments per frame", panel_x + 12, y, 10, Color(180, 215, 250, 255)); y += lh
        draw_text(" * Lead Required    : MANDATORY for moving targets!", panel_x + 12, y, 10, Color(255, 90, 90, 255)); y += lh

    draw_line(panel_x + 10, y + 2, panel_x + panel_w - 10, y + 2, Color(40, 65, 105, 200)); y += 8

    # 2. Live Reticle Raycast Geometry
    draw_text("RAYCAST RETICLE GEOMETRY:", panel_x + 12, y, 11, Color(245, 210, 80, 255)); y += lh
    draw_text(f"Ray Origin  (O)     : ({player_pos.x:+.1f}, {player_pos.y:+.1f}, {player_pos.z:+.1f})", panel_x + 12, y, 10, Color(200, 220, 245, 255)); y += lh
    draw_text(f"Ray Direction (D)   : ({cam_forward.x:+.2f}, {cam_forward.y:+.2f}, {cam_forward.z:+.2f})", panel_x + 12, y, 10, Color(200, 220, 245, 255)); y += lh
    if aim_hit.hit:
        draw_text(f"Target Under Aim    : {aim_hit.target_name}", panel_x + 12, y, 10, Color(100, 255, 160, 255)); y += lh
        draw_text(f"Distance to Target  : {aim_hit.distance:.1f} meters", panel_x + 12, y, 10, Color(200, 220, 245, 255)); y += lh
        draw_text(f"Surface Normal (N)  : ({aim_hit.normal.x:+.2f}, {aim_hit.normal.y:+.2f}, {aim_hit.normal.z:+.2f})", panel_x + 12, y, 10, Color(170, 200, 235, 255)); y += lh
    else:
        draw_text("Target Under Aim    : None (Open Backstop Range)", panel_x + 12, y, 10, Color(150, 165, 185, 255)); y += lh
        draw_text("Distance to Target  : > 160.0 meters", panel_x + 12, y, 10, Color(150, 165, 185, 255)); y += lh
        y += lh

    draw_line(panel_x + 10, y + 2, panel_x + panel_w - 10, y + 2, Color(40, 65, 105, 200)); y += 8

    # 3. Moving Target Lead Math Inspector
    draw_text("TARGET LEADING VECTOR MATH:", panel_x + 12, y, 11, Color(245, 210, 80, 255)); y += lh
    move_status = "ON [Rails Moving]" if movement_enabled else "OFF [Stationary]"
    draw_text(f"[F2] Target Rails   : {move_status}", panel_x + 12, y, 10, Color(200, 220, 245, 255)); y += lh

    if active_target is not None:
        tgt_speed = abs(active_target.vel.x)
        draw_text(f"Sample Target       : {active_target.name} (v = {tgt_speed:.1f} m/s)", panel_x + 12, y, 10, Color(180, 210, 245, 255)); y += lh
        d = math.sqrt((active_target.pos.x - player_pos.x)**2 + (active_target.pos.z - player_pos.z)**2)
        if weapon.mode == MODE_HITSCAN:
            draw_text(f"Hitscan Lead Offset : dx = 0.00m (t = 0.00s)", panel_x + 12, y, 10, Color(0, 240, 255, 255)); y += lh
            draw_text("--> Crosshair directly on target GUARANTEES hit", panel_x + 14, y, 9, Color(160, 220, 255, 220)); y += lh
        else:
            t_fly = d / weapon.projectile_speed
            lead_offset = tgt_speed * t_fly
            lead_col = Color(255, 130, 80, 255)
            draw_text(f"Projectile Lead Off : dx = v_tgt * t = {lead_offset:.2f} meters", panel_x + 12, y, 10, lead_col); y += lh
            draw_text(f"Flight Time at {int(d)}m   : t = {t_fly:.2f}s (Aim ahead!)", panel_x + 14, y, 9, Color(255, 215, 120, 220)); y += lh
    else:
        y += lh * 2

    draw_line(panel_x + 10, y + 2, panel_x + panel_w - 10, y + 2, Color(40, 65, 105, 200)); y += 8

    # 4. Shooting Performance & Object Pool
    draw_text("SESSION METRICS & RESOURCE POOLS:", panel_x + 12, y, 11, Color(245, 210, 80, 255)); y += lh
    acc = (weapon.hits_registered / max(1, weapon.shots_fired)) * 100.0
    draw_text(f"Shots: {weapon.shots_fired} | Hits: {weapon.hits_registered} | Bullseyes: {weapon.bullseyes} | Acc: {acc:.1f}%",
              panel_x + 12, y, 10, Color(200, 225, 255, 255)); y += lh
    draw_text(f"Score: {weapon.total_score} pts | Last Hit: {weapon.last_hit_name} (+{weapon.last_hit_score})",
              panel_x + 12, y, 10, Color(255, 215, 0, 255)); y += lh

    active_p = sum(1 for p in weapon.projectiles if p.active)
    active_t = sum(1 for t in weapon.tracers if t.active)
    active_s = sum(1 for s in weapon.sparks if s.active)
    draw_text(f"Pool Usage          : {active_p} Bullets | {active_t} Tracers | {active_s} Sparks",
              panel_x + 12, y, 10, Color(160, 185, 215, 255)); y += lh


def draw_tactical_reticle(screen_w: int, screen_h: int, aim_hit: RayHit,
                          recoil_kick: float, hitmarker_timer: float, weapon_mode: int):
    """Renders dynamic crosshair with hitmarker notifications and range readout."""
    cx = screen_w // 2
    cy = screen_h // 2

    # Spread expands on recoil kick
    spread = int(10 + recoil_kick * 18.0)
    line_len = 8

    # Reticle color depends on target under aim
    if aim_hit.hit and aim_hit.target_id > 0:
        ret_col = Color(255, 70, 70, 255)
    elif weapon_mode == MODE_HITSCAN:
        ret_col = Color(0, 240, 255, 220)
    else:
        ret_col = Color(255, 175, 50, 220)

    # 4 Reticle Ticks
    draw_line(cx - spread - line_len, cy, cx - spread, cy, ret_col)
    draw_line(cx + spread, cy, cx + spread + line_len, cy, ret_col)
    draw_line(cx, cy - spread - line_len, cx, cy - spread, ret_col)
    draw_line(cx, cy + spread, cx, cy + spread + line_len, ret_col)
    draw_circle(cx, cy, 1.5, ret_col)

    # Hitmarker (Red X on successful hit)
    if hitmarker_timer > 0.0:
        hm_alpha = max(0, min(255, int(255.0 * (hitmarker_timer / 0.28))))
        hm_col = Color(255, 220, 40, hm_alpha)
        hm_size = 9
        draw_line(cx - hm_size, cy - hm_size, cx - 3, cy - 3, hm_col)
        draw_line(cx + 3, cy + 3, cx + hm_size, cy + hm_size, hm_col)
        draw_line(cx + hm_size, cy - hm_size, cx + 3, cy - 3, hm_col)
        draw_line(cx - hm_size, cy + hm_size, cx - 3, cy + 3, hm_col)

    # Rangefinder HUD text below crosshair
    if aim_hit.hit:
        dist_str = f"{aim_hit.distance:.1f}m"
        draw_text(dist_str, cx - 18, cy + spread + 14, 11, Color(220, 235, 255, 220))


# ==============================================================================
# BLOCK 4: MAIN GAME LOOP & AUTOMATED SMOKE TEST
# ==============================================================================

class HitscanRangeLab:
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()

        self.sfx = SoundLibrary()
        self.sfx.init_defaults()

        self.show_xray = True
        self.target_movement = True
        self.mouse_locked = False

        # Weapon Rig
        self.weapon = WeaponRig()

        # Camera & First-Person Controller
        self.player_pos = Vector3(0.0, 1.7, 0.0)
        self.cam_yaw = 0.0    # Radians (0 looking down +Z towards range)
        self.cam_pitch = 0.0  # Radians (-up / +down)

        self.camera = Camera3D()
        self.camera.position = Vector3(self.player_pos.x, self.player_pos.y, self.player_pos.z)
        self.camera.target = Vector3(0.0, 1.7, 50.0)
        self.camera.up = Vector3(0.0, 1.0, 0.0)
        self.camera.fovy = 65.0
        self.camera.projection = CAMERA_PERSPECTIVE

        # Setup Firing Range Targets
        self.targets = []
        self._init_targets()

        # Setup Cover Obstacle Barricades
        self.obstacles = []
        self._init_obstacles()

    def _init_targets(self):
        # 1. Close-Range Stationary Bullseyes
        self.targets.append(Target3D(1, "Target 15m (Close)", TARGET_TYPE_BULLSEYE, Vector3(-5.0, 1.7, 15.0), radius=0.75))
        self.targets.append(Target3D(2, "Target 30m (Mid)", TARGET_TYPE_BULLSEYE, Vector3(5.0, 1.7, 30.0), radius=0.85))

        # 2. Moving Rail Targets (Horizontal track across range)
        self.targets.append(Target3D(3, "Rail Slider 45m", TARGET_TYPE_RAIL,
                                     Vector3(0.0, 2.2, 45.0), radius=0.85,
                                     rail_min_x=-10.0, rail_max_x=10.0, speed=4.5))

        self.targets.append(Target3D(4, "Fast Rail 70m", TARGET_TYPE_RAIL,
                                     Vector3(0.0, 2.8, 70.0), radius=0.95,
                                     rail_min_x=-14.0, rail_max_x=14.0, speed=8.0))

        # 3. Long-Range Target & Flying Drone Sentinel
        self.targets.append(Target3D(5, "Bullseye 100m (Sniper)", TARGET_TYPE_BULLSEYE, Vector3(0.0, 3.2, 100.0), radius=1.1))
        self.targets.append(Target3D(6, "Flying Drone Sentinel 85m", TARGET_TYPE_DRONE,
                                     Vector3(0.0, 5.0, 85.0), radius=1.0,
                                     rail_min_x=-16.0, rail_max_x=16.0, speed=6.0))

    def _init_obstacles(self):
        # Concrete / Steel protective barrier plates
        self.obstacles.append(Obstacle3D(Vector3(-7.5, 0.0, 22.0), Vector3(-3.5, 3.0, 22.8), "Steel Barricade Left"))
        self.obstacles.append(Obstacle3D(Vector3(3.5, 0.0, 38.0), Vector3(7.5, 3.2, 38.8), "Cover Pillar Right"))

    def handle_input(self, dt: float):
        # Pattern & X-Ray Toggles
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
            self.sfx.play("click", 0.6)

        if is_dual_pattern_toggle_pressed():
            self.weapon.mode = MODE_PROJECTILE if self.weapon.mode == MODE_HITSCAN else MODE_HITSCAN
            self.sfx.play("coin" if self.weapon.mode == MODE_HITSCAN else "powerup", 0.7)

        if is_dual_secondary_toggle_pressed():
            self.target_movement = not self.target_movement
            self.sfx.play("click", 0.6)

        # Velocity preset tuning in projectile mode
        if is_key_pressed(KEY_ONE):
            self.weapon.projectile_speed = 25.0
            self.sfx.play("click", 0.5)
        elif is_key_pressed(KEY_TWO):
            self.weapon.projectile_speed = 50.0
            self.sfx.play("click", 0.5)
        elif is_key_pressed(KEY_THREE):
            self.weapon.projectile_speed = 100.0
            self.sfx.play("click", 0.5)

        # Mouse Lock Toggle (Right Click or C)
        if is_mouse_button_pressed(MOUSE_BUTTON_RIGHT) or is_key_pressed(KEY_C):
            self.mouse_locked = not self.mouse_locked
            if self.mouse_locked:
                disable_cursor()
            else:
                enable_cursor()

        # Reset Simulation & Stats
        if is_dual_reset_pressed():
            self.weapon.shots_fired = 0
            self.weapon.hits_registered = 0
            self.weapon.bullseyes = 0
            self.weapon.total_score = 0
            for t in self.targets:
                t.active = True
                t.hp = t.max_hp
                t.knockdown_angle = 0.0
            self.sfx.play("powerup", 0.7)

        # Camera Look (Mouse Delta + Gamepad Right Stick)
        mouse_pos = get_mouse_position()
        in_hud_safe_zone = (mouse_pos.y > 52) or self.mouse_locked

        if in_hud_safe_zone:
            m_delta = get_mouse_delta()
            sens = 0.0024
            self.cam_yaw -= m_delta.x * sens
            self.cam_pitch = max(-1.25, min(1.25, self.cam_pitch + m_delta.y * sens))

        look_analog = get_dual_look_2d(deadzone=0.18, use_arrow_keys=True)
        stick_sens = 2.4
        self.cam_yaw -= look_analog.x * stick_sens * dt
        self.cam_pitch = max(-1.25, min(1.25, self.cam_pitch + look_analog.y * stick_sens * dt))

        # Player Movement (WASD + Gamepad Left Stick)
        move_input = get_dual_move_2d(deadzone=0.18, use_arrow_keys=False)
        f_x = math.sin(self.cam_yaw)
        f_z = math.cos(self.cam_yaw)
        r_x = f_z
        r_z = -f_x

        speed = 5.0
        move_x = (r_x * move_input.x + f_x * (-move_input.y)) * speed * dt
        move_z = (r_z * move_input.x + f_z * (-move_input.y)) * speed * dt

        self.player_pos.x -= move_x
        self.player_pos.z += move_z

        # Clamp inside shooting booth platform
        self.player_pos.x = max(-6.0, min(6.0, self.player_pos.x))
        self.player_pos.z = max(-2.5, min(2.5, self.player_pos.z))

    def fire_weapon(self, ray: Ray3D):
        """Fires weapon according to active pattern (Hitscan vs Travel Projectile)."""
        self.weapon.shots_fired += 1
        self.weapon.fire_cooldown = self.weapon.fire_rate
        self.weapon.recoil_kick = 1.0

        # Muzzle position slightly offset right and down from eye
        muzzle = Vector3(
            self.player_pos.x + math.cos(self.cam_yaw) * 0.28,
            self.player_pos.y - 0.22,
            self.player_pos.z - math.sin(self.cam_yaw) * 0.28
        )

        if self.weapon.mode == MODE_HITSCAN:
            # =================================================================
            # PATTERN 1: HITSCAN (INSTANT RAYCAST)
            # =================================================================
            self.sfx.play("laser", 0.8)
            hit = raycast_world(ray, self.targets, self.obstacles)

            if hit.hit:
                # Instant tracer connecting muzzle to exact hit point
                self.weapon.spawn_tracer(muzzle, hit.point, Color(0, 240, 255, 255))
                self.weapon.spawn_spark_burst(hit.point, hit.normal, 18, Color(0, 240, 255, 255))
                self._register_hit(hit)
            else:
                # Ray misses into the distant sky/backstop
                far_pt = Vector3(
                    ray.origin.x + ray.dir.x * 140.0,
                    ray.origin.y + ray.dir.y * 140.0,
                    ray.origin.z + ray.dir.z * 140.0
                )
                self.weapon.spawn_tracer(muzzle, far_pt, Color(0, 180, 255, 180))

        else:
            # =================================================================
            # PATTERN 2: TRAVEL PROJECTILE (SIMULATED VELOCITY)
            # =================================================================
            self.sfx.play("jump", 0.65)
            self.weapon.spawn_projectile(muzzle, ray.dir)

    def _register_hit(self, hit: RayHit):
        """Processes hit registration, scores, sounds, and knockdown animations."""
        self.weapon.hits_registered += 1
        self.weapon.hitmarker_timer = 0.28
        self.weapon.last_hit_name = hit.target_name
        self.weapon.last_hit_distance = hit.distance
        self.weapon.last_hit_score = hit.score_value
        self.weapon.total_score += hit.score_value

        if hit.is_bullseye:
            self.weapon.bullseyes += 1
            self.sfx.play("coin", 0.85)
        else:
            self.sfx.play("hit", 0.75)

        for t in self.targets:
            if t.id == hit.target_id:
                t.trigger_hit(hit.is_bullseye)
                break
        for obs in self.obstacles:
            if obs.label == hit.target_name:
                obs.flash_timer = 1.0
                break

    def update(self):
        dt = min(get_frame_time(), 0.05)

        self.handle_input(dt)
        self.weapon.update(dt)

        # Update Targets
        for t in self.targets:
            t.update(dt, self.target_movement)
        for obs in self.obstacles:
            obs.update(dt)

        # Compute Forward Look Direction
        cos_p = math.cos(self.cam_pitch)
        sin_p = math.sin(self.cam_pitch)
        sin_y = math.sin(self.cam_yaw)
        cos_y = math.cos(self.cam_yaw)

        cam_fwd = Vector3(sin_y * cos_p, -sin_p, cos_y * cos_p)

        # Update 3D Camera Rig
        self.camera.position.x = self.player_pos.x
        self.camera.position.y = self.player_pos.y
        self.camera.position.z = self.player_pos.z

        self.camera.target.x = self.player_pos.x + cam_fwd.x * 20.0
        self.camera.target.y = self.player_pos.y + cam_fwd.y * 20.0
        self.camera.target.z = self.player_pos.z + cam_fwd.z * 20.0

        aim_ray = Ray3D(self.player_pos, cam_fwd)
        self.current_aim_hit = raycast_world(aim_ray, self.targets, self.obstacles)

        # Fire Weapon Trigger (Left Click / Gamepad RT)
        if is_dual_primary_fire_down() and self.weapon.fire_cooldown <= 0.0:
            self.fire_weapon(aim_ray)

        # Update Projectiles with Swept Continuous Collision Detection (CCD)
        for p in self.weapon.projectiles:
            if not p.active:
                continue

            p.prev_pos.x = p.pos.x
            p.prev_pos.y = p.pos.y
            p.prev_pos.z = p.pos.z

            step_x = p.vel.x * dt
            step_y = p.vel.y * dt
            step_z = p.vel.z * dt
            step_dist = math.sqrt(step_x * step_x + step_y * step_y + step_z * step_z)

            p.pos.x += step_x
            p.pos.y += step_y
            p.pos.z += step_z
            p.travel_distance += step_dist
            p.lifetime -= dt

            # Swept CCD Raycast along trajectory segment
            if step_dist > 0.0001:
                sweep_dir = Vector3(step_x / step_dist, step_y / step_dist, step_z / step_dist)
                sweep_ray = Ray3D(p.prev_pos, sweep_dir)
                hit = raycast_world(sweep_ray, self.targets, self.obstacles, max_dist=step_dist)

                if hit.hit:
                    p.active = False
                    self.weapon.spawn_spark_burst(hit.point, hit.normal, 20, Color(255, 180, 50, 255))
                    self._register_hit(hit)
                    continue

            if p.lifetime <= 0.0 or p.pos.y < 0.0 or p.pos.z > 140.0:
                p.active = False

    def draw_3d_environment(self):
        """Renders firing range architecture, floor distance lines, targets and obstacles."""
        # Ground Range Floor
        draw_cube(Vector3(0.0, -0.2, 60.0), 40.0, 0.4, 130.0, Color(20, 24, 34, 255))
        draw_cube_wires(Vector3(0.0, -0.2, 60.0), 40.0, 0.4, 130.0, Color(40, 50, 72, 255))

        # Shooting platform floor
        draw_cube(Vector3(0.0, 0.0, 0.0), 16.0, 0.2, 8.0, Color(32, 42, 60, 255))
        draw_cube_wires(Vector3(0.0, 0.0, 0.0), 16.0, 0.2, 8.0, Color(60, 85, 125, 255))

        # Distance Yardage Marker Stripes on range floor
        distances = [15, 30, 45, 70, 85, 100]
        for dist_m in distances:
            col = Color(80, 140, 220, 160) if dist_m != 100 else Color(255, 200, 50, 200)
            draw_cube(Vector3(0.0, 0.02, float(dist_m)), 32.0, 0.04, 0.6, col)

        # Distant Backstop Wall at 120m
        draw_cube(Vector3(0.0, 10.0, 120.0), 44.0, 20.0, 2.0, Color(25, 30, 42, 255))
        draw_cube_wires(Vector3(0.0, 10.0, 120.0), 44.0, 20.0, 2.0, Color(55, 75, 105, 255))

        # Side Enclosure Barriers
        draw_cube(Vector3(-18.0, 4.0, 60.0), 1.0, 8.0, 120.0, Color(16, 20, 30, 255))
        draw_cube(Vector3(18.0, 4.0, 60.0), 1.0, 8.0, 120.0, Color(16, 20, 30, 255))

        # 1. Draw Obstacle Barricades
        for obs in self.obstacles:
            cx = (obs.min_pos.x + obs.max_pos.x) * 0.5
            cy = (obs.min_pos.y + obs.max_pos.y) * 0.5
            cz = (obs.min_pos.z + obs.max_pos.z) * 0.5
            sx = obs.max_pos.x - obs.min_pos.x
            sy = obs.max_pos.y - obs.min_pos.y
            sz = obs.max_pos.z - obs.min_pos.z

            base_col = Color(55, 65, 80, 255)
            if obs.flash_timer > 0.0:
                base_col = Color(220, 240, 255, 255)
            draw_cube(Vector3(cx, cy, cz), sx, sy, sz, base_col)
            draw_cube_wires(Vector3(cx, cy, cz), sx, sy, sz, Color(90, 120, 160, 255))

        # 2. Draw Targets
        for t in self.targets:
            if not t.active:
                continue

            # Draw elevated rail beams
            if t.type == TARGET_TYPE_RAIL:
                rail_len = t.rail_max_x - t.rail_min_x
                rail_cx = (t.rail_min_x + t.rail_max_x) * 0.5
                draw_cube(Vector3(rail_cx, t.base_pos.y - 0.4, t.pos.z), rail_len + 1.0, 0.15, 0.3, Color(70, 80, 95, 255))
                # Support legs
                draw_cube(Vector3(t.rail_min_x, (t.base_pos.y - 0.4) * 0.5, t.pos.z), 0.3, t.base_pos.y, 0.3, Color(50, 60, 75, 255))
                draw_cube(Vector3(t.rail_max_x, (t.base_pos.y - 0.4) * 0.5, t.pos.z), 0.3, t.base_pos.y, 0.3, Color(50, 60, 75, 255))

            if t.type == TARGET_TYPE_DRONE:
                # Use articulated 3D Drone from assets/models_3d/drone.py!
                draw_drone_enemy_3d(t.pos, rotation_y=180.0, anim_timer=t.anim_timer, scale=1.4)
            else:
                # Support post for ground bullseyes
                post_h = t.pos.y
                draw_cylinder(Vector3(t.pos.x, post_h * 0.5, t.pos.z), 0.1, 0.1, post_h, 8, Color(80, 90, 105, 255))

                # Spring-loaded hinged target plate
                rl_push_matrix()
                rl_translatef(t.pos.x, t.pos.y, t.pos.z)
                rl_rotatef(t.knockdown_angle, 1.0, 0.0, 0.0)

                # Outer Target Ring (White/Alloy)
                outer_col = Color(230, 235, 245, 255)
                if t.flash_timer > 0.0:
                    outer_col = Color(0, 240, 255, 255)
                draw_cylinder(Vector3(0.0, 0.0, 0.0), t.radius, t.radius, 0.12, 20, outer_col)

                # Middle Ring (Radiant Red)
                draw_cylinder(Vector3(0.0, 0.0, 0.01), t.radius * 0.65, t.radius * 0.65, 0.13, 18, Color(235, 50, 50, 255))

                # Center Bullseye (Gold / Neon Cyan)
                draw_cylinder(Vector3(0.0, 0.0, 0.02), t.radius * 0.32, t.radius * 0.32, 0.14, 16, Color(255, 215, 0, 255))
                rl_pop_matrix()

        # 3. Draw Active Projectiles
        for p in self.weapon.projectiles:
            if p.active:
                draw_sphere(p.pos, p.radius, Color(255, 180, 40, 255))
                # Projectile motion tail segment
                draw_line_3d(p.prev_pos, p.pos, Color(255, 240, 100, 255))

        # 4. Draw Active Tracer Beams
        for tr in self.weapon.tracers:
            if tr.active:
                alpha = max(0, min(255, int(255.0 * (tr.life / tr.max_life))))
                t_col = Color(tr.color.r, tr.color.g, tr.color.b, alpha)
                draw_line_3d(tr.start_pos, tr.end_pos, t_col)

        # 5. Draw 3D Spark Particles
        for s in self.weapon.sparks:
            if s.active:
                draw_cube(s.pos, s.size, s.size, s.size, s.color)

        # 6. X-Ray 3D Visualizations
        if self.show_xray:
            for t in self.targets:
                if not t.active:
                    continue
                wire_col = Color(0, 255, 140, 160)
                if self.current_aim_hit.hit and self.current_aim_hit.target_id == t.id:
                    wire_col = Color(255, 50, 50, 220)
                draw_sphere_wires(t.pos, t.radius, 10, 10, wire_col)

                # In Projectile mode: render Holographic Predicted Lead Intercept Marker!
                if self.weapon.mode == MODE_PROJECTILE and self.target_movement and abs(t.vel.x) > 0.1:
                    lead_pt = compute_lead_intercept(t.pos, t.vel, self.player_pos, self.weapon.projectile_speed)
                    draw_sphere_wires(lead_pt, 0.45, 8, 8, Color(255, 215, 0, 220))
                    draw_line_3d(t.pos, lead_pt, Color(255, 215, 0, 160))

    def draw_hud(self):
        """Renders 2D top banner, reticle, and educational information."""
        # Top-Left Pattern Banner
        banner_x = 24
        banner_y = 16
        draw_rectangle(banner_x, banner_y, 400, 40, Color(14, 18, 30, 230))
        draw_rectangle_lines(banner_x, banner_y, 400, 40, Color(45, 65, 105, 255))

        if self.weapon.mode == MODE_HITSCAN:
            draw_text("PATTERN: HITSCAN (INSTANT RAYCAST)", banner_x + 12, banner_y + 6, 12, Color(0, 240, 255, 255))
            draw_text("v = Infinity | Travel Time: 0.00ms | Zero Lead Aiming Required", banner_x + 12, banner_y + 22, 10, Color(180, 215, 245, 255))
        else:
            spd = int(self.weapon.projectile_speed)
            draw_text("PATTERN: TRAVEL PROJECTILE (SIMULATED VELOCITY)", banner_x + 12, banner_y + 6, 12, Color(255, 160, 40, 255))
            draw_text(f"v = {spd} m/s | Travel Time: d/v | Aim Ahead with Lead Intercept!", banner_x + 12, banner_y + 22, 10, Color(255, 215, 140, 255))

        # Bottom-Right Control Quick-Reference
        ctl_w = 340
        ctl_h = 105
        ctl_x = SCREEN_WIDTH - ctl_w - 24
        ctl_y = SCREEN_HEIGHT - ctl_h - 18
        draw_rectangle(ctl_x, ctl_y, ctl_w, ctl_h, Color(12, 16, 26, 225))
        draw_rectangle_lines(ctl_x, ctl_y, ctl_w, ctl_h, Color(45, 65, 100, 255))

        cy = ctl_y + 8
        draw_text("INTERACTIVE LAB CONTROLS:", ctl_x + 10, cy, 11, Color(0, 220, 255, 255)); cy += 16
        draw_text("[F1] / Gamepad LB : Toggle Hitscan vs Travel Projectile", ctl_x + 10, cy, 10, Color(200, 220, 245, 255)); cy += 14
        draw_text("[F2] / Gamepad RB : Toggle Target Movement (Rails)", ctl_x + 10, cy, 10, Color(200, 220, 245, 255)); cy += 14
        draw_text("[1] / [2] / [3]   : Projectile Speed (25 / 50 / 100 m/s)", ctl_x + 10, cy, 10, Color(200, 220, 245, 255)); cy += 14
        draw_text("[Tab] / Pad Select: Toggle X-Ray Telemetry Overlay", ctl_x + 10, cy, 10, Color(200, 220, 245, 255)); cy += 14
        draw_text("Right Click / [C] : Toggle FPS Mouse Free-Look Lock", ctl_x + 10, cy, 10, Color(255, 215, 0, 255))

        # Tactical Reticle
        draw_tactical_reticle(SCREEN_WIDTH, SCREEN_HEIGHT, self.current_aim_hit,
                              self.weapon.recoil_kick, self.weapon.hitmarker_timer, self.weapon.mode)

        # X-Ray Overlay Panel
        if self.show_xray:
            active_rail_target = self.targets[2] if len(self.targets) > 2 else None
            cos_p = math.cos(self.cam_pitch)
            sin_p = math.sin(self.cam_pitch)
            cam_fwd = Vector3(math.sin(self.cam_yaw) * cos_p, -sin_p, math.cos(self.cam_yaw) * cos_p)
            draw_xray_hud(self.weapon, self.player_pos, cam_fwd,
                          self.current_aim_hit, active_rail_target, self.target_movement)

    def draw(self):
        begin_drawing()
        clear_background(Color(12, 14, 22, 255))

        # 1. 3D World Rendering
        begin_mode_3d(self.camera)
        self.draw_3d_environment()
        end_mode_3d()

        # 2. 2D HUD & Overlay Rendering
        self.draw_hud()

        # Mandatory Global Badges & Top-Bar Settings
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

        if self.mouse_locked:
            enable_cursor()
        self.sfx.unload_all()
        close_audio_device()
        close_window()


if __name__ == "__main__":
    is_smoke = "--smoke-test" in sys.argv
    HitscanRangeLab().run(smoke_test=is_smoke)

