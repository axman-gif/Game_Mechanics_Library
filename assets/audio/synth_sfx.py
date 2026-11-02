# -*- coding: utf-8 -*-
"""
Procedural Sound Effect (SFX) Synthesizer for Raylib Python
-----------------------------------------------------------
Generates retro, arcade, and modern game sound effects purely from mathematical
waveforms (sine, square, triangle, sawtooth, white noise, FM modulation, and
resonant one-pole IIR filters) directly in memory, loading them into Raylib Sound
objects without requiring external audio files.

Included Effects (48 Procedural Sounds):
  Combat & Weapons (16):
    - Laser / Blaster : Downward frequency sweep (classic retro pew)
    - Heavy Laser     : Low resonant plasma cannon blast with sub-bass rumble
    - Explosion       : Low-pass filtered noise with rumble decay
    - Hit / Impact    : Punchy pitch drop with heavy punch
    - Parry / Deflect : High-pitched dissonant metallic ring with crystal decay
    - Shield Block    : Heavy blunt resonant barrier impact
    - Reload          : 3-stage mechanical slide, eject, and chamber snap
    - Empty / Dry Fire: Sharp hollow hammer click when out of ammo
    - Shotgun         : Wide-band scattergun blast with pump-action rack clack
    - Sniper          : Supersonic whip crack with metallic barrel ring & canyon echo
    - Charge Up       : Quadratic frequency riser with accelerating LFO pulse
    - Sword Slash     : Crisp aerodynamic blade cleave with steel edge whistle
    - Critical Hit    : Sub-bass armor slam layered with crystalline FM shatter chime
    - Ricochet        : Metallic bullet deflection ping with rapid Doppler warble
    - Flame           : Turbulent thermal-draft noise burst with crackling embers
    - Freeze          : Inharmonic FM ice crystallization chimes with frost crackle

  Movement & Kinematics (10):
    - Jump            : Classic upward frequency slide
    - Dash / Whoosh   : Aerodynamic rushing air sweep for dodges and swings
    - Footstep        : Subtle, low-impact floor tap with surface friction
    - Land            : Solid ground thump after falling or jumping
    - Double Jump     : Two-stage mid-air flutter kick with octave harmonic lift
    - Grapple         : Pneumatic launch pop, high-speed cable winch & magnetic latch
    - Thruster        : Deep rocket combustion rumble with rising turbine spool whine
    - Teleport        : Vacuum implosion swell into ring-modulated quantum phase burst
    - Slide           : Kinetic ground-slide / drift friction scrape with gravel hiss
    - Bounce          : Elastic springboard / bumper rebound with damped pitch wobble

  Progression, Rewards & Health (11):
    - Coin / Pickup   : Bright 2-tone melodic chime (B5 to E6)
    - Powerup         : Rising 4-tone victory arpeggio
    - Level Up        : Sparkling 5-note pentatonic fanfare
    - Heal / Restore  : Soothing rising shimmer with vibrato modulation
    - Hurt            : Low grunted pitch dive with distortion
    - Chest Open      : Mechanical iron lock unlatch followed by 4-note Lydian reveal
    - Craft / Forge   : Double blacksmith anvil hammer strike with warm temper glow
    - Debuff / Curse  : Sinister descending tritone steps with subharmonic saw grit
    - Gem / Crystal   : Ultra-bright high-octave 3-note diamond bell sparkle (C6-G6-C7)
    - Revive          : Celestial organ triad swell with ascending octave shimmer
    - Death / Defeat  : 4-step descending minor cascade into sub-bass power-down drop

  UI & Feedback (11):
    - Click           : Standard UI button blip
    - Select / Hover  : Ultra-soft, gentle cursor hover tick
    - Cancel / Back   : Soft descending 2-tone dismissal blip
    - Error / Buzz    : Low harsh dissonant buzzer for invalid actions
    - Alert / Alarm   : Piercing 2-tone exclamation chirp for stealth / target lock
    - Confirm         : Crisp 2-tone ascending perfect-fifth UI accept chime (E5->B5)
    - Pause           : Classic 4-note retro staccato pause/menu stinger
    - Typewriter      : Ultra-short 25ms mechanical keystroke / dialogue voice pop
    - Notification    : Pleasant dual-chime toast & quest objective bell (A5->D6)
    - Sonar Ping      : High-Q 1480 Hz radar/minimap ping with secondary echo return
    - Countdown       : Punchy 880 Hz arcade timer & race countdown beep

Includes SoundLibrary for easy one-line caching and playback.
"""

