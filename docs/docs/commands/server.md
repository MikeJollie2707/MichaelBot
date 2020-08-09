# Settings commands [EXPERIMENT]

*This section is labeled as [EXPERIMENT], which means the function/command is currently in internal testing (alpha) and not publicly available.*

These are commands that focus in providing Quality of Life for the guild. It comes with logging, welcoming, bad words filtering (new), goodbye (new), reaction roles (new), enabling/disabling a command (new).

## \_\_init\_\_ [INTERNAL]

*This section is labeled as [INTERNAL], meaning that is is **NOT** a command. It is here only to serve the developers purpose.*

A constructor of the category. This set the `Core` category's emoji as `🛠`.

## log_enable

Enable logging in your server.

**Full Signature:**

```py
@commands.command(aliases = ["log-enable"])
@commands.has_guild_permissions(manage_guild = True)
@commands.bot_has_permissions(send_messages = True)
@commands.bot_has_guild_permissions(view_audit_log = True)
@commands.cooldown(rate = 1,  per = 3.0, type = commands.BucketType.guild)
async def log_enable(self, ctx):
```

**Simplified Signature:**

```
log_enable
log-enable
```

**Example:** `$log_enable`

**Expected Output:** *a confirm message*

## log_setup

Set the logging channel or view which channel is one.
This implicitly call `log_enable()` if you haven't.

**Full Signature:**

```py
@commands.command(aliases = ["log-setup"])
@commands.has_guild_permissions(manage_guild = True)
@commands.bot_has_permissions(send_messages = True)
@commands.bot_has_guild_permissions(view_audit_log = True)
@commands.cooldown(rate = 1,  per = 3.0, type = commands.BucketType.guild)
async def log_setup(self, ctx, log : discord.TextChannel = None):
```

**Simplified Signature:**

```
log_setup [channel]
log-setup [channel]
```

**Parameters:**

- `channel`: The text channel you want the bot to send logs. By default, it's the current channel the command is invoked in.

**Examples:**

- **Example 1:** `$log_setup`
- **Example 2:** `$log_setup #mikejollie-is-gay-change-my-mind`

**Expected Output:** *a verification embed at [channel]*

## log_disable

Disable logging in your server.

**Full Signature:**

```py
@commands.command(aliases = ["log-disable"])
@commands.has_guild_permissions(manage_guild = True)
@commands.bot_has_permissions(send_messages = True)
@commands.cooldown(rate = 1,  per = 3.0, type = commands.BucketType.guild)
async def log_disable(self, ctx):
```

**Simplified Signature:**

```
log_disable
log-disable
```

**Example:** `$log_disable`

**Expected Output:** *a confirm message*

*This document is last updated on Aug 8th 2020 by MikeJollie#1067*
