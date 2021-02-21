<!-- omit in toc -->
# Utility methods

These are functions that helps with several tasks.

<!-- omit in toc -->
## Table of Contents

## get_config

*This function is a coroutine.*

Return a guild's information as a `dict`. 

The resultant dictionary has a special key called `ERROR` which indicates whether or not the dictionary is good to use. `0` is good.

It is NOT recommended to add/remove any keys from this dictionary.

**Full signature:**

```py
async def get_config(bot, guild_id) -> dict:
```

**Parameters:**

- `bot`: A `commands.Bot` instance that has a `pool` attribute.
- `guild_id`: The guild's id.

## save_config

*This function is a coroutine.*

Save the configuration of the guild. This function is a temporary version of a `DB.Guild.bulk_update()` method.

**Full signature:**

```py
async def save_config(bot, config) -> None:
```

**Parameters:**

- `bot`: A `commands.Bot` instance that has a `pool` attribute.
- `config`: A dictionary. This dictionary should always be previously returned from [`get_config()`](#get_config).

## calculate

Calculate a simple mathematic expression and return the result as a `str`.

This is currently used only in the `calc` command.

**Full signature:**

```py
def calculate(expression : str) -> str:
```

**Parameter:**

- `expression`: The mathematic expression.

**Return:** The result of the expression.

- If a `ZeroDivisionError` is raised, it'll return `Infinity/Undefined`.
- If an `Exception` is raised, it'll return `Error`.

## convert_roleperms_dpy_discord

Convert a role permission string from `discord.py` to what it looks like in Discord.

**Full signature:**

```py
def convert_roleperms_dpy_discord(role_permissions : str) -> str:
```

**Parameter:**

- `role_permissions`: The role permission.

**Example:** `convert_roleperms_dpy_discord("create_instant_invite") -> "Create Invite"`

## convert_channelperms_dpy_discord

Convert a channel permission string from `discord.py` to what it looks like in Discord.

**Full signature:**

```py
def convert_channelperms_dpy_discord(channel_permissions : str) -> str:
```

**Parameter:**

- `channel_permissions`: The channel permission.

**Example:** `convert_channelperms_dpy_discord("external_emojis") -> "Use External Emojis"`

## clean_signature

Automatically convert a command's signature into a more friendly version to display in the `Usage` section of a help command.

The command's signature is obtained using the `signature` attribute.

Variables should be named carefully:

- `a_variable` will be `a variable`.
- `a__variable` will be `a/variable`.

**Full signature:**

```py
def clean_signature(command_signature : str) -> str:
```

## format_time

Convert a `datetime.timedelta` to a nice string. This only converts up to seconds. For possible milliseconds values, don't use this.

**Full signature:**

```py
def format_time(time : datetime.timedelta, options = {}) -> str:
```

**Parameters:**

- `time`: A `datetime.timedelta`.
- `options`: An optional `dict` to configure the string. Possible options are:
- `include_seconds`: Whether or not to include seconds in the string. Default to `False`.
- `include_zeroes`: Whether or not to include 0 parts in the string. Default to `True`.
    - With `False`, it'll return `7 minutes` instead of `0 days 0 hours 7 minutes 0 seconds`.

## get_default_embed

Generate a "default" embed with footer and the time.

Note that for logging, you should overwrite the footer to something else. It is default to `Requested by `

**Full signature:**

```py
def get_default_embed(title : str = "", url : str = "", description : str = "", color : discord.Color = discord.Color.green(), timestamp : datetime.datetime = datetime.datetime.utcnow(), author : discord.User = None) -> discord.Embed:
```

**Parameters:**

- `timestamp`: the timestamp, usually `utcnow()`. The default value is there just to make the parameters look good, you still have to provide it.
- `author`: optional `discord.User` or `discord.Member` to set to the footer. If not provided, it won't set the footer.
- `title`: optional title.
- `url`: optional url for the title.
- `description`: optional description. Internally it'll remove the tabs.
- `color`: optional color, default to green.

**Return type:** `discord.Embed` or `None` on failure.

## mention

A utility function that returns a mention string to be used.

The only reason this function exists is because `discord.Role.mention` being retarded when the role is `@everyone`.

In that case, the function will return directly `@everyone`, not `@@everyone`. Otherwise, the function just simply return `object.mention`.

Because of this, you can use the default `.mention` (recommended) unless it's a `discord.Role`.

Note that if there's a custom role that's literally named `@everyone` then this function will return `@everyone`, not `@@everyone`.

**Full signature:**

```py
def mention(discord_object : discord.Object) -> str:
```

**Parameter:**

- `discord_object`: A Discord Object that is mentionable, including `discord.abc.User`, `discord.abc.GuildChannel` and `discord.Role`.

**Return:** The string used to mention the object.

- If the parameter's type does not satisfy the above requirements, it returns empty string.

## striplist

Turn a list of objects into a string.

**Full signature:**

```py
def striplist(array : typing.Union[list, numpy.ndarray]) -> str:
```

**Parameter:**

- `array`: A list of objects.

**Return:** A string, or `None` if `array` is empty.

*This document is last updated on Feb 20th (PT) by MikeJollie#1067*
