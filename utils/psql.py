# The code uses a lot of `id`, which turns out to be shadowing the builtin `id()`.
#pylint: disable=redefined-builtin

'''Contains many functions that hide all "naked" SQL to use.'''

from __future__ import annotations

# NOTE: Docstring will be ''' while query/multiline string will be """ for the autoDocstring extension to work.
import dataclasses
import datetime as dt
import logging
import random
import typing as t

import asyncpg
import hikari

from utils.helpers import ClassToDict

logger = logging.getLogger("MichaelBot")
T = t.TypeVar('T')

# TODO: Add constraint checking when updating values.

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
    '''Raised when trying to add an element that's already available in a unique-only list (set).'''

def record_to_type(record: asyncpg.Record, /, result_type: t.Type[T] = dict) -> T:
    '''Convert a `asyncpg.Record` into a `dict` or `None` if the object is already `None`.

    This is for convenience purpose, where `dict(Record)` will return `{}` which is not an accurate
    representation of empty. `obj is None` or `obj is not None` is more obvious to anyone than
    `bool(obj)` or `not bool(obj)`.

    Parameters
    ----------
    record : asyncpg.Record
        The record to convert.
    result_type : t.Type
        The type to convert to. The type must be a dataclass or an object that can be initialized via kwargs or a `dict`. Default to `dict`.

    Return
    ------
    t.Optional[T]
        Either `None` or `result_type`.
    '''
    
    if record is None: 
        return None
    
    d = dict(record)
    if result_type is dict:
        return d
    
    return result_type(**d)

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

    return f"INSERT INTO {table_name} VALUES {arg_str};"

