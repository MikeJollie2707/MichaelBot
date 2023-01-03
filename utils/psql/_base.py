import dataclasses
import logging
import typing as t

import asyncpg

__all__ = (
    # No need to re-import these later on.
    # BUG: Because for some reasons, griffe can't build docs if I try to from _base import *,
    # I'll need to comment this out.
    #"dataclasses",
    #"logging",
    #"t",
    #"asyncpg",

    "logger",
    "record_to_type",
    "insert_into_query",
    "update_query",
    "_get_all",
    "_get_one",
    "run_and_return_count",
    "BaseSQLObject"
)

logger = logging.getLogger("MichaelBot")
T = t.TypeVar('T')

def record_to_type(record: asyncpg.Record, /, result_type: t.Type[T] = dict) -> T | dict | None:
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

    Returns
    -------
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

def update_query(table_name: str, columns: t.Sequence[str]) -> tuple[str, int]:
    '''Return an incomplete SQL statement to update columns in a table.

    The returning query will have the format of `UPDATE table SET col1 = val1, ...` with missing semicolon.
    Therefore, you can add any additional constraints, such as WHERE clause.

    Parameters
    ----------
    table_name : str
        The table to update.
    columns : t.Sequence[str]
        The columns to update.

    Returns
    -------
    tuple(str, int)
        An incomplete UPDATE statement and the number to be used in any next parameters (ie. 6 to be used as `($6)`)
    '''

    params = []
    last_index = 0
    for index, column in enumerate(columns):
        params.append(f"{column} = (${index + 1})")
        last_index = index + 1
    arg_str = ', '.join(params)

    return (f"UPDATE {table_name} SET {arg_str} ", last_index + 1)

async def _get_all(conn: asyncpg.Connection, query: str, *args, where: t.Callable[[T], bool] = lambda r: True, result_type: type[T] = dict) -> list[T]:
    '''Run a `SELECT` statement and return a list of objects.

    This should NOT be used outside of the module. Instead, use `table_name.get_all()`.

    Parameters
    ----------
    conn : asyncpg.Connection
        The connection to use.
    query : str 
        The `SELECT` statement to run. This should not contain `WHERE` clause.
        Conditions should be set in `where` parameter.
    *args : tuple
        Any parameters to be passed into the query.
    where : t.Callable[[dict], bool]
        Additional conditions to filter. By default, no condition is applied (always return `True`).
    result_type : t.Type[T]
        The type to convert to. The type must be a dataclass or an object that can be initialized via kwargs or a `dict`. Default to `dict`.

    Returns
    -------
    list[T]
        A list of `result_type` or empty list.
    '''

    result = await conn.fetch(query, *args)
    records: list[result_type] = []
    record_obj = None
    for record in result:
        # NOTE: This code is for handling dict case; will remove soon.
        #record_obj = record_to_type(record)
        #if record_obj is None or (record_obj is not None and where(record_obj)):
        #    l.append(record_obj)
        record_obj = record_to_type(record, result_type)
        if record_obj is None or (record_obj is not None and where(record_obj)):
            records.append(record_obj)
    
    return records

async def _get_one(conn: asyncpg.Connection, query: str, *constraints, result_type: t.Type[T] = dict) -> t.Optional[T]:
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
    logger.debug(query)
    params = ' '.join([str(p) for p in args])
    logger.debug(params)
    status = await conn.execute(query, *args, **kwargs)
    
    # INSERT returns "INSERT oid count".
    try:
        count = int(status.split()[-1])
        return count
    except ValueError:
        return None

