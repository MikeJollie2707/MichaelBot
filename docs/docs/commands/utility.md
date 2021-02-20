<!-- omit in toc -->
# Utility commands

These are commands that are just random and fun.

<!-- omit in toc -->
## Table of Contents

- [\_\_init\_\_ [INTERNAL]](#__init__-internal)
- [cog_check [INTERNAL]](#cog_check-internal)
- [calc](#calc)
- [dice](#dice)
- [embed](#embed)
    - [embed info](#embed-info)
- [embed_simple [BETA]](#embed_simple-beta)
- [how](#how)
- [howgay](#howgay)
- [ping](#ping)
- [poll [BETA]](#poll-beta)
- [say](#say)
- [send](#send)
- [speak](#speak)

## \_\_init\_\_ [INTERNAL]

*This section is labeled as [INTERNAL], meaning that is is **NOT** a command. It is here only to serve the developers purpose.*

A constructor of the category. This set the `Utility` category's emoji as `😆`.

## cog_check [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A check that apply to all the command in this category. This check will check if `ctx` is in private DM or not, and will raise `NoPrivateMessage()` exception if it is.

## calc

A mini calculator that calculate like a calculator (duh).

Possible constants you can use are: `PI`, `E`.

*Note 1: Trigonometry functions follow radian, not degree*.

*Note 2: `sin(PI)` and some others will returns non-zero result due to decimal accuracy.*

**Usage:** `<prefix>calc <expression>`

**Examples:**

- **Example 1:** `$calc 1+2`
- **Example 2:** `$calc 1 + 2 - 3 * 4 / 5`
- **Example 3:** `$calc sqrt(25) * (3 + 4) - sin(0)`

**You need:** None.

**The bot needs:** `Read Message History`, `Send Messages`.

## dice

Roll a dice. Simple. 6-sided though.

**Usage:** `<prefix>dice`

**Example:** `$dice`

**You need:** None.

**The bot needs:** `Read Message History`, `Send Messages`.

## embed

Create and send a full-featured rich embed. Refers to [`embed info`](#embed-info) for more information.

**Usage:** `<prefix>embed <json-like object>`

**Parameter:**

- `json-like object`: *Refers to [`embed info`](#embed-info) for more information*.

**Cooldown:** 5 seconds per 1 use (user)

**Example:** In *[`embed info`](#embed-info)*

**You need:** None.

**The bot needs:** `Send Messages`.

***Subcommands:*** [info](#embed-info)

### embed info

Display the following text:

To create a full-featured rich embed, you must use the JSON format as part of the argument.

Take a look at [this awesome page](https://embedbuilder.nadekobot.me/) that visualize the embed and make your life much easier when writing JSON. 

Edit the embed like you want to, and copy the JSON on the right, and surround that around codeblock to look easier.

For example:

$embed
```
{
"title": "Title",
"description": "Description",
"color": 53380,
"fields": [
    {
    "name": "Field 1",
    "value": "Value 1",
    "inline": true
    }
]
}
```

Try poking around the visualizer for many other features.

For those who are hardcore enough to say "Visualizer is for noob", then go read [the official definition of an embed](https://discordapp.com/developers/docs/resources/channel#embed-object)
and write one for yourself.

**Usage:** `<prefix>embed info`

**Cooldown:** 5 seconds per 1 use (user)

**Example:** `$embed info`

**You need:** None.

**The bot needs:** `Manage Messages`, `Read Message History`, `Send Messages`.

## embed_simple [BETA]

*This section is labeled as [BETA], which means the function/command is currently in beta testing and possibly publicly available.*

Send a simple embed message.

You'll respond to 3 questions to determine the content. Use `Pass` if you want to skip one.

**Usage:** `<prefix>embed_simple`

**Cooldown:** 5 seconds per 1 use (user)

**Example:** `$embed_simple`

**You need:** None.

**The bot needs:** `Manage Messages`, `Read Message History`, `Send Messages`.

## how

An ultimate measurement to everything except gayness. Use [`howgay`](#howgay) for that.

**Usage:** `<prefix>how <measure unit> <target>`

**Parameters:**

- `measure unit`: Can be anything. Be creative! Examples: `smart`, `dumb`, `weird`, etc.
- `target`: Can be anything. Be creative! Examples: `MichaelBot`, `MikeJollie`, `your mom`, etc.

**Cooldown:** 10 seconds per 5 uses (user)

**Examples:**

- **Example 1:** `$how smart Stranger.com`
- **Example 2:** `$how "stupidly dumb" "Nightmare monsters"`

**You need:** None.

**The bot needs:** `Read Message History`, `Send Messages`.

## howgay

An ultimate measurement to gayness. Use [`how`](#how) if you want to measure other things.

**Usage:** `<prefix>howgay <target>`

**Parameters:**

- `target`: Can be anything. Be creative! Examples: `MichaelBot`, `Ace_Shiro`, `Fortnite`, etc.

**Cooldwn:** 10 seconds per 5 uses (user)

**Examples:**

- **Example 1:** `$howgay MikeJollie`
- **Example 2:** `$howgay "iphone 11"`

**You need:** None.

**The bot needs:** `Read Message History`, `Send Messages`.

## ping

Show the latency of the bot. It might take a while to update.

**Usage:** `<prefix>ping`

**Example:** `$ping`

**You need:** None.

**The bot needs:** `Read Message History`, `Send Messages`.

## poll [BETA]

*This section is labeled as [BETA], which means the function/command is currently in beta testing and possibly publicly available.*

Make a poll for you right in the current channel.

Currently it only support up to 10 options max and at least 2 options.

**Usage:** `<prefix>poll <title> <choice 1 | choice 2 | choice n>`

**Parameters:**

- `title`: The title of the poll. Wrap with `""` if it has spaces.
- `choice 1 | choice 2`: The options separated by a space, `|` and another space.

**Example:** `$poll "Who's cooler?" MichaelBot | MikeJollie | "Some random nons"`

**You need:** None.

**The bot needs:** `Add Reactions`, `Read Message History`, `Send Messages`.

## say

Repeat what you say. Like a parrot.

**Usage:** `<prefix>say <content>`

**Parameter:**

- `content`: The content.

**Example:** `$say MikeJollie is gay lol.`

**You need:** None.

**The bot needs:** `Manage Messages`, `Send Messages`.

## send

Send a message to a user or to a channel.

A basic rule is the bot can't send message to the destination if it can't see or doesn't have permissions.

**Usage:** `<prefix>send <id> <message>`

**Parameters:**

- `id`: Either a channel's id or a user's id. The destination must allows the bot to send.
- `message`: The message.

**Cooldown:** 120 seconds per 1 use (user)

**Example:** `$send 577663051722129427 Gay.`

**You need:** None.

**The bot needs:** `Send Messages`.

## speak

Make the bot speak!

**Usage:** `<prefix>speak <content>`

**Parameter:**

- `content`: The content

**Example:** `$speak MikeJollie is gay.`

**You need:** None.

**The bot needs:** `Manage Messages`, `Send TTS Messages`, `Send Messages`.

*This document is last updated on Feb 20th (PT) by MikeJollie#1067*
