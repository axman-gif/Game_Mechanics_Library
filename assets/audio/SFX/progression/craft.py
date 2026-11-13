# -*- coding: utf-8 -*-
"""
Procedural Blacksmith Craft Sound Effect (SFX) Synthesizer
==========================================================
Type             : Procedural Audio SFX (Sound)
Target File      : assets/audio/SFX/progression/craft.py
Waveforms Used   : Double steel modal sine cluster (1180/1770/2950 Hz) + 95 Hz anvil body resonance
Category         : Progression & Economy

Problem Solved:
  Synthesizes an authentic blacksmith forging and crafting success cue directly in memory
  from pure mathematical waveforms into a 16-bit PCM buffer loaded into a Raylib Sound struct.

Waveform Theory & Mathematical Rationale:
  - Steel Inharmonic Modes: High bending modes of steel deck: f1=1180 Hz, f2=1770 Hz, f3=2950 Hz.
  - Anvil Body Resonance: Heavy 95 Hz sub-impact thud representing cast iron base and timber log mass.
  - Double Strike Sequence:
      Strike 1 (0ms): Light positioning tap (amp 0.45), 0.5ms attack, decay k=9.0.
      Strike 2 (90ms): Heavy blow (amp 1.0), 0.5ms attack, decay k=3.2, injecting 95 Hz body resonance.
  - Filters: 2-pole biquad bandpass filter at 2 kHz (Q=1.0) + 1st-order highpass filter at 70 Hz.
  - Headroom: Normalized to 28,000 in signed 16-bit PCM (~-1.4 dBFS).

Direct C++ Translation (raylib.h):
  struct CraftSFX {
      Sound sound;
      void Play(float vol, float pitch) { SetSoundVolume(sound, vol); SetSoundPitch(sound, pitch); PlaySound(sound); }
      void Stop() { StopSound(sound); }
      void Unload() { UnloadSound(sound); }
  };
"""

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
# AUDIO SYNTHESIS CONSTANTS
# ==============================================================================
SAMPLE_RATE: int = 44100
PI2: float = 2.0 * math.pi
STRIKE1_OFFSET: float = 0.000      # Strike 1 starts at 0 ms
STRIKE2_OFFSET: float = 0.090      # Strike 2 heavy blow at 90 ms
TOTAL_DURATION: float = 0.340      # Total sound duration 340 ms
ATTACK_DURATION: float = 0.0005    # 0.5 ms impact attack ramp
DECAY_K1: float = 9.0              # Strike 1 exponential decay constant
DECAY_K2: float = 3.2              # Strike 2 exponential decay constant
STRIKE1_AMP_RATIO: float = 0.45    # Strike 1 amplitude relative to Strike 2
STEEL_MODE_F1: float = 1180.0      # Hz (Fundamental steel deck mode)
STEEL_MODE_F2: float = 1770.0      # Hz (Secondary modal partial)
STEEL_MODE_F3: float = 2950.0      # Hz (Tertiary modal partial)
ANVIL_BODY_FREQ: float = 95.0      # Hz (Cast iron anvil base resonance)
BPF_CENTER_FREQ: float = 2000.0    # Hz (Biquad band-pass center frequency)
BPF_Q: float = 1.0                 # Quality factor Q for band-pass filter
HPF_CUTOFF: float = 70.0           # Hz (1st-order high-pass filter cutoff)
TARGET_PEAK_AMPLITUDE: float = 28000.0  # Peak signed 16-bit PCM target (~-1.4 dBFS)


def pack_riff_wav_mono_16bit(sample_rate: int, raw_samples: list) -> bytes:
    """Packs signed 16-bit PCM integer samples into canonical 44-byte RIFF/WAVE container."""
    pcm_bytes = bytearray()
    for val in raw_samples:
        clamped = max(-32767, min(32767, int(val)))
        pcm_bytes.extend(py_struct.pack('<h', clamped))

    data_size = len(pcm_bytes)
    header = py_struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF', 36 + data_size, b'WAVE',
        b'fmt ', 16, 1, 1, sample_rate, sample_rate * 2, 2, 16,
        b'data', data_size
    )
    return bytes(header + pcm_bytes)


