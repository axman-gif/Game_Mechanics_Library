# Minigames Architectural Guidelines & Master Template (`minigames/`)

This document defines the architectural standards, design principles, quality invariants, and authoritative 5-block implementation template for all standalone minigame prototypes in the repository.

All prototype inventory, tracking statuses, and subagent assignments are maintained exclusively in the companion spreadsheet:
👉 [**`tasks/minigames.csv`**](../tasks/minigames.csv) (106 planned prototypes across sections 3.0 to 3.7)

> **Architectural Documentation Notice**: This document is **read-only** during development and prototype creation. It serves as the single source of truth for minigame structure and code conventions. Status tracking (strictly binary `pending` / `done`) is managed automatically across [`tasks/minigames.csv`](../tasks/minigames.csv) via `python -B tasks.py --sync-statuses`, executed exclusively by the Lead Orchestrator upon batch completion. Subagents and craftsmen must never edit this file or the tracking spreadsheet.

---

## 1. Global Repository Philosophy & Core Invariants

This repository is built for **learning and inspiration**. Every prototype illustrates a concrete game programming pattern in isolation or in a focused multi-pattern arcade loop.

### 1.1 Simple Beats Clever
- Prioritize architectural clarity over clever language tricks or compressed syntax.
- Write code that explains itself through transparent naming, obvious control flow, and thorough educational commentary.
- Comments must explain **WHY** an equation, state machine, or data structure exists in plain language without unnecessary jargon.

### 1.2 Python as Executable Pseudocode (1-to-1 C++ Transferability)
Python is used strictly as readable, executable pseudocode. Learners study these minigames to understand data structures and algorithms, and port them directly to **C++, C, C#, Rust, or Zig**. All code must translate 1-to-1 to statically typed systems languages:
1. **NO Decorators**: Do not use `@dataclass`, `@property`, `@staticmethod`, `@classmethod`, `@lru_cache`, or custom decorators. Declare plain classes with an explicit `__init__(self)` constructor initializing every member variable line-by-line (equivalent to a C++ `struct` or `class`).
2. **NO Generators or Coroutines**: Do not use `yield`, `async`, or `await`. Frame-based game loops advance step-by-step via `update(dt)`. Multi-step sequences must be modeled with explicit state enums/integers and timers (`self.state`, `self.timer`).
3. **NO Dynamic Metaprogramming or Dunder Methods**: Do not define `__call__`, `__getitem__`, `__getattr__`, `__add__`, `__mul__`, or invoke `getattr()`, `setattr()`, `eval()`, `*args`, or `**kwargs`. Use explicit method calls (`pool.get_slot(i)`, `vector_add(a, b)`). Only `__init__` is permitted.
4. **NO Walrus Operators (`:=`) or Functional Chains**: Do not use walrus operators, `lambda`, `map`, or `filter`. Write explicit `for` loops and `if/else` branches so that $O(N)$ execution and branching complexity are immediately visible to anyone porting the logic to C++.
5. **Pre-allocated Fixed Arrays & Explicit Indices**: Avoid allocating dynamic lists inside frame loops (e.g. `enemies = [e for e in enemies if e.active]`). Instead, pre-allocate fixed-capacity lists (`self.pool = [Entity() for _ in range(MAX_ENTITIES)]`) with explicit integer counters and active flags, directly mirroring `std::array<T, N>` in C++.

### 1.3 Readability Criterion
> **Readability Criterion**: A file must be completely understandable reading top to bottom, without jumping back and forth across different files. Clarity always wins over line count.

- Organize code linearly: Configuration -> Pattern Class -> Entities -> Telemetry Overlay -> HUD -> Main Game Loop.
- Do not introduce hidden dependencies or implicit global side effects.
- Provide thorough comments explaining the mathematical and architectural rationale directly above the relevant operations.

### 1.4 Line Limits (Guidance for Token Control)
To preserve subagent context budgets and prevent code bloat while ensuring deep pedagogical value, the repository enforces line boundaries:

