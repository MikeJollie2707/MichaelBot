'''Contains everything needed to build a complex menu.'''
from __future__ import annotations

import typing as t

import hikari
import miru
import lightbulb

from utils import helpers
from utils.nav.navigator import timeout_button, run_view

PageLike = t.TypeVar("PageLike", str, hikari.Embed)

class MenuComponent:
    '''
    A tree-like node that represents the menu's option structure.
    The node has two "states": a regular node state and a fake node.

    A regular node state is when the `options` is a dictionary, which will determine the child nodes.
    A fake node state is when the `options` is a list of contents to display. In this case,
    the node's content is set to `None`, and no further child nodes can be created from this node.

    The child nodes can be accessed using dictionary notation IF there are child nodes.
    '''
    def __init__(self, content: PageLike, options: t.Union[t.Dict[MenuButton, MenuComponent], list] = None):
        '''
        Create a node that stores the content and optionally, its options.
        The `options` can be a list, which will set the content to `None` regardless of what is passed.
        Passing a list also seal you from performing any operations on this node.
        It is recommended to not pass a `dict` through `options`, but instead, use `.add_options()`.
        '''
        self.content = content
        self.options : t.Union[t.Dict[MenuButton, MenuComponent], list] = options
        self.__parent__ : t.Optional[MenuComponent] = None

        if isinstance(self.options, list):
            self.content = None
    
    def add_option(self, key: MenuButton, content: PageLike) -> MenuComponent:
        '''Add an option into the current node. Return the newly added node to further add more layers.

        Warnings
        --------
        The returned object is the newly added object, not the current object.

        Parameters
        ----------
        key : MenuButton
            The button for the new option.
        content : PageLike
            The content of the new option.

        Returns
        -------
        MenuComponent
            The newly added option.

        Raises
        ------
        KeyError
            The current MenuComponent is already a fake node.
        LookupError
            There is already a similar key registered.
        '''
        
        if isinstance(self.options, list):
            raise KeyError("Cannot add more options.")
        
        if self.options is None:
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
    def add_options(self, options: t.Dict[MenuButton, PageLike]):
        '''Add multiple options into the current node.

        Warnings
        --------
        This will overwrite any possible duplicate keys.

        Parameters
        ----------
        options : t.Dict[MenuButton, PageLike]
            A mapping of {button: content}.

        Raises
        ------
        KeyError
            The current MenuComponent is already a fake node.
        '''
        
        if self.options is None:
            self.options = {}
        elif isinstance(self.options, list):
            raise KeyError("Cannot add more options.")
        
        for key in options:
            self.options[key] = MenuComponent(options[key])
            self.options[key].__parent__ = self
    
    def add_list_options(self, key: str, contents: t.List[PageLike]) -> MenuComponent:
        '''Append a fake node to this node. Return the newly added node to do whatever you want.

        Parameters
        ----------
        key : str
            The button for the new option.
        contents : t.List[PageLike]
            A list of content for the new option.

        Returns
        -------
        MenuComponent
            The newly added option.

        Raises
        ------
        KeyError
            The current MenuComponent is already a fake node.
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
    
    def force_add_list_options(self, contents: t.List[PageLike]):
        '''Turn the current node into a fake node.
        This is also the only way to edit a fake node.

        Parameters
        ----------
        contents : t.List[PageLike]
            A list of content for the option.
        '''
        if self.options is None:
            self.options = []
        
        for content in contents:
            self.options.append(content)
        self.content = None
    
    def __getitem__(self, key: MenuButton) -> t.Optional[MenuComponent]:
        '''Return the MenuComponent with the matching key, or `None` if none was found.

        Parameters
        ----------
        key : MenuButton
            The option you're retrieving.

        Returns
        -------
        t.Optional[MenuComponent]
            The option with matching key, or `None` if none was found.

        Raises
        ------
        IndexError
            The current MenuComponent is already a fake node.
        '''
        if isinstance(self.options, dict):
            return self.options.get(key)

        raise IndexError("Index doesn't exist.")

class MenuButton(miru.Button):
    '''Represents a generic button inside `ComplexView`. This should only be used in `ComplexView`.'''

    async def callback(self, _: miru.Context) -> None:
        '''Calls when the button is pressed.

        It'll move to the option if the current `MenuComponent` is not a fake node.
        '''
        view: ComplexView = self.view

        if isinstance(view.menu.options, dict):
            view.menu = view.menu.options[self]
        
        await view.update()

class ReturnMenuButton(MenuButton):
    '''Represents a return button.'''
    def __init__(self) -> None:
        super().__init__(
            style = hikari.ButtonStyle.SECONDARY,
            emoji = helpers.get_emote(":arrow_up_small:"),
            custom_id = "return_button"
        )
    
    async def callback(self, _: miru.Context) -> None:
        '''Calls when the button is pressed.

        It'll move to the parent node if it is not `None`.

        Raises
        ------
        RuntimeError
            The return button is in the root menu.
        '''
        view: ComplexView = self.view
        
        if view.menu.__parent__ is not None:
            view.menu = view.menu.__parent__
            view.current_page = 0
        else:
            raise RuntimeError("A return button is available in the root menu.")
        
        await view.update()

class StopMenuButton(MenuButton):
    '''Represents a terminate button.'''
    def __init__(self) -> None:
        super().__init__(
            style = hikari.ButtonStyle.DANGER,
            emoji = helpers.get_emote(":stop_button:"),
            custom_id = "stop_button"
        )
    
    async def callback(self, _: miru.Context) -> None:
        '''Calls when the button is pressed.

        It'll stop the `ComplexView` and delete the menu.
        '''
        view: ComplexView = self.view
        view.stop()
        
        if view.message:
            await view.message.delete()

class NextMenuButton(MenuButton):
    '''A button to move to the next page list. This behaves similarly to `nav.NextButton()`.'''
    def __init__(
        self, 
        *, 
        style: t.Union[hikari.ButtonStyle, int] = hikari.ButtonStyle.PRIMARY, 
        label: t.Optional[str] = None, 
        disabled: bool = False, 
        custom_id: t.Optional[str] = "next_menu_button", 
        url: t.Optional[str] = None, 
        emoji: t.Union[hikari.Emoji, str, None] = helpers.get_emote(":arrow_forward:"),
        row: t.Optional[int] = None
    ) -> None:
        super().__init__(style=style, label=label, disabled=disabled, custom_id=custom_id, url=url, emoji=emoji, row=row)
    
    async def callback(self, _: miru.Context) -> None:
        '''Calls when the button is pressed.

        Move to the next page, or cycle back if it's already the last page.
        '''
        view: ComplexView = self.view
        view.current_page += 1
        if view.current_page > len(view.menu.options) - 1:
            view.current_page = 0

        await view.update()

class PrevMenuButton(MenuButton):
    '''A button to move to the previous page list. This behaves similarly to `nav.PrevButton()`.'''
    def __init__(
        self, 
        *, 
        style: t.Union[hikari.ButtonStyle, int] = hikari.ButtonStyle.PRIMARY, 
        label: t.Optional[str] = None, 
        disabled: bool = False, 
        custom_id: t.Optional[str] = "prev_menu_button", 
        url: t.Optional[str] = None, 
        emoji: t.Union[hikari.Emoji, str, None] = helpers.get_emote(":arrow_backward:"),
        row: t.Optional[int] = None
    ) -> None:
        super().__init__(style=style, label=label, disabled=disabled, custom_id=custom_id, url=url, emoji=emoji, row=row)
    
    async def callback(self, _: miru.Context) -> None:
        '''Calls when the button is pressed.

        Move to the previous page, or cycle back if it's already the first page.
        '''
        view: ComplexView = self.view
        view.current_page -= 1
        if view.current_page < 0:
            view.current_page = len(view.menu.options) - 1

        await view.update()

class FirstMenuButton(MenuButton):
    '''A button to move to the first page list. This behaves similarly to `nav.FirstButton()`.'''
    def __init__(
        self, 
        *, 
        style: t.Union[hikari.ButtonStyle, int] = hikari.ButtonStyle.PRIMARY, 
        label: t.Optional[str] = None, 
        disabled: bool = False, 
        custom_id: t.Optional[str] = "first_menu_button", 
        url: t.Optional[str] = None, 
        emoji: t.Union[hikari.Emoji, str, None] = helpers.get_emote(":last_track_button:"),
        row: t.Optional[int] = None
    ) -> None:
        super().__init__(style=style, label=label, disabled=disabled, custom_id=custom_id, url=url, emoji=emoji, row=row)
    
    async def callback(self, _: miru.Context) -> None:
        '''Calls when the button is pressed.

        Move to the first page.
        '''
        view: ComplexView = self.view
        view.current_page = 0

        await view.update()

class LastMenuButton(MenuButton):
    '''A button to move to the last page list. This behaves similarly to `nav.LastButton()`.'''
    def __init__(
        self, 
        *, 
        style: t.Union[hikari.ButtonStyle, int] = hikari.ButtonStyle.PRIMARY, 
        label: t.Optional[str] = None, 
        disabled: bool = False, 
        custom_id: t.Optional[str] = "last_menu_button", 
        url: t.Optional[str] = None, 
        emoji: t.Union[hikari.Emoji, str, None] = helpers.get_emote(":next_track_button:"),
        row: t.Optional[int] = None
    ) -> None:
        super().__init__(style=style, label=label, disabled=disabled, custom_id=custom_id, url=url, emoji=emoji, row=row)
    
    async def callback(self, _: miru.Context) -> None:
        '''Calls when the button is pressed.

        Move to the last page.
        '''
        view: ComplexView = self.view
        view.current_page = len(view.menu.options) - 1

        await view.update()
        
class ComplexView(miru.View):
    '''A complex menu.'''
    def __init__(self, menu: MenuComponent, *, timeout: t.Optional[float] = 120, autodefer: bool = True, authors: t.Sequence[int] = None) -> None:
        '''Construct a complex menu.

        Parameters
        ----------
        menu : MenuComponent
            A `MenuComponent` tree. This must be a root node.
        timeout : t.Optional[float], optional
            How long (in seconds) the menu should accept interactions. Default to `120`.
        autodefer : bool, optional
            Whether or not the menu should defer when possible. Default to `True`.
        authors : t.Sequence[int], optional
            A list of ids that are allowed to interact with this view. Default to `None`.
        '''

        super().__init__(timeout=timeout, autodefer=autodefer)

        self.menu = menu
        self._author_ids = authors

        # For list menu
        self.current_page: int = 0
    
    async def view_check(self, context: miru.Context) -> bool:
        if not self._author_ids:
            return True
        
        if context.user.id not in self._author_ids:
            await context.respond("You're not allowed to interact with this menu!", flags = hikari.MessageFlag.EPHEMERAL)
        
        return context.user.id in self._author_ids
    
    def _update_button(self) -> None:
        '''
        Update the button based on the current menu state.
        '''
        self.clear_items()
        if isinstance(self.menu.options, dict):
            for button in self.menu.options:
                self.add_item(button)
        elif isinstance(self.menu.options, list):
            # TODO: Might optimize this so it wouldn't reset the buttons.
            self.add_item(FirstMenuButton())
            self.add_item(PrevMenuButton())
            self.add_item(NextMenuButton())
            self.add_item(LastMenuButton())

            for index, item in enumerate(self.menu.options):
                if isinstance(item, hikari.Embed):
                    item.set_footer(f"Page {index + 1}/{len(self.menu.options)}")
        
        if self.menu.__parent__ is None:
            self.add_item(StopMenuButton())
        else:
            self.add_item(ReturnMenuButton())
    
    async def update(self) -> None:
        '''Update the menu. This shouldn't be called by the user.

        Raises
        ------
        RuntimeError
            The message is not found (for unknown reasons).
        
        Notes
        -----
        All `MenuButton` should call this method inside their callbacks once it's done with everything.
        '''
        self._update_button()
        content = self.menu.content
        
        # If view is in a list menu. Can also check if menu.content is None instead.
        if isinstance(self.menu.options, list):
            content = self.menu.options[self.current_page]
        
        if self.message:
            await self.message.edit(content, components = self.build())
        else:
            raise RuntimeError("Oops ComplexView.update() failed.")
    
    async def on_timeout(self) -> None:
        '''Called when the view times out.

        Notes
        -----
        This adds the timeout button into the menu.
        '''
        self.clear_items()
        self.add_item(timeout_button())
        await super().on_timeout()
    
    async def run(self, ctx: lightbulb.Context) -> None:
        '''Start the menu and make it listen to the interactions.

        The menu is guaranteed to be finished once this method is over.

        Parameters
        ----------
        ctx : lightbulb.Context
            A `lightbulb` context.
        '''

        self._update_button()
        await run_view(self, ctx, self.menu.content)
