import lightbulb
import hikari
import aiohttp
import asyncpg
import lavaplayer

import datetime as dt
import logging
import typing as t
from dataclasses import dataclass
from enum import Enum

import utils.psql as psql

class UserCache:
    '''
    Represent a user data in the database.
    
    This contains one module:
    - `user_module`: Represent the `Users` table.
    '''
    def __init__(self, user_module: dict = {}):
        if user_module is None:
            user_module = {}
        else:
            user_module.pop("id", None)
        
        self.user_module = user_module
    
    async def add_user_module(self, conn, user: hikari.User):
        '''
        Add a user into the cache and the database.
        '''
        await psql.Users.add_one(conn, user.id, user.username)
        user_info = await psql.Users.get_one(conn, user.id)
        self.user_module = user_info
    async def update_user_module(self, conn, id: int, column: str, new_value):
        '''
        Edit a user data in the cache and the database.
        '''
        await psql.Users.update_column(conn, id, column, new_value)
        self.user_module[column] = new_value
    
    async def force_sync(self, conn, user_id: int):
        '''
        Force this object to update with database.
        If the method returns `None`, the entry for this user isn't on the database, thus you should use `add_user_module()` instead.
        Otherwise, it returns itself.
        '''

        user = await psql.Users.get_one(conn, user_id)
        if user is None:
            return None
        else:
            user.pop("id", None)
        
        self.user_module = user
        return self

class GuildCache:
    '''
    Represent a guild data in the database.
    
    This contains two module:
    - `guild_module`: Represent the `Guilds` table.
    - `logging_module`: Represent the `GuildsLogs` table.
    '''
    def __init__(self, guild_module: dict = {}, logging_module: dict = {}):
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
        await psql.Guilds.add_one(conn, guild)
        guild_info = await psql.Guilds.get_one(conn, guild.id)
        self.guild_module = guild_info
    
    async def update_guild_module(self, conn, id: int, column: str, new_value):
        '''
        Edit a guild module data in the cache and the database.
        '''
        await psql.Guilds.update_column(conn, id, column, new_value)
        self.guild_module[column] = new_value
    
    async def add_logging_module(self, conn, guild: hikari.Guild):
        '''
        Add a logging module into the cache and the database.
        '''
        await psql.GuildsLogs.add_one(conn, guild)
        logging_info = await psql.GuildsLogs.get_one(conn, guild.id)
        self.logging_module = logging_info
    
    async def update_logging_module(self, conn, id: int, column: str, new_value):
        '''
        Update a logging module in the cache and the database.
        '''
        await psql.GuildsLogs.update_column(conn, id, column, new_value)
        self.logging_module[column] = new_value
    
    async def force_sync(self, conn, guild_id: int):
        '''
        Force this object to update with database.
        If the method returns `None`, the entry for this guild isn't on the database, thus you should use `add_guild_module()` instead.
        Otherwise, it returns itself.
        '''

        guild = await psql.Guilds.get_one(conn, guild_id)
        if guild is None:
            return None
        else:
            guild.pop("id", None)
        
        guild_log = await psql.GuildsLogs.get_one(conn, guild_id)
        if guild_log is None:
            guild_log = {}
        else:
            guild_log.pop("guild_id", None)
        
        self.guild_module = guild
        self.logging_module = guild_log
        return self

# Reference: https://github.com/Rapptz/discord.py/blob/master/discord/colour.py#L164
class DefaultColor(Enum):
    '''
    Store several default colors to use instantly.
    '''

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

@dataclass
class NodeExtra:
    '''A class to store extra data for the `lavaplayer.Node`'''
    queue_loop: bool = False
    working_channel: int = 0

class MichaelBot(lightbulb.BotApp):
    __slots__ = (
        "info", 
        "secrets",
        "online_at",
        "logging",
        "pool",
        "aio_session",
        "guild_cache",
        "user_cache",
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
        A subclass of `lightbulb.BotApp`. This allows syntax highlight on many custom attributes.

        Unique Parameters:
        - `info`: The bot info. Store the one in `config.json`.
        - `secrets`: The bot's secrets such as token, database info, etc.
        '''
        self.info: dict = kwargs.pop("info")
        self.secrets: dict = kwargs.pop("secrets")
        
        self.online_at: dt.datetime = None
        self.logging: logging.Logger = logging.getLogger("MichaelBot")

        self.pool: t.Optional[asyncpg.Pool] = None
        self.aio_session: t.Optional[aiohttp.ClientSession] = None

        # Store some db info. This allows read-only operation much cheaper.
        self.guild_cache: dict[int, GuildCache] = {}
        self.user_cache: dict[int, UserCache] = {}

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
                self.logging.setLevel(logging.DEBUG)
                log_level = "DEBUG"
            elif option in ["--quiet", "-q"]:
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
        '''
        Get the slash command with the given name, or `None` if none was found.

        Unlike the default behavior in `lightbulb.BotApp`, this also searches for subcommands.
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
