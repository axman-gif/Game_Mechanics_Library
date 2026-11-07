# Agent Operating Instructions & Repository Context Hub (AGENTS.md)

Welcome, Agent. This repository is an **interactive encyclopedia of video game design patterns** built with **Raylib in Python (`pyray`)**.

The graphics and audio are intentionally built using **procedural primitives** (2D and 3D geometric shapes like spheres, cubes, cylinders, and rectangular prisms) and **in-memory audio synthesis** to emphasize architectural clarity, mathematical elegance, and hands-on pattern learning over external art assets.

---

## 1. Mandatory Step 0: Pre-Flight Check & Scope Control

**CRITICAL RULE**: Before generating code or planning a new minigame/asset/feature, you **MUST** review the existing components in the workspace:

1. **Check Existing Minigames & Catalog Taxonomy**: Review [`rules/minigames.md`](rules/minigames.md) for architectural guidelines and [`tasks/minigames.csv`](tasks/minigames.csv) for task status:
   - **Section 3.0: Core Multi-Pattern Prototypes** (combining 4+ patterns: Orbital Siege 2D, Titan Strider 3D, Tactical Commander TBS, Frontline Outpost RTS).
   - **Sections 3.1–3.7: Extended Single-Pattern Labs** (focused on 1 pattern in isolation):
     - `3.1 Menus & UI`
     - `3.2 Combat & Weapons`
     - `3.3 Enemies & AI`
     - `3.4 Progression & Economy`
     - `3.5 World & Exploration`
     - `3.6 Movement & Camera`
     - `3.7 Puzzle, Stealth & Other`
2. **Check Existing Visual & Audio Assets**: Consult the decomposed asset guidelines and tracking spreadsheets in `tasks/` (saving tokens by querying exclusively via `tasks.py --list`; never read raw CSV files into context):
   - [`rules/audio.md`](rules/audio.md), [`tasks/SFXs.csv`](tasks/SFXs.csv), & [`tasks/BGMs.csv`](tasks/BGMs.csv): For procedural sound effects (`assets/audio/SFX/<category>/<name>.py`) and background music tracks (`assets/audio/BGM/<vibe>/<name>.py`).
   - [`assets/audio/synth_sfx.py`](assets/audio/synth_sfx.py): Central dynamic audio discovery registry (`SFX_REGISTRY`, `BGM_REGISTRY`) and selective in-RAM loader (`SoundLibrary`).
   - [`rules/minigames.md`](rules/minigames.md) Section 3.5: Authoritative guide for minigame audio imports, selective in-RAM loading via `SFXS = [...]` and `BGMS = [...]`, per-frame `sfx.update()`, and clean teardown.
   - [`rules/models_3D.md`](rules/models_3D.md) & [`tasks/models_3D.csv`](tasks/models_3D.csv): For 3D procedural primitive models (`assets/models_3D/`).
   - [`rules/sprites_2D.md`](rules/sprites_2D.md) & [`tasks/sprites_2D.csv`](tasks/sprites_2D.csv): For 2D procedural primitive sprites (`assets/sprites_2D/`).
   - [`rules/assets.md`](rules/assets.md): Top-level router index and quick-import reference.  
   **NEVER rewrite or duplicate existing assets.**
3. **Interactive Tasks Editor (`tasks.py`)**: All tracking spreadsheets in `tasks/` are visually inspected, edited, and maintained via `python -B tasks.py`. Humans should always use `tasks.py` rather than LibreOffice Calc or Microsoft Excel to prevent file corruption and schema breakage.
4. **Check Existing Utilities & Math**: Review [`rules/utils.md`](rules/utils.md) to reuse non-native collision routines (rotated 3D/2D capsules, SAT OBB), spatial hash grids (`SpatialGrid2D`/`3D`), AI pursuit/pathfinding algorithms (A*, BFS, seek, lead intercept), math dampening/shake tools, and the global UI/Font/Window manager (`utils/ui_settings.py`). **NEVER rewrite these utilities** (unless a single-pattern lab is specifically teaching that algorithm, in which case expose its step-by-step state visually).
5. **Reference Game Design Patterns & Creative Autonomy**: Consult [`rules/patterns.md`](rules/patterns.md) to document and explain demonstrated design patterns. **Creative Autonomy Rule**: Subagents are **not** restricted to existing patterns in [`rules/patterns.md`](rules/patterns.md)—they are encouraged to invent or adapt novel game design patterns and register them into [`rules/patterns.md`](rules/patterns.md).

