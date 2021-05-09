from math import e
import discord
from discord.ext import commands

import datetime as dt
import typing

import asyncpg
from utilities.loot import get_item_info
from utilities.michaelexceptions import MichaelBotException

class MichaelBotDatabaseException(MichaelBotException):
    pass

class ItemNotPresent(MichaelBotDatabaseException):
    """
    This exception is typically raised when an item is not available in the inventory.
    """
    pass
class PotionNotActive(MichaelBotDatabaseException):
    """
    This exception is typically raised when a potion is not active and is still in inventory.
    """
    pass
class EquipmentNotActive(MichaelBotDatabaseException):
    """
    This exception is typically raised when a tool is not active and is still in inventory.
    """
    pass
class TooLargeRemoval(MichaelBotDatabaseException):
    """
    This exception is typically raised when the amount removed from inventory cause the final amount
    to be negative.
    """
    pass
class ItemExpired(MichaelBotDatabaseException):
    """
    This exception is typically raised when the tool/potion/portal's remaining use is
    0 or negative.

    Note that this exception will need to be raised *AFTER* the operation is completed.
    Thus, this exception should be treated as a special notification rather than an error.
    """
    pass

async def update_db(bot):
    """
    Update database once in a while.
    This is called once during bot's loading up, and whenever the bot's cache is ready.

    Parameter:
    - `bot`: A `commands.Bot` object.
    """
    bot.debug("Updating database on ready...")
    async with bot.pool.acquire() as conn:
        async with conn.transaction():
            for guild in bot.guilds:
                result = await Guild.find_guild(conn, guild.id)
                if result is None:
                    await Guild.insert_guild(conn, guild)

                # There might be new member join during this process, so we need to put this outside the if.
                for member in guild.members:
                    if not member.bot:
                        user_existed = await User.find_user(conn, member.id)
                        member_existed = await Member.find_member(conn, member.id, guild.id)
                        if user_existed is None:
                            await User.insert_user(conn, member)
                            await Member.insert_member(conn, member)
                        # Sometimes, there can be desync between DUsers and DUsers_DGuilds (various reasons, including non-complete support).
                        elif member_existed is None:
                            await Member.insert_member(conn, member)
            
            items = get_item_info()
            count = 1
            for key in items:
                # Insert item id into the list.
                items[key].insert(0, key)
                # Dict in python3.8+ is ordered, so we can rely on this to dynamically set inner_sort.
                items[key].insert(2, count)
                count += 1
                await Items.create_item(conn, items[key])
                          
async def insert_into(conn, table_name : str, *args):
    """
    Insert values into `table_name`.

    Parameter:
    - `conn`: The connection you want to do.
        + It's usually just `pool.acquire()`.
    - `table_name`: The table where you want to add.
        + If it's `dGuilds`, consider using `insert_guild` instead.
        + If it's `dUsers`, consider using `insert_user` instead.
        + If it's `dUsers_dGuilds`, consider using `insert_member` instead.
    - `*args`: This must be a list of tuples.
        + `len(tuple)` must equals to the number of column you want to insert.
    """

    arg_str = "("
    for j in range(len(max(*args, key = len))):
        arg_str += '$' + str(j + 1) + ", "
    arg_str = arg_str[:-2] + ')'

    await conn.executemany('''
        INSERT INTO %s
        VALUES %s
    ''' % (table_name, arg_str), *args
    )
