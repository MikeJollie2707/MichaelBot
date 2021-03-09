import discord
from discord.ext import commands
import humanize

import datetime
import textwrap

from categories.templates.help import BigHelp, SmallHelp
from categories.templates.navigate import Pages

import categories.utilities.facility as Facility
import categories.utilities.db as DB
from categories.utilities.checks import has_database

class Core(commands.Cog):
    """Commands related to information and bot settings."""
    def __init__(self, bot):
        self.bot = bot
        self.emoji = '⚙️'
        
        self.bot.help_command = BigHelp()
        self.bot.help_command.cog = self

    async def cog_check(self, ctx):
        if isinstance(ctx.channel, discord.DMChannel):
            raise commands.NoPrivateMessage()
        
        return True
    
    @commands.group(invoke_without_command = True)
    @commands.bot_has_permissions(read_message_history = True, add_reactions = True, send_messages = True)
    async def changelog(self, ctx):
        '''
        Show the latest 10 changes of the bot.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Read Message History`, `Add Reactions`, `Send Messages`.
        '''
        channel_id = 644393721512722432 # Do not change
        channel = self.bot.get_channel(channel_id)
        if channel == None:
            await ctx.send("Seems like I can't retrieve the change logs. You might wanna report this to the developers.")
            return

        paginator = Pages()

        async for message in channel.history(limit = 10):
            embed = Facility.get_default_embed(
                description = message.content, 
                color = discord.Color.green(),
                timestamp = datetime.datetime.utcnow(),
                author = ctx.author
            )
            paginator.add_page(embed)
        
        await paginator.event(ctx, interupt = False)
    @changelog.command()
    async def dev(self, ctx):
        '''
        Show the latest 10 changes of the bot *behind the scene*.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Read Message History`, `Add Reactions`, `Send Messages`.
        '''
        
        channel_id = 759288597500788766

        channel = self.bot.get_channel(channel_id)
        if channel == None:
            await ctx.send("Seems like I can't retrieve the change logs. You might wanna report this to the developers.")
            return

        paginator = Pages()

        async for message in channel.history(limit = 10):
            embed = Facility.get_default_embed(
                description = message.content, 
                color = discord.Color.green(),
                timestamp = datetime.datetime.utcnow(),
                author = ctx.author
            )
            paginator.add_page(embed)
        
        await paginator.event(ctx, interupt = False)

    @commands.command()
    @commands.bot_has_permissions(read_message_history = True, add_reactions = True, manage_messages = True, send_messages = True)
    async def help(self, ctx, *, command__category = ""):
        '''
        Show compact help about a command, or a category.
        Note: command name and category name is case sensitive; `Core` is different from `core`.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example 1:** {prefix}{command_name}
        **Example 2:** {prefix}{command_name} info
        **Example 3:** {prefix}{command_name} Core
        **Example 4:** {prefix}{command_name} changelog dev
                       
        **You need:** None.
        **I need:** `Read Message History`, `Add Reactions`, `Manage Messages`, `Send Messages`.
        '''

        help_command = SmallHelp(ctx)
        
        if command__category == "":
            await help_command.send_bot_help()
        else:
            category = self.bot.get_cog(command__category)
            command = self.bot.get_command(command__category)

            if category != None:
                await help_command.send_cog_help(category)
            elif command != None:
                await help_command.send_command_help(command)
            else:
                await ctx.send("Command \"%s\" not found." % command__category)

    @commands.command(aliases = ["about"])
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    async def info(self, ctx):
        '''
        Information about the bot.

        **Aliases:** `about`
        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Read Message History`, `Send Messages`.
        '''

        text = self.bot.description
        if self.bot.version is not None:
            text += '\n' + self.bot.version
        
        embed = Facility.get_default_embed(
            author = ctx.author,
            title = self.bot.user.name, 
            description = self.bot.description, 
            color = discord.Color.green(),
            timestamp = datetime.datetime.utcnow()
        ).add_field(
            name = "Version:",
            value = self.bot.version if self.bot.version is not None else "1.5.0",
            inline = False
        ).add_field(
            name  = "Team:", 
            value = textwrap.dedent('''
                    **Original Owner + Tester:** <@462726152377860109>
                    **Developer:** <@472832990012243969>
                    '''), 
            inline = False
        ).add_field(
            name  = "Bot info:", 
            value = textwrap.dedent('''
                    **Language:** Python
                    **Library:** [discord.py](https://github.com/Rapptz/discord.py), [Lavalink](https://github.com/Frederikam/Lavalink), [WaveLink](https://github.com/PythonistaGuild/Wavelink)
                    **Repo:** [Click here](https://github.com/MikeJollie2707/MichaelBot)
                    '''), 
            inline = False
        ).set_author(
            name = ctx.author.name, 
            icon_url = ctx.author.avatar_url
        ).set_thumbnail(
            url = self.bot.user.avatar_url
        )

        current_time = datetime.datetime.utcnow()
        up_time = current_time - self.bot.online_at
        #days = up_time.days
        #hours = int(up_time.seconds / 3600) # We gotta round here, or else minutes will always be 0.
        #minutes = (up_time.seconds / 60) - (hours * 60) # Hour = second / 3600, minute = second / 60 (true minute without converting to hour) - hour * 60 (convert hour to minute) = remain minute

        embed.add_field(
            name  = "Host Device:",
            value = textwrap.dedent('''
                    **Processor:** Intel Core i5-4690S CPU @ 3.20GHz x 4
                    **Memory:** 15.5 GiB of RAM
                    **Bot Uptime:** %s
                    ''' % humanize.precisedelta(up_time, "minutes", format = "%0.0f")
                ),
            inline = False
        )

        await ctx.reply(embed = embed, mention_author = False)

    @commands.command()
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    async def note(self, ctx):
        '''
        Provide syntax convention in `help` and `help-all`.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Read Message History`, `Send Messages`.
        '''

        embed = Facility.get_default_embed(
            title = "MichaelBot",
            url = "https://mikejollie2707.github.io/MichaelBot",
            description = "Check out the bot documentation's front page: <https://mikejollie2707.github.io/MichaelBot>",
            timestamp = datetime.datetime.utcnow(),
            author = ctx.author
        )

        await ctx.reply(embed = embed, mention_author = False)

    @commands.command()
    @commands.check(has_database)
    @commands.has_guild_permissions(manage_guild = True)
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    @commands.cooldown(rate = 1, per = 10.0, type = commands.BucketType.guild)
    async def prefix(self, ctx, new_prefix : str = None):
        '''
        View and set the prefix for the bot.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Cooldown:** 10 seconds per 1 use (guild).
        **Example 1:** {prefix}{command_name}
        **Example 2:** {prefix}{command_name} %
        
        **You need:** `Manage Server`.
        **I need:** `Read Message History`, `Send Messages`.
        '''

        async with self.bot.pool.acquire() as conn:
            if new_prefix == None:
                bot_prefix = await DB.Guild.get_prefix(conn, ctx.guild.id)
                await ctx.reply("Current prefix: " + bot_prefix, mention_author = False)
            else:
                await DB.Guild.update_prefix(conn, ctx.guild.id, new_prefix)
                # Confirmation
                bot_prefix = await DB.Guild.get_prefix(conn, ctx.guild.id)
                await ctx.reply("Changed prefix to " + bot_prefix + " for guild ID " + str(ctx.guild.id), mention_author = False)

    @commands.command()
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    async def profile(self, ctx, member : discord.Member = None):
        '''
        Information about yourself or another __member__.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example 1:** {prefix}{command_name} MikeJollie
        **Example 2:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Read Message History`, `Send Messages`.
        '''

        if member == None:
            member = ctx.author
        else:
            member = member

        embed = Facility.get_default_embed(
            author = member,
            color = discord.Color.green(),
            timestamp = datetime.datetime.utcnow()
        ).set_author(
            name = member.name,
            icon_url = member.avatar_url
        ).add_field(
            name = "Username:", 
            value = member.name,
            inline = True
        ).add_field(
            name = "Nickname:", 
            value = member.nick if member.nick != None else member.name,
            inline = True
        ).add_field(
            name = "Avatar URL:", 
            value = "[Click here](%s)" % member.avatar_url,
            inline = True
        ).set_thumbnail(
            url = member.avatar_url
        )

        role_list = [Facility.mention(role) for role in member.roles[::-1]]
        s = " - "
        s = s.join(role_list)

        embed.add_field(name = "Roles:", value = s)

        await ctx.reply(embed = embed, mention_author = False)

    # TODO: Rewrite this command signature.
    @commands.command()
    @commands.bot_has_permissions(manage_messages = True, send_messages = True)
    @commands.cooldown(rate = 1, per = 30.0, type = commands.BucketType.user)
    async def report(self, ctx, report__suggest : str, *, content : str):
        '''
        Report a bug or suggest a feature for the bot.
        Provide constructive reports and suggestions are appreciated.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Cooldown:** 30 seconds per use (user).
        **Example 1:** {prefix}{command_name} report This command has a bug.
        **Example 2:** {prefix}{command_name} suggest This command should be improved.

        **You need:** None.
        **I need:** `Manage Messages`, `Send Messages`.
        '''

        report_chan = 644339079164723201 # Do not change
        channel = ctx.bot.get_channel(report_chan)
        if channel == None:
            channel = await ctx.bot.fetch_channel(report_chan)
            if channel == None:
                await ctx.send("I can't seems to do this command right now. Join the [support server](https://discordapp.com/jeMeyNw) with this new error message and ping the Developer to inform them.")
                raise RuntimeError("Cannot find report channel.")

        #flag = content.split()[0]
        flag = report__suggest
        if (flag == "report") or (flag == "suggest"):
            msg = " "

            #for i in range(0, len(content.split())):
            #    msg += content.split()[i] + ' '
            msg = msg.join(content.split())

            embed = Facility.get_default_embed(
                title = flag.capitalize(), 
                description = msg, 
                color = discord.Color.green(),
                timestamp = datetime.datetime.utcnow()
            )
            embed.set_author(
                name = ctx.author.name, 
                icon_url = ctx.author.avatar_url
            )
            embed.add_field(
                name = "Sender ID:",
                value = ctx.author.id,
                inline = False
            )

            try:
                await channel.send(embed = embed)
            except discord.Forbidden as forbidden:
                await ctx.send("I can't seems to do this command right now. Join the [support server](https://discordapp.com/jeMeyNw) with this new error message and ping the Developer to inform them.")
                raise forbidden
            else:
                await ctx.message.delete()
                await ctx.send("Your opinion has been sent.", delete_after = 5)
        else:
            await ctx.send("Incorrect argument. First argument should be either `suggest` or `report`.")

    @commands.command(aliases = ["server-info"])
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    async def serverinfo(self, ctx):
        '''
        Information about the server that invoke this command.

        **Aliases:** `server-info`
        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Read Message History`, `Send Messages`.
        '''

        guild = ctx.guild
        embed = discord.Embed(
            description = "Information about this server.", 
            color = discord.Color.green(),
            timestamp = datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url = guild.icon_url)

        embed.add_field(
            name = "Name", 
            value = guild.name
        )
        embed.add_field(
            name = "Created on", 
            value = guild.created_at.strftime("%b %d %Y")
        )
        embed.add_field(
            name = "Owner", 
            value = str(guild.owner)
        )
        embed.add_field(
            name = "Roles", 
            value = str(len(guild.roles)) + " roles."
        )
        embed.add_field(
            name = "Channels", 
            value = textwrap.dedent('''
                    Text channels: %d
                    Voice channels: %d
                    ''' % (len(guild.text_channels), len(guild.voice_channels))
            )
        )
        
        online = 0
        bot = 0
        guild_size = 0
        for member in guild.members:
            if member.status != discord.Status.offline:
                online += 1
            if member.bot:
                bot += 1
            guild_size += 1
        
        embed.add_field(
            name = "Members", 
            value = '''
                    %d members,
                    %d online,
                    %d bots,
                    %d humans.
                    ''' % (guild_size, online, bot, guild_size - bot)
        ).set_footer(
            text = "Server ID: %s" % str(guild.id)
        )

        await ctx.reply(embed = embed, mention_author = False)
        
def setup(bot):
    bot.add_cog(Core(bot))