### 1.1 Ambiguity Gate & Mandatory Specification Check
Before writing or modifying any code, the agent **MUST** evaluate the clarity, target section, and scope of the prompt:
- **Standard Single-Turn Request (without `/teamwork`)**:
  - The user must explicitly request **strictly 1 prototype or asset** by specifying either its name or category.
  - **Multi-File Halt**: If the user requests $\ge 2$ files in a single prompt without `/teamwork`, **THE AGENT MUST STOP IMMEDIATELY WITHOUT TOUCHING OR CREATING ANY CODE.** The agent must reply:
    > *"I detected a request for multiple files. To maintain pedagogical quality, prevent context dilution, and ensure role-specialized subagent execution, multi-file requests must use the `/teamwork` command (e.g. `/teamwork build 3 games from section 3.2 and 2 from section 3.3` or `/teamwork create 4 combat weapon SFX`). For standard single-turn prompts, please request strictly 1 item."*
  - **Ambiguity Halt**: If the request is generic or open-ended, halt immediately and ask the user to clarify.
- **Autonomous Multi-Script Sessions (with `/teamwork`)**:
  - Multi-script batching is permitted for **up to 8 files per session**.
  - **Oversized Batch Halt**: If the user requests $> 8$ files in a single `/teamwork` session, **THE AGENT MUST STOP IMMEDIATELY WITHOUT TOUCHING OR CREATING ANY CODE**, and ask the user to break the request into batches of at most 8 files.
  - **Automatic Directory & Catalog Inference**: The user does **not** need to type folder paths or `.md` filenames. The orchestrator automatically routes:
    - Sound Effects (SFX) $\rightarrow$ default `assets/audio/SFX/<category>/` via `rules/audio.md`
    - Background Music (BGM) $\rightarrow$ default `assets/audio/BGM/<vibe>/` via `rules/audio.md`
    - 3D Models $\rightarrow$ default `assets/models_3D/` via `rules/models_3D.md`
    - 2D Sprites $\rightarrow$ default `assets/sprites_2D/` via `rules/sprites_2D.md`
    - Minigames $\rightarrow$ default `minigames/3.x_<category>/` via `rules/minigames.md`
  - **Educational Ambiguity Refusal**: If a `/teamwork` request is ambiguous or underspecified (e.g. "make some games", "build 4 things", "work on sound"), **THE AGENT MUST STOP IMMEDIATELY WITHOUT TOUCHING OR CREATING ANY CODE** and output the Educational Specificity Reply:
    > *"In this repository, every minigame, BGM soundtrack, SFX synthesizer, 3D model, and 2D sprite is designed as a standalone, modular, and reusable building block with zero external dependencies and strict C++ transferability.*  
    > *To execute this task with dedicated parallel subagents while preventing duplicate files or context drift, please specify the exact number of files (up to 8) and target categories or prototype concepts. You do not need to provide paths or doc names—the orchestrator will automatically infer them:*  
    > *- Minigames: `/teamwork build 3 minigames from Section 3.2 and 2 from Section 3.3` or `/teamwork build 2 minigames: Micro-Inventory Grid and Socket Workbench`*  
    > *- SFX: `/teamwork create 4 SFX for combat weapons` (auto-targets `assets/audio/SFX/<category>/` via `rules/audio.md`)*  
    > *- BGM: `/teamwork compose 2 BGM tracks for dungeon and stealth` (auto-targets `assets/audio/BGM/<vibe>/` via `rules/audio.md`)*  
    > *- 3D Models: `/teamwork create 2 3D models for vehicles and mechs` (auto-targets `assets/models_3D/` via `rules/models_3D.md`)*  
    > *- 2D Sprites: `/teamwork create 3 2D sprites for top-down enemies` (auto-targets `assets/sprites_2D/` via `rules/sprites_2D.md`)*  
    > *- Mixed Batches: `/teamwork build 2 combat minigames and 3 weapon SFX` or `/teamwork create 3 SFX, 2 BGM, and 2 2D sprites`"*

