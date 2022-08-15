# Death Mechanism

The death mechanism is somewhat punishing for the beginners, but it'll strike harder for non-beginners if they don't understand a thing. This page will attempt to explain the death mechanism in MichaelBot in a simple way. You can always check out `categories/economy.py` for more technical details.

Also note that the death mechanism only happens to action commands (`mine`, `explore`, `chop`).

## Implementation of Probability

Probability in MichaelBot is very easily implemented. Normally, when you say "there's a 15% you'll die on the next action command", MichaelBot implement this as (note that I don't study too deep into probability, so I might get a few terms wrong):

- Set `0.15` (15 / 100 = 0.15) as the probability.
- Generate a random decimal number between `0` and `1` (inclusive).
- If this number is smaller or equal to `0.15`, the bot says that this number hits, and you'll die. Otherwise, this number misses, and you won't die.

In this page, I'll often refer the second step as **RNG** (random number generator). Understand this might make the later sections easier to understand.

## Death Chance

Death chance (or death rate) is calculated based on the value of the reward you'll get. The value in this case is basically the sell prices of all items time the amount of each items. **This is calculated before any multipliers are applied.** For example, if you have an x2 reward multiplier, this will be applied *after* the death chance is calculated, so you won't have double the death chance. *Luck Potion's main effect, however, will be applied before calculating death chance.* The number after this step is referred to as **raw death chance** (death chance that has not been processed).

### Death Cap

Death Chance Cap, or Death Cap, is a number that limits the upper bound of your death chance. The purpose of this is to prevent you from dying all the time. Without this, you can reach 50% or even 100% death chance, giving you a very terrible experience.

Currently, the death cap for Overworld is 15% (`0.15`) and for Nether is 30% (`0.30`).

The exact formula for converting reward value to death chance can be found in `get_death_rate()` in `categories/economy.py`, but basically, at around a value of `100` (= 100 money), the death chance would be around `0.15`, which is the cap of the Overworld. This death chance will then be capped by the Death Cap. For example, if the reward value is like `1000`, which makes the death chance super high, this step will then cap the death chance to the values defined above.

### Death Reductions

Death Rate Reductions, or Death Reductions, further lower the death chance. **This is applied after capping the death chance.** Basically the bot will check for your relevant equipments and any relevant boosts you have that lower the death chance and apply directly to this chance. For example, a diamond tool has a death reduction of 5%, so it'll take the current death chance **and subtract 5% out of that (not multiply 95%).** This will be applied continuously until it goes through all the reductions. Finally, it'll return a non-negative death chance. **From `0.1.16` (and its development version `0.1.16dev`) onward, the minimum death chance is `0.005` (or 0.5%), even after applying all death reductions.** This value was `0` prior to this update. This final value is your **death chance**.

Example:

- You have a diamond pickaxe, so you're having a 5% reductions.
- You also have a strength potion equipped, so you have another 8% reductions.
- You mine something and get a raw death chance of 21%.
- You're mining in the Overworld, so the bot caps your death chance to 15%.
- Now the bot applies reductions. You have 5% + 8% = 13% reductions. Thus, you'll have 15% - 13% = 2% death chance.
- Since this is larger than 0.5%, 2% will be your death chance.

#### Available Reductions

These are the current reductions:

- Wood tools: 15%
- Stone tools: 15%
- Iron tools: 1%
- Diamond tools: 5%
- Netherite tools: 10%
- Fire Potion: 2%
- Fortune Potion: 2% when mining
- Looting Potion: 2% when exploring
- Nature Potion: 2% when chopping
- Strength Potion: 8%
- Luck Potion: 10%
- Undying Potion: ?% (not decided)

Note that for `x tools`, this means that the percent only applies to the corresponding action. For example, if you have a diamond pickaxe and an iron sword, then when mining, you'll have the 5% reductions, while when you're exploring, you'll have the 1% reductions.

The reason behind such huge numbers behind wood and stone tools is to completely remove death from the player while in the Overworld, or as MikeJollie likes to say, "beginners' spawn protection". However, as of `0.1.16`, this is no longer the case.

## Death Penalty

When the RNG is bad enough to hit the death chance, the user will dies. The penalty of dying are:

- Losing all equipments with few exceptions.
- Losing all potions.
- Losing 20% of current balance (rounded up).
- Losing 5% of all items in inventory (rounded up).
- If the user is in a different world, they'll be forced to be in the Overworld, with a few exceptions. *This won't update the cooldown in `travel`*.

Out of all of these, losing all potions and 5% of all items in inventory are arguably the worst, so don't die :)
