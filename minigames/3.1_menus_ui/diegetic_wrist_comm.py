# -*- coding: utf-8 -*-
"""
Diegetic Wrist Comm - Diegetic World-Space Holographic Interface
================================================================
Section          : 3.1 Menus & UI
Pattern Category : User Interface & Presentation
Dimension        : 3D

Problem Solved:
  Traditional 2D screen-space HUDs (heads-up displays) break player immersion by pinning
  static health bars, ammo counters, and minimaps directly to the camera viewport glass.
  This disconnects UI state from physical in-world avatars, eliminating spatial depth,
  environmental lighting interaction, parallax motion cues, and physical embodiment.

How the Pattern Works:
  1. Diegetic World-Space Transformation: UI surfaces exist as tangible geometric planes
     anchored to character skeleton bones (forearm/wrist) in 3D world space, subject to
     standard camera projection, depth foreshortening, and distance attenuation.
  2. Spring-Damped Parallax Lag: The holographic projection plane uses second-order spring
     physics (F = -k*x - c*v) to simulate rotational inertia and photonic emitter delay,
     creating authentic depth separation between the mechanical wrist gauntlet and the
     floating holographic screen.
  3. Offscreen Texture Projection (FBO / RenderTexture2D): The interactive terminal
     (vitals, arsenal, tactical radar, atmospheric telemetry) is rendered into an in-memory
     render texture and mapped onto a 3D oriented quad with alpha blending and scanlines.
  4. Localized World-to-Radar Coordinate Mapping: Translates 3D world entity coordinates
     into the wrist radar's local polar/planar projection space relative to player facing.

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - WASD / Left Stick / D-Pad     : Walk / Navigate Sci-Fi Research Chamber
  - Mouse / Right Stick / Arrows  : Look around / Aim camera view
  - Space / Gamepad LT or RT      : Hold to Raise / Inspect Wrist Comm (Focus Mode)
  - C / Gamepad X                 : Toggle Sticky Inspect Focus Lock
  - Q / E or 1-4 / Gamepad LB/RB  : Cycle Terminal Tabs (Vitals, Arsenal, Radar, Environment)
  - Left Click / Gamepad A        : Cycle Sub-Modes (Fire Mode in Arsenal, Pulse in Vitals)
  - [Tab] / Gamepad Y (Select)    : Toggle X-Ray Telemetry & Mathematical Projection Overlay
  - [F1]  / Gamepad R3            : Toggle Diegetic World-Space vs Flat 2D Screen-Space HUD
  - [F2]  / Gamepad L3            : Toggle Parallax Spring Inertia Lag ON/OFF
  - [Ctrl +/-]                    : Increase / Decrease UI Font Size
  - [F11]                         : Toggle Fullscreen
  - [R]   / Gamepad Start         : Reset Simulation
"""

import sys
import os
import math
import random

# 1. Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# 2. Add repository root to search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# 3. Mandatory Raylib & modular imports
from pyray import *
from assets import *
from utils import *

# Window & Viewport Dimensions
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WINDOW_TITLE = "Diegetic Wrist Comm - 3D World-Space UI (Raylib Pattern Lab)"

# Terminal Offscreen Buffer Resolution
HOLO_TEX_WIDTH = 512
HOLO_TEX_HEIGHT = 384

# Tab Enumerations (Explicit C++ enum mapping)
TAB_VITALS = 0
TAB_ARSENAL = 1
TAB_RADAR = 2
TAB_ENVIRONMENT = 3

# Fire Mode Enumerations
FIRE_MODE_SEMI = 0
FIRE_MODE_BURST = 1
FIRE_MODE_AUTO = 2


# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATION
# ==============================================================================

