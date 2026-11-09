# -*- coding: utf-8 -*-
"""
Procedural Background Music (BGM) Synthesizer - Astral Sanctuary
================================================================
Type             : Procedural Audio BGM (Music Stream)
Target File      : assets/audio/BGM/mystical/astral_sanctuary.py
Waveforms Used   : Pure sine sub-swell, detuned sine cluster glass harp, formant-filtered choir pad, shaped high-pass noise stardust
Category         : Interactive BGM Soundtracks
Vibe             : mystical

Problem Solved:
  Generates a higher-dimensional spirit realm and floating shrine soundtrack
  purely in RAM using algorithmic procedural synthesis with zero external audio files.
  Streams audio seamlessly via Raylib's Music struct with memory-pinned buffers.

Musical Theory & Mathematical Rationale:
  - Tempo: 82.0 Beats Per Minute (BPM) in 4/4 meter across 8 bars (32 beats).
  - Duration & Sample Count:
      Exact duration is 8 bars (32 beats).
      Beat length       = 60.0 / 82.0 = 0.731707 seconds (32,268.29 samples)
      Total duration    = 32 * (60.0 / 82.0) = 23.414634 seconds
      Total loop sample count N = round(44100 * 1920.0 / 82.0) = 1,032,585 samples.
  - Mode: E Lydian (E, F#, G#, A#, B, C#, D#).
      The characteristic sound of the Lydian mode is the raised 4th degree (A#),
      imparting an ethereal, transcendent celestial quality without the tension
      of a minor interval or the traditional major scale tritone pull.
  - Multi-Voice Architecture:
      1. Cosmic Sub-Swell (gain 0.38):
         Pure sine dual-frequency sub-bass (E1 at 41.20 Hz, E2 at 82.41 Hz)
         breathing with a slow 4-bar sinusoidal amplitude cycle at 0.0854 Hz
         (frequency = 1.0 / (16 beats * (60/82)s) = 0.085417 Hz).
      2. Glass Harp Arpeggios (gain 0.28):
         Cascading 32-step high register melodic clusters in E Lydian.
         Each note is synthesized from a cluster of 3 close sines (f0, 1.003*f0, 0.997*f0)
         producing crystalline shimmer, modulated by an exponential decay envelope (k = 4.5).
      3. Angelic Choir Pad (gain 0.24):
         Sustained modal chords (Emaj7, F#7, G#m7, Emaj7#11) shifting every 2 bars,
         shaped by a resonant two-pole vowel formant filter morphing between
         vowel formants U (~350 Hz), O (~500 Hz), and A (~800 Hz) via a slow 8-bar LFO.
      4. Stardust Downbeat Bursts (gain 0.12):
         High-pass filtered noise bursts on the downbeat of each 4-beat bar,
         decaying rapidly via e^(-14.0 * t) to evoke cosmic dust collisions.
  - PCM Headroom & Clamping:
      Master mix is strictly clamped to [-26000, 26000] PCM before packing to prevent
      short integer overflow and ensure pristine dynamic headroom.

Direct C++ Raylib Translation (raylib.h):
  struct AstralSanctuaryBGM {
      Music music;
      void Play(float volume, float pitch, bool loop) {
          SetMusicVolume(music, volume);
          SetMusicPitch(music, pitch);
          music.looping = loop;
          PlayMusicStream(music);
      }
      void Update() { UpdateMusicStream(music); }
      void Stop()   { StopMusicStream(music); }
      void Unload() { UnloadMusicStream(music); }
  };
"""

import sys
import os
import math
import random
import struct as py_struct
import array as py_array

# 1. Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# 2. Add repository root to search path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

# 3. Mandatory Raylib and utility imports
from pyray import *
from utils import *

# ==============================================================================
# AUDIO & MUSICAL CONSTANTS
# ==============================================================================
SAMPLE_RATE = 44100
INV_SAMPLE_RATE = 1.0 / float(SAMPLE_RATE)
PI2 = 2.0 * math.pi
BPM = 82.0

