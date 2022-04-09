# Inspired by: https://github.com/kamfretoz/XJ9/blob/main/meta/error_handler.py
# Lightbulb error hierachy: https://hikari-lightbulb.readthedocs.io/en/latest/_modules/lightbulb/errors.html

import lightbulb
import hikari

import datetime as dt

import utilities.helpers as helpers
import utilities.errors as errors
import utilities.models as models

__error_responses__ = {
    "CommandNotFound": "Command `{}` cannot be found.",
    "CommandIsOnCooldown": "Chill out! `{}` seconds left.",
    "BotMissingRequiredPermission": "Bot is missing the following permissions: {}.",
    "MissingRequiredPermission": "You're missing the following permissions: {}.",
    "MissingRequiredRole": "You're missing the following roles: {}.",
    "NSFWChannelOnly": "Hey! Go to your horny channel to use this command!",
    "GuildBlacklisted": "Uh oh, your server is blacklisted by the bot developers. This means you can't use any of my features. You can appeal by joining my support server.",
    "UserBlacklisted": "Uh oh, you are blacklisted by the bot developers. This means you can't use any of my features. You can appeal by joining my support server.",
    "CheckFailure": "Command `{}` does not satisfy the following requirement: {}.",
    "ConverterFailure": "The following option cannot be converted properly: {}.",
    "NotEnoughArguments": "You're missing the following arguments: {}.",
}

async def send_error_message(error_type: str, event: lightbulb.CommandErrorEvent, *args):
    message = __error_responses__[error_type]
    if args is not None:
        message = message.format(*args)
    
    await event.context.respond(message)

async def on_command_error(event: lightbulb.CommandErrorEvent):
    #if isinstance(event.exception, lightbulb.CommandInvocationError):
    #    await event.context.respond("Something went wrong.")
    #    #raise event.exception
    
    exception = event.exception.__cause__ or event.exception

    if isinstance(exception, lightbulb.errors.CommandNotFound):
        #await send_error_message("CommandNotFound", event, exception.invoked_with)
        await event.bot.rest.trigger_typing(event.context.channel_id)
    elif isinstance(exception, lightbulb.errors.CommandIsOnCooldown):
        await send_error_message("CommandIsOnCooldown", event, exception.retry_after)
    elif isinstance(exception, lightbulb.errors.BotMissingRequiredPermission):
        if not exception.missing_perms & hikari.Permissions.SEND_MESSAGES:
            await send_error_message("BotMissingRequiredPermission", event, helpers.striplist(helpers.get_friendly_permissions(exception.missing_perms)))
        else:
            print("Failed")
    elif isinstance(exception, lightbulb.errors.MissingRequiredPermission):
        await send_error_message("MissingRequiredPermission", event, helpers.striplist(helpers.get_friendly_permissions(exception.missing_perms)))
    elif isinstance(exception, lightbulb.errors.MissingRequiredRole):
        pass
    elif isinstance(exception, lightbulb.errors.NSFWChannelOnly):
        await send_error_message("NSFWChannelOnly", event)
    elif isinstance(exception, errors.GuildBlacklisted):
        await send_error_message("GuildBlacklisted", event)
    elif isinstance(exception, errors.UserBlacklisted):
        await send_error_message("UserBlacklisted", event)
    elif isinstance(exception, errors.CustomCheckFailed):
        await send_error_message("CheckFailure", event, event.context.command.name, exception.args[0])
    elif isinstance(exception, lightbulb.errors.CheckFailure):
        await send_error_message("CheckFailure", event, event.context.command.name, exception.message)
    elif isinstance(exception, lightbulb.errors.ConverterFailure):
        await send_error_message("ConverterFailure", event, exception.option.name)
    elif isinstance(exception, lightbulb.errors.NotEnoughArguments):
        await send_error_message("NotEnoughArguments", event, helpers.striplist([f"`{option.name}`" for option in exception.missing_options]))
    else:
        raise exception


def load(bot: models.MichaelBot):
    bot.subscribe(lightbulb.CommandErrorEvent, on_command_error)
    #pass
def unload(bot: models.MichaelBot):
    bot.unsubscribe(lightbulb.CommandErrorEvent, on_command_error)
    #pass
