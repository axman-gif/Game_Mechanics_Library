# 3D Procedural Models Architectural Guidelines & Registry (`assets/models_3D/`)
=============================================================================

This document defines the architectural standards, procedural primitive construction rules, animation interfaces, and a copy-pasteable **code template** for all 3D procedural models.

All 3D model task tracking, primitive specifications, and progress statuses are maintained in the companion spreadsheet:
👉 [**`tasks/models_3D.csv`**](../tasks/models_3D.csv) (29 planned models: 4 base models and 25 specialized models)

---

## 1. Golden Architecture Rules for 3D Procedural Models

1. **Pure Geometric Primitives**: All 3D models are constructed purely from mathematical 3D primitives (`draw_sphere`, `draw_cube`, `draw_cylinder_ex`). External 3D mesh files (`.obj`, `.gltf`, `.fbx`, `.blend`) and textured materials are strictly forbidden.
2. **Language-Agnostic & C++-Transferable Code**:
   In alignment with [`README.md`](../README.md) and [`AGENTS.md`](../AGENTS.md), model renderers must be written in transparent, imperative code without decorators (`@dataclass`, `@property`), generators (`yield`), or dynamic metaclasses. Calculations must rely on explicit trigonometry (`math.sin`, `math.cos`) and basic vector math that translates 1-to-1 to C++ (`raylib.h`) and C#.
3. **Canonical Procedural Animation Interface**:
   Every 3D model drawing function must accept standardized procedural animation arguments:
```python
def draw_model_name_3d(
    position: Vector3,
    rotation_y: float = 0.0,
    anim_timer: float = 0.0,
    scale: float = 1.0,
    palette: dict = None
) -> None:
    pass
```
4. **Color Palettes with Concrete Defaults**: Every model must expose an explicit default dictionary mapping semantic body parts (`armor`, `joints`, `visor`, `core`, `thruster`) to Raylib `Color` instances. When `palette=None` is passed, it uses its documented `DEFAULT_<NAME>_PALETTE`.
5. **Default Destination Directory**: All 3D procedural models are strictly located in `assets/models_3D/`.
6. **3D Camera Context**: All 3D model drawing routines must execute inside `begin_mode_3d(camera)` ... `end_mode_3d()`. HUD and screen-space text projections must occur outside 3D mode.
7. **Strict Sizing Bounds**: Every 3D procedural model module must strictly remain within the **400 to 800 line** target range (floor: **400 lines**, hard ceiling: **1,000 lines**). Scripts below 400 lines lack pedagogical explanations and articulated animation logic; scripts above 1,000 lines cause token bloat.
8. **Standalone Previewer & Automated `--smoke-test`**:
   Every model file must be standalone executable (`if __name__ == "__main__":`). Running `python -B assets/models_3D/<file>.py` opens an interactive 3D Orbit Viewer. Running with `--smoke-test` renders 3 frames headlessly and exits with code `0`.

---

## 2. Standard 3D Model Code Template

Every craftsman subagent creating a 3D model must follow this exact anatomy. Copy and adapt this template for your target asset:

