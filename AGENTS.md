# Agent Operating Instructions & Repository Context Hub (AGENTS.md)

Welcome, Agent. This repository is an **interactive encyclopedia of video game design patterns** built with **Raylib in Python (`pyray`)**.

The graphics and audio are intentionally built using **procedural primitives** (2D and 3D geometric shapes like spheres, cubes, cylinders, and rectangular prisms) and **in-memory audio synthesis** to emphasize architectural clarity, mathematical elegance, and hands-on pattern learning over external art assets.

---

## 1. Mandatory Step 0: Pre-Flight Check & Scope Control

**CRITICAL RULE**: Before generating code or planning a new minigame/feature, you **MUST** review the existing components in the workspace:

1. **Check Existing Minigames & Catalog Taxonomy**: Review [`minigames.md`](minigames.md) to locate the exact 3.x catalog section for the requested minigame:
   - **Section 3.0: Core Multi-Pattern Prototypes** (large 600–900 lines, combining 4+ patterns: Space Swarm, Mecha Colosseum 3D, Drone Defense 3D). Max 1 per prompt.
   - **Sections 3.1–3.7: Extended Single-Pattern Labs** (focused 250–500 lines, 1 to 2 per prompt):
     - `3.1 Menus & UI`
     - `3.2 Combat & Weapons`
     - `3.3 Enemies & AI`
     - `3.4 Progression & Economy`
     - `3.5 World & Exploration`
     - `3.6 Movement & Camera`
     - `3.7 Puzzle, Stealth & Other`
2. **Check Existing Visual & Audio Assets**: Review [`assets.md`](assets.md) to reuse existing 3D models (`assets/models_3d/`), 2D primitive renderers (`assets/sprites_2d/`), and procedural audio synthesizers (`assets/audio/`). **NEVER rewrite or duplicate these assets.**
3. **Check Existing Utilities & Math**: Review [`utils.md`](utils.md) to reuse non-native collision routines (rotated 3D/2D capsules, SAT OBB), spatial hash grids (`SpatialGrid2D`/`3D`), AI pursuit/pathfinding algorithms (A*, BFS, seek, lead intercept), math dampening/shake tools, and the global UI/Font/Window manager (`utils/ui_settings.py`). **NEVER rewrite these utilities** (unless a single-pattern lab is specifically teaching that algorithm, in which case expose its step-by-step state visually).
4. **Reference Game Design Patterns**: Consult [`patterns.md`](patterns.md) to document and explain the design patterns demonstrated.

### Batch Size & Scope Limits (Quality Guardrail)
To prevent output truncation, skipped comments, or degraded code quality:
- **Full Multi-Pattern Minigames** (600–900 lines, combining 4+ patterns like `minigames/space_swarm.py`): Build **at most 1 prototype per prompt**.
- **Focused Single-Pattern Labs** (250–450 lines, from Extended Catalog sections 3.1–3.7 in `minigames.md`): Build **1 to 2 prototypes per prompt** (maximum 3 only if explicitly requested by the user and within the same 2D category).
- **Focused Lab Scope**: Single-pattern labs must start **immediately in the interactive gameplay/sandbox state** (skip title screens unless the pattern itself is a menu/scene-stack pattern) so 100% of the code focuses on experiencing and inspecting the target pattern.

---

## 2. Core Repository Rules

### Rule 1: No Bytecode / Zero `__pycache__` Generation
- **NEVER** generate `__pycache__` directories in the repository during tests, scripts, or execution.
- When running terminal commands or tests, always use `python -B` or pass `$env:PYTHONDONTWRITEBYTECODE="1"`.
- Every script and package **MUST** enforce `sys.dont_write_bytecode = True` at the very top before any imports:
  ```python
  import sys
  sys.dont_write_bytecode = True
  ```

### Rule 2: Mandatory `from pyray import *` followed by `from utils import *`
- Every minigame inside `minigames/` must be a **single, self-contained Python script** (e.g., `minigames/space_swarm.py`).
- In **EVERY** script, you **MUST** import in this exact order:
  ```python
  from pyray import *
  from assets import *
  from utils import *
  ```
- Importing `from utils import *` after `from pyray import *` automatically enables the repository's **Global Top-Bar Settings Dropdowns** (`Font`, `Font Size [Ctrl +/-]`, and `Window Size / Fullscreen [F11]`) backed by `config.json`. Keep the top-bar region `x = 450..980, y = 14..48` free of HUD text so the dropdown bar (`draw_ui_settings_bar(450, 16)`) never overlaps your HUD.
- Every minigame must be directly executable from the terminal (`python -B minigames/<script_name>.py`) and discoverable via the root [`launcher.py`](launcher.py).

### Rule 3: Mandatory 5-Block Pedagogical Anatomy & Template
Every minigame script must follow a strict 5-block anatomy so learners can locate the pattern implementation immediately and automated tests can verify it without hanging:

```python
# -*- coding: utf-8 -*-
"""
<Prototype Title> - <Target Design Pattern(s)>
==============================================
Section          : <3.0, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, or 3.7>
Pattern Category : <Category from patterns.md>
Dimension        : <2D or 3D>

Problem Solved:
  <1-2 sentences explaining what goes wrong in games without this pattern>

How the Pattern Works:
  <Clear mathematical and architectural explanation of the pattern>

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - <Movement / Action keys + Gamepad Left/Right Stick, D-Pad & Face/Trigger buttons>
  - [Tab] / Gamepad View (Select) : Toggle X-Ray Pattern Telemetry & Debug Overlay
  - [F1]  / Gamepad R3            : Toggle Pattern ON/OFF (compare behavior with vs. without the pattern)
  - [Ctrl +/-]                    : Increase / Decrease UI Font Size
  - [F11]                         : Toggle Fullscreen
  - [R]   / Gamepad Start         : Reset simulation
"""

import sys
import os
import math
import random

# 1. Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# 2. Add repository root to search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 3. Mandatory Raylib & modular imports
from pyray import *
from assets import *
from utils import *

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WINDOW_TITLE = "<Prototype Title> - <Pattern Name> (Raylib Pattern Lab)"

# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATION (<PATTERN NAME>)
# ==============================================================================
# Isolate the pure pattern classes/functions here with thorough novice-friendly
# comments explaining WHY the math/architecture works and how it maps to C++
# (e.g., struct fields, fixed-size arrays, explicit indices).


# ==============================================================================
# BLOCK 2: WORLD SIMULATION & ENTITIES
# ==============================================================================
# Entities, environment setup, and integration with assets/ and utils/.


# ==============================================================================
# BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY ([Tab] & [F1])
# ==============================================================================
# Visualizes internal pattern metrics (counters, state graphs, vectors, pools).


# ==============================================================================
# BLOCK 4: MAIN GAME LOOP & AUTOMATED SMOKE TEST
# ==============================================================================
class PatternLabGame:
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()
        self.sfx = SoundLibrary()
        self.sfx.init_defaults()
        self.show_xray = True
        self.pattern_enabled = True

    def update(self):
        dt = min(get_frame_time(), 0.05)
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
        if is_dual_pattern_toggle_pressed():
            self.pattern_enabled = not self.pattern_enabled
            self.sfx.play("click", 0.6)
        # Update simulation (use get_dual_move_2d() / get_dual_look_2d() for simultaneous KB/M + Gamepad)...

    def draw(self):
        begin_drawing()
        clear_background(Color(12, 14, 22, 255))
        # Draw world & HUD...
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)  # Top-bar Font, Size (Ctrl+/-), and Window (F11) dropdowns
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
    PatternLabGame().run(smoke_test=is_smoke)
```

### Rule 4: Language-Agnostic & C++-Transferable Code (Zero "Pythonic Magic")
Python is used in this repository strictly as **readable, executable pseudocode**. Learners study this code to understand data structures and algorithms and port them to **C++, C, C#, Rust, or Zig**. You **MUST** write code that translates 1-to-1 to C++:
1. **NO Decorators (`@dataclass`, `@property`, `@staticmethod`, `@classmethod`, `@lru_cache`, custom `@decorator`)**:
   - Declare plain classes with an explicit `__init__(self)` constructor initializing every member variable line-by-line with concrete default values (equivalent to a C++ `struct` or `class`).
2. **NO Generators (`yield`), Coroutines (`async`/`await`), or `with` Context Managers for Game Logic**:
   - Game loops and state machines advance frame-by-frame via `update(dt)`. Represent multi-step sequences with explicit state variables (`self.state`, `self.timer`, `self.step_index`), never `yield`.
3. **NO Dunder / Magic Methods (except `__init__`) or Dynamic Metaprogramming**:
   - Never implement `__call__`, `__getitem__`, `__getattr__`, `__add__`, `__mul__`, or use `getattr()`, `setattr()`, `eval()`, `*args`, or `**kwargs` in game/pattern logic. Use explicit method names (`pool.get_slot(i)`, `add_vectors(a, b)`).
4. **NO Complex List/Dict Comprehensions, Walrus Operators (`:=`), or `lambda`/`map`/`filter` Chains**:
   - Write explicit `for` loops and `if/else` blocks so the exact $O(N)$ control flow and branching are visible to someone translating the loop to C++.
   - Never reallocate lists every frame with filter comprehensions (e.g., avoid `enemies = [e for e in enemies if e.active]`); instead use pre-allocated pools with `active = False` flags or in-place index loops.
