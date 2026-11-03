# Minigames Registry (`minigames/`)

This document is the official registry and tracking board for all experimental minigames.

---

## 1. Golden Architecture Rules for Minigames

1. **Single File Requirement**: Every minigame in `minigames/` must be a **single, standalone Python script** located inside its designated 3.x category subfolder (e.g., `minigames/3.0_core_prototypes/space_swarm.py` or `minigames/3.1_menus_ui/weapon_wheel.py`). It must be runnable on its own via `python -B minigames/<subfolder>/<script_name>.py` and testable headlessly via `python -B minigames/<subfolder>/<script_name>.py --smoke-test`.
2. **Modular Imports Allowed**: Each minigame script must enforce zero bytecode and import from `assets` and `utils`:
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
5. **Unified Sizing Limits & Strict Batch Scope**:
   - **Target Range**: **600 to 1,500 lines** per minigame script across all sections (3.0 through 3.7).
   - **Floor**: **600 lines minimum**. Every script must provide thorough novice-friendly comments, complete 5-block anatomy, dual input parity, and X-Ray overlays.
   - **Hard Ceiling**: **1,800 lines maximum**. Under NO circumstances may any minigame script exceed 1,800 lines (enforced automatically by `audit_minigame.py`).
   - **Batch Limits**: Build strictly **1 prototype per prompt** in standard requests. Multi-script requests (up to 8 per session) are strictly reserved for `/teamwork` autonomous sessions where tasks and sections are clearly specified, executed using role-specialized subagents following the Autonomous Teamwork Protocol (Sequential Isolated Craftsman Guild).
6. **Simultaneous Keyboard/Mouse & Gamepad Controls (Dual Input & Unified Pointer Parity)**:
   - Every minigame must support Keyboard/Mouse and Gamepad simultaneously via `utils/gamepad_input.py` (`get_dual_move_2d`, `get_dual_look_2d`, `is_dual_*`, `draw_gamepad_status_badge`), activating gamepad input automatically whenever a controller is detected without disabling Keyboard/Mouse.
   - For strategy and UI systems, ensure inputs are pointer-unified: interactions work identically with mouse clicks, drag gestures, and tap targets (minimum 44x44 pixel target bounds), without requiring touchscreen-only hooks (`on_touch`).
7. **Registration & Smoke Test Mandatory**: Every time a new minigame is created, verify it with `python -B audit_minigame.py minigames/<subfolder>/<script_name>.py` and `python -B minigames/<subfolder>/<script_name>.py --smoke-test` and log it in Section 2 below. Also launch `python -B launcher.py` from the repository root to browse all built prototypes interactively.

---

## 2. Active Minigames Registry

| Section | Minigame File | Dim | Design Patterns Demonstrated (from [patterns.md](patterns.md)) | Assets & Utils Used | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Section 3.0: Core Multi-Pattern | `minigames/3.0_core_prototypes/orbital_siege.py` | 2D | N-Body Gravitational Well, Object Pool, Spatial Partitioning (`SpatialGrid2D`), State Machine (FSM), Wave Director | `SoundLibrary`, `SpatialGrid2D`, `approach`, `clamp`, `gamepad_input`, `ui_settings` | Complete (1,627 lines) |
| Section 3.1: Menus & UI | `minigames/3.1_menus_ui/diegetic_wrist_comm.py` | 3D | Diegetic World-Space Interface, Damped Spring Parallax, Offscreen Texture Projection (FBO), Localized Radar Coordinate Pipeline | `draw_drone_enemy_3d`, `DEFAULT_DRONE_PALETTE`, `SoundLibrary`, `damp`, `lerp`, `clamp`, `gamepad_input`, `ui_settings` | Complete (1,685 lines) |
| Section 3.2: Combat & Weapons | `minigames/3.2_combat_weapons/ballistic_mortar_arc.py` | 2D | Parabolic Kinematics & Closed-Form Trajectory Solver, Object Pool, Destructible Heightfield Terrain | `SoundLibrary`, `TraumaShake`, `damp`, `clamp`, `gamepad_input`, `ui_settings` | Complete (1,287 lines) |
| Section 3.3: Enemies & AI | `minigames/3.3_enemies_ai/boid_flocking.py` | 2D | Reynolds Steering Behaviors (Separation, Cohesion, Alignment), Apex Predator Panic State, Spatial Partitioning (`SpatialGrid2D`), Polarization Order Metric | `SoundLibrary`, `SpatialGrid2D`, `clamp`, `gamepad_input`, `ui_settings` | Complete (1,295 lines) |
| Section 3.4: Progression & Economy | `minigames/3.4_progression_economy/cumulative_loot_pinata.py` | 2D | Cumulative Distribution Function (CDF) Sampling, Dynamic Magic Find Scaling, Bad Luck Pity Escalation, Chi-Square Goodness-of-Fit, Law of Large Numbers Empirical Histogram | `SoundLibrary`, `closest_point_on_segment_2d`, `distance_2d`, `clamp`, `gamepad_input`, `ui_settings` | Complete (1,565 lines) |
| Section 3.5: World & Procedural Generation | `minigames/3.5_world_procgen/cellular_caverns.py` | 2D | Cellular Automata Smoothing (4-5 Rule), Double-Buffered Ping-Pong State Stepping, Queue-Based BFS Flood-Fill Connectivity, Disconnected Pocket Culling | `SoundLibrary`, `damp`, `clamp`, `gamepad_input`, `ui_settings` | Complete (1,189 lines) |
| Section 3.6: Movement & Camera | `minigames/3.6_movement_camera/platformer_forgiveness.py` | 2D | Coyote Time, Jump Buffering, Variable Jump Height Cutoff, Apex Float Boost, Corner Ledge Nudge | `SoundLibrary`, `gamepad_input`, `ui_settings` | Complete (1,547 lines) |
| Section 3.7: Puzzle, Stealth & Other | `minigames/3.7_puzzle_stealth/sokoban_deadlock.py` | 2D | Command Pattern (Action Encapsulation, Undo/Redo Dual Stack), Heuristic Deadlock Detection (Corner Deadlocks, Wall Line Deadlocks, 2x2 Square Freeze Deadlocks) | `SoundLibrary`, `damp`, `clamp`, `gamepad_input`, `ui_settings` | Complete (1,607 lines) |

