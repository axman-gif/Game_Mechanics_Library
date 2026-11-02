# -*- coding: utf-8 -*-
"""
Procedural Audio Sound Player & Interactive Synth Workstation
============================================================
Location         : assets/audio/sound_player.py
Component        : Audio Showcase, Telemetry & Interactive Jukebox
Dimension        : 2D Graphical User Interface

Problem Solved:
  Procedural audio synthesizers generate sounds purely from mathematical formulas in memory
  without external asset files (.wav/.mp3). Without a dedicated tactile testing tool, developers
  and sound designers cannot preview, compare, inspect sample envelopes, or calibrate playback
  volumes and loop boundaries in isolation without launching complex minigames.

How the Player Works:
  1. Dual Soundboard & Jukebox Architecture:
     - Master View Tabs: [SOUND EFFECTS (48)] and [MUSIC SOUNDTRACKS (12)]
     - Plays procedural sound effects and background music simultaneously to test audio balance.
  2. 12 Procedural BGM Soundtracks:
     - Action / Combat (126 BPM, 8-bar Dm progression)
     - Ambient Exploration (84 BPM, 4-bar Am9 pad)
     - Boss Encounter (140 BPM, 8-bar Cm syncopated drive)
     - Stealth & Suspense (96 BPM, 8-bar Dm heartbeat groove)
     - Retro Arcade (132 BPM, 8-bar NES-style chiptune)
     - Victory / Shop (116 BPM, 8-bar G major organ & chimes)
     - Cyberpunk Synthwave (136 BPM, 8-bar Em rolling 16th bass & PWM neon lead)
     - Dark Dungeon Crypt (92 BPM, 8-bar E Phrygian pedal drone & harpsichord)
     - Puzzle & Logic Lab (104 BPM, 8-bar C Lydian plucked bass, FM Rhodes & marimba)
     - High-Octane Racing (152 BPM, 8-bar Am octave-jumping bass & breakbeat)
     - Fantasy Tavern (112 BPM, 8-bar D Dorian folk oom-pah bass, lute & wooden flute)
     - Cosmic Mystery (88 BPM, 8-bar F#m9 LFO sub swell, glass pad & delay plucks)
  3. Real-Time Oscilloscope & Spectrum Visualizer:
     Animates a 16-band reactive frequency equalizer with peak-hold caps and a continuous
     CRT oscilloscope waveform responding dynamically to SFX triggers and BGM beats.
  4. Audio Gain Mixer & Sliders:
     Provides interactive Master, SFX, and BGM volume controls with instantaneous gain scaling.
  5. X-Ray Telemetry Overlay ([Tab]):
     Inspects audio device configuration, sampling rates, memory footprint, and C++ audio pipeline notes.

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - Q / E / Gamepad LB / RB              : Switch View [SOUND EFFECTS] vs [MUSIC SOUNDTRACKS]
  - Mouse Click / Drag / Wheel           : Click any SFX or Music card, scroll list, or drag faders
  - Up / Down / W / S / Left Stick / D-Pad: Navigate cards in active view
  - Space / Enter / Gamepad A (South)    : Play selected sound effect or toggle selected music track
  - 1, 2, 3, 4, 5                        : Filter SFX categories [ALL, COMBAT, MOVE, PROG, UI]
  - M / Gamepad X (West)                 : Toggle BGM Play / Pause
  - N / Gamepad Y (North)                : Next BGM Track
  - [ / ]                                : Decrease / Increase Master Volume
  - [Tab] / Gamepad View (Select)        : Toggle X-Ray Audio Telemetry Overlay
  - [F1]                                 : Toggle Visualizer Mode (Spectrum + Oscilloscope vs Raw Scope)
  - [Ctrl +/-]                           : Increase / Decrease UI Font Size
  - [F11]                                : Toggle Fullscreen
  - [R] / Gamepad Start                  : Stop all sounds & reset mixer
"""

import sys
import os
import math
import random

# 1. Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# 2. Add repository root to search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# 3. Mandatory Raylib & modular workspace imports
from pyray import *
from assets.audio.synth_sfx import SoundLibrary
from assets.audio.synth_music import (
    SynthMusicPlayer,
    generate_action_track,
    generate_ambient_track,
    generate_boss_track,
    generate_stealth_track,
    generate_retro_arcade_track,
    generate_victory_track,
    generate_cyberpunk_track,
    generate_dungeon_track,
    generate_puzzle_track,
    generate_racing_track,
    generate_tavern_track,
    generate_mystery_track
)
from utils import *

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WINDOW_TITLE = "Procedural Audio Synthesizer & Sound Player (Raylib Pattern Lab)"

# ==============================================================================
# PALETTE DEFINITIONS
# ==============================================================================
COLOR_BG_DARK           = Color(11, 14, 23, 255)
COLOR_PANEL_BG          = Color(17, 23, 38, 245)
COLOR_PANEL_BORDER      = Color(42, 60, 95, 255)
COLOR_PANEL_HEADER      = Color(24, 34, 56, 255)

COLOR_TEXT_MAIN         = Color(232, 240, 255, 255)
COLOR_TEXT_DIM          = Color(135, 155, 185, 255)
COLOR_TEXT_MUTED        = Color(85, 105, 135, 255)

COLOR_CYAN_ACCENT       = Color(0, 220, 255, 255)
COLOR_GOLD_ACCENT       = Color(255, 205, 50, 255)
COLOR_GREEN_ACCENT      = Color(60, 245, 130, 255)
COLOR_RED_ACCENT        = Color(255, 80, 80, 255)
COLOR_PURPLE_ACCENT     = Color(200, 100, 255, 255)

COLOR_CARD_BG           = Color(20, 28, 48, 255)
COLOR_CARD_HOVER        = Color(28, 40, 70, 255)
COLOR_CARD_SELECTED     = Color(32, 65, 115, 255)
COLOR_CARD_PLAYING      = Color(22, 54, 44, 255)

# View Modes
VIEW_SFX   = 0
VIEW_MUSIC = 1

# Category filter indices for SFX
CAT_ALL         = 0
CAT_COMBAT      = 1
CAT_MOVEMENT    = 2
CAT_PROGRESSION = 3
CAT_UI          = 4
CAT_COUNT       = 5

CAT_NAMES = ["ALL (48)", "COMBAT (16)", "MOVEMENT (10)", "PROGRESSION (11)", "UI (11)"]
CAT_KEYS  = ["ALL", "COMBAT", "MOVEMENT", "PROGRESSION", "UI"]

# ==============================================================================
# BLOCK 1: SFX & MUSIC METADATA
# ==============================================================================

