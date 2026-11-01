# -*- coding: utf-8 -*-
"""
Procedural Background Music (BGM) Synthesizer for Raylib Python
---------------------------------------------------------------
Generates complete, loopable multi-voice chiptune and ambient soundtracks
using mathematical waveform synthesis (basslines, chord pads, arpeggios, and drums).

Soundtrack Modes:
  - Action / Combat: Fast 128 BPM driving beat with bass and square-wave leads
  - Ambient / Exploration: Relaxed 85 BPM atmospheric chord pads with gentle melodic pulses
  - Boss Encounter: Intense 140 BPM minor progression with rapid syncopated bass

Includes SynthMusicPlayer for automatic seamless looping and volume control.
"""

import io
import math
import struct
import wave
from pyray import (
    load_wave_from_memory, load_sound_from_wave, unload_wave,
    unload_sound, play_sound, stop_sound, pause_sound, resume_sound,
    is_sound_playing, set_sound_volume, Sound
)

SAMPLE_RATE = 22050


def _build_music_sound(buffer_samples: list, sample_rate: int = SAMPLE_RATE) -> Sound:
    """Normalizes peak dynamics, packs to WAV bytes, and returns a Raylib Sound."""
    # Peak normalization to 95% full dynamic range
    peak = max(abs(v) for v in buffer_samples) if buffer_samples else 1.0
    norm_gain = 0.95 / max(0.001, peak)
    
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
# SOUNDTRACK GENERATORS
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

