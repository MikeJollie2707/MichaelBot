import datetime as dt
import random
from textwrap import dedent

import lightbulb
import hikari
import humanize

from categories.econ import loot
from utils import checks, converters, helpers, models, nav, psql

CURRENCY_ICON = "<:emerald:993835688137072670>"

def display_reward(bot: models.MichaelBot, loot_table: dict[str, int], *, emote: bool = False) -> str:
    rewards: list[str] = []
    money: int = 0
    for item_id, amount in loot_table.items():
        if amount > 0:
            if item_id in ("money", "bonus"):
                money += amount
            else:
                item = bot.item_cache.get(item_id)
                if item is not None:
                    if emote:
                        rewards.append(f"{item.emoji} x {amount}")
                    else:
                        rewards.append(f"{amount}x *{item.name}*")
    if money > 0:
        rewards.insert(0, f"{CURRENCY_ICON}{money}")
    return ', '.join(rewards)

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
async def remove_reward(conn, user_id: int, loot_table: dict[str, int]):
    pass

plugin = lightbulb.Plugin("Economy", "Money stuffs", include_datastore = True)
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
@lightbulb.option("item", "Item to craft.", type = converters.ItemConverter, autocomplete = True)
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
        for item_id in recipe:
            recipe[item_id] *= times

    async with bot.pool.acquire() as conn:
        # Try removing the items; if any falls below 0, it fails to craft.
        success: bool = True
        missing: dict[str, int] = {}
        inventories = await psql.Inventory.get_all_where(conn, where = lambda r: r.item_id in recipe and r.user_id == ctx.author.id)
        for inv in inventories:
            inv.amount -= recipe[inv.item_id]
            if inv.amount < 0:
                missing[inv.item_id] = -inv.amount
                success = False
        
        if not success:
            await bot.reset_cooldown(ctx)
            await ctx.respond(f"You're missing the following items: {display_reward(bot, missing)}")
            return
        
        for inv in inventories:
            await psql.Inventory.update(conn, inv)
        await psql.Inventory.add(conn, ctx.author.id, item.id, recipe["result"])
    await ctx.respond(f"Successfully crafted {display_reward(bot, {item.id: recipe['result']})}.", reply = True)
@craft.autocomplete("item")
async def craft_item_autocomplete(option: hikari.AutocompleteInteractionOption, interaction: hikari.AutocompleteInteraction):
    bot: models.MichaelBot = interaction.app

    def match_algorithm(name: str, input_value: str):
        return name.lower().startswith(input_value.lower())

    valid_match = []
    for item in bot.item_cache.values():
        if loot.get_craft_recipe(item.id):
            valid_match.append(item.name)
            if item.aliases:
                for alias in item.aliases:
                    valid_match.append(alias)
    
    if option.value == '':
        return valid_match[:25]
    return [valid_item for valid_item in valid_match if match_algorithm(valid_item, option.value)][:25]

