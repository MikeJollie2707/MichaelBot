import discord
from discord.ext import commands
import asyncpg
import asyncpg.exceptions as pg_exceptions

# Debug stuffs
import sys
import traceback
import logging

import json
import asyncio
import typing # IntelliSense only

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

        self.DEBUG : typing.Optional[bool] = kwargs.get("debug")
        self.version : typing.Optional[str] = kwargs.get("version")
        self.__divider__ = "----------------------------\n"

        self.pool : typing.Optional[asyncpg.pool.Pool]= None
        
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

def setup_logger(enable : bool = True):
    if enable:
        logger = logging.getLogger("discord")
        logger.setLevel(logging.WARNING)
        handler = logging.FileHandler(filename = "discord.log", encoding = "utf-8", mode = "w")
        handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
        logger.addHandler(handler)

def get_info():
    bot_info = secrets = None
    argc = len(sys.argv)

    if (argc == 2):
        bot_info, secrets = load_info(sys.argv[1])
    else:
        print("Incorrect amount of arguments. The first argument should be the bot index in 'config.json'")
    
    return bot_info, secrets
    
async def get_prefix(bot : MichaelBot, message):
    #if bot.pool is not None and message.guild is not None:
    #    async with bot.pool.acquire() as conn:
    #        prefix = await DB.Guild.get_prefix(conn, message.guild.id)
    #else:
    #    prefix = '$'
    prefix = None
    if message.guild is not None:
        prefix = bot._prefixes[message.guild.id]
    if prefix is None:
        prefix = '$'
    
    return commands.when_mentioned_or(prefix)(bot, message)

async def main():
    bot_info, secrets = get_info()
    
    if not any([bot_info, secrets]):
        print("Unable to load enough information for the bot.")
        print("Bot info:", bot_info)
        print("Secrets:", secrets)
    else:
        # v1.5.0+ requires Intent.members to be enabled to use most of member cache.
        intent = discord.Intents().default()
        intent.members = True

        description = bot_info.get("description") if bot_info.get("description") is not None else "`None`"
        debug = bot_info.get("debug") if bot_info.get("debug") is not None else False

        bot = MichaelBot(
            command_prefix = get_prefix, 
            description = description,
            status = discord.Status.online,
            activity = discord.Game(name = "Kubuntu"),
            intents = intent,

            debug = debug,
            version = bot_info.get("version")
        )
        
        try:
            bot.debug("Connecting to database...")
            bot.pool = await asyncpg.create_pool(
                dsn = secrets.get("dsn"),
                host = secrets.get("host"),
                port = secrets.get("port"),
                user = secrets.get("user"),
                database = secrets.get("database"),
                password = secrets.get("password")
            )
        except pg_exceptions.InvalidCatalogNameError:
            print("Can't seems to find the database.")
        except pg_exceptions.InvalidPasswordError:
            print("Wrong password or wrong user.")
        except ConnectionRefusedError:
            print("Can't connect to database.")
        
        bot.debug("Loading extensions...")
        for extension in sorted(__discord_extension__):
            bot.load_extension(extension)

        try:
            await bot.start(secrets["token"])
        except KeyboardInterrupt:
            await bot.close()
        except Exception:
            print(traceback.print_exc())
        finally:
            if bot.pool is not None:
                await bot.pool.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot closed by key interruption.")
        print("You may now close the terminal.")
