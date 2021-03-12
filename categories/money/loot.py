import random

def acapitalize(st : str) -> str:
    return " ".join(word.capitalize() for word in st.split())

def get_item_info():
    return {
        "log": ["🪵", "log", 10, None],
        "wood": ["<:plank:819616763074838569>", "wood", 10, None],
        "stick": ["<:stick:819615522878521434>", "stick", 10, None],
        "wood_pickaxe": ["<:wood_pickaxe:819617302164930570>", "wooden pickaxe", 10, None],
        "stone": ["<:stone:819728758160097290>", "stone", 10, None],
        "coal": ["<:coal:819742286250377306>", "coal", 10, None]
    }

def get_emote(name : str) -> str:
    info = get_item_info()
    for key in info:
        if info[key][1] == name:
            return info[key][0]

def get_emote_i(id : str) -> str:
    info = get_item_info()
    return info[id][0]

def get_internal_name(name : str) -> str:
    info = get_item_info()
    for key in info:
        if info[key][1] == name:
            return key

def get_friendly_name(id : str) -> str:
    info = get_item_info()
    return acapitalize(info[id][1])

def get_friendly_reward(reward : dict, emote = True) -> str:
    msg = ""
    items = get_item_info()
    for key in reward:
        if reward[key] != 0:
            if emote:
                msg += f"{items[key][0]} x {reward[key]}, "
            else:
                msg += f"{reward[key]}x {acapitalize(items[key][1])}, "
    
    # Remove ', '
    msg = msg[:-2]
    return msg

def get_mine_loot(pick_name : str):
    if pick_name == "wood_pickaxe":
        return {
            "stone": 0.90,
            "coal": 0.10,
            "rolls": 7
        }
    elif pick_name == "stone_pickaxe":
        return {
            "stone": 0.50,
            "coal": 0.25,
            "iron": 0.25,
            "rolls": 25
        }
    elif pick_name == "iron_pickaxe":
        return {
            "stone": 0.20,
            "coal": 0.25,
            "iron": 0.45,
            "diamond": 0.10,
            "rolls": 40
        }
    
    return None

def get_daily_loot(streak : int):
    if streak < 10:
        return {
            "log": random.randint(3, 5),
            "wood": random.randint(0, 3),
            "stick": random.randint(1, 6)
        }
    elif streak < 51:
        return {
            "log": random.randint(5, 10),
            "stone": random.randint(3, 5),
            "coal": random.randint(10, 12)
        }
    elif streak < 101:
        return {
            "log": random.randint(12, 15),
            "stone": random.randint(7, 14),
            "iron": random.randint(1, 3),
            "diamond": random.randint(0, 1)
        }
    elif streak < 201:
        return {
            "log": random.randint(20, 25),
            "stone": random.randint(20, 25),
            "iron": random.randint(5, 10),
            "diamond": random.randint(2, 5)
        }
    
    return None

def get_bonus_loot(bonus : int):
    # We might not need this.
    pass

def get_craft_ingredient(item : str):
    craft_recipe = {
        "wood": {
            "log": 1,
            "quantity": 4
        },
        "stick": {
            "wood": 2,
            "quantity": 4
        },
        "wood_pickaxe": {
            "wood": 3,
            "stick": 2,
            "quantity": 1
        }
    }
    
    if item is None:
        return craft_recipe
    else:
        return craft_recipe.get(item)