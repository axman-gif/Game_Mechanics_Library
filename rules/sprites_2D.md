# 2D Procedural Sprites Architectural Guidelines & Registry (`assets/sprites_2D/`)
=============================================================================

This document defines the architectural standards, vector primitive rendering rules, procedural animation interfaces, and a copy-pasteable **code template** for all 2D procedural sprites.

All 2D sprite task tracking, vector specifications, and progress statuses are maintained in the companion spreadsheet:
👉 [**`tasks/sprites_2D.csv`**](../tasks/sprites_2D.csv) (29 planned sprites: 4 base sprites and 25 specialized sprites)

---

## 1. Golden Architecture Rules for 2D Procedural Sprites

1. **Pure Geometric Primitives**: All 2D sprites are drawn directly onto the framebuffer using Raylib 2D vector calls (`draw_circle_v`, `draw_rectangle_pro`, `draw_line_ex`, `draw_triangle`, `draw_poly`). External raster image files (`.png`, `.jpg`, `.bmp`, `.tga`) and sprite sheets are strictly forbidden.
2. **Language-Agnostic & C++-Transferable Code**:
   In alignment with [`README.md`](../README.md) and [`AGENTS.md`](../AGENTS.md), sprite drawing functions must be written as pure imperative routines without decorators (`@dataclass`), generators (`yield`), or dynamic metaclasses. All geometric transformations must use basic trigonometry (`math.sin`, `math.cos`) and explicit vector math that translates 1-to-1 to C++ (`raylib.h`) and C#.
3. **Canonical Procedural Animation Interface**:
   Every 2D sprite drawing function must accept standardized procedural animation arguments:
```python
def draw_sprite_name_2d(
    position: Vector2,
    facing_angle_rad: float = 0.0,
    anim_timer: float = 0.0,
    scale: float = 1.0,
    palette: dict = None
) -> None:
    pass
```
4. **Color Palettes with Concrete Defaults**: Every sprite must expose an explicit default dictionary mapping semantic parts (`body`, `armor`, `accent`, `outline`, `eye`, `weapon`) to Raylib `Color` instances. When `palette=None` is passed, it uses its documented `DEFAULT_<NAME>_PALETTE`.
5. **Default Destination Directory**: All 2D procedural sprites are strictly located in `assets/sprites_2D/`.
6. **2D Rendering Order & Int Casting**: Ensure all coordinates and dimensions passed to non-vector draw routines (`draw_rectangle`, `draw_text`) are explicitly cast to `int` to satisfy Raylib CFFI type contracts. Vector routines (`draw_circle_v`, `draw_rectangle_pro`) take `Vector2`.
7. **Strict Sizing Bounds**: Every 2D procedural sprite module must strictly remain within the **400 to 800 line** target range (floor: **400 lines**, hard ceiling: **1,000 lines**). Scripts below 400 lines lack pedagogical explanations and vector animation loops; scripts above 1,000 lines cause token bloat.
8. **Standalone Previewer & Automated `--smoke-test`**:
   Every sprite file must be standalone executable (`if __name__ == "__main__":`). Running `python -B assets/sprites_2D/<file>.py` opens an interactive 2D Vector Preview Canvas. Running with `--smoke-test` renders 3 frames headlessly and exits with code `0`.

---

## 2. Standard 2D Sprite Code Template

Every craftsman subagent creating a 2D sprite must follow this exact anatomy. Copy and adapt this template for your target asset:

