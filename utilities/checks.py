import discord
from discord.ext import commands

def is_dev(ctx):
    return ctx.author.id in [472832990012243969, 462726152377860109, 481934034130174010]
                            #MikeJollie#1067     Stranger.com#4843   MJ2#8267

def has_database(ctx):
    return ctx.bot.pool is not None

