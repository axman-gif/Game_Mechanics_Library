# Minigames Architectural Guidelines & Registry (`minigames/`)

This document defines the architectural standards, design principles, and quality invariants for all standalone minigame prototypes.

All task tracking, prototype inventory, and progress statuses are maintained in the companion spreadsheet:
👉 [**`tasks/minigames.csv`**](../tasks/minigames.csv) (106 planned prototypes across sections 3.0 to 3.7)

---

## 1. Golden Architecture Rules for Minigames

1. **Single File Requirement**: Every minigame in `minigames/` must be a **single, standalone Python script** located inside its designated 3.x category subfolder (e.g., `minigames/3.0_core_prototypes/orbital_siege.py` or `minigames/3.2_combat_weapons/ballistic_mortar_arc.py`). It must be runnable on its own via `python -B minigames/<subfolder>/<script_name>.py` and testable headlessly via `python -B minigames/<subfolder>/<script_name>.py --smoke-test`.
2. **Modular Imports Allowed**: Each minigame script must enforce zero bytecode and import from `pyray`, `assets`, and `utils` in this exact order:
   ```python
   import sys
   import os
   sys.dont_write_bytecode = True
   sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

   from pyray import *
   from assets import *
   from utils import *
   ```
3. **Interactive Learning First (`[Tab]` X-Ray & `[F1]` Toggle)**:
   - Press `[Tab]` to toggle a live **X-Ray Telemetry & Debug Overlay** showing internal pattern state (pool usage, spatial grid cells, FSM/BT active node, raycast lines, timing bars).
   - Press `[F1]` (or number keys) to toggle the target pattern `ON/OFF` or tune its parameters so learners can feel the difference with vs. without the pattern.
4. **Language-Agnostic & C++-Transferable Code (Zero Pythonic Magic)**:
   - Python is used strictly as readable, executable pseudocode so learners can easily port every data structure and algorithm to **C++, C, C#, Rust, or Zig**.
   - **Forbidden**: Decorators (`@dataclass`, `@property`, `@staticmethod`), generators (`yield`), coroutines (`async`/`await`), magic dunder methods (other than `__init__`), `lambda`/`map`/`filter`, walrus operators (`:=`), or per-frame list comprehensions.
   - **Required**: Plain struct-like classes with explicit `__init__` fields, pre-allocated fixed arrays, integer indices/counters, and explicit `for` loops with `if/else` branches.
5. **Unified Sizing Limits & Strict Scope**:
   - **Target Range**: **600 to 1,500 lines** per minigame script across all sections (3.0 through 3.7).
   - **Floor**: **600 lines minimum**. Every script must provide thorough novice-friendly comments, complete 5-block anatomy, dual input parity, and X-Ray overlays.
   - **Hard Ceiling**: **1,800 lines maximum**. Under NO circumstances may any minigame script exceed 1,800 lines (enforced automatically by `audit_minigame.py`).
6. **Simultaneous Keyboard/Mouse & Gamepad Controls (Dual Input & Unified Pointer Parity)**:
   - Every minigame must support Keyboard/Mouse and Gamepad simultaneously via `utils/gamepad_input.py` (`get_dual_move_2d`, `get_dual_look_2d`, `is_dual_*`, `draw_gamepad_status_badge`), activating gamepad input automatically whenever a controller is detected without disabling Keyboard/Mouse.
   - For strategy and UI systems, ensure inputs are pointer-unified: interactions work identically with mouse clicks, drag gestures, and tap targets (minimum 44x44 pixel target bounds).
7. **Safe HUD Region**:
   - Keep the top-bar region `x = 450..980, y = 14..48` clear of HUD text so the repository's global settings dropdown bar (`draw_ui_settings_bar(450, 16)`) never overlaps game text.
8. **Automated Verification**:
   - After creating or editing any minigame, verify it headlessly:
     ```bash
     $env:PYTHONDONTWRITEBYTECODE="1"
     python -B audit_minigame.py minigames/<subfolder>/<script_name>.py
     python -B minigames/<subfolder>/<script_name>.py --smoke-test
     ```

---

## 2. 3.x Catalog Taxonomy Overview

