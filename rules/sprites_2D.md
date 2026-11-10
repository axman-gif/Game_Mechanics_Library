# 2D Procedural Sprites Architectural Guidelines & Registry (`assets/sprites_2D/`)
=============================================================================

This document defines the architectural standards, vector primitive rendering rules, procedural animation interfaces, and a copy-pasteable **code template** for all 2D procedural sprites.
All 2D sprites are organized into dedicated category subfolders within `assets/sprites_2D/<category>/` (`crawler_automaton/`, `projectile_vfx/`, `side_scroller/`, `swarm_floating/`, and `top_down/`).

All 2D sprite task tracking, vector specifications, and progress statuses are maintained in the companion spreadsheet:
👉 [**`tasks/sprites_2D.csv`**](../tasks/sprites_2D.csv) (29 planned sprites: 4 base sprites and 25 specialized sprites)

For top-level asset architecture and unified contracts, see [**`rules/assets.md`**](assets.md).

---

## 1. Golden Architecture Rules for 2D Procedural Sprites

1. **Pure Geometric Primitives**: All 2D sprites are drawn directly onto the framebuffer using Raylib 2D vector and primitive calls (`draw_circle`, `draw_circle_v`, `draw_rectangle_pro`, `draw_rectangle`, `draw_line`, `draw_line_ex`, `draw_triangle`, `draw_poly`). External raster image files (`.png`, `.jpg`, `.bmp`, `.tga`) and sprite sheets are strictly forbidden.
2. **Language-Agnostic & C++-Transferable Code (Simple Beats Clever)**:
   In alignment with [`README.md`](../README.md) and [`AGENTS.md`](../AGENTS.md), this repository is built for learning and inspiration. Python serves as **executable, readable pseudocode** that ports 1-to-1 to C++, C, C#, Rust, or Zig.
   - Use plain classes with explicit `__init__` constructors initializing all fields line-by-line.
   - Use explicit `for` loops and `if/else` branching.
   - **Strictly forbidden**: decorators (`@dataclass`, `@property`, `@staticmethod`), generators (`yield`), coroutines (`async`/`await`), lambdas, list/dict comprehensions in rendering loops, and magic dunders (except `__init__`).
   - Write novice-friendly comments explaining **WHY** equations work in simple words without unnecessary jargon.
3. **Canonical Procedural Animation Interface (Unified Asset Contract B)**:
   Every 2D sprite module must export a standardized external drawing function:
```python
def draw_<name>_2d(
    position: Vector2,
    facing_angle_rad: float = 0.0,
    anim_timer: float = 0.0,
    scale: float = 1.0,
    palette: dict = None
) -> None:
    pass
```
   - `position` (`Vector2`): The anchor position in world or screen coordinates.
   - `facing_angle_rad` (`float`): Sprite orientation angle strictly in **radians** (0.0 rad points along the positive X-axis).
   - `anim_timer` (`float`): Continuous time variable driving procedural oscillation (sway, bob, breath).
   - `scale` (`float`): Uniform multiplier for dimensions and geometric offsets.
   - `palette` (`dict`): Optional color theme override. When `None`, the function falls back to its documented `DEFAULT_<NAME>_PALETTE`.
4. **Color Palettes & Named Geometric Constants**:
   - Every sprite must expose an explicit default dictionary constant named `DEFAULT_<NAME>_PALETTE` mapping semantic parts (`body`, `armor`, `accent`, `outline`, `eye`, `weapon`) to Raylib `Color` instances.
   - **No Magic Numbers**: Body dimensions, limb offsets, radii, and weapon coordinates must be declared as uppercase named constants (e.g., `BASE_RADIUS`, `SHOULDER_RADIUS`, `WEAPON_WIDTH`) rather than hardcoded inline numbers.
5. **Default Destination Directory**: All 2D procedural sprites are strictly located in their designated category subfolder within `assets/sprites_2D/<category>/` (`assets/sprites_2D/crawler_automaton/`, `assets/sprites_2D/projectile_vfx/`, `assets/sprites_2D/side_scroller/`, `assets/sprites_2D/swarm_floating/`, `assets/sprites_2D/top_down/`).
6. **2D Rendering Order & Explicit Int Casting**:
   All coordinates and dimensions passed to non-vector pixel draw routines (`draw_line`, `draw_circle`, `draw_rectangle`, `draw_text`) must be explicitly cast to `int` (`int(x)`, `int(y)`) to satisfy Raylib CFFI type contracts and prevent float truncation issues. Vector routines (`draw_circle_v`, `draw_rectangle_pro`) take `Vector2`.