async def __get_all__(conn: asyncpg.Connection, query: str, *, where: t.Callable[[T], bool] = lambda r: True, result_type: t.Type[T] = dict) -> list[T]:
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
    result_type : t.Type[T]
        The type to convert to. The type must be a dataclass or an object that can be initialized via kwargs or a `dict`. Default to `dict`.

    Returns
    -------
    list[T]
        A list of `result_type` or empty list.
    '''

    result = await conn.fetch(query)
    l = []
    record_obj = None
    for record in result:
        # NOTE: This code is for handling dict case; will remove soon.
        #record_obj = record_to_type(record)
        #if record_obj is None or (record_obj is not None and where(record_obj)):
        #    l.append(record_obj)
        record_obj = record_to_type(record, result_type)
        if record_obj is None or (record_obj is not None and where(record_obj)):
            l.append(record_obj)
    
    return l

async def __get_one__(conn: asyncpg.Connection, query: str, *constraints, result_type: t.Type[T] = dict) -> t.Optional[T]:
    '''Run a `SELECT` statement and return the first object that matches the constraints.

    Parameters
    ----------
    conn : asyncpg.Connection
        The connection to use.
    query : str 
        The `SELECT` statement to run. This should contain a `WHERE` clause.
    *constraints : str
        Arguments to be formatted into the query.
    result_type : t.Type[T]
        The type to convert to. The type must be a dataclass or an object that can be initialized via kwargs or a `dict`. Default to `dict`.

    Returns
    -------
    t.Optional[T]
        A `result_type` or `None` if no object is found.
    '''
    
    record = await conn.fetchrow(query, *constraints)
    return record_to_type(record, result_type)

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

@dataclasses.dataclass(slots = True)
class Guild(ClassToDict):
    '''Represent an entry in the `Guilds` table along with possible operations related to the table.

    It is advised to use the cache in the bot instead. These methods are for mostly cache construction.
    '''

    id: int
    name: str
    is_whitelist: bool = True
    prefix: str = '$'
    
    __PREVENT_UPDATE = ("id")
    
    @staticmethod
    async def get_all(conn: asyncpg.Connection, *, as_dict: bool = False) -> list[t.Union[Guild, dict]]:
        '''Get all entries in the table.'''
        
        return await Guild.get_all_where(conn, as_dict = as_dict)
    @staticmethod
    async def get_all_where(conn: asyncpg.Connection, *, where: t.Callable[[dict], bool] = lambda r: True, as_dict: bool = False) -> list[t.Union[Guild, dict]]:
        '''Get all entires in the table that matches the condition.'''
        
        query = """
            SELECT * FROM Guilds
            ORDER BY Guilds.name;
        """
        return await __get_all__(conn, query, where = where, result_type = Guild if not as_dict else dict)
    @staticmethod
    async def get_one(conn: asyncpg.Connection, id: int, *, as_dict: bool = False) -> t.Union[Guild, dict]:
        '''Get the first entry in the table that matches the pkey provided.'''
        
        query = """
            SELECT * FROM Guilds
            WHERE id = ($1);
        """
        return await __get_one__(conn, query, id, result_type = Guild if not as_dict else dict)
    @staticmethod
    async def insert_one(conn: asyncpg.Connection, guild: Guild) -> int:
        '''Insert an entry into the table.'''

        query = insert_into_query("Guilds", len(guild.__slots__))
        return await run_and_return_count(conn, query, guild.id, guild.name, guild.is_whitelist, guild.prefix)
    @staticmethod
    async def delete(conn: asyncpg.Connection, id: int) -> int:
        '''Delete an entry in the table based on the provided key.'''
        
        query = """
            DELETE FROM Guilds
            WHERE id = ($1);
        """
        return await run_and_return_count(conn, query, id)
    @staticmethod
    async def update_column(conn: asyncpg.Connection, id: int, column: str, new_value) -> int:
        '''Update a specific column with a new value.

        Warnings
        --------
        Columns that are in `__PREVENT_UPDATE` (usually primary keys) will be ignored. To update such columns, use raw SQL.

        Notes
        -----
        Always prefer using other functions to update rather than this function if possible.
        '''

        if column in Guild.__PREVENT_UPDATE:
            return 0
        
        query = f"""
            UPDATE Guilds
            SET {column} = ($1)
            WHERE id = ($2);
        """
        return await run_and_return_count(conn, query, new_value, id)
    @staticmethod
    async def update(conn: asyncpg.Connection, guild: Guild) -> int:
        '''Update an entry based on the provided object, or insert it if not existed.

        This function calls `get_one()` internally, causing an overhead.

        Notes
        -----
        This function has its own transaction.
        '''
        
        existed_guild = await Guild.get_one(conn, guild.id)
        if not existed_guild:
            return await Guild.insert_one(conn, guild)

        diff_col = []
        for col in existed_guild.__slots__:
            if getattr(existed_guild, col) != getattr(guild, col):
                diff_col.append(col)
        
        async with conn.transaction():
            for change in diff_col:
                await Guild.update_column(conn, guild.id, change, getattr(guild, change))

@dataclasses.dataclass(slots = True)    
class GuildLog(ClassToDict):
    '''Represent an entry in the `GuildsLogs` table along with possible operations related to the table.

    It is advised to use the cache in the bot instead. These methods are for mostly cache construction.
    '''

    guild_id: int
    log_channel: int = None
    guild_channel_create: bool = True
    guild_channel_delete: bool = True
    guild_channel_update: bool = True
    guild_ban: bool = True
    guild_unban: bool = True
    guild_update: bool = True
    member_join: bool = True
    member_leave: bool = True
    member_update: bool = True
    guild_bulk_message_delete: bool = True
    guild_message_delete: bool = True
    guild_message_update: bool = True
    role_create: bool = True
    role_delete: bool = True
    role_update: bool = True
    command_complete: bool = True
    command_error: bool = True

    __PREVENT_UPDATE = ("guild_id")

    @staticmethod
    async def get_all(conn: asyncpg.Connection, *, as_dict: bool = False) -> list[t.Union[GuildLog, dict]]:
        '''Get all entries in the table.'''
        
        return await GuildLog.get_all_where(conn, as_dict = as_dict)
    @staticmethod
    async def get_all_where(conn: asyncpg.Connection, *, where: t.Callable[[dict], bool] = lambda r: True, as_dict: bool = False) -> list[t.Union[GuildLog, dict]]:
        '''Get all entires in the table that matches the condition.'''
        
        query = """
            SELECT * FROM GuildsLogs;
        """
        return await __get_all__(conn, query, where = where, result_type = GuildLog if not as_dict else dict)
    @staticmethod
    async def get_one(conn: asyncpg.Connection, id: int, *, as_dict: bool = False) -> t.Union[GuildLog, dict]:
        '''Get the first entry in the table that matches the pkey provided.'''
        
        query = """
            SELECT * FROM GuildsLogs
            WHERE guild_id = ($1);
        """
        return await __get_one__(conn, query, id, result_type = GuildLog if not as_dict else dict)
    @staticmethod
    async def insert_one(conn: asyncpg.Connection, guild_id: int) -> int:
        '''Insert an entry into the table.'''

        # Only guild_id is required.
        query = insert_into_query("GuildsLogs", 1)
        return await run_and_return_count(conn, query, guild_id)
    @staticmethod
    async def delete(conn: asyncpg.Connection, id: int) -> int:
        '''Delete an entry in the table based on the provided key.'''

        query = """
            DELETE FROM GuildsLogs
            WHERE guild_id = ($1);
        """
        return await run_and_return_count(conn, query, id)
    @staticmethod
    async def update_column(conn: asyncpg.Connection, id: int, column: str, new_value) -> int:
        '''Update a specific column with a new value.

        Warnings
        --------
        Columns that are in `__PREVENT_UPDATE` (usually primary keys) will be ignored. To update such columns, use raw SQL.

        Notes
        -----
        Always prefer using other functions to update rather than this function if possible.
        '''

        if column in GuildLog.__PREVENT_UPDATE:
            return 0
        
        query = f"""
            UPDATE GuildsLogs
            SET {column} = ($1)
            WHERE guild_id = ($2);
        """
        return await run_and_return_count(conn, query, new_value, id)
    @staticmethod
    async def update(conn: asyncpg.Connection, guild: GuildLog) -> int:
        '''Update an entry based on the provided object, or insert it if not existed.

        This function calls `get_one()` internally, causing an overhead.

        Notes
        -----
        This function has its own transaction.
        '''

        existed_guild = await GuildLog.get_one(conn, guild.guild_id)
        if not existed_guild:
            return await GuildLog.insert_one(conn, guild.guild_id)

        diff_col = []
        for col in existed_guild.__slots__:
            if getattr(existed_guild, col) != getattr(guild, col):
                diff_col.append(col)
        
        async with conn.transaction():
            for change in diff_col:
                await GuildLog.update_column(conn, guild.guild_id, change, getattr(guild, change))

@dataclasses.dataclass(slots = True)
class User(ClassToDict):
    '''Represent an entry in the `Users` table along with possible operations related to the table.

    It is advised to use the cache in the bot instead. These methods are for mostly cache construction.
    '''

    id: int
    name: str
    is_whitelist: bool = True
    balance: int = 0
    world: str = "overworld"
    last_travel: dt.datetime = None
    daily_streak: int = 0
    last_daily: dt.datetime = None
    
    __WORLD_TYPE = ("overworld", "nether", "end")
    __PREVENT_UPDATE = ("id")

    @staticmethod
    async def get_all(conn: asyncpg.Connection, *, as_dict: bool = False) -> list[User]:
        '''Get all entries in the table.'''
        
        return await User.get_all_where(conn, as_dict = as_dict)
    @staticmethod
    async def get_all_where(conn: asyncpg.Connection, *, where: t.Callable[[dict], bool] = lambda r: True, as_dict: bool = False) -> list[t.Union[User, dict]]:
        '''Get all entires in the table that matches the condition.'''

        query = """
            SELECT * FROM Users
            ORDER BY Users.name;
        """
        return await __get_all__(conn, query, where = where, result_type = User if not as_dict else dict)
    @staticmethod
    async def get_one(conn: asyncpg.Connection, id: int, as_dict: bool = False) -> t.Union[User, dict]:
        '''Get the first entry in the table that matches the pkey provided.'''

        query = """
            SELECT * FROM Users
            WHERE id = ($1);
        """
        return await __get_one__(conn, query, id, result_type = User if not as_dict else dict)
    @staticmethod
    async def insert_one(conn: asyncpg.Connection, user: User) -> int:
        '''Insert an entry into the table.'''

        query = insert_into_query("Users", len(user.__slots__))
        return await run_and_return_count(conn, query, 
            user.id, 
            user.name, 
            user.is_whitelist, 
            user.balance, 
            user.world, 
            user.last_travel,
            user.daily_streak, 
            user.last_daily
        )
    @staticmethod
    async def delete(conn: asyncpg.Connection, id: int) -> int:
        '''Delete an entry in the table based on the provided key.'''

        query = """
            DELETE FROM Users
            WHERE id = ($1);
        """
        return await run_and_return_count(conn, query, id)
    @staticmethod
    async def update_column(conn: asyncpg.Connection, id: int, column: str, new_value) -> int:
        '''Update a specific column with a new value.

        Warnings
        --------
        Columns that are in `__PREVENT_UPDATE` (usually primary keys) will be ignored. To update such columns, use raw SQL.

        Notes
        -----
        Always prefer using other functions to update rather than this function if possible.
        '''

        if column in User.__PREVENT_UPDATE:
            return 0

        query = f"""
            UPDATE Users
            SET {column} = ($1)
            WHERE id = ($2);
        """
        return await run_and_return_count(conn, query, new_value, id)
    @staticmethod
    async def update_balance(conn: asyncpg.Connection, id: int, new_balance: int) -> int:
        if new_balance < 0:
            # Might raise a warning here?
            return 0
        
        return await User.update_column(conn, id, "balance", new_balance)
    @staticmethod
    async def update_streak(conn: asyncpg.Connection, id: int, new_streak: int) -> int:
        if new_streak < 0:
            # Might raise a warning here?
            return 0
        
        return await User.update_column(conn, id, "daily_streak", new_streak)
    @staticmethod
    async def add_money(conn: asyncpg.Connection, id: int, amount: int) -> int:
        if amount <= 0:
            return 0
        
        existed = await User.get_one(conn, id)
        if not existed:
            raise UpdateError(f"Trying to update entry '{id}', but it is not found.")
        
        return await User.update_balance(conn, id, existed.balance + amount)
    @staticmethod
    async def remove_money(conn: asyncpg.Connection, id: int, amount: int) -> int:
        if amount <= 0:
            return 0
        
        existed = await User.get_one(conn, id)
        if not existed:
            raise UpdateError(f"Trying to update entry '{id}', but it is not found.")
        
        if existed.balance <= amount:
            # Might raise a warning here? Idk.
            existed.balance = 0
        else:
            existed.balance -= amount
        
        return await User.update_balance(conn, id, existed.balance)
    @staticmethod
    async def update(conn: asyncpg.Connection, user: User) -> int:
        '''Update an entry based on the provided object, or insert it if not existed.

        This function calls `get_one()` internally, causing an overhead.

        Notes
        -----
        This function has its own transaction.
        '''

        existed_user = await User.get_one(conn, user.id)
        if not existed_user:
            return await User.insert_one(conn, user)

        diff_col = []
        for col in existed_user.__slots__:
            if getattr(existed_user, col) != getattr(user, col):
                diff_col.append(col)
        
        async with conn.transaction():
            for change in diff_col:
                await User.update_column(conn, user.id, change, getattr(user, change))

@dataclasses.dataclass(slots = True)
class Reminders(ClassToDict):
    '''Represent an entry in the `Reminders` table along with possible operations related to the table.'''

    remind_id: int
    user_id: int
    awake_time: dt.datetime
    message: str

    __PREVENT_UPDATE = ("remind_id", "user_id")

    @staticmethod
    async def get_user_reminders(conn: asyncpg.Connection, user_id: int, *, as_dict: bool = False) -> list[t.Optional[t.Union[Reminders, dict]]]:
        '''Get a list of reminders a user have.'''
        
        query = """
            SELECT * FROM Reminders
            WHERE user_id = ($1);
        """

        result = await conn.fetch(query, user_id)
        return [record_to_type(record, result_type = Reminders if not as_dict else dict) for record in result]
    @staticmethod
    async def get_reminders(conn: asyncpg.Connection, lower_time: dt.datetime, upper_time: dt.datetime, *, as_dict: bool = False) -> list[t.Optional[t.Union[Reminders, dict]]]:
        '''Get a list of reminders within `(lower_time, upper_time]`.'''

        query = """
            SELECT * FROM Reminders
            WHERE awake_time > ($1) AND awake_time <= ($2);
        """

        result = await conn.fetch(query, lower_time, upper_time)
        return [record_to_type(record, result_type = Reminders if not as_dict else dict) for record in result]
    @staticmethod
    async def get_past_reminders(conn: asyncpg.Connection, now: dt.datetime, *, as_dict: bool = False) -> list[t.Optional[t.Union[Reminders, dict]]]:
        '''Get a list of reminders that are supposed to be cleared before the time provided.'''
        
        query = """
            SELECT * FROM Reminders
            WHERE awake_time < ($1);
        """

        result = await conn.fetch(query, now)
        return [record_to_type(record, result_type = Reminders if not as_dict else dict) for record in result]
    @staticmethod
    async def insert_reminder(conn: asyncpg.Connection, user_id: int, when: dt.datetime, message: str) -> int:
        '''Insert a reminder entry.'''
        
        query = """
            INSERT INTO Reminders (user_id, awake_time, message)
                VALUES ($1, $2, $3);
        """
        return await run_and_return_count(conn, query, user_id, when, message)
    @staticmethod
    async def delete_reminder(conn: asyncpg.Connection, remind_id: int, user_id: int) -> int:
        '''Delete a reminder entry.'''

        # Although remind_id is sufficient, user_id is to make sure a user can't remove another reminder.
        query = """
            DELETE FROM Reminders
            WHERE remind_id = ($1) AND user_id = ($2);
        """
        return await run_and_return_count(conn, query, remind_id, user_id)

@dataclasses.dataclass(slots = True)
class Item(ClassToDict):
    '''Represent an entry in the `Items` table along with possible operations related to the table.

    This is mostly used for the bot's cache purpose. If you're using this directly in a code, you're probably doing it wrong.
    '''
    
    id: str
    sort_id: int
    name: str
    emoji: str
    description: str
    rarity: str
    sell_price: int
    buy_price: t.Optional[int] = None
    aliases: list[str] = dataclasses.field(default_factory = list)
    durability: int = None

    __PREVENT_UPDATE = ("id")

    @staticmethod
    async def get_all(conn: asyncpg.Connection, *, as_dict: bool = False) -> list[t.Union[Item, dict]]:
        '''Get all entries in the table.'''

        return await Item.get_all_where(conn, as_dict = as_dict)
    @staticmethod
    async def get_all_where(conn: asyncpg.Connection, *, where: t.Callable[[Item], bool] = lambda r: True, as_dict: bool = False) -> list[t.Union[Item, dict]]:
        '''Get all entires in the table that matches the condition.'''

        query = """
            SELECT * FROM Items
            ORDER by sort_id;
        """
        return await __get_all__(conn, query, where = where, result_type = Item if not as_dict else dict)
    @staticmethod
    async def get_one(conn: asyncpg.Connection, id: str, *, as_dict: bool = False) -> t.Union[Item, dict]:
        '''Get the first entry in the table that matches the condition.'''

        query = """
            SELECT * FROM Items
            WHERE id = ($1);
        """
        return await __get_one__(conn, query, id, result_type = Item if not as_dict else dict)
    @staticmethod
    async def get_by_name(conn: asyncpg.Connection, name_or_alias: str, *, as_dict: bool = False) -> t.Union[Item, dict]:
        '''Get the first item that has its name/aliases match the provided.'''

        def filter_name_alias(record: Item):
            return record.name.lower() == name_or_alias.lower() or name_or_alias.lower() in [alias.lower() for alias in record.aliases]
        
        res = await Item.get_all_where(conn, where = filter_name_alias, as_dict = as_dict)
        
        assert len(res) <= 1
        if res:
            return res[0]
        return None
    @staticmethod
    async def insert_one(conn: asyncpg.Connection, item: Item):
        '''Insert an entry into the table.'''

        query = insert_into_query("Items", len(item.__slots__))
        return await run_and_return_count(conn, query, 
            item.id, 
            item.sort_id, 
            item.name, 
            item.aliases, 
            item.emoji, 
            item.description, 
            item.rarity,
            item.buy_price,
            item.sell_price,
            item.durability,
        )
    @staticmethod
    async def update_column(conn: asyncpg.Connection, id: str, column: str, new_value) -> int:
        '''Update a specific column with a new value.

        Warnings
        --------
        Columns that are in `__PREVENT_UPDATE` (usually primary keys) will be ignored. To update such columns, use raw SQL.

        Notes
        -----
        Always prefer using other functions to update rather than this function if possible.
        '''

        if column in Item.__PREVENT_UPDATE:
            return 0
        
        query = f"""
            UPDATE Items
            SET {column} = ($2)
            WHERE id = ($1);
        """
        return await run_and_return_count(conn, query, id, new_value)
    @staticmethod
    async def update(conn: asyncpg.Connection, item: Item):
        '''Update an entry based on the provided object, or insert it if not existed.

        This function calls `get_one()` internally, causing an overhead.

        Notes
        -----
        This function has its own transaction.
        '''

        existing_item = await Item.get_one(conn, item.id)
        if existing_item is None:
            await Item.insert_one(conn, item)
            logger.info("Loaded new item '%s' into the database.", item.id)
        else:
            diff_col = []
            for col in existing_item.__slots__:
                if getattr(existing_item, col) != getattr(item, col):
                    diff_col.append(col)

            async with conn.transaction():
                for change in diff_col:
                    await Item.update_column(conn, item.id, change, getattr(item, change))

            if diff_col:
                logger.info("Updated item '%s' in the following columns: %s.", item.id, diff_col)

@dataclasses.dataclass(slots = True)
class Inventory(ClassToDict):
    '''Represent an entry in the `UserInventory` table along with possible operations related to the table.'''

    user_id: int
    item_id: str
    amount: int

    __PREVENT_UPDATE = ("user_id", "item_id")

    @staticmethod
    async def get_all(conn: asyncpg.Connection, *, as_dict: bool = False) -> list[t.Union[Inventory, dict]]:
        '''Get all entries in the table.'''

        return await Inventory.get_all_where(conn, as_dict = as_dict)
    @staticmethod
    async def get_all_where(conn: asyncpg.Connection, *, where: t.Callable[[Inventory], bool] = lambda r: True, as_dict: bool = False) -> list[t.Union[Inventory, dict]]:
        '''Get all entires in the table that matches the condition.'''

        query = """
            SELECT * FROM UserInventory
            ORDER BY amount DESC;
        """
        return await __get_all__(conn, query, where = where, result_type = Inventory if not as_dict else dict)
    @staticmethod
    async def get_one(conn: asyncpg.Connection, user_id: int, item_id: str, *, as_dict: bool = False) -> t.Union[Inventory, dict]:
        '''Get the first entry in the table that matches the pkey provided.'''

        query = """
            SELECT * FROM UserInventory
            WHERE user_id = ($1) AND item_id = ($2);
        """

        return await __get_one__(conn, query, user_id, item_id, result_type = Inventory if not as_dict else dict)
    @staticmethod
    async def get_user_inventory(conn, user_id: int, *, as_dict: bool = False) -> list[t.Union[Inventory, dict]]:
        '''Get all entries in the table that belongs to a user.'''

        return await Inventory.get_all_where(conn, where = lambda r: r.user_id == user_id, as_dict = as_dict)
    @staticmethod
    async def insert_one(conn: asyncpg.Connection, inventory: Inventory) -> int:
        '''Insert an entry into the table.'''

        query = insert_into_query("UserInventory", len(Inventory.__slots__))
        return await run_and_return_count(conn, query, inventory.user_id, inventory.item_id, inventory.amount)
    @staticmethod
    async def delete(conn: asyncpg.Connection, user_id: int, item_id: str) -> int:
        query = """
            DELETE FROM UserInventory
            WHERE user_id = ($1) AND item_id = ($2);
        """
        return await run_and_return_count(conn, query, user_id, item_id)
    @staticmethod
    async def update_column(conn: asyncpg.Connection, user_id: int, item_id: str, column: str, new_value) -> int:
        '''Update a specific column with a new value.

        Warnings
        --------
        Columns that are in `__PREVENT_UPDATE` (usually primary keys) will be ignored. To update such columns, use raw SQL.

        Notes
        -----
        Always prefer using other functions to update rather than this function if possible.
        '''

        if column in Inventory.__PREVENT_UPDATE:
            return 0
        
        query = f"""
            UPDATE UserInventory
            SET {column} = ($3)
            WHERE user_id = ($1) AND item_id = ($2);
        """
        return await run_and_return_count(conn, query, user_id, item_id, new_value)
    @staticmethod
    async def add(conn: asyncpg.Connection, user_id: int, item_id: str, amount: int = 1) -> int:
        '''Add item into the user's inventory.

        Notes
        -----
        This should be preferred over `Inventory.insert_one()`.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        user_id : int
            The user's id to insert.
        item_id : str
            The item's id to insert.
        amount : int, optional
            The amount of items to add. Default to 1.

        Returns
        -------
        int
            The number of entries affected. Should be 1 or 0.
        '''

        existed = await Inventory.get_one(conn, user_id, item_id)
        if not existed:
            return await Inventory.insert_one(conn, Inventory(user_id, item_id, amount))
        else:
            return await Inventory.update_column(conn, user_id, item_id, "amount", existed.amount + amount)
    @staticmethod
    async def remove(conn: asyncpg.Connection, user_id: int, item_id: str, amount: int = 1) -> int:
        '''Remove item from the user's inventory.

        Notes
        -----
        This should be preferred over `Inventory.delete()`.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        user_id : int
            The user's id to insert.
        item_id : str
            The item's id to insert.
        amount : int, optional
            The amount of items to remove. Default to 1.

        Returns
        -------
        int
            The number of entries affected. Should be 1 or 0.
        '''
        existed = await Inventory.get_one(conn, user_id, item_id)
        if not existed:
            return 0
        elif existed.amount <= amount:
            return await Inventory.delete(conn, user_id, item_id)
        else:
            return await Inventory.update_column(conn, user_id, item_id, "amount", existed.amount - amount)
    @staticmethod
    async def update(conn: asyncpg.Connection, inventory: Inventory) -> int:
        '''Update an entry based on the provided object, or insert it if not existed.

        This function calls `get_one()` internally, causing an overhead.

        Notes
        -----
        This function has its own transaction.
        '''

        existing_inv = await Inventory.get_one(conn, inventory.user_id, inventory.item_id)
        if not existing_inv:
            return await Inventory.insert_one(conn, inventory)
        
        if inventory.amount <= 0:
            return await Inventory.delete(conn, inventory.user_id, inventory.item_id)

        diff_col = []
        for col in existing_inv.__slots__:
            if col in ("user_id", "item_id", "amount"):
                if getattr(existing_inv, col) != getattr(inventory, col):
                    diff_col.append(col)
        async with conn.transaction():
            for change in diff_col:
                await Inventory.update_column(conn, inventory.user_id, inventory.item_id, change, getattr(inventory, change))

@dataclasses.dataclass(slots = True)
class Equipment(ClassToDict):
    '''Represent an entry in the `UserEquipment` table along with possible operations related to the table.'''

    user_id: int
    item_id: str
    eq_type: str
    remain_durability: int
    
    __EQUIPMENT_TYPE__ = ("_sword", "_pickaxe", "_axe", "_potion")
    __PREVENT_UPDATE = ("user_id", "item_id", "eq_type")

    @staticmethod
    async def get_all(conn: asyncpg.Connection, *, as_dict: bool = False) -> list[t.Union[Equipment, dict]]:
        '''Get all entries in the table.'''

        return await Equipment.get_all_where(conn, as_dict = as_dict)
    @staticmethod
    async def get_all_where(conn: asyncpg.Connection, *, where: t.Callable[[Equipment], bool] = lambda r: True, as_dict: bool = False) -> list[t.Union[Equipment, dict]]:
        '''Get all entires in the table that matches the condition.'''

        query = """
            SELECT * FROM UserEquipment;
        """

        return await __get_all__(conn, query, where = where, result_type = Equipment if not as_dict else dict)
    @staticmethod
    async def get_one(conn: asyncpg.Connection, user_id: int, item_id: str, *, as_dict: bool = False) -> t.Union[Equipment, dict]:
        '''Get the first entry in the table that matches the pkey provided.'''

        query = """
            SELECT * FROM UserEquipment
            WHERE user_id = ($1) AND item_id = ($2);
        """

        return await __get_one__(conn, query, user_id, item_id, result_type = Equipment if not as_dict else dict)
    @staticmethod
    async def get_equipment(conn: asyncpg.Connection, user_id: int, equipment_type: str, *, as_dict: bool = False) -> t.Union[Equipment, dict]:
        '''Get a user's equipment based on equipment type.'''

        query = """
            SELECT * FROM UserEquipment
            WHERE user_id = ($1) AND eq_type = ($2);
        """

        return await __get_one__(conn, query, user_id, equipment_type, result_type = Equipment if not as_dict else dict)
    @staticmethod
    async def get_user_equipments(conn: asyncpg.Connection, user_id: int, *, as_dict: bool = False) -> list[t.Union[Equipment, dict]]:
        return await Equipment.get_all_where(conn, where = lambda r: r.user_id == user_id, as_dict = as_dict)
    @staticmethod
    async def insert_one(conn: asyncpg.Connection, equipment: Equipment) -> int:
        '''Insert an entry into the table.'''
        
        query = insert_into_query("UserEquipment", len(equipment.__slots__))
        return await run_and_return_count(conn, query, equipment.user_id, equipment.item_id, equipment.eq_type, equipment.remain_durability)
    @staticmethod
    async def transfer_from_inventory(conn: asyncpg.Connection, inventory: Inventory) -> int:
        '''Transfer an equipment from the inventory.

        Warnings
        --------
        This does not check whether the user already has that equipment. 
        This must be checked by the user, otherwise an `asyncpg.UniqueViolationError` might be raised.

        Notes
        -----
        This function already has its own transaction. There is no need to wrap a transaction for this function.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        inventory : Inventory
            The inventory wrapping the equipment.

        Returns
        -------
        int
            The number of entries affected. Should be 1 or 0.
        
        Raises
        ------
        asyncpg.UniqueViolationError
            The unique constraint on `(user_id, eq_type)` is violated.
        '''

        is_equipment = False
        for eq_type in Equipment.__EQUIPMENT_TYPE__:
            if eq_type in inventory.item_id:
                is_equipment = True
                item = await Item.get_one(conn, inventory.item_id)
                equipment = Equipment(inventory.user_id, inventory.item_id, eq_type, item.durability)
                break
        
        if not is_equipment:
            return 0
        
        async with conn.transaction():
            status = await Inventory.remove(conn, inventory.user_id, inventory.item_id)
            if status == 0:
                return 0
            
            # TODO: Add a check to see if the same equipment type is already there.
            return await Equipment.insert_one(conn, equipment)
    @staticmethod
    async def delete(conn: asyncpg.Connection, user_id: int, item_id: str) -> int:
        '''Delete an entry in the table based on the provided key.'''

        query = """
            DELETE FROM UserEquipment
            WHERE user_id = ($1) AND item_id = ($2);
        """

        return await run_and_return_count(conn, query, user_id, item_id)
    @staticmethod
    async def update_column(conn: asyncpg.Connection, user_id: int, item_id: str, column: str, new_value) -> int:
        '''Update a specific column with a new value.

        Warnings
        --------
        Columns that are in `__PREVENT_UPDATE` (usually primary keys) will be ignored. To update such columns, use raw SQL.

        Notes
        -----
        Always prefer using other functions to update rather than this function if possible.
        '''

        if column in Equipment.__PREVENT_UPDATE:
            return 0
        
        query = f"""
            UPDATE UserEquipment
            SET {column} = ($3)
            WHERE user_id = ($1) AND item_id = ($2);
        """

        return await run_and_return_count(conn, query, user_id, item_id, new_value)
    @staticmethod
    async def update_durability(conn: asyncpg.Connection, user_id: int, item_id: str, new_durability: int) -> int:
        '''Update an equipment's durability and remove if needed.'''
        
        if new_durability <= 0:
            return await Equipment.delete(conn, user_id, item_id)
        return await Equipment.update_column(conn, user_id, item_id, "remain_durability", new_durability)
    @staticmethod
    def is_equipment(item_id: str) -> bool:
        '''Check if the item is an equipment or not.

        Parameters
        ----------
        item_id : str
            The item's id to check.

        Returns
        -------
        bool
            Whether the item is an equipment or not.
        '''
        for eq_type in Equipment.__EQUIPMENT_TYPE__:
            if eq_type in item_id:
                return True
        return False
    @staticmethod
    def is_true_equipment(item_id: str) -> bool:
        return Equipment.is_equipment(item_id) and not Equipment.is_potion(item_id)
    @staticmethod
    def is_potion(item_id: str) -> bool:
        return "_potion" in item_id
    @staticmethod
    def get_equipment_type(item_id: str) -> t.Optional[str]:
        '''Return the equipment type of the equipment.

        Parameters
        ----------
        item_id : str
            The item's id.

        Returns
        -------
        t.Optional[str]
            The equipment type of the equipment, or `None` if it is not an equipment.
        '''
        if not Equipment.is_equipment(item_id):
            return None
        
        return '_' + item_id.split('_')[-1]

