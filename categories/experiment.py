import asyncio
import discord
from discord.ext import commands

import datetime

import categories.utilities.facility as Facility

# This category is for testing purpose.
class Experiment(commands.Cog, command_attrs = {"hidden" : True}):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def create_role(self, ctx):
        guild = ctx.guild
        role = await guild.create_role(
            name = "Eh",
            permissions = discord.Permissions(
                send_messages = False,
                send_tts_messages = False,
                add_reactions = False,
                speak = False
            ),
            color = discord.Color.red()
        )
        #category = discord.utils.find(lambda cat: cat.name == "NSFW", guild.channels)
        #await category.set_permissions(role,
        #    send_messages = False,
        #    send_tts_messages = False,
        #    add_reactions = False,
        #    speak = False
        #)
        channel = ctx.channel
        await channel.set_permissions(role,
            send_messages = False,
            send_tts_messages = False,
            add_reactions = False,
        )
    @commands.command()
    async def wake_up_shiro(self, ctx):
        '''
        A fun way to wake up <@391582107446804485> due to his shitty mobile notification.
        '''
        while True:
            messages = [
                "<@391582107446804485> wake up.",
                "<@391582107446804485> hello.",
                "<@391582107446804485> is washing the dishes.",
                "<@391582107446804485> how many pings now?",
                "<@391582107446804485> imagine not using discord 24/7. Couldn't be me.",
                "<@391582107446804485> hey hey hey.",
                "<@391582107446804485> friendly reminder: send a message in discord to stop this madness.",
                "<@391582107446804485> forgot to send message in discord.",
                "<@391582107446804485>'s laptop broke, so he can't reply. RIP.",
                "<@391582107446804485> EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE.",
                "<@391582107446804485> I think your phone is trash, let's use nokia brick instead.",
                "<@391582107446804485> what's up bro?",
                "<@391582107446804485> I think I should creep into your DM..."
            ]
            import random
            choose = random.randint(0, len(messages) - 1)
            await ctx.send(messages[choose])
            await asyncio.sleep(10)


    


def setup(bot):
    bot.add_cog(Experiment(bot))