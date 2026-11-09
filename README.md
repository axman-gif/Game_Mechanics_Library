# 🎮 Video Game Design Patterns Library (`pyray` / Raylib Python)

<div align="center">

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Raylib](https://img.shields.io/badge/Raylib-pyray%206.0%2B-D73A49?style=for-the-badge&logo=raylib&logoColor=white)](https://www.raylib.com/)
[![Assets](https://img.shields.io/badge/Art%20Assets-0%20(100%25%20Procedural)-2ea44f?style=for-the-badge)](rules/assets.md)
[![Audio](https://img.shields.io/badge/Audio-Synthesized%20in%20RAM-orange?style=for-the-badge)](rules/audio.md)
[![Gamepad](https://img.shields.io/badge/Input-Dual%20KB%2FM%20%2B%20Gamepad-8A2BE2?style=for-the-badge)](rules/utils.md)
[![C++ Ready](https://img.shields.io/badge/Code%20Style-1%3A1%20C%2B%2B%20Transferable-blue?style=for-the-badge)](AGENTS.md)

**An interactive, beginner-friendly encyclopedia of video game programming patterns.**  
*Learn game architecture hands-on with pure geometric math, in-memory sound synthesis, live telemetry, and zero black-box game engines.*

---

### 🌐 Select Language / Selecciona tu Idioma
[🇬🇧 **English Guide**](#-english-guide) &nbsp;|&nbsp; [🇪🇸 **Guía en Español**](#-guía-en-español)

---

</div>

## 📑 Table of Contents / Tabla de Contenido
- [🇬🇧 English Guide](#-english-guide)
  - [🌟 What is this Project?](#-what-is-this-project)
  - [✨ Interactive Learning Features](#-interactive-learning-features)
  - [🚀 Quick-Start for Beginners (Step-by-Step)](#-quick-start-for-beginners-step-by-step)
  - [🕹️ How to Play & Explore](#️-how-to-play--explore)
  - [🎮 Global Controls (Keyboard, Mouse & Gamepad)](#-global-controls-keyboard-mouse--gamepad)
  - [🧩 Built Minigames & Pattern Showcase](#-built-minigames--pattern-showcase)
  - [💡 The "No-Magic" C++ Porting Philosophy](#-the-no-magic-c-porting-philosophy)
- [🇪🇸 Guía en Español](#-guía-en-español)
  - [🌟 ¿Qué es este proyecto?](#-qué-es-este-proyecto)
  - [✨ Características Interactivas de Aprendizaje](#-características-interactivas-de-aprendizaje)
  - [🚀 Guía Rápida para Principiantes (Paso a Paso)](#-guía-rápida-para-principiantes-paso-a-paso)
  - [🕹️ Cómo Jugar y Explorar](#️-cómo-jugar-y-explorar)
  - [🎮 Controles Globales (Teclado, Ratón y Mando)](#-controles-globales-teclado-ratón-y-mando)
  - [🧩 Catálogo de Minijuegos y Patrones](#-catálogo-de-minijuegos-y-patrones)
  - [💡 Filosofía "Cero Magia": Transferibilidad a C++](#-filosofía-cero-magia-transferibilidad-a-c)
- [📁 Repository Map / Estructura del Proyecto](#-repository-map--estructura-del-proyecto)
- [❓ Frequently Asked Questions & Troubleshooting](#-frequently-asked-questions--troubleshooting)

---

# 🇬🇧 English Guide

## 🌟 What is this Project?

Learning video game architecture is often frustrating for beginners. Modern engines like Unity, Unreal, or Godot hide the underlying math behind complex editors and gigabytes of dependencies, while traditional programming tutorials often get bogged down downloading 3D models, textures, and audio files.

This repository takes a radically different, ultra-clear approach:
1. **Zero External Art & Audio Assets**: Every 2D sprite and 3D character is built in real time using **mathematical primitives** (spheres, cubes, cylinders, lines, polygons). Every sound effect and background chord is **procedurally synthesized in RAM** using raw waveforms (sine, square, saw).
2. **Single-File Laboratories**: Every minigame inside `minigames/` is completely standalone. You can open a single `.py` file, read how the pattern works, change numbers, and immediately see the results.
3. **Pure, C++-Transferable Logic**: We use Python strictly as **executable pseudocode**. No confusing "Python magic" (no decorators, no generators, no complex comprehensions). Everything is written with simple structs, explicit arrays, and loops that translate **1-to-1 to C++, C, C#, Rust, or Zig**.
4. **Dual Controls Out-of-the-Box**: Plug in any modern controller (Xbox, PlayStation, or generic USB gamepad) and it will work seamlessly alongside your Keyboard and Mouse simultaneously.

---

## ✨ Interactive Learning Features

Every minigame in this collection includes two signature pedagogical tools:

> [!TIP]
> ### 🔬 1. The X-Ray Inspector (`[Tab]` or Gamepad `Y` / `Triangle`)
> Press **`[Tab]`** at any time to peel back the graphics and view the mathematical machinery underneath:
> - **Spatial Hash Grids**: Watch cell boundaries highlight as entities move across them.
> - **Object Pools**: Inspect active vs. available bullet slots and allocation metrics live.
> - **AI Brains**: See Behavior Tree and Finite State Machine (FSM) states change in real time.
> - **Physics & Rays**: Visualize collision capsules, line-of-sight raycasts, and trajectory vectors.

> [!NOTE]
> ### 🎚️ 2. The Live Pattern Toggle (`[F1]` or Gamepad `LB` / `L1`)
> Want to understand *why* a design pattern matters? Press **`[F1]`** to turn the pattern **OFF** during gameplay:
> - Turn off the **Object Pool** and feel the frame-rate hitch as memory gets allocated dynamically.
> - Turn off the **Spatial Grid** and watch CPU usage spike as collision checks degrade to $O(N^2)$.
> - Turn off **Camera Trauma Damping** and experience how stiff and jarring unsmoothed screens feel.
> - Press **`[F1]`** again to turn the pattern back **ON** and instantly feel the difference!

---

## 🚀 Quick-Start for Beginners (Step-by-Step)

You do **not** need to be an expert programmer or have Visual Studio installed to run this project. You only need standard Python!

### Step 1: Install Python 3.10+
1. Go to the official website: [python.org/downloads](https://www.python.org/downloads/).
2. Download and run the installer for your operating system.
3. > [!IMPORTANT]
   > **Windows Users**: On the very first screen of the installer, **check the box that says "Add python.exe to PATH"** before clicking Install. This enables you to run Python from any command line.

### Step 2: Download or Clone this Repository
- **With Git**:
  ```bash
  git clone https://github.com/AXMAN/Game_Mechanics_Library.git
  cd Game_Mechanics_Library
  ```
- **Without Git**: Click the green **Code** button at the top of this GitHub page, select **Download ZIP**, and extract it into a folder on your computer.

### Step 3: Create & Activate a Virtual Environment
A virtual environment ensures the project's dependencies don't interfere with the rest of your system. Open your terminal inside the project folder:

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(If PowerShell shows a script execution error, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and try activating again).*

**On Windows (Command Prompt - CMD):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 4: Install Raylib (Only 1 Dependency!)
This project only requires the official Raylib CFFI package (`pyray`):
```bash
pip install -r requirements.txt
```

---

## 🕹️ How to Play & Explore

### Option A: The Interactive Visual Hub (`launcher.py`)
The easiest way to explore the encyclopedia is with our built-in graphical launcher:
```bash
python -B launcher.py
```
*(The `-B` flag prevents Python from creating unnecessary `__pycache__` folders).*

Within the launcher:
- Browse minigames grouped by category (**Menus & UI**, **Combat & Weapons**, **Enemies & AI**, etc.).
- Read the **Problem Solved** and **How the Pattern Works** right inside the UI.
- Press **`Enter`** or click **`Launch Prototype`** to play.
- Press **`T`** or click **`Run Smoke Test`** to run an automated 3-frame integrity check.

### Option B: Run Any Minigame Directly
Every minigame is completely standalone. You can run any script straight from your terminal:
```bash
python -B minigames/<category_subfolder>/<script_name>.py

# Example:
# python -B minigames/3.0_core_prototypes/orbital_siege.py
```

### Option C: The Interactive Task Catalog & Spreadsheet Editor (`tasks.py`)
To inspect, edit, sort, and add prototypes or procedural assets across any catalog without risking CSV delimiter or quote corruption:
```bash
python -B tasks.py
```
- **Hot-Switch Catalogs**: Switch between `minigames.csv`, `SFXs.csv`, `BGMs.csv`, `models_3D.csv`, and `sprites_2D.csv` at runtime.
- **Hidden Technical Columns**: Keeps internal keys (`id`, `target_file`) hidden from the UI grid while faithfully auto-generating them when rows are added.
- **Pattern Selector Modal**: Select patterns directly from `rules/patterns.md` via a searchable multi-select checklist.
- **Safe Row Editing**: Insert rows above or below, duplicate rows, and sort alphanumerically with guaranteed schema immutability.

### Option D: The Interactive Procedural Asset Viewer & Workbench (`assets/audio/asset_viewer.py`)
To inspect, preview, audition, and test all 100% procedural assets across the repository without launching a full minigame:
```bash
python -B assets/audio/asset_viewer.py
```
- **4 Specialized Asset Tabs**:
  - **3D Models** (`assets/models_3D/`): Interactive 3D orbit camera, play/pause walking animations, stop/reset timer, speed, scale, yaw rotation slider, floor grid, wireframe toggle, and swappable semantic color palettes (Default, Stealth, Cyberpunk, Desert).
  - **2D Sprites** (`assets/sprites_2D/`): 2D zoom & pan canvas, play/pause procedural vector animations, facing angle dial/slider ($0^\circ \dots 360^\circ$ / radians), transparency checkerboard grid, scale, and swappable palettes (Default, Neon, Crimson, Emerald).
  - **SFX Sounds** (`assets/audio/SFX/`): One-shot trigger with `[Space]`, stop with `[S]`, loop toggle, volume & pitch sliders, real-time PCM oscilloscope waveform display with scanning playhead, and synthesis telemetry.
  - **BGM Tracks** (`assets/audio/BGM/`): Streaming music player with Play, Pause, Resume, Stop, draggable progress scrubber, volume & pitch/tempo sliders, tempo beat pulse flash indicator, and dynamic 24-band animated graphic equalizer / spectrum visualizer.
- **Live In-Memory Discovery**: Powered directly by `assets/audio/asset_loader.py`. Press **`[F5]`** at any time to dynamically rescan disk files and discover newly created assets without restarting.
- **Ready-to-Use Minigame Code**: The right inspector panel shows the exact Python code snippet to import and use any selected asset in your minigames.
- **Automated Smoke Test**: Run `python -B assets/audio/asset_viewer.py --smoke-test` to verify all 4 tabs and audio streaming headlessly in CI/CD.

---

## 🎮 Global Controls (Keyboard, Mouse & Gamepad)

All prototypes feature unified controls with simultaneous Keyboard/Mouse and Gamepad support:

| Action | Keyboard & Mouse | Gamepad / Controller |
| :--- | :--- | :--- |
| **Movement / Navigate** | `W` `A` `S` `D` / Arrow Keys | **Left Analog Stick** (with radial deadzone) or **D-Pad** |
| **Aim / Reticle / Look** | **Mouse Cursor** / `Q` & `E` | **Right Analog Stick** (steers reticle or 3D camera) |
| **Primary Action / Select** | `Space` / Left Mouse Button / `Enter` | **Face Button A** (Xbox) / **Cross** (PlayStation) / `RT` |
| **Secondary Action / Back** | `Right Click` / `Esc` / `Backspace` | **Face Button B** (Xbox) / **Circle** (PlayStation) / `LT` |
| **🔬 X-Ray Telemetry Overlay** | **`[Tab]`** | **Face Button Y** (Xbox) / **Triangle** (PlayStation) |
| **🎚️ Pattern Toggle (ON/OFF)** | **`[F1]`** | **Left Bumper (`LB` / `L1`)** |
| **🎛️ Secondary Toggle / Parameter** | **`[F2]`** | **Right Bumper (`RB` / `R1`)** |
| **🔄 Reset Simulation** | **`[R]`** | **Start** (Xbox Menu / PlayStation Options) |
| **🔤 Font Size Adjust** | **`Ctrl + '+'`** / **`Ctrl + '-'`** | *Use Top Bar Dropdown* |
| **🖥️ Toggle Fullscreen** | **`[F11]`** | *Use Top Bar Dropdown* |

> [!TIP]
> ### ⚙️ The Global Top Settings Bar
> Every window displays an interactive bar at the top:
> - **`Font`**: Switch live between Raylib's pixel font and your system's TrueType fonts (`Consolas`, `Segoe UI`, `Arial`, etc.).
> - **`Size`**: Adjust UI text size on the fly.
> - **`Win`**: Change window resolution (`1024x576`, `1280x720`, `1600x900`, `1920x1080`) or toggle Fullscreen (`F11`).
> - **`PAD Status`**: Live indicator showing whether your controller is detected (`PAD: ON` vs `PAD: OFF`).
> 
> *All your settings are automatically saved in `config.json`.*

---

## 🧩 Built Minigames & Pattern Showcase

The library organizes minigames and experimental laboratories into designated subfolders under [`minigames/`](minigames/):

| Section | Category Subfolder | Dimension & Scope | Description of Laboratory Mechanics |
| :---: | :--- | :---: | :--- |
| **3.0** | [`3.0_core_prototypes/`](minigames/3.0_core_prototypes/) | **2D / 3D Full Slices** | Multi-pattern arcade and strategy loops combining 4+ systems (orbital gravity wells, procedural IK behemoths, subterranean excavation drills, 6-DOF space dogfights, turn-based tactics, and RTS outposts). |
| **3.1** | [`3.1_menus_ui/`](minigames/3.1_menus_ui/) | **2D / 3D Menus & UI** | Tactile and responsive interface architectures: diegetic 3D displays, polyomino inventories, modular weapon socket DAGs, radial wheels, maximalist 4X ledgers, and unified cross-platform touch/mouse viewports. |
| **3.2** | [`3.2_combat_weapons/`](minigames/3.2_combat_weapons/) | **2D / 3D Combat** | Kinetic weapon ballistics, parabolic mortars, penetrating hitscan, recoil bloom springs, active reload timing, fighting game frame-data arcs, parry stagger windows, elemental reactions, and RTS siege splash. |
| **3.3** | [`3.3_enemies_ai/`](minigames/3.3_enemies_ai/) | **2D / 3D AI Systems** | Autonomous enemy steering, flocking boids, Dijkstra flow fields for swarms, tactical cover scoring, visualized behavior trees, threat aggro tables, multi-phase bosses, and RTS military formation steering. |
| **3.4** | [`3.4_progression_economy/`](minigames/3.4_progression_economy/) | **2D Progression** | Mathematical progression and economy models: CDF loot drop histograms, polynomial/exponential XP curves, crafting DAGs, market supply/demand, deckbuilder cycles, and 4X resource flow ledgers. |
| **3.5** | [`3.5_world_procgen/`](minigames/3.5_world_procgen/) | **2D / 3D Worlds** | Procedural generation and exploration: cellular automata caverns, BSP dungeons, Amanatides-Woo DDA voxel raymarching, infinite chunk streaming, dynamic day-night orbits, and dual-layer fog of war. |
| **3.6** | [`3.6_movement_camera/`](minigames/3.6_movement_camera/) | **2D / 3D Movement** | Movement kinematics and game feel: Coyote time and jump buffers, Verlet pendulum grapples, 3D Quake-style strafing controllers, spring-arm orbit cameras, trauma screen shake, and RTS panning cameras. |
| **3.7** | [`3.7_puzzle_stealth/`](minigames/3.7_puzzle_stealth/) | **2D / 3D Systems** | Discrete logic and systemic interactions: Sokoban deadlock detection with undo/redo stacks, stealth illumination sensors, cellular fluid automata, lockpicking sweet spots, and RTS marquee box selection. |

### 🎯 5-Tier Difficulty Rating System

Every prototype is calibrated to an explicit difficulty rating indicating algorithmic and mathematical complexity:

- `1 - Beginner`: Single-formula mechanics, discrete HUD timers, or isolated UI/audio feedback (e.g. Active Reload, XP Curves, Trauma Shake).
- `2 - Novice`: Straightforward 2D kinematics, basic trigonometric vectors, and classic game loops (e.g. Parabolic Mortar, Shotgun Choke, Coyote Time).
- `3 - Intermediate`: Foundational game programming patterns, spatial data structures, and procedural generation (e.g. Object Pools, Spatial Grids, Behavior Trees, BSP Dungeons, Verlet Grappling).
- `4 - Advanced`: High-complexity multi-agent systems, dynamic flow fields, 3D kinematics, and multi-pattern loops (e.g. Dijkstra Flow Fields, Tactical Cover AI, Quake Kinematics, RTS Marquee/Formations).
- `5 - Master`: Apex architectural systems featuring cutting-edge algorithms (e.g. Procedural Inverse Kinematics in 3D, 6-DOF Inertial Flight Interception, Amanatides-Woo Fast Voxel DDA).

### 🗂️ Interactive Minigame Catalog (106 Prototypes)

Click any category below to expand its full prototype roster with difficulty ratings, target patterns, and source files:

<details>
<summary><b>Section 3.0: Core Multi-Pattern Prototypes (7 prototypes)</b></summary>

| ID | Title | Difficulty | Dim | Demonstrated Patterns | Target File |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `mg_301_orbital_siege` | Orbital Siege 2D | **4 - Advanced** | 2D | N-Body Gravitational Well, Object Pool, Spatial Partitioning (SpatialGrid2D), State Machine (FSM), Wave Director | [`minigames/3.0_core_prototypes/orbital_siege.py`](minigames/3.0_core_prototypes/orbital_siege.py) |
| `mg_302_titan_strider` | Titan Strider 3D | **5 - Master** | 3D | Procedural Inverse Kinematics, Behavior Tree (BT), Rotated Capsule Collisions (Capsule3D), Multi-Phase Boss, Camera Rig (TraumaShake) | [`minigames/3.0_core_prototypes/titan_strider.py`](minigames/3.0_core_prototypes/titan_strider.py) |
| `mg_303_subterranean_drill` | Subterranean Drill Rig 2D | **4 - Advanced** | 2D | Destructible Tile Grid, A* Pathfinding Burrowers, Cellular Particle Fall, Resource Pressure Loop, Command Pattern | [`minigames/3.0_core_prototypes/subterranean_drill_rig.py`](minigames/3.0_core_prototypes/subterranean_drill_rig.py) |
| `mg_304_gunship_interceptor` | Gunship Interceptor 3D | **5 - Master** | 3D | 6-DOF Inertial Flight Kinematics, Lead-Pursuit Intercept Math, Swept-Volume Raymarching, Spatial Partitioning (SpatialGrid3D), Audio Synthesis | [`minigames/3.0_core_prototypes/gunship_interceptor.py`](minigames/3.0_core_prototypes/gunship_interceptor.py) |
| `mg_305_chrono_infiltrator` | Chrono Infiltrator 2D | **4 - Advanced** | 2D | Command Pattern (Circular History Ring Buffer), Raycast Vision Cones, Alert Level State Machine, Spatial Hashing (SpatialGrid2D) | [`minigames/3.0_core_prototypes/chrono_infiltrator.py`](minigames/3.0_core_prototypes/chrono_infiltrator.py) |
| `mg_306_tactical_commander` | Tactical Commander TBS 2D | **4 - Advanced** | 2D | Hexagonal Axial Coordinate System, Action Points (AP) Budget, Bresenham Line-of-Sight Grid, Zone of Control (ZoC), Initiative Turn Queue | [`minigames/3.0_core_prototypes/tactical_commander_tbs.py`](minigames/3.0_core_prototypes/tactical_commander_tbs.py) |
| `mg_307_frontline_outpost` | Frontline Outpost RTS 2D | **4 - Advanced** | 2D | Marquee Box Selection, Multi-Agent Flow Field Pathfinding, Worker Harvesting FSM, Footprint Placement Grid, Dual-Layer Fog of War | [`minigames/3.0_core_prototypes/frontline_outpost_rts.py`](minigames/3.0_core_prototypes/frontline_outpost_rts.py) |

</details>

<details>
<summary><b>Section 3.1: Menus & UI (17 prototypes)</b></summary>

| ID | Title | Difficulty | Dim | Demonstrated Patterns | Target File |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `mg_3101_wrist_comm` | Diegetic Wrist Comm 3D | **4 - Advanced** | 3D | Diegetic World-Space Interface, Damped Spring Parallax, Offscreen Texture Projection (FBO), Localized Radar Coordinate Pipeline | [`minigames/3.1_menus_ui/diegetic_wrist_comm.py`](minigames/3.1_menus_ui/diegetic_wrist_comm.py) |
| `mg_3102_inventory_grid` | Micro-Inventory Grid 2D | **3 - Intermediate** | 2D | Polyomino Cell Packing & First-Fit Heuristics | [`minigames/3.1_menus_ui/micro_inventory_grid.py`](minigames/3.1_menus_ui/micro_inventory_grid.py) |
| `mg_3103_weapon_workbench` | Modular Weapon Workbench 2D | **4 - Advanced** | 2D | Socket-Attachment Graph & Pure Stat Pipeline | [`minigames/3.1_menus_ui/modular_weapon_workbench.py`](minigames/3.1_menus_ui/modular_weapon_workbench.py) |
| `mg_3104_lock_on_reticle` | Tactical Lock-On Reticle 3D | **3 - Intermediate** | 3D | Screen-Space Reticle Projection & Viewport Clamping | [`minigames/3.1_menus_ui/tactical_lock_on_reticle.py`](minigames/3.1_menus_ui/tactical_lock_on_reticle.py) |
| `mg_3105_radial_action_pie` | Radial Action Pie 2D | **2 - Novice** | 2D | Angular Sector Partitioning & Bullet-Time Dilation | [`minigames/3.1_menus_ui/radial_action_pie.py`](minigames/3.1_menus_ui/radial_action_pie.py) |
| `mg_3106_floating_combat_splats` | Floating Combat Splats 2D | **2 - Novice** | 2D | Zero-Allocation Pool & Trajectory Curves | [`minigames/3.1_menus_ui/floating_combat_splats.py`](minigames/3.1_menus_ui/floating_combat_splats.py) |
| `mg_3107_tech_constellation` | Interactive Tech Constellation 2D | **3 - Intermediate** | 2D | Directed Acyclic Graph (DAG) Reachability & Virtual Canvas | [`minigames/3.1_menus_ui/interactive_tech_constellation.py`](minigames/3.1_menus_ui/interactive_tech_constellation.py) |
| `mg_3108_hotbar_gcd` | Tactical Hotbar GCD 2D | **1 - Beginner** | 2D | Dual-Tier Global Cooldown (GCD) & Action Dispatcher | [`minigames/3.1_menus_ui/tactical_hotbar_gcd.py`](minigames/3.1_menus_ui/tactical_hotbar_gcd.py) |
| `mg_3109_dialogue_yarn` | Dialogue Yarn Engine 2D | **3 - Intermediate** | 2D | Branching Dialogue Tree & Conditional Gating | [`minigames/3.1_menus_ui/dialogue_yarn_engine.py`](minigames/3.1_menus_ui/dialogue_yarn_engine.py) |
| `mg_3110_settings_rack` | Audio-Visual Settings Rack 2D | **3 - Intermediate** | 2D | Command Pattern & Persisted Setting Dispatcher | [`minigames/3.1_menus_ui/settings_rack.py`](minigames/3.1_menus_ui/settings_rack.py) |
| `mg_3111_skyline_compass` | Skyline Compass Strip 3D | **3 - Intermediate** | 3D | Horizontal Degree Tape & Proximity Waypoint Projection | [`minigames/3.1_menus_ui/skyline_compass_strip.py`](minigames/3.1_menus_ui/skyline_compass_strip.py) |
| `mg_3112_lagging_chip_health` | Lagging Chip Health Bar 2D | **1 - Beginner** | 2D | Multi-Tiered HUD Gauge & Catchup Damping | [`minigames/3.1_menus_ui/lagging_chip_health.py`](minigames/3.1_menus_ui/lagging_chip_health.py) |
| `mg_3113_strategy_ledger` | 4X Grand Strategy Ledger 2D | **4 - Advanced** | 2D | Maximalist Multi-Panel Dashboard & Column Sorting | [`minigames/3.1_menus_ui/strategy_ledger.py`](minigames/3.1_menus_ui/strategy_ledger.py) |
| `mg_3114_minimalist_radial` | Immersive Minimalist Radial 2D | **2 - Novice** | 2D | Minimalist HUD-Less Action Rings & Idle Fade | [`minigames/3.1_menus_ui/immersive_minimalist_radial.py`](minigames/3.1_menus_ui/immersive_minimalist_radial.py) |
| `mg_3115_pointer_viewport` | Unified Pointer Viewport 2D | **2 - Novice** | 2D | Cross-Platform Touch/Mouse Navigation & Virtual Canvas | [`minigames/3.1_menus_ui/unified_pointer_viewport.py`](minigames/3.1_menus_ui/unified_pointer_viewport.py) |
| `mg_3116_isometric_tile_cursor` | Isometric Tile Cursor 2D | **3 - Intermediate** | 2D | Screen-to-Isometric Coordinate Inversion | [`minigames/3.1_menus_ui/isometric_tile_cursor.py`](minigames/3.1_menus_ui/isometric_tile_cursor.py) |
| `mg_3117_hex_coordinate_inspector` | Hex Coordinate Inspector 2D | **3 - Intermediate** | 2D | Axial & Cube Coordinate Space Math | [`minigames/3.1_menus_ui/hex_coordinate_inspector.py`](minigames/3.1_menus_ui/hex_coordinate_inspector.py) |

</details>

<details>
<summary><b>Section 3.2: Combat & Weapons (17 prototypes)</b></summary>

| ID | Title | Difficulty | Dim | Demonstrated Patterns | Target File |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `mg_3201_mortar_arc` | Ballistic Mortar Arc 2D | **2 - Novice** | 2D | Parabolic Kinematics & Closed-Form Trajectory Solver | [`minigames/3.2_combat_weapons/ballistic_mortar_arc.py`](minigames/3.2_combat_weapons/ballistic_mortar_arc.py) |
| `mg_3202_hitscan_penetration` | Hitscan Penetration Rig 3D | **3 - Intermediate** | 3D | Multi-Stage Raycast & Material Density Attenuation | [`minigames/3.2_combat_weapons/hitscan_penetration_rig.py`](minigames/3.2_combat_weapons/hitscan_penetration_rig.py) |
| `mg_3203_shotgun_choke` | Shotgun Dispersion Choke 2D | **2 - Novice** | 2D | Gaussian Distribution Cone & Pellet Grouping | [`minigames/3.2_combat_weapons/shotgun_dispersion_choke.py`](minigames/3.2_combat_weapons/shotgun_dispersion_choke.py) |
| `mg_3204_recoil_bloom` | Recoil Bloom & Recovery 3D | **3 - Intermediate** | 3D | Exponential Spring Dissipation & Angular Bloom | [`minigames/3.2_combat_weapons/recoil_bloom_recovery.py`](minigames/3.2_combat_weapons/recoil_bloom_recovery.py) |
| `mg_3205_active_reload` | Active Reload Timing 2D | **1 - Beginner** | 2D | Timing Window State Machine & Cooldown Modulation | [`minigames/3.2_combat_weapons/active_reload_timing.py`](minigames/3.2_combat_weapons/active_reload_timing.py) |
| `mg_3206_melee_frame_data` | Melee Frame Data Arc 2D | **3 - Intermediate** | 2D | Frame-Accurate Attack Lifecycle & Swept Polygon Hitbox | [`minigames/3.2_combat_weapons/melee_frame_data_arc.py`](minigames/3.2_combat_weapons/melee_frame_data_arc.py) |
| `mg_3207_parry_timing` | Parry Timing & Stagger 2D | **2 - Novice** | 2D | Counter-Window Detection & Poise Breakdown | [`minigames/3.2_combat_weapons/parry_timing_stagger.py`](minigames/3.2_combat_weapons/parry_timing_stagger.py) |
| `mg_3208_elemental_reaction` | Elemental Reaction Matrix 2D | **3 - Intermediate** | 2D | Combinatorial Status Pipeline & Aura Persistence | [`minigames/3.2_combat_weapons/elemental_reaction_matrix.py`](minigames/3.2_combat_weapons/elemental_reaction_matrix.py) |
| `mg_3209_predictive_intercept` | Predictive Intercept Targeter 3D | **3 - Intermediate** | 3D | Quadratic Intercept Math & Lead Reticle Calculation | [`minigames/3.2_combat_weapons/predictive_intercept_targeter.py`](minigames/3.2_combat_weapons/predictive_intercept_targeter.py) |
| `mg_3210_pro_nav_missile` | Proportional Navigation Missile 2D | **3 - Intermediate** | 2D | Pro-Nav Guidance Laws & Countermeasure Decoys | [`minigames/3.2_combat_weapons/pro_nav_missile.py`](minigames/3.2_combat_weapons/pro_nav_missile.py) |
| `mg_3211_ricochet_laser` | Specular Ricochet Laser 2D | **2 - Novice** | 2D | Geometric Normal Reflection & Ray Marching | [`minigames/3.2_combat_weapons/specular_ricochet_laser.py`](minigames/3.2_combat_weapons/specular_ricochet_laser.py) |
| `mg_3212_hit_stop_juice` | Impact Feel & Hit-Stop Lab 2D | **2 - Novice** | 2D | Micro-Freeze Frame, Trauma Shake & White Flash | [`minigames/3.2_combat_weapons/impact_feel_hit_stop.py`](minigames/3.2_combat_weapons/impact_feel_hit_stop.py) |
| `mg_3213_cartridge_hopper` | Modular Cartridge Hopper 2D | **2 - Novice** | 2D | Strategy Pattern Projectile Dispatcher | [`minigames/3.2_combat_weapons/modular_cartridge_hopper.py`](minigames/3.2_combat_weapons/modular_cartridge_hopper.py) |
| `mg_3214_directional_shield` | Directional Shield Flank 2D | **2 - Novice** | 2D | Angular Guard Arc & Dot Product Facing Check | [`minigames/3.2_combat_weapons/directional_shield_flank.py`](minigames/3.2_combat_weapons/directional_shield_flank.py) |
| `mg_3215_zone_of_control` | Grid Zone of Control & Flank 2D | **3 - Intermediate** | 2D | Zone of Control (ZoC) & Flanking Multiplier Matrix | [`minigames/3.2_combat_weapons/grid_zone_of_control.py`](minigames/3.2_combat_weapons/grid_zone_of_control.py) |
| `mg_3216_rts_siege_battery` | RTS Siege Battery Splash 2D | **3 - Intermediate** | 2D | Ground-Target Ballistics & Quadratic Area Splash | [`minigames/3.2_combat_weapons/rts_siege_battery.py`](minigames/3.2_combat_weapons/rts_siege_battery.py) |
| `mg_3217_supercover_raycaster` | Grid Supercover Raycaster 2D | **3 - Intermediate** | 2D | Supercover Grid Traversal & Cover Mitigation | [`minigames/3.2_combat_weapons/grid_supercover_raycaster.py`](minigames/3.2_combat_weapons/grid_supercover_raycaster.py) |

</details>

<details>
<summary><b>Section 3.3: Enemies & AI (15 prototypes)</b></summary>

| ID | Title | Difficulty | Dim | Demonstrated Patterns | Target File |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `mg_3301_boid_flocking` | Boid Flocking & Predator Panic 2D | **3 - Intermediate** | 2D | Reynolds Steering Behaviors (Separation, Cohesion, Alignment) | [`minigames/3.3_enemies_ai/boid_flocking.py`](minigames/3.3_enemies_ai/boid_flocking.py) |
| `mg_3302_flow_field_horde` | Dijkstra Flow Field Horde 2D | **4 - Advanced** | 2D | Flow Field / Distance Integration Grid | [`minigames/3.3_enemies_ai/flow_field_horde.py`](minigames/3.3_enemies_ai/flow_field_horde.py) |
| `mg_3303_tactical_cover_ai` | Tactical Cover & Flank AI 3D | **4 - Advanced** | 3D | Utility AI Cover Scoring & Line-of-Sight Evaluation | [`minigames/3.3_enemies_ai/tactical_cover_ai.py`](minigames/3.3_enemies_ai/tactical_cover_ai.py) |
| `mg_3304_behavior_tree` | Visualized Behavior Tree 2D | **3 - Intermediate** | 2D | Hierarchical Behavior Tree (Selector, Sequence, Decorator) | [`minigames/3.3_enemies_ai/visualized_behavior_tree.py`](minigames/3.3_enemies_ai/visualized_behavior_tree.py) |
| `mg_3305_threat_table` | Raid Boss Threat Table 3D | **3 - Intermediate** | 3D | Aggro Table & Threat Accumulation Pipeline | [`minigames/3.3_enemies_ai/raid_boss_threat_table.py`](minigames/3.3_enemies_ai/raid_boss_threat_table.py) |
| `mg_3306_colossus_boss` | Multi-Stage Colossus Boss 3D | **4 - Advanced** | 3D | Multi-Phase State Machine & Attack Choreography | [`minigames/3.3_enemies_ai/colossus_boss.py`](minigames/3.3_enemies_ai/colossus_boss.py) |
| `mg_3307_ghost_pursuers` | Ghost Pursuer Archetypes 2D | **2 - Novice** | 2D | Diverse Target-Tile Targeting Heuristics | [`minigames/3.3_enemies_ai/ghost_pursuer_archetypes.py`](minigames/3.3_enemies_ai/ghost_pursuer_archetypes.py) |
| `mg_3308_squad_blackboard` | Squad Blackboard Coordination 2D | **4 - Advanced** | 2D | Shared Blackboard & Combat Token Allocation | [`minigames/3.3_enemies_ai/squad_blackboard.py`](minigames/3.3_enemies_ai/squad_blackboard.py) |
| `mg_3309_stealth_sensory` | Stealth Sensory Cones 2D | **3 - Intermediate** | 2D | Raycast Vision Polygons & Acoustic Hearing Rings | [`minigames/3.3_enemies_ai/stealth_sensory_cones.py`](minigames/3.3_enemies_ai/stealth_sensory_cones.py) |
| `mg_3310_tension_director` | Dynamic Tension AI Director 2D | **4 - Advanced** | 2D | AI Director & Emotional Tension Curves | [`minigames/3.3_enemies_ai/dynamic_tension_director.py`](minigames/3.3_enemies_ai/dynamic_tension_director.py) |
| `mg_3311_telegraphed_hazard` | Telegraphed Hazard Forecast 2D | **2 - Novice** | 2D | Attack Forecasting & Fill-Progress Telegraphs | [`minigames/3.3_enemies_ai/telegraphed_hazard_forecast.py`](minigames/3.3_enemies_ai/telegraphed_hazard_forecast.py) |
| `mg_3312_territorial_leash` | Territorial Leash Anchor 3D | **2 - Novice** | 3D | Tether Radius & Soft Reset State Machine | [`minigames/3.3_enemies_ai/territorial_leash_anchor.py`](minigames/3.3_enemies_ai/territorial_leash_anchor.py) |
| `mg_3313_formation_steering` | RTS Formation Steering 2D | **4 - Advanced** | 2D | Rigid/Elastic Formation Slots & Offset Steering | [`minigames/3.3_enemies_ai/rts_formation_steering.py`](minigames/3.3_enemies_ai/rts_formation_steering.py) |
| `mg_3314_tbs_utility_brain` | TBS Utility Tactical Brain 2D | **4 - Advanced** | 2D | Goal-Oriented Action Utility Curves & Scoring | [`minigames/3.3_enemies_ai/tbs_utility_tactical_brain.py`](minigames/3.3_enemies_ai/tbs_utility_tactical_brain.py) |
| `mg_3315_harvester_cycle` | Harvester Resource Cycle FSM 2D | **2 - Novice** | 2D | Finite State Machine Worker Gathering Cycle | [`minigames/3.3_enemies_ai/harvester_cycle_fsm.py`](minigames/3.3_enemies_ai/harvester_cycle_fsm.py) |

</details>

<details>
<summary><b>Section 3.4: Progression & Economy (12 prototypes)</b></summary>

| ID | Title | Difficulty | Dim | Demonstrated Patterns | Target File |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `mg_3401_loot_pinata` | Cumulative Loot Piñata 2D | **2 - Novice** | 2D | Cumulative Distribution Function (CDF) Sampling & Histograms | [`minigames/3.4_progression_economy/cumulative_loot_pinata.py`](minigames/3.4_progression_economy/cumulative_loot_pinata.py) |
| `mg_3402_xp_curves` | Mathematical XP Curves 2D | **1 - Beginner** | 2D | Level Progression Curves & Diminishing Returns | [`minigames/3.4_progression_economy/mathematical_xp_curves.py`](minigames/3.4_progression_economy/mathematical_xp_curves.py) |
| `mg_3403_crafting_dag` | Crafting Dependency DAG 2D | **3 - Intermediate** | 2D | Directed Acyclic Graph Recipe Solver & Atomic Deductions | [`minigames/3.4_progression_economy/crafting_dag.py`](minigames/3.4_progression_economy/crafting_dag.py) |
| `mg_3404_merchant_exchange` | Dynamic Merchant Exchange 2D | **3 - Intermediate** | 2D | Supply & Demand Price Floating & Arbitrage Prevention | [`minigames/3.4_progression_economy/dynamic_merchant_exchange.py`](minigames/3.4_progression_economy/dynamic_merchant_exchange.py) |
| `mg_3405_passive_relics` | Passive Relic Synergy Stack 2D | **3 - Intermediate** | 2D | Observer Pattern Item Hook Pipeline | [`minigames/3.4_progression_economy/passive_relic_synergy.py`](minigames/3.4_progression_economy/passive_relic_synergy.py) |
| `mg_3406_gacha_pity` | Gacha Pity Simulator 2D | **1 - Beginner** | 2D | Soft Pity Thresholds & 50/50 Guarantee Engine | [`minigames/3.4_progression_economy/gacha_pity_simulator.py`](minigames/3.4_progression_economy/gacha_pity_simulator.py) |
| `mg_3407_weapon_integrity` | Weapon Integrity & Repair 2D | **2 - Novice** | 2D | Item Durability Degradation & Scrap Salvage | [`minigames/3.4_progression_economy/weapon_integrity_repair.py`](minigames/3.4_progression_economy/weapon_integrity_repair.py) |
| `mg_3408_deckbuilder_hand` | Deckbuilder Hand Cycle 2D | **3 - Intermediate** | 2D | Deck, Hand, Discard & Exhaust Pile State Engine | [`minigames/3.4_progression_economy/deckbuilder_hand_cycle.py`](minigames/3.4_progression_economy/deckbuilder_hand_cycle.py) |
| `mg_3409_idle_forge` | Incremental Idle Forge 2D | **1 - Beginner** | 2D | Exponential Growth Curves & Offline Accumulation | [`minigames/3.4_progression_economy/incremental_idle_forge.py`](minigames/3.4_progression_economy/incremental_idle_forge.py) |
| `mg_3410_attribute_respec` | RPG Attribute Respec 2D | **1 - Beginner** | 2D | Primary-to-Secondary Derived Stat Pipeline | [`minigames/3.4_progression_economy/rpg_attribute_respec.py`](minigames/3.4_progression_economy/rpg_attribute_respec.py) |
| `mg_3411_tech_tree_research` | RTS Tech Tree Research Lab 2D | **3 - Intermediate** | 2D | Technology DAG Queue & Global Modifier Propagation | [`minigames/3.4_progression_economy/rts_tech_tree_research.py`](minigames/3.4_progression_economy/rts_tech_tree_research.py) |
| `mg_3412_resource_ledger` | 4X Resource Flow Ledger 2D | **4 - Advanced** | 2D | Multi-Commodity Inflow/Outflow Matrix & Deficit Penalties | [`minigames/3.4_progression_economy/resource_flow_ledger.py`](minigames/3.4_progression_economy/resource_flow_ledger.py) |

</details>

<details>
<summary><b>Section 3.5: World & Exploration (13 prototypes)</b></summary>

| ID | Title | Difficulty | Dim | Demonstrated Patterns | Target File |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `mg_3501_cellular_caverns` | Cellular Automata Caverns 2D | **3 - Intermediate** | 2D | Cellular Automata Smoothing & Flood-Fill Connectivity | [`minigames/3.5_world_procgen/cellular_caverns.py`](minigames/3.5_world_procgen/cellular_caverns.py) |
| `mg_3502_bsp_dungeon` | BSP Dungeon Architect 2D | **3 - Intermediate** | 2D | Binary Space Partitioning (BSP) & Room Linkage | [`minigames/3.5_world_procgen/bsp_dungeon_architect.py`](minigames/3.5_world_procgen/bsp_dungeon_architect.py) |
| `mg_3503_voxel_dda` | Voxel Raymarching DDA 3D | **5 - Master** | 3D | Fast Voxel Traversal (Amanatides-Woo DDA) & Hidden Face Culling | [`minigames/3.5_world_procgen/voxel_raymarching_dda.py`](minigames/3.5_world_procgen/voxel_raymarching_dda.py) |
| `mg_3504_chunk_streamer` | Infinite Chunk Streamer 2D | **3 - Intermediate** | 2D | Hash Grid Spatial Streaming & Memory Management | [`minigames/3.5_world_procgen/infinite_chunk_streamer.py`](minigames/3.5_world_procgen/infinite_chunk_streamer.py) |
| `mg_3505_layered_noise_heightmap` | Layered Noise Heightmap 3D | **4 - Advanced** | 3D | Multi-Octave Fractal Noise Terrain & Normal Baking | [`minigames/3.5_world_procgen/layered_noise_heightmap.py`](minigames/3.5_world_procgen/layered_noise_heightmap.py) |
| `mg_3506_celestial_orbit` | Dynamic Celestial Orbit 3D | **3 - Intermediate** | 3D | Day-Night Celestial Orbit & Sky Dome Gradient | [`minigames/3.5_world_procgen/dynamic_celestial_orbit.py`](minigames/3.5_world_procgen/dynamic_celestial_orbit.py) |
| `mg_3507_biome_hazard` | Hazardous Biome Suit 3D | **3 - Intermediate** | 3D | Environmental Hazard Zones & Exposure Decay | [`minigames/3.5_world_procgen/hazardous_biome_suit.py`](minigames/3.5_world_procgen/hazardous_biome_suit.py) |
| `mg_3508_destructible_terrain` | Destructible Terrain Mask 2D | **3 - Intermediate** | 2D | Bitmask Terrain Deformation & Sand Physics | [`minigames/3.5_world_procgen/destructible_terrain_mask.py`](minigames/3.5_world_procgen/destructible_terrain_mask.py) |
| `mg_3509_ability_gate` | Lock-and-Key Ability Gate 2D | **2 - Novice** | 2D | Metroidvania Progression Graph & Reachability | [`minigames/3.5_world_procgen/ability_gate_graph.py`](minigames/3.5_world_procgen/ability_gate_graph.py) |
| `mg_3510_obstacle_runner` | Infinite Lane Obstacle Runner 3D | **2 - Novice** | 3D | Segment Pooling & Dynamic Obstacle Weaving | [`minigames/3.5_world_procgen/infinite_lane_runner.py`](minigames/3.5_world_procgen/infinite_lane_runner.py) |
| `mg_3511_dual_layer_fog` | Dual-Layer Fog of War 2D | **3 - Intermediate** | 2D | Three-State Visibility Bitmask & Dynamic Sight Radii | [`minigames/3.5_world_procgen/dual_layer_fog.py`](minigames/3.5_world_procgen/dual_layer_fog.py) |
| `mg_3512_hex_biomes` | Hex World Biome Generator 2D | **3 - Intermediate** | 2D | Procedural Hex Map & Elevation Moisture Matrix | [`minigames/3.5_world_procgen/hex_world_biomes.py`](minigames/3.5_world_procgen/hex_world_biomes.py) |
| `mg_3513_building_placement` | RTS Building Placement Grid 2D | **2 - Novice** | 2D | Multi-Cell Footprint Clearance & Ghost Snapping | [`minigames/3.5_world_procgen/rts_building_placement.py`](minigames/3.5_world_procgen/rts_building_placement.py) |

</details>

<details>
<summary><b>Section 3.6: Movement & Camera (12 prototypes)</b></summary>

| ID | Title | Difficulty | Dim | Demonstrated Patterns | Target File |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `mg_3601_platformer_forgiveness` | Platformer Forgiveness Lab 2D | **2 - Novice** | 2D | Coyote Time, Jump Buffering & Corner Assist | [`minigames/3.6_movement_camera/platformer_forgiveness.py`](minigames/3.6_movement_camera/platformer_forgiveness.py) |
| `mg_3602_grappling_cable` | Pendulum Grappling Cable 2D | **3 - Intermediate** | 2D | Verlet Rope Integration & Angular Momentum Swing | [`minigames/3.6_movement_camera/pendulum_grappling_cable.py`](minigames/3.6_movement_camera/pendulum_grappling_cable.py) |
| `mg_3603_kinematic_controller` | Kinematic Character Rig 3D | **4 - Advanced** | 3D | Ground Friction, Air Strafe & Ledge Step-Up | [`minigames/3.6_movement_camera/kinematic_character_rig.py`](minigames/3.6_movement_camera/kinematic_character_rig.py) |
| `mg_3604_toroidal_drifter` | Newtonian Toroidal Drifter 2D | **2 - Novice** | 2D | Thruster Vectors, Inertial Momentum & Screen Wrapping | [`minigames/3.6_movement_camera/newtonian_toroidal_drifter.py`](minigames/3.6_movement_camera/newtonian_toroidal_drifter.py) |
| `mg_3605_spring_arm_camera` | Third-Person Spring Arm 3D | **3 - Intermediate** | 3D | Spherical Orbit Camera & Occlusion Spherecast | [`minigames/3.6_movement_camera/third_person_spring_arm.py`](minigames/3.6_movement_camera/third_person_spring_arm.py) |
| `mg_3606_wall_run_parkour` | Wall Run & Parkour Cling 3D | **4 - Advanced** | 3D | Wall Surface Normal Raycasts & Kinetic Parkour | [`minigames/3.6_movement_camera/wall_run_parkour.py`](minigames/3.6_movement_camera/wall_run_parkour.py) |
| `mg_3607_trauma_shake` | Trauma Screen Shake Rig 2D/3D | **1 - Beginner** | 2D | Polynomial Trauma Math (Trauma^2 / Trauma^3) & Noise Decay | [`minigames/3.6_movement_camera/trauma_screen_shake.py`](minigames/3.6_movement_camera/trauma_screen_shake.py) |
| `mg_3608_arcade_kart_slip` | Arcade Kart Slip Angle 3D | **4 - Advanced** | 3D | Arcade Vehicle Steering, Lateral Friction & Drift Boost | [`minigames/3.6_movement_camera/arcade_kart_slip.py`](minigames/3.6_movement_camera/arcade_kart_slip.py) |
| `mg_3609_smart_framing_camera` | Smart Framing Virtual Camera 2D | **2 - Novice** | 2D | Lookahead Framing, Deadzones & Multi-Target Zoom | [`minigames/3.6_movement_camera/smart_framing_camera.py`](minigames/3.6_movement_camera/smart_framing_camera.py) |
| `mg_3610_dash_ghost_trail` | Kinematic Dash Ghost Trail 2D | **2 - Novice** | 2D | Directional Burst Dash, I-Frames & Alpha Trails | [`minigames/3.6_movement_camera/dash_ghost_trail.py`](minigames/3.6_movement_camera/dash_ghost_trail.py) |
| `mg_3611_rts_camera_rig` | RTS Strategic Camera Rig 2D | **2 - Novice** | 2D | Screen-Edge Panning, Glide Momentum & Minimap Teleport | [`minigames/3.6_movement_camera/rts_camera_rig.py`](minigames/3.6_movement_camera/rts_camera_rig.py) |
| `mg_3612_tbs_ap_path_noodle` | TBS Action Point Path Noodle 2D | **3 - Intermediate** | 2D | A* Grid Pathfinding, AP Cost Preview & Elevation Traversal | [`minigames/3.6_movement_camera/tbs_ap_path_noodle.py`](minigames/3.6_movement_camera/tbs_ap_path_noodle.py) |

</details>

<details>
<summary><b>Section 3.7: Puzzle, Stealth & Other (13 prototypes)</b></summary>

| ID | Title | Difficulty | Dim | Demonstrated Patterns | Target File |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `mg_3701_sokoban_deadlock` | Sokoban Deadlock Solver 2D | **3 - Intermediate** | 2D | Command Pattern Undo/Redo & Heuristic Deadlock Detection | [`minigames/3.7_puzzle_stealth/sokoban_deadlock.py`](minigames/3.7_puzzle_stealth/sokoban_deadlock.py) |
| `mg_3702_stealth_lux` | Stealth Lux Illumination 3D | **3 - Intermediate** | 3D | Light Sampling Sensor & Stance Multipliers | [`minigames/3.7_puzzle_stealth/stealth_lux_illumination.py`](minigames/3.7_puzzle_stealth/stealth_lux_illumination.py) |
| `mg_3703_fluid_automata` | Fluid Cellular Automata 2D | **3 - Intermediate** | 2D | Falling Sand Simulation & Liquid Equalization | [`minigames/3.7_puzzle_stealth/fluid_cellular_automata.py`](minigames/3.7_puzzle_stealth/fluid_cellular_automata.py) |
| `mg_3704_lockpick_sweet_spot` | Lockpick Sweet Spot 2D | **1 - Beginner** | 2D | Angle Deviation Thresholds & Tension Vibration | [`minigames/3.7_puzzle_stealth/lockpick_sweet_spot.py`](minigames/3.7_puzzle_stealth/lockpick_sweet_spot.py) |
| `mg_3705_rhythm_judgment` | Rhythm Judgment Track 2D | **1 - Beginner** | 2D | Millisecond Audio Sync & Hit-Window Tolerances | [`minigames/3.7_puzzle_stealth/rhythm_judgment_track.py`](minigames/3.7_puzzle_stealth/rhythm_judgment_track.py) |
| `mg_3706_prism_laser_network` | Prism Beam Network 2D | **3 - Intermediate** | 2D | Raycast Laser Splitters, Color Filters & Receptors | [`minigames/3.7_puzzle_stealth/prism_beam_network.py`](minigames/3.7_puzzle_stealth/prism_beam_network.py) |
| `mg_3707_match3_cascade` | Cascading Match-3 Engine 2D | **3 - Intermediate** | 2D | Grid Swap Adjacency, Flood Clear & Gravity Refill | [`minigames/3.7_puzzle_stealth/match3_cascade_engine.py`](minigames/3.7_puzzle_stealth/match3_cascade_engine.py) |
| `mg_3708_time_rewind` | Circular Time Rewind 2D | **3 - Intermediate** | 2D | Fixed-Memory Ring Buffer & Reverse Playback | [`minigames/3.7_puzzle_stealth/circular_time_rewind.py`](minigames/3.7_puzzle_stealth/circular_time_rewind.py) |
| `mg_3709_pipe_pressure` | Pipe Circuit Pressure 2D | **2 - Novice** | 2D | Grid Breadth-First Search (BFS) Connectivity & Flow | [`minigames/3.7_puzzle_stealth/pipe_circuit_pressure.py`](minigames/3.7_puzzle_stealth/pipe_circuit_pressure.py) |
| `mg_3710_tactile_juice` | Tactile Juice Sandbox 2D | **1 - Beginner** | 2D | Game Feel Micro-Interactions (Squash, Tween, Shake) | [`minigames/3.7_puzzle_stealth/tactile_juice_sandbox.py`](minigames/3.7_puzzle_stealth/tactile_juice_sandbox.py) |
| `mg_3711_marquee_selector` | Marquee Box Multi-Selector 2D | **2 - Novice** | 2D | Screen-Space Bounding Box Query & Selection State | [`minigames/3.7_puzzle_stealth/marquee_box_selector.py`](minigames/3.7_puzzle_stealth/marquee_box_selector.py) |
| `mg_3712_initiative_timeline` | Dynamic Initiative Timeline 2D | **2 - Novice** | 2D | Grandia-Style Action Timeline & Cast Interruption | [`minigames/3.7_puzzle_stealth/dynamic_initiative_timeline.py`](minigames/3.7_puzzle_stealth/dynamic_initiative_timeline.py) |
| `mg_3713_territory_influence` | Territory Influence Border 2D | **3 - Intermediate** | 2D | Cellular Cultural Influence & Voronoi Border Expansion | [`minigames/3.7_puzzle_stealth/territory_influence_border.py`](minigames/3.7_puzzle_stealth/territory_influence_border.py) |

</details>

---

## 💡 The "No-Magic" C++ Porting Philosophy

In this repository, Python is used exclusively for its accessibility and instant iteration. We strictly avoid Python-only idioms so you can easily translate any pattern into **C++, C, C#, Rust, or Zig**:

```
❌ Forbidden in our code:            ✅ Used instead:
---------------------------------------------------------------------------------
No @dataclass or @property           Explicit struct-like classes with __init__
No generators (yield) or async       Explicit frame-by-frame update(dt) functions
No magic dunders (__call__, etc.)    Named methods (pool.get_slot(), add_vectors())
No per-frame list comprehensions     Pre-allocated fixed arrays & in-place loops
No dynamic getattr/eval/metaclasses  Direct field access and explicit integers
```

### Direct 1-to-1 Mapping to C++:

| Pattern Concept in this Repo (Python + `pyray`) | Equivalent Direct C++ Code (`raylib.h`) |
| :--- | :--- |
| `class Bullet:` with fields set in `__init__` | `struct Bullet { Vector2 pos; Vector2 vel; bool active; };` |
| `self.pool = [Bullet() for _ in range(600)]` | `std::array<Bullet, 600> pool;` |
| `for i in range(len(self.pool)):` with `if/else` | `for (int i = 0; i < pool.size(); ++i) { ... }` |
| `init_window(1280, 720, "Title")` | `InitWindow(1280, 720, "Title");` |
| `draw_sphere(pos, radius, color)` | `DrawSphere(pos, radius, color);` |

### 📏 Script Sizing Guidelines & Readability Criterion

To keep learning lightweight, modular, and directly portable without cognitive overload or token bloat, all code adheres to clear line budget guidance:

- **Minigames (Sections 3.0 to 3.7)**: Floor **300 lines**, Target **300–1,500 lines**, Hard ceiling **1,800 lines**.
- **Procedural Assets (SFX, BGM, 3D Models, 2D Sprites)**: Floor **200 lines**, Target **200–800 lines**, Hard ceiling **1,000 lines**.

> [!IMPORTANT]
> **Token Control & Pedagogical Integrity**:
> - Limits are guidance for token control and scope discipline.
> - **Never pad a file** to reach the floor with dummy code or artificial comments.
> - **Never compress code** or drop explanatory comments to fit under the ceiling.
> - **Readability Criterion**: A file must be understandable reading top to bottom, without jumping to other files; **clarity wins over line count**.

---

## 📊 CSV-Driven Dynamic Registries & Task Management

To maintain lightweight, token-efficient documentation and provide an intuitive workflow for both humans and AI subagents, all active inventories and task tracking are managed through four **spreadsheet-safe CSV files**:

| Registry Spreadsheet | Description & Content | Total Planned Items |
| :--- | :--- | :---: |
| [**`tasks/minigames.csv`**](tasks/minigames.csv) | All standalone prototypes across Sections 3.0 to 3.7 with difficulty ratings, patterns, and binary status | **106 prototypes** |
| [**`tasks/SFXs.csv`**](tasks/SFXs.csv) | Procedural SFX synthesizers across 6 modular categories | **73 SFX items** |
| [**`tasks/BGMs.csv`**](tasks/BGMs.csv) | Algorithmic streaming BGM tracks categorized by emotional vibe | **18 BGM tracks** |
| [**`tasks/models_3D.csv`**](tasks/models_3D.csv) | 3D procedural primitive models with primitives, animation, and palette keys | **29 models** |
| [**`tasks/sprites_2D.csv`**](tasks/sprites_2D.csv) | 2D procedural vector sprites with primitives, animation, and palette keys | **29 sprites** |

### 🛠️ How Humans Can Edit the CSV Files
To avoid unintentional formatting mistakes or character encoding changes when editing catalogs, use our built-in graphical editor:
```bash
python -B tasks.py
```
- **Guaranteed Schema Safety**: Columns `id` and `target_file` are protected and auto-generated, while column schema is immutable.
- **Pattern Verification**: Pick verified patterns straight from `rules/patterns.md` with zero typographical errors.
- **Desktop Spreadsheet Fallback**: You can also open `tasks/*.csv` in LibreOffice Calc, Excel, or Google Sheets with UTF-8 BOM encoding.
- **Alphanumeric explicit identifiers**: Keys like `mg_orbital_siege` and `"sec_3_0"` prevent Excel from auto-converting numbers into dates or truncated decimals.
- **Universal compatibility**: All text fields are RFC 4180 quoted and saved in UTF-8. The Python scripts automatically detect and accept both comma (`,`) and semicolon (`;`) separators as well as Windows Excel BOM headers.
- **Status column**: Strictly binary `pending` (target file absent from disk) and `done` (target file present on disk). Statuses are automatically synchronized across all 5 catalogs via `python -B tasks.py --sync-statuses`.

### ⚡ Automated Status Synchronization, Quality Gate & Fast CLI Queries
Subagents do not parse massive markdown catalogs, and craftsmen subagents never edit CSV task statuses manually. Instead, the Lead Orchestrator queries tasks using compact CLI calls (<50 tokens) and enforces an upfront **Asset Prerequisite Verification Gate** before assembling any minigame:

```bash
# 1. Synchronize disk presence across all task catalogs automatically:
python -B tasks.py --sync-statuses

# 2. Query minigames by difficulty tier:
python -B tasks.py --list minigames --difficulty beginner

# 3. Query the next pending task in a specific section:
python -B tasks.py --list minigames --section 3.2 --status pending --limit 1

# 4. Check asset prerequisites for a minigame (parses strictly id, status, description):
python -B tasks.py --check-prerequisites mg_301_orbital_siege

# 5. Read task summaries (id, status, description) across all catalogs:
python -B tasks.py --descriptions
```

- **Mandatory Quality Preservation Gate**: Whenever a user requests building minigames, the Orchestrator checks all asset catalogs (`SFXs.csv`, `BGMs.csv`, `models_3D.csv`, `sprites_2D.csv`) by reading strictly `id`, `status`, and `description`. If **even a single (1) required asset is missing or pending**, the Orchestrator halts craftsman invocation for that minigame, explains to the user which assets are missing, and details how withholding the craftsman preserves library quality (preventing inlined wave synthesizers, ad-hoc primitive drawings, or silent placeholders under Rule 10).
- **Craftsman Specification Injection**: Once all required visual and audio assets exist on disk (`status == done`), the Orchestrator spawns the craftsman subagent and injects exact asset contracts (`draw_<name>_3d`, `draw_<name>_2d`, `SFXS = [...]`, `BGMS = [...]`) into the subagent prompt.

---
---

# 🇪🇸 Guía en Español

## 🌟 ¿Qué es este proyecto?

Aprender la arquitectura interna de los videojuegos suele ser abrumador para quienes dan sus primeros pasos. Los motores comerciales como Unity, Unreal o Godot esconden la matemática y la lógica detrás de interfaces pesadas y descargas gigantescas, mientras que los tutoriales tradicionales suelen perder horas descargando modelos 3D, texturas y archivos de audio.

Este repositorio propone un método radicalmente distinto, claro y educativo:
1. **Cero Recursos Externos (Gráficos y Audio 100% Procedurales)**: Cada sprite 2D y modelo 3D articulado se construye en tiempo real mediante **primitivas geométricas** (esferas, cubos, cilindros, líneas y polígonos). Cada efecto de sonido y acorde musical se **sintetiza en memoria RAM** a partir de ondas matemáticas (senoidal, cuadrada, sierra). ¡No necesitas descargar ningún archivo de arte o audio!
2. **Laboratorios en un Solo Archivo**: Cada minijuego dentro de `minigames/` es 100% autónomo. Puedes abrir un archivo `.py`, leer cómo funciona el patrón, cambiar números y ver el resultado de inmediato.
3. **Lógica Pura y Traducible 1:1 a C++**: Utilizamos Python únicamente como **pseudocódigo ejecutable**. No hay "magia oculta" de Python (nada de decoradores extraños, generadores o comprensiones crípticas). Todo está escrito con estructuras simples, arreglos fijos e índices numéricos que puedes portar directamente a **C++, C, C#, Rust o Zig**.
4. **Soporte de Mando/Gamepad de Fábrica**: Conecta cualquier mando de videojuegos (Xbox, PlayStation o genérico USB) y funcionará automáticamente junto al teclado y ratón de forma simultánea.

---

## ✨ Características Interactivas de Aprendizaje

Cada prototipo incluye dos herramientas pedagógicas fundamentales:

> [!TIP]
> ### 🔬 1. El Inspector de Rayos X (`[Tab]` o Mando `Y` / `Triángulo`)
> Presiona **`[Tab]`** en cualquier momento para hacer transparentes los gráficos y ver la maquinaria matemática en tiempo real:
> - **Rejillas Espaciales (*Spatial Grid*)**: Observa cómo se iluminan las celdas de colisión al moverse los objetos.
> - **Reserva de Objetos (*Object Pool*)**: Inspecciona cuántos proyectiles están activos vs disponibles sin saturar la memoria.
> - **Cerebros de IA**: Observa los nodos activos de los Árboles de Comportamiento (*Behavior Trees*) y Máquinas de Estados (*FSM*).
> - **Vectores y Físicas**: Visualiza cápsulas de colisión 3D, líneas de visión (*Raycasts*) y vectores de aceleración.

> [!NOTE]
> ### 🎚️ 2. El Interruptor del Patrón (`[F1]` o Mando `LB` / `L1`)
> ¿Quieres entender *por qué* existe un patrón de diseño? Presiona **`[F1]`** para **DESACTIVARLO** en pleno juego:
> - Apaga el **Object Pool** y siente los tirones en los fotogramas cuando la memoria se asigna y destruye en bucle.
> - Apaga la **Rejilla Espacial** y observa cómo el procesador se satura al comparar colisiones de todos contra todos ($O(N^2)$).
> - Apaga la **Suavización de Cámara** y siente lo tosca que se vuelve la experiencia sin amortiguamiento matemático.
> - ¡Vuelve a pulsar **`[F1]`** para reactivar el patrón y comprobar la enorme mejora!

---

## 🚀 Guía Rápida para Principiantes (Paso a Paso)

¡No necesitas ser un experto ni tener compiladores complejos instalados! Solo requieres Python estándar:

### Paso 1: Instalar Python 3.10 o superior
1. Ingresa a la página oficial: [python.org/downloads](https://www.python.org/downloads/).
2. Descarga y ejecuta el instalador correspondiente a tu sistema operativo.
3. > [!IMPORTANT]
   > **En Windows**: En la primera pantalla del instalador, **marca obligatoriamente la casilla "Add python.exe to PATH"** antes de presionar Instalar. Esto te permitirá ejecutar comandos desde la terminal.

### Paso 2: Descargar o Clonar el Repositorio
- **Con Git**:
  ```bash
  git clone https://github.com/AXMAN/Game_Mechanics_Library.git
  cd Game_Mechanics_Library
  ```
- **Sin Git**: Haz clic en el botón verde **Code** arriba a la derecha en esta página de GitHub, selecciona **Download ZIP**, y descomprímelo en una carpeta de tu preferencia.

### Paso 3: Crear y Activar un Entorno Virtual
Un entorno virtual evita conflictos con otras versiones o librerías de tu equipo. Abre una terminal dentro de la carpeta del proyecto y ejecuta:

**En Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(Si PowerShell muestra un aviso de directiva de ejecución, escribe `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` y vuelve a activar).*

**En Windows (Símbolo del Sistema - CMD):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

**En macOS o Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Paso 4: Instalar Raylib (¡Única dependencia!)
Solo necesitamos la librería gráfica oficial de Raylib para Python (`pyray`):
```bash
pip install -r requirements.txt
```

---

## 🕹️ Cómo Jugar y Explorar

### Opción A: El Lanzador Visual Interactivo (`launcher.py`)
Es la manera más cómoda y recomendada de recorrer toda la enciclopedia:
```bash
python -B launcher.py
```
*(El modificador `-B` evita que Python genere carpetas temporales `__pycache__`).*

Dentro del lanzador podrás:
- Filtrar los minijuegos por categoría (**Menús e Interfaz**, **Combate**, **IA y Enemigos**, etc.).
- Leer el **Problema Resuelto** y la **Explicación Matemática** de cada patrón antes de jugar.
- Pulsar **`Enter`** o hacer clic en **`Launch Prototype`** para abrir el minijuego.
- Pulsar **`T`** o hacer clic en **`Run Smoke Test`** para realizar una prueba automática de 3 fotogramas.

### Opción B: Ejecutar Cualquier Minijuego Directamente
Cada minijuego es un archivo independiente. Puedes ejecutar el que desees directamente desde la terminal:
```bash
python -B minigames/<subcarpeta_de_categoria>/<nombre_del_script>.py

# Ejemplo:
# python -B minigames/3.0_core_prototypes/orbital_siege.py
```

### Opción C: El Editor Interactivo de Tareas y Hojas de Cálculo (`tasks.py`)
Para inspeccionar, editar, ordenar y agregar prototipos o recursos procedurales sin riesgo de corromper delimitadores CSV:
```bash
python -B tasks.py
```
- **Cambio de Catálogo en Caliente**: Alterna entre `minigames.csv`, `SFXs.csv`, `BGMs.csv`, `models_3D.csv` y `sprites_2D.csv`.
- **Columnas Técnicas Ocultas**: Mantiene `id` y `target_file` fuera de la vista para evitar errores humanos, generándolos fielmente al guardar.
- **Selector Modal de Patrones**: Asigna patrones de diseño directamente desde `rules/patterns.md` con búsqueda en vivo.

### Opción D: El Visualizador Interactivo de Recursos Procedurales (`assets/audio/asset_viewer.py`)
Para inspeccionar, escuchar, probar y experimentar con todos los recursos 100% procedurales del repositorio sin necesidad de abrir un minijuego:
```bash
python -B assets/audio/asset_viewer.py
```
- **4 Pestañas Especializadas por Tipo de Recurso**:
  - **Modelos 3D** (`assets/models_3D/`): Cámara orbital interactiva con ratón, reproducción/pausa de animaciones de marcha, parada/reinicio a 0.0s, velocidad, escala, rotación yaw, rejilla de suelo, modo alámbrico y paletas intercambiables (Default, Stealth, Cyberpunk, Desert).
  - **Sprites 2D** (`assets/sprites_2D/`): Lienzo interactivo con paneo y zoom, reproducción/pausa de animaciones vectoriales, dial de ángulo direccional ($0^\circ \dots 360^\circ$ / radianes), cuadrícula de transparencia (damero) y paletas intercambiables (Default, Neon, Crimson, Emerald).
  - **Efectos de Sonido SFX** (`assets/audio/SFX/`): Disparo instantáneo con `[Espacio]`, parada con `[S]`, modo bucle, barras de volumen y tono (pitch), osciloscopio en tiempo real con forma de onda PCM y cabezal de reproducción animado.
  - **Música BGM** (`assets/audio/BGM/`): Reproductor de audio en streaming con Play, Pausa, Reanudar, Parar, barra de tiempo interactiva (scrubber), volumen, tempo/tono, indicador de pulso de compás (BPM) y ecualizador gráfico animado de 24 bandas con medidores de picos.
- **Descubrimiento Dinámico en Memoria**: Alimentado directamente por `assets/audio/asset_loader.py`. Pulsa **`[F5]`** para reescanear el disco y detectar nuevos recursos al instante.
- **Fragmentos de Código para Minijuegos**: El panel inspector derecho muestra la llamada exacta en Python para importar y usar cualquier modelo, sprite o sonido en tus proyectos.
- **Prueba de Integridad Automatizada**: Ejecuta `python -B assets/audio/asset_viewer.py --smoke-test` para verificar las 4 pestañas y el streaming de audio en modo headless.

---

## 🎮 Controles Globales (Teclado, Ratón y Mando)

Todos los minijuegos responden a un esquema unificado de controles que combina teclado, ratón y gamepad al mismo tiempo:

| Acción | Teclado y Ratón | Mando / Gamepad |
| :--- | :--- | :--- |
| **Moverse / Navegar** | `W` `A` `S` `D` / Flechas del teclado | **Stick Analógico Izquierdo** (con zona muerta radial) o **D-Pad** |
| **Apuntar / Mirilla / Vista** | **Cursor del Ratón** / `Q` y `E` | **Stick Analógico Derecho** (apunta la mirilla o gira la cámara 3D) |
| **Acción Principal / Seleccionar** | `Espacio` / Clic Izquierdo / `Enter` | **Botón A** (Xbox) / **Cruz** (PlayStation) / Gatillo `RT` |
| **Acción Secundaria / Cancelar** | `Clic Derecho` / `Esc` / `Backspace` | **Botón B** (Xbox) / **Círculo** (PlayStation) / Gatillo `LT` |
| **🔬 Modo Rayos X (Telemetría)** | **`[Tab]`** | **Botón Y** (Xbox) / **Triángulo** (PlayStation) |
| **🎚️ Alternar Patrón (ON/OFF)** | **`[F1]`** | **Botón Superior Izquierdo (`LB` / `L1`)** |
| **🎛️ Parámetro / Toggle Secundario** | **`[F2]`** | **Botón Superior Derecho (`RB` / `R1`)** |
| **🔄 Reiniciar Simulación** | **`[R]`** | **Botón Start** (Xbox Menú / PlayStation Options) |
| **🔤 Ajustar Tamaño de Letra** | **`Ctrl + '+'`** / **`Ctrl + '-'`** | *Usa el menú desplegable superior* |
| **🖥️ Alternar Pantalla Completa** | **`[F11]`** | *Usa el menú desplegable superior* |

> [!TIP]
> ### ⚙️ La Barra Superior de Ajustes Globales
> Todas las ventanas del proyecto cuentan con una barra superior interactiva:
> - **`Font`**: Alterna en vivo entre la fuente pixelada clásica de Raylib y las fuentes TrueType de tu sistema (`Consolas`, `Segoe UI`, `Arial`, etc.).
> - **`Size`**: Ajusta el tamaño de la letra de toda la interfaz en vivo.
> - **`Win`**: Cambia la resolución (`1024x576`, `1280x720`, `1600x900`, `1920x1080`) o activa **Pantalla Completa (`F11`)**.
> - **`PAD Status`**: Indicador visual que te muestra en tiempo real si tu mando está conectado (`PAD: ON` vs `PAD: OFF`).
> 
> *Tus preferencias se guardan automáticamente en `config.json` para tus próximas partidas.*

---

## 🧩 Catálogo de Minijuegos y Patrones

El proyecto organiza sus minijuegos y laboratorios experimentales en subcarpetas temáticas dentro de [`minigames/`](minigames/):

| Sección | Subcarpeta de la Categoría | Dimensión y Alcance | Descripción del Contenido y Mecánicas |
| :---: | :--- | :---: | :--- |
| **3.0** | [`3.0_core_prototypes/`](minigames/3.0_core_prototypes/) | **2D / 3D Rebanadas Completas** | Bucles arcade y de estrategia multi-patrón que combinan 4+ sistemas (gravedad orbital, colosos con IK procedimental, taladros de excavación, combate espacial 6-DOF, táctica por turnos y estrategia RTS). |
| **3.1** | [`3.1_menus_ui/`](minigames/3.1_menus_ui/) | **2D / 3D Menús e Interfaces** | Arquitecturas de interfaz táctil y responsiva: pantallas diegéticas 3D, inventarios por poliominós, bancos de modificación modular con grafos DAG, ruedas radiales, libros de cuentas 4X maximalistas y navegación unificada ratón/táctil. |
| **3.2** | [`3.2_combat_weapons/`](minigames/3.2_combat_weapons/) | **2D / 3D Sistemas de Combate** | Balística de proyectiles cinéticos, morteros parabólicos, hitscan con penetración, resortes de retroceso y dispersión, recargas activas, arcos de daño por fotogramas (*frame data*), ventanas de parry y daño de área RTS. |
| **3.3** | [`3.3_enemies_ai/`](minigames/3.3_enemies_ai/) | **2D / 3D IA y Comportamientos** | Dirección autónoma de enemigos, bandadas *boids*, campos de flujo Dijkstra para hordas, árboles de comportamiento visualizados, tablas de amenaza *aggro*, jefes por fases y formaciones militares RTS. |
| **3.4** | [`3.4_progression_economy/`](minigames/3.4_progression_economy/) | **2D Economía y Progresión** | Modelos matemáticos de progresión: tablas de botín con muestreo CDF, curvas de nivel polinomiales/exponenciales, redes de crafteo DAG, simulador de *pity* gacha y flujos macroeconómicos 4X. |
| **3.5** | [`3.5_world_procgen/`](minigames/3.5_world_procgen/) | **2D / 3D Mundos y Entorno** | Generación procedimental y exploración: cavernas por autómatas celulares, mazmorras BSP, vóxeles 3D con DDA de Amanatides-Woo, niebla de guerra de doble capa y generación de biomas hexagonales. |
| **3.6** | [`3.6_movement_camera/`](minigames/3.6_movement_camera/) | **2D / 3D Físicas y Cámaras** | Sensación cinemática (*game feel*): Coyote time y almacenamiento de saltos (*jump buffer*), péndulos Verlet para garfios, controladores 3D tipo Quake, cámaras con resorte anti-oclusión y cámaras RTS. |
| **3.7** | [`3.7_puzzle_stealth/`](minigames/3.7_puzzle_stealth/) | **2D / 3D Lógica y Sigilo** | Lógica discreta e interacciones sistémicas: puzles Sokoban con detección de bloqueos y pila Deshacer/Rehacer, sensores de iluminación de sigilo, fluidos celulares, ganzúas y cajas de selección (*marquee*). |

---

## 💡 Filosofía "Cero Magia": Transferibilidad a C++

En este proyecto, Python se emplea exclusivamente por su velocidad de lectura y agilidad para iterar. Prohibimos expresamente cualquier truco exclusivo de Python para que puedas tomar cualquiera de estos algoritmos y portarlo línea por línea a **C++, C, C#, Rust o Zig**:

```
❌ Prohibido en este repositorio:          ✅ Utilizado en su lugar:
---------------------------------------------------------------------------------
Nada de @dataclass ni @property            Clases planas estilo struct con __init__
Nada de generadores (yield) ni async       Funciones de avance por fotograma update(dt)
Nada de métodos mágicos (__call__, etc.)   Métodos con nombre explícito (pool.get(), etc.)
Nada de comprensiones de lista por frame   Arreglos preasignados y bucles explícitos
Nada de metaprogramación dinámica          Acceso directo a variables y enteros
```

### Tabla de Traducción Directa a C++:

| Concepto en Python (`pyray`) | Código equivalente directo en C++ (`raylib.h`) |
| :--- | :--- |
| `class Bullet:` con variables en `__init__` | `struct Bullet { Vector2 pos; Vector2 vel; bool active; };` |
| `self.pool = [Bullet() for _ in range(600)]` | `std::array<Bullet, 600> pool;` |
| Bucles `for i in range(len(self.pool)):` con `if/else` | `for (int i = 0; i < pool.size(); ++i) { ... }` |
| `init_window(1280, 720, "Título")` | `InitWindow(1280, 720, "Título");` |
| `draw_sphere(pos, radio, color)` | `DrawSphere(pos, radio, color);` |

### 📏 Presupuesto de Líneas y Criterio de Legibilidad

Para que el aprendizaje sea ágil, modular y libre de sobrecarga cognitiva o dispersión de tokens, todo el código sigue directrices de tamaño claras:

- **Minijuegos (Secciones 3.0 a 3.7)**: Mínimo (*floor*) **300 líneas**, Objetivo (*target*) **300–1.500 líneas**, Techo máximo (*ceiling*) **1.800 líneas**.
- **Recursos Procedurales (SFX, BGM, Modelos 3D, Sprites 2D)**: Mínimo (*floor*) **200 líneas**, Objetivo (*target*) **200–800 líneas**, Techo máximo (*ceiling*) **1.000 líneas**.

> [!IMPORTANT]
> **Control de Tokens e Integridad Pedagógica**:
> - Los límites son pautas orientativas para el control de tokens y alcance.
> - **Nunca rellenes artificialmente un archivo** para alcanzar el mínimo con código innecesario o comentarios de relleno.
> - **Nunca comprimas código** ni elimines comentarios explicativos para forzarlo a caber bajo el techo máximo.
> - **Criterio de Legibilidad**: Cada archivo debe poder entenderse leyéndose linealmente de arriba hacia abajo, sin necesidad de saltar a otros archivos; **la claridad siempre triunfa sobre el conteo de líneas**.

### ⚡ Sincronización Automatizada de Estados, Control de Calidad de Activos y CLI
Los subagentes no leen catálogos masivos en Markdown ni editan estados manualmente. En su lugar, el Orquestador Principal ejecuta consultas CLI compactas (<50 tokens) y evalúa los prerrequisitos de activos antes de construir cualquier minijuego:

```bash
# 1. Sincronizar presencia de archivos en disco automáticamente:
python -B tasks.py --sync-statuses

# 2. Comprobar prerrequisitos de activos para un minijuego (lee estrictamente id, status y description):
python -B tasks.py --check-prerequisites mg_301_orbital_siege

# 3. Leer resúmenes de tareas (id, status, description) en todos los catálogos:
python -B tasks.py --descriptions
```

- **Filtro Estricto de Calidad**: Si falta incluso un solo ($1$) activo requerido (modelo 3D, sprite 2D, SFX o BGM), el Orquestador **detiene la invocación del subagente artesano**, explica al usuario qué activos faltan y cómo esta pausa preserva la calidad y modularidad del minijuego (Regla 10: Cero activos improvisados o incrustados en la lógica).
- **Inyección de Especificaciones**: Cuando todos los activos están listos (`status == done`), el Orquestador inyecta las especificaciones exactas (`draw_<name>_2d/3d`, `SFXS = [...]`, `BGMS = [...]`) directamente en el subagente artesano.

---
---

# 📁 Repository Map / Estructura del Proyecto

```text
Game_Mechanics_Library/
├── README.md                  # 📖 Este manual / Beginner's manual (English & Español)
├── AGENTS.md                  # 🤖 Reglas de arquitectura y plantilla pedagógica en 5 bloques
├── config.json                # ⚙️ Preferencias persistentes de interfaz (fuente, tamaño, ventana)
├── launcher.py                # 🚀 Lanzador visual interactivo y catálogo general
├── tasks.py                   # 📊 Editor gráfico interactivo de tareas y hojas de cálculo (Raylib GUI)
├── audit_minigame.py          # 🔍 Validador y auditor automatizado de calidad de minijuegos
├── tasks/                     # 📋 Directorio central de hojas de seguimiento CSV
│   ├── minigames.csv          #    106 prototipos planificados y construidos (Secciones 3.0 a 3.7)
│   ├── SFXs.csv               #    73 sintetizadores SFX procedurales (6 categorías)
│   ├── BGMs.csv               #    18 pistas BGM algorítmicas (12 vibras emocionales)
│   ├── models_3D.csv          #    29 modelos procedurales 3D
│   └── sprites_2D.csv         #    29 sprites vectoriales 2D
├── requirements.txt           # 📦 Única dependencia del proyecto: raylib (pyray)
├── rules/                     # 📜 Guías arquitectónicas, catálogos y patrones
│   ├── patterns.md            # 📚 Enciclopedia teórica de patrones de diseño de videojuegos
│   ├── minigames.md           # 📋 Registro detallado de todos los minijuegos construidos y planificados
│   ├── assets.md              # 🎨 Índice router de recursos y modelos procedurales
│   ├── audio.md               # 🎵 Registro de efectos de sonido (SFX) y música (BGM)
│   ├── models_3D.md           # 🧊 Registro de modelos 3D procedurales por primitivas
│   ├── sprites_2D.md          # 👾 Registro de sprites 2D procedurales por primitivas
│   └── utils.md               # 🧮 Documentación de colisiones no-nativas, rejillas y matemáticas
│
├── assets/                    # 🎨 Biblioteca de recursos matemáticos (¡Cero archivos externos!)
│   ├── __init__.py            #    Exportador central y registro de recursos procedurales
│   ├── models_3D/             #    Modelos 3D por primitivas (.gitkeep)
│   ├── sprites_2D/            #    Sprites 2D por primitivas geométricas animadas (.gitkeep)
│   └── audio/                 #    Sintetizadores de audio procedural en memoria RAM
│       ├── asset_loader.py    #    Universal dynamic asset discovery registry & loader
│       ├── asset_viewer.py    #    🎨 Visualizador e inspector interactivo de recursos (3D, 2D, SFX, BGM)
│       ├── synth_sfx.py       #    Registro dinámico y SoundLibrary de carga selectiva en RAM
│       ├── SFX/               #    Efectos de sonido procedurales por categoría
│       │   ├── combat/        #       SFX de combate y armas (.gitkeep)
│       │   ├── creature/      #       SFX de criaturas y monstruos (.gitkeep)
│       │   ├── environment/   #       SFX ambientales (.gitkeep)
│       │   ├── movement/      #       SFX de movimiento y locomoción (.gitkeep)
│       │   ├── progression/   #       SFX de progreso e ítems (.gitkeep)
│       │   └── ui_hud/        #       SFX de interfaz y HUD (.gitkeep)
│       └── BGM/               #    Pistas musicales algorítmicas por vibras emocionales
│           ├── calm/          #       Ambiente calmo y travesía (.gitkeep)
│           ├── cheerful/      #       Taberna alegre y festiva (.gitkeep)
│           ├── curious/       #       Puzle curioso e introspectivo (.gitkeep)
│           ├── eerie/         #       Mazmorra misteriosa y catacumbas (.gitkeep)
│           ├── energetic/     #       Acción enérgica, carreras y synth pulse (.gitkeep)
│           ├── futuristic/    #       Sintetizador ciberpunk futurista (.gitkeep)
│           ├── industrial/    #       Astillero y maquinaria industrial (.gitkeep)
│           ├── intense/       #       Jefes y asedio intenso (.gitkeep)
│           ├── mystical/      #       Misterio cósmico y espacial (.gitkeep)
│           ├── nostalgic/     #       Arcade retro y chiptune nostálgico (.gitkeep)
│           ├── suspenseful/   #       Sigilo y espionaje con suspenso (.gitkeep)
│           └── triumphant/    #       Fanfarria de victoria triunfante (.gitkeep)
│
├── utils/                     # 🧮 Utilidades matemáticas y de entrada
│   ├── __init__.py            #    Exportador central de utilidades y gestor de UI
│   ├── collisions.py          #    Cápsula rotada 3D/2D, SAT OBB y proyecciones de segmentos
│   ├── spatial_grid.py        #    Rejillas espaciales 2D y 3D (SpatialGrid2D / SpatialGrid3D)
│   ├── ai_pursuit.py          #    Algoritmos de dirección (Seek, Intercept), A* y línea de visión (LOS)
│   ├── math_helpers.py        #    Lerp, amortiguamiento (damp), curvas y temblor de cámara (TraumaShake)
│   ├── ui_settings.py         #    Barra superior con dropdowns de fuentes, tamaños (Ctrl +/-) y F11
│   └── gamepad_input.py       #    Mapeo simultáneo de Teclado/Ratón y Mando con zona muerta radial
│
└── minigames/                 # 🎮 Prototipos y laboratorios de aprendizaje clasificados
    ├── 3.0_core_prototypes/   #    Prototipos completos multi-patrón (.gitkeep)
    ├── 3.1_menus_ui/          #    Laboratorios de interfaz, menús e inventarios táctiles (.gitkeep)
    ├── 3.2_combat_weapons/    #    Sistemas de combate, balística y armas (.gitkeep)
    ├── 3.3_enemies_ai/        #    Comportamientos de enemigos e IA (.gitkeep)
    ├── 3.4_progression_economy/#   Economía, crafteo y progresión RPG (.gitkeep)
    ├── 3.5_world_procgen/     #    Generación procedimental de mundos (.gitkeep)
    ├── 3.6_movement_camera/   #    Físicas de movimiento y cámaras kinemáticas (.gitkeep)
    └── 3.7_puzzle_stealth/    #    Puzzles, sigilo y sistemas lógicos (.gitkeep)
```

---

# ❓ Frequently Asked Questions & Troubleshooting

### 🇬🇧 English FAQ
1. **PowerShell says "Execution of scripts is disabled on this system" when activating `.venv`:**  
   Run this single command in your PowerShell window:  
   `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`  
   Then run `.\.venv\Scripts\Activate.ps1` again.
2. **The window opens and closes immediately:**  
   Make sure you installed Raylib by running `pip install -r requirements.txt`. You can also run any minigame with the smoke test flag to verify errors:  
   `python -B minigames/3.0_core_prototypes/space_swarm.py --smoke-test`
3. **Why do we run scripts with `python -B`?**  
   The `-B` flag tells Python not to write bytecode `.pyc` files and `__pycache__` directories, keeping the repository spotless and lightweight.
4. **My gamepad is connected, but not responding:**  
   Check the top-right corner of the window. If it shows `PAD: OFF`, reconnect your controller via USB or Bluetooth. Once detected, the badge will switch to `PAD: ON [KB/M + Pad]`.

---

### 🇪🇸 Preguntas Frecuentes en Español
1. **PowerShell dice "La ejecución de scripts está deshabilitada en este sistema" al activar `.venv`:**  
   Ejecuta este comando en la ventana de PowerShell:  
   `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`  
   Luego vuelve a ejecutar `.\.venv\Scripts\Activate.ps1`.
2. **La ventana se abre y se cierra al instante:**  
   Asegúrate de haber instalado Raylib ejecutando `pip install -r requirements.txt`. Puedes verificar si hay algún error ejecutando la prueba de integridad:  
   `python -B minigames/3.0_core_prototypes/space_swarm.py --smoke-test`
3. **¿Por qué usamos `python -B` para ejecutar?**  
   El modificador `-B` le indica a Python que no genere carpetas temporales `__pycache__` ni archivos `.pyc`, manteniendo tu carpeta de trabajo limpia y sin basura.
4. **Mi mando está conectado pero el juego no responde:**  
   Revisa la esquina superior derecha de la ventana. Si dice `PAD: OFF`, desconecta y vuelve a conectar el mando por cable USB o Bluetooth. Al detectarlo, el indicador cambiará automáticamente a `PAD: ON [KB/M + Pad]`.

---

<div align="center">

**Happy Game Programming! / ¡Feliz Programación de Videojuegos!**  
*Built with ❤️ using Python & Raylib.*

</div>
