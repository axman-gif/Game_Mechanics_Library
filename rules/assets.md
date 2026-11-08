# Procedural Assets Hub (`assets/`)
===================================

Welcome to the procedural asset index and architectural hub for the **Video Game Design Patterns Library**.

In this repository, **all visual models, 2D sprites, sound effects (SFX), and background music (BGM) are constructed 100% procedurally in memory** using mathematical primitives, pure trigonometry, and raw waveform synthesis. External art files (`.png`, `.jpg`, `.obj`, `.fbx`) and recorded audio files (`.wav`, `.mp3`, `.ogg`) are strictly forbidden.

---

## 💡 Repository Philosophy & C++ Porting Principle

This repository is built for **learning and inspiration**. In alignment with [`README.md`](../README.md) and [`AGENTS.md`](../AGENTS.md):
- **Simple beats clever**: Prefer straightforward, legible implementations over clever tricks.
- **Python as Executable Pseudocode**: Python is used exclusively as readable pseudocode designed so a student or developer can study data structures, trigonometry, and synthesis loops, and port them **1-to-1 to C++, C, C#, Rust, or Zig**.
- **Pedagogical Comments**: Comments explain **WHY** equations, angles, and buffer layouts work in plain language without academic jargon.

```
❌ Forbidden in Asset Code:              ✅ Used Instead:
---------------------------------------------------------------------------------
No @dataclass, @property, or decorators Explicit struct-like classes with __init__
No generators (yield) or async/await     Explicit frame/sample loops and step indices
No magic dunders (__call__, __len__, etc.) Named methods (calc_joint(), get_slot())
No per-frame list/dict comprehensions    Pre-allocated fixed arrays & in-place loops
No dynamic getattr/eval/metaclasses      Direct struct field access and explicit math
No hardcoded magic numbers               Named module-level constants & palette dicts
No lambda, map, or filter chains         Clear for-loops and explicit if-conditions
```

### Direct 1-to-1 Mapping to C++ Raylib (`raylib.h`):

| Asset Concept in this Repo (`pyray`) | Equivalent Direct C++ Code (`raylib.h`) |
| :--- | :--- |
| `DEFAULT_PALETTE = {"armor": Color(45, 55, 72, 255)}` | `struct Palette { Color armor; ... }; const Palette DEFAULT_PALETTE = { {45, 55, 72, 255} };` |
| `draw_cube(pos, width, height, length, col)` | `DrawCube(pos, width, height, length, col);` |
| `draw_sphere(pos, radius, col)` | `DrawSphere(pos, radius, col);` |
| `draw_circle_v(center, radius, col)` | `DrawCircleV(center, radius, col);` |
| `draw_rectangle_pro(rect, origin, rot, col)` | `DrawRectanglePro(rect, origin, rot, col);` |
| `load_wave_from_memory(".wav", data, len(data))` | `LoadWaveFromMemory(".wav", buffer, bufferSize);` |
| `load_sound_from_wave(wave)` | `LoadSoundFromWave(wave);` |
| `load_music_stream_from_memory(".wav", data, len(data))` | `LoadMusicStreamFromMemory(".wav", buffer, bufferSize);` |

---

## 📏 Readability Criterion & Sizing Guidelines

### Readability Criterion
> **A file must be understandable reading top to bottom, without jumping to other files; clarity wins over line count.**

Code organization must be linear and self-contained. A learner should be able to scroll from the module header, past constants and palettes, down through procedural drawing or synthesis functions, and end at the standalone previewer without needing external mental context.

### Line Limits (Token Control Guidance)
Line limits exist to guide token economy and prevent bloated files:

| Target Category | Floor | Target Range | Hard Ceiling |
| :--- | :---: | :---: | :---: |
| **Procedural Assets** (SFX, BGM, 3D Models, 2D Sprites) | **200 lines** | **200 – 800 lines** | **1,000 lines** |
| **Minigames** (Core Prototypes & Single-Pattern Labs) | **300 lines** | **300 – 1,500 lines** | **1,800 lines** |

- **Guidance, Not Artificial Padding**: Line limits are strictly guidance for token control. **Never pad a file** with redundant blank lines or meaningless filler to reach the floor.
- **Never Compress at the Expense of Clarity**: **Never compress code**, collapse multi-line structures, or drop pedagogical comments to stay under the ceiling. Clarity always takes precedence.

