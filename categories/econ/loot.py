'''Define the loot tables for the economy system and a bunch of constants.'''

import copy
import random
import typing as t

# Define dict keys that are special and not considered as "item".
# A few special keywords that are reserved in the loot tables:
# - "result": Usually in crafting-related stuff, it defines how many items will end up as the result of the craft.
# - "money": The money as a reward.
# - "bonus": Same as "money", just different message.
# - "cost": The money lost.
# - "raw_damage": The raw damage of an action. Used in action commands.
RESERVED_KEYS = (
    "result",
    "money",
    "bonus",
    "cost",
    "raw_damage"
)

# Define items that will not be multiplied by `multiply_reward()`, which also prevent them from being affected by multiplying potions.
PREVENT_MULTIPLY = (
    "shulker_box",
    "streak_freezer",
)

# Define items that will not be removed upon death.
NON_REMOVABLE_ON_DEATH = (
    "shulker_box",
    "streak_freezer",
)

# Define how many potions can be equipped by default.
POTIONS_CAP = 3

# Define how many shulker slot to be counted. This doesn't mean the user can't own more shulker boxes, it just extra shulker boxes won't count towards extra slots.
MAX_SHULKER_EFFECT = 27

# Define the base maximum amount of items per slot can the extra slot hold. For each shulker that exceed MAX_SHULKER_EFFECT, a SAFE_SLOT_PER_EXTRA_SHULKER multiplier will add towards the total items.
MAX_SAFE_SPACE_BASE = 50
SAFE_SPACE_PER_EXTRA_SHULKER = 10

# Define how often sudden death will trigger and kill the user regardless of their common damage reduction.
SUDDEN_DEATH_CHANCE = 0.0025
SUDDEN_DEATH_MESSAGES = (
    "You fell from y 319 all the way to y -64. Not even water can save you.\n",
    "A mysterious force decided to kill you out of nowhere. Talk about deus ex machina.\n",
    "You just got /kill. Too bad!\n",
    "You got killed by crappy isekai writing. Apparently, you're not the main character of the story.\n",
    "You saw a Warden and realized the bot doesn't have anything called Armor.\n",
    "You were killed by [Intentional Bot Design]\n",
)

# Define the maximum healing effect of a food item. This also define what item is considered as food.
FOOD_HEALING = {
    "mushroom": 10,
    "apple": 10,
    "orange": 10,
    "cherries": 8,
    "carrot": 14,
    "bacon": 17,
    "meat": 20,
    "chicken": 20,
    "gold_apple": 60,
}

# Define the damage reduction for each item.
DMG_REDUCTIONS = {
    # Tools
    "wood_pickaxe": 0,
    
    "stone_sword": 10,
    "stone_pickaxe": 10,
    "stone_axe": 10,
    
    "iron_sword": 20,
    "iron_pickaxe": 15,
    "iron_axe": 20,

    "diamond_sword": 25,
    "diamond_pickaxe": 25,
    "diamond_axe": 25,

    "nether_sword": 25,
    "nether_pickaxe": 25,
    "nether_axe": 25,

    "fragile_star_pickaxe": 30,
    "fragile_star_sword": 30,
    "fragile_star_axe": 30,

    # Badges
    "death1": 2,
    "death3": 3,

    # Potions
    "luck_potion": 10,
    "fire_potion": 2,
    "haste_potion": 2,
    "fortune_potion": 5,
    "nature_potion": 5,
    "strength_potion": 2,
    "looting_potion": 5,
    "undying_potion": 0,
}

class RewardRNG:
    '''Define the RNG to randomize.

    This emulate 2 RNGs. The first RNG will determine whether or not to roll the second RNG.
    The second RNG will generate a number between the defined range, with a custom RNG behavior
    taken into account.

    Attributes
    ----------
    rate : float
        Define the rate at which the second RNG will roll. Must be between 0 and 1.
    min_amount : int
        Define the minimum number for the second RNG. This should be positive.
    max_amount : int
        Define the maximum number for the second RNG. This should be positive.
    amount_layout : tuple[int], optional
        Define the rng distribution between `min_amount` and `max_amount`. This must satisfy `len(amount_layout) == (max_amount - min_amount + 1) and sum(amount_layout) == 100`
    '''
    __slots__ = ("rate", "min_amount", "max_amount", "amount_layout")

    def __init__(self, rate: float, min_amount: int, max_amount: int, *, amount_layout: tuple[int] = None):
        if rate < 0 or rate > 1:
            raise ValueError("'rate' must be in [0, 1].")
        if min_amount > max_amount:
            raise ValueError("'min_amount' must be smaller than or equal to 'max_amount'.")
        if amount_layout:
            if len(amount_layout) != (max_amount - min_amount + 1):
                raise ValueError("'amount_layout' must have the same amount of items as (max_amount - min_amount + 1).")
            if sum(amount_layout) != 100:
                print(sum(amount_layout))
                raise ValueError("'amount_layout' must sum up to 100.")

        self.rate = rate
        self.min_amount = min_amount
        self.max_amount = max_amount
        self.amount_layout = amount_layout

    def shift_min_amount(self, amount: int):
        self.min_amount += amount
        self.max_amount += amount

    def roll(self) -> int:
        '''Roll the RNG based on the provided information.

        Returns
        -------
        int
            The number after randomizing.
        '''
        
        if self.rate < 1:
            r = random.random()
            if r > self.rate:
                return 0
            
        if self.min_amount == self.max_amount:
            return self.min_amount
        
        if not self.amount_layout:
            return random.choice(range(self.min_amount, self.max_amount + 1))
        
        r = random.random()
        rate = 0
        for index, amount_rate in enumerate(self.amount_layout):
            rate += amount_rate / 100.0
            if r <= rate:
                return min(self.min_amount + index, self.max_amount)
        
        return self.max_amount

