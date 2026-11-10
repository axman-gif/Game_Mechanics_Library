# -*- coding: utf-8 -*-
"""
Backwards Compatibility Forwarder: assets/audio/asset_loader.py -> assets/asset_loader.py
========================================================================================
Central asset loader has moved to `assets/asset_loader.py`.
This module transparently re-exports all registries and functions.
"""
import sys
import os

sys.dont_write_bytecode = True

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

from assets.asset_loader import *

if __name__ == "__main__":
    smoke_test = "--smoke-test" in sys.argv
    print(f"=== Legacy Asset Loader Forwarder ===")
    print(f"  3D Models discovered : {len(models_3D)}")
    print(f"  2D Sprites discovered: {len(sprites_2D)}")
    print(f"  Audio cues discovered: {len(audio)} (SFX: {len(sfx)}, BGM: {len(bgm)})")
    if smoke_test:
        print("[PASS] legacy assets/audio/asset_loader.py --smoke-test passed.")
        sys.exit(0)
