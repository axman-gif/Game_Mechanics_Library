# -*- coding: utf-8 -*-
"""
2D Procedural Primitive Sprites for Raylib Games
"""

import sys
sys.dont_write_bytecode = True

from .humanoid_2d import draw_humanoid_enemy_2d, DEFAULT_HUMANOID_2D_PALETTE
from .creature_2d import (
    draw_slime_enemy_2d, DEFAULT_SLIME_PALETTE,
    draw_flying_drone_2d, DEFAULT_FLYING_PALETTE,
    draw_crawler_enemy_2d, DEFAULT_CRAWLER_PALETTE
)

__all__ = [
    "draw_humanoid_enemy_2d",
    "draw_slime_enemy_2d",
    "draw_flying_drone_2d",
    "draw_crawler_enemy_2d",
    "DEFAULT_HUMANOID_2D_PALETTE",
    "DEFAULT_SLIME_PALETTE",
    "DEFAULT_FLYING_PALETTE",
    "DEFAULT_CRAWLER_PALETTE"
]

