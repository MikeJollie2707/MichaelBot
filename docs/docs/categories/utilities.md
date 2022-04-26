# Utilities Category

Utility Commands.

## `profile [member = None]`

Information about yourself or another member.

Type: `Prefix Command`, `Slash Command`

Parameters:

- `member`: A Discord member. Default to you.

## `server-info`

Information about this server.

Type: `Prefix Command`, `Slash Command`

Aliases: `serverinfo`

## `role-info <role>`

Information about a role in this server.

Type: `Prefix Command`, `Slash Command`

Parameters:

- `role`: A Discord role.

Aliases: `roleinfo`

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

*Last updated on Apr 25, 2022*
