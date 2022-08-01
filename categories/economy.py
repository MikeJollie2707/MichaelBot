import asyncio
import datetime as dt
import random
from textwrap import dedent

import lightbulb
import miru
import hikari
import humanize
from lightbulb.ext import tasks

from categories.econ import loot, trader
from utils import checks, converters, helpers, models, nav, psql

CURRENCY_ICON = "<:emerald:993835688137072670>"
TRADE_REFRESH = 3600 * 4

def get_death_rate(reward_value: int, equipment: psql.Equipment, world: str, reductions: float = 0) -> float:
    '''Return the dying chance based on the arguments provided.
    
    Death rate is capped at `0.15` (`0.45` if in nether) before taking `equipment` and `reductions` into consideration, so
    in most cases, this value is `[0, 0.15)` (or `[0, 0.45)`)
    '''

    cap_death = 0.15
    if world == "nether":
        cap_death = 0.45
    
    rate = min(cap_death, reward_value / (5 ** 4))
    
    if "wood" in equipment.item_id:
        rate -= 0.15
    elif "stone" in equipment.item_id:
        rate -= 0.15
    elif "iron" in equipment.item_id:
        rate -= 0.005
    elif "diamond" in equipment.item_id:
        rate -= 0.01
    elif "nether" in equipment.item_id:
        rate -= 0.05
    
    return max(rate - reductions, 0)

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

def multiply_reward(loot_table: dict[str, int], multiplier: int):
    '''A shortcut to multiply the rewards in-place.

    Parameters
    ----------
    loot_table : dict[str, int]
        The loot table.
    multiplier : int
        The multiplier. Cannot be 0.
    '''

    if multiplier == 0:
        raise ValueError("'multiplier' cannot be 0.")

    for key in loot_table:
        loot_table[key] *= multiplier

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

async def add_reward(conn, user_id: int, loot_table: dict[str, int]):
    '''A shortcut to add rewards to the user.

    For some special keys (as defined in `loot.RESERVED_KEYS`), this will attempt to add money also.

    Notes
    -----
    This function has its own transaction.

    Parameters
    ----------
    conn : asyncpg.Connection
        The connection to use.
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
            if item_id == "cost":
                money -= amount
            else:
                money += amount
        await psql.User.add_money(conn, user_id, money)

async def process_death(conn, bot: models.MichaelBot, user: psql.User):
    '''A shortcut to process a user's death.

    This includes wiping all their equipped tools, 5% of their inventories, 20% of their money,
    and move them to the Overworld.

    Parameters
    ----------
    conn : asyncpg.Connection
        The connection to use.
    bot : models.MichaelBot
        The bot instance.
    user : psql.User
        The user to process.
    '''

    equipments = await psql.Equipment.get_user_equipments(conn, user.id)
    inventories = await psql.Inventory.get_user_inventory(conn, user.id)
    
    async with conn.transaction():
        for equipment in equipments:
            if not ("nether_" in equipment.item_id and user.world == "nether"):
                await psql.Equipment.delete(conn, user.id, equipment.item_id)
        
        for inv in inventories:
            inv.amount -= inv.amount * 5 // 100
            await psql.Inventory.update(conn, inv)
        
        user.balance -= user.balance * 20 // 100
        user.world = "overworld"
        await bot.user_cache.update(conn, user)

plugin = lightbulb.Plugin("Economy", "Economic Commands", include_datastore = True)
plugin.d.emote = helpers.get_emote(":dollar:")
plugin.add_checks(
    checks.is_db_connected, 
    checks.is_command_enabled, 
    lightbulb.bot_has_guild_permissions(*helpers.COMMAND_STANDARD_PERMISSIONS)
)

@plugin.command()
@lightbulb.command("balance", "View your balance.", aliases = ["bal"])
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def balance(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    async with bot.pool.acquire() as conn:
        user = await psql.User.get_one(conn, ctx.author.id)
        await ctx.respond(f"You have {CURRENCY_ICON}{user.balance}.")

@plugin.command()
@lightbulb.option("money", "The amount to bet. You'll either lose this or get 2x back. At least 1.", type = int, default = 1, min_value = 1)
@lightbulb.option("number", "Your guessing number. Stay within 0-50!", type = int, min_value = 0, max_value = 50)
@lightbulb.command("bet", "Bet your money to guess a number in the range 0-50. Don't worry, I won't cheat :)")
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
        confirm_menu = nav.ConfirmView(timeout = 10)
        resp = await ctx.respond("You're betting all your money right now, are you sure about this?", reply = True, components = confirm_menu.build())
        confirm_menu.start(await resp.message())
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
@lightbulb.command("additem", "Add item.")
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
@lightbulb.command("addmoney", "Add money.")
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
@lightbulb.option("potion", "the name or alias of the potion to brew.", type = converters.ItemConverter, autocomplete = True)
@lightbulb.command("brew", "Brew various potions.")
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
        user.balance -= recipe["cost"]
    
    async with bot.pool.acquire() as conn:
        # Try removing the items; if any falls below 0, it fails to craft.
        success: bool = True
        missing: dict[str, int] = {}
        # Only retrieve relevant items.
        inventories = await psql.Inventory.get_all_where(conn, where = lambda r: r.item_id in recipe and r.user_id == ctx.author.id)

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
            # Update balance.
            await bot.user_cache.update(conn, user)
            await psql.Inventory.add(conn, ctx.author.id, potion.id, recipe["result"])
    await ctx.respond(f"Successfully brewed {get_reward_str(bot, {potion.id: recipe['result']})}.", reply = True)
@brew.autocomplete("potion")
async def brew_potion_autocomplete(option: hikari.AutocompleteInteractionOption, interaction: hikari.AutocompleteInteraction):
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

@plugin.command()
@lightbulb.set_help(dedent('''
    - It is recommended to use the `Slash Command` version of this command.
