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
                await message.edit(content = ":clock12:", embed = None)
                await message.clear_reactions()

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