5. **Prefer Explicit Arrays, Indices, and Integer Constants / String States**:
   - Use simple fixed-capacity lists (`self.slots = []` populated in a `for` loop at startup), integer counters (`self.active_count`), and explicit struct-like objects so the memory layout mirrors `std::array<T, N>` or `std::vector<T>` in C++.

### Rule 5: Mandatory X-Ray Overlay (`[Tab]`) & Pattern Comparison (`[F1]`)
Because this repository exists to **teach** game design patterns:
1. **`[Tab]` X-Ray Inspector Overlay (Default ON in Single-Pattern Labs)**: Every minigame must render a clean telemetry panel or world-space debug visualization showing the pattern's inner workings in real time (e.g., active vs. free slots in an Object Pool, active node in a Behavior Tree/FSM, spatial grid cell outlines and query counts, trajectory/raycast vectors, or timing window bars).
2. **`[F1]` Live Pattern Toggle / Parameter Tuning**: Whenever a pattern improves performance, feel, or architecture (e.g., Coyote Time, Object Pool, Spatial Grid, Hit-Stop, Auto-Aim, Camera Damping, Recoil), allow pressing `[F1]` (or `1`/`2`/`3`) to toggle the pattern `ON/OFF` or adjust its parameters live so the learner can immediately feel the difference.

### Rule 6: Mandatory Non-Blocking Verification (`--smoke-test`)
- **NEVER** execute `python -B minigames/<script>.py` without `--smoke-test` from an agent tool call, because the Raylib window will stay open indefinitely and hang the terminal.
- After creating or editing any minigame, you **MUST** verify it by running:
  ```bash
  python -B minigames/<script_name>.py --smoke-test
  ```
- This executes 3 full `update()` and `draw()` frames and closes cleanly, catching 100% of syntax errors, missing imports, and `pyray` CFFI type mismatches.

### Rule 7: Immediate Documentation Updates & Novice-Friendly English
- All code, comments, and markdown documents must be written in **clear, readable English**.
- Include thorough comments explaining *why* equations work (e.g., shortest segment distance, Reynolds steering, DDA raycast, spring damping) and brief notes on how the data structures map to C++.
- Whenever you create or modify:
  - A minigame $\rightarrow$ Update [`minigames.md`](minigames.md) (and [`patterns.md`](patterns.md) if adding a new pattern).
  - An asset $\rightarrow$ Update [`assets.md`](assets.md).
  - A utility $\rightarrow$ Update [`utils.md`](utils.md).

### Rule 8: Simultaneous Keyboard/Mouse & Gamepad Controls (Dual Input)
- Every minigame and the launcher **MUST** support **Gamepad (Controller) input** that activates automatically whenever a connected controller is detected (`is_gamepad_available`) and works **simultaneously** alongside **Keyboard & Mouse** (either one, the other, or both at the same time — never locking out Keyboard/Mouse when a controller is plugged in).
- Always reuse the helpers in [`utils/gamepad_input.py`](utils/gamepad_input.py) (exported via `from utils import *`):
  - **2D / 3D Movement**: `get_dual_move_2d()` (combines `WASD` / `Arrow Keys` + `Gamepad Left Stick` with radial deadzone + `D-Pad`, clamping combined magnitude to `<= 1.0` so using both devices never doubles player speed).
  - **Aiming / Camera Look**: `get_dual_look_2d()` (combines `Q`/`E` or `Left`/`Right` keys + `Gamepad Right Stick` with radial deadzone). For cursor/reticle aiming in 2D, allow the Mouse cursor when moved and smoothly steer with the Gamepad Right Stick when deflected.
  - **Actions & Lab Toggles**: `is_dual_primary_fire_down()`, `is_dual_primary_fire_pressed()`, `is_dual_secondary_fire_pressed()`, `is_dual_jump_down()`, `is_dual_jump_pressed()`, `is_dual_dash_down()`, `is_dual_dash_pressed()`, `is_dual_xray_toggle_pressed()` (`[Tab]` / `Gamepad Y`), `is_dual_pattern_toggle_pressed()` (`[F1]` / `GamepadLB`), `is_dual_secondary_toggle_pressed()` (`[F2]` / `GamepadRB`), and `is_dual_reset_pressed()` (`[R]` / `Gamepad Select` or `Start`).
  - **HUD Status Badge**: Call `draw_gamepad_status_badge(985, 22, 11)` on the top HUD bar so the learner can see live controller detection (`PAD: ON [KB/M + Pad]` vs. `PAD: OFF [KB/M Only]`).

### Rule 9: Catalog Classification & Launcher Dropdown Synchronization
Every minigame script MUST be classified under its designated section from `minigames.md` (`3.0` or `3.1` through `3.7`):
1. **Docstring Section Tag**: Declare `Section          : <3.x Category>` in the script header docstring so `launcher.py`'s AST parser assigns it to the corresponding 3.x dropdown menu filter automatically.
2. **Sync `minigames.md`**:
   - Mark the item in its planned 3.x section with a `(built)` suffix.
   - Add an entry in Section 2 (Active Minigames Registry) specifying its Section designation (e.g., `Section 3.1: Menus & UI`).
