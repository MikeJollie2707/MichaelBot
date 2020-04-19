import discord
from discord.ext import commands

import asyncio
import random
import datetime

from categories.utilityfun.embedparser import parser

class Utility(commands.Cog, command_attrs = {"cooldown_after_parsing" : True}):
    '''Commands related to utilities and fun.'''
    def __init__(self, bot):
        self.bot = bot
        self.emoji = '😆'

    @commands.command()
    async def ping(self, ctx):
        '''
        Show the latency of the bot.

        **Usage:** <prefix>**{command_name}**
        **Example:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Send Messages`.
        '''

        latency = self.bot.latency

        await ctx.send(str(format((latency * 1000), '.2f')) + "ms")

    @commands.command()
    async def dice(self, ctx):
        '''
        Roll a dice for you.

        **Usage:** <prefix>**{command_name}**
        **Example:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Send Messages`.
        '''

        await ctx.send("It's %d :game_die:" % (random.randint(1, 6)))

    @commands.command()
    @commands.bot_has_permissions(read_message_history = True, add_reactions = True, send_messages = True)
    async def poll(self, ctx, title, *, choices):
        '''
        Make a poll for you right in the current channel.
        Note: the number of options must greater than 1, and at max 10.

        **Usage:** <prefix>**{command_name}** <title> <choice 1 | choice 2 | choice n>
        **Example:** {prefix}{command_name} "What's the most awesome bot in Discord?" MichaelBot | MikeJollie | Some random dude

        **You need:** None.
        **I need:** `Read Message History`, `Add Reactions`, `Send Messages`.
        '''
        
        embed = discord.Embed(
            title = title,
            color = discord.Color.green(),
            timestamp = datetime.datetime.utcnow()
        )

        embed.set_author(
            name = ctx.author.name, 
            icon_url = ctx.author.avatar_url
        )
        embed.set_footer(
            text = f"Created by: {ctx.author.name}",
            icon_url = ctx.author.avatar_url
        )

        # TODO: Make it support near endless options by the format <emoji 1> <option 1> | <emoji 2> <option 2> | ....
        options = choices.split(" | ")
        if len(options) <= 1:
            ctx.send("The option is too low! It must be greater than 1.")
        elif len(options) > 10:
            ctx.send("The option is too high! It must not exceed 10.")
        else:
            emojis = []
            for i in range(1, len(options) + 1):
                emoji = ''
                if i == 1:
                    emoji = '1️⃣'
                elif i == 2:
                    emoji = '2️⃣'
                elif i == 3:
                    emoji = '3️⃣'
                elif i == 4:
                    emoji = '4️⃣'
                elif i == 5:
                    emoji = '5️⃣'
                elif i == 6:
                    emoji = '6️⃣'
                elif i == 7:
                    emoji = '7️⃣'
                elif i == 8:
                    emoji = '8️⃣'
                elif i == 9:
                    emoji = '9️⃣'
                elif i == 10:
                    emoji = '🔟'
                
                embed.add_field(name = emoji, value = options[i - 1])
                emojis.append(emoji)
        
        poll = await ctx.send(embed = embed)
        for i in range (0, len(options)):
            await poll.add_reaction(emojis[i])

    @commands.command()
    async def say(self, ctx, *, content: str):
        '''
        Repeat what you say.

        **Usage:** <prefix>**{command_name}** <message>
        **Example:** {prefix}{command_name} MikeJollie is gay.

        **You need:** None.
        **I need:** `Manage Messages`, `Send Messages`.
        '''

        await ctx.message.delete()
        await ctx.send(content)

    @commands.command()
    async def speak(self, ctx, *, content: str):
        '''
        Make the bot speak!

        **Usage:** <prefix>**{command_name}** <message>
        **Example:** {prefix}{command_name} MikeJollie is gay

        **You need:** None.
        **I need:** `Manage Messages`, `Send TTS Messages`, `Send Messages`.
        '''

        await ctx.message.delete()
        await ctx.send(content, tts = True)

    @commands.command(enabled = True)
    async def calc(self, ctx, *, content: str):
        '''
        A mini calculator that calculate almost everything.
        Note: Trignometry functions return radian.

        **Usage:** <prefix>**{command_name}** <expression>
        **Example 1:** {prefix}{command_name} 1+2
        **Example 2:** {prefix}{command_name} 5*(2 + 3)
        **Example 3:** {prefix}{command_name} sqrt(25)

        **You need:** None.
        **I need:** `Send Messages`.
        '''

        from categories.utilityfun.calc import calculate
        result = calculate(content)

        embed = discord.Embed(color = discord.Color.green())
        embed.add_field(
            name = "**Result:**", 
            value = result
        )

        await ctx.send(embed = embed)

    @commands.command()
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def embed_simple(self, ctx, title : str = "", content : str = '', color : str = "", destination : str = ""):
        '''
        Send a simple embed message.
        Note: You'll respond to 3 questions to set the embed you want.

        **Usage:** <prefix>**{command_name}**
        **Cooldown:** 5 seconds per use (user)
        **Example:** {prefix}{command_name}

        **You need:** None.
        **I need:** `Read Message History`, `Manage Messages`, `Send Messages`.
        '''

        await ctx.message.delete()

        def check(message):
            return message.content != "" and message.content != "Pass"
        
        async def clean(prompt):
            input_list = await ctx.channel.history(limit = 3).flatten()

            for message in input_list:
                if message.id != prompt.id and message.author == ctx.message.author:
                    await message.delete()
                elif message.id == prompt.id:
                    await message.delete()
                    break


        title = ""
        content = ""
        color = discord.Color.default()

        prompt = await ctx.send("What's your title?\n(Example: Ok boomer)")

        try:
            msg1 = await self.bot.wait_for("message", timeout = 60.0, check = check)
            title = "**" + msg1.content + "**"
            await clean(prompt)

            prompt = await ctx.send("What's your content?\n(Example: MikeJollie sucks)")
            msg2 = await self.bot.wait_for("message", timeout = 60.0, check = check)
            content = msg2.content
            await clean(prompt)

            prompt = await ctx.send("What color do you want? You can type a hex number (6-digit number with `0x`prefix) or type these predefined colors: `green`, `default`, `red`, `orange`, `blue`.\n(Example: 0x00ffff)")
            msg3 = await self.bot.wait_for("message", timeout = 60.0, check = check)
            if msg3.content.upper() == 'RED':
                color = discord.Color.red()
            elif msg3.content.upper() == 'GREEN':
                color = discord.Color.green()
            elif msg3.content.upper() == 'BLUE':
                color = discord.Color.blue()
            elif msg3.content.upper() == 'ORANGE':
                color = discord.Color.orange()
            else:
                try:
                    hex_color = int(msg3.content, base = 16)
                    color = discord.Color(value = hex_color)
                except ValueError:
                    await ctx.send("Invalid color number and option.")
                    return
                
        except asyncio.TimeoutError:
            await ctx.send("Process ended due to overtime.")
            return
        
        embed = discord.Embed(
            title = title, 
            description = content, 
            color = color
        )

        await ctx.send(embed = embed)

    @commands.group()
    async def embed(self, ctx, *, inp : str = ""):
        '''
        Send a full-featured rich embed.
        Note: It is recommended to use `embed help` to know more about how to use this command.

        **Usage:** <prefix>**{command_name}** <args>
        **Example 1:** {prefix}{command_name} TITLE This is the title DESCRIPTION description COLOR 111111
        *View `embed help` for more examples*

        **You need:** None.
        **I need:** `Send Messages`.
        '''
        
        if ctx.invoked_subcommand is None:
            embed = discord.Embed.from_dict(parser(inp))
            await ctx.send(embed = embed)
    
    @embed.command()
    async def help(self, ctx):
        pass

    @commands.command()
    @commands.cooldown(5, 10.0, commands.BucketType.user)
    async def howgay(self, ctx, *, target: str):
        '''
        An ultimate measurement of gayness.

        **Usage:** <prefix>**{command_name}** <anything you want to measure>
        **Cooldown:** 10 seconds per 5 uses (user)
        **Example 1:** {prefix}{command_name} MikeJollie
        **Example 2:** {prefix}{command_name} "iPhone 11"

        **You need:** None.
        **I need:** `Send Messages`.
        '''
        
        if target.upper() == "MIKEJOLLIE":
            percent_gay = 0
        elif target.upper() == "STRANGER.COM":
            percent_gay = 100
        else:
            percent_gay = random.randint(0, 100)
        
        if percent_gay == 0:
            await ctx.send(f"Holy moly, the {target} is 100% straight :open_mouth:, zero trace of gayness.")
        else:
            await ctx.send(f"{target} is `{percent_gay}%` gay :rainbow_flag:.")

    @commands.command()
    @commands.cooldown(5, 10.0, commands.BucketType.user)
    async def how(self, ctx, measure_unit : str, *, target : str):
        '''
        An ultimate measurement to measure everything except gayness.

        **Usage:** <prefix>**{command_name}** <something to use to rate> <something to rate>
        **Cooldown:** 10 seconds per 5 uses (user)
        **Example 1:** {prefix}{command_name} smart Stranger.com
        **Example 2:** {prefix}{command_name} "stupidly dumb" "Nightmare monsters"

        **You need:** None.
        **I need:** `Send Messages`.
        '''

        percent_thing = random.randint(0, 100)
        await ctx.send(target + " is `" + str(percent_thing) + "%` " + measure_unit + ".")

    @commands.command(hidden = True)
    @commands.cooldown(1, 120.0, commands.BucketType.user)
    async def send(self, ctx, id : int, *, msg : str):
        '''
        Send a message to either a channel or a user that the bot can see.

        **Usage:** <prefix>**{command_name}** <user ID / channel ID> <content>
        **Cooldown:** 120 seconds per use (user)
        **Example 1:** {prefix}{command_name} 577663051722129427 Gay.
        **Example 2:** {prefix}{command_name} 400983101507108876 All of you are gay.

        **You need:** None.
        **I need:** `Send Messages` at <destination>.
        '''

        target = self.bot.get_user(id)
        if target == None:
            target = self.bot.get_channel(id)
            if target == None:
                await ctx.send("Destination not found.")
                return
        try:
            await target.send(msg)
        except AttributeError:
            await ctx.send("I cannot send message to myself dummy.")
        except discord.Forbidden:
            await ctx.send("It seems like I cannot send message to this place!")
        else:
            await ctx.send("Message sent!", delete_after = 5)

def setup(bot):
    bot.add_cog(Utility(bot))