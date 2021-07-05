import discord

import asyncio

from discord.ext import commands

# A class that support navigating pages of embeds.

class Pages:
    """
    A paginator that allows using Discord reactions to switch pages in an ordered manner.
    
    By default, there are 5 functionalities:
    - `fast_previous`: Return to page 0.
    - `previous`: Return to previous page if possible.
    - `forward`: Move 1 page forward if possible.
    - `fast_forward`: Move to the last page.
    - `terminate`: Exist the paginator.
    
    You can customize the emojis for each functionality in the constructor.
    To remove a functionality, override `_emoji_list` and override `_on_reaction()`.
    """
    def __init__(self, init_page = 0, **kwargs):
        """
        Construct a paginator.

        Parameters:
        - `init_page`: The starting page index. Default is `0`.
        - `fast_previous`, `previous`, `forward`, `fast_forward`, `terminate`: The respective emoji for each functionality. These are all optionals.
        """
        self.__page_list__ = []
        self._current_page = init_page

        self._FAST_PREVIOUS = kwargs.get("fast_previous") if kwargs.get("fast_previous") is not None else '⏮️'
        self._PREVIOUS = kwargs.get("previous") if kwargs.get("previous") is not None else '◀️'
        self._FORWARD = kwargs.get("forward") if kwargs.get("forward") is not None else '▶️'
        self._FAST_FORWARD = kwargs.get("fast_forward") if kwargs.get("fast_forward") is not None else '⏭️'
        self._TERMINATE = kwargs.get("terminate") if kwargs.get("terminate") is not None else '⏹️'
        self._emoji_list = [self._FAST_PREVIOUS, self._PREVIOUS, self._FORWARD, self._FAST_FORWARD, self._TERMINATE]

    def add_page(self, page : discord.Embed):
        """
        Add a page into the paginator.
        
        Parameter:
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

        A function use to start the paginator.

        Parameter:
        - `ctx`: The context.
        - `message`: The message to bind to. If none provided, a new message will be sent. Otherwise, it'll edit the message.
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
            message = await channel.send(embed = self.__page_list__[self._current_page])
        else:
            await message.edit(embed = self.__page_list__[self._current_page])
        for emoji in self._emoji_list:
            await message.add_reaction(emoji)

        def reaction_check(reaction, user):
            return reaction.message.id == message.id and user != message.author
        
        while True:
            try:
                reaction, user = await bot.wait_for("reaction_add", check = reaction_check, timeout = 120.0)
            except asyncio.TimeoutError:
                self._current_page = -1
                await message.clear_reactions()
                await message.add_reaction('🕛')
                break
            else:
                if interupt or (not interupt and user == author):
                    if reaction.emoji in self._emoji_list:
                        terminate = await self._on_reaction(message, reaction)
                        if terminate:
                            break
                        
                        await message.edit(embed = self.__page_list__[self._current_page])
                await message.remove_reaction(reaction, user)
    
    async def _on_reaction(self, message, reaction) -> bool:
        """
        A method that is called when a reaction is valid (according to `interupt` and author check).
        Override this if you want remove a functionality.

        Parameter:
        - `message`: The message the paginator is belonged to.
        - `reaction`: The reaction.

        Return:
        - `True` if the paginator is reacted with termination, `False` otherwise.
        """
        if reaction.emoji == '⏮️':
            self._current_page = 0
        
        elif reaction.emoji == '◀️':
            if self._current_page != 0:
                self._current_page -= 1

        elif reaction.emoji == '▶️':
            if self._current_page < len(self.__page_list__) - 1:
                self._current_page += 1

        elif reaction.emoji == '⏭️':
            self._current_page = len(self.__page_list__) - 1
            
        elif reaction.emoji == '⏹️':
            self._current_page = -1
            await self._on_terminate(message)    
            return True
        
        return False
    
    async def _on_terminate(self, message):
        """
        A cleanup function when the paginator is terminated.

        Parameter:
        - `message`: The message the paginator is belonged to.
        """
        await message.edit(content = ":white_check_mark:", embed = None)
        await message.clear_reactions()

class MinimalPages(Pages):
    """
    A minimal paginator which only has `forward`, `previous`, and `terminate` functionality.
    It also silently terminate.
    """
    def __init__(self, init_page = 0, **kwargs):
        super().__init__(init_page, **kwargs)

        self._emoji_list = [self._PREVIOUS, self._FORWARD, self._TERMINATE]
    
    async def _on_reaction(self, message, reaction) -> bool:
        if reaction.emoji == self._PREVIOUS:
            if self._current_page != 0:
                self._current_page -= 1
        elif reaction.emoji == self._FORWARD:
            if self._current_page < len(self.__page_list__) - 1:
                self._current_page += 1
        elif reaction.emoji == self._TERMINATE:
            await self._on_terminate(message)
            return True
        
        return False
    
    async def _on_terminate(self, message):
        pass
        
def listpage_generator(max_item, item_list, title_formatter, item_formatter):
    """
    Return a `Pages()` that split the items in the list into different pages.

    Important Parameter:
    - `max_item`: The maximum amount of items per page.
    - `item_list`: List of items to display.
    - `title_formatter`: A callback that accept a single item and return a `discord.Embed`.
    - `item_formatter`: A callback that accept a `discord.Embed` and a single item. Returns nothing.
    """
    page = Pages()
    import utilities.facility as Facility
    embed = None
    for index, item in enumerate(item_list):
        if index % max_item == 0:
            embed = title_formatter(item)

        item_formatter(embed, item)

        if index % max_item == max_item - 1:
            page.add_page(embed)
            embed = None
    if embed is not None:
        page.add_page(embed)
    return page
