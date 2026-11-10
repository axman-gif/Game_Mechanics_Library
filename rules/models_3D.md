# 3D Procedural Models Architectural Guidelines & Registry (`assets/models_3D/`)
=============================================================================

This document defines the architectural standards, procedural primitive construction rules, animation interfaces, and a copy-pasteable **code template** for all 3D procedural models.
All 3D models are organized into dedicated category subfolders within `assets/models_3D/<category>/` (`beast/`, `drone/`, `environment_prop/`, `humanoid/`, and `turret_boss/`).

All 3D model task tracking, primitive specifications, and progress statuses are maintained in the companion spreadsheet:
👉 [**`tasks/models_3D.csv`**](../tasks/models_3D.csv)

Related documentation guides:
- Top-Level Asset Catalog: [`rules/assets.md`](assets.md)
- 2D Procedural Sprites: [`rules/sprites_2D.md`](sprites_2D.md)
- Procedural Audio & Synthesis: [`rules/audio.md`](audio.md)
- Minigame Design & Architecture: [`rules/minigames.md`](minigames.md)
- Reusable Math & Physics Utilities: [`rules/utils.md`](utils.md)

---

## 1. Golden Architecture Rules for 3D Procedural Models

1. **Pure Geometric Primitives**: All 3D models are constructed purely from mathematical 3D primitives (`draw_sphere`, `draw_cube`, `draw_cube_wires`, `draw_cylinder_ex`). External 3D mesh files (`.obj`, `.gltf`, `.fbx`, `.blend`) and textured bitmap materials are strictly forbidden.

2. **Global Repository Philosophy & Language-Agnostic C++ Transferability**:
   In alignment with [`README.md`](../README.md) and [`AGENTS.md`](../AGENTS.md), this repository is built for learning and inspiration: **simple beats clever**. Python serves as readable, executable pseudocode that ports 1-to-1 to C++, C, C#, Rust, or Zig:
   - **Zero Dynamic "Pythonic Magic"**: Plain classes with explicit `__init__(self)` constructors initializing every member variable line-by-line; zero decorators (`@dataclass`, `@property`, `@staticmethod`, `@classmethod`), zero generators (`yield`), zero coroutines (`async`/`await`), zero lambdas or functional chains (`map`/`filter`), and zero magic dunder overrides (`__getattr__`, `__getitem__`).
   - **Explicit Math & Control Flow**: Straightforward trigonometry (`math.sin`, `math.cos`), scalar coordinates, and explicit `for` / `if/else` control flow.
   - **Educational Comments**: Comments explain **WHY** equations work and why geometric structures are placed where they are, using simple, clear words without academic jargon.

3. **Unified Asset Contract A (Canonical 3D Drawing Interface)**:
   Every 3D model drawing function must adhere strictly to the standardized signature:
   ```python
   def draw_<name>_3d(
       position: Vector3,
       rotation_y: float = 0.0,
       anim_timer: float = 0.0,
       scale: float = 1.0,
       palette: dict = None
   ) -> None:
       pass
   ```
   - `position`: `Vector3` base location in 3D world space.
   - `rotation_y`: Yaw rotation around the vertical Y-axis **in DEGREES** (converted internally to radians via `rotation_y * (math.pi / 180.0)` for trigonometric offsets or passed directly to matrix transforms).
   - `anim_timer`: Continuous elapsed time in seconds driving sinusoidal locomotion, breathing, and secondary articulated motions.
   - `scale`: Uniform scalar multiplier scaling all primitive radii, heights, lengths, and spatial offsets.
   - `palette`: Optional semantic color dictionary mapping body part keys (`armor`, `joints`, `visor`, `core`, etc.) to Raylib `Color` instances. When `palette=None` is passed, the function falls back to its documented `DEFAULT_<NAME>_PALETTE`.

