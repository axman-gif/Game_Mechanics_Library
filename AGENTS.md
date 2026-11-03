# Agent Operating Instructions & Repository Context Hub (AGENTS.md)

Welcome, Agent. This repository is an **interactive encyclopedia of video game design patterns** built with **Raylib in Python (`pyray`)**.

The graphics and audio are intentionally built using **procedural primitives** (2D and 3D geometric shapes like spheres, cubes, cylinders, and rectangular prisms) and **in-memory audio synthesis** to emphasize architectural clarity, mathematical elegance, and hands-on pattern learning over external art assets.

---

## 1. Mandatory Step 0: Pre-Flight Check & Scope Control

**CRITICAL RULE**: Before generating code or planning a new minigame/feature, you **MUST** review the existing components in the workspace:

1. **Check Existing Minigames & Catalog Taxonomy**: Review [`minigames.md`](minigames.md) to locate the exact 3.x catalog section for the requested minigame:
   - **Section 3.0: Core Multi-Pattern Prototypes** (combining 4+ patterns: Orbital Siege 2D, Titan Strider 3D, Tactical Commander TBS, Frontline Outpost RTS).
   - **Sections 3.1–3.7: Extended Single-Pattern Labs** (focused on 1 pattern in isolation):
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

### 1.1 Ambiguity Gate & Mandatory Specification Check
Before writing or modifying any code, the agent **MUST** evaluate the clarity, target section, and scope of the prompt:
- **Standard Single-Turn Request (without `/teamwork`)**:
  - The user must explicitly request **strictly 1 prototype** by specifying either its exact prototype name or section from `minigames.md`.
  - **Multi-Minigame Halt**: If the user requests $\ge 2$ minigames in a single prompt without `/teamwork`, **THE AGENT MUST STOP IMMEDIATELY WITHOUT TOUCHING OR CREATING ANY CODE.** The agent must reply:
    > *"I detected a request for multiple minigames. To maintain pedagogical quality, prevent context dilution, and ensure role-specialized subagent execution, multi-script requests must use the `/teamwork` command (e.g. `/teamwork build 3 games from section 3.2 and 2 from section 3.3` or `/teamwork making 4 minigames from minigames.md using section 3.1`). For standard single-turn prompts, please request strictly 1 prototype."*
  - **Ambiguity Halt**: If the request is generic, open-ended (e.g., "make some minigames", "fix bugs in minigames", "advance on the list", "do something in section 3"):
    - **THE AGENT MUST STOP IMMEDIATELY WITHOUT TOUCHING OR CREATING ANY CODE.**
    - The agent must ask the user to clarify the exact prototype name and catalog section from `minigames.md`.
- **Autonomous Multi-Script Sessions (with `/teamwork`)**:
  - Multi-script batching is permitted for **up to 8 scripts per session**, provided the prompt is specific enough (e.g. *"build 3 games from section 3.1 and 3 from section 3.2"*, *"make 1 game from each of sections 3.1 through 3.7"*, or listing specific prototype names from `minigames.md`).
  - **Oversized Batch Halt**: If the user requests $> 8$ minigames in a single `/teamwork` session, **THE AGENT MUST STOP IMMEDIATELY WITHOUT TOUCHING OR CREATING ANY CODE**, and ask the user to break the request into batches of at most 8 prototypes.
  - **Sequential Isolated Subagent Invariant**: The Lead Coordinator MUST process scripts strictly **one at a time** using an isolated subagent per prototype (spawn subagent $N$ with clean context $\rightarrow$ write directly to disk $\rightarrow$ verify with `audit_minigame.py` $\rightarrow$ report 5-line summary $\rightarrow$ update documentation $\rightarrow$ advance to subagent $N+1$). It must NEVER attempt to generate or modify multiple scripts in a single tool call or message.

### 1.2 Script Sizing & Pedagogical Quality Invariants
To maximize token economy, eliminate bloat, maintain deep architectural pedagogy, and ensure zero runtime defects:
- **Strict Size Limits (Unified Across ALL Sections 3.0 to 3.7)**:
  - **Target Range**: **600 to 1,500 lines** per minigame script.
  - **Floor**: **600 lines minimum**. Scripts below 600 lines fail `audit_minigame.py` (prevents cutting corners on comments, 5-block anatomy, dual input, and X-Ray overlays).
  - **Hard Ceiling**: **1,800 lines maximum**. Under NO circumstances may any minigame script exceed 1,800 lines (prevents token bloat).
