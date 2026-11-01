# -*- coding: utf-8 -*-
"""
Space Swarm - 2D Bullet Hell & Swarm Survival Minigame
======================================================
Section          : 3.0 Core Multi-Pattern Prototypes
Pattern Category : Core Multi-Pattern, Object Pool, Spatial Partitioning
Dimension        : 2D

A fast-paced retro 2D arcade shooter built with Raylib Python (`pyray`).

Design Patterns Demonstrated:
  1. Object Pool Pattern: Fixed pools for player bullets, enemy bullet hell patterns,
     and explosion particles to ensure zero garbage collection stutter.
  2. Spatial Partitioning Pattern: SpatialGrid2D for broadphase collision queries
     between bullets, swarm enemies, and the player.
  3. Camera Rig & Trauma Screen Shake: Dynamic quadratic screen shake on impacts
     and explosions using the Trauma model.
  4. State Machine Pattern (FSM): Clean transitions across TITLE, PLAYING, GAMEOVER,
     and VICTORY states.
  5. Wave Director / Pacing Pattern: Staged enemy swarm deployment with escalating
     bullet hell projectile patterns (aimed bolts, radial rings, sweeping spirals).
  6. Procedural Primitive Assembler: Player starship, shields, and thrusters rendered
     with 2D geometric shapes, combining with procedural drone enemies from assets.
  7. Procedural Audio Synthesis: In-memory SFX library and background combat soundtrack.

Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - WASD / Arrows / Left Stick / D-Pad : Move starship
  - Left Shift / Gamepad LB / LT / B   : Focus mode (slows ship for precision dodging, shows hitbox)
  - Space / J / L-Click / Gamepad A/RT : Rapid-fire plasma lasers
  - Tab / Gamepad View (Select)        : Toggle X-Ray Pattern Telemetry & Spatial Grid Overlay
  - F1 / Gamepad R3                    : Toggle Trauma Screen Shake ON/OFF
  - Ctrl + '+' / '-'                   : Increase / Decrease UI Font Size
  - F11                                : Toggle Fullscreen
  - M                                  : Toggle BGM sound
  - R / Gamepad Start                  : Restart game (on Game Over / Victory)
"""

import sys
import os
import math
import random

# ==============================================================================
# MANDATORY STEP 0 & PRE-FLIGHT REPOSITORY RULES
# ==============================================================================

# 1. Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# 2. Add repository root to search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 3. Mandatory Raylib & modular workspace imports
from pyray import *
from assets import *
from utils import *

# ==============================================================================
# CONFIGURATION & CONSTANTS
# ==============================================================================

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WINDOW_TITLE = "Space Swarm - Bullet Hell Prototype (Raylib)"

# Colors
COLOR_BG = Color(8, 10, 18, 255)
COLOR_GRID = Color(18, 22, 36, 120)
COLOR_PLAYER_HULL = Color(40, 200, 255, 255)
COLOR_PLAYER_CORE = Color(240, 250, 255, 255)
COLOR_PLAYER_HITBOX = Color(255, 50, 50, 255)
COLOR_PLAYER_BULLET = Color(80, 240, 255, 255)
COLOR_ENEMY_BULLET = Color(255, 70, 90, 255)
COLOR_ENEMY_BULLET_CORE = Color(255, 220, 220, 255)
COLOR_SHIELD = Color(0, 180, 255, 180)

# ==============================================================================
# OBJECT POOLING SYSTEM (PATTERN 1: OBJECT POOL)
# ==============================================================================

class Bullet:
    """
    Pre-allocated projectile object reused in bullet pools.
    C++ Equivalent: struct Bullet { bool active; Vector2 pos; Vector2 vel; float radius; Color color; bool is_enemy; };
    """
    def __init__(self):
        self.active = False
        self.pos = Vector2(0.0, 0.0)
        self.vel = Vector2(0.0, 0.0)
        self.radius = 4.0
        self.color = COLOR_PLAYER_BULLET
        self.is_enemy = False

class BulletPool:
    """
    Object Pool for projectiles. Pre-allocates memory upfront to eliminate
    allocations, memory fragmentation, and garbage collection hitches during combat.
    C++ Equivalent: std::array<Bullet, 600> pool;
    """
    def __init__(self, capacity: int = 600):
        self.capacity = capacity
        self.pool = []
        for _ in range(capacity):
            self.pool.append(Bullet())

    def spawn(self, x: float, y: float, vx: float, vy: float, radius: float, color: Color, is_enemy: bool = False) -> Bullet:
        """Finds the first inactive bullet in the pool and activates it."""
        for b in self.pool:
            if not b.active:
                b.active = True
                b.pos.x = x
                b.pos.y = y
                b.vel.x = vx
                b.vel.y = vy
                b.radius = radius
                b.color = color
                b.is_enemy = is_enemy
                return b
        return None # Pool exhausted

    def update(self, dt: float):
        """Advances active bullets and recycles those that leave the screen."""
        for b in self.pool:
            if b.active:
                b.pos.x += b.vel.x * dt
                b.pos.y += b.vel.y * dt
                # Boundary check with margin
                if b.pos.x < -30 or b.pos.x > SCREEN_WIDTH + 30 or b.pos.y < -30 or b.pos.y > SCREEN_HEIGHT + 30:
                    b.active = False

    def draw(self):
        """Renders all active projectiles with luminous glowing rings."""
        for b in self.pool:
            if b.active:
                bx, by = int(b.pos.x), int(b.pos.y)
                # Outer glow ring
                draw_circle(bx, by, b.radius + 1.5, b.color)
                # Inner white core for luminous bullet-hell clarity
                draw_circle(bx, by, max(1.0, b.radius * 0.5), WHITE)

    def clear(self):
        """Recycles all bullets instantly."""
        for b in self.pool:
            b.active = False