---

## 3. Planned Minigame Prototypes & Pattern Mapping

The following catalog presents a reimagined, comprehensive blueprint of video game design patterns, tactical gameplay loops, real-time/turn-based strategy architectures, and systemic mechanics. Each entry isolates a fundamental architectural problem, illustrates clean mathematical solutions, and provides a rich, tactile sandbox for interactive study.

---

### 3.0 Core Multi-Pattern Prototypes

These larger prototypes (600–900 lines) integrate 4 or more foundational patterns into complete, playable arcade or strategy loops. They demonstrate how decoupled systems (physics, AI, pools, audio, rendering pipelines) communicate cleanly without spaghetti dependencies.

| Concept Name | Dimension | Target Patterns | Description |
| :--- | :--- | :--- | :--- |
| **Orbital Siege 2D** (built) | 2D | N-Body Gravitational Well, Object Pool, Spatial Partitioning (`SpatialGrid2D`), State Machine (FSM), Wave Director | A top-down Newtonian physics arena where a central celestial mass exerts continuous gravitational pull on swarms of orbital drone raiders. Manage ship momentum, orbital slingshots, pre-allocated projectile pools, spatial collision hashing, and dynamic wave escalation. |
| **Titan Strider 3D** | 3D | Procedural Inverse Kinematics, Behavior Tree (BT), Rotated Capsule Collisions (`Capsule3D`), Multi-Phase Boss, Camera Rig (`TraumaShake`) | Third-person boss arena against a colossal quadruped walking behemoth whose legs plant dynamically on uneven terrain using ground-raycast IK. Players evade telegraphed stomps, target articulated joint capsules, and track boss aggression branches across three distinct damage phases. |
| **Subterranean Drill Rig 2D** | 2D | Destructible Tile Grid, A* Pathfinding Burrowers, Cellular Particle Fall, Resource Pressure Loop, Command Pattern | Pilot an industrial excavation drill down into layered geological strata. Mine precious mineral veins while bio-crawlers navigate carved tunnels via A* pathfinding. Falling loose gravel, drill heat management, and reversible hydraulic booster commands create constant mechanical tension. |
| **Gunship Interceptor 3D** | 3D | 6-DOF Inertial Flight Kinematics, Lead-Pursuit Intercept Math, Swept-Volume Raymarching, Spatial Partitioning (`SpatialGrid3D`), Audio Synthesis | Zero-G space dogfighting sandbox featuring full 6-degrees-of-freedom flight dynamics with thruster dampening. Dogfight against agile interceptors using real-time predictive lead target reticles, hitscan flak turrets, and procedural thruster audio synthesis. |
| **Chrono Infiltrator 2D** | 2D | Command Pattern (Circular History Ring Buffer), Raycast Vision Cones, Alert Level State Machine, Spatial Hashing (`SpatialGrid2D`) | Top-down tactical stealth espionage laboratory. Infiltrate high-security vaults patrolled by guards with dynamic raycast field-of-view cones and noise perception thresholds. Players record and rewind local timeline state up to 6 seconds to coordinate multi-switch bypasses and avoid patrols. |
| **Tactical Commander TBS 2D** | 2D | Hexagonal Axial Coordinate System, Action Points (AP) Budget, Bresenham Line-of-Sight Grid, Zone of Control (ZoC), Initiative Turn Queue | Turn-based tactical grid combat lab. Command a strike squad across a hex grid using axial coordinates $(q, r)$. Spend finite Action Points on movement, attacks, and overwatch stances, while evaluating cover mechanics, line-of-sight occlusion, and turn order initiative timelines. |
| **Frontline Outpost RTS 2D** | 2D | Marquee Box Selection, Multi-Agent Flow Field Pathfinding, Worker Harvesting FSM, Footprint Placement Grid, Dual-Layer Fog of War | Real-time strategy outpost simulation. Drag-select combat units with a marquee bounding box, order harvesters on an autonomous mining/deposit cycle, validate building placement footprints on an occupancy grid, and uncover dynamic dual-layer fog of war. |

---

### Extended Catalog: Single-Pattern Laboratories

The following sections (3.1 to 3.7) focus strictly on **single-pattern isolation** (600–1,500 lines per script, hard ceiling of 1,800 lines). Each lab starts directly in the interactive sandbox state, bypassing title screens to maximize pedagogical clarity. Every lab features a `[Tab]` telemetry overlay exposing internal data structures and an `[F1]` toggle to compare behavior with versus without the design pattern.

