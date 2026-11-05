# -*- coding: utf-8 -*-
"""
Procedural Laser Sound Effect (SFX) Synthesizer
================================================
Type             : Procedural Audio SFX (Sound)
Target File      : assets/audio/SFX/combat/laser.py
Waveforms Used   : Downward exponential sine sweep with square-wave harmonic grit
Category         : Combat & Weapons

Problem Solved:
  Eliminates external .wav/.mp3 dependencies by synthesizing a retro arcade laser
  blast entirely from mathematical waveforms into an in-memory 16-bit PCM buffer,
  loading directly into a Raylib Sound struct.

Waveform Theory & Mathematical Rationale:
  - The carrier frequency dives exponentially from 880 Hz (A5) down to 220 Hz (A3)
    over 120 milliseconds: f(t) = 880.0 * exp(-3.0 * t / duration).
  - Exponential pitch dives evoke rapid energy discharge (classic sci-fi blaster).
  - Mixing a pure sine wave (70%) with a hard-clipped square wave (30%) injects
    odd-harmonic grit without harsh digital clipping.
  - An exponential amplitude envelope (exp(-6.0 * progress)) guarantees a snappy
    initial attack that decays smoothly to zero with no boundary clicks.

Direct C++ Raylib Translation (raylib.h):
  struct LaserSFX {
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

import sys
import os
import math
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
# AUDIO CONSTANTS (Palette-Free Synthesis Parameters)
# ==============================================================================
SAMPLE_RATE = 44100
PI2 = 2.0 * math.pi

DEFAULT_DURATION = 0.12        # 120 ms
START_FREQUENCY = 880.0        # Hz (A5)
END_FREQUENCY = 220.0          # Hz (A3)
DECAY_RATE = 6.0               # Exponential envelope decay factor


# ==============================================================================
# IN-MEMORY RIFF/WAV PACKER (C++ 44-Byte Header Equivalent)
# ==============================================================================
def pack_riff_wav_mono_16bit(sample_rate: int, raw_samples: list) -> bytes:
    """
    Packs signed 16-bit PCM integer samples (-32767 to 32767) into an in-memory
    canonical 44-byte RIFF/WAVE container.
    
    C++ Architecture Note:
      Mirrors writing a packed 44-byte header struct into memory before passing
      the contiguous byte buffer directly to Raylib's LoadWaveFromMemory().
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
# CORE PROCEDURAL SFX SYNTHESIS FUNCTION
# ==============================================================================
def create_laser_sfx(
    duration: float = DEFAULT_DURATION,
    start_freq: float = START_FREQUENCY,
    end_freq: float = END_FREQUENCY
) -> Sound:
    """
    Synthesizes a downward exponential laser blast into a Raylib Sound struct.
    Returns a ready-to-play Sound handle resident in audio memory.
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    phase = 0.0

    for i in range(total_samples):
        # Normalized time progress (0.0 to 1.0)
        progress = float(i) / float(total_samples)

        # Exponential pitch glide downward from start_freq to end_freq
        decay_factor = math.log(end_freq / start_freq)
        current_freq = start_freq * math.exp(decay_factor * progress)
        phase += PI2 * current_freq / SAMPLE_RATE

        # Exponential decay envelope (avoids boundary clicks)
        envelope = math.exp(-DECAY_RATE * progress)

        # Mix sine wave carrier (70%) with square wave odd-harmonics (30%)
        sine_val = math.sin(phase)
        square_val = 1.0 if sine_val > 0.0 else -1.0
        mixed = (0.70 * sine_val) + (0.30 * square_val)

        # Scale to signed 16-bit amplitude range (peak ~26,000 to prevent clipping)
        sample_16bit = mixed * envelope * 26000.0
        samples.append(sample_16bit)

    wav_bytes = pack_riff_wav_mono_16bit(SAMPLE_RATE, samples)
    wave = load_wave_from_memory(".wav", wav_bytes, len(wav_bytes))
    sound = load_sound_from_wave(wave)
    unload_wave(wave)  # Free CPU RAM Wave container; Sound retains audio device handle
    return sound


# Standardized alias mapping for dynamic discovery
create_sfx = create_laser_sfx


# ==============================================================================
# STANDARDIZED PLAYBACK CONTROL METHODS
# ==============================================================================
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
# STANDALONE AUDITION WORKBENCH & AUTOMATED SMOKE TEST
# ==============================================================================
class SFXAuditionApp:
    """
    Interactive sound previewer workbench allowing developers and students
    to audition the laser sound effect with live parameter controls and telemetry.
    """
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        init_window(self.screen_width, self.screen_height, "SFX Workbench - Laser (assets/audio/SFX/combat/laser.py)")
        set_target_fps(60)
        init_audio_device()

        self.sound = create_laser_sfx()
        self.trigger_pulse = 0.0
        self.volume = 0.85
        self.pitch = 1.0
        self.trigger_count = 0

    def trigger(self):
        """Triggers sound playback with current pitch/volume and animates visualizer."""
        play_sfx(self.sound, self.volume, self.pitch)
        self.trigger_pulse = 1.0
        self.trigger_count += 1

    def update(self):
        dt = min(get_frame_time(), 0.05)
        if self.trigger_pulse > 0.0:
            self.trigger_pulse = max(0.0, self.trigger_pulse - dt * 3.5)

        # Trigger inputs: Space, Left Click, or Gamepad Face A / RT
        if is_key_pressed(KEY_SPACE) or is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            self.trigger()

        # Pitch adjustments: Up/Down arrows
        if is_key_pressed(KEY_UP):
            self.pitch = min(2.0, self.pitch + 0.1)
        elif is_key_pressed(KEY_DOWN):
            self.pitch = max(0.5, self.pitch - 0.1)

        # Reset pitch
        if is_key_pressed(KEY_R):
            self.pitch = 1.0
            self.volume = 0.85

    def draw(self):
        begin_drawing()
        clear_background(Color(12, 16, 26, 255))

        # Header (keeps top-bar region x=450..980 clear for ui settings)
        draw_text("PROCEDURAL SFX AUDITION WORKBENCH", 24, 20, 20, RAYWHITE)
        draw_text("Asset: assets/audio/SFX/combat/laser.py | Waveform: Exponential Sine+Square Sweep", 24, 50, 13, SKYBLUE)

        # Control Instructions Card
        panel_y = 100
        draw_rectangle(24, panel_y, 400, 180, Color(20, 26, 42, 255))
        draw_rectangle_lines(24, panel_y, 400, 180, Color(45, 60, 95, 255))
        draw_text("CONTROLS & SHORTCUTS", 40, panel_y + 14, 15, YELLOW)
        draw_text("- [Space] / [Left Click] : Trigger Laser SFX", 40, panel_y + 44, 13, RAYWHITE)
        draw_text("- [Up] / [Down] Arrows   : Adjust Pitch (+/- 0.1)", 40, panel_y + 70, 13, RAYWHITE)
        draw_text("- [R] Key                : Reset Pitch & Volume", 40, panel_y + 96, 13, RAYWHITE)
        draw_text(f"Current Pitch   : {self.pitch:.1f}x", 40, panel_y + 124, 13, GREEN)
        draw_text(f"Total Triggers  : {self.trigger_count}", 40, panel_y + 146, 13, LIGHTGRAY)

        # Real-time Visualizer Panel
        vis_x = 450
        vis_y = 100
        vis_w = 800
        vis_h = 360
        draw_rectangle(vis_x, vis_y, vis_w, vis_h, Color(16, 22, 34, 255))
        draw_rectangle_lines(vis_x, vis_y, vis_w, vis_h, Color(45, 60, 95, 255))
        draw_text("AUDIO OUTPUT & AMPLITUDE MONITOR", vis_x + 20, vis_y + 16, 15, SKYBLUE)

        # Center line
        mid_y = vis_y + (vis_h // 2)
        draw_line(vis_x + 20, mid_y, vis_x + vis_w - 20, mid_y, Color(35, 45, 65, 255))

        # Dynamic amplitude pulse bar
        meter_w = int(self.trigger_pulse * (vis_w - 40))
        glow_r = int(255 * self.trigger_pulse)
        glow_g = int(120 * self.trigger_pulse)
        draw_rectangle(vis_x + 20, mid_y - 20, meter_w, 40, Color(glow_r, glow_g, 220, 220))
        draw_rectangle_lines(vis_x + 20, mid_y - 20, vis_w - 40, 40, Color(60, 80, 120, 255))

        # Simulated frequency sweep visualization curve
        prev_pt_x = vis_x + 20
        prev_pt_y = mid_y
        steps = 64
        for s in range(1, steps + 1):
            t = float(s) / float(steps)
            pt_x = vis_x + 20 + int(t * (vis_w - 40))
            wave_amp = math.sin(t * 24.0 * self.pitch) * math.exp(-3.0 * t) * self.trigger_pulse * 90.0
            pt_y = int(mid_y - wave_amp)
            draw_line(prev_pt_x, prev_pt_y, pt_x, pt_y, Color(0, 220, 255, 240))
            prev_pt_x = pt_x
            prev_pt_y = pt_y

        # Global Top-Bar Integration
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)
        end_drawing()

    def run(self, smoke_test: bool = False):
        frame_count = 0
        if smoke_test:
            # Trigger once to verify audio device synthesis and playback
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

