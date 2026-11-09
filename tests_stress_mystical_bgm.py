# -*- coding: utf-8 -*-
"""
tests_stress_mystical_bgm.py
============================
Empirical Adversarial Stress Test Suite for the 4 Mystical Procedural BGM Tracks:
  1. assets/audio/BGM/mystical/cosmic_mystery.py
  2. assets/audio/BGM/mystical/astral_sanctuary.py
  3. assets/audio/BGM/mystical/ancient_runestone.py
  4. assets/audio/BGM/mystical/crystal_caverns.py

Stress Test Dimensions:
  1. Long-duration stream update (120 consecutive frames per track with aggressive GC cycles).
  2. Signal richness & spectral analysis (RMS power, DC offset, peak clamping, frequency bands).
  3. Concurrent multi-track instantiation (all 4 tracks co-existing in RAM with stream switching).
"""

import sys
import os
import gc
import time
import struct
import math
import numpy as np
import psutil

# Enforce zero bytecode generation
sys.dont_write_bytecode = True

# Add workspace root to sys.path
REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

from pyray import *
from utils import *
import struct as py_struct

import assets.audio.BGM.mystical.cosmic_mystery as cosmic_mod
import assets.audio.BGM.mystical.astral_sanctuary as astral_mod
import assets.audio.BGM.mystical.ancient_runestone as runestone_mod
import assets.audio.BGM.mystical.crystal_caverns as caverns_mod

TRACK_SPECS = [
    {
        "id": "bgm_cosmic_mystery",
        "name": "Cosmic Mystery",
        "module": cosmic_mod,
        "generator_name": "generate_mystery_track",
        "expected_samples": 962182,
        "max_pcm_ceiling": 26000,
        "min_pcm_floor": -26000,
        "tempo": 88.0,
    },
    {
        "id": "bgm_mystical_astral_sanctuary",
        "name": "Astral Sanctuary",
        "module": astral_mod,
        "generator_name": "create_astral_sanctuary_bgm",
        "expected_samples": 1032585,
        "max_pcm_ceiling": 26000,
        "min_pcm_floor": -26000,
        "tempo": 82.0,
    },
    {
        "id": "bgm_mystical_ancient_runestone",
        "name": "Ancient Runestone",
        "module": runestone_mod,
        "generator_name": "create_ancient_runestone_bgm",
        "expected_samples": 984558,
        "max_pcm_ceiling": 26500,
        "min_pcm_floor": -26500,
        "tempo": 86.0,
    },
    {
        "id": "bgm_mystical_crystal_caverns",
        "name": "Crystal Caverns",
        "module": caverns_mod,
        "generator_name": "create_crystal_caverns_bgm",
        "expected_samples": 940800,
        "max_pcm_ceiling": 26500,
        "min_pcm_floor": -26500,
        "tempo": 90.0,
    },
]


def parse_wav_samples(wav_bytes: bytes):
    """
    Parses a 44-byte RIFF/WAVE header and extracts raw 16-bit PCM samples.
    """
    assert len(wav_bytes) >= 44, "WAV header too short"
    riff, total_chunk_sz, wave = py_struct.unpack('<4sI4s', wav_bytes[0:12])
    assert riff == b'RIFF', f"Expected RIFF header, got {riff}"
    assert wave == b'WAVE', f"Expected WAVE format, got {wave}"

    fmt_id, fmt_sz, audio_fmt, channels, sample_rate, byte_rate, block_align, bits = py_struct.unpack(
        '<4sIHHIIHH', wav_bytes[12:36]
    )
    assert fmt_id == b'fmt ', f"Expected fmt chunk, got {fmt_id}"
    assert audio_fmt == 1, f"Expected PCM format (1), got {audio_fmt}"
    assert channels == 1, f"Expected mono (1 channel), got {channels}"
    assert sample_rate == 44100, f"Expected 44100 Hz, got {sample_rate}"
    assert bits == 16, f"Expected 16-bit PCM, got {bits}"

    data_id, data_sz = py_struct.unpack('<4sI', wav_bytes[36:44])
    assert data_id == b'data', f"Expected data chunk, got {data_id}"
    assert len(wav_bytes) - 44 == data_sz, f"Data size mismatch: header {data_sz} vs actual {len(wav_bytes)-44}"

    pcm_data = np.frombuffer(wav_bytes[44:], dtype=np.int16)
    return pcm_data, sample_rate