---

#### 3.1 Menus & Tactile UI

Explores diegetic interfaces, spatial menu navigation, micro-interactions, responsive HUD layouts, maximalist/minimalist dashboards, and cross-platform pointer interactions.

| Concept Name | Dimension | Target Patterns | Description |
| :--- | :--- | :--- | :--- |
| **Diegetic Wrist Comm** (built) | 3D | Diegetic World-Space Interface | Holographic 3D wrist terminal attached to the player's forearm bone. Displays vital statistics, ammo counters, and localized radar inside the 3D game world with projection angles and depth parallax rather than a static screen-space HUD. |
| **Micro-Inventory Grid** | 2D | Polyomino Cell Packing & First-Fit Heuristics | Grid inventory system where irregularly shaped equipment items occupy multi-cell blocks. Features discrete 90-degree rotations, drag-and-drop collision detection against occupied cells, and an automated First-Fit Decreasing auto-pack solver. |
| **Modular Weapon Workbench** | 2D | Socket-Attachment Graph & Pure Stat Pipeline | Weapon customization bench with receiver, barrel, magazine, optics, and stock sockets. Swapping modular parts recalculates derived weapon parameters (accuracy bloom, fire rate, recoil impulse, weight) through a pure functional stat recalculation pipeline. |
| **Tactical Lock-On Reticle** | 3D | Screen-Space Reticle Projection & Viewport Clamping | Project 3D enemy anchor coordinates into 2D screen space with smooth damping. Features viewport edge-clamping arrows for off-screen targets, target-switching hysteresis via stick deflection, and off-axis distance scaling. |
| **Radial Action Pie** | 2D | Angular Sector Partitioning & Bullet-Time Dilation | Hold-to-open 8-way radial selector. Pointer vector angle maps directly to discrete pie slices with inner deadzone rejection. Opening the wheel engages a global game-time dilation factor (0.1x bullet time) with smooth radial spring animations. |
| **Floating Combat Splats** | 2D | Zero-Allocation Pool & Trajectory Curves | Floating damage counter pool launching values along quadratic bezier arcs. Implements dynamic font scaling for critical strikes, color coding by elemental damage type, and batch recycling without frame-time allocations. |
| **Interactive Tech Constellation** | 2D | Directed Acyclic Graph (DAG) Reachability & Virtual Canvas | Interactive skill constellation with virtual canvas pan and zoom. Nodes unlock via prerequisite edge reachability, featuring locked, available, active, and master visual states, accompanied by anti-refund orphan node validation. |
| **Tactical Hotbar GCD** | 2D | Dual-Tier Global Cooldown (GCD) & Action Dispatcher | MMO-style quickslot hotbar demonstrating 1-second global cooldowns alongside individual spell cooldown sweep wipes. Supports drag-to-rebind slot assignments and keyboard/gamepad direct action dispatching. |
| **Dialogue Yarn Engine** | 2D | Branching Dialogue Tree & Conditional Gating | Node-based conversation engine featuring variable-driven dialogue branches, moral alignment condition checks, typewriter text streaming with cadence pitch shifts, and keyboard/gamepad dialogue choice selection. |
| **Audio-Visual Settings Rack** | 2D | Command Pattern & Persisted Setting Dispatcher | Clean settings panel with stepped volume sliders, window resolution selectors, fullscreen toggles, and live key/button remapping listeners, all backed by an atomic undoable Command architecture. |
| **Skyline Compass Strip** | 3D | Horizontal Degree Tape & Proximity Waypoint Projection | Skyrim-style 360-degree horizontal compass tape fixed to the top HUD. Renders objective markers, cardinal directions, and dynamic target icons with distance-based alpha fading and off-heading clamping. |
| **Lagging Chip Health Bar** | 2D | Multi-Tiered HUD Gauge & Catchup Damping | Triple-layered health gauge demonstrating instant hit depletion, delayed white-chip catchup lerp, animated damage tick markers, and overshield barrier overlays. |
| **4X Grand Strategy Ledger** | 2D | Maximalist Multi-Panel Dashboard & Column Sorting | Dense 4X empire management interface. Features collapsible side drawers, sortable multi-column province ledgers, demographic distribution charts, and economic deficit warnings designed for high information density. |
| **Immersive Minimalist Radial** | 2D | Minimalist HUD-Less Action Rings & Idle Fade | Zero-HUD game view where all interface elements remain invisible until interacting with world objects. Opening context rings displays concise icon options that scale with spring dampening and fade out on idle. |
| **Unified Pointer Viewport** | 2D | Cross-Platform Touch/Mouse Navigation & Virtual Canvas | Responsive viewport controller featuring inertial drag-panning, wheel/pinch zoom centered on cursor, and a thumb-friendly bottom dock with 48px square buttons optimized for both mouse and touch interaction. |
| **Isometric Tile Cursor** | 2D | Screen-to-Isometric Coordinate Inversion | 2D isometric diamond tile picker. Uses matrix inversion math to project screen pointer coordinates into discrete isometric $(x, y)$ tile coordinates, highlighting multi-tile selection rectangles with height elevation offsets. |
| **Hex Coordinate Inspector** | 2D | Axial & Cube Coordinate Space Math | Hexagonal grid telemetry lab displaying axial $(q, r)$ and cube $(x, y, z)$ coordinates. Demonstrates hex distance formulas, ring expansions, field-of-movement radii, and pointer snap math. |

