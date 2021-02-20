<!-- omit in toc -->
# Help template

This is a template for the help command. It is used in `help` and `help-all`.

Between `help` and `help-all`, `help-all` is automatically handled by the library, while `help` is a custom command that copies the behavior of `help-all`.

<!-- omit in toc -->
## Table of Contents

- [cog_help_format](#cog_help_format)
- [command_help_format](#command_help_format)
- [BigHelp](#bighelp)
    - [\_\_init\_\_](#__init__)
    - [send_bot_help](#send_bot_help)
    - [send_cog_help](#send_cog_help)
    - [send_group_help](#send_group_help)
    - [send_command_help](#send_command_help)
- [SmallHelp](#smallhelp)
    - [\_\_init\_\_](#__init__-1)
    - [send_bot_help](#send_bot_help-1)
    - [send_cog_help](#send_cog_help-1)
    - [send_command_help](#send_command_help-1)

## cog_help_format

Return an embed that display a category's help. 

The method is responsible for the display of a category's help.

**Full signature:**

```py
def cog_help_format(ctx : commands.Context, cog : commands.Cog) -> discord.Embed:
```

**Parameters:**

- `ctx`: A `commands.Context`.
- `cog`: A `commands.Cog` to display.

## command_help_format

Return an embed that display a command's help.

- If the command has subcommands, it'll display as a brief section.

The method is responsible for the display of a command's help.

**Full signature:**

```py
def command_help_format(ctx : commands.Context, command : commands.Command) -> discord.Embed:
```

**Parameters:**

- `ctx`: A `commands.Context`.
- `cog`: A `commands.Command` to display.

## BigHelp

A class inherited from [`commands.HelpCommand`](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#helpcommand).

The implementation of `help-all` command.

### \_\_init\_\_

The constructor of the class. It sets the docstring and the command's name to `help-all`.

### send_bot_help

*This function is a coroutine.*

An overridden version of [`HelpCommand.send_bot_help()`](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.HelpCommand.send_bot_help).

This is invoked when no arguments are passed to the help command.

**Full signature:**

```py
async def send_bot_help(self, mapping):
```

### send_cog_help

*This function is a coroutine.*

An overridden version of [`HelpCommand.send_cog_help()`](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.HelpCommand.send_cog_help).

This is invoked when the argument passed is a `commands.Cog`.

**Full signature:**

```py
async def send_cog_help(self, cog):
```

### send_group_help

*This function is a coroutine.*

An overridden version of [`HelpCommand.send_group_help()`](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.HelpCommand.send_group_help).

This is invoked when the argument passed is a `commands.Group`.

**Full signature:**

```py
async def send_group_help(self, group):
```

### send_command_help

*This function is a coroutine.*

An overridden version of [`HelpCommand.send_command_help()`](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.HelpCommand.send_command_help).

This is invoked when the argument passed is a `commands.Command`.

**Full signature:**

```py
async def send_command_help(self, command):
```

## SmallHelp

A custom class that has a similar design to [`BigHelp`](#bighelp). It does not inherit from `commands.HelpCommand` due to complex internal design of a help command of the library.

The display implementation of the `help` command. The logic implementation of the `help` command is available in `core.py` file.

### \_\_init\_\_

The constructor of the class. It accepts a `commands.Context` as a general purpose argument.

**Full signature:**

```py
def __init__(self, ctx):
```

### send_bot_help

*This function is a coroutine.*

Display a general help. This is intended to invoke when there is no argument passed in the help command.

**Full signature:**

```py
async def send_bot_help(self):
```

### send_cog_help

*This function is a coroutine.*

Display a category's help. This is intended to invoke when the argument is a category.

**Full signature:**

```py
async def send_cog_help(self, cog):
```

### send_command_help

*This function is a coroutine.*

Display a command's help. If there are any subcommands, it also display them briefly. This is intended to invoke when the argument is a command or a subcommand.

**Full signature:**

```py
async def send_command_help(self, command):
```

*This document is last updated on Feb 20th (PT) by MikeJollie#1067*
