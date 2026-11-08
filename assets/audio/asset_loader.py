# -*- coding: utf-8 -*-
"""
Central Procedural Asset Discovery Registry & Dynamic Loader (asset_loader.py)
=============================================================================
Location: assets/audio/asset_loader.py
Role    : Universal Registry & Dynamic Asset Loader for 3D Models, 2D Sprites & Audio

Problem Solved:
  Eliminates static, bloated __init__.py import hubs and namespace collisions by
  dynamically scanning procedural asset directories (assets/models_3D,
  assets/sprites_2D, assets/audio/SFX, and assets/audio/BGM) on startup.
  
  Exposes central dictionary registries mapping:
    "file_stem (without .py)": "path/to/file.py"
  
  Craftsman subagents building minigames use these dictionaries and their keys
  to load procedural assets on demand without external art dependencies.

Dictionaries Provided:
  - models_3D : Procedural 3D primitive models (assets/models_3D/)
  - sprites_2D: Procedural 2D vector sprites (assets/sprites_2D/)
  - audio     : All procedural sound effects & music tracks (assets/audio/)
  - sfx       : Sound effects registry (assets/audio/SFX/)
  - bgm       : Background music tracks registry (assets/audio/BGM/)
"""

import sys
import os
import importlib.util
from typing import Dict, List, Optional, Any, Tuple

# 1. Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# 2. Add repository root to search path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

# 3. Mandatory Raylib and utility imports
from pyray import *
from utils import *

# 4. Canonical Asset Directories
ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
AUDIO_DIR = os.path.join(ASSETS_DIR, "audio")
MODELS_3D_DIR = os.path.join(ASSETS_DIR, "models_3D")
SPRITES_2D_DIR = os.path.join(ASSETS_DIR, "sprites_2D")
SFX_DIR = os.path.join(AUDIO_DIR, "SFX")
BGM_DIR = os.path.join(AUDIO_DIR, "BGM")

# ==============================================================================
# GLOBAL ASSET DICTIONARY REGISTRIES
# ==============================================================================
# Format: { "file_stem_without_py": "path/to/file.py" }
models_3D: Dict[str, str] = {}
sprites_2D: Dict[str, str] = {}
audio: Dict[str, str] = {}
sfx: Dict[str, str] = {}
bgm: Dict[str, str] = {}

# Internal cache for loaded Python modules
_LOADED_MODULES: Dict[str, Any] = {}


# ==============================================================================
# KEY NORMALIZATION & DISCOVERY
# ==============================================================================
def normalize_asset_stem(filename: str) -> str:
    """
    Extracts the clean identifier stem from a filename.
    Example: 'laser.py' -> 'laser', 'sfx_combat_laser.py' -> 'combat_laser'.
    """
    stem = os.path.splitext(filename)[0]
    return stem


