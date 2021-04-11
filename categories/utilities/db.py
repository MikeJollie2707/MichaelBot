from math import e
import discord
from discord.ext import commands

import datetime as dt
import typing

import asyncpg
from categories.utilities.loot import get_item_info

class MichaelBotDatabaseException(Exception):
    pass

class ItemNotPresent(MichaelBotDatabaseException):
    pass
class PotionNotActive(MichaelBotDatabaseException):
    pass
class EquipmentNotActive(MichaelBotDatabaseException):
    pass
class TooLargeRemoval(MichaelBotDatabaseException):
    pass
class ItemExpired(MichaelBotDatabaseException):
    pass

async def update_db(bot):
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
                        if user_existed is None:
                            await User.insert_user(conn, member)
                            await Member.insert_member(conn, member)
            
            items = get_item_info()
            for key in items:
                items[key].insert(0, key)
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

        Parameter:
        - `conn`: The connection you want to do.
            + It's usually just `pool.acquire()`.
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

        Parameter:
        - `conn`: The connection
            + Usually from `pool.acquire()`.
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

        Parameter:
        - `conn`: The connection.
            + Usually from `pool.acquire()`.
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
            UPDATE DUsers
            SET %s
            WHERE id = (%d)
        ''' % (update_str, id), *update_arg)
    
    @classmethod
    async def get_money(cls, conn, id) -> int:
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

        Internally this call `get_money()` and `update_money()`.
        """

        if amount > 0:
            money = await cls.get_money(conn, id)
            return await cls.update_money(conn, id, money + amount)
    @classmethod
    async def remove_money(cls, conn, id, amount : int):
        """
        Remove an amount of money from the user.
        If amount is negative, no changes are made.

        *If the resulting money is less than 0, the money is 0.*

        Internally this call `get_money()` and `update_money()`.
        """
        if amount > 0:
            money = await cls.get_money(conn, id)
            # No need to check because update_money() checks.
            return await cls.update_money(conn, id, money - amount)
    
    @classmethod
    async def inc_streak(cls, conn, id):
        """
        Increase the streak by 1.
        """

        user = await cls.find_user(conn, id)
        await cls.update_streak(conn, id, user["streak_daily"] + 1)

    class Inventory:
        """
        A group of methods mainly deals with DUsers_Items table.
        """

        # DUsers_Items
        @classmethod
        async def get_whole_inventory(cls, conn, user_id : int) -> typing.Optional[typing.List[dict]]:
            """
            Retrieve an entire inventory. `None` if the user has empty inventory.
            """

            # No need to JOIN in this method due to limited uses.
            query = '''
                SELECT * FROM DUsers_Items
                WHERE user_id = ($1);
            '''
            
            result = await conn.fetch(query, user_id)
            if result is None:
                return None
            
            return [rec_to_dict(row) for row in result]
        
        @classmethod
        async def get_one_inventory(cls, conn, user_id : int, item_id : int) -> typing.Optional[dict]:
            """
            Get an inventory slot.

            The structure of the resultant dictionary is the same as `Items.get_items()` structure, with
            the additional `quantity` keys.

            `None` if no such slot exist.
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

            `None` if no such equipments.

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
            Add an amount of item to the user's inventory slot.
            
            If the inventory slot (identified by both user_id and item_id) doesn't exist, it'll be created.

            **DO NOT USE THIS TO ADD ACTIVE EQUIPMENTS OR ACTIVE POTIONS**
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

            If the resultant amount is 0, the slot is deleted.
            If the item doesn't exist, the function raises `ItemNotPresent` exception.
            If the resultant amount < 0, the function raises `InvTooLargeRemoval` exception.
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
            item_existed = await cls.get_one_inventory(conn, user_id, item_id)
            if item_existed is None:
                return
            elif quantity <= 0:
                await cls.remove(conn, user_id, item_id, item_existed["quantity"])
            else:
                await cls.add(conn, user_id, item_id, quantity - item_existed["quantity"])

    class ActiveTools:
        # DUsers_ActiveTools
        @classmethod
        def get_tool_type(cls, tool_id : str) -> str:
            if "_pickaxe" in tool_id:
                return "pickaxe"
            elif "_axe" in tool_id:
                return "axe"
            elif "_sword" in tool_id:
                return "sword"
            elif "_rod" in tool_id:
                return "rod"

        @classmethod
        async def get_equipments(cls, conn, user_id : int) -> typing.Optional[typing.List[dict]]:
            """
            Get a list of active equipments.

            `None` if no active equipments.
            """
            query = '''
                SELECT Items.*, DUsers_ActiveTools.durability_left
                FROM DUsers_ActiveTools
                    INNER JOIN Items ON item_id = id
                WHERE user_id = ($1);
            '''

            result = await conn.fetch(query, user_id)
            return [rec_to_dict(record) for record in result]

        @classmethod
        async def get_equipment(cls, conn, tool_type : str, user_id : int) -> typing.Optional[dict]:
            """
            Get an active equipment based on its type.
            
            It is recommended to pass `tool_type` with `get_tool_type()`.
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
            tool = await cls.get_equipment(conn, cls.get_tool_type(tool_id), user_id)
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

            This method does not deal with the situation where the user already equipped a same tool type.
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
        async def unequip_tool(cls, conn, user_id : int, item_id : int):
            """
            Unequip the tool from the user.

            This destroys the items if the tool is used, otherwise, it's added back to the inventory.
            If the item is destroyed, it raises `ItemExpired`.
            """
            equipped = await cls.get_equipment(conn, cls.get_tool_type(item_id), user_id)
            if equipped is not None:
                query = '''
                    DELETE FROM DUsers_ActiveTools
                    WHERE user_id = ($1) AND item_id = ($2);
                '''

                await conn.execute(query, user_id, item_id)
                if equipped["durability_left"] == equipped["durability"]:
                    await User.Inventory.add(conn, user_id, item_id)
                else:
                    raise ItemExpired(f"Item {item_id}'s durability is forcefully returned to 0.")
            else:
                raise ItemNotPresent(f"Item {item_id} is not currently equipping by user {user_id}.")
    class ActivePortals:
        # DUsers_ActivePortals
        @classmethod
        async def get_portals(cls, conn, user_id : int) -> typing.Optional[typing.List[dict]]:
            query = '''
                SELECT Items.*, DUsers_ActivePortals.remain_uses
                FROM DUsers_ActivePortals
                    INNER JOIN Items ON item_id = id
                WHERE user_id = ($1);
            '''

            result = await conn.fetch(query, user_id)
            return [rec_to_dict(record) for record in result]
        @classmethod
        async def get_portal(cls, conn, user_id : int, portal_id : str) -> typing.Optional[dict]:
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
            # It is the bot's job to keep this table has no similar portals.
            portal = await Items.get_item(conn, portal_id)
            query = '''
                INSERT INTO DUsers_ActivePortals
                VALUES ($1, $2, $3);
            '''
            await conn.execute(query, user_id, portal_id, portal["durability"])
        @classmethod
        async def remove(cls, conn, user_id : int, portal_id : str):
            query = '''
                DELETE FROM DUsers_ActivePortals
                WHERE user_id = ($1) AND item_id = ($2);
            '''

            await conn.execute(query, user_id, portal_id)
        @classmethod
        async def dec_durability(cls, conn, user_id : int, portal_id : int, amount : int = 1):
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
        async def get_potions(cls, conn, user_id : int):
            query = '''
                SELECT Items.*, DUsers_ActivePotions.remain_uses
                FROM DUsers_ActivePotions
                    INNER JOIN Items ON item_id = id
                WHERE user_id = ($1);
            '''

            result = await conn.fetch(query, user_id)
            return [rec_to_dict(record) for record in result]
        @classmethod
        async def get_potion(cls, conn, user_id : int, potion_id : str):
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
            default_durability = (await Items.get_item(conn, potion_id))["durability"]
            from math import ceil
            return ceil(remaining / default_durability)
        @classmethod
        async def set_potion_active(cls, conn, user_id : int, potion_id : str, amount : int = 1):
            try:
                await User.Inventory.remove(conn, user_id, potion_id, amount)
            except ItemNotPresent as inp:
                raise inp
            except TooLargeRemoval as itlr:
                raise itlr
            
            await cls.add_active_potion(conn, user_id, potion_id, amount)
        
        @classmethod
        async def add_active_potion(cls, conn, user_id : int, potion_id : int, amount : int = 1):
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
    async def find_guild(cls, conn, id : int) -> dict:
        """
        Find a guild data in `DGuilds`.

        If a guild is found, it'll return a `dict`, otherwise it'll return `None`.

        Parameter:
        - `conn`: The connection
            + Usually from `pool.acquire()`
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

        Parameter:
        - `conn`: The connection
            + Usually from `pool.acquire()`.
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

    #@classmethod
    #async def update_autorole(cls, conn, id : int, new_list : list):
    #    pass

    #@classmethod
    #async def update_customcmd(cls, conn, id : int, new_list : list):
    #    pass

    @classmethod
    async def get_prefix(cls, conn, id : int):
        guild_info = await cls.find_guild(conn, id)
        return guild_info["prefix"]

class Member:
    """
    A group of methods dealing specifically with `DUsers_DGuilds` table.
    """

    @classmethod
    async def find_member(cls, conn, user_id : int, guild_id : int) -> dict:
        result = await conn.fetchrow('''
            SELECT *
            FROM DUsers_DGuilds
            WHERE user_id = ($1) AND guild_id = ($2);
        ''', user_id, guild_id)

        return rec_to_dict(result)
    
    @classmethod
    async def insert_member(cls, conn, member : discord.Member):
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
    
# Currently we still need some sort of function that scan the db periodically for some schedule stuffs. 



class Items:
    @classmethod
    async def get_whole_items(cls, conn) -> typing.Optional[typing.List[dict]]:
        query = '''
            SELECT * FROM Items
            ORDER BY inner_sort;
        '''
        
        result = await conn.fetch(query)
        return [rec_to_dict(record) for record in result]
    @classmethod
    async def get_item(cls, conn, id : str) -> typing.Optional[dict]:
        query = '''
            SELECT * FROM Items
            WHERE id = ($1);
        '''

        result = await conn.fetchrow(query, id)
        return rec_to_dict(result)
    
    @classmethod
    async def create_item(cls, conn, *args):
        exist = await cls.get_item(conn, args[0][0])
        if exist is None:
            await insert_into(conn, "Items", [*args])

    @classmethod
    async def remove_item(cls, conn):
        pass
    
    @classmethod
    async def get_friendly_name(cls, conn, id : str) -> str:
        query = '''
            SELECT *
            FROM Items
            WHERE id = ($1);
        '''

        return await conn.fetchval(query, id, column = 3)

    @classmethod
    async def get_internal_name(cls, conn, friendly_name : str) -> str:
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

        Important Parameter:
        - `lower_time_limit`: The start of the interval.
        - `upper_time_limit`: The end of the interval.

        Return: `[]` if there are no notifications within the interval, `list(dict)` if there is.
        """

        query = '''
            SELECT * FROM DNotify
            WHERE awake_time > ($1) AND awake_time <= ($2);
        '''

        result = await conn.fetch(query, lower_time_limit, upper_time_limit)
        
        if result is None:
            return []
        else:
            return [dict(record) for record in result]
    
    @classmethod
    async def get_past_notify(cls, conn, now : dt.datetime) -> typing.List[typing.Optional[dict]]:
        """
        Get all notifications that passed the time.

        Important Parameter:
        - `now`: The time to check.

        Return: `[]` if there are no such notifications, `list(dict)` if there is.
        """
        query = '''
            SELECT * FROM DNotify
            WHERE awake_time < ($1);
        '''

        result = await conn.fetch(query, now)

        if result is None:
            return []
        else:
            return [dict(record) for record in result]
    
    @classmethod
    async def add_notify(cls, conn, user_id : int, when : dt.datetime, message : str):
        query = '''
        INSERT INTO DNotify (user_id, awake_time, message)
        VALUES ($1, $2, $3);
        '''
        await conn.execute(query, user_id, when, message)
    
    @classmethod
    async def remove_notify(cls, conn, id : int):
        query = '''
            DELETE FROM DNotify
            WHERE id = ($1);
        '''

        await conn.execute(query, id)

def rec_to_dict(record : asyncpg.Record) -> dict:
    if record is None:
        return None
    else:
        return dict(record)

