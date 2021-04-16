import discord
from discord.ext import commands

import asyncio
import typing

class Menu:
    def __init__(self, init_page : discord.Embed, terminate_emoji : str, return_emoji : str):
        """
        Param:
        - `init_page`: The center page.
        - `terminate_emoji`: The stop emoji.
        - `return_emoji`: The return emoji.
        Exception:
        - TypeError: This exception is raised when `init_page` is not a `discord.Embed`.
        """
        self.__pages__ = {} # A dict with the format {emoji: discord.Embed}
        self.__terminator__ = terminate_emoji
        self.__return__ = return_emoji

        if isinstance(init_page, discord.Embed):
            self.__init_page__ = init_page
        else:
            raise TypeError("'init_page' must be discord.Embed.")
    
    def add_page(self, emoji : str, page : discord.Embed):
        """
        Add page to the menu.

        Param:
        - `emoji`: the emoji you want the page to be reacted.
        - `page`: the page you want to add. It must be a `discord.Embed`.

        Exception:
        - `IndexError`: When `emoji` is the same as `terminate_emoji` in the constructor.
        - `TypeError`: When `page` is not a `discord.Embed`.
        """
        if isinstance(page, discord.Embed):
            if emoji != self.__terminator__:
                self.__pages__[emoji] = page
            else:
                raise IndexError("Cannot add page with %s emoji." % emoji)
        else:
            raise TypeError("'page' must be discord.Embed.")
    def add_pages(self, pages : typing.Dict[str, discord.Embed]):
        """
        Add pages to the menu.

        Param:
        - `pages`: A dictionary in the format Dict[str, discord.Embed].

        Exception:
        - `IndexError`: When `emoji` is the same as `terminate_emoji` in the constructor.
        - `TypeError`: When `page` is not a `discord.Embed`.
        """
        for page in pages:
            self.add_page(page["emoji"], page["page"])

    async def event(self, ctx : commands.Context, channel : discord.TextChannel = None, interupt = True):
        """
        This function is a coroutine.

        A function use to interact with the menu.

        Param:
        - `ctx`: The context.
        - `channel`: The channel you want to send the menu in. If none provided, it'll use `ctx.channel`.
        - `interupt`: `False` if you don't want other user to react the menu, `True` otherwise. Default value is `True`.
        
        Exception:
        - `AttributeError`: When the parameter(s) is wrong type.
        - `discord.Forbidden`: When the bot doesn't have permission to send messages/add reactions/read messages history.
        """

        bot = ctx.bot
        channel = ctx.channel if channel is None else channel
        author = ctx.author

        if len(self.__pages__) == 0:
            return
        
        self.__pages__[self.__terminator__] = None

        message = await channel.send(embed = self.__init_page__)
        for emoji in self.__pages__:
            await message.add_reaction(emoji)
        
        available_options = [] # Available reactions that a user can react.
        for key in self.__pages__:
            available_options.append(key)

        def reaction_check(reaction, user):
            return reaction.message.id == message.id and user != message.author
        
        while True:
            try:
                reaction, user = await bot.wait_for("reaction_add", check = reaction_check, timeout = 120.0)
            except asyncio.TimeoutError:
                await message.clear_reactions()
                await message.add_reaction('🕛')

                break
            else:
                if interupt == False:
                    if user == author:
                        if reaction.emoji in available_options:
                            if reaction.emoji == self.__terminator__:
                                await message.edit(content = ":white_check_mark:", embed = None)
                                await message.clear_reactions()
                                break

                            elif reaction.emoji == self.__return__:
                                await message.edit(embed = self.__init_page__)

                                available_options = []
                                for key in self.__pages__:
                                    available_options.append(key)
                                
                            else:
                                available_options = []
                                available_options = self.__return__
                            
                                await message.edit(embed = self.__pages__[reaction.emoji])
                            
                            await message.clear_reactions()
                            for emoji in available_options:
                                await message.add_reaction(emoji)
                            continue
                        #else:
                        #    await message.remove_reaction(reaction, user)
                    #else: # If uncomment then 1 tab the next line
                    await message.remove_reaction(reaction, user)
                else:
                    if reaction.emoji in available_options:
                        if reaction.emoji == self.__terminator__:
                            await message.edit(content = ":white_check_mark:", embed = None)
                            await message.clear_reactions()
                            break

                        elif reaction.emoji == self.__return__:
                            await message.edit(embed = self.__init_page__)

                            available_options = []
                            for key in self.__pages__:
                                available_options.append(key)
                        
                        else:
                            available_options = []
                            available_options = self.__return__

                            await message.edit(embed = self.__pages__[reaction.emoji])
                        
                        await message.clear_reactions()
                        for emoji in available_options:
                            await message.add_reaction(emoji)
                        continue
                    else:
                        await message.remove_reaction(reaction, user)