class HolographicProjectionPlane:
    """
    Pattern: Diegetic World-Space Holographic Plane with Damped Spring Parallax.
    
    C++ / Architectural Mapping:
      struct HolographicPlane {
          Vector3 world_center;
          Vector3 spring_velocity;
          Vector3 normal;
          Vector3 up_vector;
          Vector3 right_vector;
          float width;
          float height;
          float spring_stiffness;
          float spring_damping;
          bool parallax_active;
      };

    Mathematical Concept:
      In a diegetic interface, the display exists as an oriented quad in 3D space:
        Corner_TL = Center - Right*(W/2) + Up*(H/2)
        Corner_TR = Center + Right*(W/2) + Up*(H/2)
        Corner_BR = Center + Right*(W/2) - Up*(H/2)
        Corner_BL = Center - Right*(W/2) - Up*(H/2)
      
      When the player turns their head or moves the forearm, the holographic
      emitter plane trails behind via a 2nd-order damped harmonic oscillator:
        a_spring = -k * (x_current - x_target) - c * v_current
        v_current += a_spring * dt
        x_current += v_current * dt
      
      This creates depth separation and rotational parallax between the solid
      mechanical wrist housing and the floating photonic hologram.
    """
    def __init__(self):
        self.width = 0.40
        self.height = 0.30
        self.world_center = Vector3(0.0, 1.4, 3.5)
        self.target_center = Vector3(0.0, 1.4, 3.5)
        self.spring_vel = Vector3(0.0, 0.0, 0.0)
        
        # Second-order harmonic oscillator coefficients
        self.spring_stiffness = 145.0  # k: spring tension restoring force
        self.spring_damping = 15.0     # c: viscous friction velocity decay
        
        # Surface orientation vectors in 3D world space
        self.normal = Vector3(0.0, 0.0, 1.0)
        self.up_vec = Vector3(0.0, 1.0, 0.0)
        self.right_vec = Vector3(1.0, 0.0, 0.0)
        
        # Telemetry metrics
        self.current_offset = Vector3(0.0, 0.0, 0.0)
        self.parallax_enabled = True
        self.scanline_phase = 0.0
        self.flicker_alpha = 1.0
        self.distance_to_cam = 0.0
        self.angle_to_cam_deg = 0.0

    def update(self, dt: float, anchor_pos: Vector3, cam_pos: Vector3, wrist_up: Vector3, wrist_forward: Vector3):
        # 1. Compute ideal target center in 3D world space:
        # Hover 0.18 meters above the physical wrist emitter plate along the gauntlet normal
        target_x = anchor_pos.x + wrist_up.x * 0.18 + wrist_forward.x * 0.03
        target_y = anchor_pos.y + wrist_up.y * 0.18 + wrist_forward.y * 0.03
        target_z = anchor_pos.z + wrist_up.z * 0.18 + wrist_forward.z * 0.03
        self.target_center = Vector3(float(target_x), float(target_y), float(target_z))

        # 2. Compute damped spring displacement (Parallax Lag)
        if self.parallax_enabled:
            # Displacement error vector from current position to target anchor
            dx = self.world_center.x - self.target_center.x
            dy = self.world_center.y - self.target_center.y
            dz = self.world_center.z - self.target_center.z

            # Spring acceleration: F_total = -k * displacement - c * velocity
            ax = -self.spring_stiffness * dx - self.spring_damping * self.spring_vel.x
            ay = -self.spring_stiffness * dy - self.spring_damping * self.spring_vel.y
            az = -self.spring_stiffness * dz - self.spring_damping * self.spring_vel.z

            # Euler integration for velocity and position
            self.spring_vel.x += ax * dt
            self.spring_vel.y += ay * dt
            self.spring_vel.z += az * dt

            self.world_center.x += self.spring_vel.x * dt
            self.world_center.y += self.spring_vel.y * dt
            self.world_center.z += self.spring_vel.z * dt

            # Constrain maximum spring stretch to avoid geometric detachment
            curr_dx = self.world_center.x - self.target_center.x
            curr_dy = self.world_center.y - self.target_center.y
            curr_dz = self.world_center.z - self.target_center.z
            dist_sq = curr_dx * curr_dx + curr_dy * curr_dy + curr_dz * curr_dz
            max_stretch = 0.14
            if dist_sq > max_stretch * max_stretch:
                stretch_dist = math.sqrt(dist_sq)
                scale = max_stretch / stretch_dist
                self.world_center.x = self.target_center.x + curr_dx * scale
                self.world_center.y = self.target_center.y + curr_dy * scale
                self.world_center.z = self.target_center.z + curr_dz * scale
                self.spring_vel.x *= 0.5
                self.spring_vel.y *= 0.5
                self.spring_vel.z *= 0.5

            self.current_offset = Vector3(
                float(self.world_center.x - self.target_center.x),
                float(self.world_center.y - self.target_center.y),
                float(self.world_center.z - self.target_center.z)
            )
        else:
            # Rigid lock without spring lag
            self.world_center.x = self.target_center.x
            self.world_center.y = self.target_center.y
            self.world_center.z = self.target_center.z
            self.spring_vel = Vector3(0.0, 0.0, 0.0)
            self.current_offset = Vector3(0.0, 0.0, 0.0)

        # 3. Orient the holographic screen to face the camera eye:
        to_cam_x = cam_pos.x - self.world_center.x
        to_cam_y = cam_pos.y - self.world_center.y
        to_cam_z = cam_pos.z - self.world_center.z
        cam_dist = math.sqrt(to_cam_x * to_cam_x + to_cam_y * to_cam_y + to_cam_z * to_cam_z)
        self.distance_to_cam = cam_dist

        if cam_dist > 0.0001:
            nx = to_cam_x / cam_dist
            ny = to_cam_y / cam_dist
            nz = to_cam_z / cam_dist
            self.normal = Vector3(float(nx), float(ny), float(nz))
        else:
            self.normal = Vector3(0.0, 0.0, 1.0)

        # Build orthonormal basis: Up is aligned with wrist up vector or world Y
        # Right = Cross(WorldUp, Normal)
        rx = -self.normal.z
        ry = 0.0
        rz = self.normal.x
        rmag = math.sqrt(rx * rx + rz * rz)
        if rmag > 0.0001:
            self.right_vec = Vector3(float(rx / rmag), 0.0, float(rz / rmag))
        else:
            self.right_vec = Vector3(1.0, 0.0, 0.0)

        # Up = Cross(Normal, Right)
        ux = self.normal.y * self.right_vec.z - self.normal.z * self.right_vec.y
        uy = self.normal.z * self.right_vec.x - self.normal.x * self.right_vec.z
        uz = self.normal.x * self.right_vec.y - self.normal.y * self.right_vec.x
        umag = math.sqrt(ux * ux + uy * uy + uz * uz)
        if umag > 0.0001:
            self.up_vec = Vector3(float(ux / umag), float(uy / umag), float(uz / umag))
        else:
            self.up_vec = Vector3(0.0, 1.0, 0.0)

        # Scanline phase and subtle quantum photonic flicker
        self.scanline_phase += dt * 4.0
        if self.scanline_phase > 1000.0:
            self.scanline_phase = 0.0
        self.flicker_alpha = 0.94 + 0.06 * math.sin(self.scanline_phase * 12.0)

        # Angle between surface normal and camera line of sight (foreshortening metric)
        dot_n_cam = self.normal.x * (to_cam_x / max(cam_dist, 0.001)) + \
                    self.normal.y * (to_cam_y / max(cam_dist, 0.001)) + \
                    self.normal.z * (to_cam_z / max(cam_dist, 0.001))
        dot_n_cam = max(-1.0, min(1.0, dot_n_cam))
        self.angle_to_cam_deg = math.degrees(math.acos(dot_n_cam))

    def get_corners(self):
        """
        Returns the 4 corners of the 3D quad in world space:
        [Top-Left, Top-Right, Bottom-Right, Bottom-Left].
        """
        hw = self.width * 0.5
        hh = self.height * 0.5

        # TL = Center - Right*hw + Up*hh
        tl = Vector3(
            float(self.world_center.x - self.right_vec.x * hw + self.up_vec.x * hh),
            float(self.world_center.y - self.right_vec.y * hw + self.up_vec.y * hh),
            float(self.world_center.z - self.right_vec.z * hw + self.up_vec.z * hh)
        )
        # TR = Center + Right*hw + Up*hh
        tr = Vector3(
            float(self.world_center.x + self.right_vec.x * hw + self.up_vec.x * hh),
            float(self.world_center.y + self.right_vec.y * hw + self.up_vec.y * hh),
            float(self.world_center.z + self.right_vec.z * hw + self.up_vec.z * hh)
        )
        # BR = Center + Right*hw - Up*hh
        br = Vector3(
            float(self.world_center.x + self.right_vec.x * hw - self.up_vec.x * hh),
            float(self.world_center.y + self.right_vec.y * hw - self.up_vec.y * hh),
            float(self.world_center.z + self.right_vec.z * hw - self.up_vec.z * hh)
        )
        # BL = Center - Right*hw - Up*hh
        bl = Vector3(
            float(self.world_center.x - self.right_vec.x * hw - self.up_vec.x * hh),
            float(self.world_center.y - self.right_vec.y * hw - self.up_vec.y * hh),
            float(self.world_center.z - self.right_vec.z * hw - self.up_vec.z * hh)
        )
        return [tl, tr, br, bl]

    def draw_3d_quad(self, texture_id: int):
        """
        Renders the holographic render texture onto the oriented 3D quad using rlgl.
        Applies OpenGL additive transparency and color tinting.
        """
        corners = self.get_corners()
        tl = corners[0]
        tr = corners[1]
        br = corners[2]
        bl = corners[3]

        alpha_int = int(220 * self.flicker_alpha)
        alpha_int = max(0, min(255, alpha_int))

        rl_set_texture(texture_id)
        rl_begin(RL_QUADS)
        
        # Render textured quad with cyan holographic luminescence
        rl_color4ub(180, 240, 255, alpha_int)

        # Top-Left (UV: 0, 1 for flipped FBO)
        rl_tex_coord2f(0.0, 1.0)
        rl_vertex3f(tl.x, tl.y, tl.z)

        # Top-Right (UV: 1, 1)
        rl_tex_coord2f(1.0, 1.0)
        rl_vertex3f(tr.x, tr.y, tr.z)

        # Bottom-Right (UV: 1, 0)
        rl_tex_coord2f(1.0, 0.0)
        rl_vertex3f(br.x, br.y, br.z)

        # Bottom-Left (UV: 0, 0)
        rl_tex_coord2f(0.0, 0.0)
        rl_vertex3f(bl.x, bl.y, bl.z)

        rl_end()
        rl_set_texture(0)

    def draw_3d_frame(self):
        """
        Draws glowing holographic wireframe boundaries and corner projector brackets.
        """
        corners = self.get_corners()
        tl = corners[0]
        tr = corners[1]
        br = corners[2]
        bl = corners[3]

        frame_color = Color(0, 240, 255, int(180 * self.flicker_alpha))
        draw_line_3d(tl, tr, frame_color)
        draw_line_3d(tr, br, frame_color)
        draw_line_3d(br, bl, frame_color)
        draw_line_3d(bl, tl, frame_color)

        # Corner brackets (notches at 12% length along each border)
        bracket_color = Color(255, 255, 255, int(220 * self.flicker_alpha))
        corner_len = 0.04
        
        # TL corner brackets
        draw_line_3d(tl, Vector3(tl.x + self.right_vec.x * corner_len, tl.y + self.right_vec.y * corner_len, tl.z + self.right_vec.z * corner_len), bracket_color)
        draw_line_3d(tl, Vector3(tl.x - self.up_vec.x * corner_len, tl.y - self.up_vec.y * corner_len, tl.z - self.up_vec.z * corner_len), bracket_color)

        # TR corner brackets
        draw_line_3d(tr, Vector3(tr.x - self.right_vec.x * corner_len, tr.y - self.right_vec.y * corner_len, tr.z - self.right_vec.z * corner_len), bracket_color)
        draw_line_3d(tr, Vector3(tr.x - self.up_vec.x * corner_len, tr.y - self.up_vec.y * corner_len, tr.z - self.up_vec.z * corner_len), bracket_color)

        # BR corner brackets
        draw_line_3d(br, Vector3(br.x - self.right_vec.x * corner_len, br.y - self.right_vec.y * corner_len, br.z - self.right_vec.z * corner_len), bracket_color)
        draw_line_3d(br, Vector3(br.x + self.up_vec.x * corner_len, br.y + self.up_vec.y * corner_len, br.z + self.up_vec.z * corner_len), bracket_color)

        # BL corner brackets
        draw_line_3d(bl, Vector3(bl.x + self.right_vec.x * corner_len, bl.y + self.right_vec.y * corner_len, bl.z + self.right_vec.z * corner_len), bracket_color)
        draw_line_3d(bl, Vector3(bl.x + self.up_vec.x * corner_len, bl.y + self.up_vec.y * corner_len, bl.z + self.up_vec.z * corner_len), bracket_color)

    def draw_projector_beams(self, emitter_nodes: list):
        """
        Draws 4 volumetric laser projector lines connecting physical wrist emitter
        pylons to the 4 corners of the floating holographic quad.
        """
        corners = self.get_corners()
        tl = corners[0]
        tr = corners[1]
        br = corners[2]
        bl = corners[3]

        beam_color = Color(0, 210, 255, int(110 * self.flicker_alpha))
        core_beam_color = Color(220, 255, 255, int(160 * self.flicker_alpha))

        targets = [bl, br, tr, tl]
        for i in range(4):
            if i < len(emitter_nodes):
                e_pos = emitter_nodes[i]
                t_pos = targets[i]
                draw_line_3d(e_pos, t_pos, beam_color)
                # Thin inner beam core for laser intensity
                mid_x = (e_pos.x + t_pos.x) * 0.5
                mid_y = (e_pos.y + t_pos.y) * 0.5
                mid_z = (e_pos.z + t_pos.z) * 0.5
                draw_line_3d(e_pos, Vector3(float(mid_x), float(mid_y), float(mid_z)), core_beam_color)


