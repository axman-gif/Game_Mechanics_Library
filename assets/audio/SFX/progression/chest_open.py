# -*- coding: utf-8 -*-
"""
Procedural Treasure Chest Open Sound Effect (SFX) Synthesizer
=============================================================
Type             : Procedural Audio SFX (Sound)
Target File      : assets/audio/SFX/progression/chest_open.py
Catalog ID       : sfx_prog_chest_open
Function Name    : create_chest_open_sfx
Category         : Progression & Economy (Loot, Rewards, Secret Chambers)
Waveforms Used   : Damped 850 Hz square impulse click + 4-note Lydian sine arpeggio
                   (D5, F#5, A5, C#6) with 0.25 Hz chorus shimmer + 60 Hz sub-bass warmth
                   undertone + 800 Hz to 3500 Hz dynamic bandpass sweep

Problem Solved:
  Eliminates external audio file dependencies (.wav/.mp3) by synthesizing an iconic,
  majestic secret discovery and treasure chest opening stinger directly in RAM.
  Packaged in-memory into a canonical 16-bit mono PCM 44-byte RIFF WAV container
  and loaded directly into a Raylib Sound hardware handle.

Waveform Theory & Mathematical Rationale:
  - Sequence Architecture:
      1. Mechanical Latch Click: 20 ms (0.020 s), 850 Hz square wave impulse with steep
         exponential damping: env(t) = exp(-12.0 * (t / 0.020)).
      2. 4-Note Ascending Lydian Arpeggio: 310 ms window (77.5 ms note spacing):
           - D5  (587.33 Hz) : Tonic root
           - F#5 (739.99 Hz) : Major 3rd (warm brightness)
           - A5  (880.00 Hz) : Perfect 5th (structural resonance)
           - C#6 (1108.73 Hz): Major 7th (majestic Lydian discovery aura)
      3. Amplitude Envelopes: 1 ms linear attack ramp, 380 ms exponential decay tail
         (k = 2.5): env(tau) = exp(-2.5 * (tau / 0.380)). Voices ring polyphonically.
      4. 0.25 Hz Chorus Shimmer: Dual detuned voices frequency-modulated by a 0.25 Hz
         LFO at ~6 cents depth for rich acoustic beating and celestial warmth.
      5. 60 Hz Sub-Bass Undertone: Pure 60 Hz sine wave providing chest cavity resonance.
      6. Dynamic Bandpass Sweep (800 Hz -> 3500 Hz): 2-pole resonant State-Variable
         Filter (SVF) sweeping center frequency upwards as the chest lid opens.
      7. Headroom: Normalized to ~25,000 signed 16-bit PCM target (~-2.35 dBFS headroom).

Direct C++ Raylib Translation (raylib.h):
  struct ChestOpenSFX {
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

sys.dont_write_bytecode = True

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

from pyray import *
from utils import *


# ==============================================================================
# PART 3: AUDIO SYNTHESIS CONSTANTS & TUNING PARAMETERS
# ==============================================================================
SAMPLE_RATE: int = 44100
PI2: float = 2.0 * math.pi

# 1. Mechanical Iron Latch Click
CLICK_FREQ: float = 850.0               # Hz (Damped square impulse)
CLICK_DURATION: float = 0.020           # 20 ms (0.020 s)

# 2. Four-Note Ascending Lydian Arpeggio (D5, F#5, A5, C#6)
NOTE_FREQS = [587.33, 739.99, 880.00, 1108.73]  # Hz
NOTE_NAMES = ["D5 (587 Hz)", "F#5 (740 Hz)", "A5 (880 Hz)", "C#6 (1108 Hz)"]
ARPEGGIO_DURATION: float = 0.310         # 310 ms arpeggio sequence window
NOTE_STEP: float = ARPEGGIO_DURATION / 4.0  # 77.5 ms between note onsets
ATTACK_DURATION: float = 0.001          # 1 ms linear attack ramp
DECAY_TAIL_DURATION: float = 0.380      # 380 ms exponential decay tail
DECAY_FACTOR_K: float = 2.5             # Exponential decay factor k=2.5

# 3. Chorus Shimmer & Sub-Bass Undertone
CHORUS_LFO_FREQ: float = 0.25           # 0.25 Hz LFO modulation
CHORUS_DEPTH: float = 0.0035            # ~6 cents detune modulation depth
SUB_BASS_FREQ: float = 60.0             # 60 Hz sub-bass warmth undertone

# 4. Dynamic Bandpass Sweep
BPF_START_FC: float = 800.0             # 800 Hz initial cutoff
BPF_END_FC: float = 3500.0              # 3500 Hz open cutoff
BPF_Q: float = 1.0                      # Bandpass resonance Q factor

# 5. Global Timing & PCM Target
TOTAL_DURATION: float = CLICK_DURATION + ARPEGGIO_DURATION + DECAY_TAIL_DURATION  # 0.710 s
TARGET_PEAK_AMPLITUDE: float = 25000.0   # Signed 16-bit PCM target (~-2.35 dBFS headroom)


# ==============================================================================
# PART 4: IN-MEMORY RIFF WAV PACKER HELPER (C++ 44-Byte Header Equivalent)
# ==============================================================================
def pack_riff_wav_mono_16bit(sample_rate: int, raw_samples: list) -> bytes:
    """Packs signed 16-bit PCM samples into an in-memory 44-byte RIFF/WAVE container."""
    num_samples = len(raw_samples)
    pcm_bytes = bytearray()
    for i in range(num_samples):
        val = raw_samples[i]
        clamped = max(-32767, min(32767, int(val)))
        pcm_bytes.extend(py_struct.pack('<h', clamped))

    fmt_size = 16
    audio_format = 1        # PCM
    num_channels = 1        # Mono
    byte_rate = sample_rate * num_channels * 2
    block_align = num_channels * 2
    bits_per_sample = 16
    data_size = len(pcm_bytes)
    total_chunk_size = 36 + data_size

    header = py_struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF', total_chunk_size, b'WAVE',
        b'fmt ', fmt_size, audio_format,
        num_channels, sample_rate, byte_rate,
        block_align, bits_per_sample,
        b'data', data_size
    )
    return bytes(header + pcm_bytes)


# ==============================================================================
# PART 5: CORE SYNTHESIS FUNCTION & STANDARDIZED CONTROL METHODS
# ==============================================================================
def create_chest_open_sfx(volume: float = 1.0) -> Sound:
    """Synthesizes a majestic treasure chest open stinger into a Raylib Sound handle."""
    total_samples = int(SAMPLE_RATE * TOTAL_DURATION)
    click_samples = int(SAMPLE_RATE * CLICK_DURATION)

    note_start_samples = [click_samples + int(n * NOTE_STEP * SAMPLE_RATE) for n in range(4)]
    click_track = [0.0] * total_samples
    raw_chime = [0.0] * total_samples
    sub_bass = [0.0] * total_samples

    # 1. Synthesize Initial Iron Latch Click (Damped 850 Hz Square Impulse, 20ms)
    for i in range(click_samples):
        t = float(i) / float(SAMPLE_RATE)
        progress = float(i) / float(click_samples)
        sq = 1.0 if math.sin(PI2 * CLICK_FREQ * t) >= 0.0 else -1.0
        click_track[i] = sq * math.exp(-12.0 * progress) * 0.40

    # 2. Synthesize 4-Note Lydian Pure Sine Arpeggio with 0.25 Hz Chorus Shimmer
    for n in range(4):
        base_freq = NOTE_FREQS[n]
        start_idx = note_start_samples[n]
        phase_main = 0.0
        phase_c1 = 0.0
        phase_c2 = 0.0

        for i in range(start_idx, total_samples):
            dt_note = float(i - start_idx) / float(SAMPLE_RATE)
            t_global = float(i) / float(SAMPLE_RATE)
            if dt_note > DECAY_TAIL_DURATION:
                break

            env_attack = dt_note / ATTACK_DURATION if dt_note < ATTACK_DURATION else 1.0
            env_decay = math.exp(-DECAY_FACTOR_K * (dt_note / DECAY_TAIL_DURATION))
            env = env_attack * env_decay

            lfo = math.sin(PI2 * CHORUS_LFO_FREQ * t_global)
            freq_c1 = base_freq * (1.0 + CHORUS_DEPTH * lfo)
            freq_c2 = base_freq * (1.0 - CHORUS_DEPTH * lfo * 0.70)

            phase_main += PI2 * base_freq / float(SAMPLE_RATE)
            phase_c1 += PI2 * freq_c1 / float(SAMPLE_RATE)
            phase_c2 += PI2 * freq_c2 / float(SAMPLE_RATE)

            voice = (0.50 * math.sin(phase_main) + 0.30 * math.sin(phase_c1) + 0.20 * math.sin(phase_c2))
            raw_chime[i] += voice * env

    # 3. Synthesize 60 Hz Sub-Bass Warmth Undertone
    for i in range(click_samples, total_samples):
        dt_sub = float(i - click_samples) / float(SAMPLE_RATE)
        t_global = float(i) / float(SAMPLE_RATE)
        sub_prog = dt_sub / (ARPEGGIO_DURATION + DECAY_TAIL_DURATION)
        if sub_prog <= 1.0:
            sub_bass[i] = 0.30 * math.sin(PI2 * SUB_BASS_FREQ * t_global) * math.exp(-3.2 * sub_prog)

    # 4. Filter Arpeggio through Dynamic Bandpass Sweep (800 Hz -> 3500 Hz) via SVF
    filtered_chime = [0.0] * total_samples
    s1, s2 = 0.0, 0.0
    sweep_span = int(SAMPLE_RATE * ARPEGGIO_DURATION)

    for i in range(total_samples):
        if i < click_samples:
            fc = BPF_START_FC
        elif i < click_samples + sweep_span:
            sweep_p = float(i - click_samples) / float(sweep_span)
            fc = BPF_START_FC + (BPF_END_FC - BPF_START_FC) * sweep_p
        else:
            fc = BPF_END_FC

        fc_clamped = max(40.0, min(float(fc), SAMPLE_RATE * 0.45))
        g = math.tan(math.pi * fc_clamped / float(SAMPLE_RATE))
        k = 1.0 / BPF_Q
        a1 = 1.0 / (1.0 + g * (g + k))
        a2, a3 = g * a1, g * (g * a1)

        x = raw_chime[i]
        v3 = x - s2
        v1 = a1 * s1 + a2 * v3  # Bandpass output
        v2 = s2 + a2 * s1 + a3 * v3
        s1, s2 = 2.0 * v1 - s1, 2.0 * v2 - s2
        filtered_chime[i] = v1

    # 5. Composite Mix & Normalization (~-2.35 dBFS Headroom)
    mixed_samples = [filtered_chime[i] + click_track[i] + sub_bass[i] for i in range(total_samples)]
    max_peak = max(abs(s) for s in mixed_samples)
    scale = (TARGET_PEAK_AMPLITUDE * max(0.0, min(1.0, volume))) / max_peak if max_peak > 0.0001 else TARGET_PEAK_AMPLITUDE

    pcm_samples = [max(-32767, min(32767, int(s * scale))) for s in mixed_samples]
    wav_bytes = pack_riff_wav_mono_16bit(SAMPLE_RATE, pcm_samples)
    wave = load_wave_from_memory(".wav", wav_bytes, len(wav_bytes))
    sound = load_sound_from_wave(wave)
    unload_wave(wave)
    return sound


create_sfx = create_chest_open_sfx


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
# PART 6: STANDALONE AUDITION WORKBENCH & VISUAL TELEMETRY STAGE
# ==============================================================================
class ChestSparkle:
    """Visual reward particle emitted when the treasure chest opens."""
    def __init__(self, x: float, y: float, vx: float, vy: float, life: float, color: Any):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life, self.max_life = life, life
        self.color = color

    def update(self, dt: float) -> bool:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 80.0 * dt
        self.life -= dt
        return self.life > 0.0

    def draw(self):
        progress = max(0.0, self.life / self.max_life)
        alpha = int(255 * progress)
        if hasattr(self.color, 'r'):
            r, g, b = int(self.color.r), int(self.color.g), int(self.color.b)
        else:
            r, g, b = int(self.color[0]), int(self.color[1]), int(self.color[2])
        c = Color(r, g, b, alpha)
        sz = max(1.5, 4.5 * progress)
        draw_circle(int(self.x), int(self.y), sz, c)
        draw_line(int(self.x - sz * 2.2), int(self.y), int(self.x + sz * 2.2), int(self.y), c)
        draw_line(int(self.x), int(self.y - sz * 2.2), int(self.x), int(self.y + sz * 2.2), c)


class SFXAuditionApp:
    """Interactive previewer workbench with procedural chest visualizer and oscilloscope."""
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        init_window(self.screen_width, self.screen_height, "SFX Workbench - Chest Open (assets/audio/SFX/progression/chest_open.py)")
        set_target_fps(60)
        init_audio_device()

        self.sound = create_chest_open_sfx()
        self.trigger_pulse = 0.0
        self.volume = 0.90
        self.pitch = 1.0
        self.trigger_count = 0
        self.lid_open_amount = 0.0
        self.sparkles = []
        self.ray_rotation = 0.0

    def trigger(self):
        """Triggers sound playback with current pitch/volume and animates visualizer."""
        play_sfx(self.sound, self.volume, self.pitch)
        self.trigger_pulse = 1.0
        self.trigger_count += 1
        self.lid_open_amount = 1.0

        chest_cx, chest_cy = 600.0, 280.0
        particle_colors = [GOLD, YELLOW, Color(255, 100, 100, 255), Color(100, 230, 255, 255), Color(120, 255, 140, 255)]
        for k in range(24):
            angle = -math.pi * 0.5 + (float(k - 12) / 12.0) * 1.1
            speed = 90.0 + (float(k % 5) * 35.0)
            self.sparkles.append(ChestSparkle(chest_cx, chest_cy, math.cos(angle) * speed, math.sin(angle) * speed, 0.65, particle_colors[k % 5]))

    def update(self):
        dt = min(get_frame_time(), 0.05)
        if self.trigger_pulse > 0.0:
            self.trigger_pulse = max(0.0, self.trigger_pulse - dt * 2.2)
        if self.lid_open_amount > 0.0:
            self.lid_open_amount = max(0.0, self.lid_open_amount - dt * 1.5)

        self.ray_rotation = (self.ray_rotation + dt * 0.8) % PI2
        self.sparkles = [sp for sp in self.sparkles if sp.update(dt)]

        # Trigger inputs: Space, Enter, Left Click, or Gamepad Face Down (A / Cross)
        key_trig = is_key_pressed(KEY_SPACE) or is_key_pressed(KEY_ENTER) or is_mouse_button_pressed(MOUSE_BUTTON_LEFT)
        pad_trig = is_gamepad_available(0) and is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_FACE_DOWN)
        if key_trig or pad_trig:
            self.trigger()

        # Pitch adjustments: Up/Down arrows or Gamepad D-pad Up/Down
        if is_key_pressed(KEY_UP) or (is_gamepad_available(0) and is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_UP)):
            self.pitch = min(2.0, self.pitch + 0.1)
        elif is_key_pressed(KEY_DOWN) or (is_gamepad_available(0) and is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_DOWN)):
            self.pitch = max(0.5, self.pitch - 0.1)

        # Volume adjustments: Right/Left arrows or Gamepad D-pad Right/Left
        if is_key_pressed(KEY_RIGHT) or (is_gamepad_available(0) and is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_RIGHT)):
            self.volume = min(1.0, self.volume + 0.05)
        elif is_key_pressed(KEY_LEFT) or (is_gamepad_available(0) and is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_LEFT)):
            self.volume = max(0.0, self.volume - 0.05)

        # Reset controls: [R] Key or Gamepad Start
        pad_reset = is_gamepad_available(0) and is_gamepad_button_pressed(0, GAMEPAD_BUTTON_MIDDLE_RIGHT)
        if is_key_pressed(KEY_R) or pad_reset:
            self.pitch, self.volume = 1.0, 0.90

    def draw(self):
        begin_drawing()
        clear_background(Color(14, 18, 28, 255))

        # Header (Top HUD region x=450..980, y=14..48 kept clear for settings bar)
        draw_text("PROCEDURAL SFX AUDITION WORKBENCH", 24, 20, 20, RAYWHITE)
        draw_text("Asset: assets/audio/SFX/progression/chest_open.py | Waveform: Latch Click + 4-Note Lydian Sine Arpeggio", 24, 50, 13, GOLD)

        # Left Column: Control Panel & Specifications Card
        panel_y = 90
        panel_w = 380
        panel_h = 590
        draw_rectangle(24, panel_y, panel_w, panel_h, Color(22, 28, 44, 255))
        draw_rectangle_lines(24, panel_y, panel_w, panel_h, Color(55, 70, 110, 255))

        draw_text("CONTROLS & SHORTCUTS", 42, panel_y + 16, 15, YELLOW)
        draw_text("- [Space] / [Enter] / [Click] : Open Chest (Trigger SFX)", 42, panel_y + 44, 12, RAYWHITE)
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
        draw_text("Latch Click: 850 Hz Damped Square (20ms)", 42, panel_y + 304, 12, RAYWHITE)
        draw_text("Arpeggio   : D5 -> F#5 -> A5 -> C#6 (310ms)", 42, panel_y + 326, 12, YELLOW)
        draw_text("Harmony    : D Lydian Majestic 7th Chord", 42, panel_y + 348, 12, RAYWHITE)
        draw_text("Envelope   : 1ms Attack -> 380ms Exp Decay (k=2.5)", 42, panel_y + 370, 12, LIGHTGRAY)
        draw_text("Chorus     : 0.25 Hz Stereo Shimmer LFO", 42, panel_y + 392, 12, SKYBLUE)
        draw_text("Undertone  : 60 Hz Sub-Bass Warmth", 42, panel_y + 414, 12, RAYWHITE)
        draw_text("Filter     : 800 Hz -> 3500 Hz Dynamic SVF Sweep", 42, panel_y + 436, 12, GREEN)
        draw_text("PCM Headroom: ~25,000 Peak (-2.35 dBFS)", 42, panel_y + 458, 12, LIGHTGRAY)

        draw_line(42, panel_y + 482, 24 + panel_w - 42, panel_y + 482, Color(55, 70, 110, 255))
        draw_text("C++ EQUIVALENT ARCHITECTURE", 42, panel_y + 496, 13, SKYBLUE)
        draw_text("Wave w = LoadWaveFromMemory(...);", 42, panel_y + 520, 11, LIGHTGRAY)
        draw_text("Sound s = LoadSoundFromWave(w);", 42, panel_y + 540, 11, LIGHTGRAY)
        draw_text("UnloadWave(w); // Retains audio device RAM", 42, panel_y + 560, 11, LIGHTGRAY)

        # Right Stage: Visualizer & Oscilloscope
        stage_x, stage_y, stage_w, stage_h = 420, 90, 836, 590
        draw_rectangle(stage_x, stage_y, stage_w, stage_h, Color(18, 24, 38, 255))
        draw_rectangle_lines(stage_x, stage_y, stage_w, stage_h, Color(55, 70, 110, 255))
        draw_text("INTERACTIVE TREASURE CHEST DISCOVERY STAGE", stage_x + 20, stage_y + 16, 15, GOLD)

        # Procedural 2D Animated Treasure Chest
        chest_cx, chest_cy = stage_x + 180, stage_y + 185
        box_w, box_h = 170, 80
        box_x, box_y = int(chest_cx - box_w // 2), int(chest_cy - box_h // 2 + 15)

        # Light Rays when chest lid opens
        if self.lid_open_amount > 0.05:
            ray_alpha = int(140 * self.lid_open_amount)
            for r_idx in range(8):
                angle = self.ray_rotation + (float(r_idx) / 8.0) * PI2
                rx = chest_cx + math.cos(angle) * (110.0 + self.lid_open_amount * 45.0)
                ry = (box_y - 10) + math.sin(angle) * (80.0 + self.lid_open_amount * 35.0)
                draw_line(int(chest_cx), int(box_y - 10), int(rx), int(ry), Color(255, 220, 80, ray_alpha))

        # Chest Base Body
        draw_rectangle(box_x, box_y, box_w, box_h, Color(95, 50, 20, 255))
        draw_rectangle_lines(box_x, box_y, box_w, box_h, Color(50, 25, 10, 255))
        draw_line(box_x + 4, box_y + 26, box_x + box_w - 4, box_y + 26, Color(75, 40, 15, 255))
        draw_line(box_x + 4, box_y + 52, box_x + box_w - 4, box_y + 52, Color(75, 40, 15, 255))
        draw_rectangle(box_x, box_y, 14, box_h, Color(65, 75, 90, 255))
        draw_rectangle(box_x + box_w - 14, box_y, 14, box_h, Color(65, 75, 90, 255))
        draw_rectangle(box_x + (box_w // 2) - 8, box_y, 16, box_h, Color(65, 75, 90, 255))

        # Golden treasure mound inside chest when open
        if self.lid_open_amount > 0.1:
            gold_alpha = int(240 * min(1.0, self.lid_open_amount * 1.5))
            draw_ellipse(int(chest_cx), box_y + 10, box_w // 2 - 18, 16, Color(255, 215, 0, gold_alpha))
            draw_circle(int(chest_cx - 30), box_y + 8, 4, Color(255, 60, 60, gold_alpha))
            draw_circle(int(chest_cx + 25), box_y + 11, 4, Color(60, 230, 80, gold_alpha))
            draw_circle(int(chest_cx + 4), box_y + 6, 5, Color(100, 220, 255, gold_alpha))

        # Chest Hinged Lid (Swings upward when triggered)
        lid_h = 32
        lid_lift = int(self.lid_open_amount * 42.0)
        lid_y = box_y - lid_h - lid_lift
        if self.trigger_pulse > 0.05:
            draw_rectangle_lines(box_x - 3, lid_y - 3, box_w + 6, box_h + lid_h + lid_lift + 6, Color(255, 215, 0, int(100 * self.trigger_pulse)))

        draw_rectangle(box_x - 2, lid_y, box_w + 4, lid_h, Color(115, 60, 25, 255))
        draw_rectangle_lines(box_x - 2, lid_y, box_w + 4, lid_h, Color(60, 30, 12, 255))
        draw_rectangle(box_x - 2, lid_y, 14, lid_h, Color(65, 75, 90, 255))
        draw_rectangle(box_x + box_w - 12, lid_y, 14, lid_h, Color(65, 75, 90, 255))
        draw_rectangle(box_x + (box_w // 2) - 8, lid_y, 16, lid_h, Color(65, 75, 90, 255))

        # Golden Lock Hasp
        hasp_y = box_y - 6 - (lid_lift // 2)
        hasp_color = GOLD if self.trigger_pulse > 0.1 else Color(180, 140, 30, 255)
        draw_rectangle(int(chest_cx - 9), int(hasp_y), 18, 20, hasp_color)
        draw_circle(int(chest_cx), int(hasp_y + 10), 3, DARKGRAY)

        for sp in self.sparkles:
            sp.draw()

        draw_text("Procedural Treasure Chest Primitive", int(chest_cx) - 110, box_y + box_h + 12, 13, RAYWHITE)
        draw_text("Press [Space] or Click to Open", int(chest_cx) - 85, box_y + box_h + 30, 11, LIGHTGRAY)

        # Energy Peak Meter
        meter_x, meter_y, meter_w, meter_h = stage_x + 380, stage_y + 115, 420, 32
        draw_rectangle(meter_x, meter_y, meter_w, meter_h, Color(12, 16, 26, 255))
        draw_rectangle_lines(meter_x, meter_y, meter_w, meter_h, Color(55, 70, 110, 255))
        pulse_fill = int(self.trigger_pulse * (meter_w - 4))
        if pulse_fill > 0:
            draw_rectangle(meter_x + 2, meter_y + 2, pulse_fill, meter_h - 4, Color(int(255 * self.trigger_pulse), int(215 * self.trigger_pulse), 0, 230))
        draw_text("Instantaneous Energy Peak Meter", meter_x, meter_y - 20, 12, SKYBLUE)
        draw_text(f"{int(self.trigger_pulse * 100)}%", meter_x + meter_w - 40, meter_y + 8, 12, RAYWHITE)

        # Four-Note Lydian Modal Frequency Trajectory Box
        notes_box_y = stage_y + 175
        draw_rectangle(meter_x, notes_box_y, meter_w, 110, Color(14, 20, 32, 255))
        draw_rectangle_lines(meter_x, notes_box_y, meter_w, 110, Color(55, 70, 110, 255))
        draw_text("FOUR-NOTE LYDIAN ARPEGGIO TRAJECTORY (310ms)", meter_x + 14, notes_box_y + 12, 12, GOLD)

        card_w, card_h = 92, 60
        for n_idx in range(4):
            cx = meter_x + 14 + n_idx * (card_w + 8)
            cy = notes_box_y + 36
            note_active = (self.trigger_pulse > 0.05) and (
                (n_idx == 0 and self.trigger_pulse > 0.75)
                or (n_idx == 1 and 0.50 < self.trigger_pulse <= 0.75)
                or (n_idx == 2 and 0.25 < self.trigger_pulse <= 0.50)
                or (n_idx == 3 and self.trigger_pulse <= 0.25)
            )
            draw_rectangle(cx, cy, card_w, card_h, Color(30, 42, 65, 255) if note_active else Color(20, 26, 40, 255))
            draw_rectangle_lines(cx, cy, card_w, card_h, GOLD if note_active else Color(60, 80, 120, 255))
            draw_text(NOTE_NAMES[n_idx].split()[0], cx + 8, cy + 10, 13, YELLOW if note_active else RAYWHITE)
            draw_text(f"{int(NOTE_FREQS[n_idx])} Hz", cx + 8, cy + 28, 11, LIGHTGRAY)
            draw_text(["Root", "Maj 3", "Perf 5", "Maj 7"][n_idx], cx + 8, cy + 44, 9, SKYBLUE)

        # Oscilloscope Waveform & Dynamic Filter Sweep Inspector (Lower Stage)
        scope_x, scope_y, scope_w, scope_h = stage_x + 20, stage_y + 315, stage_w - 40, 245
        draw_rectangle(scope_x, scope_y, scope_w, scope_h, Color(12, 16, 26, 255))
        draw_rectangle_lines(scope_x, scope_y, scope_w, scope_h, Color(55, 70, 110, 255))
        draw_text("IN-MEMORY 16-BIT PCM WAVEFORM & DYNAMIC SVF SWEEP INSPECTOR", scope_x + 16, scope_y + 12, 13, SKYBLUE)

        mid_y = scope_y + (scope_h // 2)
        draw_line(scope_x + 10, mid_y, scope_x + scope_w - 10, mid_y, Color(35, 45, 65, 255))

        click_px = scope_x + int((20.0 / 710.0) * scope_w)
        arp_px = scope_x + int(((20.0 + 310.0) / 710.0) * scope_w)
        draw_line(click_px, scope_y + 35, click_px, scope_y + scope_h - 10, Color(70, 90, 130, 255))
        draw_line(arp_px, scope_y + 35, arp_px, scope_y + scope_h - 10, Color(70, 90, 130, 255))
        draw_text("Latch (20ms)", scope_x + 14, scope_y + scope_h - 22, 10, RED)
        draw_text("4-Note Lydian Arpeggio (310ms)", click_px + 14, scope_y + scope_h - 22, 10, YELLOW)
        draw_text("Exp Tail (380ms, k=2.5)", arp_px + 14, scope_y + scope_h - 22, 10, GOLD)

        # Filter Sweep Trajectory Curve (800 Hz -> 3500 Hz dynamic bandpass)
        sweep_steps = 100
        prev_fx, prev_fy = scope_x + 10, scope_y + scope_h - 40
        for s in range(sweep_steps + 1):
            t_norm = float(s) / float(sweep_steps)
            fx = scope_x + 10 + int(t_norm * (scope_w - 20))
            if t_norm < (20.0 / 710.0):
                fc_val = 800.0
            elif t_norm < (330.0 / 710.0):
                fc_val = 800.0 + (3500.0 - 800.0) * ((t_norm - (20.0 / 710.0)) / (310.0 / 710.0))
            else:
                fc_val = 3500.0
            fy = int(scope_y + scope_h - 35 - ((fc_val - 800.0) / 2700.0) * (scope_h * 0.45))
            if s > 0:
                draw_line(prev_fx, prev_fy, fx, fy, Color(60, 200, 100, 160))
            prev_fx, prev_fy = fx, fy
        draw_text("SVF Sweep: 800Hz -> 3500Hz", scope_x + scope_w - 180, scope_y + 38, 10, Color(80, 220, 120, 255))

        # Oscilloscope Waveform Curve
        steps = 220
        prev_px, prev_py = scope_x + 10, mid_y
        for s in range(steps + 1):
            t_norm = float(s) / float(steps)
            px = scope_x + 10 + int(t_norm * (scope_w - 20))
            if t_norm < (20.0 / 710.0):
                prog = t_norm / (20.0 / 710.0)
                sq = 1.0 if math.sin(t_norm * 140.0 * PI2) >= 0.0 else -1.0
                wave_val = sq * math.exp(-12.0 * prog) * 0.45
                line_color = Color(255, 120, 120, 230)
            elif t_norm < (330.0 / 710.0):
                prog = (t_norm - (20.0 / 710.0)) / (310.0 / 710.0)
                note_idx = min(3, int(prog * 4.0))
                freq_mult = [22.0, 28.0, 34.0, 42.0][note_idx] * self.pitch
                wave_val = math.sin(t_norm * freq_mult * PI2) * math.exp(-1.8 * (prog * 4.0 - note_idx))
                line_color = Color(100, 220, 255, 230)
            else:
                prog = (t_norm - (330.0 / 710.0)) / (380.0 / 710.0)
                wave_val = math.sin(t_norm * 42.0 * self.pitch * PI2) * math.exp(-DECAY_FACTOR_K * prog)
                line_color = Color(255, 215, 0, 230)

            py = int(mid_y - (wave_val * (scope_h * 0.36) * (0.20 + 0.80 * self.trigger_pulse)))
            if s > 0:
                draw_line(prev_px, prev_py, px, py, line_color)
            prev_px, prev_py = px, py

        # Top-Bar Dropdowns and Gamepad Status HUD clearance
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)
        end_drawing()

    def run(self, smoke_test: bool = False):
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


# ==============================================================================
# MAIN EXECUTION ROUTER
# ==============================================================================
if __name__ == "__main__":
    is_smoke = "--smoke-test" in sys.argv
    SFXAuditionApp().run(smoke_test=is_smoke)