```python
# -*- coding: utf-8 -*-
"""
Tactical Spec-Ops Operator - 2D Procedural Vector Sprite
========================================================
Category         : top_down
Target File      : assets/sprites_2D/tactical_ops.py
Primitives Used  : Circles (helmet, hands, shoulders), Rectangles (torso vest, weapon), Lines (laser sight)
Animation Loop   : Walking shoulder-sway, weapon recoil pulse, tactical laser pulsation, breathing squash

Problem Solved:
  Eliminates pixel art texture dependencies and resolution-scaling blur by rendering
  an articulated top-down soldier purely from vector primitives, rotation matrices,
  and trigonometric oscillation in real time.

How the Procedural Articulation Works:
  - Vector transforms use standard 2D rotation formulas:
      x' = cos(theta) * dx - sin(theta) * dy
      y' = sin(theta) * dx + cos(theta) * dy
  - Walking produces alternating counter-phase shoulder sway and weapon bob via math.sin(anim_timer * speed).
  - Aiming laser pulses opacity using sinusoidal modulation: 180 + 75 * sin(anim_timer * 10).

C++ Raylib Equivalent:
  struct TacticalOpsPalette { Color armor; Color vest; Color hands; Color visor; Color weapon; Color laser; };
  void DrawTacticalOps2D(Vector2 position, float facing_angle_rad, float anim_timer, float scale, const TacticalOpsPalette* palette);
  Mapped directly to DrawCircleV, DrawRectanglePro, and DrawLineEx from raylib.h.
"""

import sys
import os
import math

# 1. Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# 2. Add repository root to search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# 3. Mandatory Raylib and utility imports
from pyray import *
from utils import *

# ==============================================================================
# SEMANTIC COLOR PALETTES (Exposes concrete defaults)
# ==============================================================================
# Mapping semantic body parts to Raylib Color structs.
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


# ==============================================================================
# VECTOR ROTATION & COORDINATE MATH HELPERS (C++-Transferable)
# ==============================================================================
def rotate_vector_2d(dx: float, dy: float, cos_a: float, sin_a: float) -> Vector2:
    """
    Rotates a 2D local offset (dx, dy) by precomputed cos(a) and sin(a).
    Translates directly to:
      Vector2 r = { cos_a * dx - sin_a * dy, sin_a * dx + cos_a * dy };
    """
    rx = (cos_a * dx) - (sin_a * dy)
    ry = (sin_a * dx) + (cos_a * dy)
    return Vector2(rx, ry)


# ==============================================================================
# CORE PROCEDURAL 2D DRAWING FUNCTION
# ==============================================================================
def draw_tactical_ops_2d(
    position: Vector2,
    facing_angle_rad: float = 0.0,
    anim_timer: float = 0.0,
    scale: float = 1.0,
    palette: dict = None
) -> None:
    """
    Renders an articulated 2D top-down Tactical Operator at position oriented along
    facing_angle_rad with procedural walking sway, weapon bob, and pulsing laser beam.
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

    # 2. Trigonometric basis vectors for orientation
    cos_a = math.cos(facing_angle_rad)
    sin_a = math.sin(facing_angle_rad)

    # 3. Kinematic Sway & Breathing Oscillation
    walk_speed = 6.0
    sway = math.sin(anim_timer * walk_speed) * 3.5 * scale
    breath = math.sin(anim_timer * 2.0) * 0.8 * scale
    base_radius = 16.0 * scale

    # 4. Laser Targeting Ray (Emitted forward from carbine barrel)
    barrel_forward = 34.0 * scale
    barrel_side = 8.0 * scale
    b_off = rotate_vector_2d(barrel_forward, barrel_side, cos_a, sin_a)
    laser_start = Vector2(position.x + b_off.x, position.y + b_off.y)

    laser_len = 180.0 * scale
    laser_end_off = rotate_vector_2d(barrel_forward + laser_len, barrel_side, cos_a, sin_a)
    laser_end = Vector2(position.x + laser_end_off.x, position.y + laser_end_off.y)

    # Modulate laser alpha slightly for realistic optical beam flicker
    laser_alpha = int(170 + 75 * math.sin(anim_timer * 12.0))
    laser_alpha = max(0, min(255, laser_alpha))
    c_flicker_laser = Color(c_laser.r, c_laser.g, c_laser.b, laser_alpha)
    draw_line_ex(laser_start, laser_end, 1.8 * scale, c_flicker_laser)
    draw_circle_v(laser_end, 2.5 * scale, c_flicker_laser)

    # 5. Articulated Shoulder Pads & Kevlar Vest (Torso)
    # Left Shoulder (dx = -2.0, dy = -14.0 + sway)
    ls_off = rotate_vector_2d(-2.0 * scale, (-14.0 * scale) + sway, cos_a, sin_a)
    ls_pos = Vector2(position.x + ls_off.x, position.y + ls_off.y)
    draw_circle_v(ls_pos, 7.5 * scale, c_outline)
    draw_circle_v(ls_pos, 6.0 * scale, c_armor)

    # Right Shoulder (dx = -2.0, dy = 14.0 - sway)
    rs_off = rotate_vector_2d(-2.0 * scale, (14.0 * scale) - sway, cos_a, sin_a)
    rs_pos = Vector2(position.x + rs_off.x, position.y + rs_off.y)
    draw_circle_v(rs_pos, 7.5 * scale, c_outline)
    draw_circle_v(rs_pos, 6.0 * scale, c_armor)

    # Armored Chestplate / Vest
    vest_center_off = rotate_vector_2d(0.0, 0.0, cos_a, sin_a)
    vest_pos = Vector2(position.x + vest_center_off.x, position.y + vest_center_off.y)
    draw_circle_v(vest_pos, (13.0 * scale) + breath, c_outline)
    draw_circle_v(vest_pos, (11.5 * scale) + breath, c_vest)

    # 6. Assault Carbine & Articulated Hands (Two-point weapon grip)
    # Weapon Receiver Body (Oriented along facing angle)
    wpn_off = rotate_vector_2d(18.0 * scale, 8.0 * scale, cos_a, sin_a)
    wpn_pos = Vector2(position.x + wpn_off.x, position.y + wpn_off.y)
    wpn_rect = Rectangle(wpn_pos.x, wpn_pos.y, 24.0 * scale, 6.0 * scale)
    wpn_origin = Vector2(4.0 * scale, 3.0 * scale)
    wpn_deg = facing_angle_rad * (180.0 / math.pi)
    draw_rectangle_pro(wpn_rect, wpn_origin, wpn_deg, c_weapon)

    # Carbine Suppressor / Muzzle Tip
    muz_off = rotate_vector_2d(32.0 * scale, 8.0 * scale, cos_a, sin_a)
    draw_circle_v(Vector2(position.x + muz_off.x, position.y + muz_off.y), 2.2 * scale, c_armor)

    # Left Hand (Front Foregrip: dx = 22.0, dy = 6.0)
    lh_off = rotate_vector_2d(22.0 * scale, 6.0 * scale, cos_a, sin_a)
    lh_pos = Vector2(position.x + lh_off.x, position.y + lh_off.y)
    draw_circle_v(lh_pos, 3.8 * scale, c_outline)
    draw_circle_v(lh_pos, 3.0 * scale, c_hands)

    # Right Hand (Rear Trigger: dx = 12.0, dy = 9.0)
    rh_off = rotate_vector_2d(12.0 * scale, 9.0 * scale, cos_a, sin_a)
    rh_pos = Vector2(position.x + rh_off.x, position.y + rh_off.y)
    draw_circle_v(rh_pos, 3.8 * scale, c_outline)
    draw_circle_v(rh_pos, 3.0 * scale, c_hands)

    # 7. Ballistic Combat Helmet & Visor Slit
    helm_off = rotate_vector_2d(0.0, 0.0, cos_a, sin_a)
    helm_pos = Vector2(position.x + helm_off.x, position.y + helm_off.y)
    draw_circle_v(helm_pos, (base_radius * 0.75) + 1.5, c_outline)
    draw_circle_v(helm_pos, base_radius * 0.75, c_armor)

    # Tactical HUD Visor (Arc slit in front of helmet)
    v_start_off = rotate_vector_2d(6.0 * scale, -5.0 * scale, cos_a, sin_a)
    v_end_off = rotate_vector_2d(6.0 * scale, 5.0 * scale, cos_a, sin_a)
    v_start = Vector2(position.x + v_start_off.x, position.y + v_start_off.y)
    v_end = Vector2(position.x + v_end_off.x, position.y + v_end_off.y)
    draw_line_ex(v_start, v_end, 2.5 * scale, c_visor)


# ==============================================================================
# STANDALONE INTERACTIVE VIEWER & AUTOMATED SMOKE TEST
# ==============================================================================
class Sprite2DViewer:
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
        self.auto_rotate = False

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
            draw_line(x, 0, x, self.screen_height, Color(30, 36, 48, 255))
        for y in range(0, self.screen_height, grid_step):
            draw_line(0, y, self.screen_width, y, Color(30, 36, 48, 255))

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
    Sprite2DViewer().run(smoke_test=is_smoke)
```

