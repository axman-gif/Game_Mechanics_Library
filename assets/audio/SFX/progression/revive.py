# -*- coding: utf-8 -*-
import sys
sys.dont_write_bytecode = True

"""
Procedural Revive Sound Effect (SFX) Synthesizer
================================================
Type             : Procedural Audio SFX (Sound)
Target File      : assets/audio/SFX/progression/revive.py
Waveforms Used   : F-major organ triad (F4-A4-C5-F5) blended sine-saw (80/20 mix)
                   with micro-portamento (+30 Hz), 0.3 Hz chorus LFO, and 2-pole low-pass filter
Category         : Progression & Economy (Player Respawn, Teammate Revival, Phoenix-Down Resurrection)
Catalog ID       : sfx_prog_revive
Function Name    : create_revive_sfx

Problem Solved:
  Eliminates external audio dependencies (.wav/.ogg/.mp3) by synthesizing a triumphant,
  glorious resurrection stinger entirely from mathematical primitives directly into an
  in-memory 16-bit mono PCM buffer loaded into a Raylib Sound struct with zero disk I/O.

Waveform Theory & Mathematical Rationale:
  - F-Major Organ Triad Voicing:
      Notes: F4 (349.23 Hz), A4 (440.00 Hz), C5 (523.25 Hz), F5 (698.46 Hz).
      The root F4 provides solid foundation, the major third A4 introduces warmth and triumph,
      the fifth C5 establishes harmonic stability, and the octave F5 adds spiritual brilliance.
  - Blended Sine-Saw Waveforms (80/20 Mix):
      Each organ pipe blends fundamental roundness (80% sine) with overtone brilliance (20% saw):
        saw(phi) = 2.0 * ((phi / (2 * pi)) % 1.0) - 1.0
        voice(t) = 0.8 * sin(phi) + 0.2 * saw(phi)
      Yields the majestic, breathy body of liturgical pipe organs without digital harshness.
  - Uplifting Micro-Portamento (+30 Hz Glide):
      During the initial swell, an upward micro-glide of +30.0 Hz elevates the chord:
        portamento(t) = 30.0 * (1.0 - exp(-3.5 * progress))
      Evokes the sensation of a soul rising from the fallen state back to triumphant vitality.
  - Warm Ensemble Chorus LFO (0.3 Hz Flutter):
      A slow 0.3 Hz low-frequency oscillator modulates each voice with quarter-phase offsets
      (phi_c = v * pi / 2) to simulate cathedral chamber air column interference:
        mod_v(t) = 0.006 * sin(2 * pi * 0.3 * t + phi_c)
  - 3-Stage Amplitude Envelope (Attack -> Sustain -> Release):
      - Swell Attack (0 to 65 ms)      : Sinusoidal ease-in ramp delivering a spiritual crescendo.
      - Glorious Sustain (65 to 305 ms): Full 240 ms resonant chord body projecting resurrection power.
      - Warm Release (305 to 465 ms)   : Smooth 160 ms exponential tail (k = 3.0) normalized to 0.0.
      Total duration: exactly 465 ms (20,506 samples @ 44.1 kHz).
  - Warm 2-Pole Low-Pass Filter:
      A 2-pole Butterworth biquad filter with cutoff at 2400 Hz (Q = 0.7071) softens saw overtones.
  - Headroom & Clamping:
      Peak amplitude normalized to 25,000 (-2.35 dB headroom) and strictly clamped to [-32767, 32767].

Direct C++ Raylib Translation (raylib.h):
  struct ReviveSFX {
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
# PART 2: PATH SETUP & MANDATORY IMPORTS
# ==============================================================================
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

DEFAULT_DURATION = 0.465        # 465 ms total duration
TRIAD_F4 = 349.23               # F4 fundamental root (Hz)
TRIAD_A4 = 440.00               # A4 major third (Hz)
TRIAD_C5 = 523.25               # C5 perfect fifth (Hz)
TRIAD_F5 = 698.46               # F5 octave ceiling (Hz)
TRIAD_FREQUENCIES = (TRIAD_F4, TRIAD_A4, TRIAD_C5, TRIAD_F5)

SINE_RATIO = 0.8                # 80% sine wave fundamental
SAW_RATIO = 0.2                 # 20% saw wave overtone brilliance

PORTAMENTO_GLIDE = 30.0         # +30 Hz upward micro-portamento
PORTAMENTO_RATE = 3.5           # Exponential rise rate factor

CHORUS_LFO_FREQ = 0.3           # 0.3 Hz warm chorus LFO
CHORUS_LFO_DEPTH = 0.006        # 0.6% detune depth

ATTACK_TIME = 0.065             # 65 ms gradual swell attack
SUSTAIN_TIME = 0.240            # 240 ms glorious sustain body
RELEASE_TIME = 0.160            # 160 ms warm release tail
RELEASE_DECAY_K = 3.0           # Exponential decay factor for release

LP_CUTOFF_HZ = 2400.0           # 2-pole low-pass filter cutoff frequency (Hz)
LP_RESONANCE_Q = 0.7071         # Butterworth Q factor (maximally flat passband)

TARGET_PEAK_AMPLITUDE = 25000.0 # -2.35 dB headroom (target range 24000-26000)


# ==============================================================================
# PART 4: 2-POLE BIQUAD DIGITAL FILTER (C++ Butterworth Biquad Equivalent)
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

        # Normalize filter coefficients by a0
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
# PART 5: IN-MEMORY RIFF WAV PACKER HELPER (C++ 44-Byte Header Equivalent)
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
# PART 6: CORE SYNTHESIS FUNCTION & STANDARDIZED CONTROL METHODS
# ==============================================================================
def create_revive_sfx(
    duration: float = DEFAULT_DURATION,
    volume: float = 1.0
) -> Sound:
    """
    Synthesizes the triumphant F-major organ triad resurrection swell into a ready-to-play
    Raylib Sound struct.

    Parameters:
      duration : Total length in seconds (default: 0.465s = 465ms)
      volume   : Master amplitude gain multiplier (0.0 to 1.0)

    Returns:
      Raylib Sound handle resident in audio hardware memory.
    """
    total_samples = int(SAMPLE_RATE * duration)
    attack_samples = int(SAMPLE_RATE * ATTACK_TIME)
    sustain_end_sample = int(SAMPLE_RATE * (ATTACK_TIME + SUSTAIN_TIME))
    release_samples = max(1, total_samples - sustain_end_sample)
    exp_neg_k = math.exp(-RELEASE_DECAY_K)

    lp_filter = BiquadLowPass2Pole(SAMPLE_RATE, LP_CUTOFF_HZ, LP_RESONANCE_Q)

    phases = [0.0, 0.0, 0.0, 0.0]
    unfiltered_samples = []

    for i in range(total_samples):
        t = float(i) / float(SAMPLE_RATE)
        progress = float(i) / float(total_samples)

        # 1. Micro-portamento: Uplifting upward glide (+30.0 Hz) during the swell
        portamento = PORTAMENTO_GLIDE * (1.0 - math.exp(-PORTAMENTO_RATE * progress))

        # 2. 3-Stage Amplitude Envelope (Attack -> Sustain -> Release)
        if i < attack_samples:
            p_att = float(i) / float(attack_samples)
            envelope = math.sin(0.5 * math.pi * p_att)
        elif i < sustain_end_sample:
            envelope = 1.0
        else:
            p_rel = float(i - sustain_end_sample) / float(release_samples)
            p_rel = max(0.0, min(1.0, p_rel))
            envelope = (math.exp(-RELEASE_DECAY_K * p_rel) - exp_neg_k) / (1.0 - exp_neg_k)

        # 3. Synthesize each of the 4 voices in the F-major organ triad (F4, A4, C5, F5)
        chord_signal = 0.0
        for v in range(4):
            base_freq = TRIAD_FREQUENCIES[v]
            # Chorus LFO: 0.3 Hz with quarter-phase stagger for rich ensemble flutter
            voice_chorus_phase = float(v) * (0.5 * math.pi)
            chorus_mod = math.sin(PI2 * CHORUS_LFO_FREQ * t + voice_chorus_phase) * CHORUS_LFO_DEPTH
            voice_freq = (base_freq + portamento) * (1.0 + chorus_mod)

            phases[v] += PI2 * voice_freq / float(SAMPLE_RATE)

            # Waveform: 80% sine + 20% saw wave
            phase_v = phases[v]
            sine_val = math.sin(phase_v)
            saw_norm = (phase_v / PI2) % 1.0
            saw_val = 2.0 * saw_norm - 1.0
            voice_signal = (SINE_RATIO * sine_val) + (SAW_RATIO * saw_val)
            chord_signal += voice_signal

        # 4. Mix voices and apply amplitude envelope
        mixed_signal = (chord_signal * 0.25) * envelope

        # 5. Apply 2-pole low-pass Butterworth filter @ 2400 Hz
        filtered_val = lp_filter.process(mixed_signal)
        unfiltered_samples.append(filtered_val)

    # 6. Peak amplitude headroom normalization (-2.35 dB headroom)
    max_amp = 0.0
    for s in unfiltered_samples:
        abs_s = abs(s)
        if abs_s > max_amp:
            max_amp = abs_s

    gain = (TARGET_PEAK_AMPLITUDE / max_amp) * max(0.0, min(1.0, volume)) if max_amp > 1e-6 else 1.0

    # 7. Pack into signed 16-bit PCM buffer and load into Raylib Sound
    pcm_samples = []
    for s in unfiltered_samples:
        scaled = s * gain
        clamped = max(-32767, min(32767, int(scaled)))
        pcm_samples.append(clamped)

    wav_bytes = pack_riff_wav_mono_16bit(SAMPLE_RATE, pcm_samples)
    wave = load_wave_from_memory(".wav", wav_bytes, len(wav_bytes))
    sound = load_sound_from_wave(wave)
    unload_wave(wave)
    return sound


# Standardized alias mapping for dynamic discovery
create_sfx = create_revive_sfx


def play_sfx(sound: Sound, volume: float = 1.0, pitch: float = 1.0) -> None:
    """Plays the revive sound effect with explicit volume and pitch scaling."""
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
# PART 7: STANDALONE AUDITION WORKBENCH & VISUALIZER
# ==============================================================================
class SFXAuditionApp:
    """
    Interactive sound previewer workbench allowing developers and students
    to audition the revive sound effect with live parameter controls and telemetry.
    """
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        init_window(
            self.screen_width,
            self.screen_height,
            "SFX Workbench - Revive Resurrection Swell (assets/audio/SFX/progression/revive.py)"
        )
        set_target_fps(60)
        init_audio_device()

        self.sound = create_revive_sfx()
        self.trigger_pulse = 0.0
        self.volume = 0.90
        self.pitch = 1.0
        self.trigger_count = 0
        self.show_xray = False
        self.anim_time = 0.0

        # Radiant ascending feather and soul spark particles
        self.particles = []
        for _ in range(36):
            self.particles.append({
                "x": 0.0, "y": 0.0, "vx": 0.0, "vy": 0.0,
                "life": 0.0, "max_life": 1.0, "size": 3.0, "hue_type": 0
            })

    def trigger(self):
        """Triggers sound playback with current pitch/volume and animates visualizer."""
        play_sfx(self.sound, self.volume, self.pitch)
        self.trigger_pulse = 1.0
        self.trigger_count += 1

        cx, cy = 853.0, 280.0
        import random
        for idx, p in enumerate(self.particles):
            ang = random.uniform(0.0, PI2)
            dist = random.uniform(5.0, 50.0)
            p["x"] = cx + math.cos(ang) * dist
            p["y"] = cy + math.sin(ang) * dist
            p["vx"] = random.uniform(-65.0, 65.0)
            p["vy"] = -random.uniform(70.0, 210.0)  # Strong upward ascent
            p["life"] = 1.0
            p["max_life"] = random.uniform(0.45, 0.95)
            p["size"] = random.uniform(3.0, 6.5)
            p["hue_type"] = idx % 3  # 0: Gold, 1: Celestial Amber, 2: Cyan

    def update(self):
        dt = min(get_frame_time(), 0.05)
        self.anim_time += dt

        if self.trigger_pulse > 0.0:
            self.trigger_pulse = max(0.0, self.trigger_pulse - dt * 2.2)

        for p in self.particles:
            if p["life"] > 0.0:
                p["life"] = max(0.0, p["life"] - dt / p["max_life"])
                p["x"] += p["vx"] * dt
                p["y"] += p["vy"] * dt
                p["vy"] += 20.0 * dt

        gamepad_trigger = False
        if is_gamepad_available(0):
            if (is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_FACE_DOWN) or
                is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_TRIGGER_1) or
                is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_TRIGGER_2)):
                gamepad_trigger = True

        if is_key_pressed(KEY_SPACE) or is_mouse_button_pressed(MOUSE_BUTTON_LEFT) or gamepad_trigger:
            self.trigger()

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

        if is_key_pressed(KEY_RIGHT):
            self.volume = min(1.0, self.volume + 0.05)
        elif is_key_pressed(KEY_LEFT):
            self.volume = max(0.0, self.volume - 0.05)

        reset_pressed = is_key_pressed(KEY_R)
        if is_gamepad_available(0) and is_gamepad_button_pressed(0, GAMEPAD_BUTTON_MIDDLE_RIGHT):
            reset_pressed = True
        if reset_pressed:
            self.pitch = 1.0
            self.volume = 0.90

        tab_pressed = is_key_pressed(KEY_TAB) or is_key_pressed(KEY_F1)
        if is_gamepad_available(0) and is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_FACE_UP):
            tab_pressed = True
        if tab_pressed:
            self.show_xray = not self.show_xray

    def draw(self):
        begin_drawing()
        clear_background(Color(12, 16, 24, 255))

        # Header (clear area maintained at x=450..980, y=14..48 for settings bar)
        draw_text("PROCEDURAL SFX AUDITION WORKBENCH", 24, 18, 20, RAYWHITE)
        draw_text("Asset: assets/audio/SFX/progression/revive.py | F-Major Organ Triad Swell", 24, 46, 13, GOLD)

        # Control Panel (Left)
        panel_y, panel_w, panel_h = 90, 400, 240
        draw_rectangle(24, panel_y, panel_w, panel_h, Color(18, 24, 36, 255))
        draw_rectangle_lines(24, panel_y, panel_w, panel_h, Color(60, 80, 120, 255))

        draw_text("INTERACTIVE CONTROLS & SHORTCUTS", 40, panel_y + 14, 15, YELLOW)
        draw_text("- [Space] / [Left Click] / Gamepad [A] : Trigger Revive SFX", 40, panel_y + 42, 13, RAYWHITE)
        draw_text("- [Up] / [Down] Arrows / D-Pad         : Adjust Pitch (+/- 0.1x)", 40, panel_y + 68, 13, RAYWHITE)
        draw_text("- [Left] / [Right] Arrows              : Adjust Volume (+/- 0.05)", 40, panel_y + 94, 13, RAYWHITE)
        draw_text("- [R] Key / Gamepad [Start]            : Reset Pitch & Volume", 40, panel_y + 120, 13, RAYWHITE)
        draw_text("- [Tab] / [F1] / Gamepad [Y]           : Toggle X-Ray Telemetry", 40, panel_y + 146, 13, SKYBLUE)

        draw_text(f"Current Pitch    : {self.pitch:.1f}x", 40, panel_y + 178, 13, GOLD)
        draw_text(f"Current Volume   : {self.volume:.2f}", 40, panel_y + 198, 13, GOLD)
        draw_text(f"Total Triggers   : {self.trigger_count}", 40, panel_y + 218, 13, LIGHTGRAY)

        # Parameter Specification Card
        card_y, card_h = panel_y + panel_h + 16, 320
        draw_rectangle(24, card_y, panel_w, card_h, Color(16, 20, 30, 255))
        draw_rectangle_lines(24, card_y, panel_w, card_h, Color(50, 70, 100, 255))
        draw_text("SYNTHESIS SPECIFICATION & ARCHITECTURE", 40, card_y + 14, 14, SKYBLUE)

        specs = [
            ("Catalog ID", "sfx_prog_revive"),
            ("Organ Voicing", "F4 (349.23), A4 (440), C5 (523.25), F5 (698.46)"),
            ("Waveform Mix", "80% Sine + 20% Sawtooth Blended Pipes"),
            ("Portamento", "+30.0 Hz Uplifting Micro-Glide"),
            ("Chorus LFO", "0.3 Hz Slow Ensemble Flutter (phi=v*pi/2)"),
            ("Envelope Attack", "65 ms Sinusoidal Ease-in Swell"),
            ("Envelope Sustain", "240 ms Glorious Resonant Body"),
            ("Envelope Release", "160 ms Warm Exponential Tail (k=3.0)"),
            ("Total Duration", "465 ms (20,506 samples @ 44.1 kHz)"),
            ("Low-Pass Filter", "2-pole Butterworth Biquad @ 2400 Hz"),
            ("Peak Amplitude", "~25,000 (-2.35 dB Headroom)"),
            ("Container", "In-Memory 44-byte RIFF/WAV -> Sound")
        ]
        line_offset = card_y + 40
        for label, val in specs:
            draw_text(f"{label:<17}:", 40, line_offset, 12, GRAY)
            draw_text(val, 185, line_offset, 12, RAYWHITE)
            line_offset += 22

        # Visualizer Workbench (Right)
        vis_x, vis_y, vis_w, vis_h = 450, 90, 806, 576
        draw_rectangle(vis_x, vis_y, vis_w, vis_h, Color(14, 18, 28, 255))
        draw_rectangle_lines(vis_x, vis_y, vis_w, vis_h, Color(60, 80, 120, 255))

        draw_text("RESURRECTION HALO & WINGS VISUALIZER", vis_x + 20, vis_y + 16, 15, GOLD)
        draw_text("F-Major Organ Triad Swell Simulation with 0.3 Hz Ensemble Flutter", vis_x + 20, vis_y + 38, 12, GRAY)

        center_x = vis_x + (vis_w // 2)
        center_y = vis_y + 185

        # 1. Angel / Phoenix Wings
        wing_spread = 25.0 + self.trigger_pulse * 40.0
        wing_alpha = max(60, min(255, int(120 + self.trigger_pulse * 135)))
        for side in (-1, 1):
            for feather_idx in range(6):
                f_frac = float(feather_idx) / 5.0
                base_x, base_y = center_x + side * 22, center_y + 10
                mid_x = center_x + side * int(45 + feather_idx * 15 + wing_spread * 0.7)
                mid_y = center_y - int(20 + feather_idx * 14 + self.trigger_pulse * 25.0)
                tip_x = center_x + side * int(80 + feather_idx * 26 + wing_spread)
                tip_y = center_y - int(40 + feather_idx * 16 - (feather_idx ** 2) * 2 + self.trigger_pulse * 30.0)

                feather_color = Color(255, int(210 - f_frac * 60), int(100 + f_frac * 140), wing_alpha)
                draw_line(int(base_x), int(base_y), int(mid_x), int(mid_y), feather_color)
                draw_line(int(mid_x), int(mid_y), int(tip_x), int(tip_y), feather_color)
                draw_circle(int(tip_x), int(tip_y), 3.0 + self.trigger_pulse * 2.0, feather_color)

        # 2. Concentric Golden-Cyan Halo
        halo_radius = 42.0 + (self.trigger_pulse * 55.0)
        halo_alpha = max(0, min(255, int(self.trigger_pulse * 180)))
        draw_circle(center_x, center_y, halo_radius * 1.5, Color(50, 160, 240, halo_alpha // 5))
        draw_circle(center_x, center_y, halo_radius, Color(255, 215, 80, halo_alpha // 4))
        draw_circle_lines(center_x, center_y, halo_radius, Color(255, 220, 100, max(80, halo_alpha)))
        draw_circle_lines(center_x, center_y, halo_radius * 0.75, Color(100, 220, 255, max(80, halo_alpha)))
        draw_circle(center_x, center_y, 14.0 + self.trigger_pulse * 10.0, Color(255, 245, 180, 230))

        # 3. Radiant Sunburst Rays
        num_rays = 12
        for r_idx in range(num_rays):
            ray_ang = self.anim_time * 0.5 + float(r_idx) * (PI2 / float(num_rays))
            ray_len = 45.0 + 20.0 * math.sin(self.anim_time * 3.0 + r_idx) + self.trigger_pulse * 45.0
            rx1 = center_x + int(math.cos(ray_ang) * (halo_radius + 4))
            ry1 = center_y + int(math.sin(ray_ang) * (halo_radius + 4))
            rx2 = center_x + int(math.cos(ray_ang) * (halo_radius + ray_len))
            ry2 = center_y + int(math.sin(ray_ang) * (halo_radius + ray_len))
            ray_col = Color(255, 225, 120, max(0, min(255, int(self.trigger_pulse * 190 + 35))))
            draw_line(rx1, ry1, rx2, ry2, ray_col)

        # 4. Radiant Ascending Particles
        for p in self.particles:
            if p["life"] > 0.0:
                p_alpha = max(0, min(255, int(p["life"] * 240)))
                p_col = Color(255, 220, 90, p_alpha) if p["hue_type"] == 0 else (
                    Color(255, 170, 60, p_alpha) if p["hue_type"] == 1 else Color(110, 230, 255, p_alpha)
                )
                draw_circle(int(p["x"]), int(p["y"]), p["size"] * (0.4 + 0.6 * p["life"]), p_col)

        # 5. Dynamic Amplitude Swell Bar
        meter_y, meter_w = vis_y + 340, vis_w - 40
        draw_rectangle(vis_x + 20, meter_y, meter_w, 20, Color(24, 32, 48, 255))
        draw_rectangle_lines(vis_x + 20, meter_y, meter_w, 20, Color(50, 70, 100, 255))
        active_meter = int(self.trigger_pulse * meter_w)
        draw_rectangle(vis_x + 20, meter_y, active_meter, 20, Color(255, 200, 60, 225))
        draw_text("AMPLITUDE SWELL & TRIAD RESONANCE", vis_x + 24, meter_y + 4, 11, RAYWHITE)

        # 6. Oscilloscope with Simulated Triad Waveform
        wave_y = vis_y + 445
        draw_line(vis_x + 20, wave_y, vis_x + vis_w - 20, wave_y, Color(40, 55, 80, 255))
        draw_text("OSCILLOSCOPE: F-MAJOR ORGAN TRIAD WAVEFORM (SINE-SAW 80/20 MIX)", vis_x + 20, wave_y - 65, 12, SKYBLUE)

        prev_pt_x, prev_pt_y = vis_x + 20, wave_y
        steps = 140
        for s in range(steps):
            t_frac = float(s) / float(steps - 1)
            pt_x = vis_x + 20 + int(t_frac * (vis_w - 40))

            # Envelope evaluation
            if t_frac < 0.14:
                env = math.sin(0.5 * math.pi * (t_frac / 0.14))
            elif t_frac < 0.656:
                env = 1.0
            else:
                p_r = (t_frac - 0.656) / 0.344
                env = (math.exp(-3.0 * p_r) - math.exp(-3.0)) / (1.0 - math.exp(-3.0))

            # Organ triad synthesis preview
            t_sim = t_frac * DEFAULT_DURATION
            p_glide = 30.0 * (1.0 - math.exp(-3.5 * t_frac))
            s_triad = 0.0
            for idx_f, f_base in enumerate(TRIAD_FREQUENCIES):
                mod_c = math.sin(PI2 * 0.3 * t_sim + idx_f * 0.5 * math.pi) * 0.006
                f_inst = (f_base + p_glide) * (1.0 + mod_c) * self.pitch
                phi = PI2 * f_inst * t_sim
                s_sine = math.sin(phi)
                s_saw = 2.0 * ((phi / PI2) % 1.0) - 1.0
                s_triad += 0.8 * s_sine + 0.2 * s_saw

            wave_amp = (s_triad * 0.25) * env * (24.0 + self.trigger_pulse * 36.0)
            pt_y = int(wave_y - wave_amp)
            draw_line(prev_pt_x, prev_pt_y, pt_x, pt_y, Color(255, 215, 80, 230))
            prev_pt_x, prev_pt_y = pt_x, pt_y

        # Envelope segment markers
        x_att = vis_x + 20 + int((0.065 / 0.465) * (vis_w - 40))
        x_sus = vis_x + 20 + int(((0.065 + 0.240) / 0.465) * (vis_w - 40))
        draw_line(x_att, wave_y - 45, x_att, wave_y + 45, Color(120, 160, 220, 180))
        draw_line(x_sus, wave_y - 45, x_sus, wave_y + 45, Color(120, 160, 220, 180))
        draw_text("Attack: 65ms (Swell)", vis_x + 22, wave_y + 48, 11, YELLOW)
        draw_text("Sustain: 240ms (F-Major Triad)", x_att + 6, wave_y + 48, 11, GOLD)
        draw_text("Release: 160ms (Tail k=3.0)", x_sus + 6, wave_y + 48, 11, SKYBLUE)

        # 7. X-Ray Telemetry Overlay
        if self.show_xray:
            ox, oy, ow, oh = vis_x + 20, vis_y + 60, vis_w - 40, 265
            draw_rectangle(ox, oy, ow, oh, Color(10, 14, 22, 245))
            draw_rectangle_lines(ox, oy, ow, oh, Color(255, 215, 80, 255))
            draw_text("X-RAY TELEMETRY: RESURRECTION SYNTHESIS EQUATIONS", ox + 16, oy + 12, 14, YELLOW)

            eqs = [
                "1. F-Major Triad Voicing : F4(349.23 Hz), A4(440.00 Hz), C5(523.25 Hz), F5(698.46 Hz)",
                "2. Blended Pipe Waveform : s_v(t) = 0.8 * sin(phi) + 0.2 * [2.0 * ((phi / 2pi) % 1.0) - 1.0]",
                "3. Upward Micro-Portamento: delta_f(t) = 30.0 * [1.0 - exp(-3.5 * t / 0.465)]",
                "4. Warm Ensemble Chorus  : f_v(t) = (f_base + delta_f) * [1.0 + 0.006 * sin(2pi * 0.3 * t + v * pi/2)]",
                "5. 2-Pole Butterworth LPF: Cutoff = 2400 Hz, Q = 0.7071 (RBJ Biquad Difference Equation)",
                "6. 3-Stage Amplitude Env : Attack(65ms) sin-ramp -> Sustain(240ms) 1.0 -> Release(160ms) exp(-3.0*p)",
                "7. Headroom Scaling      : Peak amplitude scaled to 25,000 / 32,767 (~-2.35 dB Headroom)"
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
