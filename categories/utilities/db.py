import discord
from discord.ext import commands

import datetime
import typing

import asyncpg
from categories.utilities.loot import get_item_info

async def update_db(bot):
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
    async def find_user(cls, conn, user_id : int) -> asyncpg.Record:
        """
        Find a member data in `DUsers`.

        If a member is found, it'll return a `Record` of the member, otherwise it'll return `None`.

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

        return result

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
                (member.id, member.name, True, 0, None, 0)
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

        return await conn.execute('''
            UPDATE DUsers
            SET %s = ($1)
            WHERE id = ($2);
        ''' % col_name, new_value, id)

    @classmethod
    async def update_name(cls, conn, id, new_name : str):
        return await cls.__update_generic__(conn, id, "name", new_name)
    @classmethod
    async def update_whitelist(cls, conn, id, new_status : bool):
        return await cls.__update_generic__(conn, id, "is_whitelist", new_status)
    @classmethod
    async def update_money(cls, conn, id, new_money : int):
        # Money can't be lower than 0, for now.
        if new_money <= 0:
            new_money = 0
        
        return await cls.__update_generic__(conn, id, "money", new_money)
    @classmethod
    async def update_last_daily(cls, conn, id, new_last_daily : datetime.datetime):
        return await cls.__update_generic__(conn, id, "last_daily", new_last_daily)
    @classmethod
    async def update_streak(cls, conn, id, new_streak : int):
        return await cls.__update_generic__(conn, id, "streak_daily", new_streak)
    
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
            UPDATE dUsers
            SET %s
            WHERE id = (%d)
        ''' % (update_str, id), *update_arg)
    
    @classmethod
    async def get_money(cls, conn, id) -> int:
        member_info = dict(await cls.find_user(conn, id))
        return member_info["money"]
    
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

class Guild:
    """
    A group of methods dealing specifically with `DGuilds` table.
    """

    @classmethod
    async def find_guild(cls, conn, id : int):
        """
        Find a guild data in `DGuilds`.

        If a guild is found, it'll return a `Record`, otherwise it'll return `None`.

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

        return result
    
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
        
        return await conn.execute('''
            UPDATE DGuilds
            SET %s = ($1)
            WHERE id = ($2);
        ''' % col_name, new_value, id)
    
    @classmethod
    async def update_name(cls, conn, id : int, new_name : str):
        return await cls.update_generic(conn, id, "name", new_name)
    
    @classmethod
    async def update_whitelist(cls, conn, id : int, new_status : bool):
        return await cls.update_generic(conn, id, "is_whitelist", new_status)
    
    @classmethod
    async def update_prefix(cls, conn, id : int, new_prefix : str):
        await cls.update_generic(conn, id, "prefix", new_prefix)

    @classmethod
    async def update_enable_log(cls, conn, id : int, new_status : bool):
        await cls.update_generic(conn, id, "enable_log", new_status)
    
    @classmethod
    async def update_log_channel(cls, conn, id : int, new_channel : int):
        await cls.update_generic(conn, id, "log_channel", new_channel)

    #@classmethod
    #async def update_autorole(cls, conn, id : int, new_list : list):
    #    pass

    #@classmethod
    #async def update_customcmd(cls, conn, id : int, new_list : list):
    #    pass

    @classmethod
    async def get_prefix(cls, conn, id : int):
        guild_info = dict(await cls.find_guild(conn, id))
        return guild_info["prefix"]

class Member:
    """
    A group of methods dealing specifically with `DUsers_DGuilds` table.
    """

    @classmethod
    async def find_member(cls, conn, user_id : int, guild_id : int):
        result = await conn.fetchrow('''
            SELECT *
            FROM DUsers_DGuilds
            WHERE user_id = ($1) AND guild_id = ($2);
        ''', user_id, guild_id)

        return result
    
    @classmethod
    async def insert_member(cls, conn, member : discord.Member):
        member_existed = await Member.find_member(conn, member.id, member.guild.id)
        if member_existed is None:
            await insert_into(conn, "DUsers_DGuilds", [
                (member.id, member.guild.id, None)
            ])
    
    @classmethod
    async def update_generic(cls, conn, ids : typing.Tuple[int], col_name : str, new_value):
        return await conn.execute('''
            UPDATE DUsers_DGuilds
            SET %s = ($1)
            WHERE user_id = ($2) AND guild_id = ($3);
        ''' % col_name, new_value, ids[0], ids[1])
    
# Currently we still need some sort of function that scan the db periodically for some schedule stuffs. 

