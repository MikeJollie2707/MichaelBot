# Command List

## Table of Content

- [Introduction](#introduction)
- [Conventions](#conventions)
  - [Parameters](#conventions-param)
  - [Permissions](#convetions-permit)
  - [Prefix](#convetions-prefix)
  - [User/Member](#conventions-user/member)
  - [Cooldown](#conventions-cooldown)
- [Core commands](#core)
  - [`info`](#info)

## Introduction <a id = "introduction"></a>

This is the help for almost every commands in MichaelBotPy bot.

This document will tries to be detailed and easy-to-understand (consider it as a bigger `help`).

If you want to invite the bot, you won't be able to, yet. You can however, ask MikeJollie#1067 to invite the bot via MichaelBotPy support server: <https://discord.gg/jeMeyNw>

## Conventions <a id = "conventions"></a>

These are the conventions used throughout this document:

<a id = "conventions-param"></a>

### Parameters

- `<parameter>`: Required parameter. The bot will **raise error without this parameter**.
- `[parameter]`: Optional parameter. The bot can **still works without this parameter**.
- `<param1/param2/...>` or `[param1/param2/...]`: You can provide **either** param style. **The accuracy is in descending order**.
  - Example: if it's `profile [mention/ID/name/nickname]`, means you can, optionally, provide **either the mention, the id or the name/nickname** of the user. Using `mention` or `id` will provide **more accuracy** than `name/nickname`.
- If the parameter has space, use `"this is considered a param"` to make it a param.
  - Example: if it's `profile [mention/ID/name/nickname]` and the `name` is `Hello World` then you will use `profile "Hello World"`. Using `profile Hello World` will most likely **raise error**.

<a id = "conventions-permit"></a>

### Permissions

- `You need`: The required permission **you** need to have to execute the command.
- `I need`: The required permission **the bot** need to have to execute the command.
- This document will asssume the bot has `Send Messages` and `Read Messages` in the channel you provoke the command.

<a id = "conventions-prefix"></a>

### Prefix

- This document will assume you know **how to provoke a command** ~~using `<prefix><command_name>`~~. If you don't know the prefix of the bot, use `@MichaelBotPy prefix` or use the bot's mention as the prefix (not recommended).
  - The default prefix is `$` ~~no it doesn't have $sudo~~.

<a id = "conventions-user/member"></a>

### User/Member

- When this document refers to **"user"**, it refers to a **Discord user regardless of the server**.
- When this document refers to **"member"**, it refers to a **Discord user in a certain server(s)**.
- The difference will be clarified later on in this document.

<a id = "conventions-cooldown"></a>

### Cooldown

- The convention for cooldown syntax in this doc (and `help`) is `x seconds per n use(s) (cooldown type)`.
  - `x`: The cooldown **duration** before you can use the command.
  - `n`: The number of **times** the command is used before invoking the cooldown.
  - `cooldown type`: There are usually 4 types of cooldown in this bot:
    - `global`: The cooldown applies to **every servers** the bot joins.
      - Example: If a person invokes `prefix` n times, **no one** can invoke `prefix` again until x seconds are passed.
    - `guild`: The cooldown applies to **everyone in a certain server**.
      - Example: If a person invokes `kick` n times, **no one in that person's server** can invoke `kick` again until x seconds are passed.
    - `user`: The cooldown applies to that **certain user**.
      - Example: If the user `MikeJollie` invoke `embed_simple` n times, **that certain user** can not invoke `embed_simple` again until x seconds are passed.
    - `member`: The cooldown applies to that **certain member**.
      - Example: If the member `MikeJollie` invoke `test` n times, **that certain member** can not invoke `MikeJollie` **in the same server he invoked** again until x seconds are passed. **He can invoke the command in a different server in that duration however**.

<a id = "core"></a>

## Core commands

<a id = "info"></a>

1. `info`: Provide information about the bot.

- **Syntax:** `info`
- **Example:** `info`
- **Expected Output:** *An embed contains information*

2. `profile`: Provide information about yourself or another member.

- **Syntax:** `profile [discrim/ID/mention/name/nickname]`
- **Example:**
  - **Example 1:** `profile @MikeJollie` (not preferred because people can get annoyed)
  - **Example 2:** `profile 472832990012243969` (most recommend if you have Developer Mode)
  - **Example 3:** `profile MikeJollie` (preferred, although not too accurate)
  - **Example 4:** `profile MJ` (same as Example 3)
  - **Example 5:** `profile MikeJollie#1067` (most preferred)
- **Expected Output:** *An embed contains information*

3. `serverinfo`: Provide information about the current server.

- **Alias:** `server-info`
- **Syntax:** `serverinfo` or `server-info`
- **Example:** `serverinfo`
- **Expected Output:** *An embed contains information*

4. `prefix`: View and set the prefix for the bot. `Unstable`.

- **Syntax:** `prefix [new prefix]`
- **Cooldown:** `5 seconds per 1 use (global)`
- **Example:**
  - **Example 1:** `prefix`
  - **Example 2:** `prefix /invoke`
- **Expected Output:**
  - **Example 1:** `Current prefix: <current prefix>`
  - **Example 2:** `New prefix: /invoke`
- **You need:** `Manage Server`

5. `note`: Provide syntax convention for `help` and `help-all`. You most likely should read [Conventions](#conventions) if that's why you're reading this.

- **Syntax:** `note`
- **Example:** `note`
- **Expected Output:** *Undefined*


