# -*- coding: utf-8 -*-
"""
Cumulative Loot Piñata - Cumulative Distribution Function (CDF) Sampling & Frequency Histograms
=================================================================================================
Section          : 3.4 Progression & Economy
Pattern Category : Progression & Economy (Probabilistic Loot & Sampling)
Dimension        : 2D

Problem Solved:
  In game economies, loot tables, and gacha reward mechanics, naive uniform random generation
  (flat 1/N odds) destroys economic progression by granting ultra-rare artifacts at the same
  frequency as mundane vendor trash. Conversely, naive hardcoded if/else ladders are rigid,
  difficult to rebalance, scale poorly across hundreds of items, and cannot support dynamic
  player stats like Magic Find or bad-luck pity thresholds. Without a formal Cumulative
  Distribution Function (CDF) sampling pipeline and empirical frequency validation, game
  designers have no mathematical guarantee that drop rates converge to design specifications
  under the Law of Large Numbers.

How the Pattern Works:
  1. Discrete Probability Density Function (PDF) & Base Weights:
     Each rarity tier k in {0..K-1} is assigned an integer weight w_k.
     Total weight: W = sum(w_k).
     Theoretical Probability: P(k) = w_k / W.
     Here we define 5 tiers:
       - Common    : 600 weight -> 60.0% probability
       - Uncommon  : 250 weight -> 25.0% probability
       - Rare      : 100 weight -> 10.0% probability
       - Epic      :  40 weight ->  4.0% probability
       - Legendary :  10 weight ->  1.0% probability
       Total Base Weight = 1,000.

  2. Cumulative Distribution Function (CDF):
     The cumulative sum array C_k represents the upper bound of tier k's sampling slice:
       C_k = sum_{i=0}^k w_i
     This partitions the half-open interval [0, W) into K non-overlapping sub-intervals:
       Interval_k = [C_{k-1}, C_k)  (with C_{-1} = 0)
     Normalized to [0.0, 1.0), the cumulative intervals become [F_{k-1}, F_k).

  3. Inverse Transform Sampling:
     To draw an item, sample a uniform random real number R in [0.0, W) (or u in [0.0, 1.0)).
     Perform a search over the cumulative array to find the unique index k such that:
       C_{k-1} <= R < C_k
     In C++, this maps to `std::lower_bound` binary search O(log K) for large tables, or
     a contiguous cache-friendly linear scan O(K) for small tables (K=5).

  4. Dynamic Magic Find / Luck Modifier:
     When the player boosts their Magic Find (MF) or Luck stat L, base weights are dynamically
     skewed toward higher tiers using tier-specific scaling coefficients:
       w'_k = w_k * (1.0 + L * beta_k)
     where beta = [0.0, 0.25, 0.80, 2.20, 5.50].
     Common items gain 0% boost, while Legendary items receive massive relative weight
     expansion, shifting the probability mass without breaking normalization.

  5. Dynamic Pity Escalation Engine:
     To mitigate extreme bad-luck streaks, consecutive non-legendary rolls increment a
     `pity_counter`:
       - Soft Pity (rolls 40..69): Legendary weight increases linearly with each dry roll.
       - Hard Pity (roll 70): Legendary drop is 100% guaranteed.
     Upon rolling Legendary, the pity counter resets to 0.

  6. Real-Time Frequency Histogram & Chi-Square (chi^2) Goodness-of-Fit:
     Every roll updates an empirical observation vector O_k. The system calculates Pearson's
     Chi-Square statistic against expected counts E_k = N * P(k):
       chi^2 = sum_{k=0}^{K-1} ((O_k - E_k)^2 / E_k)  with degrees of freedom df = K - 1 = 4.
     If chi^2 < 9.488 (critical value at p = 0.05), the observed data statistically conforms
     to the theoretical CDF, confirming empirical convergence under the Law of Large Numbers.

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - Reticle Aim / Bat Position  : Mouse Cursor OR Gamepad Left Stick / WASD
  - Whack Piñata (Physical Hit) : Space / Left Click / RT / Gamepad A (South)
  - Batch Roll 100x             : E / Gamepad X (West) (rapid Monte Carlo test)
  - Batch Roll 1,000x           : Q / Gamepad Y (North) (instant Law of Large Numbers convergence)
  - Adjust Luck / Magic Find    : Arrow Up / Down OR Gamepad D-Pad Up / Down (+0% .. +300%)
  - [Tab] / Gamepad View (Select): Toggle X-Ray Telemetry Overlay (Histogram, CDF Table, Chi-Square)
  - [F1]  / Gamepad LB          : Toggle Pattern ON/OFF (Weighted CDF Sampling vs Flat Uniform 20%)
  - [F2]  / Gamepad RB          : Toggle Dynamic Pity Escalation System ON / OFF
  - [C]                         : Clear Roll Statistics & Reset Histogram
  - [Ctrl +/-]                  : Increase / Decrease UI Font Size
  - [F11]                       : Toggle Fullscreen
  - [R]   / Gamepad Start       : Full Simulation Reset
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

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WINDOW_TITLE = "Cumulative Loot Piñata - CDF Sampling & Frequency Histograms (Raylib)"

# Arena Simulation Constants
ARENA_LEFT = 32.0
ARENA_RIGHT = 1248.0
ARENA_FLOOR_Y = 650.0
CEILING_ANCHOR_X = 640.0
CEILING_ANCHOR_Y = 64.0

# 5 Rarity Tier Constants (C++: enum class RarityTier : uint8_t { Common=0, Uncommon, Rare, Epic, Legendary })
TIER_COMMON = 0
TIER_UNCOMMON = 1
TIER_RARE = 2
TIER_EPIC = 3
TIER_LEGENDARY = 4
NUM_TIERS = 5

# Chi-Square Critical Value for df = 4 at alpha = 0.05
CHI_SQUARE_CRITICAL_DF4 = 9.488


# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATION
# ==============================================================================

class TierDefinition:
    """
    Fixed metadata configuration for a single loot rarity tier.
    Maps directly to a plain C++ struct:
      struct TierDefinition {
          int id;
          const char* name;
          float base_weight;
          int gold_value;
          Color primary_color;
          Color glow_color;
          float luck_scale_factor;
      };
    """
    def __init__(self, tier_id: int, name: str, base_weight: float, gold_value: int,
                 primary_color: Color, glow_color: Color, luck_scale_factor: float):
        self.tier_id = tier_id
        self.name = name
        self.base_weight = base_weight
        self.gold_value = gold_value
        self.primary_color = primary_color
        self.glow_color = glow_color
        self.luck_scale_factor = luck_scale_factor


class CdfLootEngine:
    """
    Cumulative Distribution Function (CDF) Sampling Engine with Dynamic Luck
    Scaling, Pity Escalation, and Real-Time Goodness-of-Fit Statistics.

    C++ Transferability:
      - All weights, cumulative intervals, and observed counts are stored in
        fixed-capacity arrays (`std::array<float, 5>` and `std::array<int, 5>`).
      - Sampling uses explicit linear interval search (`for` loop with index comparison).
      - Zero dynamic memory allocations occur during `sample_roll()` execution.
    """
    def __init__(self):
        # 1. Initialize static tier configurations
        self.tiers = [
            TierDefinition(TIER_COMMON, "Common", 600.0, 1,
                           Color(205, 215, 225, 255), Color(140, 155, 175, 120), 0.0),
            TierDefinition(TIER_UNCOMMON, "Uncommon", 250.0, 5,
                           Color(45, 225, 105, 255), Color(25, 150, 65, 140), 0.25),
            TierDefinition(TIER_RARE, "Rare", 100.0, 25,
                           Color(35, 165, 255, 255), Color(15, 95, 185, 160), 0.85),
            TierDefinition(TIER_EPIC, "Epic", 40.0, 100,
                           Color(190, 75, 250, 255), Color(120, 35, 175, 180), 2.40),
            TierDefinition(TIER_LEGENDARY, "Legendary", 10.0, 500,
                           Color(255, 210, 30, 255), Color(215, 140, 15, 210), 5.80),
        ]

        # 2. Dynamic weights and CDF cumulative arrays
        self.effective_weights = [0.0, 0.0, 0.0, 0.0, 0.0]
        self.cumulative_weights = [0.0, 0.0, 0.0, 0.0, 0.0]
        self.normalized_probs = [0.0, 0.0, 0.0, 0.0, 0.0]
        self.total_weight = 1000.0

        # 3. Interactive modifiers
        self.luck_modifier = 0.0           # 0.0 = +0% MF, 1.0 = +100% MF, max = 3.0 (+300% MF)
        self.use_cdf_pattern = True        # [F1]: True = Weighted CDF, False = Flat Uniform (20% each)
        self.pity_enabled = True           # [F2]: True = Pity Thresholds Active, False = Pure Probabilistic
        self.pity_counter = 0              # Consecutive rolls without a Legendary drop
        self.pity_soft_threshold = 40      # Beyond 40 rolls, legendary weight ramps up
        self.pity_hard_threshold = 70      # At 70 rolls, legendary drop is 100% guaranteed

        # 4. Statistical trackers & Law of Large Numbers empirical counters
        self.observed_counts = [0, 0, 0, 0, 0]
        self.total_rolls = 0
        self.lifetime_gold_wealth = 0
        self.last_rolled_tier = TIER_COMMON
        self.last_roll_random_value = 0.0
        self.pity_triggered_last_roll = False

        # Streak metrics
        self.current_streak_tier = -1
        self.current_streak_length = 0
        self.max_legendary_streak = 0

        # Compute initial distribution curves
        self.recalculate_distribution()

    def recalculate_distribution(self):
        """
        Recalculates effective weights, cumulative sums (CDF), and normalized
        probabilities based on current Luck modifier and Pity escalation state.

        Why Cumulative Sampling?
          Given weights [w0, w1, w2, w3, w4], the cumulative array C is:
            C_0 = w0
            C_1 = w0 + w1
            C_2 = w0 + w1 + w2
            C_3 = w0 + w1 + w2 + w3
            C_4 = w0 + w1 + w2 + w3 + w4 = Total_Weight
          Any uniform random number R in [0, Total_Weight) maps to exactly one
          interval [C_{k-1}, C_k) with probability exactly equal to w_k / Total_Weight.
        """
        # Case A: Pattern Disabled -> Flat Uniform Randomness (Each tier gets 200.0 weight = 20%)
        if not self.use_cdf_pattern:
            for i in range(NUM_TIERS):
                self.effective_weights[i] = 200.0
            self.total_weight = 1000.0
            run_sum = 0.0
            for i in range(NUM_TIERS):
                run_sum += self.effective_weights[i]
                self.cumulative_weights[i] = run_sum
                self.normalized_probs[i] = self.effective_weights[i] / self.total_weight
            return

        # Case B: Pattern Enabled -> Weighted CDF with Magic Find & Soft Pity Ramp
        running_total = 0.0
        for i in range(NUM_TIERS):
            base_w = self.tiers[i].base_weight
            scale = self.tiers[i].luck_scale_factor
            # Dynamic Magic Find scaling formula: w' = w * (1 + Luck * Factor)
            eff_w = base_w * (1.0 + self.luck_modifier * scale)

            # Apply Soft Pity Escalation if dry streak exceeds threshold
            if self.pity_enabled and i == TIER_LEGENDARY and self.pity_counter > self.pity_soft_threshold:
                excess_dry_rolls = self.pity_counter - self.pity_soft_threshold
                # Linearly inject additional weight for every roll past soft threshold
                soft_pity_boost = float(excess_dry_rolls) * 14.0
                eff_w += soft_pity_boost

            self.effective_weights[i] = eff_w
            running_total += eff_w

        self.total_weight = max(0.0001, running_total)

        # Build monotonic cumulative sum array C_k and normalized probabilities P_k
        accumulator = 0.0
        for i in range(NUM_TIERS):
            accumulator += self.effective_weights[i]
            self.cumulative_weights[i] = accumulator
            self.normalized_probs[i] = self.effective_weights[i] / self.total_weight

    def sample_roll(self) -> int:
        """
        Executes a single probabilistic drop using Inverse Transform CDF Sampling.
        Returns the dropped tier index in [0..4].
        """
        # Step 1: Check Hard Pity Guarantee
        if self.use_cdf_pattern and self.pity_enabled and self.pity_counter >= self.pity_hard_threshold:
            selected_tier = TIER_LEGENDARY
            self.pity_triggered_last_roll = True
            self.last_roll_random_value = self.total_weight - 0.001
        elif not self.use_cdf_pattern:
            # Flat uniform random tier selection (Pattern OFF)
            selected_tier = random.randint(0, NUM_TIERS - 1)
            self.pity_triggered_last_roll = False
            self.last_roll_random_value = float(selected_tier * 200 + 100)
        else:
            # Step 2: Standard Inverse Transform Sampling over Cumulative Interval [0, Total_Weight)
            roll_r = random.uniform(0.0, self.total_weight)
            self.last_roll_random_value = roll_r
            self.pity_triggered_last_roll = False

            selected_tier = TIER_COMMON
            for k in range(NUM_TIERS):
                if roll_r < self.cumulative_weights[k]:
                    selected_tier = k
                    break

        # Step 3: Update State & Pity Counters
        if selected_tier == TIER_LEGENDARY:
            self.pity_counter = 0
        else:
            self.pity_counter += 1

        # Step 4: Record Statistics
        self.observed_counts[selected_tier] += 1
        self.total_rolls += 1
        self.lifetime_gold_wealth += self.tiers[selected_tier].gold_value
        self.last_rolled_tier = selected_tier

        # Step 5: Streak Tracking
        if selected_tier == self.current_streak_tier:
            self.current_streak_length += 1
        else:
            self.current_streak_tier = selected_tier
            self.current_streak_length = 1

        if selected_tier == TIER_LEGENDARY:
            if self.current_streak_length > self.max_legendary_streak:
                self.max_legendary_streak = self.current_streak_length

        # If pity modified distribution dynamically, refresh curves
        if self.pity_enabled and self.pity_counter >= self.pity_soft_threshold:
            self.recalculate_distribution()

        return selected_tier

    def batch_roll(self, roll_count: int):
        """
        Executes a fast Monte Carlo batch simulation of N rolls.
        Demonstrates the Law of Large Numbers converging to the theoretical CDF.
        """
        for _ in range(roll_count):
            self.sample_roll()

    def compute_chi_square(self):
        """
        Calculates Pearson's Chi-Square Goodness-of-Fit statistic:
          chi^2 = sum_{k=0}^{K-1} ((O_k - E_k)^2 / E_k)
        where:
          O_k = Observed count for tier k
          E_k = Expected count = total_rolls * normalized_probs[k]
        Degrees of freedom: df = K - 1 = 5 - 1 = 4.

        Returns tuple: (chi_square_value, is_statistically_valid, p_interpretation_text)
        """
        if self.total_rolls < 25:
            return 0.0, True, "Sample size too small (<25 rolls) for reliable Chi-Square"

        chi_sq = 0.0
        n_float = float(self.total_rolls)

        for k in range(NUM_TIERS):
            expected = n_float * self.normalized_probs[k]
            # Avoid divide-by-zero on tiny expected values
            safe_expected = max(0.01, expected)
            observed = float(self.observed_counts[k])
            diff = observed - safe_expected
            chi_sq += (diff * diff) / safe_expected

        is_valid = (chi_sq < CHI_SQUARE_CRITICAL_DF4)
        if is_valid:
            interpretation = f"CONVERGED: chi^2={chi_sq:.2f} < 9.488 (p > 0.05, Null Hypothesis holds)"
        else:
            interpretation = f"DIVERGENT: chi^2={chi_sq:.2f} >= 9.488 (p <= 0.05, Significant Bias)"

        return chi_sq, is_valid, interpretation

    def reset_statistics(self):
        """Resets all roll counters, empirical histogram values, and pity counters."""
        for i in range(NUM_TIERS):
            self.observed_counts[i] = 0
        self.total_rolls = 0
        self.lifetime_gold_wealth = 0
        self.pity_counter = 0
        self.last_rolled_tier = TIER_COMMON
        self.last_roll_random_value = 0.0
        self.pity_triggered_last_roll = False
        self.current_streak_tier = -1
        self.current_streak_length = 0
        self.max_legendary_streak = 0
        self.recalculate_distribution()


# ==============================================================================
# BLOCK 2: WORLD SIMULATION & ENTITIES
# ==============================================================================

class PinataSpring:
    """
    Physical Spring-Mass Pendulum Piñata with Rubber Squash-and-Stretch Deformation.

    Physics Formulation:
      - Suspended from ceiling anchor A = (CEILING_ANCHOR_X, CEILING_ANCHOR_Y).
      - Elastic rest length L_0 = 195.0 px.
      - Hooke's Law Restoring Spring Force:
          F_spring = -k_s * (L - L_0) * u_dir
      - Damping:
          F_damping = -c_d * v
      - Restoring Pendulum Center Gravity:
          Pulls bob toward vertical equilibrium under the ceiling anchor.
      - Cartoon Squash-and-Stretch:
          When struck, receives an instantaneous deformation velocity vector.
          Deformation coordinates (scale_x, scale_y) oscillate back to 1.0 via
          a damped harmonic oscillator.
    """
    def __init__(self, anchor_x: float, anchor_y: float):
        self.anchor_x = anchor_x
        self.anchor_y = anchor_y
        self.x = anchor_x
        self.y = anchor_y + 195.0
        self.vx = 0.0
        self.vy = 0.0
        self.rest_length = 195.0
        self.spring_k = 36.0
        self.damping_c = 4.0
        self.gravity_g = 320.0
        self.radius = 48.0

        # Squash and stretch state
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.stretch_vx = 0.0
        self.stretch_vy = 0.0
        self.rubber_k = 180.0
        self.rubber_c = 14.0

        # Visual hit flash and streamers
        self.hit_flash_timer = 0.0
        self.sway_time = 0.0

        # Trailing decorative ribbons (6 hanging strips at base of piñata)
        self.ribbon_offsets_x = [-24.0, -14.0, -4.0, 6.0, 16.0, 26.0]
        self.ribbon_tip_x = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.ribbon_tip_y = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.ribbon_colors = [
            Color(255, 60, 110, 255),
            Color(40, 220, 255, 255),
            Color(255, 220, 40, 255),
            Color(160, 60, 255, 255),
            Color(60, 230, 120, 255),
            Color(255, 140, 30, 255)
        ]
        for i in range(6):
            self.ribbon_tip_x[i] = self.x + self.ribbon_offsets_x[i]
            self.ribbon_tip_y[i] = self.y + 40.0

    def apply_impulse(self, impulse_x: float, impulse_y: float):
        """Applies physical impact impulse and triggers rubber deformation."""
        self.vx += impulse_x
        self.vy += impulse_y
        self.hit_flash_timer = 0.16

        # Squash along impact normal, stretch along perpendicular
        imp_mag = math.sqrt(impulse_x * impulse_x + impulse_y * impulse_y)
        if imp_mag > 0.001:
            nx = impulse_x / imp_mag
            ny = impulse_y / imp_mag
            # Flatten along normal, bulge sideways
            self.stretch_vx += (-nx * 3.5 + ny * 2.0)
            self.stretch_vy += (-ny * 3.5 + nx * 2.0)

    def update(self, dt: float):
        # Cap delta time to prevent spring explosions
        clamped_dt = min(dt, 0.033)
        self.sway_time += clamped_dt

        # 1. Spring-Mass Pendulum Kinematics
        dx = self.x - self.anchor_x
        dy = self.y - self.anchor_y
        dist = math.sqrt(dx * dx + dy * dy)
        dist_safe = max(0.001, dist)
        dir_x = dx / dist_safe
        dir_y = dy / dist_safe

        # Hooke's Law Restoring Spring Force
        displacement = dist - self.rest_length
        f_spring_x = -self.spring_k * displacement * dir_x
        f_spring_y = -self.spring_k * displacement * dir_y

        # Velocity damping
        f_damp_x = -self.damping_c * self.vx
        f_damp_y = -self.damping_c * self.vy

        # Lateral centering pendulum tension (brings bob directly under anchor)
        f_pendulum_x = -24.0 * (self.x - self.anchor_x)

        # Downward gravity
        f_grav_y = self.gravity_g

        # Integrate spring acceleration
        acc_x = f_spring_x + f_damp_x + f_pendulum_x
        acc_y = f_spring_y + f_damp_y + f_grav_y

        self.vx += acc_x * clamped_dt
        self.vy += acc_y * clamped_dt
        self.x += self.vx * clamped_dt
        self.y += self.vy * clamped_dt

        # Keep within screen bounds
        if self.x < ARENA_LEFT + 60.0:
            self.x = ARENA_LEFT + 60.0
            self.vx = -self.vx * 0.4
        elif self.x > ARENA_RIGHT - 60.0:
            self.x = ARENA_RIGHT - 60.0
            self.vx = -self.vx * 0.4

        # 2. Rubber Squash-and-Stretch Harmonic Oscillator
        err_x = self.scale_x - 1.0
        err_y = self.scale_y - 1.0
        acc_sx = -self.rubber_k * err_x - self.rubber_c * self.stretch_vx
        acc_sy = -self.rubber_k * err_y - self.rubber_c * self.stretch_vy

        self.stretch_vx += acc_sx * clamped_dt
        self.stretch_vy += acc_sy * clamped_dt
        self.scale_x += self.stretch_vx * clamped_dt
        self.scale_y += self.stretch_vy * clamped_dt

        # Clamp deformation extremes
        self.scale_x = max(0.55, min(1.65, self.scale_x))
        self.scale_y = max(0.55, min(1.65, self.scale_y))

        # Decay hit flash
        if self.hit_flash_timer > 0.0:
            self.hit_flash_timer = max(0.0, self.hit_flash_timer - clamped_dt)

        # 3. Trailing Ribbons Physics (Follower lag with sine wave flutter)
        for i in range(6):
            base_attach_x = self.x + self.ribbon_offsets_x[i] * self.scale_x
            base_attach_y = self.y + 36.0 * self.scale_y

            wind_flutter = math.sin(self.sway_time * 6.0 + float(i) * 1.1) * 12.0
            target_tip_x = base_attach_x + wind_flutter - (self.vx * 0.08)
            target_tip_y = base_attach_y + 44.0 - (self.vy * 0.04)

            # Smooth exponential follow
            self.ribbon_tip_x[i] += (target_tip_x - self.ribbon_tip_x[i]) * min(1.0, 18.0 * clamped_dt)
            self.ribbon_tip_y[i] += (target_tip_y - self.ribbon_tip_y[i]) * min(1.0, 18.0 * clamped_dt)

    def draw(self):
        """Draws the braided suspension rope, colorful piñata body, and fluttering streamers."""
        # 1. Draw Braided Suspension Rope
        steps = 14
        prev_rx = self.anchor_x
        prev_ry = self.anchor_y
        for s in range(1, steps + 1):
            t = float(s) / float(steps)
            curr_rx = self.anchor_x + (self.x - self.anchor_x) * t
            curr_ry = self.anchor_y + (self.y - 42.0 * self.scale_y - self.anchor_y) * t
            # Slight catenary sag curve
            sag = math.sin(t * 3.14159) * 4.0
            draw_line(int(prev_rx), int(prev_ry + sag), int(curr_rx), int(curr_ry + sag), Color(210, 190, 140, 255))
            prev_rx = curr_rx
            prev_ry = curr_ry

        # Draw ceiling anchor eyelet ring
        draw_circle(int(self.anchor_x), int(self.anchor_y), 7, Color(160, 170, 185, 255))
        draw_circle(int(self.anchor_x), int(self.anchor_y), 4, Color(30, 36, 50, 255))

        # 2. Draw Trailing Streamers / Ribbons
        for i in range(6):
            base_x = self.x + self.ribbon_offsets_x[i] * self.scale_x
            base_y = self.y + 36.0 * self.scale_y
            tip_x = self.ribbon_tip_x[i]
            tip_y = self.ribbon_tip_y[i]
            col = self.ribbon_colors[i]
            draw_line(int(base_x), int(base_y), int(tip_x), int(tip_y), col)
            draw_circle(int(tip_x), int(tip_y), 3, col)

        # 3. Draw Multi-Layered Candy-Striped Piñata Donkey/Star Body
        cx = int(self.x)
        cy = int(self.y)
        rad_x = int(self.radius * self.scale_x)
        rad_y = int(self.radius * self.scale_y)

        # Flash white on hit
        if self.hit_flash_timer > 0.0:
            flash_intensity = int((self.hit_flash_timer / 0.16) * 255.0)
            flash_col = Color(255, 255, 255, flash_intensity)
            draw_ellipse(cx, cy, rad_x + 8, rad_y + 8, flash_col)

        # Base body oval
        draw_ellipse(cx, cy, rad_x, rad_y, Color(35, 42, 60, 255))

        # Horizontal Papier-Mâché Candy Stripes (5 colorful horizontal sections)
        stripe_colors = [
            Color(255, 65, 110, 255),  # Hot Pink
            Color(255, 160, 25, 255),  # Tangerine
            Color(255, 225, 45, 255),  # Bright Gold
            Color(40, 225, 120, 255),  # Emerald Lime
            Color(45, 185, 255, 255),  # Sky Cyan
        ]
        num_stripes = 5
        stripe_height = (rad_y * 2) // num_stripes
        for s in range(num_stripes):
            sy = cy - rad_y + s * stripe_height
            # Calculate width at this slice using ellipse formula: (y/b)^2 + (x/a)^2 <= 1
            mid_y = sy + stripe_height // 2 - cy
            rel_y = abs(mid_y) / max(1.0, float(rad_y))
            if rel_y < 1.0:
                span_x = int(math.sqrt(1.0 - rel_y * rel_y) * float(rad_x))
                draw_rectangle(cx - span_x, sy, span_x * 2, stripe_height, stripe_colors[s])

        # Piñata Body Contour Outline
        draw_ellipse_lines(cx, cy, rad_x, rad_y, Color(240, 245, 255, 220))

        # Festive Donkey Head / Horn Cones
        horn_left_x = cx - int(24.0 * self.scale_x)
        horn_right_x = cx + int(24.0 * self.scale_x)
        horn_top_y = cy - int(48.0 * self.scale_y)

        # Left Papier-Mâché Ear
        v1_l = Vector2(float(horn_left_x - 14), float(cy - int(24 * self.scale_y)))
        v2_l = Vector2(float(horn_left_x), float(cy - int(20 * self.scale_y)))
        v3_l = Vector2(float(horn_left_x - 8), float(horn_top_y - 12))
        draw_triangle(v1_l, v2_l, v3_l, Color(255, 70, 120, 255))

        # Right Papier-Mâché Ear
        v1_r = Vector2(float(horn_right_x), float(cy - int(20 * self.scale_y)))
        v2_r = Vector2(float(horn_right_x + 14), float(cy - int(24 * self.scale_y)))
        v3_r = Vector2(float(horn_right_x + 8), float(horn_top_y - 12))
        draw_triangle(v1_r, v2_r, v3_r, Color(45, 185, 255, 255))

        # Central Golden Star Emblem
        draw_circle(cx, cy, max(4, int(11 * min(self.scale_x, self.scale_y))), Color(255, 215, 30, 255))
        draw_circle(cx, cy, max(2, int(6 * min(self.scale_x, self.scale_y))), Color(255, 255, 255, 255))


class BatPlayer:
    """
    Player Bat Controller supporting simultaneous Keyboard/Mouse and Gamepad.
    Rotates around hand pivot and swings along a fast parabolic arc.
    """
    def __init__(self):
        self.x = 480.0
        self.y = 300.0
        self.aim_angle = 0.0          # Angle in radians facing piñata
        self.bat_length = 68.0
        self.bat_width = 12.0

        # Swing Animation State Machine (C++: enum class SwingState { Idle, Windup, Swing, Recover })
        self.SWING_IDLE = 0
        self.SWING_ACTIVE = 1
        self.SWING_RECOVER = 2
        self.state = self.SWING_IDLE
        self.swing_timer = 0.0
        self.swing_duration = 0.14
        self.current_swing_offset_angle = 0.0
        self.hit_registered_this_swing = False

        # Visual motion blur trail
        self.trail_angles = [0.0, 0.0, 0.0, 0.0, 0.0]

    def trigger_swing(self):
        """Initiates a full bat swing."""
        if self.state == self.SWING_IDLE:
            self.state = self.SWING_ACTIVE
            self.swing_timer = 0.0
            self.hit_registered_this_swing = False

    def update(self, dt: float, pinata_x: float, pinata_y: float):
        # 1. Position Input (WASD / Left Stick / Mouse Cursor)
        move_vec = get_dual_move_2d()
        speed = 460.0
        self.x += move_vec.x * speed * dt
        self.y += move_vec.y * speed * dt

        # Also blend smoothly toward mouse if mouse is moving
        mouse_pos = get_mouse_position()
        dx_m = mouse_pos.x - self.x
        dy_m = mouse_pos.y - self.y
        dist_to_mouse = math.sqrt(dx_m * dx_m + dy_m * dy_m)
        if dist_to_mouse > 4.0 and (is_mouse_button_down(MOUSE_BUTTON_LEFT) or dist_to_mouse < 300.0):
            # Follow mouse with soft spring
            self.x += (mouse_pos.x - self.x) * min(1.0, 16.0 * dt)
            self.y += (mouse_pos.y - self.y) * min(1.0, 16.0 * dt)

        # Arena Clamping
        self.x = max(ARENA_LEFT + 80.0, min(ARENA_RIGHT - 80.0, self.x))
        self.y = max(140.0, min(ARENA_FLOOR_Y - 40.0, self.y))

        # 2. Aiming Angle: Face Piñata or use Right Stick
        look_vec = get_dual_look_2d()
        look_mag = math.sqrt(look_vec.x * look_vec.x + look_vec.y * look_vec.y)
        if look_mag > 0.2:
            self.aim_angle = math.atan2(look_vec.y, look_vec.x)
        else:
            # Face directly toward Piñata bob
            dx = pinata_x - self.x
            dy = pinata_y - self.y
            self.aim_angle = math.atan2(dy, dx)

        # 3. Advance Swing State Machine
        if self.state == self.SWING_ACTIVE:
            self.swing_timer += dt
            t = min(1.0, self.swing_timer / self.swing_duration)
            # Fast cubic swing arc from -65 deg to +70 deg
            # Smooth cubic curve: 3t^2 - 2t^3
            ease_t = 3.0 * t * t - 2.0 * t * t * t
            self.current_swing_offset_angle = -1.13 + ease_t * 2.35

            if t >= 1.0:
                self.state = self.SWING_RECOVER
                self.swing_timer = 0.0
        elif self.state == self.SWING_RECOVER:
            self.swing_timer += dt
            recover_dur = 0.12
            t = min(1.0, self.swing_timer / recover_dur)
            # Smooth return to neutral angle
            self.current_swing_offset_angle = 1.22 * (1.0 - t)
            if t >= 1.0:
                self.state = self.SWING_IDLE
                self.current_swing_offset_angle = 0.0
        else:
            self.current_swing_offset_angle = 0.0

        # Update motion blur trailing angles
        effective_angle = self.aim_angle + self.current_swing_offset_angle
        for i in range(4, 0, -1):
            self.trail_angles[i] = self.trail_angles[i - 1]
        self.trail_angles[0] = effective_angle

    def get_bat_tip_position(self):
        """Returns the world-space (x, y) coordinates of the bat's hitting tip."""
        effective_angle = self.aim_angle + self.current_swing_offset_angle
        tip_x = self.x + math.cos(effective_angle) * self.bat_length
        tip_y = self.y + math.sin(effective_angle) * self.bat_length
        return tip_x, tip_y

    def draw(self):
        """Draws player bat, grip wrap, and translucent swing trail."""
        effective_angle = self.aim_angle + self.current_swing_offset_angle
        tip_x, tip_y = self.get_bat_tip_position()

        # 1. Translucent Motion Blur Swing Fan Trail
        if self.state == self.SWING_ACTIVE:
            for i in range(4):
                ang_a = self.trail_angles[i]
                ang_b = self.trail_angles[i + 1]
                p1 = Vector2(float(self.x), float(self.y))
                p2 = Vector2(float(self.x + math.cos(ang_a) * (self.bat_length + 6.0)),
                             float(self.y + math.sin(ang_a) * (self.bat_length + 6.0)))
                p3 = Vector2(float(self.x + math.cos(ang_b) * (self.bat_length + 6.0)),
                             float(self.y + math.sin(ang_b) * (self.bat_length + 6.0)))
                alpha = int(90.0 * (1.0 - float(i) * 0.22))
                draw_triangle(p1, p2, p3, Color(255, 230, 140, alpha))

        # 2. Bat Body (Wooden Louisville Slugger cylinder with tapered grip)
        perp_x = -math.sin(effective_angle)
        perp_y = math.cos(effective_angle)
        half_w = self.bat_width * 0.5

        # Barrel tip
        v_tip_l = Vector2(float(tip_x + perp_x * half_w), float(tip_y + perp_y * half_w))
        v_tip_r = Vector2(float(tip_x - perp_x * half_w), float(tip_y - perp_y * half_w))

        # Handle grip base
        grip_x = self.x + math.cos(effective_angle) * 16.0
        grip_y = self.y + math.sin(effective_angle) * 16.0
        v_grip_l = Vector2(float(grip_x + perp_x * (half_w * 0.5)), float(grip_y + perp_y * (half_w * 0.5)))
        v_grip_r = Vector2(float(grip_x - perp_x * (half_w * 0.5)), float(grip_y - perp_y * (half_w * 0.5)))

        # Draw wooden barrel quad
        draw_triangle(v_grip_l, v_tip_l, v_tip_r, Color(225, 175, 105, 255))
        draw_triangle(v_grip_l, v_tip_r, v_grip_r, Color(195, 140, 75, 255))

        # Bat grip tape (Leather wrap)
        draw_line(int(self.x), int(self.y), int(grip_x), int(grip_y), Color(160, 50, 40, 255))
        draw_circle(int(self.x), int(self.y), 5, Color(220, 70, 60, 255))

        # Bat tip knob
        draw_circle(int(tip_x), int(tip_y), int(half_w), Color(245, 195, 125, 255))


