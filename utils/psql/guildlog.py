from utils.psql._base import *

@dataclasses.dataclass(slots = True)    
class GuildLog(_BaseSQLObject):
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

    _tbl_name: t.ClassVar[str] = "GuildsLogs"
    _PREVENT_UPDATE: t.ClassVar[tuple[str]] = ("guild_id", )

    @classmethod
    async def fetch_all_where(cls, conn: asyncpg.Connection, *, as_dict: bool = False, where: t.Callable[[t.Self], bool] = lambda r: True) -> list[t.Self] | list[dict] | list[None]:
        query = """
            SELECT * FROM GuildsLogs;
        """
        return await _get_all(conn, query, where = where, result_type = GuildLog if not as_dict else dict)
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
            The attributes to find, such as `id = value`. You must provide the following kw: `guild_id: int`.

        Returns
        -------
        t.Self | dict | None
            Either the object itself or `dict`, depending on `as_dict`. If not existed, `None` is returned.
        
        Raises
        ------
        KeyError
            The needed keyword is not present in `**kwargs`.
        '''

        _guild_id = kwargs["guild_id"]
        query = """
            SELECT * FROM GuildsLogs
            WHERE guild_id = ($1);
        """

        return await _get_one(conn, query, _guild_id, result_type = GuildLog if not as_dict else dict)
    @classmethod
    async def insert_one(cls, conn: asyncpg.Connection, obj_or_id: t.Self | int) -> int:
        '''Insert an entry to the table.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        obj_or_id : GuildLog | int
            The entry to insert, or the id of the guild.

        Returns
        -------
        int
            The amount of entries inserted. Normally, this should be 1.

        Raises
        ------
        TypeError
            `obj` does not inherit from `__BaseSQLObject` and is not type `int`.
        '''

        if isinstance(obj_or_id, type(cls)):
            return await super(GuildLog, cls).insert_one(conn, obj_or_id)
        
        # Only need to insert the guild id.
        query = insert_into_query(GuildLog._tbl_name, 1)
        return await run_and_return_count(conn, query, obj_or_id)
    @classmethod
    async def delete(cls, conn: asyncpg.Connection, **kwargs) -> int:
        '''Delete an entry from the table.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        **kwargs : dict, optional
            The attributes to find, such as `id = value`. You must provide the following kw: `guild_id: int`
        
        Returns
        -------
        int
            The amount of entries deleted.

        Raises
        ------
        KeyError
            The needed keyword is not present in `**kwargs`.
        '''

        _guild_id = kwargs["guild_id"]
        query = """
            DELETE FROM GuildsLogs
            WHERE guild_id = ($1);
        """

        return await run_and_return_count(conn, query, _guild_id)
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
        **kwargs
            The attributes to find, such as `id = value`. You must provide the following kw: `guild_id: int`.

        Returns
        -------
        int
            The amount of entries updated.
        
        Raises
        ------
        KeyError
            The needed kw is not present in `**kwargs`.
        '''

        check = await super(GuildLog, cls).update_column(conn, column_value_pair, **kwargs)
        if not check:
            return 0

        if len(column_value_pair) < 1:
            return 0
        _guild_id = kwargs["guild_id"]

        query, index = update_query(GuildLog._tbl_name, column_value_pair.keys())
        query += f"WHERE guild_id = (${index});"
        return await run_and_return_count(conn, query, *(column_value_pair.values()), _guild_id)
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
        
        existed_guild = await GuildLog.fetch_one(conn, guild_id = guild.guild_id)
        if not existed_guild:
            return await GuildLog.insert_one(conn, guild)
    
        diff_col = {}
        for col in existed_guild.__slots__:
            if getattr(existed_guild, col) != getattr(guild, col):
                diff_col[col] = getattr(guild, col)
        
        return await GuildLog.update_column(conn, diff_col, guild_id = guild.guild_id)
