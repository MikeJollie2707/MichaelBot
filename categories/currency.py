import discord
from discord.ext import commands
import humanize

import datetime
import random
import typing # IntelliSense purpose only

import categories.utilities.db as DB
import categories.utilities.facility as Facility
import categories.utilities.loot as LootTable
from categories.utilities.converters import ItemConverter
from categories.utilities.checks import has_database
from categories.templates.navigate import Pages
from bot import MichaelBot # IntelliSense purpose only

class Currency(commands.Cog, command_attrs = {"cooldown_after_parsing" : True}):
    """Commands related to money."""
    def __init__(self, bot : MichaelBot):
        self.bot = bot
        self.emoji = '💰'
    
    async def cog_check(self, ctx : commands.Context):
        if isinstance(ctx.channel, discord.DMChannel):
            raise commands.NoPrivateMessage()
        if not has_database(ctx):
            raise commands.CheckFailure("Bot doesn't have database.")
        return True
    
    @commands.Cog.listener("on_member_join")
    async def _member_join(self, member):
        async with self.bot.pool.acquire() as conn:
            exist = await DB.User.find_user(conn, member.id)
            if exist is None:
                await DB.User.insert_user(conn, member)

    @commands.command(aliases = ['adv'])
    @commands.bot_has_permissions(external_emojis = True, read_message_history = True, send_messages = True)
    @commands.cooldown(rate = 1, per = 300.0, type = commands.BucketType.user)
    async def adventure(self, ctx : commands.Context):
        '''
        Go on an adventure to gather materials! 
        Watch out though, you might encounter unwanted enemies. Better bring a sword.

        **Aliases:** `adv`
        **Usage:** <prefix>**{command_name}** {command_signature}
        **Cooldown:** 5 minutes per 1 use (user)
        **Example:** {prefix}{command_name}

        **You need:** A sword.
        **I need:** `Use External Emojis`, `Read Message History`, `Send Messages`.
        '''
        
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                current_sword = await DB.Inventory.find_equip(conn, "sword", ctx.author.id)
                if current_sword is None:
                    await ctx.reply("You have no sword equip.", mention_author = False)
                    return
                
                loot = LootTable.get_adventure_loot(current_sword["item_id"])
                lower_bound = 0
                upper_bound = 0
                final_reward = {}
                for i in range(0, loot["rolls"]):
                    for reward in loot:
                        if reward != "rolls":
                            if reward not in final_reward:
                                final_reward[reward] = 0
                            upper_bound += loot[reward]
                            chance = random.random()
                            if chance >= lower_bound and chance < upper_bound:
                                final_reward[reward] += 1
                            
                            lower_bound = upper_bound
                    lower_bound = 0
                    upper_bound = 0
                
                message = await LootTable.get_friendly_reward(conn, final_reward)
                any_reward = False
                for reward in final_reward:
                    if final_reward[reward] != 0:
                        any_reward = True
                        await DB.Inventory.add(conn, ctx.author.id, reward, final_reward[reward])
                
                if any_reward:
                    await ctx.reply("You go on an adventure and get %s." % message, mention_author = False)
                else:
                    await ctx.reply("You go on an adventure but didn't get anything :(", mention_author = False)

    @commands.command(aliases = ['bal'])
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    @commands.cooldown(rate = 1, per = 2.0, type = commands.BucketType.user)
    async def balance(self, ctx : commands.Context):
        '''
        Display the amount of money you currently have.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Cooldown:** 2 seconds per 1 use (user)
        **Example:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Read Message History`, `Send Messages`.
        '''
        
        member_money = 0
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                member_money = await DB.User.get_money(conn, ctx.author.id)

        await ctx.reply("You have $%d." % member_money, mention_author = False)

    @commands.command()
    @commands.bot_has_permissions(external_emojis = True, read_message_history = True, send_messages = True)
    @commands.cooldown(rate = 1, per = 300.0, type = commands.BucketType.user)
    async def chop(self, ctx : commands.Context):
        '''
        Chop some trees.

        The majority of reward is log, although you can also find some other things with a better axe.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Cooldown:** 5 minutes per 1 use (user).
        **Example:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Use External Emojis`, `Read Message History`, `Send Messages`.
        '''

        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                current_axe = await DB.Inventory.find_equip(conn, "axe", ctx.author.id)
                if current_axe is None:
                    await ctx.reply("You have no axe equip.")
                    return
                
                loot = LootTable.get_chop_loot(current_axe["item_id"])
                world = await DB.User.get_world(conn, ctx.author.id)
                loot = LootTable.get_chop_loot(current_axe["item_id"], world)
                upper_bound = 0
                final_reward = {}
                for i in range(0, loot["rolls"]):
                    for reward in loot:
                        if reward != "rolls":
                            if reward not in final_reward:
                                final_reward[reward] = 0
                            upper_bound += loot[reward]
                            chance = random.random()
                            if chance >= lower_bound and chance < upper_bound:
                                final_reward[reward] += 1
                            
                            lower_bound = upper_bound
                    lower_bound = 0
                    upper_bound = 0
                
                message = await LootTable.get_friendly_reward(conn, final_reward)
                any_reward = False
                for reward in final_reward:
                    if final_reward[reward] != 0:
                        any_reward = True
                        await DB.Inventory.add(conn, ctx.author.id, reward, final_reward[reward])

                if any_reward:               
                    await ctx.reply("You go chopping trees and get %s." % message, mention_author = False)
                else:
                    await ctx.reply("You go chopping trees, but no tree was found :(", mention_author = False)
    
    @commands.group(invoke_without_command = True)
    @commands.bot_has_permissions(external_emojis = True, read_message_history = True, send_messages = True)
    async def craft(self, ctx : commands.Context, n : typing.Optional[int] = 1, *, item : ItemConverter):
        '''
        Perform a craft `n` times.
        This will give you `n * <quantity>` items, with `<quantity>` is the `You gain` section in `craft recipe`.

        Craft wisely!

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example 1:** {prefix}{command_name} 2 stick
        **Example 2:** {prefix}{command_name} wooden pickaxe

        **You need:** None.
        **I need:** `Use External Emojis`, `Read Message History`, `Send Messages`.
        '''

        if ctx.invoked_subcommand is None:
            if n <= 0:
                n = 1
            async with self.bot.pool.acquire() as conn:
                async with conn.transaction():
                    exist = await DB.Items.get_item(conn, item)
                    if exist is None:
                        await ctx.reply("This item doesn't exist. Please check `craft recipe` for possible crafting items.", mention_author = False)
                        return
                    
                    ingredient = LootTable.get_craft_ingredient(item)
                    if ingredient is None:
                        await ctx.reply("This item isn't craftable. Please check `craft recipe` for possible crafting items.", mention_author = False)
                        return
                    
                    # Perform a local transaction, and if it's valid, push to db.
                    fake_inv = {} # Dict {item: remaining_amount}
                    miss = {} # Dict {item: missing_amount}
                    for key in ingredient:
                        if key != "quantity":
                            # The item may not exist due to x0.
                            slot = await DB.Inventory.get_one_inventory(conn, ctx.author.id, key)
                            if slot is None:
                                fake_inv[key] = -(n * ingredient[key])
                            else:
                                fake_inv[key] = slot["quantity"] - n * ingredient[key]
                            
                            if fake_inv[key] < 0:
                                miss[key] = abs(fake_inv[key])
                    
                    if len(miss) == 0:
                        for key in fake_inv:
                            await DB.Inventory.update(conn, ctx.author.id, key, fake_inv[key])
                        await DB.Inventory.add(conn, ctx.author.id, item, n * ingredient["quantity"])
                        official_name = LootTable.acapitalize(exist["name"])
                        await ctx.reply(f"Crafted {n * ingredient['quantity']}x **{official_name}** successfully", mention_author = False)
                        
                    else:
                        miss_string = await LootTable.get_friendly_reward(conn, miss, False)
                        await ctx.reply("Missing the following items: %s" % miss_string, mention_author = False)

    @craft.command()
    @commands.bot_has_permissions(external_emojis = True, read_message_history = True, send_messages = True)
    async def recipe(self, ctx : commands.Context, *, item : ItemConverter = None):
        '''
        Recipe for an item or all the recipes.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example 1:** {prefix}{command_name} wood
        **Example 2:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Use External Emojis`, `Read Message History`, `Send Messages`.
        '''

        recipe = LootTable.get_craft_ingredient(item)

        if item is None:
            MAX_ITEMS = 4
            cnt = 0
            page = Pages()
            embed = None
            friendly_name = ""
            for key in recipe:
                if cnt == 0:
                    embed = Facility.get_default_embed(
                        title = "All crafting recipes",
                        timestamp = datetime.datetime.utcnow(),
                        author = ctx.author
                    )
                
                async with self.bot.pool.acquire() as conn:
                    friendly_name = await DB.Items.get_friendly_name(conn, key)
                
                    outp = recipe[key].pop("quantity", None)
                    embed.add_field(
                        name = LootTable.acapitalize(friendly_name),
                        value = "**Input:** %s\n**Output:** %s\n" % (await LootTable.get_friendly_reward(conn, recipe[key]), await LootTable.get_friendly_reward(conn, {key : outp})),
                        inline = False
                    )

                cnt += 1
                if cnt == MAX_ITEMS:
                    page.add_page(embed)
                    embed = None
                    cnt = 0
            # If the amount of items doesn't reach MAX_ITEMS.
            if embed is not None:
                page.add_page(embed)
            
            await page.event(ctx, interupt = False) 
        elif recipe is not None:
            async with self.bot.pool.acquire() as conn:
                friendly_name = await DB.Items.get_friendly_name(conn, item)
                outp = recipe.pop("quantity", None)
                embed = Facility.get_default_embed(
                    title = "%s's crafting recipe" % LootTable.acapitalize(friendly_name),
                    timestamp = datetime.datetime.utcnow(),
                    author = ctx.author
                ).add_field(
                    name = "Recipe:",
                    value = await LootTable.get_friendly_reward(conn, recipe),
                    inline = False
                ).add_field(
                    name = "Receive:",
                    value = await LootTable.get_friendly_reward(conn, {item : outp}),
                    inline = False
                )

            await ctx.reply(embed = embed, mention_author = False)
        else:
            await ctx.reply("This item doesn't exist.", mention_author = False)

    @commands.command()
    @commands.bot_has_permissions(external_emojis = True, read_message_history = True, send_messages = True)
    async def daily(self, ctx : commands.Context):
        '''
        Get an amount of money every 24h.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Use External Emojis`, `Read Message History`, `Send Messages`.
        '''

        # Retrieve user info
        # Check if his last daily is <24h
        # If yes then update money and increase streak,
        # otherwise, reset the streak

        too_early = False
        too_late = False
        old_streak = 0
        member = {}
        daily_amount = 100
        daily_bonus = 0

        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                member = await DB.User.find_user(conn, ctx.author.id)

                if member["last_daily"] is None:
                    member["last_daily"] = datetime.datetime.utcnow()
                elif datetime.datetime.utcnow() - member["last_daily"] < datetime.timedelta(hours = 24.0):
                    too_early = True
                elif datetime.datetime.utcnow() - member["last_daily"] >= datetime.timedelta(hours = 48.0):
                    old_streak = member["streak_daily"]
                    member["streak_daily"] = 0
                    too_late = True
                
                if not too_early:
                    # The daily amount is calculated as followed:
                    # - From streak 0 - 9: 100
                    # - From streak 10 - 99: 300 + (streak / 10) * 10
                    # - From streak 100 - 499: 500 + streak
                    # - From streak 500+: 1500 + streak * 2
                    # Note: The bonus is cap at $2000, so after streak 1000, it is not possible to increase.

                    if member["streak_daily"] < 10:
                        daily_amount = 100
                        daily_bonus = 0
                    elif member["streak_daily"] < 100:
                        daily_amount = 300
                        daily_bonus = int(member["streak_daily"] / 10) * 10
                    elif member["streak_daily"] < 500:
                        daily_amount = 500
                        daily_bonus = member["streak_daily"]
                    else:
                        daily_amount = 1500
                        daily_bonus = member["streak_daily"] * 2
                        if daily_bonus > 2000:
                            daily_bonus = 2000
                    
                    daily_amount += daily_bonus

                    member["last_daily"] = datetime.datetime.utcnow()
                    
                    await DB.User.inc_streak(conn, ctx.author.id)
                    await DB.User.add_money(conn, ctx.author.id, daily_amount)
                    await DB.User.update_last_daily(conn, ctx.author.id, member["last_daily"])

                    loot = LootTable.get_daily_loot(member["streak_daily"] + 1)
                    for key in loot:
                        await DB.Inventory.add(conn, ctx.author.id, key, loot[key])
         
        if too_early:
            remaining_time = datetime.timedelta(hours = 24) - (datetime.datetime.utcnow() - member["last_daily"])
            remaining_str = humanize.precisedelta(remaining_time, "seconds", format = "%0.0f")
            await ctx.reply(f"You still have {remaining_str} left before you can collect your daily.", mention_author = False)
        else:
            msg = ""
            if too_late:
                msg += "You didn't collect your daily for more than 24 hours, so your streak of `x%d` is reset :(\n" % old_streak
            
            if daily_bonus > 0:
                msg += f"You received an extra of **${daily_bonus}** for maintaining your streak.\n"
            async with self.bot.pool.acquire() as conn:
                msg += await LootTable.get_friendly_reward(conn, LootTable.get_daily_loot(member["streak_daily"])) + '\n'
            msg += f":white_check_mark: You got **${daily_amount}** daily money in total.\nYour streak: `x{member['streak_daily'] + 1}`.\n"

            await ctx.reply(msg, mention_author = False)
    
    @commands.command()
    @commands.bot_has_permissions(external_emojis = True, read_message_history = True, send_messages = True)
    @commands.cooldown(rate = 1, per = 5.0, type = commands.BucketType.user)
    async def equip(self, ctx : commands.Context, *, tool_name : ItemConverter):
        '''
        Equip either a pickaxe, an axe, a sword, or a fishing rod.

        `tool name` must be an item existed in your inventory.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example:** {prefix}{command_name} wooden pickaxe

        **You need:** None.
        **I need:** `Use External Emojis`, `Read Message History`, `Send Messages`.
        '''
        
        if tool_name is None:
            await ctx.reply("This item doesn't exist.", mention_author = False)
            return
        if "_pickaxe" not in tool_name and "_axe" not in tool_name and "_sword" not in tool_name and "_rod" not in tool_name:
            await ctx.reply(f"You can't equip this!", mention_author = False)
            return
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                exist = await DB.Items.get_item(conn, tool_name)
                if exist is None:
                    await ctx.reply(f"This tool does not exist.", mention_author = False)
                    return
                
                tool_type = ""
                if "_pickaxe" in tool_name:
                    tool_type = "pickaxe"
                elif "_axe" in tool_name:
                    tool_type = "axe"
                elif "_sword" in tool_name:
                    tool_type = "sword"
                elif "_rod" in tool_name:
                    tool_type = "rod"
                
                has_equipped = await DB.Inventory.find_equip(conn, tool_type, ctx.author.id)
                if has_equipped is not None:
                    await DB.Inventory.unequip_tool(conn, ctx.author.id, has_equipped["item_id"])
                await DB.Inventory.equip_tool(conn, ctx.author.id, tool_name)
                official_name = await DB.Items.get_friendly_name(conn, tool_name)
                await ctx.reply(f"Added {official_name} to main equipments.", mention_author = False)

    @commands.command(aliases = ['inv'])
    @commands.bot_has_permissions(external_emojis = True, read_message_history = True, send_messages = True)
    @commands.cooldown(rate = 1, per = 5.0, type = commands.BucketType.user)
    async def inventory(self, ctx : commands.Context):
        '''
        View your inventory. Sorted by amount.

        **Aliases:** `inv`.
        **Usage:** <prefix>**{command_name}** {command_signature}
        **Cooldown:** 5 seconds per 1 use (user).
        **Example:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Use External Emojis`, `Read Message History`, `Send Messages`.
        '''

        async with self.bot.pool.acquire() as conn:
            inventory = await DB.Inventory.get_whole_inventory(conn, ctx.author.id)
            if inventory is None or inventory == [None] * len(inventory):
                await ctx.reply("*Insert empty inventory here*", mention_author = False)
                return
            
            def _on_amount(slot):
                return -slot["quantity"]
            def _on_order(slot):
                item = LootTable.get_item_info()[slot["item_id"]]
                return item[1]
            inventory.sort(key = _on_amount)
            inventory.sort(key = _on_order)

            inventory_dict = {}
            for slot in inventory:
                inventory_dict[slot["item_id"]] = slot["quantity"]
            await ctx.reply(await LootTable.get_friendly_reward(conn, inventory_dict), mention_author = False)

    @commands.command()
    @commands.bot_has_permissions(external_emojis = True, read_message_history = True, send_messages = True)
    @commands.cooldown(rate = 1, per = 5.0, type = commands.BucketType.user)
    async def iteminfo(self, ctx : commands.Context, *, item : ItemConverter):
        '''
        Display an item's information.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Cooldown:** 5 seconds per 1 use (user)
        **Example:** {prefix}{command_name} diamond

        **You need:** None.
        **I need:** `Use External Emojis`, `Read Message History`, `Send Messages`.
        '''

        if item is not None:
            async with self.bot.pool.acquire() as conn:
                exist = await DB.Items.get_item(conn, item)
                if exist is None:
                    await ctx.reply("This item doesn't exist.", mention_author = False)
                    return
                
                desc = exist["description"]
                rarity = exist["rarity"]
                emote = exist["emoji"]
                friendly_name = exist["name"]

                craftable = LootTable.get_craft_ingredient(item)
                purchasable = await DB.Items.get_prices(conn, item)
                
                embed = Facility.get_default_embed(
                    title = f"{LootTable.acapitalize(friendly_name)}",
                    description = f"*{desc}*",
                    timestamp = datetime.datetime.utcnow(),
                    author = ctx.author
                ).add_field(
                    name = "Emoji:",
                    value = emote,
                ).add_field(
                    name = "Rarity:",
                    value = LootTable.acapitalize(rarity)
                )

                if craftable is not None:
                    out = craftable.pop("quantity")
                    embed.add_field(
                        name = "Recipe:",
                        value = f"{await LootTable.get_friendly_reward(conn, craftable)} -> {await LootTable.get_friendly_reward(conn, {item : out})}",
                        inline = False
                    )
                else:
                    embed.add_field(
                        name = "Recipe:",
                        value = "*Cannot be crafted.*",
                        inline = False
                    )
                
                price_str = f"Buy: {f'${purchasable[0]}' if purchasable[0] is not None else 'N/A'}\nSell: {f'${purchasable[1]}' if purchasable[1] is not None else 'N/A'}"
                embed.add_field(
                    name = "Prices:",
                    value = price_str,
                    inline = False
                )

            await ctx.reply(embed = embed, mention_author = False)
        else:
            await ctx.reply("This item does not exist.", mention_author = False)

    @commands.command()
    @commands.bot_has_permissions(external_emojis = True, read_message_history = True, send_messages = True)
    @commands.cooldown(rate = 1, per = 300.0, type = commands.BucketType.user)
    async def mine(self, ctx : commands.Context):
        '''
        Go mining to earn resources.

        You need to have a pickaxe equipped using the `equip` command.

        **Usage:** <prefix>**{command_name}**
        **Cooldown:** 5 minutes per 1 use (user).
        **Example:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Use External Emojis`, `Read Message History`, `Send Messages`.
        '''

        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                current_pick = await DB.Inventory.find_equip(conn, "pickaxe", ctx.author.id)
                if current_pick is None:
                    await ctx.reply("You have no pickaxe equip.", mention_author = False)
                    return
                
                loot = LootTable.get_mine_loot(current_pick["item_id"])
                lower_bound = 0
                upper_bound = 0
                final_reward = {}
                for i in range(0, loot["rolls"]):
                    for reward in loot:
                        if reward != "rolls":
                            if reward not in final_reward:
                                final_reward[reward] = 0
                            upper_bound += loot[reward]
                            chance = random.random()
                            if chance >= lower_bound and chance < upper_bound:
                                final_reward[reward] += 1
                            
                            lower_bound = upper_bound
                    lower_bound = 0
                    upper_bound = 0
                
                message = await LootTable.get_friendly_reward(conn, final_reward)
                any_reward = False
                for reward in final_reward:
                    if final_reward[reward] != 0:
                        any_reward = True
                        await DB.Inventory.add(conn, ctx.author.id, reward, final_reward[reward])
                
                if any_reward:
                    await ctx.reply("You go mining and get %s." % message, mention_author = False)
                else:
                    await ctx.reply("You go mining, but you didn't feel well so you left with nothing.", mention_author = False)
    
    @commands.command(aliases = ['lb'], hidden = True)
    @commands.cooldown(rate = 1, per = 5.0, type = commands.BucketType.member)
    async def topmoney(self, ctx : commands.Context, local__global = "local"):
        '''
        Show the top 10 users with the most amount of money.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Cooldown:** 5 seconds per 1 use (member)
        **Example 1:** {prefix}{command_name} global
        **Example 2:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Send Messages`.
        '''
        pass
    
    @commands.group(aliases = ['market'])
    @commands.bot_has_permissions(external_emojis = True, read_message_history = True, send_messages = True)
    @commands.cooldown(rate = 1, per = 5.0, type = commands.BucketType.user)
    async def trade(self, ctx : commands.Context):
        '''
        Display all items' value in terms of money.

        To buy or sell items, please use the command's subcommands.

        **Aliases:** `market`
        **Usage:** <prefix>**{command_name}** {command_signature}
        **Cooldown:** 5 seconds per 1 use (user)
        **Example:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Use External Emojis`, `Read Message History`, `Send Messages`.
        '''

        if ctx.invoked_subcommand is None:
            MAX_ITEMS = 4
            cnt = 0
            page = Pages()
            embed = None
            async with self.bot.pool.acquire() as conn:
                items = await DB.Items.get_whole_items(conn)
                for item in items:
                    if cnt == 0:
                        embed = Facility.get_default_embed(
                            title = "Market",
                            timestamp = datetime.datetime.utcnow(),
                            author = ctx.author
                        )
                    embed.add_field(
                        name = "%s **%s**" % (item["emoji"], LootTable.acapitalize(item["name"])),
                        value = "*%s*\n**Buy Price**: %s\n**Sell Price**: %s" % (item["description"], 
                                                                                "N/A" if item["buy_price"] is None else f"${item['buy_price']}",
                                                                                "N/A" if item["sell_price"] is None else f"${item['sell_price']}"),
                        inline = False
                    )
                    cnt += 1
                    if cnt == MAX_ITEMS:
                        page.add_page(embed)
                        embed = None
                        cnt = 0
                if embed is not None:
                    page.add_page(embed)
                await page.event(ctx, interupt = False)

    @trade.command()
    @commands.bot_has_permissions(external_emojis = True, read_message_history = True, send_messages = True)
    @commands.cooldown(rate = 1, per = 5.0, type = commands.BucketType.user)
    async def buy(self, ctx, amount : typing.Optional[int] = 1, *, item : ItemConverter):
        '''
        Buy an item with your money.
        Note that many items can't be bought.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Cooldown:** 5 seconds per 1 use (user)
        **Example 1:** {prefix}{command_name} wood
        **Example 2:** {prefix}{command_name} 10 wooden axe

        **You need:** None.
        **I need:** `Use External Emojis`, `Read Message History`, `Send Messages`.
        '''

        if item is None:
            await ctx.reply("This item doesn't exist. Please use `trade` to see all items.", mention_author = False)
            return
        if amount < 1:
            return
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                actual_item = await DB.Items.get_item(conn, item)
                if actual_item["buy_price"] is None:
                    await ctx.reply("This item is not purchasable!", mention_author = False)
                    return
                money = await DB.User.get_money(conn, ctx.author.id)
                if money - amount * actual_item["buy_price"] < 0:
                    await ctx.reply("You don't have enough money to buy. Total cost is: %d" % amount * actual_item["buy_price"], mention_author = False)
                    return
                
                await DB.User.remove_money(conn, ctx.author.id, amount * actual_item["buy_price"])
                await DB.Inventory.add(conn, ctx.author.id, item, amount)
                await ctx.reply(f"Bought {await LootTable.get_friendly_reward(conn, {item : amount}, False)} successfully.", mention_author = False)
            
    @trade.command()
    @commands.bot_has_permissions(external_emojis = True, read_message_history = True, send_messages = True)
    @commands.cooldown(rate = 1, per = 5.0, type = commands.BucketType.user)
    async def sell(self, ctx, amount : typing.Optional[int] = 1, *, item : ItemConverter):
        '''
        Sell items in your inventory for money.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Cooldown:** 5 seconds per 1 use (user)
        **Example 1:** {prefix}{command_name} diamond
        **Example 2:** {prefix}{command_name} 5 wooden pickaxe

        **You need:** None.
        **I need:** `Use External Emojis`, `Read Message History`, `Send Messages`.
        '''

        if item is None:
            await ctx.reply("This item doesn't exist. Please use `trade` to see all items.", mention_author = False)
            return
        if amount < 1:
            return
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                inv_slot = await DB.Inventory.get_one_inventory(conn, ctx.author.id, item)
                actual_item = await DB.Items.get_item(conn, item)
                if actual_item["sell_price"] is None:
                    await ctx.reply("This item cannot be sold.", mention_author = False)
                    return
                result = await DB.Inventory.remove(conn, ctx.author.id, item, amount)
                if result == "":
                    await ctx.reply("You don't have enough items to sell. You only have: %d" % inv_slot["quantity"] if inv_slot is not None else 0)
                    return
                await DB.User.add_money(conn, ctx.author.id, amount * actual_item["sell_price"])
                await ctx.reply(f"Sold {await LootTable.get_friendly_reward(conn, {item : amount}, False)} successfully for ${amount * actual_item['sell_price']}", mention_author = False)
                
    @commands.command(aliases = ['moveto', 'goto'])
    @commands.bot_has_permissions(external_emojis = True, read_message_history = True, send_messages = True)
    async def travelto(self, ctx, destination : str):
        '''
        Travel to another dimension.
        You can travel to either `Overworld` or `Nether` currently.

        **Aliases:** `moveto`, `goto`
        **Usage:** <prefix>**{command_name}** {command_signature}
        **Cooldown:** 1 day after 1 use (user)
        **Example:** {prefix}{command_name} nether

        **You need:** A Nether portal item.
        **I need:** `Use External Emojis`, `Read Message History`, `Send Messages`.
        '''

        dest = 0
        if destination.upper() == "OVERWORLD":
            dest = 0
        elif destination.upper() == "NETHER":
            dest = 1
        else:
            await ctx.reply("There's no such destination to travel!", mention_author = False)
            return
        
        async with self.bot.pool.acquire() as conn:
            user_info = await DB.User.find_user(conn, ctx.author.id)
            world = user_info["world"]
            if world == dest:
                await ctx.reply("You're already at %s." % LootTable.get_world(dest), mention_author = False)
                return
            
            if (dest == 1 and world == 0) or (dest == 0 and world == 1):
                user_inv = await DB.Inventory.get_one_inventory(conn, ctx.author.id, "nether")
            
            if user_inv is None:
                await ctx.reply("You don't have a portal to travel to this destination.", mention_author = False)
                return

            if user_info["last_move"] is not None:
                if datetime.datetime.utcnow() - user_info["last_move"] < datetime.timedelta(hours = 24.0):
                    remaining_time = datetime.timedelta(hours = 24) - (datetime.datetime.utcnow() - user_info["last_move"])
                    remaining_str = humanize.precisedelta(remaining_time, "seconds", format = "%0.0f")
                    await ctx.reply(f"You still have {remaining_str} left before you can travel again.", mention_author = False)
                    return
            if user_info["world"] == dest:
                await ctx.reply("Already at %s." % LootTable.get_world(dest), mention_author = False)
                return

            await DB.User.update_world(conn, ctx.author.id, dest)
            await DB.User.update_last_move(conn, ctx.author.id, datetime.datetime.utcnow())
            # Decrease portal durability here...

            await ctx.reply("Moved to %s." % LootTable.get_world(dest), mention_author = False)

def setup(bot : MichaelBot):
    bot.add_cog(Currency(bot))
