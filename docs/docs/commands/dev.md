<!-- omit in toc -->
# Dev commands

These are the commands that are only for the bot developers to use ~~to abuse power~~.

<!-- omit in toc -->
## Table of Contents

- [is_dev [INTERNAL]](#isdev-internal)
- [\_\_init\_\_ [INTERNAL]](#init-internal)
- [cog_check [INTERNAL]](#cogcheck-internal)
- [all_guild](#allguild)
- [leave_guild](#leaveguild)
- [reload](#reload)
- [report_response](#reportresponse)
- [reset\_all\_cooldown](#resetallcooldown)

## is_dev [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

This is a check to see if the invoker is a developer.

## \_\_init\_\_ [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A constructor of the category.

## cog_check [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A check that apply to all the command in this category. This check will check if `is_dev(ctx.author)` and `isDM(ctx.channel)`, raise `CheckFailure()` and `NoPrivateMessage()` respectively.

## all_guild

Display all guilds the bot is in.

**Full Signature:**

```py
@commands.command()
async def all_guild(self, ctx):
```

**Simplified Signature:**

```
all_guild
```

**Example:** `$all_guild`

**Expected Output:** *an embed with information*

## leave_guild

Make the bot leave the current invoked guild (so you can save yourself from clicking the kick button).

**Full Signature:**

```py
@commands.command()
@commands.is_owner()
async def leave_guild(self, ctx):
```

**Simplified Signature:**

```
leave_guild
```

**Example:** `$leave_guild`

**Expected Output:** *verification steps*

## reload

Reload a module. This is extremely useful when you don't want to shut down the bot, but still want the update to arrive.
Note that by reloading the module, the categories order in `help` will be changed.

**Full Signature:**

```py
@commands.command()
@commands.cooldown(1, 5.0, commands.BucketType.default)
async def reload(self, ctx, name):
```

**Simplified Signature:**

```
reload <module name>
```

**Example:** `$reload categories.dev`

**Expected Output:** `Reloaded extension categories.dev`

## report_response

Response to a report/suggestion. Note that the command will look through the last 100 messages in the report channel in the support server.

It is recommended not to use this more than once on the same report/suggestion.

**Full Signature:**

```py
@commands.command(aliases = ["suggest_response"])
@commands.cooldown(1, 60.0, commands.BucketType.default)
async def report_response(self, ctx, message_ID : int, *, response : str):
```

**Simplified Signature:**

```
report_response <messageID> <response>
suggest_response <messageID> <response>
```

**Parameters:**

- `messageID`: The message ID of the report.
- `response`: The response itself.

**Example:** `$report_response 649139994270892033 Nah`

**Expected Output:** *embed edited*

## reset\_all\_cooldown

Reset all cooldowns on every commands.

**Full Signature:**

```py
@commands.command()
async def reset_all_cooldown(self, ctx):
```

**Simplified Signature:**

```
reset_all_cooldown
```

**Example:** `$reset_all_cooldown`

**Expected Output:** `All cooldown reseted.`

*This document is last updated on April 23rd (PT) by MikeJollie#1067*