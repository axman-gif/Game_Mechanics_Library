# Utilities Registry (`utils/`)

This document is the official registry of non-native math, collision, spatial partitioning, and AI routines available in `utils/`.
**Rule for AI Agents & Developers**:
1. Always consult this file before implementing custom physics, math, pathfinding, or steering algorithms. Reuse existing utilities to maintain consistency and save tokens.
2. **C++ & Cross-Language Transferability**: All algorithms and data structures must be written using explicit struct-like classes, fixed/indexed arrays, and standard `for`/`while` loops—avoiding Python-only features (`@decorator`, `yield`, magic methods, or comprehension tricks) so learners can port them 1-to-1 to C++ and other game programming languages.

---

## 1. Quick Import Syntax

```python
# Import all utilities
from utils import *

# Or import by domain
from utils.collisions import Capsule3D, check_collision_capsules_3d, OBB2D, check_collision_obb_2d
from utils.spatial_grid import SpatialGrid2D, SpatialGrid3D, TileGrid2D
from utils.ai_pursuit import seek_2d, predict_intercept_2d, find_path_astar
from utils.math_helpers import damp, TraumaShake, ease_out_bounce
```

---

## 2. Non-Native Collisions (`utils/collisions.py`)

Raylib natively only checks basic axis-aligned bounding boxes (AABB) and upright cylinders. This module provides arbitrary 3D and 2D rotated collisions.

### 2.1 Rotated Capsule Collisions
A capsule is defined by its central line segment (start to end) and a radius:
- `Capsule3D(start: Vector3, end: Vector3, radius: float)`
- `Capsule2D(start: Vector2, end: Vector2, radius: float)`

#### Functions:
- `check_collision_capsules_3d(p1: Vector3, p2: Vector3, r1: float, q1: Vector3, q2: Vector3, r2: float) -> bool`:
  Computes the exact shortest distance between two 3D line segments. Returns `True` if $d \le r_1 + r_2$. Handles parallel, skew, and degenerate lines safely.
- `check_collision_capsule_sphere_3d(start: Vector3, end: Vector3, radius: float, sphere_pos: Vector3, sphere_radius: float) -> bool`:
  Tests 3D capsule vs 3D sphere.
- `check_collision_capsules_2d(p1: Vector2, p2: Vector2, r1: float, q1: Vector2, q2: Vector2, r2: float) -> bool`:
  2D rotated capsule vs capsule intersection.
- `check_collision_capsule_circle_2d(cap_start: Vector2, cap_end: Vector2, cap_radius: float, circle_center: Vector2, circle_radius: float) -> bool`:
  2D capsule vs circle collision.

### 2.2 Rotated Bounding Boxes (OBB via SAT)
- `OBB2D(center: Vector2, half_extents: Vector2, angle_radians: float)`
- `check_collision_obb_2d(obb1: OBB2D, obb2: OBB2D) -> bool`:
  Tests intersection between two arbitrary oriented rectangles using the Separating Axis Theorem (SAT).

### 2.3 Segment Math & Projections
- `closest_point_on_segment_3d(point: Vector3, seg_a: Vector3, seg_b: Vector3) -> Vector3`
- `closest_point_on_segment_2d(point: Vector2, seg_a: Vector2, seg_b: Vector2) -> Vector2`
- `closest_points_between_segments_3d(p1, p2, q1, q2) -> (c1, c2, distance)`
- `closest_points_between_segments_2d(p1, p2, q1, q2) -> (c1, c2, distance)`

---

## 3. Spatial Partitioning & Grid Maps (`utils/spatial_grid.py`)

### 3.1 `SpatialGrid2D(cell_size=64.0)`
Fast 2D spatial hash map reducing collision testing from $O(N^2)$ to $O(N)$.
- `clear()`: Clears grid buckets (call at the beginning of each frame).
- `insert(entity, x, y, radius=0.0)`: Registers entity into overlapping cells.
- `query_radius(x, y, radius) -> List[entity]`: Returns nearby entities within radius.

### 3.2 `SpatialGrid3D(cell_size=4.0)`
Fast 3D spatial hash map for 3D physics broadphase.
- `clear()`: Clears grid.
- `insert(entity, x, y, z, radius=0.0)`: Registers 3D entity.
- `query_sphere(x, y, z, radius) -> List[entity]`: Returns all nearby entities inside query sphere.

### 3.3 `TileGrid2D(cols, rows, cell_size=32.0, default_val=0)`
2D discrete tile map for labyrinths, walls, and pathfinding.
- `is_walkable(gx, gy) -> bool`: Checks if coordinate is in bounds and free (val == 0).
- `get_cell(gx, gy) -> int` / `set_cell(gx, gy, val)`
- `world_to_grid(wx, wy) -> (gx, gy)`: Continuous world coordinates to grid indices.
- `grid_to_world(gx, gy, center=True) -> (wx, wy)`: Grid indices to continuous coordinates.
- `get_neighbors(gx, gy, allow_diagonals=False) -> List[(gx, gy)]`: Returns traversable adjacent cells.

