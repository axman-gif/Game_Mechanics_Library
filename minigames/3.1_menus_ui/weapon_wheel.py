# -*- coding: utf-8 -*-
"""
Weapon Wheel - Radial Menu with Sector Partitioning & Time Dilation
===================================================================
Section          : 3.1 Menus & UI
Pattern Category : Menus & User Interface, Gameplay Flow (Time Dilation)
Dimension        : 2D

Problem Solved:
  Linear weapon hotbars (1-9 keys) require players to remove fingers from movement
  keys (WASD) and fail on gamepads where cycling 8 weapons via bumpers is sluggish
  and fatal during combat. Radial menus solve this with 360-degree directional
  selection. However, naive radial menus suffer from center deadzone jitter, lack of
  angular sector boundaries, and failure to slow game time—causing players to take
  unavoidable damage while selecting weapons.

How the Pattern Works:
  1. Angular Sector Partitioning: Divides a circular ring into N equal slices
     (slice_angle = 2*pi / N). Using atan2(dy, dx), cursor deflection is converted
     into an angle theta in [0, 2*pi). The sector index is computed mathematically:
     sector = floor((theta + slice_angle/2) / slice_angle) % N.
  2. Radial Deadzone & Hysteresis: If distance from center is below R_dead (e.g. 45px),
     the current weapon selection is locked, completely preventing jitter near the origin.
  3. Time Dilation (Bullet-Time): Opening the wheel scales simulation delta time
     down to 15% speed (dt_sim = dt_real * time_scale) via framerate-independent
     damping (damp), giving the player tactical thinking time while the combat arena
     remains organically alive.
  4. Instant Decoupled Weapon Swap: Releasing the wheel equips the selected weapon,
     updating firing mechanics, projectile pools, and HUD readouts immediately.

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - Hold Q / Tab / Middle Click / Gamepad LB : Open Weapon Wheel (Time Dilation slows time)
  - Mouse Angle / Gamepad Right Stick       : Steer selection around 360° radial ring
  - Release Wheel Key                       : Equip selected weapon
  - WASD / Gamepad Left Stick               : Move player character in live combat arena
  - Left Mouse / Space / Gamepad RT         : Fire equipped weapon
  - [Tab] / Gamepad View (Select)           : Toggle X-Ray Telemetry & Sector Math Overlay
  - [F1]  / Gamepad LB (Toggle Mode)        : Toggle Time Dilation: [Slow-Motion (15%)] vs [Real-Time (100%)]
  - [F2]  / Gamepad RB                      : Toggle Deadzone: [Active Deadzone] vs [Zero Deadzone (Jitter)]
  - [Ctrl +/-]                              : Increase / Decrease UI Font Size
  - [F11]                                   : Toggle Fullscreen
  - [R]   / Gamepad Start                   : Reset Arena Dummies & Target Swarms
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
WINDOW_TITLE = "Weapon Wheel - Radial Menu & Time Dilation (Raylib Pattern Lab)"

# Palette
COLOR_ARENA_BG         = Color(12, 16, 26, 255)
COLOR_GRID_LINE        = Color(24, 32, 50, 150)
COLOR_WHEEL_BACKDROP   = Color(8, 10, 18, 210)
COLOR_WHEEL_BASE       = Color(26, 36, 58, 220)
COLOR_WHEEL_BORDER     = Color(50, 75, 120, 255)
COLOR_WHEEL_HOVER      = Color(0, 220, 255, 230)
COLOR_WHEEL_GLOW       = Color(0, 220, 255, 70)
COLOR_DEADZONE_RING    = Color(255, 80, 80, 140)
COLOR_RAY_DIVIDER      = Color(70, 100, 150, 180)

# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATION
# ==============================================================================

class WeaponSlice:
    """
    Metadata definition for a radial weapon slice.
    C++ Equivalent:
      struct WeaponSlice {
          std::string name;
          float damage;
          float fire_rate;
          float speed;
          int ammo;
          Color color;
      };
    """
    def __init__(self, name: str, damage: float, fire_rate: float, speed: float, ammo: int, color: Color):
        self.name = name
        self.damage = damage
        self.fire_rate = fire_rate
        self.speed = speed
        self.ammo = ammo
        self.color = color


class RadialWeaponWheel:
    """
    Encapsulates angular sector partitioning, deadzone hysteresis,
    and radial slice selection math.
    """
    def __init__(self, center: Vector2, inner_radius: float = 75.0, outer_radius: float = 195.0):
        self.center = center
        self.inner_radius = inner_radius
        self.outer_radius = outer_radius
        self.deadzone_radius = 45.0        # [F2] Toggleable deadzone
        self.use_deadzone = True
        self.slices = []
        self.selected_index = 0
        self.hovered_index = 0
        self.current_angle_deg = 0.0
        self.input_distance = 0.0
        self.is_open = False
        self.wheel_scale = 0.0             # Smooth opening scale (0.0 to 1.0)
        self.time_dilation_enabled = True  # [F1] Toggle
        self.current_time_scale = 1.0

    def add_weapon(self, name: str, damage: float, fire_rate: float, speed: float, ammo: int, color: Color):
        self.slices.append(WeaponSlice(name, damage, fire_rate, speed, ammo, color))

    def update_input(self, input_vector: Vector2, is_wheel_held: bool, dt: float):
        """
        Processes radial directional input and smoothly scales wheel animation and time dilation.
        """
        self.is_open = is_wheel_held

        # 1. Animate Wheel Opening/Closing Scale
        target_scale = 1.0 if self.is_open else 0.0
        self.wheel_scale = damp(self.wheel_scale, target_scale, 20.0, dt)

        # 2. Time Dilation: Scale simulation speed
        if self.time_dilation_enabled:
            target_time_scale = 0.15 if self.is_open else 1.0
        else:
            target_time_scale = 1.0
        self.current_time_scale = damp(self.current_time_scale, target_time_scale, 18.0, dt)

        if not self.is_open or not self.slices:
            return

        # 3. Calculate Input Distance & Angle (Cartesian to Polar)
        self.input_distance = math.sqrt(input_vector.x * input_vector.x + input_vector.y * input_vector.y)

        # Deadzone check: prevent jitter at center
        if self.use_deadzone and self.input_distance < self.deadzone_radius:
            return

        if self.input_distance > 0.001:
            # Angle in radians and degrees: atan2(dy, dx)
            # 0 deg = Right (+X), 90 deg = Down (+Y in screen space)
            rad = math.atan2(input_vector.y, input_vector.x)
            deg = math.degrees(rad)
            if deg < 0.0:
                deg += 360.0
            self.current_angle_deg = deg

            # 4. Sector Math: Sector = floor((angle + slice_angle/2) / slice_angle) % N
            n = len(self.slices)
            slice_angle = 360.0 / float(n)
            sector_idx = int((self.current_angle_deg + slice_angle * 0.5) / slice_angle) % n
            self.hovered_index = sector_idx
            self.selected_index = sector_idx

    def get_selected_weapon(self) -> WeaponSlice:
        if 0 <= self.selected_index < len(self.slices):
            return self.slices[self.selected_index]
        return None

    def draw(self):
        """Renders the radial wheel geometry, sectors, and active highlight."""
        if self.wheel_scale < 0.02 or not self.slices:
            return

        n = len(self.slices)
        slice_deg = 360.0 / float(n)
        scaled_inner = self.inner_radius * self.wheel_scale
        scaled_outer = self.outer_radius * self.wheel_scale

        # Darkened backdrop
        draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, Color(6, 8, 14, int(160 * self.wheel_scale)))

        # Draw each circular slice
        for i in range(n):
            weapon = self.slices[i]
            is_hovered = (i == self.hovered_index)

            start_angle = i * slice_deg - slice_deg * 0.5
            end_angle = i * slice_deg + slice_deg * 0.5

            # Expand hovered slice outer radius slightly for tactile pop
            slice_outer = (scaled_outer + 16.0) if is_hovered else scaled_outer
            slice_col = COLOR_WHEEL_HOVER if is_hovered else COLOR_WHEEL_BASE

            # Draw outer ring slice
            draw_ring(self.center, scaled_inner, slice_outer, start_angle, end_angle, 24, slice_col)

            # Draw boundary separator lines
            mid_rad = math.radians(end_angle)
            p1 = Vector2(self.center.x + math.cos(mid_rad) * scaled_inner, self.center.y + math.sin(mid_rad) * scaled_inner)
            p2 = Vector2(self.center.x + math.cos(mid_rad) * slice_outer, self.center.y + math.sin(mid_rad) * slice_outer)
            draw_line_ex(p1, p2, 2.0, COLOR_WHEEL_BORDER)

            # Draw Weapon Label in sector midpoint
            label_angle = math.radians(i * slice_deg)
            label_r = (scaled_inner + slice_outer) * 0.5
            lx = self.center.x + math.cos(label_angle) * label_r
            ly = self.center.y + math.sin(label_angle) * label_r

            txt_col = WHITE if is_hovered else Color(190, 215, 245, 255)
            font_sz = 14 if is_hovered else 12
            draw_text(weapon.name, int(lx - len(weapon.name) * 3.5), int(ly - 6), font_sz, txt_col)

        # Center Hub Circle & Selected Weapon Stats Card
        draw_circle_v(self.center, scaled_inner - 4.0, Color(16, 22, 38, 255))
        draw_circle_lines(int(self.center.x), int(self.center.y), scaled_inner - 4.0, COLOR_WHEEL_BORDER)

        cur = self.get_selected_weapon()
        if cur:
            draw_text(cur.name, int(self.center.x - len(cur.name) * 4.2), int(self.center.y - 30), 16, COLOR_WHEEL_HOVER)
            draw_text(f"DMG: {int(cur.damage)}", int(self.center.x - 36), int(self.center.y - 8), 12, Color(255, 210, 80, 255))
            draw_text(f"RATE: {cur.fire_rate:.2f}s", int(self.center.x - 36), int(self.center.y + 8), 12, Color(180, 210, 245, 255))
            draw_text(f"AMMO: {cur.ammo}", int(self.center.x - 36), int(self.center.y + 24), 12, Color(140, 240, 160, 255))

        # Deadzone Circle Outline (visual reminder)
        if self.use_deadzone:
            draw_circle_lines(int(self.center.x), int(self.center.y), self.deadzone_radius * self.wheel_scale, COLOR_DEADZONE_RING)


# ==============================================================================
# BLOCK 2: WORLD SIMULATION & ENTITIES
# ==============================================================================

class Bullet2D:
    """Pre-allocated projectile."""
    def __init__(self):
        self.active = False
        self.pos = Vector2(0.0, 0.0)
        self.vel = Vector2(0.0, 0.0)
        self.color = WHITE
        self.radius = 4.0
        self.damage = 10.0
        self.lifetime = 0.0

    def spawn(self, pos: Vector2, vel: Vector2, radius: float, damage: float, color: Color):
        self.active = True
        self.pos = Vector2(pos.x, pos.y)
        self.vel = Vector2(vel.x, vel.y)
        self.radius = radius
        self.damage = damage
        self.color = color
        self.lifetime = 2.0

    def update(self, dt: float):
        if not self.active:
            return
        self.pos.x += self.vel.x * dt
        self.pos.y += self.vel.y * dt
        self.lifetime -= dt
        if self.lifetime <= 0.0 or self.pos.x < 0 or self.pos.x > SCREEN_WIDTH or self.pos.y < 0 or self.pos.y > SCREEN_HEIGHT:
            self.active = False


class DummyTarget:
    """Combat arena target dummy responding to hits."""
    def __init__(self, pos: Vector2, radius: float = 24.0):
        self.pos = pos
        self.radius = radius
        self.hp = 100
        self.max_hp = 100
        self.hit_flash = 0.0
        self.orbit_angle = random.uniform(0.0, 6.28)
        self.center_x = pos.x
        self.center_y = pos.y

    def update(self, dt: float):
        self.hit_flash = max(0.0, self.hit_flash - dt * 4.0)
        self.orbit_angle += 0.8 * dt
        self.pos.x = self.center_x + math.sin(self.orbit_angle) * 35.0
        self.pos.y = self.center_y + math.cos(self.orbit_angle) * 20.0

    def draw(self):
        col = Color(255, 80, 80, 255) if self.hit_flash < 0.1 else WHITE
        draw_circle_v(self.pos, self.radius, col)
        draw_circle_lines(int(self.pos.x), int(self.pos.y), self.radius, Color(255, 140, 140, 255))
        # Health bar
        bar_w = 40
        ratio = max(0.0, self.hp / float(self.max_hp))
        draw_rectangle(int(self.pos.x - 20), int(self.pos.y - 34), bar_w, 5, Color(30, 40, 50, 255))
        draw_rectangle(int(self.pos.x - 20), int(self.pos.y - 34), int(bar_w * ratio), 5, Color(80, 255, 120, 255))


class PlayerHero:
    """Playable character maneuvering in the arena."""
    def __init__(self, pos: Vector2):
        self.pos = pos
        self.speed = 280.0
        self.facing_rad = 0.0
        self.fire_timer = 0.0

    def update(self, move_vec: Vector2, look_vec: Vector2, dt: float):
        self.fire_timer = max(0.0, self.fire_timer - dt)

        # Movement
        self.pos.x += move_vec.x * self.speed * dt
        self.pos.y += move_vec.y * self.speed * dt
        self.pos.x = max(40, min(SCREEN_WIDTH - 40, self.pos.x))
        self.pos.y = max(80, min(SCREEN_HEIGHT - 60, self.pos.y))

        # Facing direction
        if abs(look_vec.x) + abs(look_vec.y) > 0.05:
            self.facing_rad = math.atan2(look_vec.y, look_vec.x)

    def draw(self):
        draw_humanoid_enemy_2d(
            self.pos,
            facing_angle_rad=self.facing_rad,
            anim_timer=get_time(),
            scale=1.1,
            is_attacking=(self.fire_timer > 0.0)
        )


class WeaponWheelGame:
    """Complete Weapon Wheel & Time Dilation interactive pattern lab."""

    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()

        self.sfx = SoundLibrary()
        self.sfx.init_defaults()

        # Wheel pattern setup (center screen)
        wheel_center = Vector2(SCREEN_WIDTH * 0.5, SCREEN_HEIGHT * 0.5)
        self.wheel = RadialWeaponWheel(wheel_center, inner_radius=75.0, outer_radius=190.0)

        # Populate 8 Sci-Fi Weapons
        self.wheel.add_weapon("PULSE PISTOL",   damage=18.0, fire_rate=0.18, speed=650.0, ammo=999, color=Color(0, 240, 255, 255))
        self.wheel.add_weapon("FLAK SHOTGUN",   damage=45.0, fire_rate=0.65, speed=520.0, ammo=32,  color=Color(255, 160, 40, 255))
        self.wheel.add_weapon("PLASMA RIFLE",   damage=28.0, fire_rate=0.12, speed=720.0, ammo=150, color=Color(0, 255, 140, 255))
        self.wheel.add_weapon("HEAVY ROCKET",   damage=95.0, fire_rate=1.10, speed=380.0, ammo=12,  color=Color(255, 60, 60, 255))
        self.wheel.add_weapon("BEAM LASER",     damage=15.0, fire_rate=0.06, speed=900.0, ammo=200, color=Color(255, 240, 60, 255))
        self.wheel.add_weapon("CRYO CANNON",    damage=32.0, fire_rate=0.45, speed=480.0, ammo=45,  color=Color(120, 200, 255, 255))
        self.wheel.add_weapon("TESLA COIL",     damage=40.0, fire_rate=0.55, speed=580.0, ammo=28,  color=Color(210, 100, 255, 255))
        self.wheel.add_weapon("ENERGY BLADE",   damage=75.0, fire_rate=0.35, speed=400.0, ammo=999, color=Color(255, 255, 255, 255))

        # Simulation Entities
        self.player = PlayerHero(Vector2(260.0, 360.0))
        self.bullets = []
        for _ in range(80):
            self.bullets.append(Bullet2D())
        self.dummies = [
            DummyTarget(Vector2(950.0, 220.0)),
            DummyTarget(Vector2(1050.0, 420.0)),
            DummyTarget(Vector2(880.0, 560.0))
        ]

        self.show_xray = True
        self.score = 0

    def update(self):
        dt_real = min(get_frame_time(), 0.05)

        # 1. Global Pattern Toggles
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
            self.sfx.play("click", 0.6)

        if is_dual_pattern_toggle_pressed():
            self.wheel.time_dilation_enabled = not self.wheel.time_dilation_enabled
            self.sfx.play("coin", 0.65)

        if is_dual_secondary_toggle_pressed():
            self.wheel.use_deadzone = not self.wheel.use_deadzone
            self.sfx.play("click", 0.6)

        if is_dual_reset_pressed():
            for d in self.dummies:
                d.hp = d.max_hp
            self.sfx.play("powerup", 0.7)

        # 2. Check if Weapon Wheel is opened
        wheel_held = (
            is_key_down(KEY_Q)
            or is_mouse_button_down(MOUSE_BUTTON_MIDDLE)
            or is_gamepad_button_down(get_active_gamepad_id(), GAMEPAD_BUTTON_LEFT_TRIGGER_1)
        )

        # Compute radial input direction relative to wheel center
        mx, my = get_mouse_x(), get_mouse_y()
        mouse_dir = Vector2(mx - self.wheel.center.x, my - self.wheel.center.y)

        # Gamepad Right Stick override if deflected
        pad_id = get_active_gamepad_id()
        if pad_id >= 0:
            rx = get_gamepad_axis_movement(pad_id, GAMEPAD_AXIS_RIGHT_X)
            ry = get_gamepad_axis_movement(pad_id, GAMEPAD_AXIS_RIGHT_Y)
            if math.sqrt(rx * rx + ry * ry) > 0.25:
                mouse_dir = Vector2(rx * 120.0, ry * 120.0)

        prev_sel = self.wheel.selected_index
        self.wheel.update_input(mouse_dir, wheel_held, dt_real)
        if self.wheel.is_open and self.wheel.selected_index != prev_sel:
            self.sfx.play("click", 0.45)

        # 3. Time Dilation Scaling: Apply to World Simulation
        # dt_sim slows down to 15% when wheel is open!
        dt_sim = dt_real * self.wheel.current_time_scale

        # Move Player
        move_vec = get_dual_move_2d(deadzone=0.20, use_arrow_keys=True)
        player_look = Vector2(mx - self.player.pos.x, my - self.player.pos.y)
        self.player.update(move_vec, player_look, dt_sim)

        # Fire Weapon (only when wheel is NOT open)
        if not self.wheel.is_open and is_dual_primary_fire_down():
            if self.player.fire_timer <= 0.0:
                cur_w = self.wheel.get_selected_weapon()
                if cur_w and cur_w.ammo > 0:
                    self.player.fire_timer = cur_w.fire_rate
                    if cur_w.ammo < 999:
                        cur_w.ammo -= 1

                    # Projectile trajectory
                    p_dir = normalize_2d(player_look)
                    # Shotgun spread variation
                    spread_count = 5 if "SHOTGUN" in cur_w.name else 1
                    for s in range(spread_count):
                        ang_offset = (random.random() - 0.5) * 0.35 if spread_count > 1 else 0.0
                        cos_a = math.cos(self.player.facing_rad + ang_offset)
                        sin_a = math.sin(self.player.facing_rad + ang_offset)
                        vel = Vector2(cos_a * cur_w.speed, sin_a * cur_w.speed)

                        for b in self.bullets:
                            if not b.active:
                                b.spawn(self.player.pos, vel, radius=5.0, damage=cur_w.damage, color=cur_w.color)
                                break
                    self.sfx.play("laser", 0.6)

        # Update Bullets & Dummies in Sim Time
        for b in self.bullets:
            b.update(dt_sim)

        for d in self.dummies:
            d.update(dt_sim)

        # Bullet-Dummy Collisions
        for b in self.bullets:
            if not b.active:
                continue
            for d in self.dummies:
                dx = d.pos.x - b.pos.x
                dy = d.pos.y - b.pos.y
                if math.sqrt(dx * dx + dy * dy) <= (d.radius + b.radius):
                    b.active = False
                    d.hp = max(0, d.hp - int(b.damage))
                    d.hit_flash = 1.0
                    self.score += 50
                    self.sfx.play("hit", 0.65)
                    break

    # ==========================================================================
    # BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY ([Tab], [F1], [F2])
    # ==========================================================================
    def draw_xray_overlay(self):
        """Renders the radial sector partitioning math, angles, and time dilation metrics."""
        panel_x = 24
        panel_y = 86
        panel_w = 400
        panel_h = 320

        draw_rectangle(panel_x, panel_y, panel_w, panel_h, Color(14, 18, 30, 240))
        draw_rectangle_lines(panel_x, panel_y, panel_w, panel_h, Color(45, 75, 120, 255))

        draw_text("RADIAL MENU & TIME DILATION X-RAY [Tab]", panel_x + 16, panel_y + 14, 14, COLOR_WHEEL_HOVER)
        draw_line(panel_x + 16, panel_y + 36, panel_x + panel_w - 16, panel_y + 36, Color(45, 75, 120, 255))

        y = panel_y + 46
        # Time Dilation Telemetry
        td_col = Color(80, 255, 140, 255) if self.wheel.time_dilation_enabled else Color(255, 120, 120, 255)
        td_mode = "BULLET-TIME ACTIVE (15% Speed)" if self.wheel.time_dilation_enabled else "REAL-TIME (100% Speed)"
        draw_text(f"[F1] Time Dilation: {td_mode}", panel_x + 16, y, 12, td_col)
        y += 18
        draw_text(f" * Time Scale: {self.wheel.current_time_scale * 100:.1f}% (dt_sim = dt * scale)", panel_x + 16, y, 11, Color(170, 200, 235, 255))
        y += 15
        draw_text(" * Slows world physics so player can aim wheel safely", panel_x + 16, y, 11, Color(170, 200, 235, 255))

        # Deadzone Telemetry
        y += 22
        dz_col = Color(80, 255, 140, 255) if self.wheel.use_deadzone else Color(255, 120, 120, 255)
        dz_mode = "ACTIVE DEADZONE (45px)" if self.wheel.use_deadzone else "ZERO DEADZONE (JITTERY CENTER)"
        draw_text(f"[F2] Center Hysteresis: {dz_mode}", panel_x + 16, y, 12, dz_col)
        y += 18
        draw_text(f" * Input Distance from Center: {self.wheel.input_distance:.1f}px", panel_x + 16, y, 11, Color(170, 200, 235, 255))

        # Angular Partitioning Math
        y += 22
        draw_text("POLAR ANGLE & SECTOR CALCULATION:", panel_x + 16, y, 12, Color(255, 210, 80, 255))
        y += 18
        draw_text(f" * theta = atan2(dy, dx) = {self.wheel.current_angle_deg:.1f} deg", panel_x + 16, y, 11, Color(170, 200, 235, 255))
        y += 16
        draw_text(f" * Sector = floor((theta + 22.5°) / 45°) = Slice #{self.wheel.selected_index}", panel_x + 16, y, 11, Color(170, 200, 235, 255))

        # Wheel State
        y += 20
        status_txt = "WHEEL OPEN (SLOW-MO RUNNING)" if self.wheel.is_open else "WHEEL CLOSED (HOLD Q TO OPEN)"
        draw_text(f"STATUS: {status_txt}", panel_x + 16, y, 12, Color(0, 240, 255, 255))

    # ==========================================================================
    # BLOCK 4: MAIN GAME LOOP & AUTOMATED SMOKE TEST
    # ==========================================================================
    def draw(self):
        begin_drawing()
        clear_background(COLOR_ARENA_BG)

        # Arena Grid Floor
        for gx in range(0, SCREEN_WIDTH, 48):
            draw_line(gx, 0, gx, SCREEN_HEIGHT, COLOR_GRID_LINE)
        for gy in range(0, SCREEN_HEIGHT, 48):
            draw_line(0, gy, SCREEN_WIDTH, gy, COLOR_GRID_LINE)

        # Draw Dummies
        for d in self.dummies:
            d.draw()

        # Draw Bullets
        for b in self.bullets:
            if b.active:
                draw_circle_v(b.pos, b.radius, b.color)

        # Draw Player Commando
        self.player.draw()

        # Draw Radial Weapon Wheel on top
        self.wheel.draw()

        # Header Bar
        draw_rectangle(0, 0, SCREEN_WIDTH, 56, Color(12, 16, 26, 240))
        draw_line(0, 56, SCREEN_WIDTH, 56, Color(35, 50, 80, 255))
        draw_text("WEAPON WHEEL - RADIAL SECTOR PARTITIONING", 24, 18, 18, COLOR_WHEEL_HOVER)

        # Dropdowns & Gamepad Badge
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)

        # Bottom HUD: Active Weapon Card
        hud_y = SCREEN_HEIGHT - 54
        draw_rectangle(0, hud_y, SCREEN_WIDTH, 54, Color(12, 16, 26, 240))
        draw_line(0, hud_y, SCREEN_WIDTH, hud_y, Color(35, 50, 80, 255))

        cur_w = self.wheel.get_selected_weapon()
        if cur_w:
            draw_text(f"EQUIPPED: {cur_w.name}", 24, hud_y + 18, 15, cur_w.color)
            draw_text(f"AMMO: {cur_w.ammo}", 240, hud_y + 18, 14, Color(180, 210, 245, 255))
            draw_text(f"SCORE: {self.score}", 360, hud_y + 18, 14, Color(255, 220, 80, 255))

        draw_text(
            "[Hold Q/Tab/LB] Open Wheel   [WASD/Left-Stick] Move   [Click/RT] Fire   [Tab] X-Ray   [F1] Time Dilation   [F2] Deadzone",
            510, hud_y + 18, 12, Color(170, 195, 225, 255)
        )

        # X-Ray Telemetry Overlay
        if self.show_xray:
            self.draw_xray_overlay()

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
    WeaponWheelGame().run(smoke_test=is_smoke)