# Complete catalog descriptor for each procedural sound in SoundLibrary (48 SFX)
SFX_CATALOG = [
    # Combat & Weapons (16)
    {"key": "laser",        "cat": "COMBAT",      "title": "Laser Blaster",  "desc": "900Hz -> 180Hz downward pitch slide",     "time": 0.12},
    {"key": "heavy_laser",  "cat": "COMBAT",      "title": "Heavy Laser",    "desc": "520Hz -> 60Hz power plasma cannon blast", "time": 0.25},
    {"key": "explosion",    "cat": "COMBAT",      "title": "Explosion",      "desc": "Filtered white noise with 65Hz rumble",   "time": 0.45},
    {"key": "hit",          "cat": "COMBAT",      "title": "Hit Impact",     "desc": "Punchy 280Hz exponential dive impact",     "time": 0.10},
    {"key": "parry",        "cat": "COMBAT",      "title": "Blade Parry",    "desc": "1760Hz/2640Hz metallic ring & long tail",  "time": 0.32},
    {"key": "shield_block", "cat": "COMBAT",      "title": "Shield Block",   "desc": "240Hz barrier impact with 65Hz sub thud",  "time": 0.18},
    {"key": "reload",       "cat": "COMBAT",      "title": "Gun Reload",     "desc": "3-stage latch pull, slide & chamber snap", "time": 0.22},
    {"key": "empty",        "cat": "COMBAT",      "title": "Dry Fire Click", "desc": "950Hz -> 400Hz hollow hammer click",      "time": 0.05},
    {"key": "shotgun",      "cat": "COMBAT",      "title": "Shotgun Pump",   "desc": "Scattergun sub-blast + 2-stage pump rack", "time": 0.34},
    {"key": "sniper",       "cat": "COMBAT",      "title": "Sniper Crack",   "desc": "2200Hz whip crack, barrel ring & echo",    "time": 0.42},
    {"key": "charge_up",    "cat": "COMBAT",      "title": "Charge Riser",   "desc": "160->1120Hz quadratic sweep + LFO pulse",  "time": 0.45},
    {"key": "sword_slash",  "cat": "COMBAT",      "title": "Sword Slash",    "desc": "Band-pass air cleave + steel edge whistle","time": 0.16},
    {"key": "critical_hit", "cat": "COMBAT",      "title": "Critical Hit",   "desc": "Sub-bass slam + G6/C7/G7 crystal shatter", "time": 0.28},
    {"key": "ricochet",     "cat": "COMBAT",      "title": "Bullet Ricochet","desc": "2600->580Hz metallic ping + 35Hz warble",  "time": 0.24},
    {"key": "flame",        "cat": "COMBAT",      "title": "Flame Burst",    "desc": "8Hz thermal draft noise + ember crackles", "time": 0.38},
    {"key": "freeze",       "cat": "COMBAT",      "title": "Frost Freeze",   "desc": "Inharmonic FM ice crystals & frost snap",  "time": 0.35},

    # Movement & Kinematics (10)
    {"key": "jump",         "cat": "MOVEMENT",    "title": "Jump Sweep",     "desc": "150Hz -> 600Hz 8-bit upward frequency",   "time": 0.14},
    {"key": "dash",         "cat": "MOVEMENT",    "title": "Dash Whoosh",    "desc": "Aerodynamic rushing air whoosh (300->60)", "time": 0.18},
    {"key": "footstep",     "cat": "MOVEMENT",    "title": "Footstep Tap",   "desc": "Subtle 120Hz floor tap with friction scuff","time": 0.07},
    {"key": "land",         "cat": "MOVEMENT",    "title": "Ground Land",    "desc": "160Hz -> 35Hz solid landing impact thud",  "time": 0.14},
    {"key": "double_jump",  "cat": "MOVEMENT",    "title": "Double Jump",    "desc": "2-stage mid-air kick + octave lift sweep", "time": 0.18},
    {"key": "grapple",      "cat": "MOVEMENT",    "title": "Grapple Hook",   "desc": "Pneumatic fire, 48Hz winch & claw clank",  "time": 0.30},
    {"key": "thruster",     "cat": "MOVEMENT",    "title": "Jet Thruster",   "desc": "72Hz rocket burn + 420->780Hz spool whine","time": 0.32},
    {"key": "teleport",     "cat": "MOVEMENT",    "title": "Quantum Blink",  "desc": "Vacuum implosion + ring-mod warp burst",   "time": 0.28},
    {"key": "slide",        "cat": "MOVEMENT",    "title": "Kinetic Slide",  "desc": "Dual-pole surface scrape + scuff decay",   "time": 0.24},
    {"key": "bounce",       "cat": "MOVEMENT",    "title": "Spring Bounce",  "desc": "180->440Hz elastic boing + 24Hz wobble",   "time": 0.22},

    # Progression, Rewards & Health (11)
    {"key": "coin",         "cat": "PROGRESSION", "title": "Coin Pickup",    "desc": "Bright 2-tone melodic chime (B5 to E6)",   "time": 0.16},
    {"key": "powerup",      "cat": "PROGRESSION", "title": "Powerup Fanfare","desc": "Rising 4-tone victory arpeggio (E4 to E5)","time": 0.32},
    {"key": "level_up",     "cat": "PROGRESSION", "title": "Level Up",       "desc": "5-note pentatonic major chime (C5 to C6)", "time": 0.48},
    {"key": "heal",         "cat": "PROGRESSION", "title": "Heal Restore",   "desc": "380Hz -> 740Hz shimmer with 10Hz vibrato", "time": 0.32},
    {"key": "hurt",         "cat": "PROGRESSION", "title": "Hurt Groan",     "desc": "180Hz -> 70Hz groaning dive with grit",    "time": 0.15},
    {"key": "chest_open",   "cat": "PROGRESSION", "title": "Chest Unlock",   "desc": "Iron lock unlatch + 4-note Lydian reveal", "time": 0.46},
    {"key": "craft",        "cat": "PROGRESSION", "title": "Anvil Craft",    "desc": "Double forge hammer ring + harmonic glow", "time": 0.36},
    {"key": "debuff",       "cat": "PROGRESSION", "title": "Curse Debuff",   "desc": "Descending tritone steps (A4->Eb4->A3)",   "time": 0.28},
    {"key": "gem",          "cat": "PROGRESSION", "title": "Crystal Gem",    "desc": "High-octave C6-G6-C7 glassy FM sparkle",   "time": 0.24},
    {"key": "revive",       "cat": "PROGRESSION", "title": "Revive Swell",   "desc": "F-major organ triad swell + 6Hz shimmer",  "time": 0.50},
    {"key": "death",        "cat": "PROGRESSION", "title": "Defeat Drop",    "desc": "4-step minor cascade + sub power-down",    "time": 0.45},

    # UI & Feedback (11)
    {"key": "click",        "cat": "UI",          "title": "UI Click",       "desc": "Clean 1200Hz standard button blip",        "time": 0.04},
    {"key": "select",       "cat": "UI",          "title": "Cursor Hover",   "desc": "Ultra-soft 1750Hz sine hover tick (30ms)", "time": 0.03},
    {"key": "cancel",       "cat": "UI",          "title": "Cancel / Back",  "desc": "Soft descending 2-tone blip (740->494Hz)", "time": 0.12},
    {"key": "error",        "cat": "UI",          "title": "Error Buzzer",   "desc": "Harsh 125Hz/133Hz dissonant 8Hz beat",     "time": 0.20},
    {"key": "alert",        "cat": "UI",          "title": "Alert Siren",    "desc": "880Hz -> 1318Hz 2-pulse exclamation",      "time": 0.22},
    {"key": "confirm",      "cat": "UI",          "title": "UI Confirm",     "desc": "Crisp E5 -> B5 ascending fifth chime",     "time": 0.12},
    {"key": "pause",        "cat": "UI",          "title": "Pause Stinger",  "desc": "Classic C6-G5-E5-C6 staccato menu jingle", "time": 0.18},
    {"key": "typewriter",   "cat": "UI",          "title": "Typewriter Pop", "desc": "25ms warm keystroke & dialogue speech blip","time": 0.025},
    {"key": "notification", "cat": "UI",          "title": "Toast Chime",    "desc": "Dual-bell A5 -> D6 achievement/quest pop", "time": 0.24},
    {"key": "sonar_ping",   "cat": "UI",          "title": "Sonar Ping",     "desc": "1480Hz radar ping + secondary echo tap",   "time": 0.34},
    {"key": "countdown",    "cat": "UI",          "title": "Countdown Beep", "desc": "Punchy 880Hz arcade race/timer beep",      "time": 0.10},
]


def get_category_color(cat: str) -> Color:
    """Returns a standardized palette accent based on sound category."""
    if cat == "COMBAT":
        return COLOR_RED_ACCENT
    if cat == "MOVEMENT":
        return COLOR_CYAN_ACCENT
    if cat == "PROGRESSION":
        return COLOR_GOLD_ACCENT
    if cat == "UI":
        return COLOR_PURPLE_ACCENT
    return COLOR_TEXT_MAIN


# ==============================================================================
# BLOCK 2: INTERACTIVE AUDIO WORKSTATION STATE
# ==============================================================================

