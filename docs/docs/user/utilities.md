# Utilities Category

Utility Commands.

## `base-convert <from_base> <to_base> <number>`

Convert a number to the desired base.

Type: `Prefix Command`, `Slash Command`

Parameters:

- `from_base`: The base the number you're converting. Valid options are `2`, `8`, `10`, and `16`.
- `to_base`: The base you want to convert to. Valid options are the same as `from_base`.
- `number`: The number you're converting.

## `calc <expression>`

Calculate a math expression.

Type: `Prefix Command`, `Slash Command`

Parameters:

- `expression`: The math expression.

Additional Info:

- Rounding errors, along with other debatable values such as `0^0` is incorrect due to language limitation.

## `embed`

Send an embed.

Additional Info:

- This command only works with subcommands.

### `embed from-json <raw_embed>`

Send an embed from a JSON object. Check out https://embedbuilder.nadekobot.me/ for easier time.

Type: `Prefix Command`, `Slash Command`

Cooldown: 3 seconds after 1 use per user.

Parameters:

- `raw_embed`: The embed in JSON format.

### `embed to-json <message_id> [channel]`

Take the embed from a message and convert it to a JSON object.

Type: `Prefix Command`, `Slash Command`

Cooldown: 3 seconds after 1 use per user.

Parameters:

- `message_id`: The message ID. The bot can't get a message that's too old.
- `channel`: The channel the message is in. Default to the current channel.

Additional Info:

- This is useful when you want to change slightly from an existing embed.

### `embed simple [title = None] [description = None] [color = green] [channel = None]`

Create and send a simple embed. Useful for quick embeds.

Type: `Slash Command`

Cooldown: 3 seconds after 1 use per user.

Parameters:

- `title`: The title of the embed.
- `description`: The description of the embed.
- `color`: Your choice of color. Default to green.
- `channel`: The channel to send this embed. Default to the current one.

Additional Info:

- This is an alternative to `embed interactive`.
- Either `title` or `description` must be non-empty.

### `embed interactive`

Create a simple embed with prompts.

Type: `Prefix Command`

Cooldown: 3 seconds after 1 use per user.

Additional Info:

- Bot needs to have `Manage Messages`.
- This is an alternative to `embed simple`.


### `embed interactive2`

Create a simple embed with visual prompts.

Type: `Prefix Command`

Cooldown: 3 seconds after 1 use per user.

Additional Info:

- Bot needs to have `Manage Messages`.
- This is an alternative to `embed simple`.

## `profile [member = None]`

Information about yourself or another member.

Type: `Prefix Command`, `Slash Command`

Parameters:

- `member`: A Discord member. Default to you.

## `remindme`

Create a reminder. Make sure your DM is open to the bot.

Type: `None`

Aliases: `rmd`, `notify`, `timer`

Additional Info:

- This command only works with subcommands.

### `remindme create <interval> <*message>`

Create a reminder. Make sure your DM is open to the bot.

Type: `Prefix Command`, `Slash Command`

Cooldown: 5 seconds after 1 use per user.

Parameters:

- `interval`: How long until the bot reminds you. Must be between 1 minute and 30 days. Example: `3d2m1s`
- `message`: The message the bot will send after the interval.

Additional Info:

- An interval of less than 120 seconds is considered to be a "short reminder".

### `remindme view`

View all your long reminders.

Type: `Prefix Command`, `Slash Command`

Cooldown: 5 seconds after 1 use per user.

Additional Info:

- Due to optimization, this command won't display short reminders.

### `remindme remove <remind_id>`

Remove a long reminder.

Type: `Prefix Command`, `Slash Command`

Cooldown: 5 seconds after 1 use per user.

Parameters:

- `remind_id`: The reminder's id. You can find it in `remindme view`.

Additional Info:

- Due to optimization, this command won't remove short reminders.

## `urban <*term>`

Search a term on urbandictionary.

Type: `Prefix Command`, `Slash Command`

Cooldown: 5 seconds after 1 use per user.

Parameters:

- `term`: The term to search. Example: `rickroll`.

## `weather <*city_name>`

Display weather information for a location.

Type: `Prefix Command`, `Slash Command`

Cooldown: 5 seconds after 1 use per user.

Parameters:

- `city_name`: The city to check. Example: `Paris`.

*Last updated on Jul 25, 2022*
