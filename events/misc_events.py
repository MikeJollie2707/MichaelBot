import lightbulb
import hikari
import asyncpg
import asyncpg.exceptions as pg_exception
import aiohttp

import datetime as dt
import logging

import utilities.models as models
import utilities.psql as psql

plugin = lightbulb.Plugin("Listeners", "Internal Listeners")

@plugin.listener(hikari.StartingEvent)
async def on_shard_connect(event: hikari.StartingEvent):
    bot = event.app
    bot.d.online_at = dt.datetime.now().astimezone()
    
    if bot.d.pool is None:
        try:
            bot.d.pool = await asyncpg.create_pool(
                host = bot.d.secrets["host"],
                port = bot.d.secrets["port"],
                database = bot.d.secrets["database"],
                user = bot.d.secrets["user"],
                password = bot.d.secrets["password"]
            )
            logging.info("Bot successfully connected to the database.")
        except pg_exception.InvalidPasswordError:
            logging.error(f"Invalid password for user '{bot.d.secretes['user']}'.")
        except pg_exception.InvalidCatalogNameError:
            logging.error(f"Unable to find database '{bot.d.secrets['database']}'")
        except ConnectionRefusedError:
            logging.error(f"Unable to connect to a database at {bot.d.secrets['host']}, port {bot.d.secrets['port']}")
    
    if bot.d.pool is None:
        logging.warn("Unable to connect to a database. Bot will be missing features.")
    
    if bot.d.aio_session is None:
        bot.d.aio_session = aiohttp.ClientSession()
        logging.info("aiohttp connection session created.")

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
            logging.info("Populated user cache with stored info.")

@plugin.listener(hikari.GuildJoinEvent)
async def on_guild_join(event: hikari.GuildJoinEvent):
    bot = event.app

    if bot.d.pool is not None:
        async with bot.d.pool.acquire() as conn:
            guild = event.guild
            if bot.d.guild_cache.get(guild.id) is None:
                bot.d.guild_cache[guild.id] = models.GuildCache()
                res = await bot.d.guild_cache[guild.id].force_sync(conn, guild)
                if res is None:
                    await bot.d.guild_cache[guild.id].add_guild_module(conn, guild)
                logging.info(f"Bot joined guild '{guild.id}'. Cache entry added.")

@plugin.listener(hikari.GuildLeaveEvent)
async def on_guild_leave(event: hikari.GuildLeaveEvent):
    bot = event.app
    if bot.d.pool is not None:
        bot.d.guild_cache.pop(event.guild_id, None)
        logging.info(f"Bot left guild '{event.guild_id}'. Cache entry removed.")

@plugin.listener(hikari.StoppingEvent)
async def on_stopped(event: hikari.StoppingEvent):
    bot = event.app

    if bot.d.pool is not None:
        await bot.d.pool.close()
        logging.info("Postgres connection pool gracefully closed.")
    if bot.d.aio_session is not None:
        await bot.d.aio_session.close()
        logging.info("aiohttp connection session gracefully closed.")

def load(bot: lightbulb.BotApp):
    bot.add_plugin(plugin)
def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(plugin)
