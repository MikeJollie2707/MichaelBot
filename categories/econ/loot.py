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

__CRAFT_RECIPE__ = {
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
}

def roll_amount(*, rate: float, min_amount: int, max_amount: int, amount_layout: tuple[float] = None) -> int:
    '''Return the amount of items based on the provided RNG.

    Parameters
    ----------
    rate : float
        Define the drop rate of the associated item. Must be between 0 and 1.
    min_amount : int
        Define the minimum amount of this item to drop if it happens to roll. This should be positive.
    max_amount : int
        Define the maximum amount of this item to drop if it happens to roll. This should be positive.
    amount_layout : tuple[float], optional
        Define the rng distribution between `min_amount` and `max_amount`. This should satisfy `len(amount_layout) == (max_amount - min_amount + 1) and sum(amount_layout) == 1`

    Returns
    -------
    int
        The final amount based on the RNG.
    '''
    if rate < 1:
        r = random.random()
        if rate > r:
            return 0
    
    if amount_layout is None:
        return random.choice(range(min_amount, max_amount + 1))
    
    r = random.random()
    _rate = 0
    for index, amount_rate in enumerate(amount_layout):
        rate += amount_rate
        if r <= _rate:
            return min(min_amount + index, max_amount)
    
    return max_amount

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

def get_mine_loot(pickaxe_id: str, world: str) -> dict[str, int]:
    reward: dict[str, int] = {}

    if world == "overworld":
        if pickaxe_id == "wood_pickaxe":
            reward = {
                "stone": roll_amount(rate = 1, min_amount = 1, max_amount = 2),
            }
            return reward
        elif pickaxe_id == "stone_pickaxe":
            reward = {
                "stone": roll_amount(rate = 1, min_amount = 3, max_amount = 5),
                "iron": roll_amount(rate = 0.5, min_amount = 1, max_amount = 2, amount_layout = (0.75, 0.25)),
            }
            return reward
    return None

def get_sword_loot(sword_id: str, world: str) -> dict[str, int]:
    reward: dict[str, int] = {}

    if world == "overworld":
        if sword_id == "stone_sword":
            reward = {
                "rotten_flesh": roll_amount(rate = 1, min_amount = 2, max_amount = 4),
                "spider_eye": roll_amount(rate = 0.2, min_amount = 1, max_amount = 2),
            }
            return reward

    return None

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

    return __CRAFT_RECIPE__.get(item_id)

def __driver_code__():
    '''DO NOT CALL THIS FUNCTION.

    This is a function only because all variables used will be public when exporting (thank you Python for its scoping "rule").
    '''
    
    SIMULATION_TIME = 1000000
    rate_tracker: dict[str, int] = {"total": 0}

    for i in range(0, SIMULATION_TIME):
        loot_rate = get_sword_loot("stone_sword", "overworld")

        for reward in loot_rate:
            if reward not in rate_tracker:
                rate_tracker[reward] = loot_rate[reward]
            else:
                rate_tracker[reward] += loot_rate[reward]
            
            rate_tracker["total"] += loot_rate[reward]
    
    total = rate_tracker["total"]
    del rate_tracker["total"]

    print(f"Sim {SIMULATION_TIME:,} times, total amount: {total:,}")
    for item, amount in rate_tracker.items():
        print(f"- {item}: {amount:,} / {total:,} ({float(amount) / total * 100 :.5f}%)")

if __name__ == "__main__":
    __driver_code__()
