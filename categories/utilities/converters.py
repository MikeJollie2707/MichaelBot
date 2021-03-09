import discord
from discord.ext import commands

import datetime

import pytimeparse

class IntervalConverter(commands.Converter):
    async def convert(self, ctx, arg : str) -> datetime.timedelta:
        return datetime.timedelta(seconds = pytimeparse.parse(arg))