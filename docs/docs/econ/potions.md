# Potions

Potions can be seen as special equipments. They're internally treated as equipments, yet are slightly different from equipments. Potions are essential in midgame and especially endgame. However, they're often very expensive, so you'd need to do some planning before using them.

A user can equip at most 3 different kinds of potions at once, and you can only equip at most 1 of the same kind of potions at once. Potions are created to mainly support action commands (`mine`, `explore`, `chop`), so keep this in mind. This may change in the future.

All potions have their own effects that might stack with other potions' effects. These are often referred to as their **main effect**. However, these effects often has a *chance* to activate. When a potion activates, it'll apply its main effect and lose 1 durability, just like when you use an equipment. When it doesn't, nothing happens.

In addition to their main effects, potions often have their **passive effects**. These are effects that always activate and doesn't consume any durability nor chance. These are often death reductions.

All potions will be cleared when you die, so you have to plan carefully with your death chance.

Potions can be obtained via **brewing**, which is just crafting but for potions. You'll need a lot of items along with some money, then use `brew <potion>`. Currently, each brew will give you 3 potions.

This document will briefly describe all current potions in more details. It won't list the brew recipe because this can be easily checked via `info item`. All of the info here can be verified in the source code in `categories/economy.py` and `categories/econ/loot.py` if you have trust issues with me.

## Fire Potion

The easiest potion to obtain. You can grab it in `market` with a price of 1500 as an alternate way besides the standard brewing system.

- **Main Effect:** When the user "dies" the Nether, there is a 70% chance this potion will activate, negating the death of the user. 
- **Passive Effect:** Lower the death chance by 2% on all dimensions.
- **Durability:** 10

Basically, after applying the passive 2% reduction, this lower your death rate by 70%. This is very good when you just enter Nether for the first few times.

## Haste Potion

- **Main Effect:** A 50% chance to roll the drop 5 times and get all of them while mining and chopping.
- **Passive Effect:** Lower the death chance by 2% while mining.
- **Durability:** 20

Note that because it says "roll", you don't necessarily get x5 rewards, but your probability of getting an item is theoretically x5.

## Fortune Potion

- **Main Effect:** A 50% chance to multiply the drop by 4 times while mining.
- **Passive Effect:** Lower the death chance by 5% while mining.
- **Durability:** 20

## Nature Potion

- **Main Effect:** A 50% chance to multiply the drop by 4 times while chopping.
- **Passive Effect:** Lower the death chance by 5% while chopping.
- **Durability:** 20

## Strength Potion

- **Main Effect:** A 50% chance to roll the drop 5 times and get all of them while exploring.
- **Passive Effect:** Lower the death chance by 2% while exploring.
- **Durability:** 20

Note that because it says "roll", you don't necessarily get x5 rewards, but your probability of getting an item is theoretically x5.

## Looting Potion

- **Main Effect:** A 50% chance to multiply the drop by 4 times while exploring.
- **Passive Effect:** Lower the death chance by 5% while exploring.
- **Durability:** 20

## Luck Potion

- **Main Effect:** A 50% chance to multiplies the drop by 2 times. Also ensure that 1. If a possible drop is already dropped, it'll then drop `max_amount` and 2. If a possible drop is not dropped, it'll then drop `min_amount` or 1, whichever is higher.
- **Passive Effect:** Lower the death chance by 10% on all dimensions. As a `Legendary` equipment, this cannot be lost upon death while equipped.
- **Durability:** 50

This is a powerful potion that basically removes the rate in which an item drops. It'd be basically 50%, completely based on whether the potion activates or not. However, this does contribute to the death chance calculation. The 10% death reductions should absolutely offset this.

## Undying Potion

- **Main Effect:** When the user "dies", there is a 100% chance this potion will activate, negating the death of the user. If `Fire Potion` is activated, `Fire Potion` will be prioritized over this potion.
- **Passive Effect:** While equipped, this potion will allow the user to equip 1 more potion.
- **Durability:** 20

This is a useful potion that guarantees you to not die, while essentially costing you no potion slot. Definitely useful to get.