7. **Line Limits & Readability Criterion**:
   - **Procedural Assets** (SFX, BGM, 3D models, 2D sprites): floor **200 lines**, target **200 to 800 lines**, hard ceiling **1,000 lines**.
   - **Minigames**: floor **300 lines**, target **300 to 1,500 lines**, hard ceiling **1,800 lines**.
   - **Token Guidance, Not Padding**: Line limits are practical guidance for token control. **Never pad a file** to artificially reach the floor. **Never compress code or drop comments** to squeeze under the ceiling.
   - **Readability Criterion**: A file must be understandable reading top to bottom, without jumping back and forth to other files. **Clarity always wins over line count.**
8. **Standalone Previewer & Automated `--smoke-test`**:
   Every sprite file must be standalone executable (`if __name__ == "__main__":`). Running `python -B assets/sprites_2D/<category>/<file>.py` launches an interactive preview application (`SpritePreviewApp`). Running with `--smoke-test` renders 3 frames headlessly and exits with code `0`.
9. **Assets-Only Minigames Rule & Orchestrator Prerequisite Gate**:
   Minigames must use only assets that ALREADY exist inside the `assets/` package.
   - **Lead Orchestrator Prerequisite Check**: Before spawning a 2D minigame craftsman, the Orchestrator runs a Python script reading strictly `id`, `status`, and `description` from `tasks/sprites_2D.csv`.
   - **Quality Preservation Gate**: If any required 2D sprite is missing or pending, craftsman invocation for that minigame is halted immediately. The Orchestrator explains to the user which sprite is missing and how withholding the craftsman preserves vector visual quality (preventing raw, monolithic circles and boxes drawn locally in the minigame).
   - **Specification Injection**: Once verified (`status == done`), the exact drawing function `draw_<name>_2d(position, facing_angle_rad, anim_timer, scale, palette)` and default palette `DEFAULT_<NAME>_PALETTE` are injected into the minigame craftsman prompt.
---

## 2. Standard 2D Sprite Code Template

Every craftsman subagent creating a 2D sprite must follow this exact 6-part anatomy. Copy and adapt this template for your target asset:

