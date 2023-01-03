import dataclasses
import typing as t

import asyncpg

from utils.psql._base import *


@dataclasses.dataclass(slots = True)
class LogSetting(BaseSQLObject):
    '''Represent an entry in the `LogSettings` table along with possible operations related to the table.
    
    This table does not offer any creating, updating, or deleting operations because it only serves as a pseudo enum.
    '''
    
    id: int
    name: str

    _tbl_name: t.ClassVar[str] = "LogSettings"
    _PREVENT_UPDATE: t.ClassVar[tuple[str]] = ("id", )

    @classmethod
    async def fetch_all_where(cls, conn: asyncpg.Connection, *, as_dict: bool = False, where: t.Callable[[t.Self], bool] = lambda r: True) -> list[t.Self] | list[dict] | list[None]:
        query = """
            SELECT * FROM LogSettings
            ORDER BY id;
        """

        return await _get_all(conn, query, where = where, result_type = LogSetting if not as_dict else dict)
    @classmethod
    async def fetch_all_setting_names(cls, conn: asyncpg.Connection) -> list[str]:
        '''Fetch all the settings' names.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.

        Returns
        -------
        list[str]
            A list of settings' names.
        '''
        return [setting.name for setting in await LogSetting.fetch_all(conn)]

@dataclasses.dataclass(slots = True)
class GuildLogSetting(BaseSQLObject):
    '''Represent an entry in the table `GuildLogSettings` along with possible operations related to the table.
    
    Generally, you shouldn't use this class directly. It is safer to do so through `GuildLog`.
    '''
    
    guild_id: int
    setting_name: str
    is_enabled: bool = True

    _tbl_name: t.ClassVar[str] = "GuildLogSettings"
    _PREVENT_UPDATE: t.ClassVar[tuple[str]] = ("guild_id", "setting_name")

    @classmethod
    async def fetch_all_where(cls, conn: asyncpg.Connection, *, as_dict: bool = False, where: t.Callable[[t.Self], bool] = lambda r: True) -> list[t.Self] | list[dict] | list[None]:
        query = """
            SELECT * FROM GuildLogSettings;
        """

        return await _get_all(conn, query, where = where, result_type = GuildLogSetting if not as_dict else dict)
    @classmethod
    async def fetch_guild_settings(cls, conn: asyncpg.Connection, guild_id: int, *, as_dict: bool = False) -> list[t.Self] | list[dict]:
        '''Fetch all settings for a guild.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        guild_id : int
            The guild's id.
        as_dict : bool, optional
            Whether the result should be in the `dict` or in `Self`, by default False

        Returns
        -------
        list[t.Self] | list[dict]
            A list of settings for a guild, or empty list if there's no settings.
        '''
        query = """
            SELECT * FROM GuildLogSettings
            WHERE guild_id = ($1);
        """

        return await _get_all(conn, query, result_type = GuildLogSetting if not as_dict else dict)
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
            The attributes to find, such as `id = value`. You must provide the following kw: `guild_id: int`, `setting_name: str`.

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
        _setting_name = kwargs["setting_name"]

        query = """
            SELECT * FROM GuildLogSettings
            WHERE guild_id = ($1) AND setting_name = ($2);
        """
        return await _get_one(conn, query, _guild_id, _setting_name, result_type = GuildLogSetting if not as_dict else dict)
    @classmethod
    async def insert_default(cls, conn: asyncpg.Connection, guild_id: int, default_value: bool = True):
        '''An efficient way to create all default guild's log settings.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        guild_id : int
            The guild's id to create.
        default_value : bool, optional
            The default value for all these settings, by default True.
        '''
        all_settings = await LogSetting.fetch_all_setting_names(conn)
        query = insert_into_query(cls._tbl_name, len(cls.__slots__))
        _entries = [(guild_id, setting, default_value) for setting in all_settings]
        await conn.executemany(query, _entries)
    @classmethod
    async def delete_guild_settings(cls, conn: asyncpg.Connection, guild_id: int) -> int:
        '''Delete all log settings in a guild.

        Generally, the only time to use this function is to clean up the table. To disable logging for a guild,
        update `GuildLog.log_channel` to `None`.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        guild_id : int
            The guild's id.

        Returns
        -------
        int
            The amount of entries deleted.
        '''
        query = """
            DELETE FROM GuildLogSettings
            WHERE guild_id = ($1);
        """
        return await run_and_return_count(conn, query, guild_id)
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
            The attributes to find, such as `id = value`. You must provide the following kw: `guild_id: int`, `setting_name: str`.

        Returns
        -------
        int
            The amount of entries updated.
        
        Raises
        ------
        KeyError
            The needed kw is not present in `**kwargs`.
        '''
        check = await super(GuildLogSetting, cls).update_column(conn, column_value_pair, **kwargs)
        if not check:
            return 0
        
        if len(column_value_pair) < 1:
            return 0
        _guild_id = kwargs["guild_id"]
        _setting_name = kwargs["setting_name"]

        query, index = update_query(GuildLogSetting._tbl_name, column_value_pair.keys())
        query += f"WHERE guild_id = (${index}) AND setting_name = (${index + 1});"
        return await run_and_return_count(conn, query, *(column_value_pair.values()), _guild_id, _setting_name)
    @classmethod
    async def update(cls, conn: asyncpg.Connection, glog_setting: t.Self) -> int:
        '''Update an entry based on the provided object, or insert if it's not found.

        This function calls `fetch_one()` internally, causing an overhead.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        glog_setting : t.Self
            The object to update/insert.

        Returns
        -------
        int
            The number of entries affected.
        '''
        existed_setting = await GuildLogSetting.fetch_one(conn, guild_id = glog_setting.guild_id, setting_name = glog_setting.setting_name)
        if not existed_setting:
            return await GuildLogSetting.insert_one(conn, glog_setting)
        
        diff_col = {}
        for col in existed_setting.__slots__:
            if getattr(existed_setting, col) != getattr(glog_setting, col):
                diff_col[col] = getattr(glog_setting, col)
        
        return await GuildLogSetting.update_column(conn, diff_col, guild_id = glog_setting.guild_id, setting_name = glog_setting.setting_name)
    @classmethod
    async def updatemany(cls, conn: asyncpg.Connection, glog_settings: list[t.Self]) -> None:
        '''Update many setting entries more efficiently.

        This is useful to change all settings for a guild at once, but also can be used for many guilds.
        
        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        glog_settings : list[t.Self]
            A list of setting to update with.
        '''
        if not glog_settings:
            return
        
        prepare_query, index = update_query(cls._tbl_name, ["is_enabled"])
        prepare_query += f"WHERE guild_id = (${index}) AND setting_name = (${index + 1});"

        _args = [(setting.is_enabled, setting.guild_id, setting.setting_name) for setting in glog_settings]
        await conn.executemany(prepare_query, _args)

@dataclasses.dataclass(slots = True)
class GuildLog(BaseSQLObject):
    '''Represent an entry in the table `GuildLogs` along with possible operations related to the table.
    
    Note that `log_settings` is a special attribute; conventional edit functions such as `update_column()` and `update()` will ignore this attribute.
    To update this attribute, use `update_settings()`.
    '''
    guild_id: int
    log_channel: int | None
    
    log_settings: list[GuildLogSetting] = dataclasses.field(default_factory = list)

    _tbl_name: t.ClassVar[str] = "GuildLogs"
    _PREVENT_UPDATE: t.ClassVar[tuple[str]] = ("guild_id", "log_settings")

    @classmethod
    async def fetch_all_where(cls, conn: asyncpg.Connection, *, as_dict: bool = False, where: t.Callable[[t.Self], bool] = lambda r: True) -> list[t.Self] | list[dict] | list[None]:
        '''Fetch all entries in the table that matches the condition.

        Warnings
        --------
        Argument `as_dict` is ignored in this function due to technical complications.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        as_dict : bool, optional
            This parameter is ignored, and only included for overriding purposes.
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
        query = """
            SELECT GuildLogs.guild_id, GuildLogs.log_channel, GuildLogSettings.setting_name, GuildLogSettings.is_enabled FROM GuildLogs
                INNER JOIN GuildLogSettings ON GuildLogSettings.guild_id = GuildLogs.guild_id
            ;
        """
        result = await _get_all(conn, query, where = where, result_type = dict)
        if not result:
            return []
        
        d: dict[int, list[tuple[int, GuildLogSetting]]] = {}
        for res in result:
            if d.get(res["guild_id"]) is None:
                d[res["guild_id"]] = [(res["log_channel"], GuildLogSetting(res["guild_id"], res["setting_name"], res["is_enabled"]))]
            else:
                d[res["guild_id"]].append((res["log_channel"], GuildLogSetting(res["guild_id"], res["setting_name"], res["is_enabled"])))
        
        result = []
        for key, value in d.items():
            result.append(GuildLog(key, value[0][0], [pair[1] for pair in value]))
        return result
    @classmethod
    async def fetch_one(cls, conn: asyncpg.Connection, *, as_dict: bool = False, **kwargs) -> t.Self | dict | None:
        '''Fetch one entry in the table that matches the condition.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        as_dict : bool, optional
            Whether the result should be in the `dict` or in `Self`, by default False
        exclude_settings : bool, optional
            Whether to skip populating `.log_settings` or not, by default `False`. If set to `True`, 
            the return object will have `.log_settings` empty regardless of whether or not it is actually empty. 
            This is useful because fetching the settings requires joining tables.
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
        _exclude_settings = kwargs.get("exclude_settings")

        if _exclude_settings:
            query = """
                SELECT * FROM GuildLogs
                WHERE guild_id = ($1);
            """
        else:
            query = """
                SELECT GuildLogs.guild_id, GuildLogs.log_channel, GuildLogSettings.setting_name, GuildLogSettings.is_enabled FROM GuildLogs
                    INNER JOIN GuildLogSettings ON GuildLogSettings.guild_id = GuildLogs.guild_id
                WHERE GuildLogs.guild_id = ($1);
            """
        result = await _get_all(conn, query, _guild_id, result_type = dict)
        if not result:
            return None
        
        if _exclude_settings:
            return GuildLog(**result[0])
        
        obj = GuildLog(_guild_id, result[0]["log_channel"])
        for res in result:
            obj.log_settings.append(GuildLogSetting(_guild_id, res["setting_name"], res["is_enabled"]))
        return obj
    @classmethod
    async def insert_one(cls, conn: asyncpg.Connection, obj: t.Self) -> int:
        query = insert_into_query(cls._tbl_name, 2)
        async with conn.transaction():
            count = await run_and_return_count(conn, query, obj.guild_id, obj.log_channel)
            # If for some reasons the log settings already existed, instead of throwing exception, we silently terminate and warn about that.
            try:
                await GuildLogSetting.insert_default(conn, obj.guild_id)
            except asyncpg.UniqueViolationError:
                logger.warn(f"Trying to create log settings for {obj.guild_id} after assigning log channel, but settings already existed. No new settings created.")
        return count
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
        '''
        existed_log = await GuildLog.fetch_one(conn, guild_id = obj.guild_id, exclude_settings = True)
        if not existed_log:
            return await GuildLog.insert_one(conn, obj)
        
        diff_col = {}
        for col in existed_log.__slots__:
            if getattr(existed_log, col) != getattr(obj, col):
                diff_col[col] = getattr(obj, col)
        
        return await GuildLog.update_column(conn, diff_col, guild_id = obj.guild_id)
    @classmethod
    async def update_settings(cls, conn: asyncpg.Connection, obj: t.Self):
        '''Update the log settings of a guild.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        obj : t.Self
            The object to update.
        '''
        return await GuildLogSetting.updatemany(conn, obj.log_settings)
    def get_settings_names(self) -> list[str]:
        '''Return all settings' names in this object.

        Returns
        -------
        list[str]
            A list of settings' names.
        '''
        return [setting.setting_name for setting in self.log_settings]
    @property
    def settings_dict_view(self) -> dict[str, bool]:
        '''Return a view on the `.log_settings` attribute.

        Returns
        -------
        dict[str, bool]
            A view on the `.log_settings` attribute with the following format: `{setting_name: is_enabled}`
        '''
        d = {}
        for setting in self.log_settings:
            d[setting.setting_name] = setting.is_enabled
        return d
