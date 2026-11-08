# -*- coding: utf-8 -*-
"""
Game Math, Easing & Camera Shake Helpers for Raylib Python
----------------------------------------------------------
Provides standard game math utilities:
  - Interpolation: lerp, clamp, approach, framerate-independent damp
  - Vector operations: distance, normalization, angle conversions
  - Easing functions: Quad, Elastic, Bounce
  - Camera Shake: Trauma-based 2D camera shake generator

Written cleanly for beginners.
"""

import math
import random
from pyray import Vector2, Vector3, Color

# ==============================================================================
# CFFI SAFE TYPE CASTING HELPERS
# ==============================================================================

def safe_color(r: float, g: float, b: float, a: float = 255.0) -> Color:
    """
    Safely creates a Raylib Color struct by clamping and casting each channel
    to an unsigned 8-bit integer (0..255).
    
    Prevents Raylib CFFI 'unsigned char' type errors when passing floats or
    out-of-bounds values.
    """
    cr = int(max(0, min(255, round(float(r)))))
    cg = int(max(0, min(255, round(float(g)))))
    cb = int(max(0, min(255, round(float(b)))))
    ca = int(max(0, min(255, round(float(a)))))
    return Color(cr, cg, cb, ca)

# ==============================================================================
# INTERPOLATION & CLAMPING
# ==============================================================================