'''))
@lightbulb.add_cooldown(length = 1, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.option("times", "How many times this command is executed. Default to 1.", type = int, min_value = 1, max_value = 100, default = 1)
@lightbulb.option("item", "The name or alias of the item to craft.", type = converters.ItemConverter, autocomplete = True)
@lightbulb.command("craft", "Craft various items.")
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
        inventories = await psql.Inventory.get_all_where(conn, where = lambda r: r.item_id in recipe and r.user_id == ctx.author.id)

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
            await psql.Inventory.add(conn, ctx.author.id, item.id, recipe["result"])
    await ctx.respond(f"Successfully crafted {get_reward_str(bot, {item.id: recipe['result']})}.", reply = True)
@craft.autocomplete("item")
async def craft_item_autocomplete(option: hikari.AutocompleteInteractionOption, interaction: hikari.AutocompleteInteraction):
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

@plugin.command()
@lightbulb.set_help(dedent('''
    - There is a hard cooldown of 24 hours before you can collect the next daily.
    - The higher the daily streak, the better your reward will be.
    - If you don't collect your daily within 48 hours since the last time you collect, your streak will be reset to 1.
'''))
@lightbulb.command("daily", "Receive rewards everyday. Don't miss it though!")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def daily(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    response: str = ""
    async with bot.pool.acquire() as conn:
        existed = bot.user_cache.get(ctx.author.id)
        
        # User should be guaranteed to be created via checks.is_command_enabled() check.
        assert existed is not None

        now = dt.datetime.now().astimezone()
        async with conn.transaction():
            if existed.last_daily is None:
                response += "Yooo first time collecting daily, welcome!\n"
                existed.daily_streak = 1
            elif now - existed.last_daily < dt.timedelta(days = 1):
                remaining_time = dt.timedelta(days = 1) + existed.last_daily - now
                await ctx.respond(f"You're a bit too early. You have `{humanize.precisedelta(remaining_time, format = '%0.0f')}` left.")
                return
            # A user need to collect the daily before the second day.
            elif now - existed.last_daily >= dt.timedelta(days = 2):
                # They're collecting daily now, so it's 1.
                response += f"Oops, your old streak of `{existed.daily_streak}x` got obliterated. Wake up early next time :)\n"
                existed.daily_streak = 1
            else:
                existed.daily_streak += 1
                response += f"You gained a new streak! Your streak now: `{existed.daily_streak}x`\n"
            
            existed.last_daily = now
            await bot.user_cache.update(conn, existed)

            daily_loot = loot.get_daily_loot(existed.daily_streak)
            await add_reward(conn, ctx.author.id, daily_loot)
            response += f"You received: {get_reward_str(bot, daily_loot, option = 'emote')}\n"

        await ctx.respond(response, reply = True)

@plugin.command()
@lightbulb.set_help(dedent('''
    - It is recommended to use the `Slash Command` version of this command.
'''))
@lightbulb.add_cooldown(length = 10, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.option("equipment", "The equipment's name or alias to equip.", type = converters.ItemConverter, autocomplete = True)
@lightbulb.command("equip", "Equip a tool. Get to work!")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def equip(ctx: lightbulb.Context):
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
        inv = await psql.Inventory.get_one(conn, ctx.author.id, item.id)
        if not inv:
            await bot.reset_cooldown(ctx)
            await ctx.respond("You don't have this equipment in your inventory!", reply = True, mentions_reply = True)
            return
        
        # Check for equipment type conflict.
        existed: psql.Equipment = await psql.Equipment.get_equipment(conn, ctx.author.id, psql.Equipment.get_equipment_type(item.id))
        response_str = ""

        if existed:
            # Destroy old equipment, then move new one.
            existed_item = bot.item_cache.get(existed.item_id)
            async with conn.transaction():
                await psql.Equipment.delete(conn, ctx.author.id, existed.item_id)
                await psql.Equipment.transfer_from_inventory(conn, inv)
                response_str += f"Unequipped *{existed_item.name}* into the void.\n"
        else:
            await psql.Equipment.transfer_from_inventory(conn, inv)
        response_str += f"Equipped *{item.name}*."
        
        await ctx.respond(response_str, reply = True)
@equip.autocomplete("equipment")
async def equip_equipment_autocomplete(option: hikari.AutocompleteInteractionOption, interaction: hikari.AutocompleteInteraction):
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

@plugin.command()
@lightbulb.set_help(dedent('''
    - It is recommended to use the `Slash Command` version of this command.