---

#### 3.2 Combat & Weapons

Explores projectile kinematics, hit detection architectures, frame-data state machines, recoil dissipation, kinetic combat feedback, and strategy combat rules.

| Concept Name | Dimension | Target Patterns | Description |
| :--- | :--- | :--- | :--- |
| **Ballistic Mortar Arc** (built) | 2D | Parabolic Kinematics & Closed-Form Trajectory Solver | Artillery cannon calculating trajectory curves under gravitational acceleration and atmospheric drag. Displays real-time dotted predictive trajectory parabolas and solves required launch angles for given target coordinates. |
| **Hitscan Penetration Rig** | 3D | Multi-Stage Raycast & Material Density Attenuation | High-velocity sniper raycast penetrating consecutive collision slabs. Calculates residual energy loss, surface normal deflection angles, and exit-wound particle bursts based on material density parameters. |
| **Shotgun Dispersion Choke** | 2D | Gaussian Distribution Cone & Pellet Grouping | Shotgun pellet spawner comparing uniform random dispersion against Gaussian normal clustering. Interactive sliders tune choke tightness, distance spread degradation, and multi-pellet impulse summation against physics targets. |
| **Recoil Bloom & Recovery** | 3D | Exponential Spring Dissipation & Angular Bloom | Procedural recoil engine where continuous automatic fire adds pitch/yaw crosshair displacement and expands cone-of-fire bloom. Ceasing fire engages a damped spring return model with recovery hysteresis. |
| **Active Reload Timing** | 2D | Timing Window State Machine & Cooldown Modulation | Gears of War-style active reload sweep bar. Pressing reload within the narrow sweet-spot zone grants instantaneous ammo cycling and damage boost; missing the zone incurs an extended jam recovery penalty. |
| **Melee Frame Data Arc** | 2D | Frame-Accurate Attack Lifecycle & Swept Polygon Hitbox | Visualizes fighting game combat phases: Startup (invulnerable/vulnerable frames), Active (swept sector hitbox collision window), and Recovery (cancel windows into dash or block) with on-screen frame-step controls. |
| **Parry Timing & Stagger** | 2D | Counter-Window Detection & Poise Breakdown | Enemy telegraphed strikes require activating guard within a tight 6-frame parry window. Successful parries trigger hit-stop freeze frames, dynamic deflect sparks, and deplete enemy poise bars for critical vulnerability. |
| **Elemental Reaction Matrix** | 2D | Combinatorial Status Pipeline & Aura Persistence | Chemical combat reaction engine (e.g., Pyro + Hydro = Vaporize multiplier; Electro + Cryo = Superconduct defense shred; Cryo + Hydro = Freeze immobilize). Manages status aura decay timers and chained area-of-effect explosions. |
| **Predictive Intercept Targeter** | 3D | Quadratic Intercept Math & Lead Reticle Calculation | Computes the exact future meeting point between a projectile of finite speed and an accelerating 3D target. Renders the projected lead intercept crosshair for optimal targeting calculation. |
| **Proportional Navigation Missile** | 2D | Pro-Nav Guidance Laws & Countermeasure Decoys | Homing missile simulation utilizing Proportional Navigation guidance (LOS rate of change acceleration commands) to pursue agile evasive targets, complete with turn-rate clamping and flare decoy distraction logic. |
| **Specular Ricochet Laser** | 2D | Geometric Normal Reflection & Ray Marching | Continuous laser beam bouncing off rotatable specular mirror planes. Calculates incident ray vector reflections ($R = V - 2(V \cdot N)N$) across up to 10 bounces to trigger photoelectric target sensors. |
| **Impact Feel & Hit-Stop Lab** | 2D | Micro-Freeze Frame, Trauma Shake & White Flash | Deconstructs combat impact juice: independently toggle hit-stop duration (0 to 120ms freeze), screen shake trauma intensity, sprite white flash overlay, and directional knockback dampening. |
| **Modular Cartridge Hopper** | 2D | Strategy Pattern Projectile Dispatcher | Weapon system dynamically swapping cartridge strategies (Armor-Piercing, High-Explosive Frag, Cryo-Shatter, Bouncing Ricochet) at runtime without altering core weapon firing and cycling logic. |
| **Directional Shield Flank** | 2D | Angular Guard Arc & Dot Product Facing Check | Combatant equipped with a directional front riot shield. Uses vector dot products between shield facing and incoming bullet velocities to deflect frontal impacts while leaving the rear flank vulnerable to bypass attacks. |
| **Grid Zone of Control & Flank** | 2D | Zone of Control (ZoC) & Flanking Multiplier Matrix | Turn-based strategy combat simulator. Entering an adjacent enemy grid cell triggers a Zone of Control lock, trapping movement. Attacking an occupied enemy from rear or flank grid angles applies tactical damage multipliers. |
| **RTS Siege Battery Splash** | 2D | Ground-Target Ballistics & Quadratic Area Splash | Long-range siege artillery targeting ground coordinates. Simulates shell flight arc time, dispersion deviation radius, and quadratic blast damage falloff impacting all units within the detonation circle. |
| **Grid Supercover Raycaster** | 2D | Supercover Grid Traversal & Cover Mitigation | Tile-based line-of-sight raycaster. Traces visibility rays through grid cells, detecting whether targets benefit from low barricade cover (50% hit mitigation), high obstacle occlusion (100% blocked), or elevation bonuses. |