---

## 📚 Dedicated Asset Catalogs & Spreadsheets

Specifications, templates, and tracking are decomposed into three dedicated rulebooks and companion spreadsheets:

| Asset Kind | Architectural Rules & Template | Tracking Spreadsheet | Planned Items | Default Destination |
| :--- | :--- | :--- | :---: | :--- |
| **Procedural Sound Effects (SFX)** | [**`rules/audio.md`**](audio.md) | [**`tasks/SFXs.csv`**](../tasks/SFXs.csv) | See [`tasks/SFXs.csv`](../tasks/SFXs.csv) (73 SFX) | `assets/audio/synth_sfx.py`<br>`assets/audio/SFX/` |
| **Background Music (BGM)** | [**`rules/audio.md`**](audio.md) | [**`tasks/BGMs.csv`**](../tasks/BGMs.csv) | See [`tasks/BGMs.csv`](../tasks/BGMs.csv) (18 BGM) | `assets/audio/synth_sfx.py`<br>`assets/audio/BGM/` |
| **3D Procedural Models** | [**`rules/models_3D.md`**](models_3D.md) | [**`tasks/models_3D.csv`**](../tasks/models_3D.csv) | See [`tasks/models_3D.csv`](../tasks/models_3D.csv) (29 models) | `assets/models_3D/` |
| **2D Procedural Sprites** | [**`rules/sprites_2D.md`**](sprites_2D.md) | [**`tasks/sprites_2D.csv`**](../tasks/sprites_2D.csv) | See [`tasks/sprites_2D.csv`](../tasks/sprites_2D.csv) (29 sprites) | `assets/sprites_2D/` |

