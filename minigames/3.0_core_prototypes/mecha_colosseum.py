# -*- coding: utf-8 -*-
"""
Mecha Colosseum 3D - Behavior Trees, Kinematic Character Controller & Audio Synthesis
=====================================================================================
Section          : 3.0 Core Multi-Pattern Prototypes
Pattern Category : Artificial Intelligence, Physics/Kinematics, Audio Synthesis
Dimension        : 3D

Problem Solved:
  In 3D combat arenas, physics-driven rigid bodies cause mechas to snag on walls, bounce
  uncontrollably, or tip over. Meanwhile, hardcoded finite state machines (FSMs) become
  an unmaintainable mess when authoring multi-phase bosses that must dynamically prioritize
  between enrage combos, tactical retreats, pounce charges, and long-range artillery.

How the Patterns Work:
  1. Behavior Tree (BT): A hierarchical tree of Composite (Selector, Sequence), Condition,
     and Action nodes. Selectors prioritize tactical branches (e.g., Enraged Slam ->
     Close-Range Defense -> Pounce Charge -> Artillery Barrage -> Stalk). Sequences enforce
     ordered multi-step execution. Leaves return SUCCESS, FAILURE, or RUNNING.
  2. Kinematic Character Controller (Move-and-Slide): Velocity is integrated directly while
     detecting collisions with arena boundaries and cover pillars. On impact, the velocity is
     projected onto the surface tangent plane (v_slide = v - (v . n) * n), allowing the mecha
     to glide smoothly along obstacles without sticking or vibrating.
  3. Procedural Audio Synthesis: In-memory procedural audio generates laser fire, homing
     rocket launches, jet thruster bursts, shield impacts, and boss roars via SoundLibrary.
  4. Object Pool: Pre-allocated projectile and 3D particle pools eliminate memory allocation
     spikes and garbage collection hitching during heavy combat.
  5. Camera Rig & Screen Shake: Third-person orbital follow camera with framerate-independent
     spring damping (damp_v3) and quadratic Trauma screen shake.

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - WASD / Left Stick / D-Pad          : Move Mecha (relative to camera facing)
  - R-Mouse Drag / Arrows / Right Stick: Orbit Camera & Aim Heading
  - Spacebar / Gamepad A (or LT)       : Thruster Boost Jump (hold to hover, uses fuel)
  - Left Shift / Gamepad B (or LB)     : Kinetic Dash (directional burst with cooldown)
  - Left Mouse / J / Gamepad RT/RB/X   : Twin Plasma Arm Cannons (rapid fire)
  - K / Gamepad Y                      : Heavy Swarm Rocket (homing missile)
  - [Tab] / Gamepad View (Select)      : Toggle X-Ray Telemetry (BT Graph & Slide Vectors)
  - [F1] / Gamepad R3 (R-Stick Click)  : Toggle AI Brain: [Behavior Tree] vs [Dumb Chaser]
  - [F2] / Gamepad L3 (L-Stick Click)  : Toggle Kinematic Slide: [Slide ON] vs [Direct Snag]
  - [Ctrl +/-]                         : Increase / Decrease UI Font Size
  - [F11]                              : Toggle Fullscreen
  - [M]                                : Toggle Audio BGM
  - [R] / Gamepad Start                : Reset Colosseum Match
"""

import sys
import os
import math
import random

# ==============================================================================
# MANDATORY PRE-FLIGHT REPOSITORY CONFIGURATION
# ==============================================================================

# 1. Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# 2. Add repository root to search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# 3. Mandatory Raylib & modular workspace imports
from pyray import *
from assets import *
from utils import *

# Window & Arena Configuration
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WINDOW_TITLE = "Mecha Colosseum 3D - Behavior Trees & Kinematic Controller (Raylib)"

# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATIONS
# ==============================================================================

# ------------------------------------------------------------------------------
# PATTERN 1: BEHAVIOR TREE (BT) ARCHITECTURE
# ------------------------------------------------------------------------------
# Novice-friendly Behavior Tree implementation translating 1-to-1 into C++:
#   enum class BTStatus { Success = 1, Failure = 2, Running = 3 };
#   class BTNode { virtual BTStatus tick(Blackboard& bb, float dt) = 0; };
# Fixed-depth tree traversal without recursion recursion limits or hidden coroutines.

BT_SUCCESS = 1
BT_FAILURE = 2
BT_RUNNING = 3

BT_STATUS_NAMES = {
    BT_SUCCESS: "SUCCESS",
    BT_FAILURE: "FAILURE",
    BT_RUNNING: "RUNNING"
}

class BTNode:
    """
    Base node in a Behavior Tree.
    C++ Equivalent:
      class BTNode {
      public:
          std::string name;
          int status = 1;
          virtual int tick(BTBlackboard& bb, float dt) = 0;
          virtual void reset() { status = 1; }
      };
    """
    def __init__(self, name: str):
        self.name = name
        self.status = BT_SUCCESS
        self.last_tick_frame = 0

    def tick(self, bb, dt: float) -> int:
        return BT_SUCCESS

    def reset(self):
        self.status = BT_SUCCESS


class BTComposite(BTNode):
    """Base class for nodes containing ordered child branches."""
    def __init__(self, name: str):
        BTNode.__init__(self, name)
        self.children = []
        self.running_child_idx = -1

    def add_child(self, child: BTNode):
        self.children.append(child)
        return self

    def reset(self):
        self.status = BT_SUCCESS
        self.running_child_idx = -1
        for child in self.children:
            child.reset()


class BTSelector(BTComposite):
    """
    Fallback / Priority Selector Node.
    Ticked in priority order (index 0 to N-1).
    - If ANY child returns SUCCESS: Selector immediately returns SUCCESS.
    - If a child returns RUNNING: Selector remembers child and returns RUNNING.
    - If ALL children return FAILURE: Selector returns FAILURE.
    C++ Equivalent: Unreal Engine / BehaviorTree.CPP 'Fallback' node.
    """
    def __init__(self, name: str):
        BTComposite.__init__(self, name)

    def tick(self, bb, dt: float) -> int:
        start_idx = 0
        if self.running_child_idx >= 0:
            start_idx = self.running_child_idx

        for i in range(start_idx, len(self.children)):
            child = self.children[i]
            child_status = child.tick(bb, dt)
            if child_status == BT_RUNNING:
                self.running_child_idx = i
                self.status = BT_RUNNING
                return BT_RUNNING
            elif child_status == BT_SUCCESS:
                self.running_child_idx = -1
                self.status = BT_SUCCESS
                return BT_SUCCESS

        self.running_child_idx = -1
        self.status = BT_FAILURE
        return BT_FAILURE


class BTSequence(BTComposite):
    """
    Sequential Execution Node.
    Ticked in linear sequence (index 0 to N-1).
    - If ANY child returns FAILURE: Sequence aborts and returns FAILURE.
    - If a child returns RUNNING: Sequence pauses at that child and returns RUNNING.
    - If ALL children return SUCCESS: Sequence completes and returns SUCCESS.
    C++ Equivalent: Unreal Engine 'Sequence' composite.
    """
    def __init__(self, name: str):
        BTComposite.__init__(self, name)

    def tick(self, bb, dt: float) -> int:
        start_idx = 0
        if self.running_child_idx >= 0:
            start_idx = self.running_child_idx

        for i in range(start_idx, len(self.children)):
            child = self.children[i]
            child_status = child.tick(bb, dt)
            if child_status == BT_RUNNING:
                self.running_child_idx = i
                self.status = BT_RUNNING
                return BT_RUNNING
            elif child_status == BT_FAILURE:
                self.running_child_idx = -1
                self.status = BT_FAILURE
                return BT_FAILURE

        self.running_child_idx = -1
        self.status = BT_SUCCESS
        return BT_SUCCESS


class BTCondition(BTNode):
    """
    Leaf node evaluating a condition predicate on the blackboard.
    Returns BT_SUCCESS if condition is True, else BT_FAILURE.
    """
    def __init__(self, name: str, predicate_func):
        BTNode.__init__(self, name)
        self.predicate_func = predicate_func

    def tick(self, bb, dt: float) -> int:
        is_met = self.predicate_func(bb)
        if is_met:
            self.status = BT_SUCCESS
            return BT_SUCCESS
        else:
            self.status = BT_FAILURE
            return BT_FAILURE


class BTAction(BTNode):
    """
    Leaf node executing a tactical action method.
    Returns BT_SUCCESS, BT_FAILURE, or BT_RUNNING.
    """
    def __init__(self, name: str, action_func):
        BTNode.__init__(self, name)
        self.action_func = action_func

    def tick(self, bb, dt: float) -> int:
        self.status = self.action_func(bb, dt)
        return self.status


class BTBlackboard:
    """
    Shared blackboard repository storing sensory perception, tactical timers,
    and references needed across the boss Behavior Tree.
    C++ Equivalent: struct Blackboard { ... };
    """
    def __init__(self):
        self.boss = None
        self.player = None
        self.arena = None
        self.projectiles = None
        self.particles = None
        self.sfx = None
        self.shake = None

        # Sensory Perception
        self.dist_to_player = 0.0
        self.dir_to_player_x = 0.0
        self.dir_to_player_z = 1.0
        self.has_los = True
        self.is_enraged = False

        # Tactical Cooldown Timers
        self.slam_cooldown = 4.0
        self.charge_cooldown = 2.0
        self.artillery_cooldown = 3.0
        self.cleave_cooldown = 1.5

        # Action Execution State (for multi-frame actions)
        self.action_phase = 0      # 0: Idle, 1: Telegraph, 2: Execute, 3: Recover
        self.action_timer = 0.0
        self.locked_target_x = 0.0
        self.locked_target_z = 0.0
        self.active_action_name = "Idle"
        self.active_branch_name = "Root"


# ------------------------------------------------------------------------------
# PATTERN 2: KINEMATIC CHARACTER CONTROLLER (MOVE-AND-SLIDE)
# ------------------------------------------------------------------------------
# Explains why game engines use kinematic controllers instead of pure rigid bodies:
#   1. Naive Euler physics bounces on walls or snags when walking into corners.
#   2. Move-and-slide projects velocity onto the contact normal plane:
#        v_slide = v - (v . n) * n
#      This converts forward motion against an angled barrier into a smooth slide.
#   3. Depenetration displaces the character hull out of the collider geometry.