class Particle:
    """Pre-allocated spark/debris particle."""
    def __init__(self):
        self.active = False
        self.pos = Vector2(0.0, 0.0)
        self.vel = Vector2(0.0, 0.0)
        self.life = 0.0
        self.max_life = 0.5
        self.size = 2.0
        self.color = WHITE

class ParticlePool:
    """
    Object Pool for visual hit sparks, thruster trails, and explosions.
    C++ Equivalent: std::array<Particle, 400> pool;
    """
    def __init__(self, capacity: int = 400):
        self.capacity = capacity
        self.pool = []
        for _ in range(capacity):
            self.pool.append(Particle())

    def emit_burst(self, x: float, y: float, count: int, speed: float, color: Color, max_life: float = 0.6):
        spawned = 0
        for p in self.pool:
            if not p.active:
                p.active = True
                p.pos.x = x
                p.pos.y = y
                angle = random.random() * math.pi * 2.0
                spd = speed * (0.3 + 0.7 * random.random())
                p.vel.x = math.cos(angle) * spd
                p.vel.y = math.sin(angle) * spd
                p.life = 0.0
                p.max_life = max_life * (0.5 + 0.5 * random.random())
                p.size = random.uniform(2.0, 4.5)
                p.color = color
                spawned += 1
                if spawned >= count:
                    break

    def update(self, dt: float):
        for p in self.pool:
            if p.active:
                p.life += dt
                if p.life >= p.max_life:
                    p.active = False
                else:
                    p.pos.x += p.vel.x * dt
                    p.pos.y += p.vel.y * dt
                    # Drag / friction
                    p.vel.x *= 0.94
                    p.vel.y *= 0.94

    def draw(self):
        for p in self.pool:
            if p.active:
                alpha = 1.0 - (p.life / p.max_life)
                c = Color(p.color.r, p.color.g, p.color.b, int(255 * alpha))
                curr_size = p.size * alpha
                draw_circle(int(p.pos.x), int(p.pos.y), max(1.0, curr_size), c)

    def clear(self):
        for p in self.pool:
            p.active = False


# ==============================================================================
# PROCEDURAL BACKGROUND (PARALLAX STARFIELD)
# ==============================================================================

class Starfield:
    """Multi-layer procedural parallax starfield."""
    def __init__(self, count: int = 140):
        self.stars = []
        for _ in range(count):
            self.stars.append({
                "x": random.uniform(0, SCREEN_WIDTH),
                "y": random.uniform(0, SCREEN_HEIGHT),
                "speed": random.uniform(20.0, 110.0),
                "size": random.uniform(1.0, 2.5),
                "color": Color(random.randint(140, 220), random.randint(160, 240), 255, random.randint(120, 240))
            })

    def update(self, dt: float):
        for s in self.stars:
            s["y"] += s["speed"] * dt
            if s["y"] > SCREEN_HEIGHT:
                s["y"] = 0.0
                s["x"] = random.uniform(0, SCREEN_WIDTH)

    def draw(self):
        for s in self.stars:
            draw_circle(int(s["x"]), int(s["y"]), s["size"], s["color"])


# ==============================================================================
# PLAYER STARSHIP (PROCEDURAL PRIMITIVE ASSEMBLER)
# ==============================================================================

