<!-- omit in toc -->
# Moderation commands

These are commands that performs moderating action.

## \_\_init\_\_ [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A constructor of this category. This set the `Moderation` category's emoji as `🔨`.

## ban

Ban a member out of the server.

Note that the bot's role needs to be higher than the member to ban.

**Full Signature:**

```py
@commands.command()
@commands.has_guild_permissions(ban_members = True)
@commands.bot_has_permissions(send_messages = True)
@commands.bot_has_guild_permissions(ban_members = True)
@commands.cooldown(rate = 2, per = 5.0, type = commands.BucketType.guild)
async def ban(self, ctx, user : discord.Member, *, reason = None):
```

**Simplified Signature:**

```
ban <member> [reason]
```

**Parameters:**

- `member`: A Discord member. It can be any in the following form: `[ID/discriminator/mention/name/nickname]`
- `reason`: The reason for banning.

**Example:** `$ban MikeJollie Look at too many lolis`

**Expected Output:** *an embed with verification*

### ban_eh [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

An local error handler for the `ban` command.

It is currently only response to the `BadArgument` exception, which signify the user is not in the guild cache.

## hackban

Ban a user out of the server.

This user does not need to share the server with the bot.

**Full Signature:**

```py
@commands.command()
@commands.has_guild_permissions(ban_members = True)
@commands.bot_has_permissions(send_messages = True)
@commands.bot_has_guild_permissions(ban_members = True)
@commands.cooldown(rate = 2, per = 5.0, type = commands.BucketType.guild)
async def hackban(self, ctx, id : int, *, reason = None):
```

**Simplified Signature:**

```
hackban <ID> [reason]
```

**Parameters:**

- `id`: The id of the user.
- `reason`: The reason for banning.

**Example:** `$hackban 472832990012243969 Befriend with too many lolis`

**Expected Output:** *an embed with verification*

## kick

Kick a member out of the server.

Note that the bot's role needs to be higher than the member to kick.

**Full Signature:**

```py
@commands.command()
@commands.has_guild_permissions(kick_members = True)
@commands.bot_has_permissions(send_messages = True)
@commands.bot_has_guild_permissions(kick_members = True)
@commands.cooldown(rate = 2, per = 5.0, type = commands.BucketType.guild)
async def kick(self, ctx, member : discord.Member, *, reason = None):
```

**Simplified Signature:**

```
kick <member> [reason]
```

**Parameters:**

- `member`: A Discord member. It can be any in the following form: `[ID/discriminator/mention/name/nickname]`
- `reason`: The reason for kicking.

**Example:** `$kick MikeJollie Being dumb`

**Expected Output:** *an embed with verification*

### kick_eh [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A local error handler for the `kick` command.

It is currently only response to the `BadArgument` exception, which signify that the member is not in the guild.

## mute [INCOMPLETE] [DEVELOPING]

*This section is labeled as [INCOMPLETE], will be updated in the future.*

*This section is labeled as [DEVELOPING], which means the function/command is currently under development and not available for testing.*

Mute a member from chatting.

**Full Signature:**

```py
@commands.command(hidden = True, enabled = True)
@commands.has_permissions(kick_members = True)
@commands.bot_has_guild_permissions(kick_members = True)
@commands.cooldown(1, 5.0, commands.BucketType.guild)
async def mute(self, ctx, member : discord.Member, *, reason = None):
```

**Simplified Signature:**

```
mute <member> [reason]
```

**Parameters:**

- `member`: A Discord member. It can be any in the following form: `[ID/discriminator/mention/name/nickname]`
- `reason`: The reason for muting.

**Example:** `$mute MikeJollie Stop saying "Loli is justice"`

**Expected Output:** *an embed with verification*

## unban

Unban a user from the server.

This user does not need to share the server with the bot.

**Full Signature:**

```py
@commands.command()
@commands.has_guild_permissions(ban_members = True)
@commands.bot_has_permissions(send_messages = True)
@commands.bot_has_guild_permissions(ban_members = True)
@commands.cooldown(rate = 2, per = 5.0, type = commands.BucketType.guild)
async def unban(self, ctx, id : int, *, reason = None):
```

**Simplified Signature:**

```
unban <ID> [reason]
```

**Parameters:**

- `id`: The id of the user.
- `reason`: The reason for banning.

**Example:** `$unban 472832990012243969 You've been trained by the FBI now`

**Expected Output:** *an embed with verification*

*This document is last updated on May 26th (PT) by MikeJollie#1067*
