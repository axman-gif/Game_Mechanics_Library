# -*- coding: utf-8 -*-
"""
Skill Web - Node Graph & Prerequisite Validation Pipeline
=========================================================
Section          : 3.1 Menus & UI
Pattern Category : Menus & User Interface, RPG Progression & Economy
Dimension        : 2D

Problem Solved:
  In RPGs, action games, and MMOs (Path of Exile, Diablo, Final Fantasy Sphere Grid,
  World of Warcraft, Skyrim), character progression relies on deep, branching skill
  trees and webs. Naively tracking skills with loose boolean flags causes illegal unlocks
  (skipping prerequisites), state corruption, and severe refund exploits (e.g. allocating
  Root -> Branch -> Keystone, then refunding the Root while keeping the Keystone!).
  Furthermore, without structured Directed Acyclic Graph (DAG) reachability validation,
  implementing multi-parent hybrid prerequisites or mutual exclusions becomes brittle spaghetti.

How the Pattern Works:
  1. Directed Acyclic Graph (DAG) Node Topology:
     Skills are organized as an explicit adjacency graph of `SkillNode` structs holding:
       - `node_id`, `name`, `branch`, `max_points`, `current_points`
       - `prerequisites: List[int]` (parent IDs that must be satisfied)
       - `stat_modifier_type`, `stat_bonus_per_point`
       - `position: Vector2` (spatial layout coordinates for visual graph rendering)
  2. 4-State Visual Lifecycle:
     Every node dynamically computes its active state:
       - LOCKED    : Prerequisites not met (dim slate, padlock indicator).
       - AVAILABLE : Prerequisites satisfied, points available in purse (pulsing gold rim).
       - INVESTED  : At least 1 point allocated (active branch theme color).
       - MAXED     : Maximum points allocated (radiant gold border and energy glint).
  3. DAG Orphan Protection (Anti-Refund Exploit Algorithm):
     When the player attempts to refund a point from an invested node, the engine executes
     a temporary simulation:
       - Tentatively decrement target node points.
       - Execute a Breadth-First Search (BFS) reachability traversal from the Root nodes.
       - If any other invested node becomes orphaned (disconnected from roots), the refund
         is REJECTED atomically with clear diagnostic feedback!
  4. Pure Derived Stat Calculation Pipeline:
     Character stats (HP, ATK, DEF, SPD, CRIT) are completely derived on-demand by summing
     all currently allocated node modifiers:
       Stat = Base_Value + sum(node.current_points * node.bonus)
     This eliminates floating-point drift, save-file corruption, and attribute desync.
  5. Interactive Pattern Comparison ([F1] & [F2]):
     - [F1]: Toggle Strict DAG Prerequisite Gating (ON) vs Freeform Unlocked Allocator (OFF).
     - [F2]: Toggle Mutual Exclusion Archetype Gating (e.g. Bloodthirst vs Colossus Aegis).

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - Left / Right / Up / Down (WASD / Arrows / Gamepad Stick / D-Pad) : Spatial node cursor traversal
  - Mouse Hover / Left Click on Node                                : Select / Focus node
  - Enter / Space / Gamepad A / Click Allocate                      : Allocate +1 Skill Point
  - Backspace / Right Click / Gamepad B / Click Refund              : Refund -1 Skill Point (with DAG orphan check)
  - [P] / Gamepad X                                                 : Grant +5 Skill Points for testing
  - [Tab] / Gamepad View (Select)                                   : Toggle X-Ray Telemetry & DAG Reachability Inspector
  - [F1]  / Gamepad LB                                              : Toggle Pattern ON/OFF (Strict DAG Gating vs Freeform)
  - [F2]  / Gamepad RB                                              : Toggle Mutual Exclusion Keystone Lockout
  - [Ctrl +/-]                                                      : Increase / Decrease UI Font Size
  - [F11]                                                           : Toggle Fullscreen
  - [R]   / Gamepad Start                                           : Full Respec (Refund All Allocated Points)
"""

import sys
import os
import math
from typing import List, Dict, Set, Optional

# 1. Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# 2. Add repository root to search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# 3. Mandatory Raylib & modular workspace imports
from pyray import *
from assets import *
from utils import *

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WINDOW_TITLE = "Skill Web - Node Graph & Prerequisite Validation (Raylib Pattern Lab)"

# UI Palette Constants
COLOR_BG               = Color(10, 14, 24, 255)
COLOR_PANEL_BG         = Color(16, 22, 36, 252)
COLOR_PANEL_BORDER     = Color(42, 58, 92, 255)
COLOR_CANVAS_GRID      = Color(20, 28, 48, 160)
COLOR_SLOT_BORDER      = Color(38, 50, 78, 255)

COLOR_TEXT_MAIN        = Color(235, 242, 255, 255)
COLOR_TEXT_DIM         = Color(135, 155, 185, 255)
COLOR_GOLD_ACCENT      = Color(255, 205, 55, 255)
COLOR_CYAN_ACCENT      = Color(45, 215, 255, 255)
COLOR_GREEN_READY      = Color(65, 245, 130, 255)
COLOR_RED_ERROR        = Color(255, 75, 75, 255)
COLOR_WHITE            = Color(255, 255, 255, 255)

# Branch Theme Colors
BRANCH_ROOT     = 0
BRANCH_OFFENSE  = 1
BRANCH_AGILITY  = 2
BRANCH_DEFENSE  = 3
BRANCH_HYBRID   = 4

BRANCH_NAMES = ["Origin", "Juggernaut (Offense)", "Windstrider (Agility)", "Bulwark (Defense)", "Nexus (Hybrid)"]
BRANCH_COLORS = [
    Color(255, 215, 60, 255),   # Origin: Bright Gold
    Color(255, 80, 80, 255),    # Offense: Crimson Vermilion
    Color(65, 225, 140, 255),   # Agility: Emerald Green
    Color(70, 160, 255, 255),   # Defense: Cobalt Sapphire
    Color(215, 95, 255, 255),   # Hybrid: Arcane Violet
]

# Node Lifecycle States (C++ Enum equivalent)
STATE_LOCKED    = 0  # Prerequisites missing
STATE_AVAILABLE = 1  # Prerequisites satisfied, points in purse
STATE_INVESTED  = 2  # Has >= 1 point, but not maxed
STATE_MAXED     = 3  # Maximum points invested

# Stat Types (C++ Enum equivalent)
STAT_HP    = 0
STAT_ATK   = 1
STAT_DEF   = 2
STAT_SPD   = 3
STAT_CRIT  = 4

STAT_NAMES = ["Max Health", "Attack Power", "Armor Defense", "Move Speed", "Critical Strike"]
STAT_UNITS = ["HP", "ATK", "DEF", "SPD", "%"]

# Layout Geometry
CANVAS_X = 25
CANVAS_Y = 60
CANVAS_W = 840
CANVAS_H = 645

DESK_X   = 885
DESK_Y   = 60
DESK_W   = 370
DESK_H   = 645


# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATION (SKILL NODE & GRAPH REACHABILITY)
# ==============================================================================

