from operator import add
import discord
from discord.ext import commands
import humanize

import traceback
import sys
import datetime
import typing # IntelliSense purpose only

import utilities.facility as Facility
import utilities.db as DB
from bot import MichaelBot # IntelliSense purpose only

class Events(commands.Cog):
    def __init__(self, bot : MichaelBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        if self.bot.pool is not None:
            await DB.update_db(self.bot)

            guilds = self.bot.guilds
            async with self.bot.pool.acquire() as conn:
                for guild in guilds:
                    prefix = await DB.Guild.get_prefix(conn, guild.id)
                    if prefix is None:
                        prefix = '$'
                    self.bot._prefixes[guild.id] = prefix
            
        
        print("Logged in as")
        print(self.bot.user.name)
        print(self.bot.user.id)
        print("------------")

    @commands.Cog.listener()
    async def on_connect(self):
        if not hasattr(self.bot, "online_at"):
            self.bot.online_at = datetime.datetime.utcnow()
        
    
    @commands.Cog.listener()
    async def on_disconnect(self):
        print(f"Bot logged out on {datetime.datetime.now()}")

    @commands.Cog.listener()
    async def on_resumed(self):
        print(f"Bot reconnected on {datetime.datetime.now()}")
    
    @commands.Cog.listener("on_guild_join")
    async def _guild_join(self, guild):
        if self.bot.pool is not None:
            async with self.bot.pool.acquire() as conn:
                guild_existed = await DB.Guild.find_guild(conn, guild.id)
                if guild_existed is None:
                    async with conn.transaction():
                        for member in guild.members:
                            if not member.bot:
                                user_existed = await DB.User.find_user(conn, member.id)
                                member_existed = await DB.Member.find_member(conn, member.id, guild.id)
                                if user_existed is None:
                                    await DB.User.insert_user(conn, member)
                                    await DB.Member.insert_member(conn, member)
                                elif member_existed is None:
                                    await DB.Member.insert_member(conn, member)
            self.bot._prefixes[guild.id] = '$'


    @commands.Cog.listener("on_message")
    async def _message(self, message : discord.Message):
        if message.author == self.bot.user:
            return
            
        elif isinstance(message.channel, discord.DMChannel):
            RESPONSE_LIST = [
                    "I only talk in server, sorry.",
                    "Sorry mate, I really hate responding to DM.",
                    "Hey my developer hasn't allowed me to say in DM.",
                    "You may go to your server and use one of my commands.",
                    "So many people try to DM bots, but they always fail.",
                    "Bot is my name, DM is not my game.",
                    "Stop raiding my DM.",
                    "Sorry, can't respond your message here :(",
                    "It is really impossible to expect from a bot to respond to someone's DM.",
                    "I can't talk in DM, ask this guy -> <@472832990012243969>"
            ]
            dm_chan : discord.DMChannel = message.author.dm_channel
            
            import random
            await dm_chan.send(random.choice(RESPONSE_LIST))
        
        #await bot.process_commands(message) # uncomment this if this event is outside of a cog.

    @commands.Cog.listener("on_command_error")
    async def _command_error(self, ctx : commands.Context, error : commands.CommandError):
        ERROR_SEPARATOR = "-----------------------------------------------------------------------"
        
        if isinstance(error, commands.CommandNotFound):
            return await ctx.trigger_typing()
        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send("Missing the following required argument: %s. Please use `%shelp %s` for more information." % (f"`{error.param.name}`", ctx.prefix, ctx.command))
        elif isinstance(error, commands.BadArgument):
            if ctx.command.name != "kick" and ctx.command.name != "ban":
                await ctx.send("Wrong argument type. Please use `%shelp %s` for more information." % (ctx.prefix, ctx.command))
            return
        elif isinstance(error, commands.NoPrivateMessage):
            return
        elif isinstance(error, commands.DisabledCommand):
            return await ctx.send("Sorry, but this command is disabled for now, it'll be back soon :thumbsup:")
        elif isinstance(error, commands.TooManyArguments):
            return await ctx.send("Too many arguments. Please use `%shelp %s` for more information." % (ctx.prefix, ctx.command))
        elif isinstance(error, commands.CommandOnCooldown):
            return await ctx.send("Hey there slow down! %s left!" % humanize.precisedelta(error.retry_after, "seconds", format = "%0.2f"))
        elif isinstance(error, commands.MissingPermissions):
            missing_perms = [f"`{Facility.convert_roleperms_dpy_discord(permission)}`" for permission in error.missing_perms]
            return await ctx.send("You are missing the following permission(s) to execute this command: " + Facility.striplist(missing_perms))
        elif isinstance(error, commands.BotMissingPermissions):
            if "send_messages" in error.missing_perms:
                return await ctx.author.send("Hey! Sorry for disturbing, but I'm missing `Send Messages` permission.")
                missing_perms = [f"`{Facility.convert_roleperms_dpy_discord(permission)}`" for permission in error.missing_perms]
                return await ctx.send("I'm missing the following permission(s) to execute this command: " + Facility.striplist(missing_perms))
        elif isinstance(error, commands.NSFWChannelRequired):
            return await ctx.send("This command is NSFW! Either find a NSFW channel to use this or don't use this at all!")
        elif isinstance(error, commands.ChannelNotReadable):
            return await ctx.send("It seems the channel you provided is not readable for me. Might want to do something about that.")
        
        else:
            error_text = "This command raised the following exception. Please copy and report it to the developer using `report`. Thank you and sorry for this inconvenience."
            error_text += "```%s```" % error
            await ctx.send(error_text)
            self.bot.debug(ERROR_SEPARATOR)
            self.bot.debug("%s raised a fatal error!\n" % ctx.command.name)
            self.bot.debug("Ignoring exception in command {}:".format(ctx.command), file = sys.stderr)
            if self.bot.DEBUG:
                traceback.print_exception(type(error), error, error.__traceback__, file = sys.stderr)
            self.bot.debug(ERROR_SEPARATOR)
            self.bot.debug("\n\n")

    @commands.Cog.listener("on_command_completion")
    async def _command_completion(self, ctx : commands.Context):
        if ctx.cog.qualified_name == "Dev":
            self.bot.debug("%s used %s at %s." % (str(ctx.author), ctx.command.name, str(datetime.datetime.today())))
            self.bot.debug("\n\n")

def setup(bot : MichaelBot):
    bot.add_cog(Events(bot))