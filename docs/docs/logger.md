<!-- omit in toc -->
# Logging events

Unlike other categories, this categories only contains logging events for the logging feature of a Discord Bot.

This category has no commands. If you're looking for setting up a logging channel/welcome channel/..., refers to page `Settings`.

*This section will be reformatted in near future.*

<!-- omit in toc -->
## Table of Contents

- [Specification [INTERNAL]](#specification-internal)
- [\_\_init\_\_ [INTERNAL]](#init-internal)
- [log_check [INTERNAL]](#logcheck-internal)
- [role\_dpyperms\_to\_dperms [INTERNAL]](#roledpypermstodperms-internal)
- [channel\_dpyperms\_to\_dperms [INTERNAL]](#channeldpypermstodperms-internal)
- [on\_message\_delete](#onmessagedelete)
- [on\_bulk\_message\_delete [DEVELOPING]](#onbulkmessagedelete-developing)
- [on\_raw\_message\_edit](#onrawmessageedit)
- [on\_message\_edit](#onmessageedit)
- [on\_member\_ban](#onmemberban)
- [on\_member\_unban](#onmemberunban)
- [on\_member\_join](#onmemberjoin)
- [on\_member\_leave](#onmemberleave)
- [on\_member\_update](#onmemberupdate)
- [on\_guild\_channel\_create](#onguildchannelcreate)
- [on\_guild\_channel\_delete](#onguildchanneldelete)
- [on\_guild\_channel\_update](#onguildchannelupdate)
- [on\_guild\_update](#onguildupdate)
- [on\_guild\_role\_create](#onguildrolecreate)
- [on\_guild\_role\_delete](#onguildroledelete)
- [on\_guild\_role\_update](#onguildroleupdate)
- [command_error](#commanderror)

## Specification [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

This is a set of format that the developers must follow while writing events for consistency. Any changes that does not follow this specification will be denied.

**Full Specification:**

```py
# Specification:
# Every single events here (except raw events) must have the following variables declared at the very first line after checking log:
# - log_channel: the channel that's gonna send the embed. Retrieve using gconfig.get_config and config["LOG_CHANNEL"]
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

# Color specification:
# Moderation action = Black
# Warn / Mute = Red
# Change (server change, message change, member change, etc.) = Yellow
# Delete (delete message, delete role, delete channel, etc.) = Orange
# Create (create channel, create role, etc.) = Green
# Join / Leave (server) = Blue
# Other = Teal
```

## \_\_init\_\_ [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A constructor of the category. This set the emoji for the category as `📝`.

This also defines the fixed colors for each audit log action. Any changes that does not follow this specification will be denied.

**Color Specification:**

```py
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
```

## log_check [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

An internal check if a guild enabled logging feature. It **MUST** be the first thing to check when writing any events.

**Full Signature:**

```py
def log_check(self, guild):
```

**Return:**

- `True` if `config["ERROR"] == 0` and `config["STATUS_LOG"] == 1` and `config["LOG_CHANNEL"] != 0`
- `False` otherwise.

## role\_dpyperms\_to\_dperms [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A utility method to convert a role permission to the text.

**Full Signature:**

```py
def role_dpyperms_to_dperms(self, role_permissions : str):
```

**Return type:** `str`

**Example:** `role_dpyperms_to_dperms("manage_guild")` -> `"Manage Server"`

## channel\_dpyperms\_to\_dperms [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A utility method to convert a channel permission to the text.

**Full Signature:**

```py
def channel_dpyperms_to_dperms(self, channel_permissions : str):
```

**Return type:** `str`

**Example:** `channel_dpyperms_to_dperms("manage_channels")` -> `"Manage Channels"`

## on\_message\_delete

An event that is invoked when a message is deleted **if the message is in cache**. 

- If the message isn't in cache, `on_raw_message_delete` is invoked instead.
- If it is a purge, then `on_bulk_message_delete` is invoked instead.

This event falls under `delete` in `AuditLogActionCategory`. The color of the embed is orange.

**Full Signature:**

```py
@commands.Cog.listener()
async def on_message_delete(self, message):
```

**Limitation:**

- The deletor does not always display correctly (due to Discord limitation).

## on\_bulk\_message\_delete [DEVELOPING]

*This section is labeled as [DEVELOPING], which means the function/command is currently under development and not available for testing.*

## on\_raw\_message\_edit

An event that is invoked when a message is edited **even if the message isn't in cache**.

- If the message is in cache, the event will do nothing and leave the task to `on_message_edit`.

This event falls under `update` in `AuditLogActionCategory`. The color of the embed is yellow.

**Full Signature:**

```py
@commands.Cog.listener()
async def on_raw_message_edit(self, payload):
```

**Limitation:**

- The old content of the message cannot be found.
- There is a rare chance that the new content of the message cannot be found.

## on\_message\_edit

An event that is invoked when a message is edited **if the message is in cache**.

- If the message isn't in cache, [`on_raw_message_edit`](#onrawmessageedit) is invoked instead.

This event falls under `update` in `AuditLogActionCategory`. The color of the embed is yellow.

**Full Signature:**

```py
@commands.Cog.listener()
async def on_message_edit(self, before, after):
```

**Limitation:**

- Does not log embed editing.

## on\_member\_ban

An event that is invoked when a user/member is banned.

- The ban action will also invoke `on_member_leave` if the member is in the guild.

The color of the embed is black.

**Full Signature:**

```py
@commands.Cog.listener()
async def on_member_ban(self, guild, user):
```

**Limitation:**

- `None`

## on\_member\_unban

An event that is invoked when a user is unbanned.

The color of the embed is black.

**Full Signature:**

```py
@commands.Cog.listener()
async def on_member_unban(self, guild, user):
```

**Limitation:**

- `None`

## on\_member\_join

An event that is invoked when a user join the guild.

The color of the embed is blue.

**Full Signature:**

```py
@commands.Cog.listener()
async def on_member_join(self, member):
```

**Limitation:**

- `None`

## on\_member\_leave

An event that is invoked when a member leave the guild.

- This event is also invoked when a member is banned/kicked.

The color of the embed is blue.

**Full Signature:**

```py
@commands.Cog.listener()
async def on_member_remove(self, member):
```

**Limitation:**

- When a kicked member rejoin and leave, the member will be logged that the member is kicked twice. (unsure)

## on\_member\_update

An event that is invoked when a member's role changes, a member's status/activity changes, a member's nickname changes or a member is muted/deafened.

This event falls under `update` in `AuditLogActionCategory`. The color of the embed is yellow.

**Full Signature:**

```py
@commands.Cog.listener()
async def on_member_update(self, before, after):
```

**Limitation:**

- Changes in member's status/activity will not be logged by MichaelBot due to unnecessary spamming.
- Changes in member is muted/deafened is currently not be logged by MichaelBot due to the unnecessary logging.

## on\_guild\_channel\_create

An event that is invoked when a channel in a guild is created.

This event falls under `create` in `AuditLogActionCategory`. The color of the embed is green.

**Full Signature:**

```py
@commands.Cog.listener()
async def on_guild_channel_create(self, channel):
```

**Limitation:**

- Does not display bitrate information in `VoiceChannel`.

## on\_guild\_channel\_delete

An event that is invoked when a channel in a guild is deleted.

This event falls under `delete` in `AuditLogActionCategory`. The color of the embed is orange.

**Full Signature:**

```py
@commands.Cog.listener()
async def on_guild_channel_delete(self, channel):
```

**Limitation:**

- Does not display bitrate information in `VoiceChannel`.

## on\_guild\_channel\_update

An event that is invoked when a channel in a guild is edited.

The edit can be either channel's name, channel's topic, channel's position or channel's permission.

This event falls under `update` in `AuditLogActionCategory`. The color of the embed is yellow.

**Full Signature:**

```py
@commands.Cog.listener()
async def on_guild_channel_update(self, before, after):
```

**Limitation:**

- Changes in channel's position will not be logged by MichaelBot due to both spamming potential and messy Discord internal channel's position definition.

## on\_guild\_update

An event that is invoked when the guild itself is edited.

The edit can be either guild's name, guild's avatar or guild's owner.

This event falls under `update` in `AuditLogActionCategory`. The color of the embed is yellow.

**Full Signature:**

```py
@commands.Cog.listener()
async def on_guild_update(self, before, after):
```

**Limitation:**

- Does not log changes in guild's avatar yet.

## on\_guild\_role\_create

An event that is invoked when a role is created.

This event falls under `create` in `AuditLogActionCategory`. The color of the embed is green.

**Full Signature:**

```py
@commands.Cog.listener()
async def on_guild_role_create(self, role):
```

**Limitation:**

- Information may be logged incorrectly if the role is created by a bot.

## on\_guild\_role\_delete

An event that is invoked when a role is deleted.

This event falls under `delete` in `AuditLogActionCategory`. The color of the embed is orange.

**Full Signature:**

```py
@commands.Cog.listener()
async def on_guild_role_delete(self, role):
```

**Limitation:**

- Requires `View Audit Log` permission.

## on\_guild\_role\_update

An event that is invoked when a role is edited.

The edit can be either role's name changes, role's color changes, role is mentionable changes, role display separately changes or role's permission changes.

This event falls under `update` in `AuditLogActionCategory`. The color of the embed is yellow.

**Full Signature:**

```py
@commands.Cog.listener()
async def on_guild_role_update(self, before, after):
```

**Limitation:**

- Changes in mentionable and displaying separately for role will not be logged by MichaelBot due to unnecessary logging.

## command_error

A listener that listen to `on_command_error` and display the error to the logging channel.

**Full Signature:**

```py
@commands.Cog.listener("on_command_error")
async def command_error(self, ctx, error):
```

**Limitation:**

- Not user-friendly error message (can't change).
- If the original message has codeblock, the embed will display ugly.

*This document is last updated on April 23rd (PT) by MikeJollie#1067*