---

#### 3.3 Enemies & Autonomous AI

Explores autonomous steering, hierarchical decision-making, perception modeling, squad coordination, tactical combat choreography, and strategy AI routines.

| Concept Name | Dimension | Target Patterns | Description |
| :--- | :--- | :--- | :--- |
| **Boid Flocking & Predator Panic** (built) | 2D | Reynolds Steering Behaviors (Separation, Cohesion, Alignment) | Autonomous flocking simulation demonstrating Separation, Cohesion, and Alignment forces. Introducing an active predator entity causes the flock to dynamically split, scatter, and flee based on panic threshold radii. |
| **Dijkstra Flow Field Horde** | 2D | Flow Field / Distance Integration Grid | Unified navigation grid calculating distance integration vectors toward the player across complex obstacle geometry. Enables hundreds of autonomous horde entities to navigate efficiently without per-entity path searches. |
| **Tactical Cover & Flank AI** | 3D | Utility AI Cover Scoring & Line-of-Sight Evaluation | AI agents evaluate environmental cover nodes, scoring each spot based on player line-of-sight obstruction, flanking distance, and escape routes, dynamically advancing from cover to cover. |
| **Visualized Behavior Tree** | 2D | Hierarchical Behavior Tree (Selector, Sequence, Decorator) | Behavior tree governing guard patrol, suspicion investigation, and target pursuit. A real-time telemetry panel highlights the active running leaf node, success/failure returns, and condition decorators. |
| **Raid Boss Threat Table** | 3D | Aggro Table & Threat Accumulation Pipeline | MMO raid boss intelligence tracking an internal threat table. Simulates damage output, healing aggro, and taunt modifiers across multiple target entities, shifting focus dynamically as threat values decay. |
| **Multi-Stage Colossus Boss** | 3D | Multi-Phase State Machine & Attack Choreography | Colossal mechanical boss transitioning across 3 distinct combat phases at health thresholds. Each phase introduces new telegraphed attack routines (ground shockwaves, mortar barrages, sweeping sweep lasers) and exposed weak points. |
| **Ghost Pursuer Archetypes** | 2D | Diverse Target-Tile Targeting Heuristics | Pac-Man inspired AI lab implementing four distinct pursuers: Direct Aggressor (targets player position), Predictive Interceptor (targets 4 tiles ahead), Flanker (pincer maneuver), and Ambivalent Wanderer (roams when close). |
| **Squad Blackboard Coordination** | 2D | Shared Blackboard & Combat Token Allocation | Coordinated squad AI communicating via a shared blackboard. Distributes finite "attack tokens" to prevent enemies from dogpiling simultaneously, orchestrating suppressive fire while teammates execute flanking maneuvers. |
| **Stealth Sensory Cones** | 2D | Raycast Vision Polygons & Acoustic Hearing Rings | Perception system blending angular raycast vision cones (occluded by world geometry) with acoustic noise detection rings generated by player sprinting, jumping, and interacting. |
| **Dynamic Tension AI Director** | 2D | AI Director & Emotional Tension Curves | Left 4 Dead style director monitoring player stress metrics (health remaining, ammo reserves, combat intensity) to modulate horde spawn budgets between Build-up, Sustained Peak, and Relaxation phases. |
| **Telegraphed Hazard Forecast** | 2D | Attack Forecasting & Fill-Progress Telegraphs | Boss attack choreography displaying geometric danger zones (expanding circles, linear charge lanes, angular sweeping cones) with visible fill-up countdown meters before executing lethal damage. |
| **Territorial Leash Anchor** | 3D | Tether Radius & Soft Reset State Machine | RPG creature behavior tied to home territory anchors. Pursues targets up to a maximum leash radius, after which it enters an invulnerable sprint-return state back to its nest with health regeneration. |
| **RTS Formation Steering** | 2D | Rigid/Elastic Formation Slots & Offset Steering | Multi-unit military formations (Line, Wedge, Column, Box). Units calculate local formation slot offsets relative to squad leader facing, steering smoothly while dynamically reassigning slots when units die. |
| **TBS Utility Tactical Brain** | 2D | Goal-Oriented Action Utility Curves & Scoring | Turn-based AI selecting decisions (Advance, Seek Cover, Heal Ally, Flank, Hunker Down) by passing game state through mathematical response curves to evaluate action utility scores. |
| **Harvester Resource Cycle FSM** | 2D | Finite State Machine Worker Gathering Cycle | RTS worker unit state machine executing an autonomous resource gathering loop: `IDLE` -> `MOVE_TO_PATCH` -> `HARVEST` (duration timer) -> `RETURN_TO_BASE` -> `DEPOSIT` -> repeat. |

---

#### 3.4 Progression & Game Economies

Explores probabilistic loot distribution, mathematical character growth curves, crafting networks, dynamic trade economies, research tech trees, and item modifier pipelines.

