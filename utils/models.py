'''Contains many data structures, including the customized `MichaelBot` class.'''

import copy
import datetime as dt
import typing as t
from dataclasses import dataclass, field

import aiohttp
import asyncpg
import hikari
import lavaplayer
import lightbulb

from utils import psql


class GuildCache:
    '''A wrapper around `dict[str, psql.Guild]`

    This includes many ways to obtain info, such as `get()`, `keys()`, `items()`, `values()`, and `__getitem__()`.
    These methods will return a deep copy of the desired object, so you can freely edit them.

    Warnings
    --------
    A cache should be used immediately upon fetching. You must periodically refresh the data if you use it in a session-like setting,
    otherwise, two or more cache might exist at the same time, causing some sort of "data race" when updating.
    '''

    def __init__(self) -> None:
        self.__guild_mapping: dict[str, psql.Guild] = {}
    
    def __getitem__(self, guild_id: int):
        return copy.deepcopy(self.__guild_mapping[guild_id])
    def get(self, guild_id: int):
        return copy.deepcopy(self.__guild_mapping.get(guild_id))
    def keys(self):
        return self.__guild_mapping.keys()
    def items(self):
        return self.__guild_mapping.items()
    def values(self):
        return self.__guild_mapping.values()
    
    async def insert(self, conn: asyncpg.Connection, guild: psql.Guild):
        '''Explicitly add a new guild to the cache and to the db.

        This is mostly used to save overheads within `psql.Guild.sync()`

        Warnings
        --------
        Using this method means you're 100% sure the guild doesn't exist. For entries that *might* exist,
        consider using `update_with()`.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        guild : psql.Guild
            The guild to insert.
        '''

        await psql.Guild.insert_one(conn, guild)
        self.__guild_mapping[guild.id] = guild
    async def update(self, conn: asyncpg.Connection, guild: psql.Guild):
        await psql.Guild.update(conn, guild)
        self.__guild_mapping[guild.id] = guild
    async def update_from_db(self, conn: asyncpg.Connection, guild_id: int):
        guild = await psql.Guild.fetch_one(conn, id = guild_id)
        if guild is None:
            del self.__guild_mapping[guild_id]
        
        self.__guild_mapping[guild.id] = guild
    async def update_all_from_db(self, conn: asyncpg.Connection):
        guilds = await psql.Guild.fetch_all(conn)
        
        self.__guild_mapping = {}

        for guild in guilds:
            self.__guild_mapping[guild.id] = guild
    def update_local(self, guild: psql.Guild):
        self.__guild_mapping[guild.id] = guild
    def remove_local(self, guild_id: int):
        del self.__guild_mapping[guild_id]

class LogCache:
    '''A wrapper around `dict[str, psql.GuildLog]`

    This includes many ways to obtain info, such as `get()`, `keys()`, `items()`, `values()`, and `__getitem__()`.
    These methods will return a deep copy of the desired object, so you can freely edit them.

    Warnings
    --------
    A cache should be used immediately upon fetching. You must periodically refresh the data if you use it in a session-like setting,
    otherwise, two or more cache might exist at the same time, causing some sort of "data race" when updating.
    '''

    def __init__(self) -> None:
        self.__log_mapping: dict[str, psql.GuildLog] = {}
    
    def __getitem__(self, guild_id: int):
        return copy.deepcopy(self.__log_mapping[guild_id])
    def get(self, guild_id: int):
        return copy.deepcopy(self.__log_mapping.get(guild_id))
    def keys(self):
        return self.__log_mapping.keys()
    def items(self):
        return self.__log_mapping.items()
    def values(self):
        return self.__log_mapping.values()
    
    async def insert(self, conn: asyncpg.Connection, guild: psql.GuildLog):
        await psql.GuildLog.insert_one(conn, guild)
        self.__log_mapping[guild.guild_id] = guild
    async def update(self, conn: asyncpg.Connection, guild: psql.GuildLog, *, update_settings: bool = True):
        '''Update the database and cache with this object.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        guild : psql.GuildLog
            The object to upsert.
        update_settings : bool, optional
            Whether or not to also update `.log_settings`, by default True. If `False`, this method will ignore `.log_settings`, which can be faster.
        '''
        async with conn.transaction():
            await psql.GuildLog.update_except_settings(conn, guild)
            if update_settings:
                await psql.GuildLog.update_settings(conn, guild)
        self.__log_mapping[guild.guild_id] = guild
    async def update_from_db(self, conn: asyncpg.Connection, guild_id: int):
        guild = await psql.GuildLog.fetch_one(conn, guild_id = guild_id)
        if guild is None:
            del self.__log_mapping[guild_id]
        
        self.__log_mapping[guild.guild_id] = guild
    async def update_all_from_db(self, conn: asyncpg.Connection):
        guilds = await psql.GuildLog.fetch_all(conn)
        
        self.__log_mapping = {}

        for guild in guilds:
            self.__log_mapping[guild.guild_id] = guild
    def update_local(self, guild: psql.GuildLog):
        self.__log_mapping[guild.guild_id] = guild
    def remove_local(self, guild_id: int):
        del self.__log_mapping[guild_id]