```python
# -*- coding: utf-8 -*-
"""
Tactical Spec-Ops Operator - 2D Procedural Vector Sprite
========================================================
Category         : top_down
Target File      : assets/sprites_2D/top_down/tactical_ops.py
Primitives Used  : Circles (helmet, hands, shoulders), Rectangles (torso vest, weapon), Lines (laser sight)
Animation Loop   : Walking shoulder-sway, weapon recoil pulse, tactical laser pulsation, breathing squash

Problem Solved:
  Eliminates pixel art texture dependencies and resolution-scaling blur by rendering
  an articulated top-down soldier purely from vector primitives, rotation matrices,
  and trigonometric oscillation in real time.

How the Procedural Articulation Works:
  - Vector transforms use standard 2D rotation formulas:
      rx = cos(angle_rad) * vx - sin(angle_rad) * vy
      ry = sin(angle_rad) * vx + cos(angle_rad) * vy
  - Walking produces alternating counter-phase shoulder sway and weapon bob via math.sin(anim_timer * speed).
  - Aiming laser pulses opacity using sinusoidal modulation: 180 + 75 * sin(anim_timer * 10).

C++ Raylib Equivalent:
  struct TacticalOpsPalette { Color armor; Color vest; Color hands; Color visor; Color weapon; Color laser; Color outline; };
  void RotateVector2D(float vx, float vy, float angle_rad, float* out_x, float* out_y);
  void DrawTacticalOps2D(Vector2 position, float facing_angle_rad, float anim_timer, float scale, const TacticalOpsPalette* palette);
  Mapped directly to DrawCircle, DrawCircleV, DrawRectanglePro, and DrawLine from raylib.h.
"""

# ==============================================================================
# PART 2: ZERO __PYCACHE__ SETUP, SYS.PATH & RAYLIB IMPORTS
# ==============================================================================
import sys
import os
import math

# 1. Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# 2. Add repository root to search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

# 3. Mandatory Raylib and utility imports
from pyray import *
from utils import *

# ==============================================================================
# PART 3: COLOR PALETTES & NAMED GEOMETRIC CONSTANTS
# ==============================================================================
# Semantic color palettes mapping body parts to Raylib Color structs.
# In C++, this translates directly to a constant struct instance:
# const TacticalOpsPalette DEFAULT_TACTICAL_OPS_PALETTE = { ... };

DEFAULT_TACTICAL_OPS_PALETTE = {
    "armor": Color(48, 56, 65, 255),       # Tactical charcoal ballistic helmet
    "vest": Color(74, 85, 96, 255),        # Kevlar load-bearing vest
    "hands": Color(180, 150, 120, 255),    # Combat tactical gloves
    "visor": Color(0, 230, 255, 255),      # Cyan night-vision / HUD lens
    "weapon": Color(25, 28, 33, 255),      # Matte black carbine receiver
    "laser": Color(255, 30, 30, 200),      # Crimson laser targeting ray
    "outline": Color(18, 22, 28, 255),     # Contrast edge contour
}

STEALTH_TACTICAL_OPS_PALETTE = {
    "armor": Color(20, 35, 28, 255),       # Subdued woodland camo
    "vest": Color(35, 55, 42, 255),
    "hands": Color(90, 80, 70, 255),
    "visor": Color(80, 255, 120, 255),     # Emerald night-vision phosphor
    "weapon": Color(18, 20, 22, 255),
    "laser": Color(60, 255, 60, 200),      # Night-ops green laser ray
    "outline": Color(10, 15, 12, 255),
}

# Named geometric dimensions (replacing magic numbers for clarity & easy tuning)
BASE_RADIUS = 16.0
SHOULDER_RADIUS = 6.0
SHOULDER_OUTLINE_RADIUS = 7.5
SHOULDER_OFFSET_X = -2.0
SHOULDER_OFFSET_Y = 14.0
VEST_RADIUS = 11.5
VEST_OUTLINE_RADIUS = 13.0
WEAPON_WIDTH = 24.0
WEAPON_HEIGHT = 6.0
WEAPON_OFFSET_X = 18.0
WEAPON_OFFSET_Y = 8.0
HAND_RADIUS = 3.0
HAND_OUTLINE_RADIUS = 3.8
HAND_LEFT_OFFSET_X = 22.0
HAND_LEFT_OFFSET_Y = 6.0
HAND_RIGHT_OFFSET_X = 12.0
HAND_RIGHT_OFFSET_Y = 9.0
BARREL_FORWARD = 34.0
BARREL_SIDE = 8.0
LASER_LENGTH = 180.0
VISOR_OFFSET_X = 6.0
VISOR_OFFSET_Y = 5.0
WALK_SPEED = 6.0


# ==============================================================================
# PART 4: CANONICAL 2D DRAWING FUNCTION & ROTATION HELPER
# ==============================================================================
def rotate_vector_2d(vx: float, vy: float, angle_rad: float) -> tuple[float, float]:
    """
    Rotates a 2D local offset (vx, vy) by angle_rad (in radians).
    Returns (rx, ry) tuple. Translates directly to C++:
      float cos_a = cosf(angle_rad);
      float sin_a = sinf(angle_rad);
      float rx = (cos_a * vx) - (sin_a * vy);
      float ry = (sin_a * vx) + (cos_a * vy);
    """
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    rx = (cos_a * vx) - (sin_a * vy)
    ry = (sin_a * vx) + (cos_a * vy)
    return (rx, ry)


def draw_tactical_ops_2d(
    position: Vector2,
    facing_angle_rad: float = 0.0,
    anim_timer: float = 0.0,
    scale: float = 1.0,
    palette: dict = None
) -> None:
    """
    Renders an articulated 2D top-down Tactical Operator at position oriented along
    facing_angle_rad (radians) with procedural walking sway, weapon bob, and pulsing laser beam.
    Coordinates passed to pixel draw routines are explicitly cast to int for Raylib CFFI safety.
    """
    # 1. Fallback to default palette if None provided
    pal = palette
    if pal is None:
        pal = DEFAULT_TACTICAL_OPS_PALETTE

    c_armor = pal["armor"]
    c_vest = pal["vest"]
    c_hands = pal["hands"]
    c_visor = pal["visor"]
    c_weapon = pal["weapon"]
    c_laser = pal["laser"]
    c_outline = pal["outline"]

    # 2. Kinematic Sway & Breathing Oscillation
    sway = math.sin(anim_timer * WALK_SPEED) * 3.5 * scale
    breath = math.sin(anim_timer * 2.0) * 0.8 * scale
    scaled_base_radius = BASE_RADIUS * scale

    # 3. Laser Targeting Ray (Emitted forward from carbine barrel)
    barrel_fwd = BARREL_FORWARD * scale
    barrel_side = BARREL_SIDE * scale
    bx_off, by_off = rotate_vector_2d(barrel_fwd, barrel_side, facing_angle_rad)
    laser_start_x = int(position.x + bx_off)
    laser_start_y = int(position.y + by_off)

    laser_len = LASER_LENGTH * scale
    lx_off, ly_off = rotate_vector_2d(barrel_fwd + laser_len, barrel_side, facing_angle_rad)
    laser_end_x = int(position.x + lx_off)
    laser_end_y = int(position.y + ly_off)

    # Modulate laser alpha slightly for realistic optical beam flicker
    laser_alpha = int(170 + 75 * math.sin(anim_timer * 12.0))
    laser_alpha = max(0, min(255, laser_alpha))
    c_flicker_laser = Color(c_laser.r, c_laser.g, c_laser.b, laser_alpha)
    draw_line(laser_start_x, laser_start_y, laser_end_x, laser_end_y, c_flicker_laser)
    draw_circle(laser_end_x, laser_end_y, 2.5 * scale, c_flicker_laser)

    # 4. Articulated Shoulder Pads & Kevlar Vest (Torso)
    # Left Shoulder
    ls_x_off, ls_y_off = rotate_vector_2d(SHOULDER_OFFSET_X * scale, (SHOULDER_OFFSET_Y * scale) + sway, facing_angle_rad)
    ls_x = int(position.x + ls_x_off)
    ls_y = int(position.y + ls_y_off)
    draw_circle(ls_x, ls_y, SHOULDER_OUTLINE_RADIUS * scale, c_outline)
    draw_circle(ls_x, ls_y, SHOULDER_RADIUS * scale, c_armor)

    # Right Shoulder
    rs_x_off, rs_y_off = rotate_vector_2d(SHOULDER_OFFSET_X * scale, (-SHOULDER_OFFSET_Y * scale) - sway, facing_angle_rad)
    rs_x = int(position.x + rs_x_off)
    rs_y = int(position.y + rs_y_off)
    draw_circle(rs_x, rs_y, SHOULDER_OUTLINE_RADIUS * scale, c_outline)
    draw_circle(rs_x, rs_y, SHOULDER_RADIUS * scale, c_armor)

    # Armored Chestplate / Vest
    vest_x = int(position.x)
    vest_y = int(position.y)
    draw_circle(vest_x, vest_y, (VEST_OUTLINE_RADIUS * scale) + breath, c_outline)
    draw_circle(vest_x, vest_y, (VEST_RADIUS * scale) + breath, c_vest)

    # 5. Assault Carbine & Articulated Hands (Two-point weapon grip)
    # Weapon Receiver Body (Oriented along facing angle in degrees for DrawRectanglePro)
    wpn_x_off, wpn_y_off = rotate_vector_2d(WEAPON_OFFSET_X * scale, WEAPON_OFFSET_Y * scale, facing_angle_rad)
    wpn_x = position.x + wpn_x_off
    wpn_y = position.y + wpn_y_off
    wpn_rect = Rectangle(wpn_x, wpn_y, WEAPON_WIDTH * scale, WEAPON_HEIGHT * scale)
    wpn_origin = Vector2(4.0 * scale, 3.0 * scale)
    wpn_deg = facing_angle_rad * (180.0 / math.pi)
    draw_rectangle_pro(wpn_rect, wpn_origin, wpn_deg, c_weapon)

    # Carbine Suppressor / Muzzle Tip
    muz_x_off, muz_y_off = rotate_vector_2d(BARREL_FORWARD * scale, BARREL_SIDE * scale, facing_angle_rad)
    muz_x = int(position.x + muz_x_off)
    muz_y = int(position.y + muz_y_off)
    draw_circle(muz_x, muz_y, 2.2 * scale, c_armor)

    # Left Hand (Front Foregrip)
    lh_x_off, lh_y_off = rotate_vector_2d(HAND_LEFT_OFFSET_X * scale, HAND_LEFT_OFFSET_Y * scale, facing_angle_rad)
    lh_x = int(position.x + lh_x_off)
    lh_y = int(position.y + lh_y_off)
    draw_circle(lh_x, lh_y, HAND_OUTLINE_RADIUS * scale, c_outline)
    draw_circle(lh_x, lh_y, HAND_RADIUS * scale, c_hands)

    # Right Hand (Rear Trigger)
    rh_x_off, rh_y_off = rotate_vector_2d(HAND_RIGHT_OFFSET_X * scale, HAND_RIGHT_OFFSET_Y * scale, facing_angle_rad)
    rh_x = int(position.x + rh_x_off)
    rh_y = int(position.y + rh_y_off)
    draw_circle(rh_x, rh_y, HAND_OUTLINE_RADIUS * scale, c_outline)
    draw_circle(rh_x, rh_y, HAND_RADIUS * scale, c_hands)

    # 6. Ballistic Combat Helmet & Visor Slit
    helm_x = int(position.x)
    helm_y = int(position.y)
    draw_circle(helm_x, helm_y, (scaled_base_radius * 0.75) + 1.5, c_outline)
    draw_circle(helm_x, helm_y, scaled_base_radius * 0.75, c_armor)

    # Tactical HUD Visor (Arc slit in front of helmet)
    v1_x_off, v1_y_off = rotate_vector_2d(VISOR_OFFSET_X * scale, -VISOR_OFFSET_Y * scale, facing_angle_rad)
    v2_x_off, v2_y_off = rotate_vector_2d(VISOR_OFFSET_X * scale, VISOR_OFFSET_Y * scale, facing_angle_rad)
    v1_x = int(position.x + v1_x_off)
    v1_y = int(position.y + v1_y_off)
    v2_x = int(position.x + v2_x_off)
    v2_y = int(position.y + v2_y_off)
    draw_line(v1_x, v1_y, v2_x, v2_y, c_visor)


# ==============================================================================
# PART 5: C++ MAPPING & MEMORY LAYOUT REFERENCE
# ==============================================================================
# In C++ (raylib.h), this entire module maps 1-to-1 with zero dynamic allocation:
#
# struct TacticalOpsPalette {
#     Color armor;
#     Color vest;
#     Color hands;
#     Color visor;
#     Color weapon;
#     Color laser;
#     Color outline;
# };
#
# void RotateVector2D(float vx, float vy, float angle_rad, float* out_x, float* out_y);
# void DrawTacticalOps2D(Vector2 position, float facing_angle_rad, float anim_timer, float scale, const TacticalOpsPalette* palette);
#
# Memory Layout & Performance:
# - TacticalOpsPalette is a flat struct of 7 Color structs (28 bytes total, 4 bytes each: r, g, b, a).
# - Position is a Vector2 (8 bytes: float x, float y).
# - All trigonometric calculations (sin, cos) execute in registers with zero heap allocation.
# - Renders directly to the active framebuffer via immediate Raylib draw calls.


# ==============================================================================
# PART 6: STANDALONE 2D PREVIEW CANVAS (SpritePreviewApp)
# ==============================================================================
class SpritePreviewApp:
    """
    Interactive 2D preview canvas allowing inspection, continuous steering,
    animation speed adjustment, scale zooming, palette swapping, and smoke testing.
    """
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        init_window(self.screen_width, self.screen_height, "2D Sprite Inspector - Tactical Ops")
        set_target_fps(60)

        self.center = Vector2(self.screen_width / 2.0, self.screen_height / 2.0)
        self.facing_angle = 0.0
        self.anim_timer = 0.0
        self.anim_playing = True
        self.scale = 2.0

        self.active_palette_idx = 0
        self.palettes = [DEFAULT_TACTICAL_OPS_PALETTE, STEALTH_TACTICAL_OPS_PALETTE]
        self.palette_names = ["Tactical Slate", "Stealth Recon"]

    def update(self):
        dt = min(get_frame_time(), 0.05)
        if self.anim_playing:
            self.anim_timer += dt

        # Aim towards mouse cursor when mouse moves
        mouse_pos = get_mouse_position()
        dx = mouse_pos.x - self.center.x
        dy = mouse_pos.y - self.center.y
        if math.sqrt(dx * dx + dy * dy) > 20.0:
            self.facing_angle = math.atan2(dy, dx)

        # Keyboard Manual Controls
        if is_key_down(KEY_LEFT) or is_key_down(KEY_A):
            self.facing_angle -= 3.0 * dt
        if is_key_down(KEY_RIGHT) or is_key_down(KEY_D):
            self.facing_angle += 3.0 * dt

        # Toggle Animation Play/Pause
        if is_key_pressed(KEY_SPACE):
            self.anim_playing = not self.anim_playing

        # Cycle Palettes
        if is_key_pressed(KEY_P) or is_key_pressed(KEY_ONE):
            self.active_palette_idx = (self.active_palette_idx + 1) % len(self.palettes)

        # Scale Adjustment (+ / -)
        if is_key_pressed(KEY_EQUAL) or is_key_pressed(KEY_KP_ADD):
            self.scale = min(5.0, self.scale + 0.5)
        if is_key_pressed(KEY_MINUS) or is_key_pressed(KEY_KP_SUBTRACT):
            self.scale = max(0.5, self.scale - 0.5)

    def draw(self):
        begin_drawing()
        clear_background(Color(22, 26, 35, 255))

        # Background Subtle Coordinate Grid
        grid_step = 40
        for x in range(0, self.screen_width, grid_step):
            draw_line(int(x), 0, int(x), self.screen_height, Color(30, 36, 48, 255))
        for y in range(0, self.screen_height, grid_step):
            draw_line(0, int(y), self.screen_width, int(y), Color(30, 36, 48, 255))

        # Draw Sprite at Screen Center
        draw_tactical_ops_2d(
            self.center,
            facing_angle_rad=self.facing_angle,
            anim_timer=self.anim_timer,
            scale=self.scale,
            palette=self.palettes[self.active_palette_idx]
        )

        # HUD & Telemetry (Clear of top-bar region x=450..980)
        draw_text("2D SPRITE INSPECTOR: Tactical Spec-Ops Operator", 24, 20, 20, RAYWHITE)
        draw_text("[Mouse / A-D] Aim | [Space] Play/Pause | [P] Cycle Palette | [+/-] Scale", 24, 52, 14, LIGHTGRAY)
        draw_text(f"Palette: {self.palette_names[self.active_palette_idx]} | Scale: {self.scale:.1f}x", 24, 76, 14, YELLOW)
        angle_deg = self.facing_angle * (180.0 / math.pi) % 360.0
        draw_text(f"Angle: {angle_deg:.1f} deg | Anim Timer: {self.anim_timer:.2f}s", 24, 98, 14, SKYBLUE)

        # Global Top-Bar Integration
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
        close_window()


if __name__ == "__main__":
    is_smoke = "--smoke-test" in sys.argv
    SpritePreviewApp().run(smoke_test=is_smoke)
```

