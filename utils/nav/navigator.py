'''Contains common forms of menu navigator.'''

import typing as t

import hikari
import lightbulb
import miru
from miru.ext import nav

from utils import helpers

T = t.TypeVar("T")

async def run_view(view: miru.View, ctx: lightbulb.Context, initial_content: t.Union[str, hikari.Embed] = None) -> None:
    '''A simplified way to run a `miru.View`.

    Parameters
    ----------
    view : miru.View
        A `miru.View` or its subclasses.
    ctx : lightbulb.Context
        A context to send the view.
    initial_content : t.Union[str, hikari.Embed], optional
        The content to first display. This is optional for `nav.NavigatorView` and its subclasses.

    Raises
    ------
    TypeError
        `initial_content` is not provided, but `view` is not type `nav.NavigatorView`.
    hikari.BadRequestError
        Maybe `ctx` is deferred.
    '''
    if initial_content is None:
        if isinstance(view, nav.NavigatorView):
            # nav.NavigatorView cannot be run on an interaction with a response already (typically deferring)
            # so we have to do things manually here.
            # Reference: https://github.com/HyperGH/hikari-miru/blob/main/miru/ext/nav/navigator.py#L227
            for button in view.children:
                if isinstance(button, nav.NavButton):
                    await button.before_page_change()

            initial_content = view.pages[view.current_page]
            
            #await view.send(ctx.interaction)
            #return
        else:
            raise TypeError("'initial_content' must be provided if 'view' is not type 'NavigatorView'.")
    
    resp_proxy = await ctx.respond(initial_content, components = view.build())
    await view.start(await resp_proxy)
    await view.wait()

def timeout_button() -> nav.NavButton:
    '''Return a `nav.NavButton` to be use in `nav.NavigatorView`.
    This button is safe to use in `miru.View`.

    Returns
    -------
    nav.NavButton
        The default timeout button.
    '''
    return nav.NavButton(
        style = hikari.ButtonStyle.SECONDARY, 
        emoji = helpers.get_emote(":clock12:"),
        custom_id = "timeout_button",
        disabled = True
    )

class StopButtonDelete(nav.StopButton):
    '''
    A custom button to stop the navigator AND delete the message.
    This button should only be used in `nav.NavigatorView`.
    '''
    async def callback(self, context: miru.Context) -> None:
        # Reference: https://github.com/HyperGH/hikari-miru/blob/main/miru/ext/nav/buttons.py#L239

        #pylint: disable=protected-access
        view: nav.NavigatorView = self.view
        if not view.message and not view._inter:
            return
        
        if view._inter and view.ephemeral:
            await view._inter.delete_initial_response()
        elif view.message:
            await view.message.delete()
        #pylint: enable=protected-access
        view.stop()

class ButtonNavigator(nav.NavigatorView):
    '''
    The default navigator.
    '''
    def __init__(self, *args, **kwargs) -> None:
        '''Construct a default navigator.

        Parameters
        ----------
        pages : list[str | hikari.Embed]
            A list of content to be displayed.
        buttons : list[nav.NavButton], optional
            A list of buttons to display. It is safe to ignore this parameter for most use cases.
        timeout : float, optional
            The amount of seconds before the view time out. Default to `120.0`.
        autodefer : bool, optional
            Whether the view will handle deferred response. It is safe to ignore this parameter for most use cases. Default to `True`.
        authors : t.Sequence[int], optional
            A list of ids that are allowed to interact with this view. Default to `None`.
        '''

        self._author_ids: t.Optional[t.Sequence[int]] = kwargs.pop("authors", None)
        super().__init__(*args, **kwargs)

        for index, item in enumerate(self.pages):
            if isinstance(item, hikari.Embed):
                item.set_footer(f"Page {index + 1}/{len(self.pages)}")
    
    def get_default_buttons(self) -> t.Sequence[nav.NavButton]:
        '''
        Returns a list of default buttons.
        These are `FirstButton()`, `PrevButton()`, `NextButton()`, `LastButton()`, and `StopButtonDelete()`.

        Returns
        -------
        t.List[nav.NavButton[nav.NavigatorView]]
            A list of default buttons.
        '''

        return [nav.FirstButton(), nav.PrevButton(), nav.NextButton(), nav.LastButton(), StopButtonDelete()]
    
    async def view_check(self, context: miru.Context) -> bool:
        if not self._author_ids:
            return True
        
        if context.user.id not in self._author_ids:
            await context.respond("You're not allowed to interact with this menu!", flags = hikari.MessageFlag.EPHEMERAL)
        
        return context.user.id in self._author_ids
    
    async def on_timeout(self) -> None:
        '''Called when the view times out.

        Notes
        -----
        This adds the timeout button into the menu.
        '''
        self.clear_items()
        self.add_item(timeout_button())
        await super().on_timeout()