```python
# -*- coding: utf-8 -*-
"""
Exo-Knight Heavy Armored Unit - 3D Procedural Primitive Model
============================================================
Category         : humanoid
Target File      : assets/models_3D/exo_knight.py
Primitives Used  : Spheres (pauldrons, helmet, joints), Cubes (chestplate, gauntlets), Cylinders (limbs, sword)
Animation Loop   : Walking stride gait, arm counter-swing, breathing chest rise, idle weapon bob

Problem Solved:
  Eliminates bulky 3D mesh files (.obj/.fbx) and external texture dependencies by
  synthesizing an articulated armored biped purely from Raylib geometric primitives
  and trigonometric transforms in real time.

How the Procedural Articulation Works:
  - The model hierarchy is computed relative to a base 'position' (Vector3).
  - Walk cycles use sinusoidal oscillation: leg angles swing via math.sin(anim_timer * speed).
  - Counter-phase oscillation: the left and right limbs oscillate with an angular phase offset of pi.
  - Sword blade and visor emit procedural specular glow via contrasting palette highlights.

C++ Raylib Equivalent:
  struct ExoKnightPalette { Color armor; Color armor_dark; Color joints; Color visor; Color core; Color blade; };
  void DrawExoKnight3D(Vector3 position, float rotation_y, float anim_timer, float scale, const ExoKnightPalette* palette);
  Mapped directly to DrawCube, DrawSphere, and DrawCylinderEx from raylib.h.
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
# const ExoKnightPalette DEFAULT_EXO_KNIGHT_PALETTE = { ... };

DEFAULT_EXO_KNIGHT_PALETTE = {
    "armor": Color(45, 55, 72, 255),        # Deep charcoal tactical plate
    "armor_dark": Color(28, 34, 46, 255),   # Under-suit plating
    "joints": Color(100, 110, 125, 255),    # Exposed mechanical servos
    "visor": Color(0, 220, 255, 255),       # Cyan HUD visor slit
    "core": Color(255, 170, 0, 255),        # Amber fusion chest reactor
    "blade": Color(220, 235, 255, 255),     # Plasma edge highlight
    "accent": Color(200, 40, 40, 255),      # Warning hazard stripes
}

DESERT_EXO_KNIGHT_PALETTE = {
    "armor": Color(160, 130, 90, 255),      # Desert tan ceramic
    "armor_dark": Color(110, 90, 60, 255),
    "joints": Color(80, 70, 60, 255),
    "visor": Color(255, 120, 0, 255),       # Solar orange visor
    "core": Color(0, 230, 180, 255),
    "blade": Color(255, 240, 200, 255),
    "accent": Color(60, 120, 60, 255),
}


# ==============================================================================
# CORE PROCEDURAL 3D DRAWING FUNCTION
# ==============================================================================
def draw_exo_knight_3d(
    position: Vector3,
    rotation_y: float = 0.0,
    anim_timer: float = 0.0,
    scale: float = 1.0,
    palette: dict = None
) -> None:
    """
    Renders an articulated 3D Exo-Knight at position with procedural walking and breathing animation.
    Must be called between begin_mode_3d(camera) and end_mode_3d().
    """
    # 1. Fallback to default palette if None provided
    pal = palette
    if pal is None:
        pal = DEFAULT_EXO_KNIGHT_PALETTE

    c_armor = pal["armor"]
    c_armor_dark = pal["armor_dark"]
    c_joints = pal["joints"]
    c_visor = pal["visor"]
    c_core = pal["core"]
    c_blade = pal["blade"]
    c_accent = pal["accent"]

    # 2. Kinematic & Animation Timers (Continuous sinusoidal waves)
    walk_speed = 4.0
    walk_stride = math.sin(anim_timer * walk_speed)
    walk_bob = abs(math.cos(anim_timer * walk_speed)) * 0.12 * scale
    breath = math.sin(anim_timer * 1.5) * 0.03 * scale

    # Base root position with vertical walking bounce
    bx = position.x
    by = position.y + walk_bob
    bz = position.z

    # Trigonometric forward/right vectors based on rotation_y (in radians)
    rad_y = rotation_y * (math.pi / 180.0)
    cos_r = math.cos(rad_y)
    sin_r = math.sin(rad_y)

    # 3. Torso & Power Core (Central Mass)
    torso_y = by + (1.35 * scale) + breath
    torso_w = 0.70 * scale
    torso_h = 0.85 * scale
    torso_l = 0.45 * scale
    draw_cube(Vector3(bx, torso_y, bz), torso_w, torso_h, torso_l, c_armor)
    draw_cube_wires(Vector3(bx, torso_y, bz), torso_w, torso_h, torso_l, c_armor_dark)

    # Fusion Reactor Core (Front-facing glowing sphere)
    core_offset_z = 0.24 * scale
    core_x = bx + (sin_r * core_offset_z)
    core_z = bz + (cos_r * core_offset_z)
    draw_sphere(Vector3(core_x, torso_y + (0.1 * scale), core_z), 0.14 * scale, c_core)

    # 4. Articulated Head & Tactical Visor
    head_y = torso_y + (0.65 * scale)
    head_radius = 0.28 * scale
    draw_sphere(Vector3(bx, head_y, bz), head_radius, c_armor_dark)

    # Armored Crest (Helmet Ridge)
    crest_h = 0.12 * scale
    crest_l = 0.38 * scale
    draw_cube(Vector3(bx, head_y + (0.22 * scale), bz), 0.12 * scale, crest_h, crest_l, c_accent)

    # Glowing Visor Slit
    visor_offset_z = 0.22 * scale
    vx = bx + (sin_r * visor_offset_z)
    vz = bz + (cos_r * visor_offset_z)
    draw_cube(Vector3(vx, head_y, vz), 0.32 * scale, 0.08 * scale, 0.10 * scale, c_visor)

    # 5. Articulated Pauldrons & Shoulder Joints
    shoulder_spread = 0.52 * scale
    shoulder_y = torso_y + (0.32 * scale)

    # Left & Right Shoulder Spans
    ls_x = bx - (cos_r * shoulder_spread)
    ls_z = bz + (sin_r * shoulder_spread)
    rs_x = bx + (cos_r * shoulder_spread)
    rs_z = bz - (sin_r * shoulder_spread)

    draw_sphere(Vector3(ls_x, shoulder_y, ls_z), 0.22 * scale, c_armor)
    draw_sphere(Vector3(rs_x, shoulder_y, rs_z), 0.22 * scale, c_armor)

    # 6. Articulated Arms (Counter-swinging gait)
    arm_swing_angle = walk_stride * 0.45  # Radians
    arm_len = 0.60 * scale

    # Left Hand / Arm
    l_hand_y = shoulder_y - arm_len + (math.sin(arm_swing_angle) * 0.15 * scale)
    draw_cylinder_ex(
        Vector3(ls_x, shoulder_y, ls_z),
        Vector3(ls_x, l_hand_y, ls_z),
        0.09 * scale, 0.07 * scale, 6, c_joints
    )
    draw_sphere(Vector3(ls_x, l_hand_y, ls_z), 0.11 * scale, c_armor_dark)

    # Right Hand / Weapon Arm (Holding Plasma Greatsword)
    r_hand_y = shoulder_y - arm_len - (math.sin(arm_swing_angle) * 0.15 * scale)
    draw_cylinder_ex(
        Vector3(rs_x, shoulder_y, rs_z),
        Vector3(rs_x, r_hand_y, rs_z),
        0.09 * scale, 0.07 * scale, 6, c_joints
    )
    draw_sphere(Vector3(rs_x, r_hand_y, rs_z), 0.11 * scale, c_armor_dark)

    # Plasma Greatsword (Attached to Right Hand)
    sword_hilt_y = r_hand_y
    sword_tip_y = sword_hilt_y + (1.20 * scale)
    draw_cylinder_ex(
        Vector3(rs_x, sword_hilt_y, rs_z),
        Vector3(rs_x, sword_tip_y, rs_z),
        0.04 * scale, 0.02 * scale, 6, c_blade
    )
    draw_cube(Vector3(rs_x, sword_hilt_y + 0.1 * scale, rs_z), 0.25 * scale, 0.04 * scale, 0.06 * scale, c_accent)

    # 7. Articulated Legs (Pelvis, Thighs, Shins, Boots)
    pelvis_y = by + (0.85 * scale)
    leg_spread = 0.24 * scale
    leg_len = 0.85 * scale

    # Sinusoidal Stride Offsets
    l_stride = walk_stride * 0.35 * scale
    r_stride = -walk_stride * 0.35 * scale

    # Left Leg (Forward / Back)
    ll_x = bx - (cos_r * leg_spread) + (sin_r * l_stride)
    ll_z = bz + (sin_r * leg_spread) + (cos_r * l_stride)
    draw_cylinder_ex(
        Vector3(ll_x, pelvis_y, ll_z),
        Vector3(ll_x, by, ll_z),
        0.11 * scale, 0.08 * scale, 6, c_joints
    )
    # Left Armored Boot
    draw_cube(Vector3(ll_x, by + (0.1 * scale), ll_z), 0.22 * scale, 0.20 * scale, 0.35 * scale, c_armor)

    # Right Leg (Anti-phase)
    rl_x = bx + (cos_r * leg_spread) + (sin_r * r_stride)
    rl_z = bz - (sin_r * leg_spread) + (cos_r * r_stride)
    draw_cylinder_ex(
        Vector3(rl_x, pelvis_y, rl_z),
        Vector3(rl_x, by, rl_z),
        0.11 * scale, 0.08 * scale, 6, c_joints
    )
    # Right Armored Boot
    draw_cube(Vector3(rl_x, by + (0.1 * scale), rl_z), 0.22 * scale, 0.20 * scale, 0.35 * scale, c_armor)


# ==============================================================================
# STANDALONE INTERACTIVE VIEWER & AUTOMATED SMOKE TEST
# ==============================================================================
class Model3DViewer:
    """
    Interactive 3D previewer allowing inspection, rotation, zooming,
    palette swapping, and automated 3-frame smoke testing.
    """
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        init_window(self.screen_width, self.screen_height, "3D Model Inspector - Exo-Knight")
        set_target_fps(60)

        # 3D Orbit Camera Setup
        self.camera = Camera3D(
            Vector3(0.0, 3.0, 5.0),   # Position
            Vector3(0.0, 1.2, 0.0),   # Target
            Vector3(0.0, 1.0, 0.0),   # Up vector
            45.0,                     # FOV
            CAMERA_PERSPECTIVE
        )

        self.anim_timer = 0.0
        self.anim_playing = True
        self.rotation_y = 0.0
        self.active_palette_idx = 0
        self.palettes = [DEFAULT_EXO_KNIGHT_PALETTE, DESERT_EXO_KNIGHT_PALETTE]
        self.palette_names = ["Tactical Slate", "Desert Ceramic"]

    def update(self):
        dt = min(get_frame_time(), 0.05)
        if self.anim_playing:
            self.anim_timer += dt

        # Orbit Controls: Drag mouse left-click or use arrow keys
        if is_mouse_button_down(MOUSE_BUTTON_LEFT):
            delta = get_mouse_delta()
            self.rotation_y += delta.x * 0.5

        if is_key_down(KEY_LEFT):
            self.rotation_y -= 60.0 * dt
        if is_key_down(KEY_RIGHT):
            self.rotation_y += 60.0 * dt

        # Toggle Animation Play/Pause
        if is_key_pressed(KEY_SPACE):
            self.anim_playing = not self.anim_playing

        # Cycle Palettes
        if is_key_pressed(KEY_P) or is_key_pressed(KEY_ONE):
            self.active_palette_idx = (self.active_palette_idx + 1) % len(self.palettes)

        # Zoom via Mouse Wheel
        wheel = get_mouse_wheel_move()
        if wheel != 0.0:
            cam_dist = math.sqrt(self.camera.position.x**2 + self.camera.position.z**2)
            cam_dist = max(2.0, min(12.0, cam_dist - wheel * 0.8))
            self.camera.position.z = cam_dist

    def draw(self):
        begin_drawing()
        clear_background(Color(18, 22, 30, 255))

        # 3D Scene Rendering
        begin_mode_3d(self.camera)
        draw_grid(10, 1.0)
        draw_exo_knight_3d(
            Vector3(0.0, 0.0, 0.0),
            rotation_y=self.rotation_y,
            anim_timer=self.anim_timer,
            scale=1.0,
            palette=self.palettes[self.active_palette_idx]
        )
        end_mode_3d()

        # HUD & Telemetry Overlay (Keeps x=450..980 clear for global bar)
        draw_text("3D MODEL INSPECTOR: Exo-Knight Heavy Armored Unit", 24, 20, 20, RAYWHITE)
        draw_text("[L-Drag / Left-Right] Rotate | [Space] Play/Pause | [P] Cycle Palette", 24, 52, 14, LIGHTGRAY)
        draw_text(f"Palette: {self.palette_names[self.active_palette_idx]}", 24, 76, 14, YELLOW)
        draw_text(f"Anim Timer: {self.anim_timer:.2f}s | Rotation: {self.rotation_y:.1f} deg", 24, 98, 14, SKYBLUE)

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
    Model3DViewer().run(smoke_test=is_smoke)
```

