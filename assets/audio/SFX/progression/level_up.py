# -*- coding: utf-8 -*-
"""
Procedural Level Up Fanfare Sound Effect (SFX) Synthesizer
==========================================================
Type             : Procedural Audio SFX (Sound)
Target File      : assets/audio/SFX/progression/level_up.py
Catalog ID       : sfx_prog_level_up
Waveforms Used   : Blended sine-square carrier (85/15 mix), 4 Hz vibrato LFO, 130 Hz sub-bass sine
Category         : Progression & Economy (sfx_prog_level_up)

Problem Solved:
  Eliminates static external audio assets (.wav, .mp3) by procedurally synthesizing
  a triumphant 5-note pentatonic fanfare entirely in memory into a 16-bit mono PCM
  RIFF/WAV buffer, loading directly into a Raylib Sound struct.

Waveform Theory & Mathematical Rationale:
  - Musical Scale (Major Pentatonic):
      Notes: C5 (523.25 Hz), D5 (587.33 Hz), E5 (659.25 Hz), G5 (783.99 Hz), C6 (1046.50 Hz).
      The major pentatonic scale contains no semitones or tritone dissonance (scale degrees
      1, 2, 3, 5, 8), producing an inherently triumphant, heroic, and celebratory fanfare.
  - Step Sequencer Timing:
      Notes step at 65ms intervals (0.000s, 0.065s, 0.130s, 0.195s, 0.260s).
      The first 4 notes act as rapid ascending herald steps leading to the climactic C6.
  - Blended Sine-Square Carrier (85/15 Mix):
      The carrier blends a pure fundamental sine wave (85%) with odd-harmonic square grit (15%):
      mix(t) = 0.85 * sin(phi) + 0.15 * sign(sin(phi)).
      This yields warm, rich brass-like clarity without harsh clipping distortion.
  - Climactic Vibrato Modulation:
      The sustained C6 note (at t >= 0.260s) receives an active 4 Hz low-frequency vibrato:
      f_inst(t) = 1046.50 + 18.0 * sin(2 * pi * 4.0 * t_local).
      This imparts a singing, resonant acoustic character reminiscent of a brass trumpet.
  - Multi-Layer Octave Sub-Bass Reinforcement:
      A dedicated sub-bass oscillator at 130.0 Hz (close to C3 = 130.81 Hz) runs beneath
      the fanfare to deliver tactile low-end punch and acoustic weight.
  - Amplitude Envelope Anatomy:
      - Per-note fast attack of 2ms (0.002s) eliminates transient clicks while preserving punch.
      - Ascending herald notes maintain energy with a subtle 10% articulation decay.
      - Final C6 note features a long resonant release tail: env_tail(t) = exp(-2.2 * t / 0.180).
      - Boundary fade-out on the final 3ms guarantees absolute zero boundary DC thumps.
  - Amplitude Scaling & Headroom:
      Peak amplitude is scaled to ~24000-26000, leaving ~-2.5 dB headroom below signed 16-bit
      maximum (32767) to ensure zero digital clipping on any DAC hardware.

Direct C++ Raylib Translation (raylib.h):
  struct LevelUpSFX {
      Sound sound;
      void Play(float volume = 1.0f, float pitch = 1.0f) {
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

DEFAULT_DURATION = 0.420       # Total duration in seconds (420 ms)
NOTE_STEP = 0.065              # Step duration for ascending herald notes (65 ms)
ATTACK_TIME = 0.002            # Per-note rapid attack envelope (2 ms)
TAIL_SPAN = 0.180              # Resonant release decay span (180 ms)
DECAY_RATE_K = 2.2             # Release exponential decay factor (k = 2.2)

VIBRATO_RATE = 4.0             # LFO frequency on final C6 note (4 Hz)
VIBRATO_DEPTH = 18.0           # Pitch modulation depth on C6 (+/- 18.0 Hz)
SUB_BASS_FREQ = 130.0          # Sub-bass reinforcement frequency (130 Hz)

# 5-Note Pentatonic Fanfare Frequencies: C5, D5, E5, G5, C6
NOTE_FREQS = [523.25, 587.33, 659.25, 783.99, 1046.50]
NOTE_NAMES = ["C5", "D5", "E5", "G5", "C6"]

# Amplitude headroom scaling (~-2.5 dB below signed 16-bit ceiling 32767)
PEAK_AMPLITUDE = 25000.0


# ==============================================================================
# PART 4: IN-MEMORY RIFF WAV PACKER HELPER (C++ 44-Byte Header Equivalent)
# ==============================================================================
def pack_riff_wav_mono_16bit(sample_rate: int, raw_samples: list) -> bytes:
    """
    Packs signed 16-bit PCM integer samples (-32767 to 32767) into an in-memory
    canonical 44-byte RIFF/WAVE container.

    C++ Architecture Note:
      Mirrors writing a packed 44-byte RIFF header struct into memory before
      passing the contiguous buffer directly to Raylib's LoadWaveFromMemory().
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
    audio_format = 1        # PCM format code
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
def create_level_up_sfx(
    volume: float = 1.0,
    duration: float = DEFAULT_DURATION
) -> Sound:
    """
    Synthesizes a triumphant 5-note pentatonic fanfare (C5 to C6) into a Raylib Sound struct.
    Returns a ready-to-play Sound handle resident in audio hardware memory.
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []

    # Oscillator phase accumulators
    carrier_phase = 0.0
    sub_phase = 0.0

    for i in range(total_samples):
        # Current sample timestamp in seconds
        t = float(i) / float(SAMPLE_RATE)

        # ----------------------------------------------------------------------
        # 1. Step Sequencer & Pitch Determination
        # ----------------------------------------------------------------------
        if t < 4.0 * NOTE_STEP:
            # Ascending herald notes (C5, D5, E5, G5)
            note_idx = int(t / NOTE_STEP)
            t_local = t - float(note_idx) * NOTE_STEP
            freq = NOTE_FREQS[note_idx]

            # Continuous phase accumulation
            carrier_phase += PI2 * freq / SAMPLE_RATE

            # 2ms attack ramp + 10% articulation decay
            attack = min(1.0, t_local / ATTACK_TIME)
            decay = 1.0 - 0.10 * (t_local / NOTE_STEP)
            carrier_env = attack * decay
        else:
            # Final sustained C6 with vibrato and resonant release tail
            t_local = t - 4.0 * NOTE_STEP

            # Smooth onset for 4 Hz vibrato (ramped in over first 35ms)
            vib_ramp = min(1.0, t_local / 0.035)
            vibrato_offset = vib_ramp * VIBRATO_DEPTH * math.sin(PI2 * VIBRATO_RATE * t_local)
            freq = NOTE_FREQS[4] + vibrato_offset

            # Continuous phase accumulation
            carrier_phase += PI2 * freq / SAMPLE_RATE

            # 2ms attack ramp + long resonant release tail (k=2.2)
            attack = min(1.0, t_local / ATTACK_TIME)
            release = math.exp(-DECAY_RATE_K * (t_local / TAIL_SPAN))

            # Anti-click safety fade on final 3ms of audio buffer
            end_fade = max(0.0, min(1.0, (duration - t) / 0.003))
            carrier_env = attack * release * end_fade

        # ----------------------------------------------------------------------
        # 2. Blended Sine-Square Carrier Synthesis (85/15 Mix)
        # ----------------------------------------------------------------------
        sine_val = math.sin(carrier_phase)
        square_val = 1.0 if sine_val >= 0.0 else -1.0
        blended_carrier = (0.85 * sine_val) + (0.15 * square_val)
        carrier_sample = blended_carrier * carrier_env

        # ----------------------------------------------------------------------
        # 3. Octave Sub-Bass Reinforcement (130 Hz Sine)
        # ----------------------------------------------------------------------
        sub_phase += PI2 * SUB_BASS_FREQ / SAMPLE_RATE
        sub_sine = math.sin(sub_phase)
        sub_attack = min(1.0, t / 0.005)
        sub_decay = math.exp(-1.8 * (t / duration))
        sub_fade = max(0.0, min(1.0, (duration - t) / 0.004))
        sub_env = sub_attack * sub_decay * sub_fade
        sub_sample = sub_sine * sub_env

        # ----------------------------------------------------------------------
        # 4. Multi-Layer Mixing & Clamping
        # ----------------------------------------------------------------------
        # 80% carrier fanfare + 20% sub-bass body
        mixed = (0.80 * carrier_sample) + (0.20 * sub_sample)
        sample_16bit = mixed * PEAK_AMPLITUDE
        samples.append(sample_16bit)

    # Pack PCM buffer into canonical RIFF/WAV header
    wav_bytes = pack_riff_wav_mono_16bit(SAMPLE_RATE, samples)

    # Upload to Raylib audio device
    wave = load_wave_from_memory(".wav", wav_bytes, len(wav_bytes))
    sound = load_sound_from_wave(wave)
    unload_wave(wave)  # Free raw CPU RAM buffer; Sound retains hardware handle

    if volume != 1.0:
        set_sound_volume(sound, max(0.0, min(1.0, volume)))

    return sound


# Standardized alias mapping for dynamic discovery
create_sfx = create_level_up_sfx


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
    to audition the level-up fanfare sound effect with live parameter controls,
    pentatonic ladder monitoring, and telemetry.
    """
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        init_window(
            self.screen_width,
            self.screen_height,
            "SFX Workbench - Level Up Fanfare (assets/audio/SFX/progression/level_up.py)"
        )
        set_target_fps(60)
        init_audio_device()

        self.sound = create_level_up_sfx()
        self.trigger_pulse = 0.0
        self.playback_timer = 0.0
        self.volume = 0.85
        self.pitch = 1.0
        self.trigger_count = 0

    def trigger(self):
        """Triggers sound playback with current pitch/volume and animates visualizer."""
        play_sfx(self.sound, self.volume, self.pitch)
        self.trigger_pulse = 1.0
        self.playback_timer = DEFAULT_DURATION / max(0.5, self.pitch)
        self.trigger_count += 1

    def update(self):
        dt = min(get_frame_time(), 0.05)

        # Decay animation meters
        if self.trigger_pulse > 0.0:
            self.trigger_pulse = max(0.0, self.trigger_pulse - dt * 2.8)
        if self.playback_timer > 0.0:
            self.playback_timer = max(0.0, self.playback_timer - dt)

        # Trigger inputs: Space, Left Click, or Gamepad Face Down (A) / Right Trigger
        gamepad_trigger = (
            is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_FACE_DOWN)
            or is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_TRIGGER_1)
            or is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_TRIGGER_2)
        )
        if is_key_pressed(KEY_SPACE) or is_mouse_button_pressed(MOUSE_BUTTON_LEFT) or gamepad_trigger:
            self.trigger()

        # Pitch adjustments: Up/Down arrows or Gamepad DPad Up/Down
        pitch_up = is_key_pressed(KEY_UP) or is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_UP)
        pitch_down = is_key_pressed(KEY_DOWN) or is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_DOWN)
        if pitch_up:
            self.pitch = min(2.0, self.pitch + 0.1)
        elif pitch_down:
            self.pitch = max(0.5, self.pitch - 0.1)

        # Volume adjustments: Left/Right arrows
        if is_key_pressed(KEY_RIGHT):
            self.volume = min(1.0, self.volume + 0.05)
        elif is_key_pressed(KEY_LEFT):
            self.volume = max(0.1, self.volume - 0.05)

        # Reset controls: [R] Key or Gamepad Start
        gamepad_reset = is_gamepad_button_pressed(0, GAMEPAD_BUTTON_MIDDLE_RIGHT)
        if is_key_pressed(KEY_R) or gamepad_reset:
            self.pitch = 1.0
            self.volume = 0.85

    def draw(self):
        begin_drawing()
        clear_background(Color(12, 16, 26, 255))

        # Header (keeps top-bar region x=450..980, y=14..48 clear for global dropdowns)
        draw_text("PROCEDURAL SFX AUDITION WORKBENCH", 24, 20, 20, RAYWHITE)
        draw_text(
            "Asset: assets/audio/SFX/progression/level_up.py | Waveform: 5-Note Pentatonic Fanfare (85/15 Sine+Square)",
            24, 48, 12, SKYBLUE
        )

        # ----------------------------------------------------------------------
        # Left Column: Information & Controls Cards
        # ----------------------------------------------------------------------
        panel_y = 90

        # Info & Specs Card
        draw_rectangle(24, panel_y, 400, 165, Color(20, 26, 42, 255))
        draw_rectangle_lines(24, panel_y, 400, 165, Color(45, 60, 95, 255))
        draw_text("FANFARE SPECIFICATIONS", 40, panel_y + 14, 15, GOLD)
        draw_text("- Scale: C Major Pentatonic (C5, D5, E5, G5, C6)", 40, panel_y + 40, 12, RAYWHITE)
        draw_text("- Waveform: 85% Sine + 15% Square Carrier", 40, panel_y + 62, 12, RAYWHITE)
        draw_text("- Cadence: 65ms note intervals, 420ms total", 40, panel_y + 84, 12, RAYWHITE)
        draw_text("- Modulation: 4 Hz Vibrato (+/-18 Hz) on C6", 40, panel_y + 106, 12, RAYWHITE)
        draw_text("- Sub-Bass: 130 Hz Sine Layer for low-end body", 40, panel_y + 128, 12, RAYWHITE)

        # Controls & Dual-Input Card
        ctrl_y = panel_y + 180
        draw_rectangle(24, ctrl_y, 400, 210, Color(20, 26, 42, 255))
        draw_rectangle_lines(24, ctrl_y, 400, 210, Color(45, 60, 95, 255))
        draw_text("CONTROLS & SHORTCUTS", 40, ctrl_y + 14, 15, YELLOW)
        draw_text("- [Space] / [Left Click] / Gamepad A : Trigger SFX", 40, ctrl_y + 40, 12, RAYWHITE)
        draw_text("- [Up] / [Down] / DPad Up/Down     : Pitch (+/- 0.1x)", 40, ctrl_y + 64, 12, RAYWHITE)
        draw_text("- [Left] / [Right] Arrows          : Volume (+/- 0.05)", 40, ctrl_y + 88, 12, RAYWHITE)
        draw_text("- [R] Key / Gamepad Start          : Reset All", 40, ctrl_y + 112, 12, RAYWHITE)

        draw_text(f"Current Pitch   : {self.pitch:.1f}x", 40, ctrl_y + 142, 13, GREEN)
        draw_text(f"Current Volume  : {int(self.volume * 100)}%", 220, ctrl_y + 142, 13, SKYBLUE)
        draw_text(f"Total Triggers  : {self.trigger_count}", 40, ctrl_y + 168, 13, LIGHTGRAY)

        # ----------------------------------------------------------------------
        # Right Column: Audio Output & Pentatonic Step Monitor
        # ----------------------------------------------------------------------
        vis_x = 450
        vis_y = 90
        vis_w = 800
        vis_h = 420
        draw_rectangle(vis_x, vis_y, vis_w, vis_h, Color(16, 22, 34, 255))
        draw_rectangle_lines(vis_x, vis_y, vis_w, vis_h, Color(45, 60, 95, 255))
        draw_text("REAL-TIME AUDIO MONITOR & PENTATONIC STEP SEQUENCER", vis_x + 20, vis_y + 16, 15, SKYBLUE)

        # Pentatonic Ladder Lights (5 Steps)
        ladder_y = vis_y + 50
        box_w = 140
        box_h = 55
        spacing = 12

        # Compute active note index based on elapsed playback time
        active_note = -1
        if self.playback_timer > 0.0:
            elapsed = (DEFAULT_DURATION / max(0.5, self.pitch)) - self.playback_timer
            step_scaled = NOTE_STEP / max(0.5, self.pitch)
            active_note = min(4, int(elapsed / step_scaled))

        for idx in range(5):
            bx = vis_x + 20 + idx * (box_w + spacing)
            is_active = (idx == active_note)
            bg_col = Color(50, 180, 255, 220) if is_active else Color(25, 33, 50, 255)
            border_col = Color(255, 220, 60, 255) if is_active else Color(50, 65, 95, 255)
            text_col = Color(10, 20, 30, 255) if is_active else RAYWHITE

            draw_rectangle(bx, ladder_y, box_w, box_h, bg_col)
            draw_rectangle_lines(bx, ladder_y, box_w, box_h, border_col)
            draw_text(f"Note {idx + 1}: {NOTE_NAMES[idx]}", bx + 12, ladder_y + 10, 13, text_col)
            draw_text(f"{NOTE_FREQS[idx]:.1f} Hz", bx + 12, ladder_y + 30, 11, text_col if is_active else LIGHTGRAY)

        # Amplitude Pulse Meter
        meter_y = vis_y + 130
        meter_w = int(self.trigger_pulse * (vis_w - 40))
        glow_r = int(255 * self.trigger_pulse)
        glow_g = int(200 * self.trigger_pulse)
        draw_rectangle(vis_x + 20, meter_y, meter_w, 24, Color(glow_r, glow_g, 80, 220))
        draw_rectangle_lines(vis_x + 20, meter_y, vis_w - 40, 24, Color(60, 80, 120, 255))
        draw_text("SIGNAL AMPLITUDE", vis_x + 30, meter_y + 6, 11, RAYWHITE)

        # Waveform Oscilloscope Display
        osc_y = vis_y + 180
        osc_h = 210
        draw_rectangle(vis_x + 20, osc_y, vis_w - 40, osc_h, Color(10, 14, 22, 255))
        draw_rectangle_lines(vis_x + 20, osc_y, vis_w - 40, osc_h, Color(40, 52, 78, 255))

        mid_y = osc_y + (osc_h // 2)
        draw_line(vis_x + 20, mid_y, vis_x + vis_w - 20, mid_y, Color(30, 42, 60, 255))
        draw_text("FANFARE COMPOSITE OSCILLOSCOPE (Carrier 85/15 + Sub-Bass 130Hz)", vis_x + 30, osc_y + 12, 12, GOLD)

        # Oscilloscope Curve Plotting
        prev_pt_x = vis_x + 20
        prev_pt_y = mid_y
        steps = 120
        for s in range(1, steps + 1):
            t_norm = float(s) / float(steps)
            pt_x = vis_x + 20 + int(t_norm * (vis_w - 40))

            # Simulate synthesized waveform envelope and vibrato modulation
            wave_time = t_norm * DEFAULT_DURATION
            note_i = min(4, int(wave_time / NOTE_STEP))
            f_base = NOTE_FREQS[note_i] * self.pitch
            vibrato = 18.0 * math.sin(PI2 * VIBRATO_RATE * wave_time) if note_i == 4 else 0.0

            sine_c = math.sin(PI2 * (f_base + vibrato) * wave_time * 0.015)
            sq_c = 1.0 if sine_c >= 0.0 else -1.0
            carrier = (0.85 * sine_c) + (0.15 * sq_c)
            sub = 0.25 * math.sin(PI2 * SUB_BASS_FREQ * wave_time * 0.015)

            decay = math.exp(-2.2 * max(0.0, wave_time - 4.0 * NOTE_STEP) / TAIL_SPAN)
            wave_amp = (carrier + sub) * decay * self.trigger_pulse * 75.0
            pt_y = int(mid_y - wave_amp)

            draw_line(prev_pt_x, prev_pt_y, pt_x, pt_y, Color(0, 220, 255, 230))
            prev_pt_x = pt_x
            prev_pt_y = pt_y

        # Global Top-Bar Integration (Region x=450..980, y=14..48 preserved clear)
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)
        end_drawing()

    def run(self, smoke_test: bool = False):
        frame_count = 0
        if smoke_test:
            # Trigger once to verify audio device synthesis, hardware upload, and playback
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
