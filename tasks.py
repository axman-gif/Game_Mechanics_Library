# -*- coding: utf-8 -*-
"""
Interactive Task Catalog & Spreadsheet Editor (tasks.py)
========================================================
Graphical Raylib Python application located in repository root to inspect, edit,
sort, and maintain all project tracking spreadsheets located in `tasks/`.

Features:
  - Hot runtime switching between all CSV catalogs in `tasks/`
    (minigames.csv, SFXs.csv, BGMs.csv, models_3D.csv, sprites_2D.csv).
  - Automated disk status synchronization (`--sync-statuses [catalog]`).
  - Binary status restriction (`pending` and `done`).
  - Pedagogical difficulty column support (`1 - Beginner` to `5 - Master`).
  - Strictly hides internal technical columns (`id` and `target_file`) from the
    visual table while preserving and auto-generating them faithfully on disk.
  - Alphanumeric column sorting (Ascending, Descending, Original Row Order).
  - Search / Filter bar for rapid keyword queries.
  - Cell editing for text and dropdown enum fields (status, difficulty, dimension, section).
  - Dedicated multi-select checklist modal for `patterns` populated dynamically
    from `rules/patterns.md` with real-time text search.
  - Safe row insertion (Above, Below, Duplicate, Delete) with zero-corruption guarantees.
  - Full integration with `utils/ui_settings.py` (Font switching, Font size Ctrl+/-,
    Window resolution, and Fullscreen F11).
  - Headless CLI queries and mutations (`--list`, `--get`, `--set-status`, `--check`, `--sync-statuses`, `--smoke-test`).

Usage:
  python -B tasks.py
  python -B tasks.py --smoke-test
  python -B tasks.py --sync-statuses [catalog]
  python -B tasks.py --list [catalog] [--difficulty <tier>] [--status <pending|done>]
  python -B tasks.py --get <catalog> <id_or_file>
  python -B tasks.py --set-status <catalog> <id_or_file> <status>
  python -B tasks.py --check <catalog> <name_or_func>
"""

import sys
import os
import csv
import re
import time
from typing import List, Dict, Optional, Set, Any

# 1. Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# 2. Add repository root to search path
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

# 3. Mandatory Raylib & modular imports
from pyray import *
from utils import *

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WINDOW_TITLE = "Tasks Catalog & Spreadsheet Editor (Raylib Python)"

# Visual UI Palette (Cybernetic Dark Theme matching launcher.py)
COLOR_BG = Color(10, 13, 22, 255)
COLOR_PANEL = Color(18, 23, 38, 255)
COLOR_PANEL_ALT = Color(14, 18, 30, 255)
COLOR_PANEL_BORDER = Color(48, 65, 105, 255)
COLOR_HEADER_BG = Color(24, 34, 56, 255)
COLOR_HOVER_ROW = Color(28, 42, 68, 255)
COLOR_SELECTED_ROW = Color(26, 52, 88, 255)
COLOR_SELECTED_CELL_BORDER = Color(70, 205, 255, 255)

COLOR_ACCENT = Color(70, 205, 255, 255)
COLOR_ACCENT_GOLD = Color(255, 215, 0, 255)
COLOR_ACCENT_GREEN = Color(60, 220, 120, 255)
COLOR_ACCENT_RED = Color(255, 80, 80, 255)

COLOR_TEXT_MAIN = Color(235, 242, 255, 255)
COLOR_TEXT_DIM = Color(145, 160, 185, 255)
COLOR_TEXT_MUTED = Color(95, 110, 135, 255)

COLOR_BADGE_DONE = Color(35, 140, 75, 255)
COLOR_BADGE_PENDING = Color(65, 80, 110, 255)
COLOR_BADGE_BUILT = COLOR_BADGE_DONE  # Backwards compatibility alias

# Canonical tracking spreadsheets in tasks/
CANONICAL_CATALOGS: List[str] = [
    "minigames.csv",
    "SFXs.csv",
    "BGMs.csv",
    "models_3D.csv",
    "sprites_2D.csv",
]

# Internal technical columns strictly hidden from the visual editing table
HIDDEN_COLUMNS: Set[str] = {"id", "target_file"}

# Canonical Column Widths for clean table layout
DEFAULT_COL_WIDTHS: Dict[str, int] = {
    "difficulty": 140,
    "section": 90,
    "dimension": 90,
    "status": 120,
    "type": 95,
    "category": 130,
    "vibe": 120,
    "title": 220,
    "concept_name": 220,
    "function_name": 220,
    "patterns": 310,
    "primitives_used": 190,
    "animation_features": 210,
    "palette_keys": 190,
    "audio_specs": 240,
    "description": 420,
}


def natural_sort_key(value: Any) -> list:
    """Splits string into numeric and string fragments for natural alphanumeric sorting."""
    s = str(value or "")
    fragments = []
    for token in re.split(r"(\d+)", s.lower()):
        if token.isdigit():
            fragments.append(int(token))
        else:
            fragments.append(token)
    return fragments


def wrap_cell_text(text: str, max_chars_per_line: int, max_lines: int = 3) -> List[str]:
    """Splits text into words and wraps across up to max_lines, appending ... if truncated."""
    if not text:
        return []
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        test = f"{cur} {w}".strip()
        if len(test) <= max_chars_per_line:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        truncated = lines[:max_lines]
        if len(truncated[-1]) + 3 <= max_chars_per_line:
            truncated[-1] = truncated[-1] + "..."
        else:
            truncated[-1] = truncated[-1][:max(1, max_chars_per_line - 3)] + "..."
        return truncated
    return lines


