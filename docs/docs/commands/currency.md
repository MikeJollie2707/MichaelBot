<!-- omit in toc -->
# Currency commands [INCOMPLETE]

*This section is labeled as [INCOMPLETE], will be updated in the future.*

These are commands that involve fake economy. All items and currencies are shared across guilds. For further guides, refer to [this](#../currency/currency_start.md).

<!-- omit on toc -->
## Table of Contents

- [\_\_init\_\_ [INTERNAL]](#__init__-internal)
- [daily](#daily)
- [balance](#balance)
- [topmoney [DEVELOPING]](#topmoney-developing)

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

**Usage:** `<prefix>brew [n=1] <potion>`

**Parameters:**

- `n`: The number of times this command is executed. **It is NOT the amount of potions you'll get**.
- `potion`: The potion you want to brew. Refer to [`brew recipe`](#recipe-brew) for brewable potions.

**Examples:**

- **Example 1:** `$brew 2 fire potion`
- **Example 2:** `$brew luck potion`

**You need:** None.

**The bot needs:** `Use External Emojis`, `Read Message History`, `Send Messages`.

***Subcommands:*** [`recipe`](#recipe-brew)

### recipe (brew)

Show the recipe for one potion or for all potions.



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

Perform a craft `n` times.

This will give you `n * <quantity>` items, with `<quantity>` is the `You gain` section in `craft recipe`.

Craft wisely!

**Usage:** `<prefix>craft [n=1] <item>`

**Parameters:**

- `n`: The number of times this command is executed. **It is NOT the amount of items you'll get**.
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

**Usage:** `<prefix>daily`

**Cooldown:** 1 day per 1 use (user)

**Example:** `$daily`

**You need:** None.

**The bot needs:** `Read Message History`, `Send Messages`.

## topmoney [DEVELOPING]

*This section is labeled as [DEVELOPING], which means the function/command is currently under development and not available for testing.*

Show the top 10 users with the most amount of money.

The default option is `local`.

**Usage:** `<prefix>topmoney [global/local]`

**Parameter:**

- `global/local`: Either `global` (all MichaelBot's users) or `local` (all members in the guild invoked).

**Examples:**

- **Example 1:** `$topmoney global`
- **Example 2:** `$topmoney`

**You need:** None.
**The bot needs:** `Read Message History`, `Send Messages`.

## work

Go to work and earn money.

*This command is going to get removed once inventory system is implemented.*

**Usage:** `<prefix>work`

**Cooldown:** 120 seconds per 1 use (user)

**Example:** `$work`

**You need:** None.

**The bot needs:** `Read Message History`, `Send Messages`.

*This document is last updated on Feb 19th (PT) by MikeJollie#1067*