- **Minigames (Sections 3.0 through 3.7)**:
  - **Floor**: **300 lines minimum**. (Ensures sufficient depth, educational commentary, dual input parity, and X-Ray overlays).
  - **Target Range**: **300 to 1,500 lines**.
  - **Hard Ceiling**: **1,800 lines maximum**. (Prevents context exhaustion; verified by [`audit_minigame.py`](../audit_minigame.py)).
- **Procedural Assets (SFX, BGM, 3D Models, 2D Sprites)**:
  - **Floor**: **200 lines minimum**.
  - **Target Range**: **200 to 800 lines**.
  - **Hard Ceiling**: **1,000 lines maximum**.

> **Crucial Invariant on Line Limits**: These limits are **guidance for token control**, not arbitrary quotas. **Never pad a file** with redundant whitespace, meaningless loops, or dummy comments just to reach the floor. Conversely, **never compress code**, truncate functions, or drop educational comments to fit under the ceiling. If code is clear, well-commented, and implements the pattern genuinely, clarity always prevails.

---

## 2. Canonical 5-Block Minigame Template (Authoritative Copy)

Every minigame in `minigames/` must be a **single, standalone Python script** located in its designated 3.x category subfolder. It must follow the canonical 5-block anatomy detailed below.

### 2.1 The 5 Blocks Explained
1. **Block 1: Core Pattern Implementation**:
   - The pure, isolated pattern class or function (e.g., `ObjectPool`, `BehaviorTree`, `SpatialHashGrid`, `CoyoteTimer`, `CommandQueue`).
   - Completely decoupled from graphics or windowing logic.
   - Includes novice-friendly comments explaining *why* the data structures and algorithms work and how they map to C++ (e.g., struct layout, explicit indices, fixed buffers).
2. **Block 2: World Simulation & Entities**:
   - Simulation state, game entities, and mechanics that exercise the pattern.
   - Integrates with reusable assets ([`rules/assets.md`](assets.md)) and math/physics utilities ([`rules/utils.md`](utils.md)).
3. **Block 3: Telemetry & X-Ray Debug Overlay ([Tab] / Gamepad Y)**:
   - Live visual inspection overlay toggled via `[Tab]` or Gamepad `Y`.
   - Renders internal telemetry: active/free slot counters, state machine graphs, spatial grid cell boundaries, trajectory rays, or timing windows.
4. **Block 4: HUD & Settings Bar**:
   - Draws player-facing status badges, pattern toggle indicators (`[F1]`), and controls help.
   - Renders controller connection status via `draw_gamepad_status_badge(985, 22, 11)`.
   - Calls `draw_ui_settings_bar(450, 16)` to display the global Font, Font Size (`Ctrl +/-`), and Window Size (`F11`) dropdowns.
   - **Safe HUD Region**: Keeps `x = 450..980, y = 14..48` completely clear of text or game elements to avoid overlapping the settings dropdown bar.
5. **Block 5: Main Game Loop & Automated Smoke Test**:
   - Encapsulated in a `PatternLabGame` class with explicit `__init__`, `update(dt)`, `draw()`, and `run(smoke_test)`.
   - Headless verification exit: `if smoke_test and frame_count >= 3: break`.
   - Full audio teardown (`self.sfx.unload_all()`, `close_audio_device()`) and window close.

### 2.2 Authoritative 5-Block Script Template