# Define the loot generated for a mining session in each location.
# The amount of loot is set to an RNG, which will then be rolled when calling `get_activity_loot()`.
# It is REQUIRED to provide the key "raw_damage" for each tool (even if it deals 0 damage!)
__MINE_LOOT = {
    "5 (Overworld)": {
        "wood_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 0.05, min_amount = 0, max_amount = 1),
        },
        "stone_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 3, max_amount = 5),
            "iron": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 2, amount_layout = (75, 25)),
            "raw_damage": RewardRNG(rate = 0.05, min_amount = 0, max_amount = 1),
        },
        "iron_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 5, max_amount = 7),
            "iron": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 3, amount_layout = (50, 30, 20)),
            "raw_damage": RewardRNG(rate = 0.05, min_amount = 0, max_amount = 1),
        },
        "diamond_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 8, max_amount = 11),
            "iron": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 3, amount_layout = (50, 30, 20)),
            "raw_damage": RewardRNG(rate = 0.05, min_amount = 0, max_amount = 1),
        },
        "nether_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 9, max_amount = 12),
            "iron": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 3),
            "raw_damage": RewardRNG(rate = 0.05, min_amount = 0, max_amount = 1),
        },
        "fragile_star_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 11, max_amount = 14),
            "iron": RewardRNG(rate = 0.3, min_amount = 1, max_amount = 4),
            "raw_damage": RewardRNG(rate = 0.05, min_amount = 0, max_amount = 1),
        },
    },
    "4 (Overworld)": {
        "wood_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 10, max_amount = 20),
        },
        "stone_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 3, max_amount = 5),
            "iron": RewardRNG(rate = 0.5, min_amount = 2, max_amount = 3),
            "raw_damage": RewardRNG(rate = 1, min_amount = 10, max_amount = 20),
        },
        "iron_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 5, max_amount = 7),
            "iron": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 5),
            "diamond": RewardRNG(rate = 0.01, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 10, max_amount = 20),
        },
        "diamond_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 8, max_amount = 11),
            "iron": RewardRNG(rate = 0.5, min_amount = 2, max_amount = 6, amount_layout = (40, 40, 10, 5, 5)),
            "diamond": RewardRNG(rate = 0.01, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 10, max_amount = 20),
        },
        "nether_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 8, max_amount = 11),
            "iron": RewardRNG(rate = 0.5, min_amount = 2, max_amount = 6),
            "diamond": RewardRNG(rate = 0.01, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 10, max_amount = 20),
        },
        "fragile_star_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 10, max_amount = 13),
            "iron": RewardRNG(rate = 0.75, min_amount = 2, max_amount = 7),
            "diamond": RewardRNG(rate = 0.015, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 10, max_amount = 20),
        },
    },
    "3 (Overworld)": {
        "wood_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 15, max_amount = 30),
        },
        "stone_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 3, max_amount = 5),
            "iron": RewardRNG(rate = 0.3, min_amount = 2, max_amount = 3),
            "raw_damage": RewardRNG(rate = 1, min_amount = 15, max_amount = 30),
        },
        "iron_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 5, max_amount = 7),
            "iron": RewardRNG(rate = 0.3, min_amount = 1, max_amount = 5),
            "diamond": RewardRNG(rate = 0.05, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 15, max_amount = 30),
        },
        "diamond_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 8, max_amount = 11),
            "iron": RewardRNG(rate = 0.3, min_amount = 2, max_amount = 6, amount_layout = (40, 40, 10, 5, 5)),
            "diamond": RewardRNG(rate = 0.05, min_amount = 1, max_amount = 1),
            "obsidian": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 15, max_amount = 30),
        },
        "nether_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 8, max_amount = 11),
            "iron": RewardRNG(rate = 0.3, min_amount = 2, max_amount = 6),
            "diamond": RewardRNG(rate = 0.05, min_amount = 1, max_amount = 2),
            "obsidian": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 15, max_amount = 30),
        },
        "fragile_star_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 10, max_amount = 13),
            "iron": RewardRNG(rate = 0.45, min_amount = 2, max_amount = 7),
            "diamond": RewardRNG(rate = 0.075, min_amount = 1, max_amount = 2),
            "obsidian": RewardRNG(rate = 0.3, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 15, max_amount = 30),
        },
    },
    "2 (Overworld)": {
        "wood_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 25, max_amount = 40),
        },
        "stone_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 3, max_amount = 5),
            "iron": RewardRNG(rate = 0.2, min_amount = 2, max_amount = 3),
            "raw_damage": RewardRNG(rate = 1, min_amount = 25, max_amount = 40),
        },
        "iron_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 5, max_amount = 7),
            "iron": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 5),
            "diamond": RewardRNG(rate = 0.1, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 25, max_amount = 40),
        },
        "diamond_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 8, max_amount = 11),
            "iron": RewardRNG(rate = 0.2, min_amount = 2, max_amount = 6, amount_layout = (40, 40, 10, 5, 5)),
            "diamond": RewardRNG(rate = 0.1, min_amount = 1, max_amount = 3),
            "obsidian": RewardRNG(rate = 0.3, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 25, max_amount = 40),
        },
        "nether_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 8, max_amount = 11),
            "iron": RewardRNG(rate = 0.2, min_amount = 2, max_amount = 6),
            "diamond": RewardRNG(rate = 0.1, min_amount = 1, max_amount = 3),
            "obsidian": RewardRNG(rate = 0.3, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 25, max_amount = 40),
        },
        "fragile_star_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 10, max_amount = 13),
            "iron": RewardRNG(rate = 0.3, min_amount = 2, max_amount = 7),
            "diamond": RewardRNG(rate = 0.15, min_amount = 1, max_amount = 4),
            "obsidian": RewardRNG(rate = 0.45, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 25, max_amount = 40),
        },
    },
    "1 (Overworld)": {
        "wood_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 30, max_amount = 60),
        },
        "stone_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 3, max_amount = 5),
            "iron": RewardRNG(rate = 0.2, min_amount = 2, max_amount = 3),
            "raw_damage": RewardRNG(rate = 1, min_amount = 30, max_amount = 60),
        },
        "iron_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 5, max_amount = 7),
            "iron": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 5),
            "diamond": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 30, max_amount = 60),
        },
        "diamond_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 8, max_amount = 11),
            "iron": RewardRNG(rate = 0.2, min_amount = 2, max_amount = 6, amount_layout = (40, 40, 10, 5, 5)),
            "diamond": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 3),
            "obsidian": RewardRNG(rate = 0.3, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 30, max_amount = 60),
        },
        "nether_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 8, max_amount = 11),
            "iron": RewardRNG(rate = 0.2, min_amount = 2, max_amount = 6),
            "diamond": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 3),
            "obsidian": RewardRNG(rate = 0.3, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 30, max_amount = 60),
        },
        "fragile_star_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 10, max_amount = 13),
            "iron": RewardRNG(rate = 0.3, min_amount = 2, max_amount = 7),
            "diamond": RewardRNG(rate = 0.3, min_amount = 1, max_amount = 4),
            "obsidian": RewardRNG(rate = 0.45, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 30, max_amount = 60),
        },
    },
    
    "-1 (Nether)": {
        "wood_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 1, max_amount = 5),
            "stone": RewardRNG(rate = 0.25, min_amount = 1, max_amount = 2),
            "gold": RewardRNG(rate = 0.1, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 1, max_amount = 5),
        },
        "stone_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 4, max_amount = 7),
            "stone": RewardRNG(rate = 0.25, min_amount = 3, max_amount = 5),
            "gold": RewardRNG(rate = 0.1, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 1, max_amount = 5),
        },
        "iron_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 10, max_amount = 15),
            "stone": RewardRNG(rate = 0.25, min_amount = 5, max_amount = 7),
            "gold": RewardRNG(rate = 0.1, min_amount = 5, max_amount = 9),
            "raw_damage": RewardRNG(rate = 1, min_amount = 1, max_amount = 5),
        },
        "diamond_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 15, max_amount = 20),
            "stone": RewardRNG(rate = 0.25, min_amount = 5, max_amount = 7),
            "gold": RewardRNG(rate = 0.1, min_amount = 7, max_amount = 10),
            "obsidian": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 1),
            "debris": RewardRNG(rate = 0.005, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 1, max_amount = 20),
        },
        "nether_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 15, max_amount = 20),
            "stone": RewardRNG(rate = 0.25, min_amount = 5, max_amount = 7),
            "gold": RewardRNG(rate = 0.1, min_amount = 7, max_amount = 10),
            "obsidian": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 1),
            "debris": RewardRNG(rate = 0.005, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 1, max_amount = 20),
        },
        "bed_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 30, max_amount = 40),
            "stone": RewardRNG(rate = 0.25, min_amount = 10, max_amount = 14),
            "gold": RewardRNG(rate = 0.1, min_amount = 14, max_amount = 20),
            "debris": RewardRNG(rate = 0, min_amount = 0, max_amount = 0),
            "raw_damage": RewardRNG(rate = 1, min_amount = 1, max_amount = 30),
        },
        "fragile_star_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 18, max_amount = 24),
            "stone": RewardRNG(rate = 0.375, min_amount = 6, max_amount = 8),
            "gold": RewardRNG(rate = 0.15, min_amount = 8, max_amount = 12),
            "obsidian": RewardRNG(rate = 0.3, min_amount = 1, max_amount = 1),
            "debris": RewardRNG(rate = 0.0075, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 1, max_amount = 20),
        },
    },
    "-2 (Nether)": {
        "wood_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 1, max_amount = 5),
            "stone": RewardRNG(rate = 0.25, min_amount = 1, max_amount = 2),
            "gold": RewardRNG(rate = 0.4, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 10, max_amount = 25),
        },
        "stone_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 4, max_amount = 7),
            "stone": RewardRNG(rate = 0.25, min_amount = 3, max_amount = 5),
            "gold": RewardRNG(rate = 0.4, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 10, max_amount = 25),
        },
        "iron_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 10, max_amount = 15),
            "stone": RewardRNG(rate = 0.25, min_amount = 5, max_amount = 7),
            "gold": RewardRNG(rate = 0.4, min_amount = 5, max_amount = 9),
            "raw_damage": RewardRNG(rate = 1, min_amount = 10, max_amount = 25),
        },
        "diamond_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 15, max_amount = 20),
            "stone": RewardRNG(rate = 0.25, min_amount = 5, max_amount = 7),
            "gold": RewardRNG(rate = 0.4, min_amount = 7, max_amount = 10),
            "obsidian": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 1),
            "debris": RewardRNG(rate = 0.005, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 10, max_amount = 40),
        },
        "nether_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 15, max_amount = 20),
            "stone": RewardRNG(rate = 0.25, min_amount = 5, max_amount = 7),
            "gold": RewardRNG(rate = 0.4, min_amount = 7, max_amount = 10),
            "obsidian": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 1),
            "debris": RewardRNG(rate = 0.005, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 10, max_amount = 40),
        },
        "bed_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 30, max_amount = 40),
            "stone": RewardRNG(rate = 0.25, min_amount = 10, max_amount = 14),
            "gold": RewardRNG(rate = 0.4, min_amount = 14, max_amount = 20),
            "debris": RewardRNG(rate = 0.005, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 1, max_amount = 50),
        },
        "fragile_star_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 18, max_amount = 24),
            "stone": RewardRNG(rate = 0.375, min_amount = 6, max_amount = 8),
            "gold": RewardRNG(rate = 0.6, min_amount = 8, max_amount = 12),
            "obsidian": RewardRNG(rate = 0.3, min_amount = 1, max_amount = 1),
            "debris": RewardRNG(rate = 0.0075, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 10, max_amount = 40),
        },
    },
    "-3 (Nether)": {
        "wood_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 1, max_amount = 5),
            "stone": RewardRNG(rate = 0.25, min_amount = 1, max_amount = 2),
            "gold": RewardRNG(rate = 0.4, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 25, max_amount = 30),
        },
        "stone_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 4, max_amount = 7),
            "stone": RewardRNG(rate = 0.25, min_amount = 3, max_amount = 5),
            "gold": RewardRNG(rate = 0.4, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 25, max_amount = 30),
        },
        "iron_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 10, max_amount = 15),
            "stone": RewardRNG(rate = 0.25, min_amount = 5, max_amount = 7),
            "gold": RewardRNG(rate = 0.4, min_amount = 5, max_amount = 9),
            "raw_damage": RewardRNG(rate = 1, min_amount = 25, max_amount = 30),
        },
        "diamond_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 15, max_amount = 20),
            "stone": RewardRNG(rate = 0.25, min_amount = 5, max_amount = 7),
            "gold": RewardRNG(rate = 0.4, min_amount = 7, max_amount = 10),
            "obsidian": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 1),
            "debris": RewardRNG(rate = 0.01, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 20, max_amount = 65),
        },
        "nether_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 15, max_amount = 20),
            "stone": RewardRNG(rate = 0.25, min_amount = 5, max_amount = 7),
            "gold": RewardRNG(rate = 0.4, min_amount = 7, max_amount = 10),
            "obsidian": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 1),
            "debris": RewardRNG(rate = 0.01, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 20, max_amount = 65),
        },
        "bed_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 30, max_amount = 40),
            "stone": RewardRNG(rate = 0.25, min_amount = 10, max_amount = 14),
            "gold": RewardRNG(rate = 0.4, min_amount = 14, max_amount = 20),
            "debris": RewardRNG(rate = 0.01, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 1, max_amount = 100),
        },
        "fragile_star_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 18, max_amount = 24),
            "stone": RewardRNG(rate = 0.375, min_amount = 6, max_amount = 8),
            "gold": RewardRNG(rate = 0.6, min_amount = 8, max_amount = 12),
            "obsidian": RewardRNG(rate = 0.3, min_amount = 1, max_amount = 1),
            "debris": RewardRNG(rate = 0.015, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 20, max_amount = 65),
        },
    },
    "-4 (Nether)": {
        "wood_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 1, max_amount = 5),
            "stone": RewardRNG(rate = 0.25, min_amount = 1, max_amount = 2),
            "gold": RewardRNG(rate = 0.4, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 30, max_amount = 40),
        },
        "stone_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 4, max_amount = 7),
            "stone": RewardRNG(rate = 0.25, min_amount = 3, max_amount = 5),
            "gold": RewardRNG(rate = 0.4, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 30, max_amount = 40),
        },
        "iron_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 10, max_amount = 15),
            "stone": RewardRNG(rate = 0.25, min_amount = 5, max_amount = 7),
            "gold": RewardRNG(rate = 0.4, min_amount = 5, max_amount = 9),
            "raw_damage": RewardRNG(rate = 1, min_amount = 30, max_amount = 40),
        },
        "diamond_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 15, max_amount = 20),
            "stone": RewardRNG(rate = 0.25, min_amount = 5, max_amount = 7),
            "gold": RewardRNG(rate = 0.4, min_amount = 7, max_amount = 10),
            "obsidian": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 1),
            "debris": RewardRNG(rate = 0.05, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 25, max_amount = 75),
        },
        "nether_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 15, max_amount = 20),
            "stone": RewardRNG(rate = 0.25, min_amount = 5, max_amount = 7),
            "gold": RewardRNG(rate = 0.4, min_amount = 7, max_amount = 10),
            "obsidian": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 1),
            "debris": RewardRNG(rate = 0.05, min_amount = 1, max_amount = 3),
            "raw_damage": RewardRNG(rate = 1, min_amount = 25, max_amount = 75),
        },
        "bed_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 30, max_amount = 40),
            "stone": RewardRNG(rate = 0.25, min_amount = 10, max_amount = 14),
            "gold": RewardRNG(rate = 0.4, min_amount = 14, max_amount = 20),
            "debris": RewardRNG(rate = 0.05, min_amount = 1, max_amount = 4),
            "raw_damage": RewardRNG(rate = 1, min_amount = 1, max_amount = 100),
        },
        "fragile_star_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 18, max_amount = 24),
            "stone": RewardRNG(rate = 0.375, min_amount = 6, max_amount = 8),
            "gold": RewardRNG(rate = 0.6, min_amount = 8, max_amount = 12),
            "obsidian": RewardRNG(rate = 0.3, min_amount = 1, max_amount = 1),
            "debris": RewardRNG(rate = 0.075, min_amount = 1, max_amount = 3),
            "raw_damage": RewardRNG(rate = 1, min_amount = 25, max_amount = 75),
        }
    },
    "-5 (Nether)": {
        "wood_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 1, max_amount = 5),
            "stone": RewardRNG(rate = 0.25, min_amount = 1, max_amount = 2),
            "gold": RewardRNG(rate = 1, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 90, max_amount = 100),
        },
        "stone_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 4, max_amount = 7),
            "stone": RewardRNG(rate = 0.25, min_amount = 3, max_amount = 5),
            "gold": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 90, max_amount = 100),
        },
        "iron_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 10, max_amount = 15),
            "stone": RewardRNG(rate = 0.25, min_amount = 5, max_amount = 7),
            "gold": RewardRNG(rate = 1, min_amount = 5, max_amount = 9),
            "raw_damage": RewardRNG(rate = 1, min_amount = 40, max_amount = 60),
        },
        "diamond_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 15, max_amount = 20),
            "stone": RewardRNG(rate = 0.25, min_amount = 5, max_amount = 7),
            "gold": RewardRNG(rate = 1, min_amount = 7, max_amount = 10),
            "obsidian": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 1),
            "debris": RewardRNG(rate = 0.05, min_amount = 1, max_amount = 3),
            "raw_damage": RewardRNG(rate = 1, min_amount = 30, max_amount = 80),
        },
        "nether_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 15, max_amount = 20),
            "stone": RewardRNG(rate = 0.25, min_amount = 5, max_amount = 7),
            "gold": RewardRNG(rate = 1, min_amount = 7, max_amount = 10),
            "obsidian": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 1),
            "debris": RewardRNG(rate = 0.05, min_amount = 1, max_amount = 4),
            "raw_damage": RewardRNG(rate = 1, min_amount = 30, max_amount = 80),
        },
        "bed_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 30, max_amount = 40),
            "stone": RewardRNG(rate = 0.25, min_amount = 10, max_amount = 14),
            "gold": RewardRNG(rate = 1, min_amount = 14, max_amount = 20),
            "debris": RewardRNG(rate = 0.1, min_amount = 1, max_amount = 5),
            "raw_damage": RewardRNG(rate = 1, min_amount = 1, max_amount = 100),
        },
        "fragile_star_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 18, max_amount = 24),
            "stone": RewardRNG(rate = 0.375, min_amount = 6, max_amount = 8),
            "gold": RewardRNG(rate = 1, min_amount = 8, max_amount = 12),
            "obsidian": RewardRNG(rate = 0.3, min_amount = 1, max_amount = 1),
            "debris": RewardRNG(rate = 0.075, min_amount = 1, max_amount = 5),
            "raw_damage": RewardRNG(rate = 1, min_amount = 30, max_amount = 80),
        }
    },

    "Wasteland (End)": {
        "wood_pickaxe": {
            "raw_damage": RewardRNG(rate = 0, min_amount = 0, max_amount = 0),
        },
        "stone_pickaxe": {
            "space_rock": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 10, max_amount = 30),
        },
        "iron_pickaxe": {
            "space_rock": RewardRNG(rate = 1, min_amount = 1, max_amount = 4),
            "raw_damage": RewardRNG(rate = 1, min_amount = 40, max_amount = 50),
        },
        "diamond_pickaxe": {
            "space_rock": RewardRNG(rate = 1, min_amount = 2, max_amount = 4),
            "comet_fragment": RewardRNG(rate = 0.01, min_amount = 0, max_amount = 1, amount_layout = (30, 70)),
            "raw_damage": RewardRNG(rate = 1, min_amount = 80, max_amount = 100),
        },
        "nether_pickaxe": {
            "space_rock": RewardRNG(rate = 1, min_amount = 2, max_amount = 5),
            "comet_fragment": RewardRNG(rate = 0.05, min_amount = 0, max_amount = 1, amount_layout = (30, 70)),
            "raw_damage": RewardRNG(rate = 1, min_amount = 80, max_amount = 100),
        },
        "fragile_star_pickaxe": {
            "space_rock": RewardRNG(rate = 1, min_amount = 2, max_amount = 6),
            "comet_fragment": RewardRNG(rate = 0.15, min_amount = 0, max_amount = 1, amount_layout = (30, 70)),
            "raw_damage": RewardRNG(rate = 1, min_amount = 80, max_amount = 100),
        },
    }
}

