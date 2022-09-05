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
    amount: int = 0, 
    predicate: t.Callable[[hikari.Message], bool] = lambda m: True
) -> hikari.LazyIterator[hikari.Message]:
    '''Get an iterator of messages based on the criteria specified.

    Args:
        bot (models.MichaelBot): The bot instance.
        channel_id (int): The channel to purge.
        amount (int, optional): The maximum amount of messages to delete. If 0, then there's no max.
        predicate (Callable[[hikari.Message], bool], optional): A callback that filter out the message to delete. By default, no filter is applied.

    Returns:
        hikari.LazyIterator[hikari.Message]: _description_
    '''
    bulk_delete_limit = dt.datetime.now().astimezone() - dt.timedelta(weeks = 2)
    if amount > 0:
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
            .filter(predicate))
async def do_purge(
    bot: models.MichaelBot,
    iterator: hikari.LazyIterator[hikari.Message],
    channel_id: int
) -> int:
    '''This is a coroutine. Purge messages using the iterator provided.

    Args:
        bot (models.MichaelBot): The bot instance.
        iterator (hikari.LazyIterator[hikari.Message]): An iterator of Message. Should be obtained via `get_purge_iterator()`.
        channel_id (int): The channel to delete. This must match what is passed through `get_purge_iterator()`.
    
    Return:
        int: The number of messages successfully deleted.
    '''

    count: int = 0
    async for messages in iterator.chunk(100):
        try:
            await bot.rest.delete_messages(channel_id, messages)
            count += len(messages)
        except hikari.BulkDeleteError as bulk_delete_error:
            count += len(bulk_delete_error.messages_deleted)
        
        # Hard limit to purging. Will need to see how big this can go.
        if count >= 1000:
            break
    return count
@plugin.command()
@lightbulb.set_help(dedent('''
    - The bot can delete messages up to 2 weeks. It can't delete any messages past that point.
'''))
@lightbulb.add_checks(
    lightbulb.bot_has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES),
    lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES)
)
@lightbulb.add_cooldown(length = 10.0, uses = 1, bucket = lightbulb.GuildBucket)
@lightbulb.option("amount", "The amount of messages to delete, or 0 to delete all. Default to 0.", type = int, default = 0)
@lightbulb.command("purge", f"[{plugin.name}] Purge the most recent messages.")
@lightbulb.implements(lightbulb.PrefixCommandGroup, lightbulb.SlashCommandGroup)
async def purge(ctx: lightbulb.Context):
    await purge_messages(ctx)

@purge.child
@lightbulb.set_help(dedent('''
    - The bot can delete messages up to 2 weeks. It can't delete any messages past that point.
'''))
@lightbulb.add_checks(
    lightbulb.bot_has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES),
    lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES)
)
@lightbulb.add_cooldown(length = 10.0, uses = 1, bucket = lightbulb.GuildBucket)
@lightbulb.option("amount", "The amount of messages to delete. Default to all.", type = int, min_value = 0, max_value = 500, default = 0)
@lightbulb.command("messages", f"[{plugin.name}] Purge the most recent messages.", inherit_checks = True)
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def purge_messages(ctx: lightbulb.Context):
    amount = ctx.options.amount
    bot: models.MichaelBot = ctx.bot

    if amount != 0:
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
@lightbulb.add_checks(
    lightbulb.bot_has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES),
    lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES)
)
@lightbulb.add_cooldown(length = 10.0, uses = 1, bucket = lightbulb.GuildBucket)
@lightbulb.option("amount", "The amount of messages to delete, or 0 to delete all. Default to 0.", type = int, min_value = 0, max_value = 500, default = 0)
@lightbulb.option("member", "The member to delete.", type = hikari.Member)
@lightbulb.command("member", f"[{plugin.name}] Purge the most recent messages from a user.", inherit_checks = True)
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def purge_member(ctx: lightbulb.Context):
    member: hikari.Member = ctx.options.member
    amount: int = ctx.options.amount
    bot: models.MichaelBot = ctx.bot

    if amount != 0:
        amount = max(1, min(amount, 500))
        if isinstance(ctx, lightbulb.PrefixContext) and ctx.author.id == member.id:
            amount += 1

    predicate = lambda m: m.author.id == member.id
    
    iterator = get_purge_iterator(bot, ctx.channel_id, predicate = predicate, amount = amount)
    count = await do_purge(bot, iterator, ctx.channel_id)

    await ctx.respond(f"Successfully deleted {count} messages from user `{member}`.", delete_after = 5)

