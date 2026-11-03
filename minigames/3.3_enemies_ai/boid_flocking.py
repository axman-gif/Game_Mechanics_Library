# -*- coding: utf-8 -*-
"""
Boid Flocking & Predator Panic - Reynolds Steering Behaviors & Panic State
==========================================================================
Section          : 3.3 Enemies & AI
Pattern Category : Enemies & Autonomous AI (Flocking & Steering)
Dimension        : 2D

Problem Solved:
  In games featuring swarms, herds, bird flocks, or schools of fish, independent entity movement
  either causes entities to overlap and clip unnaturally, scatter into chaotic noise, or move in
  rigid, robotic lockstep formations. Without localized flocking rules, agents cannot self-organize
  into organic, fluid groups, nor can they dynamically adapt, split, and evade when an apex predator
  invades their territory. Furthermore, naive pairwise distance checking across hundreds of agents
  scales at O(N^2), causing extreme frame-rate degradation without spatial partitioning.

How the Pattern Works:
  1. Craig Reynolds' Three Foundational Flocking Rules (1987):
     - Separation: Steer to avoid crowding local flockmates within a tight inner radius.
         F_sep = sum((p_i - p_j) / dist_ij^2) for all neighbors within r_separation
     - Alignment: Steer towards the average velocity/heading of neighbors within perception range.
         F_ali = normalize(sum(v_j) / N) * max_speed - v_i
     - Cohesion: Steer towards the average position (center of mass) of local flockmates.
         F_coh = seek(sum(p_j) / N) - v_i
  2. Spatial Partitioning Acceleration:
     Instead of evaluating all pairs (200 boids = 40,000 distance checks per frame), entities register
     into a 2D Spatial Hash Grid (`SpatialGrid2D` from `utils`). Each boid queries only its immediate
     grid buckets, reducing distance checks from O(N^2) to O(N) average and sustaining 60+ FPS.
  3. Apex Predator Panic & Dynamic Swarm Splitting:
     When an active predator approaches within the Panic Radius (r_panic):
     - The boid enters STATE_PANIC: Cohesion weight drops to zero (breaking swarm lock).
     - Maximum steering force and top speed double for emergency evasion bursts.
     - A dominant flee force pushes radially away from the predator.
     - Separation weight increases so the fleeing swarm dynamically bifurcates around the threat,
       streaming into distinct evasion sub-swarms before reforming once the threat recedes.
  4. Obstacle Avoidance & Soft Boundary Steering:
     Circular monoliths and boundaries exert smooth repulsive lateral forces, allowing boids
     to glide naturally around coral formations and retain momentum.
  5. Global Flocking Order Parameter / Polarization Metric:
     Phi = (1 / N) * || sum(v_i / ||v_i||) ||
     Measures synchronized schooling order from 0.0 (turbulent random chaos) to 1.0 (perfect swarm unison).

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - Predator Movement / Aim       : WASD / Left Stick / D-Pad OR Mouse / Right Stick
  - Predator Lunge / Sprint Boost : Space / Left Click / RT / Gamepad A
  - Toggle Predator Auto-Hunt     : P / Gamepad B (switches between Player Control and AI Hunting Instinct)
  - Spawn Boid Pulse / Scatter    : E / Gamepad X (scatters boids outward from predator/cursor)
  - Parameter Selection           : Up / Down OR Gamepad D-Pad Up / Down
  - Parameter Value Tune          : Left / Right OR Gamepad D-Pad Left / Right
  - Cycle Flocking Modes          : [F1] / Gamepad LB (Full Flocking -> Separation -> Alignment -> Cohesion -> Panic)
  - Select Specific Mode Hotkeys  : [1] Full Flocking, [2] Separation Only, [3] Alignment Only,
                                    [4] Cohesion Only, [5] Panic Only, [6] Steering OFF
  - [Tab] / Gamepad Y (Select)    : Toggle X-Ray Telemetry Overlay (Force Vectors, Spatial Grid, Polarization Meter)
  - [Ctrl +/-]                    : Increase / Decrease UI Font Size
  - [F11]                         : Toggle Fullscreen
  - [R]   / Gamepad Start         : Reset Simulation (respawn boids, restore default weights)
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
WINDOW_TITLE = "Boid Flocking & Predator Panic - Reynolds Steering Behaviors (Raylib)"

# Reserve Boundaries
RESERVE_MIN_X = 28.0
RESERVE_MAX_X = 1252.0
RESERVE_MIN_Y = 58.0
RESERVE_MAX_Y = 692.0

# Flocking Rule Mode Constants (C++: enum class FlockingMode : uint8_t)
MODE_FULL_FLOCKING = 0
MODE_SEPARATION_ONLY = 1
MODE_ALIGNMENT_ONLY = 2
MODE_COHESION_ONLY = 3
MODE_PREDATOR_PANIC_ONLY = 4
MODE_STEERING_OFF = 5

MODE_NAMES = [
    "Full Flocking (All Rules)",
    "Separation Only (Dispersal)",
    "Alignment Only (Parallel Drift)",
    "Cohesion Only (Clumping Knot)",
    "Predator Panic Only (Pure Evasion)",
    "Steering Disabled (Inertial Drift)"
]

# Boid State Constants (C++: enum class BoidState : uint8_t)
STATE_CALM = 0
STATE_PANIC = 1
STATE_SCATTER = 2


# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATION
# ==============================================================================

class SteeringForces:
    """
    Data structure holding the individual and resultant steering force vectors
    computed during each boid's Reynolds evaluation step.
    
    C++ Equivalent:
      struct SteeringForces {
          Vector2 separation;
          Vector2 alignment;
          Vector2 cohesion;
          Vector2 obstacle_avoidance;
          Vector2 predator_flee;
          Vector2 boundary_steering;
          Vector2 net_steering;
      };
    """
    def __init__(self):
        self.reset()

    def reset(self):
        self.sep_x = 0.0
        self.sep_y = 0.0
        self.ali_x = 0.0
        self.ali_y = 0.0
        self.coh_x = 0.0
        self.coh_y = 0.0
        self.obs_x = 0.0
        self.obs_y = 0.0
        self.flee_x = 0.0
        self.flee_y = 0.0
        self.bound_x = 0.0
        self.bound_y = 0.0
        self.net_x = 0.0
        self.net_y = 0.0


class BoidParameters:
    """
    Interactive simulation parameters tuning Craig Reynolds' force weights,
    perception radii, and speed thresholds.
    
    C++ Equivalent:
      struct BoidParameters {
          float weight_separation;
          float weight_alignment;
          float weight_cohesion;
          float weight_obstacle;
          float weight_panic;
          float radius_perception;
          float radius_separation;
          float radius_panic;
          float max_speed_calm;
          float max_speed_panic;
          float max_force_calm;
          float max_force_panic;
      };
    """
    def __init__(self):
        self.reset_defaults()

    def reset_defaults(self):
        # Force Weights
        self.weight_separation = 1.6
        self.weight_alignment = 1.1
        self.weight_cohesion = 0.9
        self.weight_obstacle = 2.8
        self.weight_panic = 3.6
        # Sensory Radii (pixels)
        self.radius_perception = 64.0
        self.radius_separation = 26.0
        self.radius_panic = 160.0
        # Kinematic Limits
        self.max_speed_calm = 160.0
        self.max_speed_panic = 270.0
        self.max_force_calm = 240.0
        self.max_force_panic = 560.0


class Boid:
    """
    Autonomous flocking agent swimming in the 2D aquatic reserve.
    Maintains localized position, velocity, heading, and live telemetry vectors.
    
    C++ Equivalent:
      class Boid {
      public:
          int id;
          bool active;
          float x, y;
          float vx, vy;
          float ax, ay;
          uint8_t state;
          float panic_timer;
          float anim_phase;
          int neighbor_count;
          bool is_selected;
          SteeringForces forces;
          float trail_x[6];
          float trail_y[6];
      };
    """
    def __init__(self, boid_id: int, init_x: float, init_y: float):
        self.id = boid_id
        self.active = True
        self.x = float(init_x)
        self.y = float(init_y)

        # Randomized initial heading
        angle = random.uniform(0.0, 2.0 * math.pi)
        speed = random.uniform(80.0, 140.0)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

        # Accumulated frame acceleration
        self.ax = 0.0
        self.ay = 0.0

        self.state = STATE_CALM
        self.panic_timer = 0.0
        self.anim_phase = random.uniform(0.0, 6.28)
        self.neighbor_count = 0
        self.is_selected = False
        self.forces = SteeringForces()

        # Hydrodynamic tail history (fixed pre-allocated array)
        self.trail_x = [self.x] * 6
        self.trail_y = [self.y] * 6
        self.trail_timer = 0.0

    def apply_force(self, fx: float, fy: float):
        """Accumulates an instantaneous steering force vector."""
        self.ax += fx
        self.ay += fy

    def compute_reynolds_steering(
        self,
        neighbors: list,
        obstacles: list,
        predator_x: float,
        predator_y: float,
        predator_active: bool,
        params: BoidParameters,
        mode: int
    ):
        """
        Calculates Craig Reynolds' classical flocking forces (Separation, Alignment, Cohesion),
        obstacle deflection, and apex predator evasion panic.
        Pure O(K) complexity where K is the count of local neighbors within perception.
        """
        self.forces.reset()
        self.neighbor_count = 0

        if mode == MODE_STEERING_OFF:
            return

        # 1. PREDATOR DETECTION & PANIC EVALUATION
        dist_pred = 9999.0
        in_panic_zone = False

        if predator_active:
            pdx = self.x - predator_x
            pdy = self.y - predator_y
            dist_pred = math.sqrt(pdx * pdx + pdy * pdy)

            if dist_pred < params.radius_panic:
                in_panic_zone = True
                self.state = STATE_PANIC
                self.panic_timer = 0.65
            elif self.panic_timer > 0.0:
                self.state = STATE_PANIC
            else:
                self.state = STATE_CALM
        else:
            self.state = STATE_CALM

        # 2. LOCAL NEIGHBOR SCAN (Separation, Alignment, Cohesion Accumulators)
        sep_accum_x = 0.0
        sep_accum_y = 0.0
        sep_count = 0
        ali_accum_x = 0.0
        ali_accum_y = 0.0
        ali_count = 0
        coh_accum_x = 0.0
        coh_accum_y = 0.0
        coh_count = 0

        r_per = params.radius_perception
        r_sep = params.radius_separation
        r_per_sq = r_per * r_per
        r_sep_sq = r_sep * r_sep

        for other in neighbors:
            if other.id == self.id or not other.active:
                continue

            dx = other.x - self.x
            dy = other.y - self.y
            dist_sq = dx * dx + dy * dy

            if dist_sq < 0.0001 or dist_sq > r_per_sq:
                continue

            dist = math.sqrt(dist_sq)
            self.neighbor_count += 1

            # Rule A: Separation (Crowding avoidance within tight inner radius)
            if dist_sq < r_sep_sq:
                sep_accum_x -= (dx / dist) / max(0.1, dist / r_sep)
                sep_accum_y -= (dy / dist) / max(0.1, dist / r_sep)
                sep_count += 1

            # Rule B: Alignment (Match velocity heading of local flock)
            ali_accum_x += other.vx
            ali_accum_y += other.vy
            ali_count += 1

            # Rule C: Cohesion (Steer toward center of mass of local flock)
            coh_accum_x += other.x
            coh_accum_y += other.y
            coh_count += 1

        # Determine current kinematic ceilings based on panic alert
        if self.state == STATE_PANIC:
            cur_max_speed = params.max_speed_panic
            cur_max_force = params.max_force_panic
        else:
            cur_max_speed = params.max_speed_calm
            cur_max_force = params.max_force_calm

        # 3. CONVERT ACCUMULATORS TO REYNOLDS STEERING FORCES (Desired - Current)
        # --- A. Separation Force ---
        if sep_count > 0 and mode in (MODE_FULL_FLOCKING, MODE_SEPARATION_ONLY):
            avg_sep_x = sep_accum_x / float(sep_count)
            avg_sep_y = sep_accum_y / float(sep_count)
            sep_mag = math.sqrt(avg_sep_x * avg_sep_x + avg_sep_y * avg_sep_y)
            if sep_mag > 0.0001:
                des_vx = (avg_sep_x / sep_mag) * cur_max_speed
                des_vy = (avg_sep_y / sep_mag) * cur_max_speed
                steer_x = des_vx - self.vx
                steer_y = des_vy - self.vy
                steer_mag = math.sqrt(steer_x * steer_x + steer_y * steer_y)
                if steer_mag > cur_max_force:
                    steer_x = (steer_x / steer_mag) * cur_max_force
                    steer_y = (steer_y / steer_mag) * cur_max_force
                sep_mult = params.weight_separation * (1.8 if self.state == STATE_PANIC else 1.0)
                self.forces.sep_x = steer_x * sep_mult
                self.forces.sep_y = steer_y * sep_mult

        # --- B. Alignment Force ---
        if ali_count > 0 and mode in (MODE_FULL_FLOCKING, MODE_ALIGNMENT_ONLY):
            avg_vx = ali_accum_x / float(ali_count)
            avg_vy = ali_accum_y / float(ali_count)
            avg_vmag = math.sqrt(avg_vx * avg_vx + avg_vy * avg_vy)
            if avg_vmag > 0.0001:
                des_vx = (avg_vx / avg_vmag) * cur_max_speed
                des_vy = (avg_vy / avg_vmag) * cur_max_speed
                steer_x = des_vx - self.vx
                steer_y = des_vy - self.vy
                steer_mag = math.sqrt(steer_x * steer_x + steer_y * steer_y)
                if steer_mag > cur_max_force:
                    steer_x = (steer_x / steer_mag) * cur_max_force
                    steer_y = (steer_y / steer_mag) * cur_max_force
                ali_mult = params.weight_alignment * (0.4 if self.state == STATE_PANIC else 1.0)
                self.forces.ali_x = steer_x * ali_mult
                self.forces.ali_y = steer_y * ali_mult

        # --- C. Cohesion Force (Seek center of mass) ---
        if coh_count > 0 and mode in (MODE_FULL_FLOCKING, MODE_COHESION_ONLY):
            if self.state != STATE_PANIC:
                center_x = coh_accum_x / float(coh_count)
                center_y = coh_accum_y / float(coh_count)
                to_center_x = center_x - self.x
                to_center_y = center_y - self.y
                center_dist = math.sqrt(to_center_x * to_center_x + to_center_y * to_center_y)
                if center_dist > 0.0001:
                    des_vx = (to_center_x / center_dist) * cur_max_speed
                    des_vy = (to_center_y / center_dist) * cur_max_speed
                    steer_x = des_vx - self.vx
                    steer_y = des_vy - self.vy
                    steer_mag = math.sqrt(steer_x * steer_x + steer_y * steer_y)
                    if steer_mag > cur_max_force:
                        steer_x = (steer_x / steer_mag) * cur_max_force
                        steer_y = (steer_y / steer_mag) * cur_max_force
                    self.forces.coh_x = steer_x * params.weight_cohesion
                    self.forces.coh_y = steer_y * params.weight_cohesion

        # 4. PREDATOR PANIC FLEE FORCE
        if in_panic_zone and mode in (MODE_FULL_FLOCKING, MODE_PREDATOR_PANIC_ONLY):
            pdx = self.x - predator_x
            pdy = self.y - predator_y
            if dist_pred > 0.0001:
                norm_pdx = pdx / dist_pred
                norm_pdy = pdy / dist_pred
                proximity_factor = max(0.0, min(1.0, 1.0 - (dist_pred / params.radius_panic)))
                panic_speed = cur_max_speed * (1.0 + 0.35 * proximity_factor)
                des_vx = norm_pdx * panic_speed
                des_vy = norm_pdy * panic_speed
                steer_x = des_vx - self.vx
                steer_y = des_vy - self.vy
                steer_mag = math.sqrt(steer_x * steer_x + steer_y * steer_y)
                if steer_mag > cur_max_force:
                    steer_x = (steer_x / steer_mag) * cur_max_force
                    steer_y = (steer_y / steer_mag) * cur_max_force
                flee_weight = params.weight_panic * (1.0 + 0.5 * proximity_factor)
                self.forces.flee_x = steer_x * flee_weight
                self.forces.flee_y = steer_y * flee_weight

        # 5. STATIC OBSTACLE LATERAL AVOIDANCE
        obs_force_x = 0.0
        obs_force_y = 0.0
        for obs in obstacles:
            odx = self.x - obs.x
            ody = self.y - obs.y
            odist = math.sqrt(odx * odx + ody * ody)
            safe_margin = obs.radius + 40.0
            if odist < safe_margin and odist > 0.0001:
                overlap = safe_margin - odist
                push_mag = (overlap / 40.0) * cur_max_force * params.weight_obstacle
                obs_force_x += (odx / odist) * push_mag
                obs_force_y += (ody / odist) * push_mag
        self.forces.obs_x = obs_force_x
        self.forces.obs_y = obs_force_y

        # 6. SOFT BOUNDARY STEERING (Aquatic Reserve Margins)
        pad = 52.0
        bound_fx = 0.0
        bound_fy = 0.0
        if self.x < RESERVE_MIN_X + pad:
            bound_fx += ((RESERVE_MIN_X + pad - self.x) / pad) * cur_max_force * 2.2
        elif self.x > RESERVE_MAX_X - pad:
            bound_fx -= ((self.x - (RESERVE_MAX_X - pad)) / pad) * cur_max_force * 2.2

        if self.y < RESERVE_MIN_Y + pad:
            bound_fy += ((RESERVE_MIN_Y + pad - self.y) / pad) * cur_max_force * 2.2
        elif self.y > RESERVE_MAX_Y - pad:
            bound_fy -= ((self.y - (RESERVE_MAX_Y - pad)) / pad) * cur_max_force * 2.2

        self.forces.bound_x = bound_fx
        self.forces.bound_y = bound_fy

        # 7. SUMMATION & ACCELERATION APPLICATION
        net_x = (
            self.forces.sep_x + self.forces.ali_x + self.forces.coh_x +
            self.forces.flee_x + self.forces.obs_x + self.forces.bound_x
        )
        net_y = (
            self.forces.sep_y + self.forces.ali_y + self.forces.coh_y +
            self.forces.flee_y + self.forces.obs_y + self.forces.bound_y
        )
        net_mag = math.sqrt(net_x * net_x + net_y * net_y)
        if net_mag > cur_max_force:
            net_x = (net_x / net_mag) * cur_max_force
            net_y = (net_y / net_mag) * cur_max_force

        self.forces.net_x = net_x
        self.forces.net_y = net_y
        self.apply_force(net_x, net_y)

    def update_kinematics(self, dt: float, params: BoidParameters):
        """Integrates acceleration into velocity and position using Euler-Cromer integration."""
        self.vx += self.ax * dt
        self.vy += self.ay * dt
        self.ax = 0.0
        self.ay = 0.0

        top_speed = params.max_speed_panic if self.state == STATE_PANIC else params.max_speed_calm
        v_mag = math.sqrt(self.vx * self.vx + self.vy * self.vy)
        min_speed = 45.0
        if v_mag > top_speed:
            self.vx = (self.vx / v_mag) * top_speed
            self.vy = (self.vy / v_mag) * top_speed
        elif v_mag < min_speed and v_mag > 0.0001:
            self.vx = (self.vx / v_mag) * min_speed
            self.vy = (self.vy / v_mag) * min_speed

        self.x += self.vx * dt
        self.y += self.vy * dt

        if self.panic_timer > 0.0:
            self.panic_timer -= dt
            if self.panic_timer <= 0.0:
                self.state = STATE_CALM

        # Boundary clamping
        if self.x < RESERVE_MIN_X:
            self.x = RESERVE_MIN_X
            self.vx = abs(self.vx) * 0.7
        elif self.x > RESERVE_MAX_X:
            self.x = RESERVE_MAX_X
            self.vx = -abs(self.vx) * 0.7

        if self.y < RESERVE_MIN_Y:
            self.y = RESERVE_MIN_Y
            self.vy = abs(self.vy) * 0.7
        elif self.y > RESERVE_MAX_Y:
            self.y = RESERVE_MAX_Y
            self.vy = -abs(self.vy) * 0.7

        # Tail trail update
        self.trail_timer += dt
        if self.trail_timer >= 0.035:
            self.trail_timer = 0.0
            for i in range(len(self.trail_x) - 1, 0, -1):
                self.trail_x[i] = self.trail_x[i - 1]
                self.trail_y[i] = self.trail_y[i - 1]
            self.trail_x[0] = self.x
            self.trail_y[0] = self.y

        wag_rate = 6.0 + (v_mag / top_speed) * 14.0
        self.anim_phase += dt * wag_rate
        if self.anim_phase > 628.0:
            self.anim_phase -= 628.0


# ==============================================================================
# BLOCK 2: WORLD SIMULATION & ENTITIES
# ==============================================================================

class Obstacle:
    """Static environmental monolith / coral reef formation in the aquatic reserve."""
    def __init__(self, x: float, y: float, radius: float, name: str = "Coral Spire"):
        self.x = float(x)
        self.y = float(y)
        self.radius = float(radius)
        self.name = name
        self.color_body = Color(30, 75, 85, 235)
        self.color_rim = Color(65, 160, 175, 255)
        self.color_glow = Color(35, 120, 135, 120)
        self.pulse = random.uniform(0.0, 6.28)

    def update(self, dt: float):
        self.pulse += dt * 1.8
        if self.pulse > 628.0:
            self.pulse -= 628.0

    def draw(self):
        cx = int(self.x)
        cy = int(self.y)
        r = int(self.radius)
        glow_r = int(self.radius + 6.0 + 3.0 * math.sin(self.pulse))
        draw_circle(cx, cy, glow_r, self.color_glow)
        draw_circle(cx, cy, r, self.color_body)
        draw_circle_lines(cx, cy, r, self.color_rim)
        draw_circle_lines(cx, cy, int(self.radius * 0.65), Color(50, 110, 125, 160))
        draw_circle_lines(cx, cy, int(self.radius * 0.35), Color(35, 80, 95, 200))


class ApexPredator:
    """Active apex predator hunting boids in the reserve with dual control & auto AI."""
    def __init__(self, x: float, y: float):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.heading_rad = 0.0
        self.speed_normal = 165.0
        self.speed_boost = 320.0
        self.is_boosting = False
        self.boost_timer = 0.0
        self.boost_cooldown = 0.0
        self.is_auto_hunt = False
        self.eaten_count = 0
        self.hunting_target_x = x
        self.hunting_target_y = y
        self.patrol_angle = 0.0
        self.wake_x = [self.x] * 8
        self.wake_y = [self.y] * 8
        self.wake_timer = 0.0
        self.anim_jaw = 0.0

    def lunge_boost(self):
        """Activates a high-speed lunge sprint if off cooldown."""
        if self.boost_cooldown <= 0.0 and not self.is_boosting:
            self.is_boosting = True
            self.boost_timer = 0.42
            self.boost_cooldown = 1.6
            return True
        return False

    def update_auto_hunt(self, boids: list, spatial_grid: SpatialGrid2D, dt: float):
        """Autonomous hunting: stalks nearest boid cluster or patrols circuit."""
        nearby = spatial_grid.query_radius(self.x, self.y, 280.0)
        target_found = False
        closest_dist = 9999.0
        best_tx = self.x
        best_ty = self.y

        if len(nearby) > 0:
            for boid in nearby:
                if not boid.active:
                    continue
                dx = boid.x - self.x
                dy = boid.y - self.y
                d = math.sqrt(dx * dx + dy * dy)
                if d < closest_dist:
                    closest_dist = d
                    best_tx = boid.x
                    best_ty = boid.y
                    target_found = True

        if target_found:
            self.hunting_target_x = best_tx
            self.hunting_target_y = best_ty
            if closest_dist < 130.0 and self.boost_cooldown <= 0.0:
                self.lunge_boost()
        else:
            self.patrol_angle += dt * 0.9
            cx = (RESERVE_MIN_X + RESERVE_MAX_X) * 0.5
            cy = (RESERVE_MIN_Y + RESERVE_MAX_Y) * 0.5
            self.hunting_target_x = cx + math.cos(self.patrol_angle) * 360.0
            self.hunting_target_y = cy + math.sin(self.patrol_angle * 1.5) * 200.0

        tdx = self.hunting_target_x - self.x
        tdy = self.hunting_target_y - self.y
        tdist = math.sqrt(tdx * tdx + tdy * tdy)

        if tdist > 1.0:
            cur_speed = self.speed_boost if self.is_boosting else self.speed_normal
            des_vx = (tdx / tdist) * cur_speed
            des_vy = (tdy / tdist) * cur_speed
            self.vx += (des_vx - self.vx) * min(1.0, dt * 5.0)
            self.vy += (des_vy - self.vy) * min(1.0, dt * 5.0)

    def update_manual(self, move_dir: Vector2, look_dir: Vector2, mouse_pos: Vector2, dt: float):
        """Player-controlled steering using simultaneous WASD/Stick."""
        cur_speed = self.speed_boost if self.is_boosting else self.speed_normal
        input_mag = math.sqrt(move_dir.x * move_dir.x + move_dir.y * move_dir.y)
        if input_mag > 0.08:
            des_vx = move_dir.x * cur_speed
            des_vy = move_dir.y * cur_speed
            self.vx += (des_vx - self.vx) * min(1.0, dt * 7.5)
            self.vy += (des_vy - self.vy) * min(1.0, dt * 7.5)
        else:
            self.vx *= max(0.0, 1.0 - dt * 3.5)
            self.vy *= max(0.0, 1.0 - dt * 3.5)

    def update_physics(self, dt: float):
        """Advances predator position and updates timers."""
        if self.boost_timer > 0.0:
            self.boost_timer -= dt
            if self.boost_timer <= 0.0:
                self.is_boosting = False
        if self.boost_cooldown > 0.0:
            self.boost_cooldown -= dt

        self.x += self.vx * dt
        self.y += self.vy * dt
        v_mag = math.sqrt(self.vx * self.vx + self.vy * self.vy)
        if v_mag > 12.0:
            self.heading_rad = math.atan2(self.vy, self.vx)

        self.x = max(RESERVE_MIN_X + 15.0, min(RESERVE_MAX_X - 15.0, self.x))
        self.y = max(RESERVE_MIN_Y + 15.0, min(RESERVE_MAX_Y - 15.0, self.y))

        self.wake_timer += dt
        if self.wake_timer >= 0.04:
            self.wake_timer = 0.0
            for i in range(len(self.wake_x) - 1, 0, -1):
                self.wake_x[i] = self.wake_x[i - 1]
                self.wake_y[i] = self.wake_y[i - 1]
            self.wake_x[0] = self.x
            self.wake_y[0] = self.y

        self.anim_jaw += dt * (12.0 if self.is_boosting else 4.0)
        if self.anim_jaw > 628.0:
            self.anim_jaw -= 628.0

    def draw(self, panic_radius: float, show_xray: bool):
        """Renders apex predator shark silhouette with animated fins and jaw."""
        cx = int(self.x)
        cy = int(self.y)
        angle = self.heading_rad

        for i in range(len(self.wake_x) - 1):
            alpha = int(120 * (1.0 - (i / float(len(self.wake_x)))))
            r_wake = int(16 - i * 1.8)
            if r_wake > 2:
                draw_circle(int(self.wake_x[i]), int(self.wake_y[i]), r_wake, Color(220, 60, 50, alpha))

        if show_xray:
            draw_circle_lines(cx, cy, int(panic_radius), Color(255, 60, 80, 110))
            draw_circle_lines(cx, cy, 32, Color(255, 220, 40, 180))

        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        tip_x = self.x + cos_a * 26.0
        tip_y = self.y + sin_a * 26.0
        tail_x = self.x - cos_a * 24.0
        tail_y = self.y - sin_a * 24.0
        left_fin_x = self.x - cos_a * 4.0 - sin_a * 18.0
        left_fin_y = self.y - sin_a * 4.0 + cos_a * 18.0
        right_fin_x = self.x - cos_a * 4.0 + sin_a * 18.0
        right_fin_y = self.y - sin_a * 4.0 - cos_a * 18.0

        body_color = Color(195, 35, 45, 255) if self.is_boosting else Color(155, 30, 40, 255)
        belly_color = Color(240, 75, 75, 255)
        trim_color = Color(255, 180, 80, 255) if self.is_boosting else Color(220, 90, 80, 255)

        draw_triangle(Vector2(float(tip_x), float(tip_y)), Vector2(float(left_fin_x), float(left_fin_y)), Vector2(float(tail_x), float(tail_y)), body_color)
        draw_triangle(Vector2(float(tip_x), float(tip_y)), Vector2(float(tail_x), float(tail_y)), Vector2(float(right_fin_x), float(right_fin_y)), belly_color)

        eye_x = self.x + cos_a * 10.0 - sin_a * 6.0
        eye_y = self.y + sin_a * 10.0 + cos_a * 6.0
        draw_circle(int(eye_x), int(eye_y), 3, Color(255, 235, 40, 255))
        draw_circle(int(eye_x), int(eye_y), 1, Color(10, 10, 10, 255))

        wag = math.sin(self.anim_jaw) * 8.0
        tail_tip_x = tail_x - cos_a * 12.0 - sin_a * wag
        tail_tip_y = tail_y - sin_a * 12.0 + cos_a * wag
        draw_line_ex(Vector2(float(tail_x), float(tail_y)), Vector2(float(tail_tip_x), float(tail_tip_y)), 4.0, trim_color)


class AquaticParticle:
    """Zero-allocation aquatic bubble or dispersion particle."""
    def __init__(self):
        self.active = False
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.radius = 2.0
        self.lifetime = 0.0
        self.max_lifetime = 1.0
        self.color = Color(120, 220, 240, 200)

    def spawn(self, x: float, y: float, vx: float, vy: float, radius: float, duration: float, color: Color):
        self.active = True
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = radius
        self.lifetime = duration
        self.max_lifetime = duration
        self.color = color

    def update(self, dt: float):
        if not self.active:
            return
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy -= 18.0 * dt
        self.lifetime -= dt
        if self.lifetime <= 0.0:
            self.active = False


class FlockingReserveSimulation:
    """Simulation coordinator managing boids, obstacles, predator, spatial grid, and metrics."""
    def __init__(self, boid_count: int = 200):
        self.boids = []
        self.obstacles = []
        self.particles = []
        self.predator = ApexPredator(640.0, 360.0)
        self.spatial_grid = SpatialGrid2D(cell_size=64.0)
        self.params = BoidParameters()
        self.active_mode = MODE_FULL_FLOCKING
        self.selected_boid_id = -1
        self.polarization_order = 0.0
        self.avg_neighbor_count = 0.0
        self.total_eaten = 0

        for _ in range(80):
            self.particles.append(AquaticParticle())

        self.init_obstacles()

        for i in range(boid_count):
            bx = random.uniform(RESERVE_MIN_X + 80.0, RESERVE_MAX_X - 80.0)
            by = random.uniform(RESERVE_MIN_Y + 80.0, RESERVE_MAX_Y - 80.0)
            self.boids.append(Boid(i, bx, by))

        if len(self.boids) > 0:
            self.selected_boid_id = 0
            self.boids[0].is_selected = True

    def init_obstacles(self):
        """Places monolith coral reefs in the reserve."""
        self.obstacles.clear()
        self.obstacles.append(Obstacle(360.0, 240.0, 48.0, "North Reef Monolith"))
        self.obstacles.append(Obstacle(920.0, 260.0, 52.0, "East Coral Spire"))
        self.obstacles.append(Obstacle(440.0, 520.0, 45.0, "South Shallows"))
        self.obstacles.append(Obstacle(840.0, 500.0, 56.0, "Abyssal Pillar"))

    def reset_simulation(self):
        """Resets boid positions, predator state, and default parameters."""
        self.params.reset_defaults()
        for boid in self.boids:
            boid.active = True
            boid.x = random.uniform(RESERVE_MIN_X + 80.0, RESERVE_MAX_X - 80.0)
            boid.y = random.uniform(RESERVE_MIN_Y + 80.0, RESERVE_MAX_Y - 80.0)
            angle = random.uniform(0.0, 6.28)
            spd = random.uniform(90.0, 150.0)
            boid.vx = math.cos(angle) * spd
            boid.vy = math.sin(angle) * spd
            boid.state = STATE_CALM
            boid.panic_timer = 0.0
            boid.forces.reset()

        self.predator.x = 640.0
        self.predator.y = 360.0
        self.predator.vx = 0.0
        self.predator.vy = 0.0
        self.predator.is_boosting = False
        self.predator.eaten_count = 0
        self.total_eaten = 0

    def spawn_bubbles(self, x: float, y: float, count: int = 5, color: Color = None):
        """Emits buoyant underwater bubbles."""
        c = color or Color(140, 230, 255, 180)
        spawned = 0
        for p in self.particles:
            if not p.active:
                ang = random.uniform(0.0, 6.28)
                spd = random.uniform(20.0, 80.0)
                dur = random.uniform(0.4, 0.9)
                rad = random.uniform(1.5, 4.0)
                p.spawn(x, y, math.cos(ang) * spd, math.sin(ang) * spd, rad, dur, c)
                spawned += 1
                if spawned >= count:
                    break

    def trigger_pulse_scatter(self, origin_x: float, origin_y: float, sfx: SoundLibrary):
        """Triggers an acoustic sonic pulse that scatters nearby boids."""
        sfx.play("sonar_ping", 0.7)
        self.spawn_bubbles(origin_x, origin_y, 16, Color(80, 240, 255, 230))
        for boid in self.boids:
            if not boid.active:
                continue
            dx = boid.x - origin_x
            dy = boid.y - origin_y
            d = math.sqrt(dx * dx + dy * dy)
            if d < 220.0 and d > 0.001:
                push = (1.0 - (d / 220.0)) * 520.0
                boid.vx += (dx / d) * push
                boid.vy += (dy / d) * push
                boid.state = STATE_PANIC
                boid.panic_timer = 1.0

    def select_boid_at(self, screen_x: float, screen_y: float):
        """Selects the closest boid to pointer coordinates for telemetry inspection."""
        closest_id = -1
        min_dist = 45.0
        for boid in self.boids:
            if not boid.active:
                continue
            dx = boid.x - screen_x
            dy = boid.y - screen_y
            d = math.sqrt(dx * dx + dy * dy)
            if d < min_dist:
                min_dist = d
                closest_id = boid.id

        if closest_id >= 0:
            for boid in self.boids:
                boid.is_selected = (boid.id == closest_id)
            self.selected_boid_id = closest_id

    def update(self, dt: float, move_dir: Vector2, look_dir: Vector2, mouse_pos: Vector2, sfx: SoundLibrary):
        """Simulation tick: Spatial partitioning, steering forces, predator hunting, and metrics."""
        for obs in self.obstacles:
            obs.update(dt)

        if self.predator.is_auto_hunt:
            self.predator.update_auto_hunt(self.boids, self.spatial_grid, dt)
        else:
            self.predator.update_manual(move_dir, look_dir, mouse_pos, dt)
        self.predator.update_physics(dt)

        # Spatial hash grid reconstruction: O(N)
        self.spatial_grid.clear()
        for boid in self.boids:
            if boid.active:
                self.spatial_grid.insert(boid, boid.x, boid.y, radius=0.0)

        total_neighbors = 0
        active_boid_count = 0
        sum_unit_vx = 0.0
        sum_unit_vy = 0.0

        for boid in self.boids:
            if not boid.active:
                continue
            active_boid_count += 1
            neighbors = self.spatial_grid.query_radius(boid.x, boid.y, self.params.radius_perception)
            total_neighbors += boid.neighbor_count

            boid.compute_reynolds_steering(
                neighbors, self.obstacles, self.predator.x, self.predator.y, True, self.params, self.active_mode
            )
            boid.update_kinematics(dt, self.params)

            v_mag = math.sqrt(boid.vx * boid.vx + boid.vy * boid.vy)
            if v_mag > 0.0001:
                sum_unit_vx += boid.vx / v_mag
                sum_unit_vy += boid.vy / v_mag

            # Predator strike check
            pdx = boid.x - self.predator.x
            pdy = boid.y - self.predator.y
            pdist = math.sqrt(pdx * pdx + pdy * pdy)
            strike_radius = 28.0 if self.predator.is_boosting else 20.0

            if pdist < strike_radius:
                self.spawn_bubbles(boid.x, boid.y, 8, Color(255, 90, 70, 240))
                sfx.play("hit", 0.6)
                self.predator.eaten_count += 1
                self.total_eaten += 1
                spawn_side = random.choice([0, 1, 2, 3])
                if spawn_side == 0:
                    boid.x = RESERVE_MIN_X + 40.0
                    boid.y = random.uniform(RESERVE_MIN_Y + 50.0, RESERVE_MAX_Y - 50.0)
                    boid.vx = 120.0
                elif spawn_side == 1:
                    boid.x = RESERVE_MAX_X - 40.0
                    boid.y = random.uniform(RESERVE_MIN_Y + 50.0, RESERVE_MAX_Y - 50.0)
                    boid.vx = -120.0
                elif spawn_side == 2:
                    boid.x = random.uniform(RESERVE_MIN_X + 50.0, RESERVE_MAX_X - 50.0)
                    boid.y = RESERVE_MIN_Y + 40.0
                    boid.vy = 120.0
                else:
                    boid.x = random.uniform(RESERVE_MIN_X + 50.0, RESERVE_MAX_X - 50.0)
                    boid.y = RESERVE_MAX_Y - 40.0
                    boid.vy = -120.0

        if active_boid_count > 0:
            self.avg_neighbor_count = total_neighbors / float(active_boid_count)
            order_mag = math.sqrt(sum_unit_vx * sum_unit_vx + sum_unit_vy * sum_unit_vy)
            self.polarization_order = order_mag / float(active_boid_count)
        else:
            self.polarization_order = 0.0

        for p in self.particles:
            p.update(dt)


# ==============================================================================
# BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY
# ==============================================================================

class TelemetryOverlay:
    """Renders diagnostic telemetry, spatial hash grid, force vectors, and polarization meter."""
    def __init__(self):
        self.selected_param_idx = 0
        self.param_names = [
            "Separation Weight (W_sep)",
            "Alignment Weight (W_ali)",
            "Cohesion Weight (W_coh)",
            "Perception Radius (R_per)",
            "Panic Distance (R_panic)"
        ]

    def cycle_param_selection(self, delta: int):
        self.selected_param_idx = (self.selected_param_idx + delta) % len(self.param_names)

    def adjust_selected_param(self, sim: FlockingReserveSimulation, delta: float):
        p = sim.params
        idx = self.selected_param_idx
        if idx == 0:
            p.weight_separation = max(0.0, min(5.0, p.weight_separation + delta * 0.2))
        elif idx == 1:
            p.weight_alignment = max(0.0, min(5.0, p.weight_alignment + delta * 0.2))
        elif idx == 2:
            p.weight_cohesion = max(0.0, min(5.0, p.weight_cohesion + delta * 0.2))
        elif idx == 3:
            p.radius_perception = max(20.0, min(160.0, p.radius_perception + delta * 5.0))
        elif idx == 4:
            p.radius_panic = max(60.0, min(320.0, p.radius_panic + delta * 10.0))

    def draw_spatial_grid_overlay(self, sim: FlockingReserveSimulation):
        """Draws the 2D Spatial Hash Grid wireframe and cell boid counts."""
        cell_size = sim.spatial_grid.cell_size
        grid_map = sim.spatial_grid.grid
        min_cx = int(math.floor(RESERVE_MIN_X / cell_size))
        max_cx = int(math.floor(RESERVE_MAX_X / cell_size))
        min_cy = int(math.floor(RESERVE_MIN_Y / cell_size))
        max_cy = int(math.floor(RESERVE_MAX_Y / cell_size))

        for cx in range(min_cx, max_cx + 2):
            wx = int(cx * cell_size)
            draw_line(wx, int(RESERVE_MIN_Y), wx, int(RESERVE_MAX_Y), Color(25, 55, 75, 70))

        for cy in range(min_cy, max_cy + 2):
            wy = int(cy * cell_size)
            draw_line(int(RESERVE_MIN_X), wy, int(RESERVE_MAX_X), wy, Color(25, 55, 75, 70))

        for cell_coords in grid_map.keys():
            entries = grid_map[cell_coords]
            cnt = len(entries)
            if cnt > 0:
                cell_x, cell_y = cell_coords
                wx = int(cell_x * cell_size)
                wy = int(cell_y * cell_size)
                if wx >= RESERVE_MIN_X - 10 and wx <= RESERVE_MAX_X and wy >= RESERVE_MIN_Y - 10 and wy <= RESERVE_MAX_Y:
                    draw_rectangle(wx + 1, wy + 1, int(cell_size - 2), int(cell_size - 2), Color(40, 140, 160, min(80, cnt * 10)))
                    draw_text(str(cnt), wx + 4, wy + 4, 10, Color(120, 220, 240, 160))

    def draw_selected_boid_vectors(self, boid: Boid, sim: FlockingReserveSimulation):
        """
        Draws Craig Reynolds' force vector decomposition for the selected boid:
        - Separation: RED | Alignment: GREEN | Cohesion: BLUE
        - Obstacle: ORANGE | Panic: MAGENTA | Net: YELLOW | Velocity: CYAN
        """
        cx = int(boid.x)
        cy = int(boid.y)
        draw_circle_lines(cx, cy, int(sim.params.radius_perception), Color(70, 210, 255, 140))
        draw_circle_lines(cx, cy, int(sim.params.radius_separation), Color(255, 100, 100, 160))

        scale = 0.28
        f = boid.forces

        if abs(f.sep_x) > 0.1 or abs(f.sep_y) > 0.1:
            draw_line_ex(Vector2(boid.x, boid.y), Vector2(boid.x + f.sep_x * scale, boid.y + f.sep_y * scale), 2.5, Color(255, 70, 70, 240))
        if abs(f.ali_x) > 0.1 or abs(f.ali_y) > 0.1:
            draw_line_ex(Vector2(boid.x, boid.y), Vector2(boid.x + f.ali_x * scale, boid.y + f.ali_y * scale), 2.5, Color(60, 240, 90, 240))
        if abs(f.coh_x) > 0.1 or abs(f.coh_y) > 0.1:
            draw_line_ex(Vector2(boid.x, boid.y), Vector2(boid.x + f.coh_x * scale, boid.y + f.coh_y * scale), 2.5, Color(70, 130, 255, 240))
        if abs(f.obs_x) > 0.1 or abs(f.obs_y) > 0.1:
            draw_line_ex(Vector2(boid.x, boid.y), Vector2(boid.x + f.obs_x * scale, boid.y + f.obs_y * scale), 2.5, Color(255, 165, 40, 240))
        if abs(f.flee_x) > 0.1 or abs(f.flee_y) > 0.1:
            draw_line_ex(Vector2(boid.x, boid.y), Vector2(boid.x + f.flee_x * scale, boid.y + f.flee_y * scale), 3.0, Color(255, 50, 210, 255))
        if abs(f.net_x) > 0.1 or abs(f.net_y) > 0.1:
            draw_line_ex(Vector2(boid.x, boid.y), Vector2(boid.x + f.net_x * scale, boid.y + f.net_y * scale), 3.2, Color(255, 245, 50, 255))

        draw_line_ex(Vector2(boid.x, boid.y), Vector2(boid.x + boid.vx * 0.35, boid.y + boid.vy * 0.35), 2.0, Color(180, 250, 255, 220))
        draw_circle_lines(cx, cy, 14, Color(255, 235, 60, 220))

    def draw_telemetry_hud(self, sim: FlockingReserveSimulation, show_xray: bool):
        """Renders HUD telemetry cards, parameter tuning, and polarization order meter."""
        draw_rectangle(24, 14, 410, 36, Color(16, 22, 34, 230))
        draw_rectangle_lines(24, 14, 410, 36, Color(45, 75, 115, 255))
        draw_text("BOID FLOCKING & PREDATOR PANIC", 36, 22, 14, Color(240, 245, 255, 255))
        draw_text(f"MODE [F1]: {MODE_NAMES[sim.active_mode]}", 36, 38, 10, Color(70, 210, 255, 255))

        panel_x = 24
        panel_y = 510
        panel_w = 340
        panel_h = 190
        draw_rectangle(panel_x, panel_y, panel_w, panel_h, Color(14, 20, 32, 235))
        draw_rectangle_lines(panel_x, panel_y, panel_w, panel_h, Color(40, 65, 95, 255))
        draw_text("REYNOLDS PARAMETERS ([Up/Down] Select, [Left/Right] Tune)", panel_x + 12, panel_y + 10, 11, Color(255, 215, 80, 255))

        p = sim.params
        values = [
            f"{p.weight_separation:.2f}",
            f"{p.weight_alignment:.2f}",
            f"{p.weight_cohesion:.2f}",
            f"{p.radius_perception:.1f} px",
            f"{p.radius_panic:.1f} px"
        ]

        for i in range(len(self.param_names)):
            item_y = panel_y + 32 + i * 26
            is_active = (i == self.selected_param_idx)
            if is_active:
                draw_rectangle(panel_x + 8, item_y - 2, panel_w - 16, 22, Color(30, 65, 105, 180))
                draw_rectangle_lines(panel_x + 8, item_y - 2, panel_w - 16, 22, Color(80, 175, 255, 255))

            name_col = Color(255, 255, 255, 255) if is_active else Color(170, 185, 210, 255)
            val_col = Color(80, 235, 140, 255) if is_active else Color(130, 200, 160, 255)
            draw_text(self.param_names[i], panel_x + 16, item_y + 2, 11, name_col)
            draw_text(values[i], panel_x + 265, item_y + 2, 11, val_col)

        draw_text("Hotkeys [1-6]: Select Rule | [P]: Predator Auto-Hunt | [E]: Sonic Scatter", panel_x + 12, panel_y + 168, 10, Color(140, 160, 185, 255))

        right_w = 290
        right_h = 210
        right_x = SCREEN_WIDTH - right_w - 24
        right_y = SCREEN_HEIGHT - right_h - 18
        draw_rectangle(right_x, right_y, right_w, right_h, Color(14, 20, 32, 235))
        draw_rectangle_lines(right_x, right_y, right_w, right_h, Color(40, 65, 95, 255))
        draw_text("SWARM TELEMETRY & POLARIZATION", right_x + 12, right_y + 10, 11, Color(70, 210, 255, 255))

        phi = sim.polarization_order
        draw_text(f"Global Polarization Phi: {phi:.3f}", right_x + 14, right_y + 34, 11, Color(240, 245, 255, 255))

        bar_x = right_x + 14
        bar_y = right_y + 52
        bar_w = 260
        bar_h = 14
        draw_rectangle(bar_x, bar_y, bar_w, bar_h, Color(24, 32, 48, 255))
        draw_rectangle_lines(bar_x, bar_y, bar_w, bar_h, Color(55, 75, 110, 255))
        fill_w = int(bar_w * max(0.0, min(1.0, phi)))
        bar_col = Color(int(255 * (1.0 - phi)), int(80 + 175 * phi), int(120 + 135 * phi), 255)
        if fill_w > 0:
            draw_rectangle(bar_x + 1, bar_y + 1, fill_w - 2, bar_h - 2, bar_col)

        state_label = "Chaotic / Dispersed" if phi < 0.35 else ("Coordinated Flocking" if phi < 0.75 else "Synchronized School")
        draw_text(state_label, right_x + 14, right_y + 70, 10, Color(180, 200, 225, 255))
        draw_text(f"Boid Population      : {len(sim.boids)} agents", right_x + 14, right_y + 92, 10, Color(190, 205, 225, 255))
        draw_text(f"Avg Neighbors/Boid   : {sim.avg_neighbor_count:.1f} agents", right_x + 14, right_y + 108, 10, Color(190, 205, 225, 255))
        draw_text("Spatial Grid Speedup : O(N) vs O(N^2)", right_x + 14, right_y + 124, 10, Color(80, 235, 140, 255))
        pred_mode = "AUTONOMOUS HUNT" if sim.predator.is_auto_hunt else "PLAYER MANUAL"
        draw_text(f"Predator Mode [P]    : {pred_mode}", right_x + 14, right_y + 140, 10, Color(255, 180, 80, 255))
        draw_text(f"Prey Dispersed/Eaten : {sim.total_eaten} boids", right_x + 14, right_y + 156, 10, Color(255, 100, 100, 255))

        if show_xray:
            draw_text("X-Ray: [Red] Sep [Grn] Ali [Blu] Coh [Mag] Panic", right_x + 14, right_y + 180, 10, Color(255, 225, 70, 255))
        else:
            draw_text("Press [Tab] / Gamepad Y for Vector X-Ray Overlay", right_x + 14, right_y + 180, 10, Color(120, 140, 170, 255))


# ==============================================================================
# BLOCK 4: MAIN GAME LOOP & AUTOMATED SMOKE TEST
# ==============================================================================

class PatternLabGame:
    """Interactive pattern laboratory orchestrating dual input, simulation, and smoke testing."""
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()

        self.sfx = SoundLibrary()
        self.sfx.init_defaults()
        self.simulation = FlockingReserveSimulation(boid_count=200)
        self.telemetry = TelemetryOverlay()
        self.show_xray = True
        self.param_tune_timer = 0.0

    def handle_inputs(self, dt: float):
        """Processes simultaneous Keyboard/Mouse and Gamepad input."""
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
            self.sfx.play("click", 0.5)

        if is_dual_pattern_toggle_pressed():
            self.simulation.active_mode = (self.simulation.active_mode + 1) % len(MODE_NAMES)
            self.sfx.play("select", 0.6)

        # Direct number keys [1] - [6] for rule isolation
        if is_key_pressed(KEY_ONE):
            self.simulation.active_mode = MODE_FULL_FLOCKING
            self.sfx.play("select", 0.6)
        elif is_key_pressed(KEY_TWO):
            self.simulation.active_mode = MODE_SEPARATION_ONLY
            self.sfx.play("select", 0.6)
        elif is_key_pressed(KEY_THREE):
            self.simulation.active_mode = MODE_ALIGNMENT_ONLY
            self.sfx.play("select", 0.6)
        elif is_key_pressed(KEY_FOUR):
            self.simulation.active_mode = MODE_COHESION_ONLY
            self.sfx.play("select", 0.6)
        elif is_key_pressed(KEY_FIVE):
            self.simulation.active_mode = MODE_PREDATOR_PANIC_ONLY
            self.sfx.play("select", 0.6)
        elif is_key_pressed(KEY_SIX):
            self.simulation.active_mode = MODE_STEERING_OFF
            self.sfx.play("select", 0.6)

        if is_dual_reset_pressed():
            self.simulation.reset_simulation()
            self.sfx.play("cancel", 0.6)

        pad_id = get_active_gamepad_id()
        if is_key_pressed(KEY_P) or (pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_FACE_RIGHT)):
            self.simulation.predator.is_auto_hunt = not self.simulation.predator.is_auto_hunt
            self.sfx.play("click", 0.6)

        if is_dual_jump_pressed() or is_dual_primary_fire_pressed():
            if self.simulation.predator.lunge_boost():
                self.sfx.play("dash", 0.7)

        if is_key_pressed(KEY_E) or (pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_FACE_LEFT)):
            self.simulation.trigger_pulse_scatter(self.simulation.predator.x, self.simulation.predator.y, self.sfx)

        if is_key_pressed(KEY_UP) or (pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_LEFT_FACE_UP)):
            self.telemetry.cycle_param_selection(-1)
            self.sfx.play("select", 0.4)
        elif is_key_pressed(KEY_DOWN) or (pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_LEFT_FACE_DOWN)):
            self.telemetry.cycle_param_selection(1)
            self.sfx.play("select", 0.4)

        self.param_tune_timer += dt
        tune_delta = 0.0
        if is_key_down(KEY_LEFT) or (pad_id >= 0 and is_gamepad_button_down(pad_id, GAMEPAD_BUTTON_LEFT_FACE_LEFT)):
            if self.param_tune_timer > 0.09:
                tune_delta = -1.0
                self.param_tune_timer = 0.0
        elif is_key_down(KEY_RIGHT) or (pad_id >= 0 and is_gamepad_button_down(pad_id, GAMEPAD_BUTTON_LEFT_FACE_RIGHT)):
            if self.param_tune_timer > 0.09:
                tune_delta = 1.0
                self.param_tune_timer = 0.0

        if tune_delta != 0.0:
            self.telemetry.adjust_selected_param(self.simulation, tune_delta)

        if is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            mpos = get_mouse_position()
            if mpos.x > 380 and mpos.x < 980 and mpos.y > 60:
                self.simulation.select_boid_at(mpos.x, mpos.y)

    def update(self):
        """Simulation tick."""
        dt = min(get_frame_time(), 0.05)
        self.handle_inputs(dt)
        move_dir = get_dual_move_2d(deadzone=0.18, use_arrow_keys=False)
        look_dir = get_dual_look_2d(deadzone=0.18, use_arrow_keys=False)
        mouse_pos = get_mouse_position()
        self.simulation.update(dt, move_dir, look_dir, mouse_pos, self.sfx)

    def draw_boid(self, boid: Boid):
        """Renders an individual boid agent as an animated aquatic swimmer."""
        v_mag = math.sqrt(boid.vx * boid.vx + boid.vy * boid.vy)
        angle = math.atan2(boid.vy, boid.vx) if v_mag > 0.001 else 0.0
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        nose_x = boid.x + cos_a * 8.5
        nose_y = boid.y + sin_a * 8.5
        left_x = boid.x - cos_a * 5.0 - sin_a * 4.5
        left_y = boid.y - sin_a * 5.0 + cos_a * 4.5
        right_x = boid.x - cos_a * 5.0 + sin_a * 4.5
        right_y = boid.y - sin_a * 5.0 - cos_a * 4.5

        if boid.state == STATE_PANIC:
            body_col = Color(255, 95, 65, 245)
            rim_col = Color(255, 220, 180, 255)
        else:
            body_col = Color(55, 215, 225, 225)
            rim_col = Color(190, 250, 255, 255)

        draw_triangle(Vector2(float(nose_x), float(nose_y)), Vector2(float(left_x), float(left_y)), Vector2(float(right_x), float(right_y)), body_col)

        tail_wag = math.sin(boid.anim_phase) * 3.5
        tail_x = boid.x - cos_a * 9.0 - sin_a * tail_wag
        tail_y = boid.y - sin_a * 9.0 + cos_a * tail_wag
        draw_line_ex(Vector2(boid.x - cos_a * 4.0, boid.y - sin_a * 4.0), Vector2(float(tail_x), float(tail_y)), 1.8, rim_col)

    def draw(self):
        """Renders world environment, entities, telemetry overlay, and settings bar."""
        begin_drawing()
        clear_background(Color(10, 16, 28, 255))

        draw_rectangle_lines(int(RESERVE_MIN_X), int(RESERVE_MIN_Y), int(RESERVE_MAX_X - RESERVE_MIN_X), int(RESERVE_MAX_Y - RESERVE_MIN_Y), Color(30, 60, 90, 160))

        if self.show_xray:
            self.telemetry.draw_spatial_grid_overlay(self.simulation)

        for obs in self.simulation.obstacles:
            obs.draw()

        for p in self.simulation.particles:
            if p.active:
                alpha = int(220 * (p.lifetime / p.max_lifetime))
                draw_circle(int(p.x), int(p.y), p.radius, Color(p.color.r, p.color.g, p.color.b, alpha))

        selected_boid = None
        for boid in self.simulation.boids:
            if boid.active:
                self.draw_boid(boid)
                if boid.is_selected:
                    selected_boid = boid

        self.simulation.predator.draw(self.simulation.params.radius_panic, self.show_xray)

        if self.show_xray and selected_boid is not None:
            self.telemetry.draw_selected_boid_vectors(selected_boid, self.simulation)

        self.telemetry.draw_telemetry_hud(self.simulation, self.show_xray)

        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)
        end_drawing()

    def run(self, smoke_test: bool = False):
        """Main game loop with headless automated smoke test support."""
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
    PatternLabGame().run(smoke_test=is_smoke)
