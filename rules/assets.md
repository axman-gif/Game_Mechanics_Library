# Procedural Assets Hub (`assets/`)
===================================

Welcome to the procedural asset index and architectural hub for the **Video Game Design Patterns Library**.

In this repository, **all visual models, 2D sprites, sound effects (SFX), and background music (BGM) are constructed 100% procedurally in memory** using mathematical primitives, pure trigonometry, and raw waveform synthesis. External art files (`.png`, `.jpg`, `.obj`, `.fbx`) and recorded audio files (`.wav`, `.mp3`, `.ogg`) are strictly forbidden.

---

## 💡 The "No-Magic" C++ Porting Philosophy

In alignment with [`README.md`](../README.md) and [`AGENTS.md`](../AGENTS.md), Python is used exclusively as **executable, readable pseudocode**. Every procedural asset module is designed so a student or developer can study the data structures, trigonometric articulation, and sample synthesis loops, and port them **1-to-1 to C++, C, C#, Rust, or Zig**:

```
❌ Forbidden in Asset Code:              ✅ Used Instead:
---------------------------------------------------------------------------------
No @dataclass, @property, or decorators Explicit struct-like classes with __init__
No generators (yield) or async/await     Explicit frame/sample loops and step indices
No magic dunders (__call__, __len__, etc.) Named methods (calc_joint(), get_slot())
No per-frame list/dict comprehensions    Pre-allocated fixed arrays & in-place loops
No dynamic getattr/eval/metaclasses      Direct struct field access and explicit math
No hardcoded magic numbers               Named semantic constants & palette dicts
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

---

## 📚 Dedicated Asset Catalogs & Spreadsheets

To maintain token efficiency and ensure clean role specialization for AI craftsmen subagents, specifications and tracking are decomposed into three dedicated rule books and companion spreadsheets:

| Asset Kind | Architectural Rules & Template | Tracking Spreadsheet | Planned Items | Default Destination |
| :--- | :--- | :--- | :---: | :--- |
| **Procedural Audio (SFX & BGM)** | [**`audio.md`**](audio.md) | [**`tasks/audio.csv`**](../tasks/audio.csv) | **90 items** (73 SFX, 17 BGM) | `assets/audio/synth_sfx.py`<br>`assets/audio/SFX/`<br>`assets/audio/BGM/` |
| **3D Procedural Models** | [**`models_3D.md`**](models_3D.md) | [**`tasks/models_3D.csv`**](../tasks/models_3D.csv) | **29 models** | `assets/models_3D/` |
| **2D Procedural Sprites** | [**`sprites_2D.md`**](sprites_2D.md) | [**`tasks/sprites_2D.csv`**](../tasks/sprites_2D.csv) | **29 sprites** | `assets/sprites_2D/` |

---

## 🧩 Canonical Asset Interfaces & Standard Signatures

To ensure effortless and frictionless integration into minigames, all assets adhere to standardized function signatures and data contracts:

### 1. 3D Procedural Primitive Models
- **Signature**:
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
- **Context**: Must be called within `begin_mode_3d(camera)` ... `end_mode_3d()`.
- **Palette**: Exposes explicit `DEFAULT_<NAME>_PALETTE` mapping semantic body parts (`armor`, `joints`, `visor`, `core`, `thruster`) to Raylib `Color` instances.

### 2. 2D Procedural Vector Sprites
- **Signature**:
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
- **Context**: Screen-space or 2D camera viewport (`begin_mode_2d(camera)`).
- **Palette**: Exposes explicit `DEFAULT_<NAME>_PALETTE` mapping semantic elements (`body`, `eyes`, `outline`, `accent`, `weapon`) to Raylib `Color` instances.

### 3. Procedural Sound Effects (SFX)
- **Signature**:
```python
def create_sound_name_sfx() -> Sound:
    pass
```
- **Synthesis**: In-memory PCM wave synthesized into RIFF WAV bytes via `struct.pack`, loaded into a Raylib `Sound` struct via `load_wave_from_memory` and `load_sound_from_wave`.
- **Caching**: Loaded once at startup into `SoundLibrary` and played repeatedly with `sfx.play("<name>", volume)`.

### 4. Algorithmic Background Music (BGM)
- **Signature**:
```python
def generate_music_track() -> Music:
    pass
```
  *(Or driven frame-by-frame via `SynthMusicPlayer`)*
- **Synthesis**: Multi-layer procedural tracker sequencing bass, arpeggios, and percussion chords in RAM with seamless loop points.

---

## 🏛️ Mandatory Anatomy Contract for Procedural Asset Modules

Every asset file created inside `assets/` must follow an identical 6-part anatomy to guarantee consistency, C++ transferability, and testability:

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
import struct as py_struct  # Note: Aliased to prevent collision with pyray.struct string constant

# 1. Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# 2. Add repository root to search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# 3. Mandatory Raylib and utility imports
from pyray import *
from utils import *

# 4. Explicit Semantic Color Palette / Audio Specification Constants
# (e.g. DEFAULT_<NAME>_PALETTE = { ... })

# 5. Core Procedural Rendering / Synthesis Function
# (e.g. draw_<name>_3d / draw_<name>_2d / create_<name>_sfx)

# 6. Standalone Interactive Previewer & Automated Smoke Test
# (if __name__ == "__main__": with --smoke-test support)
```

