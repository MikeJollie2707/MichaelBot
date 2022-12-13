import datetime as dt
import typing as t

import miru

class ModalWithCallback(miru.Modal):
    '''A class to create Discord modal.

    This class behaves exactly the same as `miru.Modal`, except you can attach callbacks to it after construction.
    Therefore, for a quick-and-dirty modal usage, you can use this without subclassing `miru.Modal`.

    To attach callbacks, use `as_...()` methods (you can use it as a decorator).
    '''

    def __init__(self, title: str, *, custom_id: t.Optional[str] = None, timeout: t.Optional[t.Union[float, int, dt.timedelta]] = 300) -> None:
        super().__init__(title, custom_id=custom_id, timeout=timeout)
        self.__callback = None
        self.__timeout = None
        self.__check = None
        self.__on_error = None
    
    def as_callback(self, callback: t.Callable[[miru.ModalContext], t.Awaitable[None]]):
        self.__callback = callback
    def as_timeout(self, callback: t.Callable[[None], t.Awaitable[None]]):
        self.__timeout = callback
    def as_check(self, callback: t.Callable[[miru.ModalContext], t.Awaitable[bool]]):
        self.__check = callback
    def as_error(self, callback: t.Callable[[Exception, t.Optional[miru.ModalContext]], t.Awaitable[None]]):
        self.__on_error = callback
    
    async def callback(self, context: miru.ModalContext) -> None:
        if self.__callback:
            return await self.__callback(context)
        return await super().callback(context)
    async def on_timeout(self) -> None:
        if self.__timeout:
            return await self.__timeout()
        return await super().on_timeout()
    async def modal_check(self, context: miru.ModalContext) -> bool:
        if self.__check:
            return await self.__check(context)
        return await super().modal_check(context)
    async def on_error(self, error: Exception, context: t.Optional[miru.ModalContext] = None) -> None:
        if self.__on_error:
            return await self.__on_error(error, context)
        return await super().on_error(error, context)