### 1.2 Script Sizing, Readability Criterion & Pedagogical Invariants
To maximize token economy, eliminate bloat, maintain deep architectural pedagogy, and ensure zero runtime defects:
- **Strict Size Limits for Minigames (Sections 3.0 to 3.7)**:
  - **Target Range**: **300 to 1,500 lines** per minigame script.
  - **Floor**: **300 lines minimum**. (Prevents cutting corners on comments, 5-block anatomy, dual input, and X-Ray overlays).
  - **Hard Ceiling**: **1,800 lines maximum**. Under NO circumstances may any minigame script exceed 1,800 lines (prevents token bloat).
- **Strict Size Limits for Procedural Assets (SFX, BGM, 3D Models, 2D Sprites)**:
  - **Target Range**: **200 to 800 lines** per procedural asset module.
  - **Floor**: **200 lines minimum**. (Ensures complete mathematical primitives, animation loops, color palettes, and pedagogical C++ mapping comments).
  - **Hard Ceiling**: **1,000 lines maximum**. Under NO circumstances may any procedural asset module exceed 1,000 lines (preserves subagent token budgets).
- **Token Control & Line Limit Guidance**:
  - Line limits are guidance for token control. **NEVER** pad a file with artificial lines or redundant comments just to reach the floor. **NEVER** compress code, truncate functions, or drop comments to fit under the ceiling.
- **Readability Criterion (Clarity Wins over Line Count)**:
  - A file must be completely understandable reading top to bottom, without jumping back and forth to other files. Pedagogical clarity and self-contained understanding always win over strict line count.
- **Pedagogical Quality Invariants (Non-Negotiable within Line Budget)**:
  - **Simple beats clever**: Python is executable pseudocode that ports 1-to-1 to C++, C, C#, Rust, or Zig (plain classes with `__init__`, explicit loops, no decorators, no generators, no lambdas, no magic dunders).
  - Every script MUST provide:
    1. Novice-friendly comments explaining *why* equations work in plain language without academic jargon, alongside direct C++ equivalent mappings (memory layout, explicit indices, struct fields).
    2. Complete structure (5-block anatomy for minigames; canonical procedural drawing/synthesis interfaces for assets).
    3. Complete simultaneous Keyboard/Mouse + Gamepad parity for minigames (no mouse-only or key-only actions).
    4. Safe HUD layout (keeping `x = 450..980, y = 14..48` clear for the global dropdown bar).
    5. Full state reset on `[R]` / Gamepad Start, zero CFFI type casting errors, and clamped Color channels (`0..255`).