def create_craft_sfx(volume: float = 1.0) -> Sound:
    """Synthesizes a double blacksmith anvil strike crafting cue into a Raylib Sound struct."""
    num_samples = int(SAMPLE_RATE * TOTAL_DURATION)
    strike1_samples = int(SAMPLE_RATE * STRIKE2_OFFSET)
    attack_samples = max(1, int(SAMPLE_RATE * ATTACK_DURATION))

    raw_modal = [0.0] * num_samples
    body_samples = [0.0] * num_samples

    # 1. Synthesize Strike 1 (0-90ms) and Strike 2 (90-340ms)
    for i in range(num_samples):
        t = float(i) / float(SAMPLE_RATE)
        if i < strike1_samples:
            # Strike 1: Positioning Tap
            t1 = t
            env1 = float(i) / float(attack_samples) if i < attack_samples else math.exp(-DECAY_K1 * (t1 - ATTACK_DURATION) / (STRIKE2_OFFSET - ATTACK_DURATION))
            m1 = math.sin(PI2 * STEEL_MODE_F1 * t1)
            m2 = math.sin(PI2 * STEEL_MODE_F2 * t1)
            m3 = math.sin(PI2 * STEEL_MODE_F3 * t1)
            transient = 0.25 * math.sin(PI2 * 4400.0 * t1) * math.exp(-t1 / 0.0015)
            raw_modal[i] = ((0.50 * m1 + 0.32 * m2 + 0.18 * m3) + transient) * (STRIKE1_AMP_RATIO * env1)
        else:
            # Strike 2: Heavy Blow
            t2 = t - STRIKE2_OFFSET
            i2 = i - strike1_samples
            strike2_duration = TOTAL_DURATION - STRIKE2_OFFSET
            env2 = float(i2) / float(attack_samples) if i2 < attack_samples else math.exp(-DECAY_K2 * (t2 - ATTACK_DURATION) / (strike2_duration - ATTACK_DURATION))
            m1 = math.sin(PI2 * STEEL_MODE_F1 * t2)
            m2 = math.sin(PI2 * STEEL_MODE_F2 * t2)
            m3 = math.sin(PI2 * STEEL_MODE_F3 * t2)
            transient = 0.35 * math.sin(PI2 * 4800.0 * t2) * math.exp(-t2 / 0.002)
            raw_modal[i] = ((0.50 * m1 + 0.32 * m2 + 0.18 * m3) + transient) * env2
            tail_fade = max(0.0, 1.0 - (t2 / strike2_duration) ** 3)
            body_samples[i] = 0.35 * math.sin(PI2 * ANVIL_BODY_FREQ * t2) * math.exp(-5.0 * t2) * tail_fade

    # 2. 2-Pole Biquad Band-Pass Filter at 2 kHz (Q = 1.0)
    w0 = PI2 * BPF_CENTER_FREQ / float(SAMPLE_RATE)
    alpha = math.sin(w0) / (2.0 * BPF_Q)
    b0, b1, b2 = alpha / (1.0 + alpha), 0.0, -alpha / (1.0 + alpha)
    a1 = (-2.0 * math.cos(w0)) / (1.0 + alpha)
    a2 = (1.0 - alpha) / (1.0 + alpha)

    filtered_modal = [0.0] * num_samples
    x1 = x2 = y1 = y2 = 0.0
    for i in range(num_samples):
        x0 = raw_modal[i]
        y0 = b0 * x0 + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1 = x1, x0
        y2, y1 = y1, y0
        filtered_modal[i] = y0 + body_samples[i]

    # 3. 1st-Order High-Pass Filter (fc = 70 Hz) to eliminate DC offset
    rc = 1.0 / (PI2 * HPF_CUTOFF)
    dt = 1.0 / float(SAMPLE_RATE)
    alpha_hp = rc / (rc + dt)
    final_samples = [0.0] * num_samples
    prev_x = prev_y = 0.0
    for i in range(num_samples):
        x = filtered_modal[i]
        y = alpha_hp * (prev_y + x - prev_x)
        prev_x, prev_y = x, y
        final_samples[i] = y

    # 4. Peak Normalization and Scaling
    max_abs = max((abs(s) for s in final_samples), default=0.001)
    scale = (TARGET_PEAK_AMPLITUDE * max(0.0, min(1.0, volume))) / max_abs if max_abs > 0.0001 else TARGET_PEAK_AMPLITUDE
    pcm_samples = [max(-32767, min(32767, int(y * scale))) for y in final_samples]

    wav_bytes = pack_riff_wav_mono_16bit(SAMPLE_RATE, pcm_samples)
    wave = load_wave_from_memory(".wav", wav_bytes, len(wav_bytes))
    sound = load_sound_from_wave(wave)
    unload_wave(wave)
    return sound


