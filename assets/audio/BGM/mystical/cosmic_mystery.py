# -*- coding: utf-8 -*-
"""
Procedural Background Music (BGM) Synthesizer - Cosmic Mystery
==============================================================
Type             : Procedural Audio BGM (Music Stream)
Target File      : assets/audio/BGM/mystical/cosmic_mystery.py
Waveforms Used   : Algorithmic pure sine drone, detuned sine bell pairs, dual supersaw choir pad, stardust pings, shaped noise
Category         : Interactive BGM Soundtracks
Vibe             : mystical

Problem Solved:
  Eliminates bulky pre-rendered soundtrack audio files by algorithmically composing
  an 8-bar ethereal zero-G space drift loop purely in RAM using mathematical waveforms.
  Streams in continuous memory-pinned buffers via Raylib's Music struct for minimal
  memory footprint, zero runtime latency, and zero CFFI memory safety defects.

Musical Theory & Mathematical Rationale:
  - Tempo: 88.0 Beats Per Minute (BPM) in 4/4 meter across 8 bars (32 beats).
  - Clock Timing & Sample Calculations:
      Total samples N = 8 * 4 * (44100 * 60 / 88.0) = 962,182 samples (21.818s loop).
      Samples per beat = 962,182 / 32 = 30,068.18 samples (~0.6818s).
  - Scale & Harmony: F# Minor 9 modal progression across 8 bars:
      Bars 1-2: F#m9  (Root F#1 46.25 Hz; Pad: F#3, A3, C#4, E4, G#4)
      Bars 3-4: Dmaj7 (Pad: D3, F#3, A3, C#4)
      Bars 5-6: Bm9   (Pad: B2, D3, F#3, C#4)
      Bars 7-8: C#m7  (Pad: C#3, E3, G#3, B3)
  - Procedural Voice Architecture (4 Layers):
      1. Voice 1 (Bass Drone - gain 0.40): Deep 46.25 Hz F#1 pure sine sub-drone
         oscillating with slow 0.1 Hz amplitude breathing: A(t) = 0.40 * [0.75 + 0.25*sin(2*pi*0.1*t)].
      2. Voice 2 (Lead/Arp Glass Bells - gain 0.24): Shimmering crystalline bells
         composed of detuned high sine pairs (f0 and f0 * 1.004) across F# minor
         (F#5 739.99 Hz, A5 880.0 Hz, C#6 1108.73 Hz, E6 1318.51 Hz, G#6 1661.22 Hz)
         with exponential decay k = 3.5.
      3. Voice 3 (Choir Pad - gain 0.24): Dual supersaw pad (saw + detuned saw)
         passing through a 600 Hz single-pole low-pass filter modulated by a 0.2 Hz chorus LFO.
      4. Voice 4 (Cosmic Texture - gain 0.12): Delicate decaying stardust sparkle pings
         (2400-3600 Hz, decay k = 12.0) and shaped cosmic background radiation noise bursts
         on measure downbeats.
  - Seamless Looping & Peak Clamping:
      Master mix is clamped strictly to [-26000, 26000] signed 16-bit PCM.
      Micro-fades at loop boundaries guarantee zero DC offset or click artifacts.

Direct C++ Raylib Translation (raylib.h):
  struct CosmicMysteryBGM {
      Music music;
      void Play(float volume, float pitch, bool loop) {
          SetMusicVolume(music, volume);
          SetMusicPitch(music, pitch);
          music.looping = loop;
          PlayMusicStream(music);
      }
      void Update() { UpdateMusicStream(music); } // Feeds streaming ring buffer
      void Stop()   { StopMusicStream(music); }
      void Unload() { UnloadMusicStream(music); }
  };
"""

import sys
import os
import math
import random
import struct as py_struct  # Aliased to prevent collision with pyray.struct

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
PI2 = 2.0 * math.pi
BPM = 88.0

# 8 Bars in 4/4 time at 88.0 BPM = exactly 962,182 samples
TOTAL_BARS = 8
BEATS_PER_BAR = 4
TOTAL_BEATS = TOTAL_BARS * BEATS_PER_BAR  # 32 beats
TOTAL_LOOP_SAMPLES = 962182
LOOP_DURATION_SECONDS = float(TOTAL_LOOP_SAMPLES) / float(SAMPLE_RATE)  # ~21.818s

