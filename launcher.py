# -*- coding: utf-8 -*-
"""
Interactive Game Design Pattern Hub & Minigame Launcher
=======================================================
Scans `minigames/*.py` using Python's AST (without importing or executing them),
extracts their pedagogical docstrings and 3.x catalog section classification,
and provides a graphical Raylib dashboard with category dropdown filtering to
inspect, smoke-test, and launch any prototype in the repository.

Usage:
  python -B launcher.py
  python -B launcher.py --smoke-test
"""

import sys
import os

# 1. Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# 2. Add repository root to search path
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

import ast
import subprocess
from typing import List, Dict

# 3. Mandatory Raylib & modular imports
from pyray import *
from assets import *
from utils import *

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WINDOW_TITLE = "Game Design Patterns Hub & Launcher (Raylib Python)"

# UI Palette
COLOR_BG = Color(10, 13, 22, 255)
COLOR_PANEL = Color(18, 23, 38, 255)
COLOR_PANEL_BORDER = Color(48, 65, 105, 255)
COLOR_ITEM_SELECTED = Color(32, 85, 145, 255)
COLOR_ITEM_HOVER = Color(24, 34, 56, 255)
COLOR_ACCENT = Color(70, 205, 255, 255)
COLOR_TEXT_MAIN = Color(235, 242, 255, 255)
COLOR_TEXT_DIM = Color(145, 160, 185, 255)

# 3.x Catalog Taxonomy Categories from minigames.md
CAT_ALL = "ALL"
CAT_3_0 = "3.0"
CAT_3_1 = "3.1"
CAT_3_2 = "3.2"
CAT_3_3 = "3.3"
CAT_3_4 = "3.4"
CAT_3_5 = "3.5"
CAT_3_6 = "3.6"
CAT_3_7 = "3.7"

CATALOG_SECTIONS = [
    {
        "id": CAT_ALL,
        "name": "All Categories",
        "title": "All Built Prototypes",
        "desc": "Browse all standalone minigames and design pattern labs across all categories.",
        "planned_count": 133
    },
    {
        "id": CAT_3_0,
        "name": "3.0 Core Multi-Pattern",
        "title": "Section 3.0: Core Multi-Pattern Prototypes",
        "desc": "Full multi-pattern arcade and action prototypes combining 4+ patterns: Space Swarm, Mecha Colosseum 3D, Drone Defense 3D.",
        "planned_count": 5
    },
    {
        "id": CAT_3_1,
        "name": "3.1 Menus & UI",
        "title": "Section 3.1: Menus & User Interface",
        "desc": "Tactile menus and interface architectures: Title Screen Cursor, Weapon Wheel, Tabbed Status Menu, Attaché Case, Tetris Backpack, Overloaded Mule, Paper Doll, Gear Compare.",
        "planned_count": 30
    },
    {
        "id": CAT_3_2,
        "name": "3.2 Combat & Weapons",
        "title": "Section 3.2: Combat & Weapon Systems",
        "desc": "Offensive and defensive mechanics: Hitscan tracing, Ballistic arcs, Spread cones, Combo input buffers, Parry windows, Recoil bloom, Hit-stop freeze frames.",
        "planned_count": 25
    },
    {
        "id": CAT_3_3,
        "name": "3.3 Enemies & AI",
        "title": "Section 3.3: Enemies & Game AI",
        "desc": "Artificial intelligence behaviors: Waypoint patrols, Alert state machines, Flow fields, Boid flocking, Telegraphed snipers, Three-phase bosses, Bullet generators.",
        "planned_count": 23
    },
    {
        "id": CAT_3_4,
        "name": "3.4 Progression & Economy",
        "title": "Section 3.4: Progression & Economy Loops",
        "desc": "RPG and survival loops: Loot drop tables with rarity tiers, XP leveling curves, Herb/ammo crafting alchemy, Scrap buy/sell economies, Gacha pity timers.",
        "planned_count": 15
    },
    {
        "id": CAT_3_5,
        "name": "3.5 World & Exploration",
        "title": "Section 3.5: World & Procedural Exploration",
        "desc": "Environment generation: Voxel chunked sandboxes, Noise terrain heightmaps, Cellular automata caves, BSP room-and-corridor dungeons, Lock-and-key gating.",
        "planned_count": 16
    },
    {
        "id": CAT_3_6,
        "name": "3.6 Movement & Camera",
        "title": "Section 3.6: Physics, Movement & Camera Rigs",
        "desc": "Kinematic movement feel: Coyote time and jump buffers, Dash with invulnerability frames, Grappling swing pendulums, Orbit cameras with collision.",
        "planned_count": 15
    },
    {
        "id": CAT_3_7,
        "name": "3.7 Puzzle, Stealth & Other",
        "title": "Section 3.7: Puzzle, Stealth & Systemic Mechanics",
        "desc": "Logic and systemic patterns: Sokoban push-block puzzles, Vision cone stealth, Tower targeting priorities, Command pattern undo/rewind, Particle emitters.",
        "planned_count": 19
    },
]