### 1.3 Batch Size & Autonomous Parallel Swarm Protocol (`/teamwork`)
To eliminate context dilution, prevent degradation in code depth, avoid attention drift across long sessions, and maximize throughput, the repository adopts the **Parallel Isolated Craftsman Swarm**:
- **Standard Single-Turn Request**: Build strictly **1 prototype or asset per prompt/cycle**. Complete the file, run verification, report to user, and halt.
- **Autonomous Multi-Script Sessions (`/teamwork`, Up to 8 Files)**:
  When invoked via `/teamwork` for $N$ files ($1 \le N \le 8$, e.g., `/teamwork create 3 SFX, 2 BGM, and 2 2D sprites` or `/teamwork build 3 minigames from Section 3.2`), the Lead Orchestrator and subagents follow the **Parallel Swarm Protocol**:
  1. **Lead Orchestrator Queue & Invariant Checks**:
     - The Orchestrator validates the total batch count $N \le 8$.
     - **Strict Task Uniqueness Invariant**: Under NO circumstances may more than one subagent take the same task or generate the same file ($Agent_i \leftrightarrow TargetFile_i$).
     - Automatically routes targets to their canonical directories (`minigames/3.x_*`, `assets/audio/SFX/<category>/`, `assets/audio/BGM/<vibe>/`, `assets/models_3D/`, `assets/sprites_2D/`) without requiring manual paths from the user.
     - **Exclusive Task Lifecycle**: The Orchestrator sets task status from `pending` to `in_progress` via `python -B tasks.py --set-status <catalog> <task_id> in_progress` when assigning to a subagent.
  2. **Concurrent Spawning of $N$ Isolated Subagents (0-Token Context)**:
     - The Orchestrator issues $N$ concurrent `invoke_subagent` calls in a single turn.
     - **Decoupled Orchestration**: The Orchestrator does not micromanage internal code details. It equips each subagent with:
       - Dedicated target file path in its canonical default directory.
       - Clean requirements extracted via `tasks.py --get` from the tracking catalog.
       - Applicable design pattern references.
       - Pedagogical invariants (C++ transferability, 5-block anatomy, line counts, pyray CFFI gotchas).
     - **Zero In-Chat Code Spillage**: Each subagent writes code directly to disk via file writing tools. Subagents do NOT print large source files into chat text.
     - **Non-Blocking Verification**: Each subagent verifies its own file directly (e.g. `$env:PYTHONDONTWRITEBYTECODE="1"; python -B audit_minigame.py minigames/<subfolder>/<script_name>.py` or the appropriate `--smoke-test`).
     - **Strict 1-Retry Policy**: If verification fails, the subagent performs at most one (1) retry fix. If it fails a second time, it halts and reports the failure.
     - **Concise Completion Report**: Each subagent sends a 5-line summary message back to the Orchestrator (File path, Line count, Demonstrated patterns, Audit status) and terminates. Craftsmen NEVER edit CSV files or `assets/__init__.py`.
  3. **Creative Pattern Discovery & Registration**:
     - Subagents have full creative freedom to introduce novel design patterns. When a subagent creates a new pattern, it documents its mathematical and architectural rationale and registers it in [`rules/patterns.md`](rules/patterns.md).
  4. **Documentation & Release Synchronization**:
     - Upon receiving completion reports from all parallel subagents, the Orchestrator:
       - Updates task status in `tasks/minigames.csv`, `tasks/SFXs.csv`, `tasks/BGMs.csv`, `tasks/models_3D.csv`, or `tasks/sprites_2D.csv` from `in_progress` to `built` exclusively via `python -B tasks.py --set-status <catalog> <id> built`.
       - Registers any newly built procedural assets in `assets/__init__.py` (Orchestrator ONLY).
       - Updates [`rules/patterns.md`](rules/patterns.md) if any subagents introduced new design patterns (no other `rules/*.md` files require editing during builds).
       - Runs `python -B launcher.py --smoke-test` to verify launcher dropdown synchronization across all categories.
       - Reports a consolidated summary table of all built files to the user.
  5. **Autonomous Non-Intervention Guarantee**: As long as the request specifies target file counts and categories clearly, the Orchestrator executes the entire parallel swarm pipeline autonomously without pausing to ask conversational questions between files.
- **Focused Lab Scope**: Single-pattern labs must start **immediately in the interactive gameplay/sandbox state** (skip title screens unless the pattern itself is a menu/scene-stack pattern) so 100% of the code focuses on experiencing and inspecting the target pattern.

### 1.4 Token-Saving Console Query Protocol (Orchestrator & Craftsmen)
To prevent context dilution and avoid blowing token budgets when inspecting large tracking catalogs:
1. **Never read raw CSV files into agent context**:
   Under **NO** circumstances may either the Lead Orchestrator or Craftsmen subagents call `view_file` or read raw `.csv` files into context. Reading full CSV files burns 4,000 to 8,000 tokens per turn and causes context overflow. All catalog queries must go through the headless `tasks.py` CLI.
2. **Lead Orchestrator Fast CLI Queries (<50 tokens)**:
   The Orchestrator queries pending tasks using the headless `tasks.py` CLI:
   ```bash
   # Query next pending minigames in a specific section
   python -B tasks.py --list minigames --section 3.2 --status pending --limit 3

   # Query next pending minigames across all sections (fallback to pending row order)
   python -B tasks.py --list minigames --status pending --limit 3

   # Query next pending audio assets by type (SFX or BGM)
   python -B tasks.py --list SFXs --category combat --status pending --limit 3
   python -B tasks.py --list BGMs --vibe energetic --status pending --limit 2

   # Query next pending audio assets across all categories/vibes
   python -B tasks.py --list SFXs --status pending --limit 4
   python -B tasks.py --list BGMs --status pending --limit 4

   # Query next pending 3D models or 2D sprites
   python -B tasks.py --list models_3D --status pending --limit 2
   python -B tasks.py --list sprites_2D --status pending --limit 2

   # Query full specifications of a specific task
   python -B tasks.py --get minigames mg_3201_mortar_arc
   python -B tasks.py --get SFXs sfx_combat_laser
   python -B tasks.py --get BGMs bgm_synth_pulse
   ```
