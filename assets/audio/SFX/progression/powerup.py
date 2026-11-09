# -*- coding: utf-8 -*-
"""
Procedural Powerup Sound Effect (SFX) Synthesizer
=================================================
Type             : Procedural Audio SFX (Sound)
Target File      : assets/audio/SFX/progression/powerup.py
Catalog ID       : sfx_prog_powerup
Waveforms Used   : Pure sine wave arpeggio with harmonic bell overtones, 5 Hz vibrato,
                   and biquad high-shelf boost
Category         : Progression & Economy

Problem Solved:
  Eliminates external audio file dependencies (.wav/.mp3) by synthesizing an uplifting,
  euphoric 4-tone powerup arpeggio directly in RAM into a 16-bit mono PCM buffer,
  packing it into an in-memory RIFF/WAVE container and loading it into a Raylib Sound struct.

Waveform Theory & Mathematical Rationale:
  - Triad to Octave Arpeggio: Plays an ascending 4-tone sequence:
      Note 0: E4 (329.63 Hz) at t = 0.000 s
      Note 1: G4 (392.00 Hz) at t = 0.035 s
      Note 2: B4 (493.88 Hz) at t = 0.070 s
      Note 3: E5 (659.25 Hz) at t = 0.105 s
    The note onsets progress in rapid 35ms steps across an E minor triad into octave
    resolution, creating a bright sense of positive reward and state elevation.
  - Cumulative Sustain & Shimmering Decay:
    Each note features a rapid 1ms linear attack (avoiding boundary pop clicks) and
    sustains into a blossoming chord. At t = 105ms (onset of E5), the sound enters an
    exponential decay tail (k = 4.0): envelope(t) = exp(-4.0 * (t - 0.105) / 0.085).
  - 5 Hz Vibrato on Final Resolution Note:
    The final note (E5) includes pitch vibrato at 5.0 Hz with a subtle 2% depth (about 35 cents),
    instilling a warm, crystalline shimmer in the sustained resolution.
  - Harmonic Bell Overtones:
    Layered with the fundamental sine wave are subtle bell harmonics at 2x (octave, 18%),
    3x (octave+fifth, 8%), and 4.2x (high sparkle mode, 4%) to evoke a crystalline chime.
  - High-Shelf Boost (2 kHz, +4 dB):
    Filtered through an Audio EQ Cookbook biquad high-shelf filter to accentuate high-frequency
    sparkle without harshness.
  - Headroom & Normalization:
    Peak amplitude is normalized to 25,000 (~-2.5 dB headroom) and clamped to [-32767, 32767].

Direct C++ Raylib Translation (raylib.h):
  struct PowerupSFX {
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

# ==============================================================================
# PART 2: ZERO __pycache__ SETUP, PATH SETUP & RAYLIB IMPORTS
# ==============================================================================
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
# PART 3: AUDIO SYNTHESIS CONSTANTS
# ==============================================================================
SAMPLE_RATE = 44100
PI2 = 2.0 * math.pi

# Arpeggio frequencies: E minor triad + octave resolution
FREQ_E4 = 329.63
FREQ_G4 = 392.00
FREQ_B4 = 493.88
FREQ_E5 = 659.25

ARPEGGIO_FREQS = [FREQ_E4, FREQ_G4, FREQ_B4, FREQ_E5]
NOTE_STEP_DURATION = 0.035     # 35 ms step between note onsets
TOTAL_DURATION = 0.190         # 190 ms total duration
ATTACK_DURATION = 0.001        # 1 ms attack per note
FINAL_NOTE_ONSET = 0.105       # 105 ms (onset of E5)
DECAY_RATE_K = 4.0             # Exponential decay factor (k = 4.0)
VIBRATO_FREQ = 5.0             # 5 Hz vibrato modulation
VIBRATO_DEPTH = 0.02           # 2% frequency variation depth
HIGH_SHELF_FREQ = 2000.0       # 2 kHz high-shelf cutoff frequency
HIGH_SHELF_GAIN_DB = 4.0       # +4 dB shelf boost
TARGET_PEAK_AMPLITUDE = 25000.0# Peak amplitude (~-2.5 dB headroom)


# ==============================================================================
# PART 4: IN-MEMORY RIFF WAV PACKER (C++ 44-Byte Header Equivalent)
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
# PART 5: CORE SYNTHESIS FUNCTION & STANDARDIZED CONTROL METHODS
# ==============================================================================
def create_powerup_sfx(volume: float = 1.0) -> Sound:
    """
    Synthesizes the ascending 4-tone positive powerup arpeggio into a Raylib Sound struct.
    
    Mathematical breakdown:
      - Notes: E4 (329.63 Hz), G4 (392.00 Hz), B4 (493.88 Hz), E5 (659.25 Hz).
      - Step: 35 ms interval between onsets (total 190 ms).
      - Envelopes: 1 ms linear attack with cumulative sustain.
      - Resolution: Shimmering exponential decay (k=4.0) with 5 Hz vibrato on E5.
      - Timbre: Fundamental sine + bell overtones (2x, 3x, 4.2x modes).
      - EQ: High-shelf boost biquad filter at 2 kHz (+4 dB).
      - Normalization: Scaled to 24000-26000 (~-2.5 dB headroom) and clamped.

    Returns:
      Sound: Ready-to-play Sound handle resident in audio memory.
    """
    total_samples = int(SAMPLE_RATE * TOTAL_DURATION)
    raw_samples = [0.0] * total_samples
    phases = [0.0, 0.0, 0.0, 0.0]

    tail_duration = TOTAL_DURATION - FINAL_NOTE_ONSET  # 85 ms
    tail_dur_inv = 1.0 / tail_duration if tail_duration > 0.0 else 1.0

    for i in range(total_samples):
        t = float(i) / float(SAMPLE_RATE)
        sample_acc = 0.0

        for k in range(4):
            t_start = float(k) * NOTE_STEP_DURATION
            if t >= t_start:
                dt = t - t_start

                # 1 ms linear attack per note (avoids boundary clicks)
                if dt < ATTACK_DURATION:
                    env_attack = dt / ATTACK_DURATION
                else:
                    env_attack = 1.0

                # Shimmering exponential decay on final resolution note
                if t >= FINAL_NOTE_ONSET:
                    decay_progress = (t - FINAL_NOTE_ONSET) * tail_dur_inv
                    env_decay = math.exp(-DECAY_RATE_K * decay_progress)
                else:
                    env_decay = 1.0

                # Cumulative sustain weighting (earlier notes ring gently behind lead)
                sustain_weight = 0.65 if k < 3 else 1.0

                # Frequency calculation (with 5 Hz vibrato on final note E5)
                freq = ARPEGGIO_FREQS[k]
                if k == 3 and t >= FINAL_NOTE_ONSET:
                    vibrato_time = t - FINAL_NOTE_ONSET
                    vibrato_mod = math.sin(PI2 * VIBRATO_FREQ * vibrato_time)
                    freq = freq * (1.0 + VIBRATO_DEPTH * vibrato_mod)

                # Continuous phase accumulation
                phases[k] += PI2 * freq / float(SAMPLE_RATE)
                p = phases[k]

                # Pure sine fundamental + subtle harmonic bell overtones
                fundamental = math.sin(p)
                bell_octave = 0.18 * math.sin(2.0 * p)      # Octave mode
                bell_fifth = 0.08 * math.sin(3.0 * p)       # Octave + fifth
                bell_sparkle = 0.04 * math.sin(4.2 * p)     # Chime sparkle mode
                note_tone = fundamental + bell_octave + bell_fifth + bell_sparkle

                # Micro-fade at buffer boundary (last 2 ms) to ensure zero DC click
                fade_boundary = 1.0
                if t > (TOTAL_DURATION - 0.002):
                    fade_boundary = max(0.0, (TOTAL_DURATION - t) / 0.002)

                sample_acc += note_tone * env_attack * env_decay * sustain_weight * fade_boundary

        raw_samples[i] = sample_acc

    # --------------------------------------------------------------------------
    # Biquad High-Shelf Filter at 2 kHz (+4 dB Boost)
    # Robert Bristow-Johnson Audio EQ Cookbook implementation
    # --------------------------------------------------------------------------
    f0 = HIGH_SHELF_FREQ
    fs = float(SAMPLE_RATE)
    gain_db = HIGH_SHELF_GAIN_DB
    amp_a = 10.0 ** (gain_db / 40.0)
    w0 = PI2 * f0 / fs
    cos_w0 = math.cos(w0)
    sin_w0 = math.sin(w0)
    alpha = sin_w0 / 2.0 * math.sqrt(2.0)  # Slope S = 1.0

    b0 = amp_a * ((amp_a + 1.0) + (amp_a - 1.0) * cos_w0 + 2.0 * math.sqrt(amp_a) * alpha)
    b1 = -2.0 * amp_a * ((amp_a - 1.0) + (amp_a + 1.0) * cos_w0)
    b2 = amp_a * ((amp_a + 1.0) + (amp_a - 1.0) * cos_w0 - 2.0 * math.sqrt(amp_a) * alpha)
    a0 = (amp_a + 1.0) - (amp_a - 1.0) * cos_w0 + 2.0 * math.sqrt(amp_a) * alpha
    a1 = 2.0 * ((amp_a - 1.0) - (amp_a + 1.0) * cos_w0)
    a2 = (amp_a + 1.0) - (amp_a - 1.0) * cos_w0 - 2.0 * math.sqrt(amp_a) * alpha

    # Normalize biquad coefficients
    b0_norm = b0 / a0
    b1_norm = b1 / a0
    b2_norm = b2 / a0
    a1_norm = a1 / a0
    a2_norm = a2 / a0

    filtered_samples = [0.0] * total_samples
    x1 = 0.0
    x2 = 0.0
    y1 = 0.0
    y2 = 0.0

    for i in range(total_samples):
        x0 = raw_samples[i]
        y0 = b0_norm * x0 + b1_norm * x1 + b2_norm * x2 - a1_norm * y1 - a2_norm * y2
        x2 = x1
        x1 = x0
        y2 = y1
        y1 = y0
        filtered_samples[i] = y0

    # --------------------------------------------------------------------------
    # Headroom Normalization & Scaling (Target Peak 24,000 to 26,000)
    # --------------------------------------------------------------------------
    max_peak = 0.0
    for s in filtered_samples:
        abs_s = abs(s)
        if abs_s > max_peak:
            max_peak = abs_s

    user_volume = max(0.0, min(1.0, volume))
    target_amplitude = TARGET_PEAK_AMPLITUDE * user_volume
    scale = (target_amplitude / max_peak) if max_peak > 0.0 else 0.0

    scaled_samples = [s * scale for s in filtered_samples]

    wav_bytes = pack_riff_wav_mono_16bit(SAMPLE_RATE, scaled_samples)
    wave = load_wave_from_memory(".wav", wav_bytes, len(wav_bytes))
    sound = load_sound_from_wave(wave)
    unload_wave(wave)  # Free CPU RAM wave container; Sound retains device audio
    return sound


# Standardized alias mapping for dynamic discovery
create_sfx = create_powerup_sfx


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
# PART 6: STANDALONE AUDITION WORKBENCH & AUTOMATED SMOKE TEST
# ==============================================================================
class SFXAuditionApp:
    """
    Interactive sound previewer workbench allowing developers and students
    to audition the powerup sound effect with live parameter controls and telemetry.
    """
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        init_window(self.screen_width, self.screen_height, "SFX Workbench - Powerup (assets/audio/SFX/progression/powerup.py)")
        set_target_fps(60)
        init_audio_device()

        self.sound = create_powerup_sfx()
        self.trigger_pulse = 0.0
        self.playback_timer = 0.0
        self.volume = 0.85
        self.pitch = 1.0
        self.trigger_count = 0

    def trigger(self):
        """Triggers sound playback with current pitch/volume and animates visualizer."""
        play_sfx(self.sound, self.volume, self.pitch)
        self.trigger_pulse = 1.0
        self.playback_timer = TOTAL_DURATION / self.pitch
        self.trigger_count += 1

    def update(self):
        dt = min(get_frame_time(), 0.05)
        if self.trigger_pulse > 0.0:
            self.trigger_pulse = max(0.0, self.trigger_pulse - dt * 3.5)
        if self.playback_timer > 0.0:
            self.playback_timer = max(0.0, self.playback_timer - dt)

        # Trigger inputs: Space, Left Click, or Gamepad Face Down (A)
        if is_key_pressed(KEY_SPACE) or is_mouse_button_pressed(MOUSE_BUTTON_LEFT) or is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_FACE_DOWN):
            self.trigger()

        # Pitch adjustments: Up/Down arrows
        if is_key_pressed(KEY_UP):
            self.pitch = min(2.0, self.pitch + 0.1)
        elif is_key_pressed(KEY_DOWN):
            self.pitch = max(0.5, self.pitch - 0.1)

        # Volume adjustments: Right/Left arrows
        if is_key_pressed(KEY_RIGHT):
            self.volume = min(1.0, self.volume + 0.05)
        elif is_key_pressed(KEY_LEFT):
            self.volume = max(0.0, self.volume - 0.05)

        # Reset controls: [R] Key or Gamepad Start
        if is_key_pressed(KEY_R) or is_gamepad_button_pressed(0, GAMEPAD_BUTTON_MIDDLE_RIGHT):
            self.pitch = 1.0
            self.volume = 0.85

    def draw(self):
        begin_drawing()
        clear_background(Color(12, 16, 26, 255))

        # Header (keeps top-bar region x=450..980, y=14..48 clear for UI settings bar)
        draw_text("PROCEDURAL SFX AUDITION WORKBENCH", 24, 20, 20, RAYWHITE)
        draw_text("Asset: assets/audio/SFX/progression/powerup.py | Mode: Ascending E4-G4-B4-E5 Arpeggio", 24, 50, 13, SKYBLUE)

        # Control Instructions Card
        panel_y = 90
        draw_rectangle(24, panel_y, 400, 250, Color(20, 26, 42, 255))
        draw_rectangle_lines(24, panel_y, 400, 250, Color(45, 60, 95, 255))
        draw_text("CONTROLS & SHORTCUTS", 40, panel_y + 14, 15, YELLOW)
        draw_text("- [Space] / [Left Click]  : Trigger Powerup SFX", 40, panel_y + 44, 13, RAYWHITE)
        draw_text("- [Gamepad A / RT]        : Trigger Powerup SFX", 40, panel_y + 68, 13, RAYWHITE)
        draw_text("- [Up] / [Down] Arrows    : Adjust Pitch (+/- 0.1)", 40, panel_y + 92, 13, RAYWHITE)
        draw_text("- [Right] / [Left] Arrows : Adjust Volume (+/- 0.05)", 40, panel_y + 116, 13, RAYWHITE)
        draw_text("- [R] / Gamepad Start     : Reset Pitch & Volume", 40, panel_y + 140, 13, RAYWHITE)

        draw_line(40, panel_y + 168, 400, panel_y + 168, Color(40, 52, 80, 255))
        draw_text(f"Current Pitch   : {self.pitch:.1f}x", 40, panel_y + 180, 13, GREEN)
        draw_text(f"Current Volume  : {int(self.volume * 100)}%", 200, panel_y + 180, 13, GOLD)
        draw_text(f"Total Triggers  : {self.trigger_count}", 40, panel_y + 208, 13, LIGHTGRAY)

        # Synthesis Specs Card
        specs_y = 360
        draw_rectangle(24, specs_y, 400, 320, Color(18, 24, 38, 255))
        draw_rectangle_lines(24, specs_y, 400, 320, Color(45, 60, 95, 255))
        draw_text("SYNTHESIS SPECIFICATIONS", 40, specs_y + 14, 15, SKYBLUE)
        draw_text("Duration        : 190 ms (4 notes @ 35 ms step)", 40, specs_y + 44, 13, RAYWHITE)
        draw_text("Triad Tones     : E4 (329.6 Hz) -> G4 (392.0 Hz)", 40, specs_y + 70, 13, RAYWHITE)
        draw_text("Resolution      : B4 (493.9 Hz) -> E5 (659.3 Hz)", 40, specs_y + 96, 13, RAYWHITE)
        draw_text("Attack / Decay  : 1 ms attack, exp decay (k=4.0)", 40, specs_y + 122, 13, RAYWHITE)
        draw_text("Vibrato LFO     : 5.0 Hz, 2% depth on final E5", 40, specs_y + 148, 13, RAYWHITE)
        draw_text("Bell Harmonics  : 2x (18%), 3x (8%), 4.2x (4%)", 40, specs_y + 174, 13, RAYWHITE)
        draw_text("EQ Filter       : 2 kHz Biquad High-Shelf (+4 dB)", 40, specs_y + 200, 13, RAYWHITE)
        draw_text("Peak Amplitude  : 25,000 (~-2.5 dBFS headroom)", 40, specs_y + 226, 13, GREEN)
        draw_text("Format          : 44.1 kHz, 16-bit Mono PCM", 40, specs_y + 252, 13, LIGHTGRAY)

        # Real-time Visualizer Panel
        vis_x = 450
        vis_y = 90
        vis_w = 800
        vis_h = 360
        draw_rectangle(vis_x, vis_y, vis_w, vis_h, Color(16, 22, 34, 255))
        draw_rectangle_lines(vis_x, vis_y, vis_w, vis_h, Color(45, 60, 95, 255))
        draw_text("ARPEGGIO WAVEFORM & FREQUENCY MONITOR", vis_x + 20, vis_y + 16, 15, SKYBLUE)

        # Center line
        mid_y = vis_y + (vis_h // 2)
        draw_line(vis_x + 20, mid_y, vis_x + vis_w - 20, mid_y, Color(35, 45, 65, 255))

        # Dynamic amplitude pulse bar
        meter_w = int(self.trigger_pulse * (vis_w - 40))
        glow_r = int(50 + 180 * self.trigger_pulse)
        glow_g = int(140 + 115 * self.trigger_pulse)
        draw_rectangle(vis_x + 20, mid_y - 20, meter_w, 40, Color(glow_r, glow_g, 255, 200))
        draw_rectangle_lines(vis_x + 20, mid_y - 20, vis_w - 40, 40, Color(60, 80, 120, 255))

        # Simulated arpeggio wave curve
        prev_pt_x = vis_x + 20
        prev_pt_y = mid_y
        steps = 120
        for s in range(1, steps + 1):
            t = float(s) / float(steps)
            pt_x = vis_x + 20 + int(t * (vis_w - 40))

            # Approximate 4-note ascending frequency profile
            if t < 0.25:
                freq_factor = 1.0
            elif t < 0.50:
                freq_factor = 1.189
            elif t < 0.75:
                freq_factor = 1.498
            else:
                freq_factor = 2.0 * (1.0 + 0.05 * math.sin(t * 30.0))

            envelope = math.exp(-2.5 * max(0.0, t - 0.55))
            wave_amp = math.sin(t * 40.0 * freq_factor * self.pitch) * envelope * self.trigger_pulse * 85.0
            pt_y = int(mid_y - wave_amp)
            draw_line(prev_pt_x, prev_pt_y, pt_x, pt_y, Color(0, 230, 255, 240))
            prev_pt_x = pt_x
            prev_pt_y = pt_y

        # Note Step Progression Indicator Cards
        note_card_w = (vis_w - 50) // 4
        note_card_y = vis_y + vis_h + 20
        note_names = ["E4 (329.6 Hz)", "G4 (392.0 Hz)", "B4 (493.9 Hz)", "E5 (659.3 Hz)"]
        chord_roles = ["Root (0 ms)", "Minor 3rd (35 ms)", "Fifth (70 ms)", "Octave + Vib (105 ms)"]

        # Calculate active note based on playback timer
        active_step = -1
        if self.playback_timer > 0.0:
            elapsed = (TOTAL_DURATION / self.pitch) - self.playback_timer
            step_idx = int(elapsed / (NOTE_STEP_DURATION / self.pitch))
            active_step = min(3, max(0, step_idx))

        for idx in range(4):
            card_x = vis_x + idx * (note_card_w + 10)
            is_active = (active_step == idx) or (self.trigger_pulse > 0.7)

            if is_active:
                bg_col = Color(30, 60, 95, 255)
                border_col = Color(0, 220, 255, 255)
                text_col = YELLOW
            else:
                bg_col = Color(20, 26, 42, 255)
                border_col = Color(40, 52, 80, 255)
                text_col = RAYWHITE

            draw_rectangle(card_x, note_card_y, note_card_w, 90, bg_col)
            draw_rectangle_lines(card_x, note_card_y, note_card_w, 90, border_col)
            draw_text(f"NOTE {idx + 1}", card_x + 12, note_card_y + 12, 13, text_col)
            draw_text(note_names[idx], card_x + 12, note_card_y + 36, 13, RAYWHITE)
            draw_text(chord_roles[idx], card_x + 12, note_card_y + 60, 11, SKYBLUE)

        # Global Top-Bar Integration
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)
        end_drawing()

    def run(self, smoke_test: bool = False):
        frame_count = 0
        if smoke_test:
            # Trigger once to verify audio device synthesis, buffer upload, and playback
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
