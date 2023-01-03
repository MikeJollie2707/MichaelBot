import dataclasses
import typing as t

import asyncpg

from utils.psql._base import *


@dataclasses.dataclass(slots = True)
class ExtraInventory(BaseSQLObject):
    # Although this class is practically a clone of Inventory, we need to manually define all of them because of default args.
    '''Represent an entry in the `UserExtraInventory` table along with possible operations related to the table.'''

    user_id: int
    item_id: str
    amount: int

    _tbl_name: t.ClassVar[str] = "UserExtraInventory"
    _PREVENT_UPDATE: t.ClassVar[tuple[str]] = ("user_id", "item_id")

    @classmethod
    async def fetch_all_where(cls, conn: asyncpg.Connection, *, as_dict: bool = False, where: t.Callable[[t.Self], bool] = lambda r: True) -> list[t.Self] | list[dict] | list[None]:
        query = """
            SELECT * FROM UserExtraInventory
            ORDER BY amount DESC;
        """
        return await _get_all(conn, query, where = where, result_type = ExtraInventory if not as_dict else dict)
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
            The attributes to find, such as `id = value`. You must provide the following kw: `user_id: int`, `item_id: str`.

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
        _item_id = kwargs["item_id"]
        query = """
            SELECT * FROM UserExtraInventory
            WHERE user_id = ($1) AND item_id = ($2);
        """

        return await _get_one(conn, query, _user_id, _item_id, result_type = ExtraInventory if not as_dict else dict)
    @staticmethod
    async def get_user_inventory(conn, user_id: int, *, as_dict: bool = False) -> list[t.Self] | list[dict] | list[None]:
        '''Get all entries in the table that belongs to a user.'''

        return await ExtraInventory.fetch_all_where(conn, where = lambda r: r.user_id == user_id, as_dict = as_dict)
    @classmethod
    async def delete(cls, conn: asyncpg.Connection, **kwargs) -> int:
        '''Delete an entry from the table.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        **kwargs : dict, optional
            The attributes to find, such as `id = value`. You must provide the following kw: `user_id: int`, `item_id: str`.
        
        Returns
        -------
        int
            The amount of entries deleted.

        Raises
        ------
        KeyError
            The needed keyword is not present in `**kwargs`.
        '''
        _user_id = kwargs["user_id"]
        _item_id = kwargs["item_id"]
        query = """
            DELETE FROM UserExtraInventory
            WHERE user_id = ($1) AND item_id = ($2);
        """

        return await run_and_return_count(conn, query, _user_id, _item_id)
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
            The attributes to find, such as `id = value`. You must provide the following kw: `user_id: int`, `item_id: str`.

        Returns
        -------
        int
            The amount of entries updated.
        
        Raises
        ------
        KeyError
            The needed kw is not present in `**kwargs`.
        '''

        # For this part, the hierarchy is kinda confusing, so it's best to just implement the check yourself.
        for column in column_value_pair:
            if column in ExtraInventory._PREVENT_UPDATE:
                return 0

        if len(column_value_pair) < 1:
            return 0
        _user_id = kwargs["user_id"]
        _item_id = kwargs["item_id"]

        query, index = update_query(ExtraInventory._tbl_name, column_value_pair.keys())
        query += f"WHERE user_id = (${index}) AND item_id = (${index + 1});"
        return await run_and_return_count(conn, query, *(column_value_pair.values()), _user_id, _item_id)
    @staticmethod
    async def add(conn: asyncpg.Connection, user_id: int, item_id: str, amount: int = 1) -> int:
        '''Add item into the user's safe inventory.

        Notes
        -----
        This should be preferred over `ExtraInventory.insert_one()`.

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

        existed = await ExtraInventory.fetch_one(conn, user_id = user_id, item_id = item_id)
        if not existed:
            return await ExtraInventory.insert_one(conn, ExtraInventory(user_id, item_id, amount))
        else:
            return await ExtraInventory.update_column(conn, {"amount": existed.amount + amount}, user_id = user_id, item_id = item_id)
    @staticmethod
    async def remove(conn: asyncpg.Connection, user_id: int, item_id: str, amount: int = 1) -> int:
        '''Remove item from the user's safe inventory.

        Notes
        -----
        This should be preferred over `ExtraInventory.delete()`.

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
        existed = await ExtraInventory.fetch_one(conn, user_id = user_id, item_id = item_id)
        if not existed:
            return 0
        elif existed.amount <= amount:
            return await ExtraInventory.delete(conn, user_id = user_id, item_id = item_id)
        else:
            return await ExtraInventory.update_column(conn, {"amount": existed.amount - amount}, user_id = user_id, item_id = item_id)
    @classmethod
    async def update(cls, conn: asyncpg.Connection, inventory: t.Self) -> int:
        '''Update an entry based on the provided object, or insert if it's not found.

        This function calls `fetch_one()` internally, causing an overhead.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        inventory : t.Self
            The object to update/insert.

        Returns
        -------
        int
            The number of entries affected.
        '''
        
        existed_inv = await ExtraInventory.fetch_one(conn, user_id = inventory.user_id, item_id = inventory.item_id)
        if not existed_inv:
            return await ExtraInventory.insert_one(conn, inventory)
        
        if inventory.amount <= 0:
            return await ExtraInventory.delete(conn, user_id = inventory)
    
        diff_col = {}
        for col in existed_inv.__slots__:
            if getattr(existed_inv, col) != getattr(inventory, col):
                diff_col[col] = getattr(inventory, col)
        
        return await ExtraInventory.update_column(conn, diff_col, user_id = inventory.user_id, item_id = inventory.item_id)