---

## 3. Minigame Integration & Import Standards

### 3.1 Importing 2D Sprites in Minigames

Minigames can import procedural sprites using either key-based loaders or granular per-module imports:

```python
# Option A: Key-Based Loader via asset_loader (Standard minigame pattern)
from assets.asset_loader import sprites_2D, load_sprite_2d
draw_tactical_ops_2d, DEFAULT_TACTICAL_OPS_PALETTE = load_sprite_2d("tactical_ops")

# Option B: Granular Import (Explicit dependency tracking)
from assets.sprites_2D.top_down.tactical_ops import draw_tactical_ops_2d, DEFAULT_TACTICAL_OPS_PALETTE
```

### 3.2 Invocation Inside Minigame Draw Loop

Inside any 2D minigame prototype (e.g. `minigames/3.2_combat_weapons/active_reload_timing.py`), invoke the sprite within screen-space or a 2D camera viewport (`begin_mode_2d(camera)`):

```python
# Inside Minigame draw():
# Render the player entity with smooth facing orientation and walking animation
draw_tactical_ops_2d(
    position=self.player.pos,
    facing_angle_rad=self.player.aim_angle,
    anim_timer=self.player.walk_timer,
    scale=1.2,
    palette=DEFAULT_TACTICAL_OPS_PALETTE
)
```

