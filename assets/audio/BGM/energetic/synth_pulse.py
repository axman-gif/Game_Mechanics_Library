# -*- coding: utf-8 -*-
"""
Procedural Background Music (BGM) Synthesizer - Synth Pulse
============================================================
Type             : Procedural Audio BGM (Music Stream)
Target File      : assets/audio/BGM/energetic/synth_pulse.py
Waveforms Used   : Algorithmic triangle bass, modulated square lead, shaped noise hi-hats
Category         : Interactive BGM Soundtracks

Problem Solved:
  Eliminates bulky soundtrack audio files by algorithmically composing multi-layer,
  looping background music purely in RAM using mathematical waveforms. Streamed
  in small buffer chunks via Raylib's Music struct for minimal memory footprint.

Musical Theory & Mathematical Rationale:
  - Tempo: 120 Beats Per Minute (BPM).
  - Clock Timing:
      Samples per beat       = (SAMPLE_RATE * 60) / 120 = 22,050 samples (0.50s)
      Samples per 16th step  = (SAMPLE_RATE * 15) / 120 = 5,512 samples (0.125s)
  - Scale: A-minor pentatonic (A, C, D, E, G).
      Bass frequencies : A2 (110.0 Hz), C3 (130.81 Hz), D3 (146.83 Hz), E3 (164.81 Hz)
      Lead frequencies : A3 (220.0 Hz), C4 (261.63 Hz), D4 (293.66 Hz), E4 (329.63 Hz),
                         G4 (392.0 Hz), A4 (440.0 Hz), C5 (523.25 Hz), E5 (659.25 Hz)
  - Rhythm Sequencing:
      Bass voice   : Sustained triangle wave changing pitch every quarter note (4 steps).
      Lead voice   : Melodic 16th-note square-wave arpeggio with sharp ADSR decay.
      Percussion   : White-noise bursts on odd 16th steps simulating an electronic hi-hat.
  - Seamless Loop Points:
      Total duration is strictly 4.0 seconds (2 bars of 4/4 time). The sample count is an
      exact integer multiple of measure lengths, ensuring the end loops back to index 0
      with continuous phase and zero audio pops.

Direct C++ Raylib Translation (raylib.h):
  struct SynthPulseBGM {
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
BPM = 120.0

# 2 Bars at 120 BPM in 4/4 time = 4.0 seconds total loop
LOOP_DURATION_SECONDS = 4.0
TOTAL_LOOP_SAMPLES = int(SAMPLE_RATE * LOOP_DURATION_SECONDS)

# Step sequencer timing: 16th note steps (16 steps per bar * 2 bars = 32 steps)
TOTAL_STEPS = 32
SAMPLES_PER_STEP = TOTAL_LOOP_SAMPLES // TOTAL_STEPS
STEP_DURATION_SEC = float(SAMPLES_PER_STEP) / float(SAMPLE_RATE)

# Pitch tables (frequencies in Hz)
BASS_NOTES = [110.0, 130.81, 146.83, 164.81]  # A2, C3, D3, E3
LEAD_NOTES = [
    220.00, 261.63, 293.66, 329.63,
    392.00, 440.00, 523.25, 659.25
]

# Arpeggio sequence indices mapping into LEAD_NOTES (32-step sequence)
LEAD_SEQUENCE = [
    0, 2, 4, 5, 4, 2, 1, 3,
    0, 2, 4, 7, 5, 4, 2, 1,
    0, 3, 5, 6, 5, 3, 2, 4,
    1, 2, 4, 5, 7, 5, 4, 2
]


# ==============================================================================
# IN-MEMORY RIFF/WAV PACKER (C++ 44-Byte Header Equivalent)
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
# CORE PROCEDURAL BGM SYNTHESIS FUNCTION
# ==============================================================================
def create_synth_pulse_bgm() -> Music:
    """
    Algorithmically synthesizes a 2-bar looping electronic music track in RAM.
    Returns a streaming Raylib Music struct with looping enabled.
    """
    samples = []
    phase_bass = 0.0
    phase_lead = 0.0

    for i in range(TOTAL_LOOP_SAMPLES):
        step_idx = (i // SAMPLES_PER_STEP) % TOTAL_STEPS
        step_sample = i % SAMPLES_PER_STEP
        step_t = float(step_sample) / float(SAMPLE_RATE)
        step_progress = step_t / STEP_DURATION_SEC

        # ----------------------------------------------------------------------
        # Voice 1: Bassline (Triangle wave, changes pitch every 4 steps = quarter note)
        # ----------------------------------------------------------------------
        bass_note_idx = (step_idx // 4) % len(BASS_NOTES)
        bass_freq = BASS_NOTES[bass_note_idx]
        phase_bass += PI2 * bass_freq / SAMPLE_RATE

        # Mathematical triangle wave: (2 / pi) * asin(sin(phase))
        tri_bass = (2.0 / math.pi) * math.asin(math.sin(phase_bass))
        bass_envelope = math.exp(-2.5 * (step_sample / (SAMPLES_PER_STEP * 4)))
        bass_amp = tri_bass * bass_envelope * 0.45

        # ----------------------------------------------------------------------
        # Voice 2: Lead Pulse Arpeggio (Snappy square wave, changes every 16th step)
        # ----------------------------------------------------------------------
        lead_note_idx = LEAD_SEQUENCE[step_idx]
        lead_freq = LEAD_NOTES[lead_note_idx]
        phase_lead += PI2 * lead_freq / SAMPLE_RATE

        sq_lead = 1.0 if math.sin(phase_lead) > 0.0 else -1.0
        lead_envelope = math.exp(-6.5 * step_progress)
        lead_amp = sq_lead * lead_envelope * 0.25

        # ----------------------------------------------------------------------
        # Voice 3: Percussion Hi-Hat (Filtered white noise burst on every 2nd step)
        # ----------------------------------------------------------------------
        hat_amp = 0.0
        if step_idx % 2 == 1:
            raw_noise = random.random() * 2.0 - 1.0
            hat_env = math.exp(-24.0 * step_progress)
            hat_amp = raw_noise * hat_env * 0.15

        # ----------------------------------------------------------------------
        # Master Mix & 16-bit PCM Scaling
        # ----------------------------------------------------------------------
        master_mix = bass_amp + lead_amp + hat_amp
        sample_16bit = master_mix * 24000.0
        samples.append(sample_16bit)

    wav_bytes = pack_riff_wav_mono_16bit(SAMPLE_RATE, samples)
    music = load_music_stream_from_memory(".wav", wav_bytes, len(wav_bytes))
    music.looping = True  # Default to looping indefinitely
    return music


# Standardized alias mapping for dynamic discovery
create_bgm = create_synth_pulse_bgm


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
        init_window(self.screen_width, self.screen_height, "BGM Workbench - Synth Pulse (assets/audio/BGM/energetic/synth_pulse.py)")
        set_target_fps(60)
        init_audio_device()

        self.music = create_synth_pulse_bgm()
        self.volume = 0.70
        self.pitch = 1.0
        self.is_playing = False
        self.beat_anim = 0.0

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

        # 1. CRITICAL: Feed audio stream buffer every frame
        if self.is_playing:
            update_bgm(self.music)

        # Beat animation pulse
        if self.beat_anim > 0.0:
            self.beat_anim = max(0.0, self.beat_anim - dt * 2.5)

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
        begin_drawing()
        clear_background(Color(12, 16, 26, 255))

        # Title Header (keeps safe top region x=450..980 clear for dropdowns)
        draw_text("PROCEDURAL BGM AUDITION WORKBENCH", 24, 20, 20, RAYWHITE)
        draw_text("Asset: assets/audio/BGM/synth_pulse.py | 120 BPM A-Minor Pentatonic Arpeggio", 24, 50, 13, ORANGE)

        # Control Info Card
        panel_y = 100
        draw_rectangle(24, panel_y, 400, 220, Color(20, 26, 42, 255))
        draw_rectangle_lines(24, panel_y, 400, 220, Color(45, 60, 95, 255))
        draw_text("BGM CONTROLS", 40, panel_y + 14, 15, YELLOW)
        draw_text("- [Space] / [M]          : Play / Pause Stream", 40, panel_y + 44, 13, RAYWHITE)
        draw_text("- [Up] / [Down] Arrows   : Volume (+/- 5%)", 40, panel_y + 70, 13, RAYWHITE)
        draw_text("- [Left] / [Right] Arrows: Tempo / Pitch (+/- 5%)", 40, panel_y + 96, 13, RAYWHITE)
        draw_text(f"Playback State  : {'PLAYING (Looping)' if self.is_playing else 'PAUSED'}", 
                  40, panel_y + 130, 13, GREEN if self.is_playing else RED)
        draw_text(f"Volume          : {int(self.volume * 100)}%", 40, panel_y + 154, 13, SKYBLUE)
        draw_text(f"Tempo / Pitch   : {self.pitch:.2f}x", 40, panel_y + 178, 13, SKYBLUE)

        # Real-time Stream Output Visualizer
        vis_x = 450
        vis_y = 100
        vis_w = 800
        vis_h = 360
        draw_rectangle(vis_x, vis_y, vis_w, vis_h, Color(16, 22, 34, 255))
        draw_rectangle_lines(vis_x, vis_y, vis_w, vis_h, Color(45, 60, 95, 255))
        draw_text("STREAM BUFFER & MULTI-VOICE RHYTHM MONITOR", vis_x + 20, vis_y + 16, 15, ORANGE)

        # Step Sequencer Activity Grid (32 Steps)
        time_played = get_music_time_played(self.music)
        time_total = get_music_time_length(self.music)
        loop_progress = (time_played / time_total) if time_total > 0.0 else 0.0
        current_step = int(loop_progress * TOTAL_STEPS) % TOTAL_STEPS

        grid_y = vis_y + 60
        step_w = (vis_w - 40) // TOTAL_STEPS
        for s in range(TOTAL_STEPS):
            bx = vis_x + 20 + (s * step_w)
            is_cur = (s == current_step) and self.is_playing
            box_col = ORANGE if is_cur else (Color(40, 55, 80, 255) if s % 4 == 0 else Color(24, 32, 48, 255))
            draw_rectangle(bx, grid_y, step_w - 2, 36, box_col)

        draw_text(f"Sequencer Step: {current_step + 1} / {TOTAL_STEPS} | Loop Time: {time_played:.2f}s / {time_total:.2f}s", 
                  vis_x + 20, grid_y + 48, 13, LIGHTGRAY)

        # Loop Progress Bar
        bar_y = vis_y + 160
        draw_rectangle(vis_x + 20, bar_y, vis_w - 40, 16, Color(24, 30, 45, 255))
        fill_w = int(loop_progress * (vis_w - 40))
        draw_rectangle(vis_x + 20, bar_y, fill_w, 16, SKYBLUE)
        draw_rectangle_lines(vis_x + 20, bar_y, vis_w - 40, 16, Color(60, 80, 110, 255))

        # Bass/Lead/Percussion Channel Meters
        meter_y = vis_y + 210
        bass_active = (current_step // 4) % len(BASS_NOTES)
        draw_text(f"[Bass Voice]  Freq: {BASS_NOTES[bass_active]:.1f} Hz (Triangle)", vis_x + 20, meter_y, 13, Color(100, 200, 255, 255))
        lead_active = LEAD_SEQUENCE[current_step]
        draw_text(f"[Lead Voice]  Freq: {LEAD_NOTES[lead_active]:.1f} Hz (Square)", vis_x + 20, meter_y + 26, 13, Color(255, 200, 80, 255))
        hat_active = "TICK" if current_step % 2 == 1 else "-"
        draw_text(f"[Percussion]  Hi-Hat: {hat_active} (White Noise)", vis_x + 20, meter_y + 52, 13, Color(220, 220, 220, 255))

        # Top Bar Settings Dropdowns
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

