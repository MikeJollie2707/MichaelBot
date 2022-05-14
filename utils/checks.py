'''Custom checks for various commands.'''

import lightbulb

import utils.errors as errors
import utils.models as models
import utils.psql as psql

@lightbulb.Check
def is_dev(ctx: lightbulb.Context) -> bool:
    '''
    Check if the user invoked is a MichaelBot developer.

    Exceptions:
    - `errors.CustomCheckFailed`: The user is not a MichaelBot developer.
    '''
    if ctx.author.id not in [472832990012243969, 462726152377860109]: raise errors.CustomCheckFailed("`Author must be a MichaelBot developer`")
    return True

@lightbulb.Check
async def is_command_enabled(ctx: lightbulb.Context) -> bool:
    '''
    Check if a command is enabled in a given context.
    This will also add and/or sync the cache if necessary.

    Exceptions:
    - `lightbulb.OnlyInGuild`: The context is not in a guild.
    - `errors.GuildBlacklisted`: The guild the context is in is blacklisted.
    - `errors.UserBlacklisted`: The user invoked is blacklisted.
    '''

    bot: models.MichaelBot = ctx.bot
    if ctx.guild_id is None:
        raise lightbulb.OnlyInGuild
    
    # A db-existing check should be separated.
    if bot.pool is None:
        return True
    
    guild_cache = bot.guild_cache.get(ctx.guild_id)
    user_cache = bot.user_cache.get(ctx.author.id)

    if guild_cache is None:
        guild_cache = models.GuildCache()
        async with bot.pool.acquire() as conn:
            async with conn.transaction():
                guild = await psql.Guilds.get_one(conn, ctx.guild_id)
                if guild is None:
                    await guild_cache.add_guild_module(conn, ctx.get_guild())
                else:
                    await guild_cache.force_sync(conn, ctx.author.id)
    if user_cache is None:
        user_cache = models.UserCache()
        async with bot.pool.acquire() as conn:
            async with conn.transaction():
                user = await psql.Users.get_one(conn, ctx.author.id)
                if user is None:
                    await user_cache.add_user_module(conn, ctx.author)
                else:
                    await user_cache.force_sync(conn, ctx.author.id)
    
    if not guild_cache.guild_module["is_whitelist"]:
        raise errors.GuildBlacklisted
    if not user_cache.user_module["is_whitelist"]:
        raise errors.UserBlacklisted
        
    return True

@lightbulb.Check
def is_db_connected(ctx: lightbulb.Context) -> bool:
    '''
    Check if a database connection pool is available.
    This must be checked on commands that uses connection pool.

    Exception:
    - `errors.NoDatabase`: The bot doesn't have a database connection pool.
    '''
    bot: models.MichaelBot = ctx.bot
    if bot.pool is None:
        raise errors.NoDatabase
    return True

@lightbulb.Check
def is_aiohttp_existed(ctx: lightbulb.Context) -> bool:
    '''
    Check if a http client is available.
    This must be checked on commands that uses http methods.

    Exception:
    - `errors.NoHTTPClient`: The bot doesn't have a http client.
    '''
    bot: models.MichaelBot = ctx.bot
    if bot.aio_session is None:
        raise errors.NoHTTPClient
    return True