class Inventory:
    """
    A group of methods mainly deals with DUsers_Items table.
    """

    @classmethod
    async def get_whole_inventory(cls, conn, user_id : int):
        query = '''
            SELECT * FROM DUsers_Items
            WHERE user_id = ($1);
        '''
        
        result = await conn.fetch(query, user_id)
        if result is None:
            return None
        
        return [rec_to_dict(row) for row in result]
    
    @classmethod
    async def get_one_inventory(cls, conn, user_id, item_id):
        query = '''
            SELECT * FROM DUsers_Items
            WHERE user_id = ($1) AND item_id = ($2);
        '''
        
        result = await conn.fetchrow(query, user_id, item_id)
        return rec_to_dict(result)
    
    @classmethod
    async def add(cls, conn, user_id, item_id, amount = 1):
        """
        Add an amount of item to the user's inventory slot.
        
        If the inventory slot (identified by both user_id and item_id) doesn't exist, it'll be created.
        """

        item_existed = await cls.get_one_inventory(conn, user_id, item_id)
        if item_existed is None:
            query = '''
                INSERT INTO DUsers_Items
                VALUES ($1, $2, $3, $4);
            '''
            await conn.execute(query, user_id, item_id, amount, False)
        else:
            query = '''
                UPDATE DUsers_Items
                SET quantity = ($1)
                WHERE user_id = ($2) AND item_id = ($3);
            '''

            await conn.execute(query, item_existed["quantity"] + amount, user_id, item_id)
    
    @classmethod
    async def remove(cls, conn, user_id, item_id, amount = 1) -> str:
        """
        Remove an amount of item from the user's inventory slot.

        If the resultant amount is 0, the slot is deleted.
        If the resultant amount is < 0, or the item doesn't exist, the function return an empty string to test `is None`.
        """

        item_existed = await cls.get_one_inventory(conn, user_id, item_id)
        if item_existed is None:
            return ""
        else:
            if item_existed["quantity"] - amount == 0:
                query = '''
                    DELETE FROM DUsers_Items
                    WHERE user_id = ($1) AND item_id = ($2);
                '''

                await conn.execute(query, user_id, item_id)
            
            elif item_existed["quantity"] - amount < 0:
                return ""
            else:
                query = '''
                    UPDATE DUsers_Items
                    SET quantity = ($1)
                    WHERE user_id = ($2) AND item_id = ($3);
                '''

                await conn.execute(query, item_existed["quantity"] - amount, user_id, item_id)
        
    @classmethod
    async def update(cls, conn, user_id, item_id, quantity):
        item_existed = await cls.get_one_inventory(conn, user_id, item_id)
        if item_existed is None:
            return
        elif quantity <= 0:
            await cls.remove(conn, user_id, item_id, item_existed["quantity"])
        else:
            await cls.add(conn, user_id, item_id, quantity - item_existed["quantity"])

    @classmethod
    async def find_equip(cls, conn, tool_type : str, user_id):
        query = f'''
            SELECT * FROM DUsers_Items
            WHERE item_id LIKE '%\_{tool_type}' AND is_main = TRUE AND user_id = ($1);
        '''

        result = await conn.fetchrow(query, user_id)
        return rec_to_dict(result)

    @classmethod
    async def equip_tool(cls, conn, user_id, item_id):
        query = '''
            UPDATE DUsers_Items
            SET is_main = TRUE
            WHERE user_id = ($1) AND item_id = ($2);
        '''

        await conn.execute(query, user_id, item_id)
    
    @classmethod
    async def unequip_tool(cls, conn, user_id, item_id):
        query = '''
            UPDATE DUsers_Items
            SET is_main = FALSE
            WHERE user_id = ($1) AND item_id = ($2);
        '''

        await conn.execute(query, user_id, item_id)

    @classmethod
    async def get_equip_pickaxe(cls, conn, user_id):
        query = '''
            SELECT item_id
            FROM DUsers_Items
            WHERE user_id = ($1) AND is_main = TRUE;
        '''

        return await conn.fetchval(query, user_id)

class Items:
    @classmethod
    async def create_item(cls, conn, *args):
        exist = await cls.get_item(conn, args[0][0])
        if exist is None:
            await insert_into(conn, "Items", [*args])

    @classmethod
    async def get_item(cls, conn, id : str) -> dict:
        query = '''
            SELECT * FROM Items
            WHERE id = ($1);
        '''

        result = await conn.fetchrow(query, id)
        return rec_to_dict(result)

    @classmethod
    async def remove_item(cls, conn):
        pass
    
    @classmethod
    async def get_friendly_name(cls, conn, id : str) -> str:
        query = '''
            SELECT name
            FROM Items
            WHERE id = ($1);
        '''

        return await conn.fetchval(query, id, column = 2)

    @classmethod
    async def get_internal_name(cls, conn, friendly_name : str) -> str:
        query = '''
            SELECT id
            FROM Items
            WHERE name = ($1);
        '''
        
        return await conn.fetchval(query, friendly_name)
    
    @classmethod
    async def get_prices(cls, conn, id : str):
        item = await cls.get_item(conn, id)
        if item is None:
            return None
        else:
            return (item["buy_price"], item["sell_price"])

class Notify:
    @classmethod
    async def get_notify(cls, conn, lower_time_limit, upper_time_limit):
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
    async def get_past_notify(cls, conn, now):
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
    async def add_notify(cls, conn, user_id : int, when : datetime.datetime, message : str):
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

async def to_dict(bot) -> dict:
    """
    Transform the entire database into dictionary format. (need update)

    It is in the following format:
    `{
        guild_id: [
            member_id1,
            member_id2,
            ...
        ]
    }`
    """
    # Transfer the DB to dictionary
    dictionary = {}
    async with bot.pool.acquire() as conn:
        async with conn.transaction():
            result = await conn.fetch('''
                SELECT *
                FROM dUsers_dGuilds;
            '''
            )

            for record in result:
                if dictionary.get(record["guild_id"]) is None:
                    dictionary[record["guild_id"]] = [record["user_id"]]
                else:
                    dictionary[record["guild_id"]].append(record["user_id"])
    
    return dictionary
