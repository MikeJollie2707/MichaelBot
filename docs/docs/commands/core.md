<!-- omit in toc -->
# Core commands

These are commands that are mostly related to information.

## \_\_init\_\_ [INTERNAL]

*This section is labeled as [INTERNAL], meaning that is is **NOT** a command. It is here only to serve the developers purpose.*

A constructor of the category. This set the `Core` category's emoji as `⚙️`.

## cog_check [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A check that apply to all the command in this category. This check will check if `ctx` is in private DM or not, and will raise `NoPrivateMessage()` exception if it is.

## changelog

Show the latest 10 changes of the bot.

**Full Signature:**

```py
@commands.command()
@commands.bot_has_permissions(read_message_history = True, add_reactions = True, send_messages = True)
async def changelog(self, ctx):
```

**Simplified Signature:**

```
changelog
```

**Example:** `$changelog`

**Expected Output:** *an embed with reactions to navigate*

## help

Show compact help about a command or a category. Note that the command name and category name is case sensitive.

**Full Signature:**

```py
@commands.command()
@commands.bot_has_permissions(read_message_history = True, add_reactions = True, send_messages = True)
async def help(self, ctx, categoryOrcommand = ""):
```

**Simplified Signature:**

```
help [category/command]
```

**Parameters:**

- `category/command`: The category's name or the command's name or the command's aliases.

**Examples:**

- **Example 1:** `$help Core`
- **Example 2:** `$help info`
- **Example 3:** `$help`

**Expected Output:**

- Example 1: *an embed with reactions to navigate*
- Example 2: *an embed with information*
- Example 3: *an embed with reactions to select*

## help-all

Show help about the bot, a command, or a category.

Note: command name and category name is case sensitive; Core is different from core.

**Full Signature:**

```py
# Doesn't exist
```

**Simplified Signature:**

```
help-all [category/command]
```

**Parameters:**

- `category/command`: The category's name or the command's name or the command's aliases.

**Examples:**

- **Example 1:** `$help-all Core`
- **Example 2:** `$help-all info`
- **Example 3:** `$help-all`

**Expected Output:**

- Example 1: *an embed with information*
- Example 2: *an embed with information*
- Example 3: *an embed with information*

## info

Provide information about the bot.

**Full Signature:**

```py
@commands.command(aliases = ["about"])
@commands.bot_has_permissions(send_messages = True)
async def info(self, ctx):
```

**Simplified Signature:**
```
info
```

**Example:** `$info`

**Expected Output:** *an embed with information*

## note

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

**Full Signature:**

```py
@commands.command()
@commands.bot_has_permissions(send_messages = True)
async def profile(self, ctx, member: discord.Member = None):
```

**Simplified Signature:**

```
profile [member]
```

**Parameter:**

- `member`: A Discord member. It can be any in the following form: `[ID/discriminator/mention/name/nickname]`
  
**Examples:**

- **Example 1:** `$profile 472832990012243969` (recommended if you turn Developer Mode)
- **Example 2:** `$profile MikeJollie#1067` (recommended for normal uses)
- **Example 3:** `$profile`

**Expected Output:** *an embed with information*

## report

Report a bug or suggest new features for the bot.

**Full Signature:**

```py
@commands.command()
@commands.bot_has_permissions(manage_messages = True, send_messages = True)
@commands.cooldown(rate = 1, per = 30.0, type = commands.BucketType.user)
async def report(self, ctx, *, content : str):
```

**Simplified Signature:**

```
report <type> <content>
```

**Parameters:**

- `type`: Either `report` or `suggest`, based on your need. It is recommended to use the correct label for the report/suggestion to be easily viewed.
- `content`: The report/suggestion.

**Examples:**

- **Example 1:** `$report report The command xyz raise error (full error here...)`
- **Example 2:** `$report suggest The command profile should have this feature (feature here...)`

**Expected Output:**

```py
Your opinion has been sent.
```

## serverinfo

Provide information about the server that invoke the command.

**Full Signature:**

```py
@commands.command(aliases = ["server-info"])
@commands.bot_has_permissions(send_messages = True)
async def serverinfo(self, ctx):
```

**Simplified Signature:**

```
serverinfo
server-info
```

**Example:** `$serverinfo`

**Expected Output:** *an embed with information*

*This document is last updated on May 26th (PT) by MikeJollie#1067*