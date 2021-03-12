def get_item_info():
    return {
        "log": ["🪵", "Log", 10, None],
        "wood": ["<:plank:819616763074838569>", "wood", 10, None],
        "stick": ["<:stick:819615522878521434>", "stick", 10, None],
        "wood_pickaxe": ["<:wood_pickaxe:819617302164930570>", "wooden pickaxe", 10, None],
        "stone": ["<:stone:819728758160097290>", "stone", 10, None],
        "coal": ["<:coal:819742286250377306>", "coal", 10, None]
    }

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

def get_craft_ingredient(item : str):
    if item == "wood":
        return {
            "log": 1,
            "quantity": 4
        }
    elif item == "stick":
        return {
            "wood": 2,
            "quantity": 4
        }
    elif item == "wood_pickaxe":
        return {
            "wood": 3,
            "stick": 2,
            "quantity": 1
        }
    
    return None