class SoundPlayerState:
    """
    Encapsulates all interactive state, audio library handles, BGM streaming,
    visualizer telemetry, and UI layout metrics.
    """
    def __init__(self):
        # Sound Effects Library (48 procedural sounds)
        self.sfx = SoundLibrary()
        self.sfx.init_defaults()

        # Pre-synthesize all 12 procedural soundtrack modes
        self.music = SynthMusicPlayer()
        self.action_track = generate_action_track(bpm=126.0)
        self.ambient_track = generate_ambient_track(bpm=84.0)
        self.boss_track = generate_boss_track(bpm=140.0)
        self.stealth_track = generate_stealth_track(bpm=96.0)
        self.arcade_track = generate_retro_arcade_track(bpm=132.0)
        self.victory_track = generate_victory_track(bpm=116.0)
        self.cyberpunk_track = generate_cyberpunk_track(bpm=136.0)
        self.dungeon_track = generate_dungeon_track(bpm=92.0)
        self.puzzle_track = generate_puzzle_track(bpm=104.0)
        self.racing_track = generate_racing_track(bpm=152.0)
        self.tavern_track = generate_tavern_track(bpm=112.0)
        self.mystery_track = generate_mystery_track(bpm=88.0)

        self.music_tracks = [
            {
                "title": "Action / Combat Loop",
                "bpm": 126.0,
                "bars": 8,
                "key": "D Minor",
                "progression": "Dm - Bb - F - C - Dm - Bb - Gm - A7",
                "instrumentation": "Driving 4-on-floor bass, chord pads & 16th-note arpeggios",
                "sound": self.action_track,
                "duration": (60.0 / 126.0) * 4.0 * 8,
            },
            {
                "title": "Ambient Exploration Loop",
                "bpm": 84.0,
                "bars": 4,
                "key": "A Minor 9",
                "progression": "Am9 - Fmaj7 - Cmaj7 - Em",
                "instrumentation": "Slow sinusoidal chord pads with chorus detune & sub drone",
                "sound": self.ambient_track,
                "duration": (60.0 / 84.0) * 4.0 * 4,
            },
            {
                "title": "Boss Encounter Loop",
                "bpm": 140.0,
                "bars": 8,
                "key": "C Minor",
                "progression": "Cm - Ab - Fm - G7 - Cm - Ab - Ddim - G7",
                "instrumentation": "Syncopated 8th saw bass, brassy minor pads & aggressive arpeggios",
                "sound": self.boss_track,
                "duration": (60.0 / 140.0) * 4.0 * 8,
            },
            {
                "title": "Stealth & Suspense Loop",
                "bpm": 96.0,
                "bars": 8,
                "key": "D Minor Modal",
                "progression": "Dm - Dm9 - Bb/D - A7/C# - Dm - Ddim - Bb - A7",
                "instrumentation": "Heartbeat sub-bass pulse, ticking 16th hi-hats & eerie pads",
                "sound": self.stealth_track,
                "duration": (60.0 / 96.0) * 4.0 * 8,
            },
            {
                "title": "Retro Arcade Chiptune",
                "bpm": 132.0,
                "bars": 8,
                "key": "F / C Major",
                "progression": "F - G - Em - Am - Dm - G7 - C - C6",
                "instrumentation": "Bouncy walking triangle bass & catchy 8-bit square wave lead",
                "sound": self.arcade_track,
                "duration": (60.0 / 132.0) * 4.0 * 8,
            },
            {
                "title": "Victory / Merchant Shop",
                "bpm": 116.0,
                "bars": 8,
                "key": "G Major",
                "progression": "G - D - Em - C - G - D - C - G",
                "instrumentation": "Warm organ bass, lush chord pads & sparkling bell chimes",
                "sound": self.victory_track,
                "duration": (60.0 / 116.0) * 4.0 * 8,
            },
            {
                "title": "Cyberpunk Synthwave Drive",
                "bpm": 136.0,
                "bars": 8,
                "key": "E Minor",
                "progression": "Em - C - G - D - Em - C - Am - B7",
                "instrumentation": "Rolling 16th ducking saw bass, kick/snare & PWM neon lead",
                "sound": self.cyberpunk_track,
                "duration": (60.0 / 136.0) * 4.0 * 8,
            },
            {
                "title": "Dark Dungeon / Crypt Crawl",
                "bpm": 92.0,
                "bars": 8,
                "key": "E Phrygian",
                "progression": "Em - Fmaj7 - Em - Dm - Am - Fmaj7 - Bm7b5 - B7",
                "instrumentation": "Cathedral pedal drone, harpsichord lute arps & ghost bells",
                "sound": self.dungeon_track,
                "duration": (60.0 / 92.0) * 4.0 * 8,
            },
            {
                "title": "Puzzle & Logic Lab",
                "bpm": 104.0,
                "bars": 8,
                "key": "C Lydian / Maj7",
                "progression": "Cmaj7 - D7 - Bm7 - Em7 - Am7 - D7 - Gmaj7 - G7",
                "instrumentation": "Plucked upright bass, FM Rhodes piano & syncopated marimba",
                "sound": self.puzzle_track,
                "duration": (60.0 / 104.0) * 4.0 * 8,
            },
            {
                "title": "High-Octane Turbo Racing",
                "bpm": 152.0,
                "bars": 8,
                "key": "A Minor",
                "progression": "Am - F - G - Em - Am - Dm - F - E7",
                "instrumentation": "Galloping octave-jumping bass, 16th breakbeat & saw-square lead",
                "sound": self.racing_track,
                "duration": (60.0 / 152.0) * 4.0 * 8,
            },
            {
                "title": "Fantasy Tavern / RPG Town",
                "bpm": 112.0,
                "bars": 8,
                "key": "D Dorian",
                "progression": "Dm - C - Dm - G - Dm - Am - Bb - A7",
                "instrumentation": "Bouncy oom-pah folk bass, strummed lute & wooden flute melody",
                "sound": self.tavern_track,
                "duration": (60.0 / 112.0) * 4.0 * 8,
            },
            {
                "title": "Cosmic Mystery / Space Drift",
                "bpm": 88.0,
                "bars": 8,
                "key": "F# Minor 9",
                "progression": "F#m9 - Dmaj7 - Bm7 - C#7 - F#m9 - Dmaj7 - Esus4 - C#7",
                "instrumentation": "LFO cosmic sub-bass, dual-detuned glass pad & delay echo plucks",
                "sound": self.mystery_track,
                "duration": (60.0 / 88.0) * 4.0 * 8,
            }
        ]

        # Active View Mode: VIEW_SFX or VIEW_MUSIC
        self.view_mode = VIEW_SFX

        # Active Track & Mixer Defaults
        self.active_track_idx = 0
        self.music.load_track(self.music_tracks[0]["sound"])

        self.master_volume = 0.85
        self.sfx_volume = 1.0
        self.bgm_volume = 0.60
        self.sfx_muted = False
        self.bgm_muted = False

        # Start with music actively playing so workstation is immediately live!
        effective_vol = self.master_volume * self.bgm_volume
        self.music.set_volume(effective_vol)
        self.music.play()
        self.music_playing = True
        self.track_elapsed = 0.0

        # SFX Selection & Filtering
        self.active_cat_idx = CAT_ALL
        self.selected_sfx_idx = 0
        self.scroll_y = 0.0
        self.max_scroll_y = 0.0
        self.filtered_sfx = list(SFX_CATALOG)

        # Music Track Selection & Scrolling (in VIEW_MUSIC)
        self.selected_music_idx = 0
        self.music_scroll_y = 0.0
        self.max_music_scroll_y = 0.0

        # Telemetry & Visualizer state
        self.last_played_key = "None"
        self.last_played_time = 0.0
        self.last_played_duration = 0.0
        self.card_flash_timers = [0.0] * len(SFX_CATALOG)
        self.scope_timer = 0.0

        # 16-Band Equalizer spectrum levels and peak-hold caps
        self.spectrum_bands = [0.0] * 16
        self.spectrum_peaks = [0.0] * 16

        # Toggles
        self.show_xray = False
        self.show_raw_scope = False

        # Gamepad input cooldowns
        self.pad_nav_cooldown = 0.0
        self.pad_tab_cooldown = 0.0

    def filter_by_category(self, cat_idx: int):
        """Switches active category tab and updates visible sound list."""
        self.active_cat_idx = cat_idx % CAT_COUNT
        key = CAT_KEYS[self.active_cat_idx]
        if key == "ALL":
            self.filtered_sfx = list(SFX_CATALOG)
        else:
            filtered = []
            for item in SFX_CATALOG:
                if item["cat"] == key:
                    filtered.append(item)
            self.filtered_sfx = filtered

        if self.selected_sfx_idx >= len(self.filtered_sfx):
            self.selected_sfx_idx = max(0, len(self.filtered_sfx) - 1)
        self.scroll_y = 0.0

    def play_sfx_by_key(self, key: str, duration: float = 0.15):
        """Triggers a sound effect with current volume multiplier and updates visualizer."""
        if self.sfx_muted:
            return

        effective_vol = self.master_volume * self.sfx_volume
        self.sfx.play(key, effective_vol)

        self.last_played_key = key
        self.last_played_duration = duration
        self.last_played_time = duration

        # Flash trigger card
        for i, item in enumerate(SFX_CATALOG):
            if item["key"] == key:
                self.card_flash_timers[i] = 0.35
                break

        # Stimulate visualizer spectrum bands based on sound type
        self._stimulate_spectrum_for_sfx(key)

    def _stimulate_spectrum_for_sfx(self, key: str):
        """Simulates harmonic spectrum impulses according to sound characteristics."""
        if key in ("explosion", "land", "shield_block", "hit", "shotgun", "critical_hit", "thruster", "death"):
            for b in range(0, 6):
                self.spectrum_bands[b] = min(1.0, self.spectrum_bands[b] + random.uniform(0.6, 0.95))
        elif key in ("laser", "heavy_laser", "dash", "sniper", "charge_up", "sword_slash", "flame", "slide", "teleport"):
            for b in range(3, 12):
                self.spectrum_bands[b] = min(1.0, self.spectrum_bands[b] + random.uniform(0.5, 0.88))
        elif key in ("parry", "coin", "level_up", "heal", "freeze", "gem", "chest_open", "craft", "revive", "sonar_ping"):
            for b in range(8, 16):
                self.spectrum_bands[b] = min(1.0, self.spectrum_bands[b] + random.uniform(0.6, 0.98))
        else:
            for b in range(5, 13):
                self.spectrum_bands[b] = min(1.0, self.spectrum_bands[b] + random.uniform(0.4, 0.78))

    def play_track_by_index(self, idx: int):
        """Plays or toggles a specific background music track by index."""
        target_idx = idx % len(self.music_tracks)
        if target_idx == self.active_track_idx and self.music_playing:
            # If already playing, stop playback
            self.music.stop()
            self.music_playing = False
        else:
            self.active_track_idx = target_idx
            track_info = self.music_tracks[self.active_track_idx]
            self.music.load_track(track_info["sound"])
            effective_vol = 0.0 if self.bgm_muted else (self.master_volume * self.bgm_volume)
            self.music.set_volume(effective_vol)
            self.music.play()
            self.music_playing = True
            self.track_elapsed = 0.0

    def toggle_bgm(self):
        """Toggles BGM playback on or off."""
        if self.music_playing:
            self.music.stop()
            self.music_playing = False
        else:
            effective_vol = 0.0 if self.bgm_muted else (self.master_volume * self.bgm_volume)
            self.music.set_volume(effective_vol)
            self.music.play()
            self.music_playing = True

    def next_bgm_track(self):
        """Cycles to next background soundtrack seamlessly."""
        self.active_track_idx = (self.active_track_idx + 1) % len(self.music_tracks)
        self.selected_music_idx = self.active_track_idx
        track_info = self.music_tracks[self.active_track_idx]
        self.music.load_track(track_info["sound"])
        effective_vol = 0.0 if self.bgm_muted else (self.master_volume * self.bgm_volume)
        self.music.set_volume(effective_vol)
        if self.music_playing:
            self.music.play()
        self.track_elapsed = 0.0

    def prev_bgm_track(self):
        """Cycles to previous background soundtrack."""
        self.active_track_idx = (self.active_track_idx - 1) % len(self.music_tracks)
        self.selected_music_idx = self.active_track_idx
        track_info = self.music_tracks[self.active_track_idx]
        self.music.load_track(track_info["sound"])
        effective_vol = 0.0 if self.bgm_muted else (self.master_volume * self.bgm_volume)
        self.music.set_volume(effective_vol)
        if self.music_playing:
            self.music.play()
        self.track_elapsed = 0.0

    def apply_bgm_volume(self):
        """Pushes master * BGM volume (or silence when BGM is muted) to the music stream."""
        effective_vol = 0.0 if self.bgm_muted else (self.master_volume * self.bgm_volume)
        self.music.set_volume(effective_vol)

    def update(self, dt: float):
        """Updates timers, audio streaming, sliders, and visualizer decay."""
        self.scope_timer += dt

        # Update BGM streaming and timeline
        if self.music_playing:
            self.music.update()
            track_info = self.music_tracks[self.active_track_idx]
            self.track_elapsed += dt
            if self.track_elapsed >= track_info["duration"]:
                self.track_elapsed = self.track_elapsed % track_info["duration"]

            # Rhythmic beat pulse into visualizer spectrum
            bpm = track_info["bpm"]
            beat_sec = 60.0 / bpm
            beat_phase = (self.track_elapsed % beat_sec) / beat_sec
            if beat_phase < 0.12:
                self.spectrum_bands[0] = max(self.spectrum_bands[0], 0.75 * (1.0 - beat_phase / 0.12))
                self.spectrum_bands[1] = max(self.spectrum_bands[1], 0.65 * (1.0 - beat_phase / 0.12))
                self.spectrum_bands[2] = max(self.spectrum_bands[2], 0.50 * (1.0 - beat_phase / 0.12))
            for b in range(3, 10):
                wave_val = 0.25 * math.sin(self.scope_timer * 6.0 + b * 0.4) + 0.25
                self.spectrum_bands[b] = max(self.spectrum_bands[b], wave_val * (self.bgm_volume if not self.bgm_muted else 0.0))

        # Decay spectrum bands and update peaks
        for b in range(16):
            self.spectrum_bands[b] = damp(self.spectrum_bands[b], 0.0, 7.5, dt)
            if self.spectrum_bands[b] > self.spectrum_peaks[b]:
                self.spectrum_peaks[b] = self.spectrum_bands[b]
            else:
                self.spectrum_peaks[b] = damp(self.spectrum_peaks[b], 0.0, 2.0, dt)

        # Decay card flash timers
        for i in range(len(self.card_flash_timers)):
            if self.card_flash_timers[i] > 0.0:
                self.card_flash_timers[i] = max(0.0, self.card_flash_timers[i] - dt)

        if self.last_played_time > 0.0:
            self.last_played_time = max(0.0, self.last_played_time - dt)

        # Handle navigation cooldowns
        if self.pad_nav_cooldown > 0.0:
            self.pad_nav_cooldown -= dt
        if self.pad_tab_cooldown > 0.0:
            self.pad_tab_cooldown -= dt

    def unload(self):
        """Disposes all audio buffers cleanly without memory leaks."""
        self.music.stop()
        for trk in self.music_tracks:
            snd = trk.get("sound")
            if snd:
                unload_sound(snd)
        self.music.current_sound = None
        self.music.is_playing = False
        self.sfx.unload_all()