```python
# -*- coding: utf-8 -*-
"""
<Prototype Title> - <Target Design Pattern(s)>
==============================================
Difficulty       : <1 - Beginner | 2 - Novice | 3 - Intermediate | 4 - Advanced | 5 - Master>
Section          : <3.0, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, or 3.7>
Pattern Category : <Category from rules/patterns.md>
Dimension        : <2D or 3D>

Problem Solved:
  <1-2 sentences explaining what goes wrong in game engines without this pattern>

How the Pattern Works:
  <Clear mathematical and architectural explanation of the pattern>

Interactive Learning Controls:
  - Movement / Aim                : WASD / Arrow Keys / Mouse / Gamepad Left & Right Stick
  - Primary / Secondary Action    : Left / Right Click / Gamepad RT & LT
  - [Tab] / Gamepad Y (Triangle)  : Toggle X-Ray Pattern Telemetry & Debug Overlay
  - [F1]  / Gamepad LB (L1)       : Toggle Pattern ON/OFF (compare behavior live)
  - [F2]  / Gamepad RB (R1)       : Toggle Secondary Parameter / Mode
  - [Ctrl +/-]                    : Adjust UI Font Size
  - [F11]                         : Toggle Fullscreen
  - [R]   / Gamepad Start         : Reset Simulation State
"""

import sys
import os
import math
import random

# 1. Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# 2. Add repository root to search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# 3. Mandatory Raylib, Asset, and Utility imports in exact order
from pyray import *
from assets.audio.asset_loader import *
from utils import *

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WINDOW_TITLE = "<Prototype Title> - <Pattern Name> (Raylib Pattern Lab)"

# ------------------------------------------------------------------------------
# Audio Assets Configuration (Selective In-RAM Loading)
# Minigames declare strictly the audio cues needed to avoid loading unused assets.
# ------------------------------------------------------------------------------
SFXS = ["laser"]
BGMS = ["synth_pulse"]


# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATION (<PATTERN NAME>)
# ==============================================================================
# C++ Architecture Note:
# In C++, this pattern is represented as a concrete struct/class with pre-allocated
# storage (e.g. std::array<Slot, CAPACITY>). Avoid dynamic heap allocations during
# gameplay updates. Member variables use explicit scalar types and index pointers.

class PatternManager:
    """
    Pure pattern logic isolated from rendering and platform dependencies.
    """
    def __init__(self, capacity: int = 64):
        self.capacity = capacity
        # Pre-allocated fixed list representing contiguous C++ memory buffer
        self.active_flags = [False] * capacity
        self.values = [0.0] * capacity
        self.active_count = 0
        self.is_enabled = True

    def reset(self):
        """Reset internal pattern state without reallocating buffers."""
        for i in range(self.capacity):
            self.active_flags[i] = False
            self.values[i] = 0.0
        self.active_count = 0

    def update(self, dt: float):
        """Advance pattern state frame-by-frame."""
        if not self.is_enabled:
            return
        for i in range(self.capacity):
            if self.active_flags[i]:
                self.values[i] -= dt
                if self.values[i] <= 0.0:
                    self.active_flags[i] = False
                    self.active_count -= 1


# ==============================================================================
# BLOCK 2: WORLD SIMULATION & ENTITIES
# ==============================================================================
class SimulationEntity:
    """
    Game entity interacting with the core pattern.
    """
    def __init__(self, x: float, y: float):
        self.position = Vector2(x, y)
        self.velocity = Vector2(0.0, 0.0)
        self.radius = 16.0
        self.is_alive = True

    def update(self, dt: float):
        self.position.x += self.velocity.x * dt
        self.position.y += self.velocity.y * dt


class SimulationWorld:
    """
    Manages entities, physics integration, and interactions.
    """
    def __init__(self, pattern: PatternManager, sfx: SoundLibrary):
        self.pattern = pattern
        self.sfx = sfx
        self.player = SimulationEntity(SCREEN_WIDTH * 0.5, SCREEN_HEIGHT * 0.5)
        self.entities = [SimulationEntity(100.0 * i, 200.0) for i in range(8)]

    def reset(self):
        self.pattern.reset()
        self.player.position = Vector2(SCREEN_WIDTH * 0.5, SCREEN_HEIGHT * 0.5)
        self.player.velocity = Vector2(0.0, 0.0)

    def update(self, dt: float):
        # Dual-input polling for simultaneous Keyboard/Mouse and Gamepad
        move_x, move_y = get_dual_move_2d(deadzone=0.18)
        speed = 280.0
        self.player.velocity.x = move_x * speed
        self.player.velocity.y = move_y * speed
        self.player.update(dt)

        # Keep player within screen bounds
        self.player.position.x = max(20.0, min(float(SCREEN_WIDTH - 20), self.player.position.x))
        self.player.position.y = max(60.0, min(float(SCREEN_HEIGHT - 20), self.player.position.y))

        # Advance pattern logic
        self.pattern.update(dt)


# ==============================================================================
# BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY ([Tab] / Gamepad Y)
# ==============================================================================
def draw_xray_overlay(world: SimulationWorld, pattern: PatternManager):
    """
    Visualizes internal pattern states, allocation metrics, and spatial vectors.
    """
    # 1. World-space visual telemetry (wireframes, bounds, vector rays)
    draw_circle_lines(int(world.player.position.x), int(world.player.position.y), 
                      int(world.player.radius + 8.0), Color(0, 220, 255, 180))

    # 2. Diagnostic Telemetry HUD panel (bottom-left)
    panel_x = 24
    panel_y = SCREEN_HEIGHT - 170
    panel_w = 340
    panel_h = 145

    draw_rectangle(panel_x, panel_y, panel_w, panel_h, Color(16, 20, 32, 230))
    draw_rectangle_lines(panel_x, panel_y, panel_w, panel_h, Color(60, 100, 160, 255))

    draw_text("[TAB] X-RAY PATTERN TELEMETRY", panel_x + 12, panel_y + 10, 13, Color(0, 220, 255, 255))
    draw_text(f"Pattern Status : {'ENABLED (Pattern Active)' if pattern.is_enabled else 'DISABLED (Raw Baseline)'}", 
              panel_x + 12, panel_y + 32, 12, Color(220, 220, 220, 255))
    draw_text(f"Active Slots   : {pattern.active_count} / {pattern.capacity}", 
              panel_x + 12, panel_y + 52, 12, Color(200, 200, 200, 255))
    draw_text(f"Player Pos     : ({world.player.position.x:.1f}, {world.player.position.y:.1f})", 
              panel_x + 12, panel_y + 72, 12, Color(180, 180, 180, 255))
    draw_text(f"Velocity Vector: ({world.player.velocity.x:.1f}, {world.player.velocity.y:.1f})", 
              panel_x + 12, panel_y + 92, 12, Color(180, 180, 180, 255))

    # Capacity utilization progress bar
    bar_x = panel_x + 12
    bar_y = panel_y + 118
    bar_w = panel_w - 24
    bar_h = 12
    draw_rectangle(bar_x, bar_y, bar_w, bar_h, Color(30, 35, 50, 255))
    fill_w = int(bar_w * (pattern.active_count / max(1, pattern.capacity)))
    draw_rectangle(bar_x, bar_y, fill_w, bar_h, Color(0, 200, 120, 255))
    draw_rectangle_lines(bar_x, bar_y, bar_w, bar_h, Color(80, 90, 120, 255))


# ==============================================================================
# BLOCK 4: HUD & SETTINGS BAR
# ==============================================================================
def draw_hud(world: SimulationWorld, pattern: PatternManager, show_xray: bool):
    """
    Renders top-bar status, controls legend, settings dropdowns, and gamepad badge.
    """
    # Title and Pattern status (top-left)
    draw_text(WINDOW_TITLE, 20, 16, 16, Color(240, 240, 240, 255))
    status_color = Color(80, 220, 120, 255) if pattern.is_enabled else Color(240, 90, 90, 255)
    status_text = "[F1/LB] Pattern: ACTIVE" if pattern.is_enabled else "[F1/LB] Pattern: BYPASS"
    draw_text(status_text, 20, 38, 14, status_color)

    # Controls legend (bottom-right)
    legend_y = SCREEN_HEIGHT - 65
    draw_text("Move: WASD / Stick | Action: Mouse / RT | Reset: [R] / Start", 
              SCREEN_WIDTH - 530, legend_y, 13, Color(160, 170, 190, 255))
    draw_text("Toggle X-Ray: [Tab] / Y | Toggle Pattern: [F1] / LB | Mode: [F2] / RB", 
              SCREEN_WIDTH - 530, legend_y + 20, 13, Color(140, 150, 170, 255))

    # Safe HUD region: keep x = 450..980, y = 14..48 completely clear of game text
    # Draw global UI Settings dropdowns (Font, Size [Ctrl+/-], Window [F11])
    draw_ui_settings_bar(450, 16)

    # Gamepad connection status indicator
    draw_gamepad_status_badge(985, 22, 11)


# ==============================================================================
# BLOCK 5: MAIN GAME LOOP & AUTOMATED SMOKE TEST
# ==============================================================================
class PatternLabGame:
    """
    Manages window lifecycle, audio device, event dispatch, and automated testing.
    """
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()

        # Audio synthesis library (Selective in-RAM compilation)
        self.sfx = SoundLibrary()
        self.sfx.load(sfx=SFXS, bgm=BGMS)

        # Core pattern and world instantiation
        self.pattern = PatternManager(capacity=64)
        self.world = SimulationWorld(self.pattern, self.sfx)

        # Debug & telemetry toggles
        self.show_xray = True

    def handle_input(self):
        """Processes global toggle inputs and resets."""
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
            self.sfx.play("click", 0.5)

        if is_dual_pattern_toggle_pressed():
            self.pattern.is_enabled = not self.pattern.is_enabled
            self.sfx.play("click", 0.7)

        if is_dual_reset_pressed():
            self.world.reset()
            self.sfx.play("click", 0.6)

    def update(self, dt: float):
        """Advances simulation and streams background music."""
        self.handle_input()
        self.world.update(dt)
        # Required every frame to feed in-memory audio/music buffers
        self.sfx.update()

    def draw(self):
        """Renders world entities, telemetry overlay, and HUD."""
        begin_drawing()
        clear_background(Color(14, 16, 24, 255))

        # World entities rendering
        p = self.world.player
        draw_circle(int(p.position.x), int(p.position.y), p.radius, Color(70, 140, 240, 255))
        draw_circle_lines(int(p.position.x), int(p.position.y), p.radius, Color(160, 200, 255, 255))

        # Block 3: Telemetry Overlay
        if self.show_xray:
            draw_xray_overlay(self.world, self.pattern)

        # Block 4: HUD and Top-Bar Settings Dropdowns
        draw_hud(self.world, self.pattern, self.show_xray)

        end_drawing()

    def run(self, smoke_test: bool = False):
        """
        Main simulation loop with automated non-blocking smoke test exit.
        """
        frame_count = 0
        while not window_should_close():
            dt = min(get_frame_time(), 0.05)
            self.update(dt)
            self.draw()
            frame_count += 1

            # Headless verification gatekeeper: exit immediately after 3 frames
            if smoke_test and frame_count >= 3:
                break

        # Teardown audio and window resources cleanly
        self.sfx.unload_all()
        close_audio_device()
        close_window()


if __name__ == "__main__":
    is_smoke = "--smoke-test" in sys.argv
    PatternLabGame().run(smoke_test=is_smoke)
```