class WristGauntletModel:
    """
    Procedural Sci-Fi Exosuit Armature & Wrist Gauntlet.
    
    C++ / Architectural Mapping:
      struct ExosuitGauntlet {
          Vector3 elbow_position;
          Vector3 wrist_position;
          Vector3 emitter_nodes[4];
          float inspect_factor;
          Matrix transform;
      };
    
    Constructed from procedural geometric primitives (cylinders, cubes, joints):
      - Forearm Carbon-Alloy Chassis (slanted rectangular hull with copper heatsinks)
      - Elbow Joint & Forearm Cuff Servo
      - Armored Wrist Bracer & Articulated Hand Guard
      - 4 Corner Projector Emitter Pylons with glowing cyan photonic lenses
      - Telemetry Status LEDs (Power green, Comm link amber)
    """
    def __init__(self):
        self.wrist_pos = Vector3(0.0, 1.2, 3.5)
        self.elbow_pos = Vector3(0.2, 0.9, 3.8)
        self.inspect_factor = 0.0
        self.inspect_target = 0.0
        self.wrist_normal = Vector3(0.0, 1.0, 0.0)
        self.wrist_up = Vector3(0.0, 1.0, 0.0)
        self.wrist_forward = Vector3(0.0, 0.0, 1.0)
        self.wrist_right = Vector3(1.0, 0.0, 0.0)
        
        # 4 Projector Emitter Pylon World Positions
        self.emitter_nodes = []
        for _ in range(4):
            self.emitter_nodes.append(Vector3(0.0, 0.0, 0.0))

        # Materials & Color Palette
        self.col_hull = Color(24, 28, 38, 255)         # Armored matte dark alloy
        self.col_trim = Color(55, 65, 82, 255)         # Secondary chassis armor
        self.col_joint = Color(110, 120, 140, 255)     # Servo mechanics
        self.col_copper = Color(210, 105, 30, 255)     # Heatsink fin copper
        self.col_emitter = Color(0, 240, 255, 255)     # Glowing cyan emitter lens
        self.col_led_green = Color(40, 255, 120, 255)  # Power status LED
        self.col_led_amber = Color(255, 190, 30, 255)  # Data link status LED

    def update(self, dt: float, is_inspecting: bool, cam_pos: Vector3, cam_forward: Vector3, cam_right: Vector3, cam_up: Vector3):
        # 1. Smoothly interpolate inspect factor (0.0 = Lowered Ready, 1.0 = Inspect Focus)
        self.inspect_target = 1.0 if is_inspecting else 0.0
        self.inspect_factor = damp(self.inspect_factor, self.inspect_target, 11.0, dt)

        # 2. Local space offsets relative to first-person camera:
        # Lowered Ready: down and to the right side of the screen
        # Inspect Focus: raised up in front of the chest, angled toward player face
        local_x = lerp(0.26, 0.02, self.inspect_factor)
        local_y = lerp(-0.28, -0.15, self.inspect_factor)
        local_z = lerp(0.48, 0.42, self.inspect_factor)

        # Wrist world position
        wx = cam_pos.x + cam_right.x * local_x + cam_up.x * local_y + cam_forward.x * local_z
        wy = cam_pos.y + cam_right.y * local_x + cam_up.y * local_y + cam_forward.y * local_z
        wz = cam_pos.z + cam_right.z * local_x + cam_up.z * local_y + cam_forward.z * local_z
        self.wrist_pos = Vector3(float(wx), float(wy), float(wz))

        # Elbow position (placed behind and lower toward character shoulder)
        elbow_lx = local_x + 0.12
        elbow_ly = local_y - 0.28
        elbow_lz = local_z - 0.36
        ex = cam_pos.x + cam_right.x * elbow_lx + cam_up.x * elbow_ly + cam_forward.x * elbow_lz
        ey = cam_pos.y + cam_right.y * elbow_lx + cam_up.y * elbow_ly + cam_forward.y * elbow_lz
        ez = cam_pos.z + cam_right.z * elbow_lx + cam_up.z * elbow_ly + cam_forward.z * elbow_lz
        self.elbow_pos = Vector3(float(ex), float(ey), float(ez))

        # Orientation: In inspect mode, gauntlet top tilts toward camera eye
        # Wrist Normal points upward/inward toward camera
        arm_dir_x = self.wrist_pos.x - self.elbow_pos.x
        arm_dir_y = self.wrist_pos.y - self.elbow_pos.y
        arm_dir_z = self.wrist_pos.z - self.elbow_pos.z
        arm_len = math.sqrt(arm_dir_x * arm_dir_x + arm_dir_y * arm_dir_y + arm_dir_z * arm_dir_z)
        if arm_len > 0.001:
            self.wrist_forward = Vector3(float(arm_dir_x / arm_len), float(arm_dir_y / arm_len), float(arm_dir_z / arm_len))
        else:
            self.wrist_forward = cam_forward

        # Wrist Up Vector (normal of the emitter plate)
        # Blend between camera up and facing back to camera eye as inspect increases
        up_blend_y = lerp(cam_up.y, -cam_forward.y + 0.4, self.inspect_factor)
        up_blend_x = lerp(cam_up.x, -cam_forward.x, self.inspect_factor)
        up_blend_z = lerp(cam_up.z, -cam_forward.z, self.inspect_factor)
        up_mag = math.sqrt(up_blend_x * up_blend_x + up_blend_y * up_blend_y + up_blend_z * up_blend_z)
        if up_mag > 0.001:
            self.wrist_up = Vector3(float(up_blend_x / up_mag), float(up_blend_y / up_mag), float(up_blend_z / up_mag))
        else:
            self.wrist_up = cam_up

        # Wrist Right Vector = Cross(Forward, Up)
        wr_x = self.wrist_forward.y * self.wrist_up.z - self.wrist_forward.z * self.wrist_up.y
        wr_y = self.wrist_forward.z * self.wrist_up.x - self.wrist_forward.x * self.wrist_up.z
        wr_z = self.wrist_forward.x * self.wrist_up.y - self.wrist_forward.y * self.wrist_up.x
        wr_mag = math.sqrt(wr_x * wr_x + wr_y * wr_y + wr_z * wr_z)
        if wr_mag > 0.001:
            self.wrist_right = Vector3(float(wr_x / wr_mag), float(wr_y / wr_mag), float(wr_z / wr_mag))
        else:
            self.wrist_right = cam_right

        # 3. Calculate 4 Projector Emitter Pylon positions on gauntlet top plate
        ew = 0.065  # Half-width of emitter housing
        el = 0.050  # Half-length of emitter housing
        eh = 0.024  # Height elevation above wrist centerline

        # Base center of emitter housing on top of wrist
        base_x = self.wrist_pos.x + self.wrist_up.x * eh
        base_y = self.wrist_pos.y + self.wrist_up.y * eh
        base_z = self.wrist_pos.z + self.wrist_up.z * eh

        # Node 0: Bottom-Left (-R, -F)
        self.emitter_nodes[0] = Vector3(
            float(base_x - self.wrist_right.x * ew - self.wrist_forward.x * el),
            float(base_y - self.wrist_right.y * ew - self.wrist_forward.y * el),
            float(base_z - self.wrist_right.z * ew - self.wrist_forward.z * el)
        )
        # Node 1: Bottom-Right (+R, -F)
        self.emitter_nodes[1] = Vector3(
            float(base_x + self.wrist_right.x * ew - self.wrist_forward.x * el),
            float(base_y + self.wrist_right.y * ew - self.wrist_forward.y * el),
            float(base_z + self.wrist_right.z * ew - self.wrist_forward.z * el)
        )
        # Node 2: Top-Right (+R, +F)
        self.emitter_nodes[2] = Vector3(
            float(base_x + self.wrist_right.x * ew + self.wrist_forward.x * el),
            float(base_y + self.wrist_right.y * ew + self.wrist_forward.y * el),
            float(base_z + self.wrist_right.z * ew + self.wrist_forward.z * el)
        )
        # Node 3: Top-Left (-R, +F)
        self.emitter_nodes[3] = Vector3(
            float(base_x - self.wrist_right.x * ew + self.wrist_forward.x * el),
            float(base_y - self.wrist_right.y * ew + self.wrist_forward.y * el),
            float(base_z - self.wrist_right.z * ew + self.wrist_forward.z * el)
        )

    def draw_3d(self):
        """
        Renders the procedural 3D armored gauntlet using geometric primitives.
        """
        # Forearm Main Hull Cylinder / Segment
        mid_x = (self.elbow_pos.x + self.wrist_pos.x) * 0.5
        mid_y = (self.elbow_pos.y + self.wrist_pos.y) * 0.5
        mid_z = (self.elbow_pos.z + self.wrist_pos.z) * 0.5
        mid_forearm = Vector3(float(mid_x), float(mid_y), float(mid_z))

        # Main Armature Segment
        draw_line_3d(self.elbow_pos, self.wrist_pos, self.col_hull)
        draw_sphere(self.elbow_pos, 0.055, self.col_joint)
        draw_sphere(self.wrist_pos, 0.048, self.col_joint)

        # Dorsal Forearm Armor Plate (slanted box atop forearm)
        draw_cube(mid_forearm, 0.08, 0.06, 0.28, self.col_hull)
        draw_cube_wires(mid_forearm, 0.082, 0.062, 0.282, self.col_trim)

        # Copper Heatsink Ridges on forearm side
        draw_cube(Vector3(mid_x + self.wrist_right.x * 0.042, mid_y + self.wrist_right.y * 0.042, mid_z + self.wrist_right.z * 0.042), 0.015, 0.03, 0.16, self.col_copper)

        # Wrist Gauntlet Housing Pad (Emitter mount tray)
        tray_pos = Vector3(
            float(self.wrist_pos.x + self.wrist_up.x * 0.022),
            float(self.wrist_pos.y + self.wrist_up.y * 0.022),
            float(self.wrist_pos.z + self.wrist_up.z * 0.022)
        )
        draw_cube(tray_pos, 0.14, 0.025, 0.11, self.col_hull)
        draw_cube_wires(tray_pos, 0.142, 0.026, 0.112, self.col_trim)

        # Central Photonic Core Lens (recessed circle on tray)
        draw_sphere(tray_pos, 0.024, Color(0, 160, 240, 230))
        draw_sphere(tray_pos, 0.012, WHITE)

        # 4 Emitter Pylons with glowing cyan nodes
        for node in self.emitter_nodes:
            draw_cube(node, 0.014, 0.014, 0.014, self.col_joint)
            draw_sphere(node, 0.009, self.col_emitter)

        # Status LEDs on front bracer bevel
        led_green_pos = Vector3(
            float(tray_pos.x - self.wrist_right.x * 0.045 + self.wrist_forward.x * 0.052),
            float(tray_pos.y - self.wrist_right.y * 0.045 + self.wrist_forward.y * 0.052),
            float(tray_pos.z - self.wrist_right.z * 0.045 + self.wrist_forward.z * 0.052)
        )
        led_amber_pos = Vector3(
            float(tray_pos.x - self.wrist_right.x * 0.030 + self.wrist_forward.x * 0.052),
            float(tray_pos.y - self.wrist_right.y * 0.030 + self.wrist_forward.y * 0.052),
            float(tray_pos.z - self.wrist_right.z * 0.030 + self.wrist_forward.z * 0.052)
        )
        draw_sphere(led_green_pos, 0.005, self.col_led_green)
        draw_sphere(led_amber_pos, 0.005, self.col_led_amber)

        # Articulated Hand Guard / Glove Knuckle Shield
        knuckle_pos = Vector3(
            float(self.wrist_pos.x + self.wrist_forward.x * 0.08),
            float(self.wrist_pos.y + self.wrist_forward.y * 0.08),
            float(self.wrist_pos.z + self.wrist_forward.z * 0.08)
        )
        draw_cube(knuckle_pos, 0.09, 0.035, 0.07, self.col_hull)
        draw_cube_wires(knuckle_pos, 0.092, 0.036, 0.072, self.col_trim)


