import discord
from discord.ext import commands

import asyncpg

class DB(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @classmethod
    async def init_db(cls, bot):
        # Create DB if it's not established
        pass

    @classmethod
    async def to_dict(cls):
        # Transfer the DB to dictionary
        pass