3. **Direct Spec Injection to Craftsmen (0 CSV tokens spent by Craftsmen)**:
   When spawning a craftsman via `invoke_subagent`, the Orchestrator extracts the target row's fields (`target_file`, `title`, `dimension`, `patterns`, `description`) via `tasks.py --get` and embeds them directly into the prompt. Craftsmen subagents NEVER need to read or parse CSV files.
4. **Exclusive CSV Task Lifecycle (pending -> in_progress -> built)**:
   Task status transitions follow a strict lifecycle managed **exclusively by the Lead Orchestrator** using `tasks.py`:
   - `pending` $\rightarrow$ Default initial state in tracking catalogs.
   - `in_progress` $\rightarrow$ Set by Orchestrator upon dispatching subagents (`python -B tasks.py --set-status <catalog> <task_id> in_progress`).
   - `built` $\rightarrow$ Set by Orchestrator upon subagent verification (`python -B tasks.py --set-status <catalog> <task_id> built`).
   - **Craftsmen subagents MUST NEVER edit CSV files or execute `--set-status`**. Only the Orchestrator modifies task status and registers assets in `assets/__init__.py`.
5. **Collision Prevention Check**:
   Before creating a procedural asset, the Orchestrator or subagent checks if a function or concept name is already registered:
   ```bash
   python -B tasks.py --check SFXs create_laser_sound
   python -B tasks.py --check BGMs synth_pulse
   ```

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
- Every minigame inside `minigames/` must be a **single, self-contained Python script** located inside its designated 3.x category subfolder.
- In **EVERY** script, you **MUST** import in this exact order:
  ```python
  from pyray import *
  from assets import *
  from utils import *
  ```
- Importing `from utils import *` after `from pyray import *` automatically enables the repository's **Global Top-Bar Settings Dropdowns** (`Font`, `Font Size [Ctrl +/-]`, and `Window Size / Fullscreen [F11]`) backed by `config.json`. Keep the top-bar region `x = 450..980, y = 14..48` free of HUD text so the dropdown bar (`draw_ui_settings_bar(450, 16)`) never overlaps your HUD.
- Every minigame must be directly executable from the terminal (`python -B minigames/<subfolder>/<script_name>.py`) and discoverable via the root [`launcher.py`](launcher.py).

### Rule 3: Mandatory 5-Block Pedagogical Anatomy (Single Authoritative Template)
Every minigame script in `minigames/` must follow the standardized **5-Block Pedagogical Anatomy**.
The **single authoritative template** for minigames is defined in [`rules/minigames.md`](rules/minigames.md). All minigames implement these 5 blocks:
- **Block 1: Header Docstring & Metadata**: Canonical script header specifying Title, Section (e.g. `3.2`), Pattern Category, Dimension (`2D` or `3D`), Problem Solved, Mathematical/Algorithmic Concept, and Dual Controls summary.
- **Block 2: Core Pattern Implementation**: Isolated, self-contained pattern classes and functions with novice-friendly comments explaining mathematical rationale and direct C++ mapping (struct fields, fixed-size arrays, explicit indices).
- **Block 3: World Simulation & Entities**: Concrete game entities, environment setup, and asset integration demonstrating the pattern in action.
- **Block 4: Telemetry & X-Ray Debug Overlay**: Visual telemetry panel and world-space debug inspector toggled via `[Tab]` / Gamepad `Y` (`Triangle`), with live pattern parameter/behavior toggle via `[F1]` / Gamepad `LB` (`L1`).
- **Block 5: Main Game Loop & Automated Smoke Test**: Window initialization, audio device lifecycle, selective in-RAM audio loading via `SFXS` & `BGMS` lists (`self.sfx.load(sfx=SFXS, bgm=BGMS)`), per-frame `self.sfx.update()`, 60 FPS update/draw loop, dual controller input polling, safe HUD layout, global settings dropdown bar (`draw_ui_settings_bar(450, 16)`), clean audio teardown (`self.sfx.unload_all()`), and non-blocking `--smoke-test` exit after 3 frames.

*(Consult [`rules/minigames.md`](rules/minigames.md) for the complete reference code template).*

