import random

import utilities.db as DB

def acapitalize(st : str) -> str:
    return " ".join(word.capitalize() for word in st.split())

def get_item_info():
    return {
        # General format:
        # id: ['emoji', 'name', 'rarity', buy_price, sell_price, durability, 
        #   description]

        # Overworld materials
        "log": ["🪵", "log", "common", None, 18, None,
            "A basic necessity for everyone. Useful at any times."],
        "wood": ["<:plank:819616763074838569>", "wood", "common", 8, 4, None,
            "A basic material for basic stuffs."],
        "stick": ["<:stick:819615522878521434>", "stick", "common", 4, 2, None,
            "A necessity item used to craft various tools."],
        "stone": ["<:stone:819728758160097290>", "stone", "common", None, 20, None,
            "A harder material than wood."],
        "iron": ["<:iron:820009715286671410>", "iron", "uncommon", None, 45, None,
            "Iron!"],
        "redstone": ["<:redstone:822527280777396264>", "redstone", "uncommon", None, 42, None,
            "A red dust that's commonly mistaken as blood. It's understandable, it has pulse after all."],
        "diamond": ["💎", "diamond", "rare", None, 100, None,
            "Shiny stuffs isn't it? It can be used to craft some of the best tools in the world."],
        
        # Overworld tools
        "wood_sword": ["<:wood_sword:820757505017118751>", "wooden sword", "common", 10, 8, 59, 
            "A weak sword."],
        "wood_pickaxe": ["<:wood_pickaxe:819617302164930570>", "wooden pickaxe", "common", 12, 10, 59,
            "A weak pickaxe."],
        "wood_axe": ["<:wood_axe:820009505530052621>", "wooden axe", "common", 11, 9, 59,
            "A weak axe."],
        "stone_sword": ["<:stone_sword:820757729790394389>", "stone sword", "common", None, 23, 131,
            "A decent sword. Better than a toy sword, right?"],
        "stone_pickaxe": ["<:stone_pickaxe:820044330613866497>", "stone pickaxe", "common", None, 25, 131,
            "A better pickaxe. Hope you can get some iron soon."],
        "stone_axe": ["<:stone_axe:820009331000606760>", "stone axe", "common", None, 27, 131,
            "A better axe."],
        "iron_sword": ["<:iron_sword:821448555989696593>", "iron sword", "uncommon", None, 65, 250,
            "A pretty good sword. You can slay more enemies now due to how good this sword is."],
        "iron_pickaxe": ["<:iron_pickaxe:820757966432632854>", "iron pickaxe", "uncommon", None, 65, 250,
            "A pretty good pickaxe. You may encounter some lucky stuffs with this pickaxe."],
        "iron_axe": ["<:iron_axe:820758123714838559>", "iron axe", "uncommon", None, 63, 250,
            "A pretty good axe."],
        "diamond_sword": ["<:diamond_sword:822530447715598396>", "diamond sword", "rare", None, 200, 1561,
            "The best sword in the world? Idk, it doesn't do much though..."],
        "diamond_pickaxe": ["<:diamond_pickaxe:822530447481372703>", "diamond pickaxe", "rare", None, 250, 1561,
            "The best pickaxe in the world. You can mine anything :)"],
        "diamond_axe": ["<:diamond_axe:822530447719268382>", "diamond axe", "rare", None, 195, 1561,
            "The best axe in the world. Chopping go brr."],
        
        "anvil": ["<:anvil:837478303862489108>", "anvil", "rare", None, 1200, None,
            "A useful item required to upgrade tools. I wonder what that means..."],
        
        # Nether-related materials
        "obsidian": ["<:obsidian:822532045673725964>", "obsidian", "rare", None, 75, None,
            "The hardest material in the world. It silently emits power that connects to another world."],
        "nether": ["⛩️", "nether portal", "???", None, None, 6,
            "A mysterious gate that travels to the deepest place in the world."],
        "netherrack": ["<:netherrack:823592746865655868>", "netherrack", "common", None, 5, None,
            "A red-ish stone block only presents in the hottest place."],
        "gold": ["<:gold:823592599314104331>", "gold", "uncommon", None, 50, None,
            "Gold. How useful."],
        "debris": ["<:debris:823622624118702081>", "ancient debris", "rare+", None, 500, None,
            "A leftover of what was once the toughest metal in the universe. Such toughness is only achievable under the undying heat."],
        "netherite": ["<:netherite:828129193275293706>", "netherite", "rare+", None, 2000, None,
            "The toughest metal in the universe, recovered from its leftover."],
        "nether_sword": ["<:nether_sword:828129193434939442>", "netherite sword", "rare+", None, 2200, 2032,
            "A sword created from the shiniest thing on Earth, and enhanced with the toughest metal in the universe. It can cut down even the toughest enemy."],
        "nether_pickaxe": ["<:nether_pickaxe:828129193254191144>", "netherite pickaxe", "rare+", None, 2200, 2032,
            "A pickaxe created from the shiniest thing on Earth, and enhanced with the toughest metal in the universe."],
        "nether_axe": ["<:nether_axe:828129193367175178>", "netherite axe", "rare+", None, 2200, 2032,
            "An axe created from the shiniest thing on Earth, and enhanced with the toughest metal in the universe."],

        # Moon-related materials
        "pearl": ["<:pearl:837479108555440198>", "pearl", "rare", None, 70, None,
            "A rare drop from mysterious tall creatures. They're pretty shy it seems."],
        "moonstone": ["<:moonstone:839207608275435620>", "moonstone", "common", None, 23, None,
            "A stone with a weird white surface. They're surprisingly long to break."],
        "end": ["<:end_frame:839207656219738126>", "space portal", "???", None, None, 6,
            "A mysterious portal that travels beyond the sky."],
        "ender_eye": ["<:mysterious_eye:839207993391317003>", "mysterious eye", "rare", None, None, None,
            "This eye looks kinda weird. It seems to have some correlation to the space portal though..."],
        "space_orb": ["☄️", "space orb", "legendary+", None, 10000, None,
            "An enchanting orb founded randomly during your adventure in the Space."],
        "star_fragment": ["💫", "star fragment", "legendary+", None, 10000, None,
            "A fragment of the star, once existed in the universe. It possesses hidden energies of the star."],
        "star_gem": ["🌟", "star gem", "mythic", None, 1000000, None,
            "A shiny gem created from its fragment, but is greatly enhanced by the space orb."],
        "fragile_star_sword": ["", "star sword (fragile)", "mythic", None, 125000, 5000,
            "A sword created from the gem of the star. Unfortunately, it can't stand against extreme heat, and will break if brought into the Nether."],
        "star_sword": ["", "star sword", "mythic+", None, 150000, 7500,
            "A sword created from the gem of the star, enhanced by the metal of the underworld. It can now stand against any kind of heat."],
        "fragile_star_pickaxe": ["<:fragile_star_pickaxe:839925697463582792>", "star pickaxe (fragile)", "mythic", None, 125000, 5000,
            "A pickaxe created from the gem of the star. Unfortunately, it can't stand against extreme heat, and will break if brought into the Nether."],
        "star_pickaxe": ["<:star_pickaxe:839930221314834483>", "star pickaxe", "mythic+", None, 150000, 7500,
            "A pickaxe created from the gem of the star, enhanced by the metal of the underworld. It can now stand against any kind of heat."],
        "fragile_star_axe": ["", "star axe (fragile)", "mythic", None, 125000, 5000,
            "An axe created from the gem of the star. Unfortunately, it can't stand against extreme heat, and will break if brought into the Nether."],
        "star_axe": ["", "star axe", "mythic+", None, 150000, 7500,
            "An axe created from the gem of the star, enhanced by the metal of the underworld. It can now stand against any kind of heat."],
        

        # General purpose materials
        "coal": ["<:coal:819742286250377306>", "coal", "common", 15, 10, None,
            "A mysterious dark object used for fuel."],
        "apple": ["🍎", "apple", "common", 10, 8, None,
            "An apple. Yummy. Watch out for the worms though."],
        "flower": ["🌸", "flower", "common", 11, 8, None,
            "A beautiful flower."],
        "moyai": ["🌺", "moyai", "???", None, None, None,
            "A mysterious mystical flower. It is unknown what this flower truly is."],
        "string": ["<:string:820758307542401055>", "string", "common", 15, 10, None,
            "A useful drop for brewing potions."],
        "spider_eye": ["<:spider_eye:820758868468301864>", "spider eye", "uncommon", 35, 25, None,
            "An uncommon drop for brewing potions."],
        "bone": ["<:bone2:828133597529374720>", "bone", "common", None, 20, None,
            "A common drop from skeletons. Hopefully it has some uses."],
        "zombie_meat": ["<:zombie_meat:828133597659529276>", "rotten flesh", "common", None, 20, None,
            "A common drop from zombies. Don't eat it."],
        "gunpowder": ["<:gunpowder:821528688646160395>", "gunpowder", "uncommon", 50, 30, None,
            "An uncommon drop for some uhh __minor__ terrorism purposes."],
        "magma_cream": ["<:magma_cream:823593239683924038>", "magma cream", "common", 30, 25, None,
            "A common drop for brewing potions."],
        "blaze": ["<:blaze_rod:826150261906472960>", "blaze rod", "uncommon", None, 50, None,
            "An uncommon drop for brewing potions."],
        "nether_star": ["<:nether_star:828135277351534592>", "nether star", "legendary", None, None, None,
            "A legendary drop from a monster that can only be challenged with the sword created from its origin."],
        
        # Potions
        "luck_potion": ["<a:luck_potion:826871436769493062>", "luck potion", "rare+", 100000, 1000, 10,
            "May the luck be with you."],
        "fire_potion": ["<a:fire_potion:828135033466126366>", "fire potion", "rare", 10000, 100, 10,
            "Reduce the chance of dying in the Nether."],
        "haste_potion": ["<a:haste_potion:828135803812577330>", "haste potion", "rare+", 120000, 2000, 10,
            "Increase loot yield from a mining session. This potion's stack affects the loot yield rate."],
        "looting_potion": ["<a:looting_potion:841783868860399719>", "looting potion", "rare+", 120000, 2000, 10,
            "Increase loot yield from adventuring. This potion's stack affects the loot yield rate."],
        "bland_potion": ["<:bland_potion:882679421356630116>", "bland potion", "common", 1000, 10, 1,
            "Erase all potions effects. Why would you need that?"],
        "undying_potion": ["<:undying_potion:828136854657826836>", "undying potion", "???", None, None, 10000000,
            "To achieve immortal, one simply requires many many sacrifices."]
    }

