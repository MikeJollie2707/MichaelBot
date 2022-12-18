import dataclasses
import typing as t

import asyncpg
import datetime as dt

from utils.psql._base import *

@dataclasses.dataclass(slots = True)
class ActiveTrade(BaseSQLObject):
    id: int
    type: str
    item_src: str
    amount_src: int
    item_dest: str
    amount_dest: int
    next_reset: dt.datetime
    hard_limit: int = 15

    _tbl_name: t.ClassVar[str] = "ActiveTrades"
    _PREVENT_UPDATE: t.ClassVar[tuple[str]] = ("id", "type")
    __TRADE_TYPE = ("trade", "barter")

    @classmethod
    async def fetch_all_where(cls, conn: asyncpg.Connection, *, as_dict: bool = False, where: t.Callable[[t.Self], bool] = lambda r: True) -> list[t.Self] | list[dict] | list[None]:
        query = """
            SELECT * FROM ActiveTrades
            ORDER BY id;
        """
        return await _get_all(conn, query, where = where, result_type = ActiveTrade if not as_dict else dict)
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
            The attributes to find, such as `id = value`. You must provide the following kw: `id: int`, `type: str`.

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
        _type = kwargs["type"]
        query = """
            SELECT * FROM ActiveTrades
            WHERE id = ($1) AND type = ($2);
        """

        return await _get_one(conn, query, _id, _type, result_type = ActiveTrade if not as_dict else dict)
    @staticmethod
    async def get_by_type(conn: asyncpg.Connection, type: str, *, as_dict: bool = False):
        return await ActiveTrade.fetch_all_where(conn, where = lambda r: r.type == type, as_dict = as_dict)
    @staticmethod
    async def refresh(conn: asyncpg.Connection, trades: list[t.Self]):
        async with conn.transaction():
            await conn.execute("TRUNCATE TABLE ActiveTrades CASCADE;")
            for trade in trades:
                await ActiveTrade.insert_one(conn, trade)