class TerminalState:
    """
    Simulated suit telemetry and weapon state driving the wrist terminal display.
    
    C++ / Architectural Mapping:
      struct SuitTelemetry {
          uint8_t active_tab;
          float health, max_health;
          float shield, max_shield;
          float oxygen_time;
          float core_temp;
          int plasma_ammo, max_ammo, reserve_ammo;
          uint8_t fire_mode;
          float radar_sweep_deg;
          float pressure_kpa;
          float radiation_msv;
          float heading_deg;
      };
    """
    def __init__(self):
        self.active_tab = TAB_VITALS
        self.tab_names = ["VITALS", "ARSENAL", "RADAR", "ENVIRONMENT"]

        # Vitals Subsystem
        self.health = 88.0
        self.max_health = 100.0
        self.shield = 125.0
        self.max_shield = 150.0
        self.oxygen_time = 418.0   # seconds
        self.core_temp = 38.6      # Celsius
        self.battery_pct = 94.0    # %
        self.heart_rate = 74       # BPM
        self.ekg_phase = 0.0
        self.shield_pulse = 0.0

        # Arsenal Subsystem
        self.plasma_ammo = 42
        self.max_ammo = 60
        self.reserve_ammo = 180
        self.heatsink_temp = 0.28   # 0.0 to 1.0 normalized
        self.fire_mode = FIRE_MODE_SEMI
        self.fire_mode_names = ["SEMI-AUTO", "3-RD BURST", "OVERCHARGE AUTO"]
        self.rounds_fired_total = 0

        # Tactical Radar Subsystem
        self.radar_range_m = 16.0   # 16-meter local coverage radius
        self.sweep_angle_deg = 0.0
        self.tracked_drones = []
        self.tracked_beacons = []
        self.closest_drone_dist = 99.0
        self.closest_drone_bearing = 0.0

        # Environmental Telemetry
        self.pressure_kpa = 101.32  # Standard Earth sea-level
        self.radiation_msv = 0.14   # Safe tier (< 0.50)
        self.temp_c = 21.4          # Ambient lab temperature
        self.gravity_g = 0.98       # Standard gravity
        self.air_purity = 99.6      # %
        self.heading_degrees = 0.0

    def cycle_tab(self, direction: int):
        self.active_tab = (self.active_tab + direction) % 4
        if self.active_tab < 0:
            self.active_tab = 3

    def set_tab(self, index: int):
        if 0 <= index <= 3:
            self.active_tab = index

    def cycle_fire_mode(self):
        self.fire_mode = (self.fire_mode + 1) % 3

    def fire_test_round(self):
        """Simulates plasma discharge with heatsink thermal build-up."""
        if self.plasma_ammo > 0:
            burst_count = 1
            if self.fire_mode == FIRE_MODE_BURST:
                burst_count = min(3, self.plasma_ammo)
            elif self.fire_mode == FIRE_MODE_AUTO:
                burst_count = min(5, self.plasma_ammo)

            self.plasma_ammo -= burst_count
            self.rounds_fired_total += burst_count
            self.heatsink_temp = min(1.0, self.heatsink_temp + 0.06 * burst_count)
        else:
            # Auto-reload from reserves
            reload_amount = min(self.max_ammo, self.reserve_ammo)
            self.plasma_ammo = reload_amount
            self.reserve_ammo -= reload_amount

    def update(self, dt: float, player_yaw_deg: float, player_pos: Vector3, world_drones: list, world_beacons: list):
        # 1. Vitals clock & rhythm
        self.oxygen_time = max(0.0, self.oxygen_time - dt * 0.15)
        self.ekg_phase += dt * (self.heart_rate / 60.0) * 6.28318
        if self.ekg_phase > 6283.18:
            self.ekg_phase = 0.0

        # Shield gentle ripple
        self.shield_pulse += dt * 3.0
        if self.shield_pulse > 1000.0:
            self.shield_pulse = 0.0

        # Cool down heatsink
        self.heatsink_temp = max(0.12, self.heatsink_temp - dt * 0.18)

        # 2. Radar sweep rotation (360 deg in 2.5 seconds = 144 deg/sec)
        self.sweep_angle_deg = (self.sweep_angle_deg + dt * 144.0) % 360.0

        # 3. Compass heading tracking
        self.heading_degrees = (player_yaw_deg) % 360.0
        if self.heading_degrees < 0.0:
            self.heading_degrees += 360.0

        # 4. Localized Tactical Radar Coordinate Projection:
        # Transforms each 3D world entity (Drone, Beacon) relative to the player's
        # world position and horizontal facing angle (heading).
        # C++ Formula:
        #   dx = X_entity - X_player; dz = Z_entity - Z_player;
        #   x_rad =  dx * cos(yaw) - dz * sin(yaw);
        #   y_rad =  dx * sin(yaw) + dz * cos(yaw);
        yaw_rad = math.radians(player_yaw_deg)
        cos_y = math.cos(yaw_rad)
        sin_y = math.sin(yaw_rad)

        self.tracked_drones = []
        min_dist = 999.0
        closest_bearing = 0.0

        for d in world_drones:
            dx = d.position.x - player_pos.x
            dz = d.position.z - player_pos.z
            dist = math.sqrt(dx * dx + dz * dz)
            
            # Rotate into player local heading space: Forward (+Z) is UP on radar
            rx = dx * cos_y - dz * sin_y
            ry = dx * sin_y + dz * cos_y

            # Angle relative to player nose (-180 to +180)
            bearing = math.degrees(math.atan2(rx, ry))

            # Store as plain dictionary (maps to C++ RadarBlip struct)
            blip = {
                "rel_x": rx,
                "rel_y": ry,
                "dist": dist,
                "bearing": bearing,
                "type": "drone",
                "id": d.drone_id
            }
            self.tracked_drones.append(blip)

            if dist < min_dist:
                min_dist = dist
                closest_bearing = bearing

        self.closest_drone_dist = min_dist
        self.closest_drone_bearing = closest_bearing

        self.tracked_beacons = []
        for b in world_beacons:
            dx = b.position.x - player_pos.x
            dz = b.position.z - player_pos.z
            dist = math.sqrt(dx * dx + dz * dz)
            rx = dx * cos_y - dz * sin_y
            ry = dx * sin_y + dz * cos_y
            bearing = math.degrees(math.atan2(rx, ry))

            b_blip = {
                "rel_x": rx,
                "rel_y": ry,
                "dist": dist,
                "bearing": bearing,
                "type": "beacon",
                "id": b.beacon_id
            }
            self.tracked_beacons.append(b_blip)


