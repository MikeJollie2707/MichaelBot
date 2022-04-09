import lightbulb
import hikari

import sys
import json
import os
import logging

from utilities.models import MichaelBot

EXTENSIONS = [
    "categories.admin",
    "categories.bot",
    "categories.fun",
    "categories.help",
    "categories.info",
    "categories.music",
    "events.error_handler",
    "events.logger",
    "events.misc_events",
]

async def retrieve_prefix(bot: MichaelBot, message: hikari.Message):
    # Force return when this is MichaelBeta.
    if bot.get_me().id == 649822097492803584:
        return '!'
    
    guild = bot.guild_cache.get(message.guild_id)
    if guild is None: return bot.info["prefix"]
    else: return guild.guild_module["prefix"]

def load_info(bot_name: str):
    '''
    Load the bot information from `config.json`.

    Parameter:
    - `bot_name`: Bot index as indicated in `config.json`.
    '''
    bot_info: dict = None
    secrets: dict = None

    with open("./setup/config.json", encoding = "utf-8") as fin:
        bot_info = json.load(fin)[bot_name]
        
        with open(f"./setup/{bot_info['secret']}", encoding = "utf-8") as fi:
            secrets = json.load(fi)
    
    return (bot_info, secrets)

def create_bot(bot_info, secrets) -> MichaelBot:
    bot = MichaelBot(
        token = secrets["token"],
        prefix = lightbulb.when_mentioned_or(retrieve_prefix),
        intents = hikari.Intents.ALL ^ hikari.Intents.GUILD_PRESENCES,
        logs = None if bot_info["launch_option"] == "silent-terminal" else logging.INFO
    )

    bot.info = bot_info
    bot.secrets = secrets
    bot.logging = logging.getLogger("MichaelBot")

    if bot_info["launch_option"] == "debug":
        bot.default_enabled_guilds = bot_info["default_guilds"]
        bot.logging.setLevel(logging.DEBUG)
    elif bot_info["launch_option"] == "silent-terminal": pass
    else:
        bot.logging.setLevel(logging.INFO)
    
    for extension in sorted(EXTENSIONS):
        bot.load_extensions(extension)
    
    return bot

if __name__ == "__main__":
    if os.name != "nt":
        import uvloop
        uvloop.install()
    
    argc = len(sys.argv)
    bot_info, secrets = load_info(sys.argv[1])
    bot_info["launch_option"] = ""
    if argc > 2:
        if sys.argv[2] == "--debug":
            bot_info["launch_option"] = "debug"
        elif sys.argv[2] == "--silent-terminal":
            bot_info["launch_option"] = "silent-terminal"
    
    bot = create_bot(bot_info, secrets)
    bot.run(
        activity = hikari.Activity(name = "P3 All Bindings", type = hikari.ActivityType.PLAYING)
    )