class PlayerShip:
    """
    Player-controlled starship assembled from 2D primitives.
    Demonstrates Kinematic movement, focus mode, and precise hitbox logic.
    """
    def __init__(self, x: float, y: float):
        self.pos = Vector2(x, y)
        self.base_speed = 360.0
        self.focus_speed = 170.0
        self.hitbox_radius = 4.5  # Authentic bullet hell pinpoint hitbox
        self.visual_radius = 18.0
        self.health = 3
        self.max_health = 3
        self.fire_timer = 0.0
        self.fire_rate = 0.08     # 12.5 shots per second
        self.invulnerable_timer = 0.0
        self.tilt_angle = 0.0

    def update(self, dt: float, bullet_pool: BulletPool, particle_pool: ParticlePool, sfx: SoundLibrary):
        # 1. Focus Mode (Shift OR Gamepad LB / LT / B)
        is_focused = is_dual_dash_down()
        current_speed = self.focus_speed if is_focused else self.base_speed

        # 2. Movement Inputs (Simultaneous WASD / Arrows + Gamepad Left Stick / D-Pad)
        move_vec = get_dual_move_2d(deadzone=0.18, use_arrow_keys=True)
        move_x = move_vec.x * current_speed
        move_y = move_vec.y * current_speed

        self.pos.x += move_x * dt
        self.pos.y += move_y * dt

        # Screen boundaries clamping
        self.pos.x = clamp(self.pos.x, 24.0, SCREEN_WIDTH - 24.0)
        self.pos.y = clamp(self.pos.y, 30.0, SCREEN_HEIGHT - 30.0)

        # Ship banking tilt
        target_tilt = (move_x / current_speed) * 0.25
        self.tilt_angle = damp(self.tilt_angle, target_tilt, 14.0, dt)

        # 3. Weapons Fire (Simultaneous Space / J / L-Click + Gamepad A / X / RB / RT)
        self.fire_timer -= dt
        wants_to_fire = is_dual_primary_fire_down() or is_dual_jump_down()
        if wants_to_fire and self.fire_timer <= 0.0:
            self.fire_timer = self.fire_rate
            # Dual wing blaster cannons
            wing_span = 12.0
            bullet_speed = 880.0
            bullet_pool.spawn(self.pos.x - wing_span, self.pos.y - 10.0, 0.0, -bullet_speed, 4.0, COLOR_PLAYER_BULLET, is_enemy=False)
            bullet_pool.spawn(self.pos.x + wing_span, self.pos.y - 10.0, 0.0, -bullet_speed, 4.0, COLOR_PLAYER_BULLET, is_enemy=False)
            
            # Subtle thruster sparks
            particle_pool.emit_burst(self.pos.x, self.pos.y + 14.0, 2, 40.0, Color(0, 180, 255, 200), 0.2)
            sfx.play("laser", 0.35)

        # 4. Invulnerability Timer
        if self.invulnerable_timer > 0.0:
            self.invulnerable_timer -= dt

    def take_hit(self, particle_pool: ParticlePool, sfx: SoundLibrary, shake: TraumaShake) -> bool:
        """Applies damage if not currently in temporary invulnerability."""
        if self.invulnerable_timer > 0.0:
            return False
            
        self.health -= 1
        self.invulnerable_timer = 1.6
        particle_pool.emit_burst(self.pos.x, self.pos.y, 25, 200.0, COLOR_PLAYER_HULL, 0.5)
        shake.add_trauma(0.55) # Punchy trauma screen shake
        sfx.play("hurt", 0.8)
        return True

    def draw(self, is_focused: bool):
        # Flashing opacity during invulnerability
        if self.invulnerable_timer > 0.0 and int(get_time() * 20) % 2 == 0:
            return

        cx, cy = self.pos.x, self.pos.y
        sin_t = math.sin(self.tilt_angle)
        cos_t = math.cos(self.tilt_angle)

        # --- Procedural Thruster Plume ---
        flicker = random.uniform(12.0, 20.0)
        t_tip = Vector2(cx, cy + flicker)
        t_l = Vector2(cx - 5.0, cy + 8.0)
        t_r = Vector2(cx + 5.0, cy + 8.0)
        draw_triangle(t_tip, t_r, t_l, Color(255, 140, 0, 220))
        draw_circle(int(cx), int(cy + 8.0), 3.5, Color(255, 230, 100, 255))

        # --- Starship Hull (Aggressive Sci-Fi Interceptor Triangles) ---
        nose = Vector2(cx, cy - 20.0)
        wing_l = Vector2(cx - 18.0 * cos_t, cy + 12.0)
        wing_r = Vector2(cx + 18.0 * cos_t, cy + 12.0)
        tail_center = Vector2(cx, cy + 4.0)

        # Wings & Fuselage
        draw_triangle(nose, wing_r, tail_center, COLOR_PLAYER_HULL)
        draw_triangle(nose, tail_center, wing_l, Color(30, 150, 210, 255))
        draw_circle(int(cx), int(cy - 2.0), 6.5, COLOR_PLAYER_CORE)

        # Wingtip Cannons
        draw_rectangle(int(cx - 14.0 * cos_t) - 2, int(cy - 2), 4, 10, COLOR_GRID)
        draw_rectangle(int(cx + 14.0 * cos_t) - 2, int(cy - 2), 4, 10, COLOR_GRID)

        # --- Focus Mode Precise Hitbox Overlay ---
        if is_focused:
            # Concentric glowing targeting rings around the true 4.5px hitbox
            draw_circle(int(cx), int(cy), self.hitbox_radius, COLOR_PLAYER_HITBOX)
            draw_circle_lines(int(cx), int(cy), self.hitbox_radius + 4.0, Color(255, 255, 255, 180))


# ==============================================================================
# ENEMY SWARM UNITS & BULLET PATTERN CONTROLLERS
# ==============================================================================

