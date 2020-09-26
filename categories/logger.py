import discord
from discord.ext import commands

import datetime
import inspect

from categories.utilities.method_cog import Facility

# Specification:
# Every single events here (except raw events) must have the following variables declared at the very first line after checking log:
# - log_channel: the channel that's gonna send the embed. Retrieve using Facility.get_config and config["LOG_CHANNEL"]
# - log_title: the log title that's gonna pass in title in discord.Embed
# - log_content: the log content that's gonna pass in description in discord.Embed
# - log_color: the color of the embed. It must be self.color_... depend on the current event.
# - log_time: the timestamp of the embed. Typically get from entry.created_at.
# - Optional(executor): the Member that triggered the event.

# Log embed specification:
# Every single embed send here (except raw events) must have the following format:
# Embed.author as the executor.
# Embed.title as log_title.
# Embed.description as log_content.
# Embed.color as log_color.
# Embed.timestamp as log_time.
# Embed.footer as the executor.
# Optional (Embed.thumbnail) as the target.

# People should understand that discord's audit log itself is screwed in many ways (including not logging bot's changing mass permission
# for example) and so don't expect logging to log 100% correct or even 90% correct.

class LogContent:
    '''
    A helper class to attach the log content.

    This is used because both `textwrap.dedent()` and `inspect.cleandoc()` seems to fail to
    clean up tabs from docstring, so this is preferred.
    '''
    def __init__(self, msg = ""):
        self.content = msg
    
    def append(self, *contents):
        '''
        Append the `content` to the current content of this class.

        By default, this method will add a newline at the end of `content`.

        This method returns `self` to allow chaining.
        '''

        for content in contents:
            self.content += content
            print(self.content)
            self.content += '\n'

        return self
    
