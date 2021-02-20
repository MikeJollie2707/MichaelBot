<!-- omit in toc -->
# Menu template

This is a template for a menu-like control in Discord. It uses reactions to go into a section.

This is used in various commands and functions, notably in `help`.

<!-- omit in toc -->
## Table of Contents

- [Menu](#menu)
    - [\_\_init\_\_](#__init__)
    - [add_page](#add_page)
    - [add_pages](#add_pages)
    - [event](#event)

## Menu

The implementation class for the menu structure.

Internally, it contains a dictionary in the following format: `{'emoji': embed}`.

### \_\_init\_\_

The constructor of the class. It sets the starting page, the terminate emoji and the return-to-start-page emoji.

**Full signature:**

```py
def __init__(self, init_page : discord.Embed, terminate_emoji : str, return_emoji : str):
```

**Parameters:**

- `init_page`: The center page.
- `terminate_emoji`: An emoji used to exit the menu.
- `return_emoji`: An emoji used to exit small branch back to the center page.
    - The emoji parameters should NOT be the same (currently no check for this).

**Exception:**

- `TypeError`: Raises when `init_page` is not a `discord.Embed`.

### add_page

Add a page to the menu.

**Full signature:**

```py
def add_page(self, emoji : str, page : discord.Embed):
```

**Parameters:**

- `emoji`: The unique emoji that identifies the page.
- `page`: The page.

**Exceptions:**

- `IndexError`: Raises when `emoji` is the same as the terminate emoji.
- `TypeError`: Raises when `page` is not a `discord.Embed`.

### add_pages

Add multiple pages to the menu.

**Full signature:**

```py
def add_pages(self, pages : typing.Dict[str, discord.Embed]):
```

**Parameter:**

- `pages`: A `dict` that has the format `{'emoji': page}`.

**Exceptions:**

*See [Exceptions](#add_page)*.

### event

*This function is a coroutine.*

A function used to interact with the menu.

This will fire up the menu and manage it until timeout (which is 2 minutes of inactivity).

**Full signature:**

```py
async def event(self, ctx : commands.Context, channel : discord.TextChannel = None, interupt = True):
```

**Parameters:**

- `ctx`: The context.
- `channel`: The channel you want to send the menu in. If none provided, it'll use `ctx.channel`.
- `interupt`: `False` if you don't want other user to react the menu, `True` otherwise. Default value is `True`, although it is recommended to `False`.

**Exceptions:**

- `AttributeError`: Raises when the parameter(s) is wrong type.
- `discord.Forbidden`: Raises when the bot doesn't have permission to send messages/add reactions/read messages history.

*This document is last updated on Feb 20th (PT) by MikeJollie#1067*