class HolographicTerminalRenderer:
    """
    Renders the interactive 512x384 terminal display into an offscreen RenderTexture2D.
    
    C++ / Architectural Mapping:
      Translates to an offscreen Framebuffer Object (FBO) rendered once per frame,
      whose texture ID is bound to the 3D oriented holographic quad.
    """
    def __init__(self):
        self.fbo = load_render_texture(HOLO_TEX_WIDTH, HOLO_TEX_HEIGHT)
        self.bg_color = Color(8, 14, 24, 255)
        self.grid_color = Color(16, 32, 54, 255)
        self.accent_cyan = Color(0, 220, 255, 255)
        self.accent_green = Color(40, 255, 130, 255)
        self.accent_amber = Color(255, 185, 30, 255)
        self.accent_red = Color(255, 60, 60, 255)
        self.text_dim = Color(120, 160, 195, 255)

    def unload(self):
        unload_render_texture(self.fbo)

    def render_content(self, state: TerminalState):
        """Draws all interface graphics into the offscreen RenderTexture."""
        begin_texture_mode(self.fbo)
        clear_background(self.bg_color)

        # 1. Subtle Background Holographic Grid Lines
        grid_step = 32
        for gx in range(0, HOLO_TEX_WIDTH, grid_step):
            draw_line(gx, 0, gx, HOLO_TEX_HEIGHT, self.grid_color)
        for gy in range(0, HOLO_TEX_HEIGHT, grid_step):
            draw_line(0, gy, HOLO_TEX_WIDTH, gy, self.grid_color)

        # Subtle scanline overlay
        for sy in range(0, HOLO_TEX_HEIGHT, 4):
            draw_line(0, sy, HOLO_TEX_WIDTH, sy, Color(0, 0, 0, 35))

        # 2. Top Header & Tab Navigation Bar
        draw_rectangle(0, 0, HOLO_TEX_WIDTH, 42, Color(12, 22, 38, 240))
        draw_line(0, 42, HOLO_TEX_WIDTH, 42, self.accent_cyan)

        # Tab Buttons [VITALS] [ARSENAL] [RADAR] [ENVIRONMENT]
        tab_w = int(HOLO_TEX_WIDTH / 4)
        for i in range(4):
            tx = i * tab_w
            is_active = (i == state.active_tab)
            if is_active:
                draw_rectangle(tx + 2, 4, tab_w - 4, 34, Color(0, 75, 120, 200))
                draw_rectangle_lines(tx + 2, 4, tab_w - 4, 34, self.accent_cyan)
                draw_line(tx + 4, 37, tx + tab_w - 4, 37, WHITE)
                draw_text(f"[{i+1}] {state.tab_names[i]}", tx + 8, 14, 11, WHITE)
            else:
                draw_rectangle(tx + 2, 4, tab_w - 4, 34, Color(16, 26, 42, 140))
                draw_rectangle_lines(tx + 2, 4, tab_w - 4, 34, Color(35, 60, 90, 255))
                draw_text(f"[{i+1}] {state.tab_names[i]}", tx + 8, 14, 11, self.text_dim)

        # 3. Active Tab Content Rendering
        if state.active_tab == TAB_VITALS:
            self._render_tab_vitals(state)
        elif state.active_tab == TAB_ARSENAL:
            self._render_tab_arsenal(state)
        elif state.active_tab == TAB_RADAR:
            self._render_tab_radar(state)
        elif state.active_tab == TAB_ENVIRONMENT:
            self._render_tab_environment(state)

        # 4. Bottom System Status Bar
        draw_rectangle(0, HOLO_TEX_HEIGHT - 26, HOLO_TEX_WIDTH, 26, Color(10, 18, 32, 240))
        draw_line(0, HOLO_TEX_HEIGHT - 26, HOLO_TEX_WIDTH, HOLO_TEX_HEIGHT - 26, Color(30, 60, 95, 255))
        draw_text("HOLO-LINK: STABLE", 14, HOLO_TEX_HEIGHT - 18, 10, self.accent_green)
        draw_text("FREQ: 433.92 MHz", 170, HOLO_TEX_HEIGHT - 18, 10, self.text_dim)
        draw_text(f"BATT: {int(state.battery_pct)}%", 330, HOLO_TEX_HEIGHT - 18, 10, self.accent_cyan)
        draw_text("[Q/E or LB/RB: TABS]", 400, HOLO_TEX_HEIGHT - 18, 10, self.accent_amber)

        end_texture_mode()

    def _render_tab_vitals(self, state: TerminalState):
        """Tab 0: Health, Kinetic Shield, Oxygen Countdown, and EKG Waveform."""
        # Section Header
        draw_text("OPERATOR BIOMETRICS & EXOSUIT INTEGRITY", 20, 52, 13, self.accent_cyan)

        # 1. Health Bar (Green segmented)
        draw_text(f"HULL HEALTH: {int(state.health)} / {int(state.max_health)} HP", 24, 76, 12, WHITE)
        draw_rectangle(24, 94, 210, 20, Color(14, 24, 38, 255))
        draw_rectangle_lines(24, 94, 210, 20, Color(40, 75, 115, 255))
        hp_fill_w = int(206 * (state.health / state.max_health))
        draw_rectangle(26, 96, hp_fill_w, 16, self.accent_green)

        # Health Segments
        for seg in range(1, 10):
            draw_line(24 + seg * 21, 94, 24 + seg * 21, 114, Color(10, 20, 30, 200))

        # 2. Kinetic Shield Bar (Cyan Ripple)
        draw_text(f"KINETIC SHIELD: {int(state.shield)} / {int(state.max_shield)} SHD", 260, 76, 12, WHITE)
        draw_rectangle(260, 94, 210, 20, Color(14, 24, 38, 255))
        draw_rectangle_lines(260, 94, 210, 20, Color(40, 75, 115, 255))
        shd_fill_w = int(206 * (state.shield / state.max_shield))
        draw_rectangle(262, 96, shd_fill_w, 16, self.accent_cyan)
        for seg in range(1, 10):
            draw_line(260 + seg * 21, 94, 260 + seg * 21, 114, Color(10, 20, 30, 200))

        # 3. Life Support Oxygen Countdown
        draw_rectangle(24, 130, 210, 80, Color(12, 22, 36, 180))
        draw_rectangle_lines(24, 130, 210, 80, Color(45, 80, 125, 255))
        draw_text("LIFE SUPPORT O2", 34, 138, 11, self.text_dim)
        mins = int(state.oxygen_time) // 60
        secs = int(state.oxygen_time) % 60
        draw_text(f"{mins:02d}:{secs:02d} REMAINING", 34, 156, 15, self.accent_cyan)
        draw_text("SCRUBBERS: NOMINAL (99.6%)", 34, 184, 10, self.accent_green)

        # 4. Core Wattage & Suit Temperature
        draw_rectangle(260, 130, 210, 80, Color(12, 22, 36, 180))
        draw_rectangle_lines(260, 130, 210, 80, Color(45, 80, 125, 255))
        draw_text("CORE REACTOR TEMP", 270, 138, 11, self.text_dim)
        draw_text(f"{state.core_temp:.1f} °C", 270, 156, 16, self.accent_green)
        draw_text("OUTPUT: 4.82 kW STABLE", 270, 184, 10, self.text_dim)

        # 5. Dynamic EKG Oscilloscope Waveform Box
        draw_rectangle(24, 226, 446, 110, Color(10, 18, 30, 220))
        draw_rectangle_lines(24, 226, 446, 110, Color(0, 160, 220, 255))
        draw_text(f"CARDIAC PULSE: {state.heart_rate} BPM", 34, 234, 11, self.accent_green)

        # Centerline grid for EKG
        draw_line(24, 281, 470, 281, Color(20, 45, 70, 255))

        # Synthetic ECG Waveform rendering (P-Q-R-S-T wave model)
        prev_x = 24
        prev_y = 281
        wave_pts = 70
        step_w = 446.0 / wave_pts

        for i in range(wave_pts):
            sample_t = state.ekg_phase + i * 0.12
            # Base heartbeat spike
            mod_t = sample_t % 6.28318
            spike = 0.0
            if 1.4 < mod_t < 1.6:
                spike = -18.0 * math.sin((mod_t - 1.4) * 15.7)
            elif 1.6 <= mod_t < 1.8:
                spike = 38.0 * math.sin((mod_t - 1.6) * 15.7)
            elif 1.8 <= mod_t < 2.0:
                spike = -12.0 * math.sin((mod_t - 1.8) * 15.7)

            curr_x = int(24 + i * step_w)
            curr_y = int(281 + spike)
            draw_line(prev_x, prev_y, curr_x, curr_y, self.accent_green)
            prev_x = curr_x
            prev_y = curr_y

    def _render_tab_arsenal(self, state: TerminalState):
        """Tab 1: Plasma ammunition counter, heatsink thermal bar, fire mode selector."""
        draw_text("ORDNANCE & WEAPON SYSTEMS TELEMETRY", 20, 52, 13, self.accent_cyan)

        # Weapon Name Box
        draw_rectangle(24, 74, 464, 42, Color(12, 22, 38, 200))
        draw_rectangle_lines(24, 74, 464, 42, Color(45, 80, 125, 255))
        draw_text("PRIMARY ARM: MK-IV FOCUSED ION LANCE", 36, 82, 12, WHITE)
        draw_text(f"FIRE MODE: {state.fire_mode_names[state.fire_mode]} [CLICK / [A] TO CYCLE]", 36, 98, 10, self.accent_amber)

        # Huge Digital Ammo Display
        draw_rectangle(24, 126, 210, 110, Color(12, 22, 38, 200))
        draw_rectangle_lines(24, 126, 210, 110, Color(45, 80, 125, 255))
        draw_text("PLASMA AMMO", 36, 136, 11, self.text_dim)
        draw_text(f"{state.plasma_ammo:02d}", 36, 154, 42, self.accent_cyan if state.plasma_ammo > 10 else self.accent_red)
        draw_text(f"/ {state.max_ammo} (RESERVE: {state.reserve_ammo})", 108, 178, 11, self.text_dim)
        draw_text(f"TOTAL SHOTS FIRED: {state.rounds_fired_total}", 36, 210, 10, self.text_dim)

        # Cartridge Ammo Grid (3 rows of 20 cells)
        draw_rectangle(248, 126, 240, 110, Color(12, 22, 38, 200))
        draw_rectangle_lines(248, 126, 240, 110, Color(45, 80, 125, 255))
        draw_text("MAGAZINE CELL ARRAY", 258, 136, 11, self.text_dim)

        cell_idx = 0
        for row in range(3):
            for col in range(20):
                cx = 258 + col * 11
                cy = 158 + row * 18
                if cell_idx < state.plasma_ammo:
                    draw_rectangle(cx, cy, 8, 14, self.accent_cyan)
                else:
                    draw_rectangle(cx, cy, 8, 14, Color(25, 38, 55, 255))
                    draw_rectangle_lines(cx, cy, 8, 14, Color(40, 60, 85, 255))
                cell_idx += 1

        # Thermal Heatsink Dissipation Gauge
        draw_rectangle(24, 250, 464, 76, Color(12, 22, 38, 200))
        draw_rectangle_lines(24, 250, 464, 76, Color(45, 80, 125, 255))
        draw_text("THERMAL HEATSINK HEAT LOAD", 36, 258, 11, self.text_dim)

        heat_pct = int(state.heatsink_temp * 100.0)
        draw_text(f"{heat_pct}% TEMPERATURE", 340, 258, 11, self.accent_amber if heat_pct > 60 else self.accent_green)
        draw_rectangle(36, 278, 436, 22, Color(16, 26, 42, 255))
        draw_rectangle_lines(36, 278, 436, 22, Color(40, 75, 115, 255))

        fill_w = int(432 * state.heatsink_temp)
        bar_col = self.accent_green
        if state.heatsink_temp > 0.8:
            bar_col = self.accent_red
        elif state.heatsink_temp > 0.5:
            bar_col = self.accent_amber
        draw_rectangle(38, 280, fill_w, 18, bar_col)

        draw_text("VENTING SYSTEM: LIQUID HELIUM RE-CIRCULATOR ACTIVE", 36, 308, 10, self.text_dim)

    def _render_tab_radar(self, state: TerminalState):
        """Tab 2: Localized 3D Tactical Radar displaying drone blips and waypoints."""
        draw_text("LOCAL TACTICAL SCANNER (16m PROJECTION)", 20, 52, 13, self.accent_cyan)

        radar_cx = 160
        radar_cy = 195
        radar_r = 120

        # Radar Base Circle & Concentric Rings (5m, 10m, 15m)
        draw_circle(radar_cx, radar_cy, radar_r, Color(10, 20, 34, 240))
        draw_circle_lines(radar_cx, radar_cy, radar_r, self.accent_cyan)
        draw_circle_lines(radar_cx, radar_cy, int(radar_r * 0.66), Color(25, 75, 115, 255))
        draw_circle_lines(radar_cx, radar_cy, int(radar_r * 0.33), Color(20, 60, 95, 255))

        # Crosshairs
        draw_line(radar_cx - radar_r, radar_cy, radar_cx + radar_r, radar_cy, Color(20, 55, 85, 255))
        draw_line(radar_cx, radar_cy - radar_r, radar_cx, radar_cy + radar_r, Color(20, 55, 85, 255))

        # Cardinal Labels
        draw_text("N", radar_cx - 4, radar_cy - radar_r + 4, 10, self.accent_cyan)
        draw_text("S", radar_cx - 4, radar_cy + radar_r - 14, 10, self.text_dim)
        draw_text("W", radar_cx - radar_r + 4, radar_cy - 5, 10, self.text_dim)
        draw_text("E", radar_cx + radar_r - 12, radar_cy - 5, 10, self.text_dim)

        # Rotating Sweep Beam Line
        sw_rad = math.radians(state.sweep_angle_deg)
        sw_x = radar_cx + int(radar_r * math.cos(sw_rad))
        sw_y = radar_cy + int(radar_r * math.sin(sw_rad))
        draw_line(radar_cx, radar_cy, sw_x, sw_y, Color(0, 240, 255, 180))

        # Draw Player Marker at Center
        draw_circle(radar_cx, radar_cy, 4.0, WHITE)
        draw_circle_lines(radar_cx, radar_cy, 6.0, self.accent_cyan)

        # Draw Tracked Entity Blips on Radar
        scale_px_per_m = radar_r / state.radar_range_m

        # 1. Beacons (Amber Triangles)
        for b in state.tracked_beacons:
            bx = radar_cx + int(b["rel_x"] * scale_px_per_m)
            by = radar_cy - int(b["rel_y"] * scale_px_per_m)  # -Y because screen Y goes down
            # Clamp inside radar radius
            cdx = bx - radar_cx
            cdy = by - radar_cy
            cdist = math.sqrt(cdx * cdx + cdy * cdy)
            if cdist < radar_r - 4:
                draw_circle(bx, by, 3.5, self.accent_amber)
                draw_circle_lines(bx, by, 6.0, Color(255, 190, 40, 160))

        # 2. Drones (Cyan Diamonds)
        for d in state.tracked_drones:
            dx = radar_cx + int(d["rel_x"] * scale_px_per_m)
            dy = radar_cy - int(d["rel_y"] * scale_px_per_m)
            cdx = dx - radar_cx
            cdy = dy - radar_cy
            cdist = math.sqrt(cdx * cdx + cdy * cdy)
            if cdist < radar_r - 4:
                draw_rectangle(dx - 3, dy - 3, 7, 7, self.accent_cyan)
                draw_rectangle_lines(dx - 5, dy - 5, 11, 11, Color(0, 255, 255, 140))
                draw_text(f"D{d['id']}", dx + 7, dy - 5, 9, WHITE)

        # Radar Readout Telemetry Box on Right
        draw_rectangle(300, 74, 188, 250, Color(12, 22, 38, 200))
        draw_rectangle_lines(300, 74, 188, 250, Color(45, 80, 125, 255))
        draw_text("RADAR TELEMETRY", 312, 86, 11, self.accent_cyan)
        draw_text(f"RANGE: {int(state.radar_range_m)} METERS", 312, 108, 10, self.text_dim)
        draw_text(f"DRONES: {len(state.tracked_drones)} CONTACTS", 312, 128, 11, WHITE)
        draw_text(f"BEACONS: {len(state.tracked_beacons)} WAYPOINTS", 312, 148, 11, self.accent_amber)
        
        draw_line(312, 172, 476, 172, Color(35, 60, 95, 255))
        draw_text("NEAREST CONTACT:", 312, 184, 10, self.text_dim)
        draw_text(f"{state.closest_drone_dist:.1f} METERS", 312, 202, 14, self.accent_cyan)
        draw_text(f"BEARING: {state.closest_drone_bearing:+.1f}°", 312, 224, 11, self.accent_green)
        draw_text("TRACKING: ACTIVE LOCK", 312, 250, 10, self.accent_green)

    def _render_tab_environment(self, state: TerminalState):
        """Tab 3: Compass tape, barometric pressure, radiation hazard, ambient atmosphere."""
        draw_text("ATMOSPHERIC & ENVIRONMENTAL SENSORS", 20, 52, 13, self.accent_cyan)

        # 1. 360-Degree Horizontal Compass Tape
        draw_rectangle(24, 74, 464, 46, Color(12, 22, 38, 220))
        draw_rectangle_lines(24, 74, 464, 46, Color(45, 80, 125, 255))

        center_tape_x = 256
        heading = state.heading_degrees

        # Draw compass degree ticks
        for deg in range(0, 360, 15):
            diff = (deg - heading + 180.0) % 360.0 - 180.0
            tx = int(center_tape_x + diff * 3.2)
            if 30 <= tx <= 480:
                is_cardinal = (deg % 90 == 0)
                is_sub = (deg % 45 == 0)
                tick_h = 16 if is_cardinal else (10 if is_sub else 6)
                draw_line(tx, 118 - tick_h, tx, 118, Color(90, 140, 195, 255))

                if is_cardinal:
                    card_names = {0: "N", 90: "E", 180: "S", 270: "W"}
                    cname = card_names.get(deg, "")
                    draw_text(cname, tx - 4, 82, 12, self.accent_cyan)
                elif is_sub:
                    sub_names = {45: "NE", 135: "SE", 225: "SW", 315: "NW"}
                    sname = sub_names.get(deg, "")
                    draw_text(sname, tx - 6, 84, 10, self.text_dim)

        # Center Reticle Needle for Compass
        draw_triangle(
            Vector2(float(center_tape_x), 118.0),
            Vector2(float(center_tape_x - 5), 110.0),
            Vector2(float(center_tape_x + 5), 110.0),
            self.accent_amber
        )
        draw_text(f"{int(heading)}°", center_tape_x - 10, 124, 11, WHITE)

        # 2. Atmospheric Barometer & Pressure
        draw_rectangle(24, 146, 210, 90, Color(12, 22, 38, 200))
        draw_rectangle_lines(24, 146, 210, 90, Color(45, 80, 125, 255))
        draw_text("BAROMETRIC PRESSURE", 34, 156, 11, self.text_dim)
        draw_text(f"{state.pressure_kpa:.2f} kPa", 34, 174, 16, self.accent_cyan)
        draw_text("AIR MIX: 78% N2, 21% O2", 34, 198, 10, self.text_dim)
        draw_text("STATUS: PRESSURIZED / SAFE", 34, 214, 10, self.accent_green)

        # 3. Ambient Radiation Dosimeter
        draw_rectangle(260, 146, 210, 90, Color(12, 22, 38, 200))
        draw_rectangle_lines(260, 146, 210, 90, Color(45, 80, 125, 255))
        draw_text("RADIATION DOSIMETER", 270, 156, 11, self.text_dim)
        draw_text(f"{state.radiation_msv:.2f} mSv/h", 270, 174, 16, self.accent_green)
        
        # Hazard Level Bar
        draw_rectangle(270, 200, 180, 12, Color(16, 26, 42, 255))
        rad_w = int(180 * min(1.0, state.radiation_msv / 1.0))
        draw_rectangle(270, 200, rad_w, 12, self.accent_green)
        draw_text("TIER 1 BACKGROUND LEVEL", 270, 216, 9, self.text_dim)

        # 4. Planetary Gravity & Ambient Temperature
        draw_rectangle(24, 250, 464, 74, Color(12, 22, 38, 200))
        draw_rectangle_lines(24, 250, 464, 74, Color(45, 80, 125, 255))
        draw_text(f"LOCAL GRAVITATIONAL FIELD: {state.gravity_g:.2f} G", 36, 262, 11, WHITE)
        draw_text(f"AMBIENT TEMPERATURE: {state.temp_c:.1f} °C (STABLE)", 36, 282, 11, self.accent_cyan)
        draw_text("CHAMBER CONTAINMENT FIELD: 100% OPERATIONAL", 36, 302, 10, self.accent_green)