@purge.child
@lightbulb.set_help(dedent('''
    - The bot can delete messages up to 2 weeks. It can't delete any messages past that point.
'''))
@lightbulb.add_checks(
    lightbulb.bot_has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES),
    lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES)
)
@lightbulb.add_cooldown(length = 10.0, uses = 1, bucket = lightbulb.GuildBucket)
@lightbulb.option("amount", "The amount of messages to delete, or 0 to delete all. Default to 0.", type = int, min_value = 0, max_value = 500, default = 0)
@lightbulb.command("embed", f"[{plugin.name}] Purge the most recent messages with embeds.", inherit_checks = True)
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def purge_embed(ctx: lightbulb.Context):
    amount: int = ctx.options.amount
    bot: models.MichaelBot = ctx.bot

    if amount != 0:
        amount = max(1, min(amount, 500))
        if isinstance(ctx, lightbulb.PrefixContext) and bool(ctx.event.message.embeds):
            amount += 1
    
    iterator = get_purge_iterator(bot, ctx.channel_id, predicate = lambda m: bool(m.embeds), amount = amount)
    count = await do_purge(bot, iterator, ctx.channel_id)
    
    await ctx.respond(f"Successfully deleted {count} messages with embeds.", delete_after = 5)

@purge.child
@lightbulb.set_help(dedent('''
    - The bot can delete messages up to 2 weeks. It can't delete any messages past that point.
'''))
@lightbulb.add_checks(
    lightbulb.bot_has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES),
    lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES)
)
@lightbulb.add_cooldown(length = 10.0, uses = 1, bucket = lightbulb.GuildBucket)
@lightbulb.option("to_message", "The link to the ending message. Default to the latest message.", type = hikari.Message, default = None)
@lightbulb.option("from_message", "The link to the starting message.", type = hikari.Message)
@lightbulb.command("range", f"[{plugin.name}] Purge the messages within between two messages.", inherit_checks = True)
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def purge_range(ctx: lightbulb.Context):
    from_message: hikari.Message = ctx.options.from_message
    to_message: hikari.Message = ctx.options.to_message
    bot: models.MichaelBot = ctx.bot
    
    if to_message is None:
        if isinstance(ctx, lightbulb.PrefixContext):
            to_message = ctx.event.message
        else:
            channel: hikari.GuildTextChannel = ctx.get_channel()
            msg_history = await channel.fetch_history(around = dt.datetime.now().astimezone()).limit(1)
            to_message = msg_history[0]
    else:
        to_message = await lightbulb.MessageConverter(ctx).convert(to_message)
    from_message = await lightbulb.MessageConverter(ctx).convert(from_message)

    from_date = from_message.created_at
    to_date = to_message.created_at
    def between_date(msg: hikari.Message):
        return from_date <= msg.created_at <= to_date
    iterator = get_purge_iterator(bot, ctx.channel_id, predicate = between_date)
    count = await do_purge(bot, iterator, ctx.channel_id)

    await ctx.respond(f"Successfully deleted {count} messages between the range specified.", delete_after = 5)

@purge.child
@lightbulb.set_help(dedent('''
    - This command will delete any occurrence of the provided pattern. If the string is `e e` and the message is `the end` then it'll be deleted.
    - To delete messages that contain any of the provided words, consider using `purge words`.
    - The bot can delete messages up to 2 weeks. It can't delete any messages past that point.
'''))
@lightbulb.add_checks(
    lightbulb.bot_has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES),
    lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES)
)
@lightbulb.add_cooldown(length = 10.0, uses = 1, bucket = lightbulb.GuildBucket)
@lightbulb.option("amount", "The amount of messages to delete, or 0 to delete all. Default to 0.", type = int, min_value = 0, max_value = 500, default = 0)
@lightbulb.option("string", "The words to delete. Any messages with this string occurrence will be deleted.")
@lightbulb.command("string", f"[{plugin.name}] Purge the most recent messages contain the string specified.", inherit_checks = True)
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def purge_string(ctx: lightbulb.Context):
    string: str = ctx.options.string
    amount: int = ctx.options.amount
    bot: models.MichaelBot = ctx.bot

    if amount != 0:
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
@lightbulb.add_checks(
    lightbulb.bot_has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES),
    lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES)
)
@lightbulb.add_cooldown(length = 10.0, uses = 1, bucket = lightbulb.GuildBucket)
@lightbulb.option("amount", "The amount of messages to delete, or 0 to delete all. Default to 0.", type = int, min_value = 0, max_value = 500, default = 0)
@lightbulb.option("words", "The words to filter, separated by white space.")
@lightbulb.command("words", f"[{plugin.name}] Purge the most recent messages contain any of the words specified.", inherit_checks = True, auto_defer = True)
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

    if amount != 0:
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