# Define the loot generated for an exploring session in each location.
# The amount of loot is set to an RNG, which will then be rolled when calling `get_activity_loot()`.
# It is REQUIRED to provide the key "raw_damage" for each tool (even if it deals 0 damage!)
__EXPLORE_LOOT = {
    "5 (Overworld)": {
        "stone_sword": {
            "rotten_flesh": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 2),
            "meat": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 2),
            "bacon": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 2),
            "chicken": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 2),
        },
        "iron_sword": {
            "rotten_flesh": RewardRNG(rate = 0.5, min_amount = 3, max_amount = 5),
            "meat": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 2),
            "bacon": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 2),
            "chicken": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 2),
        },
        "diamond_sword": {
            "rotten_flesh": RewardRNG(rate = 0.5, min_amount = 3, max_amount = 5),
            "meat": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 2),
            "bacon": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 2),
            "chicken": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 2),
        },
        "nether_sword": {
            "rotten_flesh": RewardRNG(rate = 0.5, min_amount = 3, max_amount = 5),
            "meat": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 2),
            "bacon": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 2),
            "chicken": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 2),
        },
        "fragile_star_sword": {
            "rotten_flesh": RewardRNG(rate = 0.75, min_amount = 4, max_amount = 6),
            "meat": RewardRNG(rate = 0.3, min_amount = 1, max_amount = 2),
            "bacon": RewardRNG(rate = 0.3, min_amount = 1, max_amount = 2),
            "chicken": RewardRNG(rate = 0.3, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 2),
        },
    },
    "4 (Overworld)": {
        "stone_sword": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 1, max_amount = 4),
            "spider_eye": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 10, max_amount = 20),
        },
        "iron_sword": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 4, max_amount = 7),
            "spider_eye": RewardRNG(rate = 0.2, min_amount = 2, max_amount = 5),
            "gunpowder": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 10, max_amount = 20),
        },
        "diamond_sword": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 5, max_amount = 10),
            "spider_eye": RewardRNG(rate = 0.2, min_amount = 3, max_amount = 5),
            "gunpowder": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 4),
            "raw_damage": RewardRNG(rate = 1, min_amount = 10, max_amount = 20),
        },
        "nether_sword": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 5, max_amount = 10),
            "spider_eye": RewardRNG(rate = 0.2, min_amount = 3, max_amount = 5),
            "gunpowder": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 4),
            "raw_damage": RewardRNG(rate = 1, min_amount = 10, max_amount = 20),
        },
        "fragile_star_sword": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 6, max_amount = 12),
            "spider_eye": RewardRNG(rate = 0.3, min_amount = 4, max_amount = 6),
            "gunpowder": RewardRNG(rate = 0.3, min_amount = 1, max_amount = 5),
            "raw_damage": RewardRNG(rate = 1, min_amount = 10, max_amount = 20),
        },
    },
    "3 (Overworld)": {
        "stone_sword": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 1, max_amount = 4),
            "spider_eye": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 15, max_amount = 30),
        },
        "iron_sword": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 4, max_amount = 7),
            "spider_eye": RewardRNG(rate = 0.5, min_amount = 2, max_amount = 5),
            "gunpowder": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 15, max_amount = 30),
        },
        "diamond_sword": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 5, max_amount = 10),
            "spider_eye": RewardRNG(rate = 0.5, min_amount = 3, max_amount = 6),
            "gunpowder": RewardRNG(rate = 0.5, min_amount = 2, max_amount = 5),
            "pearl": RewardRNG(rate = 0.1, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 15, max_amount = 30),
        },
        "nether_sword": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 5, max_amount = 10),
            "spider_eye": RewardRNG(rate = 0.5, min_amount = 3, max_amount = 6),
            "gunpowder": RewardRNG(rate = 0.5, min_amount = 2, max_amount = 5),
            "pearl": RewardRNG(rate = 0.1, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 15, max_amount = 30),
        },
        "fragile_star_sword": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 6, max_amount = 12),
            "spider_eye": RewardRNG(rate = 0.75, min_amount = 4, max_amount = 7),
            "gunpowder": RewardRNG(rate = 0.75, min_amount = 2, max_amount = 6),
            "pearl": RewardRNG(rate = 0.15, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 15, max_amount = 30),
        },
    },
    "2 (Overworld)": {
        "stone_sword": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 1, max_amount = 4),
            "spider_eye": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 25, max_amount = 40),
        },
        "iron_sword": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 5, max_amount = 7),
            "spider_eye": RewardRNG(rate = 0.8, min_amount = 4, max_amount = 7),
            "gunpowder": RewardRNG(rate = 0.8, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 25, max_amount = 40),
        },
        "diamond_sword": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 7, max_amount = 10),
            "spider_eye": RewardRNG(rate = 0.8, min_amount = 5, max_amount = 7),
            "gunpowder": RewardRNG(rate = 0.8, min_amount = 1, max_amount = 4),
            "pearl": RewardRNG(rate = 0.1, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 25, max_amount = 40),
        },
        "nether_sword": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 7, max_amount = 10),
            "spider_eye": RewardRNG(rate = 0.8, min_amount = 5, max_amount = 7),
            "gunpowder": RewardRNG(rate = 0.8, min_amount = 1, max_amount = 4),
            "pearl": RewardRNG(rate = 0.1, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 25, max_amount = 40),
        },
        "fragile_star_sword": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 8, max_amount = 12),
            "spider_eye": RewardRNG(rate = 1, min_amount = 6, max_amount = 8),
            "gunpowder": RewardRNG(rate = 1, min_amount = 1, max_amount = 5),
            "pearl": RewardRNG(rate = 0.15, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 25, max_amount = 40),
        },
    },
    "1 (Overworld)": {
        "stone_sword": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 1, max_amount = 4),
            "spider_eye": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 30, max_amount = 60),
        },
        "iron_sword": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 5, max_amount = 7),
            "spider_eye": RewardRNG(rate = 1, min_amount = 4, max_amount = 7),
            "gunpowder": RewardRNG(rate = 1, min_amount = 1, max_amount = 4),
            "raw_damage": RewardRNG(rate = 1, min_amount = 30, max_amount = 60),
        },
        "diamond_sword": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 10, max_amount = 12),
            "spider_eye": RewardRNG(rate = 1, min_amount = 5, max_amount = 10),
            "gunpowder": RewardRNG(rate = 1, min_amount = 2, max_amount = 5),
            "pearl": RewardRNG(rate = 0.1, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 30, max_amount = 60),
        },
        "nether_sword": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 10, max_amount = 12),
            "spider_eye": RewardRNG(rate = 1, min_amount = 5, max_amount = 10),
            "gunpowder": RewardRNG(rate = 1, min_amount = 3, max_amount = 6),
            "pearl": RewardRNG(rate = 0.1, min_amount = 1, max_amount = 3),
            "raw_damage": RewardRNG(rate = 1, min_amount = 30, max_amount = 60),
        },
        "fragile_star_sword": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 12, max_amount = 14),
            "spider_eye": RewardRNG(rate = 1, min_amount = 6, max_amount = 12),
            "gunpowder": RewardRNG(rate = 1, min_amount = 4, max_amount = 7),
            "pearl": RewardRNG(rate = 0.15, min_amount = 1, max_amount = 4),
            "raw_damage": RewardRNG(rate = 1, min_amount = 30, max_amount = 60),
        }
    },

    "Fortress (Nether)": {
        "stone_sword": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 3, max_amount = 6),
            "gold": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 1),
            "magma_cream": RewardRNG(rate = 0.25, min_amount = 3, max_amount = 5),
            "blaze_rod": RewardRNG(rate = 0.01, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 25, max_amount = 50),
        },
        "iron_sword": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 5, max_amount = 10),
            "gold": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 2),
            "magma_cream": RewardRNG(rate = 0.25, min_amount = 5, max_amount = 8),
            "gunpowder": RewardRNG(rate = 0.1, min_amount = 1, max_amount = 1),
            "blaze_rod": RewardRNG(rate = 0.1, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 25, max_amount = 50),
        },
        "diamond_sword": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 6, max_amount = 12),
            "gold": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "magma_cream": RewardRNG(rate = 0.25, min_amount = 7, max_amount = 10),
            "gunpowder": RewardRNG(rate = 0.1, min_amount = 1, max_amount = 2),
            "blaze_rod": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 3),
            "raw_damage": RewardRNG(rate = 1, min_amount = 25, max_amount = 50),
        },
        "nether_sword": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 9, max_amount = 11),
            "gold": RewardRNG(rate = 1, min_amount = 2, max_amount = 3),
            "magma_cream": RewardRNG(rate = 0.25, min_amount = 8, max_amount = 10),
            "gunpowder": RewardRNG(rate = 0.1, min_amount = 1, max_amount = 2),
            "blaze_rod": RewardRNG(rate = 0.25, min_amount = 1, max_amount = 4),
            "raw_damage": RewardRNG(rate = 1, min_amount = 25, max_amount = 50),
        },
        "fragile_star_sword": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 11, max_amount = 13),
            "gold": RewardRNG(rate = 1, min_amount = 2, max_amount = 4),
            "magma_cream": RewardRNG(rate = 0.375, min_amount = 10, max_amount = 12),
            "gunpowder": RewardRNG(rate = 0.15, min_amount = 1, max_amount = 2),
            "blaze_rod": RewardRNG(rate = 0.375, min_amount = 1, max_amount = 5),
            "raw_damage": RewardRNG(rate = 1, min_amount = 25, max_amount = 50),
        }
    },
    "Bastion Remnant (Nether)": {
        "stone_sword": {
            "rotten_flesh": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 1),
            "gold": RewardRNG(rate = 1, min_amount = 3, max_amount = 6),
            "magma_cream": RewardRNG(rate = 0.25, min_amount = 3, max_amount = 5),
            "meat": RewardRNG(rate = 0.25, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 40, max_amount = 60),
        },
        "iron_sword": {
            "rotten_flesh": RewardRNG(rate = 0.5, min_amount = 3, max_amount = 5),
            "gold": RewardRNG(rate = 1, min_amount = 9, max_amount = 12),
            "magma_cream": RewardRNG(rate = 0.25, min_amount = 5, max_amount = 8),
            "meat": RewardRNG(rate = 0.25, min_amount = 3, max_amount = 5),
            "raw_damage": RewardRNG(rate = 1, min_amount = 40, max_amount = 60),
        },
        "diamond_sword": {
            "rotten_flesh": RewardRNG(rate = 0.5, min_amount = 5, max_amount = 7),
            "gold": RewardRNG(rate = 1, min_amount = 15, max_amount = 20),
            "magma_cream": RewardRNG(rate = 0.25, min_amount = 7, max_amount = 10),
            "meat": RewardRNG(rate = 0.25, min_amount = 5, max_amount = 8),
            "debris": RewardRNG(rate = 0.01, min_amount = 1, max_amount = 3),
            "raw_damage": RewardRNG(rate = 1, min_amount = 40, max_amount = 60),
        },
        "nether_sword": {
            "rotten_flesh": RewardRNG(rate = 0.5, min_amount = 5, max_amount = 7),
            "gold": RewardRNG(rate = 1, min_amount = 15, max_amount = 20),
            "magma_cream": RewardRNG(rate = 0.25, min_amount = 10, max_amount = 15),
            "meat": RewardRNG(rate = 0.25, min_amount = 5, max_amount = 8),
            "debris": RewardRNG(rate = 0.01, min_amount = 1, max_amount = 3),
            "raw_damage": RewardRNG(rate = 1, min_amount = 40, max_amount = 60),
        },
        "fragile_star_sword": {
            "rotten_flesh": RewardRNG(rate = 0.75, min_amount = 6, max_amount = 8),
            "gold": RewardRNG(rate = 1, min_amount = 18, max_amount = 24),
            "magma_cream": RewardRNG(rate = 0.375, min_amount = 12, max_amount = 18),
            "meat": RewardRNG(rate = 0.375, min_amount = 6, max_amount = 10),
            "debris": RewardRNG(rate = 0.015, min_amount = 1, max_amount = 4),
            "raw_damage": RewardRNG(rate = 1, min_amount = 40, max_amount = 60),
        },
    },
    "Abandoned Factory (Nether)": {
        "stone_sword": {
            "stone_sword": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 1),
            "stone_pickaxe": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 1),
            "stone_axe": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 1),
            "gold": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 2),
            "debris": RewardRNG(rate = 0.01, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 50, max_amount = 100),
        },
        "iron_sword": {
            "iron_sword": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 1),
            "iron_pickaxe": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 1),
            "iron_axe": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 1),
            "gold": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 5),
            "debris": RewardRNG(rate = 0.01, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 50, max_amount = 100),
        },
        "diamond_sword": {
            "iron_sword": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 1),
            "iron_pickaxe": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 1),
            "iron_axe": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 1),
            "gold": RewardRNG(rate = 0.5, min_amount = 3, max_amount = 10),
            "debris": RewardRNG(rate = 0.03, min_amount = 1, max_amount = 1),
            "netherite": RewardRNG(rate = 0.015, min_amount = 0, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 50, max_amount = 100),
        },
        "nether_sword": {
            "iron_sword": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 1),
            "iron_pickaxe": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 1),
            "iron_axe": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 1),
            "gold": RewardRNG(rate = 0.5, min_amount = 3, max_amount = 10),
            "debris": RewardRNG(rate = 0.1, min_amount = 1, max_amount = 1),
            "netherite": RewardRNG(rate = 0.03, min_amount = 0, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 50, max_amount = 100),
        },
        "fragile_star_sword": {
            "iron_sword": RewardRNG(rate = 0.75, min_amount = 1, max_amount = 1),
            "iron_pickaxe": RewardRNG(rate = 0.75, min_amount = 1, max_amount = 1),
            "iron_axe": RewardRNG(rate = 0.75, min_amount = 1, max_amount = 1),
            "gold": RewardRNG(rate = 0.75, min_amount = 4, max_amount = 12),
            "debris": RewardRNG(rate = 0.15, min_amount = 1, max_amount = 1),
            "netherite": RewardRNG(rate = 0.045, min_amount = 0, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 50, max_amount = 100),
        }
    },
    "Hidden Shrine (Nether)": {
        "stone_sword": {
            # Purposely empty.
        },
        "iron_sword": {
            # Purposely empty.
        },
        "diamond_sword": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 1, max_amount = 60),
            "gold": RewardRNG(rate = 1, min_amount = 1, max_amount = 30),
            "magma_cream": RewardRNG(rate = 1, min_amount = 1, max_amount = 30),
            "gunpowder": RewardRNG(rate = 1, min_amount = 1, max_amount = 30),
            "pearl": RewardRNG(rate = 1, min_amount = 1, max_amount = 20),
            "blaze_rod": RewardRNG(rate = 1, min_amount = 1, max_amount = 30),
            "nether_star": RewardRNG(rate = 0.05, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 80, max_amount = 150),
        },
        "nether_sword": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 1, max_amount = 60),
            "gold": RewardRNG(rate = 1, min_amount = 1, max_amount = 30),
            "magma_cream": RewardRNG(rate = 1, min_amount = 1, max_amount = 30),
            "gunpowder": RewardRNG(rate = 1, min_amount = 1, max_amount = 30),
            "pearl": RewardRNG(rate = 1, min_amount = 1, max_amount = 20),
            "blaze_rod": RewardRNG(rate = 1, min_amount = 1, max_amount = 30),
            "nether_star": RewardRNG(rate = 0.1, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 80, max_amount = 150),
        },
        "fragile_star_sword": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 1, max_amount = 72),
            "gold": RewardRNG(rate = 1, min_amount = 1, max_amount = 36),
            "magma_cream": RewardRNG(rate = 1, min_amount = 1, max_amount = 36),
            "gunpowder": RewardRNG(rate = 1, min_amount = 1, max_amount = 36),
            "pearl": RewardRNG(rate = 1, min_amount = 1, max_amount = 24),
            "blaze_rod": RewardRNG(rate = 1, min_amount = 1, max_amount = 36),
            "nether_star": RewardRNG(rate = 0.15, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 80, max_amount = 150),
        },
    },

    "Void Domain (End)": {
        "stone_sword": {
            "raw_damage": RewardRNG(rate = 1, min_amount = 100, max_amount = 150),
        },
        "iron_sword": {
            "raw_damage": RewardRNG(rate = 1, min_amount = 100, max_amount = 150),
        },
        "diamond_sword": {
            "raw_damage": RewardRNG(rate = 1, min_amount = 100, max_amount = 150),
        },
        "nether_sword": {
            "star_fragment": RewardRNG(rate = 0.05, min_amount = 0, max_amount = 2, amount_layout = [50, 40, 10]),
            "raw_damage": RewardRNG(rate = 1, min_amount = 100, max_amount = 150),
        },
        "fragile_star_sword": {
            "star_fragment": RewardRNG(rate = 0.09, min_amount = 0, max_amount = 2, amount_layout = [50, 45, 5]),
            "raw_damage": RewardRNG(rate = 1, min_amount = 100, max_amount = 150),
        },
    }
}