# ==============================================================================
# BLOCK 2: WORLD SIMULATION & ENTITIES
# ==============================================================================

class ResearchChamber:
    """
    3D Sci-Fi Testing & Calibration Chamber.
    A high-tech 20m x 20m arena with grid floors, warning borders, corner pillars,
    and wall boundary containment.
    """
    def __init__(self):
        self.half_size = 9.5
        self.wall_height = 4.5
        self.col_floor = Color(14, 18, 28, 255)
        self.col_grid = Color(28, 42, 65, 255)
        self.col_pillar = Color(35, 42, 58, 255)
        self.col_light = Color(0, 220, 255, 220)
        self.col_hazard = Color(240, 180, 30, 200)

    def clamp_bounds(self, pos: Vector3):
        """Clamps the player inside the chamber walls."""
        pos.x = max(-self.half_size + 0.8, min(self.half_size - 0.8, pos.x))
        pos.z = max(-self.half_size + 0.8, min(self.half_size - 0.8, pos.z))

    def draw_3d(self):
        """Renders the physical 3D environment geometry."""
        # 1. Floor Grid
        draw_grid(20, 1.0)

        # 2. Central Holographic Pedestal / Anchor Plate
        draw_cylinder(Vector3(0.0, 0.05, 0.0), 1.8, 2.0, 0.1, 16, self.col_pillar)
        draw_cylinder_wires(Vector3(0.0, 0.05, 0.0), 1.82, 2.02, 0.102, 16, self.col_light)

        # 3. 4 Corner Observation Pillars with vertical light bars
        corners = [
            (-self.half_size, -self.half_size),
            ( self.half_size, -self.half_size),
            ( self.half_size,  self.half_size),
            (-self.half_size,  self.half_size)
        ]
        for cx, cz in corners:
            pillar_pos = Vector3(float(cx), float(self.wall_height * 0.5), float(cz))
            draw_cube(pillar_pos, 1.2, float(self.wall_height), 1.2, self.col_pillar)
            draw_cube_wires(pillar_pos, 1.22, float(self.wall_height), 1.22, Color(50, 70, 100, 255))
            # Glowing light slit on pillar face
            draw_line_3d(
                Vector3(float(cx), 0.2, float(cz)),
                Vector3(float(cx), float(self.wall_height - 0.2), float(cz)),
                self.col_light
            )

        # 4. Perimeter Containment Rails
        hs = self.half_size
        col_rail = Color(40, 55, 80, 255)
        draw_line_3d(Vector3(-hs, 1.0, -hs), Vector3( hs, 1.0, -hs), col_rail)
        draw_line_3d(Vector3( hs, 1.0, -hs), Vector3( hs, 1.0,  hs), col_rail)
        draw_line_3d(Vector3( hs, 1.0,  hs), Vector3(-hs, 1.0,  hs), col_rail)
        draw_line_3d(Vector3(-hs, 1.0,  hs), Vector3(-hs, 1.0, -hs), col_rail)


class SensorDrone:
    """
    Autonomous hovering sensor drone wandering inside the 3D research chamber.
    Reuses procedural 3D model drawing from assets.models_3d.drone.
    """
    def __init__(self, drone_id: int, start_x: float, start_z: float):
        self.drone_id = drone_id
        self.position = Vector3(float(start_x), 1.5, float(start_z))
        self.target_pos = Vector3(float(start_x), 1.5, float(start_z))
        self.yaw = random.uniform(0.0, 360.0)
        self.anim_timer = random.uniform(0.0, 10.0)
        self.speed = 1.6
        self.dwell_timer = 0.0

    def pick_new_target(self):
        self.target_pos = Vector3(
            float(random.uniform(-7.5, 7.5)),
            float(random.uniform(1.2, 2.2)),
            float(random.uniform(-7.5, 7.5))
        )

    def update(self, dt: float):
        self.anim_timer += dt
        
        # Steer toward target waypoint
        dx = self.target_pos.x - self.position.x
        dy = self.target_pos.y - self.position.y
        dz = self.target_pos.z - self.position.z
        dist = math.sqrt(dx * dx + dz * dz)

        if dist > 0.4:
            move_step = self.speed * dt
            self.position.x += (dx / dist) * move_step
            self.position.y += (dy / max(dist, 0.1)) * (move_step * 0.4)
            self.position.z += (dz / dist) * move_step
            self.yaw = math.degrees(math.atan2(dx, dz))
        else:
            self.dwell_timer += dt
            if self.dwell_timer > 2.0:
                self.dwell_timer = 0.0
                self.pick_new_target()

    def draw_3d(self):
        """Draws procedural 3D sentinel drone using assets library."""
        draw_drone_enemy_3d(self.position, self.yaw, self.anim_timer, 0.65)


class WaypointBeacon:
    """
    Stationary calibration beacon pedestal positioned in the chamber.
    """
    def __init__(self, beacon_id: int, pos_x: float, pos_z: float):
        self.beacon_id = beacon_id
        self.position = Vector3(float(pos_x), 0.0, float(pos_z))
        self.pulse_timer = random.uniform(0.0, 6.28)

    def update(self, dt: float):
        self.pulse_timer += dt * 3.0
        if self.pulse_timer > 1000.0:
            self.pulse_timer = 0.0

    def draw_3d(self):
        pulse = 0.8 + 0.2 * math.sin(self.pulse_timer)
        # Pedestal base
        draw_cylinder(self.position, 0.35, 0.45, 0.7, 12, Color(35, 45, 60, 255))
        # Glowing beacon energy sphere
        core_pos = Vector3(self.position.x, 0.95, self.position.z)
        draw_sphere(core_pos, 0.16 * pulse, Color(255, 185, 30, 255))
        draw_sphere(core_pos, 0.08, WHITE)