---

## 4. Artificial Intelligence & Pathfinding (`utils/ai_pursuit.py`)

### 4.1 Steering Behaviors
- `seek_2d(current_pos: Vector2, target_pos: Vector2, speed: float) -> Vector2`: Direct attraction.
- `flee_2d(current_pos: Vector2, threat_pos: Vector2, speed: float) -> Vector2`: Direct repulsion.
- `arrive_2d(current_pos: Vector2, target_pos: Vector2, max_speed: float, slowing_radius=80.0) -> Vector2`: Smooth deceleration without overshoot.
- `predict_intercept_2d(chaser_pos, target_pos, target_velocity, chaser_speed) -> Vector2`: Predicts future position (lead targeting) and steers to intercept.
- `wander_2d(current_angle: float, wander_jitter: float = 0.3) -> float`: Returns perturbed heading.
- `seek_3d(current_pos: Vector3, target_pos: Vector3, speed: float) -> Vector3`: 3D direct seek.
- `predict_intercept_3d(chaser_pos, target_pos, target_velocity, chaser_speed) -> Vector3`: 3D predictive intercept.

### 4.2 Sensory Perception
- `has_line_of_sight_grid(tile_grid, start_pos: Vector2, target_pos: Vector2) -> bool`:
  Bresenham DDA raycast verifying unobstructed vision against wall tiles.

### 4.3 Grid Pathfinding
- `find_path_astar(tile_grid, start_gx_gy, target_gx_gy, allow_diagonals=False) -> List[(gx, gy)]`:
  Shortest path using A* search with Manhattan/Octile heuristic.
- `find_path_bfs(tile_grid, start_gx_gy, target_gx_gy) -> List[(gx, gy)]`:
  Breadth-first search for unweighted maze navigation.

---

## 5. Math, Easing & Camera Helpers (`utils/math_helpers.py`)

### 5.1 Interpolation & Dampening
- `clamp(val, min_val, max_val) -> float`
- `lerp(a, b, t) -> float`
- `lerp_v2(a: Vector2, b: Vector2, t) -> Vector2` / `lerp_v3(a: Vector3, b: Vector3, t) -> Vector3`
- `approach(current, target, max_delta) -> float`: Steps toward target without overshooting.
- `damp(current, target, smoothing, dt) -> float`: Framerate-independent exponential smoothing.
- `damp_v2(...)` / `damp_v3(...)`: Framerate-independent vector smoothing.

### 5.2 Vectors & Angles
- `distance_2d(v1, v2) -> float` / `distance_3d(v1, v2) -> float`
- `normalize_2d(v) -> Vector2` / `normalize_3d(v) -> Vector3`
- `angle_to_vector_2d(angle_rad) -> Vector2`
- `vector_to_angle_2d(v: Vector2) -> float`

### 5.3 Easing Functions (Animations & Visuals)
- `ease_in_quad(t)` / `ease_out_quad(t)` / `ease_in_out_quad(t)`
- `ease_out_bounce(t)`: Bounces at end of motion.
- `ease_out_elastic(t)`: Spring overshoot.

### 5.4 Screen Shake (`TraumaShake`)
```python
shake = TraumaShake(max_offset_px=16.0, max_angle_deg=3.0, decay_rate=1.2)

# When an explosion happens:
shake.add_trauma(0.6)

# In update loop:
dx, dy, angle = shake.update(dt)
camera.target.x += dx
camera.target.y += dy
```

---

## 6. Global UI Settings, Font & Window Manager (`utils/ui_settings.py`)

Automatically exported when importing `from utils import *` after `from pyray import *`. Reads and writes user preferences to the root `config.json` file (`font_name`, `font_size_offset`, `window_size`, `fullscreen`).

### 6.1 Automatic Features in Every Minigame & Launcher
- **Top-Bar Dropdown Menus (`x = 450..978, y = 16..46`)**: Renders 3 interactive dropdowns on the top HUD layer before `end_drawing()`:
  1. **Font Family**: Select between `"Default (Pixel)"` and detected system TTF fonts (`Consolas`, `Segoe UI`, `Courier New`, `Arial`, `Verdana`, `DejaVu Mono`, etc.).
  2. **Font Size Offset**: Select size presets (`Small -4` to `Huge +8`) or adjust live with **`Ctrl + '+'`** and **`Ctrl + '-'`**.
  3. **Window Resolution**: Select `1024x576`, `1280x720`, `1600x900`, `1920x1080`, or **`Fullscreen (F11)`** (also toggleable at any time with **`F11`**).
