import lightbulb
import hikari

import typing as t
from dataclasses import dataclass

import utilities.psql as psql

class UserCache:
    def __init__(self, user_module: dict = {}):
        if user_module is None:
            user_module = {}
        else:
            user_module.pop("id", None)
        
        self.user_module = user_module
    
    async def add_user_module(self, conn, user: hikari.User):
        await psql.Users.add_one(conn, user.id, user.username)
        user_info = await psql.Users.get_one(conn, user.id)
        self.user_module = user_info
    async def update_user_module(self, conn, id: int, column: str, new_value):
        await psql.Users.update_column(conn, id, column, new_value)
        self.user_module[column] = new_value
    
    async def force_sync(self, conn, user_id: int):
        '''
        Force the cache to update with database.
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
        await psql.Guilds.add_one(conn, guild)
        guild_info = await psql.Guilds.get_one(conn, guild.id)
        self.guild_module = guild_info
    
    async def update_guild_module(self, conn, id: int, column: str, new_value):
        await psql.Guilds.update_column(conn, id, column, new_value)
        self.guild_module[column] = new_value
    
    async def add_logging_module(self, conn, guild: hikari.Guild):
        await psql.Guilds.Logs.add_one(conn, guild)
        logging_info = await psql.Guilds.Logs.get_one(conn, guild.id)
        self.logging_module = logging_info
    
    async def update_logging_module(self, conn, id: int, column: str, new_value):
        await psql.Guilds.Logs.update_column(conn, id, column, new_value)
        self.logging_module[column] = new_value
    
    async def force_sync(self, conn, guild_id: int):
        '''
        Force the cache to update with database.
        If the method returns `None`, the entry for this guild isn't on the database, thus you should use `add_guild_module()` instead.
        Otherwise, it returns itself.
        '''

        guild = await psql.Guilds.get_one(conn, guild_id)
        if guild is None:
            return None
        else:
            guild.pop("id", None)
        
        guild_log = await psql.Guilds.Logs.get_one(conn, guild_id)
        if guild_log is None:
            guild_log = {}
        else:
            guild_log.pop("guild_id", None)
        
        self.guild_module = guild
        self.logging_module = guild_log
        return self

def get_guild_cache(bot: lightbulb.BotApp, guild_id: int) -> t.Optional[GuildCache]:
    '''
    Return a guild's cache.
    This allows you to have IntelliSense all those methods and save some spaces.

    The returned cache is a reference, thus changing it will change the actual cache.
    '''

    return bot.d.guild_cache.get(guild_id)

def get_user_cache(bot: lightbulb.BotApp, user_id: int) -> t.Optional[UserCache]:
    '''
    Return a user's cache.
    This allows you to have IntelliSense all those methods and save some spaces.

    The returned cache is a reference, thus changing it will change the actual cache.
    '''

    return bot.d.user_cache.get(user_id)

# Reference: https://github.com/Rapptz/discord.py/blob/master/discord/colour.py#L164
class DefaultColor:
    '''
    Store several default colors to use instantly.
    '''
    @staticmethod
    def teal(): return hikari.Color(0x1abc9c)

    @staticmethod
    def dark_teal(): return hikari.Color(0x11806a)

    @staticmethod
    def brand_green(): return hikari.Color(0x57F287)

    @staticmethod
    def green(): return hikari.Color(0x2ecc71)

    @staticmethod
    def dark_green(): return hikari.Color(0x1f8b4c)

    @staticmethod
    def blue(): return hikari.Color(0x3498db)

    @staticmethod
    def dark_blue(): return hikari.Color(0x206694)

    @staticmethod
    def purple(): return hikari.Color(0x9b59b6)

    @staticmethod
    def dark_purple(): return hikari.Color(0x71368a)

    @staticmethod
    def magenta(): return hikari.Color(0xe91e63)

    @staticmethod
    def dark_magenta(): return hikari.Color(0xad1457)

    @staticmethod
    def gold(): return hikari.Color(0xf1c40f)

    @staticmethod
    def dark_gold(): return hikari.Color(0xc27c0e)

    @staticmethod
    def orange(): return hikari.Color(0xe67e22)

    @staticmethod
    def dark_orange(): return hikari.Color(0xa84300)

    @staticmethod
    def brand_red(): return hikari.Color(0xED4245)

    @staticmethod
    def red(): return hikari.Color(0xe74c3c)

    @staticmethod
    def dark_red(): return hikari.Color(0x992d22)

    @staticmethod
    def lighter_gray(): return hikari.Color(0x95a5a6)

    @staticmethod
    def dark_gray(): return hikari.Color(0x607d8b)

    @staticmethod
    def light_gray(): return hikari.Color(0x979c9f)

    @staticmethod
    def darker_gray(): return hikari.Color(0x546e7a)

    @staticmethod
    def og_blurple(): return hikari.Color(0x7289da)

    @staticmethod
    def blurple(): return hikari.Color(0x5865F2)

    @staticmethod
    def greyple(): return hikari.Color(0x5865F2)

    @staticmethod
    def dark_theme(): return hikari.Color(0x36393F)

    @staticmethod
    def fuchsia(): return hikari.Color(0xEB459E)

    @staticmethod
    def yellow(): return hikari.Color(0xFEE75C)

@dataclass
class NodeExtra:
    queue_loop: bool = False
    working_channel: int = 0
