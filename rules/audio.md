# Procedural Audio Architectural Guidelines & Registry (`assets/audio/`)
========================================================================

This document defines the architectural standards, procedural synthesis principles, audio device lifecycles, and copy-pasteable **code templates** for all procedural in-memory sound effects (SFX) and background music (BGM).

All audio task tracking, synthesizer inventory, and progress statuses are maintained in the companion spreadsheet:
👉 [**`tasks/audio.csv`**](../tasks/audio.csv) (90 planned items: 73 SFX and 17 BGM soundtracks)

---

## 1. Golden Architecture Rules for Procedural Audio

1. **Zero External Audio Assets**: Every sound effect and musical measure is synthesized purely in RAM from mathematical waveforms (sine, triangle, square, sawtooth, filtered white noise). External `.wav`, `.mp3`, or `.ogg` files are strictly forbidden.
2. **In-Memory RIFF WAV Loading**:
   Audio is synthesized into a 16-bit mono PCM sample buffer, packed with an in-memory RIFF WAV header via `struct.pack`, loaded into a Raylib `Wave` struct via `load_wave_from_memory(".wav", data, len(data))`, converted to a Raylib `Sound` struct via `load_sound_from_wave(wave)`, and freed via `unload_wave(wave)`.
3. **Strict C++ & Cross-Language Transferability**:
   In alignment with [`README.md`](../README.md) and [`AGENTS.md`](../AGENTS.md), all synthesizer routines must use explicit struct-like classes, fixed sample buffers (`std::vector<short int>` / `std::array<float, N>` style), and explicit `for` loops. Generators (`yield`), decorators, and dynamic metaprogramming are forbidden.
4. **Pre-Allocated Sound Caching**:
   Procedural audio must be synthesized and loaded into Raylib `Sound` structs once at startup (`sfx.init_defaults()`) and reused via `SoundLibrary.play("<name>")`. Never synthesize or re-allocate audio buffers inside dynamic gameplay loops.
5. **Default Destination Directories & Files**:
   - The core comprehensive synthesizer & SoundLibrary is located at `assets/audio/synth_sfx.py`.
   - Dedicated modular sound effect synthesizers are located in `assets/audio/SFX/`.
   - Dedicated procedural background music tracks are located in `assets/audio/BGM/`.
6. **Device Lifecycle Cleanliness**:
   Always ensure `init_audio_device()` is called before loading sounds and `sfx.unload_all()` followed by `close_audio_device()` is called at application exit to prevent memory leaks or audio driver hangs.
7. **Strict Sizing Bounds**:
   Every procedural audio synthesizer module must strictly remain within the **400 to 800 line** target range (floor: **400 lines**, hard ceiling: **1,000 lines**). Scripts below 400 lines lack pedagogical explanations and waveform modulation loops; scripts above 1,000 lines cause token bloat.
8. **Standalone Previewer & Automated `--smoke-test`**:
   Every audio file must be standalone executable (`if __name__ == "__main__":`). Running `python -B assets/audio/SFX/<file>.py` opens an interactive Sound Audition Workbench. Running with `--smoke-test` synthesizes the sound buffer, verifies valid audio device loading, tests playback, runs 3 frames, and exits with code `0`.

---

## 2. The "No-Magic" C++ Porting Philosophy for Audio

In C++, synthesizing procedural audio in memory and loading it with Raylib follows the exact same memory layout:

```cpp
// Direct C++ Raylib Translation (raylib.h):
Wave wave = LoadWaveFromMemory(".wav", memoryBuffer, bufferSize);
Sound sound = LoadSoundFromWave(wave);
UnloadWave(wave); // Free raw PCM data, keep GPU/audio device sound
PlaySound(sound);
// At shutdown:
UnloadSound(sound);
CloseAudioDevice();
```

