'''Contains many data structures, including the customized `MichaelBot` class.'''

import datetime as dt
import typing as t
from dataclasses import dataclass

import aiohttp
import asyncpg
import hikari
import lavaplayer
import lightbulb

from utils import psql

class GuildCache:
    '''
    Represent a guild data in the database.
    
    This contains two module:
    
    - `guild_module`: Represent the `Guilds` table.
    - `logging_module`: Represent the `GuildsLogs` table.
    '''
    def __init__(self, guild_module: dict = None, logging_module: dict = None):
        if guild_module is None:
            guild_module = {}
        else:
            guild_module.pop("id", None)
        
        if logging_module is None:
            logging_module = {}
        else:
            logging_module.pop("guild_id", None)
        
        self.guild_module = guild_module
        self.logging_module = logging_module
    
    async def add_guild_module(self, conn, guild: hikari.Guild):
        '''
        Add a guild module into the cache and the database.
        '''
        #await psql.Guilds._insert_one(conn, guild)
        await psql.Guild.insert_one(conn, psql.Guild(guild.id, guild.name))
        guild_info = await psql.Guild.get_one(conn, guild.id, as_dict = True)
        self.guild_module = guild_info
    
    async def update_guild_module(self, conn, guild_id: int, column: str, new_value):
        '''
        Edit a guild module data in the cache and the database.
        '''
        await psql.Guild.update_column(conn, guild_id, column, new_value)
        self.guild_module[column] = new_value
    
    async def add_logging_module(self, conn, guild: hikari.Guild):
        '''
        Add a logging module into the cache and the database.
        '''
        await psql.GuildsLogs.insert_one(conn, guild.id)
        logging_info = await psql.GuildsLogs.get_one(conn, guild.id, as_dict = True)
        self.logging_module = logging_info
    
    async def update_logging_module(self, conn, guild_id: int, column: str, new_value):
        '''
        Update a logging module in the cache and the database.
        '''
        await psql.GuildsLogs.update_column(conn, guild_id, column, new_value)
        self.logging_module[column] = new_value
    
    async def force_sync(self, conn, guild_id: int):
        '''
        Force this object to update with database.
        If the method returns `None`, the entry for this guild isn't on the database, thus you should use `add_guild_module()` instead.
        Otherwise, it returns itself.
        '''

        guild = await psql.Guild.get_one(conn, guild_id, as_dict = True)
        if guild is None:
            return None
        else:
            guild.pop("id", None)
        
        guild_log = await psql.GuildsLogs.get_one(conn, guild_id, as_dict = True)
        if guild_log is None:
            guild_log = {}
        else:
            guild_log.pop("guild_id", None)
        
        self.guild_module = guild
        self.logging_module = guild_log
        return self

class UserCache:
    def __init__(self) -> None:
        self.__user_mapping: dict[str, psql.User] = {}
    
    def __getitem__(self, user_id: int):
        return self.__user_mapping[user_id]
    def get(self, user_id: int):
        return self.__user_mapping.get(user_id)
    def keys(self):
        return self.__user_mapping.keys()
    def items(self):
        return self.__user_mapping.items()
    def values(self):
        return self.__user_mapping.values()
    
    async def insert(self, conn: asyncpg.Connection, user: psql.User):
        '''Explicitly add a new user to the cache and to the db.

        This is mostly used to save overheads within `psql.User.sync()`

        Warnings
        --------
        Using this method means you're 100% sure the user doesn't exist. For entries that *might* exist,
        consider using `sync_user()`.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        user : psql.User
            The user to insert.
        '''

        await psql.User.insert_one(conn, user)
        self.__user_mapping[user.id] = user
    async def sync_user(self, conn: asyncpg.Connection, user: psql.User):
        '''Sync the database with the new value.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        user : psql.User
            The user value to update with.
        '''

        await psql.User.sync(conn, user)
        self.__user_mapping[user.id] = user
    async def sync_from_db(self, conn: asyncpg.Connection, user_id: int):
        user = await psql.User.get_one(conn, user_id)
        if user is None:
            del self.__user_mapping[user_id]
        
        self.__user_mapping[user.id] = user
    def local_sync(self, user: psql.User):
        self.__user_mapping[user.id] = user

class ItemCache:
    '''A wrapper around `dict[str, psql.Item]`
    
    This includes many ways to obtain info, such as `get()`, `keys()`, `items()`, `values()`, and `__getitem__()`.
    
    To edit the cache, use either `sync_item()` (update db with new values) or `local_sync()` (update the local cache with new values).
    '''
    def __init__(self):
        self.__item_mapping: dict[str, psql.Item] = {}
    
    def __getitem__(self, item_id: str):
        return self.__item_mapping[item_id]
    def get(self, item_id: str):
        return self.__item_mapping.get(item_id)
    def keys(self):
        return self.__item_mapping.keys()
    def items(self):
        return self.__item_mapping.items()
    def values(self):
        return self.__item_mapping.values()

    async def sync_item(self, conn: asyncpg.Connection, item: psql.Item):
        '''Sync the database with the new value.

        This is basically a call to `psql.Item.sync()`.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        item : psql.Item
            The item value to update with.
        '''

        await psql.Item.sync(conn, item)
        self.__item_mapping[item.id] = item
    def local_sync(self, item: psql.Item):
        '''Set the cache item with the new value.

        This basically sets the internal mapping with the new item.

        Parameters
        ----------
        item : psql.Item
            The item value to update with.
        '''

        self.__item_mapping[item.id] = item

