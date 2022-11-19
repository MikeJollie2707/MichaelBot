# Damage Mechanism

The damage mechanism can be beneficial if you know what's going on in order to avoid damage lost and eventually, death. You can always check out `categories/economy.py` for more technical details.

Also note that the damage mechanism only happens to action commands (`mine`, `explore`, `chop`).

## Brief

Overall, the bot will use the loot table generated from each action command to determine the **maximum damage** you'll receive. After a few processing, the actual damage you'll be taking (or **final damage**) will be a random value in the range of `[max_dmg / 2, max_dmg]`. Thus, the damage mentioned for the rest of the page will refer to **max damage**, unless stated otherwise.

## Reward Value

When a loot table is generated for action commands (before multipliers and rerolls start to apply), the bot also generate the max damage for this action. These are manually defined, but generally, the better the reward, the higher the damage. The exact values can be found in `categories/econ/loot.py`, under the `__<ACTION>_LOOT` variable.

### Damage Reductions

Damage Reductions further lower the damage. Basically the bot will check for your relevant equipments and any relevant boosts you have that lower the damage and apply directly. For example, a diamond pickaxe has a damage reduction of 25, so it'll take the current damage and subtract 25 out of that. This will be applied continuously until it goes through all the reductions. However, no matter how many reductions you apply, *the max damage can't be lower than 2*.

Finally, your **final damage** will be determined by a random number between `[floor(dmg / 2) - 1, dmg]`, where `dmg` is the max damage. This is to ensure there are varieties in the final damage.

Example:

- You have a diamond pickaxe, so you're having a 25 damage reductions.
- You also have a strength potion equipped, so you have another 2 damage reductions.
- You mine something and get a raw damage of 60.
- You're mining in the Overworld, so the bot caps your damage to 50.
- Now the bot applies reductions. You have 25 + 2 = 27 reductions. Thus, you'll at most receive 50 - 27 = 23 damage.
- Your final damage (the damage you're actually taking) will be a random number between `[floor(23 / 2) - 1, 23]`, which is `[10, 23]`.

#### Available Reductions

All damage reductions can be found in `categories/econ/loot.py`, defined by the `DMG_REDUCTIONS` variable.

- Wood tools: 0
- Stone tools: 10
- Iron sword + axe: 20
- Iron pickaxe: 15
- Diamond tools: 25
- Netherite tools: 25
- Star tools: 30
- Fire Potion: 2
- Haste Potion: 2 when mining and chopping
- Strength Potion: 2 when exploring
- Fortune Potion: 5 when mining
- Looting Potion: 5 when exploring
- Nature Potion: 5 when chopping
- Luck Potion: 10
- `Staph Dying!` badge: 2 per equipment (including potions)
- `Kasaneru IF` badge: 3 per equipment (including potions)

Note that for tools, reduction only applies to the corresponding action. For example, if you have a diamond pickaxe and an iron sword, then when mining, you'll have the 25 reductions, while when you're exploring, you'll have the 20 reductions.

## Death Penalty

If you don't monitor your health and let it drop to 0 or below, you dies. These are the consequences of death:

- Losing all equipments with few exceptions.
- Losing all potions.
- Losing 20% of current balance (rounded up).
- Losing 5% of all items in inventory (rounded up).
    - If the user is in the `End`, this will be 95% of the inventory rounded down.
    - If you have `How are you still sane?` badge, this penalty is halved.
- If the user is in a different world, they'll be forced to be in the Overworld, with a few exceptions. *This won't update the cooldown in `travel`*.
- Health reset back to 100.

Out of all of these, losing all potions and 5% of all items in inventory are arguably the worst, so don't die :)
