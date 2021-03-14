import random

def acapitalize(st : str) -> str:
    return " ".join(word.capitalize() for word in st.split())

def get_item_info():
    return {
        "log": ["🪵", "log", 10, None],
        "wood": ["<:plank:819616763074838569>", "wood", 10, None],
        "stick": ["<:stick:819615522878521434>", "stick", 10, None],
        "wood_pickaxe": ["<:wood_pickaxe:819617302164930570>", "wooden pickaxe", 10, None],
        "wood_axe": ["<:wood_axe:820009505530052621>", "wooden axe", 10, None],
        "wood_sword": ["<:wood_sword:820757505017118751>", "wooden sword", 10, None],
        "stone": ["<:stone:819728758160097290>", "stone", 10, None],
        "stone_pickaxe": ["<:stone_pickaxe:820044330613866497>", "stone pickaxe", 10, None],
        "stone_axe": ["<:stone_axe:820009331000606760>", "stone axe", 10, None],
        "stone_sword": ["<:stone_sword:820757729790394389>", "stone sword", 10, None],
        "iron": ["<:iron:820009715286671410>", "iron", 10, None],
        "iron_pickaxe": ["<:iron_pickaxe:820757966432632854>", "iron pickaxe", 10, None],
        "iron_axe": ["<:iron_axe:820758123714838559>", "iron axe", 10, None],

        "coal": ["<:coal:819742286250377306>", "coal", 10, None],
        "string": ["<:string:820758307542401055>", "string", 10, None],
        "spider_eye": ["<:spider_eye:820758868468301864>", "spider eye", 10, None],
        "apple": ["🍎", "apple", 10, None],
        "flower": ["🌸", "flower", 10, None]
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

def get_mine_loot(pick : str):
    if pick == "wood_pickaxe":
        return {
            "stone": 0.90,
            "coal": 0.10,
            "rolls": 6
        }
    elif pick == "stone_pickaxe":
        return {
            "stone": 0.50,
            "coal": 0.35,
            "iron": 0.10,
            "rolls": 20
        }
    elif pick == "iron_pickaxe":
        return {
            "stone": 0.35,
            "coal": 0.30,
            "iron": 0.25,
            "diamond": 0.10,
            "rolls": 25
        }
    elif pick == "diamond_pickaxe":
        return {
            "stone": 0.15,
            "coal": 0.10,
            "iron": 0.30,
            "diamond": 0.20,
            "obsidian": 0.25,
            "rolls": 35
        }
    
    return None

def get_chop_loot(axe : str):
    if axe == "wood_axe":
        return {
            "log": 1,
            "rolls": 3
        }
    elif axe == "stone_axe":
        return {
            "log": 0.60,
            "wood": 0.30,
            "stick": 0.10,
            "rolls": 20
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
        },
        "wood_axe": {
            "wood": 3,
            "stick": 3,
            "quantity": 1
        },
        "stone_pickaxe": {
            "stone": 3,
            "stick": 2,
            "quantity": 1
        },
        "stone_axe": {
            "stone": 3,
            "stick": 3,
            "quantity": 1
        },
        "coal": {
            "log": 1,
            "wood": 1,
            "quantity": 2
        }
    }
    
    if item is None:
        return craft_recipe
    else:
        return craft_recipe.get(item)