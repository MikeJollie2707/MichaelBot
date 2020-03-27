import discord
from discord.ext import commands

import os
import sys
import traceback
import logging
import json

def setup(bot_name):
    TOKEN = None
    prefix = None
    description = ""

    fin = open("./setup/config.json")
    initial_bot_state = json.load(fin)

    try:
        fi = open(f"./setup/{initial_bot_state[bot_name]['token']}")
        bot_config = json.load(fi)
    except FileNotFoundError:
        print("Cannot open file containing the token.")
    except KeyError:
        print("Bot config is wrong.")
    except:
        print(traceback.print_exc())
    else:
        TOKEN = bot_config["token"]
        prefix = initial_bot_state[bot_name]["prefix"]
        description = initial_bot_state[bot_name]["description"]
    
    return (TOKEN, prefix, description)

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
        bot_info = setup(sys.argv[1])
    else:
        print("Too many arguments. The second argument should be the bot's index in 'config.json'.")

    TOKEN = bot_info[0]
    prefix = bot_info[1]
    description = bot_info[2]

    setupLogger(enable = True)

    if TOKEN is None or prefix is None:
        print("Unable to load token and prefix.")
    else:
        bot = commands.Bot(command_prefix = commands.when_mentioned_or(prefix), description = description)

        try:
            for filename in sorted(os.listdir('./categories')):
                if filename.endswith('.py'):
                    bot.load_extension(f'categories.{filename[:-3]}')
        except Exception:
            print(traceback.print_exc())
        else:
            bot.run(TOKEN)