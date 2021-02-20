<!-- omit in toc -->
# Logging events

Unlike other categories, this categories only contains logging events for the logging feature of a Discord Bot.

**This category has no commands.** If you're looking for setting up a logging channel/welcome channel/..., refers to page [`Settings`](server.md).

*This section will be reformatted in near future.*

<!-- omit in toc -->
## Table of Contents

- [Format [INTERNAL]](#format-internal)
- [LogContent [INTERNAL]](#logcontent-internal)
    - [\_\_init\_\_ [INTERNAL]](#__init__-internal)
    - [append [INTERNAL]](#append-internal)
- [\_\_init\_\_ [INTERNAL]](#__init__-internal-1)
- [log_check [INTERNAL]](#log_check-internal)
- [Events](#events)
    - [_message\_delete](#_message_delete)
    - [_bulk\_message\_delete [DEVELOPING]](#_bulk_message_delete-developing)
    - [_raw\_message\_edit](#_raw_message_edit)
    - [_message\_edit](#_message_edit)
    - [_member\_ban](#_member_ban)
    - [_member\_unban](#_member_unban)
    - [_member\_join](#_member_join)
    - [_member\_leave](#_member_leave)
    - [_member\_update](#_member_update)
    - [_guild\_channel\_create](#_guild_channel_create)
    - [_guild\_channel\_delete](#_guild_channel_delete)
    - [_guild\_channel\_update](#_guild_channel_update)
    - [_guild\_update](#_guild_update)
    - [_guild\_role\_create](#_guild_role_create)
    - [_guild\_role\_delete](#_guild_role_delete)
    - [_guild\_role\_update](#_guild_role_update)
    - [command_error](#command_error)

## Format [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

This is a set of format that the developers must follow while writing events for consistency. Any changes that does not follow this specification will be denied.

**Full Specification:**

```py
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
```

## LogContent [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A utility class to help removing the troublesome tabs on mobile.

### \_\_init\_\_ [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

The constructor. This also optionally set a base `content`.

**Full Signature:**

```py
def __init__(self, msg = ""):
```

### append [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

Append the `content` to the current content of this class. By default, this method will add a newline at the end of `content`. This method returns `self` to allow chaining.

```py
def append(self, *contents):
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
async def log_check(self, guild):
```

**Return:**

- `True` if `config["ERROR"] == 0` and `config["enable_log"] == True` and `config["log_channel"] != 0`
- `False` otherwise.

## Events

### _message\_delete

An event that is invoked when a message is deleted **if the message is in cache**. 

- If the message isn't in cache, `_raw_message_delete` is invoked instead.
- If it is a purge, then [`_bulk_message_delete`](#_bulk_message_delete-developing) is invoked instead.
- If the content of this log exceeds 2000 characters, the content will be put in `hastebin.com` instead.

This event falls under `delete` in `AuditLogActionCategory`. The color of the embed is orange.

**Full Signature:**

```py
@commands.Cog.listener("on_message_delete")
async def _message_delete(self, message):
```

**Limitation:**

- The deletor does not always display correctly (due to Discord limitation).

### _bulk\_message\_delete [DEVELOPING]

*This section is labeled as [DEVELOPING], which means the function/command is currently under development and not available for testing.*

### _raw\_message\_edit

An event that is invoked when a message is edited **even if the message isn't in cache**.

- If the message is in cache, the event will do nothing and leave the task to [`_message_edit`](#_message_edit).

This event falls under `update` in `AuditLogActionCategory`. The color of the embed is yellow.

**Full Signature:**

```py
@commands.Cog.listener("on_raw_message_edit")
async def _raw_message_edit(self, payload):
```

**Limitation:**

- The old content of the message cannot be found.
- There is a rare chance that the new content of the message cannot be found.

### _message\_edit

An event that is invoked when a message is edited **if the message is in cache**.

- If the message isn't in cache, [`_raw_message_edit`](#_raw_message_edit) is invoked instead.
- If the logging content exceeds 2000 characters, the content will be put in `hastebin.com` instead.

This event falls under `update` in `AuditLogActionCategory`. The color of the embed is yellow.

**Full Signature:**

```py
@commands.Cog.listener("on_message_edit")
async def _message_edit(self, before, after):
```

**Limitation:**

- `None`.

### _member\_ban

An event that is invoked when a user/member is banned.

- The ban action will also invoke [`_member_leave`](#_member_leave) if the member is in the guild.

The color of the embed is black.

**Full Signature:**

```py
@commands.Cog.listener("on_member_ban")
async def _member_ban(self, guild, user):
```

**Limitation:**

- `None`

### _member\_unban

An event that is invoked when a user is unbanned.

The color of the embed is black.

**Full Signature:**

```py
@commands.Cog.listener()
async def on_member_unban(self, guild, user):
```

**Limitation:**

- `None`

### _member\_join

An event that is invoked when a user join the guild.

The color of the embed is blue.

**Full Signature:**

```py
@commands.Cog.listener("on_member_join")
async def _member_join(self, member):
```

**Limitation:**

- `None`

### _member\_leave

An event that is invoked when a member leave the guild.

- This event is also invoked when a member is banned/kicked.

The color of the embed is blue.

**Full Signature:**

```py
@commands.Cog.listener("on_member_leave")
async def _member_remove(self, member):
```

**Limitation:**

- When a kicked member rejoin and leave, the member will be logged that the member is kicked twice.

### _member\_update

An event that is invoked when a member's role changes, a member's status/activity changes, a member's nickname changes or a member is muted/deafened.

This event falls under `update` in `AuditLogActionCategory`. The color of the embed is yellow.

**Full Signature:**

```py
@commands.Cog.listener("on_member_update")
async def _member_update(self, before, after):
```

**Limitation:**

- Changes in member's status/activity will not be logged by MichaelBot due to unnecessary spamming.
- Changes in member is muted/deafened is currently not be logged by MichaelBot due to the unnecessary logging.

### _guild\_channel\_create

An event that is invoked when a channel in a guild is created.

This event falls under `create` in `AuditLogActionCategory`. The color of the embed is green.

**Full Signature:**

```py
@commands.Cog.listener("on_guild_channel_create")
async def _guild_channel_create(self, channel):
```

**Limitation:**

- Does not display bitrate information in `VoiceChannel`.

### _guild\_channel\_delete

An event that is invoked when a channel in a guild is deleted.

This event falls under `delete` in `AuditLogActionCategory`. The color of the embed is orange.

**Full Signature:**

```py
@commands.Cog.listener("on_guild_channel_delete")
async def _guild_channel_delete(self, channel):
```

**Limitation:**

- Does not display bitrate information in `VoiceChannel`.

### _guild\_channel\_update

An event that is invoked when a channel in a guild is edited.

The edit can be either channel's name, channel's topic, channel's position or channel's permission.

This event falls under `update` in `AuditLogActionCategory`. The color of the embed is yellow.

**Full Signature:**

```py
@commands.Cog.listener("on_guild_channel_update")
async def _guild_channel_update(self, before, after):
```

**Limitation:**

- Changes in channel's position will not be logged by MichaelBot due to both spamming potential and messy Discord internal channel's position definition.

### _guild\_update

An event that is invoked when the guild itself is edited.

The edit can be either guild's name, guild's avatar or guild's owner.

This event falls under `update` in `AuditLogActionCategory`. The color of the embed is yellow.

**Full Signature:**

```py
@commands.Cog.listener("on_guild_update")
async def _guild_update(self, before, after):
```

**Limitation:**

- Does not log changes in guild's avatar yet.

### _guild\_role\_create

An event that is invoked when a role is created.

This event falls under `create` in `AuditLogActionCategory`. The color of the embed is green.

**Full Signature:**

```py
@commands.Cog.listener("on_guild_role_create")
async def _guild_role_create(self, role):
```

**Limitation:**

- `None`.

### _guild\_role\_delete

An event that is invoked when a role is deleted.

This event falls under `delete` in `AuditLogActionCategory`. The color of the embed is orange.

**Full Signature:**

```py
@commands.Cog.listener("on_guild_role_delete")
async def _guild_role_delete(self, role):
```

**Limitation:**

- Requires `View Audit Log` permission.

### _guild\_role\_update

An event that is invoked when a role is edited.

The edit can be either role's name changes, role's color changes, role is mentionable changes, role display separately changes or role's permission changes.

This event falls under `update` in `AuditLogActionCategory`. The color of the embed is yellow.

**Full Signature:**

```py
@commands.Cog.listener("on_guild_role_update")
async def _guild_role_update(self, before, after):
```

**Limitation:**

- Changes in mentionable and displaying separately for role will not be logged by MichaelBot due to unnecessary logging.

### command_error

A listener that listen to `on_command_error` and display the error to the logging channel.

**Full Signature:**

```py
@commands.Cog.listener("on_command_error")
async def command_error(self, ctx, error):
```

**Limitation:**

- Not user-friendly error message (can't change).
- If the original message has codeblock, the embed will display ugly.

*This document is last updated on Feb 19th (PT) by MikeJollie#1067*