# Define the loot generated for a chopping session in each location.
# The amount of loot is set to an RNG, which will then be rolled when calling `get_activity_loot()`.
# It is REQUIRED to provide the key "raw_damage" for each tool (even if it deals 0 damage!)
__CHOP_LOOT = {
    "Forest (Overworld)": {
        "stone_axe": {
            "wood": RewardRNG(rate = 1, min_amount = 1, max_amount = 3),
            "leaf": RewardRNG(rate = 1, min_amount = 10, max_amount = 15),
            "apple": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "orange": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "cherries": RewardRNG(rate = 1, min_amount = 1, max_amount = 4),
            "carrot": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 2),
            "hibiscus": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 3),
            "tulip": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 3),
            "rose": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 3),
            "lucky_clover": RewardRNG(rate = 0.1, min_amount = 1, max_amount = 3),
            "raw_damage": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 2),
        },
        "iron_axe": {
            "wood": RewardRNG(rate = 1, min_amount = 1, max_amount = 3),
            "leaf": RewardRNG(rate = 1, min_amount = 15, max_amount = 20),
            "apple": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "orange": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "cherries": RewardRNG(rate = 1, min_amount = 1, max_amount = 4),
            "carrot": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 2),
            "hibiscus": RewardRNG(rate = 0.5, min_amount = 3, max_amount = 5),
            "tulip": RewardRNG(rate = 0.5, min_amount = 3, max_amount = 5),
            "rose": RewardRNG(rate = 0.5, min_amount = 3, max_amount = 5),
            "lucky_clover": RewardRNG(rate = 0.1, min_amount = 1, max_amount = 3),
            "raw_damage": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 2),
        },
        "diamond_axe": {
            "wood": RewardRNG(rate = 1, min_amount = 1, max_amount = 3),
            "leaf": RewardRNG(rate = 1, min_amount = 20, max_amount = 25),
            "apple": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "orange": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "cherries": RewardRNG(rate = 1, min_amount = 1, max_amount = 4),
            "carrot": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 2),
            "hibiscus": RewardRNG(rate = 0.5, min_amount = 5, max_amount = 10),
            "tulip": RewardRNG(rate = 0.5, min_amount = 5, max_amount = 10),
            "rose": RewardRNG(rate = 0.5, min_amount = 5, max_amount = 10),
            "lucky_clover": RewardRNG(rate = 0.15, min_amount = 1, max_amount = 5),
            "raw_damage": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 2),
        },
        "nether_axe": {
            "wood": RewardRNG(rate = 1, min_amount = 2, max_amount = 3),
            "leaf": RewardRNG(rate = 1, min_amount = 25, max_amount = 30),
            "apple": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "orange": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "cherries": RewardRNG(rate = 1, min_amount = 1, max_amount = 4),
            "carrot": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 2),
            "hibiscus": RewardRNG(rate = 0.5, min_amount = 8, max_amount = 10),
            "tulip": RewardRNG(rate = 0.5, min_amount = 8, max_amount = 10),
            "rose": RewardRNG(rate = 0.5, min_amount = 8, max_amount = 10),
            "lucky_clover": RewardRNG(rate = 0.15, min_amount = 2, max_amount = 6),
            "raw_damage": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 2),
        },
        "fragile_star_axe": {
            "wood": RewardRNG(rate = 1, min_amount = 2, max_amount = 4),
            "leaf": RewardRNG(rate = 1, min_amount = 30, max_amount = 36),
            "apple": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "orange": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "cherries": RewardRNG(rate = 1, min_amount = 1, max_amount = 5),
            "carrot": RewardRNG(rate = 0.75, min_amount = 1, max_amount = 2),
            "hibiscus": RewardRNG(rate = 0.75, min_amount = 10, max_amount = 12),
            "tulip": RewardRNG(rate = 0.75, min_amount = 10, max_amount = 12),
            "rose": RewardRNG(rate = 0.75, min_amount = 10, max_amount = 12),
            "lucky_clover": RewardRNG(rate = 0.225, min_amount = 2, max_amount = 7),
            "raw_damage": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 2),
        },
    },
    "Village (Overworld)": {
        "stone_axe": {
            "wood": RewardRNG(rate = 1, min_amount = 1, max_amount = 3),
            "apple": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "orange": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "cherries": RewardRNG(rate = 1, min_amount = 1, max_amount = 4),
            "carrot": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 2),
            "bed_pickaxe": RewardRNG(rate = 0.1, min_amount = 1, max_amount = 5),
            "iron": RewardRNG(rate = 0.1, min_amount = 1, max_amount = 5),
            "raw_damage": RewardRNG(rate = 1, min_amount = 1, max_amount = 10),
        },
        "iron_axe": {
            "wood": RewardRNG(rate = 1, min_amount = 1, max_amount = 3),
            "apple": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "orange": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "cherries": RewardRNG(rate = 1, min_amount = 1, max_amount = 4),
            "carrot": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 2),
            "bed_pickaxe": RewardRNG(rate = 0.1, min_amount = 1, max_amount = 5),
            "iron": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 5),
            "raw_damage": RewardRNG(rate = 1, min_amount = 1, max_amount = 10),
        },
        "diamond_axe": {
            "wood": RewardRNG(rate = 1, min_amount = 1, max_amount = 3),
            "apple": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "orange": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "cherries": RewardRNG(rate = 1, min_amount = 1, max_amount = 4),
            "carrot": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 2),
            "bed_pickaxe": RewardRNG(rate = 0.1, min_amount = 1, max_amount = 5),
            "iron": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 5),
            "raw_damage": RewardRNG(rate = 1, min_amount = 1, max_amount = 10),
        },
        "nether_axe": {
            "wood": RewardRNG(rate = 1, min_amount = 2, max_amount = 3),
            "apple": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "orange": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "cherries": RewardRNG(rate = 1, min_amount = 1, max_amount = 4),
            "carrot": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 2),
            "bed_pickaxe": RewardRNG(rate = 0.1, min_amount = 1, max_amount = 5),
            "iron": RewardRNG(rate = 0.1, min_amount = 1, max_amount = 5),
            "raw_damage": RewardRNG(rate = 1, min_amount = 1, max_amount = 10),
        },
        "fragile_star_axe": {
            "wood": RewardRNG(rate = 1, min_amount = 2, max_amount = 4),
            "apple": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "orange": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "cherries": RewardRNG(rate = 1, min_amount = 1, max_amount = 5),
            "carrot": RewardRNG(rate = 0.75, min_amount = 1, max_amount = 2),
            "bed_pickaxe": RewardRNG(rate = 0.15, min_amount = 1, max_amount = 6),
            "iron": RewardRNG(rate = 0.15, min_amount = 1, max_amount = 6),
            "raw_damage": RewardRNG(rate = 1, min_amount = 1, max_amount = 10),
        },
    },
    "Desert Temple (Overworld)": {
        "stone_axe": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 1, max_amount = 4),
            "spider_eye": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 2),
            "gunpowder": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 2),
            "diamond": RewardRNG(rate = 0.02, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 5, max_amount = 100, amount_layout = tuple([50, 48] + [0] * 93 + [2])),
        },
        "iron_axe": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 4, max_amount = 7),
            "spider_eye": RewardRNG(rate = 0.5, min_amount = 2, max_amount = 5),
            "gunpowder": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 2),
            "diamond": RewardRNG(rate = 0.02, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 5, max_amount = 100, amount_layout = tuple([50, 48] + [0] * 93 + [2])),
        },
        "diamond_axe": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 4, max_amount = 7),
            "spider_eye": RewardRNG(rate = 0.5, min_amount = 3, max_amount = 5),
            "gunpowder": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 4),
            "diamond": RewardRNG(rate = 0.02, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 5, max_amount = 100, amount_layout = tuple([50, 48] + [0] * 93 + [2])),
        },
        "nether_axe": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 4, max_amount = 7),
            "spider_eye": RewardRNG(rate = 0.5, min_amount = 2, max_amount = 5),
            "gunpowder": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 4),
            "diamond": RewardRNG(rate = 0.02, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 5, max_amount = 100, amount_layout = tuple([50, 48] + [0] * 93 + [2])),
        },
        "fragile_star_axe": {
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 5, max_amount = 8),
            "spider_eye": RewardRNG(rate = 0.75, min_amount = 2, max_amount = 6),
            "gunpowder": RewardRNG(rate = 0.75, min_amount = 1, max_amount = 5),
            "diamond": RewardRNG(rate = 0.03, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 5, max_amount = 100, amount_layout = tuple([50, 48] + [0] * 93 + [2])),
        }
    },
    
    "Crimson Forest (Nether)": {
        "stone_axe": {
            "wood": RewardRNG(rate = 1, min_amount = 5, max_amount = 7),
            "dry_leaf": RewardRNG(rate = 1, min_amount = 100, max_amount = 150),
            "bacon": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 1),
            "meat": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 20, max_amount = 35),
        },
        "iron_axe": {
            "wood": RewardRNG(rate = 1, min_amount = 10, max_amount = 15),
            "dry_leaf": RewardRNG(rate = 1, min_amount = 150, max_amount = 200),
            "mushroom": RewardRNG(rate = 0.3, min_amount = 3, max_amount = 5),
            "bacon": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "meat": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 20, max_amount = 35),
        },
        "diamond_axe": {
            "wood": RewardRNG(rate = 1, min_amount = 15, max_amount = 20),
            "dry_leaf": RewardRNG(rate = 1, min_amount = 200, max_amount = 250),
            "mushroom": RewardRNG(rate = 0.3, min_amount = 5, max_amount = 7),
            "bacon": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "meat": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 20, max_amount = 35),
        },
        "nether_axe": {
            "wood": RewardRNG(rate = 1, min_amount = 20, max_amount = 25),
            "dry_leaf": RewardRNG(rate = 1, min_amount = 250, max_amount = 300),
            "mushroom": RewardRNG(rate = 0.3, min_amount = 5, max_amount = 7),
            "bacon": RewardRNG(rate = 1, min_amount = 1, max_amount = 3),
            "meat": RewardRNG(rate = 1, min_amount = 1, max_amount = 3),
            "raw_damage": RewardRNG(rate = 1, min_amount = 20, max_amount = 35),
        },
        "fragile_star_axe": {
            "wood": RewardRNG(rate = 1, min_amount = 24, max_amount = 30),
            "dry_leaf": RewardRNG(rate = 1, min_amount = 200, max_amount = 360),
            "mushroom": RewardRNG(rate = 0.36, min_amount = 6, max_amount = 8),
            "bacon": RewardRNG(rate = 1, min_amount = 1, max_amount = 4),
            "meat": RewardRNG(rate = 1, min_amount = 1, max_amount = 4),
            "raw_damage": RewardRNG(rate = 1, min_amount = 20, max_amount = 35),
        }
    },
    "Warped Forest (Nether)": {
        "stone_axe": {
            "wood": RewardRNG(rate = 1, min_amount = 5, max_amount = 7),
            "dry_leaf": RewardRNG(rate = 1, min_amount = 100, max_amount = 150),
            "pearl": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 20, max_amount = 35),
        },
        "iron_axe": {
            "wood": RewardRNG(rate = 1, min_amount = 10, max_amount = 15),
            "dry_leaf": RewardRNG(rate = 1, min_amount = 100, max_amount = 150),
            "pearl": RewardRNG(rate = 1, min_amount = 1, max_amount = 4),
            "raw_damage": RewardRNG(rate = 1, min_amount = 20, max_amount = 35),
        },
        "diamond_axe": {
            "wood": RewardRNG(rate = 1, min_amount = 15, max_amount = 20),
            "dry_leaf": RewardRNG(rate = 1, min_amount = 100, max_amount = 150),
            "pearl": RewardRNG(rate = 1, min_amount = 1, max_amount = 4),
            "raw_damage": RewardRNG(rate = 1, min_amount = 20, max_amount = 35),
        },
        "nether_axe": {
            "wood": RewardRNG(rate = 1, min_amount = 20, max_amount = 25),
            "dry_leaf": RewardRNG(rate = 1, min_amount = 100, max_amount = 150),
            "pearl": RewardRNG(rate = 1, min_amount = 1, max_amount = 5),
            "raw_damage": RewardRNG(rate = 1, min_amount = 20, max_amount = 35),
        },
        "fragile_star_axe": {
            "wood": RewardRNG(rate = 1, min_amount = 24, max_amount = 30),
            "dry_leaf": RewardRNG(rate = 1, min_amount = 120, max_amount = 180),
            "pearl": RewardRNG(rate = 1, min_amount = 1, max_amount = 6),
            "raw_damage": RewardRNG(rate = 1, min_amount = 20, max_amount = 35),
        }
    },
    "Soul Sand Valley (Nether)": {
        "stone_axe": {
            "gunpowder": RewardRNG(rate = 1, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 30, max_amount = 75),
        },
        "iron_axe": {
            "gunpowder": RewardRNG(rate = 1, min_amount = 1, max_amount = 3),
            "raw_damage": RewardRNG(rate = 1, min_amount = 30, max_amount = 75),
        },
        "diamond_axe": {
            "gunpowder": RewardRNG(rate = 1, min_amount = 3, max_amount = 5),
            "raw_damage": RewardRNG(rate = 1, min_amount = 30, max_amount = 75),
        },
        "nether_axe": {
            "gunpowder": RewardRNG(rate = 1, min_amount = 3, max_amount = 6),
            "raw_damage": RewardRNG(rate = 1, min_amount = 30, max_amount = 75),
        },
        "fragile_star_axe": {
            "gunpowder": RewardRNG(rate = 1, min_amount = 4, max_amount = 7),
            "raw_damage": RewardRNG(rate = 1, min_amount = 30, max_amount = 75),
        },
    },
    "Basalt Deltas (Nether)": {
        "stone_axe": {
            "magma_cream": RewardRNG(rate = 1, min_amount = 5, max_amount = 10),
            "raw_damage": RewardRNG(rate = 1, min_amount = 30, max_amount = 75),
        },
        "iron_axe": {
            "magma_cream": RewardRNG(rate = 1, min_amount = 10, max_amount = 20),
            "raw_damage": RewardRNG(rate = 1, min_amount = 30, max_amount = 75),
        },
        "diamond_axe": {
            "magma_cream": RewardRNG(rate = 1, min_amount = 20, max_amount = 50),
            "raw_damage": RewardRNG(rate = 1, min_amount = 30, max_amount = 75),
        },
        "nether_axe": {
            "magma_cream": RewardRNG(rate = 1, min_amount = 20, max_amount = 60),
            "raw_damage": RewardRNG(rate = 1, min_amount = 30, max_amount = 75),
        },
        "fragile_star_axe": {
            "magma_cream": RewardRNG(rate = 1, min_amount = 24, max_amount = 72),
            "raw_damage": RewardRNG(rate = 1, min_amount = 30, max_amount = 75),
        },
    },

    "End City (End)": {
        "stone_axe": {
            "gold": RewardRNG(rate = 1, min_amount = 5, max_amount = 7),
            "diamond": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 3),
            "shulker_box": RewardRNG(rate = 0.05, min_amount = 0, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 50, max_amount = 100),
        },
        "iron_axe": {
            "gold": RewardRNG(rate = 1, min_amount = 5, max_amount = 10),
            "diamond": RewardRNG(rate = 0.5, min_amount = 5, max_amount = 6),
            "shulker_box": RewardRNG(rate = 0.05, min_amount = 0, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 50, max_amount = 100),
        },
        "diamond_axe": {
            "gold": RewardRNG(rate = 1, min_amount = 10, max_amount = 12),
            "diamond": RewardRNG(rate = 0.5, min_amount = 6, max_amount = 8),
            "comet_fragment": RewardRNG(rate = 0.005, min_amount = 0, max_amount = 1),
            "shulker_box": RewardRNG(rate = 0.05, min_amount = 0, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 50, max_amount = 100),
        },
        "nether_axe": {
            "gold": RewardRNG(rate = 1, min_amount = 10, max_amount = 12),
            "diamond": RewardRNG(rate = 0.5, min_amount = 6, max_amount = 8),
            "comet_fragment": RewardRNG(rate = 0.005, min_amount = 0, max_amount = 1),
            "star_fragment": RewardRNG(rate = 0.005, min_amount = 0, max_amount = 2),
            "shulker_box": RewardRNG(rate = 0.05, min_amount = 0, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 50, max_amount = 100),
        },
        "fragile_star_axe": {
            "gold": RewardRNG(rate = 1, min_amount = 12, max_amount = 14),
            "diamond": RewardRNG(rate = 0.75, min_amount = 7, max_amount = 9),
            "comet_fragment": RewardRNG(rate = 0.05, min_amount = 0, max_amount = 1),
            "star_fragment": RewardRNG(rate = 0.05, min_amount = 0, max_amount = 2),
            "shulker_box": RewardRNG(rate = 0.06, min_amount = 0, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 50, max_amount = 100),
        },
    },
    "Floating Island (End)": {
        "stone_axe": {
            "pearl": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 1),
            "raw_damage": RewardRNG(rate = 1, min_amount = 80, max_amount = 100),
        },
        "iron_axe": {
            "pearl": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            "raw_damage": RewardRNG(rate = 1, min_amount = 80, max_amount = 100),
        },
        "diamond_axe": {
            "pearl": RewardRNG(rate = 1, min_amount = 5, max_amount = 10),
            "raw_damage": RewardRNG(rate = 1, min_amount = 10, max_amount = 100),
        },
        "nether_axe": {
            "pearl": RewardRNG(rate = 1, min_amount = 5, max_amount = 12),
            "raw_damage": RewardRNG(rate = 1, min_amount = 10, max_amount = 100),
        },
        "fragile_star_axe": {
            "pearl": RewardRNG(rate = 1, min_amount = 6, max_amount = 14),
            "raw_damage": RewardRNG(rate = 1, min_amount = 10, max_amount = 100),
        }
    }
}

