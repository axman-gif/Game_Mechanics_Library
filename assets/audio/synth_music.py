# -*- coding: utf-8 -*-
"""
Procedural Background Music (BGM) Synthesizer for Raylib Python
---------------------------------------------------------------
Generates complete, loopable multi-voice chiptune, synthwave, orchestral, and ambient
soundtracks using mathematical waveform synthesis (basslines, chord pads, FM bells,
pulse-width modulation, arpeggios, and synthesized drum grooves).

Soundtrack Modes (12 Complete Loops):
  1.  Action / Combat      : Fast 126 BPM driving beat with bass and square-wave leads
  2.  Ambient / Exploration: Relaxed 84 BPM atmospheric chord pads with gentle melodic pulses
  3.  Boss Encounter       : Intense 140 BPM minor progression with syncopated bass and fast arpeggios
  4.  Stealth & Suspense   : Tense 96 BPM minimalist groove with heartbeat sub-bass and ticking hi-hats
  5.  Retro Arcade         : Bouncy 132 BPM NES-style chiptune with walking triangle bass and 8-bit leads
  6.  Victory / Shop       : Warm 116 BPM uplifting progression with organ bass and sparkling chimes
  7.  Cyberpunk Synthwave  : Driving 136 BPM neon E-minor loop with rolling 16th bass, kick/snare & PWM lead
  8.  Dark Dungeon         : Haunting 92 BPM E-Phrygian crypt loop with pedal drone, harpsichord & ghost bells
  9.  Puzzle & Logic Lab   : Thoughtful 104 BPM C-Lydian groove with plucked bass, FM Rhodes & marimba melody
  10. High-Octane Racing   : Turbo 152 BPM A-minor chase with octave-jumping bass, breakbeat & saw-square lead
  11. Fantasy Tavern       : Cheerful 112 BPM D-Dorian RPG town folk tune with oom-pah bass, lute & wooden flute
  12. Cosmic Mystery       : Ethereal 88 BPM F#-minor zero-G drift with LFO sub swell, glass pad & echo plucks

Includes SynthMusicPlayer for automatic seamless looping and volume control.
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
    unload_sound, play_sound, stop_sound, pause_sound, resume_sound,
    is_sound_playing, set_sound_volume, Sound
)

SAMPLE_RATE = 22050


def _build_music_sound(buffer_samples: list, sample_rate: int = SAMPLE_RATE) -> Sound:
    """
    Normalizes peak dynamics, packs to 16-bit Mono PCM WAV bytes, and returns a Raylib Sound.

    Novice / C++ Note:
      Multi-voice mixing sums several oscillators into a single floating-point buffer.
      Peak normalization scans the array for the maximum absolute amplitude and scales
      every sample to 95% of full scale ([-0.95, 0.95]) before int16_t quantization,
      guaranteeing consistent loudness across tracks without digital clipping.
    """
    peak = 0.001
    for val in buffer_samples:
        abs_val = abs(val)
        if abs_val > peak:
            peak = abs_val
    norm_gain = 0.95 / peak
    
    raw_frames = bytearray()
    for val in buffer_samples:
        clamped = max(-1.0, min(1.0, val * norm_gain))
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
# SOUNDTRACK GENERATORS (12 COMPLETE MULTI-VOICE LOOPS)
# ==============================================================================

def generate_action_track(bpm: float = 126.0) -> Sound:
    """
    Generates an 8-bar fast action/combat soundtrack loop.
    Contains:
      - Driving 4-on-the-floor synth bass
      - Dual-voice harmonic chord pads
      - 16th-note arpeggiated melodic lead
    """
    beat_sec = 60.0 / bpm
    bar_sec = beat_sec * 4.0
    
    # Progression: Dm - Bb - F - C (Classic heroic action loop)
    progression = [
        ([146.83, 174.61, 220.00], 73.42),   # Dm (D, F, A)
        ([116.54, 146.83, 174.61], 58.27),   # Bb (Bb, D, F)
        ([174.61, 220.00, 261.63], 87.31),   # F  (F, A, C)
        ([130.81, 164.81, 196.00], 65.41),   # C  (C, E, G)
        ([146.83, 174.61, 220.00], 73.42),   # Dm
        ([116.54, 146.83, 174.61], 58.27),   # Bb
        ([196.00, 233.08, 293.66], 98.00),   # Gm (G, Bb, D)
        ([164.81, 207.65, 246.94], 82.41),   # A7 (A, C#, E)
    ]
    
    total_bars = len(progression)
    total_sec = total_bars * bar_sec
    total_samples = int(total_sec * SAMPLE_RATE)
    buf = [0.0] * total_samples
    
    for bar_idx, (chord_notes, bass_freq) in enumerate(progression):
        b_start = int(bar_idx * bar_sec * SAMPLE_RATE)
        b_end = int((bar_idx + 1) * bar_sec * SAMPLE_RATE)
        
        # 1. Punchy Synth Bass (Quarter notes)
        q_len = int(beat_sec * SAMPLE_RATE)
        for q in range(4):
            q_s = b_start + q * q_len
            q_e = min(q_s + q_len, total_samples)
            for s in range(q_s, q_e):
                t_sub = (s - q_s) / SAMPLE_RATE
                env = math.exp(-4.2 * t_sub)
                buf[s] += 0.32 * math.sin(2.0 * math.pi * bass_freq * t_sub) * env
                
        # 2. Chord Pad
        for s in range(b_start, min(b_end, total_samples)):
            t_bar = (s - b_start) / SAMPLE_RATE
            env = math.sin(math.pi * t_bar / bar_sec)
            for f in chord_notes:
                buf[s] += 0.12 * math.sin(2.0 * math.pi * f * t_bar) * env
                
        # 3. 16th-note Arpeggio Lead
        step_len = int((beat_sec / 4.0) * SAMPLE_RATE)
        scale = chord_notes + [chord_notes[0] * 2.0, chord_notes[1] * 2.0]
        for step in range(16):
            s_start = b_start + step * step_len
            s_end = min(s_start + step_len, total_samples)
            note_freq = scale[step % len(scale)]
            for s in range(s_start, s_end):
                t_arp = (s - s_start) / SAMPLE_RATE
                env = math.exp(-9.0 * t_arp)
                sq = 1.0 if math.sin(2.0 * math.pi * note_freq * t_arp) > 0 else -1.0
                buf[s] += 0.18 * sq * env

    # Click-free crossfade at boundaries
    fade = int(0.04 * SAMPLE_RATE)
    for i in range(fade):
        factor = i / fade
        buf[i] *= factor
        buf[total_samples - 1 - i] *= factor
        
    return _build_music_sound(buf)


def generate_ambient_track(bpm: float = 84.0) -> Sound:
    """
    Generates a peaceful, atmospheric ambient exploration soundtrack.
    Slow sinusoidal chord pads with gentle harmonic resonance.
    """
    beat_sec = 60.0 / bpm
    bar_sec = beat_sec * 4.0
    
    # Progression: Am9 - Fmaj7 - Cmaj7 - Em
    progression = [
        ([220.00, 261.63, 329.63, 493.88], 55.0),   # Am9
        ([174.61, 220.00, 261.63, 329.63], 43.65),  # Fmaj7
        ([261.63, 329.63, 392.00, 493.88], 65.41),  # Cmaj7
        ([164.81, 196.00, 246.94, 293.66], 41.20)   # Em
    ]
    
    total_bars = len(progression)
    total_sec = total_bars * bar_sec
    total_samples = int(total_sec * SAMPLE_RATE)
    buf = [0.0] * total_samples
    
    for bar_idx, (chord_notes, bass_freq) in enumerate(progression):
        b_start = int(bar_idx * bar_sec * SAMPLE_RATE)
        b_end = int((bar_idx + 1) * bar_sec * SAMPLE_RATE)
        
        # Sub drone bass
        for s in range(b_start, min(b_end, total_samples)):
            t_bar = (s - b_start) / SAMPLE_RATE
            env = math.sin(math.pi * t_bar / bar_sec)
            buf[s] += 0.35 * math.sin(2.0 * math.pi * bass_freq * t_bar) * env
            
            # Shimmering chord pad
            for f in chord_notes:
                buf[s] += 0.10 * math.sin(2.0 * math.pi * f * t_bar) * env
                # Slight chorus detune
                buf[s] += 0.05 * math.sin(2.0 * math.pi * (f + 0.8) * t_bar) * env

    fade = int(0.08 * SAMPLE_RATE)
    for i in range(fade):
        factor = i / fade
        buf[i] *= factor
        buf[total_samples - 1 - i] *= factor
        
    return _build_music_sound(buf)


def generate_boss_track(bpm: float = 140.0) -> Sound:
    """
    Generates an intense, driving 8-bar boss encounter soundtrack loop.
    Contains:
      - Aggressive syncopated 8th-note synth bass with saw grit
      - Brassy minor chord pads with swell dynamics
      - Relentless high-tension 16th-note arpeggios
    """
    beat_sec = 60.0 / bpm
    bar_sec = beat_sec * 4.0
    
    # Progression: Cm - Ab - Fm - G7 (Dramatic, high-stakes combat)
    progression = [
        ([130.81, 155.56, 196.00], 65.41),  # Cm
        ([103.83, 130.81, 155.56], 51.91),  # Ab
        ([174.61, 207.65, 261.63], 87.31),  # Fm
        ([196.00, 246.94, 293.66], 98.00),  # G7
        ([130.81, 155.56, 196.00], 65.41),  # Cm
        ([103.83, 130.81, 155.56], 51.91),  # Ab
        ([146.83, 174.61, 207.65], 73.42),  # Ddim
        ([196.00, 246.94, 293.66], 98.00),  # G7
    ]
    
    total_bars = len(progression)
    total_samples = int(total_bars * bar_sec * SAMPLE_RATE)
    buf = [0.0] * total_samples
    
    for bar_idx, (chord_notes, bass_freq) in enumerate(progression):
        b_start = int(bar_idx * bar_sec * SAMPLE_RATE)
        b_end = int((bar_idx + 1) * bar_sec * SAMPLE_RATE)
        
        # 1. Driving Syncopated Bass (8th notes with accents on 1, 4, 7)
        step_len = int((beat_sec / 2.0) * SAMPLE_RATE)
        for step in range(8):
            s_start = b_start + step * step_len
            s_end = min(s_start + step_len, total_samples)
            accent = 1.35 if step in (0, 3, 6) else 0.75
            phase = 0.0
            phase_step = 2.0 * math.pi * bass_freq / SAMPLE_RATE
            for s in range(s_start, s_end):
                t_sub = (s - s_start) / SAMPLE_RATE
                env = math.exp(-7.0 * t_sub)
                phase += phase_step
                sine = math.sin(phase)
                sq = 1.0 if sine > 0 else -1.0
                buf[s] += 0.35 * (0.6 * sine + 0.4 * sq) * env * accent
                
        # 2. Brassy Minor Chords with Swell
        for s in range(b_start, min(b_end, total_samples)):
            t_bar = (s - b_start) / SAMPLE_RATE
            env = math.sin(math.pi * t_bar / bar_sec)
            for f in chord_notes:
                phase = 2.0 * math.pi * f * t_bar
                sq = 1.0 if math.sin(phase) > 0 else -1.0
                buf[s] += 0.08 * (0.7 * math.sin(phase) + 0.3 * sq) * env
                
        # 3. High-Tension 16th-note Arpeggio Ostinato
        arp_len = int((beat_sec / 4.0) * SAMPLE_RATE)
        arp_scale = chord_notes + [chord_notes[0] * 2.0, chord_notes[1] * 2.0]
        for step in range(16):
            s_start = b_start + step * arp_len
            s_end = min(s_start + arp_len, total_samples)
            f_note = arp_scale[(step * 2) % len(arp_scale)]
            phase = 0.0
            phase_step = 2.0 * math.pi * f_note / SAMPLE_RATE
            for s in range(s_start, s_end):
                t_arp = (s - s_start) / SAMPLE_RATE
                env = math.exp(-10.0 * t_arp)
                phase += phase_step
                sq = 1.0 if math.sin(phase) > 0 else -1.0
                buf[s] += 0.16 * sq * env

    fade = int(0.04 * SAMPLE_RATE)
    for i in range(fade):
        factor = i / fade
        buf[i] *= factor
        buf[total_samples - 1 - i] *= factor
        
    return _build_music_sound(buf)


def generate_stealth_track(bpm: float = 96.0) -> Sound:
    """
    Generates a tense, atmospheric stealth and suspense soundtrack loop.
    Contains:
      - Low-frequency heartbeat sub-bass pulses on beats 1 and 2.5
      - 16th-note muted clock ticking hi-hats
      - Sparse, eerie harmonic chord pads in D minor
    """
    beat_sec = 60.0 / bpm
    bar_sec = beat_sec * 4.0
    
    # Progression: Tense modal progression in D minor
    progression = [
        ([146.83, 174.61, 220.00], 73.42),          # Dm
        ([146.83, 174.61, 220.00, 329.63], 73.42),   # Dm9
        ([146.83, 174.61, 233.08], 58.27),          # Bb/D
        ([138.59, 174.61, 220.00], 69.30),          # A7/C#
        ([146.83, 174.61, 220.00], 73.42),          # Dm
        ([146.83, 174.61, 207.65], 73.42),          # Ddim
        ([116.54, 146.83, 174.61], 58.27),          # Bb
        ([138.59, 164.81, 220.00], 69.30),          # A7
    ]
    
    total_bars = len(progression)
    total_samples = int(total_bars * bar_sec * SAMPLE_RATE)
    buf = [0.0] * total_samples
    
    for bar_idx, (chord_notes, bass_freq) in enumerate(progression):
        b_start = int(bar_idx * bar_sec * SAMPLE_RATE)
        b_end = int((bar_idx + 1) * bar_sec * SAMPLE_RATE)
        
        # 1. Heartbeat Sub-Bass Pulse (beats 0 and 2.5)
        pulse_len = int(beat_sec * SAMPLE_RATE)
        for p_beat in (0.0, 2.5):
            p_s = b_start + int(p_beat * pulse_len)
            p_e = min(p_s + pulse_len, total_samples)
            phase = 0.0
            phase_step = 2.0 * math.pi * bass_freq / SAMPLE_RATE
            for s in range(p_s, p_e):
                t_sub = (s - p_s) / SAMPLE_RATE
                env = math.exp(-7.0 * t_sub)
                phase += phase_step
                buf[s] += 0.40 * math.sin(phase) * env
                
        # 2. Ticking Hi-Hats (16th notes)
        tick_len = int((beat_sec / 4.0) * SAMPLE_RATE)
        for t_step in range(16):
            t_s = b_start + t_step * tick_len
            t_e = min(t_s + int(0.02 * SAMPLE_RATE), total_samples)
            noise_val = 0.0
            for s in range(t_s, t_e):
                raw_noise = random.random() * 2.0 - 1.0
                noise_val += 0.4 * (raw_noise - noise_val)
                t_env = math.exp(-60.0 * (s - t_s) / SAMPLE_RATE)
                buf[s] += 0.08 * noise_val * t_env
                
        # 3. Eerie Ambient Pad
        for s in range(b_start, min(b_end, total_samples)):
            t_bar = (s - b_start) / SAMPLE_RATE
            env = math.sin(math.pi * t_bar / bar_sec)
            for f in chord_notes:
                phase = 2.0 * math.pi * f * t_bar
                buf[s] += 0.07 * math.sin(phase) * env

    fade = int(0.06 * SAMPLE_RATE)
    for i in range(fade):
        factor = i / fade
        buf[i] *= factor
        buf[total_samples - 1 - i] *= factor
        
    return _build_music_sound(buf)


def generate_retro_arcade_track(bpm: float = 132.0) -> Sound:
    """
    Generates a cheerful, upbeat 8-bar classic NES-style chiptune soundtrack loop.
    Contains:
      - Bouncy walking bassline synthesized with triangle waveforms
      - Catchy 50% duty cycle square wave melody lead
      - Warm chiptune chord accompaniment
    """
    beat_sec = 60.0 / bpm
    bar_sec = beat_sec * 4.0
    
    # Progression: F - G - Em - Am - Dm - G7 - C - C6 (Classic energetic chiptune progression)
    progression = [
        ([174.61, 220.00, 261.63], 87.31),   # F
        ([196.00, 246.94, 293.66], 98.00),   # G
        ([164.81, 196.00, 246.94], 82.41),   # Em
        ([220.00, 261.63, 329.63], 110.00),  # Am
        ([146.83, 174.61, 220.00], 73.42),   # Dm
        ([196.00, 246.94, 293.66], 98.00),   # G7
        ([130.81, 164.81, 196.00], 65.41),   # C
        ([130.81, 164.81, 220.00], 65.41),   # C6
    ]
    
    total_bars = len(progression)
    total_samples = int(total_bars * bar_sec * SAMPLE_RATE)
    buf = [0.0] * total_samples
    
    for bar_idx, (chord_notes, bass_freq) in enumerate(progression):
        b_start = int(bar_idx * bar_sec * SAMPLE_RATE)
        b_end = int((bar_idx + 1) * bar_sec * SAMPLE_RATE)
        
        # 1. Bouncy Triangle Bass (Walking 8th notes on alternating roots/fifths)
        step_len = int((beat_sec / 2.0) * SAMPLE_RATE)
        for step in range(8):
            s_start = b_start + step * step_len
            s_end = min(s_start + step_len, total_samples)
            f_bass = bass_freq if step % 2 == 0 else (bass_freq * 1.5)
            phase = 0.0
            phase_step = 2.0 * math.pi * f_bass / SAMPLE_RATE
            for s in range(s_start, s_end):
                t_sub = (s - s_start) / SAMPLE_RATE
                env = math.exp(-5.0 * t_sub)
                phase += phase_step
                norm_p = (phase / (2.0 * math.pi)) % 1.0
                tri = 2.0 * abs(2.0 * norm_p - 1.0) - 1.0
                buf[s] += 0.35 * tri * env
                
        # 2. Catchy 8-bit Square Wave Melody Lead (Quarter notes)
        melody_notes = [chord_notes[0] * 2.0, chord_notes[1] * 2.0, chord_notes[2] * 2.0, chord_notes[1] * 2.0]
        q_len = int(beat_sec * SAMPLE_RATE)
        for q in range(4):
            q_s = b_start + q * q_len
            q_e = min(q_s + q_len, total_samples)
            f_lead = melody_notes[q % len(melody_notes)]
            phase = 0.0
            phase_step = 2.0 * math.pi * f_lead / SAMPLE_RATE
            for s in range(q_s, q_e):
                t_q = (s - q_s) / SAMPLE_RATE
                env = math.exp(-4.0 * t_q)
                phase += phase_step
                sq = 1.0 if math.sin(phase) > 0 else -1.0
                buf[s] += 0.20 * sq * env

    fade = int(0.04 * SAMPLE_RATE)
    for i in range(fade):
        factor = i / fade
        buf[i] *= factor
        buf[total_samples - 1 - i] *= factor
        
    return _build_music_sound(buf)


def generate_victory_track(bpm: float = 116.0) -> Sound:
    """
    Generates a warm, uplifting 8-bar victory fanfare and RPG merchant shop loop.
    Contains:
      - Warm sinusoidal organ bass
      - Gentle chord pads with acoustic warmth
      - Sparkling pentatonic bell chimes
    """
    beat_sec = 60.0 / bpm
    bar_sec = beat_sec * 4.0
    
    # Progression: G - D - Em - C (Warm, celebratory major loop)
    progression = [
        ([196.00, 246.94, 293.66], 98.00),  # G
        ([146.83, 220.00, 293.66], 73.42),  # D
        ([164.81, 196.00, 246.94], 82.41),  # Em
        ([130.81, 164.81, 196.00], 65.41),  # C
        ([196.00, 246.94, 293.66], 98.00),  # G
        ([146.83, 220.00, 293.66], 73.42),  # D
        ([130.81, 164.81, 196.00], 65.41),  # C
        ([196.00, 246.94, 293.66], 98.00),  # G
    ]
    
    total_bars = len(progression)
    total_samples = int(total_bars * bar_sec * SAMPLE_RATE)
    buf = [0.0] * total_samples
    
    for bar_idx, (chord_notes, bass_freq) in enumerate(progression):
        b_start = int(bar_idx * bar_sec * SAMPLE_RATE)
        b_end = int((bar_idx + 1) * bar_sec * SAMPLE_RATE)
        
        # 1. Warm Organ Bass (Half notes)
        half_len = int(beat_sec * 2.0 * SAMPLE_RATE)
        for h in range(2):
            h_s = b_start + h * half_len
            h_e = min(h_s + half_len, total_samples)
            phase = 0.0
            phase_step = 2.0 * math.pi * bass_freq / SAMPLE_RATE
            for s in range(h_s, h_e):
                t_h = (s - h_s) / SAMPLE_RATE
                env = math.exp(-2.5 * t_h)
                phase += phase_step
                buf[s] += 0.32 * math.sin(phase) * env
                
        # 2. Warm Harmonic Pad
        for s in range(b_start, min(b_end, total_samples)):
            t_bar = (s - b_start) / SAMPLE_RATE
            env = math.sin(math.pi * t_bar / bar_sec)
            for f in chord_notes:
                phase = 2.0 * math.pi * f * t_bar
                buf[s] += 0.08 * math.sin(phase) * env
                
        # 3. Sparkling Pentatonic Chimes (Eighth notes)
        chime_step = int((beat_sec / 2.0) * SAMPLE_RATE)
        scale = chord_notes + [chord_notes[0] * 2.0]
        for c_idx in range(8):
            c_s = b_start + c_idx * chime_step
            c_e = min(c_s + chime_step, total_samples)
            f_note = scale[c_idx % len(scale)]
            phase = 0.0
            phase_step = 2.0 * math.pi * f_note / SAMPLE_RATE
            for s in range(c_s, c_e):
                t_c = (s - c_s) / SAMPLE_RATE
                env = math.exp(-6.0 * t_c)
                phase += phase_step
                buf[s] += 0.14 * math.sin(phase) * env

    fade = int(0.04 * SAMPLE_RATE)
    for i in range(fade):
        factor = i / fade
        buf[i] *= factor
        buf[total_samples - 1 - i] *= factor
        
    return _build_music_sound(buf)


def generate_cyberpunk_track(bpm: float = 136.0) -> Sound:
    """
    Generates an 8-bar Cyberpunk / Sci-Fi Synthwave soundtrack loop in E Minor.
    Contains:
      - Rolling 16th-note sawtooth/sub bassline with sidechain-style ducking envelope
      - Synthesized 4-on-the-floor electronic kick drum and backbeat noise snare
      - Pulse-Width Modulated (PWM) neon arpeggio lead
    """
    beat_sec = 60.0 / bpm
    bar_sec = beat_sec * 4.0

    # Progression: Em - C - G - D - Em - C - Am - B7
    progression = [
        ([164.81, 196.00, 246.94], 82.41),   # Em
        ([130.81, 164.81, 196.00], 65.41),   # C
        ([196.00, 246.94, 293.66], 98.00),   # G
        ([146.83, 185.00, 220.00], 73.42),   # D
        ([164.81, 196.00, 246.94], 82.41),   # Em
        ([130.81, 164.81, 196.00], 65.41),   # C
        ([220.00, 261.63, 329.63], 55.00),   # Am
        ([123.47, 185.00, 246.94], 61.74),   # B7
    ]

    total_bars = len(progression)
    total_samples = int(total_bars * bar_sec * SAMPLE_RATE)
    buf = [0.0] * total_samples

    for bar_idx, (chord_notes, bass_freq) in enumerate(progression):
        b_start = int(bar_idx * bar_sec * SAMPLE_RATE)

        # 1. Rolling 16th-note Synthwave Bass (with off-beat pumping accents)
        step_16 = int((beat_sec / 4.0) * SAMPLE_RATE)
        for step in range(16):
            s_start = b_start + step * step_16
            s_end = min(s_start + step_16, total_samples)
            # Sidechain ducking feel: quieter on downbeats (0, 4, 8, 12), louder on off-beats
            pump = 0.60 if (step % 4 == 0) else 1.15
            f_b = bass_freq * 2.0 if (step % 4 == 2) else bass_freq
            phase = 0.0
            phase_step = 2.0 * math.pi * f_b / SAMPLE_RATE
            for s in range(s_start, s_end):
                t_s = (s - s_start) / SAMPLE_RATE
                env = math.exp(-11.0 * t_s)
                phase += phase_step
                norm_p = (phase / (2.0 * math.pi)) % 1.0
                saw = 2.0 * norm_p - 1.0
                buf[s] += 0.28 * (0.55 * math.sin(phase) + 0.45 * saw) * env * pump

        # 2. Electronic Kick (beats 0, 1, 2, 3) & Snare (beats 1, 3)
        q_len = int(beat_sec * SAMPLE_RATE)
        for q in range(4):
            q_s = b_start + q * q_len
            kick_end = min(q_s + int(0.14 * SAMPLE_RATE), total_samples)
            k_phase = 0.0
            for s in range(q_s, kick_end):
                t_k = (s - q_s) / SAMPLE_RATE
                k_freq = 145.0 * math.exp(-24.0 * t_k) + 42.0
                k_phase += 2.0 * math.pi * k_freq / SAMPLE_RATE
                buf[s] += 0.30 * math.sin(k_phase) * math.exp(-12.0 * t_k)

            if q in (1, 3):
                snare_end = min(q_s + int(0.12 * SAMPLE_RATE), total_samples)
                noise_lp = 0.0
                for s in range(q_s, snare_end):
                    t_sn = (s - q_s) / SAMPLE_RATE
                    raw_n = random.random() * 2.0 - 1.0
                    noise_lp += 0.35 * (raw_n - noise_lp)
                    buf[s] += 0.16 * noise_lp * math.exp(-18.0 * t_sn)

        # 3. PWM Neon Lead Arpeggio (8th notes with dynamic duty cycle)
        step_8 = int((beat_sec / 2.0) * SAMPLE_RATE)
        lead_pattern = [
            chord_notes[0] * 2.0, chord_notes[1] * 2.0, chord_notes[2] * 2.0, chord_notes[1] * 2.0,
            chord_notes[2] * 2.0, chord_notes[0] * 4.0, chord_notes[2] * 2.0, chord_notes[1] * 2.0
        ]
        for step in range(8):
            s_start = b_start + step * step_8
            s_end = min(s_start + step_8, total_samples)
            f_lead = lead_pattern[step]
            phase = 0.0
            phase_step = 2.0 * math.pi * f_lead / SAMPLE_RATE
            for s in range(s_start, s_end):
                t_l = (s - s_start) / SAMPLE_RATE
                env = math.exp(-5.5 * t_l)
                phase += phase_step
                # Pulse-Width Modulation (duty cycle sweeps between 0.25 and 0.75)
                duty = 0.50 + 0.25 * math.sin(2.0 * math.pi * 4.0 * t_l)
                norm_p = (phase / (2.0 * math.pi)) % 1.0
                pwm = 1.0 if norm_p < duty else -1.0
                buf[s] += 0.15 * (0.65 * math.sin(phase) + 0.35 * pwm) * env

    fade = int(0.04 * SAMPLE_RATE)
    for i in range(fade):
        factor = i / fade
        buf[i] *= factor
        buf[total_samples - 1 - i] *= factor

    return _build_music_sound(buf)


def generate_dungeon_track(bpm: float = 92.0) -> Sound:
    """
    Generates a dark, mysterious 8-bar Dungeon / Crypt Crawl soundtrack loop.
    Contains:
      - Deep cathedral pedal sub-bass drone in E Phrygian / Harmonic Minor
      - Plucky dark harpsichord / lute 8th-note arpeggios
      - Haunting high-register ghost bell chimes with eerie vibrato
    """
    beat_sec = 60.0 / bpm
    bar_sec = beat_sec * 4.0

    # Progression: Em - Fmaj7 - Em - Dm - Am - Fmaj7 - Bdim - B7 (Phrygian / Dark Classical)
    progression = [
        ([164.81, 196.00, 246.94], 82.41),   # Em
        ([174.61, 220.00, 261.63], 87.31),   # Fmaj7 (Phrygian bII)
        ([164.81, 196.00, 246.94], 82.41),   # Em
        ([146.83, 174.61, 220.00], 73.42),   # Dm
        ([220.00, 261.63, 329.63], 55.00),   # Am
        ([174.61, 220.00, 261.63], 87.31),   # Fmaj7
        ([123.47, 174.61, 220.00], 61.74),   # Bm7b5
        ([123.47, 185.00, 246.94], 61.74),   # B7
    ]

    total_bars = len(progression)
    total_samples = int(total_bars * bar_sec * SAMPLE_RATE)
    buf = [0.0] * total_samples

    for bar_idx, (chord_notes, bass_freq) in enumerate(progression):
        b_start = int(bar_idx * bar_sec * SAMPLE_RATE)
        b_end = int((bar_idx + 1) * bar_sec * SAMPLE_RATE)

        # 1. Cathedral Pedal Drone (root + fifth sub-harmonic swell)
        for s in range(b_start, min(b_end, total_samples)):
            t_bar = (s - b_start) / SAMPLE_RATE
            env = math.sin(math.pi * t_bar / bar_sec)
            p_root = 2.0 * math.pi * bass_freq * t_bar
            p_fifth = 2.0 * math.pi * (bass_freq * 1.5) * t_bar
            buf[s] += (0.28 * math.sin(p_root) + 0.10 * math.sin(p_fifth)) * env

        # 2. Plucky Harpsichord / Dark Lute Arpeggios (8th notes)
        step_8 = int((beat_sec / 2.0) * SAMPLE_RATE)
        arp_seq = [
            chord_notes[0], chord_notes[1], chord_notes[2], chord_notes[0] * 2.0,
            chord_notes[2], chord_notes[1], chord_notes[2], chord_notes[1]
        ]
        for step in range(8):
            s_start = b_start + step * step_8
            s_end = min(s_start + step_8, total_samples)
            f_arp = arp_seq[step]
            phase = 0.0
            phase_step = 2.0 * math.pi * f_arp / SAMPLE_RATE
            for s in range(s_start, s_end):
                t_a = (s - s_start) / SAMPLE_RATE
                env = math.exp(-6.5 * t_a)
                phase += phase_step
                norm_p = (phase / (2.0 * math.pi)) % 1.0
                tri = 2.0 * abs(2.0 * norm_p - 1.0) - 1.0
                # Narrow 25% pulse wave adds harpsichord string pluck brightness
                pulse_25 = 1.0 if norm_p < 0.25 else -0.33
                buf[s] += 0.18 * (0.65 * tri + 0.35 * pulse_25) * env

        # 3. Haunting Ghost Bell (Half-note high bell on beats 1 and 3)
        half_len = int(beat_sec * 2.0 * SAMPLE_RATE)
        for h in range(2):
            h_s = b_start + h * half_len
            h_e = min(h_s + half_len, total_samples)
            f_bell = chord_notes[2 - h] * 4.0
            phase = 0.0
            vib_phase = 0.0
            for s in range(h_s, h_e):
                t_h = (s - h_s) / SAMPLE_RATE
                vib_phase += 2.0 * math.pi * 5.5 / SAMPLE_RATE
                inst_freq = f_bell + math.sin(vib_phase) * 4.5
                phase += 2.0 * math.pi * inst_freq / SAMPLE_RATE
                env = math.exp(-3.2 * t_h)
                buf[s] += 0.11 * math.sin(phase) * env

    fade = int(0.06 * SAMPLE_RATE)
    for i in range(fade):
        factor = i / fade
        buf[i] *= factor
        buf[total_samples - 1 - i] *= factor

    return _build_music_sound(buf)


def generate_puzzle_track(bpm: float = 104.0) -> Sound:
    """
    Generates a warm, intellectual 8-bar Puzzle & Logic Lab soundtrack loop.
    Contains:
      - Plucked acoustic-style upright bass on beats 1, 3, and 4.5
      - FM Electric Piano (Rhodes-style) jazz/Lydian chord voicings
      - Playful syncopated wooden marimba / kalimba mallet melody
    """
    beat_sec = 60.0 / bpm
    bar_sec = beat_sec * 4.0

    # Progression: Cmaj7 - D7 - Bm7 - Em7 - Am7 - D7 - Gmaj7 - G7 (Thoughtful jazz-pop loop)
    progression = [
        ([261.63, 329.63, 392.00, 493.88], 65.41),   # Cmaj7
        ([293.66, 369.99, 440.00, 523.25], 73.42),   # D7
        ([246.94, 293.66, 369.99, 440.00], 61.74),   # Bm7
        ([164.81, 196.00, 246.94, 293.66], 82.41),   # Em7
        ([220.00, 261.63, 329.63, 392.00], 55.00),   # Am7
        ([293.66, 369.99, 440.00, 523.25], 73.42),   # D7
        ([196.00, 246.94, 293.66, 369.99], 98.00),   # Gmaj7
        ([196.00, 246.94, 293.66, 349.23], 98.00),   # G7
    ]

    total_bars = len(progression)
    total_samples = int(total_bars * bar_sec * SAMPLE_RATE)
    buf = [0.0] * total_samples

    for bar_idx, (chord_notes, bass_freq) in enumerate(progression):
        b_start = int(bar_idx * bar_sec * SAMPLE_RATE)
        b_end = int((bar_idx + 1) * bar_sec * SAMPLE_RATE)

        # 1. Plucked Upright Bass (beats 0.0, 2.0, and a fifth walk-up on 3.5)
        q_len = int(beat_sec * SAMPLE_RATE)
        bass_hits = [(0.0, 1.8, bass_freq), (2.0, 1.4, bass_freq), (3.5, 0.5, bass_freq * 1.5)]
        for beat_pos, dur_beats, f_b in bass_hits:
            p_s = b_start + int(beat_pos * q_len)
            p_e = min(p_s + int(dur_beats * q_len), total_samples)
            phase = 0.0
            phase_step = 2.0 * math.pi * f_b / SAMPLE_RATE
            for s in range(p_s, p_e):
                t_b = (s - p_s) / SAMPLE_RATE
                env = math.exp(-4.5 * t_b)
                phase += phase_step
                # Fundamental + warm 2nd harmonic pluck
                buf[s] += 0.30 * (0.80 * math.sin(phase) + 0.20 * math.sin(phase * 2.0) * env) * env

        # 2. FM Electric Piano Pad (Rhodes-style warm chord with decaying tine bell)
        for s in range(b_start, min(b_end, total_samples)):
            t_bar = (s - b_start) / SAMPLE_RATE
            env_body = math.exp(-1.4 * t_bar) * math.sin(math.pi * min(1.0, t_bar / 0.03 if t_bar < 0.03 else 1.0 - (t_bar / bar_sec) * 0.5))
            env_tine = math.exp(-12.0 * t_bar)
            for f in chord_notes:
                p = 2.0 * math.pi * f * t_bar
                buf[s] += (0.065 * math.sin(p) * env_body + 0.025 * math.sin(p * 3.0) * env_tine)

        # 3. Syncopated Wooden Marimba / Kalimba Melody (16th-note grid steps 0, 3, 6, 8, 11, 14)
        step_16 = int((beat_sec / 4.0) * SAMPLE_RATE)
        marimba_steps = [0, 3, 6, 8, 11, 14]
        for m_idx, step in enumerate(marimba_steps):
            s_start = b_start + step * step_16
            s_end = min(s_start + step_16 * 2, total_samples)
            f_note = chord_notes[m_idx % len(chord_notes)] * 2.0
            phase = 0.0
            phase_step = 2.0 * math.pi * f_note / SAMPLE_RATE
            for s in range(s_start, s_end):
                t_m = (s - s_start) / SAMPLE_RATE
                env_main = math.exp(-9.5 * t_m)
                env_wood = math.exp(-38.0 * t_m)
                phase += phase_step
                # Marimba acoustics: fundamental sine + 4th harmonic wooden resonator strike
                mallet = 0.78 * math.sin(phase) * env_main + 0.22 * math.sin(phase * 4.0) * env_wood
                buf[s] += 0.20 * mallet

    fade = int(0.05 * SAMPLE_RATE)
    for i in range(fade):
        factor = i / fade
        buf[i] *= factor
        buf[total_samples - 1 - i] *= factor

    return _build_music_sound(buf)


def generate_racing_track(bpm: float = 152.0) -> Sound:
    """
    Generates a high-octane 8-bar Turbo Racing & Chase soundtrack loop at 152 BPM.
    Contains:
      - Galloping octave-jumping 8th-note bassline (OutRun / F-Zero arcade style)
      - Fast 16th-note hi-hat and snare breakbeat groove
      - Soaring saw-square heroic lead melody
    """
    beat_sec = 60.0 / bpm
    bar_sec = beat_sec * 4.0

    # Progression: Am - F - G - Em - Am - Dm - F - E7
    progression = [
        ([220.00, 261.63, 329.63], 55.00),   # Am
        ([174.61, 220.00, 261.63], 87.31),   # F
        ([196.00, 246.94, 293.66], 98.00),   # G
        ([164.81, 196.00, 246.94], 82.41),   # Em
        ([220.00, 261.63, 329.63], 55.00),   # Am
        ([146.83, 174.61, 220.00], 73.42),   # Dm
        ([174.61, 220.00, 261.63], 87.31),   # F
        ([164.81, 207.65, 246.94], 82.41),   # E7
    ]

    total_bars = len(progression)
    total_samples = int(total_bars * bar_sec * SAMPLE_RATE)
    buf = [0.0] * total_samples

    for bar_idx, (chord_notes, bass_freq) in enumerate(progression):
        b_start = int(bar_idx * bar_sec * SAMPLE_RATE)

        # 1. Octave-Jumping 8th-note Bassline (Root on downbeat, Octave on upbeat)
        step_8 = int((beat_sec / 2.0) * SAMPLE_RATE)
        for step in range(8):
            s_start = b_start + step * step_8
            s_end = min(s_start + step_8, total_samples)
            f_bass = bass_freq if (step % 2 == 0) else (bass_freq * 2.0)
            phase = 0.0
            phase_step = 2.0 * math.pi * f_bass / SAMPLE_RATE
            for s in range(s_start, s_end):
                t_b = (s - s_start) / SAMPLE_RATE
                env = math.exp(-7.5 * t_b)
                phase += phase_step
                sine = math.sin(phase)
                sq = 1.0 if sine > 0 else -1.0
                buf[s] += 0.30 * (0.60 * sine + 0.40 * sq) * env

        # 2. Breakbeat Hi-Hat & Snare Groove (16th notes)
        step_16 = int((beat_sec / 4.0) * SAMPLE_RATE)
        for step in range(16):
            s_start = b_start + step * step_16
            is_snare = (step in (4, 12, 15))
            hit_dur = 0.07 if is_snare else 0.025
            s_end = min(s_start + int(hit_dur * SAMPLE_RATE), total_samples)
            noise_val = 0.0
            for s in range(s_start, s_end):
                t_d = (s - s_start) / SAMPLE_RATE
                raw_n = random.random() * 2.0 - 1.0
                noise_val += (0.35 if is_snare else 0.65) * (raw_n - noise_val)
                decay = 24.0 if is_snare else 55.0
                amp = 0.15 if is_snare else 0.06
                buf[s] += amp * noise_val * math.exp(-decay * t_d)

        # 3. High-Speed Heroic Lead Ostinato (16th-note melodic drive)
        lead_scale = [
            chord_notes[0] * 2.0, chord_notes[1] * 2.0, chord_notes[2] * 2.0, chord_notes[0] * 4.0,
            chord_notes[2] * 2.0, chord_notes[1] * 2.0, chord_notes[2] * 2.0, chord_notes[1] * 2.0
        ]
        for step in range(16):
            s_start = b_start + step * step_16
            s_end = min(s_start + step_16, total_samples)
            f_note = lead_scale[step % len(lead_scale)]
            phase = 0.0
            phase_step = 2.0 * math.pi * f_note / SAMPLE_RATE
            for s in range(s_start, s_end):
                t_l = (s - s_start) / SAMPLE_RATE
                env = math.exp(-8.5 * t_l)
                phase += phase_step
                norm_p = (phase / (2.0 * math.pi)) % 1.0
                saw = 2.0 * norm_p - 1.0
                sq = 1.0 if norm_p < 0.5 else -1.0
                buf[s] += 0.16 * (0.55 * saw + 0.45 * sq) * env

    fade = int(0.04 * SAMPLE_RATE)
    for i in range(fade):
        factor = i / fade
        buf[i] *= factor
        buf[total_samples - 1 - i] *= factor

    return _build_music_sound(buf)


def generate_tavern_track(bpm: float = 112.0) -> Sound:
    """
    Generates a cheerful 8-bar Fantasy Tavern / RPG Town folk soundtrack loop.
    Contains:
      - Bouncy alternating root-fifth acoustic bass ("oom-pah" quarter notes)
      - Strummed acoustic lute / harp chord arpeggios
      - Warm wooden flute / recorder melody in D Dorian with breath envelope and vibrato
    """
    beat_sec = 60.0 / bpm
    bar_sec = beat_sec * 4.0

    # Progression: Dm - C - Dm - G - Dm - Am - Bb - A7 (Classic D Dorian Renaissance/RPG folk)
    progression = [
        ([146.83, 174.61, 220.00], 73.42),   # Dm
        ([130.81, 164.81, 196.00], 65.41),   # C
        ([146.83, 174.61, 220.00], 73.42),   # Dm
        ([196.00, 246.94, 293.66], 98.00),   # G (Dorian IV major)
        ([146.83, 174.61, 220.00], 73.42),   # Dm
        ([220.00, 261.63, 329.63], 55.00),   # Am
        ([116.54, 146.83, 174.61], 58.27),   # Bb
        ([138.59, 164.81, 220.00], 69.30),   # A7
    ]

    total_bars = len(progression)
    total_samples = int(total_bars * bar_sec * SAMPLE_RATE)
    buf = [0.0] * total_samples

    for bar_idx, (chord_notes, bass_freq) in enumerate(progression):
        b_start = int(bar_idx * bar_sec * SAMPLE_RATE)

        # 1. Bouncy "Oom-Pah" Root-Fifth Bass (Quarter notes)
        q_len = int(beat_sec * SAMPLE_RATE)
        for q in range(4):
            q_s = b_start + q * q_len
            q_e = min(q_s + q_len, total_samples)
            f_b = bass_freq if (q % 2 == 0) else (bass_freq * 1.5)
            phase = 0.0
            phase_step = 2.0 * math.pi * f_b / SAMPLE_RATE
            for s in range(q_s, q_e):
                t_q = (s - q_s) / SAMPLE_RATE
                env = math.exp(-5.0 * t_q)
                phase += phase_step
                norm_p = (phase / (2.0 * math.pi)) % 1.0
                tri = 2.0 * abs(2.0 * norm_p - 1.0) - 1.0
                buf[s] += 0.30 * (0.70 * math.sin(phase) + 0.30 * tri) * env

        # 2. Lute / Harp Plucked Accompaniment (8th notes)
        step_8 = int((beat_sec / 2.0) * SAMPLE_RATE)
        lute_seq = [
            chord_notes[0], chord_notes[1], chord_notes[2], chord_notes[1],
            chord_notes[0] * 2.0, chord_notes[2], chord_notes[1], chord_notes[2]
        ]
        for step in range(8):
            s_start = b_start + step * step_8
            s_end = min(s_start + step_8, total_samples)
            f_lute = lute_seq[step]
            phase = 0.0
            phase_step = 2.0 * math.pi * f_lute / SAMPLE_RATE
            for s in range(s_start, s_end):
                t_l = (s - s_start) / SAMPLE_RATE
                env = math.exp(-7.0 * t_l)
                phase += phase_step
                # Acoustic string timbre: fundamental + 2nd + 3rd harmonics
                pluck = 0.65 * math.sin(phase) + 0.25 * math.sin(phase * 2.0) + 0.10 * math.sin(phase * 3.0)
                buf[s] += 0.16 * pluck * env

        # 3. Wooden Flute / Recorder Melody (Quarter notes with soft breath attack & vibrato)
        flute_notes = [chord_notes[2] * 2.0, chord_notes[1] * 2.0, chord_notes[0] * 2.0, chord_notes[1] * 2.0]
        if bar_idx % 2 == 1:
            flute_notes = [chord_notes[1] * 2.0, chord_notes[2] * 2.0, chord_notes[0] * 4.0, chord_notes[2] * 2.0]
        for q in range(4):
            q_s = b_start + q * q_len
            q_e = min(q_s + q_len, total_samples)
            f_flute = flute_notes[q]
            phase = 0.0
            vib_phase = 0.0
            for s in range(q_s, q_e):
                t_f = (s - q_s) / SAMPLE_RATE
                vib_phase += 2.0 * math.pi * 5.2 / SAMPLE_RATE
                inst_freq = f_flute + math.sin(vib_phase) * 3.5 * min(1.0, t_f / 0.15)
                phase += 2.0 * math.pi * inst_freq / SAMPLE_RATE
                # Soft breath attack (40 ms fade-in) and smooth release
                attack = min(1.0, t_f / 0.04)
                decay = math.exp(-2.8 * t_f)
                buf[s] += 0.20 * (0.85 * math.sin(phase) + 0.15 * math.sin(phase * 2.0)) * attack * decay

    fade = int(0.04 * SAMPLE_RATE)
    for i in range(fade):
        factor = i / fade
        buf[i] *= factor
        buf[total_samples - 1 - i] *= factor

    return _build_music_sound(buf)


def generate_mystery_track(bpm: float = 88.0) -> Sound:
    """
    Generates an ethereal 8-bar Cosmic Mystery / Zero-G Space Drift soundtrack loop.
    Contains:
      - Deep cosmic sub-bass swell with slow LFO amplitude modulation
      - Shimmering dual-detuned glassy space pad in F# Minor / Lydian
      - Crystalline starlight 8th-note plucks with dotted-8th echo delay
    """
    beat_sec = 60.0 / bpm
    bar_sec = beat_sec * 4.0

    # Progression: F#m9 - Dmaj7 - Bm7 - C#7 - F#m9 - Dmaj7 - Esus4 - C#7
    progression = [
        ([185.00, 220.00, 277.18, 415.30], 46.25),   # F#m9
        ([146.83, 185.00, 220.00, 277.18], 73.42),   # Dmaj7
        ([246.94, 293.66, 369.99, 440.00], 61.74),   # Bm7
        ([138.59, 174.61, 207.65, 246.94], 69.30),   # C#7
        ([185.00, 220.00, 277.18, 415.30], 46.25),   # F#m9
        ([146.83, 185.00, 220.00, 277.18], 73.42),   # Dmaj7
        ([164.81, 220.00, 246.94, 329.63], 82.41),   # Esus4
        ([138.59, 174.61, 207.65, 246.94], 69.30),   # C#7
    ]

    total_bars = len(progression)
    total_samples = int(total_bars * bar_sec * SAMPLE_RATE)
    buf = [0.0] * total_samples

    for bar_idx, (chord_notes, bass_freq) in enumerate(progression):
        b_start = int(bar_idx * bar_sec * SAMPLE_RATE)
        b_end = int((bar_idx + 1) * bar_sec * SAMPLE_RATE)

        # 1. Cosmic Sub-Bass & Shimmering Glass Pad
        for s in range(b_start, min(b_end, total_samples)):
            t_bar = (s - b_start) / SAMPLE_RATE
            env = math.sin(math.pi * t_bar / bar_sec)
            lfo = 0.75 + 0.25 * math.sin(2.0 * math.pi * 1.5 * t_bar)
            buf[s] += 0.32 * math.sin(2.0 * math.pi * bass_freq * t_bar) * env * lfo

            for f in chord_notes:
                buf[s] += 0.075 * math.sin(2.0 * math.pi * f * t_bar) * env
                buf[s] += 0.045 * math.sin(2.0 * math.pi * (f * 1.003) * t_bar) * env

        # 2. Crystalline Starlight Plucks with Dotted-8th Delay Echo
        step_8 = int((beat_sec / 2.0) * SAMPLE_RATE)
        delay_offset = int((beat_sec * 0.75) * SAMPLE_RATE)  # Dotted 8th echo tap
        for step in range(8):
            s_start = b_start + step * step_8
            s_end = min(s_start + step_8, total_samples)
            f_star = chord_notes[(step * 3) % len(chord_notes)] * 2.0
            phase = 0.0
            phase_step = 2.0 * math.pi * f_star / SAMPLE_RATE
            for s in range(s_start, s_end):
                t_p = (s - s_start) / SAMPLE_RATE
                env = math.exp(-8.0 * t_p)
                phase += phase_step
                sample_val = 0.16 * (0.75 * math.sin(phase) + 0.25 * math.sin(phase * 2.0)) * env
                buf[s] += sample_val
                # Write attenuated delay echo into future buffer position (wrapping around loop)
                echo_idx = (s + delay_offset) % total_samples
                buf[echo_idx] += sample_val * 0.45

    fade = int(0.06 * SAMPLE_RATE)
    for i in range(fade):
        factor = i / fade
        buf[i] *= factor
        buf[total_samples - 1 - i] *= factor

    return _build_music_sound(buf)


# ==============================================================================
# MUSIC PLAYER (SEAMLESS LOOPING & CONTROL)
# ==============================================================================

class SynthMusicPlayer:
    """
    High-level background music manager.
    Plays a synthesized Sound track and automatically loops it when finished.
    """
    def __init__(self):
        self.current_sound = None
        self.volume = 0.65
        self.is_playing = False

    def load_track(self, sound_track: Sound):
        """Sets the active soundtrack."""
        if self.current_sound and self.is_playing:
            stop_sound(self.current_sound)
        self.current_sound = sound_track
        set_sound_volume(self.current_sound, self.volume)

    def play(self):
        """Starts playing the soundtrack."""
        if self.current_sound:
            play_sound(self.current_sound)
            self.is_playing = True

    def update(self):
        """Call once per frame in your game loop. Automatically restarts playback when track ends."""
        if self.is_playing and self.current_sound:
            if not is_sound_playing(self.current_sound):
                play_sound(self.current_sound)

    def pause(self):
        if self.current_sound and self.is_playing:
            pause_sound(self.current_sound)

    def resume(self):
        if self.current_sound:
            resume_sound(self.current_sound)

    def stop(self):
        if self.current_sound and self.is_playing:
            stop_sound(self.current_sound)
            self.is_playing = False

    def set_volume(self, volume: float):
        self.volume = max(0.0, min(1.0, volume))
        if self.current_sound:
            set_sound_volume(self.current_sound, self.volume)

    def unload(self):
        if self.current_sound:
            stop_sound(self.current_sound)
            unload_sound(self.current_sound)
            self.current_sound = None
            self.is_playing = False