class User:
    """
    A group of methods dealing specifically with `dUsers` table.
    For `dUsers_dGuilds` table, refers to `Member` instead.
    """

    @classmethod
    async def find_user(cls, conn, user_id : int) -> dict:
        """
        Find a member data in `DUsers`.

        If a member is found, it'll return a `dict` of the member, otherwise it'll return `None`.

        Important Parameter:
        - `user_id`: The user's id.
        """

        result = await conn.fetchrow('''
            SELECT *
            FROM DUsers
            WHERE id = ($1)
        ''', user_id)

        return rec_to_dict(result)
    @classmethod
    async def insert_user(cls, conn, member : discord.Member):
        """
        Insert a default user data into `DUsers`.

        If the user already exist, this method do nothing.

        Important Parameter:
        - `member`: A Discord member to insert.
        """

        member_existed = await cls.find_user(conn, member.id)
        if member_existed is None:
            await insert_into(conn, "DUsers", [
                (member.id, member.name, True, 0, None, 0, 0, None)
            ])
    @classmethod
    async def __update_generic__(cls, conn, id : int, col_name : str, new_value):
        """
        A generic method to update a column in `DUsers` table.
        
        This method's variations `update_...` is recommended. Only use this when there's a new column.

        Important Parameter:
        - `id`: The member id.
        - `col_name`: The column name in the table. **This must be exactly the same as in the table**.
        - `new_value`: The new value.
        """

        await conn.execute('''
            UPDATE DUsers
            SET %s = ($1)
            WHERE id = ($2);
        ''' % col_name, new_value, id)
    @classmethod
    async def update_name(cls, conn, id, new_name : str):
        await cls.__update_generic__(conn, id, "name", new_name)
    @classmethod
    async def update_whitelist(cls, conn, id, new_status : bool):
        await cls.__update_generic__(conn, id, "is_whitelist", new_status)
    @classmethod
    async def update_money(cls, conn, id, new_money : int):
        # Money can't be lower than 0, for now.
        if new_money <= 0:
            new_money = 0
        
        await cls.__update_generic__(conn, id, "money", new_money)
    @classmethod
    async def update_last_daily(cls, conn, id, new_last_daily : dt.datetime):
        await cls.__update_generic__(conn, id, "last_daily", new_last_daily)
    @classmethod
    async def update_streak(cls, conn, id, new_streak : int):
        await cls.__update_generic__(conn, id, "streak_daily", new_streak)  
    @classmethod
    async def update_world(cls, conn, id, new_world : int):
        await cls.__update_generic__(conn, id, "world", new_world)   
    @classmethod
    async def update_last_move(cls, conn, id, new_last_move : dt.datetime):
        await cls.__update_generic__(conn, id, "last_move", new_last_move)
    @classmethod
    async def bulk_update(cls, conn, id, new_values : dict):
        """
        Update all values in one SQL statement.

        Important Parameter:
        - `id`: The user's id.
        - `new_values`: A dict of `{"col_name": value}`.
            + `col_name` must match the table's column.
            + Order can be arbitrary.
        """

        update_str = ""
        update_arg = []
        count = 1
        for column in new_values:
            update_str += f"{column} = (${count}), "
            update_arg.append(new_values[column])
            count += 1
        update_str = update_str[:-2]

        await conn.execute('''
            UPDATE DUsers
            SET %s
            WHERE id = (%d)
        ''' % (update_str, id), *update_arg)
    
    @classmethod
    async def get_money(cls, conn, id) -> int:
        """
        Get the user's money.
        If there's no such user, the amount returned is 0.

        Important Parameter:
        - `id`: The user's id.
        """
        exist = await cls.find_user(conn, id)
        return exist["money"] if exist is not None else 0    
    @classmethod
    async def get_world(cls, conn, id) -> typing.Optional[int]:
        exist = await cls.find_user(conn, id)
        return exist["world"] if exist is not None else None

    @classmethod
    async def add_money(cls, conn, id, amount : int):
        """
        Add an amount of money to the user.
        If amount is negative, no changes are made.

        Important Parameter:
        - `id`: The user's id.
        - `amount`: The amount to add.
        """

        if amount > 0:
            money = await cls.get_money(conn, id)
            return await cls.update_money(conn, id, money + amount)
    @classmethod
    async def remove_money(cls, conn, id, amount : int):
        """
        Remove an amount of money from the user.
        
        - If amount is negative, no changes are made.
        - If the resulting money is less than 0, the money is 0.

        Important Parameter:
        - `id`: The user's id.
        - `amount`: The amount to remove.
        """
        if amount > 0:
            money = await cls.get_money(conn, id)
            # No need to check because update_money() checks.
            return await cls.update_money(conn, id, money - amount)
    
    @classmethod
    async def inc_streak(cls, conn, id):
        """
        Increase the streak by 1.

        Important Parameter:
        - `id`: The user's id.
        """

        user = await cls.find_user(conn, id)
        await cls.update_streak(conn, id, user["streak_daily"] + 1)

    class Inventory:
        """
        A group of methods mainly deals with DUsers_Items table.
        """

        @classmethod
        async def get_whole_inventory(cls, conn, user_id : int) -> typing.List[typing.Optional[dict]]:
            """
            Retrieve an entire inventory, sorted based on reverse quantity and reverse `inner_sort`.
            
            The structure of each element is the same as `Items.get_items()` structure, with
            the additional `quantity` key.

            - If the inventory is empty, a list of `None` is returned.
            
            Important Parameter:
            - `user_id`: The user's id.
            """

            query = '''
                SELECT Items.*, DUsers_Items.quantity
                FROM DUsers_Items
                    INNER JOIN Items ON item_id = id
                WHERE DUsers_Items.user_id = ($1)
                ORDER BY DUsers_Items.quantity DESC, Items.inner_sort DESC;
            '''
            
            result = await conn.fetch(query, user_id)      
            return [rec_to_dict(row) for row in result]
        
        @classmethod
        async def get_one_inventory(cls, conn, user_id : int, item_id : int) -> typing.Optional[dict]:
            """
            Get an inventory slot.

            The structure of the resultant dictionary is the same as `Items.get_items()` structure, with
            the additional `quantity` keys.

            - If no such slot exist, `None` is returned.

            Important Parameter:
            - `user_id`: The user's id.
            - `item_id`: The item's inner name.
            """
            query = '''
                SELECT Items.*, DUsers_Items.quantity
                FROM DUsers_Items
                    INNER JOIN Items ON item_id = id
                WHERE user_id = ($1) AND item_id = ($2);
            '''
            
            result = await conn.fetchrow(query, user_id, item_id)
            return rec_to_dict(result)

        @classmethod
        async def find_equipment(cls, conn, tool_type : str, user_id : int) -> typing.Optional[dict]:
            """
            Find the "tool" items that are inactive (still in the inventory).

            - If there are no such equipments, `None` is returned.

            Important Parameters:
            - `tool_type`: Either `pickaxe`, `axe` or `sword`.
            - `user_id`: The user's id.
            """

            query = f'''
                SELECT Items.*, DUsers_Items.quantity
                FROM DUsers_Items
                    INNER JOIN Items ON item_id = id
                WHERE item_id LIKE '%\_{tool_type}' AND user_id = ($1);
            '''

            result = await conn.fetchrow(query, user_id)
            return rec_to_dict(result)

        @classmethod
        async def add(cls, conn, user_id : int, item_id : int, amount : int = 1):
            """
            Add an amount of item to the user's inventory slot. **It is not a method deal with active items.**
            
            - If the inventory slot (identified by both `user_id` and `item_id`) doesn't exist, it'll be created.

            Important Parameter:
            - `user_id`: The user's id.
            - `item_id`: The item's inner name.
            - `amount`: The amount of items to add.
            """

            item_existed = await cls.get_one_inventory(conn, user_id, item_id)
            if item_existed is None:
                query = '''
                    INSERT INTO DUsers_Items
                    VALUES ($1, $2, $3);
                '''
                await conn.execute(query, user_id, item_id, amount)
            else:
                query = '''
                    UPDATE DUsers_Items
                    SET quantity = ($1)
                    WHERE user_id = ($2) AND item_id = ($3);
                '''

                await conn.execute(query, item_existed["quantity"] + amount, user_id, item_id)
        
        @classmethod
        async def remove(cls, conn, user_id : int, item_id : int, amount : int = 1) -> str:
            """
            Remove an amount of item from the user's inventory slot.

            - If the resultant amount is 0, the slot is deleted.
            - If the item doesn't exist, the function raises `ItemNotPresent` exception.
            - If the resultant amount < 0, the function raises `TooLargeRemoval` exception.
            """

            item_existed = await cls.get_one_inventory(conn, user_id, item_id)
            if item_existed is None:
                raise ItemNotPresent(f"Item {item_id} does not exist in the user {user_id}'s inventory.")
            else:
                if item_existed["quantity"] - amount == 0:
                    query = '''
                        DELETE FROM DUsers_Items
                        WHERE user_id = ($1) AND item_id = ($2);
                    '''

                    await conn.execute(query, user_id, item_id)
                
                elif item_existed["quantity"] - amount < 0:
                    raise TooLargeRemoval("Quantity exceeded the amount presented in the inventory.")
                else:
                    query = '''
                        UPDATE DUsers_Items
                        SET quantity = ($1)
                        WHERE user_id = ($2) AND item_id = ($3);
                    '''

                    await conn.execute(query, item_existed["quantity"] - amount, user_id, item_id)
            
        @classmethod
        async def update_quantity(cls, conn, user_id : int, item_id : int, quantity : int):
            """
            Update the inventory slot's quantity.

            Important Parameter:
            - `user_id`: The user's id.
            - `item_id`: The item's inner name.
            - `quantity`: The new amount.
            """
            item_existed = await cls.get_one_inventory(conn, user_id, item_id)
            if item_existed is None:
                return
            elif quantity <= 0:
                await cls.remove(conn, user_id, item_id, item_existed["quantity"])
            else:
                await cls.add(conn, user_id, item_id, quantity - item_existed["quantity"])

    class ActiveTools:
        """
        A group of methods mainly deals with DUsers_ActiveTools.
        """

        # DUsers_ActiveTools
        @classmethod
        def get_tool_type(cls, tool_id : str) -> str:
            """
            A utility function to determine what kind of tool is the tool.

            Important Parameter:
            - `tool_id`: The item's inner name.
            """
            if "_pickaxe" in tool_id:
                return "pickaxe"
            elif "_axe" in tool_id:
                return "axe"
            elif "_sword" in tool_id:
                return "sword"
            elif "_rod" in tool_id:
                return "rod"

        @classmethod
        async def get_tools(cls, conn, user_id : int) -> typing.List[typing.Optional[dict]]:
            """
            Get a list of active equipments, sorted by `inner_sort`.

            The structure of each element is same as `Items.get_item()`, along with the extra
            `durability_left` key.

            - If there are no active equipments, a list of `None` is returned.

            Important Parameter:
            - `user_id`: The user's id.
            """
            query = '''
                SELECT Items.*, DUsers_ActiveTools.durability_left
                FROM DUsers_ActiveTools
                    INNER JOIN Items ON item_id = id
                WHERE user_id = ($1)
                ORDER BY Items.inner_sort;
            '''

            result = await conn.fetch(query, user_id)
            return [rec_to_dict(record) for record in result]

        @classmethod
        async def get_tool(cls, conn, tool_type : str, user_id : int) -> typing.Optional[dict]:
            """
            Get an active tool based on its type.
            
            - If there is no such tool, `None` is returned.

            Important Parameter:
            - `tool_type`: The tool type. It is recommended to pass in the result of `ActiveTools.get_tool_type()`.
            - `user_id`: The user's id.
            """
            query = f'''
                SELECT Items.*, DUsers_ActiveTools.durability_left
                FROM DUsers_ActiveTools
                    INNER JOIN Items ON item_id = id
                WHERE item_id LIKE '%\_{tool_type}' AND user_id = ($1);
            '''

            result = await conn.fetchrow(query, user_id)
            return rec_to_dict(result)

        @classmethod
        async def dec_durability(cls, conn, user_id : int, tool_id : int, amount : int = 1):
            """
            Decrease the tool's durability by an amount.

            - If the tool's durability reaches 0 and below, `ItemExpired` is raised.

            Important Parameter:
            - `user_id`: The user's id.
            - `tool_id`: The item's inner name.
            - `amount`: The amount of durability to decrease.
            """
            tool = await cls.get_tool(conn, cls.get_tool_type(tool_id), user_id)
            if tool is not None:
                if tool["durability_left"] - amount <= 0:
                    await cls.unequip_tool(conn, user_id, tool_id)
                    raise ItemExpired
                else:
                    query = '''
                        UPDATE DUsers_ActiveTools
                        SET durability_left = ($1)
                        WHERE user_id = ($2) AND item_id = ($3);
                    '''
                    await conn.execute(query, tool["durability_left"] - amount, user_id, tool_id)

        @classmethod
        async def equip_tool(cls, conn, user_id : int, item_id : int):
            """
            Equip the tool for the user.
            **This method does not deal with the situation where the user already equipped a same tool type.**

            - If the user doesn't have such tool, `ItemNotPresent` is raised.
            - Can potentially raise exceptions from `Inventory.remove()`.

            Important Parameter:
            - `user_id`: The user's id.
            - `item_id`: The item's inner name.
            """
            
            exist = await User.Inventory.get_one_inventory(conn, user_id, item_id)
            if exist is None:
                raise ItemNotPresent(f"Item {item_id} does not exist in the user {user_id}'s inventory.")
            
            await User.Inventory.remove(conn, user_id, item_id)

            query = '''
                INSERT INTO DUsers_ActiveTools
                VALUES ($1, $2, $3);
            '''
            await conn.execute(query, user_id, item_id, exist["durability"])
        
        @classmethod
        async def unequip_tool(cls, conn, user_id : int, item_id : int, return_inv = True):
            """
            Unequip the tool from the user.
            This destroys the items if the tool is used or `return_inv` is `False`,
            otherwise, it's added back to the inventory.
            
            - If the item is destroyed, `ItemExpired` is raised.
            - If the item is not equipped, `ItemNotPresent` is raised.

            Important Parameter:
            - `user_id`: The user's id.
            - `item_id`: The item's inner name.
            - `return_inv`: `False` = destroy the item regardless of being used or not.
            """
            equipped = await cls.get_tool(conn, cls.get_tool_type(item_id), user_id)
            if equipped is not None:
                query = '''
                    DELETE FROM DUsers_ActiveTools
                    WHERE user_id = ($1) AND item_id = ($2);
                '''

                await conn.execute(query, user_id, item_id)
                if equipped["durability_left"] == equipped["durability"] and return_inv:
                    await User.Inventory.add(conn, user_id, item_id)
                else:
                    raise ItemExpired(f"Item {item_id}'s durability is forcefully returned to 0.")
            else:
                raise ItemNotPresent(f"Item {item_id} is not currently equipping by user {user_id}.")
    class ActivePortals:
        # DUsers_ActivePortals
        @classmethod
        async def get_portals(cls, conn, user_id : int) -> typing.List[typing.Optional[dict]]:
            """
            Get a list of active portals, sorted by `inner_sort`.

            The structure of each element is same as `Items.get_item()`, along with the extra
            `remain_uses` key.

            - If there are no active portals, a list of `None` is returned.

            Important Parameter:
            - `user_id`: The user's id.
            """

            query = '''
                SELECT Items.*, DUsers_ActivePortals.remain_uses
                FROM DUsers_ActivePortals
                    INNER JOIN Items ON item_id = id
                WHERE user_id = ($1)
                ORDER BY Items.inner_sort;
            '''

            result = await conn.fetch(query, user_id)
            return [rec_to_dict(record) for record in result]
        @classmethod
        async def get_portal(cls, conn, user_id : int, portal_id : str) -> typing.Optional[dict]:
            """
            Get a portal, based on its id.

            The structure is the same as `Items.get_item()`, along with the extra `remain_uses`
            key.

            Important Parameter:
            - `user_id`: The user's id.
            - `portal_id`: The portal's inner name.
            """
            query = '''
                SELECT Items.*, DUsers_ActivePortals.remain_uses
                FROM DUsers_ActivePortals
                    INNER JOIN Items ON item_id = id
                WHERE user_id = ($1) AND item_id = ($2);
            '''

            result = await conn.fetchrow(query, user_id, portal_id)
            return rec_to_dict(result)
        
        @classmethod
        async def add(cls, conn, user_id : int, portal_id : str):
            """
            Add a portal to activate it.
            This does NOT check for duplication.

            Important Parameter:
            - `user_id`: The user's id.
            - `portal_id`: The portal's inner name.
            """
            # It is the bot's job to keep this table has no similar portals.
            portal = await Items.get_item(conn, portal_id)
            query = '''
                INSERT INTO DUsers_ActivePortals
                VALUES ($1, $2, $3);
            '''
            await conn.execute(query, user_id, portal_id, portal["durability"])
        @classmethod
        async def remove(cls, conn, user_id : int, portal_id : str):
            """
            Remove a portal.
            
            - If there isn't such portal, the method does nothing.

            Important Parameter:
            - `user_id`: The user's id.
            - `portal_id`: The portal's inner name.
            """
            query = '''
                DELETE FROM DUsers_ActivePortals
                WHERE user_id = ($1) AND item_id = ($2);
            '''

            await conn.execute(query, user_id, portal_id)
        @classmethod
        async def dec_durability(cls, conn, user_id : int, portal_id : int, amount : int = 1):
            """
            Decrease the portal's remaining uses.

            - If the final remaining uses is 0 or negative, the portal is removed, and `ItemExpired` is raised.
            
            Important Parameter:
            - `user_id`: The user's id.
            - `portal_id`: The portal's inner name.
            - `amount`: The amount of durability to remove.
            """
            tool = await cls.get_portal(conn, user_id, portal_id)
            if tool is not None:
                if tool["remain_uses"] - amount <= 0:
                    await cls.remove(conn, user_id, portal_id)
                    raise ItemExpired
                else:
                    query = '''
                        UPDATE DUsers_ActivePortals
                        SET remain_uses = ($1)
                        WHERE user_id = ($2) AND item_id = ($3);
                    '''
                    await conn.execute(query, tool["remain_uses"] - amount, user_id, portal_id)
    
    class ActivePotions:
        # DUsers_ActivePotions
        @classmethod
        async def get_potions(cls, conn, user_id : int) -> typing.List[typing.Optional[dict]]:
            """
            Get a list of active potions, sorted by `inner_sort`.

            The structure of each element is similar to `Items.get_item()`, along with an extra
            `remain_uses` key.

            - If there are no active potions, a list of `None` is returned.

            Important Parameter:
            - `user_id`: The user's id.
            """
            query = '''
                SELECT Items.*, DUsers_ActivePotions.remain_uses
                FROM DUsers_ActivePotions
                    INNER JOIN Items ON item_id = id
                WHERE user_id = ($1)
                ORDER BY Items.inner_sort;
            '''

            result = await conn.fetch(query, user_id)
            return [rec_to_dict(record) for record in result]
        @classmethod
        async def get_potion(cls, conn, user_id : int, potion_id : str) -> typing.Optional[dict]:
            """
            Get an active potion.

            The structure is similar to `Items.get_item()`, along with an extra `remain_uses` key.

            Important Parameter:
            - `user_id`: The user's id.
            - `potion_id`: The potion's inner name.
            """
            query = '''
                SELECT Items.*, DUsers_ActivePotions.remain_uses
                FROM DUsers_ActivePotions
                    INNER JOIN Items ON item_id = id
                WHERE user_id = ($1) AND item_id = ($2);
            '''

            result = await conn.fetchrow(query, user_id, potion_id)
            return rec_to_dict(result)

        @classmethod
        async def get_stack(cls, conn, potion_id : str, remaining : int):
            """
            An abstract way to get the stack of potions.
            The stack of a potion with a given remaining use is `remain_uses / base_durability`
            rounded up.

            Important Parameter:
            - `potion_id`: The potion's id.
            - `remaining`: The remaining uses of the potion.
            """
            default_durability = (await Items.get_item(conn, potion_id))["durability"]
            from math import ceil
            return ceil(remaining / default_durability)
        @classmethod
        async def set_potion_active(cls, conn, user_id : int, potion_id : str, amount : int = 1):
            """
            Make a potion active from the user's inventory.
            In reality, this only remove the potion from the user's inventory, then call `add_active_potion`.

            - Can potentially raises exceptions from `Inventory.remove()`.

            Important Parameter:
            - `user_id`: The user's id.
            - `potion_id`: The potion's inner name.
            - `amount`: The amount of potion to add. This is NOT the remain uses.
            """
            try:
                await User.Inventory.remove(conn, user_id, potion_id, amount)
            except ItemNotPresent as inp:
                raise inp
            except TooLargeRemoval as itlr:
                raise itlr
            
            await cls.__add_active_potion__(conn, user_id, potion_id, amount)
        
        @classmethod
        async def __add_active_potion__(cls, conn, user_id : int, potion_id : int, amount : int = 1):
            """
            Add the potion into the active table.

            Important Parameter:
            - `user_id`: The user's id.
            - `potion_id`: The potion's inner name.
            - `amount`: The amount of potion to add. This is NOT remaining uses.
            """
            existed = await cls.get_potion(conn, user_id, potion_id)
            if existed is None:
                actual_item = await Items.get_item(conn, potion_id)
                query = '''
                    INSERT INTO DUsers_ActivePotions
                    VALUES ($1, $2, $3);
                '''

                await conn.execute(query, user_id, potion_id, actual_item["durability"] * amount)
            else:
                query = '''
                    UPDATE DUsers_ActivePotions
                    SET remain_uses = ($1)
                    WHERE user_id = ($2) AND item_id = ($3);
                '''

                await conn.execute(query, existed["remain_uses"] + amount * existed["durability"], user_id, potion_id)
        
        @classmethod
        async def decrease_active_potion(cls, conn, user_id : int, potion_id : int, durability : int = 1):
            """
            Decrease the durability of the potion.

            - If the potion is not active, `PotionNotActive` is raised.
            - If the potion's durability is 0 or negative, `ItemExpired` is raised.

            Important Parameter:
            - `user_id`: The user's id.
            - `potion_id`: The potion's inner name.
            - `durability`: The amount of durability to remove.
            """
            existed = await cls.get_potion(conn, user_id, potion_id)
            if existed is None:
                raise PotionNotActive(f"Potion {potion_id} is not active.")
            else:
                if existed["remain_uses"] - durability <= 0:
                    query = '''
                        DELETE FROM DUsers_ActivePotions
                        WHERE user_id = ($1) AND item_id = ($2);
                    '''

                    await conn.execute(query, user_id, potion_id)
                    raise ItemExpired
                else:
                    query = '''
                        UPDATE DUsers_ActivePotions
                        SET remain_uses = ($1)
                        WHERE user_id = ($2) AND item_id = ($3);
                    '''

                    await conn.execute(query, existed["remain_uses"] - durability, user_id, potion_id)

