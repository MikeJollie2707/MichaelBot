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
                return await ctx.reply("*Cricket noises*", mention_author = False)

            from templates.navigate import listpage_generator
            def title_formatter(command):
                embed = Facility.get_default_embed(
                    title = "Custom Commands",
                    timestamp = dt.datetime.utcnow()
                ).set_author(
                    name = ctx.guild.name,
                    icon_url = ctx.guild.icon_url
                )
                return embed
            def item_formatter(embed, command):
                embed.add_field(
                    name = command["name"],
                    value = f"*{command['description']}*" if command["description"] != "" else "*None*",
                    inline = False
                )
            page = listpage_generator(3, custom_commands, title_formatter, item_formatter)
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
        
            arguments = Facility.flag_parse(input, self.__flags__)
            description = arguments["--description"]
            message = arguments["--message"]
            channel = arguments["--channel"]
            is_reply = arguments["--reply"]
            addroles = arguments["--addroles"]
            rmvroles = arguments["--rmvroles"]

            addroles_list = []
            rmvroles_list = []

            if isinstance(description, bool):
                return await ctx.reply("`--description` is not a flag but rather an argument.")
            if message is None:
                return await ctx.reply("`--message` is a required argument.")
            if isinstance(message, bool):
                return await ctx.reply("`--message` is not a flag but rather an argument.")
            if isinstance(channel, bool):
                return await ctx.reply("`--channel` must be an existed channel's ID.")
            elif channel is not None:
                try:
                    channel = int(channel)
                except ValueError:
                    return await ctx.reply("`--channel` must be an existed channel's ID.")
                
                dchannel = ctx.guild.get_channel(channel)
                if dchannel is None:
                    return await ctx.reply("`--channel` must be an existed channel's ID.")
            # I decide to make `--reply` both a flag and argument (although there will be no info in argument).
            if is_reply is not None:
                is_reply = True
            else:
                is_reply = False
            if isinstance(addroles, bool) or isinstance(rmvroles, bool):
                return await ctx.reply("`--addroles`/`--rmvroles` is not a flag but rather an argument.")
            if isinstance(addroles, str):
                addroles_list = []
                for role in addroles.split():
                    try:
                        drole = ctx.guild.get_role(int(role))
                    except ValueError:
                        return await ctx.reply("`--addroles` must contain existed roles' ID.")
                    if drole is not None and drole < ctx.guild.get_member(self.bot.user.id).top_role:
                        addroles_list.append(int(role))
            if isinstance(rmvroles, str):
                rmvroles_list = []
                for role in rmvroles.split():
                    try:
                        drole = ctx.guild.get_role(int(role))
                    except ValueError:
                        return await ctx.reply("`--rmvroles` must contain existed roles' ID.")
                    if drole is not None and drole < ctx.guild.get_member(self.bot.user.id).top_role:
                        rmvroles_list.append(int(role))
                
            async with conn.transaction():
                await DB.CustomCommand.add(conn, ctx.guild.id, name, {
                    "description": description,
                    "message": message,
                    "channel": channel,
                    "is_reply": is_reply,
                    "addroles": addroles_list,
                    "rmvroles": rmvroles_list
                })

            await ctx.reply(f"Added command `{name}`.", mention_author = False)
    
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
