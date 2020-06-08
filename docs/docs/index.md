<!-- omit in toc -->
# Welcome to MichaelBot's documentation

<!-- omit in toc -->
## Table of Contents

- [Introduction](#introduction)
- [Convention](#convention)
  - [Parameters](#parameters)
  - [Prefix](#prefix)
  - [User/Member Concept](#usermember-concept)
  - [Permissions](#permissions)
  - [Cooldown](#cooldown)
  - [Understanding command's signature](#understanding-commands-signature)

## Introduction

This is the official documentation for MichaelBot. This can be used as a developer documentation or user documentation.

If you want to invite the bot, you won't be able to, yet. You can however, ask `MikeJollie#1067` to invite the bot via [MichaelBot support server](https://discord.gg/jeMeyNw).

The source of the bot is available publicly on [GitHub](https://github.com/MikeJollie2707/MichaelBot).

## Convention

These are the conventions I use throughout this document:

### Parameters

These are the parameter types you will find in `help` and in `Simplified Signature` section later.

`<parameter>`: Required parameter. The bot will **raise error without this parameter**.

`[parameter]`: Optional parameter. The bot can **still works without this parameter**.

`<param1/param2/...>` or `[param1/param2/...]`: You can provide **either** param style. **The accuracy is in descending order**.

- Example: if it's `profile [mention/ID/name/nickname]`, means you can, optionally, provide **either the mention, the id or the name/nickname** of the user. Using `mention` or `id` will provide **more accuracy** than `name/nickname`.

If the parameter has space, use `"double quotes"` to make it a param.

- Example: if it's `profile [mention/ID/name/nickname]` and the `name` is `Hello World` then you will use `profile "Hello World"`. Using `profile Hello World` will most likely **raise error**.

### Prefix

This document will assume you know **how to provoke a command** using `<prefix><command_name>`. If you don't know the prefix of the bot, use the bot's mention as the prefix (not recommended).

- The default prefix is `$` but no it doesn't have $sudo.

### User/Member Concept

User/Member are usually confused terms for a Discord user, but here are the difference.

- When this document refers to **"user"**, it refers to a **Discord user regardless of the server**.
- When this document refers to **"member"**, it refers to a **Discord user in a certain server(s)**.

Note that Discord API doesn't allow bot to **get information about a user/member if the bot does not see the user/member**, which means the bot needs to share at least **1** server with the user/member to actually work.

### Permissions

The convention for permissions in `help` is as follow:

- `You need`: The required permission **you** need to have to execute the command.
- `I need`: The required permission **the bot** need to have to execute the command.

This document will asssume the bot has `Send Messages` and `Read Messages` in the channel you provoke the command.

### Cooldown

The convention for cooldown syntax in `help` is `x seconds per n use(s) (cooldown type)`.

`x`: The cooldown **duration** before you can use the command.

`n`: The number of **times** the command is used before invoking the cooldown.

`cooldown type`: There are usually 4 types of cooldown in this bot:

- `global`: The cooldown applies to **every servers** the bot joins.
  - Example: If a person invokes `prefix` n times, **no one** can invoke `prefix` again until x seconds are passed.
- `guild`: The cooldown applies to **everyone in a certain server**.
  - Example: If a person invokes `kick` n times, **no one in that person's server** can invoke `kick` again until x seconds are passed.
- `user`: The cooldown applies to that **certain user**.
  - Example: If the user `MikeJollie` invoke `embed_simple` n times, **that certain user** can not invoke `embed_simple` again until x seconds are passed.
- `member`: The cooldown applies to that **certain member**.
  - Example: If the member `MikeJollie` invoke `test` n times, **that certain member** can not invoke `MikeJollie` **in the same server he invoked** again until x seconds are passed. **He can invoke the command in a different server in that duration however**.

### Understanding command's signature

If you're not a geek, you can refer to `help <command>` and read the sections above.

A typical command's signature is as follow:

```py
@commands.command(aliases = ["alias1", "alias2"])
@commands.has_permissions(manage_messages = True)
@commands.has_guild_permissions(...)
@commands.bot_has_permissions(...)
@commands.bot_has_guild_permissions(...)
@commands.cooldown(rate = 1, per = 3.0, type = commands.BucketType.default)
async def test(self, ctx, param1, param2 : discord.User, param3 : discord.User = None):
```

**The first line**'s significance is the `aliases = []`. It **tells that the command has the following alias(es)**, which can be used instead of using the command's name.

**The second line** means **the user who invoke the command must have a certain permission at the invoked channel to invoke the command**.

- In this example, the user must have `Manage Messages` permission in the channel to use the command.

**The third line** is similar to the second line, except **it consider the guild's permission**.

- For example, a member that is not allowed to add reactions to a certain channel can still invoke the command if the member's roles allowed.

**The fourth line** is the same as the second line except it **checks the bot's permission**.

**The fifth line** is the same as the third line except it **checks the bot's guild permission**.

**The sixth line defines the cooldown for the command**. `rate` means `x`, `per` means `n` and `type` means `cooldown type` in [cooldown](#cooldown).

- `default` is `global`.

The last line defines the command with the name `test`, that accept at max 3 parameters (ignore `self` and `ctx`).

- The first argument is `param1`, and it is required.
- The second argument is `param2`, and it is required. However, the bot will intepret `param2` as if it is a [User](#usermember-concept), and so the parameter will accept `<ID/discriminator/mention/name/nickname>`. If the bot fails to convert to a User, it'll raise error.
- The third argument is `param3`, and it is optional. It'll do the same thing as `param2`, but if it doesn't presence, the bot will ignore it.
- `test hey MikeJollie` is valid, `test` is invalid, `test hey MikeJollie Stranger.com` is valid, `test hey` is invalid.

*This document is last updated on May 26th (PT) by MikeJollie#1067*