class KinematicController3D:
    """
    3D Kinematic Character Controller handling swept collisions and surface sliding.
    C++ Equivalent: CharacterController::MoveAndSlide()
    """
    def __init__(self, radius: float = 0.9, height: float = 2.2):
        self.radius = radius
        self.height = height
        self.pos = Vector3(0.0, 0.0, 0.0)
        self.vel = Vector3(0.0, 0.0, 0.0)
        self.intended_vel = Vector3(0.0, 0.0, 0.0)
        self.is_grounded = True
        self.is_sliding = False
        self.contact_normal = Vector3(0.0, 0.0, 0.0)
        self.slide_enabled = True   # Toggled with [F2] to demonstrate difference

    def move_and_slide(self, desired_horizontal_vel: Vector3, dt: float, arena, boss):
        """
        Integrates movement with 3D cylindrical swept collision detection and plane projection.
        """
        self.intended_vel.x = desired_horizontal_vel.x
        self.intended_vel.y = 0.0
        self.intended_vel.z = desired_horizontal_vel.z

        # Smooth velocity acceleration toward desired input
        accel = 16.0
        self.vel.x = approach(self.vel.x, desired_horizontal_vel.x, accel * dt)
        self.vel.z = approach(self.vel.z, desired_horizontal_vel.z, accel * dt)

        # Proposed new position
        new_x = self.pos.x + self.vel.x * dt
        new_z = self.pos.z + self.vel.z * dt

        self.is_sliding = False
        self.contact_normal.x = 0.0
        self.contact_normal.y = 0.0
        self.contact_normal.z = 0.0

        # Iteration 1: Arena Boundary Collision
        arena_dist = math.sqrt(new_x * new_x + new_z * new_z)
        max_dist = arena.radius - self.radius
        if arena_dist > max_dist:
            if arena_dist > 0.0001:
                # Normal pointing inward from arena boundary
                nx = -new_x / arena_dist
                nz = -new_z / arena_dist
                self.contact_normal.x = nx
                self.contact_normal.z = nz
                self.is_sliding = True
                new_x = -nx * max_dist
                new_z = -nz * max_dist

                if self.slide_enabled:
                    # Project velocity onto wall tangent
                    dot = self.vel.x * nx + self.vel.z * nz
                    if dot < 0.0:
                        self.vel.x -= dot * nx
                        self.vel.z -= dot * nz
                else:
                    # Naive block: stops dead upon touching wall
                    self.vel.x = 0.0
                    self.vel.z = 0.0

        # Iteration 2: Cover Pillar Collisions
        for pillar in arena.pillars:
            dx = new_x - pillar.pos.x
            dz = new_z - pillar.pos.z
            dist = math.sqrt(dx * dx + dz * dz)
            min_dist = pillar.radius + self.radius
            if dist < min_dist:
                if dist > 0.0001:
                    nx = dx / dist
                    nz = dz / dist
                    self.contact_normal.x = nx
                    self.contact_normal.z = nz
                    self.is_sliding = True
                    new_x = pillar.pos.x + nx * min_dist
                    new_z = pillar.pos.z + nz * min_dist

                    if self.slide_enabled:
                        dot = self.vel.x * nx + self.vel.z * nz
                        if dot < 0.0:
                            self.vel.x -= dot * nx
                            self.vel.z -= dot * nz
                    else:
                        self.vel.x = 0.0
                        self.vel.z = 0.0

        # Iteration 3: Boss Hull Collision
        if boss is not None and boss.hp > 0.0:
            dx = new_x - boss.pos.x
            dz = new_z - boss.pos.z
            dist = math.sqrt(dx * dx + dz * dz)
            min_dist = boss.radius + self.radius
            if dist < min_dist:
                if dist > 0.0001:
                    nx = dx / dist
                    nz = dz / dist
                    self.contact_normal.x = nx
                    self.contact_normal.z = nz
                    self.is_sliding = True
                    new_x = boss.pos.x + nx * min_dist
                    new_z = boss.pos.z + nz * min_dist

                    if self.slide_enabled:
                        dot = self.vel.x * nx + self.vel.z * nz
                        if dot < 0.0:
                            self.vel.x -= dot * nx
                            self.vel.z -= dot * nz
                    else:
                        self.vel.x = 0.0
                        self.vel.z = 0.0

        self.pos.x = new_x
        self.pos.z = new_z


# ==============================================================================
# BLOCK 2: WORLD SIMULATION & ENTITIES
# ==============================================================================

# ------------------------------------------------------------------------------
# OBJECT POOLING FOR PROJECTILES & PARTICLES
# ------------------------------------------------------------------------------
PROJ_PLAYER_PLASMA = 1
PROJ_PLAYER_ROCKET = 2
PROJ_BOSS_MORTAR = 3
PROJ_BOSS_SHOCKWAVE = 4

class Projectile:
    """Pre-allocated projectile slot for zero garbage collection overhead."""
    def __init__(self):
        self.active = False
        self.ptype = PROJ_PLAYER_PLASMA
        self.pos = Vector3(0.0, 0.0, 0.0)
        self.vel = Vector3(0.0, 0.0, 0.0)
        self.radius = 0.3
        self.life = 0.0
        self.max_life = 3.0
        self.damage = 10.0
        self.color = Color(0, 230, 255, 255)
        self.trail_timer = 0.0


class ProjectilePool:
    """Fixed-capacity pool of 120 projectiles."""
    def __init__(self, capacity: int = 120):
        self.capacity = capacity
        self.pool = []
        for _ in range(capacity):
            self.pool.append(Projectile())

    def spawn(self, ptype: int, pos: Vector3, vel: Vector3, radius: float,
              life: float, damage: float, color: Color) -> Projectile:
        for p in self.pool:
            if not p.active:
                p.active = True
                p.ptype = ptype
                p.pos.x = pos.x
                p.pos.y = pos.y
                p.pos.z = pos.z
                p.vel.x = vel.x
                p.vel.y = vel.y
                p.vel.z = vel.z
                p.radius = radius
                p.life = life
                p.max_life = life
                p.damage = damage
                p.color = color
                p.trail_timer = 0.0
                return p
        return None

    def clear(self):
        for p in self.pool:
            p.active = False


class Particle3D:
    """Pre-allocated 3D spark / smoke / explosion particle."""
    def __init__(self):
        self.active = False
        self.pos = Vector3(0.0, 0.0, 0.0)
        self.vel = Vector3(0.0, 0.0, 0.0)
        self.size = 0.1
        self.life = 0.0
        self.max_life = 1.0
        self.color = Color(255, 200, 50, 255)


class ParticlePool3D:
    """Fixed-capacity pool of 200 3D particles."""
    def __init__(self, capacity: int = 200):
        self.capacity = capacity
        self.pool = []
        for _ in range(capacity):
            self.pool.append(Particle3D())

    def spawn_burst(self, pos: Vector3, count: int, color: Color, speed: float = 8.0, life: float = 0.6):
        spawned = 0
        for p in self.pool:
            if not p.active:
                p.active = True
                p.pos.x = pos.x
                p.pos.y = pos.y
                p.pos.z = pos.z
                theta = random.random() * math.pi * 2.0
                phi = (random.random() - 0.5) * math.pi
                spd = speed * (0.4 + random.random() * 0.8)
                p.vel.x = math.cos(phi) * math.cos(theta) * spd
                p.vel.y = math.sin(phi) * spd + 1.5
                p.vel.z = math.cos(phi) * math.sin(theta) * spd
                p.size = 0.12 + random.random() * 0.12
                p.life = life * (0.7 + random.random() * 0.6)
                p.max_life = p.life
                p.color = color
                spawned += 1
                if spawned >= count:
                    break

    def update(self, dt: float):
        for p in self.pool:
            if p.active:
                p.life -= dt
                if p.life <= 0.0:
                    p.active = False
                else:
                    p.pos.x += p.vel.x * dt
                    p.pos.y += p.vel.y * dt
                    p.pos.z += p.vel.z * dt
                    p.vel.y -= 12.0 * dt  # Gravity
                    if p.pos.y < 0.05:
                        p.pos.y = 0.05
                        p.vel.x *= 0.8
                        p.vel.z *= 0.8

    def draw(self):
        for p in self.pool:
            if p.active:
                t = p.life / p.max_life
                alpha = int(255 * t)
                c = Color(p.color.r, p.color.g, p.color.b, max(0, min(255, alpha)))
                draw_cube(p.pos, p.size * t, p.size * t, p.size * t, c)


# ------------------------------------------------------------------------------
# ARENA ENVIRONMENT & COVER PILLARS
# ------------------------------------------------------------------------------
class CoverPillar:
    """Tactical cover monoliths that block line of sight, lasers, and charges."""
    def __init__(self, x: float, z: float, radius: float = 2.4, height: float = 7.5):
        self.pos = Vector3(x, 0.0, z)
        self.radius = radius
        self.height = height


class ColosseumArena:
    """3D Colosseum Arena with concentric battle floor, cover pillars, and forcefield."""
    def __init__(self, radius: float = 34.0):
        self.radius = radius
        self.pillars = [
            CoverPillar(-14.0, -14.0, 2.4, 7.5),
            CoverPillar( 14.0, -14.0, 2.4, 7.5),
            CoverPillar(-14.0,  14.0, 2.4, 7.5),
            CoverPillar( 14.0,  14.0, 2.4, 7.5),
        ]

    def draw_3d(self):
        # 1. Main floor platform (metallic concentric disks)
        draw_cylinder(Vector3(0.0, -0.2, 0.0), self.radius, self.radius, 0.4, 48, Color(22, 26, 38, 255))
        draw_cylinder_wires(Vector3(0.0, 0.02, 0.0), self.radius, self.radius, 0.05, 48, Color(50, 85, 140, 255))

        # 2. Inner tactical combat ring (radius 18.0)
        draw_cylinder_wires(Vector3(0.0, 0.03, 0.0), 18.0, 18.0, 0.05, 36, Color(40, 65, 100, 180))

        # 3. Floor grid
        draw_grid(34, 2.0)

        # 4. Tactical Cover Pillars
        for pillar in self.pillars:
            # Pillar Base
            draw_cylinder(Vector3(pillar.pos.x, 0.4, pillar.pos.z), pillar.radius + 0.3, pillar.radius + 0.5, 0.8, 16, Color(35, 40, 52, 255))
            # Main Shaft
            draw_cylinder(Vector3(pillar.pos.x, pillar.height * 0.5, pillar.pos.z), pillar.radius, pillar.radius, pillar.height, 16, Color(55, 65, 82, 255))
            # Glowing Energy Conduit Ring
            draw_cylinder(Vector3(pillar.pos.x, pillar.height * 0.5, pillar.pos.z), pillar.radius + 0.08, pillar.radius + 0.08, 0.5, 16, Color(0, 190, 255, 200))
            # Pillar Cap
            draw_cylinder(Vector3(pillar.pos.x, pillar.height, pillar.pos.z), pillar.radius + 0.2, pillar.radius - 0.2, 0.6, 16, Color(42, 48, 62, 255))
            # Wireframe accents
            draw_cylinder_wires(Vector3(pillar.pos.x, pillar.height * 0.5, pillar.pos.z), pillar.radius, pillar.radius, pillar.height, 16, Color(25, 30, 40, 255))

        # 5. Perimeter Barrier Monoliths
        monolith_count = 16
        for i in range(monolith_count):
            angle = (i / monolith_count) * math.pi * 2.0
            mx = math.cos(angle) * (self.radius + 1.2)
            mz = math.sin(angle) * (self.radius + 1.2)
            draw_cube(Vector3(mx, 3.5, mz), 1.2, 7.0, 1.2, Color(40, 48, 68, 255))
            draw_cube(Vector3(mx, 3.5, mz), 0.6, 5.0, 0.6, Color(0, 180, 255, 150))
            draw_cube_wires(Vector3(mx, 3.5, mz), 1.2, 7.0, 1.2, Color(60, 80, 110, 255))


