'''Utility Commands'''

# API commands are inspired by: https://github.com/kamfretoz/XJ9/tree/main/extensions/utils
import asyncio
import datetime as dt
import json
from textwrap import dedent

import hikari
import humanize
import lightbulb
import py_expression_eval
from lightbulb.ext import tasks

from utils import checks, converters, errors, helpers, models, psql
from utils.nav.navigator import ItemListBuilder, run_view

NOTIFY_REFRESH = 2 * 60

plugin = lightbulb.Plugin(name = "Utilities", description = "Utility Commands", include_datastore = True)
plugin.d.emote = helpers.get_emote(":gear:")
plugin.add_checks(checks.is_command_enabled, lightbulb.bot_has_guild_permissions(*helpers.COMMAND_STANDARD_PERMISSIONS))

# TODO: Deal with errors.CustomAPIFailed more appropriately.
# Currently, it's sending a command-scope error message and a global unhandled message.

@plugin.command()
@lightbulb.option("number", "The number you're converting.", type = str)
@lightbulb.option("to_base", "The base you want to convert to.", type = int, choices = [2, 8, 10, 16])
@lightbulb.option("from_base", "The base the number you're converting.", type = int, choices = [2, 8, 10, 16])
@lightbulb.command("base-convert", "Convert a number to the desired base.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def base_convert(ctx: lightbulb.Context):
    from_base: int = ctx.options.from_base
    to_base: int = ctx.options.to_base
    number: str = ctx.options.number

    # Force into default bases when used as flaw Prefix Command.
    if from_base not in [2, 8, 10, 16]:
        from_base = 10
    if to_base not in [2, 8, 10, 16]:
        to_base = 16

    base_10: int = 0
    # Parse if user put spaces between binary to make it easier to read.
    if from_base == 2:
        number = "".join(number.split(' '))
    
    try:
        base_10 = int(number, base = from_base)
    except ValueError:
        await ctx.respond(f"The number is not at base `{from_base}`.", reply = True, mentions_reply = True)
        return
    
    if to_base == 10:
        await ctx.respond(f"{number} = {base_10}", reply = True)
    elif to_base == 2:
        await ctx.respond(f"{number} = {base_10:b}", reply = True)
    elif to_base == 8:
        await ctx.respond(f"{number} = {base_10:o}", reply = True)
    elif to_base == 16:
        await ctx.respond(f"{number} = #{base_10:X}", reply = True)

@plugin.command()
@lightbulb.set_help(dedent('''
    - Rounding errors, along with other debatable values such as `0^0` is incorrect due to language limitation.
'''))
@lightbulb.option("expression", "The math expression.", modifier = helpers.CONSUME_REST_OPTION)
@lightbulb.command("calc", "Calculate a math expression.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def calc(ctx: lightbulb.Context):
    parser = py_expression_eval.Parser()

    try:
        result = parser.parse(ctx.options.expression).evaluate({})
        await ctx.respond(f"Result: `{result}`")
    except ZeroDivisionError:
        await ctx.respond("Zero division detected!", reply = True, mentions_reply = True)
    except Exception:
        await ctx.respond("An error occurred!", reply = True, mentions_reply = True)

@plugin.command()
@lightbulb.set_help(dedent('''
    - This command only works with subcommands.
'''))
@lightbulb.command("embed", "Send an embed.")
@lightbulb.implements(lightbulb.PrefixCommandGroup, lightbulb.SlashCommandGroup)
async def _embed(ctx: lightbulb.Context):
    raise lightbulb.CommandNotFound(invoked_with = ctx.invoked_with)

@_embed.child
@lightbulb.add_cooldown(length = 3.0, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.option("raw_embed", "The embed in JSON format.", modifier = helpers.CONSUME_REST_OPTION)
@lightbulb.command("from-json", "Send an embed from a JSON object. Check out https://embedbuilder.nadekobot.me/ for easier time.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def embed_from_json(ctx: lightbulb.Context):
    raw_embed: str = ctx.options.raw_embed

    raw_embed = raw_embed.strip("```").strip()
    
    try:
        json_embed = json.loads(raw_embed)
        if not isinstance(json_embed, dict):
            raise json.JSONDecodeError("JSON object must be enclosed in `{{}}`.", doc = raw_embed, pos = 0)
        
        embed = helpers.embed_from_dict(json_embed)
        await ctx.respond(embed = embed)

        # Delete message later for user to look at what they did.
        if isinstance(ctx, lightbulb.PrefixContext):
            await ctx.event.message.delete()
    except json.JSONDecodeError as js:
        await ctx.respond(f"{ctx.author.mention} The JSON you provided is not valid. Detail message: `{js}`", user_mentions = True)
    except ValueError:
        await ctx.respond(f"{ctx.author.mention} The color you provided is invalid. It must be an integer of base 10.", user_mentions = True)
    except hikari.BadRequestError as bad:
        await ctx.respond(f"{ctx.author.mention} The JSON you provided is ill-formed. Detail message: `{bad}`", user_mentions = True)
    
@_embed.child
@lightbulb.set_help(dedent('''
    - This is useful when you want to change slightly from an existing embed.
'''))
@lightbulb.add_cooldown(length = 3.0, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.option("channel", "The channel the message is in. Default to the current channel.", 
    type = hikari.TextableGuildChannel, 
    channel_types = (hikari.ChannelType.GUILD_TEXT,),
    default = None, 
    modifier = helpers.CONSUME_REST_OPTION
)
@lightbulb.option("message_id", "The message ID. The bot can't get a message that's too old.")
@lightbulb.command("to-json", "Take the embed from a message and convert it to a JSON object.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def embed_to_json(ctx: lightbulb.Context):
    message_id = ctx.options.message_id
    channel = ctx.options.channel
    bot: models.MichaelBot = ctx.bot

    channel_id: int = 0
    if ctx.options.channel is None:
        channel_id = ctx.channel_id
    else:
        channel_id = channel.id
    
    message: hikari.Message = None
    try:
        message = await bot.rest.fetch_message(channel_id, message_id)
    except hikari.NotFoundError:
        await ctx.respond("I can't get this message!", reply = True, mentions_reply = True)
        return
    
    if not message.embeds:
        await ctx.respond("There's no embed in this message!", reply = True, mentions_reply = True)
    else:
        for embed in message.embeds:
            d = helpers.embed_to_dict(embed)
            
            # Might raise message too long error.
            await ctx.respond(f"```{json.dumps(d, indent = 4)}```")

@_embed.child
@lightbulb.set_help(dedent('''
    - This is an alternative to `embed interactive`.
    - Either `title` or `description` must be non-empty.
'''))
@lightbulb.add_cooldown(length = 3.0, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.option("channel", "The channel to send this embed. Default to the current one.", type = hikari.TextableGuildChannel, channel_types = (hikari.ChannelType.GUILD_TEXT,), default = None)
@lightbulb.option("color", "Your choice of color. Default to green.", autocomplete = True, default = "green")
@lightbulb.option("description", "The description of the embed.", default = None)
@lightbulb.option("title", "The title of the embed.", default = None)
@lightbulb.command("simple", "Create and send a simple embed. Useful for quick embeds.")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def embed_simple(ctx: lightbulb.Context):
    title = ctx.options.title
    description = ctx.options.description
    color = ctx.options.color
    channel = ctx.options.channel

    if not title and not description:
        await ctx.respond("Embed cannot be empty!", reply = True, mentions_reply = True)
    else:
        if color not in models.DefaultColor._member_names_:
            color = "green"
        
        embed = hikari.Embed(
            title = title,
            description = description,
            color = models.DefaultColor[color].value
        )

        if channel is None:
            await ctx.respond(embed = embed)
        else:
            await ctx.respond("Sent!")
            await ctx.bot.rest.create_message(channel, embed = embed)
@embed_simple.autocomplete("color")
async def embed_simple_autocomplete(option: hikari.AutocompleteInteractionOption, _interaction: hikari.AutocompleteInteraction):
    if option.value != "":
        return [color for color in models.DefaultColor._member_names_ if color.startswith(option.value)]
    return models.DefaultColor._member_names_[:25]

@_embed.child
@lightbulb.set_help(dedent('''
    - Bot needs to have `Manage Messages`.
    - This is an alternative to `embed simple`.
'''))
@lightbulb.add_cooldown(length = 3.0, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES))
@lightbulb.command("interactive", "Create a simple embed with prompts.")
@lightbulb.implements(lightbulb.PrefixSubCommand)
async def embed_interactive(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    def is_response(event: hikari.GuildMessageCreateEvent):
        msg = event.message
        return msg.author == ctx.author and msg.channel_id == ctx.channel_id
    
    title = ""
    description = ""
    color = None
    channel = None
    available_colors = models.DefaultColor._member_names_

    await ctx.event.message.delete()
    try:
        await ctx.respond("What's the title? (Type `None` to skip)")
        event = await bot.wait_for(hikari.GuildMessageCreateEvent, timeout = 120, predicate = is_response)
        if event.message.content.strip('`') != "None":
            title = event.message.content
        
        await event.message.delete()
        await ctx.delete_last_response()

        await ctx.respond("What's the description? (Type `None` to skip)")
        event = await bot.wait_for(hikari.GuildMessageCreateEvent, timeout = 120, predicate = is_response)
        if event.message.content.strip('`') != "None":
            description = event.message.content
        
        await event.message.delete()
        await ctx.delete_last_response()

        if title == "" and description == "":
            await ctx.respond("Embed must have at least a title or a description. If you don't want these fields, use `embed from-json`.")
            return

        await ctx.respond(f"What's the color? You can enter a hex number or one of the following predefined colors: `{helpers.striplist(available_colors)}`")
        event = await bot.wait_for(hikari.GuildMessageCreateEvent, timeout = 120, predicate = is_response)
        color_content = event.message.content.lower()
        if color_content in available_colors:
            color = models.DefaultColor[color_content].value
        else:
            try:
                color = hikari.Color(int(color_content, base = 16))
            except ValueError:
                await ctx.respond("Invalid color.")
                return
        
        await event.message.delete()
        await ctx.delete_last_response()

        await ctx.respond("Which channel to send this embed? (Type `None` to send it here)")
        event = await bot.wait_for(hikari.GuildMessageCreateEvent, timeout = 120, predicate = is_response)
        if event.message.content.strip('`') != "None":
            channel = await lightbulb.TextableGuildChannelConverter(ctx).convert(event.message.content.strip('`'))
        if channel is None:
            channel = ctx.get_channel()
        
        await event.message.delete()
        await ctx.delete_last_response()

        embed = hikari.Embed(
            title = title,
            description = description,
            color = color
        )
        await bot.rest.create_message(channel, embed = embed)
    except asyncio.TimeoutError:
        await ctx.respond("Session timed out.")

@_embed.child
@lightbulb.set_help(dedent('''
    - Bot needs to have `Manage Messages`.
    - This is an alternative to `embed simple`.
'''))
@lightbulb.add_cooldown(length = 3.0, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES))
@lightbulb.command("interactive2", "Create a simple embed with visual prompts.")
@lightbulb.implements(lightbulb.PrefixSubCommand)
async def embed_interactive2(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    embed = hikari.Embed(
        title = "Template Embed",
        description = "Choose one of the below buttons to edit the embed. Any changes will be reflected on this embed."
    )

    available_colors = models.DefaultColor._member_names_
    channel = ctx.get_channel()
    timeout = 120

    row = bot.rest.build_action_row()
    button = row.add_button(hikari.ButtonStyle.SECONDARY, "edit_title")
    button.set_label("Edit Title")
    button.add_to_container()
    button = row.add_button(hikari.ButtonStyle.SECONDARY, "edit_description")
    button.set_label("Edit Description")
    button.add_to_container()
    button = row.add_button(hikari.ButtonStyle.SECONDARY, "edit_color")
    button.set_label("Edit Color")
    button.add_to_container()
    button = row.add_button(hikari.ButtonStyle.SECONDARY, "edit_destination")
    button.set_label("Edit Destination")
    button.add_to_container()
    button = row.add_button(hikari.ButtonStyle.PRIMARY, "send")
    button.set_label("Send")
    button.set_emoji(helpers.get_emote(":arrow_forward:"))
    button.add_to_container()
    msg = await ctx.respond(f"Destination: {channel.mention}", embed = embed, components = [row])
    
    def is_valid_interaction(event: hikari.InteractionCreateEvent) -> bool:
        if not isinstance(event.interaction, hikari.ComponentInteraction):
            return False
        
        return (
            event.interaction.custom_id in ("edit_title", "edit_description", "edit_color", "edit_destination", "send")
            and event.interaction.member.id == ctx.author.id
        )
    
    def is_response(event: hikari.GuildMessageCreateEvent):
        msg = event.message
        return msg.author == ctx.author and msg.channel_id == ctx.channel_id
    
    while True:
        try:
            event = await bot.wait_for(hikari.InteractionCreateEvent, timeout = timeout, predicate = is_valid_interaction)
            interaction: hikari.ComponentInteraction = event.interaction
            if interaction.custom_id == "edit_title":
                await interaction.create_initial_response(
                    hikari.ResponseType.MESSAGE_CREATE,
                    "What's the title? (Type `None` to clear)",
                    flags = hikari.MessageFlag.EPHEMERAL
                )
                
                try:
                    setter_event = await bot.wait_for(hikari.GuildMessageCreateEvent, timeout = timeout, predicate = is_response)
                    if setter_event.message.content.strip('`') != "None":
                        embed.title = setter_event.message.content
                    else:
                        embed.title = ""
                    
                    await msg.edit(embed = embed)
                    await setter_event.message.delete()
                except asyncio.TimeoutError:
                    await interaction.edit_initial_response(f"`{interaction.custom_id}` session expired.")
            elif interaction.custom_id == "edit_description":
                await interaction.create_initial_response(
                    hikari.ResponseType.MESSAGE_CREATE,
                    "What's the description? (Type `None` to clear)",
                    flags = hikari.MessageFlag.EPHEMERAL
                )
                
                try:
                    setter_event = await bot.wait_for(hikari.GuildMessageCreateEvent, timeout = timeout, predicate = is_response)
                    if setter_event.message.content.strip('`') != "None":
                        embed.description = setter_event.message.content
                    else:
                        embed.description = ""
                    
                    await msg.edit(embed = embed)
                    await setter_event.message.delete()
                except asyncio.TimeoutError:
                    await interaction.edit_initial_response(f"`{interaction.custom_id}` session expired.")
            elif interaction.custom_id == "edit_color":
                await interaction.create_initial_response(
                    hikari.ResponseType.MESSAGE_CREATE,
                    f"What's the color? You can enter a hex number or one of the following predefined colors: `{helpers.striplist(available_colors)}`",
                    flags = hikari.MessageFlag.EPHEMERAL
                )

                try:
                    setter_event = await bot.wait_for(hikari.GuildMessageCreateEvent, timeout = timeout, predicate = is_response)
                    color_content = setter_event.message.content.lower()

                    if color_content in available_colors:
                        embed.color = models.DefaultColor[color_content].value
                    else:
                        try:
                            embed.color = hikari.Color(int(color_content, base = 16))
                        except ValueError:
                            pass
                    
                    await msg.edit(embed = embed)
                    await setter_event.message.delete()
                except asyncio.TimeoutError:
                    await interaction.edit_initial_response(f"`{interaction.custom_id}` session expired.")
            elif interaction.custom_id == "edit_destination":
                await interaction.create_initial_response(
                    hikari.ResponseType.MESSAGE_CREATE,
                    "Which channel to send this embed? (Type `None` to send it here)",
                    flags = hikari.MessageFlag.EPHEMERAL
                )

                try:
                    setter_event = await bot.wait_for(hikari.GuildMessageCreateEvent, timeout = timeout, predicate = is_response)
                    if setter_event.message.content.strip('`') != "None":
                        channel = await lightbulb.TextableGuildChannelConverter(ctx).convert(setter_event.message.content.strip('`'))
                    elif channel is None or setter_event.message.content.strip('`') == "None":
                        channel = ctx.get_channel()
                    
                    await msg.edit(f"Destination: {channel.mention}")
                    await setter_event.message.delete()
                except asyncio.TimeoutError:
                    await interaction.edit_initial_response(f"`{interaction.custom_id}` session expired.")
            elif interaction.custom_id == "send":
                # No need to response to the interaction if we just delete the message.
                await bot.rest.create_message(channel, embed = embed)
                await msg.delete()
                return
        except asyncio.TimeoutError:
            await msg.edit("Session expired.", embeds = None, components = None)
            return

async def do_remind(bot: models.MichaelBot, user: hikari.User, message: str, when: dt.datetime = None, remind_id: int = None):
    '''Send `user` a DM about `message` at time `when`.

    This should be created as a `Task` to avoid logic-blocking (the code itself is not async-blocking).

    Args:
        bot (models.MichaelBot): Bot instance.
        user (hikari.User): The user to DM.
        message (str): The message to be sent.
        when (dt.datetime, optional): The time to send. If `None` or smaller than current time, the message will be sent immediately.
        remind_id (int, optional): The reminder's id to be removed once the reminder is sent. If `None`, reminder will not be removed from database.
    '''
    if when is not None:
        await helpers.sleep_until(when)
    
    try:
        # BUG: user seems to be None in some cases.
        await user.send("Hi there! You told me to remind you about:\n" + message)

        if remind_id is not None:
            async with bot.pool.acquire() as conn:
                await psql.Reminders.delete_reminder(conn, remind_id, user.id)
    except hikari.ForbiddenError:
        # Don't remove reminder if the sending fails, will retry to send on next refresh cycle.
        pass
@tasks.task(s = NOTIFY_REFRESH, auto_start = True, pass_app = True, wait_before_execution = True)
async def scan_reminders(bot: models.MichaelBot):
    '''Check for past and future reminders every `NOTIFY_REFRESH` seconds.

    - If there are any past reminders (tried to send, but couldn't due to permissions, disconnect, etc.), it'll try sending them again.
    - If there are any future reminders within `NOTIFY_REFRESH` seconds, it'll create `do_remind()` task to be launched.

    Args:
        bot (models.MichaelBot): The bot.
    '''

    if bot.pool is None: return

    current = dt.datetime.now().astimezone()
    future = current + dt.timedelta(seconds = NOTIFY_REFRESH)

    async with bot.pool.acquire() as conn:
        passed = await psql.Reminders.get_past_reminders(conn, current)
        upcoming = await psql.Reminders.get_reminders(conn, current, future)
    
    for missed_reminder in passed:
        user = bot.cache.get_user(missed_reminder["user_id"])
        assert user is not None
        bot.create_task(do_remind(bot, user, missed_reminder["message"], current, missed_reminder["remind_id"]))
    
    for upcoming_reminder in upcoming:
        user = bot.cache.get_user(upcoming_reminder["user_id"])
        assert user is not None
        bot.create_task(do_remind(bot, user, upcoming_reminder["message"], upcoming_reminder["awake_time"], upcoming_reminder["remind_id"]))

@plugin.command()
@lightbulb.set_help(dedent('''
    - This command only works with subcommands.
'''))
@lightbulb.command("remindme", "Create a reminder. Make sure your DM is open to the bot.", hidden = True, aliases = ["rmd", "notify", "timer"])
@lightbulb.implements(lightbulb.PrefixCommandGroup, lightbulb.SlashCommandGroup)
async def remind(ctx: lightbulb.Context):
    raise lightbulb.CommandNotFound(invoked_with = ctx.invoked_with)

@remind.child
@lightbulb.set_help(dedent(f'''
    - An interval of less than {NOTIFY_REFRESH} seconds is considered to be a "short reminder".
'''))
@lightbulb.add_cooldown(length = 5.0, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.option("message", "The message the bot will send after the interval.", modifier = helpers.CONSUME_REST_OPTION)
@lightbulb.option("interval", "How long until the bot reminds you. Must be between 1 minute and 30 days. Example: 3d2m1s", type = converters.IntervalConverter)
@lightbulb.command("create", "Create a reminder. Make sure your DM is open to the bot.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def remind_create(ctx: lightbulb.Context):
    interval: dt.timedelta = ctx.options.interval
    bot: models.MichaelBot = ctx.bot

    if isinstance(ctx, lightbulb.SlashContext):
        interval = await converters.IntervalConverter(ctx).convert(ctx.options.interval)

    when: dt.datetime = dt.datetime.now().astimezone() + interval
    if interval.total_seconds() < 60:
        await ctx.respond("The interval is too small. Must be at least 1 minute.", reply = True, mentions_reply = True)
    elif interval.total_seconds() > 30 * 24 * 60 * 60:
        await ctx.respond("The interval is too large. Must be at most 30 days.", reply = True, mentions_reply = True)
    elif interval.total_seconds() < NOTIFY_REFRESH:
        bot.create_task(do_remind(bot, ctx.author, ctx.options.message, when))
        await ctx.respond("A short reminder has been created. Expect the bot to DM you soon:tm:", reply = True)
    else:
        async with bot.pool.acquire() as conn:
            await psql.Reminders.insert_reminder(conn, ctx.author.id, when, ctx.options.message)
        await ctx.respond(f"I'll remind you about '{ctx.options.message}' in `{humanize.precisedelta(interval, format = '%0.0f')}`.", reply = True)

@remind.child
@lightbulb.set_help(dedent('''
    - Due to optimization, this command won't display short reminders.
'''))
@lightbulb.add_cooldown(length = 5.0, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.command("view", "View all your long reminders.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def remind_view(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    reminders = []
    async with bot.pool.acquire() as conn:
        reminders = await psql.Reminders.get_user_reminders(conn, ctx.author.id)
    
    if len(reminders) == 0:
        embed = helpers.get_default_embed(
            title = "Reminders",
            description = "*Cricket noises*",
            author = ctx.author,
            timestamp = dt.datetime.now().astimezone()
        )
        await ctx.respond(embed = embed, reply = True)
    else:
        builder = ItemListBuilder(reminders, max_item_per_page = 5)
        def start_format(_, __):
            embed = helpers.get_default_embed(
                title = "Reminders",
                description = "",
                author = ctx.author,
                timestamp = dt.datetime.now().astimezone()
            )
            embed.description = "**Format:** 0. `remind_id` Reminder message - 0h0m\n\n"
            return embed
        def entry_format(embed: hikari.Embed, index: int, item: dict):
            message = item["message"]
            if len(item["message"]) > 30:
                message = item["message"][:27] + "..."
            
            time_till_awake: dt.timedelta = item["awake_time"] - dt.datetime.now().astimezone()
            embed.description += f"{index + 1}. `{item['remind_id']}` {message} - {humanize.precisedelta(time_till_awake, 'minutes', format = '%0.0f')}\n"
        
        builder.set_page_start_formatter(start_format)
        builder.set_entry_formatter(entry_format)
        await run_view(builder.build(), ctx)

@remind.child
@lightbulb.set_help(dedent('''
    - Due to optimization, this command won't remove short reminders.
'''))
@lightbulb.add_cooldown(length = 5.0, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.option("remind_id", "The reminder's id. You can find it in `remindme view`.", type = int)
@lightbulb.command("remove", "Remove a long reminder.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def remind_remove(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    async with bot.pool.acquire() as conn:
        await psql.Reminders.delete_reminder(conn, ctx.options.remind_id, ctx.author.id)
    
    await ctx.respond(f"Removed the reminder `{ctx.options.remind_id}`.")

@plugin.command()
@lightbulb.add_checks(checks.is_aiohttp_existed)
@lightbulb.add_cooldown(length = 5.0, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.option("term", "The term to search. Example: `rickroll`.", modifier = helpers.CONSUME_REST_OPTION)
@lightbulb.command("urban", "Search a term on urbandictionary.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def urban(ctx: lightbulb.Context):
    term = ctx.options.term
    bot: models.MichaelBot = ctx.bot

    BASE_URL = "http://api.urbandictionary.com/v0/define"
    parameters = {
        "term": term
    }
    async with bot.aio_session.get(BASE_URL, params = parameters) as resp:
        if resp.status == 200:
            resp_json = await resp.json()
            if len(resp_json["list"]) > 0:
                top_entry = resp_json["list"][0]
                definition = top_entry["definition"].replace('[', '').replace(']', '')
                if len(definition) > 900:
                    definition = definition[:901]
                    definition += "..."
                example = top_entry["example"].replace('[', '').replace(']', '')
                if len(example) > 900:
                    example = example[:901]
                    example += "..."
                elif example == "":
                    example = "`None provided`"
                
                embed = helpers.get_default_embed(
                    title = f"{top_entry['word']}",
                    timestamp = dt.datetime.now().astimezone()
                )
                embed.add_field(
                    name = "Definition:",
                    value = definition
                )
                embed.add_field(
                    name = "Example:",
                    value = example
                )
                embed.add_field(
                    name = "Ratio:",
                    value = f"{helpers.get_emote(':thumbs_up:')} {top_entry['thumbs_up']} - {helpers.get_emote(':thumbs_down:')} {top_entry['thumbs_down']}"
                )
                embed.set_footer(
                    text = f"Defined by: {top_entry['author']}"
                )

                await ctx.respond(embed = embed, reply = True)
            else:
                await ctx.respond("Sorry, that word doesn't exist on urban dictionary.", reply = True, mentions_reply = True)
        else:
            raise errors.CustomAPIFailed(f"Endpoint {BASE_URL} returned with status {resp.status}. Raw response: {await resp.text()}")

@plugin.command()
@lightbulb.add_checks(checks.is_aiohttp_existed)
@lightbulb.add_cooldown(length = 5.0, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.option("city_name", "The city to check. Example: `Paris`.", modifier = helpers.CONSUME_REST_OPTION)
@lightbulb.command("weather", "Display weather information for a location.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def weather(ctx: lightbulb.Context):
    city_name = ctx.options.city_name
    bot: models.MichaelBot = ctx.bot

    api_key = bot.secrets.get("weather_api_key")
    if not api_key:
        raise NotImplementedError("Weather API key not detected.")
    
    BASE_URL = "http://api.weatherapi.com/v1"
    parameters = {
        "q": city_name,
        "key": api_key,
    }
    async with bot.aio_session.get(BASE_URL + "/current.json", params = parameters) as resp:
        if resp.status == 200:
            resp_json = await resp.json()
            location = resp_json["location"]
            current = resp_json["current"]

            embed = hikari.Embed(
                title = "Weather Information",
                description = f"Condition: {current['condition']['text']}",
                timestamp = dt.datetime.now().astimezone()
            ).set_footer(
                text = "Powered by: weatherapi.com",
                icon = "http://cdn.weatherapi.com/v4/images/weatherapi_logo.png"
            )
            embed.add_field(
                name = "Location:",
                value = dedent(f'''
                    City: {location["name"]}
                    Country: {location["country"]}
                    Timezone: {location["tz_id"]}
                ''')
            )
            embed.add_field(
                name = "Temperature:",
                value = dedent(f'''
                    True Temperature: {current["temp_c"]} °C / {current["temp_f"]} °F
                    Feel Like: {current["feelslike_c"]} °C / {current["feelslike_f"]} °F
                ''')
            )
            embed.add_field(
                name = "Wind:",
                value = dedent(f'''
                    Speed: {current["wind_kph"]} km/h ({current["wind_mph"]} mph)
                    Gusts: {current["gust_kph"]} km/h ({current["gust_mph"]} mph)
                    Direction: {current["wind_degree"]}° {current["wind_dir"]}
                ''')
            )
            embed.add_field(
                name = "Others:",
                value = dedent(f'''
                    Pressure: {current["pressure_mb"]} hPa ({current["pressure_in"]} inches)
                    Precipitation: {current["precip_mm"]} mm ({current["precip_in"]} inches)
                    Humidity: {current["humidity"]}%
                    Cloudiness: {current["cloud"]}%
                    UV Index: {current["uv"]}
                ''')
            )
            embed.set_thumbnail("http:" + current["condition"]["icon"])

            if current["is_day"] == 1:
                embed.color = models.DefaultColor.gold.value
            else:
                embed.color = models.DefaultColor.dark_blue.value

            await ctx.respond(embed = embed, reply = True)
        elif resp.status == 400:
            await ctx.respond("City not found.", reply = True, mentions_reply = True)
        else:
            resp_json = await resp.json()
            await ctx.respond(f"Weather API return the following error: `{resp_json['error']['message']}`", reply = True, mentions_reply = True)

def load(bot: models.MichaelBot):
    bot.add_plugin(plugin)
def unload(bot: models.MichaelBot):
    bot.remove_plugin(plugin)
