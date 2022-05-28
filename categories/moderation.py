import datetime as dt
from textwrap import dedent
import typing as t

import lightbulb
import hikari

from utils import checks, helpers, models

plugin = lightbulb.Plugin("Moderation", "Moderation Commands", include_datastore = True)
plugin.d.emote = helpers.get_emote(":hammer:")
plugin.add_checks(checks.is_command_enabled, lightbulb.bot_has_guild_permissions(*helpers.COMMAND_STANDARD_PERMISSIONS))

def get_purge_iterator(
    bot: models.MichaelBot, 
    channel_id: int, 
    *, 
    amount: int = None, 
    predicate: t.Callable[[hikari.Message], bool] = lambda m: True
) -> hikari.LazyIterator[hikari.Message]:
    
    bulk_delete_limit = dt.datetime.now().astimezone() - dt.timedelta(days = 1)
    if amount is not None:
        return (
            bot.rest.fetch_messages(channel_id)
            .take_while(lambda message: message.created_at > bulk_delete_limit)
            .filter(predicate)
            .limit(amount)
        )
    else:
        return (
            bot.rest.fetch_messages(channel_id)
            .take_while(lambda message: message.created_at > bulk_delete_limit)
            .filter(predicate)
        )

async def do_purge(
    bot: models.MichaelBot,
    iterator: hikari.LazyIterator[hikari.Message],
    channel_id: int
):
    count: int = 0
    async for messages in iterator.chunk(100):
        try:
            await bot.rest.delete_messages(channel_id, messages)
            count += len(messages)
        except hikari.BulkDeleteError as bulk_delete_error:
            count += len(bulk_delete_error.messages_deleted)
    return count

@plugin.command()
@lightbulb.set_help(dedent('''
    - The bot can delete messages up to 2 weeks. It can't delete any messages past that point.
'''))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES))
@lightbulb.command("purge", "Purge all messages that meet certain conditions.")
@lightbulb.implements(lightbulb.PrefixCommandGroup, lightbulb.SlashCommandGroup)
async def purge(ctx: lightbulb.Context):
    raise lightbulb.CommandNotFound(invoked_with = ctx.invoked_with)

@purge.child
@lightbulb.set_help(dedent('''
    - The bot can delete messages up to 2 weeks. It can't delete any messages past that point.
'''))
@lightbulb.option("amount", "The amount of messages to delete. Default to all.", type = int, min_value = 1, max_value = 500, default = None)
@lightbulb.command("messages", "Purge the most recent messages.", inherit_checks = True, auto_defer = True)
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def purge_messages(ctx: lightbulb.Context):
    amount = ctx.options.amount
    bot: models.MichaelBot = ctx.bot

    if amount is not None:
        amount = max(1, min(amount, 500))
        if isinstance(ctx, lightbulb.PrefixContext):
            # Delete the command just sent.
            amount += 1

    iterator = get_purge_iterator(bot, ctx.channel_id, amount = amount)
    count = await do_purge(bot, iterator, ctx.channel_id)
    
    await ctx.respond(f"Successfully deleted {count} messages.", delete_after = 5)

@purge.child
@lightbulb.set_help(dedent('''
    - The bot can delete messages up to 2 weeks. It can't delete any messages past that point.
'''))
@lightbulb.option("amount", "The amount of messages to delete. Default to 1.", type = int, min_value = 1, max_value = 500, default = 1)
@lightbulb.option("member", "The member to delete.", type = hikari.Member)
@lightbulb.command("user", "Purge the most recent messages from a user.", inherit_checks = True, auto_defer = True)
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def purge_user(ctx: lightbulb.Context):
    member: hikari.Member = ctx.options.member
    amount: int = ctx.options.amount
    bot: models.MichaelBot = ctx.bot

    amount = max(1, min(amount, 500))
    if isinstance(ctx, lightbulb.PrefixContext):
        amount += 1
    
    iterator = get_purge_iterator(bot, ctx.channel_id, predicate = lambda m: m.author.id == member.id, amount = amount)
    count = await do_purge(bot, iterator, ctx.channel_id)

    await ctx.respond(f"Successfully deleted {count} messages from user `{member}`.", delete_after = 5)

