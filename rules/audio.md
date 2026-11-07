# Procedural Audio Architectural Guidelines & Code Templates (`assets/audio/`)
==============================================================================

This document defines the architectural standards, procedural synthesis principles, audio hardware lifecycles, and canonical **code templates** for all procedural in-memory sound effects (SFX) and background music (BGM).

All audio task tracking, synthesizer inventory, and progress statuses are maintained in the companion spreadsheets:
👉 [**`tasks/SFXs.csv`**](../tasks/SFXs.csv) (73 procedural sound effects)
👉 [**`tasks/BGMs.csv`**](../tasks/BGMs.csv) (18 background music tracks categorized by emotional vibe)

---

## 1. Golden Architecture Rules for Procedural Audio

1. **Zero External Audio Assets**:
   Every sound effect and musical measure is synthesized purely in RAM from mathematical waveforms (sine, triangle, square, sawtooth, filtered white noise). External `.wav`, `.mp3`, or `.ogg` audio files are strictly forbidden.
2. **In-Memory RIFF WAV Loading (Sound vs. Music Stream)**:
   - **SFX**: Short one-shot effects are synthesized into a 16-bit mono PCM sample buffer, packed with an in-memory 44-byte RIFF WAV header, and loaded into a Raylib `Sound` struct via `load_wave_from_memory` and `load_sound_from_wave`. The raw `Wave` struct is immediately unloaded with `unload_wave(wave)`.
   - **BGM**: Looping background tracks are synthesized into a multi-measure 16-bit mono PCM buffer and loaded into a streaming Raylib `Music` struct via `load_music_stream_from_memory` with `music.looping = True`.
3. **Repository Philosophy: Simple Beats Clever & 1-to-1 C++ Transferability**:
   This repository is an educational encyclopedia designed for learning and inspiration. Python is used strictly as executable pseudocode that ports 1-to-1 to C++, C, C#, Rust, or Zig. All synthesis routines and audio classes must use plain classes with explicit `__init__`, fixed sample buffers (`std::vector<short int>` / `std::array<float, N>` style), explicit `for` loops, no decorators, no generators, no lambdas, no magic dunders, and comments explaining WHY in plain English without academic jargon.
4. **Modular Category Asset Organization & Central Dynamic Registry**:
   - Individual procedural sound effects are standalone modules organized by category into `assets/audio/SFX/<category>/<name>.py`.
   - Individual procedural background music tracks are standalone modules organized by emotional vibe into `assets/audio/BGM/<vibe>/<name>.py`.
   - The central discovery registry and selective in-RAM loader is located at `assets/audio/synth_sfx.py`.
5. **Decoupled Minigame Integration (Instructions in `rules/minigames.md`)**:
   Minigames do not synthesize ad-hoc audio. Minigames declare strictly two lists (`SFXS = [...]` and `BGMS = [...]`) and load them via `SoundLibrary`. All instructions for importing and using audio inside minigames are located in [`rules/minigames.md`](minigames.md) Section 3.5.
6. **Device Lifecycle Cleanliness**:
   Always call `init_audio_device()` before synthesizing or loading audio into hardware memory. Always call `unload_all()` followed by `close_audio_device()` at application shutdown to prevent memory leaks or audio driver hangs.
7. **Line Limits & Sizing Guidance**:
   - **Floor**: **200 lines minimum**. (Ensures complete mathematical primitives, visual audition workbench, and pedagogical C++ mapping comments).
   - **Target Range**: **200 to 800 lines** per procedural audio module.
   - **Hard Ceiling**: **1,000 lines maximum**.
   - **Readability Criterion**: Every audio file must be understandable reading top to bottom, without jumping across files; clarity always wins over line count.
8. **Standalone Previewer & Automated `--smoke-test`**:
   Every audio file must be standalone executable (`if __name__ == "__main__":`). Running `python -B assets/audio/SFX/<category>/<file>.py` or `python -B assets/audio/BGM/<vibe>/<file>.py` opens an interactive Sound Audition Workbench. Running with `--smoke-test` synthesizes the buffer, verifies audio device loading, tests playback, runs 3 frames, unloads all resources, and exits with code `0`.

---