def wrap_docstring_lines(raw_lines: List[str], max_chars: int = 82) -> List[str]:
    """Wraps long docstring lines preserving bullet indentations so text never overflows panels."""
    wrapped: List[str] = []
    for raw in raw_lines:
        if len(raw) <= max_chars:
            wrapped.append(raw)
        else:
            indent = ""
            if raw.startswith("  - "):
                indent = "    "
            elif raw.startswith("    "):
                indent = "    "
            elif raw.startswith("  "):
                indent = "  "

            words = raw.split(" ")
            cur_line = ""
            for w in words:
                if not cur_line:
                    cur_line = w
                elif len(cur_line) + 1 + len(w) <= max_chars:
                    cur_line += " " + w
                else:
                    wrapped.append(cur_line)
                    cur_line = indent + w
            if cur_line:
                wrapped.append(cur_line)
    return wrapped


def extract_section_from_docstring(raw_doc: str, fname: str, parent_folder: str = "") -> tuple:
    """Extracts (section_id, section_name) from AST docstrings, parent folder, or known taxonomy mapping."""
    for line in raw_doc.splitlines():
        clean = line.strip().lower()
        if clean.startswith("section"):
            parts = line.split(":", 1)
            if len(parts) > 1:
                val = parts[1].strip()
                for sec in CATALOG_SECTIONS:
                    if sec["id"] != CAT_ALL:
                        if sec["id"] in val or sec["name"].lower() in val.lower():
                            return (sec["id"], sec["name"])

    # Check parent folder (e.g. 3.0_core_prototypes, 3.1_menus_ui)
    if parent_folder:
        for sec in CATALOG_SECTIONS:
            if sec["id"] != CAT_ALL and (parent_folder.startswith(sec["id"]) or sec["id"] in parent_folder):
                return (sec["id"], sec["name"])

    # Fallback known mapping
    known_map = {
        "space_swarm.py": ("3.0", "3.0 Core Multi-Pattern"),
        "mecha_colosseum.py": ("3.0", "3.0 Core Multi-Pattern"),
        "drone_defense_3d.py": ("3.0", "3.0 Core Multi-Pattern"),
        "title_screen_cursor.py": ("3.1", "3.1 Menus & UI"),
        "weapon_wheel.py": ("3.1", "3.1 Menus & UI"),
        "tabbed_status_menu.py": ("3.1", "3.1 Menus & UI"),
        "attache_case.py": ("3.1", "3.1 Menus & UI"),
        "tetris_backpack.py": ("3.1", "3.1 Menus & UI"),
        "overloaded_mule.py": ("3.1", "3.1 Menus & UI"),
        "paper_doll.py": ("3.1", "3.1 Menus & UI"),
        "gear_compare.py": ("3.1", "3.1 Menus & UI"),
        "merchant_stall.py": ("3.1", "3.1 Menus & UI"),
        "workbench.py": ("3.1", "3.1 Menus & UI"),
        "skill_web.py": ("3.1", "3.1 Menus & UI"),
        "minimap_compass.py": ("3.1", "3.1 Menus & UI"),
    }
    if fname in known_map:
        return known_map[fname]

    return ("3.0", "3.0 Core Multi-Pattern")


def scan_minigames(minigames_dir: str) -> List[Dict[str, str]]:
    """
    Scans `minigames/` and its subdirectories for standalone `.py` scripts and extracts their
    module docstring, 3.x catalog section, and line count using `ast` without executing the scripts.
    """
    entries: List[Dict[str, str]] = []
    if not os.path.isdir(minigames_dir):
        return entries

    file_list = []
    for root, dirs, files in os.walk(minigames_dir):
        dirs.sort()
        for fname in sorted(files):
            if fname.endswith(".py") and not fname.startswith("_"):
                full_path = os.path.join(root, fname)
                rel_path = os.path.relpath(full_path, minigames_dir).replace("\\", "/")
                parent_dir = os.path.basename(root)
                file_list.append((fname, full_path, rel_path, parent_dir))

    # Sort files deterministically: first by section/parent_dir, then by filename
    file_list.sort(key=lambda item: (item[3], item[0]))

    for fname, full_path, rel_path, parent_dir in file_list:
        try:
            with open(full_path, "r", encoding="utf-8-sig") as fp:
                source = fp.read()
            line_count = len(source.splitlines())
            tree = ast.parse(source, filename=fname)
            raw_doc = ast.get_docstring(tree) or "No module docstring provided."
        except Exception as exc:
            line_count = 0
            raw_doc = f"Error parsing file: {exc}"

        doc_lines = [line.rstrip() for line in raw_doc.strip().splitlines()]
        title = doc_lines[0] if doc_lines else fname
        # Strip underline separator if present on line 2
        if len(doc_lines) > 1 and set(doc_lines[1].strip()) <= {"=", "-"}:
            body_lines = doc_lines[2:]
        else:
            body_lines = doc_lines[1:]

        wrapped_body = wrap_docstring_lines(body_lines, max_chars=82)
        sec_id, sec_name = extract_section_from_docstring(raw_doc, fname, parent_dir)

        entries.append({
            "filename": fname,
            "rel_path": rel_path,
            "path": full_path,
            "title": title,
            "section_id": sec_id,
            "section_name": sec_name,
            "lines": str(line_count),
            "body_lines": wrapped_body,
            "smoke_status": "Untested",
        })

    return entries


