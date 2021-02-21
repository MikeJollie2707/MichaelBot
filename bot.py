import discord
from discord.ext import commands
import asyncpg

import sys
import traceback
import logging
import json
import asyncio

import categories.utilities.db as DB

__discord_extension__ = [
    "categories.core",
    "categories.currency",
    "categories.dev",
    "categories.events",
    "categories.experiment",
    "categories.game",
    "categories.logger",
    "categories.moderation",
    #"categories.music",
    "categories.nsfw",
    "categories.server",
    "categories.utility"
]

class MichaelBot(commands.Bot):
    def __init__(self, command_prefix, help_command = commands.DefaultHelpCommand(), description = None, **kwargs):
        super().__init__(command_prefix, help_command, description, **kwargs)

        self.DEBUG = kwargs.get("allow_debug")
        self.version = kwargs.get("version")
        
    def debug(self, message : str):
        if self.DEBUG:
            print(message)

def load_info(bot_name):
    bot_info = None # A dict
    secrets = None # A dict

    try:
        with open("./setup/config.json") as fin:
            bot_info = json.load(fin)[bot_name]
            
            with open(f"./setup/{bot_info['secret']}") as fi:
                secrets = json.load(fi)
    except FileNotFoundError as fnfe:
        print(fnfe)
    except KeyError as ke:
        print(ke)
    
    return (bot_info, secrets)

def setupLogger(enable : bool = True):
    if enable:
        logger = logging.getLogger("discord")
        logger.setLevel(logging.WARNING)
        handler = logging.FileHandler(filename = "discord.log", encoding = "utf-8", mode = "w")
        handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
        logger.addHandler(handler)
    
async def get_prefix(bot, message):
    async with bot.pool.acquire() as conn:
        prefix = await DB.Guild.get_prefix(conn, message.guild.id)
    
    return commands.when_mentioned_or(prefix)(bot, message)

if __name__ == "__main__":
    bot_info = secrets = None
    argc = len(sys.argv)

    if (argc == 2):
        # sys.argv is a list, with the script's name as the first one, and the argument as the second one.
        bot_info, secrets = load_info(sys.argv[1])
    else:
        print("Too many arguments. The second argument should be the bot's index in 'config.json'.")

    setupLogger(enable = False)

    if not any([bot_info, secrets]):
        print("Unable to load enough information for the bot.")
        print("Bot info: ", bot_info)
        print("Secret info: ", secrets)
    else:
        intent = discord.Intents().default()
        intent.members = True
        bot = MichaelBot(
            command_prefix = get_prefix, 
            description = bot_info.get("description"),
            status = discord.Status.online,
            activity = discord.Game(name = "Kubuntu"),
            intents = intent, # v1.5.0+ requires Intent.members to be enabled to use most of member cache.

            debug = bot_info.get("debug") if bot_info.get("debug") is not None else False,
            version = bot_info.get("version")
        )
        # https://discordpy.readthedocs.io/en/latest/intents.html for intents

        if not hasattr(bot, "__divider__"):
            bot.__divider__ = "----------------------------\n"
        
        if not hasattr(bot, "pool") and not hasattr(bot, "json"):
            loop = asyncio.get_event_loop()
            bot.pool = loop.run_until_complete(asyncpg.create_pool(
                host = secrets["host"],
                user = secrets["user"],
                database = secrets["database"],
                password = secrets["password"]
            ))
            # It might throw sth here but too lazy to catch so hey.
            bot.json = {}

        try:
            for extension in sorted(__discord_extension__):
                bot.load_extension(extension)
            
            bot.run(secrets["token"])

            # Close the pool connection here, just to be safe
            # but bcuz of async stuffs, I'll have to rewrite quite a bit
            # and I don't have time rn.
            # await bot.pool.close()
        except Exception:
            print(traceback.print_exc())
        
        print("Bot closed all connection from the pool.")
        print("Bot disconnected. You can now close the terminal.")
