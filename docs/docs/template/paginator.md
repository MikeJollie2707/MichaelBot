<!-- omit in toc -->
# Pages template

This is a template for a paginator-like control in Discord. It uses reactions to move on to the next or previous pages.

This is used in various commands, notably in `help`, `nhentai`, etc.

<!-- omit in toc -->
## Table of Contents

- [Pages](#pages)
    - [\_\_init\_\_](#__init__)
    - [add_page](#add_page)
    - [event](#event)

## Pages

The implementation class for the paginator structure.

Internally, it contains a list of embeds.

### \_\_init\_\_

The constructor of the class. It sets the initial page.

**Full signature:**

```py
def __init__(self, init_page = 0):
```

**Parameter:**

- `init_page`: The starting index.

### add_page

Add a page into the paginator.

**Full signature:**

```py
def add_page(self, page : discord.Embed):
```

**Parameter:**

- `page`: The page.

**Exception:**

- `TypeError`: Raises when `page` is not a `discord.Embed`.

### event

*This function is a coroutine.*

A function used to interact with the paginator.

This will fire up the paginator and manage it until timeout (which is 2 minutes of inactivity).

**Full signature:**

```py
async def event(self, ctx : commands.Context, channel : discord.TextChannel = None, interupt = True):
```

**Parameters:**

- `ctx`: The context.
- `channel`: The channel you want the pages to be sent. If none provided, it'll use `ctx.channel`.
- `interupt`: `False` if you don't want other user to react the paginator, `True` otherwise. Default value is `True`.
        
**Exception:**

- `AttributeError`: Raises when the parameter(s) is wrong type.
- `discord.Forbidden`: Raises when the bot doesn't have permissions to send messages/add reactions/read message history.

*This document is last updated on Feb 20th (PT) by MikeJollie#1067*
