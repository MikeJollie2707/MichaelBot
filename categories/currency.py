import discord
from discord.ext import commands
import humanize

import datetime
import random
import typing # IntelliSense purpose only

import utilities.db as DB
import utilities.facility as Facility
import utilities.loot as LootTable
from utilities.converters import ItemConverter
from utilities.checks import has_database
from templates.navigate import Pages
from bot import MichaelBot # IntelliSense purpose only

DURABILITY_PENALTY = 0.05
DURABILITY_MAX_PENALTY = 100

NETHER_DIE = 0.025
OVERWORLD_DIE = 0.0125
MONEY_PENALTY_DIE = 0.10

LUCK_ACTIVATE_CHANCE = 0.5
FIRE_ACTIVATE_CHANCE = 0.25
HASTE_ACTIVATE_CHANCE = 0.75

NETHERITE_SURVIVE_CHANCE = 0.25

# Unused for now
POTION_STACK_MULTIPLIER = 1

# Pending functions that needs to be clean: craft (possible rework), daily

class Currency(commands.Cog, command_attrs = {"cooldown_after_parsing" : True}):
    """Commands related to money."""
    def __init__(self, bot : MichaelBot):
        self.bot = bot
        self.emoji = '💰'

    def __get_reward__(self, loot : dict, bonus_stack = 0) -> dict:
        """
        RNG the final reward, given a dictionary returned by `loot.get_..._loot()`.

        Parameter:
        - `loot`: A dictionary that dictates the drop chance. It must be returned by `loot.get_..._loot()`.
        - `bonus_stack`: An optional number indicates the stack of potions such as Haste and Looting.
        """
        rolls = loot.pop("rolls")
        final_reward = {}

        for reward in loot:
            if final_reward.get(reward) is None:
                final_reward[reward] = 0
            
            for i in range(0, rolls):
                chance = random.random()
                if chance <= loot[reward]:
                    final_reward[reward] += 1 + bonus_stack

        return final_reward
    
    async def __remove_equipments_on_die__(self, conn, member):
        """
        Remove equipments and `DEATH_PENALTY` of user's money.
        If the tool is netherite, there's a `NETHERITE_LOSE_CHANCE` chance it won't be removed.
        """
        equipment = await DB.User.ActiveTools.get_equipments(conn, member.id)
        for tool in equipment:
            # Netherite tools have a chance to not lose.
            if "nether_" in tool:
                rng = random.random()
                if rng <= NETHERITE_SURVIVE_CHANCE:
                    continue
            
            try:
                await DB.User.ActiveTools.unequip_tool(conn, member.id, tool["id"], False)
            except DB.ItemExpired:
                pass
        money = await DB.User.get_money(conn, member.id)
        await DB.User.remove_money(conn, member.id, int(money * MONEY_PENALTY_DIE))
    
    async def __attempt_fire__(self, conn, member):
        """
        Attempt to use fire potion.
        - If it is successfully used AND the fire pot is not expired, return `True`.
        - If it is successfully used AND the fire pot is expired, throw `DB.ItemExpired`.
        - If it is unsuccessful, return `False`.
        """
        has_fire_pot = await DB.User.ActivePotions.get_potion(conn, member.id, "fire_potion")
        use_fire = random.random()
        if use_fire <= FIRE_ACTIVATE_CHANCE and has_fire_pot is not None:
            await DB.User.ActivePotions.decrease_active_potion(conn, member.id, "fire_potion")
            return True
        else:
            return False

    async def __attempt_luck__(self, conn, member, loot):
        """
        Attempt to use luck potion.
        - If it is successful, `loot["rolls"]` will be modified.
            - If luck potion expires, throw `DB.ItemExpired`.
        - If it is not successful, nothing happen.
        """
        use_luck = random.random()
        if use_luck <= LUCK_ACTIVATE_CHANCE:
            is_luck = await DB.User.ActivePotions.get_potion(conn, member.id, "luck_potion")
            if is_luck is not None:
                loot["rolls"] += round(loot["rolls"] * await DB.User.ActivePotions.get_stack(conn, "luck_potion", is_luck["remain_uses"]) * POTION_STACK_MULTIPLIER)
                await DB.User.ActivePotions.decrease_active_potion(conn, member.id, "luck_potion")
    
    async def __attempt_haste__(self, conn, member):
        """
        Attempt to use haste potion.
        - If it is successful AND haste potion is not expired, return the number of stacks.
        - If it is successful AND haste potion is expired, throw `DB.ItemExpired`.
        - If it is not successful, return `0`.
        """
        use_haste = random.random()
        haste_stack = 0
        if use_haste <= HASTE_ACTIVATE_CHANCE:
            is_haste = await DB.User.ActivePotions.get_potion(conn, member.id, "haste_potion")
            if is_haste is not None:
                haste_stack = await DB.User.ActivePotions.get_stack(conn, "haste_potion", is_haste["remain_uses"]) * POTION_STACK_MULTIPLIER
                await DB.User.ActivePotions.decrease_active_potion(conn, member.id, "haste_potion")
            
        return haste_stack
    
    async def __reduce_tool_durability__(self, conn, member, current_tool):
        from math import ceil
        base_durability = (await DB.Items.get_item(conn, current_tool["id"]))["durability"]
        max_durability_loss = ceil(base_durability * DURABILITY_PENALTY)
        if max_durability_loss > DURABILITY_MAX_PENALTY:
            max_durability_loss = DURABILITY_MAX_PENALTY
        await DB.User.ActiveTools.dec_durability(conn, member.id, current_tool["id"], random.randint(1, max_durability_loss))
    
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
        
        # The code for `adventure()`, `chop()` should be identical for now.
        # Just copy and change some stuffs.

        message = ""
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                # Edit the name of the variable and the string argument.
                current_sword = await DB.User.ActiveTools.get_equipment(conn, "sword", ctx.author.id)
                if current_sword is None:
                    # Edit this message.
                    await ctx.reply("You have no sword equip.", mention_author = False)
                    ctx.command.reset_cooldown(ctx)
                    return
                
                world = await DB.User.get_world(conn, ctx.author.id)
                # Edit function name
                loot = LootTable.get_adventure_loot(current_sword["id"], world)
                
                die_chance = 0
                if world == 0:
                    die_chance = OVERWORLD_DIE
                elif world == 1:
                    die_chance = NETHER_DIE
                
                rng = random.random()
                # This section is ugly as fuck but I can't really do anything about this.
                die = False
                if rng <= die_chance:
                    if world == 1:
                        try:
                            # If no exception, then True/False, otherwise, it's False.
                            die = not (await self.__attempt_fire__(conn, ctx.author))
                            if not die:
                                message += "**Fire Potion** saved you from a cruel death.\n"
                        except DB.ItemExpired:
                            message += "**Fire Potion** saved you from a cruel death.\n"
                            message += "**Fire Potion** expired.\n"
                            die = False
                    else:
                        die = True
                                            
                if die:
                    await self.__remove_equipments_on_die__(conn, ctx.author)
                    
                    # Edit the function name
                    message += LootTable.get_adventure_msg("die", world)
                    await ctx.reply(message, mention_author = False)
                    return
                
                try:
                    await self.__attempt_luck__(conn, ctx.author, loot)
                except DB.ItemExpired:
                    message += "**Luck Potion** expired.\n"

                # A dict of {"item": amount}
                final_reward = self.__get_reward__(loot)
                
                reward_string = await LootTable.get_friendly_reward(conn, final_reward)
                any_reward = False
                for reward in final_reward:
                    if final_reward[reward] != 0:
                        any_reward = True
                        # Rewards are guaranteed to not be any of the tools/potions/portals.
                        await DB.User.Inventory.add(conn, ctx.author.id, reward, final_reward[reward])
                
                if any_reward:
                    try:
                        await self.__reduce_tool_durability__(conn, ctx.author, current_sword)
                    except DB.ItemExpired:
                        message += f"Your **{LootTable.acapitalize(current_sword['name'])}** broke after get adventure :(\n"
                    
                    # Edit function name.
                    await ctx.reply(message + LootTable.get_adventure_msg("reward", world, reward_string), mention_author = False)
                else:
                    # Edit function name.
                    await ctx.reply(message + LootTable.get_adventure_msg("empty", world), mention_author = False)
                    ctx.command.reset_cooldown(ctx)

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

        # The code for `adventure()`, `chop()` should be identical for now.
        # Just copy and change some stuffs.

        message = ""
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                # Edit the name of the variable and the string argument.
                current_axe = await DB.User.ActiveTools.get_equipment(conn, "axe", ctx.author.id)
                if current_axe is None:
                    # Edit this message.
                    await ctx.reply("You have no axe equip.", mention_author = False)
                    ctx.command.reset_cooldown(ctx)
                    return
                
                world = await DB.User.get_world(conn, ctx.author.id)
                # Edit function name
                loot = LootTable.get_chop_loot(current_axe["id"], world)
                
                die_chance = 0
                if world == 0:
                    die_chance = OVERWORLD_DIE
                elif world == 1:
                    die_chance = NETHER_DIE
                
                rng = random.random()
                # This section is ugly as fuck but I can't really do anything about this.
                die = False
                if rng <= die_chance:
                    if world == 1:
                        try:
                            # If no exception, then True/False, otherwise, it's False.
                            die = not (await self.__attempt_fire__(conn, ctx.author))
                            if not die:
                                message += "**Fire Potion** saved you from a cruel death.\n"
                        except DB.ItemExpired:
                            message += "**Fire Potion** saved you from a cruel death.\n"
                            message += "**Fire Potion** expired.\n"
                            die = False
                    else:
                        die = True
                            
                if die:
                    await self.__remove_equipments_on_die__(conn, ctx.author)
                    
                    # Edit the function name
                    message += LootTable.get_chop_msg("die", world)
                    await ctx.reply(message, mention_author = False)
                    return
                
                try:
                    await self.__attempt_luck__(conn, ctx.author, loot)
                except DB.ItemExpired:
                    message += "**Luck Potion** expired.\n"

                # A dict of {"item": amount}
                final_reward = self.__get_reward__(loot)
                
                reward_string = await LootTable.get_friendly_reward(conn, final_reward)
                any_reward = False
                for reward in final_reward:
                    if final_reward[reward] != 0:
                        any_reward = True
                        # Rewards are guaranteed to not be any of the tools/potions/portals.
                        await DB.User.Inventory.add(conn, ctx.author.id, reward, final_reward[reward])
                
                if any_reward:
                    try:
                        await self.__reduce_tool_durability__(conn, ctx.author, current_axe)
                    except DB.ItemExpired:
                        message += f"Your **{LootTable.acapitalize(current_axe['name'])}** broke after get adventure :(\n"
                    
                    # Edit function name.
                    await ctx.reply(message + LootTable.get_chop_msg("reward", world, reward_string), mention_author = False)
                else:
                    # Edit function name.
                    await ctx.reply(message + LootTable.get_chop_msg("empty", world), mention_author = False)
                    ctx.command.reset_cooldown(ctx)
    
    @commands.group(invoke_without_command = True)
    @commands.bot_has_permissions(external_emojis = True, read_message_history = True, send_messages = True)
    async def craft(self, ctx : commands.Context, amount : typing.Optional[int] = 1, *, item : ItemConverter):
        '''
        Craft up to `amount` items.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example 1:** {prefix}{command_name} 2 stick
        **Example 2:** {prefix}{command_name} wooden pickaxe

        **You need:** None.
        **I need:** `Use External Emojis`, `Read Message History`, `Send Messages`.
        '''

        if ctx.invoked_subcommand is None:
            if amount is None or amount <= 0:
                amount = 1
            async with self.bot.pool.acquire() as conn:
                async with conn.transaction():
                    exist = await DB.Items.get_item(conn, item)
                    if exist is None:
                        await ctx.reply("This item doesn't exist. Please check `craft recipe` for possible crafting items.", mention_author = False)
                        return
                    
                    # You can only craft one of each portal.
                    if exist["id"] == "nether" or exist["id"] == "end":
                        amount = 1
                        portals = await DB.User.ActivePortals.get_portals(conn, ctx.author.id)
                        if portals is not None:
                            for portal in portals:
                                if portal["name"] == exist["name"]:
                                    await ctx.reply("You already have this portal.", mention_author = False)
                                    return
                    
                    ingredient = LootTable.get_craft_ingredient(item)
                    if ingredient is None:
                        await ctx.reply("This item isn't craftable. Please check `craft recipe` for possible crafting items.", mention_author = False)
                        return
                    
                    times = amount // ingredient["quantity"]
                    if times == 0:
                        await ctx.reply("The minimum yield from crafting of this item is %d. Please check `craft recipe` to know more." % ingredient["quantity"], mention_author = False)
                        return
                    
                    # Perform a local transaction, and if it's valid, push to db.
                    fake_inv = {} # Dict {item: remaining_amount}
                    miss = {} # Dict {item: missing_amount}
                    for key in ingredient:
                        if key != "quantity":
                            # The item may not exist due to x0.
                            slot = await DB.User.Inventory.get_one_inventory(conn, ctx.author.id, key)
                            if slot is None:
                                fake_inv[key] = -(amount * ingredient[key])
                            else:
                                fake_inv[key] = slot["quantity"] - times * ingredient[key]
                            
                            if fake_inv[key] < 0:
                                miss[key] = abs(fake_inv[key])
                    
                    if len(miss) == 0:
                        for key in fake_inv:
                            await DB.User.Inventory.update_quantity(conn, ctx.author.id, key, fake_inv[key])
                        
                        # For portals, they need to be added right after crafting is finished.
                        if item == "nether" or item == "end":
                            await DB.User.ActivePortals.add(conn, ctx.author.id, item)
                        else:
                            await DB.User.Inventory.add(conn, ctx.author.id, item, times * ingredient["quantity"])
                        
                        official_name = LootTable.acapitalize(exist["name"])
                        await ctx.reply(f"Crafted {times * ingredient['quantity']}x **{official_name}** successfully", mention_author = False)
                        
                    else:
                        miss_string = await LootTable.get_friendly_reward(conn, miss, False)
                        await ctx.reply("Missing the following items: %s" % miss_string, mention_author = False)

    @craft.command(name = 'recipe')
    @commands.bot_has_permissions(external_emojis = True, read_message_history = True, send_messages = True)
    async def craft_recipe(self, ctx : commands.Context, *, item : ItemConverter = None):
        '''
        Show the recipe for an item or all the recipes.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example 1:** {prefix}{command_name} wood
        **Example 2:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Use External Emojis`, `Read Message History`, `Send Messages`.
        '''

        recipe = LootTable.get_craft_ingredient(item)

        if item is None:
            MAX_ITEMS = 4
            cnt = 0 # Keep track for MAX_ITEMS
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

    @commands.group(invoke_without_command = True)
    @commands.bot_has_permissions(external_emojis = True, read_message_history = True, send_messages = True)
    async def brew(self, ctx : commands.Context, amount : typing.Optional[int] = 1, *, potion : ItemConverter):
        '''
        Brew potion.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example:** {prefix}{command_name} luck potion

        **You need:** None.
        **I need:** `Use External Emojis`, `Read Message History`, `Send Messages`.
        '''

        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                exist = await DB.Items.get_item(conn, potion)
                if exist is None:
                    await ctx.reply("This potion doesn't exist. Please check `brew recipe` for possible brewing potions.", mention_author = False)
                    return
                if "_potion" not in potion:
                    await ctx.reply("This is not a potion.", mention_author = False)
                    return
                
                ingredient = LootTable.get_brew_ingredient(potion)
                if ingredient is None:
                    await ctx.reply("This potion is not brewable. Please check `brew recipe` for possible brewing potions.", mention_author = False)
                    return
                
                # Perform a local transaction, and if it's valid, push to db.
                fake_inv = {} # Dict {item: remaining_amount}
                miss = {} # Dict {item: missing_amount}
                for key in ingredient:
                    if key != "quantity" and key != "money":
                        # The item may not exist due to x0.
                        slot = await DB.User.Inventory.get_one_inventory(conn, ctx.author.id, key)
                        if slot is None:
                            fake_inv[key] = -(amount * ingredient[key])
                        else:
                            fake_inv[key] = slot["quantity"] - amount * ingredient[key]
                        
                        if fake_inv[key] < 0:
                            miss[key] = abs(fake_inv[key])
                money = await DB.User.get_money(conn, ctx.author.id)
                
                if len(miss) == 0 and money >= ingredient["money"]:
                    for key in fake_inv:
                        await DB.User.Inventory.update_quantity(conn, ctx.author.id, key, fake_inv[key])
                    
                    await DB.User.Inventory.add(conn, ctx.author.id, potion, amount * ingredient["quantity"])
                    await DB.User.remove_money(conn, ctx.author.id, ingredient["money"])
                    
                    official_name = LootTable.acapitalize(exist["name"])
                    await ctx.reply(f"Brewed {amount * ingredient['quantity']}x **{official_name}** successfully", mention_author = False)
                    
                else:
                    if ingredient["money"] > money:
                        await ctx.reply("You're missing $%d to run the brewing stand. You need: $%d" % (ingredient["money"] - money, ingredient["money"]), mention_author = False)
                    else:
                        miss_string = await LootTable.get_friendly_reward(conn, miss, False)
                        await ctx.reply("Missing the following items: %s" % miss_string, mention_author = False)

    @brew.command(name = 'recipe')
    @commands.bot_has_permissions(external_emojis = True, read_message_history = True, send_messages = True)
    async def brew_recipe(self, ctx : commands.Context, *, potion : ItemConverter = None):
        '''
        Recipe for a potion or all the recipes.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example 1:** {prefix}{command_name} luck potion
        **Example 2:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Use External Emojis`, `Read Message History`, `Send Messages`.
        '''

        recipe = LootTable.get_brew_ingredient(potion)

        if potion is None:
            recipe.pop("undying_potion")
            MAX_ITEMS = 4
            cnt = 0 # Keep track for MAX_ITEMS
            page = Pages()
            embed = None
            friendly_name = ""
            for key in recipe:
                if cnt == 0:
                    embed = Facility.get_default_embed(
                        title = "All brewing recipes",
                        timestamp = datetime.datetime.utcnow(),
                        author = ctx.author
                    )
                
                async with self.bot.pool.acquire() as conn:
                    friendly_name = await DB.Items.get_friendly_name(conn, key)
                
                    outp = recipe[key].pop("quantity", None)
                    embed.add_field(
                        name = LootTable.acapitalize(friendly_name),
                        value = "**Input:** %s\n**Cost:** $%d\n**Output:** %s\n" % (await LootTable.get_friendly_reward(conn, recipe[key]), recipe[key]["money"], await LootTable.get_friendly_reward(conn, {key : outp})),
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
                friendly_name = await DB.Items.get_friendly_name(conn, potion)
                outp = recipe.pop("quantity", None)
                embed = Facility.get_default_embed(
                    title = "%s's brewing recipe" % LootTable.acapitalize(friendly_name),
                    timestamp = datetime.datetime.utcnow(),
                    author = ctx.author
                ).add_field(
                    name = "Recipe:",
                    value = await LootTable.get_friendly_reward(conn, recipe),
                    inline = False
                ).add_field(
                    name = "Receive:",
                    value = await LootTable.get_friendly_reward(conn, {potion : outp}),
                    inline = False
                )

            await ctx.reply(embed = embed, mention_author = False)
        else:
            await ctx.reply("This potion doesn't exist.", mention_author = False)

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
        loot = None

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
                    # - From streak 10 - 99: 300 + (streak / 10) * 100
                    # - From streak 100 - 499: 1000 + streak * 5
                    # - From streak 500+: 2000 + streak * 10
                    # Note: The bonus is cap at $10000, so after streak 1000, it is not possible to increase.

                    if member["streak_daily"] < 10:
                        daily_amount = 100
                        daily_bonus = 0
                    elif member["streak_daily"] < 100:
                        daily_amount = 300
                        daily_bonus = int(member["streak_daily"] / 10) * 100
                    elif member["streak_daily"] < 500:
                        daily_amount = 1000
                        daily_bonus = member["streak_daily"] * 5
                    else:
                        daily_amount = 2000
                        daily_bonus = member["streak_daily"] * 10
                        if daily_bonus > 10000:
                            daily_bonus = 10000
                    
                    daily_amount += daily_bonus

                    member["last_daily"] = datetime.datetime.utcnow()
                    
                    await DB.User.inc_streak(conn, ctx.author.id)
                    await DB.User.add_money(conn, ctx.author.id, daily_amount)
                    await DB.User.update_last_daily(conn, ctx.author.id, member["last_daily"])

                    loot = LootTable.get_daily_loot(member["streak_daily"] + 1)
                    for key in loot:
                        await DB.User.Inventory.add(conn, ctx.author.id, key, loot[key])
         
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
                
                msg += "Here are some free items: " + await LootTable.get_friendly_reward(conn, loot) + '\n'
                msg += f":white_check_mark: You got **${daily_amount}** in total.\nYour streak: `x{member['streak_daily'] + 1}`.\n"

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
            ctx.command.reset_cooldown(ctx)
            return
        if "_pickaxe" not in tool_name and "_axe" not in tool_name and "_sword" not in tool_name and "_rod" not in tool_name:
            await ctx.reply(f"You can't equip this!", mention_author = False)
            ctx.command.reset_cooldown(ctx)
            return
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                exist = await DB.Items.get_item(conn, tool_name)
                if exist is None:
                    await ctx.reply(f"This tool does not exist.", mention_author = False)
                    ctx.command.reset_cooldown(ctx)
                    return
                exist_inv = await DB.User.Inventory.get_one_inventory(conn, ctx.author.id, tool_name)
                if exist_inv is None:
                    await ctx.reply(f"You don't have this tool in your inventory.", mention_author = False)
                    ctx.command.reset_cooldown(ctx)
                    return
                
                tool_type = DB.User.ActiveTools.get_tool_type(tool_name)
                
                message = ""
                has_equipped = await DB.User.ActiveTools.get_equipment(conn, tool_type, ctx.author.id)
                # Swap out the same tool type.
                if has_equipped is not None:
                    try:
                        name = LootTable.acapitalize(await DB.Items.get_friendly_name(conn, has_equipped["id"]))
                        message += "You swapped out the old **%s** with the new tool.\n" % name
                        await DB.User.ActiveTools.unequip_tool(conn, ctx.author.id, has_equipped["id"])
                    except DB.ItemExpired:
                        message += "Your old tool is used, so it's gone into the Void after you remove it :(\n"
                    else:
                        message += "You haven't used the old tool, so it's back into your inventory.\n"
                    
                await DB.User.ActiveTools.equip_tool(conn, ctx.author.id, tool_name)
                official_name = LootTable.acapitalize(await DB.Items.get_friendly_name(conn, tool_name))
                message += f"Added **{official_name}** to main equipments."
                await ctx.reply(message, mention_author = False)

    @commands.command()
    @commands.bot_has_permissions(external_emojis = True, read_message_history = True, send_messages = True)
    async def equipments(self, ctx : commands.Context):
        '''
        Display your equipments and its durability.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Use External Emojis`, `Read Message History`, `Send Messages`.
        '''

        embed = Facility.get_default_embed(
            title = f"{ctx.author}'s Current Equipments",
            timestamp = datetime.datetime.utcnow(),
            author = ctx.author
        )
        async with self.bot.pool.acquire() as conn:
            equipments = await DB.User.ActiveTools.get_equipments(conn, ctx.author.id)
            potions = await DB.User.ActivePotions.get_potions(conn, ctx.author.id)
            portals = await DB.User.ActivePortals.get_portals(conn, ctx.author.id)

            def on_inner_sort(item):
                return item["inner_sort"]
            equipments.sort(key = on_inner_sort)
            potions.sort(key = on_inner_sort)
            portals.sort(key = on_inner_sort)

            if len(equipments) == 0 and len(potions) == 0 and len(portals) == 0:
                embed.description = "*Cricket noises*"
            for tool in equipments:
                embed.add_field(
                    name = "%s **%s** [%d/%d]" % (tool['emoji'], LootTable.acapitalize(tool['name']), tool['durability_left'], tool['durability']),
                    value = f"*{tool['description']}*",
                    inline = False
                )
            for potion in potions:
                embed.add_field(
                    name = "%s **%s** [%d/%d]" % (potion['emoji'], LootTable.acapitalize(potion['name']), potion['remain_uses'], potion['durability']),
                    value = f"*{potion['description']}*",
                    inline = False
                )
            for portal in portals:
                embed.add_field(
                    name = "%s **%s** [%d/%d]" % (portal['emoji'], LootTable.acapitalize(portal['name']), portal['remain_uses'], portal['durability']),
                    value = f"*{portal['description']}*",
                    inline = False
                )
            embed.set_thumbnail(url = ctx.author.avatar_url)
        
        await ctx.reply(embed = embed, mention_author = False)

    @commands.group(aliases = ['inv'], invoke_without_command = True)
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
            inventory = await DB.User.Inventory.get_whole_inventory(conn, ctx.author.id)
            if inventory is None or inventory == [None] * len(inventory):
                await ctx.reply("*Insert empty inventory here*", mention_author = False)
                return

            inventory_dict = {}
            for slot in inventory:
                inventory_dict[slot["id"]] = slot["quantity"]
            await ctx.reply(await LootTable.get_friendly_reward(conn, inventory_dict), mention_author = False)
    
    @inventory.command(name = 'all')
    async def inv_all(self, ctx : commands.Context):
        MAX_ITEMS = 5
        cnt = 0
        page = Pages()
        embed = None
        async with self.bot.pool.acquire() as conn:
            inv = await DB.User.Inventory.get_whole_inventory(conn, ctx.author.id)
            for item in inv:
                if cnt == 0:
                    embed = Facility.get_default_embed(
                        timestamp = datetime.datetime.utcnow(),
                        author = ctx.author
                    ).set_author(
                        name = f"{ctx.author.name}'s inventory",
                        icon_url = ctx.author.avatar_url
                    )
                embed.add_field(
                    name = f"{item['emoji']} **{LootTable.acapitalize(item['name'])} x {item['quantity']}**",
                    value = f"*{item['description']}*",
                    inline = False
                )
                cnt += 1
                if cnt == MAX_ITEMS:
                    page.add_page(embed)
                    cnt = 0
                    embed = None
            
            if embed is not None:
                page.add_page(embed)
            await page.event(ctx, interupt = False)
    
    @inventory.command(name = 'value')
    async def inv_value(self, ctx : commands.Context):
        value = 0
        async with self.bot.pool.acquire() as conn:
            inv = await DB.User.Inventory.get_whole_inventory(conn, ctx.author.id)
            for item in inv:
                if item["sell_price"] is not None:
                    value += item["sell_price"] * item["quantity"]
        
        if value != 0:
            await ctx.reply("If you sell all sellable items, you'll get $%d." % value, mention_author = False)
        else:
            await ctx.reply("Your inventory is either empty, or filled with unsellable items.", mention_author = False)
    
    @inventory.command(name = 'sort')
    async def inv_sort(self, ctx : commands.Context):
        await ctx.reply("It seems you're trying to activate a command that is secretly developed. Don't tell anyone about this.", mention_author = False)


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
                    ctx.command.reset_cooldown(ctx)
                    return
                
                desc = exist["description"]
                rarity = exist["rarity"]
                emote = exist["emoji"]
                friendly_name = exist["name"]
                buy_price = exist["buy_price"]
                sell_price = exist["sell_price"]

                craftable = LootTable.get_craft_ingredient(item)
                
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
                
                price_str = "Buy: %s\nSell: %s" % (
                    f"${buy_price}" if buy_price is not None else "N/A",
                    f"${sell_price}" if sell_price is not None else "N/A",
                )
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

        message = ""
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                # Edit the name of the variable and the string argument.
                current_pick = await DB.User.ActiveTools.get_equipment(conn, "pickaxe", ctx.author.id)
                if current_pick is None:
                    # Edit this message.
                    await ctx.reply("You have no pickaxe equip.", mention_author = False)
                    ctx.command.reset_cooldown(ctx)
                    return
                
                world = await DB.User.get_world(conn, ctx.author.id)
                # Edit function name
                loot = LootTable.get_mine_loot(current_pick["id"], world)
                
                die_chance = 0
                if world == 0:
                    die_chance = OVERWORLD_DIE
                elif world == 1:
                    die_chance = NETHER_DIE
                
                rng = random.random()
                # This section is ugly as fuck but I can't really do anything about this.
                die = False
                if rng <= die_chance:
                    if world == 1:
                        try:
                            # If no exception, then True/False, otherwise, it's False.
                            die = not(await self.__attempt_fire__(conn, ctx.author))
                            if not die:
                                message += "**Fire Potion** saved you from a cruel death.\n"
                        except DB.ItemExpired:
                            message += "**Fire Potion** saved you from a cruel death.\n"
                            message += "**Fire Potion** expired.\n"
                            die = False
                    else:
                        die = True
                            
                if die:
                    await self.__remove_equipments_on_die__(conn, ctx.author)
                    
                    # Edit the function name
                    message += LootTable.get_adventure_msg("die", world)
                    await ctx.reply(message, mention_author = False)
                    return
                
                try:
                    await self.__attempt_luck__(conn, ctx.author, loot)
                except DB.ItemExpired:
                    message += "**Luck Potion** expired.\n"

                try:
                    haste_stack = await self.__attempt_haste__(conn, ctx.author)
                except DB.ItemExpired:
                    message += "**Haste Potion** expired.\n"
                    # Before it expires, the stack is 1.
                    haste_stack = 1
                
                # A dict of {"item": amount}
                final_reward = self.__get_reward__(loot, haste_stack)
                
                reward_string = await LootTable.get_friendly_reward(conn, final_reward)
                any_reward = False
                for reward in final_reward:
                    if final_reward[reward] != 0:
                        any_reward = True
                        # Rewards are guaranteed to not be any of the tools/potions/portals.
                        await DB.User.Inventory.add(conn, ctx.author.id, reward, final_reward[reward])
                
                if any_reward:
                    try:
                        await self.__reduce_tool_durability__(conn, ctx.author, current_pick)
                    except DB.ItemExpired:
                        message += f"Your **{LootTable.acapitalize(current_pick['name'])}** broke after get adventure :(\n"
                    
                    # Edit function name.
                    await ctx.reply(message + LootTable.get_mine_msg("reward", world, reward_string), mention_author = False)
                else:
                    # Edit function name.
                    await ctx.reply(message + LootTable.get_mine_msg("empty", world), mention_author = False)
                    ctx.command.reset_cooldown(ctx)
    
    @commands.command()
    @commands.bot_has_permissions(external_emojis = True, read_message_history = True, send_messages = True)
    @commands.cooldown(rate = 1, per = 10.0, type = commands.BucketType.user)
    async def usepotion(self, ctx : commands.Context, amount : typing.Optional[int] = 1, *, potion : ItemConverter):
        '''
        Use a potion.
        Note that you can only have at max 10 potions of the same potion at once.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Example:** {prefix}{command_name} 5 luck potion

        **You need:** None.
        **I need:** `Use External Emojis`, `Read Message History`, `Send Messages`.
        '''
        if amount is None:
            amount = 1
        if potion is None:
            await ctx.reply("This potion doesn't exist.")
            ctx.command.reset_cooldown(ctx)
            return
        if "_potion" not in potion:
            await ctx.reply("This is not a potion.")
            ctx.command.reset_cooldown(ctx)
            return
        
        async with self.bot.pool.acquire() as conn:
            actual_potion = await DB.User.ActivePotions.get_potion(conn, ctx.author.id, potion)
            if actual_potion is not None:
                pot_stack = await DB.User.ActivePotions.get_stack(conn, potion, actual_potion["remain_uses"])
                if pot_stack == 10:
                    await ctx.reply("You cannot stack a potion more than 10.", mention_author = False)
                    ctx.command.reset_cooldown(ctx)
                    return
            else:
                current_potions = await DB.User.ActivePotions.get_potions(conn, ctx.author.id)
                if len(current_potions) == 3:
                    await ctx.reply("You cannot have more than 3 different potions at the same time.", mention_author = False)
                    return
            
            async with conn.transaction():
                try:
                    await DB.User.ActivePotions.set_potion_active(conn, ctx.author.id, potion, amount)
                except DB.ItemNotPresent:
                    await ctx.reply("You don't have such a potion.", mention_author = False)
                    ctx.command.reset_cooldown(ctx)
                    return
                except DB.TooLargeRemoval:
                    await ctx.reply("You don't have this many potion.", mention_author = False)
                    ctx.command.reset_cooldown(ctx)
                    return
                
                official_name = await DB.Items.get_friendly_name(conn, potion)
                await ctx.reply(f"Used {LootTable.acapitalize(official_name)}.", mention_author = False)

    @commands.command(aliases = ['lb'])
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    @commands.cooldown(rate = 1, per = 5.0, type = commands.BucketType.member)
    async def leaderboard(self, ctx : commands.Context, local__global = "local"):
        '''
        Show the top 10 users with the most amount of money.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Cooldown:** 5 seconds per 1 use (member)
        **Example 1:** {prefix}{command_name} global
        **Example 2:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Read Messages History`, `Send Messages`.
        '''
        
        async with self.bot.pool.acquire() as conn:
            query = ""
            if local__global == "local":
                query = '''
                    SELECT DUsers.id, DUsers.money FROM DUsers_DGuilds
                        INNER JOIN DUsers ON user_id = id
                    WHERE DUsers_DGuilds.guild_id = %d AND DUsers.money > 0
                    ORDER BY DUsers.money DESC
                    LIMIT 10;
                ''' % ctx.guild.id
            # Any other args will result in global.
            else:
                query = '''
                    SELECT id, money FROM DUsers
                    WHERE money > 0
                    ORDER BY money DESC
                    LIMIT 10;
                '''
            
            result = await conn.fetch(query)
            if result is None:
                await ctx.reply("It seems I can't retrieve any users somehow. You might want to report this to the developer.", mention_author = False)
                return
            
            record_list = [DB.rec_to_dict(record) for record in result]

            embed = Facility.get_default_embed(
                title = "Top 10 richest people %s" % ("in " + ctx.guild.name if local__global == "local" else "on MichaelBot"),
                timestamp = datetime.datetime.utcnow(),
                author = ctx.author
            )
            embed.description = ""
            for index, record in enumerate(record_list):
                user = self.bot.get_user(record["id"])
                embed.description += f"{index + 1}. **{user}** - ${record['money']}\n"
            
            await ctx.reply(embed = embed, mention_author = False)
    
    @commands.group(invoke_without_command = True)
    @commands.bot_has_permissions(external_emojis = True, read_message_history = True, send_messages = True)
    @commands.cooldown(rate = 1, per = 5.0, type = commands.BucketType.user)
    async def market(self, ctx : commands.Context):
        '''
        Display all items' value in terms of money.

        To buy or sell items, please use the command's subcommands.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Cooldown:** 5 seconds per 1 use (user)
        **Example:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Use External Emojis`, `Read Message History`, `Send Messages`.
        '''

        if ctx.invoked_subcommand is None:
            MAX_ITEMS = 4
            cnt = 0 # Keep track of MAX_ITEMS
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
                        value = "*%s*\n**Buy Price**: %s\n**Sell Price**: %s" % (
                            item["description"], 
                            "N/A" if item["buy_price"] is None else f"${item['buy_price']}",
                            "N/A" if item["sell_price"] is None else f"${item['sell_price']}"
                        ),
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

    @market.command()
    @commands.bot_has_permissions(external_emojis = True, read_message_history = True, send_messages = True)
    @commands.cooldown(rate = 1, per = 5.0, type = commands.BucketType.user)
    async def buy(self, ctx : commands.Context, amount : typing.Optional[int] = 1, *, item : ItemConverter):
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
            ctx.command.reset_cooldown(ctx)
            return
        if amount < 1:
            await ctx.reply("You can't buy 0 or smaller items dummy.", mention_author = False)
            ctx.command.reset_cooldown(ctx)
            return
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                actual_item = await DB.Items.get_item(conn, item)
                if actual_item["buy_price"] is None:
                    await ctx.reply("This item is not purchasable!", mention_author = False)
                    ctx.command.reset_cooldown(ctx)
                    return
                money = await DB.User.get_money(conn, ctx.author.id)
                if money - amount * actual_item["buy_price"] < 0:
                    await ctx.reply("You don't have enough money to buy. Total cost is: $%d" % amount * actual_item["buy_price"], mention_author = False)
                    ctx.command.reset_cooldown(ctx)
                    return
                
                await DB.User.remove_money(conn, ctx.author.id, amount * actual_item["buy_price"])
                await DB.User.Inventory.add(conn, ctx.author.id, item, amount)
                await ctx.reply(f"Bought {await LootTable.get_friendly_reward(conn, {item : amount}, False)} (${amount * actual_item['buy_price']})successfully.", mention_author = False)
            
    @market.command()
    @commands.bot_has_permissions(external_emojis = True, read_message_history = True, send_messages = True)
    @commands.cooldown(rate = 1, per = 5.0, type = commands.BucketType.user)
    async def sell(self, ctx : commands.Context, amount : typing.Optional[int] = 1, *, item : ItemConverter):
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
            ctx.command.reset_cooldown(ctx)
            return
        if amount < 1:
            await ctx.reply("So...are you selling or not?", mention_author = False)
            ctx.command.reset_cooldown(ctx)
            return
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                inv_slot = await DB.User.Inventory.get_one_inventory(conn, ctx.author.id, item)
                if inv_slot is None:
                    await ctx.reply("You don't have such item to sell.", mention_author = False)
                    ctx.command.reset_cooldown(ctx)
                    return
                if inv_slot["sell_price"] is None:
                    await ctx.reply("This item cannot be sold.", mention_author = False)
                    ctx.command.reset_cooldown(ctx)
                    return
                # The function won't affect the inventory if it fails.
                try:
                    await DB.User.Inventory.remove(conn, ctx.author.id, item, amount)
                except DB.TooLargeRemoval:
                    await ctx.reply("You don't have enough items to sell. You only have: %d" % inv_slot["quantity"] if inv_slot is not None else 0, mention_author = False)
                    ctx.command.reset_cooldown(ctx)
                    return
                await DB.User.add_money(conn, ctx.author.id, amount * inv_slot["sell_price"])
                await ctx.reply(f"Sold {await LootTable.get_friendly_reward(conn, {item : amount}, False)} successfully for ${amount * inv_slot['sell_price']}", mention_author = False)
                
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
        elif destination.upper() == "SPACE":
            dest = 2
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
                user_inv = await DB.User.ActivePortals.get_portal(conn, ctx.author.id, "nether")
            elif (dest == 2 and world == 0) or (dest == 0 and world == 2):
                user_inv = await DB.User.ActivePortals.get_portal(conn, ctx.author.id, "end")
            
            if user_inv is None:
                await ctx.reply("You don't have a portal to travel to this destination.", mention_author = False)
                return
            
            if user_info["last_move"] is not None:
                if datetime.datetime.utcnow() - user_info["last_move"] < datetime.timedelta(hours = 24.0):
                    remaining_time = datetime.timedelta(hours = 24) - (datetime.datetime.utcnow() - user_info["last_move"])
                    remaining_str = humanize.precisedelta(remaining_time, "seconds", format = "%0.0f")
                    await ctx.reply(f"You still have {remaining_str} left before you can travel again.", mention_author = False)
                    return
            if (dest == 2 and world == 0) or (dest == 0 and world == 2):
                eye_exist = await DB.User.Inventory.get_one_inventory(conn, ctx.author.id, "ender_eye")
                blaze_exist = await DB.User.Inventory.get_one_inventory(conn, ctx.author.id, "blaze")
                if eye_exist is None:
                    await ctx.reply(f"You have no **Mysterious Eye** to travel.", mention_author = False)
                    return
                if eye_exist["quantity"] < 2 and blaze_exist is None:
                    await ctx.reply(f"You might not be able to return, so no I won't allow you.", mention_author = False)
                    return
                            
            async with conn.transaction():
                message = "Moved to %s.\n" % LootTable.get_world(dest)
                await DB.User.update_world(conn, ctx.author.id, dest)
                await DB.User.update_last_move(conn, ctx.author.id, datetime.datetime.utcnow())
                try:    
                    if (dest == 1 and world == 0) or (dest == 0 and world == 1):
                        await DB.User.ActivePortals.dec_durability(conn, ctx.author.id, "nether")
                    elif (dest == 2 and world == 0) or (dest == 0 and world == 2):
                        await DB.User.ActivePortals.dec_durability(conn, ctx.author.id, "end")
                        await DB.User.Inventory.remove(conn, ctx.author.id, "ender_eye")
                except DB.ItemExpired:
                    message += "The portal broke!\n"
                await ctx.reply(message, mention_author = False)

def setup(bot : MichaelBot):
    bot.add_cog(Currency(bot))