class Guild:
    """
    A group of methods dealing specifically with `DGuilds` table.
    """

    @classmethod
    async def find_guild(cls, conn, id : int) -> typing.Optional[dict]:
        """
        Find a guild data in `DGuilds`.

        Important Parameter:
        - `id`: The guild's id.
        """
        result = await conn.fetchrow('''
            SELECT *
            FROM DGuilds
            WHERE id = ($1)
        ''', id)

        return rec_to_dict(result)
    
    @classmethod
    async def insert_guild(cls, conn, guild : discord.Guild):
        """
        Insert a guild into `DGuilds`.
        If the guild already existed, the method does nothing.

        Important Parameter:
        - `guild`: A Discord guild.
        """
        
        guild_existed = await cls.find_guild(conn, guild.id)
        if guild_existed is None:
            await insert_into(conn, "DGuilds", [
                (guild.id, guild.name, True, '$', False, 0)
            ])

    @classmethod
    async def update_generic(cls, conn, id : int, col_name : str, new_value):
        """
        A generic method to update a column in `DGuilds` table.
        
        This method's variations `update_...` is recommended. Only use this when there's a new column.

        Parameter:
        - `conn`: The connection.
            + Usually from `pool.acquire()`.
        - `id`: The member id.
        - `col_name`: The column name in the table. **This must be exactly the same as in the table**.
        - `new_value`: The new value.
        """
        
        await conn.execute('''
            UPDATE DGuilds
            SET %s = ($1)
            WHERE id = ($2);
        ''' % col_name, new_value, id)
    
    @classmethod
    async def update_name(cls, conn, id : int, new_name : str):
        await cls.update_generic(conn, id, "name", new_name)
    
    @classmethod
    async def update_whitelist(cls, conn, id : int, new_status : bool):
        await cls.update_generic(conn, id, "is_whitelist", new_status)
    
    @classmethod
    async def update_prefix(cls, conn, id : int, new_prefix : str):
        await cls.update_generic(conn, id, "prefix", new_prefix)

    @classmethod
    async def update_enable_log(cls, conn, id : int, new_status : bool):
        await cls.update_generic(conn, id, "enable_log", new_status)
    
    @classmethod
    async def update_log_channel(cls, conn, id : int, new_channel : int):
        await cls.update_generic(conn, id, "log_channel", new_channel)

    @classmethod
    async def bulk_update(cls, conn, id, new_values : dict):
        """
        Update all values in one SQL statement.

        Parameter:
        - `conn`: The connection.
            + Usually from `pool.acquire()`.
        - `id`: The user's id.
        - `new_values`: A dict of `{"col_name": value}`.
            + `col_name` must match the table's column.
            + Order can be arbitrary.
        """

        update_str = ""
        update_arg = []
        count = 1
        for column in new_values:
            update_str += f"{column} = (${count}), "
            update_arg.append(new_values[column])
            count += 1
        update_str = update_str[:-2]

        await conn.execute('''
            UPDATE DGuilds
            SET %s
            WHERE id = (%d);
        ''' % (update_str, id), *update_arg)

    @classmethod
    async def get_prefix(cls, conn, id : int) -> str:
        """
        Get the prefix for a guild.

        Important Parameter:
        - `id`: The guild's id.
        """
        guild_info = await cls.find_guild(conn, id)
        return guild_info["prefix"]

    class Role:
        """A group of methods dealing specifically with `DGuilds_ARoles` table."""
        @classmethod
        async def get_roles(cls, conn, guild_id : int) -> typing.List[typing.Optional[dict]]:
            """
            Get a list of self-assign roles in a guild.

            Important Parameter:
            - `guild_id`: The guild's id.
            """
            query = '''
                SELECT * FROM DGuilds_ARoles
                WHERE guild_id = ($1);
            '''

            result = await conn.fetch(query, guild_id)
            return [rec_to_dict(record) for record in result]
        
        @classmethod
        async def get_role(cls, conn, guild_id : int, role_id : int) -> typing.Optional[dict]:
            """
            Get a self-assign role.
            
            Important Parameter:
            - `guild_id`: The guild's id.
            - `role_id`: The role's id.
            """
            query = '''
                SELECT * FROM DGuilds_ARoles
                WHERE guild_id = ($1) AND role_id = ($2);
            '''

            result = await conn.fetchrow(query, guild_id, role_id)
            return rec_to_dict(result)
        
        @classmethod
        async def add_role(cls, conn, guild_id : int, role_id : int, description : str = "*None provided*"):
            """
            Make a role self-assignable.

            Important Parameter:
            - `guild_id`: The guild's id.
            - `role_id`: The role's id.
            - `description`: The description for this role.
            """
            existed = await cls.get_role(conn, guild_id, role_id)
            if existed is None:
                if description is None:
                    description = "*None provided*"
                
                query = '''
                    INSERT INTO DGuilds_ARoles
                    VALUES ($1, $2, $3);
                '''
                await conn.execute(query, guild_id, role_id, description)

        @classmethod
        async def remove_role(cls, conn, guild_id : int, role_id : int):
            """
            Make a role non-self-assignable.

            Important Parameter:
            - `guild_id`: The guild's id.
            - `role_id`: The role's id.
            """
            query = '''
                DELETE FROM DGuilds_ARoles
                WHERE guild_id = ($1) AND role_id = ($2);
            '''
            await conn.execute(query, guild_id, role_id)