def get_badge_info():
    return {
        "log1": ["🕛", "the beginning",
            "A decorative badge. Earned from having a log in your inventory."],
        "stone1": ["<:stone_pickaxe:820044330613866497>", "upgrade people, upgrade",
            "A decorative badge. Earned from having a Stone Pickaxe in your inventory."],
        "iron1": ["<:iron:820009715286671410>", "metal",
            "A decorative badge. Earned from having an iron in your inventory."],
        "diamond1": ["💎", "diamond!",
            "A decorative badge. Earned from having a diamond in your inventory."],
        "nether1": ["🔥", "hellfire",
            "A decorative badge. Earned from entering the Nether."],
        "debris1": ["<:debris:823622624118702081>", "hidden in the depth",
            "A decorative badge. Earned from getting Ancient Debris."],
        "netherite1": ["<:netherite:828129193275293706>", "restoration",
            "A decorative badge. Earned from crafting Netherite."],

        "wooden_age": ["🪵", "wooden age",
            "After chopping quite an amount of logs, the merchant decides to buy your wood for a higher price."],
        "stone_age": ["<:stone:819728758160097290>", "stone age",
            "There's a shortage of stone ~~definitely not caused by you~~, so stone sell's price is increased."],
        "iron_age": ["<:iron:820009715286671410>", "iron age",
            "Everyone wants iron. With that in mind, you now sell it for even a higher price."],
        "diamond2": ["🍀", "oh shiny!",
            "After mining quite an amount of diamonds, you now know the strategy to greatly improve your chance of finding diamonds."],
        "netherite2": ["<:netherite:828129193275293706>", "heavy metals",
            "After obtaining quite an amount of netherites, you now know the strategy to greatly improve your chance of finding ancient debris."]
    }