### Rule 4: Language-Agnostic & C++-Transferable Code (Zero "Pythonic Magic")
This repository exists for **learning and inspiration**: **simple beats clever**. Python is used strictly as **readable, executable pseudocode**. Learners study this code to understand data structures and algorithms and port them 1-to-1 to **C++, C, C#, Rust, or Zig**. Comments must explain *WHY* equations work in simple words without academic jargon.

You **MUST** write code that translates 1-to-1 to C++:
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
  - **Line Cap Preservation**: The corrected minigame script MUST STILL remain strictly under the **1,800-line hard ceiling** (and target the 300–1,500 line range, with a 300-line minimum). Corrected procedural asset modules MUST remain strictly under the **1,000-line hard ceiling** (and target the 200–800 line range, with a 200-line minimum). Limits are guidance for token control: never pad code to reach the floor, never compress code to fit the ceiling, and readability top-to-bottom wins over line count.
  - **Terminal Stop on Second Failure**: If the script still fails after the single retry attempt, the agent **MUST STOP IMMEDIATELY**, log the exact error and line numbers to the user, and request human guidance rather than attempting further automated loops.

### Rule 7: Novice-Friendly Comments & Catalog Immutability during Builds
- All code, comments, and markdown documents must be written in **clear, readable English** explaining *why* equations work in simple words without academic jargon (e.g., shortest segment distance, Reynolds steering, DDA raycast, spring damping) and brief notes on how data structures map to C++.
- **Rules Catalog Immutability during Asset/Minigame Creation**:
  - Subagents do **NOT** edit rulebooks (`rules/minigames.md`, `rules/audio.md`, `rules/models_3D.md`, `rules/sprites_2D.md`, `rules/utils.md`, or `rules/assets.md`) when creating minigames or assets.
  - All task tracking is managed exclusively in `tasks/*.csv` by the Lead Orchestrator via `tasks.py`.
- **Exception for Novel Patterns**:
  - If and only if a subagent invents or adapts a novel design pattern, it must register and document the new pattern in [`rules/patterns.md`](rules/patterns.md).

### Rule 8: Simultaneous Keyboard/Mouse & Gamepad Controls (Canonical Mapping)
- Every minigame and the launcher **MUST** support **Gamepad (Controller) input** that activates automatically whenever a connected controller is detected (`is_gamepad_available`) and works **simultaneously** alongside **Keyboard & Mouse** (either one, the other, or both at the same time — never locking out Keyboard/Mouse when a controller is plugged in).
- Always reuse the canonical helpers in [`utils/gamepad_input.py`](utils/gamepad_input.py) (exported via `from utils import *`) adhering to the Canonical Controls Table in [`rules/utils.md`](rules/utils.md):
  - **2D / 3D Movement**: `get_dual_move_2d()` (combines `WASD` / `Arrow Keys` + `Gamepad Left Stick` with radial deadzone + `D-Pad`, clamping combined magnitude to `<= 1.0` so using both devices never doubles player speed).
  - **Aiming / Camera Look**: `get_dual_look_2d()` (combines `Q`/`E` or `Left`/`Right` keys + `Gamepad Right Stick` with radial deadzone). For cursor/reticle aiming in 2D, allow the Mouse cursor when moved and smoothly steer with the Gamepad Right Stick when deflected.
  - **Primary Action / Fire**: `is_dual_primary_fire_pressed()` / `down()` (`Left Mouse` / `Space` + Gamepad `RT` / `A`).
  - **Secondary Action / Alt Fire**: `is_dual_secondary_fire_pressed()` / `down()` (`Right Mouse` / `Shift` + Gamepad `LT` / `X`).
  - **Jump**: `is_dual_jump_pressed()` / `down()` (`Space` + Gamepad `A`).
  - **Dash / Evade**: `is_dual_dash_pressed()` / `down()` (`Left Shift` + Gamepad `B`).
  - **X-Ray Overlay Toggle**: `is_dual_xray_toggle_pressed()` (`[Tab]` / Gamepad `Y` (`Triangle`)).
  - **Pattern Toggle**: `is_dual_pattern_toggle_pressed()` (`[F1]` / Gamepad `LB` (`L1`)).
  - **Secondary Pattern Toggle**: `is_dual_secondary_toggle_pressed()` (`[F2]` / Gamepad `RB` (`R1`)).
  - **Reset Simulation**: `is_dual_reset_pressed()` (`[R]` / Gamepad `Start`).
  - **HUD Status Badge**: Call `draw_gamepad_status_badge(985, 22, 11)` on the top HUD bar so the learner can see live controller detection (`PAD: ON [KB/M + Pad]` vs. `PAD: OFF [KB/M Only]`).