class FirstPersonPlayer:
    """
    First-person player avatar navigating the 3D chamber.
    Controls camera position, yaw, pitch, and inspect state.
    """
    def __init__(self):
        self.position = Vector3(0.0, 1.6, 4.0)
        self.yaw = 0.0       # Horizontal angle in radians (0 = looking along +Z)
        self.pitch = 0.0     # Vertical angle in radians (clamped to +/- 75 deg)
        self.is_inspecting = False
        self.sticky_inspect = False
        self.walk_speed = 3.6
        self.turn_speed = 2.4

    def update(self, dt: float, move_vec: Vector2, look_vec: Vector2, mouse_delta: Vector2, inspect_held: bool, toggle_sticky: bool):
        # 1. Inspect mode toggling
        if toggle_sticky:
            self.sticky_inspect = not self.sticky_inspect
        self.is_inspecting = inspect_held or self.sticky_inspect

        # 2. Camera Rotation (Simultaneous Mouse + Gamepad Right Stick + Arrow Keys)
        # Mouse look
        mouse_sens = 0.0028
        self.yaw -= mouse_delta.x * mouse_sens
        self.pitch -= mouse_delta.y * mouse_sens

        # Gamepad / Arrow Keys Look
        self.yaw -= look_vec.x * self.turn_speed * dt
        self.pitch -= look_vec.y * self.turn_speed * dt

        # Clamp vertical pitch to +/- 75 degrees (-1.31 to +1.31 radians)
        self.pitch = max(-1.31, min(1.31, self.pitch))

        # 3. Walking Movement (WASD + Left Stick + D-Pad)
        # Forward vector in horizontal plane
        fwd_x = math.sin(self.yaw)
        fwd_z = math.cos(self.yaw)
        # Right vector in horizontal plane
        rgt_x = math.cos(self.yaw)
        rgt_z = -math.sin(self.yaw)

        # move_vec.y is negative for Up/W, positive for Down/S
        # move_vec.x is negative for Left/A, positive for Right/D
        vx = (rgt_x * move_vec.x - fwd_x * move_vec.y) * self.walk_speed
        vz = (rgt_z * move_vec.x - fwd_z * move_vec.y) * self.walk_speed

        self.position.x += vx * dt
        self.position.z += vz * dt

    def get_camera(self):
        cam = Camera3D()
        cam.position = self.position
        
        # Compute camera target from yaw and pitch
        look_x = math.sin(self.yaw) * math.cos(self.pitch)
        look_y = math.sin(self.pitch)
        look_z = math.cos(self.yaw) * math.cos(self.pitch)
        
        cam.target = Vector3(
            float(self.position.x + look_x),
            float(self.position.y + look_y),
            float(self.position.z + look_z)
        )
        cam.up = Vector3(0.0, 1.0, 0.0)
        cam.fovy = 65.0
        cam.projection = CAMERA_PERSPECTIVE
        return cam

    def get_forward(self):
        look_x = math.sin(self.yaw) * math.cos(self.pitch)
        look_y = math.sin(self.pitch)
        look_z = math.cos(self.yaw) * math.cos(self.pitch)
        return Vector3(float(look_x), float(look_y), float(look_z))

    def get_right(self):
        rx = math.cos(self.yaw)
        rz = -math.sin(self.yaw)
        return Vector3(float(rx), 0.0, float(rz))

    def get_up(self):
        fwd = self.get_forward()
        rgt = self.get_right()
        # Up = Cross(Right, Forward)
        ux = rgt.y * fwd.z - rgt.z * fwd.y
        uy = rgt.z * fwd.x - rgt.x * fwd.z
        uz = rgt.x * fwd.y - rgt.y * fwd.x
        return Vector3(float(ux), float(uy), float(uz))


# ==============================================================================
# BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY
# ==============================================================================

class XRayTelemetryOverlay:
    """
    Pattern X-Ray Inspector & Projection Geometry Telemetry.
    Visualizes internal vector math, harmonic spring states, and coordinate pipelines.
    """
    def __init__(self):
        self.col_panel_bg = Color(10, 16, 28, 240)
        self.col_border = Color(0, 220, 255, 255)
        self.col_header = Color(0, 255, 220, 255)
        self.col_text = Color(180, 210, 240, 255)
        self.col_val = Color(255, 255, 255, 255)
        self.col_amber = Color(255, 190, 40, 255)
        self.col_green = Color(50, 255, 130, 255)

    def draw_2d_panel(
        self,
        holo_plane: HolographicProjectionPlane,
        gauntlet: WristGauntletModel,
        state: TerminalState,
        player: FirstPersonPlayer,
        is_diegetic: bool,
        parallax_enabled: bool
    ):
        """Draws the transparent analytical readout panel on the left viewport."""
        px = 24
        py = 58
        pw = 410
        ph = 638

        draw_rectangle(px, py, pw, ph, self.col_panel_bg)
        draw_rectangle_lines(px, py, pw, ph, self.col_border)

        # Title
        draw_text("=== DIEGETIC INTERFACE X-RAY TELEMETRY ===", px + 14, py + 14, 13, self.col_header)

        # 1. Core Architecture State
        draw_text("PATTERN CONFIGURATION:", px + 14, py + 38, 11, self.col_amber)
        mode_str = "DIEGETIC 3D WORLD-SPACE" if is_diegetic else "FLAT 2D SCREEN-SPACE HUD"
        draw_text(f"  [F1] Mode         : {mode_str}", px + 14, py + 54, 11, self.col_val)
        par_str = "DAMPED SPRING (k=145, c=15)" if parallax_enabled else "RIGID ATTACHED (LOCKED)"
        draw_text(f"  [F2] Parallax Lag : {par_str}", px + 14, py + 70, 11, self.col_val)
        insp_str = "INSPECT FOCUS (100%)" if gauntlet.inspect_factor > 0.85 else f"LOWERED READY ({int(gauntlet.inspect_factor*100)}%)"
        draw_text(f"  Gauntlet Armature : {insp_str}", px + 14, py + 86, 11, self.col_green)

        # 2. 3D World Transform Math
        draw_line(px + 14, py + 108, px + pw - 14, py + 108, Color(40, 75, 115, 255))
        draw_text("3D PROJECTION PLANE TRANSFORM:", px + 14, py + 116, 11, self.col_amber)
        c = holo_plane.world_center
        draw_text(f"  World Center : ({c.x:+.3f}, {c.y:+.3f}, {c.z:+.3f}) m", px + 14, py + 132, 11, self.col_val)
        n = holo_plane.normal
        draw_text(f"  Normal Vector: ({n.x:+.3f}, {n.y:+.3f}, {n.z:+.3f})", px + 14, py + 148, 11, self.col_val)
        draw_text(f"  Dimensions   : {holo_plane.width:.2f}m x {holo_plane.height:.2f}m (4:3 Aspect)", px + 14, py + 164, 11, self.col_val)
        draw_text(f"  Camera Dist  : {holo_plane.distance_to_cam:.3f} m", px + 14, py + 180, 11, self.col_val)
        draw_text(f"  Tilt to Eye  : {holo_plane.angle_to_cam_deg:.1f}° (Foreshortening)", px + 14, py + 196, 11, self.col_green)

        # 3. Harmonic Oscillator Spring Telemetry
        draw_line(px + 14, py + 218, px + pw - 14, py + 218, Color(40, 75, 115, 255))
        draw_text("SECOND-ORDER SPRING LAG DYNAMICS:", px + 14, py + 226, 11, self.col_amber)
        off = holo_plane.current_offset
        draw_text(f"  Displacement Δ: ({off.x:+.4f}, {off.y:+.4f}, {off.z:+.4f}) m", px + 14, py + 242, 11, self.col_val)
        vel = holo_plane.spring_vel
        vel_mag = math.sqrt(vel.x * vel.x + vel.y * vel.y + vel.z * vel.z)
        draw_text(f"  Spring Vel |v|: {vel_mag:.4f} m/s", px + 14, py + 258, 11, self.col_val)
        draw_text("  ODE Equation  : a = -145*Δx - 15*v", px + 14, py + 274, 11, self.col_text)

        # 4. Localized Tactical Radar Projection Pipeline
        draw_line(px + 14, py + 296, px + pw - 14, py + 296, Color(40, 75, 115, 255))
        draw_text("RADAR COORDINATE PROJECTION PIPELINE:", px + 14, py + 304, 11, self.col_amber)
        draw_text(f"  Player World Pos: ({player.position.x:+.2f}, {player.position.z:+.2f})", px + 14, py + 320, 11, self.col_val)
        draw_text(f"  Heading (Yaw)   : {state.heading_degrees:.1f}°", px + 14, py + 336, 11, self.col_val)
        draw_text(f"  Tracked Targets : {len(state.tracked_drones)} Drones, {len(state.tracked_beacons)} Beacons", px + 14, py + 352, 11, self.col_val)
        draw_text("  Projection Math : X_rad = dx*cosθ - dz*sinθ", px + 14, py + 368, 11, self.col_text)
        draw_text("                    Y_rad = dx*sinθ + dz*cosθ", px + 14, py + 384, 11, self.col_text)

        # 5. Graphics & Rendering Metrics
        draw_line(px + 14, py + 406, px + pw - 14, py + 406, Color(40, 75, 115, 255))
        draw_text("RENDER PIPELINE SPECIFICATIONS:", px + 14, py + 414, 11, self.col_amber)
        draw_text(f"  Offscreen FBO : {HOLO_TEX_WIDTH} x {HOLO_TEX_HEIGHT} (RGBA8)", px + 14, py + 430, 11, self.col_val)
        draw_text("  3D Primitive  : rlgl RL_QUADS + Normal Texture", px + 14, py + 446, 11, self.col_val)
        draw_text("  Alpha Blending: Additive Translucent Holo", px + 14, py + 462, 11, self.col_val)
        draw_text("  Projector Rigs: 4 Volumetric Ray Beams", px + 14, py + 478, 11, self.col_green)

        # Pedagogical notes
        draw_line(px + 14, py + 500, px + pw - 14, py + 500, Color(40, 75, 115, 255))
        draw_text("ARCHITECTURAL TAKEAWAYS:", px + 14, py + 508, 11, self.col_header)
        draw_text("1. Eliminates HUD disconnect by rooting UI", px + 14, py + 524, 10, self.col_text)
        draw_text("   into character skeleton bones.", px + 14, py + 538, 10, self.col_text)
        draw_text("2. Spring damping provides organic mass & delay.", px + 14, py + 554, 10, self.col_text)
        draw_text("3. Preserves spatial presence during locomotion.", px + 14, py + 570, 10, self.col_text)
        draw_text("[Tab] Close X-Ray | [F1] Toggle Diegetic/2D", px + 14, py + 602, 11, self.col_amber)

    def draw_3d_gizmos(self, holo_plane: HolographicProjectionPlane, drones: list, beacons: list):
        """Draws 3D spatial debug vectors (normals, projection frustums, radar tracking rays)."""
        # 1. Surface normal vector line from hologram center
        c = holo_plane.world_center
        n = holo_plane.normal
        normal_end = Vector3(float(c.x + n.x * 0.25), float(c.y + n.y * 0.25), float(c.z + n.z * 0.25))
        draw_line_3d(c, normal_end, Color(255, 60, 180, 255))
        draw_sphere(normal_end, 0.012, Color(255, 60, 180, 255))

        # 2. Radar Target Tracking Lines: Connect each drone to the wrist hologram
        for d in drones:
            draw_line_3d(c, d.position, Color(0, 240, 255, 60))