def get_world(world : int) -> str:
    if world == 0:
        return "Overworld"
    elif world == 1:
        return "Nether"
    elif world == 2:
        return "Space"

async def get_friendly_reward(conn, reward : dict, emote : bool = None) -> str:
    msg = ""
    for key in reward:
        if reward[key] != 0:
            item = await DB.Items.get_item(conn, key)
            if item is not None:
                if emote is True:
                    msg += f"{item['emoji']} x {reward[key]}, "
                elif emote is False:
                    msg += f"{reward[key]}x **{acapitalize(item['name'])}**, "
                else:
                    msg += f"{item['emoji']} {reward[key]}x *{acapitalize(item['name'])}*, "
    
    # Remove ', '
    msg = msg[:-2]
    return msg

def get_mine_loot(pick : str, world : int):
    if world == 0:
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
                "stone": 0.40, # 4 on average
                "coal": 0.30, # 3 on average
                "iron": 0.10, # 1 on average
                "redstone": 0.10, # 1 on average
                "diamond": 0.01, # 0.1 on average
                "rolls": 10
            }
        elif pick == "diamond_pickaxe":
            return {
                "stone": 0.40, # 8 on average
                "coal": 0.30, # 6 on average
                "iron": 0.12, # 2.4 on average
                "redstone": 0.10, # 2 on average
                "diamond": 0.01, # 0.2 on average
                "obsidian": 0.05, # 1 on average
                "rolls": 20
            }
        elif pick == "nether_pickaxe":
            return {
                "stone": 0.38, # 9.5 on average
                "coal": 0.25, # 6.25 on average
                "iron": 0.15, # 3.75 on average
                "redstone": 0.15, # 3.75 on average
                "diamond": 0.02, # 0.5 on average
                "obsidian": 0.05, # 1.25 on average
                "rolls": 25
            }
        elif "star_pickaxe" in pick:
            return {
                "stone": 0.38, # 9.5 on average
                "coal": 0.25, # 6.25 on average
                "iron": 0.15, # 3.75 on average
                "redstone": 0.15, # 3.75 on average
                "diamond": 0.02, # 0.5 on average
                "obsidian": 0.05, # 1.25 on average
                "rolls": 50
            }
    elif world == 1:
        if pick == "wood_pickaxe":
            return {
                "netherrack": 0.99, # 2.97 on average
                "gold": 0.01, # 0.03 on average
                "rolls": 3
            }
        elif pick == "stone_pickaxe":
            return {
                "netherrack": 0.99, # 7.92 on average
                "gold": 0.01, # 0.08 on average
                "rolls": 8
            }
        elif pick == "iron_pickaxe":
            return {
                "netherrack": 0.98, # 9.8 on average
                "gold": 0.02, # 0.2 on average
                "rolls": 10
            }
        elif pick == "diamond_pickaxe":
            return {
                "netherrack": 0.96, # 19.2 on average
                "gold": 0.02, # 0.4 on average
                "obsidian": 0.005, # 0.1 on average
                "debris": 0.001, # 0.02 on average
                "rolls": 20
            }
        elif pick == "nether_pickaxe":
            return {
                "netherrack": 0.93, # 23.25 on average
                "gold": 0.05, # 1.25 on average
                "obsidian": 0.005, # 0.125 on average
                "debris": 0.001, # 0.025 on average
                "rolls": 25
            }
        elif pick == "star_pickaxe":
            return {
                "netherrack": 0.93, # 46.5 on average
                "gold": 0.05, # 2.5 on average
                "obsidian": 0.01, # 0.5 on average
                "debris": 0.002, # 0.1 on average
                "rolls": 50
            }
    elif world == 2:
        if pick == "wood_pickaxe":
            return {
                "moonstone": 0.2, # 0.6 on average
                "rolls": 3
            }
        elif pick == "stone_pickaxe":
            return {
                "moonstone": 0.2, # 1.6 on average
                "rolls": 8
            }
        elif pick == "iron_pickaxe":
            return {
                "moonstone": 0.5, # 5 on average
                "rolls": 10
            }
        elif pick == "diamond_pickaxe":
            return {
                "moonstone": 0.5, # 10 on average
                "obsidian": 0.2, # 4 on average
                "star_fragment": 0.0001, # 0.002 on average
                "rolls": 20
            }
        elif pick == "nether_pickaxe":
            return {
                "moonstone": 0.7, # 17.5 on average
                "obsidian": 0.2, # 5 on average
                "star_fragment": 0.0005, # 0.0125 on average
                "rolls": 25
            }
        elif "star_pickaxe" in pick:
            return {
                "moonstone": 0.5, # 25 on average
                "obsidian": 0.4, # 20 on average
                "star_fragment": 0.001, # 0.05 on average
                "rolls": 50
            }
    return None