## 2. The "No-Magic" C++ Porting Philosophy for Audio

In C++, synthesizing procedural audio in memory and loading it with Raylib follows the exact same memory layout and API calls:

```cpp
// Direct C++ Raylib Translation (raylib.h):

// 1. One-Shot SFX (Buffered in RAM / Audio device):
Wave wave = LoadWaveFromMemory(".wav", memoryBuffer, bufferSize);
Sound sound = LoadSoundFromWave(wave);
UnloadWave(wave);           // Free raw PCM data; Sound retains device audio
SetSoundVolume(sound, 0.85f);
SetSoundPitch(sound, 1.0f);
PlaySound(sound);
UnloadSound(sound);         // Free at shutdown

// 2. Looping BGM (Streamed from in-memory WAV buffer):
Music music = LoadMusicStreamFromMemory(".wav", memoryBuffer, bufferSize);
music.looping = true;
SetMusicVolume(music, 0.7f);
PlayMusicStream(music);
// In game loop:
UpdateMusicStream(music);   // Feeds audio stream buffer frame-by-frame
UnloadMusicStream(music);   // Free at shutdown

// Global device lifecycle:
InitAudioDevice();
// ...
CloseAudioDevice();
```

| Python Implementation (`pyray`) | Equivalent Direct C++ Code (`raylib.h`) |
| :--- | :--- |
| `raw_bytes = bytearray()` with `py_struct.pack('<h', val)` | `std::vector<short int> buffer(num_samples);` |
| `wave = load_wave_from_memory(".wav", data, len(data))` | `Wave wave = LoadWaveFromMemory(".wav", data, size);` |
| `sound = load_sound_from_wave(wave)` | `Sound sound = LoadSoundFromWave(wave);` |
| `unload_wave(wave)` | `UnloadWave(wave);` |
| `music = load_music_stream_from_memory(".wav", data, len(data))` | `Music music = LoadMusicStreamFromMemory(".wav", data, size);` |
| `music.looping = True` | `music.looping = true;` |
| `update_music_stream(music)` | `UpdateMusicStream(music);` |
| `play_sound(sound)` / `play_music_stream(music)` | `PlaySound(sound);` / `PlayMusicStream(music);` |
| `stop_sound(sound)` / `stop_music_stream(music)` | `StopSound(sound);` / `StopMusicStream(music);` |
| `unload_sound(sound)` / `unload_music_stream(music)` | `UnloadSound(sound);` / `UnloadMusicStream(music);` |

---

## 3. Modular Audio Code Templates

Craftsmen subagents authoring audio assets in `assets/audio/` must implement one of the two canonical templates below:
- **Code Template 1 (SFX)**: For short one-shot sound effects loaded into Raylib `Sound` (`assets/audio/SFX/<category>/<name>.py`).
- **Code Template 2 (BGM)**: For multi-bar looping background music streamed via Raylib `Music` (`assets/audio/BGM/<vibe>/<name>.py`).

*(Note: Minigame audio import and usage instructions are intentionally omitted here; refer to [`rules/minigames.md`](minigames.md) Section 3.5 for minigame integration).*

---

### Code Template 1: Modular SFX Synthesizer (`assets/audio/SFX/<category>/<name>.py`)

Every modular sound effect module adheres to this 6-part anatomy:

```python
# -*- coding: utf-8 -*-
"""
<Asset Title> - Procedural SFX Synthesizer
===========================================
Type             : Procedural Audio SFX (Sound)
Target File      : assets/audio/SFX/<category>/<name>.py
Waveforms Used   : <e.g. Downward exponential sine sweep with square grit>
Category         : <combat / movement / creature / environment / ui_hud>

Problem Solved:
  <1-2 sentences explaining what audio cue this provides and why procedural synthesis avoids asset files>

Waveform Theory & Mathematical Rationale:
  <Explanation of carrier frequency, modulation, envelopes, and harmonics>

Direct C++ Raylib Translation (raylib.h):
  struct <Name>SFX {
      Sound sound;
      void Play(float volume, float pitch) {
          SetSoundVolume(sound, volume);
          SetSoundPitch(sound, pitch);
          PlaySound(sound);
      }
      void Stop() { StopSound(sound); }
      void Unload() { UnloadSound(sound); }
  };
"""

# ==============================================================================
# PART 2: ZERO __pycache__ SETUP, PATH SETUP & RAYLIB IMPORTS
# ==============================================================================
import sys
import os
import math
import struct as py_struct  # Aliased to prevent collision with pyray.struct

# Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# Add repository root to search path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

from pyray import *
from utils import *

# ==============================================================================
# PART 3: AUDIO SYNTHESIS CONSTANTS
# ==============================================================================
SAMPLE_RATE = 44100
PI2 = 2.0 * math.pi

DEFAULT_DURATION = 0.12        # Seconds
START_FREQUENCY = 880.0        # Hz
END_FREQUENCY = 220.0          # Hz
DECAY_RATE = 6.0               # Exponential decay factor


# ==============================================================================
# PART 4: IN-MEMORY RIFF WAV PACKER HELPER (C++ 44-Byte Header Equivalent)
# ==============================================================================
def pack_riff_wav_mono_16bit(sample_rate: int, raw_samples: list) -> bytes:
    """
    Packs signed 16-bit PCM integer samples (-32767 to 32767) into an in-memory
    canonical 44-byte RIFF/WAVE container.
    """
    num_samples = len(raw_samples)
    pcm_bytes = bytearray()
    for i in range(num_samples):
        val = raw_samples[i]
        clamped = max(-32767, min(32767, int(val)))
        pcm_bytes.extend(py_struct.pack('<h', clamped))

    riff_id = b'RIFF'
    wave_id = b'WAVE'
    fmt_id = b'fmt '
    fmt_size = 16
    audio_format = 1        # PCM
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


# ==============================================================================
# PART 5: CORE SYNTHESIS FUNCTION & STANDARDIZED CONTROL METHODS
# ==============================================================================
def create_<name>_sfx(
    duration: float = DEFAULT_DURATION,
    start_freq: float = START_FREQUENCY,
    end_freq: float = END_FREQUENCY
) -> Sound:
    """
    Synthesizes the sound effect into a ready-to-play Raylib Sound struct.
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    phase = 0.0

    for i in range(total_samples):
        progress = float(i) / float(total_samples)

        # Exponential pitch glide
        decay_factor = math.log(end_freq / start_freq)
        current_freq = start_freq * math.exp(decay_factor * progress)
        phase += PI2 * current_freq / SAMPLE_RATE

        # Envelope
        envelope = math.exp(-DECAY_RATE * progress)

        # Waveform generation
        sine_val = math.sin(phase)
        sample_16bit = sine_val * envelope * 26000.0
        samples.append(sample_16bit)

    wav_bytes = pack_riff_wav_mono_16bit(SAMPLE_RATE, samples)
    wave = load_wave_from_memory(".wav", wav_bytes, len(wav_bytes))
    sound = load_sound_from_wave(wave)
    unload_wave(wave)
    return sound


# Standardized alias mapping for dynamic discovery
create_sfx = create_<name>_sfx


def play_sfx(sound: Sound, volume: float = 1.0, pitch: float = 1.0) -> None:
    """Plays the sound effect with explicit volume and pitch scaling."""
    set_sound_volume(sound, max(0.0, min(1.0, volume)))
    set_sound_pitch(sound, max(0.5, min(2.0, pitch)))
    play_sound(sound)


def stop_sfx(sound: Sound) -> None:
    """Stops playback of the sound effect immediately."""
    stop_sound(sound)


def unload_sfx(sound: Sound) -> None:
    """Frees the Sound resource from audio hardware memory."""
    unload_sound(sound)


# ==============================================================================
# PART 6: STANDALONE AUDITION WORKBENCH & AUTOMATED SMOKE TEST
# ==============================================================================
class SFXAuditionApp:
    def __init__(self):
        init_window(1280, 720, "SFX Workbench - <Name>")
        set_target_fps(60)
        init_audio_device()
        self.sound = create_sfx()
        self.trigger_pulse = 0.0

    def trigger(self):
        play_sfx(self.sound, 0.85, 1.0)
        self.trigger_pulse = 1.0

    def update(self):
        dt = min(get_frame_time(), 0.05)
        if self.trigger_pulse > 0.0:
            self.trigger_pulse = max(0.0, self.trigger_pulse - dt * 3.5)
        if is_key_pressed(KEY_SPACE) or is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            self.trigger()

    def draw(self):
        begin_drawing()
        clear_background(Color(12, 16, 26, 255))
        draw_text("PROCEDURAL SFX AUDITION WORKBENCH", 24, 20, 20, RAYWHITE)
        draw_text("[Space] / [Left Click] Trigger SFX", 24, 50, 13, SKYBLUE)
        
        # Real-time visual pulse
        pulse_w = int(self.trigger_pulse * 760)
        draw_rectangle(450, 200, pulse_w, 30, Color(0, 220, 255, 255))
        
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)
        end_drawing()

    def run(self, smoke_test: bool = False):
        frame_count = 0
        if smoke_test:
            self.trigger()
        while not window_should_close():
            self.update()
            self.draw()
            frame_count += 1
            if smoke_test and frame_count >= 3:
                break
        unload_sfx(self.sound)
        close_audio_device()
        close_window()


if __name__ == "__main__":
    is_smoke = "--smoke-test" in sys.argv
    SFXAuditionApp().run(smoke_test=is_smoke)
```

