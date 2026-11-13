# -*- coding: utf-8 -*-
"""
Procedural Gem Sound Effect (SFX) Synthesizer
=============================================
Type             : Procedural Audio SFX (Sound)
Target File      : assets/audio/SFX/progression/gem.py
Catalog ID       : sfx_prog_gem
Waveforms Used   : Triple crystal cascading sine burst (C6 -> G6 -> C7) + 5% 5th/7th odd harmonics + 900 Hz HPF
Category         : Progression & Economy (sfx_prog_gem)

Problem Solved:
  Eliminates external audio file dependencies (.wav/.mp3) by synthesizing an iconic,
  high-value luxury pickup chime directly in memory from pure mathematical waveforms
  into an in-memory 16-bit PCM buffer, loading directly into a Raylib Sound struct.

Waveform Theory & Mathematical Rationale:
  - Sequence & Musical Pitch (Triple Crystal Sparkle):
      Note 1: C6 (1046.50 Hz) for 28 ms (0.000s to 0.028s).
      Note 2: G6 (1567.98 Hz) for 28 ms (0.028s to 0.056s).
      Note 3: C7 (2093.00 Hz) for 79 ms (0.056s to 0.135s).
      Total Duration: 135 ms (0.135 s, 5953 samples @ 44.1 kHz).
  - Musical Intervals:
      Transition 1 (C6 -> G6): Ascending perfect fifth (frequency ratio 3:2, 1.50).
      Transition 2 (G6 -> C7): Ascending perfect fourth (frequency ratio 4:3, 1.333).
      Span (C6 -> C7): Complete octave double (ratio 2:1, 2.0).
      In psychoacoustics, rapid ascending root -> fifth -> octave arpeggiation communicates
      unmistakable wealth, precious gem acquisition, diamond loot collection, and currency jackpots.
  - Harmonic Layering (5% 5th & 7th High Odd Harmonics):
      Carrier blends the fundamental with subtle upper odd harmonics:
        carrier(t) = sin(phi) + 0.05 * sin(5 * phi) + 0.05 * sin(7 * phi)
      For C7 (2093 Hz), the 5th harmonic is 10,465 Hz and the 7th harmonic is 14,651 Hz.
      These ultra-high acoustic frequencies replicate the sparkling, crystalline facet
      reflections of a cut diamond without harsh metallic clang.
  - Amplitude Envelope Anatomy:
      - Notes 1 & 2 (C6, G6): Crisp 0.5 ms linear attack ramp to eliminate boundary clicks,
        maintaining energetic presence with subtle articulation decay.
      - Note 3 (C7): Crisp 0.5 ms attack articulation transitioning into a shimmering
        exponential decay tail extending 80 ms past the note onset:
          env_tail(t) = exp(-4.8 * progress) * (1.0 + 0.05 * sin(2 * pi * 32.0 * t_local))
  - High-Pass Filter (HPF):
      A 1st-order single-pole IIR filter with cutoff fc = 900 Hz:
        alpha = RC / (RC + dt), where RC = 1 / (2 * pi * fc) and dt = 1 / sample_rate.
        y[i] = alpha * (y[i - 1] + x[i] - x[i - 1])
      Eliminates all sub-bass rumble, DC offset, and switching clicks below 900 Hz while
      passing the crisp 1046 Hz, 1568 Hz, and 2093 Hz crystal notes uncolored.
  - Amplitude Scaling & Headroom:
      Peak amplitude normalized and scaled to ~25,000 (signed 16-bit PCM, [-32767, 32767]),
      providing ~-2.5 dBFS of safe headroom to prevent digital clipping when gems are
      collected in rapid successive cascades.

Direct C++ Raylib Translation (raylib.h):
  struct GemSFX {
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

# Note 1: C6 (Root crystal note)
FREQ_C6: float = 1046.50           # Hz (C6)
DURATION_NOTE1: float = 0.028      # 28 ms burst

# Note 2: G6 (Ascending perfect fifth)
FREQ_G6: float = 1567.98           # Hz (G6)
DURATION_NOTE2: float = 0.028      # 28 ms burst

# Note 3: C7 (Climactic octave sparkle)
FREQ_C7: float = 2093.00           # Hz (C7)
DURATION_NOTE3_TAIL: float = 0.079 # ~80 ms ringing release tail

# Total timing
TOTAL_DURATION: float = DURATION_NOTE1 + DURATION_NOTE2 + DURATION_NOTE3_TAIL  # 135 ms (0.135 s)
ATTACK_DURATION: float = 0.0005    # 0.5 ms crisp linear attack
DECAY_RATE_K: float = 4.8          # Exponential decay factor k=4.8
HPF_CUTOFF: float = 900.0          # 900 Hz High-Pass Filter cutoff
TARGET_PEAK_AMPLITUDE: float = 25000.0  # Signed 16-bit PCM target (~-2.5 dBFS)


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
def create_gem_sfx(
    volume: float = 1.0,
    duration: float = TOTAL_DURATION,
    freq_n1: float = FREQ_C6,
    freq_n2: float = FREQ_G6,
    freq_n3: float = FREQ_C7
) -> Sound:
    """
    Synthesizes a luxury triple crystal diamond sparkle pickup chime into a Raylib Sound struct.

    Parameters:
      volume   : Overall master amplitude scale factor (0.0 to 1.0).
      duration : Total duration of the sound effect in seconds (default 135 ms).
      freq_n1  : Initial crystal burst frequency in Hz (default 1046.50 Hz, C6).
      freq_n2  : Intermediate crystal burst frequency in Hz (default 1567.98 Hz, G6).
      freq_n3  : Climactic crystal sparkle frequency in Hz (default 2093.00 Hz, C7).

    Returns:
      A ready-to-play Sound handle resident in audio hardware memory.
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples_note1 = int(SAMPLE_RATE * DURATION_NOTE1)
    samples_note2 = int(SAMPLE_RATE * DURATION_NOTE2)

    raw_samples = []
    phase = 0.0

    # 1. Synthesize 3 cascading bursts with 5% 5th and 7th high odd harmonics
    for i in range(total_samples):
        t = float(i) / float(SAMPLE_RATE)

        if t < DURATION_NOTE1:
            # Burst 1: C6 (1046.50 Hz)
            t_local = t
            current_freq = freq_n1
            phase += PI2 * current_freq / float(SAMPLE_RATE)

            # Envelope: 0.5 ms crisp linear attack + 5% articulation decay
            if t_local < ATTACK_DURATION:
                attack = t_local / ATTACK_DURATION
            else:
                attack = 1.0
            decay = 1.0 - 0.05 * (t_local / DURATION_NOTE1)
            envelope = attack * decay

        elif t < (DURATION_NOTE1 + DURATION_NOTE2):
            # Burst 2: G6 (1567.98 Hz)
            t_local = t - DURATION_NOTE1
            current_freq = freq_n2
            phase += PI2 * current_freq / float(SAMPLE_RATE)

            # Envelope: 0.5 ms crisp linear attack + 5% articulation decay
            if t_local < ATTACK_DURATION:
                attack = t_local / ATTACK_DURATION
            else:
                attack = 1.0
            decay = 1.0 - 0.05 * (t_local / DURATION_NOTE2)
            envelope = attack * decay

        else:
            # Burst 3: C7 (2093.00 Hz) with shimmering exponential decay tail
            t_local = t - (DURATION_NOTE1 + DURATION_NOTE2)
            current_freq = freq_n3
            phase += PI2 * current_freq / float(SAMPLE_RATE)

            # Envelope: 0.5 ms crisp attack + exponential release tail (k=4.8)
            if t_local < ATTACK_DURATION:
                attack = t_local / ATTACK_DURATION
            else:
                attack = 1.0

            tail_span = max(0.001, duration - (DURATION_NOTE1 + DURATION_NOTE2))
            decay_prog = max(0.0, (t_local - ATTACK_DURATION) / max(0.001, tail_span - ATTACK_DURATION))
            exp_decay = math.exp(-DECAY_RATE_K * decay_prog)

            # Crystalline shimmer modulation (32 Hz micro-tremolo on decay)
            shimmer = 1.0 + 0.05 * math.sin(PI2 * 32.0 * t_local)
            envelope = attack * exp_decay * shimmer

        # Anti-click safety fade on the final 2 ms of buffer
        if (duration - t) < 0.002:
            fade_out = max(0.0, (duration - t) / 0.002)
            envelope *= fade_out

        # Carrier oscillator: Pure fundamental sine layered with 5% 5th and 7th harmonics
        # Replicates crystalline diamond acoustic facets (10.4 kHz and 14.6 kHz sparkle)
        sine_val = math.sin(phase)
        h5_val = math.sin(5.0 * phase)
        h7_val = math.sin(7.0 * phase)
        carrier = sine_val + 0.05 * h5_val + 0.05 * h7_val

        raw_val = carrier * envelope
        raw_samples.append(raw_val)

    # 2. Apply 1st-Order Single-Pole High-Pass Filter (fc = 900 Hz)
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
create_sfx = create_gem_sfx


