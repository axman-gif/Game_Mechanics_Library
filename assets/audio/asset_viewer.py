# -*- coding: utf-8 -*-
"""
Backwards Compatibility Forwarder: assets/audio/asset_viewer.py -> assets/asset_viewer.py
========================================================================================
Interactive asset viewer has moved to `assets/asset_viewer.py`.
This module transparently forwards execution to the canonical location.
"""
import sys
import os
import subprocess

sys.dont_write_bytecode = True

if __name__ == "__main__":
    canonical = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "asset_viewer.py"))
    cmd = [sys.executable, "-B", canonical] + sys.argv[1:]
    res = subprocess.run(cmd)
    sys.exit(res.returncode)

