# -*- coding: utf-8 -*-
import sys
sys.dont_write_bytecode = True

"""
Procedural Debuff Sound Effect (SFX) Synthesizer
================================================
Type             : Procedural Audio SFX (Sound)
Target File      : assets/audio/SFX/progression/debuff.py
Waveforms Used   : Harsh sawtooth glissando with 9 Hz FM flutter and 2-pole resonant LPF
Category         : Progression & Economy (Status Affliction, Poison, Armor Debuff, Slow, Curse)
Catalog ID       : sfx_prog_debuff
Function Name    : create_debuff_sfx

Problem Solved:
  Eliminates external .wav/.mp3 dependencies by synthesizing an ominous, biting status
  affliction warning sound purely from mathematical waveforms in RAM into a 16-bit mono
  PCM buffer, loading directly into a Raylib Sound struct with zero runtime file I/O.

Waveform Theory & Mathematical Rationale:
  - Descending Tritone Glissando (Diabolus in Musica):
    Carrier base frequency begins on A4 (440.0 Hz), descends through the tritone
    midpoint Eb4 (311.13 Hz), and settles on A3 (220.0 Hz) over 260 ms:
      Interval 1: A4 (440.0 Hz) down to Eb4 (311.13 Hz) -> Diminished 5th (tritone, 6 semitones)
      Interval 2: Eb4 (311.13 Hz) down to A3 (220.0 Hz) -> Diminished 5th (tritone, 6 semitones)
    The diminished fifth has historically evoked dread, instability, and impending doom.
    Spanning exactly one octave through two symmetric tritones creates an unsettling
    downward trajectory signaling weakening, affliction, or vulnerability.
  
  - Continuous Exponential Frequency Trajectory:
    Because two equal tritone intervals divide an octave in half in equal temperament:
      f_ratio = 220.0 / 440.0 = 0.5 = 2^(-1)
      f(t) = f_start * (f_end / f_start) ** (t / duration)
    At t = 0.0s    : f(0.0)   = 440.00 Hz (A4)
    At t = 0.130s  : f(0.130) = 440.00 * (0.5)^0.5 = 311.13 Hz (Eb4)
    At t = 0.260s  : f(0.260) = 440.00 * (0.5)^1.0 = 220.00 Hz (A3)
    This yields a continuous, mathematically rigorous logarithmic pitch slide.

  - Aggressive 9 Hz Frequency Modulation Flutter:
    A low-frequency oscillator at f_m = 9.0 Hz modulates the carrier phase with
    modulation index beta = 0.6:
      phi_mod(t) = phi_carrier(t) + beta * sin(2 * pi * 9.0 * t)
    This phase modulation introduces rapid frequency flutter sidebands, giving the
    glissando a trembling, sickly, unstable affliction shudder.

  - Harsh Sawtooth Waveform:
    A geometric sawtooth wave is generated via normalized phase wrapping:
      saw(phi) = 2.0 * (phi / (2 * pi) mod 1.0) - 1.0
    The sawtooth wave contains all integer harmonics (1/n amplitude falloff),
    providing the raw metallic bite and buzzing aggression needed for a warning cue.

  - Resonant Low-Pass Filter with 450 Hz Spike (Q = 3.5):
    A 2-pole digital biquad low-pass filter with cutoff f_c = 450 Hz and quality factor
    Q = 3.5 introduces a sharp +10.9 dB resonance spike right around A4 (440 Hz):
      H(s) = w0^2 / (s^2 + (w0 / Q)*s + w0^2)
    As the sawtooth descends from 440 Hz to 220 Hz, its fundamental and lower harmonics
    sweep directly across this resonant peak, producing an eerie, hollow, vocal-like
    throaty rasp that darkens into a murky rumble.

  - 3-Stage Amplitude Envelope:
    - Attack (0 to 4 ms)      : Rapid 4 ms sinusoidal ease-in avoiding click artifacts.
    - Sustain (4 to 174 ms)   : 170 ms steady descending sustain body carrying the tritone.
    - Release (174 to 260 ms) : 86 ms steep exponential decay (k = 5.5):
        env(t) = exp(-5.5 * (t - t_sus) / t_rel)
      normalized to terminate exactly at zero.

  - Headroom & Clamping:
    Filtered samples are normalized to peak at ~25,000 (-2.35 dB headroom) and strictly
    clamped to signed 16-bit PCM integer range [-32767, 32767].

Direct C++ Raylib Translation (raylib.h):
  struct DebuffSFX {
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
# PART 2: PATH SETUP & RAYLIB IMPORTS
# ==============================================================================
import os
import math
import struct as py_struct  # Aliased to prevent collision with pyray.struct

# Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# Add repository root to search path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

# Mandatory Raylib and utility imports
from pyray import *
from utils import *

# ==============================================================================
# PART 3: AUDIO SYNTHESIS CONSTANTS
# ==============================================================================
SAMPLE_RATE = 44100
PI2 = 2.0 * math.pi

# Time durations (total 260 ms = 4 ms + 170 ms + 86 ms)
DEFAULT_DURATION = 0.260       # 260 ms total duration
ATTACK_TIME = 0.004            # 4 ms fast attack
SUSTAIN_TIME = 0.170           # 170 ms steady descending sustain
RELEASE_TIME = 0.086           # 86 ms exponential decay
RELEASE_DECAY_K = 5.5          # Exponential decay steepness factor

# Tritone glissando carrier frequencies (A4 -> Eb4 -> A3)
START_FREQUENCY = 440.00       # A4 in Hz
MID_FREQUENCY = 311.13         # Eb4 in Hz (tritone midpoint: diminished 5th)
END_FREQUENCY = 220.00         # A3 in Hz (one octave down)

# FM Flutter modulation parameters
FM_FLUTTER_FREQ = 9.0          # 9 Hz LFO flutter rate
FM_MOD_INDEX = 0.6             # Modulation index beta = 0.6

# 2-Pole Resonant Low-Pass Filter parameters
LP_CUTOFF_HZ = 450.0           # 450 Hz cutoff frequency
LP_RESONANCE_Q = 3.5           # Q = 3.5 (+10.9 dB resonant spike)

# Headroom scaling
TARGET_PEAK_AMPLITUDE = 25000.0  # -2.35 dB headroom (peak target 25,000 / 32,767)


# ==============================================================================
# PART 4: 2-POLE BIQUAD RESONANT FILTER (C++ RBJ Cookbook Biquad Equivalent)
# ==============================================================================
class BiquadResonantLowPass:
    """
    Direct C++ transferable 2-pole biquad resonant low-pass filter (RBJ design).
    C++ Equivalent:
      struct BiquadResonantLowPass {
          float b0, b1, b2, a1, a2;
          float x1 = 0.0f, x2 = 0.0f, y1 = 0.0f, y2 = 0.0f;
          void Init(float sampleRate, float cutoffHz, float q);
          float Process(float inSample);
      };
    """
    def __init__(self, sample_rate: int, cutoff_hz: float, q: float = 3.5):
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

        # Delay history registers
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
# PART 5: IN-MEMORY RIFF WAV CONTAINER PACKER (C++ 44-Byte Header Equivalent)
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
    audio_format = 1        # Standard PCM
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
# PART 6: CORE SYNTHESIS FUNCTION & STANDARDIZED API
# ==============================================================================
def create_debuff_sfx(
    duration: float = DEFAULT_DURATION,
    start_freq: float = START_FREQUENCY,
    mid_freq: float = MID_FREQUENCY,
    end_freq: float = END_FREQUENCY,
    volume: float = 1.0
) -> Sound:
    """
    Synthesizes the descending tritone status debuff warning sound effect into a
    ready-to-play Raylib Sound handle resident in audio memory.

    Parameters:
      duration   : Total duration in seconds (default: 0.260s = 260ms)
      start_freq : Starting frequency in Hz (default: 440.0 Hz A4)
      mid_freq   : Tritone midpoint frequency in Hz (default: 311.13 Hz Eb4)
      end_freq   : Settling frequency in Hz (default: 220.0 Hz A3)
      volume     : Master gain multiplier (0.0 to 1.0)

    Returns:
      Raylib Sound handle resident in audio memory.
    """
    total_samples = int(SAMPLE_RATE * duration)

    # Envelope sample boundary indices
    attack_samples = max(1, int(SAMPLE_RATE * ATTACK_TIME))
    sustain_end_sample = int(SAMPLE_RATE * (ATTACK_TIME + SUSTAIN_TIME))
    release_samples = max(1, total_samples - sustain_end_sample)
    exp_neg_k = math.exp(-RELEASE_DECAY_K)

    # Initialize 2-pole resonant low-pass filter
    lp_filter = BiquadResonantLowPass(SAMPLE_RATE, LP_CUTOFF_HZ, LP_RESONANCE_Q)

    carrier_phase = 0.0
    unfiltered_samples = []

    for i in range(total_samples):
        t = float(i) / float(SAMPLE_RATE)
        progress = float(i) / float(total_samples)

        # 1. Continuous Tritone Glissando Frequency Trajectory (A4 -> Eb4 -> A3)
        if progress < 0.5:
            p_sub = progress / 0.5
            current_freq = start_freq * math.pow(mid_freq / start_freq, p_sub)
        else:
            p_sub = (progress - 0.5) / 0.5
            current_freq = mid_freq * math.pow(end_freq / mid_freq, p_sub)

        # 2. Advance Carrier Phase with Base Glissando Frequency
        carrier_phase += PI2 * current_freq / float(SAMPLE_RATE)

        # 3. 9 Hz Frequency Modulation Flutter with Index 0.6
        # Phase modulation adds aggressive instability flutter sidebands
        flutter_lfo = math.sin(PI2 * FM_FLUTTER_FREQ * t)
        flutter_phase = carrier_phase + (FM_MOD_INDEX * flutter_lfo)

        # 4. Generate Harsh Sawtooth Waveform from Modulated Phase
        # Normalized phase wrapped to [0.0, 1.0) -> scaled to [-1.0, 1.0]
        norm_phase = (flutter_phase / PI2) % 1.0
        raw_saw = 2.0 * norm_phase - 1.0

        # 5. 3-Stage Amplitude Envelope (Attack -> Sustain -> Exponential Release)
        if i < attack_samples:
            # 4 ms soft sinusoidal ease-in ramp to prevent edge clicking
            p_att = float(i) / float(attack_samples)
            envelope = math.sin(0.5 * math.pi * p_att)
        elif i < sustain_end_sample:
            # 170 ms steady descending sustain body
            p_sus = float(i - attack_samples) / float(sustain_end_sample - attack_samples)
            envelope = 1.0 - (0.08 * p_sus)  # Gentle 8% descending contour
        else:
            # 86 ms steep exponential decay (k = 5.5) terminating at 0.0
            p_rel = float(i - sustain_end_sample) / float(release_samples)
            exp_term = math.exp(-RELEASE_DECAY_K * p_rel)
            envelope = 0.92 * ((exp_term - exp_neg_k) / (1.0 - exp_neg_k))

        # 6. Apply Amplitude Envelope
        enveloped_sample = raw_saw * envelope

        # 7. Apply 2-Pole Resonant Low-Pass Filter (Cutoff = 450 Hz, Q = 3.5)
        filtered_sample = lp_filter.process(enveloped_sample)
        unfiltered_samples.append(filtered_sample)

    # 8. Normalize Peak Amplitude to ~25,000 (-2.35 dB headroom) and apply volume
    max_amp = 0.0
    for s in unfiltered_samples:
        abs_s = abs(s)
        if abs_s > max_amp:
            max_amp = abs_s

    if max_amp > 1e-6:
        gain = (TARGET_PEAK_AMPLITUDE / max_amp) * max(0.0, min(1.0, volume))
    else:
        gain = 1.0

    # 9. Clamp to 16-Bit Signed Integer Range [-32767, 32767]
    pcm_samples = []
    for s in unfiltered_samples:
        scaled_val = s * gain
        clamped_val = max(-32767, min(32767, int(scaled_val)))
        pcm_samples.append(clamped_val)

    # 10. Pack into Memory RIFF/WAV Container and Load into Raylib Sound
    wav_bytes = pack_riff_wav_mono_16bit(SAMPLE_RATE, pcm_samples)
    wave = load_wave_from_memory(".wav", wav_bytes, len(wav_bytes))
    sound = load_sound_from_wave(wave)
    unload_wave(wave)  # Free CPU Wave struct; audio hardware retains PCM Sound handle
    return sound


# Standardized alias mapping for dynamic discovery
create_sfx = create_debuff_sfx


# ==============================================================================
# STANDARDIZED PLAYBACK CONTROL METHODS
# ==============================================================================
def play_sfx(sound: Sound, volume: float = 1.0, pitch: float = 1.0) -> None:
    """Plays the debuff affliction sound effect with explicit volume and pitch scaling."""
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
# PART 7: STANDALONE AUDITION WORKBENCH & AUTOMATED SMOKE TEST
# ==============================================================================
class SFXAuditionApp:
    """
    Interactive sound previewer workbench allowing developers and students
    to audition the debuff sound effect with live parameter controls, visual
    affliction telemetry, and oscilloscope display.
    """
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        init_window(
            self.screen_width,
            self.screen_height,
            "SFX Workbench - Debuff Affliction Glissando (assets/audio/SFX/progression/debuff.py)"
        )
        set_target_fps(60)
        init_audio_device()

        self.sound = create_debuff_sfx()
        self.trigger_pulse = 0.0
        self.volume = 0.85
        self.pitch = 1.0
        self.trigger_count = 0
        self.show_xray = False

        # Affliction miasma particles for curse visualizer
        self.particles = []
        for _ in range(36):
            self.particles.append({
                "x": 0.0,
                "y": 0.0,
                "vx": 0.0,
                "vy": 0.0,
                "life": 0.0,
                "max_life": 1.0,
                "size": 3.0,
                "color_type": 0
            })

    def trigger(self):
        """Triggers sound playback with current pitch/volume and animates curse burst."""
        play_sfx(self.sound, self.volume, self.pitch)
        self.trigger_pulse = 1.0
        self.trigger_count += 1

        # Spawn necrotic affliction particles drifting downwards
        cx = 853.0
        cy = 280.0
        import random
        for idx, p in enumerate(self.particles):
            ang = random.uniform(0.0, PI2)
            spd = random.uniform(30.0, 150.0)
            p["x"] = cx + math.cos(ang) * random.uniform(8.0, 48.0)
            p["y"] = cy + math.sin(ang) * random.uniform(8.0, 48.0)
            p["vx"] = math.cos(ang) * spd
            p["vy"] = math.sin(ang) * spd + random.uniform(35.0, 95.0)  # Downward affliction drift
            p["life"] = 1.0
            p["max_life"] = random.uniform(0.45, 0.85)
            p["size"] = random.uniform(3.0, 7.0)
            p["color_type"] = idx % 2  # 0: Curse Purple, 1: Miasma Green

    def update(self):
        dt = min(get_frame_time(), 0.05)
        if self.trigger_pulse > 0.0:
            self.trigger_pulse = max(0.0, self.trigger_pulse - dt * 3.2)

        # Update affliction particles
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

        # Toggle X-Ray Telemetry Overlay: Tab / F1 / Gamepad Y
        tab_pressed = is_key_pressed(KEY_TAB) or is_key_pressed(KEY_F1)
        if is_gamepad_available(0) and is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_FACE_UP):
            tab_pressed = True
        if tab_pressed:
            self.show_xray = not self.show_xray

    def draw(self):
        begin_drawing()
        clear_background(Color(16, 12, 20, 255))

        # Header (keeps top-bar region x=450..980, y=14..48 clear for UI settings bar)
        draw_text("PROCEDURAL SFX AUDITION WORKBENCH", 24, 18, 20, RAYWHITE)
        draw_text("Asset: assets/audio/SFX/progression/debuff.py | Descending Tritone Affliction Slide", 24, 46, 13, Color(220, 80, 100, 255))

        # ======================================================================
        # LEFT CONTROL PANEL (x=24, y=90, w=400)
        # ======================================================================
        panel_y = 90
        panel_w = 400
        panel_h = 240
        draw_rectangle(24, panel_y, panel_w, panel_h, Color(24, 16, 30, 255))
        draw_rectangle_lines(24, panel_y, panel_w, panel_h, Color(80, 40, 95, 255))

        draw_text("INTERACTIVE CONTROLS & SHORTCUTS", 40, panel_y + 14, 15, YELLOW)
        draw_text("- [Space] / [Left Click] / Gamepad [A] : Trigger Debuff SFX", 40, panel_y + 42, 13, RAYWHITE)
        draw_text("- [Up] / [Down] Arrows / D-Pad         : Adjust Pitch (+/- 0.1x)", 40, panel_y + 68, 13, RAYWHITE)
        draw_text("- [Left] / [Right] Arrows              : Adjust Volume (+/- 0.05)", 40, panel_y + 94, 13, RAYWHITE)
        draw_text("- [R] Key / Gamepad [Start]            : Reset Pitch & Volume", 40, panel_y + 120, 13, RAYWHITE)
        draw_text("- [Tab] / [F1] / Gamepad [Y]           : Toggle X-Ray Telemetry", 40, panel_y + 146, 13, Color(210, 120, 240, 255))

        draw_text(f"Current Pitch    : {self.pitch:.1f}x", 40, panel_y + 178, 13, Color(240, 120, 140, 255))
        draw_text(f"Current Volume   : {self.volume:.2f}", 40, panel_y + 198, 13, Color(240, 120, 140, 255))
        draw_text(f"Total Triggers   : {self.trigger_count}", 40, panel_y + 218, 13, LIGHTGRAY)

        # Parameter Specification Card (Below controls)
        card_y = panel_y + panel_h + 16
        card_h = 320
        draw_rectangle(24, card_y, panel_w, card_h, Color(20, 14, 26, 255))
        draw_rectangle_lines(24, card_y, panel_w, card_h, Color(65, 30, 80, 255))
        draw_text("SYNTHESIS SPECIFICATION & ARCHITECTURE", 40, card_y + 14, 14, Color(200, 130, 240, 255))

        specs = [
            ("Catalog ID", "sfx_prog_debuff"),
            ("Waveform", "Harsh sawtooth glissando + 9 Hz FM"),
            ("Start Pitch", "440.00 Hz (A4)"),
            ("Tritone Mid", "311.13 Hz (Eb4 - Diminished 5th)"),
            ("End Pitch", "220.00 Hz (A3 - Octave down)"),
            ("FM Flutter", "9.0 Hz LFO with index beta = 0.6"),
            ("Envelope Attack", "4 ms fast sinusoidal ease-in"),
            ("Envelope Sustain", "170 ms steady descending sustain"),
            ("Envelope Release", "86 ms steep exponential decay (k=5.5)"),
            ("Total Duration", "260 ms (11,466 samples @ 44.1 kHz)"),
            ("Filter Type", "2-pole resonant LPF @ 450 Hz (Q=3.5)"),
            ("Container", "In-Memory 44-byte RIFF/WAV -> Sound")
        ]
        line_offset = card_y + 40
        for label, val in specs:
            draw_text(f"{label:<17}:", 40, line_offset, 12, GRAY)
            draw_text(val, 185, line_offset, 12, RAYWHITE)
            line_offset += 22

        # ======================================================================
        # RIGHT VISUALIZER WORKBENCH (x=450, y=90, w=806)
        # ======================================================================
        vis_x = 450
        vis_y = 90
        vis_w = 806
        vis_h = 576
        draw_rectangle(vis_x, vis_y, vis_w, vis_h, Color(20, 14, 26, 255))
        draw_rectangle_lines(vis_x, vis_y, vis_w, vis_h, Color(80, 40, 95, 255))

        draw_text("AFFLICTION RUNE & TRITONE OSCILLOSCOPE", vis_x + 20, vis_y + 16, 15, Color(240, 90, 110, 255))
        draw_text("Tritone Glissando Simulation (A4 440 Hz -> Eb4 311.13 Hz -> A3 220 Hz + 9 Hz Flutter)", vis_x + 20, vis_y + 38, 12, GRAY)

        # Center affliction curse visualizer
        center_x = vis_x + (vis_w // 2)
        center_y = vis_y + 190

        # Pulsing Necrotic Curse Rune & Rings
        pulse_val = self.trigger_pulse
        curse_radius = 42.0 + (pulse_val * 58.0)
        glow_alpha = int(pulse_val * 160)

        # Outer poison aura glow
        draw_circle(center_x, center_y, curse_radius, Color(160, 40, 180, glow_alpha // 4))
        draw_circle_lines(center_x, center_y, curse_radius, Color(220, 60, 160, glow_alpha))
        draw_circle_lines(center_x, center_y, curse_radius * 0.75, Color(120, 220, 90, glow_alpha))

        # Inner afflicted diamond / skull motif
        poly_points = 6
        for step in range(poly_points):
            ang1 = (float(step) / float(poly_points)) * PI2 - (pulse_val * 0.4)
            ang2 = (float(step + 1) / float(poly_points)) * PI2 - (pulse_val * 0.4)
            r_outer = 22.0 + (pulse_val * 12.0)
            x1 = center_x + int(math.cos(ang1) * r_outer)
            y1 = center_y + int(math.sin(ang1) * r_outer)
            x2 = center_x + int(math.cos(ang2) * r_outer)
            y2 = center_y + int(math.sin(ang2) * r_outer)
            draw_line(x1, y1, x2, y2, Color(240, 80, 100, 220))

        draw_circle(center_x, center_y, 10.0 + (pulse_val * 6.0), Color(255, 60, 90, 240))

        # Draw descending miasma particles
        for p in self.particles:
            if p["life"] > 0.0:
                p_alpha = int(p["life"] * 240)
                if p["color_type"] == 0:
                    p_col = Color(190, 60, 220, p_alpha)  # Curse Purple
                else:
                    p_col = Color(90, 220, 110, p_alpha)  # Miasma Green
                draw_circle(
                    int(p["x"]),
                    int(p["y"]),
                    p["size"] * (0.4 + 0.6 * p["life"]),
                    p_col
                )

        # Amplitude envelope pulse meter
        meter_y = vis_y + 325
        meter_w = vis_w - 40
        draw_rectangle(vis_x + 20, meter_y, meter_w, 18, Color(28, 18, 36, 255))
        draw_rectangle_lines(vis_x + 20, meter_y, meter_w, 18, Color(75, 35, 90, 255))
        active_meter = int(pulse_val * meter_w)
        draw_rectangle(vis_x + 20, meter_y, active_meter, 18, Color(220, 60, 90, 220))
        draw_text("AMPLITUDE ENVELOPE DYNAMICS", vis_x + 24, meter_y + 3, 11, RAYWHITE)

        # Simulated Oscilloscope: Harsh Sawtooth Waveform with Tritone FM Flutter
        wave_y = vis_y + 440
        draw_line(vis_x + 20, wave_y, vis_x + vis_w - 20, wave_y, Color(50, 30, 60, 255))
        draw_text("OSCILLOSCOPE: HARSH SAWTOOTH + 9 Hz FM FLUTTER + 450 Hz RESONANCE", vis_x + 20, wave_y - 65, 12, Color(210, 130, 240, 255))

        prev_pt_x = vis_x + 20
        prev_pt_y = wave_y
        steps = 140
        for s in range(1, steps + 1):
            t = float(s) / float(steps)
            pt_x = vis_x + 20 + int(t * (vis_w - 40))

            # Descending frequency glide simulation (440 Hz down to 220 Hz)
            freq_factor = 1.0 - (0.5 * t)
            # 9 Hz FM flutter modulation
            flutter = 0.6 * math.sin(t * PI2 * 9.0 * 0.260 * 3.0)
            saw_phase = ((t * 18.0 * freq_factor * self.pitch + flutter) % 1.0)
            saw_wave = 2.0 * saw_phase - 1.0

            # Resonant harmonic ringing simulation
            res_ring = 0.35 * math.sin(t * 36.0 * freq_factor)

            # 3-Stage envelope contour
            if t < 0.015:  # 4 ms / 260 ms = ~0.015
                env = math.sin(0.5 * math.pi * (t / 0.015))
            elif t < 0.669:  # (4 + 170) / 260 = ~0.669
                env = 1.0 - 0.08 * ((t - 0.015) / 0.654)
            else:  # Release stage
                p_rel = (t - 0.669) / 0.331
                env = 0.92 * math.exp(-5.5 * p_rel)

            combined_wave = (saw_wave + res_ring) * env * (28.0 + pulse_val * 32.0)
            pt_y = int(wave_y - combined_wave)
            draw_line(prev_pt_x, prev_pt_y, pt_x, pt_y, Color(240, 75, 120, 220))
            prev_pt_x = pt_x
            prev_pt_y = pt_y

        # Envelope segment markers
        x_att = vis_x + 20 + int(0.015 * (vis_w - 40))
        x_sus = vis_x + 20 + int(0.669 * (vis_w - 40))
        draw_line(x_att, wave_y - 45, x_att, wave_y + 45, Color(120, 50, 80, 180))
        draw_line(x_sus, wave_y - 45, x_sus, wave_y + 45, Color(120, 50, 80, 180))
        draw_text("Attack: 4ms", vis_x + 22, wave_y + 48, 11, YELLOW)
        draw_text("Steady Sustain: 170ms", x_att + 6, wave_y + 48, 11, Color(240, 120, 140, 255))
        draw_text("Exponential Decay: 86ms (k=5.5)", x_sus + 6, wave_y + 48, 11, Color(210, 130, 240, 255))

        # X-Ray Telemetry Overlay (Toggled via Tab / F1 / Gamepad Y)
        if self.show_xray:
            ox = vis_x + 20
            oy = vis_y + 60
            ow = vis_w - 40
            oh = 250
            draw_rectangle(ox, oy, ow, oh, Color(12, 8, 16, 245))
            draw_rectangle_lines(ox, oy, ow, oh, Color(220, 70, 120, 255))
            draw_text("X-RAY TELEMETRY: MATHEMATICAL SYNTHESIS PIPELINE", ox + 16, oy + 12, 14, YELLOW)

            eqs = [
                "1. Tritone Glissando: f(p) = A4(440Hz) -> Eb4(311.13Hz) -> A3(220Hz) over 260ms",
                "2. Carrier Phase    : phi += 2*pi * f(t) / 44100",
                "3. 9 Hz FM Flutter  : phi_mod(t) = phi(t) + 0.6 * sin(2*pi * 9.0 * t)",
                "4. Harsh Sawtooth   : saw(phi) = 2 * (phi_mod / 2*pi mod 1.0) - 1.0",
                "5. Resonant Biquad  : 2-pole low-pass with cutoff fc=450 Hz, Q=3.5 (+10.9 dB peak)",
                "6. 3-Stage Envelope : Attack(4ms) sin -> Sustain(170ms) 1.0 -> Decay(86ms) exp(-5.5*p)",
                "7. Normalization    : Scaled to 25,000 / 32,767 (-2.35 dB headroom) -> 16-bit PCM"
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
