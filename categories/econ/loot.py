'''Define the loot tables for the economy system.'''

# A few special keywords that are reserved in the loot tables:
# - "result": Usually in crafting-related stuff, it defines how many items will end up as the result of the craft.
# - "money": The money as a reward.
# - "bonus": Same as "money", just different message.
# - "cost": The money lost.

import dataclasses
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
    }
}

@dataclasses.dataclass()
class RewardRNG:
    '''Define an item's drop rate.

    There are 3 attributes: `rate`, `min_amount`, and `max_amount`.
    
    Attributes
    ----------
    rate : float
        Define the drop rate of the associated item. Must be between 0 and 1.
    min_amount : int
        Define the minimum amount of this item to drop if it happens to roll. This should be positive.
    max_amount : int
        Define the maximum amount of this item to drop if it happens to roll. This should be positive.
    '''
    rate: float
    min_amount: int
    max_amount: int

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

def get_mine_loot_rate(pickaxe_id: str, world: str) -> dict[str, RewardRNG]:
    if world == "overworld":
        if pickaxe_id == "wood_pickaxe":
            return {
                "stone": RewardRNG(rate = 1, min_amount = 1, max_amount = 2),
            }
        elif pickaxe_id == "stone_pickaxe":
            return {
                "stone": RewardRNG(rate = 1, min_amount = 3, max_amount = 5),
                "iron": RewardRNG(rate = 0.5, min_amount = 1, max_amount = 2),
            }
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
