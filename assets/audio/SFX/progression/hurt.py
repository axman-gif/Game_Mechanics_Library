# -*- coding: utf-8 -*-
import sys
sys.dont_write_bytecode = True

"""
Procedural Hurt Sound Effect (SFX) Synthesizer
==============================================
Type             : Procedural Audio SFX (Sound)
Target File      : assets/audio/SFX/progression/hurt.py
Waveforms Used   : Descending distorted triangle vocal grunt + dissonant minor-second sine clash + low-pass noise burst
Category         : Progression & Feedback (Player Damage Received, Health Depletion, Vitality Loss)
Catalog ID       : sfx_prog_hurt
Function Name    : create_hurt_sfx

Problem Solved:
  Eliminates external .wav/.mp3 dependencies by synthesizing a visceral, jarring damage-received
  impact cue entirely from mathematical waveforms into an in-memory 16-bit PCM buffer, loading
  directly into a Raylib Sound struct with zero runtime file I/O.

Waveform Theory & Mathematical Rationale:
  - Descending Distorted Vocal Grunt:
    A visceral vocalization synthesized from a triangle wave diving rapidly in pitch from
    260.0 Hz to 85.0 Hz over the 130ms duration along a steep exponential trajectory:
      f_grunt(t) = f_start * exp(ln(f_end / f_start) * (t / duration))
    The raw symmetric triangle waveform:
      tri(phase) = 4.0 * |((phase / 2pi) mod 1.0) - 0.5| - 1.0
    is processed through a non-linear hyperbolic tangent saturation transfer function (drive = 1.85):
      sat(x) = tanh(drive * x) / tanh(drive)
    which introduces rich odd-harmonic saturation mimicking human vocal cord constriction under impact.
  - Dissonant Minor-Second Sine Clash:
    Two carrier sine waves at 185.0 Hz (F#3) and 196.0 Hz (G3) form a dissonant minor-second interval:
      clash(t) = 0.5 * (sin(2pi * 185.0 * t) + sin(2pi * 196.0 * t))
    The 11.0 Hz difference produces rapid acoustic beating and psychoacoustic dissonance,
    instantly communicating pain and danger to the nervous system.
  - 15ms Blunt Trauma Low-Pass Noise Transient:
    A fast 15ms burst of pseudo-random white noise filtered through a 2-pole Butterworth low-pass
    filter (cutoff 400.0 Hz, Q = 0.7071) simulates physical blunt flesh/armor trauma.
  - 3-Stage Amplitude Envelope:
    - Attack (0 to 1 ms)     : Immediate 1ms linear rise preventing boundary clicks while hitting instantly.
    - Sustain (1 to 76 ms)   : 75ms compressed body preserving vocal punch and tactile presence.
    - Decay (76 to 130 ms)   : 54ms steep exponential decay with factor k = 8.0:
        env(p) = (exp(-8.0 * p) - exp(-8.0)) / (1.0 - exp(-8.0))
      guaranteeing seamless convergence to zero with zero pop at sound termination.
  - Headroom & Clamping:
    Samples are scaled to peak at ~25500 (-2.18 dB headroom) and strictly clamped to [-32767, 32767].

Direct C++ Raylib Translation (raylib.h):
  struct HurtSFX {
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
# ZERO __pycache__ SETUP, PATH SETUP & RAYLIB IMPORTS
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
# AUDIO SYNTHESIS CONSTANTS (Palette-Free Synthesis Parameters)
# ==============================================================================
SAMPLE_RATE = 44100
PI2 = 2.0 * math.pi

DEFAULT_DURATION = 0.130       # 130 ms total duration
GRUNT_START_FREQ = 260.0       # 260.0 Hz initial vocal pitch
GRUNT_END_FREQ = 85.0          # 85.0 Hz final vocal pitch (exponential dive)
GRUNT_DRIVE = 1.85             # Tanh saturation drive factor for vocal grit

DISS_FREQ_1 = 185.0            # 185.0 Hz (F#3) minor-second lower tone
DISS_FREQ_2 = 196.0            # 196.0 Hz (G3) minor-second upper tone (11 Hz clash)

ATTACK_TIME = 0.001            # 1 ms immediate attack
SUSTAIN_TIME = 0.075           # 75 ms compressed body
DECAY_TIME = 0.054             # 54 ms steep exponential decay (1 + 75 + 54 = 130 ms)
DECAY_K = 8.0                  # Exponential decay factor (k = 8.0)

NOISE_BURST_TIME = 0.015       # 15 ms blunt trauma noise burst
NOISE_CUTOFF_HZ = 400.0        # 400.0 Hz low-pass filter cutoff
NOISE_RESONANCE_Q = 0.7071     # Butterworth Q factor (maximally flat passband)

TARGET_PEAK_AMPLITUDE = 25500.0  # -2.18 dB headroom in signed 16-bit PCM space


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

        self.b0 = b0_raw / a0_raw
        self.b1 = b1_raw / a0_raw
        self.b2 = b2_raw / a0_raw
        self.a1 = a1_raw / a0_raw
        self.a2 = a2_raw / a0_raw

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
# DETERMINISTIC PSEUDO-RANDOM NOISE GENERATOR (C++ LCG Equivalent)
# ==============================================================================
class FastNoiseLCG:
    """
    Deterministic Linear Congruential Generator (LCG) producing uniform white noise in [-1.0, 1.0].
    C++ Equivalent:
      struct FastNoiseLCG {
          uint32_t state = 123456789;
          float NextSample() {
              state = state * 1103515245 + 12345;
              return ((float)(state & 0x7FFFFFFF) / 1073741824.0f) - 1.0f;
          }
      };
    """
    def __init__(self, seed: int = 123456789):
        self.state = seed & 0xFFFFFFFF

    def next_sample(self) -> float:
        self.state = (1103515245 * self.state + 12345) & 0x7FFFFFFF
        return (float(self.state) / 1073741824.0) - 1.0


# ==============================================================================
# IN-MEMORY RIFF WAV PACKER HELPER (C++ 44-Byte Header Equivalent)
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
# CORE SYNTHESIS FUNCTION & STANDARDIZED CONTROL METHODS
# ==============================================================================
def create_hurt_sfx(
    duration: float = DEFAULT_DURATION,
    start_freq: float = GRUNT_START_FREQ,
    end_freq: float = GRUNT_END_FREQ,
    volume: float = 1.0
) -> Sound:
    """
    Synthesizes the visceral player damage received vocal grunt sound effect
    into a ready-to-play Raylib Sound struct.

    Parameters:
      duration   : Total length in seconds (default: 0.130s = 130ms)
      start_freq : Starting frequency of vocal grunt in Hz (default: 260.0 Hz)
      end_freq   : Final diving frequency in Hz (default: 85.0 Hz)
      volume     : Master amplitude gain multiplier (0.0 to 1.0)

    Returns:
      Raylib Sound handle resident in audio memory.
    """
    total_samples = int(SAMPLE_RATE * duration)
    freq_log_ratio = math.log(end_freq / start_freq)

    # Envelope sample boundaries
    attack_samples = max(1, int(SAMPLE_RATE * ATTACK_TIME))
    sustain_end_sample = int(SAMPLE_RATE * (ATTACK_TIME + SUSTAIN_TIME))
    decay_samples = max(1, total_samples - sustain_end_sample)
    exp_neg_k = math.exp(-DECAY_K)

    # 15ms Blunt trauma noise burst parameters
    noise_samples = int(SAMPLE_RATE * NOISE_BURST_TIME)
    noise_lpf = BiquadLowPass2Pole(SAMPLE_RATE, NOISE_CUTOFF_HZ, NOISE_RESONANCE_Q)
    noise_gen = FastNoiseLCG(987654321)

    tanh_norm = math.tanh(GRUNT_DRIVE)
    grunt_phase = 0.0
    sine1_phase = 0.0
    sine2_phase = 0.0
    raw_mixed_samples = []

    for i in range(total_samples):
        t = float(i) / float(SAMPLE_RATE)
        prog = float(i) / float(total_samples)

        # 1. Vocal grunt: Exponential pitch dive (260 Hz -> 85 Hz)
        cur_grunt_freq = start_freq * math.exp(freq_log_ratio * prog)
        grunt_phase += PI2 * cur_grunt_freq / float(SAMPLE_RATE)

        # Symmetric triangle wave in [-1.0, 1.0]
        norm_phase = (grunt_phase / PI2) % 1.0
        tri_raw = 4.0 * abs(norm_phase - 0.5) - 1.0

        # Non-linear hyperbolic tangent distortion for vocal grit
        tri_distorted = math.tanh(GRUNT_DRIVE * tri_raw) / tanh_norm

        # 2. Dissonant minor-second sine clash (185 Hz and 196 Hz)
        sine1_phase += PI2 * DISS_FREQ_1 / float(SAMPLE_RATE)
        sine2_phase += PI2 * DISS_FREQ_2 / float(SAMPLE_RATE)
        clash_sine = 0.5 * (math.sin(sine1_phase) + math.sin(sine2_phase))

        # 3. 15ms Low-pass blunt trauma noise burst
        if i < noise_samples:
            white_noise = noise_gen.next_sample()
            filtered_noise = noise_lpf.process(white_noise)
            # Fast taper envelope for blunt impact transient
            if i < attack_samples:
                noise_env = float(i) / float(attack_samples)
            else:
                noise_env = 1.0 - (float(i - attack_samples) / float(noise_samples - attack_samples))
            noise_signal = filtered_noise * noise_env
        else:
            noise_signal = 0.0

        # 4. 3-Stage Amplitude Envelope (1ms Attack -> 75ms Sustain -> 54ms Exponential Decay)
        if i < attack_samples:
            envelope = float(i) / float(attack_samples)
        elif i < sustain_end_sample:
            envelope = 1.0
        else:
            p_decay = float(i - sustain_end_sample) / float(decay_samples)
            envelope = (math.exp(-DECAY_K * p_decay) - exp_neg_k) / (1.0 - exp_neg_k)

        # 5. Composite waveform summation
        sample_sum = (0.50 * tri_distorted + 0.30 * clash_sine + 0.35 * noise_signal) * envelope
        raw_mixed_samples.append(sample_sum)

    # 6. Peak amplitude normalization & headroom scaling
    max_peak = 0.0
    for s in raw_mixed_samples:
        abs_val = abs(s)
        if abs_val > max_peak:
            max_peak = abs_val

    if max_peak > 1e-6:
        gain = (TARGET_PEAK_AMPLITUDE / max_peak) * max(0.0, min(1.0, volume))
    else:
        gain = 1.0

    # 7. Clamp to signed 16-bit PCM integer range [-32767, 32767]
    pcm_samples = []
    for s in raw_mixed_samples:
        scaled = s * gain
        clamped = max(-32767, min(32767, int(scaled)))
        pcm_samples.append(clamped)

    # 8. Pack into in-memory RIFF WAV container and load into Raylib Sound
    wav_bytes = pack_riff_wav_mono_16bit(SAMPLE_RATE, pcm_samples)
    wave = load_wave_from_memory(".wav", wav_bytes, len(wav_bytes))
    sound = load_sound_from_wave(wave)
    unload_wave(wave)
    return sound


# Standardized alias mapping for dynamic discovery
create_sfx = create_hurt_sfx


# ==============================================================================
# STANDARDIZED PLAYBACK CONTROL METHODS
# ==============================================================================
def play_sfx(sound: Sound, volume: float = 1.0, pitch: float = 1.0) -> None:
    """Plays the hurt sound effect with explicit volume and pitch scaling."""
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
    to audition the hurt damage sound effect with live parameter controls and telemetry.
    """
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        init_window(
            self.screen_width,
            self.screen_height,
            "SFX Workbench - Hurt Damage Grunt (assets/audio/SFX/progression/hurt.py)"
        )
        set_target_fps(60)
        init_audio_device()

        self.sound = create_hurt_sfx()
        self.trigger_pulse = 0.0
        self.volume = 0.85
        self.pitch = 1.0
        self.trigger_count = 0
        self.show_xray = False

        # Visualizer particles for damage impact splatter
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
        """Triggers sound playback with current pitch/volume and animates visualizer."""
        play_sfx(self.sound, self.volume, self.pitch)
        self.trigger_pulse = 1.0
        self.trigger_count += 1

        # Spawn visceral damage splatter particles
        cx = 850.0
        cy = 300.0
        import random
        for idx, p in enumerate(self.particles):
            ang = random.uniform(0.0, PI2)
            spd = random.uniform(60.0, 260.0)
            p["x"] = cx + math.cos(ang) * random.uniform(2.0, 25.0)
            p["y"] = cy + math.sin(ang) * random.uniform(2.0, 25.0)
            p["vx"] = math.cos(ang) * spd
            p["vy"] = math.sin(ang) * spd - random.uniform(20.0, 80.0)
            p["life"] = 1.0
            p["max_life"] = random.uniform(0.3, 0.7)
            p["size"] = random.uniform(3.0, 7.5)
            p["color_type"] = idx % 3

    def update(self):
        dt = min(get_frame_time(), 0.05)
        if self.trigger_pulse > 0.0:
            self.trigger_pulse = max(0.0, self.trigger_pulse - dt * 3.5)

        # Update particles with gravity
        for p in self.particles:
            if p["life"] > 0.0:
                p["life"] = max(0.0, p["life"] - dt / p["max_life"])
                p["x"] += p["vx"] * dt
                p["y"] += p["vy"] * dt
                p["vy"] += 380.0 * dt  # Gravity pull downward

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
        clear_background(Color(18, 10, 12, 255))

        # Dynamic red vignette screen flash when damaged
        if self.trigger_pulse > 0.01:
            flash_alpha = int(self.trigger_pulse * 90)
            draw_rectangle(0, 0, self.screen_width, self.screen_height, Color(220, 20, 30, flash_alpha))

        # Header (keeps top-bar region x=450..980, y=14..48 clear for UI settings bar)
        draw_text("PROCEDURAL SFX AUDITION WORKBENCH", 24, 18, 20, RAYWHITE)
        draw_text("Asset: assets/audio/SFX/progression/hurt.py | Vocal Grunt & Dissonant Impact", 24, 46, 13, RED)

        # ======================================================================
        # LEFT CONTROL PANEL (x=24, y=90, w=400)
        # ======================================================================
        panel_y = 90
        panel_w = 400
        panel_h = 240
        draw_rectangle(24, panel_y, panel_w, panel_h, Color(28, 16, 18, 255))
        draw_rectangle_lines(24, panel_y, panel_w, panel_h, Color(90, 35, 45, 255))

        draw_text("INTERACTIVE CONTROLS & SHORTCUTS", 40, panel_y + 14, 15, YELLOW)
        draw_text("- [Space] / [Left Click] / Gamepad [A] : Trigger Hurt SFX", 40, panel_y + 42, 13, RAYWHITE)
        draw_text("- [Up] / [Down] Arrows / D-Pad         : Adjust Pitch (+/- 0.1x)", 40, panel_y + 68, 13, RAYWHITE)
        draw_text("- [Left] / [Right] Arrows              : Adjust Volume (+/- 0.05)", 40, panel_y + 94, 13, RAYWHITE)
        draw_text("- [R] Key / Gamepad [Start]            : Reset Pitch & Volume", 40, panel_y + 120, 13, RAYWHITE)
        draw_text("- [Tab] / [F1] / Gamepad [Y]           : Toggle X-Ray Telemetry", 40, panel_y + 146, 13, SKYBLUE)

        draw_text(f"Current Pitch    : {self.pitch:.1f}x", 40, panel_y + 178, 13, RED)
        draw_text(f"Current Volume   : {self.volume:.2f}", 40, panel_y + 198, 13, RED)
        draw_text(f"Total Triggers   : {self.trigger_count}", 40, panel_y + 218, 13, LIGHTGRAY)

        # Parameter Specification Card (Below controls)
        card_y = panel_y + panel_h + 16
        card_h = 320
        draw_rectangle(24, card_y, panel_w, card_h, Color(24, 14, 16, 255))
        draw_rectangle_lines(24, card_y, panel_w, card_h, Color(75, 30, 38, 255))
        draw_text("SYNTHESIS SPECIFICATION & ARCHITECTURE", 40, card_y + 14, 14, ORANGE)

        specs = [
            ("Catalog ID", "sfx_prog_hurt"),
            ("Waveforms", "Distorted triangle + dissonant sines + noise"),
            ("Vocal Grunt Dive", "260.0 Hz -> 85.0 Hz (steep exponential)"),
            ("Distortion Drive", "tanh(1.85 * tri) / tanh(1.85) saturation"),
            ("Dissonant Clash", "185.0 Hz (F#3) & 196.0 Hz (G3) [11 Hz clash]"),
            ("Blunt Trauma", "15ms white noise through 400 Hz 2-pole LPF"),
            ("Envelope Attack", "1 ms immediate linear ramp"),
            ("Envelope Sustain", "75 ms compressed punch body"),
            ("Envelope Decay", "54 ms steep exponential decay (k=8.0)"),
            ("Total Duration", "130 ms (5,733 samples @ 44.1 kHz)"),
            ("Peak Amplitude", "~25,500 (-2.18 dB headroom)"),
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
        draw_rectangle(vis_x, vis_y, vis_w, vis_h, Color(20, 12, 14, 255))
        draw_rectangle_lines(vis_x, vis_y, vis_w, vis_h, Color(90, 35, 45, 255))

        draw_text("DAMAGE TRAUMA & WAVEFORM VISUALIZER", vis_x + 20, vis_y + 16, 15, RED)
        draw_text("Real-time Vocal Grunt Dive & Minor-Second Acoustic Clashing (185 Hz vs 196 Hz)", vis_x + 20, vis_y + 38, 12, GRAY)

        # Center visualization area: Shattered heart / impact target
        center_x = vis_x + (vis_w // 2)
        center_y = vis_y + 175

        # Screen shake offset when triggered
        shake_x = 0
        shake_y = 0
        if self.trigger_pulse > 0.05:
            import random
            shake_mag = int(self.trigger_pulse * 12)
            shake_x = random.randint(-shake_mag, shake_mag)
            shake_y = random.randint(-shake_mag, shake_mag)

        cx = center_x + shake_x
        cy = center_y + shake_y

        # Impact aura rings
        aura_rad = 40.0 + (self.trigger_pulse * 55.0)
        glow_a = int(self.trigger_pulse * 160)
        draw_circle(cx, cy, aura_rad, Color(180, 20, 30, glow_a // 4))
        draw_circle_lines(cx, cy, aura_rad, Color(240, 50, 60, glow_a))
        draw_circle_lines(cx, cy, aura_rad * 0.7, Color(255, 100, 110, glow_a))

        # Heart / Damage crest rendering
        heart_scale = 1.0 + (self.trigger_pulse * 0.25)
        r_top = int(18 * heart_scale)
        draw_circle(cx - r_top, cy - r_top // 2, r_top, Color(220, 30, 45, 240))
        draw_circle(cx + r_top, cy - r_top // 2, r_top, Color(220, 30, 45, 240))
        draw_triangle(
            Vector2(cx - r_top * 2.0, cy - r_top // 4),
            Vector2(cx + r_top * 2.0, cy - r_top // 4),
            Vector2(cx, cy + r_top * 2.2),
            Color(220, 30, 45, 240)
        )

        # Fracture jagged crack lines when damaged
        if self.trigger_pulse > 0.02:
            crack_a = int(self.trigger_pulse * 255)
            draw_line(cx - 5, cy - 25, cx + 2, cy - 8, Color(255, 255, 255, crack_a))
            draw_line(cx + 2, cy - 8, cx - 8, cy + 6, Color(255, 255, 255, crack_a))
            draw_line(cx - 8, cy + 6, cx + 4, cy + 22, Color(255, 255, 255, crack_a))

        # Blood & spark particles
        for p in self.particles:
            if p["life"] > 0.0:
                p_alpha = int(p["life"] * 255)
                if p["color_type"] == 0:
                    p_col = Color(240, 30, 40, p_alpha)
                elif p["color_type"] == 1:
                    p_col = Color(160, 10, 20, p_alpha)
                else:
                    p_col = Color(255, 120, 40, p_alpha)
                draw_circle(
                    int(p["x"]),
                    int(p["y"]),
                    p["size"] * (0.4 + 0.6 * p["life"]),
                    p_col
                )

        # Dynamic amplitude pulse meter bar
        meter_y = vis_y + 310
        meter_w = vis_w - 40
        draw_rectangle(vis_x + 20, meter_y, meter_w, 20, Color(35, 18, 22, 255))
        draw_rectangle_lines(vis_x + 20, meter_y, meter_w, 20, Color(80, 30, 40, 255))
        active_meter = int(self.trigger_pulse * meter_w)
        draw_rectangle(vis_x + 20, meter_y, active_meter, 20, Color(220, 40, 50, 230))
        draw_text("IMPACT AMPLITUDE TRANSIENT", vis_x + 24, meter_y + 4, 11, RAYWHITE)

        # Dual oscilloscope: Grunt triangle dive + minor-second beating + noise burst
        wave_y = vis_y + 430
        draw_line(vis_x + 20, wave_y, vis_x + vis_w - 20, wave_y, Color(60, 25, 30, 255))
        draw_text("OSCILLOSCOPE: DISTORTED TRIANGLE DIVE (260->85 Hz) + 11 Hz BEAT + 400 Hz NOISE", vis_x + 20, wave_y - 72, 12, ORANGE)

        prev_pt_x = vis_x + 20
        prev_pt_y = wave_y
        steps = 140
        for s in range(1, steps + 1):
            t_ratio = float(s) / float(steps)
            pt_x = vis_x + 20 + int(t_ratio * (vis_w - 40))

            # Dive frequency in [260 -> 85]
            freq_dive = 260.0 * math.exp(math.log(85.0 / 260.0) * t_ratio)
            phase = t_ratio * freq_dive * 0.04 * PI2 * self.pitch

            # Distorted triangle approximation
            tri = 4.0 * abs(((phase / PI2) % 1.0) - 0.5) - 1.0
            dist_tri = math.tanh(1.85 * tri) / math.tanh(1.85)

            # Dissonant minor-second beating (11 Hz difference)
            clash_beat = math.cos(t_ratio * 11.0 * PI2 * 0.130 * 4.0)

            # Noise burst during early 15%
            noise_val = 0.0
            if t_ratio < 0.15:
                noise_val = math.sin(t_ratio * 180.0) * (1.0 - t_ratio / 0.15) * 0.4

            # Envelope
            if t_ratio < 0.01:
                env = t_ratio / 0.01
            elif t_ratio < 0.58:
                env = 1.0
            else:
                p_dec = (t_ratio - 0.58) / 0.42
                env = math.exp(-8.0 * p_dec)

            wave_amp = (0.50 * dist_tri + 0.30 * clash_beat + noise_val) * env * (28.0 + self.trigger_pulse * 40.0)
            pt_y = int(wave_y - wave_amp)
            draw_line(prev_pt_x, prev_pt_y, pt_x, pt_y, Color(240, 60, 70, 220))
            prev_pt_x = pt_x
            prev_pt_y = pt_y

        # Envelope segment markers
        x_att = vis_x + 20 + int((1.0 / 130.0) * (vis_w - 40))
        x_sus = vis_x + 20 + int((76.0 / 130.0) * (vis_w - 40))
        x_noise = vis_x + 20 + int((15.0 / 130.0) * (vis_w - 40))

        draw_line(x_att, wave_y - 45, x_att, wave_y + 45, Color(160, 80, 50, 180))
        draw_line(x_sus, wave_y - 45, x_sus, wave_y + 45, Color(160, 80, 50, 180))
        draw_line(x_noise, wave_y - 25, x_noise, wave_y + 25, Color(120, 40, 50, 140))

        draw_text("Attack: 1ms", vis_x + 22, wave_y + 48, 11, YELLOW)
        draw_text("Sustain: 75ms", x_att + 6, wave_y + 48, 11, RED)
        draw_text("Decay: 54ms (k=8.0)", x_sus + 6, wave_y + 48, 11, ORANGE)
        draw_text("Noise: 15ms", x_noise + 4, wave_y - 36, 10, GRAY)

        # X-Ray Telemetry Overlay (Toggled via Tab / F1)
        if self.show_xray:
            ox = vis_x + 20
            oy = vis_y + 60
            ow = vis_w - 40
            oh = 260
            draw_rectangle(ox, oy, ow, oh, Color(14, 8, 10, 248))
            draw_rectangle_lines(ox, oy, ow, oh, Color(220, 60, 70, 255))
            draw_text("X-RAY TELEMETRY: REAL-TIME SYNTHESIS EQUATIONS", ox + 16, oy + 12, 14, YELLOW)

            eqs = [
                "1. Vocal Grunt Dive   : f(t) = 260.0 * exp(ln(85.0 / 260.0) * (t / 0.130)) [Exponential]",
                "2. Triangle Distortion : sat(x) = tanh(1.85 * tri) / tanh(1.85) [Vocal Cord Saturation]",
                "3. Minor-Second Clash  : clash(t) = 0.5 * [sin(2pi*185.0*t) + sin(2pi*196.0*t)] -> 11 Hz Beat",
                "4. 15ms Blunt Trauma   : LCG White Noise filtered through 2-Pole Butterworth LPF (fc = 400 Hz)",
                "5. 2-Pole Biquad LPF   : y[n] = b0*x[n] + b1*x[n-1] + b2*x[n-2] - a1*y[n-1] - a2*y[n-2]",
                "6. 3-Stage Envelope    : Attack(1ms) Linear -> Sustain(75ms) 1.0 -> Decay(54ms) exp(-8.0 * p)",
                "7. Peak Headroom       : Normalized to 25,500 / 32,767 (~-2.18 dB headroom)"
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
