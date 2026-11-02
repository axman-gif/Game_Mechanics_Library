# -*- coding: utf-8 -*-
"""
Simultaneous Keyboard/Mouse & Gamepad Input Utilities (`utils/gamepad_input.py`)
--------------------------------------------------------------------------------
Provides hardware-agnostic dual input polling so every minigame and the launcher
respond simultaneously to Keyboard + Mouse AND any connected Gamepad (Xbox,
PlayStation, Switch Pro, Steam Deck, or generic XInput/DirectInput controllers).

Design Principles (C++ Transferable):
  1. Automatic Hot-Plug Detection: Scans gamepad slots 0..3 every frame via
     `is_gamepad_available(i)`. If a controller is plugged in at any time, its
     axes and buttons work immediately alongside keyboard and mouse.
  2. Radial Deadzone Filtering: Analog sticks apply a scaled radial deadzone
     (`deadzone = 0.18`) instead of an axial box deadzone, eliminating stick
     drift while preserving smooth 360-degree analog directional control.
  3. Simultaneous Multiplexing (OR / Vector Merge): Never locks out keyboard/mouse
     when a gamepad is connected. Both input sources remain active at the same time.
"""

import sys
import math

sys.dont_write_bytecode = True

from pyray import (
    Vector2,
    Color,
    is_key_down,
    is_key_pressed,
    is_mouse_button_down,
    is_mouse_button_pressed,
    is_gamepad_available,
    get_gamepad_name,
    get_gamepad_axis_movement,
    is_gamepad_button_down,
    is_gamepad_button_pressed,
    KEY_W,
    KEY_A,
    KEY_S,
    KEY_D,
    KEY_UP,
    KEY_DOWN,
    KEY_LEFT,
    KEY_RIGHT,
    KEY_SPACE,
    KEY_ENTER,
    KEY_TAB,
    KEY_F1,
    KEY_F2,
    KEY_R,
    KEY_J,
    KEY_K,
    KEY_Z,
    KEY_X,
    KEY_F,
    KEY_LEFT_SHIFT,
    KEY_RIGHT_SHIFT,
    MOUSE_BUTTON_LEFT,
    GAMEPAD_AXIS_LEFT_X,
    GAMEPAD_AXIS_LEFT_Y,
    GAMEPAD_AXIS_RIGHT_X,
    GAMEPAD_AXIS_RIGHT_Y,
    GAMEPAD_AXIS_LEFT_TRIGGER,
    GAMEPAD_AXIS_RIGHT_TRIGGER,
    GAMEPAD_BUTTON_LEFT_FACE_UP,
    GAMEPAD_BUTTON_LEFT_FACE_RIGHT,
    GAMEPAD_BUTTON_LEFT_FACE_DOWN,
    GAMEPAD_BUTTON_LEFT_FACE_LEFT,
    GAMEPAD_BUTTON_RIGHT_FACE_UP,
    GAMEPAD_BUTTON_RIGHT_FACE_RIGHT,
    GAMEPAD_BUTTON_RIGHT_FACE_DOWN,
    GAMEPAD_BUTTON_RIGHT_FACE_LEFT,
    GAMEPAD_BUTTON_LEFT_TRIGGER_1,
    GAMEPAD_BUTTON_LEFT_TRIGGER_2,
    GAMEPAD_BUTTON_RIGHT_TRIGGER_1,
    GAMEPAD_BUTTON_RIGHT_TRIGGER_2,
    GAMEPAD_BUTTON_MIDDLE_LEFT,
    GAMEPAD_BUTTON_MIDDLE_RIGHT,
    GAMEPAD_BUTTON_LEFT_THUMB,
    GAMEPAD_BUTTON_RIGHT_THUMB,
)
from .ui_settings import draw_text


# ==============================================================================
# 1. GAMEPAD DETECTION & HOT-PLUG DISCOVERY
# ==============================================================================

def get_active_gamepad_id() -> int:
    """
    Scans gamepad ports 0..3 and returns the index of the first connected
    controller, or -1 if no controller is connected.
    C++ Equivalent:
      int get_active_gamepad_id() {
          for (int i = 0; i < 4; ++i) if (IsGamepadAvailable(i)) return i;
          return -1;
      }
    """
    for pad_id in range(4):
        if is_gamepad_available(pad_id):
            return pad_id
    return -1


def is_any_gamepad_connected() -> bool:
    """Returns True if at least one gamepad is currently connected."""
    return get_active_gamepad_id() >= 0


def get_active_gamepad_name() -> str:
    """Returns the human-readable controller name, or 'None' if disconnected."""
    pad_id = get_active_gamepad_id()
    if pad_id < 0:
        return "None"
    raw_name = get_gamepad_name(pad_id)
    if raw_name and len(str(raw_name).strip()) > 0:
        return str(raw_name).strip()
    return f"Gamepad #{pad_id}"