| Python Implementation (`pyray`) | Equivalent Direct C++ Code (`raylib.h`) |
| :--- | :--- |
| `raw_bytes = bytearray()` with `struct.pack('<h', sample)` | `std::vector<short int> buffer(num_samples);` |
| `wave = load_wave_from_memory(".wav", data, len(data))` | `Wave wave = LoadWaveFromMemory(".wav", data, size);` |
| `sound = load_sound_from_wave(wave)` | `Sound sound = LoadSoundFromWave(wave);` |
| `unload_wave(wave)` | `UnloadWave(wave);` |
| `play_sound(sound)` / `set_sound_volume(sound, vol)` | `PlaySound(sound); SetSoundVolume(sound, vol);` |
| `unload_sound(sound)` | `UnloadSound(sound);` |

---

## 3. Standard Procedural SFX Code Template

Every craftsman subagent creating procedural sound effects must follow this exact anatomy. Copy and adapt this template for your target asset:

```python
# -*- coding: utf-8 -*-
"""
Combat & Weapon Sound Effects Synthesizer - In-RAM Procedural Audio
==================================================================
Category         : combat
Target File      : assets/audio/synth_sfx.py
Waveforms Used   : Sine sweeps, triangle bodies, decaying white noise, harmonic clusters
Synthesized SFX  : Laser Blast, Heavy Explosion, Kinetic Impact, Resonant Shield Parry

Problem Solved:
  Eliminates bulky .wav/.mp3 audio asset downloads by synthesizing high-impact,
  zero-latency sound effects purely from mathematical waveforms in RAM at startup.

How the Procedural Synthesis Works:
  - 16-bit mono PCM samples (44,100 Hz) are generated via mathematical equations.
  - Frequency sweeps use exponential or linear interpolation: f(t) = f_start + (f_end - f_start) * (t / duration).
  - Envelopes use linear Attack-Decay-Sustain-Release (ADSR) multiplier curves.
  - A valid in-memory 44-byte RIFF header is prepended using Python's standard struct.pack.
  - Raylib loads the in-RAM buffer via load_wave_from_memory and converts it to a Sound struct.

C++ Raylib Equivalent:
  struct SoundLibrary { Sound laser; Sound explosion; Sound hit; Sound parry; };
  void InitSoundLibrary(SoundLibrary* lib);
  void PlaySFX(Sound sound, float volume, float pitch);
  void FreeSoundLibrary(SoundLibrary* lib);
"""

import sys
import os
import math
import random
import struct as py_struct  # Aliased to prevent collision with pyray.struct string constant

# 1. Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# 2. Add repository root to search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

# 3. Mandatory Raylib and utility imports
from pyray import *
from utils import *

SAMPLE_RATE = 44100


# ==============================================================================
# IN-RAM RIFF WAV FORMAT PACKER (C++-Transferable Memory Layout)
# ==============================================================================
def pack_riff_wav_mono_16bit(sample_rate: int, raw_samples: list) -> bytes:
    """
    Packs a list of signed 16-bit integer samples (-32768 to 32767) into a standard
    44-byte RIFF/WAVE header followed by raw PCM data.
    Directly mirrors writing a 44-byte header struct into memory in C++.
    """
    num_samples = len(raw_samples)
    pcm_bytes = bytearray()
    for i in range(num_samples):
        val = raw_samples[i]
        clamped = max(-32767, min(32767, int(val)))
        pcm_bytes.extend(py_struct.pack('<h', clamped))

    # Standard RIFF/WAVE 44-Byte Header
    riff_id = b'RIFF'
    wave_id = b'WAVE'
    fmt_id = b'fmt '
    fmt_size = 16
    audio_format = 1        # PCM = 1
    num_channels = 1        # Mono
    byte_rate = sample_rate * num_channels * 2
    block_align = num_channels * 2
    bits_per_sample = 16
    data_id = b'data'
    data_size = len(pcm_bytes)
    total_chunk_size = 36 + data_size

    header = py_struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        riff_id, total_chunk_size, wave_id,
        fmt_id, fmt_size, audio_format,
        num_channels, sample_rate, byte_rate,
        block_align, bits_per_sample,
        data_id, data_size
    )
    return bytes(header + pcm_bytes)


def load_sound_from_samples(sample_rate: int, samples: list) -> Sound:
    """
    Synthesizes samples into RAM and returns a fully initialized Raylib Sound struct.
    """
    wav_bytes = pack_riff_wav_mono_16bit(sample_rate, samples)
    wave = load_wave_from_memory(".wav", wav_bytes, len(wav_bytes))
    sound = load_sound_from_wave(wave)
    unload_wave(wave)  # Free Wave struct in memory; Sound retains device audio
    return sound


# ==============================================================================
# PROCEDURAL SOUND EFFECT SYNTHESIZERS
# ==============================================================================
def create_laser_sfx() -> Sound:
    """
    Downward exponential frequency sweep (880 Hz -> 220 Hz, 140ms).
    Produces a crisp, punchy arcade laser blast.
    """
    duration = 0.14
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    phase = 0.0

    for i in range(num_samples):
        t = float(i) / SAMPLE_RATE
        progress = t / duration

        # Exponential pitch glide downward
        freq = 880.0 * math.exp(-3.0 * progress)
        phase += 2.0 * math.pi * freq / SAMPLE_RATE

        # Sine wave with exponential decay envelope
        env = math.exp(-6.0 * progress)
        sample_val = math.sin(phase) * env * 30000.0
        samples.append(sample_val)

    return load_sound_from_samples(SAMPLE_RATE, samples)


def create_heavy_laser_sfx() -> Sound:
    """
    Dual square-wave pulse with sub-bass carrier (440 Hz -> 110 Hz, 240ms).
    Produces a powerful charged beam or railgun blast.
    """
    duration = 0.24
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    phase1 = 0.0
    phase2 = 0.0

    for i in range(num_samples):
        t = float(i) / SAMPLE_RATE
        progress = t / duration

        freq1 = 440.0 * (1.0 - 0.75 * progress)
        freq2 = 110.0 * (1.0 - 0.50 * progress)
        phase1 += 2.0 * math.pi * freq1 / SAMPLE_RATE
        phase2 += 2.0 * math.pi * freq2 / SAMPLE_RATE

        # Square wave harmonics with sub-bass sine
        sq = 1.0 if (math.sin(phase1) > 0.0) else -1.0
        sub = math.sin(phase2)

        env = math.exp(-4.5 * progress)
        sample_val = (sq * 0.6 + sub * 0.4) * env * 28000.0
        samples.append(sample_val)

    return load_sound_from_samples(SAMPLE_RATE, samples)


def create_explosion_sfx() -> Sound:
    """
    Low-pass filtered white noise with a 45 Hz sub-bass carrier (550ms).
    Produces a deep, rumbling cinematic detonation.
    """
    duration = 0.55
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    phase_sub = 0.0
    filtered_noise = 0.0

    # Deterministic pseudo-random seed for repeatable synthesis
    rng = random.Random(42)

    for i in range(num_samples):
        t = float(i) / SAMPLE_RATE
        progress = t / duration

        # Sub-bass rumble carrier (45 Hz -> 25 Hz)
        freq_sub = 45.0 * (1.0 - 0.45 * progress)
        phase_sub += 2.0 * math.pi * freq_sub / SAMPLE_RATE
        sub_body = math.sin(phase_sub)

        # Low-pass single-pole IIR filter approximation on noise
        white_noise = rng.uniform(-1.0, 1.0)
        cutoff = max(0.01, 0.40 * (1.0 - progress))
        filtered_noise = filtered_noise + cutoff * (white_noise - filtered_noise)

        # Non-linear decay envelope
        env = math.exp(-4.0 * progress)
        sample_val = (filtered_noise * 0.7 + sub_body * 0.3) * env * 31000.0
        samples.append(sample_val)

    return load_sound_from_samples(SAMPLE_RATE, samples)


def create_hit_sfx() -> Sound:
    """
    High-impact 150 Hz impulse with decaying triangle body (90ms).
    Produces a tactile kinetic bullet/fist hit sound.
    """
    duration = 0.09
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    phase = 0.0

    for i in range(num_samples):
        t = float(i) / SAMPLE_RATE
        progress = t / duration

        freq = 150.0 * (1.0 - 0.60 * progress)
        phase += 2.0 * math.pi * freq / SAMPLE_RATE

        # Triangle waveform
        tri = (2.0 / math.pi) * math.asin(math.sin(phase))
        env = math.exp(-10.0 * progress)
        sample_val = tri * env * 29000.0
        samples.append(sample_val)

    return load_sound_from_samples(SAMPLE_RATE, samples)


def create_parry_sfx() -> Sound:
    """
    High-frequency harmonic sine cluster (2200 Hz & 3300 Hz) with metallic ring (320ms).
    Produces a bright, rewarding deflection chime.
    """
    duration = 0.32
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    phase1 = 0.0
    phase2 = 0.0

    for i in range(num_samples):
        t = float(i) / SAMPLE_RATE
        progress = t / duration

        phase1 += 2.0 * math.pi * 2200.0 / SAMPLE_RATE
        phase2 += 2.0 * math.pi * 3300.0 / SAMPLE_RATE

        # Resonant chime harmonic beating
        chime = (math.sin(phase1) * 0.6) + (math.sin(phase2) * 0.4)
        env = math.exp(-5.0 * progress)
        sample_val = chime * env * 26000.0
        samples.append(sample_val)

    return load_sound_from_samples(SAMPLE_RATE, samples)


# ==============================================================================
# CENTRAL SOUND LIBRARY (Pre-Allocated Sound Caching)
# ==============================================================================
class SoundLibrary:
    """
    Pre-allocated sound effect manager. Synthesizes all sounds once at startup
    and exposes safe playback with volume and pitch modulation.
    Translates directly to a C++ SoundManager struct.
    """
    def __init__(self):
        self.sounds = {}
        self.initialized = False

    def init_defaults(self):
        """Synthesizes default procedural sound effects into RAM."""
        if self.initialized:
            return
        self.sounds["laser"] = create_laser_sfx()
        self.sounds["heavy_laser"] = create_heavy_laser_sfx()
        self.sounds["explosion"] = create_explosion_sfx()
        self.sounds["hit"] = create_hit_sfx()
        self.sounds["parry"] = create_parry_sfx()
        self.initialized = True

    def play(self, name: str, volume: float = 1.0, pitch: float = 1.0):
        """Plays a pre-cached sound effect with specified volume and pitch."""
        if not self.initialized or name not in self.sounds:
            return
        snd = self.sounds[name]
        set_sound_volume(snd, max(0.0, min(1.0, volume)))
        set_sound_pitch(snd, max(0.5, min(2.0, pitch)))
        play_sound(snd)

    def unload_all(self):
        """Frees all allocated Raylib Sound structs at application shutdown."""
        if not self.initialized:
            return
        for name in list(self.sounds.keys()):
            unload_sound(self.sounds[name])
        self.sounds.clear()
        self.initialized = False


# ==============================================================================
# STANDALONE AUDITION WORKBENCH & AUTOMATED SMOKE TEST
# ==============================================================================
class SoundPlayerApp:
    """
    Interactive audio audition bench allowing developers to trigger and inspect
    each procedural sound effect live, with automated smoke test support.
    """
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        init_window(self.screen_width, self.screen_height, "Audio Inspector - Procedural SFX")
        set_target_fps(60)
        init_audio_device()

        self.library = SoundLibrary()
        self.library.init_defaults()

        self.sound_keys = ["laser", "heavy_laser", "explosion", "hit", "parry"]
        self.selected_idx = 0
        self.last_played = "None"
        self.pulse_anim = 0.0

    def update(self):
        dt = min(get_frame_time(), 0.05)
        if self.pulse_anim > 0.0:
            self.pulse_anim = max(0.0, self.pulse_anim - dt * 3.0)

        # Number keys 1-5 to trigger sounds
        if is_key_pressed(KEY_ONE):
            self.trigger_sound(0)
        elif is_key_pressed(KEY_TWO):
            self.trigger_sound(1)
        elif is_key_pressed(KEY_THREE):
            self.trigger_sound(2)
        elif is_key_pressed(KEY_FOUR):
            self.trigger_sound(3)
        elif is_key_pressed(KEY_FIVE):
            self.trigger_sound(4)
        elif is_key_pressed(KEY_SPACE):
            self.trigger_sound(self.selected_idx)

        # Arrow Up/Down to navigate
        if is_key_pressed(KEY_UP):
            self.selected_idx = (self.selected_idx - 1) % len(self.sound_keys)
        if is_key_pressed(KEY_DOWN):
            self.selected_idx = (self.selected_idx + 1) % len(self.sound_keys)

    def trigger_sound(self, idx: int):
        self.selected_idx = idx
        name = self.sound_keys[idx]
        self.library.play(name, volume=1.0)
        self.last_played = name
        self.pulse_anim = 1.0

    def draw(self):
        begin_drawing()
        clear_background(Color(16, 20, 28, 255))

        # Title & Controls (Clear of top-bar region x=450..980)
        draw_text("PROCEDURAL AUDIO INSPECTOR: In-RAM SFX Synthesizer", 24, 20, 20, RAYWHITE)
        draw_text("[1-5] Trigger Specific Sound | [Space] Play Selected | [Up/Down] Navigate", 24, 52, 14, LIGHTGRAY)

        # Sound List Cards
        start_y = 110
        for i in range(len(self.sound_keys)):
            name = self.sound_keys[i]
            y = start_y + (i * 68)
            is_sel = (i == self.selected_idx)

            card_col = Color(35, 45, 62, 255) if is_sel else Color(24, 30, 42, 255)
            draw_rectangle(24, y, 400, 56, card_col)
            draw_rectangle_lines(24, y, 400, 56, Color(0, 220, 255, 255) if is_sel else Color(45, 55, 75, 255))

            draw_text(f"[{i + 1}] {name.upper()}", 40, y + 12, 18, YELLOW if is_sel else RAYWHITE)
            draw_text("Synthesized in RAM", 40, y + 34, 12, GRAY)

        # Audio Output Monitor & Waveform Visualizer
        draw_rectangle(450, 110, 800, 396, Color(22, 28, 38, 255))
        draw_rectangle_lines(450, 110, 800, 396, Color(45, 55, 75, 255))
        draw_text("REAL-TIME AUDIO OUTPUT MONITOR", 470, 126, 16, SKYBLUE)
        draw_text(f"Last Played: {self.last_played.upper()}", 470, 154, 14, RAYWHITE)

        # Visualizer Pulse Bar
        pulse_w = int(self.pulse_anim * 760)
        bar_col = Color(int(255 * self.pulse_anim), int(180 * self.pulse_anim), 50, 255)
        draw_rectangle(470, 200, pulse_w, 24, bar_col)

        # Global Top-Bar Integration
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)
        end_drawing()

    def run(self, smoke_test: bool = False):
        frame_count = 0
        while not window_should_close():
            self.update()
            self.draw()
            frame_count += 1
            if smoke_test and frame_count >= 3:
                break
        self.library.unload_all()
        close_audio_device()
        close_window()


if __name__ == "__main__":
    is_smoke = "--smoke-test" in sys.argv
    SoundPlayerApp().run(smoke_test=is_smoke)
```

