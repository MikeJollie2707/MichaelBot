import discord

import asyncio

from discord.ext import commands

# A class that support navigating pages of embeds.

class Pages:
    def __init__(self, init_page = 0, **kwargs):
        """
        Param:
        - `init_page`: The starting page index. Default is `0`.
        """
        self.__page_list__ = []
        self.__current_page__ = init_page

        self._FAST_PREVIOUS = kwargs.get("fast_previous")
        self._PREVIOUS = kwargs.get("previous")
        self._FORWARD = kwargs.get("forward")
        self._FAST_FORWARD = kwargs.get("fast_forward")
        self._TERMINATE = kwargs.get("terminate")
        self.__emoji_list__ = [self._FAST_PREVIOUS, self._PREVIOUS, self._FORWARD, self._FAST_FORWARD, self._TERMINATE]

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
    
    async def start(self, ctx : commands.Context, message : discord.Message = None, channel : discord.TextChannel = None, interupt = False):
        """
        This function is a coroutine.

        A function use to interact with the paginator.

        Param:
        - `ctx`: The context.
        - `channel`: The channel you want the pages to be sent. If none provided, it'll use `ctx.channel`.
        - `interupt`: `False` if you don't want other user to react the paginator, `True` otherwise. Default value is `False`.
        
        Exception:
        - `AttributeError`: This exception is raised when the parameter(s) is wrong type.
        - `discord.Forbidden`: When the bot doesn't have permissions to send messages/add reactions/read message history.
        """

        bot = ctx.bot
        channel = ctx.channel if channel is None else channel
        author = ctx.author

        if len(self.__page_list__) == 0:
            return
        
        if len(self.__page_list__) == 1:
            await ctx.channel.send(embed = self.__page_list__[0])
            return
        
        for num in range(0, len(self.__page_list__)):
            self.__page_list__[num].set_footer(text = "Page %d/%d" % (num + 1, len(self.__page_list__)))

        if message is None:
            message = await channel.send(embed = self.__page_list__[self.__current_page__])
        else:
            await message.edit(embed = self.__page_list__[self.__current_page__])
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
                if interupt or (not interupt and user == author):
                    if reaction.emoji in self.__emoji_list__:
                        terminate = await self._on_reaction(message, reaction)
                        if terminate:
                            break
                        
                        await message.edit(embed = self.__page_list__[self.__current_page__])
                await message.remove_reaction(reaction, user)
    
    async def _on_reaction(self, message, reaction) -> bool:
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
            await self._on_terminate(message)    
            return True
        
        return False
    
    async def _on_terminate(self, message):
        await message.edit(content = ":white_check_mark:", embed = None)
        await message.clear_reactions()

class MinimalPages(Pages):
    def __init__(self, init_page = 0, **kwargs):
        super().__init__(init_page, **kwargs)

        self.__emoji_list__ = [self._PREVIOUS, self._FORWARD, self._TERMINATE]
    
    async def _on_reaction(self, message, reaction) -> bool:
        if reaction.emoji == self._PREVIOUS:
            if self.__current_page__ != 0:
                self.__current_page__ -= 1
        elif reaction.emoji == self._FORWARD:
            if self.__current_page__ < len(self.__page_list__) - 1:
                self.__current_page__ += 1
        elif reaction.emoji == self._TERMINATE:
            await self._on_terminate(message)
            return True
        
        return False
    
    async def _on_terminate(self, message):
        await message.edit(content = ":white_check_mark:", embed = None)
        await message.clear_reactions()
