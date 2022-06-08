#pylint: disable=protected-access

# Reference: https://github.com/tandemdude/hikari-lightbulb/blob/development/lightbulb/utils/nav.py

# For self-typing. Not sure why this is not part of Python.
from __future__ import annotations

import asyncio
import typing as t

import hikari
import lightbulb
# Default callback functions
from lightbulb.utils.nav import *

from utils import helpers

T = t.TypeVar("T")

__default_emojis__ = {
    "first_page": helpers.get_emote(":last_track_button:"),
    "prev_page": helpers.get_emote(":arrow_backward:"),
    "next_page": helpers.get_emote(":arrow_forward:"),
    "last_page": helpers.get_emote(":next_track_button:"),
    "terminate": helpers.get_emote(":stop_button:"),
    "timeout": helpers.get_emote(":clock12:"),
    "success": helpers.get_emote(":white_check_mark:"),
    "return": helpers.get_emote(":arrow_up_small:"),
}

# In lightbulb, when each buttons are pressed, they call a hidden callback (stop as `stop()`, etc.)
# When subclass the default navigators/menus, these buttons will call those hidden callback.
# The problem with the default `stop` behavior is it deletes the message regardless, which is pretty bad ._.
# So we need a stop function that essentially calls the "destructor" of the navigators/menus to make it do whatever it wants.
async def __cleanup_stop__(nav: t.Union[ReactionPages, ButtonPages], _: hikari.Event) -> None:
    """
    As opposed to the default behavior, this stop will call the Navigator's destructor (which is `_on_stop()`) instead of deleting message.
    """

    assert nav._msg is not None
    await nav._remove_listener()
    await nav._on_stop()
    nav._msg = None
    if nav._timeout_task is not None:
        nav._timeout_task.cancel()

# Since the default class design kinda sucks (no way to do any cleanup), we're adding 2 methods:
# - `_on_timeout()` will be called when the class timeout.
# - `_on_stop()` will be called when it gracefully close.
# This also means I need to rewrite `_timeout_coro()` to include `_on_timeout()` call, `create_default_button()` to include new `__cleanup_stop__()`.
# There might be a need to rewrite `run()` since you might want some different initial behavior. These often are very specific so I don't have a definite method for it.

class ReactionPages(ReactionNavigator):
    def __init__(self, pages: t.Sequence[hikari.Embed], *, buttons: t.Optional[t.Sequence[ReactionButton]] = None, original_message: t.Optional[hikari.Message] = None, timeout: float = 120) -> None:
        super().__init__(pages, buttons=buttons, timeout=timeout)
        self._msg = original_message

        for index, embed in enumerate(self.pages):
            embed.set_footer(text = "Page %d/%d" % (index + 1, len(self.pages)))
    
    def create_default_buttons(self) -> t.List[ReactionButton]:
        buttons = [
            ReactionButton(__default_emojis__["first_page"], first_page),
            ReactionButton(__default_emojis__["prev_page"], prev_page),
            ReactionButton(__default_emojis__["next_page"], next_page),
            ReactionButton(__default_emojis__["last_page"], last_page),
            ReactionButton(__default_emojis__["terminate"], __cleanup_stop__),
        ]
        return buttons

    async def _timeout_coro(self) -> None:
        try:
            await asyncio.sleep(self._timeout)
            await self._remove_listener()
            await self._on_timeout()
        except asyncio.CancelledError:
            pass
    
    async def run(self, context: lightbulb.Context) -> None:
        intent_to_check_for = (
            hikari.Intents.GUILD_MESSAGE_REACTIONS
            if context.guild_id is not None
            else hikari.Intents.DM_MESSAGE_REACTIONS
        )
        if not (context.app.intents & intent_to_check_for) == intent_to_check_for:
            raise hikari.MissingIntentError(intent_to_check_for)

        self._context = context
        context.app.subscribe(hikari.ReactionAddEvent, self._process_reaction_add)
        if self._msg is None:
            self._msg = await self._send_initial_msg(self.pages[self.current_page_index])
        else:
            await self._msg.edit(self.pages[self.current_page_index])
        for button in self.buttons:
            await self._msg.add_reaction(button.emoji)

        if self._timeout_task is not None:
            self._timeout_task.cancel()
        self._timeout_task = asyncio.create_task(self._timeout_coro())
    
    async def _on_timeout(self):
        await self._msg.add_reaction(__default_emojis__["timeout"])
    async def _on_stop(self):
        await self._msg.edit(__default_emojis__["success"], embeds = None)

