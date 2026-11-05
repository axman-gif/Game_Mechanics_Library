# -*- coding: utf-8 -*-
"""
Central Procedural Assets Exporter (assets/__init__.py)
======================================================
Provides unified exports for procedural 3D primitive models, 2D vector sprites,
and the in-memory procedural audio engine (SoundLibrary & asset registries).
"""

import sys
sys.dont_write_bytecode = True

# Audio subsystem exports
from assets.audio.synth_sfx import SoundLibrary, SFX_REGISTRY, BGM_REGISTRY, scan_audio_assets

__all__ = [
    "SoundLibrary",
    "SFX_REGISTRY",
    "BGM_REGISTRY",
    "scan_audio_assets",
]