def test_signal_richness_and_acoustics():
    """
    Stress Test 2: Signal richness, spectral distribution, DC offset, and peak clamping.
    """
    print("\n" + "="*80)
    print("STRESS TEST 2: SIGNAL RICHNESS & SPECTRAL ANALYSIS")
    print("="*80)

    results = []
    init_audio_device()

    try:
        for spec in TRACK_SPECS:
            name = spec["name"]
            mod = spec["module"]
            gen_fn = getattr(mod, spec["generator_name"])

            print(f"\n--- Analyzing Track: {name} ({spec['id']}) ---")
            music = gen_fn()
            music_id = id(music)

            # Check buffer pinning in module table
            assert music_id in mod._ACTIVE_BUFFERS, f"Buffer for {name} was NOT pinned in _ACTIVE_BUFFERS!"
            wav_bytes = mod._ACTIVE_BUFFERS[music_id]

            pcm_samples, sr = parse_wav_samples(wav_bytes)
            num_samples = len(pcm_samples)
            print(f"  * Sample count: {num_samples:,} (Expected: {spec['expected_samples']:,})")
            assert num_samples == spec["expected_samples"], (
                f"Sample count mismatch for {name}: {num_samples} != {spec['expected_samples']}"
            )

            # Range & Clamping Checks
            min_val = int(np.min(pcm_samples))
            max_val = int(np.max(pcm_samples))
            abs_peak = int(np.max(np.abs(pcm_samples)))
            print(f"  * Peak Amplitude: {abs_peak:,} (Min: {min_val}, Max: {max_val})")
            print(f"  * Clamping ceiling: [{-spec['max_pcm_ceiling']}, {spec['max_pcm_ceiling']}]")

            assert min_val >= spec["min_pcm_floor"], (
                f"Clamping violation: min value {min_val} < floor {spec['min_pcm_floor']}"
            )
            assert max_val <= spec["max_pcm_ceiling"], (
                f"Clamping violation: max value {max_val} > ceiling {spec['max_pcm_ceiling']}"
            )

            # DC Offset Analysis
            dc_offset = float(np.mean(pcm_samples))
            normalized_dc = abs(dc_offset) / 32767.0
            print(f"  * DC Offset: {dc_offset:.4f} samples (Normalized: {normalized_dc:.6f})")
            assert normalized_dc < 0.005, (
                f"Excessive DC offset detected in {name}: {normalized_dc:.6f} >= 0.005"
            )

            # RMS Power Analysis
            float_samples = pcm_samples.astype(np.float64) / 32767.0
            rms = float(np.sqrt(np.mean(float_samples ** 2)))
            rms_db = 20.0 * math.log10(rms) if rms > 0 else -999.0
            crest_factor = (abs_peak / 32767.0) / rms if rms > 0 else 0.0
            crest_factor_db = 20.0 * math.log10(crest_factor) if crest_factor > 0 else 0.0

            print(f"  * RMS Power: {rms:.4f} ({rms_db:.2f} dBFS)")
            print(f"  * Crest Factor: {crest_factor:.2f} ({crest_factor_db:.2f} dB)")

            # Reject flat silence (RMS < 0.05) or clipped blocks (RMS > 0.80)
            assert rms >= 0.05, f"Audio signal too faint or silent! RMS = {rms:.4f} < 0.05"
            assert rms <= 0.60, f"Audio signal excessively loud/compressed! RMS = {rms:.4f} > 0.60"

            # Spectral Frequency Band Analysis (FFT)
            fft_mag = np.abs(np.fft.rfft(float_samples))
            freqs = np.fft.rfftfreq(num_samples, d=1.0/sr)
            power_spectrum = fft_mag ** 2
            total_power = float(np.sum(power_spectrum))

            def band_energy(f_low, f_high):
                mask = (freqs >= f_low) & (freqs < f_high)
                return float(np.sum(power_spectrum[mask])) / total_power * 100.0

            sub_bass_pct = band_energy(20, 80)
            bass_pct = band_energy(80, 250)
            low_mid_pct = band_energy(250, 1000)
            high_mid_pct = band_energy(1000, 4000)
            presence_pct = band_energy(4000, 12000)

            print(f"  * Frequency Energy Distribution:")
            print(f"      Sub-Bass (20-80 Hz)    : {sub_bass_pct:5.2f}%")
            print(f"      Bass     (80-250 Hz)   : {bass_pct:5.2f}%")
            print(f"      Low-Mids (250-1000 Hz) : {low_mid_pct:5.2f}%")
            print(f"      High-Mids(1000-4000 Hz): {high_mid_pct:5.2f}%")
            print(f"      Presence (4000-12000Hz): {presence_pct:5.2f}%")

            # Check that audio has non-trivial energy across spectrum
            # Cosmic Mystery is an ambient zero-G sub-drone piece where sub-bass is prominent
            assert (sub_bass_pct + bass_pct + low_mid_pct + high_mid_pct) > 90.0, f"Abnormal spectral energy in {name}!"
            assert total_power > 0.0, f"Zero power spectrum in {name}!"

            # Unload track and verify buffer is unpinned
            mod.unload_bgm(music)
            assert music_id not in mod._ACTIVE_BUFFERS, f"Buffer {music_id} not purged from _ACTIVE_BUFFERS!"

            results.append({
                "name": name,
                "samples": num_samples,
                "peak": abs_peak,
                "rms_db": rms_db,
                "dc_offset": dc_offset,
                "sub_bass_pct": sub_bass_pct,
                "bass_pct": bass_pct,
                "low_mid_pct": low_mid_pct,
                "high_mid_pct": high_mid_pct,
                "presence_pct": presence_pct,
            })
    finally:
        close_audio_device()

    print("\n[PASS] Stress Test 2 (Signal Richness & Acoustics) completed successfully.")
    return results


