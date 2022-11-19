# Action Commands

Action commands in economy refers to the command `mine`, `explore`, and `chop` as a whole. These are the 3 main ways to interact with the economy as they're the only reliable way to get more resources.

## Action requirement

To use any of the action commands, you need the corresponding tool for an action. In particular, `mine` requires a pickaxe to be equipped, `explore` requires a sword to be equipped, and `chop` requires an axe to be equipped. You don't need to equip all 3 equipments to use the command; you only need the one that's required for the action you're intending to perform.

## Tools

A tool is a special item that can be equipped. This includes pickaxes, swords, axes, and potions (there are some other items that are internally treated as a tool, feel free to find out). For further info on potions, view [this page](potions.md). The rest of this page will apply to only pickaxes, swords, and axes.

To equip a tool, use `use tool <tool name>`. By default, a user can only equip one of each type of tool (up to 1 pickaxe, 1 sword, and 1 axe can be equipped simultaneously). If you try to equip a new tool into a preoccupied slot, these things will happen:

- If the old tool at the slot is craftable, it'll be destroyed and return x% of the original crafting recipe rounded down, where x% is determined by the old tool `remaining durability / original durability`. Consequentially, if the old tool is not craftable, it'll simply be destroyed.
- The new tool is equipped.

Note that this will happen regardless of the rank of the tool. Equipping a wood pickaxe while you already have a netherite pickaxe will have...some considerable consequences.

## Locations

Once you have your tools ready, the next part is challenging. Locations for action commands are added fairly recently, so it might be a bit confusing. Basically, each locations have their own loot table. The cool thing about this is some locations are good for finding certain resources, so you'll need to go around and try it all out. Do note that some locations are located in certain worlds, so you'll need to travel around if you want to access more locations.

Be mindful however, the more loot a location give, the more damage it'll deal (to read more about damage, view [this](death.md)). In slash commands, the locations are sorted based on the max damage of the location. With insufficient tools, some locations can potentially one-hit you, so do check your equipments carefully.

## Using action commands

The syntax for `mine` is `mine <location>`, where `location` is given to you as choices in slash commands. The same syntax also applies to `explore` and `chop`.
