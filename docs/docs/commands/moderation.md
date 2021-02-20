<!-- omit in toc -->
# Moderation commands

<!-- omit in toc -->
## Table of Contents

- [\_\_init\_\_ [INTERNAL]](#__init__-internal)
- [ban](#ban)
    - [ban_eh [INTERNAL]](#ban_eh-internal)
- [hackban](#hackban)
- [kick](#kick)
    - [kick_eh [INTERNAL]](#kick_eh-internal)
- [mute [INCOMPLETE] [DEVELOPING]](#mute-incomplete-developing)
- [unban](#unban)

These are commands that performs moderating action.

## \_\_init\_\_ [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A constructor of this category. This set the `Moderation` category's emoji as `🔨`.

## ban

Ban a member in the server.

Note that the bot's role needs to be higher than the member to ban.

**Usage:** `<prefix>ban <member> [reason]`

**Parameters:**

- `member`: A Discord member.
- `reason`: The reason for banning.

**Cooldown:** 5 seconds per 2 uses (guild).

**Example:** `$ban MikeJollie Audam-kun`

**You need:** `Ban Members`.

**The bot needs:** `Ban Members`, `Read Message History`, `Send Messages`.

### ban_eh [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A local error handler for the `ban` command.

It is currently only response to the `BadArgument` exception, which signify the user is not in the guild cache.

## hackban

Ban a user out of the server.

This user does not need to share the server with the bot.

**Usage:** `<prefix>hackban <id> [reason]`

**Parameters:**

- `id`: The id of the user.
- `reason`: The reason for banning.

**Cooldown:** 5 seconds per 2 uses (guild).

**Example:** `$hackban 472832990012243969 You have too many lolis`

**You need:** `Ban Members`.

**The bot needs:** `Ban Members`, `Read Message History`, `Send Messages`.

## kick

Kick a member out of the server.

Note that the bot's role needs to be higher than the member to kick.

**Usage:** `<prefix>kick <member> [reason]`

**Parameters:**

- `member`: A Discord member.
- `reason`: The reason for kicking.

**Cooldown:** 5 seconds per 2 uses (guild).

**Example:** `$kick MikeJollie Being dumb`

**You need:** `Kick Members`

**The bot needs:** `Kick Members`, `Read Message History`, `Send Messages`.

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

**Usage:** `<prefix>unban <id> [reason]`

**Parameters:**

- `id`: The id of the user.
- `reason`: The reason for unbanning.

**Cooldown:** 5 seconds per 2 uses (guild).

**Example:** `$unban 472832990012243969 You've been trained by the FBI now`

**You need:** `Ban Members`.

**The bot needs:** `Ban Members`, `Read Message History`, `Send Messages`.

*This document is last updated on Feb 19th (PT) by MikeJollie#1067*
