# Currency 102

## Daily

The `daily` command is the only true starting point for new users. As the name suggested, you'll get a certain money and loot everyday. The command has a hard-coded 24-hour cooldown, with another 24-hour window to collect. If you collect before this 24-hour runs out, you will gain a streak. After certain streak milestones, you'll get much better money and loot. However, if you miss out the window, your streak will be reset to 0.

## Craft

Like Minecraft, after you get some materials, you'll eventually need to craft. This can be done using the `craft` command. You can also use its subcommand to view all possible crafting recipes.

## Tools

Tools are special items that can be used to perform *activities*. Currently there are 3 types of tools: pickaxe, axe, and sword. They are needed to use `mine`, `chop`, and `adventure` respectively. A tool has a fixed durability. This will wear out gradually as you perform activities.

To use a tool, you need to equip with `equip`. You can check your current equipments with `equipments`. Once equipped, the tool can be used for the corresponding activity. If you try to equip the same type of tool, the old tool will be swapped out and will have 2 fates: either going back into your inventory (unused) or going to the Void (used). Be sure to check the durability before swapping tools.

## Activities

Activities are a general terms to use when you use `mine`, `chop` or `adventure`. Each activity will give you items that is determined by your corresponding tool. The better the tool, the more loot you will get.

There is a small chance of *dying* while doing these activities. Once you get the death message, all your equipped equipments are destroyed, and you lose 10% of your money as a fee to revive you.

There is also chances of *idle*. While idling, you don't lose any items nor gain anything. The activity will also reset its cooldown. In other words, it's just like you didn't do the session in the first place.

## Shop

The `market` command is used to convert items that you have into money. It also can be used to obtain some materials necessary for future uses. With `market` alone, you'll see a reaction page to see all the items' prices. With its subcommands `market buy` and `market sell`, you can buy or sell items.

To sell items, such items must be available in your inventory. Not all items are purchasable or sellable.

## Inventory

At the end of the day, you want to check what items you have. This is achieved with the command `inventory`. Note that equipped equipments *won't* show up in the `inventory`. This also implies that once equipped, the tool can only be used and then later on destroyed. It can't be sold during this process unless you swap it out.