class Option:
    def __init__(self, options, terminate_emoji = '❌', return_emoji = '🔼'):
        """
        Construct a reaction menu.

        Parameters:
        - `option`: A recursive list(dict) in the following format: `[base_embed, {emote: [embed, {...}], ...}]`.
        - `terminate_emoji`: The emoji used to stop the menu. **IT MUST NOT BE AN EMOJI IN `option`**.
        - `return_emoji`: The emoji used to return to the previous page. **IT MUST NOT BE AN EMOJI IN `option`**.
        """

        self.__base_embed__ = options[0]
        self.__terminate_emoji__ = terminate_emoji
        self.__return_emoji__ = return_emoji

        # This has a recursive format of [embed, {emote: [embed, {...}], ...}]
        self.__dynamic_options__ = options[1]
        # A stack-like list to track the previously available emoji for a certain page.
        self.__previous_options__ = []
        # A stack-like list to track the current embed.
        self.__embeds_route__ = []
    
    async def start(self, ctx, channel = None):
        """
        Start the menu session.

        Parameters:
        - `ctx`: The context.
        - `channel`: Optional destination. By default, it is `ctx.channel`.
        """
        if channel is None:
            channel = ctx.channel
        try:
            message = await channel.send(embed = self.__base_embed__)
            for reaction in self.__dynamic_options__:
                await message.add_reaction(reaction)
            await message.add_reaction(self.__terminate_emoji__)
            self.__embeds_route__.append(self.__base_embed__)
            
            def reaction_check(reaction, user):
                return reaction.message.id == message.id and user.id != message.author.id and user.id == ctx.author.id
            
            while True:
                try:
                    reaction, user = await ctx.bot.wait_for("reaction_add", check = reaction_check, timeout = 120.0)
                except asyncio.TimeoutError:
                    await self._on_timeout__(message)
                    break
                else:
                    # Terminate/return emoji doesn't belong to choice list, so I can have a check here.
                    option = self.__dynamic_options__.get(str(reaction.emoji))
                    if option is not None:
                        if isinstance(option, discord.Embed):
                            await message.edit(embed = option)
                            await message.clear_reactions()
                            await message.add_reaction(self.__return_emoji__)

                            self.__previous_options__.append(self.__dynamic_options__)
                            self.__embeds_route__.append(option)
                            self.__dynamic_options__ = {}
                        elif isinstance(option, list):
                            await message.edit(embed = option[0])

                            await message.clear_reactions()
                            for sub_reactions in option[1]:
                                await message.add_reaction(sub_reactions)
                            await message.add_reaction(self.__return_emoji__)
                            
                            self.__previous_options__.append(self.__dynamic_options__)
                            self.__embeds_route__.append(option[0])
                            self.__dynamic_options__ = option[1]
                    else:
                        # It still needs to check if it's truly the terminate/return emoji or just
                        # some random emote added.

                        # We're at base_embed here.
                        if len(self.__embeds_route__) == 1:
                            if str(reaction.emoji) == self.__terminate_emoji__:
                                await self._on_stop__(message)
                                break
                        
                        if str(reaction.emoji) == self.__return_emoji__:
                            # Pop out the current embed, and display the previous embed.
                            self.__embeds_route__.pop()
                            embed = self.__embeds_route__[-1]
                            await message.edit(embed = embed)
                            
                            # __previous_options__ tracks the option for the previous embed only,
                            # so we need to pop that and add those reactions.
                            await message.clear_reactions()
                            self.__dynamic_options__ = self.__previous_options__.pop()
                            for sub_reactions in self.__dynamic_options__:
                                await message.add_reaction(sub_reactions)
                            

                            if len(self.__embeds_route__) == 1:
                                await message.add_reaction(self.__terminate_emoji__)
                            else:
                                await message.add_reaction(self.__return_emoji__)
        except Exception as e:
            raise e
    
    async def _on_stop__(self, message):
        await message.clear_reactions()
        await message.edit(content = ":white_check_mark:", embed = None)
    async def _on_timeout__(self, message):
        await message.clear_reactions()
        await message.add_reaction('🕛')