class MiniReactionPages(ReactionPages):
    def __init__(self, pages: t.Sequence[hikari.Embed], *, original_message : t.Optional[hikari.Message] = None, terminator : t.Optional[str] = None, timeout: float = 120) -> None:
        if terminator is not None:
            super().__init__(pages, buttons = self.create_default_buttons() + [ReactionButton(terminator, __cleanup_stop__)], original_message = original_message, timeout = timeout)
        else:
            super().__init__(pages, original_message = original_message, timeout = timeout)
    
    def create_default_buttons(self) -> t.List[ReactionButton]:
        buttons = [
            ReactionButton(__default_emojis__["prev_page"], prev_page),
            ReactionButton(__default_emojis__["next_page"], next_page),
        ]
        return buttons
    
    async def _on_stop(self):
        await self._msg.remove_all_reactions()

class ButtonPages(ButtonNavigator):
    def __init__(self, pages: t.Sequence[hikari.Embed], *, buttons: t.Optional[t.Sequence[ComponentButton]] = None, original_message: t.Optional[hikari.Message] = None, timeout: float = 120) -> None:
        super().__init__(pages, buttons=buttons, timeout=timeout)
        self._msg = original_message

        for index, embed in enumerate(self.pages):
            embed.set_footer(text = "Page %d/%d" % (index + 1, len(self.pages)))
    
    def create_default_buttons(self) -> t.Sequence[ComponentButton]:
        buttons = [
            ComponentButton(__default_emojis__["first_page"], True, hikari.ButtonStyle.PRIMARY, "first_page", first_page),
            ComponentButton(__default_emojis__["prev_page"], True, hikari.ButtonStyle.PRIMARY, "prev_page", prev_page),
            ComponentButton(__default_emojis__["next_page"], True, hikari.ButtonStyle.PRIMARY, "next_page", next_page),
            ComponentButton(__default_emojis__["last_page"], True, hikari.ButtonStyle.PRIMARY, "last_page", last_page),
            ComponentButton(__default_emojis__["terminate"], True, hikari.ButtonStyle.DANGER, "stop", __cleanup_stop__),
        ]
        
        return buttons
    async def _timeout_coro(self) -> None:
        try:
            await asyncio.sleep(self._timeout)
            await self._remove_listener()
            await self._on_timeout()
        except asyncio.CancelledError:
            pass
    
    async def run(self, context: lightbulb.context.base.Context) -> None:
        self._context = context
        context.app.subscribe(hikari.InteractionCreateEvent, self._process_interaction_create)
        if self._msg is None:
            self._msg = await self._send_initial_msg(self.pages[self.current_page_index])
        else:
            await self._msg.edit(self.pages[self.current_page_index], component = await self.build_buttons())

        if self._timeout_task is not None:
            self._timeout_task.cancel()
        self._timeout_task = asyncio.create_task(self._timeout_coro())

    async def _on_timeout(self):
        row = self._context.app.rest.build_action_row()
        button = ComponentButton(__default_emojis__["timeout"], True, hikari.ButtonStyle.SECONDARY, "timeout", lambda _, __: None)
        button.build(row, True)
        await self._msg.edit(component = row)
    async def _on_stop(self):
        await self._msg.delete()

