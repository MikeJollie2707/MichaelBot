import discord
from discord.ext import commands

from categories.utilities.db import DB

class Currency(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def daily(self, ctx):
        pass

    @commands.command()
    async def addmoney(self, ctx, amount, *, member : discord.Member):
        pass
    
    @commands.command()
    async def rmvmoney(self, ctx, amount, *, member: discord.Member):
        pass

def setup(bot):
    bot.add_cog(Currency(bot))