import sys
sys.dont_write_bytecode = True

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
    
    Novice / C++ Note:
      In C/C++, audio engines (like miniaudio, SDL_Audio, or Raylib's LoadSoundFromWave)
      expect a contiguous buffer of signed 16-bit integers (int16_t, range -32768 to 32767).
      Clamping values to [-1.0, 1.0] before multiplying by 32767 prevents integer overflow
      and harsh digital clipping distortion.
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
# SFX GENERATORS - COMBAT & WEAPONS (16)
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


def create_heavy_laser_sfx(duration: float = 0.25) -> Sound:
    """
    Creates a deep sci-fi plasma cannon / heavy blast sound.
    Sweeps from 520 Hz down to 60 Hz with square harmonic grit and sub-bass rumble.
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    phase = 0.0
    sub_phase = 0.0
    for i in range(total_samples):
        t = i / total_samples
        # Nonlinear power sweep gives prolonged punch at the top before diving
        freq = 520.0 * ((1.0 - t) ** 1.8) + 60.0
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        sub_phase += 2.0 * math.pi * 65.0 / SAMPLE_RATE
        envelope = math.exp(-4.5 * t)
        
        sine = math.sin(phase)
        square = 1.0 if sine > 0 else -1.0
        rumble = math.sin(sub_phase)
        val = (0.50 * sine + 0.30 * square + 0.20 * rumble) * envelope * 0.50
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
        
        # Simple one-pole low-pass filter on random noise: y[n] = y[n-1] + a * (x[n] - y[n-1])
        raw_noise = random.random() * 2.0 - 1.0
        noise_val += 0.15 * (raw_noise - noise_val)
        
        # Low rumble tone (65 Hz decaying)
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


def create_parry_sfx(duration: float = 0.32) -> Sound:
    """
    Creates a sharp metallic blade deflect / parry clang.
    Uses dissonant high-frequency harmonics (1760 Hz, 2640 Hz, 3520 Hz) with an initial
    friction noise transient and an extended exponential crystalline ringing tail.
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    phase_1 = 0.0
    phase_2 = 0.0
    phase_3 = 0.0
    for i in range(total_samples):
        t = i / total_samples
        phase_1 += 2.0 * math.pi * 1760.0 / SAMPLE_RATE  # Fundamental (A6)
        phase_2 += 2.0 * math.pi * 2640.0 / SAMPLE_RATE  # Perfect fifth harmonic (E7)
        phase_3 += 2.0 * math.pi * 3520.0 / SAMPLE_RATE  # Octave overtone (A7)
        envelope = math.exp(-8.5 * t)
        
        # Crisp high-frequency friction burst during the first 30 ms
        transient = (random.random() * 2.0 - 1.0) * math.exp(-60.0 * t) if t < 0.03 else 0.0
        ring = 0.45 * math.sin(phase_1) + 0.35 * math.sin(phase_2) + 0.20 * math.sin(phase_3)
        val = (0.75 * ring + 0.25 * transient) * envelope * 0.48
        samples.append(val)
    return _build_wav_sound(samples)


def create_shield_block_sfx(duration: float = 0.18) -> Sound:
    """
    Creates a heavy, resonant shield deflection or energy barrier impact thud.
    Blends a diving mid-range square/sine wave with a 65 Hz sub-bass foundation.
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    phase = 0.0
    sub_phase = 0.0
    noise_val = 0.0
    for i in range(total_samples):
        t = i / total_samples
        freq = 240.0 * math.exp(-12.0 * t) + 70.0
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        sub_phase += 2.0 * math.pi * 65.0 / SAMPLE_RATE
        envelope = math.exp(-12.0 * t)
        
        raw_noise = random.random() * 2.0 - 1.0
        noise_val += 0.18 * (raw_noise - noise_val)
        
        mid = math.sin(phase)
        square = 1.0 if mid > 0 else -1.0
        val = (0.45 * mid + 0.20 * square + 0.20 * math.sin(sub_phase) + 0.15 * noise_val) * envelope * 0.52
        samples.append(val)
    return _build_wav_sound(samples)


def create_reload_sfx(duration: float = 0.22) -> Sound:
    """
    Creates a 3-stage mechanical firearm reload / lever latch sound:
      1. Magazine release / slide pull (0 - 0.06s, high 1400 Hz click)
      2. Mechanical friction slide (0.06 - 0.13s, subtle filtered noise)
      3. Magazine lock / chamber snap (0.13 - 0.22s, firm 920 Hz double click)
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    phase_1 = 0.0
    phase_2 = 0.0
    noise_val = 0.0
    t_click1 = 0.0
    t_click2 = 0.13
    for i in range(total_samples):
        sec = i / SAMPLE_RATE
        raw_noise = random.random() * 2.0 - 1.0
        noise_val += 0.25 * (raw_noise - noise_val)
        val = 0.0
        
        if sec < 0.06:
            dt1 = sec - t_click1
            phase_1 += 2.0 * math.pi * 1400.0 / SAMPLE_RATE
            env1 = math.exp(-50.0 * dt1)
            val += math.sin(phase_1) * env1 * 0.35
        elif sec < 0.13:
            env_slide = math.sin(math.pi * ((sec - 0.06) / 0.07))
            val += noise_val * env_slide * 0.12
        else:
            dt2 = sec - t_click2
            phase_2 += 2.0 * math.pi * 920.0 / SAMPLE_RATE
            env2 = math.exp(-40.0 * dt2)
            square = 1.0 if math.sin(phase_2) > 0 else -1.0
            val += (0.6 * math.sin(phase_2) + 0.4 * square) * env2 * 0.42
            
        samples.append(val)
    return _build_wav_sound(samples)


def create_empty_sfx(duration: float = 0.05) -> Sound:
    """
    Creates a crisp, hollow mechanical dry fire click when a weapon's magazine is empty.
    Sweeps 950 Hz down to 400 Hz over 50 ms with rapid exponential cutoff.
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    phase = 0.0
    for i in range(total_samples):
        t = i / total_samples
        freq = 950.0 - 550.0 * t
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        envelope = math.exp(-42.0 * t)
        square = 1.0 if math.sin(phase) > 0 else -1.0
        val = (0.5 * math.sin(phase) + 0.5 * square) * envelope * 0.35
        samples.append(val)
    return _build_wav_sound(samples)


def create_shotgun_sfx(duration: float = 0.34) -> Sound:
    """
    Creates a heavy scattergun blast followed by a 2-stage pump-action rack clack:
      1. Muzzle blast & chest thump (0.00 - 0.21s: 150->42 Hz sub-punch + wide-band noise)
      2. Pump pull back (0.21 - 0.27s: 820 Hz metallic slide latch)
      3. Pump push forward (0.27 - 0.34s: 1180 Hz chamber lock snap)
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    phase = 0.0
    rack_phase = 0.0
    noise_val = 0.0
    for i in range(total_samples):
        sec = i / SAMPLE_RATE
        raw_noise = random.random() * 2.0 - 1.0
        noise_val += 0.32 * (raw_noise - noise_val)
        val = 0.0

        if sec < 0.21:
            t_blast = sec / 0.21
            freq = 150.0 * math.exp(-14.0 * t_blast) + 42.0
            phase += 2.0 * math.pi * freq / SAMPLE_RATE
            env = math.exp(-7.5 * t_blast)
            sub_punch = math.sin(phase)
            val = (0.60 * noise_val + 0.40 * sub_punch) * env * 0.65
        elif sec < 0.27:
            dt1 = sec - 0.21
            rack_phase += 2.0 * math.pi * 820.0 / SAMPLE_RATE
            env1 = math.exp(-48.0 * dt1)
            val = (0.55 * math.sin(rack_phase) + 0.45 * noise_val) * env1 * 0.32
        else:
            dt2 = sec - 0.27
            rack_phase += 2.0 * math.pi * 1180.0 / SAMPLE_RATE
            env2 = math.exp(-42.0 * dt2)
            sq = 1.0 if math.sin(rack_phase) > 0 else -1.0
            val = (0.50 * math.sin(rack_phase) + 0.30 * sq + 0.20 * noise_val) * env2 * 0.38

        samples.append(val)
    return _build_wav_sound(samples)


def create_sniper_sfx(duration: float = 0.42) -> Sound:
    """
    Creates a high-velocity precision sniper rifle shot.
    Combines an instantaneous supersonic whip crack (2200 Hz -> 180 Hz in 35 ms),
    a high-pressure metallic barrel ring (880 Hz + 1320 Hz), and a long canyon tail.
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    crack_phase = 0.0
    ring_phase_1 = 0.0
    ring_phase_2 = 0.0
    noise_lp = 0.0
    for i in range(total_samples):
        t = i / total_samples
        sec = i / SAMPLE_RATE

        # Supersonic whip crack transient
        crack_freq = 2200.0 * math.exp(-32.0 * t) + 140.0
        crack_phase += 2.0 * math.pi * crack_freq / SAMPLE_RATE
        crack_env = math.exp(-26.0 * t)

        # Metallic receiver/barrel resonance
        ring_phase_1 += 2.0 * math.pi * 880.0 / SAMPLE_RATE
        ring_phase_2 += 2.0 * math.pi * 1320.0 / SAMPLE_RATE
        ring_env = math.exp(-11.0 * t)
        ring = (0.65 * math.sin(ring_phase_1) + 0.35 * math.sin(ring_phase_2)) * ring_env

        # Canyon echo tail (filtered noise)
        raw_noise = random.random() * 2.0 - 1.0
        cutoff = 0.45 if sec < 0.05 else 0.12
        noise_lp += cutoff * (raw_noise - noise_lp)
        tail_env = math.exp(-5.2 * t)

        val = (0.45 * math.sin(crack_phase) * crack_env + 0.20 * ring + 0.55 * noise_lp * tail_env) * 0.65
        samples.append(val)
    return _build_wav_sound(samples)


def create_charge_up_sfx(duration: float = 0.45) -> Sound:
    """
    Creates an accelerating energy weapon / railgun capacitor charge-up riser.
    Base frequency sweeps quadratically from 160 Hz to 1120 Hz while an LFO pulse
    modulator accelerates from 6 Hz to 28 Hz to build anticipation before firing.
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    carrier_phase = 0.0
    lfo_phase = 0.0
    for i in range(total_samples):
        t = i / total_samples
        freq = 160.0 + 960.0 * (t * t)
        lfo_freq = 6.0 + 22.0 * t
        carrier_phase += 2.0 * math.pi * freq / SAMPLE_RATE
        lfo_phase += 2.0 * math.pi * lfo_freq / SAMPLE_RATE

        # Amplitude rises as capacitor nears full charge, with fade at very end
        pulse = 0.65 + 0.35 * math.sin(lfo_phase)
        env = (0.25 + 0.75 * t) * (1.0 if t < 0.92 else (1.0 - t) / 0.08)

        sine = math.sin(carrier_phase)
        norm_p = (carrier_phase / (2.0 * math.pi)) % 1.0
        tri = 2.0 * abs(2.0 * norm_p - 1.0) - 1.0
        val = (0.65 * sine + 0.35 * tri) * pulse * env * 0.42
        samples.append(val)
    return _build_wav_sound(samples)


def create_sword_slash_sfx(duration: float = 0.16) -> Sound:
    """
    Creates a crisp melee blade cleave cutting through air.
    Blends band-shaped aerodynamic noise with a high-frequency steel edge whistle
    sweeping from 1950 Hz down to 920 Hz.
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    edge_phase = 0.0
    lp_fast = 0.0
    lp_slow = 0.0
    for i in range(total_samples):
        t = i / total_samples
        # Band-pass air whoosh (difference of two low-pass filters)
        raw_noise = random.random() * 2.0 - 1.0
        lp_fast += 0.45 * (raw_noise - lp_fast)
        lp_slow += 0.08 * (raw_noise - lp_slow)
        band_noise = lp_fast - lp_slow

        # Steel blade edge shimmer
        edge_freq = 1950.0 - 1030.0 * (t ** 0.7)
        edge_phase += 2.0 * math.pi * edge_freq / SAMPLE_RATE

        # Skewed bell envelope peaking at 30% of the swing arc
        envelope = math.sin(math.pi * (t ** 0.6)) * math.exp(-2.8 * t)
        val = (0.72 * band_noise + 0.28 * math.sin(edge_phase)) * envelope * 0.55
        samples.append(val)
    return _build_wav_sound(samples)


def create_critical_hit_sfx(duration: float = 0.28) -> Sound:
    """
    Creates a devastating critical strike / headshot impact sound.
    Layers a heavy sub-bass armor slam (320 Hz -> 45 Hz) with a bright 3-partial
    crystalline FM chime burst (G6, C7, G7) for unmistakable high-damage feedback.
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    slam_phase = 0.0
    chime_1 = 0.0
    chime_2 = 0.0
    chime_3 = 0.0
    for i in range(total_samples):
        t = i / total_samples
        # 1. Heavy kinetic punch
        slam_freq = 320.0 * math.exp(-20.0 * t) + 45.0
        slam_phase += 2.0 * math.pi * slam_freq / SAMPLE_RATE
        slam_env = math.exp(-10.0 * t)
        slam_sine = math.sin(slam_phase)
        slam_sq = 1.0 if slam_sine > 0 else -1.0
        slam = (0.70 * slam_sine + 0.30 * slam_sq) * slam_env

        # 2. Crystalline critical harmonic burst (1567.98 Hz, 2093.00 Hz, 3135.96 Hz)
        chime_1 += 2.0 * math.pi * 1567.98 / SAMPLE_RATE
        chime_2 += 2.0 * math.pi * 2093.00 / SAMPLE_RATE
        chime_3 += 2.0 * math.pi * 3135.96 / SAMPLE_RATE
        chime_env = math.exp(-6.5 * t)
        spark = (0.45 * math.sin(chime_1) + 0.35 * math.sin(chime_2) + 0.20 * math.sin(chime_3)) * chime_env

        val = (0.55 * slam + 0.45 * spark) * 0.55
        samples.append(val)
    return _build_wav_sound(samples)


def create_ricochet_sfx(duration: float = 0.24) -> Sound:
    """
    Creates a classic bullet deflection / wall ricochet "pew-twang" ping.
    Uses a sharp metallic contact transient followed by a rapidly frequency-modulated
    whistle sweeping from 2600 Hz down to 580 Hz with a 35 Hz Doppler warble.
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    phase = 0.0
    mod_phase = 0.0
    for i in range(total_samples):
        t = i / total_samples
        mod_phase += 2.0 * math.pi * 35.0 / SAMPLE_RATE
        warble = math.sin(mod_phase) * 140.0 * (1.0 - t)
        freq = 2600.0 * ((1.0 - t) ** 1.6) + 580.0 + warble
        phase += 2.0 * math.pi * freq / SAMPLE_RATE

        envelope = math.exp(-6.5 * t)
        ping = (random.random() * 2.0 - 1.0) * math.exp(-70.0 * t) if t < 0.02 else 0.0
        val = (0.80 * math.sin(phase) + 0.20 * ping) * envelope * 0.44
        samples.append(val)
    return _build_wav_sound(samples)


def create_flame_sfx(duration: float = 0.38) -> Sound:
    """
    Creates a roaring fire / flamethrower ignition burst with crackling embers.
    Modulates a low-pass filtered turbulence generator with an 8 Hz thermal draft wave
    and injects stochastic high-frequency ember pops.
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    noise_lp = 0.0
    draft_phase = 0.0
    sub_phase = 0.0
    for i in range(total_samples):
        t = i / total_samples
        draft_phase += 2.0 * math.pi * 8.5 / SAMPLE_RATE
        sub_phase += 2.0 * math.pi * 78.0 / SAMPLE_RATE

        raw_noise = random.random() * 2.0 - 1.0
        cutoff = 0.14 + 0.06 * math.sin(draft_phase)
        noise_lp += cutoff * (raw_noise - noise_lp)

        # Stochastic ember crackle spikes
        crackle = raw_noise * 0.45 if abs(raw_noise) > 0.96 else 0.0
        envelope = math.sin(math.pi * (t ** 0.55)) * math.exp(-2.2 * t)
        val = (0.65 * noise_lp + 0.20 * math.sin(sub_phase) + 0.15 * crackle) * envelope * 0.55
        samples.append(val)
    return _build_wav_sound(samples)


def create_freeze_sfx(duration: float = 0.35) -> Sound:
    """
    Creates a crystalline frost / ice shatter sound effect.
    Synthesizes 4 high-frequency inharmonic FM bell partials (2100 Hz to 4680 Hz)
    layered with crisp, brittle ice-cracking impulses.
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    p1 = 0.0
    p2 = 0.0
    p3 = 0.0
    p4 = 0.0
    for i in range(total_samples):
        t = i / total_samples
        # Staggered crystal partials
        p1 += 2.0 * math.pi * 2120.0 / SAMPLE_RATE
        p2 += 2.0 * math.pi * 2890.0 / SAMPLE_RATE
        p3 += 2.0 * math.pi * 3740.0 / SAMPLE_RATE
        p4 += 2.0 * math.pi * 4680.0 / SAMPLE_RATE

        env1 = math.exp(-7.0 * t)
        env2 = math.exp(-9.0 * max(0.0, t - 0.05)) if t >= 0.05 else 0.0
        env3 = math.exp(-11.0 * max(0.0, t - 0.11)) if t >= 0.11 else 0.0

        crystals = (
            0.35 * math.sin(p1) * env1 +
            0.30 * math.sin(p2 + 0.5 * math.sin(p1)) * env2 +
            0.20 * math.sin(p3) * env2 +
            0.15 * math.sin(p4) * env3
        )
        frost_crackle = (random.random() * 2.0 - 1.0) * math.exp(-18.0 * t) * 0.25
        samples.append((crystals + frost_crackle) * 0.45)
    return _build_wav_sound(samples)


# ==============================================================================
# SFX GENERATORS - MOVEMENT & KINEMATICS (10)
# ==============================================================================

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


def create_dash_sfx(duration: float = 0.18) -> Sound:
    """
    Creates an aerodynamic rushing air whoosh sound for dashes, dodges, and weapon swings.
    Blends a downward pitch dive with envelope-tracked filtered noise.
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    noise_val = 0.0
    phase = 0.0
    for i in range(total_samples):
        t = i / total_samples
        freq = 300.0 * (1.0 - t * 0.8)
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        # Envelope rises rapidly on root curve then drops smoothly via exponential decay
        envelope = math.sin(math.pi * (t ** 0.5)) * math.exp(-3.5 * t)
        
        raw_noise = random.random() * 2.0 - 1.0
        noise_val += 0.25 * (raw_noise - noise_val)
        sine = math.sin(phase)
        val = (0.5 * sine + 0.5 * noise_val) * envelope * 0.50
        samples.append(val)
    return _build_wav_sound(samples)


def create_footstep_sfx(duration: float = 0.07) -> Sound:
    """
    Creates a subtle, muffled floor tap with surface friction for character footsteps.
    Kept short and low-volume so rapid locomotion does not overwhelm combat or music.
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    phase = 0.0
    noise_val = 0.0
    for i in range(total_samples):
        t = i / total_samples
        freq = 120.0 * math.exp(-25.0 * t) + 40.0
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        envelope = math.exp(-28.0 * t)
        
        raw_noise = random.random() * 2.0 - 1.0
        noise_val += 0.30 * (raw_noise - noise_val)
        friction = noise_val if t < 0.25 else 0.0
        val = (0.70 * math.sin(phase) + 0.30 * friction) * envelope * 0.35
        samples.append(val)
    return _build_wav_sound(samples)


def create_land_sfx(duration: float = 0.14) -> Sound:
    """
    Creates a solid ground impact thud when a character lands from a jump or fall.
    Combines a deep 160 Hz -> 35 Hz dive with low-frequency rumble.
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    phase = 0.0
    noise_val = 0.0
    for i in range(total_samples):
        t = i / total_samples
        freq = 160.0 * math.exp(-20.0 * t) + 35.0
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        envelope = math.exp(-14.0 * t)
        
        raw_noise = random.random() * 2.0 - 1.0
        noise_val += 0.20 * (raw_noise - noise_val)
        val = (0.60 * math.sin(phase) + 0.40 * noise_val) * envelope * 0.55
        samples.append(val)
    return _build_wav_sound(samples)


def create_double_jump_sfx(duration: float = 0.18) -> Sound:
    """
    Creates a nimble 2-stage mid-air double-jump flutter boost.
    Stage 1 (0 - 38%) performs a quick air-kick sweep (240->480 Hz);
    Stage 2 (38% - 100%) leaps an octave higher (480->980 Hz) with bright triangle-square lift.
    """
    total_samples = int(SAMPLE_RATE * duration)
    split = int(total_samples * 0.38)
    samples = []
    phase = 0.0
    for i in range(total_samples):
        if i < split:
            t_sub = i / max(1, split)
            freq = 240.0 + 240.0 * t_sub
            env = 1.0 - 0.3 * t_sub
        else:
            t_sub = (i - split) / max(1, total_samples - split)
            freq = 480.0 + 500.0 * (t_sub ** 0.8)
            env = math.exp(-3.5 * t_sub)

        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        sine = math.sin(phase)
        sq = 1.0 if sine > 0 else -1.0
        val = (0.55 * sine + 0.45 * sq) * env * 0.38
        samples.append(val)
    return _build_wav_sound(samples)


def create_grapple_sfx(duration: float = 0.30) -> Sound:
    """
    Creates a 3-stage mechanical grappling hook launch and anchor lock:
      1. Pneumatic piston fire pop (0.00 - 0.05s)
      2. High-speed metallic cable winch ratchet (0.05 - 0.22s, 48 Hz gear teeth)
      3. Heavy magnetic / claw anchor clank (0.22 - 0.30s)
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    phase = 0.0
    ratchet_phase = 0.0
    for i in range(total_samples):
        sec = i / SAMPLE_RATE
        val = 0.0
        if sec < 0.05:
            t1 = sec / 0.05
            freq = 420.0 - 240.0 * t1
            phase += 2.0 * math.pi * freq / SAMPLE_RATE
            val = math.sin(phase) * math.exp(-35.0 * sec) * 0.48
        elif sec < 0.22:
            t2 = (sec - 0.05) / 0.17
            freq = 1150.0 + 650.0 * t2
            phase += 2.0 * math.pi * freq / SAMPLE_RATE
            ratchet_phase += 2.0 * math.pi * 48.0 / SAMPLE_RATE
            teeth = 0.55 + 0.45 * (1.0 if math.sin(ratchet_phase) > 0 else -1.0)
            val = math.sin(phase) * teeth * 0.28
        else:
            dt3 = sec - 0.22
            phase += 2.0 * math.pi * 1380.0 / SAMPLE_RATE
            sub = math.sin(2.0 * math.pi * 220.0 * dt3)
            env3 = math.exp(-38.0 * dt3)
            sq = 1.0 if math.sin(phase) > 0 else -1.0
            val = (0.45 * sq + 0.55 * sub) * env3 * 0.50
        samples.append(val)
    return _build_wav_sound(samples)


def create_thruster_sfx(duration: float = 0.32) -> Sound:
    """
    Creates a deep mecha / spacecraft booster thruster ignition and burn.
    Combines a 72 Hz combustion rumble, low-pass rocket exhaust noise, and a rising
    turbine spool whine (420 Hz -> 780 Hz).
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    rumble_phase = 0.0
    spool_phase = 0.0
    noise_lp = 0.0
    for i in range(total_samples):
        t = i / total_samples
        rumble_phase += 2.0 * math.pi * 72.0 / SAMPLE_RATE
        spool_freq = 420.0 + 360.0 * (t ** 0.7)
        spool_phase += 2.0 * math.pi * spool_freq / SAMPLE_RATE

        raw_noise = random.random() * 2.0 - 1.0
        noise_lp += 0.22 * (raw_noise - noise_lp)

        envelope = math.sin(math.pi * (t ** 0.45)) * math.exp(-2.0 * t)
        val = (0.55 * noise_lp + 0.30 * math.sin(rumble_phase) + 0.15 * math.sin(spool_phase)) * envelope * 0.52
        samples.append(val)
    return _build_wav_sound(samples)


def create_teleport_sfx(duration: float = 0.28) -> Sound:
    """
    Creates a sci-fi quantum blink / spatial warp sound.
    Features a reverse-envelope vacuum implosion (0 - 40%) followed by a ring-modulated
    harmonic fold-out sweep (220 Hz -> 1760 Hz).
    """
    total_samples = int(SAMPLE_RATE * duration)
    split = int(total_samples * 0.40)
    samples = []
    carrier_phase = 0.0
    mod_phase = 0.0
    for i in range(total_samples):
        if i < split:
            t_in = i / max(1, split)
            freq = 660.0 - 440.0 * t_in
            env = t_in * t_in
        else:
            t_out = (i - split) / max(1, total_samples - split)
            freq = 220.0 + 1540.0 * (t_out ** 1.4)
            env = math.exp(-5.5 * t_out)

        carrier_phase += 2.0 * math.pi * freq / SAMPLE_RATE
        mod_phase += 2.0 * math.pi * 45.0 / SAMPLE_RATE
        # Ring modulation: carrier multiplied by modulator
        ring_mod = math.sin(carrier_phase) * (0.65 + 0.35 * math.cos(mod_phase))
        samples.append(ring_mod * env * 0.44)
    return _build_wav_sound(samples)


def create_slide_sfx(duration: float = 0.24) -> Sound:
    """
    Creates a kinetic ground-slide, wall-slide, or vehicle drift friction scrape.
    Blends band-filtered surface scuff noise with a decaying resonant body tone.
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    phase = 0.0
    lp_1 = 0.0
    lp_2 = 0.0
    for i in range(total_samples):
        t = i / total_samples
        freq = 210.0 * math.exp(-6.0 * t) + 85.0
        phase += 2.0 * math.pi * freq / SAMPLE_RATE

        raw_noise = random.random() * 2.0 - 1.0
        lp_1 += 0.38 * (raw_noise - lp_1)
        lp_2 += 0.09 * (raw_noise - lp_2)
        scrape = lp_1 - lp_2

        envelope = math.sin(math.pi * (t ** 0.4)) * math.exp(-3.2 * t)
        val = (0.72 * scrape + 0.28 * math.sin(phase)) * envelope * 0.45
        samples.append(val)
    return _build_wav_sound(samples)


def create_bounce_sfx(duration: float = 0.22) -> Sound:
    """
    Creates an elastic springboard / bumper / slime rebound "boing" sound.
    Sweeps pitch from 180 Hz to 440 Hz while oscillating with a damped 24 Hz pitch wobble.
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    phase = 0.0
    wobble_phase = 0.0
    for i in range(total_samples):
        t = i / total_samples
        wobble_phase += 2.0 * math.pi * 24.0 / SAMPLE_RATE
        wobble = math.sin(wobble_phase) * 95.0 * math.exp(-4.0 * t)
        freq = 180.0 + 260.0 * (t ** 0.6) + wobble
        phase += 2.0 * math.pi * freq / SAMPLE_RATE

        envelope = math.exp(-5.5 * t)
        sine = math.sin(phase)
        norm_p = (phase / (2.0 * math.pi)) % 1.0
        tri = 2.0 * abs(2.0 * norm_p - 1.0) - 1.0
        val = (0.65 * sine + 0.35 * tri) * envelope * 0.42
        samples.append(val)
    return _build_wav_sound(samples)


# ==============================================================================
# SFX GENERATORS - PROGRESSION, REWARDS & HEALTH (11)
# ==============================================================================

def create_coin_sfx(duration: float = 0.16) -> Sound:
    """Creates a 2-tone melodic pickup chime (B5 to E6)."""
    total_samples = int(SAMPLE_RATE * duration)
    half_samples = total_samples // 2
    samples = []
    phase = 0.0
    for i in range(total_samples):
        freq = 987.77 if i < half_samples else 1318.51  # B5 then E6
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        t_local = (i % half_samples) / half_samples
        envelope = 1.0 - t_local * 0.7
        val = math.sin(phase) * envelope * 0.40
        samples.append(val)
    return _build_wav_sound(samples)


def create_powerup_sfx(duration: float = 0.32) -> Sound:
    """Creates a rising 4-note victory / powerup fanfare (E4, G4, B4, E5)."""
    notes = [330.0, 392.0, 493.88, 659.25]  # E4, G4, B4, E5
    step_samples = int(SAMPLE_RATE * (duration / len(notes)))
    samples = []
    for note in notes:
        phase = 0.0
        for i in range(step_samples):
            phase += 2.0 * math.pi * note / SAMPLE_RATE
            t = i / step_samples
            env = math.exp(-4.0 * t)
            sq = 1.0 if math.sin(phase) > 0 else -1.0
            sine = math.sin(phase)
            samples.append((0.6 * sq + 0.4 * sine) * env * 0.35)
    return _build_wav_sound(samples)


def create_level_up_sfx(duration: float = 0.48) -> Sound:
    """
    Creates a sparkling, triumphant 5-note pentatonic fanfare (C5, E5, G5, B5, C6).
    Each note sustains smoothly into the next, blending pure sine and bright triangle waves.
    """
    notes = [523.25, 659.25, 783.99, 987.77, 1046.50]  # C5, E5, G5, B5, C6
    total_samples = int(SAMPLE_RATE * duration)
    step = total_samples // len(notes)
    samples = []
    phase = 0.0
    for n_idx in range(len(notes)):
        freq = notes[n_idx]
        note_len = step if n_idx < len(notes) - 1 else total_samples - step * (len(notes) - 1)
        for i in range(note_len):
            phase += 2.0 * math.pi * freq / SAMPLE_RATE
            t = i / note_len
            envelope = math.exp(-3.5 * t)
            sine = math.sin(phase)
            # Mathematical triangle wave: 2 * |2 * (phase_normalized % 1) - 1| - 1
            norm_phase = (phase / (2.0 * math.pi)) % 1.0
            triangle = 2.0 * abs(2.0 * norm_phase - 1.0) - 1.0
            val = (0.70 * sine + 0.30 * triangle) * envelope * 0.40
            samples.append(val)
    return _build_wav_sound(samples)


def create_heal_sfx(duration: float = 0.32) -> Sound:
    """
    Creates a soothing, shimmering restoration chime for health potions or recovery.
    Frequency glides gently upward (380 Hz to 740 Hz) modulated by a 10 Hz vibrato wave.
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    phase = 0.0
    vibrato_phase = 0.0
    for i in range(total_samples):
        t = i / total_samples
        vibrato_phase += 2.0 * math.pi * 10.0 / SAMPLE_RATE
        vibrato = math.sin(vibrato_phase) * 22.0
        freq = 380.0 + 360.0 * (t ** 0.8) + vibrato
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        envelope = math.sin(math.pi * t)
        val = math.sin(phase) * envelope * 0.35
        samples.append(val)
    return _build_wav_sound(samples)


def create_hurt_sfx(duration: float = 0.15) -> Sound:
    """Creates an aggressive hurt groan sound with low pitch slide and distortion."""
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


def create_chest_open_sfx(duration: float = 0.46) -> Sound:
    """
    Creates an RPG treasure chest unlock and discovery fanfare:
      1. Heavy iron lock unlatch click (0.00 - 0.09s)
      2. Magical 4-note ascending Lydian arpeggio (D5, F#5, A5, C#6) with bell harmonics.
    """
    total_samples = int(SAMPLE_RATE * duration)
    latch_samples = int(SAMPLE_RATE * 0.09)
    chime_samples = total_samples - latch_samples
    notes = [587.33, 739.99, 880.00, 1108.73]  # D5, F#5, A5, C#6
    step = chime_samples // len(notes)

    samples = []
    latch_phase = 0.0
    for i in range(latch_samples):
        t_l = i / max(1, latch_samples)
        freq = 520.0 if t_l < 0.45 else 780.0
        latch_phase += 2.0 * math.pi * freq / SAMPLE_RATE
        env = math.exp(-22.0 * (t_l % 0.45))
        samples.append(math.sin(latch_phase) * env * 0.35)

    phase = 0.0
    overtone_phase = 0.0
    for n_idx in range(len(notes)):
        freq = notes[n_idx]
        n_len = step if n_idx < len(notes) - 1 else chime_samples - step * (len(notes) - 1)
        for i in range(n_len):
            t_n = i / max(1, n_len)
            phase += 2.0 * math.pi * freq / SAMPLE_RATE
            overtone_phase += 2.0 * math.pi * (freq * 2.0) / SAMPLE_RATE
            decay = 2.2 if n_idx == len(notes) - 1 else 4.2
            env = math.exp(-decay * t_n)
            val = (0.72 * math.sin(phase) + 0.28 * math.sin(overtone_phase)) * env * 0.42
            samples.append(val)
    return _build_wav_sound(samples)


def create_craft_sfx(duration: float = 0.36) -> Sound:
    """
    Creates a blacksmith forge anvil strike and item crafting completion sound.
    Strikes a metallic anvil twice (t = 0.00s and t = 0.14s using steel modes at
    1180 Hz, 1770 Hz, and 2950 Hz) with a warm harmonic synthesis tail.
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    p1 = 0.0
    p2 = 0.0
    p3 = 0.0
    glow_phase = 0.0
    for i in range(total_samples):
        sec = i / SAMPLE_RATE
        # Two hammer strikes: first at 0.0s, second higher-pitched strike at 0.14s
        pitch_mult = 1.0 if sec < 0.14 else 1.18
        dt_strike = sec if sec < 0.14 else (sec - 0.14)

        p1 += 2.0 * math.pi * (1180.0 * pitch_mult) / SAMPLE_RATE
        p2 += 2.0 * math.pi * (1770.0 * pitch_mult) / SAMPLE_RATE
        p3 += 2.0 * math.pi * (2950.0 * pitch_mult) / SAMPLE_RATE
        glow_phase += 2.0 * math.pi * 587.33 / SAMPLE_RATE

        strike_env = math.exp(-16.0 * dt_strike)
        spark_noise = (random.random() * 2.0 - 1.0) * math.exp(-65.0 * dt_strike) if dt_strike < 0.025 else 0.0
        anvil = (0.45 * math.sin(p1) + 0.35 * math.sin(p2) + 0.20 * math.sin(p3)) * strike_env
        glow = math.sin(glow_phase) * math.sin(math.pi * (sec / duration)) * 0.18

        val = (0.72 * anvil + 0.18 * spark_noise + glow) * 0.48
        samples.append(val)
    return _build_wav_sound(samples)


def create_debuff_sfx(duration: float = 0.28) -> Sound:
    """
    Creates a sinister status affliction, poison, curse, or encumbrance penalty sound.
    Steps downward through a dissonant diminished tritone interval (440 Hz -> 311.13 Hz -> 220 Hz)
    with gritty saw-square subharmonics.
    """
    notes = [440.00, 311.13, 220.00]  # A4 -> Eb4 (tritone) -> A3
    total_samples = int(SAMPLE_RATE * duration)
    step = total_samples // len(notes)
    samples = []
    phase = 0.0
    wobble_phase = 0.0
    for n_idx in range(len(notes)):
        base_freq = notes[n_idx]
        n_len = step if n_idx < len(notes) - 1 else total_samples - step * (len(notes) - 1)
        for i in range(n_len):
            t_n = i / max(1, n_len)
            wobble_phase += 2.0 * math.pi * 18.0 / SAMPLE_RATE
            freq = base_freq - 18.0 * t_n + math.sin(wobble_phase) * 8.0
            phase += 2.0 * math.pi * freq / SAMPLE_RATE

            env = math.exp(-3.8 * t_n)
            sine = math.sin(phase)
            sq = 1.0 if sine > 0 else -1.0
            val = (0.55 * sine + 0.45 * sq) * env * 0.38
            samples.append(val)
    return _build_wav_sound(samples)


def create_gem_sfx(duration: float = 0.24) -> Sound:
    """
    Creates an ultra-bright crystalline gem / rare drop pickup sparkle.
    Plays a rapid 3-note high-octave bell arpeggio (C6 -> G6 -> C7) with glassy FM overtones.
    """
    notes = [1046.50, 1567.98, 2093.00]  # C6, G6, C7
    total_samples = int(SAMPLE_RATE * duration)
    step = total_samples // len(notes)
    samples = []
    phase = 0.0
    mod_phase = 0.0
    for n_idx in range(len(notes)):
        freq = notes[n_idx]
        n_len = step if n_idx < len(notes) - 1 else total_samples - step * (len(notes) - 1)
        for i in range(n_len):
            t_n = i / max(1, n_len)
            phase += 2.0 * math.pi * freq / SAMPLE_RATE
            mod_phase += 2.0 * math.pi * (freq * 2.5) / SAMPLE_RATE
            decay = 3.0 if n_idx == len(notes) - 1 else 6.0
            env = math.exp(-decay * t_n)
            bell = math.sin(phase + 0.35 * math.sin(mod_phase) * env)
            samples.append(bell * env * 0.38)
    return _build_wav_sound(samples)


def create_revive_sfx(duration: float = 0.50) -> Sound:
    """
    Creates an uplifting resurrection / checkpoint restore harmonic swell.
    Synthesizes a warm F-major organ triad (F4, A4, C5) that glides upward to include F5
    with a 6 Hz celestial shimmer.
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    p_root = 0.0
    p_third = 0.0
    p_fifth = 0.0
    p_oct = 0.0
    lfo_phase = 0.0
    for i in range(total_samples):
        t = i / total_samples
        lfo_phase += 2.0 * math.pi * 6.5 / SAMPLE_RATE
        shimmer = 1.0 + 0.006 * math.sin(lfo_phase)

        p_root += 2.0 * math.pi * (349.23 * shimmer) / SAMPLE_RATE   # F4
        p_third += 2.0 * math.pi * (440.00 * shimmer) / SAMPLE_RATE  # A4
        p_fifth += 2.0 * math.pi * (523.25 * shimmer) / SAMPLE_RATE  # C5
        p_oct += 2.0 * math.pi * (698.46 * shimmer) / SAMPLE_RATE    # F5

        # Smooth cathedral swell envelope
        env = math.sin(math.pi * (t ** 0.7))
        oct_weight = t * 0.35
        chord = (
            0.32 * math.sin(p_root) +
            0.26 * math.sin(p_third) +
            0.24 * math.sin(p_fifth) +
            oct_weight * math.sin(p_oct)
        )
        samples.append(chord * env * 0.45)
    return _build_wav_sound(samples)


def create_death_sfx(duration: float = 0.45) -> Sound:
    """
    Creates a dramatic arcade defeat / knockout sequence.
    Steps through 4 descending minor/diminished square-triangle tones before collapsing
    into a deep sub-bass power-down drop (261.63 Hz -> 45.0 Hz).
    """
    total_samples = int(SAMPLE_RATE * duration)
    steps_samples = int(total_samples * 0.56)
    drop_samples = total_samples - steps_samples
    step_notes = [392.00, 349.23, 311.13, 261.63]  # G4, F4, Eb4, C4
    step_len = steps_samples // len(step_notes)

    samples = []
    phase = 0.0
    for n_idx in range(len(step_notes)):
        freq = step_notes[n_idx]
        n_len = step_len if n_idx < len(step_notes) - 1 else steps_samples - step_len * (len(step_notes) - 1)
        for i in range(n_len):
            t_n = i / max(1, n_len)
            phase += 2.0 * math.pi * freq / SAMPLE_RATE
            env = 1.0 - 0.35 * t_n
            sine = math.sin(phase)
            sq = 1.0 if sine > 0 else -1.0
            samples.append((0.55 * sine + 0.45 * sq) * env * 0.40)

    for i in range(drop_samples):
        t_d = i / max(1, drop_samples)
        freq = 261.63 * ((1.0 - t_d) ** 1.5) + 45.0
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        env = math.exp(-3.5 * t_d)
        sine = math.sin(phase)
        sq = 1.0 if sine > 0 else -1.0
        samples.append((0.65 * sine + 0.35 * sq) * env * 0.45)
    return _build_wav_sound(samples)


# ==============================================================================
# SFX GENERATORS - USER INTERFACE & SIGNALS (11)
# ==============================================================================

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


def create_select_sfx(duration: float = 0.03) -> Sound:
    """
    Creates an ultra-soft, gentle UI cursor hover tick (1750 Hz pure sine window).
    Designed to remain clean and non-fatiguing during rapid menu or inventory navigation.
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    phase = 0.0
    for i in range(total_samples):
        t = i / total_samples
        phase += 2.0 * math.pi * 1750.0 / SAMPLE_RATE
        envelope = math.sin(math.pi * t)
        val = math.sin(phase) * envelope * 0.22
        samples.append(val)
    return _build_wav_sound(samples)


def create_cancel_sfx(duration: float = 0.12) -> Sound:
    """
    Creates a soft descending 2-tone dismissal blip for UI back, close, or cancel actions.
    Steps down from 740 Hz to 494 Hz with gentle linear decay.
    """
    total_samples = int(SAMPLE_RATE * duration)
    half = total_samples // 2
    samples = []
    phase = 0.0
    for i in range(total_samples):
        freq = 740.0 if i < half else 494.0
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        t_loc = (i % half) / half
        envelope = 1.0 - t_loc * 0.8
        val = math.sin(phase) * envelope * 0.30
        samples.append(val)
    return _build_wav_sound(samples)


def create_error_sfx(duration: float = 0.20) -> Sound:
    """
    Creates a low, harsh retro buzzer for invalid actions, locked gates, or insufficient funds.
    Emits two dissonant frequencies (125 Hz and 133 Hz) producing an aggressive 8 Hz beat.
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    phase_1 = 0.0
    phase_2 = 0.0
    for i in range(total_samples):
        t = i / total_samples
        phase_1 += 2.0 * math.pi * 125.0 / SAMPLE_RATE
        phase_2 += 2.0 * math.pi * 133.0 / SAMPLE_RATE
        envelope = 1.0 - t
        sq1 = 1.0 if math.sin(phase_1) > 0 else -1.0
        sq2 = 1.0 if math.sin(phase_2) > 0 else -1.0
        val = (0.5 * sq1 + 0.5 * sq2) * envelope * 0.32
        samples.append(val)
    return _build_wav_sound(samples)


def create_alert_sfx(duration: float = 0.22) -> Sound:
    """
    Creates a piercing 2-pulse exclamation alarm chirp (stealth detection or turret lock-on).
    Emits an 880 Hz pulse (A5) followed by a louder 1318.5 Hz pulse (E6).
    """
    total_samples = int(SAMPLE_RATE * duration)
    half = total_samples // 2
    samples = []
    phase_1 = 0.0
    phase_2 = 0.0
    for i in range(total_samples):
        if i < half:
            phase_1 += 2.0 * math.pi * 880.0 / SAMPLE_RATE
            t_sub = i / half
            env = math.sin(math.pi * t_sub)
            sq = 1.0 if math.sin(phase_1) > 0 else -1.0
            val = (0.65 * math.sin(phase_1) + 0.35 * sq) * env * 0.38
        else:
            phase_2 += 2.0 * math.pi * 1318.51 / SAMPLE_RATE
            t_sub = (i - half) / (total_samples - half)
            env = math.sin(math.pi * t_sub)
            sq = 1.0 if math.sin(phase_2) > 0 else -1.0
            val = (0.65 * math.sin(phase_2) + 0.35 * sq) * env * 0.45
        samples.append(val)
    return _build_wav_sound(samples)


def create_confirm_sfx(duration: float = 0.12) -> Sound:
    """
    Creates a crisp, positive 2-tone ascending perfect-fifth UI accept chime (E5 -> B5).
    Ideal for confirming menu dialogs, equipping gear, or locking in selections.
    """
    total_samples = int(SAMPLE_RATE * duration)
    half = total_samples // 2
    samples = []
    phase = 0.0
    for i in range(total_samples):
        freq = 659.25 if i < half else 987.77  # E5 then B5
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        t_loc = (i % max(1, half)) / max(1, half)
        envelope = math.exp(-4.5 * t_loc)
        sine = math.sin(phase)
        norm_p = (phase / (2.0 * math.pi)) % 1.0
        tri = 2.0 * abs(2.0 * norm_p - 1.0) - 1.0
        val = (0.75 * sine + 0.25 * tri) * envelope * 0.35
        samples.append(val)
    return _build_wav_sound(samples)


def create_pause_sfx(duration: float = 0.18) -> Sound:
    """
    Creates a classic 4-note retro staccato pause/menu stinger (C6 - G5 - E5 - C6).
    Cuts cleanly through active gameplay when opening or closing a pause overlay.
    """
    notes = [1046.50, 783.99, 659.25, 1046.50]
    total_samples = int(SAMPLE_RATE * duration)
    step = total_samples // len(notes)
    samples = []
    phase = 0.0
    for n_idx in range(len(notes)):
        freq = notes[n_idx]
        n_len = step if n_idx < len(notes) - 1 else total_samples - step * (len(notes) - 1)
        for i in range(n_len):
            t_n = i / max(1, n_len)
            phase += 2.0 * math.pi * freq / SAMPLE_RATE
            env = math.exp(-6.0 * t_n)
            sine = math.sin(phase)
            sq = 1.0 if sine > 0 else -1.0
            samples.append((0.60 * sine + 0.40 * sq) * env * 0.32)
    return _build_wav_sound(samples)


def create_typewriter_sfx(duration: float = 0.025) -> Sound:
    """
    Creates an ultra-short 25ms mechanical keystroke / RPG dialogue character blip.
    Combines a warm 680 Hz -> 320 Hz pitch pop with a tiny tactile key-cap click so
    rapid 25-char/sec text rendering sounds crisp without causing ear fatigue.
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    phase = 0.0
    for i in range(total_samples):
        t = i / total_samples
        freq = 680.0 - 360.0 * t
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        env = math.exp(-32.0 * t)
        click_noise = (random.random() * 2.0 - 1.0) * 0.25 if t < 0.18 else 0.0
        val = (0.80 * math.sin(phase) + click_noise) * env * 0.26
        samples.append(val)
    return _build_wav_sound(samples)


def create_notification_sfx(duration: float = 0.24) -> Sound:
    """
    Creates a pleasant dual-chime toast notification / achievement / quest update bell.
    Blends an A5 (880 Hz) chime into a sustained D6 (1174.66 Hz) harmonic bell.
    """
    total_samples = int(SAMPLE_RATE * duration)
    split = int(total_samples * 0.35)
    samples = []
    p1 = 0.0
    p2 = 0.0
    for i in range(total_samples):
        p1 += 2.0 * math.pi * 880.00 / SAMPLE_RATE
        p2 += 2.0 * math.pi * 1174.66 / SAMPLE_RATE
        t1 = i / total_samples
        env1 = math.exp(-7.5 * t1)
        val = 0.60 * math.sin(p1) * env1
        if i >= split:
            t2 = (i - split) / max(1, total_samples - split)
            env2 = math.exp(-4.5 * t2)
            val += 0.75 * math.sin(p2) * env2
        samples.append(val * 0.36)
    return _build_wav_sound(samples)


def create_sonar_ping_sfx(duration: float = 0.34) -> Sound:
    """
    Creates a submarine / radar / minimap high-Q resonant sonar ping (1480 Hz)
    followed by an attenuated secondary echo reflection at t = 0.17s.
    """
    total_samples = int(SAMPLE_RATE * duration)
    echo_start = int(total_samples * 0.50)
    samples = []
    phase = 0.0
    for i in range(total_samples):
        phase += 2.0 * math.pi * 1480.0 / SAMPLE_RATE
        t = i / total_samples
        env_main = math.exp(-14.0 * t)
        val = math.sin(phase) * env_main
        if i >= echo_start:
            t_echo = (i - echo_start) / max(1, total_samples - echo_start)
            env_echo = math.exp(-12.0 * t_echo)
            val += 0.38 * math.sin(phase) * env_echo
        samples.append(val * 0.38)
    return _build_wav_sound(samples)


def create_countdown_sfx(duration: float = 0.10) -> Sound:
    """
    Creates a crisp arcade timer / race / QTE countdown beep (880 Hz A5).
    Uses a fast 3ms attack window and a clean harmonic overtone for timing precision.
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    phase_1 = 0.0
    phase_2 = 0.0
    for i in range(total_samples):
        t = i / total_samples
        phase_1 += 2.0 * math.pi * 880.0 / SAMPLE_RATE
        phase_2 += 2.0 * math.pi * 1760.0 / SAMPLE_RATE
        attack = min(1.0, t / 0.04)
        decay = math.exp(-6.5 * t)
        sine = math.sin(phase_1)
        sq = 1.0 if sine > 0 else -1.0
        val = (0.65 * sine + 0.20 * sq + 0.15 * math.sin(phase_2)) * attack * decay * 0.36
        samples.append(val)
    return _build_wav_sound(samples)


# ==============================================================================
# SOUND LIBRARY (CACHE & MANAGEMENT)
# ==============================================================================

class SoundLibrary:
    """
    Manages a cached collection of synthesized sounds.
    Prevents re-synthesizing audio every frame. Call library.play('laser') anywhere.
    
    C++ / Architectural Mapping:
      Equivalent to an AudioResourceManager wrapping std::unordered_map<std::string, Sound>.
      All waveforms are generated once during startup, stored in video/audio memory,
      and reused frame-by-frame with zero allocation overhead.
    """
    def __init__(self):
        self.sounds = {}
        self.aliases = {
            "blip": "select",
            "shoot": "laser",
            "boom": "explosion",
            "slash": "sword_slash",
            "crit": "critical_hit",
            "pickup": "coin",
            "ping": "sonar_ping",
            "beep": "countdown"
        }
        self.is_initialized = False

    def init_defaults(self):
        """
        Synthesizes and caches all 48 default game sound effects covering
        combat, kinematics, progression, and user interface actions.
        """
        # Combat & Weapons (16)
        self.sounds["laser"] = create_laser_sfx()
        self.sounds["heavy_laser"] = create_heavy_laser_sfx()
        self.sounds["explosion"] = create_explosion_sfx()
        self.sounds["hit"] = create_hit_sfx()
        self.sounds["parry"] = create_parry_sfx()
        self.sounds["shield_block"] = create_shield_block_sfx()
        self.sounds["reload"] = create_reload_sfx()
        self.sounds["empty"] = create_empty_sfx()
        self.sounds["shotgun"] = create_shotgun_sfx()
        self.sounds["sniper"] = create_sniper_sfx()
        self.sounds["charge_up"] = create_charge_up_sfx()
        self.sounds["sword_slash"] = create_sword_slash_sfx()
        self.sounds["critical_hit"] = create_critical_hit_sfx()
        self.sounds["ricochet"] = create_ricochet_sfx()
        self.sounds["flame"] = create_flame_sfx()
        self.sounds["freeze"] = create_freeze_sfx()
        
        # Movement & Kinematics (10)
        self.sounds["jump"] = create_jump_sfx()
        self.sounds["dash"] = create_dash_sfx()
        self.sounds["footstep"] = create_footstep_sfx()
        self.sounds["land"] = create_land_sfx()
        self.sounds["double_jump"] = create_double_jump_sfx()
        self.sounds["grapple"] = create_grapple_sfx()
        self.sounds["thruster"] = create_thruster_sfx()
        self.sounds["teleport"] = create_teleport_sfx()
        self.sounds["slide"] = create_slide_sfx()
        self.sounds["bounce"] = create_bounce_sfx()
        
        # Progression, Rewards & Health (11)
        self.sounds["coin"] = create_coin_sfx()
        self.sounds["powerup"] = create_powerup_sfx()
        self.sounds["level_up"] = create_level_up_sfx()
        self.sounds["heal"] = create_heal_sfx()
        self.sounds["hurt"] = create_hurt_sfx()
        self.sounds["chest_open"] = create_chest_open_sfx()
        self.sounds["craft"] = create_craft_sfx()
        self.sounds["debuff"] = create_debuff_sfx()
        self.sounds["gem"] = create_gem_sfx()
        self.sounds["revive"] = create_revive_sfx()
        self.sounds["death"] = create_death_sfx()
        
        # User Interface & Signals (11)
        self.sounds["click"] = create_click_sfx()
        self.sounds["select"] = create_select_sfx()
        self.sounds["cancel"] = create_cancel_sfx()
        self.sounds["error"] = create_error_sfx()
        self.sounds["alert"] = create_alert_sfx()
        self.sounds["confirm"] = create_confirm_sfx()
        self.sounds["pause"] = create_pause_sfx()
        self.sounds["typewriter"] = create_typewriter_sfx()
        self.sounds["notification"] = create_notification_sfx()
        self.sounds["sonar_ping"] = create_sonar_ping_sfx()
        self.sounds["countdown"] = create_countdown_sfx()
        
        self.is_initialized = True

    def register(self, name: str, sound: Sound):
        """Registers or replaces a custom sound in the cache."""
        self.sounds[name] = sound

    def has(self, name: str) -> bool:
        """Returns True if the specified sound name (or alias) is registered in the cache."""
        if name in self.sounds:
            return True
        mapped = self.aliases.get(name)
        return mapped in self.sounds if mapped else False

    def count(self) -> int:
        """Returns the total number of cached sound effects."""
        return len(self.sounds)

    def play(self, name: str, volume: float = 1.0):
        """Plays a sound by name (or alias) with optional volume scaling."""
        snd = self.sounds.get(name)
        if not snd:
            mapped = self.aliases.get(name)
            if mapped:
                snd = self.sounds.get(mapped)
        if snd:
            set_sound_volume(snd, volume)
            play_sound(snd)

    def get(self, name: str) -> Sound:
        """Retrieves the Raylib Sound object directly."""
        snd = self.sounds.get(name)
        if not snd:
            mapped = self.aliases.get(name)
            if mapped:
                snd = self.sounds.get(mapped)
        return snd

    def unload_all(self):
        """
        Frees all cached sounds from memory.
        Guards against double-free if any sound is registered under multiple names.
        """
        unloaded_ids = set()
        for snd in self.sounds.values():
            snd_id = id(snd)
            if snd_id not in unloaded_ids:
                unload_sound(snd)
                unloaded_ids.add(snd_id)
        self.sounds.clear()
        self.is_initialized = False