class PatternHubLauncher:
    """Graphical browser and test runner for all minigame prototypes with 3.x category dropdowns."""

    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)

        init_audio_device()
        self.sfx = SoundLibrary()
        self.sfx.init_defaults()

        self.music = SynthMusicPlayer()
        self.ambient_track = generate_ambient_track(bpm=84.0)
        self.music.load_track(self.ambient_track)
        self.music.set_volume(0.4)
        self.music.play()
        self.music_enabled = True

        self.minigames_dir = os.path.join(ROOT_DIR, "minigames")
        self.entries = scan_minigames(self.minigames_dir)

        # 3.x Section Dropdown Filter
        self.selected_section_id = CAT_ALL
        self.category_dropdown_open = False
        self.selected_idx = 0
        self.scroll_offset = 0
        self.desc_scroll_y = 0.0
        self.filtered_entries: List[Dict[str, str]] = []
        self._update_filtered_entries()

        self.max_visible_items = 10
        self.max_desc_scroll = 0.0
        self.r_stick_active = False
        self.status_banner = "Ready. Press [Enter / Gamepad A] to play or [S / Gamepad X] to smoke-test."
        self.status_color = COLOR_ACCENT
        self.anim_timer = 0.0
        self.pad_nav_cooldown = 0.0
        self.bumper_cooldown = 0.0

    def _update_filtered_entries(self):
        """Filters minigames by the selected 3.x catalog category."""
        if self.selected_section_id == CAT_ALL:
            self.filtered_entries = list(self.entries)
        else:
            self.filtered_entries = [e for e in self.entries if e["section_id"] == self.selected_section_id]

        if self.selected_idx >= len(self.filtered_entries):
            self.selected_idx = max(0, len(self.filtered_entries) - 1)
        self.scroll_offset = 0
        self.desc_scroll_y = 0.0

    def set_section(self, section_id: str):
        """Switches the active 3.x catalog filter and updates the list."""
        if self.selected_section_id != section_id:
            self.selected_section_id = section_id
            self._update_filtered_entries()
            self.sfx.play("click", 0.6)
            sec_name = self.get_section_info(section_id)["name"]
            self.status_banner = f"Filtered: {sec_name} ({len(self.filtered_entries)} prototype(s))."
            self.status_color = COLOR_ACCENT

    def get_section_info(self, section_id: str) -> dict:
        for sec in CATALOG_SECTIONS:
            if sec["id"] == section_id:
                return sec
        return CATALOG_SECTIONS[0]

    def cycle_section(self, direction: int):
        """Cycles to previous or next 3.x catalog category (Q / E or Gamepad LB / RB)."""
        cur_idx = 0
        for i, sec in enumerate(CATALOG_SECTIONS):
            if sec["id"] == self.selected_section_id:
                cur_idx = i
                break
        next_idx = (cur_idx + direction) % len(CATALOG_SECTIONS)
        self.set_section(CATALOG_SECTIONS[next_idx]["id"])

    def rescan(self):
        self.entries = scan_minigames(self.minigames_dir)
        self._update_filtered_entries()
        self.status_banner = f"Rescanned minigames/: found {len(self.entries)} prototype(s)."
        self.status_color = COLOR_ACCENT
        self.sfx.play("click", 0.6)

    def launch_selected(self, smoke_test: bool = False):
        if not self.filtered_entries:
            return
        entry = self.filtered_entries[self.selected_idx]
        script_path = entry["path"]
        self.sfx.play("powerup" if not smoke_test else "click", 0.6)

        if self.music_enabled:
            self.music.pause()

        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        cmd = [sys.executable, "-B", script_path]
        if smoke_test:
            cmd.append("--smoke-test")

        try:
            result = subprocess.run(cmd, cwd=ROOT_DIR, env=env, check=False)
            if result.returncode == 0:
                if smoke_test:
                    entry["smoke_status"] = "PASS (Exit 0)"
                    self.status_banner = f"Smoke test PASSED for {entry['filename']}!"
                    self.status_color = GREEN
                else:
                    self.status_banner = f"Closed {entry['filename']} cleanly (Exit 0)."
                    self.status_color = COLOR_ACCENT
            else:
                entry["smoke_status"] = f"FAIL (Exit {result.returncode})"
                self.status_banner = f"{entry['filename']} exited with code {result.returncode}."
                self.status_color = RED
        except Exception as exc:
            self.status_banner = f"Launch error: {exc}"
            self.status_color = RED

        ui_settings.reload_from_disk()

        if self.music_enabled:
            self.music.resume()

    def update(self):
        dt = min(get_frame_time(), 0.05)
        self.anim_timer += dt

        if self.music_enabled:
            self.music.update()

        if is_key_pressed(KEY_M):
            self.music_enabled = not self.music_enabled
            if self.music_enabled:
                self.music.resume()
            else:
                self.music.pause()

        if is_key_pressed(KEY_R) and not self.category_dropdown_open:
            self.rescan()

        if self.pad_nav_cooldown > 0.0:
            self.pad_nav_cooldown -= dt
        if self.bumper_cooldown > 0.0:
            self.bumper_cooldown -= dt

        # Close category dropdown if top-bar settings dropdown opens
        if ui_settings.open_dropdown is not None:
            self.category_dropdown_open = False

        # Close category dropdown on ESC
        if self.category_dropdown_open and is_key_pressed(KEY_ESCAPE):
            self.category_dropdown_open = False
            self.sfx.play("click", 0.4)

        # 1. Section Bumper Cycling: [Q / E] or Gamepad [LB / RB]
        pad_id = get_active_gamepad_id()
        pad_lb = (pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_LEFT_TRIGGER_1))
        pad_rb = (pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_TRIGGER_1))

        if (is_key_pressed(KEY_Q) or pad_lb) and self.bumper_cooldown <= 0.0:
            self.cycle_section(-1)
            self.bumper_cooldown = 0.22
        elif (is_key_pressed(KEY_E) or pad_rb) and self.bumper_cooldown <= 0.0:
            self.cycle_section(1)
            self.bumper_cooldown = 0.22

        # Calculate max description scroll based on lines and font size
        right_h = 566
        viewport_h = right_h - 96
        line_step = max(16, 19 + ui_settings.font_size_offset)

        if self.filtered_entries:
            cur = self.filtered_entries[self.selected_idx]
            total_text_h = len(cur["body_lines"]) * line_step
            self.max_desc_scroll = max(0.0, float(total_text_h - viewport_h + 30))
        else:
            self.max_desc_scroll = 0.0

        # Gamepad Dual-Stick Polling
        pad_down = False
        pad_up = False
        self.r_stick_active = False

        if pad_id >= 0:
            if is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_LEFT_FACE_DOWN):
                pad_down = True
            elif is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_LEFT_FACE_UP):
                pad_up = True
            elif self.pad_nav_cooldown <= 0.0:
                l_stick_y = get_gamepad_axis_movement(pad_id, GAMEPAD_AXIS_LEFT_Y)
                if l_stick_y > 0.45:
                    pad_down = True
                    self.pad_nav_cooldown = 0.20
                elif l_stick_y < -0.45:
                    pad_up = True
                    self.pad_nav_cooldown = 0.20

            r_stick_y = get_gamepad_axis_movement(pad_id, GAMEPAD_AXIS_RIGHT_Y)
            if abs(r_stick_y) > 0.15:
                self.r_stick_active = True
                self.desc_scroll_y += r_stick_y * 450.0 * dt

        # Mouse & Keyboard Navigation
        prev_idx = self.selected_idx
        mx, my = get_mouse_x(), get_mouse_y()
        left_x, left_y, left_w, left_h = 24, 86, 420, 566
        right_x, right_y, right_w = 464, 86, 792

        # Dropdown button rectangle
        btn_x = left_x + 12
        btn_y = left_y + 28
        btn_w = left_w - 24
        btn_h = 36

        # Category Dropdown Menu bounds
        drop_menu_x = btn_x
        drop_menu_y = btn_y + btn_h + 2
        drop_menu_w = btn_w
        drop_menu_h = len(CATALOG_SECTIONS) * 32 + 6

        # Handle mouse interactions when no top-bar settings dropdown is open
        if ui_settings.open_dropdown is None:
            # Click on Category Dropdown Button
            if is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
                if btn_x <= mx <= btn_x + btn_w and btn_y <= my <= btn_y + btn_h:
                    self.category_dropdown_open = not self.category_dropdown_open
                    self.sfx.play("click", 0.5)
                elif self.category_dropdown_open:
                    # Check click on category dropdown items
                    if drop_menu_x <= mx <= drop_menu_x + drop_menu_w and drop_menu_y <= my <= drop_menu_y + drop_menu_h:
                        rel_y = my - (drop_menu_y + 3)
                        clicked_idx = int(rel_y / 32)
                        if 0 <= clicked_idx < len(CATALOG_SECTIONS):
                            self.set_section(CATALOG_SECTIONS[clicked_idx]["id"])
                            self.category_dropdown_open = False
                    else:
                        # Clicked outside dropdown -> close
                        self.category_dropdown_open = False

            # If dropdown is not open, handle script list interactions
            if not self.category_dropdown_open:
                wheel = get_mouse_wheel_move()

                if is_key_down(KEY_PAGE_DOWN):
                    self.desc_scroll_y += 450.0 * dt
                if is_key_down(KEY_PAGE_UP):
                    self.desc_scroll_y -= 450.0 * dt

                # Mouse wheel routing
                if wheel != 0:
                    if (right_x <= mx <= right_x + right_w) and (left_y <= my <= left_h + left_y):
                        self.desc_scroll_y -= wheel * 55.0
                    elif (left_x <= mx <= left_x + left_w) and (left_y <= my <= left_h + left_y):
                        if self.filtered_entries:
                            if wheel < 0:
                                self.selected_idx = (self.selected_idx + 1) % len(self.filtered_entries)
                            else:
                                self.selected_idx = (self.selected_idx - 1) % len(self.filtered_entries)

                # Script selection via Arrow keys / WASD / D-Pad
                if self.filtered_entries:
                    if is_key_pressed(KEY_DOWN) or is_key_pressed(KEY_S) or pad_down:
                        self.selected_idx = (self.selected_idx + 1) % len(self.filtered_entries)
                    elif is_key_pressed(KEY_UP) or is_key_pressed(KEY_W) or pad_up:
                        self.selected_idx = (self.selected_idx - 1) % len(self.filtered_entries)

                    # Click to select script in list
                    if is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
                        visible = self.filtered_entries[self.scroll_offset : self.scroll_offset + self.max_visible_items]
                        list_start_y = left_y + 96
                        for idx in range(len(visible)):
                            item_y = list_start_y + idx * 44
                            if (left_x + 10 <= mx <= left_x + left_w - 20) and (item_y <= my <= item_y + 38):
                                self.selected_idx = self.scroll_offset + idx
                                break

                # Scrollbar dragging
                sb_track_x = right_x + right_w - 14
                sb_track_y = left_y + 82
                sb_track_w = 8
                sb_track_h = left_h - 96
                if is_mouse_button_down(MOUSE_BUTTON_LEFT):
                    if (sb_track_x - 6 <= mx <= sb_track_x + sb_track_w + 6) and (sb_track_y <= my <= sb_track_y + sb_track_h):
                        rel = (my - sb_track_y) / float(sb_track_h)
                        self.desc_scroll_y = max(0.0, min(self.max_desc_scroll, rel * self.max_desc_scroll))

        # Reset description scroll to top when changing selection
        if self.selected_idx != prev_idx:
            self.desc_scroll_y = 0.0
            self.sfx.play("click", 0.45)

        self.desc_scroll_y = max(0.0, min(self.desc_scroll_y, self.max_desc_scroll))

        # Keep selected item visible in list scroll
        if self.filtered_entries:
            if self.selected_idx < self.scroll_offset:
                self.scroll_offset = self.selected_idx
            elif self.selected_idx >= self.scroll_offset + self.max_visible_items:
                self.scroll_offset = self.selected_idx - self.max_visible_items + 1

        # Launch or Smoke Test
        pad_launch = pad_id >= 0 and (
            is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_FACE_DOWN)
            or is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_MIDDLE_RIGHT)
        )
        pad_smoke = pad_id >= 0 and is_gamepad_button_pressed(pad_id, GAMEPAD_BUTTON_RIGHT_FACE_LEFT)

        if (is_key_pressed(KEY_ENTER) or is_key_pressed(KEY_SPACE) or pad_launch) and not self.category_dropdown_open:
            self.launch_selected(smoke_test=False)
        elif (is_key_pressed(KEY_S) or pad_smoke) and not self.category_dropdown_open:
            self.launch_selected(smoke_test=True)

    def draw(self):
        begin_drawing()
        clear_background(COLOR_BG)

        # Header Bar
        draw_rectangle(0, 0, SCREEN_WIDTH, 68, COLOR_PANEL)
        draw_line(0, 68, SCREEN_WIDTH, 68, COLOR_PANEL_BORDER)
        draw_text("GAME DESIGN PATTERNS HUB", 24, 15, 24, COLOR_ACCENT)
        draw_text(
            "Interactive Raylib Python Prototype Encyclopedia & Browser",
            24, 43, 14, COLOR_TEXT_DIM
        )

        # Global Top-Bar Settings Dropdowns (Font, Size, Window)
        draw_ui_settings_bar(450, 19)

        # Built Prototype Counter Badge
        badge_text = f"BUILT: {len(self.entries)} ({len(self.filtered_entries)} shown)"
        draw_rectangle(SCREEN_WIDTH - 256, 18, 232, 32, Color(26, 40, 68, 255))
        draw_rectangle_lines(SCREEN_WIDTH - 256, 18, 232, 32, COLOR_ACCENT)
        draw_text(badge_text, SCREEN_WIDTH - 242, 26, 14, WHITE)

        # Animated Mascot Preview
        draw_slime_enemy_2d(Vector2(SCREEN_WIDTH - 280.0, 35.0), self.anim_timer * 3.0, 14.0)

        # Left Panel: Category Dropdown & Script List
        left_x, left_y, left_w, left_h = 24, 86, 420, 566
        draw_rectangle(left_x, left_y, left_w, left_h, COLOR_PANEL)
        draw_rectangle_lines(left_x, left_y, left_w, left_h, COLOR_PANEL_BORDER)

        # Dropdown Header
        draw_text("CATALOG SECTION:", left_x + 14, left_y + 12, 11, COLOR_TEXT_DIM)
        draw_text("[Q/E or LB/RB to Cycle]", left_x + left_w - 146, left_y + 12, 11, COLOR_ACCENT)

        # Category Dropdown Button
        btn_x = left_x + 12
        btn_y = left_y + 28
        btn_w = left_w - 24
        btn_h = 36

        cur_sec_info = self.get_section_info(self.selected_section_id)
        btn_col = Color(32, 45, 72, 255) if self.category_dropdown_open else Color(24, 32, 52, 255)
        draw_rectangle(btn_x, btn_y, btn_w, btn_h, btn_col)
        draw_rectangle_lines(btn_x, btn_y, btn_w, btn_h, COLOR_ACCENT if self.category_dropdown_open else COLOR_PANEL_BORDER)

        # Category Button Text
        cat_badge = f"[{cur_sec_info['id']}]"
        draw_text(cat_badge, btn_x + 12, btn_y + 10, 14, COLOR_ACCENT)
        cat_label = f"{cur_sec_info['name']} ({len(self.filtered_entries)} built)"
        draw_text(cat_label, btn_x + 55, btn_y + 10, 14, WHITE)
        arrow_char = "^" if self.category_dropdown_open else "v"
        draw_text(arrow_char, btn_x + btn_w - 22, btn_y + 10, 14, COLOR_ACCENT)

        draw_line(left_x, left_y + 72, left_x + left_w, left_y + 72, COLOR_PANEL_BORDER)

        # Script List Header
        list_hdr = f"PROTOTYPES IN SECTION ({len(self.filtered_entries)}):"
        draw_text(list_hdr, left_x + 14, left_y + 78, 11, COLOR_TEXT_DIM)

        # Script List Rendering
        list_start_y = left_y + 96
        if not self.filtered_entries:
            # Empty state for 3.x categories with 0 built prototypes
            box_x = left_x + 14
            box_y = list_start_y + 10
            box_w = left_w - 28
            box_h = 240
            draw_rectangle(box_x, box_y, box_w, box_h, Color(16, 22, 36, 255))
            draw_rectangle_lines(box_x, box_y, box_w, box_h, COLOR_PANEL_BORDER)

            draw_text("NO PROTOTYPES BUILT YET", box_x + 18, box_y + 20, 15, COLOR_ACCENT)
            draw_text(cur_sec_info["name"], box_x + 18, box_y + 44, 13, WHITE)
            draw_text(f"{cur_sec_info['planned_count']} planned prototypes in minigames.md", box_x + 18, box_y + 68, 12, COLOR_TEXT_DIM)

            draw_line(box_x + 18, box_y + 90, box_x + box_w - 18, box_y + 90, COLOR_PANEL_BORDER)

            draw_text("To switch catalog sections:", box_x + 18, box_y + 104, 12, COLOR_TEXT_DIM)
            draw_text("• Press [Q / E] or Gamepad [LB / RB]", box_x + 18, box_y + 128, 12, COLOR_ACCENT)
            draw_text("• Click the category dropdown above", box_x + 18, box_y + 152, 12, COLOR_ACCENT)
            draw_text("• Select [All Categories] to see all 9", box_x + 18, box_y + 176, 12, COLOR_ACCENT)
        else:
            visible = self.filtered_entries[self.scroll_offset : self.scroll_offset + self.max_visible_items]
            has_left_sb = len(self.filtered_entries) > self.max_visible_items
            item_width = (left_w - 28) if has_left_sb else (left_w - 20)

            for idx, entry in enumerate(visible):
                actual_idx = self.scroll_offset + idx
                item_y = list_start_y + idx * 44
                is_sel = actual_idx == self.selected_idx
                bg_col = COLOR_ITEM_SELECTED if is_sel else COLOR_ITEM_HOVER
                draw_rectangle(left_x + 10, item_y, item_width, 38, bg_col)
                if is_sel:
                    draw_rectangle_lines(left_x + 10, item_y, item_width, 38, COLOR_ACCENT)

                # Section Tag Badge
                sec_badge = f"[{entry['section_id']}]"
                draw_text(sec_badge, left_x + 16, item_y + 11, 12, COLOR_ACCENT if is_sel else Color(130, 160, 205, 255))

                label = f"{entry['filename']}"
                draw_text(label, left_x + 58, item_y + 11, 14, WHITE if is_sel else COLOR_TEXT_MAIN)

                smoke_col = GREEN if "PASS" in entry["smoke_status"] else (RED if "FAIL" in entry["smoke_status"] else COLOR_TEXT_DIM)
                draw_text(f"{entry['lines']}L", left_x + item_width - 50, item_y + 12, 12, smoke_col)

            # Left Panel Scrollbar
            if has_left_sb:
                l_track_x = left_x + left_w - 14
                l_track_y = list_start_y
                l_track_w = 6
                l_track_h = self.max_visible_items * 44 - 6
                draw_rectangle(l_track_x, l_track_y, l_track_w, l_track_h, Color(20, 26, 42, 255))
                draw_rectangle_lines(l_track_x, l_track_y, l_track_w, l_track_h, Color(40, 52, 80, 255))
                l_thumb_ratio = self.max_visible_items / float(len(self.filtered_entries))
                l_thumb_h = max(24, int(l_track_h * l_thumb_ratio))
                l_max_scroll = len(self.filtered_entries) - self.max_visible_items
                l_thumb_y = l_track_y + int((l_track_h - l_thumb_h) * (self.scroll_offset / float(l_max_scroll)))
                draw_rectangle(l_track_x, l_thumb_y, l_track_w, l_thumb_h, Color(70, 160, 230, 255))

        # Right Panel: Docstring Inspector or Planned Catalog Overview
        right_x, right_y, right_w, right_h = 464, 86, 792, 566
        draw_rectangle(right_x, right_y, right_w, right_h, COLOR_PANEL)
        draw_rectangle_lines(right_x, right_y, right_w, right_h, COLOR_PANEL_BORDER)

        if self.filtered_entries:
            cur = self.filtered_entries[self.selected_idx]
            title_size = 20 if len(cur["title"]) < 58 else 18
            draw_text(cur["title"], right_x + 22, right_y + 16, title_size, GOLD)

            # Section & Script Metadata
            draw_rectangle(right_x + 22, right_y + 44, 100, 20, Color(24, 45, 75, 255))
            draw_rectangle_lines(right_x + 22, right_y + 44, 100, 20, COLOR_ACCENT)
            draw_text(f"Section {cur['section_id']}", right_x + 28, right_y + 48, 11, COLOR_ACCENT)

            rel_display = cur.get("rel_path", cur["filename"])
            meta = f"minigames/{rel_display} ({cur['lines']}L)  |  Smoke: {cur['smoke_status']}"
            draw_text(meta, right_x + 132, right_y + 47, 13, COLOR_TEXT_MAIN)
            draw_text("[R-Stick / Wheel] Scroll Doc", right_x + right_w - 232, right_y + 47, 12, Color(160, 185, 220, 255))
            draw_line(right_x, right_y + 72, right_x + right_w, right_y + 72, COLOR_PANEL_BORDER)

            viewport_y = right_y + 82
            viewport_h = right_h - 96
            line_step = max(16, 19 + ui_settings.font_size_offset)

            begin_scissor_mode(right_x + 10, int(viewport_y), right_w - 28, int(viewport_h))
            text_y = viewport_y + 6 - self.desc_scroll_y
            for line in cur["body_lines"]:
                if (text_y + line_step >= viewport_y) and (text_y <= viewport_y + viewport_h):
                    is_header = line.endswith(":") and not line.startswith(" ")
                    col = COLOR_ACCENT if is_header else COLOR_TEXT_MAIN
                    draw_text(line, right_x + 24, int(text_y), 15, col)
                text_y += line_step
            end_scissor_mode()

            # Right Panel Scrollbar
            sb_track_x = right_x + right_w - 14
            sb_track_y = viewport_y
            sb_track_w = 6
            sb_track_h = viewport_h
            draw_rectangle(sb_track_x, sb_track_y, sb_track_w, sb_track_h, Color(20, 26, 42, 255))
            draw_rectangle_lines(sb_track_x, sb_track_y, sb_track_w, sb_track_h, Color(40, 52, 80, 255))

            if self.max_desc_scroll > 0.0:
                thumb_ratio = viewport_h / (viewport_h + self.max_desc_scroll)
                thumb_h = max(32, int(sb_track_h * thumb_ratio))
                scroll_ratio = self.desc_scroll_y / self.max_desc_scroll
                thumb_y = sb_track_y + int((sb_track_h - thumb_h) * scroll_ratio)
                thumb_col = Color(0, 220, 255, 255) if self.r_stick_active else Color(65, 110, 175, 255)
                draw_rectangle(sb_track_x, thumb_y, sb_track_w, thumb_h, thumb_col)
                draw_rectangle_lines(sb_track_x, thumb_y, sb_track_w, thumb_h, Color(160, 215, 255, 255))
        else:
            # Right Panel Planned Section Overview
            draw_text(cur_sec_info["title"], right_x + 22, right_y + 16, 20, GOLD)
            meta = f"Planned Catalog ({cur_sec_info['planned_count']} prototypes documented in minigames.md)"
            draw_text(meta, right_x + 22, right_y + 46, 13, COLOR_ACCENT)
            draw_line(right_x, right_y + 72, right_x + right_w, right_y + 72, COLOR_PANEL_BORDER)

            draw_text("Category Overview & Learning Objectives:", right_x + 24, right_y + 90, 16, COLOR_ACCENT)
            draw_text(cur_sec_info["desc"], right_x + 24, right_y + 120, 15, COLOR_TEXT_MAIN)

            draw_text("Consult minigames.md to see the planned prototypes for this section.", right_x + 24, right_y + 170, 14, COLOR_TEXT_DIM)
            draw_text("Ask the agent: 'make <prototype name>' to implement any pattern from this category!", right_x + 24, right_y + 196, 14, COLOR_ACCENT_GOLD)

        # Bottom Controls & Status Bar
        draw_rectangle(0, SCREEN_HEIGHT - 54, SCREEN_WIDTH, 54, COLOR_PANEL)
        draw_line(0, SCREEN_HEIGHT - 54, SCREEN_WIDTH, SCREEN_HEIGHT - 54, COLOR_PANEL_BORDER)
        draw_text(
            "[L-Stick/Arrows] Select Script   [Q/E or LB/RB] Section Filter   [Enter/A] Launch   [S/X] Smoke-Test   [Ctrl +/-] Font   [F11] Fullscreen",
            24, SCREEN_HEIGHT - 44, 13, WHITE
        )
        draw_text(self.status_banner, 24, SCREEN_HEIGHT - 22, 13, self.status_color)
        draw_gamepad_status_badge(SCREEN_WIDTH - 340, SCREEN_HEIGHT - 21, 12)

        # Floating Category Dropdown Menu (Drawn on top of everything when open)
        if self.category_dropdown_open:
            drop_menu_x = btn_x
            drop_menu_y = btn_y + btn_h + 2
            drop_menu_w = btn_w
            drop_menu_h = len(CATALOG_SECTIONS) * 32 + 6

            draw_rectangle(drop_menu_x, drop_menu_y, drop_menu_w, drop_menu_h, Color(16, 22, 38, 255))
            draw_rectangle_lines(drop_menu_x, drop_menu_y, drop_menu_w, drop_menu_h, COLOR_ACCENT)

            mx, my = get_mouse_x(), get_mouse_y()

            for s_idx, sec in enumerate(CATALOG_SECTIONS):
                iy = drop_menu_y + 3 + s_idx * 32
                is_cur = (sec["id"] == self.selected_section_id)
                is_hov = (drop_menu_x <= mx <= drop_menu_x + drop_menu_w and iy <= my <= iy + 30)

                bg_c = Color(35, 65, 115, 255) if is_cur else (Color(28, 40, 68, 255) if is_hov else Color(16, 22, 38, 255))
                draw_rectangle(drop_menu_x + 2, iy, drop_menu_w - 4, 30, bg_c)

                # Built count badge
                if sec["id"] == CAT_ALL:
                    cnt = len(self.entries)
                else:
                    cnt = len([e for e in self.entries if e["section_id"] == sec["id"]])

                cnt_col = GREEN if cnt > 0 else Color(120, 135, 160, 255)
                cnt_str = f"{cnt} built"

                txt_col = GOLD if is_cur else (WHITE if is_hov else COLOR_TEXT_MAIN)
                draw_text(sec["name"], drop_menu_x + 12, iy + 7, 13, txt_col)
                draw_text(cnt_str, drop_menu_x + drop_menu_w - 75, iy + 8, 11, cnt_col)

        end_drawing()

    def run(self, smoke_test: bool = False):
        frame_count = 0
        while not window_should_close():
            self.update()
            self.draw()
            frame_count += 1
            if smoke_test and frame_count >= 3:
                break

        self.sfx.unload_all()
        self.music.unload()
        close_audio_device()
        close_window()


if __name__ == "__main__":
    is_smoke = "--smoke-test" in sys.argv
    PatternHubLauncher().run(smoke_test=is_smoke)