def play_sfx(sound: Sound, volume: float = 1.0, pitch: float = 1.0) -> None:
    """Plays the gem sound effect with explicit volume and pitch scaling."""
    set_sound_volume(sound, max(0.0, min(1.0, volume)))
    set_sound_pitch(sound, max(0.5, min(2.0, pitch)))
    play_sound(sound)


def stop_sfx(sound: Sound) -> None:
    """Stops playback of the gem sound effect immediately."""
    stop_sound(sound)


def unload_sfx(sound: Sound) -> None:
    """Frees the Sound resource from audio hardware memory."""
    unload_sound(sound)


# ==============================================================================
# PART 6: STANDALONE AUDITION WORKBENCH & AUTOMATED SMOKE TEST
# ==============================================================================
class GemSparkle:
    """Visual crystal particle emitted when the gem SFX triggers in the workbench."""
    def __init__(self, x: float, y: float, vx: float, vy: float, life: float, color: Any):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = color
        self.rotation = 0.0
        self.rot_speed = (hash(str(vx)) % 10 - 5) * 1.5

    def update(self, dt: float) -> bool:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rotation += self.rot_speed * dt
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
        sz = max(1.5, 6.0 * progress)

        # 4-pointed diamond sparkle geometry
        ix = int(self.x)
        iy = int(self.y)
        draw_circle(ix, iy, max(1.0, sz * 0.4), c)
        draw_line(int(ix - sz * 2.5), iy, int(ix + sz * 2.5), iy, c)
        draw_line(ix, int(iy - sz * 2.5), ix, int(iy + sz * 2.5), c)
        draw_line(int(ix - sz * 1.2), int(iy - sz * 1.2), int(ix + sz * 1.2), int(iy + sz * 1.2), c)
        draw_line(int(ix - sz * 1.2), int(iy + sz * 1.2), int(ix + sz * 1.2), int(iy - sz * 1.2), c)