def test_long_duration_streaming_with_gc_stress():
    """
    Stress Test 1: 120 consecutive frames of update_bgm() per track under aggressive GC pressure.
    """
    print("\n" + "="*80)
    print("STRESS TEST 1: LONG-DURATION STREAM UPDATE & GC BUFFER PINNING")
    print("="*80)

    for spec in TRACK_SPECS:
        name = spec["name"]
        mod = spec["module"]
        gen_fn = getattr(mod, spec["generator_name"])

        print(f"\n--- Testing Long Streaming (120 frames): {name} ---")
        init_audio_device()

        try:
            music = gen_fn()
            music_id = id(music)
            assert music_id in mod._ACTIVE_BUFFERS, f"Buffer not pinned for {name}!"

            # Start playback
            mod.play_bgm(music, volume=0.7, pitch=1.0, loop=True)
            assert is_music_stream_playing(music), f"Music stream {name} failed to start playing!"

            # 120 consecutive frames of streaming with periodic aggressive GC
            gc_cycles_run = 0
            start_time = time.time()

            for frame in range(1, 121):
                # Feed the streaming ring buffer
                mod.update_bgm(music)

                # Every 8 frames, trigger aggressive garbage collection & memory churn
                if frame % 8 == 0:
                    # Allocate temporary garbage to perturb heap
                    dummy_churn = [bytearray(1024 * 64) for _ in range(20)]
                    dummy_churn_dict = {f"k_{x}": list(range(100)) for x in range(50)}
                    del dummy_churn
                    del dummy_churn_dict
                    gc.collect(0)
                    gc.collect(1)
                    gc.collect(2)
                    gc_cycles_run += 1

                # Pace the frame simulation (~16.6ms / frame = 60 FPS)
                time.sleep(0.016)

            elapsed = time.time() - start_time
            print(f"  * Streamed 120 frames successfully over {elapsed:.2f}s ({gc_cycles_run} GC pressure cycles).")
            print(f"  * Stream status: Playing = {is_music_stream_playing(music)}")
            assert is_music_stream_playing(music), f"Stream stopped unexpectedly in {name}!"

            # Verify buffer pinning held memory intact
            assert music_id in mod._ACTIVE_BUFFERS, f"Buffer lost from _ACTIVE_BUFFERS during streaming!"
            wav_bytes = mod._ACTIVE_BUFFERS[music_id]
            assert len(wav_bytes) == spec["expected_samples"] * 2 + 44, "Pinned buffer corrupted during GC!"

            # Clean unload
            mod.stop_bgm(music)
            mod.unload_bgm(music)
            assert music_id not in mod._ACTIVE_BUFFERS, f"Buffer {music_id} failed to purge on unload!"

        finally:
            close_audio_device()

    print("\n[PASS] Stress Test 1 (Long-Duration Stream Update & GC Pinning) completed successfully.")


