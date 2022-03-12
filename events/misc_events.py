import lightbulb
import hikari
import asyncpg
import asyncpg.exceptions as pg_exception

import datetime as dt
import logging

import utilities.psql as psql

plugin = lightbulb.Plugin("Listeners", "Internal Listeners")

@plugin.listener(hikari.ShardConnectedEvent)
async def on_shard_connect(event: hikari.ShardConnectedEvent):
    bot = event.app
    bot.d.online_at = dt.datetime.now().astimezone()
    
    if bot.d.pool is None:
        try:
            bot.d.pool = await asyncpg.create_pool(
                host = bot.d.__secrets__["host"],
                port = bot.d.__secrets__["port"],
                database = bot.d.__secrets__["database"],
                user = bot.d.__secrets__["user"],
                password = bot.d.__secrets__["password"]
            )
        except pg_exception.InvalidPasswordError:
            logging.error(f"Invalid password for user '{bot.d.__secrets__['user']}'.")
        except pg_exception.InvalidCatalogNameError:
            logging.error(f"Unable to find database '{bot.d.__secrets__['database']}'")
        except ConnectionRefusedError:
            logging.error(f"Unable to connect to a database at {bot.d.__secrets__['host']}, port {bot.d.__secrets__['port']}")
    
    if bot.d.pool is None:
        logging.warn("Unable to connect to a database. Bot will be missing features.")
    else:
        logging.info("Bot successfully connected to the database.")

@plugin.listener(hikari.ShardReadyEvent)
async def on_shard_ready(event: hikari.ShardReadyEvent):
    bot = event.app

    async with bot.d.pool.acquire() as conn:
        async with conn.transaction():
            guilds = []
            async for guild in bot.rest.fetch_my_guilds():
                guilds.append(guild)
            
            await psql.guilds.add_many(conn, guilds)

def load(bot):
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