def get_chop_loot(axe : str, world : int):
    if world == 0:
        if axe == "wood_axe":
            return {
                "log": 1, # 3 guaranteed
                "rolls": 3
            }
        elif axe == "stone_axe":
            return {
                "log": 0.80, # 5.6 on average
                "stick": 0.01, # 1.4 on average
                "apple": 0.19, # 1.33 on average
                "rolls": 7
            }
        elif axe == "iron_axe":
            return {
                "log": 0.70, # 7 on average
                "stick": 0.05, # 0.5 on average
                "apple": 0.15, # 1.5 on average
                "flower": 0.10, # 1 on average
                "rolls": 10
            }
        elif axe == "diamond_axe":
            return {
                "log": 0.45, # 9 on average
                "stick": 0.05, # 1 on average
                "apple": 0.25, # 5 on average
                "flower": 0.19, # 3.8 on average
                "moyai": 0.000000005, # 0.0000001 on average
                "rolls": 20
            }
        elif axe == "nether_axe":
            return {
                "log": 0.50, # 12.5 on average
                "stick": 0.05, # 1.25 on average
                "apple": 0.20, # 5 on average
                "flower": 0.15, # 3.75 on average
                "moyai": 0.00000001, # 0.00000025 on average
                "rolls": 25
            }
        elif "star_axe" in axe:
            return {
                "log": 0.50, # 25 on average
                "stick": 0.05, # 2.5 on average
                "apple": 0.20, # 10 on average
                "flower": 0.15, # 7.5 on average
                "moyai": 0.000001, # 0.00005 on average
                "rolls": 50
            }
    elif world == 1:
        if axe == "wood_axe":
            return {
                "log": 0.5, # 1.5 on average
                "rolls": 3
            }
        elif axe == "stone_axe":
            return {
                "log": 0.50, # 3.5 on average
                "rolls": 7
            }
        elif axe == "iron_axe":
            return {
                "log": 0.50, # 5 on average
                "rolls": 10
            }
        elif axe == "diamond_axe":
            return {
                "log": 0.40, # 8 on average
                "rolls": 20
            }
        elif axe == "nether_axe":
            return {
                "log": 0.50, # 12.5 on average
                "rolls": 25
            }
        elif axe == "star_axe":
            return {
                "log": 0.50, # 25 on average
                "rolls": 50
            }
    return None

