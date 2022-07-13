import datetime as dt
import random
from textwrap import dedent

import lightbulb
import hikari
import humanize

from categories.econ import loot
from utils import checks, helpers, models, psql
from utils.nav import confirm, navigator

CURRENCY_ICON = "<:emerald:993835688137072670>"

def display_reward(bot: models.MichaelBot, loot_table: dict[str, int], *, emote: bool = False) -> str:
    rewards: list = []
    for item_id, amount in loot_table.items():
        item_cache = bot.item_cache.get(item_id)
        if item_cache is not None:
            item = item_cache.item_module
            if emote:
                rewards.append(f"{item['emoji']} x {amount}")
            else:
                rewards.append(f"{amount}x *{item['name']}*")
    return ', '.join(rewards)

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
    
    async with bot.pool.acquire() as conn:
        user = await psql.User.get_one(conn, ctx.author.id)
        if user.balance < money:
            await ctx.respond(f"You don't have enough money to bet {CURRENCY_ICON}{money}!", reply = True, mentions_reply = True)
            return
        if user.balance == money:
            confirm_menu = confirm.ConfirmView(timeout = 10)
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
            await psql.User.add_money(conn, ctx.author.id, money)
            user.balance += money
        else:
            rsp += f"And it is incorrect! The number is `{actual_num}`. Better luck next time!\n"
            await psql.User.remove_money(conn, ctx.author.id, money)
            user.balance -= money
        
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
        await psql.User.add_money(conn, ctx.author.id, min(500, max(1, ctx.options.amount)))
    await ctx.respond(f"Added {CURRENCY_ICON}{ctx.options.amount}.")

