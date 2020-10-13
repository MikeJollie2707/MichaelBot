import discord

import asyncio
import typing

from discord.ext import commands

# A class that support navigating pages of embeds.

class Pages:
    def __init__(self, init_page = 0):
        """
        Param:
        - `init_page`: The starting page index. Default is `0`.
        """
        self.__page_list__ = []
        self.__current_page__ = init_page
        self.__emoji_list__ = ['⏮️', '◀️', '▶️', '⏭️', '⏹️']
    
    def add_page(self, page : discord.Embed):
        """
        Add a page into the paginator.
        Param:
        - `page`: A `discord.Embed`.

        Exception:
        - `TypeError`: When `page` is not `discord.Embed`.
        """
        if isinstance(page, discord.Embed):
            self.__page_list__.append(page)
        else:
            raise TypeError("'page' must be discord.Embed.")
    
    async def event(self, ctx : commands.Context, channel : discord.TextChannel = None, interupt = True):
        """
        This function is a coroutine.

        A function use to interact with the paginator.

        Param:
        - `ctx`: The context.
        - `channel`: The channel you want the pages to be sent. If none provided, it'll use `ctx.channel`.
        - `interupt`: `False` if you don't want other user to react the paginator, `True` otherwise. Default value is `True`.
        
        Exception:
        - `AttributeError`: This exception is raised when the parameter(s) is wrong type.
        - `discord.Forbidden`: When the bot doesn't have permissions to send messages/add reactions/read message history.
        """

        bot = ctx.bot
        channel = ctx.channel if channel is None else channel
        author = ctx.author

        if len(self.__page_list__) == 0:
            return
        
        for num in range(0, len(self.__page_list__)):
            self.__page_list__[num].set_footer(text = "Page %d/%d" % (num + 1, len(self.__page_list__)))

        message = await channel.send(embed = self.__page_list__[self.__current_page__])
        for emoji in self.__emoji_list__:
            await message.add_reaction(emoji)

        def reaction_check(reaction, user):
            return reaction.message.id == message.id and user != message.author
        
        while True:
            try:
                reaction, user = await bot.wait_for("reaction_add", check = reaction_check, timeout = 120.0)
            except asyncio.TimeoutError:
                self.__current_page__ = -1
                await message.clear_reactions()
                await message.add_reaction('🕛')
                break
            else:
                if interupt:
                    if reaction.emoji in self.__emoji_list__:
                        if reaction.emoji == '⏮️':
                            self.__current_page__ = 0
                        
                        elif reaction.emoji == '◀️':
                            if self.__current_page__ != 0:
                                self.__current_page__ -= 1

                        elif reaction.emoji == '▶️':
                            if self.__current_page__ < len(self.__page_list__) - 1:
                                self.__current_page__ += 1

                        elif reaction.emoji == '⏭️':
                            self.__current_page__ = len(self.__page_list__) - 1
                            
                        elif reaction.emoji == '⏹️':
                            self.__current_page__ = -1
                            await message.edit(content = ":white_check_mark:", embed = None)
                            await message.clear_reactions()
                            return
                        
                        await message.edit(embed = self.__page_list__[self.__current_page__])
                    await message.remove_reaction(reaction, user)
                else:
                    if user == author:
                        if reaction.emoji in self.__emoji_list__:
                            if reaction.emoji == '⏮️':
                                self.__current_page__ = 0
                            elif reaction.emoji == '◀️':
                                if self.__current_page__ != 0:
                                    self.__current_page__ -= 1
                            elif reaction.emoji == '▶️':
                                if self.__current_page__ < len(self.__page_list__) - 1:
                                    self.__current_page__ += 1
                            elif reaction.emoji == '⏭️':
                                self.__current_page__ = len(self.__page_list__) - 1
                            elif reaction.emoji == '⏹️':
                                self.__current_page__ = -1
                                await message.edit(content = ":white_check_mark:", embed = None)
                                await message.clear_reactions()
                                return
                            
                            await message.edit(embed = self.__page_list__[self.__current_page__])
                    await message.remove_reaction(reaction, user)