---

### Code Template 2: Modular Algorithmic BGM Synthesizer (`assets/audio/BGM/<vibe>/<name>.py`)

Every modular background music module adheres to this 6-part anatomy:

```python
# -*- coding: utf-8 -*-
"""
<Asset Title> - Procedural BGM Synthesizer
===========================================
Type             : Procedural Audio BGM (Music Stream)
Target File      : assets/audio/BGM/<vibe>/<name>.py
Waveforms Used   : <e.g. Triangle bass, square arpeggio, shaped noise hi-hats>
Category         : Interactive BGM Soundtracks
Vibe             : <calm / cheerful / curious / eerie / energetic / futuristic / industrial / intense / mystical / nostalgic / suspenseful / triumphant>

Problem Solved:
  <1-2 sentences explaining the musical purpose and streaming RAM benefits>

Musical Theory & Mathematical Rationale:
  - Tempo: <e.g. 120 BPM>
  - Clock Timing: Samples per beat = (SAMPLE_RATE * 60) / BPM.
  - Musical Scale: Mathematical pitch frequencies using f(n) = 440.0 * 2^((n - 69) / 12).
  - Multi-Channel Voices: Layered bass, melody, and percussion voices.
  - Seamless Loop Points: Sample count matches exact integer measures.

Direct C++ Raylib Translation (raylib.h):
  struct <Name>BGM {
      Music music;
      void Play(float volume, float pitch, bool loop) {
          SetMusicVolume(music, volume);
          SetMusicPitch(music, pitch);
          music.looping = loop;
          PlayMusicStream(music);
      }
      void Update() { UpdateMusicStream(music); } // Feeds streaming buffer every frame
      void Stop()   { StopMusicStream(music); }
      void Unload() { UnloadMusicStream(music); }
  };
"""

# ==============================================================================
# PART 2: ZERO __pycache__ SETUP, PATH SETUP & RAYLIB IMPORTS
# ==============================================================================
import sys
import os
import math
import random
import struct as py_struct  # Aliased to prevent collision with pyray.struct

# Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# Add repository root to search path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

from pyray import *
from utils import *

# ==============================================================================
# PART 3: AUDIO & MUSICAL CONSTANTS
# ==============================================================================
SAMPLE_RATE = 44100
PI2 = 2.0 * math.pi
BPM = 120.0

LOOP_DURATION_SECONDS = 4.0
TOTAL_LOOP_SAMPLES = int(SAMPLE_RATE * LOOP_DURATION_SECONDS)
TOTAL_STEPS = 32
SAMPLES_PER_STEP = TOTAL_LOOP_SAMPLES // TOTAL_STEPS
STEP_DURATION_SEC = float(SAMPLES_PER_STEP) / float(SAMPLE_RATE)

# Pitch tables (frequencies in Hz)
BASS_NOTES = [110.0, 130.81, 146.83, 164.81]
LEAD_NOTES = [220.00, 261.63, 293.66, 329.63, 392.00, 440.00, 523.25, 659.25]
LEAD_SEQUENCE = [0, 2, 4, 5, 4, 2, 1, 3, 0, 2, 4, 7, 5, 4, 2, 1,
                 0, 3, 5, 6, 5, 3, 2, 4, 1, 2, 4, 5, 7, 5, 4, 2]


# ==============================================================================
# PART 4: IN-MEMORY RIFF WAV PACKER HELPER (C++ 44-Byte Header Equivalent)
# ==============================================================================
def pack_riff_wav_mono_16bit(sample_rate: int, raw_samples: list) -> bytes:
    """
    Packs signed 16-bit PCM integer samples (-32767 to 32767) into an in-memory
    canonical 44-byte RIFF/WAVE container.
    """
    num_samples = len(raw_samples)
    pcm_bytes = bytearray()
    for i in range(num_samples):
        val = raw_samples[i]
        clamped = max(-32767, min(32767, int(val)))
        pcm_bytes.extend(py_struct.pack('<h', clamped))

    riff_id = b'RIFF'
    wave_id = b'WAVE'
    fmt_id = b'fmt '
    fmt_size = 16
    audio_format = 1        # PCM
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


# ==============================================================================
# PART 5: CORE SYNTHESIS FUNCTION & STANDARDIZED CONTROL METHODS
# ==============================================================================
def create_<name>_bgm() -> Music:
    """
    Algorithmically synthesizes looping background music in RAM into a Raylib Music struct.
    """
    samples = []
    phase_bass = 0.0
    phase_lead = 0.0

    for i in range(TOTAL_LOOP_SAMPLES):
        step_idx = (i // SAMPLES_PER_STEP) % TOTAL_STEPS
        step_sample = i % SAMPLES_PER_STEP
        step_progress = float(step_sample) / float(SAMPLES_PER_STEP)

        # Voice 1: Bassline (Triangle)
        bass_note_idx = (step_idx // 4) % len(BASS_NOTES)
        phase_bass += PI2 * BASS_NOTES[bass_note_idx] / SAMPLE_RATE
        tri_bass = (2.0 / math.pi) * math.asin(math.sin(phase_bass))
        bass_amp = tri_bass * math.exp(-2.5 * (step_sample / (SAMPLES_PER_STEP * 4))) * 0.45

        # Voice 2: Lead Pulse (Square)
        lead_note_idx = LEAD_SEQUENCE[step_idx]
        phase_lead += PI2 * LEAD_NOTES[lead_note_idx] / SAMPLE_RATE
        sq_lead = 1.0 if math.sin(phase_lead) > 0.0 else -1.0
        lead_amp = sq_lead * math.exp(-6.5 * step_progress) * 0.25

        # Voice 3: Percussion Hi-Hat (Noise)
        hat_amp = 0.0
        if step_idx % 2 == 1:
            hat_amp = (random.random() * 2.0 - 1.0) * math.exp(-24.0 * step_progress) * 0.15

        master_mix = bass_amp + lead_amp + hat_amp
        samples.append(master_mix * 24000.0)

    wav_bytes = pack_riff_wav_mono_16bit(SAMPLE_RATE, samples)
    music = load_music_stream_from_memory(".wav", wav_bytes, len(wav_bytes))
    music.looping = True
    return music


# Standardized alias mapping for dynamic discovery
create_bgm = create_<name>_bgm


def play_bgm(music: Music, volume: float = 1.0, pitch: float = 1.0, loop: bool = True) -> None:
    """Starts streaming playback of the music track with loop control."""
    set_music_volume(music, max(0.0, min(1.0, volume)))
    set_music_pitch(music, max(0.5, min(2.0, pitch)))
    music.looping = loop
    play_music_stream(music)


def stop_bgm(music: Music) -> None:
    """Stops music stream playback."""
    stop_music_stream(music)


def pause_bgm(music: Music) -> None:
    """Pauses the music stream."""
    pause_music_stream(music)


def resume_bgm(music: Music) -> None:
    """Resumes the music stream."""
    resume_music_stream(music)


def update_bgm(music: Music) -> None:
    """
    Feeds audio stream buffers frame-by-frame.
    MUST be called once per frame in the main update loop.
    """
    update_music_stream(music)


def unload_bgm(music: Music) -> None:
    """Frees the streaming Music buffers from memory."""
    unload_music_stream(music)


# ==============================================================================
# PART 6: STANDALONE AUDITION WORKBENCH & AUTOMATED SMOKE TEST
# ==============================================================================
class BGMAuditionApp:
    def __init__(self):
        init_window(1280, 720, "BGM Workbench - <Name>")
        set_target_fps(60)
        init_audio_device()
        self.music = create_bgm()
        self.is_playing = True
        play_bgm(self.music, 0.70, 1.0, loop=True)

    def update(self):
        if self.is_playing:
            update_bgm(self.music)
        if is_key_pressed(KEY_SPACE) or is_key_pressed(KEY_M):
            if self.is_playing:
                pause_bgm(self.music)
                self.is_playing = False
            else:
                resume_bgm(self.music)
                self.is_playing = True

    def draw(self):
        begin_drawing()
        clear_background(Color(12, 16, 26, 255))
        draw_text("PROCEDURAL BGM AUDITION WORKBENCH", 24, 20, 20, RAYWHITE)
        draw_text("[Space] / [M] Toggle Play/Pause", 24, 50, 13, ORANGE)
        
        # Telemetry & Top Bar
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
        unload_bgm(self.music)
        close_audio_device()
        close_window()


if __name__ == "__main__":
    is_smoke = "--smoke-test" in sys.argv
    BGMAuditionApp().run(smoke_test=is_smoke)
```

