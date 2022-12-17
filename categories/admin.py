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
        guild_cache = bot.guild_cache.get(guild_id)
        if guild_cache is None:
            guild = await psql.Guild.fetch_one(conn, id = guild_id)
            if guild is None:
                await ctx.respond("Can't blacklist a guild that's not available in database.", reply = True, mentions_reply = True)
                return
            
            bot.guild_cache.update_local(guild)
            guild_cache = guild
        
        guild_cache.is_whitelist = False
        await bot.guild_cache.update(conn, guild_cache)
    
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
        user_cache = bot.user_cache.get(user_id)
        if user_cache is None:
            user = await psql.User.fetch_one(conn, id = user_id)
            if user is None:
                await ctx.respond("Can't blacklist a user that's not available in database.", reply = True, mentions_reply = True)
                return
            
            bot.user_cache.update_local(user)
            user_cache = user
        
        user_cache.is_whitelist = False
        await bot.user_cache.update(conn, user_cache)
    
    await ctx.respond("Blacklisted!", reply = True)

@plugin.command()
@lightbulb.command("count-slashes", "Count all registered slash commands.", hidden = True)
@lightbulb.implements(lightbulb.PrefixCommand)
async def count_slashes(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    count: int = 0
    # TODO: Group this into categories so it's less painful to look at.
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
            guilds = await psql.Guild.fetch_all(conn)
            for guild in guilds:
                bot.guild_cache.update_local(guild)
            
            logs = await psql.GuildLog.fetch_all(conn)
            for log in logs:
                bot.log_cache.update_local(log)
            
            users = await psql.User.fetch_all(conn)
            for user in users:
                bot.user_cache.update_local(user)
    
    await ctx.respond("Cache is now sync to the database.", reply = True)

@force_sync_cache.child
@lightbulb.option("user_id", "The user's id to sync.", type = hikari.User)
@lightbulb.command("user", "Force update the user's cache with the current data in database.", hidden = True)
@lightbulb.implements(lightbulb.PrefixSubCommand)
async def force_sync_cache_user(ctx: lightbulb.Context):
    user_id = ctx.options.user_id.id
    bot: models.MichaelBot = ctx.bot

    async with bot.pool.acquire() as conn:
        await bot.user_cache.update_from_db(conn, user_id)
    
    await ctx.respond(f"User cache for {ctx.options.user_id} synced.", reply = True)

@force_sync_cache.child
@lightbulb.option("guild_id", "The guild's id to sync.", type = hikari.Guild)
@lightbulb.command("guild", "Force update the guild's cache with the current data in database.", hidden = True)
@lightbulb.implements(lightbulb.PrefixSubCommand)
async def force_sync_cache_guild(ctx: lightbulb.Context):
    guild_id = ctx.options.guild_id.id
    bot: models.MichaelBot = ctx.bot

    async with bot.pool.acquire() as conn:
        await bot.guild_cache.update_from_db(conn, guild_id)
        await bot.log_cache.update_from_db(conn, guild_id)
    
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
            value = f"```{psql.asdict(guild_cache)}```"
        )
        await ctx.respond(embed = embed, reply = True)
    else:
        await ctx.respond("Cache for this guild doesn't exist.", reply = True, mentions_reply = True)

@cache_view.child
@lightbulb.option("guild_id", "The guild's id to view.", type = hikari.Guild)
@lightbulb.command("log", "View the cache of a guild.", hidden = True)
@lightbulb.implements(lightbulb.PrefixSubCommand)
async def cache_view_log(ctx: lightbulb.Context):
    guild_id = ctx.options.guild_id.id
    bot: models.MichaelBot = ctx.bot

    log_cache = bot.log_cache.get(guild_id)
    if log_cache is not None:
        embed = helpers.get_default_embed(
            title = "Log Cache View",
            author = ctx.author,
            timestamp = dt.datetime.now().astimezone()
        ).add_field(
            name = "Log Module",
            value = f"```{psql.asdict(log_cache)}```"
        )
        await ctx.respond(embed = embed, reply = True)
    else:
        await ctx.respond("Cache for this guild doesn't exist.", reply = True, mentions_reply = True)