---

## 4. Minigame Integration Example

To synthesize and use procedural audio in any minigame prototype:

```python
from assets.audio.synth_sfx import SoundLibrary

class MyMinigame:
    def __init__(self):
        init_window(1280, 720, "Game Prototype")
        init_audio_device()
        
        # Initialize and synthesize procedural sounds into RAM
        self.sfx = SoundLibrary()
        self.sfx.init_defaults()

    def update(self):
        # Trigger sounds during gameplay events
        if is_key_pressed(KEY_SPACE):
            self.sfx.play("laser", volume=0.8, pitch=1.0)
        if self.enemy_destroyed:
            self.sfx.play("explosion", volume=1.0)

    def teardown(self):
        # Free audio resources at game exit
        self.sfx.unload_all()
        close_audio_device()
        close_window()
```

---

## 5. Procedural BGM (Background Music) Synthesis Principles

For algorithmic BGM tracks in `assets/audio/BGM/`:
1. **Musical Scale Frequencies**: Use mathematical formulas for chromatic and pentatonic note frequencies:
   $$f(n) = 440.0 \times 2^{(n - 69) / 12}$$
2. **Tempo & Step Sequencer**: Calculate samples per beat:
   $$\text{Samples per Beat} = \frac{\text{Sample Rate} \times 60}{\text{BPM}}$$