class EnemyDrone:
    """
    Swarm enemy unit rendered with procedural primitives.
    Executes various bullet patterns (aimed, radial rings, spiral curtains).
    """
    def __init__(self, x: float, y: float, drone_type: str = "scout"):
        self.pos = Vector2(x, y)
        self.type = drone_type
        self.active = True
        self.anim_timer = random.uniform(0.0, 10.0)
        self.fire_timer = random.uniform(0.5, 1.8)
        self.time_alive = 0.0

        if self.type == "scout":
            self.radius = 16.0
            self.max_hp = 3
            self.hp = 3
            self.score_value = 100
            self.fire_interval = 1.4
            self.speed = 140.0
            self.palette = DEFAULT_FLYING_PALETTE
        elif self.type == "sentinel":
            self.radius = 24.0
            self.max_hp = 14
            self.hp = 14
            self.score_value = 450
            self.fire_interval = 1.9
            self.speed = 70.0
            # Red/Gold armored heavy palette
            self.palette = {
                "body": Color(85, 30, 45, 255),
                "wing": Color(190, 60, 60, 255),
                "eye": Color(255, 200, 0, 255),
                "pupil": Color(20, 20, 20, 255)
            }
        elif self.type == "boss":
            self.radius = 38.0
            self.max_hp = 110
            self.hp = 110
            self.score_value = 2500
            self.fire_interval = 0.9
            self.speed = 50.0
            self.palette = {
                "body": Color(40, 25, 60, 255),
                "wing": Color(220, 50, 200, 255),
                "eye": Color(0, 240, 255, 255),
                "pupil": Color(255, 255, 255, 255)
            }

    def update(self, dt: float, player_pos: Vector2, bullet_pool: BulletPool, sfx: SoundLibrary):
        self.anim_timer += dt
        self.time_alive += dt
        self.fire_timer -= dt

        # --- Movement Patterns ---
        if self.type == "scout":
            # Sinusoidal swooping wave
            self.pos.y += self.speed * dt
            self.pos.x += math.sin(self.time_alive * 2.8 + self.pos.y * 0.01) * 110.0 * dt
            if self.pos.y > SCREEN_HEIGHT + 40:
                self.active = False

        elif self.type == "sentinel":
            # Enter from top, hover in place, weave horizontally
            target_y = 160.0 + (self.radius * 2.0)
            if self.pos.y < target_y:
                self.pos.y = approach(self.pos.y, target_y, self.speed * dt)
            else:
                self.pos.x += math.cos(self.time_alive * 1.5) * 80.0 * dt

        elif self.type == "boss":
            # Commander Boss: Smooth figure-8 holding pattern at top
            target_y = 150.0
            if self.pos.y < target_y:
                self.pos.y = approach(self.pos.y, target_y, 45.0 * dt)
            else:
                self.pos.x = (SCREEN_WIDTH / 2.0) + math.sin(self.time_alive * 0.8) * 360.0
                self.pos.y = target_y + math.sin(self.time_alive * 1.6) * 45.0

        # Keep on screen horizontally
        self.pos.x = clamp(self.pos.x, self.radius + 20.0, SCREEN_WIDTH - self.radius - 20.0)

        # --- Bullet Hell Attack Patterns ---
        if self.fire_timer <= 0.0 and self.pos.y > 0 and self.pos.y < SCREEN_HEIGHT - 60:
            self.fire_timer = self.fire_interval
            self._fire_pattern(player_pos, bullet_pool, sfx)

    def _fire_pattern(self, player_pos: Vector2, bullet_pool: BulletPool, sfx: SoundLibrary):
        """Dispatches distinctive geometric bullet patterns based on enemy archetype."""
        if self.type == "scout":
            # Direct Aimed Laser Bolt toward player
            angle = math.atan2(player_pos.y - self.pos.y, player_pos.x - self.pos.x)
            spd = 280.0
            bullet_pool.spawn(self.pos.x, self.pos.y + self.radius,
                              math.cos(angle) * spd, math.sin(angle) * spd,
                              4.5, COLOR_ENEMY_BULLET, is_enemy=True)

        elif self.type == "sentinel":
            # Radial 8-Way Ring Pattern
            arms = 8
            spd = 200.0
            base_rot = self.time_alive * 1.2 # Rotates gradually each shot
            for i in range(arms):
                a = base_rot + (i * (2.0 * math.pi / arms))
                bullet_pool.spawn(self.pos.x, self.pos.y,
                                  math.cos(a) * spd, math.sin(a) * spd,
                                  5.0, COLOR_ENEMY_BULLET, is_enemy=True)

        elif self.type == "boss":
            # Dual Pattern: Alternating Sweeping Spiral & Direct Triple Spread
            pattern_cycle = int(self.time_alive * 2.0) % 2
            if pattern_cycle == 0:
                # 12-way expanding blossom ring
                arms = 12
                spd = 210.0
                offset = math.sin(self.time_alive * 4.0)
                for i in range(arms):
                    a = offset + (i * (2.0 * math.pi / arms))
                    bullet_pool.spawn(self.pos.x, self.pos.y,
                                      math.cos(a) * spd, math.sin(a) * spd,
                                      5.5, COLOR_ENEMY_BULLET, is_enemy=True)
            else:
                # High-speed targeted 3-way shotgun spread
                base_angle = math.atan2(player_pos.y - self.pos.y, player_pos.x - self.pos.x)
                spd = 340.0
                for spread in [-0.22, 0.0, 0.22]:
                    a = base_angle + spread
                    bullet_pool.spawn(self.pos.x, self.pos.y,
                                      math.cos(a) * spd, math.sin(a) * spd,
                                      5.0, Color(255, 140, 50, 255), is_enemy=True)

    def draw(self):
        # Procedural visual rendering directly utilizing assets module
        draw_flying_drone_2d(self.pos, self.anim_timer, self.radius, self.palette)

        # Health bar for heavy enemies and boss
        if self.type in ("sentinel", "boss") and self.hp < self.max_hp:
            bar_w = self.radius * 2.2
            bar_h = 5.0
            bx = self.pos.x - bar_w * 0.5
            by = self.pos.y - self.radius - 12.0
            draw_rectangle(int(bx), int(by), int(bar_w), int(bar_h), Color(40, 40, 40, 200))
            hp_w = bar_w * (self.hp / self.max_hp)
            draw_rectangle(int(bx), int(by), int(hp_w), int(bar_h), Color(255, 50, 70, 255))


