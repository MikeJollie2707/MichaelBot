import lightbulb
import hikari

import datetime
import pytimeparse

class IntervalConverter(lightbulb.converters.BaseConverter):
    async def convert(self, arg: str) -> datetime.timedelta:
        return datetime.timedelta(seconds = pytimeparse.parse(arg))
