import dataclasses
import typing as t

import asyncpg
import datetime as dt

from utils.psql._base import *

@dataclasses.dataclass(slots = True)
class User(BaseSQLObject):
    '''Represent an entry in the `Users` table along with possible operations related to the table.

    It is advised to use the cache in the bot instead. These methods are for mostly cache construction.
    '''

    id: int
    name: str
    is_whitelist: bool = True
    balance: int = 0
    world: str = "overworld"
    last_travel: t.Optional[dt.datetime] = None
    daily_streak: int = 0
    last_daily: t.Optional[dt.datetime] = None
    health: int = 100
    
    _tbl_name: t.ClassVar[str] = "Users"
    _PREVENT_UPDATE: t.ClassVar[tuple[str]] = ("id", )
    __WORLD_TYPE = ("overworld", "nether", "end")

    @classmethod
    async def fetch_all_where(cls, conn: asyncpg.Connection, *, as_dict: bool = False, where: t.Callable[[t.Self], bool] = lambda r: True) -> list[t.Self] | list[dict] | list[None]:
        query = """
            SELECT * FROM Users
            ORDER BY Users.name;
        """
        return await _get_all(conn, query, where = where, result_type = User if not as_dict else dict)
    @classmethod
    async def fetch_one(cls, conn: asyncpg.Connection, *, as_dict: bool = False, **kwargs) -> t.Self | dict | None:
        '''Fetch one entry in the table that matches the condition.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        as_dict : bool, optional
            Whether the result should be in the `dict` or in `Self`, by default False
        **kwargs
            The attributes to find, such as `id = value`. You must provide the following kw: `id: int`.

        Returns
        -------
        t.Self | dict | None
            Either the object itself or `dict`, depending on `as_dict`. If not existed, `None` is returned.
        
        Raises
        ------
        KeyError
            The needed keyword is not present in `**kwargs`.
        '''

        _id = kwargs["id"]
        query = """
            SELECT * FROM Users
            WHERE id = ($1);
        """

        return await _get_one(conn, query, _id, result_type = User if not as_dict else dict)
    @classmethod
    async def delete(cls, conn: asyncpg.Connection, **kwargs) -> int:
        '''Delete an entry from the table.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        **kwargs : dict, optional
            The attributes to find, such as `id = value`. You must provide the following kw: `id: int`.
        
        Returns
        -------
        int
            The amount of entries deleted.

        Raises
        ------
        KeyError
            The needed keyword is not present in `**kwargs`.
        '''

        _id = kwargs["id"]
        query = """
            DELETE FROM Users
            WHERE id = ($1);
        """

        return await run_and_return_count(conn, query, _id)
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
            The attributes to find, such as `id = value`. You must provide the following kw: `id: int`.

        Returns
        -------
        int
            The amount of entries updated.
        
        Raises
        ------
        KeyError
            The needed kw is not present in `**kwargs`.
        '''
        check = await super(User, cls).update_column(conn, column_value_pair, **kwargs)
        if not check:
            return 0

        if len(column_value_pair) < 1:
            return 0
        _id = kwargs["id"]

        query, index = update_query(User._tbl_name, column_value_pair.keys())
        query += f"WHERE id = (${index});"
        return await run_and_return_count(conn, query, *(column_value_pair.values()), _id)
    @staticmethod
    async def update_balance(conn: asyncpg.Connection, id: int, new_balance: int) -> int:
        if new_balance < 0:
            # Might raise a warning here?
            return 0
        
        return await User.update_column(conn, {"balance": new_balance}, id = id)
    @staticmethod
    async def update_streak(conn: asyncpg.Connection, id: int, new_streak: int) -> int:
        if new_streak < 0:
            # Might raise a warning here?
            return 0
        
        return await User.update_column(conn, {"daily_streak": new_streak}, id = id)
    @staticmethod
    async def add_money(conn: asyncpg.Connection, id: int, amount: int) -> int:
        if amount <= 0:
            return 0
        
        existed = await User.fetch_one(conn, id = id)
        if not existed:
            return 0
        
        return await User.update_balance(conn, id, existed.balance + amount)
    @staticmethod
    async def remove_money(conn: asyncpg.Connection, id: int, amount: int) -> int:
        if amount <= 0:
            return 0
        
        existed = await User.fetch_one(conn, id = id)
        if not existed:
            return 0
        
        if existed.balance <= amount:
            # Might raise a warning here? Idk.
            existed.balance = 0
        else:
            existed.balance -= amount
        
        return await User.update_balance(conn, id, existed.balance)
    @classmethod
    async def update(cls, conn: asyncpg.Connection, user: t.Self) -> int:
        '''Update an entry based on the provided object, or insert if it's not found.

        This function calls `fetch_one()` internally, causing an overhead.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        user : t.Self
            The object to update/insert.

        Returns
        -------
        int
            The number of entries affected.
        '''
        
        existed_guild = await User.fetch_one(conn, id = user.id)
        if not existed_guild:
            return await User.insert_one(conn, user)
    
        diff_col = {}
        for col in existed_guild.__slots__:
            if getattr(existed_guild, col) != getattr(user, col):
                diff_col[col] = getattr(user, col)
        
        return await User.update_column(conn, diff_col, id = user.id)