# ==============================================================================
# WAVE DIRECTOR & STAGING (PATTERN 5: SPAWN DIRECTOR)
# ==============================================================================

class WaveDirector:
    """Controls progression, pacing, and staging of enemy waves."""
    def __init__(self):
        self.current_wave = 1
        self.wave_timer = 0.0
        self.spawn_queue = []
        self.wave_active = False
        self.wave_complete_banner_timer = 0.0
        self.all_waves_cleared = False

    def start_wave(self, wave_num: int):
        self.current_wave = wave_num
        self.wave_timer = 0.0
        self.wave_active = True
        self.spawn_queue.clear()

        # Design staged spawns (timestamp, type, start_x, start_y)
        if wave_num == 1:
            # Wave 1: Scouting swarms
            for i in range(7):
                self.spawn_queue.append((0.8 + i * 0.7, "scout", 200.0 + i * 140.0, -30.0))
            for i in range(7):
                self.spawn_queue.append((6.5 + i * 0.6, "scout", 1080.0 - i * 130.0, -30.0))

        elif wave_num == 2:
            # Wave 2: Scouts + 2 Heavy Sentinels
            self.spawn_queue.append((0.5, "sentinel", 360.0, -50.0))
            self.spawn_queue.append((1.5, "sentinel", 920.0, -50.0))
            for i in range(10):
                self.spawn_queue.append((3.0 + i * 0.8, "scout", 180.0 + (i % 5) * 220.0, -30.0))

        elif wave_num == 3:
            # Wave 3: Heavy barrage (3 Sentinels in triangle)
            self.spawn_queue.append((0.5, "sentinel", 640.0, -50.0))
            self.spawn_queue.append((2.0, "sentinel", 300.0, -50.0))
            self.spawn_queue.append((2.0, "sentinel", 980.0, -50.0))
            for i in range(12):
                self.spawn_queue.append((5.0 + i * 0.7, "scout", random.uniform(100, 1180), -30.0))

        elif wave_num == 4:
            # Final Wave: The Swarm Commander Boss + Escorts
            self.spawn_queue.append((1.0, "boss", 640.0, -70.0))
            self.spawn_queue.append((4.0, "sentinel", 250.0, -50.0))
            self.spawn_queue.append((4.0, "sentinel", 1030.0, -50.0))
            for i in range(14):
                self.spawn_queue.append((8.0 + i * 1.5, "scout", random.uniform(120, 1160), -30.0))

    def update(self, dt: float, enemies: list):
        if not self.wave_active:
            return

        self.wave_timer += dt

        # Spawn queued units when their timestamp is reached
        remaining_spawns = []
        for spawn_time, drone_type, sx, sy in self.spawn_queue:
            if self.wave_timer >= spawn_time:
                enemies.append(EnemyDrone(sx, sy, drone_type))
            else:
                remaining_spawns.append((spawn_time, drone_type, sx, sy))
        self.spawn_queue = remaining_spawns

        # Check for wave completion
        if len(self.spawn_queue) == 0 and len(enemies) == 0:
            self.wave_active = False
            self.wave_complete_banner_timer = 2.5
            if self.current_wave < 4:
                self.start_wave(self.current_wave + 1)
            else:
                self.all_waves_cleared = True


# ==============================================================================
# MAIN GAME APPLICATION (STATE MACHINE PATTERN)
# ==============================================================================

