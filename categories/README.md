# Cog structure

```py
import discord
from discord.ext import commands

# Import more Python craps here
import datetime # Must have if you plan to send an embed

# Import your craps here
from categories.utilities import methods # Must have

class Cog(commands.Cog):
    '''Description of the cog'''
    def __init__(self, bot):
        self.bot = bot
        self.emoji = ''
    
    @commands.command()
    async def command(self, ctx):
    '''
    Description
    Notes
    
    **Aliases:** `alias`, `aliases`.
    **Usage:** <prefix>{command_name} <param>
    **Cooldown:**
    **Examples:** {prefix}{command_name}

    **You need:**
    **I need:**
    '''
    # Implementation here

    # More commands here

def setup(bot):
    bot.add_cog(Cog(bot))
```
