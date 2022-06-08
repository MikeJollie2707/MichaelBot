'''Custom argument converters.'''

import datetime

import lightbulb
import pytimeparse

class IntervalConverter(lightbulb.converters.BaseConverter):
    '''A converter to convert a string into a `datetime.timedelta` object.'''
    async def convert(self, arg: str) -> datetime.timedelta:
        return datetime.timedelta(seconds = pytimeparse.parse(arg))
