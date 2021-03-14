import discord
from discord.ext import commands
from discord.ext.commands.core import command
import humanize

import datetime
import random
import typing # IntelliSense purpose only

import categories.utilities.db as DB
import categories.utilities.facility as Facility
import categories.money.loot as LootTable
from categories.utilities.converters import ItemConverter
from categories.utilities.checks import has_database
from categories.templates.navigate import Pages
from bot import MichaelBot # IntelliSense purpose only

class Currency(commands.Cog, command_attrs = {"cooldown_after_parsing" : True}):
    """Commands related to money."""
    def __init__(self, bot : MichaelBot):
        self.bot = bot
        self.emoji = '💰'
    
    @commands.command()
    @commands.check(has_database)
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    async def daily(self, ctx : commands.Context):
        '''
        Get an amount of money every 24h.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Read Message History`, `Send Messages`.
        '''

        # Retrieve user info
        # Check if his last daily is <24h
        # If yes then update money and increase streak,
        # otherwise, reset the streak

        too_early = False
        too_late = False
        old_streak = 0
        member = {}
        daily_amount = 100
        daily_bonus = 0

        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                member = DB.rec_to_dict(await DB.User.find_user(conn, ctx.author.id))

                if member["last_daily"] is None:
                    member["last_daily"] = datetime.datetime.utcnow()
                elif datetime.datetime.utcnow() - member["last_daily"] < datetime.timedelta(hours = 24.0):
                    too_early = True
                elif datetime.datetime.utcnow() - member["last_daily"] >= datetime.timedelta(hours = 48.0):
                    old_streak = member["streak_daily"]
                    member["streak_daily"] = 0
                    too_late = True
                
                if not too_early:
                    # The daily amount is calculated as followed:
                    # - From streak 0 - 9: 100
                    # - From streak 10 - 99: 120 + (streak / 10) * 10
                    # - From streak 100 - 499: 500 + streak
                    # - From streak 500+: 1500 + streak * 2
                    # Note: The bonus is cap at $2000, so after streak 1000, it is not possible to increase.

                    if member["streak_daily"] < 10:
                        daily_amount = 100
                        daily_bonus = 0
                    elif member["streak_daily"] < 100:
                        daily_amount = 120
                        daily_bonus = int(member["streak_daily"] / 10) * 10
                    elif member["streak_daily"] < 500:
                        daily_amount = 500
                        daily_bonus = member["streak_daily"]
                    else:
                        daily_amount = 1500
                        daily_bonus = member["streak_daily"] * 2
                        if daily_bonus > 2000:
                            daily_bonus = 2000
                    
                    daily_amount += daily_bonus

                    member["last_daily"] = datetime.datetime.utcnow()
                    
                    await DB.User.inc_streak(conn, ctx.author.id)
                    await DB.User.add_money(conn, ctx.author.id, daily_amount)
                    await DB.User.update_last_daily(conn, ctx.author.id, member["last_daily"])

                    loot = LootTable.get_daily_loot(member["streak_daily"] + 1)
                    for key in loot:
                        await DB.Inventory.add(conn, ctx.author.id, key, loot[key])
         
        if too_early:
            remaining_time = datetime.timedelta(hours = 24) - (datetime.datetime.utcnow() - member["last_daily"])
            remaining_str = humanize.precisedelta(remaining_time, "seconds", format = "%0.0f")
            await ctx.reply(f"You still have {remaining_str} left before you can collect your daily.", mention_author = False)
        else:
            msg = ""
            if too_late:
                msg += "You didn't collect your daily for more than 24 hours, so your streak of `x%d` is reset :(\n" % old_streak
            
            if daily_bonus > 0:
                msg += f"You received an extra of **${daily_bonus}** for maintaining your streak.\n"

            msg += LootTable.get_friendly_reward(LootTable.get_daily_loot(member["streak_daily"])) + '\n'
            msg += f":white_check_mark: You got **${daily_amount}** daily money in total.\nYour streak: `x{member['streak_daily'] + 1}`.\n"

            await ctx.reply(msg, mention_author = False)
            
    @commands.command(enabled = False)
    @commands.check(has_database)
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    @commands.cooldown(rate = 1, per = 300.0, type = commands.BucketType.user)
    async def work(self, ctx : commands.Context):
        '''
        Go to work and earn money.

        *Warning: This is an early stage for several commands. This command will be gone when inventory is implemented.*

        **Usage:** <prefix>**{command_name} {command_signature}
        **Cooldown:** 5 minutes per 1 use.
        **Example:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Read Message History`, `Send Messages`.
        '''

        amount = random.randint(15, 25)        
        async with self.bot.pool.acquire() as conn:
            await DB.User.add_money(conn, ctx.author.id, amount)
        
        embed = Facility.get_default_embed(
            description = "You worked and earned $%d." % amount,
            timestamp = datetime.datetime.utcnow()
        )
        await ctx.reply(embed = embed, mention_author = False)

    @commands.command()
    @commands.check(has_database)
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    @commands.cooldown(rate = 1, per = 300.0, type = commands.BucketType.user)
    async def mine(self, ctx : commands.Context):
        '''
        Go mining to earn resources.

        You need to have a pickaxe equipped using the `equip` command.

        **Usage:** <prefix>**{command_name}**
        **Cooldown:** 5 minutes per 1 use (user).
        **Example:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Read Message History`, `Send Messages`.
        '''

        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                current_pick = await DB.Inventory.find_equip(conn, "pickaxe", ctx.author.id)
                if current_pick is None:
                    await ctx.reply("You have no pickaxe equip.")
                    return
                
                loot = LootTable.get_mine_loot(current_pick["item_id"])
                lower_bound = 0
                upper_bound = 0
                final_reward = {}
                for i in range(0, loot["rolls"]):
                    for reward in loot:
                        if reward != "rolls":
                            if reward not in final_reward:
                                final_reward[reward] = 0
                            upper_bound += loot[reward]
                            chance = random.random()
                            if chance >= lower_bound and chance < upper_bound:
                                final_reward[reward] += 1
                            
                            lower_bound = upper_bound
                    lower_bound = 0
                    upper_bound = 0
                
                message = LootTable.get_friendly_reward(final_reward)
                any_reward = False
                for reward in final_reward:
                    if final_reward[reward] != 0:
                        any_reward = True
                        await DB.Inventory.add(conn, ctx.author.id, reward, final_reward[reward])
                
                if any_reward:
                    await ctx.reply("You go mining and get %s." % message, mention_author = False)
                else:
                    await ctx.reply("You go mining, but you didn't feel well so you left with nothing.", mention_author = False)
    
    @commands.command()
    @commands.check(has_database)
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    @commands.cooldown(rate = 1, per = 300.0, type = commands.BucketType.user)
    async def chop(self, ctx : commands.Context):
        '''
        Chop some trees.

        The majority of reward is log, although you can also find some other things with a better axe.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Cooldown:** 5 minutes per 1 use (user).
        **Example:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Read Message History`, `Send Messages`.
        '''

        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                current_axe = await DB.Inventory.find_equip(conn, "axe", ctx.author.id)
                if current_axe is None:
                    await ctx.reply("You have no axe equip.")
                    return
                
                loot = LootTable.get_chop_loot(current_axe["item_id"])
                lower_bound = 0
                upper_bound = 0
                final_reward = {}
                for i in range(0, loot["rolls"]):
                    for reward in loot:
                        if reward != "rolls":
                            if reward not in final_reward:
                                final_reward[reward] = 0
                            upper_bound += loot[reward]
                            chance = random.random()
                            if chance >= lower_bound and chance < upper_bound:
                                final_reward[reward] += 1
                            
                            lower_bound = upper_bound
                    lower_bound = 0
                    upper_bound = 0
                
                message = LootTable.get_friendly_reward(final_reward)
                any_reward = False
                for reward in final_reward:
                    if final_reward[reward] != 0:
                        any_reward = True
                        await DB.Inventory.add(conn, ctx.author.id, reward, final_reward[reward])

                if any_reward:               
                    await ctx.reply("You go chopping trees and get %s." % message, mention_author = False)
                else:
                    await ctx.reply("You go chopping trees, but no tree was found :(", mention_author = False)

    @commands.group(invoke_without_command = True)
    @commands.check(has_database)
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    async def craft(self, ctx : commands.Context, n : typing.Optional[int] = 1, *, item : ItemConverter):
        '''
        Perform a craft `n` times.
        This will give you `n * <quantity>` items, with `<quantity>` is the `You gain` section in `craft recipe`.

        Craft wisely!

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example 1:** {prefix}{command_name} 2 stick
        **Example 2:** {prefix}{command_name} wooden pickaxe

        **You need:** None.
        **I need:** `Read Message History`, `Send Messages`.
        '''

        if ctx.invoked_subcommand is None:
            if n <= 0:
                n = 1
            async with self.bot.pool.acquire() as conn:
                async with conn.transaction():
                    exist = await DB.Items.get_item(conn, item)
                    if exist is None:
                        await ctx.reply("This item doesn't exist. Please check `craft recipe` for possible crafting items.", mention_author = False)
                        return
                    
                    ingredient = LootTable.get_craft_ingredient(item)
                    if ingredient is None:
                        await ctx.reply("This item isn't craftable. Please check `craft recipe` for possible crafting items.", mention_author = False)
                        return
                    
                    missing_items = []
                    for key in ingredient:
                        if key != "quantity":
                            result = await DB.Inventory.remove(conn, ctx.author.id, key, n * ingredient[key])
                            if result is not None:
                                missing_items.append(f"**{LootTable.get_friendly_name(key)}**")
                        
                    if len(missing_items) == 0:
                        official_name = LootTable.get_friendly_name(item)
                        await DB.Inventory.add(conn, ctx.author.id, item, n * ingredient["quantity"])
                        await ctx.reply(f"Crafted {n * ingredient[key]}x **{official_name}** successfully.", mention_author = False)
                    else:
                        text = Facility.striplist(missing_items)
                        await ctx.reply("Missing the following items: %s" % text, mention_author = False)

    @craft.command()
    @commands.check(has_database)
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    async def recipe(self, ctx : commands.Context, *, item : ItemConverter = None):
        '''
        Recipe for an item or all the recipes.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example 1:** {prefix}{command_name} wood
        **Example 2:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Read Message History`, `Send Messages`.
        '''

        recipe = LootTable.get_craft_ingredient(item)

        if item is None:
            MAX_ITEMS = 4
            cnt = 0
            page = Pages()
            embed = None
            for key in recipe:
                if cnt == 0:
                    embed = Facility.get_default_embed(
                        title = "All crafting recipes",
                        timestamp = datetime.datetime.utcnow(),
                        author = ctx.author
                    )
                
                friendly_name = LootTable.get_friendly_name(key)
                outp = recipe[key].pop("quantity", None)
                embed.add_field(
                    name = LootTable.acapitalize(friendly_name),
                    value = "**Input:** %s\n**Output:** %s\n" % (LootTable.get_friendly_reward(recipe[key]), LootTable.get_friendly_reward({key : outp})),
                    inline = False
                )

                cnt += 1
                if cnt == MAX_ITEMS:
                    page.add_page(embed)
                    embed = None
                    cnt = 0
            # If the amount of items doesn't reach MAX_ITEMS.
            if embed is not None:
                page.add_page(embed)
            
            await page.event(ctx, interupt = False) 
        elif recipe is not None:
            friendly_name = LootTable.get_friendly_name(item)
            outp = recipe.pop("quantity", None)
            embed = Facility.get_default_embed(
                title = "%s's crafting recipe" % LootTable.acapitalize(friendly_name),
                timestamp = datetime.datetime.utcnow(),
                author = ctx.author
            ).add_field(
                name = "You lose:",
                value = LootTable.get_friendly_reward(recipe),
                inline = False
            ).add_field(
                name = "You gain:",
                value = LootTable.get_friendly_reward({item : outp}),
                inline = False
            )

            await ctx.reply(embed = embed, mention_author = False)
        else:
            await ctx.reply("This item doesn't exist.", mention_author = False)

    @commands.command(aliases = ['inv'])
    @commands.check(has_database)
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    @commands.cooldown(rate = 1, per = 5.0, type = commands.BucketType.user)
    async def inventory(self, ctx : commands.Context):
        '''
        View your inventory. Sorted by amount.

        **Aliases:** `inv`.
        **Usage:** <prefix>**{command_name}** {command_signature}
        **Cooldown:** 5 seconds per 1 use (user).
        **Example:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Read Message History`, `Send Messages`.
        '''

        async with self.bot.pool.acquire() as conn:
            inventory = await DB.Inventory.get_whole_inventory(conn, ctx.author.id)
            if inventory is None:
                await ctx.reply("*Insert empty inventory here*", mention_author = False)
                return
            
            def _on_amount(slot):
                return -slot["quantity"]
            inventory.sort(key = _on_amount)

            inventory_dict = {}
            for slot in inventory:
                inventory_dict[slot["item_id"]] = slot["quantity"]
            await ctx.reply(LootTable.get_friendly_reward(inventory_dict), mention_author = False)

    @commands.command(aliases = ['adv'])
    @commands.check(has_database)
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    @commands.cooldown(rate = 1, per = 5.0, type = commands.BucketType.user)
    async def adventure(self, ctx : commands.Context):
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                current_sword = await DB.Inventory.find_equip(conn, "sword", ctx.author.id)
                if current_sword is None:
                    await ctx.reply("You have no sword equip.")
                    return
                
                loot = LootTable.get_adventure_loot(current_sword["item_id"])
                lower_bound = 0
                upper_bound = 0
                final_reward = {}
                for i in range(0, loot["rolls"]):
                    for reward in loot:
                        if reward != "rolls":
                            if reward not in final_reward:
                                final_reward[reward] = 0
                            upper_bound += loot[reward]
                            chance = random.random()
                            if chance >= lower_bound and chance < upper_bound:
                                final_reward[reward] += 1
                            
                            lower_bound = upper_bound
                    lower_bound = 0
                    upper_bound = 0
                
                message = LootTable.get_friendly_reward(final_reward)
                any_reward = False
                for reward in final_reward:
                    if final_reward[reward] != 0:
                        any_reward = True
                        await DB.Inventory.add(conn, ctx.author.id, reward, final_reward[reward])
                
                if any_reward:
                    await ctx.reply("You go on an adventure and get %s." % message, mention_author = False)
                else:
                    await ctx.reply("You go on an adventure but didn't get anything :(", mention_author = False)

    @commands.command(hidden = True)
    async def trade(self, ctx : commands.Context):
        pass

    @commands.command()
    @commands.check(has_database)
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    @commands.cooldown(rate = 1, per = 5.0, type = commands.BucketType.user)
    async def equip(self, ctx : commands.Context, *, tool_name : ItemConverter):
        '''
        Equip either a pickaxe, an axe, a sword, or a fishing rod.

        `tool name` must be an item existed in your inventory.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example:** {prefix}{command_name} wooden pickaxe
        '''
        
        if "_pickaxe" not in tool_name and "_axe" not in tool_name and "_sword" not in tool_name and "_rod" not in tool_name:
            await ctx.reply(f"You can't equip this!", mention_author = False)
            return
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                exist = await DB.Items.get_item(conn, tool_name)
                if exist is None:
                    await ctx.reply(f"This tool does not exist.", mention_author = False)
                    return
                
                tool_type = ""
                if "_pickaxe" in tool_name:
                    tool_type = "pickaxe"
                elif "_axe" in tool_name:
                    tool_type = "axe"
                elif "_sword" in tool_name:
                    tool_type = "sword"
                elif "_rod" in tool_name:
                    tool_type = "rod"
                
                has_equipped = await DB.Inventory.find_equip(conn, tool_type, ctx.author.id)
                if has_equipped is not None:
                    await DB.Inventory.unequip_tool(conn, ctx.author.id, has_equipped["item_id"])
                await DB.Inventory.equip_tool(conn, ctx.author.id, tool_name)
                official_name = await DB.Items.get_official_name(conn, tool_name)
                await ctx.reply(f"Added {official_name} to main equipments.", mention_author = False)

    @commands.command(aliases = ['bal'])
    @commands.check(has_database)
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    @commands.cooldown(rate = 1, per = 2.0, type = commands.BucketType.user)
    async def balance(self, ctx : commands.Context):
        '''
        Display the amount of money you currently have.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Cooldown:** 2 seconds per 1 use (user)
        **Example:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Read Message History`, `Send Messages`.
        '''
        
        member_money = 0
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                member_money = await DB.User.get_money(conn, ctx.author.id)

        await ctx.reply("You have $%d." % member_money, mention_author = False)
    
    @commands.command(aliases = ['lb'], hidden = True)
    @commands.check(has_database)
    @commands.cooldown(rate = 1, per = 5.0, type = commands.BucketType.member)
    async def topmoney(self, ctx : commands.Context, local__global = "local"):
        '''
        Show the top 10 users with the most amount of money.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Cooldown:** 5 seconds per 1 use (member)
        **Example 1:** {prefix}{command_name} global
        **Example 2:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Send Messages`.
        '''
        pass
            

def setup(bot : MichaelBot):
    bot.add_cog(Currency(bot))