3. **Multi-Channel Voices**: Synthesize Bass (Triangle wave), Lead (Arpeggiated Square wave), and Rhythm (Noise snips) into combined sample frames.
4. **Standalone BGM Previewer**: Every BGM track must provide an interactive previewer and `--smoke-test` exit just like SFX modules.

---

## 6. Audio Categorization Overview

All 90 items in [`tasks/audio.csv`](../tasks/audio.csv) are categorized across 6 functional categories:

- **Combat & Weapons** (21 SFX): Energy weapons, kinetic impacts, explosions, active reloads, parries, elemental burns, and charged railguns.
- **Movement & Kinematics** (15 SFX): Footsteps, jumps, double jumps, dashes, thrusters, pneumatic puffs, grappling cables, and wall-run friction scrapes.
- **Creature & Entity** (16 SFX): Vocalizations, insectoid chitters, golem stomps, slime splats, damage grunts, and revival stingers.
- **Environmental & Ambient** (16 SFX): Structural hull groans, geothermal steam vents, fluorescent light flickers, cavern water drips, and acid bubbles.
- **Interface & Signals** (16 SFX): Clicks, selections, cancellations, errors, confirmations, radar sonar pings, and byte streams.
- **Interactive BGM Soundtracks** (17 BGM): Multi-layer algorithmic music with seamless loop points across diverse moods (action, ambient, boss, stealth, chiptune, cyberpunk, dungeon, and synthwave).