class MiniButtonPages(ButtonPages):
    def __init__(self, pages: t.Sequence[hikari.Embed], *, original_message: t.Optional[hikari.Message] = None, terminator: t.Optional[ComponentButton] = None, timeout: float = 120) -> None:
        if terminator is not None:
            super().__init__(pages, buttons = self.create_default_buttons() + [terminator], original_message=original_message, timeout=timeout)
        else:
            super().__init__(pages, original_message = original_message, timeout = timeout)
    def create_default_buttons(self) -> t.Sequence[ComponentButton]:
        buttons = [
            ComponentButton(__default_emojis__["prev_page"], True, hikari.ButtonStyle.PRIMARY, "prev_page", prev_page),
            ComponentButton(__default_emojis__["next_page"], True, hikari.ButtonStyle.PRIMARY, "next_page", next_page),
        ]
        return buttons
    async def _on_stop(self):
        # BUG: when attached to a MenuInteractionWrapper, this will clear the buttons even when the menu is returning.
        # This is probably because there's no way to determine whether this call is gonna finish before the menu starts updating.
        await self._msg.edit(component = None)

class MenuComponent:
    '''
    A tree-like node that represents the menu's option structure.
    The node has two "states": a regular node state and a fake node.

    A regular node state is when the `options` is a dictionary, which will determine the child nodes.
    A fake node state is when the `options` is a list of contents to display. In this case,
    the node's content is set to `None`, and no further child nodes can be created from this node.

    The child nodes can be accessed using dictionary notation IF there are child nodes.
    '''
    def __init__(self, content: T, options: t.Union[t.Dict[str, MenuComponent], list] = None):
        '''
        Create a node that stores the content and optionally, its options.
        The `options` can be a list, which will set the content to `None` regardless of what is passed.
        Passing a list also seal you from performing any operations on this node.
        It is recommended to not pass a `dict` through `options`, but instead, use `.add_options()`.
        '''
        self.content = content
        self.options : t.Union[t.Dict[str, MenuComponent], list] = options
        self.__parent__ : t.Optional[MenuComponent] = None

        if isinstance(self.options, list):
            self.content = None
    
    def add_option(self, key: str, content: T) -> MenuComponent:
        '''
        Add an option into the current node. Return the newly added node to further add more layers.
        '''
        
        if isinstance(self.options, list):
            raise KeyError("Cannot add more options.")
        elif self.options is None:
            self.options = {key: MenuComponent(content)}
            self.options[key].__parent__ = self
            return self.options[key]
        elif self.options.get(key) is None:
            component = MenuComponent(content)
            component.__parent__ = self
            self.options[key] = component
            return self.options[key]
        else:
            raise LookupError("Duplicated keys.")
    def add_options(self, options: t.Dict[str, T]):
        '''
        Add multiple options into the current node.
        '''
        
        if self.options is None:
            self.options = {}
        elif isinstance(self.options, list):
            raise KeyError("Cannot add more options.")
        
        for key in options:
            self.options[key] = MenuComponent(options[key])
            self.options[key].__parent__ = self
    
    def add_list_options(self, key: str, contents: t.List[T]) -> MenuComponent:
        '''
        Append a fake node to this node. Return the newly added node to do whatever you want.
        '''

        if self.options is None:
            self.options = {}
        elif isinstance(self.options, list):
            raise KeyError("Cannot add more options.")
        
        component = None
        if len(contents) == 1:
            component = MenuComponent(content = contents[0])
        else:
            component = MenuComponent(content = None, options = contents)
        
        component.__parent__ = self
        self.options[key] = component
        return component
    
    def force_add_list_options(self, contents: t.List[T]):
        '''
        Turn the current node into a fake node.
        This is also the only way to edit a fake node.
        '''
        if self.options is None:
            self.options = []
        
        for content in contents:
            self.options.append(content)
        self.content = None
    
    def __getitem__(self, key):
        if isinstance(self.options, dict):
            return self.options[key]
        else:
            raise IndexError("Index doesn't exist.")