# ------------------------------------------------------------------------------
# PLAYER MECHA ENTITY
# ------------------------------------------------------------------------------
class PlayerMecha:
    """
    Procedurally rendered player mecha equipped with a Kinematic Character Controller,
    thruster jetpack, twin plasma arm cannons, and micro-missile launchers.
    """
    def __init__(self, start_x: float = 0.0, start_z: float = -20.0):
        self.controller = KinematicController3D(radius=0.9, height=2.2)
        self.controller.pos.x = start_x
        self.controller.pos.y = 0.0
        self.controller.pos.z = start_z

        self.facing_yaw = 0.0
        self.hp = 100.0
        self.max_hp = 100.0
        self.boost_energy = 100.0
        self.max_boost_energy = 100.0

        # Ability Timers
        self.dash_cooldown = 0.0
        self.dash_active_timer = 0.0
        self.dash_dir = Vector3(0.0, 0.0, 0.0)
        self.primary_cooldown = 0.0
        self.secondary_cooldown = 0.0
        self.is_boosting = False
        self.anim_timer = 0.0
        self.arm_barrel_toggle = 0

    def update(self, dt: float, move_dir: Vector3, is_boost_held: bool,
               dash_requested: bool, arena, boss, sfx, particles):
        self.anim_timer += dt
        speed = 14.0

        # Cooldown ticks
        if self.dash_cooldown > 0.0:
            self.dash_cooldown -= dt
        if self.primary_cooldown > 0.0:
            self.primary_cooldown -= dt
        if self.secondary_cooldown > 0.0:
            self.secondary_cooldown -= dt

        # Thruster Dash Logic
        if dash_requested and self.dash_cooldown <= 0.0 and self.boost_energy >= 30.0:
            self.boost_energy -= 30.0
            self.dash_cooldown = 1.1
            self.dash_active_timer = 0.22
            if abs(move_dir.x) > 0.01 or abs(move_dir.z) > 0.01:
                self.dash_dir.x = move_dir.x
                self.dash_dir.z = move_dir.z
            else:
                self.dash_dir.x = math.sin(self.facing_yaw * math.pi / 180.0)
                self.dash_dir.z = math.cos(self.facing_yaw * math.pi / 180.0)
            sfx.play("powerup", 0.6)
            particles.spawn_burst(self.controller.pos, 16, Color(0, 240, 255, 255), 10.0, 0.4)

        if self.dash_active_timer > 0.0:
            self.dash_active_timer -= dt
            dash_speed = 34.0
            horiz_vel = Vector3(self.dash_dir.x * dash_speed, 0.0, self.dash_dir.z * dash_speed)
        else:
            horiz_vel = Vector3(move_dir.x * speed, 0.0, move_dir.z * speed)

        # Vertical Thruster Boost Jump
        self.is_boosting = False
        gravity = -30.0
        if is_boost_held and self.boost_energy > 0.0:
            self.is_boosting = True
            self.boost_energy = max(0.0, self.boost_energy - 35.0 * dt)
            self.controller.vel.y = approach(self.controller.vel.y, 11.0, 45.0 * dt)
            # Spawn thruster sparks
            jet_pos = Vector3(self.controller.pos.x, self.controller.pos.y + 0.8, self.controller.pos.z)
            particles.spawn_burst(jet_pos, 2, Color(255, 170, 40, 255), 4.0, 0.25)
        else:
            self.controller.vel.y += gravity * dt

        # Integrate vertical movement
        self.controller.pos.y += self.controller.vel.y * dt
        if self.controller.pos.y <= 0.0:
            self.controller.pos.y = 0.0
            self.controller.vel.y = 0.0
            self.controller.is_grounded = True
            # Energy regeneration while grounded
            self.boost_energy = min(self.max_boost_energy, self.boost_energy + 28.0 * dt)
        else:
            self.controller.is_grounded = False

        # Integrate horizontal movement through Kinematic Move-and-Slide
        self.controller.move_and_slide(horiz_vel, dt, arena, boss)

        # Smooth mecha rotation toward movement direction
        if abs(move_dir.x) > 0.05 or abs(move_dir.z) > 0.05:
            target_yaw = math.atan2(move_dir.x, move_dir.z) * 180.0 / math.pi
            # Angular approach
            diff = (target_yaw - self.facing_yaw + 180.0) % 360.0 - 180.0
            self.facing_yaw += diff * min(1.0, 14.0 * dt)

    def draw_3d(self):
        pos = self.controller.pos
        yaw = self.facing_yaw

        rl_push_matrix()
        rl_translatef(pos.x, pos.y, pos.z)
        rl_rotatef(yaw, 0.0, 1.0, 0.0)

        # Walk/Hover bobbing animation
        bob = math.sin(self.anim_timer * 10.0) * 0.06 if self.controller.is_grounded and (abs(self.controller.vel.x) > 1.0 or abs(self.controller.vel.z) > 1.0) else 0.0

        # 1. Main Torso / Cockpit Chassis
        draw_cube(Vector3(0.0, 1.4 + bob, 0.0), 0.9, 0.75, 0.7, Color(35, 45, 62, 255))
        draw_cube_wires(Vector3(0.0, 1.4 + bob, 0.0), 0.9, 0.75, 0.7, Color(60, 80, 110, 255))

        # Chest Armor Carapace
        draw_cube(Vector3(0.0, 1.45 + bob, 0.28), 0.75, 0.55, 0.28, Color(52, 68, 92, 255))

        # Glowing Cyan Visor Slit
        draw_cube(Vector3(0.0, 1.62 + bob, 0.38), 0.5, 0.12, 0.1, Color(0, 240, 255, 255))

        # 2. Shoulder Missile Pod Pauldrons
        draw_cube(Vector3(-0.68, 1.65 + bob, 0.0), 0.42, 0.38, 0.55, Color(42, 54, 76, 255))
        draw_cube(Vector3( 0.68, 1.65 + bob, 0.0), 0.42, 0.38, 0.55, Color(42, 54, 76, 255))

        # 3. Dual Forearm Plasma Cannons
        draw_cylinder(Vector3(-0.68, 1.25 + bob, 0.35), 0.11, 0.11, 0.8, 12, Color(22, 26, 34, 255))
        draw_cylinder(Vector3( 0.68, 1.25 + bob, 0.35), 0.11, 0.11, 0.8, 12, Color(22, 26, 34, 255))
        draw_sphere(Vector3(-0.68, 1.25 + bob, 0.75), 0.13, Color(0, 230, 255, 255))
        draw_sphere(Vector3( 0.68, 1.25 + bob, 0.75), 0.13, Color(0, 230, 255, 255))

        # 4. Back Jet Thrusters
        draw_cylinder(Vector3(-0.3, 1.5 + bob, -0.42), 0.14, 0.16, 0.5, 12, Color(30, 36, 48, 255))
        draw_cylinder(Vector3( 0.3, 1.5 + bob, -0.42), 0.14, 0.16, 0.5, 12, Color(30, 36, 48, 255))

        # Active Thruster Jet Flame Cones
        if self.is_boosting or self.dash_active_timer > 0.0:
            flame_scale = 1.5 if self.dash_active_timer > 0.0 else 1.0
            draw_cylinder(Vector3(-0.3, 1.2 + bob, -0.42), 0.14 * flame_scale, 0.02, 0.6 * flame_scale, 10, Color(255, 160, 40, 255))
            draw_cylinder(Vector3( 0.3, 1.2 + bob, -0.42), 0.14 * flame_scale, 0.02, 0.6 * flame_scale, 10, Color(255, 160, 40, 255))

        # 5. Bipedal Legs & Foot Pads
        leg_swing = math.sin(self.anim_timer * 10.0) * 18.0 if self.controller.is_grounded and (abs(self.controller.vel.x) > 1.0 or abs(self.controller.vel.z) > 1.0) else 0.0
        # Left Leg
        draw_cylinder(Vector3(-0.35, 0.55, 0.0), 0.12, 0.12, 0.7, 10, Color(28, 34, 46, 255))
        draw_cube(Vector3(-0.35, 0.1, 0.08), 0.28, 0.18, 0.45, Color(45, 58, 80, 255))
        # Right Leg
        draw_cylinder(Vector3( 0.35, 0.55, 0.0), 0.12, 0.12, 0.7, 10, Color(28, 34, 46, 255))
        draw_cube(Vector3( 0.35, 0.1, 0.08), 0.28, 0.18, 0.45, Color(45, 58, 80, 255))

        rl_pop_matrix()


# ------------------------------------------------------------------------------
# BOSS TITAN BEHEMOTH (BEHAVIOR TREE DRIVEN)
# ------------------------------------------------------------------------------
# Tactical Actions for Behavior Tree Leaf Nodes

def cond_is_enraged_and_ready(bb: BTBlackboard) -> bool:
    """Evaluates if the Boss is in Phase 2 and Enrage Slam cooldown is ready."""
    return bb.boss.hp <= 300.0 and bb.slam_cooldown <= 0.0

