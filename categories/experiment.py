import discord
from discord.ext import commands

from categories.utilities.db import DB

# This category is for testing purpose.
class Experiment(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def drop(self, ctx):
        await DB.drop_all_table(self.bot)
    @commands.command()
    async def create(self, ctx):
        await DB.init_db(self.bot)

    


def setup(bot):
    bot.add_cog(Experiment(bot))