BEAT_SAMPLES = TOTAL_LOOP_SAMPLES / float(TOTAL_BEATS)  # ~30,068.1875 samples/beat
BAR_SAMPLES = int(BEAT_SAMPLES * BEATS_PER_BAR)

# Voice 2: Glass Bell frequencies in F# minor (Hz)
BELL_NOTES = [
    # Bars 1-2: F#m9 (F#5, A5, C#6, E6, G#6)
    1108.73, 1318.51, 1661.22, 1318.51, 1108.73, 880.00, 739.99, 880.00,
    # Bars 3-4: Dmaj7
    739.99, 880.00, 1108.73, 1318.51, 1108.73, 880.00, 739.99, 1108.73,
    # Bars 5-6: Bm9
    739.99, 880.00, 1108.73, 1318.51, 1661.22, 1318.51, 1108.73, 880.00,
    # Bars 7-8: C#m7
    1661.22, 1318.51, 1108.73, 1318.51, 1661.22, 1318.51, 1108.73, 739.99
]

# Voice 3: Pad chord note frequencies (Hz) for each 2-bar progression segment
PAD_CHORDS = [
    [185.00, 220.00, 277.18, 329.63, 415.30],  # Bars 1-2: F#m9
    [146.83, 185.00, 220.00, 277.18],          # Bars 3-4: Dmaj7
    [123.47, 146.83, 185.00, 277.18],          # Bars 5-6: Bm9
    [138.59, 164.81, 207.65, 246.94]           # Bars 7-8: C#m7
]

# Module-level buffer pinning table to protect in-memory WAV stream from GC
_ACTIVE_BUFFERS = {}