class UserCache:
    '''A wrapper around `dict[str, psql.User]`

    This includes many ways to obtain info, such as `get()`, `keys()`, `items()`, `values()`, and `__getitem__()`.
    These methods will return a deep copy of the desired object, so you can freely edit them.

    Warnings
    --------
    A cache should be used immediately upon fetching. You must periodically refresh the data if you use it in a session-like setting,
    otherwise, two or more cache might exist at the same time, causing some sort of "data race" when updating.
    '''

    def __init__(self) -> None:
        self.__user_mapping: dict[int, psql.User] = {}
    
    def __getitem__(self, user_id: int):
        return copy.deepcopy(self.__user_mapping[user_id])
    def get(self, user_id: int):
        return copy.deepcopy(self.__user_mapping.get(user_id))
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
    async def update(self, conn: asyncpg.Connection, user: psql.User):
        '''Sync the database with the new value.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to use.
        user : psql.User
            The user value to update with.
        '''

        await psql.User.update(conn, user)
        self.__user_mapping[user.id] = user
    async def update_from_db(self, conn: asyncpg.Connection, user_id: int):
        user = await psql.User.fetch_one(conn, id = user_id)
        if user is None:
            del self.__user_mapping[user_id]
        
        self.__user_mapping[user.id] = user
    async def update_all_from_db(self, conn: asyncpg.Connection):
        users = await psql.User.fetch_all(conn)
        
        self.__user_mapping = {}
        
        for user in users:
            self.__user_mapping[user.id] = user
    def update_local(self, user: psql.User):
        self.__user_mapping[user.id] = user

class ItemCache:
    '''A wrapper around `dict[str, psql.Item]`

    This includes many ways to obtain info, such as `get()`, `keys()`, `items()`, `values()`, and `__getitem__()`.
    These methods will return a deep copy of the desired object, so you can freely edit them.

    Warnings
    --------
    A cache should be used immediately upon fetching. You must periodically refresh the data if you use it in a session-like setting,
    otherwise, two or more cache might exist at the same time, causing some sort of "data race" when updating.
    '''

    def __init__(self):
        self.__item_mapping: dict[str, psql.Item] = {}
    
    def __getitem__(self, item_id: str) -> psql.Item:
        '''Return a copy of the item matching the item's id.'''

        return copy.deepcopy(self.__item_mapping[item_id])
    def get(self, item_id: str) -> psql.Item | None:
        '''Return a copy of the item matching the item's id, or `None` if none was found.'''

        return copy.deepcopy(self.__item_mapping.get(item_id))
    def get_by_name(self, name_or_alias: str) -> psql.Item | None:
        '''Return a copy of the item matching the item's name or alias, or `None` if none was found.'''

        if self.get(name_or_alias):
            return self.get(name_or_alias)
        
        name = name_or_alias.lower()
        
        for item in self.__item_mapping.values():
            if name == item.name.lower():
                return copy.deepcopy(item)
            if item.aliases and name in [alias.lower() for alias in item.aliases]:
                return copy.deepcopy(item)
        return None
    def keys(self):
        '''Return an iterable of keys inside the underlying `dict`.'''

        return self.__item_mapping.keys()
    def items(self):
        '''Return an iterable of items inside the underlying `dict`.'''

        return self.__item_mapping.items()
    def values(self):
        '''Return an iterable of values inside the underlying `dict`.'''

        return self.__item_mapping.values()

    async def update(self, conn: asyncpg.Connection, item: psql.Item):
        await psql.Item.update(conn, item)
        self.__item_mapping[item.id] = item
    def update_local(self, item: psql.Item):
        '''Set the cache item with the new value.

        This basically sets the internal mapping with the new item.

        Parameters
        ----------
        item : psql.Item
            The item value to update with.
        '''

        self.__item_mapping[item.id] = item

