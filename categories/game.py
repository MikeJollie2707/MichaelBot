import discord
from discord.ext import commands

import random
import numpy
import typing # IntelliSense purpose only

import utilities.facility as Facility
import utilities.db as DB
from utilities.checks import has_database
from bot import MichaelBot # IntelliSense purpose only

class Game(commands.Cog, command_attrs = {"cooldown_after_parsing" : True}):
    """Commands related to minigames. Most of these also rewards money."""
    def __init__(self, bot : MichaelBot):
        self.bot = bot
        self.emoji = '🎮'
    
    @commands.command()
    async def minesweeper(self, ctx):
        pass
    
    @commands.command()
    async def blackjack(self, ctx):
        pass

    @commands.command()
    @commands.check(has_database)
    @commands.cooldown(rate = 1, per = 5.0, type = commands.BucketType.user)
    async def slots(self, ctx : commands.Context, amount : int = 50):
        # First, we have this set of items, with some of them repeat.
        # For the first rotation, we get a random subset of 3 in the list.
        # We then save the 2ND item of that SUBLIST to cache or sth.
        # 1. Shuffle the default list.
        # 2. For 2nd, we roll a dice of 3 each.
        # 3. If it's 1, then the subset of the 2nd MUST have its 2ND item as the cached item.
        # Go back to 1 for the 3rd list.
        # This way, a player has a 1/9 chance to win, 1/108 chance to jackpot and 1/108 chance to trigger bomb.

        default_slot = numpy.array(('🍎', '🍇', '💣', '💲', '🍟', '🍜', '🎰', '🍎', '🍇', '💲', '🍟', '🍜'))
        rng = numpy.random.default_rng()
        
        # Get random subset of 3 in the list.
        slice = random.randint(0, len(default_slot) - 1)
        new_slot = numpy.append(default_slot[slice:], default_slot[:slice])

        # Get and save the 2ND item of the sublist
        first_rotation = new_slot[:3]
        cached_item = first_rotation[1]

        rng.shuffle(default_slot)
        dice = random.randint(0, 3)
        
        # If dice is 1, then the 2nd item of the sublist must be the cached item.
        if dice == 1:
            for i in range(-1, len(default_slot) - 2):
                if default_slot[i + 1] == cached_item:
                    slice = i
                    break
        else:
            slice = random.randint(0, len(default_slot) - 1)
        
        new_slot = numpy.append(default_slot[slice:], default_slot[:slice])
        second_rotation = new_slot[:3]

        rng.shuffle(default_slot)
        dice = random.randint(0, 3)
        if dice == 1:
            for i in range(-1, len(default_slot) - 2):
                if default_slot[i + 1] == cached_item:
                    slice = i
                    break
        else:
            slice = random.randint(0, len(default_slot) - 1)
        
        new_slot = numpy.append(default_slot[slice:], default_slot[:slice])
        third_rotation = new_slot[:3]

        displays = numpy.array([
            first_rotation,
            second_rotation,
            third_rotation
        ]).transpose()

        msg = "And the result is...\n"
        for i in range(0, 3):
            for j in range(0, 3):
                msg += displays[i][j]
            if i == 1:
                msg += '⬅'
            
            msg += '\n'

        if displays[1][0] == displays[1][1] and displays[1][1] == displays[1][2]:
            if cached_item == '🎰':
                msg += "You hit the jackpot!"
            elif cached_item == '💣':
                msg += "You hit the bomb! Oh No!"
            else:
                msg += "You win!"
        else:
            msg += "You lose!"

        msg += '\n\n'
        
        reward = amount
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                if "jackpot" in msg:
                    reward *= 3
                    reward += amount
                elif "bomb" in msg:
                    reward = -(reward * 3)
                elif "win" in msg:
                    reward *= 1
                    reward += amount
                elif "lose" in msg:
                    reward = -reward
                
                money = await DB.User.get_money(conn, ctx.author.id)
                await DB.User.update_money(conn, ctx.author.id, money + reward)
        
        if "lose" in msg or "bomb" in msg:
            msg += f"Better luck next time :thumbsup:."
        else:
            msg += f"You receive **${abs(reward)}**, and you got to keep the bet amount :)."
        
        await ctx.reply(msg, mention_author = False)


        
def setup(bot : MichaelBot):
    bot.add_cog(Game(bot))