MINE_LOCATION = __MINE_LOOT.keys()
EXPLORE_LOCATION = __EXPLORE_LOOT.keys()
CHOP_LOCATION = __CHOP_LOOT.keys()
WORLD_LOCATION = {
    "overworld": (
        "5 (Overworld)", "4 (Overworld)", "3 (Overworld)", "2 (Overworld)", "1 (Overworld)",
        "Forest (Overworld)", "Village (Overworld)", "Desert Temple (Overworld)",
    ),
    "nether": (
        "-1 (Nether)", "-2 (Nether)", "-3 (Nether)", "-4 (Nether)", "-5 (Nether)",
        "Fortress (Nether)", "Bastion Remnant (Nether)", "Abandoned Factory (Nether)", "Hidden Shrine (Nether)",
        "Crimson Forest (Nether)", "Warped Forest (Nether)", "Soul Sand Valley (Nether)", "Basalt Deltas (Nether)",
    ),
    "end": (
        "Wasteland (End)", "Void Domain (End)", "End City (End)", "Floating Island (End)"
    )
}

# Define the crafting recipe for items.
# For each item's crafting recipe, there must be a special key "result" which denote the amount of items as a result of crafting.
__CRAFT_RECIPE = {
    "stick": {
        "wood": 1,
        "result": 2
    },
    "wood_pickaxe": {
        "wood": 3,
        "stick": 2,
        "result": 1
    },
    "stone_pickaxe": {
        "stone": 3,
        "stick": 2,
        "result": 1
    },
    "stone_sword": {
        "stone": 2,
        "stick": 1,
        "result": 1
    },
    "stone_axe": {
        "stone": 3,
        "stick": 2,
        "result": 1
    },
    "iron_pickaxe": {
        "iron": 3,
        "stick": 2,
        "result": 1
    },
    "iron_sword": {
        "iron": 2,
        "stick": 1,
        "result": 1
    },
    "iron_axe": {
        "iron": 3,
        "stick": 1,
        "result": 1
    },
    "diamond_pickaxe": {
        "diamond": 3,
        "stick": 2,
        "result": 1
    },
    "diamond_sword": {
        "diamond": 2,
        "stick": 1,
        "result": 1
    },
    "diamond_axe": {
        "diamond": 3,
        "stick": 2,
        "result": 1
    },
    "nether_ticket": {
        "obsidian": 10,
        "result": 5
    },
    "netherite": {
        "debris": 4,
        "gold": 4,
        "result": 1
    },
    "nether_pickaxe": {
        "netherite": 1,
        "iron": 20,
        "diamond_pickaxe": 1,
        "result": 1
    },
    "nether_sword": {
        "netherite": 1,
        "iron": 20,
        "diamond_sword": 1,
        "result": 1
    },
    "nether_axe": {
        "netherite": 1,
        "iron": 20,
        "diamond_axe": 1,
        "result": 1
    },
    "end_ticket": {
        "nether_star": 4,
        "pearl": 2,
        "blaze_rod": 1,
        "result": 2
    },
    "star_gem": {
        "star_fragment": 150,
        "comet_fragment": 150,
        "space_rock": 2500,
        "result": 1
    },
    "fragile_star_pickaxe": {
        "star_gem": 1,
        "nether_pickaxe": 1,
        "result": 1
    },
    "fragile_star_sword": {
        "star_gem": 1,
        "nether_sword": 1,
        "result": 1
    },
    "fragile_star_axe": {
        "star_gem": 1,
        "nether_axe": 1,
        "result": 1
    }
}

