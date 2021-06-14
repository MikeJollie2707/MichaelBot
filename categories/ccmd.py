import discord
from discord.ext import commands

import datetime as dt

import utilities.db as DB
import utilities.facility as Facility

from bot import MichaelBot

class CustomCommand(commands.Cog, name = "Custom Commands", command_attrs = {"cooldown_after_parsing": True}):
    def __init__(self, bot):
        self.bot : MichaelBot = bot
        self.emoji = '✨'

        self.__flags__ = ["--message", "--description", "--addroles", "--rmvroles"]
    
    @commands.group(aliases = ['ccmd', 'customcmd'], invoke_without_command = True)
    async def ccommand(self, ctx):
        async with self.bot.pool.acquire() as conn:
            custom_commands = await DB.CustomCommand.get_commands(conn, ctx.guild.id)
            if custom_commands == [None] * len(custom_commands):
                return
            
            from templates.navigate import Pages
            page = Pages()
            
            MAX_COMMAND = 10
            embed = None
            for index, command in enumerate(custom_commands):
                if index % MAX_COMMAND == 0:
                    embed = Facility.get_default_embed(
                        title = "Custom Commands",
                        timestamp = dt.datetime.utcnow()
                    ).set_author(
                        name = ctx.guild.name,
                        icon_url = ctx.guild.icon_url
                    )
                
                embed.add_field(
                    name = command["name"],
                    value = f"*{command['description']}*",
                    inline = False
                )

                if index % MAX_COMMAND == MAX_COMMAND - 1:
                    page.add_page(embed)
                    embed = None
            if embed is not None:
                page.add_page(embed)
            
            await page.start(ctx)
    
    @ccommand.command()
    async def add(self, ctx : commands.Context, name, *, input):
        builtin_existed = ctx.bot.get_command(name)
        if builtin_existed is not None:
            return await ctx.reply("This command's name already existed within the bot. Please choose a different one.")
        
        async with self.bot.pool.acquire() as conn:
            existed = await DB.CustomCommand.get_command(conn, ctx.guild.id, name)
            if existed is not None:
                return await ctx.reply(f"This guild already has a command with the name `{name}`. Please choose a different one.")
        
            async with conn.transaction():
                arguments = Facility.flag_parse(input, self.__flags__)
                description = arguments["--description"]
                message = arguments["--message"]
                addroles = arguments["--addroles"]
                rmvroles = arguments["--rmvroles"]
                if isinstance(description, str) and isinstance(message, str) and isinstance(addroles, str) and isinstance(rmvroles, str):
                    addroles_list = []
                    rmvroles_list = []
                    for role in addroles.split():
                        try:
                            drole = ctx.guild.get_role(int(role))
                        except ValueError:
                            raise commands.BadArgument
                        if drole is not None and drole < ctx.guild.get_member(self.bot.user.id).top_role:
                            addroles_list.append(int(role))
                    for role in rmvroles.split():
                        try:
                            drole = ctx.guild.get_role(int(role))
                        except ValueError:
                            raise commands.BadArgument
                        if drole is not None and drole < ctx.guild.get_member(self.bot.user.id).top_role:
                            rmvroles_list.append(int(role))
                    
                    await DB.CustomCommand.add(conn, ctx.guild.id, name, {
                        "description": description,
                        "message": message,
                        "addroles": addroles_list,
                        "rmvroles": rmvroles_list
                    })
                else:
                    raise commands.BadArgument

            await ctx.reply(f"Added command `{name}`.")
    
    @ccommand.command()
    async def remove(self, ctx, name):
        builtin_existed = ctx.bot.get_command(name)
        if builtin_existed is not None:
            return await ctx.reply("This command's name somehow matches the bot's default commands. Contact the developer.")
        
        async with self.bot.pool.acquire() as conn:
            existed = await DB.CustomCommand.get_command(conn, ctx.guild.id, name)
            if existed is None:
                return await ctx.reply(f"There is no such command in this guild.")

            async with conn.transaction():
                await DB.CustomCommand.remove(conn, ctx.guild.id, name)
            await ctx.reply(f"Removed command `{name}`.")
    
    @ccommand.group()
    async def edit(self, ctx):
        pass

    @edit.command(name = "description")
    async def desc(self, ctx, *, new_description):
        await ctx.send("Yo boi")


def setup(bot):
    bot.add_cog(CustomCommand(bot))