def normalize_audio_cue(filename: str) -> str:
    """
    Normalizes audio file stems for convenient cue lookups.
    Example: 'sfx_combat_laser.py' -> 'combat_laser', 'laser.py' -> 'laser'.
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


def _clean_repo_path(full_path: str) -> str:
    """Returns a forward-slash normalized path relative to REPO_ROOT."""
    rel = os.path.relpath(full_path, REPO_ROOT)
    return rel.replace("\\", "/")


def scan_all_assets() -> None:
    """
    Crawls assets/models_3D, assets/sprites_2D, and assets/audio (SFX & BGM)
    and populates all central dictionary registries.
    """
    global models_3D, sprites_2D, audio, sfx, bgm
    models_3D.clear()
    sprites_2D.clear()
    audio.clear()
    sfx.clear()
    bgm.clear()

    # 1. Discover 3D Models (assets/models_3D/)
    if os.path.exists(MODELS_3D_DIR):
        for root, _, files in os.walk(MODELS_3D_DIR):
            for f in sorted(files):
                if f.endswith(".py") and not f.startswith("__") and not f.startswith("test_"):
                    full_path = os.path.abspath(os.path.join(root, f))
                    repo_path = _clean_repo_path(full_path)
                    stem = normalize_asset_stem(f)
                    models_3D[stem] = repo_path

    # 2. Discover 2D Sprites (assets/sprites_2D/)
    if os.path.exists(SPRITES_2D_DIR):
        for root, _, files in os.walk(SPRITES_2D_DIR):
            for f in sorted(files):
                if f.endswith(".py") and not f.startswith("__") and not f.startswith("test_"):
                    full_path = os.path.abspath(os.path.join(root, f))
                    repo_path = _clean_repo_path(full_path)
                    stem = normalize_asset_stem(f)
                    sprites_2D[stem] = repo_path

    # 3. Discover Audio (assets/audio/SFX/ and assets/audio/BGM/)
    # SFX
    if os.path.exists(SFX_DIR):
        for root, _, files in os.walk(SFX_DIR):
            for f in sorted(files):
                if f.endswith(".py") and not f.startswith("__") and not f.startswith("test_"):
                    full_path = os.path.abspath(os.path.join(root, f))
                    repo_path = _clean_repo_path(full_path)
                    stem = normalize_asset_stem(f)
                    cue = normalize_audio_cue(f)
                    sfx[stem] = repo_path
                    audio[stem] = repo_path
                    if cue != stem:
                        sfx[cue] = repo_path
                        audio[cue] = repo_path

    # BGM
    if os.path.exists(BGM_DIR):
        for root, _, files in os.walk(BGM_DIR):
            for f in sorted(files):
                if f.endswith(".py") and not f.startswith("__") and not f.startswith("test_"):
                    full_path = os.path.abspath(os.path.join(root, f))
                    repo_path = _clean_repo_path(full_path)
                    stem = normalize_asset_stem(f)
                    cue = normalize_audio_cue(f)
                    bgm[stem] = repo_path
                    audio[stem] = repo_path
                    if cue != stem:
                        bgm[cue] = repo_path
                        audio[cue] = repo_path


# Initialize registries upon module import
scan_all_assets()


# ==============================================================================
# DYNAMIC MODULE IMPORT UTILITIES (Used by Craftsmen Subagents)
# ==============================================================================
def resolve_asset_path(registry: Dict[str, str], key: str) -> Optional[str]:
    """
    Resolves the absolute filesystem path for an asset key from a dictionary registry.
    Accepts exact stem or normalized cue key.
    """
    rel_path = registry.get(key) or registry.get(key.lower())
    if not rel_path:
        return None
    if os.path.isabs(rel_path):
        return rel_path
    return os.path.abspath(os.path.join(REPO_ROOT, rel_path))


def import_asset_by_key(registry: Dict[str, str], key: str) -> Any:
    """
    Dynamically imports and returns the Python module for the given asset key
    from the specified dictionary registry (models_3D, sprites_2D, audio, sfx, bgm).
    
    Zero bytecode files are written (__pycache__ free).
    """
    abs_path = resolve_asset_path(registry, key)
    if not abs_path or not os.path.exists(abs_path):
        available = ", ".join(sorted(registry.keys())) or "None"
        raise FileNotFoundError(
            f"[asset_loader] Asset with key '{key}' was not found in registry.\n"
            f"Available keys: [{available}]"
        )

    if abs_path in _LOADED_MODULES:
        return _LOADED_MODULES[abs_path]

    module_name = f"assets_dynamic_{key}"
    spec = importlib.util.spec_from_file_location(module_name, abs_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"[asset_loader] Failed to load spec for asset: {abs_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    _LOADED_MODULES[abs_path] = module
    return module


def load_model_3d(key: str) -> Tuple[Any, Optional[dict]]:
    """
    Convenience loader for 3D procedural models.
    Returns: (draw_func, default_palette)
    """
    mod = import_asset_by_key(models_3D, key)
    draw_func = None
    palette = None

    for attr in dir(mod):
        if attr.startswith("draw_") and attr.endswith("_3d"):
            draw_func = getattr(mod, attr)
        elif attr.startswith("DEFAULT_") and attr.endswith("_PALETTE"):
            palette = getattr(mod, attr)

    if draw_func is None:
        raise AttributeError(f"[asset_loader] 3D Model '{key}' does not expose a draw_*_3d function.")
    return draw_func, palette


def load_sprite_2d(key: str) -> Tuple[Any, Optional[dict]]:
    """
    Convenience loader for 2D procedural sprites.
    Returns: (draw_func, default_palette)
    """
    mod = import_asset_by_key(sprites_2D, key)
    draw_func = None
    palette = None

    for attr in dir(mod):
        if attr.startswith("draw_") and attr.endswith("_2d"):
            draw_func = getattr(mod, attr)
        elif attr.startswith("DEFAULT_") and attr.endswith("_PALETTE"):
            palette = getattr(mod, attr)

    if draw_func is None:
        raise AttributeError(f"[asset_loader] 2D Sprite '{key}' does not expose a draw_*_2d function.")
    return draw_func, palette


# ==============================================================================
# AUDIO SUBSYSTEM EXPORTS & HEADLESS RESILIENCE
# ==============================================================================
from assets.audio.synth_sfx import (
    SoundLibrary,
    SFX_REGISTRY,
    BGM_REGISTRY,
    scan_audio_assets,
    safe_init_audio_device,
    pack_riff_wav_mono_16bit,
)

__all__ = [
    # Registries
    "models_3D",
    "sprites_2D",
    "audio",
    "sfx",
    "bgm",
    # Discovery & Dynamic Loaders
    "scan_all_assets",
    "resolve_asset_path",
    "import_asset_by_key",
    "load_model_3d",
    "load_sprite_2d",
    # Audio Runtime
    "SoundLibrary",
    "SFX_REGISTRY",
    "BGM_REGISTRY",
    "scan_audio_assets",
    "safe_init_audio_device",
    "pack_riff_wav_mono_16bit",
]


# ==============================================================================
# STANDALONE CLI TEST / VERIFICATION
# ==============================================================================
if __name__ == "__main__":
    smoke_test = "--smoke-test" in sys.argv
    print(f"=== Asset Loader Summary ===")
    print(f"  3D Models discovered : {len(models_3D)}")
    print(f"  2D Sprites discovered: {len(sprites_2D)}")
    print(f"  Audio cues discovered: {len(audio)} (SFX: {len(sfx)}, BGM: {len(bgm)})")
    
    if "laser" in audio:
        mod = import_asset_by_key(audio, "laser")
        print(f"  Successfully imported dynamic audio cue 'laser': {mod}")
    
    if smoke_test:
        print("[PASS] asset_loader.py --smoke-test passed.")
        sys.exit(0)