class SFXAuditionApp:
    """
    Interactive sound previewer workbench allowing developers and students
    to audition the gem sound effect with live parameter controls, faceted
    diamond visualizer, oscilloscope, telemetry, and automated smoke test capability.
    """
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        init_window(self.screen_width, self.screen_height, "SFX Workbench - Gem (assets/audio/SFX/progression/gem.py)")
        set_target_fps(60)
        init_audio_device()

        self.sound = create_gem_sfx()
        self.trigger_pulse = 0.0
        self.volume = 0.90
        self.pitch = 1.0
        self.trigger_count = 0
        self.gem_rotation = 0.0
        self.gem_glint_timer = 0.0
        self.sparkles = []

    def trigger(self):
        """Triggers sound playback with current pitch/volume and animates visualizer."""
        play_sfx(self.sound, self.volume, self.pitch)
        self.trigger_pulse = 1.0
        self.trigger_count += 1

        # Spawn sparkling crystal celebration particles around the diamond
        gem_cx = 600.0
        gem_cy = 280.0
        sparkle_colors = [
            Color(140, 240, 255, 255),  # Cyan diamond
            Color(255, 255, 255, 255),  # Pure white glint
            Color(180, 220, 255, 255),  # Sky crystal
            Color(220, 245, 255, 255),  # Ice diamond
            Color(100, 200, 255, 255)   # Deep cyan
        ]

        for k in range(24):
            angle = (float(k) / 24.0) * PI2
            speed = 90.0 + (float(k % 6) * 35.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - 20.0  # Slight upward buoyant bias
            life = 0.40 + (float(k % 5) * 0.08)
            col = sparkle_colors[k % len(sparkle_colors)]
            self.sparkles.append(GemSparkle(gem_cx, gem_cy, vx, vy, life, col))

    def update(self):
        dt = min(get_frame_time(), 0.05)

        # Decay pulse & advance gem glint
        if self.trigger_pulse > 0.0:
            self.trigger_pulse = max(0.0, self.trigger_pulse - dt * 3.5)

        self.gem_glint_timer += dt * (2.0 + self.trigger_pulse * 6.0)
        if self.gem_glint_timer > PI2:
            self.gem_glint_timer -= PI2

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

    def draw_diamond_gem(self, cx: float, cy: float, scale: float):
        """Draws an exquisite procedural faceted brilliant diamond gem in 2D."""
        # Diamond proportions
        table_hw = 42.0 * scale
        girdle_hw = 72.0 * scale
        crown_h = 32.0 * scale
        pavilion_h = 75.0 * scale

        y_top = cy - crown_h
        y_girdle = cy
        y_culet = cy + pavilion_h

        # Dynamic facet illumination modulation
        glint_phase = math.sin(self.gem_glint_timer)
        pulse_boost = self.trigger_pulse * 40.0

        # Facet colors (Jewel cyan, diamond white, sapphire depth)
        c_table = Color(int(200 + pulse_boost), int(240 + pulse_boost * 0.3), 255, 255)
        c_crown_l = Color(130, 210, 255, 255)
        c_crown_c1 = Color(170, 230, 255, 255)
        c_crown_c2 = Color(150, 220, 255, 255)
        c_crown_r = Color(110, 195, 250, 255)

        c_pav_l = Color(50, 130, 220, 255)
        c_pav_c1 = Color(85, 175, 245, 255)
        c_pav_c2 = Color(70, 155, 235, 255)
        c_pav_r = Color(35, 105, 195, 255)

        outline_col = Color(220, 245, 255, 255)

        # Draw outer glowing halo on trigger
        if self.trigger_pulse > 0.05:
            aura_radius = (girdle_hw + 30.0) * (1.0 + self.trigger_pulse * 0.25)
            aura_alpha = int(140 * self.trigger_pulse)
            draw_circle(int(cx), int(cy + 15.0 * scale), aura_radius, Color(100, 220, 255, aura_alpha))
            draw_circle(int(cx), int(cy + 15.0 * scale), aura_radius * 0.65, Color(220, 250, 255, aura_alpha))

        # Crown Points
        p_table_l = Vector2(cx - table_hw, y_top)
        p_table_r = Vector2(cx + table_hw, y_top)
        p_girdle_l = Vector2(cx - girdle_hw, y_girdle)
        p_girdle_r = Vector2(cx + girdle_hw, y_girdle)
        p_culet = Vector2(cx, y_culet)

        # Intermediate facet points for rich brilliance
        p_table_cl = Vector2(cx - table_hw * 0.35, y_top)
        p_table_cr = Vector2(cx + table_hw * 0.35, y_top)
        p_girdle_cl = Vector2(cx - girdle_hw * 0.40, y_girdle)
        p_girdle_cr = Vector2(cx + girdle_hw * 0.40, y_girdle)

        # 1. Crown Facets
        # Left wing
        draw_triangle(p_table_l, p_girdle_l, p_girdle_cl, c_crown_l)
        # Center-left bezel
        draw_triangle(p_table_l, p_girdle_cl, p_table_cl, c_crown_c1)
        # Center facet
        draw_triangle(p_table_cl, p_girdle_cl, p_girdle_cr, c_table)
        draw_triangle(p_table_cl, p_girdle_cr, p_table_cr, c_table)
        # Center-right bezel
        draw_triangle(p_table_cr, p_girdle_cr, p_table_r, c_crown_c2)
        # Right wing
        draw_triangle(p_table_r, p_girdle_cr, p_girdle_r, c_crown_r)

        # 2. Pavilion Facets (Converging to bottom culet point)
        # Left pavilion facet
        draw_triangle(p_girdle_l, p_culet, p_girdle_cl, c_pav_l)
        # Center-left pavilion facet
        draw_triangle(p_girdle_cl, p_culet, Vector2(cx, y_girdle), c_pav_c1)
        # Center-right pavilion facet
        draw_triangle(Vector2(cx, y_girdle), p_culet, p_girdle_cr, c_pav_c2)
        # Right pavilion facet
        draw_triangle(p_girdle_cr, p_culet, p_girdle_r, c_pav_r)

        # 3. Facet Outline Wireframe & Glint Streaks
        draw_line_ex(p_table_l, p_table_r, 2.0, outline_col)
        draw_line_ex(p_table_l, p_girdle_l, 2.0, outline_col)
        draw_line_ex(p_table_r, p_girdle_r, 2.0, outline_col)
        draw_line_ex(p_girdle_l, p_girdle_r, 2.0, outline_col)
        draw_line_ex(p_girdle_l, p_culet, 2.5, outline_col)
        draw_line_ex(p_girdle_r, p_culet, 2.5, outline_col)

        # Interior facet lines
        faint_line = Color(200, 240, 255, 180)
        draw_line(int(p_girdle_cl.x), int(p_girdle_cl.y), int(p_culet.x), int(p_culet.y), faint_line)
        draw_line(int(p_girdle_cr.x), int(p_girdle_cr.y), int(p_culet.x), int(p_culet.y), faint_line)
        draw_line(int(cx), int(y_girdle), int(p_culet.x), int(p_culet.y), faint_line)
        draw_line(int(p_table_cl.x), int(p_table_cl.y), int(p_girdle_cl.x), int(p_girdle_cl.y), faint_line)
        draw_line(int(p_table_cr.x), int(p_table_cr.y), int(p_girdle_cr.x), int(p_girdle_cr.y), faint_line)

        # 4. Traveling Light Glint on Table Facet
        glint_x = cx + glint_phase * (table_hw * 0.70)
        glint_alpha = int(180 + 75 * abs(glint_phase))
        draw_circle(int(glint_x), int(y_top + 4.0), 3.5, Color(255, 255, 255, glint_alpha))
        draw_line(int(glint_x - 10.0), int(y_top + 4.0), int(glint_x + 10.0), int(y_top + 4.0), Color(255, 255, 255, glint_alpha))
        draw_line(int(glint_x), int(y_top - 6.0), int(glint_x), int(y_top + 14.0), Color(255, 255, 255, glint_alpha))

    def draw(self):
        begin_drawing()
        clear_background(Color(12, 16, 26, 255))

        # Header (keeps top-bar region x=450..980, y=14..48 completely clear)
        draw_text("PROCEDURAL SFX AUDITION WORKBENCH", 24, 20, 20, RAYWHITE)
        draw_text("Asset: assets/audio/SFX/progression/gem.py | Waveform: Triple Crystal Sparkle (C6 -> G6 -> C7)", 24, 50, 13, SKYBLUE)

        # Left Control Instructions & Telemetry Panel
        panel_y = 90
        panel_w = 380
        panel_h = 590
        draw_rectangle(24, panel_y, panel_w, panel_h, Color(20, 26, 42, 255))
        draw_rectangle_lines(24, panel_y, panel_w, panel_h, Color(45, 65, 105, 255))

        draw_text("CONTROLS & SHORTCUTS", 42, panel_y + 16, 15, SKYBLUE)
        draw_text("- [Space] / [Enter] / [Click] : Trigger Gem SFX", 42, panel_y + 44, 12, RAYWHITE)
        draw_text("- [Up] / [Down] Arrows        : Pitch (+/- 0.1x)", 42, panel_y + 68, 12, RAYWHITE)
        draw_text("- [Right] / [Left] Arrows     : Volume (+/- 0.05)", 42, panel_y + 92, 12, RAYWHITE)
        draw_text("- [R] Key / Gamepad Start     : Reset All Parameters", 42, panel_y + 116, 12, RAYWHITE)

        draw_line(42, panel_y + 144, 24 + panel_w - 42, panel_y + 144, Color(45, 65, 105, 255))

        draw_text("CURRENT TELEMETRY", 42, panel_y + 158, 15, Color(140, 220, 255, 255))
        draw_text(f"Total Triggers : {self.trigger_count}", 42, panel_y + 186, 13, LIGHTGRAY)
        draw_text(f"Active Pitch   : {self.pitch:.1f}x", 42, panel_y + 210, 13, GREEN)
        draw_text(f"Master Volume  : {int(self.volume * 100)}%", 42, panel_y + 234, 13, GREEN)

        draw_line(42, panel_y + 262, 24 + panel_w - 42, panel_y + 262, Color(45, 65, 105, 255))

        draw_text("SYNTHESIS SPECIFICATIONS", 42, panel_y + 276, 15, Color(160, 230, 255, 255))
        draw_text("Burst 1 : C6 (1046.50 Hz) for 28 ms", 42, panel_y + 304, 12, RAYWHITE)
        draw_text("Burst 2 : G6 (1567.98 Hz) for 28 ms", 42, panel_y + 326, 12, RAYWHITE)
        draw_text("Burst 3 : C7 (2093.00 Hz) for 79 ms tail", 42, panel_y + 348, 12, RAYWHITE)
        draw_text("Total   : 135 ms (5953 samples @ 44.1 kHz)", 42, panel_y + 370, 12, LIGHTGRAY)
        draw_text("Harmonics: 5% 5th (10.4 kHz) & 7th (14.6 kHz)", 42, panel_y + 392, 12, SKYBLUE)
        draw_text("Filter  : 1-Pole HPF (fc = 900 Hz)", 42, panel_y + 414, 12, RAYWHITE)
        draw_text("Envelope: 0.5ms Attack -> Shimmer Decay (k=4.8)", 42, panel_y + 436, 12, LIGHTGRAY)
        draw_text("Peak    : ~25,000 PCM (-2.5 dBFS Headroom)", 42, panel_y + 458, 12, GREEN)

        draw_line(42, panel_y + 484, 24 + panel_w - 42, panel_y + 484, Color(45, 65, 105, 255))
        draw_text("C++ EQUIVALENT ARCHITECTURE", 42, panel_y + 498, 13, SKYBLUE)
        draw_text("Wave w = LoadWaveFromMemory(...);", 42, panel_y + 524, 11, LIGHTGRAY)
        draw_text("Sound s = LoadSoundFromWave(w);", 42, panel_y + 544, 11, LIGHTGRAY)
        draw_text("UnloadWave(w); // Retains audio device RAM", 42, panel_y + 564, 11, LIGHTGRAY)

        # Right Stage: Visualizer Panels
        stage_x = 420
        stage_y = 90
        stage_w = 836
        stage_h = 590
        draw_rectangle(stage_x, stage_y, stage_w, stage_h, Color(16, 22, 34, 255))
        draw_rectangle_lines(stage_x, stage_y, stage_w, stage_h, Color(45, 65, 105, 255))

        draw_text("INTERACTIVE PRECIOUS GEM AUDITION STAGE", stage_x + 20, stage_y + 16, 15, Color(160, 230, 255, 255))

        # Draw Faceted Diamond Gem Primitive
        gem_cx = float(stage_x + 180)
        gem_cy = float(stage_y + 175)
        gem_scale = 1.0 + (self.trigger_pulse * 0.18)
        self.draw_diamond_gem(gem_cx, gem_cy, gem_scale)

        # Draw Sparkle particles
        for sp in self.sparkles:
            sp.draw()

        draw_text("Procedural Diamond Primitive", int(gem_cx) - 88, int(gem_cy) + 95, 13, RAYWHITE)
        draw_text("Click / Space to collect gem", int(gem_cx) - 82, int(gem_cy) + 115, 11, LIGHTGRAY)

        # Instantaneous Energy Peak Meter (Horizontal)
        meter_x = stage_x + 380
        meter_y = stage_y + 115
        meter_w = 420
        meter_h = 32
        draw_rectangle(meter_x, meter_y, meter_w, meter_h, Color(10, 14, 22, 255))
        draw_rectangle_lines(meter_x, meter_y, meter_w, meter_h, Color(45, 65, 105, 255))
        pulse_fill = int(self.trigger_pulse * (meter_w - 4))
        if pulse_fill > 0:
            meter_color = Color(int(100 + 155 * self.trigger_pulse), int(210 + 45 * self.trigger_pulse), 255, 230)
            draw_rectangle(meter_x + 2, meter_y + 2, pulse_fill, meter_h - 4, meter_color)
        draw_text("Instantaneous Energy Peak Meter", meter_x, meter_y - 20, 12, SKYBLUE)
        draw_text(f"{int(self.trigger_pulse * 100)}%", meter_x + meter_w - 40, meter_y + 8, 12, RAYWHITE)

        # Triple Frequency Trajectory Sequencer Cards
        seq_y = stage_y + 175
        seq_h = 105
        draw_rectangle(meter_x, seq_y, meter_w, seq_h, Color(12, 18, 28, 255))
        draw_rectangle_lines(meter_x, seq_y, meter_w, seq_h, Color(45, 65, 105, 255))
        draw_text("TRIPLE CRYSTAL FREQUENCY TRAJECTORY", meter_x + 14, seq_y + 10, 12, Color(160, 230, 255, 255))

        # Dynamic burst highlight indicators
        b1_active = self.trigger_pulse > 0.65
        b2_active = 0.35 < self.trigger_pulse <= 0.65
        b3_active = 0.0 < self.trigger_pulse <= 0.35

        c_b1 = Color(140, 230, 255, 255) if b1_active else Color(70, 95, 130, 255)
        c_b2 = Color(160, 240, 255, 255) if b2_active else Color(70, 95, 130, 255)
        c_b3 = Color(220, 255, 255, 255) if b3_active else Color(70, 95, 130, 255)

        card_w = 120
        # Card 1: C6
        draw_rectangle(meter_x + 12, seq_y + 36, card_w, 54, Color(20, 28, 44, 255))
        draw_rectangle_lines(meter_x + 12, seq_y + 36, card_w, 54, c_b1)
        draw_text("Burst 1: C6", meter_x + 20, seq_y + 44, 12, c_b1)
        draw_text("1046.5 Hz (28ms)", meter_x + 20, seq_y + 60, 10, LIGHTGRAY)
        draw_text("Root Chime", meter_x + 20, seq_y + 74, 9, SKYBLUE)

        draw_text("->", meter_x + 138, seq_y + 54, 14, RAYWHITE)

        # Card 2: G6
        draw_rectangle(meter_x + 152, seq_y + 36, card_w, 54, Color(20, 28, 44, 255))
        draw_rectangle_lines(meter_x + 152, seq_y + 36, card_w, 54, c_b2)
        draw_text("Burst 2: G6", meter_x + 160, seq_y + 44, 12, c_b2)
        draw_text("1568.0 Hz (28ms)", meter_x + 160, seq_y + 60, 10, LIGHTGRAY)
        draw_text("Fifth (+7 semi)", meter_x + 160, seq_y + 74, 9, SKYBLUE)

        draw_text("->", meter_x + 278, seq_y + 54, 14, RAYWHITE)

        # Card 3: C7
        draw_rectangle(meter_x + 292, seq_y + 36, card_w, 54, Color(20, 28, 44, 255))
        draw_rectangle_lines(meter_x + 292, seq_y + 36, card_w, 54, c_b3)
        draw_text("Burst 3: C7", meter_x + 300, seq_y + 44, 12, c_b3)
        draw_text("2093.0 Hz (79ms)", meter_x + 300, seq_y + 60, 10, LIGHTGRAY)
        draw_text("Octave Sparkle", meter_x + 300, seq_y + 74, 9, Color(200, 240, 255, 255))

        # Oscilloscope Waveform Panel (Lower Half)
        scope_x = stage_x + 20
        scope_y = stage_y + 310
        scope_w = stage_w - 40
        scope_h = 250
        draw_rectangle(scope_x, scope_y, scope_w, scope_h, Color(10, 14, 22, 255))
        draw_rectangle_lines(scope_x, scope_y, scope_w, scope_h, Color(45, 65, 105, 255))
        draw_text("IN-MEMORY 16-BIT PCM WAVEFORM & CRYSTAL HARMONICS INSPECTOR", scope_x + 16, scope_y + 12, 13, SKYBLUE)

        mid_y = scope_y + (scope_h // 2)
        draw_line(scope_x + 10, mid_y, scope_x + scope_w - 10, mid_y, Color(30, 40, 60, 255))

        # Vertical dividing lines for Burst 1 -> Burst 2 -> Burst 3
        # 28ms / 135ms = ~20.7%, 56ms / 135ms = ~41.5%
        split1_x = scope_x + int((28.0 / 135.0) * scope_w)
        split2_x = scope_x + int((56.0 / 135.0) * scope_w)

        draw_line(split1_x, scope_y + 35, split1_x, scope_y + scope_h - 10, Color(50, 75, 115, 255))
        draw_line(split2_x, scope_y + 35, split2_x, scope_y + scope_h - 10, Color(50, 75, 115, 255))

        draw_text("C6 (0..28ms)", scope_x + 24, scope_y + scope_h - 22, 11, Color(130, 210, 255, 255))
        draw_text("G6 (28..56ms)", split1_x + 15, scope_y + scope_h - 22, 11, Color(160, 230, 255, 255))
        draw_text("C7 Ring-Out Tail (56..135ms, k=4.8)", split2_x + 20, scope_y + scope_h - 22, 11, Color(220, 250, 255, 255))

        # Draw mathematical waveform curve
        steps = 220
        prev_px = scope_x + 10
        prev_py = mid_y
        for s in range(steps + 1):
            t_norm = float(s) / float(steps)
            px = scope_x + 10 + int(t_norm * (scope_w - 20))

            if t_norm < (28.0 / 135.0):
                # Burst 1: C6
                prog = t_norm / (28.0 / 135.0)
                env = min(1.0, prog * 10.0) * (1.0 - 0.05 * prog)
                freq_factor = 24.0 * self.pitch
                carrier = math.sin(t_norm * freq_factor * PI2) + 0.05 * math.sin(5.0 * t_norm * freq_factor * PI2)
                wave_val = carrier * env
                line_color = Color(120, 215, 255, 220)
            elif t_norm < (56.0 / 135.0):
                # Burst 2: G6
                prog = (t_norm - (28.0 / 135.0)) / (28.0 / 135.0)
                env = min(1.0, prog * 10.0) * (1.0 - 0.05 * prog)
                freq_factor = 36.0 * self.pitch
                carrier = math.sin(t_norm * freq_factor * PI2) + 0.05 * math.sin(5.0 * t_norm * freq_factor * PI2)
                wave_val = carrier * env
                line_color = Color(160, 235, 255, 230)
            else:
                # Burst 3: C7
                prog = (t_norm - (56.0 / 135.0)) / (79.0 / 135.0)
                env = math.exp(-4.8 * prog) * (1.0 + 0.05 * math.sin(PI2 * 6.0 * prog))
                freq_factor = 48.0 * self.pitch
                carrier = math.sin(t_norm * freq_factor * PI2) + 0.05 * math.sin(5.0 * t_norm * freq_factor * PI2) + 0.05 * math.sin(7.0 * t_norm * freq_factor * PI2)
                wave_val = carrier * env
                line_color = Color(240, 250, 255, 240)

            # Modulate amplitude with trigger pulse or display subtle resting trace
            active_scale = 0.25 + 0.75 * self.trigger_pulse
            py = int(mid_y - (wave_val * (scope_h * 0.38) * active_scale))

            if s > 0:
                draw_line(prev_px, prev_py, px, py, line_color)
            prev_px = px
            prev_py = py

        # Top-Bar Dropdowns and Gamepad Status HUD clearance (x = 450..980, y = 14..48)
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
