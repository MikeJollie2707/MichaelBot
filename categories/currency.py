from asyncpg.exceptions import ConfigFileError
import discord
from discord import member
from discord.ext import commands

import datetime
import copy

from categories.utilities.db import DB

class Currency(commands.Cog, command_attrs = {"cooldown_after_parsing" : True}):
    """Commands related to money."""
    def __init__(self, bot):
        self.bot = bot
        self.emoji = '💰'
    
    @commands.command()
    #@commands.cooldown(rate = 1, per = 10.0, type = commands.BucketType.user)
    async def daily(self, ctx):
        '''
        Get an amount of money every 24h.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Send Messages`.
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
                        daily_bonus = member_local_info["streak_daily"] / 10 * 10
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
                    
                    await DB.User.update_money(conn, member_local_info["id"], member_local_info["money"])
                    await DB.User.update_streak(conn, member_local_info["id"], member_local_info["streak_daily"])
                    await DB.User.update_last_daily(conn, member_local_info["id"], member_local_info["last_daily"])
        if too_early:
            await ctx.send("You still have %s left before you can collect your daily." % str(datetime.datetime.utcnow() - member_local_info["last_daily"]))
        else:
            if too_late:
                await ctx.send("You didn't collect your daily for more than 24 hours, so your streak of `x%d` is reset :(" % old_streak)
            
            await ctx.send(f":white_check_mark: You got **${daily_amount}** daily money.\nYour streak: `x{member_local_info['streak_daily']}`.")
            
            if daily_bonus > 0:
                await ctx.send(f"You also receive **${daily_bonus}** for maintaining your streak.")
            

    @commands.command()
    async def addmoney(self, ctx, amount : int, *, member : discord.Member = None):
        '''
        Add a certain amount of money to a user or to yourself.

        The limit range is `[1-25]`.

        *Warning: This command is available only in beta. Once the currency is official, this command will
        no longer available.*

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example:** {prefix}{command_name} 25

        **You need:** None
        **I need:** `Send Messages`.
        '''

        if member is None:
            member = ctx.author
        
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                member_money = await DB.User.get_money(conn, member.id)
                member_money += amount

                await DB.User.update_money(conn, member.id, member_money)
        
        await ctx.send("Added $%d to %s." % (amount, member.name))

    @commands.command()
    async def rmvmoney(self, ctx, amount, *, member: discord.Member = None):
        '''
        Remove a certain amount of money from a user or from yourself.

        The limit range is `[1-25]`. If the removal cause the target's money to drop below 0, it'll be 0.

        *Warning: This command is available only in beta. Once the currency is official, this command will
        no longer available.*

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example:** {prefix}{command_name} 25

        **You need:** None
        **I need:** `Send Messages`.
        '''

        if member is None:
            member = ctx.author
        
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                member_money = await DB.User.get_money(conn, member.id)
                member_money -= amount

                await DB.User.update_money(conn, member.id, member_money)
        
        await ctx.send("Removed $%d from %s." % (amount, member.name))

    @commands.command()
    @commands.cooldown(rate = 1, per = 2.0, type = commands.BucketType.user)
    async def balance(self, ctx):
        '''
        Display the amount of money you currently have.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Cooldown:** 2 seconds per 1 use (user)
        **Example:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Send Messages`.
        '''
        
        member_money = 0
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                member_money = await DB.User.get_money(conn, ctx.author.id)

        await ctx.send("You have $%d." % member_money)
    
    @commands.command()
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
