import dataclasses
import typing as t

import asyncpg

from utils.psql._base import *


@dataclasses.dataclass(slots = True)
class Guild(BaseSQLObject):
    '''Represent an entry in the `Guilds` table along with possible operations related to the table.

    It is advised to use the cache in the bot instead. These methods are for mostly cache construction.
    '''

    id: int
    name: str
    is_whitelist: bool = True
    prefix: str = '$'
    
    _tbl_name: t.ClassVar[str] = "Guilds"
    _PREVENT_UPDATE: t.ClassVar[tuple[str]] = ("id", )

    @classmethod
    async def fetch_all_where(cls, conn: asyncpg.Connection, *, as_dict: bool = False, where: t.Callable[[t.Self], bool] = lambda r: True) -> list[t.Self] | list[dict] | list[None]:
        query = """
            SELECT * FROM Guilds
            ORDER BY Guilds.name;
        """
        return await _get_all(conn, query, where = where, result_type = Guild if not as_dict else dict)
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
            SELECT * FROM Guilds
            WHERE id = ($1);
        """

        return await _get_one(conn, query, _id, result_type = Guild if not as_dict else dict)
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
            DELETE FROM Guilds
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
        
        check = await super(Guild, cls).update_column(conn, column_value_pair, **kwargs)
        if not check:
            return 0
        
        if len(column_value_pair) < 1:
            return 0
        _id = kwargs["id"]
        
        query, index = update_query(Guild._tbl_name, column_value_pair.keys())
        query += f"WHERE id = (${index});"
        return await run_and_return_count(conn, query, *(column_value_pair.values()), _id)
    @classmethod
    async def update(cls, conn: asyncpg.Connection, guild: t.Self) -> int:
        '''Update an entry based on the provided object, or insert if it's not found.

        This function calls `fetch_one()` internally, causing an overhead.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        guild : t.Self
            The object to update/insert.

        Returns
        -------
        int
            The number of entries affected.
        '''
        
        existed_guild = await Guild.fetch_one(conn, id = guild.id)
        if not existed_guild:
            return await Guild.insert_one(conn, guild)
    
        diff_col = {}
        for col in existed_guild.__slots__:
            if getattr(existed_guild, col) != getattr(guild, col):
                diff_col[col] = getattr(guild, col)
        
        return await Guild.update_column(conn, diff_col, id = guild.id)
