import lightbulb
import hikari

import sys
import json
import os

from utilities.models import MichaelBot

EXTENSIONS = [
    "categories.admin",
    "categories.bot",
    "categories.fun",
    "categories.help",
    "categories.info",
    "categories.music",
    "categories.test",
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

        info = bot_info,
        secrets = secrets
    )
    
    for extension in sorted(EXTENSIONS):
        bot.load_extensions(extension)
    
    return bot

if __name__ == "__main__":
    if os.name != "nt":
        import uvloop
        uvloop.install()
    
    argc = len(sys.argv)
    bot_info, secrets = load_info(sys.argv[1])
    
    bot = create_bot(bot_info, secrets)
    bot.run(
        activity = hikari.Activity(name = "P3 All Bindings", type = hikari.ActivityType.PLAYING)
    )
