import dataclasses
import typing as t

import asyncpg
from utils.psql._base import *

@dataclasses.dataclass(slots = True)
class UserTrade(BaseSQLObject):
    user_id: int
    trade_id: int
    trade_type: str
    hard_limit: int
    count: int = 1

    _tbl_name: t.ClassVar[str] = "Users_ActiveTrades"
    _PREVENT_UPDATE: t.ClassVar[tuple[str]] = ("user_id", "trade_id", "trade_type", "hard_limit")

    @classmethod
    async def fetch_all_where(cls, conn: asyncpg.Connection, *, as_dict: bool = False, where: t.Callable[[t.Self], bool] = lambda r: True) -> list[t.Self] | list[dict] | list[None]:
        query = """
            SELECT * FROM Users_ActiveTrades
            ORDER BY trade_id;
        """
        return await _get_all(conn, query, where = where, result_type = UserTrade if not as_dict else dict)
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
            The attributes to find, such as `id = value`. You must provide the following kw: `user_id: int`, `trade_id: int`, `trade_type: str`.

        Returns
        -------
        t.Self | dict | None
            Either the object itself or `dict`, depending on `as_dict`. If not existed, `None` is returned.
        
        Raises
        ------
        KeyError
            The needed keyword is not present in `**kwargs`.
        '''
        _user_id = kwargs["user_id"]
        _trade_id = kwargs["trade_id"]
        _trade_type = kwargs["trade_type"]
        query = """
            SELECT * FROM Users_ActiveTrades
            WHERE user_id = ($1) AND trade_id = ($2) AND trade_type = ($3);
        """

        return await _get_one(conn, query, _user_id, _trade_id, _trade_type, result_type = UserTrade if not as_dict else dict)
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
            The attributes to find, such as `id = value`. You must provide the following kw: `user_id: int`, `trade_id: int`, `trade_type: str`.

        Returns
        -------
        int
            The amount of entries updated.
        
        Raises
        ------
        KeyError
            The needed kw is not present in `**kwargs`.
        '''
        check = await super(UserTrade, cls).update_column(conn, column_value_pair, **kwargs)
        if not check:
            return 0
        
        if len(column_value_pair) < 1:
            return 0
        _user_id = kwargs["user_id"]
        _trade_id = kwargs["trade_id"]
        _trade_type = kwargs["trade_type"]

        query, index = update_query(UserTrade._tbl_name, column_value_pair.keys())
        query += f"WHERE user_id = (${index}) AND trade_id = (${index + 1}) AND trade_type = (${index + 2});"
        return await run_and_return_count(conn, query, *(column_value_pair.values()), _user_id, _trade_id, _trade_type)
    @classmethod
    async def update(conn: asyncpg.Connection, user_trade: t.Self):
        '''Update an entry based on the provided object, or insert if it's not found.

        This function calls `fetch_one()` internally, causing an overhead.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        user_trade : t.Self
            The object to update/insert.

        Returns
        -------
        int
            The number of entries affected.
        '''
        existing_trade = await UserTrade.fetch_one(conn, user_id = user_trade.user_id, trade_id = user_trade.trade_id, trade_type = user_trade.trade_type)
        if not existing_trade:
            return await UserTrade.insert_one(conn, user_trade)

        diff_col = {}
        for col in existing_trade.__slots__:
            if getattr(existing_trade, col) != getattr(user_trade, col):
                diff_col[col] = getattr(user_trade, col)
        
        return await UserTrade.update_column(conn, diff_col, user_id = user_trade.user_id, trade_id = user_trade.trade_id, trade_type = user_trade.trade_type)
