# Assets Registry (`assets/`)

This document is the official registry of all visual and audio components currently available in `assets/`.
**Rule for AI Agents & Developers**:
1. Always check this file before implementing any graphic rendering or audio synthesis code. Reuse existing assets whenever possible to avoid duplicate code and save tokens.
2. **C++ & Cross-Language Transferability**: Keep all procedural asset code free of Python-exclusive syntax (no decorators like `@dataclass`/`@property`, no `yield` generators, no complex comprehensions). Use explicit loops, basic trigonometric math (`sin`, `cos`), and standard Raylib primitive calls (`draw_sphere`, `draw_cube`, `draw_cylinder_ex`, `draw_circle`) so any developer can translate these procedural models directly into C++ or C#.

---

## 1. Quick Import Syntax

```python
# Import all assets
from assets import *

# Or import specific categories
from assets.models_3d import draw_humanoid_enemy_3d, draw_drone_enemy_3d
from assets.sprites_2d import draw_humanoid_enemy_2d, draw_slime_enemy_2d
from assets.audio import SoundLibrary, SynthMusicPlayer
```

---

## 2. 3D Procedural Primitive Models (`assets/models_3d/`)

All 3D models are constructed purely from geometric primitives (spheres, cubes, cylinders, rectangular prisms) with built-in procedural animation parameters.

### 2.1 `draw_humanoid_enemy_3d`
- **File**: `assets/models_3d/humanoid.py`
- **Primitives Used**: Spheres (head, joints), Rectangular Prisms / Cubes (pelvis, chest armor, feet), Cylinders (limbs, weapon pole).
- **Signature**:
  ```python
  draw_humanoid_enemy_3d(position: Vector3, rotation_y: float = 0.0, anim_timer: float = 0.0, scale: float = 1.0, is_attacking: bool = False, palette: dict = None)
  ```
- **Features**: Natural leg and arm swinging cycles, footstep bounce, chest breathing, weapon attack posture.
- **Palette Keys**: `armor`, `chest`, `joints`, `visor`, `weapon`, `energy`.

### 2.2 `draw_quadruped_beast_3d`
- **File**: `assets/models_3d/beast.py`
- **Primitives Used**: Cylinders (spine, legs, tail), Rectangular Prisms (torso, armor carapace, head, claws), Spheres (joints, glowing eyes, tail mace).
- **Signature**:
  ```python
  draw_quadruped_beast_3d(position: Vector3, rotation_y: float = 0.0, anim_timer: float = 0.0, scale: float = 1.0, palette: dict = None)
  ```
- **Features**: Synchronized 4-leg trotting gait, body bounce, swinging segmented tail, head bobbing.
- **Palette Keys**: `body`, `plates`, `joints`, `horns`, `eyes`.

### 2.3 `draw_drone_enemy_3d`
- **File**: `assets/models_3d/drone.py`
- **Primitives Used**: Spheres (core shell, glowing cyclops lens), Rectangular Prisms (4 X-wing stabilizer fins), Cylinders (wing struts, sensor domes, twin laser barrels).
- **Signature**:
  ```python
  draw_drone_enemy_3d(position: Vector3, rotation_y: float = 0.0, anim_timer: float = 0.0, scale: float = 1.0, palette: dict = None)
  ```
- **Features**: Levitation floating bob, directional tilt, pulsating core lens, underside twin guns.
- **Palette Keys**: `hull`, `trim`, `thruster`, `core`, `laser`.

### 2.4 `draw_turret_boss_3d`
- **File**: `assets/models_3d/turret.py`
- **Primitives Used**: Stepped Concentric Cylinders (base anchor rings, pivot collar, cannon barrels), Rectangular Prisms (hazard stripes, turret housing, ammo bunker, barrel shrouds), Spheres (top alarm beacon).
- **Signature**:
  ```python
  draw_turret_boss_3d(position: Vector3, yaw_deg: float = 0.0, pitch_deg: float = 0.0, anim_timer: float = 0.0, scale: float = 1.0, palette: dict = None)
  ```
- **Features**: Independent horizontal yaw rotation, vertical barrel pitch elevation, pulsating alarm beacon.
- **Palette Keys**: `base`, `armor`, `trim`, `barrel`, `beacon`.

---

## 3. 2D Procedural Primitive Sprites (`assets/sprites_2d/`)

