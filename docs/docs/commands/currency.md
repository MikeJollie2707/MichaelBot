<!-- omit in toc -->
# Currency commands [INCOMPLETE]

*This section is labeled as [INCOMPLETE], will be updated in the future.*

These are commands that involve fake economy. All items and currencies are shared across guilds. For further guides, refer to [this](#../currency/currency_start.md).

<!-- omit on toc -->
## Table of Contents
- [Table of Contents](#table-of-contents)
- [\_\_init\_\_ [INTERNAL]](#__init__-internal)
- [adventure](#adventure)
- [balance](#balance)
- [brew](#brew)
    - [recipe (brew)](#recipe-brew)
- [chop](#chop)
- [craft](#craft)
    - [recipe (craft)](#recipe-craft)
- [daily](#daily)

## \_\_init\_\_ [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A constructor for this category. This set the `Currency` category's emoji is `💲`.

## adventure

*This is an activity*

Go on an adventure to gather materials!

Watch out though, you might encounter unwanted enemies. Better bring a sword.

**Aliases:** `adv`

**Usage:** `<prefix>adventure`

**Cooldown:** 5 minutes per 1 use (user)

**Example:** `$adv`

**You need:** None.

**The bot needs:** `Use External Emojis`, `Read Message History`, `Send Messages`.

## balance

Display the amount of money you currently have.

**Usage:** `<prefix>balance`

**Cooldown:** 2 seconds per 1 use (user)

**Example:** `$balance`

**You need:** None.

**The bot needs:** `Read Message History`, `Send Messages`.

## brew

Brew potions.

This command behaves the same way [`craft`](#craft) does.

**Usage:** `<prefix>brew [amount=1] <potion>`

**Parameters:**

- `amount`: The amount of potion you want to brew.
- `potion`: The potion you want to brew. Refer to [`brew recipe`](#recipe-brew) for brewable potions.

**Examples:**

- **Example 1:** `$brew 2 fire potion`
- **Example 2:** `$brew luck potion`

**You need:** None.

**The bot needs:** `Use External Emojis`, `Read Message History`, `Send Messages`.

***Subcommands:*** [`recipe`](#recipe-brew)

### recipe (brew)

Show the recipe for one potion or for all potions.

**Usage:** `<prefix>brew recipe [potion]`

**Parameters:**

- `potion`: The potion you want to view. If this is not provided, all potions' recipe will be displayed.

**Examples:**

- **Example 1:** `$brew recipe`
- **Example 2:** `$brew recipe luck potion`

**You need:** None.

**The bot needs:** `Use External Emojis`, `Read Message History`, `Send Messages`.

## chop

*This is an activity*

Chop some trees.

The majority of reward is log, although you can also find some other things with a better axe.

**Usage:** `<prefix>chop`

**Cooldown:** 5 minutes per 1 use (user).

**Example:** `$chop`

**You need:** None.

**The bot needs:** `Use External Emojis`, `Read Message History`, `Send Messages`.

## craft

Craft up to `amount` items.

The command will repeatedly attempt to craft the item until the pseudo-amount exceed `amount`, in which it will rollback the latest craft attempt. That will be the final amount of the craft.

**Usage:** `<prefix>craft [amount=1] <item>`

**Parameters:**

- `amount`: The maximum amount of items you'll get.
- `item`: The item you want to craft. Refer to [`craft recipe`](#recipe-craft) for craftable items.

**Examples:**

- **Example 1:** `$craft 2 stick`
- **Example 2:** `$craft wooden pickaxe`

**You need:** None.

**The bot needs:** `Use External Emojis`, `Read Message History`, `Send Messages`.

***Subcommands:*** [`recipe`](#recipe)

### recipe (craft)

Show the *crafting* recipe for one item or for all items.

**Usage:** `<prefix>craft recipe [item]`

**Parameter:**

- `item`: The item you want. If this is not provided, the command will show all recipes for all items.

**Examples:**

- **Example 1:** `$craft recipe`
- **Example 2:** `$craft recipe wood`

**You need:** None.

**The bot needs:** `Use External Emojis`, `Read Message History`, `Send Messages`.

## daily

Get an amount of money every 24h.

This command's cooldown is hard-coded. You cannot reset it with `reset_all_cooldown`.

**Usage:** `<prefix>daily`

**Cooldown:** 1 day per 1 use (user)

**Example:** `$daily`

**You need:** None.

**The bot needs:** `Read Message History`, `Send Messages`.

## equip

Equip a tool.

*This document is last updated on Feb 19th (PT) by MikeJollie#1067*
