# The code uses a lot of `id`, which turns out to be shadowing the builtin `id()`.
#pylint: disable=redefined-builtin

'''Contains many functions that hide all "naked" SQL to use.'''

# NOTE: Docstring will be ''' while query/multiline string will be """ for the autoDocstring extension to work.
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
    '''Return the query to insert into a table that has `len_col` columns.

    Parameters
    ----------
    table_name : str
        The table to insert.
    len_col : int
        How many column does the table have.

    Returns
    -------
    str
        An INSERT SQL statement with query formatter ready to use in `.execute()`
    '''
    arg_str = "("
    for index in range(len_col):
        arg_str += f"${index + 1}, "
    arg_str = arg_str[:-2] + ')'

    return f"INSERT INTO {table_name} VALUES {arg_str} ON CONFLICT DO NOTHING;"

async def __get_all__(conn: asyncpg.Connection, query: str, *, where: t.Callable[[dict], bool] = lambda r: True) -> list[dict]:
    '''Run a `SELECT` statement and return a list of objects.

    This should NOT be used outside of the module. Instead, use `table_name.get_all()`.

    Parameters
    ----------
    conn : asyncpg.Connection
        The connection to use.
    query : str 
        The `SELECT` statement to run. This should not contain `WHERE` clause.
        Conditions should be set in `where` parameter.
    where : t.Callable[[dict], bool]
        Additional conditions to filter. By default, no condition is applied (always return `True`).

    Returns
    -------
    list[dict]
        A list of `dict` or empty list.
    '''

    result = await conn.fetch(query)
    l = []
    record_obj = None
    for record in result:
        record_obj = record_to_dict(record)
        if record_obj is None or (record_obj is not None and where(record_obj)):
            l.append(record_obj)
    
    return l

async def __get_one__(conn: asyncpg.Connection, query: str, *constraints) -> t.Optional[dict]:
    '''Run a `SELECT` statement and return the first object that matches the constraints.

    Parameters
    ----------
    conn : asyncpg.Connection
        The connection to use.
    query : str 
        The `SELECT` statement to run. This should contain a `WHERE` clause.
    constraints : str
        Arguments to be formatted into the query.

    Returns
    -------
    t.Optional[dict]
        A `dict` or `None` if no object is found.
    '''
    
    record = await conn.fetchrow(query, *constraints)
    return record_to_dict(record)

async def run_and_return_count(conn: asyncpg.Connection, query: str, *args, **kwargs) -> t.Optional[int]:
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
    status = await conn.execute(query, *args, **kwargs)
    
    # INSERT returns "INSERT oid count".
    try:
        count = int(status.split()[-1])
        return count
    except ValueError:
        return None
    
class Guilds:
    '''Functions to interact with the `Guilds` table.'''
    @staticmethod
    async def get_all(conn):
        '''Get all entries in the table.'''
        
        return await Guilds.get_all_where(conn)
    @staticmethod
    async def get_all_where(conn, *, where: t.Callable[[dict], bool] = lambda r: True):
        '''Get all entires in the table that matches the condition.'''
        
        query = """
            SELECT * FROM Guilds
            ORDER BY Guilds.name;
        """
        return await __get_all__(conn, query, where = where)
    @staticmethod
    async def get_one(conn, id: int):
        '''Get the first entry in the table that matches the condition.'''
        
        query = """
            SELECT * FROM Guilds
            WHERE id = ($1);
        """
        return await __get_one__(conn, query, id)
    
    @staticmethod
    async def insert_one(conn, guild: hikari.Guild) -> int:
        '''Insert an entry into the table.'''
        
        query = insert_into_query("Guilds", 4)
        #await conn.execute(query, guild.id, guild.name, True, '$')
        return await run_and_return_count(conn, query, guild.id, guild.name, True, '$')
    @classmethod
    async def _add_many(cls, conn, guilds: t.Tuple[hikari.Guild]):
        query = insert_into_query("Guilds", 4)

        args = []
        for guild in guilds:
            args.append((guild.id, guild.name, True, '$'))
        
        await conn.executemany(query, args)
    @staticmethod
    async def delete(conn, id: int) -> int:
        '''Delete an entry in the table based on the provided key.'''
        
        query = """
            DELETE FROM Guilds
            WHERE id = ($1);
        """
        #await conn.execute(query, id)
        return await run_and_return_count(conn, query, id)
    @staticmethod
    async def update_column(conn, id: int, column: str, new_value) -> int:
        '''Update a specific column with a new value.

        Notes
        -----
        Always prefer using other functions to update rather than this function if possible.
        '''

        query = f"""
            UPDATE Guilds
            SET {column} = ($1)
            WHERE id = ($2);
        """
        #await conn.execute(query, new_value, id)
        return await run_and_return_count(conn, query, new_value, id)
    