| Concept Name | Dimension | Target Patterns | Description |
| :--- | :--- | :--- | :--- |
| **Cumulative Loot Piñata** (built) | 2D | Cumulative Distribution Function (CDF) Sampling & Histograms | Weighted loot drop engine sampling across 5 rarity tiers. Features interactive luck modifier sliders, magic find scaling, and a real-time 1,000-roll frequency distribution histogram validating probability accuracy. |
| **Mathematical XP Curves** | 2D | Level Progression Curves & Diminishing Returns | Interactive progression laboratory comparing Linear, Polynomial, and Exponential XP curves. Demonstrates level-up thresholds, stat allocation budgets, and soft/hard diminishing return caps on primary attributes. |
| **Crafting Dependency DAG** | 2D | Directed Acyclic Graph Recipe Solver & Atomic Deductions | Deep crafting synthesis system modeling multi-tier recipes. Validates ingredient availability, handles recursive sub-component crafting, and executes atomic inventory transactions preventing item duplication. |
| **Dynamic Merchant Exchange** | 2D | Supply & Demand Price Floating & Arbitrage Prevention | Merchant trading simulator where commodity buy and sell prices fluctuate based on local stock inventory levels, player trading volume, and regional shortages, with markdown spreads preventing infinite loops. |
| **Passive Relic Synergy Stack** | 2D | Observer Pattern Item Hook Pipeline | Rogue-like passive item system (Binding of Isaac style) where stackable relics register listeners to game events (`OnHit`, `OnTakeDamage`, `OnKill`), chaining status procs without hardcoded player dependencies. |
| **Gacha Pity Simulator** | 2D | Soft Pity Thresholds & 50/50 Guarantee Engine | High-rarity gacha pull simulator modeling baseline drop rates, soft pity probability ramp-ups after pull 70, hard guarantees at pull 90, and 50/50 banner mechanics with Monte Carlo aggregate roll testing. |
| **Weapon Integrity & Repair** | 2D | Item Durability Degradation & Scrap Salvage | Gear wear-and-tear mechanics featuring condition tiers (Pristine, Worn, Damaged, Broken) that degrade weapon stats, alongside repair material costs and scrap salvage yield pipelines. |
| **Deckbuilder Hand Cycle** | 2D | Deck, Hand, Discard & Exhaust Pile State Engine | Slay the Spire card flow modeling Draw Pile, Hand, Discard Pile, and Exhaust Pile. Features turn-based energy pools, card play action dispatching, end-of-turn discard sweeps, and reshuffle mechanics. |
| **Incremental Idle Forge** | 2D | Exponential Growth Curves & Offline Accumulation | Idle incremental engine modeling exponential generator costs ($Cost = Base \times 1.15^N$), tier upgrades, passive production rates, and mathematical calculation of offline accumulated resource gains. |
| **RPG Attribute Respec** | 2D | Primary-to-Secondary Derived Stat Pipeline | Character attribute allocation board (Strength, Agility, Intelligence, Vitality) feeding a pure derived stat pipeline (Attack Power, Critical Chance, Evasion, Mana Pool, Max Health) with full respec refund validation. |
| **RTS Tech Tree Research Lab** | 2D | Technology DAG Queue & Global Modifier Propagation | Strategy research tree. Manages research time queues, verifies building tier prerequisites (e.g. Barracks required for Armory), and propagates global stat buffs (Armor +1, Speed +10%) across active unit pools. |
| **4X Resource Flow Ledger** | 2D | Multi-Commodity Inflow/Outflow Matrix & Deficit Penalties | Macroeconomic simulator balancing Gold, Food, Energy, and Production. Calculates per-turn net yields, stockpile caps, trade route imports, and penalties triggered by resource deficits (e.g., famine starvation). |

---

#### 3.5 World & Procedural Generation

Explores algorithmic terrain generation, cellular automata, dungeon carving, voxel raymarching, infinite chunk streaming, fog of war, and structural placement validation.