### 3.3 Mandatory Rule: Assets-Only Minigames

Minigames must use **only assets that currently exist** in `assets/` (`assets/sprites_2D/<category>/`, `assets/models_3D/<category>/`, `assets/audio/SFX/<category>/`, `assets/audio/BGM/<vibe>/`).
- Subagents and developers must **never** create inline placeholder art/primitives or fabricate mock asset files inside minigame code.
- If a minigame task references a 2D sprite that has not yet been implemented, the agent must **STOP IMMEDIATELY, report the missing asset to the orchestrator/user, and request that the asset be created first** before writing the minigame.
---

## 4. 2D Sprite Categorization Overview

All planned sprites in [`tasks/sprites_2D.csv`](../tasks/sprites_2D.csv) are categorized across 5 architectural classes, each stored in its dedicated subfolder under `assets/sprites_2D/`:

- **Top-Down Actors & Humanoids** (`assets/sprites_2D/top_down/`): Top-down soldiers, spec-ops operators, riot enforcers, battle mages, flamethrower pyros, and ghillie infiltrators.
- **Side-Scrolling Entities** (`assets/sprites_2D/side_scroller/`): Platformer knights, deformable slime blobs, steampunk automatons, gargoyle sentries, and wheel raiders.
- **Swarms & Floating Organisms** (`assets/sprites_2D/swarm_floating/`): Airborne drones, abyssal jellyfish, micro-nanite swarms, beholder eyes, plasma wisps, and cyber mosquitoes.
- **Mechanical Crawlers & Automatons** (`assets/sprites_2D/crawler_automaton/`): Insectoid crawlers, mine-layer bots, clockwork centipedes, tread dozers, sentry turrets, and hover-hoppers.
- **Projectile VFX & HUD Reticle Sprites** (`assets/sprites_2D/projectile_vfx/`): Railgun shockcones, thermal plasma bursts, smart-lock missile reticles, EMP lightning arcs, and grenade trajectory pips.