class ItemListBuilder:
    '''A builder to fit a list of item into a navigator appropriately. (This is experimental and can be removed at any time).'''
    def __init__(self, items: list[T], max_item_per_page: int):
        '''Construct the builder.

        Parameters
        ----------
        items : list[T]
            A list of items.
        max_item_per_page : int
            The max amount of item to display before moving to a new page.
        '''

        self.items = items
        self.max_item = max_item_per_page

        self.page_start_formatter: t.Callable[[int, T], hikari.Embed] = None
        self.entry_formatter: t.Callable[[hikari.Embed, int, T], None] = None
        self.page_end_formatter: t.Callable[[hikari.Embed, int, T], None] = lambda embed, index, item: None
    
    def set_page_start_formatter(self, callback: t.Callable[[int, T], hikari.Embed], /):
        '''Set this callback as the formatter to run whenever a new page is requested to be created.

        Notes
        -----
        This is recommended to use as a decorator.

        Parameters
        ----------
        callback : t.Callable[[int, T], hikari.Embed]
            The callback to use. It must accept an `int` (index of the item), the item itself, and return a `hikari.Embed`.
        '''
        self.page_start_formatter = callback
    def set_entry_formatter(self, callback: t.Callable[[hikari.Embed, int, T], None], /):
        '''Set this callback as the formatter to run while iterating through the item list.

        Notes
        -----
        This is recommended to use as a decorator.

        Parameters
        ----------
        callback : t.Callable[[hikari.Embed, int, T], None]
            The callback to use. It must accept a `hikari.Embed` (the page it's editing), an `int` (index of the item), and the item itself.
        '''
        self.entry_formatter = callback
    def set_page_end_formatter(self, callback: t.Callable[[hikari.Embed, int, T], None], /):
        '''Set this callback as the formatter to run once adding items to a page is finished.

        Notes
        -----
        This is recommended to use as a decorator.

        Parameters
        ----------
        callback : t.Callable[[hikari.Embed, int, T], None]
            The callback to use. It must accept a `hikari.Embed` (the page it's editing), an `int` (index of the item), and the item itself.
        '''
        self.page_end_formatter = callback
    
    def build(self, *, page_type = ButtonNavigator, authors: t.Sequence[int] = None):
        '''Start the formatting process and return an object of `page_type`.

        Warnings
        --------
        The builder must provide at least `page_start_formatter` and either `entry_formatter` or `page_end_formatter` before this method is called.

        Parameters
        ----------
        page_type : t.Type, optional
            The type of navigator to use, by default ButtonNavigator. This must have a `pages` argument accepting a list of `hikari.Embed` and a `authors` argument accepting a list of ids.
        authors : t.Sequence[int], optional
            The ids of people that are allowed to interact with the navigator. Default to `None`.

        Returns
        -------
        t.Any
            The type passed into the constructor, by default ButtonNavigator.

        Raises
        ------
        NotImplementedError
            `page_start_formatter` is empty or both `entry_formatter` and `page_end_formatter` are empty.
        '''

        if self.page_start_formatter is None or (self.entry_formatter is None and self.page_end_formatter is None):
            raise NotImplementedError("Not enough formatters are defined.")

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

        return page_type(pages = embeds, authors = authors)
