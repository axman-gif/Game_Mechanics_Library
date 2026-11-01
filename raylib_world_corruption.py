# -*- coding: utf-8 -*-
"""
Created on Sat Oct 24 2026

@author: AXMAN
Raylib World Corruption Simulation
Interactive fort expansion and grid corruption simulator built with Raylib
"""

import io
import math
import random
import wave
import struct as py_struct
import sys
from pyray import *

sys.dont_write_bytecode = True

# ==============================================================================
# ORIGINAL DATA STRUCTURE (world_creation.py)
# ==============================================================================

def create_world(width=20, height=12):
    return [[0 for _ in range(width)] for _ in range(height)]

def print_world(grid):
    for row in grid:
        print(" ".join(f"{val:2}" for val in row))
    print()

def is_border(square, grid, faction):
    x, y = square["x"], square["y"]
    height = len(grid)
    width = len(grid[0])
    directions = {"N":(-1,0),
                  "S":(1,0),
                  "W":(0,-1),
                  "E":(0,1)
        }
    
    for dy, dx in directions.values():
        ny, nx = y + dy, x + dx
        if not (0 <= ny < height and 0 <= nx < width):
            return True
        if grid[ny][nx] != faction:
            return True
            
    return False

def is_surrounded(grid, x, y, treat_edges_as_occupied=True):
    height = len(grid)
    width = len(grid[0])
    directions = {"N":(-1,0),
                  "S":(1,0),
                  "W":(0,-1),
                  "E":(0,1)
        }
    
    occupied_count = 0
    for dy, dx in directions.values():
        ny, nx = y + dy, x + dx
        if 0 <= ny < height and 0 <= nx < width:
            if grid[ny][nx] != 0:
                occupied_count += 1
        else:
            if treat_edges_as_occupied:
                occupied_count += 1
                
    return occupied_count == 4

def spawn(grid, faction, avoid_edge_traps=True):
    height = len(grid)
    width = len(grid[0])
    valid_positions = []

    for y in range(height):
        for x in range(width):
            if grid[y][x] == 0:
                if not is_surrounded(grid, x, y, treat_edges_as_occupied=avoid_edge_traps):
                    valid_positions.append({"x": x, "y": y})

    if not valid_positions:
        print(f"No free cells for faction {faction}.")
        return None

    chosen = random.choice(valid_positions)
    grid[chosen["y"]][chosen["x"]] = faction
    return chosen

class Fort:
    def __init__(self, faction, grid, x=None, y=None):
        self.faction = faction
        self.fort_squares = []
        self.border_squares = []

        # If explicit valid x, y coordinates are given, place manually
        if x is not None and y is not None:
            grid[y][x] = self.faction
            self.fort_squares.append({"x": x, "y": y})
        # If omitted, delegate automatically to spawn()
        else:
            spawned = spawn(grid, self.faction)
            if spawned:
                self.fort_squares.append(spawned)

    def expand(self, grid):
        """
        Executes one expansion step (1 single cell).
        Returns True if expansion succeeded, False if blocked with no space.
        """
        if not self.fort_squares:
            return False

        height = len(grid)
        width = len(grid[0])
        directions = {"N":(-1,0),
                      "S":(1,0),
                      "W":(0,-1),
                      "E":(0,1)
            }

        candidates = set()
        occupied = {(sq["x"], sq["y"]) for sq in self.fort_squares}

        for sq in self.fort_squares:
            for dy, dx in directions.values():
                nx, ny = sq["x"] + dx, sq["y"] + dy
                if 0 <= nx < width and 0 <= ny < height:
                    if (nx, ny) not in occupied and grid[ny][nx] == 0:
                        candidates.add((nx, ny))

        if not candidates:
            return False

        chosen_x, chosen_y = random.choice(list(candidates))
        grid[chosen_y][chosen_x] = self.faction
        self.fort_squares.append({"x": chosen_x, "y": chosen_y})
        return True

    def update_borders(self, grid):
        self.border_squares.clear()
        for sq in self.fort_squares:
            if is_border(sq, grid, self.faction):
                self.border_squares.append(sq)
        return self.border_squares


# ==============================================================================
# AUDIO SYNTHESIZER (Loud & Punchy Chiptune/Retro Soundtrack & SFX)
# ==============================================================================