4. **Semantic Color Palettes & Named Geometric Constants**:
   - Every model file must define an explicit dictionary constant named `DEFAULT_<NAME>_PALETTE` mapping semantic parts to Raylib `Color` structs. Secondary theme palettes (e.g. `DESERT_<NAME>_PALETTE`, `STEALTH_<NAME>_PALETTE`) can also be provided.
   - **Replace Magic Numbers with Named Constants**: All dimensional proportions (e.g. `LEG_LENGTH`, `ARM_LENGTH`, `TORSO_HEIGHT`, `HEAD_RADIUS`, `BODY_RADIUS`) must be defined as named module-level constants rather than hardcoded magic literals. This makes the geometric anatomy immediately obvious and translates 1-to-1 to C++ `static const float` parameters.

5. **Default Destination Directory**: All 3D procedural models are strictly located in their designated category subfolder within `assets/models_3D/<category>/` (`assets/models_3D/beast/`, `assets/models_3D/drone/`, `assets/models_3D/environment_prop/`, `assets/models_3D/humanoid/`, `assets/models_3D/turret_boss/`).

6. **3D Camera Context**: All 3D model drawing routines must execute inside `begin_mode_3d(camera)` ... `end_mode_3d()`. HUD and screen-space text projections must occur outside 3D mode.

7. **Line Limits & Sizing Bounds**:
   - **Procedural Assets (SFX, BGM, 3D models, 2D sprites)**: Floor **200 lines**, target range **200 to 800 lines**, hard ceiling **1,000 lines**.
   - **Minigames (Sections 3.0 to 3.7)**: Floor **300 lines**, target range **300 to 1,500 lines**, hard ceiling **1,800 lines**.
   - **Token Control Guidance**: Line limits exist strictly as operational bounds for token budget management and context preservation. **Never pad a file with artificial filler or boilerplate to reach the floor.** **Never compress code, combine lines, truncate functions, or drop comments to fit under the ceiling.**
   - **Readability Criterion**: Every file must be understandable by reading it top to bottom, without having to jump to other files; clarity and pedagogical completeness always win over line count.

8. **Standalone Previewer & Automated `--smoke-test`**:
   Every 3D model module must be standalone executable (`if __name__ == "__main__":`). Running `python -B assets/models_3D/<category>/<model_file>.py` opens an interactive 3D Orbit Viewer (`ModelViewerApp`) with mouse drag orbit, zoom, play/pause, and palette swapping. When invoked with `--smoke-test`, it renders 3 frames headlessly and exits cleanly with code `0`.

9. **Assets-Only Minigames Rule & Orchestrator Prerequisite Gate**:
   Minigames must use only assets that ALREADY exist inside the `assets/` package.
   - **Lead Orchestrator Prerequisite Check**: Before spawning a 3D minigame craftsman, the Orchestrator runs a Python script reading strictly `id`, `status`, and `description` from `tasks/models_3D.csv`.
   - **Quality Preservation Gate**: If any required 3D model is missing or pending, craftsman invocation for that minigame is halted immediately. The Orchestrator explains to the user which model is missing and how withholding the craftsman preserves visual quality (preventing crude, monolithic inlined shapes that break modularity).
   - **Specification Injection**: Once verified (`status == done`), the exact drawing function `draw_<name>_3d(position, rotation_y, anim_timer, scale, palette)` and default palette `DEFAULT_<NAME>_PALETTE` are injected into the minigame craftsman prompt.

---

## 2. Standard 3D Model Code Template

Every craftsman subagent creating a 3D model must follow this exact 6-part anatomy. Copy and adapt this template for your target asset:

```python
# -*- coding: utf-8 -*-
"""
Exo-Knight Heavy Armored Unit - 3D Procedural Primitive Model
============================================================
Category         : humanoid
Target File      : assets/models_3D/humanoid/exo_knight.py
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
  struct ExoKnightPalette { Color armor; Color armor_dark; Color joints; Color visor; Color core; Color blade; Color accent; };
  void DrawExoKnight3D(Vector3 position, float rotation_y, float anim_timer, float scale, const ExoKnightPalette* palette);
  Mapped directly to DrawCube, DrawSphere, and DrawCylinderEx from raylib.h.
"""

# ==============================================================================
# PART 2: ZERO BYTECODE, SYS.PATH & MANDATORY RAYLIB IMPORTS
# ==============================================================================
import sys
import os
import math

# Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# Add repository root to search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

# Mandatory Raylib and utility imports
from pyray import *
from utils import *

# ==============================================================================
# PART 3: PALETTES & NAMED GEOMETRIC CONSTANTS (Zero Magic Numbers)
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

# Named geometric proportions (replaces magic numbers)
TORSO_WIDTH = 0.70
TORSO_HEIGHT = 0.85
TORSO_LENGTH = 0.45
TORSO_ELEVATION = 1.35

CORE_RADIUS = 0.14
CORE_OFFSET_Z = 0.24

HEAD_RADIUS = 0.28
HEAD_ELEVATION = 0.65
CREST_HEIGHT = 0.12
CREST_LENGTH = 0.38
VISOR_OFFSET_Z = 0.22

SHOULDER_SPREAD = 0.52
SHOULDER_ELEVATION = 0.32
SHOULDER_RADIUS = 0.22

ARM_LENGTH = 0.60
ARM_RADIUS_TOP = 0.09
ARM_RADIUS_BOTTOM = 0.07
HAND_RADIUS = 0.11

SWORD_BLADE_LENGTH = 1.20
SWORD_BLADE_RADIUS = 0.04

PELVIS_ELEVATION = 0.85
LEG_SPREAD = 0.24
LEG_LENGTH = 0.85
LEG_RADIUS_TOP = 0.11
LEG_RADIUS_BOTTOM = 0.08
BOOT_WIDTH = 0.22
BOOT_HEIGHT = 0.20
BOOT_LENGTH = 0.35

WALK_SPEED = 4.0


# ==============================================================================
# PART 4: CANONICAL 3D PROCEDURAL DRAWING FUNCTION
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

    Parameters:
      position   : World-space base root location (feet center).
      rotation_y : Heading angle in DEGREES around Y axis (0 deg = facing +Z).
      anim_timer : Elapsed seconds driving stride, counter-swing, and breath cycles.
      scale      : Geometric scaling factor (1.0 = standard human height ~1.85m).
      palette    : Optional dictionary overriding DEFAULT_EXO_KNIGHT_PALETTE colors.
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
    walk_stride = math.sin(anim_timer * WALK_SPEED)
    walk_bob = abs(math.cos(anim_timer * WALK_SPEED)) * 0.12 * scale
    breath = math.sin(anim_timer * 1.5) * 0.03 * scale

    # Base root position with vertical walking bounce
    bx = position.x
    by = position.y + walk_bob
    bz = position.z

    # Trigonometric forward/right vectors based on rotation_y (in DEGREES converted to radians)
    rad_y = rotation_y * (math.pi / 180.0)
    cos_r = math.cos(rad_y)
    sin_r = math.sin(rad_y)

    # 3. Torso & Power Core (Central Mass)
    torso_y = by + (TORSO_ELEVATION * scale) + breath
    torso_w = TORSO_WIDTH * scale
    torso_h = TORSO_HEIGHT * scale
    torso_l = TORSO_LENGTH * scale
    draw_cube(Vector3(bx, torso_y, bz), torso_w, torso_h, torso_l, c_armor)
    draw_cube_wires(Vector3(bx, torso_y, bz), torso_w, torso_h, torso_l, c_armor_dark)

    # Fusion Reactor Core (Front-facing glowing sphere)
    core_offset_z = CORE_OFFSET_Z * scale
    core_x = bx + (sin_r * core_offset_z)
    core_z = bz + (cos_r * core_offset_z)
    draw_sphere(Vector3(core_x, torso_y + (0.10 * scale), core_z), CORE_RADIUS * scale, c_core)

    # 4. Articulated Head & Tactical Visor
    head_y = torso_y + (HEAD_ELEVATION * scale)
    draw_sphere(Vector3(bx, head_y, bz), HEAD_RADIUS * scale, c_armor_dark)

    # Armored Crest (Helmet Ridge)
    draw_cube(Vector3(bx, head_y + (0.22 * scale), bz), 0.12 * scale, CREST_HEIGHT * scale, CREST_LENGTH * scale, c_accent)

    # Glowing Visor Slit
    visor_offset_z = VISOR_OFFSET_Z * scale
    vx = bx + (sin_r * visor_offset_z)
    vz = bz + (cos_r * visor_offset_z)
    draw_cube(Vector3(vx, head_y, vz), 0.32 * scale, 0.08 * scale, 0.10 * scale, c_visor)

    # 5. Articulated Pauldrons & Shoulder Joints
    shoulder_spread = SHOULDER_SPREAD * scale
    shoulder_y = torso_y + (SHOULDER_ELEVATION * scale)

    # Left & Right Shoulder Spans
    ls_x = bx - (cos_r * shoulder_spread)
    ls_z = bz + (sin_r * shoulder_spread)
    rs_x = bx + (cos_r * shoulder_spread)
    rs_z = bz - (sin_r * shoulder_spread)

    draw_sphere(Vector3(ls_x, shoulder_y, ls_z), SHOULDER_RADIUS * scale, c_armor)
    draw_sphere(Vector3(rs_x, shoulder_y, rs_z), SHOULDER_RADIUS * scale, c_armor)

    # 6. Articulated Arms (Counter-swinging gait)
    arm_swing_angle = walk_stride * 0.45  # Radians
    arm_len = ARM_LENGTH * scale

    # Left Hand / Arm
    l_hand_y = shoulder_y - arm_len + (math.sin(arm_swing_angle) * 0.15 * scale)
    draw_cylinder_ex(
        Vector3(ls_x, shoulder_y, ls_z),
        Vector3(ls_x, l_hand_y, ls_z),
        ARM_RADIUS_TOP * scale, ARM_RADIUS_BOTTOM * scale, 6, c_joints
    )
    draw_sphere(Vector3(ls_x, l_hand_y, ls_z), HAND_RADIUS * scale, c_armor_dark)

    # Right Hand / Weapon Arm (Holding Plasma Greatsword)
    r_hand_y = shoulder_y - arm_len - (math.sin(arm_swing_angle) * 0.15 * scale)
    draw_cylinder_ex(
        Vector3(rs_x, shoulder_y, rs_z),
        Vector3(rs_x, r_hand_y, rs_z),
        ARM_RADIUS_TOP * scale, ARM_RADIUS_BOTTOM * scale, 6, c_joints
    )
    draw_sphere(Vector3(rs_x, r_hand_y, rs_z), HAND_RADIUS * scale, c_armor_dark)

    # Plasma Greatsword (Attached to Right Hand)
    sword_hilt_y = r_hand_y
    sword_tip_y = sword_hilt_y + (SWORD_BLADE_LENGTH * scale)
    draw_cylinder_ex(
        Vector3(rs_x, sword_hilt_y, rs_z),
        Vector3(rs_x, sword_tip_y, rs_z),
        SWORD_BLADE_RADIUS * scale, (SWORD_BLADE_RADIUS * 0.5) * scale, 6, c_blade
    )
    draw_cube(Vector3(rs_x, sword_hilt_y + 0.10 * scale, rs_z), 0.25 * scale, 0.04 * scale, 0.06 * scale, c_accent)

    # 7. Articulated Legs (Pelvis, Thighs, Shins, Boots)
    pelvis_y = by + (PELVIS_ELEVATION * scale)
    leg_spread = LEG_SPREAD * scale
    leg_len = LEG_LENGTH * scale

    # Sinusoidal Stride Offsets
    l_stride = walk_stride * 0.35 * scale
    r_stride = -walk_stride * 0.35 * scale

    # Left Leg (Forward / Back)
    ll_x = bx - (cos_r * leg_spread) + (sin_r * l_stride)
    ll_z = bz + (sin_r * leg_spread) + (cos_r * l_stride)
    draw_cylinder_ex(
        Vector3(ll_x, pelvis_y, ll_z),
        Vector3(ll_x, by, ll_z),
        LEG_RADIUS_TOP * scale, LEG_RADIUS_BOTTOM * scale, 6, c_joints
    )
    # Left Armored Boot
    draw_cube(Vector3(ll_x, by + (0.10 * scale), ll_z), BOOT_WIDTH * scale, BOOT_HEIGHT * scale, BOOT_LENGTH * scale, c_armor)

    # Right Leg (Anti-phase)
    rl_x = bx + (cos_r * leg_spread) + (sin_r * r_stride)
    rl_z = bz - (sin_r * leg_spread) + (cos_r * r_stride)
    draw_cylinder_ex(
        Vector3(rl_x, pelvis_y, rl_z),
        Vector3(rl_x, by, rl_z),
        LEG_RADIUS_TOP * scale, LEG_RADIUS_BOTTOM * scale, 6, c_joints
    )
    # Right Armored Boot
    draw_cube(Vector3(rl_x, by + (0.10 * scale), rl_z), BOOT_WIDTH * scale, BOOT_HEIGHT * scale, BOOT_LENGTH * scale, c_armor)


# ==============================================================================
# PART 5: C++ MAPPING & MEMORY LAYOUT (Zero "Pythonic Magic")
# ==============================================================================
# In C++ (raylib.h), this procedural model requires zero dynamic memory allocation:
#
# struct ExoKnightPalette {
#     Color armor;
#     Color armor_dark;
#     Color joints;
#     Color visor;
#     Color core;
#     Color blade;
#     Color accent;
# };
#
# static const ExoKnightPalette DEFAULT_EXO_KNIGHT_PALETTE = {
#     (Color){45, 55, 72, 255},
#     (Color){28, 34, 46, 255},
#     (Color){100, 110, 125, 255},
#     (Color){0, 220, 255, 255},
#     (Color){255, 170, 0, 255},
#     (Color){220, 235, 255, 255},
#     (Color){200, 40, 40, 255}
# };
#
# void DrawExoKnight3D(Vector3 position, float rotation_y, float anim_timer, float scale, const ExoKnightPalette* palette);
#
# Memory Layout & Performance Notes:
# - Zero heap allocations: all coordinates and matrices exist on the CPU stack.
# - Immediate GPU buffers: primitives map directly to DrawCube, DrawSphere, and DrawCylinderEx.
# - C++ Transferability: Replace math.sin/cos with sinf/cosf from <math.h>. Replace Vector3 with raylib::Vector3.


# ==============================================================================
# PART 6: STANDALONE 3D ORBIT VIEWER (ModelViewerApp)
# ==============================================================================
class ModelViewerApp:
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
    ModelViewerApp().run(smoke_test=is_smoke)
```

