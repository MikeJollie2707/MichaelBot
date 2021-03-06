import discord
from discord.ext import commands
import asyncpg

import os
import sys
import traceback
import logging
import json
import asyncio

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
    "categories.utility",
    "categories.utilities.method_cog"
]

class MichaelBot(commands.Bot):
    def __init__(self, command_prefix, help_command = commands.DefaultHelpCommand(), description = None, **kwargs):
        super().__init__(command_prefix, help_command, description, **kwargs)
        
    
    def debug(self, message : str):
        if self.DEBUG:
            print(message)

def setup(bot_name):
    TOKEN = None # A str
    bot_info = None # A dict
    db_info = None # A dict

    try:
        with open("./setup/config.json") as fin:
            bot_info = json.load(fin)[bot_name]
            
            with open(f"./setup/{bot_info['token']}") as fi:
                TOKEN = json.load(fi).get("token")
            with open(f"./setup/{bot_info['db']}") as fi:
                db_info = json.load(fi)
    except FileNotFoundError as fnfe:
        print(fnfe)
    except KeyError as ke:
        print(ke)
    
    return (TOKEN, bot_info, db_info)

def setupLogger(enable : bool = True):
    logger = logging.getLogger("discord")
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(filename = "discord.log", encoding = "utf-8", mode = "w")
    handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
    logger.addHandler(handler)

if __name__ == "__main__":
    argc = len(sys.argv)
    
    TOKEN = bot_info = db_info = None

    if (argc == 2):
        # sys.argv is a list, with the script's name as the first one, and the argument as the second one.
        TOKEN, bot_info, db_info = setup(sys.argv[1])
    else:
        print("Too many arguments. The second argument should be the bot's index in 'config.json'.")

    setupLogger(enable = True)

    if not any([TOKEN, bot_info, db_info]):
        print("Unable to load enough information for the bot.")
        print("Token: ", TOKEN)
        print("Bot info: ", bot_info)
        print("DB info: ", db_info)
    else:
        intent = discord.Intents().default()
        intent.members = True
        bot = MichaelBot(
            command_prefix = commands.when_mentioned_or(bot_info["prefix"]), 
            description = bot_info.get("description"),
            status = discord.Status.online,
            activity = discord.Game(name = "Kubuntu"),
            intents = intent # v1.5.0 requires Intent.members to be enabled to use most of member cache.
        )
        # https://discordpy.readthedocs.io/en/latest/intents.html for intents

        if not hasattr(bot, "version"):
            bot.version = bot_info.get("version")
        if not hasattr(bot, "DEBUG"):
            bot.DEBUG = bot_info.get("debug") if bot_info.get("debug") is not None else False
        if not hasattr(bot, "__divider__"):
            bot.__divider__ = "----------------------------\n"
        
        if not hasattr(bot, "pool") and not hasattr(bot, "json"):
            loop = asyncio.get_event_loop()
            bot.pool = loop.run_until_complete(asyncpg.create_pool(
                host = db_info["host"],
                user = db_info["user"],
                database = db_info["database"],
                password = db_info["password"],
                #port = 5432
            ))
            # It might throw sth here but too lazy to catch so hey.
            bot.json = {}

        try:
            for extension in sorted(__discord_extension__):
                bot.load_extension(extension)
            
            #bot.__db__ = None # Disable db_init
            bot.run(TOKEN)

            # Close the pool connection here, just to be safe
            # but bcuz of async stuffs, I'll have to rewrite quite a bit
            # and I don't have time rn.
            # await bot.pool.close()

            print("Bot closed all connection from the pool.")
            print("Bot disconnected. You can now close the terminal.")
        except Exception:
            print(traceback.print_exc())
