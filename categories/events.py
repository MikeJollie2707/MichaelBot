import discord
from discord.ext import commands

import traceback
import sys
import json
from datetime import datetime

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Logged in as")
        print(self.bot.user.name)
        print(self.bot.user.id)
        print("------------")

    @commands.Cog.listener()
    async def on_connect(self):
        if not hasattr(self.bot, "online_at"):
            self.bot.online_at = datetime.utcnow()
    
    @commands.Cog.listener()
    async def on_disconnect(self):
        if hasattr(self.bot, "guild_config"):
            pass

    @commands.Cog.listener()
    async def on_message(self, message):
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
            dm_chan = message.author.dm_channel
            
            import random
            random_response = random.randint(0, len(RESPONSE_LIST) - 1)
            await dm_chan.send(RESPONSE_LIST[random_response])
        
        #await bot.process_commands(message) # uncomment this if this event is outside of a cog.

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        ERROR_SEPARATOR = "-----------------------------------------------------------------------"
        try:
            if isinstance(error, commands.CommandError):
                print("%s raised an error!" % ctx.command.name)
        except AttributeError: # If command not found, wrong syntax, etc.
            async with ctx.typing(): # This will make the bot type for 10 seconds.
                n = 0
            return

        isErrorComplex = False    
        
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Missing arguments. Please use `%shelp %s` for more information." % (ctx.prefix, ctx.command))

        elif isinstance(error, commands.BadArgument):
            if ctx.command.name == "kick" or ctx.command.name == "ban":
                return
            else:
                await ctx.send("Wrong argument type. Please use `%shelp %s` for more information." % (ctx.prefix, ctx.command))

        elif isinstance(error, commands.NoPrivateMessage):
            return
        
        elif isinstance(error, commands.DisabledCommand):
            await ctx.send("Sorry, but this command is disabled for now, it'll be back soon :thumbsup:")

        elif isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments. Please use `%shelp %s` for more information." % (ctx.prefix, ctx.command))
        
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send("Hey there slow down! %0.2f seconds left!" % error.retry_after)

        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You are missing the following permission(s) to execute this command: " + str(error.missing_perms))
        
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("I'm missing the following permission(s) to execute this command: " + str(error.missing_perms))
        
        else:
            error_text = "This command raised the following exception. Please copy and report it to the developer using `report`. Thank you and sorry for this inconvenience."
            error_text += "```%s```" % error
            await ctx.send(error_text)
            print(ERROR_SEPARATOR)
            print("Ignoring exception in command {}:".format(ctx.command), file = sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file = sys.stderr)
            print(ERROR_SEPARATOR)
            print("\n\n")
            isErrorComplex = True
        
        if not isErrorComplex:
            print("It seems that this error isn't fatal (no traceback). Check the logging channel to know more.")
            print("\n\n")


    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        if ctx.cog.qualified_name == "Dev":
            print("%s used %s at %s." % (str(ctx.author), ctx.command.name, str(datetime.today())))
            print("\n\n")

def setup(bot):
    bot.add_cog(Events(bot))