@cache_view.child
@lightbulb.option("user_id", "The user's id.", type = hikari.User)
@lightbulb.command("user", "View the cache of a user.", hidden = True)
@lightbulb.implements(lightbulb.PrefixSubCommand)
async def cache_view_user(ctx: lightbulb.Context):
    user_id = ctx.options.user_id.id
    bot: models.MichaelBot = ctx.bot

    user_cache = bot.user_cache.get(user_id)
    if user_cache is not None:
        embed = helpers.get_default_embed(
            title = "User Cache View",
            author = ctx.author,
            timestamp = dt.datetime.now().astimezone()
        ).add_field(
            name = "User Module",
            value = f"```{psql.asdict(user_cache)}```"
        )
        await ctx.respond(embed = embed, reply = True)
    else:
        await ctx.respond("Cache for this user doesn't exist.", reply = True, mentions_reply = True)

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
            name = "Item Module",
            value = f"```{psql.asdict(item_cache)}```"
        )
        await ctx.respond(embed = embed, reply = True)
    else:
        await ctx.respond("Cache for this item doesn't exist.", reply = True, mentions_reply = True)

@plugin.command()
@lightbulb.option("value_name", "The value's exact name. This should exist in either loot.py or trader.py")
@lightbulb.command("get-econ-value", "Display secret values of economy setting.", hidden = True)
@lightbulb.implements(lightbulb.PrefixCommand)
async def get_econ_value(ctx: lightbulb.Context):
    from categories.econ import loot, trader
    value_name = ctx.options.value_name

    value = loot.__dict__.get(value_name)
    if not value:
        value = trader.__dict__.get(value_name)
    
    await ctx.respond(f"```{value}```", reply = True)

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
@lightbulb.option("command", "The command to reset.")
@lightbulb.command("reset-cooldown", "Reset a command's cooldown. This only resets soft cooldown.", hidden = True)
@lightbulb.implements(lightbulb.PrefixCommand)
async def reset_cooldown(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    commands: list[lightbulb.Command] = []
    commands.append(bot.get_prefix_command(ctx.options.command))
    commands.append(bot.get_slash_command(ctx.options.command))
    commands.append(bot.get_message_command(ctx.options.command))
    commands.append(bot.get_user_command(ctx.options.command))

    for command in commands:
        if command is not None:
            if command.cooldown_manager is not None:
                # Cooldown is shared among all types of command, so erase once is enough.
                await command.cooldown_manager.reset_cooldown(ctx)
                break
    await ctx.respond(f"Reset `{ctx.options.command}` cooldown.", reply = True)

@plugin.command()
@lightbulb.command("shutdown", "Shut the bot down.", hidden = True)
@lightbulb.implements(lightbulb.PrefixCommand)
async def shutdown(ctx: lightbulb.Context):
    await ctx.respond("Bot shutting down...")
    await ctx.bot.close()

@plugin.command()
@lightbulb.option("badge_id2", "The badge you're trying to update.")
@lightbulb.option("badge_id1", "The badge you're getting the progress.")
@lightbulb.command("sync-badge-progress", "Update a badge progress with another badge progress for all users. Useful when adding new tiers of badges.", hidden = True)
@lightbulb.implements(lightbulb.PrefixCommand)
async def sync_badge_progress(ctx: lightbulb.Context):
    badge_id1 = ctx.options.badge_id1
    badge_id2 = ctx.options.badge_id2
    bot: models.MichaelBot = ctx.bot

    async with bot.pool.acquire() as conn:
        async with conn.transaction():
            for user_id in bot.user_cache.keys():
                badge1 = await psql.UserBadge.fetch_one(conn, user_id = user_id, badge_id = badge_id1)
                badge2 = await psql.UserBadge.fetch_one(conn, user_id = user_id, badge_id = badge_id2)

                if not badge1:
                    print(f"User {user_id} doesn't have {badge_id1}. Skipping...")
                    continue

                if not badge2:
                    await psql.UserBadge.add_progress(conn, user_id, badge_id2, badge1.badge_progress)
                else:
                    await psql.UserBadge.update_column(conn, {"badge_progress": badge1.badge_progress}, user_id = user_id, badge_id = badge_id2)
    
    await ctx.respond("Finished syncing!", reply = True)

def load(bot: models.MichaelBot):
    bot.add_plugin(plugin)
def unload(bot: models.MichaelBot):
    bot.remove_plugin(plugin)