- **Pedagogical Quality Invariants (Non-Negotiable within Line Budget)**:
  - Even within the 600–1,500 line target, the agent must NEVER compress code, truncate functions, or omit comments to fit arbitrary limits.
  - Every script MUST provide:
    1. Novice-friendly comments explaining *why* equations work and their direct C++ equivalent (memory layout, explicit indices, struct fields).
    2. The full 5-block anatomy (Imports, Block 1 Core Pattern, Block 2 Entities/Simulation, Block 3 Telemetry X-Ray Overlay, Block 4 Dual Input Loop & Smoke Test).
    3. Complete simultaneous Keyboard/Mouse + Gamepad parity (no mouse-only or key-only actions).
    4. Safe HUD layout (keeping `x = 450..980, y = 14..48` clear for the global dropdown bar).
    5. Full state reset on `[R]` / Gamepad Start, zero CFFI type casting errors, and clamped Color channels (`0..255`).

### 1.3 Batch Size & Autonomous Teamwork Protocol (`/teamwork`)
To eliminate context dilution, prevent degradation in code depth, avoid attention drift across long multi-game sessions, and run seamlessly without requiring constant user intervention, the repository adopts **Option A: The Sequential Isolated Craftsman Guild**:
- **Standard Single-Turn Request**: Build strictly **1 prototype per prompt/cycle** (target 600–1,500 lines, maximum 1,800 lines). Complete the file, run verification via `audit_minigame.py`, update documentation, and halt.
- **Autonomous Multi-Script Sessions (`/teamwork`, Up to 8 Scripts)**:
  When invoked via `/teamwork` for up to 8 prototypes (e.g., `/teamwork making X amount of minigames from minigames.md using section(s) 3.x...`), the Lead Coordinator and subagents follow the **Autonomous Teamwork Protocol**:
  1. **Lead Coordinator Queue & Pre-Flight**:
     - The Coordinator validates that all requested prototypes exist in `minigames.md` and total $\le 8$ files.
     - Sequences the batch queue strictly one prototype at a time.
  2. **Dedicated Craftsman Subagent per Minigame (Fresh 0-Token Context)**:
     - For each prototype $k \in \{1 \dots N\}$, the Coordinator invokes an isolated subagent via `invoke_subagent`:
       ```python
       invoke_subagent(
           Role="Minigame Craftsman",
           TypeName="self",
           Workspace="inherit",
           Prompt="Build <Prototype Name> in minigames/<subfolder>/<script_name>.py following AGENTS.md rules..."
       )
       ```
     - **Clean Context Isolation**: The subagent receives ONLY the target prototype requirements, patterns from `patterns.md`, the 5-block anatomy, line bounds (600–1,500 lines, hard ceiling 1,800), and pyray CFFI gotchas. It carries zero previous token history from earlier games, preventing memory/attention drift.
     - **Zero In-Chat Code Spillage**: The subagent writes code directly to `minigames/<subfolder>/<script_name>.py` via `write_file`. It does NOT print the 600–1,500 lines of code into the chat conversation text.
     - **Non-Blocking Verification**: The subagent runs `$env:PYTHONDONTWRITEBYTECODE="1"; python -B audit_minigame.py minigames/<subfolder>/<script_name>.py`.
     - **Strict 1-Retry Policy**: If `audit_minigame.py` fails, the subagent performs at most one (1) retry fix. If it fails a second time, it halts and reports the failure.
     - **Concise Completion Report**: The subagent sends a 5-line summary message back to the Coordinator (File path, Line count, Demonstrated patterns, Audit status) and terminates.
  3. **Documentation & Release Synchronization**:
     - Upon receiving the Craftsman's success report, the Coordinator:
       - Updates `minigames.md` (marks `(built)` in the planned catalog and logs an entry in Section 2 Active Registry).
       - Updates `patterns.md` if registering new patterns.
       - Runs `python -B launcher.py --smoke-test` to verify launcher dropdown synchronization.
     - The Coordinator then advances directly to prototype $k+1$.
  4. **Dedicated Time & Pacing Allocation**: The system allocates ~4 to 6 minutes of deep compute and rigorous execution per prototype (accumulating ~30 to 45 minutes for a full 6–8 prototype run). Subagents must NEVER rush, truncate comments, or omit 5-block components to finish early.
  5. **Autonomous Non-Intervention Guarantee**: As long as the request specifies target prototypes and sections clearly, the Coordinator executes the entire multi-agent pipeline autonomously without pausing to ask conversational questions or requesting manual approvals between files.
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
- Every minigame inside `minigames/` must be a **single, self-contained Python script** located inside its designated 3.x category subfolder (e.g., `minigames/3.0_core_prototypes/space_swarm.py` or `minigames/3.1_menus_ui/weapon_wheel.py`).
- In **EVERY** script, you **MUST** import in this exact order:
  ```python
  from pyray import *
  from assets import *
  from utils import *
  ```
