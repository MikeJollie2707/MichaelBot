import discord
from discord.ext import commands

import datetime

import pytimeparse
import utilities.db as DB

class IntervalConverter(commands.Converter):
    async def convert(self, ctx, arg : str) -> datetime.timedelta:
        return datetime.timedelta(seconds = pytimeparse.parse(arg))

class ItemConverter(commands.Converter):
    async def convert(self, ctx, arg : str) -> str:
        async with ctx.bot.pool.acquire() as conn:
            arg = arg.lower()
            return await DB.Items.get_internal_name(conn, arg)