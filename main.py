import lightbulb
import hikari

import sys
import json
import os
import logging

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

async def retrieve_prefix(bot: lightbulb.BotApp, message: hikari.Message):
    # Force return when this is MichaelBeta.
    if bot.get_me().id == 649822097492803584:
        return '!'
    
    guild = bot.d.guild_cache.get(message.guild_id)
    if guild is None: return bot.d.bot_info["prefix"]
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

def create_bot(bot_info, secrets) -> lightbulb.BotApp:
    bot = lightbulb.BotApp(
        token = secrets["token"], 
        prefix = lightbulb.when_mentioned_or(retrieve_prefix),
        intents = hikari.Intents.ALL ^ hikari.Intents.GUILD_PRESENCES,
        help_slash_command = True
    )
    bot.d.bot_info = bot_info
    bot.d.secrets = secrets

    bot.d.logging = logging.getLogger("MichaelBot")
    bot.d.logging.setLevel(logging.INFO)

    bot.d.pool = None
    bot.d.aio_session = None
    # Hold high-traffic data on database (usually for read-only purpose).
    bot.d.guild_cache = {}
    bot.d.user_cache = {}

    if bot_info["debug"]:
        bot.default_enabled_guilds = bot_info["default_guilds"]
        bot.d.logging.setLevel(logging.DEBUG)
    
    for extension in sorted(EXTENSIONS):
        bot.load_extensions(extension)
    
    return bot

if __name__ == "__main__":
    if os.name != "nt":
        import uvloop
        uvloop.install()
    
    argc = len(sys.argv)
    bot_info, secrets = load_info(sys.argv[1])
    bot_info["debug"] = False
    if argc > 2:
        if sys.argv[2] == "--debug":
            bot_info["debug"] = True
    
    bot = create_bot(bot_info, secrets)
    bot.run(
        activity = hikari.Activity(name = "P3 All Bindings", type = hikari.ActivityType.PLAYING)
    )