def generate_synth_soundtrack(sample_rate=22050):
    """
    Procedural chiptune/retro ambient music synthesizer.
    Generates a full-bodied 8-bar harmonic loop with bass, pads, and arpeggios,
    normalized to optimal dynamic range for louder, richer playback.
    """
    bpm = 116
    beat_sec = 60.0 / bpm
    bar_sec = beat_sec * 4.0
    
    progression = [
        ([220.00, 261.63, 329.63], 110.00),  # Am
        ([174.61, 220.00, 261.63], 87.31),   # F
        ([261.63, 329.63, 392.00], 130.81),  # C
        ([196.00, 246.94, 293.66], 98.00),   # G
        ([146.83, 174.61, 220.00], 73.42),   # Dm
        ([164.81, 196.00, 246.94], 82.41),   # Em
        ([174.61, 220.00, 261.63], 87.31),   # F
        ([164.81, 207.65, 246.94], 82.41),   # E7
    ]
    
    total_bars = len(progression)
    total_sec = total_bars * bar_sec
    total_samples = int(total_sec * sample_rate)
    buf = [0.0] * total_samples
    
    for bar_idx, (chord_notes, bass_f) in enumerate(progression):
        b_start = int(bar_idx * bar_sec * sample_rate)
        b_end = int((bar_idx + 1) * bar_sec * sample_rate)
        
        # 1. Bassline with punchy low presence
        q_len = int(beat_sec * sample_rate)
        for q in range(4):
            q_s = b_start + q * q_len
            q_e = min(q_s + q_len, total_samples)
            f_bass = bass_f * (2.0 if q in (1, 3) else 1.0)
            for s in range(q_s, q_e):
                t_sub = (s - q_s) / sample_rate
                env = math.exp(-3.8 * t_sub)
                buf[s] += 0.26 * math.sin(2.0 * math.pi * f_bass * t_sub) * env
                
        # 2. Rich warm chord pad (increased presence for louder acoustic body)
        for s in range(b_start, min(b_end, total_samples)):
            t_bar = (s - b_start) / sample_rate
            env = math.sin(math.pi * t_bar / bar_sec)
            for freq in chord_notes:
                buf[s] += 0.15 * math.sin(2.0 * math.pi * freq * t_bar) * env
                
        # 3. Punchy melodic arpeggio (16 sixteenth notes per bar, crisp square/sine mix)
        step_len = int((beat_sec / 4.0) * sample_rate)
        scale_arp = chord_notes + [chord_notes[0] * 2.0, chord_notes[1] * 2.0, chord_notes[2] * 2.0]
        for step in range(16):
            s_start = b_start + step * step_len
            s_end = min(s_start + step_len, total_samples)
            note_freq = scale_arp[step % len(scale_arp)]
            for s in range(s_start, s_end):
                t_arp = (s - s_start) / sample_rate
                env = math.exp(-11.0 * t_arp)
                sq = 1.0 if math.sin(2.0 * math.pi * note_freq * t_arp) > 0 else -1.0
                sine = math.sin(2.0 * math.pi * note_freq * t_arp)
                buf[s] += 0.24 * (0.40 * sq + 0.60 * sine) * env

    # Boundary fade for clickless loop
    fade_samples = int(0.05 * sample_rate)
    for i in range(fade_samples):
        factor = i / fade_samples
        buf[i] *= factor
        buf[total_samples - 1 - i] *= factor

    # Peak normalization to 98% full-scale dynamic range for maximum volume output
    peak = max(abs(v) for v in buf) if buf else 1.0
    if peak > 0:
        norm_gain = 0.98 / peak
        for i in range(total_samples):
            buf[i] *= norm_gain
        
    raw_frames = bytearray()
    for val in buf:
        clamped = max(-1.0, min(1.0, val))
        raw_frames += py_struct.pack('<h', int(clamped * 32767))
        
    out = io.BytesIO()
    with wave.open(out, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(raw_frames)
    return out.getvalue()

def generate_sfx(freq_start, freq_end, duration=0.08, sample_rate=22050):
    """Generates a short synthesized sound effect for user interactions."""
    total = int(sample_rate * duration)
    frames = bytearray()
    phase = 0.0
    for i in range(total):
        t = i / total
        f = freq_start + (freq_end - freq_start) * t
        phase += 2.0 * math.pi * f / sample_rate
        env = math.sin(math.pi * (1.0 - t))
        val = int(32767 * 0.35 * math.sin(phase) * env)
        frames += py_struct.pack('<h', val)
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(frames)
    data = buf.getvalue()
    w_obj = load_wave_from_memory(b'.wav', data, len(data))
    snd = load_sound_from_wave(w_obj)
    unload_wave(w_obj)
    return snd


# ==============================================================================
# GENERAL SETTINGS & RESOLUTION 1280 * 720
# ==============================================================================

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

def get_virtual_mouse_position():
    """Maps actual screen mouse position to 1280x720 virtual canvas coordinates."""
    sw = get_screen_width()
    sh = get_screen_height()
    scale = min(sw / SCREEN_WIDTH, sh / SCREEN_HEIGHT)
    ox = (sw - SCREEN_WIDTH * scale) / 2.0
    oy = (sh - SCREEN_HEIGHT * scale) / 2.0
    raw = get_mouse_position()
    return Vector2((raw.x - ox) / scale, (raw.y - oy) / scale)


# ==============================================================================
# UI COMPONENTS (Sliders & Buttons)
# ==============================================================================

class UISlider:
    def __init__(self, x, y, width, height, min_val, max_val, current_val, label, unit="", is_proportional=False):
        self.rect = Rectangle(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.val = current_val
        self.label = label
        self.unit = unit
        self.is_proportional = is_proportional
        self.dragging = False

    def update(self):
        mouse_pos = get_virtual_mouse_position()
        mouse_down = is_mouse_button_down(MOUSE_BUTTON_LEFT)

        range_span = max(1, self.max_val - self.min_val)
        self.val = max(self.min_val, min(self.max_val, self.val))
        norm = (self.val - self.min_val) / range_span
        norm = max(0.0, min(1.0, norm))
        
        handle_x = self.rect.x + norm * self.rect.width
        handle_rect = Rectangle(handle_x - 12, self.rect.y - 4, 24, self.rect.height + 8)

        track_hover = check_collision_point_rec(mouse_pos, self.rect)
        handle_hover = check_collision_point_rec(mouse_pos, handle_rect)

        if is_mouse_button_pressed(MOUSE_BUTTON_LEFT) and (track_hover or handle_hover):
            self.dragging = True

        if not mouse_down:
            self.dragging = False

        changed = False
        if self.dragging:
            norm = (mouse_pos.x - self.rect.x) / self.rect.width
            norm = max(0.0, min(1.0, norm))
            new_val = int(round(self.min_val + norm * (self.max_val - self.min_val)))
            new_val = max(self.min_val, min(self.max_val, new_val))
            if new_val != self.val:
                self.val = new_val
                changed = True

        return changed

    def draw(self):
        # Track background bar
        track_bar = Rectangle(self.rect.x, self.rect.y + 4, self.rect.width, 8)
        draw_rectangle_rounded(track_bar, 0.5, 4, Color(50, 45, 55, 255))
        
        # Active filled bar
        range_span = max(1, self.max_val - self.min_val)
        norm = (self.val - self.min_val) / range_span
        norm = max(0.0, min(1.0, norm))
        handle_x = self.rect.x + norm * self.rect.width
        fill_w = max(0.0, handle_x - self.rect.x)
        if fill_w > 0:
            fill_bar = Rectangle(self.rect.x, self.rect.y + 4, fill_w, 8)
            draw_rectangle_rounded(fill_bar, 0.5, 4, Color(255, 205, 50, 255))

        # Handle thumb (strictly kept within boundaries)
        handle_color = Color(255, 235, 120, 255) if self.dragging else Color(245, 245, 245, 255)
        cx = int(handle_x)
        cy = int(self.rect.y + self.rect.height / 2)
        draw_circle(cx, cy, 9, handle_color)
        draw_circle_lines(cx, cy, 9, BLACK)

        # Label
        draw_text(self.label, int(self.rect.x), int(self.rect.y - 18), 14, WHITE)
        
        # Formatted readout (proportional or standard)
        if self.is_proportional:
            pct = norm * 100.0
            val_str = f"{self.val} / {self.max_val} ({pct:.0f}%)"
        elif self.unit:
            val_str = f"{self.val}{self.unit}"
        else:
            val_str = str(self.val)

        val_w = measure_text(val_str, 14)
        draw_text(val_str, int(self.rect.x + self.rect.width - val_w), int(self.rect.y - 18), 14, Color(255, 215, 60, 255))

def draw_ui_button(rect, text, bg_color, hover_color, text_color, font_size=14):
    """Draws an interactive button and returns True if clicked."""
    mouse_pos = get_virtual_mouse_position()
    hovered = check_collision_point_rec(mouse_pos, rect)
    col = hover_color if hovered else bg_color
    draw_rectangle_rounded(rect, 0.25, 4, col)
    draw_rectangle_rounded_lines(rect, 0.25, 4, BLACK)
    
    t_w = measure_text(text, font_size)
    t_x = int(rect.x + (rect.width - t_w) / 2)
    t_y = int(rect.y + (rect.height - font_size) / 2)
    draw_text(text, t_x, t_y, font_size, text_color)
    return hovered and is_mouse_button_pressed(MOUSE_BUTTON_LEFT)


# Initialize Raylib Window
set_config_flags(FLAG_WINDOW_RESIZABLE)
init_window(SCREEN_WIDTH, SCREEN_HEIGHT, "World Corruption - Raylib Simulator")
set_target_fps(0)

# Virtual render texture for proportional scaling and fullscreen letterboxing
target_render = load_render_texture(SCREEN_WIDTH, SCREEN_HEIGHT)
set_texture_filter(target_render.texture, TEXTURE_FILTER_BILINEAR)

# Initialize Audio Device
init_audio_device()
set_master_volume(1.0)

# Load synthesized background music stream from memory
bgm_data = generate_synth_soundtrack()
bgm_stream = load_music_stream_from_memory(b".wav", bgm_data, len(bgm_data))
play_music_stream(bgm_stream)

# Maximum initial volume (100% on natural logarithmic taper)
volume_slider_val = 100
initial_gain = math.pow(volume_slider_val / 100.0, 1.4)
set_music_volume(bgm_stream, initial_gain)
music_enabled = True

# Synthesized sound effects
snd_expand = generate_sfx(350, 750, 0.07)
snd_shrink = generate_sfx(650, 300, 0.07)
snd_reset  = generate_sfx(520, 1040, 0.12)
snd_place  = generate_sfx(440, 880, 0.08)

# ==============================================================================
# CENTER 480 * 480 GRID
# ==============================================================================

GRID_SIZE = 480
GRID_X = (SCREEN_WIDTH - GRID_SIZE) // 2   # (1280 - 480) // 2 = 400
GRID_Y = (SCREEN_HEIGHT - GRID_SIZE) // 2  # (720 - 480) // 2 = 120

# Palette of distinct colors for fort circles
FACTION_COLORS = [
    Color(33, 150, 243, 255),   # Fort 1: Electric Blue
    Color(46, 204, 113, 255),   # Fort 2: Emerald Green
    Color(255, 193, 7, 255),    # Fort 3: Amber Gold
    Color(170, 70, 220, 255),   # Fort 4: Vivid Purple
    Color(255, 110, 30, 255),   # Fort 5: Coral Orange
    Color(0, 210, 210, 255),    # Fort 6: Bright Turquoise
    Color(255, 105, 180, 255),  # Fort 7: Hot Pink
    Color(245, 245, 245, 255),  # Fort 8: Pure White
]

# ==============================================================================
# WORLD & SIMULATION STATE
# ==============================================================================

world_w = 16
world_h = 16
num_forts = 8

world = []
forts = []
expansion_history = []  # Stack of (fort, x, y) tuples for exact reversibility
current_turn_idx = 0    # Cyclic turn order (0 -> 1 -> 2 -> ... -> 0)
status_message = "Ready. Press '+' to expand or '-' to shrink."
auto_play = False
auto_timer = 0.0

# Option 1: Interactive Spawn Placement Mode
placement_mode = False
selected_spawn_fort_idx = 0

def get_proportional_capacity():
    """Calculates fair proportional cell capacity per fort."""
    return max(1, (world_w * world_h) // num_forts)

def setup_world(w, h, f_count):
    """Initializes the grid and places each fort at its starting position."""
    global world, forts, expansion_history, current_turn_idx, world_w, world_h, num_forts, selected_spawn_fort_idx
    world_w = w
    world_h = h
    num_forts = f_count
    world = create_world(world_w, world_h)
    forts = []
    expansion_history = []
    current_turn_idx = 0
    selected_spawn_fort_idx = max(0, min(selected_spawn_fort_idx, num_forts - 1))

    # Preferred initial spots distributed cleanly in a circular ring around center
    cx, cy = world_w // 2, world_h // 2
    r = max(2, min(world_w, world_h) // 4)
    initial_spots = []
    for i in range(num_forts):
        angle = -math.pi / 2.0 + i * (2.0 * math.pi / num_forts)
        sx = int(round(cx + r * math.cos(angle)))
        sy = int(round(cy + r * math.sin(angle)))
        sx = max(0, min(world_w - 1, sx))
        sy = max(0, min(world_h - 1, sy))
        initial_spots.append((sx, sy))

    for i in range(num_forts):
        faction_id = i + 1
        placed = False
        if i < len(initial_spots):
            sx, sy = initial_spots[i]
            if 0 <= sx < world_w and 0 <= sy < world_h and world[sy][sx] == 0:
                forts.append(Fort(faction_id, world, sx, sy))
                placed = True
        if not placed:
            forts.append(Fort(faction_id, world)) # Fallback to spawn()
            
    for f in forts:
        f.update_borders(world)

def place_initial_fort(fort_idx, target_x, target_y):
    """Sets the initial spawn nucleus of a fort to exact grid coordinates."""
    global world, forts, expansion_history, current_turn_idx
    if not (0 <= fort_idx < len(forts)):
        return False
    if not (0 <= target_x < world_w and 0 <= target_y < world_h):
        return False
    
    f = forts[fort_idx]
    if world[target_y][target_x] != 0 and world[target_y][target_x] != f.faction:
        return False
        
    # Clear previous cells for this fort
    for sq in f.fort_squares:
        world[sq["y"]][sq["x"]] = 0
    expansion_history.clear()
    current_turn_idx = 0
    
    # Assign new spawn nucleus
    world[target_y][target_x] = f.faction
    f.fort_squares = [{"x": target_x, "y": target_y}]
    f.update_borders(world)
    return True

def randomize_all_spawns():
    """Randomly scatters initial fort spawns across valid empty board positions."""
    global world, forts, expansion_history, current_turn_idx, status_message
    expansion_history.clear()
    current_turn_idx = 0
    world = create_world(world_w, world_h)
    new_forts = []
    for i in range(num_forts):
        faction_id = i + 1
        new_forts.append(Fort(faction_id, world))
    forts = new_forts
    for f in forts:
        f.update_borders(world)
    if music_enabled:
        play_sound(snd_reset)
    status_message = "All fort spawn points randomly redistributed."

setup_world(world_w, world_h, num_forts)

def step_forward():
    """
    Expands by 1 cell in cyclic turn order (1, 2, 3, 1, 2...).
    Continues until empty spaces on the board are exhausted.
    """
    global current_turn_idx, status_message
    empty_count = sum(row.count(0) for row in world)
    if empty_count == 0:
        status_message = "Grid is full! No empty cells remaining."
        return False

    n_forts = len(forts)
    # Attempt expansion in cyclic turn order starting from current_turn_idx
    for attempt in range(n_forts):
        cand_idx = (current_turn_idx + attempt) % n_forts
        f = forts[cand_idx]
        if f.expand(world):
            new_sq = f.fort_squares[-1]
            expansion_history.append((f, new_sq["x"], new_sq["y"]))
            current_turn_idx = (cand_idx + 1) % n_forts
            f.update_borders(world)
            if music_enabled:
                play_sound(snd_expand)
            status_message = f"Turn executed: Fort {f.faction} expanded."
            return True

    status_message = "All forts are blocked without free adjacent space."
    return False

def step_backward():
    """
    Shrinks cells in exact reverse turn order (... 3, 2, 1, 3, 2).
    Operates until only the initial cell per fort remains.
    """
    global current_turn_idx, status_message
    if not expansion_history:
        status_message = "Only the initial cell remains for each fort."
        return False

    f, x, y = expansion_history.pop()
    
    # Remove cell from fort
    if f.fort_squares and f.fort_squares[-1] == {"x": x, "y": y}:
        f.fort_squares.pop()
    else:
        for idx in range(len(f.fort_squares) - 1, -1, -1):
            if f.fort_squares[idx]["x"] == x and f.fort_squares[idx]["y"] == y:
                f.fort_squares.pop(idx)
                break
                
    world[y][x] = 0
    f.update_borders(world)

    # Revert turn index to this fort
    if f in forts:
        current_turn_idx = forts.index(f)

    if music_enabled:
        play_sound(snd_shrink)
    status_message = f"Fort {f.faction} cell undone."
    return True

def reset_to_initial():
    """Resets world to the original state with only 1 initial cell per fort."""
    global current_turn_idx, status_message
    while expansion_history:
        f, x, y = expansion_history.pop()
        if len(f.fort_squares) > 1 and f.fort_squares[-1] == {"x": x, "y": y}:
            f.fort_squares.pop()
        world[y][x] = 0
        f.update_borders(world)
    current_turn_idx = 0
    if music_enabled:
        play_sound(snd_reset)
    status_message = "World reset to initial cells for each fort."

# ==============================================================================
# UI SLIDERS
# ==============================================================================

# Left panel: Sliders for world dimensions
slider_ancho = UISlider(40, 112, 310, 16, min_val=6, max_val=32, current_val=world_w, label="World Width (Columns)")
slider_largo = UISlider(40, 154, 310, 16, min_val=6, max_val=32, current_val=world_h, label="World Height (Rows)")
slider_fuertes = UISlider(40, 196, 310, 16, min_val=2, max_val=8, current_val=num_forts, label="Number of Forts")

# Proportional cell target slider
init_cap = get_proportional_capacity()
slider_casillas_fuerte = UISlider(
    40, 438, 310, 16,
    min_val=1,
    max_val=init_cap,
    current_val=1,
    label="Cells per Fort (Target)",
    is_proportional=True
)

# Right panel: Logarithmic volume slider below mute button
slider_volumen = UISlider(
    925, 592, 315, 16,
    min_val=0,
    max_val=100,
    current_val=volume_slider_val,
    label="Music Volume (Log Scale)",
    unit="%"
)

# Keyboard repeat timers for '+' and '-'
key_hold_time = 0.0
repeat_interval = 0.08
repeat_delay = 0.30

# ==============================================================================
# MAIN LOOP (No main loop function, direct while loop)
# ==============================================================================

while not window_should_close():
    dt = get_frame_time()

    # 1. Update procedural audio stream
    if music_enabled:
        update_music_stream(bgm_stream)

    # 2. Update interactive sliders
    slider_ancho.update()
    slider_largo.update()
    slider_fuertes.update()
    slider_casillas_fuerte.update()
    vol_changed = slider_volumen.update()

    # Update volume with natural logarithmic perception curve
    if vol_changed:
        vol_norm = slider_volumen.val / 100.0
        log_gain = math.pow(vol_norm, 1.4) if vol_norm > 0 else 0.0
        if music_enabled:
            set_music_volume(bgm_stream, log_gain)

    # 3. Handle keyboard shortcuts (+, -, R, N, M, E, G, 1-8, Space)
    char_pressed = get_char_pressed()
    
    # Key +
    plus_pressed = (
        is_key_pressed(KEY_KP_ADD) or 
        is_key_pressed(KEY_EQUAL) or 
        char_pressed == ord('+')
    )
    plus_down = is_key_down(KEY_KP_ADD) or is_key_down(KEY_EQUAL)
    
    # Key -
    minus_pressed = (
        is_key_pressed(KEY_MINUS) or 
        is_key_pressed(KEY_KP_SUBTRACT) or 
        char_pressed == ord('-')
    )
    minus_down = is_key_down(KEY_MINUS) or is_key_down(KEY_KP_SUBTRACT)

    # Key R (Reset)
    r_pressed = is_key_pressed(KEY_R) or char_pressed in (ord('r'), ord('R'))

    # Key N (Recreate World with dimensions)
    n_pressed = is_key_pressed(KEY_N) or char_pressed in (ord('n'), ord('N'))
    
    # Key M (Music Mute/Unmute)
    m_pressed = is_key_pressed(KEY_M) or char_pressed in (ord('m'), ord('M'))

    # Key Space (Auto-Play)
    space_pressed = is_key_pressed(KEY_SPACE)

    # Key E (Toggle Spawn Placement Mode)
    e_pressed = is_key_pressed(KEY_E) or char_pressed in (ord('e'), ord('E'))

    # Key G (Randomize All Spawns)
    g_pressed = is_key_pressed(KEY_G) or char_pressed in (ord('g'), ord('G'))

    # Key F11 (Toggle Fullscreen)
    f11_pressed = is_key_pressed(KEY_F11)
    if f11_pressed:
        toggle_fullscreen()
        if not is_window_fullscreen():
            set_window_size(SCREEN_WIDTH, SCREEN_HEIGHT)

    # Number keys 1-8 to switch active fort in placement mode
    for num_k in range(min(len(forts), 8)):
        if is_key_pressed(KEY_ONE + num_k) or char_pressed == ord(str(num_k + 1)):
            selected_spawn_fort_idx = num_k
            if placement_mode:
                status_message = f"Selected Fort {forts[selected_spawn_fort_idx].faction} for spawn placement."

    # Process Toggle Spawn Placement Mode
    if e_pressed:
        placement_mode = not placement_mode
        if placement_mode:
            auto_play = False
            reset_to_initial()
            if music_enabled:
                play_sound(snd_place)
            status_message = f"Placement Mode ON: Click grid cell to place Fort {forts[selected_spawn_fort_idx].faction}."
        else:
            if music_enabled:
                play_sound(snd_reset)
            status_message = "Initial spawns locked! Ready. Press '+' to expand."

    # Process Randomize Spawns
    if g_pressed:
        randomize_all_spawns()

    # Process Music Mute toggle
    if m_pressed:
        music_enabled = not music_enabled
        if music_enabled:
            resume_music_stream(bgm_stream)
            vol_norm = slider_volumen.val / 100.0
            set_music_volume(bgm_stream, math.pow(vol_norm, 1.4) if vol_norm > 0 else 0.0)
        else:
            pause_music_stream(bgm_stream)

    # Process Reset (R)
    if r_pressed:
        reset_to_initial()
        slider_casillas_fuerte.val = 1

    # Process Recreate World (N)
    if n_pressed:
        setup_world(slider_ancho.val, slider_largo.val, slider_fuertes.val)
        cap = get_proportional_capacity()
        slider_casillas_fuerte.max_val = cap
        slider_casillas_fuerte.val = 1
        if music_enabled:
            play_sound(snd_reset)
        status_message = "World recreated with new dimensions [N]."

    # Process Auto-Play
    if space_pressed:
        if not placement_mode:
            auto_play = not auto_play
        else:
            status_message = "Press 'E' to lock spawns before running auto-play!"

    if auto_play and not placement_mode:
        auto_timer += dt
        if auto_timer >= 0.12:
            auto_timer = 0.0
            if not step_forward():
                auto_play = False

    # Single press and smooth continuous hold repeat for + and -
    if plus_pressed:
        if not placement_mode:
            step_forward()
        else:
            status_message = "Press 'E' to lock spawns before expanding!"
        key_hold_time = 0.0
    elif plus_down and not placement_mode:
        key_hold_time += dt
        if key_hold_time > repeat_delay:
            step_forward()
            key_hold_time -= repeat_interval

    if minus_pressed:
        if not placement_mode:
            step_backward()
        else:
            status_message = "Press 'E' to lock spawns before shrinking!"
        key_hold_time = 0.0
    elif minus_down and not placement_mode:
        key_hold_time += dt
        if key_hold_time > repeat_delay:
            step_backward()
            key_hold_time -= repeat_interval

    if not plus_down and not minus_down:
        key_hold_time = 0.0

    # Keep proportional target slider synchronized with dynamic board capacity
    if forts:
        base_cap = get_proportional_capacity()
        highest_fort = max(len(f.fort_squares) for f in forts)
        slider_casillas_fuerte.max_val = max(base_cap, highest_fort)
        if not slider_casillas_fuerte.dragging:
            avg_cells = sum(len(f.fort_squares) for f in forts) // len(forts)
            slider_casillas_fuerte.val = max(1, avg_cells)

    # ==========================================================================
    # RENDERING (Virtual 1280x720 Canvas -> Proportional Display with Letterbox)
    # ==========================================================================
    begin_texture_mode(target_render)

    # Red background
    clear_background(Color(195, 28, 38, 255))

    # --------------------------------------------------------------------------
    # Left Panel: Settings and Actions
    # --------------------------------------------------------------------------
    panel_left = Rectangle(25, 25, 345, 670)
    draw_rectangle_rounded(panel_left, 0.04, 6, Color(22, 14, 18, 235))
    draw_rectangle_rounded_lines(panel_left, 0.04, 6, Color(70, 20, 25, 255))

    draw_text("SETTINGS", 40, 42, 19, Color(255, 215, 60, 255))
    draw_text("World settings & dimensions", 40, 65, 13, Color(200, 200, 200, 255))
    draw_line(40, 84, 350, 84, Color(90, 30, 35, 255))

    # Sliders for world dimensions
    slider_ancho.draw()
    slider_largo.draw()
    slider_fuertes.draw()

    # Button to recreate world (also triggered by key N)
    btn_recreate = Rectangle(40, 226, 310, 26)
    if draw_ui_button(btn_recreate, "Recreate World [N]", Color(140, 35, 45, 255), Color(180, 45, 60, 255), WHITE, 13):
        setup_world(slider_ancho.val, slider_largo.val, slider_fuertes.val)
        slider_casillas_fuerte.max_val = get_proportional_capacity()
        slider_casillas_fuerte.val = 1
        if music_enabled:
            play_sound(snd_reset)
        status_message = "World recreated with new dimensions [N]."

    # Option 1: Spawn Placement Mode Toggle Button (E)
    btn_placement = Rectangle(40, 258, 310, 28)
    place_label = "LOCK SPAWNS & START [E]" if placement_mode else "Edit Spawn Points [E]"
    place_bg = Color(190, 135, 20, 255) if placement_mode else Color(75, 45, 115, 255)
    place_hover = Color(225, 165, 30, 255) if placement_mode else Color(105, 65, 155, 255)
    if draw_ui_button(btn_placement, place_label, place_bg, place_hover, WHITE, 13):
        placement_mode = not placement_mode
        if placement_mode:
            auto_play = False
            reset_to_initial()
            if music_enabled:
                play_sound(snd_place)
            status_message = f"Placement Mode ON: Click grid cell to place Fort {forts[selected_spawn_fort_idx].faction}."
        else:
            if music_enabled:
                play_sound(snd_reset)
            status_message = "Initial spawns locked! Ready. Press '+' to expand."

    # Fort Selection Badges Ribbon (1 click or keys 1-8 to choose active fort)
    num_f = len(forts)
    mouse_pos = get_virtual_mouse_position()
    if num_f > 4:
        cols = 4
        gap_x = 6
        gap_y = 6
        badge_w = (310 - (cols - 1) * gap_x) / cols
        badge_h = 22
        for i, f in enumerate(forts):
            col_idx = i % cols
            row_idx = i // cols
            bx = int(40 + col_idx * (badge_w + gap_x))
            by = int(294 + row_idx * (badge_h + gap_y))
            brect = Rectangle(bx, by, badge_w, badge_h)
            f_col = FACTION_COLORS[(f.faction - 1) % len(FACTION_COLORS)]
            is_sel = (i == selected_spawn_fort_idx)
            
            hvd = check_collision_point_rec(mouse_pos, brect)
            draw_rectangle_rounded(brect, 0.3, 4, f_col)
            border_col = Color(255, 235, 120, 255) if is_sel else (WHITE if hvd else BLACK)
            draw_rectangle_rounded_lines(brect, 0.3, 4, border_col)
            
            btxt = f"Fort {f.faction}"
            tw = measure_text(btxt, 11)
            draw_text(btxt, int(brect.x + (brect.width - tw) / 2), int(brect.y + 5), 11, BLACK)
            
            if is_sel:
                draw_circle(int(brect.x + 8), int(brect.y + 11), 3, WHITE)
                draw_circle_lines(int(brect.x + 8), int(brect.y + 11), 3, BLACK)
                
            if hvd and is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
                selected_spawn_fort_idx = i
                status_message = f"Selected Fort {f.faction} for spawn placement."
    else:
        badge_gap = 6
        badge_w = (310 - (num_f - 1) * badge_gap) / max(1, num_f)
        for i, f in enumerate(forts):
            bx = int(40 + i * (badge_w + badge_gap))
            brect = Rectangle(bx, 302, badge_w, 24)
            f_col = FACTION_COLORS[(f.faction - 1) % len(FACTION_COLORS)]
            is_sel = (i == selected_spawn_fort_idx)
            
            hvd = check_collision_point_rec(mouse_pos, brect)
            draw_rectangle_rounded(brect, 0.3, 4, f_col)
            border_col = Color(255, 235, 120, 255) if is_sel else (WHITE if hvd else BLACK)
            draw_rectangle_rounded_lines(brect, 0.3, 4, border_col)
            
            btxt = f"Fort {f.faction}"
            tw = measure_text(btxt, 12)
            draw_text(btxt, int(brect.x + (brect.width - tw) / 2), int(brect.y + 6), 12, BLACK)
            
            if is_sel:
                draw_circle(int(brect.x + 8), int(brect.y + 12), 3, WHITE)
                draw_circle_lines(int(brect.x + 8), int(brect.y + 12), 3, BLACK)
                
            if hvd and is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
                selected_spawn_fort_idx = i
                status_message = f"Selected Fort {f.faction} for spawn placement."

    # Randomize Spawns Button (G)
    btn_rand_spawns = Rectangle(40, 350, 310, 24)
    if draw_ui_button(btn_rand_spawns, "Randomize All Spawns [G]", Color(45, 50, 65, 255), Color(65, 75, 95, 255), Color(220, 220, 220, 255), 12):
        randomize_all_spawns()

    draw_line(40, 384, 350, 384, Color(90, 30, 35, 255))
    draw_text("CELL CAPACITY", 40, 396, 16, Color(255, 215, 60, 255))

    # Proportional cell target slider
    slider_casillas_fuerte.draw()

    # Button to apply target size across all forts
    btn_apply_size = Rectangle(40, 466, 310, 26)
    if draw_ui_button(btn_apply_size, "Apply Target to Forts", Color(45, 85, 155, 255), Color(60, 110, 190, 255), WHITE, 13):
        if not placement_mode:
            target = slider_casillas_fuerte.val
            while any(len(f.fort_squares) < target for f in forts):
                if not step_forward():
                    break
            while any(len(f.fort_squares) > target for f in forts):
                if not step_backward():
                    break
        else:
            status_message = "Lock spawns first [E] before applying targets!"

    draw_line(40, 502, 350, 502, Color(90, 30, 35, 255))
    draw_text("TURN ACTIONS", 40, 514, 16, Color(255, 215, 60, 255))

    # Buttons + and -
    btn_plus = Rectangle(40, 536, 150, 34)
    if draw_ui_button(btn_plus, "+ Expand (+)", Color(40, 140, 70, 255), Color(50, 175, 90, 255), WHITE, 14):
        if not placement_mode:
            step_forward()
        else:
            status_message = "Press 'E' to lock spawns and begin expansion!"

    btn_minus = Rectangle(200, 536, 150, 34)
    if draw_ui_button(btn_minus, "- Shrink (-)", Color(170, 80, 20, 255), Color(210, 100, 25, 255), WHITE, 14):
        if not placement_mode:
            step_backward()
        else:
            status_message = "Press 'E' to lock spawns and begin expansion!"

    # Reset button (R)
    btn_reset = Rectangle(40, 576, 310, 30)
    if draw_ui_button(btn_reset, "Reset to Initial (R)", Color(130, 30, 30, 255), Color(170, 40, 40, 255), WHITE, 13):
        reset_to_initial()
        slider_casillas_fuerte.val = 1

    # Auto-play button (Space)
    btn_auto = Rectangle(40, 612, 310, 30)
    auto_label = "Pause Auto (Space)" if auto_play else "Auto-Expand (Space)"
    auto_bg = Color(160, 120, 20, 255) if auto_play else Color(60, 55, 65, 255)
    if draw_ui_button(btn_auto, auto_label, auto_bg, Color(190, 145, 25, 255), WHITE, 13):
        if not placement_mode:
            auto_play = not auto_play
        else:
            status_message = "Press 'E' to lock spawns and begin auto-expansion!"

    # --------------------------------------------------------------------------
    # Top Panel: Title and Status
    # --------------------------------------------------------------------------
    panel_top = Rectangle(395, 25, 490, 75)
    draw_rectangle_rounded(panel_top, 0.15, 6, Color(22, 14, 18, 235))
    draw_rectangle_rounded_lines(panel_top, 0.15, 6, Color(70, 20, 25, 255))

    # Interactive Fullscreen button (F11)
    btn_fs = Rectangle(815, 34, 58, 24)
    fs_txt = "WIN" if is_window_fullscreen() else "FULL [F11]"
    fs_bg = Color(50, 95, 130, 255) if is_window_fullscreen() else Color(45, 40, 55, 255)
    if draw_ui_button(btn_fs, fs_txt, fs_bg, Color(70, 120, 165, 255), WHITE, 10):
        toggle_fullscreen()
        if not is_window_fullscreen():
            set_window_size(SCREEN_WIDTH, SCREEN_HEIGHT)

    active_spawn_color = FACTION_COLORS[(forts[selected_spawn_fort_idx].faction - 1) % len(FACTION_COLORS)]
    if placement_mode:
        title_text = f"SPAWN PLACEMENT: FORT {forts[selected_spawn_fort_idx].faction}"
        t_w = measure_text(title_text, 22)
        draw_text(title_text, int(panel_top.x + (panel_top.width - t_w) / 2), 36, 22, active_spawn_color)

        sub_text = "Click empty cell to place spawn | [E] Lock Spawns | [G] Random"
        sub_w = measure_text(sub_text, 13)
        draw_text(sub_text, int(panel_top.x + (panel_top.width - sub_w) / 2), 68, 13, Color(245, 245, 245, 255))
    else:
        title_text = "WORLD CORRUPTION"
        t_w = measure_text(title_text, 26)
        draw_text(title_text, int(panel_top.x + (panel_top.width - t_w) / 2), 38, 26, Color(255, 215, 60, 255))

        sub_w = measure_text(status_message, 13)
        draw_text(status_message, int(panel_top.x + (panel_top.width - sub_w) / 2), 70, 13, Color(220, 220, 220, 255))

    # --------------------------------------------------------------------------
    # Center 480 * 480 Grid
    # --------------------------------------------------------------------------
    # Clean white background for vibrant circle contrast
    draw_rectangle(GRID_X, GRID_Y, GRID_SIZE, GRID_SIZE, Color(252, 252, 255, 255))

    cell_w = GRID_SIZE / world_w
    cell_h = GRID_SIZE / world_h

    # Check mouse hover on central grid
    hover_col = -1
    hover_row = -1
    grid_hovered = (GRID_X <= mouse_pos.x < GRID_X + GRID_SIZE and GRID_Y <= mouse_pos.y < GRID_Y + GRID_SIZE)
    if grid_hovered:
        hover_col = int((mouse_pos.x - GRID_X) // cell_w)
        hover_row = int((mouse_pos.y - GRID_Y) // cell_h)
        hover_col = max(0, min(world_w - 1, hover_col))
        hover_row = max(0, min(world_h - 1, hover_row))

        # Handle direct cell click in placement mode
        if placement_mode and is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            target_f = forts[selected_spawn_fort_idx]
            occ_val = world[hover_row][hover_col]
            if occ_val == 0 or occ_val == target_f.faction:
                if place_initial_fort(selected_spawn_fort_idx, hover_col, hover_row):
                    if music_enabled:
                        play_sound(snd_place)
                    next_idx = (selected_spawn_fort_idx + 1) % len(forts)
                    status_message = f"Fort {target_f.faction} placed at ({hover_col}, {hover_row}). Next: Fort {forts[next_idx].faction}."
                    selected_spawn_fort_idx = next_idx
            else:
                if music_enabled:
                    play_sound(snd_shrink)
                status_message = f"Cell ({hover_col}, {hover_row}) occupied by Fort {occ_val}! Pick an empty cell."

    # Draw colored circles for occupied cells
    for y in range(world_h):
        for x in range(world_w):
            faction = world[y][x]
            if faction > 0:
                color_idx = (faction - 1) % len(FACTION_COLORS)
                f_color = FACTION_COLORS[color_idx]
                
                cx = int(GRID_X + (x + 0.5) * cell_w)
                cy = int(GRID_Y + (y + 0.5) * cell_h)
                rad = max(2, int(min(cell_w, cell_h) * 0.40))
                
                # Fort circle
                draw_circle(cx, cy, rad, f_color)
                draw_circle_lines(cx, cy, rad, Color(20, 20, 20, 190))

                # Highlight initial spawn nucleus with white dot
                f_obj = next((f for f in forts if f.faction == faction), None)
                if f_obj and f_obj.fort_squares and f_obj.fort_squares[0]["x"] == x and f_obj.fort_squares[0]["y"] == y:
                    dot_rad = max(1, rad // 3)
                    draw_circle(cx, cy, dot_rad, WHITE)
                    draw_circle_lines(cx, cy, dot_rad, BLACK)

    # In placement mode: render hover cell wash and translucent ghost circle
    if placement_mode and grid_hovered and hover_col >= 0 and hover_row >= 0:
        hx = int(GRID_X + hover_col * cell_w)
        hy = int(GRID_Y + hover_row * cell_h)
        draw_rectangle(hx, hy, int(cell_w), int(cell_h), Color(active_spawn_color.r, active_spawn_color.g, active_spawn_color.b, 65))
        
        gcx = int(GRID_X + (hover_col + 0.5) * cell_w)
        gcy = int(GRID_Y + (hover_row + 0.5) * cell_h)
        grad = max(2, int(min(cell_w, cell_h) * 0.40))
        draw_circle(gcx, gcy, grad, Color(active_spawn_color.r, active_spawn_color.g, active_spawn_color.b, 175))
        draw_circle_lines(gcx, gcy, grad, WHITE)
        draw_circle(gcx, gcy, max(1, grad // 3), WHITE)

        # Coordinate tooltip
        tip = f"Place Fort {forts[selected_spawn_fort_idx].faction} ({hover_col}, {hover_row})"
        tip_w = measure_text(tip, 12)
        tip_x = max(GRID_X + 10, min(GRID_X + GRID_SIZE - tip_w - 12, gcx - tip_w // 2))
        tip_y = max(GRID_Y + 8, gcy - grad - 22)
        draw_rectangle_rounded(Rectangle(tip_x - 6, tip_y - 2, tip_w + 12, 18), 0.3, 4, Color(15, 12, 20, 235))
        draw_rectangle_rounded_lines(Rectangle(tip_x - 6, tip_y - 2, tip_w + 12, 18), 0.3, 4, active_spawn_color)
        draw_text(tip, tip_x, tip_y + 1, 12, WHITE)

    # Black grid lines
    for col in range(world_w + 1):
        lx = int(GRID_X + col * cell_w)
        draw_line(lx, GRID_Y, lx, GRID_Y + GRID_SIZE, BLACK)

    for row in range(world_h + 1):
        ly = int(GRID_Y + row * cell_h)
        draw_line(GRID_X, ly, GRID_X + GRID_SIZE, ly, BLACK)

    # Grid outer border (glows with active fort color during placement mode)
    if placement_mode:
        draw_rectangle_lines_ex(Rectangle(GRID_X, GRID_Y, GRID_SIZE, GRID_SIZE), 3.0, active_spawn_color)
    else:
        draw_rectangle_lines_ex(Rectangle(GRID_X, GRID_Y, GRID_SIZE, GRID_SIZE), 3.0, BLACK)

    # --------------------------------------------------------------------------
    # Bottom Panel: Quick Keyboard Shortcuts
    # --------------------------------------------------------------------------
    panel_bot = Rectangle(395, 620, 490, 75)
    draw_rectangle_rounded(panel_bot, 0.15, 6, Color(22, 14, 18, 235))
    draw_rectangle_rounded_lines(panel_bot, 0.15, 6, Color(70, 20, 25, 255))

    draw_text("Keyboard Shortcuts:", 415, 632, 14, Color(255, 215, 60, 255))
    draw_text("[+] Expand | [-] Shrink | [R] Reset | [N] Recreate | [E] Spawns", 415, 650, 13, WHITE)
    draw_text("[1-8] Pick Fort | [G] Random Spawns | [F11] Fullscreen | [Space] Auto | [M] Mute", 415, 668, 12, Color(200, 200, 200, 255))

    # --------------------------------------------------------------------------
    # Right Panel: Forts Status, Statistics & Audio Controls
    # --------------------------------------------------------------------------
    panel_right = Rectangle(910, 25, 345, 670)
    draw_rectangle_rounded(panel_right, 0.04, 6, Color(22, 14, 18, 235))
    draw_rectangle_rounded_lines(panel_right, 0.04, 6, Color(70, 20, 25, 255))

    draw_text("FORTS STATUS", 925, 42, 18, Color(255, 215, 60, 255))
    draw_text("Cyclic expansion monitor", 925, 63, 12, Color(200, 200, 200, 255))
    draw_line(925, 80, 1235, 80, Color(90, 30, 35, 255))

    # Current turn badge with active fort's faction color
    if forts:
        active_fort = forts[current_turn_idx % len(forts)]
        act_col = FACTION_COLORS[(active_fort.faction - 1) % len(FACTION_COLORS)]
        
        turn_box = Rectangle(925, 88, 315, 28)
        draw_rectangle_rounded(turn_box, 0.25, 4, act_col)
        draw_rectangle_rounded_lines(turn_box, 0.25, 4, BLACK)
        
        turn_text = f"NEXT TURN (+): FORT {active_fort.faction}"
        t_w = measure_text(turn_text, 13)
        draw_text(turn_text, int(turn_box.x + (turn_box.width - t_w) / 2), 95, 13, BLACK)

    # Individual fort rows (dynamically fitted for 2 to 8 forts without overlap)
    y_entry = 124
    total_cells = world_w * world_h
    occupied_cells = sum(len(f.fort_squares) for f in forts)
    row_step = 27 if len(forts) > 6 else (32 if len(forts) > 4 else 42)
    bar_h = 5 if len(forts) > 6 else (6 if len(forts) > 4 else 7)

    for idx, f in enumerate(forts):
        f_col = FACTION_COLORS[(f.faction - 1) % len(FACTION_COLORS)]
        count = len(f.fort_squares)
        pct = (count / total_cells) * 100.0

        # Color dot indicator
        draw_circle(938, y_entry + 8, 6, f_col)
        draw_circle_lines(938, y_entry + 8, 6, WHITE)

        # Name and count
        is_turn = (idx == current_turn_idx % len(forts))
        prefix = "-> " if is_turn else "   "
        draw_text(f"{prefix}Fort {f.faction}:", 948, y_entry + 1, 13, Color(255, 235, 120, 255) if is_turn else WHITE)
        count_str = f"{count} ({pct:.1f}%)"
        c_w = measure_text(count_str, 12)
        draw_text(count_str, 1235 - c_w, y_entry + 2, 12, Color(210, 210, 210, 255))

        # Territory proportion bar
        bar_y = y_entry + 17
        bar_bg = Rectangle(948, bar_y, 285, bar_h)
        draw_rectangle_rounded(bar_bg, 0.5, 3, Color(45, 40, 50, 255))
        bar_w = max(0.0, (count / total_cells) * 285)
        if bar_w > 0:
            bar_fill = Rectangle(948, bar_y, bar_w, bar_h)
            draw_rectangle_rounded(bar_fill, 0.5, 3, f_col)

        y_entry += row_step

    stat_y_start = 356
    draw_line(925, stat_y_start, 1235, stat_y_start, Color(90, 30, 35, 255))
    draw_text("WORLD STATISTICS", 925, stat_y_start + 10, 15, Color(255, 215, 60, 255))

    empty_cells = total_cells - occupied_cells
    occ_pct = (occupied_cells / total_cells) * 100.0
    s_y = stat_y_start + 32
    draw_text(f"Dimensions: {world_w} x {world_h} ({total_cells} cells)", 925, s_y, 13, WHITE)
    draw_text(f"Occupied: {occupied_cells} ({occ_pct:.1f}%)", 925, s_y + 19, 13, Color(100, 230, 120, 255))
    draw_text(f"Free Cells: {empty_cells}", 925, s_y + 38, 13, Color(255, 180, 80, 255))
    draw_text(f"History Steps: {len(expansion_history)}", 925, s_y + 57, 13, Color(200, 200, 255, 255))

    # Audio controls and logarithmic volume slider
    audio_y = 480
    draw_line(925, audio_y, 1235, audio_y, Color(90, 30, 35, 255))
    draw_text("AUDIO & VOLUME", 925, audio_y + 10, 15, Color(255, 215, 60, 255))

    # Mute / Unmute button
    music_status_txt = "Synth Music: [ ACTIVE ]" if music_enabled else "Synth Music: [ MUTED ]"
    btn_music = Rectangle(925, audio_y + 32, 315, 30)
    music_btn_col = Color(35, 100, 120, 255) if music_enabled else Color(80, 50, 60, 255)
    if draw_ui_button(btn_music, music_status_txt, music_btn_col, Color(50, 130, 160, 255), WHITE, 13):
        music_enabled = not music_enabled
        if music_enabled:
            resume_music_stream(bgm_stream)
            vol_norm = slider_volumen.val / 100.0
            set_music_volume(bgm_stream, math.pow(vol_norm, 1.4) if vol_norm > 0 else 0.0)
        else:
            pause_music_stream(bgm_stream)

    # Logarithmic volume slider
    slider_volumen.draw()

    end_texture_mode()

    # --------------------------------------------------------------------------
    # Outer Screen Presentation with Proportional Scaling & FPS
    # --------------------------------------------------------------------------
    begin_drawing()
    clear_background(Color(18, 12, 16, 255))

    sw = get_screen_width()
    sh = get_screen_height()
    scale = min(sw / SCREEN_WIDTH, sh / SCREEN_HEIGHT)
    ox = (sw - SCREEN_WIDTH * scale) / 2.0
    oy = (sh - SCREEN_HEIGHT * scale) / 2.0

    # Draw scaled virtual canvas
    draw_texture_pro(
        target_render.texture,
        Rectangle(0, 0, SCREEN_WIDTH, -SCREEN_HEIGHT),
        Rectangle(ox, oy, SCREEN_WIDTH * scale, SCREEN_HEIGHT * scale),
        Vector2(0, 0),
        0.0,
        WHITE
    )

    # Yellow FPS indicator in the top-left corner
    fps_val = get_fps()
    fps_str = f"FPS: {fps_val}"
    fps_w = measure_text(fps_str, 15)
    fps_box = Rectangle(10, 3, fps_w + 14, 19)
    draw_rectangle_rounded(fps_box, 0.4, 4, Color(15, 12, 18, 220))
    draw_rectangle_rounded_lines(fps_box, 0.4, 4, Color(80, 25, 30, 220))
    draw_text(fps_str, 17, 5, 15, Color(255, 225, 0, 255))

    end_drawing()

# ==============================================================================
# RESOURCE CLEANUP
# ==============================================================================

stop_music_stream(bgm_stream)
unload_music_stream(bgm_stream)
unload_sound(snd_expand)
unload_sound(snd_shrink)
unload_sound(snd_reset)
unload_sound(snd_place)
close_audio_device()
unload_render_texture(target_render)
close_window()