class Member:
    """
    A group of methods dealing specifically with `DUsers_DGuilds` table.
    """

    @classmethod
    async def find_member(cls, conn, user_id : int, guild_id : int) -> typing.Optional[dict]:
        """
        Get a member's info.

        Important Parameter:
        - `user_id`: The user's id.
        - `guild_id`: The guild's id.
        """
        result = await conn.fetchrow('''
            SELECT *
            FROM DUsers_DGuilds
            WHERE user_id = ($1) AND guild_id = ($2);
        ''', user_id, guild_id)

        return rec_to_dict(result)
    
    @classmethod
    async def insert_member(cls, conn, member : discord.Member):
        """
        Insert a member.

        Important Parameter:
        - `member`: A Discord member.
        """
        member_existed = await Member.find_member(conn, member.id, member.guild.id)
        if member_existed is None:
            await insert_into(conn, "DUsers_DGuilds", [
                (member.id, member.guild.id)
            ])
    
    @classmethod
    async def update_generic(cls, conn, ids : typing.Tuple[int], col_name : str, new_value):
        return await conn.execute('''
            UPDATE DUsers_DGuilds
            SET %s = ($1)
            WHERE user_id = ($2) AND guild_id = ($3);
        ''' % col_name, new_value, ids[0], ids[1])
    
    class TempMute:
        """A group of methods dealing specifically with `DMembers_Tempmute`."""
        @classmethod
        async def get_mutes(cls, conn, lower_time_limit : dt.datetime, upper_time_limit : dt.datetime):
            """
            Get a list of mute entry within the time range.

            - If there are no entry in the time range, an empty list is returned.

            Important Parameter:
            - `lower_time_limit`: The minimum time to search.
            - `upper_time_limit`: The maximum time to search.
            """
            query = '''
                SELECT * FROM DMembers_Tempmute
                WHERE expire > ($1) AND expire <= ($2);
            '''
            result = await conn.fetch(query, lower_time_limit, upper_time_limit)
            if result == [None] * len(result):
                return []
            else:
                return [rec_to_dict(record) for record in result]
        @classmethod
        async def get_missed_mute(cls, conn, now : dt.datetime):
            """
            Get a list of passed mute entry based on the time provided.

            - If there are no such entry, an empty list is returned.

            Important Parameter:
            - `now`: The time to check.
            """
            query = '''
                SELECT * FROM DMembers_Tempmute
                WHERE expire < ($1);
            '''
            result = await conn.fetch(query, now)
            if result == [None] * len(result):
                return []
            else:
                return [rec_to_dict(record) for record in result]
        @classmethod
        async def add_entry(cls, conn, user_id : int, guild_id : int, expire : dt.datetime):
            """
            Add a mute entry.

            Important Parameter:
            - `user_id`: The user's id.
            - `guild_id`: The guild's id.
            - `expire`: The expired time.
            """
            query = '''
                INSERT INTO DMembers_Tempmute
                VALUES ($1, $2, $3);
            '''
            await conn.execute(query, user_id, guild_id, expire)
        @classmethod
        async def remove_entry(cls, conn, user_id : int, guild_id : int):
            """
            Remove a mute entry.
            
            Important Parameter:
            - `user_id`: The user's id.
            - `guild_id`: The guild's id.
            """
            query = '''
                DELETE FROM DMembers_Tempmute
                WHERE user_id = ($1) AND guild_id = ($2);
            '''

            await conn.execute(query, user_id, guild_id)
        @classmethod
        async def get_entry(cls, conn, user_id : int, guild_id : int):
            """
            Get a specific entry for a member.

            Important Parameter:
            - `user_id`: The user's id.
            - `guild_id`: The guild's id.
            """
            query = '''
                SELECT * FROM DMembers_Tempmute
                WHERE user_id = ($1) AND guild_id = ($2);
            '''
            
            return rec_to_dict(await conn.fetchrow(query, user_id, guild_id))
    
