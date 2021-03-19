import random

import categories.utilities.db as DB

def acapitalize(st : str) -> str:
    return " ".join(word.capitalize() for word in st.split())

def get_item_info():
    return {
        # General format:
        # id: ['emoji', 'name', 'rarity', buy_price, sell_price, durability, 
        #   description]
        "log": ["🪵", "log", "common", None, 20, None,
            "A basic necessity for everyone. Useful at any times."],
        "wood": ["<:plank:819616763074838569>", "wood", "common", 8, 4, None,
            "A basic material for basic stuffs."],
        "stick": ["<:stick:819615522878521434>", "stick", "common", 4, 2, None,
            "A necessity item used to craft various tools."],
        "wood_pickaxe": ["<:wood_pickaxe:819617302164930570>", "wooden pickaxe", "common", 30, 25, None,
            "A fragile pickaxe."],
        "wood_axe": ["<:wood_axe:820009505530052621>", "wooden axe", "common", 32, 27, None,
            "A fragile axe."],
        "wood_sword": ["<:wood_sword:820757505017118751>", "wooden sword", "common", 28, 23, None, 
            "A weak sword."],
        "stone": ["<:stone:819728758160097290>", "stone", "common", None, 15, None,
            "A harder material than wood."],
        "stone_pickaxe": ["<:stone_pickaxe:820044330613866497>", "stone pickaxe", "common", None, 11, None,
            "A better pickaxe. Hope you can get some iron soon."],
        "stone_axe": ["<:stone_axe:820009331000606760>", "stone axe", "common", None, 12, None,
            "A better axe."],
        "stone_sword": ["<:stone_sword:820757729790394389>", "stone sword", "common", None, 10, None,
            "A decent sword. Better than a toy sword, right?"],
        "iron": ["<:iron:820009715286671410>", "iron", "uncommon", None, 30, None,
            "Iron!"],
        "iron_pickaxe": ["<:iron_pickaxe:820757966432632854>", "iron pickaxe", "uncommon", None, 35, None,
            "A pretty good pickaxe. You may encounter some lucky stuffs with this pickaxe."],
        "iron_axe": ["<:iron_axe:820758123714838559>", "iron axe", "uncommon", None, 37, None,
            "A pretty good axe."],
        "iron_sword": ["<:iron_sword:821448555989696593>", "iron sword", "uncommon", None, 33, None,
            "A pretty good sword. You can slay more enemies now due to how good this sword is."],
        "redstone": ["<:redstone:822527280777396264>", "redstone", "uncommon", None, 50, None,
            "A red dust that's commonly mistaken as blood. It's understandable, it has pulse after all."],
        "diamond": ["💎", "diamond", "rare", 150, 100, None,
            "Shiny stuffs isn't it? It can be used to craft some of the best tools in the world."],
        "diamond_pickaxe": ["<:diamond_pickaxe:822530447481372703>", "diamond pickaxe", "rare", None, 150, None,
            "The best pickaxe in the world. You can mine anything :)"],
        "diamond_axe": ["<:diamond_axe:822530447719268382>", "diamond axe", "rare", None, 150, None,
            "The best axe in the world. Chopping go brr."],
        "diamond_sword": ["<:diamond_sword:822530447715598396>", "diamond sword", "rare", None, 150, None,
            "The best sword in the world? Idk, it doesn't do much though..."],
        "obsidian": ["<:obsidian:822532045673725964>", "obsidian", "rare", None, 80, None,
            "The hardest material in the world. It silently emits power that connects to another world."],

        "coal": ["<:coal:819742286250377306>", "coal", "common", 15, 10, None,
            "A mysterious dark object used for fuel."],
        "string": ["<:string:820758307542401055>", "string", "common", 15, 10, None,
            "A useful drop for some future uses."],
        "spider_eye": ["<:spider_eye:820758868468301864>", "spider eye", "uncommon", None, 20, None,
            "An uncommon drop for some future uses."],
        "gunpowder": ["<:gunpowder:821528688646160395>", "gunpowder", "uncommon", 50, 30, None,
            "An uncommon drop for some uhh *minor* terrorism purposes."],
        "apple": ["🍎", "apple", "common", None, 10, None,
            "An apple. Yummy. Watch out for the worms though."],
        "flower": ["🌸", "flower", "common", None, 10, None,
            "A beautiful flower."],
        "moyai": ["🌺", "moyai", "???", None, None, None,
            "A mysterious mystical flower. It is unknown what this flower truly is."]
    }

