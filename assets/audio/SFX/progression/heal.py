# -*- coding: utf-8 -*-
import sys
sys.dont_write_bytecode = True

"""
Procedural Heal Sound Effect (SFX) Synthesizer
==============================================
Type             : Procedural Audio SFX (Sound)
Target File      : assets/audio/SFX/progression/heal.py
Waveforms Used   : Dual detuned sine shimmer with 6 Hz vibrato and 2-pole low-pass filter
Category         : Progression & Economy (Health Recovery, Healing Spells, Vitality Wells)
Catalog ID       : sfx_prog_heal
Function Name    : create_heal_sfx

Problem Solved:
  Eliminates external .wav/.mp3 dependencies by synthesizing a warm, restorative
  vitality swell entirely from mathematical waveforms into an in-memory 16-bit PCM buffer,
  loading directly into a Raylib Sound struct with zero runtime file I/O.

Waveform Theory & Mathematical Rationale:
  - Acoustic Beating Shimmer:
    Two carrier sine waves are initialized slightly detuned at 523.25 Hz (C5) and
    526.50 Hz, producing a natural acoustic beating modulation of Delta f = 3.25 Hz:
      I(t) = sin(w1 * t) + sin(w2 * t) = 2 * cos((w1 - w2)*t / 2) * sin((w1 + w2)*t / 2)
    This generates an organic, comforting vitality shimmer without artificial chorus delays.
  - Upward Pitch Trajectory:
    Carrier base frequency glides smoothly upward from C5 (523.25 Hz) to G5 (783.99 Hz)
    over the 280ms duration:
      f_base(t) = f_start * (f_end / f_start) ** (t / duration)
    Ascending musical intervals (a perfect fifth) naturally communicate uplifting rejuvenation,
    restoration, and character revitalization.
  - 6 Hz Vibrato Modulation:
    A gentle low-frequency oscillation (LFO) at 6.0 Hz introduces subtle pitch warmth:
      f_mod(t) = f(t) * (1.0 + A_vib * sin(2 * pi * 6.0 * t))
    where A_vib = 0.012 (~20 cents pitch depth) creates a gentle musical vibrato.
  - 3-Stage Amplitude Envelope:
    - Attack (0 to 35 ms)    : Soft sinusoidal ease-in ramp avoiding sudden transient pops.
    - Sustain (35 to 215 ms)  : Stable 180 ms resonant body providing restorative presence.
    - Release (215 to 280 ms) : Smooth 65 ms exponential decay (k = 4.5):
        env(t) = exp(-4.5 * (t - t_sus) / t_rel)
      normalized to terminate exactly at zero with no boundary discontinuity.
  - Warm 2-Pole Low-Pass Filter:
    A 2-pole Butterworth digital biquad low-pass filter with cutoff at 1400 Hz attenuates
    high-frequency digital edge, imparting an analog warmth and velvety tonal character.
  - Headroom & Clamping:
    Samples are scaled to peak at ~25000 (-2.35 dB headroom) and strictly clamped to [-32767, 32767].

Direct C++ Raylib Translation (raylib.h):
  struct HealSFX {
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
# PART 3: AUDIO SYNTHESIS CONSTANTS (Palette-Free Synthesis Parameters)
# ==============================================================================
SAMPLE_RATE = 44100
PI2 = 2.0 * math.pi

DEFAULT_DURATION = 0.280       # 280 ms total duration
START_FREQUENCY = 523.25       # C5 (Hz)
START_DETUNE_FREQ = 526.50     # C5 + 3.25 Hz acoustic beating shimmer
END_FREQUENCY = 783.99         # G5 (Hz) - ascending restorative fifth

ATTACK_TIME = 0.035            # 35 ms soft attack
SUSTAIN_TIME = 0.180           # 180 ms gentle sustain
RELEASE_TIME = 0.065           # 65 ms exponential decay
RELEASE_DECAY_K = 4.5          # Release exponential curve factor

VIBRATO_FREQ = 6.0             # 6 Hz LFO vibrato rate
VIBRATO_DEPTH = 0.012          # ~1.2% subtle pitch modulation depth (~20 cents)

LP_CUTOFF_HZ = 1400.0          # 2-pole low-pass filter cutoff frequency (Hz)
LP_RESONANCE_Q = 0.7071        # Butterworth Q factor (maximally flat passband)

TARGET_PEAK_AMPLITUDE = 25000.0  # -2.35 dB headroom (target range 24000-26000)


# ==============================================================================
# 2-POLE BIQUAD DIGITAL FILTER (C++ Butterworth Biquad Equivalent)
# ==============================================================================
class BiquadLowPass2Pole:
    """
    Direct C++ transferable 2-pole biquad low-pass filter (Butterworth design).
    C++ Equivalent:
      struct BiquadLowPass2Pole {
          float b0, b1, b2, a1, a2;
          float x1 = 0.0f, x2 = 0.0f, y1 = 0.0f, y2 = 0.0f;
          void Init(float sampleRate, float cutoffHz, float q);
          float Process(float inSample);
      };
    """
    def __init__(self, sample_rate: int, cutoff_hz: float, q: float = 0.7071):
        # Calculate standard RBJ Audio EQ Cookbook biquad coefficients
        w0 = PI2 * cutoff_hz / float(sample_rate)
        cos_w0 = math.cos(w0)
        sin_w0 = math.sin(w0)
        alpha = sin_w0 / (2.0 * q)

        b0_raw = (1.0 - cos_w0) * 0.5
        b1_raw = 1.0 - cos_w0
        b2_raw = (1.0 - cos_w0) * 0.5
        a0_raw = 1.0 + alpha
        a1_raw = -2.0 * cos_w0
        a2_raw = 1.0 - alpha

        # Normalize by a0
        self.b0 = b0_raw / a0_raw
        self.b1 = b1_raw / a0_raw
        self.b2 = b2_raw / a0_raw
        self.a1 = a1_raw / a0_raw
        self.a2 = a2_raw / a0_raw

        # Delay registers
        self.x1 = 0.0
        self.x2 = 0.0
        self.y1 = 0.0
        self.y2 = 0.0

    def process(self, x: float) -> float:
        """Processes a single audio sample through the 2-pole difference equation."""
        y = (self.b0 * x) + (self.b1 * self.x1) + (self.b2 * self.x2) - (self.a1 * self.y1) - (self.a2 * self.y2)
        self.x2 = self.x1
        self.x1 = x
        self.y2 = self.y1
        self.y1 = y
        return y


# ==============================================================================
# PART 4: IN-MEMORY RIFF WAV PACKER HELPER (C++ 44-Byte Header Equivalent)
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
# PART 5: CORE SYNTHESIS FUNCTION & STANDARDIZED CONTROL METHODS
# ==============================================================================
def create_heal_sfx(
    duration: float = DEFAULT_DURATION,
    start_freq: float = START_FREQUENCY,
    end_freq: float = END_FREQUENCY,
    volume: float = 1.0
) -> Sound:
    """
    Synthesizes the restorative heal vitality swell sound effect into a ready-to-play
    Raylib Sound struct.
    
    Parameters:
      duration   : Total length in seconds (default: 0.280s = 280ms)
      start_freq : Fundamental starting carrier frequency in Hz (default: 523.25 Hz C5)
      end_freq   : Fundamental target carrier frequency in Hz (default: 783.99 Hz G5)
      volume     : Master amplitude gain multiplier (0.0 to 1.0)
    
    Returns:
      Raylib Sound handle resident in audio memory.
    """
    total_samples = int(SAMPLE_RATE * duration)
    detune_ratio = START_DETUNE_FREQ / START_FREQUENCY
    freq_log_ratio = math.log(end_freq / start_freq)

    # 3-stage envelope sample boundary divisions
    attack_samples = int(SAMPLE_RATE * ATTACK_TIME)
    sustain_end_sample = int(SAMPLE_RATE * (ATTACK_TIME + SUSTAIN_TIME))
    release_samples = max(1, total_samples - sustain_end_sample)
    exp_neg_k = math.exp(-RELEASE_DECAY_K)

    # Instantiate 2-pole low-pass Butterworth filter
    lp_filter = BiquadLowPass2Pole(SAMPLE_RATE, LP_CUTOFF_HZ, LP_RESONANCE_Q)

    phase_1 = 0.0
    phase_2 = 0.0
    unfiltered_samples = []

    for i in range(total_samples):
        t = float(i) / float(SAMPLE_RATE)
        progress = float(i) / float(total_samples)

        # 1. Frequency trajectory: Exponential pitch glide upward from C5 to G5
        base_freq = start_freq * math.exp(freq_log_ratio * progress)

        # 2. 6 Hz vibrato modulation LFO (~20 cents pitch depth)
        vib_lfo = math.sin(PI2 * VIBRATO_FREQ * t)
        vib_multiplier = 1.0 + (VIBRATO_DEPTH * vib_lfo)

        # 3. Dual detuned oscillators: 3.25 Hz acoustic beating shimmer at C5
        freq_1 = base_freq * vib_multiplier
        freq_2 = (base_freq * detune_ratio) * vib_multiplier

        phase_1 += PI2 * freq_1 / float(SAMPLE_RATE)
        phase_2 += PI2 * freq_2 / float(SAMPLE_RATE)

        # 4. 3-Stage Amplitude Envelope (Attack -> Sustain -> Release)
        if i < attack_samples:
            # Soft sinusoidal ease-in ramp avoids transient click
            p_att = float(i) / float(attack_samples)
            envelope = math.sin(0.5 * math.pi * p_att)
        elif i < sustain_end_sample:
            # Gentle sustain body
            envelope = 1.0
        else:
            # Smooth exponential decay normalized to zero
            p_rel = float(i - sustain_end_sample) / float(release_samples)
            envelope = (math.exp(-RELEASE_DECAY_K * p_rel) - exp_neg_k) / (1.0 - exp_neg_k)

        # 5. Dual sine wave summation
        sine_1 = math.sin(phase_1)
        sine_2 = math.sin(phase_2)
        combined_signal = 0.5 * (sine_1 + sine_2) * envelope

        # 6. Apply 2-pole low-pass biquad filter
        filtered_val = lp_filter.process(combined_signal)
        unfiltered_samples.append(filtered_val)

    # 7. Normalize peak amplitude to ~25000 (-2.35 dB headroom) and apply volume
    max_amp = 0.0
    for s in unfiltered_samples:
        abs_s = abs(s)
        if abs_s > max_amp:
            max_amp = abs_s

    if max_amp > 1e-6:
        gain = (TARGET_PEAK_AMPLITUDE / max_amp) * max(0.0, min(1.0, volume))
    else:
        gain = 1.0

    # 8. Clamp to signed 16-bit PCM integer range [-32767, 32767]
    pcm_samples = []
    for s in unfiltered_samples:
        scaled_sample = s * gain
        clamped_sample = max(-32767, min(32767, int(scaled_sample)))
        pcm_samples.append(clamped_sample)

    # 9. Pack into in-memory RIFF WAV container and load into Raylib Sound
    wav_bytes = pack_riff_wav_mono_16bit(SAMPLE_RATE, pcm_samples)
    wave = load_wave_from_memory(".wav", wav_bytes, len(wav_bytes))
    sound = load_sound_from_wave(wave)
    unload_wave(wave)  # Free raw CPU Wave container; Sound retains audio hardware handle
    return sound


# Standardized alias mapping for dynamic discovery
create_sfx = create_heal_sfx


# ==============================================================================
# STANDARDIZED PLAYBACK CONTROL METHODS
# ==============================================================================
def play_sfx(sound: Sound, volume: float = 1.0, pitch: float = 1.0) -> None:
    """Plays the heal sound effect with explicit volume and pitch scaling."""
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
    to audition the heal sound effect with live parameter controls and telemetry.
    """
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        init_window(
            self.screen_width,
            self.screen_height,
            "SFX Workbench - Heal Vitality Swell (assets/audio/SFX/progression/heal.py)"
        )
        set_target_fps(60)
        init_audio_device()

        self.sound = create_heal_sfx()
        self.trigger_pulse = 0.0
        self.volume = 0.85
        self.pitch = 1.0
        self.trigger_count = 0
        self.show_xray = False

        # Visualizer particles for vitality swell animation
        self.particles = []
        for _ in range(32):
            self.particles.append({
                "x": 0.0,
                "y": 0.0,
                "vx": 0.0,
                "vy": 0.0,
                "life": 0.0,
                "max_life": 1.0,
                "size": 3.0
            })

    def trigger(self):
        """Triggers sound playback with current pitch/volume and animates visualizer."""
        play_sfx(self.sound, self.volume, self.pitch)
        self.trigger_pulse = 1.0
        self.trigger_count += 1

        # Spawn restorative vitality sparkle particles
        cx = 850.0
        cy = 320.0
        import random
        for p in self.particles:
            ang = random.uniform(0.0, PI2)
            spd = random.uniform(40.0, 160.0)
            p["x"] = cx + math.cos(ang) * random.uniform(5.0, 40.0)
            p["y"] = cy + math.sin(ang) * random.uniform(5.0, 40.0)
            p["vx"] = math.cos(ang) * spd
            p["vy"] = math.sin(ang) * spd - random.uniform(30.0, 80.0)  # Ascending drift
            p["life"] = 1.0
            p["max_life"] = random.uniform(0.4, 0.8)
            p["size"] = random.uniform(2.5, 6.0)

    def update(self):
        dt = min(get_frame_time(), 0.05)
        if self.trigger_pulse > 0.0:
            self.trigger_pulse = max(0.0, self.trigger_pulse - dt * 2.8)

        # Update particles
        for p in self.particles:
            if p["life"] > 0.0:
                p["life"] = max(0.0, p["life"] - dt / p["max_life"])
                p["x"] += p["vx"] * dt
                p["y"] += p["vy"] * dt

        # Trigger inputs: Space, Left Click, or Gamepad Face A / RT
        gamepad_trigger = False
        if is_gamepad_available(0):
            if (is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_FACE_DOWN) or
                is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_TRIGGER_1) or
                is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_TRIGGER_2)):
                gamepad_trigger = True

        if is_key_pressed(KEY_SPACE) or is_mouse_button_pressed(MOUSE_BUTTON_LEFT) or gamepad_trigger:
            self.trigger()

        # Pitch adjustments: Up/Down arrows or Gamepad D-pad Up/Down
        pitch_up = is_key_pressed(KEY_UP)
        pitch_down = is_key_pressed(KEY_DOWN)
        if is_gamepad_available(0):
            if is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_UP):
                pitch_up = True
            if is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_DOWN):
                pitch_down = True

        if pitch_up:
            self.pitch = min(2.0, self.pitch + 0.1)
        elif pitch_down:
            self.pitch = max(0.5, self.pitch - 0.1)

        # Volume adjustments: Left/Right arrows
        if is_key_pressed(KEY_RIGHT):
            self.volume = min(1.0, self.volume + 0.05)
        elif is_key_pressed(KEY_LEFT):
            self.volume = max(0.0, self.volume - 0.05)

        # Reset pitch & volume: R key or Gamepad Start
        reset_pressed = is_key_pressed(KEY_R)
        if is_gamepad_available(0) and is_gamepad_button_pressed(0, GAMEPAD_BUTTON_MIDDLE_RIGHT):
            reset_pressed = True
        if reset_pressed:
            self.pitch = 1.0
            self.volume = 0.85

        # Toggle X-Ray Telemetry Overlay: Tab or Gamepad Y
        tab_pressed = is_key_pressed(KEY_TAB) or is_key_pressed(KEY_F1)
        if is_gamepad_available(0) and is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_FACE_UP):
            tab_pressed = True
        if tab_pressed:
            self.show_xray = not self.show_xray

    def draw(self):
        begin_drawing()
        clear_background(Color(10, 18, 22, 255))

        # Header (keeps top-bar region x=450..980, y=14..48 clear for UI settings bar)
        draw_text("PROCEDURAL SFX AUDITION WORKBENCH", 24, 18, 20, RAYWHITE)
        draw_text("Asset: assets/audio/SFX/progression/heal.py | Restorative Vitality Swell", 24, 46, 13, GREEN)

        # ======================================================================
        # LEFT CONTROL PANEL (x=24, y=90, w=400)
        # ======================================================================
        panel_y = 90
        panel_w = 400
        panel_h = 240
        draw_rectangle(24, panel_y, panel_w, panel_h, Color(16, 28, 32, 255))
        draw_rectangle_lines(24, panel_y, panel_w, panel_h, Color(35, 75, 65, 255))

        draw_text("INTERACTIVE CONTROLS & SHORTCUTS", 40, panel_y + 14, 15, YELLOW)
        draw_text("- [Space] / [Left Click] / Gamepad [A] : Trigger Heal SFX", 40, panel_y + 42, 13, RAYWHITE)
        draw_text("- [Up] / [Down] Arrows / D-Pad         : Adjust Pitch (+/- 0.1x)", 40, panel_y + 68, 13, RAYWHITE)
        draw_text("- [Left] / [Right] Arrows              : Adjust Volume (+/- 0.05)", 40, panel_y + 94, 13, RAYWHITE)
        draw_text("- [R] Key / Gamepad [Start]            : Reset Pitch & Volume", 40, panel_y + 120, 13, RAYWHITE)
        draw_text("- [Tab] / [F1] / Gamepad [Y]           : Toggle X-Ray Telemetry", 40, panel_y + 146, 13, SKYBLUE)

        draw_text(f"Current Pitch    : {self.pitch:.1f}x", 40, panel_y + 178, 13, GREEN)
        draw_text(f"Current Volume   : {self.volume:.2f}", 40, panel_y + 198, 13, GREEN)
        draw_text(f"Total Triggers   : {self.trigger_count}", 40, panel_y + 218, 13, LIGHTGRAY)

        # Parameter Specification Card (Below controls)
        card_y = panel_y + panel_h + 16
        card_h = 320
        draw_rectangle(24, card_y, panel_w, card_h, Color(14, 24, 28, 255))
        draw_rectangle_lines(24, card_y, panel_w, card_h, Color(30, 60, 50, 255))
        draw_text("SYNTHESIS SPECIFICATION & ARCHITECTURE", 40, card_y + 14, 14, SKYBLUE)

        specs = [
            ("Catalog ID", "sfx_prog_heal"),
            ("Waveforms", "Dual detuned sine shimmer + 6 Hz LFO"),
            ("Base Frequency", "523.25 Hz (C5) -> 783.99 Hz (G5)"),
            ("Detune Shimmer", "526.50 Hz (+3.25 Hz acoustic beating)"),
            ("Vibrato Rate", "6.0 Hz LFO (~20 cents pitch depth)"),
            ("Envelope Attack", "35 ms soft sinusoidal ease-in"),
            ("Envelope Sustain", "180 ms resonant body"),
            ("Envelope Release", "65 ms exponential decay (k=4.5)"),
            ("Total Duration", "280 ms (12,348 samples @ 44.1 kHz)"),
            ("Low-Pass Filter", "2-pole Butterworth biquad @ 1400 Hz"),
            ("Peak Amplitude", "~25,000 (-2.35 dB headroom)"),
            ("Container", "In-Memory 44-byte RIFF/WAV -> Sound")
        ]
        line_offset = card_y + 40
        for label, val in specs:
            draw_text(f"{label:<17}:", 40, line_offset, 12, GRAY)
            draw_text(val, 185, line_offset, 12, RAYWHITE)
            line_offset += 22

        # ======================================================================
        # RIGHT VISUALIZER WORKBENCH (x=450, y=90, w=800)
        # ======================================================================
        vis_x = 450
        vis_y = 90
        vis_w = 806
        vis_h = 576
        draw_rectangle(vis_x, vis_y, vis_w, vis_h, Color(12, 22, 26, 255))
        draw_rectangle_lines(vis_x, vis_y, vis_w, vis_h, Color(35, 75, 65, 255))

        draw_text("RESTORATIVE AURA & WAVEFORM VISUALIZER", vis_x + 20, vis_y + 16, 15, GREEN)
        draw_text("Real-time Acoustic Shimmer Simulation (523.25 Hz / 526.50 Hz Interference)", vis_x + 20, vis_y + 38, 12, GRAY)

        # Visualizer center area
        center_x = vis_x + (vis_w // 2)
        center_y = vis_y + 200

        # Dynamic vitality aura circle with glowing rings
        aura_radius = 45.0 + (self.trigger_pulse * 65.0)
        glow_alpha = int(self.trigger_pulse * 140)
        draw_circle(center_x, center_y, aura_radius, Color(30, 180, 100, glow_alpha // 3))
        draw_circle_lines(center_x, center_y, aura_radius, Color(80, 255, 160, glow_alpha))
        draw_circle_lines(center_x, center_y, aura_radius * 0.7, Color(140, 255, 200, glow_alpha))
        draw_circle(center_x, center_y, 14.0 + self.trigger_pulse * 8.0, Color(160, 255, 220, 220))

        # Draw vitality shimmer particles
        for p in self.particles:
            if p["life"] > 0.0:
                p_alpha = int(p["life"] * 240)
                draw_circle(
                    int(p["x"]),
                    int(p["y"]),
                    p["size"] * (0.5 + 0.5 * p["life"]),
                    Color(120, 255, 180, p_alpha)
                )

        # Dynamic amplitude pulse meter bar
        meter_y = vis_y + 340
        meter_w = vis_w - 40
        draw_rectangle(vis_x + 20, meter_y, meter_w, 20, Color(20, 35, 40, 255))
        draw_rectangle_lines(vis_x + 20, meter_y, meter_w, 20, Color(40, 80, 70, 255))
        active_meter = int(self.trigger_pulse * meter_w)
        draw_rectangle(vis_x + 20, meter_y, active_meter, 20, Color(40, 220, 120, 220))
        draw_text("AMPLITUDE ENVELOPE SWELL", vis_x + 24, meter_y + 4, 11, RAYWHITE)

        # Simulated frequency sweep curve with dual-sine beating envelope
        wave_y = vis_y + 440
        draw_line(vis_x + 20, wave_y, vis_x + vis_w - 20, wave_y, Color(30, 55, 50, 255))
        draw_text("OSCILLOSCOPE: DUAL DETUNED SINE INTERFERENCE (3.25 Hz BEAT)", vis_x + 20, wave_y - 65, 12, SKYBLUE)

        prev_pt_x = vis_x + 20
        prev_pt_y = wave_y
        steps = 120
        for s in range(1, steps + 1):
            t = float(s) / float(steps)
            pt_x = vis_x + 20 + int(t * (vis_w - 40))

            # Acoustic beating amplitude modulation at 3.25 Hz: cos(Delta w * t / 2)
            beating = math.cos(t * 3.25 * PI2 * 0.280 * 2.0)
            carrier = math.sin(t * (12.0 + t * 6.0) * self.pitch)

            # Combined simulated waveform with envelope
            if t < 0.125:  # Attack portion
                env = math.sin(0.5 * math.pi * (t / 0.125))
            elif t < 0.77:  # Sustain portion
                env = 1.0
            else:  # Release portion
                env = math.exp(-4.5 * ((t - 0.77) / 0.23))

            wave_amp = carrier * beating * env * (25.0 + self.trigger_pulse * 35.0)
            pt_y = int(wave_y - wave_amp)
            draw_line(prev_pt_x, prev_pt_y, pt_x, pt_y, Color(60, 240, 160, 220))
            prev_pt_x = pt_x
            prev_pt_y = pt_y

        # Envelope segment markers
        x_att = vis_x + 20 + int(0.125 * (vis_w - 40))
        x_sus = vis_x + 20 + int(0.770 * (vis_w - 40))
        draw_line(x_att, wave_y - 45, x_att, wave_y + 45, Color(80, 140, 100, 180))
        draw_line(x_sus, wave_y - 45, x_sus, wave_y + 45, Color(80, 140, 100, 180))
        draw_text("Attack: 35ms", vis_x + 22, wave_y + 48, 11, YELLOW)
        draw_text("Sustain: 180ms", x_att + 6, wave_y + 48, 11, GREEN)
        draw_text("Release: 65ms (k=4.5)", x_sus + 6, wave_y + 48, 11, SKYBLUE)

        # X-Ray Telemetry Overlay (Toggled via Tab / F1)
        if self.show_xray:
            ox = vis_x + 20
            oy = vis_y + 60
            ow = vis_w - 40
            oh = 260
            draw_rectangle(ox, oy, ow, oh, Color(8, 14, 18, 245))
            draw_rectangle_lines(ox, oy, ow, oh, Color(60, 220, 140, 255))
            draw_text("X-RAY TELEMETRY: REAL-TIME SYNTHESIS EQUATIONS", ox + 16, oy + 12, 14, YELLOW)

            eqs = [
                "1. Acoustic Beating  : s(t) = 0.5 * [sin(w1*t) + sin(w2*t)] = cos(Dw*t/2) * sin(S_w*t/2)",
                "2. Pitch Trajectory  : f_base(t) = 523.25 * exp(ln(783.99/523.25) * t / 0.280)",
                "3. Vibrato LFO       : f(t) = f_base(t) * [1.0 + 0.012 * sin(2*pi * 6.0 * t)]",
                "4. Detune Shimmer    : f2(t) = f(t) * (526.50 / 523.25) -> Delta f = 3.25 Hz",
                "5. 2-Pole Biquad LPF : y[n] = b0*x[n] + b1*x[n-1] + b2*x[n-2] - a1*y[n-1] - a2*y[n-2]",
                "6. Envelope Stages   : Attack(35ms) sin-ramp -> Sustain(180ms) 1.0 -> Release(65ms) exp(-4.5*p)",
                "7. Headroom Scaling  : Peak scaled to 25,000 / 32,767 (~-2.35 dB headroom)"
            ]
            for idx, eq in enumerate(eqs):
                draw_text(eq, ox + 16, oy + 38 + (idx * 24), 12, RAYWHITE)

        # Top Bar Integration (Clear area maintained at x=450..980, y=14..48)
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)

        end_drawing()

    def run(self, smoke_test: bool = False):
        """Runs the audition workbench loop or automated smoke-test."""
        frame_count = 0
        if smoke_test:
            # Trigger once to verify audio device synthesis, buffer streaming, and playback
            self.trigger()

        while not window_should_close():
            self.update()
            self.draw()
            frame_count += 1
            if smoke_test and frame_count >= 3:
                break

        # Clean teardown of audio device and window
        unload_sfx(self.sound)
        close_audio_device()
        close_window()


if __name__ == "__main__":
    is_smoke = "--smoke-test" in sys.argv
    SFXAuditionApp().run(smoke_test=is_smoke)
