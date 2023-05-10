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

async def update_item(conn: asyncpg.Connection, bot: models.MichaelBot):
    item_data: list[dict]
    try:
        with open("./categories/econ/items.json", encoding = "utf-8") as fin:
            item_data = json.load(fin)
    except FileNotFoundError:
        logger.warning("Bot is trying to load './categories/econ/items.json', but it is not found.")
    else:
        async with conn.transaction():
            for index, item in enumerate(item_data):
                # Ignore the sample item.
                if index == 0: continue

                item["sort_id"] = index
                await bot.item_cache.update(conn, psql.Item(**item))

async def update_badge(conn: asyncpg.Connection, _: models.MichaelBot):
    badge_data: list[dict]
    try:
        with open("./categories/econ/badges.json", encoding = 'utf-8') as fin:
            badge_data = json.load(fin)
    except FileNotFoundError:
        logger.warning("Bot is trying to load './categories/econ/items.json', but it is not found.")
    else:
        async with conn.transaction():
            for index, badge in enumerate(badge_data):
                if index == 0: continue

                badge["sort_id"] = index
                await psql.Badge.update(conn, psql.Badge(**badge))
                
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
                await update_item(conn, bot)
                await update_badge(conn, bot)
    
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
                        # If guild not available in cache, try get it in db.
                        existed = await psql.Guild.fetch_one(conn, id = guild.id)
                        if not existed:
                            # Very new guild.
                            await bot.guild_cache.insert(conn, psql.Guild(guild.id, guild.name))
                        else:
                            # Probably some sort of desync.
                            bot.guild_cache.update_local(existed)
                    else:
                        # Probably some sort of desync.
                        await bot.guild_cache.update_from_db(conn, guild.id)
                logger.info("Populated guild cache with stored info.")

                await bot.log_cache.update_all_from_db(conn)
                logger.info("Populated log cache with stored info.")
                
                await bot.user_cache.update_all_from_db(conn)
                logger.info("Populated user cache with stored info.")
    
    logger.info("Bot is now ready to go!")

@plugin.listener(hikari.GuildJoinEvent)
async def on_guild_join(event: hikari.GuildJoinEvent):
    bot: models.MichaelBot = event.app

    if bot.pool is not None:
        async with bot.pool.acquire() as conn:
            guild = event.guild
            
            # Pretty much same code as on_shard_ready().
            if bot.guild_cache.get(guild.id) is None:
                existed = await psql.Guild.fetch_one(conn, id = guild.id)
                if not existed:
                    await bot.guild_cache.insert(conn, psql.Guild(guild.id, guild.name))
                else:
                    # Handle on reconnect
                    await bot.guild_cache.update_local(existed)
                
                logger.info(f"Bot joined guild '{guild.id}'. Cache entry added.")
            else:
                await bot.guild_cache.update_from_db(conn, guild.id)

@plugin.listener(hikari.GuildLeaveEvent)
async def on_guild_leave(event: hikari.GuildLeaveEvent):
    bot: models.MichaelBot = event.app
    if bot.pool is not None:
        bot.guild_cache.remove_local(event.guild_id)
        logger.info(f"Bot left guild '{event.guild_id}'. Cache entry removed.")

@plugin.listener(hikari.GuildMessageCreateEvent)
async def on_guild_message(event: hikari.GuildMessageCreateEvent):
    msg = event.message
    if msg.author.is_bot or event.guild_id != 868449475323101224:
        return

@plugin.listener(lightbulb.CommandCompletionEvent)
async def on_command_complete(event: lightbulb.CommandCompletionEvent):
    # This event is not needed when concurrency can be handled correctly by the lib.
    bot: models.MichaelBot = event.app
    command = event.command
    # Remove concurrency
    if command.max_concurrency:
        bot.custom_command_concurrency_session.release_session(event.context)

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