---

## 3. Reusable Assets Integration & The "Assets-Only" Rule

All graphics and audio in this repository are created procedurally using pure geometric primitives and mathematical waveform synthesis. To preserve modularity and eliminate code duplication, minigames **never** synthesize waveforms or define low-level procedural draw primitives internally.

### 3.1 The "Assets-Only" Minigames Rule
> **MANDATORY ASSETS-ONLY RULE**: Minigames must use **ONLY** procedural assets that already exist inside `assets/` ([`rules/assets.md`](assets.md)).
>
> If a minigame prototype concept requires a procedural asset (a 3D model, 2D sprite, SFX, or BGM track) that is **not yet present** in the catalog:
> 1. **STOP IMMEDIATELY**. Do not write code or create dummy placeholder rendering inside the minigame.
> 2. **Report the missing asset** to the Orchestrator with its category and target interface.
> 3. Minigame subagents must **NEVER** create new files inside `assets/` or invent their own procedural rendering routines. Assets must be authored by dedicated asset craftsmen first, vetted by their standalone test harness, and registered by the Orchestrator.

### 3.2 Unified Asset Import Syntax
Minigames import procedural assets and utilities using clean, standardized interfaces:

```python
# Canonical import pattern at the top of every minigame
from pyray import *
from assets.audio.asset_loader import *
from utils import *
```