# ==============================================================================
# 2. RADIAL DEADZONE & ANALOG STICK / TRIGGER HELPERS
# ==============================================================================

def apply_radial_deadzone(raw_x: float, raw_y: float, deadzone: float = 0.18) -> Vector2:
    """
    Applies a scaled radial deadzone to a 2D analog stick input.
    Why Radial instead of Axial?
      Checking |x| < dz and |y| < dz independently creates a cross-shaped deadzone
      that snaps diagonal movement to the 4 cardinal axes. A radial deadzone checks
      the Euclidean length sqrt(x^2 + y^2) and smoothly remaps [deadzone .. 1.0]
      onto [0.0 .. 1.0] in every direction.
    """
    mag = math.sqrt(raw_x * raw_x + raw_y * raw_y)
    if mag <= deadzone or mag < 0.0001:
        return Vector2(0.0, 0.0)

    effective_span = max(0.001, 1.0 - deadzone)
    scaled_mag = (mag - deadzone) / effective_span
    if scaled_mag > 1.0:
        scaled_mag = 1.0

    nx = (raw_x / mag) * scaled_mag
    ny = (raw_y / mag) * scaled_mag
    return Vector2(nx, ny)


def get_gamepad_left_stick(
    deadzone: float = 0.18,
    include_dpad: bool = True,
    include_dpad_x: bool = True,
    include_dpad_y: bool = True,
) -> Vector2:
    """
    Returns the 2D movement vector from the active Gamepad's Left Analog Stick
    (and optionally D-Pad buttons), or (0, 0) if no gamepad is connected.
    """
    pad_id = get_active_gamepad_id()
    if pad_id < 0:
        return Vector2(0.0, 0.0)

    lx = get_gamepad_axis_movement(pad_id, GAMEPAD_AXIS_LEFT_X)
    ly = get_gamepad_axis_movement(pad_id, GAMEPAD_AXIS_LEFT_Y)
    vec = apply_radial_deadzone(lx, ly, deadzone)

    if include_dpad:
        dx = 0.0
        dy = 0.0
        if include_dpad_x:
            if is_gamepad_button_down(pad_id, GAMEPAD_BUTTON_LEFT_FACE_LEFT):
                dx -= 1.0
            if is_gamepad_button_down(pad_id, GAMEPAD_BUTTON_LEFT_FACE_RIGHT):
                dx += 1.0
        if include_dpad_y:
            if is_gamepad_button_down(pad_id, GAMEPAD_BUTTON_LEFT_FACE_UP):
                dy -= 1.0
            if is_gamepad_button_down(pad_id, GAMEPAD_BUTTON_LEFT_FACE_DOWN):
                dy += 1.0

        if abs(dx) > 0.0 or abs(dy) > 0.0:
            vec.x += dx
            vec.y += dy
            mag = math.sqrt(vec.x * vec.x + vec.y * vec.y)
            if mag > 1.0:
                vec.x /= mag
                vec.y /= mag

    return vec


def get_gamepad_right_stick(deadzone: float = 0.18) -> Vector2:
    """
    Returns the 2D aiming / camera vector from the active Gamepad's Right Stick,
    or (0, 0) if no gamepad is connected.
    """
    pad_id = get_active_gamepad_id()
    if pad_id < 0:
        return Vector2(0.0, 0.0)

    rx = get_gamepad_axis_movement(pad_id, GAMEPAD_AXIS_RIGHT_X)
    ry = get_gamepad_axis_movement(pad_id, GAMEPAD_AXIS_RIGHT_Y)
    return apply_radial_deadzone(rx, ry, deadzone)


def is_gamepad_trigger_down(is_right_trigger: bool = True, threshold: float = 0.25) -> bool:
    """
    Checks whether the Left or Right analog trigger (LT/L2 or RT/R2) is held down.
    Supports both digital trigger buttons and GLFW's [-1.0 .. +1.0] trigger axis.
    """
    pad_id = get_active_gamepad_id()
    if pad_id < 0:
        return False

    if is_right_trigger:
        if is_gamepad_button_down(pad_id, GAMEPAD_BUTTON_RIGHT_TRIGGER_2):
            return True
        axis_val = get_gamepad_axis_movement(pad_id, GAMEPAD_AXIS_RIGHT_TRIGGER)
        return axis_val > threshold
    else:
        if is_gamepad_button_down(pad_id, GAMEPAD_BUTTON_LEFT_TRIGGER_2):
            return True
        axis_val = get_gamepad_axis_movement(pad_id, GAMEPAD_AXIS_LEFT_TRIGGER)
        return axis_val > threshold