- Importing `from utils import *` after `from pyray import *` automatically enables the repository's **Global Top-Bar Settings Dropdowns** (`Font`, `Font Size [Ctrl +/-]`, and `Window Size / Fullscreen [F11]`) backed by `config.json`. Keep the top-bar region `x = 450..980, y = 14..48` free of HUD text so the dropdown bar (`draw_ui_settings_bar(450, 16)`) never overlaps your HUD.
- Every minigame must be directly executable from the terminal (`python -B minigames/<subfolder>/<script_name>.py`) and discoverable via the root [`launcher.py`](launcher.py).

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
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

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

### Rule 6: Mandatory Non-Blocking Verification & Strict 1-Retry Policy
- **NEVER** execute `python -B minigames/<subfolder>/<script>.py` without `--smoke-test` from an agent tool call, because the Raylib window will stay open indefinitely and hang the terminal.
- After creating or editing any minigame, you **MUST** verify it using the automated gatekeeper:
  ```bash
  $env:PYTHONDONTWRITEBYTECODE="1"
  python -B audit_minigame.py minigames/<subfolder>/<script_name>.py
  ```
  *(This executes template checks, C++-transferable AST rules, and 3 full Raylib `update()`/`draw()` frames to catch 100% of syntax errors, missing imports, and CFFI type mismatches).*
- **Strict 1-Retry Policy for Bug Fixes**:
  - If `audit_minigame.py` or `--smoke-test` fails (AST rule violation, syntax error, pyray CFFI type crash, missing imports, or logic defect), the agent is permitted **AT MOST ONE (1) retry pass** to correct all identified issues.
  - **Line Cap Preservation**: The corrected file MUST STILL remain strictly under the **1,800-line hard ceiling** (and target the 600–1,500 line range, with a 600-line minimum).
  - **Terminal Stop on Second Failure**: If the script still fails after the single retry attempt, the agent **MUST STOP IMMEDIATELY**, log the exact error and line numbers to the user, and request human guidance rather than attempting further automated loops.

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
4. **Dual Smoke Test**: Run both `python -B minigames/<subfolder>/<script_name>.py --smoke-test` AND `python -B launcher.py --smoke-test` to verify zero regressions in the prototype and the launcher dropdown system.

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
└── minigames/                 <-- Categorized single-file minigames & pattern labs
    ├── 3.0_core_prototypes/   <-- Full multi-pattern prototypes (Space Swarm, Mecha Colosseum, Drone Defense)
    ├── 3.1_menus_ui/          <-- Tactile UI and inventory labs (Title Screen, Weapon Wheel, Attaché Case, etc.)
    ├── 3.2_combat_weapons/    <-- Combat mechanics (Hitscan, Ballistics, Recoil, Ammo, Parry)
    ├── 3.3_enemies_ai/        <-- AI patterns (Patrols, Alert FSM, Flow Fields, Boss Phases)
    ├── 3.4_progression_economy/<-- RPG loops (Loot tables, Crafting, XP curves, Shops)
    ├── 3.5_world_exploration/ <-- Procedural generation (Voxel chunks, Caves, BSP Dungeons)
    ├── 3.6_movement_camera/   <-- Kinematic movement feel (Coyote time, Jump buffer, Dash, Grapple)
    └── 3.7_puzzle_stealth/    <-- Logic & systemic mechanics (Push blocks, Vision cones, Undo/Redo)
```