### 3.3 3D Models (`assets/models_3D/`)
3D procedural models follow a canonical function signature ([`rules/models_3D.md`](models_3D.md)):
```python
draw_<name>_3d(position: Vector3, rotation_y: float = 0.0, anim_timer: float = 0.0, scale: float = 1.0, palette: dict = None) -> None
```
- `rotation_y`: Specified in **DEGREES**.
- `palette`: Optional dictionary overriding default color constants.
- **Example Usage in Minigame**:
  ```python
  # Rendering an existing 3D scout ship
  ship_pos = Vector3(player.x, player.y, player.z)
  draw_scout_ship_3d(ship_pos, rotation_y=player.heading_deg, anim_timer=world.time, scale=1.2)
  ```

### 3.4 2D Sprites (`assets/sprites_2D/`)
2D procedural sprites follow a canonical function signature ([`rules/sprites_2D.md`](sprites_2D.md)):
```python
draw_<name>_2d(position: Vector2, facing_angle_rad: float = 0.0, anim_timer: float = 0.0, scale: float = 1.0, palette: dict = None) -> None
```
- `facing_angle_rad`: Specified in **RADIANS**.
- `palette`: Optional dictionary overriding default color constants.
- **Example Usage in Minigame**:
  ```python
  # Rendering an existing 2D crawler enemy
  enemy_pos = Vector2(enemy.x, enemy.y)
  draw_crawler_2d(enemy_pos, facing_angle_rad=enemy.angle, anim_timer=enemy.anim_time, scale=1.0)
  ```

