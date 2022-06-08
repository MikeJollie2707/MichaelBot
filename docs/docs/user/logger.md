# Logs Category

Logging commands.

## `log-set`

Set a channel as a log channel.

Type: `Prefix Command`

Additional Info:

- This command doesn't do anything. Please use the subcommands.

### `log-set all [channel = None]`

Set a channel to dump all the logs. This automatically enables logging system.

Type: `Prefix Command`, `Slash Command`

Parameters:

- `channel`: The Discord channel to dump all the logs. Default to current channel.

Additional Info:

- Author needs to have `Manage Server`.

### `log-set option <logging_option>`

Enable a logging option.

Type: `Prefix Command`, `Slash Command` (recommended)

Parameters:

- `logging_option`: Log type to turn on. Check `log-view` to see all options.

Additional Info:

- Author needs to have `Manage Server`.
- It is recommended to use the `Slash Command` version of the command.

### `log-disable`

Disable logging or part of the logging system.

Type: `Prefix Command`

Additional Info:

- This command doesn't do anything. Please use the subcommands.

### `log-disable all`

Disable logging system.

Type: `Prefix Command`, `Slash Command`

### `log-disable option <logging_option>`

Disable a logging option.

Type: `Prefix Command`, `Slash Command` (recommended)

Parameters:

- `logging_option`: Log type to turn off. Check `log-view` to see all options.

Additional Info:

- Author needs to have `Manage Server`.
- It is recommended to use the `Slash Command` version of the command.

### `log-view`

View all log settings.

Type: `Prefix Command`, `Slash Command`

Additional Info:

- Author needs to have `Manage Server`.

*Last updated on Apr 1, 2022*
