import lightbulb
import hikari
import asyncpg

import utilities.helpers as helpers
import utilities.checks as checks
import utilities.psql as psql
from utilities.checks import is_dev

plugin = lightbulb.Plugin("Secret", "Developer-only commands.", include_datastore = True)
plugin.d.emote = helpers.get_emote(":computer:")
plugin.add_checks(is_dev, checks.is_command_enabled, lightbulb.bot_has_guild_permissions(*helpers.COMMAND_STANDARD_PERMISSIONS))

@plugin.command()
@lightbulb.option("guild", "Guild to blacklist (recommend ID).", type = hikari.Guild)
@lightbulb.command("blacklist-guild", "Blacklist a guild.", hidden = True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def blacklist_guild(ctx: lightbulb.Context):
    guild_id = 0
    if isinstance(ctx, lightbulb.SlashContext):
        guild = await lightbulb.converters.GuildConverter(ctx).convert(ctx.options.guild)
        guild_id = guild.id
    else:
        guild_id = ctx.options.guild.id
    
    async with ctx.bot.d.pool.acquire() as conn:
        async with conn.transaction():
            await psql.guilds.update_column(conn, guild_id, "is_whitelist", False)
    
    await ctx.respond("Blacklisted!", reply = True)

@plugin.command()
@lightbulb.command("purge-slashes", "Force delete every slash commands in test guilds.", hidden = True)
@lightbulb.implements(lightbulb.PrefixCommand)
async def purge_slashes(ctx: lightbulb.Context):
    await ctx.bot.purge_application_commands(*ctx.bot.d.bot_info["default_guilds"])
    await ctx.respond("Cleared all slash commands in test guilds. Restart the bot to see them again.", reply = True)

@plugin.command()
@lightbulb.option("extension", "The extension to reload.")
@lightbulb.command("reload", "Reload an extension.", hidden = True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def reload(ctx: lightbulb.Context):
    ctx.bot.reload_extensions(ctx.options.extension)
    await ctx.respond(f"Reloaded extension {ctx.options.extension}.", reply = True)
@reload.set_error_handler()
async def reload_error(event: lightbulb.CommandErrorEvent):
    exception = event.exception.__cause__ or event.exception
    if isinstance(exception, lightbulb.ExtensionNotFound):
        await event.context.respond("This extension does not exist.", reply = True, mentions_reply = True)

@plugin.command()
@lightbulb.command("shutdown", "Shut the bot down.", hidden = True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def shutdown(ctx: lightbulb.Context):
    await ctx.respond("Bot shutting down...")
    await ctx.bot.close()

@plugin.command()
@lightbulb.command("test", "test", hidden = True)
@lightbulb.implements(lightbulb.PrefixCommand)
async def test(ctx: lightbulb.Context):
    async with ctx.bot.d.pool.acquire() as conn:
        guild = await psql.guilds.get_one(conn, ctx.guild_id)
        await psql.guilds.update_column(conn, ctx.guild_id, "prefix", "%")

def load(bot):
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
