# -*- coding: utf-8 -*-
"""
Utilities Module for Raylib Games
Exposes non-native collisions, spatial grids, AI steering, pathfinding, and game math helpers.
"""

import sys
sys.dont_write_bytecode = True

from .collisions import (
    Capsule2D,
    Capsule3D,
    OBB2D,
    closest_point_on_segment_2d,
    closest_point_on_segment_3d,
    closest_points_between_segments_2d,
    closest_points_between_segments_3d,
    check_collision_capsule_circle_2d,
    check_collision_capsules_2d,
    check_collision_capsule_sphere_3d,
    check_collision_capsules_3d,
    check_collision_obb_2d
)

from .spatial_grid import (
    SpatialGrid2D,
    SpatialGrid3D,
    TileGrid2D
)

from .ai_pursuit import (
    seek_2d,
    flee_2d,
    arrive_2d,
    predict_intercept_2d,
    wander_2d,
    seek_3d,
    predict_intercept_3d,
    has_line_of_sight_grid,
    find_path_astar,
    find_path_bfs
)

from .math_helpers import (
    clamp,
    safe_color,
    lerp,
    lerp_v2,
    lerp_v3,
    approach,
    damp,
    damp_v2,
    damp_v3,
    distance_2d,
    distance_3d,
    normalize_2d,
    normalize_3d,
    angle_to_vector_2d,
    vector_to_angle_2d,
    ease_in_quad,
    ease_out_quad,
    ease_in_out_quad,
    ease_out_bounce,
    ease_out_elastic,
    TraumaShake
)

from .ui_settings import (
    ui_settings,
    UISettingsManager,
    init_window,
    close_window,
    begin_drawing,
    end_drawing,
    begin_mode_2d,
    end_mode_2d,
    begin_mode_3d,
    end_mode_3d,
    begin_scissor_mode,
    end_scissor_mode,
    draw_text,
    draw_ui_settings_bar,
)

from .gamepad_input import (
    get_active_gamepad_id,
    is_any_gamepad_connected,
    get_active_gamepad_name,
    apply_radial_deadzone,
    get_gamepad_left_stick,
    get_gamepad_right_stick,
    is_gamepad_trigger_down,
    get_dual_move_2d,
    get_dual_look_2d,
    is_dual_primary_fire_down,
    is_dual_primary_fire_pressed,
    is_dual_secondary_fire_pressed,
    is_dual_jump_down,
    is_dual_jump_pressed,
    is_dual_dash_down,
    is_dual_dash_pressed,
    is_dual_xray_toggle_pressed,
    is_dual_pattern_toggle_pressed,
    is_dual_secondary_toggle_pressed,
    is_dual_reset_pressed,
    draw_gamepad_status_badge,
)

__all__ = [
    # Collisions
    "Capsule2D", "Capsule3D", "OBB2D",
    "closest_point_on_segment_2d", "closest_point_on_segment_3d",
    "closest_points_between_segments_2d", "closest_points_between_segments_3d",
    "check_collision_capsule_circle_2d", "check_collision_capsules_2d",
    "check_collision_capsule_sphere_3d", "check_collision_capsules_3d",
    "check_collision_obb_2d",
    # Spatial
    "SpatialGrid2D", "SpatialGrid3D", "TileGrid2D",
    # AI & Pathfinding
    "seek_2d", "flee_2d", "arrive_2d", "predict_intercept_2d", "wander_2d",
    "seek_3d", "predict_intercept_3d", "has_line_of_sight_grid",
    "find_path_astar", "find_path_bfs",
    # Math & Easing
    "clamp", "safe_color", "lerp", "lerp_v2", "lerp_v3", "approach",
    "damp", "damp_v2", "damp_v3", "distance_2d", "distance_3d",
    "normalize_2d", "normalize_3d", "angle_to_vector_2d", "vector_to_angle_2d",
    "ease_in_quad", "ease_out_quad", "ease_in_out_quad", "ease_out_bounce", "ease_out_elastic",
    "TraumaShake",
    # Global UI Settings, Font & Window Manager
    "ui_settings", "UISettingsManager",
    "init_window", "close_window", "begin_drawing", "end_drawing",
    "begin_mode_2d", "end_mode_2d", "begin_mode_3d", "end_mode_3d",
    "begin_scissor_mode", "end_scissor_mode",
    "draw_text", "draw_ui_settings_bar",
    # Simultaneous Keyboard/Mouse + Gamepad Input
    "get_active_gamepad_id", "is_any_gamepad_connected", "get_active_gamepad_name",
    "apply_radial_deadzone", "get_gamepad_left_stick", "get_gamepad_right_stick",
    "is_gamepad_trigger_down", "get_dual_move_2d", "get_dual_look_2d",
    "is_dual_primary_fire_down", "is_dual_primary_fire_pressed",
    "is_dual_secondary_fire_pressed", "is_dual_jump_down", "is_dual_jump_pressed",
    "is_dual_dash_down", "is_dual_dash_pressed", "is_dual_xray_toggle_pressed",
    "is_dual_pattern_toggle_pressed", "is_dual_secondary_toggle_pressed",
    "is_dual_reset_pressed", "draw_gamepad_status_badge"
]

