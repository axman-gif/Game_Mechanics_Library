# -*- coding: utf-8 -*-
"""
Assets Module for Raylib Games
Exposes 3D primitive models, 2D primitive renderers, and procedural synth audio tools.
"""

import sys
sys.dont_write_bytecode = True

from .models_3d import (
    draw_humanoid_enemy_3d,
    draw_quadruped_beast_3d,
    draw_drone_enemy_3d,
    draw_turret_boss_3d,
    DEFAULT_HUMANOID_PALETTE,
    DEFAULT_BEAST_PALETTE,
    DEFAULT_DRONE_PALETTE,
    DEFAULT_TURRET_PALETTE
)

from .sprites_2d import (
    draw_humanoid_enemy_2d,
    draw_slime_enemy_2d,
    draw_flying_drone_2d,
    draw_crawler_enemy_2d,
    DEFAULT_HUMANOID_2D_PALETTE,
    DEFAULT_SLIME_PALETTE,
    DEFAULT_FLYING_PALETTE,
    DEFAULT_CRAWLER_PALETTE
)

from .audio import (
    create_laser_sfx,
    create_explosion_sfx,
    create_hit_sfx,
    create_jump_sfx,
    create_coin_sfx,
    create_powerup_sfx,
    create_hurt_sfx,
    create_click_sfx,
    SoundLibrary,
    generate_action_track,
    generate_ambient_track,
    SynthMusicPlayer
)

__all__ = [
    # 3D
    "draw_humanoid_enemy_3d",
    "draw_quadruped_beast_3d",
    "draw_drone_enemy_3d",
    "draw_turret_boss_3d",
    "DEFAULT_HUMANOID_PALETTE",
    "DEFAULT_BEAST_PALETTE",
    "DEFAULT_DRONE_PALETTE",
    "DEFAULT_TURRET_PALETTE",
    # 2D
    "draw_humanoid_enemy_2d",
    "draw_slime_enemy_2d",
    "draw_flying_drone_2d",
    "draw_crawler_enemy_2d",
    "DEFAULT_HUMANOID_2D_PALETTE",
    "DEFAULT_SLIME_PALETTE",
    "DEFAULT_FLYING_PALETTE",
    "DEFAULT_CRAWLER_PALETTE",
    # Audio
    "create_laser_sfx",
    "create_explosion_sfx",
    "create_hit_sfx",
    "create_jump_sfx",
    "create_coin_sfx",
    "create_powerup_sfx",
    "create_hurt_sfx",
    "create_click_sfx",
    "SoundLibrary",
    "generate_action_track",
    "generate_ambient_track",
    "SynthMusicPlayer"
]