def handle_headless_cli(repo_root: str, args: List[str]) -> bool:
    """Handles CLI queries and mutations without launching Raylib window.
    Returns True if a CLI command was processed, False otherwise.
    """
    tasks_dir = os.path.join(repo_root, "tasks")

    def resolve_csv_paths(cat_name: str) -> List[str]:
        c_lower = cat_name.lower().replace(".csv", "")
        if c_lower in ("sfx", "sfxs"):
            return [os.path.join(tasks_dir, "SFXs.csv")]
        elif c_lower in ("bgm", "bgms"):
            return [os.path.join(tasks_dir, "BGMs.csv")]
        elif c_lower == "audio":
            paths = []
            sfx_p = os.path.join(tasks_dir, "SFXs.csv")
            bgm_p = os.path.join(tasks_dir, "BGMs.csv")
            if os.path.exists(sfx_p):
                paths.append(sfx_p)
            if os.path.exists(bgm_p):
                paths.append(bgm_p)
            if not paths:
                fallback = os.path.join(tasks_dir, "audio.csv")
                if os.path.exists(fallback):
                    paths.append(fallback)
            return paths
        elif c_lower in ("models_3d", "models3d", "models", "model"):
            return [os.path.join(tasks_dir, "models_3D.csv")]
        elif c_lower in ("sprites_2d", "sprites2d", "sprites", "sprite"):
            return [os.path.join(tasks_dir, "sprites_2D.csv")]
        elif c_lower in ("minigames", "minigame", "games", "game"):
            return [os.path.join(tasks_dir, "minigames.csv")]
        else:
            clean = cat_name if cat_name.endswith(".csv") else f"{cat_name}.csv"
            if os.path.isdir(tasks_dir):
                for f in os.listdir(tasks_dir):
                    if f.lower() == clean.lower():
                        return [os.path.join(tasks_dir, f)]
            return [os.path.join(tasks_dir, clean)]

    if "--sync-statuses" in args:
        idx = args.index("--sync-statuses")
        cat_arg = None
        if idx + 1 < len(args) and not args[idx + 1].startswith("--"):
            cat_arg = args[idx + 1]

        if cat_arg:
            target_paths = resolve_csv_paths(cat_arg)
        else:
            target_paths = [os.path.join(tasks_dir, c) for c in CANONICAL_CATALOGS]

        total_tasks = 0
        total_done = 0
        total_pending = 0
        total_updated = 0
        catalogs_synced = 0

        for path in target_paths:
            if not os.path.exists(path):
                print(f"[WARN] Catalog file not found: {path}")
                continue

            rel_name = os.path.relpath(path, repo_root).replace("\\", "/")
            fieldnames = []
            rows = []
            with open(path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                fieldnames = list(reader.fieldnames or [])
                for r in reader:
                    rows.append(r)

            cat_done = 0
            cat_pending = 0
            cat_updated = 0

            for r in rows:
                target_file = (r.get("target_file") or "").strip()
                if target_file:
                    full_path = target_file if os.path.isabs(target_file) else os.path.join(repo_root, target_file)
                    full_path = os.path.normpath(full_path)
                    file_exists = os.path.isfile(full_path)
                else:
                    file_exists = False

                expected_status = "done" if file_exists else "pending"
                cur_status = (r.get("status") or "").strip().lower()

                if cur_status != expected_status:
                    cat_updated += 1

                r["status"] = expected_status

                if expected_status == "done":
                    cat_done += 1
                else:
                    cat_pending += 1

            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
                writer.writeheader()
                writer.writerows(rows)

            print(f"[SYNC] {rel_name}: {len(rows)} tasks -> {cat_done} done, {cat_pending} pending ({cat_updated} updated)")

            total_tasks += len(rows)
            total_done += cat_done
            total_pending += cat_pending
            total_updated += cat_updated
            catalogs_synced += 1

        print(f"[SYNC COMPLETE] Total synced: {total_tasks} tasks across {catalogs_synced} catalog(s) ({total_done} done, {total_pending} pending, {total_updated} updated).")
        return True

    if "--list" in args:
        idx = args.index("--list")
        cat_arg = args[idx + 1] if idx + 1 < len(args) and not args[idx + 1].startswith("--") else "minigames"

        # Parse filters
        section_filter = None
        category_filter = None
        status_filter = None
        type_filter = None
        vibe_filter = None
        difficulty_filter = None
        limit_val = None

        if "--section" in args:
            s_idx = args.index("--section")
            if s_idx + 1 < len(args):
                section_filter = args[s_idx + 1]
        if "--category" in args:
            c_idx = args.index("--category")
            if c_idx + 1 < len(args):
                category_filter = args[c_idx + 1]
        if "--status" in args:
            st_idx = args.index("--status")
            if st_idx + 1 < len(args):
                status_filter = args[st_idx + 1].lower().strip()
        if "--type" in args:
            t_idx = args.index("--type")
            if t_idx + 1 < len(args):
                type_filter = args[t_idx + 1].upper()
        if "--vibe" in args:
            v_idx = args.index("--vibe")
            if v_idx + 1 < len(args):
                vibe_filter = args[v_idx + 1].lower()
        if "--difficulty" in args:
            d_idx = args.index("--difficulty")
            if d_idx + 1 < len(args):
                difficulty_filter = args[d_idx + 1].lower().strip()
        if "--limit" in args:
            l_idx = args.index("--limit")
            if l_idx + 1 < len(args) and args[l_idx + 1].isdigit():
                limit_val = int(args[l_idx + 1])

        # Filter resolution for audio aliases
        paths = resolve_csv_paths(cat_arg)
        if type_filter == "SFX" and len(paths) > 1:
            paths = [p for p in paths if "sfx" in os.path.basename(p).lower()]
        elif (type_filter == "BGM" or vibe_filter) and len(paths) > 1:
            paths = [p for p in paths if "bgm" in os.path.basename(p).lower()]

        if not paths or not any(os.path.exists(p) for p in paths):
            print(f"[ERROR] Catalog file not found for: {cat_arg}")
            return True

        count = 0
        for path in paths:
            if not os.path.exists(path):
                continue
            cat_name = os.path.basename(path).lower()
            with open(path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    if section_filter and r.get("section") != section_filter:
                        continue
                    if category_filter and r.get("category") != category_filter:
                        continue
                    if status_filter:
                        r_st = r.get("status", "").lower().strip()
                        if status_filter == "done" and r_st in ("done", "built"):
                            pass
                        elif r_st != status_filter:
                            continue
                    if type_filter and r.get("type", "").upper() != type_filter:
                        continue
                    if vibe_filter and r.get("vibe", "").lower() != vibe_filter:
                        continue
                    if difficulty_filter and difficulty_filter not in r.get("difficulty", "").lower():
                        continue

                    r_id = r.get("id", "")
                    r_status = r.get("status", "")
                    r_file = r.get("target_file", "")

                    if "minigames" in cat_name:
                        r_diff = r.get("difficulty", "")
                        r_sec = r.get("section", "")
                        r_title = r.get("title", "")
                        r_dim = r.get("dimension", "")
                        r_pat = r.get("patterns", "")
                        if r_diff:
                            print(f"{r_id} | {r_diff} | {r_sec} | {r_title} | {r_dim} | {r_file} | {r_pat} | {r_status}")
                        else:
                            print(f"{r_id} | {r_sec} | {r_title} | {r_dim} | {r_file} | {r_pat} | {r_status}")
                    elif "bgm" in cat_name:
                        r_type = r.get("type", "BGM")
                        r_cat = r.get("category", "")
                        r_vibe = r.get("vibe", "")
                        r_fn = r.get("function_name", "")
                        r_spec = r.get("audio_specs", "")
                        print(f"{r_id} | {r_type} | {r_cat} | {r_vibe} | {r_fn} | {r_file} | {r_spec} | {r_status}")
                    elif "sfx" in cat_name or "audio" in cat_name:
                        r_type = r.get("type", "SFX")
                        r_cat = r.get("category", "")
                        r_fn = r.get("function_name", "")
                        r_spec = r.get("audio_specs", "")
                        print(f"{r_id} | {r_type} | {r_cat} | {r_fn} | {r_file} | {r_spec} | {r_status}")
                    else:
                        r_cat = r.get("category", "")
                        r_name = r.get("concept_name", "")
                        r_fn = r.get("function_name", "")
                        r_prim = r.get("primitives_used", "")
                        print(f"{r_id} | {r_cat} | {r_name} | {r_fn} | {r_file} | {r_prim} | {r_status}")

                    count += 1
                    if limit_val and count >= limit_val:
                        break
            if limit_val and count >= limit_val:
                break
        print(f"[Total matching: {count}]")
        return True

    if "--get" in args:
        idx = args.index("--get")
        if idx + 2 >= len(args):
            print("[ERROR] Usage: python -B tasks.py --get <catalog> <id_or_file>")
            return True
        cat_arg = args[idx + 1]
        target_key = args[idx + 2]
        paths = resolve_csv_paths(cat_arg)
        found = False
        for path in paths:
            if not os.path.exists(path):
                continue
            with open(path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    if r.get("id") == target_key or r.get("target_file") == target_key or r.get("target_file", "").endswith(target_key):
                        found = True
                        for k, v in r.items():
                            print(f"{k}: {v}")
                        break
            if found:
                break
        if not found:
            print(f"[NOT FOUND] No record matching '{target_key}' in {cat_arg}")
        return True

    if "--set-status" in args:
        idx = args.index("--set-status")
        if idx + 3 >= len(args):
            print("[ERROR] Usage: python -B tasks.py --set-status <catalog> <id_or_file> <status>")
            return True
        cat_arg = args[idx + 1]
        target_key = args[idx + 2]
        new_status = args[idx + 3].lower().strip()
        if new_status not in ("pending", "done"):
            print(f"[ERROR] Invalid status '{new_status}'. Permitted status values are strictly: 'pending', 'done'")
            return True
        paths = resolve_csv_paths(cat_arg)
        updated = False
        target_path_updated = ""
        for path in paths:
            if not os.path.exists(path):
                continue
            rows = []
            fieldnames = []
            with open(path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                fieldnames = list(reader.fieldnames or [])
                for r in reader:
                    if (r.get("id") == target_key or r.get("target_file") == target_key or r.get("target_file", "").endswith(target_key)) and not updated:
                        r["status"] = new_status
                        updated = True
                        target_path_updated = path
                    rows.append(r)
            if updated and target_path_updated == path:
                with open(path, "w", encoding="utf-8-sig", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
                    writer.writeheader()
                    writer.writerows(rows)
                break
        if updated:
            print(f"[OK] Updated status to '{new_status}' for '{target_key}' in {os.path.basename(target_path_updated)}")
        else:
            print(f"[ERROR] Target '{target_key}' not found in {cat_arg}")
        return True

    if "--check" in args:
        idx = args.index("--check")
        if idx + 2 >= len(args):
            print("[ERROR] Usage: python -B tasks.py --check <catalog> <name_or_func>")
            return True
        cat_arg = args[idx + 1]
        target_name = args[idx + 2].lower()
        paths = resolve_csv_paths(cat_arg)
        matches = []
        for path in paths:
            if not os.path.exists(path):
                continue
            with open(path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    for k in ("id", "function_name", "concept_name", "title", "target_file", "vibe"):
                        if target_name in r.get(k, "").lower():
                            matches.append(f"{r.get('id')} | {r.get(k)} | {r.get('target_file')}")
                            break
        if matches:
            print(f"[EXISTS] {len(matches)} match(es) for '{target_name}':")
            for m in matches:
                print(f"  - {m}")
        else:
            print(f"[AVAILABLE] '{target_name}' not found in {cat_arg}")
        return True

    return False


def load_patterns_from_md(repo_root: str) -> List[str]:
    """Dynamically parses patterns.md for all pattern headings (### X.Y <Title>)."""
    patterns_path = os.path.join(repo_root, "rules", "patterns.md")
    if not os.path.exists(patterns_path):
        patterns_path = os.path.join(repo_root, "patterns.md")
    if not os.path.exists(patterns_path):
        return [
            "Game Loop", "Update Method", "Component Pattern", "Command Pattern",
            "State Machine (FSM)", "Object Pool", "Spatial Partitioning",
            "Steering Behaviors", "Behavior Tree (BT)", "A* Pathfinding"
        ]
    try:
        with open(patterns_path, "r", encoding="utf-8") as f:
            content = f.read()
        matches = re.findall(r"^###\s+[\d\.]+\s+(.+)$", content, flags=re.MULTILINE)
        cleaned = [m.strip() for m in matches if m.strip()]
        if cleaned:
            return sorted(list(dict.fromkeys(cleaned)))
    except Exception as exc:
        print(f"[WARN] Failed to parse patterns.md: {exc}")

    return [
        "Game Loop", "Update Method", "Command Pattern", "State Machine (FSM)",
        "Object Pool", "Spatial Partitioning (SpatialGrid2D)", "Behavior Tree (BT)"
    ]


class TasksEditor:
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)

        self.repo_root = ROOT_DIR
        self.tasks_dir = os.path.join(self.repo_root, "tasks")
        os.makedirs(self.tasks_dir, exist_ok=True)

        # Dynamic pattern catalog from patterns.md
        self.available_patterns = load_patterns_from_md(self.repo_root)

        # Discovered CSV files
        self.csv_files: List[str] = []
        self._discover_csv_files()

        # Data store per file: filename -> dict
        # { "fieldnames": [...], "rows": [...], "is_dirty": False, "sort_col": None, "sort_dir": 0 }
        self.file_data: Dict[str, dict] = {}
        self.active_file_idx = 0

        # Load all CSVs
        for fname in self.csv_files:
            self._load_csv_file(fname)

        # Table selection and scroll
        self.selected_row_idx = 0
        self.selected_col_idx = 0
        self.scroll_y = 0
        self.scroll_x = 0
        self.filter_text = ""
        self.is_filtering = False

        # Adjusted text (Wrap text) feature
        self.wrap_text = False

        # Horizontal scrollbar dragging state
        self.is_dragging_hscroll = False
        self.drag_hscroll_start_mx = 0
        self.drag_hscroll_start_scroll_x = 0

        # Status & notification banner
        self.status_banner = "Welcome to Tasks Editor. Use [Ctrl+S] to save changes, [Tab] to switch files."
        self.status_color = COLOR_ACCENT
        self.status_timer = 5.0

        # Modal Dialogs:
        # None, "text_edit", "patterns_select", "enum_select", "confirm_delete", "confirm_switch"
        self.active_modal: Optional[str] = None

        # Text editor modal state
        self.edit_buffer = ""
        self.edit_row_target = 0
        self.edit_col_name = ""
        self.edit_cursor_pos = 0

        # Pattern checklist modal state
        self.pattern_filter = ""
        self.pattern_checked_set: Set[str] = set()
        self.pattern_scroll_y = 0

        # Enum selector modal state
        self.enum_options: List[str] = []
        self.enum_target_row = 0
        self.enum_target_col = ""
        self.enum_selected_idx = 0

        # Confirmation modal state
        self.confirm_title = ""
        self.confirm_message = ""
        self.confirm_callback = None
        self.pending_switch_idx = -1

        # Double click timing
        self.last_click_time = 0.0
        self.last_clicked_cell = (-1, -1)

    def _discover_csv_files(self):
        """Scans the tasks/ directory for all CSV files."""
        candidates = CANONICAL_CATALOGS
        found = []
        # Preferred order first
        for name in candidates:
            p = os.path.join(self.tasks_dir, name)
            if os.path.exists(p):
                found.append(name)

        # Then any extra .csv files in tasks/
        if os.path.isdir(self.tasks_dir):
            for entry in sorted(os.listdir(self.tasks_dir)):
                if entry.endswith(".csv") and entry not in found:
                    found.append(entry)

        self.csv_files = found
        if not self.csv_files:
            # Fallback placeholder if directory empty
            dummy = "tasks_placeholder.csv"
            dummy_path = os.path.join(self.tasks_dir, dummy)
            with open(dummy_path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["id", "title", "target_file", "status", "description"])
                writer.writerow(["task_001", "Initial Task", "none.py", "pending", "Description"])
            self.csv_files = [dummy]

    def _load_csv_file(self, fname: str):
        """Loads a single CSV file with utf-8-sig, preserving fieldnames and rows."""
        path = os.path.join(self.tasks_dir, fname)
        rows: List[dict] = []
        fieldnames: List[str] = []
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    fieldnames = list(reader.fieldnames or [])
                    for r in reader:
                        # Clean whitespace and None values
                        clean_row = {}
                        for k in fieldnames:
                            clean_row[k] = (r.get(k) or "").strip()
                        rows.append(clean_row)
            except Exception as exc:
                print(f"[ERROR] Failed to load {fname}: {exc}")

        # Compute visible columns (excluding hidden columns)
        visible_cols = [c for c in fieldnames if c not in HIDDEN_COLUMNS]

        self.file_data[fname] = {
            "fieldnames": fieldnames,
            "visible_cols": visible_cols,
            "rows": rows,
            "original_order": list(range(len(rows))),
            "is_dirty": False,
            "sort_col": None,
            "sort_dir": 0,  # 0: original, 1: asc, -1: desc
        }

    def get_current_fname(self) -> str:
        if 0 <= self.active_file_idx < len(self.csv_files):
            return self.csv_files[self.active_file_idx]
        return ""

    def get_current_data(self) -> dict:
        fname = self.get_current_fname()
        return self.file_data.get(fname, {"fieldnames": [], "visible_cols": [], "rows": [], "is_dirty": False})

    def get_filtered_rows_indices(self) -> List[int]:
        """Returns the indices into data['rows'] that match the current search filter."""
        data = self.get_current_data()
        rows = data.get("rows", [])
        if not self.filter_text:
            return list(range(len(rows)))

        q = self.filter_text.lower().strip()
        matching = []
        for i, row in enumerate(rows):
            match = False
            for col_name in data["visible_cols"]:
                if q in str(row.get(col_name, "")).lower():
                    match = True
                    break
            if match:
                matching.append(i)
        return matching

    def save_active_file(self):
        """Saves current active CSV back to tasks/ with exact schema and UTF-8 encoding."""
        fname = self.get_current_fname()
        if not fname:
            return
        data = self.get_current_data()
        path = os.path.join(self.tasks_dir, fname)

        fieldnames = data["fieldnames"]
        rows = data["rows"]

        try:
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
                writer.writeheader()
                for r in rows:
                    # Guarantee all keys exist
                    row_dict = {k: r.get(k, "") for k in fieldnames}
                    writer.writerow(row_dict)

            data["is_dirty"] = False
            self.status_banner = f"Successfully saved tasks/{fname} ({len(rows)} rows)!"
            self.status_color = COLOR_ACCENT_GREEN
            self.status_timer = 4.0
        except Exception as exc:
            self.status_banner = f"Failed to save tasks/{fname}: {exc}"
            self.status_color = COLOR_ACCENT_RED
            self.status_timer = 6.0

    def reload_active_file(self):
        """Discards memory state and reloads the current active file from disk."""
        fname = self.get_current_fname()
        if not fname:
            return
        self._load_csv_file(fname)
        self.selected_row_idx = 0
        self.status_banner = f"Reloaded tasks/{fname} from disk."
        self.status_color = COLOR_ACCENT
        self.status_timer = 3.0

    def sort_by_column(self, col_name: str):
        """Cycles sort order: Ascending -> Descending -> Original Row Order."""
        data = self.get_current_data()
        cur_sort_col = data.get("sort_col")
        cur_sort_dir = data.get("sort_dir", 0)

        if cur_sort_col != col_name:
            new_dir = 1
        else:
            if cur_sort_dir == 1:
                new_dir = -1
            elif cur_sort_dir == -1:
                new_dir = 0
            else:
                new_dir = 1

        data["sort_col"] = col_name if new_dir != 0 else None
        data["sort_dir"] = new_dir

        if new_dir == 0:
            # Restore original order
            indexed = list(enumerate(data["rows"]))
            # Sort back by original index stored in row tag if available, or keep current
            self.status_banner = f"Reset sort order to default for {self.get_current_fname()}."
        elif new_dir == 1:
            data["rows"].sort(key=lambda r: natural_sort_key(r.get(col_name, "")))
            self.status_banner = f"Sorted by '{col_name}' Ascending [▲]."
        else:
            data["rows"].sort(key=lambda r: natural_sort_key(r.get(col_name, "")), reverse=True)
            self.status_banner = f"Sorted by '{col_name}' Descending [▼]."

        self.status_color = COLOR_ACCENT
        self.status_timer = 3.0
        self.selected_row_idx = 0

    def switch_file(self, target_idx: int):
        """Switches to another CSV file with unsaved modifications check."""
        if target_idx == self.active_file_idx:
            return
        current_data = self.get_current_data()
        if current_data.get("is_dirty", False):
            # Show confirmation modal
            self.pending_switch_idx = target_idx
            self.active_modal = "confirm_switch"
            return

        self._do_switch_file(target_idx)

    def _do_switch_file(self, target_idx: int):
        self.active_file_idx = target_idx
        self.selected_row_idx = 0
        self.selected_col_idx = 0
        self.scroll_y = 0
        self.scroll_x = 0
        self.filter_text = ""
        fname = self.get_current_fname()
        self.status_banner = f"Switched to tasks/{fname} ({len(self.get_current_data().get('rows', []))} rows)."
        self.status_color = COLOR_ACCENT
        self.status_timer = 3.0

    def generate_new_row(self, insert_position_hint: int) -> dict:
        """Auto-generates a clean new row with unique ID and target_file matching catalog schema."""
        data = self.get_current_data()
        fname = self.get_current_fname()
        fieldnames = data["fieldnames"]
        new_row = {k: "" for k in fieldnames}

        # Unique suffix from timestamp
        suffix = f"{int(time.time() * 10) % 100000:05d}"

        if "minigames" in fname:
            # Infer section and difficulty from neighboring row if possible
            sec = "3.2"
            rows = data["rows"]
            if 0 <= insert_position_hint < len(rows):
                sec = rows[insert_position_hint].get("section", "3.2")
            sec_clean = sec.replace(".", "")
            new_row["id"] = f"mg_{sec_clean}_{suffix}_custom"
            if "difficulty" in fieldnames:
                diff = "2 - Novice"
                if 0 <= insert_position_hint < len(rows):
                    diff = rows[insert_position_hint].get("difficulty", "2 - Novice") or "2 - Novice"
                new_row["difficulty"] = diff
            new_row["section"] = sec
            new_row["title"] = f"New Prototype {suffix}"
            new_row["dimension"] = "2D"
            new_row["target_file"] = f"minigames/3.x_category/prototype_{suffix}.py"
            new_row["patterns"] = "Game Loop, Update Method"
            new_row["status"] = "pending"
            new_row["description"] = "Pedagogical description of the target mechanics."

        elif "sfx" in fname.lower():
            cat = "combat"
            rows = data["rows"]
            if 0 <= insert_position_hint < len(rows):
                cat = rows[insert_position_hint].get("category", "combat")
            new_row["id"] = f"sfx_{cat}_{suffix}"
            new_row["type"] = "SFX"
            new_row["category"] = cat
            new_row["function_name"] = f"create_{cat}_sound_{suffix}"
            new_row["target_file"] = f"assets/audio/SFX/{cat}/sound_{suffix}.py"
            new_row["audio_specs"] = "44.1kHz 16-bit Mono Sine Wave"
            new_row["status"] = "pending"
            new_row["description"] = "Procedural audio synthesizer description."

        elif "bgm" in fname.lower():
            cat = "music"
            vibe = "energetic"
            rows = data["rows"]
            if 0 <= insert_position_hint < len(rows):
                cat = rows[insert_position_hint].get("category", "music")
                vibe = rows[insert_position_hint].get("vibe", "energetic")
            new_row["id"] = f"bgm_{vibe}_{suffix}"
            new_row["type"] = "BGM"
            new_row["category"] = cat
            new_row["vibe"] = vibe
            new_row["function_name"] = f"generate_{vibe}_track_{suffix}"
            new_row["target_file"] = f"assets/audio/BGM/{vibe}/track_{suffix}.py"
            new_row["audio_specs"] = "120.0 BPM | A minor | 8-bar loop"
            new_row["status"] = "pending"
            new_row["description"] = "Procedural background music stream description."

        elif "audio" in fname:
            cat = "combat"
            typ = "sfx"
            rows = data["rows"]
            if 0 <= insert_position_hint < len(rows):
                cat = rows[insert_position_hint].get("category", "combat")
                typ = rows[insert_position_hint].get("type", "sfx")
            new_row["id"] = f"{typ}_{cat}_{suffix}"
            new_row["type"] = typ
            new_row["category"] = cat
            new_row["function_name"] = f"create_{cat}_sound_{suffix}"
            subfolder = "SFX" if typ.lower() == "sfx" else "BGM"
            new_row["target_file"] = f"assets/audio/{subfolder}/{cat}/sound_{suffix}.py"
            new_row["audio_specs"] = "44.1kHz 16-bit Mono Sine Wave"
            new_row["status"] = "pending"
            new_row["description"] = "Procedural audio synthesizer description."

        elif "models_3D" in fname:
            cat = "humanoid"
            rows = data["rows"]
            if 0 <= insert_position_hint < len(rows):
                cat = rows[insert_position_hint].get("category", "humanoid")
            new_row["id"] = f"m3d_{cat}_{suffix}"
            new_row["category"] = cat
            new_row["concept_name"] = f"Model {suffix}"
            new_row["function_name"] = f"draw_model_{suffix}_3d"
            new_row["target_file"] = f"assets/models_3D/model_{suffix}.py"
            new_row["primitives_used"] = "Spheres, Cylinders, Cubes"
            new_row["animation_features"] = "Procedural walk bobbing"
            new_row["palette_keys"] = "armor, joints, visor"
            new_row["status"] = "pending"
            new_row["description"] = "3D procedural primitive model specification."

        elif "sprites_2D" in fname:
            cat = "top_down"
            rows = data["rows"]
            if 0 <= insert_position_hint < len(rows):
                cat = rows[insert_position_hint].get("category", "top_down")
            new_row["id"] = f"s2d_{cat}_{suffix}"
            new_row["category"] = cat
            new_row["concept_name"] = f"Sprite {suffix}"
            new_row["function_name"] = f"draw_sprite_{suffix}_2d"
            new_row["target_file"] = f"assets/sprites_2D/sprite_{suffix}.py"
            new_row["primitives_used"] = "Circles, Rectangles, Lines"
            new_row["animation_features"] = "Breathing squash and stretch"
            new_row["palette_keys"] = "body, outline, core"
            new_row["status"] = "pending"
            new_row["description"] = "2D procedural primitive sprite specification."

        else:
            new_row["id"] = f"task_{suffix}"
            new_row["target_file"] = f"tasks/task_{suffix}.py"
            new_row["status"] = "pending"
            new_row["description"] = "Custom task description."

        if "difficulty" in fieldnames and not new_row.get("difficulty"):
            diff = "2 - Novice"
            rows = data.get("rows", [])
            if 0 <= insert_position_hint < len(rows):
                diff = rows[insert_position_hint].get("difficulty", "2 - Novice") or "2 - Novice"
            new_row["difficulty"] = diff

        return new_row

    def insert_row(self, position: str = "below"):
        """Inserts a new row above or below the selected row."""
        data = self.get_current_data()
        rows = data["rows"]
        matching = self.get_filtered_rows_indices()

        if matching and 0 <= self.selected_row_idx < len(matching):
            actual_idx = matching[self.selected_row_idx]
        else:
            actual_idx = len(rows)

        insert_at = actual_idx if position == "above" else actual_idx + 1
        insert_at = max(0, min(len(rows), insert_at))

        new_row = self.generate_new_row(actual_idx)
        rows.insert(insert_at, new_row)
        data["is_dirty"] = True

        self.status_banner = f"Inserted new row at position #{insert_at + 1}."
        self.status_color = COLOR_ACCENT_GREEN
        self.status_timer = 3.0

        # Adjust selection
        matching_new = self.get_filtered_rows_indices()
        if insert_at in matching_new:
            self.selected_row_idx = matching_new.index(insert_at)

    def duplicate_selected_row(self):
        """Duplicates the currently selected row with a unique ID and marks dirty."""
        data = self.get_current_data()
        rows = data["rows"]
        matching = self.get_filtered_rows_indices()
        if not matching or not (0 <= self.selected_row_idx < len(matching)):
            return

        actual_idx = matching[self.selected_row_idx]
        source = rows[actual_idx]
        clone = dict(source)

        suffix = f"{int(time.time() * 10) % 100000:05d}"
        if "id" in clone:
            clone["id"] = f"{clone['id']}_copy_{suffix}"
        if "target_file" in clone and clone["target_file"]:
            base, ext = os.path.splitext(clone["target_file"])
            clone["target_file"] = f"{base}_copy_{suffix}{ext}"
        if "title" in clone:
            clone["title"] = f"{clone['title']} (Copy)"
        elif "concept_name" in clone:
            clone["concept_name"] = f"{clone['concept_name']} (Copy)"

        clone["status"] = "pending"

        rows.insert(actual_idx + 1, clone)
        data["is_dirty"] = True

        self.status_banner = f"Duplicated row #{actual_idx + 1} with new ID."
        self.status_color = COLOR_ACCENT_GREEN
        self.status_timer = 3.0
        self.selected_row_idx += 1

    def delete_selected_row(self):
        """Opens confirmation modal to delete the selected row."""
        matching = self.get_filtered_rows_indices()
        if not matching or not (0 <= self.selected_row_idx < len(matching)):
            return
        actual_idx = matching[self.selected_row_idx]
        data = self.get_current_data()
        row = data["rows"][actual_idx]
        label = row.get("title") or row.get("concept_name") or row.get("function_name") or f"Row #{actual_idx + 1}"

        self.confirm_title = "Confirm Row Deletion"
        self.confirm_message = f"Are you sure you want to permanently delete:\n'{label}'?\n\nThis cannot be undone once saved."
        self.confirm_callback = self._do_delete_row
        self.active_modal = "confirm_delete"

    def _do_delete_row(self):
        data = self.get_current_data()
        rows = data["rows"]
        matching = self.get_filtered_rows_indices()
        if matching and 0 <= self.selected_row_idx < len(matching):
            actual_idx = matching[self.selected_row_idx]
            del rows[actual_idx]
            data["is_dirty"] = True
            self.status_banner = f"Deleted row #{actual_idx + 1}."
            self.status_color = COLOR_ACCENT_RED
            self.status_timer = 3.0
            if self.selected_row_idx >= len(self.get_filtered_rows_indices()):
                self.selected_row_idx = max(0, len(self.get_filtered_rows_indices()) - 1)

    def open_cell_editor(self):
        """Opens appropriate editor modal based on the selected cell's column."""
        data = self.get_current_data()
        matching = self.get_filtered_rows_indices()
        visible_cols = data["visible_cols"]

        if not matching or not (0 <= self.selected_row_idx < len(matching)):
            return
        if not (0 <= self.selected_col_idx < len(visible_cols)):
            return

        actual_row_idx = matching[self.selected_row_idx]
        col_name = visible_cols[self.selected_col_idx]
        current_val = data["rows"][actual_row_idx].get(col_name, "")

        if col_name == "patterns":
            # Open Multi-Select Patterns Modal
            self.pattern_filter = ""
            self.pattern_scroll_y = 0
            # Pre-check current patterns
            active_patterns = [p.strip() for p in current_val.split(",") if p.strip()]
            self.pattern_checked_set = set(active_patterns)
            self.edit_row_target = actual_row_idx
            self.active_modal = "patterns_select"

        elif col_name == "status":
            self.enum_options = ["pending", "done"]
            self.enum_target_row = actual_row_idx
            self.enum_target_col = col_name
            self.enum_selected_idx = 0
            if current_val in self.enum_options:
                self.enum_selected_idx = self.enum_options.index(current_val)
            self.active_modal = "enum_select"

        elif col_name == "difficulty":
            self.enum_options = [
                "1 - Beginner",
                "2 - Novice",
                "3 - Intermediate",
                "4 - Advanced",
                "5 - Master",
            ]
            self.enum_target_row = actual_row_idx
            self.enum_target_col = col_name
            self.enum_selected_idx = 0
            if current_val in self.enum_options:
                self.enum_selected_idx = self.enum_options.index(current_val)
            self.active_modal = "enum_select"

        elif col_name == "dimension":
            self.enum_options = ["2D", "3D"]
            self.enum_target_row = actual_row_idx
            self.enum_target_col = col_name
            self.enum_selected_idx = 0
            if current_val in self.enum_options:
                self.enum_selected_idx = self.enum_options.index(current_val)
            self.active_modal = "enum_select"

        elif col_name == "section":
            self.enum_options = ["3.0", "3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7"]
            self.enum_target_row = actual_row_idx
            self.enum_target_col = col_name
            self.enum_selected_idx = 0
            if current_val in self.enum_options:
                self.enum_selected_idx = self.enum_options.index(current_val)
            self.active_modal = "enum_select"

        elif col_name == "type" and any(k in self.get_current_fname().lower() for k in ("audio", "sfx", "bgm")):
            self.enum_options = ["SFX", "BGM"]
            self.enum_target_row = actual_row_idx
            self.enum_target_col = col_name
            self.enum_selected_idx = 0
            if current_val in self.enum_options:
                self.enum_selected_idx = self.enum_options.index(current_val)
            self.active_modal = "enum_select"

        elif col_name == "vibe" and "bgm" in self.get_current_fname().lower():
            existing_vibes = sorted(list(set(r.get("vibe", "") for r in self.get_current_data()["rows"] if r.get("vibe"))))
            if not existing_vibes:
                existing_vibes = [
                    "calm", "cheerful", "curious", "eerie", "energetic",
                    "futuristic", "industrial", "intense", "mystical",
                    "nostalgic", "suspenseful", "triumphant"
                ]
            self.enum_options = existing_vibes
            self.enum_target_row = actual_row_idx
            self.enum_target_col = col_name
            self.enum_selected_idx = 0
            if current_val in self.enum_options:
                self.enum_selected_idx = self.enum_options.index(current_val)
            self.active_modal = "enum_select"

        else:
            # Open text editor modal
            self.edit_buffer = str(current_val)
            self.edit_row_target = actual_row_idx
            self.edit_col_name = col_name
            self.edit_cursor_pos = len(self.edit_buffer)
            self.active_modal = "text_edit"

    def commit_text_edit(self):
        if self.active_modal == "text_edit":
            data = self.get_current_data()
            old_val = data["rows"][self.edit_row_target].get(self.edit_col_name, "")
            if old_val != self.edit_buffer:
                data["rows"][self.edit_row_target][self.edit_col_name] = self.edit_buffer
                data["is_dirty"] = True
                self.status_banner = f"Updated '{self.edit_col_name}'."
                self.status_color = COLOR_ACCENT
                self.status_timer = 2.5
        self.active_modal = None

    def commit_patterns_select(self):
        if self.active_modal == "patterns_select":
            data = self.get_current_data()
            # Order checked patterns according to available_patterns order
            ordered = [p for p in self.available_patterns if p in self.pattern_checked_set]
            # Add any custom patterns that weren't in available_patterns
            for p in self.pattern_checked_set:
                if p not in ordered:
                    ordered.append(p)

            formatted = ", ".join(ordered)
            old_val = data["rows"][self.edit_row_target].get("patterns", "")
            if old_val != formatted:
                data["rows"][self.edit_row_target]["patterns"] = formatted
                data["is_dirty"] = True
                self.status_banner = f"Updated patterns ({len(ordered)} selected)."
                self.status_color = COLOR_ACCENT
                self.status_timer = 2.5
        self.active_modal = None

    def commit_enum_select(self):
        if self.active_modal == "enum_select":
            data = self.get_current_data()
            if 0 <= self.enum_selected_idx < len(self.enum_options):
                val = self.enum_options[self.enum_selected_idx]
                old_val = data["rows"][self.enum_target_row].get(self.enum_target_col, "")
                if old_val != val:
                    data["rows"][self.enum_target_row][self.enum_target_col] = val
                    data["is_dirty"] = True
                    self.status_banner = f"Set {self.enum_target_col} to '{val}'."
                    self.status_color = COLOR_ACCENT
                    self.status_timer = 2.5
        self.active_modal = None

    def update(self):
        dt = min(get_frame_time(), 0.05)
        if self.status_timer > 0:
            self.status_timer -= dt

        # Global shortcuts when no modal is active and ui_settings dropdown is closed
        if self.active_modal is None and ui_settings.open_dropdown is None:
            # Save: Ctrl + S
            if (is_key_down(KEY_LEFT_CONTROL) or is_key_down(KEY_RIGHT_CONTROL)) and is_key_pressed(KEY_S):
                self.save_active_file()

            # Reload: [R]
            elif is_key_pressed(KEY_R) and not self.is_filtering:
                self.reload_active_file()

            # Switch CSV tab: [Tab]
            elif is_key_pressed(KEY_TAB):
                next_idx = (self.active_file_idx + 1) % len(self.csv_files)
                self.switch_file(next_idx)

            # Insert Row Above: Ctrl + Shift + Enter
            elif (is_key_down(KEY_LEFT_CONTROL) or is_key_down(KEY_RIGHT_CONTROL)) and (
                is_key_down(KEY_LEFT_SHIFT) or is_key_down(KEY_RIGHT_SHIFT)
            ) and is_key_pressed(KEY_ENTER):
                self.insert_row(position="above")

            # Insert Row Below: Ctrl + Enter or [Insert]
            elif ((is_key_down(KEY_LEFT_CONTROL) or is_key_down(KEY_RIGHT_CONTROL)) and is_key_pressed(KEY_ENTER)) or is_key_pressed(KEY_INSERT):
                self.insert_row(position="below")

            # Duplicate Row: Ctrl + D
            elif (is_key_down(KEY_LEFT_CONTROL) or is_key_down(KEY_RIGHT_CONTROL)) and is_key_pressed(KEY_D):
                self.duplicate_selected_row()

            # Delete Row: [Delete]
            elif is_key_pressed(KEY_DELETE) and not self.is_filtering:
                self.delete_selected_row()

            # Open cell editor: [Enter] or [Space]
            elif is_key_pressed(KEY_ENTER) or (is_key_pressed(KEY_SPACE) and not self.is_filtering):
                self.open_cell_editor()

            # Toggle Adjusted Text (Wrap): [W]
            elif is_key_pressed(KEY_W) and not self.is_filtering:
                self.wrap_text = not self.wrap_text
                st = "ON" if self.wrap_text else "OFF"
                self.status_banner = f"Adjusted Text (Wrap): {st}."
                self.status_color = COLOR_ACCENT
                self.status_timer = 2.0

            # Reset Sort Order: [0]
            elif is_key_pressed(KEY_ZERO) and not self.is_filtering:
                data = self.get_current_data()
                data["sort_col"] = None
                data["sort_dir"] = 0
                self.status_banner = "Reset sort order to row index."
                self.status_color = COLOR_ACCENT

            # Search bar focus / toggle: [Ctrl + F]
            elif (is_key_down(KEY_LEFT_CONTROL) or is_key_down(KEY_RIGHT_CONTROL)) and is_key_pressed(KEY_F):
                self.is_filtering = True

            # Table Navigation (Arrows)
            matching = self.get_filtered_rows_indices()
            data = self.get_current_data()
            vis_cols = data["visible_cols"]

            if not self.is_filtering:
                if is_key_pressed(KEY_UP):
                    if self.selected_row_idx > 0:
                        self.selected_row_idx -= 1
                elif is_key_pressed(KEY_DOWN):
                    if self.selected_row_idx < len(matching) - 1:
                        self.selected_row_idx += 1
                elif is_key_pressed(KEY_LEFT):
                    if self.selected_col_idx > 0:
                        self.selected_col_idx -= 1
                elif is_key_pressed(KEY_RIGHT):
                    if self.selected_col_idx < len(vis_cols) - 1:
                        self.selected_col_idx += 1
                elif is_key_pressed(KEY_PAGE_UP):
                    self.selected_row_idx = max(0, self.selected_row_idx - 10)
                elif is_key_pressed(KEY_PAGE_DOWN):
                    self.selected_row_idx = min(max(0, len(matching) - 1), self.selected_row_idx + 10)
                elif is_key_pressed(KEY_HOME):
                    self.selected_row_idx = 0
                elif is_key_pressed(KEY_END):
                    self.selected_row_idx = max(0, len(matching) - 1)

            # Mouse wheel scroll
            wheel = get_mouse_wheel_move()
            if wheel != 0:
                if is_key_down(KEY_LEFT_SHIFT) or is_key_down(KEY_RIGHT_SHIFT):
                    self.scroll_x = max(0, self.scroll_x - int(wheel * 60))
                else:
                    self.scroll_y = max(0, self.scroll_y - int(wheel * 3))

        # Horizontal scrollbar dragging logic
        if self.is_dragging_hscroll:
            if is_mouse_button_down(MOUSE_BUTTON_LEFT):
                data = self.get_current_data()
                vis_cols = data.get("visible_cols", [])
                col_widths = [DEFAULT_COL_WIDTHS.get(c, 160) for c in vis_cols]
                total_grid_w = sum(col_widths)
                table_w = SCREEN_WIDTH - 40
                max_scroll_x = max(0, total_grid_w - table_w)
                if max_scroll_x > 0:
                    thumb_w = max(40, int(table_w * (table_w / total_grid_w)))
                    track_avail = max(1, table_w - thumb_w)
                    delta_mx = get_mouse_x() - self.drag_hscroll_start_mx
                    delta_scroll = int((delta_mx / track_avail) * max_scroll_x)
                    self.scroll_x = max(0, min(max_scroll_x, self.drag_hscroll_start_scroll_x + delta_scroll))
            else:
                self.is_dragging_hscroll = False

        # Handle Modals Input
        self._update_modals()

    def _update_modals(self):
        """Processes keyboard and mouse events inside open modal dialogs."""
        if self.active_modal is None:
            return

        if self.active_modal == "text_edit":
            # Text editing handling
            if is_key_pressed(KEY_ESCAPE):
                self.active_modal = None
                return
            if is_key_pressed(KEY_ENTER):
                self.commit_text_edit()
                return

            # Backspace
            if is_key_pressed(KEY_BACKSPACE) or (is_key_down(KEY_BACKSPACE) and get_time() % 0.08 < 0.04):
                if self.edit_cursor_pos > 0:
                    self.edit_buffer = self.edit_buffer[:self.edit_cursor_pos - 1] + self.edit_buffer[self.edit_cursor_pos:]
                    self.edit_cursor_pos -= 1

            # Delete
            if is_key_pressed(KEY_DELETE):
                if self.edit_cursor_pos < len(self.edit_buffer):
                    self.edit_buffer = self.edit_buffer[:self.edit_cursor_pos] + self.edit_buffer[self.edit_cursor_pos + 1:]

            # Left / Right / Home / End
            if is_key_pressed(KEY_LEFT):
                self.edit_cursor_pos = max(0, self.edit_cursor_pos - 1)
            elif is_key_pressed(KEY_RIGHT):
                self.edit_cursor_pos = min(len(self.edit_buffer), self.edit_cursor_pos + 1)
            elif is_key_pressed(KEY_HOME):
                self.edit_cursor_pos = 0
            elif is_key_pressed(KEY_END):
                self.edit_cursor_pos = len(self.edit_buffer)

            # Paste from clipboard: Ctrl + V
            if (is_key_down(KEY_LEFT_CONTROL) or is_key_down(KEY_RIGHT_CONTROL)) and is_key_pressed(KEY_V):
                clip = get_clipboard_text()
                if clip:
                    # Clean newlines for single-line consistency
                    clip_clean = clip.replace("\r", "").replace("\n", " ")
                    self.edit_buffer = self.edit_buffer[:self.edit_cursor_pos] + clip_clean + self.edit_buffer[self.edit_cursor_pos:]
                    self.edit_cursor_pos += len(clip_clean)

            # Character typing
            ch = get_char_pressed()
            while ch > 0:
                if 32 <= ch <= 126 or ch >= 160:
                    char_str = chr(ch)
                    self.edit_buffer = self.edit_buffer[:self.edit_cursor_pos] + char_str + self.edit_buffer[self.edit_cursor_pos:]
                    self.edit_cursor_pos += 1
                ch = get_char_pressed()

        elif self.active_modal == "patterns_select":
            if is_key_pressed(KEY_ESCAPE):
                self.active_modal = None
                return
            if is_key_pressed(KEY_ENTER):
                self.commit_patterns_select()
                return

            # Pattern search filter typing
            if is_key_pressed(KEY_BACKSPACE):
                if len(self.pattern_filter) > 0:
                    self.pattern_filter = self.pattern_filter[:-1]

            ch = get_char_pressed()
            while ch > 0:
                if 32 <= ch <= 126:
                    self.pattern_filter += chr(ch)
                ch = get_char_pressed()

            # Mouse wheel in patterns list
            wheel = get_mouse_wheel_move()
            if wheel != 0:
                self.pattern_scroll_y = max(0, self.pattern_scroll_y - int(wheel * 32))

        elif self.active_modal == "enum_select":
            if is_key_pressed(KEY_ESCAPE):
                self.active_modal = None
                return
            if is_key_pressed(KEY_ENTER):
                self.commit_enum_select()
                return
            if is_key_pressed(KEY_UP):
                self.enum_selected_idx = max(0, self.enum_selected_idx - 1)
            elif is_key_pressed(KEY_DOWN):
                self.enum_selected_idx = min(len(self.enum_options) - 1, self.enum_selected_idx + 1)

        elif self.active_modal == "confirm_delete":
            if is_key_pressed(KEY_ESCAPE):
                self.active_modal = None
            elif is_key_pressed(KEY_ENTER):
                if self.confirm_callback:
                    self.confirm_callback()
                self.active_modal = None

        elif self.active_modal == "confirm_switch":
            if is_key_pressed(KEY_ESCAPE):
                self.active_modal = None
                self.pending_switch_idx = -1

    def draw(self):
        begin_drawing()
        clear_background(COLOR_BG)

        # 1. Header & Global UI Settings Bar
        self._draw_header()

        # 2. File Selector Tabs
        self._draw_tabs_bar()

        # 3. Action Toolbar (Buttons, Search, Stats)
        self._draw_toolbar()

        # 4. Main Data Grid Table
        self._draw_table()

        # 5. Bottom Technical Inspector & Status Bar
        self._draw_status_bar()

        # 6. Modal Overlays (if active)
        if self.active_modal is not None:
            self._draw_active_modal()

        # 7. Global Top-Bar Settings Dropdown (Font, Size, Window)
        # Keeps region x=450..980 clear and draws dropdown on top
        draw_ui_settings_bar(450, 14)

        end_drawing()

    def _draw_header(self):
        """Renders the top application title bar."""
        draw_rectangle(0, 0, SCREEN_WIDTH, 52, COLOR_PANEL)
        draw_line(0, 52, SCREEN_WIDTH, 52, COLOR_PANEL_BORDER)

        draw_text("TASKS CATALOG & SPREADSHEET EDITOR", 24, 16, 18, COLOR_ACCENT)
        draw_text("Raylib Python", 380, 19, 13, COLOR_TEXT_MUTED)

        # Save and Reload buttons on the top right
        btn_w, btn_h = 130, 30
        save_x = SCREEN_WIDTH - 290
        reload_x = SCREEN_WIDTH - 150
        by = 11

        mx, my = get_mouse_x(), get_mouse_y()
        clicked = is_mouse_button_pressed(MOUSE_BUTTON_LEFT)

        # Save Button
        save_hover = (save_x <= mx <= save_x + btn_w) and (by <= my <= by + btn_h)
        data = self.get_current_data()
        save_col = COLOR_ACCENT_GREEN if data.get("is_dirty", False) else COLOR_PANEL_BORDER
        draw_rectangle(save_x, by, btn_w, btn_h, Color(24, 48, 36, 255) if save_hover else Color(18, 36, 26, 255))
        draw_rectangle_lines(save_x, by, btn_w, btn_h, save_col)
        draw_text("Save (Ctrl+S)", save_x + 14, by + 7, 13, COLOR_TEXT_MAIN)
        if save_hover and clicked and self.active_modal is None and ui_settings.open_dropdown is None:
            self.save_active_file()

        # Reload Button
        reload_hover = (reload_x <= mx <= reload_x + btn_w) and (by <= my <= by + btn_h)
        draw_rectangle(reload_x, by, btn_w, btn_h, Color(32, 42, 64, 255) if reload_hover else Color(22, 30, 48, 255))
        draw_rectangle_lines(reload_x, by, btn_w, btn_h, COLOR_PANEL_BORDER)
        draw_text("Reload (R)", reload_x + 28, by + 7, 13, COLOR_TEXT_MAIN)
        if reload_hover and clicked and self.active_modal is None and ui_settings.open_dropdown is None:
            self.reload_active_file()

    def _draw_tabs_bar(self):
        """Renders file tabs for switching between CSVs in tasks/."""
        bar_y = 54
        bar_h = 36
        draw_rectangle(0, bar_y, SCREEN_WIDTH, bar_h, COLOR_PANEL_ALT)
        draw_line(0, bar_y + bar_h, SCREEN_WIDTH, bar_y + bar_h, COLOR_PANEL_BORDER)

        mx, my = get_mouse_x(), get_mouse_y()
        clicked = is_mouse_button_pressed(MOUSE_BUTTON_LEFT)

        cur_x = 20
        for i, fname in enumerate(self.csv_files):
            is_active = (i == self.active_file_idx)
            is_dirty = self.file_data.get(fname, {}).get("is_dirty", False)

            # Icon badge based on name
            icon = "🎮 " if "minigames" in fname else ("🔊 " if "sfx" in fname.lower() else ("🎵 " if ("bgm" in fname.lower() or "audio" in fname.lower()) else ("🧊 " if "models" in fname else "🎨 ")))
            label = f"{icon}{fname}" + (" *" if is_dirty else "")

            tab_w = max(130, len(label) * 8 + 36)
            tab_rect = (cur_x, bar_y + 4, tab_w, bar_h - 4)

            tab_hover = (cur_x <= mx <= cur_x + tab_w) and (bar_y + 4 <= my <= bar_y + bar_h)

            if is_active:
                draw_rectangle(cur_x, bar_y + 4, tab_w, bar_h - 4, COLOR_PANEL)
                draw_line(cur_x, bar_y + 4, cur_x + tab_w, bar_y + 4, COLOR_ACCENT)
                draw_line(cur_x, bar_y + 4, cur_x, bar_y + bar_h, COLOR_PANEL_BORDER)
                draw_line(cur_x + tab_w, bar_y + 4, cur_x + tab_w, bar_y + bar_h, COLOR_PANEL_BORDER)
                text_col = COLOR_ACCENT if not is_dirty else COLOR_ACCENT_GOLD
            else:
                if tab_hover:
                    draw_rectangle(cur_x, bar_y + 6, tab_w, bar_h - 6, COLOR_HOVER_ROW)
                text_col = COLOR_TEXT_DIM

            draw_text(label, cur_x + 12, bar_y + 11, 13, text_col)

            if tab_hover and clicked and self.active_modal is None and ui_settings.open_dropdown is None:
                self.switch_file(i)

            cur_x += tab_w + 8

    def _draw_toolbar(self):
        """Renders toolbar with row manipulation buttons and live stats."""
        tool_y = 92
        tool_h = 42
        draw_rectangle(0, tool_y, SCREEN_WIDTH, tool_h, COLOR_BG)
        draw_line(0, tool_y + tool_h, SCREEN_WIDTH, tool_y + tool_h, COLOR_PANEL_BORDER)

        mx, my = get_mouse_x(), get_mouse_y()
        clicked = is_mouse_button_pressed(MOUSE_BUTTON_LEFT)

        def toggle_wrap():
            self.wrap_text = not self.wrap_text
            st = "ON" if self.wrap_text else "OFF"
            self.status_banner = f"Adjusted Text (Wrap): {st}."
            self.status_color = COLOR_ACCENT
            self.status_timer = 2.0

        # Quick action buttons
        buttons = [
            ("+ Insert Above", 112, lambda: self.insert_row("above"), COLOR_TEXT_MAIN, False),
            ("+ Insert Below", 112, lambda: self.insert_row("below"), COLOR_TEXT_MAIN, False),
            ("Duplicate", 86, self.duplicate_selected_row, COLOR_TEXT_MAIN, False),
            ("Delete", 76, self.delete_selected_row, COLOR_ACCENT_RED, False),
            ("Reset Sort", 86, lambda: self.sort_by_column(""), COLOR_TEXT_DIM, False),
            ("Wrap Text: " + ("ON" if self.wrap_text else "OFF"), 114, toggle_wrap, COLOR_ACCENT if self.wrap_text else COLOR_TEXT_MAIN, self.wrap_text),
        ]

        bx = 20
        by = tool_y + 7
        bh = 28
        for item in buttons:
            lbl, bw, action, txt_col, is_active = item
            b_hover = (bx <= mx <= bx + bw) and (by <= my <= by + bh)
            btn_bg = COLOR_SELECTED_ROW if is_active else (Color(28, 38, 58, 255) if b_hover else Color(18, 26, 42, 255))
            btn_border = COLOR_ACCENT if is_active else COLOR_PANEL_BORDER
            draw_rectangle(bx, by, bw, bh, btn_bg)
            draw_rectangle_lines(bx, by, bw, bh, btn_border)
            draw_text(lbl, bx + 10, by + 6, 12, txt_col)

            if b_hover and clicked and self.active_modal is None and ui_settings.open_dropdown is None:
                action()

            bx += bw + 8

        # Search / Filter Box
        fx = bx + 12
        fw = 160
        fh = 28
        f_hover = (fx <= mx <= fx + fw) and (by <= my <= by + fh)
        draw_rectangle(fx, by, fw, fh, Color(14, 20, 32, 255))
        draw_rectangle_lines(fx, by, fw, fh, COLOR_ACCENT if self.is_filtering else COLOR_PANEL_BORDER)

        filter_display = self.filter_text if self.filter_text else "Search (Ctrl+F)..."
        filter_col = COLOR_TEXT_MAIN if self.filter_text else COLOR_TEXT_MUTED
        draw_text(filter_display, fx + 8, by + 7, 12, filter_col)

        if f_hover and clicked and self.active_modal is None:
            self.is_filtering = True

        # Clear search button if active
        if self.filter_text:
            cx = fx + fw - 22
            c_hover = (cx <= mx <= cx + 18) and (by + 4 <= my <= by + 24)
            draw_text("x", cx + 4, by + 5, 13, COLOR_ACCENT if c_hover else COLOR_TEXT_MUTED)
            if c_hover and clicked:
                self.filter_text = ""
                self.is_filtering = False

        # Live Row Counts on the right
        data = self.get_current_data()
        rows = data.get("rows", [])
        total = len(rows)
        done = sum(1 for r in rows if r.get("status") in ("done", "built"))
        pending = sum(1 for r in rows if r.get("status") not in ("done", "built"))

        stats_str = f"Total: {total} | Done: {done} | Pending: {pending}"
        draw_text(stats_str, SCREEN_WIDTH - 420, by + 7, 12, COLOR_TEXT_MUTED)

    def _draw_table(self):
        """Renders the scrollable data grid table with hidden columns filtered out."""
        table_x = 20
        hscroll_y = 136
        hscroll_h = 10
        table_y = 148
        table_w = SCREEN_WIDTH - 40
        table_h = SCREEN_HEIGHT - table_y - 42

        data = self.get_current_data()
        visible_cols = data.get("visible_cols", [])
        rows = data.get("rows", [])
        matching_indices = self.get_filtered_rows_indices()

        if not visible_cols:
            draw_text("No visible columns found in this catalog.", table_x + 20, table_y + 30, 14, COLOR_TEXT_MUTED)
            return

        # Calculate column widths
        col_widths = []
        for c in visible_cols:
            w = DEFAULT_COL_WIDTHS.get(c, 160)
            col_widths.append(w)

        total_grid_w = sum(col_widths)
        row_h = max(54, 58 + ui_settings.font_size_offset) if self.wrap_text else max(24, 28 + ui_settings.font_size_offset)
        header_h = 32

        mx, my = get_mouse_x(), get_mouse_y()
        clicked = is_mouse_button_pressed(MOUSE_BUTTON_LEFT)

        max_scroll_x = max(0, total_grid_w - table_w)

        # 0. Horizontal Scrollbar (placed directly on top of the column headers)
        draw_rectangle(table_x, hscroll_y, table_w, hscroll_h, Color(14, 18, 30, 255))
        draw_rectangle_lines(table_x, hscroll_y, table_w, hscroll_h, COLOR_PANEL_BORDER)

        if max_scroll_x > 0:
            thumb_w = max(40, int(table_w * (table_w / total_grid_w)))
            track_avail = max(1, table_w - thumb_w)
            thumb_x = table_x + int(track_avail * (self.scroll_x / max_scroll_x))
            thumb_hover = (thumb_x <= mx <= thumb_x + thumb_w) and (hscroll_y <= my <= hscroll_y + hscroll_h)
            track_hover = (table_x <= mx <= table_x + table_w) and (hscroll_y <= my <= hscroll_y + hscroll_h)

            if clicked and self.active_modal is None and ui_settings.open_dropdown is None:
                if thumb_hover:
                    self.is_dragging_hscroll = True
                    self.drag_hscroll_start_mx = mx
                    self.drag_hscroll_start_scroll_x = self.scroll_x
                elif track_hover:
                    click_ratio = max(0.0, min(1.0, (mx - table_x - thumb_w / 2) / track_avail))
                    self.scroll_x = int(click_ratio * max_scroll_x)
                    self.is_dragging_hscroll = True
                    self.drag_hscroll_start_mx = mx
                    self.drag_hscroll_start_scroll_x = self.scroll_x

            thumb_col = COLOR_ACCENT if (self.is_dragging_hscroll or thumb_hover) else Color(60, 95, 145, 255)
            draw_rectangle(thumb_x, hscroll_y + 1, thumb_w, hscroll_h - 2, thumb_col)

        # 1. Header Row
        draw_rectangle(table_x, table_y, table_w, header_h, COLOR_HEADER_BG)
        draw_line(table_x, table_y + header_h, table_x + table_w, table_y + header_h, COLOR_PANEL_BORDER)

        begin_scissor_mode(table_x, table_y, table_w, header_h)
        cur_cx = table_x - self.scroll_x
        for ci, col_name in enumerate(visible_cols):
            cw = col_widths[ci]
            h_hover = (cur_cx <= mx <= cur_cx + cw) and (table_y <= my <= table_y + header_h)

            if h_hover:
                draw_rectangle(cur_cx, table_y, cw, header_h, COLOR_HOVER_ROW)

            # Sort indicator
            sort_ind = ""
            if data.get("sort_col") == col_name:
                sort_ind = " ▲" if data.get("sort_dir") == 1 else " ▼"

            col_label = f"{col_name.upper()}{sort_ind}"
            draw_text(col_label, cur_cx + 8, table_y + 8, 12, COLOR_ACCENT if sort_ind else COLOR_TEXT_MAIN)
            draw_line(cur_cx + cw - 1, table_y, cur_cx + cw - 1, table_y + header_h, COLOR_PANEL_BORDER)

            if h_hover and clicked and self.active_modal is None and ui_settings.open_dropdown is None:
                self.sort_by_column(col_name)

            cur_cx += cw
        end_scissor_mode()

        # 2. Table Data Rows
        body_y = table_y + header_h
        body_h = table_h - header_h

        visible_row_count = body_h // row_h
        max_scroll_y = max(0, len(matching_indices) - visible_row_count)
        self.scroll_y = max(0, min(max_scroll_y, self.scroll_y))

        # Clamp scroll_x
        self.scroll_x = max(0, min(max_scroll_x, self.scroll_x))

        begin_scissor_mode(table_x, body_y, table_w, body_h)

        start_row = self.scroll_y
        end_row = min(len(matching_indices), start_row + visible_row_count + 2)

        for ri in range(start_row, end_row):
            actual_row_idx = matching_indices[ri]
            row_data = rows[actual_row_idx]
            ry = body_y + (ri - start_row) * row_h

            is_selected_row = (ri == self.selected_row_idx)
            row_hover = (table_x <= mx <= table_x + table_w) and (ry <= my < ry + row_h)

            # Zebra Background
            if is_selected_row:
                bg_col = COLOR_SELECTED_ROW
            elif row_hover:
                bg_col = COLOR_HOVER_ROW
            else:
                bg_col = COLOR_PANEL if (ri % 2 == 0) else COLOR_PANEL_ALT

            draw_rectangle(table_x, ry, table_w, row_h, bg_col)
            draw_line(table_x, ry + row_h - 1, table_x + table_w, ry + row_h - 1, Color(24, 32, 52, 255))

            # Draw cells
            cur_cx = table_x - self.scroll_x
            for ci, col_name in enumerate(visible_cols):
                cw = col_widths[ci]
                cell_hover = row_hover and (cur_cx <= mx < cur_cx + cw)
                is_selected_cell = is_selected_row and (ci == self.selected_col_idx)

                # Selected cell outline
                if is_selected_cell:
                    draw_rectangle_lines(cur_cx, ry, cw, row_h, COLOR_SELECTED_CELL_BORDER)

                cell_val = str(row_data.get(col_name, ""))

                # Status Badge rendering
                if col_name == "status":
                    badge_h = 20 if self.wrap_text else (row_h - 8)
                    badge_y = ry + (row_h - badge_h) // 2 if self.wrap_text else (ry + 4)
                    self._draw_status_badge(cell_val, cur_cx + 8, badge_y, cw - 16, badge_h)
                else:
                    txt_col = COLOR_TEXT_MAIN if not is_selected_cell else Color(255, 255, 255, 255)
                    if self.wrap_text:
                        chars_per_line = max(6, int((cw - 16) / 7.6))
                        lines = wrap_cell_text(cell_val, chars_per_line, max_lines=3)
                        line_gap = 16 + ui_settings.font_size_offset // 2
                        if not lines:
                            lines = [""]
                        for li, l_txt in enumerate(lines):
                            draw_text(l_txt, cur_cx + 8, ry + 6 + li * line_gap, 12, txt_col)
                    else:
                        max_chars = max(4, int(cw / 7.8))
                        display_val = cell_val if len(cell_val) <= max_chars else (cell_val[:max_chars - 3] + "...")
                        draw_text(display_val, cur_cx + 8, ry + 5, 12, txt_col)

                draw_line(cur_cx + cw - 1, ry, cur_cx + cw - 1, ry + row_h, Color(32, 42, 68, 255))

                # Handle cell clicking
                if cell_hover and clicked and self.active_modal is None and ui_settings.open_dropdown is None:
                    self.selected_row_idx = ri
                    self.selected_col_idx = ci
                    now = get_time()
                    if (ri, ci) == self.last_clicked_cell and (now - self.last_click_time) < 0.35:
                        self.open_cell_editor()
                    self.last_click_time = now
                    self.last_clicked_cell = (ri, ci)

                cur_cx += cw

        end_scissor_mode()

        # 3. Scrollbar indicators
        if max_scroll_y > 0:
            sb_h = max(20, int(body_h * (visible_row_count / len(matching_indices))))
            sb_y = body_y + int((body_h - sb_h) * (self.scroll_y / max_scroll_y))
            draw_rectangle(SCREEN_WIDTH - 24, sb_y, 4, sb_h, COLOR_ACCENT)

    def _draw_status_badge(self, status: str, x: int, y: int, w: int, h: int):
        """Draws colored status pill badge."""
        st = status.lower().strip()
        if st in ("done", "built"):
            col = COLOR_BADGE_DONE
            label = "Done"
        else:
            col = COLOR_BADGE_PENDING
            label = "Pending"

        draw_rectangle(x, y, w, h, col)
        draw_text(label, x + (w - len(label) * 7) // 2, y + 2, 11, COLOR_TEXT_MAIN)

    def _draw_status_bar(self):
        """Renders bottom status bar with hidden metadata inspection and keybindings."""
        bar_y = SCREEN_HEIGHT - 36
        bar_h = 36
        draw_rectangle(0, bar_y, SCREEN_WIDTH, bar_h, COLOR_PANEL)
        draw_line(0, bar_y, SCREEN_WIDTH, bar_y, COLOR_PANEL_BORDER)

        data = self.get_current_data()
        rows = data.get("rows", [])
        matching = self.get_filtered_rows_indices()

        # Technical preview of selected row's hidden ID and target_file
        meta_str = ""
        if matching and 0 <= self.selected_row_idx < len(matching):
            actual_idx = matching[self.selected_row_idx]
            cur_row = rows[actual_idx]
            meta_str = f"[ID: {cur_row.get('id', 'N/A')}]  [Target: {cur_row.get('target_file', 'N/A')}]"

        draw_text(meta_str, 20, bar_y + 10, 12, COLOR_ACCENT)

        # Status notification message
        if self.status_banner:
            draw_text(self.status_banner, 540, bar_y + 10, 12, self.status_color)

        # Keybindings hints on the right
        hints = "[Enter] Edit  [W] Wrap  [Ctrl+S] Save  [Ins] Add  [Del] Delete  [F11] Full"
        draw_text(hints, SCREEN_WIDTH - 420, bar_y + 10, 11, COLOR_TEXT_MUTED)

    def _draw_active_modal(self):
        """Renders modal dialog overlay based on active_modal type."""
        # Backdrop
        draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, Color(0, 0, 0, 190))

        if self.active_modal == "text_edit":
            self._draw_text_edit_modal()
        elif self.active_modal == "patterns_select":
            self._draw_patterns_select_modal()
        elif self.active_modal == "enum_select":
            self._draw_enum_select_modal()
        elif self.active_modal in ("confirm_delete", "confirm_switch"):
            self._draw_confirm_modal()

    def _draw_text_edit_modal(self):
        """Modal for editing freeform text fields."""
        mw, mh = 640, 260
        mx, my = (SCREEN_WIDTH - mw) // 2, (SCREEN_HEIGHT - mh) // 2

        draw_rectangle(mx, my, mw, mh, COLOR_PANEL)
        draw_rectangle_lines(mx, my, mw, mh, COLOR_ACCENT)

        draw_text(f"Edit Field: {self.edit_col_name.upper()}", mx + 24, my + 20, 16, COLOR_ACCENT)
        draw_text("Press [Enter] to apply changes, [Esc] to cancel.", mx + 24, my + 44, 12, COLOR_TEXT_MUTED)

        # Input box
        bx, by, bw, bh = mx + 24, my + 76, mw - 48, 80
        draw_rectangle(bx, by, bw, bh, Color(12, 16, 26, 255))
        draw_rectangle_lines(bx, by, bw, bh, COLOR_PANEL_BORDER)

        # Text with cursor
        wrapped = self.edit_buffer
        draw_text(wrapped, bx + 12, by + 12, 14, COLOR_TEXT_MAIN)

        # Blinking cursor
        if int(get_time() * 2) % 2 == 0:
            cursor_x = bx + 12 + len(self.edit_buffer[:self.edit_cursor_pos]) * 8
            draw_line(cursor_x, by + 10, cursor_x, by + 28, COLOR_ACCENT)

        # Buttons
        self._draw_modal_buttons(mx, my + mh - 54, mw, self.commit_text_edit, lambda: setattr(self, "active_modal", None))

    def _draw_patterns_select_modal(self):
        """Modal with search filter and multi-select checklist from patterns.md."""
        mw, mh = 680, 520
        mx, my = (SCREEN_WIDTH - mw) // 2, (SCREEN_HEIGHT - mh) // 2

        draw_rectangle(mx, my, mw, mh, COLOR_PANEL)
        draw_rectangle_lines(mx, my, mw, mh, COLOR_ACCENT)

        draw_text("SELECT PATTERNS (rules/patterns.md)", mx + 24, my + 18, 16, COLOR_ACCENT)
        draw_text("Check applicable design patterns. Real-time search from rules/patterns.md.", mx + 24, my + 40, 12, COLOR_TEXT_MUTED)

        # Filter box
        fx, fy, fw, fh = mx + 24, my + 64, mw - 48, 30
        draw_rectangle(fx, fy, fw, fh, Color(12, 16, 26, 255))
        draw_rectangle_lines(fx, fy, fw, fh, COLOR_PANEL_BORDER)
        f_display = self.pattern_filter if self.pattern_filter else "Filter patterns..."
        f_col = COLOR_TEXT_MAIN if self.pattern_filter else COLOR_TEXT_MUTED
        draw_text(f_display, fx + 10, fy + 8, 13, f_col)

        # Filtered patterns list
        q = self.pattern_filter.lower().strip()
        filtered = [p for p in self.available_patterns if q in p.lower()]

        # Scrollable area
        list_y = fy + fh + 12
        list_h = mh - 180
        item_h = 28

        begin_scissor_mode(fx, list_y, fw, list_h)

        max_scroll = max(0, len(filtered) * item_h - list_h)
        self.pattern_scroll_y = max(0, min(max_scroll, self.pattern_scroll_y))

        mouse_x, mouse_y = get_mouse_x(), get_mouse_y()
        clicked = is_mouse_button_pressed(MOUSE_BUTTON_LEFT)

        for i, pat in enumerate(filtered):
            iy = list_y + i * item_h - self.pattern_scroll_y
            if iy + item_h < list_y or iy > list_y + list_h:
                continue

            is_checked = pat in self.pattern_checked_set
            item_hover = (fx <= mouse_x <= fx + fw) and (iy <= mouse_y < iy + item_h)

            if item_hover:
                draw_rectangle(fx, iy, fw, item_h, COLOR_HOVER_ROW)

            # Checkbox icon
            box_x, box_y, box_s = fx + 8, iy + 6, 16
            draw_rectangle(box_x, box_y, box_s, box_s, Color(16, 24, 40, 255))
            draw_rectangle_lines(box_x, box_y, box_s, box_s, COLOR_ACCENT if is_checked else COLOR_PANEL_BORDER)
            if is_checked:
                draw_text("X", box_x + 4, box_y + 1, 12, COLOR_ACCENT_GOLD)

            txt_col = COLOR_TEXT_MAIN if is_checked else (COLOR_TEXT_DIM if not item_hover else COLOR_TEXT_MAIN)
            draw_text(pat, box_x + box_s + 12, iy + 6, 13, txt_col)

            if item_hover and clicked:
                if is_checked:
                    self.pattern_checked_set.remove(pat)
                else:
                    self.pattern_checked_set.add(pat)

        end_scissor_mode()

        # Quick bulk buttons
        bx, by = mx + 24, my + mh - 98
        draw_text(f"Selected: {len(self.pattern_checked_set)} pattern(s)", bx, by + 4, 12, COLOR_ACCENT)

        # Clear All button
        btn_clear = (bx + 200, by, 90, 24)
        if (btn_clear[0] <= mouse_x <= btn_clear[0] + btn_clear[2]) and (btn_clear[1] <= mouse_y <= btn_clear[1] + btn_clear[3]):
            draw_rectangle(*btn_clear, COLOR_HOVER_ROW)
            if clicked:
                self.pattern_checked_set.clear()
        draw_rectangle_lines(*btn_clear, COLOR_PANEL_BORDER)
        draw_text("Clear All", btn_clear[0] + 16, btn_clear[1] + 5, 11, COLOR_TEXT_DIM)

        # Select All Filtered button
        btn_all = (bx + 300, by, 120, 24)
        if (btn_all[0] <= mouse_x <= btn_all[0] + btn_all[2]) and (btn_all[1] <= mouse_y <= btn_all[1] + btn_all[3]):
            draw_rectangle(*btn_all, COLOR_HOVER_ROW)
            if clicked:
                for p in filtered:
                    self.pattern_checked_set.add(p)
        draw_rectangle_lines(*btn_all, COLOR_PANEL_BORDER)
        draw_text("Select Filtered", btn_all[0] + 14, btn_all[1] + 5, 11, COLOR_TEXT_DIM)

        # Footer Buttons (Apply / Cancel)
        self._draw_modal_buttons(mx, my + mh - 54, mw, self.commit_patterns_select, lambda: setattr(self, "active_modal", None))

    def _draw_enum_select_modal(self):
        """Modal for selecting single option from enum dropdown."""
        mw, mh = 420, 240
        mx, my = (SCREEN_WIDTH - mw) // 2, (SCREEN_HEIGHT - mh) // 2

        draw_rectangle(mx, my, mw, mh, COLOR_PANEL)
        draw_rectangle_lines(mx, my, mw, mh, COLOR_ACCENT)

        draw_text(f"Select: {self.enum_target_col.upper()}", mx + 24, my + 20, 16, COLOR_ACCENT)

        item_h = 32
        mouse_x, mouse_y = get_mouse_x(), get_mouse_y()
        clicked = is_mouse_button_pressed(MOUSE_BUTTON_LEFT)

        for i, opt in enumerate(self.enum_options):
            iy = my + 64 + i * (item_h + 6)
            is_cur = (i == self.enum_selected_idx)
            hover = (mx + 24 <= mouse_x <= mx + mw - 24) and (iy <= mouse_y < iy + item_h)

            bg = COLOR_SELECTED_ROW if is_cur else (COLOR_HOVER_ROW if hover else Color(14, 20, 32, 255))
            draw_rectangle(mx + 24, iy, mw - 48, item_h, bg)
            draw_rectangle_lines(mx + 24, iy, mw - 48, item_h, COLOR_ACCENT if is_cur else COLOR_PANEL_BORDER)
            draw_text(opt, mx + 40, iy + 8, 14, COLOR_ACCENT_GOLD if is_cur else COLOR_TEXT_MAIN)

            if hover and clicked:
                self.enum_selected_idx = i
                self.commit_enum_select()

        self._draw_modal_buttons(mx, my + mh - 50, mw, self.commit_enum_select, lambda: setattr(self, "active_modal", None))

    def _draw_confirm_modal(self):
        """Modal for confirm delete or confirm discard switch."""
        mw, mh = 480, 200
        mx, my = (SCREEN_WIDTH - mw) // 2, (SCREEN_HEIGHT - mh) // 2

        draw_rectangle(mx, my, mw, mh, COLOR_PANEL)
        draw_rectangle_lines(mx, my, mw, mh, COLOR_ACCENT_RED if self.active_modal == "confirm_delete" else COLOR_ACCENT_GOLD)

        title = self.confirm_title if self.active_modal == "confirm_delete" else "Unsaved Changes"
        draw_text(title, mx + 24, my + 20, 16, COLOR_ACCENT_RED if self.active_modal == "confirm_delete" else COLOR_ACCENT_GOLD)

        if self.active_modal == "confirm_switch":
            msg = "You have unsaved changes in the current catalog.\nSave before switching, or discard changes?"
            draw_text(msg, mx + 24, my + 56, 13, COLOR_TEXT_MAIN)

            # 3 buttons: Save & Switch, Discard & Switch, Cancel
            mouse_x, mouse_y = get_mouse_x(), get_mouse_y()
            clicked = is_mouse_button_pressed(MOUSE_BUTTON_LEFT)

            # Save & Switch
            b1 = (mx + 24, my + mh - 50, 130, 32)
            if (b1[0] <= mouse_x <= b1[0] + b1[2]) and (b1[1] <= mouse_y <= b1[1] + b1[3]):
                draw_rectangle(*b1, Color(24, 48, 36, 255))
                if clicked:
                    self.save_active_file()
                    self.active_modal = None
                    self._do_switch_file(self.pending_switch_idx)
            draw_rectangle_lines(*b1, COLOR_ACCENT_GREEN)
            draw_text("Save & Switch", b1[0] + 16, b1[1] + 8, 12, COLOR_TEXT_MAIN)

            # Discard & Switch
            b2 = (mx + 164, my + mh - 50, 140, 32)
            if (b2[0] <= mouse_x <= b2[0] + b2[2]) and (b2[1] <= mouse_y <= b2[1] + b2[3]):
                draw_rectangle(*b2, Color(48, 24, 24, 255))
                if clicked:
                    self.reload_active_file()
                    self.active_modal = None
                    self._do_switch_file(self.pending_switch_idx)
            draw_rectangle_lines(*b2, COLOR_ACCENT_RED)
            draw_text("Discard & Switch", b2[0] + 14, b2[1] + 8, 12, COLOR_TEXT_MAIN)

            # Cancel
            b3 = (mx + 314, my + mh - 50, 100, 32)
            if (b3[0] <= mouse_x <= b3[0] + b3[2]) and (b3[1] <= mouse_y <= b3[1] + b3[3]):
                draw_rectangle(*b3, COLOR_HOVER_ROW)
                if clicked:
                    self.active_modal = None
                    self.pending_switch_idx = -1
            draw_rectangle_lines(*b3, COLOR_PANEL_BORDER)
            draw_text("Cancel", b3[0] + 28, b3[1] + 8, 12, COLOR_TEXT_DIM)

        else:
            draw_text(self.confirm_message, mx + 24, my + 56, 13, COLOR_TEXT_MAIN)
            self._draw_modal_buttons(mx, my + mh - 50, mw, self.confirm_callback, lambda: setattr(self, "active_modal", None), ok_label="Delete", ok_col=COLOR_ACCENT_RED)

    def _draw_modal_buttons(self, modal_x: int, btn_y: int, modal_w: int, on_ok, on_cancel, ok_label: str = "Apply", ok_col: Color = COLOR_ACCENT_GREEN):
        """Helper to render Apply/Cancel buttons in modal dialogs."""
        btn_w, btn_h = 100, 32
        ok_x = modal_x + modal_w - 230
        cancel_x = modal_x + modal_w - 120

        mouse_x, mouse_y = get_mouse_x(), get_mouse_y()
        clicked = is_mouse_button_pressed(MOUSE_BUTTON_LEFT)

        # OK / Apply Button
        ok_hover = (ok_x <= mouse_x <= ok_x + btn_w) and (btn_y <= mouse_y <= btn_y + btn_h)
        draw_rectangle(ok_x, btn_y, btn_w, btn_h, Color(24, 48, 36, 255) if ok_hover else Color(18, 36, 26, 255))
        draw_rectangle_lines(ok_x, btn_y, btn_w, btn_h, ok_col)
        draw_text(ok_label, ok_x + (btn_w - len(ok_label) * 8) // 2, btn_y + 8, 13, COLOR_TEXT_MAIN)
        if ok_hover and clicked:
            if on_ok:
                on_ok()

        # Cancel Button
        can_hover = (cancel_x <= mouse_x <= cancel_x + btn_w) and (btn_y <= mouse_y <= btn_y + btn_h)
        draw_rectangle(cancel_x, btn_y, btn_w, btn_h, Color(32, 42, 64, 255) if can_hover else Color(22, 30, 48, 255))
        draw_rectangle_lines(cancel_x, btn_y, btn_w, btn_h, COLOR_PANEL_BORDER)
        draw_text("Cancel", cancel_x + 24, btn_y + 8, 13, COLOR_TEXT_DIM)
        if can_hover and clicked:
            if on_cancel:
                on_cancel()

    def run(self, smoke_test: bool = False):
        frame_count = 0
        while not window_should_close():
            self.update()
            self.draw()
            frame_count += 1
            if smoke_test and frame_count >= 3:
                break
        close_window()


if __name__ == "__main__":
    if handle_headless_cli(ROOT_DIR, sys.argv):
        sys.exit(0)
    is_smoke = "--smoke-test" in sys.argv
    TasksEditor().run(smoke_test=is_smoke)

