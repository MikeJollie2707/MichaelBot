# Currency 101

The bot has a dedicated currency system that is heavily inspired by the Minecraft concept. However, because of the Discord limitation, sometimes it can be confusing on where to start or where to progress. This page serve a basic introduction to the overall economic system of MichaelBot.

## Start

First off, use the command `daily`. The bot will then gives you some fictional **money** and more importantly, **items**. It'll probably look like `5x Log, 1x Stick`. Congratulation, now you have the starting items to further progress!

## Crafting

Like Minecraft, you can craft items from other items! If you just use `daily` for the first time, you'll have enough item to get your first pickaxe! Execute these commands:

```
craft 8 wood
craft 4 stick
craft wooden pickaxe
```

You got your first pickaxe! You can view it in your **inventory** with `inventory` command. Pickaxes, along with some other items, are considered as **tool**, a special subset of item. There are 3 types of tools, and pickaxe is one of them, but we'll talk about this later.

## Activity

What can you do with a wooden pickaxe? Just like Minecraft, the sole purpose of this is to get a couple of stones and then throw it away completely. Here's how to get some stone for the next pickaxe:

```
equip wooden pickaxe
mine
```

The first command essentially remove the wooden pickaxe from your inventory and put it in your **equipments**. You can view it with `equipments` command.

The second commands will perform an **activity** called *mining*. There are currently 3 types of activities, which is discussed in a separate article. However, this specific activity will use the pickaxe you equipped to mine for resources. Most likely you'll get stone and maybe some coal. You may or may not have 3 stones, but if you don't, don't worry. You can wait for 5 minutes and do the mining activity again to get more stones :)

## Stone Rank

If you manage to get 3 stones, you can go ahead and craft the stone pickaxe! However, if you try to equip it, you'll probably see the message `Your old tool is used, so it's gone into the Void after you remove it :(`. It is because you can have multiple pickaxes (or in general, tools of the same type) *in your inventory*, but you can only equip one tool of the same type *in your equipments*. For example, if you equip the stone pickaxe while having the wood pickaxe, the wood pickaxe will get replaced by the new stone pickaxe. The wooden pickaxe will then have 2 fates: if it is used, then it'll be destroyed, otherwise, it'll return to your inventory safely. Unfortunately, you used the wooden pickaxe to get stones, so now it's gone :(

## Conclusion

And that's it for the absolute beginning. Read other articles to know some general info. Explore!

## Disclaimers

### Regarding exploiting bugs

If you are caught exploiting major bugs in MichaelBot to gain advantage, your progress can be reset, and sometimes you might be even get blacklist from the bot. Use `report report` to report the bug instead of exploiting it.

### Regarding real money

As mentioned, under **no** circumstances MichaelBot's money is related to real money (including crypto currency).

If you receive such trade, report and do not trade. Accepting the trade is a blacklistable on both parties. You will also receive no support for such trade.