---

## 🚀 Unified Import & Minigame Usage

Minigames inside `minigames/` can import assets using either bulk or granular imports:

### Bulk Import (Recommended for Prototypes):
```python
from assets import *
```

### Granular Import (For Isolated Testing):
```python
# 3D Models
from assets.models_3D.exo_knight import draw_exo_knight_3d, DEFAULT_EXO_KNIGHT_PALETTE

# 2D Sprites
from assets.sprites_2D.tactical_ops import draw_tactical_ops_2d, DEFAULT_TACTICAL_OPS_PALETTE

# Audio SFX & BGM
from assets.audio.synth_sfx import create_laser_sfx, create_explosion_sfx, SoundLibrary
from assets.audio.BGM.synth_music import generate_boss_track
```

### Complete Minigame Integration Example:
```python
# Inside Minigame update() and draw():
def update(self):
    dt = get_frame_time()
    self.anim_timer += dt
    if is_key_pressed(KEY_SPACE):
        self.sfx.play("laser", 0.8)

def draw(self):
    begin_drawing()
    clear_background(Color(15, 18, 26, 255))
    
    # 3D Mode: Draw 3D procedural entities
    begin_mode_3d(self.camera)
    draw_exo_knight_3d(Vector3(0.0, 0.0, 0.0), rotation_y=self.angle, anim_timer=self.anim_timer)
    end_mode_3d()
    
    # 2D Mode: Draw 2D procedural UI / HUD sprites
    draw_tactical_ops_2d(Vector2(100.0, 100.0), facing_angle_rad=0.0, anim_timer=self.anim_timer)
    
    # Global UI Settings Bar
    draw_gamepad_status_badge(985, 22, 11)
    draw_ui_settings_bar(450, 16)
    end_drawing()
```

---

## 🛠️ Autonomous Subagent Asset Creation Protocol

When an AI craftsman subagent is tasked with creating an asset (via single-turn prompt or `/teamwork` swarm):

1. **Step 1: Check Task Specifications**:
   Query [`tasks/audio.csv`](../tasks/audio.csv), [`tasks/models_3D.csv`](../tasks/models_3D.csv), or [`tasks/sprites_2D.csv`](../tasks/sprites_2D.csv) via the headless CLI:
   ```bash
   python -B tasks.py --get <catalog> <task_id>
   ```
2. **Step 2: Prevent Collisions**:
   Check if the function name already exists in the catalog:
   ```bash
   python -B tasks.py --check <catalog> <function_name>
   ```
3. **Step 3: Implement Module using Canonical Template**:
   Follow the dedicated code template in:
   - [`rules/models_3D.md`](models_3D.md) for 3D Models
   - [`rules/sprites_2D.md`](sprites_2D.md) for 2D Sprites
   - [`rules/audio.md`](audio.md) for SFX and BGM
   *Respect the sizing invariant: 400 to 800 lines (400 minimum, 1,000 maximum).*
4. **Step 4: Non-Blocking Automated Verification**:
   Execute the asset's built-in smoke test:
   ```bash
   $env:PYTHONDONTWRITEBYTECODE="1"
   python -B <target_file> --smoke-test
   ```
5. **Step 5: Mark Built**:
   Update task status on disk using the CLI:
   ```bash
   python -B tasks.py --set-status <catalog> <task_id> built
   ```

---

## 🏛️ Golden Asset Rules Summary

1. **Zero External Media Files**: No `.png`, `.jpg`, `.bmp`, `.wav`, `.mp3`, `.ogg`, `.obj`, or `.fbx` files.
2. **C++ Transferability**: Plain classes with explicit `__init__`, fixed arrays, explicit loops, zero decorators, zero generators, zero lambdas.
3. **Canonical Directories & Files**:
   - `assets/audio/synth_sfx.py` for Comprehensive Procedural SFX Synthesizer & SoundLibrary
   - `assets/audio/SFX/` for Dedicated Modular Sound Effects
   - `assets/audio/BGM/` for Algorithmic Background Music Tracks
   - `assets/models_3D/` for 3D Primitive Models
   - `assets/sprites_2D/` for 2D Primitive Sprites
4. **Strict Sizing Bounds**: Target 400 to 800 lines (Floor: **400 lines**, Ceiling: **1,000 lines**).
5. **Standalone Preview & Smoke Test**: Every asset file must execute interactively when run directly (`python -B <file>.py`) and terminate cleanly after 3 frames when invoked with `--smoke-test`.
6. **Task Catalog Integrity**: Always manage and update `tasks/*.csv` through `tasks.py` to prevent delimiter, quote, or encoding corruption.