class MenuReactionWrapper:
    def __init__(self, component: MenuComponent, *, terminate_emoji: str = __default_emojis__["terminate"], return_emoji: str = __default_emojis__["return"], timeout: float = 120):
        if isinstance(component.options, list):
            raise NotImplementedError("Use ReactionPages instead.")
        self.__menu__: MenuComponent = component
        self._timeout = timeout
        self.__terminate_button__ = ReactionButton(terminate_emoji, None)
        self.__return_button__ = ReactionButton(return_emoji, None)

        self._context: t.Optional[lightbulb.context.Context]= None
        self._msg: t.Optional[hikari.Message] = None
        self._timeout_task: t.Optional[asyncio.Task[None]] = None

    def _get_available_buttons(self, page: MenuComponent) -> t.List[ReactionButton]:
        options = []
        if isinstance(page.options, dict):
            for emote in page.options:
                options.append(ReactionButton(emote, None))
        if page.__parent__ is not None:
            options.append(self.__return_button__)
        else:
            options.append(self.__terminate_button__)
        
        return options

    async def _update_msg(self, message: hikari.Message, page: MenuComponent):
        await message.edit(page.content)
        await message.remove_all_reactions()
        for emote in self._get_available_buttons(page):
            await message.add_reaction(emote.emoji)
    
    async def _send_initial_message(self, page: MenuComponent) -> hikari.Message:
        assert self._context is not None
        resp = await self._context.respond(page.content)
        return await resp.message()

    async def _process_reaction_add(self, event: hikari.ReactionAddEvent) -> None:
        assert self._context is not None and self._msg is not None
        if event.user_id != self._context.author.id or event.message_id != self._msg.id:
            return
        
        # A MenuComponent content is empty when it contains a list of Ts (embeds).
        # Since this callback is called whenever a reaction is added, we must ignore this.
        # However, we do need processing when it's a return emoji, since that's stopping the paging.
        if self.__menu__.content is None and not self.__return_button__.is_pressed(event):
            return

        if await self._remove_unwanted_reactions(event):
            return

        if self.__return_button__.is_pressed(event) and self._msg is not None:
            self.__menu__ = self.__menu__.__parent__
            await self._update_msg(self._msg, self.__menu__)
        elif self.__terminate_button__.is_pressed(event) and self._msg is not None:
            await __cleanup_stop__(self, event)
            return
        elif self.__menu__.options is not None:
            for button in self._get_available_buttons(self.__menu__):
                if button.is_pressed(event) and self._msg is not None:
                    # Change current menu to new menu.
                    self.__menu__ = self.__menu__.options[button.emoji]
                    if not isinstance(self.__menu__.options, list):
                        await self._update_msg(self._msg, self.__menu__)
                    break
        
        # If the menu is a list then we display it using a Page instead.
        if isinstance(self.__menu__.options, list):
            await self._msg.remove_all_reactions()
            page = MiniReactionPages(self.__menu__.options, original_message = self._msg, terminator = self.__return_button__.emoji)
            await page.run(self._context)
        
    async def _remove_listener(self) -> None:
        assert self._context is not None
        self._context.app.unsubscribe(hikari.ReactionAddEvent, self._process_reaction_add)

        if self._msg is None:
            return

        try:
            await self._msg.remove_all_reactions()
        except (hikari.ForbiddenError, hikari.NotFoundError):
            pass

    async def _timeout_coro(self) -> None:
        try:
            await asyncio.sleep(self._timeout)
            await self._remove_listener()
        except asyncio.CancelledError:
            pass
    
    async def run(self, context: lightbulb.Context) -> None:
        intent_to_check_for = (
            hikari.Intents.GUILD_MESSAGE_REACTIONS
            if context.guild_id is not None
            else hikari.Intents.DM_MESSAGE_REACTIONS
        )
        if not (context.app.intents & intent_to_check_for) == intent_to_check_for:
            raise hikari.MissingIntentError(intent_to_check_for)

        self._context = context
        context.app.subscribe(hikari.ReactionAddEvent, self._process_reaction_add)
        self._msg = await self._send_initial_message(self.__menu__)
        for button in self._get_available_buttons(self.__menu__):
            await self._msg.add_reaction(button.emoji)

        if self._timeout_task is not None:
            self._timeout_task.cancel()
        self._timeout_task = asyncio.create_task(self._timeout_coro())
    
    async def _remove_unwanted_reactions(self, event: hikari.ReactionAddEvent) -> bool:
        weird_emote = True
        for button in self._get_available_buttons(self.__menu__):
            if button.is_pressed(event):
                weird_emote = False
                break
        if weird_emote:
            await self._msg.remove_reaction(event.emoji_name, user = event.user_id)
        return weird_emote

    async def _on_stop(self):
        await self._msg.delete()

