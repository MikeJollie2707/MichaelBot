<!-- omit in toc -->
# Currency commands [DEVELOPING]

*This section is labeled as [DEVELOPING], which means the function/command is currently under development and not available for testing.*

These are commands that involve fake economy.

<!-- omit in toc -->
## Table of Contents

- [\_\_init\_\_ [INTERNAL]](#__init__-internal)
- [daily [BETA]](#daily-beta)
- [addmoney [EXPERIMENT]](#addmoney-experiment)
- [rmvmoney [DEVELOPING]](#rmvmoney-developing)
- [balance [BETA]](#balance-beta)

## \_\_init\_\_ [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A constructor for this category. This set the `Currency` category's emoji is `💲`.

## daily [BETA]

*This section is labeled as [BETA], which means the function/command is currently in beta testing and possibly publicly available.*

Get an amount of money every 24h.

**Usage:** `<prefix>daily`

**Cooldown:** 10 seconds per 1 use (user)

**Example:** `$daily`

**You need:** None.

**The bot need:** `Send Messages`.

## addmoney [EXPERIMENT]

*This section is labeled as [EXPERIMENT], which means the function/command is currently in internal testing (alpha) and not publicly available.*

**Usage:** `<prefix>addmoney <amount> <member>`

**Parameter:**

- `amount`: The amount of money you want to add.
- `member`: The member you want to add the money.

**Example:** `$addmoney 1000 MikeJollie`

**You need:** None, for now.

**The bot need:** `Send Messages`.

## rmvmoney [DEVELOPING]

*This section is labeled as [DEVELOPING], which means the function/command is currently under development and not available for testing.*

**Usage:** `<prefix>rmvmoney <amount> <member>`

**Parameter:**

- `amount`: The amount of money you want to remove. If larger than the member's actual money, the money remain will be 0.
- `member`: The member you want to remove the money.

**Example:** `$rmvmoney 1000 MikeJollie`

**You need:** None, for now.

**The bot need:** `Send Messages`.

## balance [BETA]

*This section is labeled as [BETA], which means the function/command is currently in beta testing and possibly publicly available.*

Display the amount of money you currently have.

**Usage:** `<prefix>balance`

**Cooldown:** 2 seconds per 1 use (user)

**Example:** `$balance`

**You need:** None.

**The bot need:** `Send Messages`.

*This document is last updated on Oct 31st (PT) by MikeJollie#1067*
