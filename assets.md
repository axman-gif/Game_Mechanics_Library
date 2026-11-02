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
Provides 48 procedural game sound effects synthesized purely from mathematical waveforms in memory:

#### Combat & Weapons (16)
- `create_laser_sfx()`: Downward frequency sweep (classic retro blaster).
- `create_heavy_laser_sfx()`: Deep plasma cannon blast with sub-bass rumble.
- `create_explosion_sfx()`: Decaying low-pass filtered white noise with sub-bass rumble.
- `create_hit_sfx()`: Punchy collision impact / melee thud.
- `create_parry_sfx()`: Crisp, high-pitched metallic blade clang with extended crystalline resonance.
- `create_shield_block_sfx()`: Heavy resonant blunt barrier impact thud.
- `create_reload_sfx()`: 3-stage mechanical slide, eject, and chamber lock snap.
- `create_empty_sfx()`: Hollow dry fire hammer click when out of ammo.
- `create_shotgun_sfx()`: Wide-band scattergun sub-bass blast followed by a 2-stage pump-action rack clack.
- `create_sniper_sfx()`: Instantaneous supersonic whip crack, metallic barrel ring, and long canyon echo tail.
- `create_charge_up_sfx()`: Quadratic pitch riser (`160 Hz -> 1120 Hz`) with accelerating LFO capacitor pulse.
- `create_sword_slash_sfx()`: Band-pass aerodynamic blade cleave with a high-frequency steel edge whistle.
- `create_critical_hit_sfx()`: Sub-bass armor slam layered with a 3-partial crystalline FM shatter chime (`G6/C7/G7`).
- `create_ricochet_sfx()`: Metallic bullet deflection ping (`2600 Hz -> 580 Hz`) with a 35 Hz Doppler warble.
- `create_flame_sfx()`: Turbulent thermal-draft filtered noise burst with stochastic crackling embers.
- `create_freeze_sfx()`: Staggered inharmonic FM ice crystallization chimes with brittle frost crackle.

#### Movement & Kinematics (10)
- `create_jump_sfx()`: Upward frequency slide.
- `create_dash_sfx()`: Aerodynamic rushing air whoosh for dodges, dashes, or weapon swings.
- `create_footstep_sfx()`: Subtle, low-impact floor tap with surface friction for character walking.
- `create_land_sfx()`: Solid ground impact thump after falling or jumping.
- `create_double_jump_sfx()`: Nimble 2-stage mid-air flutter kick leaping an octave higher (`240->480->980 Hz`).
- `create_grapple_sfx()`: 3-stage pneumatic harpoon pop, 48 Hz cable winch ratchet, and magnetic claw clank.
- `create_thruster_sfx()`: Deep 72 Hz rocket combustion rumble with a rising turbine spool whine (`420->780 Hz`).
- `create_teleport_sfx()`: Reverse-envelope vacuum implosion folding into a ring-modulated quantum warp burst.
- `create_slide_sfx()`: Dual-pole band-filtered kinetic crouch/wall-slide friction scrape with scuff decay.
- `create_bounce_sfx()`: Elastic springboard / slime bumper rebound (`180->440 Hz`) with a damped 24 Hz pitch wobble.

#### Progression, Rewards & Health (11)
- `create_coin_sfx()`: Bright 2-tone melodic pickup chime (B5 to E6).
- `create_powerup_sfx()`: Rising 4-tone victory arpeggio (E4, G4, B4, E5).
- `create_level_up_sfx()`: Sparkling, triumphant 5-note pentatonic fanfare (C5 to C6).
- `create_heal_sfx()`: Soothing restoration shimmer with vibrato modulation.
- `create_hurt_sfx()`: Low pitched groan with pitch slide and distortion.
- `create_chest_open_sfx()`: Mechanical iron lock unlatch followed by a magical 4-note Lydian discovery arpeggio (`D5-F#5-A5-C#6`).
- `create_craft_sfx()`: Double blacksmith anvil hammer strike (`1180/1770/2950 Hz` steel modes) with a warm harmonic glow.
- `create_debuff_sfx()`: Sinister status curse / encumbrance affliction stepping down a tritone (`A4 -> Eb4 -> A3`).
- `create_gem_sfx()`: High-octave 3-note crystal diamond sparkle (`C6 -> G6 -> C7`) with glassy FM overtones.
- `create_revive_sfx()`: Warm F-major cathedral organ triad swell (`F4-A4-C5-F5`) with 6.5 Hz celestial shimmer.
- `create_death_sfx()`: 4-step descending minor/diminished arcade cascade collapsing into a sub-bass power-down drop.

