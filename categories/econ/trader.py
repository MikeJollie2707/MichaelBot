import datetime as dt
import math
import random

from utils import models, psql

__TRADE_WHITELIST = ("money",
    "wood", "stick", "rotten_flesh", "spider_eye", "gunpowder", "pearl",
    "leaf", "hibiscus", "tulip", "rose", "lucky_clover", "gold_apple",
    "stone", "iron", "iron_pickaxe", "iron_sword", "iron_axe", "diamond", "obsidian",
    "overworld_ticket", "nether_ticket", "nether_respawner",
)
__BARTER_WHITELIST = ("gold",
    "wood", "stick", "wood_pickaxe", "rotten_flesh", "spider_eye", "gunpowder", "pearl",
    "stone", "iron", "iron_pickaxe", "iron_sword", "iron_axe", 
    "diamond", "diamond_pickaxe", "diamond_sword", "diamond_axe", "obsidian",
    "overworld_ticket", "nether_ticket", "nether_respawner", "redstone", "dry_leaf", "mushroom", "magma_cream",
    "fire_potion",
)

def generate_trades(item_cache: models.ItemCache, next_reset: dt.datetime, amount: int = 6) -> list[psql.ActiveTrade]:
    '''Generate trades based on pre-determined rules.

    Parameters
    ----------
    item_cache : models.ItemCache
        The bot's item cache. This is to get item's information.
    next_reset : dt.datetime
        When these trades will reset.
    amount : int, optional
        How many trade to generate, by default 6

    Returns
    -------
    list[psql.ActiveTrade]
        A list of trades to be added.
    '''

    trades = []
    # Avoid duplicate trades.
    traded_item = ["money"]
    for i in range(1, amount + 1):
        trade = psql.ActiveTrade(i, "trade", "", 0, "", 0, next_reset, 15)
        max_value_limit = random.randint(1, 300)

        # item -> money
        if i == 1:
            # Limit this, otherwise it'd be a free money maker strat.
            max_value_limit = random.randint(1, 50)
            trade.hard_limit = 5

            trade.item_dest = "money"
            
            trade.item_src = "money"
            while trade.item_src in traded_item:
                trade.item_src = random.choice(__TRADE_WHITELIST)
            traded_item.append(trade.item_src)
            
            # Get the item's value.
            item = item_cache[trade.item_src]
            src_price = item.sell_price

            # Force the current max to be at least the item's price so we can avoid amount = 0.
            max_value_limit = max(max_value_limit, src_price)
            # Get the max amount of item to not exceed the trade's current max value.
            src_max_amount = max_value_limit // src_price
            
            trade.amount_src = random.randint(1, src_max_amount)
            # Overvalue the item.
            trade.amount_dest = math.ceil(trade.amount_src * src_price * (0.85 + random.random()))
        # item -> item
        elif i == amount:
            # Select items so they don't go against each other.
            trade.item_src = "money"
            while trade.item_src in traded_item:
                trade.item_src = random.choice(__TRADE_WHITELIST)
            traded_item.append(trade.item_src)
            
            trade.item_dest = "money"
            while trade.item_dest in traded_item:
                trade.item_dest = random.choice(__TRADE_WHITELIST)
            traded_item.append(trade.item_dest)

            # Limit diamond trade.
            if trade.item_dest == "diamond":
                trade.hard_limit = 5
            if trade.item_dest == "gold_apple":
                trade.hard_limit = 5
            
            # Get the items' values.
            item_src = item_cache[trade.item_src]
            item_dest = item_cache[trade.item_dest]

            src_price = item_src.sell_price
            
            dest_price = item_dest.buy_price
            if not item_dest.buy_price:
                dest_price = item_dest.sell_price
            
            # Lower the limit if these are tools, otherwise you'll end up with super trash trades.
            if psql.Equipment.is_equipment(item_src.id) or psql.Equipment.is_equipment(item_dest.id):
                max_value_limit = 50
            # Force the current max to be at least the item's price so we can avoid amount = 0.
            max_value_limit = max(src_price, dest_price, max_value_limit)
            
            # At this point we can guarantee the trade will have at least 1 on both side, we can safely get amount.
            src_max_amount = max_value_limit // src_price
            dest_max_amount = max_value_limit // dest_price
            
            if src_price > dest_price:
                trade.amount_src = random.randint(1, src_max_amount)
                trade.amount_dest = math.ceil((trade.amount_src * src_price // dest_price) * random.random())
            else:
                trade.amount_dest = random.randint(1, dest_max_amount)
                trade.amount_src = math.ceil((trade.amount_dest * dest_price // src_price) * random.random())
        # money -> item
        else:
            trade.item_src = "money"

            trade.item_dest = "money"
            while trade.item_dest in traded_item:
                trade.item_dest = random.choice(__TRADE_WHITELIST)
            traded_item.append(trade.item_dest)

            # Limit diamond trade.
            if trade.item_dest == "diamond":
                trade.hard_limit = 5
            if trade.item_dest == "gold_apple":
                trade.hard_limit = 5
            
            # Get the item's value.
            item = item_cache[trade.item_dest]
            dest_price = item.buy_price
            if not item.buy_price:
                dest_price = item.sell_price
            
            # Lower the limit if these are tools, otherwise you'll end up with super trash trades.
            if psql.Equipment.is_equipment(item.id):
                max_value_limit = 50
            # Force the current max to be at least the item's price so we can avoid amount = 0.
            max_value_limit = max(max_value_limit, dest_price)
            
            # Get the max amount of item to not exceed the trade's current max value.
            dest_max_amount = max_value_limit // dest_price
            
            trade.amount_dest = random.randint(1, dest_max_amount)
            # Devalue the item, but also have a chance to overvalue the item.
            trade.amount_src = math.ceil(trade.amount_dest * dest_price * (0.65 + random.random()))
        
        trades.append(trade)
    return trades

def generate_barters(item_cache: models.ItemCache, next_reset: dt.datetime, amount: int = 9) -> list[psql.ActiveTrade]:
    '''Generate barters based on pre-determined rules.

    Parameters
    ----------
    item_cache : models.ItemCache
        The bot's item cache. This is to get item's information.
    next_reset : dt.datetime
        When these barters will reset.
    amount : int, optional
        How many barter to generate, by default 9

    Returns
    -------
    list[psql.ActiveTrade]
        A list of barters to be added.
    '''

    barters = []
    # Avoid duplicate barters.
    bartered_items = ["gold"]
    for i in range(1, amount + 1):
        barter = psql.ActiveTrade(i, "barter", "", 0, "", 0, next_reset, 20)
        max_value_limit = random.randint(1, 600)

        if i == 1:
            max_value_limit = random.randint(1, 25)
            barter.hard_limit = 5

            barter.item_dest = "gold"
            barter.item_src = "gold"
            while barter.item_src in bartered_items:
                barter.item_src = random.choice(__BARTER_WHITELIST)
            bartered_items.append(barter.item_src)
        else:
            barter.item_src = "gold"
            barter.item_dest = "gold"
            while barter.item_dest in bartered_items:
                barter.item_dest = random.choice(__BARTER_WHITELIST)
            bartered_items.append(barter.item_dest)
            
        # Get the items' values.
        item_src = item_cache[barter.item_src]
        item_dest = item_cache[barter.item_dest]

        src_price = item_src.sell_price
        
        dest_price = item_dest.buy_price
        if not item_dest.buy_price:
            dest_price = item_dest.sell_price
        
        # Avoid too overpower barter.
        if psql.Equipment.is_equipment(barter.item_src) or psql.Equipment.is_equipment(barter.item_dest):
            max_value_limit = 100
            barter.hard_limit = 5
        # Force the current max to be at least the item's price so we can avoid amount = 0.
        max_value_limit = max(src_price, dest_price, max_value_limit)
        
        # At this point we can guarantee the trade will have at least 1 on both side, we can safely get amount.
        src_max_amount = max_value_limit // src_price
        dest_max_amount = max_value_limit // dest_price
        
        if src_price > dest_price:
            barter.amount_src = random.randint(1, src_max_amount)
            barter.amount_dest = math.ceil((barter.amount_src * src_price // dest_price) * random.random())
        else:
            barter.amount_dest = random.randint(1, dest_max_amount)
            barter.amount_src = math.ceil((barter.amount_dest * dest_price // src_price) * random.random())
        
        barters.append(barter)
    return barters