### 3.5 Procedural Audio & Music (`assets/audio/`)
Audio is managed through `SoundLibrary` (`assets/audio/synth_sfx.py`), which dynamically inspects the modular asset category subfolders (`assets/audio/SFX/<category>/` and `assets/audio/BGM/<vibe>/`) and compiles into RAM **only** the specific audio files declared by the minigame:

#### 1. Importing the Audio Subsystem:
```python
from pyray import *
from assets.audio.asset_loader import *   # Automatically exports models_3D, sprites_2D, audio, sfx, bgm, SoundLibrary
from utils import *

# Or via granular import:
# from assets.audio.asset_loader import models_3D, sprites_2D, audio, sfx, bgm, SoundLibrary
```

#### 2. Declaring Required Audio Lists:
Every minigame specifies strictly two lists at module level:
```python
# Declare only the audio cues required by this prototype:
SFXS = ["laser", "hit", "explosion"]
BGMS = ["synth_pulse"]
```
- **Name or Path Resolution**: Items can be either clean cue names (`"laser"`, `"synth_pulse"`) or relative/absolute file paths (`"assets/audio/SFX/combat/laser.py"` or `"combat/laser"`). `SoundLibrary` resolves both automatically via `SFX_REGISTRY` and `BGM_REGISTRY`.
- **Zero RAM Waste**: Audio files not listed in `SFXS` or `BGMS` are **never** imported, parsed, or synthesized into hardware RAM.

#### 3. Initializing Audio in `PatternLabGame`:
```python
class PatternLabGame:
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()  # Mandatory BEFORE compiling audio into RAM

        # Selective Audio Loading:
        self.sfx = SoundLibrary()
        self.sfx.load(sfx=SFXS, bgm=BGMS)

        # Start looping background music (loop=True is default for BGM):
        self.sfx.play("synth_pulse", volume=0.6, loop=True)
```

#### 4. Playback and Control Methods:
- **Trigger Sound Effects**:
  ```python
  self.sfx.play("laser", volume=0.8, pitch=1.0)
  ```
- **Music Stream Controls**:
  ```python
  self.sfx.pause("synth_pulse")
  self.sfx.resume("synth_pulse")
  self.sfx.stop("synth_pulse")
  ```
- **CRITICAL Per-Frame Stream Update**:
  Background music streams audio dynamically in small chunks. You **MUST** call `self.sfx.update()` once per frame in your `update(dt)` loop:
  ```python
  def update(self, dt: float):
      self.handle_input()
      self.world.update(dt)
      self.sfx.update()  # Feeds active streaming music buffers
  ```
- **Clean Hardware Teardown**:
  ```python
  def teardown(self):
      self.sfx.unload_all()   # Frees all Sound and Music handles
      close_audio_device()    # Closes hardware audio driver
      close_window()
  ```