class LootGem:
    """
    Ballistic Loot Gem Drop with Ground Bouncing, Sparkle Trails, and Tier Glow.
    Maps to a fixed C++ struct inside a contiguous pre-allocated array.
    """
    def __init__(self):
        self.active = False
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.tier_id = TIER_COMMON
        self.gold_value = 1
        self.radius = 8.0
        self.life = 0.0
        self.max_life = 6.0
        self.bounce_count = 0
        self.settled = False
        self.rot_angle = 0.0
        self.rot_speed = 0.0

    def spawn(self, x: float, y: float, vx: float, vy: float, tier_id: int, gold_value: int):
        self.active = True
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.tier_id = tier_id
        self.gold_value = gold_value
        self.life = 0.0
        self.max_life = 6.5
        self.bounce_count = 0
        self.settled = False
        self.rot_angle = random.uniform(0.0, 6.28)
        self.rot_speed = random.uniform(-8.0, 8.0)

        # Tier radius scaling
        radii = [7.0, 8.0, 9.5, 11.5, 14.0]
        self.radius = radii[tier_id]

    def update(self, dt: float):
        if not self.active:
            return

        self.life += dt
        if self.life >= self.max_life:
            self.active = False
            return

        if not self.settled:
            # Gravity acceleration
            self.vy += 540.0 * dt
            self.x += self.vx * dt
            self.y += self.vy * dt
            self.rot_angle += self.rot_speed * dt

            # Ground collision at ARENA_FLOOR_Y
            if self.y >= ARENA_FLOOR_Y - self.radius:
                self.y = ARENA_FLOOR_Y - self.radius
                self.vy = -self.vy * 0.52   # Restitution coefficient
                self.vx = self.vx * 0.74   # Ground friction
                self.bounce_count += 1
                self.rot_speed *= 0.65

                # Rest condition
                if abs(self.vy) < 28.0 and abs(self.vx) < 18.0:
                    self.vy = 0.0
                    self.vx = 0.0
                    self.settled = True

            # Arena wall bounce
            if self.x < ARENA_LEFT + self.radius:
                self.x = ARENA_LEFT + self.radius
                self.vx = -self.vx * 0.6
            elif self.x > ARENA_RIGHT - self.radius:
                self.x = ARENA_RIGHT - self.radius
                self.vx = -self.vx * 0.6

    def draw(self, tiers: list):
        if not self.active:
            return

        cfg = tiers[self.tier_id]
        cx = int(self.x)
        cy = int(self.y)
        rad = int(self.radius)

        # Alpha fadeout over final 1.5 seconds
        alpha = 255
        if self.life > self.max_life - 1.5:
            fade_t = (self.max_life - self.life) / 1.5
            alpha = max(0, min(255, int(fade_t * 255.0)))

        # Outer pulsing glow halo for Rare, Epic, Legendary
        if self.tier_id >= TIER_RARE:
            glow_rad = rad + int(4.0 + math.sin(self.life * 8.0) * 2.0)
            glow_col = Color(cfg.glow_color.r, cfg.glow_color.g, cfg.glow_color.b, min(alpha, 120))
            draw_circle(cx, cy, glow_rad, glow_col)

        # Faceted Diamond Gem Geometry
        col_main = Color(cfg.primary_color.r, cfg.primary_color.g, cfg.primary_color.b, alpha)
        col_highlight = Color(255, 255, 255, alpha)

        p_top = Vector2(float(cx), float(cy - rad))
        p_bot = Vector2(float(cx), float(cy + rad))
        p_left = Vector2(float(cx - rad), float(cy))
        p_right = Vector2(float(cx + rad), float(cy))

        # Diamond 4-triangle facet render
        draw_triangle(p_top, p_left, Vector2(float(cx), float(cy)), col_main)
        draw_triangle(p_top, Vector2(float(cx), float(cy)), p_right, col_highlight)
        draw_triangle(Vector2(float(cx), float(cy)), p_left, p_bot, col_main)
        draw_triangle(Vector2(float(cx), float(cy)), p_bot, p_right, col_main)

        # Highlight facet glint
        draw_circle(cx - 2, cy - 2, max(1, rad // 3), Color(255, 255, 255, alpha))


class LootGemPool:
    """
    Fixed-Capacity Zero-Allocation Pool for Loot Gems.
    Rule 4 & AGENTS.md compliant: Pre-allocates 128 items at startup.
    """
    def __init__(self, capacity: int = 128):
        self.capacity = capacity
        self.gems = []
        for _ in range(capacity):
            self.gems.append(LootGem())

    def spawn(self, x: float, y: float, vx: float, vy: float, tier_id: int, gold_value: int) -> bool:
        for i in range(self.capacity):
            if not self.gems[i].active:
                self.gems[i].spawn(x, y, vx, vy, tier_id, gold_value)
                return True
        return False

    def update(self, dt: float):
        for i in range(self.capacity):
            if self.gems[i].active:
                self.gems[i].update(dt)

    def draw(self, tiers: list):
        for i in range(self.capacity):
            if self.gems[i].active:
                self.gems[i].draw(tiers)

    def clear(self):
        for i in range(self.capacity):
            self.gems[i].active = False


class ConfettiParticle:
    """Confetti spark emitted when piñata is hit or rare items drop."""
    def __init__(self):
        self.active = False
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.color = Color(255, 255, 255, 255)
        self.life = 0.0
        self.max_life = 1.0
        self.size = 4.0

    def spawn(self, x: float, y: float, vx: float, vy: float, color: Color, max_life: float):
        self.active = True
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.life = 0.0
        self.max_life = max_life
        self.size = random.uniform(3.0, 6.0)

    def update(self, dt: float):
        if not self.active:
            return
        self.life += dt
        if self.life >= self.max_life:
            self.active = False
            return
        self.vy += 320.0 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self):
        if not self.active:
            return
        fade = 1.0 - (self.life / self.max_life)
        alpha = max(0, min(255, int(fade * 255.0)))
        col = Color(self.color.r, self.color.g, self.color.b, alpha)
        draw_rectangle(int(self.x), int(self.y), int(self.size), int(self.size), col)


class ConfettiPool:
    """Pre-allocated pool of 256 celebratory confetti particles."""
    def __init__(self, capacity: int = 256):
        self.capacity = capacity
        self.particles = []
        for _ in range(capacity):
            self.particles.append(ConfettiParticle())

    def burst(self, x: float, y: float, count: int, base_color: Color):
        spawned = 0
        for i in range(self.capacity):
            if not self.particles[i].active:
                angle = random.uniform(0.0, 6.28)
                speed = random.uniform(120.0, 420.0)
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed - 90.0
                life = random.uniform(0.6, 1.4)
                self.particles[i].spawn(x, y, vx, vy, base_color, life)
                spawned += 1
                if spawned >= count:
                    break

    def update(self, dt: float):
        for i in range(self.capacity):
            if self.particles[i].active:
                self.particles[i].update(dt)

    def draw(self):
        for i in range(self.capacity):
            if self.particles[i].active:
                self.particles[i].draw()


class FloatingTextSplat:
    """Floating combat text notification for drop announcements."""
    def __init__(self):
        self.active = False
        self.text = ""
        self.x = 0.0
        self.y = 0.0
        self.color = Color(255, 255, 255, 255)
        self.life = 0.0
        self.max_life = 1.2
        self.font_size = 18

    def spawn(self, text: str, x: float, y: float, color: Color, font_size: int = 18):
        self.active = True
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.life = 0.0
        self.max_life = 1.2
        self.font_size = font_size

    def update(self, dt: float):
        if not self.active:
            return
        self.life += dt
        if self.life >= self.max_life:
            self.active = False
            return
        self.y -= 40.0 * dt

    def draw(self):
        if not self.active:
            return
        fade = 1.0 - (self.life / self.max_life)
        alpha = max(0, min(255, int(fade * 255.0)))
        col = Color(self.color.r, self.color.g, self.color.b, alpha)
        draw_text(self.text, int(self.x), int(self.y), self.font_size, col)


class FloatingTextPool:
    """Pre-allocated pool of 32 floating text notifications."""
    def __init__(self, capacity: int = 32):
        self.capacity = capacity
        self.texts = []
        for _ in range(capacity):
            self.texts.append(FloatingTextSplat())

    def spawn(self, text: str, x: float, y: float, color: Color, font_size: int = 18):
        for i in range(self.capacity):
            if not self.texts[i].active:
                self.texts[i].spawn(text, x, y, color, font_size)
                break

    def update(self, dt: float):
        for i in range(self.capacity):
            if self.texts[i].active:
                self.texts[i].update(dt)

    def draw(self):
        for i in range(self.capacity):
            if self.texts[i].active:
                self.texts[i].draw()


# ==============================================================================
# BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY
# ==============================================================================

class TelemetryOverlay:
    """
    Renders the live educational telemetry panel:
      1. Real-time Frequency Histogram comparing observed % vs theoretical CDF %.
      2. Exact Numerical CDF Range Table [C_{k-1}, C_k).
      3. Pearson's Chi-Square (chi^2) Goodness-of-Fit Statistic and P-Value validation.
      4. Dynamic Pity Escalation Meter & Bad Luck Prevention tracking.
      5. Macro Economy Lifetime Ledger.
    """
    def __init__(self):
        pass

    def draw(self, engine: CdfLootEngine):
        # 1. Semi-translucent dark backdrop panel (Bottom-Half Telemetry Hub)
        panel_x = 32
        panel_y = 390
        panel_w = 1216
        panel_h = 295

        draw_rectangle(panel_x, panel_y, panel_w, panel_h, Color(12, 16, 26, 240))
        draw_rectangle_lines(panel_x, panel_y, panel_w, panel_h, Color(45, 65, 95, 255))

        # Panel Header
        draw_rectangle(panel_x, panel_y, panel_w, 28, Color(22, 32, 52, 255))
        draw_text("X-RAY TELEMETRY: CUMULATIVE DISTRIBUTION FUNCTION (CDF) & FREQUENCY HISTOGRAM",
                  panel_x + 14, panel_y + 7, 14, Color(0, 225, 255, 255))
        draw_text("[Tab] Close Overlay", panel_x + panel_w - 150, panel_y + 7, 12, Color(150, 175, 205, 255))

        # ----------------------------------------------------------------------
        # COLUMN A: REAL-TIME FREQUENCY HISTOGRAM (Observed % vs Target CDF %)
        # ----------------------------------------------------------------------
        col_a_x = panel_x + 16
        col_a_y = panel_y + 36

        draw_text("EMPIRICAL FREQUENCY HISTOGRAM (N = %d Rolls)" % engine.total_rolls,
                  col_a_x, col_a_y, 13, Color(255, 215, 60, 255))

        hist_bar_max_w = 260
        hist_row_h = 24
        bar_start_y = col_a_y + 22

        n_safe = max(1, engine.total_rolls)

        for k in range(NUM_TIERS):
            ry = bar_start_y + k * (hist_row_h + 12)
            cfg = engine.tiers[k]

            # Tier Name Label & Color Tag
            draw_rectangle(col_a_x, ry, 10, hist_row_h, cfg.primary_color)
            draw_text(f"{cfg.name:<9}", col_a_x + 16, ry + 4, 12, cfg.primary_color)

            # Bar Slot Background
            slot_x = col_a_x + 95
            draw_rectangle(slot_x, ry, hist_bar_max_w, hist_row_h, Color(25, 34, 52, 255))
            draw_rectangle_lines(slot_x, ry, hist_bar_max_w, hist_row_h, Color(50, 70, 100, 255))

            # Observed Empirical Bar Fill
            obs_pct = float(engine.observed_counts[k]) / float(n_safe)
            fill_w = int(obs_pct * float(hist_bar_max_w))
            fill_w = min(hist_bar_max_w, max(0, fill_w))
            draw_rectangle(slot_x, ry, fill_w, hist_row_h, cfg.primary_color)

            # Theoretical Expected Target Marker (Bright White Vertical Tick)
            exp_pct = engine.normalized_probs[k]
            exp_marker_x = slot_x + int(exp_pct * float(hist_bar_max_w))
            draw_line(exp_marker_x, ry - 3, exp_marker_x, ry + hist_row_h + 3, Color(255, 255, 255, 255))
            draw_line(exp_marker_x + 1, ry - 3, exp_marker_x + 1, ry + hist_row_h + 3, Color(255, 255, 255, 255))

            # Readout Text: Observed vs Expected & Delta
            delta_pct = (obs_pct - exp_pct) * 100.0
            sign_str = "+" if delta_pct >= 0.0 else ""
            readout = f"Obs:{obs_pct * 100.0:5.1f}% | Exp:{exp_pct * 100.0:5.1f}% ({sign_str}{delta_pct:4.1f}%)"
            delta_col = Color(160, 230, 160, 255) if abs(delta_pct) < 3.0 else Color(255, 140, 100, 255)
            draw_text(readout, slot_x + hist_bar_max_w + 10, ry + 4, 11, delta_col)

        # ----------------------------------------------------------------------
        # COLUMN B: CUMULATIVE DISTRIBUTION FUNCTION (CDF) TABLE
        # ----------------------------------------------------------------------
        col_b_x = panel_x + 590
        col_b_y = panel_y + 36

        draw_text("CUMULATIVE INTERVALS [C_{k-1}, C_k) & NORMALIZED PROBABILITIES",
                  col_b_x, col_b_y, 13, Color(255, 215, 60, 255))

        table_y = col_b_y + 22
        # Header row
        draw_rectangle(col_b_x, table_y, 600, 18, Color(28, 40, 64, 255))
        draw_text("TIER", col_b_x + 8, table_y + 3, 11, Color(160, 185, 215, 255))
        draw_text("BASE WT", col_b_x + 90, table_y + 3, 11, Color(160, 185, 215, 255))
        draw_text("EFF WT", col_b_x + 160, table_y + 3, 11, Color(160, 185, 215, 255))
        draw_text("P(k)", col_b_x + 230, table_y + 3, 11, Color(160, 185, 215, 255))
        draw_text("CDF INTERVAL [C_k-1, C_k)", col_b_x + 290, table_y + 3, 11, Color(160, 185, 215, 255))
        draw_text("DROPS", col_b_x + 480, table_y + 3, 11, Color(160, 185, 215, 255))
        draw_text("OBS %", col_b_x + 540, table_y + 3, 11, Color(160, 185, 215, 255))

        prev_cumulative = 0.0
        for k in range(NUM_TIERS):
            row_y = table_y + 20 + k * 20
            cfg = engine.tiers[k]

            # Highlight currently rolled tier
            is_recent = (engine.last_rolled_tier == k)
            bg_col = Color(35, 52, 85, 255) if is_recent else Color(18, 25, 40, 255)
            draw_rectangle(col_b_x, row_y, 600, 18, bg_col)

            # Tier Name
            draw_text(cfg.name, col_b_x + 8, row_y + 3, 11, cfg.primary_color)

            # Base Weight
            draw_text(f"{cfg.base_weight:6.0f}", col_b_x + 90, row_y + 3, 11, Color(210, 220, 235, 255))

            # Effective Weight
            draw_text(f"{engine.effective_weights[k]:6.1f}", col_b_x + 160, row_y + 3, 11, Color(255, 230, 120, 255))

            # Probability P(k)
            draw_text(f"{engine.normalized_probs[k] * 100.0:5.2f}%", col_b_x + 230, row_y + 3, 11, Color(120, 240, 255, 255))

            # Cumulative Interval
            curr_cumulative = engine.cumulative_weights[k]
            draw_text(f"[{prev_cumulative:6.1f} .. {curr_cumulative:6.1f})", col_b_x + 290, row_y + 3, 11, Color(200, 215, 235, 255))
            prev_cumulative = curr_cumulative

            # Drops Count
            draw_text(f"{engine.observed_counts[k]:5d}", col_b_x + 480, row_y + 3, 11, Color(240, 245, 255, 255))

            # Empirical Frequency %
            obs_pct = (float(engine.observed_counts[k]) / float(n_safe)) * 100.0
            draw_text(f"{obs_pct:5.1f}%", col_b_x + 540, row_y + 3, 11, cfg.primary_color)

        # ----------------------------------------------------------------------
        # BOTTOM ROW: CHI-SQUARE GOODNESS-OF-FIT & PITY STATUS
        # ----------------------------------------------------------------------
        stat_box_y = panel_y + 195
        stat_box_w = 1184
        stat_box_h = 88
        draw_rectangle(col_a_x, stat_box_y, stat_box_w, stat_box_h, Color(18, 25, 42, 255))
        draw_rectangle_lines(col_a_x, stat_box_y, stat_box_w, stat_box_h, Color(45, 65, 95, 255))

        # 1. Pearson's Chi-Square Test Readout
        chi_val, chi_pass, chi_text = engine.compute_chi_square()
        badge_col = Color(50, 230, 120, 255) if chi_pass else Color(255, 95, 80, 255)

        draw_text("PEARSON CHI-SQUARE (chi^2) GOODNESS-OF-FIT (df = 4, alpha = 0.05):",
                  col_a_x + 12, stat_box_y + 8, 12, Color(255, 215, 60, 255))
        draw_text(f"Computed chi^2 = {chi_val:7.2f}  |  Critical Threshold = {CHI_SQUARE_CRITICAL_DF4}",
                  col_a_x + 12, stat_box_y + 26, 12, Color(220, 235, 255, 255))
        draw_text(f"Status: {chi_text}", col_a_x + 12, stat_box_y + 44, 12, badge_col)

        # 2. Pity System Meter
        pity_x = col_a_x + 620
        draw_text("BAD LUCK PITY COUNTER:", pity_x, stat_box_y + 8, 12, Color(255, 215, 60, 255))

        pity_str = f"Dry Rolls: {engine.pity_counter} / {engine.pity_hard_threshold} (Hard Pity)"
        draw_text(pity_str, pity_x, stat_box_y + 26, 12, Color(240, 245, 255, 255))

        # Pity Bar Fill
        pity_bar_w = 260
        pity_ratio = min(1.0, float(engine.pity_counter) / float(engine.pity_hard_threshold))
        draw_rectangle(pity_x, stat_box_y + 46, pity_bar_w, 14, Color(30, 40, 60, 255))
        draw_rectangle(pity_x, stat_box_y + 46, int(pity_ratio * float(pity_bar_w)), 14, Color(255, 205, 30, 255))
        draw_rectangle_lines(pity_x, stat_box_y + 46, pity_bar_w, 14, Color(60, 80, 115, 255))

        # Soft pity marker at 40/70
        soft_marker_x = pity_x + int((40.0 / 70.0) * float(pity_bar_w))
        draw_line(soft_marker_x, stat_box_y + 42, soft_marker_x, stat_box_y + 64, Color(255, 100, 100, 255))
        draw_text("Soft Pity (40)", soft_marker_x - 30, stat_box_y + 66, 10, Color(255, 140, 140, 255))

        # Pity state announcement
        if engine.pity_counter >= engine.pity_hard_threshold:
            pity_status_text = "HARD PITY: Next roll GUARANTEED LEGENDARY (100%)"
            pity_status_col = Color(255, 215, 30, 255)
        elif engine.pity_counter >= engine.pity_soft_threshold:
            pity_status_text = f"SOFT PITY ACTIVE: Legendary weight boosted (+{(engine.pity_counter - 40) * 14} wt)"
            pity_status_col = Color(255, 165, 40, 255)
        else:
            pity_status_text = "PITY: Normal baseline rates"
            pity_status_col = Color(140, 165, 195, 255)
        draw_text(pity_status_text, pity_x + pity_bar_w + 14, stat_box_y + 46, 11, pity_status_col)

        # 3. Economy Wealth Readout
        draw_text(f"Total Wealth: {engine.lifetime_gold_wealth:,} Gold",
                  col_a_x + 12, stat_box_y + 66, 11, Color(255, 225, 80, 255))
        avg_gold = float(engine.lifetime_gold_wealth) / float(n_safe)
        draw_text(f"Avg/Roll: {avg_gold:.1f} Gold",
                  col_a_x + 220, stat_box_y + 66, 11, Color(160, 220, 255, 255))
        draw_text(f"Max Legendary Streak: {engine.max_legendary_streak}",
                  col_a_x + 400, stat_box_y + 66, 11, Color(255, 180, 255, 255))


# ==============================================================================
# BLOCK 4: MAIN GAME LOOP & AUTOMATED SMOKE TEST
# ==============================================================================

class PatternLabGame:
    """
    Main Game Application Orchestrator for Cumulative Loot Piñata.
    Integrates world physics, audio synthesis, CDF sampling, and Raylib rendering.
    """
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()

        # Procedural Sound Synthesis (In-Memory Audio Assets)
        self.snd_hit = create_hit_sfx()
        self.snd_crit = create_critical_hit_sfx()
        self.snd_coin = create_coin_sfx()
        self.snd_powerup = create_powerup_sfx()
        self.snd_click = create_click_sfx()

        # Core Game Systems
        self.loot_engine = CdfLootEngine()
        self.pinata = PinataSpring(CEILING_ANCHOR_X, CEILING_ANCHOR_Y)
        self.player_bat = BatPlayer()
        self.gem_pool = LootGemPool(128)
        self.confetti_pool = ConfettiPool(256)
        self.text_pool = FloatingTextPool(32)
        self.telemetry = TelemetryOverlay()

        # Interaction & Screen Shake State
        self.show_xray = True
        self.shake_trauma = 0.0
        self.shake_offset_x = 0.0
        self.shake_offset_y = 0.0

    def trigger_loot_explosion(self, hit_x: float, hit_y: float, is_sweet_spot: bool):
        """Rolls loot from CDF engine, launches physical gems, and triggers audiovisual cues."""
        gem_count = 8 if is_sweet_spot else 4

        # Play Audio
        if is_audio_device_ready():
            if is_sweet_spot:
                play_sound(self.snd_crit)
            else:
                play_sound(self.snd_hit)

        # Trigger screen shake
        self.shake_trauma = min(1.0, self.shake_trauma + (0.55 if is_sweet_spot else 0.35))

        # Burst Confetti
        burst_color = Color(255, 215, 30, 255) if is_sweet_spot else Color(255, 80, 140, 255)
        self.confetti_pool.burst(hit_x, hit_y, 24 if is_sweet_spot else 12, burst_color)

        # Sample and spawn individual loot drops
        best_tier = TIER_COMMON
        for _ in range(gem_count):
            tier_id = self.loot_engine.sample_roll()
            if tier_id > best_tier:
                best_tier = tier_id

            # Fountain launch angle (-135 to -45 degrees)
            launch_angle = random.uniform(-2.35, -0.78)
            launch_speed = random.uniform(220.0, 480.0)
            vx = math.cos(launch_angle) * launch_speed
            vy = math.sin(launch_angle) * launch_speed

            gold_val = self.loot_engine.tiers[tier_id].gold_value
            self.gem_pool.spawn(hit_x, hit_y, vx, vy, tier_id, gold_val)

        # Audio celebration for high tier drops
        if is_audio_device_ready():
            if best_tier >= TIER_EPIC:
                play_sound(self.snd_powerup)
            else:
                play_sound(self.snd_coin)

        # Floating Text Splat
        cfg_best = self.loot_engine.tiers[best_tier]
        if is_sweet_spot:
            splat_text = f"CRIT HIT! +{gem_count} GEMS! [{cfg_best.name.upper()}]"
            self.text_pool.spawn(splat_text, hit_x - 60.0, hit_y - 40.0, Color(255, 230, 50, 255), 20)
        else:
            splat_text = f"WHACK! [{cfg_best.name}]"
            self.text_pool.spawn(splat_text, hit_x - 30.0, hit_y - 30.0, cfg_best.primary_color, 16)

    def update(self):
        dt = min(get_frame_time(), 0.05)

        # ----------------------------------------------------------------------
        # 1. INPUT HANDLING & CONTROLS
        # ----------------------------------------------------------------------
        # [Tab] / Gamepad View (Select): Toggle X-Ray Telemetry Overlay
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray

        # [F1] / Gamepad LB: Live Pattern Comparison Toggle (Weighted CDF vs Flat Uniform)
        if is_dual_pattern_toggle_pressed():
            self.loot_engine.use_cdf_pattern = not self.loot_engine.use_cdf_pattern
            self.loot_engine.recalculate_distribution()
            if is_audio_device_ready():
                play_sound(self.snd_click)
            mode_name = "WEIGHTED CDF SAMPLING" if self.loot_engine.use_cdf_pattern else "FLAT UNIFORM RANDOM"
            self.text_pool.spawn(f"ENGINE: {mode_name}", 480, 240, Color(255, 215, 30, 255), 18)

        # [F2] / Gamepad RB: Toggle Bad Luck Pity Escalation System
        if is_dual_secondary_toggle_pressed():
            self.loot_engine.pity_enabled = not self.loot_engine.pity_enabled
            self.loot_engine.recalculate_distribution()
            if is_audio_device_ready():
                play_sound(self.snd_click)
            pity_name = "PITY ESCALATION ENABLED" if self.loot_engine.pity_enabled else "PITY SYSTEM DISABLED"
            self.text_pool.spawn(pity_name, 500, 270, Color(120, 240, 255, 255), 18)

        # [R] / Gamepad Start: Reset Entire Simulation
        if is_dual_reset_pressed():
            self.loot_engine.reset_statistics()
            self.pinata.x = CEILING_ANCHOR_X
            self.pinata.y = CEILING_ANCHOR_Y + 195.0
            self.pinata.vx = 0.0
            self.pinata.vy = 0.0
            self.gem_pool.clear()
            if is_audio_device_ready():
                play_sound(self.snd_click)
            self.text_pool.spawn("SIMULATION RESET", 560, 260, Color(255, 255, 255, 255), 20)

        # [C]: Clear Statistics Only
        if is_key_pressed(KEY_C):
            self.loot_engine.reset_statistics()
            if is_audio_device_ready():
                play_sound(self.snd_click)
            self.text_pool.spawn("STATISTICS CLEARED", 550, 260, Color(255, 220, 100, 255), 18)

        # Monte Carlo Rapid Testing: [E] / Gamepad X (100 rolls), [Q] / Gamepad Y (1,000 rolls)
        if is_key_pressed(KEY_E) or (is_any_gamepad_connected() and is_gamepad_button_pressed(get_active_gamepad_id(), GAMEPAD_BUTTON_RIGHT_FACE_LEFT)):
            self.loot_engine.batch_roll(100)
            if is_audio_device_ready():
                play_sound(self.snd_coin)
            self.text_pool.spawn("+100 BATCH ROLLS (Law of Large Numbers)", 450, 220, Color(100, 240, 160, 255), 18)
            # Spawn a few visual gems for flair
            for _ in range(6):
                t_id = random.randint(0, NUM_TIERS - 1)
                self.gem_pool.spawn(self.pinata.x, self.pinata.y, random.uniform(-200, 200), random.uniform(-350, -100),
                                    t_id, self.loot_engine.tiers[t_id].gold_value)

        if is_key_pressed(KEY_Q) or (is_any_gamepad_connected() and is_gamepad_button_pressed(get_active_gamepad_id(), GAMEPAD_BUTTON_RIGHT_FACE_UP)):
            self.loot_engine.batch_roll(1000)
            if is_audio_device_ready():
                play_sound(self.snd_powerup)
            self.text_pool.spawn("+1,000 MONTE CARLO ROLLS (Convergence Reached!)", 400, 200, Color(255, 215, 30, 255), 20)
            # Burst celebratory confetti
            self.confetti_pool.burst(self.pinata.x, self.pinata.y, 48, Color(255, 215, 30, 255))

        # Adjust Magic Find / Luck: Arrow Up/Down or D-Pad Up/Down
        luck_changed = False
        if is_key_pressed(KEY_UP) or (is_any_gamepad_connected() and is_gamepad_button_pressed(get_active_gamepad_id(), GAMEPAD_BUTTON_LEFT_FACE_UP)):
            self.loot_engine.luck_modifier = min(3.0, self.loot_engine.luck_modifier + 0.25)
            luck_changed = True
        elif is_key_pressed(KEY_DOWN) or (is_any_gamepad_connected() and is_gamepad_button_pressed(get_active_gamepad_id(), GAMEPAD_BUTTON_LEFT_FACE_DOWN)):
            self.loot_engine.luck_modifier = max(0.0, self.loot_engine.luck_modifier - 0.25)
            luck_changed = True

        if luck_changed:
            self.loot_engine.recalculate_distribution()
            if is_audio_device_ready():
                play_sound(self.snd_click)
            mf_pct = int(self.loot_engine.luck_modifier * 100.0)
            self.text_pool.spawn(f"MAGIC FIND: +{mf_pct}%", 560, 290, Color(140, 220, 255, 255), 18)

        # ----------------------------------------------------------------------
        # 2. PLAYER BAT & PIÑATA COLLISION
        # ----------------------------------------------------------------------
        # Strike Piñata: Space / Left Click / RT / Gamepad A
        if is_dual_primary_fire_pressed():
            self.player_bat.trigger_swing()

        self.player_bat.update(dt, self.pinata.x, self.pinata.y)

        # Check collision during active swing phase
        if self.player_bat.state == self.player_bat.SWING_ACTIVE and not self.player_bat.hit_registered_this_swing:
            bat_tip_x, bat_tip_y = self.player_bat.get_bat_tip_position()
            # Segment vs Circle collision using Vector2 structs
            pt_pinata = Vector2(float(self.pinata.x), float(self.pinata.y))
            pt_bat_base = Vector2(float(self.player_bat.x), float(self.player_bat.y))
            pt_bat_tip = Vector2(float(bat_tip_x), float(bat_tip_y))

            close_pt = closest_point_on_segment_2d(pt_pinata, pt_bat_base, pt_bat_tip)
            dist_to_pinata = distance_2d(close_pt, pt_pinata)
            hit_threshold = self.pinata.radius + 14.0

            if dist_to_pinata <= hit_threshold:
                self.player_bat.hit_registered_this_swing = True

                # Impact vector
                hit_dx = self.pinata.x - close_pt.x
                hit_dy = self.pinata.y - close_pt.y
                h_mag = math.sqrt(hit_dx * hit_dx + hit_dy * hit_dy)
                if h_mag < 0.001:
                    hit_dx = 1.0
                    hit_dy = -0.5
                    h_mag = 1.0
                nx = hit_dx / h_mag
                ny = hit_dy / h_mag

                # Sweet spot check (hit near the bat's hitting sweet spot tip)
                dist_to_tip = distance_2d(close_pt, pt_bat_tip)
                is_sweet_spot = (dist_to_tip < 24.0)

                impulse_power = 560.0 if is_sweet_spot else 380.0
                self.pinata.apply_impulse(nx * impulse_power, ny * impulse_power - 120.0)

                # Trigger loot shower
                self.trigger_loot_explosion(close_pt.x, close_pt.y, is_sweet_spot)

        # ----------------------------------------------------------------------
        # 3. ENTITY UPDATES & SHAKE DISSIPATION
        # ----------------------------------------------------------------------
        self.pinata.update(dt)
        self.gem_pool.update(dt)
        self.confetti_pool.update(dt)
        self.text_pool.update(dt)

        # Screen Shake decay
        if self.shake_trauma > 0.0:
            self.shake_trauma = max(0.0, self.shake_trauma - 2.2 * dt)
            shake_amt = self.shake_trauma * self.shake_trauma * 16.0
            self.shake_offset_x = (random.random() * 2.0 - 1.0) * shake_amt
            self.shake_offset_y = (random.random() * 2.0 - 1.0) * shake_amt
        else:
            self.shake_offset_x = 0.0
            self.shake_offset_y = 0.0

    def draw(self):
        begin_drawing()
        clear_background(Color(12, 15, 24, 255))

        # 1. Background Proving Arena Details
        # Wooden overhead support beam
        draw_rectangle(0, 0, SCREEN_WIDTH, 48, Color(24, 30, 44, 255))
        draw_line(0, 48, SCREEN_WIDTH, 48, Color(45, 60, 90, 255))

        # Arena Wall boundaries
        draw_line(int(ARENA_LEFT), 48, int(ARENA_LEFT), int(ARENA_FLOOR_Y), Color(30, 42, 65, 255))
        draw_line(int(ARENA_RIGHT), 48, int(ARENA_RIGHT), int(ARENA_FLOOR_Y), Color(30, 42, 65, 255))

        # Arena Wooden Floor
        draw_rectangle(0, int(ARENA_FLOOR_Y), SCREEN_WIDTH, int(SCREEN_HEIGHT - ARENA_FLOOR_Y), Color(20, 26, 38, 255))
        draw_line(0, int(ARENA_FLOOR_Y), SCREEN_WIDTH, int(ARENA_FLOOR_Y), Color(60, 85, 125, 255))
        for fx in range(60, SCREEN_WIDTH, 90):
            draw_line(fx, int(ARENA_FLOOR_Y), fx, SCREEN_HEIGHT, Color(28, 36, 52, 255))

        # 2. World Entities
        self.confetti_pool.draw()
        self.gem_pool.draw(self.loot_engine.tiers)
        self.pinata.draw()
        self.player_bat.draw()
        self.text_pool.draw()

        # 3. Top Header Information
        draw_text("CUMULATIVE LOOT PIÑATA", 32, 14, 16, Color(255, 215, 30, 255))
        pattern_sub = "SECTION 3.4: PROGRESSION & ECONOMY (CDF SAMPLING & HISTOGRAMS)"
        draw_text(pattern_sub, 32, 32, 10, Color(140, 165, 195, 255))

        # Live Pattern Status Indicator (Top-Left Hub)
        if self.loot_engine.use_cdf_pattern:
            draw_text("PATTERN [F1]: WEIGHTED CDF [BALANCED ECONOMY]", 32, 54, 12, Color(60, 240, 130, 255))
        else:
            draw_text("PATTERN [F1]: FLAT UNIFORM RANDOM [ECONOMY BROKEN!]", 32, 54, 12, Color(255, 90, 90, 255))

        mf_val = int(self.loot_engine.luck_modifier * 100.0)
        draw_text(f"LUCK / MAGIC FIND [Up/Down]: +{mf_val}%", 32, 72, 12, Color(0, 220, 255, 255))

        # 4. Mandatory AGENTS.md Top-Bar HUD Clearance & Controls Badges
        # Keep x = 450..980, y = 14..48 clear for draw_ui_settings_bar(450, 16)
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)

        # 5. Interactive X-Ray Overlay ([Tab])
        if self.show_xray:
            self.telemetry.draw(self.loot_engine)
        else:
            # Compact minimized hint prompt
            draw_rectangle(32, SCREEN_HEIGHT - 34, 460, 24, Color(16, 22, 34, 200))
            draw_rectangle_lines(32, SCREEN_HEIGHT - 34, 460, 24, Color(45, 65, 95, 255))
            draw_text("Press [Tab] / Gamepad Select to Open Full CDF X-Ray Telemetry Hub",
                      42, SCREEN_HEIGHT - 28, 12, Color(200, 225, 255, 255))

        # Bottom Controls Quick Bar
        quick_controls = "Controls: Space/RT: Hit | E/X: Roll 100x | Q/Y: Roll 1,000x | Up/Down: Luck | [F1]: CDF vs Uniform | [R]: Reset"
        draw_text(quick_controls, 32, SCREEN_HEIGHT - 16, 10, Color(130, 150, 175, 255))

        end_drawing()

    def run(self, smoke_test: bool = False):
        frame_count = 0
        while not window_should_close():
            self.update()
            self.draw()
            frame_count += 1
            if smoke_test and frame_count >= 3:
                break

        # Cleanup procedural sound buffers
        if is_audio_device_ready():
            unload_sound(self.snd_hit)
            unload_sound(self.snd_crit)
            unload_sound(self.snd_coin)
            unload_sound(self.snd_powerup)
            unload_sound(self.snd_click)
        close_audio_device()
        close_window()


if __name__ == "__main__":
    is_smoke = "--smoke-test" in sys.argv
    PatternLabGame().run(smoke_test=is_smoke)