__BREW_RECIPE = {
    # 37491
    "luck_potion": {
        "nether_star": 66,
        "lucky_clover": 420,
        "hibiscus": 777,
        "tulip": 777,
        "rose": 777,
        "redstone": 777,
        "gunpowder": 777,
        "blaze_rod": 69,
        "cost": 6969,
        "result": 3
    },
    # 35058
    "undying_potion": {
        "nether_star": 99,
        "lucky_clover": 99,
        "nether_respawner": 33,
        "fire_potion": 9,
        "redstone": 666,
        "gunpowder": 666,
        "blaze_rod": 99,
        "cost": 420,
        "result": 3
    },
    # 1947
    "fire_potion": {
        "magma_cream": 60,
        "hibiscus": 99,
        "tulip": 99,
        "rose": 99,
        "redstone": 150,
        "gunpowder": 15,
        "spider_eye": 60,
        "blaze_rod": 3,
        "cost": 300,
        "result": 3
    },
    # 3875
    "haste_potion": {
        "nether_star": 1,
        "lucky_clover": 60,
        "redstone": 150,
        "gunpowder": 150,
        "gold": 60,
        "diamond": 9,
        "blaze_rod": 3,
        "cost": 450,
        "result": 3
    },
    # 2775
    "fortune_potion": {
        "lucky_clover": 15,
        "redstone": 300,
        "gunpowder": 75,
        "gold": 60,
        "diamond": 3,
        "blaze_rod": 3,
        "cost": 450,
        "result": 3
    },
    # 2640
    "nature_potion": {
        "leaf": 450,
        "hibiscus": 120,
        "tulip": 120,
        "rose": 120,
        "mushroom": 150,
        "redstone": 150,
        "gunpowder": 15,
        "blaze_rod": 3,
        "cost": 450,
        "result": 3
    },
    # 3620
    "strength_potion": {
        "nether_star": 1,
        "rotten_flesh": 240,
        "spider_eye": 90,
        "gunpowder": 90,
        "pearl": 45,
        "redstone": 150,
        "blaze_rod": 3,
        "cost": 450,
        "result": 3
    },
    # 2760
    "looting_potion": {
        "rotten_flesh": 210,
        "spider_eye": 90,
        "magma_cream": 30,
        "gunpowder": 45,
        "pearl": 30,
        "redstone": 120,
        "blaze_rod": 3,
        "cost": 450,
        "result": 3
    }
}

