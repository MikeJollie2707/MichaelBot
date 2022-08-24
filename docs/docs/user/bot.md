# Bot Category

Bot-related Commands

## `changelog [option = stable]`

Show 10 latest stable changes to the bot.

Type: `Prefix Command`, `Slash Command`

Cooldown: 5 seconds after 1 use per user.

Parameters:

- `option`: Additional options. Valid options are `dev`/`development` and `stable`.

Additional Info:

- Bot needs to have `Manage Messages` permission if used as a Prefix Command.

## `help [*name = None]`

Get help information for the bot.

Type: `Prefix Command`, `Slash Command`

Aliases: `h`

Parameters:

- `name`: Category name or command name. Is case-sensitive.

## `info`

Show information about the bot.

Type: `Prefix Command`, `Slash Command`

Aliases: `about`

### `info bot`

Show information about the bot.

Type: `Prefix Command`, `Slash Command`

### `info host`

Show information about the machine hosting the bot.

Type: `Prefix Command`, `Slash Command`

### `info item`

Show information for an item.

Type: `Prefix Command`, `Slash Command`

Additional Note:

- Refer to [this](../econ/start.md) to have context on this command.

### `info member [member]`

Show information about yourself or another member.

Type: `Prefix Command`, `Slash Command`

Parameters:

- `member`: A Discord member. Default to yourself.

### `info role <role>`

Show information about a role.

Type: `Prefix Command`, `Slash Command`

Parameters:

- `role`: A Discord role.

### `info server`

Show information about this server.

Type: `Prefix Command`, `Slash Command`

## `ping`

Check the bot if it's alive.

Type: `Prefix Command`, `Slash Command`

## `prefix [new_prefix = None]`

View or edit the bot prefix for the guild. This only affects Prefix Commands.

Type: `Prefix Command`, `Slash Command`

Cooldown: 5 seconds after 1 use per guild.

Parameters:

- `new_prefix`: The new prefix. Should not be longer than 5 characters or contain spaces.

Additional Info:

- Author needs to have `Manage Server` permission.

## `report <type> <*reason>`

Report a bug or suggest a feature for the bot. Please be constructive.

Type: `Prefix Command`, `Slash Command` (recommended).

Cooldown: 5 seconds after 1 use per user.

Parameters:

- `type`: The type of report you're making. Either `bug` or `suggest`.
- `reason`: The content you're trying to send.

*Last updated on Jul 25, 2022*
