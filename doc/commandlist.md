# Command List

This is the help for almost every commands in MichaelBotPy bot.

This document will tries to be detailed and easy-to-understand, but it's better to use `help`.

If you want to invite the bot, you won't be able to, yet. You can however, ask MikeJollie#1067 to invite the bot via MichaelBotPy support server: <https://discord.gg/jeMeyNw>

## Conventions

These are the conventions used throughout this document:

### Parameters

- `<parameter>`: Required parameter. Without this parameter, the bot will raise error.
- `[parameter]`: Optional parameter. The bot can still works without this parameter.
- `<param1/param2/...>` or `[param1/param2/...]`: You can provide either param style. The accuracy is in descending order.
  - Example: if it's `profile [mention/ID/name/nickname]`, means you can, optionally, provide either the mention, the id or the name/nickname of the user. Using mention or id will provide more accuracy than name/nickname.

### Permissions

- `You need`: The required permission you need to have to execute the command.
- `I need`: The required permission the bot need to have to execute the command.

### Prefix

- This document will assume you know how to provoke a command ~~using `<prefix><command_name>`~~. If you don't know the prefix of the bot, use `@MichaelBotPy prefix` or use the bot's mention as the prefix (not recommended).
  - The default prefix is `$` ~~no it doesn't have $sudo~~.
- This document will asssume the bot has `Send Messages` and `Read Messages` in the channel you provoke the command.

## Core commands

1. `info`: Provide information about the bot.
  - Syntax: `info`
  - Example: `info`
  - Expected Output: *An embed contains information*