__POTION_CHANCE = {
    "fire_potion": 1,
    "haste_potion": 0.50,
    "fortune_potion": 0.50,
    "nature_potion": 0.50,
    "strength_potion": 0.50,
    "looting_potion": 0.50,
    "luck_potion": 0.65,
    "undying_potion": 1,
}

def get_daily_loot(streak: int) -> dict[str, int]:
    '''Return the daily loot based on the current streak.

    Parameters
    ----------
    streak : int
        The current streak.

    Returns
    -------
    dict[str, int]
        A `dict` denoting the loot table.
    '''

    if streak <= 1:
        return {
            "money": 50,
            "wood": 5
        }
    if streak <= 6:
        return {
            "money": 10,
            "wood": random.randint(10, 15)
        }
    if streak <= 13:
        return {
            "money": 100,
            "bonus": streak,
            "wood": random.randint(10, 15),
            "leaf": random.randint(50, 60),
            "hibiscus": random.randint(10, 12),
            "tulip": random.randint(10, 12),
            "rose": random.randint(10, 12),
        }
    if streak <= 27:
        return {
            "money": 200,
            "bonus": 5 * streak,
            "wood": random.randint(20, 25),
            "leaf": random.randint(100, 110),
            "hibiscus": random.randint(20, 22),
            "tulip": random.randint(20, 22),
            "rose": random.randint(20, 22),
        }
    if streak <= 60:
        return {
            "money": 1000,
            "bonus": 2 * streak,
            "wood": random.randint(50, 55),
            "leaf": random.randint(210, 220),
            "hibiscus": random.randint(50, 52),
            "tulip": random.randint(50, 52),
            "rose": random.randint(50, 52),
            "lucky_clover": random.randint(1, 5),
        }
    if streak <= 90:    
        return {
            "money": 2000,
            "bonus": 5 * streak,
            "wood": random.randint(190, 210),
            "leaf": random.randint(190, 210),
            "hibiscus": random.randint(190, 210),
            "tulip": random.randint(190, 210),
            "rose": random.randint(190, 210),
            "lucky_clover": random.randint(1, 10),
        }
    return {
        "money": 5000,
        "bonus": 10 * streak,
        "wood": random.randint(500, 1000),
        "leaf": random.randint(1000, 2000),
        "hibiscus": random.randint(500, 1000),
        "tulip": random.randint(500, 1000),
        "rose": random.randint(500, 1000),
        "lucky_clover": random.randint(5, 20),
        "diamond": random.randint(10, 20),
        "debris": random.randint(0, 4),
    }

