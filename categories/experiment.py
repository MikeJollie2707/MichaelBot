import discord
from discord.ext import commands

# This category is for testing purpose.
class Experiment(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(hidden = True)
    async def testPaginator(self, ctx):
        '''
        {0}
        '''
        embed1 = discord.Embed()
        embed1.add_field(name = "Hola1", value = "Yo1")
        embed2 = discord.Embed()
        embed2.add_field(name = "Hola2", value = "Yo2")
        embed3 = discord.Embed()
        embed3.add_field(name = "Hola3", value = "Yo3")
        from categories.templates.navigate import Pages
        navigator = Pages()
        navigator.add_page(embed1)
        navigator.add_page(embed2)
        navigator.add_page(embed3)

        await navigator.event(self.bot, ctx.channel)

    @commands.command(hidden = True)
    async def testMenu(self, ctx):
        embed1 = discord.Embed(title = "Init")
        embed2 = discord.Embed(title = "Page1")
        embed3 = discord.Embed(title = "Page2")
        from categories.templates.menu import Menu
        menu = Menu(embed1,'⏹', '🔼')
        menu.add_page('1️⃣', embed2)
        menu.add_page('2️⃣', embed3)

        await menu.event(self.bot, ctx.channel)
    
    @commands.command(hidden = True)
    async def testCogUtility(self, ctx):
        from categories.utilities.method_cog import Facility
        await ctx.send(embed = Facility.get_default_embed())


    @commands.command(hidden = True)
    async def testRole(self, ctx):
        role = ctx.guild.get_role(644337371474690048)
        role2 = ctx.guild.get_role(672637903184199690)

        await ctx.author.add_roles(role, role2)


def setup(bot):
    bot.add_cog(Experiment(bot))