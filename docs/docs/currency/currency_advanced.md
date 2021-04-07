# Currency 104

## Potions

Potions are rich people's playground. It enhances the effectiveness of activities. You can not "craft" potions however, you *brew* them. The command `brew` is like the `craft` command, but exclusively for potions. Thus, you can check the ingredient by `brew recipe` subcommand.

Potions are similar to tools, in the sense that they have durability and can be viewed with `equipments`. To use a potion, `usepotion`. A potion has *stacks*. Some potions' effectiveness increase as the stacks increase. The max stack for any potions is 10. Stacks are calculated as `current durability / potion's base durability` rounded up.

Potions also have a chance to activate. Usually it is 50%, but the exact number varies between potions.
