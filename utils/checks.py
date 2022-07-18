'''Custom checks for various commands.'''

import lightbulb

from utils import errors, models, psql

@lightbulb.Check
def is_dev(ctx: lightbulb.Context) -> bool:
    '''
    Check if the user invoked is a MichaelBot developer.

    Exceptions:
    - `errors.CustomCheckFailed`: The user is not a MichaelBot developer.
    '''
    if ctx.author.id not in [472832990012243969, 462726152377860109]:
        raise errors.CustomCheckFailed("`Author must be a MichaelBot developer`")
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

    if guild_cache is None or user_cache is None:
        async with bot.pool.acquire() as conn:
            # Checking cache to sync if needed.
            if guild_cache is None:
                guild = await psql.Guild.get_one(conn, ctx.guild_id)
                if guild is None:
                    guild = psql.Guild(ctx.guild_id, ctx.get_guild().name)
                    await bot.guild_cache.insert(conn, guild)
                else:
                    bot.guild_cache.sync_local(guild)
                
                guild_cache = guild
            
            if user_cache is None:
                user = await psql.User.get_one(conn, ctx.author.id)
                if user is None:
                    user = psql.User(ctx.author.id, ctx.author.username)
                    await bot.user_cache.insert(conn, user)
                else:
                    bot.user_cache.local_sync(user)
                
                user_cache = user
    
    if not guild_cache.is_whitelist:
        raise errors.GuildBlacklisted
    if not user_cache.is_whitelist:
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