class SkillNode:
    """
    Plain struct representing a skill or passive perk node in the graph.
    C++ Equivalent:
      struct SkillNode {
          int node_id;
          char name[32];
          int branch;
          int icon_type;
          int max_points;
          int current_points;
          float x, y;
          int stat_type;
          float stat_bonus_per_point;
          int prerequisite_count;
          int prerequisites[4];
          int conflict_node_id;
      };
    """
    def __init__(
        self,
        node_id: int,
        name: str,
        branch: int,
        icon_type: int,
        max_points: int,
        x: float,
        y: float,
        stat_type: int,
        stat_bonus_per_point: float,
        prerequisites: List[int],
        lore: str,
        conflict_node_id: int = -1
    ):
        self.node_id = node_id
        self.name = name
        self.branch = branch
        self.icon_type = icon_type
        self.max_points = max_points
        self.current_points = 0
        self.x = x
        self.y = y
        self.stat_type = stat_type
        self.stat_bonus_per_point = stat_bonus_per_point
        self.prerequisites = prerequisites
        self.lore = lore
        self.conflict_node_id = conflict_node_id

    def is_active(self) -> bool:
        return self.current_points > 0

    def is_maxed(self) -> bool:
        return self.current_points >= self.max_points


class SkillWebGraph:
    """
    Directed Acyclic Graph (DAG) validation engine.
    Executes prerequisite checks, BFS reachability tests, and orphan-protection.
    """
    def __init__(self, nodes: List[SkillNode]):
        self.nodes = nodes
        self.node_map: Dict[int, SkillNode] = {}
        self.root_ids = []
        for n in nodes:
            self.node_map[n.node_id] = n
            if len(n.prerequisites) == 0:
                self.root_ids.append(n.node_id)

        # Configurable pattern toggles
        self.strict_gating_enabled = True       # Pattern ON: Strict DAG verification vs OFF: Freeform cheat
        self.mutual_exclusion_enabled = True     # Mutual exclusion lockouts between opposite keystones

    def get_node_state(self, node: SkillNode, available_points: int) -> int:
        """Evaluates the 4-state visual lifecycle of a node."""
        if node.is_maxed():
            return STATE_MAXED
        if node.is_active():
            return STATE_INVESTED

        if not self.strict_gating_enabled:
            return STATE_AVAILABLE if available_points > 0 else STATE_LOCKED

        # Verify all prerequisites are satisfied
        can_unlock = self.are_prerequisites_satisfied(node)
        if can_unlock and available_points > 0:
            return STATE_AVAILABLE
        return STATE_LOCKED

    def are_prerequisites_satisfied(self, node: SkillNode) -> bool:
        """Verifies that all parent prerequisite nodes have at least 1 point."""
        if not self.strict_gating_enabled:
            return True

        # Check mutual exclusion conflict
        if self.mutual_exclusion_enabled and node.conflict_node_id != -1:
            conflict = self.node_map.get(node.conflict_node_id)
            if conflict and conflict.is_active():
                return False

        if len(node.prerequisites) == 0:
            return True

        for parent_id in node.prerequisites:
            parent = self.node_map.get(parent_id)
            if not parent or parent.current_points <= 0:
                return False
        return True

    def can_allocate_point(self, node: SkillNode, available_points: int) -> Tuple[bool, str]:
        """Precondition check for point allocation."""
        if available_points <= 0:
            return False, "No available Skill Points remaining."
        if node.current_points >= node.max_points:
            return False, "Node has already reached maximum rank."

        if self.mutual_exclusion_enabled and node.conflict_node_id != -1:
            conflict = self.node_map.get(node.conflict_node_id)
            if conflict and conflict.is_active():
                return False, f"Locked! Mutually exclusive with '{conflict.name}'."

        if not self.are_prerequisites_satisfied(node):
            return False, "Prerequisites not met: Parent nodes must be invested first."

        return True, "Ready to allocate."

    def can_refund_point(self, node: SkillNode) -> Tuple[bool, str]:
        """
        Anti-Refund Exploit Algorithm (DAG Orphan Protection):
        Simulates the refund and runs BFS reachability from root nodes.
        If any currently active node loses its path to the roots, reject the refund!
        """
        if node.current_points <= 0:
            return False, "No points invested in this node to refund."

        # Cannot refund origin root node
        if len(node.prerequisites) == 0:
            return False, "Cannot refund the foundational Origin Keystone."

        if not self.strict_gating_enabled:
            return True, "Freeform mode: Refund allowed."

        # If node has more than 1 point, reducing it to >= 1 still keeps all children connected!
        if node.current_points > 1:
            return True, "Safe to refund rank."

        # Node has exactly 1 point. Refunding it deactivates the node.
        # Check if any child depends on this node being active.
        direct_active_children = []
        for other in self.nodes:
            if other.node_id != node.node_id and other.is_active():
                if node.node_id in other.prerequisites:
                    direct_active_children.append(other)

        if not direct_active_children:
            return True, "No active children depend on this node."

        # Algorithmic BFS reachability simulation
        # Create virtual points map where target node has 0 points
        virtual_points = {}
        for n in self.nodes:
            virtual_points[n.node_id] = n.current_points
        virtual_points[node.node_id] = 0

        # Run BFS from roots
        reachable_active: Set[int] = set()
        queue = []
        for r_id in self.root_ids:
            if virtual_points.get(r_id, 0) > 0:
                queue.append(r_id)

        visited = set(queue)
        while queue:
            cur_id = queue.pop(0)
            reachable_active.add(cur_id)

            # Find all nodes that list cur_id as a prerequisite
            for cand in self.nodes:
                if cand.node_id not in visited and virtual_points.get(cand.node_id, 0) > 0:
                    # Check if all prerequisites of cand are satisfied under virtual state
                    all_req_ok = True
                    for parent_id in cand.prerequisites:
                        if parent_id not in reachable_active:
                            all_req_ok = False
                            break
                    if all_req_ok:
                        visited.add(cand.node_id)
                        queue.append(cand.node_id)

        # Verify if every invested node is still reachable
        for other in self.nodes:
            if other.node_id != node.node_id and other.is_active():
                if other.node_id not in reachable_active:
                    return False, f"DAG Violation: Refunding this node would orphan '{other.name}'!"

        return True, "Safe to refund."


# ==============================================================================
# BLOCK 2: WORLD SIMULATION & ENTITIES (GRAPH TOPOLOGY & DERIVED STATS)
# ==============================================================================