# ==============================================================================
# IN-MEMORY RIFF/WAV PACKER (C++ 44-Byte Header Equivalent)
# ==============================================================================
def pack_riff_wav_mono_16bit(sample_rate: int, raw_samples: list) -> bytes:
    """
    Packs signed 16-bit PCM integer samples into an in-memory canonical
    44-byte RIFF/WAVE container without writing temporary files to disk.
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
# CORE PROCEDURAL BGM SYNTHESIS FUNCTION
# ==============================================================================
def generate_mystery_track() -> Music:
    """
    Procedurally synthesizes the 8-bar F# minor 9 zero-G space drift BGM track
    in memory. Returns a streaming Raylib Music struct with looping enabled.
    """
    inv_sr = 1.0 / SAMPLE_RATE
    inv_pi = 1.0 / math.pi
    drone_dp = PI2 * 46.25 * inv_sr
    lfo_breath_dp = PI2 * 0.1 * inv_sr
    lfo_chorus_dp = PI2 * 0.2 * inv_sr

    # Precalculate pad chord phase increments and normalization scales
    chord_configs = []
    for chord in PAD_CHORDS:
        steps = [(PI2 * f * inv_sr, PI2 * (f * 1.0035) * inv_sr) for f in chord]
        chord_configs.append((steps, 0.5 / float(len(chord))))

    samples = []
    phase_drone = 0.0
    lfo_breath_phase = 0.0
    lfo_chorus_phase = 0.0

    # Voice 2: 2 Alternating bell voices for polyphonic ring-out
    bell_phases = [[0.0, 0.0], [0.0, 0.0]]
    bell_dphases = [[0.0, 0.0], [0.0, 0.0]]
    bell_envs = [0.0, 0.0]
    mult_bell = math.exp(-3.5 * inv_sr)

    # Voice 3: Pad state
    pad_phases = [[0.0, 0.0] for _ in range(5)]
    pad_filtered = 0.0

    # Voice 4: Noise & Sparkle state
    noise_filtered = 0.0
    noise_env = 0.0
    mult_noise = math.exp(-6.0 * inv_sr)
    sparkle_env = 0.0
    sparkle_phase = 0.0
    sparkle_dphase = 0.0
    mult_sparkle = math.exp(-12.0 * inv_sr)

    prev_beat = -1
    sparkle_sample_offset = int(BEAT_SAMPLES * 2.5)

    append_sample = samples.append
    sin_fn = math.sin
    rand_fn = random.random

    for i in range(TOTAL_LOOP_SAMPLES):
        beat_idx = int(i / BEAT_SAMPLES)
        if beat_idx >= TOTAL_BEATS:
            beat_idx = TOTAL_BEATS - 1

        # Rhythm trigger: Bell plucks on beat events
        if beat_idx != prev_beat:
            v_idx = beat_idx % 2
            f0 = BELL_NOTES[beat_idx]
            bell_dphases[v_idx][0] = PI2 * f0 * inv_sr
            bell_dphases[v_idx][1] = PI2 * (f0 * 1.004) * inv_sr
            bell_phases[v_idx][0] = 0.0
            bell_phases[v_idx][1] = 0.0
            bell_envs[v_idx] = 1.0
            prev_beat = beat_idx

        sample_in_bar = i % BAR_SAMPLES
        # Downbeat trigger: Background radiation noise burst on measure start
        if sample_in_bar == 0:
            noise_env = 1.0

        # Sparkle trigger: High stardust ping on beat 2.5 of each measure
        if sample_in_bar == sparkle_sample_offset:
            sparkle_env = 1.0
            sparkle_phase = 0.0
            f_sp = 2600.0 + (beat_idx // 8) * 280.0
            sparkle_dphase = PI2 * f_sp * inv_sr

        # ----------------------------------------------------------------------
        # Voice 1: Bass Drone (46.25 Hz F#1 pure sine, 0.1 Hz breathing LFO)
        # ----------------------------------------------------------------------
        phase_drone += drone_dp
        lfo_breath_phase += lfo_breath_dp
        lfo_breath = 0.75 + 0.25 * sin_fn(lfo_breath_phase)
        v1 = sin_fn(phase_drone) * lfo_breath * 0.40

        # ----------------------------------------------------------------------
        # Voice 2: Lead/Arp Glass Bells (Detuned high sine pairs, decay k=3.5)
        # ----------------------------------------------------------------------
        v2_sum = 0.0
        for v in range(2):
            if bell_envs[v] > 0.0005:
                bell_phases[v][0] += bell_dphases[v][0]
                bell_phases[v][1] += bell_dphases[v][1]
                bell_envs[v] *= mult_bell
                v2_sum += (sin_fn(bell_phases[v][0]) + sin_fn(bell_phases[v][1])) * (0.5 * bell_envs[v])
        v2 = v2_sum * 0.24

        # ----------------------------------------------------------------------
        # Voice 3: Choir Pad (Dual supersaw through 600 Hz LPF + 0.2 Hz chorus)
        # ----------------------------------------------------------------------
        chord_idx = (beat_idx // 8) % 4
        ch_steps, ch_scale = chord_configs[chord_idx]
        pad_raw = 0.0
        for n_idx in range(len(ch_steps)):
            dp0, dp1 = ch_steps[n_idx]
            p0 = (pad_phases[n_idx][0] + dp0) % PI2
            p1 = (pad_phases[n_idx][1] + dp1) % PI2
            pad_phases[n_idx][0] = p0
            pad_phases[n_idx][1] = p1
            pad_raw += (p0 + p1) * inv_pi - 2.0
        pad_raw *= ch_scale

        lfo_chorus_phase += lfo_chorus_dp
        f_cut = 600.0 + 120.0 * sin_fn(lfo_chorus_phase)
        alpha = (PI2 * f_cut * inv_sr) / (1.0 + PI2 * f_cut * inv_sr)
        pad_filtered += alpha * (pad_raw - pad_filtered)
        v3 = pad_filtered * 0.24

        # ----------------------------------------------------------------------
        # Voice 4: Cosmic Texture (Stardust sparkle ping + shaped cosmic noise)
        # ----------------------------------------------------------------------
        v4_sparkle = 0.0
        if sparkle_env > 0.0005:
            sparkle_phase += sparkle_dphase
            sparkle_env *= mult_sparkle
            v4_sparkle = sin_fn(sparkle_phase) * sparkle_env

        noise_filtered += 0.15 * ((rand_fn() * 2.0 - 1.0) - noise_filtered)
        noise_env *= mult_noise
        v4 = (0.5 * v4_sparkle + 0.5 * noise_filtered * noise_env) * 0.12

        # ----------------------------------------------------------------------
        # Master Mix & Clamping to [-26000, 26000]
        # ----------------------------------------------------------------------
        master = v1 + v2 + v3 + v4

        # Boundary micro-fade (200 samples = ~4.5ms) prevents boundary click
        if i < 200:
            master *= (float(i) * 0.005)
        elif i >= TOTAL_LOOP_SAMPLES - 200:
            master *= (float(TOTAL_LOOP_SAMPLES - 1 - i) * 0.005)

        pcm = max(-26000.0, min(26000.0, master * 26000.0))
        append_sample(pcm)

    wav_bytes = pack_riff_wav_mono_16bit(SAMPLE_RATE, samples)
    music = load_music_stream_from_memory(".wav", wav_bytes, len(wav_bytes))
    music.looping = True

    # Memory pinning: store bytes reference in module table keyed by id(music)
    # This prevents Python GC deallocation and subsequent CFFI access violation
    _ACTIVE_BUFFERS[id(music)] = wav_bytes
    return music


# Standardized aliases for universal dynamic discovery & SoundLibrary compatibility
create_bgm = generate_mystery_track
create_cosmic_mystery_bgm = generate_mystery_track


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
    """Frees the streaming Music buffers from memory and unpins memory buffer."""
    if music is not None:
        _ACTIVE_BUFFERS.pop(id(music), None)
        unload_music_stream(music)


# ==============================================================================
# STANDALONE AUDITION WORKBENCH & AUTOMATED SMOKE TEST
# ==============================================================================
class BGMAuditionApp:
    """
    Interactive audition workbench allowing developers and students
    to audition procedural BGM tracks live with tempo telemetry and visualizer.
    """
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        init_window(
            self.screen_width,
            self.screen_height,
            "BGM Workbench - Cosmic Mystery (assets/audio/BGM/mystical/cosmic_mystery.py)"
        )
        set_target_fps(60)
        init_audio_device()

        self.music = generate_mystery_track()
        self.volume = 0.70
        self.pitch = 1.0
        self.is_playing = False

        # Start playback automatically in audition app
        play_bgm(self.music, self.volume, self.pitch, loop=True)
        self.is_playing = True

    def toggle_playback(self):
        if self.is_playing:
            pause_bgm(self.music)
            self.is_playing = False
        else:
            resume_bgm(self.music)
            self.is_playing = True

    def reset_playback(self):
        stop_bgm(self.music)
        play_bgm(self.music, self.volume, self.pitch, loop=True)
        self.is_playing = True

    def update(self):
        # 1. CRITICAL: Feed audio stream buffer every frame
        if self.is_playing:
            update_bgm(self.music)

        # Space or M or Gamepad A toggles Play/Pause
        pad_a = is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_FACE_DOWN) if is_gamepad_available(0) else False
        if is_key_pressed(KEY_SPACE) or is_key_pressed(KEY_M) or pad_a:
            self.toggle_playback()

        # R or Gamepad Start resets playback
        pad_start = is_gamepad_button_pressed(0, GAMEPAD_BUTTON_MIDDLE_RIGHT) if is_gamepad_available(0) else False
        if is_key_pressed(KEY_R) or pad_start:
            self.reset_playback()

        # Up/Down arrows or D-pad adjusts volume
        pad_up = is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_UP) if is_gamepad_available(0) else False
        pad_down = is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_DOWN) if is_gamepad_available(0) else False
        if is_key_pressed(KEY_UP) or pad_up:
            self.volume = min(1.0, self.volume + 0.05)
            set_music_volume(self.music, self.volume)
        elif is_key_pressed(KEY_DOWN) or pad_down:
            self.volume = max(0.0, self.volume - 0.05)
            set_music_volume(self.music, self.volume)

        # Left/Right arrows or D-pad adjusts pitch/tempo
        pad_left = is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_LEFT) if is_gamepad_available(0) else False
        pad_right = is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_RIGHT) if is_gamepad_available(0) else False
        if is_key_pressed(KEY_RIGHT) or pad_right:
            self.pitch = min(2.0, self.pitch + 0.05)
            set_music_pitch(self.music, self.pitch)
        elif is_key_pressed(KEY_LEFT) or pad_left:
            self.pitch = max(0.5, self.pitch - 0.05)
            set_music_pitch(self.music, self.pitch)

    def draw(self):
        begin_drawing()
        clear_background(Color(10, 12, 22, 255))

        # Title Header (keeps safe top region x=450..980, y=14..48 clear for global dropdowns)
        draw_text("PROCEDURAL BGM AUDITION WORKBENCH", 24, 18, 20, RAYWHITE)
        draw_text(
            "Asset: assets/audio/BGM/mystical/cosmic_mystery.py | 88 BPM F# Minor 9 Zero-G Space Drift",
            24, 46, 13, Color(160, 200, 255, 255)
        )

        # Control Info Card
        panel_y = 96
        draw_rectangle(24, panel_y, 400, 270, Color(18, 24, 38, 255))
        draw_rectangle_lines(24, panel_y, 400, 270, Color(45, 60, 95, 255))
        draw_text("BGM CONTROLS & STATUS", 40, panel_y + 14, 15, YELLOW)
        draw_text("- [Space] / [M] / Pad (A) : Play / Pause Stream", 40, panel_y + 42, 13, RAYWHITE)
        draw_text("- [Up] / [Down] / Pad Up/Dn: Volume (+/- 5%)", 40, panel_y + 68, 13, RAYWHITE)
        draw_text("- [Left] / [Right]        : Tempo / Pitch (+/- 5%)", 40, panel_y + 94, 13, RAYWHITE)
        draw_text("- [R] / Pad Start          : Reset Stream to Start", 40, panel_y + 120, 13, RAYWHITE)

        draw_text(
            f"Playback State : {'PLAYING (Looping)' if self.is_playing else 'PAUSED'}",
            40, panel_y + 154, 13, GREEN if self.is_playing else RED
        )
        draw_text(f"Volume         : {int(self.volume * 100)}%", 40, panel_y + 178, 13, SKYBLUE)
        draw_text(f"Tempo / Pitch  : {self.pitch:.2f}x ({BPM * self.pitch:.1f} BPM)", 40, panel_y + 202, 13, SKYBLUE)
        draw_text("Buffer Pinning : Active (_ACTIVE_BUFFERS)", 40, panel_y + 226, 13, LIME)

        # Real-time Stream Output Visualizer
        vis_x = 450
        vis_y = 96
        vis_w = 800
        vis_h = 580
        draw_rectangle(vis_x, vis_y, vis_w, vis_h, Color(14, 18, 30, 255))
        draw_rectangle_lines(vis_x, vis_y, vis_w, vis_h, Color(45, 60, 95, 255))
        draw_text("STREAM BUFFER & 4-VOICE HARMONIC MONITOR", vis_x + 20, vis_y + 16, 15, ORANGE)

        time_played = get_music_time_played(self.music)
        time_total = get_music_time_length(self.music)
        loop_progress = (time_played / time_total) if time_total > 0.0 else 0.0
        current_beat = int(loop_progress * TOTAL_BEATS) % TOTAL_BEATS
        current_bar = (current_beat // BEATS_PER_BAR) % TOTAL_BARS
        current_chord_idx = (current_beat // 8) % 4
        chord_names = ["F#m9 (Bars 1-2)", "Dmaj7 (Bars 3-4)", "Bm9 (Bars 5-6)", "C#m7 (Bars 7-8)"]

        # Sequencer Activity Grid (32 Beats across 8 Bars)
        grid_y = vis_y + 54
        step_w = (vis_w - 40) // TOTAL_BEATS
        for s in range(TOTAL_BEATS):
            bx = vis_x + 20 + (s * step_w)
            is_cur = (s == current_beat) and self.is_playing
            bar_color = Color(35, 50, 75, 255) if (s // 4) % 2 == 0 else Color(22, 32, 50, 255)
            box_col = ORANGE if is_cur else bar_color
            draw_rectangle(bx, grid_y, step_w - 2, 32, box_col)

        draw_text(
            f"Beat: {current_beat + 1} / {TOTAL_BEATS} | Bar: {current_bar + 1} / {TOTAL_BARS} | Loop: {time_played:.2f}s / {time_total:.2f}s",
            vis_x + 20, grid_y + 42, 13, LIGHTGRAY
        )

        # Loop Progress Bar
        bar_y = vis_y + 140
        draw_rectangle(vis_x + 20, bar_y, vis_w - 40, 16, Color(22, 28, 44, 255))
        fill_w = int(loop_progress * (vis_w - 40))
        draw_rectangle(vis_x + 20, bar_y, fill_w, 16, SKYBLUE)
        draw_rectangle_lines(vis_x + 20, bar_y, vis_w - 40, 16, Color(60, 80, 110, 255))

        # Active Harmonic Section Info
        info_y = vis_y + 180
        draw_rectangle(vis_x + 20, info_y, vis_w - 40, 50, Color(20, 28, 46, 255))
        draw_rectangle_lines(vis_x + 20, info_y, vis_w - 40, 50, Color(50, 70, 110, 255))
        draw_text("ACTIVE HARMONY :", vis_x + 36, info_y + 16, 14, YELLOW)
        draw_text(chord_names[current_chord_idx], vis_x + 190, info_y + 16, 14, GREEN)

        # Multi-Voice Channel Telemetry Meters
        meters_y = vis_y + 256
        draw_text("4 PROCEDURAL VOICE LAYERS :", vis_x + 20, meters_y, 14, GOLD)

        # Voice 1 Telemetry
        v1_y = meters_y + 28
        draw_rectangle(vis_x + 20, v1_y, vis_w - 40, 56, Color(18, 24, 38, 255))
        draw_rectangle_lines(vis_x + 20, v1_y, vis_w - 40, 56, Color(40, 55, 85, 255))
        draw_text("Voice 1: Sub-Bass Drone (Gain: 0.40)", vis_x + 32, v1_y + 8, 13, Color(120, 200, 255, 255))
        draw_text("Pure Sine at F#1 (46.25 Hz) with 0.1 Hz breathing amplitude modulation", vis_x + 32, v1_y + 30, 12, LIGHTGRAY)

        # Voice 2 Telemetry
        v2_y = v1_y + 68
        draw_rectangle(vis_x + 20, v2_y, vis_w - 40, 56, Color(18, 24, 38, 255))
        draw_rectangle_lines(vis_x + 20, v2_y, vis_w - 40, 56, Color(40, 55, 85, 255))
        active_bell_freq = BELL_NOTES[current_beat]
        draw_text("Voice 2: Lead/Arp Glass Bells (Gain: 0.24)", vis_x + 32, v2_y + 8, 13, Color(255, 215, 100, 255))
        draw_text(
            f"Detuned High Sines (f0={active_bell_freq:.1f} Hz, f1={active_bell_freq * 1.004:.1f} Hz) | Decay k=3.5",
            vis_x + 32, v2_y + 30, 12, LIGHTGRAY
        )

        # Voice 3 Telemetry
        v3_y = v2_y + 68
        draw_rectangle(vis_x + 20, v3_y, vis_w - 40, 56, Color(18, 24, 38, 255))
        draw_rectangle_lines(vis_x + 20, v3_y, vis_w - 40, 56, Color(40, 55, 85, 255))
        draw_text("Voice 3: Ethereal Choir Pad (Gain: 0.24)", vis_x + 32, v3_y + 8, 13, Color(180, 150, 255, 255))
        draw_text("Dual Supersaw (Saw + Detuned Saw) through 600 Hz LPF with 0.2 Hz Chorus LFO", vis_x + 32, v3_y + 30, 12, LIGHTGRAY)

        # Voice 4 Telemetry
        v4_y = v3_y + 68
        draw_rectangle(vis_x + 20, v4_y, vis_w - 40, 56, Color(18, 24, 38, 255))
        draw_rectangle_lines(vis_x + 20, v4_y, vis_w - 40, 56, Color(40, 55, 85, 255))
        draw_text("Voice 4: Cosmic Texture (Gain: 0.12)", vis_x + 32, v4_y + 8, 13, Color(220, 220, 220, 255))
        draw_text("High Stardust Sparkle Pings (2400-3600 Hz, k=12) & Background Radiation Downbeat Noise", vis_x + 32, v4_y + 30, 12, LIGHTGRAY)

        # Top Bar Settings Dropdowns (x=450..980, y=14..48 cleared)
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