# Standardized alias mapping
create_sfx = create_craft_sfx


def play_sfx(sound: Sound, volume: float = 1.0, pitch: float = 1.0) -> None:
    """Plays craft sound effect with volume and pitch scaling."""
    set_sound_volume(sound, max(0.0, min(1.0, volume)))
    set_sound_pitch(sound, max(0.5, min(2.0, pitch)))
    play_sound(sound)


def stop_sfx(sound: Sound) -> None:
    """Stops sound effect playback immediately."""
    stop_sound(sound)


def unload_sfx(sound: Sound) -> None:
    """Frees the Sound resource from audio hardware memory."""
    unload_sound(sound)


# ==============================================================================
# AUDITION WORKBENCH & VISUALIZERS
# ==============================================================================
class AnvilSpark:
    """Spark particle ejected from anvil hammer strike."""
    def __init__(self, x: float, y: float, vx: float, vy: float, life: float, color: Any, size: float = 3.0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size

    def update(self, dt: float) -> bool:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 420.0 * dt
        self.vx *= max(0.0, 1.0 - 1.2 * dt)
        self.life -= dt
        return self.life > 0.0

    def draw(self):
        progress = max(0.0, self.life / self.max_life)
        alpha = int(255 * progress)
        if isinstance(self.color, (tuple, list)):
            r, g, b = int(self.color[0]), int(self.color[1]), int(self.color[2])
        else:
            r, g, b = int(self.color.r), int(self.color.g), int(self.color.b)
        c = Color(r, g, b, max(0, min(255, alpha)))
        sz = max(1.0, self.size * progress)
        draw_circle(int(self.x), int(self.y), sz, c)
        draw_line(int(self.x), int(self.y), int(self.x - self.vx * 0.025), int(self.y - self.vy * 0.025), c)


class SFXAuditionApp:
    """Interactive audition workbench with animated blacksmith anvil, hammer, sparks, and oscilloscope."""
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        init_window(self.screen_width, self.screen_height, "SFX Workbench - Blacksmith Craft (assets/audio/SFX/progression/craft.py)")
        set_target_fps(60)
        init_audio_device()

        self.sound = create_craft_sfx()
        self.volume = 0.90
        self.pitch = 1.0
        self.trigger_count = 0

        self.anim_timer = 1.0
        self.is_animating = False
        self.strike1_fired = False
        self.strike2_fired = False
        self.anvil_glow = 0.0
        self.sparks = []
        self.scope_points = self._generate_scope_data()

    def _generate_scope_data(self) -> list:
        points = []
        steps = 240
        for s in range(steps + 1):
            t_norm = float(s) / float(steps)
            t_sec = t_norm * TOTAL_DURATION
            if t_sec < STRIKE2_OFFSET:
                prog1 = max(0.0, t_sec / STRIKE2_OFFSET)
                env = STRIKE1_AMP_RATIO * math.exp(-DECAY_K1 * prog1)
                wave = math.sin(PI2 * 18.0 * t_norm) * env
            else:
                prog2 = max(0.0, (t_sec - STRIKE2_OFFSET) / (TOTAL_DURATION - STRIKE2_OFFSET))
                env = math.exp(-DECAY_K2 * prog2)
                wave = (0.75 * math.sin(PI2 * 32.0 * t_norm) + 0.35 * math.sin(PI2 * 6.0 * t_norm)) * env
            points.append(wave)
        return points

    def trigger(self):
        """Triggers craft sound effect playback and starts synchronized anvil animation."""
        play_sfx(self.sound, self.volume, self.pitch)
        self.anim_timer = 0.0
        self.is_animating = True
        self.strike1_fired = False
        self.strike2_fired = False
        self.trigger_count += 1

    def _spawn_sparks(self, cx: float, cy: float, count: int, heavy: bool):
        for k in range(count):
            angle = -math.pi * (0.15 + 0.70 * (float(k) / max(1, count - 1)))
            speed = 120.0 + (float(k % 5) * 50.0) if not heavy else 220.0 + (float(k % 7) * 70.0)
            vx = math.cos(angle) * speed + (float(k % 3 - 1) * 30.0)
            vy = math.sin(angle) * speed
            life = 0.25 + (float(k % 4) * 0.08) if not heavy else 0.40 + (float(k % 5) * 0.10)
            color = RAYWHITE if (heavy and k % 3 == 0) else (GOLD if k % 2 == 0 else ORANGE)
            self.sparks.append(AnvilSpark(cx, cy, vx, vy, life, color, 3.5 if heavy else 2.5))

    def update(self):
        dt = min(get_frame_time(), 0.05)
        if self.is_animating:
            self.anim_timer += dt
            if not self.strike1_fired:
                self.strike1_fired = True
                self._spawn_sparks(620.0, 310.0, 10, heavy=False)
                self.anvil_glow = max(self.anvil_glow, 0.45)
            if self.anim_timer >= STRIKE2_OFFSET and not self.strike2_fired:
                self.strike2_fired = True
                self._spawn_sparks(620.0, 310.0, 32, heavy=True)
                self.anvil_glow = 1.0
            if self.anim_timer >= 0.45:
                self.is_animating = False

        if self.anvil_glow > 0.0:
            self.anvil_glow = max(0.0, self.anvil_glow - dt * 2.8)

        self.sparks = [sp for sp in self.sparks if sp.update(dt)]

        pad_down = is_gamepad_available(0) and is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_FACE_DOWN)
        if is_key_pressed(KEY_SPACE) or is_key_pressed(KEY_ENTER) or is_mouse_button_pressed(MOUSE_BUTTON_LEFT) or pad_down:
            self.trigger()

        # Pitch & Volume Adjustments
        if is_key_pressed(KEY_UP) or (is_gamepad_available(0) and is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_UP)):
            self.pitch = min(2.0, self.pitch + 0.1)
        elif is_key_pressed(KEY_DOWN) or (is_gamepad_available(0) and is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_DOWN)):
            self.pitch = max(0.5, self.pitch - 0.1)
        if is_key_pressed(KEY_RIGHT) or (is_gamepad_available(0) and is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_RIGHT)):
            self.volume = min(1.0, self.volume + 0.05)
        elif is_key_pressed(KEY_LEFT) or (is_gamepad_available(0) and is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_LEFT)):
            self.volume = max(0.0, self.volume - 0.05)

        # Reset parameters
        pad_reset = is_gamepad_available(0) and (is_gamepad_button_pressed(0, GAMEPAD_BUTTON_MIDDLE_RIGHT) or is_gamepad_button_pressed(0, GAMEPAD_BUTTON_MIDDLE_LEFT))
        if is_key_pressed(KEY_R) or pad_reset:
            self.pitch = 1.0
            self.volume = 0.90

    def draw(self):
        begin_drawing()
        clear_background(Color(14, 18, 28, 255))

        # Header (keeps top-bar region x=450..980, y=14..48 completely clear)
        draw_text("PROCEDURAL SFX AUDITION WORKBENCH", 24, 20, 20, RAYWHITE)
        draw_text("Asset: assets/audio/SFX/progression/craft.py | Blacksmith Double Anvil Strike (1180/1770/2950 Hz)", 24, 50, 13, GOLD)

        # Left Control & Telemetry Panel
        py, pw, ph = 90, 380, 590
        draw_rectangle(24, py, pw, ph, Color(22, 28, 44, 255))
        draw_rectangle_lines(24, py, pw, ph, Color(55, 70, 110, 255))

        draw_text("CONTROLS & SHORTCUTS", 42, py + 16, 15, YELLOW)
        draw_text("- [Space] / [Enter] / [Click] : Trigger Craft SFX", 42, py + 44, 12, RAYWHITE)
        draw_text("- [Up] / [Down] Arrows        : Pitch (+/- 0.1x)", 42, py + 68, 12, RAYWHITE)
        draw_text("- [Right] / [Left] Arrows     : Volume (+/- 0.05)", 42, py + 92, 12, RAYWHITE)
        draw_text("- [R] Key / Gamepad Start     : Reset All Parameters", 42, py + 116, 12, RAYWHITE)

        draw_line(42, py + 144, 24 + pw - 42, py + 144, Color(55, 70, 110, 255))
        draw_text("CURRENT TELEMETRY", 42, py + 158, 15, SKYBLUE)
        draw_text(f"Total Triggers : {self.trigger_count}", 42, py + 186, 13, LIGHTGRAY)
        draw_text(f"Active Pitch   : {self.pitch:.1f}x", 42, py + 210, 13, GREEN)
        draw_text(f"Master Volume  : {int(self.volume * 100)}%", 42, py + 234, 13, GREEN)

        draw_line(42, py + 262, 24 + pw - 42, py + 262, Color(55, 70, 110, 255))
        draw_text("SYNTHESIS SPECIFICATIONS", 42, py + 276, 15, GOLD)
        draw_text("Strike 1 : Tap at 0ms (0.5ms Attack, k=9.0)", 42, py + 304, 12, RAYWHITE)
        draw_text("Strike 2 : Blow at 90ms (0.5ms Attack, k=3.2)", 42, py + 326, 12, RAYWHITE)
        draw_text("Modes    : Steel Sine Cluster 1180/1770/2950 Hz", 42, py + 348, 12, YELLOW)
        draw_text("Resonance: 95 Hz Anvil Body Low Resonance", 42, py + 370, 12, RAYWHITE)
        draw_text("Total    : 340 ms (14,994 samples @ 44.1 kHz)", 42, py + 392, 12, LIGHTGRAY)
        draw_text("Filter   : 2-Pole Biquad BPF (2 kHz) + 70 Hz HPF", 42, py + 414, 12, RAYWHITE)
        draw_text("Peak     : ~28,000 PCM (-1.4 dBFS Headroom)", 42, py + 436, 12, GREEN)

        draw_line(42, py + 464, 24 + pw - 42, py + 464, Color(55, 70, 110, 255))
        draw_text("C++ EQUIVALENT ARCHITECTURE", 42, py + 478, 13, SKYBLUE)
        draw_text("Wave w = LoadWaveFromMemory(...);", 42, py + 504, 11, LIGHTGRAY)
        draw_text("Sound s = LoadSoundFromWave(w);", 42, py + 524, 11, LIGHTGRAY)
        draw_text("UnloadWave(w); // Audio device retained", 42, py + 544, 11, LIGHTGRAY)
        draw_text("PlaySound(s);  // 1-to-1 Raylib parity", 42, py + 564, 11, LIGHTGRAY)

        # Right Stage: Visualizer Panels
        sx, sy, sw, sh = 420, 90, 836, 590
        draw_rectangle(sx, sy, sw, sh, Color(18, 24, 38, 255))
        draw_rectangle_lines(sx, sy, sw, sh, Color(55, 70, 110, 255))
        draw_text("INTERACTIVE BLACKSMITH ANVIL & FORGING WORKBENCH", sx + 20, sy + 16, 15, GOLD)

        # Blacksmith Anvil Drawing
        acx, atop = sx + 200, sy + 200
        draw_rectangle(acx - 90, atop + 80, 180, 60, Color(70, 42, 22, 255))  # Timber stump
        draw_rectangle(acx - 90, atop + 102, 180, 8, Color(55, 60, 70, 255))  # Iron band
        draw_rectangle(acx - 75, atop + 56, 150, 24, Color(80, 85, 95, 255))   # Anvil base
        draw_rectangle(acx - 45, atop + 18, 90, 38, Color(105, 110, 120, 255)) # Anvil waist
        draw_triangle(Vector2(float(acx - 130), float(atop + 12)), Vector2(float(acx - 75), float(atop + 26)), Vector2(float(acx - 75), float(atop)), Color(150, 155, 165, 255)) # Horn
        draw_rectangle(acx - 75, atop, 160, 18, Color(175, 180, 190, 255))     # Top deck face
        draw_rectangle_lines(acx - 75, atop, 160, 18, Color(225, 230, 240, 255))
        draw_rectangle(acx + 70, atop + 4, 25, 12, Color(125, 130, 140, 255))
        draw_rectangle(acx + 78, atop + 6, 6, 6, Color(20, 24, 32, 255))       # Hardy hole

        # Heated workpiece
        bar_x, bar_y = acx - 10, atop - 6
        glow_g = int(120 + 135 * self.anvil_glow)
        glow_b = int(20 + 200 * self.anvil_glow)
        draw_rectangle(bar_x, bar_y, 40, 8, Color(255, max(0, min(255, glow_g)), max(0, min(255, glow_b)), 255))
        if self.anvil_glow > 0.05:
            draw_circle(bar_x + 20, bar_y + 4, 28.0 + 20.0 * self.anvil_glow, Color(255, 140, 30, int(120 * self.anvil_glow)))

        # Animated Hammer
        hx, hy, hrot = float(bar_x + 20), float(bar_y), -0.45
        if not self.is_animating:
            hx, hy = hx + 35.0, hy - 45.0
        else:
            t = self.anim_timer
            if t < 0.02:
                hy, hrot = hy - 8.0, 0.0
            elif t < 0.055:
                prog = (t - 0.02) / 0.035
                hx, hy, hrot = hx + 25.0 * prog, hy - 8.0 - 45.0 * prog, -0.60 * prog
            elif t < STRIKE2_OFFSET:
                prog = (t - 0.055) / (STRIKE2_OFFSET - 0.055)
                hx, hy, hrot = hx + 25.0 * (1.0 - prog), hy - 53.0 + 45.0 * prog, -0.60 * (1.0 - prog)
            elif t < STRIKE2_OFFSET + 0.04:
                hx, hy, hrot = hx + float(int(t * 1000) % 3 - 1), hy - 8.0, 0.0
            else:
                prog = min(1.0, (t - (STRIKE2_OFFSET + 0.04)) / 0.25)
                hx, hy, hrot = hx + 35.0 * prog, hy - 8.0 - 37.0 * prog, -0.45 * prog

        handle_end = Vector2(hx + math.cos(hrot - 0.5) * 70.0, hy + math.sin(hrot - 0.5) * 70.0)
        draw_line_ex(Vector2(hx, hy), handle_end, 5.0, Color(160, 110, 60, 255))
        draw_rectangle_pro(Rectangle(hx, hy, 36.0, 16.0), Vector2(18.0, 8.0), math.degrees(hrot), Color(190, 195, 205, 255))

        for sp in self.sparks:
            sp.draw()

        draw_text("Interactive Blacksmith Anvil", acx - 85, atop + 148, 13, RAYWHITE)
        draw_text("Click / Space to strike", acx - 65, atop + 168, 11, LIGHTGRAY)

        # Impact Energy Meter
        mx, my, mw, mh = sx + 430, sy + 110, 380, 32
        draw_rectangle(mx, my, mw, mh, Color(12, 16, 26, 255))
        draw_rectangle_lines(mx, my, mw, mh, Color(55, 70, 110, 255))
        if self.anvil_glow > 0:
            draw_rectangle(mx + 2, my + 2, int(self.anvil_glow * (mw - 4)), mh - 4, Color(int(255 * self.anvil_glow), int(180 * self.anvil_glow), 20, 240))
        draw_text("Instantaneous Forging Impact Energy", mx, my - 20, 12, SKYBLUE)
        draw_text(f"{int(self.anvil_glow * 100)}%", mx + mw - 40, my + 8, 12, RAYWHITE)

        # Trajectory Info Box
        tbx = sy + 175
        draw_rectangle(mx, tbx, mw, 115, Color(14, 20, 32, 255))
        draw_rectangle_lines(mx, tbx, mw, 115, Color(55, 70, 110, 255))
        draw_text("DOUBLE BLACKSMITH STRIKE TRAJECTORY", mx + 14, tbx + 12, 12, GOLD)
        t1_active = self.is_animating and (self.anim_timer < STRIKE2_OFFSET)
        t2_active = self.is_animating and (self.anim_timer >= STRIKE2_OFFSET)
        c1 = YELLOW if t1_active else Color(100, 120, 160, 255)
        c2 = GOLD if t2_active else Color(100, 120, 160, 255)
        draw_rectangle(mx + 14, tbx + 38, 160, 62, Color(24, 32, 50, 255))
        draw_rectangle_lines(mx + 14, tbx + 38, 160, 62, c1)
        draw_text("Strike 1: Tap (0ms)", mx + 22, tbx + 46, 12, c1)
        draw_text("0.5ms Attack, k=9.0", mx + 22, tbx + 64, 11, LIGHTGRAY)
        draw_text("Steel Modes (0.45x)", mx + 22, tbx + 80, 10, SKYBLUE)
        draw_text("->", mx + 182, tbx + 60, 15, RAYWHITE)
        draw_rectangle(mx + 205, tbx + 38, 160, 62, Color(24, 32, 50, 255))
        draw_rectangle_lines(mx + 205, tbx + 38, 160, 62, c2)
        draw_text("Strike 2: Blow (90ms)", mx + 213, tbx + 46, 12, c2)
        draw_text("0.5ms Attack, k=3.2", mx + 213, tbx + 64, 11, LIGHTGRAY)
        draw_text("+95Hz Anvil Body Low", mx + 213, tbx + 80, 10, GOLD)

        # Oscilloscope Waveform Panel
        scx, scy, scw, sch = sx + 20, sy + 320, sw - 40, 240
        draw_rectangle(scx, scy, scw, sch, Color(12, 16, 26, 255))
        draw_rectangle_lines(scx, scy, scw, sch, Color(55, 70, 110, 255))
        draw_text("IN-MEMORY 16-BIT PCM WAVEFORM & ENVELOPE INSPECTOR", scx + 16, scy + 12, 13, SKYBLUE)
        mid_y = scy + (sch // 2)
        draw_line(scx + 10, mid_y, scx + scw - 10, mid_y, Color(35, 45, 65, 255))

        split_x = scx + int((STRIKE2_OFFSET / TOTAL_DURATION) * scw)
        draw_line(split_x, scy + 35, split_x, scy + sch - 10, Color(70, 90, 130, 255))
        draw_text("Strike 1 (90ms, k=9.0)", scx + 20, scy + sch - 22, 11, SKYBLUE)
        draw_text("Strike 2 Blow + 95Hz Body (250ms, k=3.2)", split_x + 16, scy + sch - 22, 11, GOLD)

        # Draw waveform curve
        steps = len(self.scope_points) - 1
        prev_px, prev_py = scx + 10, mid_y
        for s in range(steps + 1):
            t_norm = float(s) / float(steps)
            px = scx + 10 + int(t_norm * (scw - 20))
            line_color = Color(100, 200, 255, 220) if t_norm < (STRIKE2_OFFSET / TOTAL_DURATION) else Color(255, 215, 0, 230)
            py_scope = int(mid_y - (self.scope_points[s] * (sch * 0.40) * (0.30 + 0.70 * self.anvil_glow)))
            if s > 0:
                draw_line(prev_px, prev_py, px, py_scope, line_color)
            prev_px, prev_py = px, py_scope

        # Animated playhead cursor
        if self.is_animating and self.anim_timer <= TOTAL_DURATION:
            cx = scx + 10 + int((self.anim_timer / TOTAL_DURATION) * (scw - 20))
            draw_line(cx, scy + 35, cx, scy + sch - 10, RAYWHITE)
            draw_circle(cx, mid_y, 4.0, RAYWHITE)

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


if __name__ == "__main__":
    is_smoke = "--smoke-test" in sys.argv
    SFXAuditionApp().run(smoke_test=is_smoke)