def clamp(val: float, min_val: float, max_val: float) -> float:
    """Clamps a numeric value between min_val and max_val."""
    return max(min_val, min(val, max_val))


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b by factor t (0.0 to 1.0)."""
    return a + (b - a) * t


def lerp_v2(a: Vector2, b: Vector2, t: float) -> Vector2:
    """Linear interpolation between two Vector2s."""
    return Vector2(lerp(a.x, b.x, t), lerp(a.y, b.y, t))


def lerp_v3(a: Vector3, b: Vector3, t: float) -> Vector3:
    """Linear interpolation between two Vector3s."""
    return Vector3(lerp(a.x, b.x, t), lerp(a.y, b.y, t), lerp(a.z, b.z, t))


def approach(current: float, target: float, max_delta: float) -> float:
    """
    Moves current toward target by at most max_delta steps.
    Never overshoots target.
    """
    if current < target:
        return min(current + max_delta, target)
    else:
        return max(current - max_delta, target)


def damp(current: float, target: float, smoothing: float, dt: float) -> float:
    """
    Framerate-independent exponential smoothing.
    Higher smoothing = slower transition (e.g., smoothing=5 to 15 is typical).
    """
    return lerp(current, target, 1.0 - math.exp(-smoothing * dt))


def damp_v2(current: Vector2, target: Vector2, smoothing: float, dt: float) -> Vector2:
    """Framerate-independent smoothing for Vector2."""
    factor = 1.0 - math.exp(-smoothing * dt)
    return Vector2(lerp(current.x, target.x, factor), lerp(current.y, target.y, factor))


def damp_v3(current: Vector3, target: Vector3, smoothing: float, dt: float) -> Vector3:
    """Framerate-independent smoothing for Vector3."""
    factor = 1.0 - math.exp(-smoothing * dt)
    return Vector3(lerp(current.x, target.x, factor), lerp(current.y, target.y, factor), lerp(current.z, target.z, factor))


# ==============================================================================
# VECTORS & ANGLES
# ==============================================================================

def distance_2d(v1: Vector2, v2: Vector2) -> float:
    """Euclidean distance between two 2D points."""
    dx = v1.x - v2.x
    dy = v1.y - v2.y
    return math.sqrt(dx * dx + dy * dy)


def distance_3d(v1: Vector3, v2: Vector3) -> float:
    """Euclidean distance between two 3D points."""
    dx = v1.x - v2.x
    dy = v1.y - v2.y
    dz = v1.z - v2.z
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def normalize_2d(v: Vector2) -> Vector2:
    """Returns a unit vector pointing in the direction of v."""
    length = math.sqrt(v.x * v.x + v.y * v.y)
    if length < 0.0001:
        return Vector2(0.0, 0.0)
    return Vector2(v.x / length, v.y / length)


def normalize_3d(v: Vector3) -> Vector3:
    """Returns a unit vector pointing in the direction of v."""
    length = math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)
    if length < 0.0001:
        return Vector3(0.0, 0.0, 0.0)
    return Vector3(v.x / length, v.y / length, v.z / length)


def angle_to_vector_2d(angle_radians: float) -> Vector2:
    """Returns a unit direction vector corresponding to the given angle in radians."""
    return Vector2(math.cos(angle_radians), math.sin(angle_radians))


def vector_to_angle_2d(v: Vector2) -> float:
    """Returns the angle in radians of a 2D direction vector."""
    return math.atan2(v.y, v.x)


# ==============================================================================
# EASING CURVES (ANIMATIONS & JUICE)
# ==============================================================================

def ease_in_quad(t: float) -> float:
    """Accelerating from zero velocity."""
    t = clamp(t, 0.0, 1.0)
    return t * t


def ease_out_quad(t: float) -> float:
    """Decelerating to zero velocity."""
    t = clamp(t, 0.0, 1.0)
    return t * (2.0 - t)


def ease_in_out_quad(t: float) -> float:
    """Smooth acceleration and deceleration."""
    t = clamp(t, 0.0, 1.0)
    return 2.0 * t * t if t < 0.5 else -1.0 + (4.0 - 2.0 * t) * t


def ease_out_bounce(t: float) -> float:
    """Bounces at the end of the motion."""
    t = clamp(t, 0.0, 1.0)
    n1 = 7.5625
    d1 = 2.75
    if t < 1.0 / d1:
        return n1 * t * t
    elif t < 2.0 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    elif t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    else:
        t -= 2.625 / d1
        return n1 * t * t + 0.984375


def ease_out_elastic(t: float) -> float:
    """Elastic overshoot at the end."""
    t = clamp(t, 0.0, 1.0)
    if t == 0.0 or t == 1.0:
        return t
    p = 0.3
    return math.pow(2.0, -10.0 * t) * math.sin((t - p / 4.0) * (2.0 * math.pi) / p) + 1.0


# ==============================================================================
# CAMERA SHAKE (TRAUMA MODEL)
# ==============================================================================

class TraumaShake:
    """
    Implements Squirrel Eiserloh's classic trauma-based screen shake model.
    Trauma is an energy value from 0.0 to 1.0. Shake intensity equals trauma^2 or trauma^3.
    """
    def __init__(self, max_offset_px: float = 16.0, max_angle_deg: float = 3.0, decay_rate: float = 1.2):
        self.trauma = 0.0
        self.max_offset = max_offset_px
        self.max_angle_rad = math.radians(max_angle_deg)
        self.decay = decay_rate

    def add_trauma(self, amount: float):
        """Adds trauma (capped between 0.0 and 1.0). Typical hit: +0.2, explosion: +0.6."""
        self.trauma = clamp(self.trauma + amount, 0.0, 1.0)

    def update(self, dt: float) -> Tuple[float, float, float]:
        """
        Updates decay and returns: (offset_x, offset_y, rotation_radians).
        Apply this to your camera target / offset each frame.
        """
        if self.trauma <= 0.0:
            return 0.0, 0.0, 0.0
            
        self.trauma = max(0.0, self.trauma - self.decay * dt)
        shake_intensity = self.trauma * self.trauma  # Quadratic falloff feels best
        
        offset_x = (random.random() * 2.0 - 1.0) * self.max_offset * shake_intensity
        offset_y = (random.random() * 2.0 - 1.0) * self.max_offset * shake_intensity
        angle = (random.random() * 2.0 - 1.0) * self.max_angle_rad * shake_intensity
        
        return offset_x, offset_y, angle

