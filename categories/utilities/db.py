import discord
from discord.ext import commands

import datetime
import typing

import asyncpg
from asyncpg import exceptions as pg_exception

async def init_db(bot):
    # Create DB if it's not established
    async with bot.pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS dGuilds (
                    id INT8 PRIMARY KEY,
                    name TEXT NOT NULL,
                    is_whitelist BOOL DEFAULT TRUE,
                    autorole_list INT8[],
                    customcmd_list TEXT[]
                );
            ''')
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS dUsers (
                    id INT8 PRIMARY KEY,
                    name TEXT NOT NULL,
                    is_whitelist BOOL DEFAULT TRUE,
                    money INT8 DEFAULT 0,
                    last_daily TIMESTAMP,
                    streak_daily INT4 DEFAULT 0
                );
            ''')
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS dUsers_dGuilds (
                    user_id INT8 NOT NULL REFERENCES dUsers(id) ON UPDATE CASCADE ON DELETE CASCADE,
                    guild_id INT8 NOT NULL REFERENCES dGuilds(id) ON UPDATE CASCADE ON DELETE CASCADE,
                    tempmute_end TIMESTAMP,
                    PRIMARY KEY (user_id, guild_id)
                );
            ''')

        for guild in bot.guilds:
            # Alternative way: perform an update_guild(), then if the
            # status is UPDATE 0, meaning it doesn't exist, then insert it.
            # This will probably make it in a transaction, rather than separate.
            try:
                await Guild.insert_guild(conn, guild)
            except pg_exception.UniqueViolationError:
                pass
            for member in guild.members:
                try:
                    await User.insert_user(conn, member)
                except pg_exception.UniqueViolationError:
                    pass
                    
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

async def insert_guild(conn, *args):
    """
    Insert a guild data into table `dGuilds`.

    This will be rewritten into the same format as `insert_member`.

    Parameter:
    - `conn`: The connection you want to do.
        + It's usually just `pool.acquire()`.
    - `*args`: This must be a list of tuples.
        + `len(tuple)` must equals to the number of column you want to insert.
    """

    await insert_into(conn, "dGuilds", *args)

async def insert_member(conn, member : discord.Member):
    """
    Insert a member data into the database.

    Specifically, it adds to `dUsers`, `dUsers_dGuilds`.

    Parameter:
    - `conn`: The connection you want to do.
        + It's usually just `pool.acquire()`.
    - `member`: The member.
    """

    member_existed = await User.find_user(conn, member.id)
    if member_existed is None:
        await insert_into(conn, "dUsers", [
            (member.id, member.name, True, 0, None, 0)
        ])
    
        await insert_into(conn, "dUsers_dGuilds", [
            (member.id, member.guild.id, None)
        ])

async def update_by_id(conn, table_name : str, *args):
    # Might remove this method
    arg_str = "("
    for j in range(len(max(*args, key = len))):
        arg_str += '$' + str(j + 1) + ", "
    arg_str = arg_str[:-2] + ')'

    await conn.executemany('''
        UPDATE %s
        SET 
    ''')

class User:
    """
    A group of methods dealing specifically with `dUsers` table.
    For `dUsers_dGuilds` table, refers to `Member` instead.
    """

    @classmethod
    async def find_user(cls, conn, user_id : int) -> asyncpg.Record:
        """
        Find a member data in `dUsers`.

        If a member is found, it'll return a `Record` of the member, otherwise it'll return `None`.

        Parameter:
        - `conn`: The connection you want to do.
            + It's usually just `pool.acquire()`.
        - `user_id`: The user's id.
        """

        result = await conn.fetchrow('''
            SELECT *
            FROM dUsers
            WHERE id = %d
        ''' % user_id)

        return result

    @classmethod
    async def insert_user(cls, conn, member : discord.Member):
        """
        Insert a default user data into `dUsers`.

        If the user already exist, this method do nothing.

        Parameter:
        - `conn`: The connection
            + Usually from `pool.acquire()`.
        - `member`: A Discord member to insert.
        """

        member_existed = await cls.find_user(conn, member.id)
        if member_existed is None:
            await insert_into(conn, "dUsers", [
                (member.id, member.name, True, 0, None, 0)
            ])
    
    @classmethod
    async def update_generic(cls, conn, id : int, col_name : str, new_value):
        """
        A generic method to update a column in `dUsers` table.
        
        This method's variations `update_...` is recommended. Only use this when there's a new column.

        Parameter:
        - `conn`: The connection.
            + Usually from `pool.acquire()`.
        - `id`: The member id.
        - `col_name`: The column name in the table. **This must be exactly the same as in the table**.
        - `new_value`: The new value.
        """
        await conn.execute('''
            UPDATE dUsers
            SET %s = ($1)
            WHERE id = ($2);
        ''' % col_name, new_value, id)

    @classmethod
    async def update_name(cls, conn, id, new_name : str):
        await cls.update_generic(conn, id, "name", new_name)
    @classmethod
    async def update_whitelist(cls, conn, id, new_status : bool):
        await cls.update_generic(conn, id, "is_whitelist", new_status)
    @classmethod
    async def update_money(cls, conn, id, new_money : int):
        # Money can't be lower than 0, for now.
        if new_money <= 0:
            new_money = 0
        
        await cls.update_generic(conn, id, "money", new_money)
    @classmethod
    async def update_last_daily(cls, conn, id, new_last_daily : datetime.datetime):
        await cls.update_generic(conn, id, "last_daily", new_last_daily)
    @classmethod
    async def update_streak(cls, conn, id, new_streak : int):
        await cls.update_generic(conn, id, "streak_daily", new_streak)
    
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
        member_info = record_to_dict(await cls.find_user(conn, id))
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
            await cls.update_money(conn, id, money + amount)
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
            await cls.update_money(conn, id, money - amount)

class Guild:
    """
    A group of methods dealing specifically with `dGuilds` table.
    """

    @classmethod
    async def find_guild(cls, conn, id : int):
        result = await conn.fetchrow('''
            SELECT *
            FROM dGuilds
            WHERE id = ($1)
        ''', id)

        return result
    
    @classmethod
    async def insert_guild(cls, conn, guild : discord.Guild):
        guild_existed = await cls.find_guild(conn, guild.id)
        if guild_existed is None:
            await insert_into(conn, "dGuilds", [
                (guild.id, guild.name, True, [], [])
            ])

    @classmethod
    async def update_generic(cls, conn, id : int, col_name : str, new_value):
        await conn.execute('''
            UPDATE dGuilds
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
    async def update_autorole(cls, conn, id : int, new_list : list):
        await cls.update_generic(conn, id, "autorole_list", new_list)

    @classmethod
    async def update_customcmd(cls, conn, id : int, new_list : list):
        pass

class Member:
    pass
    
    

def record_to_dict(record : asyncpg.Record) -> dict:
    result = {}
    if record is None:
        return None
    
    for item in record.items():
        result[item[0]] = item[1]
    
    return result

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
