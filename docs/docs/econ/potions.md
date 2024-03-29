# Potions

Potions can be seen as special equipments. They're internally treated as equipments, yet are slightly different from equipments. Potions are essential in midgame and especially endgame. However, they're often very expensive, so you'd need to do some planning before using them.

A user can equip at most 3 different kinds of potions at once, and you can only equip at most 1 of the same kind of potions at once. Potions are created to mainly support action commands (`mine`, `explore`, `chop`), so keep this in mind. This may change in the future.

All potions have their own effects that might stack with other potions' effects. These are often referred to as their **main effect**. However, these effects often has a *chance* to activate. When a potion activates, it'll apply its main effect and lose 1 durability, just like when you use an equipment. When it doesn't, nothing happens.

In addition to their main effects, potions often have their **passive effects**. These are effects that always activate and doesn't consume any durability nor chance. These are often death reductions.

All potions will be cleared when you die, so you have to plan carefully with your death chance.

Potions can be obtained via **brewing**, which is just crafting but for potions. You'll need a lot of items along with some money, then use `brew <potion>`. Currently, each brew will give you 3 potions, but this can be increased via [badges](badges.md).

This document will briefly describe all current potions in more details. It won't list the brew recipe because this can be easily checked via `info item`. All of the info here can be verified in the source code in `categories/economy.py` and `categories/econ/loot.py` if you have trust issues with me.

## Fire Potion

The easiest potion to obtain. You can grab it in `market` with a price of 1500 alternatively besides the standard brewing system.

- **Main Effect:** When the user dies in the Nether, there is a 100% chance this potion will activate, negating the death of the user. 
- **Passive Effect:** Lower the maximum damage by 2 on all dimensions.
- **Durability:** 10

This is a more lazy option if you're tight on food, so you decide whether or not to invest in this potion. Just to note, if you enter the Nether with low gear (which you shouldn't anyway), you should get this because the Nether will most likely one-hit you in some locations.

## Haste Potion

- **Main Effect:** A 50% chance to roll the drop 7 times and get all of them while mining and chopping.
- **Passive Effect:** Lower the maximum damage by 2 while mining.
- **Durability:** 20

Note that because it says "roll", you don't necessarily get x7 rewards, but your probability of getting an item is theoretically x7.

## Fortune Potion

- **Main Effect:** A 50% chance to multiply the drop by 4 times while mining.
- **Passive Effect:** Lower the maximum damage by 5 while mining.
- **Durability:** 20

## Nature Potion

- **Main Effect:** A 50% chance to multiply the drop by 4 times while chopping.
- **Passive Effect:** Lower the maximum damage by 5 while chopping.
- **Durability:** 20

## Strength Potion

- **Main Effect:** A 50% chance to roll the drop 7 times and get all of them while exploring.
- **Passive Effect:** Lower the maximum damage by 2 while exploring.
- **Durability:** 20

Note that because it says "roll", you don't necessarily get x7 rewards, but your probability of getting an item is theoretically x7.

## Looting Potion

- **Main Effect:** A 50% chance to multiply the drop by 5 times while exploring.
- **Passive Effect:** Lower the maximum damage by 5 while exploring.
- **Durability:** 20

## Luck Potion

- **Main Effect:** A 65% chance to multiplies the drop by 3 times (rounded up). Also ensure that 1. If a possible drop is already dropped, it'll then drop `max_amount` and 2. If a possible drop is not dropped, it'll then drop `min_amount`.
- **Passive Effect:** Lower the maximum damage by 10 on all dimensions. As a `Legendary` equipment, this cannot be lost upon death while equipped.
- **Durability:** 50

This is a powerful potion that basically removes the rate in which most items drop. It'd be basically 50%, completely based on whether the potion activates or not. However, note that there's a chance an item won't be dropped if its `min_amount` is 0.

## Undying Potion

- **Main Effect:** When the user receives a lethal damage or a damage over 60, there is a 100% chance this potion will activate, negating the said damage to the user. If `Fire Potion` is activated, `Fire Potion` will be prioritized over this potion.
- **Passive Effect:** While equipped, this potion will allow the user to equip 1 more potion. As a `Legendary` equipment, this cannot be lost upon death while equipped.
- **Durability:** 20

This is an extremely useful potion that guarantees you to not die, while essentially costing you no potion slot. It also renders some locations no longer dangerous, since most of the damage dealt by those location are typically well over 60. Definitely useful to get.
