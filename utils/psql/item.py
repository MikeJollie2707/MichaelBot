import logging

from utils.psql._base import *


@dataclasses.dataclass(slots = True)
class Item(_BaseSQLObject):
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

    _tbl_name: t.ClassVar[str] = "Items"
    _PREVENT_UPDATE: t.ClassVar[tuple[str]] = ("id", )

    @classmethod
    async def fetch_all_where(cls, conn: asyncpg.Connection, *, as_dict: bool = False, where: t.Callable[[t.Self], bool] = lambda r: True) -> list[t.Self] | list[dict] | list[None]:
        query = """
            SELECT * FROM Items
            ORDER by sort_id;
        """
        return await _get_all(conn, query, where = where, result_type = Item if not as_dict else dict)
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
            SELECT * FROM Items
            WHERE id = ($1);
        """

        return await _get_one(conn, query, _id, result_type = Item if not as_dict else dict)
    @staticmethod
    async def fetch_by_name(conn: asyncpg.Connection, name_or_alias: str, *, as_dict: bool = False) -> t.Self | dict | None:
        '''Fetch the first item that has its name/aliases match the provided.'''

        def filter_name_alias(record: t.Self):
            return record.name.lower() == name_or_alias.lower() or name_or_alias.lower() in [alias.lower() for alias in record.aliases]
        
        res = await Item.fetch_all_where(conn, where = filter_name_alias, as_dict = as_dict)
        
        assert len(res) <= 1
        if res:
            return res[0]
        return None
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
            The attributes to find, such as `id = value`. You must provide the following kw: `id: str`.

        Returns
        -------
        int
            The amount of entries updated.
        
        Raises
        ------
        KeyError
            The needed kw is not present in `**kwargs`.
        '''
        check = await super(Item, cls).update_column(conn, column_value_pair, **kwargs)
        if not check:
            return 0
        
        if len(column_value_pair) < 1:
            return 0
        _id = kwargs["id"]

        query, index = update_query(Item._tbl_name, column_value_pair.keys())
        query += f"WHERE id = (${index});"
        return await run_and_return_count(conn, query, *(column_value_pair.values()), _id)
    @classmethod
    async def update(cls, conn: asyncpg.Connection, item: t.Self) -> int:
        '''Update an entry based on the provided object, or insert if it's not found.

        This function calls `fetch_one()` internally, causing an overhead.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        item : t.Self
            The object to update/insert.

        Returns
        -------
        int
            The number of entries affected.
        '''
        
        existed_guild = await Item.fetch_one(conn, id = item.id)
        if not existed_guild:
            count = await Item.insert_one(conn, item)
            logger.info("Loaded new item '%s' into the database.", item.id)
        else:
            diff_col = {}
            for col in existed_guild.__slots__:
                if getattr(existed_guild, col) != getattr(item, col):
                    diff_col[col] = getattr(item, col)
            
            count = await Item.update_column(conn, diff_col, id = item.id)
            if diff_col:
                logger.info("Updated item '%s' in the following columns: %s.", item.id, diff_col.keys())
        
        return count