class Logging(commands.Cog):
    '''Commands related to logging actions in server.'''
    def __init__(self, bot):
        self.bot = bot
        self.log_channel = 649111117204815883
        self.emoji = '📝'

        # Color specification:
        # Moderation action = Black
        # Warn / Mute = Red
        # Change (server change, message change, member change, etc.) = Yellow
        # Delete (delete message, delete role, delete channel, etc.) = Orange
        # Create (create channel, create role, etc.) = Green
        # Join / Leave (server) = Blue
        # Other = Teal
        self.color_moderation = 0x000000
        self.color_warn_mute = discord.Color.red()
        self.color_change = discord.Color.gold()
        self.color_delete = discord.Color.orange()
        self.color_create = discord.Color.green()
        self.color_guild_join_leave = discord.Color.blue()
        self.color_other = discord.Color.teal()

    def log_check(self, guild):
        config = Facility.get_config(guild.id)
        if config["ERROR"] == 0 and config["STATUS_LOG"] == 1 and config["LOG_CHANNEL"] != 0:
            return True
        elif config["ERROR"] != 0:
            print("File not found.")
            return False
        elif config["STATUS_LOG"] == 0:
            print("Logging not enabled.")
            return False
        else:
            print("Log channel not set.")
            return False

    def role_dpyperms_to_dperms(self, role_permissions : str):
        if role_permissions == "administrator":
            return "Administrator"
        if role_permissions == "view_audit_log":
            return "View Audit Log"
        if role_permissions == "manage_guild":
            return "Manage Server"
        if role_permissions == "manage_roles":
            return "Manage Roles"
        if role_permissions == "manage_channels":
            return "Manage Channels"
        if role_permissions == "kick_members":
            return "Kick Members"
        if role_permissions == "ban_members":
            return "Ban Members"
        if role_permissions == "create_instant_invite":
            return "Create Invite"
        if role_permissions == "change_nickname":
            return "Change Nickname"
        if role_permissions == "manage_nicknames":
            return "Manage Nicknames"
        if role_permissions == "manage_emojis":
            return "Manage Emojis"
        if role_permissions == "manage_webhooks":
            return "Manage Webhooks"
        if role_permissions == "read_messages":
            return "Read Text Channels & See Voice Channels"
        if role_permissions == "send_messages":
            return "Send Messages"
        if role_permissions == "send_tts_messages":
            return "Send TTS Messages"
        if role_permissions == "embed_links":
            return "Embed Links"
        if role_permissions == "attach_files":
            return "Attach Files"
        if role_permissions == "read_message_history":
            return "Read Message History"
        if role_permissions == "mention_everyone":
            return "Mention Everyone"
        if role_permissions == "external_emojis":
            return "Use External Emojis"
        if role_permissions == "add_reactions":
            return "Add Reactions"
        if role_permissions == "connect":
            return "Connect"
        if role_permissions == "speak":
            return "Speak"
        if role_permissions == "mute_members":
            return "Mute Members"
        if role_permissions == "deafen_members":
            return "Deafen Members"
        if role_permissions == "move_members":
            return "Move Members"
        if role_permissions == "use_voice_activation":
            return "Use Voice Activity"
        if role_permissions == "priority_speaker":
            return "Priority Speaker"
        if role_permissions == "stream":
            return "Go Live"
    
    def channel_dpyperms_to_dperms(self, channel_permissions : str):
        if channel_permissions == "create_instant_invite":
            return "Create Invite"
        if channel_permissions == "manage_channels":
            return "Manage Channels"
        if channel_permissions == "manage_roles":
            return "Manage Permissions"
        if channel_permissions == "manage_webhooks":
            return "Manage Webhooks"
        if channel_permissions == "read_messages":
            return "Read Messages & View Channel"
        if channel_permissions == "send_messages":
            return "Send Messages"
        if channel_permissions == "send_tts_messages":
            return "Send TTS Messages"
        if channel_permissions == "embed_links":
            return "Embed Links"
        if channel_permissions == "attach_files":
            return "Attach Files"
        if channel_permissions == "read_message_history":
            return "Read Message History"
        if channel_permissions == "mention_everyone":
            return "Mention Everyone"
        if channel_permissions == "external_emojis":
            return "Use External Emojis"
        if channel_permissions == "add_reactions":
            return "Add Reactions"
        # Voice channels
        if channel_permissions == "connect":
            return "Connect"
        if channel_permissions == "speak":
            return "Speak"
        if channel_permissions == "mute_members":
            return "Mute Members"
        if channel_permissions == "deafen_members":
            return "Deafen Members"
        if channel_permissions == "move_members":
            return "Move Members"
        if channel_permissions == "use_voice_activation":
            return "Use Voice Activity"
        if channel_permissions == "priority_speaker":
            return "Priority Speaker"
        if channel_permissions == "stream":
            return "Go Live"

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        guild = message.guild
        # First we check if the logging feature is enabled in that guild.
        if self.log_check(guild):
            # Then we get the log channel of that guild.
            config = Facility.get_config(guild.id)
            log_channel = self.bot.get_channel(config["LOG_CHANNEL"])

            # Initialize variables according to specification.
            log_title = "Message Deleted"
            log_content = LogContent()
            log_color = self.color_delete
            log_time = None

            executor = None

            async for entry in message.guild.audit_logs(action = discord.AuditLogAction.message_delete, limit = 1):
                executor = entry.user
                # Audit log doesn't log message that the author delete himself.
                log_time = datetime.datetime.utcnow()
                
                # Because audit log doesn't log message that the author delete himself,
                # we need to check if the latest message_delete is roughly the same time as the event is fired.
                # The 60 seconds is relative. Can be changed, but shouldn't lower than 30 seconds.
                # Can't really do anything here except hardcode.
                log_time2 = entry.created_at
                deltatime = log_time - log_time2
                if deltatime.seconds < 30 and deltatime.days == 0:
                    executor = message.author

                # Generally we have 3 cases to deal with: normal text only, possibly have attachment, and possibly have embed.
                # For attachment, what we can do is to provide a proxy URL to the attachment, which only usable for images.
                # For embed, what we can do is to provide the preview of a single embed a.k.a the dict version of the embed.
                # How are we gonna display the embed correctly?
                # We can have a content = ("Content: %s" % message.content) if message.content != "" else ""
                # For attachment, first we get the list of attachments through message.attachments
                # Same as content, we check if the attachments list is empty or not.
                # Then, for each attachment, we get the proxy URL, and put it to attachment_message.
                # For embeds, it's relatively easy but messy: we also get the list of embeds through message.embeds
                # Then we simply display the dict, easy.
                content_message = f"**Content:** {message.content}" if message.content != "" else ""
                if len(message.attachments) == 0:
                    attachment_message = ""
                else:
                    counter = 1
                    attachment_message = "\n----------------------------\n" if content_message != "" else ""
                    for attachment in message.attachments:
                        attachment_message += f"**Attachment {counter}**\n[View]({attachment.proxy_url}) (Only available for images)\n"
                        counter += 1
                    attachment_message += "----------------------------"
                if len(message.embeds) == 0:
                    embed_message = ""
                else:
                    import json # This help formatting the dict better
                    counter = 1
                    embed_message = "\n----------------------------\n" if (content_message != "" and attachment_message != "") else ""
                    for embed in message.embeds:
                        embed_message = "**Embed %d**\n```%s```" % (counter, json.dumps(embed.to_dict(), indent = 2))
                        counter += 1
                    embed_message += "----------------------------"
                
                log_content.append(
                    "%s%s%s" % (content_message, attachment_message, embed_message),
                    "**Author:** %s" % message.author.mention,
                    "**Deleted by:** %s" % executor.mention,
                    "----------------------------",
                    "**Channel:** %s" % message.channel.mention
                )

                embed = Facility.get_default_embed(
                    title = log_title,
                    description = log_content.content,
                    color = log_color,
                    timestamp = log_time
                )

                embed.set_thumbnail(
                    url = message.author.avatar_url
                ).set_author(
                    name = str(executor), 
                    icon_url = executor.avatar_url
                ).set_footer(
                    text = str(executor),
                    icon_url = executor.avatar_url
                )
                
                await log_channel.send(embed = embed)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        pass

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        if payload.cached_message != None: # on_message_edit
            return
        else:
            guild = self.bot.get_channel(payload.channel_id).guild
            if self.log_check(guild):
                config = Facility.get_config(guild.id)
                log_channel = self.bot.get_channel(config["LOG_CHANNEL"])

                edited_message = None
                message_channel = None
                
                # We're attempting to retrieve the message here...
                try:
                    message_channel = self.bot.get_channel(payload.channel_id)
                    edited_message = await message_channel.fetch_message(payload.message_id)
                except discord.NotFound:
                    message_channel = None
                except discord.HTTPException:
                    pass
                
                log_title = "Message Edited"
                log_content = LogContent().append(
                    "⚠ The original content of the message is not found.",
                    "**Current content:** %s" % edited_message.content,
                    "**Author:** %s" % edited_message.author.mention,
                    "----------------------------",
                    "**Message ID:** %d" % payload.message_id,
                    "**Message URL:** [Jump to message](%s)" % edited_message.jump_url,
                    "**Channel:** %s" % message_channel.mention if message_channel is not None else "Channel not found."
                )

                log_color = self.color_change
                log_time = edited_message.edited_at

                embed = Facility.get_default_embed(
                    title = log_title,
                    description = log_content.content,
                    color = log_color,
                    timestamp = log_time
                ).set_thumbnail(
                    url = edited_message.author.avatar_url
                )

                await log_channel.send(embed = embed)
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        # We don't log bot messages yet.
        if after.author.bot == False:
            guild = before.guild
            # First we check if the logging feature is enabled in that guild.
            if self.log_check(guild):
                # We retrieve the logging channel for that guild.
                config = Facility.get_config(guild.id)
                log_channel = self.bot.get_channel(config["LOG_CHANNEL"])

                log_title = "Message Edited"

                # Basically, we generally have 3 types of messages: normal text, attachments and embeds.
                # However, attachments can't be edited, so that's one task down.
                # For the rest, just do like message_delete.
                content_message = "**Content before:** %s\n**Content after:** %s" % (before.content, after.content) if after.content != "" else ""

                # We don't support edited embed because displaying both dict form is too large.
                # TODO: Find an alternative for this.

                log_content = LogContent().append(
                    content_message,
                    "**Author:** %s" % after.author.mention,
                    "----------------------------",
                    "**Message URL**: [Jump to message](%s)"  % after.jump_url,
                    "**Channel:** %s" % after.channel.mention
                )
                log_color = self.color_change
                log_time = after.edited_at

                # When posting a link, the message will be internally edited to have the embed of the link
                # which trigger this event, but doesn't change the edited_at attr in Message.
                # So we need to check if that's the case, and if it is, we don't log.
                if log_time is None:
                    return

                embed = Facility.get_default_embed(
                    title = log_title,
                    description = log_content.content,
                    color = log_color,
                    timestamp = log_time
                ).set_thumbnail(
                    url = after.author.avatar_url
                ).set_author(
                    name = str(after.author), 
                    icon_url = after.author.avatar_url
                ).set_footer(
                    text = str(after.author),
                    icon_url = after.author.avatar_url
                )

                await log_channel.send(embed = embed)
    
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        # First we check if the logging feature is enabled in that guild.
        if self.log_check(guild):
            # We retrieve the logging channel for that guild.
            config = Facility.get_config(guild.id)
            log_channel = self.bot.get_channel(config["LOG_CHANNEL"])

            log_title = "User Banned"
            log_content = LogContent()
            log_color = self.color_moderation
            log_time = None

            reason = "Not provided."
            executor = None
            
            # Simply retrieve the latest ban log and get info from that.
            async for entry in guild.audit_logs(action = discord.AuditLogAction.ban, limit = 1):        
                if entry.reason == None:
                    reason = "Not provided."
                else:
                    reason = entry.reason
                executor = entry.user
                log_time = entry.created_at
                
                log_content = f'''
                                **User:** {user.mention}
                                **User Name:** {user}
                                **Reason:** {reason}
                                ----------------------------
                                **Banned by:** {executor.mention}
                                '''
                
                log_content.append(
                    "**User:** %s" % user.mention,
                    "**User Name:** %s" % user,
                    "**Reason:** %s" % reason,
                    "----------------------------",
                    "**Banned by:** %s" % executor.mention
                )

                embed = Facility.get_default_embed(
                    title = log_title,
                    description = log_content,
                    color = log_color,
                    timestamp = log_time
                ).set_thumbnail(
                    url = user.avatar_url
                ).set_author(
                    name = str(executor),
                    icon_url = executor.avatar_url
                ).set_footer(
                    text = str(executor),
                    icon_url = executor.avatar_url
                )

                await log_channel.send(embed = embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        # First we check if the logging feature is enabled in that guild.
        if self.log_check(guild):
            # We retrieve the logging channel for that guild.
            config = Facility.get_config(guild.id)
            log_channel = self.bot.get_channel(config["LOG_CHANNEL"])

            log_title = "User Unbanned"
            log_content = ""
            log_color = self.color_moderation
            log_time = None

            reason = ""
            executor = None
            
            # Similar to on_member_ban
            async for entry in guild.audit_logs(action = discord.AuditLogAction.unban, limit = 1):        
                if entry.reason == None:
                    reason = "Not provided."
                else:
                    reason = entry.reason
                executor = entry.user
                log_time = entry.created_at
                
                log_content = f'''
                                **User:** {user.mention}
                                **User Name:** {user}
                                **Reason:** {reason}
                                ----------------------------
                                **Unbanned by:** {executor.mention}
                                '''
                
                embed = Facility.get_default_embed(
                    title = log_title, 
                    description = log_content, 
                    color = log_color, 
                    timestamp = log_time
                ).set_thumbnail(
                    url = user.avatar_url
                ).set_author(
                    name = str(executor),
                    icon_url = executor.avatar_url
                ).set_footer(
                    text = str(executor),
                    icon_url = executor.avatar_url
                )

                await log_channel.send(embed = embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild

        # First we check if the logging feature is enabled in that guild.
        if self.log_check(guild):
            # We retrieve the logging channel for that guild.
            config = Facility.get_config(guild.id)
            log_channel = self.bot.get_channel(config["LOG_CHANNEL"])

            log_title = "Member Joined"
            log_content = '''
                            **Member:** %s
                            **Member Name:** %s
                            ----------------------------
                            **Member ID:** %d
                            **Account created on:** %s (UTC)
                            ''' % (
                                member.mention,
                                str(member),
                                member.id,

                                member.created_at.strftime("%b %m %Y %I:%M %p"),
                            ) # Don't use f-strings here, it's messy.
            log_color = self.color_guild_join_leave
            log_time = datetime.datetime.utcnow()

            embed = Facility.get_default_embed(
                title = log_title,
                description = log_content,
                color = log_color,
                timestamp = log_time
            ).set_thumbnail(
                url = member.avatar_url
            ).set_author(
                name = str(member),
                icon_url = member.avatar_url
            ).set_footer(
                text = str(member),
                icon_url = member.avatar_url
            )

            await log_channel.send(embed = embed)
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild = member.guild

        # First we check if the logging feature is enabled in that guild.
        if self.log_check(guild):
            # We retrieve the logging channel for that guild.
            config = Facility.get_config(guild.id)
            log_channel = self.bot.get_channel(config["LOG_CHANNEL"])

            log_title = ""
            log_content = ""
            log_color = None
            log_time = None

            reason = "Not provided."
            executor = None
            
            # When a member is banned/kicked/left by their will, this event will be triggered. 
            # For banning, we already have on_member_ban to deal with.
            # Now we have to separate whether a member is kicked or left on their own will.
            # The approach is to look at the latest kick log and determine if it's the same user.
            # Now, this approach has a flaw, and that's when the kicked member rejoin and left, then it'll log that member as kicked twice. (Not tested yet, just by observating the code)
            # A probably solution for that is to retrieve the time between the on_member_remove, but that's straight up hardcode.

            # We retrieve the latest entry.
            async for entry in guild.audit_logs(limit = 1):
                # If that entry is a kick entry with the same member, then it's a kick. Again, this still has the same flaw.
                if entry.target.id == member.id and entry.action == discord.AuditLogAction.kick:
                    if entry.reason == None:
                        reason = "Not provided."
                    else:
                        reason = entry.reason
                    
                    executor = entry.user
                    log_time = entry.created_at

                    log_title = "Member Kicked"
                    log_content = f'''
                                    **Member:** {member.mention}
                                    **Member Name:** {member}
                                    **Reason:** {reason}
                                    ----------------------------
                                    **Kicked by:** {executor.mention}
                                    '''
                    log_color = self.color_moderation
                    
                    embed = Facility.get_default_embed(
                        title = log_title, 
                        description = log_content, 
                        color = log_color, 
                        timestamp = log_time
                    ).set_thumbnail(
                        url = member.avatar_url
                    ).set_author(
                        name = str(executor),
                        icon_url = executor.avatar_url
                    ).set_footer(
                        text = str(executor),
                        icon_url = executor.avatar_url
                    )

                    await log_channel.send(embed = embed)

                # We still want to display the leave message, so we need this.
                log_title = "Member Left"
                log_content = f'''
                                **Member:** {member.mention}
                                **Member name:** {member}
                                ----------------------------
                                **Member ID:** {member.id}
                                '''
                log_color = self.color_guild_join_leave
                log_time = datetime.datetime.utcnow()

                embed = Facility.get_default_embed(
                    title = log_title, 
                    description = log_content, 
                    color = log_color, 
                    timestamp = log_time
                ).set_thumbnail(
                    url = member.avatar_url
                ).set_author(
                    name = str(member),
                    icon_url = member.avatar_url
                ).set_footer(
                    text = str(member),
                    icon_url = member.avatar_url
                )

                await log_channel.send(embed = embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        guild = before.guild

        # First we check if the logging feature is enabled in that guild.
        if self.log_check(guild):
            # We retrieve the logging channel for that guild.
            config = Facility.get_config(guild.id)
            log_channel = self.bot.get_channel(config["LOG_CHANNEL"])

            log_title = ""
            log_content = ""
            log_color = self.color_change
            log_time = None

            executor = None
            flag = False # Avoid displaying embed if the member change their activity / status because it's spammy (and unnecessary).

            async for entry in guild.audit_logs(limit = 1):
                executor = entry.user
                log_time = entry.created_at

                # If the role changed.
                if entry.action == discord.AuditLogAction.member_role_update:
                    flag = True

                    # First, we check is it a role remove, or a role add.
                    # The check is simple, if the previous role list is longer, it's a role remove, if the after role list is longer, it's a role add; there's no otherwise.
                    # A role add can be performed multiple roles (add_roles() in dpy), so we display all of them. Same goes for role remove.

                    old_roles = before.roles
                    new_roles = after.roles

                    role_change = []
                    if len(old_roles) < len(new_roles):
                        log_title = "Member Role Added"
                        role_change = [Facility.mention(role) for role in new_roles if role not in old_roles]

                        # The role_change will contain something like this: ["<@&1234>", "<@&2345>", ...]

                        log_content = f'''
                                        **Member:** {after.mention}
                                        **Member Name:** {after}
                                        **Role added:** {Facility.striplist(role_change)}
                                        ----------------------------
                                        **Added by:** {executor.mention}
                                        '''
                    elif len(old_roles) > len(new_roles):
                        log_title = "Member Role Removed"
                        role_change = [Facility.mention(role) for role in old_roles if role not in new_roles]

                        log_content = f'''
                                        **Member:** {after.mention}
                                        **Member Name:** {after}
                                        **Role removed:** {str(role_change).strip("[']")}
                                        ----------------------------
                                        **Removed by:** {executor.mention}
                                        '''
                    # There was an unknown bug that print an empty embed for no reason.
                    # TODO: Find out what happened.
                    else:
                        flag = False
                # If the nickname changed OR they're mute/deafen/... We currently don't update voice channel logging yet (cuz it's unnecessary in my opinion)
                elif entry.action == discord.AuditLogAction.member_update:
                    flag = True

                    # The approach is simple: check the before nickname and the after nickname.
                    # There are also cases that the before nickname is None and vice versa, so we need to set accordingly to the original name.

                    old_nick = before.nick
                    new_nick = after.nick

                    if old_nick == new_nick:
                        return
                    elif old_nick == None:
                        old_nick = before.name
                    elif new_nick == None:
                        new_nick = after.name
                    
                    log_title = "Nickname Changed"
                    log_content = f'''
                                    **Before:** {old_nick}
                                    **After:** {new_nick}
                                    ----------------------------
                                    **Edited by:** {executor.mention}
                                    '''
                
                if flag:
                    embed = Facility.get_default_embed(
                        title = log_title, 
                        description = log_content, 
                        color = log_color, 
                        timestamp = log_time
                    ).set_thumbnail(
                        url = after.avatar_url
                    ).set_author(
                        name = str(executor), 
                        icon_url = executor.avatar_url
                    ).set_footer(
                        text = str(executor),
                        icon_url = executor.avatar_url
                    )

                    await log_channel.send(embed = embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        guild = channel.guild

        # First we check if the logging feature is enabled in that guild.
        if self.log_check(guild):
            # We retrieve the logging channel for that guild.
            config = Facility.get_config(guild.id)
            log_channel = self.bot.get_channel(config["LOG_CHANNEL"])

            log_title = ""
            log_content = ""
            log_color = self.color_create
            log_time = None

            executor = None

            # Simply look into the audit log and get the information.
            # There are 3 types of channel we're interested: TextChannel, VoiceChannel and CategoryChannel (aka category)
            # We simply just check if it's an instance of one of those three.
            async for entry in guild.audit_logs(limit = 1, action = discord.AuditLogAction.channel_create):
                executor = entry.user
                log_time = entry.created_at

                if isinstance(channel, discord.TextChannel):
                    log_title = "Text Channel Created"
                    log_content = '''
                                    **Name:** `%s`
                                    **Jump to:** %s
                                    **Category:** `%s`
                                    **Created by:** %s
                                    ----------------------------
                                    **ID:** %d
                                    **Is NSFW:** %s
                                    **Position:** %d
                                    ''' % (
                                        channel.name,
                                        channel.mention,
                                        channel.category.name if channel.category != None else "<None>", 
                                        executor.mention,

                                        channel.id, 
                                        "Yes" if channel.is_nsfw() else "No", 
                                        channel.position
                                    ) # Don't f-strings this.

                elif isinstance(channel, discord.VoiceChannel):
                    # We'll probably cover some info about bitrate in the future.
                    log_title = "Voice Channel Created"
                    log_content = '''
                                    **Name:** `%s`
                                    **Jump to:** %s
                                    **Category:** `%s`
                                    **Created by:** %s
                                    ----------------------------
                                    **ID:** %d
                                    **Position:** %d
                                    ''' % (
                                        channel.name, 
                                        channel.mention,
                                        channel.category.name if channel.category != None else "<None>",
                                        executor.mention,

                                        channel.id, 
                                        channel.position
                                    ) # Don't f-strings this.

                elif isinstance(channel, discord.CategoryChannel):
                    log_title = "Category Created"
                    log_content = '''
                                    **Name:** `%s`
                                    **Created by:** %s
                                    ----------------------------
                                    **ID:** %d
                                    **Position:** %d
                                    ''' % (
                                        channel.name, 
                                        executor.mention, 

                                        channel.id, 
                                        channel.position
                                    ) # Don't f-strings this.
                
                embed = Facility.get_default_embed(
                    title = log_title, 
                    description = log_content, 
                    color = log_color,
                    timestamp = log_time
                ).set_author(
                    name = str(executor),
                    icon_url = executor.avatar_url
                ).set_footer(
                    text = str(executor),
                    icon_url = executor.avatar_url
                )

                await log_channel.send(embed = embed)
    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        guild = channel.guild

        # First we check if the logging feature is enabled in that guild.
        if self.log_check(guild):
            # We retrieve the logging channel for that guild.
            config = Facility.get_config(guild.id)
            log_channel = self.bot.get_channel(config["LOG_CHANNEL"])
            
            log_title = ""
            log_content = ""
            log_color = self.color_delete
            log_time = None

            executor = None

            # Same idea as on_guild_channel_create.
            async for entry in guild.audit_logs(limit = 1, action = discord.AuditLogAction.channel_delete):
                executor = entry.user
                log_time = entry.created_at

                if isinstance(channel, discord.TextChannel):
                    log_title = "Text Channel Deleted"
                    log_content = '''
                                    **Name:** `%s`
                                    **Category:** `%s`
                                    **Deleted by:** %s
                                    ----------------------------
                                    **ID:** %d
                                    **Was NSFW:** %s
                                    **Position:** %d
                                    ''' % (
                                        channel.name, 
                                        channel.category.name if channel.category != None else "<None>", 
                                        executor.mention,

                                        channel.id, 
                                        "Yes" if channel.is_nsfw() else "No", 
                                        channel.position
                                    ) # Don't f-strings this.

                elif isinstance(channel, discord.VoiceChannel):
                    log_title = "Voice Channel Deleted"
                    log_content = '''
                                    **Name:** `%s`
                                    **Category:** `%s`
                                    **Deleted by:** %s
                                    ----------------------------
                                    **ID:** %d
                                    **Position:** %d
                                    ''' % (
                                        channel.name, 
                                        channel.category.name if channel.category != None else "<None>",
                                        executor.mention,

                                        channel.id, 
                                        channel.position
                                    ) # Don't f-strings this.

                elif isinstance(channel, discord.CategoryChannel):
                    log_title = "Category Deleted"
                    log_content = '''
                                    **Name:** `%s`
                                    **Deleted by:** %s
                                    ----------------------------
                                    **ID:** %d
                                    **Position:** %d
                                    ''' % (
                                        channel.name, 
                                        executor.mention,

                                        channel.id, 
                                        channel.position
                                    ) # Don't f-strings this.
                
                embed = Facility.get_default_embed(
                    title = log_title, 
                    description = log_content, 
                    color = log_color,
                    timestamp = log_time
                )
                embed.set_author(
                    name = str(executor),
                    icon_url = executor.avatar_url
                )
                embed.set_footer(
                    text = str(executor),
                    icon_url = executor.avatar_url
                )

                await log_channel.send(embed = embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        guild = before.guild

        # First we check if the logging feature is enabled in that guild.
        if self.log_check(guild):
            # We retrieve the logging channel for that guild.
            config = Facility.get_config(guild.id)
            log_channel = self.bot.get_channel(config["LOG_CHANNEL"])

            log_title = ""
            log_content = ""
            log_color = self.color_change
            log_time = None

            executor = None

            # We have 4 changes possible to a channel: name, topic, position and permission.
            # name and topic is self-explanatory: we just need to check the prev name/topic and after name/topic.
            # We don't support position yet, because it's spammy if you move a channel way up/down. TODO: Find alternatives.
            # Permission is one heck of a problem, and will be explained clearer down below.
            async for entry in guild.audit_logs(action = discord.AuditLogAction.channel_update, limit = 1):
                executor = entry.user
                log_time = entry.created_at

                if before.name != after.name:
                    log_title = "Channel Name Changed"
                    log_content = f'''
                                    **Channel:** {after.mention}
                                    **Before:** {before.name}
                                    **After:** {after.name}
                                    ----------------------------
                                    **Channel ID:** {after.id}
                                    **Changed by:** {executor.mention}
                                    '''
                    
                    # Put embed inside here instead of outside because user can change multiple thing before pressing save.
                    embed = Facility.get_default_embed(
                        title = log_title, 
                        description = log_content, 
                        color = log_color, 
                        timestamp = log_time
                    ).set_author(
                        name = str(executor),
                        icon_url = executor.avatar_url
                    ).set_footer(
                        text = str(executor),
                        icon_url = executor.avatar_url
                    )

                    await log_channel.send(embed = embed)
                # Archived, can cause spamming if move a channel way up/down.
                if before.position != after.position:
                    pass
                if before.topic != after.topic and before.topic != None: # For some reasons, changing the name of a new channel will also call this.
                    log_title = "Channel Topic Changed"
                    log_content = f'''
                                    **Channel:** {after.mention}
                                    **Before:** {before.topic}
                                    **After:** {after.topic}
                                    ----------------------------
                                    **Channel ID:** {after.id}
                                    **Changed by:** {executor.mention}
                                    '''
                    
                    embed = Facility.get_default_embed(
                        title = log_title, 
                        description = log_content, 
                        color = log_color, 
                        timestamp = log_time
                    ).set_author(
                        name = str(entry.user),
                        icon_url = entry.user.avatar_url
                    ).set_footer(
                        text = str(entry.user),
                        icon_url = entry.user.avatar_url
                    )
                    
                    await log_channel.send(embed = embed)
            # The structure of overwrites look like this:
            # class PermissionOverwrite { self.send_messages = True/None/False; self.read_messages = True/None/False;...}
            # before.overwrites and after.overwrites return sth like this:
            # {"Role/Member": PermissionOverwrite, "Role/Member": PermissionOverwrite,...}
            # which is a dict.
            #
            # So first of, we check if there are any new keys or missing keys
            # If yes, then it's permission added/removed, and we look for the key and its value.
            # If no, we'll check every keys if is there any differences in the PermissionOverwrite part (remember, Channel.overwrites is a dict)
            # Then we iterate (by iter()) through all the attributes in PermissionOverwrite for before and after
            # If there's sth different, then we log it right away, because a user can edit many permissions before one press "Save Changes".
            async for entry in guild.audit_logs(action = discord.AuditLogAction.overwrite_update, limit = 1):
                executor = entry.user
                log_time = entry.created_at

                if before.overwrites != after.overwrites:
                    action = ""
                    permission = None
                    target_type = ""

                    for key in after.overwrites:

                        # If there's a permission added (add permission for a member/role)
                        if key not in before.overwrites:
                            log_title = "Channel Permission Added"
                            log_content = '''
                                            **Target:** %s (%s)
                                            ----------------------------
                                            **Channel:** %s
                                            **Added by:** %s
                                            ''' % (
                                                Facility.mention(key), 
                                                "Role" if isinstance(key, discord.Role) else "Member", 

                                                after.mention, 
                                                executor.mention
                                            )
                            
                            embed = Facility.get_default_embed(
                                title = log_title, 
                                description = log_content, 
                                color = log_color, 
                                timestamp = log_time
                            ).set_author(
                                name = str(executor),
                                icon_url = executor.avatar_url
                            ).set_footer(
                                text = str(executor),
                                icon_url = executor.avatar_url
                            )

                            await log_channel.send(embed = embed)
                            
                        else:
                            # If the current key with the overwrite is different, then we start the process.
                            if before.overwrites[key] != after.overwrites[key]:
                                if isinstance(key, discord.Role):
                                    target_type = "Role"
                                else:
                                    target_type = "Member"
                        
                            # This is not confirmed if true or not, but discord.PermissionOverwrite is quite similar to
                            # discord.Permissions, except that it has None.

                            # Retrieve a PermissionOverwrite object.
                            before_overwrite = before.overwrites[key]
                            after_overwrite = after.overwrites[key]
                            
                            # Get the iter to iterate through the PermissionOverwrite.
                            iter_before = iter(before_overwrite)
                            iter_after = iter(after_overwrite)

                            granted = []
                            neutralized = []
                            denied = []

                            while True:
                                try:
                                    i_before = next(iter_before) # i_before and i_after is a tuple of (perm, False/None/True)
                                    i_after = next(iter_after)

                                    if i_before != i_after:
                                        permission = self.channel_dpyperms_to_dperms(i_after[0])
                                        if i_after[1]:
                                            action = "`%s`: " % permission
                                            if i_before[1] is None:
                                                action += "`Neutralized -> Granted`"
                                            else:
                                                action += "`Denied -> Granted`"

                                            granted.append(action)
                                        elif i_after[1] is None:
                                            action = "`%s`: " % permission
                                            if i_before[1]:
                                                action += "`Granted -> Neutralized`"
                                            else:
                                                action += "`Denied -> Neutralized`"

                                            neutralized.append(action)
                                        else:
                                            action = "`%s`: " % permission
                                            if i_before[1] is None:
                                                action += "`Neutralized -> Denied`"
                                            else:
                                                action += "`Granted -> Denied`"

                                            denied.append(action)
                                except StopIteration:
                                    break
                                
                            if len(granted) == 0 and len(neutralized) == 0 and len(denied) == 0:
                                continue
                            
                            # Visual format...
                            # TODO: Change the process to local functions cuz it's repetitive af

                            # Remove the [] and ' in the list...
                            granted_message = Facility.striplist(granted)
                            neutralized_message = Facility.striplist(neutralized)
                            denied_message = Facility.striplist(denied)
                            
                            if granted_message == "":
                                pass
                            elif neutralized_message == "" and granted_message != "" and denied_message != "":
                                neutralized_message = '\n\n'
                            elif granted_message != "" and neutralized_message != "" and denied_message == "":
                                granted_message += '\n\n'
                            elif granted_message != "" and neutralized_message != "" and denied_message != "":
                                granted_message += '\n\n'
                                neutralized_message += '\n\n'
                            
                            # Now the string will be like `Perm`: `PreState -> NewState`, `Perm`: `PreState -> NewState`, ...
                            # This part is to insert newline after the comma.
                            for i in range(0, len(granted_message)):
                                if granted_message[i] == ',':
                                    granted_message = granted_message[0:(i + 1)] + '\n' + granted_message[(i + 1):]
                            for i in range(0, len(neutralized_message)):
                                if neutralized_message[i] == ',':
                                    neutralized_message = neutralized_message[0:(i + 1)] + '\n' + neutralized_message[(i + 1):]
                            for i in range(0, len(denied_message)):
                                if denied_message[i] == ',':
                                    denied_message = denied_message[0:(i + 1)] + '\n' + denied_message[(i + 1):]


                            log_title = "Channel Permission Changed"
                            log_content = f'''
                                            **Target:** {key.mention} ({target_type})

                                            {granted_message}{neutralized_message}{denied_message}

                                            ----------------------------
                                            **Channel:** {after.mention}
                                            **Changed by:** {executor.mention}
                                            '''
                            
                            embed = Facility.get_default_embed(
                                title = log_title,
                                description = log_content,
                                color = log_color,
                                timestamp = log_time
                            ).set_author(
                                name = str(executor),
                                icon_url = executor.avatar_url
                            ).set_footer(
                                text = str(executor),
                                icon_url = executor.avatar_url
                            )

                            await log_channel.send(embed = embed)

                    for key in before.overwrites:
                        if key not in after.overwrites:
                            log_title = "Channel Permission Removed"
                            log_content = '''
                                            **Target:** %s (%s)
                                            ----------------------------
                                            **Channel:** %s
                                            **Removed by:** %s
                                            ''' % (
                                                Facility.mention(key), 
                                                "Role" if isinstance(key, discord.Role) else "Member", 

                                                after.id, 
                                                executor.mention
                                            )
                            
                            embed = Facility.get_default_embed(
                                title = log_title, 
                                description = log_content, 
                                color = log_color, 
                                timestamp = log_time
                            )
                            embed.set_author(
                                name = str(executor),
                                icon_url = executor.avatar_url
                            )
                            embed.set_footer(
                                text = str(executor),
                                icon_url = executor.avatar_url
                            )

                            await log_channel.send(embed = embed)

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        # First we check if the logging feature is enabled in that guild.
        if self.log_check(after.guild):
            # We retrieve the logging channel for that guild
            config = Facility.get_config(after.guild.id)
            log_channel = self.bot.get_channel(config["LOG_CHANNEL"])

            log_title = ""
            log_content = ""
            log_color = self.color_change
            log_time = None

            executor = None

            async for entry in after.guild.audit_logs(action = discord.AuditLogAction.guild_update, limit = 1):
                executor = entry.user
                log_time = entry.created_at

                flag = False

                if hasattr(entry.before, "name") and hasattr(entry.after, "name"):
                    flag = True
                    log_title = "Server Name Changed"
                    log_content = f'''
                                    **Before:** {before.name}
                                    **After:** {after.name}
                                    ----------------------------
                                    **Changed by:** {executor.mention}
                                    '''
                elif hasattr(entry.before, "owner") and hasattr(entry.after, "owner"):
                    flag = True
                    log_title = "Server Owner Changed"
                    log_content = f'''
                                    **Before:** {before.owner.mention}
                                    **After:** {after.owner.mention}
                                    '''
                
                if flag:
                    embed = Facility.get_default_embed(
                        title = log_title,
                        description = log_content,
                        color = log_color,
                        timestamp = log_time
                    ).set_author(
                        name = str(executor),
                        icon_url = executor.avatar_url
                    ).set_footer(
                        text = str(executor),
                        icon_url = executor.avatar_url
                    )

                    await log_channel.send(embed = embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        guild = role.guild

        # First we check if the logging feature is enabled in that guild.
        if self.log_check(guild):
            # We retrieve the logging channel for that guild.
            config = Facility.get_config(guild.id)
            log_channel = self.bot.get_channel(config["LOG_CHANNEL"])

            log_title = "Role Created"
            log_content = ""
            log_color = self.color_create
            log_time = None

            executor = None

            async for entry in guild.audit_logs(action = discord.AuditLogAction.role_create, limit = 1):
                log_time = entry.created_at
                executor = entry.user

                role_perm = []
                
                # Painful experience :D
                if role.permissions.administrator:
                    role_perm.append("Administrator")
                if role.permissions.view_audit_log:
                    role_perm.append("View Audit Log")
                if role.permissions.manage_guild:
                    role_perm.append("Manage Server")
                if role.permissions.manage_roles:
                    role_perm.append("Manage Roles")
                if role.permissions.manage_channels:
                    role_perm.append("Manage Channels")
                if role.permissions.kick_members:
                    role_perm.append("Kick Members")
                if role.permissions.ban_members:
                    role_perm.append("Ban Members")
                if role.permissions.create_instant_invite:
                    role_perm.append("Create Invite")
                if role.permissions.change_nickname:
                    role_perm.append("Change Nickname")
                if role.permissions.manage_nicknames:
                    role_perm.append("Manage Nicknames")
                if role.permissions.manage_emojis:
                    role_perm.append("Manage Emojis")
                if role.permissions.manage_webhooks:
                    role_perm.append("Manage Webhooks")
                if role.permissions.send_messages:
                    role_perm.append("Send Messages")
                if role.permissions.send_tts_messages:
                    role_perm.append("Send TTS Messages")
                if role.permissions.embed_links:
                    role_perm.append("Embed Links")
                if role.permissions.attach_files:
                    role_perm.append("Attach Files")
                if role.permissions.read_message_history:
                    role_perm.append("Read Message History")
                if role.permissions.mention_everyone:
                    role_perm.append("Mention Everyone")
                if role.permissions.external_emojis:
                    role_perm.append("Use External Emojis")
                if role.permissions.add_reactions:
                    role_perm.append("Add Reactions")
                if role.permissions.connect:
                    role_perm.append("Connect")
                if role.permissions.speak:
                    role_perm.append("Speak")
                if role.permissions.mute_members:
                    role_perm.append("Mute Members")
                if role.permissions.deafen_members:
                    role_perm.append("Deafen Members")
                if role.permissions.move_members:
                    role_perm.append("Move Members")
                if role.permissions.use_voice_activation:
                    role_perm.append("Use Voice Activity")
                if role.permissions.priority_speaker:
                    role_perm.append("Priority Speaker")
                if role.permissions.stream:
                    role_perm.append("Go Live")
                
                str_role_perm = ""
                for perm in role_perm:
                    str_role_perm += "`%s` " % perm

                # TODO: Although this method will bypass user created role, it'll not pass the bot created role, as bot created role can have denied permissions on creation.
                log_content = '''
                                **Role:** %s
                                **Name:** %s
                                **Created by:** %s
                                **Granted Permissions:** %s
                                ----------------------------
                                **Is separated:** %s
                                **Is mentionable:** %s
                                **Color:** %s
                                ''' % (
                                    Facility.mention(role), # It's unlikely for this role to be @everyone but consistency is nice. 
                                    role.name, 
                                    executor.mention, 
                                    str_role_perm,
                                    "Yes" if role.hoist else "No",
                                    "Yes" if role.mentionable else "No",
                                    str(role.color)
                                )

                embed = Facility.get_default_embed(
                    title = log_title,
                    description = log_content,
                    color = log_color,
                    timestamp = log_time
                ).set_author(
                    name = str(executor),
                    icon_url = executor.avatar_url
                ).set_footer(
                    text = str(executor),
                    icon_url = executor.avatar_url
                )

                await log_channel.send(embed = embed)
    
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        guild = role.guild

        # First we check if the logging feature is enabled in that guild.
        if self.log_check(guild):
            # We retrieve the logging channel for that guild.
            config = Facility.get_config(guild.id)
            log_channel = self.bot.get_channel(config["LOG_CHANNEL"])

            log_title = "Role Deleted"
            log_content = ""
            log_color = self.color_delete
            log_time = None

            executor = None

            async for entry in guild.audit_logs(action = discord.AuditLogAction.role_delete, limit = 1):
                log_time = entry.created_at
                executor = entry.user
            
                log_content = '''
                                **Name:** `%s`
                                **Deleted by:** %s
                                ----------------------------
                                **Was separated:** %s
                                **Was mentionable:** %s
                                **Color:** %s
                                ''' % (
                                    role.name,
                                    executor.mention,
                                    "Yes" if role.hoist else "No",
                                    "Yes" if role.mentionable else "No",
                                    str(role.color)
                                )
                
                embed = Facility.get_default_embed(
                    title = log_title,
                    description = log_content,
                    color = log_color,
                    timestamp = log_time
                ).set_author(
                    name = str(executor),
                    icon_url = executor.avatar_url
                ).set_footer(
                    text = str(executor),
                    icon_url = executor.avatar_url
                )

                await log_channel.send(embed = embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        guild = before.guild

        # First we check if the logging feature is enabled in that guild.
        if self.log_check(guild):
            # We retrieve the logging channel for that guild.
            config = Facility.get_config(guild.id)
            log_channel = self.bot.get_channel(config["LOG_CHANNEL"])

            log_title = ""
            log_content = ""
            log_color = self.color_change
            log_time = None

            executor = None

            async for entry in guild.audit_logs(action = discord.AuditLogAction.role_update, limit = 1):
                log_time = entry.created_at
                executor = entry.user

                if before.name != after.name:
                    log_title = "Role Name Changed"
                    log_content = f'''
                                    **Role:** {Facility.mention(after)}
                                    **Before:** {before.name}
                                    **After:** {after.name}
                                    ----------------------------
                                    **Changed by:** {executor.mention}
                                    '''
                    
                    embed = Facility.get_default_embed(
                        title = log_title,
                        description = log_content,
                        color = log_color,
                        timestamp = log_time
                    ).set_author(
                        name = str(executor),
                        icon_url = executor.avatar_url
                    ).set_footer(
                        text = str(executor),
                        icon_url = executor.avatar_url
                    )

                    await log_channel.send(embed = embed)
                if before.color != after.color:
                    log_title = "Role Color Changed"
                    log_content = f'''
                                    **Role:** {Facility.mention(after)}
                                    **Before:** {before.color}
                                    **After:** {after.color}
                                    ----------------------------
                                    **Changed by:** {executor.mention}
                                    '''
                    
                    embed = Facility.get_default_embed(
                        title = log_title,
                        description = log_content,
                        color = log_color,
                        timestamp = log_time
                    ).set_author(
                        name = str(executor),
                        icon_url = executor.avatar_url
                    ).set_footer(
                        text = str(executor),
                        icon_url = executor.avatar_url
                    )

                    await log_channel.send(embed = embed)
                # The next 2 seems unimportant, so skip those for now.
                if before.mentionable != after.mentionable:
                    pass
                if before.hoist != after.hoist:
                    pass
                # Quite similar to on_guild_channel_update
                # However, it's easier because it's a Permission, which only have False/True field.
                # And also, before.permissions directly return a Permission instead of a dictionary of {"key": PermissionOverwrite}
                if before.permissions != after.permissions:
                    action = ""
                    permission = None
                    
                    iter_before = iter(before.permissions)
                    iter_after = iter(after.permissions)

                    granted = []
                    denied = []

                    while True:
                        try:
                            i_before = next(iter_before) # i_before and i_after now is a tuple of (perm, False/True)
                            i_after = next(iter_after)

                            if i_before != i_after:
                                permission = self.role_dpyperms_to_dperms(i_after[0])
                                
                                if i_after[1]:
                                    action = "`%s`: `Denied -> Granted`" % permission
                                    granted.append(action)
                                else:
                                    action = "`%s`: `Granted -> Denied`" % permission
                                    denied.append(action)
                        except StopIteration:
                            break
                    
                    if len(granted) == 0 and len(denied) == 0:
                        return
                    
                    granted_message = Facility.striplist(granted)
                    denied_message = Facility.striplist(denied)

                    if denied_message != "" and granted_message != "":
                        granted_message += "\n\n"
                    
                    log_title = "Role Permission Changed"
                    log_content = f'''
                                    **Target:** {after.name}

                                    {granted_message}{denied_message}

                                    ----------------------------
                                    **Changed by:** {executor.mention}
                                    '''

                    embed = Facility.get_default_embed(
                        title = log_title,
                        description = log_content,
                        color = log_color,
                        timestamp = log_time
                    ).set_author(
                        name = str(executor),
                        icon_url = executor.avatar_url
                    ).set_footer(
                        text = str(executor),
                        icon_url = executor.avatar_url
                    )

                    await log_channel.send(embed = embed)

    @commands.Cog.listener("on_command_error")
    async def command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        
        if self.log_check(ctx.guild):
            config = Facility.get_config(ctx.guild.id)
            log_channel = self.bot.get_channel(config["LOG_CHANNEL"])

            log_title = "Command Raised Error"
            log_content = '''
                            A command raised an error.

                            Command arguments:
                            ```%s %s```
                            Message:
                            ```%s```
                            Error:
                            ```%s```
                            ''' % (ctx.command.name, ctx.command.signature, ctx.message.content, error)
            log_color = self.color_other
            log_time = datetime.datetime.utcnow()

            embed = Facility.get_default_embed(
                title = log_title,
                description = log_content,
                color = log_color,
                timestamp = log_time
            ).set_author(
                name = ctx.author, 
                icon_url = ctx.author.avatar_url
            ).set_footer(
                text = ctx.author, 
                icon_url = ctx.author.avatar_url
            )

            await log_channel.send(embed = embed)

def setup(bot):
    bot.add_cog(Logging(bot))