def act_shockwave_slam(bb: BTBlackboard, dt: float) -> int:
    """
    Multi-stage Boss Enrage Slam Action:
      Phase 1: Telegraph (Boss rears up, eyes roar bright red, 0.5s)
      Phase 2: Leap & Ground Slam (Spawns 360-degree shockwave ring, 0.4s)
      Phase 3: Recovery pause (0.4s)
    """
    bb.active_action_name = "ShockwaveSlam"
    bb.active_branch_name = "Phase2EnrageCombo"

    if bb.action_phase == 0:
        bb.action_phase = 1
        bb.action_timer = 0.55
        bb.sfx.play("hurt", 0.9)
        return BT_RUNNING

    elif bb.action_phase == 1:
        # Telegraph phase
        bb.action_timer -= dt
        # Turn to player
        bb.boss.facing_yaw = approach(bb.boss.facing_yaw, bb.angle_to_player, 180.0 * dt)
        if bb.action_timer <= 0.0:
            bb.action_phase = 2
            bb.action_timer = 0.35
            # Record slam leap target
            bb.locked_target_x = bb.player.controller.pos.x
            bb.locked_target_z = bb.player.controller.pos.z
        return BT_RUNNING

    elif bb.action_phase == 2:
        # Leap & Slam
        bb.action_timer -= dt
        # Interpolate position toward target
        bb.boss.pos.x = approach(bb.boss.pos.x, bb.locked_target_x, 16.0 * dt)
        bb.boss.pos.z = approach(bb.boss.pos.z, bb.locked_target_z, 16.0 * dt)
        bb.boss.pos.y = math.sin((1.0 - (bb.action_timer / 0.35)) * math.pi) * 2.5

        if bb.action_timer <= 0.0:
            bb.boss.pos.y = 0.0
            bb.action_phase = 3
            bb.action_timer = 0.4
            # Slam Impact!
            bb.sfx.play("explosion", 1.0)
            bb.shake.add_trauma(0.7)
            bb.particles.spawn_burst(bb.boss.pos, 35, Color(255, 90, 30, 255), 14.0, 0.7)

            # Spawn Expanding Shockwave Ring
            bb.projectiles.spawn(
                PROJ_BOSS_SHOCKWAVE,
                Vector3(bb.boss.pos.x, 0.1, bb.boss.pos.z),
                Vector3(0.0, 0.0, 0.0),
                radius=1.5,
                life=2.0,
                damage=28.0,
                color=Color(255, 70, 20, 220)
            )
        return BT_RUNNING

    elif bb.action_phase == 3:
        # Recovery
        bb.action_timer -= dt
        if bb.action_timer <= 0.0:
            bb.action_phase = 0
            bb.slam_cooldown = 9.0
            return BT_SUCCESS
        return BT_RUNNING

    return BT_SUCCESS


def cond_player_too_close(bb: BTBlackboard) -> bool:
    """Checks if player penetrated inside close-quarters defense perimeter (< 8.5m)."""
    return bb.dist_to_player < 8.5

def cond_cleave_ready(bb: BTBlackboard) -> bool:
    return bb.cleave_cooldown <= 0.0

def act_tail_cleave(bb: BTBlackboard, dt: float) -> int:
    """Spins 360 degrees to cleave nearby targets with tail mace."""
    bb.active_action_name = "TailCleave"
    bb.active_branch_name = "CloseQuarterDefense"

    if bb.action_phase == 0:
        bb.action_phase = 1
        bb.action_timer = 0.4
        bb.sfx.play("hit", 0.8)
        return BT_RUNNING

    elif bb.action_phase == 1:
        bb.action_timer -= dt
        bb.boss.facing_yaw += 900.0 * dt  # Rapid spin
        if bb.action_timer <= 0.0:
            # Check damage on player
            if bb.dist_to_player < 7.0 and bb.player.controller.pos.y < 1.5:
                bb.player.hp -= 20.0
                bb.sfx.play("hurt", 0.9)
                bb.shake.add_trauma(0.5)
                # Knockback
                bb.player.controller.vel.x = bb.dir_to_player_x * 18.0
                bb.player.controller.vel.z = bb.dir_to_player_z * 18.0
            bb.action_phase = 0
            bb.cleave_cooldown = 3.5
            return BT_SUCCESS
        return BT_RUNNING

    return BT_SUCCESS

def act_disengage_hop(bb: BTBlackboard, dt: float) -> int:
    """Tactical backward leap to restore defensive distance."""
    bb.active_action_name = "DisengageHop"
    bb.active_branch_name = "CloseQuarterDefense"

    if bb.action_phase == 0:
        bb.action_phase = 1
        bb.action_timer = 0.35
        bb.sfx.play("jump", 0.7)
        return BT_RUNNING

    elif bb.action_phase == 1:
        bb.action_timer -= dt
        # Move away from player
        bb.boss.pos.x -= bb.dir_to_player_x * 14.0 * dt
        bb.boss.pos.z -= bb.dir_to_player_z * 14.0 * dt
        bb.boss.pos.y = math.sin((1.0 - (bb.action_timer / 0.35)) * math.pi) * 1.5
        if bb.action_timer <= 0.0:
            bb.boss.pos.y = 0.0
            bb.action_phase = 0
            return BT_SUCCESS
        return BT_RUNNING

    return BT_SUCCESS


def cond_can_pounce_charge(bb: BTBlackboard) -> bool:
    """Checks if Boss has clear Line-of-Sight and is in mid-range charging corridor (8.5m..24m)."""
    return (bb.dist_to_player >= 8.5 and bb.dist_to_player <= 24.0 and
            bb.charge_cooldown <= 0.0 and bb.has_los)

def act_pounce_charge(bb: BTBlackboard, dt: float) -> int:
    """
    High-speed ramming charge:
      Phase 1: Aim & Paw Ground (0.4s)
      Phase 2: Blitz Surge forward along locked vector (0.65s)
      Phase 3: Skid / Recovery (0.3s)
    """
    bb.active_action_name = "PounceCharge"
    bb.active_branch_name = "PounceChargeAssault"

    if bb.action_phase == 0:
        bb.action_phase = 1
        bb.action_timer = 0.4
        bb.locked_target_x = bb.dir_to_player_x
        bb.locked_target_z = bb.dir_to_player_z
        bb.sfx.play("laser", 0.5)
        return BT_RUNNING

    elif bb.action_phase == 1:
        bb.action_timer -= dt
        bb.boss.facing_yaw = approach(bb.boss.facing_yaw, bb.angle_to_player, 240.0 * dt)
        if bb.action_timer <= 0.0:
            bb.action_phase = 2
            bb.action_timer = 0.65
            bb.sfx.play("powerup", 0.8)
        return BT_RUNNING

    elif bb.action_phase == 2:
        bb.action_timer -= dt
        charge_spd = 25.0
        bb.boss.pos.x += bb.locked_target_x * charge_spd * dt
        bb.boss.pos.z += bb.locked_target_z * charge_spd * dt
        # Spawn ground dust
        bb.particles.spawn_burst(bb.boss.pos, 2, Color(180, 150, 100, 180), 5.0, 0.3)

        # Check collision with player
        if bb.dist_to_player < (bb.boss.radius + bb.player.controller.radius):
            bb.player.hp -= 24.0
            bb.sfx.play("hit", 1.0)
            bb.shake.add_trauma(0.65)
            bb.player.controller.vel.x = bb.locked_target_x * 24.0
            bb.player.controller.vel.z = bb.locked_target_z * 24.0
            bb.action_phase = 3
            bb.action_timer = 0.3

        # Stop on arena boundary
        d_center = math.sqrt(bb.boss.pos.x * bb.boss.pos.x + bb.boss.pos.z * bb.boss.pos.z)
        if d_center > (bb.arena.radius - bb.boss.radius):
            bb.action_phase = 3
            bb.action_timer = 0.3

        if bb.action_timer <= 0.0:
            bb.action_phase = 3
            bb.action_timer = 0.3
        return BT_RUNNING

    elif bb.action_phase == 3:
        bb.action_timer -= dt
        if bb.action_timer <= 0.0:
            bb.action_phase = 0
            bb.charge_cooldown = 5.5
            return BT_SUCCESS
        return BT_RUNNING

    return BT_SUCCESS


def cond_can_artillery(bb: BTBlackboard) -> bool:
    """Checks if player is at long range (>13m) and artillery cooldown is ready."""
    return bb.dist_to_player > 13.0 and bb.artillery_cooldown <= 0.0

def act_fire_artillery(bb: BTBlackboard, dt: float) -> int:
    """Rotates dorsal turret and launches 3 ballistic mortar shells at the player."""
    bb.active_action_name = "FireArtillery"
    bb.active_branch_name = "LongRangeArtillery"

    if bb.action_phase == 0:
        bb.action_phase = 1
        bb.action_timer = 0.6
        return BT_RUNNING

    elif bb.action_phase == 1:
        bb.action_timer -= dt
        # Aim dorsal turret at player
        bb.boss.turret_yaw = bb.angle_to_player
        bb.boss.turret_pitch = 22.0

        # Fire 3 shells at intervals
        if 0.38 < bb.action_timer <= 0.40 or 0.18 < bb.action_timer <= 0.20 or 0.0 < bb.action_timer <= 0.02:
            bb.sfx.play("laser", 0.7)
            # Ballistic trajectory calculation
            spread_x = (random.random() - 0.5) * 6.0
            spread_z = (random.random() - 0.5) * 6.0
            target_pos = Vector3(bb.player.controller.pos.x + spread_x, 0.0, bb.player.controller.pos.z + spread_z)
            t_flight = 1.3
            vx = (target_pos.x - bb.boss.pos.x) / t_flight
            vz = (target_pos.z - bb.boss.pos.z) / t_flight
            vy = 12.0  # Upward arc with gravity
            start_pos = Vector3(bb.boss.pos.x, bb.boss.pos.y + 2.2, bb.boss.pos.z)
            bb.projectiles.spawn(
                PROJ_BOSS_MORTAR,
                start_pos,
                Vector3(vx, vy, vz),
                radius=0.45,
                life=t_flight + 0.1,
                damage=18.0,
                color=Color(255, 60, 60, 255)
            )

        if bb.action_timer <= 0.0:
            bb.action_phase = 0
            bb.artillery_cooldown = 4.5
            return BT_SUCCESS
        return BT_RUNNING

    return BT_SUCCESS


def act_tactical_stalk(bb: BTBlackboard, dt: float) -> int:
    """
    Default Fallback Action:
    Maintains tactical engagement distance (12..16m), circles/flanks the player,
    and takes potshots from the dorsal turret.
    """
    bb.active_action_name = "TacticalStalk"
    bb.active_branch_name = "TacticalStalkFallback"

    # Aim turret
    bb.boss.turret_yaw = bb.angle_to_player
    bb.boss.turret_pitch = 10.0

    # Face player
    bb.boss.facing_yaw = approach(bb.boss.facing_yaw, bb.angle_to_player, 120.0 * dt)

    stalk_speed = 7.0 if bb.boss.hp > 300.0 else 10.0
    desired_dist = 14.0

    # Distance regulation
    if bb.dist_to_player < (desired_dist - 2.0):
        # Back away
        bb.boss.pos.x -= bb.dir_to_player_x * stalk_speed * dt
        bb.boss.pos.z -= bb.dir_to_player_z * stalk_speed * dt
    elif bb.dist_to_player > (desired_dist + 2.0):
        # Approach
        bb.boss.pos.x += bb.dir_to_player_x * stalk_speed * dt
        bb.boss.pos.z += bb.dir_to_player_z * stalk_speed * dt
    else:
        # Circle strafe
        perp_x = -bb.dir_to_player_z
        perp_z = bb.dir_to_player_x
        bb.boss.pos.x += perp_x * stalk_speed * 0.7 * dt
        bb.boss.pos.z += perp_z * stalk_speed * 0.7 * dt

    # Keep inside arena
    d_center = math.sqrt(bb.boss.pos.x * bb.boss.pos.x + bb.boss.pos.z * bb.boss.pos.z)
    max_d = bb.arena.radius - bb.boss.radius
    if d_center > max_d and d_center > 0.001:
        bb.boss.pos.x = (bb.boss.pos.x / d_center) * max_d
        bb.boss.pos.z = (bb.boss.pos.z / d_center) * max_d

    return BT_RUNNING


