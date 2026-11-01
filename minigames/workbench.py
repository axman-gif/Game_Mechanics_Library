# -*- coding: utf-8 -*-
"""
Workbench - Crafting Recipes & Dependency Graph Architecture
============================================================
Section          : 3.1 Menus & UI
Pattern Category : Menus & User Interface, RPG Progression & Economy
Dimension        : 2D

Problem Solved:
  In RPGs, survival sandboxes, and crafting games (Minecraft, Terraria, Monster Hunter,
  Skyrim, World of Warcraft), players combine raw materials into finished tools, gear,
  and potions. Naive implementations scatter ad-hoc `if/else` checks throughout the codebase,
  causing material duplication glitches, partial state consumption on failure, and lack of
  visual feedback for missing ingredients. Furthermore, without a structured Recipe
  Dependency Graph, players cannot see multi-tier prerequisite craft chains (e.g.
  Ore -> Ingot -> Blade -> Sword) or perform bulk crafting cleanly.

How the Pattern Works:
  1. Declarative Recipe Struct & Dependency Graph:
     Every craftable item is defined by an immutable `CraftingRecipe` struct holding:
       - `result_item_id`, `result_count` (e.g. 5x Arrows per craft)
       - `category` (Equipment, Alchemy, Components)
       - `ingredients: List[IngredientSlot]` (pairs of `item_id` and `required_count`)
       - `tier_req` (Station tier prerequisite)
  2. Dynamic Ingredient Gating & Visual State Evaluation:
     For every recipe, the engine cross-references the player's current stock:
       - Ready (Full Color): All ingredients owned in required amounts.
       - Missing / Greyed Out (Muted Color): Highlights exact deficits (`Iron Ingot: 1 / 3`).
       - Max Craftable: min over all ingredients of (owned_count // required_count).
  3. Atomic Crafting Transaction Pipeline:
     Crafting is an all-or-nothing 3-step operation:
       - Validate: Verifies 100% of required quantities exist before touching state.
       - Atomic Deduction: Deducts (quantity * required_count) for all ingredients.
       - Atomic Award: Grants (quantity * result_count) of the target item.
  4. Recursive Sub-Crafting Engine ([F2]):
     When enabled, if the player lacks intermediate components (e.g. Iron Ingots) but
     owns their raw predecessors (Iron Ore), the engine automatically synthesizes
     sub-tier requirements in topological dependency order!
  5. Interactive Pattern Comparison ([F1] & [Tab]):
     Toggle between Strict Material Gating (Pattern ON) and Free Creative Mode (Pattern OFF)
     to inspect how gating rules protect economy progression.

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - Up / Down (W / S) / Gamepad D-Pad      : Navigate recipe catalog
  - Left / Right (A / D) / Gamepad Stick   : Cycle category tabs ([ALL], [EQUIP], [ALCH], [PARTS])
  - Mouse Click on Recipe                  : Focus recipe for assembly
  - Q / E / Left / Right (on Stepper)      : Adjust bulk craft quantity ([-] / [+])
  - [1], [5], [M] / Gamepad X              : Quick Quantity: 1, 5, or Max Craftable
  - Enter / Space / Gamepad A              : Craft Selected Recipe
  - Keys [1]..[5] / Mouse Click on Rack    : Quick Gather test materials (Wood, Ore, Herbs, Feathers, Leather)
  - [Tab] / Gamepad View (Select)          : Toggle X-Ray Telemetry & Recipe Dependency DAG
  - [F1]  / Gamepad LB                     : Toggle Pattern ON/OFF (Strict Ingredient Gating vs Free Mode)
  - [F2]  / Gamepad RB                     : Toggle Recursive Sub-Crafting (Auto-Synthesize Prerequisites)
  - [Ctrl +/-]                             : Increase / Decrease UI Font Size
  - [F11]                                  : Toggle Fullscreen
  - [R]   / Gamepad Start                  : Reset materials and crafted inventory
"""

import sys
import os
import math
import random
from typing import List, Dict, Tuple, Optional

# 1. Enforce zero __pycache__ generation
sys.dont_write_bytecode = True

# 2. Add repository root to search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 3. Mandatory Raylib & modular workspace imports
from pyray import *
from assets import *
from utils import *

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WINDOW_TITLE = "Workbench - Crafting Recipes & Dependency Graph (Raylib Pattern Lab)"

# UI Palette Constants
COLOR_BG               = Color(12, 16, 26, 255)
COLOR_PANEL_BG         = Color(18, 24, 38, 252)
COLOR_PANEL_BORDER     = Color(45, 60, 92, 255)
COLOR_WOOD_DARK        = Color(55, 38, 26, 255)
COLOR_WOOD_LIGHT       = Color(92, 64, 44, 255)
COLOR_ANVIL_STEEL      = Color(70, 80, 100, 255)

COLOR_SLOT_EMPTY       = Color(14, 19, 30, 255)
COLOR_SLOT_BORDER      = Color(38, 50, 78, 255)
COLOR_SLOT_HOVER       = Color(65, 95, 145, 255)
COLOR_SLOT_SELECTED    = Color(245, 195, 45, 255)
COLOR_SLOT_LOCKED      = Color(22, 26, 36, 200)

COLOR_TEXT_MAIN        = Color(235, 242, 255, 255)
COLOR_TEXT_DIM         = Color(140, 160, 190, 255)
COLOR_GOLD_ACCENT      = Color(255, 205, 55, 255)
COLOR_CYAN_ACCENT      = Color(45, 215, 255, 255)
COLOR_GREEN_READY      = Color(65, 245, 130, 255)
COLOR_RED_MISSING      = Color(255, 80, 80, 255)
COLOR_PURPLE_ACCENT    = Color(195, 95, 255, 255)
COLOR_ORANGE_ACCENT    = Color(255, 145, 50, 255)
COLOR_WHITE            = Color(255, 255, 255, 255)

# Recipe Categories (C++ Enum equivalent)
CAT_ALL        = 0
CAT_EQUIPMENT  = 1
CAT_ALCHEMY    = 2
CAT_COMPONENTS = 3

CATEGORY_NAMES = ["All Recipes", "Equipment", "Alchemy", "Components"]
CATEGORY_COLORS = [
    COLOR_CYAN_ACCENT,
    Color(255, 105, 95, 255),   # Equipment: Vermilion Red
    Color(65, 225, 160, 255),   # Alchemy: Emerald Green
    Color(245, 195, 45, 255),   # Components: Amber Gold
]

# Geometry Layout
PANEL_LEFT_X   = 25
PANEL_LEFT_Y   = 60
PANEL_LEFT_W   = 385
PANEL_LEFT_H   = 645

PANEL_CENTER_X = 425
PANEL_CENTER_Y = 60
PANEL_CENTER_W = 430
PANEL_CENTER_H = 645

PANEL_RIGHT_X  = 870
PANEL_RIGHT_Y  = 60
PANEL_RIGHT_W  = 385
PANEL_RIGHT_H  = 645


# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATION (RECIPES & DEPENDENCY GRAPH)
# ==============================================================================

class ItemDef:
    """
    Plain struct representing an item definition in the world database.
    C++ Equivalent:
      struct ItemDef {
          int item_id;
          char name[32];
          int category;
          int icon_type;
          char description[64];
          bool is_raw_material;
      };
    """
    def __init__(self, item_id: int, name: str, category: int, icon_type: int,
                 description: str, is_raw_material: bool = False):
        self.item_id = item_id
        self.name = name
        self.category = category
        self.icon_type = icon_type
        self.description = description
        self.is_raw_material = is_raw_material


class IngredientSlot:
    """
    Represents an input requirement in a crafting recipe.
    C++ Equivalent:
      struct IngredientSlot {
          int item_id;
          int required_count;
      };
    """
    def __init__(self, item_id: int, required_count: int):
        self.item_id = item_id
        self.required_count = required_count


class CraftingRecipe:
    """
    Declarative representation of a crafting recipe.
    C++ Equivalent:
      struct CraftingRecipe {
          int recipe_id;
          int result_item_id;
          int result_count;
          int category;
          int ingredient_count;
          IngredientSlot ingredients[4];
          int tier_requirement;
      };
    """
    def __init__(self, recipe_id: int, result_item_id: int, result_count: int,
                 category: int, ingredients: List[IngredientSlot], tier_req: int = 1):
        self.recipe_id = recipe_id
        self.result_item_id = result_item_id
        self.result_count = result_count
        self.category = category
        self.ingredients = ingredients
        self.tier_req = tier_req


class RecipeValidationResult:
    """
    Carries the evaluated feasibility state for a candidate recipe.
    C++ Equivalent:
      struct RecipeValidationResult {
          bool can_craft;
          int max_craftable;
          int missing_count;
          int deficit_per_ingredient[4];
      };
    """
    def __init__(self, can_craft: bool, max_craftable: int, deficits: Dict[int, int]):
        self.can_craft = can_craft
        self.max_craftable = max_craftable
        self.deficits = deficits  # item_id -> deficit count (0 if sufficient)


