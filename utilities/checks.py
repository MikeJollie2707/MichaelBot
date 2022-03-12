import lightbulb
import hikari

import utilities.errors as errors

@lightbulb.Check
def is_dev(ctx: lightbulb.Context) -> bool:
    if ctx.author.id not in [472832990012243969, 462726152377860109]: raise errors.CustomCheckFailed("`Author must be a MichaelBot developer`")
    return True

@lightbulb.Check
async def is_guild_enabled(ctx: lightbulb.Context) -> bool:
    #if ctx.guild_id in [868449475323101224]:
    #    raise errors.GuildBlacklisted
    return True