# ==============================================================================
# 3. SIMULTANEOUS DUAL INPUT (KEYBOARD/MOUSE + GAMEPAD COMBINED)
# ==============================================================================

def get_dual_move_2d(
    deadzone: float = 0.18,
    use_arrow_keys: bool = True,
    include_dpad: bool = True,
    include_dpad_x: bool = True,
    include_dpad_y: bool = True,
) -> Vector2:
    """
    Simultaneously polls Keyboard (WASD + optional Arrow Keys) AND Gamepad
    (Left Stick + D-Pad). Either or both can be used at the same time.
    Preserves analog partial tilt speed (< 1.0) while clamping combined magnitude <= 1.0.
    """
    kb_x = 0.0
    kb_y = 0.0
    if is_key_down(KEY_A) or (use_arrow_keys and is_key_down(KEY_LEFT)):
        kb_x -= 1.0
    if is_key_down(KEY_D) or (use_arrow_keys and is_key_down(KEY_RIGHT)):
        kb_x += 1.0
    if is_key_down(KEY_W) or (use_arrow_keys and is_key_down(KEY_UP)):
        kb_y -= 1.0
    if is_key_down(KEY_S) or (use_arrow_keys and is_key_down(KEY_DOWN)):
        kb_y += 1.0

    kb_mag = math.sqrt(kb_x * kb_x + kb_y * kb_y)
    if kb_mag > 1.0:
        kb_x /= kb_mag
        kb_y /= kb_mag

    pad_vec = get_gamepad_left_stick(
        deadzone=deadzone,
        include_dpad=include_dpad,
        include_dpad_x=include_dpad_x,
        include_dpad_y=include_dpad_y,
    )

    out_x = kb_x + pad_vec.x
    out_y = kb_y + pad_vec.y
    out_mag = math.sqrt(out_x * out_x + out_y * out_y)
    if out_mag > 1.0:
        out_x /= out_mag
        out_y /= out_mag

    return Vector2(out_x, out_y)


def get_dual_look_2d(deadzone: float = 0.18, use_arrow_keys: bool = True) -> Vector2:
    """
    Simultaneously polls Keyboard (Arrow Keys) AND Gamepad (Right Analog Stick)
    for 3D camera orbiting or 2D twin-stick aiming.
    """
    kb_x = 0.0
    kb_y = 0.0
    if use_arrow_keys:
        if is_key_down(KEY_LEFT):
            kb_x -= 1.0
        if is_key_down(KEY_RIGHT):
            kb_x += 1.0
        if is_key_down(KEY_UP):
            kb_y -= 1.0
        if is_key_down(KEY_DOWN):
            kb_y += 1.0

    pad_look = get_gamepad_right_stick(deadzone=deadzone)
    out_x = kb_x + pad_look.x
    out_y = kb_y + pad_look.y
    out_mag = math.sqrt(out_x * out_x + out_y * out_y)
    if out_mag > 1.0:
        out_x /= out_mag
        out_y /= out_mag

    return Vector2(out_x, out_y)


def is_dual_primary_fire_down() -> bool:
    """
    Returns True if Primary Fire / Attack is held on Keyboard/Mouse (Left Click,
    J, Z) OR Gamepad (RT/R2, RB/R1, X/Square).
    """
    if is_mouse_button_down(MOUSE_BUTTON_LEFT) or is_key_down(KEY_J) or is_key_down(KEY_Z):
        return True
    pad_id = get_active_gamepad_id()
    if pad_id >= 0:
        if (
            is_gamepad_button_down(pad_id, GAMEPAD_BUTTON_RIGHT_FACE_LEFT)
            or is_gamepad_button_down(pad_id, GAMEPAD_BUTTON_RIGHT_TRIGGER_1)
            or is_gamepad_trigger_down(is_right_trigger=True)
        ):
            return True
    return False


def is_dual_primary_fire_pressed() -> bool:
    """Single-frame press check for Primary Fire / Confirm."""
    if is_mouse_button_pressed(MOUSE_BUTTON_LEFT) or is_key_pressed(KEY_J) or is_key_pressed(KEY_Z):
        return True
    pad_id = get_active_gamepad_id()
    if pad_id >= 0:
        if (
            is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_FACE_LEFT)
            or is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_TRIGGER_1)
            or is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_TRIGGER_2)
        ):
            return True
    return False


def is_dual_secondary_fire_pressed() -> bool:
    """
    Returns True if Secondary Fire / Heavy Skill is pressed on Keyboard (K, X, F)
    OR Gamepad (Y/Triangle).
    """
    if is_key_pressed(KEY_K) or is_key_pressed(KEY_X) or is_key_pressed(KEY_F):
        return True
    pad_id = get_active_gamepad_id()
    if pad_id >= 0:
        if is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_FACE_UP):
            return True
    return False