class GuildsLogs:
    '''Functions to interact with the `GuildsLogs` table.'''
    @staticmethod
    async def get_all(conn):
        '''Get all entries in the table.'''
        
        return await GuildsLogs.get_all_where(conn)
    @staticmethod
    async def get_all_where(conn, *, where: t.Callable[[dict], bool] = lambda r: True):
        '''Get all entires in the table that matches the condition.'''
        
        query = """
            SELECT * FROM GuildsLogs;
        """
        return await __get_all__(conn, query, where = where)
    @staticmethod
    async def get_one(conn, id: int):
        '''Get the first entry in the table that matches the condition.'''
        
        query = """
            SELECT * FROM GuildsLogs
            WHERE guild_id = ($1);
        """
        return await __get_one__(conn, query, id)
    
    # Only 2 columns are required, rest are defaults.
    @classmethod
    async def _add_many(cls, conn, guilds: t.Tuple[hikari.Guild]):
        query = '''
            INSERT INTO GuildsLogs
            VALUES ($1) ON CONFLICT DO NOTHING;
        '''

        args = []
        for guild in guilds:
            args.append((guild.id))

        await conn.executemany(query, args)
    @staticmethod
    async def insert_one(conn, guild: hikari.Guild) -> int:
        '''Insert an entry into the table.'''

        query = """
            INSERT INTO GuildsLogs
            VALUES ($1) ON CONFLICT DO NOTHING;
        """
        #await conn.execute(query, (guild.id))
        return await run_and_return_count(conn, query, guild.id)
    @staticmethod
    async def delete(conn, id: int) -> int:
        '''Delete an entry in the table based on the provided key.'''

        query = """
            DELETE FROM GuildsLogs
            WHERE guild_id = ($1);
        """
        #await conn.execute(query, id)
        return await run_and_return_count(conn, query, id)
    @staticmethod
    async def update_column(conn, id: int, column: str, new_value) -> int:
        '''Update a specific column with a new value.

        Notes
        -----
        Always prefer using other functions to update rather than this function if possible.
        '''

        query = f"""
            UPDATE GuildsLogs
            SET {column} = ($1)
            WHERE guild_id = ($2);
        """
        #await conn.execute(query, new_value, id)
        return await run_and_return_count(conn, query, new_value, id)

class Users:
    '''Functions to interact with the `Users` table.'''
    @staticmethod
    async def get_all(conn):
        '''Get all entries in the table.'''
        
        return await Users.get_all_where(conn)
    @staticmethod
    async def get_all_where(conn, *, where: t.Callable[[dict], bool] = lambda r: True):
        '''Get all entires in the table that matches the condition.'''

        query = """
            SELECT * FROM Users
            ORDER BY Users.name;
        """
        return await __get_all__(conn, query, where = where)
    @staticmethod
    async def get_one(conn, id: int):
        '''Get the first entry in the table that matches the condition.'''

        query = """
            SELECT * FROM Users
            WHERE id = ($1);
        """
        return await __get_one__(conn, query, id)
    @staticmethod
    async def insert_one(conn, user_id: int, user_name: str) -> int:
        '''Insert an entry into the table.'''

        query = insert_into_query("Users", 3)
        #await conn.execute(query, user_id, user_name, True)
        return await run_and_return_count(conn, query, user_id, user_name, True)
    @classmethod
    async def _add_many(cls, conn, users: list[hikari.User]):
        query = insert_into_query("Users", 3)

        args = []
        for user in users:
            args.append((user.id, user.username, True))
        
        await conn.executemany(query, args)
    @staticmethod
    async def delete(conn, id: int) -> int:
        '''Delete an entry in the table based on the provided key.'''

        query = """
            DELETE FROM Users
            WHERE id = ($1);
        """
        #await conn.execute(query, id)
        return await run_and_return_count(conn, query, id)
    @staticmethod
    async def update_column(conn, id: int, column: str, new_value) -> int:
        '''Update a specific column with a new value.

        Notes
        -----
        Always prefer using other functions to update rather than this function if possible.
        '''

        query = f"""
            UPDATE Users
            SET {column} = ($1)
            WHERE id = ($2);
        """
        #await conn.execute(query, new_value, id)
        return await run_and_return_count(conn, query, new_value, id)

