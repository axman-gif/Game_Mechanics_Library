# -*- coding: utf-8 -*-
"""
Procedural Audio Discovery Registry & In-RAM Selective SoundLibrary
===================================================================
Module           : assets/audio/synth_sfx.py
Target Role      : Central Audio Registry & Selective In-RAM Resource Manager
Waveforms Loaded : Discovered modular procedural SFX (.wav PCM) & BGM (.wav streams)

Problem Solved:
  Eliminates memory bloat, unnecessary sound compilation, and massive monolithic
  audio scripts by dynamically scanning the modular asset category directories
  (`assets/audio/SFX/<category>/` and `assets/audio/BGM/<vibe>/`), indexing their file paths into
  in-memory registries (`SFX_REGISTRY` and `BGM_REGISTRY`), and selectively loading
  into RAM strictly the audio cues declared by each minigame.

How Dynamic Selective Loading Works:
  1. Discovery: On import or initialization, scan_audio_assets() crawls the SFX
     and BGM category folders and records paths in SFX_REGISTRY and BGM_REGISTRY.
  2. Declaration: In any minigame script, the developer or subagent declares strictly
     two lists specifying the required audio cues:
       SFXS = ["laser", "hit"]
       BGMS = ["synth_pulse"]
  3. Selective Loading: SoundLibrary.load(sfx=SFXS, bgm=BGMS) dynamically imports
     ONLY those specific Python files via importlib, calls their synthesis functions,
     and loads them into Raylib Sound and Music structs in audio memory.
  4. Memory Conservation: Unused sounds across the 90+ repository audio assets are
     never loaded, parsed, or synthesized into RAM.

C++ Architectural Equivalent (raylib.h):
  In a statically compiled C++ game engine, this architecture directly maps to an
  AudioResourceManager managing two hash maps:
    struct AudioResourceManager {
        std::unordered_map<std::string, Sound> sounds;
        std::unordered_map<std::string, Music> music;
        Music* active_music = nullptr;

        void LoadSFX(const std::string& name, const std::string& filepath);
        void LoadBGM(const std::string& name, const std::string& filepath);
        void Play(const std::string& name, float volume, float pitch, bool loop);
        void Stop(const std::string& name);
        void Pause(const std::string& name);
        void Resume(const std::string& name);
        void Update(); // Feeds active streaming buffers frame-by-frame
        void UnloadAll();
    };
"""

import sys
import os
import importlib.util
import struct as py_struct  # Aliased to prevent collision with pyray.struct
from typing import Dict, List, Optional, Any

# 1. Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# 2. Add repository root to search path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

# 3. Mandatory Raylib and utility imports
from pyray import *
from utils import *

# Canonical Audio Asset Directories
AUDIO_DIR = os.path.dirname(os.path.abspath(__file__))
SFX_DIR = os.path.join(AUDIO_DIR, "SFX")
BGM_DIR = os.path.join(AUDIO_DIR, "BGM")

# Global Discovery Registries (mapping cue_name -> absolute file path)
SFX_REGISTRY: Dict[str, str] = {}
BGM_REGISTRY: Dict[str, str] = {}


# ==============================================================================
# AUDIO DEVICE & BUFFER RESILIENCE HELPERS (Problems 3 & 5)
# ==============================================================================
def safe_init_audio_device() -> bool:
    """
    Defensively initializes Raylib's audio subsystem.
    Returns True if audio hardware is ready for synthesis/playback,
    or False if running in a headless / dummy environment without an audio device.
    """
    try:
        if not is_audio_device_ready():
            init_audio_device()
        return is_audio_device_ready()
    except Exception:
        return False


