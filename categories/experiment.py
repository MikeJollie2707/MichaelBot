import discord
from discord.ext import commands

# This category is for testing purpose.
class Experiment(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command
    async def testinitDB(self, ctx):
        pass    
    


def setup(bot):
    bot.add_cog(Experiment(bot))