def test_concurrent_multi_track_instantiation():
    """
    Stress Test 3: Concurrent instantiation of all 4 tracks in memory with cross-track streaming.
    """
    print("\n" + "="*80)
    print("STRESS TEST 3: CONCURRENT 4-TRACK MEMORY INSTANTIATION")
    print("="*80)

    process = psutil.Process(os.getpid())
    gc.collect()
    mem_baseline = process.memory_info().rss / (1024 * 1024)
    print(f"  * Baseline Memory RSS: {mem_baseline:.2f} MB")

    init_audio_device()

    try:
        active_musics = []
        total_samples_resident = 0

        # Concurrently instantiate all 4 tracks
        print("  * Instantiating all 4 tracks simultaneously in RAM...")
        for spec in TRACK_SPECS:
            gen_fn = getattr(spec["module"], spec["generator_name"])
            music = gen_fn()
            active_musics.append((spec, music))
            total_samples_resident += spec["expected_samples"]
            print(f"    -> Instantiated {spec['name']} ({spec['expected_samples']:,} samples)")

        gc.collect()
        mem_loaded = process.memory_info().rss / (1024 * 1024)
        print(f"  * All 4 tracks resident. RSS: {mem_loaded:.2f} MB (Delta: +{mem_loaded - mem_baseline:.2f} MB)")
        print(f"  * Total active PCM samples in memory: {total_samples_resident:,} ({total_samples_resident * 2 / (1024*1024):.2f} MB PCM)")

        # Verify all 4 buffers are pinned in their respective modules
        for spec, music in active_musics:
            assert id(music) in spec["module"]._ACTIVE_BUFFERS, f"Pinning missing for {spec['name']}!"

        # Concurrent playback switching stress:
        # Cycle through tracks: play track k for 30 frames, pause, switch to track k+1
        print("  * Executing sequential track audition and seamless switching...")
        for i, (spec, music) in enumerate(active_musics):
            mod = spec["module"]
            print(f"    -> Playing Track {i+1}/4: {spec['name']} (30 frames)")
            mod.play_bgm(music, volume=0.6, pitch=1.0, loop=True)
            for _ in range(30):
                mod.update_bgm(music)
                time.sleep(0.010)
            mod.pause_bgm(music)

        # Simultaneous update stress: update all 4 streams in lock-step for 30 frames with GC
        print("  * Simultaneously updating all 4 streaming buffers for 30 frames under active GC churn...")
        # Resume all 4
        for spec, music in active_musics:
            spec["module"].resume_bgm(music)

        for frame in range(30):
            for spec, music in active_musics:
                spec["module"].update_bgm(music)
            if frame % 5 == 0:
                gc.collect(0)
                gc.collect(1)
            time.sleep(0.010)

        # Teardown in reverse order
        print("  * Unloading all 4 tracks in reverse order...")
        for spec, music in reversed(active_musics):
            mod = spec["module"]
            mod.stop_bgm(music)
            mod.unload_bgm(music)
            assert id(music) not in mod._ACTIVE_BUFFERS, f"Buffer not unpinned for {spec['name']}!"

        gc.collect()
        mem_unloaded = process.memory_info().rss / (1024 * 1024)
        print(f"  * Post-teardown RSS: {mem_unloaded:.2f} MB (Residual diff from baseline: {mem_unloaded - mem_baseline:+.2f} MB)")

    finally:
        close_audio_device()

    print("\n[PASS] Stress Test 3 (Concurrent Multi-Track Instantiation) completed successfully.")


if __name__ == "__main__":
    print("="*80)
    print("STARTING EMPIRICAL ADVERSARIAL STRESS TEST SUITE")
    print("="*80)

    t0 = time.time()
    spectral_results = test_signal_richness_and_acoustics()
    test_long_duration_streaming_with_gc_stress()
    test_concurrent_multi_track_instantiation()
    total_time = time.time() - t0

    print("\n" + "="*80)
    print(f"ALL EMPIRICAL STRESS TESTS PASSED WITH ZERO DEFECTS (Total runtime: {total_time:.2f}s)")
    print("="*80)