---

## 3. Minigame Integration Example

To render this model in any minigame prototype (e.g. `minigames/3.0_core_prototypes/titan_strider.py`):

```python
from assets.models_3D.exo_knight import draw_exo_knight_3d, DEFAULT_EXO_KNIGHT_PALETTE

# Inside Minigame draw():
begin_mode_3d(self.camera)
# Render boss or enemy unit
draw_exo_knight_3d(
    position=self.boss.position,
    rotation_y=self.boss.facing_angle,
    anim_timer=self.boss.stride_timer,
    scale=1.5,
    palette=DEFAULT_EXO_KNIGHT_PALETTE
)
end_mode_3d()
```

---

## 4. 3D Model Categorization Overview

All 29 models in [`tasks/models_3D.csv`](../tasks/models_3D.csv) are categorized across 5 architectural classes:

- **Characters & Humanoids** (6 models): Bipedal soldiers, exo-knights, cyber ninjas, industrial miners, psionic cultists, and riot vanguards.
- **Beasts & Quadruped Organisms** (6 models): Four-legged predators, armored pangolins, sabertooth prowlers, arachnid stalkers, sand wyrms, and spore bulls.
- **Drones & Airborne Constructs** (6 models): Hovering recon drones, tri-rotor hexacopters, stealth flying wings, kinetic dropships, and nanite carriers.
- **Turrets, Bosses & Heavy Armor** (6 models): Fortified base turrets, orbital defense railcannons, core guardians, siege juggernauts, and flak sentries.
- **Environment Props & Interactive Structures** (5 models): Power conduit relays, airlock blast gates, mineral refining drills, monolith gateways, and supply crates.

