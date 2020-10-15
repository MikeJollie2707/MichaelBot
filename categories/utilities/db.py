import discord
from discord.ext import commands

import datetime
import typing

import asyncpg
from asyncpg import exceptions as pg_exception

class DB(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @classmethod
    async def init_db(cls, bot):
        # Create DB if it's not established
        async with bot.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS dGuilds (
                        id INT8 PRIMARY KEY,
                        name TEXT NOT NULL
                    );
                ''')
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS dUsers (
                        id INT8 PRIMARY KEY,
                        name TEXT NOT NULL,
                        money INT8 DEFAULT 0,
                        last_daily TIMESTAMP,
                        streak_daily INT4 DEFAULT 0
                    );
                ''')
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS dUsers_dGuilds (
                        user_id INT8 NOT NULL,
                        guild_id INT8 NOT NULL
                    );
                ''')

            for guild in bot.guilds:
                # Alternative way: perform an update_guild(), then if the
                # status is UPDATE 0, meaning it doesn't exist, then insert it.
                # This will probably make it in a transaction, rather than separate.
                try:
                    await cls.insert_guild(conn, [(guild.id, guild.name)])
                except pg_exception.UniqueViolationError:
                    pass
                for member in guild.members:
                    try:
                        await cls.insert_member(conn, member)
                    except pg_exception.UniqueViolationError:
                        pass

    @classmethod
    async def insert_into(cls, conn, table_name : str, *args):
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
    
    @classmethod
    async def insert_guild(cls, conn, *args):
        """
        Insert a guild data into table `dGuilds`.

        This will be rewritten into the same format as `insert_member`.

        Parameter:
        - `conn`: The connection you want to do.
            + It's usually just `pool.acquire()`.
        - `*args`: This must be a list of tuples.
            + `len(tuple)` must equals to the number of column you want to insert.
        """

        await cls.insert_into(conn, "dGuilds", *args)
    
    @classmethod
    async def insert_member(cls, conn, member : discord.Member):
        """
        Insert a member data into the database.

        Specifically, it adds to `dUsers`, `dUsers_dGuilds`.

        Parameter:
        - `conn`: The connection you want to do.
            + It's usually just `pool.acquire()`.
        - `member`: The member.
        """

        member_existed = await cls.find_member(conn, member)
        if member_existed is None:
            await cls.insert_into(conn, "dUsers", [
                (member.id, member.name, 0, None, 0)
            ])
        
        await cls.insert_into(conn, "dUsers_dGuilds", [
            (member.id, member.guild.id)
        ])
    
    @classmethod
    async def find_member(cls, conn, member : discord.Member):
        """
        Find a member data in `dUsers`.

        If a member is found, it'll return a `Record` of the member, otherwise it'll return `None`.

        Parameter:
        - `conn`: The connection you want to do.
            + It's usually just `pool.acquire()`.
        - `member`: The member.
        """

        result = await conn.fetchrow('''
            SELECT *
            FROM dUsers
            WHERE id = %d
        ''' % member.id)

        return result

    @classmethod
    async def update_by_id(cls, conn, table_name : str, *args):
        arg_str = "("
        for j in range(len(max(*args, key = len))):
            arg_str += '$' + str(j + 1) + ", "
        arg_str = arg_str[:-2] + ')'

        await conn.executemany('''
            UPDATE %s
            SET 
        ''')

    @classmethod
    async def update_member(cls, conn, member : typing.Union[tuple, dict]):
        member_tuple = []
        if isinstance(member, dict):
            for key in member:
                member_tuple.append(member[key])
        else:
            member_tuple = member
        
        member_tuple = tuple(member_tuple)

    @classmethod
    def record_to_dict(cls, record : asyncpg.Record):
        result = {}
        for item in record.items():
            result[item[0]] = item[1]
        
        return result

    @classmethod
    async def drop_all_table(cls, bot):
        async with bot.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute('''
                    DROP TABLE dUsers, dGuilds, dUsers_dGuilds, dUsersInfo;
                ''')


    @classmethod
    async def to_dict(cls, bot) -> dict:
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