---

## 3. Minigame Integration Example

To render this sprite in any 2D minigame prototype (e.g. `minigames/3.2_combat_weapons/active_reload_timing.py`):

```python
from assets.sprites_2D.tactical_ops import draw_tactical_ops_2d, DEFAULT_TACTICAL_OPS_PALETTE

# Inside Minigame draw():
# Render the player entity with smooth mouse-facing orientation
draw_tactical_ops_2d(
    position=self.player.pos,
    facing_angle_rad=self.player.aim_angle,
    anim_timer=self.player.walk_timer,
    scale=1.2,
    palette=DEFAULT_TACTICAL_OPS_PALETTE
)
```

---

## 4. 2D Sprite Categorization Overview

All 29 sprites in [`tasks/sprites_2D.csv`](../tasks/sprites_2D.csv) are categorized across 5 architectural classes:

- **Top-Down Actors & Humanoids** (6 sprites): Top-down soldiers, spec-ops operators, riot enforcers, battle mages, flamethrower pyros, and ghillie infiltrators.
- **Side-Scrolling Entities** (6 sprites): Platformer knights, deformable slime blobs, steampunk automatons, gargoyle sentries, and wheel raiders.
- **Swarms & Floating Organisms** (6 sprites): Airborne drones, abyssal jellyfish, micro-nanite swarms, beholder eyes, plasma wisps, and cyber mosquitoes.
- **Mechanical Crawlers & Automatons** (6 sprites): Insectoid crawlers, mine-layer bots, clockwork centipedes, tread dozers, sentry turrets, and hover-hoppers.
- **Projectile VFX & HUD Reticle Sprites** (5 sprites): Railgun shockcones, thermal plasma bursts, smart-lock missile reticles, EMP lightning arcs, and grenade trajectory pips.

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
python -B tasks.py --check models_3D "Tactical Ops"
```

### 5.4 Mark a 2D Sprite as Built (Fast CLI)
```bash
python -B tasks.py --set-status sprites_2D s2d_top_tactical_ops built
```

### 5.5 Fallback: Python Standard Library `csv` One-Liners
```bash
# Query pending in top_down category
python -B -c "import csv; f=open('tasks/sprites_2D.csv', encoding='utf-8-sig'); r=csv.DictReader(f); print(next(dict(id=x['id'], func=x['function_name'], file=x['target_file']) for x in r if x['category']=='top_down' and x['status']=='pending'))"

# Count pending vs built 2D sprites
python -B -c "import csv; from collections import Counter; f=open('tasks/sprites_2D.csv', encoding='utf-8-sig'); c=Counter((x['category'], x['status']) for x in csv.DictReader(f)); [print(f'{k[0]} [{k[1]}]: {v}') for k, v in sorted(c.items())]"
```

---

## 6. Human Spreadsheet Editing & Tasks Editor (`tasks.py`)

To inspect, sort, and edit [`tasks/sprites_2D.csv`](../tasks/sprites_2D.csv) without risking CSV delimiter or encoding corruption:
1. **Interactive Tasks Editor (`tasks.py`)**: Run `python -B tasks.py` to open the graphical Raylib task manager with hot-switching, sorting, cell editing, horizontal scrolling, and "Adjusted Text" (Wrap Text).
2. **Never alter column header names**: The first row must keep `id,category,concept_name,function_name,target_file,primitives_used,animation_features,palette_keys,status,description`.
3. **Allowed status values**: `pending`, `in_progress`, `built`.
