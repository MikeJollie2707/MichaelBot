import lightbulb
import hikari
import asyncpg
import asyncpg.exceptions as pg_exception

import datetime as dt
import logging

import utilities.psql as psql

plugin = lightbulb.Plugin("Listeners", "Internal Listeners")

@plugin.listener(hikari.StartingEvent)
async def on_shard_connect(event: hikari.StartingEvent):
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
            logging.info("Bot successfully connected to the database.")
        except pg_exception.InvalidPasswordError:
            logging.error(f"Invalid password for user '{bot.d.__secrets__['user']}'.")
        except pg_exception.InvalidCatalogNameError:
            logging.error(f"Unable to find database '{bot.d.__secrets__['database']}'")
        except ConnectionRefusedError:
            logging.error(f"Unable to connect to a database at {bot.d.__secrets__['host']}, port {bot.d.__secrets__['port']}")
    
    if bot.d.pool is None:
        logging.warn("Unable to connect to a database. Bot will be missing features.")

@plugin.listener(hikari.ShardReadyEvent)
async def on_shard_ready(event: hikari.ShardReadyEvent):
    bot = event.app

    if bot.d.pool is not None:
        async with bot.d.pool.acquire() as conn:
            guilds = []
            async for guild in bot.rest.fetch_my_guilds():
                guilds.append(guild)
            
            async with conn.transaction():
                await psql.Guilds.add_many(conn, guilds)
            logging.info("Updated database from current guilds.")
            
            guilds_info = await psql.Guilds.get_all(conn)
            for guild in guilds_info:
                # DatabaseCache will pop ids in constructor.
                guild_id = guild["id"]
                log_info = await psql.Guilds.Logs.get_one(conn, guild_id)
                bot.d.guild_cache[guild_id] = models.GuildCache(guild_module = guild, logging_module = log_info)
            logging.info("Populated guild cache with stored info.")

            users_info = await psql.Users.get_all(conn)
            for user in users_info:
                user_id = user["id"]
                bot.d.user_cache[user_id] = models.UserCache(user_module = user)
                print(bot.d.user_cache[user_id].user_module)
            logging.info("Populated user cache with stored info.")


def load(bot):
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