# ==============================================================================
# BLOCK 3: RENDERING, OSCILLOSCOPE & USER INTERFACE
# ==============================================================================

def draw_header_title():
    """Draws workstation top header while preserving top-bar settings space."""
    draw_rectangle(0, 0, SCREEN_WIDTH, 52, COLOR_PANEL_HEADER)
    draw_line(0, 52, SCREEN_WIDTH, 52, COLOR_PANEL_BORDER)

    # Left Title
    draw_circle(24, 26, 8, COLOR_CYAN_ACCENT)
    draw_text("PROCEDURAL AUDIO WORKSTATION", 40, 16, 20, COLOR_TEXT_MAIN)
    draw_text("Raylib Synth SFX & BGM Jukebox", 370, 20, 12, COLOR_TEXT_DIM)


def draw_master_view_tabs(state: SoundPlayerState, panel_x: int, panel_y: int, panel_w: int, mouse_pos: Vector2, mouse_clicked: bool):
    """Renders the top view mode selector: [SOUND EFFECTS (48)] vs [MUSIC SOUNDTRACKS (12)]."""
    tab_w = (panel_w - 24) // 2
    tab_h = 36

    # Tab 0: SFX
    rec_sfx = Rectangle(float(panel_x + 10), float(panel_y + 10), float(tab_w), float(tab_h))
    is_hover_sfx = check_collision_point_rec(mouse_pos, rec_sfx)
    if is_hover_sfx and mouse_clicked:
        state.view_mode = VIEW_SFX
        state.sfx.play("select", 0.5)

    is_active_sfx = (state.view_mode == VIEW_SFX)
    bg_sfx = COLOR_CARD_SELECTED if is_active_sfx else (COLOR_CARD_HOVER if is_hover_sfx else COLOR_CARD_BG)
    border_sfx = COLOR_CYAN_ACCENT if is_active_sfx else COLOR_PANEL_BORDER

    draw_rectangle_rec(rec_sfx, bg_sfx)
    draw_rectangle_lines_ex(rec_sfx, 1.0, border_sfx)
    draw_text(f"SOUND EFFECTS ({len(SFX_CATALOG)})", panel_x + 95, panel_y + 20, 14, COLOR_TEXT_MAIN if is_active_sfx else COLOR_TEXT_DIM)

    # Tab 1: Music
    rec_mus = Rectangle(float(panel_x + 14 + tab_w), float(panel_y + 10), float(tab_w), float(tab_h))
    is_hover_mus = check_collision_point_rec(mouse_pos, rec_mus)
    if is_hover_mus and mouse_clicked:
        state.view_mode = VIEW_MUSIC
        state.sfx.play("select", 0.5)

    is_active_mus = (state.view_mode == VIEW_MUSIC)
    bg_mus = COLOR_CARD_SELECTED if is_active_mus else (COLOR_CARD_HOVER if is_hover_mus else COLOR_CARD_BG)
    border_mus = COLOR_GREEN_ACCENT if is_active_mus else COLOR_PANEL_BORDER

    draw_rectangle_rec(rec_mus, bg_mus)
    draw_rectangle_lines_ex(rec_mus, 1.0, border_mus)
    draw_text(f"MUSIC SOUNDTRACKS ({len(state.music_tracks)})", panel_x + 14 + tab_w + 75, panel_y + 20, 14, COLOR_GREEN_ACCENT if is_active_mus else COLOR_TEXT_DIM)


def draw_sfx_soundboard(state: SoundPlayerState, panel_x: int, panel_y: int, panel_w: int, panel_h: int, mouse_pos: Vector2, mouse_clicked: bool):
    """Renders the SFX soundboard grid with category filter bar."""
    # Category Filter Bar (Tabs 1 to 5)
    tab_y = panel_y + 54
    tab_w = (panel_w - 24) // CAT_COUNT
    for i in range(CAT_COUNT):
        tx = panel_x + 12 + i * tab_w
        ty = tab_y
        tw = tab_w - 6
        th = 28

        tab_rec = Rectangle(float(tx), float(ty), float(tw), float(th))
        is_hover = check_collision_point_rec(mouse_pos, tab_rec)
        is_active = (i == state.active_cat_idx)

        if is_hover and mouse_clicked:
            state.filter_by_category(i)
            state.sfx.play("select", 0.5)

        bg_col = COLOR_CARD_SELECTED if is_active else (COLOR_CARD_HOVER if is_hover else COLOR_CARD_BG)
        border_col = COLOR_CYAN_ACCENT if is_active else COLOR_PANEL_BORDER
        text_col = COLOR_TEXT_MAIN if is_active else COLOR_TEXT_DIM

        draw_rectangle(tx, ty, tw, th, bg_col)
        draw_rectangle_lines(tx, ty, tw, th, border_col)
        draw_text(CAT_NAMES[i], tx + 8, ty + 8, 11, text_col)

    # Sub-header count
    draw_text(f"Visible SFX: {len(state.filtered_sfx)} / {len(SFX_CATALOG)}  (Scroll with Mouse Wheel or Up/Down)", panel_x + 16, panel_y + 88, 11, COLOR_TEXT_DIM)

    # Sound Cards Grid (2 Columns)
    cards_top_y = panel_y + 106
    card_w = (panel_w - 32) // 2
    card_h = 42
    gap_y = 6

    total_rows = (len(state.filtered_sfx) + 1) // 2
    visible_height = panel_h - 120
    content_height = total_rows * (card_h + gap_y)
    state.max_scroll_y = max(0.0, float(content_height - visible_height))

    # Mouse Wheel Scroll
    wheel = get_mouse_wheel_move()
    if wheel != 0.0:
        state.scroll_y = max(0.0, min(state.max_scroll_y, state.scroll_y - wheel * 28.0))

    begin_scissor_mode(panel_x + 4, cards_top_y, panel_w - 8, visible_height)

    for idx, item in enumerate(state.filtered_sfx):
        row = idx // 2
        col = idx % 2
        cx = panel_x + 12 + col * (card_w + 8)
        cy = int(cards_top_y + row * (card_h + gap_y) - state.scroll_y)

        if cy + card_h < cards_top_y or cy > cards_top_y + visible_height:
            continue

        card_rec = Rectangle(float(cx), float(cy), float(card_w), float(card_h))
        is_hover = check_collision_point_rec(mouse_pos, card_rec)
        is_selected = (idx == state.selected_sfx_idx)

        if is_hover and mouse_clicked:
            state.selected_sfx_idx = idx
            state.play_sfx_by_key(item["key"], item["time"])

        catalog_idx = 0
        for ci, cat_item in enumerate(SFX_CATALOG):
            if cat_item["key"] == item["key"]:
                catalog_idx = ci
                break
        flash_amt = state.card_flash_timers[catalog_idx] / 0.35 if state.card_flash_timers[catalog_idx] > 0.0 else 0.0

        if flash_amt > 0.0:
            bg_col = Color(
                int(20 + 70 * flash_amt),
                int(28 + 120 * flash_amt),
                int(48 + 150 * flash_amt),
                255
            )
        elif is_selected:
            bg_col = COLOR_CARD_SELECTED
        elif is_hover:
            bg_col = COLOR_CARD_HOVER
        else:
            bg_col = COLOR_CARD_BG

        border_col = COLOR_CYAN_ACCENT if (is_selected or flash_amt > 0.0) else COLOR_PANEL_BORDER

        draw_rectangle(cx, cy, card_w, card_h, bg_col)
        draw_rectangle_lines(cx, cy, card_w, card_h, border_col)

        cat_col = get_category_color(item["cat"])
        draw_triangle(
            Vector2(float(cx + 10), float(cy + 13)),
            Vector2(float(cx + 10), float(cy + 29)),
            Vector2(float(cx + 22), float(cy + 21)),
            cat_col
        )

        draw_text(item["title"], cx + 28, cy + 7, 13, COLOR_TEXT_MAIN)
        draw_text(item["desc"], cx + 28, cy + 23, 10, COLOR_TEXT_DIM)

        badge_w = 46
        badge_x = cx + card_w - badge_w - 8
        draw_rectangle(badge_x, cy + 11, badge_w, 18, Color(22, 30, 50, 255))
        draw_rectangle_lines(badge_x, cy + 11, badge_w, 18, cat_col)
        draw_text(item["cat"][:4], badge_x + 5, cy + 14, 10, cat_col)

    end_scissor_mode()

    if state.max_scroll_y > 0.0:
        bar_track_x = panel_x + panel_w - 10
        bar_track_y = cards_top_y
        bar_track_h = visible_height
        thumb_h = max(24, int(bar_track_h * (visible_height / content_height)))
        thumb_y = bar_track_y + int((bar_track_h - thumb_h) * (state.scroll_y / state.max_scroll_y))
        draw_rectangle(bar_track_x, bar_track_y, 4, bar_track_h, Color(24, 32, 54, 255))
        draw_rectangle(bar_track_x, thumb_y, 4, thumb_h, COLOR_CYAN_ACCENT)