3. **Sync `patterns.md`**: Ensure the demonstrated pattern is documented under its category and registered in the Summary Matrix.
4. **Dual Smoke Test**: Run both `python -B minigames/<script_name>.py --smoke-test` AND `python -B launcher.py --smoke-test` to verify zero regressions in the prototype and the launcher dropdown system.

---

## 3. `pyray` (CFFI) Gotchas Cheat Sheet (Read to Avoid Runtime Errors)

`pyray` uses CFFI bindings over C structs. Keep these 4 rules in mind on every line of rendering and math code:

1. **Cast 2D Coordinates to `int` for Non-Vector Draw Calls**:
   Functions like `draw_text(text, x, y, size, color)`, `draw_rectangle(x, y, w, h, color)`, `draw_rectangle_lines(x, y, w, h, color)`, `draw_circle(x, y, radius, color)`, and `draw_line(x1, y1, x2, y2, color)` expect **C integers** for coordinates and dimensions. Passing a Python `float` raises `TypeError: incompatible types`.
   - *Fix*: Wrap coordinates with `int(x)` or use vector equivalents (`draw_circle_v(pos, r, col)`, `draw_line_ex(p1, p2, thick, col)`).
2. **Clamp & Cast `Color(r, g, b, a)` Channels to `int` in `0..255`**:
   Computing dynamic alpha or color flashes (e.g., `255 * timer`) produces floats or values outside `0..255`, which crashes CFFI.
   - *Fix*: Always use `Color(r, g, b, max(0, min(255, int(alpha))))`.
3. **Do Not Use `+`, `-`, or `*` Operators Directly on `Vector2` / `Vector3`**:
   `pyray` CFFI structs (`Vector2`, `Vector3`) do not reliably support Python arithmetic operators across all versions.
   - *Fix*: Access `.x`, `.y`, `.z` directly (`pos.x += vel.x * dt`) or use the helper functions in `utils/math_helpers.py` (`lerp_v2`, `damp_v2`, `distance_2d`, `normalize_2d`).
4. **3D Mode vs. 2D Overlay Separation**:
   In 3D minigames, all `draw_cube`, `draw_sphere`, `draw_cylinder_ex`, and `draw_grid` calls must be inside `begin_mode_3d(camera)` ... `end_mode_3d()`. All `draw_text` and 2D HUD calls must be placed **after** `end_mode_3d()` (using `get_world_to_screen(pos, camera)` if projecting 3D labels to 2D).

---

## 4. Directory Map & Component Index

```
./
├── AGENTS.md                  <-- You are here (Agent rules, template & pyray gotchas)
├── README.md                  <-- Beginner onboarding & usage instructions
├── config.json                <-- Persisted UI preferences (font, font size, window size)
├── launcher.py                <-- Interactive Pattern Encyclopedia & Minigame Hub
├── patterns.md                <-- Exhaustive catalog of 2D & 3D game design patterns
├── assets.md                  <-- Registry of all 3D models, 2D sprites, and synth audio
├── utils.md                   <-- Registry of collisions, spatial grids, AI, math & UI
├── minigames.md               <-- Registry and status of all standalone minigames
│
├── assets/                    <-- Reusable procedural visual and audio assets
│   ├── models_3d/             <-- 3D procedural primitive models (Humanoid, Beast, Drone, Turret)
│   ├── sprites_2d/            <-- 2D procedural primitive sprites (Humanoid, Slime, Flying, Crawler)
│   └── audio/                 <-- Procedural in-memory SFX and BGM synthesizers
│
├── utils/                     <-- Reusable non-native utilities
│   ├── collisions.py          <-- Rotated capsule 3D/2D, SAT OBB, segment projections
│   ├── spatial_grid.py        <-- 2D & 3D spatial hash grids, 2D tile navigation grid
│   ├── ai_pursuit.py          <-- Steering (Seek, Lead Intercept, Wander), A* & BFS pathfinding, LOS
│   ├── math_helpers.py        <-- Lerp, damp, approach, easing curves, Trauma screen shake
│   ├── ui_settings.py         <-- Global Font, Font Size (Ctrl+/-), Window (F11) & config.json manager
│   └── gamepad_input.py       <-- Simultaneous Keyboard/Mouse + Gamepad hot-plug & radial deadzone
│
└── minigames/                 <-- Standalone single-file minigames & pattern labs
    ├── space_swarm.py         <-- 2D Bullet Hell & Swarm Survival (Object Pool, Spatial Grid, Trauma Shake)
    └── mecha_colosseum.py     <-- 3D Boss Arena (Behavior Trees, Kinematic Slide Controller, Audio Synth)
```