def is_dual_jump_down() -> bool:
    """
    Returns True if Jump / Thruster Boost is held on Keyboard (Spacebar)
    OR Gamepad (A/Cross or LT/L2).
    """
    if is_key_down(KEY_SPACE):
        return True
    pad_id = get_active_gamepad_id()
    if pad_id >= 0:
        if (
            is_gamepad_button_down(pad_id, GAMEPAD_BUTTON_RIGHT_FACE_DOWN)
            or is_gamepad_trigger_down(is_right_trigger=False)
        ):
            return True
    return False


def is_dual_jump_pressed() -> bool:
    """Single-frame press check for Jump (Spacebar or Gamepad A/Cross)."""
    if is_key_pressed(KEY_SPACE):
        return True
    pad_id = get_active_gamepad_id()
    if pad_id >= 0:
        if is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_FACE_DOWN):
            return True
    return False


def is_dual_dash_down() -> bool:
    """
    Returns True if Dash / Focus Mode is held on Keyboard (Left/Right Shift)
    OR Gamepad (B/Circle, LB/L1, or LT/L2).
    """
    if is_key_down(KEY_LEFT_SHIFT) or is_key_down(KEY_RIGHT_SHIFT):
        return True
    pad_id = get_active_gamepad_id()
    if pad_id >= 0:
        if (
            is_gamepad_button_down(pad_id, GAMEPAD_BUTTON_RIGHT_FACE_RIGHT)
            or is_gamepad_button_down(pad_id, GAMEPAD_BUTTON_LEFT_TRIGGER_1)
            or is_gamepad_trigger_down(is_right_trigger=False)
        ):
            return True
    return False


def is_dual_dash_pressed() -> bool:
    """
    Single-frame press check for Dash / Evade on Keyboard (Left/Right Shift)
    OR Gamepad (B/Circle or LB/L1).
    """
    if is_key_pressed(KEY_LEFT_SHIFT) or is_key_pressed(KEY_RIGHT_SHIFT):
        return True
    pad_id = get_active_gamepad_id()
    if pad_id >= 0:
        if (
            is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_FACE_RIGHT)
            or is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_LEFT_TRIGGER_1)
        ):
            return True
    return False


def is_dual_xray_toggle_pressed() -> bool:
    """
    Toggles the [Tab] X-Ray Telemetry Overlay via Keyboard [Tab]
    OR Gamepad [View / Select / Back / Share] (`GAMEPAD_BUTTON_MIDDLE_LEFT`).
    """
    if is_key_pressed(KEY_TAB):
        return True
    pad_id = get_active_gamepad_id()
    if pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_MIDDLE_LEFT):
        return True
    return False


def is_dual_pattern_toggle_pressed() -> bool:
    """
    Toggles the primary [F1] Pattern Comparison via Keyboard [F1]
    OR Gamepad Right Stick Click [R3] (`GAMEPAD_BUTTON_RIGHT_THUMB`).
    """
    if is_key_pressed(KEY_F1):
        return True
    pad_id = get_active_gamepad_id()
    if pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_THUMB):
        return True
    return False


def is_dual_secondary_toggle_pressed() -> bool:
    """
    Toggles the secondary [F2] Pattern Comparison via Keyboard [F2]
    OR Gamepad Left Stick Click [L3] (`GAMEPAD_BUTTON_LEFT_THUMB`).
    """
    if is_key_pressed(KEY_F2):
        return True
    pad_id = get_active_gamepad_id()
    if pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_LEFT_THUMB):
        return True
    return False


def is_dual_reset_pressed() -> bool:
    """
    Resets the match/simulation via Keyboard [R]
    OR Gamepad [Start / Menu / Options] (`GAMEPAD_BUTTON_MIDDLE_RIGHT`).
    """
    if is_key_pressed(KEY_R):
        return True
    pad_id = get_active_gamepad_id()
    if pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_MIDDLE_RIGHT):
        return True
    return False


def draw_gamepad_status_badge(x: int, y: int, font_size: int = 11):
    """
    Renders a live HUD indicator showing that simultaneous Keyboard/Mouse + Gamepad
    controls are active when a controller is detected.
    """
    if is_any_gamepad_connected():
        cname = get_active_gamepad_name()
        if len(cname) > 18:
            cname = cname[:18]
        draw_text(
            f"INPUT: KB/M + {cname} [SIMULTANEOUS]",
            int(x),
            int(y),
            int(font_size),
            Color(80, 235, 130, 255),
        )
    else:
        draw_text(
            "INPUT: KB/Mouse (Connect Gamepad anytime)",
            int(x),
            int(y),
            int(font_size),
            Color(135, 150, 175, 255),
        )

