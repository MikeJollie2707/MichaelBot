import asyncio
import datetime as dt
import random
from enum import IntFlag, auto
from textwrap import dedent

import hikari
import humanize
import lightbulb
import miru
from lightbulb.ext import tasks

from categories.econ import loot, trader
from utils import checks, converters, helpers, models, nav, psql

CURRENCY_ICON = "<:emerald:993835688137072670>"
TRADE_REFRESH = 3600 * 4

class PotionActivation(IntFlag):
    '''A bit class that stores whether a potion is activated. This saves some memory.'''
    FIRE_POTION = auto()
    HASTE_POTION = auto()
    FORTUNE_POTION = auto()
    STRENGTH_POTION = auto()
    LOOTING_POTION = auto()
    NATURE_POTION = auto()
    LUCK_POTION = auto()
    UNDYING_POTION = auto()

    def has_flag(self, flags, *, any_flag: bool = False) -> bool:
        if any_flag:
            return bool(self & flags)
        return self & flags == flags

def get_final_damage(raw_damage: int, reductions: int) -> int:
    # Check sudden death
    if random.random() <= loot.SUDDEN_DEATH_CHANCE:
        return 9999999999
    
    dmg = max(2, raw_damage - reductions)
    return random.randint(int(dmg / 2) - 1, dmg)

def get_reward_str(bot: models.MichaelBot, loot_table: dict[str, int], *, option: str = "text") -> str:
    '''Return a reward string for a given item dictionary.

    Parameters
    ----------
    bot : models.MichaelBot
        The bot instance.
    loot_table : dict[str, int]
        A `dict` with `{'item_id': amount}`.
    option : str, optional
        The option to display. Available options are `text`, `emote`, or `full`.

    Returns
    -------
    str
        A reward string.
    '''

    if option not in ("text", "emote", "full"):
        raise ValueError("'option' must be either 'text', 'emote', or 'full'.")

    rewards: list[str] = []
    money: int = 0
    for item_id, amount in loot_table.items():
        if amount > 0:
            if item_id in ("money", "bonus"):
                money += amount
            else:
                item = bot.item_cache.get(item_id)
                if item is not None:
                    if option == "emote":
                        rewards.append(f"{item.emoji} x {amount}")
                    elif option == "text":
                        rewards.append(f"{amount}x *{item.name}*")
                    else:
                        rewards.append(f"{amount}x {item.emoji} *{item.name}*")
    if money > 0:
        rewards.insert(0, f"{CURRENCY_ICON}{money}")
    return ', '.join(rewards)

def get_reward_value(loot_table: dict[str, int], item_cache: models.ItemCache) -> int:
    '''Get the value of a loot table.

    Parameters
    ----------
    loot_table : dict[str, int]
        The loot table.
    item_cache : models.ItemCache
        The item cache.

    Returns
    -------
    int
        The value of the loot table.
    '''

    value: int = 0
    for item_id, amount in loot_table.items():
        if item_id in loot.RESERVED_KEYS:
            if item_id in ("money", "bonus"):
                value += amount
            elif item_id == "cost":
                value -= amount
            continue
        
        item = item_cache[item_id]
        value += item.sell_price * amount
    
    return value

def multiply_reward(loot_table: dict[str, int], multiplier: int | float):
    '''A shortcut to multiply the rewards in-place.
    This will not multiply rewards that are defined in `loot.PREVENT_MULTIPLY`.

    Parameters
    ----------
    loot_table : dict[str, int]
        The loot table.
    multiplier : int | float
        The multiplier. Cannot be 0. If this is a float, the result will be rounded normally.
    '''

    if multiplier == 0:
        raise ValueError("'multiplier' cannot be 0.")

    for key in loot_table:
        if key not in loot.PREVENT_MULTIPLY:
            loot_table[key] = round(loot_table[key] * multiplier)

def filter_equipment_types(equipments: list[psql.Equipment], eq_types_or_ids: tuple[str]) -> tuple[psql.Equipment | None]:
    '''Filter equipments based on their types (like for tools) or their ids (like for potions).

    Warnings
    --------
    This is intended to work for equipments that belongs to only one user.

    Parameters
    ----------
    equipments : list[psql.Equipment]
        A list of equipment to filter.
    eq_types_or_ids : tuple[str]
        A tuple of the equipment's type or id.

    Returns
    -------
    tuple[psql.Equipment | None]
        The resultant equipment or `None` if none was found. The order of these equipments (including `None`) matches the order of `eq_types_or_ids`.
    '''

    results = []
    for eq_type_or_id in eq_types_or_ids:
        is_break = False
        for equipment in equipments:
            if equipment.eq_type == eq_type_or_id or equipment.item_id == eq_type_or_id:
                results.append(equipment)
                is_break = True
                break
        
        if not is_break:
            results.append(None)
    return tuple(results)

async def add_reward_to_user(conn, bot: models.MichaelBot, user_id: int, loot_table: dict[str, int]):
    '''A shortcut to add rewards to the user.

    For some special keys (as defined in `loot.RESERVED_KEYS`), this will attempt to add money also.

    This also attempt to add some badges.

    Notes
    -----
    This function internally calls `UserCache.update()`.

    Parameters
    ----------
    conn : asyncpg.Connection
        The connection to use.
    bot : models.MichaelBot
        The bot instance.
    user_id : int
        The user's id.
    loot_table : dict[str, int]
        The loot to add. This will be left untouched after the call, so you can check for reserved keys for custom messages.
    '''

    money: int = 0
    async with conn.transaction():
        for item_id, amount in loot_table.items():
            if item_id not in loot.RESERVED_KEYS:
                if amount > 0:
                    await psql.Inventory.add(conn, user_id, item_id, amount)

                    # Process badge.
                    if item_id == "wood":
                        await psql.UserBadge.add_progress(conn, user_id, "wood0", amount)
                    elif item_id == "iron":
                        await psql.UserBadge.add_progress(conn, user_id, "iron0", amount)
                    elif item_id == "diamond":
                        await psql.UserBadge.add_progress(conn, user_id, "diamond0", amount)
                    elif item_id == "debris":
                        await psql.UserBadge.add_progress(conn, user_id, "debris0", amount)
                    elif item_id == "blaze_rod":
                        await psql.UserBadge.add_progress(conn, user_id, "blaze0", amount)
            elif item_id == "cost":
                money -= amount
            else:
                money += amount
        
        user = bot.user_cache[user_id]
        user.balance += money
        await bot.user_cache.update(conn, user)

async def process_death(conn, bot: models.MichaelBot, user: psql.User):
    '''A shortcut to process a user's death.

    This includes wiping all their equipped tools, applying penalties to inventories and money,
    and move them to the Overworld.

    This also attempt the following badges: `death0`, `death1`, `death2`, `death3`.

    Notes
    -----
    This function internally calls `UserCache.update()`.

    Parameters
    ----------
    conn : asyncpg.Connection
        The connection to use.
    bot : models.MichaelBot
        The bot instance.
    user : psql.User
        The user to process.
    '''

    equipments: list[psql.Equipment] = await psql.Equipment.fetch_user_equipments(conn, user.id)
    inventories: list[psql.Inventory] = await psql.Inventory.get_user_inventory(conn, user.id)
    back_to_overworld = True
    
    async with conn.transaction():
        await psql.UserBadge.add_progress(conn, user.id, "death0")
        await psql.UserBadge.add_progress(conn, user.id, "death1")
        await psql.UserBadge.add_progress(conn, user.id, "death2")
        await psql.UserBadge.add_progress(conn, user.id, "death3")

        death2_badge = await psql.UserBadge.fetch_one(conn, user_id = user.id, badge_id = "death2")

        for equipment in equipments:
            item = bot.item_cache[equipment.item_id]
            if item.rarity.lower() == "legendary":
                continue
            if "nether_" in equipment.item_id and user.world == "nether":
                continue

            await psql.Equipment.delete(conn, user_id = user.id, item_id = equipment.item_id)
        
        strict_penalty = False # Round up or down, default to down.
        death_penalty = 0.05
        if user.world == "end":
            death_penalty = 0.95
            strict_penalty = True
        if death2_badge.completed():
            death_penalty *= 0.5
        
        for inv in inventories:
            if inv.item_id in loot.NON_REMOVABLE_ON_DEATH:
                continue
            
            if user.world == "nether" and inv.item_id == "nether_respawner":
                inv.amount -= 1
                back_to_overworld = False
            else:
                if not strict_penalty:
                    inv.amount -= int(inv.amount * death_penalty)
                else:
                    # Round up.
                    inv.amount -= int(inv.amount * death_penalty) + 1
                
                inv.amount = max(0, inv.amount)
                
            await psql.Inventory.update(conn, inv)
        
        user.balance -= user.balance * 20 // 100
        if back_to_overworld:
            user.world = "overworld"
        user.health = 100
        
        await bot.user_cache.update(conn, user)

async def item_autocomplete(option: hikari.AutocompleteInteractionOption, interaction: hikari.AutocompleteInteraction):
    bot: models.MichaelBot = interaction.app

    def match_algorithm(name: str, input_value: str):
        return name.lower().startswith(input_value.lower())

    items = []
    for item in bot.item_cache.values():
        items.append(item.name)
    
    if option.value == '':
        return items[:25]
    return [match_equipment for match_equipment in items if match_algorithm(match_equipment, option.value)][:25]

async def equipment_autocomplete(option: hikari.AutocompleteInteractionOption, interaction: hikari.AutocompleteInteraction):
    bot: models.MichaelBot = interaction.app

    def match_algorithm(name: str, input_value: str):
        return name.lower().startswith(input_value.lower())

    equipments = []
    for item in bot.item_cache.values():
        if psql.Equipment.is_true_equipment(item.id):
            equipments.append(item.name)
    
    if option.value == '':
        return equipments[:25]
    return [match_equipment for match_equipment in equipments if match_algorithm(match_equipment, option.value)][:25]

async def potion_autocomplete(option: hikari.AutocompleteInteractionOption, interaction: hikari.AutocompleteInteraction):
    bot: models.MichaelBot = interaction.app

    def match_algorithm(name: str, input_value: str):
        return name.lower().startswith(input_value.lower())

    potions = []
    for item in bot.item_cache.values():
        if psql.Equipment.is_potion(item.id):
            potions.append(item.name)
    
    if option.value == '':
        return potions[:25]
    return [match_potion for match_potion in potions if match_algorithm(match_potion, option.value)][:25]

async def food_autocomplete(option: hikari.AutocompleteInteractionOption, interaction: hikari.AutocompleteInteraction):
    bot: models.MichaelBot = interaction.app

    def match_algorithm(name: str, input_value: str):
        return name.lower().startswith(input_value.lower())
    
    foods = []
    for item in bot.item_cache.values():
        if item.id in loot.FOOD_HEALING:
            foods.append(item.name)
        
    if option.value == '':
        return foods[:25]
    return [match_food for match_food in foods if match_algorithm(match_food, option.value)][:25]

async def craftable_autocomplete(option: hikari.AutocompleteInteractionOption, interaction: hikari.AutocompleteInteraction):
    bot: models.MichaelBot = interaction.app

    def match_algorithm(name: str, input_value: str):
        return name.lower().startswith(input_value.lower())

    valid_match = []
    for item in bot.item_cache.values():
        if loot.get_craft_recipe(item.id):
            valid_match.append(item.name)
    
    if option.value == '':
        return valid_match[:25]
    return [valid_item for valid_item in valid_match if match_algorithm(valid_item, option.value)][:25]

async def brewable_autocomplete(option: hikari.AutocompleteInteractionOption, interaction: hikari.AutocompleteInteraction):
    bot: models.MichaelBot = interaction.app

    def match_algorithm(name: str, input_value: str):
        return name.lower().startswith(input_value.lower())

    valid_match = []
    for item in bot.item_cache.values():
        if loot.get_brew_recipe(item.id) and psql.Equipment.is_potion(item.id):
            valid_match.append(item.name)
    
    if option.value == '':
        return valid_match[:25]
    return [valid_item for valid_item in valid_match if match_algorithm(valid_item, option.value)][:25]

