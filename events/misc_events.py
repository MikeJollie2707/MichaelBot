import lightbulb
import hikari
import asyncpg
import asyncpg.exceptions as pg_exception
import aiohttp

import datetime as dt

import utils.models as models
import utils.psql as psql

plugin = lightbulb.Plugin("Listeners", "Internal Listeners")

@plugin.listener(hikari.StartingEvent)
async def on_starting(event: hikari.StartingEvent):
    bot: models.MichaelBot = event.app
    if bot.online_at is None:
        bot.online_at = dt.datetime.now().astimezone()
    
    if bot.pool is None:
        try:
            bot.pool = await asyncpg.create_pool(
                host = bot.secrets["host"],
                port = bot.secrets["port"],
                database = bot.secrets["database"],
                user = bot.secrets["user"],
                password = bot.secrets["password"]
            )
            bot.logging.info("Bot successfully connected to the database.")
        except pg_exception.InvalidPasswordError:
            bot.logging.error(f"Invalid password for user '{bot.secrets['user']}'.")
        except pg_exception.InvalidCatalogNameError:
            bot.logging.error(f"Unable to find database '{bot.secrets['database']}'")
        except ConnectionRefusedError:
            bot.logging.error(f"Unable to connect to a database at {bot.secrets['host']}, port {bot.secrets['port']}")
    
    if bot.pool is None:
        bot.logging.warning("Unable to connect to a database. Bot will be missing features.")
    
    if bot.aio_session is None:
        bot.aio_session = aiohttp.ClientSession()
        bot.logging.info("aiohttp connection session created.")

@plugin.listener(hikari.ShardReadyEvent)
async def on_shard_ready(event: hikari.ShardReadyEvent):
    bot: models.MichaelBot = event.app

    if bot.pool is not None:
        async with bot.pool.acquire() as conn:
            # Only cache guilds that are available to bot, not all guilds in db.
            async for guild in bot.rest.fetch_my_guilds():
                if bot.guild_cache.get(guild.id) is None:
                    bot.guild_cache[guild.id] = models.GuildCache()
                    res = await bot.guild_cache[guild.id].force_sync(conn, guild)
                    if res is None:
                        await bot.guild_cache[guild.id].add_guild_module(conn, guild)
                else:
                    # Handle on reconnect
                    res = await bot.guild_cache[guild.id].force_sync(conn, guild)
            
            bot.logging.info("Populated guild cache with stored info.")

            users_info = await psql.Users.get_all(conn)
            for user in users_info:
                user_id = user["id"]
                bot.user_cache[user_id] = models.UserCache(user_module = user)
            bot.logging.info("Populated user cache with stored info.")

@plugin.listener(hikari.GuildJoinEvent)
async def on_guild_join(event: hikari.GuildJoinEvent):
    bot: models.MichaelBot = event.app

    if bot.pool is not None:
        async with bot.pool.acquire() as conn:
            guild = event.guild
            if bot.guild_cache.get(guild.id) is None:
                bot.guild_cache[guild.id] = models.GuildCache()
                res = await bot.guild_cache[guild.id].force_sync(conn, guild)
                if res is None:
                    await bot.guild_cache[guild.id].add_guild_module(conn, guild)
                bot.logging.info(f"Bot joined guild '{guild.id}'. Cache entry added.")

@plugin.listener(hikari.GuildLeaveEvent)
async def on_guild_leave(event: hikari.GuildLeaveEvent):
    bot: models.MichaelBot = event.app
    if bot.pool is not None:
        bot.guild_cache.pop(event.guild_id, None)
        bot.logging.info(f"Bot left guild '{event.guild_id}'. Cache entry removed.")

@plugin.listener(hikari.StoppingEvent)
async def on_stopping(event: hikari.StoppingEvent):
    bot: models.MichaelBot = event.app

    if bot.pool is not None:
        await bot.pool.close()
        bot.logging.info("Postgres connection pool gracefully closed.")
    if bot.aio_session is not None:
        await bot.aio_session.close()
        bot.logging.info("aiohttp connection session gracefully closed.")

def load(bot: models.MichaelBot):
    bot.add_plugin(plugin)
def unload(bot: models.MichaelBot):
    bot.remove_plugin(plugin)
