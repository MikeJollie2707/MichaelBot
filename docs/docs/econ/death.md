# Damage Mechanism

The damage mechanism can be beneficial if you know what's going on in order to avoid damage lost and eventually, death. You can always check out `categories/economy.py` for more technical details.

Also note that the damage mechanism only happens to action commands (`mine`, `explore`, `chop`).

## Brief

Overall, the bot will use the loot table generated from each action command to determine the **maximum damage** you'll receive. After a few processing, the actual damage you'll be taking (or **final damage**) will be a random value in the range of `[max_dmg / 2, max_dmg]`. Thus, the damage mentioned for the rest of the page will refer to **max damage**, unless stated otherwise.

## Reward Value

After a loot table is generated for action commands (before multipliers and rerolls start to apply), the bot will calculate this loot table's value. The reward value is simply a sum of `item's sell price * amount`. This value will then be used to determine the max damage. The higher the value, the higher the max damage. The exact formula for converting reward value to death chance can be found in `get_dmg_taken()` in `categories/economy.py`.

## Damage Multipliers

After the max damage is calculated, a random multiplier is used to multiply with this max damage, resulting in a new max damage.

Currently, two possible multipliers in the Overworld is `1` and `1.5`, with `1` having a 2/3 chance of being chosen. In the Nether, the possible multipliers are `1`, `1.5`, and `2`, with `2/5`, `2/5`, `1/5` chance of being chosen respectively.

After the multiplier is chosen, the new max damage will be the result of the old max damage times this multiplier (with normal rounding).

### Damage Cap

Damage Cap is a number that limits your max damage. The purpose of this is to control how often can you die in a dimension. It's also used to control how high a damage can be dealt before it becomes terribly high out of control. This is applied right after applying the multipliers.

Currently, the damage cap in Overworld is `50` and in Nether is `100`.

For example, if the reward value is like `1000`, which makes the damage super high, this step will then cap the damage to the values defined above.

### Damage Reductions

Damage Reductions further lower the damage. **This is applied after capping the damage.** Basically the bot will check for your relevant equipments and any relevant boosts you have that lower the damage and apply directly. For example, a diamond pickaxe has a damage reduction of 25, so it'll take the current damage and subtract 25 out of that. This will be applied continuously until it goes through all the reductions. However, no matter how many reductions you apply, *the max damage can't be lower than 2*.

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

- Wood tools: 50
- Stone tools: 50
- Iron sword + axe: 20
- Iron pickaxe: 15
- Diamond tools: 25
- Netherite tools: 25
- Fire Potion: 2
- Haste Potion: 2 when mining and chopping
- Strength Potion: 2 when exploring
- Fortune Potion: 5 when mining
- Looting Potion: 5 when exploring
- Nature Potion: 5 when chopping
- Luck Potion: 10
- `Staph Dying!` badge: 3 per equipment (including potions)
- `Kasaneru IF` badge: 2 per equipment (including potions)

Note that for tools, reduction only applies to the corresponding action. For example, if you have a diamond pickaxe and an iron sword, then when mining, you'll have the 25 reductions, while when you're exploring, you'll have the 20 reductions.

The reason behind such huge numbers behind wood and stone tools is to lower the damage for new users, or as MikeJollie likes to say, "beginners' spawn protection".

## Death Penalty

If you don't monitor your health and let it drop to 0 or below, you dies. These are the consequences of death:

- Losing all equipments with few exceptions.
- Losing all potions.
- Losing 20% of current balance (rounded up).
- Losing 5% (2% if `How are you still sane?` badge is acquired) of all items in inventory (rounded up).
- If the user is in a different world, they'll be forced to be in the Overworld, with a few exceptions. *This won't update the cooldown in `travel`*.
- Health reset back to 100.

Out of all of these, losing all potions and 5% of all items in inventory are arguably the worst, so don't die :)