@plugin.command()
@lightbulb.set_help(dedent('''
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
            response += f"You received: {display_reward(bot, daily_loot, emote = True)}\n"

        await ctx.respond(response, reply = True)

@plugin.command()
@lightbulb.set_help(dedent('''
    - It is recommended to use the `Slash Command` version of this command.
'''))
@lightbulb.add_cooldown(length = 10, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.option("equipment", "The equipment to equip.", type = converters.ItemConverter, autocomplete = True)
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
            if item.aliases:
                for alias in item.aliases:
                    equipments.append(alias)
    
    if option.value == '':
        return equipments[:25]
    return [match_equipment for match_equipment in equipments if match_algorithm(match_equipment, option.value)][:25]

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
            await ctx.respond(f"**{ctx.author.username}'s Inventory**\n{display_reward(bot, inv_dict, emote = True)}", reply = True)
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
@lightbulb.command("market", "Public trades")
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
    
    await builder.build().send(ctx.channel_id)

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
    
    await ctx.respond(f"Successfully purchased {display_reward(bot, {item.id : amount}, emote = True)}.", reply = True)

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
    
    await ctx.respond(f"Successfully sold {display_reward(bot, {item.id : amount}, emote = True)} for {CURRENCY_ICON}{profit}.", reply = True)

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
        if item.aliases:
            for alias in item.aliases:
                items.append(alias)
    
    if option.value == '':
        return items[:25]
    return [match_equipment for match_equipment in items if match_algorithm(match_equipment, option.value)][:25]

@plugin.command()
@lightbulb.add_cooldown(length = 300, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.command("mine", "Mine for resources. You'll need a pickaxe equipped.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def mine(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    async with bot.pool.acquire() as conn:
        pickaxe_existed = await psql.Equipment.get_equipment(conn, ctx.author.id, "_pickaxe")
        if not pickaxe_existed:
            await bot.reset_cooldown(ctx)
            await ctx.respond("You don't have a pickaxe!", reply = True, mentions_reply = True)
            return
        
        user = await psql.User.get_one(conn, ctx.author.id)
        assert user is not None
        
        loot_table = loot.get_mine_loot(pickaxe_existed.item_id, user.world)
        if not loot_table:
            await bot.reset_cooldown(ctx)
            await ctx.respond("Oof, I can't seem to generate a working loot table. Might want to report this to dev so they can fix it.", reply = True, mentions_reply = True)
            return
        
        async with conn.transaction():
            await add_reward(conn, ctx.author.id, loot_table)
            await psql.Equipment.update_durability(conn, ctx.author.id, pickaxe_existed.item_id, pickaxe_existed.remain_durability - 1)
    
    await ctx.respond(f"You mined and received {display_reward(bot, loot_table, emote = True)}", reply = True)
    if pickaxe_existed.remain_durability - 1 == 0:
        await ctx.respond(f"Your {bot.item_cache[pickaxe_existed.item_id].emoji} *{bot.item_cache[pickaxe_existed.item_id].name}* broke after the last mining session!", reply = True)

@plugin.command()
@lightbulb.add_cooldown(length = 300, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.command("explore", "Explore the world and get resources by killing monsters. You'll need a sword equipped.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def explore(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    async with bot.pool.acquire() as conn:
        sword_existed = await psql.Equipment.get_equipment(conn, ctx.author.id, "_sword")
        if not sword_existed:
            await bot.reset_cooldown(ctx)
            await ctx.respond("You don't have a sword!", reply = True, mentions_reply = True)
            return
        
        user = await psql.User.get_one(conn, ctx.author.id)
        assert user is not None
        
        loot_table = loot.get_sword_loot(sword_existed.item_id, user.world)
        if not loot_table:
            await bot.reset_cooldown(ctx)
            await ctx.respond("Oof, I can't seem to generate a working loot table. Might want to report this to dev so they can fix it.", reply = True, mentions_reply = True)
            return
        
        async with conn.transaction():
            await add_reward(conn, ctx.author.id, loot_table)
            await psql.Equipment.update_durability(conn, ctx.author.id, sword_existed.item_id, sword_existed.remain_durability - 1)
    
    await ctx.respond(f"You explored and collected {display_reward(bot, loot_table, emote = True)}", reply = True)
    if sword_existed.remain_durability - 1 == 0:
        await ctx.respond(f"Your {bot.item_cache[sword_existed.item_id].emoji} *{bot.item_cache[sword_existed.item_id].name}* broke after the last exploring session!", reply = True)

@plugin.command()
@lightbulb.command("trade", "Periodic trade for rarer items.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def trade(ctx: lightbulb.Context):
    raise NotImplementedError

@plugin.command()
@lightbulb.command("barter", "Barter stuff with gold.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def barter(ctx: lightbulb.Context):
    raise NotImplementedError

def load(bot: models.MichaelBot):
    bot.add_plugin(plugin)
def unload(bot: models.MichaelBot):
    bot.remove_plugin(plugin)
