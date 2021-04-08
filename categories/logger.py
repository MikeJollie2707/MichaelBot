import discord
from discord.ext import commands

import datetime
import aiohttp # External paste site when embed is too large.
import mystbin
import typing # IntelliSense purpose only

import categories.utilities.facility as Facility
from categories.utilities.checks import bot_has_database
from bot import MichaelBot # IntelliSense purpose only

# Specification:
# Every single events here (except raw events) must have the following variables declared at the very first line after checking log:
# - log_channel: the channel that's gonna send the embed. Retrieve using Facility.get_config and config["log_channel"]
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
            self.content += '\n'

        return self
    
    def __str__(self):
        return self.content
    
class Logging(commands.Cog):
    '''Commands related to logging actions in server.'''
    def __init__(self, bot : MichaelBot):
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

    async def log_check(self, guild):
        if guild is None:
            return False
        if bot_has_database(self.bot):
            config = await Facility.get_config(self.bot, guild.id)
            if config["ERROR"] == 0 and config["enable_log"] and config["log_channel"] != 0:
                return True
            elif config["ERROR"] != 0:
                print("Guild not found.")
            elif config["enable_log"] == 0:
                print("Logging not enabled.")
            else:
                print("Log channel not set.")
        
        return False

    @commands.Cog.listener("on_message_delete")
    async def _message_delete(self, message):
        guild = message.guild
        # First we check if the logging feature is enabled in that guild.
        if await self.log_check(guild):
            # Then we get the log channel of that guild.
            config = await Facility.get_config(self.bot, guild.id)
            log_channel = self.bot.get_channel(config["log_channel"])

            # Initialize variables according to specification.
            log_title = "Message Deleted"
            log_content = LogContent()
            log_color = self.color_delete
            log_time = None

            executor = message.author

            async for entry in message.guild.audit_logs(action = discord.AuditLogAction.message_delete, limit = 1):
                executor = entry.user
                # Audit log doesn't log message that the author delete himself.
                log_time = datetime.datetime.utcnow()
                
                # Because audit log doesn't log message that the author delete himself,
                # we need to check if the latest message_delete is roughly the same time as the event is fired.
                # 1 second is for offset delay. Increasing this reduce the accuracy.
                # Can't really do anything here except hard-code.
                log_time2 = entry.created_at
                deltatime = log_time - log_time2
                if deltatime.total_seconds() < 1:
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
                embed_message += "\n----------------------------"
            
            if len(content_message + attachment_message + embed_message) < 2000:
                log_content.append(
                    "%s%s%s" % (content_message, attachment_message, embed_message),
                    "**Author:** %s" % message.author.mention,
                    "**Deleted by:** %s" % executor.mention,
                    "----------------------------",
                    "**Channel:** %s" % message.channel.mention
                )
            else:
                mystbin_client = mystbin.Client()
                paste = await mystbin_client.post(content_message + attachment_message + embed_message, syntax = "md")
                log_content.append(
                    "The log content is too long! View the full text here: ",
                    f"<{paste}>",
                    "**Author:** %s" % message.author.mention,
                    "**Deleted by:** %s" % executor.mention,
                    "----------------------------",
                    "**Channel:** %s" % message.channel.mention
                )
                await mystbin_client.close()

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

    @commands.Cog.listener("on_bulk_message_delete")
    async def _bulk_message_delete(self, messages):
        pass

    @commands.Cog.listener("on_raw_message_edit")
    async def _raw_message_edit(self, payload):
        if payload.cached_message != None: # on_message_edit
            return
        
        guild = self.bot.get_channel(payload.channel_id).guild
        if await self.log_check(guild):
            config = await Facility.get_config(self.bot, guild.id)
            log_channel = self.bot.get_channel(config["log_channel"])

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
                "**Author:** %s" % edited_message.author.mention,
                "----------------------------",
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
    
    @commands.Cog.listener("on_message_edit")
    async def _message_edit(self, before, after):
        # We don't log bot messages yet.
        if after.author.bot == False:
            guild = before.guild
            # First we check if the logging feature is enabled in that guild.
            if await self.log_check(guild):
                # Then we get the log channel of that guild.
                config = await Facility.get_config(self.bot, guild.id)
                log_channel = self.bot.get_channel(config["log_channel"])

                BASE_URL = "https://hastebin.com/"

                log_title = "Message Edited"
                log_content = LogContent()

                # Basically, we generally have 3 types of messages: normal text, attachments and embeds.
                # However, attachments can't be edited, so that's one task down.
                # For the rest, just do like message_delete.
                content_message = "**Content before:** %s\n**Content after:** %s" % (before.content, after.content) if after.content != "" else ""

                # Although a normal user can't really edit embed, it's just for fun to support embed editing.
                # Basically compare two lists of embeds and display if they're different.
                embed_message = ""

                if before.embeds != after.embeds:
                    import json
                    embed_message = "\n----------------------------\n" if content_message != "" else ""
                    counter = 1
                    for embed in before.embeds:
                        embed_message += "Embed %d before:\n" % counter
                        embed_message += "```%s```" % json.dumps(embed.to_dict(), indent = 2)
                        counter += 1
                    counter = 1
                    for embed in after.embeds:
                        embed_message += "Embed %d after:\n" % counter
                        embed_message += "```%s```" % json.dumps(embed.to_dict(), indent = 2)
                        counter += 1
                
                # Exceed max character check. 1800 to avoid cases when the Author and below part exceed max char limit.
                if len(content_message + embed_message) < 1800:
                    log_content.append(
                        content_message,
                        "**Author:** %s" % after.author.mention,
                        "----------------------------",
                        "**Message URL**: [Jump to message](%s)"  % after.jump_url,
                        "**Channel:** %s" % after.channel.mention
                    )
                else:
                    mystbin_client = mystbin.Client()
                    paste = await mystbin_client.post(content_message + embed_message, syntax = "md")
                    log_content.append(
                        "The log content is too long! View the full text here: ",
                        f"<{paste}>",
                        "**Author:** %s" % after.author.mention,
                        "----------------------------",
                        "**Message URL**: [Jump to message](%s)" % after.jump_url,
                        "**Channel:** %s" % after.channel.mention
                    )
                    await mystbin_client.close()
                
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
    
    @commands.Cog.listener("on_member_ban")
    async def _member_ban(self, guild, user):
        # First we check if the logging feature is enabled in that guild.
        if await self.log_check(guild):
            # Then we get the log channel of that guild.
            config = await Facility.get_config(self.bot, guild.id)
            log_channel = self.bot.get_channel(config["log_channel"])

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
                
                log_content.append(
                    "**User:** %s" % user.mention,
                    "**User Name:** %s" % user,
                    "**Reason:** %s" % reason,
                    "----------------------------",
                    "**Banned by:** %s" % executor.mention
                )

                embed = Facility.get_default_embed(
                    title = log_title,
                    description = log_content.content,
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

    @commands.Cog.listener("on_member_unban")
    async def _member_unban(self, guild, user):
        # First we check if the logging feature is enabled in that guild.
        if await self.log_check(guild):
            # Then we get the log channel of that guild.
            config = await Facility.get_config(self.bot, guild.id)
            log_channel = self.bot.get_channel(config["log_channel"])

            log_title = "User Unbanned"
            log_content = LogContent()
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
                
                log_content.append(
                    "**User:** %s" % user.mention,
                    "**User Name:** %s" % user,
                    "**Reason:** %s" % reason,
                    "----------------------------",
                    "**Unbanned by:** %s" % executor.mention
                )
                
                embed = Facility.get_default_embed(
                    title = log_title, 
                    description = log_content.content, 
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

    @commands.Cog.listener("on_member_join")
    async def _member_join(self, member):
        guild = member.guild

        # First we check if the logging feature is enabled in that guild.
        if await self.log_check(guild):
            import humanize
            # Then we get the log channel of that guild.
            config = await Facility.get_config(self.bot, guild.id)
            log_channel = self.bot.get_channel(config["log_channel"])

            log_title = "Member Joined"
            log_content = LogContent().append(
                "**Member:** %s" % member.mention,
                "**Member Name:** %s" % str(member),
                "----------------------------",
                "**Member ID:** %d" % member.id,
                "**Account created on:** %s (UTC)" % member.created_at.strftime("%b %m %Y %I:%M %p"),
                "**Account age:** %s" % humanize.precisedelta(datetime.datetime.utcnow() - member.created_at, format = '%0.0f')
            )

            log_color = self.color_guild_join_leave
            log_time = datetime.datetime.utcnow()

            embed = Facility.get_default_embed(
                title = log_title,
                description = log_content.content,
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
    
    @commands.Cog.listener("on_member_remove")
    async def _member_remove(self, member):
        guild = member.guild

        # First we check if the logging feature is enabled in that guild.
        if await self.log_check(guild):
            # Then we get the log channel of that guild.
            config = await Facility.get_config(self.bot, guild.id)
            log_channel = self.bot.get_channel(config["log_channel"])

            log_title = ""
            log_content = LogContent()
            log_color = None
            log_time = None

            reason = "Not provided."
            executor = None
            
            # When a member is banned/kicked/left by their will, this event will be triggered. 
            # For banning, we already have on_member_ban to deal with.
            # The approach is to look at the latest kick log and determine if it's the same user.
            # Now, this approach has a flaw, and that's when the kicked member rejoin and left, then it'll log that member as kicked twice.
            # A probably solution for that is to retrieve the time between the on_member_remove, but that's straight up hardcode.

            # We retrieve the latest kick entry.
            async for entry in guild.audit_logs(action = discord.AuditLogAction.kick, limit = 1):
                delta_time = datetime.datetime.utcnow() - entry.created_at
                if entry.target.id == member.id and delta_time.total_seconds() <= 1.0:
                    if entry.reason == None:
                        reason = "Not provided."
                    else:
                        reason = entry.reason
                
                    executor = entry.user
                    log_time = entry.created_at

                    log_title = "Member Kicked"
                    log_content.append(
                        f"**Member:** {member.mention}",
                        f"**Member Name:** {member}",
                        f"**Reason:** {reason}",
                        "----------------------------",
                        f"**Kicked by:** {executor.mention}"
                    )
                    log_color = self.color_moderation
                    
                    embed = Facility.get_default_embed(
                        title = log_title, 
                        description = log_content.content, 
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
                # This is most likely a simple leave
                else:
                    pass

            # We still want to display the leave message, so we need this.
            log_title = "Member Left"
            log_content.append(
                f"**Member:** {member.mention}",
                f"**Member Name:** {member}",
                "----------------------------",
                f"**Member ID:** {member.id}"
            )
            log_color = self.color_guild_join_leave
            log_time = datetime.datetime.utcnow()

            embed = Facility.get_default_embed(
                title = log_title, 
                description = log_content.content, 
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

    @commands.Cog.listener("on_member_update")
    async def _member_update(self, before, after):
        guild = before.guild

        # First we check if the logging feature is enabled in that guild.
        if await self.log_check(guild):
            # Then we get the log channel of that guild.
            config = await Facility.get_config(self.bot, guild.id)
            log_channel = self.bot.get_channel(config["log_channel"])

            log_title = ""
            log_content = LogContent()
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

                        log_content.append(
                            "**Member:** %s" % after.mention,
                            "**Member Name:** %s" % after,
                            "**Role added:** %s" % Facility.striplist(role_change),
                            "----------------------------",
                            "**Added by:** %s" % executor.mention
                        )
                    elif len(old_roles) > len(new_roles):
                        log_title = "Member Role Removed"
                        role_change = [Facility.mention(role) for role in old_roles if role not in new_roles]

                        log_content.append(
                            "**Member:** %s" % after.mention,
                            "**Member Name:** %s" % after,
                            "**Role removed:** %s" % Facility.striplist(role_change),
                            "----------------------------",
                            "**Removed by:** %s" % executor.mention
                        )
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
                    log_content.append(
                        "**Before:** %s" % old_nick,
                        "**After:** %s" % new_nick,
                        "----------------------------",
                        "**Edited by:** %s" % executor.mention 
                    )
                
            if flag:
                embed = Facility.get_default_embed(
                    title = log_title, 
                    description = log_content.content, 
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

    @commands.Cog.listener("on_guild_channel_create")
    async def _guild_channel_create(self, channel):
        guild = channel.guild

       # First we check if the logging feature is enabled in that guild.
        if await self.log_check(guild):
            # Then we get the log channel of that guild.
            config = await Facility.get_config(self.bot, guild.id)
            log_channel = self.bot.get_channel(config["log_channel"])

            log_title = ""
            log_content = LogContent()
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
                    log_content.append(
                        "**Name:** `%s`" % channel.name,
                        "**Jump to:** %s" % channel.mention,
                        "**Category:** `%s`" % channel.category.name if channel.category != None else "<None>",
                        "**Created by:** %s" % executor.mention,
                        "----------------------------",
                        "**ID:** %d" % channel.id,
                        "**Is NSFW:** %s" % ("Yes" if channel.is_nsfw() else "No"),
                        "**Position:** %d" % channel.position
                    )

                elif isinstance(channel, discord.VoiceChannel):
                    # We'll probably cover some info about bitrate in the future.
                    log_title = "Voice Channel Created"
                    log_content.append(
                        "**Name:** `%s`" % channel.name,
                        "**Jump to:** %s" % channel.mention,
                        "**Category:** `%s`" % channel.category.name if channel.category != None else "<None>",
                        "**Created by:** %s" % executor.mention,
                        "----------------------------",
                        "**ID:** %d" % channel.id,
                        "**Position:** %d" % channel.position
                    )

                elif isinstance(channel, discord.CategoryChannel):
                    log_title = "Category Created"
                    log_content.append(
                        "**Name:** `%s`" % channel.name,
                        "**Created by:** %s" % executor.mention,
                        "----------------------------",
                        "**ID:** %d" % channel.id,
                        "**Position:** %d" % channel.position
                    )
                
                embed = Facility.get_default_embed(
                    title = log_title, 
                    description = log_content.content, 
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
    
    @commands.Cog.listener("on_guild_channel_delete")
    async def _guild_channel_delete(self, channel):
        guild = channel.guild

        # First we check if the logging feature is enabled in that guild.
        if await self.log_check(guild):
            # Then we get the log channel of that guild.
            config = await Facility.get_config(self.bot, guild.id)
            log_channel = self.bot.get_channel(config["log_channel"])
            
            log_title = ""
            log_content = LogContent()
            log_color = self.color_delete
            log_time = None

            executor = None

            # Same idea as on_guild_channel_create.
            async for entry in guild.audit_logs(limit = 1, action = discord.AuditLogAction.channel_delete):
                executor = entry.user
                log_time = entry.created_at

                if isinstance(channel, discord.TextChannel):
                    log_title = "Text Channel Deleted"
                    log_content.append(
                        "**Name:** `%s`" % channel.name,
                        "**Category:** `%s`" % channel.category.name if channel.category != None else "<None>",
                        "**Deleted by:** %s" % executor.mention,
                        "----------------------------",
                        "**ID:** %d" % channel.id,
                        "**Was NSFW:** %s" % ("Yes" if channel.is_nsfw() else "No")
                    )

                elif isinstance(channel, discord.VoiceChannel):
                    log_title = "Voice Channel Deleted"
                    log_content.append(
                        "**Name:** `%s`" % channel.name,
                        "**Category:** `%s`" % channel.category.name if channel.category != None else "<None>",
                        "**Deleted by:** %s" % executor.mention,
                        "----------------------------",
                        "**ID:** %d" % channel.id
                    )

                elif isinstance(channel, discord.CategoryChannel):
                    log_title = "Category Deleted"
                    log_content.append(
                        "**Name:** `%s`" % channel.name,
                        "**Deleted by:** %s" % executor.mention,
                        "----------------------------",
                        "**ID:** %d" % channel.id
                    )
                
                embed = Facility.get_default_embed(
                    title = log_title, 
                    description = log_content.content, 
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

    @commands.Cog.listener("on_guild_channel_update")
    async def _guild_channel_update(self, before, after):
        guild = before.guild

        # First we check if the logging feature is enabled in that guild.
        if await self.log_check(guild):
            # Then we get the log channel of that guild.
            config = await Facility.get_config(self.bot, guild.id)
            log_channel = self.bot.get_channel(config["log_channel"])

            log_title = ""
            log_content = LogContent()
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
                    log_content.append(
                        f"**Before:** {before.name}",
                        f"**After:** {after.name}",
                        "----------------------------",
                        f"**Jump to:** {after.mention}",
                        f"**Channel ID:** {after.id}",
                        f"**Changed by:** {executor.mention}"
                    )
                    
                    # Put embed inside here instead of outside because user can change multiple thing before pressing save.
                    embed = Facility.get_default_embed(
                        title = log_title, 
                        description = log_content.content, 
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
                if not isinstance(after, discord.VoiceChannel):
                    if before.topic != after.topic:
                        log_title = "Channel Topic Changed"
                        log_content.append(
                            f"**Channel:** {after.mention}",
                        f"**Before:** {before.topic}",
                        f"**After:** {after.topic}",
                        "----------------------------",
                        f"**Channel ID:** {after.id}",
                        f"**Changed by:** {executor.mention}"
                    )
                    
                    embed = Facility.get_default_embed(
                        title = log_title, 
                        description = log_content.content, 
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
            # First, we'll check if there's any new/missing permissions. We can't compare the len, because you can add
            # and remove one permission and the len is still same. If there is then we'll log it right away.
            # Because you can also edit something while adding/removing stuffs, a check to see any differences
            # is mandatory. If there is then we combine all the changes and log it.
            if before.overwrites != after.overwrites:
                new_permissions = []
                removed_permissions = []
                # A flag to restrict the amount call to Discord API. We want to do this as little as possible.
                retrieved_update = False
                
                # Check new permissions
                for target in after.overwrites:
                    if target not in before.overwrites:
                        if not retrieved_update:
                            async for entry in guild.audit_logs(action = discord.AuditLogAction.overwrite_create, limit = 1):
                                executor = entry.user
                                log_time = entry.created_at
                            retrieved_update = True
                        
                        # If there's a permission added (add permission for a member/role)
                        new_permissions.append("%s (%s)" % (Facility.mention(target), "Role" if isinstance(target, discord.Role) else "Member"))
                if len(new_permissions) != 0:
                    new_perms_str = Facility.striplist(new_permissions)

                    log_title = "Channel Permission Added"
                    log_content.append(
                                "**Target:** %s (%s)" % (Facility.mention(key), "Role" if isinstance(key, discord.Role) else "Member"),
                                "----------------------------",
                                "**Channel:** %s" % after.mention,
                                "**Added by:** %s" % executor.mention
                            )
                            
                            embed = Facility.get_default_embed(
                                title = log_title, 
                                description = log_content.content, 
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
                    log_content = LogContent()
                retrieved_update = False
                
                # Check removed permissions
                for target in before.overwrites:
                    if target not in after.overwrites:
                        if not retrieved_update:
                            async for entry in guild.audit_logs(action = discord.AuditLogAction.overwrite_delete, limit = 1):
                                executor = entry.user
                                log_time = entry.created_at
                            retrieved_update = True
                        
                        removed_permissions.append("%s (%s)" % (Facility.mention(target), "Role" if isinstance(target, discord.Role) else "Member"))                    
                if len(removed_permissions) != 0:
                    removed_perms_str = Facility.striplist(removed_permissions)
                    log_title = "Channel Permission Removed"
                    log_content.append(
                        "**Target:** %s" % removed_perms_str,
                        "----------------------------",
                        "**Channel:** %s" % after.mention,
                        "**Removed by:** %s" % executor.mention
                    )
                    
                            # Retrieve a PermissionOverwrite object.
                            before_overwrite = before.overwrites[key]
                            after_overwrite = after.overwrites[key]
                            
                    await log_channel.send(embed = embed)
                    log_content = LogContent()
                retrieved_update = False

                # Now we deal with edited permissions
                before_target_overwrite = before.overwrites
                after_target_overwrite = after.overwrites

                for target in after_target_overwrite:
                    if target in before_target_overwrite and before_target_overwrite[target] != after_target_overwrite[target]:
                            granted = []
                            neutralized = []
                            denied = []

                            while True:
                                try:
                                    i_before = next(iter_before) # i_before and i_after is a tuple of (perm, False/None/True)
                                    i_after = next(iter_after)

                                    if i_before != i_after:
                                        permission = Facility.convert_channelperms_dpy_discord(i_after[0])
                                        if i_after[1]:
                                            action = "`%s`: " % permission
                                            if i_before[1] is None:
                                                action += "`Neutralized -> Granted`"
                                            else:
                                                action += "`Denied -> Granted`"

                                            granted.append(action)
                                        elif i_after[1] is None:
                                            print(i_after)
                                            print(i_before)
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

                            # Turn list to string.
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
                            log_content.append(
                                "**Target:** %s (%s)" % (Facility.mention(key), target_type),
                                f"\n{granted_message}{neutralized_message}{denied_message}\n",
                                "----------------------------",
                                "**Channel:** %s" % after.mention,
                                "**Changed by:** %s" % executor.mention
                            )
                            
                            embed = Facility.get_default_embed(
                                title = log_title,
                                description = log_content.content,
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
                        log_content = LogContent()
                       
    @commands.Cog.listener("on_guild_update")
    async def _guild_update(self, before, after):
        # First we check if the logging feature is enabled in that guild.
        if await self.log_check(after):
            # Then we get the log channel of that guild.
            config = await Facility.get_config(self.bot, after.id)
            log_channel = self.bot.get_channel(config["log_channel"])

            log_title = ""
            log_content = LogContent()
            log_color = self.color_change
            log_time = None

            executor = None

            async for entry in after.audit_logs(action = discord.AuditLogAction.guild_update, limit = 1):
                executor = entry.user
                log_time = entry.created_at

                flag = False

                if hasattr(entry.before, "name") and hasattr(entry.after, "name"):
                    flag = True
                    log_title = "Server Name Changed"
                    log_content.append(
                        f"**Before:** {before.name}",
                        f"**After:** {after.name}",
                        "----------------------------",
                        f"**Changed by:** {executor.mention}"
                    )
                elif hasattr(entry.before, "owner") and hasattr(entry.after, "owner"):
                    flag = True
                    log_title = "Server Owner Changed"
                    log_content = f'''
                                    **Before:** {before.owner.mention}
                                    **After:** {after.owner.mention}
                                    '''
                    log_content.append(
                        f"**Before:** {before.owner.mention}",
                        f"**After:** {after.owner.mention}"
                    )
                
                if flag:
                    embed = Facility.get_default_embed(
                        title = log_title,
                        description = log_content.content,
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

    @commands.Cog.listener("on_guild_role_create")
    async def _guild_role_create(self, role):
        guild = role.guild

        # First we check if the logging feature is enabled in that guild.
        if await self.log_check(guild):
            # Then we get the log channel of that guild.
            config = await Facility.get_config(self.bot, guild.id)
            log_channel = self.bot.get_channel(config["log_channel"])

            log_title = "Role Created"
            log_content = LogContent()
            log_color = self.color_create
            log_time = None

            executor = None

            async for entry in guild.audit_logs(action = discord.AuditLogAction.role_create, limit = 1):
                log_time = entry.created_at
                executor = entry.user

                role_perm = []
                deny_perm = []
                
                # Painful experience :D
                if role.permissions.administrator:
                    role_perm.append("Administrator")
                else:
                    deny_perm.append("Administrator")
                if role.permissions.view_audit_log:
                    role_perm.append("View Audit Log")
                else:
                    deny_perm.append("View Audit Log")
                if role.permissions.manage_guild:
                    role_perm.append("Manage Server")
                else:
                    deny_perm.append("Manage Server")
                if role.permissions.manage_roles:
                    role_perm.append("Manage Roles")
                else:
                    deny_perm.append("Manage Roles")
                if role.permissions.manage_channels:
                    role_perm.append("Manage Channels")
                else:
                    deny_perm.append("Manage Channels")
                if role.permissions.kick_members:
                    role_perm.append("Kick Members")
                else:
                    deny_perm.append("Kick Members")
                if role.permissions.ban_members:
                    role_perm.append("Ban Members")
                else:
                    deny_perm.append("Ban Members")
                if role.permissions.create_instant_invite:
                    role_perm.append("Create Invite")
                else:
                    deny_perm.append("Create Invite")
                if role.permissions.change_nickname:
                    role_perm.append("Change Nickname")
                else:
                    deny_perm.append("Change Nickname")
                if role.permissions.manage_nicknames:
                    role_perm.append("Manage Nicknames")
                else:
                    deny_perm.append("Manage Nicknames")
                if role.permissions.manage_emojis:
                    role_perm.append("Manage Emojis")
                else:
                    deny_perm.append("Manage Emojis")
                if role.permissions.manage_webhooks:
                    role_perm.append("Manage Webhooks")
                else:
                    deny_perm.append("Manage Webhooks")
                if role.permissions.send_messages:
                    role_perm.append("Send Messages")
                else:
                    deny_perm.append("Send Messages")
                if role.permissions.send_tts_messages:
                    role_perm.append("Send TTS Messages")
                else:
                    deny_perm.append("Send TTS Messages")
                if role.permissions.embed_links:
                    role_perm.append("Embed Links")
                else:
                    deny_perm.append("Embed Links")
                if role.permissions.attach_files:
                    role_perm.append("Attach Files")
                else:
                    deny_perm.append("Attach Files")
                if role.permissions.read_message_history:
                    role_perm.append("Read Message History")
                else:
                    deny_perm.append("Read Message History")
                if role.permissions.mention_everyone:
                    role_perm.append("Mention Everyone")
                else:
                    deny_perm.append("Mention Everyone")
                if role.permissions.external_emojis:
                    role_perm.append("Use External Emojis")
                else:
                    deny_perm.append("Use External Emojis")
                if role.permissions.add_reactions:
                    role_perm.append("Add Reactions")
                else:
                    deny_perm.append("Add Reactions")
                if role.permissions.connect:
                    role_perm.append("Connect")
                else:
                    deny_perm.append("Connect")
                if role.permissions.speak:
                    role_perm.append("Speak")
                else:
                    deny_perm.append("Speak")
                if role.permissions.mute_members:
                    role_perm.append("Mute Members")
                else:
                    deny_perm.append("Mute Members")
                if role.permissions.deafen_members:
                    role_perm.append("Deafen Members")
                else:
                    deny_perm.append("Deafen Members")
                if role.permissions.move_members:
                    role_perm.append("Move Members")
                else:
                    deny_perm.append("Move Members")
                if role.permissions.use_voice_activation:
                    role_perm.append("Use Voice Activity")
                else:
                    deny_perm.append("Use Voice Activity")
                if role.permissions.priority_speaker:
                    role_perm.append("Priority Speaker")
                else:
                    deny_perm.append("Priority Speaker")
                if role.permissions.stream:
                    role_perm.append("Go Live")
                else:
                    deny_perm.append("Go Live")
                
                granted_perms = ""
                for perm in role_perm:
                    granted_perms += "`%s` " % perm
                denied_perms = ""
                for perm in deny_perm:
                    denied_perms += "`%s` " % perm

                # TODO: Although this method will bypass user created role, it'll not pass the bot created role, as bot created role can have denied permissions on creation.
                log_content.append(
                    "**Role:** %s" % Facility.mention(role),
                    "**Name:** %s" % role.name,
                    "**Created by:** %s" % executor.mention,
                    "**Granted Permissions:** %s" % granted_perms,
                    "**Denied Permissions:** %s" % denied_perms,
                    "----------------------------",
                    "**Is separated:** %s" % ("Yes" if role.hoist else "No"),
                    "**Is mentionable:** %s" % ("Yes" if role.mentionable else "No"),
                    "**Color:** %s" % str(role.color)
                )

                embed = Facility.get_default_embed(
                    title = log_title,
                    description = log_content.content,
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
    
    @commands.Cog.listener("on_guild_role_delete")
    async def _guild_role_delete(self, role):
        guild = role.guild

        # First we check if the logging feature is enabled in that guild.
        if await self.log_check(guild):
            # Then we get the log channel of that guild.
            config = await Facility.get_config(self.bot, guild.id)
            log_channel = self.bot.get_channel(config["log_channel"])

            log_title = "Role Deleted"
            log_content = LogContent()
            log_color = self.color_delete
            log_time = None

            executor = None

            async for entry in guild.audit_logs(action = discord.AuditLogAction.role_delete, limit = 1):
                log_time = entry.created_at
                executor = entry.user
            
                log_content.append(
                    "**Name:** `%s`" % role.name,
                    "**Deleted by:** %s" % executor.mention,
                    "----------------------------",
                    "**Was separated:** %s" % ("Yes" if role.hoist else "No"),
                    "**Was mentionable:** %s" % ("Yes" if role.mentionable else "No"),
                    "**Color:** %s" % str(role.color)
                )
                
                embed = Facility.get_default_embed(
                    title = log_title,
                    description = log_content.content,
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

    @commands.Cog.listener("on_guild_role_update")
    async def _guild_role_update(self, before, after):
        guild = before.guild

        # First we check if the logging feature is enabled in that guild.
        if await self.log_check(guild):
            # Then we get the log channel of that guild.
            config = await Facility.get_config(self.bot, guild.id)
            log_channel = self.bot.get_channel(config["log_channel"])

            log_title = ""
            log_content = LogContent()
            log_color = self.color_change
            log_time = None

            executor = None

            async for entry in guild.audit_logs(action = discord.AuditLogAction.role_update, limit = 1):
                log_time = entry.created_at
                executor = entry.user

                if before.name != after.name:
                    log_title = "Role Name Changed"
                    log_content.append(
                        f"**Role:** {Facility.mention(after)}",
                        f"**Before:** {before.name}",
                        f"**After:** {after.name}",
                        "----------------------------",
                        f"**Changed by:** {executor.mention}"
                    )
                    
                    embed = Facility.get_default_embed(
                        title = log_title,
                        description = log_content.content,
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
                    log_content.append(
                        f"**Role:** {Facility.mention(after)}",
                        f"**Before:** {before.color}",
                        f"**After:** {after.color}",
                        "----------------------------",
                        f"**Changed by:** {executor.mention}"
                    )
                    
                    embed = Facility.get_default_embed(
                        title = log_title,
                        description = log_content.content,
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
                                permission = Facility.convert_roleperms_dpy_discord(i_after[0])
                                
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
                    log_content.append(
                        f"**Target:** {after.name}\n",
                        f"{granted_message}{denied_message}\n",
                        "----------------------------",
                        f"**Changed by:** {executor.mention}"
                    )

                    embed = Facility.get_default_embed(
                        title = log_title,
                        description = log_content.content,
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
        
        # First we check if the logging feature is enabled in that guild.
        if await self.log_check(ctx.guild):
            # Then we get the log channel of that guild.
            config = await Facility.get_config(self.bot, ctx.guild.id)
            log_channel = self.bot.get_channel(config["log_channel"])

            log_title = "Command Raised Error"
            log_content = LogContent().append(
                "A command raised an error.\n",
                "Command arguments:",
                "```%s %s```" % (ctx.command.name, ctx.command.signature),
                "Message:"
                "```%s```" % ctx.message.content,
                "Error:",
                "```%s```" % error
            )
            log_color = self.color_other
            log_time = datetime.datetime.utcnow()

            embed = Facility.get_default_embed(
                title = log_title,
                description = log_content.content,
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

def setup(bot : MichaelBot):
    bot.add_cog(Logging(bot))