# -*- coding: utf-8 -*-
"""
Procedural Background Music (BGM) Synthesizer - Curious Clockwork Workshop
========================================================================
Type             : Procedural Audio BGM (Music Stream)
Target File      : assets/audio/BGM/curious/clockwork_workshop.py
Waveforms Used   : Additive staccato bass sines, inharmonic metallic music box pings,
                   bandpass micro-noise escapement clicks, pneumatic steam hiss & thud
Category         : Interactive BGM Soundtracks
Vibe             : Curious (Clockwork Workshop / Tinkerer Engineering Laboratory)

Problem Solved:
  Eliminates static, heavy external audio assets by algorithmically synthesizing an
  intricate 8-bar tinkerer laboratory soundtrack directly in RAM. Streaming through
  Raylib's Music struct minimizes memory footprint while procedural generation ensures
  mathematically seamless loop seams with zero audio pop artifacts.

Musical Theory & Mathematical Rationale:
  - Tempo: 100.0 Beats Per Minute (BPM) in 4/4 meter.
  - Clock Timing:
      Beat Duration          = 60.0 / 100.0 = 0.600 seconds per beat.
      Loop Duration (8 Bars) = 32 beats * 0.600 = 19.200 seconds.
      Total Sample Count     = round(44100 * 19.200) = 846,720 samples.
      Samples Per Beat       = 26,460 samples (exact integer).
      Samples Per 8th Note   = 13,230 samples (exact integer).
      Samples Per 16th Note  = 6,615 samples (exact integer).
  - Modal Architecture: A Dorian Mode (A, B, C, D, E, F#, G).
      Progression (2 bars each across 8 bars / 32 beats):
        Bars 1-2 (Beats 0..7)  : Am  (Root A, minor 3rd C, 5th E, minor 7th G)
        Bars 3-4 (Beats 8..15) : D   (Root D, major 3rd F#, 5th A, minor 7th C - Dorian bright 6th F#)
        Bars 5-6 (Beats 16..23): Am  (Root A, minor 3rd C, 5th E, minor 7th G - playful variations)
        Bars 7-8 (Beats 24..31): Em  (Root E, minor 3rd G, 5th B, minor 7th D - tension & resolution)
  - 4 Procedural Voice Layers:
      Voice 1 (Pendulum Escapement Bass, Gain 0.38):
        Precise staccato bassline mimicking a swinging mechanical pendulum escapement.
        Even steps provide solid fundamental grounding while odd steps emphasize harmonic
        pallet releases (tick-tock timbre alternation) with snappy exponential decay.
      Voice 2 (Music Box Lead, Gain 0.28):
        Intricate music box melody composed of struck metallic tine pings. Each note
        features physical inharmonic overtone clusters (fundamental + 2.756x overtone)
        with authentic dual-rate metallic damping that rings pleasantly across chords.
      Voice 3 (Clockwork Atmosphere, Gain 0.20):
        Syncopated clockwork gear clicks and ratchet rumbles produced by shaped micro-noise
        bursts on 16th-note ticks, alongside multi-click ratchet bursts at measure ends
        and a subtle low-frequency 54 Hz gear train rumble.
      Voice 4 (Pneumatic Steam Percussion, Gain 0.14):
        High-frequency steam release valve sizzle on measure transitions paired with
        a downward pitch-swept pneumatic pressure thud (120 Hz -> 45 Hz) on 2-bar cadences.
  - Master Clamping:
      Master mix saturated through hyperbolic tangent and clamped strictly to [-27000, 27000]
      in signed 16-bit mono PCM, leaving ample digital headroom.

Direct C++ Raylib Translation (raylib.h):
  struct ClockworkWorkshopBGM {
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
BPM = 100.0

# 8 Bars of 4/4 time at 100.0 BPM = exactly 32 beats
TOTAL_BEATS = 32
SECONDS_PER_BEAT = 60.0 / BPM
LOOP_DURATION_SECONDS = TOTAL_BEATS * SECONDS_PER_BEAT  # 19.200 seconds

# Exact loop sample count: round(44100 * 32 * 60 / 100.0) = 846,720 samples
TOTAL_LOOP_SAMPLES = 846720
SAMPLES_PER_BEAT = 26460
SAMPLES_PER_8TH = 13230
SAMPLES_PER_16TH = 6615

# Harmonic progression metadata for UI and synthesis analysis
CHORD_NAMES = ["Am", "Am", "D", "D", "Am", "Am", "Em", "Em"]

# Voice 1: 64 Eighth-note bass frequencies (in Hz) across 8 bars in A Dorian
# Bars 1-2: Am | Bars 3-4: D major | Bars 5-6: Am | Bars 7-8: Em
BASS_STEPS = [
    # Bars 1-2: Am (Beats 0..7, 16 steps)
    55.00, 110.00,  82.41, 110.00,   65.41,  82.41,   55.00,  98.00,
    55.00, 110.00,  82.41, 110.00,   65.41,  73.42,   82.41,  98.00,
    # Bars 3-4: D (Beats 8..15, 16 steps)
    73.42, 110.00,  92.50,  73.42,  110.00, 130.81,   73.42,  92.50,
    73.42, 110.00,  92.50,  73.42,  130.81, 110.00,   92.50,  82.41,
    # Bars 5-6: Am (Beats 16..23, 16 steps)
    55.00, 110.00,  65.41,  82.41,   98.00, 110.00,   82.41,  65.41,
    55.00, 110.00,  82.41, 110.00,   65.41,  73.42,   82.41,  98.00,
    # Bars 7-8: Em (Beats 24..31, 16 steps)
    82.41, 123.47,  98.00,  82.41,  123.47, 146.83,   82.41,  98.00,
    82.41, 123.47, 146.83, 123.47,   98.00,  82.41,   82.41,  49.00,
]

# Voice 2: Intricate music box melody: (start_beat, duration_beats, frequency_hz)
# Mode: A Dorian over progression Am (bars 1-2) -> D (bars 3-4) -> Am (bars 5-6) -> Em (bars 7-8)
MUSIC_BOX_NOTES = [
    # Bars 1-2 (Am): Curious tinkerer opening motif
    (0.0, 0.75, 659.25),   # E5
    (0.75, 0.75, 880.00),  # A5
    (1.5, 0.5, 1046.50),   # C6
    (2.0, 1.0, 987.77),    # B5
    (3.0, 0.5, 880.00),    # A5
    (3.5, 0.5, 783.99),    # G5
    (4.0, 1.0, 880.00),    # A5
    (5.0, 0.5, 1046.50),   # C6
    (5.5, 0.5, 1174.66),   # D6
    (6.0, 1.5, 1318.51),   # E6
    (7.5, 0.5, 1174.66),   # D6

    # Bars 3-4 (D): Bright Dorian F# introduces mechanical invention
    (8.0, 0.75, 739.99),   # F#5
    (8.75, 0.75, 880.00),  # A5
    (9.5, 0.5, 1174.66),   # D6
    (10.0, 1.0, 1046.50),  # C6
    (11.0, 0.5, 987.77),   # B5
    (11.5, 0.5, 739.99),   # F#5
    (12.0, 1.0, 1174.66),  # D6
    (13.0, 0.5, 987.77),   # B5
    (13.5, 0.5, 880.00),   # A5
    (14.0, 1.0, 739.99),   # F#5
    (15.0, 0.5, 659.25),   # E5
    (15.5, 0.5, 587.33),   # D5

    # Bars 5-6 (Am): Intricate rapid tinkerer flourishes
    (16.0, 0.5, 523.25),   # C5
    (16.5, 0.5, 659.25),   # E5
    (17.0, 0.5, 880.00),   # A5
    (17.5, 0.5, 1046.50),  # C6
    (18.0, 1.0, 1318.51),  # E6
    (19.0, 0.5, 1174.66),  # D6
    (19.5, 0.5, 1046.50),  # C6
    (20.0, 0.5, 987.77),   # B5
    (20.5, 0.5, 880.00),   # A5
    (21.0, 0.5, 783.99),   # G5
    (21.5, 0.5, 659.25),   # E5
    (22.0, 1.5, 880.00),   # A5
    (23.5, 0.5, 987.77),   # B5

    # Bars 7-8 (Em): Clockwork winding down and rhythmic resolution to tonic A
    (24.0, 0.75, 783.99),  # G5
    (24.75, 0.75, 987.77), # B5
    (25.5, 0.5, 1318.51),  # E6
    (26.0, 1.0, 1174.66),  # D6
    (27.0, 0.5, 987.77),   # B5
    (27.5, 0.5, 783.99),   # G5
    (28.0, 0.5, 659.25),   # E5
    (28.5, 0.5, 739.99),   # F#5
    (29.0, 0.5, 783.99),   # G5
    (29.5, 0.5, 987.77),   # B5
    (30.0, 0.5, 1046.50),  # C6
    (30.5, 0.5, 987.77),   # B5
    (31.0, 1.0, 880.00),   # A5 (resolves cleanly to tonic)
]

# 16th-note steps (0..127) where rapid ratchet bursts trigger
RATCHET_16TH_STEPS = {14, 28, 46, 60, 78, 92, 110, 124, 125, 126, 127}

# Module-level pinned buffer registry to protect against GC deallocation
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
def create_clockwork_workshop_bgm() -> Music:
    """
    Synthesizes the 8-bar 'Curious Clockwork Workshop' mechanical loop in RAM.
    Returns an initialized Raylib Music stream with looping enabled.
    """
    sin = math.sin
    cos = math.cos
    exp = math.exp
    tanh = math.tanh
    inv_sr = 1.0 / float(SAMPLE_RATE)
    pack_into = py_struct.pack_into

    # --------------------------------------------------------------------------
    # 1. Precalculate Music Box Polyphonic Lead Buffer (Voice 2)
    # --------------------------------------------------------------------------
    lead_buffer = [0.0] * TOTAL_LOOP_SAMPLES
    ring_samples = int(0.70 * SAMPLE_RATE)  # Ringing tine decay length

    for start_b, dur_b, note_freq in MUSIC_BOX_NOTES:
        s_start = int(start_b * SAMPLES_PER_BEAT)
        s_len = min(ring_samples, TOTAL_LOOP_SAMPLES - s_start)
        dphi = PI2 * note_freq * inv_sr
        dphi_ov = dphi * 2.756  # Inharmonic metallic chime overtone
        phi = 0.0
        phi_ov = 0.0
        for k in range(s_len):
            t = float(k) * inv_sr
            env_main = exp(-4.2 * t)
            env_ov = exp(-18.0 * t)
            val = (sin(phi) + 0.35 * sin(phi_ov) * env_ov) * env_main
            lead_buffer[s_start + k] += val
            phi += dphi
            phi_ov += dphi_ov

    # --------------------------------------------------------------------------
    # 2. Envelope Lookup Tables for Maximum Generation Throughput
    # --------------------------------------------------------------------------
    bass_env_table = [0.0] * SAMPLES_PER_8TH
    for s in range(SAMPLES_PER_8TH):
        t_s = float(s) * inv_sr
        bass_env_table[s] = exp(-11.5 * t_s)

    click_env_table = [0.0] * SAMPLES_PER_16TH
    for s in range(SAMPLES_PER_16TH):
        t_s = float(s) * inv_sr
        click_env_table[s] = exp(-120.0 * t_s)

    # Phase accumulators
    phase_bass = 0.0
    phase_rumble = 0.0
    phase_steam_thud = 0.0
    prev_noise_click = 0.0
    prev_noise_steam = 0.0

    dphi_rumble = PI2 * 54.0 * inv_sr

    # Preallocate PCM byte buffer
    pcm_buffer = bytearray(TOTAL_LOOP_SAMPLES * 2)

    # --------------------------------------------------------------------------
    # 3. Main Multi-Voice Synthesis Loop (846,720 Samples)
    # --------------------------------------------------------------------------
    for i in range(TOTAL_LOOP_SAMPLES):
        step_8th = i // SAMPLES_PER_8TH
        s_in_8th = i % SAMPLES_PER_8TH
        step_16th = i // SAMPLES_PER_16TH
        s_in_16th = i % SAMPLES_PER_16TH

        # ----------------------------------------------------------------------
        # Voice 1: Pendulum Escapement Bass (Gain 0.38)
        # Staccato bassline with alternating tick-tock harmonic emphasis
        # ----------------------------------------------------------------------
        f_bass = BASS_STEPS[step_8th]
        phase_bass += PI2 * f_bass * inv_sr
        harm_weight = 0.35 if (step_8th % 2 == 1) else 0.22
        bass_wave = sin(phase_bass) + harm_weight * sin(2.0 * phase_bass)
        v1 = 0.38 * bass_wave * bass_env_table[s_in_8th]

        # ----------------------------------------------------------------------
        # Voice 2: Music Box Lead (Gain 0.28)
        # Polyphonically pre-rendered metallic chime tines
        # ----------------------------------------------------------------------
        v2 = 0.28 * lead_buffer[i]

        # ----------------------------------------------------------------------
        # Voice 3: Clockwork Atmosphere (Gain 0.20)
        # 16th-note escapement click, syncopated ratchets & 54 Hz gear train rumble
        # ----------------------------------------------------------------------
        raw_n1 = random.random() * 2.0 - 1.0
        hp_n1 = raw_n1 - 0.70 * prev_noise_click
        prev_noise_click = raw_n1
        click_gain = 0.70 if (step_16th % 2 == 0) else 0.40
        click_sig = hp_n1 * click_env_table[s_in_16th] * click_gain

        # Ratchet burst mechanism (rapid micro-clicks on designated steps)
        ratchet_sig = 0.0
        if step_16th in RATCHET_16TH_STEPS:
            s_in_ratchet = i % 600
            t_r = float(s_in_ratchet) * inv_sr
            ratchet_sig = hp_n1 * exp(-150.0 * t_r) * 0.90

        # Continuous cog train rumble
        phase_rumble += dphi_rumble
        rumble = 0.15 * sin(phase_rumble) * (0.8 + 0.2 * sin(PI2 * 2.5 * float(i) * inv_sr))

        v3 = 0.20 * (click_sig + ratchet_sig + rumble)

        # ----------------------------------------------------------------------
        # Voice 4: Pneumatic Steam Release Percussion (Gain 0.14)
        # Steam valve hiss on measure transitions + pneumatic downbeat thud
        # ----------------------------------------------------------------------
        meas_sample = i % (4 * SAMPLES_PER_BEAT)
        t_steam = float(meas_sample) * inv_sr
        v4 = 0.0
        if t_steam < 0.40:
            raw_n2 = random.random() * 2.0 - 1.0
            hp_n2 = raw_n2 - 0.80 * prev_noise_steam
            prev_noise_steam = raw_n2
            steam_hiss = hp_n2 * exp(-6.5 * t_steam)

            # Heavy pneumatic anchor thud on 2-bar cadences (beats 0, 8, 16, 24)
            thud = 0.0
            if (i // (4 * SAMPLES_PER_BEAT)) % 2 == 0 and t_steam < 0.20:
                f_thud = 45.0 + 75.0 * exp(-20.0 * t_steam)
                phase_steam_thud += PI2 * f_thud * inv_sr
                thud = 0.75 * sin(phase_steam_thud) * exp(-14.0 * t_steam)
            v4 = 0.14 * (steam_hiss + thud)

        # ----------------------------------------------------------------------
        # Master Mix, Hyperbolic Tangent Saturation & Headroom Clamping
        # ----------------------------------------------------------------------
        mix = tanh((v1 + v2 + v3 + v4) * 1.25)

        # Seamless loop boundary micro-fade (256 samples click prevention)
        if i < 256:
            mix *= 0.5 * (1.0 - cos(math.pi * float(i) / 256.0))
        elif i > TOTAL_LOOP_SAMPLES - 256:
            mix *= 0.5 * (1.0 - cos(math.pi * float(TOTAL_LOOP_SAMPLES - 1 - i) / 256.0))

        # Clamp strictly to [-27000, 27000]
        pcm_int = int(mix * 27000.0)
        clamped_pcm = max(-27000, min(27000, pcm_int))
        pack_into('<h', pcm_buffer, i * 2, clamped_pcm)

    # Package in canonical 44-byte RIFF container and initialize streaming Music
    wav_bytes = pack_riff_wav_mono_16bit(SAMPLE_RATE, pcm_buffer)
    music = load_music_stream_from_memory(".wav", wav_bytes, len(wav_bytes))
    music.looping = True

    # Pin WAV buffer in memory to protect from Python GC while streaming
    _ACTIVE_BUFFERS[id(music)] = wav_bytes
    return music


# Standardized alias mappings for universal dynamic discovery
create_bgm = create_clockwork_workshop_bgm
generate_clockwork_workshop_track = create_clockwork_workshop_bgm
bgm_curious_clockwork_workshop = create_clockwork_workshop_bgm


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
    Interactive audition workbench allowing developers and students to examine
    and audition the Curious Clockwork Workshop BGM with real-time telemetry.
    """
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        init_window(
            self.screen_width,
            self.screen_height,
            "BGM Workbench - Curious Clockwork Workshop (assets/audio/BGM/curious/clockwork_workshop.py)"
        )
        set_target_fps(60)
        init_audio_device()

        self.music = create_clockwork_workshop_bgm()
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

        # Up/Down / Gamepad D-pad Up/Down: Volume (+/- 5%)
        if is_key_pressed(KEY_UP) or is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_UP):
            self.volume = min(1.0, self.volume + 0.05)
            set_music_volume(self.music, self.volume)
        elif is_key_pressed(KEY_DOWN) or is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_DOWN):
            self.volume = max(0.0, self.volume - 0.05)
            set_music_volume(self.music, self.volume)

        # Left/Right / Gamepad D-pad Left/Right: Pitch/Tempo (+/- 5%)
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
        clear_background(Color(18, 16, 22, 255))

        # Title Header (kept in left region x < 450, leaving top-bar x=450..980, y=14..48 clear)
        draw_text("PROCEDURAL BGM AUDITION WORKBENCH", 24, 18, 18, RAYWHITE)
        draw_text(
            "Asset: assets/audio/BGM/curious/clockwork_workshop.py | 100.0 BPM A Dorian Tinkerer Lab",
            24, 44, 12, Color(240, 190, 70, 255)
        )

        # ----------------------------------------------------------------------
        # LEFT COLUMN: Telemetry & Controls Info Cards
        # ----------------------------------------------------------------------
        panel_y = 74
        draw_rectangle(24, panel_y, 400, 260, Color(28, 24, 32, 255))
        draw_rectangle_lines(24, panel_y, 400, 260, Color(80, 65, 50, 255))
        draw_text("CLOCKWORK WORKSHOP TELEMETRY", 40, panel_y + 14, 14, Color(240, 190, 70, 255))
        draw_text("Tempo / Meter   : 100.0 BPM | 4/4 Time | 8 Bars", 40, panel_y + 40, 12, RAYWHITE)
        draw_text("Harmonic Mode   : A Dorian (A - B - C - D - E - F# - G)", 40, panel_y + 64, 12, RAYWHITE)
        draw_text("Progression     : Am (2b) -> D (2b) -> Am (2b) -> Em (2b)", 40, panel_y + 88, 12, LIGHTGRAY)
        draw_text("Loop Duration   : 19.20s (846,720 Samples)", 40, panel_y + 112, 12, LIGHTGRAY)
        draw_text("Voice 1 (Bass)  : Pendulum Escapement Staccato (Gain 0.38)", 40, panel_y + 136, 12, Color(220, 140, 80, 255))
        draw_text("Voice 2 (Lead)  : Music Box Metallic Sine Pings (Gain 0.28)", 40, panel_y + 160, 12, Color(255, 220, 100, 255))
        draw_text("Voice 3 (Atmo)  : Cogs, Ratchets & Micro-Noise Clicks (0.20)", 40, panel_y + 184, 12, Color(160, 200, 240, 255))
        draw_text("Voice 4 (Rhythm): Steam Release Valve & Pneumatic Thud (0.14)", 40, panel_y + 208, 12, Color(240, 120, 100, 255))
        draw_text("Saturation Head : Clamped strictly to [-27000, 27000]", 40, panel_y + 232, 11, GREEN)

        # Controls Card
        ctrl_y = panel_y + 276
        draw_rectangle(24, ctrl_y, 400, 230, Color(28, 24, 32, 255))
        draw_rectangle_lines(24, ctrl_y, 400, 230, Color(80, 65, 50, 255))
        draw_text("BGM CONTROLS", 40, ctrl_y + 14, 14, Color(255, 200, 80, 255))
        draw_text("- [Space] / [M] / Gamepad (A)  : Play / Pause Stream", 40, ctrl_y + 40, 12, RAYWHITE)
        draw_text("- [Up] / [Down] / Gamepad D-pad: Volume (+/- 5%)", 40, ctrl_y + 64, 12, RAYWHITE)
        draw_text("- [Left] / [Right] / D-pad L/R : Tempo / Pitch (+/- 5%)", 40, ctrl_y + 88, 12, RAYWHITE)
        draw_text("- [R] / Gamepad Start          : Reset Loop to Beginning", 40, ctrl_y + 112, 12, RAYWHITE)
        draw_text(
            f"Playback State  : {'PLAYING (Looping)' if self.is_playing else 'PAUSED'}",
            40, ctrl_y + 142, 13, GREEN if self.is_playing else RED
        )
        draw_text(f"Master Volume   : {int(self.volume * 100)}%", 40, ctrl_y + 166, 13, GOLD)
        draw_text(f"Tempo / Pitch   : {self.pitch:.2f}x", 40, ctrl_y + 190, 13, GOLD)

        # ----------------------------------------------------------------------
        # RIGHT COLUMN: Visualizer, Sequencer Grid & Animated Clockwork Mechanisms
        # Top-bar safe area (x=450..980, y=14..48) is strictly avoided!
        # ----------------------------------------------------------------------
        vis_x = 450
        vis_y = 74
        vis_w = 806
        vis_h = 620
        draw_rectangle(vis_x, vis_y, vis_w, vis_h, Color(22, 20, 28, 255))
        draw_rectangle_lines(vis_x, vis_y, vis_w, vis_h, Color(75, 60, 50, 255))
        draw_text(
            "WORKBENCH SEQUENCER & CLOCKWORK MECHANISMS",
            vis_x + 20, vis_y + 16, 15, Color(240, 190, 70, 255)
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

            # Harmonic chord color coding
            if bar_idx in (0, 1, 4, 5):   # Am bars (Warm copper)
                base_col = Color(55, 38, 24, 255) if (s % 4 == 0) else Color(36, 25, 16, 255)
            elif bar_idx in (2, 3):        # D bars (Bright golden brass)
                base_col = Color(65, 50, 20, 255) if (s % 4 == 0) else Color(42, 32, 14, 255)
            else:                          # Em bars (Deep steel iron)
                base_col = Color(40, 36, 48, 255) if (s % 4 == 0) else Color(26, 24, 34, 255)

            box_col = Color(255, 215, 80, 255) if is_active else base_col
            draw_rectangle(bx, grid_y, step_w - 2, 32, box_col)
            if is_active:
                draw_rectangle_lines(bx, grid_y, step_w - 2, 32, RAYWHITE)

        draw_text(
            f"Sequencer Beat: {current_beat + 1:02d} / 32 | Bar: {current_bar + 1} / 8 | Chord: {current_chord} | Time: {time_played:.2f}s / {time_total:.2f}s",
            vis_x + 20, grid_y + 42, 12, LIGHTGRAY
        )

        # Loop Progress Bar
        bar_y = vis_y + 128
        draw_rectangle(vis_x + 20, bar_y, vis_w - 40, 12, Color(30, 26, 36, 255))
        fill_w = int(loop_progress * (vis_w - 40))
        draw_rectangle(vis_x + 20, bar_y, fill_w, 12, Color(240, 180, 60, 255))
        draw_rectangle_lines(vis_x + 20, bar_y, vis_w - 40, 12, Color(75, 60, 50, 255))

        # ----------------------------------------------------------------------
        # 4 Animated Procedural Clockwork Mechanisms
        # ----------------------------------------------------------------------
        mech_y = vis_y + 160
        draw_text(
            "MECHANICAL LABORATORY RIG (PROCEDURAL LAYER VISUALIZER)",
            vis_x + 20, mech_y, 13, Color(255, 200, 80, 255)
        )

        cards = [
            ("ESCAPEMENT BASS", "Pendulum & Pallet", Color(220, 140, 80, 255)),
            ("MUSIC BOX LEAD", "Cylinder & Plucked Tines", Color(255, 220, 100, 255)),
            ("GEAR ATMOSPHERE", "Interlocking Cog Train", Color(160, 200, 240, 255)),
            ("STEAM PERCUSSION", "Pressure Gauge Valve", Color(240, 120, 100, 255)),
        ]

        card_w = (vis_w - 60) // 4
        for c_idx, (c_title, c_sub, c_col) in enumerate(cards):
            cx = vis_x + 20 + c_idx * (card_w + 7)
            cy = mech_y + 26
            ch = 150

            # Card background
            draw_rectangle(cx, cy, card_w, ch, Color(30, 26, 36, 255))
            draw_rectangle_lines(cx, cy, card_w, ch, Color(70, 55, 45, 255))

            # Render custom procedural animation per mechanism
            if c_idx == 0:
                # 1. Escapement Pendulum: Oscillating pendulum arm & bob
                pivot_x = cx + card_w // 2
                pivot_y = cy + 18
                pend_ang = math.sin(time_played * math.pi * (100.0 / 60.0)) * 0.42 if self.is_playing else 0.0
                arm_len = 50.0
                bob_x = pivot_x + int(arm_len * math.sin(pend_ang))
                bob_y = pivot_y + int(arm_len * math.cos(pend_ang))

                # Draw anchor escapement fork
                draw_line(pivot_x - 12, pivot_y - 4, pivot_x + 12, pivot_y - 4, Color(160, 140, 120, 255))
                draw_line(pivot_x, pivot_y, bob_x, bob_y, Color(200, 180, 140, 255))
                draw_circle(bob_x, bob_y, 8, c_col)
                draw_circle_lines(bob_x, bob_y, 8, RAYWHITE)

            elif c_idx == 1:
                # 2. Music Box Cylinder: Rotating drum with plucked comb tines
                cyl_x = cx + 22
                cyl_y = cy + 24
                cyl_w = card_w - 44
                draw_rectangle(cyl_x, cyl_y, cyl_w, 36, Color(55, 42, 28, 255))
                draw_rectangle_lines(cyl_x, cyl_y, cyl_w, 36, Color(120, 95, 60, 255))

                # Pins moving across cylinder
                pin_offset = int((time_played * 40.0) % cyl_w) if self.is_playing else 0
                for px_rel in (10, 30, 55, 80, 110):
                    px_abs = cyl_x + ((px_rel + pin_offset) % cyl_w)
                    draw_circle(px_abs, cyl_y + 18, 3, Color(255, 230, 120, 255))

                # 6 Comb steel tines
                for tine_i in range(6):
                    tx = cyl_x + 8 + tine_i * ((cyl_w - 16) // 5)
                    tine_lit = (current_beat % 6 == tine_i) and self.is_playing
                    t_col = c_col if tine_lit else Color(100, 90, 80, 255)
                    draw_line(tx, cyl_y + 36, tx, cyl_y + 54, t_col)

            elif c_idx == 2:
                # 3. Cog Train: Two meshed rotating brass gears
                g1_x = cx + card_w // 2 - 20
                g1_y = cy + 42
                g2_x = cx + card_w // 2 + 22
                g2_y = cy + 50

                rot = time_played * 2.2 if self.is_playing else 0.0
                draw_circle_lines(g1_x, g1_y, 20, c_col)
                draw_circle_lines(g2_x, g2_y, 14, Color(140, 180, 220, 255))

                # Radial gear teeth lines
                for t_ang in range(8):
                    ang_rad = rot + t_ang * (PI2 / 8.0)
                    tx1 = g1_x + int(16 * math.cos(ang_rad))
                    ty1 = g1_y + int(16 * math.sin(ang_rad))
                    tx2 = g1_x + int(24 * math.cos(ang_rad))
                    ty2 = g1_y + int(24 * math.sin(ang_rad))
                    draw_line(tx1, ty1, tx2, ty2, c_col)

                draw_circle(g1_x, g1_y, 4, Color(80, 70, 60, 255))
                draw_circle(g2_x, g2_y, 3, Color(80, 70, 60, 255))

            else:
                # 4. Steam Pressure Gauge: Dial with jumping needle
                gauge_x = cx + card_w // 2
                gauge_y = cy + 45
                gauge_r = 28
                draw_circle(gauge_x, gauge_y, gauge_r, Color(40, 32, 28, 255))
                draw_circle_lines(gauge_x, gauge_y, gauge_r, c_col)

                # Needle jumps on measure transitions (beat % 4 == 0)
                is_steam = (current_beat % 4 == 0) and self.is_playing
                needle_angle = -0.4 if is_steam else -2.2
                nx = gauge_x + int((gauge_r - 6) * math.cos(needle_angle))
                ny = gauge_y + int((gauge_r - 6) * math.sin(needle_angle))
                draw_line(gauge_x, gauge_y, nx, ny, RED if is_steam else Color(220, 200, 160, 255))
                draw_circle(gauge_x, gauge_y, 3, RAYWHITE)

            # Labels
            draw_text(c_title, cx + 8, cy + 104, 11, c_col)
            draw_text(c_sub, cx + 8, cy + 124, 10, LIGHTGRAY)

        # ----------------------------------------------------------------------
        # Voice Layer Telemetry Readout Panels
        # ----------------------------------------------------------------------
        meter_y = mech_y + 196
        draw_rectangle(vis_x + 20, meter_y, vis_w - 40, 150, Color(28, 24, 32, 255))
        draw_rectangle_lines(vis_x + 20, meter_y, vis_w - 40, 150, Color(75, 60, 50, 255))
        draw_text("LAYER OSCILLATOR STATUS", vis_x + 36, meter_y + 12, 13, Color(240, 190, 70, 255))

        step_8th = min(63, int((loop_progress * TOTAL_BEATS) * 2.0))
        cur_bass_f = BASS_STEPS[step_8th]
        draw_text(
            f"[Voice 1: Escapement Bass]  Target: {cur_bass_f:.1f} Hz | Staccato Decay: k=11.5 | Gain: 0.38",
            vis_x + 36, meter_y + 36, 12, Color(220, 140, 80, 255)
        )

        lead_idx = min(len(MUSIC_BOX_NOTES) - 1, int(loop_progress * len(MUSIC_BOX_NOTES)))
        lead_freq = MUSIC_BOX_NOTES[lead_idx][2]
        draw_text(
            f"[Voice 2: Music Box Lead]   Active Tine: {lead_freq:.1f} Hz | Overtone: 2.756x | Gain: 0.28",
            vis_x + 36, meter_y + 60, 12, Color(255, 220, 100, 255)
        )

        ratchet_state = "ENGAGED (Click Burst)" if ((int(loop_progress * 128) % 16) >= 14) else "STEADY ESCAPEMENT (16th Ticks)"
        draw_text(
            f"[Voice 3: Clock Atmosphere] Ratchet State: {ratchet_state} | 54 Hz Cog Rumble | Gain: 0.20",
            vis_x + 36, meter_y + 84, 12, Color(160, 200, 240, 255)
        )

        steam_state = "VALVE OPEN (Pneumatic Sizzle & Thud)" if (current_beat % 4 == 0) else "PRESSURE CHARGING"
        draw_text(
            f"[Voice 4: Steam Percussion] Exhaust State: {steam_state} | Gain: 0.14",
            vis_x + 36, meter_y + 108, 12, Color(240, 120, 100, 255)
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
