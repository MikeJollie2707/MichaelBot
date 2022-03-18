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
            guild_cache = models.get_guild_cache(ctx.bot, ctx.guild_id)
            await guild_cache.update_guild_module(conn, guild_id, "is_whitelist", False)
    
    await ctx.respond("Blacklisted!", reply = True)

@plugin.command()
@lightbulb.option("user", "User to blacklist (recommend ID). Must be available in database.", type = hikari.User)
@lightbulb.command("blacklist-user", "Blacklist a user.", hidden = True)
@lightbulb.implements(lightbulb.PrefixCommand)
async def blacklist_user(ctx: lightbulb.Context):
    user_id = 0
    if isinstance(ctx, lightbulb.SlashContext):
        user = await lightbulb.converters.UserConverter(ctx).convert(ctx.options.user)
        user_id = user.id
    else:
        user_id = ctx.options.user.id
    
    if user_id == 472832990012243969:
        await ctx.respond("Sorry, can't blacklist my bot owner. That's not a thing.", reply = True, mentions_reply = True)
        return
    
    async with ctx.bot.d.pool.acquire() as conn:
        async with conn.transaction():
            user_cache = models.get_user_cache(ctx.bot, ctx.guild_id)
            if user_cache is None:
                user_db = await psql.Users.get_one(conn, user_id)
                if user_db is None:
                    await ctx.respond("Can't blacklist a user that's not available in database.", reply = True, mentions_reply = True)
                    return
                else:
                    user_cache = models.UserCache()
                    await user_cache.force_sync(conn, user_id)
            
            await user_cache.update_user_module(conn, user_id, "is_whitelist", False)
    
    await ctx.respond("Blacklisted!", reply = True)

@plugin.command()
@lightbulb.command("force-sync-cache", "Force update the cache with the current data in database.", hidden = True)
@lightbulb.implements(lightbulb.PrefixCommandGroup)
async def force_sync_cache(ctx: lightbulb.Context):
    async with ctx.bot.d.pool.acquire() as conn:
        async with conn.transaction():
            guilds = await psql.Guilds.get_all(conn)
            for guild in guilds:
                guild_id = guild["id"]
                ctx.bot.d.guild_cache[guild_id] = models.GuildCache()
                guild_cache = models.get_guild_cache(ctx.bot, guild_id)
                await guild_cache.force_sync(conn, guild_id)
            
            users = await psql.Users.get_all(conn)
            for user in users:
                user_id = user["id"]
                ctx.bot.d.user_cache[user_id] = models.UserCache()
                user_cache = models.get_user_cache(ctx.bot, user_id)
                await user_cache.force_sync(conn, user_id)
    
    await ctx.respond("Cache is now sync to the database.", reply = True)

@force_sync_cache.child
@lightbulb.option("user_id", "The user's id to sync.", type = hikari.User)
@lightbulb.command("user", "Force update the user's cache with the current data in database.", hidden = True)
@lightbulb.implements(lightbulb.PrefixSubCommand)
async def force_sync_cache_user(ctx: lightbulb.Context):
    user_id = ctx.options.user_id.id

    async with ctx.bot.d.pool.acquire() as conn:
        async with conn.transaction():
            ctx.bot.d.user_cache[user_id] = models.UserCache()
            user_cache = models.get_user_cache(ctx.bot, user_id)
            await user_cache.force_sync(conn, user_id)
    
    await ctx.respond(f"User cache for {ctx.options.user_id} synced.", reply = True)

@force_sync_cache.child
@lightbulb.option("guild_id", "The guild's id to sync.", type = hikari.Guild)
@lightbulb.command("guild", "Force update the guild's cache with the current data in database.", hidden = True)
@lightbulb.implements(lightbulb.PrefixSubCommand)
async def force_sync_cache_guild(ctx: lightbulb.Context):
    guild_id = ctx.options.guild_id.id

    async with ctx.bot.d.pool.acquire() as conn:
        async with conn.transaction():
            ctx.bot.d.guild_cache[guild_id] = models.GuildCache()
            guild_cache = models.get_guild_cache(ctx.bot, guild_id)
            await guild_cache.force_sync(conn, guild_id)
    
    await ctx.respond(f"Guild cache for {ctx.options.guild_id} synced.", reply = True)

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
