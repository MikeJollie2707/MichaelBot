import random
import utilities.loot as Loot

PICK_TYPE = "nether_sword"
WORLD = 2
SELECT_ITEM = "space_orb"
SIMULATION = 1000

# Assuming the best possible situation: 100% proc chance, constant 10 stacks.
EXTERNAL_BUFFS = []

roll_total = 0
item_total = 0

r = Loot.get_adventure_loot(PICK_TYPE, WORLD)
rolls = r.pop("rolls")
if "luck_potion" in EXTERNAL_BUFFS:
    rolls *= 10
reward = {}

for i in range(0, SIMULATION):
    for item in r:
        if reward.get(item) is None:
            reward[item] = 0
        for j in range(0, rolls):
            rng = random.random()
            if rng <= r[item]:
                reward[item] += 1
                item_total += 1

text = f'''
SIMULATION ENDED
================
Times: {SIMULATION}
Pickaxe type: {PICK_TYPE}
Reported item: {SELECT_ITEM}

Here is the full result: {reward}
In {SIMULATION} simulations, the number of items are {item_total}.
The ratio of {SELECT_ITEM} to total is {reward[SELECT_ITEM]} : {item_total}.
In terms of decimal, this is {(reward[SELECT_ITEM] / item_total) :.5f}, or {reward[SELECT_ITEM] / item_total * 100 :.2f}%.
'''

print(text)