### 3.6 Reusable Utilities (`utils/`)
Never reinvent non-native math, collisions, or spatial partitioning algorithms ([`rules/utils.md`](utils.md)):
- **Rotated Collisions** (`utils.collisions`): `Capsule3D`, `Capsule2D`, `check_collision_capsules_3d`, `OBB2D`, `check_collision_obb_2d`.
- **Spatial Partitioning** (`utils.spatial_grid`): `SpatialGrid2D`, `SpatialGrid3D` for accelerating proximity queries from $O(N^2)$ to $O(N)$.
- **AI & Pathfinding** (`utils.ai_pursuit`): `seek_2d`, `predict_intercept_2d`, `find_path_astar`.
- **Math & Juice** (`utils.math_helpers`): `damp(current, target, smoothing, dt)`, `TraumaShake` (decaying rotational camera shake), `ease_out_bounce`.
- **Global UI Settings** (`utils.ui_settings`): `draw_ui_settings_bar(450, 16)`.
- **Simultaneous Dual Input** (`utils.gamepad_input`): `get_dual_move_2d()`, `get_dual_look_2d()`, `is_dual_*`.

---

## 4. Canonical Controls & Input Parity

Every minigame must provide **complete simultaneous dual-input parity** between Keyboard/Mouse and Gamepad (Controller). A player should be able to touch the controller, keyboard, or mouse at any time with instant response and zero input mode switching.

### 4.1 Canonical Input Mapping Table

| Interaction | Keyboard / Mouse | Gamepad (Xbox / PlayStation) | Architectural Purpose |
|---|---|---|---|
| **2D / 3D Movement** | `W`, `A`, `S`, `D` / Arrow Keys | Left Analog Stick / D-Pad | Smooth directional movement with radial deadzone |
| **Aim / Look / Steer** | Mouse Pointer / `Q`, `E` | Right Analog Stick | Analog rotational targeting or directional steering |
| **Primary Action** | Left Mouse Button / `Space` | Right Trigger (`RT`) / Button `X` ($\square$) | Primary weapon fire, tool activate, confirm |
| **Secondary Action** | Right Mouse Button | Left Trigger (`LT`) / Button `B` ($\bigcirc$) | Secondary fire, dash, alternate tool, cancel |
| **X-Ray Overlay** | `Tab` | Button `Y` ($\Delta$) | Toggle telemetry panel, vector rays, bounding volumes |
| **Pattern Toggle** | `F1` | Left Bumper (`LB` / `L1`) | Toggle pattern ON/OFF to compare behavior live |
| **Secondary Toggle** | `F2` | Right Bumper (`RB` / `R1`) | Cycle secondary pattern parameter or simulation mode |
| **Reset Simulation** | `R` | Start (`Start` / `Options`) | Fully reset entities, pools, and pattern state |
| **Font Size Scale** | `Ctrl` + `+` / `Ctrl` + `-` | — | Scaled by global UI Settings manager |
| **Fullscreen** | `F11` | — | Toggled by global UI Settings manager |

### 4.2 Safe HUD Region Invariant
The global UI Settings manager renders an interactive top-bar dropdown for font selection, font size offset, and window resolution.
- **Top-Bar Safe Area**: `x = 450..980, y = 14..48`.
- **Rule**: Never place minigame scores, title headers, health bars, or diagnostic text inside this rectangle.
- Minigame titles and primary status badges belong on the top-left (`x = 20..440, y = 16..50`).
- Gamepad status indicator belongs at `draw_gamepad_status_badge(985, 22, 11)`.

---

## 5. Catalog Taxonomy Overview (Sections 3.0 to 3.7)

The 106 planned prototypes in [`tasks/minigames.csv`](../tasks/minigames.csv) are categorized across 8 architectural sections and directories:

- **Section 3.0: Core Multi-Pattern Prototypes** (`minigames/3.0_core_prototypes/`, 7 prototypes):
  Full arcade and strategy loops combining 4+ patterns in concert (e.g. Orbital Siege 2D, Titan Strider 3D, Frontline Outpost RTS).
- **Section 3.1: Menus & UI** (`minigames/3.1_menus_ui/`, 17 prototypes):
  Tactile game UI patterns (Diegetic Wrist Comm, Micro-Inventory Grid, Modular Socket Workbench, Radial Pie, Strategy Ledger Tables).
- **Section 3.2: Combat & Weapons** (`minigames/3.2_combat_weapons/`, 17 prototypes):
  Ballistics, projectile arcs, parry timing windows, hit-stop juice, recoil impulses, predictive lead intercept, and auto-aim cones.