The 106 planned prototypes in [`tasks/minigames.csv`](../tasks/minigames.csv) are categorized across 8 distinct architectural sections and directories:

- **Section 3.0: Core Multi-Pattern Prototypes** (`minigames/3.0_core_prototypes/`, 7 prototypes): Full arcade and strategy loops combining 4+ patterns (e.g. Orbital Siege 2D, Titan Strider 3D, Frontline Outpost RTS).
- **Section 3.1: Menus & UI** (`minigames/3.1_menus_ui/`, 17 prototypes): Tactile menus and interfaces (Diegetic Wrist Comm, Micro-Inventory Grid, Modular Workbench, Radial Pie, Strategy Ledgers).
- **Section 3.2: Combat & Weapons** (`minigames/3.2_combat_weapons/`, 17 prototypes): Projectile ballistics, frame data, parry windows, hit-stop juice, and targeting algorithms.
- **Section 3.3: Enemies & AI** (`minigames/3.3_enemies_ai/`, 15 prototypes): Flocking, flow fields, behavior trees, colossus multi-phase bosses, and squad blackboard coordination.
- **Section 3.4: Progression & Economy** (`minigames/3.4_progression_economy/`, 12 prototypes): Cumulative loot CDF sampling, mathematical XP curves, crafting DAGs, and gacha pity math.
- **Section 3.5: World & Procedural Exploration** (`minigames/3.5_world_procgen/`, 13 prototypes): Cellular automata caverns, BSP dungeons, voxel DDA raymarching, and dual-layer fog of war.
- **Section 3.6: Movement & Camera Rigs** (`minigames/3.6_movement_camera/`, 12 prototypes): Platformer forgiveness (Coyote time), verlet grappling, trauma screen shake, and kinematic controllers.
- **Section 3.7: Puzzle, Stealth & Other** (`minigames/3.7_puzzle_stealth/`, 13 prototypes): Undo/redo command stacks, deadlock detection, fluid cellular automata, and rhythm hit-windows.

---

## 3. Querying & Updating Tasks via CLI & Python `csv`

Subagents and automated scripts query [`tasks/minigames.csv`](../tasks/minigames.csv) using the headless `tasks.py` CLI (<50ms, zero Raylib GUI window) or Python's standard library `csv` module (<50 tokens per query).

### 3.1 Find Pending Prototypes in a Section (Fast CLI)
```bash
python -B tasks.py --list minigames --section 3.2 --status pending --limit 3
```

### 3.2 Fetch Full Prototype Specifications by ID (Fast CLI)
```bash
python -B tasks.py --get minigames mg_3201_mortar_arc
```

### 3.3 Mark a Prototype as Built (Fast CLI)
```bash
python -B tasks.py --set-status minigames mg_3201_mortar_arc built
```

### 3.4 Fallback: Python Standard Library `csv` One-Liners
```bash
# Query pending in section 3.2
python -B -c "import csv; f=open('tasks/minigames.csv', encoding='utf-8-sig'); r=csv.DictReader(f); print(next(dict(id=x['id'], title=x['title'], file=x['target_file']) for x in r if x['section']=='3.2' and x['status']=='pending'))"

# Count pending vs built prototypes
python -B -c "import csv; from collections import Counter; f=open('tasks/minigames.csv', encoding='utf-8-sig'); c=Counter((x['section'], x['status']) for x in csv.DictReader(f)); [print(f'{k[0]} [{k[1]}]: {v}') for k, v in sorted(c.items())]"
```

---

## 4. Human Spreadsheet Editing & Tasks Editor (`tasks.py`)

To inspect, sort, and edit [`tasks/minigames.csv`](../tasks/minigames.csv) without risking CSV delimiter, quote, or encoding corruption:
1. **Interactive Tasks Editor (`tasks.py`)**: Run `python -B tasks.py` to open the graphical Raylib task manager with hot-switching, sorting, cell editing, horizontal scrolling, and "Adjusted Text" (Wrap Text).
2. **Never alter column header names**: The first row must keep `id,section,title,dimension,target_file,patterns,status,description`.
3. **Allowed status values**: `pending`, `in_progress`, `built`.
