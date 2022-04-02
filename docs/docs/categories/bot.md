# Bot Category

Bot-related Commands

## `changelog`

Show 10 latest stable changes to the bot.

Type: `Prefix Command`

Cooldown: 5 seconds after 1 use per user.

### `changelog stable`

Show 10 latest stable changes to the bot. This exists for Slash Commands.

Type: `Prefix Command`, `Slash Command`

Cooldown: 5 seconds after 1 use per user.

### `changelog development`

Show 10 latest changes to the bot *behind the scene*.

Type: `Prefix Command`, `Slash Command`

Cooldown: 5 seconds after 1 use per user.

## `info`

Show information about the bot.

Type: `Prefix Command`, `Slash Command`

Aliases: `about`

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

*Last updated on Apr 1, 2022*
