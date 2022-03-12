import lightbulb
import hikari

import sys
import json
import os

import utilities.psql as psql

__discord_extensions__ = [
    "categories.admin",
    "categories.core",
    "categories.fun",
    "categories.help",
    "categories.music",
    "events.error_handler",
    "events.misc_events"
]

async def retrieve_prefix(bot: lightbulb.BotApp, message: hikari.Message):
    async with bot.d.pool.acquire() as conn:
        # Force return.
        if bot.get_me().id == 649822097492803584:
            return '!'
        
        guild = await psql.guilds.get_one(conn, message.guild_id)
        if guild is not None:
            return guild["prefix"]
        else:
            return bot.d.bot_info["prefix"]

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

def create_bot() -> lightbulb.BotApp:
    argc = len(sys.argv)

    bot_info, secrets = load_info(sys.argv[1])
    bot_info["debug"] = False
    if argc > 2:
        if sys.argv[2] == "--debug":
            bot_info["debug"] = True
    
    bot = lightbulb.BotApp(
        token = secrets["token"], 
        prefix = lightbulb.when_mentioned_or(retrieve_prefix),
        intents = hikari.Intents.ALL ^ hikari.Intents.GUILD_PRESENCES,
    )
    
    bot.d.bot_info = bot_info
    bot.d.__secrets__ = secrets
    bot.d.pool = None
    bot.d.prefixes = {}
    # Whitelist MichaelBot and Bruh server for early testing.
    if bot_info["debug"]:
        bot.default_enabled_guilds = [644336990698995712, 705270581184167987, 868449475323101224]
    
    for extension in sorted(__discord_extensions__):
        bot.load_extensions(extension)
    
    return bot

if __name__ == "__main__":
    if os.name != "nt":
        import uvloop
        uvloop.install()
    
    bot = create_bot()
    bot.run()
