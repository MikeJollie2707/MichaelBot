import discord
from discord.ext import commands

import asyncio
import typing

from templates.navigate import MinimalPages

class Option:
    def __init__(self, options, terminate_emoji = '❌', return_emoji = '🔼'):
        """
        Construct a reaction menu.

        Parameters:
        - `option`: A recursive list(dict) in the following format: `[base_embed, {emote: [embed, {...}], ...}]`.
            - To include paginator into the menu, the list (not the base list) must be all `discord.Embed` instead of another `dict`.
        - `terminate_emoji`: The emoji used to stop the menu. **IT MUST NOT BE AN EMOJI IN `option`**.
        - `return_emoji`: The emoji used to return to the previous page. **IT MUST NOT BE AN EMOJI IN `option`**.
        """

        self.__base_embed__ = options[0]
        self.__terminate_emoji__ = terminate_emoji
        self.__return_emoji__ = return_emoji

        # Track all current reactions except the terminate and return one.
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
                        # Deadend MenuPage.
                        if isinstance(option, discord.Embed):
                            await message.edit(embed = option)
                            await message.clear_reactions()
                            await message.add_reaction(self.__return_emoji__)

                            self.__previous_options__.append(self.__dynamic_options__)
                            self.__embeds_route__.append(option)
                            self.__dynamic_options__ = {}
                        # Either another submenu, or a list of pages.
                        elif isinstance(option, list):
                            await message.edit(embed = option[0])

                            await message.clear_reactions()
                            # Submenu
                            if isinstance(option[1], dict):
                                for sub_reactions in option[1]:
                                    await message.add_reaction(sub_reactions)

                                await message.add_reaction(self.__return_emoji__)
                                
                                self.__previous_options__.append(self.__dynamic_options__)
                                self.__embeds_route__.append(option[0])
                                self.__dynamic_options__ = option[1]
                            # List of pages, deadend
                            elif isinstance(option[1], discord.Embed):
                                # We want the terminate to be menu's return emoji to be consistent.
                                subpages = MinimalPages(previous = '◀️', forward = '▶️', terminate = self.__return_emoji__)
                                for page in option:
                                    subpages.add_page(page)

                                # The whole thing is just one big deadend, so this part here will look like deadend embed part.
                                self.__previous_options__.append(self.__dynamic_options__)
                                self.__embeds_route__.append(option[0])
                                self.__dynamic_options__ = {}

                                await subpages.start(ctx, message = message)
                                # We "return" from the deadend embed, so go back.
                                await self._on_return(message)
                    else:
                        # It still needs to check if it's truly the terminate/return emoji or just
                        # some random emote added.

                        # We're at base_embed here.
                        if len(self.__embeds_route__) == 1:
                            if str(reaction.emoji) == self.__terminate_emoji__:
                                await self._on_stop__(message)
                                break
                        
                        if str(reaction.emoji) == self.__return_emoji__:
                            await self._on_return(message)
        except Exception as e:
            raise e
    
    async def _on_return(self, message):
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
    async def _on_stop__(self, message):
        await message.clear_reactions()
        await message.edit(content = ":white_check_mark:", embed = None)
    async def _on_timeout__(self, message):
        await message.clear_reactions()
        await message.add_reaction('🕛')