def create_skill_web_nodes() -> List[SkillNode]:
    """
    Constructs the 17-node interconnected skill web graph across 3 thematic wings.
    Coordinates are normalized to the Canvas region (840x645).
    """
    nodes = [
        # Origin Keystone (Root)
        SkillNode(0, "Adventurer's Origin", BRANCH_ROOT, 0, 1, 420.0, 560.0,
                  STAT_HP, 20.0, [], "The humble origin of every legend. Unlocks adjacent branches."),

        # Tier 1 Primaries
        SkillNode(1, "Strike Mastery", BRANCH_OFFENSE, 1, 3, 260.0, 470.0,
                  STAT_ATK, 4.0, [0], "Hones edge alignment and swing momentum. +4 Attack per point."),
        SkillNode(2, "Fleet Footed", BRANCH_AGILITY, 2, 3, 420.0, 450.0,
                  STAT_SPD, 5.0, [0], "Lightens footsteps and improves gait. +5 Move Speed per point."),
        SkillNode(3, "Iron Skin", BRANCH_DEFENSE, 3, 3, 580.0, 470.0,
                  STAT_DEF, 3.0, [0], "Hardens muscles and bone density. +3 Defense per point."),

        # Tier 2 Intermediates & Hybrids
        SkillNode(4, "Heavy Impact", BRANCH_OFFENSE, 4, 3, 160.0, 370.0,
                  STAT_ATK, 6.0, [1], "Concussive strikes stagger defensive foes. +6 Attack per point."),
        SkillNode(5, "Battle Cry", BRANCH_HYBRID, 5, 2, 310.0, 360.0,
                  STAT_HP, 15.0, [1, 2], "Roaring shout inspiring combat vigor. +15 Health per point."),
        SkillNode(6, "Windrunner", BRANCH_AGILITY, 6, 3, 420.0, 340.0,
                  STAT_CRIT, 2.5, [2], "Channels tailwinds into sprint speed. +2.5% Crit Chance per point."),
        SkillNode(7, "Steadfast Guard", BRANCH_HYBRID, 7, 2, 530.0, 360.0,
                  STAT_DEF, 4.0, [2, 3], "Immovable posture repelling incoming blows. +4 Defense per point."),
        SkillNode(8, "Fortify", BRANCH_DEFENSE, 8, 3, 680.0, 370.0,
                  STAT_HP, 20.0, [3], "Reinforces vital organs with stone grit. +20 Health per point."),

        # Tier 3 Advanced Masteries
        SkillNode(9, "Cleave", BRANCH_OFFENSE, 8, 3, 130.0, 250.0,
                  STAT_ATK, 8.0, [4], "Wide sweeping swings cleaving multiple foes. +8 Attack per point."),
        SkillNode(10, "Riposte Nexus", BRANCH_HYBRID, 9, 2, 290.0, 240.0,
                  STAT_CRIT, 3.0, [5], "Fluid parry counter-attacks. +3% Crit Chance per point."),
        SkillNode(11, "Quick Reflexes", BRANCH_AGILITY, 10, 3, 420.0, 220.0,
                  STAT_SPD, 7.0, [6], "Instantaneous reaction timing. +7 Move Speed per point."),
        SkillNode(12, "Shield Wall", BRANCH_DEFENSE, 11, 3, 710.0, 250.0,
                  STAT_DEF, 6.0, [8], "Locking shields to form an impenetrable redoubt. +6 Defense per point."),
        SkillNode(13, "Vanguard Bastion", BRANCH_HYBRID, 12, 2, 550.0, 240.0,
                  STAT_HP, 25.0, [7], "Imposing forward shield line. +25 Health per point."),

        # Tier 4 Apex Keystones (1-point Masteries with Mutual Exclusions)
        SkillNode(14, "Bloodthirst Avatar", BRANCH_OFFENSE, 13, 1, 160.0, 115.0,
                  STAT_ATK, 25.0, [9, 10], "Apex Berserker: All attacks leech life and deal +25 Attack.",
                  conflict_node_id=16),
        SkillNode(15, "Tempest Avatar", BRANCH_AGILITY, 14, 1, 420.0, 100.0,
                  STAT_CRIT, 12.0, [11], "Apex Strider: Move like a lightning gale. +12% Crit, +15 Speed."),
        SkillNode(16, "Colossus Aegis", BRANCH_DEFENSE, 15, 1, 680.0, 115.0,
                  STAT_DEF, 20.0, [12, 13], "Apex Titan: Unflinching stone titan. +20 Defense, +50 HP.",
                  conflict_node_id=14),
    ]
    return nodes


class SkillWebSimulation:
    """Manages player progression points, selection cursor, and live derived attributes."""
    def __init__(self):
        self.nodes = create_skill_web_nodes()
        self.graph = SkillWebGraph(self.nodes)

        # Baseline Character Attributes (Immutable base)
        self.base_stats = {
            STAT_HP: 100.0,
            STAT_ATK: 15.0,
            STAT_DEF: 10.0,
            STAT_SPD: 100.0,
            STAT_CRIT: 5.0
        }

        self.reset_progression()

        # Selection state
        self.selected_node_idx = 0
        self.anim_timer = 0.0
        self.toast_msg = ""
        self.toast_timer = 0.0
        self.toast_is_error = False
        self.pulse_timer = 0.0

    def reset_progression(self):
        """Restores starting point pool and resets node points to root only."""
        self.available_points = 5
        self.total_earned_points = 6
        for n in self.nodes:
            n.current_points = 0

        # Origin root is pre-allocated
        origin = self.graph.node_map.get(0)
        if origin:
            origin.current_points = 1

        self.selected_node_idx = 0

    def get_selected_node(self) -> SkillNode:
        if 0 <= self.selected_node_idx < len(self.nodes):
            return self.nodes[self.selected_node_idx]
        return self.nodes[0]

    def calculate_derived_stats(self) -> Dict[int, float]:
        """
        Pure Derived Stat Pipeline:
        Recalculates effective attributes cleanly by summing allocated node bonuses.
        Zero floating-point drift or attribute leak!
        """
        stats = dict(self.base_stats)
        for n in self.nodes:
            if n.current_points > 0:
                bonus = n.current_points * n.stat_bonus_per_point
                stats[n.stat_type] = stats.get(n.stat_type, 0.0) + bonus
                # Special synergy: Tempest Avatar grants bonus speed
                if n.node_id == 15 and n.current_points > 0:
                    stats[STAT_SPD] = stats.get(STAT_SPD, 100.0) + 15.0
                # Special synergy: Colossus Aegis grants bonus HP
                if n.node_id == 16 and n.current_points > 0:
                    stats[STAT_HP] = stats.get(STAT_HP, 100.0) + 50.0
        return stats

    def allocate_point_to_selected(self, sfx: SoundLibrary) -> bool:
        node = self.get_selected_node()
        can_alloc, reason = self.graph.can_allocate_point(node, self.available_points)

        if not can_alloc:
            self.toast_msg = f"Allocation Blocked: {reason}"
            self.toast_timer = 2.4
            self.toast_is_error = True
            sfx.play("hurt", 0.6)
            return False

        # Commit point
        node.current_points += 1
        if self.graph.strict_gating_enabled:
            self.available_points -= 1

        self.pulse_timer = 0.4
        self.toast_msg = f"Allocated rank to '{node.name}' ({node.current_points}/{node.max_points})!"
        self.toast_timer = 2.0
        self.toast_is_error = False

        if node.is_maxed() and node.max_points == 1:
            sfx.play("powerup", 0.8)  # Apex Keystone Fanfare!
        else:
            sfx.play("coin", 0.8)
        return True

    def refund_point_from_selected(self, sfx: SoundLibrary) -> bool:
        node = self.get_selected_node()
        can_ref, reason = self.graph.can_refund_point(node)

        if not can_ref:
            self.toast_msg = f"Refund Rejected: {reason}"
            self.toast_timer = 2.8
            self.toast_is_error = True
            sfx.play("hurt", 0.7)
            return False

        # Commit refund
        node.current_points -= 1
        if self.graph.strict_gating_enabled:
            self.available_points += 1

        self.toast_msg = f"Refunded rank from '{node.name}' (+1 Skill Point restored)!"
        self.toast_timer = 2.0
        self.toast_is_error = False
        sfx.play("click", 0.7)
        return True

    def grant_test_points(self, amount: int, sfx: SoundLibrary):
        self.available_points += amount
        self.total_earned_points += amount
        self.toast_msg = f"+ Granted {amount} Skill Points for testing!"
        self.toast_timer = 1.8
        self.toast_is_error = False
        sfx.play("powerup", 0.7)