# Currently we still need some sort of function that scan the db periodically for some schedule stuffs. 



class Items:
    """A group of methods dealing specifically with `Items` table."""
    @classmethod
    async def get_whole_items(cls, conn) -> typing.List[typing.Optional[dict]]:
        """
        Get a list of all items, sorted by `inner_sort`.

        - If there are no items, a list of `None` is returned.
        """
        query = '''
            SELECT * FROM Items
            ORDER BY inner_sort;
        '''
        
        result = await conn.fetch(query)
        return [rec_to_dict(record) for record in result]
    @classmethod
    async def get_item(cls, conn, id : str) -> typing.Optional[dict]:
        """
        Get an item.

        Important Parameter:
        - `id`: The item's inner name.
        """
        query = '''
            SELECT * FROM Items
            WHERE id = ($1);
        '''

        result = await conn.fetchrow(query, id)
        return rec_to_dict(result)
    
    @classmethod
    async def create_item(cls, conn, *args):
        """
        Create an item.
        
        Important Parameter:
        - `args`: A list of attributes of an item. This list exclude the item's id and inner sort, and must
        follow the order listed in the table.
        """
        exist = await cls.get_item(conn, args[0][0])
        if exist is None:
            await insert_into(conn, "Items", [*args])

    @classmethod
    async def remove_item(cls, conn):
        pass
    
    @classmethod
    async def get_friendly_name(cls, conn, id : str) -> str:
        """
        Get the item's UI name.

        Important Parameter:
        - `id`: The item's id.
        """
        query = '''
            SELECT *
            FROM Items
            WHERE id = ($1);
        '''

        return await conn.fetchval(query, id, column = 3)

    @classmethod
    async def get_internal_name(cls, conn, friendly_name : str) -> str:
        """
        Get the item's id.

        Important Parameter:
        - `friendly_name`: The UI name of an item.
        """
        query = '''
            SELECT id
            FROM Items
            WHERE name = ($1);
        '''
        
        return await conn.fetchval(query, friendly_name)