'''))
@lightbulb.add_cooldown(length = 10, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.option("potion", "The potion's name or alias to use.", type = converters.ItemConverter, autocomplete = True)
@lightbulb.command("usepotion", "Use a potion.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def usepotion(ctx: lightbulb.Context):
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
        inv = await psql.Inventory.get_one(conn, ctx.author.id, potion.id)
        if not inv:
            await bot.reset_cooldown(ctx)
            await ctx.respond("You don't have this potion in your inventory!", reply = True, mentions_reply = True)
            return

        potions = await psql.Equipment.get_user_potions(conn, ctx.author.id)
        if len(potions) >= 3:
            await bot.reset_cooldown(ctx)
            await ctx.respond("You currently have 3 potions equipped. You'll need to wait for one of them to expire before using another.", reply = True, mentions_reply = True)
            return
        existed = await psql.Equipment.get_one(conn, ctx.author.id, potion.id)
        if existed:
            await bot.reset_cooldown(ctx)
            await ctx.respond("You're already using this potion.", reply = True, mentions_reply = True)
            return
        
        await psql.Equipment.transfer_from_inventory(conn, inv)
        
    await ctx.respond(f"Equipped *{potion.name}*", reply = True)
@usepotion.autocomplete("potion")
async def usepotion_potion_autocomplete(option: hikari.AutocompleteInteractionOption, interaction: hikari.AutocompleteInteraction):
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

@plugin.command()
@lightbulb.add_cooldown(length = 10, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.command("equipments", "View your current equipments.")
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

    async with bot.pool.acquire() as conn:
        equipments = await psql.Equipment.get_user_equipments(conn, ctx.author.id)
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
@lightbulb.command("inventory", "View your inventory.", aliases = ["inv"])
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def inventory(ctx: lightbulb.Context):
    view_option = ctx.options.view_option
    bot: models.MichaelBot = ctx.bot
    
    async with bot.pool.acquire() as conn:
        inventories = await psql.Inventory.get_user_inventory(conn, ctx.author.id)
        if not inventories:
            await ctx.respond("*Cricket noises*", reply = True)
            return
        
        if view_option == "compact":
            inv_dict: dict[str, int] = {}
            for inv in inventories:
                inv_dict[inv.item_id] = inv.amount
            await ctx.respond(f"**{ctx.author.username}'s Inventory**\n{get_reward_str(bot, inv_dict, option = 'emote')}", reply = True)
        elif view_option == "full":
            page = nav.ItemListBuilder(inventories, 5)
            @page.set_page_start_formatter
            def start_format(index: int, inv: psql.Inventory) -> hikari.Embed:
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
            def entry_format(embed: hikari.Embed, index: int, inv: psql.Inventory):
                item = bot.item_cache[inv.item_id]
                embed.add_field(
                    name = f"{inv.amount}x {item.emoji} {item.name}",
                    value = f"*{item.description}*\nTotal value: {CURRENCY_ICON}{item.sell_price * inv.amount}"
                )
            
            await nav.run_view(page.build(), ctx)
        elif view_option == "value":
            value = 0
            for inv in inventories:
                item = bot.item_cache[inv.item_id]
                value += item.sell_price * inv.amount
            await ctx.respond(f"If you sell all your items in your inventory, you'll get: {CURRENCY_ICON}{value}.", reply = True)

@plugin.command()
@lightbulb.command("market", "View public purchases.")
@lightbulb.implements(lightbulb.PrefixCommandGroup, lightbulb.SlashCommandGroup)
async def market(ctx: lightbulb.Context):
    await market_view(ctx)

@market.child
@lightbulb.command("view", "View public purchases.")
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
    
    await nav.run_view(builder.build(), ctx)

@market.child
@lightbulb.option("amount", "The amount to purchase. Default to 1.", type = int, min_value = 1, default = 1)
@lightbulb.option("item", "The item to purchase.", type = converters.ItemConverter, autocomplete = True)
@lightbulb.command("buy", "Buy an item from the market.")
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
            await psql.Inventory.add(conn, ctx.author.id, item.id, amount)
            await bot.user_cache.update(conn, user)
    
    await ctx.respond(f"Successfully purchased {get_reward_str(bot, {item.id : amount}, option = 'emote')}.", reply = True)

@market.child
@lightbulb.option("amount", "The amount to sell, or 0 to sell all. Default to 1.", type = int, min_value = 0, default = 1)
@lightbulb.option("item", "The item to sell.", type = converters.ItemConverter, autocomplete = True)
@lightbulb.command("sell", "Sell items from your inventory.")
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
        inv = await psql.Inventory.get_one(conn, ctx.author.id, item.id)
        if not inv or inv.amount < amount:
            await ctx.respond("You don't have enough of this item to sell.", reply = True, mentions_reply = True)
            return
        
        if amount == 0:
            amount = inv.amount
        
        profit = item.sell_price * amount
        user = bot.user_cache[ctx.author.id]
        user.balance += profit

        async with conn.transaction():
            await psql.Inventory.remove(conn, ctx.author.id, item.id, amount)
            await bot.user_cache.update(conn, user)
    
    await ctx.respond(f"Successfully sold {get_reward_str(bot, {item.id : amount}, option = 'emote')} for {CURRENCY_ICON}{profit}.", reply = True)

@market_buy.autocomplete("item")
@market_sell.autocomplete("item")
async def item_autocomplete(option: hikari.AutocompleteInteractionOption, interaction: hikari.AutocompleteInteraction):
    # Specifically for this command, we can autocomplete items
    # that appears in inventory, but we'll need to cache, 
    # otherwise it'll be very expensive to request DB every character.
    bot: models.MichaelBot = interaction.app

    def match_algorithm(name: str, input_value: str):
        return name.lower().startswith(input_value.lower())

    items = []
    for item in bot.item_cache.values():
        items.append(item.name)
    
    if option.value == '':
        return items[:25]
    return [match_equipment for match_equipment in items if match_algorithm(match_equipment, option.value)][:25]

@plugin.command()
@lightbulb.add_cooldown(length = 120, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.command("mine", "Mine for resources. You'll need a pickaxe equipped.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def mine(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    luck_activated = False
    fire_activated = False
    fortune_activated = False
    response_str = ""

    async with bot.pool.acquire() as conn:
        pickaxe_existed = await psql.Equipment.get_equipment(conn, ctx.author.id, "_pickaxe")
        if not pickaxe_existed:
            await bot.reset_cooldown(ctx)
            await ctx.respond("You don't have a pickaxe!", reply = True, mentions_reply = True)
            return
        
        user = bot.user_cache[ctx.author.id]
        if pickaxe_existed.item_id == "bed_pickaxe" and user.world == "overworld":
            await bot.reset_cooldown(ctx)
            await ctx.respond("This pickaxe doesn't work in the Overworld!", reply = True, mentions_reply = True)
            return
        
        death_reductions = 0
        
        # Check external buffs for lowering death rate.
        has_luck_potion = await psql.Equipment.get_one(conn, ctx.author.id, "luck_potion")
        has_fire_potion = await psql.Equipment.get_one(conn, ctx.author.id, "fire_potion")
        has_fortune_potion = await psql.Equipment.get_one(conn, ctx.author.id, "fortune_potion")
        # Also roll the potion if they exist, you lose all of them anw if you dies so.
        # After this, x_activated == True guarantees x_potion exists.
        if has_luck_potion:
            death_reductions += 0.005
            luck_activated = loot.roll_potion_activate("luck_potion")
        if has_fire_potion:
            death_reductions += 0.01
            fire_activated = loot.roll_potion_activate("fire_potion")
        if has_fortune_potion:
            fortune_activated = loot.roll_potion_activate("fortune_potion")
        
        loot_table = loot.get_activity_loot(pickaxe_existed.item_id, user.world, luck_activated)
        if not loot_table:
            await bot.reset_cooldown(ctx)
            await ctx.respond("Oof, I can't seem to generate a working loot table. Might want to report this to dev so they can fix it.", reply = True, mentions_reply = True)
            return
        
        death_rate = get_death_rate(get_reward_value(loot_table, bot.item_cache), pickaxe_existed, user.world, death_reductions)
        r = random.random()
        # Dies
        if r <= death_rate:
            if not (user.world == "nether" and fire_activated):
                await process_death(conn, bot, user)
                await ctx.respond("You had an accident and died miserably. All your equipments are lost, and you lost some of your items and money.", reply = True, mentions_reply = True)
                return
        # Disable fire potion if the user is not dead in the first place.
        elif fire_activated:
            fire_activated = False
        
        if luck_activated:
            multiply_reward(loot_table, 5)
        if fortune_activated:
            multiply_reward(loot_table, 5)
        
        async with conn.transaction():
            await add_reward(conn, ctx.author.id, loot_table)
            await psql.Equipment.update_durability(conn, ctx.author.id, pickaxe_existed.item_id, pickaxe_existed.remain_durability - 1)
            
            if fire_activated:
                await psql.Equipment.update_durability(conn, ctx.author.id, "fire_potion", has_fire_potion.remain_durability - 1)
                response_str += "*Fire Potion* activated, saving you from death!\n"
            if luck_activated:
                await psql.Equipment.update_durability(conn, ctx.author.id, "luck_potion", has_luck_potion.remain_durability - 1)
                response_str += "*Luck Potion* activated, giving you a reward boost!\n"
            if fortune_activated:
                await psql.Equipment.update_durability(conn, ctx.author.id, "fortune_potion", has_fortune_potion.remain_durability - 1)
                response_str += "*Fortune Potion* activated, giving you a reward boost!\n"
    
    response_str += f"You mined and received {get_reward_str(bot, loot_table, option = 'emote')}\n"
    if pickaxe_existed.remain_durability - 1 == 0:
        pickaxe_item = bot.item_cache[pickaxe_existed.item_id]
        response_str += f"Your {pickaxe_item.emoji} *{pickaxe_item.name}* broke after the last mining session!"
    
    await ctx.respond(response_str, reply = True)

@plugin.command()
@lightbulb.add_cooldown(length = 120, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.command("explore", "Explore the caves and get resources by killing monsters. You'll need a sword equipped.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def explore(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    luck_activated = False
    fire_activated = False
    looting_activated = False
    response_str = ""

    async with bot.pool.acquire() as conn:
        sword_existed = await psql.Equipment.get_equipment(conn, ctx.author.id, "_sword")
        if not sword_existed:
            await bot.reset_cooldown(ctx)
            await ctx.respond("You don't have a sword!", reply = True, mentions_reply = True)
            return
        
        user = bot.user_cache[ctx.author.id]

        death_reductions = 0
        
        # Check external buffs for lowering death rate.
        has_luck_potion = await psql.Equipment.get_one(conn, ctx.author.id, "luck_potion")
        has_fire_potion = await psql.Equipment.get_one(conn, ctx.author.id, "fire_potion")
        has_looting_potion = await psql.Equipment.get_one(conn, ctx.author.id, "looting_potion")
        # Also roll the potion if they exist, you lose all of them anw if you dies so.
        # After this, x_activated == True guarantees x_potion exists.
        if has_luck_potion:
            death_reductions += 0.005
            luck_activated = loot.roll_potion_activate("luck_potion")
        if has_fire_potion:
            death_reductions += 0.01
            fire_activated = loot.roll_potion_activate("fire_potion")
        if has_looting_potion:
            looting_activated = loot.roll_potion_activate("looting_potion")
        
        loot_table = loot.get_activity_loot(sword_existed.item_id, user.world, luck_activated)
        if not loot_table:
            await bot.reset_cooldown(ctx)
            await ctx.respond("Oof, I can't seem to generate a working loot table. Might want to report this to dev so they can fix it.", reply = True, mentions_reply = True)
            return
        
        death_rate = get_death_rate(get_reward_value(loot_table, bot.item_cache), sword_existed, user.world, death_reductions)
        r = random.random()
        # Dies
        if r <= death_rate:
            if not (user.world == "nether" and fire_activated):
                await process_death(conn, bot, user)
                await ctx.respond("You had an accident and died miserably. All your equipments are lost, and you lost some of your items and money.", reply = True, mentions_reply = True)
                return
        # Disable fire potion if the user is not dead in the first place.
        elif fire_activated:
            fire_activated = False
        
        if luck_activated:
            multiply_reward(loot_table, 5)
        if looting_activated:
            multiply_reward(loot_table, 5)
        
        async with conn.transaction():
            await add_reward(conn, ctx.author.id, loot_table)
            await psql.Equipment.update_durability(conn, ctx.author.id, sword_existed.item_id, sword_existed.remain_durability - 1)
            
            if fire_activated:
                await psql.Equipment.update_durability(conn, ctx.author.id, "fire_potion", has_fire_potion.remain_durability - 1)
                response_str += "*Fire Potion* activated, saving you from death!\n"
            if luck_activated:
                await psql.Equipment.update_durability(conn, ctx.author.id, "luck_potion", has_luck_potion.remain_durability - 1)
                response_str += "*Luck Potion* activated, giving you a reward boost!\n"
            if looting_activated:
                await psql.Equipment.update_durability(conn, ctx.author.id, "looting_potion", has_looting_potion.remain_durability - 1)
                response_str += "*Looting Potion* activated, giving you a reward boost!\n"
    
    response_str += f"You explored and obtained {get_reward_str(bot, loot_table, option = 'emote')}\n"
    if sword_existed.remain_durability - 1 == 0:
        sword_item = bot.item_cache[sword_existed.item_id]
        response_str += f"Your {sword_item.emoji} *{sword_item.name}* broke after the last exploring session!"
    
    await ctx.respond(response_str, reply = True)

@plugin.command()
@lightbulb.add_cooldown(length = 120, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.command("chop", "Chop trees from various forest to gain plant-related resources. You'll need an axe equipped.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def chop(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    luck_activated = False
    fire_activated = False
    nature_activated = False
    response_str = ""

    async with bot.pool.acquire() as conn:
        axe_existed = await psql.Equipment.get_equipment(conn, ctx.author.id, "_axe")
        if not axe_existed:
            await bot.reset_cooldown(ctx)
            await ctx.respond("You don't have an axe!", reply = True, mentions_reply = True)
            return
        
        user = bot.user_cache[ctx.author.id]
        
        death_reductions = 0
        
        # Check external buffs for lowering death rate.
        has_luck_potion = await psql.Equipment.get_one(conn, ctx.author.id, "luck_potion")
        has_fire_potion = await psql.Equipment.get_one(conn, ctx.author.id, "fire_potion")
        has_nature_potion = await psql.Equipment.get_one(conn, ctx.author.id, "nature_potion")
        # Also roll the potion if they exist, you lose all of them anw if you dies so.
        # After this, x_activated == True guarantees x_potion exists.
        if has_luck_potion:
            death_reductions += 0.005
            luck_activated = loot.roll_potion_activate("loot_potion")
        if has_fire_potion:
            death_reductions += 0.01
            fire_activated = loot.roll_potion_activate("fire_potion")
        if has_nature_potion:
            death_reductions += 0.02
            nature_activated = loot.roll_potion_activate("nature_potion")
        
        loot_table = loot.get_activity_loot(axe_existed.item_id, user.world, luck_activated)
        if not loot_table:
            await bot.reset_cooldown(ctx)
            await ctx.respond("Oof, I can't seem to generate a working loot table. Might want to report this to dev so they can fix it.", reply = True, mentions_reply = True)
            return
        # Disable fire potion if the user is not dead in the first place.
        elif fire_activated:
            fire_activated = False
        
        death_rate = get_death_rate(get_reward_value(loot_table, bot.item_cache), axe_existed, user.world, death_reductions)
        r = random.random()
        # Dies
        if r <= death_rate:
            if not (user.world == "nether" and fire_activated):
                await process_death(conn, bot, user)
                await ctx.respond("You had an accident and died miserably. All your equipments are lost, and you lost some of your items and money.", reply = True, mentions_reply = True)
                return
        
        if luck_activated:
            multiply_reward(loot_table, 5)
        if nature_activated:
            multiply_reward(loot_table, 5)
        
        async with conn.transaction():
            await add_reward(conn, ctx.author.id, loot_table)
            await psql.Equipment.update_durability(conn, ctx.author.id, axe_existed.item_id, axe_existed.remain_durability - 1)
            
            if fire_activated:
                await psql.Equipment.update_durability(conn, ctx.author.id, "fire_potion", has_fire_potion.remain_durability - 1)
                response_str += "*Fire Potion* activated, saving you from death!\n"
            if luck_activated:
                await psql.Equipment.update_durability(conn, ctx.author.id, "luck_potion", has_luck_potion.remain_durability - 1)
                response_str += "*Luck Potion* activated, giving you a reward boost!\n"
            if nature_activated:
                await psql.Equipment.update_durability(conn, ctx.author.id, "nature_potion", has_nature_potion.remain_durability - 1)
                response_str += "*Fortune Potion* activated, giving you a reward boost!\n"
    
    response_str += f"You chopped and collected {get_reward_str(bot, loot_table, option = 'emote')}\n"
    if axe_existed.remain_durability - 1 == 0:
        axe_item = bot.item_cache[axe_existed.item_id]
        response_str += f"Your {axe_item.emoji} *{axe_item.name}* broke after the last chopping session!"
    
    await ctx.respond(response_str, reply = True)

async def do_refresh_trade(bot: models.MichaelBot, when: dt.datetime = None):
    '''Renew trades and barters.

    This should be created as a `Task` to avoid logic-blocking (the code itself is not async-blocking).

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
        trades = await psql.ActiveTrade.get_all(conn)
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
async def on_shard_ready(event: hikari.ShardReadyEvent):
    refresh_trade.start()