---

## 3. Minigame Integration & Usage

### 3.1 Key-Based vs. Granular Import Patterns

Minigames can import 3D procedural models using either key-based loading via `models_3D` or granular imports:

**Key-Based Loader (Standard minigame pattern)**:
```python
from assets.asset_loader import models_3D, load_model_3d

# Load drawing function and default palette by key:
draw_exo_knight_3d, DEFAULT_EXO_KNIGHT_PALETTE = load_model_3d("exo_knight")

# Inside Minigame draw():
begin_mode_3d(self.camera)
draw_exo_knight_3d(
    position=self.player.position,
    rotation_y=self.player.yaw_degrees,
    anim_timer=self.player.walk_timer,
    scale=1.0
)
end_mode_3d()
```

**Granular Import (For isolated prototypes)**:
```python
from assets.models_3D.humanoid.exo_knight import draw_exo_knight_3d, DEFAULT_EXO_KNIGHT_PALETTE

# Inside Minigame draw():
begin_mode_3d(self.camera)
draw_exo_knight_3d(
    position=self.boss.position,
    rotation_y=self.boss.facing_angle_deg,
    anim_timer=self.boss.stride_timer,
    scale=1.5,
    palette=DEFAULT_EXO_KNIGHT_PALETTE
)
end_mode_3d()
```

