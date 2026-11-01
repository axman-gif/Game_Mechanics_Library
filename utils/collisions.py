# -*- coding: utf-8 -*-
"""
Non-Native Collision Routines for Raylib Python
------------------------------------------------
Provides specialized collision detection routines not natively provided by Raylib,
focusing on:
  - 2D & 3D Rotated Capsule vs Capsule collision (segment-to-segment shortest distance)
  - Capsule vs Sphere / Circle
  - 2D Rotated Bounding Box (OBB) using Separating Axis Theorem (SAT)
  - Point to segment projections and distance queries

Written for beginners: clear math explanation, no external dependencies outside pyray and math.
"""

import math
from pyray import Vector2, Vector3

EPSILON = 1e-7

# ==============================================================================
# DATA STRUCTURES
# ==============================================================================

class Capsule2D:
    """A 2D capsule defined by a line segment between start and end, with a radius."""
    def __init__(self, start: Vector2, end: Vector2, radius: float):
        self.start = start
        self.end = end
        self.radius = float(radius)

    def get_length(self) -> float:
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        return math.sqrt(dx * dx + dy * dy)


class Capsule3D:
    """A 3D capsule defined by a central axis segment from start to end, with a radius."""
    def __init__(self, start: Vector3, end: Vector3, radius: float):
        self.start = start
        self.end = end
        self.radius = float(radius)

    def get_length(self) -> float:
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        dz = self.end.z - self.start.z
        return math.sqrt(dx * dx + dy * dy + dz * dz)


class OBB2D:
    """
    An Oriented Bounding Box in 2D (a rectangle that can rotate at any angle).
    Center: (center_x, center_y)
    Half sizes: (half_width, half_height)
    Rotation: angle_radians
    """
    def __init__(self, center: Vector2, half_extents: Vector2, angle_radians: float):
        self.center = center
        self.half_extents = half_extents
        self.angle = angle_radians

    def get_corners(self):
        """Returns the 4 corner points of the rotated rectangle in counter-clockwise order."""
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        
        # Local axes
        axis_x = (cos_a, sin_a)
        axis_y = (-sin_a, cos_a)
        
        hx, hy = self.half_extents.x, self.half_extents.y
        cx, cy = self.center.x, self.center.y
        
        corners = []
        for sx, sy in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
            px = cx + sx * hx * axis_x[0] + sy * hy * axis_y[0]
            py = cy + sx * hx * axis_x[1] + sy * hy * axis_y[1]
            corners.append(Vector2(px, py))
        return corners


# ==============================================================================
# 2D SEGMENT & CAPSULE COLLISIONS
# ==============================================================================

def closest_point_on_segment_2d(point: Vector2, seg_a: Vector2, seg_b: Vector2) -> Vector2:
    """
    Calculates the point on line segment AB closest to point P in 2D.
    Clamps parameter t between 0.0 and 1.0.
    """
    ab_x = seg_b.x - seg_a.x
    ab_y = seg_b.y - seg_a.y
    ab_len_sq = ab_x * ab_x + ab_y * ab_y
    
    if ab_len_sq < EPSILON:
        return Vector2(seg_a.x, seg_a.y)
        
    ap_x = point.x - seg_a.x
    ap_y = point.y - seg_a.y
    
    # Projection factor t = (AP . AB) / |AB|^2
    t = (ap_x * ab_x + ap_y * ab_y) / ab_len_sq
    t = max(0.0, min(1.0, t))
    
    return Vector2(seg_a.x + t * ab_x, seg_a.y + t * ab_y)


def check_collision_capsule_circle_2d(cap_start: Vector2, cap_end: Vector2, cap_radius: float,
                                      circle_center: Vector2, circle_radius: float) -> bool:
    """Tests if a 2D capsule intersects with a 2D circle."""
    closest = closest_point_on_segment_2d(circle_center, cap_start, cap_end)
    dx = circle_center.x - closest.x
    dy = circle_center.y - closest.y
    dist_sq = dx * dx + dy * dy
    radius_sum = cap_radius + circle_radius
    return dist_sq <= (radius_sum * radius_sum)