@plugin.command()
@lightbulb.set_help(dedent(f'''
    - Trades can contains purchases that can't be made via `market`.
    - Trades will reset every {TRADE_REFRESH / 3600} hours.
    - This can only be used when you're in the Overworld.
'''))
@lightbulb.add_cooldown(length = 5, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.command("trade", "View and/or perform a trade. Get your money ready.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def _trade(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    user = bot.user_cache[ctx.author.id]
    if user.world != "overworld":
        await ctx.respond("You need to be in the Overworld to use this command!", reply = True, mentions_reply = True)
        return

    async with bot.pool.acquire() as conn:
        trades = await psql.ActiveTrade.get_all_where(conn, where = lambda r: r.type == "trade")
        user_trades = await psql.UserTrade.get_all_where(conn, where = lambda r: r.user_id == ctx.author.id and r.trade_type == "trade")

    embed = helpers.get_default_embed(
        description = f"*Trades will refresh in {humanize.precisedelta(trades[0].next_reset - dt.datetime.now().astimezone(), format = '%0.0f')}*",
        author = ctx.author,
        timestamp = dt.datetime.now().astimezone()
    ).set_author(
        name = "Available Trades",
        icon = bot.get_me().avatar_url
    ).set_thumbnail(bot.get_me().avatar_url)
    
    view = miru.View()
    options = []

    # Bunch of formatting here.
    for i, trade in enumerate(trades):
        user_trade_count: int = 0
        trade_count: int = trade.hard_limit

        # Get the corresponding user trade to this trade.
        if user_trades:
            for u_trade in user_trades:
                if u_trade.trade_id == trade.id:
                    user_trade_count = u_trade.count
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
            name = f"Trade {i + 1} ({user_trade_count}/{trade_count})",
            value = f"{src_str} ---> {dest_str}",
            inline = True
        )

        options.append(miru.SelectOption(
            label = f"Trade {i + 1}",
            value = str(i + 1)
        ))
    view.add_item(miru.Select(
        options = options,
        placeholder = "Select a trade to perform"
    ))

    # Logically this should be ephemeral, but you can't get an ephemeral message object...
    resp = await ctx.respond(embed = embed, components = view.build())
    msg = await resp.message()
    view.start(msg)

    def is_select_interaction(event: hikari.InteractionCreateEvent):
        if not isinstance(event.interaction, hikari.ComponentInteraction):
            return False
        
        return event.interaction.message.id == msg.id and event.interaction.member.id == ctx.author.id
    
    while True:
        try:
            event = await bot.wait_for(hikari.InteractionCreateEvent, timeout = 120, predicate = is_select_interaction)
            interaction: hikari.ComponentInteraction = event.interaction
            selected = int(interaction.values[0])
            selected_trade = trades[selected - 1]

            if selected_trade.next_reset < dt.datetime.now().astimezone():
                # Maybe edit into an updated trade?
                await msg.edit("This trade menu is expired. Invoke this command again for a list of updated trades.", embed = None, components = None)
                break
            
            # Process trade here.
            async with bot.pool.acquire() as conn:
                user_trade = await psql.UserTrade.get_one(conn, ctx.author.id, selected, "trade")
                if user_trade is None:
                    user_trade = psql.UserTrade(ctx.author.id, selected_trade.id, selected_trade.type, selected_trade.hard_limit, 0)

                if user_trade.count + 1 > user_trade.hard_limit:
                    await ctx.respond("You can't make this trade anymore!", reply = True, mentions_reply = True, 
                        flags = hikari.MessageFlag.EPHEMERAL
                    )
                    continue

                if selected_trade.item_src == "money":
                    inv = await psql.Inventory.get_one(conn, ctx.author.id, selected_trade.item_dest)

                    if user.balance < selected_trade.amount_src:
                        await ctx.respond("You don't have enough money to make this trade!", reply = True, mentions_reply = True, 
                            flags = hikari.MessageFlag.EPHEMERAL
                        )
                        continue

                    async with conn.transaction():
                        await psql.Inventory.add(conn, ctx.author.id, selected_trade.item_dest, selected_trade.amount_dest)
                        user.balance -= selected_trade.amount_src
                        await bot.user_cache.update(conn, user)
                        user_trade.count += 1
                        await psql.UserTrade.update(conn, user_trade)
                elif selected_trade.item_dest == "money":
                    inv = await psql.Inventory.get_one(conn, ctx.author.id, selected_trade.item_src)

                    if inv is None or inv.amount < selected_trade.amount_src:
                        await ctx.respond("You don't have enough items to make this trade!", reply = True, mentions_reply = True,
                            flags = hikari.MessageFlag.EPHEMERAL
                        )
                        continue

                    async with conn.transaction():
                        await psql.Inventory.remove(conn, ctx.author.id, selected_trade.item_src, selected_trade.amount_src)
                        user.balance += selected_trade.amount_dest
                        await bot.user_cache.update(conn, user)
                        user_trade.count += 1
                        await psql.UserTrade.update(conn, user_trade)
                else:
                    inv = await psql.Inventory.get_one(conn, ctx.author.id, selected_trade.item_src)

                    if inv is None or inv.amount < selected_trade.amount_src:
                        await ctx.respond("You don't have enough items to make this trade!", reply = True, mentions_reply = True,
                            flags = hikari.MessageFlag.EPHEMERAL
                        )
                        continue

                    async with conn.transaction():
                        await psql.Inventory.remove(conn, ctx.author.id, selected_trade.item_src, selected_trade.amount_src)
                        await psql.Inventory.add(conn, ctx.author.id, selected_trade.item_dest, selected_trade.amount_dest)
                        user_trade.count += 1
                        await psql.UserTrade.update(conn, user_trade)

                # Update the menu.
                embed.fields[selected - 1].name = f"Trade {selected} ({user_trade.count}/{selected_trade.hard_limit})"
                if user_trade.count == selected_trade.hard_limit:
                    del options[selected - 1]
                    view.clear_items()
                    view.add_item(miru.Select(
                        options = options,
                        placeholder = "Select a trade to perform"
                    ))
                await msg.edit(embed = embed, components = view.build())
        except asyncio.TimeoutError:
            await msg.edit(components = None)
            break

@plugin.command()
@lightbulb.set_help(dedent(f'''
    - Barters can contains purchases that can't be made via `market`.
    - Barters will reset every {TRADE_REFRESH / 3600} hours.
    - This can only be used when you're in the Nether.
'''))
@lightbulb.add_cooldown(length = 5, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.command("barter", "View and/or perform a barter. Get your gold ready.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def _barter(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    user = bot.user_cache[ctx.author.id]
    if user.world != "nether":
        await ctx.respond("You need to be in the Nether to use this command!", reply = True, mentions_reply = True)
        return

    async with bot.pool.acquire() as conn:
        barters = await psql.ActiveTrade.get_all_where(conn, where = lambda r: r.type == "barter")
        user_barters = await psql.UserTrade.get_all_where(conn, where = lambda r: r.user_id == ctx.author.id and r.trade_type == "barter")

    embed = helpers.get_default_embed(
        description = f"*Barters will refresh in {humanize.precisedelta(barters[0].next_reset - dt.datetime.now().astimezone(), format = '%0.0f')}*",
        author = ctx.author,
        timestamp = dt.datetime.now().astimezone()
    ).set_author(
        name = "Available Barters",
        icon = bot.get_me().avatar_url
    ).set_thumbnail(bot.get_me().avatar_url)
    
    view = miru.View()
    options = []

    # Bunch of formatting here.
    for i, barter in enumerate(barters):
        user_barter_count: int = 0
        barter_count: int = barter.hard_limit

        # Get the corresponding user trade to this trade.
        if user_barters:
            for u_barter in user_barters:
                if u_barter.trade_id == barter.id:
                    user_barter_count = u_barter.count
                    break

        item = bot.item_cache[barter.item_src]
        src_str = f"{item.emoji} x {barter.amount_src}"
        item = bot.item_cache[barter.item_dest]
        dest_str = f"{item.emoji} x {barter.amount_dest}"
        
        embed.add_field(
            name = f"Barter {i + 1} ({user_barter_count}/{barter_count})",
            value = f"{src_str} ---> {dest_str}",
            inline = True
        )

        if user_barter_count < barter_count:
            options.append(miru.SelectOption(
                label = f"Barter {i + 1}",
                value = str(i + 1)
            ))
    view.add_item(miru.Select(
        options = options,
        placeholder = "Select a barter to perform"
    ))

    # Logically this should be ephemeral, but you can't get an ephemeral message object...
    resp = await ctx.respond(embed = embed, components = view.build())
    msg = await resp.message()
    view.start(msg)

    def is_select_interaction(event: hikari.InteractionCreateEvent):
        if not isinstance(event.interaction, hikari.ComponentInteraction):
            return False
        
        return event.interaction.message.id == msg.id and event.interaction.member.id == ctx.author.id
    
    while True:
        try:
            event = await bot.wait_for(hikari.InteractionCreateEvent, timeout = 120, predicate = is_select_interaction)
            interaction: hikari.ComponentInteraction = event.interaction
            selected = int(interaction.values[0])
            selected_barter = barters[selected - 1]

            if selected_barter.next_reset < dt.datetime.now().astimezone():
                # Maybe edit into an updated barter?
                await msg.edit("This barter menu is expired. Invoke this command again for a list of updated barters.", embed = None, components = None)
                break
            
            # Process trade here.
            async with bot.pool.acquire() as conn:
                user_trade = await psql.UserTrade.get_one(conn, ctx.author.id, selected, "barter")
                if user_trade is None:
                    user_trade = psql.UserTrade(ctx.author.id, selected_barter.id, selected_barter.type, selected_barter.hard_limit, 0)

                if user_trade.count + 1 > user_trade.hard_limit:
                    await ctx.respond("You can't make this barter anymore!", reply = True, mentions_reply = True, 
                        flags = hikari.MessageFlag.EPHEMERAL
                    )
                    continue
                
                inv = await psql.Inventory.get_one(conn, ctx.author.id, selected_barter.item_src)

                if inv is None or inv.amount < selected_barter.amount_src:
                    await ctx.respond("You don't have enough items to make this barter!", reply = True, mentions_reply = True,
                        flags = hikari.MessageFlag.EPHEMERAL
                    )
                    continue

                async with conn.transaction():
                    await psql.Inventory.remove(conn, ctx.author.id, selected_barter.item_src, selected_barter.amount_src)
                    await psql.Inventory.add(conn, ctx.author.id, selected_barter.item_dest, selected_barter.amount_dest)
                    user_trade.count += 1
                    await psql.UserTrade.update(conn, user_trade)

                # Update the menu.
                embed.fields[selected - 1].name = f"Barter {selected} ({user_trade.count}/{selected_barter.hard_limit})"
                if user_trade.count == selected_barter.hard_limit:
                    del options[selected - 1]
                    view.clear_items()
                    view.add_item(miru.Select(
                        options = options,
                        placeholder = "Select a barter to perform"
                    ))
                await msg.edit(embed = embed, components = view.build())
        except asyncio.TimeoutError:
            await msg.edit(components = None)
            break

@plugin.command()
@lightbulb.set_help(dedent('''
    - There is a hard cooldown of 24 hours between each travel, so plan ahead before moving.
    - It is recommended to use the `Slash Command` version of this command.
'''))
@lightbulb.option("world", "The world to travel to.", choices = ("overworld", "nether"))
@lightbulb.command("travel", "Travel to another world.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def travel(ctx: lightbulb.Context):
    world: str = ctx.options.world
    bot: models.MichaelBot = ctx.bot

    if world not in ("overworld", "nether"):
        raise lightbulb.NotEnoughArguments(missing = [ctx.invoked.options["world"]])
    
    user = bot.user_cache[ctx.author.id]
    current = dt.datetime.now().astimezone()
    if user.world == world:
        await ctx.respond("You're currently in this world already!", reply = True, mentions_reply = True)
        return
    if user.last_travel is not None:
        if current - user.last_travel < dt.timedelta(days = 1):
            await ctx.respond(f"You'll need to wait for `{humanize.precisedelta(user.last_travel + dt.timedelta(days = 1) - current, format = '%0.0f')}` before you can travel again.",
                reply = True, mentions_reply = True
            )
            return
    
    async with bot.pool.acquire() as conn:
        ticket = None
        if world == "overworld":
            ticket = await psql.Inventory.get_one(conn, ctx.author.id, "overworld_ticket")
        elif world == "nether":
            ticket = await psql.Inventory.get_one(conn, ctx.author.id, "nether_ticket")
        
        if ticket is None:
            await ctx.respond("You don't have the ticket to travel!", reply = True, mentions_reply = True)
            return
        
        async with conn.transaction():
            await psql.Inventory.remove(conn, ctx.author.id, ticket.item_id)
            user.world = world
            user.last_travel = dt.datetime.now().astimezone()
            await bot.user_cache.update(conn, user)
        
        await ctx.respond(f"Successfully moved to the `{world.capitalize()}`.", reply = True)

def load(bot: models.MichaelBot):
    bot.add_plugin(plugin)
def unload(bot: models.MichaelBot):
    bot.remove_plugin(plugin)
