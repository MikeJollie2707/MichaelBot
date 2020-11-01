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

## Introduction

This is the official documentation for MichaelBot. This can be used as a developer documentation or user documentation.

If you want to invite the bot, you won't be able to, yet. You can however, ask `MikeJollie#1067` to invite the bot via [MichaelBot support server](https://discord.gg/jeMeyNw).

The source of the bot is available publicly on [GitHub](https://github.com/MikeJollie2707/MichaelBot).

## Convention

The conventions in this document should be relatively straightforward. The conventions uses in `help` is a bit less clear, due to not having enough spaces.

These are the conventions I use in the help command:

### Parameters

These are the parameter types you will find in `help` and in `Simplified Signature` section later.

`<parameter>`: Required parameter. The bot will **raise error without this parameter**.

`[parameter]`: Optional parameter. The bot can **still works without this parameter**.

`<param1/param2/...>` or `[param1/param2/...]`: You can provide **either** param style.

If the parameter has space, use `"double quotes"` to make it a param.

- Example: if it's `profile [mention/ID/name/nickname]` and the `name` is `Hello World` then you will use `profile "Hello World"`.

`<member>` or `<user>` or `<channel>` or `<guild>`: Discord related argument. It is the equivalent of `<ID/discrimination/mention/name/nickname>`.

### Prefix

This document will assume you know **how to use a command** using `<prefix><command_name>`. If you don't know the prefix of the bot, use the bot's mention as the prefix (not recommended).

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

This document will assume the bot always has `Send Messages` and `Read Messages` in the channel you use the command.

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

*This document is last updated on Oct 31st (PT) by MikeJollie#1067*
