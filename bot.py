import discord
from discord.ext import commands
import asyncpg

import os
import sys
import traceback
import logging
import json
import asyncio

def setup(bot_name):
    TOKEN = None # A str
    bot_info = None # A dict
    db_info = None # A dict

    fin = open("./setup/config.json")
    initial_bot_state = json.load(fin)

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

    bot_info = None
    if (argc == 2):
        # sys.argv is a list, with the script's name as the first one, and the argument as the second one.
        TOKEN, bot_info, db_info = setup(sys.argv[1])
    else:
        print("Too many arguments. The second argument should be the bot's index in 'config.json'.")

    TOKEN = bot_info[0]
    prefix = bot_info[1]
    description = bot_info[2]

    setupLogger(enable = True)

    if not any([TOKEN, bot_info, db_info]):
        print("Unable to load enough information for the bot.")
        print("Token: ", TOKEN)
        print("Bot info: ", bot_info)
        print("DB info: ", db_info)
    else:
        bot = commands.Bot(
            command_prefix = commands.when_mentioned_or(prefix), 
            description = description,
            status = discord.Status.online,
            activity = discord.Game(name = "Linux")
        )

        if not hasattr(bot, "version"):
            bot.version = bot_info.get("version")
        
        if not hasattr(bot, "pool"):
            loop = asyncio.get_event_loop()
            bot.pool = loop.run_until_complete(asyncpg.create_pool(
                host = db_info["host"],
                user = db_info["user"],
                database = db_info["database"],
                password = db_info["password"]
            ))
            # It might throw sth here but too lazy to catch so hey.

        try:
            for filename in sorted(os.listdir('./categories')):
                if filename.endswith('.py'):
                    bot.load_extension(f'categories.{filename[:-3]}')
            
            bot.run(TOKEN)
        except Exception:
            print(traceback.print_exc())
