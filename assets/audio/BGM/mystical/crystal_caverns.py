# -*- coding: utf-8 -*-
"""
Procedural Background Music (BGM) Synthesizer - Crystal Caverns
==============================================================
Type             : Procedural Audio BGM (Music Stream)
Target File      : assets/audio/BGM/mystical/crystal_caverns.py
Waveforms Used   : Pure sine sub-bass, odd-harmonic additive celesta, chorused pad, chirp FM echoes
Category         : Mystical BGM Soundtracks

Problem Solved:
  Eliminates static, multi-megabyte audio soundtrack assets by algorithmically
  synthesizing a subterranean, gemstone-resonant 8-bar loop purely in RAM.
  Streams dynamically through Raylib's Music struct with zero disk I/O,
  strict CFFI memory buffer pinning, and seamless phase continuity.

Musical Theory & Mathematical Rationale:
  - Tempo: 90.0 Beats Per Minute (BPM) in 4/4 meter across 8 bars (32 beats).
  - Exact Clock Timing:
      Samples per beat       = (SAMPLE_RATE * 60) / 90.0 = 29,400 samples (0.6667s)
      Samples per 16th step  = (SAMPLE_RATE * 15) / 90.0 = 7,350 samples (0.1667s)
      Total Loop Samples     = 8 bars * 4 beats * 29,400 = 940,800 samples (21.3333s)
  - Harmonic Progression in B Minor 9 (2 bars per chord):
      Bars 1-2: Bm9     (B, D, F#, A, C#)   - Bedrock fundamental B1 (61.74 Hz)
      Bars 3-4: Gmaj7   (G, B, D, F#)       - Bedrock fundamental G1 (49.00 Hz)
      Bars 5-6: Em9     (E, G, B, D, F#)    - Bedrock fundamental E1 (41.20 Hz)
      Bars 7-8: F#7sus4 (F#, B, C#, E)      - Bedrock fundamental F#1 (46.25 Hz)
  - Procedural Voice Layer Architecture:
      1. Voice 1 (Bedrock Crystal Sub-Tone - Gain 0.38):
         Continuous pure sine fundamental tracking root pitches with gentle sinusoidal swell.
      2. Voice 2 (Prismatic Celesta Plucks - Gain 0.28):
         Odd-harmonic additive synthesis: S(t) = sin(wt) + 1/3*sin(3wt) + 1/5*sin(5wt) + 1/7*sin(7wt),
         normalized by 1.676 and shaped by an exponential decay envelope e^(-4.2 * t).
      3. Voice 3 (Glowing Mineral Ambient Pad - Gain 0.22):
         Sustained multi-tone chord pads enriched by a slow 0.3 Hz chorus LFO and boundary crossfades.
      4. Voice 4 (Cavernous Water Drop Pings - Gain 0.14):
         Rapid downward frequency chirp (2200 -> 1400 Hz over 18ms) followed by cavernous
         acoustic reflections at delta_t = 0.18s (45% amp) and delta_t = 0.36s (20% amp).
  - Dynamic Headroom & Master PCM Clamping:
      Normalized composite waveform scaled by 28,000.0 and strictly clamped to [-26500, 26500]
      before little-endian 16-bit integer packing into a standard 44-byte RIFF WAVE header.

Direct C++ Raylib Translation (raylib.h):
  struct CrystalCavernsBGM {
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
import struct as py_struct

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
BPM = 90.0

# 8 Bars at 90.0 BPM in 4/4 time = 32 beats = 21.3333 seconds
TOTAL_BARS = 8
BEATS_PER_BAR = 4
TOTAL_BEATS = TOTAL_BARS * BEATS_PER_BAR  # 32 beats
SAMPLES_PER_BEAT = int(SAMPLE_RATE * 60.0 / BPM)  # 29,400 samples
TOTAL_LOOP_SAMPLES = TOTAL_BEATS * SAMPLES_PER_BEAT  # 940,800 samples

# 16th-note step sequencer: 16 steps per bar * 8 bars = 128 steps
STEPS_PER_BAR = 16
TOTAL_STEPS = TOTAL_BARS * STEPS_PER_BAR  # 128 steps
SAMPLES_PER_STEP = TOTAL_LOOP_SAMPLES // TOTAL_STEPS  # 7,350 samples
STEP_DURATION_SEC = float(SAMPLES_PER_STEP) / float(SAMPLE_RATE)  # ~0.1667s

# Harmonic progression root frequencies (Hz) for 4 chord blocks (2 bars each)
CHORD_ROOT_FREQS = [61.74, 49.00, 41.20, 46.25]  # B1, G1, E1, F#1
CHORD_NAMES = ["Bm9", "Gmaj7", "Em9", "F#7sus4"]

# Pad chord tones for Voice 3 (Hz)
PAD_CHORDS = [
    [246.94, 369.99, 440.00, 554.37],  # Bm9     (B3, F#4, A4, C#5)
    [196.00, 246.94, 293.66, 369.99],  # Gmaj7   (G3, B3, D4, F#4)
    [164.81, 246.94, 293.66, 369.99],  # Em9     (E3, B3, D4, F#4)
    [185.00, 246.94, 277.18, 329.63],  # F#7sus4 (F#3, B3, C#4, E4)
]

# Prismatic Celesta scale palettes for Voice 2 (Hz)
CELESTA_PALETTES = [
    [493.88, 554.37, 587.33, 739.99, 880.00, 1108.73, 1174.66, 1479.98],  # Bm9
    [392.00, 493.88, 587.33, 739.99, 880.00, 987.77, 1174.66, 1479.98],   # Gmaj7
    [329.63, 392.00, 493.88, 587.33, 739.99, 880.00, 987.77, 1174.66],   # Em9
    [369.99, 493.88, 554.37, 659.25, 739.99, 987.77, 1108.73, 1318.51],  # F#7sus4
]

# 16-step arpeggio pattern mapped into the 8-note palette (cycles twice per 2-bar block)
CELESTA_PATTERN = [0, 2, 4, 5, 7, 5, 4, 2, 1, 3, 5, 6, 4, 3, 2, 1]

# Water drop trigger positions (in quarter beats)
WATER_DROP_BEATS = [3.5, 7.0, 11.5, 15.0, 19.5, 23.0, 27.5, 31.0]

# Memory pin dictionary to prevent garbage collection of in-memory WAV byte buffers
_ACTIVE_BUFFERS = {}


# ==============================================================================
# IN-MEMORY RIFF/WAV PACKER (C++ 44-Byte Header Equivalent)
# ==============================================================================
def pack_riff_wav_mono_16bit(sample_rate: int, raw_samples: list) -> bytes:
    """
    Packs signed 16-bit PCM integer samples into an in-memory canonical
    44-byte RIFF/WAVE container.
    """
    num_samples = len(raw_samples)
    clamped_samples = [max(-32767, min(32767, int(val))) for val in raw_samples]
    pcm_bytes = py_struct.pack(f"<{num_samples}h", *clamped_samples)

    riff_id = b"RIFF"
    wave_id = b"WAVE"
    fmt_id = b"fmt "
    fmt_size = 16
    audio_format = 1        # PCM
    num_channels = 1        # Mono
    byte_rate = sample_rate * num_channels * 2
    block_align = num_channels * 2
    bits_per_sample = 16
    data_id = b"data"
    data_size = len(pcm_bytes)
    total_chunk_size = 36 + data_size

    header = py_struct.pack(
        "<4sI4s4sIHHIIHH4sI",
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
def create_crystal_caverns_bgm() -> Music:
    """
    Algorithmically synthesizes an 8-bar looping subterranean gemstone soundtrack in RAM.
    Returns a streaming Raylib Music struct with looping enabled and memory pinned.
    """
    buffer = [0.0] * TOTAL_LOOP_SAMPLES
    samples_per_chord = TOTAL_LOOP_SAMPLES // 4  # 2 bars = 235,200 samples

    # --------------------------------------------------------------------------
    # Voice 1: Bedrock Crystal Sub-Tone (Pure sine fundamental, Gain 0.38)
    # --------------------------------------------------------------------------
    phase_v1 = 0.0
    for c_idx in range(4):
        freq = CHORD_ROOT_FREQS[c_idx]
        freq_inc = PI2 * freq / SAMPLE_RATE
        start_idx = c_idx * samples_per_chord
        end_idx = start_idx + samples_per_chord

        for i in range(start_idx, end_idx):
            phase_v1 += freq_inc
            # Sinusoidal swell breathing across each 2-bar chord segment
            swell = 0.85 + 0.15 * math.sin(PI2 * (i - start_idx) / samples_per_chord)
            buffer[i] += math.sin(phase_v1) * swell * 0.38

    # --------------------------------------------------------------------------
    # Voice 2: Prismatic Celesta Plucks (Odd-Harmonic Additive Synthesis, Gain 0.28)
    # --------------------------------------------------------------------------
    # Odd harmonics sum normalization: 1 + 1/3 + 1/5 + 1/7 = 1.676
    harm_norm = 1.0 / 1.676
    decay_samples = int(0.70 * SAMPLE_RATE)  # 0.7s decay envelope

    for step in range(0, TOTAL_STEPS, 2):  # Triggers every 8th note (every 2 16th steps)
        chord_idx = step // 32
        palette = CELESTA_PALETTES[chord_idx]
        pattern_idx = (step // 2) % len(CELESTA_PATTERN)
        note_freq = palette[CELESTA_PATTERN[pattern_idx]]

        start_sample = step * SAMPLES_PER_STEP
        end_sample = min(TOTAL_LOOP_SAMPLES, start_sample + decay_samples)
        omega = PI2 * note_freq / SAMPLE_RATE

        for i in range(start_sample, end_sample):
            t_rel = (i - start_sample) / SAMPLE_RATE
            # Exponential decay factor k = 4.2
            env_decay = math.exp(-4.2 * t_rel)
            phi = omega * (i - start_sample)
            # Additive odd-harmonic synthesis: 1, 3, 5, 7 multiples
            odd_harm = (
                math.sin(phi)
                + (1.0 / 3.0) * math.sin(3.0 * phi)
                + (1.0 / 5.0) * math.sin(5.0 * phi)
                + (1.0 / 7.0) * math.sin(7.0 * phi)
            )
            buffer[i] += (odd_harm * harm_norm) * env_decay * 0.28

    # --------------------------------------------------------------------------
    # Voice 3: Glowing Mineral Ambient Pad (Modal Chord Chorus, Gain 0.22)
    # --------------------------------------------------------------------------
    fade_len = int(0.06 * SAMPLE_RATE)  # 60ms smooth cross-fade between chord blocks
    for c_idx in range(4):
        start_idx = c_idx * samples_per_chord
        end_idx = start_idx + samples_per_chord
        chord_tones = PAD_CHORDS[c_idx]
        num_tones = len(chord_tones)
        tone_phases = [0.0] * num_tones
        tone_incs = [PI2 * f / SAMPLE_RATE for f in chord_tones]

        for i in range(start_idx, end_idx):
            t_sec = i / SAMPLE_RATE
            # Slow 0.3 Hz chorus amplitude modulation
            chorus = 0.85 + 0.15 * math.sin(PI2 * 0.3 * t_sec)

            # Boundary smooth fade to eliminate chord-boundary clicks
            rel_i = i - start_idx
            fade = 1.0
            if rel_i < fade_len:
                fade = rel_i / fade_len
            elif (end_idx - i) < fade_len:
                fade = (end_idx - i) / fade_len

            chord_sum = 0.0
            for k in range(num_tones):
                tone_phases[k] += tone_incs[k]
                chord_sum += math.sin(tone_phases[k])

            buffer[i] += (chord_sum / num_tones) * chorus * fade * 0.22

    # --------------------------------------------------------------------------
    # Voice 4: Cavernous Water Drop Pings (Chirp FM Echoes, Gain 0.14)
    # --------------------------------------------------------------------------
    chirp_dur = 0.018  # 18 ms
    chirp_samples = int(chirp_dur * SAMPLE_RATE)
    f_start = 2200.0
    f_end = 1400.0
    delta_f = f_end - f_start

    # Acoustic cavern reflection echoes at delta_t = 0.18s and 0.36s
    reflections = [(0.0, 1.0), (0.18, 0.45), (0.36, 0.20)]

    for beat_time in WATER_DROP_BEATS:
        base_sample = int(beat_time * SAMPLES_PER_BEAT)
        for dt_sec, refl_gain in reflections:
            echo_start = base_sample + int(dt_sec * SAMPLE_RATE)
            for s in range(chirp_samples):
                idx = echo_start + s
                if idx >= TOTAL_LOOP_SAMPLES:
                    continue
                t_rel = s / SAMPLE_RATE
                # Instantaneous phase for linear frequency descent
                phi_chirp = PI2 * (f_start * t_rel + (delta_f / (2.0 * chirp_dur)) * (t_rel * t_rel))
                window = 1.0 - (s / chirp_samples)
                chirp_val = math.sin(phi_chirp) * window * refl_gain * 0.14
                buffer[idx] += chirp_val

    # --------------------------------------------------------------------------
    # Master Mix & PCM Clamping (Strictly [-26500, 26500])
    # --------------------------------------------------------------------------
    pcm_samples = []
    pcm_multiplier = 28000.0
    for i in range(TOTAL_LOOP_SAMPLES):
        scaled_val = buffer[i] * pcm_multiplier
        # Clamp strictly to [-26500, 26500] short range
        clamped_val = int(max(-26500.0, min(26500.0, scaled_val)))
        pcm_samples.append(clamped_val)

    wav_bytes = pack_riff_wav_mono_16bit(SAMPLE_RATE, pcm_samples)
    music = load_music_stream_from_memory(".wav", wav_bytes, len(wav_bytes))
    music.looping = True

    # Pin byte buffer in memory dictionary to prevent GC access violation
    _ACTIVE_BUFFERS[id(music)] = wav_bytes
    return music


# Standardized alias mapping for dynamic discovery
create_bgm = create_crystal_caverns_bgm


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
    unload_music_stream(music)
    _ACTIVE_BUFFERS.pop(id(music), None)


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
            "BGM Workbench - Crystal Caverns (assets/audio/BGM/mystical/crystal_caverns.py)"
        )
        set_target_fps(60)
        init_audio_device()

        self.music = create_crystal_caverns_bgm()
        self.volume = 0.70
        self.pitch = 1.0
        self.is_playing = False
        self.gamepad_id = 0

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
        # 1. CRITICAL: Feed audio stream buffer every frame
        if self.is_playing:
            update_bgm(self.music)

        # Gamepad connection check
        gp_connected = is_gamepad_available(self.gamepad_id)

        # Space, M, or Gamepad A/Start toggles Play/Pause
        kb_toggle = is_key_pressed(KEY_SPACE) or is_key_pressed(KEY_M)
        gp_toggle = gp_connected and (
            is_gamepad_button_pressed(self.gamepad_id, GAMEPAD_BUTTON_RIGHT_FACE_DOWN)
            or is_gamepad_button_pressed(self.gamepad_id, GAMEPAD_BUTTON_MIDDLE_RIGHT)
        )
        if kb_toggle or gp_toggle:
            self.toggle_playback()

        # Up/Down arrows or Gamepad D-pad Up/Down adjusts volume
        vol_up = is_key_pressed(KEY_UP) or (gp_connected and is_gamepad_button_pressed(self.gamepad_id, GAMEPAD_BUTTON_LEFT_FACE_UP))
        vol_dn = is_key_pressed(KEY_DOWN) or (gp_connected and is_gamepad_button_pressed(self.gamepad_id, GAMEPAD_BUTTON_LEFT_FACE_DOWN))
        if vol_up:
            self.volume = min(1.0, self.volume + 0.05)
            set_music_volume(self.music, self.volume)
        elif vol_dn:
            self.volume = max(0.0, self.volume - 0.05)
            set_music_volume(self.music, self.volume)

        # Left/Right arrows or Gamepad D-pad Left/Right adjusts pitch/tempo
        pit_up = is_key_pressed(KEY_RIGHT) or (gp_connected and is_gamepad_button_pressed(self.gamepad_id, GAMEPAD_BUTTON_LEFT_FACE_RIGHT))
        pit_dn = is_key_pressed(KEY_LEFT) or (gp_connected and is_gamepad_button_pressed(self.gamepad_id, GAMEPAD_BUTTON_LEFT_FACE_LEFT))
        if pit_up:
            self.pitch = min(2.0, self.pitch + 0.05)
            set_music_pitch(self.music, self.pitch)
        elif pit_dn:
            self.pitch = max(0.5, self.pitch - 0.05)
            set_music_pitch(self.music, self.pitch)

    def draw(self):
        begin_drawing()
        clear_background(Color(10, 14, 24, 255))

        # Title Header (keeps safe top region x=450..980, y=14..48 clear for dropdowns)
        draw_text("PROCEDURAL BGM AUDITION WORKBENCH", 24, 20, 20, RAYWHITE)
        draw_text("Asset: assets/audio/BGM/mystical/crystal_caverns.py | 90 BPM B-Minor 9 Subterranean", 24, 50, 13, SKYBLUE)

        # Control Info Card
        panel_y = 90
        draw_rectangle(24, panel_y, 400, 280, Color(18, 24, 40, 255))
        draw_rectangle_lines(24, panel_y, 400, 280, Color(45, 65, 105, 255))
        draw_text("BGM CONTROLS (DUAL INPUT)", 40, panel_y + 14, 15, YELLOW)
        draw_text("- [Space] / [M] / Gamepad (A/Start): Play / Pause", 40, panel_y + 44, 13, RAYWHITE)
        draw_text("- [Up] / [Down] / Gamepad D-pad UD : Volume (+/- 5%)", 40, panel_y + 70, 13, RAYWHITE)
        draw_text("- [Left] / [Right] / Gamepad D-pad LR: Pitch (+/- 5%)", 40, panel_y + 96, 13, RAYWHITE)
        draw_text(
            f"Playback State : {'PLAYING (Looping)' if self.is_playing else 'PAUSED'}",
            40, panel_y + 130, 13, GREEN if self.is_playing else RED
        )
        draw_text(f"Volume         : {int(self.volume * 100)}%", 40, panel_y + 154, 13, SKYBLUE)
        draw_text(f"Tempo / Pitch  : {self.pitch:.2f}x (Effective {BPM * self.pitch:.1f} BPM)", 40, panel_y + 178, 13, SKYBLUE)
        draw_text(f"Loop Length    : {TOTAL_LOOP_SAMPLES:,} samples (21.33s)", 40, panel_y + 202, 13, LIGHTGRAY)
        draw_text(f"Peak PCM Clamp : [-26500, +26500] 16-bit", 40, panel_y + 226, 13, GOLD)
        draw_text(f"Memory Pinned  : {len(_ACTIVE_BUFFERS)} active stream buffer(s)", 40, panel_y + 250, 13, Color(160, 220, 160, 255))

        # Real-time Stream Output Visualizer
        vis_x = 450
        vis_y = 90
        vis_w = 800
        vis_h = 600
        draw_rectangle(vis_x, vis_y, vis_w, vis_h, Color(14, 20, 32, 255))
        draw_rectangle_lines(vis_x, vis_y, vis_w, vis_h, Color(45, 65, 105, 255))
        draw_text("STREAM BUFFER & MULTI-VOICE RHYTHM MONITOR", vis_x + 20, vis_y + 16, 15, ORANGE)

        # Loop Progress and Step Sequencer Tracking
        time_played = get_music_time_played(self.music)
        time_total = get_music_time_length(self.music)
        loop_progress = (time_played / time_total) if time_total > 0.0 else 0.0
        current_step = int(loop_progress * TOTAL_STEPS) % TOTAL_STEPS
        current_beat = int(loop_progress * TOTAL_BEATS) % TOTAL_BEATS
        current_chord_idx = (current_step // 32) % 4

        # 32-Beat Sequencer Activity Grid
        grid_y = vis_y + 55
        beat_w = (vis_w - 40) // 32
        for b in range(32):
            bx = vis_x + 20 + (b * beat_w)
            is_cur_beat = (b == current_beat) and self.is_playing
            chord_zone = b // 8
            # Color chord blocks distinctly
            block_colors = [
                Color(30, 45, 75, 255),
                Color(40, 60, 50, 255),
                Color(55, 40, 65, 255),
                Color(65, 45, 35, 255),
            ]
            box_col = SKYBLUE if is_cur_beat else block_colors[chord_zone]
            draw_rectangle(bx, grid_y, beat_w - 2, 32, box_col)

        draw_text(
            f"Beat: {current_beat + 1:02d} / 32 | Step: {current_step + 1:03d} / 128 | Time: {time_played:.2f}s / {time_total:.2f}s",
            vis_x + 20, grid_y + 42, 13, LIGHTGRAY
        )

        # Loop Progress Bar
        bar_y = vis_y + 140
        draw_rectangle(vis_x + 20, bar_y, vis_w - 40, 16, Color(24, 30, 45, 255))
        fill_w = int(loop_progress * (vis_w - 40))
        draw_rectangle(vis_x + 20, bar_y, fill_w, 16, Color(80, 180, 240, 255))
        draw_rectangle_lines(vis_x + 20, bar_y, vis_w - 40, 16, Color(60, 90, 130, 255))

        # Current Harmonic Section Indicator
        sect_y = vis_y + 175
        cur_chord_name = CHORD_NAMES[current_chord_idx]
        cur_root = CHORD_ROOT_FREQS[current_chord_idx]
        draw_text(
            f"Current Harmonic Block : Bars {current_chord_idx * 2 + 1}-{current_chord_idx * 2 + 2} -> {cur_chord_name} (Root {cur_root:.2f} Hz)",
            vis_x + 20, sect_y, 14, YELLOW
        )

        # 4 Procedural Voice Layer Meters
        layer_y = vis_y + 215
        box_spacing = 80

        # Voice 1: Bedrock Sub-Tone
        draw_rectangle(vis_x + 20, layer_y, vis_w - 40, 70, Color(20, 28, 46, 255))
        draw_rectangle_lines(vis_x + 20, layer_y, vis_w - 40, 70, Color(40, 60, 95, 255))
        draw_text("Voice 1: Bedrock Crystal Sub-Tone (Gain 0.38)", vis_x + 35, layer_y + 10, 13, Color(120, 200, 255, 255))
        draw_text(f"Pure sine sub-fundamental: {cur_root:.2f} Hz | Sinusoidal breathing swell", vis_x + 35, layer_y + 35, 12, RAYWHITE)

        # Voice 2: Prismatic Celesta Plucks
        v2_y = layer_y + box_spacing
        draw_rectangle(vis_x + 20, v2_y, vis_w - 40, 70, Color(20, 28, 46, 255))
        draw_rectangle_lines(vis_x + 20, v2_y, vis_w - 40, 70, Color(40, 60, 95, 255))
        cel_idx = (current_step // 2) % len(CELESTA_PATTERN)
        cel_freq = CELESTA_PALETTES[current_chord_idx][CELESTA_PATTERN[cel_idx]]
        draw_text("Voice 2: Prismatic Celesta Plucks (Gain 0.28)", vis_x + 35, v2_y + 10, 13, Color(255, 215, 100, 255))
        draw_text(f"Odd-harmonic additive (1, 3, 5, 7x): {cel_freq:.2f} Hz | Decay k=4.2", vis_x + 35, v2_y + 35, 12, RAYWHITE)

        # Voice 3: Glowing Mineral Ambient Pad
        v3_y = v2_y + box_spacing
        draw_rectangle(vis_x + 20, v3_y, vis_w - 40, 70, Color(20, 28, 46, 255))
        draw_rectangle_lines(vis_x + 20, v3_y, vis_w - 40, 70, Color(40, 60, 95, 255))
        pad_tones_str = ", ".join(f"{f:.1f}Hz" for f in PAD_CHORDS[current_chord_idx])
        draw_text("Voice 3: Glowing Mineral Ambient Pad (Gain 0.22)", vis_x + 35, v3_y + 10, 13, Color(160, 230, 160, 255))
        draw_text(f"Modal chord tones: [{pad_tones_str}] | 0.3 Hz chorus LFO", vis_x + 35, v3_y + 35, 12, RAYWHITE)

        # Voice 4: Cavernous Water Drop Pings
        v4_y = v3_y + box_spacing
        draw_rectangle(vis_x + 20, v4_y, vis_w - 40, 70, Color(20, 28, 46, 255))
        draw_rectangle_lines(vis_x + 20, v4_y, vis_w - 40, 70, Color(40, 60, 95, 255))
        # Active water drop echo check
        water_active = any(abs(current_beat - wb) < 0.6 for wb in WATER_DROP_BEATS)
        water_status = "ECHO ACTIVE (Reflections at 0.18s, 0.36s)" if water_active else "Silent (Awaiting Next Drop)"
        water_color = Color(100, 255, 255, 255) if water_active else LIGHTGRAY
        draw_text("Voice 4: Cavernous Water Drop Pings (Gain 0.14)", vis_x + 35, v4_y + 10, 13, Color(100, 240, 255, 255))
        draw_text(f"2200 -> 1400 Hz (18ms) chirp | Status: {water_status}", vis_x + 35, v4_y + 35, 12, water_color)

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