class BossTitan:
    """
    Titan Colosseum Boss combining the Quadruped Beast chassis with a back-mounted
    Heavy Turret, driven by a Behavior Tree.
    """
    def __init__(self, start_x: float = 0.0, start_z: float = 16.0):
        self.pos = Vector3(start_x, 0.0, start_z)
        self.facing_yaw = 180.0
        self.turret_yaw = 180.0
        self.turret_pitch = 10.0
        self.radius = 2.8
        self.scale = 1.6
        self.anim_timer = 0.0

        self.hp = 600.0
        self.max_hp = 600.0
        self.chip_hp = 600.0  # Lagging health bar

        self.ai_mode = "BT"   # "BT" (Behavior Tree) or "DUMB" (Direct Chaser)

        # Build Behavior Tree
        self.blackboard = BTBlackboard()
        self.blackboard.boss = self
        self.bt_root = self._build_behavior_tree()

    def _build_behavior_tree(self) -> BTNode:
        """
        Constructs the hierarchical Behavior Tree for the Boss.
        Priority Hierarchy:
          [?] RootPrioritySelector
            |-- [->] Phase2EnrageCombo (HP <= 50%)
            |-- [->] CloseQuarterDefense (dist < 8.5m)
            |-- [->] PounceChargeAssault (dist 8.5..24m, LOS clear)
            |-- [->] LongRangeArtillery (dist > 13m)
            +-- [!] TacticalStalk (Fallback)
        """
        root = BTSelector("RootPrioritySelector")

        # Branch 1: Phase 2 Enrage Combo
        seq_enrage = BTSequence("Phase2EnrageCombo")
        seq_enrage.add_child(BTCondition("IsEnragedAndReady", cond_is_enraged_and_ready))
        seq_enrage.add_child(BTAction("ExecuteShockwaveSlam", act_shockwave_slam))
        root.add_child(seq_enrage)

        # Branch 2: Close-Range Defense
        seq_close = BTSequence("CloseQuarterDefense")
        seq_close.add_child(BTCondition("PlayerTooClose", cond_player_too_close))
        sel_melee = BTSelector("MeleeOptionSelector")

        seq_cleave = BTSequence("TailCleaveOption")
        seq_cleave.add_child(BTCondition("CleaveReady", cond_cleave_ready))
        seq_cleave.add_child(BTAction("PerformTailCleave", act_tail_cleave))
        sel_melee.add_child(seq_cleave)
        sel_melee.add_child(BTAction("DisengageHop", act_disengage_hop))
        seq_close.add_child(sel_melee)
        root.add_child(seq_close)

        # Branch 3: Pounce Charge
        seq_charge = BTSequence("PounceChargeAssault")
        seq_charge.add_child(BTCondition("CanPounceCharge", cond_can_pounce_charge))
        seq_charge.add_child(BTAction("ExecutePounceCharge", act_pounce_charge))
        root.add_child(seq_charge)

        # Branch 4: Long-Range Artillery
        seq_artillery = BTSequence("LongRangeArtillery")
        seq_artillery.add_child(BTCondition("CanFireArtillery", cond_can_artillery))
        seq_artillery.add_child(BTAction("FireTurretArtillery", act_fire_artillery))
        root.add_child(seq_artillery)

        # Branch 5: Tactical Stalk (Fallback)
        root.add_child(BTAction("TacticalStalk", act_tactical_stalk))

        return root

    def update(self, dt: float, player: PlayerMecha, arena: ColosseumArena,
               projectiles: ProjectilePool, particles: ParticlePool3D,
               sfx: SoundLibrary, shake: TraumaShake):
        self.anim_timer += dt

        # Smooth lagging chip health bar
        self.chip_hp = approach(self.chip_hp, self.hp, 60.0 * dt)

        # Tick tactical cooldowns
        if self.blackboard.slam_cooldown > 0.0:
            self.blackboard.slam_cooldown -= dt
        if self.blackboard.charge_cooldown > 0.0:
            self.blackboard.charge_cooldown -= dt
        if self.blackboard.artillery_cooldown > 0.0:
            self.blackboard.artillery_cooldown -= dt
        if self.blackboard.cleave_cooldown > 0.0:
            self.blackboard.cleave_cooldown -= dt

        # Update sensory perception on Blackboard
        dx = player.controller.pos.x - self.pos.x
        dz = player.controller.pos.z - self.pos.z
        dist = math.sqrt(dx * dx + dz * dz)
        self.blackboard.dist_to_player = dist
        if dist > 0.0001:
            self.blackboard.dir_to_player_x = dx / dist
            self.blackboard.dir_to_player_z = dz / dist
        self.blackboard.angle_to_player = math.atan2(dx, dz) * 180.0 / math.pi
        self.blackboard.is_enraged = (self.hp <= 300.0)

        # Line-of-sight raycast against cover pillars
        has_los = True
        for pillar in arena.pillars:
            p_closest = closest_point_on_segment_2d(
                Vector2(pillar.pos.x, pillar.pos.z),
                Vector2(self.pos.x, self.pos.z),
                Vector2(player.controller.pos.x, player.controller.pos.z)
            )
            p_dx = p_closest.x - pillar.pos.x
            p_dz = p_closest.y - pillar.pos.z
            if (p_dx * p_dx + p_dz * p_dz) < (pillar.radius * pillar.radius):
                has_los = False
                break
        self.blackboard.has_los = has_los

        # Context handles
        self.blackboard.player = player
        self.blackboard.arena = arena
        self.blackboard.projectiles = projectiles
        self.blackboard.particles = particles
        self.blackboard.sfx = sfx
        self.blackboard.shake = shake

        # AI Execution: Behavior Tree vs Dumb Direct Chaser
        if self.ai_mode == "BT":
            self.bt_root.tick(self.blackboard, dt)
        else:
            # DUMB AI: Blindly steers straight toward player, ignoring cover & tactical ranges
            self.blackboard.active_action_name = "DumbDirectSeek"
            self.blackboard.active_branch_name = "None"
            dumb_spd = 8.0
            self.facing_yaw = self.blackboard.angle_to_player
            self.pos.x += self.blackboard.dir_to_player_x * dumb_spd * dt
            self.pos.z += self.blackboard.dir_to_player_z * dumb_spd * dt

    def draw_3d(self):
        # Color palette shifts to Enraged Obsidian/Crimson in Phase 2
        palette = DEFAULT_BEAST_PALETTE
        if self.hp <= 300.0:
            palette = {
                "body": Color(45, 20, 20, 255),
                "plates": Color(95, 30, 25, 255),
                "joints": Color(25, 15, 15, 255),
                "horns": Color(255, 90, 40, 255),
                "eyes": Color(255, 20, 20, 255)
            }

        # 1. Quadruped Beast Locomotive Chassis
        draw_quadruped_beast_3d(
            self.pos,
            rotation_y=self.facing_yaw,
            anim_timer=self.anim_timer,
            scale=self.scale,
            palette=palette
        )

        # 2. Dorsal Heavy Artillery Turret mounted on upper carapace
        turret_mount_pos = Vector3(self.pos.x, self.pos.y + 1.4 * self.scale, self.pos.z)
        draw_turret_boss_3d(
            turret_mount_pos,
            yaw_deg=self.turret_yaw,
            pitch_deg=self.turret_pitch,
            anim_timer=self.anim_timer,
            scale=0.68 * self.scale
        )


# ==============================================================================
# BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAYS ([Tab], [F1], [F2])
# ==============================================================================