def get_adventure_loot(sword : str, world : int):
    if world == 0:
        if sword == "wood_sword":
            return {
                "zombie_meat": 0.30,  # 0.9 on average
                "rolls": 3
            }
        elif sword == "stone_sword":
            return {
                "string": 0.25, # 1.25 on average
                "spider_eye": 0.05, # 0.25 on average
                "zombie_meat": 0.30, # 1.5 on average
                "bone": 0.30, # 1.5 on average
                "rolls": 5
            }
        elif sword == "iron_sword":
            return {
                "string": 0.20, # 2 on average
                "spider_eye": 0.10, # 1 on average
                "zombie_meat": 0.30, # 3 on average
                "bone": 0.30, # 3 on average
                "gunpowder": 0.05, # 0.5 on average
                "pearl": 0.01, # 0.1 on average
                "rolls": 10
            }
        elif sword == "diamond_sword":
            return {
                "string": 0.20, # 4 on average
                "spider_eye": 0.15, # 3 on average
                "zombie_meat": 0.25, # 5 on average
                "bone": 0.25, # 5 on average
                "gunpowder": 0.10, # 2 on average
                "pearl": 0.05, # 1 on average
                "rolls": 20
            }
        elif sword == "nether_sword":
            return {
                "string": 0.25, # 6.25 on average
                "spider_eye": 0.15, # 3.75 on average
                "zombie_meat": 0.20, # 5 on average
                "bone": 0.20, # 5 on average
                "gunpowder": 0.15, # 3.75 on average
                "pearl": 0.05, # 1.25 on average
                "rolls": 25
            }
        elif "star_sword" in sword:
            return {
                "string": 0.20, # 10 on average
                "spider_eye": 0.20, # 10 on average
                "zombie_meat": 0.20, # 10 on average
                "bone": 0.20, # 10 on average
                "gunpowder": 0.10, # 5 on average
                "pearl": 0.10, # 5 on average
                "rolls": 50
            }
    elif world == 1:
        if sword == "wood_sword":
            return {
                "magma_cream": 0.50, # 1 on average
                "gunpowder": 0.005, # 0.01 on average
                "rolls": 2
            }
        elif sword == "stone_sword":
            return {
                "magma_cream": 0.50, # 2.5 on average
                "gunpowder": 0.10, # 0.5 on average
                "rolls": 5
            }
        elif sword == "iron_sword":
            return {
                "magma_cream": 0.50, # 5 on average
                "coal": 0.10, # 1 on average
                "gunpowder": 0.10, # 1 on average
                "blaze": 0.01, # 0.1 on average
                "pearl": 0.01, # 0.1 on average
                "rolls": 10
            }
        elif sword == "diamond_sword":
            return {
                "magma_cream": 0.25, # 5 on average
                "zombie_meat": 0.25, # 5 on average
                "bone": 0.20, # 4 on average
                "coal": 0.05, # 1 on average
                "gunpowder": 0.10, # 2 on average
                "blaze": 0.02, # 0.4 on average,
                "pearl": 0.10, # 2 on average
                "rolls": 20
            }
        elif sword == "nether_sword":
            return {
                "magma_cream": 0.20, # 5 on average
                "zombie_meat": 0.20, # 5 on average
                "bone": 0.20, # 5 on average
                "coal": 0.10, # 2.5 on average
                "gunpowder": 0.05, # 1.25 on average
                "blaze": 0.05, # 1.25 on average
                "pearl": 0.10, # 2.5 on average
                "nether_star": 0.001, # 0.025 on average
                "rolls": 25
            }
        elif sword == "star_sword":
            return {
                "magma_cream": 0.15, # 7.5 on average
                "zombie_meat": 0.15, # 7.5 on average
                "bone": 0.20, # 10 on average
                "coal": 0.10, # 5 on average
                "gunpowder": 0.03, # 1.5 on average
                "blaze": 0.17, # 8.5 on average
                "pearl": 0.10, # 5 on average
                "nether_star": 0.001, # 0.05 on average
                "rolls": 50
            }
    elif world == 2:
        if sword == "wood_sword":
            return {
                "pearl": 0.1, # 0.3 on average
                "rolls": 3
            }
        elif sword == "stone_sword":
            return {
                "pearl": 0.2, # 1.6 on average
                "rolls": 8
            }
        elif sword == "iron_sword":
            return {
                "pearl": 0.5, # 5 on average
                "rolls": 10
            }
        elif sword == "diamond_sword":
            return {
                "pearl": 0.75, # 15 on average
                "space_orb": 0.0001, # 0.002 on average
                "rolls": 20
            }
        elif sword == "nether_sword":
            return {
                "pearl": 0.75, # 18.75 on average
                "space_orb": 0.0005, # 0.0125 on average
                "rolls": 25
            }
        elif "star_sword" in sword:
            return {
                "pearl": 0.50, # 25 on average
                "space_orb": 0.001, # 0.05 on average
                "rolls": 50
            }
    return None

