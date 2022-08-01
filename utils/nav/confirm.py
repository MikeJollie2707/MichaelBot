'''Contains a confirmation menu.'''

import typing as t

import hikari
import miru

from utils import helpers
from utils.nav.menu import run_view

class ConfirmView(miru.View):
    '''
    A confirmation menu.
    '''
    def __init__(self, *, timeout: t.Optional[float] = 120, autodefer: bool = True, authors: t.Sequence[int] = None) -> None:
        self._author_ids = authors
        super().__init__(timeout = timeout, autodefer = autodefer)

        self.result: t.Optional[bool] = None
    
    async def view_check(self, context: miru.Context) -> bool:
        if not self._author_ids:
            return True
        
        if context.user.id not in self._author_ids:
            await context.respond("You're not allowed to interact with this menu!", flags = hikari.MessageFlag.EPHEMERAL)
        
        return context.user.id in self._author_ids

    @miru.button(label = "Yes", emoji = helpers.get_emote(":white_check_mark:"), style = hikari.ButtonStyle.SUCCESS, custom_id = "yes_button")
    async def yes_button(self, _: miru.Button, __: miru.Context):
        self.result = True
        self.stop()
    @miru.button(label = "No", emoji = helpers.get_emote(":negative_squared_cross_mark:"), style = hikari.ButtonStyle.DANGER, custom_id = "no_button")
    async def no_button(self, _: miru.Button, __: miru.Context):
        self.result = False
        self.stop()
    
    async def wait(self) -> t.Optional[bool]:
        '''
        Wait until the view times out or stops manually.

        Return the result of the confirmation, or `None` if it times out.
        '''
        
        await super().wait()
        await self.message.delete()
        return self.result
