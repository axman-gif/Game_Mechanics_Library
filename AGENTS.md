# Agent Operating Instructions & Repository Context Hub (AGENTS.md)

Welcome, Agent. This repository is an **interactive encyclopedia of video game design patterns** built with **Raylib in Python (`pyray`)**.
The graphics and audio are intentionally built using **procedural primitives** (2D and 3D geometric shapes) and **in-memory audio synthesis** to emphasize architectural clarity, mathematical elegance, and hands-on pattern learning over external art assets.

---

## 1. Mandatory Step 0: Pre-Flight Check & Scope Control

**CRITICAL RULE**: Before generating code or planning a minigame/asset/feature, review existing workspace components:
1. **Catalog Taxonomy**: Review `rules/minigames.md` for guidelines and `tasks/minigames.csv` for task status:
   - **Section 3.0**: Core Multi-Pattern Prototypes (combining 4+ patterns).
   - **Sections 3.1–3.7**: Extended Single-Pattern Labs (3.1 Menus/UI, 3.2 Combat/Weapons, 3.3 Enemies/AI, 3.4 Progression/Economy, 3.5 World/Exploration, 3.6 Movement/Camera, 3.7 Puzzle/Stealth).
2. **Procedural Assets**: Consult `tasks/SFXs.csv`, `tasks/BGMs.csv`, `tasks/models_3D.csv`, and `tasks/sprites_2D.csv` via headless CLI (`python -B tasks.py --list`). Discovery and selective loading are handled dynamically by `assets/asset_loader.py` and `assets/audio/synth_sfx.py`. **NEVER duplicate existing assets.**
3. **Interactive Tasks Editor (`tasks.py`)**: All tracking spreadsheets in `tasks/` are inspected, edited, and maintained via `python -B tasks.py`.
4. **Existing Utilities & Math**: Review `rules/utils.md` to reuse non-native collision routines, spatial hash grids (`SpatialGrid2D`/`3D`), steering/pathfinding algorithms (A*, BFS, seek, lead intercept), math dampening, and the global UI settings bar (`utils/ui_settings.py`). **NEVER rewrite these utilities.**
5. **Game Design Patterns**: Consult `rules/patterns.md` to document demonstrated patterns. Subagents are encouraged to adapt or invent novel patterns and register them into `rules/patterns.md`.

### 1.1 Scope Control, Batch Allowance & Ambiguity Gate
Evaluate the clarity, target section, and batch size of every prompt:
- **Standard Batches (1 to 8 files)**:
  - Users may request batches of **up to 8 files** in a single standard prompt (e.g. `create 4 progression SFX` or `build 2 combat minigames`).
  - No slash command is required for batching. The Lead Orchestrator executes batches directly in the primary conversation using the Lean 1+N Swarm.
- **Oversized Batch Halt (> 8 files)**:
  - If a request asks for $> 8$ files in a single session, **STOP IMMEDIATELY WITHOUT TOUCHING CODE** and ask the user to split the request into batches of at most 8 files.
- **Ambiguity Halt**:
  - If a request is open-ended or underspecified (e.g. "make some games", "build some assets"), halt immediately and ask for specific prototype names or target categories.
