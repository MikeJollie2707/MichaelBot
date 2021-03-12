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
        first_time = False
        old_streak = 0
        member_local_info = {}
        daily_amount = 100
        daily_bonus = 0

        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                member_local_info = dict(await DB.User.find_user(conn, ctx.author.id))

                if member_local_info["last_daily"] is None:
                    member_local_info["last_daily"] = datetime.datetime.utcnow()
                    first_time = True
                elif datetime.datetime.utcnow() - member_local_info["last_daily"] < datetime.timedelta(hours = 24.0):
                    too_early = True
                elif datetime.datetime.utcnow() - member_local_info["last_daily"] >= datetime.timedelta(hours = 48.0):
                    old_streak = member_local_info["streak_daily"]
                    member_local_info["streak_daily"] = 0
                    too_late = True
                
                if not too_early:
                    # The daily amount is calculated as followed:
                    # - From streak 0 - 9: 100
                    # - From streak 10 - 99: 120 + (streak / 10) * 10
                    # - From streak 100 - 499: 500 + streak
                    # - From streak 500+: 1500 + streak * 2
                    # Note: The bonus is cap at $2000, so after streak 1000, it is not possible to increase.

                    if member_local_info["streak_daily"] < 10:
                        daily_amount = 100
                        daily_bonus = 0
                    elif member_local_info["streak_daily"] < 100:
                        daily_amount = 120

                        # This is rounded down to the tenth.
                        daily_bonus = int(member_local_info["streak_daily"] / 10) * 10
                    elif member_local_info["streak_daily"] < 500:
                        daily_amount = 500
                        daily_bonus = member_local_info["streak_daily"]
                    else:
                        daily_amount = 1500
                        daily_bonus = member_local_info["streak_daily"] * 2
                        if daily_bonus > 2000:
                            daily_bonus = 2000
                    
                    daily_amount += daily_bonus
                    
                    member_local_info["money"] += daily_amount
                    member_local_info["streak_daily"] += 1
                    member_local_info["last_daily"] = datetime.datetime.utcnow()
                    
                    await DB.User.bulk_update(conn, ctx.author.id, {
                        "money" : member_local_info["money"],
                        "streak_daily" : member_local_info["streak_daily"],
                        "last_daily" : member_local_info["last_daily"]
                    })

                    if first_time:
                        await DB.Inventory.add(conn, ctx.author.id, "log", 4)
        if too_early:
            remaining_time = datetime.timedelta(hours = 24) - (datetime.datetime.utcnow() - member_local_info["last_daily"])
            remaining_str = humanize.precisedelta(remaining_time, "seconds", format = "%0.0f")
            await ctx.reply(f"You still have {remaining_str} left before you can collect your daily.", mention_author = False)
        else:
            msg = ""
            if too_late:
                msg += "You didn't collect your daily for more than 24 hours, so your streak of `x%d` is reset :(\n" % old_streak
            
            if daily_bonus > 0:
                msg += f"You received an extra of **${daily_bonus}** for maintaining your streak.\n"
            if first_time:
                msg += f"You received 4 logs for your first daily ever!"

            msg += f":white_check_mark: You got **${daily_amount}** daily money in total.\nYour streak: `x{member_local_info['streak_daily']}`.\n"

            
            
            await ctx.reply(msg, mention_author = False)
            
    @commands.command(enable = False)
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
                current_pick = await DB.Inventory.get_equip_pickaxe(conn, ctx.author.id)
                if current_pick is None:
                    await ctx.reply("You have no pickaxe equip.")
                
                loot = LootTable.get_mine_loot(current_pick)
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
                
                message = ""
                for reward in final_reward:
                    if final_reward[reward] != 0:
                        message += f"{final_reward[reward]}x **{reward}**, "
                        await DB.Inventory.add(conn, ctx.author.id, reward, final_reward[reward])
                message = message[:-2]
                
                await ctx.reply("You go some mining and get %s." % message, mention_author = False)

    @commands.command()
    @commands.check(has_database)
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    async def craft(self, ctx : commands.Context, n : typing.Optional[int] = 1, *, item : ItemConverter):
        '''
        Craft items `n` times.

        Note that many crafting recipes can result in many items.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example 1:** {prefix}{command_name} 2 stick
        **Example 2:** {prefix}{command_name} wooden pickaxe
        '''
        if n <= 0:
            n = 1
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                exist = await DB.Items.get_item(conn, item)
                if exist is None:
                    await ctx.reply("This item doesn't exist. Please check `craft info` for possible crafting items.", mention_author = False)
                    return
                
                ingredient = LootTable.get_craft_ingredient(item)
                if ingredient is None:
                    await ctx.reply("This item is not craftable. Please check `craft info` for possible crafting items.", mention_author = False)
                    return
                
                missing_items = []
                for key in ingredient:
                    if key != "quantity":
                        result = await DB.Inventory.remove(conn, ctx.author.id, key, n * ingredient[key])
                        if result is not None:
                            missing_items.append(await DB.Items.get_official_name(conn, key))
                    
                if len(missing_items) == 0:
                    official_name = await DB.Items.get_official_name(conn, item)
                    await DB.Inventory.add(conn, ctx.author.id, item, n * ingredient["quantity"])
                    await ctx.reply(f"Crafted {n * ingredient[key]}x **{official_name}** successfully.", mention_author = False)
                else:
                    text = Facility.striplist(missing_items)
                    await ctx.reply("Missing the following items: %s" % text, mention_author = False)
                
    @commands.command()
    @commands.check(has_database)
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    #@commands.cooldown(rate = 1, per = 300.0, type = commands.BucketType.user)
    async def equip(self, ctx : commands.Context, *, tool_name : ItemConverter):
        '''
        Equip either a pickaxe, an axe, a sword, or a fishing rod.

        *Currently only support pickaxe*

        `tool name` must be an item existed in your inventory.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example:** {prefix}{command_name} wooden pickaxe
        '''
        if "_pickaxe" not in tool_name:
            await ctx.reply(f"This is not a pickaxe.", mention_author = False)
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                exist = await DB.Items.get_item(conn, tool_name)
                if exist is None:
                    await ctx.reply(f"This pickaxe does not exist.", mention_author = False)
                
                await DB.Inventory.equip_pickaxe(conn, ctx.author.id, tool_name)
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
