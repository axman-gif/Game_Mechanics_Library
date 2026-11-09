# -*- coding: utf-8 -*-
"""
Procedural Background Music (BGM) Synthesizer - Ancient Runestone
================================================================
Type             : Procedural Audio BGM (Music Stream)
Target File      : assets/audio/BGM/mystical/ancient_runestone.py
Waveforms Used   : Additive sine drone, breath-modeled flute with vibrato, dual beating sines, pitch-swept percussion
Category         : Interactive BGM Soundtracks
Vibe             : Mystical (Druidic Megalith / Ancient Inscriptions)

Problem Solved:
  Eliminates static, heavy external audio assets by algorithmically synthesizing an
  atmospheric 8-bar mystical soundtrack directly in RAM. Streaming through Raylib's
  Music struct avoids high memory overhead while procedural generation guarantees
  mathematically perfect loop seams with zero audio pop artifacts.

Musical Theory & Mathematical Rationale:
  - Tempo: 86.0 Beats Per Minute (BPM) in 4/4 meter.
  - Clock Timing:
      Beat Duration          = 60.0 / 86.0 = 0.697674 seconds per beat.
      Loop Duration (8 Bars) = 32 beats * (60.0 / 86.0) = 22.325578 seconds.
      Total Sample Count     = round(44100 * 22.325578) = 984,558 samples.
  - Modal Architecture: D Dorian Mode (D, E, F, G, A, B, C).
      Progression (2 bars each across 8 bars / 32 beats):
        Bars 1-2 (Beats 0..7)  : Dm7 (Root D, minor 3rd F, 5th A, minor 7th C)
        Bars 3-4 (Beats 8..15) : G7  (Root G, major 3rd B, 5th D, minor 7th F)
        Bars 5-6 (Beats 16..23): Dm7 (Root D, minor 3rd F, 5th A, minor 7th C)
        Bars 7-8 (Beats 24..31): Em7 (Root E, minor 3rd G, 5th B, minor 7th D)
  - 4 Procedural Voice Layers:
      Voice 1 (Earthy Wooden Drone, Gain 0.40):
        Deep 73.4 Hz (D2) fundamental sine combined with its 3rd harmonic (220.2 Hz,
        0.22 relative amplitude) creating a hollow resonant wooden cavern resonance.
      Voice 2 (Resonant Bone Flute, Gain 0.28):
        Expressive modal melody in D Dorian with portamento pitch glides and 5.0 Hz
        vibrato (+/-1.2% pitch deviation) shaped by smooth breath envelopes.
      Voice 3 (Magical Ley-Line Pad, Gain 0.22):
        Dual carrier sines at 220.0 Hz and 222.0 Hz. The 2.0 Hz frequency delta
        generates an acoustic beat frequency modulating amplitude smoothly at 2.0 Hz.
      Voice 4 (Frame Drum & Seed Pods, Gain 0.16):
        Heartbeat pitch-swept sine (85.0 Hz downward sweep to 42.0 Hz, exponential
        decay rate k=7.5) on beats 1 and 3, paired with ceremonial bandpass noise
        shaker bursts on syncopated off-beats.
  - Master Clamping:
      Master mix softly saturated via tanh and clamped strictly to [-26500, 26500]
      in signed 16-bit mono PCM, providing 2.0 dB of digital headroom.

Direct C++ Raylib Translation (raylib.h):
  struct AncientRunestoneBGM {
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
BPM = 86.0

# 8 Bars of 4/4 time at 86.0 BPM = exactly 32 beats
TOTAL_BEATS = 32
SECONDS_PER_BEAT = 60.0 / BPM
LOOP_DURATION_SECONDS = TOTAL_BEATS * SECONDS_PER_BEAT

# Exact loop sample count: round(44100 * 32 * 60 / 86.0) = 984,558 samples
TOTAL_LOOP_SAMPLES = 984558
SAMPLES_PER_BEAT = TOTAL_LOOP_SAMPLES / float(TOTAL_BEATS)

# Harmonic progression metadata for UI and synthesis analysis
CHORD_NAMES = ["Dm7", "Dm7", "G7", "G7", "Dm7", "Dm7", "Em7", "Em7"]

# Bone flute melodic phrase definitions: (start_beat, duration_beats, frequency_hz)
# Mode: D Dorian over progression Dm7 (bars 1-2) -> G7 (bars 3-4) -> Dm7 (bars 5-6) -> Em7 (bars 7-8)
FLUTE_MELODY = [
    # Bars 1-2 (Dm7): Root D, minor 3rd F, 5th A, minor 7th C
    (0.0, 2.0, 293.66),   # D4
    (2.0, 1.5, 349.23),   # F4
    (3.5, 0.5, 392.00),   # G4
    (4.0, 2.0, 440.00),   # A4
    (6.0, 1.0, 523.25),   # C5
    (7.0, 1.0, 440.00),   # A4
    # Bars 3-4 (G7): Root G, major 3rd B, 5th D, minor 7th F
    (8.0, 2.0, 493.88),   # B4
    (10.0, 1.5, 587.33),  # D5
    (11.5, 0.5, 523.25),  # C5
    (12.0, 2.0, 493.88),  # B4
    (14.0, 1.0, 392.00),  # G4
    (15.0, 1.0, 349.23),  # F4
    # Bars 5-6 (Dm7): Ethereal high arch
    (16.0, 2.0, 440.00),  # A4
    (18.0, 1.5, 523.25),  # C5
    (19.5, 0.5, 587.33),  # D5
    (20.0, 2.0, 698.46),  # F5
    (22.0, 1.0, 659.25),  # E5
    (23.0, 1.0, 587.33),  # D5
    # Bars 7-8 (Em7): Tension and return resolution to D4
    (24.0, 2.0, 329.63),  # E4
    (26.0, 1.5, 392.00),  # G4
    (27.5, 0.5, 440.00),  # A4
    (28.0, 2.0, 493.88),  # B4
    (30.0, 1.0, 523.25),  # C5
    (31.0, 1.0, 293.66),  # D4 (seamless return to tonic)
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
def create_ancient_runestone_bgm() -> Music:
    """
    Synthesizes the 8-bar 'Ancient Runestone' mystical loop in RAM.
    Returns an initialized Raylib Music stream with looping enabled.
    """
    sin = math.sin
    cos = math.cos
    exp = math.exp
    tanh = math.tanh
    inv_sr = 1.0 / float(SAMPLE_RATE)
    pack_into = py_struct.pack_into

    # Precalculate flute note envelopes and portamento frequency tables
    flute_freqs = [293.66] * TOTAL_LOOP_SAMPLES
    flute_envs = [0.0] * TOTAL_LOOP_SAMPLES

    prev_freq = 293.66
    glide_samples = int(0.08 * SAMPLE_RATE)    # 80ms pitch glide between notes
    attack_samples = int(0.04 * SAMPLE_RATE)   # 40ms organic breath attack
    release_samples = int(0.06 * SAMPLE_RATE)  # 60ms soft note release

    for start_b, dur_b, target_freq in FLUTE_MELODY:
        s_start = int(start_b * SAMPLES_PER_BEAT)
        s_end = int((start_b + dur_b) * SAMPLES_PER_BEAT)
        dur = s_end - s_start
        for k in range(dur):
            idx = s_start + k
            if idx >= TOTAL_LOOP_SAMPLES:
                break
            # Portamento pitch glide
            if k < glide_samples:
                alpha = float(k) / float(glide_samples)
                freq = prev_freq + (target_freq - prev_freq) * alpha
            else:
                freq = target_freq
            flute_freqs[idx] = freq

            # Breath envelope with cosine ramps
            if k < attack_samples:
                env = 0.5 * (1.0 - cos(math.pi * float(k) / float(attack_samples)))
            elif k > dur - release_samples:
                env = 0.5 * (1.0 + cos(math.pi * float(k - (dur - release_samples)) / float(release_samples)))
            else:
                env = 1.0
            flute_envs[idx] = env
        prev_freq = target_freq

    # Phase accumulators for all procedural voice layers
    phase_drone1 = 0.0
    phase_drone3 = 0.0
    phase_pad1 = 0.0
    phase_pad2 = 0.0
    phase_flute = 0.0
    phase_vib = 0.0
    phase_drum = 0.0
    prev_noise = 0.0

    # Constant angular frequency increments
    dphi_drone1 = PI2 * 73.4 * inv_sr   # D2 fundamental wooden resonance
    dphi_drone3 = PI2 * 220.2 * inv_sr  # 3rd harmonic overtone
    dphi_pad1 = PI2 * 220.0 * inv_sr    # Ley-line binaural carrier 1
    dphi_pad2 = PI2 * 222.0 * inv_sr    # Ley-line binaural carrier 2 (2 Hz beating delta)
    vibrato_rate = PI2 * 5.0 * inv_sr   # 5.0 Hz expressive flute vibrato

    # Preallocate PCM byte buffer for maximal generation throughput
    pcm_buffer = bytearray(TOTAL_LOOP_SAMPLES * 2)

    for i in range(TOTAL_LOOP_SAMPLES):
        beat_f = float(i) / SAMPLES_PER_BEAT
        bar_beat_f = beat_f % 4.0
        bar_beat_int = int(bar_beat_f)

        # ----------------------------------------------------------------------
        # Voice 1: Earthy Wooden Drone (Gain 0.40)
        # Low D2 fundamental (73.4 Hz) + 3rd harmonic (220.2 Hz, 0.22 amplitude)
        # ----------------------------------------------------------------------
        drone_raw = (sin(phase_drone1) + 0.22 * sin(phase_drone3)) / 1.22
        v1 = 0.40 * drone_raw
        phase_drone1 += dphi_drone1
        phase_drone3 += dphi_drone3

        # ----------------------------------------------------------------------
        # Voice 2: Resonant Bone Flute (Gain 0.28)
        # D Dorian melodies with 5.0 Hz vibrato (+/-1.2% pitch deviation) & glides
        # ----------------------------------------------------------------------
        vib = 1.0 + 0.012 * sin(phase_vib)
        phase_vib += vibrato_rate
        inst_flute_freq = flute_freqs[i] * vib
        phase_flute += PI2 * inst_flute_freq * inv_sr

        # Resonant bone flute harmonic profile (fundamental + hollow overtones)
        flute_wave = (0.80 * sin(phase_flute) +
                      0.15 * sin(2.0 * phase_flute) +
                      0.05 * sin(3.0 * phase_flute))
        v2 = 0.28 * flute_wave * flute_envs[i]

        # ----------------------------------------------------------------------
        # Voice 3: Magical Ley-Line Pad (Gain 0.22)
        # Dual beating sines at 220.0 Hz & 222.0 Hz creating 2.0 Hz binaural pulsation
        # ----------------------------------------------------------------------
        pad_raw = 0.5 * (sin(phase_pad1) + sin(phase_pad2))
        v3 = 0.22 * pad_raw
        phase_pad1 += dphi_pad1
        phase_pad2 += dphi_pad2

        # ----------------------------------------------------------------------
        # Voice 4: Frame Drum & Seed Pods (Gain 0.16)
        # Heartbeat pitch-swept sine (85 -> 42 Hz, decay k=7.5) on beats 1 and 3
        # Ceremonial shaker bursts (bandpass noise) on syncopated off-beats
        # ----------------------------------------------------------------------
        v4_drum = 0.0
        v4_shaker = 0.0

        # Heartbeat low drum impact on beats 1 and 3 (0-indexed beats 0 and 2)
        if bar_beat_int in (0, 2):
            t_drum = (bar_beat_f - float(bar_beat_int)) * SECONDS_PER_BEAT
            f_drum = 42.0 + 43.0 * exp(-16.0 * t_drum)
            phase_drum += PI2 * f_drum * inv_sr
            drum_env = exp(-7.5 * t_drum)
            v4_drum = sin(phase_drum) * drum_env
        else:
            phase_drum = 0.0

        # Ceremonial shaker bursts on off-beats (0-indexed beats 1 and 3)
        if bar_beat_int in (1, 3):
            t_shake = (bar_beat_f - float(bar_beat_int)) * SECONDS_PER_BEAT
            raw_noise = random.random() * 2.0 - 1.0
            bp_noise = raw_noise - 0.75 * prev_noise
            prev_noise = raw_noise
            shake_env = exp(-22.0 * t_shake)
            v4_shaker = 0.45 * bp_noise * shake_env

        v4 = 0.16 * (0.85 * v4_drum + v4_shaker)

        # ----------------------------------------------------------------------
        # Master Mix, Soft Saturation & PCM Clamping
        # ----------------------------------------------------------------------
        master_mix = tanh((v1 + v2 + v3 + v4) * 1.30)

        # Seamless loop boundary micro-fade (128 samples click prevention ramp)
        if i < 128:
            master_mix *= 0.5 * (1.0 - cos(math.pi * float(i) / 128.0))
        elif i > TOTAL_LOOP_SAMPLES - 128:
            master_mix *= 0.5 * (1.0 - cos(math.pi * float(TOTAL_LOOP_SAMPLES - 1 - i) / 128.0))

        # Clamp strictly to [-26500, 26500]
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
create_bgm = create_ancient_runestone_bgm
bgm_mystical_ancient_runestone = create_ancient_runestone_bgm


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
    to audition the Ancient Runestone BGM live with telemetry and visualizer.
    """
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        init_window(self.screen_width, self.screen_height,
                    "BGM Workbench - Ancient Runestone (assets/audio/BGM/mystical/ancient_runestone.py)")
        set_target_fps(60)
        init_audio_device()

        self.music = create_ancient_runestone_bgm()
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
        clear_background(Color(14, 18, 26, 255))

        # Title Header (kept in left region x < 450, leaving top-bar x=450..980, y=14..48 clear)
        draw_text("PROCEDURAL BGM AUDITION WORKBENCH", 24, 18, 18, RAYWHITE)
        draw_text("Asset: assets/audio/BGM/mystical/ancient_runestone.py | 86.0 BPM D Dorian Druidic Megalith",
                  24, 44, 12, Color(80, 230, 180, 255))

        # ----------------------------------------------------------------------
        # LEFT COLUMN: Telemetry & Controls Info Cards
        # ----------------------------------------------------------------------
        panel_y = 74
        # Telemetry Card
        draw_rectangle(24, panel_y, 400, 250, Color(20, 26, 38, 255))
        draw_rectangle_lines(24, panel_y, 400, 250, Color(45, 68, 85, 255))
        draw_text("DRUIDIC MEGALITH TELEMETRY", 40, panel_y + 14, 14, Color(80, 230, 180, 255))
        draw_text("Tempo / Meter   : 86.0 BPM | 4/4 Time | 8 Bars", 40, panel_y + 40, 12, RAYWHITE)
        draw_text("Harmonic Mode   : D Dorian (D - E - F - G - A - B - C)", 40, panel_y + 64, 12, RAYWHITE)
        draw_text("Progression     : Dm7 (2b) -> G7 (2b) -> Dm7 (2b) -> Em7 (2b)", 40, panel_y + 88, 12, LIGHTGRAY)
        draw_text("Loop Duration   : 22.33s (984,558 Samples)", 40, panel_y + 112, 12, LIGHTGRAY)
        draw_text("Voice 1 (Drone) : 73.4 Hz (D2) + 220.2 Hz (Gain 0.40)", 40, panel_y + 136, 12, Color(160, 220, 160, 255))
        draw_text("Voice 2 (Flute) : D Dorian Melody + 5Hz Vib (Gain 0.28)", 40, panel_y + 160, 12, Color(255, 215, 120, 255))
        draw_text("Voice 3 (Pad)   : 220.0 / 222.0 Hz Dual Beating (Gain 0.22)", 40, panel_y + 184, 12, Color(120, 210, 255, 255))
        draw_text("Voice 4 (Rhythm): Drum (85->42Hz) + Shaker (Gain 0.16)", 40, panel_y + 208, 12, Color(240, 160, 140, 255))

        # Controls Card
        ctrl_y = panel_y + 266
        draw_rectangle(24, ctrl_y, 400, 240, Color(20, 26, 38, 255))
        draw_rectangle_lines(24, ctrl_y, 400, 240, Color(45, 68, 85, 255))
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
        # RIGHT COLUMN: Visualizer, Sequencer Grid & Runic Monoliths
        # Top-bar safe area (x=450..980, y=14..48) is strictly avoided!
        # ----------------------------------------------------------------------
        vis_x = 450
        vis_y = 74
        vis_w = 806
        vis_h = 620
        draw_rectangle(vis_x, vis_y, vis_w, vis_h, Color(16, 22, 32, 255))
        draw_rectangle_lines(vis_x, vis_y, vis_w, vis_h, Color(45, 65, 85, 255))
        draw_text("DRUIDIC SEQUENCER & PROCEDURAL VOICE LAYERS", vis_x + 20, vis_y + 16, 15, Color(80, 230, 180, 255))

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

            # Color coding according to harmonic chord progression
            if bar_idx in (0, 1, 4, 5):  # Dm7 bars
                base_col = Color(28, 55, 45, 255) if (s % 4 == 0) else Color(18, 38, 30, 255)
            elif bar_idx in (2, 3):       # G7 bars
                base_col = Color(55, 48, 25, 255) if (s % 4 == 0) else Color(38, 32, 18, 255)
            else:                         # Em7 bars
                base_col = Color(45, 30, 55, 255) if (s % 4 == 0) else Color(30, 20, 38, 255)

            box_col = Color(100, 255, 200, 255) if is_active else base_col
            draw_rectangle(bx, grid_y, step_w - 2, 32, box_col)
            if is_active:
                draw_rectangle_lines(bx, grid_y, step_w - 2, 32, RAYWHITE)

        draw_text(f"Sequencer Beat: {current_beat + 1:02d} / 32 | Bar: {current_bar + 1} / 8 | Active Chord: {current_chord} | Time: {time_played:.2f}s / {time_total:.2f}s",
                  vis_x + 20, grid_y + 42, 12, LIGHTGRAY)

        # Loop Progress Bar
        bar_y = vis_y + 128
        draw_rectangle(vis_x + 20, bar_y, vis_w - 40, 12, Color(24, 30, 42, 255))
        fill_w = int(loop_progress * (vis_w - 40))
        draw_rectangle(vis_x + 20, bar_y, fill_w, 12, Color(80, 230, 180, 255))
        draw_rectangle_lines(vis_x + 20, bar_y, vis_w - 40, 12, Color(50, 70, 95, 255))

        # ----------------------------------------------------------------------
        # Standing Runestone Megaliths (4 Visual Procedural Pillars)
        # ----------------------------------------------------------------------
        stone_y = vis_y + 160
        draw_text("ANCIENT RUNESTONE MEGALITHS (PROCEDURAL LAYER VISUALIZER)",
                  vis_x + 20, stone_y, 13, Color(255, 200, 80, 255))

        pillars = [
            ("EARTH DRONE", "73.4 Hz + 220.2 Hz", Color(70, 180, 110, 255), True),
            ("BONE FLUTE", "D Dorian Melody", Color(255, 215, 120, 255), self.is_playing),
            ("LEY-LINE PAD", "220 / 222 Hz Beat", Color(100, 200, 255, 255), self.is_playing),
            ("FRAME DRUM", "Heartbeat & Shaker", Color(240, 140, 120, 255), (current_beat % 2 == 0) and self.is_playing),
        ]

        pillar_w = (vis_w - 60) // 4
        for p_idx, (p_title, p_sub, p_col, p_glow) in enumerate(pillars):
            px = vis_x + 20 + p_idx * (pillar_w + 7)
            py = stone_y + 26
            ph = 140

            # Stone pillar body
            draw_rectangle(px, py, pillar_w, ph, Color(24, 32, 44, 255))
            draw_rectangle_lines(px, py, pillar_w, ph, Color(50, 68, 90, 255))

            # Carved runic glyph
            rx = px + pillar_w // 2
            ry = py + 45
            glyph_alpha = 255 if p_glow else 80
            g_col = Color(p_col.r, p_col.g, p_col.b, glyph_alpha)

            # Draw glowing rune lines
            draw_line(rx, ry - 22, rx, ry + 22, g_col)
            draw_line(rx - 14, ry - 10, rx + 14, ry + 10, g_col)
            draw_line(rx - 14, ry + 10, rx + 14, ry - 10, g_col)
            draw_circle_lines(rx, ry, 16, g_col)

            # Pillar labels
            draw_text(p_title, px + 8, py + 92, 11, g_col)
            draw_text(p_sub, px + 8, py + 112, 10, LIGHTGRAY)

        # ----------------------------------------------------------------------
        # Voice Layer Telemetry Panels
        # ----------------------------------------------------------------------
        meter_y = stone_y + 186
        draw_rectangle(vis_x + 20, meter_y, vis_w - 40, 160, Color(20, 26, 38, 255))
        draw_rectangle_lines(vis_x + 20, meter_y, vis_w - 40, 160, Color(45, 65, 85, 255))
        draw_text("LAYER OSCILLATOR STATUS", vis_x + 36, meter_y + 12, 13, Color(80, 230, 180, 255))

        draw_text("[Voice 1: Wooden Drone]  Fundamental: 73.4 Hz | 3rd Harmonic: 220.2 Hz (0.22 amp) | Gain: 0.40",
                  vis_x + 36, meter_y + 38, 12, Color(160, 220, 160, 255))

        flute_note_idx = min(len(FLUTE_MELODY) - 1, int((current_beat / TOTAL_BEATS) * len(FLUTE_MELODY)))
        flute_cur_freq = FLUTE_MELODY[flute_note_idx][2]
        draw_text(f"[Voice 2: Bone Flute]   Melodic Target: {flute_cur_freq:.1f} Hz | Vibrato: 5.0 Hz (+/-1.2%) | Gain: 0.28",
                  vis_x + 36, meter_y + 64, 12, Color(255, 215, 120, 255))

        draw_text("[Voice 3: Ley-Line Pad]  Dual Sines: 220.0 Hz & 222.0 Hz -> Natural 2.0 Hz Acoustic Beat | Gain: 0.22",
                  vis_x + 36, meter_y + 90, 12, Color(120, 210, 255, 255))

        drum_hit = "HEARTBEAT IMPACT (85->42 Hz)" if (current_beat % 4 in (0, 2)) else "SHAKER BURST (Bandpass)"
        draw_text(f"[Voice 4: Frame Rhythm]  Percussion State: {drum_hit} | Gain: 0.16",
                  vis_x + 36, meter_y + 116, 12, Color(240, 160, 140, 255))

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
