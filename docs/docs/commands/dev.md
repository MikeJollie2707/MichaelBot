<!-- omit in toc -->
# Dev commands

These are the commands that are only for the bot developers to use ~~to abuse power~~.

<!-- omit in toc -->
## Table of Contents

- [is_dev [INTERNAL]](#is_dev-internal)
- [\_\_init\_\_ [INTERNAL]](#__init__-internal)
- [cog_check [INTERNAL]](#cog_check-internal)
- [addmoney](#addmoney)
- [all_guild](#all_guild)
- [rmvmoney](#rmvmoney)
- [leave_guild](#leave_guild)
- [reload](#reload)
    - [reload_eh [INTERNAL]](#reload_eh-internal)
- [reload_all_extension](#reload_all_extension)
    - [reload_all_error [INTERNAL]](#reload_all_error-internal)
- [report_response](#report_response)
- [reset\_all\_cooldown](#reset_all_cooldown)
- [shutdown](#shutdown)

## is_dev [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

This is a check to see if the invoker is a developer. This applies to every single command in this category, plus any checks that the command might have.

## \_\_init\_\_ [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A constructor of the category.

## cog_check [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A check that apply to all the command in this category. This check will check if `is_dev(ctx.author)` and `isDM(ctx.channel)`, raising `CheckFailure()` and `NoPrivateMessage()` respectively.

## addmoney

Add an amount of money to a user.

**Usage:** `<prefix>addmoney <amount> <user>`

**Parameter:**

- `amount`: The amount of money you want to add.
- `user`: The user you want to add the money.

**Example:** `$addmoney 1000 MikeJollie`

**You need:** None.

**The bot need:** `Read Message History`, `Send Messages`.

## all_guild

Display all guilds the bot is in.

**Usage:** `<prefix>all_guild`

**Example:** `$all_guild`

**You need:** None.

**The bot needs:** `Read Message History`, `Send Messages`.

## rmvmoney

Remove an amount of money from the user.

**Usage:** `<prefix>rmvmoney <amount> <user>`

**Parameter:**

- `amount`: The amount of money you want to remove. If larger than the member's actual money, the money remain will be 0.
- `user`: The member you want to remove the money.

**Example:** `$rmvmoney 1000 MikeJollie`

**You need:** None.

**The bot need:** `Read Message History`, `Send Messages`.

## leave_guild

Make the bot leave the current invoked guild (so you can save yourself from clicking the kick button).

**Usage:** `<prefix>leave_guild`

**Example:** `$leave_guild`

**You need:** Owner of the guild.

**The bot needs:** `Read Message History`, `Send Messages`.

## reload

Reload a module. This is extremely useful when you don't want to shut down the bot, but still want the update to arrive.

Note that by reloading the module, the categories order in `help` will be changed.

**Usage:** `<prefix>reload <module>`

**Parameter:**

- `module`: The full module name.

**Cooldown:** 5 seconds per 1 use (global)

**Example:** `$reload categories.dev`

**You need:** None.

**The bot needs:** `Read Message History`, `Send Messages`.

### reload_eh [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A local error handler for the `reload` command.

It is currently only response to the `ModuleNotFound` exception.

## reload_all_extension

Reload all modules. Useful for OCD people (like MikeJollie) because `reload` will mess up the order in `help` and `help-all`.

**Usage:** `<prefix>reload_all_extension`

**Cooldown:** 5 seconds per 1 use (global)

**Example:** `$reload_all_extension`

**You need:** None.

**The bot needs:** `Read Message History`, `Send Messages`.

### reload_all_error [INTERNAL]

A local error handler for the `reload_all_extension` command.

It is currently doing nothing.

## report_response

Response to a report/suggestion. Note that the command will look through the last 100 messages in the report channel in the support server.

It is recommended not to use this more than once on the same report/suggestion.

**Aliases:** `suggest_response`

**Usage:** `<prefix>report_response <message ID> <response>`

**Parameters:**

- `message ID`: The message ID of the report.
- `response`: The response itself.

**Cooldown:** 60 seconds per 1 use (global)

**Example:** `$report_response 649139994270892033 Nah`

**You need:** None.

**The bot needs:** `Send Messages`.

## reset\_all\_cooldown

Reset all cooldowns on every commands.

**Usage:** `<prefix>reset_all_cooldown`

**Example:** `$reset_all_cooldown`

**You need:** None.

**The bot needs:** `Send Messages`.

## shutdown

A formal way to disconnect the bot from Discord.

**Usage:** `<prefix>shutdown`

**Example:** `$cooldown`

**You need:** None.

**The bot need:** `Send Messages`.

*This document is last updated on Feb 19th by MikeJollie#1067*
