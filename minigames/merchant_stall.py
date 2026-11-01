# -*- coding: utf-8 -*-
"""
Merchant Stall - Shop Buy/Sell Screen & Transaction Pipeline Architecture
=========================================================================
Section          : 3.1 Menus & UI
Pattern Category : Menus & User Interface, RPG Progression & Economy
Dimension        : 2D

Problem Solved:
  In RPGs, action-adventures, and survival games (Zelda, Diablo, Skyrim, Pokemon,
  Stardew Valley), players regularly trade items with NPC merchants. Naively mutating
  inventories and currencies in-place without an atomic transaction pipeline leads to
  catastrophic exploits: currency underflows/negative gold, item duplication, inventory
  capacity overflow, and economic arbitrage (infinite gold loops when sell-back price
  exceeds or matches purchase price). Furthermore, lacking bulk quantity controls forces
  players into tedious single-item click spam.

How the Pattern Works:
  1. Two-Sided Merchant Ledger & Price Multipliers:
     Both the Merchant and the Player maintain explicit inventory pools and currency
     ledgers. Market values are governed by explicit markup and markdown factors:
       Buy Unit Price  = round(Base_Value * Buy_Markup)    (default 1.00x)
       Sell Unit Price = round(Base_Value * Sell_Markdown) (default 0.50x)
     Because Sell_Markdown < Buy_Markup, economic arbitrage is mathematically impossible.
  2. 3-Stage Atomic Transaction Pipeline:
     Every purchase or sale passes through a rigid validation-execution pipeline:
       Stage 1 (Precondition Check): Verifies stock availability, sufficient currency
               (Player Gold on Buy; Merchant Gold on Sell), and bag capacity limits.
       Stage 2 (Cost Calculation): Multiplies verified quantity by unit price and
               previews projected balances before committing.
       Stage 3 (Atomic Commit): Simultaneously debits/credits currency and transfers
               items in an all-or-nothing step, preventing partial state corruption.
  3. Interactive Bulk Quantity Selector & Clamping:
     A dedicated stepper and quick-button widget ([1], [5], [MAX]) dynamically clamps
     quantities to: min(available_stock, affordability_limit, free_capacity_limit).
  4. Real-Time Economic Arbitrage Telemetry ([Tab] & [F1]):
     Learners can toggle between a Regulated Economy (50% sell markdown, capacity limits)
     and an Exploitable Parity Economy (100% buy/sell parity) to experience firsthand
     how infinite gold exploits emerge when game economies lack markdown friction.

Interactive Learning Controls (Simultaneous Keyboard/Mouse + Gamepad):
  - Left / Right (A / D) / Gamepad Stick   : Switch between Merchant Shelf and Player Satchel
  - Up / Down (W / S) / Gamepad D-Pad      : Navigate highlighted item
  - Mouse Click on Item                    : Select item for Trade / Focus
  - Q / E / Left / Right (on Stepper)      : Decrease / Increase bulk quantity ([-] / [+])
  - [1], [5], [M] / Gamepad X              : Quick Quantity: 1, 5, or Max Affordable/Available
  - Enter / Space / Gamepad A              : Confirm Purchase / Confirm Sale
  - Esc / Backspace / Gamepad B            : Cancel Trade / Deselect Item
  - [Tab] / Gamepad View (Select)          : Toggle X-Ray Telemetry & Pipeline Inspector
  - [F1]  / Gamepad LB                     : Toggle Pattern ON/OFF (Regulated 50% vs Exploitable Parity)
  - [F2]  / Gamepad RB                     : Toggle Haggle / Charisma Perk (+15% Trade Bonus)
  - [Ctrl +/-]                             : Increase / Decrease UI Font Size
  - [F11]                                  : Toggle Fullscreen
  - [R]   / Gamepad Start                  : Reset shop stock, player bag, and currency
"""

import sys
import os
import math
import random
from typing import List, Optional

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
WINDOW_TITLE = "Merchant Stall - Shop Buy/Sell Screen (Raylib Pattern Lab)"

# UI Palette Constants
COLOR_BG               = Color(12, 16, 26, 255)
COLOR_PANEL_BG         = Color(18, 24, 38, 252)
COLOR_PANEL_BORDER     = Color(45, 60, 92, 255)
COLOR_AWNING_RED       = Color(175, 45, 45, 255)
COLOR_AWNING_CREAM     = Color(235, 225, 205, 255)
COLOR_WOOD_DARK        = Color(55, 38, 26, 255)
COLOR_WOOD_LIGHT       = Color(92, 64, 44, 255)

COLOR_SLOT_EMPTY       = Color(14, 19, 30, 255)
COLOR_SLOT_BORDER      = Color(38, 50, 78, 255)
COLOR_SLOT_HOVER       = Color(65, 95, 145, 255)
COLOR_SLOT_SELECTED    = Color(245, 195, 45, 255)
COLOR_ITEM_HOVER       = Color(28, 42, 68, 255)

COLOR_TEXT_MAIN        = Color(235, 242, 255, 255)
COLOR_TEXT_DIM         = Color(140, 160, 190, 255)
COLOR_GOLD_COIN        = Color(255, 205, 55, 255)
COLOR_CYAN_ACCENT      = Color(45, 215, 255, 255)
COLOR_GREEN_SUCCESS    = Color(65, 245, 130, 255)
COLOR_RED_ERROR        = Color(255, 75, 75, 255)
COLOR_PURPLE_ACCENT    = Color(195, 85, 255, 255)
COLOR_WHITE            = Color(255, 255, 255, 255)

# Item Category Constants (C++ Enum equivalent)
CAT_CONSUMABLE = 0
CAT_WEAPON     = 1
CAT_ARMOR      = 2
CAT_MATERIAL   = 3
CAT_TREASURE   = 4

CATEGORY_NAMES = ["Consumable", "Weapon", "Armor", "Material", "Treasure"]
CATEGORY_COLORS = [
    Color(65, 225, 160, 255),   # Consumable: Emerald Green
    Color(255, 105, 95, 255),   # Weapon: Radiant Vermilion
    Color(95, 165, 255, 255),   # Armor: Cerulean Blue
    Color(215, 165, 95, 255),   # Material: Bronze Amber
    Color(245, 195, 45, 255),   # Treasure: Bright Gold
]

# Error Codes (C++ Enum equivalent)
ERR_OK                = 0
ERR_INSUFFICIENT_GOLD = 1
ERR_OUT_OF_STOCK      = 2
ERR_INVENTORY_FULL    = 3
ERR_ZERO_QUANTITY     = 4
ERR_MERCHANT_BROKE    = 5

