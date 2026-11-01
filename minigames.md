# Minigames Registry (`minigames/`)

This document is the official registry and tracking board for all experimental minigames.

---

## 1. Golden Architecture Rules for Minigames

1. **Single File Requirement**: Every minigame in `minigames/` must be a **single, standalone Python script** (e.g., `minigames/space_swarm.py`). It must be runnable on its own via `python -B minigames/<script_name>.py` and testable headlessly via `python -B minigames/<script_name>.py --smoke-test`.
2. **Modular Imports Allowed**: Each minigame script must enforce zero bytecode and import from `assets` and `utils`:
   ```python
   import sys
   import os
   sys.dont_write_bytecode = True
   sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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
5. **Two Prototype Scales (Do Not Overengineer Single-Pattern Labs)**:
   - **Multi-Pattern Minigames (Section 3)**: 600–900 lines combining 4+ patterns into a full arcade loop (**max 1 per prompt**).
   - **Single-Pattern Labs (Sections 3.1–3.7)**: 250–450 lines focused on **1 pattern in isolation**, starting immediately in the interactive sandbox without menu boilerplate (**1 to 2 per prompt**).
6. **Simultaneous Keyboard/Mouse & Gamepad Controls**: Every minigame must support Keyboard/Mouse and Gamepad simultaneously via `utils/gamepad_input.py` (`get_dual_move_2d`, `get_dual_look_2d`, `is_dual_*`, `draw_gamepad_status_badge`), activating gamepad input automatically whenever a controller is detected without disabling Keyboard/Mouse.
7. **Registration & Smoke Test Mandatory**: Every time a new minigame is created, verify it with `python -B minigames/<script_name>.py --smoke-test` and log it in Section 2 below. Also launch `python -B launcher.py` from the repository root to browse all built prototypes interactively.

---

## 2. Active Minigames Registry

| Section | Minigame File | Dim | Design Patterns Demonstrated (from `patrones.md`) | Assets & Utils Used | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **3.0** | [`minigames/space_swarm.py`](minigames/space_swarm.py) | 2D | Object Pool, Spatial Partitioning (`SpatialGrid2D`), Camera Rig (`TraumaShake`), State Machine (FSM), Wave Director | `draw_flying_drone_2d`, `SoundLibrary`, `SynthMusicPlayer`, `SpatialGrid2D`, `TraumaShake`, `get_dual_move_2d` | Built |
| **3.0** | [`minigames/mecha_colosseum.py`](minigames/mecha_colosseum.py) | 3D | Behavior Trees, Kinematic Character Controller, Audio Synthesis, Object Pool, Camera Rig | `draw_quadruped_beast_3d`, `draw_turret_boss_3d`, `SoundLibrary`, `SynthMusicPlayer`, `TraumaShake`, `closest_point_on_segment_2d`, `get_dual_move_2d` | Built |
| **3.0** | [`minigames/drone_defense_3d.py`](minigames/drone_defense_3d.py) | 3D | Rotated Capsule Collisions, State Machine (FSM), Camera Rig (`TraumaShake`), Object Pool | `draw_drone_enemy_3d`, `draw_humanoid_enemy_3d`, `draw_turret_boss_3d`, `SoundLibrary`, `Capsule3D`, `check_collision_capsules_3d`, `closest_points_between_segments_3d`, `TraumaShake`, `get_dual_look_2d` | Built |
| **3.1** | [`minigames/title_screen_cursor.py`](minigames/title_screen_cursor.py) | 2D | Vertical Menu with Cursor, Command Pattern / Action Dispatcher, Damped Cursor Rig | `draw_humanoid_enemy_2d`, `SoundLibrary`, `damp`, `get_dual_move_2d`, `draw_gamepad_status_badge` | Built |
| **3.1** | [`minigames/weapon_wheel.py`](minigames/weapon_wheel.py) | 2D | Radial Menu, Sector Partitioning, Time Dilation (Bullet-Time), Deadzone Hysteresis | `draw_humanoid_enemy_2d`, `SoundLibrary`, `damp`, `normalize_2d`, `draw_ring`, `get_dual_move_2d` | Built |
| **3.1** | [`minigames/tabbed_status_menu.py`](minigames/tabbed_status_menu.py) | 2D | Tabbed Menu (Sub-View Strategy), Animated Indicator Rig, Dynamic Stat Calculation Pipeline | `draw_humanoid_enemy_2d`, `SoundLibrary`, `damp`, `get_dual_move_2d`, `draw_gamepad_status_badge` | Built |
| **3.1** | [`minigames/attache_case.py`](minigames/attache_case.py) | 2D | Grid Inventory (Fixed-Matrix Cell Storage), Decoupled Hand Slot State Machine, Declarative Recipe Combine Engine | `SoundLibrary`, `damp`, `get_dual_move_2d`, `draw_gamepad_status_badge` | Built |
| **3.1** | [`minigames/tetris_backpack.py`](minigames/tetris_backpack.py) | 2D | Shape-Packing Inventory (Polyomino Grid Storage), Discrete 90° Clockwise Rotation, First-Fit Decreasing Auto-Pack Solver, Adjacency Synergy Pipeline | `SoundLibrary`, `get_dual_move_2d`, `draw_gamepad_status_badge`, `draw_ui_settings_bar` | Built |
| **3.1** | [`minigames/overloaded_mule.py`](minigames/overloaded_mule.py) | 2D | Weight-Based Inventory & Dynamic Encumbrance Physics, Tiered Movement Modulator, Companion Pack Mule Offload, Leash Steering | `draw_humanoid_enemy_2d`, `SoundLibrary`, `damp`, `get_dual_move_2d`, `draw_gamepad_status_badge`, `draw_ui_settings_bar` | Built |
| **3.1** | [`minigames/paper_doll.py`](minigames/paper_doll.py) | 2D | Equipment Slots (Paper Doll Architecture), Two-Handed Mutual Exclusion, Pure Derived Stat Pipeline, Multi-Tier Set Synergy Engine | `SoundLibrary`, `damp`, `draw_gamepad_status_badge`, `draw_ui_settings_bar` | Built |
| **3.1** | [`minigames/gear_compare.py`](minigames/gear_compare.py) | 2D | Stat Comparison Tooltip, Side-by-Side Dual Cards, Delta Contrast Pipeline, Smart Viewport Clamping | `SoundLibrary`, `damp`, `draw_gamepad_status_badge`, `draw_ui_settings_bar` | Built |
| **3.1** | [`minigames/merchant_stall.py`](minigames/merchant_stall.py) | 2D | Shop Buy/Sell Screen, Atomic Transaction Pipeline, Sell-Back Markdown & Arbitrage Prevention, Bulk Quantity Stepper | `draw_humanoid_enemy_2d`, `SoundLibrary`, `get_dual_move_2d`, `draw_gamepad_status_badge`, `draw_ui_settings_bar` | Built |
| **3.1** | [`minigames/workbench.py`](minigames/workbench.py) | 2D | Crafting Recipes (Dependency Graph DAG), Dynamic Ingredient Gating, Atomic Deduction Pipeline, Recursive Sub-Crafting | `SoundLibrary`, `get_dual_move_2d`, `draw_gamepad_status_badge`, `draw_ui_settings_bar` | Built |
| **3.1** | [`minigames/skill_web.py`](minigames/skill_web.py) | 2D | Skill Tree & Web (DAG Reachability), 4-State Visual Lifecycle, Anti-Refund Orphan Protection, Pure Derived Stats | `SoundLibrary`, `get_dual_move_2d`, `draw_gamepad_status_badge`, `draw_ui_settings_bar` | Built |
| **3.1** | [`minigames/minimap_compass.py`](minigames/minimap_compass.py) | 3D | Minimap and Compass Navigation Architecture, Heading-Up vs North-Up Projections, Edge-Pinning Clamping, 360° Compass Strip Tape | `draw_humanoid_enemy_3d`, `draw_drone_enemy_3d`, `SoundLibrary`, `damp`, `damp_v3`, `get_dual_move_2d`, `get_dual_look_2d`, `draw_gamepad_status_badge`, `draw_ui_settings_bar` | Built |

---

## 3. Planned Minigame Prototypes & Pattern Mapping

When asked to create new minigames, consult this catalog of ideas demonstrating specific game design patterns:

| Concept Name | Dimension | Target Patterns | Description |
| :--- | :--- | :--- | :--- |
| **Arena Survivor 2D** | 2D | Spatial Partitioning, Object Pool, Steering Behaviors | Top-down survival arena with hundreds of slime/crawler enemies steered by Reynolds behaviors, managed with `SpatialGrid2D`. |
| **Drone Defense 3D (built)** | 3D | Rotated Capsule Collisions, State Machine (FSM), Camera Rig | First-person or third-person 3D turret defending against articulated 3D drones and humanoids using capsule-capsule collisions. |
| **Dungeon Labyrinth** | 2D | Pathfinding (A* / BFS), Sensory Line-of-Sight, Command Pattern | Tile grid labyrinth where patrolling guards use A* pathfinding and line-of-sight raycasts to hunt the player. |
| **Mecha Colosseum 3D (built)** | 3D | Behavior Trees, Kinematic Character Controller, Audio Synthesis | Boss arena fighting against a quadruped beast and heavy turret boss with procedural audio feedback. |
| **Bullet Hell / Space Swarm (built)** | 2D | Object Pool, Double Buffering, Trauma Screen Shake | Swarms of rotating flying sentinels firing projectile patterns with quadratic screen shake and laser synthesis. |

---

### Extended Catalog: Single-Pattern Prototypes

The five prototypes above mix several patterns. The catalog below follows the project guideline of **one main pattern per minigame** (250–450 lines each), so each pattern can be felt and inspected in isolation. Same columns as above.

Rules for using this catalog:
- **Batch Limit**: Build **1 to 2 prototypes per prompt** (max 3 if simple 2D in the same section) so every file receives full pedagogical comments, an interactive `[Tab]` X-Ray overlay, and an `[F1]` comparison toggle.
- **Reuse First**: Pick a row, then check `assets.md` and `utils.md` before writing anything (reuse, do not duplicate).
- **Sync `patrones.md`**: If a pattern name is missing from `patrones.md`, add it there in the same task.
- **Keep the Pattern Visible**: Implement the pattern's core logic inside the `BLOCK 1: CORE PATTERN IMPLEMENTATION` section of the minigame (with an `[F1]` on/off toggle and `[Tab]` debug overlay) instead of hiding it inside `utils/`.
- **Smoke Test & Register**: Run `python -B minigames/<script_name>.py --smoke-test`, register it in Section 2, and mark its row below with a `(built)` suffix on its Concept Name.

#### 3.1 Menus & UI

| Concept Name | Dimension | Target Patterns | Description |
| :--- | :--- | :--- | :--- |
| **Title Screen Cursor (built)** | 2D | Vertical Menu with Cursor | Title/pause menu navigated with arrows or W/S, wrap-around at the ends, highlighted option, blip sound on move and confirm. |
| **Weapon Wheel (built)** | 2D | Radial Menu | Hold a key to open a ring of weapon slices; the mouse angle picks a slice; time slows down while the wheel is open. |
| **Tabbed Status Menu (built)** | 2D | Tabbed Menu | RPG-style menu with Items / Equipment / Skills / Status tabs switched with Q/E and a different layout per tab. |
| **Attaché Case (built)** | 2D | Grid Inventory | Fixed grid where every item takes one cell; move, swap, examine and combine items (herb + herb), Resident Evil style. |
| **Tetris Backpack (built)** | 2D | Shape-Packing Inventory | Items have different block shapes, rotate with R, and are rejected when they do not fit in the remaining space. |
| **Overloaded Mule (built)** | 2D | Weight-Based Inventory | List inventory with a weight limit; going over the limit slows the player down and shows an encumbrance bar. |
| **Paper Doll (built)** | 2D | Equipment Slots | Head, torso, hands and accessory slots; equipping or unequipping updates the stat totals live. |
| **Gear Compare (built)** | 2D | Stat Comparison Tooltip | Hovering an item shows green and red arrows with the stat difference versus the currently equipped item. |
| **Merchant Stall (built)** | 2D | Shop Buy/Sell Screen | NPC shop with buy and sell prices, a sell-back discount, a gold counter and a quantity selector. |
| **Workbench (built)** | 2D | Crafting Recipes | Recipe list greyed out unless ingredients are owned; crafting consumes inputs and adds the result. |
| **Skill Web (built)** | 2D | Skill Tree | Nodes linked by prerequisites; spend points; locked, available and maxed visual states. |
| **Menu Stack** | 2D | Menu Stack (Push/Pop) | Pause menu opens submenus (Options, Audio, Controls); Esc pops one level at a time. |
| **Right-Click Menu** | 2D | Context Menu | Right-click an item or entity to open a small action list (Use, Drop, Inspect) next to the cursor. |
| **Hotbar** | 2D | Quick Slot Bar | Number keys and mouse wheel select slots; items are assigned from the inventory. |
| **Talking NPC** | 2D | Dialogue Tree | Branching conversation with player choices and flags that unlock or lock later options. |
| **Typewriter Textbox** | 2D | Typewriter Text Effect | Text appears letter by letter with a blip sound; a button speeds it up or skips it. |
| **Minimap & Compass (built)** | 3D | Minimap and Compass | 3D arena with a corner minimap and a compass strip showing the bearing to the objective. |
| **Fog of War Map** | 2D | Fog of War | Explored tiles stay revealed, unexplored tiles stay dark; separate full-screen map view. |
| **Quest Log** | 2D | Quest Tracker | Quests with states (new, active, done), objective counters and a tracked-quest HUD. |
| **Results Screen** | 2D | Results and Reward Screen | Score counts up, a rank letter is revealed, and loot appears one item at a time. |
| **Diegetic Cockpit** | 3D | Diegetic UI | Health and ammo are shown on the weapon or suit model inside the world instead of a flat overlay. |
| **Settings Menu** | 2D | Settings Menu (Sliders, Toggles, Remap) | Volume sliders, fullscreen toggle and key remapping built on the Command Pattern. |
| **Drag-and-Drop Inventory** | 2D | Drag and Drop | Pick items up with the mouse, ghost preview, valid/invalid slot highlight, swap on drop. |
| **Hover Tooltips** | 2D | Tooltip System | Delayed tooltip with rarity-colored title, stats and flavor text that stays inside the screen. |
| **Floating Damage Numbers** | 2D | Floating Combat Text | Numbers rise and fade, crits are larger, all backed by an object pool. |
| **Toast Notifications** | 2D | Notification Queue | Pickup and achievement toasts are queued and slide in and out, fed by an event queue. |
| **Scene Stack** | 2D | Game State Stack | Title, Gameplay, Pause and Game Over handled as a stack of scenes with fade transitions. |
| **Damage Direction HUD** | 3D | Directional Damage Indicator | Red arcs at the screen edge point toward where the hit came from. |
| **Health Bar Styles** | 2D | HUD Gauge Variants | Segmented, lagging (white chip damage) and heart-container health bars side by side. |
| **Interaction Prompt** | 3D | Contextual Interaction Prompt | A "Press E" prompt appears on the closest interactable object within range and in front of the player. |

#### 3.2 Combat & Weapons

| Concept Name | Dimension | Target Patterns | Description |
| :--- | :--- | :--- | :--- |
| **Hitscan Range** | 3D | Hitscan | Instant ray weapon with tracer line and impact spark; a toggle switches to slow projectiles for comparison. |
| **Cannon Lab** | 2D | Ballistic Projectile | Gravity-arc cannon with angle and power controls and a dotted trajectory preview. |
| **Shotgun Alley** | 2D | Spread Cone | Each shot fires several pellets in a random cone; the spread widens with distance. |
| **Recoil Range** | 3D | Recoil and Bloom | Automatic weapon whose crosshair kicks up and whose spread grows while firing, then recovers. |
| **Charge Cannon** | 2D | Charged Attack | Hold to charge, release for more damage; the color changes at each charge level. |
| **Reload Drill** | 2D | Magazine and Reload | Limited magazine, reload time and an active-reload timing bar that rewards a well-timed press. |
| **Sniper Nest** | 3D | Aim Down Sights / Zoom | Right-click zooms with a smaller FOV, slower sensitivity and breathing sway. |
| **Lock-On Arena** | 3D | Target Lock-On | A key locks onto the nearest enemy; the camera and strafing orbit around it. |
| **Combo Dojo** | 2D | Combo Chain with Input Buffer | Three-hit melee combo with buffered inputs and cancel windows. |
| **Parry Dojo** | 2D | Parry Timing Window | Enemy telegraphs a strike; pressing block inside a tight window staggers it. |
| **Stamina Shield** | 2D | Stamina-Gated Block | Blocking and dodging drain stamina; an empty bar breaks the guard. |
| **Grenade Toss** | 3D | Arc Throw with Area Damage | Arc preview, fuse timer and explosion radius with damage falloff. |
| **Ricochet Range** | 2D | Bouncing Projectile | Bullets reflect off walls with a limited bounce count; shows the reflection vector math. |
| **Cover Shooter** | 3D | Cover System | Snap behind low walls, peek out to shoot and blind-fire while enemies suppress. |
| **Headshot Dummies** | 3D | Hit-Zone Damage Multipliers | Head, torso and limbs use separate hit zones with different damage multipliers. |
| **Status Lab** | 2D | Status Effect Pipeline | Poison, burn, freeze and stun with stacking and refresh rules shown in a debug panel. |
| **Homing Missiles** | 2D | Homing Projectile | Missiles steer toward a target with a limited turn rate; flares let the player dodge them. |
| **Laser Mirrors** | 2D | Beam Reflection | Continuous laser bounces off rotatable mirrors to reach a target. |
| **Sword Arc** | 2D | Melee Swing Arc Hitbox | Arc-shaped hitbox with startup, active and recovery frames, drawn as a debug overlay. |
| **Hit Feedback Lab** | 2D | Hit-Stop and Knockback | Freeze frames, knockback, flash and shake on impact; each effect has its own toggle. |
| **Weapon Swap** | 3D | Weapon Switching with Draw Time | Swapping has a holster and draw delay, and each weapon keeps its own ammo. |
| **Ammo Types** | 2D | Ammo Type Switching | Normal, explosive and piercing bullets with different behaviors, cycled with a key. |
| **Railgun Range** | 3D | Piercing Hitscan | A single ray passes through several targets in a line with damage falloff per hit. |
| **Aim Assist Gallery** | 2D | Auto-Aim Assist | The aim snaps gently to enemies inside a cone; the strength is adjustable. |
| **Mine Layer** | 2D | Proximity Trigger Mines | Place mines that arm after a delay and explode when an enemy enters the trigger radius. |

#### 3.3 Enemies & AI

| Concept Name | Dimension | Target Patterns | Description |
| :--- | :--- | :--- | :--- |
| **Guard Route** | 2D | Waypoint Patrol | Enemies walk loops between waypoints, pausing to look around at each stop. |
| **Alert Ladder** | 2D | Alert-Level State Machine | A guard goes Idle, Suspicious, Alerted, Searching and back to Idle, with a visible alert meter. |
| **Flow Field Horde** | 2D | Flow Field / Dijkstra Map | Hundreds of enemies follow one shared distance map toward the player through a maze. |
| **Boid Birds** | 2D | Flocking (Boids) | Separation, alignment and cohesion with sliders to tune each force live. |
| **Telegraph Sniper** | 3D | Telegraphed Attack | A sniper draws a laser line for one second before firing, giving the player time to dodge. |
| **Juggernaut** | 3D | Tank Archetype with Armor Break | Slow, high-HP enemy; a stagger meter breaks its armor and exposes a weak point. |
| **Kamikaze Swarm** | 2D | Suicide Attacker | Fast enemies blink, then explode when close to the player. |
| **Summoner** | 2D | Spawner Enemy | An enemy keeps summoning minions; killing it dispels them. |
| **Three-Phase Boss** | 3D | Multi-Phase Boss | The boss changes its attack set at health thresholds, with a short transition each time. |
| **Boss Dance** | 2D | Memorizable Attack Pattern | A fixed sequence of telegraphed attacks that the player learns by repetition. |
| **Wave Defense** | 2D | Wave Manager with Spawn Budget | Timed waves with intermissions; each wave gets a point budget spent on enemy types. |
| **Adaptive Director** | 2D | Dynamic Difficulty (AI Director) | Spawn rate and enemy mix adapt to the player's health and recent hits. |
| **Tactics Grid** | 2D | Utility AI (Turn-Based) | Fire Emblem style enemy turns: each option (attack, heal, retreat, change weapon) gets a score and the best one is picked. |
| **Threat Table** | 3D | Aggro and Threat Table | Enemies attack whoever generated the most threat; includes a decoy ally scenario. |
| **Squad Flankers** | 2D | Blackboard Squad Tactics | Enemies share what they see through a blackboard and surround the player. |
| **Ghost Personalities** | 2D | Target-Tile Chaser Personalities | Four chasers with different target rules, in the style of Pac-Man ghosts. |
| **Ambush Mimic** | 3D | Ambush Trigger | A chest-like object turns hostile when the player gets close. |
| **Pack Hunters** | 2D | Predictive Intercept | Enemies aim at where the player will be and cut off the escape route. |
| **Nest and Leash** | 3D | Leash and Home Position | Enemies are tied to a home area and walk back when the player leaves it. |
| **Shield Bearers** | 2D | Directional Shield | An enemy blocks attacks from the front, so the player must flank. |
| **Healer Support** | 2D | Support Role Enemy | A healer keeps other enemies alive, teaching target priority. |
| **Fleeing Thief** | 2D | Flee and Evade Behavior | A thief grabs loot and runs away; the player must chase it down. |
| **Bullet Pattern Gallery** | 2D | Bullet Pattern Generators | Parametric spirals, rings and aimed fans, cycled with a key to compare. |

#### 3.4 Progression & Economy

| Concept Name | Dimension | Target Patterns | Description |
| :--- | :--- | :--- | :--- |
| **Loot Piñata** | 2D | Loot Table with Rarity Tiers | Dummies drop items with rarity colors by weight; a live histogram shows the real drop rates. |
| **Level-Up Curve** | 2D | XP and Level Curve | XP orbs fill a bar; compare linear and exponential level thresholds. |
| **Herb Mixer** | 2D | Item Combination | Combine herbs or ammo following a rule table (green + red = strong heal). |
| **Scrap Economy** | 2D | Buy/Sell Economy Loop | Sell loot and buy upgrades; prices move with supply and demand. |
| **Upgrade Bench** | 2D | Weapon Upgrade Tiers | Spend materials to upgrade a weapon; cost grows each tier and high tiers can fail. |
| **Lucky Spin** | 2D | Gacha with Pity Timer | A spin wheel with visible rates and a pity counter that guarantees a rare prize. |
| **Rogue Run** | 2D | Permadeath with Meta-Progression | Dying ends the run but currency is kept to buy permanent upgrades. |
| **Checkpoint Run** | 2D | Checkpoint and Save Point | Touch a flag to save a snapshot; death respawns the player there. |
| **Relic Stack** | 2D | Stackable Passive Items | Pickups modify stats or behavior and stack (Binding of Isaac style). |
| **Idle Forge** | 2D | Incremental Growth Curves | Generators with exponentially growing costs and offline-style time accumulation. |
| **Ability Loadout** | 2D | Ability Loadout with Cooldowns | Choose four abilities before the fight, each with its own cooldown. |
| **Durability Anvil** | 2D | Item Durability and Repair | Weapons wear out with use and can be repaired for a price. |
| **Gather Nodes** | 3D | Gather Nodes with Respawn Timer | Trees and rocks give resources and regrow after a timer. |
| **Card Duel** | 2D | Deck, Hand and Discard Cycle | Draw a hand, play cards for energy, discard, reshuffle when the deck is empty. |
| **Auto-Battler Board** | 2D | Auto-Battler Synergies | Place units on a board; fights run on their own and matching types give bonuses. |

#### 3.5 World & Exploration

| Concept Name | Dimension | Target Patterns | Description |
| :--- | :--- | :--- | :--- |
| **Voxel Sandbox** | 3D | Voxel Place and Break World | Place and mine cubes in a small chunked world, with a block hotbar. |
| **Noise Terrain** | 3D | Procedural Noise Terrain | Hills and valleys generated from layered noise with sliders for scale and octaves. |
| **Cave Automata** | 2D | Cellular Automata Generation | Random fill smoothed by neighbor rules into cave shapes, stepped one iteration at a time. |
| **Room-and-Corridor Dungeon** | 2D | Procedural Dungeon (BSP Rooms) | The map is split into rooms and connected by corridors; a key regenerates it. |
| **Lock and Key Castle** | 2D | Lock-and-Key Gating | Doors need keys or abilities found elsewhere, in the Metroidvania style. |
| **Day-Night Cycle** | 3D | Time-of-Day Cycle | Sun position, sky color and enemy behavior change over a day. |
| **Survival Meters** | 2D | Survival Needs | Hunger, thirst and temperature decay over time and affect health. |
| **Ship Hangar** | 3D | Modular Slot Customization | Add, remove and sell ship modules in slots (storage, weapons, engine) with live stat changes. |
| **Fuel and Jump Map** | 2D | Resource-Limited Route Planning | Plan jumps between star systems under a fuel limit. |
| **Chunk Streamer** | 3D | Chunk Streaming | Terrain chunks load and unload around the player, with a debug view of the active chunks. |
| **Hazard Biomes** | 3D | Environmental Hazard Zones | Hot, cold and toxic zones drain suit protection that must be recharged. |
| **Trigger Volumes** | 3D | Trigger Volume Events | Invisible zones start events such as doors, spawns and cutscenes; shown as a debug overlay. |
| **Destructible Terrain** | 2D | Destructible Terrain | Explosions carve holes in the ground (Worms style). |
| **Seeded Galaxy** | 2D | Seeded Procedural Generation | The same seed always creates the same star systems, in the spirit of No Man's Sky. |
| **Planet Hopper** | 3D | Procedural Planet Generation | Pick a seed to generate a planet's color, terrain scale and enemy density. |
| **Room Camera** | 2D | Screen-by-Screen Camera | The camera snaps from room to room, Zelda style. |

#### 3.6 Movement & Camera

| Concept Name | Dimension | Target Patterns | Description |
| :--- | :--- | :--- | :--- |
| **Platformer Feel** | 2D | Coyote Time, Jump Buffer and Variable Jump | A debug panel lets you toggle each forgiveness trick and feel the difference. |
| **Dash Gauntlet** | 2D | Dash with Cooldown and I-Frames | A dash with a cooldown ring and brief invulnerability through hazards. |
| **Grid Walker** | 2D | Grid-Based Movement | Step-by-step 4-direction and 8-direction movement with smooth tweening between tiles. |
| **Camera Modes** | 3D | First/Third-Person Switching | A key switches between first-person and third-person views of the same character. |
| **Raycaster Corridor** | 3D | Raycasting (Wolfenstein Style) | Walls rendered by casting one ray per screen column over a tile map. |
| **Grappling Swing** | 2D | Rope Constraint Pendulum | Shoot a rope to an anchor and swing with pendulum physics. |
| **Twin-Stick Arena** | 2D | Twin-Stick Controls | Move with WASD and aim with the mouse independently. |
| **Arcade Kart** | 3D | Arcade Vehicle Steering with Drift | Simple car with grip, drift and speed-based turning. |
| **Orbit Camera** | 3D | Orbit Camera with Collision | Third-person camera orbits the player and pulls in when a wall is in the way. |
| **Lane Runner** | 3D | Lane-Switching Endless Runner | Three lanes, jump and slide, with speed that rises over time. |
| **Gravity Flip** | 2D | Gravity Switching | A button flips gravity between floor and ceiling. |
| **Wall Jump** | 2D | Wall Slide and Wall Jump | Slide down walls and kick off them to climb a shaft. |
| **Asteroids Drift** | 2D | Screen Wrap and Inertia Thrust | Ship with thrust and inertia that wraps at the screen edges. |
| **Parallax Scroller** | 2D | Parallax Scrolling | Background layers move at different speeds to create depth. |
| **Slide Machine** | 3D | Movement State Machine | Walk, sprint, crouch and slide as states with clear transitions. |

#### 3.7 Puzzle, Stealth & Other

| Concept Name | Dimension | Target Patterns | Description |
| :--- | :--- | :--- | :--- |
| **Crate Pusher** | 2D | Push-Block Puzzle (Sokoban) | Push crates onto targets on a grid; rules are simple but levels get hard. |
| **Cone Stealth** | 2D | Vision Cone and Noise Detection | Guards see inside a cone and hear running; the player sneaks or hides. |
| **Tower Defense** | 2D | Tower Targeting Priority | Towers choose first, last, strongest or nearest target; the priority can be switched live. |
| **QTE Sequence** | 2D | Quick-Time Event | Prompts appear with a timer; a wrong or late press fails the sequence. |
| **Rhythm Lane** | 2D | Rhythm Timing Lanes | Notes fall to a hit line in sync with the synthesized music, with Perfect, Good and Miss judgments. |
| **Fishing Bar** | 2D | Timing Bar Minigame | Keep a moving marker inside a bar to reel in the catch. |
| **Lockpick** | 2D | Lockpicking Sweet Spot | Find the hidden sweet spot angle with feedback on how close you are. |
| **Hack Pipes** | 2D | Rotate-Tiles Puzzle | Rotate pipe tiles to connect the power source to the terminal before time runs out. |
| **Match Cascade** | 2D | Match-3 with Cascades | Swap tiles to match three; matches clear, tiles fall and chain reactions score more. |
| **Time Rewind** | 2D | Command Pattern Undo/Rewind | Hold a key to rewind the last seconds by replaying stored commands backward. |
| **Falling Blocks** | 2D | Piece Spawner with 7-Bag Randomizer | Classic falling pieces with a fair random bag and line clears. |
| **Simon Says** | 2D | Sequence Memory | Repeat a growing sequence of colors and tones. |
| **Snake** | 2D | Segment Following on a Grid | The body follows the head's path; eating adds a segment. |
| **Pong AI** | 2D | Paddle AI with Reaction Delay | The AI paddle has a tunable reaction delay and error, so difficulty is adjustable. |
| **Ghost Replay** | 2D | Input Recording and Replay | Record a run, then race against a translucent ghost of yourself. |
| **Particle Lab** | 2D | Particle System with Emitters | Fire, sparks, smoke and explosions built from emitters and an object pool. |
| **Juice Lab** | 2D | Game Feel (Juice) | Toggle squash and stretch, tweening, screen shake and sound on one simple action. |
| **Save and Load** | 2D | State Serialization | Save the game state to a JSON file and load it back. |
| **Pressure Plates** | 3D | Switch-and-Door Logic Puzzle | Plates, levers and doors combined with AND/OR logic. |