async def get_friendly_reward(conn, reward : dict, emote = True) -> str:
    msg = ""
    for key in reward:
        if reward[key] != 0:
            item = await DB.Items.get_item(conn, key)
            if item is not None:
                if emote:
                    msg += f"{item['emoji']} x {reward[key]}, "
                else:
                    msg += f"{reward[key]}x **{acapitalize(item['name'])}**, "
    
    # Remove ', '
    msg = msg[:-2]
    return msg

def get_mine_loot(pick : str):
    if pick == "wood_pickaxe":
        return {
            "stone": 0.90, # 2.7 on average
            "rolls": 3
        }
    elif pick == "stone_pickaxe":
        return {
            "stone": 0.40, # 3.2 on average
            "coal": 0.40, # 3.2 on average
            "iron": 0.10, # 0.8 on average
            "rolls": 8
        }
    elif pick == "iron_pickaxe":
        return {
            "stone": 0.35, # 3.5 on average
            "coal": 0.30, # 3 on average
            "iron": 0.25, # 2.5 on average
            "redstone": 0.05, # 0.5 on average
            "diamond": 0.01, # 0.1 on average
            "rolls": 10
        }
    elif pick == "diamond_pickaxe":
        return {
            "stone": 0.26, # 5.2 on average
            "coal": 0.15, # 3 on average
            "iron": 0.25, # 5 on average
            "redstone": 0.10, # 2 on average
            "diamond": 0.05, # 1 on average
            "obsidian": 0.10, # 2 on average
            "rolls": 20
        }
    
    return None

def get_chop_loot(axe : str):
    if axe == "wood_axe":
        return {
            "log": 1, # 3 guaranteed
            "rolls": 3
        }
    elif axe == "stone_axe":
        return {
            "log": 0.60, # 4.2 on average
            "stick": 0.20, # 1.4 on average
            "apple": 0.20, # 1.4 on average
            "rolls": 7
        }
    elif axe == "iron_axe":
        return {
            "log": 0.50, # 5 on average
            "stick": 0.15, # 1.5 on average
            "apple": 0.15, # 1.5 on average
            "flower": 0.20, # 2 on average
            "rolls": 10
        }
    elif axe == "diamond_axe":
        return {
            "log": 0.45, # 9 on average
            "stick": 0.10, # 2 on average
            "apple": 0.25, # 5 on average
            "flower": 0.20, # 4 on average
            "moyai": 0.000000005, # 0.0000001 on average
            "rolls": 20
        }
    
    return None

def get_adventure_loot(sword : str):
    if sword == "wood_sword":
        return {
            "string": 0.30,  # 0.6 on average
            "rolls": 2
        }
    elif sword == "stone_sword":
        return {
            "string": 0.35, # 1.75 on average
            "spider_eye": 0.05, # 0.25 on average
            "rolls": 5
        }
    elif sword == "iron_sword":
        return {
            "string": 0.35, # 3.5 on average
            "spider_eye": 0.15, # 1.5 on average
            "gunpowder": 0.1, # 1 on average
            "rolls": 10
        }
    elif sword == "diamond_sword":
        return {
            "string": 0.30, # 6 on average
            "spider_eye": 0.15, # 3 on average
            "gunpowder": 0.25, # 5 on average
            "rolls": 20
        }
    return None

def get_daily_loot(streak : int):
    if streak < 10:
        return {
            "log": random.randint(2, 5),
            "wood": random.randint(0, 3),
            "stick": random.randint(1, 4)
        }
    elif streak < 51:
        return {
            "log": random.randint(5, 10),
            "stone": random.randint(3, 5),
            "coal": random.randint(10, 12)
        }
    elif streak < 101:
        return {
            "log": random.randint(20, 30),
            "stone": random.randint(10, 20),
            "iron": random.randint(5, 8),
            "diamond": random.randint(0, 1)
        }
    elif streak < 201:
        return {
            "log": random.randint(35, 40),
            "stone": random.randint(15, 25),
            "iron": random.randint(10, 15),
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
        "wood_sword": {
            "wood": 2,
            "stick": 1,
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
        "stone_sword": {
            "stone" : 2,
            "stick": 1,
            "quantity": 1
        },
        "iron_pickaxe": {
            "iron": 3,
            "stick": 2,
            "quantity": 1
        },
        "iron_axe": {
            "iron": 3,
            "stick": 3,
            "quantity": 1
        },
        "iron_sword": {
            "iron": 2,
            "stick": 1,
            "quantity": 1
        },
        "diamond_pickaxe": {
            "diamond": 3,
            "stick": 2,
            "quantity": 1
        },
        "diamond_axe": {
            "diamond": 3,
            "stick": 3,
            "quantity": 1
        },
        "diamond_sword": {
            "diamond": 2,
            "stick": 1,
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