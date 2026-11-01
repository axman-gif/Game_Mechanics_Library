# -*- coding: utf-8 -*-
"""
Global UI Settings, Font Manager, and Window Resolution Controller
------------------------------------------------------------------
Persists user preferences in the root `config.json` file and provides:
  1. Interactive Top-Bar Dropdown Menus for:
     - Font Type (Raylib Default Pixel + cross-platform system TTF fonts)
     - Font Size Offset (also adjustable live via Ctrl + '+' and Ctrl + '-')
     - Window Size & Fullscreen (1024x576, 1280x720, 1600x900, 1920x1080, Fullscreen [F11])
  2. Transparent Raylib wrappers (`init_window`, `begin_drawing`, `end_drawing`,
     `begin_mode_2d`, `end_mode_2d`, `begin_mode_3d`, `end_mode_3d`, `draw_text`,
     `close_window`) so `launcher.py` and every minigame in `minigames/` automatically
     share the same top-bar settings menu, font rendering, shortcuts, and scaling.
"""

import sys
import os
import json
from typing import Dict, List, Tuple, Optional

sys.dont_write_bytecode = True

import pyray as _pr
from pyray import (
    Vector2,
    Color,
    Camera2D,
    WHITE,
    GRAY,
    LIGHTGRAY,
    GOLD,
)

# Portable repository root and config.json path (works on Windows, Linux, macOS)
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_PATH = os.path.join(REPO_ROOT, "config.json")

# Known cross-platform system fonts (display name -> candidate filenames)
SYSTEM_FONT_CANDIDATES: List[Tuple[str, List[str]]] = [
    ("Consolas", ["consola.ttf", "Consolas.ttf"]),
    ("Segoe UI", ["segoeui.ttf", "SegoeUI.ttf"]),
    ("Courier New", ["cour.ttf", "Courier New.ttf", "courbd.ttf"]),
    ("Arial", ["arial.ttf", "Arial.ttf"]),
    ("Verdana", ["verdana.ttf", "Verdana.ttf"]),
    ("Tahoma", ["tahoma.ttf", "Tahoma.ttf"]),
    ("Trebuchet MS", ["trebuc.ttf", "Trebuchet MS.ttf"]),
    ("Lucida Console", ["lucon.ttf", "LucidaConsole.ttf"]),
    ("DejaVu Mono", ["DejaVuSansMono.ttf"]),
    ("Liberation Mono", ["LiberationMono-Regular.ttf"]),
    ("Ubuntu Mono", ["UbuntuMono-R.ttf"]),
    ("Menlo", ["Menlo.ttc", "Monaco.ttf"]),
]

FONT_SIZE_OPTIONS: List[Tuple[str, int]] = [
    ("Small (-4)", -4),
    ("Compact (-2)", -2),
    ("Normal (+0)", 0),
    ("Medium (+2)", 2),
    ("Large (+4)", 4),
    ("X-Large (+6)", 6),
    ("Huge (+8)", 8),
]

WINDOW_SIZE_OPTIONS: List[str] = [
    "1024x576",
    "1280x720",
    "1600x900",
    "1920x1080",
    "Fullscreen (F11)",
]


def _get_system_font_dirs() -> List[str]:
    """Returns portable font search directories across Windows, macOS, and Linux."""
    dirs: List[str] = []
    # 1. Optional repository-local fonts directory
    repo_fonts = os.path.join(REPO_ROOT, "assets", "fonts")
    if os.path.isdir(repo_fonts):
        dirs.append(repo_fonts)

    # 2. Windows font directories
    windir = os.environ.get("WINDIR") or os.environ.get("SystemRoot")
    if windir:
        dirs.append(os.path.join(windir, "Fonts"))
    local_app = os.environ.get("LOCALAPPDATA")
    if local_app:
        dirs.append(os.path.join(local_app, "Microsoft", "Windows", "Fonts"))

    # 3. macOS font directories
    dirs.extend([
        "/System/Library/Fonts",
        "/Library/Fonts",
        os.path.expanduser("~/Library/Fonts"),
    ])

    # 4. Linux font directories
    dirs.extend([
        "/usr/share/fonts",
        "/usr/local/share/fonts",
        os.path.expanduser("~/.local/share/fonts"),
        os.path.expanduser("~/.fonts"),
    ])
    return [d for d in dirs if os.path.isdir(d)]


