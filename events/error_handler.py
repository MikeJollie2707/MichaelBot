'''Global error handler for `MichaelBot`.'''

# Inspired by: https://github.com/kamfretoz/XJ9/blob/main/meta/error_handler.py
# Lightbulb error hierachy: https://hikari-lightbulb.readthedocs.io/en/latest/_modules/lightbulb/errors.html

import datetime as dt
import logging

import hikari
import humanize
import lightbulb

from utils import errors, helpers, models

logger = logging.getLogger("MichaelBot")

def __get_generic_error_embed() -> hikari.Embed:
    return hikari.Embed(
        color = models.DefaultColor.brand_red,
        timestamp = dt.datetime.now().astimezone()
    )

async def on_command_not_found(event: lightbulb.CommandErrorEvent, _: lightbulb.CommandNotFound):
    await event.bot.rest.trigger_typing(event.context.channel_id)
async def on_command_cooldown(event: lightbulb.CommandErrorEvent, exception: lightbulb.CommandIsOnCooldown):
    embed = __get_generic_error_embed()
    embed.description = f":warning: **Chill out! You need to wait for `{humanize.precisedelta(exception.retry_after, format = '%0.0f')}` before using this command again!**"

    await event.context.respond(f"{event.context.author.mention}", embed = embed, user_mentions = True, flags = hikari.MessageFlag.EPHEMERAL)
async def on_bot_missing_permission(event: lightbulb.CommandErrorEvent, exception: lightbulb.BotMissingRequiredPermission):
    if exception.missing_perms & hikari.Permissions.SEND_MESSAGES:
        logger.error(f"Command '{event.context.command.qualname}' is missing permissions, but one of them is `Send Messages`.")
        return
    
    missing_perms = ', '.join(helpers.get_friendly_permissions(exception.missing_perms))
    embed = __get_generic_error_embed()
    embed.description = f":warning: **Bot is missing the following permissions: {missing_perms}.**"

    await event.context.respond(f"{event.context.author.mention}", embed = embed, user_mentions = True, flags = hikari.MessageFlag.EPHEMERAL)
async def on_user_missing_permission(event: lightbulb.CommandErrorEvent, exception: lightbulb.MissingRequiredPermission):
    missing_perms = ', '.join(helpers.get_friendly_permissions(exception.missing_perms))
    embed = __get_generic_error_embed()
    embed.description = f":warning: **You're missing the following permissions: {missing_perms}.**"

    await event.context.respond(f"{event.context.author.mention}", embed = embed, user_mentions = True, flags = hikari.MessageFlag.EPHEMERAL)
async def on_nsfw_channel(event: lightbulb.CommandErrorEvent, _: lightbulb.NSFWChannelOnly):
    embed = __get_generic_error_embed()
    embed.description = ":warning: **This is a NSFW command. Therefore, you must use this command in a NSFW channel.**"

    await event.context.respond(f"{event.context.author.mention}", embed = embed, user_mentions = True, flags = hikari.MessageFlag.EPHEMERAL)
async def on_check_failed(event: lightbulb.CommandErrorEvent, exception: lightbulb.CheckFailure):
    embed = __get_generic_error_embed()
    embed.description = f":warning: **Command `{event.context.command.qualname}` does not satisfy the following requirement: {exception.args[0]}.**"

    await event.context.respond(f"{event.context.author.mention}", embed = embed, user_mentions = True, flags = hikari.MessageFlag.EPHEMERAL)
async def on_converter_failed(event: lightbulb.CommandErrorEvent, exception: lightbulb.ConverterFailure):
    embed = __get_generic_error_embed()
    embed.description = f":warning: **The following option cannot be converted properly: `{exception.option.name}`.\nDetails: ```{exception.__cause__}```**"

    await event.context.respond(f"{event.context.author.mention}", embed = embed, user_mentions = True, flags = hikari.MessageFlag.EPHEMERAL)
async def on_missing_arguments(event: lightbulb.CommandErrorEvent, exception: lightbulb.NotEnoughArguments):
    missing_arguments = ', '.join([f"`{option.name}`" for option in exception.missing_options])
    embed = __get_generic_error_embed()
    embed.description = f":warning: **You're missing the following arguments: {missing_arguments}.**"

    await event.context.respond(f"{event.context.author.mention}", embed = embed, user_mentions = True, flags = hikari.MessageFlag.EPHEMERAL)
async def on_max_concurrency_reached(event: lightbulb.CommandErrorEvent, exception: lightbulb.MaxConcurrencyLimitReached):
    embed = __get_generic_error_embed()
    embed.description = ":warning: **This command cannot be run multiple times while the previous one is still active.**"

    await event.context.respond(f"{event.context.author.mention}", embed = embed, user_mentions = True, flags = hikari.MessageFlag.EPHEMERAL)
