# -*- coding: utf-8 -*-
"""
Procedural Background Music (BGM) Synthesizer - Puzzle Lab
==========================================================
Type             : Procedural Audio BGM (Music Stream)
Target File      : assets/audio/BGM/curious/puzzle_lab.py
Waveforms Used   : Warm plucked upright bass, syncopated marimba & celesta, Rhodes electric piano, clockwork ratchet & woodblock
Category         : Interactive BGM Soundtracks
Vibe             : Curious (Cerebral Puzzle Lab / Socket Workbench / Logic Circuit)

Problem Solved:
  Eliminates bulky soundtrack audio files by algorithmically composing multi-layer,
  looping background music purely in RAM using mathematical waveforms. Streamed
  in small buffer chunks via Raylib's Music struct for minimal memory footprint
  while guaranteeing mathematically seamless loop seams with zero audio pop artifacts.

Musical Theory & Mathematical Rationale:
  - Tempo: 104.0 Beats Per Minute (BPM) in 4/4 meter.
  - Clock Timing:
      Beat Duration          = 60.0 / 104.0 = 0.576923 seconds per beat.
      Loop Duration (8 Bars) = 32 beats * (60.0 / 104.0) = 18.461538 seconds.
      Total Sample Count     = round(44100 * 18.461538) = 814,154 samples.
  - Modal Architecture: C Lydian Mode (C, D, E, F#, G, A, B).
      The characteristic augmented fourth (F#, 369.99 Hz / 739.99 Hz) infuses the
      composition with an inquisitive, cerebral, and optimistic mathematical tone.
      Progression (2 bars each across 8 bars / 32 beats / 64 steps):
        Bars 1-2 (Beats 0..7)  : Cmaj7 (Root C, major 3rd E, 5th G, major 7th B)
        Bars 3-4 (Beats 8..15) : D/C   (Root pedal C, major 2nd D, sharp 4th F#, 6th A)
        Bars 5-6 (Beats 16..23): Em7   (Root E, minor 3rd G, 5th B, minor 7th D)
        Bars 7-8 (Beats 24..31): Bm7   (Root B, minor 3rd D, 5th F#, minor 7th A)
  - 4 Procedural Voice Layers:
      Voice 1 (Plucked Upright Acoustic Bass, Gain 0.38):
        Warm plucked upright acoustic bass walking playfully through chord roots on
        quarter beats. Dual-partial acoustic model: fundamental sine + 2nd harmonic
        warmth (0.30 relative amp) and 3rd harmonic body presence (0.10 relative amp)
        shaped by exponential string damping (decay rates k=3.2 and k=7.5).
      Voice 2 (Resonant Marimba & Celesta, Gain 0.28):
        Syncopated inquisitive motifs in C Lydian. Tuned wooden bar model with 4th harmonic
        (k=12.0) and celesta bell chime at 9.2x fundamental (k=20.0), shaped by rapid
        percussive decay (k=6.0) as specified.
      Voice 3 (Smooth Rhodes Electric Piano Chords, Gain 0.22):
        Warm 4-note chord voicings synthesized with dual sine partials and gentle 3.2 Hz
        tremolo modulation (depth 0.18) with smooth 80ms attack/release envelopes.
      Voice 4 (Precision Clockwork Percussion, Gain 0.14):
        Precision 16th-note clockwork ratchet clicks (exponential noise + 2800 Hz metallic
        micro-tick), resonant hollow woodblock taps (840 Hz and 960 Hz, decay k=45.0), and
        brushed snare shuffles (bandpass filtered noise, decay k=18.0).
  - Master Mix & Headroom:
      Soft saturation via tanh and strictly clamped to [-27000, 27000] in signed 16-bit
      mono PCM with a 128-sample cosine micro-fade at loop boundaries for seamless looping.

Direct C++ Raylib Translation (raylib.h):
  struct PuzzleLabBGM {
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
BPM = 104.0

# 8 Bars of 4/4 meter at 104.0 BPM = exactly 32 beats = 64 steps (8th notes)
TOTAL_BEATS = 32
SECONDS_PER_BEAT = 60.0 / BPM
LOOP_DURATION_SECONDS = TOTAL_BEATS * SECONDS_PER_BEAT

# Exact loop sample count: round(44100 * 32 * 60 / 104.0) = 814,154 samples (18.46s)
TOTAL_LOOP_SAMPLES = 814154
SAMPLES_PER_BEAT = TOTAL_LOOP_SAMPLES / float(TOTAL_BEATS)
TOTAL_STEPS = 64
SAMPLES_PER_STEP = TOTAL_LOOP_SAMPLES / float(TOTAL_STEPS)

# Harmonic progression metadata for UI and synthesis analysis
CHORD_NAMES = ["Cmaj7", "Cmaj7", "D/C", "D/C", "Em7", "Em7", "Bm7", "Bm7"]

# 4-note voicings for the Rhodes piano pad (frequencies in Hz)
CHORD_NOTES = [
    [261.63, 329.63, 392.00, 493.88],  # Cmaj7 (C4, E4, G4, B4)
    [261.63, 293.66, 369.99, 440.00],  # D/C   (C4, D4, F#4, A4)
    [329.63, 392.00, 493.88, 587.33],  # Em7   (E4, G4, B4, D5)
    [293.66, 369.99, 440.00, 493.88],  # Bm7   (D4, F#4, A4, B4)
]

# Upright acoustic bass walking line across 32 quarter beats (frequencies in Hz)
BASS_NOTES = [
    # Bars 1-2: Cmaj7 walking line
    65.41, 82.41, 98.00, 123.47, 130.81, 123.47, 98.00, 73.42,
    # Bars 3-4: D/C walking line with Lydian F# and A
    65.41, 73.42, 92.50, 110.00, 146.83, 130.81, 110.00, 92.50,
    # Bars 5-6: Em7 walking line
    82.41, 98.00, 123.47, 146.83, 164.81, 146.83, 123.47, 110.00,
    # Bars 7-8: Bm7 walking line resolving to C2
    61.74, 73.42, 92.50, 110.00, 123.47, 110.00, 92.50, 73.42,
]

# Syncopated inquisitive marimba/celesta motif across 64 steps (0.0 = rest)
LEAD_PATTERN = [
    # Bars 1-2: Cmaj7 - Inquisitive arpeggio motif
    392.00, 0.0, 493.88, 523.25, 0.0, 659.25, 587.33, 0.0,
    783.99, 0.0, 659.25, 523.25, 0.0, 493.88, 392.00, 0.0,
    # Bars 3-4: D/C - Lydian sharp fourth runs (F#5 = 739.99 Hz)
    440.00, 0.0, 739.99, 0.0, 587.33, 659.25, 739.99, 0.0,
    880.00, 0.0, 739.99, 587.33, 0.0, 523.25, 440.00, 0.0,
    # Bars 5-6: Em7 - Reflective puzzle-solving motif
    493.88, 0.0, 783.99, 659.25, 0.0, 587.33, 493.88, 0.0,
    659.25, 0.0, 783.99, 987.77, 0.0, 880.00, 783.99, 0.0,
    # Bars 7-8: Bm7 - Harmonic resolution
    369.99, 0.0, 493.88, 587.33, 0.0, 739.99, 659.25, 0.0,
    587.33, 0.0, 493.88, 440.00, 0.0, 493.88, 587.33, 0.0,
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
def generate_puzzle_track() -> Music:
    """
    Synthesizes the 8-bar 'Puzzle Lab' C Lydian groove loop in RAM.
    Returns an initialized Raylib Music stream with looping enabled.
    """
    sin = math.sin
    cos = math.cos
    exp = math.exp
    tanh = math.tanh
    inv_sr = 1.0 / float(SAMPLE_RATE)
    pi2_inv_sr = PI2 * inv_sr
    pack_into = py_struct.pack_into

    pcm_buffer = bytearray(TOTAL_LOOP_SAMPLES * 2)

    # Precalculate beat and step transition points for high-performance indexing
    beat_starts = [int(b * SAMPLES_PER_BEAT) for b in range(33)]
    step_starts = [int(s * SAMPLES_PER_STEP) for s in range(65)]

    next_beat_sample = beat_starts[1]
    next_step_sample = step_starts[1]
    beat_idx = 0
    step_idx = 0
    chord_idx = 0

    # Phase accumulators
    phase_bass = 0.0
    phase_lead = 0.0
    phase_p0 = 0.0
    phase_p1 = 0.0
    phase_p2 = 0.0
    phase_p3 = 0.0
    prev_noise = 0.0

    cur_lead_freq = 392.0
    lead_note_t = 100.0

    # Frequency increments
    f_bass = BASS_NOTES[0]
    dphi_bass = pi2_inv_sr * f_bass

    cn = CHORD_NOTES[0]
    dphi_p0 = pi2_inv_sr * cn[0]
    dphi_p1 = pi2_inv_sr * cn[1]
    dphi_p2 = pi2_inv_sr * cn[2]
    dphi_p3 = pi2_inv_sr * cn[3]

    for i in range(TOTAL_LOOP_SAMPLES):
        t_global = float(i) * inv_sr

        # Beat transition handler
        if i == next_beat_sample and beat_idx < 31:
            beat_idx += 1
            next_beat_sample = beat_starts[beat_idx + 1]
            f_bass = BASS_NOTES[beat_idx]
            dphi_bass = pi2_inv_sr * f_bass
            new_chord_idx = beat_idx // 8
            if new_chord_idx != chord_idx:
                chord_idx = new_chord_idx
                cn = CHORD_NOTES[chord_idx]
                dphi_p0 = pi2_inv_sr * cn[0]
                dphi_p1 = pi2_inv_sr * cn[1]
                dphi_p2 = pi2_inv_sr * cn[2]
                dphi_p3 = pi2_inv_sr * cn[3]

        # Step transition handler
        if i == next_step_sample and step_idx < 63:
            step_idx += 1
            next_step_sample = step_starts[step_idx + 1]
            target_f = LEAD_PATTERN[step_idx]
            if target_f > 0.0:
                cur_lead_freq = target_f
                lead_note_t = 0.0

        # ----------------------------------------------------------------------
        # Voice 1: Upright Acoustic Bass (Gain 0.38)
        # Plucked double bass with fundamental + 2nd and 3rd body harmonics
        # ----------------------------------------------------------------------
        t_beat = float(i - beat_starts[beat_idx]) * inv_sr
        phase_bass += dphi_bass
        atk_bass = min(1.0, t_beat * 125.0)  # 8ms organic pluck attack
        dec_fund = exp(-3.2 * t_beat)
        dec_hi = exp(-7.5 * t_beat)
        bass_waveform = sin(phase_bass) * dec_fund + (0.30 * sin(2.0 * phase_bass) + 0.10 * sin(3.0 * phase_bass)) * dec_hi
        v1 = 0.38 * atk_bass * bass_waveform

        # ----------------------------------------------------------------------
        # Voice 2: Resonant Marimba & Celesta (Gain 0.28)
        # Syncopated inquisitive motif: wooden 4th harmonic + celesta 9.2x chime
        # ----------------------------------------------------------------------
        lead_note_t += inv_sr
        phase_lead += pi2_inv_sr * cur_lead_freq
        atk_lead = min(1.0, lead_note_t * 333.3)  # 3ms crisp mallet strike
        dec_lead = exp(-6.0 * lead_note_t)        # Specified decay k=6.0
        marimba_body = sin(phase_lead) + 0.35 * sin(4.0 * phase_lead) * exp(-12.0 * lead_note_t) + 0.16 * sin(9.2 * phase_lead) * exp(-20.0 * lead_note_t)
        v2 = 0.28 * atk_lead * dec_lead * marimba_body

        # ----------------------------------------------------------------------
        # Voice 3: Rhodes Electric Piano Chords (Gain 0.22)
        # 4-note voicings with dual sine partials and gentle 3.2 Hz tremolo
        # ----------------------------------------------------------------------
        phase_p0 += dphi_p0
        phase_p1 += dphi_p1
        phase_p2 += dphi_p2
        phase_p3 += dphi_p3
        t_chord = float(i - beat_starts[chord_idx * 8]) * inv_sr
        chord_dur = 8.0 * SECONDS_PER_BEAT
        atk_pad = min(1.0, t_chord * 12.5)  # 80ms smooth attack ramp
        rel_pad = min(1.0, (chord_dur - t_chord) * 12.5) if t_chord > (chord_dur - 0.08) else 1.0
        tremolo = 1.0 + 0.18 * sin(pi2_inv_sr * 3.2 * SAMPLE_RATE * t_global)
        pad_sum = 0.25 * (sin(phase_p0) + sin(phase_p1) + sin(phase_p2) + sin(phase_p3))
        v3 = 0.22 * pad_sum * atk_pad * rel_pad * tremolo

        # ----------------------------------------------------------------------
        # Voice 4: Clockwork Percussion (Gain 0.14)
        # Ratchet clicks, hollow woodblock taps, and brushed snare shuffles
        # ----------------------------------------------------------------------
        # 1. Clockwork ratchet click every 16th note
        t_sub = float(i % 6360) * inv_sr
        raw_noise = random.random() * 2.0 - 1.0
        ratchet = raw_noise * exp(-700.0 * t_sub) + 0.5 * sin(pi2_inv_sr * 2800.0 * SAMPLE_RATE * t_sub) * exp(-450.0 * t_sub)

        # 2. Resonant woodblock taps on syncopated off-beats
        bar_beat_f = (float(i) / SAMPLES_PER_BEAT) % 4.0
        wb_val = 0.0
        wb_t1 = (bar_beat_f - 1.0) * SECONDS_PER_BEAT
        if 0.0 <= wb_t1 < 0.12:
            wb_val = sin(pi2_inv_sr * 840.0 * SAMPLE_RATE * wb_t1) * exp(-45.0 * wb_t1)
        wb_t2 = (bar_beat_f - 2.5) * SECONDS_PER_BEAT
        if 0.0 <= wb_t2 < 0.12:
            wb_val = 0.8 * sin(pi2_inv_sr * 960.0 * SAMPLE_RATE * wb_t2) * exp(-50.0 * wb_t2)

        # 3. Brushed snare shuffle on beats 1 and 3
        bar_beat_int = int(bar_beat_f)
        snare_val = 0.0
        if bar_beat_int in (1, 3):
            t_snare = (bar_beat_f - float(bar_beat_int)) * SECONDS_PER_BEAT
            bp_noise = raw_noise - 0.70 * prev_noise
            prev_noise = raw_noise
            snare_val = bp_noise * exp(-18.0 * t_snare)

        v4 = 0.14 * (0.35 * ratchet + 0.50 * wb_val + 0.40 * snare_val)

        # ----------------------------------------------------------------------
        # Master Mix, Soft Saturation & Headroom Clamping
        # ----------------------------------------------------------------------
        master_mix = tanh((v1 + v2 + v3 + v4) * 1.25)

        # Seamless loop boundary micro-fade (128 samples click prevention ramp)
        if i < 128:
            master_mix *= 0.5 * (1.0 - cos(math.pi * float(i) / 128.0))
        elif i > TOTAL_LOOP_SAMPLES - 128:
            master_mix *= 0.5 * (1.0 - cos(math.pi * float(TOTAL_LOOP_SAMPLES - 1 - i) / 128.0))

        # Clamp strictly to [-27000, 27000]
        pcm_int = int(master_mix * 26800.0)
        clamped_pcm = max(-27000, min(27000, pcm_int))
        pack_into('<h', pcm_buffer, i * 2, clamped_pcm)

    # Encapsulate in 44-byte RIFF container and load into Raylib
    wav_bytes = pack_riff_wav_mono_16bit(SAMPLE_RATE, pcm_buffer)
    music = load_music_stream_from_memory(".wav", wav_bytes, len(wav_bytes))
    music.looping = True

    # Pin WAV buffer in memory to protect from Python GC while streaming
    _ACTIVE_BUFFERS[id(music)] = wav_bytes
    return music


# Standardized alias mappings for universal dynamic discovery
create_bgm = generate_puzzle_track
create_puzzle_lab_bgm = generate_puzzle_track
bgm_curious_puzzle_lab = generate_puzzle_track


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
    to audition the Puzzle Lab BGM live with telemetry and visualizer.
    """
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        init_window(
            self.screen_width,
            self.screen_height,
            "BGM Workbench - Puzzle Lab (assets/audio/BGM/curious/puzzle_lab.py)"
        )
        set_target_fps(60)
        init_audio_device()

        self.music = generate_puzzle_track()
        self.volume = 0.70
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

        # Feed audio stream buffer every frame
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
        clear_background(Color(14, 18, 28, 255))

        # Title Header (kept in left region x < 450, leaving top-bar x=450..980, y=14..48 clear)
        draw_text("PROCEDURAL BGM AUDITION WORKBENCH", 24, 18, 18, RAYWHITE)
        draw_text(
            "Asset: assets/audio/BGM/curious/puzzle_lab.py | 104.0 BPM C Lydian Cerebral Groove",
            24, 44, 12, Color(100, 210, 255, 255)
        )

        # ----------------------------------------------------------------------
        # LEFT COLUMN: Telemetry & Controls Info Cards
        # ----------------------------------------------------------------------
        panel_y = 74
        # Telemetry Card
        draw_rectangle(24, panel_y, 400, 250, Color(20, 26, 40, 255))
        draw_rectangle_lines(24, panel_y, 400, 250, Color(50, 70, 100, 255))
        draw_text("CEREBRAL GROOVE TELEMETRY", 40, panel_y + 14, 14, Color(100, 210, 255, 255))
        draw_text("Tempo / Meter   : 104.0 BPM | 4/4 Time | 8 Bars", 40, panel_y + 40, 12, RAYWHITE)
        draw_text("Harmonic Mode   : C Lydian (C - D - E - F# - G - A - B)", 40, panel_y + 64, 12, RAYWHITE)
        draw_text("Progression     : Cmaj7 (2b) -> D/C (2b) -> Em7 (2b) -> Bm7 (2b)", 40, panel_y + 88, 12, LIGHTGRAY)
        draw_text("Loop Duration   : 18.46s (814,154 Samples)", 40, panel_y + 112, 12, LIGHTGRAY)
        draw_text("Voice 1 (Bass)  : Upright Plucked Bass | Quarter Beats (Gain 0.38)", 40, panel_y + 136, 12, Color(130, 220, 160, 255))
        draw_text("Voice 2 (Lead)  : Marimba & Celesta | Decay k=6.0 (Gain 0.28)", 40, panel_y + 160, 12, Color(255, 215, 120, 255))
        draw_text("Voice 3 (Pad)   : Rhodes Piano | 3.2 Hz Tremolo (Gain 0.22)", 40, panel_y + 184, 12, Color(140, 200, 255, 255))
        draw_text("Voice 4 (Rhythm): Ratchet Clicks, Woodblock, Snare (Gain 0.14)", 40, panel_y + 208, 12, Color(255, 150, 130, 255))

        # Controls Card
        ctrl_y = panel_y + 266
        draw_rectangle(24, ctrl_y, 400, 240, Color(20, 26, 40, 255))
        draw_rectangle_lines(24, ctrl_y, 400, 240, Color(50, 70, 100, 255))
        draw_text("BGM CONTROLS", 40, ctrl_y + 14, 14, Color(255, 200, 80, 255))
        draw_text("- [Space] / [M] / Gamepad (A)  : Play / Pause Stream", 40, ctrl_y + 40, 12, RAYWHITE)
        draw_text("- [Up] / [Down] / Gamepad D-pad: Volume (+/- 5%)", 40, ctrl_y + 64, 12, RAYWHITE)
        draw_text("- [Left] / [Right] / D-pad L/R : Tempo / Pitch (+/- 5%)", 40, ctrl_y + 88, 12, RAYWHITE)
        draw_text("- [R] / Gamepad Start          : Reset Loop to Beginning", 40, ctrl_y + 112, 12, RAYWHITE)
        draw_text(
            f"Playback State  : {'PLAYING (Looping)' if self.is_playing else 'PAUSED'}",
            40, ctrl_y + 146, 13, GREEN if self.is_playing else RED
        )
        draw_text(f"Master Volume   : {int(self.volume * 100)}%", 40, ctrl_y + 170, 13, SKYBLUE)
        draw_text(f"Tempo / Pitch   : {self.pitch:.2f}x", 40, ctrl_y + 194, 13, SKYBLUE)
        draw_text("Buffer State    : Pinned in _ACTIVE_BUFFERS (Safe)", 40, ctrl_y + 218, 11, GREEN)

        # ----------------------------------------------------------------------
        # RIGHT COLUMN: Visualizer, Sequencer Grid & Logic Nodes
        # Top-bar safe area (x=450..980, y=14..48) is strictly avoided!
        # ----------------------------------------------------------------------
        vis_x = 450
        vis_y = 74
        vis_w = 806
        vis_h = 620
        draw_rectangle(vis_x, vis_y, vis_w, vis_h, Color(16, 22, 34, 255))
        draw_rectangle_lines(vis_x, vis_y, vis_w, vis_h, Color(45, 65, 95, 255))
        draw_text(
            "CEREBRAL LOGIC CIRCUIT & 32-BEAT SEQUENCER",
            vis_x + 20, vis_y + 16, 15, Color(100, 210, 255, 255)
        )

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
            bar_idx = s // 4

            # Color coding according to C Lydian harmonic chord progression
            if bar_idx in (0, 1):       # Cmaj7 bars (Teal / Cyan)
                base_col = Color(20, 50, 60, 255) if (s % 4 == 0) else Color(15, 35, 42, 255)
            elif bar_idx in (2, 3):     # D/C bars (Amber / Gold)
                base_col = Color(60, 48, 20, 255) if (s % 4 == 0) else Color(40, 32, 15, 255)
            elif bar_idx in (4, 5):     # Em7 bars (Amethyst / Violet)
                base_col = Color(48, 25, 60, 255) if (s % 4 == 0) else Color(32, 18, 40, 255)
            else:                       # Bm7 bars (Cobalt Blue)
                base_col = Color(25, 35, 65, 255) if (s % 4 == 0) else Color(18, 24, 45, 255)

            box_col = Color(120, 230, 255, 255) if is_active else base_col
            draw_rectangle(bx, grid_y, step_w - 2, 32, box_col)
            if is_active:
                draw_rectangle_lines(bx, grid_y, step_w - 2, 32, RAYWHITE)

        draw_text(
            f"Sequencer Beat: {current_beat + 1:02d} / 32 | Bar: {current_bar + 1} / 8 | Active Chord: {current_chord} | Time: {time_played:.2f}s / {time_total:.2f}s",
            vis_x + 20, grid_y + 42, 12, LIGHTGRAY
        )

        # Loop Progress Bar
        bar_y = vis_y + 128
        draw_rectangle(vis_x + 20, bar_y, vis_w - 40, 12, Color(24, 30, 44, 255))
        fill_w = int(loop_progress * (vis_w - 40))
        draw_rectangle(vis_x + 20, bar_y, fill_w, 12, Color(100, 210, 255, 255))
        draw_rectangle_lines(vis_x + 20, bar_y, vis_w - 40, 12, Color(50, 70, 100, 255))

        # ----------------------------------------------------------------------
        # 4 Puzzle Workbench Modules (Visual Procedural Logic Nodes)
        # ----------------------------------------------------------------------
        node_y = vis_y + 160
        draw_text(
            "PUZZLE WORKBENCH LOGIC NODES (PROCEDURAL LAYER STATUS)",
            vis_x + 20, node_y, 13, Color(255, 200, 80, 255)
        )

        bass_freq_now = BASS_NOTES[current_beat]
        step_lead_idx = min(len(LEAD_PATTERN) - 1, int(loop_progress * TOTAL_STEPS))
        lead_freq_now = LEAD_PATTERN[step_lead_idx]

        nodes = [
            ("UPRIGHT BASS", f"Root: {bass_freq_now:.1f} Hz", Color(100, 220, 150, 255), True),
            ("MARIMBA / CELESTA", f"Motif: {lead_freq_now:.1f} Hz" if lead_freq_now > 0 else "Motif: Rest", Color(255, 215, 120, 255), lead_freq_now > 0),
            ("RHODES PIANO", f"Chord: {current_chord}", Color(120, 200, 255, 255), self.is_playing),
            ("CLOCKWORK RHYTHM", "Ratchet & Woodblock", Color(255, 140, 120, 255), (current_beat % 2 == 1) and self.is_playing),
        ]

        node_w = (vis_w - 60) // 4
        for n_idx, (n_title, n_sub, n_col, n_glow) in enumerate(nodes):
            nx = vis_x + 20 + n_idx * (node_w + 7)
            ny = node_y + 26
            nh = 140

            # Logic node module body
            draw_rectangle(nx, ny, node_w, nh, Color(22, 28, 42, 255))
            draw_rectangle_lines(nx, ny, node_w, nh, Color(50, 70, 95, 255))

            # Circuit connection socket / logic symbol
            cx = nx + node_w // 2
            cy = ny + 45
            alpha = 255 if n_glow else 80
            s_col = Color(n_col.r, n_col.g, n_col.b, alpha)

            # Draw socket hexagon / diamond
            draw_line(cx, cy - 18, cx + 16, cy, s_col)
            draw_line(cx + 16, cy, cx, cy + 18, s_col)
            draw_line(cx, cy + 18, cx - 16, cy, s_col)
            draw_line(cx - 16, cy, cx, cy - 18, s_col)
            draw_circle_lines(cx, cy, 10, s_col)

            # Node labels
            draw_text(n_title, nx + 8, ny + 92, 11, s_col)
            draw_text(n_sub, nx + 8, ny + 112, 10, LIGHTGRAY)

        # ----------------------------------------------------------------------
        # Voice Layer Telemetry Panels
        # ----------------------------------------------------------------------
        meter_y = node_y + 186
        draw_rectangle(vis_x + 20, meter_y, vis_w - 40, 160, Color(20, 26, 40, 255))
        draw_rectangle_lines(vis_x + 20, meter_y, vis_w - 40, 160, Color(45, 65, 95, 255))
        draw_text("LAYER OSCILLATOR STATUS", vis_x + 36, meter_y + 12, 13, Color(100, 210, 255, 255))

        draw_text(
            f"[Voice 1: Plucked Bass]  Walking Frequency: {bass_freq_now:.1f} Hz | Dual-Partial Decay (k=3.2/7.5) | Gain: 0.38",
            vis_x + 36, meter_y + 38, 12, Color(130, 220, 160, 255)
        )

        draw_text(
            f"[Voice 2: Marimba/Celesta] Inquisitive Motif Frequency: {lead_freq_now:.1f} Hz | Chime Partial: 9.2x | Decay: k=6.0 | Gain: 0.28",
            vis_x + 36, meter_y + 64, 12, Color(255, 215, 120, 255)
        )

        draw_text(
            f"[Voice 3: Rhodes Piano]  Voicing: {current_chord} (4 notes) | Dual Sines + 3.2 Hz Tremolo (Depth 0.18) | Gain: 0.22",
            vis_x + 36, meter_y + 90, 12, Color(140, 200, 255, 255)
        )

        wb_status = "WOODBLOCK TAP (840/960 Hz)" if (current_beat % 2 == 1) else "RATCHET CLICK (16th ticks)"
        draw_text(
            f"[Voice 4: Clockwork]     Percussion Trigger: {wb_status} | Gain: 0.14",
            vis_x + 36, meter_y + 116, 12, Color(255, 150, 130, 255)
        )

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