class CraftingEngine:
    """
    Pure algorithmic crafting engine.
    Performs precondition verification, dependency analysis, atomic consumption,
    and recursive sub-crafting without side-effects until commit.
    """
    def __init__(self):
        self.strict_gating_enabled = True     # Pattern ON (Strict) vs OFF (Free Cheat Mode)
        self.recursive_subcraft_enabled = False # Auto-craft intermediate materials if raw exist

    def evaluate_recipe(self, recipe: CraftingRecipe, inventory: Dict[int, int],
                        recipes_by_result: Dict[int, CraftingRecipe]) -> RecipeValidationResult:
        """
        Evaluates whether a recipe can be crafted right now, calculating exact deficits
        and the maximum batch multiplier.
        """
        if not self.strict_gating_enabled:
            # Free creative mode: everything is craftable up to 99
            return RecipeValidationResult(True, 99, {})

        max_batches = 999
        deficits = {}
        all_satisfied = True

        for ing in recipe.ingredients:
            owned = inventory.get(ing.item_id, 0)
            needed = ing.required_count

            # Check if recursive subcrafting can bridge the deficit
            virtual_owned = owned
            if self.recursive_subcraft_enabled and owned < needed:
                sub_recipe = recipes_by_result.get(ing.item_id)
                if sub_recipe:
                    # How many sub-batches can we make from raw inputs?
                    sub_eval = self.evaluate_recipe(sub_recipe, inventory, recipes_by_result)
                    virtual_owned += sub_eval.max_craftable * sub_recipe.result_count

            if virtual_owned < needed:
                all_satisfied = False
                deficits[ing.item_id] = needed - virtual_owned
                max_batches = 0
            else:
                batches_for_ing = virtual_owned // needed
                if batches_for_ing < max_batches:
                    max_batches = batches_for_ing

        if max_batches == 999:
            max_batches = 0

        can_craft = all_satisfied and (max_batches > 0)
        return RecipeValidationResult(can_craft, max_batches, deficits)

    def execute_craft(
        self,
        recipe: CraftingRecipe,
        batch_count: int,
        inventory: Dict[int, int],
        recipes_by_result: Dict[int, CraftingRecipe]
    ) -> bool:
        """
        Stage 3: Atomic execution.
        Performs all deductions and grants result in a single consistent transaction.
        """
        if batch_count <= 0:
            return False

        eval_res = self.evaluate_recipe(recipe, inventory, recipes_by_result)
        if not eval_res.can_craft and self.strict_gating_enabled:
            return False

        if self.strict_gating_enabled:
            # First, handle recursive sub-crafting for any missing intermediate ingredients
            if self.recursive_subcraft_enabled:
                for ing in recipe.ingredients:
                    needed_total = ing.required_count * batch_count
                    owned = inventory.get(ing.item_id, 0)
                    if owned < needed_total:
                        shortfall = needed_total - owned
                        sub_recipe = recipes_by_result.get(ing.item_id)
                        if sub_recipe:
                            needed_sub_batches = int(math.ceil(shortfall / float(sub_recipe.result_count)))
                            self.execute_craft(sub_recipe, needed_sub_batches, inventory, recipes_by_result)

            # Atomic deduction of primary ingredients
            for ing in recipe.ingredients:
                cost = ing.required_count * batch_count
                inventory[ing.item_id] = max(0, inventory.get(ing.item_id, 0) - cost)

        # Atomic award of output item
        produced = recipe.result_count * batch_count
        inventory[recipe.result_item_id] = inventory.get(recipe.result_item_id, 0) + produced
        return True


# ==============================================================================
# BLOCK 2: WORLD SIMULATION & ENTITIES (CATALOG, INVENTORY & WORKBENCH STATE)
# ==============================================================================

def create_item_database() -> Dict[int, ItemDef]:
    """Generates the master list of all raw, intermediate, and finished craft items."""
    defs = [
        # Raw Harvestable Materials (IDs 1..5)
        ItemDef(1, "Oak Log", CAT_COMPONENTS, 0, "Stout timber freshly chopped from ancient oaks.", is_raw_material=True),
        ItemDef(2, "Iron Ore", CAT_COMPONENTS, 1, "Dense raw ore mined from subterranean veins.", is_raw_material=True),
        ItemDef(3, "Healing Herb", CAT_ALCHEMY, 2, "Aromatic medicinal leaves that mend wounds.", is_raw_material=True),
        ItemDef(4, "Goose Feather", CAT_COMPONENTS, 3, "Aerodynamic fletching for precision arrows.", is_raw_material=True),
        ItemDef(5, "Beast Leather", CAT_EQUIPMENT, 4, "Toughened cured hide from mountain beasts.", is_raw_material=True),

        # Intermediate Craft Components (IDs 6..8)
        ItemDef(6, "Timber Planks", CAT_COMPONENTS, 5, "Milled structural lumber for handles and frames."),
        ItemDef(7, "Iron Ingot", CAT_COMPONENTS, 6, "Smelted refined bar of pure iron."),
        ItemDef(8, "Glass Vial", CAT_ALCHEMY, 7, "Blown glass container for volatile liquids."),

        # Finished Weapons, Armor & Potions (IDs 9..16)
        ItemDef(9, "Iron Dagger", CAT_EQUIPMENT, 8, "Light swift blade. +12 Attack, High Speed."),
        ItemDef(10, "Steel Broadsword", CAT_EQUIPMENT, 9, "Balanced military blade. +24 Attack."),
        ItemDef(11, "Reinforced Shield", CAT_EQUIPMENT, 10, "Heavy oak rimmed with iron. +18 Defense."),
        ItemDef(12, "Healing Draught", CAT_ALCHEMY, 11, "Restores 50 Vitality points immediately."),
        ItemDef(13, "Hunter's Bow", CAT_EQUIPMENT, 12, "Flexible timber recurve bow. +20 Attack."),
        ItemDef(14, "Hunting Arrows", CAT_EQUIPMENT, 13, "Bundle of 5 barbed arrows with feather fletchings."),
        ItemDef(15, "Leather Jerkin", CAT_EQUIPMENT, 14, "Light protective armor. +10 Defense, +5 Mobility."),
        ItemDef(16, "Grand Elixir", CAT_ALCHEMY, 15, "Potent restorative tonic. Fully mends body and soul."),
    ]
    res = {}
    for item in defs:
        res[item.item_id] = item
    return res


def create_recipe_catalog() -> List[CraftingRecipe]:
    """
    Constructs the directed acyclic recipe graph (DAG).
    Recipes demonstrate single-step, multi-ingredient, batch output, and multi-tier chaining.
    """
    return [
        # Tier 1 Components (Raw conversion)
        CraftingRecipe(1, result_item_id=6, result_count=2, category=CAT_COMPONENTS,
                       ingredients=[IngredientSlot(1, 1)]),  # 1 Oak Log -> 2 Timber Planks
        CraftingRecipe(2, result_item_id=7, result_count=1, category=CAT_COMPONENTS,
                       ingredients=[IngredientSlot(2, 2)]),  # 2 Iron Ore -> 1 Iron Ingot
        CraftingRecipe(3, result_item_id=8, result_count=2, category=CAT_ALCHEMY,
                       ingredients=[IngredientSlot(2, 1)]),  # 1 Iron Ore (Silica flux) -> 2 Vials

        # Tier 2 Simple Gear & Potions
        CraftingRecipe(4, result_item_id=9, result_count=1, category=CAT_EQUIPMENT,
                       ingredients=[IngredientSlot(7, 1), IngredientSlot(6, 1)]),  # 1 Ingot + 1 Plank -> Dagger
        CraftingRecipe(5, result_item_id=12, result_count=1, category=CAT_ALCHEMY,
                       ingredients=[IngredientSlot(3, 2), IngredientSlot(8, 1)]),  # 2 Herbs + 1 Vial -> Potion
        CraftingRecipe(6, result_item_id=14, result_count=5, category=CAT_EQUIPMENT,
                       ingredients=[IngredientSlot(6, 1), IngredientSlot(4, 2), IngredientSlot(2, 1)]), # 1 Plank + 2 Feathers + 1 Ore -> 5 Arrows
        CraftingRecipe(7, result_item_id=15, result_count=1, category=CAT_EQUIPMENT,
                       ingredients=[IngredientSlot(5, 3)]),  # 3 Leather -> Jerkin

        # Tier 3 Advanced Gear (Multi-ingredient & Multi-tier dependencies)
        CraftingRecipe(8, result_item_id=10, result_count=1, category=CAT_EQUIPMENT,
                       ingredients=[IngredientSlot(7, 3), IngredientSlot(6, 1), IngredientSlot(5, 1)]), # 3 Ingots + 1 Plank + 1 Leather -> Sword
        CraftingRecipe(9, result_item_id=11, result_count=1, category=CAT_EQUIPMENT,
                       ingredients=[IngredientSlot(7, 2), IngredientSlot(6, 3)]),  # 2 Ingots + 3 Planks -> Shield
        CraftingRecipe(10, result_item_id=13, result_count=1, category=CAT_EQUIPMENT,
                       ingredients=[IngredientSlot(6, 2), IngredientSlot(5, 1)]),  # 2 Planks + 1 Leather -> Bow
        CraftingRecipe(11, result_item_id=16, result_count=1, category=CAT_ALCHEMY,
                       ingredients=[IngredientSlot(12, 2), IngredientSlot(7, 1)]), # 2 Potions + 1 Ingot -> Grand Elixir
    ]