### Rule 9: Catalog Classification & Launcher Dropdown Synchronization
Every minigame script MUST be classified under its designated section (`3.0` or `3.1` through `3.7`):
1. **Docstring Section Tag**: Declare `Section          : <3.x Category>` in the script header docstring so `launcher.py`'s AST parser assigns it to the corresponding 3.x dropdown menu filter automatically.
2. **Task Tracking via `tasks/minigames.csv`**:
   - Task completion is tracked exclusively in `tasks/minigames.csv` by the Lead Orchestrator using `python -B tasks.py --set-status minigames <target_file_or_id> built`.
   - `rules/minigames.md` is a reference catalog and does NOT need manual edits when building minigames.
3. **Pattern Reference**:
   - Reference existing patterns from [`rules/patterns.md`](rules/patterns.md). If a novel pattern was created, register it in [`rules/patterns.md`](rules/patterns.md).
4. **Verification**:
   - Craftsman runs `python -B audit_minigame.py minigames/<subfolder>/<script_name>.py`.
   - Orchestrator verifies launcher dropdown discovery during release synchronization via `python -B launcher.py --smoke-test`.

### Rule 10: Assets-Only Minigames (Zero Inlined or Fabricated Assets)
- Minigames MUST use ONLY procedural visual and audio assets that already exist and are registered in `assets/` (imported via `from assets import *`).
- **Missing Asset Halt**: If a minigame specification or design requires an asset (3D model, 2D sprite, SFX synthesizer, or BGM track) that does NOT already exist in `assets/`, the agent **MUST STOP IMMEDIATELY WITHOUT TOUCHING OR CREATING ANY CODE**.
- The agent must report the missing asset dependencies back to the user or orchestrator so the assets can be built first (or scheduled in a `/teamwork` batch before the minigame).
- Minigames must **NEVER** inline procedural asset synthesis, define local sound wave generators, or draw ad-hoc complex entity models that belong in the modular asset catalog.
- **Selective Audio In-RAM Loading**: Minigames declare strictly the required cues in module-level `SFXS = [...]` and `BGMS = [...]` lists, passing them to `SoundLibrary` to compile into RAM only what is needed (see `rules/minigames.md` Section 3.5).

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
├── AGENTS.md                  <-- You are here (Agent rules, parallel swarm & pyray gotchas)
├── README.md                  <-- Beginner onboarding & usage instructions
├── audit_minigame.py          <-- AST & smoke test gatekeeper for minigames
├── config.json                <-- Persisted UI preferences (font, font size, window size)
├── launcher.py                <-- Interactive Pattern Encyclopedia & Minigame Hub
├── tasks.py                   <-- Interactive Task Catalog & Spreadsheet Editor (Raylib GUI)
├── rules/                     <-- Architectural guidelines, catalogs & patterns
│   ├── patterns.md            <-- Exhaustive catalog of 2D & 3D game design patterns
│   ├── minigames.md           <-- Registry and status of all standalone minigames
│   ├── assets.md              <-- Top-level router index for procedural assets
│   ├── audio.md               <-- Procedural audio registry (SFX, BGM, workstation)
│   ├── models_3D.md           <-- Procedural 3D primitive models registry
│   ├── sprites_2D.md          <-- Procedural 2D primitive sprites registry
│   └── utils.md               <-- Registry of collisions, spatial grids, AI, math & UI
│
├── tasks/                     <-- Dedicated task catalogs & progress spreadsheets
│   ├── minigames.csv          <-- 106 planned prototypes across sections 3.0 to 3.7
│   ├── SFXs.csv               <-- 73 procedural SFX synthesizers across 6 categories
│   ├── BGMs.csv               <-- 18 algorithmic BGM tracks across 12 emotional vibes
│   ├── models_3D.csv          <-- 29 3D procedural primitive models
│   └── sprites_2D.csv         <-- 29 2D procedural vector sprites
│
├── assets/                    <-- Reusable procedural visual and audio assets
│   ├── __init__.py            <-- Central asset loader, SoundLibrary & catalog exporter
│   ├── models_3D/             <-- 3D procedural primitive models (.gitkeep)
│   ├── sprites_2D/            <-- 2D procedural vector sprites (.gitkeep)
│   └── audio/                 <-- Procedural in-memory SFX and BGM synthesizers
│       ├── synth_sfx.py       <-- Central dynamic audio discovery registry & selective in-RAM SoundLibrary
│       ├── SFX/               <-- Dedicated modular sound effect synthesizers by category
│       │   ├── combat/        <-- Combat and weapon SFX (.gitkeep)
│       │   ├── creature/      <-- Creature SFX (.gitkeep)
│       │   ├── environment/   <-- Environmental SFX (.gitkeep)
│       │   ├── movement/      <-- Movement and locomotion SFX (.gitkeep)
│       │   ├── progression/   <-- Progression, loot, and UI SFX (.gitkeep)
│       │   └── ui_hud/        <-- UI and HUD feedback SFX (.gitkeep)
│       └── BGM/               <-- Algorithmic background music tracks by emotional vibe
│           ├── calm/          <-- Calm, ambient traversal (.gitkeep)
│           ├── cheerful/      <-- Cheerful tavern, festive (.gitkeep)
│           ├── curious/       <-- Curious puzzle, inquisitive (.gitkeep)
│           ├── eerie/         <-- Eerie dungeon, catacombs (.gitkeep)
│           ├── energetic/     <-- Energetic action, racing, synth pulse (.gitkeep)
│           ├── futuristic/    <-- Futuristic cyberpunk synth (.gitkeep)
│           ├── industrial/    <-- Industrial shipyard, machinery (.gitkeep)
│           ├── intense/       <-- Intense boss, siege dreadnought (.gitkeep)
│           ├── mystical/      <-- Mystical cosmic wonder (.gitkeep)
│           ├── nostalgic/     <-- Nostalgic chiptune, retro arcade (.gitkeep)
│           ├── suspenseful/   <-- Suspenseful stealth, espionage (.gitkeep)
│           └── triumphant/    <-- Triumphant victory fanfare (.gitkeep)
│
├── utils/                     <-- Reusable non-native utilities
│   ├── __init__.py            <-- Central utility exporter & UI manager
│   ├── collisions.py          <-- Rotated capsule 3D/2D, SAT OBB, segment projections
│   ├── spatial_grid.py        <-- 2D & 3D spatial hash grids, 2D tile navigation grid
│   ├── ai_pursuit.py          <-- Steering (Seek, Lead Intercept, Wander), A* & BFS pathfinding, LOS
│   ├── math_helpers.py        <-- Lerp, damp, approach, easing curves, Trauma screen shake
│   ├── ui_settings.py         <-- Global Font, Font Size (Ctrl+/-), Window (F11) & config.json manager
│   └── gamepad_input.py       <-- Simultaneous Keyboard/Mouse + Gamepad hot-plug & radial deadzone
│
└── minigames/                 <-- Categorized single-file minigames & pattern labs
    ├── 3.0_core_prototypes/   <-- Full multi-pattern prototypes (.gitkeep)
    ├── 3.1_menus_ui/          <-- Tactile UI and inventory labs (.gitkeep)
    ├── 3.2_combat_weapons/    <-- Combat mechanics (Hitscan, Ballistics, Recoil, Ammo, Parry) (.gitkeep)
    ├── 3.3_enemies_ai/        <-- AI patterns (Patrols, Alert FSM, Flow Fields, Boss Phases) (.gitkeep)
    ├── 3.4_progression_economy/<-- RPG loops (Loot tables, Crafting, XP curves, Shops) (.gitkeep)
    ├── 3.5_world_procgen/     <-- Procedural generation (Voxel chunks, Caves, BSP Dungeons) (.gitkeep)
    ├── 3.6_movement_camera/   <-- Kinematic movement feel (Coyote time, Jump buffer, Dash, Grapple) (.gitkeep)
    └── 3.7_puzzle_stealth/    <-- Logic & systemic mechanics (Push blocks, Vision cones, Undo/Redo) (.gitkeep)
```