*(Note: Link targets resolve from this document's folder: rulebooks use `audio.md`, `models_3D.md`, `sprites_2D.md`, while spreadsheets use `../tasks/<catalog>.csv`.)*

### 🔒 Mandatory Asset Prerequisite Verification Gate (Upstream Pipeline)
Procedural visual models, 2D sprites, sound effects, and music are strictly **upstream dependencies** for all minigames:
1. **Lightweight Headless Inspection**: When a user requests a minigame, the Lead Orchestrator runs a Python script parsing strictly `id`, `status`, and `description` from all `tasks/*.csv` files (via `python -B tasks.py --check-prerequisites <minigame_id>`).
2. **Quality Preservation Rule**: If **even a single (1) asset** required by the minigame is missing or pending (`status == pending`):
   - The Orchestrator **halts craftsman invocation** for that minigame.
   - The Orchestrator explains to the user which assets are missing and how withholding the craftsman preserves the library's code quality and visual/audio polish (preventing inlined waveforms, ad-hoc primitive drawings, or broken placeholders under **Rule 10**).
3. **Specification Injection**: Once all required assets exist (`status == done`), the Orchestrator injects the exact asset signatures (`draw_<name>_3d`, `draw_<name>_2d`, `SFXS = [...]`, `BGMS = [...]`) into the subagent craftsman prompt.

---

## 🧩 Unified Asset Contract & Standard Signatures

All procedural assets in this repository adhere to a strict **Unified Asset Contract** so minigames can consume them interchangeably and predictably:

### 1. 3D Procedural Primitive Models
- **Canonical Signature**:
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
- **Angle Standard**: `rotation_y` is specified in **DEGREES** ($0^\circ \dots 360^\circ$) to match Raylib's 3D rotation conventions.
- **Render Context**: Must be called within `begin_mode_3d(camera)` ... `end_mode_3d()`.
- **Palette**: Exposes explicit `DEFAULT_<NAME>_PALETTE` mapping semantic body parts (`armor`, `joints`, `visor`, `core`, `thruster`) to Raylib `Color` instances.

### 2. 2D Procedural Vector Sprites
- **Canonical Signature**:
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
- **Angle Standard**: `facing_angle_rad` is specified in **RADIANS** ($0 \dots 2\pi$) for direct compatibility with 2D trigonometry (`math.cos`, `math.sin`, vector rotation).
- **Render Context**: Screen-space or 2D camera viewport (`begin_mode_2d(camera)` ... `end_mode_2d()`).
- **Palette**: Exposes explicit `DEFAULT_<NAME>_PALETTE` mapping semantic elements (`body`, `eyes`, `outline`, `accent`, `weapon`) to Raylib `Color` instances.

### 3. Procedural Audio (SFX & BGM)
- **Asset Creation Signatures**:
  - Sound Effects (`assets/audio/SFX/<category>/<name>.py`): `create_<name>_sfx() -> Sound` (alias `create_sfx`).
  - Background Music (`assets/audio/BGM/<vibe>/<name>.py`): `create_<name>_bgm() -> Music` (alias `create_bgm`).
- **In-Memory Synthesis**: Both SFX and BGM return ready-to-use Raylib audio structs synthesized purely in RAM using an in-memory RIFF WAV packer (`pack_riff_wav_mono_16bit`). SFX loads into Raylib `Sound` structs; BGM streams dynamically via Raylib `Music` structs.
- **Dynamic Registry & Selective In-RAM SoundLibrary (`assets/audio/synth_sfx.py`)**:
  Minigames declare strictly the required audio cues in `SFXS = [...]` and `BGMS = [...]` lists. `SoundLibrary.load(sfx=SFXS, bgm=BGMS)` dynamically loads and synthesizes *only* those declared files into hardware RAM:
  - `load(sfx=list, bgm=list)`: Dynamically compiles declared audio into RAM.
  - `play(name, volume=1.0, pitch=1.0, loop=None)`: Unified playback for Sound and Music.
  - `stop(name=None)`: Halt playback of specific cue or all audio.
  - `pause(name)` / `resume(name)`: Temporarily pause or resume audio stream.
  - `update()`: Called **once per frame** in the game loop's `update(dt)` method to feed active streaming music buffers.
  - `unload_all()`: Free all allocated Raylib audio memory upon game shutdown.

---

## 🔢 Named Constants Guideline (No Magic Numbers)

Rather than embedding raw numeric literals directly inside trigonometric formulas, geometry offsets, or sample synthesis loops, declare explicit **named module-level constants**:

```python
# ✅ GOOD: Explicit named constants describe geometry and dimensions clearly
CHASSIS_WIDTH = 2.4
CHASSIS_HEIGHT = 1.1
CHASSIS_LENGTH = 3.6
TURRET_RADIUS = 0.8
BARREL_LENGTH = 1.8
BARREL_RADIUS = 0.15

# ❌ FORBIDDEN: Raw magic numbers obscure architectural meaning
draw_cube(pos, 2.4, 1.1, 3.6, color)
draw_cylinder(pos, 0.8, 0.8, 1.8, 16, color)
```

- **Self-Documenting Geometry**: Constants make the anatomical scale and proportions immediately clear to readers.
- **Direct C++ Translation**: Maps directly to C++ typed constants (`const float CHASSIS_WIDTH = 2.4f;`).
- **Frictionless Tuning**: Proportions can be refined at the top of the file without hunting through drawing procedures.

---

## 🚫 Assets-Only Minigames Rule

To maintain strict modular decoupling across the repository:

> **Minigames inside `minigames/` MUST consume ONLY procedural assets that already exist in `assets/` and are discovered via `assets/audio/asset_loader.py`.**

- **No Ad-Hoc Inline Assets**: Minigame scripts must never draw complex multi-part custom entities directly in their world blocks, nor synthesize ad-hoc audio waves locally.
- **Missing Asset Protocol**: If a minigame design requires a visual model, 2D sprite, SFX, or BGM track that does not yet exist in `assets/`:
  1. **STOP IMMEDIATELY**.
  2. **Do not write placeholder code** or inline drawing hacks.
  3. **Report the missing asset** to the Orchestrator or user so the asset can be scheduled and created in `assets/` first.

---

## 🏛️ Mandatory Anatomy Contract for Procedural Asset Modules

Every procedural asset file created inside `assets/` must follow an identical 6-part anatomy to guarantee consistency, C++ transferability, and testability:

```python
# -*- coding: utf-8 -*-
"""
<Asset Name> - <Asset Category>
================================
Type             : <3D Model / 2D Sprite / SFX / BGM>
Target File      : <assets/.../filename.py>
Primitives / Math: <Geometric primitives or Waveform equations used>

Description & Pedagogical Concept:
  <2-3 sentences explaining the design, geometric breakdown, or waveform theory>

C++ Raylib Equivalent:
  <Explanation of how this maps to C++ struct layout and Raylib C calls>
"""

import sys
import os
import math
import struct as py_struct  # Aliased to prevent collision with pyray.struct

# 1. Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# 2. Add repository root to search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# 3. Mandatory Raylib and utility imports
from pyray import *
from utils import *

# 4. Explicit Semantic Color Palette / Named Constants
# (e.g., DEFAULT_<NAME>_PALETTE = { ... }, CORE_RADIUS = 0.5, etc.)

# 5. Core Procedural Rendering / Synthesis Function
# (e.g., draw_<name>_3d / draw_<name>_2d / create_<name>_sfx / create_<name>_bgm)

# 6. Standalone Interactive Previewer & Automated Smoke Test
# (if __name__ == "__main__": with --smoke-test support)
```

---

## 🚀 Unified Import & Minigame Usage

Minigames inside `minigames/` can import assets using the central asset loader dictionaries or granular imports:

### Bulk Import via Central Asset Loader (Recommended for Minigames):
```python
from assets.audio.asset_loader import *
# Exposes dictionary registries: models_3D, sprites_2D, audio, sfx, bgm
# and dynamic loaders: import_asset_by_key, load_model_3d, load_sprite_2d
```

### Key-Based Dynamic Loading in Minigames:
```python
# 3D Model by key
draw_knight, knight_palette = load_model_3d("exo_knight")

# 2D Sprite by key
draw_ops, ops_palette = load_sprite_2d("tactical_ops")

# Audio cues by key via SoundLibrary
SFXS = ["laser"]
BGMS = ["synth_pulse"]
```

### Granular Direct Import:
```python
# 3D Models
from assets.models_3D.exo_knight import draw_exo_knight_3d, DEFAULT_EXO_KNIGHT_PALETTE

# 2D Sprites
from assets.sprites_2D.tactical_ops import draw_tactical_ops_2d, DEFAULT_TACTICAL_OPS_PALETTE

# Audio Subsystem (Selective In-RAM Loading)
from assets.audio.synth_sfx import SoundLibrary, SFX_REGISTRY, BGM_REGISTRY
```

### Complete Minigame Integration Example:
```python
# 1. Module-level selective audio lists (load only what is needed)
SFXS = ["laser"]
BGMS = ["synth_pulse"]

class MinigameSimulation:
    def __init__(self):
        init_audio_device()
        self.sfx = SoundLibrary()
        self.sfx.load(sfx=SFXS, bgm=BGMS)
        self.sfx.play("synth_pulse", volume=0.6, loop=True)  # Stream music continuously
        self.anim_timer = 0.0
        self.facing_angle_deg = 45.0  # 3D rotation in degrees
        self.facing_angle_rad = 0.785 # 2D rotation in radians

    def update(self):
        dt = get_frame_time()
        self.anim_timer += dt
        
        # Feed streaming music buffers once per frame
        self.sfx.update()
        
        # Trigger sound effect
        if is_key_pressed(KEY_SPACE):
            self.sfx.play("laser", volume=0.8)

    def draw(self):
        begin_drawing()
        clear_background(Color(15, 18, 26, 255))
        
        # 3D Mode: Draw 3D procedural entities (rotation in DEGREES)
        begin_mode_3d(self.camera)
        draw_exo_knight_3d(
            Vector3(0.0, 0.0, 0.0),
            rotation_y=self.facing_angle_deg,
            anim_timer=self.anim_timer,
            scale=1.0
        )
        end_mode_3d()
        
        # 2D Mode: Draw 2D procedural sprites (rotation in RADIANS)
        draw_tactical_ops_2d(
            Vector2(120.0, 120.0),
            facing_angle_rad=self.facing_angle_rad,
            anim_timer=self.anim_timer,
            scale=1.0
        )
        
        # Global UI Settings Bar
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)
        end_drawing()
```

---

## 🛠️ Autonomous Subagent Asset Creation & Task Lifecycle Protocol

When an AI craftsman subagent is assigned to build an asset:

1. **Step 1: Route to Dedicated Rulebook**:
   Craftsmen review the specific architectural rules and previewer templates in:
   - 3D Models: [**`rules/models_3D.md`**](models_3D.md)
   - 2D Sprites: [**`rules/sprites_2D.md`**](sprites_2D.md)
   - Procedural Audio: [**`rules/audio.md`**](audio.md)

2. **Step 2: Direct Spec Injection (Zero CSV Tokens Spent by Craftsmen)**:
   The Orchestrator queries task specifications using the headless CLI:
   ```bash
   python -B tasks.py --get <catalog> <task_id>
   ```
   The Orchestrator injects the target specifications directly into the subagent prompt. **Neither Orchestrator nor Craftsmen read raw `.csv` files into context**, preserving token budgets.

3. **Step 3: Collision Prevention Check**:
   Before creating a new asset module, verify that the function name does not already exist:
   ```bash
   python -B tasks.py --check <catalog> <function_name>
   ```

4. **Step 4: Implementation using Canonical 6-Part Anatomy**:
   Write the module directly to disk respecting the Unified Asset Contract, named constants guideline, and C++ transferability rules.

5. **Step 5: Non-Blocking Automated Verification**:
   Verify the asset via its standalone smoke test:
   ```bash
   $env:PYTHONDONTWRITEBYTECODE="1"
   python -B <target_file> --smoke-test
   ```

6. **Step 6: Orchestrator-Exclusive Lifecycle & Registration**:
   Subagent craftsmen **do not** edit tracking spreadsheets (`tasks/*.csv`) or core registries. Craftsmen send a concise completion report to the Lead Orchestrator.
   The **Lead Orchestrator exclusively**:
   - Automatically synchronizes task status across catalogs upon batch completion:
     ```bash
     python -B tasks.py --sync-statuses
     ```
   - Newly built assets are automatically discovered dynamically by `assets/audio/asset_loader.py`.

---

## 🏛️ Golden Asset Rules Summary

1. **Zero External Media Files**: No `.png`, `.jpg`, `.bmp`, `.wav`, `.mp3`, `.ogg`, `.obj`, or `.fbx` files.
2. **C++ Transferability**: Plain classes with explicit `__init__`, fixed arrays, explicit loops, zero decorators, zero generators, zero lambdas, zero magic dunders.
3. **Canonical Directories & Files**:
   - `assets/audio/asset_loader.py` for dynamic discovery dictionary registries (`models_3D`, `sprites_2D`, `audio`, `sfx`, `bgm`)
   - `assets/audio/synth_sfx.py` for procedural audio synthesis engine & `SoundLibrary`
   - `assets/audio/SFX/<category>/` for dedicated modular sound effects
   - `assets/audio/BGM/<vibe>/` for algorithmic background music tracks categorized by emotional vibe
   - `assets/models_3D/` for 3D primitive models
   - `assets/sprites_2D/` for 2D primitive sprites
4. **Unified Asset Contract**:
   - 3D models: `draw_<name>_3d(pos, rotation_y=0.0, anim_timer=0.0, scale=1.0, palette=None)` with `rotation_y` in **degrees**.
   - 2D sprites: `draw_<name>_2d(pos, facing_angle_rad=0.0, anim_timer=0.0, scale=1.0, palette=None)` with `facing_angle_rad` in **radians**.
   - Audio: `create_<name>_sfx() -> Sound` and `create_<name>_bgm() -> Music` synthesized in memory, played via `SoundLibrary` (`play`, `stop`, `update`, `unload_all`).
5. **Named Constants**: Explicit module-level dimensions and radii instead of raw magic numbers.
6. **Assets-Only Minigames**: Minigames must consume only assets registered in `assets/`; halt and report missing assets before writing minigame code.
7. **Readability Criterion**: Every file must be understandable reading top to bottom, without jumping across files; clarity wins over line count.
8. **Strict Sizing Bounds**: Target 200 to 800 lines (Floor: **200 lines**, Ceiling: **1,000 lines**). Sizing is guidance for token control—never pad code to reach the floor, and never compress code or omit comments to stay under the ceiling.
9. **Standalone Preview & Smoke Test**: Every asset file must execute interactively when run directly (`python -B <file>.py`) and terminate cleanly after 3 frames when invoked with `--smoke-test`.
10. **Task Catalog Integrity**: Task statuses are strictly binary (`pending` / `done`) and synchronized automatically by the Orchestrator via `python -B tasks.py --sync-statuses` to prevent CSV corruption.
