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
            # Need to ensure the buttons are updated.
            # Reference: https://github.com/HyperGH/hikari-miru/blob/main/miru/ext/nav/navigator.py#L227
            #for button in view.children:
            #    if isinstance(button, nav.NavButton):
            #        await button.before_page_change()

            #initial_content = view.pages[view.current_page]
            await view.send(ctx.interaction)
            return
        else:
            raise TypeError("'initial_content' must be provided if 'view' is not type 'NavigatorView'.")
    
    resp_proxy = await ctx.respond(initial_content, components = view.build())
    view.start(await resp_proxy.message())
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
        super().__init__(*args, **kwargs)

        for index, item in enumerate(self.pages):
            if isinstance(item, hikari.Embed):
                item.set_footer(f"Page {index + 1}/{len(self.pages)}")
    
    def get_default_buttons(self) -> t.List[nav.NavButton[nav.NavigatorView]]:
        '''
        Returns a list of default buttons.
        These are `FirstButton()`, `PrevButton()`, `NextButton()`, `LastButton()`, and `StopButtonDelete()`.

        Returns
        -------
        t.List[nav.NavButton[nav.NavigatorView]]
            A list of default buttons.
        '''

        return [nav.FirstButton(), nav.PrevButton(), nav.NextButton(), nav.LastButton(), StopButtonDelete()]
    
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
    def __init__(self, items: list[T], max_item_per_page: int, page_type: t.Type = ButtonNavigator):
        self.items = items
        self.max_item = max_item_per_page
        self.page_type = page_type

        self.page_start_formatter: t.Callable[[int, T], hikari.Embed] = lambda index, item: hikari.Embed()
        self.entry_formatter: t.Callable[[hikari.Embed, int, T], None] = lambda embed, index, item: None
        self.page_end_formatter: t.Callable[[hikari.Embed, int, T], None] = lambda embed, index, item: None
    
    def set_page_start_formatter(self, callback: t.Callable[[int, T], hikari.Embed], /):
        self.page_start_formatter = callback
    def set_entry_formatter(self, callback: t.Callable[[hikari.Embed, int, T], None], /):
        self.entry_formatter = callback
    def set_page_end_formatter(self, callback: t.Callable[[hikari.Embed, int, T], None], /):
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

        return self.page_type(pages = embeds)
