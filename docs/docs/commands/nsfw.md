<!-- omit in toc -->
# NSFW commands

These are commands that are possibly NSFW. By default, it can only be used in a NSFW channel.

<!-- omit in toc -->
## Table of Contents

- [\_\_init\_\_ [INTERNAL]](#__init__-internal)
- [cog_check [INTERNAL]](#cog_check-internal)
- [konachan](#konachan)
    - [konachan tags](#konachan-tags)
- [display_hentai [INTERNAL]](#display_hentai-internal)
- [nhentai](#nhentai)
    - [nhentai random](#nhentai-random)
    - [nhentai search](#nhentai-search)

## \_\_init\_\_ [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A constructor of the category. This also set the `NSFW` category's emoji as `🔞`.

## cog_check [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A check that apply to all the command in this category. This check will check if `ctx` is in private DM or not, and will raise `NoPrivateMessage()` exception if it is. This also checks if `ctx` is in a NSFW channel or not, and will raise `NSFWChannelRequired()` if it isn't.

## konachan

Send a picture from konachan API.

This will run a search on `konachan.net` (mostly safe) or `konachan.com` and return an image.

- If not provided with tags, this will return a random image.
- If provided with tags, this will return an image with all the tags.

Visit [this page](https://konachan.net/tags) to see all the tags.

Alternatively, you can use `konachan tags` to see some popular tags.

**Usage:** `<prefix>konachan <safe/any> <tags>`

**Parameters:**

- `safe/any`: Either `safe` (search on `konachan.net`) or `any` (search on `konachan.com`). Note that `safe` won't 100% guaranteed that the image is safe (hence why it is in NSFW category).
- `tags`: A list of tags to filter. The tags **must be exactly the same** as appears in `konachan.com`.

**Cooldown:** 5 seconds per 1 use (member).

**Examples:**

- **Example 1:** `$konachan safe blush long_hair`
- **Example 2:** `$konachan any`

**You need:** None.

**The bot needs:** `Send Messages`.

***Subcommands***: [tags](#konachan-tags)

### konachan tags

Show the top 10 tags in `konachan.com`.

**Usage:** `<prefix>konachan tags`

**Example:** `$konachan tags`

**You need:** None.

**The bot needs:** `Send Messages`.

## display_hentai [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A utility function to display a doujin.

**Full signature:**

```py
async def display_hentai(self, ctx, doujin : hentai.Hentai):
```

## nhentai

Search and return a doujin on request. Why need incognito tab when you can read it here on Discord?

**The command is currently doing nothing on its own. You must use its subcommands.**

***Subcommands:*** [random](#nhentai-random), [search](#nhentai-search)

### nhentai random

Search and return a random doujin. 

This can either be a masterpiece or a piece of disgusting trash. Use this if you're bored and want to try a new experience.

**Usage:** `<prefix>nhentai random`

**Cooldown:** 5 seconds per 1 use (member).

**Example:** `$nhentai random`

**You need:** None.

**The bot needs:** `Add Reactions`, `Read Message History`, `Send Messages`.

### nhentai search

Search and return a doujin based on its tags or ID.

- If searched based on tags, it'll search based on `Most Popular`.

**Usage:** `<prefix>nhentai search <id/tags>`

**Parameter:**

- `id/tags`: Either the ID of the doujin or the tags if you want a more broad result. If there's a space in between a tag, use `-`.

**Cooldown:** 5 seconds per 1 use (member).

**Examples:**

- **Example 1:** `$nhentai search 331228`
- **Example 2:** `$nhentai search sole-male sole-female`

**You need:** None.

**The bot needs:** `Add Reactions`, `Read Message History`, `Send Messages`.

*This document is last updated on Feb 19th (PT) by MikeJollie#1067*
