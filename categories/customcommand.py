import discord
from discord.ext import commands

import datetime as dt

import utilities.db as DB
import utilities.facility as Facility

from bot import MichaelBot

class CustomCommand(commands.Cog, name = "Custom Commands", command_attrs = {"cooldown_after_parsing": True}):
    """Commands that support adding custom commands."""
    def __init__(self, bot):
        self.bot : MichaelBot = bot
        self.emoji = '✨'

        self.__flags__ = [
            "--description", 
            "--message",
            "--channel", 
            "--reply", 
            "--addroles", 
            "--rmvroles"
        ]

    @commands.Cog.listener("on_message")
    async def _message(self, message : discord.Message):
        # This is kind of oofy, but whatever conditions within `events.py`, you'll need to filter them out here.
        if message.author == self.bot.user or isinstance(message.channel, discord.DMChannel):
            return
        
        guild_prefix = self.bot._prefixes[message.guild.id] if self.bot.user.id != 649822097492803584 else '!'
        if message.content.startswith(guild_prefix):
            import utilities.db as DB
            async with self.bot.pool.acquire() as conn:
                # The message have the format of <prefix>command some_random_bs
                # To get the command, split the content, and get the first, which will be
                # <prefix>command only.
                # To remove prefix, trim the string view based on the length of prefix.
                existed = await DB.CustomCommand.get_command(conn, message.guild.id, message.content.split()[0][len(guild_prefix):])
                if existed is not None:
                    if existed["channel"] is not None:
                        channel = message.guild.get_channel(existed["channel"])
                    else:
                        channel = message.channel
                    # Can only reply to the same channel
                    reference = None
                    if existed["is_reply"] and existed["channel"] == message.channel.id:
                        reference = message
                    else:
                        reference = None
                    await channel.send(existed["message"], reference = reference)
                    if len(existed["addroles"]) > 0:
                        addroles_list = [message.guild.get_role(role) for role in existed["addroles"]]
                        try:
                            await message.author.add_roles(*addroles_list)
                        except discord.Forbidden:
                            await message.channel.send("Failed to add roles.")
                    if len(existed["rmvroles"]) > 0:
                        rmvroles_list = [message.guild.get_role(role) for role in existed["rmvroles"]]
                        try:
                            await message.author.remove_roles(*rmvroles_list)
                        except discord.Forbidden:
                            await message.channel.send("Failed to remove roles.")
    
    @commands.group(aliases = ['ccmd', 'customcmd'], invoke_without_command = True)
    @commands.cooldown(rate = 1, per = 5.0, type = commands.BucketType.guild)
    @commands.bot_has_permissions(add_reactions = True, read_message_history = True, send_messages = True)
    async def ccommand(self, ctx):
        '''
        View custom commands for this guild.

        **Usage:** {usage}
        **Cooldown:** 5 seconds per 1 use (guild)
        **Example:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Add Reactions`, `Read Message History`, `Send Messages`.
        '''
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
    @commands.cooldown(rate = 1, per = 5.0, type = commands.BucketType.guild)
    @commands.has_guild_permissions(manage_guild = True)
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    async def add(self, ctx : commands.Context, name, *, input):
        '''
        Add a custom command to the guild.

        The `input` is in the form of arguments commonly used within terminals.
        There are 5 arguments, one of which is required:
        - `--description`: The command's description.
        - **`--message`: This is required. The command's response.**
        - `--channel`: The channel the command will send the response to. Must be ID.
        - `--reply`: A flag indicating whether the message will be a reply.
        - `--addroles`: The roles the bot will add to the command invoker. Must be IDs.
        - `--rmvroles`: The roles the bot will remove to the command invoker. Must be IDs.
        Order is not important.

        **Usage:** {usage}
        **Cooldown:** 5 seconds per 1 use (guild)
        **Example 1:** {prefix}{command_name} test --message Hello
        **Example 2:** {prefix}{command_name} test2 --description Give some cool roles --message Enjoy :D --reply --addroles 704527865173114900 644339804141518848

        **You need:** `Manage Server`.
        **I need:** `Read Message History`, `Send Messages`.
        '''
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
    @commands.cooldown(rate = 1, per = 5.0, type = commands.BucketType.guild)
    @commands.has_guild_permissions(manage_guild = True)
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    async def remove(self, ctx, name):
        '''
        Remove a custom command from the guild.

        **Usage:** {usage}
        **Cooldown:** 5 seconds per 1 use (guild)
        **Example:** {prefix}{command_name} test

        **You need:** `Manage Server`.
        **I need:** `Read Message History`, `Send Messages`.
        '''
        builtin_existed = ctx.bot.get_command(name)
        if builtin_existed is not None:
            return await ctx.reply("This command's name somehow matches the bot's default commands. Contact the developer.")
        
        async with self.bot.pool.acquire() as conn:
            existed = await DB.CustomCommand.get_command(conn, ctx.guild.id, name)
            if existed is None:
                return await ctx.reply(f"There is no such command in this guild.")

            async with conn.transaction():
                await DB.CustomCommand.remove(conn, ctx.guild.id, name)
            await ctx.reply(f"Removed command `{name}`.", mention_author = False)
    
    @ccommand.group()
    async def edit(self, ctx):
        pass

    @edit.command(name = "description")
    async def desc(self, ctx, *, new_description):
        await ctx.send("Yo boi")


def setup(bot : MichaelBot):
    bot.add_cog(CustomCommand(bot))
