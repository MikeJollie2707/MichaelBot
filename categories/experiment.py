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
    async def normal_edited_message(self, ctx):
        await ctx.message.delete()
        embed = Facility.get_default_embed(
            title = "Message Edited",
            description = '''
                **Content before:** Hey
                **Content after:** Heyy
                **Author:** Non-existent
                ----------------------------
                **Message URL:** Jump to message
                **Channel:** #Ace_Shiro_is_gay
            ''',
            timestamp = datetime.datetime.utcnow()
        ).set_thumbnail(
            url = ctx.author.avatar_url
        ).set_author(
            name = str(ctx.author),
            icon_url = ctx.author.avatar_url
        ).set_footer(
            text = str(ctx.author),
            icon_url = ctx.author.avatar_url
        )
        await ctx.send(embed = embed)
    
    @commands.command()
    async def field_edited_message(self, ctx):
        await ctx.message.delete()
        embed = Facility.get_default_embed(
            title = "Message Edited",
            description = '''
                **Content before:** Hey
                **Content after:** Heyy
            ''',
            timestamp = datetime.datetime.utcnow()
        ).add_field(
            name = "**Author**",
            value = "Non-existent",
            inline = False
        ).add_field(
            name = "Message URL:",
            value = "Jump to message",
            inline = False
        ).add_field(
            name = "**Channel:**",
            value = "#Ace_Shiro_is_gay",
            inline = False
        ).set_thumbnail(
            url = ctx.author.avatar_url
        ).set_author(
            name = str(ctx.author),
            icon_url = ctx.author.avatar_url
        ).set_footer(
            text = str(ctx.author),
            icon_url = ctx.author.avatar_url
        )
        await ctx.send(embed = embed)

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