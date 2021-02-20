<!-- omit in toc -->
# Settings commands

These are commands that focus in providing Quality of Life for the guild. It comes with logging, welcoming, bad words filtering (new), goodbye (new), reaction roles (new), enabling/disabling a command (new).

<!-- omit in toc -->
## Table of Contents

- [\_\_init\_\_ [INTERNAL]](#__init__-internal)
- [log_enable](#log_enable)
- [log_setup](#log_setup)
- [log_disable](#log_disable)
- [welcome_enable](#welcome_enable)
- [welcome_setup](#welcome_setup)
- [welcome_new_member [INTERNAL]](#welcome_new_member-internal)
- [welcome_disable](#welcome_disable)

## \_\_init\_\_ [INTERNAL]

*This section is labeled as [INTERNAL], meaning that is is **NOT** a command. It is here only to serve the developers purpose.*

A constructor of the category. This set the `Core` category's emoji as `🛠`.

## log_enable

Enable logging in your server.

**Aliases:** `log-enable`

**Usage:** `<prefix>log_enable`

**Cooldown:** 3 seconds per 1 use (guild)

**Example:** `$log_enable`

**You need:** `Manage Server`.

**The bot needs:** `View Audit Log`, `Read Message History`, `Send Messages`.

## log_setup

Set the logging channel or view which channel is one.

This implicitly call [`log_enable`](#log_enable) if you haven't.

**Aliases:** `log-setup`

**Usage:** `<prefix>log_setup <channel>`

**Parameters:**

- `channel`: The text channel you want the bot to send logs. By default, it's the current channel the command is invoked in.

**Cooldown:** 3 seconds per 1 use (guild)

**Examples:**

- **Example 1:** `$log_setup`
- **Example 2:** `$log_setup #mikejollie-is-gay-change-my-mind`

**You need:** `Manage Server`.

**The bot needs:** `View Audit Log`, `Read Message History`, `Send Messages`.

## log_disable

Disable logging in your server. This doesn't remove the logging channel.

**Usage:** `<prefix>log_disable`

**Cooldown:** 3 seconds per 1 use (guild)

**Example:** `$log_disable`

**You need:** `Manage Server`.

**The bot needs:** `Read Message History`, `Send Messages.`

## welcome_enable

Enable welcoming new members in your server.

**Usage:** `<prefix>welcome_enable`

**Cooldown:** 3 seconds per 1 use (guild)

**Example:** `$welcome_enable`

**You need:** `Manage Server`.

**The bot needs:** `Read Message History`, `Send Messages`.

## welcome_setup

Set or view the welcome channel and message in your server.

This implicitly invoke [`welcome_enable`](#welcome_enable) if you haven't.

- If you don't provide a welcome text, it is default to `Hello [user.mention]! Welcome to **[guild.name]**! You're the [guild.count]th member in this server! Enjoy the fun!!! :tada:`. 

**Aliases:** `welcome-setup`

**Usage:** `<prefix>welcome_setup [channel] [welcome text]`

**Parameters:**

- `channel`: The channel you want the bot to send welcome message. By default, it is the current channel.
- `welcome text`: A welcome text. If provided, `channel` must also be provided. By default, the message is `Hello [user.mention]! Welcome to **[guild.name]**! You're the [guild.count]th member in this server! Enjoy the fun!!! :tada:`.
    - Possible arguments:
        - `[user.mention]`: Mention the new user.
        - `[user.name]`: Display the name of the user.
        - `[guild.name]`: Display the name of the guild.
        - `[guild.count]`: Display the current population of the guild.

**Cooldown:** 3 seconds per 1 use (guild)

**Examples:**

- **Example 1:** `$welcome-setup 644336991135072261 Welcome [user.mention] to [guild.name]!`
- **Example 2:** `$welcome-setup a-random-welcome-channel You are the [guild.count]th member!`
- **Example 3:** `$welcome-setup #another-random-channel`
- **Example 4:** `$welcome-setup`

**You need:** `Manage Server`.

**The bot needs:** `Read Message History`, `Send Messages`.

## welcome_new_member [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A listener to `on_member_join()` event that is responsible for sending the message to the welcome channel.

**Full signature:**

```py
@commands.Cog.listener("on_member_join")
async def welcome_new_member(self, member):
```

## welcome_disable

Disable welcoming in your server. This doesn't remove the welcome channel.

**Aliases:** `welcome-disable`

**Usage:** `<prefix>welcome_disable`

**Example:** `$welcome_disable`

**You need:** `Manage Server`.

**The bot needs:** `Read Message History`, `Send Messages`.

*This document is last updated on Feb 20th 2021 by MikeJollie#1067*
