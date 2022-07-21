'''Define the loot tables for the economy system.'''

# A few special keywords that are reserved in the loot tables:
# - "result": Usually in crafting-related stuff, it defines how many items will end up as the result of the craft.
# - "money": The money as a reward.
# - "bonus": Same as "money", just different message.
# - "cost": The money lost.

import random
import typing as t

RESERVED_KEYS = (
    "result",
    "money",
    "bonus",
    "cost",
)

class RewardRNG:
    '''Define the RNG to randomize.

    Attributes
    ----------
    rate : float
        Define the drop rate of the associated item. Must be between 0 and 1.
    min_amount : int
        Define the minimum amount of this item to drop if it happens to roll. This should be positive.
    max_amount : int
        Define the maximum amount of this item to drop if it happens to roll. This should be positive.
    amount_layout : tuple[float], optional
        Define the rng distribution between `min_amount` and `max_amount`. This should satisfy `len(amount_layout) == (max_amount - min_amount + 1) and sum(amount_layout) == 1`
    '''
    __slots__ = ("rate", "min_amount", "max_amount", "amount_layout")

    def __init__(self, rate: float, min_amount: int, max_amount: int, *, amount_layout: tuple[float] = None):
        if rate < 0 or rate > 1:
            raise ValueError("'rate' must be in [0, 1].")
        if min_amount > max_amount:
            raise ValueError("'min_amount' must be smaller than or equal to 'max_amount'.")
        if amount_layout:
            if len(amount_layout) != (max_amount - min_amount + 1):
                raise ValueError("'amount_layout' must have the same amount of items as (max_amount - min_amount + 1).")
            if sum(amount_layout) != 1:
                raise ValueError("'amount_layout' must sum up to 1.")

        self.rate = rate
        self.min_amount = min_amount
        self.max_amount = max_amount
        self.amount_layout = amount_layout

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
            rate += amount_rate
            if r <= rate:
                return min(self.min_amount + index, self.max_amount)
        
        return self.max_amount

'''Define the loot generated by equipments in each world.

The amount of loot is set to an RNG, which will then be rolled when calling `get_activity_loot()`.
Note that for each equipment in each world, it should generate at least 1 non-zero entry.
'''
__ACTIVITY_LOOT = {
    "overworld": {
        # Pickaxe
        "wood_pickaxe": {
            "stone": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
        },
        "stone_pickaxe": {
            # - stone: 86.49%
            # - iron: 13.51%
            "stone": RewardRNG(rate = 1, min_amount = 3, max_amount = 5),
            "iron": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 2, amount_layout = (0.75, 0.25)),
        },
        "iron_pickaxe": {
            # - stone: 83.83%
            # - iron: 14.50%
            # - diamond: 1.67%
            "stone": RewardRNG(rate = 1, min_amount = 4, max_amount = 7),
            "iron": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 4, amount_layout = (0.50, 0.20, 0.20, 0.10)),
            "diamond": RewardRNG(rate = 0.1, min_amount = 1, max_amount = 2, amount_layout = (0.90, 0.10)),
        },
        "diamond_pickaxe": {
            # - stone: 85.85%
            # - iron: 10.85%
            # - diamond: 1.50%
            # - obsidian: 1.80%
            "stone": RewardRNG(rate = 1, min_amount = 8, max_amount = 11),
            "iron": RewardRNG(rate = 0.6, min_amount = 1, max_amount = 5, amount_layout = (0.45, 0.25, 0.20, 0.05, 0.05)),
            "diamond": RewardRNG(rate = 0.1, min_amount = 1, max_amount = 4, amount_layout = (0.50, 0.40, 0.05, 0.05)),
            "obsidian": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 1),
        },

        # Sword
        "stone_sword": {
            # - rotten_flesh: 90.91%
            # - spider_eye: 9.09%
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 2, max_amount = 4),
            "spider_eye": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 2),
        },
        "iron_sword": {
            # - rotten_flesh: 83.3%
            # - spider_eye: 10.4%
            # - gunpowder: 6.2%
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 3, max_amount = 5),
            "spider_eye": RewardRNG(rate = 0.2, min_amount = 2, max_amount = 3),
            "gunpowder": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 2),
        },
        "diamond_sword": {
            # - rotten_flesh: 84.47%
            # - spider_eye: 11.25%
            # - gunpowder: 3.72%
            # - pearl: 0.56%
            "rotten_flesh": RewardRNG(rate = 1, min_amount = 6, max_amount = 9),
            "spider_eye": RewardRNG(rate = 0.25, min_amount = 3, max_amount = 5),
            "gunpowder": RewardRNG(rate = 0.2, min_amount = 1, max_amount = 3, amount_layout = (0.50, 0.35, 0.15)),
            "pearl": RewardRNG(rate = 0.05, min_amount = 1, max_amount = 1),
        }
    },
    "nether": {
        "wood_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 1, max_amount = 1),
        },
        "stone_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 1, max_amount = 1),
        },
        "iron_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 4, max_amount = 7),
        },
        "diamond_pickaxe": {
            "redstone": RewardRNG(rate = 1, min_amount = 8, max_amount = 11),
        },
    },
}

