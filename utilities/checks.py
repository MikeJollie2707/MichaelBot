import lightbulb
import hikari

import utilities.helpers as helpers
import utilities.models as models
import utilities.errors as errors
import utilities.psql as psql

@lightbulb.Check
def is_dev(ctx: lightbulb.Context) -> bool:
    if ctx.author.id not in [472832990012243969, 462726152377860109]: raise errors.CustomCheckFailed("`Author must be a MichaelBot developer`")
    return True

@lightbulb.Check
async def is_command_enabled(ctx: lightbulb.Context) -> bool:
    guild_cache = models.get_guild_cache(ctx.bot, ctx.guild_id)
    user_cache = models.get_user_cache(ctx.bot, ctx.author.id)

    if guild_cache is None:
        guild_cache = models.GuildCache()
        async with ctx.bot.d.pool.acquire() as conn:
            async with conn.transaction():
                guild = await psql.Guilds.get_one(conn, ctx.guild_id)
                if guild is None:
                    await guild_cache.add_guild_module(conn, ctx.get_guild())
                else:
                    await guild_cache.force_sync(conn, ctx.author.id)
    if user_cache is None:
        user_cache = models.UserCache()
        async with ctx.bot.d.pool.acquire() as conn:
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