def closest_points_between_segments_2d(p1: Vector2, p2: Vector2, q1: Vector2, q2: Vector2):
    """
    Finds the closest pair of points between segment P1-P2 and segment Q1-Q2 in 2D.
    Returns: (point_on_P, point_on_Q, distance)
    """
    d1_x = p2.x - p1.x
    d1_y = p2.y - p1.y
    d2_x = q2.x - q1.x
    d2_y = q2.y - q1.y
    r_x = p1.x - q1.x
    r_y = p1.y - q1.y
    
    a = d1_x * d1_x + d1_y * d1_y
    e = d2_x * d2_x + d2_y * d2_y
    f = d2_x * r_x + d2_y * r_y
    
    # Check if either or both segments degenerate into points
    if a <= EPSILON and e <= EPSILON:
        s, t = 0.0, 0.0
    elif a <= EPSILON:
        s = 0.0
        t = max(0.0, min(1.0, f / e))
    else:
        c = d1_x * r_x + d1_y * r_y
        if e <= EPSILON:
            t = 0.0
            s = max(0.0, min(1.0, -c / a))
        else:
            b = d1_x * d2_x + d1_y * d2_y
            denom = a * e - b * b
            if denom != 0.0:
                s = max(0.0, min(1.0, (b * f - c * e) / denom))
            else:
                s = 0.0
            t = (b * s + f) / e
            if t < 0.0:
                t = 0.0
                s = max(0.0, min(1.0, -c / a))
            elif t > 1.0:
                t = 1.0
                s = max(0.0, min(1.0, (b - c) / a))

    c1 = Vector2(p1.x + s * d1_x, p1.y + s * d1_y)
    c2 = Vector2(q1.x + t * d2_x, q1.y + t * d2_y)
    dist = math.sqrt((c1.x - c2.x) ** 2 + (c1.y - c2.y) ** 2)
    return c1, c2, dist


def check_collision_capsules_2d(p1: Vector2, p2: Vector2, r1: float,
                                q1: Vector2, q2: Vector2, r2: float) -> bool:
    """
    Returns True if two 2D capsules (defined by segments P1-P2 and Q1-Q2 with radii r1, r2) intersect.
    Works for any rotation or orientation.
    """
    _, _, dist = closest_points_between_segments_2d(p1, p2, q1, q2)
    return dist <= (r1 + r2)


# ==============================================================================
# 3D SEGMENT & ROTATED CAPSULE COLLISIONS
# ==============================================================================

def closest_point_on_segment_3d(point: Vector3, seg_a: Vector3, seg_b: Vector3) -> Vector3:
    """
    Finds the closest point on 3D segment AB to point P.
    """
    ab_x = seg_b.x - seg_a.x
    ab_y = seg_b.y - seg_a.y
    ab_z = seg_b.z - seg_a.z
    ab_len_sq = ab_x * ab_x + ab_y * ab_y + ab_z * ab_z
    
    if ab_len_sq < EPSILON:
        return Vector3(seg_a.x, seg_a.y, seg_a.z)
        
    ap_x = point.x - seg_a.x
    ap_y = point.y - seg_a.y
    ap_z = point.z - seg_a.z
    
    t = (ap_x * ab_x + ap_y * ab_y + ap_z * ab_z) / ab_len_sq
    t = max(0.0, min(1.0, t))
    
    return Vector3(seg_a.x + t * ab_x, seg_a.y + t * ab_y, seg_a.z + t * ab_z)


def check_collision_capsule_sphere_3d(cap_start: Vector3, cap_end: Vector3, cap_radius: float,
                                      sphere_pos: Vector3, sphere_radius: float) -> bool:
    """Tests if a 3D capsule intersects with a 3D sphere."""
    closest = closest_point_on_segment_3d(sphere_pos, cap_start, cap_end)
    dx = sphere_pos.x - closest.x
    dy = sphere_pos.y - closest.y
    dz = sphere_pos.z - closest.z
    dist_sq = dx * dx + dy * dy + dz * dz
    radius_sum = cap_radius + sphere_radius
    return dist_sq <= (radius_sum * radius_sum)