plugin = lightbulb.Plugin("Economy", "Economic Commands", include_datastore = True)
plugin.d.emote = helpers.get_emote(":dollar:")
plugin.add_checks(
    checks.is_db_connected, 
    checks.is_command_enabled, 
    checks.strict_concurrency, 
    lightbulb.bot_has_guild_permissions(*helpers.COMMAND_STANDARD_PERMISSIONS)
)

@plugin.command()
@lightbulb.command("badges", f"[{plugin.name}] View your badges.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def badges(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    async with bot.pool.acquire() as conn:
        ubadges = await psql.UserBadge.fetch_user_badges(conn, ctx.author.id)
        if not ubadges:
            await ctx.respond("*Cricket noises*", reply = True)
            return
        
        badges = await psql.Badge.fetch_all(conn)
        available_badges: list[psql.Badge] = []
        for badge in badges:
            for ubadge in ubadges:
                if ubadge.badge_id == badge.id and (ubadge.completed() or ubadge.badge_progress / badge.requirement >= 0.90):
                    available_badges.append(badge)
                    break
        page = nav.ItemListBuilder(available_badges, 6)
        @page.set_page_start_formatter
        def start_format(_: int, __: psql.UserBadge) -> hikari.Embed:
            return helpers.get_default_embed(
                datetime = dt.datetime.now().astimezone(),
                author = ctx.author
            ).set_author(
                name = f"{ctx.author.username}'s Badges",
                icon = ctx.author.avatar_url
            ).set_thumbnail(
                ctx.author.avatar_url
            )
        @page.set_entry_formatter
        def entry_format(embed: hikari.Embed, _: int, badge: psql.Badge):
            _ubadge = None
            for ubadge in ubadges:
                if ubadge.badge_id == badge.id:
                    _ubadge = ubadge
                    break
            
            embed_name = f"{badge.emoji} {badge.name}"
            if not _ubadge.completed():
                embed_name += f" [{_ubadge.badge_progress}/{badge.requirement}]"
            
            embed.add_field(
                name = embed_name,
                value = f"*{badge.description}*"
            )
        
        await nav.run_view(page.build(authors = (ctx.author.id,)), ctx)

@plugin.command()
@lightbulb.command("balance", f"[{plugin.name}] View your balance.", aliases = ["bal"])
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def balance(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    async with bot.pool.acquire() as conn:
        user = await psql.User.fetch_one(conn, id = ctx.author.id)
        await ctx.respond(f"You have {CURRENCY_ICON}{user.balance}.")

@plugin.command()
@lightbulb.option("money", "The amount to bet. You'll either lose this or get 2x back. At least 1.", type = int, default = 1, min_value = 1)
@lightbulb.option("number", "Your guessing number. Stay within 0-50!", type = int, min_value = 0, max_value = 50)
@lightbulb.command("bet", f"[{plugin.name}] Bet your money to guess a number in the range 0-50.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def bet(ctx: lightbulb.Context):
    number: int = ctx.options.number
    money: int = ctx.options.money
    bot: models.MichaelBot = ctx.bot

    if number < 0 or number > 50:
        number = random.randint(0, 50)
    
    if money < 1:
        money = 1
    
    user = bot.user_cache[ctx.author.id]
    if user.balance < money:
        await ctx.respond(f"You don't have enough money to bet {CURRENCY_ICON}{money}!", reply = True, mentions_reply = True)
        return
    if user.balance == money:
        confirm_menu = nav.ConfirmView(timeout = 10, authors = (ctx.author.id, ))
        resp = await ctx.respond("You're betting all your money right now, are you sure about this?", reply = True, components = confirm_menu.build())
        await confirm_menu.start(await resp)
        res = await confirm_menu.wait()
        if not res:
            if res is None:
                await ctx.respond("Confirmation timed out. I'll take it as a \"No\".", reply = True, mentions_reply = True)
            else:
                await ctx.respond("Aight stay safe!", reply = True, mentions_reply = True)
            return
    
    # No this is not a register.
    rsp: str = f"You placed your bet of {CURRENCY_ICON}{money} and guessed `{number}`...\n"
    actual_num = random.randint(0, 50)
    # Refetch user info for up-to-date info.
    user = bot.user_cache[ctx.author.id]
    if actual_num == number:
        rsp += f"And it is correct! You receive your money back and another {CURRENCY_ICON}{money}!\n"
        user.balance += money
    else:
        rsp += f"And it is incorrect! The number is `{actual_num}`. Better luck next time!\n"
        user.balance -= money

    async with bot.pool.acquire() as conn:    
        await bot.user_cache.update(conn, user)
        
    rsp += f"Your balance now: {CURRENCY_ICON}{user.balance}."
    await ctx.respond(rsp, reply = True)

@plugin.command()
@lightbulb.add_checks(checks.is_dev)
@lightbulb.option("amount", "Amount to add.", type = int, min_value = 1, default = 1)
@lightbulb.option("item", "The item to add.", type = converters.ItemConverter)
@lightbulb.command("additem", f"[{plugin.name}] Add item.")
@lightbulb.implements(lightbulb.PrefixCommand)
async def additem(ctx: lightbulb.Context):
    item = ctx.options.item
    bot: models.MichaelBot = ctx.bot
    
    if isinstance(ctx, lightbulb.SlashContext):
        item = await converters.ItemConverter(ctx).convert(item)

    async with bot.pool.acquire() as conn:
        await psql.Inventory.add(conn, ctx.author.id, item.id, ctx.options.amount)
    await ctx.respond("Added.")

@plugin.command()
@lightbulb.add_checks(checks.is_dev)
@lightbulb.option("amount", "Amount to add.", type = int, min_value = 1, max_value = 500)
@lightbulb.command("addmoney", f"[{plugin.name}] Add money.")
@lightbulb.implements(lightbulb.PrefixCommand)
async def addmoney(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    async with bot.pool.acquire() as conn:
        user = bot.user_cache[ctx.author.id]
        user.balance += min(500, max(1, ctx.options.amount))
        await bot.user_cache.update(conn, user)
    await ctx.respond(f"Added {CURRENCY_ICON}{ctx.options.amount}.")

@plugin.command()
@lightbulb.set_help(dedent('''
    - It is recommended to use the `Slash Command` version of this command.
'''))
@lightbulb.add_cooldown(length = 1, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.option("times", "How many times this command is executed. Default to 1.", type = int, min_value = 1, max_value = 100, default = 1)
@lightbulb.option("potion", "the name or alias of the potion to brew.", type = converters.ItemConverter, autocomplete = brewable_autocomplete)
@lightbulb.command("brew", f"[{plugin.name}] Brew various potions.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def brew(ctx: lightbulb.Context):
    potion: psql.Item = ctx.options.potion
    times: int = max(1, min(100, ctx.options.times))
    bot: models.MichaelBot = ctx.bot

    if isinstance(ctx, lightbulb.SlashContext):
        potion = await converters.ItemConverter(ctx).convert(potion)
    
    if potion is None:
        await bot.reset_cooldown(ctx)
        await ctx.respond("This potion doesn't exist!", reply = True, mentions_reply = True)
        return
    
    if not psql.Equipment.is_potion(potion.id):
        await bot.reset_cooldown(ctx)
        await ctx.respond("This ain't a potion.", reply = True, mentions_reply = True)
        return
    
    recipe = loot.get_brew_recipe(potion.id)
    if not recipe:
        await bot.reset_cooldown(ctx)
        await ctx.respond(f"Potion *{potion.name}* cannot be brewed.", reply = True, mentions_reply = True)
        return
    
    if times > 1:
        multiply_reward(recipe, times)
    
    user = bot.user_cache[ctx.author.id]
    if recipe.get("cost") is not None and recipe["cost"] > user.balance:
        await bot.reset_cooldown(ctx)
        await ctx.respond("You don't have enough money to brew this potion.", reply = True, mentions_reply = True)
        return
    
    if recipe.get("cost") is not None:
        user.balance -= recipe.pop("cost")
    
    async with bot.pool.acquire() as conn:
        # Try removing the items; if any falls below 0, it fails to craft.
        success: bool = True
        missing: dict[str, int] = {}
        # Only retrieve relevant items.
        inventories = await psql.Inventory.fetch_all_where(conn, where = lambda r: r.item_id in recipe and r.user_id == ctx.author.id)

        # Loop through inventories and reduce amount and track how many items missing.
        # In case inv is missing a few items or all items, then missing won't have that key, and will be checked in a separate loop.

        for inv in inventories:
            inv.amount -= recipe[inv.item_id]
            if inv.amount < 0:
                missing[inv.item_id] = -inv.amount
                success = False
            else:
                # Make sure this key is available; not available means the user don't have this item at all.
                missing[inv.item_id] = 0

        # Check if missing has all the keys in the recipe (except result).
        for item_id in recipe:
            if item_id == "result": continue

            if item_id not in missing:
                missing[item_id] = recipe[item_id]
                success = False
        
        if not success:
            await bot.reset_cooldown(ctx)
            await ctx.respond(f"You're missing the following items: {get_reward_str(bot, missing)}")
            return
        
        # Check for badges.
        brew1_badge = await psql.UserBadge.fetch_one(conn, user_id = ctx.author.id, badge_id = "brew1")
        if brew1_badge and brew1_badge.completed():
            recipe["result"] += 1 * times
        brew2_badge = await psql.UserBadge.fetch_one(conn, user_id = ctx.author.id, badge_id = "brew2")
        if brew2_badge and brew2_badge.completed():
            recipe["result"] += 2 * times
        
        async with conn.transaction():
            for inv in inventories:
                await psql.Inventory.update(conn, inv)
            # Update balance.
            await bot.user_cache.update(conn, user)
            await add_reward_to_user(conn, bot, ctx.author.id, {potion.id: recipe["result"]})

            await psql.UserBadge.add_progress(conn, ctx.author.id, "brew0", recipe["result"])
            await psql.UserBadge.add_progress(conn, ctx.author.id, "brew1", recipe["result"])
            await psql.UserBadge.add_progress(conn, ctx.author.id, "brew2", recipe["result"])
            await psql.UserBadge.add_progress(conn, ctx.author.id, "brew3", recipe["result"])
    await ctx.respond(f"Successfully brewed {get_reward_str(bot, {potion.id: recipe['result']})}.", reply = True)

@plugin.command()
@lightbulb.set_help(dedent('''
    - It is recommended to use the `Slash Command` version of this command.
'''))
@lightbulb.add_cooldown(length = 1, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.option("times", "How many times this command is executed. Default to 1.", type = int, min_value = 1, max_value = 100, default = 1)
@lightbulb.option("item", "The name or alias of the item to craft.", type = converters.ItemConverter, autocomplete = craftable_autocomplete)
@lightbulb.command("craft", f"[{plugin.name}] Craft various items.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def craft(ctx: lightbulb.Context):
    item: psql.Item = ctx.options.item
    times: int = max(1, min(100, ctx.options.times))
    bot: models.MichaelBot = ctx.bot

    if isinstance(ctx, lightbulb.SlashContext):
        item = await converters.ItemConverter(ctx).convert(item)
    
    if item is None:
        await bot.reset_cooldown(ctx)
        await ctx.respond("This item doesn't exist!", reply = True, mentions_reply = True)
        return
    
    recipe = loot.get_craft_recipe(item.id)
    if not recipe:
        await bot.reset_cooldown(ctx)
        await ctx.respond(f"Item *{item.name}* cannot be crafted.", reply = True, mentions_reply = True)
        return
    
    # Emulate executing the command multiple times.
    if times > 1:
        multiply_reward(recipe, times)

    async with bot.pool.acquire() as conn:
        # Try removing the items; if any falls below 0, it fails to craft.
        success: bool = True
        missing: dict[str, int] = {}
        # Only retrieve relevant items.
        inventories = await psql.Inventory.fetch_all_where(conn, where = lambda r: r.item_id in recipe and r.user_id == ctx.author.id)

        # Loop through inventories and reduce amount and track how many items missing.
        # In case inv is missing a few items or all items, then missing won't have that key, and will be checked in a separate loop.

        for inv in inventories:
            inv.amount -= recipe[inv.item_id]
            if inv.amount < 0:
                missing[inv.item_id] = -inv.amount
                success = False
            else:
                # Make sure this key is available; not available means the user don't have this item at all.
                missing[inv.item_id] = 0

        # Check if missing has all the keys in the recipe (except result).
        for item_id in recipe:
            if item_id == "result": continue

            if item_id not in missing:
                missing[item_id] = recipe[item_id]
                success = False

        if not success:
            await bot.reset_cooldown(ctx)
            await ctx.respond(f"You're missing the following items: {get_reward_str(bot, missing)}")
            return
        
        async with conn.transaction():
            for inv in inventories:
                await psql.Inventory.update(conn, inv)
            await add_reward_to_user(conn, bot, ctx.author.id, {item.id: recipe["result"]})
    await ctx.respond(f"Successfully crafted {get_reward_str(bot, {item.id: recipe['result']})}.", reply = True)

@plugin.command()
@lightbulb.set_help(dedent('''
    - There is a hard cooldown of 24 hours before you can collect the next daily.
    - The higher the daily streak, the better your reward will be.
    - If you don't collect your daily within 48 hours since the last time you collect, your streak will be reset to 1.
'''))
@lightbulb.command("daily", f"[{plugin.name}] Receive rewards everyday. Don't miss it though!")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def daily(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    response: str = ""
    async with bot.pool.acquire() as conn:
        user = bot.user_cache.get(ctx.author.id)
        
        # User should be guaranteed to be created via checks.is_command_enabled() check.
        assert user is not None

        now = dt.datetime.now().astimezone()
        has_streak_freeze = await psql.Inventory.fetch_one(conn, user_id = ctx.author.id, item_id = "streak_freezer")
        async with conn.transaction():
            if user.last_daily is None:
                response += "Yooo first time collecting daily, welcome!\n"
                user.daily_streak = 0
            elif now - user.last_daily < dt.timedelta(days = 1):
                remaining_time = dt.timedelta(days = 1) + user.last_daily - now
                raise lightbulb.CommandIsOnCooldown(retry_after = remaining_time.seconds)
            # A user need to collect the daily before the second day.
            elif now - user.last_daily >= dt.timedelta(days = 2):
                # No watch.
                if not has_streak_freeze:
                    response += f"Oops, your old streak of `{user.daily_streak}x` got obliterated. Wake up early next time :)\n"
                    user.daily_streak = 0
                else:
                    streak_freeze_item = bot.item_cache["streak_freezer"]
                    # Store previous freeze amount.
                    streak_freeze_amount = has_streak_freeze.amount
                    
                    days_differences = now - user.last_daily - dt.timedelta(days = 2)
                    has_streak_freeze.amount -= days_differences.days + 1
                    
                    if has_streak_freeze.amount < 0:
                        response += f"Oops, despite popping {streak_freeze_amount}x *{streak_freeze_item.name}*, " +\
                                    f"your old streak of `{user.daily_streak}` can't be saved. Wake up early next time :)\n"
                        user.daily_streak = 0
                    else:
                        timer_used = streak_freeze_amount - has_streak_freeze.amount
                        response += f"You popped {timer_used}x *{streak_freeze_item.name}* to save your streak. Watch out next time.\n"
                    
                    await psql.Inventory.remove(conn, ctx.author.id, "streak_freezer", streak_freeze_amount - has_streak_freeze.amount)
            
            user.daily_streak += 1
            response += f"You gained a new streak! Your streak now: `{user.daily_streak}x`\n"
            
            # We're risking race data for slight performance here.
            user.last_daily = now
            bot.user_cache.update_local(user)

            daily_loot = loot.get_daily_loot(user.daily_streak)
            if user.daily_streak % 10 == 0:
                daily_loot["streak_freezer"] = 1
            await add_reward_to_user(conn, bot, ctx.author.id, daily_loot)
            response += f"You received: {get_reward_str(bot, daily_loot, option = 'emote')}\n"

        await ctx.respond(response, reply = True)

@plugin.command()
@lightbulb.set_help(dedent('''
    - This command only works with subcommands.
'''))
@lightbulb.command("use", f"[{plugin.name}] Use a tool or a potion.")
@lightbulb.implements(lightbulb.PrefixCommandGroup, lightbulb.SlashCommandGroup)
async def use(ctx: lightbulb.Context):
    raise lightbulb.CommandNotFound(invoked_with = ctx.invoked_with)

@use.child
@lightbulb.add_cooldown(length = 5, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.option("equipment", "The equipment's name or alias to use.", type = converters.ItemConverter, autocomplete = equipment_autocomplete)
@lightbulb.command("tool", f"[{plugin.name}] Use a tool. Get to work!")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def use_tool(ctx: lightbulb.Context):
    item: psql.Item = ctx.options.equipment
    bot: models.MichaelBot = ctx.bot

    if isinstance(ctx, lightbulb.SlashContext):
        item = await converters.ItemConverter(ctx).convert(item)

    if not item:
        await bot.reset_cooldown(ctx)
        await ctx.respond("This equipment doesn't exist!", reply = True, mentions_reply = True)
        return
    if not psql.Equipment.is_true_equipment(item.id):
        await bot.reset_cooldown(ctx)
        await ctx.respond("This is not an equipment!", reply = True, mentions_reply = True)
        return
    
    async with bot.pool.acquire() as conn:
        inv = await psql.Inventory.fetch_one(conn, user_id = ctx.author.id, item_id = item.id)
        if not inv:
            await bot.reset_cooldown(ctx)
            await ctx.respond("You don't have this equipment in your inventory!", reply = True, mentions_reply = True)
            return
        
        # Check for equipment type conflict.
        existed: psql.Equipment = await psql.Equipment.fetch_equipment(conn, user_id = ctx.author.id, eq_type = psql.Equipment.get_equipment_type(item.id))
        response_str = ""

        if existed:
            # Refund if possible.
            existed_item = bot.item_cache.get(existed.item_id)
            response_str += f"You unequipped *{existed_item.name}* "
            async with conn.transaction():
                craftable = loot.get_craft_recipe(existed.item_id)
                if not craftable:
                    response_str += "and it disappeared like magic.\n"
                else:
                    # Refund x%
                    refund_rate = existed.remain_durability / existed_item.durability
                    for item_id in craftable:
                        if item_id == "result": continue

                        # craftable["result"] should be 1, but just in case it's not 1, we divide it to get the value of each individual tool's value.
                        craftable[item_id] = int(craftable[item_id] / craftable["result"] * refund_rate)
                    
                    # Clean the dict to prevent any dumb side-effect.
                    del craftable["result"]
                    await add_reward_to_user(conn, bot, ctx.author.id, craftable)

                    reward_str = get_reward_str(bot, craftable, option = "emote")
                    if not reward_str:
                        response_str += "and got back nothing.\n"
                    else:
                        response_str += f"and got back the following items: {reward_str}\n"
                
                await psql.Equipment.delete(conn, user_id = ctx.author.id, item_id = existed.item_id)
                await psql.Equipment.transfer_from_inventory(conn, inv)
        else:
            await psql.Equipment.transfer_from_inventory(conn, inv)
        response_str += f"Equipped {item.emoji} *{item.name}*."
        
        await ctx.respond(response_str, reply = True)

@use.child
@lightbulb.set_help(dedent('''
    - It is recommended to use the `Slash Command` version of this command.
'''))
@lightbulb.add_cooldown(length = 5, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.option("potion", "The potion's name or alias to use.", type = converters.ItemConverter, autocomplete = potion_autocomplete)
@lightbulb.command("potion", f"[{plugin.name}] Use a potion.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def use_potion(ctx: lightbulb.Context):
    potion: psql.Item = ctx.options.potion
    bot: models.MichaelBot = ctx.bot

    if isinstance(ctx, lightbulb.SlashContext):
        potion = await converters.ItemConverter(ctx).convert(potion)

    if not potion:
        await bot.reset_cooldown(ctx)
        await ctx.respond("This potion doesn't exist!", reply = True, mentions_reply = True)
        return
    if not psql.Equipment.is_potion(potion.id):
        await bot.reset_cooldown(ctx)
        await ctx.respond("This is not a potion!", reply = True, mentions_reply = True)
        return
    
    async with bot.pool.acquire() as conn:
        inv = await psql.Inventory.fetch_one(conn, user_id = ctx.author.id, item_id = potion.id)
        if not inv:
            await bot.reset_cooldown(ctx)
            await ctx.respond("You don't have this potion in your inventory!", reply = True, mentions_reply = True)
            return

        potions = await psql.Equipment.fetch_user_potions(conn, ctx.author.id)
        
        potions_cap = loot.POTIONS_CAP
        if (brew3_badge := await psql.UserBadge.fetch_one(conn, user_id = ctx.author.id, badge_id = "brew3")) and brew3_badge.completed():
            potions_cap += 1
        if await psql.Equipment.fetch_one(conn, user_id = ctx.author.id, item_id = "undying_potion"):
            potions_cap += 1
        
        if len(potions) >= potions_cap:
            await bot.reset_cooldown(ctx)
            await ctx.respond(f"You currently have {len(potions)} potions equipped. You'll need to wait for one of them to expire before using another.", reply = True, mentions_reply = True)
            return
        
        existed = await psql.Equipment.fetch_one(conn, user_id = ctx.author.id, item_id = potion.id)
        if existed:
            await bot.reset_cooldown(ctx)
            await ctx.respond("You're already using this potion.", reply = True, mentions_reply = True)
            return
        
        await psql.Equipment.transfer_from_inventory(conn, inv)
        
    await ctx.respond(f"Equipped {potion.emoji} *{potion.name}*", reply = True)

@use.child
@lightbulb.set_help(dedent('''
    - It is recommended to use the `Slash Command` version of this command.
'''))
@lightbulb.add_cooldown(length = 120, uses = 10, bucket = lightbulb.UserBucket, algorithm = lightbulb.SlidingWindowCooldownAlgorithm)
@lightbulb.option("food", "The food's name or alias to use.", type = converters.ItemConverter, autocomplete = food_autocomplete)
@lightbulb.command("food", f"[{plugin.name}] Use a food item.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def use_food(ctx: lightbulb.Context):
    food: psql.Item = ctx.options.food
    bot: models.MichaelBot = ctx.bot

    if isinstance(ctx, lightbulb.SlashContext):
        food = await converters.ItemConverter(ctx).convert(ctx.options.food)
    
    if not food:
        await bot.reset_cooldown(ctx)
        await ctx.respond("This food doesn't exist!", reply = True, mentions_reply = True)
        return
    
    if food.id not in loot.FOOD_HEALING.keys():
        await bot.reset_cooldown(ctx)
        await ctx.respond("This is not an edible item. Don't try eating unedible things. They're not good for stomach.", reply = True, mentions_reply = True)
        return
    
    heal_amount: int = 0
    async with bot.pool.acquire() as conn:
        inv = await psql.Inventory.fetch_one(conn, user_id = ctx.author.id, item_id = food.id)
        if not inv:
            await bot.reset_cooldown(ctx)
            await ctx.respond("You don't have this item in your inventory!", reply = True, mentions_reply = True)
            return
        
        user = bot.user_cache[ctx.author.id]
        if user.health >= 100:
            await bot.reset_cooldown(ctx)
            await ctx.respond("You're already at max health. No need to heal.", reply = True, mentions_reply = True)
            return
        
        heal_amount = random.randint(int(loot.FOOD_HEALING[food.id] / 2), loot.FOOD_HEALING[food.id])
        if (eat1_badge := await psql.UserBadge.fetch_one(conn, user_id = ctx.author.id, badge_id = "eat1")) and eat1_badge.completed():
            heal_amount += 5
            
            if (eat2_badge := await psql.UserBadge.fetch_one(conn, user_id = ctx.author.id, badge_id = "eat2")) and eat2_badge.completed():
                heal_amount = round(heal_amount * 1.2)
        
        # No need to cap health here. Only stop using food when health is already >= 100.
        user.health = user.health + heal_amount

        await psql.UserBadge.add_progress(conn, ctx.author.id, "eat0")
        await psql.UserBadge.add_progress(conn, ctx.author.id, "eat1")
        await psql.UserBadge.add_progress(conn, ctx.author.id, "eat2")
        await bot.user_cache.update(conn, user)
    
    await ctx.respond(f"You consumed *1x {food.emoji} {food.name}* and healed {heal_amount}HP.", reply = True)

@plugin.command()
@lightbulb.add_cooldown(length = 10, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.command("equipments", f"[{plugin.name}] View your current equipments.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def _equipments(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    embed = helpers.get_default_embed(
        author = ctx.author,
        timestamp = dt.datetime.now().astimezone()
    ).set_author(
        name = f"{ctx.author.username}'s Equipments",
        icon = ctx.author.avatar_url
    )

    embed.add_field(
        name = "HP:",
        value = f"{bot.user_cache[ctx.author.id].health}"
    )

    async with bot.pool.acquire() as conn:
        equipments = await psql.Equipment.fetch_user_equipments(conn, ctx.author.id)
        if not equipments:
            embed.description = "*Cricket noises*"
        else:
            def _equipment_order(e: psql.Equipment):
                if e.eq_type == "_sword": return 0
                if e.eq_type == "_pickaxe": return 1
                if e.eq_type == "_axe": return 2
                return bot.item_cache[e.item_id].sort_id
            
            equipments.sort(key = _equipment_order)
            for equipment in equipments:
                item_form = bot.item_cache[equipment.item_id]
                embed.add_field(
                    name = f"{item_form.emoji} {item_form.name} [{equipment.remain_durability}/{item_form.durability}]",
                    value = f"*{item_form.description}*"
                )
            embed.set_thumbnail(ctx.author.avatar_url)
    
    await ctx.respond(embed = embed, reply = True)

@plugin.command()
@lightbulb.add_cooldown(length = 10, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.option("view_option", "Options to view inventory.", choices = ("compact", "full", "value"), default = "compact")
@lightbulb.command("inventory", f"[{plugin.name}] View your inventory.", aliases = ["inv"])
@lightbulb.implements(lightbulb.PrefixCommandGroup, lightbulb.SlashCommandGroup)
async def inventory(ctx: lightbulb.Context):
    raise lightbulb.CommandNotFound(invoked_with = ctx.invoked_with)
@inventory.child
@lightbulb.add_cooldown(length = 5, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.option("view_options", "Options to view inventory.", choices = ("compact", "full", "safe", "value"), default = "compact")
@lightbulb.command("view", f"[{plugin.name}] View your inventory.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def inv_view(ctx: lightbulb.Context):
    view_option = ctx.options.view_options
    bot: models.MichaelBot = ctx.bot
    
    async with bot.pool.acquire() as conn:
        if view_option == "compact":
            inventories = await psql.Inventory.get_user_inventory(conn, ctx.author.id)
            if not inventories:
                await ctx.respond("*Cricket noises*", reply = True)
                return
            
            inv_dict: dict[str, int] = {}
            for inv in inventories:
                inv_dict[inv.item_id] = inv.amount
            await ctx.respond(f"**{ctx.author.username}'s Inventory**\n{get_reward_str(bot, inv_dict, option = 'emote')}", reply = True)
        elif view_option == "full":
            inventories = await psql.Inventory.get_user_inventory(conn, ctx.author.id)
            if not inventories:
                await ctx.respond("*Cricket noises*", reply = True)
                return
            
            page = nav.ItemListBuilder(inventories, 5)
            @page.set_page_start_formatter
            def start_format(_index: int, _inv: psql.Inventory) -> hikari.Embed:
                return helpers.get_default_embed(
                    title = f"**{ctx.author.username}'s Inventory**",
                    description = "",
                    timestamp = dt.datetime.now().astimezone()
                ).set_author(
                    name = ctx.author.username,
                    icon = ctx.author.avatar_url
                ).set_thumbnail(
                    ctx.author.avatar_url
                )
            @page.set_entry_formatter
            def entry_format(embed: hikari.Embed, _index: int, inv: psql.Inventory):
                item = bot.item_cache[inv.item_id]
                embed.add_field(
                    name = f"{inv.amount}x {item.emoji} {item.name}",
                    value = f"*{item.description}*\nTotal value: {CURRENCY_ICON}{item.sell_price * inv.amount}"
                )
            
            await nav.run_view(page.build(authors = (ctx.author.id,)), ctx)
        elif view_option == "value":
            inventories = await psql.Inventory.get_user_inventory(conn, ctx.author.id)
            value = 0
            for inv in inventories:
                item = bot.item_cache[inv.item_id]
                value += item.sell_price * inv.amount
            await ctx.respond(f"If you sell all your items in your inventory, you'll get: {CURRENCY_ICON}{value}.", reply = True)
        elif view_option == "safe":
            # Basically just compact + shulker_inventories
            inventories = await psql.ExtraInventory.get_user_inventory(conn, ctx.author.id)
            if not inventories:
                await ctx.respond("*Cricket noises*", reply = True)
                return
            
            inv_dict: dict[str, int] = {}
            for inv in inventories:
                inv_dict[inv.item_id] = inv.amount
            await ctx.respond(f"**{ctx.author.username}'s Inventory (Safe)**\n{get_reward_str(bot, inv_dict, option = 'emote')}", reply = True)

@inventory.child
@lightbulb.add_cooldown(length = 10, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.option("amount", "The amount to transfer. By default, all will be transferred.", 
    type = int, 
    min_value = 1,
    default = loot.MAX_SAFE_CAPACITY_BASE,
)
@lightbulb.option("item", "An item in your inventory.", autocomplete = item_autocomplete)
@lightbulb.command("save", f"[{plugin.name}] Transfer an item from your inventory to a safe spot.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def inv_save(ctx: lightbulb.Context):
    item: psql.Item = ctx.options.item
    amount: int = min(max(ctx.options.amount, 1), loot.MAX_SAFE_CAPACITY_BASE)
    bot: models.MichaelBot = ctx.bot

    if isinstance(ctx, lightbulb.SlashContext):
        item = await converters.ItemConverter(ctx).convert(item)
    
    if not item:
        await ctx.respond("This is not an item!", reply = True, mentions_reply = True)
        return
    
    if item.id == "shulker_box":
        await ctx.respond("You can't add this item!", reply = True, mentions_reply = True)
        return

    async with bot.pool.acquire() as conn:
        shulker_inv = await psql.Inventory.fetch_one(conn, user_id = ctx.author.id, item_id = "shulker_box")
        if not shulker_inv:
            await ctx.respond("You don't have a shulker box! Shulker box is needed in order to safely store items.", reply = True, mentions_reply = True)
            return
        
        slots_count = min(shulker_inv.amount, loot.MAX_SHULKER_EFFECT)
        max_item_per_slot = loot.MAX_SAFE_CAPACITY_BASE
        # Extra shulker boxes will increase the capacity cap per slot.
        if shulker_inv.amount > loot.MAX_SHULKER_EFFECT:
            max_item_per_slot += loot.SAFE_CAPACITY_PER_EXTRA_SHULKER * (shulker_inv.amount - loot.MAX_SHULKER_EFFECT)
        
        item_inv = await psql.Inventory.fetch_one(conn, user_id = ctx.author.id, item_id = item.id)
        if not item_inv:
            await ctx.respond("You don't have this item in your inventory!", reply = True, mentions_reply = True)
            return
        
        amount = min(item_inv.amount, amount)

        safe_inventories = await psql.ExtraInventory.get_user_inventory(conn, ctx.author.id)
        _t = tuple(filter(lambda inv: inv.item_id == item.id, safe_inventories))
        if len(_t) >= 1:
            safe_inv = _t[0]
            if safe_inv.amount >= max_item_per_slot:
                await ctx.respond(f"You already have {max_item_per_slot} of this item saved. You can't put more than that!", 
                    reply = True, mentions_reply = True, flags = hikari.MessageFlag.EPHEMERAL)
                return
            
            amount = min(amount, max_item_per_slot - safe_inv.amount)
        elif len(safe_inventories) >= slots_count:
            await ctx.respond(f"You already have {slots_count} unique items saved. You can't put more than that!",
                reply = True, mentions_reply = True, flags = hikari.MessageFlag.EPHEMERAL)
            return
        async with conn.transaction():
            await psql.ExtraInventory.add(conn, ctx.author.id, item.id, amount)
            await psql.Inventory.remove(conn, ctx.author.id, item.id, amount)
    await ctx.respond(f"Moved {get_reward_str(bot, {item.id: amount})} to the safe inventory.", reply = True)

@inventory.child
@lightbulb.add_cooldown(length = 10, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.option("amount", "The amount to transfer. By default, only 1 will be transferred.", 
    type = int,
    min_value = 1, 
    default = 1,
)
@lightbulb.option("item", "An item in your extra inventory.", autocomplete = item_autocomplete)
@lightbulb.command("unsave", f"[{plugin.name}] Transfer an item from the safe spot back to the main inventory.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def inv_unsave(ctx: lightbulb.Context):
    item: psql.Item = ctx.options.item
    amount: int = max(ctx.options.amount, 1)
    bot: models.MichaelBot = ctx.bot

    if isinstance(ctx, lightbulb.SlashContext):
        item = await converters.ItemConverter(ctx).convert(item)
    
    if not item:
        await ctx.respond("This is not an item!", reply = True, mentions_reply = True)
        return

    async with bot.pool.acquire() as conn:
        safe_inv = await psql.ExtraInventory.fetch_one(conn, user_id = ctx.author.id, item_id = item.id)
        if not safe_inv:
            await ctx.respond("You don't have this item in your safe inventory!", reply = True, mentions_reply = True)
            return
        
        amount = min(safe_inv.amount, amount)
        async with conn.transaction():
            await psql.ExtraInventory.remove(conn, ctx.author.id, item.id, amount)
            await psql.Inventory.add(conn, ctx.author.id, item.id, amount)
    await ctx.respond(f"Moved {get_reward_str(bot, {item.id: amount})} to the main inventory.", reply = True)

@plugin.command()
@lightbulb.command("market", f"[{plugin.name}] View public purchases.")
@lightbulb.implements(lightbulb.PrefixCommandGroup, lightbulb.SlashCommandGroup)
async def market(ctx: lightbulb.Context):
    await market_view(ctx)

@market.child
@lightbulb.command("view", f"[{plugin.name}] View public purchases.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def market_view(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    items = bot.item_cache.values()
    builder = nav.ItemListBuilder(items, 5)
    @builder.set_page_start_formatter
    def start_format(index: int, item: psql.Item):
        embed = helpers.get_default_embed(
            title = "Market",
            timestamp = dt.datetime.now().astimezone()
        ).set_author(
            name = bot.get_me().username,
            icon = bot.get_me().avatar_url
        ).set_thumbnail(
            bot.get_me().avatar_url
        )
        return embed
    @builder.set_entry_formatter
    def entry_format(embed: hikari.Embed, index: int, item: psql.Item):
        embed.add_field(
            name = f"{item.emoji} {item.name}",
            value = dedent(f'''
                *{item.description}*
                Buy: {f"{CURRENCY_ICON}{item.buy_price}" if item.buy_price else "N/A"}
                Sell: {CURRENCY_ICON}{item.sell_price}
            ''')
        )
    
    await nav.run_view(builder.build(authors = (ctx.author.id, )), ctx)

@market.child
@lightbulb.option("amount", "The amount to purchase. Default to 1.", type = int, min_value = 1, default = 1)
@lightbulb.option("item", "The item to purchase.", type = converters.ItemConverter, autocomplete = item_autocomplete)
@lightbulb.command("buy", f"[{plugin.name}] Buy an item from the market.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def market_buy(ctx: lightbulb.Context):
    item: psql.Item = ctx.options.item
    amount: int = ctx.options.amount
    bot: models.MichaelBot = ctx.bot

    if isinstance(ctx, lightbulb.SlashContext):
        item = await converters.ItemConverter(ctx).convert(item)
    
    if amount < 1:
        await ctx.respond("You'll need to buy at least one item!", reply = True, mentions_reply = True)
        return
    
    if item is None:
        await ctx.respond("This is not a valid item.", reply = True, mentions_reply = True)
        return
    
    if not item.buy_price:
        await ctx.respond("This item cannot be purchased from the market.", reply = True, mentions_reply = True)
        return
    
    cost = item.buy_price * amount
    user = bot.user_cache[ctx.author.id]
    if user.balance < cost:
        await ctx.respond(f"You don't have enough money to buy this many. Total cost: {CURRENCY_ICON}{cost}", reply = True, mentions_reply = True)
        return
    
    user.balance -= cost

    async with bot.pool.acquire() as conn:
        async with conn.transaction():
            await add_reward_to_user(conn, bot, ctx.author.id, {item.id: amount})
            await bot.user_cache.update(conn, user)
    
    await ctx.respond(f"Successfully purchased {get_reward_str(bot, {item.id : amount}, option = 'emote')}.", reply = True)

@market.child
@lightbulb.option("amount", "The amount to sell, or 0 to sell all. Default to 1.", type = int, min_value = 0, default = 1)
@lightbulb.option("item", "The item to sell.", type = converters.ItemConverter, autocomplete = item_autocomplete)
@lightbulb.command("sell", f"[{plugin.name}] Sell items from your inventory.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def market_sell(ctx: lightbulb.Context):
    item: psql.Item = ctx.options.item
    amount: int = ctx.options.amount
    bot: models.MichaelBot = ctx.bot

    if isinstance(ctx, lightbulb.SlashContext):
        item = await converters.ItemConverter(ctx).convert(item)
    
    if amount < 0:
        await ctx.respond("You'll need to sell at least one item!", reply = True, mentions_reply = True)
        return
    
    if item is None:
        await ctx.respond("This is not a valid item.", reply = True, mentions_reply = True)
        return
    
    if not item.sell_price:
        await ctx.respond("This item cannot be sold to the market.", reply = True, mentions_reply = True)
        return

    async with bot.pool.acquire() as conn:
        inv = await psql.Inventory.fetch_one(conn, user_id = ctx.author.id, item_id = item.id)
        if not inv or inv.amount < amount:
            await ctx.respond("You don't have enough of this item to sell.", reply = True, mentions_reply = True)
            return
        
        if amount == 0:
            amount = inv.amount
        
        if item.id == "wood":
            wood1_badge = await psql.UserBadge.fetch_one(conn, user_id = ctx.author.id, badge_id = "wood1")
            if wood1_badge and wood1_badge.completed():
                item.sell_price += 1
        elif item.id == "iron":
            iron1_badge = await psql.UserBadge.fetch_one(conn, user_id = ctx.author.id, badge_id = "iron1")
            if iron1_badge and iron1_badge.completed():
                item.sell_price += 2
        
        profit = item.sell_price * amount
        user = bot.user_cache[ctx.author.id]
        user.balance += profit

        async with conn.transaction():
            await psql.Inventory.remove(conn, ctx.author.id, item.id, amount)
            await bot.user_cache.update(conn, user)
    
    await ctx.respond(f"Successfully sold {get_reward_str(bot, {item.id : amount}, option = 'emote')} for {CURRENCY_ICON}{profit}.", reply = True)

@plugin.command()
@lightbulb.add_cooldown(length = 120, uses = 4, bucket = lightbulb.UserBucket, algorithm = lightbulb.SlidingWindowCooldownAlgorithm)
@lightbulb.option("location", "The location to mine. The deeper you go, the higher the reward and risk.", choices = loot.MINE_LOCATION, modifier = helpers.CONSUME_REST_OPTION)
@lightbulb.command("mine", f"[{plugin.name}] Use your pickaxe to mine for resources.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def mine(ctx: lightbulb.Context):
    location: str = ctx.options.location
    bot: models.MichaelBot = ctx.bot

    user = bot.user_cache[ctx.author.id]
    if location not in loot.WORLD_LOCATION[user.world]:
        await bot.reset_cooldown(ctx)
        await ctx.respond(f"This location is not available in the {user.world.capitalize()}!",
            reply = True, mentions_reply = True)
        return

    potion_activated = PotionActivation(0)
    external_buffs = []
    response_str = ""

    async with bot.pool.acquire() as conn:
        equipments = await psql.Equipment.fetch_user_equipments(conn, ctx.author.id)
        relevant_equipments = filter_equipment_types(equipments, (
            "_pickaxe", 
            "luck_potion", 
            "fire_potion", 
            "undying_potion", 
            "haste_potion", 
            "fortune_potion",
        ))

        pickaxe_existed = relevant_equipments[0]
        if not pickaxe_existed:
            await bot.reset_cooldown(ctx)
            await ctx.respond("You don't have a pickaxe!", reply = True, mentions_reply = True)
            return
        
        if pickaxe_existed.item_id == "bed_pickaxe" and user.world == "overworld":
            await bot.reset_cooldown(ctx)
            await ctx.respond("This pickaxe doesn't work in the Overworld!", reply = True, mentions_reply = True)
            return
        
        dmg_reductions = loot.DMG_REDUCTIONS.get(pickaxe_existed.item_id, 0)
        
        # Check external buffs for lowering death rate.
        has_luck_potion = relevant_equipments[1]
        has_fire_potion = relevant_equipments[2]
        has_undead_potion = relevant_equipments[3]
        has_haste_potion = relevant_equipments[4]
        has_fortune_potion = relevant_equipments[5]
        # Also roll the potion if they exist, you lose all of them anw if you dies so.
        # After this, has_flag(potion_activated, PotionActivatetion.X_POTION) == True guarantees x_potion exists.
        if has_luck_potion:
            dmg_reductions += loot.DMG_REDUCTIONS["luck_potion"]
            if loot.roll_potion_activate("luck_potion"):
                potion_activated |= PotionActivation.LUCK_POTION
                external_buffs.append("luck_potion")
        if has_fire_potion:
            dmg_reductions += loot.DMG_REDUCTIONS["fire_potion"]
            if loot.roll_potion_activate("fire_potion"):
                potion_activated |= PotionActivation.FIRE_POTION
        if has_undead_potion:
            dmg_reductions += loot.DMG_REDUCTIONS["undying_potion"]
            if loot.roll_potion_activate("undying_potion"):
                potion_activated |= PotionActivation.UNDYING_POTION
        if has_haste_potion:
            dmg_reductions += loot.DMG_REDUCTIONS["haste_potion"]
            if loot.roll_potion_activate("haste_potion"):
                potion_activated |= PotionActivation.HASTE_POTION
                external_buffs.append("haste_potion")
        if has_fortune_potion:
            dmg_reductions += loot.DMG_REDUCTIONS["fortune_potion"]
            if loot.roll_potion_activate("fortune_potion"):
                potion_activated |= PotionActivation.FORTUNE_POTION
                external_buffs.append("fortune_potion")
        
        # Check for badges.
        if (death1_badge := await psql.UserBadge.fetch_one(conn, user_id = ctx.author.id, badge_id = "death1")) and death1_badge.completed():
            dmg_reductions += loot.DMG_REDUCTIONS["death1"] * len(equipments)
        if (death3_badge := await psql.UserBadge.fetch_one(conn, user_id = ctx.author.id, badge_id = "death3")) and death3_badge.completed():
            dmg_reductions += loot.DMG_REDUCTIONS["death3"] * len(equipments)
        if (iron2_badge := await psql.UserBadge.fetch_one(conn, user_id = ctx.author.id, badge_id = "iron2")) and iron2_badge.completed():
            external_buffs.append("iron2")
        if (diamond1_badge := await psql.UserBadge.fetch_one(conn, user_id = ctx.author.id, badge_id = "diamond1")) and diamond1_badge.completed():
            external_buffs.append("diamond1")
        if (debris1_badge := await psql.UserBadge.fetch_one(conn, user_id = ctx.author.id, badge_id = "debris1")) and debris1_badge.completed():
            external_buffs.append("debris1")
        
        loot_table = loot.get_activity_loot("mine", pickaxe_existed.item_id, location, external_buffs)

        dmg_taken = get_final_damage(loot_table["raw_damage"], dmg_reductions)
        if dmg_taken > 1000:
            response_str += random.choice(loot.SUDDEN_DEATH_MESSAGES) if user.world != "end" else "You fell into the Void.\n"
        elif dmg_taken > 0:
            response_str += f"You took a damage of {dmg_taken}.\n"

        if user.health - dmg_taken <= 0:
            if not (user.world == "nether" and potion_activated.has_flag(PotionActivation.FIRE_POTION) or
                    potion_activated.has_flag(PotionActivation.UNDYING_POTION)):
                await process_death(conn, bot, user)
                response_str += "You died. Your health is 0 or below. You respawned, but you lost all your equipments, some items and money.\n"
                await ctx.respond(response_str, reply = True, mentions_reply = True)
                return
            
            if user.world == "nether" and potion_activated.has_flag(PotionActivation.FIRE_POTION | PotionActivation.UNDYING_POTION):
                potion_activated ^= PotionActivation.UNDYING_POTION
        else:
            if not (dmg_taken > 60 and potion_activated.has_flag(PotionActivation.UNDYING_POTION)):
                user.health -= dmg_taken
                
                # Disable death-preventing potions if the user is not dead in the first place.
                potion_activated &= ~(PotionActivation.FIRE_POTION | PotionActivation.UNDYING_POTION)
            else:
                # Undying Potion activated and negated the damage, so we don't need to do anything.
                pass
        
        async with conn.transaction():
            await add_reward_to_user(conn, bot, ctx.author.id, loot_table)
            await psql.Equipment.update_durability(conn, ctx.author.id, pickaxe_existed.item_id, pickaxe_existed.remain_durability - 1)
            # Update health.
            await bot.user_cache.update(conn, user)

            # Process potions.
            if potion_activated.has_flag(PotionActivation.FIRE_POTION):
                await psql.Equipment.update_durability(conn, ctx.author.id, "fire_potion", has_fire_potion.remain_durability - 1)
                response_str += "*Fire Potion* activated, saving you from death!\n"
                if has_fire_potion.remain_durability - 1 == 0:
                    response_str += "*Fire Potion* expired!\n"
            if potion_activated.has_flag(PotionActivation.UNDYING_POTION):
                await psql.Equipment.update_durability(conn, ctx.author.id, "undying_potion", has_undead_potion.remain_durability - 1)
                response_str += "*Undying Potion* activated, negating the most recent damage!\n"
                if has_undead_potion.remain_durability - 1 == 0:
                    response_str += "*Undying Potion* expired!\n"
            
            # Because we do take damage even if there's no drop, we need to check if the drop is empty before decreasing the potions that affect drops.
            empty_table = True
            for item, amount in loot_table.items():
                if not item == "raw_damage" and amount != 0:
                    empty_table = False
                    break
            
            if empty_table:
                response_str += "After a long exploring session, you came back with only dust and regret."
                await ctx.respond(response_str, reply = True, mentions_reply = True)
                return

            if potion_activated.has_flag(PotionActivation.LUCK_POTION):
                await psql.Equipment.update_durability(conn, ctx.author.id, "luck_potion", has_luck_potion.remain_durability - 1)
                response_str += "*Luck Potion* activated, giving you more rare drops!\n"
                if has_luck_potion.remain_durability - 1 == 0:
                    response_str += "*Luck Potion* expired!\n"
            if potion_activated.has_flag(PotionActivation.HASTE_POTION):
                await psql.Equipment.update_durability(conn, ctx.author.id, "haste_potion", has_haste_potion.remain_durability - 1)
                response_str += "*Haste Potion* activated, giving you a reward boost!\n"
                if has_haste_potion.remain_durability - 1 == 0:
                    response_str += "*Haste Potion* expired!\n"
            if potion_activated.has_flag(PotionActivation.FORTUNE_POTION):
                await psql.Equipment.update_durability(conn, ctx.author.id, "fortune_potion", has_fortune_potion.remain_durability - 1)
                response_str += "*Fortune Potion* activated, giving you a reward boost!\n"
                if has_fortune_potion.remain_durability - 1 == 0:
                    response_str += "*Fortune Potion* expired!\n"
            
            # Process badges.
            if loot_table.get("iron"):
                await psql.UserBadge.add_progress(conn, ctx.author.id, "iron1", loot_table["iron"])
                await psql.UserBadge.add_progress(conn, ctx.author.id, "iron2", loot_table["iron"])
            if loot_table.get("diamond"):
                await psql.UserBadge.add_progress(conn, ctx.author.id, "diamond1", loot_table["diamond"])
                await psql.UserBadge.add_progress(conn, ctx.author.id, "diamond2", loot_table["diamond"])
            if loot_table.get("debris"):
                await psql.UserBadge.add_progress(conn, ctx.author.id, "debris1", loot_table["debris"])
                await psql.UserBadge.add_progress(conn, ctx.author.id, "debris2", loot_table["debris"])
    
    response_str += f"You mined and received {get_reward_str(bot, loot_table, option = 'emote')}\n"
    if pickaxe_existed.remain_durability - 1 == 0:
        pickaxe_item = bot.item_cache[pickaxe_existed.item_id]
        response_str += f"Your {pickaxe_item.emoji} *{pickaxe_item.name}* broke after the last mining session!"
    
    await ctx.respond(response_str, reply = True)

@plugin.command()
@lightbulb.add_cooldown(length = 120, uses = 4, bucket = lightbulb.UserBucket, algorithm = lightbulb.SlidingWindowCooldownAlgorithm)
@lightbulb.option("location", "The location to explore. The deeper you go, the higher the reward and risk.", choices = loot.EXPLORE_LOCATION, modifier = helpers.CONSUME_REST_OPTION)
@lightbulb.command("explore", f"[{plugin.name}] Use your sword to explore the caverns.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def explore(ctx: lightbulb.Context):
    location: str = ctx.options.location
    bot: models.MichaelBot = ctx.bot

    user = bot.user_cache[ctx.author.id]
    if location not in loot.WORLD_LOCATION[user.world]:
        await bot.reset_cooldown(ctx)
        await ctx.respond(f"This location is not available in the {user.world.capitalize()}!",
            reply = True, mentions_reply = True)
        return

    potion_activated = PotionActivation(0)
    external_buffs = []
    response_str = ""

    async with bot.pool.acquire() as conn:
        equipments = await psql.Equipment.fetch_user_equipments(conn, ctx.author.id)
        relevant_equipments = filter_equipment_types(equipments, (
            "_sword",
            "luck_potion",
            "fire_potion",
            "undying_potion",
            "strength_potion",
            "looting_potion",
        ))
        
        sword_existed = relevant_equipments[0]
        if not sword_existed:
            await bot.reset_cooldown(ctx)
            await ctx.respond("You don't have a sword!", reply = True, mentions_reply = True)
            return

        dmg_reductions = loot.DMG_REDUCTIONS.get(sword_existed.item_id, 0)
        
        # Check external buffs for lowering death rate.
        has_luck_potion = relevant_equipments[1]
        has_fire_potion = relevant_equipments[2]
        has_undead_potion = relevant_equipments[3]
        has_strength_potion = relevant_equipments[4]
        has_looting_potion = relevant_equipments[5]
        # Also roll the potion if they exist, you lose all of them anw if you dies so.
        # After this, has_flag(potion_activated, PotionActivatetion.X_POTION) == True guarantees x_potion exists.
        if has_luck_potion:
            dmg_reductions += loot.DMG_REDUCTIONS["luck_potion"]
            if loot.roll_potion_activate("luck_potion"):
                potion_activated |= PotionActivation.LUCK_POTION
                external_buffs.append("luck_potion")
        if has_fire_potion:
            dmg_reductions += loot.DMG_REDUCTIONS["fire_potion"]
            if loot.roll_potion_activate("fire_potion"):
                potion_activated |= PotionActivation.FIRE_POTION
        if has_undead_potion:
            dmg_reductions += loot.DMG_REDUCTIONS["undying_potion"]
            if loot.roll_potion_activate("undying_potion"):
                potion_activated |= PotionActivation.UNDYING_POTION
        if has_strength_potion:
            dmg_reductions += loot.DMG_REDUCTIONS["strength_potion"]
            if loot.roll_potion_activate("strength_potion"):
                potion_activated |= PotionActivation.STRENGTH_POTION
                external_buffs.append("strength_potion")
        if has_looting_potion:
            dmg_reductions += loot.DMG_REDUCTIONS["looting_potion"]
            if loot.roll_potion_activate("looting_potion"):
                potion_activated |= PotionActivation.LOOTING_POTION
                external_buffs.append("looting_potion")
        
        # Check for badges.
        if (death1_badge := await psql.UserBadge.fetch_one(conn, user_id = ctx.author.id, badge_id = "death1")) and death1_badge.completed():
            dmg_reductions += loot.DMG_REDUCTIONS["death1"] * len(equipments)
        if (death3_badge := await psql.UserBadge.fetch_one(conn, user_id = ctx.author.id, badge_id = "death3")) and death3_badge.completed():
            dmg_reductions += loot.DMG_REDUCTIONS["death3"] * len(equipments)
        if (blaze1_badge := await psql.UserBadge.fetch_one(conn, user_id = ctx.author.id, badge_id = "blaze1")) and blaze1_badge.completed():
            external_buffs.append("blaze1")
        
        loot_table = loot.get_activity_loot("explore", sword_existed.item_id, location, external_buffs)
        dmg_taken = get_final_damage(loot_table["raw_damage"], dmg_reductions)
        if dmg_taken > 1000:
            response_str += random.choice(loot.SUDDEN_DEATH_MESSAGES) if user.world != "end" else "You fell into the Void.\n"
        elif dmg_taken > 0:
            response_str += f"You took a damage of {dmg_taken}.\n"

        if user.health - dmg_taken <= 0:
            if not (user.world == "nether" and potion_activated.has_flag(PotionActivation.FIRE_POTION) or
                    potion_activated.has_flag(PotionActivation.UNDYING_POTION)):
                await process_death(conn, bot, user)
                response_str += "You died. Your health is 0 or below. You respawned, but you lost all your equipments, some items and money.\n"
                await ctx.respond(response_str, reply = True, mentions_reply = True)
                return
            
            if user.world == "nether" and potion_activated.has_flag(PotionActivation.FIRE_POTION | PotionActivation.UNDYING_POTION):
                potion_activated ^= PotionActivation.UNDYING_POTION
        else:
            if not (dmg_taken > 60 and potion_activated.has_flag(PotionActivation.UNDYING_POTION)):
                user.health -= dmg_taken
                
                # Disable death-preventing potions if the user is not dead in the first place.
                potion_activated &= ~(PotionActivation.FIRE_POTION | PotionActivation.UNDYING_POTION)
            else:
                # Undying Potion activated and negated the damage, so we don't need to do anything.
                pass
        
        async with conn.transaction():
            await add_reward_to_user(conn, bot, ctx.author.id, loot_table)
            await psql.Equipment.update_durability(conn, ctx.author.id, sword_existed.item_id, sword_existed.remain_durability - 1)
            # Update health.
            await bot.user_cache.update(conn, user)
            
            # Process potions.
            if potion_activated.has_flag(PotionActivation.FIRE_POTION):
                await psql.Equipment.update_durability(conn, ctx.author.id, "fire_potion", has_fire_potion.remain_durability - 1)
                response_str += "*Fire Potion* activated, saving you from death!\n"
                if has_fire_potion.remain_durability - 1 == 0:
                    response_str += "*Fire Potion* expired!\n"
            if potion_activated.has_flag(PotionActivation.UNDYING_POTION):
                await psql.Equipment.update_durability(conn, ctx.author.id, "undying_potion", has_undead_potion.remain_durability - 1)
                response_str += "*Undying Potion* activated, negating the most recent damage!\n"
                if has_undead_potion.remain_durability - 1 == 0:
                    response_str += "*Undying Potion* expired!\n"
            
            # Because we do take damage even if there's no drop, we need to check if the drop is empty before decreasing the potions that affect drops.
            empty_table = True
            for item, amount in loot_table.items():
                if not item == "raw_damage" and amount != 0:
                    empty_table = False
                    break
            
            if empty_table:
                response_str += "After a long exploring session, you came back with only dust and regret."
                await ctx.respond(response_str, reply = True, mentions_reply = True)
                return

            if potion_activated.has_flag(PotionActivation.LUCK_POTION):
                await psql.Equipment.update_durability(conn, ctx.author.id, "luck_potion", has_luck_potion.remain_durability - 1)
                response_str += "*Luck Potion* activated, giving you more rare drops!\n"
                if has_luck_potion.remain_durability - 1 == 0:
                    response_str += "*Luck Potion* expired!\n"
            if potion_activated.has_flag(PotionActivation.STRENGTH_POTION):
                await psql.Equipment.update_durability(conn, ctx.author.id, "strength_potion", has_strength_potion.remain_durability - 1)
                response_str += "*Strength Potion* activated, giving you a reward boost!\n"
                if has_strength_potion.remain_durability - 1 == 0:
                    response_str += "*Strength Potion* expired!\n"
            if potion_activated.has_flag(PotionActivation.LOOTING_POTION):
                await psql.Equipment.update_durability(conn, ctx.author.id, "looting_potion", has_looting_potion.remain_durability - 1)
                response_str += "*Looting Potion* activated, giving you a reward boost!\n"
                if has_looting_potion.remain_durability - 1 == 0:
                    response_str += "*Looting Potion* expired!\n"
            
            # Process badges.
            if loot_table.get("blaze_rod"):
                await psql.UserBadge.add_progress(conn, ctx.author.id, "blaze1", loot_table["blaze_rod"])
    
    response_str += f"You explored and obtained {get_reward_str(bot, loot_table, option = 'emote')}\n"
    if sword_existed.remain_durability - 1 == 0:
        sword_item = bot.item_cache[sword_existed.item_id]
        response_str += f"Your {sword_item.emoji} *{sword_item.name}* broke after the last exploring session!"
    
    await ctx.respond(response_str, reply = True)

@plugin.command()
@lightbulb.add_cooldown(length = 120, uses = 4, bucket = lightbulb.UserBucket, algorithm = lightbulb.SlidingWindowCooldownAlgorithm)
@lightbulb.option("location", "The location to explore. Some places are more dangerous than others.", choices = loot.CHOP_LOCATION, modifier = helpers.CONSUME_REST_OPTION)
@lightbulb.command("chop", f"[{plugin.name}] Use your axe to explore the surface.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def chop(ctx: lightbulb.Context):
    location: str = ctx.options.location
    bot: models.MichaelBot = ctx.bot

    user = bot.user_cache[ctx.author.id]
    if location not in loot.WORLD_LOCATION[user.world]:
        await bot.reset_cooldown(ctx)
        await ctx.respond(f"This location is not available in the {user.world.capitalize()}!",
            reply = True, mentions_reply = True)
        return

    potion_activated = PotionActivation(0)
    external_buffs = []
    response_str = ""

    async with bot.pool.acquire() as conn:
        equipments = await psql.Equipment.fetch_user_equipments(conn, ctx.author.id)
        relevant_equipments = filter_equipment_types(equipments, (
            "_axe",
            "luck_potion",
            "fire_potion",
            "undying_potion",
            "haste_potion",
            "nature_potion",
        ))

        axe_existed = relevant_equipments[0]
        if not axe_existed:
            await bot.reset_cooldown(ctx)
            await ctx.respond("You don't have an axe!", reply = True, mentions_reply = True)
            return
        
        dmg_reductions = loot.DMG_REDUCTIONS.get(axe_existed.item_id, 0)
        
        # Check external buffs for lowering death rate.
        has_luck_potion = relevant_equipments[1]
        has_fire_potion = relevant_equipments[2]
        has_undead_potion = relevant_equipments[3]
        has_haste_potion = relevant_equipments[4]
        has_nature_potion = relevant_equipments[5]
        # Also roll the potion if they exist, you lose all of them anw if you dies so.
        # After this, x_activated == True guarantees x_potion exists.
        if has_luck_potion:
            dmg_reductions += loot.DMG_REDUCTIONS["luck_potion"]
            if loot.roll_potion_activate("luck_potion"):
                potion_activated |= PotionActivation.LUCK_POTION
                external_buffs.append("luck_potion")
        if has_fire_potion:
            dmg_reductions += loot.DMG_REDUCTIONS["fire_potion"]
            if loot.roll_potion_activate("fire_potion"):
                potion_activated |= PotionActivation.FIRE_POTION
        if has_undead_potion:
            dmg_reductions += loot.DMG_REDUCTIONS["undying_potion"]
            if loot.roll_potion_activate("undying_potion"):
                potion_activated |= PotionActivation.UNDYING_POTION
        if has_haste_potion:
            dmg_reductions += loot.DMG_REDUCTIONS["haste_potion"]
            if loot.roll_potion_activate("haste_potion"):
                potion_activated |= PotionActivation.HASTE_POTION
                external_buffs.append("haste_potion")
        if has_nature_potion:
            dmg_reductions += loot.DMG_REDUCTIONS["nature_potion"]
            if loot.roll_potion_activate("nature_potion"):
                potion_activated |= PotionActivation.NATURE_POTION
                external_buffs.append("nature_potion")
        
        # Check for badges.
        if (death1_badge := await psql.UserBadge.fetch_one(conn, user_id = ctx.author.id, badge_id = "death1")) and death1_badge.completed():
            dmg_reductions += loot.DMG_REDUCTIONS["death1"] * len(equipments)
        if (death3_badge := await psql.UserBadge.fetch_one(conn, user_id = ctx.author.id, badge_id = "death3")) and death3_badge.completed():
            dmg_reductions += loot.DMG_REDUCTIONS["death3"] * len(equipments)
        if (wood2_badge := await psql.UserBadge.fetch_one(conn, user_id = ctx.author.id, badge_id = "wood2")) and wood2_badge.completed():
            external_buffs.append("wood2")
        
        loot_table = loot.get_activity_loot("chop", axe_existed.item_id, location, external_buffs)
        
        dmg_taken = get_final_damage(loot_table["raw_damage"], dmg_reductions)
        if dmg_taken > 1000:
            response_str += random.choice(loot.SUDDEN_DEATH_MESSAGES) if user.world != "end" else "You fell into the Void.\n"
        elif dmg_taken > 0:
            response_str += f"You took a damage of {dmg_taken}.\n"

        if user.health - dmg_taken <= 0:
            if not (user.world == "nether" and potion_activated.has_flag(PotionActivation.FIRE_POTION) or
                    potion_activated.has_flag(PotionActivation.UNDYING_POTION)):
                await process_death(conn, bot, user)
                response_str += "You died. Your health is 0 or below. You respawned, but you lost all your equipments, some items and money.\n"
                await ctx.respond(response_str, reply = True, mentions_reply = True)
                return
            
            if user.world == "nether" and potion_activated.has_flag(PotionActivation.FIRE_POTION):
                potion_activated ^= PotionActivation.UNDYING_POTION
        else:
            if not (dmg_taken > 60 and potion_activated.has_flag(PotionActivation.UNDYING_POTION)):
                user.health -= dmg_taken
                
                # Disable death-preventing potions if the user is not dead in the first place.
                potion_activated &= ~(PotionActivation.FIRE_POTION | PotionActivation.UNDYING_POTION)
            else:
                # Undying Potion activated and negated the damage, so we don't need to do anything.
                pass
        
        async with conn.transaction():
            await add_reward_to_user(conn, bot, ctx.author.id, loot_table)
            await psql.Equipment.update_durability(conn, ctx.author.id, axe_existed.item_id, axe_existed.remain_durability - 1)
            # Update health.
            await bot.user_cache.update(conn, user)
            
            # Process potions.
            if potion_activated.has_flag(PotionActivation.FIRE_POTION):
                await psql.Equipment.update_durability(conn, ctx.author.id, "fire_potion", has_fire_potion.remain_durability - 1)
                response_str += "*Fire Potion* activated, saving you from death!\n"
                if has_fire_potion.remain_durability - 1 == 0:
                    response_str += "*Fire Potion* expired!\n"
            if potion_activated.has_flag(PotionActivation.UNDYING_POTION):
                await psql.Equipment.update_durability(conn, ctx.author.id, "undying_potion", has_undead_potion.remain_durability - 1)
                response_str += "*Undying Potion* activated, negating the most recent damage!\n"
                if has_undead_potion.remain_durability - 1 == 0:
                    response_str += "*Undying Potion* expired!\n"
            
            # Because we do take damage even if there's no drop, we need to check if the drop is empty before decreasing the potions that affect drops.
            empty_table = True
            for item, amount in loot_table.items():
                if not item == "raw_damage" and amount != 0:
                    empty_table = False
                    break
            
            if empty_table:
                response_str += "After a long exploring session, you came back with only dust and regret."
                await ctx.respond(response_str, reply = True, mentions_reply = True)
                return

            if potion_activated.has_flag(PotionActivation.LUCK_POTION):
                await psql.Equipment.update_durability(conn, ctx.author.id, "luck_potion", has_luck_potion.remain_durability - 1)
                response_str += "*Luck Potion* activated, giving you more rare drops!\n"
                if has_luck_potion.remain_durability - 1 == 0:
                    response_str += "*Luck Potion* expired!\n"
            if potion_activated.has_flag(PotionActivation.HASTE_POTION):
                await psql.Equipment.update_durability(conn, ctx.author.id, "haste_potion", has_haste_potion.remain_durability - 1)
                response_str += "*Haste Potion* activated, giving you a reward boost!\n"
                if has_haste_potion.remain_durability - 1 == 0:
                    response_str += "*Haste Potion* expired!\n"
            if potion_activated.has_flag(PotionActivation.NATURE_POTION):
                await psql.Equipment.update_durability(conn, ctx.author.id, "nature_potion", has_nature_potion.remain_durability - 1)
                response_str += "*Nature Potion* activated, giving you a reward boost!\n"
                if has_nature_potion.remain_durability - 1 == 0:
                    response_str += "*Nature Potion* expired!\n"
            
            # Process badges.
            if loot_table.get("wood"):
                await psql.UserBadge.add_progress(conn, ctx.author.id, "wood1", loot_table["wood"])
                await psql.UserBadge.add_progress(conn, ctx.author.id, "wood2", loot_table["wood"])
    
    response_str += f"You chopped and collected {get_reward_str(bot, loot_table, option = 'emote')}\n"
    if axe_existed.remain_durability - 1 == 0:
        axe_item = bot.item_cache[axe_existed.item_id]
        response_str += f"Your {axe_item.emoji} *{axe_item.name}* broke after the last chopping session!"
    
    await ctx.respond(response_str, reply = True)

async def do_refresh_trade(bot: models.MichaelBot, when: dt.datetime = None):
    '''Renew trades and barters.

    This should be created as a `Task` to avoid logic-blocking if `when` is provided (the code itself is not async-blocking).

    Parameters
    ----------
    bot : models.MichaelBot
        The bot's instance. Mostly to access the item's cache and db connection.
    when : dt.datetime, optional
        The time to renew. If `None`, then instantly renew.
    '''
    if when is not None:
        await helpers.sleep_until(when)
    
    current = dt.datetime.now().astimezone()
    trades: list[psql.ActiveTrade] = trader.generate_trades(bot.item_cache, current + dt.timedelta(seconds = TRADE_REFRESH))
    barters: list[psql.ActiveTrade] = trader.generate_barters(bot.item_cache, current + dt.timedelta(seconds = TRADE_REFRESH))
    
    async with bot.pool.acquire() as conn:
        await psql.ActiveTrade.refresh(conn, trades + barters)

@tasks.task(s = TRADE_REFRESH, pass_app = True, wait_before_execution = False)
async def refresh_trade(bot: models.MichaelBot):
    '''Attempt to refresh the trades/barters every `TRADE_REFRESH` seconds.

    This has to be manually started instead of `auto_start` since the bot needs to check for current deal
    when startup.
    '''

    if bot.pool is None: return

    current = dt.datetime.now().astimezone()

    async with bot.pool.acquire() as conn:
        trades = await psql.ActiveTrade.fetch_all(conn)
        if trades:
            # Since all trades has virtually the same refresh time, check one is enough.
            # If trade is not yet reset, create a task to reset.
            if trades[0].next_reset > current:
                bot.create_task(do_refresh_trade(bot, trades[0].next_reset))
            else:
                await do_refresh_trade(bot)
        else:
            await do_refresh_trade(bot)

@plugin.listener(hikari.ShardReadyEvent)
async def on_shard_ready(_: hikari.ShardReadyEvent):
    refresh_trade.start()

@plugin.command()
@lightbulb.set_help(dedent(f'''
    - Trades can contains purchases that can't be made via `market`.
    - Trades will reset every {TRADE_REFRESH / 3600} hours.
    - This can only be used when you're in the Overworld.
'''))
@lightbulb.add_cooldown(length = 5, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.set_max_concurrency(uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.command("trade", f"[{plugin.name}] View and/or perform a trade. Get your money ready.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def _trade(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    user = bot.user_cache[ctx.author.id]
    if user.world != "overworld":
        await ctx.respond("You need to be in the Overworld to use this command!", reply = True, mentions_reply = True)
        return

    async with bot.pool.acquire() as conn:
        trades = await psql.ActiveTrade.fetch_all_where(conn, where = lambda r: r.type == "trade")
        # In case the trades get yeet manually during bot uptime.
        if not trades:
            await do_refresh_trade(bot)
            trades = await psql.ActiveTrade.fetch_all_where(conn, where = lambda r: r.type == "trade")
        
        user_trades = await psql.UserTrade.fetch_all_where(conn, where = lambda r: r.user_id == ctx.author.id and r.trade_type == "trade")

    embed = helpers.get_default_embed(
        description = f"*Trades will refresh in {humanize.precisedelta(trades[0].next_reset - dt.datetime.now().astimezone(), format = '%0.0f')}*",
        author = ctx.author,
        timestamp = dt.datetime.now().astimezone()
    ).set_author(
        name = "Available Trades",
        icon = bot.get_me().avatar_url
    ).set_thumbnail(bot.get_me().avatar_url)
    
    view = miru.View()
    options: list[miru.SelectOption] = []

    # Bunch of formatting here.
    for trade in trades:
        u_trade: psql.UserTrade = None
        trade_count: int = trade.hard_limit

        # Get the corresponding user trade to this trade.
        if user_trades:
            # I really run out of names to name this var man.
            for _u_trade in user_trades:
                if _u_trade.trade_id == trade.id:
                    u_trade = _u_trade
                    break

        # A bunch of ugly formatting code.
        src_str = ""
        if trade.item_src == "money":
            src_str = f"{CURRENCY_ICON}{trade.amount_src}"
        else:
            item = bot.item_cache[trade.item_src]
            src_str = f"{item.emoji} x {trade.amount_src}"
        
        dest_str = ""
        if trade.item_dest == "money":
            dest_str = f"{CURRENCY_ICON}{trade.amount_dest}"
        else:
            item = bot.item_cache[trade.item_dest]
            dest_str = f"{item.emoji} x {trade.amount_dest}"
        
        embed.add_field(
            name = f"Trade {trade.id} ({u_trade.count if u_trade else '0'}/{trade_count})",
            value = f"{src_str} ---> {dest_str}",
            inline = True
        )

        # Only add this option if the user can still trade.
        if u_trade is None or (u_trade.count < trade_count):
            options.append(miru.SelectOption(
                label = f"Trade {trade.id}",
                value = str(trade.id)
            ))
    view.add_item(miru.Select(
        options = options,
        placeholder = "Select a trade to perform"
    ))

    # Logically this should be ephemeral, but you can't get an ephemeral message object...
    resp = await ctx.respond(embed = embed, components = view.build())
    msg = await resp.message()
    await view.start(msg)

    def is_select_interaction(event: hikari.InteractionCreateEvent):
        if not isinstance(event.interaction, hikari.ComponentInteraction):
            return False
        
        return event.interaction.message.id == msg.id and event.interaction.member.id == ctx.author.id
    
    while True:
        try:
            event = await bot.wait_for(hikari.InteractionCreateEvent, timeout = 120, predicate = is_select_interaction)
            interaction: hikari.ComponentInteraction = event.interaction
            selected = int(interaction.values[0])
            selected_trade: psql.ActiveTrade = None
            for trade in trades:
                if trade.id == selected:
                    selected_trade = trade
                    break
            
            # Refetch for latest info.
            user = bot.user_cache[ctx.author.id]
            if user.world != "overworld":
                await ctx.respond("You need to be in the Overworld to use this command!", reply = True, mentions_reply = True)
                return
            
            if selected_trade is None:
                print(trades)
                print(selected)
                await ctx.respond("Something is wrong, report this to the dev.", reply = True, mentions_reply = True)
                return

            if selected_trade.next_reset < dt.datetime.now().astimezone():
                # Maybe edit into an updated trade?
                await msg.edit("This trade menu is expired. Invoke this command again for a list of updated trades.", embed = None, components = None)
                break
            
            # Process trade here.
            async with bot.pool.acquire() as conn:
                user_trade = await psql.UserTrade.fetch_one(conn, user_id = ctx.author.id, trade_id = selected, trade_type = "trade")
                if user_trade is None:
                    user_trade = psql.UserTrade(ctx.author.id, selected_trade.id, selected_trade.type, selected_trade.hard_limit, 0)

                if user_trade.count + 1 > user_trade.hard_limit:
                    await ctx.respond("You can't make this trade anymore!", reply = True, mentions_reply = True, 
                        flags = hikari.MessageFlag.EPHEMERAL
                    )
                elif selected_trade.item_src == "money":
                    inv = await psql.Inventory.fetch_one(conn, user_id = ctx.author.id, item_id = selected_trade.item_dest)

                    if user.balance < selected_trade.amount_src:
                        await ctx.respond("You don't have enough money to make this trade!", reply = True, mentions_reply = True, 
                            flags = hikari.MessageFlag.EPHEMERAL
                        )
                    else:
                        async with conn.transaction():
                            await add_reward_to_user(conn, bot, ctx.author.id, {selected_trade.item_dest: selected_trade.amount_dest})
                            user.balance -= selected_trade.amount_src
                            await bot.user_cache.update(conn, user)
                            user_trade.count += 1
                            await psql.UserTrade.update(conn, user_trade)
                elif selected_trade.item_dest == "money":
                    inv = await psql.Inventory.fetch_one(conn, user_id = ctx.author.id, item_id = selected_trade.item_src)

                    if inv is None or inv.amount < selected_trade.amount_src:
                        await ctx.respond("You don't have enough items to make this trade!", reply = True, mentions_reply = True,
                            flags = hikari.MessageFlag.EPHEMERAL
                        )
                    else:
                        async with conn.transaction():
                            await psql.Inventory.remove(conn, ctx.author.id, selected_trade.item_src, selected_trade.amount_src)
                            user.balance += selected_trade.amount_dest
                            await bot.user_cache.update(conn, user)
                            user_trade.count += 1
                            await psql.UserTrade.update(conn, user_trade)
                else:
                    inv = await psql.Inventory.fetch_one(conn, user_id = ctx.author.id, item_id = selected_trade.item_src)

                    if inv is None or inv.amount < selected_trade.amount_src:
                        await ctx.respond("You don't have enough items to make this trade!", reply = True, mentions_reply = True,
                            flags = hikari.MessageFlag.EPHEMERAL
                        )
                    else:
                        async with conn.transaction():
                            await psql.Inventory.remove(conn, ctx.author.id, selected_trade.item_src, selected_trade.amount_src)
                            await add_reward_to_user(conn, bot, ctx.author.id, {selected_trade.item_dest: selected_trade.amount_dest})
                            user_trade.count += 1
                            await psql.UserTrade.update(conn, user_trade)

            # Update the menu.
            embed.fields[selected - 1].name = f"Trade {selected} ({user_trade.count}/{selected_trade.hard_limit})"
            if user_trade.count == selected_trade.hard_limit:
                # Remove the select option based on the selected id.
                for i, option in enumerate(options):
                    if int(option.value) == selected_trade.id:
                        del options[i]
                        break
                
                view.clear_items()
                view.add_item(miru.Select(
                    options = options,
                    placeholder = "Select a trade to perform"
                ))
            
            try:
                await msg.edit(embed = embed, components = view.build())
            except hikari.NotFoundError:
                # Message is deleted most likely.
                return
        except asyncio.TimeoutError:
            try:
                await msg.edit(components = None)
            except hikari.NotFoundError:
                # Message is deleted most likely.
                return
            break

@plugin.command()
@lightbulb.set_help(dedent(f'''
    - Barters can contains purchases that can't be made via `market`.
    - Barters will reset every {TRADE_REFRESH / 3600} hours.
    - This can only be used when you're in the Nether.
'''))
@lightbulb.add_cooldown(length = 5, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.set_max_concurrency(uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.command("barter", f"[{plugin.name}] View and/or perform a barter. Get your gold ready.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def _barter(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    user = bot.user_cache[ctx.author.id]
    if user.world != "nether":
        await ctx.respond("You need to be in the Nether to use this command!", reply = True, mentions_reply = True)
        return

    async with bot.pool.acquire() as conn:
        barters = await psql.ActiveTrade.fetch_all_where(conn, where = lambda r: r.type == "barter")
        # In case the trades get yeet manually during bot uptime.
        if not barters:
            await do_refresh_trade(bot)
            barters = await psql.ActiveTrade.fetch_all_where(conn, where = lambda r: r.type == "barter")
        
        user_barters = await psql.UserTrade.fetch_all_where(conn, where = lambda r: r.user_id == ctx.author.id and r.trade_type == "barter")

    embed = helpers.get_default_embed(
        description = f"*Barters will refresh in {humanize.precisedelta(barters[0].next_reset - dt.datetime.now().astimezone(), format = '%0.0f')}*",
        author = ctx.author,
        timestamp = dt.datetime.now().astimezone()
    ).set_author(
        name = "Available Barters",
        icon = bot.get_me().avatar_url
    ).set_thumbnail(bot.get_me().avatar_url)
    
    view = miru.View()
    options: list[miru.SelectOption] = []

    # Bunch of formatting here.
    for barter in barters:
        u_barter: psql.UserTrade = None
        barter_count: int = barter.hard_limit

        # Get the corresponding user trade to this trade.
        if user_barters:
            for _u_barter in user_barters:
                if _u_barter.trade_id == barter.id:
                    u_barter = _u_barter
                    break

        item = bot.item_cache[barter.item_src]
        src_str = f"{item.emoji} x {barter.amount_src}"
        item = bot.item_cache[barter.item_dest]
        dest_str = f"{item.emoji} x {barter.amount_dest}"
        
        embed.add_field(
            name = f"Barter {barter.id} ({u_barter.count if u_barter else '0'}/{barter_count})",
            value = f"{src_str} ---> {dest_str}",
            inline = True
        )

        # Only add this option if the user can still trade.
        if u_barter is None or (u_barter.count < barter_count):
            options.append(miru.SelectOption(
                label = f"Barter {barter.id}",
                value = str(barter.id)
            ))
    view.add_item(miru.Select(
        options = options,
        placeholder = "Select a barter to perform"
    ))

    # Logically this should be ephemeral, but you can't get an ephemeral message object...
    resp = await ctx.respond(embed = embed, components = view.build())
    msg = await resp.message()
    await view.start(msg)

    def is_select_interaction(event: hikari.InteractionCreateEvent):
        if not isinstance(event.interaction, hikari.ComponentInteraction):
            return False
        
        return event.interaction.message.id == msg.id and event.interaction.member.id == ctx.author.id
    
    while True:
        try:
            event = await bot.wait_for(hikari.InteractionCreateEvent, timeout = 120, predicate = is_select_interaction)
            interaction: hikari.ComponentInteraction = event.interaction
            selected = int(interaction.values[0])
            selected_barter: psql.ActiveTrade = None
            for barter in barters:
                if barter.id == selected:
                    selected_barter = barter
                    break
            
            # Refetch for latest info.
            user = bot.user_cache[ctx.author.id]
            if user.world != "nether":
                await ctx.respond("You need to be in the Nether to use this command!", reply = True, mentions_reply = True)
                return
            
            if selected_barter is None:
                print(barters)
                print(selected)
                await ctx.respond("Something is wrong, report this to the dev.", reply = True, mentions_reply = True)
                return

            if selected_barter.next_reset < dt.datetime.now().astimezone():
                # Maybe edit into an updated barter?
                await msg.edit("This barter menu is expired. Invoke this command again for a list of updated barters.", embed = None, components = None)
                break
            
            # Process trade here.
            async with bot.pool.acquire() as conn:
                user_trade = await psql.UserTrade.fetch_one(conn, user_id = ctx.author.id, trade_id = selected, trade_type = "barter")
                if user_trade is None:
                    user_trade = psql.UserTrade(ctx.author.id, selected_barter.id, selected_barter.type, selected_barter.hard_limit, 0)

                if user_trade.count + 1 > user_trade.hard_limit:
                    await ctx.respond("You can't make this barter anymore!", reply = True, mentions_reply = True, 
                        flags = hikari.MessageFlag.EPHEMERAL
                    )
                else:
                    inv = await psql.Inventory.fetch_one(conn, user_id = ctx.author.id, item_id = selected_barter.item_src)

                    if inv is None or inv.amount < selected_barter.amount_src:
                        await ctx.respond("You don't have enough items to make this barter!", reply = True, mentions_reply = True,
                            flags = hikari.MessageFlag.EPHEMERAL
                        )
                    else:
                        async with conn.transaction():
                            await psql.Inventory.remove(conn, ctx.author.id, selected_barter.item_src, selected_barter.amount_src)
                            await add_reward_to_user(conn, bot, ctx.author.id, {selected_barter.item_dest: selected_barter.amount_dest})
                            user_trade.count += 1
                            await psql.UserTrade.update(conn, user_trade)

            # Update the menu.
            embed.fields[selected - 1].name = f"Barter {selected} ({user_trade.count}/{selected_barter.hard_limit})"
            if user_trade.count == selected_barter.hard_limit:
                # Remove the select option based on the selected id.
                for i, option in enumerate(options):
                    if int(option.value) == selected_barter.id:
                        del options[i]
                        break
                
                view.clear_items()
                view.add_item(miru.Select(
                    options = options,
                    placeholder = "Select a barter to perform"
                ))
            try:
                await msg.edit(embed = embed, components = view.build())
            except hikari.NotFoundError:
                # Message is deleted most likely.
                return
        except asyncio.TimeoutError:
            try:
                await msg.edit(components = None)
            except hikari.NotFoundError:
                # Message is deleted most likely.
                return
            break

@plugin.command()
@lightbulb.set_help(dedent('''
    - There is a hard cooldown of 4 hours between each travel, so plan ahead before moving.
    - It is recommended to use the `Slash Command` version of this command.
'''))
@lightbulb.option("world", "The world to travel to.", choices = ("overworld", "nether", "end"))
@lightbulb.command("travel", f"[{plugin.name}] Travel to another world.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def travel(ctx: lightbulb.Context):
    world: str = ctx.options.world
    bot: models.MichaelBot = ctx.bot

    if world not in ("overworld", "nether", "end"):
        raise lightbulb.NotEnoughArguments(missing = [ctx.invoked.options["world"]])
    
    user = bot.user_cache[ctx.author.id]
    current = dt.datetime.now().astimezone()
    if user.world == world:
        await ctx.respond("You're currently in this world already!", reply = True, mentions_reply = True)
        return
    if user.last_travel is not None:
        if current - user.last_travel < dt.timedelta(hours = 4):
            await ctx.respond(f"You'll need to wait for `{humanize.precisedelta(user.last_travel + dt.timedelta(hours = 4) - current, format = '%0.0f')}` before you can travel again.",
                reply = True, mentions_reply = True
            )
            return
    
    async with bot.pool.acquire() as conn:
        # We already check if world is in pre-determined arguments, so it's safe to do this.
        ticket = await psql.Inventory.fetch_one(conn, user_id = ctx.author.id, item_id = f"{world}_ticket")
        
        if ticket is None:
            await ctx.respond("You don't have the ticket to travel!", reply = True, mentions_reply = True)
            return
        
        async with conn.transaction():
            # Give free shulker box when first in the End.
            if world == "end":
                shulker_box = await psql.Inventory.fetch_one(conn, user_id = ctx.author.id, item_id = "shulker_box")
                if not shulker_box:
                    await psql.Inventory.add(conn, ctx.author.id, "shulker_box", 3)

            await psql.Inventory.remove(conn, ctx.author.id, ticket.item_id)
            user.world = world
            user.last_travel = dt.datetime.now().astimezone()
            await bot.user_cache.update(conn, user)
        
        success_announce = f"Successfully moved to the `{world.capitalize()}`."
        if world == "end":
            success_announce += "\n*Friendly reminder: Dying in the End will wipe 95%% of your inventory. Safe important items in your safe inventory before proceeding.*"
        await ctx.respond(success_announce, reply = True)

def load(bot: models.MichaelBot):
    bot.add_plugin(plugin)
def unload(bot: models.MichaelBot):
    bot.remove_plugin(plugin)