class MenuInteractionWrapper:
    __slots__ = ("_context", "_msg", "_timeout_task", "_menu", "_timeout", "_return_button", "_terminate_button")
    def __init__(self, component: MenuComponent, *, terminate_emoji: str = __default_emojis__["terminate"], return_emoji: str = __default_emojis__["return"], timeout: float = 120):
        if isinstance(component.options, list):
            raise NotImplementedError("Use ReactionPages instead.")
        self._menu: MenuComponent = component
        self._timeout: float = timeout
        self._return_button = ComponentButton(return_emoji, True, hikari.ButtonStyle.SECONDARY, "return", None)
        self._terminate_button = ComponentButton(terminate_emoji, True, hikari.ButtonStyle.DANGER, "terminate", None)

        self._context: t.Optional[lightbulb.Context] = None
        self._msg: t.Optional[hikari.Message] = None
        self._timeout_task: t.Optional[asyncio.Task[None]] = None
    
    def _get_available_buttons(self, page: MenuComponent) -> t.Sequence[ComponentButton]:
        '''
        Return the `ComponentButton` version of `self.__menu__.options`.
        Also attach the return/stop button appropriately.
        '''

        buttons = []
        if isinstance(page.options, dict):
            for emote in page.options:
                buttons.append(ComponentButton(emote, True, hikari.ButtonStyle.PRIMARY, emote, None))
        if page.__parent__ is not None:
            buttons.append(self._return_button)
        else:
            buttons.append(self._terminate_button)
        
        return buttons

    async def _send_initial_message(self, page: MenuComponent) -> hikari.Message:
        '''
        Send the initial message and return a reference to that message.
        '''
        assert self._context is not None
        button_rows = await self._build_buttons(self._get_available_buttons(page))
        resp = await self._context.respond(page.content, components = button_rows)
        return await resp.message()

    async def _update_msg(self, inter: hikari.ComponentInteraction, page: MenuComponent) -> None:
        '''
        Update the message through interaction. Also update the buttons.
        '''
        button_rows = await self._build_buttons(self._get_available_buttons(page), disabled = self._msg is None)
        try:
            await inter.create_initial_response(hikari.ResponseType.MESSAGE_UPDATE, page.content, components = button_rows)
        except hikari.NotFoundError:
            await inter.edit_initial_response(page.content, components = button_rows)

    async def _build_buttons(self, buttons_list: t.Sequence[ComponentButton], disabled: bool = False) -> t.List[t.Union[hikari.api.ActionRowBuilder, hikari.UndefinedType]]:
        assert self._context is not None

        # An action row has 5 buttons at max, so we divide buttons into different rows.
        # A message also has 5 rows at max.
        if len(buttons_list) > 25:
            raise ValueError("Button amount exceed 25.")
        rows = []
        row = None
        for index, button in enumerate(buttons_list):
            if row is None:
                row = self._context.app.rest.build_action_row()
            
            button.build(row, disabled)
            if index % 5 == 4:
                rows.append(row)
                row = None
        if row is not None:
            rows.append(row)
        
        return rows

    async def _process_interaction_create(self, event: hikari.InteractionCreateEvent) -> None:
        if not isinstance(event.interaction, hikari.ComponentInteraction):
            return

        if self._msg is None:
            return

        assert self._context is not None

        # Check whether the interaction is at the desired id.
        if event.interaction.message.id != self._msg.id or event.interaction.user.id != self._context.author.id:
            return
        
        # Whether the sub-list is going on and the interaction pressed is not the return button.
        if self._menu.content is None and not self._return_button.is_pressed(event):
            return
        
        if self._return_button.is_pressed(event) and self._msg is not None:
            # Need a delay in case of a sub-list closing.
            # This is dirty but can't find any other ways.
            if self._menu.content is None:
                await asyncio.sleep(0.5)
            self._menu = self._menu.__parent__
            await self._update_msg(event.interaction, self._menu)
        elif self._terminate_button.is_pressed(event) and self._msg is not None:
            await __cleanup_stop__(self, event)
            return
        elif self._menu.options is not None:
            for key in self._menu.options:
                if self.is_id_pressed(key, event) and self._msg is not None:
                    self._menu = self._menu.options[key]
                    if not isinstance(self._menu.options, list):
                        await self._update_msg(event.interaction, self._menu)
                        break
        
        if isinstance(self._menu.options, list):
            fake_return_button = self._return_button
            fake_return_button.callback = __cleanup_stop__
            # Here we're trying to clear the buttons as a response from the interaction.
            # Without this, Discord will see the interaction with no response, which will display "This interaction failed."
            # Although the menu still works properly, it's a slight inconvenient.
            try:
                await event.interaction.create_initial_response(hikari.ResponseType.MESSAGE_UPDATE, component = hikari.UNDEFINED)
            except hikari.NotFoundError:
                await event.interaction.edit_initial_response(component = hikari.UNDEFINED)
            
            page = MiniButtonPages(self._menu.options, original_message = self._msg, terminator = fake_return_button)
            await page.run(self._context)

    def is_id_pressed(self, button_id: str, event: hikari.InteractionCreateEvent):
        '''
        Check if the interaction matches the id of the button (emoji).
        '''
        assert isinstance(event.interaction, hikari.ComponentInteraction)
        return event.interaction.custom_id == button_id

    async def _remove_listener(self) -> None:
        assert self._context is not None
        self._context.app.unsubscribe(hikari.InteractionCreateEvent, self._process_interaction_create)

        if self._msg is not None:
            buttons = self._get_available_buttons(self._menu)
            await self._msg.edit(components = await self._build_buttons(buttons, True))

    async def _timeout_coro(self) -> None:
        try:
            await asyncio.sleep(self._timeout)
            await self._remove_listener()
            await self._on_timeout()
        except asyncio.CancelledError:
            pass

    async def run(self, context: lightbulb.Context) -> None:
        """
        Run the navigator under the given context.
        Args:
            context (:obj:`~.context.base.Context`): Context
                to run the navigator under.
        Returns:
            ``None``
        """
        self._context = context
        context.app.subscribe(hikari.InteractionCreateEvent, self._process_interaction_create)
        self._msg = await self._send_initial_message(self._menu)

        if self._timeout_task is not None:
            self._timeout_task.cancel()
        self._timeout_task = asyncio.create_task(self._timeout_coro())
    
    async def _on_timeout(self):
        timeout_button = ComponentButton(__default_emojis__["timeout"], True, hikari.ButtonStyle.SECONDARY, "timeout", None)
        await self._msg.edit(components = await self._build_buttons([timeout_button], True))
    async def _on_stop(self):
        await self._msg.delete()