class Notify:
    @classmethod
    async def get_notifies(cls, conn, lower_time_limit : dt.datetime, upper_time_limit : dt.datetime) -> typing.List[typing.Optional[dict]]:
        """
        Get all notifications that are within the interval.

        - If there are no such notifications, an empty list is returned.

        Important Parameter:
        - `lower_time_limit`: The start of the interval.
        - `upper_time_limit`: The end of the interval.
        """

        query = '''
            SELECT * FROM DNotify
            WHERE awake_time > ($1) AND awake_time <= ($2);
        '''

        result = await conn.fetch(query, lower_time_limit, upper_time_limit)
        
        if result == [None] * len(result):
            return []
        else:
            return [rec_to_dict(record) for record in result]
    
    @classmethod
    async def get_past_notify(cls, conn, now : dt.datetime) -> typing.List[typing.Optional[dict]]:
        """
        Get all notifications that passed the time.

        - If there are no such notification, an empty list is returned.

        Important Parameter:
        - `now`: The time to check.
        """
        query = '''
            SELECT * FROM DNotify
            WHERE awake_time < ($1);
        '''

        result = await conn.fetch(query, now)

        if result == [None] * len(result):
            return []
        else:
            return [rec_to_dict(record) for record in result]
    
    @classmethod
    async def add_notify(cls, conn, user_id : int, when : dt.datetime, message : str):
        """
        Add a notification entry.

        Important Parameter:
        - `user_id`: The user's id.
        - `when`: The time to notify.
        - `message`: The message to notify.
        """
        query = '''
            INSERT INTO DNotify (user_id, awake_time, message)
            VALUES ($1, $2, $3);
        '''
        await conn.execute(query, user_id, when, message)
    
    @classmethod
    async def remove_notify(cls, conn, id : int):
        """
        Remove a notification entry.

        Important Parameter:
        - `id`: The notification's id.
        """
        query = '''
            DELETE FROM DNotify
            WHERE id = ($1);
        '''

        await conn.execute(query, id)

def rec_to_dict(record : asyncpg.Record) -> typing.Optional[dict]:
    """
    Convert a record to a `dict`.

    - If the record is `None`, `None` is returned.

    Important Parameter:
    - `record`: The record.
    """
    if record is None:
        return None
    else:
        return dict(record)