@dataclasses.dataclass(slots = True)
class BaseSQLObject:
    '''The base class of all SQL objects defined in this module.
    
    This class contains generic functions that all SQL classes will provide.
    Some functions will need to be overridden for their specific purposes.

    It's required to follow certain behavior laid out in the docstring of each functions (ie. Manually enforce `_PREVENT_UPDATE` check in `update_column()`).
    '''

    _tbl_name: t.ClassVar[str]
    '''The table's name this class is attached to.'''
    _PREVENT_UPDATE: t.ClassVar[tuple[str]]
    '''The name of the columns that won't be updated via high-level SQL Functions.'''

    @classmethod
    async def fetch_all_where(cls, conn: asyncpg.Connection, *, as_dict: bool = False, where: t.Callable[[t.Self], bool] = lambda r: True) -> list[t.Self] | list[dict] | list[None]:
        '''Fetch all entries in the table that matches the condition.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        as_dict : bool, optional
            Whether the result should be in the `dict` or in `Self`, by default False
        where : Callable[[Self | dict], bool], optional
            The WHERE filter to apply. Note that if `as_dict` is `True`, the callback must accept a `dict`.

        Returns
        -------
        list[t.Self] | list[dict]
            A list of matched entries.
        
        Raises
        -----
        NotImplementedError
            This function is required to be overridden in subclasses.
        '''

        raise NotImplementedError
    @classmethod
    async def fetch_all(cls, conn: asyncpg.Connection, *, as_dict: bool = False) -> list[t.Self] | list[dict] | list[None]:
        '''Fetch all entries in the table.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        as_dict : bool, optional
            Whether the result should be in the `dict` or in `Self`, by default False

        Returns
        -------
        list[t.Self] | list[dict]
            A list of all entries.

        Notes
        -----
        This function is optional to override. From experience, its only job is to call `fetch_all_where()` with no filter.
        '''

        return await cls.fetch_all_where(conn, as_dict = as_dict)
    @classmethod
    async def fetch_one(cls, conn: asyncpg.Connection, *, as_dict: bool = False, **kwargs) -> t.Self | dict | None:
        '''Fetch one entry in the table that matches the condition.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        as_dict : bool, optional
            Whether the result should be in the `dict` or in `Self`, by default False
        **kwargs : dict, optional
            The attributes to find, such as `id = value`. Depending on the subclass, many kw might be required.

        Returns
        -------
        t.Self | dict | None
            Either the object itself or `dict`, depending on `as_dict`. If not existed, `None` is returned.

        Raises
        ------
        KeyError
            The needed keyword is not present in `**kwargs`.
        NotImplementedError
            This function is required to be overridden in subclasses.
        
        Notes
        -----
        This must be overridden by the subclasses.
        '''

        raise NotImplementedError
    @classmethod
    async def insert_one(cls, conn: asyncpg.Connection, obj: t.Self) -> int:
        '''Insert an entry to the table.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        obj : t.Self
            The entry to insert.

        Returns
        -------
        int
            The amount of entries inserted. Normally, this should be 1.

        Raises
        ------
        TypeError
            `obj` does not inherit from `__BaseSQLObject`.
        '''
        if not isinstance(obj, BaseSQLObject):
            raise TypeError(f"Type '{type(obj)}' is not a subtype of '__BaseSQLObject'")
        
        query = insert_into_query(cls._tbl_name, len(obj.__slots__))
        return await run_and_return_count(conn, query, *[getattr(obj, attr) for attr in obj.__slots__])
    @classmethod
    async def delete(cls, conn: asyncpg.Connection, **kwargs) -> int:
        '''Delete an entry from the table.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        **kwargs : dict, optional
            The attributes to find, such as `id = value`. Depending on the subclass, many kw might be required.
        
        Returns
        -------
        int
            The amount of entries deleted.

        Raises
        ------
        KeyError
            The needed keyword is not present in `**kwargs`.
        NotImplementedError
            This function is required to be overridden in subclasses.
        
        Notes
        -----
        This must be overridden by the subclasses.
        '''

        raise NotImplementedError
    @classmethod
    async def update_column(cls, conn: asyncpg.Connection, column_value_pair: dict[str, t.Any], **kwargs) -> int:
        '''Update specified columns with new value.

        Warnings
        --------
        If a column is in `_PREVENT_UPDATE` (usually primary keys), the function will not do anything. To update such columns, use raw SQL.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        column_value_pair : dict[str, t.Any]
            The column name and the new value to update with.
        **kwargs : dict, optional
            The attributes to find, such as `id = value`. The keyword must match an existing attribute.

        Returns
        -------
        int
            The amount of entries updated.

        Raises
        ------
        KeyError
            The needed kw is not present in `**kwargs`.
        NotImplementedError
            This function is required to be overridden in subclasses.
        
        Notes
        -----
        When overriding this function, it's required to call the root's version before doing any updating. This is to apply the `_PREVENT_UPDATE` check.
        This function is rather special, as it'll return 0 if the `_PREVENT_UPDATE` check failed, 1 otherwise. The return value doesn't relate to the amount of entries affected.
        I'm pretty sure this is bad design but I don't know how to "inject" the check otherwise.
        '''
        
        for column in column_value_pair:
            if column in cls._PREVENT_UPDATE:
                return 0
        
        return 1
    @classmethod
    async def update(cls, conn: asyncpg.Connection, obj: t.Self) -> int:
        '''Update an entry based on the provided object, or insert if it's not found.

        This function calls `fetch_one()` internally, causing an overhead.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        obj : t.Self
            The object to update/insert.

        Returns
        -------
        int
            The number of entries affected.
        
        Raises
        -----
        NotImplementedError
            This function is required to be overridden in subclasses.
        '''
        
        raise NotImplementedError