@dataclasses.dataclass(slots = True)
class ActiveTrade(ClassToDict):
    id: int
    type: str
    item_src: str
    amount_src: int
    item_dest: str
    amount_dest: int
    next_reset: dt.datetime
    hard_limit: int = 15

    __TRADE_TYPE = ("trade", "barter")

    @staticmethod
    async def get_all(conn: asyncpg.Connection, *, as_dict: bool = False):
        return await ActiveTrade.get_all_where(conn, as_dict = as_dict)
    @staticmethod
    async def get_all_where(conn: asyncpg.Connection, *, where: t.Callable[[ActiveTrade], bool] = lambda r: True, as_dict: bool = False):
        query = """
            SELECT * FROM ActiveTrades
            ORDER BY id;
        """
        return await __get_all__(conn, query, where = where, result_type = ActiveTrade if not as_dict else dict)
    @staticmethod
    async def get_one(conn: asyncpg.Connection, id: int, type: str, *, as_dict: bool = False):
        query = """
            SELECT * FROM ActiveTrades
            WHERE id = ($1) AND type = ($2);
        """
        return await __get_one__(conn, query, id, type, result_type = ActiveTrade if not as_dict else dict)
    @staticmethod
    async def get_by_type(conn: asyncpg.Connection, type: str, *, as_dict: bool = False):
        return await ActiveTrade.get_all_where(conn, where = lambda r: r.type == type, as_dict = as_dict)
    @staticmethod
    async def insert_one(conn: asyncpg.Connection, trade: ActiveTrade):
        query = insert_into_query("ActiveTrades", len(ActiveTrade.__slots__))
        return await run_and_return_count(conn, query, 
            trade.id,
            trade.type,
            trade.item_src,
            trade.amount_src,
            trade.item_dest,
            trade.amount_dest,
            trade.next_reset,
            trade.hard_limit,
        )
    @staticmethod
    async def refresh(conn: asyncpg.Connection, trades: list[ActiveTrade]):
        async with conn.transaction():
            await conn.execute("TRUNCATE TABLE ActiveTrades CASCADE;")
            for trade in trades:
                await ActiveTrade.insert_one(conn, trade)

