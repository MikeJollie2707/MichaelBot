import asyncpg
import hikari
import lightbulb

import typing as t

def record_to_dict(record: asyncpg.Record) -> t.Optional[dict]:
    '''
    Convert a `Record` into a dictionary, or `None` if `record` is also `None`.
    '''
    if record is None: return None
    else: return dict(record)

async def legacy_insert_into(conn, table_name: str, *args):
    '''
    Insert values into `table_name`.

    Warning: This function is an old function from pre-rewrite. It is advised to do the logic by yourself.
    '''
    arg_str = "("
    # max(*args, key = len): Get the longest tuple in the list.
    for j in range(len(max(*args, key = len))):
        arg_str += f"${j + 1}, "
    arg_str = arg_str[:-2] + ')'

    await conn.executemany('''
        INSERT INTO %s
        VALUES %s
    ''' % (table_name, arg_str), *args
    )

def insert_into_query(table_name: str, len_col: int) -> str:
    '''
    Return the query to insert into a table that has `len_col` columns.
    '''
    arg_str = "("
    for index in range(len_col):
        arg_str += f"${index + 1}, "
    arg_str = arg_str[:-2] + ')'

    return f"INSERT INTO {table_name} VALUES {arg_str} ON CONFLICT DO NOTHING;"

async def __get_all__(conn, query):
    '''
    Warning: This methods should NOT be called. Instead, use `table_name.get_all(conn)`.


    '''
    
    result = await conn.fetch(query)
    return [record_to_dict(record) for record in result]

async def __get_one__(conn, query, *constraints):
    record = await conn.fetchrow(query, *constraints)
    return record_to_dict(record)

# This hurt my bloody soul to name class lower case but it's SQL.

class default_commands:
    @staticmethod
    async def get_all(cls, conn):
        query = '''
            SELECT * FROM default_commands
            ORDER BY default_commands.name;
        '''

        return await __get_all__(conn, query)

class guilds:
    @classmethod
    async def get_all(cls, conn):
        query = '''
            SELECT * FROM guilds
            ORDER BY guilds.name;
        '''

        return await __get_all__(conn, query)
    @classmethod
    async def get_one(cls, conn, id: int):
        query = '''
            SELECT * FROM guilds
            WHERE id = ($1);
        '''

        #record = await conn.fetchrow(query, guild_id)
        #return record_to_dict(record)
        return await __get_one__(conn, query, id)
    @classmethod
    async def add_single(cls, conn, guild: hikari.Guild):
        existed = await cls.get_one(conn, guild.id)
        query = insert_into_query("guilds", 5)
        
        await conn.execute(query, (guild.id, guild.name, True, '$', False))
    @classmethod
    async def add_many(cls, conn, guilds: t.Tuple[hikari.Guild]):
        query = insert_into_query("guilds", 5)

        args = []
        for guild in guilds:
            args.append((guild.id, guild.name, True, '$', False))
        
        await conn.executemany(query, args)
    @classmethod
    async def remove(cls, conn, id: int):
        query = '''
            DELETE FROM guilds
            WHERE id = ($1);
        '''

        await conn.execute(query, id)
    @classmethod
    async def update_column(cls, conn, id: int, column: str, new_value):
        query = f'''
            UPDATE guilds
            SET {column} = ($1)
            WHERE id = ($2);
        '''

        await conn.execute(query, new_value, id)