def pack_riff_wav_mono_16bit(sample_rate: int, raw_samples: list) -> bytes:
    """
    Packs signed 16-bit PCM integer samples (-32767 to 32767) into an in-memory
    canonical 44-byte RIFF/WAVE container.
    
    Guarantees:
      - Signed 16-bit clamping to prevent Raylib CFFI buffer overflow.
      - Exact 44-byte RIFF container struct layout: <4sI4s4sIHHIIHH4sI.
      - Returns immutable bytes pinned in Python memory during LoadWaveFromMemory().
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
# FILESYSTEM DISCOVERY ROUTINES
# ==============================================================================
def normalize_asset_key(filename: str) -> str:
    """
    Normalizes a python script filename into a clean audio cue identifier.
    Example: 'laser.py' -> 'laser', 'sfx_combat_laser.py' -> 'combat_laser'.
    """
    base = os.path.splitext(filename)[0].lower()
    if base.startswith("sfx_"):
        base = base[4:]
    elif base.startswith("bgm_"):
        base = base[4:]
    if base.endswith("_sfx"):
        base = base[:-4]
    elif base.endswith("_bgm"):
        base = base[:-4]
    return base


def scan_audio_assets() -> None:
    """
    Crawls assets/audio/SFX/ and assets/audio/BGM/ down to each Python script
    and records canonical paths in SFX_REGISTRY and BGM_REGISTRY.
    """
    global SFX_REGISTRY, BGM_REGISTRY
    SFX_REGISTRY.clear()
    BGM_REGISTRY.clear()

    # 1. Discover Sound Effects (SFX)
    if os.path.exists(SFX_DIR):
        for root, _, files in os.walk(SFX_DIR):
            for f in files:
                if f.endswith(".py") and not f.startswith("__") and not f.startswith("test_"):
                    full_path = os.path.abspath(os.path.join(root, f))
                    key = normalize_asset_key(f)
                    SFX_REGISTRY[key] = full_path
                    # Also register exact stem as secondary alias if different
                    stem = os.path.splitext(f)[0].lower()
                    if stem != key:
                        SFX_REGISTRY[stem] = full_path
                    # Also register category-relative alias (e.g. 'combat/laser')
                    rel_dir = os.path.relpath(root, SFX_DIR).replace("\\", "/").strip("./")
                    if rel_dir:
                        SFX_REGISTRY[f"{rel_dir}/{key}"] = full_path
                        if stem != key:
                            SFX_REGISTRY[f"{rel_dir}/{stem}"] = full_path

    # 2. Discover Background Music Tracks (BGM)
    if os.path.exists(BGM_DIR):
        for root, _, files in os.walk(BGM_DIR):
            for f in files:
                if f.endswith(".py") and not f.startswith("__") and not f.startswith("test_"):
                    full_path = os.path.abspath(os.path.join(root, f))
                    key = normalize_asset_key(f)
                    BGM_REGISTRY[key] = full_path
                    stem = os.path.splitext(f)[0].lower()
                    if stem != key:
                        BGM_REGISTRY[stem] = full_path
                    # Also register vibe-relative alias (e.g. 'energetic/synth_pulse')
                    rel_dir = os.path.relpath(root, BGM_DIR).replace("\\", "/").strip("./")
                    if rel_dir:
                        BGM_REGISTRY[f"{rel_dir}/{key}"] = full_path
                        if stem != key:
                            BGM_REGISTRY[f"{rel_dir}/{stem}"] = full_path


# Initialize registries upon module import
scan_audio_assets()


def get_sfx_path(name: str) -> Optional[str]:
    """Retrieves the absolute file path for a registered SFX cue."""
    key = normalize_asset_key(name)
    return SFX_REGISTRY.get(key) or SFX_REGISTRY.get(name.lower())


def get_bgm_path(name: str) -> Optional[str]:
    """Retrieves the absolute file path for a registered BGM track."""
    key = normalize_asset_key(name)
    return BGM_REGISTRY.get(key) or BGM_REGISTRY.get(name.lower())


def list_available_sfx() -> List[str]:
    """Returns a sorted list of all discovered sound effect identifiers."""
    return sorted(list(SFX_REGISTRY.keys()))


def list_available_bgm() -> List[str]:
    """Returns a sorted list of all discovered background music identifiers."""
    return sorted(list(BGM_REGISTRY.keys()))


# ==============================================================================
# DYNAMIC MODULE LOADER (Zero Bytecode In-RAM Import)
# ==============================================================================
def _import_audio_module(module_name: str, file_path: str) -> Any:
    """
    Dynamically loads an audio asset Python module from its file path
    without writing __pycache__ bytecode files to disk.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio asset script not found at path: {file_path}")

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Failed to create import spec for audio file: {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# ==============================================================================
# UNIFIED SELECTIVE IN-RAM SOUND LIBRARY
# ==============================================================================
class SoundLibrary:
    """
    Unified audio resource manager for procedural SFX (Sound) and BGM (Music).
    Loads into RAM ONLY the audio files explicitly specified in the minigame's
    SFXS and BGMS lists, preventing unnecessary memory consumption.
    """
    def __init__(self, sfx: Optional[List[str]] = None, bgm: Optional[List[str]] = None):
        self.sounds: Dict[str, Sound] = {}
        self.music: Dict[str, Music] = {}
        self.active_music: Optional[Music] = None
        self.loaded_modules: Dict[str, Any] = {}
        self.is_initialized: bool = True

        # If audio lists were passed into constructor, load them immediately
        if sfx or bgm:
            self.load(sfx=sfx, bgm=bgm)

    def load(self, sfx: Optional[List[str]] = None, bgm: Optional[List[str]] = None) -> None:
        """
        Dynamically imports and synthesizes strictly the requested SFX and BGM files.
        Accepts either cue identifiers (e.g. 'laser') or direct file paths.
        """
        # Ensure fresh registry state before loading
        if not SFX_REGISTRY or not BGM_REGISTRY:
            scan_audio_assets()

        # ----------------------------------------------------------------------
        # 1. Load Requested Sound Effects (SFX)
        # ----------------------------------------------------------------------
        if sfx:
            for item in sfx:
                if not item:
                    continue
                # Resolve file path: either a direct file path or lookup from registry
                resolved_path = None
                cue_name = item
                if os.path.isfile(item):
                    resolved_path = os.path.abspath(item)
                    cue_name = normalize_asset_key(os.path.basename(item))
                else:
                    cue_name = normalize_asset_key(item)
                    resolved_path = SFX_REGISTRY.get(cue_name) or SFX_REGISTRY.get(item.lower())

                if not resolved_path:
                    avail = ", ".join(list_available_sfx()) or "None"
                    raise FileNotFoundError(
                        f"[SoundLibrary Error] SFX '{item}' requested in minigame SFXS list "
                        f"was not found in assets/audio/SFX/<category>/.\nAvailable SFX: [{avail}]"
                    )

                if cue_name in self.sounds:
                    continue  # Already loaded

                mod_id = f"assets.audio.sfx_{cue_name}"
                mod = _import_audio_module(mod_id, resolved_path)
                self.loaded_modules[cue_name] = mod

                # Locate synthesis function: create_sfx or create_<name>_sfx
                sound_obj = None
                if hasattr(mod, "create_sfx"):
                    sound_obj = mod.create_sfx()
                else:
                    for attr_name in dir(mod):
                        if attr_name.startswith("create_") and attr_name.endswith("_sfx"):
                            func = getattr(mod, attr_name)
                            if callable(func):
                                sound_obj = func()
                                break

                if sound_obj is None:
                    raise AttributeError(
                        f"[SoundLibrary Error] SFX module '{resolved_path}' does not define "
                        f"a valid 'create_sfx()' or 'create_<name>_sfx()' synthesis function."
                    )

                self.sounds[cue_name] = sound_obj
                # Also store by original requested name for convenience
                if item != cue_name:
                    self.sounds[item] = sound_obj

        # ----------------------------------------------------------------------
        # 2. Load Requested Background Music (BGM)
        # ----------------------------------------------------------------------
        if bgm:
            for item in bgm:
                if not item:
                    continue
                resolved_path = None
                track_name = item
                if os.path.isfile(item):
                    resolved_path = os.path.abspath(item)
                    track_name = normalize_asset_key(os.path.basename(item))
                else:
                    track_name = normalize_asset_key(item)
                    resolved_path = BGM_REGISTRY.get(track_name) or BGM_REGISTRY.get(item.lower())

                if not resolved_path:
                    avail = ", ".join(list_available_bgm()) or "None"
                    raise FileNotFoundError(
                        f"[SoundLibrary Error] BGM '{item}' requested in minigame BGMS list "
                        f"was not found in assets/audio/BGM/<vibe>/.\nAvailable BGM: [{avail}]"
                    )

                if track_name in self.music:
                    continue  # Already loaded

                mod_id = f"assets.audio.bgm_{track_name}"
                mod = _import_audio_module(mod_id, resolved_path)
                self.loaded_modules[track_name] = mod

                # Locate synthesis function: create_bgm or create_<name>_bgm
                music_obj = None
                if hasattr(mod, "create_bgm"):
                    music_obj = mod.create_bgm()
                else:
                    for attr_name in dir(mod):
                        if attr_name.startswith("create_") and attr_name.endswith("_bgm"):
                            func = getattr(mod, attr_name)
                            if callable(func):
                                music_obj = func()
                                break

                if music_obj is None:
                    raise AttributeError(
                        f"[SoundLibrary Error] BGM module '{resolved_path}' does not define "
                        f"a valid 'create_bgm()' or 'create_<name>_bgm()' synthesis function."
                    )

                self.music[track_name] = music_obj
                if item != track_name:
                    self.music[item] = music_obj

    def init_defaults(self) -> None:
        """
        Lightweight fallback for launcher.py and legacy callers.
        Attempts to load standard UI sounds ('click', 'laser', 'synth_pulse') if present.
        """
        default_sfx = []
        for cue in ["click", "laser"]:
            if cue in SFX_REGISTRY:
                default_sfx.append(cue)
        default_bgm = []
        for track in ["synth_pulse"]:
            if track in BGM_REGISTRY:
                default_bgm.append(track)
        if default_sfx or default_bgm:
            self.load(sfx=default_sfx, bgm=default_bgm)

    def play(
        self,
        name: str,
        volume: float = 1.0,
        pitch: float = 1.0,
        loop: Optional[bool] = None
    ) -> None:
        """
        Unified playback for both SFX (Sound) and BGM (Music).
        - If 'name' is in self.sounds: plays as a one-shot Sound.
        - If 'name' is in self.music: streams as looping or one-shot Music.
        """
        if not is_audio_device_ready():
            return  # Headless / dummy safety guard
        vol = max(0.0, min(1.0, volume))
        pit = max(0.5, min(2.0, pitch))

        key = normalize_asset_key(name)
        if key in self.sounds or name in self.sounds:
            snd = self.sounds.get(key) or self.sounds.get(name)
            set_sound_volume(snd, vol)
            set_sound_pitch(snd, pit)
            play_sound(snd)
        elif key in self.music or name in self.music:
            mus = self.music.get(key) or self.music.get(name)
            set_music_volume(mus, vol)
            set_music_pitch(mus, pit)
            if loop is not None:
                mus.looping = loop
            else:
                mus.looping = True
            play_music_stream(mus)
            self.active_music = mus

    def stop(self, name: Optional[str] = None) -> None:
        """
        Stops playback of a specific cue or stops all active sounds and music.
        """
        if not is_audio_device_ready():
            return
        if name is not None:
            key = normalize_asset_key(name)
            if key in self.sounds or name in self.sounds:
                snd = self.sounds.get(key) or self.sounds.get(name)
                stop_sound(snd)
            elif key in self.music or name in self.music:
                mus = self.music.get(key) or self.music.get(name)
                stop_music_stream(mus)
                if self.active_music == mus:
                    self.active_music = None
        else:
            for snd in self.sounds.values():
                stop_sound(snd)
            for mus in self.music.values():
                stop_music_stream(mus)
            self.active_music = None

    def pause(self, name: str) -> None:
        """Pauses a playing sound or music track."""
        if not is_audio_device_ready():
            return
        key = normalize_asset_key(name)
        if key in self.sounds or name in self.sounds:
            snd = self.sounds.get(key) or self.sounds.get(name)
            pause_sound(snd)
        elif key in self.music or name in self.music:
            mus = self.music.get(key) or self.music.get(name)
            pause_music_stream(mus)

    def resume(self, name: str) -> None:
        """Resumes a paused sound or music track."""
        if not is_audio_device_ready():
            return
        key = normalize_asset_key(name)
        if key in self.sounds or name in self.sounds:
            snd = self.sounds.get(key) or self.sounds.get(name)
            resume_sound(snd)
        elif key in self.music or name in self.music:
            mus = self.music.get(key) or self.music.get(name)
            resume_music_stream(mus)

    def is_playing(self, name: str) -> bool:
        """Returns True if the specified sound or music stream is currently playing."""
        if not is_audio_device_ready():
            return False
        key = normalize_asset_key(name)
        if key in self.sounds or name in self.sounds:
            snd = self.sounds.get(key) or self.sounds.get(name)
            return is_sound_playing(snd)
        elif key in self.music or name in self.music:
            mus = self.music.get(key) or self.music.get(name)
            return is_music_stream_playing(mus)
        return False

    def set_volume(self, name: str, volume: float) -> None:
        """Adjusts the playback volume of a loaded sound or music stream."""
        if not is_audio_device_ready():
            return
        vol = max(0.0, min(1.0, volume))
        key = normalize_asset_key(name)
        if key in self.sounds or name in self.sounds:
            snd = self.sounds.get(key) or self.sounds.get(name)
            set_sound_volume(snd, vol)
        elif key in self.music or name in self.music:
            mus = self.music.get(key) or self.music.get(name)
            set_music_volume(mus, vol)

    def set_pitch(self, name: str, pitch: float) -> None:
        """Adjusts the playback pitch / speed of a loaded sound or music stream."""
        if not is_audio_device_ready():
            return
        pit = max(0.5, min(2.0, pitch))
        key = normalize_asset_key(name)
        if key in self.sounds or name in self.sounds:
            snd = self.sounds.get(key) or self.sounds.get(name)
            set_sound_pitch(snd, pit)
        elif key in self.music or name in self.music:
            mus = self.music.get(key) or self.music.get(name)
            set_music_pitch(mus, pit)

    def update(self) -> None:
        """
        Feeds streaming music buffers frame-by-frame.
        MUST be called once per frame in the minigame's update() loop.
        """
        if not is_audio_device_ready():
            return
        if self.active_music is not None:
            update_music_stream(self.active_music)

    def unload(self, name: str) -> None:
        """Frees an individual sound or music asset from memory."""
        if not is_audio_device_ready():
            self.sounds.pop(name, None)
            self.music.pop(name, None)
            return
        key = normalize_asset_key(name)
        if key in self.sounds or name in self.sounds:
            snd = self.sounds.pop(key, None) or self.sounds.pop(name, None)
            if snd:
                unload_sound(snd)
        elif key in self.music or name in self.music:
            mus = self.music.pop(key, None) or self.music.pop(name, None)
            if mus:
                if self.active_music == mus:
                    self.active_music = None
                unload_music_stream(mus)

    def unload_all(self) -> None:
        """
        Safely unloads all loaded Sound and Music handles from hardware memory.
        Guards against double-free if an asset was registered under multiple alias keys.
        """
        if not is_audio_device_ready():
            self.sounds.clear()
            self.music.clear()
            self.active_music = None
            return
        unloaded_sound_ids = set()
        for snd in list(self.sounds.values()):
            snd_id = id(snd)
            if snd_id not in unloaded_sound_ids:
                unload_sound(snd)
                unloaded_sound_ids.add(snd_id)
        self.sounds.clear()

        unloaded_music_ids = set()
        for mus in list(self.music.values()):
            mus_id = id(mus)
            if mus_id not in unloaded_music_ids:
                unload_music_stream(mus)
                unloaded_music_ids.add(mus_id)
        self.music.clear()
        self.active_music = None


# ==============================================================================
# STANDALONE REGISTRY INSPECTOR & SMOKE TEST
# ==============================================================================
def run_audio_registry_inspector(smoke_test: bool = False) -> None:
    """
    Launches an interactive visual inspector displaying all discovered SFX and BGM
    files with their paths, or runs an automated headless 3-frame smoke test.
    """
    screen_width = 1280
    screen_height = 720
    init_window(screen_width, screen_height, "Procedural Audio Registry & In-RAM Loader")
    set_target_fps(60)
    init_audio_device()

    # Discover and perform a test load of available assets
    scan_audio_assets()
    library = SoundLibrary()
    test_sfx = ["laser"] if "laser" in SFX_REGISTRY else []
    test_bgm = ["synth_pulse"] if "synth_pulse" in BGM_REGISTRY else []
    if test_sfx or test_bgm:
        library.load(sfx=test_sfx, bgm=test_bgm)
        if test_sfx:
            library.play(test_sfx[0], volume=0.7)

    frame_count = 0
    while not window_should_close():
        library.update()

        begin_drawing()
        clear_background(Color(12, 16, 26, 255))

        # Title (keeps region x=450..980 clear for settings bar)
        draw_text("PROCEDURAL AUDIO REGISTRY & IN-RAM LOADER", 24, 20, 20, RAYWHITE)
        draw_text(f"SFX Discovered: {len(SFX_REGISTRY)} | BGM Discovered: {len(BGM_REGISTRY)}", 24, 50, 13, SKYBLUE)

        # SFX Registry Column
        draw_rectangle(24, 90, 600, 560, Color(18, 24, 38, 255))
        draw_rectangle_lines(24, 90, 600, 560, Color(45, 60, 95, 255))
        draw_text(f"SFX ASSET REGISTRY ({len(SFX_REGISTRY)} files in assets/audio/SFX/)", 40, 106, 14, YELLOW)
        row_y = 136
        for name, path in list(SFX_REGISTRY.items())[:14]:
            rel = os.path.relpath(path, REPO_ROOT)
            draw_text(f"- {name.upper()}", 40, row_y, 13, RAYWHITE)
            draw_text(f"  {rel}", 180, row_y, 11, LIGHTGRAY)
            row_y += 26

        # BGM Registry Column
        draw_rectangle(650, 90, 600, 560, Color(18, 24, 38, 255))
        draw_rectangle_lines(650, 90, 600, 560, Color(45, 60, 95, 255))
        draw_text(f"BGM ASSET REGISTRY ({len(BGM_REGISTRY)} files in assets/audio/BGM/)", 666, 106, 14, ORANGE)
        row_y = 136
        for name, path in list(BGM_REGISTRY.items())[:14]:
            rel = os.path.relpath(path, REPO_ROOT)
            draw_text(f"- {name.upper()}", 666, row_y, 13, RAYWHITE)
            draw_text(f"  {rel}", 806, row_y, 11, LIGHTGRAY)
            row_y += 26

        # Top Bar Settings
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)
        end_drawing()

        frame_count += 1
        if smoke_test and frame_count >= 3:
            break

    library.unload_all()
    close_audio_device()
    close_window()


if __name__ == "__main__":
    is_smoke = "--smoke-test" in sys.argv
    run_audio_registry_inspector(smoke_test=is_smoke)