@dataclasses.dataclass(slots = True)
class UserTrade:
    user_id: int
    trade_id: int
    trade_type: str
    hard_limit: int
    count: int = 1

    __PREVENT_UPDATE = ("user_id", "trade_id", "trade_type", "hard_limit")

    @staticmethod
    async def get_all(conn: asyncpg.Connection, *, as_dict: bool = False):
        return await UserTrade.get_all_where(conn, as_dict = as_dict)
    @staticmethod
    async def get_all_where(conn: asyncpg.Connection, *, where: t.Callable[[UserTrade], bool] = lambda r: True, as_dict: bool = False):
        query = """
            SELECT * FROM Users_ActiveTrades
            ORDER BY trade_id;
        """
        return await __get_all__(conn, query, where = where, result_type = UserTrade if not as_dict else dict)
    @staticmethod
    async def get_one(conn: asyncpg.Connection, user_id: int, trade_id: int, trade_type: str, *, as_dict: bool = False):
        query = """
            SELECT * FROM Users_ActiveTrades
            WHERE user_id = ($1) AND trade_id = ($2) AND trade_type = ($3);
        """
        return await __get_one__(conn, query, user_id, trade_id, trade_type, result_type = UserTrade if not as_dict else dict)
    @staticmethod
    async def insert_one(conn: asyncpg.Connection, user_trade: UserTrade):
        query = insert_into_query("Users_ActiveTrades", len(UserTrade.__slots__))
        return await run_and_return_count(conn, query,
            user_trade.user_id,
            user_trade.trade_id,
            user_trade.trade_type,
            user_trade.hard_limit,
            user_trade.count,
        )
    @staticmethod
    async def update_column(conn: asyncpg.Connection, user_id: int, trade_id: int, trade_type: str, column: str, new_value):
        if column in UserTrade.__PREVENT_UPDATE:
            return 0

        query = f"""
            UPDATE Users_ActiveTrades
            SET {column} = ($4)
            WHERE user_id = ($1) AND trade_id = ($2) AND trade_type = ($3);
        """
        return await run_and_return_count(conn, query, user_id, trade_id, trade_type, new_value)
    @staticmethod
    async def update(conn: asyncpg.Connection, user_trade: UserTrade):
        existing_trade = await UserTrade.get_one(conn, user_trade.user_id, user_trade.trade_id, user_trade.trade_type)
        if not existing_trade:
            return await UserTrade.insert_one(conn, user_trade)

        diff_col = []
        for col in existing_trade.__slots__:
            if getattr(existing_trade, col) != getattr(user_trade, col):
                diff_col.append(col)
        async with conn.transaction():
            for change in diff_col:
                await UserTrade.update_column(conn, user_trade.user_id, user_trade.trade_id, user_trade.trade_type, change, getattr(user_trade, change))