def get_mine_msg(type : str, world : int, reward_string : str = "") -> str:
    """
    Get the random message for a mining session.

    Parameters:
    - `type`: The type of message you want. Acceptable are `reward`, `empty`/`nothing`, or `die`.
    - `world`: The world the user is in.
    - `reward_string`: The reward under the form of string obtained using `get_friendly_reward`. Can be ignored if `type` is not `reward`.
    """

    messages = None
    if type == "reward":
        if world == 0:
            messages = [
                f"You went mining and got {reward_string}.",
                f"You went to some caves and got out with {reward_string}.",
                f"You visited an abandoned mineshaft and stole {reward_string} from there."
            ]
        elif world == 1:
            messages = [
                f"You went mining and got {reward_string}.",
                f"You strip-mined for debris and got {reward_string}."
            ]
        elif world == 2:
            messages = [
                f"You went mining and got {reward_string}."
            ]
    elif type == "empty" or type == "nothing":
        if world == 0:
            messages = [
                "You went mining in a happy day, but you got nothing, so it was a bad day.",
                "You thought you'd get some diamonds, but it turned out to be just you being color blinded.",
                "You went mining some resources, but somebody decided to put a Curse of Greedy on you and thus you got nothing but dust."
            ]
        elif world == 1:
            messages = [
                "You went to mine, hoping for something, but you just got tons of netherrack, so you threw them all away."
            ]
        elif world == 2:
            messages = [
                "You didn't feel like mining these endless stone, so you just took a day off.",
                "You went mining, but you only got moon stones, so you gave up."
            ]
    elif type == "die":
        if world == 0:
            messages = [
                "You went mining in a ravine, but a creeper went kamikaze so you died. Don't go to a ravine.",
                "You digged into a nest of cave spiders and died horrifically.",
                "You decided to go sicko mode and digged straight down. It didn't end well."
            ]
        elif world == 1:
            messages = [
                "Your pickaxe was too good that you accidentally mined into a lava pocket and died miserably.",
                "The ghast shot you just right after you went up from your mine, effectively killed you.",
                "You slept.",
                "You bed-mined and died from *fire, hellfire*."
            ]
        elif world == 2:
            messages = [
                "You didn't pay attention to the Y-coord so you fell into the Void.",
                "You looked at an enderman and he owned you so hard while you only had your pickaxe.",
                "The elytra broke midway through the Void while you were trying to reach your mine.",
                "You mined straight down, but you forgot there are no bedrocks at the bottom."
            ]
    
    return random.choice(messages)

