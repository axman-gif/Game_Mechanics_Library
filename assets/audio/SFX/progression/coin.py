# -*- coding: utf-8 -*-
"""
Procedural Coin Sound Effect (SFX) Synthesizer
==============================================
Type             : Procedural Audio SFX (Sound)
Target File      : assets/audio/SFX/progression/coin.py
Waveforms Used   : Two-tone pure sine chime (B5 to E6) with 500 Hz high-pass filter
Category         : Progression & Economy

Problem Solved:
  Eliminates external audio file dependencies (.wav/.mp3) by synthesizing an iconic,
  bright arcade collectible coin chime directly in memory from pure mathematical sine
  waveforms into an in-memory 16-bit PCM buffer, loading directly into a Raylib Sound struct.

Waveform Theory & Mathematical Rationale:
  - Sequence: Synthesizes a two-tone melodic interval:
      Tone 1: B5 (987.77 Hz) for 45 ms (0.045 s).
      Tone 2: E6 (1318.51 Hz) for 65 ms (0.065 s).
      Total Duration: 110 ms (0.110 s).
  - Musical Interval: The transition from B5 to E6 forms an instantaneous upward step
    of an ascending perfect fourth (frequency ratio 4:3, 1318.51 / 987.77 ~= 1.3348).
    In psychoacoustics, an ascending fourth evokes an immediate sensation of energetic
    uplift, achievement, and rewarding gameplay feedback.
  - Amplitude Envelope:
      Tone 1 (B5): Rapid 0.5 ms linear attack ramp to eliminate initial boundary clicks,
      followed by flat full sustain (env = 1.0) to give the initial note weight.
      Tone 2 (E6): Rapid 0.5 ms attack articulation, followed immediately by a smooth
      exponential decay envelope: env(t) = exp(-6.5 * progress), fading naturally into
      near-silence (~-56 dB) without abrupt boundary clicks.
  - High-Pass Filter (HPF):
      A 1st-order single-pole IIR filter with cutoff fc = 500 Hz:
        alpha = RC / (RC + dt), where RC = 1 / (2 * pi * fc) and dt = 1 / sample_rate.
        y[i] = alpha * (y[i - 1] + x[i] - x[i - 1])
      Attenuates any sub-bass rumble, DC offset, or switching transient below 500 Hz
      while passing the crisp 988 Hz and 1319 Hz harmonics uncolored.
  - Headroom & Dynamic Range:
      Peak amplitude normalized and scaled to ~25,000 (signed 16-bit PCM, [-32767, 32767]),
      providing ~-2.5 dBFS of safe headroom to prevent digital clipping when multiple coins
      are collected in rapid succession.

Direct C++ Raylib Translation (raylib.h):
  struct CoinSFX {
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

# Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# Add repository root to search path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

from pyray import *
from utils import *


# ==============================================================================
# PART 3: AUDIO SYNTHESIS CONSTANTS
# ==============================================================================
SAMPLE_RATE: int = 44100
PI2: float = 2.0 * math.pi

# Note 1: B5
NOTE1_FREQ: float = 987.77         # Hz (B5)
NOTE1_DURATION: float = 0.045      # 45 ms

# Note 2: E6
NOTE2_FREQ: float = 1318.51        # Hz (E6)
NOTE2_DURATION: float = 0.065      # 65 ms

# Total timing
TOTAL_DURATION: float = NOTE1_DURATION + NOTE2_DURATION  # 110 ms
ATTACK_DURATION: float = 0.0005    # 0.5 ms attack ramp on each note
DECAY_RATE_NOTE2: float = 6.5      # Exponential decay factor k=6.5

# High-Pass Filter cutoff
HPF_CUTOFF: float = 500.0          # Hz
TARGET_PEAK_AMPLITUDE: float = 25000.0  # Peak signed 16-bit PCM target (~-2.5 dBFS)


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
def create_coin_sfx(
    volume: float = 1.0,
    duration_note1: float = NOTE1_DURATION,
    duration_note2: float = NOTE2_DURATION,
    freq_note1: float = NOTE1_FREQ,
    freq_note2: float = NOTE2_FREQ
) -> Sound:
    """
    Synthesizes a bright two-tone pure sine collectible coin chime into a Raylib Sound struct.
    
    Parameters:
      volume         : Overall master amplitude scale factor (0.0 to 1.0).
      duration_note1 : Duration of initial B5 note in seconds (default 45 ms).
      duration_note2 : Duration of secondary E6 note in seconds (default 65 ms).
      freq_note1     : Frequency of initial note in Hz (default 987.77 Hz, B5).
      freq_note2     : Frequency of secondary note in Hz (default 1318.51 Hz, E6).
      
    Returns:
      A ready-to-play Sound handle resident in audio hardware memory.
    """
    samples_note1 = int(SAMPLE_RATE * duration_note1)
    samples_note2 = int(SAMPLE_RATE * duration_note2)
    total_samples = samples_note1 + samples_note2

    raw_samples = []
    phase = 0.0

    # 1. Synthesize two-tone sine waveform with per-note amplitude envelopes
    for i in range(total_samples):
        if i < samples_note1:
            # Tone 1: B5 (987.77 Hz)
            t_note = float(i) / float(SAMPLE_RATE)
            current_freq = freq_note1
            phase += PI2 * current_freq / float(SAMPLE_RATE)

            # Envelope: 0.5 ms linear attack ramp, then flat sustain
            if t_note < ATTACK_DURATION:
                envelope = t_note / ATTACK_DURATION
            else:
                envelope = 1.0
        else:
            # Tone 2: E6 (1318.51 Hz)
            j = i - samples_note1
            t_note = float(j) / float(SAMPLE_RATE)
            current_freq = freq_note2
            phase += PI2 * current_freq / float(SAMPLE_RATE)

            # Envelope: 0.5 ms attack articulation, then exponential decay
            if t_note < ATTACK_DURATION:
                envelope = t_note / ATTACK_DURATION
            else:
                decay_prog = (t_note - ATTACK_DURATION) / max(0.001, (duration_note2 - ATTACK_DURATION))
                envelope = math.exp(-DECAY_RATE_NOTE2 * decay_prog)

        # Pure sine oscillator value multiplied by instantaneous envelope
        val = math.sin(phase) * envelope
        raw_samples.append(val)

    # 2. Apply 1st-Order Single-Pole High-Pass Filter (fc = 500 Hz)
    # Difference equation: y[i] = alpha * (y[i - 1] + x[i] - x[i - 1])
    dt = 1.0 / float(SAMPLE_RATE)
    rc = 1.0 / (PI2 * HPF_CUTOFF)
    alpha = rc / (rc + dt)

    filtered_samples = []
    prev_x = 0.0
    prev_y = 0.0
    for x in raw_samples:
        y = alpha * (prev_y + x - prev_x)
        prev_x = x
        prev_y = y
        filtered_samples.append(y)

    # 3. Peak normalization and scaling to signed 16-bit PCM target range
    max_abs = 0.0
    for s in filtered_samples:
        if abs(s) > max_abs:
            max_abs = abs(s)

    if max_abs > 0.0001:
        scale = (TARGET_PEAK_AMPLITUDE * max(0.0, min(1.0, volume))) / max_abs
    else:
        scale = TARGET_PEAK_AMPLITUDE * max(0.0, min(1.0, volume))

    pcm_samples = []
    for y in filtered_samples:
        clamped = max(-32767, min(32767, int(y * scale)))
        pcm_samples.append(clamped)

    # 4. In-memory RIFF WAV container packaging and hardware loading
    wav_bytes = pack_riff_wav_mono_16bit(SAMPLE_RATE, pcm_samples)
    wave = load_wave_from_memory(".wav", wav_bytes, len(wav_bytes))
    sound = load_sound_from_wave(wave)
    unload_wave(wave)  # Free CPU RAM Wave container; Sound retains hardware handle
    return sound


# Standardized alias mapping for dynamic discovery
create_sfx = create_coin_sfx


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
class CoinSparkle:
    """Visual particle emitted when the coin SFX triggers in the workbench."""
    def __init__(self, x: float, y: float, vx: float, vy: float, life: float, color: Any):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = color

    def update(self, dt: float) -> bool:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        return self.life > 0.0

    def draw(self):
        progress = max(0.0, self.life / self.max_life)
        alpha = int(255 * progress)
        if isinstance(self.color, (tuple, list)):
            r, g, b = int(self.color[0]), int(self.color[1]), int(self.color[2])
        else:
            r, g, b = int(self.color.r), int(self.color.g), int(self.color.b)
        c = Color(r, g, b, alpha)
        sz = max(1.0, 4.0 * progress)
        draw_circle(int(self.x), int(self.y), sz, c)
        draw_line(int(self.x - sz * 2), int(self.y), int(self.x + sz * 2), int(self.y), c)
        draw_line(int(self.x), int(self.y - sz * 2), int(self.x), int(self.y + sz * 2), c)


class SFXAuditionApp:
    """
    Interactive sound previewer workbench allowing developers and students
    to audition the coin sound effect with live parameter controls, visualizer,
    telemetry, and automated smoke test capability.
    """
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        init_window(self.screen_width, self.screen_height, "SFX Workbench - Coin (assets/audio/SFX/progression/coin.py)")
        set_target_fps(60)
        init_audio_device()

        self.sound = create_coin_sfx()
        self.trigger_pulse = 0.0
        self.volume = 0.90
        self.pitch = 1.0
        self.trigger_count = 0
        self.coin_rotation = 0.0
        self.sparkles = []

    def trigger(self):
        """Triggers sound playback with current pitch/volume and animates visualizer."""
        play_sfx(self.sound, self.volume, self.pitch)
        self.trigger_pulse = 1.0
        self.trigger_count += 1

        # Spawn sparkling celebration particles around the coin
        coin_cx = 580.0
        coin_cy = 280.0
        for k in range(16):
            angle = (float(k) / 16.0) * PI2
            speed = 80.0 + (float(k % 4) * 40.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = GOLD if k % 2 == 0 else YELLOW
            self.sparkles.append(CoinSparkle(coin_cx, coin_cy, vx, vy, 0.45, color))

    def update(self):
        dt = min(get_frame_time(), 0.05)

        # Decay pulse & rotate coin
        if self.trigger_pulse > 0.0:
            self.trigger_pulse = max(0.0, self.trigger_pulse - dt * 3.5)

        rot_speed = 3.0 + self.trigger_pulse * 10.0
        self.coin_rotation += dt * rot_speed
        if self.coin_rotation > PI2:
            self.coin_rotation -= PI2

        # Update sparkles
        active_sparkles = []
        for sp in self.sparkles:
            if sp.update(dt):
                active_sparkles.append(sp)
        self.sparkles = active_sparkles

        # Trigger inputs: Space, Enter, Left Click, or Gamepad Face Down (A / Cross)
        key_trigger = is_key_pressed(KEY_SPACE) or is_key_pressed(KEY_ENTER)
        mouse_trigger = is_mouse_button_pressed(MOUSE_BUTTON_LEFT)
        pad_trigger = False
        if is_gamepad_available(0):
            pad_trigger = is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_FACE_DOWN)

        if key_trigger or mouse_trigger or pad_trigger:
            self.trigger()

        # Pitch adjustments: Up/Down arrows or Gamepad D-pad Up/Down
        if is_key_pressed(KEY_UP) or (is_gamepad_available(0) and is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_UP)):
            self.pitch = min(2.0, self.pitch + 0.1)
        elif is_key_pressed(KEY_DOWN) or (is_gamepad_available(0) and is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_DOWN)):
            self.pitch = max(0.5, self.pitch - 0.1)

        # Volume adjustments: Right/Left arrows
        if is_key_pressed(KEY_RIGHT) or (is_gamepad_available(0) and is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_RIGHT)):
            self.volume = min(1.0, self.volume + 0.05)
        elif is_key_pressed(KEY_LEFT) or (is_gamepad_available(0) and is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_LEFT)):
            self.volume = max(0.0, self.volume - 0.05)

        # Reset controls: [R] Key or Gamepad Start/Back
        pad_reset = False
        if is_gamepad_available(0):
            pad_reset = is_gamepad_button_pressed(0, GAMEPAD_BUTTON_MIDDLE_RIGHT) or is_gamepad_button_pressed(0, GAMEPAD_BUTTON_MIDDLE_LEFT)

        if is_key_pressed(KEY_R) or pad_reset:
            self.pitch = 1.0
            self.volume = 0.90

    def draw(self):
        begin_drawing()
        clear_background(Color(14, 18, 28, 255))

        # Header (keeps top-bar region x=450..980, y=14..48 completely clear)
        draw_text("PROCEDURAL SFX AUDITION WORKBENCH", 24, 20, 20, RAYWHITE)
        draw_text("Asset: assets/audio/SFX/progression/coin.py | Waveform: Two-Tone Pure Sine Chime (B5 -> E6)", 24, 50, 13, GOLD)

        # Control Instructions Card
        panel_y = 90
        panel_w = 380
        panel_h = 590
        draw_rectangle(24, panel_y, panel_w, panel_h, Color(22, 28, 44, 255))
        draw_rectangle_lines(24, panel_y, panel_w, panel_h, Color(55, 70, 110, 255))

        draw_text("CONTROLS & SHORTCUTS", 42, panel_y + 16, 15, YELLOW)
        draw_text("- [Space] / [Enter] / [Click] : Trigger Coin SFX", 42, panel_y + 44, 12, RAYWHITE)
        draw_text("- [Up] / [Down] Arrows        : Pitch (+/- 0.1x)", 42, panel_y + 68, 12, RAYWHITE)
        draw_text("- [Right] / [Left] Arrows     : Volume (+/- 0.05)", 42, panel_y + 92, 12, RAYWHITE)
        draw_text("- [R] Key / Gamepad Start     : Reset All Parameters", 42, panel_y + 116, 12, RAYWHITE)

        draw_line(42, panel_y + 144, 24 + panel_w - 42, panel_y + 144, Color(55, 70, 110, 255))

        draw_text("CURRENT TELEMETRY", 42, panel_y + 158, 15, SKYBLUE)
        draw_text(f"Total Triggers : {self.trigger_count}", 42, panel_y + 186, 13, LIGHTGRAY)
        draw_text(f"Active Pitch   : {self.pitch:.1f}x", 42, panel_y + 210, 13, GREEN)
        draw_text(f"Master Volume  : {int(self.volume * 100)}%", 42, panel_y + 234, 13, GREEN)

        draw_line(42, panel_y + 262, 24 + panel_w - 42, panel_y + 262, Color(55, 70, 110, 255))

        draw_text("SYNTHESIS SPECIFICATIONS", 42, panel_y + 276, 15, GOLD)
        draw_text("Tone 1 : B5 (987.77 Hz) for 45 ms", 42, panel_y + 304, 12, RAYWHITE)
        draw_text("Tone 2 : E6 (1318.51 Hz) for 65 ms", 42, panel_y + 326, 12, RAYWHITE)
        draw_text("Total  : 110 ms (4850 samples @ 44.1 kHz)", 42, panel_y + 348, 12, LIGHTGRAY)
        draw_text("Step   : Ascending Perfect Fourth (4:3)", 42, panel_y + 370, 12, YELLOW)
        draw_text("Filter : 1-Pole HPF (fc = 500 Hz)", 42, panel_y + 392, 12, RAYWHITE)
        draw_text("Envelop: 0.5ms Attack -> Sustain -> ExpDecay", 42, panel_y + 414, 12, LIGHTGRAY)
        draw_text("Peak   : ~25,000 PCM (-2.5 dBFS Headroom)", 42, panel_y + 436, 12, GREEN)

        draw_line(42, panel_y + 464, 24 + panel_w - 42, panel_y + 464, Color(55, 70, 110, 255))
        draw_text("C++ EQUIVALENT ARCHITECTURE", 42, panel_y + 478, 13, SKYBLUE)
        draw_text("Wave w = LoadWaveFromMemory(...);", 42, panel_y + 504, 11, LIGHTGRAY)
        draw_text("Sound s = LoadSoundFromWave(w);", 42, panel_y + 524, 11, LIGHTGRAY)
        draw_text("UnloadWave(w); // Retains audio device RAM", 42, panel_y + 544, 11, LIGHTGRAY)
        draw_text("PlaySound(s);  // 1-to-1 Raylib parity", 42, panel_y + 564, 11, LIGHTGRAY)

        # Right Stage: Visualizer Panels
        stage_x = 420
        stage_y = 90
        stage_w = 836
        stage_h = 590
        draw_rectangle(stage_x, stage_y, stage_w, stage_h, Color(18, 24, 38, 255))
        draw_rectangle_lines(stage_x, stage_y, stage_w, stage_h, Color(55, 70, 110, 255))

        # Coin Display Section
        draw_text("INTERACTIVE COLLECTIBLE AUDITION STAGE", stage_x + 20, stage_y + 16, 15, GOLD)

        coin_cx = stage_x + 180
        coin_cy = stage_y + 180
        coin_radius = 48.0 + (self.trigger_pulse * 12.0)
        coin_aspect = math.cos(self.coin_rotation)
        coin_w = max(4.0, abs(coin_aspect) * coin_radius)

        # Outer glow during trigger
        if self.trigger_pulse > 0.05:
            glow_alpha = int(120 * self.trigger_pulse)
            draw_circle(int(coin_cx), int(coin_cy), coin_radius + 18.0, Color(255, 215, 0, glow_alpha))

        # Draw 2D rotating coin geometry
        rim_color = Color(180, 140, 20, 255) if coin_aspect >= 0 else Color(150, 110, 10, 255)
        face_color = GOLD if coin_aspect >= 0 else Color(220, 180, 40, 255)
        draw_ellipse(int(coin_cx), int(coin_cy), coin_w, coin_radius, rim_color)
        draw_ellipse(int(coin_cx), int(coin_cy), max(2.0, coin_w - 6.0), max(2.0, coin_radius - 6.0), face_color)

        # Coin star / crest marker
        if coin_w > 16.0:
            star_scale = coin_w / coin_radius
            draw_line(int(coin_cx - 14.0 * star_scale), int(coin_cy), int(coin_cx + 14.0 * star_scale), int(coin_cy), DARKBLUE)
            draw_line(int(coin_cx), int(coin_cy - 14.0), int(coin_cx), int(coin_cy + 14.0), DARKBLUE)

        # Draw Sparkle particles
        for sp in self.sparkles:
            sp.draw()

        # Coin status text
        draw_text("Interactive Coin Primitive", int(coin_cx) - 80, int(coin_cy) + 75, 13, RAYWHITE)
        draw_text("Click / Space to collect", int(coin_cx) - 75, int(coin_cy) + 95, 11, LIGHTGRAY)

        # Amplitude Pulse Meter (Horizontal)
        meter_x = stage_x + 380
        meter_y = stage_y + 120
        meter_w = 420
        meter_h = 32
        draw_rectangle(meter_x, meter_y, meter_w, meter_h, Color(12, 16, 26, 255))
        draw_rectangle_lines(meter_x, meter_y, meter_w, meter_h, Color(55, 70, 110, 255))
        pulse_fill = int(self.trigger_pulse * (meter_w - 4))
        if pulse_fill > 0:
            meter_color = Color(int(255 * self.trigger_pulse), int(215 * self.trigger_pulse), 0, 230)
            draw_rectangle(meter_x + 2, meter_y + 2, pulse_fill, meter_h - 4, meter_color)
        draw_text("Instantaneous Energy Peak Meter", meter_x, meter_y - 20, 12, SKYBLUE)
        draw_text(f"{int(self.trigger_pulse * 100)}%", meter_x + meter_w - 40, meter_y + 8, 12, RAYWHITE)

        # Spectrum notes visualization box
        notes_box_y = stage_y + 180
        draw_rectangle(meter_x, notes_box_y, meter_w, 100, Color(14, 20, 32, 255))
        draw_rectangle_lines(meter_x, notes_box_y, meter_w, 100, Color(55, 70, 110, 255))
        draw_text("TWO-TONE FREQUENCY TRAJECTORY", meter_x + 14, notes_box_y + 12, 12, GOLD)

        # Step indicator
        t1_active = self.trigger_pulse > 0.5
        t2_active = 0.0 < self.trigger_pulse <= 0.5
        c_tone1 = YELLOW if t1_active else Color(100, 120, 160, 255)
        c_tone2 = GOLD if t2_active else Color(100, 120, 160, 255)

        draw_rectangle(meter_x + 14, notes_box_y + 40, 175, 44, Color(24, 32, 50, 255))
        draw_rectangle_lines(meter_x + 14, notes_box_y + 40, 175, 44, c_tone1)
        draw_text("Tone 1: B5 (988 Hz)", meter_x + 24, notes_box_y + 48, 12, c_tone1)
        draw_text("0 ms to 45 ms", meter_x + 24, notes_box_y + 66, 11, LIGHTGRAY)

        draw_text("->", meter_x + 198, notes_box_y + 54, 15, RAYWHITE)

        draw_rectangle(meter_x + 225, notes_box_y + 40, 175, 44, Color(24, 32, 50, 255))
        draw_rectangle_lines(meter_x + 225, notes_box_y + 40, 175, 44, c_tone2)
        draw_text("Tone 2: E6 (1319 Hz)", meter_x + 235, notes_box_y + 48, 12, c_tone2)
        draw_text("45 ms to 110 ms (Decay)", meter_x + 235, notes_box_y + 66, 11, LIGHTGRAY)

        # Oscilloscope Waveform Panel (Lower Half)
        scope_x = stage_x + 20
        scope_y = stage_y + 320
        scope_w = stage_w - 40
        scope_h = 240
        draw_rectangle(scope_x, scope_y, scope_w, scope_h, Color(12, 16, 26, 255))
        draw_rectangle_lines(scope_x, scope_y, scope_w, scope_h, Color(55, 70, 110, 255))
        draw_text("IN-MEMORY 16-BIT PCM WAVEFORM & ENVELOPE INSPECTOR", scope_x + 16, scope_y + 12, 13, SKYBLUE)

        mid_y = scope_y + (scope_h // 2)
        draw_line(scope_x + 10, mid_y, scope_x + scope_w - 10, mid_y, Color(35, 45, 65, 255))

        # Vertical dividing line for Tone 1 -> Tone 2 boundary (45ms / 110ms = ~40.9% width)
        split_x = scope_x + int((45.0 / 110.0) * scope_w)
        draw_line(split_x, scope_y + 35, split_x, scope_y + scope_h - 10, Color(60, 80, 120, 255))
        draw_text("B5 (45ms)", scope_x + 30, scope_y + scope_h - 22, 11, SKYBLUE)
        draw_text("E6 Ring-Out (65ms, k=6.5)", split_x + 20, scope_y + scope_h - 22, 11, GOLD)

        # Draw mathematical waveform curve
        steps = 180
        prev_px = scope_x + 10
        prev_py = mid_y
        for s in range(steps + 1):
            t_norm = float(s) / float(steps)
            px = scope_x + 10 + int(t_norm * (scope_w - 20))

            if t_norm < (45.0 / 110.0):
                # Tone 1
                prog = t_norm / (45.0 / 110.0)
                env = min(1.0, prog * 10.0)
                freq_factor = 28.0 * self.pitch
                wave_val = math.sin(t_norm * freq_factor * PI2) * env
                line_color = Color(100, 200, 255, 220)
            else:
                # Tone 2
                prog = (t_norm - (45.0 / 110.0)) / (65.0 / 110.0)
                env = math.exp(-6.5 * prog)
                freq_factor = 38.0 * self.pitch
                wave_val = math.sin(t_norm * freq_factor * PI2) * env
                line_color = Color(255, 215, 0, 230)

            # Modulate amplitude with trigger pulse or display subtle resting trace
            active_scale = 0.25 + 0.75 * self.trigger_pulse
            py = int(mid_y - (wave_val * (scope_h * 0.38) * active_scale))

            if s > 0:
                draw_line(prev_px, prev_py, px, py, line_color)
            prev_px = px
            prev_py = py

        # Top-Bar Dropdowns and Gamepad Status HUD clearance
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)
        end_drawing()

    def run(self, smoke_test: bool = False):
        frame_count = 0
        if smoke_test:
            # Trigger once to verify audio synthesis, buffer allocation and playback
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


# ==============================================================================
# MAIN EXECUTION ROUTER
# ==============================================================================
if __name__ == "__main__":
    is_smoke = "--smoke-test" in sys.argv
    SFXAuditionApp().run(smoke_test=is_smoke)
