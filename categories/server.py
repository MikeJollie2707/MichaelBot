import discord
from discord.ext import commands

import datetime

from categories.utilities.method_cog import Facility

class Server(commands.Cog, name = "Settings", command_attrs = {"cooldown_after_parsing": True}):
    '''Commands related to the bot setting in the server.'''
    def __init__(self, bot):
        self.bot = bot
        self.emoji = '🛠'
    
    async def cog_check(self, ctx):
        if isinstance(ctx.channel, discord.DMChannel):
            raise commands.NoPrivateMessage()
        
        return True
    
    @commands.command(aliases = ["log-enable"])
    @commands.has_guild_permissions(manage_guild = True)
    @commands.bot_has_permissions(send_messages = True)
    @commands.bot_has_guild_permissions(view_audit_log = True)
    @commands.cooldown(rate = 1,  per = 3.0, type = commands.BucketType.guild)
    async def log_enable(self, ctx):
        '''
        Enable logging in your server.

        **Aliases:** `log-enable`
        **Usage:** <prefix>**{command_name}**
        **Example:** {prefix}{command_name}

        You need: `Manage Server`.
        I need: `View Audit Log`, `Send Messages`.
        '''

        config = Facility.get_config(ctx.guild.id)
        if config["STATUS_LOG"] == 1:
            await ctx.send("Logging is already enabled for this server.")
        else:
            config["STATUS_LOG"] = 1
            Facility.save_config(config)
            await ctx.send("Logging is enabled for this server. You should setup a log channel.")

    @commands.command(aliases = ["log-setup"])
    @commands.has_guild_permissions(manage_guild = True)
    @commands.bot_has_permissions(send_messages = True)
    @commands.bot_has_guild_permissions(view_audit_log = True)
    @commands.cooldown(rate = 1,  per = 3.0, type = commands.BucketType.guild)
    async def log_setup(self, ctx, log : discord.TextChannel = None):
        '''
        Set or view a log channel in your server.
        If this command is invoked but you haven't enabled logging, it'll automatically be enabled.

        **Aliases:** `log-setup`
        **Usage:** <prefix>**{command_name}** [text channel mention/ID/name]
        **Example 1:** {prefix}{command_name} 649111117204815883
        **Example 2:** {prefix}{command_name} a-random-log-channel
        **Example 3:** {prefix}{command_name}

        You need: `Manage Server`.
        I need: `View Audit Log`, `Send Messages`.
        '''

        config = Facility.get_config(ctx.guild.id)
        if log is None:
            await ctx.send("Current logging channel ID: `%d`" % config["LOG_CHANNEL"])
        else:
            config["STATUS_LOG"] = 1
            config["LOG_CHANNEL"] = log.id
            Facility.save_config(config)
            
            embed = Facility.get_default_embed(
                title = "Logging Enabled", 
                description = "This is now a logging channel.", 
                color = discord.Color.green(),
                timestamp = datetime.datetime.utcnow()
            ).set_author(
                name = self.bot.user.name, 
                icon_url = self.bot.user.avatar_url
            ).set_footer(
                text = "Set by %s" % ctx.author.name,
                icon_url = ctx.author.avatar_url
            )

            await log.send(embed = embed)
    
    @commands.command(aliases = ["log-disable"])
    @commands.has_guild_permissions(manage_guild = True)
    @commands.bot_has_permissions(send_messages = True)
    @commands.cooldown(rate = 1,  per = 3.0, type = commands.BucketType.guild)
    async def log_disable(self, ctx):
        '''
        Disable logging in your server.
        **Usage:** <prefix>**{command_name}**
        **Example:** {prefix}{command_name}

        You need: `Manage Server`.
        I need: `Send Messages`.
        '''

        config = Facility.get_config(ctx.guild.id)
        config["STATUS_LOG"] = 0
        Facility.save_config(config)
        await ctx.send("Logging is disabled for this server.")

    @commands.command(aliases = ["welcome-enable"])
    @commands.has_guild_permissions(manage_guild = True)
    @commands.bot_has_permissions(send_messages = True)
    @commands.cooldown(rate = 1,  per = 3.0, type = commands.BucketType.guild)
    async def welcome_enable(self, ctx):
        '''
        Enable welcoming new members in your server.
        **Usage:** <prefix>**{command_name}**
        **Example:** {prefix}{command_name}

        You need: `Manage Server`.
        I need: `Send Messages`.
        '''
        config = Facility.get_config(ctx.guild.id)
        if config["STATUS_WELCOME"] == 1:
            await ctx.send("Welcoming system is already enabled for this server.")
        else:
            config["STATUS_WELCOME"] = 1
            Facility.save_config(config)
            await ctx.send("Welcoming is enabled for this server. You should setup the welcome channel and message.")
    
    @commands.command(aliases = ["welcome-setup"])
    @commands.has_guild_permissions(manage_guild = True)
    @commands.bot_has_permissions(send_messages = True)
    @commands.cooldown(rate = 1,  per = 3.0, type = commands.BucketType.guild)
    async def welcome_setup(self, ctx, welcome_chan : discord.TextChannel = None, *, welcome_text : str = ""):
        '''
        Set or view the welcome channel and message in your server.
        If this command is invoked but you haven't enabled welcoming, it'll automatically be enabled.

        **Aliases:** `welcome-setup`
        **Usage:** <prefix>**{command_name}** [text channel mention/ID/name] [welcome text]
        **Argument:** `[user.mention]`, `[user.name]`, `[guild.name]`, `[guild.count]`
        **Example 1:** {prefix}{command_name} 644336991135072261 Welcome [user.mention] to [guild.name]!
        **Example 2:** {prefix}{command_name} a-random-welcome-channel You are the [guild.count]th member!
        **Example 3:** {prefix}{command_name} #another-random-channel
        **Example 4:** {prefix}{command_name}

        You need: `Manage Server`.
        I need: `Send Messages`.
        '''

        config = Facility.get_config(ctx.guild.id)
        if welcome_chan is None:
            await ctx.send(f"Current welcome channel ID: `{config['WELCOME_CHANNEL']}`\nCurrent welcome message: ", embed = discord.Embed(description = config["WELCOME_TEXT"]))
        else:
            config["STATUS_WELCOME"] = 1

            if welcome_text == "":
                welcome_text = "Hello [user.mention]! Welcome to **[guild.name]**! You're the [guild.count]th member in this server! Enjoy the fun!!! :tada:"
            config["WELCOME_TEXT"] = welcome_text

            try:
                await welcome_chan.send("Your welcome message is: %s" % welcome_text)
            except discord.Forbidden:
                await ctx.send(f"I can't send message to {welcome_chan.mention}!")
            else:
                config["WELCOME_CHANNEL"] = welcome_chan.id
                await ctx.send("Channel %s is now a welcome channel." % welcome_chan.mention)

            Facility.save_config(config)


    @commands.Cog.listener("on_member_join")
    async def welcome_new_member(self, member):
        config = Facility.get_config(member.guild.id)
        if config["ERROR"] == 0 and config["STATUS_WELCOME"] == 1 and config["WELCOME_CHANNEL"] != 0:
            welcome_channel = self.bot.get_channel(config["WELCOME_CHANNEL"])
            welcome_text = config["WELCOME_TEXT"]

            # We don't use f-string here because it'll raise attribute errors which are annoying.
            welcome_text = welcome_text.replace("[user.mention]", "<@%d>" % member.id)
            welcome_text = welcome_text.replace("[user.name]", str(member))
            welcome_text = welcome_text.replace("[guild.name]", str(member.guild))
            welcome_text = welcome_text.replace("[guild.count]", str(len(member.guild.members)))

            await welcome_channel.send(welcome_text)
        else:
            return

    @commands.command(aliases = ["welcome-disable"])
    @commands.has_guild_permissions(manage_guild = True)
    @commands.bot_has_permissions(send_messages = True)
    @commands.cooldown(rate = 1,  per = 3.0, type = commands.BucketType.guild)
    async def welcome_disable(self, ctx):
        '''
        Disable welcoming in your server.

        **Aliases:** `welcome-disable`
        **Usage:** <prefix>**{command_name}**
        **Example:** {prefix}{command_name}

        You need: `Manage Server`.
        I need: `Send Messages`.
        '''
        
        config = Facility.get_config(ctx.guild.id)
        config["STATUS_WELCOME"] = 0
        Facility.save_config(config)
        await ctx.send("Welcoming is disabled for this server.")
    

def setup(bot):
    bot.add_cog(Server(bot))