class WorkbenchSimulation:
    """Manages player material inventory, selected recipe focus, and anvil station."""
    def __init__(self):
        self.item_db = create_item_database()
        self.recipes = create_recipe_catalog()
        self.recipes_by_result = {}
        for r in self.recipes:
            self.recipes_by_result[r.result_item_id] = r

        self.engine = CraftingEngine()
        self.selected_category = CAT_ALL
        self.selected_recipe_idx = 0
        self.craft_quantity = 1

        self.anim_timer = 0.0
        self.craft_pulse_timer = 0.0
        self.toast_msg = ""
        self.toast_timer = 0.0
        self.toast_is_error = False

        self.reset_inventory()

    def reset_inventory(self):
        """Pre-populates an initial stock of raw materials for testing."""
        self.inventory: Dict[int, int] = {
            1: 6,   # 6 Oak Logs
            2: 8,   # 8 Iron Ore
            3: 5,   # 5 Healing Herbs
            4: 6,   # 6 Feathers
            5: 4,   # 4 Beast Leather
            6: 2,   # 2 Timber Planks
            7: 1,   # 1 Iron Ingot
            8: 0,   # 0 Vials
        }
        self.crafted_history: List[Tuple[str, int]] = []
        self.craft_quantity = 1

    def get_filtered_recipes(self) -> List[CraftingRecipe]:
        if self.selected_category == CAT_ALL:
            return self.recipes
        filtered = []
        for r in self.recipes:
            if r.category == self.selected_category:
                filtered.append(r)
        return filtered

    def get_selected_recipe(self) -> Optional[CraftingRecipe]:
        filtered = self.get_filtered_recipes()
        if 0 <= self.selected_recipe_idx < len(filtered):
            return filtered[self.selected_recipe_idx]
        return None

    def gather_material(self, item_id: int, count: int, sfx: SoundLibrary):
        """Harvests raw resources from the right-hand testing rack."""
        self.inventory[item_id] = self.inventory.get(item_id, 0) + count
        item = self.item_db.get(item_id)
        name = item.name if item else "Item"
        self.toast_msg = f"+ Gathered {count}x {name}"
        self.toast_timer = 1.8
        self.toast_is_error = False
        sfx.play("click", 0.6)

    def trigger_craft(self, sfx: SoundLibrary) -> bool:
        recipe = self.get_selected_recipe()
        if not recipe:
            return False

        eval_res = self.engine.evaluate_recipe(recipe, self.inventory, self.recipes_by_result)
        if not eval_res.can_craft and self.engine.strict_gating_enabled:
            self.toast_msg = "Cannot Craft: Missing required ingredients!"
            self.toast_timer = 2.2
            self.toast_is_error = True
            sfx.play("hurt", 0.7)
            return False

        qty = max(1, min(self.craft_quantity, eval_res.max_craftable)) if self.engine.strict_gating_enabled else self.craft_quantity
        success = self.engine.execute_craft(recipe, qty, self.inventory, self.recipes_by_result)

        if success:
            res_item = self.item_db.get(recipe.result_item_id)
            name = res_item.name if res_item else "Item"
            total_produced = recipe.result_count * qty
            self.toast_msg = f"Crafted {total_produced}x {name}!"
            self.toast_timer = 2.2
            self.toast_is_error = False
            self.craft_pulse_timer = 0.4
            self.crafted_history.append((name, total_produced))
            if len(self.crafted_history) > 5:
                self.crafted_history.pop(0)

            sfx.play("coin", 0.8)
            sfx.play("hit", 0.9)  # Anvil strike thud

            # Clamp quantity safely
            new_eval = self.engine.evaluate_recipe(recipe, self.inventory, self.recipes_by_result)
            self.craft_quantity = max(1, min(self.craft_quantity, new_eval.max_craftable)) if new_eval.max_craftable > 0 else 1
            return True
        return False


# ==============================================================================
# PROCEDURAL DRAWING UTILITIES FOR ITEMS & WORKBENCH
# ==============================================================================

def draw_procedural_craft_icon(icon_type: int, cx: int, cy: int, size: int, is_greyed: bool = False):
    """
    Renders high-clarity 2D procedural geometric icons for materials and crafted gear.
    C++ Equivalent: Raylib 2D primitive render calls using circles, rectangles & lines.
    """
    half = size // 2

    # Outer backing badge
    bg_col = Color(14, 18, 28, 255) if not is_greyed else Color(18, 20, 24, 200)
    border_col = Color(42, 56, 84, 255) if not is_greyed else Color(30, 36, 46, 180)
    draw_circle(cx, cy, half + 2, bg_col)
    draw_circle_lines(cx, cy, half + 2, border_col)

    # Greyscale or standard palette
    def c(r, g, b, a=255):
        if is_greyed:
            grey = int(0.299 * r + 0.587 * g + 0.114 * b)
            return Color(grey, grey, grey, 140)
        return Color(r, g, b, a)

    if icon_type == 0:  # Oak Log
        draw_rectangle(cx - half + 6, cy - half + 8, (half - 6) * 2, (half - 8) * 2, c(120, 80, 45))
        draw_circle(cx - half + 6, cy, half - 8, c(170, 125, 75))
        draw_circle(cx - half + 6, cy, half - 12, c(110, 70, 35))

    elif icon_type == 1:  # Iron Ore
        draw_circle(cx - 3, cy + 2, half - 6, c(95, 105, 120))
        draw_circle(cx + 4, cy - 3, half - 8, c(135, 145, 160))
        draw_circle(cx - 2, cy - 2, 3, c(215, 195, 120))  # Pyrite fleck

    elif icon_type == 2:  # Healing Herb
        draw_line_ex(Vector2(cx, cy + half - 5), Vector2(cx, cy - half + 6), 3.0, c(45, 140, 60))
        draw_circle(cx - 5, cy - 2, 5, c(65, 215, 95))
        draw_circle(cx + 5, cy + 1, 5, c(65, 215, 95))
        draw_circle(cx, cy - half + 5, 4, c(105, 245, 135))

    elif icon_type == 3:  # Goose Feather
        draw_line_ex(Vector2(cx - half + 6, cy + half - 6), Vector2(cx + half - 6, cy - half + 6), 3.0, c(220, 220, 230))
        draw_circle(cx + 2, cy - 2, 6, c(245, 245, 255, 180))

    elif icon_type == 4:  # Beast Leather
        draw_rectangle(cx - half + 6, cy - half + 7, (half - 6) * 2, (half - 7) * 2, c(145, 95, 55))
        draw_circle(cx, cy, 4, c(105, 65, 35))

    elif icon_type == 5:  # Timber Planks
        draw_rectangle(cx - half + 6, cy - half + 6, (half - 6) * 2, 7, c(175, 125, 75))
        draw_rectangle(cx - half + 6, cy - half + 16, (half - 6) * 2, 7, c(155, 105, 60))
        draw_rectangle(cx - half + 6, cy - half + 26, (half - 6) * 2, 7, c(175, 125, 75))

    elif icon_type == 6:  # Iron Ingot
        draw_rectangle(cx - half + 7, cy - 6, (half - 7) * 2, 12, c(150, 160, 180))
        draw_line_ex(Vector2(cx - half + 7, cy - 6), Vector2(cx + half - 7, cy - 6), 2.0, c(215, 225, 245))

    elif icon_type == 7:  # Glass Vial
        draw_rectangle(cx - 2, cy - half + 6, 4, 6, c(180, 205, 235, 160))
        draw_circle(cx, cy + 3, half - 8, c(120, 190, 235, 150))
        draw_circle_lines(cx, cy + 3, half - 8, c(210, 235, 255, 220))

    elif icon_type == 8:  # Iron Dagger
        draw_line_ex(Vector2(cx - half + 7, cy + half - 7), Vector2(cx + half - 7, cy - half + 7), 3.0, c(215, 225, 245))
        draw_line_ex(Vector2(cx - 2, cy + 6), Vector2(cx - 6, cy + 2), 3.0, c(245, 195, 55))

    elif icon_type == 9:  # Steel Broadsword
        draw_line_ex(Vector2(cx - half + 8, cy + half - 8), Vector2(cx + half - 7, cy - half + 7), 5.0, c(225, 235, 255))
        draw_line_ex(Vector2(cx - 3, cy + 8), Vector2(cx - 8, cy + 3), 4.0, c(255, 215, 60))
        draw_circle(cx - half + 6, cy + half - 6, 3, c(185, 135, 45))

    elif icon_type == 10:  # Reinforced Shield
        draw_rectangle(cx - half + 7, cy - half + 7, (half - 7) * 2, half, c(75, 105, 165))
        draw_triangle(
            Vector2(cx - half + 7, cy),
            Vector2(cx, cy + half - 5),
            Vector2(cx + half - 7, cy),
            c(75, 105, 165)
        )
        draw_rectangle(cx - 2, cy - half + 9, 4, half + 4, c(255, 215, 60))

    elif icon_type in (11, 15):  # Healing Draught / Grand Elixir
        col = c(245, 65, 80) if icon_type == 11 else c(215, 75, 255)
        draw_rectangle(cx - 2, cy - half + 6, 4, 5, c(170, 125, 75))
        draw_circle(cx, cy + 4, half - 7, col)
        draw_circle_lines(cx, cy + 4, half - 7, c(235, 245, 255))
        if icon_type == 15:
            draw_circle(cx, cy + 4, 3, c(255, 255, 255, 200))

    elif icon_type == 12:  # Hunter's Bow
        draw_circle_lines(cx - half + 10, cy, half - 4, c(145, 95, 50))
        draw_line(cx + half - 12, cy - half + 8, cx + half - 12, cy + half - 8, c(220, 220, 220))

    elif icon_type == 13:  # Hunting Arrows
        draw_line(cx - half + 8, cy, cx + half - 8, cy, c(175, 135, 85))
        draw_triangle(
            Vector2(cx + half - 8, cy - 4),
            Vector2(cx + half - 4, cy),
            Vector2(cx + half - 8, cy + 4),
            c(180, 190, 210)
        )
        draw_line(cx - half + 8, cy - 3, cx - half + 12, cy, c(235, 235, 245))

    elif icon_type == 14:  # Leather Jerkin
        draw_rectangle(cx - half + 8, cy - half + 8, (half - 8) * 2, (half - 8) * 2, c(135, 85, 45))
        draw_line(cx, cy - half + 12, cx, cy + half - 8, c(75, 45, 25))

    else:
        draw_circle(cx, cy, half - 7, c(160, 160, 180))