- **Path Agnosticism**:
  - All commands, scripts, rules, and imports MUST use workspace-relative paths (`./minigames/...`, `./tasks.py`). Never hardcode local drive letters (`A:\`, `C:\`, etc.) so the repository remains 100% clone-ready on any public environment.
- **Mandatory Asset Prerequisite Gate (Minigames)**:
  - Before spawning a minigame engineer, the Lead Orchestrator parses `tasks/minigames.csv` via `python -B tasks.py --check-prerequisites <minigame_id>`. This checks the explicit `requisites` column against asset catalogs (`SFXs.csv`, `BGMs.csv`, `models_3D.csv`, `sprites_2D.csv`).
  - **Missing Asset Halt**: If ANY required visual (3D/2D) or audio (SFX/BGM) asset is missing or pending, the Orchestrator **halts engineer invocation** and explains which assets are missing. Withholding the engineer preserves quality (strict **Rule 10** compliance).
  - **Cleared Minigames**: When all required assets are `done` (or if no requisites are required), the Orchestrator injects concrete asset drawing calls (`draw_<name>_3d/2d`) and audio cue declarations (`SFXS`, `BGMS`) into the engineer prompt.

### 1.2 Script Sizing & Pedagogical Invariants
- **Minigame Scripts (Sections 3.0 to 3.7)**: Target **300 to 1,500 lines**. Minimum floor **300 lines**; hard ceiling **1,800 lines**.
- **Procedural Asset Modules (SFX, BGM, 3D Models, 2D Sprites)**: Target **200 to 800 lines**. Minimum floor **200 lines**; hard ceiling **1,000 lines**.
- **Guidance**: Limits are for token control. Never pad with artificial lines or strip comments to fit bounds. Clarity top-to-bottom wins over line count.
- **Pedagogical Invariants**: Simple beats clever (plain classes with explicit `__init__`, explicit loops, C++ equivalent mappings). Simultaneous Keyboard/Mouse + Gamepad parity. Safe HUD layout (`x = 450..980, y = 14..48` clear for settings bar). Clean reset on `[R]`/Start.

### 1.3 Lean 1+N Swarm Protocol
Batches of 1 to 8 files are executed via the **Lean 1+N Swarm Architecture**:
1. **Agent Topology**: Strictly **1 Lead Orchestrator + $N$ isolated Engineers ($N \le 8$)**.
   - **Lead Orchestrator (Depth 0)**: The primary session. Inspects tasks via `tasks.py`, verifies prerequisites, estimates compute, spawns engineers concurrently, and synchronizes status upon completion.
   - **Engineers (Depth 1)**: Isolated, specialized subagents defined in `.agents/`:
     - `.agents/audio_engineer.md` for SFX (`assets/audio/SFX/<category>/`) and BGM (`assets/audio/BGM/<vibe>/`).
     - `.agents/model_engineer.md` for 3D primitive models (`assets/models_3D/<category>/`).
     - `.agents/sprite_engineer.md` for 2D vector sprites (`assets/sprites_2D/<category>/`).
     - `.agents/minigame_engineer.md` for minigames (`minigames/3.x_*/`).
   - **Invocation Patterns**: The Orchestrator invokes engineers using `invoke_subagent(TypeName="self", Role="<Engineer Role>", Prompt=...)` or registers them via `define_subagent` using the system prompts in `.agents/*_engineer.md`.
2. **Deterministic Token & Compute Estimation**:
   - Before launching engineers, the Lead Orchestrator calculates and displays the estimated token usage and session budget percentage:
     $$\text{Estimate} = N_{\text{engineers}} \times (\text{Prompt Tokens} + \text{Output Tokens})$$
   - *Example*: 4 SFX $\approx 4 \times 2,500 = 10,000$ tokens (~1.0% compute across parallel Flash subagents).
   - This estimation is deterministic arithmetic—**never spawn an agent to estimate tokens**.
3. **Auxiliary Role Ban**:
   - Spawning Explorers, Interviewers, Reviewers, Challengers, Forensic Auditors, or Victory Auditors is **STRICTLY FORBIDDEN**.
4. **Zero Root Test Scripts Invariant**:
   - Engineers must NEVER write benchmark scripts, stress tests, or scratch files to the repository root (e.g. NEVER generate `tests_stress_*.py`).
   - Verification is self-contained: `python -B <target_file> --smoke-test` (assets) or `python -B audit_minigame.py <file>` (minigames).
5. **Engineer Execution & Strict 1-Retry Policy**:
   - Subagents run concurrently using `Model="flash"` (or `inherit`). Tool grants are restricted to `write_file`, `edit_file`, `read_file`, and `run_command`.
   - Subagents have AT MOST 1 retry to fix verification failures. On a second failure, they halt and report back.
   - Subagents reply with a concise 5-line summary message and terminate.
6. **Deterministic Orchestrator Wrap-Up**:
   - After engineers finish, the Orchestrator updates catalogs via `python -B tasks.py --sync-statuses` and verifies launcher discovery via `python -B launcher.py --smoke-test`.

### 1.4 Token-Saving Console Query Protocol
1. **Never read raw CSV files into agent context**: Do NOT call `read_file` on `.csv` files. Use headless `tasks.py` CLI:
   ```bash
   python -B tasks.py --list minigames --section 3.2 --status pending --limit 3
   python -B tasks.py --list SFXs --category combat --status pending --limit 4
   python -B tasks.py --get minigames mg_3201_mortar_arc
   python -B tasks.py --check-prerequisites mg_301_orbital_siege
   ```
2. **Direct Spec Injection**: The Orchestrator extracts target row specifications via `tasks.py --get` and embeds them directly into the engineer prompt (0 CSV tokens spent by engineers).
3. **Automated Status Sync**: Status is derived from disk presence (`pending` when absent, `done` when present) via `python -B tasks.py --sync-statuses`. Engineers never edit CSVs.

---

## 2. Core Repository Rules

### Rule 1: No Bytecode / Zero `__pycache__` Generation
- **NEVER** generate `__pycache__` directories.
- Always use `python -B` or set `$env:PYTHONDONTWRITEBYTECODE="1"`.
- Every script and package MUST enforce:
  ```python
  import sys
  sys.dont_write_bytecode = True
  ```

### Rule 2: Mandatory Import Order & Top-Bar Clearance
- Every minigame must import in this exact order:
  ```python
  from pyray import *
  from assets.asset_loader import *
  from utils import *
  ```
- Importing `from utils import *` enables the **Global Top-Bar Settings Dropdowns** (`Font`, `Font Size [Ctrl +/-]`, and `Window Size / Fullscreen [F11]`). Keep HUD elements clear of `x = 450..980, y = 14..48`.
- Every minigame must be directly executable from terminal (`python -B minigames/<subfolder>/<script_name>.py`) and discoverable via `launcher.py`.

### Rule 3: Mandatory 5-Block Pedagogical Anatomy
Every minigame script implements these 5 blocks (see `rules/minigames.md` for reference template):
- **Block 1: Header Docstring & Metadata**: Canonical script header (Title, Difficulty tier 1–5, Section 3.x, Pattern Category, Dimension 2D/3D, Problem Solved, Mathematical Concept, Dual Controls).
- **Block 2: Core Pattern Implementation**: Isolated, self-contained pattern classes and functions with novice-friendly comments and C++ mappings.
- **Block 3: World Simulation & Entities**: Concrete game entities, environment setup, and asset integration demonstrating the pattern in action.
- **Block 4: Telemetry & X-Ray Debug Overlay**: Visual telemetry panel and world-space debug inspector toggled via `[Tab]` / Gamepad `Y`, with live pattern toggle via `[F1]` / Gamepad `LB`.
- **Block 5: Main Game Loop & Automated Smoke Test**: Window setup, audio lifecycle, selective in-RAM audio loading via `SFXS = [...]` and `BGMS = [...]`, per-frame `self.sfx.update()`, 60 FPS update/draw loop, dual controller input polling, safe HUD layout, global settings dropdown bar (`draw_ui_settings_bar(450, 16)`), clean audio teardown (`self.sfx.unload_all()`), and non-blocking `--smoke-test` exit after 3 frames.

### Rule 4: Language-Agnostic & C++-Transferable Code (Zero "Pythonic Magic")
Simple beats clever. Python is used strictly as readable, executable pseudocode porting 1-to-1 to C++, C, C#, Rust, or Zig.
1. **NO Decorators**: No `@dataclass`, `@property`, `@staticmethod`, `@classmethod`, `@lru_cache`, or custom decorators. Use plain classes with explicit `__init__(self)` constructors initializing member variables line-by-line.
2. **NO Generators or Coroutines**: No `yield`, `async`/`await`, or `with` context managers for game logic. Use frame-by-frame `update(dt)` with explicit state variables (`self.state`, `self.timer`).
3. **NO Dunder / Magic Methods**: No `__call__`, `__getitem__`, `__getattr__`, or dynamic metaprogramming (`getattr`, `setattr`, `eval`, `*args`, `**kwargs`). Use explicit method names.
4. **NO Complex Comprehensions or Lambdas**: Write explicit `for` loops and `if/else` blocks. Never reallocate lists every frame; use pre-allocated pools with active flags or in-place index loops.
5. **Prefer Explicit Arrays & Indices**: Use simple fixed-capacity lists and integer counters mirroring `std::array<T, N>` or `std::vector<T>`.

### Rule 5: Mandatory X-Ray Overlay (`[Tab]`) & Pattern Comparison (`[F1]`)
1. **`[Tab]` X-Ray Overlay**: Every minigame renders real-time telemetry or world-space debug visualization (active vs. free pool slots, active FSM/BT node, spatial grid cells, trajectory vectors). Default ON in single-pattern labs.
2. **`[F1]` Live Pattern Toggle**: Allow pressing `[F1]` (or `1`/`2`/`3` / Gamepad `LB`) to toggle the pattern ON/OFF or tune parameters live so learners immediately feel the architectural difference.

### Rule 6: Mandatory Non-Blocking Verification & Strict 1-Retry Policy
- Never execute minigames or asset scripts from agent tool calls without `--smoke-test`.
- Minigames are verified via:
  ```bash
  python -B audit_minigame.py minigames/<subfolder>/<script_name>.py
  ```
- Assets are verified via:
  ```bash
  python -B <target_file> --smoke-test
  ```
- **Strict 1-Retry Policy**: If verification fails, the engineer is allowed **AT MOST ONE (1) retry fix**. If it fails a second time, immediately halt and report the error.

### Rule 7: Novice-Friendly Comments & Catalog Immutability during Builds
- Write clear, readable English comments explaining *why* equations work without academic jargon.
- Subagents do NOT edit rulebooks (`rules/*.md`) during builds. If a subagent invents a novel design pattern, it registers it in `rules/patterns.md`.

### Rule 8: Simultaneous Keyboard/Mouse & Gamepad Controls
Every minigame and the launcher MUST support Gamepad input simultaneously alongside Keyboard/Mouse using canonical helpers in `utils/gamepad_input.py`:
- **Movement**: `get_dual_move_2d()` (WASD/Arrows + Gamepad Left Stick + D-Pad, clamped magnitude $\le 1.0$).
- **Aiming**: `get_dual_look_2d()` (Q/E or Arrows + Gamepad Right Stick).
- **Primary Action**: `is_dual_primary_fire_pressed()` / `down()` (Left Mouse / Space + Gamepad RT / A).
- **Secondary Action**: `is_dual_secondary_fire_pressed()` / `down()` (Right Mouse / Shift + Gamepad LT / X).
- **Jump**: `is_dual_jump_pressed()` / `down()` (Space + Gamepad A).
- **Dash**: `is_dual_dash_pressed()` / `down()` (Left Shift + Gamepad B).
- **X-Ray Toggle**: `is_dual_xray_toggle_pressed()` (`[Tab]` / Gamepad Y).
- **Pattern Toggle**: `is_dual_pattern_toggle_pressed()` (`[F1]` / Gamepad LB).
- **Reset Simulation**: `is_dual_reset_pressed()` (`[R]` / Gamepad Start).
- **Status Badge**: Call `draw_gamepad_status_badge(985, 22, 11)` on top HUD bar.

### Rule 9: Catalog Classification & Launcher Dropdown Synchronization
- Header docstring must include `Difficulty : <1..5>` and `Section : <3.x Category>`.
- Task tracking is managed exclusively in `tasks/*.csv` by Orchestrator via `python -B tasks.py --sync-statuses`.
- Launcher discovery is verified via `python -B launcher.py --smoke-test`.

### Rule 10: Assets-Only Minigames (Zero Inlined or Fabricated Assets)
- Minigames MUST use ONLY procedural visual and audio assets that already exist in `assets/` (imported via `from assets.asset_loader import *`).
- Asset dependencies are declared explicitly in `tasks/minigames.csv` (`requisites` column).
- Orchestrator verifies prerequisites before invoking engineer (`python -B tasks.py --check-prerequisites <id>`).
- If any required asset is missing or pending, engineer invocation is halted.
- Minigames must NEVER inline procedural audio synthesis, sound wave generators, or draw ad-hoc entity models. Declare audio cues in `SFXS = [...]` and `BGMS = [...]` for selective in-RAM loading.

---

## 3. `pyray` (CFFI) Gotchas Cheat Sheet

1. **Cast 2D Coordinates to `int` for Non-Vector Draw Calls**:
   `draw_text`, `draw_rectangle`, `draw_rectangle_lines`, `draw_circle`, and `draw_line` expect C integers. Passing floats raises `TypeError: incompatible types`. Wrap with `int(x)` or use vector variants (`draw_circle_v`, `draw_line_ex`).
2. **Clamp & Cast `Color(r, g, b, a)` Channels to `int` in `0..255`**:
   Dynamic alpha or color math producing floats or out-of-range values crashes CFFI. Always use `Color(r, g, b, max(0, min(255, int(alpha))))`.
3. **Do Not Use `+`, `-`, or `*` Directly on `Vector2` / `Vector3`**:
   `pyray` CFFI structs do not reliably support Python arithmetic operators. Access `.x`, `.y`, `.z` directly or use helpers in `utils/math_helpers.py` (`lerp_v2`, `damp_v2`, `distance_2d`).
4. **3D Mode vs. 2D Overlay Separation**:
   In 3D minigames, all 3D draw calls must be inside `begin_mode_3d(camera)` ... `end_mode_3d()`. All 2D text and HUD calls must be placed after `end_mode_3d()`.

---

## 4. Directory Map & Component Index

```
./
├── AGENTS.md                  <-- Agent operating rules & Lean 1+N Swarm protocol
├── README.md                  <-- Project overview & getting started
├── audit_minigame.py          <-- AST & smoke test gatekeeper for minigames
├── config.json                <-- Persisted UI preferences (font, font size, window size)
├── launcher.py                <-- Interactive Pattern Encyclopedia & Minigame Hub
├── tasks.py                   <-- Headless CLI & interactive task spreadsheet editor
├── .agents/                   <-- Specialized subagent profiles
│   ├── audio_engineer.md      <-- Procedural SFX and BGM synthesizer engineer
│   ├── model_engineer.md      <-- 3D procedural primitive model engineer
│   ├── sprite_engineer.md     <-- 2D procedural vector sprite engineer
│   └── minigame_engineer.md   <-- Educational minigame & pattern lab engineer
├── rules/                     <-- Human-readable architectural guidelines & catalogs
│   ├── patterns.md            <-- Catalog of 2D & 3D game design patterns
│   ├── minigames.md           <-- Reference catalog of minigames
│   ├── assets.md              <-- Router index for procedural assets
│   ├── audio.md               <-- Procedural audio guidelines
│   ├── models_3D.md           <-- Procedural 3D primitive models guidelines
│   ├── sprites_2D.md          <-- Procedural 2D vector sprites guidelines
│   └── utils.md               <-- Utilities catalog (collisions, grids, AI, math, UI)
├── tasks/                     <-- Tracking spreadsheets (minigames, SFXs, BGMs, models_3D, sprites_2D)
├── assets/                    <-- Reusable procedural visual and audio assets
│   ├── asset_loader.py        <-- Central dynamic loader & dictionary registries
│   ├── asset_viewer.py        <-- Interactive 4-tab procedural workbench & viewer
│   ├── models_3D/             <-- 3D procedural primitive models (categorized subfolders)
│   ├── sprites_2D/            <-- 2D procedural vector sprites (categorized subfolders)
│   └── audio/                 <-- In-memory SFX and BGM synthesizers
├── utils/                     <-- Non-native utilities (collisions, grids, AI pursuit, math, UI, gamepad)
└── minigames/                 <-- Categorized single-file minigames & pattern labs (3.0 to 3.7)
```
