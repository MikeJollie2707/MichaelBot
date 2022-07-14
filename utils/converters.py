'''Custom argument converters.'''

import datetime

import lightbulb
import pytimeparse

from utils import models, psql

class IntervalConverter(lightbulb.BaseConverter):
    '''A converter to convert a string into a `datetime.timedelta` object.'''
    async def convert(self, arg: str) -> datetime.timedelta:
        return datetime.timedelta(seconds = pytimeparse.parse(arg))

class ItemConverter(lightbulb.BaseConverter):
    '''A converter to convert a string into a `psql.Item` object.'''
    async def convert(self, arg: str) -> psql.Item:
        bot: models.MichaelBot = self.context.bot
        return bot.item_cache.get_by_name(arg)
