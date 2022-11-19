# Safe Inventory

Since the 0.1.20 update just dropped, this will briefly describe the new system of **safe inventory**.

## Characteristics

Safe inventory, as the name implied, is a separate area of your inventory where it'll be safe from being removed. This is mostly the concern when you dies, your inventory is decreased by an amount of %. Safe inventory will stores some items, and these items won't be removed through normal means, like `market sell` or `trade`.

## Shulker Box

Safe inventory is directly related to the new legendary item, **Shulker Box**. As a special legendary item, **it can't be removed by any means** (except via manual database manipulation). When entering the End the first time, you'll be given 3 shulker boxes. **It can't be multiplied**, which renders multiplier potions such as *Nature Potion* useless, although reroll potions such as *Haste Potion* still boost its drop rate.

## How it works

If you look into the code without knowing how it works, it'll be confusing. I'll try to be a bit more clear here by using different wording than from the source code.

- The **number of shulker boxes in your main inventory** will be **the amount of unique items you can store inside the safe inventory.** 
    - For example, if you have 3 shulker boxes, you can store 3 different items inside the safe inventory. This will go up to **27 unique items.**
- For the first 27 shulker boxes, **for each unique items, you can store up to 50 of each items.** 
    - For example, let's say the 3 unique items are diamond, netherite, and nether star. You can store 50 each of these with 3 shulker boxes, so you can store up to 50 diamonds, 50 netherites, and 50 nether stars with 3 shulker boxes. If you get another shulker box and you want to store iron, you can store 50 diamonds, 50 netherites, 50 nether stars, and 50 irons with 4 shulker boxes, and so on, up to the 27th shulker box.
- Any extra shulker boxes will increase the amount of items you can store by 10.
    - For example, let's say you have 3 unique items (diamond, netherite, and nether star) and 27 shulker boxes. Any shulker boxes after that will raise the cap of 50 by 10. So 28 shulker boxes will let you store up to 60 diamonds, 60 netherites, and 60 nether star. 29 shulker boxes will let you store up to 70 diamonds, 70 netherites, and 70 nether star, and so on.

For an obvious reason, you can't store shulker boxes inside safe inventory.
