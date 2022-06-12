# The code uses a lot of `id`, which turns out to be shadowing the builtin `id()`.
#pylint: disable=redefined-builtin

'''Contains many functions that hide all "naked" SQL to use.'''

# NOTE: Current flaw is adding/removing won't give any special status if entry doesn't exist.
import datetime as dt
import typing as t

import asyncpg
import hikari

class Error(Exception):
    '''A base error for high-level PostgreSQL operations.'''

class GetError(Error):
    '''A base error for SELECT operations.
    
    Notes
    -----
    This should only be raised when `get_x()` is implicitly called.
    This will NOT be raised if the user explicitly calls `get_x()`.
    '''

class InsertError(Error):
    '''A base error for INSERT operations.'''

class DeleteError(Error):
    '''A base error for DELETE operations.'''

class UpdateError(Error):
    '''A base error for UPDATE operations.'''

class DuplicateArrayElement(UpdateError):
    '''Raised when trying to add an element that's already available in a non-duplicate list.'''

def record_to_dict(record: asyncpg.Record, /) -> t.Optional[dict]:
    '''Convert a `Record` into a `dict` or `None` if the object is already `None`.

    This is for convenience purpose, where `dict(Record)` will return `{}` which is not an accurate
    representation of empty. `obj is None` or `obj is not None` is more obvious to anyone than
    `bool(obj)` or `not bool(obj)`.

    Args:
        record (asyncpg.Record): The record to convert.

    Returns:
        t.Optional[dict]: `dict` or `None`.
    '''
    
    if record is None: 
        return None
    return dict(record)

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

    await conn.executemany(f'''
        INSERT INTO {table_name}
        VALUES {arg_str}
    ''', *args
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

async def __get_all__(conn, query: str, *, where: t.Callable[[dict], bool] = lambda r: True) -> list[dict]:
    '''Run a `SELECT` statement and return a list of objects.

    This should NOT be used outside of the module. Instead, use `table_name.get_all()`.

    Args:
        conn: Database connection.
        query (str): The `SELECT` statement to run. This should not contain `WHERE` clause.
            Conditions should be set in `where` parameter.
        where (Callable[[dict], bool], optional): Additional conditions to filter.
            By default, no condition is applied (always return `True`).

    Returns:
        list[dict]: A list of `dict` or empty list.
    '''

    result = await conn.fetch(query)
    l = []
    record_obj = None
    for record in result:
        record_obj = record_to_dict(record)
        if record_obj is None or (record_obj is not None and where(record_obj)):
            l.append(record_obj)
    
    return l

async def __get_one__(conn, query: str, *constraints) -> t.Optional[dict]:
    '''Run a `SELECT` statement and return the first object that matches the constraints.

    Args:
        conn: Database connection.
        query (str): The `SELECT` statement to run. This should contain a `WHERE` clause.
        constraints: Arguments to be formatted into the query.

    Returns:
        Optional[dict]: A `dict` or `None` if no object is found.
    '''
    
    record = await conn.fetchrow(query, *constraints)
    return record_to_dict(record)

async def run_and_return_count(conn: asyncpg.Connection, *args, **kwargs) -> t.Optional[int]:
    '''Execute an SQL operation and return the number of entries affected.

    Warnings
    --------
    This is meant to run INSERT, DELETE, and UPDATE statements. Other statement might or might not work.

    Parameters
    ----------
    conn : asyncpg.Connection
        The connection to execute.
    *args : tuple
        The arguments to pass into `conn.execute()`
    **kwargs: dict
        The arguments to pass into `conn.execute()`

    Returns
    -------
    t.Optional[int]
        The number of rows affected. If the operation doesn't return the row count, `None` is returned.
    '''
    status = await conn.execute(*args, **kwargs)
    
    # INSERT returns "INSERT oid count".
    try:
        count = int(status.split()[-1])
        return count
    except ValueError:
        return None
    
class Guilds:
    '''Functions to interact with the `Guilds` table.'''
    @classmethod
    async def get_all(cls, conn):
        return await cls.get_all_where(conn)
    @classmethod
    async def get_all_where(cls, conn, *, where: t.Callable[[dict], bool] = lambda r: True):
        query = '''
            SELECT * FROM Guilds
            ORDER BY Guilds.name;
        '''

        return await __get_all__(conn, query, where = where)
    @classmethod
    async def get_one(cls, conn, id: int):
        query = '''
            SELECT * FROM Guilds
            WHERE id = ($1);
        '''

        return await __get_one__(conn, query, id)
    
    @classmethod
    async def add_one(cls, conn, guild: hikari.Guild):
        query = insert_into_query("Guilds", 4)
        
        await conn.execute(query, guild.id, guild.name, True, '$')
    @classmethod
    async def add_many(cls, conn, guilds: t.Tuple[hikari.Guild]):
        query = insert_into_query("Guilds", 4)

        args = []
        for guild in guilds:
            args.append((guild.id, guild.name, True, '$'))
        
        await conn.executemany(query, args)
    @classmethod
    async def remove(cls, conn, id: int):
        query = '''
            DELETE FROM Guilds
            WHERE id = ($1);
        '''

        await conn.execute(query, id)
    @classmethod
    async def update_column(cls, conn, id: int, column: str, new_value):
        query = f'''
            UPDATE Guilds
            SET {column} = ($1)
            WHERE id = ($2);
        '''

        await conn.execute(query, new_value, id)
    
class GuildsLogs:
    '''Functions to interact with the `GuildsLogs` table.'''
    @classmethod
    async def get_all(cls, conn):
        return await cls.get_all_where(conn)
    @classmethod
    async def get_all_where(cls, conn, *, where: t.Callable[[dict], bool] = lambda r: True):
        query = '''
            SELECT * FROM GuildsLogs;
        '''

        return await __get_all__(conn, query, where = where)
    @classmethod
    async def get_one(cls, conn, id: int):
        query = '''
            SELECT * FROM GuildsLogs
            WHERE guild_id = ($1);
        '''

        return await __get_one__(conn, query, id)
    
    # Only 2 columns are required, rest are defaults.
    @classmethod
    async def add_many(cls, conn, guilds: t.Tuple[hikari.Guild]):
        query = '''
            INSERT INTO GuildsLogs
            VALUES ($1) ON CONFLICT DO NOTHING;
        '''

        args = []
        for guild in guilds:
            args.append((guild.id))

        await conn.executemany(query, args)
    @classmethod
    async def add_one(cls, conn, guild: hikari.Guild):
        query = '''
            INSERT INTO GuildsLogs
            VALUES ($1) ON CONFLICT DO NOTHING;
        '''

        await conn.execute(query, (guild.id))
    @classmethod
    async def update_column(cls, conn, id: int, column: str, new_value):
        query = f'''
            UPDATE GuildsLogs
            SET {column} = ($1)
            WHERE guild_id = ($2);
        '''

        await conn.execute(query, new_value, id)

class Users:
    '''Functions to interact with the `Users` table.'''
    @classmethod
    async def get_all(cls, conn):
        return await cls.get_all_where(conn)
    @classmethod
    async def get_all_where(cls, conn, *, where: t.Callable[[dict], bool] = lambda r: True):
        query = '''
            SELECT * FROM Users
            ORDER BY Users.name;
        '''

        return await __get_all__(conn, query, where = where)
    @classmethod
    async def get_one(cls, conn, id: int):
        query = '''
            SELECT * FROM Users
            WHERE id = ($1);
        '''

        return await __get_one__(conn, query, id)
    @classmethod
    async def add_one(cls, conn, user_id: int, user_name: str):
        query = insert_into_query("Users", 3)

        await conn.execute(query, user_id, user_name, True)
    @classmethod
    async def add_many(cls, conn, users: list[hikari.User]):
        query = insert_into_query("Users", 3)

        args = []
        for user in users:
            args.append((user.id, user.username, True))
        
        await conn.executemany(query, args)
    @classmethod
    async def remove(cls, conn, id: int):
        query = '''
            DELETE FROM Users
            WHERE id = ($1);
        '''

        await conn.execute(query, id)
    @classmethod
    async def update_column(cls, conn, id: int, column: str, new_value):
        query = f'''
            UPDATE Users
            SET {column} = ($1)
            WHERE id = ($2);
        '''

        await conn.execute(query, new_value, id)

class Reminders:
    '''Functions to interact with the `Reminders` table.'''
    @classmethod
    async def get_user_reminders(cls, conn, user_id: int) -> list[dict]:
        query = '''
            SELECT * FROM Reminders
            WHERE user_id = ($1);
        '''

        result = await conn.fetch(query, user_id)
        return [record_to_dict(record) for record in result]
    @classmethod
    async def get_reminders(cls, conn, lower_time: dt.datetime, upper_time: dt.datetime) -> list[dict]:
        query = '''
            SELECT * FROM Reminders
            WHERE awake_time > ($1) AND awake_time <= ($2);
        '''

        result = await conn.fetch(query, lower_time, upper_time)
        return [record_to_dict(record) for record in result]
    @classmethod
    async def get_past_reminders(cls, conn, now: dt.datetime) -> list[dict]:
        query = '''
            SELECT * FROM Reminders
            WHERE awake_time < ($1);
        '''

        result = await conn.fetch(query, now)
        return [record_to_dict(record) for record in result]
    @classmethod
    async def add_reminder(cls, conn, user_id: int, when: dt.datetime, message: str):
        query = '''
            INSERT INTO Reminders (user_id, awake_time, message)
                VALUES ($1, $2, $3);
        '''
        
        await conn.execute(query, user_id, when, message)
    @classmethod
    async def remove_reminder(cls, conn, remind_id: int, user_id: int):
        # Although remind_id is sufficient, user_id is to make sure a user can't remove another reminder.
        query = '''
            DELETE FROM Reminders
            WHERE remind_id = ($1) AND user_id = ($2);
        '''

        await conn.execute(query, remind_id, user_id)
