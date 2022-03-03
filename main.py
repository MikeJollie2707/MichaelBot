import lightbulb
import hikari

import sys
import json
import os

__discord_extensions__ = [
    "categories.admin",
    "categories.core",
    "categories.fun",
    "categories.help",
    "categories.music",
    "events.error_handler",
    "events.misc_events"
]

def load_info(bot_name : str):
    '''
    Load the bot information from `config.json`.

    Parameter:
    - `bot_name`: Bot index as indicated in `config.json`.
    '''
    bot_info : dict = None
    secrets : dict = None

    with open("./setup/config.json", encoding = "utf-8") as fin:
        bot_info = json.load(fin)[bot_name]
        
        with open(f"./setup/{bot_info['secret']}", encoding = "utf-8") as fi:
            secrets = json.load(fi)
    
    return (bot_info, secrets)

def main():
    argc = len(sys.argv)

    bot_info, secrets = load_info(sys.argv[1])
    if argc > 2:
        if sys.argv[2] == "--debug":
            bot_info["debug"] = True
        else:
            bot_info["debug"] = False
    
    bot = lightbulb.BotApp(
        token = secrets["token"], 
        prefix = lightbulb.when_mentioned_or(bot_info["prefix"]),
        intents = hikari.Intents.ALL ^ hikari.Intents.GUILD_PRESENCES,
    )
    bot.d.version = bot_info["version"]
    bot.d.description = bot_info["description"]
    bot.d.debug = bot_info["debug"]
    # Whitelist MichaelBot and Bruh server for early testing.
    if bot_info["debug"]:
        bot.default_enabled_guilds = [644336990698995712, 705270581184167987, 868449475323101224]
    
    for extension in sorted(__discord_extensions__):
        bot.load_extensions(extension)
    
    bot.run()

if __name__ == "__main__":
    if os.name != "nt":
        import uvloop
        uvloop.install()
    
    main()