#### User Interface & Signals (11)
- `create_click_sfx()`: Subtle UI button click blip.
- `create_select_sfx()`: Ultra-soft, gentle UI cursor hover tick (non-fatiguing).
- `create_cancel_sfx()`: Soft descending 2-tone dismissal blip for UI back / close.
- `create_error_sfx()`: Low harsh dissonant buzzer (8 Hz beat) for invalid actions or locked doors.
- `create_alert_sfx()`: Piercing 2-tone exclamation chirp for stealth detection or turret lock-on.
- `create_confirm_sfx()`: Crisp 2-tone ascending perfect-fifth UI accept chime (`E5 -> B5`).
- `create_pause_sfx()`: Classic 4-note retro staccato pause/menu stinger (`C6 - G5 - E5 - C6`).
- `create_typewriter_sfx()`: Ultra-short 25ms warm mechanical keystroke & RPG dialogue speech blip.
- `create_notification_sfx()`: Pleasant dual-chime toast notification & quest objective bell (`A5 -> D6`).
- `create_sonar_ping_sfx()`: High-Q 1480 Hz radar / minimap sonar ping with a secondary echo reflection.
- `create_countdown_sfx()`: Punchy 880 Hz arcade timer & race countdown beep.

#### `SoundLibrary` Class
```python
sfx = SoundLibrary()
sfx.init_defaults()          # Synthesizes & caches all 48 SFX once on startup
sfx.play("laser")            # Plays sound by name
sfx.play("shotgun", 0.85)    # Plays scattergun blast + pump rack
sfx.play("critical_hit", 0.9)# Plays sub-bass slam + crystal shatter
sfx.play("grapple", 0.7)     # Plays 3-stage grappling hook launch
sfx.play("chest_open", 0.8)  # Plays lock click + Lydian treasure fanfare
sfx.play("typewriter", 0.4)  # Plays 25ms dialogue blip
sfx.has("sonar_ping")        # Returns True if sound (or alias) exists in cache
sfx.count()                  # Returns total number of cached sounds (48)
sfx.register("custom", snd)  # Registers custom Sound object into library
sfx.unload_all()             # Disposes audio memory at shutdown (double-free safe)
```

### 4.2 Background Music Tracks (`synth_music.py`)
Generates 12 loopable multi-voice procedural chiptune, synthwave, folk, and orchestral synth soundtracks with click-free crossfaded loop boundaries:

- `generate_action_track(bpm=126.0)`: 8-bar fast combat loop in D minor with 4-on-the-floor synth bass, chord pads, and 16th-note arpeggiated lead.
- `generate_ambient_track(bpm=84.0)`: 4-bar peaceful exploration pad in A minor 9 with chorus detune and sub drone.
- `generate_boss_track(bpm=140.0)`: 8-bar intense boss encounter in C minor with syncopated 8th-note saw bass, brassy chord pads, and rapid arpeggios.
- `generate_stealth_track(bpm=96.0)`: 8-bar tense espionage groove in D minor with heartbeat sub-bass pulses (beats 1 & 2.5), ticking 16th-note hi-hats, and eerie pads.
- `generate_retro_arcade_track(bpm=132.0)`: 8-bar cheerful NES-style chiptune in F/C major with walking triangle-wave bass and catchy 50% square wave melody.
- `generate_victory_track(bpm=116.0)`: 8-bar warm, uplifting celebration / shop loop in G major with organ bass, lush pads, and sparkling pentatonic bell chimes.
- `generate_cyberpunk_track(bpm=136.0)`: 8-bar neon sci-fi synthwave loop in E minor with sidechain-pumping 16th-note saw bass, synthesized kick/snare, and Pulse-Width Modulated (PWM) lead.
- `generate_dungeon_track(bpm=92.0)`: 8-bar haunting crypt/labyrinth loop in E Phrygian with cathedral pedal drone, 25%-pulse harpsichord arpeggios, and vibrato ghost bells.
- `generate_puzzle_track(bpm=104.0)`: 8-bar thoughtful logic-lab groove in C Lydian / Maj7 with plucked upright bass, FM Rhodes electric piano voicings, and syncopated wooden marimba melody.
- `generate_racing_track(bpm=152.0)`: 8-bar high-octane turbo chase in A minor with galloping octave-jumping 8th bass, 16th-note breakbeat percussion, and soaring saw-square lead.
- `generate_tavern_track(bpm=112.0)`: 8-bar cheerful RPG town folk tune in D Dorian with bouncy root-fifth oom-pah bass, strummed lute chords, and breath-enveloped wooden flute melody.
- `generate_mystery_track(bpm=88.0)`: 8-bar ethereal zero-G space drift in F# minor 9 with LFO-modulated cosmic sub-bass, dual-detuned glass pad, and dotted-8th delay echo starlight plucks.

#### `SynthMusicPlayer` Class
```python
music = SynthMusicPlayer()
track = generate_boss_track()
music.load_track(track)
music.play()

# Inside main game loop:
music.update()            # Auto-loops seamlessly when track ends

# At shutdown:
music.unload()
```

---

### 4.3 Interactive Audio Workstation & Sound Player (`assets/audio/sound_player.py`)

A standalone graphical soundboard, visualizer, and procedural jukebox for previewing, inspecting, and mixing all procedural audio in real time.

- **Run Command**:
  ```bash
  python -B assets/audio/sound_player.py
  python -B assets/audio/sound_player.py --smoke-test
  ```
- **Features**:
  - **Categorized SFX Soundboard**: Filterable grid (`ALL`, `COMBAT`, `MOVEMENT`, `PROGRESSION`, `UI`) with visual trigger flash and descriptions.
  - **Real-Time Visualizer**: 16-band reactive frequency spectrum equalizer with peak-hold caps and a continuous CRT oscilloscope waveform.
  - **Procedural BGM Jukebox**: Track timeline, 8 beat LEDs, and transport controls (Play, Pause, Stop, Prev, Next).
  - **Master Gain Mixer**: Interactive sliders for Master, SFX, and BGM volume levels with mute switches.
  - **X-Ray Inspector (`[Tab]`)**: In-depth audio driver, sample rate, and C++ memory telemetry.
- **Controls**:
  - `Mouse`: Click sound cards to trigger, click transport buttons, or drag volume faders.
  - `Arrow Keys / WASD / Gamepad Left Stick / D-Pad`: Navigate soundboard cards.
  - `Space / Enter / Gamepad A`: Play selected sound effect.
  - `1` - `5` / `Gamepad LB / RB`: Switch category filter tabs.
  - `M` / `Gamepad X`: Toggle BGM Play / Pause.
  - `N` / `Gamepad Y`: Next BGM track.
  - `[` / `]`: Decrease / Increase Master Volume.
  - `[Tab]` / `Gamepad Select`: Toggle X-Ray Telemetry Inspector.
  - `[F1]`: Toggle Visualizer Mode (Spectrum + Oscilloscope vs Raw Scope).
  - `[R]` / `Gamepad Start`: Stop all audio and reset mixer.