def draw_music_tracklist(state: SoundPlayerState, panel_x: int, panel_y: int, panel_w: int, panel_h: int, mouse_pos: Vector2, mouse_clicked: bool):
    """Renders the 12 scrollable procedural soundtrack cards in the left pane."""
    draw_text("CLICK ANY TRACK TO PLAY / STOP (12 LOOPABLE PROCEDURAL SOUNDTRACKS - SCROLLABLE)", panel_x + 16, panel_y + 54, 11, COLOR_GREEN_ACCENT)

    cards_top_y = panel_y + 76
    visible_height = panel_h - 86
    card_w = panel_w - 28
    card_h = 80
    gap_y = 7

    content_height = len(state.music_tracks) * (card_h + gap_y)
    state.max_music_scroll_y = max(0.0, float(content_height - visible_height))

    wheel = get_mouse_wheel_move()
    if wheel != 0.0:
        state.music_scroll_y = max(0.0, min(state.max_music_scroll_y, state.music_scroll_y - wheel * 36.0))

    begin_scissor_mode(panel_x + 4, cards_top_y, panel_w - 8, visible_height)

    for idx, trk in enumerate(state.music_tracks):
        cy = int(cards_top_y + idx * (card_h + gap_y) - state.music_scroll_y)
        if cy + card_h < cards_top_y or cy > cards_top_y + visible_height:
            continue

        card_rec = Rectangle(float(panel_x + 12), float(cy), float(card_w), float(card_h))

        is_hover = check_collision_point_rec(mouse_pos, card_rec)
        is_current = (idx == state.active_track_idx)
        is_playing_this = (is_current and state.music_playing)
        is_selected = (idx == state.selected_music_idx)

        if is_hover and mouse_clicked:
            state.selected_music_idx = idx
            state.play_track_by_index(idx)
            state.sfx.play("click", 0.5)

        # Background color
        if is_playing_this:
            bg_col = COLOR_CARD_PLAYING
            border_col = COLOR_GREEN_ACCENT
        elif is_selected:
            bg_col = COLOR_CARD_SELECTED
            border_col = COLOR_CYAN_ACCENT
        elif is_hover:
            bg_col = COLOR_CARD_HOVER
            border_col = COLOR_PANEL_BORDER
        else:
            bg_col = COLOR_CARD_BG
            border_col = COLOR_PANEL_BORDER

        draw_rectangle(panel_x + 12, cy, card_w, card_h, bg_col)
        draw_rectangle_lines(panel_x + 12, cy, card_w, card_h, border_col)

        # Play / Pause glyph button
        btn_box_x = panel_x + 22
        btn_box_y = cy + 18
        btn_box_w = 44
        btn_box_h = 44

        draw_rectangle(btn_box_x, btn_box_y, btn_box_w, btn_box_h, Color(26, 38, 64, 255))
        draw_rectangle_lines(btn_box_x, btn_box_y, btn_box_w, btn_box_h, COLOR_GREEN_ACCENT if is_playing_this else COLOR_CYAN_ACCENT)

        if is_playing_this:
            # Pause icon (two bars)
            draw_rectangle(btn_box_x + 14, btn_box_y + 12, 5, 20, COLOR_GREEN_ACCENT)
            draw_rectangle(btn_box_x + 25, btn_box_y + 12, 5, 20, COLOR_GREEN_ACCENT)
        else:
            # Play triangle
            draw_triangle(
                Vector2(float(btn_box_x + 16), float(btn_box_y + 12)),
                Vector2(float(btn_box_x + 16), float(btn_box_y + 32)),
                Vector2(float(btn_box_x + 32), float(btn_box_y + 22)),
                COLOR_CYAN_ACCENT
            )

        # Title & Badges
        draw_text(f"{idx + 1}. {trk['title']}", panel_x + 78, cy + 10, 15, COLOR_TEXT_MAIN)

        # Badges
        badge_bpm = f"{trk['bpm']} BPM"
        draw_rectangle(panel_x + 360, cy + 10, 68, 18, Color(24, 34, 56, 255))
        draw_rectangle_lines(panel_x + 360, cy + 10, 68, 18, COLOR_GOLD_ACCENT)
        draw_text(badge_bpm, panel_x + 368, cy + 13, 10, COLOR_GOLD_ACCENT)

        badge_key = trk['key']
        draw_rectangle(panel_x + 436, cy + 10, 105, 18, Color(24, 34, 56, 255))
        draw_rectangle_lines(panel_x + 436, cy + 10, 105, 18, COLOR_CYAN_ACCENT)
        draw_text(badge_key, panel_x + 442, cy + 13, 10, COLOR_CYAN_ACCENT)

        # Playing Status Indicator
        if is_playing_this:
            draw_text("NOW PLAYING [LOOP]", panel_x + 550, cy + 12, 11, COLOR_GREEN_ACCENT)
        else:
            draw_text(f"{trk['bars']} Bars ({trk['duration']:.1f}s)", panel_x + 550, cy + 12, 11, COLOR_TEXT_DIM)

        # Progression & Instrumentation lines
        draw_text(f"Chords: {trk['progression']}", panel_x + 78, cy + 30, 11, COLOR_CYAN_ACCENT)
        draw_text(trk['instrumentation'], panel_x + 78, cy + 46, 10, COLOR_TEXT_DIM)

        # Mini Progress Bar for each card
        pbar_x = panel_x + 78
        pbar_y = cy + 64
        pbar_w = card_w - 90
        pbar_h = 5

        draw_rectangle(pbar_x, pbar_y, pbar_w, pbar_h, Color(24, 32, 52, 255))
        if is_playing_this:
            prog_ratio = (state.track_elapsed / trk["duration"]) if trk["duration"] > 0 else 0.0
            prog_ratio = max(0.0, min(1.0, prog_ratio))
            draw_rectangle(pbar_x, pbar_y, int(pbar_w * prog_ratio), pbar_h, COLOR_GREEN_ACCENT)

    end_scissor_mode()

    if state.max_music_scroll_y > 0.0:
        bar_track_x = panel_x + panel_w - 10
        bar_track_y = cards_top_y
        bar_track_h = visible_height
        thumb_h = max(24, int(bar_track_h * (visible_height / content_height)))
        thumb_y = bar_track_y + int((bar_track_h - thumb_h) * (state.music_scroll_y / state.max_music_scroll_y))
        draw_rectangle(bar_track_x, bar_track_y, 4, bar_track_h, Color(24, 32, 54, 255))
        draw_rectangle(bar_track_x, thumb_y, 4, thumb_h, COLOR_GREEN_ACCENT)


def draw_left_soundboard_panel(state: SoundPlayerState, mouse_pos: Vector2, mouse_clicked: bool):
    """Renders the entire left pane with view switching between SFX and Music."""
    panel_x = 20
    panel_y = 64
    panel_w = 760
    panel_h = 600

    draw_rectangle(panel_x, panel_y, panel_w, panel_h, COLOR_PANEL_BG)
    draw_rectangle_lines(panel_x, panel_y, panel_w, panel_h, COLOR_PANEL_BORDER)

    # Master View Tabs: [SOUND EFFECTS] vs [MUSIC SOUNDTRACKS]
    draw_master_view_tabs(state, panel_x, panel_y, panel_w, mouse_pos, mouse_clicked)

    # Content based on active view mode
    if state.view_mode == VIEW_SFX:
        draw_sfx_soundboard(state, panel_x, panel_y, panel_w, panel_h, mouse_pos, mouse_clicked)
    else:
        draw_music_tracklist(state, panel_x, panel_y, panel_w, panel_h, mouse_pos, mouse_clicked)


