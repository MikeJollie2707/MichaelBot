<!-- omit in toc -->
# Currency commands [DEVELOPING]

*This section is labeled as [DEVELOPING], which means the function/command is currently under development and not available for testing.*

These are commands that involve fake economy. All items and currencies are shared across guilds.

<!-- omit on toc -->
## Table of Contents

- [\_\_init\_\_ [INTERNAL]](#__init__-internal)
- [daily](#daily)
- [balance](#balance)
- [topmoney [DEVELOPING]](#topmoney-developing)

## \_\_init\_\_ [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A constructor for this category. This set the `Currency` category's emoji is `💲`.

## daily

Get an amount of money every 24h.

**Usage:** `<prefix>daily`

**Cooldown:** 1 day per 1 use (user)

**Example:** `$daily`

**You need:** None.

**The bot needs:** `Read Message History`, `Send Messages`.

## balance

Display the amount of money you currently have.

**Usage:** `<prefix>balance`

**Cooldown:** 2 seconds per 1 use (user)

**Example:** `$balance`

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