def closest_points_between_segments_3d(p1: Vector3, p2: Vector3, q1: Vector3, q2: Vector3):
    """
    Calculates the closest points between two 3D segments P and Q.
    Handles parallel, overlapping, skewed, and degenerate segment configurations.
    Returns: (point_on_P, point_on_Q, distance)
    """
    d1_x = p2.x - p1.x
    d1_y = p2.y - p1.y
    d1_z = p2.z - p1.z
    
    d2_x = q2.x - q1.x
    d2_y = q2.y - q1.y
    d2_z = q2.z - q1.z
    
    r_x = p1.x - q1.x
    r_y = p1.y - q1.y
    r_z = p1.z - q1.z
    
    a = d1_x * d1_x + d1_y * d1_y + d1_z * d1_z
    e = d2_x * d2_x + d2_y * d2_y + d2_z * d2_z
    f = d2_x * r_x + d2_y * r_y + d2_z * r_z
    
    # Degenerate segments (one or both are single points)
    if a <= EPSILON and e <= EPSILON:
        s, t = 0.0, 0.0
    elif a <= EPSILON:
        s = 0.0
        t = max(0.0, min(1.0, f / e))
    else:
        c = d1_x * r_x + d1_y * r_y + d1_z * r_z
        if e <= EPSILON:
            t = 0.0
            s = max(0.0, min(1.0, -c / a))
        else:
            b = d1_x * d2_x + d1_y * d2_y + d1_z * d2_z
            denom = a * e - b * b
            
            # Segments not parallel
            if denom > EPSILON:
                s = max(0.0, min(1.0, (b * f - c * e) / denom))
            else:
                s = 0.0  # Parallel: pick an arbitrary s
                
            t = (b * s + f) / e
            
            if t < 0.0:
                t = 0.0
                s = max(0.0, min(1.0, -c / a))
            elif t > 1.0:
                t = 1.0
                s = max(0.0, min(1.0, (b - c) / a))

    c1 = Vector3(p1.x + s * d1_x, p1.y + s * d1_y, p1.z + s * d1_z)
    c2 = Vector3(q1.x + t * d2_x, q1.y + t * d2_y, q1.z + t * d2_z)
    
    dx = c1.x - c2.x
    dy = c1.y - c2.y
    dz = c1.z - c2.z
    dist = math.sqrt(dx * dx + dy * dy + dz * dz)
    return c1, c2, dist


def check_collision_capsules_3d(p1: Vector3, p2: Vector3, r1: float,
                                q1: Vector3, q2: Vector3, r2: float) -> bool:
    """
    Returns True if two arbitrarily rotated 3D capsules collide.
    A capsule is defined by its core central segment and its radius.
    """
    _, _, dist = closest_points_between_segments_3d(p1, p2, q1, q2)
    return dist <= (r1 + r2)


# ==============================================================================
# SEPARATING AXIS THEOREM (SAT) FOR 2D ROTATED BOXES (OBB)
# ==============================================================================

def _project_polygon_on_axis(vertices, axis_x, axis_y):
    """Calculates min and max scalar projections of vertices onto a given normal axis."""
    min_proj = float("inf")
    max_proj = float("-inf")
    for v in vertices:
        proj = v.x * axis_x + v.y * axis_y
        if proj < min_proj:
            min_proj = proj
        if proj > max_proj:
            max_proj = proj
    return min_proj, max_proj


def check_collision_obb_2d(obb1: OBB2D, obb2: OBB2D) -> bool:
    """
    Checks collision between two arbitrary 2D Oriented Bounding Boxes (OBBs)
    using the Separating Axis Theorem (SAT).
    Returns True if overlapping, False if separated.
    """
    corners1 = obb1.get_corners()
    corners2 = obb2.get_corners()
    
    # Potential separating axes are the edge normals of both boxes (4 axes total)
    axes = [
        (math.cos(obb1.angle), math.sin(obb1.angle)),
        (-math.sin(obb1.angle), math.cos(obb1.angle)),
        (math.cos(obb2.angle), math.sin(obb2.angle)),
        (-math.sin(obb2.angle), math.cos(obb2.angle))
    ]
    
    for ax, ay in axes:
        min1, max1 = _project_polygon_on_axis(corners1, ax, ay)
        min2, max2 = _project_polygon_on_axis(corners2, ax, ay)
        
        # If there is a gap on any axis, the shapes cannot be colliding
        if max1 < min2 or max2 < min1:
            return False
            
    return True