def get_chop_msg(type : str, world : int, reward_string : str = "") -> str:
    messages = None
    if type == "reward":
        if world == 0:
            messages = [
                f"You went chop some trees and got {reward_string}.",
                f"You chopped down some villager's houses to got {reward_string} because you hate them.",
                f"You went *deforestation*, which is by the way, *illegal*, to get {reward_string}."
            ]
        elif world == 1:
            messages = [
                f"You went chop some trees and got {reward_string}."
            ]
    elif type == "empty" or type == "nothing":
        if world == 0:
            messages = [
                "You were distracted by the butterflies so you did nothing.",
                "You felt sorry for the villagers somehow so you spared their homes.",
                "You were bored today so you didn't go chopping despite the command telling so."
            ]
        elif world == 1:
            messages = [
                "You were scared of the hoglins so you quitted chopping for a while.",
                "You didn't like the wood in the Nether. Why discriminate them?",
            ]
    elif type == "die":
        if world == 0:
            messages = [
                "You didn't see a creeper creeping behind you so you died.",
                "You got owned by the Iron Golem while destroying the houses. Rip equipments.",
                "You got the logs, but while navigating through the forest, you fell down a hidden ravine and died."
            ]
        elif world == 1:
            messages = [
                "You were chopping some trees, but a hoglin knocked you off the cliff so you died.",
                "You forgot to wear golden boots (*psst, they don't exist*).",
                "You looked at the enderman in the forest full of enderman."
            ]

    return random.choice(messages)

def get_adventure_msg(type : str, world : int, reward_string : str = "") -> str:
    messages = None
    if type == "reward":
        if world == 0:
            messages = [
                f"You went on an adventure and got {reward_string}.",
                f"You slayed some monsters and got {reward_string}.",
                f"You stole some villagers' chests to get {reward_string}."
            ]
        elif world == 1:
            messages = [
                f"You looted some bastion and got {reward_string}.",
                f"You went to a fortress and got {reward_string}. Spooky."
            ]
        elif world == 2:
            messages = [
                f"You killed some endermen and got {reward_string}."
            ]
    elif type == "empty" or type == "nothing":
        if world == 0:
            messages = [
                "You slept.",
                "You were a little bit sick, so you didn't really feel going on an adventure.",
                "You feared that you'd lose your house, so you didn't leave it for now."
            ]
        elif world == 1:
            messages = [
                "You decided to take a day off from walking in literal hell.",
                "You were afraid of the bastion so you listened to the OST instead.",
                "You were not confident walking around without a golden helmet, so you stayed in a 2x2 pit."
            ]
        elif world == 2:
            messages = [
                "You were sleepy while in space so you took a break.",
                "Luckily, the enderman are passive, so you took a break instead of killing them."
            ]
    elif type == "die":
        if world == 0:
            messages = [
                "A creeper jumped out of nowhere and went kamikaze. It was very effective.",
                "You smacked an Iron Golem while visiting a village, only to get smacked by it *hard*.",
                "While doing some sick parkour, you fell into a ravine and died."
            ]
        elif world == 1:
            messages = [
                "You were tired, so you slept. It was not a wise decision.",
                "While doing some sick parkour and block clutches, your mouse died midway, dragging you with it.",
                "The strider decided to die while you were riding on it.",
                "You tried to raid a bastion, only to get raided by Brute Piglins."
            ]
        elif world == 2:
            messages = [
                "You looked at an enderman and died from its gaze."
            ]
    
    return random.choice(messages)