@purge.child
@lightbulb.set_help(dedent('''
    - The bot can delete messages up to 2 weeks. It can't delete any messages past that point.
'''))
@lightbulb.option("flags", "Additional flag to set. Default flag is `--delete-with-embeds`.", choices = ["--delete-with-embeds", "--delete-embeds-only"], default = "--delete-with-embeds")
@lightbulb.option("amount", "The amount of messages to delete. Default to 1.", type = int, min_value = 1, max_value = 500, default = 1)
@lightbulb.command("embed", "Purge the most recent messages with embeds.", inherit_checks = True, auto_defer = True)
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def purge_embed(ctx: lightbulb.Context):
    amount: int = ctx.options.amount
    flags: str = ctx.options.flags
    bot: models.MichaelBot = ctx.bot

    amount = max(1, min(amount, 500))
    if isinstance(ctx, lightbulb.PrefixContext) and bool(ctx.event.message.embeds):
        amount += 1
    
    iterator = get_purge_iterator(bot, ctx.channel_id, predicate = lambda m: bool(m.embeds), amount = amount)
    count: int = 0
    if flags == "--delete-with-embeds":
        count = await do_purge(bot, iterator, ctx.channel_id)
    else:
        raise NotImplementedError("This flag is not implemented due to possible rate limiting.")
    
    await ctx.respond(f"Successfully deleted {count} messages with embeds.", delete_after = 5)

@purge.child
@lightbulb.set_help(dedent('''
    - This command will delete any occurrence of the provided pattern. If the string is `e e` and the message is `the end` then it'll be deleted.
    - To delete messages that contain any of the provided words, consider using `purge words`.
    - The bot can delete messages up to 2 weeks. It can't delete any messages past that point.
'''))
@lightbulb.option("amount", "The amount of messages to delete. Default to all.", type = int, min_value = 1, max_value = 500, default = None)
@lightbulb.option("string", "The words to delete. Any messages with this string occurrence will be deleted.")
@lightbulb.command("string", "Purge the most recent messages contain the string specified.", inherit_checks = True, auto_defer = True)
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def purge_string(ctx: lightbulb.Context):
    string: str = ctx.options.string
    amount: int = ctx.options.amount
    bot: models.MichaelBot = ctx.bot

    if amount is not None:
        amount = max(1, min(amount, 500))
        if isinstance(ctx, lightbulb.PrefixContext) and string in ctx.event.message.content:
            amount += 1

    def has_string(msg: hikari.Message):
        if msg.content is None:
            return False
        return string in msg.content
    iterator = get_purge_iterator(bot, ctx.channel_id, predicate = has_string, amount = amount)
    count = await do_purge(bot, iterator, ctx.channel_id)

    await ctx.respond(f"Successfully deleted {count} messages that contains the string `{string}`.", delete_after = 5)

@purge.child
@lightbulb.set_help(dedent('''
    - This command will delete any occurrence of the provided words. If the input words is `e f` and the message is `fly` or `set` then it'll be deleted.
    - To delete messages that contain all the provided words, consider using `purge string`.
    - The bot can delete messages up to 2 weeks. It can't delete any messages past that point.
'''))
@lightbulb.option("amount", "The amount of messages to delete. Default to all.", type = int, min_value = 1, max_value = 500, default = None)
@lightbulb.option("words", "The words to filter, separated by white space.")
@lightbulb.command("words", "Purge the most recent messages contain any of the words specified.", inherit_checks = True, auto_defer = True)
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def purge_words(ctx: lightbulb.Context):
    words: str = ctx.options.words
    amount: int = ctx.options.amount
    bot: models.MichaelBot = ctx.bot

    word_list = words.split()

    def has_word(msg: hikari.Message):
        if msg.content is None:
            return False
        for word in word_list:
            if word in msg.content:
                return True
        return False

    if amount is not None:
        amount = max(1, min(amount, 500))
        if isinstance(ctx, lightbulb.PrefixContext) and has_word(ctx.event.message):
            amount += 1
    
    iterator = get_purge_iterator(bot, ctx.channel_id, predicate = has_word, amount = amount)
    count = await do_purge(bot, iterator, ctx.channel_id)

    await ctx.respond(f"Successfully deleted {count} messages that contains any of the following words: `{', '.join(word_list)}`.", delete_after = 5)

def load(bot: models.MichaelBot):
    bot.add_plugin(plugin)
def unload(bot: models.MichaelBot):
    bot.remove_plugin(plugin)
