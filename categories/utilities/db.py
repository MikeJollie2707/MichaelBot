import discord
from discord.ext import commands

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
                        guild_id INT8 PRIMARY KEY,
                        name TEXT NOT NULL
                    );
                ''')
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS dUsers (
                        user_id INT8 PRIMARY KEY,
                        name TEXT NOT NULL
                    );
                ''')
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS dUsers_dGuilds (
                        user_id INT8 NOT NULL,
                        guild_id INT8 NOT NULL
                    );
                ''')

            for guild in bot.guilds:
                try:
                    await cls.insert_guild(conn, [(guild.id, guild.name)])
                except pg_exception.UniqueViolationError:
                    pass
                for member in guild.members:
                    try:
                        await cls.insert_user(conn, [(member.id, member.name)])
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
        await conn.executemany('''
            INSERT INTO %s VALUES ($1, $2)
        ''' % table_name, *args
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
    async def insert_user(cls, conn, *args):
        """
        Insert a user data into table `dUsers`.

        Parameter:
        - `conn`: The connection you want to do.
            + It's usually just `pool.acquire()`.
        - `*args`: This must be a list of tuples.
            + `len(tuple)` must equals to the number of column you want to insert.
        """
        await cls.insert_into(conn, "dUsers", *args)
    
    @classmethod
    async def insert_member(cls, conn, member : discord.Member):
        """
        Insert a member data into table `dUsers_dGuilds`.

        Parameter:
        - `conn`: The connection you want to do.
            + It's usually just `pool.acquire()`.
        - `member`: The member.
        """
        await cls.insert_into(conn, "dUsers_dGuilds", [
            (member.id, member.guild.id)
        ])

    @classmethod
    async def drop_all_table(cls, bot):
        async with bot.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute('''
                    DROP TABLE dUsers, dGuilds, dUsers_dGuilds;
                ''')


    @classmethod
    async def to_dict(cls, bot) -> dict:
        """
        Transform the entire database into dictionary format.

        It is in the following format:
        `{
            guild_id: [
                member_id,
                member_id,
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
