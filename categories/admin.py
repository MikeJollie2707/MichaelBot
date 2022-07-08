'''Developer-only commands.'''

import datetime as dt

import hikari
import lightbulb

from utils import checks, helpers, models, psql
from utils.checks import is_dev

plugin = lightbulb.Plugin("Secret", "Developer-only commands.", include_datastore = True)
plugin.d.emote = helpers.get_emote(":computer:")
plugin.add_checks(is_dev, checks.is_command_enabled, lightbulb.bot_has_guild_permissions(*helpers.COMMAND_STANDARD_PERMISSIONS))

@plugin.command()
@lightbulb.option("guild", "Guild to blacklist (recommend ID).", type = hikari.Guild)
@lightbulb.command("blacklist-guild", "Blacklist a guild.", hidden = True)
@lightbulb.implements(lightbulb.PrefixCommand)
async def blacklist_guild(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot
    
    guild_id = 0
    if isinstance(ctx, lightbulb.SlashContext):
        guild = await lightbulb.converters.GuildConverter(ctx).convert(ctx.options.guild)
        if guild is not None:
            guild_id = guild.id
        else:
            await ctx.respond("Guild not found.", reply = True, mentions_reply = True)
            return
    else:
        guild_id = ctx.options.guild.id
    
    async with bot.pool.acquire() as conn:
        async with conn.transaction():
            guild_cache = bot.guild_cache.get(guild_id)
            if guild_cache is None:
                guild_db = await psql.Guild.get_one(conn, guild_id)
                if guild_db is None:
                    await ctx.respond("Can't blacklist a guild that's not available in guild.", reply = True, mentions_reply = True)
                    return
                else:
                    guild_cache = models.GuildCache()
                    await guild_cache.force_sync(conn, guild_id)
            
            await guild_cache.update_guild_module(conn, guild_id, "is_whitelist", False)
    
    await ctx.respond("Blacklisted!", reply = True)

@plugin.command()
@lightbulb.option("user", "User to blacklist (recommend ID). Must be available in database.", type = hikari.User)
@lightbulb.command("blacklist-user", "Blacklist a user.", hidden = True)
@lightbulb.implements(lightbulb.PrefixCommand)
async def blacklist_user(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot
    
    user_id = 0
    if isinstance(ctx, lightbulb.SlashContext):
        user = await lightbulb.converters.UserConverter(ctx).convert(ctx.options.user)
        if user is not None:
            user_id = user.id
        else:
            await ctx.respond("User not found.", reply = True, mentions_reply = True)
            return
    else:
        user_id = ctx.options.user.id
    
    if user_id == 472832990012243969:
        await ctx.respond("Sorry, can't blacklist my bot owner. That's not a thing.", reply = True, mentions_reply = True)
        return
    
    async with bot.pool.acquire() as conn:
        async with conn.transaction():
            user_cache = bot.user_cache.get(user_id)
            if user_cache is None:
                user_db = await psql.User.get_one(conn, user_id)
                if user_db is None:
                    await ctx.respond("Can't blacklist a user that's not available in database.", reply = True, mentions_reply = True)
                    return
                else:
                    user_cache = models.UserCache()
                    await user_cache.force_sync(conn, user_id)
            
            await user_cache.update_user_module(conn, user_id, "is_whitelist", False)
    
    await ctx.respond("Blacklisted!", reply = True)

@plugin.command()
@lightbulb.command("count-slashes", "Count all registered slash commands.", hidden = True)
@lightbulb.implements(lightbulb.PrefixCommand)
async def count_slashes(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    count: int = 0
    for s_cmd in bot.slash_commands.values():
        count += 1
        print(s_cmd.qualname)
        if isinstance(s_cmd, (lightbulb.PrefixCommandGroup, lightbulb.SlashCommandGroup)):
            for sub_cmd in s_cmd.subcommands.values():
                count += 1
                print(sub_cmd.qualname)
    
    await ctx.respond(f"There are {count} slash commands (View details in terminal).", reply = True)

@plugin.command()
@lightbulb.command("force-sync-cache", "Force update the cache with the current data in database.", hidden = True)
@lightbulb.implements(lightbulb.PrefixCommandGroup)
async def force_sync_cache(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    async with bot.pool.acquire() as conn:
        async with conn.transaction():
            guilds = await psql.Guild.get_all(conn)
            for guild in guilds:
                #guild_id = guild["id"]
                guild_id = guild.id
                bot.guild_cache[guild_id] = models.GuildCache()
                await bot.guild_cache[guild_id].force_sync(conn, guild_id)
            
            users = await psql.User.get_all(conn)
            for user in users:
                #user_id = user["id"]
                user_id = user.id
                bot.user_cache[user_id] = models.UserCache()
                await bot.user_cache[user_id].force_sync(conn, user_id)
    
    await ctx.respond("Cache is now sync to the database.", reply = True)

@force_sync_cache.child
@lightbulb.option("user_id", "The user's id to sync.", type = hikari.User)
@lightbulb.command("user", "Force update the user's cache with the current data in database.", hidden = True)
@lightbulb.implements(lightbulb.PrefixSubCommand)
async def force_sync_cache_user(ctx: lightbulb.Context):
    user_id = ctx.options.user_id.id
    bot: models.MichaelBot = ctx.bot

    async with bot.pool.acquire() as conn:
        async with conn.transaction():
            bot.user_cache[user_id] = models.UserCache()
            await bot.user_cache[user_id].force_sync(conn, user_id)
    
    await ctx.respond(f"User cache for {ctx.options.user_id} synced.", reply = True)

@force_sync_cache.child
@lightbulb.option("guild_id", "The guild's id to sync.", type = hikari.Guild)
@lightbulb.command("guild", "Force update the guild's cache with the current data in database.", hidden = True)
@lightbulb.implements(lightbulb.PrefixSubCommand)
async def force_sync_cache_guild(ctx: lightbulb.Context):
    guild_id = ctx.options.guild_id.id
    bot: models.MichaelBot = ctx.bot

    async with bot.pool.acquire() as conn:
        async with conn.transaction():
            bot.guild_cache[guild_id] = models.GuildCache()
            await bot.guild_cache[guild_id].force_sync(conn, guild_id)
    
    await ctx.respond(f"Guild cache for {ctx.options.guild_id} synced.", reply = True)

@plugin.command()
@lightbulb.command("cache-view", "View the cache content.", hidden = True)
@lightbulb.implements(lightbulb.PrefixCommandGroup)
async def cache_view(ctx: lightbulb.Context):
    raise lightbulb.CommandNotFound(invoked_with = ctx.invoked_with)

@cache_view.child
@lightbulb.option("guild_id", "The guild's id to view.", type = hikari.Guild)
@lightbulb.command("guild", "View the cache of a guild.", hidden = True)
@lightbulb.implements(lightbulb.PrefixSubCommand)
async def cache_view_guild(ctx: lightbulb.Context):
    guild_id = ctx.options.guild_id.id
    bot: models.MichaelBot = ctx.bot

    guild_cache = bot.guild_cache.get(guild_id)
    if guild_cache is not None:
        embed = helpers.get_default_embed(
            title = "Guild Cache View",
            author = ctx.author,
            timestamp = dt.datetime.now().astimezone()
        ).add_field(
            name = "Guild Module",
            value = f"```{guild_cache.guild_module}```"
        ).add_field(
            name = "Logging Module",
            value = f"```{guild_cache.logging_module}```"
        )
        await ctx.respond(embed = embed, reply = True)
    else:
        await ctx.respond("Cache for this guild doesn't exist.", reply = True, mentions_reply = True)

@cache_view.child
@lightbulb.option("item_id", "The item's id to view.")
@lightbulb.command("item", "View the cache of an item.", hidden = True)
@lightbulb.implements(lightbulb.PrefixSubCommand)
async def cache_view_item(ctx: lightbulb.Context):
    item_id = ctx.options.item_id
    bot: models.MichaelBot = ctx.bot

    item_cache = bot.item_cache.get(item_id)
    if item_cache is not None:
        embed = helpers.get_default_embed(
            title = "Item Cache View",
            author = ctx.author,
            timestamp = dt.datetime.now().astimezone()
        ).add_field(
            name = "Guild Module",
            value = f"```{item_cache.item_module}```"
        )
        await ctx.respond(embed = embed, reply = True)
    else:
        await ctx.respond("Cache for this item doesn't exist.", reply = True, mentions_reply = True)

@plugin.command()
@lightbulb.command("purge-guild-slashes", "Force delete every slash commands in test guilds.", hidden = True)
@lightbulb.implements(lightbulb.PrefixCommand)
async def purge_guild_slashes(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    async with bot.rest.trigger_typing(ctx.channel_id):
        await bot.purge_application_commands(*bot.info["default_guilds"])
    await ctx.respond("Cleared all guild slash commands in test guilds.", reply = True)

@plugin.command()
@lightbulb.command("purge-slashes", "Force delete every slash commands.", hidden = True)
@lightbulb.implements(lightbulb.PrefixCommand)
async def purge_slashes(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    async with bot.rest.trigger_typing(ctx.channel_id):
        await bot.purge_application_commands(global_commands = True)
    await ctx.respond("Cleared all application commands from all guilds.", reply = True)

@plugin.command()
@lightbulb.option("extension", "The extension to reload.")
@lightbulb.command("reload", "Reload an extension.", hidden = True)
@lightbulb.implements(lightbulb.PrefixCommand)
async def reload(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    bot.reload_extensions(ctx.options.extension)
    await ctx.respond(f"Reloaded extension {ctx.options.extension}.", reply = True)
@reload.set_error_handler()
async def reload_error(event: lightbulb.CommandErrorEvent):
    exception = event.exception
    # Unwrap exception.
    if isinstance(event.exception, lightbulb.CommandInvocationError):
        exception = exception.__cause__
    
    if isinstance(exception, lightbulb.ExtensionNotFound):
        await event.context.respond("This extension does not exist.", reply = True, mentions_reply = True)
    elif isinstance(exception, lightbulb.ExtensionNotLoaded):
        await event.context.respond("This extension is not found or is not loaded.", reply = True, mentions_reply = True)
    return True

@plugin.command()
@lightbulb.command("shutdown", "Shut the bot down.", hidden = True)
@lightbulb.implements(lightbulb.PrefixCommand)
async def shutdown(ctx: lightbulb.Context):
    await ctx.respond("Bot shutting down...")
    await ctx.bot.close()

def load(bot: models.MichaelBot):
    bot.add_plugin(plugin)
def unload(bot: models.MichaelBot):
    bot.remove_plugin(plugin)