'''Define the crafting recipe for items.

For each item's crafting recipe, there must be a special key "result" which denote the amount of items as a result of crafting.
'''
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
    "nether_ticket": {
        "obsidian": 10,
        "result": 5
    },
}

def get_daily_loot(streak: int) -> dict[str, int]:
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
            "money": 10,
            "bonus": streak,
            "wood": random.randint(10, 15)
        }
    if streak <= 27:
        return {
            "money": 20,
            "bonus": 5 * (streak - 12),
            "wood": random.randint(11, 16)
        }
    if streak <= 60:
        return {
            "money": 100,
            "bonus": 2 * (streak - 20),
            "wood": random.randint(95, 105)
        }
    return {
        "money": 200,
        "bonus": 5 * (streak - 60),
        "wood": random.randint(190, 210)
    }

def get_activity_loot(equipment_id: str, world: str) -> t.Optional[dict[str, int]]:
    '''Return the loot generated by an equipment in a world.

    Parameters
    ----------
    equipment_id : str
        The equipment's id. The function won't check for valid id.
    world : str
        The world's name. The function won't check for valid world.

    Returns
    -------
    t.Optional[dict[str, int]]
        A `dict` denoting the loot table, or `None` if there's no matching loot table.
    '''
    
    reward: dict[str, int] = {}

    world_loot = __ACTIVITY_LOOT.get(world)
    if not world_loot:
        return None
    
    equipment_loot = world_loot.get(equipment_id)
    if not equipment_loot:
        return None
    
    for item_id, rng in equipment_loot.items():
        reward[item_id] = rng.roll()

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

    return __CRAFT_RECIPE.get(item_id)

def __driver_code__():
    '''DO NOT CALL THIS FUNCTION.

    This is a function only because all variables used will be public when exporting (thank you Python for its scoping "rule").
    '''
    
    SIMULATION_TIME = 10 ** 6
    total: int = 0
    rate_tracker: dict[str, int] = {}

    for i in range(0, SIMULATION_TIME):
        loot_rate = get_activity_loot("diamond_sword", "overworld")

        for reward in loot_rate:
            if reward not in rate_tracker:
                rate_tracker[reward] = loot_rate[reward]
            else:
                rate_tracker[reward] += loot_rate[reward]
            
            total += loot_rate[reward]

    print(f"Sim {SIMULATION_TIME:,} times, total amount: {total:,}")
    for item, amount in rate_tracker.items():
        print(f"- {item}: {amount:,} / {total:,} ({float(amount) / total * 100 :.5f}%)")

if __name__ == "__main__":
    __driver_code__()