def get_daily_loot(streak : int):
    if streak < 10:
        return {
            "log": random.randint(2, 5),
            "wood": random.randint(0, 3),
            "stick": random.randint(1, 4)
        }
    elif streak < 51:
        return {
            "log": random.randint(10, 20),
            "stone": random.randint(10, 15),
            "coal": random.randint(5, 10)
        }
    elif streak < 101:
        return {
            "log": random.randint(50, 70),
            "stone": random.randint(30, 45),
            "iron": random.randint(10, 30),
            "diamond": random.randint(0, 1)
        }
    elif streak < 201:
        return {
            "log": random.randint(100, 150),
            "stone": random.randint(100, 150),
            "iron": random.randint(50, 70),
            "diamond": random.randint(10, 12),
            "debris": random.randint(0, 1)
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
        "wood_sword": {
            "wood": 2,
            "stick": 1,
            "quantity": 1
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
        "stone_sword": {
            "stone" : 2,
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
        "iron_sword": {
            "iron": 2,
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
        "diamond_sword": {
            "diamond": 2,
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
        "anvil": {
            "iron": 31,
            "quantity": 1
        },
        "nether": {
            "obsidian": 10,
            "quantity": 1
        },
        "netherite": {
            "debris": 4,
            "gold": 4,
            "coal": 1,
            "quantity": 1
        },
        "nether_sword": {
            "diamond_sword": 1,
            "netherite": 1,
            "anvil": 1,
            "quantity": 1
        },
        "nether_pickaxe": {
            "diamond_pickaxe": 1,
            "netherite": 1,
            "anvil": 1,
            "quantity": 1
        },
        "nether_axe": {
            "diamond_axe": 1,
            "netherite": 1,
            "anvil": 1,
            "quantity": 1
        },
        "end": {
            "nether_star": 4,
            "quantity": 1
        },
        "ender_eye": {
            "pearl": 2,
            "blaze": 1,
            "quantity": 2
        },
        "star_gem": {
            "space_orb": 4,
            "star_fragment": 4,
            "quantity": 1
        },
        "fragile_star_sword": {
            "diamond_sword": 1,
            "star_gem": 1,
            "quantity": 1
        },
        "star_sword": {
            "fragile_star_sword": 1,
            "netherite": 50,
            "star_gem": 1,
            "anvil": 1,
            "quantity": 1
        },
        "fragile_star_pickaxe": {
            "diamond_pickaxe": 1,
            "star_gem": 1,
            "quantity": 1
        },
        "star_pickaxe": {
            "fragile_star_pickaxe": 1,
            "netherite": 50,
            "star_gem": 1,
            "anvil": 1,
            "quantity": 1
        },
        "fragile_star_axe": {
            "diamond_axe": 1,
            "star_gem": 1,
            "quantity": 1
        },
        "star_axe": {
            "fragile_star_axe": 1,
            "netherite": 50,
            "star_gem": 1,
            "anvil": 1,
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

def get_brew_ingredient(item : str):
    # All potions have the following base ingredients:
    # redstone: 32
    # spider_eye: 16
    # gunpowder: 32
    # coal: 32
    # blaze 1

    brew_recipe = {
        "luck_potion": {
            "flower": 64,
            "string": 32,

            "redstone": 32,
            "spider_eye": 32,
            "gunpowder": 32,
            "coal": 64,
            "blaze": 2,

            "money": 10000,
            "quantity": 1
        },
        "fire_potion": {
            "magma_cream": 128,

            "redstone": 32,
            "spider_eye": 16,
            "gunpowder": 32,
            "coal": 32,
            "blaze": 1,

            "money": 1000,
            "quantity": 1
        },
        "haste_potion": {
            "nether_star": 1,

            "redstone": 32,
            "spider_eye": 32,
            "gunpowder": 32,
            "coal": 64,
            "blaze": 2,

            "money": 10000,
            "quantity": 1
        },
        "looting_potion": {
            "nether_star": 1,

            "redstone": 32,
            "spider_eye": 32,
            "gunpowder": 64,
            "coal": 32,
            "blaze": 2,

            "money": 10000,
            "quantity": 1
        },
        "undying_potion": {
            "moyai": 1,
            "zombie_meat": 100000,
            "bone": 100000,
            "diamond": 10000,
            "netherite": 1000,

            "redstone": 100000,
            "spider_eye": 100000,
            "gunpowder": 100000,
            "coal": 100000,
            "blaze": 100000,

            "money": 100000000,
            "quantity": 1
        }
    }

    if item is None:
        return brew_recipe
    else:
        return brew_recipe.get(item)