# -*- coding: utf-8 -*-
"""
Procedural Background Music (BGM) Synthesizer - The Alchemist's Flask
=====================================================================
Type             : Procedural Audio BGM (Music Stream)
Target File      : assets/audio/BGM/curious/alchemists_flask.py
Waveforms Used   : Plucked upright bass, FM liquid bubble lead (24 Hz FM), glass harmonica chord pad, dropper drip pings and effervescent fizz noise
Category         : Curious BGM Soundtracks / Chemical Laboratory & Alchemy Themes

Problem Solved:
  Eliminates static, multi-megabyte audio soundtrack assets by algorithmically
  synthesizing a whimsical, potion-brewing 8-bar G-Mixolydian loop in RAM.
  Streams dynamically through Raylib's Music struct with zero disk I/O,
  strict CFFI memory buffer pinning, and seamless phase continuity.

Musical Theory & Mathematical Rationale:
  - Tempo: 98.0 Beats Per Minute (BPM) in 4/4 meter across 8 bars (32 beats).
  - Exact Clock Timing:
      Samples per beat       = (SAMPLE_RATE * 60) / 98.0 = 27,000 samples (0.6122s)
      Samples per 16th step  = (SAMPLE_RATE * 15) / 98.0 = 6,750 samples (0.1531s)
      Total Loop Samples     = 8 bars * 4 beats * 27,000 = 864,000 samples (19.5918s)
  - Harmonic Progression in G Mixolydian Mode (2 bars per chord block):
      Bars 1-2: G Mixolydian Tonic (G - B - D - F)  - Root G2 (98.00 Hz)
      Bars 3-4: F Major (F - A - C - E)            - Subtonic bVII Root F2 (87.31 Hz)
      Bars 5-6: C Major (C - E - G - Bb)           - Subdominant IV Root C2 (65.41 Hz)
      Bars 7-8: G Mixolydian Tonic (G - B - D - F)  - Return to Tonic G2 (98.00 Hz)
  - Procedural Voice Layer Architecture:
      1. Voice 1 (Plucked Upright Bass - Gain 0.38):
         Woody transient acoustic pluck with rich harmonics (1x, 2x, 3x, 4x), subtle initial
         pitch sweep (+4 Hz attack settling over 20ms), playing quirky eccentric walking intervals.
      2. Voice 2 (Liquid Bubble FM Lead - Gain 0.28):
         Liquid pitch-bending bubble lead utilizing sine wave frequency modulation (FM 24 Hz).
         Frequency sweeps upward (Minnaert bubble resonance) with 24 Hz vibrato modulation index.
      3. Voice 3 (Glass Harmonica Chord Pad - Gain 0.20):
         Glass harmonica chords with fragile high harmonic partials (1x, 2x, 3x, 4.16x),
         slow wet-friction tremolo (1.8 Hz) and smooth 80ms boundary crossfades.
      4. Voice 4 (Dropper Drip Pings & Effervescent Noise Risers - Gain 0.16):
         Dropper drip pings with rapid downward chirp (2900 -> 1550 Hz over 15ms) and cavernous
         pipette reflection, coupled with high-pass filtered effervescent bubbling fizz risers.
  - Dynamic Headroom & Master PCM Clamping:
      Composite waveform scaled by 28,000.0 and strictly clamped to [-27000, 27000]
      before little-endian 16-bit integer packing into a standard 44-byte RIFF WAVE header.

Direct C++ Raylib Translation (raylib.h):
  struct AlchemistsFlaskBGM {
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
BPM = 98.0

# 8 Bars at 98.0 BPM in 4/4 time = 32 beats = 19.5918 seconds
TOTAL_BARS = 8
BEATS_PER_BAR = 4
TOTAL_BEATS = TOTAL_BARS * BEATS_PER_BAR  # 32 beats
SAMPLES_PER_BEAT = int(SAMPLE_RATE * 60.0 / BPM)  # 27,000 samples
TOTAL_LOOP_SAMPLES = TOTAL_BEATS * SAMPLES_PER_BEAT  # 864,000 samples

# 16th-note step sequencer: 16 steps per bar * 8 bars = 128 steps
STEPS_PER_BAR = 16
TOTAL_STEPS = TOTAL_BARS * STEPS_PER_BAR  # 128 steps
SAMPLES_PER_STEP = TOTAL_LOOP_SAMPLES // TOTAL_STEPS  # 6,750 samples
STEP_DURATION_SEC = float(SAMPLES_PER_STEP) / float(SAMPLE_RATE)  # ~0.1531s

# Harmonic progression root frequencies (Hz) for 4 chord blocks (2 bars each)
CHORD_ROOT_FREQS = [98.00, 87.31, 65.41, 98.00]  # G2, F2, C2, G2
CHORD_NAMES = ["G Mixolydian (G)", "F Major (bVII)", "C Major (IV)", "G Mixolydian (G)"]

# Glass Harmonica chord tones for Voice 3 (Hz)
PAD_CHORDS = [
    [196.00, 246.94, 293.66, 349.23],  # G Mixolydian (G3, B3, D4, F4)
    [174.61, 220.00, 261.63, 329.63],  # F Major      (F3, A3, C4, E4)
    [130.81, 196.00, 261.63, 329.63],  # C Major      (C3, G3, C4, E4)
    [196.00, 261.63, 293.66, 349.23],  # Gsus4 -> G   (G3, C4, D4, F4)
]

# Quirky eccentric bass line: (beat_start, frequency_hz, duration_beats)
BASS_SCORE = [
    # Bars 1-2: G Mixolydian (G)
    (0.0, 98.00, 0.90),
    (1.5, 146.83, 0.45),
    (2.0, 98.00, 0.80),
    (3.0, 87.31, 0.80),
    (4.0, 98.00, 0.90),
    (5.0, 123.47, 0.80),
    (6.0, 146.83, 0.80),
    (7.0, 196.00, 0.80),
    # Bars 3-4: F Major (F)
    (8.0, 87.31, 0.90),
    (9.5, 130.81, 0.45),
    (10.0, 87.31, 0.80),
    (11.0, 98.00, 0.80),
    (12.0, 87.31, 0.90),
    (13.0, 110.00, 0.80),
    (14.0, 130.81, 0.80),
    (15.0, 174.61, 0.80),
    # Bars 5-6: C Major (C)
    (16.0, 65.41, 0.90),
    (17.5, 98.00, 0.45),
    (18.0, 65.41, 0.80),
    (19.0, 82.41, 0.80),
    (20.0, 98.00, 0.90),
    (21.0, 116.54, 0.80),
    (22.0, 130.81, 0.80),
    (23.0, 98.00, 0.80),
    # Bars 7-8: G Mixolydian (G)
    (24.0, 98.00, 0.90),
    (25.5, 146.83, 0.45),
    (26.0, 87.31, 0.80),
    (27.0, 73.42, 0.80),
    (28.0, 98.00, 0.90),
    (29.0, 123.47, 0.80),
    (30.0, 146.83, 0.80),
    (31.0, 98.00, 0.80),
]

# Liquid bubble melody notes: (beat_start, base_frequency_hz)
BUBBLE_LEAD_NOTES = [
    # Bar 1 (G)
    (0.5, 392.00),
    (1.25, 493.88),
    (2.0, 587.33),
    (3.0, 698.46),
    # Bar 2 (G)
    (4.5, 659.25),
    (5.25, 587.33),
    (6.0, 493.88),
    (7.0, 440.00),
    # Bar 3 (F)
    (8.5, 349.23),
    (9.25, 440.00),
    (10.0, 523.25),
    (11.0, 698.46),
    # Bar 4 (F)
    (12.5, 659.25),
    (13.25, 523.25),
    (14.0, 440.00),
    (15.0, 523.25),
    # Bar 5 (C)
    (16.5, 329.63),
    (17.25, 392.00),
    (18.0, 523.25),
    (19.0, 659.25),
    # Bar 6 (C)
    (20.5, 587.33),
    (21.25, 523.25),
    (22.0, 392.00),
    (23.0, 493.88),
    # Bar 7 (G)
    (24.5, 392.00),
    (25.25, 587.33),
    (26.0, 698.46),
    (27.0, 783.99),
    # Bar 8 (G)
    (28.5, 698.46),
    (29.25, 587.33),
    (30.0, 493.88),
    (31.0, 392.00),
]

# Dropper drip ping trigger positions (in quarter beats)
DRIP_PING_BEATS = [1.0, 3.5, 5.0, 7.5, 9.0, 11.5, 13.0, 15.5, 17.0, 19.5, 21.0, 23.5, 25.0, 27.5, 29.0, 31.5]

# Effervescent fizz riser start positions (in quarter beats)
FIZZ_RISER_BEATS = [2.0, 6.0, 10.0, 14.0, 18.0, 22.0, 26.0, 30.0]

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
def create_alchemists_flask_bgm() -> Music:
    """
    Algorithmically synthesizes an 8-bar looping whimsical potion laboratory soundtrack in RAM.
    Returns a streaming Raylib Music struct with looping enabled and memory pinned.
    """
    buffer = [0.0] * TOTAL_LOOP_SAMPLES
    samples_per_chord = TOTAL_LOOP_SAMPLES // 4  # 2 bars = 216,000 samples

    # --------------------------------------------------------------------------
    # Voice 1: Plucked Upright Bass (Quirky Eccentric Intervals, Gain 0.38)
    # --------------------------------------------------------------------------
    for beat_start, freq, dur_beats in BASS_SCORE:
        start_sample = int(beat_start * SAMPLES_PER_BEAT)
        note_samples = int(dur_beats * SAMPLES_PER_BEAT)
        end_sample = min(TOTAL_LOOP_SAMPLES, start_sample + note_samples)

        phase_bass = 0.0
        for s in range(start_sample, end_sample):
            t_rel = float(s - start_sample) / float(SAMPLE_RATE)
            # Attack pitch sag settling over 20ms (+4 Hz down to target freq)
            f_inst = freq + 4.0 * math.exp(-50.0 * t_rel)
            phase_bass += PI2 * f_inst / SAMPLE_RATE

            # Rich wooden acoustic pluck harmonics (1x, 2x, 3x, 4x)
            pluck_wave = (
                math.sin(phase_bass)
                + 0.35 * math.sin(2.0 * phase_bass)
                + 0.15 * math.sin(3.0 * phase_bass)
                + 0.05 * math.sin(4.0 * phase_bass)
            ) / 1.55

            # Percussive fingerboard snap / click
            click = 0.22 * math.sin(PI2 * 320.0 * t_rel) * math.exp(-110.0 * t_rel)

            # Pluck amplitude envelope (fast 3ms attack, natural exponential decay)
            if t_rel < 0.003:
                env = t_rel / 0.003
            else:
                env = math.exp(-3.8 * t_rel)

            buffer[s] += (pluck_wave + click) * env * 0.38

    # --------------------------------------------------------------------------
    # Voice 2: Liquid Bubble FM Lead (Sine Wave FM 24 Hz, Gain 0.28)
    # --------------------------------------------------------------------------
    bubble_dur_sec = 0.28  # 280ms bubble note duration
    bubble_samples = int(bubble_dur_sec * SAMPLE_RATE)
    fm_mod_freq = 24.0  # 24 Hz FM modulation frequency

    for beat_start, base_freq in BUBBLE_LEAD_NOTES:
        start_sample = int(beat_start * SAMPLES_PER_BEAT)
        end_sample = min(TOTAL_LOOP_SAMPLES, start_sample + bubble_samples)

        phase_lead = 0.0
        for s in range(start_sample, end_sample):
            t_rel = float(s - start_sample) / float(SAMPLE_RATE)

            # Upward bubble chirp resonance (Minnaert bubble rise: +28% pitch sweep)
            f_sweep = base_freq * (1.0 + 0.28 * (1.0 - math.exp(-22.0 * t_rel)))

            # FM 24 Hz sine modulation: vibrato depth starts at 36 Hz and decays
            fm_depth = 36.0 * math.exp(-10.0 * t_rel)
            f_mod = fm_depth * math.sin(PI2 * fm_mod_freq * t_rel)
            f_inst = f_sweep + f_mod

            phase_lead += PI2 * f_inst / SAMPLE_RATE

            # Fast 4ms bubble attack and soft liquid release
            if t_rel < 0.004:
                env = t_rel / 0.004
            else:
                env = math.exp(-7.2 * t_rel)

            buffer[s] += math.sin(phase_lead) * env * 0.28

    # --------------------------------------------------------------------------
    # Voice 3: Glass Harmonica Chord Pad (Fragile Harmonic Partials, Gain 0.20)
    # --------------------------------------------------------------------------
    fade_len = int(0.08 * SAMPLE_RATE)  # 80ms smooth cross-fade between chord blocks
    harm_weights = [1.0, 0.40, 0.18, 0.08]
    harm_multipliers = [1.0, 2.0, 3.0, 4.16]
    harm_total_norm = 1.0 / sum(harm_weights)  # 1.0 / 1.66

    for c_idx in range(4):
        start_idx = c_idx * samples_per_chord
        end_idx = start_idx + samples_per_chord
        chord_tones = PAD_CHORDS[c_idx]
        num_tones = len(chord_tones)

        # Track independent phases for each harmonic partial of each chord tone
        tone_phases = [[0.0 for _ in range(4)] for _ in range(num_tones)]

        for i in range(start_idx, end_idx):
            t_sec = float(i) / float(SAMPLE_RATE)

            # Wet friction 1.8 Hz subtle tremolo
            tremolo = 0.88 + 0.12 * math.sin(PI2 * 1.8 * t_sec)

            # Boundary smooth fade to prevent chord transition clicks
            rel_i = i - start_idx
            fade = 1.0
            if rel_i < fade_len:
                fade = float(rel_i) / float(fade_len)
            elif (end_idx - i) < fade_len:
                fade = float(end_idx - i) / float(fade_len)

            chord_sum = 0.0
            for k in range(num_tones):
                tone_f0 = chord_tones[k]
                tone_val = 0.0
                for h in range(4):
                    partial_f = tone_f0 * harm_multipliers[h]
                    tone_phases[k][h] += PI2 * partial_f / SAMPLE_RATE
                    tone_val += math.sin(tone_phases[k][h]) * harm_weights[h]
                chord_sum += tone_val * harm_total_norm

            buffer[i] += (chord_sum / float(num_tones)) * tremolo * fade * 0.20

    # --------------------------------------------------------------------------
    # Voice 4: Dropper Drip Pings & Effervescent Noise Risers (Gain 0.16)
    # --------------------------------------------------------------------------
    # 4A. Dropper Drip Pings (Downward rapid chirp + pipette echo)
    drip_chirp_dur = 0.016  # 16 ms
    drip_samples = int(drip_chirp_dur * SAMPLE_RATE)
    f_drip_start = 2900.0
    f_drip_end = 1550.0
    drip_delta_f = f_drip_end - f_drip_start

    # Acoustic reflection in glass container at delta_t = 0.07s
    drip_echoes = [(0.0, 1.0), (0.07, 0.35)]

    for beat_time in DRIP_PING_BEATS:
        base_sample = int(beat_time * SAMPLES_PER_BEAT)
        for dt_sec, echo_gain in drip_echoes:
            echo_start = base_sample + int(dt_sec * SAMPLE_RATE)
            for s in range(drip_samples):
                idx = echo_start + s
                if idx >= TOTAL_LOOP_SAMPLES:
                    continue
                t_rel = float(s) / float(SAMPLE_RATE)
                # Instantaneous phase for downward linear chirp
                phi_chirp = PI2 * (f_drip_start * t_rel + (drip_delta_f / (2.0 * drip_chirp_dur)) * (t_rel * t_rel))
                window = 1.0 - (float(s) / float(drip_samples))
                buffer[idx] += math.sin(phi_chirp) * window * echo_gain * 0.10

    # 4B. Effervescent Fizz Risers (High-pass filtered noise swell)
    fizz_dur_sec = 1.10  # 1.10s bubbling swell
    fizz_samples = int(fizz_dur_sec * SAMPLE_RATE)

    # Deterministic Linear Congruential Generator (LCG) PRNG for reproducible C++ noise
    lcg_state = 1234567
    prev_rand = 0.0

    for beat_time in FIZZ_RISER_BEATS:
        base_sample = int(beat_time * SAMPLES_PER_BEAT)
        for s in range(fizz_samples):
            idx = base_sample + s
            if idx >= TOTAL_LOOP_SAMPLES:
                continue

            t_rel = float(s) / float(SAMPLE_RATE)
            norm_t = float(s) / float(fizz_samples)

            # LCG Step
            lcg_state = (lcg_state * 1103515245 + 12345) & 0x7FFFFFFF
            cur_rand = (float(lcg_state) / 1073741824.0) - 1.0  # Range -1.0 to +1.0

            # First-order high-pass difference filter for fizzy sizzle
            hp_noise = cur_rand - 0.85 * prev_rand
            prev_rand = cur_rand

            # 32 Hz bubble popping burst modulation
            burst_mod = 0.70 + 0.30 * math.sin(PI2 * 32.0 * t_rel)

            # Cubic swell envelope that peaks and dissolves
            env_fizz = (norm_t * norm_t) * (1.0 - norm_t) * 3.8

            buffer[idx] += hp_noise * burst_mod * env_fizz * 0.08

    # --------------------------------------------------------------------------
    # Master Mix & PCM Clamping (Strictly [-27000, 27000])
    # --------------------------------------------------------------------------
    pcm_samples = []
    pcm_multiplier = 28000.0
    for i in range(TOTAL_LOOP_SAMPLES):
        scaled_val = buffer[i] * pcm_multiplier
        # Clamp strictly to [-27000, 27000] short range
        clamped_val = int(max(-27000.0, min(27000.0, scaled_val)))
        pcm_samples.append(clamped_val)

    wav_bytes = pack_riff_wav_mono_16bit(SAMPLE_RATE, pcm_samples)
    music = load_music_stream_from_memory(".wav", wav_bytes, len(wav_bytes))
    music.looping = True

    # Pin byte buffer in memory dictionary to prevent GC access violation
    _ACTIVE_BUFFERS[id(music)] = wav_bytes
    return music


# Standardized aliases for dynamic discovery
create_bgm = create_alchemists_flask_bgm
generate_alchemists_flask_track = create_alchemists_flask_bgm


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
            "BGM Workbench - The Alchemist's Flask (assets/audio/BGM/curious/alchemists_flask.py)"
        )
        set_target_fps(60)
        init_audio_device()

        self.music = create_alchemists_flask_bgm()
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

    def reset_playback(self):
        stop_bgm(self.music)
        play_bgm(self.music, self.volume, self.pitch, loop=True)
        self.is_playing = True

    def update(self):
        # 1. CRITICAL: Feed audio stream buffer every frame
        if self.is_playing:
            update_bgm(self.music)

        # Gamepad connection check
        gp_connected = is_gamepad_available(self.gamepad_id)

        # Space, M, or Gamepad A/Right face button toggles Play/Pause
        kb_toggle = is_key_pressed(KEY_SPACE) or is_key_pressed(KEY_M)
        gp_toggle = gp_connected and (
            is_gamepad_button_pressed(self.gamepad_id, GAMEPAD_BUTTON_RIGHT_FACE_DOWN)
            or is_gamepad_button_pressed(self.gamepad_id, GAMEPAD_BUTTON_MIDDLE_RIGHT)
        )
        if kb_toggle or gp_toggle:
            self.toggle_playback()

        # [R] or Gamepad Start resets track to start
        kb_reset = is_key_pressed(KEY_R)
        gp_reset = gp_connected and is_gamepad_button_pressed(self.gamepad_id, GAMEPAD_BUTTON_MIDDLE_RIGHT)
        if kb_reset:
            self.reset_playback()

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
        clear_background(Color(12, 18, 22, 255))

        # Title Header (keeps safe top region x=450..980, y=14..48 clear for dropdowns)
        draw_text("PROCEDURAL BGM AUDITION WORKBENCH", 24, 20, 20, RAYWHITE)
        draw_text("Asset: assets/audio/BGM/curious/alchemists_flask.py | 98 BPM G Mixolydian Bubbling Laboratory", 24, 50, 13, SKYBLUE)

        # Control Info Card
        panel_y = 90
        draw_rectangle(24, panel_y, 400, 300, Color(18, 26, 32, 255))
        draw_rectangle_lines(24, panel_y, 400, 300, Color(45, 75, 80, 255))
        draw_text("BGM CONTROLS (DUAL INPUT)", 40, panel_y + 14, 15, YELLOW)
        draw_text("- [Space] / [M] / Gamepad (A/Start): Play / Pause", 40, panel_y + 44, 13, RAYWHITE)
        draw_text("- [R] / Gamepad Start              : Reset Track", 40, panel_y + 70, 13, RAYWHITE)
        draw_text("- [Up] / [Down] / Gamepad D-pad UD : Volume (+/- 5%)", 40, panel_y + 96, 13, RAYWHITE)
        draw_text("- [Left] / [Right] / Gamepad D-pad LR: Pitch (+/- 5%)", 40, panel_y + 122, 13, RAYWHITE)
        draw_text(
            f"Playback State : {'PLAYING (Looping)' if self.is_playing else 'PAUSED'}",
            40, panel_y + 154, 13, GREEN if self.is_playing else RED
        )
        draw_text(f"Volume         : {int(self.volume * 100)}%", 40, panel_y + 178, 13, SKYBLUE)
        draw_text(f"Tempo / Pitch  : {self.pitch:.2f}x (Effective {BPM * self.pitch:.1f} BPM)", 40, panel_y + 202, 13, SKYBLUE)
        draw_text(f"Loop Length    : {TOTAL_LOOP_SAMPLES:,} samples (19.59s)", 40, panel_y + 226, 13, LIGHTGRAY)
        draw_text(f"Peak PCM Clamp : [-27000, +27000] 16-bit", 40, panel_y + 250, 13, GOLD)
        draw_text(f"Memory Pinned  : {len(_ACTIVE_BUFFERS)} active stream buffer(s)", 40, panel_y + 274, 13, Color(160, 230, 180, 255))

        # Real-time Stream Output Visualizer
        vis_x = 450
        vis_y = 90
        vis_w = 800
        vis_h = 600
        draw_rectangle(vis_x, vis_y, vis_w, vis_h, Color(16, 24, 28, 255))
        draw_rectangle_lines(vis_x, vis_y, vis_w, vis_h, Color(45, 75, 80, 255))
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
                Color(30, 55, 60, 255),  # G Mixolydian (Emerald teal)
                Color(55, 45, 30, 255),  # F Major (Amber copper)
                Color(30, 45, 65, 255),  # C Major (Sapphire blue)
                Color(30, 55, 60, 255),  # G Mixolydian (Emerald teal)
            ]
            box_col = SKYBLUE if is_cur_beat else block_colors[chord_zone]
            draw_rectangle(bx, grid_y, beat_w - 2, 32, box_col)

        draw_text(
            f"Beat: {current_beat + 1:02d} / 32 | Step: {current_step + 1:03d} / 128 | Time: {time_played:.2f}s / {time_total:.2f}s",
            vis_x + 20, grid_y + 42, 13, LIGHTGRAY
        )

        # Loop Progress Bar
        bar_y = vis_y + 140
        draw_rectangle(vis_x + 20, bar_y, vis_w - 40, 16, Color(24, 34, 40, 255))
        fill_w = int(loop_progress * (vis_w - 40))
        draw_rectangle(vis_x + 20, bar_y, fill_w, 16, Color(60, 200, 180, 255))
        draw_rectangle_lines(vis_x + 20, bar_y, vis_w - 40, 16, Color(50, 90, 85, 255))

        # Current Harmonic Section Indicator
        sect_y = vis_y + 175
        cur_chord_name = CHORD_NAMES[current_chord_idx]
        cur_root = CHORD_ROOT_FREQS[current_chord_idx]
        draw_text(
            f"Current Harmonic Block : Bars {current_chord_idx * 2 + 1}-{current_chord_idx * 2 + 2} -> {cur_chord_name} (Fundamental {cur_root:.2f} Hz)",
            vis_x + 20, sect_y, 14, YELLOW
        )

        # 4 Procedural Voice Layer Meters
        layer_y = vis_y + 215
        box_spacing = 80

        # Voice 1: Plucked Upright Bass
        draw_rectangle(vis_x + 20, layer_y, vis_w - 40, 70, Color(22, 32, 38, 255))
        draw_rectangle_lines(vis_x + 20, layer_y, vis_w - 40, 70, Color(45, 75, 80, 255))
        draw_text("Voice 1: Plucked Upright Bass (Gain 0.38)", vis_x + 35, layer_y + 10, 13, Color(140, 220, 200, 255))
        draw_text(f"Woody pluck transient | Eccentric walking interval: {cur_root:.2f} Hz fundamental", vis_x + 35, layer_y + 35, 12, RAYWHITE)

        # Voice 2: Liquid Bubble FM Lead
        v2_y = layer_y + box_spacing
        draw_rectangle(vis_x + 20, v2_y, vis_w - 40, 70, Color(22, 32, 38, 255))
        draw_rectangle_lines(vis_x + 20, v2_y, vis_w - 40, 70, Color(45, 75, 80, 255))
        lead_active = any(abs(current_beat - bn[0]) < 0.4 for bn in BUBBLE_LEAD_NOTES)
        lead_col = Color(255, 220, 110, 255) if lead_active else LIGHTGRAY
        draw_text("Voice 2: Liquid Bubble FM Lead (Gain 0.28)", vis_x + 35, v2_y + 10, 13, Color(255, 215, 90, 255))
        draw_text("Sine FM (24 Hz vibrato) | Minnaert bubble upward pitch sweeps", vis_x + 35, v2_y + 35, 12, lead_col)

        # Voice 3: Glass Harmonica Chord Pad
        v3_y = v2_y + box_spacing
        draw_rectangle(vis_x + 20, v3_y, vis_w - 40, 70, Color(22, 32, 38, 255))
        draw_rectangle_lines(vis_x + 20, v3_y, vis_w - 40, 70, Color(45, 75, 80, 255))
        pad_tones_str = ", ".join(f"{f:.1f}Hz" for f in PAD_CHORDS[current_chord_idx])
        draw_text("Voice 3: Glass Harmonica Chord Pad (Gain 0.20)", vis_x + 35, v3_y + 10, 13, Color(150, 240, 220, 255))
        draw_text(f"Fragile high partials (1x, 2x, 3x, 4.16x): [{pad_tones_str}] | 1.8 Hz wet tremolo", vis_x + 35, v3_y + 35, 12, RAYWHITE)

        # Voice 4: Dropper Drip Pings & Effervescent Noise
        v4_y = v3_y + box_spacing
        draw_rectangle(vis_x + 20, v4_y, vis_w - 40, 70, Color(22, 32, 38, 255))
        draw_rectangle_lines(vis_x + 20, v4_y, vis_w - 40, 70, Color(45, 75, 80, 255))
        drip_active = any(abs(current_beat - dp) < 0.3 for dp in DRIP_PING_BEATS)
        fizz_active = any(0.0 <= (current_beat - fz) < 1.5 for fz in FIZZ_RISER_BEATS)
        perc_status = "DRIP PLINK!" if drip_active else ("FIZZING BUBBLE RISER..." if fizz_active else "Resting reaction")
        draw_text("Voice 4: Dropper Drip Pings & Effervescent Noise (Gain 0.16)", vis_x + 35, v4_y + 10, 13, Color(100, 240, 255, 255))
        draw_text(f"Pipette chirps (2900->1550Hz) + High-pass fizz noise | Status: {perc_status}", vis_x + 35, v4_y + 35, 12, YELLOW if (drip_active or fizz_active) else LIGHTGRAY)

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
