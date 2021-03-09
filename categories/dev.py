import discord
from discord.ext import commands

import asyncio
import datetime
import textwrap

import categories.utilities.facility as Facility
import categories.utilities.db as DB
from categories.utilities.checks import is_dev

# Commands for developers to test things and stuffs. The format does not need to be formal.

class Dev(commands.Cog, command_attrs = {"cooldown_after_parsing" : True, "hidden" : True}):
    '''Commands for developers to abuze power'''
    def __init__(self, bot):
        self.bot = bot
        self.REPORT_CHAN = 644339079164723201
    
    async def cog_check(self, ctx):
        if isinstance(ctx.channel, discord.DMChannel):
            raise commands.NoPrivateMessage()
        elif not is_dev(ctx):
            raise commands.CheckFailure()

        return True
    
    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("This command is reserved for bot developers only!")

    @commands.command()
    @commands.bot_has_permissions(send_messages = True)
    async def all_guild(self, ctx):
        '''
        Display all the guilds the bot is currently in.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example:** {prefix}{command_name}

        **You need:** `dev status`.
        **I need:** `Send Messages`.
        '''
        
        embed = discord.Embed(
            title = "%d Guilds" % len(ctx.bot.guilds),
            color = discord.Color.green(),
            datetime = datetime.datetime.utcnow()
        )

        guilds = ctx.bot.guilds

        for index in range(0, len(guilds)):
            embed.add_field(name = f"{index + 1}. {guilds[index].name}", value = f"ID: {guilds[index].id}", inline = False)
        
        await ctx.send(embed = embed)

    @commands.command()
    async def addmoney(self, ctx, amount : int, *, member : discord.Member = None):
        '''
        Add a certain amount of money to a user or to yourself.

        The limit range is `[1-25]`.

        *Warning: This command is available only in beta. Once the currency is official, this command will
        no longer available.*

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example:** {prefix}{command_name} 25

        **You need:** None
        **I need:** `Send Messages`.
        '''

        if member is None:
            member = ctx.author
        
        async with self.bot.pool.acquire() as conn:
            await DB.User.add_money(conn, ctx.author.id, amount)
        
        await ctx.send("Added $%d to %s." % (amount, member.name))

    @commands.command()
    async def rmvmoney(self, ctx, amount : int, *, member: discord.Member = None):
        '''
        Remove a certain amount of money from a user or from yourself.

        The limit range is `[1-25]`. If the removal cause the target's money to drop below 0, it'll be 0.

        *Warning: This command is available only in beta. Once the currency is official, this command will
        no longer available.*

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example:** {prefix}{command_name} 25

        **You need:** None
        **I need:** `Send Messages`.
        '''

        if member is None:
            member = ctx.author
        
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                member_money = await DB.User.get_money(conn, member.id)
                member_money -= amount

                await DB.User.update_money(conn, member.id, member_money)
        
        await ctx.send("Removed $%d from %s." % (amount, member.name))

    @commands.command()
    @commands.cooldown(rate = 1, per = 3600)
    async def get_report_type(self, ctx, type : str):
        channel = self.bot.get_channel(self.REPORT_CHAN)
        target_emoji = ''
        if type.upper() == "PENDING":
            target_emoji = '📌'
        elif type.upper() == "SEARCHING" or type.upper() == "INVESTIGATING":
            target_emoji = '🔍'
        elif type.upper() == "UPVOTE":
            target_emoji = '👍'
        
        messages = []

        async for message in channel.history(oldest_first = True):
            reactions = message.reactions
            for reaction in reactions:
                if reaction.emoji == target_emoji:
                    messages.append(message)
        
        embed = Facility.get_default_embed(
            title = "All entries that is %s" % type,
            timestamp = datetime.datetime.utcnow(),
            author = ctx.author
        )

        for index, message in enumerate(messages):
            actual_content = message.embeds[0].description
            embed.add_field(
                name = f"Entry #{index + 1}:",
                value = "[*%s*](%s)" % (actual_content, message.jump_url),
                inline = False
            )
        
        await ctx.reply(embed = embed, mention_author = False)

    # I'm intending to move this command to a category called "Administrator" or something.
    @commands.command()
    @commands.is_owner()
    async def leave_guild(self, ctx):
        '''
        Leave the current guild.
        Note: This does not delete the server's config file yet.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example:** {prefix}{command_name}

        **You need:** `Owner of the server` OR `dev status`.
        **I need:** `Send Messages`.
        '''

        await ctx.send("Are you sure for me to leave this guild?")
        def check(msg):
            return msg.author == ctx.author
        
        try:
            confirm = self.bot.wait_for("message", check = check, timeout = 30.0)
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. I'll stay still.")
            return
        else:
            confirm_str = confirm.content.upper()
            if confirm_str[0] == "Y":
                try:
                    await ctx.send("Bye! :wave:")
                    await ctx.guild.leave()
                except discord.HTTPException:
                    await ctx.send("Leaving the guild failed. Guess you'll stick with me for a while :smile:")

    @commands.command()
    @commands.cooldown(rate = 1, per = 5.0, type = commands.BucketType.default)
    async def reload(self, ctx, extension_name):
        '''
        Reload a module.
        Useful when you don't want to disconnect the bot but still update your change.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Cooldown:** 5 seconds per use (global cooldown).
        **Example:** {prefix}{command_name} categories.templates

        **You need:** `dev status`.
        **I need:** `Send Messages` (optionally).
        '''

        self.bot.reload_extension(extension_name)

        try:
            await ctx.send("Reloaded extension " + extension_name)
        except:
            print("Can't send message to %d" % ctx.message.id)
        print("Reloaded extension " + extension_name)
    @reload.error
    async def reload_error(self, ctx, error):
        if isinstance(error, commands.ExtensionNotFound):
            await ctx.send("I cannot find this extension. Check your typo or the repo again.")
    
    @commands.command()
    @commands.cooldown(rate = 1, per = 5.0, type = commands.BucketType.default)
    async def reload_all_extension(self, ctx):
        '''
        Reload all modules.
        Useful for OCD people (like MikeJollie) because `reload` will mess up the order in `help` and `help-all`.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Cooldown:** 5 seconds per use (global cooldown).
        **Example:** {prefix}{command_name}

        **You need:** `dev status`.
        **I need:** `Send Messages`.
        '''

        extension_list = [] # We can't loop through self.bot.extensions directly because reload_extension will modify the map and raise RunTimeError

        for extension in self.bot.extensions:
            extension_list.append(extension)
        
        for extension_name in extension_list:
            self.bot.reload_extension(extension_name)
        
        try:
            await ctx.send("Reloaded all extensions.")
        except:
            print("Can't send message to %d" % ctx.message.id)
        print("Reloaded all extension")
    @reload_all_extension.error
    async def reload_all_error(self, ctx, error):
        pass
    
    @commands.command(aliases = ["suggest_response"])
    @commands.bot_has_permissions(send_messages = True)
    @commands.cooldown(rate = 1, per = 60.0, type = commands.BucketType.default)
    async def report_response(self, ctx, message_ID : int, *, response : str):
        '''
        Response to a report/suggest.
        Note that the command will look over the last 100 messages in the report channel.

        **Aliases:** `suggest_response`
        **Usage:** <prefix>**{command_name}** {command_signature}
        **Cooldown:** 60 seconds per 1 use (global)
        **Examples:** {prefix}{command_name} 670493266629886002 I like this idea, but the library doesn't allow so.

        **You need:** `dev status`.
        **I need:** `Send Messages`.
        '''

        channel = self.bot.get_channel(self.REPORT_CHAN)
        if channel == None:
            await ctx.send("Seems like I can't find the report channel. You can check again and edit the channel ID.")
            return
        
        messages = await channel.history(limit = 100).flatten()
        for message in messages:
            if message_ID == message.id:
                if len(message.embeds) == 0:
                    await ctx.send("This message is not a report/suggest type. Please check again.")
                else:
                    report = message.embeds[0]

                    response_embed = discord.Embed().from_dict(report.to_dict()) # Create a new embed using the old's dictionary form. This will make it work fast.

                    response_embed.add_field(
                        name = "**Developer Response:**",
                        value = response,
                        inline = False
                    )
                    response_embed.set_footer(
                        text = str(ctx.author),
                        icon_url = ctx.author.avatar_url
                    )

                    try:
                        await message.edit(embed = response_embed)
                    except discord.Forbidden:
                        print("The bot does not have Manage Messages in report channel.")

    @commands.command()
    async def reset_all_cooldown(self, ctx):
        '''
        Self-explanatory.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example:** {prefix}{command_name}

        You need: `dev status`.
        I need: `Send Messages`.
        '''

        for command in self.bot.commands:
            if command.is_on_cooldown(ctx):
                command.reset_cooldown(ctx)
        await ctx.send("All cooldown reseted.")

    @commands.command()
    @commands.is_owner()
    async def shutdown(self, ctx):
        '''
        Disconnect the bot from Discord.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example:** {prefix}{command_name}

        You need: `bot owner`.
        I need: `None`.
        '''

        await ctx.send("Disconnecting...")
        await self.bot.close()
        print("Bot shutdown from command.")


        


def setup(bot):
    bot.add_cog(Dev(bot))