# ==============================================================================
# PROCEDURAL DRAWING UTILITIES FOR SKILL WEB NODES & EDGES
# ==============================================================================

def draw_procedural_skill_icon(icon_type: int, cx: int, cy: int, size: int, is_active: bool):
    """
    Renders high-contrast 2D procedural geometric glyphs for skill nodes.
    C++ Equivalent: Raylib draw_line_ex, draw_circle, draw_triangle.
    """
    half = size // 2
    accent_col = COLOR_GOLD_ACCENT if is_active else COLOR_TEXT_DIM

    if icon_type == 0:  # Origin Star / Compass
        draw_circle(cx, cy, 3, accent_col)
        draw_line_ex(Vector2(cx - half + 4, cy), Vector2(cx + half - 4, cy), 2.0, accent_col)
        draw_line_ex(Vector2(cx, cy - half + 4), Vector2(cx, cy + half - 4), 2.0, accent_col)
        draw_circle_lines(cx, cy, half - 5, accent_col)

    elif icon_type in (1, 4, 8):  # Swords / Strike
        draw_line_ex(Vector2(cx - half + 5, cy + half - 5), Vector2(cx + half - 5, cy - half + 5), 3.0, accent_col)
        draw_line_ex(Vector2(cx - 2, cy + 4), Vector2(cx - 5, cy + 1), 3.0, accent_col)

    elif icon_type in (2, 6, 10):  # Wing / Boot / Agility
        draw_circle(cx - 2, cy + 3, half - 7, accent_col)
        draw_triangle(
            Vector2(cx - 2, cy - half + 5),
            Vector2(cx + half - 4, cy - 2),
            Vector2(cx - 2, cy + 3),
            accent_col
        )

    elif icon_type in (3, 7, 11):  # Shield / Defense
        draw_rectangle(cx - half + 5, cy - half + 5, (half - 5) * 2, half - 2, accent_col)
        draw_triangle(
            Vector2(cx - half + 5, cy + 2),
            Vector2(cx, cy + half - 3),
            Vector2(cx + half - 5, cy + 2),
            accent_col
        )

    elif icon_type in (5, 9, 12):  # Shouting Mouth / Nexus Star
        draw_circle(cx, cy, half - 6, accent_col)
        draw_circle(cx, cy, half - 10, COLOR_BG)
        draw_circle(cx, cy, 2, accent_col)

    elif icon_type == 13:  # Bloodthirst Skull / Axe
        draw_circle(cx, cy - 2, half - 6, Color(255, 80, 80, 255))
        draw_rectangle(cx - 4, cy + 4, 8, 4, Color(255, 80, 80, 255))
        draw_circle(cx - 3, cy - 3, 2, COLOR_BG)
        draw_circle(cx + 3, cy - 3, 2, COLOR_BG)

    elif icon_type == 14:  # Tempest Lightning Bolt
        draw_line_ex(Vector2(cx + 2, cy - half + 4), Vector2(cx - 3, cy), 3.0, Color(65, 235, 140, 255))
        draw_line_ex(Vector2(cx - 3, cy), Vector2(cx + 4, cy - 1), 3.0, Color(65, 235, 140, 255))
        draw_line_ex(Vector2(cx + 4, cy - 1), Vector2(cx - 2, cy + half - 4), 3.0, Color(65, 235, 140, 255))

    elif icon_type == 15:  # Colossus Mountain / Tower
        draw_triangle(
            Vector2(cx - half + 4, cy + half - 4),
            Vector2(cx, cy - half + 4),
            Vector2(cx + half - 4, cy + half - 4),
            Color(70, 160, 255, 255)
        )
        draw_circle(cx, cy + 2, 3, COLOR_WHITE)


def draw_curved_energy_edge(p1: Vector2, p2: Vector2, is_active: bool, anim_timer: float):
    """Renders flowing animated energy pulses along connected graph branches."""
    edge_col = Color(35, 48, 75, 180) if not is_active else Color(65, 185, 245, 240)
    line_thick = 2.0 if not is_active else 3.5

    draw_line_ex(p1, p2, line_thick, edge_col)

    # Animated energy pulse along active connections
    if is_active:
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 0.001:
            t = (anim_timer * 1.5) % 1.0
            px = int(p1.x + dx * t)
            py = int(p1.y + dy * t)
            draw_circle(px, py, 4, Color(255, 255, 255, 240))
            draw_circle(px, py, 6, Color(45, 215, 255, 120))


# ==============================================================================
# BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY ([Tab] & [F1])
# ==============================================================================

