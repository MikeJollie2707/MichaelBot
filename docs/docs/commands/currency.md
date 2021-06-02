<!-- omit in toc -->
# Currency commands

These are commands that involve fake economy. All items and currencies are shared across guilds. For further guides, refer to [this](#../currency/currency_start.md).

The argument `item` or `tool` or `potion` refers to the name of an item (ex: `wooden pickaxe`). This argument is case insensitive.

<!-- omit in toc -->
## Table of Contents
- [Constants [INTERNAL]](#constants-internal)
- [\_\_init\_\_ [INTERNAL]](#__init__-internal)
- [cog_unload [INTERNAL]](#cog_unload-internal)
- [\_\_get_reward\_\_ [INTERNAL]](#__get_reward__-internal)
- [\_\_remove_equipments_on_die\_\_ [INTERNAL]](#__remove_equipments_on_die__-internal)
- [\_\_remove_potions_on_die\_\_ [INTERNAL]](#__remove_potions_on_die__-internal)
- [\_\_attempt_fire\_\_ [INTERNAL]](#__attempt_fire__-internal)
- [\_\_attempt_luck\_\_ [INTERNAL]](#__attempt_luck__-internal)
- [\_\_attempt_haste\_\_ [INTERNAL]](#__attempt_haste__-internal)
- [\_\_attempt_looting\_\_ [INTERNAL]](#__attempt_looting__-internal)
- [\_\_reduce_tool_durability\_\_](#__reduce_tool_durability__)
- [cog_check [INTERNAL]](#cog_check-internal)
- [\_member_join [INTERNAL]](#_member_join-internal)
- [\_command_completion [INTERNAL]](#_command_completion-internal)
- [adventure](#adventure)
- [badges](#badges)
- [balance](#balance)
- [refresh_barter [INTERNAL]](#refresh_barter-internal)
- [before_barter [INTERNAL]](#before_barter-internal)
- [barter](#barter)
- [brew](#brew)
    - [brew recipe](#brew-recipe)
- [chop](#chop)
- [craft](#craft)
    - [craft recipe](#craft-recipe)
- [daily](#daily)
- [equip](#equip)
- [equipments](#equipments)
- [inventory](#inventory)
    - [inventory all](#inventory-all)
    - [inventory value](#inventory-value)
    - [inventory sort [DEVELOPING]](#inventory-sort-developing)
- [iteminfo](#iteminfo)
- [leaderboard](#leaderboard)
- [market](#market)
    - [market buy](#market-buy)
    - [market sell](#market-sell)
- [mine](#mine)
- [trade](#trade)
- [travelto](#travelto)
- [refresh_trade [INTERNAL]](#refresh_trade-internal)
- [before_trade [INTERNAL]](#before_trade-internal)
- [usepotion](#usepotion)

## Constants [INTERNAL]

These are constants that can be used to tweak many effects.

```py
# The maximum trade per refresh
MAX_TRADE = 4
# The maximum value per trade
MAX_TRADE_VALUE = 1000
# At least 1 trade has that has lower value than this
MIN_TRADE_VALUE = 200
# The maximum barter per refresh
MAX_BARTER = 5
# Refresh interval
TRADE_BARTER_REFRESH = 4 # hours

# Durability penalty rate
DURABILITY_PENALTY = 0.05
# Maximum durability loss
DURABILITY_MAX_PENALTY = 100

# Overworld die chance
OVERWORLD_DIE = 0.0125
# Nether die chance
NETHER_DIE = 0.025
# Space die chance
SPACE_DIE = 0.0125
# Money penalty rate
MONEY_PENALTY_DIE = 0.10

# Luck Potion activating chance
LUCK_ACTIVATE_CHANCE = 0.5
# Fire Potion activating chance
FIRE_ACTIVATE_CHANCE = 0.25
# Haste Potion activating chance
HASTE_ACTIVATE_CHANCE = 0.75
# Looting Potion activating chance
LOOTING_ACTIVATE_CHANCE = 0.75

# Chance of netherite tools not being destroyed upon death
NETHERITE_SURVIVE_CHANCE = 0.25

# Unused for now
POTION_STACK_MULTIPLIER = 1
```

## \_\_init\_\_ [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A constructor for this category. This set the `Currency` category's emoji is `💲`.

It also creates prep work for `trade` and `barter`.

## cog_unload [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A sort of "destructor" for this category. It ends [`refresh_barter()`](#refresh_barter-internal) and [`refresh_trade()`](#refresh_trade-internal).

## \_\_get_reward\_\_ [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

Randomly generate the final reward, given a dictionary of possible rewards and weight.

**Full signature:**

```py
def __get_reward__(self, loot : dict, bonus_stack = 0) -> dict:
```

**Important Parameters:**
- `loot`: A dictionary that should always be returned from `loot.get_..._loot()` with very minimal tweak.
- `bonus_stack`: Indicates the number of special potions' stacks, such as `Haste Potion`.

**Return:** A `dict` in the format of `{item : amount}`.

## \_\_remove_equipments_on_die\_\_ [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

Remove equipments and `DEATH_PENALTY` of user's money. Netherite tool will have a `NETHERITE_SURVIVE_CHANCE` chance it won't be removed.

**Full signature:**

```py
async def __remove_equipments_on_die__(self, conn, member):
```

## \_\_remove_potions_on_die\_\_ [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

Remove all potions from the user.

**Full signature:**

```py
async def __remove_potions_on_die__(self, conn, member):
```

## \_\_attempt_fire\_\_ [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

Attempt to use the fire potion.

- If it is successfully used AND the fire pot is not expired, return `True`.
- If it is successfully used AND the fire pot is expired, throw `DB.ItemExpired`.
- If it is unsuccessful, return `False`.

**Full signature:**

```py
async def __attempt_fire__(self, conn, member):
```

## \_\_attempt_luck\_\_ [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

Attempt to use luck potion.

- If it is successful, `loot["rolls"]` will be modified.
    - If luck potion expires, throw `DB.ItemExpired`.
- If it is not successful, nothing happen.

**Full signature:**

```py
async def __attempt_luck__(self, conn, member, loot):
```

**Important Parameter:**

- `loot`: A dictionary that should be returned from `loot.get_..._loot()`.

## \_\_attempt_haste\_\_ [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

Attempt to use haste potion.

- If it is successful AND haste potion is not expired, return the number of stacks.
- If it is successful AND haste potion is expired, throw `DB.ItemExpired`.
- If it is not successful, return `0`.

**Full signature:**

```py
async def __attempt_haste__(self, conn, member):
```

## \_\_attempt_looting\_\_ [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

Attempt to use looting potion.

- If it is successful AND looting potion is not expired, return the number of stacks.
- If it is successful AND looting potion is expired, throw `DB.ItemExpired`.
- If it is not successful, return `0`.

**Full signature:**

```py
async def __attempt_looting__(self, conn, member):
```

## \_\_reduce_tool_durability\_\_

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

Reduce the tool's durability randomly, up to the maximum penalty, defined by `DURABILITY_MAX_PENALTY`.

**Full signature:**

```py
async def __reduce_tool_durability__(self, conn, member, current_tool):
```

**Important Parameter:**

- `current_tool`: A `dict` that has an `id` key of the tool.

## cog_check [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A category-wise check.

- If `ctx` is private (DM), `NoPrivateMessage()` exception will be raised.
- If the bot doesn't have connection to a database, a generic `CheckFailure()` will be raised.

**Full signature:**

```py
async def cog_check(self, ctx : commands.Context):
```

## \_member_join [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A listener to the `on_member_join` event that insert the new user into the database if they didn't exist.

**Full signature:**

```py
async def _member_join(self, member):
```

## \_command_completion [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A listener to the `on_command_completion` event that update the badge of the user once a currency command is finished.

**Full signature:**

```py
async def _command_completion(self, ctx):
```

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

## badges

Display a user's badges or your badges.

**Usage:** `<prefix>badges [user]`

**Parameter:**

- `user`: The user you want to view. Default to yourself.

**Cooldown:** 3 seconds per 1 use (user)

**Examples:**

- **Example 1:** `$badges`
- **Example 2:** `$badges MikeJollie`

**You need:** None.

**The bot needs:** `Use External Emojis`, `Read Message History`, `Send Messages`.

## balance

Display the amount of money you currently have.

**Usage:** `<prefix>balance`

**Cooldown:** 2 seconds per 1 use (user)

**Example:** `$balance`

**You need:** None.

**The bot needs:** `Read Message History`, `Send Messages`.

## refresh_barter [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A task loop that's responsible to refresh and create barters every `TRADE_BARTER_INTERVAL` hours.

## before_barter [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A callback that ensures `refresh_barter` starts only when the bot is ready.

## barter

Barter with the Luxury Piglin for goods using gold. This command is only available in the Nether.

**Usage:** `<prefix>barter [barter_index] [time=1]`

**Parameters:**

- `barter_index`: The index of the barter you want to get. If this is not provided, it'll display all possible barters. You also do not provide the `time` parameter if this is not provided.
- `time`: The number of times you'll perform the barter. Default to 1, max is 50.

**Cooldown:** 5 seconds per 1 use (user)

**Examples:**

- **Example 1:** `$barter`
- **Example 2:** `$barter 5 2`

**You need:** None.

**The bot needs:** `Use External Emojis`, `Read Message History`, `Send Messages`.


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

***Subcommands:*** [`recipe`](#brew-recipe).

### brew recipe

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

***Subcommands:*** [`recipe`](#craft-recipe)

### craft recipe

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

*This command's cooldown is hard-coded. You cannot reset it with `reset_all_cooldown`.*

**Usage:** `<prefix>daily`

**Cooldown:** 1 day per 1 use (user)

**Example:** `$daily`

**You need:** None.

**The bot needs:** `Use External Emojis`, `Read Message History`, `Send Messages`.

## equip

Equip a tool. This can be either pickaxe, sword, or axe. The tool you try to equip must be in your inventory.

If you try to equip the same type of tool you already equipped, the old tool will be swapped out, and will be either destroyed or kept.

**Usage:** `<prefix>equip [tool]`

**Parameter:**

- `tool`: The tool name.

**Example:** `$equip iron pickaxe`

**You need:** None.

**The bot needs:** `Use External Emojis`, `Read Message History`, `Send Messages`.

## equipments

Display all your equipments and their durabilities.

**Usage:** `<prefix>equipments`

**Example:** `$equipments`

**You need:** None.

**The bot needs:** `Use External Emojis`, `Read Message History`, `Send Messages`.

## inventory

View your inventory, sorted by amount.

**Aliases:** `inv`

**Usage:** `<prefix>inventory`

**Cooldown:** 5 seconds per 1 use (user)

**Example:** `$inv`

**You need:** None.

**The bot needs:** `Use External Emojis`, `Read Message History`, `Send Messages`.

***Subcommands:*** [`all`](#inventory-all), [`value`](#inventory-value).

### inventory all

Display your inventory in a detailed manner.

**Usage:** `<prefix>inventory all`

**Cooldown:** 5 seconds per 1 use (user)

**Example:** `$inv all`

**You need:** None.

**The bot needs:** `Use External Emojis`, `Read Message History`, `Send Messages`.

### inventory value

Display the value of your inventory. This will show the money you'll get if you sell all sellable items in your inventory to `market`.

**Usage:** `<prefix>inventory value`

**Cooldown:** 5 seconds per 1 use (user)

**Example:** `$inv value`

**You need:** None.

**The bot needs:** `Use External Emojis`, `Read Message History`, `Send Messages`.

### inventory sort [DEVELOPING]

*This section is labeled as [DEVELOPING], which means the function/command is currently under development and not available for testing.*

## iteminfo

Display an item's information.

**Usage:** `<prefix>iteminfo <item>`

**Cooldown:** 5 seconds per 1 use (user)

**Example:** `$iteminfo log`

**You need:** None.

**The bot needs:** `Use External Emojis`, `Read Message History`, `Send Messages`.

## leaderboard

Show the top 10 users with the highest amount of money.

**Aliases:** `lb`

**Usage:** `<prefix>leaderboard [local/global=local]`

**Parameter:**

- `local/global`: Either `local` or `global`. `local` will show the guild's leaderboard, while `global` will show every MichaelBot's users. Default to `local`.

**Cooldown:** 5 seconds per 1 use (user)

**Example:** `$lb global`

**You need:** None.

**The bot needs:** `Read Message History`, `Send Messages`.

## market

Display all items' value in terms of money. To perform transactions, please use the command's subcommands.

**Usage:** `<prefix>market`

**Cooldown:** 5 seconds per 1 use (user)

**Example:** `$market`

**You need:** None.

**The bot needs:** `Use External Emojis`, `Read Message History`, `Send Messages`.

***Subcommands:*** [buy](#market-buy), [sell]()

### market buy

Buy an item with your money. Note that many items can't be bought.

**Usage:** `<prefix>market buy [amount=1] <item>`

**Parameter:**

- `amount`: The amount of items you want to buy. Default to 1.
- `item`: The item you want to buy.

**Cooldown:** 5 seconds per 1 use (user)

**Examples:**

- **Example 1:** `$market buy 5 wood`
- **Example 2:** `$market buy fire potion`

**You need:** None.

**The bot needs:** `Use External Emojis`, `Read Message History`, `Send Messages`.

### market sell

Sell an item in your inventory for money. Note that some items can't be sold.

**Usage:** `<prefix>market sell [amount=1] <item>`

**Parameter:**

- `amount`: The amount of items you want to sell. Default to 1, and don't go too overboard!
- `item`: The item you want to sell. Must be in your inventory.

**Cooldown:** 5 seconds per 1 use (user)

**Examples:**

- **Example 1:** `$market sell diamond`
- **Example 2:** `$market sell 10 stone`

**You need:** None.

**The bot needs:** `Use External Emojis`, `Read Message History`, `Send Messages`.

## mine

*This is an activity*

Go mining to earn resources.

Can't mine with your barehands like you did with the tree. Gotta have some proper tools ya' know?

**Usage:** `<prefix>mine`

**Example:** `$mine`

**You need:** None.

**The bot needs:** `Use External Emojis`, `Read Message History`, `Send Messages`.

## trade

Trade for items or for money. This command is only available in the Overworld.

**Usage:** `<prefix>trade [trade_index] [time=1]`

**Parameters:**

- `trade_index`: The index of the trade you want to get. If this is not provided, it'll display all possible trades. You also do not provide the `time` parameter if this is not provided.
- `time`: The number of times you'll perform the trade. Default to 1, max is 50.

**Cooldown:** 5 seconds per 1 use (user)

**Examples:**

- **Example 1:** `$trade`
- **Example 2:** `$trade 1 10`

**You need:** None.

**The bot needs:** `Use External Emojis`, `Read Message History`, `Send Messages`.

## travelto

Travel to another dimension.
Dimensions you can travel: `Overworld`, `Nether`, `Space`. More info at [Dimensions](../currency/dimensions.md).

*This command's cooldown is hard-coded. You cannot reset with `reset_all_cooldown`.*

**Aliases:** `moveto`, `goto`

**Usage:** `<prefix>travelto <destination>`

**Parameter:**

- `destination`: The destination dimension. Either `Overworld`, `Nether`, or `Space`.

**Cooldown:** 1 day per 1 use (user)

**Example:** `$travelto Nether`

**You need:** None.

**The bot needs:** `Use External Emojis`, `Read Message History`, `Send Messages`.

## refresh_trade [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A task loop that's responsible to refresh and create trades every `TRADE_BARTER_INTERVAL` hours.

## before_trade [INTERNAL]

*This section is labeled as [INTERNAL], meaning that it is **NOT** a command. It is here only to serve the developers purpose.*

A callback that ensures `refresh_trade` starts only when the bot is ready.

## usepotion

Use a potion. Note that you can only use up to 10 stacks of potions of the same kind at once.

**Usage:** `<prefix>usepotion [amount=1] <potion>`

**Parameters:**

- `amount`: The amount of stacks you want to apply.
- `potion`: The potion you want to apply.

**Cooldown:** 5 seconds per 1 use (user)

**Example:** `$usepotion 2 luck potion`

**You need:** None.

**The bot needs:** `Use External Emojis`, `Read Message History`, `Send Messages`.

*This document is last updated on June 1st (PT) by MikeJollie#1067*
