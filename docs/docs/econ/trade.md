# Trading System

The trading system refers to a non-conventional way to convert item into money and vice versa.

By the conventional way, it is to browse `market (view)`, then make any purchases using `market buy` and `market sell`. This is very stable; price are always the same unless the bot receives a balance update. However, the trading system has deals that are unconventional to `market`. These deals are fragile, and you only have around 4 hours before new deals arrive, overriding the old ones.

Each deal has a **limit** a user can use the deal before it's expired. For example, a deal can have up to 20 trades permitted. After using the deal the 20th time, it is locked. The user would have to wait until the deals refresh or take a look at other deals. **This limit is tracked per user per offer**, not globally.

As of now, `trade` and `barter` are the commands that use this system. From a design standpoint, they're practically the same. There are multiple deals, they all refresh every 4 hours, they use the same interface to interact with, etc.

As for the interface, the trading system will use an embed that list all the offers along with a *select menu* the user can choose from. The user would then choose the offer they like to deal, which the bot would then perform the action. **This cannot be undone.** As the user keeps trading, the embed will edit itself to reflect the trading limit per each offer. Once the limit is reached, that offer will no longer appear in the menu, and you'd have to choose a different one or ignore for the menu to time out.

## `trade`

The `trade` command pops up 6 deals for you to choose from. Out of these 6 deals, the first deal (or the first trade) is **guaranteed** to be an item-to-money trade. The next 4 deals are **guaranteed** to be money-to-item, and the last deal is **guaranteed** to be item-to-item. It can only be used in the Overworld.

## `barter`

The `barter` command can be considered as a superior version of `trade`. It will pop up 9 deals for you to choose from. Out of these 9 deals, the first deal is **guaranteed** to be an item-to-gold trade. The next 7 deals are **guaranteed** to be gold-to-item, and the last deal is **guaranteed** to be item-to-item. Generally, `barter` offers are higher in value since the value cap for `barter` is bigger than `trade`. It can only be used in the Nether.