---

## 5. Querying & Updating Tasks via CLI & Python `csv`

Subagents and automated scripts query [`tasks/sprites_2D.csv`](../tasks/sprites_2D.csv) using the headless `tasks.py` CLI (<50ms, zero Raylib GUI window) or Python's standard library `csv` module (<50 tokens per query).

### 5.1 Find Pending 2D Sprites in a Category (Fast CLI)
```bash
python -B tasks.py --list sprites_2D --category top_down --status pending --limit 3
```

### 5.2 Fetch Full 2D Sprite Specifications by ID (Fast CLI)
```bash
python -B tasks.py --get sprites_2D s2d_top_tactical_ops
```

### 5.3 Check if Concept Name Already Exists (Prevent Collisions)
```bash
python -B tasks.py --check sprites_2D "Tactical Ops"
```

### 5.4 Synchronize 2D Sprite Status Automatically (Fast CLI)
```bash
python -B tasks.py --sync-statuses sprites_2D
```

### 5.5 Fallback: Python Standard Library `csv` One-Liners
```bash
# Query pending in top_down category
python -B -c "import csv; f=open('tasks/sprites_2D.csv', encoding='utf-8-sig'); r=csv.DictReader(f); print(next(dict(id=x['id'], func=x['function_name'], file=x['target_file']) for x in r if x['category']=='top_down' and x['status']=='pending'))"

# Count pending vs done 2D sprites
python -B -c "import csv; from collections import Counter; f=open('tasks/sprites_2D.csv', encoding='utf-8-sig'); c=Counter((x['category'], x['status']) for x in csv.DictReader(f)); [print(f'{k[0]} [{k[1]}]: {v}') for k, v in sorted(c.items())]"
```

---

## 6. Human Spreadsheet Editing & Tasks Editor (`tasks.py`)

To inspect, sort, and edit [`tasks/sprites_2D.csv`](../tasks/sprites_2D.csv) without risking CSV delimiter or encoding corruption:
1. **Interactive Tasks Editor (`tasks.py`)**: Run `python -B tasks.py` to open the graphical Raylib task manager with hot-switching, sorting, cell editing, horizontal scrolling, and "Adjusted Text" (Wrap Text).
2. **Never alter column header names**: The first row must keep `id,category,concept_name,function_name,target_file,primitives_used,animation_features,palette_keys,status,description`.
3. **Allowed status values**: strictly binary `pending` (file absent from disk) and `done` (file present on disk). Statuses are automatically synchronized via `python -B tasks.py --sync-statuses`.