---

## 4. Querying Tasks via CLI & Python `csv`

Subagents and automated tools query [`tasks/SFXs.csv`](../tasks/SFXs.csv) and [`tasks/BGMs.csv`](../tasks/BGMs.csv) using the headless `tasks.py` CLI (<50ms, zero Raylib GUI window) or Python's standard library `csv` module (<50 tokens per query).

### 4.1 Find Pending Audio Tasks by Category & Vibe (Fast CLI)
```bash
# Query sound effects by category
python -B tasks.py --list SFXs --category combat --status pending --limit 4

# Query background music tracks by vibe
python -B tasks.py --list BGMs --vibe energetic --status pending --limit 2
python -B tasks.py --list BGMs --status pending --limit 3
```

### 4.2 Fetch Full Audio Specifications by ID (Fast CLI)
```bash
python -B tasks.py --get SFXs sfx_combat_laser
python -B tasks.py --get BGMs bgm_synth_pulse
```

### 4.3 Check if Function Name Already Exists (Prevent Collisions)
```bash
python -B tasks.py --check SFXs create_laser_sfx
python -B tasks.py --check BGMs create_synth_pulse_bgm
```

### 4.4 Mark an Audio Asset as Built (Orchestrator Only)
```bash
python -B tasks.py --set-status SFXs sfx_combat_laser built
python -B tasks.py --set-status BGMs bgm_synth_pulse built
```

---

## 5. Human Spreadsheet Editing & Tasks Editor (`tasks.py`)

To inspect, sort, and edit [`tasks/SFXs.csv`](../tasks/SFXs.csv) and [`tasks/BGMs.csv`](../tasks/BGMs.csv) without risking CSV delimiter or encoding corruption:
1. **Interactive Tasks Editor (`tasks.py`)**: Run `python -B tasks.py` to open the graphical Raylib task manager with hot-switching tabs (`minigames.csv`, `SFXs.csv`, `BGMs.csv`, `models_3D.csv`, `sprites_2D.csv`), sorting, cell editing, horizontal scrolling, and "Adjusted Text" (Wrap Text).
2. **Never alter column header names**:
   - `tasks/SFXs.csv`: `id,type,category,function_name,target_file,audio_specs,status,description`
   - `tasks/BGMs.csv`: `id,type,category,vibe,function_name,target_file,audio_specs,status,description`
3. **Canonical 1-Word Vibes**: `calm`, `cheerful`, `curious`, `eerie`, `energetic`, `futuristic`, `industrial`, `intense`, `mystical`, `nostalgic`, `suspenseful`, `triumphant`.
4. **Allowed status values**: `pending`, `in_progress`, `built`.
