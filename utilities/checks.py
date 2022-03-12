import lightbulb
import hikari

import utilities.errors as errors
import utilities.psql as psql

@lightbulb.Check
def is_dev(ctx: lightbulb.Context) -> bool:
    if ctx.author.id not in [472832990012243969, 462726152377860109]: raise errors.CustomCheckFailed("`Author must be a MichaelBot developer`")
    return True

@lightbulb.Check
async def is_guild_enabled(ctx: lightbulb.Context) -> bool:
    async with ctx.bot.d.pool.acquire() as conn:
        guild = await psql.guilds.get_one(conn, ctx.guild_id)
        if guild is None:
            return True
        
        if not guild["is_whitelist"]:
            raise errors.GuildBlacklisted
        
    return True
