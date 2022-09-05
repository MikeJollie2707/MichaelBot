'''Custom argument converters.'''

import datetime

import lightbulb
import pytimeparse

from utils import models, psql

class IntervalConverter(lightbulb.BaseConverter):
    '''A converter to convert a string into a `datetime.timedelta` object.'''
    async def convert(self, arg: str) -> datetime.timedelta:
        if (s := pytimeparse.parse(arg)):
            return datetime.timedelta(seconds = s)
        
        raise TypeError(f"'{arg}' cannot be parsed as a time expression.")

class ItemConverter(lightbulb.BaseConverter):
    '''A converter to convert a string into a `psql.Item` object.'''
    async def convert(self, arg: str) -> psql.Item:
        bot: models.MichaelBot = self.context.bot
        return bot.item_cache.get_by_name(arg)
