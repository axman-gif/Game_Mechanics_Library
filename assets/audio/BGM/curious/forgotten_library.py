# -*- coding: utf-8 -*-
"""
Procedural Background Music (BGM) Synthesizer - Forgotten Library
=================================================================
Type             : Procedural Audio BGM (Music Stream)
Target File      : assets/audio/BGM/curious/forgotten_library.py
Waveforms Used   : Muted contrabass drone, bell-modeled celesta/glockenspiel, modulated string pad, noise transients
Category         : Interactive BGM Soundtracks
Vibe             : Curious (Arcane Scholarly Archive / Lore Discovery)

Problem Solved:
  Eliminates static, heavy external audio assets by algorithmically synthesizing an
  atmospheric 8-bar arcane research archive theme directly in RAM. Streaming through
  Raylib's Music struct minimizes memory footprint while procedural generation guarantees
  mathematically perfect loop seams with zero audio pop artifacts.

Musical Theory & Mathematical Rationale:
  - Tempo: 92.0 Beats Per Minute (BPM) in 4/4 meter.
  - Clock Timing:
      Beat Duration          = 60.0 / 92.0 = 0.652174 seconds per beat.
      Loop Duration (8 Bars) = 32 beats * (60.0 / 92.0) = 20.869565 seconds.
      Total Sample Count     = round(44100 * 20.869565) = 920,348 samples.
  - Modal Architecture: C Lydian Mode (C, D, E, F#, G, A, B).
      Harmonic Progression (2 bars each across 8 bars / 32 beats):
        Bars 1-2 (Beats 0..7)  : Cmaj7(#11) (Root C, Major 3rd E, 5th G, Major 7th B, #11 F#)
        Bars 3-4 (Beats 8..15) : D/C        (D major triad over C pedal bass: C, D, F#, A)
        Bars 5-6 (Beats 16..23): Em7        (Root E, Minor 3rd G, 5th B, Minor 7th D)
        Bars 7-8 (Beats 24..31): Bm7        (Root B, Minor 3rd D, 5th F#, Minor 7th A)
  - 4 Procedural Voice Layers:
      Voice 1 (Contrabass Drone, Gain 0.38):
        Muted low contrabass anchor. Deep C2 fundamental (65.41 Hz) anchored during bars 1-4
        as a mystery pedal point, shifting to E2 (82.41 Hz) on bars 5-6 and B1 (61.74 Hz) on bars 7-8,
        enriched with warm 2nd and 3rd harmonics (0.18 and 0.05 relative amplitude).
      Voice 2 (Celesta & Glockenspiel Lead, Gain 0.28):
        Sparkling bell-like arpeggios dancing across higher octaves (C5 to G6). Employs physical
        modeling of struck metal bars with non-harmonic overtones (fundamental, 2.756f, 5.404f)
        and natural dual-rate exponential decays.
      Voice 3 (Dusty String Pad, Gain 0.22):
        Atmospheric multi-oscillator string pad shaped by a dynamic single-pole low-pass filter
        sweeping smoothly between 300 Hz and 1200 Hz across the loop, evoking dust motes drifting
        in sunlight through stained-glass library windows.
      Voice 4 (Quill & Parchment Texture, Gain 0.12):
        Tactile foley noise transients on measure boundaries (page rustle) and midpoints (quill
        scratches on parchment) simulating scholarly manuscript research.
  - Master Clamping:
      Master mix softly saturated via tanh and clamped strictly to [-26500, 26500]
      in signed 16-bit mono PCM, providing 2.0 dB of clean headroom.

Direct C++ Raylib Translation (raylib.h):
  struct ForgottenLibraryBGM {
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
BPM = 92.0

# 8 Bars of 4/4 time at 92.0 BPM = exactly 32 beats
TOTAL_BEATS = 32
SECONDS_PER_BEAT = 60.0 / BPM
LOOP_DURATION_SECONDS = TOTAL_BEATS * SECONDS_PER_BEAT

# Exact loop sample count: round(44100 * 32 * 60.0 / 92.0) = 920,348 samples
TOTAL_LOOP_SAMPLES = 920348
SAMPLES_PER_BEAT = TOTAL_LOOP_SAMPLES / float(TOTAL_BEATS)

# Harmonic progression metadata for UI and synthesis analysis
CHORD_NAMES = [
    "Cmaj7(#11)", "Cmaj7(#11)",
    "D/C", "D/C",
    "Em7", "Em7",
    "Bm7", "Bm7"
]

# 32-step Celesta and Glockenspiel bell arpeggio sequence in C Lydian (1 note per beat)
# Format: (start_beat, duration_beats, frequency_hz)
CELESTA_MELODY = [
    # Bars 1-2 (Beats 0..7): Cmaj7(#11) - Mystical discovery of ancient codex
    (0.0, 1.5, 659.25),   # E5
    (1.0, 1.5, 783.99),   # G5
    (2.0, 1.5, 987.77),   # B5
    (3.0, 1.5, 739.99),   # F#5 (#11 Lydian signature)
    (4.0, 1.5, 1318.51),  # E6
    (5.0, 1.5, 987.77),   # B5
    (6.0, 1.5, 783.99),   # G5
    (7.0, 1.5, 739.99),   # F#5
    # Bars 3-4 (Beats 8..15): D/C - Expanding curiosity & arcane revelations
    (8.0, 1.5, 739.99),   # F#5
    (9.0, 1.5, 880.00),   # A5
    (10.0, 1.5, 1174.66), # D6
    (11.0, 1.5, 1479.98), # F#6
    (12.0, 1.5, 1174.66), # D6
    (13.0, 1.5, 880.00),  # A5
    (14.0, 1.5, 739.99),  # F#5
    (15.0, 1.5, 587.33),  # D5
    # Bars 5-6 (Beats 16..23): Em7 - Deep vaulted archives and forgotten lore
    (16.0, 1.5, 783.99),  # G5
    (17.0, 1.5, 987.77),  # B5
    (18.0, 1.5, 1318.51), # E6
    (19.0, 1.5, 1567.98), # G6
    (20.0, 1.5, 1318.51), # E6
    (21.0, 1.5, 987.77),  # B5
    (22.0, 1.5, 783.99),  # G5
    (23.0, 1.5, 659.25),  # E5
    # Bars 7-8 (Beats 24..31): Bm7 - Quiet reverence leading back to tonic
    (24.0, 1.5, 739.99),  # F#5
    (25.0, 1.5, 880.00),  # A5
    (26.0, 1.5, 1174.66), # D6
    (27.0, 1.5, 1479.98), # F#6
    (28.0, 1.5, 1174.66), # D6
    (29.0, 1.5, 987.77),  # B5
    (30.0, 1.5, 880.00),  # A5
    (31.0, 1.5, 739.99),  # F#5
]

# Module-level pinned buffer registry to prevent Python GC deallocation and CFFI access violations
_ACTIVE_BUFFERS = {}


# ==============================================================================
# IN-MEMORY RIFF/WAV PACKER (C++ 44-Byte Header Equivalent)
# ==============================================================================
def pack_riff_wav_mono_16bit(sample_rate: int, raw_samples) -> bytes:
    """
    Packs signed 16-bit PCM integer samples (-32767 to 32767) into an in-memory
    canonical 44-byte RIFF/WAVE container.
    """
    if isinstance(raw_samples, (bytes, bytearray)):
        pcm_bytes = bytes(raw_samples)
    else:
        num_samples = len(raw_samples)
        pcm_bytes = bytearray(num_samples * 2)
        p_into = py_struct.pack_into
        for i in range(num_samples):
            val = raw_samples[i]
            clamped = max(-32767, min(32767, int(val)))
            p_into('<h', pcm_bytes, i * 2, clamped)
        pcm_bytes = bytes(pcm_bytes)

    riff_id = b'RIFF'
    wave_id = b'WAVE'
    fmt_id = b'fmt '
    fmt_size = 16
    audio_format = 1        # PCM format
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
def create_forgotten_library_bgm() -> Music:
    """
    Synthesizes the 8-bar 'Forgotten Library' curious soundtrack in RAM.
    Returns an initialized Raylib Music stream with looping enabled.
    """
    sin = math.sin
    cos = math.cos
    exp = math.exp
    tanh = math.tanh
    inv_sr = 1.0 / float(SAMPLE_RATE)
    pack_into = py_struct.pack_into

    # --------------------------------------------------------------------------
    # Step 1: Pre-synthesize Celesta & Glockenspiel Bell Arpeggios (Voice 2)
    # Struck bar physical modeling with seamless wrap-around loop tails
    # --------------------------------------------------------------------------
    celesta_buffer = [0.0] * TOTAL_LOOP_SAMPLES
    bell_decay_samples = int(1.4 * SAMPLE_RATE)  # 1.4s ringing chime decay

    for start_b, dur_b, target_freq in CELESTA_MELODY:
        start_idx = int(start_b * SAMPLES_PER_BEAT)
        omega1 = PI2 * target_freq * inv_sr
        omega2 = PI2 * (target_freq * 2.756) * inv_sr   # Glockenspiel bar overtone
        omega3 = PI2 * (target_freq * 5.404) * inv_sr   # High strike harmonic

        p1 = 0.0
        p2 = 0.0
        p3 = 0.0

        for k in range(bell_decay_samples):
            t_sec = float(k) * inv_sr
            # Dual-rate exponential envelope (fast strike transient + warm body decay)
            env_fund = exp(-3.8 * t_sec)
            env_over1 = exp(-9.0 * t_sec)
            env_over2 = exp(-16.0 * t_sec)

            # 80-sample soft attack ramp (1.8ms click prevention)
            if k < 80:
                att = float(k) / 80.0
            else:
                att = 1.0

            s_val = att * (
                0.72 * sin(p1) * env_fund +
                0.20 * sin(p2) * env_over1 +
                0.08 * sin(p3) * env_over2
            )

            # Seamless wrap-around modulo preserves ringing chimes across 8-bar seam
            buf_idx = (start_idx + k) % TOTAL_LOOP_SAMPLES
            celesta_buffer[buf_idx] += s_val

            p1 += omega1
            p2 += omega2
            p3 += omega3

    # --------------------------------------------------------------------------
    # Step 2: Main Audio Generation & Multi-Voice Accumulation Loop
    # --------------------------------------------------------------------------
    # Phase accumulators for all continuous oscillators
    phase_bass = 0.0
    phase_pad_c = 0.0
    phase_pad_e = 0.0
    phase_pad_g = 0.0
    phase_pad_b = 0.0

    # Low-pass filter state for dusty string pad
    filtered_pad = 0.0

    # Noise filter state for quill scratch & paper rustle
    prev_noise = 0.0

    # Preallocate PCM byte buffer for maximum throughput
    pcm_buffer = bytearray(TOTAL_LOOP_SAMPLES * 2)

    for i in range(TOTAL_LOOP_SAMPLES):
        t_now = float(i) * inv_sr
        beat_f = float(i) / SAMPLES_PER_BEAT
        bar_idx = (int(beat_f) // 4) % 8
        beat_in_bar_f = beat_f % 4.0
        beat_in_bar_int = int(beat_in_bar_f)
        sub_beat_f = beat_in_bar_f - float(beat_in_bar_int)

        # ----------------------------------------------------------------------
        # Voice 1: Muted Contrabass Drone (Gain 0.38)
        # Deep tonal anchor: C2 (65.41 Hz) pedal point on bars 1-4,
        # moving to E2 (82.41 Hz) on bars 5-6, and B1 (61.74 Hz) on bars 7-8.
        # ----------------------------------------------------------------------
        if bar_idx < 4:
            target_bass_f = 65.41   # C2
        elif bar_idx < 6:
            target_bass_f = 82.41   # E2
        else:
            target_bass_f = 61.74   # B1

        phase_bass += PI2 * target_bass_f * inv_sr
        # Warm contrabass harmonic profile (fundamental + warm 2nd and 3rd harmonics)
        bass_wave = 0.82 * sin(phase_bass) + 0.14 * sin(2.0 * phase_bass) + 0.04 * sin(3.0 * phase_bass)
        v1 = 0.38 * bass_wave

        # ----------------------------------------------------------------------
        # Voice 2: Celesta & Glockenspiel Bell Lead (Gain 0.28)
        # ----------------------------------------------------------------------
        v2 = 0.28 * celesta_buffer[i]

        # ----------------------------------------------------------------------
        # Voice 3: Dusty Atmospheric String Pad (Gain 0.22)
        # Multi-oscillator chord pad filtered through a dynamic 300..1200 Hz sweep
        # ----------------------------------------------------------------------
        if bar_idx < 2:
            # Cmaj7(#11): C3 (130.81), G3 (196.00), B3 (246.94), F#4 (369.99)
            f_c, f_e, f_g, f_b = 130.81, 196.00, 246.94, 369.99
        elif bar_idx < 4:
            # D/C: C3 (130.81), F#3 (185.00), A3 (220.00), D4 (293.66)
            f_c, f_e, f_g, f_b = 130.81, 185.00, 220.00, 293.66
        elif bar_idx < 6:
            # Em7: E3 (164.81), G3 (196.00), B3 (246.94), D4 (293.66)
            f_c, f_e, f_g, f_b = 164.81, 196.00, 246.94, 293.66
        else:
            # Bm7: B2 (123.47), F#3 (185.00), A3 (220.00), D4 (293.66)
            f_c, f_e, f_g, f_b = 123.47, 185.00, 220.00, 293.66

        phase_pad_c += PI2 * f_c * inv_sr
        phase_pad_e += PI2 * f_e * inv_sr
        phase_pad_g += PI2 * f_g * inv_sr
        phase_pad_b += PI2 * f_b * inv_sr

        # Chord oscillator blend with subtle chorus beating
        pad_raw = 0.25 * (
            sin(phase_pad_c) +
            sin(phase_pad_e) +
            sin(phase_pad_g) +
            sin(phase_pad_b)
        )

        # Dynamic Low-Pass Filter: sweeps smoothly between 300 Hz and 1200 Hz
        # fc(t) = 750 + 450 * sin(2*pi*t/LOOP_DURATION - pi/2)
        # Guarantees seamless filter matching at t=0 and t=LOOP_DURATION (300 Hz)
        mod_lfo = sin(PI2 * (float(i) / float(TOTAL_LOOP_SAMPLES)) - 0.5 * math.pi)
        cutoff_hz = 750.0 + 450.0 * mod_lfo
        # Single-pole IIR lowpass filter: y[n] = y[n-1] + alpha * (x[n] - y[n-1])
        alpha = (PI2 * cutoff_hz) / (SAMPLE_RATE + PI2 * cutoff_hz)
        filtered_pad += alpha * (pad_raw - filtered_pad)
        v3 = 0.22 * filtered_pad

        # ----------------------------------------------------------------------
        # Voice 4: Quill-Scratch and Paper-Rustle Texture (Gain 0.12)
        # Tactile parchment rustles on bar starts & rhythmic quill friction
        # ----------------------------------------------------------------------
        raw_noise = random.random() * 2.0 - 1.0
        hp_noise = raw_noise - 0.82 * prev_noise
        prev_noise = raw_noise

        v4_rustle = 0.0
        v4_scratch = 0.0

        # Paper rustle transient at measure boundary (beat 0 of each bar)
        if beat_in_bar_int == 0:
            t_rustle = sub_beat_f * SECONDS_PER_BEAT
            env_rustle = exp(-14.0 * t_rustle)
            v4_rustle = hp_noise * env_rustle * 0.70

        # Quill writing scratch on measure midpoint (beat 2 of each bar)
        if beat_in_bar_int == 2:
            t_scratch = sub_beat_f * SECONDS_PER_BEAT
            env_scratch = exp(-26.0 * t_scratch)
            v4_scratch = hp_noise * env_scratch * 0.85

        v4 = 0.12 * (v4_rustle + v4_scratch)

        # ----------------------------------------------------------------------
        # Master Mix, Soft Saturation & Clamping
        # ----------------------------------------------------------------------
        master_mix = tanh((v1 + v2 + v3 + v4) * 1.25)

        # Seamless loop boundary micro-fade (128 samples cosine ramp)
        if i < 128:
            master_mix *= 0.5 * (1.0 - cos(math.pi * float(i) / 128.0))
        elif i > TOTAL_LOOP_SAMPLES - 128:
            master_mix *= 0.5 * (1.0 - cos(math.pi * float(TOTAL_LOOP_SAMPLES - 1 - i) / 128.0))

        # Clamp strictly to [-26500, 26500] in 16-bit signed PCM
        pcm_int = int(master_mix * 26500.0)
        clamped_pcm = max(-26500, min(26500, pcm_int))
        pack_into('<h', pcm_buffer, i * 2, clamped_pcm)

    # Encapsulate in 44-byte RIFF container and load into Raylib
    wav_bytes = pack_riff_wav_mono_16bit(SAMPLE_RATE, pcm_buffer)
    music = load_music_stream_from_memory(".wav", wav_bytes, len(wav_bytes))
    music.looping = True

    # Pin WAV buffer in memory to protect from Python GC while streaming
    _ACTIVE_BUFFERS[id(music)] = wav_bytes
    return music


# Standardized alias mappings for universal dynamic discovery
create_bgm = create_forgotten_library_bgm
generate_forgotten_library_track = create_forgotten_library_bgm
bgm_curious_forgotten_library = create_forgotten_library_bgm


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
    to audition the Forgotten Library BGM live with telemetry and visualizer.
    """
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        init_window(self.screen_width, self.screen_height,
                    "BGM Workbench - Forgotten Library (assets/audio/BGM/curious/forgotten_library.py)")
        set_target_fps(60)
        init_audio_device()

        self.music = create_forgotten_library_bgm()
        self.volume = 0.75
        self.pitch = 1.0
        self.is_playing = False
        self.pulse_anim = 0.0

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

    def update(self):
        dt = min(get_frame_time(), 0.05)

        # CRITICAL: Feed audio stream buffer every frame
        if self.is_playing:
            update_bgm(self.music)

        # Pulse animation decay
        if self.pulse_anim > 0.0:
            self.pulse_anim = max(0.0, self.pulse_anim - dt * 2.0)

        # Keyboard & Gamepad Dual Controls
        # Space / M / Gamepad A: Play/Pause
        if is_key_pressed(KEY_SPACE) or is_key_pressed(KEY_M) or is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_FACE_DOWN):
            self.toggle_playback()

        # Up/Down / Gamepad D-pad Up/Down: Volume
        if is_key_pressed(KEY_UP) or is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_UP):
            self.volume = min(1.0, self.volume + 0.05)
            set_music_volume(self.music, self.volume)
        elif is_key_pressed(KEY_DOWN) or is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_DOWN):
            self.volume = max(0.0, self.volume - 0.05)
            set_music_volume(self.music, self.volume)

        # Left/Right / Gamepad D-pad Left/Right: Pitch/Tempo
        if is_key_pressed(KEY_RIGHT) or is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_RIGHT):
            self.pitch = min(2.0, self.pitch + 0.05)
            set_music_pitch(self.music, self.pitch)
        elif is_key_pressed(KEY_LEFT) or is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_LEFT):
            self.pitch = max(0.5, self.pitch - 0.05)
            set_music_pitch(self.music, self.pitch)

        # [R] / Gamepad Start: Restart Loop
        if is_key_pressed(KEY_R) or is_gamepad_button_pressed(0, GAMEPAD_BUTTON_MIDDLE_RIGHT):
            stop_bgm(self.music)
            play_bgm(self.music, self.volume, self.pitch, loop=True)
            self.is_playing = True

    def draw(self):
        begin_drawing()
        clear_background(Color(12, 16, 24, 255))

        # Title Header (kept in left region x < 450, leaving top-bar x=450..980, y=14..48 clear)
        draw_text("PROCEDURAL BGM AUDITION WORKBENCH", 24, 18, 18, RAYWHITE)
        draw_text("Asset: assets/audio/BGM/curious/forgotten_library.py | 92.0 BPM C Lydian Arcane Archive",
                  24, 44, 12, Color(120, 210, 255, 255))

        # ----------------------------------------------------------------------
        # LEFT COLUMN: Telemetry & Controls Info Cards
        # ----------------------------------------------------------------------
        panel_y = 74
        # Telemetry Card
        draw_rectangle(24, panel_y, 400, 250, Color(18, 24, 36, 255))
        draw_rectangle_lines(24, panel_y, 400, 250, Color(40, 60, 80, 255))
        draw_text("ARCANE ARCHIVE TELEMETRY", 40, panel_y + 14, 14, Color(120, 210, 255, 255))
        draw_text("Tempo / Meter   : 92.0 BPM | 4/4 Time | 8 Bars", 40, panel_y + 40, 12, RAYWHITE)
        draw_text("Harmonic Mode   : C Lydian (C - D - E - F# - G - A - B)", 40, panel_y + 64, 12, RAYWHITE)
        draw_text("Progression     : Cmaj7(#11) -> D/C -> Em7 -> Bm7 (2b)", 40, panel_y + 88, 12, LIGHTGRAY)
        draw_text("Loop Duration   : 20.87s (920,348 Samples)", 40, panel_y + 112, 12, LIGHTGRAY)
        draw_text("Voice 1 (Bass)  : Contrabass Drone (65.41 Hz C2, Gain 0.38)", 40, panel_y + 136, 12, Color(140, 200, 140, 255))
        draw_text("Voice 2 (Chime) : Celesta & Glockenspiel Lead (Gain 0.28)", 40, panel_y + 160, 12, Color(255, 220, 110, 255))
        draw_text("Voice 3 (Pad)   : Modulated Dusty String Pad (Gain 0.22)", 40, panel_y + 184, 12, Color(130, 210, 255, 255))
        draw_text("Voice 4 (Foley) : Quill Scratch & Page Rustle (Gain 0.12)", 40, panel_y + 208, 12, Color(240, 170, 140, 255))

        # Controls Card
        ctrl_y = panel_y + 266
        draw_rectangle(24, ctrl_y, 400, 240, Color(18, 24, 36, 255))
        draw_rectangle_lines(24, ctrl_y, 400, 240, Color(40, 60, 80, 255))
        draw_text("BGM CONTROLS", 40, ctrl_y + 14, 14, Color(255, 200, 80, 255))
        draw_text("- [Space] / [M] / Gamepad (A)  : Play / Pause Stream", 40, ctrl_y + 40, 12, RAYWHITE)
        draw_text("- [Up] / [Down] / Gamepad D-pad: Volume (+/- 5%)", 40, ctrl_y + 64, 12, RAYWHITE)
        draw_text("- [Left] / [Right] / D-pad L/R : Tempo / Pitch (+/- 5%)", 40, ctrl_y + 88, 12, RAYWHITE)
        draw_text("- [R] / Gamepad Start          : Reset Loop to Beginning", 40, ctrl_y + 112, 12, RAYWHITE)
        draw_text(f"Playback State  : {'PLAYING (Looping)' if self.is_playing else 'PAUSED'}",
                  40, ctrl_y + 146, 13, GREEN if self.is_playing else RED)
        draw_text(f"Master Volume   : {int(self.volume * 100)}%", 40, ctrl_y + 170, 13, SKYBLUE)
        draw_text(f"Tempo / Pitch   : {self.pitch:.2f}x", 40, ctrl_y + 194, 13, SKYBLUE)
        draw_text("Buffer State    : Pinned in _ACTIVE_BUFFERS (Safe)", 40, ctrl_y + 218, 11, GREEN)

        # ----------------------------------------------------------------------
        # RIGHT COLUMN: Sequencer Grid, Loop Timeline & Visual Procedural Tomes
        # Top-bar safe area (x=450..980, y=14..48) is strictly avoided!
        # ----------------------------------------------------------------------
        vis_x = 450
        vis_y = 74
        vis_w = 806
        vis_h = 620
        draw_rectangle(vis_x, vis_y, vis_w, vis_h, Color(15, 20, 30, 255))
        draw_rectangle_lines(vis_x, vis_y, vis_w, vis_h, Color(40, 60, 80, 255))
        draw_text("ARCANE ARCHIVE SEQUENCER & VOICE TELEMETRY", vis_x + 20, vis_y + 16, 15, Color(120, 210, 255, 255))

        # Real-time Playback Clock
        time_played = get_music_time_played(self.music)
        time_total = get_music_time_length(self.music)
        loop_progress = (time_played / time_total) if time_total > 0.0 else 0.0
        current_beat = int(loop_progress * TOTAL_BEATS) % TOTAL_BEATS
        current_bar = (current_beat // 4) % 8
        current_chord = CHORD_NAMES[current_bar]

        # 32-Step Beat Sequencer Grid
        grid_y = vis_y + 54
        step_w = (vis_w - 40) // TOTAL_BEATS
        for s in range(TOTAL_BEATS):
            bx = vis_x + 20 + (s * step_w)
            is_active = (s == current_beat) and self.is_playing
            bar_num = s // 4

            # Harmonically tinted color accents
            if bar_num in (0, 1):    # Cmaj7(#11)
                base_col = Color(24, 45, 60, 255) if (s % 4 == 0) else Color(16, 30, 42, 255)
            elif bar_num in (2, 3):  # D/C
                base_col = Color(55, 46, 22, 255) if (s % 4 == 0) else Color(36, 30, 15, 255)
            elif bar_num in (4, 5):  # Em7
                base_col = Color(20, 50, 32, 255) if (s % 4 == 0) else Color(14, 34, 22, 255)
            else:                    # Bm7
                base_col = Color(42, 28, 54, 255) if (s % 4 == 0) else Color(28, 18, 36, 255)

            box_col = Color(120, 220, 255, 255) if is_active else base_col
            draw_rectangle(bx, grid_y, step_w - 2, 32, box_col)
            if is_active:
                draw_rectangle_lines(bx, grid_y, step_w - 2, 32, RAYWHITE)

        draw_text(f"Sequencer Beat: {current_beat + 1:02d} / 32 | Bar: {current_bar + 1} / 8 | Active Chord: {current_chord} | Time: {time_played:.2f}s / {time_total:.2f}s",
                  vis_x + 20, grid_y + 42, 12, LIGHTGRAY)

        # Loop Progress Bar
        bar_y = vis_y + 128
        draw_rectangle(vis_x + 20, bar_y, vis_w - 40, 12, Color(22, 28, 38, 255))
        fill_w = int(loop_progress * (vis_w - 40))
        draw_rectangle(vis_x + 20, bar_y, fill_w, 12, Color(120, 210, 255, 255))
        draw_rectangle_lines(vis_x + 20, bar_y, vis_w - 40, 12, Color(45, 65, 90, 255))

        # ----------------------------------------------------------------------
        # Ancient Lore Tomes (4 Procedural Visual Voice Pillars)
        # ----------------------------------------------------------------------
        tome_y = vis_y + 160
        draw_text("ARCANE LIBRARY ARCHIVE TOMES (PROCEDURAL VOICE VISUALIZER)",
                  vis_x + 20, tome_y, 13, Color(255, 200, 80, 255))

        pillars = [
            ("CONTRABASS BASS", "C2 / E2 / B1 Anchor", Color(90, 190, 120, 255), True),
            ("CELESTA CHIMES", "C Lydian Arpeggios", Color(255, 220, 110, 255), self.is_playing),
            ("DUSTY STRING PAD", "300..1200 Hz Filter", Color(120, 200, 255, 255), self.is_playing),
            ("QUILL & PARCHMENT", "Page Rustle & Ink", Color(240, 160, 130, 255), (current_beat % 2 == 0) and self.is_playing),
        ]

        pillar_w = (vis_w - 60) // 4
        for p_idx, (p_title, p_sub, p_col, p_glow) in enumerate(pillars):
            px = vis_x + 20 + p_idx * (pillar_w + 7)
            py = tome_y + 26
            ph = 140

            # Ancient book spine / bookshelf panel
            draw_rectangle(px, py, pillar_w, ph, Color(22, 28, 40, 255))
            draw_rectangle_lines(px, py, pillar_w, ph, Color(45, 62, 85, 255))

            # Codex book icon & arcane runes
            rx = px + pillar_w // 2
            ry = py + 45
            glyph_alpha = 255 if p_glow else 80
            g_col = Color(p_col.r, p_col.g, p_col.b, glyph_alpha)

            # Draw procedural codex symbol
            draw_rectangle_lines(rx - 16, ry - 18, 32, 36, g_col)
            draw_line(rx, ry - 18, rx, ry + 18, g_col)
            draw_line(rx - 12, ry - 8, rx - 3, ry - 8, g_col)
            draw_line(rx + 3, ry - 8, rx + 12, ry - 8, g_col)
            draw_line(rx - 12, ry + 2, rx - 3, ry + 2, g_col)
            draw_line(rx + 3, ry + 2, rx + 12, ry + 2, g_col)
            draw_circle_lines(rx, ry, 22, g_col)

            # Labels
            draw_text(p_title, px + 8, py + 92, 11, g_col)
            draw_text(p_sub, px + 8, py + 112, 10, LIGHTGRAY)

        # ----------------------------------------------------------------------
        # Voice Layer Oscillators & Filter Readout Panel
        # ----------------------------------------------------------------------
        meter_y = tome_y + 186
        draw_rectangle(vis_x + 20, meter_y, vis_w - 40, 160, Color(18, 24, 36, 255))
        draw_rectangle_lines(vis_x + 20, meter_y, vis_w - 40, 160, Color(40, 60, 80, 255))
        draw_text("LAYER OSCILLATOR & DYNAMIC FILTER TELEMETRY", vis_x + 36, meter_y + 12, 13, Color(120, 210, 255, 255))

        bass_note_name = "C2 (65.41 Hz)" if current_bar < 4 else ("E2 (82.41 Hz)" if current_bar < 6 else "B1 (61.74 Hz)")
        draw_text(f"[Voice 1: Contrabass]  Active Anchor: {bass_note_name} | Harmonics: 2nd + 3rd | Gain: 0.38",
                  vis_x + 36, meter_y + 38, 12, Color(140, 200, 140, 255))

        cur_note_freq = CELESTA_MELODY[current_beat][2]
        draw_text(f"[Voice 2: Celesta Chime] Struck Note Freq: {cur_note_freq:.1f} Hz | Partials: 1.0f, 2.76f, 5.40f | Gain: 0.28",
                  vis_x + 36, meter_y + 64, 12, Color(255, 220, 110, 255))

        # Real-time Filter Cutoff approximation
        cur_cutoff = 750.0 + 450.0 * math.sin(PI2 * loop_progress - 0.5 * math.pi)
        draw_text(f"[Voice 3: String Pad]    Harmonic Pad: {current_chord} | Dynamic Low-Pass Cutoff: {cur_cutoff:.0f} Hz | Gain: 0.22",
                  vis_x + 36, meter_y + 90, 12, Color(130, 210, 255, 255))

        foley_state = "PAPER RUSTLE (Bar Boundary)" if (current_beat % 4 == 0) else ("QUILL SCRATCH (Parchment Ink)" if (current_beat % 4 == 2) else "QUIET ARCHIVE")
        draw_text(f"[Voice 4: Texture Foley] Parchment State: {foley_state} | Gain: 0.12",
                  vis_x + 36, meter_y + 116, 12, Color(240, 170, 140, 255))

        # Top Bar Settings Dropdowns & Gamepad Badge
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