### 3.2 Assets-Only Minigames Rule
**CRITICAL INVARIANT**: Minigames MUST use only models, sprites, and audio synthesizers that ALREADY exist inside the `assets/` package.
- If a minigame specification references a 3D model that does not yet exist in `assets/models_3D/<category>/`, **THE AGENT MUST STOP IMMEDIATELY WITHOUT TOUCHING OR CREATING ANY CODE**, and report the missing asset dependency to the orchestrator or user.
- Minigames may **NEVER** embed ad-hoc procedural mesh builders or inline 3D drawing routines inside `minigames/` files (unless the lab specifically teaches a mesh-generation design pattern like Marching Cubes or Procedural Terrain). All reusable entities belong in `assets/models_3D/<category>/`.

---

## 4. 3D Model Categorization Overview

All planned models in [`tasks/models_3D.csv`](../tasks/models_3D.csv) are categorized across 5 architectural classes, each stored in its dedicated subfolder under `assets/models_3D/`:

- **Characters & Humanoids** (`assets/models_3D/humanoid/`): Bipedal soldiers, exo-knights, cyber ninjas, industrial miners, psionic cultists, and riot vanguards.
- **Beasts & Quadruped Organisms** (`assets/models_3D/beast/`): Four-legged predators, armored pangolins, sabertooth prowlers, arachnid stalkers, sand wyrms, and spore bulls.
- **Drones & Airborne Constructs** (`assets/models_3D/drone/`): Hovering recon drones, tri-rotor hexacopters, stealth flying wings, kinetic dropships, and nanite carriers.
- **Turrets, Bosses & Heavy Armor** (`assets/models_3D/turret_boss/`): Fortified base turrets, orbital defense railcannons, core guardians, siege juggernauts, and flak sentries.
- **Environment Props & Interactive Structures** (`assets/models_3D/environment_prop/`): Power conduit relays, airlock blast gates, mineral refining drills, monolith gateways, and supply crates.