- **Transparent Raylib Wrappers**:
  - `init_window`, `begin_drawing`, `end_drawing`, `begin_mode_2d`, `end_mode_2d`, `begin_mode_3d`, `end_mode_3d`, `begin_scissor_mode`, `end_scissor_mode`, `draw_text`, and `close_window` are automatically wrapped so every script written for `1280x720` scales seamlessly to any window resolution, borderless fullscreen, and renders text with the user's chosen font and size offset.
- **Explicit Positioning Helper**:
  - `draw_ui_settings_bar(x=450, y=16)`: Sets the top-bar dropdown coordinates for the current frame. Keep `x = 450..980, y = 14..48` unobstructed in your top HUD layout.

---

## 7. Simultaneous Keyboard/Mouse + Gamepad Input (`utils/gamepad_input.py`)

Provides **simultaneous dual-input multiplexing** so players can use **Keyboard & Mouse**, a **Gamepad (Controller)**, or **both at the same time** with automatic hot-plug detection (`is_gamepad_available(0..3)`) and scaled radial deadzones.

### 7.1 Hot-Plug Detection & Radial Deadzone
- `get_active_gamepad_id() -> int`: Returns the first connected gamepad slot (`0..3`), or `-1` if none is connected.
- `is_any_gamepad_connected() -> bool`: Returns `True` if at least one controller is connected.
- `get_active_gamepad_name() -> str`: Returns the human-readable controller name (clipped to 22 chars for HUD badges).
- `apply_radial_deadzone(axis_x: float, axis_y: float, deadzone: float = 0.18) -> tuple[float, float]`:
  Applies a scaled circular deadzone so resting stick drift is zeroed out while preserving full 360-degree analog control from `0.0` to `1.0`.
- `get_gamepad_left_stick(deadzone: float = 0.18) -> tuple[float, float]`
- `get_gamepad_right_stick(deadzone: float = 0.18) -> tuple[float, float]`
- `is_gamepad_trigger_down(is_right_trigger: bool = True, threshold: float = 0.25) -> bool`

### 7.2 Simultaneous Dual-Input Polling (Keyboard/Mouse OR Gamepad OR Both)
- `get_dual_move_2d(deadzone: float = 0.18, allow_arrow_keys: bool = True) -> tuple[float, float]`:
  Combines `WASD` (and optionally `Arrow Keys`), `Gamepad Left Stick`, and `Gamepad D-Pad` simultaneously. Clamps the resulting 2D vector magnitude to `1.0` so pressing both inputs never doubles movement speed.
- `get_dual_look_2d(deadzone: float = 0.18, allow_qe_keys: bool = True, allow_arrow_keys: bool = True) -> tuple[float, float]`:
  Combines keyboard turn keys (`Q`/`E`, `Left`/`Right`) with `Gamepad Right Stick`.
- `is_dual_primary_fire_down() -> bool` / `is_dual_primary_fire_pressed() -> bool`:
  `Mouse Left`, `Space`, `RT (Right Trigger)`, or `Gamepad X (FACE_LEFT)`.
- `is_dual_secondary_fire_pressed() -> bool`:
  `Mouse Right`, `LT (Left Trigger)`, `RB`, or `Gamepad B (FACE_RIGHT)`.
- `is_dual_jump_down() -> bool` / `is_dual_jump_pressed() -> bool`:
  `Space`, `Gamepad A (FACE_DOWN)`, or `LT`.
- `is_dual_dash_down() -> bool` / `is_dual_dash_pressed() -> bool`:
  `Left Shift`, `Right Shift`, `Gamepad B (FACE_RIGHT)`, or `LB`.
- `is_dual_xray_toggle_pressed() -> bool`: `[Tab]` or `Gamepad Y (FACE_UP)`.
- `is_dual_pattern_toggle_pressed() -> bool`: `[F1]` or `Gamepad LB (LEFT_TRIGGER_1)`.
- `is_dual_secondary_toggle_pressed() -> bool`: `[F2]` or `Gamepad RB (RIGHT_TRIGGER_1)`.
- `is_dual_reset_pressed() -> bool`: `[R]`, `Gamepad Select (MIDDLE_LEFT)`, or `Gamepad Start (MIDDLE_RIGHT)`.
- `draw_gamepad_status_badge(x: int = 985, y: int = 22, font_size: int = 12)`:
  Draws a live HUD indicator showing whether a controller is active alongside Keyboard & Mouse.

### 7.3 Canonical Controls Table

Single source of truth for gamepad and keyboard mapping:

| Action | Keyboard / Mouse | Gamepad (Xbox / PlayStation) |
|---|---|---|
| X-Ray Telemetry Overlay | `Tab` | `Y` (Triangle) |
| Pattern Toggle (ON/OFF) | `F1` | `LB` (L1) |
| Secondary Toggle / Parameter | `F2` | `RB` (R1) |
| Reset Simulation | `R` | `Start` |
| Font Size | `Ctrl +/-` | *(Top HUD Bar)* |
| Toggle Fullscreen | `F11` | *(Top HUD Bar)* |