ERROR_MESSAGES = [
    "Ready for Trade",
    "Insufficient Gold to complete purchase",
    "Merchant has insufficient stock",
    "Player Satchel is full (Capacity reached)",
    "Selected quantity must be greater than zero",
    "Merchant vault has insufficient funds to buy wares"
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

MAX_PLAYER_CAPACITY = 12  # Maximum distinct slots in satchel


# ==============================================================================
# BLOCK 1: CORE PATTERN IMPLEMENTATION (SHOP & TRANSACTION PIPELINE)
# ==============================================================================

class TradeItem:
    """
    Plain struct representing a standardized trade item definition.
    C++ Equivalent:
      struct TradeItem {
          int item_id;
          char name[32];
          int category;
          int base_price;
          int icon_type;
          char lore[64];
          int stat_bonus;
      };
    """
    def __init__(self, item_id: int, name: str, category: int, base_price: int,
                 icon_type: int, lore: str, stat_bonus: int = 0):
        self.item_id = item_id
        self.name = name
        self.category = category
        self.base_price = base_price
        self.icon_type = icon_type
        self.lore = lore
        self.stat_bonus = stat_bonus


class StockEntry:
    """
    Represents an item instance with a specific stock count in an inventory or shop.
    C++ Equivalent:
      struct StockEntry {
          int item_id;
          int quantity;
      };
    """
    def __init__(self, item_id: int, quantity: int):
        self.item_id = item_id
        self.quantity = quantity


class TransactionAudit:
    """
    Represents an immutable record of an executed trade for telemetry and logging.
    C++ Equivalent:
      struct TransactionAudit {
          bool is_buy;
          int item_id;
          int quantity;
          int unit_price;
          int total_gold;
          int player_gold_after;
      };
    """
    def __init__(self, is_buy: bool, item_name: str, quantity: int,
                 unit_price: int, total_gold: int, player_gold_after: int):
        self.is_buy = is_buy
        self.item_name = item_name
        self.quantity = quantity
        self.unit_price = unit_price
        self.total_gold = total_gold
        self.player_gold_after = player_gold_after


class ShopTransactionPipeline:
    """
    Atomic Trade Engine.
    Enforces validation pre-conditions, calculates dynamic economic pricing,
    and performs all-or-nothing ledger commits to prevent state desynchronization.
    """
    def __init__(self):
        # Pricing factors
        self.base_buy_markup = 1.00      # 100% of base value
        self.base_sell_markdown = 0.50   # 50% of base value (prevents arbitrage)
        self.haggle_unlocked = False     # +15% trade reputation bonus
        self.regulated_economy = True    # Pattern ON (50% markdown) vs OFF (100% parity)

    def get_effective_buy_multiplier(self) -> float:
        """Calculates buyer multiplier after charisma / haggle discounts."""
        mult = self.base_buy_markup
        if self.haggle_unlocked:
            mult -= 0.15  # 15% discount for player purchases
        return max(0.20, mult)

    def get_effective_sell_multiplier(self) -> float:
        """Calculates seller markdown. Under parity mode, markdown equals buy markup."""
        if not self.regulated_economy:
            # Exploitable Parity Mode: 100% parity creates infinite gold loops
            return 1.00
        mult = self.base_sell_markdown
        if self.haggle_unlocked:
            mult += 0.15  # 15% bonus for player sales
        return min(0.95, mult)

    def calculate_unit_price(self, base_price: int, is_buy: bool) -> int:
        """
        Computes integer unit price for buying or selling.
        Ensures unit price is at least 1 Gold.
        """
        if is_buy:
            rate = self.get_effective_buy_multiplier()
            return max(1, int(round(base_price * rate)))
        else:
            rate = self.get_effective_sell_multiplier()
            return max(1, int(round(base_price * rate)))

    def validate_preconditions(
        self,
        is_buy: bool,
        item: TradeItem,
        quantity: int,
        player_gold: int,
        merchant_gold: int,
        available_stock: int,
        player_distinct_item_count: int,
        player_already_owns_item: bool
    ) -> int:
        """
        Stage 1 of Atomic Pipeline: Rigidly checks all constraints.
        Returns ERR_OK if safe to proceed, or a specific ERR_* code.
        """
        if quantity <= 0:
            return ERR_ZERO_QUANTITY

        if quantity > available_stock:
            return ERR_OUT_OF_STOCK

        unit_price = self.calculate_unit_price(item.base_price, is_buy)
        total_cost = unit_price * quantity

        if is_buy:
            if player_gold < total_cost:
                return ERR_INSUFFICIENT_GOLD

            # In regulated mode, player inventory cannot exceed maximum slots
            if self.regulated_economy:
                if not player_already_owns_item and player_distinct_item_count >= MAX_PLAYER_CAPACITY:
                    return ERR_INVENTORY_FULL
        else:
            # Selling to merchant
            if self.regulated_economy:
                if merchant_gold < total_cost:
                    return ERR_MERCHANT_BROKE

        return ERR_OK

    def execute_transaction(
        self,
        is_buy: bool,
        item: TradeItem,
        quantity: int,
        player_gold: int,
        merchant_gold: int
    ) -> tuple:
        """
        Stage 3 of Atomic Pipeline: Calculates the atomic balance transfers.
        Returns: (new_player_gold, new_merchant_gold, total_cost, unit_price)
        """
        unit_price = self.calculate_unit_price(item.base_price, is_buy)
        total_cost = unit_price * quantity

        if is_buy:
            new_player_gold = player_gold - total_cost
            new_merchant_gold = merchant_gold + total_cost
        else:
            new_player_gold = player_gold + total_cost
            new_merchant_gold = merchant_gold - total_cost

        return (new_player_gold, new_merchant_gold, total_cost, unit_price)


# ==============================================================================
# BLOCK 2: WORLD SIMULATION & ENTITIES (STALL, ROSTER & PROCEDURAL GRAPHICS)
# ==============================================================================

def create_item_catalog() -> List[TradeItem]:
    """Generates the master database of items with balanced values and stats."""
    return [
        TradeItem(1, "Healing Draught", CAT_CONSUMABLE, 30, 0, "Restores 50 Vitality points", stat_bonus=50),
        TradeItem(2, "Mana Elixir", CAT_CONSUMABLE, 45, 1, "Restores 40 Mana points", stat_bonus=40),
        TradeItem(3, "Iron Broadsword", CAT_WEAPON, 120, 2, "Tempered steel blade. +18 Attack", stat_bonus=18),
        TradeItem(4, "Heater Shield", CAT_ARMOR, 95, 3, "Reinforced oak and iron. +14 Defense", stat_bonus=14),
        TradeItem(5, "Hunter's Recurve", CAT_WEAPON, 140, 4, "Flexible yew wood. +22 Attack", stat_bonus=22),
        TradeItem(6, "Leather Jerkin", CAT_ARMOR, 60, 5, "Supple boiled leather. +8 Defense", stat_bonus=8),
        TradeItem(7, "Antidote Flask", CAT_CONSUMABLE, 25, 6, "Neutralizes toxic serpent venoms", stat_bonus=1),
        TradeItem(8, "Phoenix Feather", CAT_CONSUMABLE, 250, 7, "Revives fallen party members", stat_bonus=100),
        TradeItem(9, "Waybread Rations", CAT_CONSUMABLE, 10, 8, "Nutritious travel bread. +15 Vitality", stat_bonus=15),
        TradeItem(10, "Flawless Ruby", CAT_TREASURE, 300, 9, "Radiant cut gemstone of high worth", stat_bonus=0),
        TradeItem(11, "Boar Tusk", CAT_MATERIAL, 20, 10, "Dense tusk for tool crafting", stat_bonus=0),
        TradeItem(12, "Wolf Pelt", CAT_MATERIAL, 35, 11, "Thick winter fur in high demand", stat_bonus=0),
        TradeItem(13, "Goblin Ear", CAT_MATERIAL, 15, 12, "Proof of guild bounty completion", stat_bonus=0),
        TradeItem(14, "Cracked Emerald", CAT_TREASURE, 180, 13, "Slightly fractured beryl gem", stat_bonus=0),
    ]


class MerchantStallSimulation:
    """Manages the full state of the shop, player satchel, and active trade desk."""
    def __init__(self):
        self.catalog = create_item_catalog()
        self.catalog_map = {}
        for it in self.catalog:
            self.catalog_map[it.item_id] = it

        self.pipeline = ShopTransactionPipeline()
        self.reset_state()

        # UI & Animation timers
        self.anim_timer = 0.0
        self.merchant_talk_timer = 0.0
        self.merchant_dialogue = "Welcome traveler! Fresh supplies from the capital."
        self.toast_msg = ""
        self.toast_timer = 0.0
        self.toast_is_error = False

        # Selection state
        self.active_side = 0       # 0 = Merchant Wares (Buy), 1 = Player Satchel (Sell)
        self.selected_item_id = 1  # Currently selected item
        self.trade_quantity = 1    # Chosen quantity in stepper
        self.confirm_button_hover = False
        self.cancel_button_hover = False

    def reset_state(self):
        """Restores initial gold reserves and stock entries for both parties."""
        self.player_gold = 280
        self.merchant_gold = 1500

        # Merchant stock (Catalog items with quantities)
        self.merchant_stock = [
            StockEntry(1, 12),  # Healing Draught x12
            StockEntry(2, 8),   # Mana Elixir x8
            StockEntry(3, 3),   # Iron Broadsword x3
            StockEntry(4, 2),   # Heater Shield x2
            StockEntry(5, 2),   # Hunter's Recurve x2
            StockEntry(6, 4),   # Leather Jerkin x4
            StockEntry(7, 15),  # Antidote Flask x15
            StockEntry(8, 1),   # Phoenix Feather x1
            StockEntry(9, 25),  # Waybread Rations x25
            StockEntry(10, 2),  # Flawless Ruby x2
        ]

        # Player satchel items
        self.player_stock = [
            StockEntry(1, 3),   # Healing Draught x3
            StockEntry(11, 5),  # Boar Tusk x5
            StockEntry(12, 4),  # Wolf Pelt x4
            StockEntry(13, 8),  # Goblin Ear x8
            StockEntry(14, 1),  # Cracked Emerald x1
        ]

        self.audit_log: List[TransactionAudit] = []
        self.selected_item_id = 1
        self.trade_quantity = 1

    def get_merchant_stock_count(self, item_id: int) -> int:
        for entry in self.merchant_stock:
            if entry.item_id == item_id:
                return entry.quantity
        return 0

    def get_player_stock_count(self, item_id: int) -> int:
        for entry in self.player_stock:
            if entry.item_id == item_id:
                return entry.quantity
        return 0

    def get_selected_item(self) -> Optional[TradeItem]:
        if self.selected_item_id in self.catalog_map:
            return self.catalog_map[self.selected_item_id]
        return None

    def calculate_max_trade_quantity(self, is_buy: bool, item: TradeItem) -> int:
        """Computes the maximum safe quantity the player can trade right now."""
        unit_price = self.pipeline.calculate_unit_price(item.base_price, is_buy)
        if unit_price <= 0:
            return 1

        if is_buy:
            available = self.get_merchant_stock_count(item.item_id)
            if available <= 0:
                return 0
            affordable = self.player_gold // unit_price
            return max(0, min(available, affordable))
        else:
            owned = self.get_player_stock_count(item.item_id)
            if owned <= 0:
                return 0
            if self.pipeline.regulated_economy:
                merchant_can_afford = self.merchant_gold // unit_price
                return max(0, min(owned, merchant_can_afford))
            return owned

    def commit_trade(self, sfx: SoundLibrary) -> bool:
        """Executes the transaction through the atomic pipeline."""
        item = self.get_selected_item()
        if not item:
            return False

        is_buy = (self.active_side == 0)
        avail = self.get_merchant_stock_count(item.item_id) if is_buy else self.get_player_stock_count(item.item_id)
        player_owns = (self.get_player_stock_count(item.item_id) > 0)
        player_slots = len(self.player_stock)

        err = self.pipeline.validate_preconditions(
            is_buy=is_buy,
            item=item,
            quantity=self.trade_quantity,
            player_gold=self.player_gold,
            merchant_gold=self.merchant_gold,
            available_stock=avail,
            player_distinct_item_count=player_slots,
            player_already_owns_item=player_owns
        )

        if err != ERR_OK:
            self.toast_msg = ERROR_MESSAGES[err]
            self.toast_timer = 2.5
            self.toast_is_error = True
            sfx.play("hurt", 0.7)
            return False

        # Atomic commit
        new_p_gold, new_m_gold, total_cost, unit_p = self.pipeline.execute_transaction(
            is_buy, item, self.trade_quantity, self.player_gold, self.merchant_gold
        )
        self.player_gold = new_p_gold
        self.merchant_gold = new_m_gold

        if is_buy:
            # Deduct from merchant
            for entry in self.merchant_stock:
                if entry.item_id == item.item_id:
                    entry.quantity -= self.trade_quantity
                    break
            # Add to player
            found = False
            for entry in self.player_stock:
                if entry.item_id == item.item_id:
                    entry.quantity += self.trade_quantity
                    found = True
                    break
            if not found:
                self.player_stock.append(StockEntry(item.item_id, self.trade_quantity))

            self.merchant_dialogue = f"A fine choice! May the {item.name} serve you well."
            self.toast_msg = f"Bought {self.trade_quantity}x {item.name} for {total_cost} Gold!"
        else:
            # Deduct from player
            rem_entry = None
            for entry in self.player_stock:
                if entry.item_id == item.item_id:
                    entry.quantity -= self.trade_quantity
                    if entry.quantity <= 0:
                        rem_entry = entry
                    break
            if rem_entry and rem_entry in self.player_stock:
                self.player_stock.remove(rem_entry)

            # Add to merchant
            found = False
            for entry in self.merchant_stock:
                if entry.item_id == item.item_id:
                    entry.quantity += self.trade_quantity
                    found = True
                    break
            if not found:
                self.merchant_stock.append(StockEntry(item.item_id, self.trade_quantity))

            self.merchant_dialogue = f"Fair trade! These {item.name} will find a good home."
            self.toast_msg = f"Sold {self.trade_quantity}x {item.name} for {total_cost} Gold!"

        # Record audit log
        audit = TransactionAudit(
            is_buy=is_buy,
            item_name=item.name,
            quantity=self.trade_quantity,
            unit_price=unit_p,
            total_gold=total_cost,
            player_gold_after=self.player_gold
        )
        self.audit_log.append(audit)
        if len(self.audit_log) > 6:
            self.audit_log.pop(0)

        self.toast_timer = 2.5
        self.toast_is_error = False
        sfx.play("coin", 0.9)

        # Reset quantity to safe value
        max_q = self.calculate_max_trade_quantity(is_buy, item)
        self.trade_quantity = max(1, min(self.trade_quantity, max_q)) if max_q > 0 else 0
        return True


# ==============================================================================
# PROCEDURAL DRAWING UTILITIES FOR ITEMS, ICONS & STALL
# ==============================================================================

def draw_procedural_item_icon(icon_type: int, center_x: int, center_y: int, size: int):
    """
    Renders distinct, high-clarity 2D procedural geometric icons for game items.
    C++ Equivalent: Raylib 2D primitive render calls using circles, rectangles & triangles.
    """
    half = size // 2
    cx = center_x
    cy = center_y

    # Outer subtle dark badge backing
    draw_circle(cx, cy, half + 2, Color(16, 22, 34, 255))
    draw_circle_lines(cx, cy, half + 2, Color(45, 60, 90, 255))

    if icon_type in (0, 1, 6):  # Potion Flasks (Red, Blue, Green)
        flask_col = Color(245, 65, 80, 255) if icon_type == 0 else (
            Color(55, 175, 255, 255) if icon_type == 1 else Color(65, 235, 110, 255)
        )
        # Cork
        draw_rectangle(cx - 3, cy - half + 4, 6, 4, Color(170, 125, 75, 255))
        # Neck
        draw_rectangle(cx - 2, cy - half + 8, 4, 6, Color(180, 200, 225, 200))
        # Bulb
        draw_circle(cx, cy + 4, half - 7, flask_col)
        draw_circle(cx - 3, cy + 1, half - 11, Color(255, 255, 255, 120))  # Specular highlight
        draw_circle_lines(cx, cy + 4, half - 7, Color(220, 235, 255, 255))

    elif icon_type == 2:  # Iron Broadsword
        # Blade
        draw_line_ex(Vector2(cx - half + 8, cy + half - 8), Vector2(cx + half - 7, cy - half + 7), 4.0, Color(210, 225, 245, 255))
        # Crossguard
        draw_line_ex(Vector2(cx - 3, cy + 9), Vector2(cx - 9, cy + 3), 4.0, Color(245, 195, 45, 255))
        # Grip & Pommel
        draw_circle(cx - half + 6, cy + half - 6, 3, Color(185, 135, 45, 255))

    elif icon_type == 3:  # Heater Shield
        # Shield shape (curved triangle / rectangle)
        draw_rectangle(cx - half + 7, cy - half + 7, (half - 7) * 2, half, Color(65, 95, 155, 255))
        draw_triangle(
            Vector2(cx - half + 7, cy),
            Vector2(cx, cy + half - 5),
            Vector2(cx + half - 7, cy),
            Color(65, 95, 155, 255)
        )
        # Gold cross heraldry
        draw_rectangle(cx - 2, cy - half + 9, 4, half + 4, Color(255, 215, 60, 255))
        draw_rectangle(cx - half + 9, cy - 4, (half - 9) * 2, 4, Color(255, 215, 60, 255))

    elif icon_type == 4:  # Hunter's Bow
        # Wooden Arc
        draw_circle_lines(cx - half + 10, cy, half - 4, Color(145, 95, 50, 255))
        # Bowstring
        draw_line(cx + half - 12, cy - half + 8, cx + half - 12, cy + half - 8, Color(220, 220, 220, 255))
        # Nocked Arrow
        draw_line(cx - 6, cy, cx + half - 6, cy, Color(255, 215, 60, 255))

    elif icon_type == 5:  # Leather Jerkin
        draw_rectangle(cx - half + 8, cy - half + 8, (half - 8) * 2, (half - 8) * 2, Color(125, 80, 45, 255))
        draw_circle(cx, cy - half + 8, 4, Color(16, 22, 34, 255))  # Neck collar cut
        draw_line(cx, cy - half + 12, cx, cy + half - 8, Color(75, 45, 25, 255))  # Lacing

    elif icon_type == 7:  # Phoenix Feather
        draw_line_ex(Vector2(cx - half + 8, cy + half - 8), Vector2(cx + half - 7, cy - half + 7), 3.0, Color(255, 195, 45, 255))
        draw_circle(cx + 2, cy - 2, 6, Color(255, 85, 40, 220))
        draw_circle(cx - 2, cy + 2, 4, Color(255, 225, 80, 255))

    elif icon_type == 8:  # Waybread
        draw_circle(cx, cy, half - 7, Color(195, 145, 85, 255))
        draw_line(cx - 5, cy - 3, cx + 5, cy + 3, Color(135, 90, 45, 255))
        draw_line(cx - 3, cy + 4, cx + 4, cy - 4, Color(135, 90, 45, 255))

    elif icon_type in (9, 13):  # Ruby / Emerald Gemstones
        gem_col = Color(255, 55, 85, 255) if icon_type == 9 else Color(45, 225, 120, 255)
        draw_triangle(
            Vector2(cx, cy - half + 6),
            Vector2(cx - half + 8, cy),
            Vector2(cx + half - 8, cy),
            gem_col
        )
        draw_triangle(
            Vector2(cx - half + 8, cy),
            Vector2(cx, cy + half - 6),
            Vector2(cx + half - 8, cy),
            gem_col
        )
        draw_circle(cx, cy - 2, 3, Color(255, 255, 255, 180))

    elif icon_type == 10:  # Boar Tusk
        draw_line_ex(Vector2(cx - half + 8, cy + half - 8), Vector2(cx + half - 6, cy - half + 10), 5.0, Color(240, 235, 215, 255))
        draw_circle(cx + half - 6, cy - half + 10, 3, Color(255, 250, 235, 255))

    elif icon_type == 11:  # Wolf Pelt
        draw_rectangle(cx - half + 7, cy - half + 9, (half - 7) * 2, (half - 9) * 2, Color(145, 150, 165, 255))
        draw_circle(cx, cy, 5, Color(110, 115, 130, 255))

    elif icon_type == 12:  # Goblin Ear
        draw_triangle(
            Vector2(cx - half + 8, cy + half - 6),
            Vector2(cx + half - 6, cy - half + 6),
            Vector2(cx, cy + half - 8),
            Color(105, 175, 75, 255)
        )
    else:
        # Generic Item
        draw_circle(cx, cy, half - 8, Color(180, 180, 210, 255))


def draw_merchant_awning(x: int, y: int, w: int, h: int):
    """Renders a procedural striped canopy awning for the merchant stall."""
    draw_rectangle(x, y, w, h, COLOR_WOOD_DARK)
    stripe_w = 26
    num_stripes = w // stripe_w + 1
    for i in range(num_stripes):
        sx = x + i * stripe_w
        if sx + stripe_w > x + w:
            sw = (x + w) - sx
        else:
            sw = stripe_w
        if sw > 0:
            col = COLOR_AWNING_RED if (i % 2 == 0) else COLOR_AWNING_CREAM
            draw_rectangle(sx, y, sw, h, col)
            # Scalloped valance trim at bottom
            draw_circle(sx + sw // 2, y + h, sw // 2, col)

    # Awning shadow line and wooden support beam
    draw_rectangle(x, y + h, w, 4, Color(0, 0, 0, 90))
    draw_rectangle(x, y + h + 4, w, 6, COLOR_WOOD_LIGHT)


# ==============================================================================
# BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY ([Tab] & [F1])
# ==============================================================================

def draw_xray_telemetry_overlay(sim: MerchantStallSimulation):
    """
    Renders diagnostic telemetry exposing the underlying transaction pipeline,
    mathematical proof of arbitrage prevention, and atomic validation state.
    """
    # Dark translucent modal backing
    draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, Color(6, 8, 14, 235))

    ox = 120
    oy = 80
    ow = SCREEN_WIDTH - 240
    oh = SCREEN_HEIGHT - 160

    draw_rectangle(ox, oy, ow, oh, Color(16, 22, 36, 255))
    draw_rectangle_lines(ox, oy, ow, oh, COLOR_CYAN_ACCENT)

    # Header
    draw_text("[X-RAY TELEMETRY] SHOP TRANSACTION PIPELINE & ECONOMIC ARBITRAGE PROOF", ox + 24, oy + 20, 20, COLOR_GOLD_COIN)
    draw_line(ox + 20, oy + 50, ox + ow - 20, oy + 50, COLOR_PANEL_BORDER)

    # Column 1: Pipeline Architecture & State Machine
    cx1 = ox + 30
    draw_text("1. ATOMIC TRANSACTION PIPELINE STAGES", cx1, oy + 65, 16, COLOR_CYAN_ACCENT)

    stages = [
        ("STAGE 1: PRECONDITIONS", "Check stock >= Qty, Funds >= Cost, Bag < Capacity"),
        ("STAGE 2: PRICE CALC",   "Unit_Price = round(Base * Multiplier), Total = Qty * Unit"),
        ("STAGE 3: ATOMIC COMMIT", "Simultaneous double-entry currency & inventory swap"),
        ("STAGE 4: AUDIT LOG",     "Push immutable ledger entry for history & undo verification")
    ]
    sy = oy + 95
    for title, desc in stages:
        draw_rectangle(cx1, sy, 460, 48, Color(24, 32, 50, 255))
        draw_rectangle_lines(cx1, sy, 460, 48, Color(55, 75, 115, 255))
        draw_text(title, cx1 + 12, sy + 8, 13, COLOR_GREEN_SUCCESS)
        draw_text(desc, cx1 + 12, sy + 26, 11, COLOR_TEXT_DIM)
        sy += 56

    # Column 2: Arbitrage Math & Comparison
    cx2 = ox + 520
    draw_text("2. ECONOMIC ARBITRAGE PREVENTION MATHEMATICS", cx2, oy + 65, 16, COLOR_CYAN_ACCENT)

    bx = cx2
    by = oy + 95
    draw_rectangle(bx, by, 480, 224, Color(24, 32, 50, 255))
    draw_rectangle_lines(bx, by, 480, 224, Color(55, 75, 115, 255))

    buy_m = sim.pipeline.get_effective_buy_multiplier()
    sell_m = sim.pipeline.get_effective_sell_multiplier()
    margin_diff = buy_m - sell_m

    draw_text("Formula: Unit_Buy = Base * M_buy  |  Unit_Sell = Base * M_sell", bx + 14, by + 12, 13, COLOR_WHITE)
    draw_text(f"Current Buy Multiplier  (M_buy)  : {buy_m:.2f}x", bx + 14, by + 36, 13, COLOR_GOLD_COIN)
    draw_text(f"Current Sell Multiplier (M_sell) : {sell_m:.2f}x", bx + 14, by + 56, 13, COLOR_CYAN_ACCENT)
    draw_text(f"Economic Friction Margin (Delta) : {margin_diff:.2f}x", bx + 14, by + 76, 13, COLOR_GREEN_SUCCESS if margin_diff > 0 else COLOR_RED_ERROR)

    proof_text_1 = "PROOF: Infinite gold exploit requires M_sell >= M_buy."
    proof_text_2 = "Under Regulated Economy (M_sell = 0.50x), every trade cycle"
    proof_text_3 = "leaks 50% value as sink, rendering arbitrage impossible."
    proof_text_4 = "Under Parity Mode (F1: OFF), M_sell = 1.00x creates risk-free"
    proof_text_5 = "churn where buying and selling back nets zero loss."

    draw_text(proof_text_1, bx + 14, by + 105, 12, COLOR_GOLD_COIN)
    draw_text(proof_text_2, bx + 14, by + 125, 11, COLOR_TEXT_DIM)
    draw_text(proof_text_3, bx + 14, by + 142, 11, COLOR_TEXT_DIM)
    draw_text(proof_text_4, bx + 14, by + 165, 11, COLOR_RED_ERROR if not sim.pipeline.regulated_economy else COLOR_TEXT_DIM)
    draw_text(proof_text_5, bx + 14, by + 182, 11, COLOR_RED_ERROR if not sim.pipeline.regulated_economy else COLOR_TEXT_DIM)

    # Bottom Area: C++ Struct Memory Layout
    by2 = oy + 335
    draw_text("3. C++ EQUIVALENT DATA STRUCTURES & MEMORY FOOTPRINT", cx1, by2, 16, COLOR_CYAN_ACCENT)
    struct_box_y = by2 + 25
    draw_rectangle(cx1, struct_box_y, ow - 60, 110, Color(20, 26, 42, 255))
    draw_rectangle_lines(cx1, struct_box_y, ow - 60, 110, Color(45, 60, 95, 255))

    cpp_code = [
        "struct TradeItem { int id; char name[32]; int category; int base_price; int icon_type; }; // 48 bytes",
        "struct StockEntry { int item_id; int quantity; };                                          // 8 bytes",
        "struct TransactionAudit { bool is_buy; int item_id; int qty; int unit_p; int total_g; };  // 20 bytes",
        "ShopState: sizeof(Catalog[14]) = 672B | sizeof(PlayerBag[12]) = 96B | sizeof(Audit[6]) = 120B. Total < 1 KB!"
    ]
    for i, line in enumerate(cpp_code):
        draw_text(line, cx1 + 16, struct_box_y + 12 + i * 22, 12, COLOR_TEXT_MAIN)

    # Footer note
    draw_text("Press [Tab] or Gamepad Y to dismiss X-Ray Telemetry Inspector", ox + ow // 2 - 200, oy + oh - 28, 13, COLOR_TEXT_DIM)


# ==============================================================================
# BLOCK 4: MAIN GAME LOOP & AUTOMATED SMOKE TEST
# ==============================================================================

class MerchantStallGame:
    def __init__(self):
        init_window(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        set_target_fps(60)
        init_audio_device()

        self.sfx = SoundLibrary()
        self.sfx.init_defaults()

        self.sim = MerchantStallSimulation()
        self.show_xray = True  # Default ON for pedagogical clarity

        # Merchant procedural sprite palette
        self.merchant_palette = {
            "armor": Color(135, 85, 45, 255),    # Brown leather merchant vest
            "accent": Color(255, 215, 60, 255),  # Gold brooch & trim
            "skin": Color(230, 195, 165, 255),   # Human skin tone
            "weapon": Color(175, 135, 85, 255),  # Merchant wooden walking stick
            "joint": Color(50, 35, 25, 255)      # Sturdy boots
        }

    def handle_input(self, dt: float):
        # 1. Toggles
        if is_dual_xray_toggle_pressed():
            self.show_xray = not self.show_xray
            self.sfx.play("click", 0.6)

        if is_dual_pattern_toggle_pressed():  # F1 / Gamepad LB
            self.sim.pipeline.regulated_economy = not self.sim.pipeline.regulated_economy
            mode_str = "REGULATED (50% Markdown)" if self.sim.pipeline.regulated_economy else "EXPLOITABLE PARITY (100% Arbitrage)"
            self.sim.toast_msg = f"Economy Mode: {mode_str}"
            self.sim.toast_timer = 2.5
            self.sim.toast_is_error = not self.sim.pipeline.regulated_economy
            self.sfx.play("click", 0.8)

        if is_dual_secondary_toggle_pressed():  # F2 / Gamepad RB
            self.sim.pipeline.haggle_unlocked = not self.sim.pipeline.haggle_unlocked
            status = "ACTIVE (+15% Trade Bonus)" if self.sim.pipeline.haggle_unlocked else "OFF (Normal Margins)"
            self.sim.toast_msg = f"Haggle Perk: {status}"
            self.sim.toast_timer = 2.0
            self.sim.toast_is_error = False
            self.sfx.play("powerup", 0.7)

        if is_dual_reset_pressed():  # R / Gamepad Start
            self.sim.reset_state()
            self.sim.toast_msg = "Shop Roster & Player Purse Reset to Default"
            self.sim.toast_timer = 2.0
            self.sim.toast_is_error = False
            self.sfx.play("click", 0.7)

        # 2. Navigation between sides (Left: Merchant, Right: Player)
        move_vec = get_dual_move_2d()
        if is_key_pressed(KEY_A) or is_key_pressed(KEY_LEFT) or (is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_LEFT) if is_gamepad_available(0) else False):
            if self.sim.active_side != 0:
                self.sim.active_side = 0
                if len(self.sim.merchant_stock) > 0:
                    self.sim.selected_item_id = self.sim.merchant_stock[0].item_id
                    item = self.sim.get_selected_item()
                    if item:
                        self.sim.trade_quantity = max(1, min(self.sim.trade_quantity, self.sim.calculate_max_trade_quantity(True, item)))
                self.sfx.play("click", 0.5)

        if is_key_pressed(KEY_D) or is_key_pressed(KEY_RIGHT) or (is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_RIGHT) if is_gamepad_available(0) else False):
            if self.sim.active_side != 1:
                self.sim.active_side = 1
                if len(self.sim.player_stock) > 0:
                    self.sim.selected_item_id = self.sim.player_stock[0].item_id
                    item = self.sim.get_selected_item()
                    if item:
                        self.sim.trade_quantity = max(1, min(self.sim.trade_quantity, self.sim.calculate_max_trade_quantity(False, item)))
                self.sfx.play("click", 0.5)

        # 3. Item list vertical navigation
        if is_key_pressed(KEY_W) or is_key_pressed(KEY_UP) or (is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_UP) if is_gamepad_available(0) else False):
            self.cycle_selected_item(-1)
        if is_key_pressed(KEY_S) or is_key_pressed(KEY_DOWN) or (is_gamepad_button_pressed(0, GAMEPAD_BUTTON_LEFT_FACE_DOWN) if is_gamepad_available(0) else False):
            self.cycle_selected_item(1)

        # 4. Quantity Adjustments (Q / E or [-] / [+])
        item = self.sim.get_selected_item()
        if item:
            is_buy = (self.sim.active_side == 0)
            max_q = self.sim.calculate_max_trade_quantity(is_buy, item)

            if is_key_pressed(KEY_Q) or is_key_pressed(KEY_MINUS):
                if self.sim.trade_quantity > 1:
                    self.sim.trade_quantity -= 1
                    self.sfx.play("click", 0.4)
            if is_key_pressed(KEY_E) or is_key_pressed(KEY_EQUAL):
                if self.sim.trade_quantity < max_q:
                    self.sim.trade_quantity += 1
                    self.sfx.play("click", 0.4)

            # Quick shortcuts: 1, 5, MAX
            if is_key_pressed(KEY_ONE):
                self.sim.trade_quantity = 1
                self.sfx.play("click", 0.4)
            if is_key_pressed(KEY_FIVE):
                self.sim.trade_quantity = max(1, min(5, max_q))
                self.sfx.play("click", 0.4)
            if is_key_pressed(KEY_M) or (is_gamepad_button_pressed(0, GAMEPAD_BUTTON_RIGHT_FACE_LEFT) if is_gamepad_available(0) else False):
                self.sim.trade_quantity = max(1, max_q) if max_q > 0 else 0
                self.sfx.play("click", 0.5)

        # 5. Confirm Trade (Enter / Space / Gamepad A)
        if is_dual_primary_fire_pressed() or is_key_pressed(KEY_ENTER) or is_key_pressed(KEY_SPACE):
            self.sim.commit_trade(self.sfx)

        # 6. Mouse clicks on items, stepper buttons, and confirm button
        self.handle_mouse_interaction()

    def cycle_selected_item(self, direction: int):
        stock_list = self.sim.merchant_stock if self.sim.active_side == 0 else self.sim.player_stock
        if not stock_list:
            return

        cur_idx = 0
        for i, entry in enumerate(stock_list):
            if entry.item_id == self.sim.selected_item_id:
                cur_idx = i
                break

        new_idx = (cur_idx + direction) % len(stock_list)
        self.sim.selected_item_id = stock_list[new_idx].item_id
        item = self.sim.get_selected_item()
        if item:
            is_buy = (self.sim.active_side == 0)
            max_q = self.sim.calculate_max_trade_quantity(is_buy, item)
            self.sim.trade_quantity = max(1, min(self.sim.trade_quantity, max_q)) if max_q > 0 else 0
        self.sfx.play("click", 0.4)

    def handle_mouse_interaction(self):
        m_pos = get_mouse_position()
        mx = int(m_pos.x)
        my = int(m_pos.y)
        m_clicked = is_mouse_button_pressed(MOUSE_BUTTON_LEFT)

        # 1. Merchant Item list clicks (Left panel)
        list_y = PANEL_LEFT_Y + 180
        slot_h = 44
        for i, entry in enumerate(self.sim.merchant_stock):
            sy = list_y + i * (slot_h + 4)
            if PANEL_LEFT_X + 10 <= mx <= PANEL_LEFT_X + PANEL_LEFT_W - 10 and sy <= my <= sy + slot_h:
                if m_clicked:
                    self.sim.active_side = 0
                    self.sim.selected_item_id = entry.item_id
                    item = self.sim.get_selected_item()
                    if item:
                        max_q = self.sim.calculate_max_trade_quantity(True, item)
                        self.sim.trade_quantity = max(1, min(self.sim.trade_quantity, max_q)) if max_q > 0 else 0
                    self.sfx.play("click", 0.5)

        # 2. Player Item list clicks (Right panel)
        p_list_y = PANEL_RIGHT_Y + 110
        for i, entry in enumerate(self.sim.player_stock):
            sy = p_list_y + i * (slot_h + 4)
            if PANEL_RIGHT_X + 10 <= mx <= PANEL_RIGHT_X + PANEL_RIGHT_W - 10 and sy <= my <= sy + slot_h:
                if m_clicked:
                    self.sim.active_side = 1
                    self.sim.selected_item_id = entry.item_id
                    item = self.sim.get_selected_item()
                    if item:
                        max_q = self.sim.calculate_max_trade_quantity(False, item)
                        self.sim.trade_quantity = max(1, min(self.sim.trade_quantity, max_q)) if max_q > 0 else 0
                    self.sfx.play("click", 0.5)

        # 3. Center Desk controls
        # Stepper buttons: [-] and [+]
        step_y = PANEL_CENTER_Y + 360
        btn_minus = (PANEL_CENTER_X + 60, step_y, 42, 38)
        btn_plus  = (PANEL_CENTER_X + PANEL_CENTER_W - 102, step_y, 42, 38)

        item = self.sim.get_selected_item()
        if item:
            is_buy = (self.sim.active_side == 0)
            max_q = self.sim.calculate_max_trade_quantity(is_buy, item)

            if btn_minus[0] <= mx <= btn_minus[0] + btn_minus[2] and btn_minus[1] <= my <= btn_minus[1] + btn_minus[3]:
                if m_clicked and self.sim.trade_quantity > 1:
                    self.sim.trade_quantity -= 1
                    self.sfx.play("click", 0.4)

            if btn_plus[0] <= mx <= btn_plus[0] + btn_plus[2] and btn_plus[1] <= my <= btn_plus[1] + btn_plus[3]:
                if m_clicked and self.sim.trade_quantity < max_q:
                    self.sim.trade_quantity += 1
                    self.sfx.play("click", 0.4)

            # Quick buttons [1], [5], [MAX]
            quick_y = step_y + 46
            q_btns = [
                (PANEL_CENTER_X + 80, quick_y, 70, 26, 1),
                (PANEL_CENTER_X + 180, quick_y, 70, 26, 5),
                (PANEL_CENTER_X + 280, quick_y, 70, 26, max_q)
            ]
            for bx, by, bw, bh, q_val in q_btns:
                if bx <= mx <= bx + bw and by <= my <= by + bh:
                    if m_clicked:
                        self.sim.trade_quantity = max(1, min(q_val, max_q)) if max_q > 0 else 0
                        self.sfx.play("click", 0.4)

        # Confirm Trade Button
        btn_trade_y = PANEL_CENTER_Y + 490
        btn_trade_w = PANEL_CENTER_W - 60
        btn_trade_x = PANEL_CENTER_X + 30
        btn_trade_h = 48

        self.sim.confirm_button_hover = (
            btn_trade_x <= mx <= btn_trade_x + btn_trade_w and
            btn_trade_y <= my <= btn_trade_y + btn_trade_h
        )
        if self.sim.confirm_button_hover and m_clicked:
            self.sim.commit_trade(self.sfx)

    def update(self):
        dt = min(get_frame_time(), 0.05)
        self.sim.anim_timer += dt

        if self.sim.toast_timer > 0.0:
            self.sim.toast_timer -= dt

        self.handle_input(dt)

    def draw(self):
        begin_drawing()
        clear_background(COLOR_BG)

        # 1. Top HUD Header Bar
        self.draw_top_bar()

        # 2. Left Panel: Merchant Stall & Roster
        self.draw_merchant_panel()

        # 3. Center Panel: Trade Desk & Transaction Engine
        self.draw_center_trade_desk()

        # 4. Right Panel: Player Satchel & Bag
        self.draw_player_panel()

        # 5. Toast Feedback Banner (Floating confirmation / error)
        if self.sim.toast_timer > 0.0:
            self.draw_toast_notification()

        # 6. Global Dropdowns & Gamepad Badge
        draw_gamepad_status_badge(985, 22, 11)
        draw_ui_settings_bar(450, 16)  # Kept clear of text

        # 7. X-Ray Overlay ([Tab])
        if self.show_xray:
            draw_xray_telemetry_overlay(self.sim)

        end_drawing()

    def draw_top_bar(self):
        draw_rectangle(0, 0, SCREEN_WIDTH, 52, Color(16, 20, 32, 255))
        draw_line(0, 52, SCREEN_WIDTH, 52, COLOR_PANEL_BORDER)

        draw_text("MERCHANT STALL", 25, 14, 20, COLOR_GOLD_COIN)
        draw_text("SHOP BUY/SELL SCREEN & TRANSACTION PIPELINE", 195, 20, 12, COLOR_TEXT_DIM)

        # Mode indicator tags (left of UI settings dropdown bar)
        if self.sim.pipeline.regulated_economy:
            draw_rectangle(25, 34, 180, 14, Color(22, 48, 32, 255))
            draw_text("[F1] ECONOMY: REGULATED (50% MARKDOWN)", 28, 36, 9, COLOR_GREEN_SUCCESS)
        else:
            draw_rectangle(25, 34, 195, 14, Color(58, 22, 22, 255))
            draw_text("[F1] ECONOMY: EXPLOITABLE (100% PARITY)", 28, 36, 9, COLOR_RED_ERROR)

        if self.sim.pipeline.haggle_unlocked:
            draw_rectangle(225, 34, 145, 14, Color(45, 35, 18, 255))
            draw_text("[F2] HAGGLE PERK: ACTIVE (+15%)", 228, 36, 9, COLOR_GOLD_COIN)

    def draw_merchant_panel(self):
        # Panel frame
        draw_rectangle(PANEL_LEFT_X, PANEL_LEFT_Y, PANEL_LEFT_W, PANEL_LEFT_H, COLOR_PANEL_BG)
        draw_rectangle_lines(PANEL_LEFT_X, PANEL_LEFT_Y, PANEL_LEFT_W, PANEL_LEFT_H,
                             COLOR_SLOT_SELECTED if self.sim.active_side == 0 else COLOR_PANEL_BORDER)

        # Awning at top of stall
        draw_merchant_awning(PANEL_LEFT_X, PANEL_LEFT_Y, PANEL_LEFT_W, 38)

        # Merchant Avatar & Speech Bubble Area
        avatar_y = PANEL_LEFT_Y + 76
        draw_rectangle(PANEL_LEFT_X + 12, avatar_y - 28, 80, 78, Color(22, 28, 44, 255))
        draw_rectangle_lines(PANEL_LEFT_X + 12, avatar_y - 28, 80, 78, COLOR_PANEL_BORDER)

        # Procedural 2D Merchant Sprite
        merchant_pos = Vector2(PANEL_LEFT_X + 52, avatar_y + 16)
        draw_humanoid_enemy_2d(
            position=merchant_pos,
            facing_angle_rad=0.0,
            anim_timer=self.sim.anim_timer * 0.5,
            scale=1.1,
            is_attacking=False,
            palette=self.merchant_palette
        )

        # Stall Name & Treasury
        draw_text("Garrick's Goods", PANEL_LEFT_X + 102, avatar_y - 22, 16, COLOR_GOLD_COIN)
        draw_circle(PANEL_LEFT_X + 108, avatar_y + 4, 6, COLOR_GOLD_COIN)
        draw_text(f"Vault: {self.sim.merchant_gold} G", PANEL_LEFT_X + 120, avatar_y - 2, 13, COLOR_TEXT_MAIN)

        # Speech bubble
        draw_rectangle(PANEL_LEFT_X + 102, avatar_y + 16, PANEL_LEFT_W - 114, 34, Color(25, 34, 52, 255))
        draw_rectangle_lines(PANEL_LEFT_X + 102, avatar_y + 16, PANEL_LEFT_W - 114, 34, Color(50, 68, 105, 255))
        draw_text(self.sim.merchant_dialogue, PANEL_LEFT_X + 108, avatar_y + 22, 10, COLOR_TEXT_DIM)

        # Section Divider
        draw_line(PANEL_LEFT_X + 12, PANEL_LEFT_Y + 144, PANEL_LEFT_X + PANEL_LEFT_W - 12, PANEL_LEFT_Y + 144, COLOR_PANEL_BORDER)
        draw_text("MERCHANT STOCK [BUY]", PANEL_LEFT_X + 16, PANEL_LEFT_Y + 152, 13,
                  COLOR_CYAN_ACCENT if self.sim.active_side == 0 else COLOR_TEXT_DIM)
        draw_text("Click / [A] to browse", PANEL_LEFT_X + PANEL_LEFT_W - 130, PANEL_LEFT_Y + 152, 10, COLOR_TEXT_DIM)

        # Scrollable / Paginated stock list
        list_y = PANEL_LEFT_Y + 176
        slot_h = 42
        for i, entry in enumerate(self.sim.merchant_stock):
            item = self.sim.catalog_map.get(entry.item_id)
            if not item:
                continue
            sy = list_y + i * (slot_h + 4)
            is_sel = (self.sim.active_side == 0 and self.sim.selected_item_id == entry.item_id)

            bg_col = COLOR_ITEM_HOVER if is_sel else COLOR_SLOT_EMPTY
            border_col = COLOR_SLOT_SELECTED if is_sel else COLOR_SLOT_BORDER

            draw_rectangle(PANEL_LEFT_X + 10, sy, PANEL_LEFT_W - 20, slot_h, bg_col)
            draw_rectangle_lines(PANEL_LEFT_X + 10, sy, PANEL_LEFT_W - 20, slot_h, border_col)

            # Item Icon
            draw_procedural_item_icon(item.icon_type, PANEL_LEFT_X + 28, sy + slot_h // 2, 26)

            # Name & Category
            draw_text(item.name, PANEL_LEFT_X + 48, sy + 6, 12, COLOR_WHITE if is_sel else COLOR_TEXT_MAIN)
            cat_name = CATEGORY_NAMES[item.category]
            cat_col = CATEGORY_COLORS[item.category]
            draw_text(cat_name, PANEL_LEFT_X + 48, sy + 22, 10, cat_col)

            # Price Tag (Buy Price)
            unit_p = self.sim.pipeline.calculate_unit_price(item.base_price, True)
            can_afford = (self.sim.player_gold >= unit_p)
            price_col = COLOR_GOLD_COIN if can_afford else COLOR_RED_ERROR
            draw_text(f"{unit_p} G", PANEL_LEFT_X + PANEL_LEFT_W - 100, sy + 14, 13, price_col)

            # Stock Count Pill
            stock_col = COLOR_CYAN_ACCENT if entry.quantity > 0 else COLOR_RED_ERROR
            draw_rectangle(PANEL_LEFT_X + PANEL_LEFT_W - 48, sy + 12, 34, 18, Color(22, 30, 48, 255))
            draw_text(f"x{entry.quantity}", PANEL_LEFT_X + PANEL_LEFT_W - 42, sy + 15, 11, stock_col)

    def draw_player_panel(self):
        # Panel frame
        draw_rectangle(PANEL_RIGHT_X, PANEL_RIGHT_Y, PANEL_RIGHT_W, PANEL_RIGHT_H, COLOR_PANEL_BG)
        draw_rectangle_lines(PANEL_RIGHT_X, PANEL_RIGHT_Y, PANEL_RIGHT_W, PANEL_RIGHT_H,
                             COLOR_SLOT_SELECTED if self.sim.active_side == 1 else COLOR_PANEL_BORDER)

        # Header
        draw_rectangle(PANEL_RIGHT_X, PANEL_RIGHT_Y, PANEL_RIGHT_W, 38, COLOR_WOOD_DARK)
        draw_text("ADVENTURER'S SATCHEL", PANEL_RIGHT_X + 16, PANEL_RIGHT_Y + 10, 16, COLOR_GOLD_COIN)

        # Gold Pouch & Bag Capacity
        purse_y = PANEL_RIGHT_Y + 48
        draw_rectangle(PANEL_RIGHT_X + 10, purse_y, PANEL_RIGHT_W - 20, 48, Color(24, 32, 50, 255))
        draw_rectangle_lines(PANEL_RIGHT_X + 10, purse_y, PANEL_RIGHT_W - 20, 48, COLOR_PANEL_BORDER)

        # Gold coin pile icon
        draw_circle(PANEL_RIGHT_X + 28, purse_y + 24, 10, COLOR_GOLD_COIN)
        draw_circle(PANEL_RIGHT_X + 34, purse_y + 20, 8, Color(255, 230, 110, 255))
        draw_text("Player Gold:", PANEL_RIGHT_X + 50, purse_y + 10, 11, COLOR_TEXT_DIM)
        draw_text(f"{self.sim.player_gold} Gold", PANEL_RIGHT_X + 50, purse_y + 24, 16, COLOR_GOLD_COIN)

        # Bag Slots Gauge
        used_slots = len(self.sim.player_stock)
        cap_col = COLOR_GREEN_SUCCESS if used_slots < MAX_PLAYER_CAPACITY else COLOR_RED_ERROR
        draw_text(f"Slots: {used_slots}/{MAX_PLAYER_CAPACITY}", PANEL_RIGHT_X + PANEL_RIGHT_W - 95, purse_y + 10, 11, cap_col)
        # Small progress bar
        bar_w = 75
        draw_rectangle(PANEL_RIGHT_X + PANEL_RIGHT_W - 95, purse_y + 26, bar_w, 8, Color(14, 18, 28, 255))
        fill_w = int((used_slots / MAX_PLAYER_CAPACITY) * bar_w)
        draw_rectangle(PANEL_RIGHT_X + PANEL_RIGHT_W - 95, purse_y + 26, fill_w, 8, cap_col)

        # Section Header
        draw_text("INVENTORY WARES [SELL]", PANEL_RIGHT_X + 16, PANEL_RIGHT_Y + 106, 13,
                  COLOR_GREEN_SUCCESS if self.sim.active_side == 1 else COLOR_TEXT_DIM)
        draw_text("Click / [D] to browse", PANEL_RIGHT_X + PANEL_RIGHT_W - 130, PANEL_RIGHT_Y + 106, 10, COLOR_TEXT_DIM)

        # Inventory Items List
        p_list_y = PANEL_RIGHT_Y + 128
        slot_h = 42
        for i, entry in enumerate(self.sim.player_stock):
            item = self.sim.catalog_map.get(entry.item_id)
            if not item:
                continue
            sy = p_list_y + i * (slot_h + 4)
            is_sel = (self.sim.active_side == 1 and self.sim.selected_item_id == entry.item_id)

            bg_col = COLOR_ITEM_HOVER if is_sel else COLOR_SLOT_EMPTY
            border_col = COLOR_SLOT_SELECTED if is_sel else COLOR_SLOT_BORDER

            draw_rectangle(PANEL_RIGHT_X + 10, sy, PANEL_RIGHT_W - 20, slot_h, bg_col)
            draw_rectangle_lines(PANEL_RIGHT_X + 10, sy, PANEL_RIGHT_W - 20, slot_h, border_col)

            # Item Icon
            draw_procedural_item_icon(item.icon_type, PANEL_RIGHT_X + 28, sy + slot_h // 2, 26)

            # Name & Category
            draw_text(item.name, PANEL_RIGHT_X + 48, sy + 6, 12, COLOR_WHITE if is_sel else COLOR_TEXT_MAIN)
            cat_name = CATEGORY_NAMES[item.category]
            cat_col = CATEGORY_COLORS[item.category]
            draw_text(cat_name, PANEL_RIGHT_X + 48, sy + 22, 10, cat_col)

            # Sell Value Tag
            unit_sell_p = self.sim.pipeline.calculate_unit_price(item.base_price, False)
            draw_text(f"{unit_sell_p} G", PANEL_RIGHT_X + PANEL_RIGHT_W - 100, sy + 14, 13, COLOR_GREEN_SUCCESS)

            # Count Pill
            draw_rectangle(PANEL_RIGHT_X + PANEL_RIGHT_W - 48, sy + 12, 34, 18, Color(22, 30, 48, 255))
            draw_text(f"x{entry.quantity}", PANEL_RIGHT_X + PANEL_RIGHT_W - 42, sy + 15, 11, COLOR_CYAN_ACCENT)

        # Empty Satchel Slots
        for i in range(len(self.sim.player_stock), MAX_PLAYER_CAPACITY):
            sy = p_list_y + i * (slot_h + 4)
            if sy + slot_h < PANEL_RIGHT_Y + PANEL_RIGHT_H - 10:
                draw_rectangle(PANEL_RIGHT_X + 10, sy, PANEL_RIGHT_W - 20, slot_h, Color(14, 18, 28, 120))
                draw_rectangle_lines(PANEL_RIGHT_X + 10, sy, PANEL_RIGHT_W - 20, slot_h, Color(30, 40, 60, 150))
                draw_text("< Empty Satchel Slot >", PANEL_RIGHT_X + 50, sy + 14, 11, Color(75, 95, 125, 200))

    def draw_center_trade_desk(self):
        # Panel frame
        draw_rectangle(PANEL_CENTER_X, PANEL_CENTER_Y, PANEL_CENTER_W, PANEL_CENTER_H, COLOR_PANEL_BG)
        draw_rectangle_lines(PANEL_CENTER_X, PANEL_CENTER_Y, PANEL_CENTER_W, PANEL_CENTER_H, COLOR_PANEL_BORDER)

        # Desk Header
        draw_rectangle(PANEL_CENTER_X, PANEL_CENTER_Y, PANEL_CENTER_W, 38, COLOR_WOOD_DARK)
        is_buy = (self.sim.active_side == 0)
        mode_title = "TRADE EXCHANGE DESK [BUY MODE]" if is_buy else "TRADE EXCHANGE DESK [SELL MODE]"
        title_col = COLOR_CYAN_ACCENT if is_buy else COLOR_GREEN_SUCCESS
        draw_text(mode_title, PANEL_CENTER_X + 20, PANEL_CENTER_Y + 10, 15, title_col)

        item = self.sim.get_selected_item()
        if not item:
            draw_text("Select an item to trade", PANEL_CENTER_X + 120, PANEL_CENTER_Y + 200, 16, COLOR_TEXT_DIM)
            return

        # 1. Selected Item Showcase Frame
        card_y = PANEL_CENTER_Y + 50
        draw_rectangle(PANEL_CENTER_X + 20, card_y, PANEL_CENTER_W - 40, 140, Color(24, 32, 50, 255))
        draw_rectangle_lines(PANEL_CENTER_X + 20, card_y, PANEL_CENTER_W - 40, 140, COLOR_PANEL_BORDER)

        # Big Item Icon
        draw_procedural_item_icon(item.icon_type, PANEL_CENTER_X + 65, card_y + 55, 54)

        # Item Details
        draw_text(item.name, PANEL_CENTER_X + 105, card_y + 16, 17, COLOR_GOLD_COIN)
        cat_name = CATEGORY_NAMES[item.category]
        cat_col = CATEGORY_COLORS[item.category]
        draw_text(f"Category: {cat_name}", PANEL_CENTER_X + 105, card_y + 38, 11, cat_col)
        draw_text(item.lore, PANEL_CENTER_X + 105, card_y + 56, 11, COLOR_TEXT_DIM)

        # Price Breakdown Line
        unit_p = self.sim.pipeline.calculate_unit_price(item.base_price, is_buy)
        mult_str = f"{self.sim.pipeline.get_effective_buy_multiplier():.2f}x" if is_buy else f"{self.sim.pipeline.get_effective_sell_multiplier():.2f}x"
        rate_name = "Buy Markup" if is_buy else "Sell Markdown"
        draw_text(f"Base Value: {item.base_price} G  |  {rate_name}: {mult_str}  ->  Unit Price: {unit_p} G",
                  PANEL_CENTER_X + 30, card_y + 110, 11, COLOR_TEXT_MAIN)

        # 2. Interactive Bulk Quantity Stepper
        step_y = PANEL_CENTER_Y + 205
        draw_rectangle(PANEL_CENTER_X + 20, step_y, PANEL_CENTER_W - 40, 120, Color(20, 26, 42, 255))
        draw_rectangle_lines(PANEL_CENTER_X + 20, step_y, PANEL_CENTER_W - 40, 120, COLOR_PANEL_BORDER)

        draw_text("BULK QUANTITY SELECTOR", PANEL_CENTER_X + 30, step_y + 12, 13, COLOR_CYAN_ACCENT)

        # Stepper Controls
        max_q = self.sim.calculate_max_trade_quantity(is_buy, item)
        btn_y = step_y + 36

        # [-] Button
        draw_rectangle(PANEL_CENTER_X + 45, btn_y, 40, 36, Color(35, 48, 76, 255))
        draw_rectangle_lines(PANEL_CENTER_X + 45, btn_y, 40, 36, COLOR_SLOT_BORDER)
        draw_text("-", PANEL_CENTER_X + 60, btn_y + 8, 20, COLOR_WHITE)

        # Quantity Box
        draw_rectangle(PANEL_CENTER_X + 95, btn_y, PANEL_CENTER_W - 190, 36, Color(14, 18, 28, 255))
        draw_rectangle_lines(PANEL_CENTER_X + 95, btn_y, PANEL_CENTER_W - 190, 36, COLOR_GOLD_COIN)
        q_str = f"{self.sim.trade_quantity}"
        draw_text(q_str, PANEL_CENTER_X + PANEL_CENTER_W // 2 - 10, btn_y + 8, 20, COLOR_GOLD_COIN)

        # [+] Button
        draw_rectangle(PANEL_CENTER_X + PANEL_CENTER_W - 85, btn_y, 40, 36, Color(35, 48, 76, 255))
        draw_rectangle_lines(PANEL_CENTER_X + PANEL_CENTER_W - 85, btn_y, 40, 36, COLOR_SLOT_BORDER)
        draw_text("+", PANEL_CENTER_X + PANEL_CENTER_W - 71, btn_y + 8, 20, COLOR_WHITE)

        # Quick Preset Buttons [1], [5], [MAX]
        quick_y = btn_y + 44
        presets = [("x1", 1), ("x5", 5), ("MAX", max_q)]
        for i, (label, val) in enumerate(presets):
            bx = PANEL_CENTER_X + 70 + i * 105
            is_active = (self.sim.trade_quantity == val and val > 0)
            draw_rectangle(bx, quick_y, 75, 24, Color(45, 60, 92, 255) if is_active else Color(28, 36, 56, 255))
            draw_rectangle_lines(bx, quick_y, 75, 24, COLOR_SLOT_SELECTED if is_active else COLOR_SLOT_BORDER)
            draw_text(label, bx + 22, quick_y + 6, 11, COLOR_WHITE if is_active else COLOR_TEXT_DIM)

        # 3. Live Cost Calculation & Balance Projection
        cost_y = PANEL_CENTER_Y + 338
        draw_rectangle(PANEL_CENTER_X + 20, cost_y, PANEL_CENTER_W - 40, 72, Color(24, 32, 50, 255))
        draw_rectangle_lines(PANEL_CENTER_X + 20, cost_y, PANEL_CENTER_W - 40, 72, COLOR_PANEL_BORDER)

        total_cost = unit_p * self.sim.trade_quantity
        draw_text(f"Formula: {self.sim.trade_quantity} units x {unit_p} G =", PANEL_CENTER_X + 30, cost_y + 12, 13, COLOR_TEXT_DIM)
        draw_text(f"Total: {total_cost} Gold", PANEL_CENTER_X + 245, cost_y + 10, 16, COLOR_GOLD_COIN)

        # Balance impact preview
        if is_buy:
            proj_p_gold = self.sim.player_gold - total_cost
            afford_col = COLOR_GREEN_SUCCESS if proj_p_gold >= 0 else COLOR_RED_ERROR
            draw_text(f"Player Gold: {self.sim.player_gold} -> {proj_p_gold} G", PANEL_CENTER_X + 30, cost_y + 38, 12, afford_col)
            draw_text(f"Merchant Stock: {self.sim.get_merchant_stock_count(item.item_id)} -> {max(0, self.sim.get_merchant_stock_count(item.item_id) - self.sim.trade_quantity)}",
                      PANEL_CENTER_X + 220, cost_y + 38, 12, COLOR_CYAN_ACCENT)
        else:
            proj_p_gold = self.sim.player_gold + total_cost
            draw_text(f"Player Gold: {self.sim.player_gold} -> {proj_p_gold} G", PANEL_CENTER_X + 30, cost_y + 38, 12, COLOR_GREEN_SUCCESS)
            draw_text(f"Merchant Vault: {self.sim.merchant_gold} -> {self.sim.merchant_gold - total_cost} G",
                      PANEL_CENTER_X + 220, cost_y + 38, 12, COLOR_CYAN_ACCENT)

        # 4. Atomic Pre-Condition Validation Box
        val_y = PANEL_CENTER_Y + 420
        avail = self.sim.get_merchant_stock_count(item.item_id) if is_buy else self.sim.get_player_stock_count(item.item_id)
        player_owns = (self.sim.get_player_stock_count(item.item_id) > 0)
        player_slots = len(self.sim.player_stock)

        err = self.sim.pipeline.validate_preconditions(
            is_buy=is_buy,
            item=item,
            quantity=self.sim.trade_quantity,
            player_gold=self.sim.player_gold,
            merchant_gold=self.sim.merchant_gold,
            available_stock=avail,
            player_distinct_item_count=player_slots,
            player_already_owns_item=player_owns
        )

        val_bg = Color(20, 36, 26, 255) if err == ERR_OK else Color(42, 22, 22, 255)
        val_border = COLOR_GREEN_SUCCESS if err == ERR_OK else COLOR_RED_ERROR
        draw_rectangle(PANEL_CENTER_X + 20, val_y, PANEL_CENTER_W - 40, 52, val_bg)
        draw_rectangle_lines(PANEL_CENTER_X + 20, val_y, PANEL_CENTER_W - 40, 52, val_border)

        status_prefix = "[✓] VALIDATION PASSED" if err == ERR_OK else "[✗] TRANSACTION BLOCKED"
        draw_text(status_prefix, PANEL_CENTER_X + 30, val_y + 10, 13, val_border)
        draw_text(ERROR_MESSAGES[err], PANEL_CENTER_X + 30, val_y + 28, 11, COLOR_WHITE)

        # 5. Confirm Trade Button
        btn_trade_y = PANEL_CENTER_Y + 484
        btn_trade_w = PANEL_CENTER_W - 40
        btn_trade_x = PANEL_CENTER_X + 20
        btn_trade_h = 44

        btn_bg = COLOR_SLOT_SELECTED if (self.sim.confirm_button_hover and err == ERR_OK) else (
            Color(40, 85, 55, 255) if err == ERR_OK else Color(45, 45, 55, 255)
        )
        draw_rectangle(btn_trade_x, btn_trade_y, btn_trade_w, btn_trade_h, btn_bg)
        draw_rectangle_lines(btn_trade_x, btn_trade_y, btn_trade_w, btn_trade_h, COLOR_GREEN_SUCCESS if err == ERR_OK else COLOR_SLOT_BORDER)

        btn_text = f"CONFIRM PURCHASE ({total_cost} G)" if is_buy else f"CONFIRM SALE (+{total_cost} G)"
        draw_text(btn_text, btn_trade_x + btn_trade_w // 2 - 100, btn_trade_y + 14, 15, COLOR_WHITE)

        # 6. Mini Audit Trail / Transaction History
        hist_y = PANEL_CENTER_Y + 538
        draw_text("RECENT TRANSACTION AUDIT LOG", PANEL_CENTER_X + 25, hist_y, 11, COLOR_TEXT_DIM)
        for i, audit in enumerate(reversed(self.sim.audit_log[-3:])):
            ay = hist_y + 16 + i * 26
            a_bg = Color(18, 24, 36, 255)
            draw_rectangle(PANEL_CENTER_X + 20, ay, PANEL_CENTER_W - 40, 22, a_bg)
            t_col = COLOR_CYAN_ACCENT if audit.is_buy else COLOR_GREEN_SUCCESS
            t_type = "BOUGHT" if audit.is_buy else "SOLD"
            log_line = f"{t_type} {audit.quantity}x {audit.item_name} for {audit.total_gold} G (Purse: {audit.player_gold_after} G)"
            draw_text(log_line, PANEL_CENTER_X + 26, ay + 5, 10, t_col)

    def draw_toast_notification(self):
        """Displays an animated floating banner for confirmation and alerts."""
        alpha = min(1.0, self.sim.toast_timer * 2.0)
        tw = 480
        th = 40
        tx = (SCREEN_WIDTH - tw) // 2
        ty = SCREEN_HEIGHT - 65

        col_bg = Color(42, 18, 22, int(240 * alpha)) if self.sim.toast_is_error else Color(18, 48, 30, int(240 * alpha))
        col_border = COLOR_RED_ERROR if self.sim.toast_is_error else COLOR_GREEN_SUCCESS

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
    MerchantStallGame().run(smoke_test=is_smoke)
