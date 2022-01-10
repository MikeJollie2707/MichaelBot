import discord
from discord.ext import commands

import datetime as dt

import utilities.db as DB
import utilities.facility as Facility

from bot import MichaelBot
from templates.navigate import listpage_generator

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
        
        guild_prefix = self.bot.prefixes[message.guild.id] if self.bot.user.id != 649822097492803584 else '!'
        if message.content.startswith(guild_prefix):
            async with self.bot.pool.acquire() as conn:
                # The message have the format of <prefix>command some_random_bs
                # To get the command, split the content, and get the first element, which will be
                # <prefix>command only.
                # To remove prefix, trim the string view based on the length of prefix.
                command = message.content.split()[0][len(guild_prefix):]

                existed = await DB.CustomCommand.get_command(conn, message.guild.id, command)
                if existed is not None:
                    guild = message.guild
                    if existed["channel"] is not None:
                        channel = guild.get_channel(existed["channel"])
                    else:
                        channel = message.channel
                    # Can only reply to the same channel
                    reference_chan = None
                    if existed["is_reply"] and existed["channel"] == message.channel.id:
                        reference_chan = message
                    else:
                        reference_chan = None
                    
                    try:
                        await channel.send(existed["message"], reference = reference_chan)
                    except discord.Forbidden:
                        # For now, we're just silently ignore this.
                        # Might change to raising a command error though.
                        pass
                    
                    # Simply ignore if bot doesn't have role. Might change to raising a command error though.
                    if len(existed["addroles"]) > 0 and guild.me.guild_permissions.manage_roles:
                        addroles_list = []
                        for role_id in existed["addroles"]:
                            role = message.guild.get_role(role_id)
                            if role is not None and guild.me.top_role > role:
                                addroles_list.append(role)
                            else:
                                return channel.send("The following role ID cannot be added by the bot: %d." % (role_id))
                        # Since we filter out the possibility of discord.Forbidden, all that's left is discord.HTTPException, which I have 0 idea how to handle.
                        await message.author.add_roles(*addroles_list)
                    if len(existed["rmvroles"]) > 0 and guild.me.guild_permissions.manage_roles:
                        rmvroles_list = []
                        for role_id in existed["addroles"]:
                            role = message.guild.get_role(role_id)
                            if role is not None and guild.me.top_role > role:
                                rmvroles_list.append(role)
                            else:
                                return channel.send("The following role ID cannot be added by the bot: %d." % (role_id))
                        await message.author.add_roles(*rmvroles_list)
    
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
    async def add(self, ctx : commands.Context, name, *, arguments):
        '''
        Add a custom command to the guild.

        The `arguments` is in the form of arguments commonly used within terminals.
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
        
            arguments = Facility.flag_parse(arguments, self.__flags__)
            description = arguments["--description"]
            message = arguments["--message"]
            channel = arguments["--channel"]
            is_reply = bool(arguments["--reply"])
            addroles = arguments["--addroles"]
            rmvroles = arguments["--rmvroles"]

            addroles_list = []
            rmvroles_list = []

            if isinstance(description, bool):
                return await ctx.reply("`--description` is expected to have an argument, but nothing is provided.")
            if message is None:
                return await ctx.reply("`--message` is a required argument.")
            if isinstance(message, bool):
                return await ctx.reply("`--message` is expected to have an argument, but nothing is provided.")
            if isinstance(channel, bool):
                return await ctx.reply("`--channel` is expected to have an argument, but nothing is provided.")
            elif channel is not None:
                try:
                    channel = int(channel)
                except ValueError:
                    return await ctx.reply("`--channel` must be an existed channel's ID.")
                
                dchannel = ctx.guild.get_channel(channel)
                if dchannel is None:
                    return await ctx.reply("`--channel` must be an existed channel's ID.")
            if isinstance(addroles, bool) or isinstance(rmvroles, bool):
                return await ctx.reply("`--addroles`/`--rmvroles` is expected to have an argument, but nothing is provided.")
            if isinstance(addroles, str):
                addroles_list = []
                for role in addroles.split():
                    try:
                        drole = ctx.guild.get_role(int(role))
                    except ValueError:
                        return await ctx.reply("`--addroles` must contain existed roles' ID.")
                    if drole is not None and drole < ctx.guild.me.top_role:
                        addroles_list.append(int(role))
            if isinstance(rmvroles, str):
                rmvroles_list = []
                for role in rmvroles.split():
                    try:
                        drole = ctx.guild.get_role(int(role))
                    except ValueError:
                        return await ctx.reply("`--rmvroles` must contain existed roles' ID.")
                    if drole is not None and drole < ctx.guild.me.top_role:
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
            await ctx.reply(f"Removed command `{name}` from this guild.", mention_author = False)
    
    @ccommand.command()
    @commands.cooldown(rate = 1, per = 20.0, type = commands.BucketType.guild)
    @commands.has_guild_permissions(manage_guild = True)
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    async def edit(self, ctx, name, *, arguments):
        '''
        Edit a custom command in the guild.

        The `arguments` function similarly to the `add` command with some minor differences:
        - `--reply` will toggle the option to reply.
        - To clear the role list, simply provide `clear` (case-sensitive). Ex: `--addroles clear`.
        - `--message` is not required.

        **Usage:** {usage}
        **Cooldown:** 20 seconds per 1 use (guild).
        **Example:** {prefix}{command_name} test --description Forgot to add a description.

        **You need:** `Manage Server`.
        **I need:** `Read Message History`, `Send Messages`.
        '''
        builtin_existed = ctx.bot.get_command(name)
        if builtin_existed is not None:
            return await ctx.reply("This is a built-in bot command, not a custom command.")
        
        async with self.bot.pool.acquire() as conn:
            existed = await DB.CustomCommand.get_command(conn, ctx.guild.id, name)
            if existed is None:
                return await ctx.reply(f"There's no custom command with the name {name}.")
            existed.pop("name")
            existed.pop("guild_id")
        
            arguments = Facility.flag_parse(arguments, self.__flags__)
            description = arguments["--description"]
            message = arguments["--message"]
            channel = arguments["--channel"]
            is_reply = arguments["--reply"]
            addroles = arguments["--addroles"]
            rmvroles = arguments["--rmvroles"]

            if isinstance(description, bool):
                return await ctx.reply("`--description` is expected to have an argument, but nothing is provided.")
            elif description is not None:
                existed["description"] = description
            
            if isinstance(message, bool):
                return await ctx.reply("`--message` is expected to have an argument, but nothing is provided.")
            elif message is not None:
                existed["message"] = message
            
            if isinstance(channel, bool):
                return await ctx.reply("`--channel` is expected to have an argument, but nothing is provided.")
            elif channel is not None:
                try:
                    channel = int(channel)
                except ValueError:
                    return await ctx.reply("`--channel` must be an existed channel's ID.")
                
                dchannel = ctx.guild.get_channel(channel)
                if dchannel is None:
                    return await ctx.reply("`--channel` must be an existed channel's ID.")
                existed["channel"] = channel
            
            if isinstance(is_reply, bool):
                existed["is_reply"] = not existed["is_reply"]
            
            if isinstance(addroles, bool) or isinstance(rmvroles, bool):
                return await ctx.reply("`--addroles`/`--rmvroles` is expected to have an argument, but nothing is provided.")
            if isinstance(addroles, str):
                existed["addroles"] = []
                if addroles != "clear":
                    for role in addroles.split():
                        try:
                            drole = ctx.guild.get_role(int(role))
                        except ValueError:
                            return await ctx.reply("`--addroles` must contain existed roles' ID.")
                        if drole is not None and drole < ctx.guild.get_member(self.bot.user.id).top_role:
                            existed["addroles"].append(int(role))
            if isinstance(rmvroles, str):
                existed["rmvroles"] = []
                if rmvroles != "clear":
                    for role in rmvroles.split():
                        try:
                            drole = ctx.guild.get_role(int(role))
                        except ValueError:
                            return await ctx.reply("`--rmvroles` must contain existed roles' ID.")
                        if drole is not None and drole < ctx.guild.get_member(self.bot.user.id).top_role:
                            existed["rmvroles"].append(int(role))
            
            async with conn.transaction():
                await DB.CustomCommand.bulk_update(conn, ctx.guild.id, name, existed)

            await ctx.reply(f"Updated command `{name}`.", mention_author = False)

def setup(bot : MichaelBot):
    bot.add_cog(CustomCommand(bot))