# 8 Bars at 82.0 BPM in 4/4 meter = 32 beats
# Exact sample count: round(44100 * 32 * 60 / 82.0) = 1,032,585 samples (23.415s)
TOTAL_LOOP_SAMPLES = int(round(SAMPLE_RATE * 32.0 * 60.0 / BPM))
LOOP_DURATION_SECONDS = float(TOTAL_LOOP_SAMPLES) * INV_SAMPLE_RATE

# 32 Quarter-note steps across the 8 bars
TOTAL_STEPS = 32
SAMPLES_PER_STEP = TOTAL_LOOP_SAMPLES // TOTAL_STEPS
STEP_DURATION_SEC = float(SAMPLES_PER_STEP) * INV_SAMPLE_RATE

# Bar metrics (8 bars, 4 beats per bar)
TOTAL_BARS = 8
SAMPLES_PER_BAR = TOTAL_LOOP_SAMPLES // TOTAL_BARS
SAMPLES_PER_TWO_BARS = SAMPLES_PER_BAR * 2

# Glass Harp cascading notes in E Lydian (frequencies in Hz)
# Scale: E, F#, G#, A# (raised 4th), B, C#, D#
HARP_NOTES = [
    329.63, 415.30, 493.88, 622.25,  # Bar 1: E4, G#4, B4, D#5 (Emaj7)
    466.16, 493.88, 415.30, 659.25,  # Bar 2: A#4, B4, G#4, E5 (Emaj7#11 - raised 4th!)
    369.99, 466.16, 554.37, 739.99,  # Bar 3: F#4, A#4, C#5, F#5 (F# / E)
    659.25, 554.37, 466.16, 369.99,  # Bar 4: E5, C#5, A#4, F#4 (F#7 descending)
    415.30, 493.88, 622.25, 830.61,  # Bar 5: G#4, B4, D#5, G#5 (G#m)
    739.99, 622.25, 493.88, 466.16,  # Bar 6: F#5, D#5, B4, A#4 (Bmaj7)
    466.16, 554.37, 659.25, 932.33,  # Bar 7: A#4, C#5, E5, A#5 (A# dim / Lydian peak)
    830.61, 739.99, 622.25, 329.63,  # Bar 8: G#5, F#5, D#5, E4 (Lydian cadence to E)
]

# Sustained modal chords for Angelic Choir Pad (2 bars per chord)
CHORD_NAMES = [
    "Emaj7 (E-G#-B-D#)",
    "F#7/E (F#-A#-C#-E)",
    "G#m7 (G#-B-D#-F#)",
    "Emaj7#11 (E-A#-B-D#)",
]

PAD_CHORDS = [
    [164.81, 207.65, 246.94, 311.13],  # Chord 0: E3, G#3, B3, D#4
    [185.00, 233.08, 277.18, 329.63],  # Chord 1: F#3, A#3, C#4, E4
    [207.65, 246.94, 311.13, 369.99],  # Chord 2: G#3, B3, D#4, F#4
    [164.81, 233.08, 246.94, 311.13],  # Chord 3: E3, A#3, B3, D#4
]

# Module-level pinned buffer registry to prevent garbage collection crashes in CFFI
_ACTIVE_BUFFERS = {}