def draw_xray_telemetry(game):
    """
    Renders live Behavior Tree node hierarchy status badges, blackboard sensory data,
    and Kinematic Character Controller slide vectors.
    """
    bb = game.boss.blackboard

    # --------------------------------------------------------------------------
    # LEFT PANEL: BEHAVIOR TREE NODE HIERARCHY
    # --------------------------------------------------------------------------
    panel_x = 24
    panel_y = 75
    panel_w = 405
    panel_h = 515

    draw_rectangle(panel_x, panel_y, panel_w, panel_h, Color(10, 14, 24, 235))
    draw_rectangle_lines(panel_x, panel_y, panel_w, panel_h, Color(45, 75, 125, 255))

    draw_text("BEHAVIOR TREE X-RAY [Boss Titan]", panel_x + 14, panel_y + 12, 16, Color(70, 205, 255, 255))
    draw_text(f"Active Tactic: {bb.active_action_name}", panel_x + 14, panel_y + 32, 14, Color(255, 220, 90, 255))
    draw_line(panel_x + 10, panel_y + 52, panel_x + panel_w - 10, panel_y + 52, Color(40, 60, 90, 200))

    # Helper to render a node with status badge
    nodes_info = [
        ("?", "RootPrioritySelector", 0, game.boss.bt_root.status),
        ("->", "Phase2EnrageCombo", 1, game.boss.bt_root.children[0].status),
        ("C", "IsEnragedAndReady", 2, BT_SUCCESS if cond_is_enraged_and_ready(bb) else BT_FAILURE),
        ("!", "ExecuteShockwaveSlam", 2, act_status_display(bb, "ShockwaveSlam")),

        ("->", "CloseQuarterDefense", 1, game.boss.bt_root.children[1].status),
        ("C", "PlayerTooClose (<8.5m)", 2, BT_SUCCESS if cond_player_too_close(bb) else BT_FAILURE),
        ("?", "MeleeOptionSelector", 2, game.boss.bt_root.children[1].children[1].status),
        ("!", "PerformTailCleave", 3, act_status_display(bb, "TailCleave")),
        ("!", "DisengageHop", 3, act_status_display(bb, "DisengageHop")),

        ("->", "PounceChargeAssault", 1, game.boss.bt_root.children[2].status),
        ("C", "CanPounceCharge (LOS+CD)", 2, BT_SUCCESS if cond_can_pounce_charge(bb) else BT_FAILURE),
        ("!", "ExecutePounceCharge", 2, act_status_display(bb, "PounceCharge")),

        ("->", "LongRangeArtillery", 1, game.boss.bt_root.children[3].status),
        ("C", "CanFireArtillery (>13m)", 2, BT_SUCCESS if cond_can_artillery(bb) else BT_FAILURE),
        ("!", "FireTurretArtillery", 2, act_status_display(bb, "FireArtillery")),

        ("!", "TacticalStalk (Fallback)", 1, act_status_display(bb, "TacticalStalk")),
    ]

    curr_y = panel_y + 60
    for prefix, name, indent, status in nodes_info:
        indent_px = indent * 18
        badge_text = BT_STATUS_NAMES.get(status, "IDLE")
        badge_col = Color(120, 130, 150, 255)
        if status == BT_SUCCESS:
            badge_col = Color(50, 220, 110, 255)
        elif status == BT_FAILURE:
            badge_col = Color(240, 70, 70, 255)
        elif status == BT_RUNNING:
            badge_col = Color(255, 205, 40, 255)

        draw_text(f"[{prefix}] {name}", panel_x + 14 + indent_px, curr_y, 13, Color(220, 230, 245, 255))
        draw_text(f"[{badge_text}]", panel_x + panel_w - 75, curr_y, 11, badge_col)
        curr_y += 19

    # Blackboard Readouts
    draw_line(panel_x + 10, curr_y + 4, panel_x + panel_w - 10, curr_y + 4, Color(40, 60, 90, 200))
    curr_y += 12
    draw_text("BLACKBOARD SENSORY STATE:", panel_x + 14, curr_y, 12, Color(70, 205, 255, 255))
    curr_y += 16
    los_str = "CLEAR" if bb.has_los else "BLOCKED BY PILLAR"
    los_col = Color(50, 220, 110, 255) if bb.has_los else Color(240, 70, 70, 255)
    draw_text(f"Dist to Player: {bb.dist_to_player:.1f} m  | LOS: {los_str}", panel_x + 14, curr_y, 11, los_col)
    curr_y += 15
    phase_str = "Phase 2 (ENRAGED)" if bb.is_enraged else "Phase 1 (Tactical)"
    draw_text(f"Phase: {phase_str} | Slam CD: {bb.slam_cooldown:.1f}s", panel_x + 14, curr_y, 11, Color(200, 215, 235, 255))
    curr_y += 15
    draw_text(f"Charge CD: {bb.charge_cooldown:.1f}s | Artillery CD: {bb.artillery_cooldown:.1f}s", panel_x + 14, curr_y, 11, Color(200, 215, 235, 255))

    # --------------------------------------------------------------------------
    # RIGHT PANEL: KINEMATIC CHARACTER CONTROLLER TELEMETRY
    # --------------------------------------------------------------------------
    ctrl = game.player.controller
    p2_x = 985
    p2_y = 75
    p2_w = 270
    p2_h = 390

    draw_rectangle(p2_x, p2_y, p2_w, p2_h, Color(10, 14, 24, 235))
    draw_rectangle_lines(p2_x, p2_y, p2_w, p2_h, Color(45, 75, 125, 255))

    draw_text("KINEMATIC CONTROLLER", p2_x + 14, p2_y + 12, 16, Color(70, 205, 255, 255))
    draw_line(p2_x + 10, p2_y + 36, p2_x + p2_w - 10, p2_y + 36, Color(40, 60, 90, 200))

    r_y = p2_y + 46
    slide_status = "ENABLED (Slide)" if ctrl.slide_enabled else "DISABLED (Snag)"
    slide_col = Color(50, 220, 110, 255) if ctrl.slide_enabled else Color(240, 70, 70, 255)
    draw_text(f"Move-and-Slide [F2/L3]:", p2_x + 14, r_y, 12, Color(200, 210, 225, 255))
    draw_text(slide_status, p2_x + 14, r_y + 16, 13, slide_col)
    r_y += 38

    draw_text(f"Position: ({ctrl.pos.x:.1f}, {ctrl.pos.y:.1f}, {ctrl.pos.z:.1f})", p2_x + 14, r_y, 12, Color(200, 215, 235, 255))
    r_y += 20
    draw_text(f"Intended Vel: ({ctrl.intended_vel.x:.1f}, {ctrl.intended_vel.z:.1f})", p2_x + 14, r_y, 12, Color(200, 215, 235, 255))
    r_y += 20
    draw_text(f"Slide Vel:    ({ctrl.vel.x:.1f}, {ctrl.vel.z:.1f})", p2_x + 14, r_y, 12, Color(70, 205, 255, 255))
    r_y += 20
    draw_text(f"Contact N:    ({ctrl.contact_normal.x:.2f}, {ctrl.contact_normal.z:.2f})", p2_x + 14, r_y, 12, Color(255, 190, 60, 255) if ctrl.is_sliding else Color(120, 130, 140, 255))
    r_y += 20
    draw_text(f"Surface Sliding: {'YES' if ctrl.is_sliding else 'NO'}", p2_x + 14, r_y, 12, Color(255, 190, 60, 255) if ctrl.is_sliding else Color(140, 150, 160, 255))
    r_y += 20
    draw_text(f"Grounded: {'YES' if ctrl.is_grounded else 'AIRBORNE'}", p2_x + 14, r_y, 12, Color(50, 220, 110, 255) if ctrl.is_grounded else Color(0, 220, 255, 255))
    r_y += 26

    # Object Pool & Simultaneous Input Stats
    draw_line(p2_x + 10, r_y, p2_x + p2_w - 10, r_y, Color(40, 60, 90, 200))
    r_y += 10
    active_proj = 0
    for p in game.projectiles.pool:
        if p.active:
            active_proj += 1
    active_part = 0
    for p in game.particles.pool:
        if p.active:
            active_part += 1
    draw_text(f"Active Projectiles: {active_proj} / {game.projectiles.capacity}", p2_x + 14, r_y, 12, Color(200, 215, 235, 255))
    r_y += 18
    draw_text(f"Active 3D Particles: {active_part} / {game.particles.capacity}", p2_x + 14, r_y, 12, Color(200, 215, 235, 255))
    r_y += 18
    pad_label = get_active_gamepad_name()[:18] if is_any_gamepad_connected() else "None (KB/Mouse)"
    pad_col = Color(80, 235, 130, 255) if is_any_gamepad_connected() else Color(140, 150, 165, 255)
    draw_text(f"Gamepad: {pad_label}", p2_x + 14, r_y, 11, pad_col)


def act_status_display(bb: BTBlackboard, name: str) -> int:
    """Helper returning whether an action node is currently executing."""
    if bb.active_action_name == name:
        return BT_RUNNING
    return BT_SUCCESS


def draw_xray_3d_wireframes(game):
    """3D in-world wireframes showing collision hulls, radii, and line-of-sight feelers."""
    # 1. Player Kinematic Bounding Cylinder
    p_pos = game.player.controller.pos
    draw_cylinder_wires(
        Vector3(p_pos.x, p_pos.y + 1.1, p_pos.z),
        game.player.controller.radius,
        game.player.controller.radius,
        2.2, 12, Color(0, 255, 200, 180)
    )

    # 2. Boss Bounding Sphere / Cylinder
    b_pos = game.boss.pos
    draw_sphere_wires(
        Vector3(b_pos.x, b_pos.y + 1.4, b_pos.z),
        game.boss.radius,
        8, 12, Color(255, 80, 80, 180)
    )

    # 3. Line of Sight Feeler Raycast
    los_col = Color(50, 230, 100, 200) if game.boss.blackboard.has_los else Color(240, 60, 60, 200)
    draw_line_3d(
        Vector3(b_pos.x, b_pos.y + 1.5, b_pos.z),
        Vector3(p_pos.x, p_pos.y + 1.5, p_pos.z),
        los_col
    )

    # 4. Arena Boundary Wire Ring
    draw_cylinder_wires(Vector3(0.0, 1.0, 0.0), game.arena.radius, game.arena.radius, 2.0, 48, Color(0, 160, 255, 120))


# ==============================================================================
# BLOCK 4: MAIN GAME LOOP & AUTOMATED SMOKE TEST
# ==============================================================================

