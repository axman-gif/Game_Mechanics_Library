# -*- coding: utf-8 -*-
"""
Procedural Audio Synthesizer for Raylib Games
"""

import sys
sys.dont_write_bytecode = True

from .synth_sfx import (
    create_laser_sfx,
    create_explosion_sfx,
    create_hit_sfx,
    create_jump_sfx,
    create_coin_sfx,
    create_powerup_sfx,
    create_hurt_sfx,
    create_click_sfx,
    SoundLibrary
)

from .synth_music import (
    generate_action_track,
    generate_ambient_track,
    SynthMusicPlayer
)

__all__ = [
    # SFX
    "create_laser_sfx",
    "create_explosion_sfx",
    "create_hit_sfx",
    "create_jump_sfx",
    "create_coin_sfx",
    "create_powerup_sfx",
    "create_hurt_sfx",
    "create_click_sfx",
    "SoundLibrary",
    # Music
    "generate_action_track",
    "generate_ambient_track",
    "SynthMusicPlayer"
]