# ==============================================================================
# IN-MEMORY RIFF/WAV PACKER (C++ 44-Byte Header Equivalent)
# ==============================================================================
def pack_riff_wav_mono_16bit(sample_rate: int, raw_samples: list) -> bytes:
    """
    Packs signed 16-bit PCM integer samples (-32767 to 32767) into an in-memory
    canonical 44-byte RIFF/WAVE container.
    """
    num_samples = len(raw_samples)
    clamped_list = [max(-32767, min(32767, int(raw_samples[i]))) for i in range(num_samples)]
    pcm_array = py_array.array('h', clamped_list)
    pcm_bytes = pcm_array.tobytes()

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
# CORE PROCEDURAL BGM SYNTHESIS FUNCTION
# ==============================================================================
def create_astral_sanctuary_bgm() -> Music:
    """
    Algorithmically synthesizes the 8-bar looping Astral Sanctuary track in RAM.
    Exposes 4 procedural layers in E Lydian at 82.0 BPM.
    Returns a streaming Raylib Music struct with looping enabled and pinned buffer.
    """
    sin = math.sin
    cos = math.cos
    exp = math.exp
    rand = random.random

    # Phase increments for Voice 1 (Cosmic Sub-Swell: E1 41.20 Hz, E2 82.41 Hz)
    phase_e1 = 0.0
    phase_e2 = 0.0
    inc_e1 = PI2 * 41.20 * INV_SAMPLE_RATE
    inc_e2 = PI2 * 82.41 * INV_SAMPLE_RATE

    # 4-bar breathing cycle: period = 16 beats = 11.7073s -> frequency = 0.0854167 Hz
    breathe_phase = -math.pi * 0.5
    breathe_inc = PI2 * (1.0 / (16.0 * (60.0 / BPM))) * INV_SAMPLE_RATE

    # Pre-calculated phase increments for Voice 2 (Glass Harp Arpeggios)
    harp_inc1 = [PI2 * f * INV_SAMPLE_RATE for f in HARP_NOTES]
    harp_inc2 = [inc * 1.003 for inc in harp_inc1]
    harp_inc3 = [inc * 0.997 for inc in harp_inc1]

    phase_h1 = 0.0
    phase_h2 = 0.0
    phase_h3 = 0.0

    # Pre-calculated phase increments for Voice 3 (Angelic Choir Pad)
    chord_incs = [[PI2 * f * INV_SAMPLE_RATE for f in chord] for chord in PAD_CHORDS]
    p0 = 0.0
    p1 = 0.0
    p2 = 0.0
    p3 = 0.0
    inc_p0 = chord_incs[0][0]
    inc_p1 = chord_incs[0][1]
    inc_p2 = chord_incs[0][2]
    inc_p3 = chord_incs[0][3]

    # Two-pole resonant vowel formant filter state
    # Sweeps between U (~350 Hz), O (~500 Hz), and A (~800 Hz)
    r = 0.95
    s_in = 1.0 - r
    c2 = -(r * r)
    c1 = 2.0 * r * cos(PI2 * 575.0 * INV_SAMPLE_RATE)
    pad_y1 = 0.0
    pad_y2 = 0.0

    # Timing and progress multipliers
    step_prog_mult = 1.0 / float(SAMPLES_PER_STEP)
    two_bar_prog_mult = math.pi / float(SAMPLES_PER_TWO_BARS)
    formant_lfo_mult = PI2 / LOOP_DURATION_SECONDS

    # Voice 4 state: Stardust Downbeat Bursts
    prev_noise = 0.0
    random.seed(42)

    samples = [0.0] * TOTAL_LOOP_SAMPLES
    cur_step = -1
    cur_chord = -1
    ih1 = harp_inc1[0]
    ih2 = harp_inc2[0]
    ih3 = harp_inc3[0]

    for i in range(TOTAL_LOOP_SAMPLES):
        step_sample = i % SAMPLES_PER_STEP
        if step_sample == 0:
            cur_step = (i // SAMPLES_PER_STEP) % TOTAL_STEPS
            ih1 = harp_inc1[cur_step]
            ih2 = harp_inc2[cur_step]
            ih3 = harp_inc3[cur_step]

        two_bar_sample = i % SAMPLES_PER_TWO_BARS
        if two_bar_sample == 0:
            cur_chord = (i // SAMPLES_PER_TWO_BARS) % 4
            incs = chord_incs[cur_chord]
            inc_p0, inc_p1, inc_p2, inc_p3 = incs[0], incs[1], incs[2], incs[3]

        # ----------------------------------------------------------------------
        # Voice 1: Cosmic Sub-Swell (gain 0.38)
        # ----------------------------------------------------------------------
        phase_e1 += inc_e1
        phase_e2 += inc_e2
        breathe_phase += breathe_inc
        breathe_env = 0.5 + 0.5 * sin(breathe_phase)
        v1 = (0.7 * sin(phase_e1) + 0.3 * sin(phase_e2)) * breathe_env * 0.38

        # ----------------------------------------------------------------------
        # Voice 2: Glass Harp Arpeggios (gain 0.28)
        # ----------------------------------------------------------------------
        phase_h1 += ih1
        phase_h2 += ih2
        phase_h3 += ih3
        step_progress = float(step_sample) * step_prog_mult
        cluster = (sin(phase_h1) + sin(phase_h2) + sin(phase_h3)) * 0.33333333
        v2 = cluster * exp(-4.5 * step_progress) * 0.28

        # ----------------------------------------------------------------------
        # Voice 3: Angelic Choir Pad with Vowel Formant Filtering (gain 0.24)
        # ----------------------------------------------------------------------
        p0 += inc_p0
        p1 += inc_p1
        p2 += inc_p2
        p3 += inc_p3
        chord_raw = (
            sin(p0) + 0.3 * sin(p0 * 2.0) +
            sin(p1) + 0.3 * sin(p1 * 2.0) +
            sin(p2) + 0.3 * sin(p2 * 2.0) +
            sin(p3) + 0.3 * sin(p3 * 2.0)
        ) * 0.25

        # Sub-sampled control rate update for vowel formant sweep (every 16 samples)
        if (i & 15) == 0:
            t_curr = float(i) * INV_SAMPLE_RATE
            fc = 575.0 + 225.0 * sin(formant_lfo_mult * t_curr - 1.57079632679)
            c1 = 2.0 * r * cos(PI2 * fc * INV_SAMPLE_RATE)

        pad_out = c1 * pad_y1 + c2 * pad_y2 + s_in * chord_raw
        pad_y2 = pad_y1
        pad_y1 = pad_out
        chord_env = sin(float(two_bar_sample) * two_bar_prog_mult)
        v3 = pad_out * chord_env * 0.24

        # ----------------------------------------------------------------------
        # Voice 4: Stardust Downbeat Bursts (gain 0.12)
        # ----------------------------------------------------------------------
        bar_sample = i % SAMPLES_PER_BAR
        raw_noise = rand() * 2.0 - 1.0
        hp_noise = raw_noise - prev_noise
        prev_noise = raw_noise
        v4 = hp_noise * exp(-14.0 * (float(bar_sample) * INV_SAMPLE_RATE)) * 0.12

        # ----------------------------------------------------------------------
        # Master Mix & Clamping to [-26000, 26000]
        # ----------------------------------------------------------------------
        master = v1 + v2 + v3 + v4
        pcm_val = master * 26000.0
        if pcm_val > 26000.0:
            pcm_val = 26000.0
        elif pcm_val < -26000.0:
            pcm_val = -26000.0
        samples[i] = pcm_val

    wav_bytes = pack_riff_wav_mono_16bit(SAMPLE_RATE, samples)
    music = load_music_stream_from_memory(".wav", wav_bytes, len(wav_bytes))
    music.looping = True

    # Pin buffer in module-level dictionary to prevent garbage collection crash
    _ACTIVE_BUFFERS[id(music)] = wav_bytes
    return music


# Mandatory standardized alias for dynamic discovery in asset_loader.py & synth_sfx.py
create_bgm = create_astral_sanctuary_bgm


# ==============================================================================
# STANDARDIZED PLAYBACK CONTROL METHODS
# ==============================================================================
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
    """Pauses the music stream at its current playback position."""
    pause_music_stream(music)


def resume_bgm(music: Music) -> None:
    """Resumes the music stream from its paused position."""
    resume_music_stream(music)


def update_bgm(music: Music) -> None:
    """
    Feeds audio stream buffers frame-by-frame.
    MUST be called once per frame in the main update loop to prevent audio stutter.
    """
    update_music_stream(music)


def unload_bgm(music: Music) -> None:
    """Frees the streaming Music buffers from memory and audio hardware."""
    _ACTIVE_BUFFERS.pop(id(music), None)
    unload_music_stream(music)


# ==============================================================================
# STANDALONE AUDITION WORKBENCH & AUTOMATED SMOKE TEST
# ==============================================================================
class BGMAuditionApp:
    """
    Interactive background music player allowing developers and students
    to audition procedural BGM tracks live with tempo telemetry and visualizer.
    """
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        init_window(
            self.screen_width,
            self.screen_height,
            "BGM Workbench - Astral Sanctuary (assets/audio/BGM/mystical/astral_sanctuary.py)"
        )
        set_target_fps(60)
        if not is_audio_device_ready():
            init_audio_device()

        self.music = create_astral_sanctuary_bgm()
        self.volume = 0.75
        self.pitch = 1.0
        self.is_playing = False

        # Start playback automatically in audition workbench
        play_bgm(self.music, self.volume, self.pitch, loop=True)
        self.is_playing = True

    def toggle_playback(self):
        """Toggles music stream between play and pause states."""
        if self.is_playing:
            pause_bgm(self.music)
            self.is_playing = False
        else:
            resume_bgm(self.music)
            self.is_playing = True

    def update(self):
        """Per-frame update logic feeding Raylib stream buffers."""
        if self.is_playing:
            update_bgm(self.music)

        # Space or M toggles Play/Pause
        if is_key_pressed(KEY_SPACE) or is_key_pressed(KEY_M):
            self.toggle_playback()

        # Up/Down arrows adjust volume
        if is_key_pressed(KEY_UP):
            self.volume = min(1.0, self.volume + 0.05)
            set_music_volume(self.music, self.volume)
        elif is_key_pressed(KEY_DOWN):
            self.volume = max(0.0, self.volume - 0.05)
            set_music_volume(self.music, self.volume)

        # Left/Right arrows adjust pitch/tempo
        if is_key_pressed(KEY_RIGHT):
            self.pitch = min(2.0, self.pitch + 0.05)
            set_music_pitch(self.music, self.pitch)
        elif is_key_pressed(KEY_LEFT):
            self.pitch = max(0.5, self.pitch - 0.05)
            set_music_pitch(self.music, self.pitch)

    def draw(self):
        """Draws telemetry HUD and multi-voice rhythm visualizer."""
        begin_drawing()
        clear_background(Color(10, 14, 24, 255))

        # Title Header (keeps safe top region x=450..980 clear for dropdowns)
        draw_text("PROCEDURAL BGM AUDITION WORKBENCH", 24, 20, 20, RAYWHITE)
        draw_text(
            "Asset: assets/audio/BGM/mystical/astral_sanctuary.py | 82 BPM E-Lydian Spirit Realm",
            24, 48, 13, SKYBLUE
        )

        # Control Info Card
        panel_y = 90
        draw_rectangle(24, panel_y, 400, 270, Color(18, 24, 40, 255))
        draw_rectangle_lines(24, panel_y, 400, 270, Color(45, 65, 105, 255))
        draw_text("ASTRAL SANCTUARY BGM CONTROLS", 40, panel_y + 14, 15, YELLOW)
        draw_text("- [Space] / [M]          : Play / Pause Stream", 40, panel_y + 44, 13, RAYWHITE)
        draw_text("- [Up] / [Down] Arrows   : Volume (+/- 5%)", 40, panel_y + 70, 13, RAYWHITE)
        draw_text("- [Left] / [Right] Arrows: Tempo / Pitch (+/- 5%)", 40, panel_y + 96, 13, RAYWHITE)
        draw_text(
            f"Playback State  : {'PLAYING (Looping)' if self.is_playing else 'PAUSED'}",
            40, panel_y + 130, 13, GREEN if self.is_playing else RED
        )
        draw_text(f"Volume          : {int(self.volume * 100)}%", 40, panel_y + 154, 13, SKYBLUE)
        draw_text(f"Tempo / Pitch   : {self.pitch:.2f}x", 40, panel_y + 178, 13, SKYBLUE)
        draw_text("Mode / Scale    : E Lydian (E F# G# A# B C# D#)", 40, panel_y + 204, 12, GOLD)
        draw_text("Loop Metrics    : 8 Bars | 32 Beats | 82.0 BPM", 40, panel_y + 228, 12, LIGHTGRAY)

        # Synthesis Specs Card
        specs_y = 380
        draw_rectangle(24, specs_y, 400, 290, Color(16, 22, 36, 255))
        draw_rectangle_lines(24, specs_y, 400, 290, Color(40, 55, 90, 255))
        draw_text("PROCEDURAL VOICE LAYERS", 40, specs_y + 14, 15, ORANGE)
        draw_text("Voice 1: Cosmic Sub-Swell (gain 0.38)", 40, specs_y + 44, 13, SKYBLUE)
        draw_text("  - E1 (41.20 Hz) / E2 (82.41 Hz) pure sine breathing", 40, specs_y + 64, 11, LIGHTGRAY)
        draw_text("Voice 2: Glass Harp Arpeggios (gain 0.28)", 40, specs_y + 92, 13, Color(255, 200, 100, 255))
        draw_text("  - High E Lydian clusters (f0, 1.003f0, 0.997f0) k=4.5", 40, specs_y + 112, 11, LIGHTGRAY)
        draw_text("Voice 3: Angelic Choir Pad (gain 0.24)", 40, specs_y + 140, 13, Color(220, 160, 255, 255))
        draw_text("  - Modal chords with sweeping vowel formant (U-O-A)", 40, specs_y + 160, 11, LIGHTGRAY)
        draw_text("Voice 4: Stardust Downbeat Bursts (gain 0.12)", 40, specs_y + 188, 13, Color(200, 240, 255, 255))
        draw_text("  - High-pass noise bursts on bar 1 downbeats", 40, specs_y + 208, 11, LIGHTGRAY)
        draw_text("PCM Clamping: Strictly [-26000, 26000]", 40, specs_y + 236, 12, GREEN)
        draw_text("Memory Buffer: Pinned in _ACTIVE_BUFFERS (CFFI safe)", 40, specs_y + 258, 11, GOLD)

        # Real-time Stream Output Visualizer
        vis_x = 450
        vis_y = 90
        vis_w = 800
        vis_h = 580
        draw_rectangle(vis_x, vis_y, vis_w, vis_h, Color(14, 20, 32, 255))
        draw_rectangle_lines(vis_x, vis_y, vis_w, vis_h, Color(45, 65, 105, 255))
        draw_text("STREAM BUFFER & MULTI-VOICE RHYTHM MONITOR", vis_x + 20, vis_y + 16, 15, ORANGE)

        # Step Sequencer Activity Grid (32 Steps across 8 bars)
        time_played = get_music_time_played(self.music)
        time_total = get_music_time_length(self.music)
        loop_progress = (time_played / time_total) if time_total > 0.0 else 0.0
        current_step = int(loop_progress * TOTAL_STEPS) % TOTAL_STEPS

        grid_y = vis_y + 54
        step_w = (vis_w - 40) // TOTAL_STEPS
        for s in range(TOTAL_STEPS):
            bx = vis_x + 20 + (s * step_w)
            is_cur = (s == current_step) and self.is_playing
            if is_cur:
                box_col = ORANGE
            elif s % 4 == 0:
                box_col = Color(50, 75, 110, 255)
            else:
                box_col = Color(22, 30, 48, 255)
            draw_rectangle(bx, grid_y, step_w - 2, 40, box_col)
            if s % 4 == 0:
                draw_text(f"B{s//4 + 1}", bx + 2, grid_y + 44, 10, LIGHTGRAY)

        draw_text(
            f"Sequencer Step: {current_step + 1} / {TOTAL_STEPS} | Loop Time: {time_played:.2f}s / {time_total:.2f}s",
            vis_x + 20, grid_y + 60, 13, LIGHTGRAY
        )

        # Loop Progress Bar
        bar_y = vis_y + 165
        draw_rectangle(vis_x + 20, bar_y, vis_w - 40, 18, Color(22, 28, 44, 255))
        fill_w = int(loop_progress * (vis_w - 40))
        draw_rectangle(vis_x + 20, bar_y, fill_w, 18, SKYBLUE)
        draw_rectangle_lines(vis_x + 20, bar_y, vis_w - 40, 18, Color(60, 85, 120, 255))

        # Real-time Voice Monitors
        meter_y = vis_y + 215

        # Voice 1 Telemetry
        breathe_phase_val = math.sin(PI2 * 0.0854167 * time_played - math.pi * 0.5)
        breathe_pct = int((0.5 + 0.5 * breathe_phase_val) * 100)
        draw_text(
            f"[Voice 1: Cosmic Sub-Swell]  E1 (41.2 Hz) + E2 (82.4 Hz) Pure Sine | Breathing Swell: {breathe_pct}%",
            vis_x + 20, meter_y, 13, Color(120, 210, 255, 255)
        )

        # Voice 2 Telemetry
        cur_note_freq = HARP_NOTES[current_step]
        draw_text(
            f"[Voice 2: Glass Harp Arp]    Frequency: {cur_note_freq:.2f} Hz | Detuned Sine Cluster (f0, 1.003f0, 0.997f0)",
            vis_x + 20, meter_y + 36, 13, Color(255, 205, 110, 255)
        )

        # Voice 3 Telemetry
        cur_chord_idx = (current_step // 8) % 4
        chord_display = CHORD_NAMES[cur_chord_idx]
        cur_fc = 575.0 + 225.0 * math.sin(PI2 * (time_played / 23.4146) - 1.570796)
        vowel_char = "U (~350 Hz)" if cur_fc < 450 else ("O (~500 Hz)" if cur_fc < 650 else "A (~800 Hz)")
        draw_text(
            f"[Voice 3: Angelic Choir Pad] {chord_display} | Vowel Formant: {cur_fc:.1f} Hz ({vowel_char})",
            vis_x + 20, meter_y + 72, 13, Color(220, 170, 255, 255)
        )

        # Voice 4 Telemetry
        downbeat_active = "DOWNBEAT BURST (e^-14t)" if (current_step % 4 == 0 and self.is_playing) else "Rest"
        draw_text(
            f"[Voice 4: Stardust Texture]  {downbeat_active} (Differentiated High-Pass Noise)",
            vis_x + 20, meter_y + 108, 13, Color(200, 240, 255, 255)
        )

        # Mode Harmonic Explanation Box
        info_box_y = meter_y + 150
        draw_rectangle(vis_x + 20, info_box_y, vis_w - 40, 150, Color(20, 28, 44, 255))
        draw_rectangle_lines(vis_x + 20, info_box_y, vis_w - 40, 150, Color(45, 65, 100, 255))
        draw_text("LYDIAN HARMONIC INSIGHT", vis_x + 36, info_box_y + 14, 14, YELLOW)
        draw_text(
            "The E Lydian mode features a raised 4th scale degree (A# instead of A natural).",
            vis_x + 36, info_box_y + 40, 12, RAYWHITE
        )
        draw_text(
            "In Astral Sanctuary, this raised 4th forms an augmented 4th tritone with the root E,",
            vis_x + 36, info_box_y + 62, 12, LIGHTGRAY
        )
        draw_text(
            "which resolves upwards to create a weightless, floating celestial ambience.",
            vis_x + 36, info_box_y + 84, 12, LIGHTGRAY
        )
        draw_text(
            "The 4 procedural layers interlock seamlessly with exact integer loop boundaries.",
            vis_x + 36, info_box_y + 106, 12, LIGHTGRAY
        )

        # Top Bar Settings Dropdowns
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)
        end_drawing()

    def run(self, smoke_test: bool = False):
        """Main workbench loop supporting 3-frame headless smoke testing."""
        frame_count = 0
        while not window_should_close():
            self.update()
            self.draw()
            frame_count += 1
            if smoke_test and frame_count >= 3:
                break

        unload_bgm(self.music)
        if is_audio_device_ready():
            close_audio_device()
        close_window()


if __name__ == "__main__":
    is_smoke = "--smoke-test" in sys.argv
    BGMAuditionApp().run(smoke_test=is_smoke)
