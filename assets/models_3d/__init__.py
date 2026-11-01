# -*- coding: utf-8 -*-
"""
3D Procedural Primitive Models for Raylib Games
"""

import sys
sys.dont_write_bytecode = True

from .humanoid import draw_humanoid_enemy_3d, DEFAULT_PALETTE as DEFAULT_HUMANOID_PALETTE
from .beast import draw_quadruped_beast_3d, DEFAULT_BEAST_PALETTE
from .drone import draw_drone_enemy_3d, DEFAULT_DRONE_PALETTE
from .turret import draw_turret_boss_3d, DEFAULT_TURRET_PALETTE

__all__ = [
    "draw_humanoid_enemy_3d",
    "draw_quadruped_beast_3d",
    "draw_drone_enemy_3d",
    "draw_turret_boss_3d",
    "DEFAULT_HUMANOID_PALETTE",
    "DEFAULT_BEAST_PALETTE",
    "DEFAULT_DRONE_PALETTE",
    "DEFAULT_TURRET_PALETTE"
]

