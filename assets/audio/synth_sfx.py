# -*- coding: utf-8 -*-
"""
Procedural Sound Effect (SFX) Synthesizer for Raylib Python
-----------------------------------------------------------
Generates retro and arcade sound effects purely from mathematical waveforms
(sine, square, triangle, white noise) directly in memory, loading them into
Raylib Sound objects without requiring external audio files.

Included Effects:
  - Laser / Blaster: Downward frequency sweep
  - Explosion: Low-pass filtered noise with rumble decay
  - Hit / Impact: Punchy pitch drop with heavy punch
  - Jump: Upward frequency slide
  - Coin / Pickup: Bright 2-tone melodic chime
  - Powerup: Rising arpeggio fanfare
  - Hurt: Low grunted pitch dive with distortion
  - Click / UI: Short subtle blip

Includes SoundLibrary for easy one-line caching and playback.
"""

import io
import math
import random
import struct
import wave
from pyray import (
    load_wave_from_memory, load_sound_from_wave, unload_wave,
    unload_sound, play_sound, set_sound_volume, Sound
)

SAMPLE_RATE = 22050


def _build_wav_sound(pcm_floats, sample_rate: int = SAMPLE_RATE) -> Sound:
    """
    Takes a list of normalized float audio samples (-1.0 to 1.0),
    packs them into a 16-bit Mono PCM WAV buffer, and loads it into a Raylib Sound.
    """
    raw_frames = bytearray()
    for val in pcm_floats:
        # Clamp to avoid distortion
        clamped = max(-1.0, min(1.0, val))
        raw_frames += struct.pack('<h', int(clamped * 32767))
        
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(raw_frames)
        
    data = buf.getvalue()
    wave_obj = load_wave_from_memory(b'.wav', data, len(data))
    sound_obj = load_sound_from_wave(wave_obj)
    unload_wave(wave_obj)
    return sound_obj


# ==============================================================================
# SFX GENERATORS
# ==============================================================================

def create_laser_sfx(duration: float = 0.12, start_freq: float = 900.0, end_freq: float = 180.0) -> Sound:
    """Creates a retro laser shoot sound with a fast downward pitch slide."""
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    phase = 0.0
    for i in range(total_samples):
        t = i / total_samples
        freq = start_freq + (end_freq - start_freq) * (t * t)
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        envelope = 1.0 - t
        # Mix sine wave with a little square wave for retro grit
        sine = math.sin(phase)
        square = 1.0 if sine > 0 else -1.0
        val = (0.7 * sine + 0.3 * square) * envelope * 0.45
        samples.append(val)
    return _build_wav_sound(samples)


def create_explosion_sfx(duration: float = 0.45) -> Sound:
    """Creates an explosion sound using decaying white noise and low rumble."""
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    noise_val = 0.0
    phase_rumble = 0.0
    for i in range(total_samples):
        t = i / total_samples
        envelope = math.exp(-6.0 * t)
        
        # Simple one-pole low-pass filter on random noise
        raw_noise = random.random() * 2.0 - 1.0
        noise_val += 0.15 * (raw_noise - noise_val)
        
        # Low rumble tone (60 Hz decaying)
        phase_rumble += 2.0 * math.pi * (65.0 * (1.0 - t * 0.5)) / SAMPLE_RATE
        rumble = math.sin(phase_rumble)
        
        val = (0.75 * noise_val + 0.25 * rumble) * envelope * 0.65
        samples.append(val)
    return _build_wav_sound(samples)


def create_hit_sfx(duration: float = 0.10) -> Sound:
    """Creates a punchy impact/thud sound for collisions or melee attacks."""
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    phase = 0.0
    for i in range(total_samples):
        t = i / total_samples
        freq = 280.0 * math.exp(-18.0 * t) + 40.0
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        envelope = math.exp(-12.0 * t)
        val = math.sin(phase) * envelope * 0.55
        samples.append(val)
    return _build_wav_sound(samples)