---

## 7. Querying & Updating Tasks via CLI & Python `csv`

Subagents and automated scripts query [`tasks/audio.csv`](../tasks/audio.csv) using the headless `tasks.py` CLI (<50ms, zero Raylib GUI window) or Python's standard library `csv` module (<50 tokens per query).

### 7.1 Find Pending Audio Tasks in a Category (Fast CLI)
```bash
python -B tasks.py --list audio --category combat --status pending --limit 4
```

### 7.2 Fetch Full Audio Specifications by ID (Fast CLI)
```bash
python -B tasks.py --get audio sfx_combat_laser
```

### 7.3 Check if Function Name Already Exists (Prevent Collisions)
```bash
python -B tasks.py --check audio create_laser_sfx
```

### 7.4 Mark an Audio Asset as Built (Fast CLI)
```bash
python -B tasks.py --set-status audio sfx_combat_laser built
```

### 7.5 Fallback: Python Standard Library `csv` One-Liners
```bash
# Query pending in combat category
python -B -c "import csv; f=open('tasks/audio.csv', encoding='utf-8-sig'); r=csv.DictReader(f); print(next(dict(id=x['id'], func=x['function_name'], file=x['target_file']) for x in r if x['category']=='combat' and x['status']=='pending'))"

# Count pending vs built audio items
python -B -c "import csv; from collections import Counter; f=open('tasks/audio.csv', encoding='utf-8-sig'); c=Counter((x['type'], x['category'], x['status']) for x in csv.DictReader(f)); [print(f'{k[0]} / {k[1]} [{k[2]}]: {v}') for k, v in sorted(c.items())]"
```

---

## 8. Human Spreadsheet Editing & Tasks Editor (`tasks.py`)

To inspect, sort, and edit [`tasks/audio.csv`](../tasks/audio.csv) without risking CSV delimiter or encoding corruption:
1. **Interactive Tasks Editor (`tasks.py`)**: Run `python -B tasks.py` to open the graphical Raylib task manager with hot-switching, sorting, cell editing, horizontal scrolling, and "Adjusted Text" (Wrap Text).
2. **Never alter column header names**: The first row must keep `id,type,category,function_name,target_file,audio_specs,status,description`.
3. **Allowed status values**: `pending`, `in_progress`, `built`.