def draw_visualizer_panel(state: SoundPlayerState):
    """Renders the real-time CRT oscilloscope and 16-band reactive frequency equalizer."""
    panel_x = 795
    panel_y = 64
    panel_w = 465
    panel_h = 210

    draw_rectangle(panel_x, panel_y, panel_w, panel_h, Color(8, 12, 20, 255))
    draw_rectangle_lines(panel_x, panel_y, panel_w, panel_h, COLOR_PANEL_BORDER)

    draw_text("REAL-TIME AUDIO SPECTRUM & OSCILLOSCOPE", panel_x + 14, panel_y + 12, 12, COLOR_CYAN_ACCENT)
    mode_text = "MODE: [F1] SPECTRUM + SCOPE" if not state.show_raw_scope else "MODE: [F1] RAW OSCILLOSCOPE"
    draw_text(mode_text, panel_x + panel_w - 180, panel_y + 12, 10, COLOR_TEXT_DIM)

    # Grid background
    for gx in range(panel_x + 20, panel_x + panel_w - 20, 40):
        draw_line(gx, panel_y + 32, gx, panel_y + 160, Color(20, 32, 50, 100))
    for gy in range(panel_y + 32, panel_y + 160, 24):
        draw_line(panel_x + 14, gy, panel_x + panel_w - 14, gy, Color(20, 32, 50, 100))

    if not state.show_raw_scope:
        eq_x = panel_x + 20
        eq_y = panel_y + 155
        eq_w = (panel_w - 40) // 16
        max_bar_h = 70.0

        for b in range(16):
            bx = eq_x + b * eq_w
            level = state.spectrum_bands[b]
            bar_h = int(level * max_bar_h)
            peak_h = int(state.spectrum_peaks[b] * max_bar_h)

            if level > 0.8:
                bar_col = COLOR_RED_ACCENT
            elif level > 0.5:
                bar_col = COLOR_GOLD_ACCENT
            else:
                bar_col = COLOR_GREEN_ACCENT

            draw_rectangle(bx + 2, eq_y - bar_h, eq_w - 4, bar_h, bar_col)

            if peak_h > 2:
                draw_rectangle(bx + 2, eq_y - peak_h - 2, eq_w - 4, 2, COLOR_TEXT_MAIN)

        draw_text("60Hz", panel_x + 18, panel_y + 162, 9, COLOR_TEXT_MUTED)
        draw_text("1kHz", panel_x + panel_w // 2 - 12, panel_y + 162, 9, COLOR_TEXT_MUTED)
        draw_text("11kHz", panel_x + panel_w - 38, panel_y + 162, 9, COLOR_TEXT_MUTED)

    # Oscilloscope Waveform overlay
    scope_y = panel_y + (95 if not state.show_raw_scope else 105)
    scope_amp = 26.0 if not state.show_raw_scope else 50.0
    pts_count = 120
    step_x = (panel_w - 40) / float(pts_count)

    active_amp = max(0.08, max(state.spectrum_bands))
    for i in range(pts_count - 1):
        x1 = int(panel_x + 20 + i * step_x)
        x2 = int(panel_x + 20 + (i + 1) * step_x)

        phase1 = i * 0.18 + state.scope_timer * 14.0
        phase2 = (i + 1) * 0.18 + state.scope_timer * 14.0

        wave1 = math.sin(phase1) * 0.7 + math.sin(phase1 * 2.2) * 0.3
        wave2 = math.sin(phase2) * 0.7 + math.sin(phase2 * 2.2) * 0.3

        y1 = int(scope_y + wave1 * scope_amp * active_amp)
        y2 = int(scope_y + wave2 * scope_amp * active_amp)

        beam_col = Color(0, 240, 255, int(140 + 115 * active_amp))
        draw_line(x1, y1, x2, y2, beam_col)

    # Telemetry footer bar
    draw_rectangle(panel_x, panel_y + panel_h - 28, panel_w, 28, Color(14, 20, 34, 255))
    draw_line(panel_x, panel_y + panel_h - 28, panel_x + panel_w, panel_y + panel_h - 28, COLOR_PANEL_BORDER)
    sfx_banner = f"ACTIVE SFX: [{state.last_played_key.upper()}]  |  DUR: {state.last_played_duration:.2f}s  |  FORMAT: 16-BIT PCM 22.05kHz"
    draw_text(sfx_banner, panel_x + 14, panel_y + panel_h - 20, 11, COLOR_GOLD_ACCENT if state.last_played_time > 0.0 else COLOR_TEXT_DIM)


def draw_jukebox_panel(state: SoundPlayerState, mouse_pos: Vector2, mouse_clicked: bool):
    """Renders procedural background music jukebox, track progression, transport buttons, and beat LEDs."""
    panel_x = 795
    panel_y = 286
    panel_w = 465
    panel_h = 224

    draw_rectangle(panel_x, panel_y, panel_w, panel_h, COLOR_PANEL_BG)
    draw_rectangle_lines(panel_x, panel_y, panel_w, panel_h, COLOR_PANEL_BORDER)

    draw_text("PROCEDURAL BGM JUKEBOX (SYNTH MUSIC)", panel_x + 14, panel_y + 12, 12, COLOR_CYAN_ACCENT)
    status_text = "PLAYING [LOOP]" if state.music_playing else "STOPPED"
    status_col = COLOR_GREEN_ACCENT if state.music_playing else COLOR_TEXT_MUTED
    draw_text(status_text, panel_x + panel_w - 120, panel_y + 12, 11, status_col)

    track = state.music_tracks[state.active_track_idx]

    # Track Title & BPM
    draw_text(f"Track {state.active_track_idx + 1}/{len(state.music_tracks)}: {track['title']}", panel_x + 14, panel_y + 36, 15, COLOR_TEXT_MAIN)
    draw_text(f"Tempo: {track['bpm']} BPM   |   Length: {track['bars']} Bars ({track['duration']:.1f}s)", panel_x + 14, panel_y + 56, 11, COLOR_GOLD_ACCENT)

    draw_text(f"Progression: {track['progression']}", panel_x + 14, panel_y + 74, 11, COLOR_CYAN_ACCENT)
    draw_text(track['instrumentation'], panel_x + 14, panel_y + 90, 10, COLOR_TEXT_DIM)

    # Beat / Bar Progress Bar
    bar_x = panel_x + 14
    bar_y = panel_y + 112
    bar_w = panel_w - 28
    bar_h = 10
    draw_rectangle(bar_x, bar_y, bar_w, bar_h, Color(24, 32, 52, 255))

    progress = (state.track_elapsed / track["duration"]) if track["duration"] > 0 else 0.0
    progress = max(0.0, min(1.0, progress))
    fill_w = int(bar_w * progress)
    draw_rectangle(bar_x, bar_y, fill_w, bar_h, COLOR_GREEN_ACCENT if state.music_playing else COLOR_TEXT_MUTED)
    draw_rectangle_lines(bar_x, bar_y, bar_w, bar_h, COLOR_PANEL_BORDER)

    # Beat LEDs
    led_y = panel_y + 130
    led_step = bar_w // track["bars"]
    current_bar = int(progress * track["bars"])
    for b in range(track["bars"]):
        lx = bar_x + b * led_step + led_step // 2
        is_lit = (state.music_playing and b == current_bar)
        led_col = COLOR_GREEN_ACCENT if is_lit else Color(30, 42, 68, 255)
        draw_circle(lx, led_y, 4, led_col)
        draw_text(str(b + 1), lx - 3, led_y + 8, 9, COLOR_TEXT_MUTED)

    # Transport Buttons: [PREV TRACK] [PLAY / PAUSE] [STOP] [NEXT TRACK]
    btn_y = panel_y + 168
    btn_h = 36

    prev_rec = Rectangle(float(panel_x + 14), float(btn_y), 90.0, float(btn_h))
    is_prev_hover = check_collision_point_rec(mouse_pos, prev_rec)
    if is_prev_hover and mouse_clicked:
        state.prev_bgm_track()
        state.sfx.play("click", 0.5)
    draw_rectangle_rec(prev_rec, COLOR_CARD_HOVER if is_prev_hover else COLOR_CARD_BG)
    draw_rectangle_lines_ex(prev_rec, 1.0, COLOR_CYAN_ACCENT if is_prev_hover else COLOR_PANEL_BORDER)
    draw_text("< PREV [N]", panel_x + 22, btn_y + 12, 11, COLOR_TEXT_MAIN)

    play_label = "PAUSE [M]" if state.music_playing else "PLAY [M]"
    play_rec = Rectangle(float(panel_x + 114), float(btn_y), 130.0, float(btn_h))
    is_play_hover = check_collision_point_rec(mouse_pos, play_rec)
    if is_play_hover and mouse_clicked:
        state.toggle_bgm()
        state.sfx.play("click", 0.6)
    draw_rectangle_rec(play_rec, COLOR_CARD_HOVER if is_play_hover else COLOR_CARD_BG)
    draw_rectangle_lines_ex(play_rec, 1.0, COLOR_GREEN_ACCENT if is_play_hover else COLOR_PANEL_BORDER)
    draw_text(play_label, panel_x + 140, btn_y + 12, 12, COLOR_GREEN_ACCENT if state.music_playing else COLOR_TEXT_MAIN)

    stop_rec = Rectangle(float(panel_x + 254), float(btn_y), 85.0, float(btn_h))
    is_stop_hover = check_collision_point_rec(mouse_pos, stop_rec)
    if is_stop_hover and mouse_clicked:
        state.music.stop()
        state.music_playing = False
        state.track_elapsed = 0.0
        state.sfx.play("click", 0.5)
    draw_rectangle_rec(stop_rec, COLOR_CARD_HOVER if is_stop_hover else COLOR_CARD_BG)
    draw_rectangle_lines_ex(stop_rec, 1.0, COLOR_RED_ACCENT if is_stop_hover else COLOR_PANEL_BORDER)
    draw_text("STOP", panel_x + 280, btn_y + 12, 11, COLOR_TEXT_MAIN)

    next_rec = Rectangle(float(panel_x + 349), float(btn_y), 102.0, float(btn_h))
    is_next_hover = check_collision_point_rec(mouse_pos, next_rec)
    if is_next_hover and mouse_clicked:
        state.next_bgm_track()
        state.sfx.play("click", 0.5)
    draw_rectangle_rec(next_rec, COLOR_CARD_HOVER if is_next_hover else COLOR_CARD_BG)
    draw_rectangle_lines_ex(next_rec, 1.0, COLOR_CYAN_ACCENT if is_next_hover else COLOR_PANEL_BORDER)
    draw_text("NEXT [N] >", panel_x + 365, btn_y + 12, 11, COLOR_TEXT_MAIN)


def draw_mixer_panel(state: SoundPlayerState, mouse_pos: Vector2, mouse_down: bool, mouse_clicked: bool):
    """Renders Master, SFX, and BGM volume faders, mute switches, and reset actions."""
    panel_x = 795
    panel_y = 522
    panel_w = 465
    panel_h = 142

    draw_rectangle(panel_x, panel_y, panel_w, panel_h, COLOR_PANEL_BG)
    draw_rectangle_lines(panel_x, panel_y, panel_w, panel_h, COLOR_PANEL_BORDER)

    draw_text("AUDIO GAIN MIXER & VOLUME CONTROLS", panel_x + 14, panel_y + 10, 11, COLOR_CYAN_ACCENT)

    def draw_fader(label: str, val: float, y_pos: int, col: Color) -> float:
        draw_text(label, panel_x + 14, y_pos, 11, COLOR_TEXT_MAIN)
        draw_text(f"{int(val * 100)}%", panel_x + 80, y_pos, 11, col)

        track_x = panel_x + 125
        track_y = y_pos + 4
        track_w = 230
        track_h = 8

        track_rec = Rectangle(float(track_x - 4), float(track_y - 6), float(track_w + 8), float(track_h + 12))
        is_hover = check_collision_point_rec(mouse_pos, track_rec)

        new_val = val
        if is_hover and mouse_down:
            ratio = (mouse_pos.x - float(track_x)) / float(track_w)
            new_val = max(0.0, min(1.0, ratio))

        draw_rectangle(track_x, track_y, track_w, track_h, Color(24, 32, 54, 255))
        draw_rectangle(track_x, track_y, int(track_w * new_val), track_h, col)
        draw_rectangle_lines(track_x, track_y, track_w, track_h, COLOR_PANEL_BORDER)

        thumb_x = track_x + int(track_w * new_val)
        draw_circle(thumb_x, track_y + 4, 6, COLOR_TEXT_MAIN)
        return new_val

    # Master Volume
    old_master = state.master_volume
    state.master_volume = draw_fader("Master", state.master_volume, panel_y + 34, COLOR_CYAN_ACCENT)
    if state.master_volume != old_master:
        state.apply_bgm_volume()

    # SFX Volume
    state.sfx_volume = draw_fader("SFX", state.sfx_volume, panel_y + 60, COLOR_GOLD_ACCENT)

    # BGM Volume
    old_bgm = state.bgm_volume
    state.bgm_volume = draw_fader("BGM", state.bgm_volume, panel_y + 86, COLOR_GREEN_ACCENT)
    if state.bgm_volume != old_bgm:
        state.apply_bgm_volume()

    # Mute Buttons
    sfx_mute_rec = Rectangle(float(panel_x + 370), float(panel_y + 30), 82.0, 24.0)
    is_sm_hover = check_collision_point_rec(mouse_pos, sfx_mute_rec)
    if is_sm_hover and mouse_clicked:
        state.sfx_muted = not state.sfx_muted
        state.sfx.play("click", 0.5)
    sm_col = COLOR_RED_ACCENT if state.sfx_muted else COLOR_CARD_BG
    draw_rectangle_rec(sfx_mute_rec, sm_col)
    draw_rectangle_lines_ex(sfx_mute_rec, 1.0, COLOR_RED_ACCENT if state.sfx_muted else COLOR_PANEL_BORDER)
    draw_text("MUTED" if state.sfx_muted else "Mute SFX", panel_x + 382, panel_y + 36, 10, COLOR_TEXT_MAIN)

    bgm_mute_rec = Rectangle(float(panel_x + 370), float(panel_y + 60), 82.0, 24.0)
    is_bm_hover = check_collision_point_rec(mouse_pos, bgm_mute_rec)
    if is_bm_hover and mouse_clicked:
        state.bgm_muted = not state.bgm_muted
        state.apply_bgm_volume()
        state.sfx.play("click", 0.5)
    bm_col = COLOR_RED_ACCENT if state.bgm_muted else COLOR_CARD_BG
    draw_rectangle_rec(bgm_mute_rec, bm_col)
    draw_rectangle_lines_ex(bgm_mute_rec, 1.0, COLOR_RED_ACCENT if state.bgm_muted else COLOR_PANEL_BORDER)
    draw_text("MUTED" if state.bgm_muted else "Mute BGM", panel_x + 382, panel_y + 66, 10, COLOR_TEXT_MAIN)

    # Reset All
    reset_rec = Rectangle(float(panel_x + 370), float(panel_y + 92), 82.0, 26.0)
    is_res_hover = check_collision_point_rec(mouse_pos, reset_rec)
    if is_res_hover and mouse_clicked:
        state.master_volume = 0.85
        state.sfx_volume = 1.0
        state.bgm_volume = 0.60
        state.sfx_muted = False
        state.bgm_muted = False
        state.apply_bgm_volume()
        state.music.stop()
        state.music_playing = False
        state.track_elapsed = 0.0
        state.sfx.play("click", 0.5)
    draw_rectangle_rec(reset_rec, COLOR_CARD_HOVER if is_res_hover else COLOR_CARD_BG)
    draw_rectangle_lines_ex(reset_rec, 1.0, COLOR_CYAN_ACCENT if is_res_hover else COLOR_PANEL_BORDER)
    draw_text("RESET [R]", panel_x + 382, panel_y + 98, 10, COLOR_CYAN_ACCENT)


def draw_hud_footer():
    """Renders bottom shortcut and legend bar."""
    bar_y = SCREEN_HEIGHT - 44
    draw_rectangle(0, bar_y, SCREEN_WIDTH, 44, COLOR_PANEL_HEADER)
    draw_line(0, bar_y, SCREEN_WIDTH, bar_y, COLOR_PANEL_BORDER)

    legend_items = [
        "[Q / E / LB / RB] Switch SFX / Music View",
        "[Mouse / D-Pad] Navigate Cards",
        "[Space / Enter / Pad A] Trigger Sound / Track",
        "[M / Pad X] BGM Toggle",
        "[N / Pad Y] Next Track",
        "[[ / ]] Master Vol",
        "[Tab] X-Ray Telemetry",
        "[F1] Scope Mode"
    ]
    draw_text("  |  ".join(legend_items), 20, bar_y + 14, 11, COLOR_TEXT_DIM)


def draw_xray_inspector_overlay(state: SoundPlayerState):
    """Draws an in-depth telemetry overlay detailing memory and synthesis architecture."""
    panel_x = 160
    panel_y = 90
    panel_w = 960
    panel_h = 520

    draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, Color(5, 8, 14, 215))

    draw_rectangle(panel_x, panel_y, panel_w, panel_h, Color(14, 20, 34, 255))
    draw_rectangle_lines(panel_x, panel_y, panel_w, panel_h, COLOR_CYAN_ACCENT)

    draw_text("X-RAY AUDIO SYNTHESIS & TELEMETRY INSPECTOR ([Tab] to Close)", panel_x + 24, panel_y + 20, 18, COLOR_CYAN_ACCENT)
    draw_line(panel_x + 24, panel_y + 48, panel_x + panel_w - 24, panel_y + 48, COLOR_PANEL_BORDER)

    col1_x = panel_x + 30
    col2_x = panel_x + 490

    draw_text("AUDIO HARDWARE & DEVICE TELEMETRY", col1_x, panel_y + 64, 14, COLOR_GOLD_ACCENT)
    telemetry_stats = [
        ("Audio Engine Driver", "Raylib CFFI (WASAPI / miniaudio backend)"),
        ("Sample Rate", "22,050 Hz (Nyquist limit: 11,025 Hz)"),
        ("Channel Layout", "1 Channel Mono (Up-mixed to Stereo Output)"),
        ("Bit Depth", "16-bit Signed Little-Endian PCM (int16_t)"),
        ("Dynamic Clamping", "Normalized [-1.0, 1.0] -> 32,767 Int Scaling"),
        ("Cached SFX Count", f"{state.sfx.count()} Distinct Sound Objects"),
        ("Cached Music Tracks", f"{len(state.music_tracks)} Complete Soundtrack Loops"),
        ("Total RAM Footprint", "< 4.2 MB (All 48 SFX + 12 BGM Tracks)"),
        ("Synthesis Techniques", "Additive, Subtractive IIR, FM, PWM, Delay Echo")
    ]

    ty = panel_y + 92
    for label, val in telemetry_stats:
        draw_text(f"{label}:", col1_x, ty, 12, COLOR_TEXT_DIM)
        draw_text(val, col1_x + 180, ty, 12, COLOR_TEXT_MAIN)
        ty += 22

    draw_text("C++ / CROSS-LANGUAGE TRANSFERABILITY", col2_x, panel_y + 64, 14, COLOR_GOLD_ACCENT)
    arch_notes = [
        "1. Pure Procedural Generation: Zero external asset dependencies.",
        "   Eliminates 80+ MB of compressed asset files from repository.",
        "",
        "2. Fixed-Capacity Sound Buffers: In C++, SoundLibrary translates to",
        "   std::unordered_map<std::string, Sound> with zero heap allocations",
        "   during active gameplay frames.",
        "",
        "3. Mathematical Synthesis Fundamentals:",
        "   - Additive synthesis (Sine + Square + Triangle + Sawtooth)",
        "   - Subtractive filtering (One-pole & dual-pole band-pass IIR)",
        "   - FM & Ring Modulation (Crystalline chimes, bells, warp FX)",
        "   - Pulse-Width Modulation (Dynamic duty-cycle synthwave leads)",
        "",
        "4. Seamless Looping: SynthMusicPlayer checks is_sound_playing()",
        "   frame-by-frame and restarts playback with click-free crossfades."
    ]

    ty2 = panel_y + 92
    for note in arch_notes:
        draw_text(note, col2_x, ty2, 11, COLOR_TEXT_MAIN if note.startswith(("1", "2", "3", "4")) else COLOR_TEXT_DIM)
        ty2 += 18

    draw_text("Press [Tab] or [Gamepad View] to return to Audio Soundboard", panel_x + panel_w // 2 - 180, panel_y + panel_h - 32, 12, COLOR_CYAN_ACCENT)


# ==============================================================================
# BLOCK 4: MAIN GAME LOOP & DUAL INPUT DISPATCHER
# ==============================================================================

class SoundPlayerApp:
    """Main application lifecycle controller."""

    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)

        init_audio_device()
        self.state = SoundPlayerState()

    def handle_input(self):
        """Processes dual Keyboard/Mouse and Gamepad controls simultaneously."""
        dt = min(get_frame_time(), 0.05)

        # 1. Telemetry / X-Ray Toggle ([Tab] / Gamepad Select)
        if is_dual_xray_toggle_pressed():
            self.state.show_xray = not self.state.show_xray
            self.state.sfx.play("click", 0.5)

        # 2. Scope Mode Toggle ([F1])
        if is_key_pressed(KEY_F1):
            self.state.show_raw_scope = not self.state.show_raw_scope
            self.state.sfx.play("click", 0.5)

        if self.state.show_xray:
            return

        # 3. Switch View Modes ([Q] / [E] / Gamepad LB / RB)
        if is_key_pressed(KEY_Q) or is_key_pressed(KEY_E):
            self.state.view_mode = VIEW_MUSIC if self.state.view_mode == VIEW_SFX else VIEW_SFX
            self.state.sfx.play("select", 0.5)

        if is_gamepad_available(0) and self.state.pad_tab_cooldown <= 0.0:
            if is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_TRIGGER_1) or is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_TRIGGER_1):
                self.state.view_mode = VIEW_MUSIC if self.state.view_mode == VIEW_SFX else VIEW_SFX
                self.state.sfx.play("select", 0.5)
                self.state.pad_tab_cooldown = 0.25

        # 4. View Mode Specific Controls
        if self.state.view_mode == VIEW_SFX:
            # Category Filter Shortcuts (1 to 5)
            if is_key_pressed(KEY_ONE):
                self.state.filter_by_category(0)
                self.state.sfx.play("select", 0.5)
            elif is_key_pressed(KEY_TWO):
                self.state.filter_by_category(1)
                self.state.sfx.play("select", 0.5)
            elif is_key_pressed(KEY_THREE):
                self.state.filter_by_category(2)
                self.state.sfx.play("select", 0.5)
            elif is_key_pressed(KEY_FOUR):
                self.state.filter_by_category(3)
                self.state.sfx.play("select", 0.5)
            elif is_key_pressed(KEY_FIVE):
                self.state.filter_by_category(4)
                self.state.sfx.play("select", 0.5)

            # Grid Navigation
            move = get_dual_move_2d()
            if self.state.pad_nav_cooldown <= 0.0:
                if move.y > 0.4:
                    if self.state.selected_sfx_idx + 2 < len(self.state.filtered_sfx):
                        self.state.selected_sfx_idx += 2
                        self.state.sfx.play("select", 0.4)
                        self.state.pad_nav_cooldown = 0.16
                elif move.y < -0.4:
                    if self.state.selected_sfx_idx - 2 >= 0:
                        self.state.selected_sfx_idx -= 2
                        self.state.sfx.play("select", 0.4)
                        self.state.pad_nav_cooldown = 0.16
                elif move.x > 0.4:
                    if self.state.selected_sfx_idx % 2 == 0 and self.state.selected_sfx_idx + 1 < len(self.state.filtered_sfx):
                        self.state.selected_sfx_idx += 1
                        self.state.sfx.play("select", 0.4)
                        self.state.pad_nav_cooldown = 0.16
                elif move.x < -0.4:
                    if self.state.selected_sfx_idx % 2 == 1:
                        self.state.selected_sfx_idx -= 1
                        self.state.sfx.play("select", 0.4)
                        self.state.pad_nav_cooldown = 0.16

            # Auto-scroll soundboard
            sel_row = self.state.selected_sfx_idx // 2
            card_target_y = sel_row * 48
            if card_target_y < self.state.scroll_y:
                self.state.scroll_y = float(card_target_y)
            elif card_target_y > self.state.scroll_y + 430:
                self.state.scroll_y = float(card_target_y - 430)

            # Play Selected SFX
            if is_key_pressed(KEY_SPACE) or is_key_pressed(KEY_ENTER) or (is_gamepad_available(0) and is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_FACE_DOWN)):
                if 0 <= self.state.selected_sfx_idx < len(self.state.filtered_sfx):
                    item = self.state.filtered_sfx[self.state.selected_sfx_idx]
                    self.state.play_sfx_by_key(item["key"], item["time"])
        else:
            # Music Tracklist Navigation
            move = get_dual_move_2d()
            if self.state.pad_nav_cooldown <= 0.0:
                if move.y > 0.4:
                    self.state.selected_music_idx = (self.state.selected_music_idx + 1) % len(self.state.music_tracks)
                    self.state.sfx.play("select", 0.4)
                    self.state.pad_nav_cooldown = 0.18
                elif move.y < -0.4:
                    self.state.selected_music_idx = (self.state.selected_music_idx - 1) % len(self.state.music_tracks)
                    self.state.sfx.play("select", 0.4)
                    self.state.pad_nav_cooldown = 0.18

            # Auto-scroll music tracklist
            music_target_y = self.state.selected_music_idx * 87
            if music_target_y < self.state.music_scroll_y:
                self.state.music_scroll_y = float(music_target_y)
            elif music_target_y > self.state.music_scroll_y + 420:
                self.state.music_scroll_y = float(music_target_y - 420)

            # Toggle Selected Music Track
            if is_key_pressed(KEY_SPACE) or is_key_pressed(KEY_ENTER) or (is_gamepad_available(0) and is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_FACE_DOWN)):
                self.state.play_track_by_index(self.state.selected_music_idx)
                self.state.sfx.play("click", 0.5)

        # 5. Global BGM Transport shortcuts
        if is_key_pressed(KEY_M) or (is_gamepad_available(0) and is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_FACE_LEFT)):
            self.state.toggle_bgm()
            self.state.sfx.play("click", 0.5)

        if is_key_pressed(KEY_N) or (is_gamepad_available(0) and is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_FACE_UP)):
            self.state.next_bgm_track()
            self.state.sfx.play("click", 0.5)

        # 6. Volume Adjust ([ / ])
        if is_key_pressed(KEY_LEFT_BRACKET):
            self.state.master_volume = max(0.0, self.state.master_volume - 0.05)
            self.state.apply_bgm_volume()
        elif is_key_pressed(KEY_RIGHT_BRACKET):
            self.state.master_volume = min(1.0, self.state.master_volume + 0.05)
            self.state.apply_bgm_volume()

        # 7. Reset All ([R] / Gamepad Start)
        if is_key_pressed(KEY_R) or (is_gamepad_available(0) and is_gamepad_button_pressed(0, GAMEPAD_BUTTON_MIDDLE_RIGHT)):
            self.state.master_volume = 0.85
            self.state.sfx_volume = 1.0
            self.state.bgm_volume = 0.60
            self.state.sfx_muted = False
            self.state.bgm_muted = False
            self.state.apply_bgm_volume()
            self.state.music.stop()
            self.state.music_playing = False
            self.state.track_elapsed = 0.0
            self.state.sfx.play("click", 0.5)

    def draw(self):
        """Renders the complete sound workstation frame."""
        begin_drawing()
        clear_background(COLOR_BG_DARK)

        mouse_pos = get_mouse_position()
        mouse_down = is_mouse_button_down(MOUSE_BUTTON_LEFT)
        mouse_clicked = is_mouse_button_pressed(MOUSE_BUTTON_LEFT)

        # Top Bar & Header
        draw_header_title()

        # Left Soundboard (SFX or Music Tracklist)
        draw_left_soundboard_panel(self.state, mouse_pos, mouse_clicked)

        # Right Panels
        draw_visualizer_panel(self.state)
        draw_jukebox_panel(self.state, mouse_pos, mouse_clicked)
        draw_mixer_panel(self.state, mouse_pos, mouse_down, mouse_clicked)

        # Bottom Footer
        draw_hud_footer()

        # Top-Bar Workspace Settings Bar (Reserved Region x = 450..980)
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)

        # Modal Telemetry Overlay
        if self.state.show_xray:
            draw_xray_inspector_overlay(self.state)

        end_drawing()

    def run(self, smoke_test: bool = False):
        """Main workstation loop with automated smoke-test exit."""
        frame_count = 0
        while not window_should_close():
            dt = min(get_frame_time(), 0.05)
            self.handle_input()
            self.state.update(dt)
            self.draw()

            frame_count += 1
            if smoke_test and frame_count >= 3:
                break

        self.state.unload()
        close_audio_device()
        close_window()


if __name__ == "__main__":
    is_smoke = "--smoke-test" in sys.argv
    SoundPlayerApp().run(smoke_test=is_smoke)
