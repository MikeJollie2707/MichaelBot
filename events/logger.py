import datetime as dt
from io import StringIO
from textwrap import dedent

import hikari
import humanize
import lightbulb
import mystbin

from utils import checks, helpers, models, psql

EVENT_OPTION_MAPPING = {
    hikari.GuildChannelCreateEvent: "guild_channel_create",
    hikari.GuildChannelDeleteEvent: "guild_channel_delete",
    hikari.GuildChannelUpdateEvent: "guild_channel_update",
    hikari.BanCreateEvent: "guild_ban",
    hikari.BanDeleteEvent: "guild_unban",
    hikari.GuildUpdateEvent: "guild_update",
    hikari.MemberCreateEvent: "member_join",
    hikari.MemberDeleteEvent: "member_leave",
    hikari.MemberUpdateEvent: "member_update",
    hikari.GuildBulkMessageDeleteEvent: "guild_bulk_message_delete",
    hikari.GuildMessageDeleteEvent: "guild_message_delete",
    hikari.GuildMessageUpdateEvent: "guild_message_update",
    hikari.RoleCreateEvent: "role_create",
    hikari.RoleDeleteEvent: "role_delete",
    hikari.RoleUpdateEvent: "role_update",
    
    # Since lightbulb events have hierachy and stuffs we need to map all of them (or at least the one we use)
    lightbulb.PrefixCommandCompletionEvent: "command_complete",
    lightbulb.SlashCommandCompletionEvent: "command_complete",
    lightbulb.PrefixCommandErrorEvent: "command_error",
    lightbulb.SlashCommandErrorEvent: "command_error"
}

command_event_choices = list(EVENT_OPTION_MAPPING.values())
# Hard-code this shit lmao
command_event_choices.remove("command_complete")
command_event_choices.remove("command_error")

COLOR_MODERATION = models.DefaultColor.black
COLOR_CREATE = models.DefaultColor.green
COLOR_DELETE = models.DefaultColor.orange
COLOR_UPDATE = models.DefaultColor.yellow
COLOR_OTHER = models.DefaultColor.teal

def bot_has_permission_in(bot: models.MichaelBot, channel: hikari.GuildChannel, permission: hikari.Permissions):
    bot_permissions = lightbulb.utils.permissions_in(channel, bot.cache.get_member(channel.get_guild().id, bot.get_me().id), True)
    return bot_permissions & permission == permission

def is_loggable(event: hikari.Event):
    bot: models.MichaelBot = event.app
    # Since most events we're logging are guild-related, they all have `.get_guild()` method.
    if isinstance(event, hikari.RoleEvent):
        guild = bot.cache.get_guild(event.guild_id)
    elif isinstance(event, lightbulb.CommandCompletionEvent) or isinstance(event, lightbulb.CommandErrorEvent):
        guild = event.context.get_guild()
    else:
        guild = event.get_guild()
    
    # Hikari cache is empty.
    if guild is None: return False
    
    log_cache = bot.log_cache.get(guild.id)

    if log_cache is None: return False
    if type(event) not in EVENT_OPTION_MAPPING: return False
    if log_cache.log_channel is None: return False
    if getattr(log_cache, EVENT_OPTION_MAPPING[type(event)]) is None: return False

    channel = bot.cache.get_guild_channel(log_cache.log_channel)
    if channel is None: return False

    is_text_channel = channel.type == hikari.ChannelType.GUILD_TEXT
    has_send_message = bot_has_permission_in(bot, channel, hikari.Permissions.SEND_MESSAGES)
    option_enabled = getattr(log_cache, EVENT_OPTION_MAPPING[type(event)])

    return is_text_channel and has_send_message and option_enabled

plugin = lightbulb.Plugin("Logs", "Logging Commands", include_datastore = True)
plugin.d.emote = helpers.get_emote(":memo:")
plugin.add_checks(
    checks.is_db_connected,
    checks.is_command_enabled,
    lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_GUILD),
    lightbulb.bot_has_guild_permissions(*helpers.COMMAND_STANDARD_PERMISSIONS)
)

