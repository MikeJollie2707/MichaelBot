from asyncpg.exceptions import ConfigFileError
import discord
from discord import member
from discord.ext import commands

import datetime
import copy

from categories.utilities.db import DB

class Currency(commands.Cog, command_attrs = {"cooldown_after_parsing" : True, "hidden" : True}):
    def __init__(self, bot):
        self.bot = bot
        self.emoji = '💲'
    
    @commands.command()
    @commands.cooldown(rate = 1, per = 10.0, type = commands.BucketType.user)
    async def daily(self, ctx):
        '''
        Get an amount of money every 24h.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Cooldown:** 10 seconds per 1 use (user)
        **Example:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Send Messages`.
        '''

        # Retrieve user info
        # Check if his last daily is <24h
        # If yes then update money and increase streak,
        # otherwise, reset the streak
        fail = False
        member_local_info = {}
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                member_local_info = DB.record_to_dict(await DB.find_member(conn, ctx.author))

                if member_local_info["last_daily"] is None:
                    member_local_info["last_daily"] = datetime.datetime.utcnow()
                elif datetime.datetime.utcnow() - member_local_info["last_daily"] < datetime.timedelta(hours = 24.0):
                    fail = True
                
                if not fail:
                    member_local_info["money"] += 100
                    member_local_info["streak_daily"] += 1
                    
                    await DB.Member.update_money(conn, member_local_info["id"], member_local_info["money"])
                    await DB.Member.update_streak(conn, member_local_info["id"], member_local_info["streak_daily"])
                    await DB.Member.update_last_daily(conn, member_local_info["id"], member_local_info["last_daily"])
        if fail:
            await ctx.send("You still have %s left before you can collect your daily." % str(member_local_info["last_daily"]))
        else:
            await ctx.send("Congrats! You get $100 from your daily. Your streak: %d" % member_local_info["streak_daily"])
            

    @commands.command()
    async def addmoney(self, ctx, amount : int, *, member : discord.Member = None):
        if member is None:
            member = ctx.author
        
        member_local_info = {}
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                member_info = await DB.find_member(conn, member)
                member_local_info = DB.record_to_dict(member_info)

                member_local_info["money"] += amount

                await DB.Member.update_money(conn, member.id, member_local_info["money"])
        
        await ctx.send("Added $%d to %s." % (amount, member.name))

                
    
    @commands.command()
    async def rmvmoney(self, ctx, amount, *, member: discord.Member):
        pass

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
        
        member_local_info = {}
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                member_info = await DB.find_member(conn, ctx.author)
                member_local_info = DB.record_to_dict(member_info)

        await ctx.send("You have $%d." % member_local_info["money"])
    
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