def get_activity_loot(action_type: str, equipment_id: str, location: str, external_buffs: t.Sequence[str] = None) -> t.Optional[dict[str, int]]:
    '''Return the loot generated by an equipment in a world.

    Parameters
    ----------
    action_type : str
        The action's type. Either `mine`, `explore`, or `chop`.
    equipment_id : str
        The equipment's id. The function won't check for valid id.
    location : str
        The location's name. The function won't check for valid world.
    external_buffs : t.Sequence[str]
        A list of buffs' ids that can affect the drop. Example: `['luck_potion']`

    Returns
    -------
    t.Optional[dict[str, int]]
        A `dict` denoting the loot table, or `None` if there's no matching loot table.
    
    Exceptions
    ----------
    ValueError
        `action_type` value is invalid.
    '''

    if not external_buffs:
        external_buffs = []
    
    reward: dict[str, int] = {}

    action_loot_table = None
    if action_type == "mine":
        action_loot_table = __MINE_LOOT
    elif action_type == "explore":
        action_loot_table = __EXPLORE_LOOT
    elif action_type == "chop":
        action_loot_table = __CHOP_LOOT
    else:
        raise ValueError("action_type argument must be either 'mine', 'explore', or 'chop'.")
    
    world_loot = action_loot_table.get(location)

    if not world_loot:
        return None
    
    # Copy here cuz
    # - Can edit the rng.
    # - Copy world_loot is more expensive.
    equipment_loot = copy.deepcopy(world_loot.get(equipment_id))
    if not equipment_loot:
        return None
    
    for item_id, rng in equipment_loot.items():
        if item_id == "raw_damage":
            reward[item_id] = rng.roll()
            continue
        
        if item_id == "iron":
            if "iron2" in external_buffs:
                rng.rate += 0.10
        elif item_id == "diamond":
            if "diamond1" in external_buffs:
                rng.rate += 0.05
            if "diamond2" in external_buffs:
                rng.rate += 0.10
                rng.shift_min_amount(2)
        elif item_id == "debris":
            if "debris1" in external_buffs:
                rng.rate += 0.025
            if "debris2" in external_buffs:
                rng.rate += 0.05
                rng.shift_min_amount(1)
        
        elif item_id == "blaze_rod":
            if "blaze1" in external_buffs:
                rng.rate += 0.05
        
        elif item_id == "wood":
            if "wood2" in external_buffs:
                rng.shift_min_amount(2)

        if "luck_potion" in external_buffs:
            rng.rate *= 3
        
        reward[item_id] = rng.roll()
        
        if "luck_potion" in external_buffs:
            if reward[item_id] == 0:
                reward[item_id] = rng.min_amount
            else:
                reward[item_id] = rng.max_amount

    return reward

def get_craft_recipe(item_id: str) -> t.Optional[dict[str, int]]:
    '''Return the crafting recipe for an item if existed.

    Notes
    -----
    The returning `dict` has a special key `result`, which denote how many items will be crafted out of the recipe.

    Parameters
    ----------
    item_id : str
        The item's id.

    Returns
    -------
    t.Optional[dict[str, int]]
        A `dict` denoting the crafting recipe, or `None` if no crafting recipe is found.
    '''

    return copy.deepcopy(__CRAFT_RECIPE.get(item_id))

def get_brew_recipe(potion_id: str) -> t.Optional[dict[str, int]]:
    '''Return the brewing recipe for a potion if existed.

    Notes
    -----
    The returning `dict` has a special key `result`, which denote how many potions will be brewed out of the recipe.

    Parameters
    ----------
    potion_id : str
        The potion's id.

    Returns
    -------
    t.Optional[dict[str, int]]
        A `dict` denoting the brewing recipe, or `None` if no brewing recipe is found.
    '''

    return copy.deepcopy(__BREW_RECIPE.get(potion_id))

def roll_potion_activate(potion_id: str) -> bool:
    '''Try to roll and see if the potion activated.

    Parameters
    ----------
    potion_id : str
        The potion's id.

    Returns
    -------
    bool
        Whether the potion activated or not.
    '''
    chance = __POTION_CHANCE.get(potion_id, 0)
    if chance == 1:
        return True
    
    return random.random() <= chance