class SpaceSwarmGame:
    def __init__(self):
        # 1. Raylib Window & Target Framerate
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)

        # 2. Audio Subsystem
        init_audio_device()
        self.sfx = SoundLibrary()
        self.sfx.init_defaults()

        self.music = SynthMusicPlayer()
        self.action_track = generate_action_track(bpm=128.0)
        self.music.load_track(self.action_track)
        self.music.set_volume(0.55)
        self.music.play()
        self.music_enabled = True

        # 3. Core Systems
        self.state = "PLAYING" # TITLE, PLAYING, GAMEOVER, VICTORY
        self.starfield = Starfield()
        self.player = PlayerShip(SCREEN_WIDTH / 2.0, SCREEN_HEIGHT - 100.0)
        self.bullets = BulletPool(capacity=600)
        self.particles = ParticlePool(capacity=400)
        self.grid = SpatialGrid2D(cell_size=64.0) # 2D Spatial Partitioning
        self.shake = TraumaShake(max_offset_px=18.0, max_angle_deg=2.5, decay_rate=1.4)
        self.wave_director = WaveDirector()
        self.enemies = []

        # Scoring & Stats
        self.score = 0
        self.multiplier = 1
        self.combo_timer = 0.0
        self.show_xray = True
        self.shake_enabled = True

        # 2D Screen Camera for Trauma Shake
        self.camera = Camera2D()
        self.camera.offset = Vector2(SCREEN_WIDTH / 2.0, SCREEN_HEIGHT / 2.0)
        self.camera.target = Vector2(SCREEN_WIDTH / 2.0, SCREEN_HEIGHT / 2.0)
        self.camera.rotation = 0.0
        self.camera.zoom = 1.0

        # Start initial wave
        self.wave_director.start_wave(1)

    def reset_game(self):
        self.player = PlayerShip(SCREEN_WIDTH / 2.0, SCREEN_HEIGHT - 100.0)
        self.bullets.clear()
        self.particles.clear()
        self.enemies.clear()
        self.score = 0
        self.multiplier = 1
        self.combo_timer = 0.0
        self.wave_director = WaveDirector()
        self.wave_director.start_wave(1)
        self.state = "PLAYING"

    def handle_collisions(self):
        """
        Executes broadphase spatial queries via SpatialGrid2D and checks narrowphase
        exact circle/capsule hits.
        """
        self.grid.clear()

        # 1. Register enemies into spatial hash
        for enemy in self.enemies:
            if enemy.active:
                self.grid.insert(enemy, enemy.pos.x, enemy.pos.y, enemy.radius)

        # 2. Register player into spatial hash
        self.grid.insert(self.player, self.player.pos.x, self.player.pos.y, self.player.hitbox_radius)

        # 3. Test active bullets against entities in their local spatial cell
        for b in self.bullets.pool:
            if not b.active:
                continue

            if not b.is_enemy:
                # --- Player Bullet vs Enemies ---
                nearby = self.grid.query_radius(b.pos.x, b.pos.y, b.radius)
                for entity in nearby:
                    if isinstance(entity, EnemyDrone) and entity.active:
                        # Circle-circle collision test
                        dx = b.pos.x - entity.pos.x
                        dy = b.pos.y - entity.pos.y
                        dist_sq = dx * dx + dy * dy
                        r_sum = b.radius + entity.radius
                        if dist_sq <= r_sum * r_sum:
                            b.active = False
                            entity.hp -= 1
                            self.particles.emit_burst(b.pos.x, b.pos.y, 4, 80.0, COLOR_PLAYER_BULLET, 0.25)
                            self.sfx.play("hit", 0.35)

                            if entity.hp <= 0:
                                entity.active = False
                                self.score += entity.score_value * self.multiplier
                                self.combo_timer = 2.0
                                self.multiplier = min(8, self.multiplier + 1)
                                self.particles.emit_burst(entity.pos.x, entity.pos.y, 35, 240.0, entity.palette["wing"], 0.6)
                                self.shake.add_trauma(0.35 if entity.type == "scout" else 0.65)
                                self.sfx.play("explosion", 0.65)
                            break
            else:
                # --- Enemy Bullet vs Player ---
                dx = b.pos.x - self.player.pos.x
                dy = b.pos.y - self.player.pos.y
                dist_sq = dx * dx + dy * dy
                r_sum = b.radius + self.player.hitbox_radius
                if dist_sq <= r_sum * r_sum:
                    b.active = False
                    hit_registered = self.player.take_hit(self.particles, self.sfx, self.shake)
                    if hit_registered:
                        self.multiplier = 1
                        if self.player.health <= 0:
                            self.state = "GAMEOVER"
                            self.particles.emit_burst(self.player.pos.x, self.player.pos.y, 60, 320.0, COLOR_PLAYER_HULL, 0.9)

        # 4. Direct Enemy Body vs Player Ship Collision
        for enemy in self.enemies:
            if enemy.active:
                dx = enemy.pos.x - self.player.pos.x
                dy = enemy.pos.y - self.player.pos.y
                dist_sq = dx * dx + dy * dy
                r_sum = enemy.radius + self.player.visual_radius
                if dist_sq <= r_sum * r_sum:
                    hit_registered = self.player.take_hit(self.particles, self.sfx, self.shake)
                    if hit_registered:
                        enemy.hp -= 2
                        if enemy.hp <= 0:
                            enemy.active = False
                            self.particles.emit_burst(enemy.pos.x, enemy.pos.y, 30, 200.0, enemy.palette["wing"], 0.5)

    def update(self):
        dt = get_frame_time()
        # Cap dt to avoid collision tunneling if window is dragged
        dt = min(dt, 0.05)

        # Background audio stream loop
        if self.music_enabled:
            self.music.update()

        # Starfield parallax
        self.starfield.update(dt)

        # Mute audio toggle
        if is_key_pressed(KEY_M):
            self.music_enabled = not self.music_enabled
            if self.music_enabled:
                self.music.resume()
            else:
                self.music.pause()

        # Interactive Pattern Learning Toggles ([Tab/Select] X-Ray & [F1/R3] Shake Toggle)
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
            self.sfx.play("click", 0.5)
        if is_dual_pattern_toggle_pressed():
            self.shake_enabled = not self.shake_enabled
            self.sfx.play("click", 0.5)

        # State updates
        if self.state == "PLAYING":
            # Update player
            self.player.update(dt, self.bullets, self.particles, self.sfx)

            # Update enemy swarm
            for enemy in self.enemies:
                if enemy.active:
                    enemy.update(dt, self.player.pos, self.bullets, self.sfx)

            # Clean inactive enemies using explicit C++-style loop
            remaining_enemies = []
            for enemy in self.enemies:
                if enemy.active:
                    remaining_enemies.append(enemy)
            self.enemies = remaining_enemies

            # Update wave director
            self.wave_director.update(dt, self.enemies)
            if self.wave_director.all_waves_cleared:
                self.state = "VICTORY"

            # Update projectile and particle pools
            self.bullets.update(dt)
            self.particles.update(dt)

            # Spatial grid & collision testing
            self.handle_collisions()

            # Combo score multiplier decay
            if self.combo_timer > 0.0:
                self.combo_timer -= dt
                if self.combo_timer <= 0.0:
                    self.multiplier = 1

        elif self.state in ("GAMEOVER", "VICTORY"):
            self.particles.update(dt)
            self.bullets.update(dt)
            if is_dual_reset_pressed():
                self.reset_game()

        # Update trauma camera shake
        off_x, off_y, angle_rad = self.shake.update(dt)
        if self.shake_enabled:
            self.camera.target = Vector2((SCREEN_WIDTH / 2.0) + off_x, (SCREEN_HEIGHT / 2.0) + off_y)
            self.camera.rotation = math.degrees(angle_rad)
        else:
            self.camera.target = Vector2(SCREEN_WIDTH / 2.0, SCREEN_HEIGHT / 2.0)
            self.camera.rotation = 0.0

    def draw_xray_telemetry(self):
        """Renders live pattern metrics for Object Pools, SpatialGrid2D, and TraumaShake."""
        row_step = max(22, 24 + ui_settings.font_size_offset)
        panel_x = 24
        panel_y = 60
        panel_w = 370 + max(0, ui_settings.font_size_offset * 14)
        panel_h = 44 + row_step * 6
        draw_rectangle(panel_x, panel_y, panel_w, panel_h, Color(10, 16, 28, 225))
        draw_rectangle_lines(panel_x, panel_y, panel_w, panel_h, SKYBLUE)
        draw_text("X-RAY PATTERN TELEMETRY [Tab]", panel_x + 12, panel_y + 10, 16, SKYBLUE)

        active_bullets = 0
        for b in self.bullets.pool:
            if b.active:
                active_bullets += 1

        active_particles = 0
        for p in self.particles.pool:
            if p.active:
                active_particles += 1

        occupied_cells = len(self.grid.grid)

        draw_text(
            f"1. Bullet Pool   : {active_bullets:3d} / {self.bullets.capacity} active",
            panel_x + 12, panel_y + 38 + row_step * 0, 15, WHITE
        )
        draw_text(
            f"2. Particle Pool : {active_particles:3d} / {self.particles.capacity} active",
            panel_x + 12, panel_y + 38 + row_step * 1, 15, WHITE
        )
        draw_text(
            f"3. SpatialGrid2D : {occupied_cells:3d} active cells (64px)",
            panel_x + 12, panel_y + 38 + row_step * 2, 15, GREEN
        )
        shake_state = "ON" if self.shake_enabled else "OFF"
        shake_col = GOLD if self.shake_enabled else GRAY
        draw_text(
            f"4. TraumaShake   : {self.shake.trauma:.2f} [{shake_state} - F1]",
            panel_x + 12, panel_y + 38 + row_step * 3, 15, shake_col
        )
        draw_text(
            f"5. FSM State     : {self.state}",
            panel_x + 12, panel_y + 38 + row_step * 4, 15, LIGHTGRAY
        )
        draw_text(
            f"6. Wave Director : Wave {self.wave_director.current_wave} ({len(self.enemies)} drones)",
            panel_x + 12, panel_y + 38 + row_step * 5, 15, LIGHTGRAY
        )

    def draw(self):
        begin_drawing()
        clear_background(COLOR_BG)

        # Begin 2D Screen-Shake Camera Pass
        begin_mode_2d(self.camera)

        # 1. Background gridlines & starfield
        for x in range(0, SCREEN_WIDTH, 64):
            draw_line(x, 0, x, SCREEN_HEIGHT, COLOR_GRID)
        for y in range(0, SCREEN_HEIGHT, 64):
            draw_line(0, y, SCREEN_WIDTH, y, COLOR_GRID)
        self.starfield.draw()

        # 1b. Optional X-Ray SpatialGrid2D occupied cell visualization
        if self.show_xray:
            cs = int(self.grid.cell_size)
            for (cx, cy), entries in self.grid.grid.items():
                if entries:
                    wx = int(cx * cs)
                    wy = int(cy * cs)
                    draw_rectangle(wx, wy, cs, cs, Color(40, 220, 100, 35))
                    draw_rectangle_lines(wx, wy, cs, cs, Color(60, 255, 120, 140))
                    draw_text(str(len(entries)), wx + 4, wy + 4, 12, GREEN)

        # 2. Projectiles & Particles (Object Pools)
        self.bullets.draw()
        self.particles.draw()

        # 3. Enemies
        for enemy in self.enemies:
            if enemy.active:
                enemy.draw()

        # 4. Player Starship
        if self.player.health > 0:
            is_focused = is_dual_dash_down()
            self.player.draw(is_focused)

        end_mode_2d()

        # =====================================================================
        # HUD / UI OVERLAY (Non-camera coordinates)
        # =====================================================================
        # Shields / Health indicators
        draw_text("SHIELDS:", 28, 24, 18, SKYBLUE)
        for i in range(self.player.max_health):
            shield_col = SKYBLUE if i < self.player.health else DARKGRAY
            draw_rectangle(115 + i * 28, 22, 22, 18, shield_col)
            draw_rectangle_lines(115 + i * 28, 22, 22, 18, WHITE)

        # Score & Multiplier
        score_text = f"SCORE: {self.score:07d}"
        draw_text(score_text, SCREEN_WIDTH - 240, 24, 20, WHITE)
        mult_col = GOLD if self.multiplier > 1 else LIGHTGRAY
        draw_text(f"x{self.multiplier}", SCREEN_WIDTH - 240, 50, 18, mult_col)

        # Wave Counter (next to Shields so x=450..978 is free for top-bar dropdowns)
        wave_str = f"WAVE {self.wave_director.current_wave} / 4"
        draw_text(wave_str, 275, 22, 19, GOLD)

        # Top-Bar UI Dropdowns (Font, Font Size, Window Size / F11)
        draw_ui_settings_bar(450, 16)

        # Simultaneous Keyboard/Mouse + Gamepad Controls Hint & Status Badge
        draw_text(
            "[WASD/L-Stick] Move  [Shift/LB] Focus  [Space/A/RT] Fire  [Tab/Select] X-Ray  [F1/R3] Shake",
            28, SCREEN_HEIGHT - 32, 14, GRAY
        )
        draw_gamepad_status_badge(SCREEN_WIDTH - 340, SCREEN_HEIGHT - 30, 12)

        if self.show_xray:
            self.draw_xray_telemetry()

        # =====================================================================
        # GAME OVER / VICTORY OVERLAYS
        # =====================================================================
        if self.state == "GAMEOVER":
            draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, Color(10, 10, 15, 180))
            draw_text("STARSHIP DESTROYED", int(SCREEN_WIDTH / 2.0) - 220, int(SCREEN_HEIGHT / 2.0) - 60, 40, RED)
            draw_text(f"FINAL SCORE: {self.score}", int(SCREEN_WIDTH / 2.0) - 100, int(SCREEN_HEIGHT / 2.0) + 0, 22, WHITE)
            draw_text("PRESS [R] TO RESTART MISSION", int(SCREEN_WIDTH / 2.0) - 150, int(SCREEN_HEIGHT / 2.0) + 50, 20, GOLD)

        elif self.state == "VICTORY":
            draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, Color(10, 25, 20, 180))
            draw_text("SECTOR CLEARED! VICTORY", int(SCREEN_WIDTH / 2.0) - 260, int(SCREEN_HEIGHT / 2.0) - 60, 40, GREEN)
            draw_text(f"FINAL SCORE: {self.score}", int(SCREEN_WIDTH / 2.0) - 100, int(SCREEN_HEIGHT / 2.0) + 0, 22, WHITE)
            draw_text("PRESS [R] TO RE-ENGAGE SWARM", int(SCREEN_WIDTH / 2.0) - 150, int(SCREEN_HEIGHT / 2.0) + 50, 20, GOLD)

        end_drawing()

    def run(self, smoke_test: bool = False):
        """Main game loop executing input, state update, and rendering."""
        frame_count = 0
        while not window_should_close():
            self.update()
            self.draw()
            frame_count += 1
            if smoke_test and frame_count >= 3:
                break

        # Clean disposal on exit
        self.sfx.unload_all()
        self.music.unload()
        close_audio_device()
        close_window()


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    is_smoke = "--smoke-test" in sys.argv
    game = SpaceSwarmGame()
    game.run(smoke_test=is_smoke)