def draw_anvil_station(cx: int, cy: int, anim_timer: float, pulse_timer: float):
    """Renders a procedural blacksmith workbench table and anvil with hot spark effects."""
    # Wooden workbench block
    draw_rectangle(cx - 75, cy + 10, 150, 45, COLOR_WOOD_DARK)
    draw_rectangle_lines(cx - 75, cy + 10, 150, 45, COLOR_WOOD_LIGHT)
    draw_rectangle(cx - 65, cy + 20, 130, 25, Color(38, 26, 18, 255))

    # Anvil silhouette (base, waist, horn, face)
    base_col = COLOR_ANVIL_STEEL
    draw_rectangle(cx - 45, cy + 2, 90, 10, base_col)     # Foot
    draw_rectangle(cx - 20, cy - 14, 40, 16, base_col)    # Waist
    draw_rectangle(cx - 50, cy - 24, 75, 12, base_col)    # Table / Face

    # Horn (left pointed triangle)
    draw_triangle(
        Vector2(cx + 25, cy - 24),
        Vector2(cx + 25, cy - 12),
        Vector2(cx + 52, cy - 18),
        base_col
    )
    draw_line(cx - 50, cy - 24, cx + 50, cy - 24, Color(165, 185, 215, 255))  # High-carbon surface

    # Animated glowing heat / spark burst on craft
    if pulse_timer > 0.0:
        spark_alpha = int((pulse_timer / 0.4) * 255)
        draw_circle(cx - 10, cy - 24, 18, Color(255, 180, 50, spark_alpha))
        for i in range(6):
            ang = (i * 60.0 + anim_timer * 180.0) * (math.pi / 180.0)
            dist = 22.0 + (0.4 - pulse_timer) * 60.0
            sx = int(cx - 10 + math.cos(ang) * dist)
            sy = int(cy - 24 + math.sin(ang) * dist)
            draw_circle(sx, sy, 3, Color(255, 220, 90, spark_alpha))


# ==============================================================================
# BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY ([Tab] & [F1])
# ==============================================================================