@plugin.command()
@lightbulb.set_help(dedent('''
    - It is recommended to use the `Slash Command` version of this command.
'''))
@lightbulb.option("times", "How many times this command is executed. Default to 1.", type = int, min_value = 1, max_value = 100, default = 1)
@lightbulb.option("item", "Item to craft.", autocomplete = True)
@lightbulb.command("craft", "Craft various items.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def craft(ctx: lightbulb.Context):
    times: int = max(1, min(100, ctx.options.times))
    bot: models.MichaelBot = ctx.bot

    async with bot.pool.acquire() as conn:
        item = await psql.Item.get_by_name(conn, ctx.options.item)
        if item is None:
            await ctx.respond("This item doesn't exist!", reply = True, mentions_reply = True)
            return
        
        recipe = loot.get_craft_recipe(item.id)
        if not recipe:
            await ctx.respond(f"Item *{item.name}* cannot be crafted.", reply = True, mentions_reply = True)
            return
        
        success: bool = True
        missing: dict[str, int] = {}
        inventories = await psql.Inventory.get_all_where(conn, where = lambda r: r.item_id in recipe and r.user_id == ctx.author.id)
        for inv in inventories:
            inv.amount -= recipe[inv.item_id] * times
            if inv.amount < 0:
                missing[inv.item_id] = -inv.amount
                success = False
        
        if not success:
            await ctx.respond(f"You're missing the following items: {display_reward(bot, missing)}")
            return
        
        for inv in inventories:
            await psql.Inventory.sync(conn, inv)
        await psql.Inventory.add(conn, ctx.author.id, item.id, recipe["result"] * times)
    await ctx.respond(f"Successfully crafted {display_reward(bot, {item.id: recipe['result'] * times})}.", reply = True)
@craft.autocomplete("item")
async def craft_item_autocomplete(option: hikari.AutocompleteInteractionOption, interaction: hikari.AutocompleteInteraction):
    bot: models.MichaelBot = interaction.app

    def match_algorithm(name: str, input_value: str):
        return name.lower().startswith(input_value.lower())

    valid_match = []
    for item_id, cache in bot.item_cache.items():
        if loot.get_craft_recipe(item_id):
            valid_match.append(cache.item_module["name"])
            # Cache might not load aliases if the json don't specify it.
            if cache.item_module.get("aliases"):
                for alias in cache.item_module["aliases"]:
                    valid_match.append(alias)
    
    if option.value == '':
        return valid_match[:25]
    return [valid_item for valid_item in valid_match if match_algorithm(valid_item, option.value)][:25]

@plugin.command()
@lightbulb.set_help(dedent('''
    - The higher the daily streak, the better your reward will be.
    - If you don't collect your daily within 48 hours since the last time you collect, your streak will be reset to 1.
    - This command has a hard cooldown. This means the only way to reset is to tamper with the bot's database.
'''))
@lightbulb.command("daily", "Receive rewards everyday. Don't miss it though!")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def daily(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    response: str = ""
    async with bot.pool.acquire() as conn:
        existed = await psql.User.get_one(conn, ctx.author.id)
        
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
            
            await psql.User.update_streak(conn, existed.id, existed.daily_streak)
            await psql.User.update_column(conn, existed.id, "last_daily", now)

            daily_loot = loot.get_daily_loot(existed.daily_streak)
            money: int = 0
            for item_id, amount in daily_loot.items():
                if item_id in ("money", "bonus"):
                    money += amount
                    if item_id == "bonus":
                        response += f"You got an extra {CURRENCY_ICON}{amount}!\n"
                    else:
                        response += f"You received {CURRENCY_ICON}{amount}.\n"
                else:
                    await psql.Inventory.add(conn, ctx.author.id, item_id, amount)
            if money > 0:
                await psql.User.add_money(conn, ctx.author.id, money)
            response += f"You received: {display_reward(bot, daily_loot, emote = True)}\n"

        await ctx.respond(response, reply = True)

@plugin.command()
@lightbulb.set_help(dedent('''
    - It is recommended to use the `Slash Command` version of this command.
'''))
@lightbulb.option("equipment", "The equipment to equip.", autocomplete = True)
@lightbulb.command("equip", "Equip some tools boi. Get to work!")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def equip(ctx: lightbulb.Context):
    equipment = ctx.options.equipment
    bot: models.MichaelBot = ctx.bot

    async with bot.pool.acquire() as conn:
        item = await psql.Item.get_by_name(conn, equipment)
        if not item:
            await ctx.respond("This equipment doesn't exist!", reply = True, mentions_reply = True)
            return
        if not psql.Equipment.is_equipment(item.id):
            await ctx.respond("This is not an equipment!", reply = True, mentions_reply = True)
            return
        
        inv = await psql.Inventory.get_one(conn, ctx.author.id, item.id)
        if not inv:
            await ctx.respond("You don't have this equipment in your inventory!", reply = True, mentions_reply = True)
            return
        
        # Check for equipment type conflict.
        existed: psql.Equipment = await psql.Equipment.get_equipment(conn, ctx.author.id, psql.Equipment.get_equipment_type(item.id))
        if not existed:
            await psql.Equipment.transfer_from_inventory(conn, inv)
            await ctx.respond(f"Equipped *{item.name}*.", reply = True)
        else:
            await ctx.respond(f"You already have *{bot.item_cache[existed.item_id]['name']}* equipped!", reply = True, mentions_reply = True)
@equip.autocomplete("equipment")
async def equip_equipment_autocomplete(option: hikari.AutocompleteInteractionOption, interaction: hikari.AutocompleteInteraction):
    bot: models.MichaelBot = interaction.app

    def match_algorithm(name: str, input_value: str):
        return name.lower().startswith(input_value.lower())

    equipments = []
    for item_id, item_cache in bot.item_cache.items():
        if psql.Equipment.is_equipment(item_id):
            equipments.append(item_cache.item_module["name"])
            if item_cache.item_module.get("aliases"):
                for alias in item_cache.item_module["aliases"]:
                    equipments.append(alias)
    
    if option.value == '':
        return equipments[:25]
    return [match_equipment for match_equipment in equipments if match_algorithm(match_equipment, option.value)][:25]

@plugin.command()
@lightbulb.option("view_option", "Options to view inventory.", choices = ("compact", "full", "value"), default = "compact")
@lightbulb.command("inventory", "View inventory boi.", aliases = ["inv"])
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def inventory(ctx: lightbulb.Context):
    view_option = ctx.options.view_option
    bot: models.MichaelBot = ctx.bot
    
    async with bot.pool.acquire() as conn:
        inventories = await psql.Inventory.get_all(conn)
        if not inventories:
            await ctx.respond("*Cricket noises*", reply = True)
            return
        
        if view_option == "compact":
            inv_dict: dict[str, int] = {}
            for inv in inventories:
                inv_dict[inv.item_id] = inv.amount
            await ctx.respond(f"**{ctx.author.username}'s Inventory**\n{display_reward(bot, inv_dict, emote = True)}", reply = True)
        elif view_option == "full":
            page = navigator.ItemListBuilder(inventories, 5)
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
                embed.add_field(
                    name = f"{inv.amount}x {inv.emoji} {inv.name}",
                    value = f"*{inv.description}*\nTotal value: {CURRENCY_ICON}{inv.sell_price * inv.amount}"
                )
            
            await navigator.run_view(page.build(), ctx)
        elif view_option == "value":
            value = 0
            for inv in inventories:
                value += inv.sell_price * inv.amount
            await ctx.respond(f"If you sell all your items in your inventory, you'll get: {CURRENCY_ICON}{value}.", reply = True)

@plugin.command()
@lightbulb.command("market", "Public trades")
@lightbulb.implements(lightbulb.PrefixCommandGroup, lightbulb.SlashCommandGroup)
async def market(ctx: lightbulb.Context):
    raise NotImplementedError

@plugin.command()
@lightbulb.command("mine", "Mine something cool.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def mine(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    async with bot.pool.acquire() as conn:
        pickaxe_existed = await psql.Equipment.get_equipment(conn, ctx.author.id, "_pickaxe")
        if not pickaxe_existed:
            await ctx.respond("You don't have a pickaxe!", reply = True, mentions_reply = True)
            return
        
        user = await psql.User.get_one(conn, ctx.author.id)
        assert user is not None
        
        loot_table = loot.get_mine_loot(pickaxe_existed.item_id, user.world)
        if not loot_table:
            await ctx.respond("Oof, I can't seem to generate a working loot table. Might want to report this to dev so they can fix it.", reply = True, mentions_reply = True)
            return
        
        async with conn.transaction():
            for item_id, amount in loot_table.items():
                await psql.Inventory.add(conn, ctx.author.id, item_id, amount)
            
            await psql.Equipment.update_durability(conn, ctx.author.id, pickaxe_existed.item_id, pickaxe_existed.remain_durability - 1)
    
    await ctx.respond(f"You mined and received {display_reward(bot, loot_table, emote = True)}", reply = True)
    if pickaxe_existed.remain_durability - 1 == 0:
        await ctx.respond(f"Your {bot.item_cache[pickaxe_existed.item_id].item_module['emoji']} *{bot.item_cache[pickaxe_existed.item_id].item_module['name']}* broke after the last mining session!")

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