# Reference: https://github.com/Rapptz/discord.py/blob/master/discord/colour.py#L164
@dataclass(frozen = True)
class DefaultColor:
    '''Store several default colors to use instantly.'''
    
    teal = hikari.Color(0x1abc9c)
    dark_teal = hikari.Color(0x11806a)
    brand_green = hikari.Color(0x57F287)
    green = hikari.Color(0x2ecc71)
    dark_green = hikari.Color(0x1f8b4c)
    blue = hikari.Color(0x3498db)
    dark_blue = hikari.Color(0x206694)
    purple = hikari.Color(0x9b59b6)
    dark_purple = hikari.Color(0x71368a)
    magenta = hikari.Color(0xe91e63)
    dark_magenta = hikari.Color(0xad1457)
    gold = hikari.Color(0xf1c40f)
    dark_gold = hikari.Color(0xc27c0e)
    orange = hikari.Color(0xe67e22)
    dark_orange = hikari.Color(0xa84300)
    brand_red = hikari.Color(0xED4245)
    red = hikari.Color(0xe74c3c)
    dark_red = hikari.Color(0x992d22)
    lighter_gray = hikari.Color(0x95a5a6)
    dark_gray = hikari.Color(0x607d8b)
    light_gray = hikari.Color(0x979c9f)
    darker_gray = hikari.Color(0x546e7a)
    og_blurple = hikari.Color(0x7289da)
    blurple = hikari.Color(0x5865F2)
    greyple = hikari.Color(0x5865F2)
    dark_theme = hikari.Color(0x36393F)
    fuchsia = hikari.Color(0xEB459E)
    yellow = hikari.Color(0xFEE75C)
    black = hikari.Color(0x000000)
    white = hikari.Color(0xFFFFFF)
    
    available_names = []

    def __init__(self):
        if DefaultColor.available_names:
            return
        
        for attr in DefaultColor.__dict__:
            if attr.startswith("__"):
                continue
            if attr in ("get_color", "available_names"):
                continue
            DefaultColor.available_names.append(attr)

    @staticmethod
    def get_color(color: str):
        return getattr(DefaultColor(), color)

@dataclass
class NodeExtra:
    '''A class to store extra data for the `lavaplayer.Node`'''
    queue_loop: bool = False
    working_channel: int = 0

class MichaelBot(lightbulb.BotApp):
    '''A subclass of `lightbulb.BotApp`. This allows syntax highlight on many custom attributes.'''

    __slots__ = (
        "info", 
        "secrets",
        "online_at",
        "logging",
        "pool",
        "aio_session",
        "guild_cache",
        "user_cache",
        "item_cache",
        "lavalink",
        "node_extra"
    )
    def __init__(self, 
        token, 
        prefix = None, 
        ignore_bots = True, 
        owner_ids: t.Sequence[int] = (), 
        default_enabled_guilds: t.Union[int, t.Sequence[int]] = (), 
        help_class = None, 
        help_slash_command = False, 
        delete_unbound_commands = True, 
        case_insensitive_prefix_commands = False, 
        **kwargs
    ) -> None:
        '''
        Parameters
        -----------------
        info : dict
            The bot info. Store the one in `config.json`.
        secrets : dict
            The bot's secrets such as token, database info, etc.
        '''
        self.info: dict = kwargs.pop("info")
        self.secrets: dict = kwargs.pop("secrets")
        
        self.online_at: dt.datetime = None

        self.pool: t.Optional[asyncpg.Pool] = None
        self.aio_session: t.Optional[aiohttp.ClientSession] = None

        # Store some db info. This allows read-only operation much cheaper.
        self.guild_cache: dict[int, GuildCache] = {}
        self.user_cache = UserCache()
        self.item_cache = ItemCache()

        self.lavalink: t.Optional[lavaplayer.LavalinkClient] = None
        # Currently lavaplayer doesn't support adding attr to lavaplayer.objects.Node
        # so we'll make a dictionary to manually track additional info.
        self.node_extra: dict[int, NodeExtra] = {}

        launch_options = self.info.get("launch_options")
        log_level = "INFO"
        if launch_options is None:
            launch_options = ""
        for option in launch_options.split():
            if option in ["--debug", "-d"]:
                default_enabled_guilds = self.info["default_guilds"]
                log_level = "DEBUG"
            if option in ["--quiet", "-q"]:
                log_level = ""
        
        super().__init__(
            token,
            prefix,
            ignore_bots,
            owner_ids,
            default_enabled_guilds,
            help_class,
            help_slash_command,
            delete_unbound_commands,
            case_insensitive_prefix_commands,
            logs = log_level if bool(log_level) else None,
            **kwargs
        )
    
    def get_slash_command(self, name: str) -> t.Optional[lightbulb.SlashCommand]:
        '''Get the slash command with the given name, or `None` if none was found.

        Unlike the default behavior in `lightbulb.BotApp`, this also searches for subcommands.

        Parameters
        ----------
        name : str
            The command name to search.

        Returns
        -------
        t.Optional[lightbulb.SlashCommand]
            The slash command with that name, or `None` if none was found.
        '''
        # Reference: https://hikari-lightbulb.readthedocs.io/en/latest/_modules/lightbulb/app.html#BotApp.get_prefix_command
        
        parts = name.split()
        if len(parts) == 1:
            return self._slash_commands.get(name)

        maybe_group = self._slash_commands.get(parts.pop(0))
        if not isinstance(maybe_group, lightbulb.SlashCommandGroup):
            return None

        this: t.Optional[
            t.Union[
                lightbulb.SlashCommandGroup, lightbulb.SlashSubGroup, lightbulb.SlashSubCommand
            ]
        ] = maybe_group
        for part in parts:
            if this is None or isinstance(this, lightbulb.SlashSubCommand):
                return None
            this = this.get_subcommand(part)

        return this