def draw_xray_telemetry_overlay(sim: SkillWebSimulation):
    """
    Renders diagnostic telemetry exposing the DAG Reachability Matrix,
    anti-refund orphan protection algorithm, and C++ memory footprint.
    """
    draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, Color(6, 8, 14, 235))

    ox = 110
    oy = 75
    ow = SCREEN_WIDTH - 220
    oh = SCREEN_HEIGHT - 150

    draw_rectangle(ox, oy, ow, oh, Color(16, 22, 36, 255))
    draw_rectangle_lines(ox, oy, ow, oh, COLOR_CYAN_ACCENT)

    # Header
    draw_text("[X-RAY TELEMETRY] DIRECTED ACYCLIC GRAPH (DAG) REACHABILITY & ORPHAN PROTECTION", ox + 24, oy + 18, 18, COLOR_GOLD_ACCENT)
    draw_line(ox + 20, oy + 46, ox + ow - 20, oy + 46, COLOR_PANEL_BORDER)

    # Column 1: DAG Prerequisite Matrix
    cx1 = ox + 30
    draw_text("1. DAG ADJACENCY MATRIX & PREREQUISITE TOPOLOGY", cx1, oy + 58, 14, COLOR_CYAN_ACCENT)

    mat_y = oy + 82
    draw_rectangle(cx1, mat_y, 480, 200, Color(22, 28, 44, 255))
    draw_rectangle_lines(cx1, mat_y, 480, 200, COLOR_PANEL_BORDER)

    nodes_sample = sim.nodes[:8]
    draw_text("NODE ID  | NAME               | REQ PARENTS | POINTS | STATUS", cx1 + 12, mat_y + 10, 10, COLOR_GOLD_ACCENT)
    draw_line(cx1 + 10, mat_y + 24, cx1 + 470, mat_y + 24, COLOR_PANEL_BORDER)

    for i, n in enumerate(nodes_sample):
        ny = mat_y + 28 + i * 20
        status_name = ["LOCKED", "AVAIL", "INVEST", "MAXED"][sim.graph.get_node_state(n, sim.available_points)]
        col = [COLOR_RED_ERROR, COLOR_GOLD_ACCENT, COLOR_CYAN_ACCENT, COLOR_GREEN_READY][sim.graph.get_node_state(n, sim.available_points)]
        parents_str = str(n.prerequisites) if n.prerequisites else "[ ROOT ]"
        line = f"ID #{n.node_id:<2}  | {n.name:<18} | {parents_str:<11} | {n.current_points}/{n.max_points:<2}  | {status_name}"
        draw_text(line, cx1 + 12, ny, 10, col)

    # Column 2: Anti-Refund Orphan Algorithm Proof
    cx2 = ox + 530
    draw_text("2. ANTI-REFUND ORPHAN PROTECTION (BFS REACHABILITY)", cx2, oy + 58, 14, COLOR_CYAN_ACCENT)
    by = oy + 82
    draw_rectangle(cx2, by, 480, 200, Color(22, 28, 44, 255))
    draw_rectangle_lines(cx2, by, 480, 200, COLOR_PANEL_BORDER)

    draw_text("ALGORITHM PROOF: Preventing the 'Refund-Root-Keep-Keystone' Exploit:", cx2 + 12, by + 10, 10, COLOR_GOLD_ACCENT)
    steps = [
        "1. Player requests refund on Node X (Points > 0).",
        "2. If Node X == 1 point, simulate VirtualState: X.points = 0.",
        "3. Seed queue with Roots (ID #0 Origin).",
        "4. BFS expands reachable nodes where VirtualPoints > 0 AND all parents reachable.",
        "5. If ANY other invested node is NOT reachable in BFS set:",
        "   -> REJECT refund atomically with 'DAG Orphan Violation' error!",
        "6. Guarantees 100% of invested perks remain anchored to Origin."
    ]
    for i, s in enumerate(steps):
        col = COLOR_GREEN_READY if i == 5 else COLOR_TEXT_MAIN
        draw_text(s, cx2 + 12, by + 30 + i * 22, 10, col)

    # Bottom Area: C++ Memory Layout
    by3 = oy + 295
    draw_text("3. C++ EQUIVALENT DATA STRUCTURES & MEMORY FOOTPRINT", cx1, by3, 14, COLOR_CYAN_ACCENT)
    box_y = by3 + 22
    draw_rectangle(cx1, box_y, ow - 60, 110, Color(20, 26, 42, 255))
    draw_rectangle_lines(cx1, box_y, ow - 60, 110, Color(45, 60, 95, 255))

    cpp_lines = [
        "struct SkillNode { int id; char name[32]; int branch; int max_p; int cur_p; int req_count; int reqs[4]; }; // 64 bytes",
        "struct SkillGraph { SkillNode nodes[17]; int root_ids[2]; };                                                  // ~1.1 KB",
        "CharacterStats: struct Stats { float hp, atk, def, spd, crit; };                                             // 20 bytes",
        "Pure Functional Derived Stats: Stat = Base + sum(node.points * node.bonus). Zero allocation, 100% cache locality!"
    ]
    for i, line in enumerate(cpp_lines):
        draw_text(line, cx1 + 14, box_y + 12 + i * 22, 11, COLOR_TEXT_MAIN)

    draw_text("Press [Tab] or Gamepad Y to dismiss X-Ray Telemetry Inspector", ox + ow // 2 - 200, oy + oh - 26, 12, COLOR_TEXT_DIM)


# ==============================================================================
# BLOCK 4: MAIN GAME LOOP & AUTOMATED SMOKE TEST
# ==============================================================================

class SkillWebGame:
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()

        self.sfx = SoundLibrary()
        self.sfx.init_defaults()

        self.sim = SkillWebSimulation()
        self.show_xray = True  # Default ON for pedagogical clarity

    def handle_input(self, dt: float):
        # 1. Toggles
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
            self.sfx.play("click", 0.6)

        if is_dual_pattern_toggle_pressed():  # F1 / Gamepad LB
            self.sim.graph.strict_gating_enabled = not self.sim.graph.strict_gating_enabled
            mode_str = "STRICT DAG PREREQUISITE GATING (Normal RPG Rules)" if self.sim.graph.strict_gating_enabled else "FREEFORM UNLOCKED (Creative Cheat Allocator)"
            self.sim.toast_msg = f"Skill Mode: {mode_str}"
            self.sim.toast_timer = 2.5
            self.sim.toast_is_error = not self.sim.graph.strict_gating_enabled
            self.sfx.play("click", 0.8)

        if is_dual_secondary_toggle_pressed():  # F2 / Gamepad RB
            self.sim.graph.mutual_exclusion_enabled = not self.sim.graph.mutual_exclusion_enabled
            ex_str = "MUTUAL EXCLUSION: ACTIVE (Opposite Keystones Lock Out)" if self.sim.graph.mutual_exclusion_enabled else "MUTUAL EXCLUSION: OFF (All Keystones Available)"
            self.sim.toast_msg = ex_str
            self.sim.toast_timer = 2.2
            self.sim.toast_is_error = False
            self.sfx.play("powerup", 0.7)

        if is_dual_reset_pressed():  # R / Gamepad Start
            self.sim.reset_progression()
            self.sim.toast_msg = "Skill Web Fully Respec'd: All points refunded!"
            self.sim.toast_timer = 2.2
            self.sim.toast_is_error = False
            self.sfx.play("click", 0.7)

        # 2. Grant Test Points (P / Gamepad X)
        if is_key_pressed(KEY_P) or (is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_FACE_LEFT) if is_gamepad_available(0) else False):
            self.sim.grant_test_points(5, self.sfx)

        # 3. Spatial Node Navigation (WASD / Arrows / Gamepad Stick)
        cur_node = self.sim.get_selected_node()
        move_x = 0
        move_y = 0

        if is_key_pressed(KEY_W) or is_key_pressed(KEY_UP) or (is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_UP) if is_gamepad_available(0) else False):
            move_y -= 1
        if is_key_pressed(KEY_S) or is_key_pressed(KEY_DOWN) or (is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_DOWN) if is_gamepad_available(0) else False):
            move_y += 1
        if is_key_pressed(KEY_A) or is_key_pressed(KEY_LEFT) or (is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_LEFT) if is_gamepad_available(0) else False):
            move_x -= 1
        if is_key_pressed(KEY_D) or is_key_pressed(KEY_RIGHT) or (is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_RIGHT) if is_gamepad_available(0) else False):
            move_x += 1

        if move_x != 0 or move_y != 0:
            self.navigate_spatial_node(cur_node, move_x, move_y)

        # 4. Point Allocation & Refund Actions
        # Allocate: Space / Enter / Gamepad A
        if is_dual_primary_fire_pressed() or is_key_pressed(KEY_ENTER) or is_key_pressed(KEY_SPACE):
            self.sim.allocate_point_to_selected(self.sfx)

        # Refund: Backspace / Gamepad B
        if is_key_pressed(KEY_BACKSPACE) or (is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_FACE_RIGHT) if is_gamepad_available(0) else False):
            self.sim.refund_point_from_selected(self.sfx)

        # 5. Mouse interactions
        self.handle_mouse_interaction()

    def navigate_spatial_node(self, cur_node: SkillNode, dx: int, dy: int):
        """Finds closest node in the requested directional quadrant."""
        best_node_idx = -1
        best_score = 999999.0

        for i, other in enumerate(self.sim.nodes):
            if other.node_id == cur_node.node_id:
                continue

            ox = other.x - cur_node.x
            oy = other.y - cur_node.y

            # Check directional alignment
            align_x = (dx > 0 and ox > 10.0) or (dx < 0 and ox < -10.0) or (dx == 0)
            align_y = (dy > 0 and oy > 10.0) or (dy < 0 and oy < -10.0) or (dy == 0)

            if align_x and align_y:
                # Weighted directional distance
                dist = math.sqrt(ox * ox + oy * oy)
                if dist < best_score:
                    best_score = dist
                    best_node_idx = i

        if best_node_idx != -1:
            self.sim.selected_node_idx = best_node_idx
            self.sfx.play("click", 0.4)

    def handle_mouse_interaction(self):
        m_pos = get_mouse_position()
        mx = int(m_pos.x)
        my = int(m_pos.y)
        m_left_clicked = is_mouse_button_pressed(MOUSE_BUTTON_LEFT)
        m_right_clicked = is_mouse_button_pressed(MOUSE_BUTTON_RIGHT)

        # 1. Canvas Node Hover & Clicks
        for i, node in enumerate(self.sim.nodes):
            nx = int(CANVAS_X + node.x)
            ny = int(CANVAS_Y + node.y)
            radius = 24 if node.max_points > 1 or node.node_id in (14, 15, 16) else 20

            dist_sq = (mx - nx) * (mx - nx) + (my - ny) * (my - ny)
            if dist_sq <= radius * radius:
                if self.sim.selected_node_idx != i:
                    self.sim.selected_node_idx = i
                    self.sfx.play("click", 0.3)

                if m_left_clicked:
                    self.sim.allocate_point_to_selected(self.sfx)
                elif m_right_clicked:
                    self.sim.refund_point_from_selected(self.sfx)

        # 2. Right Desk Action Buttons
        # Allocate Button
        alloc_x = DESK_X + 20
        alloc_y = DESK_Y + 360
        alloc_w = (DESK_W - 50) // 2
        alloc_h = 42

        if alloc_x <= mx <= alloc_x + alloc_w and alloc_y <= my <= alloc_y + alloc_h:
            if m_left_clicked:
                self.sim.allocate_point_to_selected(self.sfx)

        # Refund Button
        ref_x = alloc_x + alloc_w + 10
        ref_y = alloc_y
        ref_w = alloc_w
        ref_h = 42

        if ref_x <= mx <= ref_x + ref_w and ref_y <= my <= ref_y + ref_h:
            if m_left_clicked:
                self.sim.refund_point_from_selected(self.sfx)

        # Grant +5 Points Button
        grant_x = DESK_X + 20
        grant_y = DESK_Y + 412
        grant_w = (DESK_W - 50) // 2
        grant_h = 32

        if grant_x <= mx <= grant_x + grant_w and grant_y <= my <= grant_y + grant_h:
            if m_left_clicked:
                self.sim.grant_test_points(5, self.sfx)

        # Full Respec Button
        respec_x = grant_x + grant_w + 10
        respec_y = grant_y
        respec_w = grant_w
        respec_h = 32

        if respec_x <= mx <= respec_x + respec_w and respec_y <= my <= respec_y + respec_h:
            if m_left_clicked:
                self.sim.reset_progression()
                self.sim.toast_msg = "Skill Web Fully Respec'd!"
                self.sim.toast_timer = 2.0
                self.sim.toast_is_error = False
                self.sfx.play("click", 0.7)

    def update(self):
        dt = min(get_frame_time(), 0.05)
        self.sim.anim_timer += dt

        if self.sim.toast_timer > 0.0:
            self.sim.toast_timer -= dt

        if self.sim.pulse_timer > 0.0:
            self.sim.pulse_timer -= dt

        self.handle_input(dt)

    def draw(self):
        begin_drawing()
        clear_background(COLOR_BG)

        # 1. Top HUD Header Bar
        self.draw_top_bar()

        # 2. Main Canvas: Interactive Skill Web Graph
        self.draw_skill_web_canvas()

        # 3. Right Desk: Focused Node Inspector & Derived Stat Manifest
        self.draw_inspector_panel()

        # 4. Toast Notification
        if self.sim.toast_timer > 0.0:
            self.draw_toast()

        # 5. Global Dropdowns & Gamepad Badge
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)

        # 6. X-Ray Overlay ([Tab])
        if self.show_xray:
            draw_xray_telemetry_overlay(self.sim)

        end_drawing()

    def draw_top_bar(self):
        draw_rectangle(0, 0, SCREEN_WIDTH, 52, Color(16, 20, 32, 255))
        draw_line(0, 52, SCREEN_WIDTH, 52, COLOR_PANEL_BORDER)

        draw_text("SKILL WEB", 25, 14, 20, COLOR_GOLD_ACCENT)
        draw_text("NODE GRAPH & PREREQUISITE VALIDATION PIPELINE", 160, 20, 12, COLOR_TEXT_DIM)

        # Mode Indicator Badges
        if self.sim.graph.strict_gating_enabled:
            draw_rectangle(25, 34, 185, 14, Color(22, 48, 32, 255))
            draw_text("[F1] GATING: STRICT DAG RULES", 28, 36, 9, COLOR_GREEN_READY)
        else:
            draw_rectangle(25, 34, 185, 14, Color(58, 22, 22, 255))
            draw_text("[F1] GATING: FREEFORM UNLOCKED", 28, 36, 9, COLOR_RED_ERROR)

        if self.sim.graph.mutual_exclusion_enabled:
            draw_rectangle(225, 34, 185, 14, Color(22, 38, 56, 255))
            draw_text("[F2] EXCLUSION: POLAR OPPOSITES", 228, 36, 9, COLOR_CYAN_ACCENT)

    def draw_skill_web_canvas(self):
        # Canvas Frame
        draw_rectangle(CANVAS_X, CANVAS_Y, CANVAS_W, CANVAS_H, Color(12, 18, 30, 255))
        draw_rectangle_lines(CANVAS_X, CANVAS_Y, CANVAS_W, CANVAS_H, COLOR_PANEL_BORDER)

        # Subtle starfield grid lines
        grid_step = 60
        for x in range(CANVAS_X, CANVAS_X + CANVAS_W, grid_step):
            draw_line(x, CANVAS_Y, x, CANVAS_Y + CANVAS_H, COLOR_CANVAS_GRID)
        for y in range(CANVAS_Y, CANVAS_Y + CANVAS_H, grid_step):
            draw_line(CANVAS_X, y, CANVAS_X + CANVAS_W, y, COLOR_CANVAS_GRID)

        # 1. Draw Connected Graph Edges (with animated energy pulses if active)
        for node in self.sim.nodes:
            p2 = Vector2(CANVAS_X + node.x, CANVAS_Y + node.y)
            for parent_id in node.prerequisites:
                parent = self.sim.graph.node_map.get(parent_id)
                if parent:
                    p1 = Vector2(CANVAS_X + parent.x, CANVAS_Y + parent.y)
                    is_active = (parent.is_active() and node.is_active())
                    draw_curved_energy_edge(p1, p2, is_active, self.sim.anim_timer)

        # 2. Draw Branch Archetype Region Labels
        draw_text("<< JUGGERNAUT (OFFENSE)", CANVAS_X + 25, CANVAS_Y + 25, 13, Color(255, 80, 80, 220))
        draw_text("WINDSTRIDER (AGILITY) ^^", CANVAS_X + CANVAS_W // 2 - 80, CANVAS_Y + 25, 13, Color(65, 225, 140, 220))
        draw_text("BULWARK (DEFENSE) >>", CANVAS_X + CANVAS_W - 200, CANVAS_Y + 25, 13, Color(70, 160, 255, 220))

        # 3. Draw All Skill Node Hubs
        for i, node in enumerate(self.sim.nodes):
            self.draw_node_hub(node, i == self.sim.selected_node_idx)

    def draw_node_hub(self, node: SkillNode, is_selected: bool):
        nx = int(CANVAS_X + node.x)
        ny = int(CANVAS_Y + node.y)
        is_keystone = (node.max_points == 1 and node.node_id > 0)
        radius = 24 if (is_keystone or node.node_id == 0) else 20

        state = self.sim.graph.get_node_state(node, self.sim.available_points)
        branch_col = BRANCH_COLORS[node.branch]

        # Outer state ring & glow
        if state == STATE_MAXED:
            glow_rad = radius + 6 + int(math.sin(self.sim.anim_timer * 4.0) * 2.0)
            draw_circle(nx, ny, glow_rad, Color(255, 205, 55, 110))
            draw_circle(nx, ny, radius, Color(28, 38, 56, 255))
            draw_circle_lines(nx, ny, radius, COLOR_GOLD_ACCENT)
        elif state == STATE_INVESTED:
            draw_circle(nx, ny, radius, Color(24, 32, 48, 255))
            draw_circle_lines(nx, ny, radius, branch_col)
        elif state == STATE_AVAILABLE:
            glow_rad = radius + 4 + int(math.sin(self.sim.anim_timer * 6.0) * 3.0)
            draw_circle(nx, ny, glow_rad, Color(65, 245, 130, 80))
            draw_circle(nx, ny, radius, Color(20, 26, 40, 255))
            draw_circle_lines(nx, ny, radius, COLOR_GREEN_READY)
        else:  # STATE_LOCKED
            draw_circle(nx, ny, radius, Color(16, 20, 28, 255))
            draw_circle_lines(nx, ny, radius, Color(42, 52, 72, 255))

        # Procedural Icon in Center
        draw_procedural_skill_icon(node.icon_type, nx, ny, radius * 2 - 8, is_active=(state in (STATE_INVESTED, STATE_MAXED)))

        # Rank Counter Pill below node
        rank_str = f"{node.current_points}/{node.max_points}"
        pill_w = 32
        pill_h = 14
        pill_x = nx - pill_w // 2
        pill_y = ny + radius + 4

        draw_rectangle(pill_x, pill_y, pill_w, pill_h, Color(14, 18, 28, 240))
        pill_border = COLOR_GOLD_ACCENT if state == STATE_MAXED else (branch_col if state == STATE_INVESTED else COLOR_SLOT_BORDER)
        draw_rectangle_lines(pill_x, pill_y, pill_w, pill_h, pill_border)
        draw_text(rank_str, pill_x + 5, pill_y + 2, 10, COLOR_WHITE if state in (STATE_INVESTED, STATE_MAXED) else COLOR_TEXT_DIM)

        # Selection Indicator (Radiant Reticle Ring)
        if is_selected:
            sel_rad = radius + 9
            draw_circle_lines(nx, ny, sel_rad, COLOR_WHITE)
            # Corner reticle brackets
            draw_line(nx - sel_rad - 3, ny, nx - sel_rad + 3, ny, COLOR_GOLD_ACCENT)
            draw_line(nx + sel_rad - 3, ny, nx + sel_rad + 3, ny, COLOR_GOLD_ACCENT)
            draw_line(nx, ny - sel_rad - 3, nx, ny - sel_rad + 3, COLOR_GOLD_ACCENT)
            draw_line(nx, ny + sel_rad - 3, nx, ny + sel_rad + 3, COLOR_GOLD_ACCENT)

    def draw_inspector_panel(self):
        draw_rectangle(DESK_X, DESK_Y, DESK_W, DESK_H, COLOR_PANEL_BG)
        draw_rectangle_lines(DESK_X, DESK_Y, DESK_W, DESK_H, COLOR_PANEL_BORDER)

        # Header: Available Points Vault
        draw_rectangle(DESK_X, DESK_Y, DESK_W, 64, Color(22, 28, 44, 255))
        draw_rectangle_lines(DESK_X, DESK_Y, DESK_W, 64, COLOR_PANEL_BORDER)

        draw_circle(DESK_X + 32, DESK_Y + 32, 16, COLOR_GOLD_ACCENT)
        draw_text("★", DESK_X + 26, DESK_Y + 22, 18, COLOR_BG)

        draw_text("AVAILABLE SKILL POINTS", DESK_X + 58, DESK_Y + 14, 11, COLOR_TEXT_DIM)
        draw_text(f"{self.sim.available_points} Points", DESK_X + 58, DESK_Y + 30, 20, COLOR_GOLD_ACCENT)

        # Invested tally on right of header
        invested_total = 0
        for n in self.sim.nodes:
            invested_total += n.current_points
        draw_text(f"Invested: {invested_total}", DESK_X + DESK_W - 90, DESK_Y + 24, 12, COLOR_CYAN_ACCENT)

        # 1. Focused Node Card
        node = self.sim.get_selected_node()
        card_y = DESK_Y + 76
        draw_rectangle(DESK_X + 15, card_y, DESK_W - 30, 160, Color(20, 26, 42, 255))
        draw_rectangle_lines(DESK_X + 15, card_y, DESK_W - 30, 160, COLOR_PANEL_BORDER)

        # Big Node Glyph
        draw_procedural_skill_icon(node.icon_type, DESK_X + 48, card_y + 42, 44, is_active=node.is_active())

        # Title & Branch
        draw_text(node.name, DESK_X + 80, card_y + 14, 15, COLOR_GOLD_ACCENT)
        branch_name = BRANCH_NAMES[node.branch]
        branch_col = BRANCH_COLORS[node.branch]
        draw_text(f"Branch: {branch_name}", DESK_X + 80, card_y + 34, 10, branch_col)
        draw_text(f"Current Rank: {node.current_points} / {node.max_points}", DESK_X + 80, card_y + 48, 11, COLOR_WHITE)

        # Lore description
        draw_text(node.lore, DESK_X + 24, card_y + 74, 10, COLOR_TEXT_DIM)

        # Stat Bonus Highlight Box
        stat_box_y = card_y + 110
        draw_rectangle(DESK_X + 24, stat_box_y, DESK_W - 48, 38, Color(14, 18, 30, 255))
        draw_rectangle_lines(DESK_X + 24, stat_box_y, DESK_W - 48, 38, COLOR_SLOT_BORDER)

        stat_name = STAT_NAMES[node.stat_type]
        unit = STAT_UNITS[node.stat_type]
        bonus_val = node.stat_bonus_per_point
        draw_text(f"Bonus: +{bonus_val}{unit} {stat_name} per point", DESK_X + 34, stat_box_y + 12, 11, COLOR_GREEN_READY)

        # 2. Prerequisite & Validation Check
        prereq_y = DESK_Y + 246
        draw_rectangle(DESK_X + 15, prereq_y, DESK_W - 30, 100, Color(22, 28, 44, 255))
        draw_rectangle_lines(DESK_X + 15, prereq_y, DESK_W - 30, 100, COLOR_PANEL_BORDER)

        draw_text("PREREQUISITE STATUS:", DESK_X + 24, prereq_y + 10, 11, COLOR_CYAN_ACCENT)

        if not node.prerequisites:
            draw_text("• Foundational Root: Always Available.", DESK_X + 24, prereq_y + 30, 10, COLOR_GREEN_READY)
        else:
            for j, pid in enumerate(node.prerequisites):
                parent = self.sim.graph.node_map.get(pid)
                if parent:
                    has_parent = (parent.current_points > 0) or not self.sim.graph.strict_gating_enabled
                    p_col = COLOR_GREEN_READY if has_parent else COLOR_RED_ERROR
                    p_mark = "[✓]" if has_parent else "[✗]"
                    p_line = f"{p_mark} Requires: {parent.name} ({parent.current_points}/{parent.max_points})"
                    draw_text(p_line, DESK_X + 24, prereq_y + 30 + j * 18, 10, p_col)

        # Mutual Exclusion Warning if applicable
        if node.conflict_node_id != -1 and self.sim.graph.mutual_exclusion_enabled:
            conflict = self.sim.graph.node_map.get(node.conflict_node_id)
            if conflict:
                conf_col = COLOR_RED_ERROR if conflict.is_active() else COLOR_GOLD_ACCENT
                conf_msg = f"! Conflicts with '{conflict.name}'"
                draw_text(conf_msg, DESK_X + 24, prereq_y + 78, 10, conf_col)

        # 3. Action Buttons ([ALLOCATE POINT] & [REFUND POINT])
        btn_y = DESK_Y + 360
        btn_w = (DESK_W - 40) // 2
        btn_h = 42

        can_alloc, _ = self.sim.graph.can_allocate_point(node, self.sim.available_points)
        alloc_col = Color(35, 95, 55, 255) if can_alloc else Color(45, 45, 55, 255)
        draw_rectangle(DESK_X + 15, btn_y, btn_w, btn_h, alloc_col)
        draw_rectangle_lines(DESK_X + 15, btn_y, btn_w, btn_h, COLOR_GREEN_READY if can_alloc else COLOR_SLOT_BORDER)
        draw_text("ALLOCATE (+1)", DESK_X + 30, btn_y + 14, 12, COLOR_WHITE if can_alloc else COLOR_TEXT_DIM)

        can_ref, _ = self.sim.graph.can_refund_point(node)
        ref_col = Color(95, 45, 45, 255) if can_ref else Color(45, 45, 55, 255)
        draw_rectangle(DESK_X + 25 + btn_w, btn_y, btn_w, btn_h, ref_col)
        draw_rectangle_lines(DESK_X + 25 + btn_w, btn_y, btn_w, btn_h, COLOR_RED_ERROR if can_ref else COLOR_SLOT_BORDER)
        draw_text("REFUND (-1)", DESK_X + 44 + btn_w, btn_y + 14, 12, COLOR_WHITE if can_ref else COLOR_TEXT_DIM)

        # 4. Helper Buttons (+5 Points & Respec)
        sub_btn_y = btn_y + 50
        sub_btn_h = 28
        draw_rectangle(DESK_X + 15, sub_btn_y, btn_w, sub_btn_h, Color(30, 42, 65, 255))
        draw_rectangle_lines(DESK_X + 15, sub_btn_y, btn_w, sub_btn_h, COLOR_CYAN_ACCENT)
        draw_text("+5 Points [P]", DESK_X + 38, sub_btn_y + 8, 10, COLOR_CYAN_ACCENT)

        draw_rectangle(DESK_X + 25 + btn_w, sub_btn_y, btn_w, sub_btn_h, Color(45, 30, 30, 255))
        draw_rectangle_lines(DESK_X + 25 + btn_w, sub_btn_y, btn_w, sub_btn_h, COLOR_RED_ERROR)
        draw_text("Full Respec [R]", DESK_X + 42 + btn_w, sub_btn_y + 8, 10, COLOR_RED_ERROR)

        # 5. Live Character Attributes Manifest
        stat_manifest_y = DESK_Y + 452
        draw_rectangle(DESK_X + 15, stat_manifest_y, DESK_W - 30, 180, Color(18, 24, 38, 255))
        draw_rectangle_lines(DESK_X + 15, stat_manifest_y, DESK_W - 30, 180, COLOR_PANEL_BORDER)

        draw_text("LIVE CHARACTER STAT TOTALS:", DESK_X + 25, stat_manifest_y + 10, 11, COLOR_GOLD_ACCENT)

        derived = self.sim.calculate_derived_stats()
        stat_rows = [
            (STAT_HP, "Max Health", COLOR_RED_ERROR),
            (STAT_ATK, "Attack Power", Color(255, 120, 95, 255)),
            (STAT_DEF, "Armor Defense", Color(95, 165, 255, 255)),
            (STAT_SPD, "Movement Speed", COLOR_GREEN_READY),
            (STAT_CRIT, "Critical Strike", COLOR_GOLD_ACCENT),
        ]
        for k, (st_id, label, col) in enumerate(stat_rows):
            sy = stat_manifest_y + 32 + k * 28
            draw_rectangle(DESK_X + 25, sy, DESK_W - 50, 24, Color(14, 18, 28, 255))
            draw_rectangle_lines(DESK_X + 25, sy, DESK_W - 50, 24, COLOR_SLOT_BORDER)

            val = derived[st_id]
            base = self.sim.base_stats[st_id]
            delta = val - base
            unit = STAT_UNITS[st_id]

            draw_text(label, DESK_X + 34, sy + 6, 11, col)
            val_str = f"{val:.1f}{unit}" if st_id == STAT_CRIT else f"{int(val)} {unit}"
            draw_text(val_str, DESK_X + DESK_W - 125, sy + 6, 11, COLOR_WHITE)

            if delta > 0:
                delta_str = f"(+{delta:.1f})" if st_id == STAT_CRIT else f"(+{int(delta)})"
                draw_text(delta_str, DESK_X + DESK_W - 65, sy + 6, 10, COLOR_GREEN_READY)

    def draw_toast(self):
        alpha = min(1.0, self.sim.toast_timer * 2.0)
        tw = 480
        th = 40
        tx = (SCREEN_WIDTH - tw) // 2
        ty = SCREEN_HEIGHT - 65

        col_bg = Color(48, 18, 22, int(240 * alpha)) if self.sim.toast_is_error else Color(18, 48, 30, int(240 * alpha))
        col_border = COLOR_RED_ERROR if self.sim.toast_is_error else COLOR_GREEN_READY

        draw_rectangle(tx, ty, tw, th, col_bg)
        draw_rectangle_lines(tx, ty, tw, th, col_border)
        draw_text(self.sim.toast_msg, tx + 20, ty + 12, 12, COLOR_WHITE)

    def run(self, smoke_test: bool = False):
        frame_count = 0
        while not window_should_close():
            self.update()
            self.draw()
            frame_count += 1
            if smoke_test and frame_count >= 3:
                break

        self.sfx.unload_all()
        close_audio_device()
        close_window()


if __name__ == "__main__":
    is_smoke = "--smoke-test" in sys.argv
    SkillWebGame().run(smoke_test=is_smoke)