| Concept Name | Dimension | Target Patterns | Description |
| :--- | :--- | :--- | :--- |
| **Cellular Automata Caverns** (built) | 2D | Cellular Automata Smoothing & Flood-Fill Connectivity | Generates organic cave systems using 4-5 rule cellular automata. Features step-by-step iteration controls, birth/survival neighbor sliders, and flood-fill flood algorithms that detect and eliminate disconnected cavern pockets. |
| **BSP Dungeon Architect** | 2D | Binary Space Partitioning (BSP) & Room Linkage | Procedural interior layout generator recursively splitting partitions into a binary tree. Places rooms with randomized margins inside leaf nodes and connects sibling rooms via L-shaped hallway corridors. |
| **Voxel Raymarching DDA** | 3D | Fast Voxel Traversal (Amanatides-Woo DDA) & Hidden Face Culling | Interactive 3D voxel sandbox. Utilizes Amanatides-Woo 3D Digital Differential Analyzer (DDA) raymarching for instant block selection, placement, and removal, with hidden-face culling optimizing rendered geometry. |
| **Infinite Chunk Streamer** | 2D | Hash Grid Spatial Streaming & Memory Management | Infinite terrain streamer loading, rendering, and unloading spatial chunks around a moving camera. Demonstrates coordinate spatial hashing, dirty chunk persistence caching, and active memory budgets. |
| **Layered Noise Heightmap** | 3D | Multi-Octave Fractal Noise Terrain & Normal Baking | 3D heightfield terrain generated by combining base noise frequency, lacunarity, persistence, and octave layers. Provides live sliders to tune terrain ruggedness, water table cutoffs, and slope-dependent vertex shading. |
| **Dynamic Celestial Orbit** | 3D | Day-Night Celestial Orbit & Sky Dome Gradient | Atmospheric lighting system orbiting directional sun and moon vectors. Updates ambient light temperatures, dynamic shadow projections, starry sky gradients, and activates nighttime-specific world hazards. |
| **Hazardous Biome Suit** | 3D | Environmental Hazard Zones & Exposure Decay | Planetary hazard simulation featuring Cryo, Thermal, and Radiation hazard zones. Standing in hostile regions drains environmental suit shielding, driving players to find thermal vents or shelter before health depletes. |
| **Destructible Terrain Mask** | 2D | Bitmask Terrain Deformation & Sand Physics | Destructible 2D terrain (Worms style) where explosions carve circular craters out of the terrain bitmap, causing unsupported loose sand particles to tumble downward under cellular gravity rules. |
| **Lock-and-Key Ability Gate** | 2D | Metroidvania Progression Graph & Reachability | Structural level progression graph where access to dungeon chambers requires specific traversal capabilities (Double Jump, Grappling Hook, Wall Climb, Bomb), validating non-linear reachable routing. |
| **Infinite Lane Obstacle Runner** | 3D | Segment Pooling & Dynamic Obstacle Weaving | Endless 3-lane runner architecture utilizing a pre-allocated pool of road segments. Spawns procedural obstacle configurations (hurdles, barriers, ramps) that increase in frequency as world speed scales. |
| **Dual-Layer Fog of War** | 2D | Three-State Visibility Bitmask & Dynamic Sight Radii | RTS fog of war system managing three visibility states per tile: Unexplored (pure black), Shrouded (explored terrain but hidden units), and Visible (currently illuminated by unit sight circles). |
| **Hex World Biome Generator** | 2D | Procedural Hex Map & Elevation Moisture Matrix | World map generator on a hex grid. Combines Perlin height elevation and moisture maps to assign hex biomes (Ocean, Tundra, Grassland, Desert, Mountains) with procedural river path generation. |
| **RTS Building Placement Grid** | 2D | Multi-Cell Footprint Clearance & Ghost Snapping | Construction placement preview. Snaps building ghost silhouettes (e.g. 1x1, 2x2, 3x3) to the terrain grid, validating against terrain slope, path obstructions, and fog of war discovery before confirming build orders. |

---

#### 3.6 Movement, Physics & Camera Rigs

Explores platforming forgiveness mechanics, kinematic character controllers, pendulum constraints, inertial drifting, strategic RTS cameras, and grid path preview rigs.

| Concept Name | Dimension | Target Patterns | Description |
| :--- | :--- | :--- | :--- |
| **Platformer Forgiveness Lab** (built) | 2D | Coyote Time, Jump Buffering & Corner Assist | The gold standard of 2D kinematic platforming feel. Isolate and test individual player-forgiveness mechanics: Coyote Time, Jump Buffering, Variable Jump Height Cutoff, Apex Float Boost, and Corner Ledge Nudge. |
| **Pendulum Grappling Cable** | 2D | Verlet Rope Integration & Angular Momentum Swing | Fire a grappling cable to attach to ceiling anchors and swing under gravity. Demonstrates rigid pendulum constraints, rope wrapping around corner collision pins, and momentum-conserving releases. |
| **Kinematic Character Rig** | 3D | Ground Friction, Air Strafe & Ledge Step-Up | First-person Quake-style kinematic movement controller. Features snappy ground acceleration, air strafe velocity manipulation, slope sliding thresholds, and automatic micro-step climbing over low obstacles. |
| **Newtonian Toroidal Drifter** | 2D | Thruster Vectors, Inertial Momentum & Screen Wrapping | Asteroids-style spacecraft physics demonstrating directional thrust impulses, rotational inertia, linear drag decay, and seamless screen-edge coordinate wrapping across a toroidal 2D plane. |
| **Third-Person Spring Arm** | 3D | Spherical Orbit Camera & Occlusion Spherecast | Third-person camera rig orbiting the player character via spherical coordinates (pitch, yaw, distance). Uses sphere-cast collision checks to automatically pull the camera forward when walls occlude the view. |
| **Wall Run & Parkour Cling** | 3D | Wall Surface Normal Raycasts & Kinetic Parkour | Wall-running controller using horizontal raycasts to detect adjacent wall surfaces, nullifying vertical gravity while applying forward velocity and outward wall-kick impulse vectors. |
| **Trauma Screen Shake Rig** | 2D/3D | Polynomial Trauma Math ($Trauma^2$ / $Trauma^3$) & Noise Decay | Implements Squirrel Eiserloh's classic trauma screen shake algorithm. Converts trauma values (0.0 to 1.0) through quadratic/cubic curves to drive translational and rotational camera offsets with linear decay. |
| **Arcade Kart Slip Angle** | 3D | Arcade Vehicle Steering, Lateral Friction & Drift Boost | Simplified arcade racing vehicle dynamics. Models forward propulsion, lateral tire grip slip angles, drift-initiate hopping, and tiered drift-spark mini-turbo boosts upon exiting turns. |
| **Smart Framing Virtual Camera** | 2D | Lookahead Framing, Deadzones & Multi-Target Zoom | Smooth camera director featuring velocity-based lookahead, soft deadzone margins, damped lerp tracking, and dynamic bounding-box zooming that keeps multiple combatants in frame (Smash Bros style). |
| **Kinematic Dash Ghost Trail** | 2D | Directional Burst Dash, I-Frames & Alpha Trails | High-speed directional dash mechanic granting temporary invulnerability frames (I-frames), obstacle phase-through capabilities, and a trailing buffer of fading alpha afterimage sprites. |
| **RTS Strategic Camera Rig** | 2D | Screen-Edge Panning, Glide Momentum & Minimap Teleport | Top-down strategy camera navigation. Supports edge-screen scrolling, drag-panning with velocity inertia, zoom-to-cursor scaling, camera bounds clamping, and instant teleportation via minimap clicks. |
| **TBS Action Point Path Noodle** | 2D | A* Grid Pathfinding, AP Cost Preview & Elevation Traversal | Tactical grid path preview. Clicking a target tile computes the shortest A* path, drawing a dashed path noodle with beads indicating step-by-step Action Point consumption and elevation climb costs. |

