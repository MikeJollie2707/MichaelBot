import typing as t

def get_daily_loot(streak: int) -> dict[str, int]:
    if streak <= 1:
        return {
            "money": 50,
            "wood": 5
        }
    if streak <= 6:
        return {
            "money": 10,
            "wood": 15
        }
    if streak <= 13:
        return {
            "money": 20,
            "bonus": streak,
            "wood": 12
        }
    if streak <= 27:
        return {
            "money": 20,
            "bonus": 5 * (streak - 12),
            "wood": 16
        }
    if streak <= 60:
        return {
            "money": 100,
            "bonus": 2 * (streak - 20),
            "wood": 100
        }
    return {
        "money": 200,
        "bonus": 5 * (streak - 60),
        "wood": 200
    }

def get_mine_loot(pickaxe_id: str, world: str) -> dict[str, int]:
    if world == "overworld":
        if pickaxe_id == "wood_pickaxe":
            return {
                "stone": random.randint(1, 2),
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

    recipe = {
        "stick": {
            "wood": 1,
            "result": 2
        },
        "wood_pickaxe": {
            "wood": 3,
            "stick": 2,
            "result": 1
        }
    }

    return recipe.get(item_id)