# ==============================================================================
# BLOCK 4: MAIN GAME LOOP & AUTOMATED SMOKE TEST
# ==============================================================================

class PatternLabGame:
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()

        # Audio synthesizer
        self.sfx = SoundLibrary()
        self.sfx.init_defaults()

        # Core subsystems
        self.terminal_renderer = HolographicTerminalRenderer()
        self.state = TerminalState()
        self.chamber = ResearchChamber()
        self.player = FirstPersonPlayer()
        self.gauntlet = WristGauntletModel()
        self.holo_plane = HolographicProjectionPlane()
        self.xray_overlay = XRayTelemetryOverlay()

        # Autonomous world entities
        self.drones = []
        drone_coords = [(-4.5, -3.5), (4.5, -2.5), (-3.0, 5.0), (3.5, 4.0)]
        for i in range(4):
            cx, cz = drone_coords[i]
            self.drones.append(SensorDrone(i + 1, cx, cz))

        self.beacons = []
        beacon_coords = [(-6.0, -6.0), (6.0, -6.0), (0.0, 6.5)]
        for i in range(3):
            bx, bz = beacon_coords[i]
            self.beacons.append(WaypointBeacon(i + 1, bx, bz))

        # Pattern experiment flags
        self.show_xray = True          # Default ON in single-pattern labs (Rule 5)
        self.pattern_enabled = True    # True = Diegetic 3D World-Space, False = Flat 2D Screen HUD
        self.parallax_enabled = True   # Parallax spring delay active

    def reset(self):
        """Resets the simulation state to initial conditions."""
        self.player = FirstPersonPlayer()
        self.state = TerminalState()
        self.holo_plane = HolographicProjectionPlane()
        self.sfx.play("select", 0.6)

    def update(self):
        dt = min(get_frame_time(), 0.05)

        # 1. Dual Input Toggles
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
            self.sfx.play("click", 0.6)

        if is_dual_pattern_toggle_pressed():
            self.pattern_enabled = not self.pattern_enabled
            self.sfx.play("select", 0.7)

        if is_dual_secondary_toggle_pressed():
            self.parallax_enabled = not self.parallax_enabled
            self.holo_plane.parallax_enabled = self.parallax_enabled
            self.sfx.play("select", 0.7)

        if is_dual_reset_pressed():
            self.reset()

        # 2. Interactive Terminal Tab Cycling (Q/E, 1-4, LB/RB, D-Pad Left/Right)
        if is_key_pressed(KEY_Q) or (get_active_gamepad_id() >= 0 and is_gamepad_button_pressed(get_active_gamepad_id(), GAMEPAD_BUTTON_LEFT_TRIGGER_1)):
            self.state.cycle_tab(-1)
            self.sfx.play("click", 0.5)
        elif is_key_pressed(KEY_E) or (get_active_gamepad_id() >= 0 and is_gamepad_button_pressed(get_active_gamepad_id(), GAMEPAD_BUTTON_RIGHT_TRIGGER_1)):
            self.state.cycle_tab(1)
            self.sfx.play("click", 0.5)

        if is_key_pressed(KEY_ONE):
            self.state.set_tab(TAB_VITALS)
            self.sfx.play("click", 0.5)
        elif is_key_pressed(KEY_TWO):
            self.state.set_tab(TAB_ARSENAL)
            self.sfx.play("click", 0.5)
        elif is_key_pressed(KEY_THREE):
            self.state.set_tab(TAB_RADAR)
            self.sfx.play("click", 0.5)
        elif is_key_pressed(KEY_FOUR):
            self.state.set_tab(TAB_ENVIRONMENT)
            self.sfx.play("click", 0.5)

        # 3. Primary Action: Cycle fire mode in Arsenal, test pulse in Vitals
        if is_dual_primary_fire_pressed():
            if self.state.active_tab == TAB_ARSENAL:
                self.state.cycle_fire_mode()
                self.state.fire_test_round()
                self.sfx.play("laser", 0.5)
            elif self.state.active_tab == TAB_VITALS:
                self.state.shield = min(self.state.max_shield, self.state.shield + 10.0)
                self.sfx.play("select", 0.6)

        # 4. Player Locomotion & Camera Control
        move_2d = get_dual_move_2d()
        look_2d = get_dual_look_2d()
        
        # Mouse look: track cursor deltas if cursor moved
        mouse_delta = get_mouse_delta()
        if not is_mouse_button_down(MOUSE_BUTTON_LEFT) and abs(mouse_delta.x) + abs(mouse_delta.y) > 0.0:
            pass  # Normal free look

        inspect_held = is_key_down(KEY_SPACE) or is_gamepad_trigger_down(is_right_trigger=False) or is_gamepad_trigger_down(is_right_trigger=True)
        toggle_sticky = is_key_pressed(KEY_C)

        self.player.update(dt, move_2d, look_2d, mouse_delta, inspect_held, toggle_sticky)
        self.chamber.clamp_bounds(self.player.position)

        # 5. Autonomous Entities Update
        for d in self.drones:
            d.update(dt)
        for b in self.beacons:
            b.update(dt)

        # 6. Gauntlet & Holographic Projection Update
        cam_forward = self.player.get_forward()
        cam_right = self.player.get_right()
        cam_up = self.player.get_up()

        self.gauntlet.update(dt, self.player.is_inspecting, self.player.position, cam_forward, cam_right, cam_up)
        self.holo_plane.update(dt, self.gauntlet.wrist_pos, self.player.position, self.gauntlet.wrist_up, self.gauntlet.wrist_forward)

        # 7. Simulation Telemetry & Offscreen Texture Rendering
        player_yaw_deg = math.degrees(self.player.yaw)
        self.state.update(dt, player_yaw_deg, self.player.position, self.drones, self.beacons)
        self.terminal_renderer.render_content(self.state)

    def draw(self):
        begin_drawing()
        clear_background(Color(10, 14, 24, 255))

        # =====================================================================
        # 3D WORLD RENDERING
        # =====================================================================
        cam = self.player.get_camera()
        begin_mode_3d(cam)

        # 1. Physical Environment & Architecture
        self.chamber.draw_3d()

        # 2. Beacons & Drones
        for b in self.beacons:
            b.draw_3d()
        for d in self.drones:
            d.draw_3d()

        # 3. Diegetic Armature & Holographic Terminal (When Pattern is ENABLED)
        if self.pattern_enabled:
            # Mechanical Gauntlet Model
            self.gauntlet.draw_3d()

            # Volumetric Projector Beams connecting gauntlet emitter nodes to hologram
            self.holo_plane.draw_projector_beams(self.gauntlet.emitter_nodes)

            # 3D Textured Hologram Quad
            self.holo_plane.draw_3d_quad(self.terminal_renderer.fbo.texture.id)

            # Holographic Boundary Wireframes & Corner Brackets
            self.holo_plane.draw_3d_frame()

            # 3D X-Ray Gizmos (Normal vectors, radar tracking rays)
            if self.show_xray:
                self.xray_overlay.draw_3d_gizmos(self.holo_plane, self.drones, self.beacons)

        end_mode_3d()

        # =====================================================================
        # 2D COMPARISON HUD: FLAT SCREEN-SPACE HUD (When Pattern is DISABLED)
        # =====================================================================
        if not self.pattern_enabled:
            # Draw the terminal texture pinned directly to the screen corner
            # Demonstrates traditional non-diegetic HUD presentation without spatial presence
            hud_w = 420
            hud_h = 315
            hud_x = SCREEN_WIDTH - hud_w - 30
            hud_y = SCREEN_HEIGHT - hud_h - 30

            draw_rectangle(hud_x - 4, hud_y - 28, hud_w + 8, hud_h + 32, Color(8, 14, 24, 230))
            draw_rectangle_lines(hud_x - 4, hud_y - 28, hud_w + 8, hud_h + 32, Color(255, 60, 60, 255))
            draw_text("TRADITIONAL 2D FLAT SCREEN-SPACE HUD [NON-DIEGETIC]", hud_x + 8, hud_y - 22, 11, Color(255, 80, 80, 255))

            # FBO textures in Raylib are vertically flipped, so source height is negative
            src_rec = Rectangle(0.0, 0.0, float(HOLO_TEX_WIDTH), float(-HOLO_TEX_HEIGHT))
            dst_rec = Rectangle(float(hud_x), float(hud_y), float(hud_w), float(hud_h))
            draw_texture_pro(self.terminal_renderer.fbo.texture, src_rec, dst_rec, Vector2(0.0, 0.0), 0.0, WHITE)

        # =====================================================================
        # 2D HUD OVERLAY & X-RAY TELEMETRY
        # =====================================================================
        # Top-bar Header Information
        draw_text("DIEGETIC WRIST COMM 3D", 24, 20, 14, Color(0, 240, 255, 255))
        
        mode_label = "MODE: [F1] DIEGETIC 3D WORLD-SPACE" if self.pattern_enabled else "MODE: [F1] FLAT 2D SCREEN-SPACE HUD"
        mode_color = Color(0, 255, 140, 255) if self.pattern_enabled else Color(255, 100, 100, 255)
        draw_text(mode_label, 230, 21, 11, mode_color)

        # Controls banner at bottom
        draw_rectangle(0, SCREEN_HEIGHT - 28, SCREEN_WIDTH, 28, Color(12, 16, 26, 230))
        draw_text(
            "WASD/Stick: Move | Mouse/Look: Aim | Space/Triggers: Inspect Wrist | Q/E or 1-4: Tabs | [Tab]: X-Ray | [F1]: Toggle Diegetic/2D | [F2]: Parallax Lag | [R]: Reset",
            24, SCREEN_HEIGHT - 20, 11, Color(145, 175, 210, 255)
        )

        # X-Ray Telemetry Panel
        if self.show_xray:
            self.xray_overlay.draw_2d_panel(
                self.holo_plane,
                self.gauntlet,
                self.state,
                self.player,
                self.pattern_enabled,
                self.parallax_enabled
            )

        # Global UI / Controller Status (Always keep 450..980 clear for dropdown bar)
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)

        end_drawing()

    def run(self, smoke_test: bool = False):
        frame_count = 0
        while not window_should_close():
            self.update()
            self.draw()
            frame_count += 1
            if smoke_test and frame_count >= 3:
                break

        # Resource cleanup
        self.terminal_renderer.unload()
        self.sfx.unload_all()
        close_audio_device()
        close_window()


if __name__ == "__main__":
    is_smoke = "--smoke-test" in sys.argv
    PatternLabGame().run(smoke_test=is_smoke)