All 2D sprites are drawn using Raylib 2D primitive render calls (`draw_circle`, `draw_rectangle`, `draw_line_ex`, `draw_triangle`).

### 3.1 `draw_humanoid_enemy_2d`
- **File**: `assets/sprites_2d/humanoid_2d.py`
- **Primitives**: Circles (head, shoulders, hands, feet), Lines (glowing visor slit, blade edge).
- **Signature**:
  ```python
  draw_humanoid_enemy_2d(position: Vector2, facing_angle_rad: float = 0.0, anim_timer: float = 0.0, scale: float = 1.0, is_attacking: bool = False, palette: dict = None)
  ```
- **Features**: Directional facing rotation (radians), leg walking stride, weapon thrust.
- **Palette Keys**: `armor`, `accent`, `skin`, `weapon`, `joint`.

### 3.2 `draw_slime_enemy_2d`
- **File**: `assets/sprites_2d/creature_2d.py`
- **Primitives**: Concentric circles, specular highlight circles, pupil circles.
- **Signature**:
  ```python
  draw_slime_enemy_2d(position: Vector2, anim_timer: float = 0.0, radius: float = 24.0, palette: dict = None)
  ```
- **Features**: Squash-and-stretch hopping bounce, dilation pupils, translucent body outline.
- **Palette Keys**: `body`, `outline`, `highlight`, `eye`, `pupil`.

### 3.3 `draw_flying_drone_2d`
- **File**: `assets/sprites_2d/creature_2d.py`
- **Primitives**: Triangles (flapping wings), Circles (cyclops eye, iris, body core).
- **Signature**:
  ```python
  draw_flying_drone_2d(position: Vector2, anim_timer: float = 0.0, radius: float = 18.0, palette: dict = None)
  ```
- **Features**: Rapid wing flapping, vertical levitation drift.
- **Palette Keys**: `body`, `wing`, `eye`, `pupil`.

### 3.4 `draw_crawler_enemy_2d`
- **File**: `assets/sprites_2d/creature_2d.py`
- **Primitives**: Circles (abdomen, cephalothorax, eyes, foot pads), Lines (articulated legs).
- **Signature**:
  ```python
  draw_crawler_enemy_2d(position: Vector2, facing_angle_rad: float = 0.0, anim_timer: float = 0.0, radius: float = 16.0, palette: dict = None)
  ```
- **Features**: 6 articulated walking legs with wave phase gait, multi-eye cluster.
- **Palette Keys**: `carapace`, `head`, `legs`, `eyes`.

---

## 4. Procedural Audio Synthesizer (`assets/audio/`)

Generates audio purely in memory without external audio files (`.wav`/`.mp3`).
> **Important**: Always call `init_audio_device()` before playing sounds and `close_audio_device()` at game exit.

### 4.1 Sound Effects (`synth_sfx.py`)
- `create_laser_sfx()`: Downward laser frequency sweep.
- `create_explosion_sfx()`: Decaying filtered white noise with sub-bass rumble.
- `create_hit_sfx()`: Punchy collision thud.
- `create_jump_sfx()`: Upward frequency slide.
- `create_coin_sfx()`: Bright 2-tone chime.
- `create_powerup_sfx()`: Rising 4-tone fanfare.
- `create_hurt_sfx()`: Low pitched groan with grit.
- `create_click_sfx()`: Subtle UI blip.

#### `SoundLibrary` Class
```python
sfx = SoundLibrary()
sfx.init_defaults()       # Generates & caches all SFX once
sfx.play("laser")         # Plays sound by name
sfx.play("explosion", 0.8)# Plays with volume scaling
sfx.unload_all()          # Disposes memory at shutdown
```

### 4.2 Background Music Tracks (`synth_music.py`)
- `generate_action_track(bpm=126.0)`: 8-bar fast combat loop with 4-on-the-floor bass and synth arpeggios.
- `generate_ambient_track(bpm=84.0)`: Atmospheric exploration pad with gentle harmonic chords.

#### `SynthMusicPlayer` Class
```python
music = SynthMusicPlayer()
track = generate_action_track()
music.load_track(track)
music.play()

# Inside main game loop:
music.update()            # Auto-loops seamlessly when track ends

# At shutdown:
music.unload()
```