---

## 5. Task Lifecycle & Orchestrator CLI Workflow

Task tracking and lifecycle management for all 3D models are maintained exclusively in [`tasks/models_3D.csv`](../tasks/models_3D.csv).

### 5.1 Token-Saving Decoupled Architecture
- **Craftsman subagents NEVER read or parse CSV files into context.** Reading full tracking spreadsheets burns 4,000 to 8,000 tokens per turn. Instead, the Lead Orchestrator queries task specifications and injects the target row fields (`target_file`, `concept_name`, `primitives_used`, `animation_features`, `palette_keys`, `description`) directly into the subagent dispatch prompt.
- **Binary task status model**: Strictly binary `pending` (file absent from disk) and `done` (file present on disk). Statuses are automatically synchronized across catalogs via `python -B tasks.py --sync-statuses`.
- **Package Registration**: Upon building and verifying a 3D model, the file is automatically discovered dynamically by `assets/asset_loader.py` into the `models_3D` dictionary.

### 5.2 Orchestrator Headless CLI Queries (<50ms, <50 tokens)
The Orchestrator queries tasks using the headless `tasks.py` CLI:

```bash
# Query next pending 3D models in a category
python -B tasks.py --list models_3D --category humanoid --status pending --limit 3

# Fetch full specification of a target model by ID
python -B tasks.py --get models_3D m3d_char_exo_knight

# Check if a model concept name already exists (prevents duplicates)
python -B tasks.py --check models_3D "Exo Knight"

# Synchronize 3D model disk presence to task status automatically
python -B tasks.py --sync-statuses models_3D
```

---

## 6. Human Spreadsheet Editing & Tasks Editor (`tasks.py`)

To inspect, sort, and edit [`tasks/models_3D.csv`](../tasks/models_3D.csv) without risking CSV delimiter, newline, or UTF-8 BOM encoding corruption:
1. **Interactive Tasks Editor (`tasks.py`)**: Run `python -B tasks.py` to open the graphical Raylib task manager with hot-switching, sorting, cell editing, horizontal scrolling, and "Adjusted Text" (Wrap Text).
2. **Never alter column header names**: The first row must keep `id,category,concept_name,function_name,target_file,primitives_used,animation_features,palette_keys,status,description`.
3. **Allowed status values**: strictly binary `pending` (file absent from disk) and `done` (file present on disk). Statuses are automatically synchronized via `python -B tasks.py --sync-statuses`.