@plugin.command()
@lightbulb.set_help(dedent('''
    - Author needs to have `Manage Server`.
'''))
@lightbulb.option("channel", "The Discord channel to dump all the logs. Default to current channel.", 
    type = hikari.TextableGuildChannel, 
    channel_types = (hikari.ChannelType.GUILD_TEXT,), 
    default = None
)
@lightbulb.command("log-enable", f"[{plugin.name}] Set a channel to dump all the logs. This automatically enables logging system.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def log_enable(ctx: lightbulb.Context):
    channel = ctx.options.channel
    bot: models.MichaelBot = ctx.bot

    if channel is None:
        channel = ctx.get_channel()
    
    # If it's invoked thru slash command.
    if isinstance(channel, hikari.InteractionChannel):
        channel = ctx.get_guild().get_channel(channel.id)
    
    if not bot_has_permission_in(bot, channel, hikari.Permissions.SEND_MESSAGES):
        await ctx.respond(f"{channel.mention} doesn't allow me to send a message!", reply = True, mentions_reply = True)
        return

    async with bot.pool.acquire() as conn:
        log_cache = bot.log_cache.get(ctx.guild_id)
        if log_cache is None:
            existed = await psql.GuildLog.get_one(conn, ctx.guild_id)
            if existed is None:
                existed = psql.GuildLog(ctx.guild_id, channel.id)
                await bot.log_cache.insert(conn, existed)
            else:
                bot.log_cache.update_local(existed)
            
            log_cache = existed
        
        log_cache.log_channel = channel
        await bot.log_cache.update(conn, log_cache)
            
    
    await ctx.respond(f"Set channel {channel.mention} as a logging channel.", reply = True)
    await bot.rest.create_message(channel, "This channel is now mine to log, muahahahaha!")

@plugin.command()
@lightbulb.set_help(dedent('''
    - Author needs to have `Manage Server`.
'''))
@lightbulb.command("log-disable", f"[{plugin.name}] Disable logging or part of the logging system.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def log_disable(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot
    
    log_cache = bot.log_cache.get(ctx.guild_id)
    if log_cache is not None:
        log_cache.log_channel = None
        async with bot.pool.acquire() as conn:
            await bot.log_cache.update(conn, log_cache)
    else:
        await ctx.respond("Logging is already disabled.", reply = True, mentions_reply = True)
        return

    await ctx.respond("Logging disabled successfully.", reply = True)

@plugin.command()
@lightbulb.set_help(dedent('''
    - Author needs to have `Manage Server`.
    - It is recommended to use the `Slash Command` version of the command.
'''))
@lightbulb.option("logging_option", "Log type to toggle. Check `log-view` to see all options.", choices = command_event_choices)
@lightbulb.command("log-option-toggle", f"[{plugin.name}] Toggle individual logging option.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def log_option_toggle(ctx: lightbulb.Context):
    logging_option = ctx.options.logging_option
    bot: models.MichaelBot = ctx.bot

    if logging_option not in EVENT_OPTION_MAPPING.values():
        raise lightbulb.NotEnoughArguments(missing = [ctx.invoked.options["logging_option"]])
    
    log_cache = bot.log_cache.get(ctx.guild_id)
    if log_cache is not None:
        setattr(log_cache, logging_option, not getattr(log_cache, logging_option))
        
        async with bot.pool.acquire() as conn:
            await bot.log_cache.update(conn, log_cache)
        
        if getattr(log_cache, logging_option):
            await ctx.respond(f"Enabled `{logging_option}`.", reply = True)
        else:
            await ctx.respond(f"Disabled `{logging_option}`.", reply = True)
    else:
        await ctx.respond("Logging is not enabled.", reply = True, mentions_reply = True)

@plugin.command()
@lightbulb.set_help(dedent('''
    - Author needs to have `Manage Server`.
'''))
@lightbulb.command("log-view", f"[{plugin.name}] View all log settings.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def log_view(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    log_cache = bot.log_cache.get(ctx.guild_id)
    embed = helpers.get_default_embed(
        title = f"Log Settings for {ctx.get_guild().name}",
        description = "",
        author = ctx.author,
        timestamp = dt.datetime.now().astimezone()
    )
    if log_cache is not None:
        for logging_option in psql.asdict(log_cache):
            if logging_option == "log_channel":
                if log_cache.log_channel is not None:
                    embed.description += f"**Log Destination:** {bot.cache.get_guild_channel(log_cache.log_channel).mention}\n"
                else:
                    embed.description += "**Log Destination:** `None`\n"
            else:
                embed.description += f"`{logging_option}`: {'Enabled' if getattr(log_cache, logging_option) else 'Disabled'}\n"
    else:
        embed.description += "**Log Destination:** `None`\n"
    embed.set_author(
        name = ctx.get_guild().name,
        icon = ctx.get_guild().icon_url
    )

    await ctx.respond(embed = embed, reply = True)

@plugin.listener(hikari.GuildChannelCreateEvent)
async def on_guild_channel_create(event: hikari.GuildChannelCreateEvent):
    if is_loggable(event):
        bot: models.MichaelBot = event.app
        log_channel = bot.log_cache[event.guild_id].log_channel
        embed = hikari.Embed(color = COLOR_CREATE)
        log_time = dt.datetime.now().astimezone()
        executor = None

        async for audit_log in bot.rest.fetch_audit_log(event.guild_id, event_type = hikari.AuditLogEventType.CHANNEL_CREATE).limit(1):
            for log_id in audit_log.entries:
                entry = audit_log.entries[log_id]
                log_time = entry.created_at
                executor = await entry.fetch_user()
                break
        
        if isinstance(event.channel, hikari.GuildTextChannel):
            category = bot.cache.get_guild_channel(event.channel.parent_id) if event.channel.parent_id is not None else None
            embed.title = "Text Channel Created"
            embed.description = dedent(f'''
                **Name:** `{event.channel.name}`
                **Jump to:** {event.channel.mention}
                **Category:** `{category.name if category is not None else "<None>"}`
            ''')
            embed.add_field(
                name = "Additional Info:",
                value = dedent(f'''
                    **ID:** {event.channel_id}
                    **Is NSFW:** {"Yes" if event.channel.is_nsfw else "No"}
                    **Position:** {event.channel.position}
                ''')
            )
        elif isinstance(event.channel, hikari.GuildVoiceChannel):
            category = bot.cache.get_guild_channel(event.channel.parent_id) if event.channel.parent_id is not None else None
            embed.title = "Voice Channel Created"
            embed.description = dedent(f'''
                **Name:** `{event.channel.name}`
                **Jump to:** {event.channel.mention}
                **Category:** `{category.name if category is not None else "<None>"}`
            ''')
            embed.add_field(
                name = "Additional Info:",
                value = dedent(f'''
                    **ID:** {event.channel_id}
                ''')
            )
        elif isinstance(event.channel, hikari.GuildCategory):
            embed.title = "Category Created"
            embed.description = dedent(f'''
                **Name:** `{event.channel.name}`
            ''')
            embed.add_field(
                name = "Additional Info:",
                value = dedent(f'''
                    **ID:** {event.channel_id}
                ''')
            )
        else:
            print("Wee woo")
        
        embed.set_footer(
            text = f"Created by: {executor}",
            icon = executor.avatar_url
        )
        embed.set_author(
            name = event.get_guild().name,
            icon = event.get_guild().icon_url
        )
        embed.timestamp = log_time
        await bot.rest.create_message(log_channel, embed = embed)

@plugin.listener(hikari.GuildChannelDeleteEvent)
async def on_guild_channel_delete(event: hikari.GuildChannelDeleteEvent):
    if is_loggable(event):
        bot: models.MichaelBot = event.app
        log_channel = bot.log_cache[event.guild_id].log_channel
        embed = hikari.Embed(color = COLOR_DELETE)
        log_time = dt.datetime.now().astimezone()
        executor = None

        async for audit_log in bot.rest.fetch_audit_log(event.guild_id, event_type = hikari.AuditLogEventType.CHANNEL_DELETE).limit(1):
            for log_id in audit_log.entries:
                entry = audit_log.entries[log_id]
                log_time = entry.created_at
                executor = await entry.fetch_user()
                break
        
        if isinstance(event.channel, hikari.GuildTextChannel):
            category = bot.cache.get_guild_channel(event.channel.parent_id) if event.channel.parent_id is not None else None
            embed.title = "Text Channel Deleted"
            embed.description = dedent(f'''
                **Name:** `{event.channel.name}`
                **Category:** `{category.name if category is not None else "<None>"}`
            ''')
            embed.add_field(
                name = "Additional Info:",
                value = dedent(f'''
                    **ID:** {event.channel_id}
                    **Was NSFW:** {"Yes" if event.channel.is_nsfw else "No"}
                ''')
            )
        elif isinstance(event.channel, hikari.GuildVoiceChannel):
            category = bot.cache.get_guild_channel(event.channel.parent_id) if event.channel.parent_id is not None else None
            embed.title = "Voice Channel Deleted"
            embed.description = dedent(f'''
                **Name:** `{event.channel.name}`
                **Category:** `{category.name if category is not None else "<None>"}`
            ''')
            embed.add_field(
                name = "Additional Info:",
                value = dedent(f'''
                    **ID:** {event.channel_id}
                ''')
            )
        elif isinstance(event.channel, hikari.GuildCategory):
            embed.title = "Category Deleted"
            embed.description = dedent(f'''
                **Name:** `{event.channel.name}`
            ''')
            embed.add_field(
                name = "Additional Info:",
                value = dedent(f'''
                    **ID:** {event.channel_id}
                ''')
            )
        else:
            print("Wee woo")
        
        embed.set_footer(
            text = f"Deleted by: {executor}",
            icon = executor.avatar_url
        )
        embed.set_author(
            name = event.get_guild().name,
            icon = event.get_guild().icon_url
        )
        embed.timestamp = log_time
        await bot.rest.create_message(log_channel, embed = embed)

@plugin.listener(hikari.GuildChannelUpdateEvent)
async def on_guild_channel_update(event: hikari.GuildChannelUpdateEvent):
    if is_loggable(event):
        bot: models.MichaelBot = event.app
        log_channel = bot.log_cache[event.guild_id].log_channel
        embed = hikari.Embed(color = COLOR_UPDATE)
        log_time = dt.datetime.now().astimezone()
        executor = None

        log_time_overwrite = dt.datetime.now().astimezone()
        executor_overwrite = None

        if event.old_channel is None:
            embed.title = "Channel Updated"
            embed.description = dedent(f'''
                ⚠ The previous state of the channel cannot be found.
                **Channel:** {event.channel.mention}
            ''')
            embed.set_author(
                name = event.get_guild().name,
                icon = event.get_guild().icon_url
            )
            embed.timestamp = dt.datetime.now().astimezone()

            await bot.rest.create_message(log_channel, embed = embed)
        else:
            # BUG: TimeoutError here sometimes.
            async for audit_log in bot.rest.fetch_audit_log(event.guild_id, event_type = hikari.AuditLogEventType.CHANNEL_UPDATE).limit(1):
                for log_id in audit_log.entries:
                    entry = audit_log.entries[log_id]
                    
                    log_time = entry.created_at
                    executor = await entry.fetch_user()
                    break
            
            if event.old_channel.name != event.channel.name:
                embed.title = "Channel Name Updated"
                embed.description = dedent(f'''
                    **Before:** {event.old_channel.name}
                    **After:** {event.channel.name}
                ''')
                embed.add_field(
                    name = "Additional Info:",
                    value = dedent(f'''
                        **Channel:** {event.channel.mention}
                        **Channel ID:** {event.channel_id}
                    ''')
                )
                if executor is not None:
                    embed.set_footer(
                        text = f"Updated by: {executor}",
                        icon = executor.avatar_url
                    )
                else:
                    embed.set_footer(
                        text = "Updated by: Unknown"
                    )
                embed.set_author(
                    name = event.get_guild().name,
                    icon = event.get_guild().icon_url
                )

                embed.timestamp = log_time
                await bot.rest.create_message(log_channel, embed = embed)
                embed = hikari.Embed(color = COLOR_UPDATE)
            if isinstance(event.channel, hikari.GuildTextChannel) and event.old_channel.topic != event.channel.topic:
                # To ignore RL SMP mass edit, but also in general bot rarely need to edit topic.
                if executor is None or not executor.is_bot:
                    embed.title = "Channel Topic Updated"
                    embed.description = dedent(f'''
                        **Before:**
                        {event.old_channel.topic}
                        **After:**
                        {event.channel.topic}
                    ''')
                    embed.add_field(
                        name = "Additional Info:",
                        value = dedent(f'''
                            **Channel:** {event.channel.mention}
                            **Channel ID:** {event.channel_id}
                        ''')
                    )
                    if executor is not None:
                        embed.set_footer(
                            text = f"Updated by: {executor}",
                            icon = executor.avatar_url
                        )
                    else:
                        embed.set_footer(
                            text = "Updated by: Unknown"
                        )
                    embed.set_author(
                        name = event.get_guild().name,
                        icon = event.get_guild().icon_url
                    )

                    embed.timestamp = log_time
                    await bot.rest.create_message(log_channel, embed = embed)
                    embed = hikari.Embed(color = COLOR_UPDATE)
            if event.old_channel.position != event.channel.position:
                # This part is particularly spammy (because moving a channel will affect all the remaining positions, which also trigger this events).
                # So we don't do this at all. Not worth it.
                pass
            if event.old_channel.permission_overwrites != event.channel.permission_overwrites:
                # Unlike other events, there are important info in the audit log that we need, so we have to call audit log appropriately.

                # Since you can change many permissions for different objects at once, we'll need to send the embeds separately as opposed to one single embed.
                before = event.old_channel
                after = event.channel

                added_permissions = []
                removed_permissions = []
                # Whether we got the log_time and executor from the necessary audit log.
                retrieved_update = False

                # Check for added permissions
                for target_id in after.permission_overwrites:
                    if target_id not in before.permission_overwrites:
                        if not retrieved_update:
                            async for audit_log in bot.rest.fetch_audit_log(event.guild_id, event_type = hikari.AuditLogEventType.CHANNEL_OVERWRITE_CREATE).limit(1):
                                for log_id in audit_log.entries:
                                    entry = audit_log.entries[log_id]
                                    log_time_overwrite = entry.created_at
                                    executor_overwrite = await entry.fetch_user()
                                    retrieved_update = True
                                    break
                        added_permissions.append(target_id)
                for target_id in added_permissions:
                    embed.title = "Channel Permissions Added"
                    target_obj = event.get_guild().get_role(target_id)
                    if target_obj is None:
                        target_obj = event.get_guild().get_member(target_id)
                    
                    granted_str = ', '.join(helpers.get_friendly_permissions(after.permission_overwrites[target_id].allow))
                    denied_str = ', '.join(helpers.get_friendly_permissions(after.permission_overwrites[target_id].deny))
                    
                    embed.description = dedent(f'''
                        **Channel:** {event.channel.mention}
                        **Target:** {helpers.mention(target_obj)} ({'Role' if isinstance(target_obj, hikari.Role) else 'Member'})
                        **Granted Permissions:** {granted_str if granted_str != "" else "`None`"}
                        **Denied Permissions:** {denied_str if denied_str != "" else "`None`"}
                    ''')
                    if executor_overwrite is not None:
                        embed.set_footer(
                            text = f"Created by: {executor_overwrite}",
                            icon = executor_overwrite.avatar_url
                        )
                    else:
                        embed.set_footer(
                            text = "Created by: Unknown"
                        )
                    embed.set_author(
                        name = event.get_guild().name,
                        icon = event.get_guild().icon_url
                    )

                    embed.timestamp = log_time_overwrite
                    embed.color = COLOR_CREATE
                    await bot.rest.create_message(log_channel, embed = embed)
                    embed = hikari.Embed(color = COLOR_UPDATE)
                
                retrieved_update = False
                executor_overwrite = None
                log_time_overwrite = log_time

                # Check for removed permissions
                for target_id in before.permission_overwrites:
                    if target_id not in after.permission_overwrites:
                        if not retrieved_update:
                            async for audit_log in bot.rest.fetch_audit_log(event.guild_id, event_type = hikari.AuditLogEventType.CHANNEL_OVERWRITE_DELETE).limit(1):
                                for log_id in audit_log.entries:
                                    entry = audit_log.entries[log_id]
                                    log_time_overwrite = entry.created_at
                                    executor_overwrite = await entry.fetch_user()
                                    retrieved_update = True
                                    break
                        removed_permissions.append(target_id)
                for target_id in removed_permissions:
                    embed.title = "Channel Permissions Removed"
                    target_obj = event.get_guild().get_role(target_id)
                    if target_obj is None:
                        target_obj = event.get_guild().get_member(target_id)
                    
                    granted_str = ', '.join(helpers.get_friendly_permissions(before.permission_overwrites[target_id].allow))
                    denied_str = ', '.join(helpers.get_friendly_permissions(before.permission_overwrites[target_id].deny))
                    
                    embed.description = dedent(f'''
                        **Channel:** {event.channel.mention}
                        **Target:** {helpers.mention(target_obj)} ({'Role' if isinstance(target_obj, hikari.Role) else 'Member'})
                        **Granted Permissions:** {granted_str if granted_str != "" else "`None`"}
                        **Denied Permissions:** {denied_str if denied_str != "" else "`None`"}
                    ''')
                    if executor_overwrite is not None:
                        embed.set_footer(
                            text = f"Deleted by: {executor_overwrite}",
                            icon = executor_overwrite.avatar_url
                        )
                    else:
                        embed.set_footer(
                            text = "Deleted by: Unknown"
                        )
                    embed.set_author(
                        name = event.get_guild().name,
                        icon = event.get_guild().icon_url
                    )

                    embed.timestamp = log_time_overwrite
                    embed.color = COLOR_DELETE
                    await bot.rest.create_message(log_channel, embed = embed)
                    embed = hikari.Embed(color = COLOR_UPDATE)

                executor_overwrite = None
                log_time_overwrite = log_time

                # Now deal with edited permissions
                for target_id in after.permission_overwrites:
                    if target_id in before.permission_overwrites and before.permission_overwrites[target_id] != after.permission_overwrites[target_id]:
                        # Send the output to a text file if too long.
                        log_attachment: hikari.Bytes = hikari.UNDEFINED

                        target_obj = event.get_guild().get_role(target_id)
                        if target_obj is None:
                            target_obj = event.get_guild().get_member(target_id)
                        
                        async for audit_log in bot.rest.fetch_audit_log(event.guild_id, event_type = hikari.AuditLogEventType.CHANNEL_OVERWRITE_UPDATE).limit(1):
                            for log_id in audit_log.entries:
                                entry = audit_log.entries[log_id]
                                log_time_overwrite = entry.created_at
                                executor_overwrite = await entry.fetch_user()
                                break
                        
                        # To get the permissions that's changed from one state to another (ie. granted to denied), we AND the bitfield
                        # between the previous state and the new state.
                        # So if before.allow = SEND_MESSAGES|READ_MESSAGES and after.deny = SEND_MESSAGES, the result of AND will be SEND_MESSAGES,
                        # which means SEND_MESSAGES is granted -> denied.
                        granted_to_denied = before.permission_overwrites[target_id].allow & after.permission_overwrites[target_id].deny
                        granted_to_neutral = before.permission_overwrites[target_id].allow & after.permission_overwrites[target_id].unset
                        neutral_to_granted = before.permission_overwrites[target_id].unset & after.permission_overwrites[target_id].allow
                        neutral_to_denied = before.permission_overwrites[target_id].unset & after.permission_overwrites[target_id].deny
                        denied_to_granted = before.permission_overwrites[target_id].deny & after.permission_overwrites[target_id].allow
                        denied_to_neutral = before.permission_overwrites[target_id].deny & after.permission_overwrites[target_id].unset

                        # Bunch of text format here.
                        granted_message = ',\n'.join(
                            [f"{permission_str}: `Granted -> Denied`" for permission_str in helpers.get_friendly_permissions(granted_to_denied)] + 
                            [f"{permission_str}: `Granted -> Neutral`" for permission_str in helpers.get_friendly_permissions(granted_to_neutral)]
                        )
                        neutralized_message = ',\n'.join(
                            [f"{permission_str}: `Neutral -> Granted`" for permission_str in helpers.get_friendly_permissions(neutral_to_granted)] + 
                            [f"{permission_str}: `Neutral -> Denied`" for permission_str in helpers.get_friendly_permissions(neutral_to_denied)]
                        )
                        denied_message = ',\n'.join(
                            [f"{permission_str}: `Denied -> Granted`" for permission_str in helpers.get_friendly_permissions(denied_to_granted)] + 
                            [f"{permission_str}: `Denied -> Neutral`" for permission_str in helpers.get_friendly_permissions(denied_to_neutral)]
                        )

                        if granted_message == "":
                            pass
                        elif neutralized_message == "" and denied_message != "":
                            neutralized_message = '\n'
                        elif neutralized_message != "" and denied_message == "":
                            granted_message += '\n'
                        elif neutralized_message != "" and denied_message != "":
                            granted_message += '\n'
                            neutralized_message += '\n'

                        embed.title = "Channel Permissions Updated"
                        content_message = dedent(f'''
                            **Channel:** {after.mention}
                            **Target:** {helpers.mention(target_obj)} ({'Role' if isinstance(target_obj, hikari.Role) else 'Member'})
                            {granted_message}{neutralized_message}{denied_message}
                        ''')
                        if len(content_message) > 1800:
                            log_attachment = hikari.Bytes(StringIO(content_message), "guild_channel_update.md")
                            embed.description = dedent('''
                                ⚠ The log content is too long, so I sent everything into a markdown file.
                            ''')
                        else:
                            embed.description = content_message
                        if executor_overwrite is not None:
                            embed.set_footer(
                                text = f"Updated by: {executor_overwrite}",
                                icon = executor_overwrite.avatar_url
                            )
                        else:
                            embed.set_footer(
                                text = "Updated by: Unknown"
                            )
                        embed.set_author(
                            name = event.get_guild().name,
                            icon = event.get_guild().icon_url
                        )

                        embed.timestamp = log_time_overwrite
                        await bot.rest.create_message(log_channel, embed = embed, attachment = log_attachment)

@plugin.listener(hikari.BanCreateEvent)
async def on_guild_ban(event: hikari.BanCreateEvent):
    pass

@plugin.listener(hikari.BanDeleteEvent)
async def on_guild_unban(event: hikari.BanDeleteEvent):
    pass

@plugin.listener(hikari.GuildUpdateEvent)
async def on_guild_update(event: hikari.GuildUpdateEvent):
    pass

@plugin.listener(hikari.MemberCreateEvent)
async def on_member_join(event: hikari.MemberCreateEvent):
    if is_loggable(event):
        bot: models.MichaelBot = event.app
        log_channel = bot.log_cache[event.guild_id].log_channel
        embed = hikari.Embed(color = COLOR_CREATE)
        log_time = dt.datetime.now().astimezone()
        
        embed.title = "Member Joined"
        embed.description = dedent(f'''
            **Member:** {event.member.mention}
            **Name:** {event.member}
        ''')
        embed.add_field(
            name = "Additional Info:",
            value = dedent(f'''
                **Member ID:** {event.member.id}
                **Account created on:** <t:{int(event.member.created_at.timestamp())}>
                **Account age:** {humanize.precisedelta(dt.datetime.now().astimezone() - event.member.created_at, format = '%0.0f')}
            ''')
        )
        embed.set_author(
            name = event.get_guild().name,
            icon = event.get_guild().icon_url
        )

        embed.timestamp = log_time
        await bot.rest.create_message(log_channel, embed = embed)

@plugin.listener(hikari.MemberDeleteEvent)
async def on_member_leave(event: hikari.MemberDeleteEvent):
    pass

@plugin.listener(hikari.MemberUpdateEvent)
async def on_member_update(event: hikari.MemberUpdateEvent):
    if is_loggable(event):
        bot: models.MichaelBot = event.app
        log_channel = bot.log_cache[event.guild_id].log_channel
        embed = hikari.Embed(color = COLOR_UPDATE)
        log_time = dt.datetime.now().astimezone()
        executor = None

        if event.old_member is None:
            pass
        else:
            if event.old_member.get_roles() != event.member.get_roles():
                async for audit_log in bot.rest.fetch_audit_log(event.guild_id, event_type = hikari.AuditLogEventType.MEMBER_ROLE_UPDATE).limit(1):
                    for log_id in audit_log.entries:
                        entry = audit_log.entries[log_id]
                        log_time = entry.created_at
                        executor = await entry.fetch_user()
                        break
                
                # You can't add generic @everyone role so default mention is enough.
                set_before_roles = set(event.old_member.get_roles())
                new_roles = [role.mention for role in event.member.get_roles() if role not in set_before_roles]
                set_after_roles = set(event.member.get_roles())
                removed_roles = [role.mention for role in event.old_member.get_roles() if role not in set_after_roles]

                if len(new_roles) != 0:
                    embed.title = "Member Role Added"
                    embed.description = dedent(f'''
                        **Member:** {event.member.mention}
                        **Role Added:** {', '.join(new_roles)}
                    ''')
                    if executor is not None:
                        embed.set_footer(
                            text = f"Updated by: {executor}",
                            icon = executor.avatar_url
                        )
                    else:
                        embed.set_footer(
                            text = "Updated by: Unknown"
                        )
                    embed.set_author(
                        name = event.get_guild().name,
                        icon = event.get_guild().icon_url
                    )

                    embed.timestamp = log_time
                    await bot.rest.create_message(log_channel, embed = embed)
                    embed = hikari.Embed(color = COLOR_UPDATE)
                if len(removed_roles) != 0:
                    embed.title = "Member Role Removed"
                    embed.description = dedent(f'''
                        **Member:** {event.member.mention}
                        **Role Removed:** {', '.join(removed_roles)}
                    ''')
                    if executor is not None:
                        embed.set_footer(
                            text = f"Updated by: {executor}",
                            icon = executor.avatar_url
                        )
                    else:
                        embed.set_footer(
                            text = "Updated by: Unknown"
                        )
                    embed.set_author(
                        name = event.get_guild().name,
                        icon = event.get_guild().icon_url
                    )

                    embed.timestamp = log_time
                    await bot.rest.create_message(log_channel, embed = embed)
                    embed = hikari.Embed(color = COLOR_UPDATE)
            if event.old_member.nickname != event.member.nickname:
                async for audit_log in bot.rest.fetch_audit_log(event.guild_id, event_type = hikari.AuditLogEventType.MEMBER_UPDATE).limit(1):
                    for log_id in audit_log.entries:
                        entry = audit_log.entries[log_id]
                        log_time = entry.created_at
                        executor = await entry.fetch_user()
                        break
                
                embed.title = "Member Nickname Updated"
                embed.description = dedent(f'''
                    **Before:** {event.old_member.nickname if event.old_member.nickname is not None else event.old_member.username}
                    **After:** {event.member.nickname if event.member.nickname is not None else event.member.username}
                ''')
                if executor is not None:
                    embed.set_footer(
                        text = f"Updated by: {executor}",
                        icon = executor.avatar_url
                    )
                else:
                    embed.set_footer(
                        text = "Updated by: Unknown"
                    )
                embed.set_author(
                    name = event.get_guild().name,
                    icon = event.get_guild().icon_url
                )

                embed.timestamp = log_time
                await bot.rest.create_message(log_channel, embed = embed)

@plugin.listener(hikari.GuildBulkMessageDeleteEvent)
async def on_guild_bulk_message_delete(event: hikari.GuildBulkMessageDeleteEvent):
    if is_loggable(event):
        bot: models.MichaelBot = event.app
        log_channel = bot.log_cache[event.guild_id].log_channel
        embed = hikari.Embed(color = COLOR_DELETE)
        log_time = dt.datetime.now().astimezone()
        executor = None

        if len(event.old_messages) > 0:
            # Send the output to a text file if too long.
            log_attachment: hikari.Bytes = hikari.UNDEFINED

            async for audit_log in bot.rest.fetch_audit_log(event.guild_id, event_type = hikari.AuditLogEventType.MESSAGE_BULK_DELETE).limit(1):
                for log_id in audit_log.entries:
                    entry = audit_log.entries[log_id]
                    log_time = entry.created_at
                    executor = await entry.fetch_user()
                    break
            
            content_message = ""
            for message_id in event.old_messages:
                message = event.old_messages[message_id]
                content_message += f"{message.author} at {message.created_at.strftime('%b %m %Y %I:%M %p')}(UTC): {message.content}\n"

                content_message += "\n"
            log_attachment = hikari.Bytes(StringIO(content_message), "guild_bulk_message_delete.md")
            embed.title = "Bulk Message Deleted"
            embed.description = dedent('''
                The content might be long, so I pasted everything into a markdown file, just to be safe.
            ''')
            embed.add_field(
                name = "Additional Info:",
                value = dedent(f'''
                    **Channel:** {event.get_channel().mention}
                ''')
            )
            if executor is not None:
                embed.set_footer(
                    text = f"Deleted by: {executor}",
                    icon = executor.avatar_url
                )
            else:
                embed.set_footer(
                    text = "Deleted by: Unknown"
                )
            embed.set_author(
                name = event.get_guild().name,
                icon = event.get_guild().icon_url
            )

            embed.timestamp = log_time
            await bot.rest.create_message(log_channel, embed = embed, attachment = log_attachment)
        else:
            embed.title = "Bulk Message Deleted"
            embed.description = "⚠ Deleted messages info cannot be found."
            embed.add_field(
                name = "Additional Info:",
                value = dedent(f'''
                    **Channel:** {event.get_channel().mention}
                ''')
            )
            embed.set_author(
                name = event.get_guild().name,
                icon = event.get_guild().icon_url
            )

            embed.timestamp = log_time
            await bot.rest.create_message(log_channel, embed = embed)

@plugin.listener(hikari.GuildMessageDeleteEvent)
async def on_guild_message_delete(event: hikari.GuildMessageDeleteEvent):
    if is_loggable(event):
        bot: models.MichaelBot = event.app
        log_channel = bot.log_cache[event.guild_id].log_channel
        embed = hikari.Embed(color = COLOR_DELETE)
        log_time: dt.datetime = dt.datetime.now().astimezone()
        executor = None

        if event.old_message is not None:
            log_attachment: hikari.Bytes = hikari.UNDEFINED
            # Since this event is pretty fucked by Discord I'm just gonna display the basic info lmfao not gonna bother look for who delete it.
            async for audit_log in bot.rest.fetch_audit_log(event.guild_id, event_type = hikari.AuditLogEventType.MESSAGE_DELETE).limit(1):
                for log_id in audit_log.entries:
                    entry = audit_log.entries[log_id]
                    if entry.target_id != event.old_message.author.id:
                        break

                    log_time = entry.created_at
                    executor = await entry.fetch_user()
                    break
            if executor is None:
                executor = event.old_message.author
            
            embed.title = "Message Deleted"
            content_message = f"**Content:** {event.old_message.content}" if event.old_message.content != "" else ""
            if len(content_message) > 1800:
                log_attachment = hikari.Bytes(StringIO(content_message), "guild_message_delete.md")
                embed.description = dedent('''
                    ⚠ The deleted content is too long, so I sent everything into a file.
                ''')
            else:
                embed.description = content_message
            if len(event.old_message.attachments) > 0:
                for index, attachment in enumerate(event.old_message.attachments):
                    embed.add_field(
                        name = f"Attachment {index + 1}:",
                        value = f"[View]({attachment.proxy_url}) (Only available for images)"
                    )
            embed.add_field(
                name = "Additional Info:",
                value = dedent(f'''
                    **Author:** {event.old_message.author.mention}
                    **Channel:** {event.get_channel().mention}
                ''')
            )
            embed.set_footer(
                text = f"Deleted by: {executor}",
                icon = executor.avatar_url
            )
            embed.set_author(
                name = event.get_guild().name,
                icon = event.get_guild().icon_url
            )

            embed.timestamp = log_time
            await bot.rest.create_message(log_channel, content = "*Note: `Deleted by:` can be incorrect due to Discord limitation.*", embed = embed, attachment = log_attachment)
        else:
            embed.title = "Message Deleted"
            embed.description = "⚠ Deleted message info cannot be found."
            embed.add_field(
                name = "Additional Info:",
                value = dedent(f'''
                    **Channel:** {event.get_channel().mention}
                ''')
            )
            embed.set_author(
                name = event.get_guild().name,
                icon = event.get_guild().icon_url
            )
            embed.timestamp = dt.datetime.now().astimezone()
            await bot.rest.create_message(log_channel, embed = embed)

@plugin.listener(hikari.GuildMessageUpdateEvent)
async def on_guild_message_update(event: hikari.GuildMessageUpdateEvent):
    if is_loggable(event):
        # Read the note for `event.author`
        if event.author == hikari.UNDEFINED:
            return
        elif not event.author.is_bot:
            bot: models.MichaelBot = event.app
            log_channel = bot.log_cache[event.guild_id].log_channel
            embed = hikari.Embed(color = COLOR_UPDATE)
            log_time: dt.datetime = dt.datetime.now().astimezone()
            executor = event.author
            log_attachment: hikari.Bytes = hikari.UNDEFINED

            before = event.old_message
            after = event.message

            if before is None:
                log_time = after.edited_timestamp
                embed.title = "Message Edited"
                embed.description = dedent('''
                    ⚠ The original content of the message cannot be found.
                ''')
            else:
                before_content = before.content if before.content != "" else "`<Empty>`"
                after_content = after.content if after.content != "" else "`<Empty>`"

                content_message = (
                    "**Before:**\n"
                    f"{before_content}\n"
                    "**After:**\n"
                    f"{after_content}\n"
                )

                log_time = after.edited_timestamp
                if log_time is None:
                    return

                embed.title = "Message Edited"
                if len(content_message) > 1800:
                    log_attachment = hikari.Bytes(StringIO(content_message), "guild_message_update.md")
                    embed.description = dedent('''
                        ⚠ The edited content is too long, so I sent everything into a markdown file.
                    ''')
                else:
                    embed.description = content_message

            embed.add_field(
                name = "Additional Info:",
                value = dedent(f'''
                    **Message URL:** [Jump to message]({after.make_link(event.guild_id)})
                    **Channel:** {event.get_channel().mention}
                ''')
            )
            embed.set_footer(
                text = f"Edited by: {executor}",
                icon = executor.avatar_url
            )
            embed.set_author(
                name = event.get_guild().name,
                icon = event.get_guild().icon_url
            )
            embed.timestamp = log_time

            await bot.rest.create_message(log_channel, embed = embed, attachment = log_attachment)

@plugin.listener(hikari.RoleCreateEvent)
async def on_role_create(event: hikari.RoleCreateEvent):
    if is_loggable(event):
        bot: models.MichaelBot = event.app
        log_channel = bot.log_cache[event.guild_id].log_channel
        embed = hikari.Embed(color = COLOR_CREATE)
        log_time: dt.datetime = dt.datetime.now().astimezone()
        executor = None

        async for audit_log in bot.rest.fetch_audit_log(event.guild_id, event_type = hikari.AuditLogEventType.ROLE_CREATE).limit(1):
            for log_id in audit_log.entries:
                entry = audit_log.entries[log_id]
                log_time = entry.created_at
                executor = await entry.fetch_user()

                allow_perms = helpers.get_friendly_permissions(event.role.permissions)
                deny_perms = helpers.get_friendly_permissions(~event.role.permissions)

                allow_str = ", ".join(allow_perms) if len(allow_perms) > 0 else "None"
                deny_str = ", ".join(deny_perms) if len(deny_perms) > 0 else "None"

                embed.title = "Role Created"
                embed.description = dedent(f'''
                    **Role:** {event.role.mention}
                    **Name:** {event.role.name}
                    **Granted Permissions:** {allow_str}
                    **Denied Permissions:** {deny_str}
                ''')
                embed.add_field(
                    name = "Additional Info:",
                    value = dedent(f'''
                        **Is Separated:** {"Yes" if event.role.is_hoisted else "No"}
                        **Is Mentionable:** {"Yes" if event.role.is_mentionable else "No"}
                        **Color:** {event.role.color}
                    ''')
                )
                embed.set_footer(
                    text = f"Created by: {executor}",
                    icon = executor.avatar_url
                )
                embed.set_author(
                    name = bot.cache.get_guild(event.guild_id).name,
                    icon = bot.cache.get_guild(event.guild_id).icon_url
                )
                embed.timestamp = log_time

                await bot.rest.create_message(log_channel, embed = embed)
                break

@plugin.listener(hikari.RoleDeleteEvent)
async def on_role_delete(event: hikari.RoleDeleteEvent):
    if is_loggable(event):
        bot: models.MichaelBot = event.app
        log_channel = bot.log_cache[event.guild_id].log_channel
        embed = hikari.Embed(color = COLOR_DELETE)
        log_time: dt.datetime = dt.datetime.now().astimezone()
        executor = None

        entry_found = False
        async for audit_log in bot.rest.fetch_audit_log(event.guild_id, event_type = hikari.AuditLogEventType.ROLE_DELETE).limit(1):
            for log_id in audit_log.entries:
                if event.old_role is not None:
                    entry_found = True
                else:
                    break

                entry = audit_log.entries[log_id]
                log_time = entry.created_at
                executor = await entry.fetch_user()

                allow_perms = helpers.get_friendly_permissions(event.old_role.permissions)
                deny_perms = helpers.get_friendly_permissions(~event.old_role.permissions)

                allow_str = ", ".join(allow_perms) if len(allow_perms) > 0 else "None"
                deny_str = ", ".join(deny_perms) if len(deny_perms) > 0 else "None"

                embed.title = "Role Deleted"
                embed.description = dedent(f'''
                    **Name:** {event.old_role.name}
                    **Granted Permissions:** {allow_str}
                    **Denied Permissions:** {deny_str}
                ''')
                embed.add_field(
                    name = "Additional Info:",
                    value = dedent(f'''
                        **Was Separated:** {"Yes" if event.old_role.is_hoisted else "No"}
                        **Was Mentionable:** {"Yes" if event.old_role.is_mentionable else "No"}
                        **Color:** {event.old_role.color}
                    ''')
                )
                embed.set_footer(
                    text = f"Deleted by: {executor}",
                    icon = executor.avatar_url
                )
                embed.set_author(
                    name = bot.cache.get_guild(event.guild_id).name,
                    icon = bot.cache.get_guild(event.guild_id).icon_url
                )
                embed.timestamp = log_time

                await bot.rest.create_message(log_channel, embed = embed)
                break

        if not entry_found:
            embed.title = "Role Deleted"
            embed.description = "⚠ Role information cannot be found."
            embed.set_author(
                name = bot.cache.get_guild(event.guild_id).name,
                icon = bot.cache.get_guild(event.guild_id).icon_url
            )
            embed.timestamp = dt.datetime.now().astimezone()
            await bot.rest.create_message(log_channel, embed = embed)

@plugin.listener(hikari.RoleUpdateEvent)
async def on_role_update(event: hikari.RoleUpdateEvent):
    if is_loggable(event):
        bot: models.MichaelBot = event.app
        log_channel = bot.log_cache[event.guild_id].log_channel
        embed = hikari.Embed(color = COLOR_UPDATE)
        log_time: dt.datetime = dt.datetime.now().astimezone()
        executor = None

        if event.old_role is None:
            embed.title = "Role Updated"
            embed.description = dedent(f'''
                ⚠ The previous state of this role cannot be found.
                **Role:** {event.role.mention}
            ''')
            embed.set_author(
                name = bot.cache.get_guild(event.guild_id).name,
                icon = bot.cache.get_guild(event.guild_id).icon_url
            )

            embed.timestamp = log_time
            await bot.rest.create_message(log_channel, embed = embed)
        else:
            async for audit_log in bot.rest.fetch_audit_log(event.guild_id, event_type = hikari.AuditLogEventType.ROLE_UPDATE).limit(1):
                for log_id in audit_log.entries:
                    entry = audit_log.entries[log_id]
                    log_time = entry.created_at
                    executor = await entry.fetch_user()
                    break
            if event.old_role.name != event.role.name:
                embed.title = "Role Name Changed"
                embed.description = dedent(f'''
                    **Role:** {helpers.mention(event.role)}
                    **Before:** {event.old_role}
                    **After:** {event.role}
                ''')
                if executor is not None:
                    embed.set_footer(
                        text = f"Updated by: {executor}",
                        icon = executor.avatar_url
                    )
                else:
                    embed.set_footer(
                        text = "Updated by: Unknown"
                    )
                embed.set_author(
                    name = bot.cache.get_guild(event.guild_id).name,
                    icon = bot.cache.get_guild(event.guild_id).icon_url
                )

                embed.timestamp = log_time
                await bot.rest.create_message(log_channel, embed = embed)
                embed = hikari.Embed(color = COLOR_UPDATE)
            if event.old_role.color != event.role.color:
                embed.title = "Role Color Changed"
                embed.description = dedent(f'''
                    **Role:** {helpers.mention(event.role)}
                    **Before:** {event.old_role.color}
                    **After:** {event.role.color}
                ''')
                if executor is not None:
                    embed.set_footer(
                        text = f"Updated by: {executor}",
                        icon = executor.avatar_url
                    )
                else:
                    embed.set_footer(
                        text = "Updated by: Unknown"
                    )
                embed.set_author(
                    name = bot.cache.get_guild(event.guild_id).name,
                    icon = bot.cache.get_guild(event.guild_id).icon_url
                )

                embed.timestamp = log_time
                await bot.rest.create_message(log_channel, embed = embed)
                embed = hikari.Embed(color = COLOR_UPDATE)
            if event.old_role.permissions != event.role.permissions:
                # Take two permissions old: 1101011 and new: 1011001 for example.
                # To get the added permissions, do ~1101011 & 1011001 = 0010000
                # To get the denied permissions, do 1101011 & ~1011001 = 0100010
                granted = ~event.old_role.permissions & event.role.permissions
                denied = event.old_role.permissions & ~event.role.permissions

                granted_message = ", ".join(
                    [f"{permission_str}: `Denied -> Granted`" for permission_str in helpers.get_friendly_permissions(granted)]
                )
                denied_message = ", ".join(
                    [f"{permission_str}: `Granted -> Denied`" for permission_str in helpers.get_friendly_permissions(denied)]
                )

                if denied_message != "" and granted_message != "":
                    granted_message += "\n"
                
                embed.title = "Role Permissions Changed"
                embed.description = dedent(f'''
                    **Role:** {helpers.mention(event.role)}
                    {granted_message}{denied_message}
                ''')
                if executor is not None:
                    embed.set_footer(
                        text = f"Updated by: {executor}",
                        icon = executor.avatar_url
                    )
                else:
                    embed.set_footer(
                        text = "Updated by: Unknown"
                    )
                embed.set_author(
                    name = bot.cache.get_guild(event.guild_id).name,
                    icon = bot.cache.get_guild(event.guild_id).icon_url
                )
                
                embed.timestamp = log_time
                await bot.rest.create_message(log_channel, embed = embed)

@plugin.listener(lightbulb.CommandCompletionEvent)
async def on_command_invoke(event: lightbulb.CommandCompletionEvent):
    if is_loggable(event):
        bot: models.MichaelBot = event.app
        log_channel = bot.log_cache[event.guild_id].log_channel
        embed = hikari.Embed(color = COLOR_OTHER)
        log_time = dt.datetime.now().astimezone()

        command_type = "Prefix Command"
        if isinstance(event.context, lightbulb.SlashContext):
            command_type = "Slash Command"
        
        embed.title = "Command Invoked"
        embed.description = dedent(f'''
            **Command:** `{event.context.invoked.qualname}`
            **Type:** `{command_type}`
        ''')
        embed.set_footer(
            text = f"Invoked by: {event.context.author}",
            icon = event.context.author.avatar_url
        )
        embed.set_author(
            name = event.context.get_guild().name,
            icon = event.context.get_guild().icon_url
        )

        embed.timestamp = log_time
        await bot.rest.create_message(log_channel, embed = embed)

@plugin.listener(lightbulb.CommandErrorEvent)
async def on_command_error(event: lightbulb.CommandErrorEvent):
    if is_loggable(event):
        bot: models.MichaelBot = event.app
        log_channel = bot.log_cache[event.context.guild_id].log_channel
        embed = hikari.Embed(color = COLOR_OTHER)
        log_time = dt.datetime.now().astimezone()

        exception = event.exception
        if isinstance(exception, lightbulb.CommandInvocationError):
            exception = exception.__cause__

        if isinstance(exception, lightbulb.CommandNotFound):
            return
        if isinstance(exception, lightbulb.CommandIsOnCooldown):
            return
        if isinstance(exception, lightbulb.MaxConcurrencyLimitReached):
            return
        
        ctx = event.context
        invoke_content: str = ""
        if isinstance(ctx, lightbulb.PrefixContext):
            invoke_content = ctx.event.message.content
        elif isinstance(ctx, lightbulb.SlashContext):
            content_l = [ctx.interaction.command_name]
            options = ctx.interaction.options
            if options:
                # Handle subcommands.
                while options[0].options:
                    content_l.append(f"{options[0].name}")
                    options = options[0].options
                
                for option in options:
                    content_l.append(f"[{option.name}: {option.value}]")
            invoke_content = ' '.join(content_l)
        else:
            invoke_content = "None"

        embed.title = "Command Raised an Error"
        embed.description = dedent(f'''
            **Command:** `{event.context.invoked.signature}`
            **Invoked as:** `{invoke_content}`
            **Error:** ```{type(exception).__name__}: {exception}```
        ''')
        embed.add_field(
            name = "Additional Info:",
            value = dedent(f'''
                **Channel:** {event.context.get_channel().mention}
            ''')
        )
        embed.set_footer(
            text = f"Invoked by: {event.context.author}",
            icon = event.context.author.avatar_url
        )
        embed.set_author(
            name = event.context.get_guild().name,
            icon = event.context.get_guild().icon_url
        )

        embed.timestamp = log_time
        await bot.rest.create_message(log_channel, embed = embed)

def load(bot: models.MichaelBot):
    bot.add_plugin(plugin)
def unload(bot: models.MichaelBot):
    bot.remove_plugin(plugin)
