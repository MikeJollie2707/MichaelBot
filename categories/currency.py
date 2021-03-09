from asyncpg.exceptions import ConfigFileError
import discord
from discord import member
from discord.ext import commands
import humanize

import datetime
import random

import categories.utilities.db as DB
import categories.utilities.facility as Facility
from categories.utilities.checks import has_database

class Currency(commands.Cog, command_attrs = {"cooldown_after_parsing" : True}):
    """Commands related to money."""
    def __init__(self, bot):
        self.bot = bot
        self.emoji = '💰'
    
    @commands.command()
    @commands.check(has_database)
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    async def daily(self, ctx):
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
        member_local_info = {}
        daily_amount = 100
        daily_bonus = 0

        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                member_local_info = DB.record_to_dict(await DB.User.find_user(conn, ctx.author.id))

                if member_local_info["last_daily"] is None:
                    member_local_info["last_daily"] = datetime.datetime.utcnow()
                elif datetime.datetime.utcnow() - member_local_info["last_daily"] < datetime.timedelta(hours = 24.0):
                    too_early = True
                elif datetime.datetime.utcnow() - member_local_info["last_daily"] >= datetime.timedelta(hours = 48.0):
                    old_streak = member_local_info["streak_daily"]
                    member_local_info["streak_daily"] = 0
                    too_late = True
                
                if not too_early:
                    # The daily amount is calculated as followed:
                    # - From streak 0 - 9: 100
                    # - From streak 10 - 99: 500 + (streak / 10) * 10
                    # - From streak 100 - 499: 1000 + streak
                    # - From streak 500+: 1500 + streak * 2
                    # Note: The bonus is cap at $2000, so after streak 1000, it is not possible to increase.

                    if member_local_info["streak_daily"] < 10:
                        daily_amount = 100
                        daily_bonus = 0
                    elif member_local_info["streak_daily"] < 100:
                        daily_amount = 500

                        # This is rounded down to the tenth.
                        daily_bonus = int(member_local_info["streak_daily"] / 10) * 10
                    elif member_local_info["streak_daily"] < 500:
                        daily_amount = 1000
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

            msg += f":white_check_mark: You got **${daily_amount}** daily money.\nYour streak: `x{member_local_info['streak_daily']}`.\n"
            
            await ctx.reply(msg, mention_author = False)
            
    @commands.command()
    @commands.check(has_database)
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    @commands.cooldown(rate = 1, per = 300.0, type = commands.BucketType.user)
    async def work(self, ctx):
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

    @commands.command(aliases = ['bal'])
    @commands.check(has_database)
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    @commands.cooldown(rate = 1, per = 2.0, type = commands.BucketType.user)
    async def balance(self, ctx):
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
    async def topmoney(self, ctx, local__global = "local"):
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
            

def setup(bot):
    bot.add_cog(Currency(bot))
