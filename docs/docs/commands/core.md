<!-- omit in toc -->
# Core commands

<!-- omit in toc -->
## Table of Contents
- [\_\_init\_\_ [INTERNAL]](#__init__-internal)
- [cog_check [INTERNAL]](#cog_check-internal)
- [changelog](#changelog)
  - [changelog dev](#changelog-dev)
- [help](#help)
- [help-all](#help-all)
- [info](#info)
- [note](#note)
- [prefix [DEPRECATED]](#prefix-deprecated)
- [profile](#profile)
- [report](#report)
- [serverinfo](#serverinfo)

These are commands that are mostly related to information.

## \_\_init\_\_ [INTERNAL]

*This section is labeled as [INTERNAL], meaning that is is **NOT** a command. It is here only to serve the developers purpose.*

A constructor of the category. This set the `Core` category's emoji as `⚙️`.

## cog_check [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A check that apply to all the command in this category. This check will check if `ctx` is in private DM or not, and will raise `NoPrivateMessage()` exception if it is.

## changelog

Show the latest 10 changes of the bot.

**Usage:** `{prefix}changelog`

**Example:** `$changelog`

**You need:** None.

**The bot need:** `Read Message History`, `Add Reactions`, `Send Messages`.

***Subcommands:*** [dev](#changelog-dev)

### changelog dev

Show the latest 10 changes of the bot *behind the scene*.

**Usage:** `{prefix}changelog dev`

**Example:** `$changelog dev`

**You need:** None.

**The bot need:** `Read Message History`, `Add Reactions`, `Send Messages`.

## help

Show compact help about a command, or a category.

Note: command name and category name is case sensitive; `Core` is different from `core`.

**Usage:** `<prefix>help [command/category]`

**Parameters:**

- `command/category`: The category's name or the command's name or the command's aliases. This also includes subcommand.

**Examples:**

- **Example 1:** `$help Core`
- **Example 2:** `$help info`
- **Example 3:** `$help changelog dev`

**You need:** None.
**The bot need:** `Read Message History`, `Add Reactions`, `Send Messages`.

## help-all

Show help about the bot, a command, or a category.

Note: command name and category name is case sensitive; Core is different from core.

**Usage:** `<prefix>help-all [command/category]`

**Parameters:**

- `category/command`: The category's name or the command's name or the command's aliases.

**Examples:**

- **Example 1:** `$help-all Core`
- **Example 2:** `$help-all info`
- **Example 3:** `$help-all`

**You need:** None.

**The bot need:** `Read Message History`, `Add Reactions`, `Send Messages`.

## info

Provide information about the bot.

**Usage:** `<prefix>info`

**Example:** `$info`

**You need:** None.

**The bot need:** `Send Messages`.

## note [DEPRECATED]

*This section is labeled as [DEPRECATED], which means it's possible to be removed in the future.*

Provide syntax convention for `help` and `help-all`. All it does is putting a link to this documentation.

**Full Signature:**

```py
@commands.command()
@commands.bot_has_permissions(send_messages = True)
async def note(self, ctx):
```

**Simplified Signature:**

```
note
```

**Example:** `note`

**Expected Output:** *an embed with a link*

## prefix [DEPRECATED]

*This section is labeled as [DEPRECATED], which means it's possible to be removed in the future.*

View and set the prefix for the bot.

**Full Signature:**

```py
@commands.command()
@commands.has_guild_permissions(manage_guild = True)
@commands.bot_has_permissions(send_messages = True)
@commands.cooldown(rate = 1, per = 5.0, type = commands.BucketType.default)
async def prefix(self, ctx, new_prefix : str = None):
```

**Simplified Signature:**

```
prefix [new_prefix]
```

**Parameters:**

- `new_prefix`: The new prefix for the bot. I recommend to set it 1-4 characters with no spaces.

**Example:** `$prefix !`

**Expected Output:**

```py
New prefix: !
```

## profile

Provide information about you or another member.

**Usage:** `<prefix>profile [member]`

**Parameter:**

- `member`: A Discord member. It can be any in the following form: `[ID/discriminator/mention/name/nickname]`
  
**Examples:**

- **Example 1:** `$profile 472832990012243969` (recommended if you turn Developer Mode on)
- **Example 2:** `$profile MikeJollie#1067` (recommended for normal uses)
- **Example 3:** `$profile`

**You need:** None.

**The bot need:** `Send Messages`.

## report

Report a bug or suggest new features for the bot.

**Usage:** `<prefix>report <report_type> <content>`

**Parameters:**

- `report_type`: Either `report` or `suggest`, based on your need. It is recommended to use the correct label for the report/suggestion to be easily viewed.
- `content`: The report/suggestion.

**Cooldown:** 30 seconds per use (user)

**Examples:**

- **Example 1:** `$report report The command xyz raise error (full error here...)`
- **Example 2:** `$report suggest The command profile should have this feature (feature here...)`

**You need:** None.
**The bot need:** `Manage Messages`, `Send Messages`.

## serverinfo

Provide information about the server that invoke the command.

**Aliases:** `server-info`

**Usage:** `<prefix>serverinfo`

**Example:** `$serverinfo`

**You need:** None.

**The bot need:** `Send Messages`.

*This document is last updated on Oct 31st (PT) by MikeJollie#1067*