async def on_no_database(event: lightbulb.CommandErrorEvent, _: errors.NoDatabase):
    embed = __get_generic_error_embed()
    embed.description = ":warning: **This command needs to connect to a database, but none detected. This is a developer-side issue.**"

    await event.context.respond(f"{event.context.author.mention}", embed = embed, user_mentions = True, flags = hikari.MessageFlag.EPHEMERAL)
async def on_no_http_client(event: lightbulb.CommandErrorEvent, _: errors.NoHTTPClient):
    embed = __get_generic_error_embed()
    embed.description = ":warning: **This command needs an aiohttp client, but none detected. This is a developer-side issue.**"

    await event.context.respond(f"{event.context.author.mention}", embed = embed, user_mentions = True, flags = hikari.MessageFlag.EPHEMERAL)
async def on_guild_blacklisted(event: lightbulb.CommandErrorEvent, _: errors.GuildBlacklisted):
    embed = __get_generic_error_embed()
    embed.description = ":warning: **Uh oh, your server is blacklisted by the bot developers. This means you can't use any of my features. You can appeal by joining my support server.**"

    await event.context.respond(f"{event.context.author.mention}", embed = embed, user_mentions = True, flags = hikari.MessageFlag.EPHEMERAL)
async def on_user_blacklisted(event: lightbulb.CommandErrorEvent, _: errors.UserBlacklisted):
    embed = __get_generic_error_embed()
    embed.description = ":warning: **Uh oh, you are blacklisted by the bot developers. This means you can't use any of my features. You can appeal by joining my support server.**"

    await event.context.respond(f"{event.context.author.mention}", embed = embed, user_mentions = True, flags = hikari.MessageFlag.EPHEMERAL)
async def on_custom_check_failed(event: lightbulb.CommandErrorEvent, exception: errors.CustomCheckFailed):
    embed = __get_generic_error_embed()
    embed.description = f":warning: **Command `{event.context.command.qualname}` does not satisfy the following requirement: {exception.args[0]}.**"

    await event.context.respond(f"{event.context.author.mention}", embed = embed, user_mentions = True, flags = hikari.MessageFlag.EPHEMERAL)
async def on_custom_api_failed(event: lightbulb.CommandErrorEvent, exception: errors.CustomAPIFailed):
    embed = __get_generic_error_embed()
    embed.description = f":warning: **The web request failed! {exception.message}.**"

    await event.context.respond(f"{event.context.author.mention}", embed = embed, user_mentions = True, flags = hikari.MessageFlag.EPHEMERAL)
async def on_generic_error(event: lightbulb.CommandErrorEvent, exception: Exception):
    embed = __get_generic_error_embed()
    embed.description = f":warning: **There's an unhandled error.\nError message: `{type(exception).__name__}: {exception}`.\nThis is a developer-side issue.**"

    await event.context.respond(f"{event.context.author.mention}", embed = embed, user_mentions = True, flags = hikari.MessageFlag.EPHEMERAL)
    logger.error(f"An error occurred in '{event.context.command.qualname}', but is not handled!", exc_info = exception)

__handler_mapping = {
    lightbulb.CommandNotFound: on_command_not_found,
    lightbulb.CommandIsOnCooldown: on_command_cooldown,
    lightbulb.BotMissingRequiredPermission: on_bot_missing_permission,
    lightbulb.MissingRequiredPermission: on_user_missing_permission,
    lightbulb.NSFWChannelOnly: on_nsfw_channel,
    lightbulb.CheckFailure: on_check_failed,
    lightbulb.ConverterFailure: on_converter_failed,
    lightbulb.NotEnoughArguments: on_missing_arguments,
    lightbulb.MaxConcurrencyLimitReached: on_max_concurrency_reached,
    errors.NoDatabase: on_no_database,
    errors.NoHTTPClient: on_no_http_client,
    errors.GuildBlacklisted: on_guild_blacklisted,
    errors.UserBlacklisted: on_user_blacklisted,
    errors.CustomCheckFailed: on_custom_check_failed,
    errors.CustomAPIFailed: on_custom_api_failed,
}

async def on_command_error(event: lightbulb.CommandErrorEvent):
    exception = event.exception
    # Unwrap exception.
    if isinstance(event.exception, lightbulb.CommandInvocationError):
        exception = exception.__cause__
    
    handler = __handler_mapping.get(type(exception), on_generic_error)
    await handler(event, exception)

def load(bot: models.MichaelBot):
    bot.subscribe(lightbulb.CommandErrorEvent, on_command_error)
def unload(bot: models.MichaelBot):
    bot.unsubscribe(lightbulb.CommandErrorEvent, on_command_error)
