import dataclasses
import typing as t

import asyncpg
import logging

from utils.psql._base import *

@dataclasses.dataclass(slots = True)
class Badge(BaseSQLObject):
    id: str
    sort_id: int
    name: str
    emoji: str
    description: str
    requirement: int = 0

    _tbl_name: t.ClassVar[str] = "Badges"
    _PREVENT_UPDATE: t.ClassVar[tuple[str]] = ("id", )

    @classmethod
    async def fetch_all_where(cls, conn: asyncpg.Connection, *, as_dict: bool = False, where: t.Callable[[t.Self], bool] = lambda r: True) -> list[t.Self] | list[dict] | list[None]:
        query = """
            SELECT * FROM Badges
            ORDER BY sort_id;
        """
        return await _get_all(conn, query, where = where, result_type = Badge if not as_dict else dict)
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
            The attributes to find, such as `id = value`. You must provide the following kw: `id: str`.

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
            SELECT * FROM Badges
            WHERE id = ($1);
        """

        return await _get_one(conn, query, _id, result_type = Badge if not as_dict else dict)
    @staticmethod
    async def fetch_by_name(conn: asyncpg.Connection, name: str, *, as_dict: bool = False):
        query = """
            SELECT * FROM Badges
            WHERE name LIKE ($1);
        """

        return await _get_one(conn, query, name, result_type = Badge if not as_dict else dict)
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
        check = await super(Badge, cls).update_column(conn, column_value_pair, **kwargs)
        if not check:
            return 0
        
        if len(column_value_pair) < 1:
            return 0
        _id = kwargs["id"]

        query, index = update_query(Badge._tbl_name, column_value_pair.keys())
        query += f"WHERE id = (${index});"
        return await run_and_return_count(conn, query, *(column_value_pair.values()), _id)
    @classmethod
    async def update(cls, conn: asyncpg.Connection, badge: t.Self) -> int:
        '''Update an entry based on the provided object, or insert if it's not found.

        This function calls `fetch_one()` internally, causing an overhead.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        badge : t.Self
            The object to update/insert.

        Returns
        -------
        int
            The number of entries affected.
        '''
        
        existed_badge = await Badge.fetch_one(conn, id = badge.id)
        if not existed_badge:
            count = await Badge.insert_one(conn, badge)
            logger.info("Loaded new badge '%s' into the database.", badge.id)
        else:
            diff_col = {}
            for col in existed_badge.__slots__:
                if getattr(existed_badge, col) != getattr(badge, col):
                    diff_col[col] = getattr(badge, col)
            
            count = await Badge.update_column(conn, diff_col, id = badge.id)
        
        return count