- **Section 3.3: Enemies & AI** (`minigames/3.3_enemies_ai/`, 15 prototypes):
  Flocking / boids, flow fields, behavior trees, finite state machines, colossus multi-segment bosses, and squad coordination blackboards.
- **Section 3.4: Progression & Economy** (`minigames/3.4_progression_economy/`, 12 prototypes):
  Cumulative loot table CDF sampling, mathematical XP curves, crafting dependency DAGs, gacha pity math, and dynamic shop economies.
- **Section 3.5: World & Procedural Exploration** (`minigames/3.5_world_procgen/`, 13 prototypes):
  Cellular automata caverns, BSP room dungeons, voxel DDA raymarching, dual-layer fog of war, and procedural infinite tile chunking.
- **Section 3.6: Movement & Camera Rigs** (`minigames/3.6_movement_camera/`, 12 prototypes):
  Platformer forgiveness (Coyote time & jump buffering), Verlet rope grappling, trauma screen shake, spring-arm cameras, and kinematic controllers.
- **Section 3.7: Puzzle, Stealth & Other** (`minigames/3.7_puzzle_stealth/`, 13 prototypes):
  Undo/redo command stacks, deadlock detection, cellular fluid simulation, light/shadow stealth cones, and rhythm hit-windows.

---

## 6. Exclusive Task Lifecycle & Orchestrator CLI Protocol

Task tracking and prototype assignments are decoupled from this architectural rulebook to prevent file merge conflicts during autonomous multi-agent sessions.

### 6.1 Exclusive CSV Task Lifecycle
1. Prototype tasks reside strictly in [`tasks/minigames.csv`](../tasks/minigames.csv) with columns: `id`, `section`, `difficulty`, `title`, `dimension`, `target_file`, `patterns`, `status`, `description`.
2. Allowed statuses are strictly binary: `pending` (target file does not exist on disk) and `done` (target file exists on disk).
3. Statuses are synchronized automatically by the Lead Orchestrator upon batch completion by executing:
   ```bash
   python -B tasks.py --sync-statuses minigames
   ```
4. Craftsmen and subagents receive their target prototype assignment directly in their dispatch prompt and **must never** open or modify `tasks/minigames.csv`.

### 6.2 Orchestrator Headless CLI Queries (<50 tokens)
The Lead Orchestrator queries prototype status and synchronizes tasks without loading large CSV files into LLM context:

```bash
# Query pending prototypes in Section 3.2
python -B tasks.py --list minigames --section 3.2 --status pending --limit 3

# Query prototypes by difficulty tier
python -B tasks.py --list minigames --difficulty beginner

# Fetch complete task specifications for a prototype by ID
python -B tasks.py --get minigames mg_3201_mortar_arc

# Synchronize disk file presence to task status automatically
python -B tasks.py --sync-statuses minigames
```

### 6.3 Human Tasks Editor (`tasks.py`)
Human developers inspect and edit tracking spreadsheets via the graphical Raylib task manager:
```bash
python -B tasks.py
```
This tool prevents comma, quote, and encoding corruption common in third-party spreadsheet software.

---

## 7. Automated Non-Blocking Verification Protocol

Every minigame script must be verified before declaring completion. Verification must run headlessly without opening an interactive window that hangs terminal execution:

### 7.1 Gatekeeper Static Audit
Verifies line counts (300 to 1,800), mandatory 5-block headers, dual input helpers, zero bytecode enforcement, and safe HUD region clearance:
```bash
$env:PYTHONDONTWRITEBYTECODE="1"
python -B audit_minigame.py minigames/<subfolder>/<script_name>.py
```

### 7.2 Headless Smoke Test Execution
Executes the minigame for strictly 3 frames to verify import resolution, CFFI type casting, shader/audio initialization, and clean teardown:
```bash
$env:PYTHONDONTWRITEBYTECODE="1"
python -B minigames/<subfolder>/<script_name>.py --smoke-test
```

### 7.3 Launcher Verification
Verifies that the new prototype is automatically discovered and indexed by the root catalog launcher:
```bash
$env:PYTHONDONTWRITEBYTECODE="1"
python -B launcher.py --smoke-test
```
