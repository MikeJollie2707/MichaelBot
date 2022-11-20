'''Simulate/test the economy system.

This is ONLY meant to be run directly. DO NOT IMPORT THIS.
'''

import json
import loot

def _cache_load() -> dict[str, dict]:
    '''Return the item information as a raw cache.

    Returns
    -------
    dict[str, dict]
        The items' information.
    '''
    item_cache = {}
    with open("categories/econ/items.json", encoding = 'utf-8') as fin:
        item_data = json.load(fin)
        for item_d in item_data:
            item_cache[item_d["id"]] = item_d
    return item_cache

def loot_value(loot_table: dict[str, int], buy_mode: bool = True):
    item_cache = _cache_load()

    values = {}
    for item_id in loot_table:
        if item_id in ("money", "bonus", "cost"):
            values[item_id] = loot_table[item_id]
        elif item_id in item_cache:
            if buy_mode and item_cache[item_id].get("buy_price"):
                values[item_id] = item_cache[item_id]["buy_price"] * loot_table[item_id]
            else:
                values[item_id] = item_cache[item_id]["sell_price"] * loot_table[item_id]
    total: int = 0
    for amount in values.values():
        total += amount
    
    print(values)
    print(total)

def average_loot_value(tool_id: str, world: str, simulation_time: int = 10 ** 6):
    '''Calculate the average value of the loot generated by tools.

    Parameters
    ----------
    tool_id : str
        A valid tool's id.
    world : str
        Either `overworld` or `nether`.
    simulation_time : int, optional
        How many times the loot will be generated, by default 10**6
    '''
    
    item_cache = _cache_load()
    
    SIMULATION_TIME = simulation_time
    value: int = 0
    
    for _ in range(0, SIMULATION_TIME):
        loot_table = loot.get_activity_loot(tool_id, world)

        for reward in loot_table:
            if reward in ("money", "bonus"):
                value += loot_table[reward]
            else:
                value += item_cache[reward]["sell_price"] * loot_table[reward]
    
    print(f"Sim {SIMULATION_TIME:,} times with the following tool: {tool_id} in {world}")
    print(f"Total value: {value}")
    print(f"Average values: {value / SIMULATION_TIME}")

def tool_simulator(tool_id: str, location: str, *, external_buffs: list[str] = None, sim_time: int = 10 ** 6):
    '''Simulate an action session.

    Parameters
    ----------
    tool_id : str
        A valid tool id.
    world : str
        A valid location defined in `loot.XYZ_LOCATION`.
    external_buffs : list[str]
        Any external buffs to pass into `loot.get_activity_loot()`.
    sim_time : int, optional
        How many times the simulation runs, by default 10**6
    '''

    SIMULATION_TIME = sim_time
    total: int = 0
    rate_tracker: dict[str, int] = {}

    action_type = "mine"
    if "_sword" in tool_id:
        action_type = "explore"
    elif "_axe" in tool_id:
        action_type = "chop"

    for _ in range(0, SIMULATION_TIME):
        loot_rate = loot.get_activity_loot(action_type, tool_id, location, external_buffs)
        del loot_rate["raw_damage"]

        for reward in loot_rate:
            if reward not in rate_tracker:
                rate_tracker[reward] = loot_rate[reward]
            else:
                rate_tracker[reward] += loot_rate[reward]
            
            total += loot_rate[reward]

    print(f"Sim {SIMULATION_TIME:,} times, total amount: {total:,}")
    print(f"Buffs: {external_buffs}")
    for item, amount in rate_tracker.items():
        print(f"- {item}: {amount:,} / {total:,} ({float(amount) / total * 100 :.5f}%)")

if __name__ == "__main__":
    #average_loot_value("diamond_sword", "nether")
    tool_simulator("fragile_star_axe", "End City (End)", 
        external_buffs=["luck_potion"],
        sim_time=200
    )
    #loot_value(loot.__BREW_RECIPE["undying_potion"], False)
