'''Various other events to handle. Most of them are related to dealing with database connection.'''

import datetime as dt
import json
import logging

import aiohttp
import asyncpg
import hikari
import lightbulb

from utils import models, psql

plugin = lightbulb.Plugin(".Listeners", "Internal Listeners")
logger = logging.getLogger("MichaelBot")

async def update_item(conn: asyncpg.Connection):
    item_data: list[dict]
    try:
        with open("./categories/econ/items.json", encoding = "utf-8") as fin:
            item_data = json.load(fin)
    except FileNotFoundError:
        logging.warning("Bot is trying to load './categories/econ/items.json', but it is not found.")
    else:    
        for index, item in enumerate(item_data):
            # Ignore the sample item.
            if index == 0: continue

            await psql.Item.sync(conn, psql.Item(**item, sort_id = index))

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
        except asyncpg.InvalidPasswordError:
            logger.error(f"Invalid password for user '{bot.secrets['user']}'.")
        except asyncpg.InvalidCatalogNameError:
            logger.error(f"Unable to find database '{bot.secrets['database']}'")
        except ConnectionRefusedError:
            logger.error(f"Unable to connect to a database at {bot.secrets['host']}, port {bot.secrets['port']}")
        else:
            logger.info("Bot successfully connected to the database.")

            async with bot.pool.acquire() as conn:
                async with conn.transaction():
                    await update_item(conn)
    
    if bot.pool is None:
        logger.warning("Unable to connect to a database. Bot will be missing features.")
    
    if bot.aio_session is None:
        bot.aio_session = aiohttp.ClientSession()
        logger.info("aiohttp connection session created.")

@plugin.listener(hikari.ShardReadyEvent)
async def on_shard_ready(event: hikari.ShardReadyEvent):
    bot: models.MichaelBot = event.app

    if bot.pool is not None:
        async with bot.pool.acquire() as conn:
            async with conn.transaction():
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
                
                logger.info("Populated guild cache with stored info.")

                users_info = await psql.User.get_all(conn, as_dict = True)
                for user in users_info:
                    user_id = user["id"]
                    bot.user_cache[user_id] = models.UserCache(user_module = user)
                logger.info("Populated user cache with stored info.")
    
    logger.info("Bot is now ready to go!")


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
                logger.info(f"Bot joined guild '{guild.id}'. Cache entry added.")

@plugin.listener(hikari.GuildLeaveEvent)
async def on_guild_leave(event: hikari.GuildLeaveEvent):
    bot: models.MichaelBot = event.app
    if bot.pool is not None:
        bot.guild_cache.pop(event.guild_id, None)
        logger.info(f"Bot left guild '{event.guild_id}'. Cache entry removed.")

@plugin.listener(hikari.StoppingEvent)
async def on_stopping(event: hikari.StoppingEvent):
    bot: models.MichaelBot = event.app

    if bot.pool is not None:
        await bot.pool.close()
        logger.info("Postgres connection pool gracefully closed.")
    if bot.aio_session is not None:
        await bot.aio_session.close()
        logger.info("aiohttp connection session gracefully closed.")

def load(bot: models.MichaelBot):
    bot.add_plugin(plugin)
def unload(bot: models.MichaelBot):
    bot.remove_plugin(plugin)
