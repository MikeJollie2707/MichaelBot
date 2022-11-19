# Economy System

MichaelBot has its own economy system that's heavily inspired by Minecraft. This document is written to serve a brief intro to this system, as it can be confusing where to start.

## Guide

Currently, the only valid way to get started is to use the command `daily`. This will gives you a pre-determined amount of money (or emerald) and some woods.

Next, you'll need to *craft* some items to move on. Like Minecraft, you usually first craft some sticks, then a wooden pickaxe to mine stone, then craft stone tools, etc. The process follows somewhat similarly using the command `craft`. It's recommended to use the slash command version, since it gives a list of items you can craft as you type.

```
/craft Stick
/craft Wood Pickaxe
```

Note that for prefix commands, some items' name need to be enclosed inside `""` like `"Wood Pickaxe"`. This is not a problem for slash commands.

A pickaxe (in this case, the `Wood Pickaxe`) is considered to be an equipment, a subset of items that can be equipped and used. Other equipment can include a sword, axe, and [potion](potions.md). To use certain equipments, you'll need to equip them using `use`. Sword, pickaxe, and axe are considered as *tools*, while potions are on their own.

```
/use tool Wood Pickaxe
```

Now that you have your wooden pickaxe equipped, time to go [mining](action.md).

```
/mine 5 (Overworld)
```

These are considered to be [*action commands*](action.md). These need certain equipments to be equipped before performing the action. In this case, `mine` requires a pickaxe equipped before using it, otherwise, it'll send an error.

After the mining, you'll have some stone. Use them to craft more tools like in Minecraft. At this point, the progression is similar to Minecraft, so you should be able to progress. If not, feel free to explore what the system can do.