---

#### 3.7 Puzzle, Stealth & Systemic Interactions

Explores discrete grid rules, reversible command stacks, stealth lighting sensors, fluid cellular automata, rhythm audio hit-windows, marquee selection, and initiative timelines.

| Concept Name | Dimension | Target Patterns | Description |
| :--- | :--- | :--- | :--- |
| **Sokoban Deadlock Solver** (built) | 2D | Command Pattern Undo/Redo & Heuristic Deadlock Detection | Grid-based push-block puzzle featuring an unlimited reversible Command stack (Undo/Redo). Telemetry overlay highlights heuristic deadlock traps (corner deadlocks, wall deadlocks) the instant a block becomes unmovable. |
| **Stealth Lux Illumination** | 3D | Light Sampling Sensor & Stance Multipliers | Stealth visibility detector calculating the player's exposure from world light sources. Multiplies light intensity by player stance (Standing, Crouching, Crawling) to drive enemy detection rates. |
| **Fluid Cellular Automata** | 2D | Falling Sand Simulation & Liquid Equalization | Grid-based cellular fluid simulation modeling gravity, lateral liquid dispersion, and immiscible fluids (Water, Oil, Acid, Lava), complete with phase change reactions (Lava + Water = Obsidian). |
| **Lockpick Sweet Spot** | 2D | Angle Deviation Thresholds & Tension Vibration | Skyrim-style cylinder lockpicking minigame. Rotate pick to discover the randomized sweet-spot angle; turning the tension wrench tests proximity, vibrating and stressing the pick if angled incorrectly. |
| **Rhythm Judgment Track** | 2D | Millisecond Audio Sync & Hit-Window Tolerances | Vertical rhythm note highway synchronized to procedural in-memory audio beats. Compares input timestamps against note arrival frames, awarding Perfect, Great, Good, and Miss judgments with visual hit bursts. |
| **Prism Beam Network** | 2D | Raycast Laser Splitters, Color Filters & Receptors | Optical puzzle where continuous laser beams reflect off rotatable mirrors, pass through colored crystal filters, and split into multiple branches to power target receptor diodes simultaneously. |
| **Cascading Match-3 Engine** | 2D | Grid Swap Adjacency, Flood Clear & Gravity Refill | Match-3 puzzle engine validating adjacent tile swaps, clearing horizontal and vertical triplets, dropping suspended tiles under gravity, and resolving chain reaction combo multipliers. |
| **Circular Time Rewind** | 2D | Fixed-Memory Ring Buffer & Reverse Playback | Braid-inspired time reversal. Continuously records player position, velocity, animation frames, and world states into a fixed-capacity circular ring buffer, replaying history backward seamlessly on command. |
| **Pipe Circuit Pressure** | 2D | Grid Breadth-First Search (BFS) Connectivity & Flow | Rotatable pipe conduit network. Uses Breadth-First Search (BFS) graph traversal to verify a continuous connected leak-free path from the high-pressure water pump to the cooling tower before time expires. |
| **Tactile Juice Sandbox** | 2D | Game Feel Micro-Interactions (Squash, Tween, Shake) | Interactive laboratory deconstructing the anatomy of "game juice" on a simple bouncy block: independently toggle squash-and-stretch scale deformations, easing curve tweens, particle puffs, and sound pitch shifts. |
| **Marquee Box Multi-Selector** | 2D | Screen-Space Bounding Box Query & Selection State | Real-time strategy unit selector. Dragging the pointer draws a rectangular marquee box selecting all friendly units whose coordinates lie within; supports Shift-click addition and Ctrl-click type selection. |
| **Dynamic Initiative Timeline** | 2D | Grandia-Style Action Timeline & Cast Interruption | Turn-based action queue visualizer. Units advance along a horizontal timeline bar toward the Action line; dealing damage to an enemy during their casting windup induces an "Interrupt" knockback backward along the timeline. |
| **Territory Influence Border** | 2D | Cellular Cultural Influence & Voronoi Border Expansion | 4X territorial expansion system. Cities emit cultural influence scores across adjacent grid tiles, dynamically recoloring ownership borders as influence waves overcome neighboring empire claims. |