def create_jump_sfx(duration: float = 0.14) -> Sound:
    """Creates a classic 8-bit platformer jump sound (upward sweep)."""
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    phase = 0.0
    for i in range(total_samples):
        t = i / total_samples
        freq = 150.0 + 450.0 * (t * t)
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        envelope = 1.0 - t * 0.6
        sq = 1.0 if math.sin(phase) > 0 else -1.0
        val = sq * envelope * 0.35
        samples.append(val)
    return _build_wav_sound(samples)


def create_coin_sfx(duration: float = 0.16) -> Sound:
    """Creates a 2-tone melodic pickup chime (B5 to E6)."""
    total_samples = int(SAMPLE_RATE * duration)
    half_samples = total_samples // 2
    samples = []
    phase = 0.0
    for i in range(total_samples):
        freq = 987.77 if i < half_samples else 1318.51 # B5 then E6
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        t_local = (i % half_samples) / half_samples
        envelope = 1.0 - t_local * 0.7
        val = math.sin(phase) * envelope * 0.40
        samples.append(val)
    return _build_wav_sound(samples)


def create_powerup_sfx(duration: float = 0.32) -> Sound:
    """Creates a rising 4-note victory / powerup fanfare."""
    notes = [330.0, 392.0, 493.88, 659.25] # E4, G4, B4, E5
    step_samples = int(SAMPLE_RATE * (duration / len(notes)))
    samples = []
    phase = 0.0
    for note in notes:
        for i in range(step_samples):
            phase += 2.0 * math.pi * note / SAMPLE_RATE
            t = i / step_samples
            env = math.exp(-4.0 * t)
            sq = 1.0 if math.sin(phase) > 0 else -1.0
            sine = math.sin(phase)
            samples.append((0.6 * sq + 0.4 * sine) * env * 0.35)
    return _build_wav_sound(samples)


def create_hurt_sfx(duration: float = 0.15) -> Sound:
    """Creates an aggressive hurt groan sound."""
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    phase = 0.0
    for i in range(total_samples):
        t = i / total_samples
        freq = 180.0 - 110.0 * t
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        env = math.exp(-7.0 * t)
        noise = (random.random() * 2.0 - 1.0) * 0.3
        sine = math.sin(phase)
        samples.append((sine + noise) * env * 0.45)
    return _build_wav_sound(samples)


def create_click_sfx(duration: float = 0.04) -> Sound:
    """Creates a short, clean UI button click blip."""
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    phase = 0.0
    for i in range(total_samples):
        t = i / total_samples
        phase += 2.0 * math.pi * 1200.0 / SAMPLE_RATE
        env = math.sin(math.pi * (1.0 - t))
        samples.append(math.sin(phase) * env * 0.30)
    return _build_wav_sound(samples)


# ==============================================================================
# SOUND LIBRARY (CACHE & MANAGEMENT)
# ==============================================================================

class SoundLibrary:
    """
    Manages a cached collection of synthesized sounds.
    Prevents re-synthesizing audio every frame. Call library.play('laser') anywhere.
    """
    def __init__(self):
        self.sounds = {}
        self.is_initialized = False

    def init_defaults(self):
        """Synthesizes and caches all default game sound effects."""
        self.sounds["laser"] = create_laser_sfx()
        self.sounds["explosion"] = create_explosion_sfx()
        self.sounds["hit"] = create_hit_sfx()
        self.sounds["jump"] = create_jump_sfx()
        self.sounds["coin"] = create_coin_sfx()
        self.sounds["powerup"] = create_powerup_sfx()
        self.sounds["hurt"] = create_hurt_sfx()
        self.sounds["click"] = create_click_sfx()
        self.is_initialized = True

    def play(self, name: str, volume: float = 1.0):
        """Plays a sound by name with optional volume scaling."""
        snd = self.sounds.get(name)
        if snd:
            set_sound_volume(snd, volume)
            play_sound(snd)

    def get(self, name: str) -> Sound:
        """Retrieves the Raylib Sound object directly."""
        return self.sounds.get(name)

    def unload_all(self):
        """Frees all cached sounds from memory."""
        for snd in self.sounds.values():
            unload_sound(snd)
        self.sounds.clear()
        self.is_initialized = False

