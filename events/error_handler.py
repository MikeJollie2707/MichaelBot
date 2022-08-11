'''Global error handler for `MichaelBot`.'''

# Inspired by: https://github.com/kamfretoz/XJ9/blob/main/meta/error_handler.py
# Lightbulb error hierachy: https://hikari-lightbulb.readthedocs.io/en/latest/_modules/lightbulb/errors.html

import datetime as dt
import logging

import hikari
import lightbulb

from utils import errors, helpers, models

logger = logging.getLogger("MichaelBot")

__error_responses__ = {
    "CommandNotFound": "Command `{}` cannot be found.",
    "CommandIsOnCooldown": "Chill out! `{:.2f}` seconds left.",
    "BotMissingRequiredPermission": "Bot is missing the following permissions: {}.",
    "MissingRequiredPermission": "You're missing the following permissions: {}.",
    "MissingRequiredRole": "You're missing the following roles: {}.",
    "NSFWChannelOnly": "Hey! Go to your horny channel to use this command!",
    "NoDatabase": "This command needs to connect to a database, but none detected. This is a developer-side issue.",
    "NoHTTPClient": "This command needs a aiohttp client, but none detected. This is a developer-side issue.",
    "GuildBlacklisted": "Uh oh, your server is blacklisted by the bot developers. This means you can't use any of my features. You can appeal by joining my support server.",
    "UserBlacklisted": "Uh oh, you are blacklisted by the bot developers. This means you can't use any of my features. You can appeal by joining my support server.",
    "CheckFailure": "Command `{}` does not satisfy the following requirement: {}.",
    "ConverterFailure": "The following option cannot be converted properly: `{}`.",
    "NotEnoughArguments": "You're missing the following arguments: {}.",
    "CustomAPIFailed": "The web request failed! {}.",
    "Others": "There's an unhandled error.\nError message: `{}`.\nThis is a developer-side issue."
}

async def send_error_message(error_type: str, event: lightbulb.CommandErrorEvent, *args):
    message = __error_responses__[error_type]
    if args is not None:
        message = message.format(*args)
    
    embed = hikari.Embed(
        description = f":warning: **{message}**",
        color = models.DefaultColor.brand_red,
        timestamp = dt.datetime.now().astimezone()
    )
    
    await event.context.respond(f"{event.context.author.mention}", embed = embed, user_mentions = True, flags = hikari.MessageFlag.EPHEMERAL)

async def on_command_error(event: lightbulb.CommandErrorEvent):
    exception = event.exception
    # Unwrap exception.
    if isinstance(event.exception, lightbulb.CommandInvocationError):
        exception = exception.__cause__

    if isinstance(exception, lightbulb.errors.CommandNotFound):
        await event.bot.rest.trigger_typing(event.context.channel_id)
    
    elif isinstance(exception, lightbulb.errors.CommandIsOnCooldown):
        await send_error_message("CommandIsOnCooldown", event, exception.retry_after)
    
    elif isinstance(exception, lightbulb.errors.BotMissingRequiredPermission):
        if not exception.missing_perms & hikari.Permissions.SEND_MESSAGES:
            await send_error_message("BotMissingRequiredPermission", event, helpers.striplist(helpers.get_friendly_permissions(exception.missing_perms)))
        else:
            logger.error(f"Command '{event.context.command.qualname}' is missing permissions, but one of them is `Send Messages`.")
    
    elif isinstance(exception, lightbulb.errors.MissingRequiredPermission):
        await send_error_message("MissingRequiredPermission", event, helpers.striplist(helpers.get_friendly_permissions(exception.missing_perms)))
    
    elif isinstance(exception, lightbulb.errors.MissingRequiredRole):
        pass
    
    elif isinstance(exception, lightbulb.errors.NSFWChannelOnly):
        await send_error_message("NSFWChannelOnly", event)
    
    elif isinstance(exception, errors.NoDatabase):
        await send_error_message("NoDatabase", event)
    
    elif isinstance(exception, errors.NoHTTPClient):
        await send_error_message("NoHTTPClient", event)
    
    elif isinstance(exception, errors.GuildBlacklisted):
        await send_error_message("GuildBlacklisted", event)
    
    elif isinstance(exception, errors.UserBlacklisted):
        await send_error_message("UserBlacklisted", event)
    
    elif isinstance(exception, errors.CustomCheckFailed):
        await send_error_message("CheckFailure", event, event.context.command.name, exception.args[0])
    
    elif isinstance(exception, lightbulb.errors.CheckFailure):
        await send_error_message("CheckFailure", event, event.context.command.name, exception.args[0])
    
    elif isinstance(exception, lightbulb.errors.ConverterFailure):
        await send_error_message("ConverterFailure", event, exception.option.name)
    
    elif isinstance(exception, lightbulb.errors.NotEnoughArguments):
        await send_error_message("NotEnoughArguments", event, helpers.striplist([f"`{option.name}`" for option in exception.missing_options]))

    elif isinstance(exception, errors.CustomAPIFailed):
        await send_error_message("CustomAPIFailed", event, exception.message)
    
    else:
        await send_error_message("Others", event, f"{type(exception).__name__}: {exception}")
        logger.error(f"An error occurred in '{event.context.command.qualname}', but is not handled!", exc_info = exception)


def load(bot: models.MichaelBot):
    bot.subscribe(lightbulb.CommandErrorEvent, on_command_error)
def unload(bot: models.MichaelBot):
    bot.unsubscribe(lightbulb.CommandErrorEvent, on_command_error)