# Reference: https://github.com/Rapptz/discord.py/blob/master/discord/colour.py
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
            if attr in ("get_color", "load", "available_names"):
                continue
            DefaultColor.available_names.append(attr)

    @staticmethod
    def get_color(color: str) -> hikari.Color:
        return getattr(DefaultColor(), color)
    @staticmethod
    def load() -> None:
        '''Load this class. This will make `available_names` available.
        '''
        _ = DefaultColor()

@dataclass
class NodeExtra:
    '''A class to store extra data for the `lavaplayer.Node`'''
    queue_loop: bool = False
    working_channel: int = 0

@dataclass
class CommandActiveSessionManager:
    '''A manager to enforce strict command concurrency.

    In `lightbulb`, if a command is implemented under two or more types of commands, concurrency will apply to those types individually.
    This leads to a scenario where you want to force a command `test` to be 1, but you can bypass by using `$test` and `/test`.
    This class provide a naive container to manage the remaining sessions of the command, regardless of its type.
    
    For command creators, to use this class, simply includes the `checks.strict_concurrency` check on top of `lightbulb.set_max_concurrency()`.
    ```py
    @plugin.command()
    @lightbulb.add_checks(checks.strict_concurrency) # Has to be above `set_max_concurrency()`.
    @lightbulb.set_max_concurrency(uses = 1, bucket = lightbulb.UserBucket)
    @lightbulb.command(...)
    @lightbulb.implements(...)
    async def foo(ctx):
        ...
    ```

    For bot maintainer, only one instance is needed in the bot construction. Acquiring and releasing resources are done in checks and command completion event.
    ```py
    # Before command is invoked.
    if command.max_concurrency:
        bot.command_concurrency_manager.acquire_session(ctx)
    ...
    # After command is finished.
    bot.command_concurrency_manager.release_session(ctx)
    ```
    '''
    # The idea is to create one instance of this in the bot, with `count` containing the max active sessions.
    # Then for each command invocation that has concurrency registered, we decrease count by 1 until it reaches 0.
    # If it reaches 0 and still decrease, we raise error.
    # When the command finish, we increase the count by 1.

    _active_session_mapping: dict[str, dict[int, int]] = field(default_factory = dict)
    _bucket_storing: dict[str, tuple[int, type[lightbulb.Bucket]]] = field(default_factory = dict)

    def _register(self, qualname: str, uses: int, bucket: type[lightbulb.Bucket]) -> None:
        '''Register a command to this manager.

        Parameters
        ----------
        qualname : str
            The command's full name.
        uses : int
            How many uses before the command runs out of its session.
        bucket : t.Type[lightbulb.Bucket]
            The bucket to manage.
        '''
        if uses > 0:
            self._bucket_storing[qualname] = (uses, bucket)
    def command_registered(self, qualname: str) -> bool:
        '''Check if the command is registered to the manager or not.

        Parameters
        ----------
        qualname : str
            The command's full name.

        Returns
        -------
        bool
            Whether the command is registered to the manager or not.
        '''
        return bool(self._bucket_storing.get(qualname))
    def acquire_session(self, ctx: lightbulb.Context) -> None:
        '''Acquire one session under the context provided.

        This session must be released via `CommandActiveSessionManager.release_session()` at some point.
        Otherwise, it'll drain all available sessions of the context.

        Parameters
        ----------
        ctx : lightbulb.Context
            The context to acquire.

        Raises
        ------
        lightbulb.MaxConcurrencyLimitReached
            The command under the context has reached its concurrency limit.
        '''
        command = ctx.command
        qualname = command.qualname
        if not self.command_registered(qualname):
            self._register(command.qualname, command.max_concurrency[0], command.max_concurrency[1])
        
        # Get the discord's id to determine the scope of active command.
        cmd_bucket = self._bucket_storing[qualname]
        session_id = cmd_bucket[1].extract_hash(ctx)
        # If this command has never been invoked then we add it to the map and use 1 session.
        if not self._active_session_mapping.get(qualname):
            self._active_session_mapping[qualname] = {session_id: cmd_bucket[0] - 1}
        else:
            ctx_session = self._active_session_mapping[qualname].get(session_id)
            # If we have no value for the ctx (for some reasons), we add again and take away 1 session.
            if ctx_session is None:
                self._active_session_mapping[qualname] = {session_id: cmd_bucket[0] - 1}
            elif ctx_session <= 0:
                raise lightbulb.MaxConcurrencyLimitReached(f"Maximum concurrency limit for command '{qualname}' exceeded.")
            else:
                self._active_session_mapping[qualname][session_id] -= 1
    def release_session(self, ctx: lightbulb.Context) -> None:
        '''Release one session under the context provided.

        Parameters
        ----------
        ctx : lightbulb.Context
            The context to release.
        '''
        command = ctx.command
        qualname = command.qualname
        if not self.command_registered(qualname):
            return
        
        cmd_bucket = self._bucket_storing[qualname]
        session_id = cmd_bucket[1].extract_hash(ctx)
        if self._active_session_mapping.get(qualname):
            ctx_session = self._active_session_mapping[qualname].get(session_id)
            if ctx_session is not None:
                self._active_session_mapping[qualname][session_id] += 1
    def clear_all_sessions(self) -> None:
        '''Clear all active sessions.
        This should only be used when there's a major error in this manager.
        '''
        self._active_session_mapping = {}

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
        "log_cache",
        "user_cache",
        "item_cache",
        "custom_command_concurrency_session",
        "lavalink",
        "node_extra",
    )
    def __init__(self, 
        token, 
        prefix = None, 
        ignore_bots = True, 
        owner_ids: t.Sequence[int] = (), 
        default_enabled_guilds: int | t.Sequence[int] = (), 
        help_class = None, 
        help_slash_command = False, 
        delete_unbound_commands = True, 
        case_insensitive_prefix_commands = False, 
        **kwargs,
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

        self.pool: asyncpg.Pool | None = None
        self.aio_session: aiohttp.ClientSession | None = None

        # Store some db info. This allows read-only operation much cheaper.
        self.guild_cache = GuildCache()
        self.log_cache = LogCache()
        self.user_cache = UserCache()
        self.item_cache = ItemCache()

        self.custom_command_concurrency_session = CommandActiveSessionManager()

        self.lavalink: lavaplayer.LavalinkClient | None = None
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
        
        DefaultColor.load()

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
    
    def get_slash_command(self, name: str) -> lightbulb.SlashCommand | None:
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

        this: lightbulb.SlashCommandGroup | lightbulb.SlashSubGroup | lightbulb.SlashSubCommand | None = maybe_group
        for part in parts:
            if this is None or isinstance(this, lightbulb.SlashSubCommand):
                return None
            this = this.get_subcommand(part)

        return this
    
    async def reset_cooldown(self, ctx: lightbulb.Context):
        '''A shortcut to reset a command's cooldown.

        Parameters
        ----------
        ctx : lightbulb.Context
            The context the command is invoked.
        '''
        
        if ctx.invoked.cooldown_manager is not None:
            try:
                await ctx.invoked.cooldown_manager.reset_cooldown(ctx)
            except KeyError:
                # The bucket for a user exists, but no cooldown is applied.
                return
