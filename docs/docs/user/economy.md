# Economy Category

Economy Commands

## `balance`

View your balance.

Type: `Prefix Command`, `Slash Command`

Aliases: `bal`

## `barter`

View and/or perform a barter. Get your gold ready.

Type: `Prefix Command`, `Slash Command`

Cooldown: 5 seconds per 1 use per user.

Additional Info:

- Barters can contains purchases that can't be made via `market`.
- Barters will reset every 4 hours.
- This can only be used when you're in the Nether.

## `bet <number> [money = 1]`

Bet your money to guess a number in the range 0-50. Don't worry, I won't cheat :)

Type: `Prefix Command`, `Slash Command`

Parameters:

- `number`: Your guessing number. Stay within 0-50!
- `money`: The amount to bet. You'll either lose this or get 2x back. At least 1.

## `craft <item> [times = 1]`

Craft various items.

Type: `Prefix Command`, `Slash Command` (recommended)

Cooldown: 1 second per 1 use per user.

Parameters:

- `item`: The name or alias of the item to craft.
- `times`: How many times this command is executed. Default to 1. Max is 100.

## `daily`

Receive rewards everyday. Don't miss it though!

Type: `Prefix Command`, `Slash Command`

Cooldown: 1 day per 1 use per user (hard).

Additional Info:

- The higher the daily streak, the better your reward will be.
- If you don't collect your daily within 48 hours since the last time you collect, your streak will be reset to 1.

## `equip <equipment>`

Equip a tool. Get to work!

Type: `Prefix Command`, `Slash Command` (recommended)

Cooldown: 10 seconds per 1 use per user.

Parameters:

- `equipment`: The equipment's name or alias to equip.

## `equipments`

View your current equipments.

Type: `Prefix Command`, `Slash Command`

Cooldown: 10 seconds per 1 use per user.

## `explore`

Explore the world and get resources by killing monsters. You'll need a sword equipped.

Type: `Prefix Command`, `Slash Command`

Cooldown: 300 seconds per 1 use per user.

## `inventory [view_option = compact]`

View your inventory.

Type: `Prefix Command`, `Slash Command`

Cooldown: 10 seconds per 1 use per user.

Aliases: `inv`

Parameters:

- `view_option`: Options to view inventory. Valid options are `full`, `compact`, and `value`. Default to `compact`.

## `market`

View public purchases.

Type: `Prefix Command`, `Slash Command`

### `market view`

View public purchases.

Type: `Prefix Command`, `Slash Command`

### `market buy <item> [amount = 1]`

Buy an item from the market.

Type: `Prefix Command`, `Slash Command`

Parameters:

- `item`: The item to purchase.
- `amount`: The amount to purchase. Default to 1.

### `market sell <item> [amount = 1]`

Sell an item from your inventory.

Type: `Prefix Command`, `Slash Command`

Parameters:

- `item`: The item to sell.
- `amount`: The amount to sell, or 0 to sell all. Default to 1.

## `mine`

Mine for resources. You'll need a pickaxe equipped.

Type: `Prefix Command`, `Slash Command`

Cooldown: 300 seconds per 1 use per user.

## `trade`

View and/or perform a trade. Get your money ready.

Type: `Prefix Command`, `Slash Command`

Cooldown: 5 seconds per 1 use per user.

Additional Info:

- Trades can contains purchases that can't be made via `market`.
- Trades will reset every 4 hours.
- This can only be used when you're in the Overworld.

## `travel <world>`

Travel to another world.

Type: `Prefix Command`, `Slash Command`

Cooldown: 1 day per 1 use per user (hard).

Parameters:

- `world`: The world to travel to. Valid options are `overworld` and `nether`.

*Last updated on Jul 25, 2022*