class Reminders:
    '''Functions to interact with the `Reminders` table.'''
    @staticmethod
    async def get_user_reminders(conn, user_id: int) -> list[t.Optional[dict]]:
        '''Get a list of reminders a user have.'''
        
        query = """
            SELECT * FROM Reminders
            WHERE user_id = ($1);
        """

        result = await conn.fetch(query, user_id)
        return [record_to_dict(record) for record in result]
    @staticmethod
    async def get_reminders(conn, lower_time: dt.datetime, upper_time: dt.datetime) -> list[t.Optional[dict]]:
        '''Get a list of reminders within the time range.'''

        query = """
            SELECT * FROM Reminders
            WHERE awake_time > ($1) AND awake_time <= ($2);
        """

        result = await conn.fetch(query, lower_time, upper_time)
        return [record_to_dict(record) for record in result]
    @staticmethod
    async def get_past_reminders(conn, now: dt.datetime) -> list[t.Optional[dict]]:
        '''Get a list of reminders that are supposed to be cleared before the time provided.'''
        
        query = """
            SELECT * FROM Reminders
            WHERE awake_time < ($1);
        """

        result = await conn.fetch(query, now)
        return [record_to_dict(record) for record in result]
    @staticmethod
    async def insert_reminder(conn, user_id: int, when: dt.datetime, message: str) -> int:
        '''Insert a reminder entry.'''
        
        query = """
            INSERT INTO Reminders (user_id, awake_time, message)
                VALUES ($1, $2, $3);
        """
        #await conn.execute(query, user_id, when, message)
        return await run_and_return_count(conn, query, user_id, when, message)
    @staticmethod
    async def delete_reminder(conn, remind_id: int, user_id: int) -> int:
        '''Delete a reminder entry.'''

        # Although remind_id is sufficient, user_id is to make sure a user can't remove another reminder.
        query = """
            DELETE FROM Reminders
            WHERE remind_id = ($1) AND user_id = ($2);
        """
        #await conn.execute(query, remind_id, user_id)
        return await run_and_return_count(conn, query, remind_id, user_id)

class Lockdown:
    '''Functions to interact with the `Lockdown` table.'''
    @staticmethod
    async def get_all(conn: asyncpg.Connection):
        return await Lockdown.get_all_where(conn)

    @staticmethod
    async def get_all_where(conn: asyncpg.Connection, *, where: t.Callable[[dict], bool] = lambda r: True):
        query = '''
            SELECT * FROM Lockdown;
        '''

        return await __get_all__(conn, query, where = where)
    
    @staticmethod
    async def get_one(conn: asyncpg.Connection, guild_id: int):
        query = '''
            SELECT * FROM Lockdown
            WHERE guild_id = ($1);
        '''

        return await __get_one__(conn, query, guild_id)
    
    @staticmethod
    async def insert_one(conn: asyncpg.Connection, guild_id: int, channels: list[int] = None):
        if channels is None:
            channels = []
        
        query = insert_into_query("Lockdown", 2)

        #await conn.execute(query, guild_id, channels)
        return await run_and_return_count(conn, query, guild_id, channels)
    
    @staticmethod
    async def delete(conn: asyncpg.Connection, guild_id: int) -> int:
        '''Delete an entry from the table.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        guild_id : int
            The pkey to the entry.
        
        Returns
        -------
        int
            The number of entries deleted.
        '''

        query = """
            DELETE FROM Lockdown
            WHERE guild_id = ($1);
        """

        #status = await conn.execute(query, guild_id)
        #return status.split()[1]
        return await run_and_return_count(conn, query, guild_id)
    
    @staticmethod
    async def update_column(conn: asyncpg.Connection, guild_id: int, column: str, new_value) -> int:
        '''Update a column with a new value.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        guild_id : int
            The entry pkey to update.
        column : str
            The column's name.
        new_value : _type_
            The new value to update.

        Returns
        -------
        int
            The number of entries updated.
        '''

        query = f"""
            UPDATE Lockdown
            SET {column} = ($1)
            WHERE guild_id = ($2);
        """

        return await run_and_return_count(conn, query, new_value, guild_id)

    @staticmethod
    async def add_channel(conn: asyncpg.Connection, guild_id: int, channel_id: int) -> int:
        '''Append a channel to the guild provided.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        guild_id : int
            The guild id to add.
        channel_id : int
            The channel id to add.

        Returns
        -------
        int
            The number of entries added. Should be 1 or 0.

        Raises
        ------
        GetError
            The entry `guild_id` doesn't exist in the table.
        '''

        # There's probably a postgres way to append the element directly but I'm not gonna risk it.
        existed = await Lockdown.get_one(conn, guild_id)
        if not existed:
            raise GetError(f"Entry {guild_id} is not found in table 'Lockdown'.")
        if channel_id in existed["channels"]:
            return 0
        
        existed["channels"].append(channel_id)
        return await Lockdown.update_column(conn, guild_id, "channels", existed["channels"])
    @staticmethod
    async def remove_channel(conn: asyncpg.Connection, guild_id: int, channel_id: int) -> int:
        '''Remove a channel from the guild provided.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        guild_id : int
            The guild id to remove.
        channel_id : int
            The channel id to remove.

        Returns
        -------
        int
            The number of entries removed. Should be 1 or 0.

        Raises
        ------
        GetError
            The entry `guild_id` doesn't exist in the table.
        '''
        
        existed = await Lockdown.get_one(conn, guild_id)
        if not existed:
            raise GetError(f"Entry {guild_id} is not found in table 'Lockdown'.")
        if channel_id not in existed["channels"]:
            return 0
        
        existed["channels"].remove(channel_id)
        return await Lockdown.update_column(conn, guild_id, "channels", existed["channels"])