class ItemListBuilder:
    def __init__(self, items: list[T], max_item_per_page: int, page_type: t.Type = ButtonPages):
        self.items = items
        self.max_item = max_item_per_page
        self.page_type = page_type

        self.page_start_formatter: t.Callable[[int, T], hikari.Embed] = lambda index, item: hikari.Embed()
        self.entry_formatter: t.Callable[[hikari.Embed, int, T]] = lambda embed, index, item: None
        self.page_end_formatter: t.Callable[[hikari.Embed, int, T]] = lambda embed, index, item: None
    
    def set_page_start_formatter(self, callback: t.Callable[[int, T], hikari.Embed], /):
        self.page_start_formatter = callback
    def set_entry_formatter(self, callback: t.Callable[[hikari.Embed, int, T]], /):
        self.entry_formatter = callback
    def set_page_end_formatter(self, callback: t.Callable[[hikari.Embed, int, T]], /):
        self.page_end_formatter = callback
    
    def build(self):
        embeds: list[hikari.Embed] = []
        embed: hikari.Embed = None
        for index, item in enumerate(self.items):
            if embed is None:
                embed = self.page_start_formatter(index, item)
            
            self.entry_formatter(embed, index, item)

            if index % self.max_item == self.max_item - 1:
                self.page_end_formatter(embed, index, item)
                
                embeds.append(embed)
                embed = None
        
        if embed is not None:
            # TODO: Fix undefined-loop-variable
            self.page_end_formatter(embed, index, item)
            embeds.append(embed)

        return self.page_type(embeds)
