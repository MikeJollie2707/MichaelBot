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
    
    @commands.command()
    @commands.cooldown(rate = 1, per = 10.0, type = commands.BucketType.user)
    async def daily(self, ctx):
        # Retrieve user info
        # Check if his last daily is <24h
        # If yes then update money and increase streak,
        # otherwise, reset the streak
        fail = False
        member_local_info = {}
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                member_info = await DB.find_member(conn, ctx.author)

                member_local_info = DB.record_to_dict(member_info)

                if member_local_info["last_daily"] is None:
                    member_local_info["last_daily"] = datetime.datetime.utcnow()
                    await conn.execute('''
                        UPDATE dUsers
                        SET last_daily = ($1)
                        WHERE id = ($2);
                    ''', datetime.datetime.utcnow(), ctx.author.id)
                elif datetime.datetime.utcnow() - member_local_info["last_daily"] < datetime.timedelta(seconds = 10.0):
                    fail = True
                
                if not fail:
                    member_local_info["money"] += 100
                    member_local_info["streak_daily"] += 1
                    #await DB.update_member(conn, confirmation)
                    await conn.execute('''
                        UPDATE dUsers
                        SET money = ($1), streak_daily = ($2)
                        WHERE id = ($3);
                    ''', member_local_info["money"], member_local_info["streak_daily"], ctx.author.id)
        if fail:
            await ctx.send("Please wait longer before you can get daily.")
        else:
            await ctx.send("Congrats! You get $100 from your daily. Your streak: %d" % member_local_info["streak_daily"])
            

    @commands.command()
    async def addmoney(self, ctx, amount : int, *, member : discord.Member):
        member_local_info = {}
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                member_info = await DB.find_member(conn, ctx.author)
                member_local_info = DB.record_to_dict(member_info)

                member_local_info["money"] += amount

                await conn.execute('''
                    UPDATE dUsers
                    SET money = ($1)
                    WHERE id = ($2)
                ''', member_local_info["money"], ctx.author.id)
        
        await ctx.send("Added $%d to %s." % (amount, ctx.author.name))

                
    
    @commands.command()
    async def rmvmoney(self, ctx, amount, *, member: discord.Member):
        pass

    @commands.command()
    async def balance(self, ctx):
        member_local_info = {}
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                member_info = await DB.find_member(conn, ctx.author)
                member_local_info = DB.record_to_dict(member_info)

        await ctx.send("You have $%d." % member_local_info["money"])
            

def setup(bot):
    bot.add_cog(Currency(bot))