def discover_available_fonts() -> Dict[str, Optional[str]]:
    """
    Discovers available TTF fonts on the current machine without hardcoded paths.
    Always includes 'Default (Pixel)' first so every OS has a guaranteed fallback.
    """
    available: Dict[str, Optional[str]] = {"Default (Pixel)": None}
    font_dirs = _get_system_font_dirs()

    # Build a case-insensitive lookup of filenames in the font directories
    file_map: Dict[str, str] = {}
    for fdir in font_dirs:
        try:
            for root, _subdirs, files in os.walk(fdir):
                for fname in files:
                    lower = fname.lower()
                    if (lower.endswith(".ttf") or lower.endswith(".otf")) and lower not in file_map:
                        file_map[lower] = os.path.join(root, fname)
                # Avoid deep recursion in Windows\Fonts which is flat
                if "windows" in fdir.lower():
                    break
        except Exception:
            continue

    for label, candidates in SYSTEM_FONT_CANDIDATES:
        for cand in candidates:
            match = file_map.get(cand.lower())
            if match and os.path.isfile(match):
                available[label] = match
                break

    return available


class UISettingsManager:
    """
    Singleton managing `config.json` persistence, custom Raylib fonts,
    `Ctrl + '+'` / `Ctrl + '-'` font scaling, `F11` fullscreen, and the
    3 interactive top-bar dropdown menus (`Font`, `Size`, `Window`).
    """

    def __init__(self):
        self.virtual_width = 1280
        self.virtual_height = 720
        self.available_fonts = discover_available_fonts()
        self.font_names = list(self.available_fonts.keys())

        # Persisted settings
        self.font_name = "Default (Pixel)"
        self.font_size_offset = 0
        self.window_size = "1280x720"
        self.fullscreen = False

        # Runtime state
        self.window_initialized = False
        self.loaded_fonts: Dict[str, _pr.Font] = {}
        self.open_dropdown: Optional[str] = None  # "font", "size", "window", or None
        self.bar_drawn_this_frame = False
        self.bar_x = 450
        self.bar_y = 18
        self.auto_overlay_enabled = True

        self.load_config()

    # ------------------------------------------------------------------
    # Config persistence (`config.json` in repo root)
    # ------------------------------------------------------------------
    def load_config(self):
        """Loads preferences from `config.json`, falling back safely if missing."""
        if os.path.isfile(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                saved_font = str(data.get("font_name", "Default (Pixel)"))
                if saved_font in self.available_fonts:
                    self.font_name = saved_font
                else:
                    self.font_name = "Default (Pixel)"

                offset = int(data.get("font_size_offset", 0))
                self.font_size_offset = max(-4, min(8, offset))

                wsize = str(data.get("window_size", "1280x720"))
                if wsize in ("1024x576", "1280x720", "1600x900", "1920x1080"):
                    self.window_size = wsize
                else:
                    self.window_size = "1280x720"

                self.fullscreen = bool(data.get("fullscreen", False))
            except Exception:
                pass
        else:
            self.save_config()

    def save_config(self):
        """Writes current preferences to `config.json` in the repository root."""
        data = {
            "font_name": self.font_name,
            "font_size_offset": self.font_size_offset,
            "window_size": self.window_size,
            "fullscreen": self.fullscreen,
        }
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as fp:
                json.dump(data, fp, indent=2)
        except Exception:
            pass

    def reload_from_disk(self):
        """Reloads `config.json` (used when returning to launcher from a minigame)."""
        prev_wsize = self.window_size
        prev_fs = self.fullscreen
        self.load_config()
        if self.window_initialized and (self.window_size != prev_wsize or self.fullscreen != prev_fs):
            self.apply_window_mode()

    # ------------------------------------------------------------------
    # Font management
    # ------------------------------------------------------------------
    def get_active_font(self):
        """Returns the active Raylib `Font` object (`None` for Default Pixel font)."""
        if not self.window_initialized or self.font_name == "Default (Pixel)":
            return None
        if self.font_name in self.loaded_fonts:
            return self.loaded_fonts[self.font_name]

        ttf_path = self.available_fonts.get(self.font_name)
        if ttf_path and os.path.isfile(ttf_path):
            try:
                fnt = _pr.load_font_ex(ttf_path, 36, None, 0)
                if fnt.glyphCount > 0:
                    _pr.set_texture_filter(fnt.texture, _pr.TEXTURE_FILTER_BILINEAR)
                    self.loaded_fonts[self.font_name] = fnt
                    return fnt
            except Exception:
                pass
        return None

    def unload_all_fonts(self):
        """Unloads all cached TTF fonts before closing the Raylib window."""
        for fnt in self.loaded_fonts.values():
            try:
                _pr.unload_font(fnt)
            except Exception:
                pass
        self.loaded_fonts.clear()
        self.window_initialized = False

    # ------------------------------------------------------------------
    # Window resolution & Fullscreen (F11)
    # ------------------------------------------------------------------
    def apply_window_mode(self):
        """Applies the current `window_size` and `fullscreen` state to the Raylib window."""
        if not self.window_initialized:
            return

        is_borderless = _pr.is_window_state(_pr.FLAG_BORDERLESS_WINDOWED_MODE)
        is_fs = _pr.is_window_fullscreen()

        if self.fullscreen:
            if not is_borderless and not is_fs:
                _pr.toggle_borderless_windowed()
        else:
            if is_borderless:
                _pr.toggle_borderless_windowed()
            if is_fs:
                _pr.toggle_fullscreen()
            try:
                parts = self.window_size.split("x")
                target_w = int(parts[0])
                target_h = int(parts[1])
                if _pr.get_screen_width() != target_w or _pr.get_screen_height() != target_h:
                    _pr.set_window_size(target_w, target_h)
                    mon = _pr.get_current_monitor()
                    mw = _pr.get_monitor_width(mon)
                    mh = _pr.get_monitor_height(mon)
                    if mw > 0 and mh > 0:
                        _pr.set_window_position(
                            max(0, (mw - target_w) // 2),
                            max(28, (mh - target_h) // 2),
                        )
            except Exception:
                pass

    def get_scale_factors(self) -> Tuple[float, float]:
        """Returns (scale_x, scale_y) from virtual 1280x720 space to actual window size."""
        if not self.window_initialized:
            return 1.0, 1.0
        sw = max(1, _pr.get_screen_width())
        sh = max(1, _pr.get_screen_height())
        return sw / float(self.virtual_width), sh / float(self.virtual_height)

    def apply_2d_scale_matrix(self):
        """Applies `rl_scalef` so 1280x720 draw calls fill the current window."""
        sx, sy = self.get_scale_factors()
        if abs(sx - 1.0) > 1e-3 or abs(sy - 1.0) > 1e-3:
            _pr.rl_scalef(sx, sy, 1.0)

    # ------------------------------------------------------------------
    # Shortcuts (`Ctrl + '+'`, `Ctrl + '-'`, `F11`)
    # ------------------------------------------------------------------
    def handle_shortcuts(self):
        """Checks keyboard shortcuts for Font Size (`Ctrl +/-`) and Fullscreen (`F11`)."""
        # F11 toggles Fullscreen
        if _pr.is_key_pressed(_pr.KEY_F11):
            self.fullscreen = not self.fullscreen
            self.apply_window_mode()
            self.save_config()

        # Ctrl + '+' and Ctrl + '-' for Font Size scaling
        ctrl_down = (
            _pr.is_key_down(_pr.KEY_LEFT_CONTROL)
            or _pr.is_key_down(_pr.KEY_RIGHT_CONTROL)
        )
        if ctrl_down:
            # Support ANSI ('='), Numpad ('+'), and Spanish/ISO ('+' on KEY_RIGHT_BRACKET)
            plus_pressed = (
                _pr.is_key_pressed(_pr.KEY_EQUAL)
                or _pr.is_key_pressed(_pr.KEY_KP_ADD)
                or _pr.is_key_pressed(_pr.KEY_RIGHT_BRACKET)
            )
            # Support ANSI ('-'), Numpad ('-'), and Spanish/ISO ('-' on KEY_SLASH)
            minus_pressed = (
                _pr.is_key_pressed(_pr.KEY_MINUS)
                or _pr.is_key_pressed(_pr.KEY_KP_SUBTRACT)
                or _pr.is_key_pressed(_pr.KEY_SLASH)
            )
            if plus_pressed:
                self.font_size_offset = min(8, self.font_size_offset + 2)
                self.save_config()
            elif minus_pressed:
                self.font_size_offset = max(-4, self.font_size_offset - 2)
                self.save_config()

    # ------------------------------------------------------------------
    # Top-Bar Interactive Dropdowns (`Font`, `Size`, `Window`)
    # ------------------------------------------------------------------
    def _draw_raw_label(self, text: str, x: int, y: int, size: int, color: Color):
        """Draws text inside the compact dropdown widgets with controlled sizing."""
        fnt = self.get_active_font()
        eff_size = max(11, min(17, size + (self.font_size_offset // 2)))
        if fnt is not None:
            _pr.draw_text_ex(fnt, str(text), Vector2(float(x), float(y)), float(eff_size), 1.0, color)
        else:
            _pr.draw_text(str(text), int(x), int(y), int(eff_size), color)

    def _size_label(self) -> str:
        for lbl, val in FONT_SIZE_OPTIONS:
            if val == self.font_size_offset:
                return lbl
        sign = "+" if self.font_size_offset >= 0 else ""
        return f"Custom ({sign}{self.font_size_offset})"

    def _window_label(self) -> str:
        if self.fullscreen:
            return "Fullscreen (F11)"
        return self.window_size

    def render_top_bar_dropdowns(self, base_x: int = 450, base_y: int = 18):
        """
        Renders the 3 dropdown menus (`Font`, `Size`, `Window`) in the header area
        and processes mouse interactions.
        """
        mx = _pr.get_mouse_x()
        my = _pr.get_mouse_y()
        clicked = _pr.is_mouse_button_pressed(_pr.MOUSE_BUTTON_LEFT)

        # Layout for the 3 dropdown boxes inside x=450..980 (530px total width)
        box_h = 30
        boxes = [
            ("font", base_x, base_y, 184, f"Font: {self.font_name[:13]}"),
            ("size", base_x + 190, base_y, 152, f"Size: {self._size_label()}"),
            ("window", base_x + 348, base_y, 180, f"Win: {self._window_label()}"),
        ]

        # Draw closed/header buttons
        clicked_header = False
        for key, bx, by, bw, label in boxes:
            hovered = (bx <= mx <= bx + bw) and (by <= my <= by + box_h)
            is_open = self.open_dropdown == key
            bg_col = Color(34, 56, 96, 240) if (hovered or is_open) else Color(20, 30, 50, 230)
            border_col = Color(90, 215, 255, 255) if (hovered or is_open) else Color(60, 85, 135, 255)

            _pr.draw_rectangle(bx, by, bw, box_h, bg_col)
            _pr.draw_rectangle_lines(bx, by, bw, box_h, border_col)
            self._draw_raw_label(label, bx + 8, by + 7, 13, WHITE)
            arrow = "^" if is_open else "v"
            self._draw_raw_label(arrow, bx + bw - 16, by + 7, 13, GOLD if is_open else LIGHTGRAY)

            if clicked and hovered:
                self.open_dropdown = None if is_open else key
                clicked_header = True

        # Draw expanded option list if a dropdown is open
        if self.open_dropdown is not None:
            if self.open_dropdown == "font":
                dd_x, dd_y, dd_w = base_x, base_y + box_h + 2, 184
                options = [(name, name == self.font_name) for name in self.font_names]
            elif self.open_dropdown == "size":
                dd_x, dd_y, dd_w = base_x + 190, base_y + box_h + 2, 152
                options = [(f"{lbl} [Ctrl+/-]", val == self.font_size_offset) for lbl, val in FONT_SIZE_OPTIONS]
            else:
                dd_x, dd_y, dd_w = base_x + 348, base_y + box_h + 2, 180
                options = [
                    (
                        opt,
                        (self.fullscreen and opt == "Fullscreen (F11)")
                        or (not self.fullscreen and opt == self.window_size),
                    )
                    for opt in WINDOW_SIZE_OPTIONS
                ]

            item_h = 28
            total_h = len(options) * item_h + 4
            _pr.draw_rectangle(dd_x, dd_y, dd_w, total_h, Color(14, 20, 34, 250))
            _pr.draw_rectangle_lines(dd_x, dd_y, dd_w, total_h, Color(90, 215, 255, 255))

            clicked_option = False
            for idx, (opt_text, is_current) in enumerate(options):
                iy = dd_y + 2 + idx * item_h
                opt_hover = (dd_x <= mx <= dd_x + dd_w) and (iy <= my < iy + item_h)
                if opt_hover:
                    _pr.draw_rectangle(dd_x + 2, iy, dd_w - 4, item_h, Color(42, 95, 160, 255))
                elif is_current:
                    _pr.draw_rectangle(dd_x + 2, iy, dd_w - 4, item_h, Color(26, 52, 88, 255))

                txt_col = GOLD if is_current else (WHITE if opt_hover else LIGHTGRAY)
                self._draw_raw_label(opt_text, dd_x + 8, iy + 6, 13, txt_col)

                if clicked and opt_hover:
                    clicked_option = True
                    if self.open_dropdown == "font":
                        self.font_name = self.font_names[idx]
                    elif self.open_dropdown == "size":
                        self.font_size_offset = FONT_SIZE_OPTIONS[idx][1]
                    elif self.open_dropdown == "window":
                        chosen = WINDOW_SIZE_OPTIONS[idx]
                        if chosen == "Fullscreen (F11)":
                            self.fullscreen = True
                        else:
                            self.fullscreen = False
                            self.window_size = chosen
                        self.apply_window_mode()
                    self.save_config()
                    self.open_dropdown = None
                    break

            if clicked and not clicked_header and not clicked_option:
                self.open_dropdown = None


# Global singleton instance shared across `launcher.py` and `minigames/*.py`
ui_settings = UISettingsManager()


# ==============================================================================
# TRANSPARENT RAYLIB WRAPPERS (EXPORTED VIA `from utils import *`)
# ==============================================================================

def init_window(width: int, height: int, title: str):
    """Initializes the Raylib window and immediately applies saved `config.json` settings."""
    _pr.set_config_flags(_pr.FLAG_WINDOW_RESIZABLE)
    _pr.init_window(int(width), int(height), str(title))
    ui_settings.virtual_width = int(width)
    ui_settings.virtual_height = int(height)
    ui_settings.window_initialized = True
    ui_settings.load_config()
    ui_settings.apply_window_mode()


def close_window():
    """Unloads cached TrueType fonts cleanly before closing the Raylib window."""
    ui_settings.unload_all_fonts()
    _pr.close_window()


def begin_drawing():
    """Begins the frame, processes `Ctrl +/-` and `F11` shortcuts, and scales coordinates."""
    ui_settings.bar_drawn_this_frame = False
    ui_settings.handle_shortcuts()
    sx, sy = ui_settings.get_scale_factors()
    _pr.set_mouse_scale(1.0 / sx, 1.0 / sy)
    _pr.begin_drawing()
    ui_settings.apply_2d_scale_matrix()


def end_drawing():
    """Renders the top-bar Font/Size/Window dropdowns on the top layer and ends the frame."""
    if ui_settings.auto_overlay_enabled and not ui_settings.bar_drawn_this_frame:
        ui_settings.render_top_bar_dropdowns(ui_settings.bar_x, ui_settings.bar_y)
        ui_settings.bar_drawn_this_frame = True
    _pr.end_drawing()


def begin_mode_2d(camera: Camera2D):
    """Begins 2D camera mode while preserving window resolution scaling."""
    sx, sy = ui_settings.get_scale_factors()
    if abs(sx - 1.0) > 1e-3 or abs(sy - 1.0) > 1e-3:
        scaled_cam = Camera2D()
        scaled_cam.offset = Vector2(camera.offset.x * sx, camera.offset.y * sy)
        scaled_cam.target = Vector2(camera.target.x, camera.target.y)
        scaled_cam.rotation = camera.rotation
        scaled_cam.zoom = camera.zoom * ((sx + sy) * 0.5)
        _pr.begin_mode_2d(scaled_cam)
    else:
        _pr.begin_mode_2d(camera)


def end_mode_2d():
    """Ends 2D camera mode and restores virtual 1280x720 scaling for HUD overlays."""
    _pr.end_mode_2d()
    ui_settings.apply_2d_scale_matrix()


def begin_mode_3d(camera):
    """Begins 3D camera mode across the full window viewport."""
    _pr.begin_mode_3d(camera)


def end_mode_3d():
    """Ends 3D camera mode and restores virtual 1280x720 scaling for 2D HUD overlays."""
    _pr.end_mode_3d()
    ui_settings.apply_2d_scale_matrix()


def begin_scissor_mode(x: int, y: int, width: int, height: int):
    """
    Begins scissor mode (clipping rectangle) while transparently scaling
    virtual 1280x720 coordinates to actual window resolution and fullscreen.
    """
    sx, sy = ui_settings.get_scale_factors()
    _pr.begin_scissor_mode(int(round(x * sx)), int(round(y * sy)), int(round(width * sx)), int(round(height * sy)))


def end_scissor_mode():
    """Ends scissor mode."""
    _pr.end_scissor_mode()


def draw_text(text: str, pos_x: int, pos_y: int, font_size: int, color: Color):
    """
    Renders text using the user's selected Font from `config.json` and scales
    `font_size` dynamically with `font_size_offset` (`Ctrl + '+'` / `Ctrl + '-'`).
    """
    eff_size = max(8, int(font_size) + ui_settings.font_size_offset)
    fnt = ui_settings.get_active_font()
    if fnt is not None:
        _pr.draw_text_ex(
            fnt,
            str(text),
            Vector2(float(int(pos_x)), float(int(pos_y))),
            float(eff_size),
            1.0,
            color,
        )
    else:
        _pr.draw_text(str(text), int(pos_x), int(pos_y), int(eff_size), color)


def draw_ui_settings_bar(x: int = 450, y: int = 18):
    """Explicit helper to position the top-bar Font, Size, and Window dropdowns."""
    ui_settings.bar_x = int(x)
    ui_settings.bar_y = int(y)