class MechaColosseumGame:
    """Complete 3D Mecha Arena Brawler Game Loop."""
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)

        # Procedural Audio System
        init_audio_device()
        self.sfx = SoundLibrary()
        self.sfx.init_defaults()
        self.music = SynthMusicPlayer()
        self.music.load_track(generate_action_track(bpm=130.0))
        self.music.play()
        self.music_enabled = True

        # Camera Rig & Trauma Shake
        self.camera = Camera3D(
            Vector3(0.0, 10.0, -32.0),
            Vector3(0.0, 1.5, -20.0),
            Vector3(0.0, 1.0, 0.0),
            52.0,
            CAMERA_PERSPECTIVE
        )
        self.cam_yaw = 0.0
        self.cam_pitch = 0.35
        self.cam_dist = 13.5
        self.shake = TraumaShake(max_offset_px=14.0, max_angle_deg=2.2, decay_rate=1.4)

        # World & Entities
        self.arena = ColosseumArena(radius=34.0)
        self.player = PlayerMecha(start_x=0.0, start_z=-20.0)
        self.boss = BossTitan(start_x=0.0, start_z=16.0)
        self.projectiles = ProjectilePool(capacity=120)
        self.particles = ParticlePool3D(capacity=200)

        # State & Learning Overlays
        self.show_xray = True
        self.match_state = "COMBAT"   # "COMBAT", "VICTORY", "DEFEAT"
        self.match_timer = 0.0

    def reset_match(self):
        self.player = PlayerMecha(start_x=0.0, start_z=-20.0)
        self.boss = BossTitan(start_x=0.0, start_z=16.0)
        self.projectiles.clear()
        self.match_state = "COMBAT"
        self.match_timer = 0.0
        self.sfx.play("click", 0.7)

    def handle_inputs(self, dt: float):
        # UI & Learning Toggles (Simultaneous Keyboard + Gamepad)
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
            self.sfx.play("click", 0.5)

        if is_dual_pattern_toggle_pressed():
            if self.boss.ai_mode == "BT":
                self.boss.ai_mode = "DUMB"
            else:
                self.boss.ai_mode = "BT"
            self.sfx.play("click", 0.6)

        if is_dual_secondary_toggle_pressed():
            self.player.controller.slide_enabled = not self.player.controller.slide_enabled
            self.sfx.play("click", 0.6)

        if is_key_pressed(KEY_M):
            self.music_enabled = not self.music_enabled
            self.sfx.play("click", 0.5)

        if is_dual_reset_pressed():
            self.reset_match()

        # Camera Orbiting: Right Mouse Drag OR Arrow Keys OR Gamepad Right Stick
        if is_mouse_button_down(MOUSE_BUTTON_RIGHT):
            m_delta = get_mouse_delta()
            self.cam_yaw -= m_delta.x * 0.005
            self.cam_pitch = max(0.12, min(1.25, self.cam_pitch + m_delta.y * 0.005))

        look_vec = get_dual_look_2d(deadzone=0.18, use_arrow_keys=True)
        if abs(look_vec.x) > 0.001:
            self.cam_yaw -= look_vec.x * 2.4 * dt
        if abs(look_vec.y) > 0.001:
            self.cam_pitch = max(0.12, min(1.25, self.cam_pitch + look_vec.y * 1.8 * dt))

        # Movement Inputs: WASD OR Gamepad Left Stick / D-Pad (relative to camera facing)
        cam_fwd_x = math.sin(self.cam_yaw)
        cam_fwd_z = math.cos(self.cam_yaw)
        cam_right_x = cam_fwd_z
        cam_right_z = -cam_fwd_x

        raw_move = get_dual_move_2d(deadzone=0.18, use_arrow_keys=False)
        # Inverted forward/backward per user preference:
        # raw_move.y < 0 means stick/W pushed forward, raw_move.x > 0 means right
        fwd_amt = raw_move.y
        right_amt = raw_move.x

        move_x = cam_fwd_x * fwd_amt + cam_right_x * right_amt
        move_z = cam_fwd_z * fwd_amt + cam_right_z * right_amt

        move_len = math.sqrt(move_x * move_x + move_z * move_z)
        if move_len > 1.0:
            move_x /= move_len
            move_z /= move_len

        # Actions (Simultaneous Keyboard/Mouse + Gamepad)
        is_boost_held = is_dual_jump_down()
        dash_requested = is_dual_dash_pressed()

        if self.match_state == "COMBAT":
            self.player.update(
                dt,
                Vector3(move_x, 0.0, move_z),
                is_boost_held,
                dash_requested,
                self.arena,
                self.boss,
                self.sfx,
                self.particles
            )

            # Weapon Firing: Primary Twin Plasma (Left Click / J OR Gamepad RT / RB / X)
            if is_dual_primary_fire_down() and self.player.primary_cooldown <= 0.0:
                self.player.primary_cooldown = 0.12
                self.player.arm_barrel_toggle = 1 - self.player.arm_barrel_toggle
                side = -0.7 if self.player.arm_barrel_toggle == 0 else 0.7

                # Muzzle position in world space
                yaw_rad = self.player.facing_yaw * math.pi / 180.0
                fx = math.sin(yaw_rad)
                fz = math.cos(yaw_rad)
                rx = fz
                rz = -fx

                muzzle_x = self.player.controller.pos.x + rx * side + fx * 0.9
                muzzle_y = self.player.controller.pos.y + 1.25
                muzzle_z = self.player.controller.pos.z + rz * side + fz * 0.9

                plasma_spd = 46.0
                vel = Vector3(fx * plasma_spd, 0.0, fz * plasma_spd)
                self.projectiles.spawn(
                    PROJ_PLAYER_PLASMA,
                    Vector3(muzzle_x, muzzle_y, muzzle_z),
                    vel,
                    radius=0.28,
                    life=2.0,
                    damage=12.0,
                    color=Color(0, 240, 255, 255)
                )
                self.sfx.play("laser", 0.5)

            # Secondary Weapon: Swarm Homing Missile (K / F OR Gamepad Y)
            if is_dual_secondary_fire_pressed() and self.player.secondary_cooldown <= 0.0:
                self.player.secondary_cooldown = 1.4
                yaw_rad = self.player.facing_yaw * math.pi / 180.0
                fx = math.sin(yaw_rad)
                fz = math.cos(yaw_rad)

                # Launch 2 missiles from shoulder pods
                for s in [-0.7, 0.7]:
                    start_pos = Vector3(
                        self.player.controller.pos.x + fz * s,
                        self.player.controller.pos.y + 1.8,
                        self.player.controller.pos.z - fx * s
                    )
                    v_init = Vector3(fx * 10.0, 8.0, fz * 10.0)
                    self.projectiles.spawn(
                        PROJ_PLAYER_ROCKET,
                        start_pos,
                        v_init,
                        radius=0.35,
                        life=3.5,
                        damage=38.0,
                        color=Color(255, 170, 30, 255)
                    )
                self.sfx.play("powerup", 0.7)

    def update_projectiles(self, dt: float):
        for p in self.projectiles.pool:
            if not p.active:
                continue

            p.life -= dt
            if p.life <= 0.0:
                p.active = False
                continue

            # Update projectile position
            if p.ptype == PROJ_PLAYER_PLASMA:
                p.pos.x += p.vel.x * dt
                p.pos.y += p.vel.y * dt
                p.pos.z += p.vel.z * dt

                # Hit Boss check
                if self.boss.hp > 0.0:
                    dx = p.pos.x - self.boss.pos.x
                    dy = p.pos.y - (self.boss.pos.y + 1.4)
                    dz = p.pos.z - self.boss.pos.z
                    if (dx * dx + dy * dy + dz * dz) < (self.boss.radius * self.boss.radius):
                        p.active = False
                        self.boss.hp = max(0.0, self.boss.hp - p.damage)
                        self.sfx.play("hit", 0.6)
                        self.particles.spawn_burst(p.pos, 6, Color(0, 240, 255, 255), 7.0, 0.3)

                # Hit Pillars check
                for pillar in self.arena.pillars:
                    dx = p.pos.x - pillar.pos.x
                    dz = p.pos.z - pillar.pos.z
                    if (dx * dx + dz * dz) < (pillar.radius * pillar.radius) and p.pos.y < pillar.height:
                        p.active = False
                        self.particles.spawn_burst(p.pos, 5, Color(70, 180, 255, 255), 6.0, 0.25)
                        break

            elif p.ptype == PROJ_PLAYER_ROCKET:
                # Homing logic toward boss
                if self.boss.hp > 0.0:
                    target_x = self.boss.pos.x
                    target_y = self.boss.pos.y + 1.4
                    target_z = self.boss.pos.z
                    to_x = target_x - p.pos.x
                    to_y = target_y - p.pos.y
                    to_z = target_z - p.pos.z
                    dist = math.sqrt(to_x * to_x + to_y * to_y + to_z * to_z)
                    if dist > 0.001:
                        spd = 24.0
                        turn_rate = 6.0 * dt
                        p.vel.x = lerp(p.vel.x, (to_x / dist) * spd, turn_rate)
                        p.vel.y = lerp(p.vel.y, (to_y / dist) * spd, turn_rate)
                        p.vel.z = lerp(p.vel.z, (to_z / dist) * spd, turn_rate)

                p.pos.x += p.vel.x * dt
                p.pos.y += p.vel.y * dt
                p.pos.z += p.vel.z * dt

                # Spawn smoke particle trail
                p.trail_timer += dt
                if p.trail_timer > 0.03:
                    p.trail_timer = 0.0
                    self.particles.spawn_burst(p.pos, 1, Color(200, 200, 200, 150), 1.5, 0.4)

                # Hit Boss check
                if self.boss.hp > 0.0:
                    dx = p.pos.x - self.boss.pos.x
                    dy = p.pos.y - (self.boss.pos.y + 1.4)
                    dz = p.pos.z - self.boss.pos.z
                    if (dx * dx + dy * dy + dz * dz) < (self.boss.radius * self.boss.radius):
                        p.active = False
                        self.boss.hp = max(0.0, self.boss.hp - p.damage)
                        self.sfx.play("explosion", 0.9)
                        self.shake.add_trauma(0.55)
                        self.particles.spawn_burst(p.pos, 28, Color(255, 160, 40, 255), 12.0, 0.6)

                # Ground or Pillar hit
                if p.pos.y <= 0.1:
                    p.active = False
                    self.sfx.play("explosion", 0.7)
                    self.particles.spawn_burst(p.pos, 18, Color(255, 140, 30, 255), 9.0, 0.45)

            elif p.ptype == PROJ_BOSS_MORTAR:
                p.vel.y -= 18.0 * dt  # Gravity
                p.pos.x += p.vel.x * dt
                p.pos.y += p.vel.y * dt
                p.pos.z += p.vel.z * dt

                # Floor Detonation
                if p.pos.y <= 0.1:
                    p.active = False
                    self.sfx.play("explosion", 0.85)
                    self.shake.add_trauma(0.4)
                    self.particles.spawn_burst(p.pos, 22, Color(255, 60, 40, 255), 10.0, 0.5)

                    # Area damage to player
                    dx = self.player.controller.pos.x - p.pos.x
                    dz = self.player.controller.pos.z - p.pos.z
                    if (dx * dx + dz * dz) < 18.0 and self.player.controller.pos.y < 2.0:
                        self.player.hp -= p.damage
                        self.sfx.play("hurt", 0.8)
                        self.shake.add_trauma(0.5)

            elif p.ptype == PROJ_BOSS_SHOCKWAVE:
                # Expands outward
                p.radius += 11.0 * dt
                if p.radius > 22.0:
                    p.active = False
                    continue

                # Hits player if player is grounded (jumping dodges it!)
                dx = self.player.controller.pos.x - p.pos.x
                dz = self.player.controller.pos.z - p.pos.z
                dist_p = math.sqrt(dx * dx + dz * dz)
                if abs(dist_p - p.radius) < 1.2 and self.player.controller.pos.y < 0.8:
                    p.active = False
                    self.player.hp -= p.damage
                    self.sfx.play("hurt", 0.9)
                    self.shake.add_trauma(0.65)
                    # Knock up and back
                    self.player.controller.vel.y = 12.0

    def update(self):
        dt = min(get_frame_time(), 0.05)
        self.match_timer += dt

        # Audio updates
        if self.music_enabled:
            self.music.update()

        # Handle keyboard/mouse inputs
        self.handle_inputs(dt)

        # Update Boss & Entities
        if self.match_state == "COMBAT":
            self.boss.update(
                dt,
                self.player,
                self.arena,
                self.projectiles,
                self.particles,
                self.sfx,
                self.shake
            )
            self.update_projectiles(dt)

            # Check Match Victory / Defeat Conditions
            if self.boss.hp <= 0.0:
                self.match_state = "VICTORY"
                self.sfx.play("powerup", 1.0)
                self.particles.spawn_burst(self.boss.pos, 60, Color(255, 215, 0, 255), 16.0, 1.2)
            elif self.player.hp <= 0.0:
                self.match_state = "DEFEAT"
                self.sfx.play("explosion", 1.0)
                self.shake.add_trauma(0.8)

        self.particles.update(dt)

        # Update Camera Follow & Trauma Screen Shake
        cam_target = Vector3(
            self.player.controller.pos.x,
            self.player.controller.pos.y + 1.6,
            self.player.controller.pos.z
        )
        cam_off_x = math.sin(self.cam_yaw) * math.cos(self.cam_pitch) * self.cam_dist
        cam_off_y = math.sin(self.cam_pitch) * self.cam_dist
        cam_off_z = math.cos(self.cam_yaw) * math.cos(self.cam_pitch) * self.cam_dist

        desired_cam_pos = Vector3(
            self.player.controller.pos.x + cam_off_x,
            self.player.controller.pos.y + cam_off_y,
            self.player.controller.pos.z + cam_off_z
        )

        self.camera.position = damp_v3(self.camera.position, desired_cam_pos, 12.0, dt)
        self.camera.target = damp_v3(self.camera.target, cam_target, 14.0, dt)

        # Apply Trauma Screen Shake to Camera
        shake_dx, shake_dy, _ = self.shake.update(dt)
        self.camera.target.x += shake_dx * 0.04
        self.camera.target.y += shake_dy * 0.04

    def draw(self):
        begin_drawing()
        clear_background(Color(10, 12, 20, 255))

        # =====================================================================
        # 3D WORLD RENDERING PASS
        # =====================================================================
        begin_mode_3d(self.camera)

        # 1. Colosseum Arena & Pillars
        self.arena.draw_3d()

        # 2. Boss Titan Behemoth
        if self.boss.hp > 0.0:
            self.boss.draw_3d()

        # 3. Player Mecha
        if self.player.hp > 0.0:
            self.player.draw_3d()

        # 4. Projectiles in 3D Space
        for p in self.projectiles.pool:
            if p.active:
                if p.ptype == PROJ_PLAYER_PLASMA:
                    draw_sphere(p.pos, p.radius, p.color)
                elif p.ptype == PROJ_PLAYER_ROCKET:
                    draw_cube(p.pos, p.radius * 2.0, p.radius * 2.0, p.radius * 3.5, p.color)
                    draw_sphere(p.pos, p.radius * 1.2, Color(255, 230, 120, 255))
                elif p.ptype == PROJ_BOSS_MORTAR:
                    draw_sphere(p.pos, p.radius, p.color)
                    draw_sphere_wires(p.pos, p.radius * 1.3, 6, 8, Color(255, 180, 50, 200))
                    # Ground warning shadow indicator
                    draw_cylinder(Vector3(p.pos.x, 0.05, p.pos.z), 1.6, 1.6, 0.02, 16, Color(255, 40, 40, 140))
                elif p.ptype == PROJ_BOSS_SHOCKWAVE:
                    draw_cylinder_wires(Vector3(p.pos.x, 0.1, p.pos.z), p.radius, p.radius, 0.4, 32, p.color)
                    draw_cylinder_wires(Vector3(p.pos.x, 0.1, p.pos.z), max(0.1, p.radius - 0.4), max(0.1, p.radius - 0.4), 0.4, 32, Color(255, 180, 40, 180))

        # 5. 3D Particles
        self.particles.draw()

        # 6. Optional X-Ray 3D Wireframes
        if self.show_xray:
            draw_xray_3d_wireframes(self)

        end_mode_3d()

        # =====================================================================
        # 2D HUD & PEDAGOGICAL TELEMETRY PASS
        # =====================================================================

        # 1. Boss Epic Health Bar (kept below dropdown y=14..48 bar at y=54)
        bar_x = 340
        bar_y = 54
        bar_w = 600
        bar_h = 16

        draw_rectangle(bar_x - 4, bar_y - 2, bar_w + 8, bar_h + 4, Color(15, 20, 30, 220))
        draw_rectangle_lines(bar_x - 4, bar_y - 2, bar_w + 8, bar_h + 4, Color(60, 80, 120, 255))

        # Lagging chip health bar
        chip_pct = max(0.0, min(1.0, self.boss.chip_hp / self.boss.max_hp))
        draw_rectangle(bar_x, bar_y, int(bar_w * chip_pct), bar_h, Color(240, 240, 240, 255))

        # Active health bar
        hp_pct = max(0.0, min(1.0, self.boss.hp / self.boss.max_hp))
        boss_hp_col = Color(230, 40, 50, 255) if self.boss.hp > 300.0 else Color(255, 80, 20, 255)
        draw_rectangle(bar_x, bar_y, int(bar_w * hp_pct), bar_h, boss_hp_col)

        draw_text("TITAN BEHEMOTH [COLOSSEUM CHAMPION]", bar_x + 8, bar_y - 18, 14, Color(255, 215, 120, 255))
        draw_text(f"{int(self.boss.hp)} / {int(self.boss.max_hp)}", bar_x + bar_w - 90, bar_y - 18, 14, Color(230, 235, 245, 255))

        # 2. Player Health & Boost Energy Gauges (Bottom-Left)
        p_hud_x = 24
        p_hud_y = 620
        draw_rectangle(p_hud_x - 4, p_hud_y - 4, 250, 68, Color(12, 16, 26, 220))
        draw_rectangle_lines(p_hud_x - 4, p_hud_y - 4, 250, 68, Color(45, 70, 110, 255))

        # Player HP Bar
        p_hp_pct = max(0.0, min(1.0, self.player.hp / self.player.max_hp))
        draw_rectangle(p_hud_x, p_hud_y, 240, 14, Color(30, 35, 45, 255))
        draw_rectangle(p_hud_x, p_hud_y, int(240 * p_hp_pct), 14, Color(40, 220, 110, 255))
        draw_text(f"HULL INTEGRITY  {int(self.player.hp)}%", p_hud_x + 6, p_hud_y + 1, 10, Color(255, 255, 255, 255))

        # Boost / Jetpack Fuel Bar
        boost_pct = max(0.0, min(1.0, self.player.boost_energy / self.player.max_boost_energy))
        draw_rectangle(p_hud_x, p_hud_y + 20, 240, 12, Color(30, 35, 45, 255))
        draw_rectangle(p_hud_x, p_hud_y + 20, int(240 * boost_pct), 12, Color(0, 200, 255, 255))
        draw_text(f"THRUSTER FUEL   {int(self.player.boost_energy)}%", p_hud_x + 6, p_hud_y + 21, 9, Color(255, 255, 255, 255))

        # Dash & Rocket Status
        dash_ready = self.player.dash_cooldown <= 0.0 and self.player.boost_energy >= 30.0
        rocket_ready = self.player.secondary_cooldown <= 0.0
        draw_text("DASH [Shift/B]:", p_hud_x, p_hud_y + 40, 11, Color(200, 210, 225, 255))
        draw_text("READY" if dash_ready else "COOLING", p_hud_x + 92, p_hud_y + 40, 11, Color(50, 220, 110, 255) if dash_ready else Color(240, 80, 80, 255))

        draw_text("ROCKET [K/Y]:", p_hud_x + 144, p_hud_y + 40, 11, Color(200, 210, 225, 255))
        draw_text("READY" if rocket_ready else "RELOAD", p_hud_x + 216, p_hud_y + 40, 11, Color(50, 220, 110, 255) if rocket_ready else Color(240, 80, 80, 255))

        # 3. Top Banner AI Mode, Slide Mode & Simultaneous Gamepad Status
        mode_str = "BEHAVIOR TREE (Smart Tactical)" if self.boss.ai_mode == "BT" else "DUMB DIRECT CHASER (No BT)"
        mode_col = Color(50, 220, 110, 255) if self.boss.ai_mode == "BT" else Color(255, 170, 40, 255)
        draw_text(f"[F1/R3] AI BRAIN: {mode_str}", 24, 20, 13, mode_col)

        slide_str = "KINEMATIC MOVE-AND-SLIDE [ON]" if self.player.controller.slide_enabled else "DIRECT SNAG (No Slide) [OFF]"
        slide_col = Color(0, 220, 255, 255) if self.player.controller.slide_enabled else Color(240, 70, 70, 255)
        draw_text(f"[F2/L3] {slide_str}", 24, 38, 12, slide_col)

        draw_gamepad_status_badge(985, 22, 11)

        # 4. Interactive Learning Controls Footer
        footer_text = "WASD/L-Stick: Move | R-Mouse/Arrows/R-Stick: Orbit | Space/A: Boost | Shift/B: Dash | Click/J/RT: Plasma | K/Y: Rocket | Tab/Select: X-Ray | R/Start: Reset"
        draw_text(footer_text, 18, 700, 11, Color(160, 180, 210, 255))

        # 5. Victory / Defeat Overlay Modals
        if self.match_state == "VICTORY":
            draw_rectangle(SCREEN_WIDTH // 2 - 250, 260, 500, 150, Color(12, 18, 30, 240))
            draw_rectangle_lines(SCREEN_WIDTH // 2 - 250, 260, 500, 150, Color(50, 220, 120, 255))
            draw_text("VICTORY! COLOSSEUM CHAMPION", SCREEN_WIDTH // 2 - 200, 285, 22, Color(255, 220, 50, 255))
            draw_text("The Titan Behemoth has fallen to your Mecha!", SCREEN_WIDTH // 2 - 170, 320, 14, Color(220, 235, 255, 255))
            draw_text("Press [R] or [Start] to Rematch the Titan", SCREEN_WIDTH // 2 - 140, 360, 15, Color(70, 205, 255, 255))
        elif self.match_state == "DEFEAT":
            draw_rectangle(SCREEN_WIDTH // 2 - 250, 260, 500, 150, Color(25, 12, 16, 240))
            draw_rectangle_lines(SCREEN_WIDTH // 2 - 250, 260, 500, 150, Color(240, 60, 70, 255))
            draw_text("CRITICAL HULL BREACH", SCREEN_WIDTH // 2 - 145, 285, 22, Color(255, 60, 70, 255))
            draw_text("Your Mecha was destroyed in the Colosseum.", SCREEN_WIDTH // 2 - 165, 320, 14, Color(240, 220, 220, 255))
            draw_text("Press [R] or [Start] to Rebuild and Retry", SCREEN_WIDTH // 2 - 140, 360, 15, Color(255, 180, 50, 255))

        # 6. Detailed X-Ray Telemetry Panels ([Tab])
        if self.show_xray:
            draw_xray_telemetry(self)

        # 7. Global Top-Bar Dropdown Settings Bar (x=450..980, y=16..46)
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

        # Shutdown & Cleanup
        self.sfx.unload_all()
        self.music.unload()
        close_audio_device()
        close_window()


if __name__ == "__main__":
    is_smoke = "--smoke-test" in sys.argv
    MechaColosseumGame().run(smoke_test=is_smoke)