---

## 5. Querying & Updating Tasks via CLI & Python `csv`

Subagents and automated scripts query [`tasks/models_3D.csv`](../tasks/models_3D.csv) using the headless `tasks.py` CLI (<50ms, zero Raylib GUI window) or Python's standard library `csv` module (<50 tokens per query).

### 5.1 Find Pending 3D Models in a Category (Fast CLI)
```bash
python -B tasks.py --list models_3D --category humanoid --status pending --limit 3
```

### 5.2 Fetch Full 3D Model Specifications by ID (Fast CLI)
```bash
python -B tasks.py --get models_3D m3d_char_exo_knight
```

### 5.3 Check if Concept Name Already Exists (Prevent Collisions)
```bash
python -B tasks.py --check models_3D "Exo Knight"
```

### 5.4 Mark a 3D Model as Built (Fast CLI)
```bash
python -B tasks.py --set-status models_3D m3d_char_exo_knight built
```

### 5.5 Fallback: Python Standard Library `csv` One-Liners
```bash
# Query pending in humanoid category
python -B -c "import csv; f=open('tasks/models_3D.csv', encoding='utf-8-sig'); r=csv.DictReader(f); print(next(dict(id=x['id'], func=x['function_name'], file=x['target_file']) for x in r if x['category']=='humanoid' and x['status']=='pending'))"

# Count pending vs built 3D models
python -B -c "import csv; from collections import Counter; f=open('tasks/models_3D.csv', encoding='utf-8-sig'); c=Counter((x['category'], x['status']) for x in csv.DictReader(f)); [print(f'{k[0]} [{k[1]}]: {v}') for k, v in sorted(c.items())]"
```

---

## 6. Human Spreadsheet Editing & Tasks Editor (`tasks.py`)

To inspect, sort, and edit [`tasks/models_3D.csv`](../tasks/models_3D.csv) without risking CSV delimiter or encoding corruption:
1. **Interactive Tasks Editor (`tasks.py`)**: Run `python -B tasks.py` to open the graphical Raylib task manager with hot-switching, sorting, cell editing, horizontal scrolling, and "Adjusted Text" (Wrap Text).
2. **Never alter column header names**: The first row must keep `id,category,concept_name,function_name,target_file,primitives_used,animation_features,palette_keys,status,description`.
3. **Allowed status values**: `pending`, `in_progress`, `built`.
