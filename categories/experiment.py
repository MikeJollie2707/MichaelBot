import discord
from discord.ext import commands

import datetime

from categories.utilities.method_cog import Facility

# This category is for testing purpose.
class Experiment(commands.Cog):
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


    


def setup(bot):
    bot.add_cog(Experiment(bot))