def draw_xray_telemetry_overlay(sim: WorkbenchSimulation):
    """
    Renders diagnostic telemetry exposing the Recipe Dependency Graph (DAG),
    precondition validation state, and memory layout.
    """
    draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, Color(6, 8, 14, 235))

    ox = 110
    oy = 75
    ow = SCREEN_WIDTH - 220
    oh = SCREEN_HEIGHT - 150

    draw_rectangle(ox, oy, ow, oh, Color(16, 22, 36, 255))
    draw_rectangle_lines(ox, oy, ow, oh, COLOR_CYAN_ACCENT)

    # Header
    draw_text("[X-RAY TELEMETRY] RECIPE DEPENDENCY GRAPH (DAG) & CRAFTING PIPELINE", ox + 24, oy + 18, 18, COLOR_GOLD_ACCENT)
    draw_line(ox + 20, oy + 46, ox + ow - 20, oy + 46, COLOR_PANEL_BORDER)

    # Section 1: Visual DAG (Directed Acyclic Graph)
    cx1 = ox + 30
    draw_text("1. RECIPE DEPENDENCY DAG (RAW -> INTERMEDIATE -> FINISHED)", cx1, oy + 58, 14, COLOR_CYAN_ACCENT)

    dag_y = oy + 84
    # Tier 1 Nodes (Raw)
    t1_nodes = ["1: Oak Log", "2: Iron Ore", "3: Healing Herb", "4: Feather", "5: Leather"]
    for i, t in enumerate(t1_nodes):
        nx = cx1 + i * 98
        draw_rectangle(nx, dag_y, 90, 28, Color(30, 42, 65, 255))
        draw_rectangle_lines(nx, dag_y, 90, 28, COLOR_CYAN_ACCENT)
        draw_text(t, nx + 6, dag_y + 8, 10, COLOR_WHITE)

    # Down arrows to Tier 2
    draw_text("↓ (Smelt/Mill)", cx1 + 35, dag_y + 32, 10, COLOR_TEXT_DIM)
    draw_text("↓ (Forge)", cx1 + 130, dag_y + 32, 10, COLOR_TEXT_DIM)
    draw_text("↓ (Blow)", cx1 + 195, dag_y + 32, 10, COLOR_TEXT_DIM)

    # Tier 2 Nodes (Intermediates)
    t2_y = dag_y + 46
    t2_nodes = [
        (cx1 + 10, "6: Timber Planks (Log)"),
        (cx1 + 170, "7: Iron Ingot (2 Ore)"),
        (cx1 + 340, "8: Glass Vial (Ore)")
    ]
    for nx, label in t2_nodes:
        draw_rectangle(nx, t2_y, 140, 28, Color(42, 34, 60, 255))
        draw_rectangle_lines(nx, t2_y, 140, 28, COLOR_GOLD_ACCENT)
        draw_text(label, nx + 6, t2_y + 8, 10, COLOR_GOLD_ACCENT)

    # Tier 3 Finished Gear
    draw_text("↓ (Combine & Assemble Components into Equipment / Alchemy)", cx1 + 20, t2_y + 32, 10, COLOR_TEXT_DIM)
    t3_y = t2_y + 48
    t3_nodes = [
        "9: Dagger (Ingot+Plank)", "10: Sword (3 Ingot+Plank+Hide)",
        "11: Shield (2 Ingot+3 Plank)", "12: Potion (2 Herb+Vial)",
        "13: Bow (2 Plank+Hide)", "14: Arrows (Plank+2 Feathers+Ore)"
    ]
    for i, t in enumerate(t3_nodes):
        nx = cx1 + (i % 3) * 168
        ny = t3_y + (i // 3) * 32
        draw_rectangle(nx, ny, 160, 26, Color(24, 38, 30, 255))
        draw_rectangle_lines(nx, ny, 160, 26, COLOR_GREEN_READY)
        draw_text(t, nx + 6, ny + 7, 9, COLOR_WHITE)

    # Section 2: Engine Mode & Sub-Crafting Status
    cx2 = ox + 550
    draw_text("2. ENGINE GATING & SUB-CRAFTING ENGINE", cx2, oy + 58, 14, COLOR_CYAN_ACCENT)
    by = oy + 84
    draw_rectangle(cx2, by, 450, 185, Color(22, 28, 44, 255))
    draw_rectangle_lines(cx2, by, 450, 185, COLOR_PANEL_BORDER)

    gating_str = "STRICT GATING: ACTIVE (Grounded survival economy)" if sim.engine.strict_gating_enabled else "STRICT GATING: DISABLED (Cheat / Creative free-craft)"
    draw_text(gating_str, cx2 + 14, by + 12, 12, COLOR_GREEN_READY if sim.engine.strict_gating_enabled else COLOR_RED_MISSING)

    sub_str = "RECURSIVE SUB-CRAFT: ENABLED (Auto-synthesizes ingots/planks)" if sim.engine.recursive_subcraft_enabled else "RECURSIVE SUB-CRAFT: DISABLED (Manual intermediate crafts required)"
    draw_text(sub_str, cx2 + 14, by + 34, 12, COLOR_CYAN_ACCENT if sim.engine.recursive_subcraft_enabled else COLOR_TEXT_DIM)

    draw_text("ATOMIC TRANSACTION PROOF:", cx2 + 14, by + 62, 11, COLOR_GOLD_ACCENT)
    draw_text("1. Precondition Check: Count owned vs (Req * Qty) across all slots.", cx2 + 14, by + 80, 10, COLOR_TEXT_MAIN)
    draw_text("2. If deficit > 0: Reject cleanly with zero state mutation.", cx2 + 14, by + 98, 10, COLOR_TEXT_MAIN)
    draw_text("3. Atomic Swap: Deduct all inputs and add output in one frame.", cx2 + 14, by + 116, 10, COLOR_TEXT_MAIN)
    draw_text("Result: Zero ingredient leakage, zero item duplication glitches.", cx2 + 14, by + 138, 10, COLOR_GREEN_READY)

    # Section 3: C++ Memory Struct Footprint
    cy3 = oy + 290
    draw_text("3. C++ EQUIVALENT DATA STRUCTURES & MEMORY FOOTPRINT", cx1, cy3, 14, COLOR_CYAN_ACCENT)
    box_y = cy3 + 24
    draw_rectangle(cx1, box_y, ow - 60, 120, Color(20, 26, 42, 255))
    draw_rectangle_lines(cx1, box_y, ow - 60, 120, Color(45, 60, 95, 255))

    cpp_lines = [
        "struct IngredientSlot { int item_id; int required_count; };                                  // 8 bytes",
        "struct CraftingRecipe { int id; int res_id; int count; int cat; IngredientSlot in[4]; };      // 48 bytes",
        "struct InventoryState { int item_counts[MAX_ITEMS]; };                                        // 64 bytes",
        "Total Memory Footprint: 11 Recipes * 48B + 16 Items * 4B = 592 bytes! Fits in single L1 cache."
    ]
    for i, line in enumerate(cpp_lines):
        draw_text(line, cx1 + 14, box_y + 12 + i * 24, 11, COLOR_TEXT_MAIN)

    draw_text("Press [Tab] or Gamepad Y to dismiss X-Ray Telemetry Inspector", ox + ow // 2 - 200, oy + oh - 26, 12, COLOR_TEXT_DIM)


# ==============================================================================
# BLOCK 4: MAIN GAME LOOP & AUTOMATED SMOKE TEST
# ==============================================================================

class WorkbenchGame:
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()

        self.sfx = SoundLibrary()
        self.sfx.init_defaults()

        self.sim = WorkbenchSimulation()
        self.show_xray = True  # Default ON for pedagogical clarity
        self.confirm_button_hover = False

    def handle_input(self, dt: float):
        # 1. Toggles
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
            self.sfx.play("click", 0.6)

        if is_dual_pattern_toggle_pressed():  # F1 / Gamepad LB
            self.sim.engine.strict_gating_enabled = not self.sim.engine.strict_gating_enabled
            mode_str = "STRICT INGREDIENT GATING (Normal Economy)" if self.sim.engine.strict_gating_enabled else "FREE CREATIVE MODE (No Materials Required)"
            self.sim.toast_msg = f"Crafting Mode: {mode_str}"
            self.sim.toast_timer = 2.5
            self.sim.toast_is_error = not self.sim.engine.strict_gating_enabled
            self.sfx.play("click", 0.8)

        if is_dual_secondary_toggle_pressed():  # F2 / Gamepad RB
            self.sim.engine.recursive_subcraft_enabled = not self.sim.engine.recursive_subcraft_enabled
            sub_str = "RECURSIVE AUTO-CRAFT: ON (Auto-Synthesize Predecessors)" if self.sim.engine.recursive_subcraft_enabled else "RECURSIVE AUTO-CRAFT: OFF (Manual Sub-Crafts Only)"
            self.sim.toast_msg = sub_str
            self.sim.toast_timer = 2.5
            self.sim.toast_is_error = False
            self.sfx.play("powerup", 0.7)

        if is_dual_reset_pressed():  # R / Gamepad Start
            self.sim.reset_inventory()
            self.sim.toast_msg = "Workbench & Satchel Restored to Initial State"
            self.sim.toast_timer = 2.0
            self.sim.toast_is_error = False
            self.sfx.play("click", 0.7)

        # 2. Category Tabs Cycling (A / D or Gamepad Left Stick)
        if is_key_pressed(KEY_A) or (is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_LEFT) if is_gamepad_available(0) else False):
            self.sim.selected_category = (self.sim.selected_category - 1) % len(CATEGORY_NAMES)
            self.sim.selected_recipe_idx = 0
            self.sfx.play("click", 0.4)

        if is_key_pressed(KEY_D) or (is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_RIGHT) if is_gamepad_available(0) else False):
            self.sim.selected_category = (self.sim.selected_category + 1) % len(CATEGORY_NAMES)
            self.sim.selected_recipe_idx = 0
            self.sfx.play("click", 0.4)

        # 3. Recipe List Navigation (W / S or Gamepad Up/Down)
        filtered = self.sim.get_filtered_recipes()
        if filtered:
            if is_key_pressed(KEY_W) or is_key_pressed(KEY_UP) or (is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_UP) if is_gamepad_available(0) else False):
                self.sim.selected_recipe_idx = (self.sim.selected_recipe_idx - 1) % len(filtered)
                self.clamp_recipe_quantity()
                self.sfx.play("click", 0.4)

            if is_key_pressed(KEY_S) or is_key_pressed(KEY_DOWN) or (is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_DOWN) if is_gamepad_available(0) else False):
                self.sim.selected_recipe_idx = (self.sim.selected_recipe_idx + 1) % len(filtered)
                self.clamp_recipe_quantity()
                self.sfx.play("click", 0.4)

        # 4. Quantity Adjustments (Q / E or [-] / [+])
        recipe = self.sim.get_selected_recipe()
        if recipe:
            eval_res = self.sim.engine.evaluate_recipe(recipe, self.sim.inventory, self.sim.recipes_by_result)
            max_q = eval_res.max_craftable if self.sim.engine.strict_gating_enabled else 99

            if is_key_pressed(KEY_Q) or is_key_pressed(KEY_MINUS):
                if self.sim.craft_quantity > 1:
                    self.sim.craft_quantity -= 1
                    self.sfx.play("click", 0.4)

            if is_key_pressed(KEY_E) or is_key_pressed(KEY_EQUAL):
                if self.sim.craft_quantity < max_q or not self.sim.engine.strict_gating_enabled:
                    self.sim.craft_quantity += 1
                    self.sfx.play("click", 0.4)

            if is_key_pressed(KEY_ONE):
                self.sim.craft_quantity = 1
                self.sfx.play("click", 0.4)
            if is_key_pressed(KEY_FIVE):
                self.sim.craft_quantity = max(1, min(5, max_q)) if self.sim.engine.strict_gating_enabled else 5
                self.sfx.play("click", 0.4)
            if is_key_pressed(KEY_M) or (is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_FACE_LEFT) if is_gamepad_available(0) else False):
                self.sim.craft_quantity = max(1, max_q) if max_q > 0 else 1
                self.sfx.play("click", 0.5)

        # 5. Quick Material Harvesting Keys (1..5)
        if is_key_down(KEY_LEFT_SHIFT) or is_key_down(KEY_RIGHT_SHIFT):
            if is_key_pressed(KEY_ONE):
                self.sim.gather_material(1, 3, self.sfx)
            elif is_key_pressed(KEY_TWO):
                self.sim.gather_material(2, 2, self.sfx)
            elif is_key_pressed(KEY_THREE):
                self.sim.gather_material(3, 2, self.sfx)
            elif is_key_pressed(KEY_FOUR):
                self.sim.gather_material(4, 3, self.sfx)
            elif is_key_pressed(KEY_FIVE):
                self.sim.gather_material(5, 2, self.sfx)

        # 6. Confirm Craft (Enter / Space / Gamepad A)
        if is_dual_primary_fire_pressed() or is_key_pressed(KEY_ENTER) or is_key_pressed(KEY_SPACE):
            self.sim.trigger_craft(self.sfx)

        # 7. Mouse interactions
        self.handle_mouse_interaction()

    def clamp_recipe_quantity(self):
        recipe = self.sim.get_selected_recipe()
        if recipe and self.sim.engine.strict_gating_enabled:
            eval_res = self.sim.engine.evaluate_recipe(recipe, self.sim.inventory, self.sim.recipes_by_result)
            self.sim.craft_quantity = max(1, min(self.sim.craft_quantity, eval_res.max_craftable)) if eval_res.max_craftable > 0 else 1

    def handle_mouse_interaction(self):
        m_pos = get_mouse_position()
        mx = int(m_pos.x)
        my = int(m_pos.y)
        m_clicked = is_mouse_button_pressed(MOUSE_BUTTON_LEFT)

        # Category Tabs Click
        tab_y = PANEL_LEFT_Y + 44
        tab_w = (PANEL_LEFT_W - 20) // 4
        for i in range(4):
            tx = PANEL_LEFT_X + 10 + i * tab_w
            if tx <= mx <= tx + tab_w and tab_y <= my <= tab_y + 28:
                if m_clicked:
                    self.sim.selected_category = i
                    self.sim.selected_recipe_idx = 0
                    self.clamp_recipe_quantity()
                    self.sfx.play("click", 0.5)

        # Recipe List Items Click
        filtered = self.sim.get_filtered_recipes()
        list_y = PANEL_LEFT_Y + 84
        slot_h = 46
        for i, r in enumerate(filtered):
            sy = list_y + i * (slot_h + 4)
            if PANEL_LEFT_X + 10 <= mx <= PANEL_LEFT_X + PANEL_LEFT_W - 10 and sy <= my <= sy + slot_h:
                if m_clicked:
                    self.sim.selected_recipe_idx = i
                    self.clamp_recipe_quantity()
                    self.sfx.play("click", 0.5)

        # Center Desk Stepper buttons
        step_y = PANEL_CENTER_Y + 395
        btn_minus = (PANEL_CENTER_X + 65, step_y, 40, 34)
        btn_plus  = (PANEL_CENTER_X + PANEL_CENTER_W - 105, step_y, 40, 34)

        recipe = self.sim.get_selected_recipe()
        if recipe:
            eval_res = self.sim.engine.evaluate_recipe(recipe, self.sim.inventory, self.sim.recipes_by_result)
            max_q = eval_res.max_craftable if self.sim.engine.strict_gating_enabled else 99

            if btn_minus[0] <= mx <= btn_minus[0] + btn_minus[2] and btn_minus[1] <= my <= btn_minus[1] + btn_minus[3]:
                if m_clicked and self.sim.craft_quantity > 1:
                    self.sim.craft_quantity -= 1
                    self.sfx.play("click", 0.4)

            if btn_plus[0] <= mx <= btn_plus[0] + btn_plus[2] and btn_plus[1] <= my <= btn_plus[1] + btn_plus[3]:
                if m_clicked and (self.sim.craft_quantity < max_q or not self.sim.engine.strict_gating_enabled):
                    self.sim.craft_quantity += 1
                    self.sfx.play("click", 0.4)

            # Quick presets
            quick_y = step_y + 42
            presets = [
                (PANEL_CENTER_X + 75, quick_y, 70, 24, 1),
                (PANEL_CENTER_X + 175, quick_y, 70, 24, 5),
                (PANEL_CENTER_X + 275, quick_y, 70, 24, max_q)
            ]
            for bx, by, bw, bh, q_val in presets:
                if bx <= mx <= bx + bw and by <= my <= by + bh:
                    if m_clicked:
                        self.sim.craft_quantity = max(1, min(q_val, max_q)) if self.sim.engine.strict_gating_enabled and max_q > 0 else (q_val if not self.sim.engine.strict_gating_enabled else 1)
                        self.sfx.play("click", 0.4)

        # Craft Button Click
        btn_craft_x = PANEL_CENTER_X + 30
        btn_craft_y = PANEL_CENTER_Y + 480
        btn_craft_w = PANEL_CENTER_W - 60
        btn_craft_h = 46

        self.confirm_button_hover = (
            btn_craft_x <= mx <= btn_craft_x + btn_craft_w and
            btn_craft_y <= my <= btn_craft_y + btn_craft_h
        )
        if self.confirm_button_hover and m_clicked:
            self.sim.trigger_craft(self.sfx)

        # Right Panel Gathering Rack Clicks
        rack_y = PANEL_RIGHT_Y + 54
        btn_h = 32
        gather_items = [(1, 3, "Oak Logs"), (2, 2, "Iron Ore"), (3, 2, "Herbs"), (4, 3, "Feathers"), (5, 2, "Leather")]
        for i, (item_id, count, label) in enumerate(gather_items):
            gy = rack_y + i * (btn_h + 4)
            if PANEL_RIGHT_X + 15 <= mx <= PANEL_RIGHT_X + PANEL_RIGHT_W - 15 and gy <= my <= gy + btn_h:
                if m_clicked:
                    self.sim.gather_material(item_id, count, self.sfx)

    def update(self):
        dt = min(get_frame_time(), 0.05)
        self.sim.anim_timer += dt

        if self.sim.toast_timer > 0.0:
            self.sim.toast_timer -= dt

        if self.sim.craft_pulse_timer > 0.0:
            self.sim.craft_pulse_timer -= dt

        self.handle_input(dt)

    def draw(self):
        begin_drawing()
        clear_background(COLOR_BG)

        # 1. Top HUD Header
        self.draw_top_bar()

        # 2. Left Panel: Recipe Book & Categories
        self.draw_recipe_catalog_panel()

        # 3. Center Panel: Anvil Crafting Station & Assembly Table
        self.draw_assembly_panel()

        # 4. Right Panel: Testing Resource Rack & Inventory Satchel
        self.draw_inventory_panel()

        # 5. Toast Feedback
        if self.sim.toast_timer > 0.0:
            self.draw_toast()

        # 6. Global Dropdowns & Gamepad Badge
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)

        # 7. X-Ray Telemetry Overlay ([Tab])
        if self.show_xray:
            draw_xray_telemetry_overlay(self.sim)

        end_drawing()

    def draw_top_bar(self):
        draw_rectangle(0, 0, SCREEN_WIDTH, 52, Color(16, 20, 32, 255))
        draw_line(0, 52, SCREEN_WIDTH, 52, COLOR_PANEL_BORDER)

        draw_text("WORKBENCH", 25, 14, 20, COLOR_GOLD_ACCENT)
        draw_text("CRAFTING RECIPES & DEPENDENCY GRAPH", 175, 20, 12, COLOR_TEXT_DIM)

        # Status mode badges (left of top settings bar)
        if self.sim.engine.strict_gating_enabled:
            draw_rectangle(25, 34, 185, 14, Color(22, 48, 32, 255))
            draw_text("[F1] GATING: STRICT INGREDIENTS", 28, 36, 9, COLOR_GREEN_READY)
        else:
            draw_rectangle(25, 34, 185, 14, Color(58, 22, 22, 255))
            draw_text("[F1] GATING: FREE CREATIVE CHEAT", 28, 36, 9, COLOR_RED_MISSING)

        if self.sim.engine.recursive_subcraft_enabled:
            draw_rectangle(225, 34, 185, 14, Color(22, 38, 56, 255))
            draw_text("[F2] SUBCRAFT: RECURSIVE AUTO", 228, 36, 9, COLOR_CYAN_ACCENT)

    def draw_recipe_catalog_panel(self):
        draw_rectangle(PANEL_LEFT_X, PANEL_LEFT_Y, PANEL_LEFT_W, PANEL_LEFT_H, COLOR_PANEL_BG)
        draw_rectangle_lines(PANEL_LEFT_X, PANEL_LEFT_Y, PANEL_LEFT_W, PANEL_LEFT_H, COLOR_PANEL_BORDER)

        # Header
        draw_rectangle(PANEL_LEFT_X, PANEL_LEFT_Y, PANEL_LEFT_W, 36, COLOR_WOOD_DARK)
        draw_text("RECIPE BLUEPRINTS", PANEL_LEFT_X + 16, PANEL_LEFT_Y + 10, 15, COLOR_GOLD_ACCENT)

        # Category Tabs ([ALL], [EQUIP], [ALCH], [PARTS])
        tab_y = PANEL_LEFT_Y + 42
        tab_labels = ["ALL", "EQUIP", "ALCH", "PARTS"]
        tab_w = (PANEL_LEFT_W - 20) // 4
        for i in range(4):
            tx = PANEL_LEFT_X + 10 + i * tab_w
            is_active = (self.sim.selected_category == i)
            col_bg = Color(35, 48, 76, 255) if is_active else Color(20, 26, 40, 255)
            draw_rectangle(tx, tab_y, tab_w - 2, 26, col_bg)
            draw_rectangle_lines(tx, tab_y, tab_w - 2, 26, COLOR_SLOT_SELECTED if is_active else COLOR_SLOT_BORDER)
            draw_text(tab_labels[i], tx + tab_w // 2 - 16, tab_y + 8, 10, COLOR_WHITE if is_active else COLOR_TEXT_DIM)

        # Recipe List
        filtered = self.sim.get_filtered_recipes()
        list_y = PANEL_LEFT_Y + 76
        slot_h = 44

        for i, recipe in enumerate(filtered):
            sy = list_y + i * (slot_h + 4)
            if sy + slot_h > PANEL_LEFT_Y + PANEL_LEFT_H - 10:
                break

            res_item = self.sim.item_db.get(recipe.result_item_id)
            if not res_item:
                continue

            eval_res = self.sim.engine.evaluate_recipe(recipe, self.sim.inventory, self.sim.recipes_by_result)
            is_sel = (self.sim.selected_recipe_idx == i)

            # Slot styling: ready vs locked
            if eval_res.can_craft:
                bg_col = Color(28, 48, 38, 255) if is_sel else Color(18, 28, 24, 255)
                border_col = COLOR_GREEN_READY if is_sel else Color(45, 80, 55, 255)
            else:
                bg_col = Color(32, 34, 42, 255) if is_sel else COLOR_SLOT_LOCKED
                border_col = COLOR_SLOT_SELECTED if is_sel else COLOR_SLOT_BORDER

            draw_rectangle(PANEL_LEFT_X + 10, sy, PANEL_LEFT_W - 20, slot_h, bg_col)
            draw_rectangle_lines(PANEL_LEFT_X + 10, sy, PANEL_LEFT_W - 20, slot_h, border_col)

            # Icon
            draw_procedural_craft_icon(res_item.icon_type, PANEL_LEFT_X + 30, sy + slot_h // 2, 28, is_greyed=(not eval_res.can_craft and self.sim.engine.strict_gating_enabled))

            # Name and Batch count
            name_text = f"{res_item.name}"
            if recipe.result_count > 1:
                name_text += f" (x{recipe.result_count})"
            draw_text(name_text, PANEL_LEFT_X + 50, sy + 6, 12, COLOR_WHITE if eval_res.can_craft else COLOR_TEXT_DIM)

            # Category / Status Tag
            cat_name = CATEGORY_NAMES[recipe.category]
            draw_text(cat_name, PANEL_LEFT_X + 50, sy + 24, 10, CATEGORY_COLORS[recipe.category])

            # Availability Badge (Ready xN or Locked/Missing)
            if eval_res.can_craft:
                badge_str = f"READY (x{eval_res.max_craftable})"
                draw_rectangle(PANEL_LEFT_X + PANEL_LEFT_W - 95, sy + 13, 80, 18, Color(24, 60, 36, 255))
                draw_text(badge_str, PANEL_LEFT_X + PANEL_LEFT_W - 90, sy + 16, 9, COLOR_GREEN_READY)
            else:
                badge_str = "LOCKED"
                draw_rectangle(PANEL_LEFT_X + PANEL_LEFT_W - 75, sy + 13, 60, 18, Color(42, 24, 24, 255))
                draw_text(badge_str, PANEL_LEFT_X + PANEL_LEFT_W - 68, sy + 16, 9, COLOR_RED_MISSING)

    def draw_assembly_panel(self):
        draw_rectangle(PANEL_CENTER_X, PANEL_CENTER_Y, PANEL_CENTER_W, PANEL_CENTER_H, COLOR_PANEL_BG)
        draw_rectangle_lines(PANEL_CENTER_X, PANEL_CENTER_Y, PANEL_CENTER_W, PANEL_CENTER_H, COLOR_PANEL_BORDER)

        # Header
        draw_rectangle(PANEL_CENTER_X, PANEL_CENTER_Y, PANEL_CENTER_W, 36, COLOR_WOOD_DARK)
        draw_text("CRAFTING ASSEMBLY TABLE", PANEL_CENTER_X + 16, PANEL_CENTER_Y + 10, 15, COLOR_GOLD_ACCENT)

        recipe = self.sim.get_selected_recipe()
        if not recipe:
            draw_text("Select a blueprint from the catalog", PANEL_CENTER_X + 80, PANEL_CENTER_Y + 200, 14, COLOR_TEXT_DIM)
            return

        res_item = self.sim.item_db.get(recipe.result_item_id)
        if not res_item:
            return

        eval_res = self.sim.engine.evaluate_recipe(recipe, self.sim.inventory, self.sim.recipes_by_result)

        # 1. Output Item Showcase Frame
        card_y = PANEL_CENTER_Y + 48
        draw_rectangle(PANEL_CENTER_X + 20, card_y, PANEL_CENTER_W - 40, 95, Color(24, 32, 50, 255))
        draw_rectangle_lines(PANEL_CENTER_X + 20, card_y, PANEL_CENTER_W - 40, 95, COLOR_PANEL_BORDER)

        draw_procedural_craft_icon(res_item.icon_type, PANEL_CENTER_X + 60, card_y + 47, 50)
        draw_text(res_item.name, PANEL_CENTER_X + 98, card_y + 14, 16, COLOR_GOLD_ACCENT)
        draw_text(f"Output: {recipe.result_count} unit(s) per craft", PANEL_CENTER_X + 98, card_y + 36, 11, COLOR_CYAN_ACCENT)
        draw_text(res_item.description, PANEL_CENTER_X + 98, card_y + 54, 10, COLOR_TEXT_DIM)

        # 2. Required Ingredients Breakdown (The Core Visual Lesson!)
        ing_y = PANEL_CENTER_Y + 152
        draw_text("REQUIRED INGREDIENTS:", PANEL_CENTER_X + 25, ing_y, 12, COLOR_CYAN_ACCENT)

        slot_y = ing_y + 20
        ing_h = 42
        for i, ing in enumerate(recipe.ingredients):
            sy = slot_y + i * (ing_h + 6)
            ing_item = self.sim.item_db.get(ing.item_id)
            if not ing_item:
                continue

            owned = self.sim.inventory.get(ing.item_id, 0)
            needed_total = ing.required_count * self.sim.craft_quantity
            has_enough = (owned >= needed_total) or not self.sim.engine.strict_gating_enabled

            bg_col = Color(20, 32, 24, 255) if has_enough else Color(38, 22, 22, 255)
            border_col = COLOR_GREEN_READY if has_enough else COLOR_RED_MISSING

            draw_rectangle(PANEL_CENTER_X + 20, sy, PANEL_CENTER_W - 40, ing_h, bg_col)
            draw_rectangle_lines(PANEL_CENTER_X + 20, sy, PANEL_CENTER_W - 40, ing_h, border_col)

            # Material Icon
            draw_procedural_craft_icon(ing_item.icon_type, PANEL_CENTER_X + 42, sy + ing_h // 2, 26, is_greyed=(not has_enough))

            # Name & Required Count
            draw_text(ing_item.name, PANEL_CENTER_X + 64, sy + 6, 12, COLOR_WHITE)
            ratio_text = f"Owned: {owned} / Need: {needed_total}"
            draw_text(ratio_text, PANEL_CENTER_X + 64, sy + 22, 10, COLOR_GREEN_READY if has_enough else COLOR_RED_MISSING)

            # Status Checkmark or Deficit Cross
            if has_enough:
                draw_text("[ OK ]", PANEL_CENTER_X + PANEL_CENTER_W - 75, sy + 14, 11, COLOR_GREEN_READY)
            else:
                deficit = needed_total - owned
                draw_text(f"[ -{deficit} ]", PANEL_CENTER_X + PANEL_CENTER_W - 80, sy + 14, 11, COLOR_RED_MISSING)

        # 3. Interactive Bulk Quantity Stepper
        step_y = PANEL_CENTER_Y + 335
        draw_rectangle(PANEL_CENTER_X + 20, step_y, PANEL_CENTER_W - 40, 115, Color(20, 26, 42, 255))
        draw_rectangle_lines(PANEL_CENTER_X + 20, step_y, PANEL_CENTER_W - 40, 115, COLOR_PANEL_BORDER)

        draw_text("BULK CRAFT MULTIPLIER", PANEL_CENTER_X + 30, step_y + 10, 12, COLOR_CYAN_ACCENT)

        btn_y = step_y + 32
        # [-]
        draw_rectangle(PANEL_CENTER_X + 50, btn_y, 40, 34, Color(35, 48, 76, 255))
        draw_rectangle_lines(PANEL_CENTER_X + 50, btn_y, 40, 34, COLOR_SLOT_BORDER)
        draw_text("-", PANEL_CENTER_X + 65, btn_y + 6, 20, COLOR_WHITE)

        # Quantity Display
        draw_rectangle(PANEL_CENTER_X + 100, btn_y, PANEL_CENTER_W - 200, 34, Color(14, 18, 28, 255))
        draw_rectangle_lines(PANEL_CENTER_X + 100, btn_y, PANEL_CENTER_W - 200, 34, COLOR_GOLD_ACCENT)
        draw_text(f"{self.sim.craft_quantity}", PANEL_CENTER_X + PANEL_CENTER_W // 2 - 8, btn_y + 7, 18, COLOR_GOLD_ACCENT)

        # [+]
        draw_rectangle(PANEL_CENTER_X + PANEL_CENTER_W - 90, btn_y, 40, 34, Color(35, 48, 76, 255))
        draw_rectangle_lines(PANEL_CENTER_X + PANEL_CENTER_W - 90, btn_y, 40, 34, COLOR_SLOT_BORDER)
        draw_text("+", PANEL_CENTER_X + PANEL_CENTER_W - 76, btn_y + 6, 20, COLOR_WHITE)

        # Quick Preset Buttons [1], [5], [MAX]
        quick_y = btn_y + 40
        max_q = eval_res.max_craftable if self.sim.engine.strict_gating_enabled else 99
        presets = [("x1", 1), ("x5", 5), ("MAX", max_q)]
        for i, (label, val) in enumerate(presets):
            bx = PANEL_CENTER_X + 65 + i * 105
            is_active = (self.sim.craft_quantity == val and val > 0)
            draw_rectangle(bx, quick_y, 80, 24, Color(45, 60, 92, 255) if is_active else Color(28, 36, 56, 255))
            draw_rectangle_lines(bx, quick_y, 80, 24, COLOR_SLOT_SELECTED if is_active else COLOR_SLOT_BORDER)
            draw_text(label, bx + 26, quick_y + 6, 11, COLOR_WHITE if is_active else COLOR_TEXT_DIM)

        # 4. Craft Action Button
        btn_y = PANEL_CENTER_Y + 462
        btn_w = PANEL_CENTER_W - 40
        btn_x = PANEL_CENTER_X + 20
        btn_h = 44

        can_craft = eval_res.can_craft or not self.sim.engine.strict_gating_enabled
        btn_bg = Color(35, 90, 50, 255) if can_craft else Color(45, 45, 55, 255)
        if self.confirm_button_hover and can_craft:
            btn_bg = Color(50, 130, 75, 255)

        draw_rectangle(btn_x, btn_y, btn_w, btn_h, btn_bg)
        draw_rectangle_lines(btn_x, btn_y, btn_w, btn_h, COLOR_GREEN_READY if can_craft else COLOR_SLOT_BORDER)

        btn_str = f"ASSEMBLE & CRAFT ({recipe.result_count * self.sim.craft_quantity}x {res_item.name})" if can_craft else "CRAFTING BLOCKED (MISSING MATERIALS)"
        draw_text(btn_str, btn_x + btn_w // 2 - 130, btn_y + 14, 13, COLOR_WHITE if can_craft else COLOR_RED_MISSING)

        # 5. Blacksmith Anvil & Workbench Graphic
        draw_anvil_station(PANEL_CENTER_X + PANEL_CENTER_W // 2, PANEL_CENTER_Y + 560, self.sim.anim_timer, self.sim.craft_pulse_timer)

    def draw_inventory_panel(self):
        draw_rectangle(PANEL_RIGHT_X, PANEL_RIGHT_Y, PANEL_RIGHT_W, PANEL_RIGHT_H, COLOR_PANEL_BG)
        draw_rectangle_lines(PANEL_RIGHT_X, PANEL_RIGHT_Y, PANEL_RIGHT_W, PANEL_RIGHT_H, COLOR_PANEL_BORDER)

        # Header
        draw_rectangle(PANEL_RIGHT_X, PANEL_RIGHT_Y, PANEL_RIGHT_W, 36, COLOR_WOOD_DARK)
        draw_text("MATERIAL SATCHEL & SUPPLY", PANEL_RIGHT_X + 16, PANEL_RIGHT_Y + 10, 15, COLOR_GOLD_ACCENT)

        # Quick Testing Resource Rack (Harvest Buttons)
        draw_text("QUICK GATHER (CLICK OR SHIFT+1..5):", PANEL_RIGHT_X + 16, PANEL_RIGHT_Y + 44, 11, COLOR_CYAN_ACCENT)
        rack_y = PANEL_RIGHT_Y + 62
        btn_h = 28
        gather_items = [
            (1, 3, "+ Chop Wood (+3)", Color(125, 80, 45, 255)),
            (2, 2, "+ Mine Iron Ore (+2)", Color(110, 120, 140, 255)),
            (3, 2, "+ Pick Herbs (+2)", Color(55, 145, 75, 255)),
            (4, 3, "+ Gather Feathers (+3)", Color(185, 185, 205, 255)),
            (5, 2, "+ Hunt Leather (+2)", Color(135, 75, 45, 255)),
        ]
        for i, (item_id, count, label, col) in enumerate(gather_items):
            gy = rack_y + i * (btn_h + 4)
            draw_rectangle(PANEL_RIGHT_X + 12, gy, PANEL_RIGHT_W - 24, btn_h, Color(24, 32, 50, 255))
            draw_rectangle_lines(PANEL_RIGHT_X + 12, gy, PANEL_RIGHT_W - 24, btn_h, col)
            draw_text(label, PANEL_RIGHT_X + 24, gy + 8, 11, col)
            cur_stock = self.sim.inventory.get(item_id, 0)
            draw_text(f"Stock: {cur_stock}", PANEL_RIGHT_X + PANEL_RIGHT_W - 85, gy + 8, 11, COLOR_TEXT_MAIN)

        # Divider
        div_y = rack_y + len(gather_items) * (btn_h + 4) + 6
        draw_line(PANEL_RIGHT_X + 12, div_y, PANEL_RIGHT_X + PANEL_RIGHT_W - 12, div_y, COLOR_PANEL_BORDER)

        # Current Material & Crafted Inventory
        draw_text("CURRENT SATCHEL CONTENTS:", PANEL_RIGHT_X + 16, div_y + 8, 11, COLOR_GOLD_ACCENT)

        inv_y = div_y + 26
        slot_h = 36
        row = 0
        for item_id, count in sorted(self.sim.inventory.items()):
            if count <= 0:
                continue
            item = self.sim.item_db.get(item_id)
            if not item:
                continue
            sy = inv_y + row * (slot_h + 4)
            if sy + slot_h > PANEL_RIGHT_Y + PANEL_RIGHT_H - 100:
                break

            draw_rectangle(PANEL_RIGHT_X + 12, sy, PANEL_RIGHT_W - 24, slot_h, COLOR_SLOT_EMPTY)
            draw_rectangle_lines(PANEL_RIGHT_X + 12, sy, PANEL_RIGHT_W - 24, slot_h, COLOR_SLOT_BORDER)

            draw_procedural_craft_icon(item.icon_type, PANEL_RIGHT_X + 28, sy + slot_h // 2, 22)
            draw_text(item.name, PANEL_RIGHT_X + 46, sy + 10, 11, COLOR_TEXT_MAIN)
            draw_text(f"x{count}", PANEL_RIGHT_X + PANEL_RIGHT_W - 55, sy + 10, 12, COLOR_GOLD_ACCENT)
            row += 1

        # Recent Crafted Log at bottom
        log_y = PANEL_RIGHT_Y + PANEL_RIGHT_H - 80
        draw_rectangle(PANEL_RIGHT_X + 12, log_y, PANEL_RIGHT_W - 24, 70, Color(16, 22, 34, 255))
        draw_rectangle_lines(PANEL_RIGHT_X + 12, log_y, PANEL_RIGHT_W - 24, 70, COLOR_PANEL_BORDER)
        draw_text("RECENT CRAFT LOG:", PANEL_RIGHT_X + 18, log_y + 6, 10, COLOR_TEXT_DIM)
        for i, (name, cnt) in enumerate(reversed(self.sim.crafted_history[-3:])):
            draw_text(f"• Produced {cnt}x {name}", PANEL_RIGHT_X + 22, log_y + 20 + i * 16, 10, COLOR_GREEN_READY)

    def draw_toast(self):
        alpha = min(1.0, self.sim.toast_timer * 2.0)
        tw = 460
        th = 40
        tx = (SCREEN_WIDTH - tw) // 2
        ty = SCREEN_HEIGHT - 65

        col_bg = Color(48, 18, 22, int(240 * alpha)) if self.sim.toast_is_error else Color(18, 48, 30, int(240 * alpha))
        col_border = COLOR_RED_MISSING if self.sim.toast_is_error else COLOR_GREEN_READY

        draw_rectangle(tx, ty, tw, th, col_bg)
        draw_rectangle_lines(tx, ty, tw, th, col_border)
        draw_text(self.sim.toast_msg, tx + 20, ty + 12, 13, COLOR_WHITE)

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
    WorkbenchGame().run(smoke_test=is_smoke)

