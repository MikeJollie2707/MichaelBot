'''Utility Commands'''

# API commands are inspired by: https://github.com/kamfretoz/XJ9/tree/main/extensions/utils
import asyncio
import datetime as dt
import json
from io import StringIO
from textwrap import dedent

import hikari
import humanize
import lightbulb
import miru
import py_expression_eval
from lightbulb.ext import tasks

from utils import checks, converters, errors, helpers, models, psql
from utils.nav import ItemListBuilder, ModalWithCallback, run_view

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
@lightbulb.command("base-convert", f"[{plugin.name}] Convert a number to the desired base.")
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
@lightbulb.command("calc", f"[{plugin.name}] Calculate a math expression.")
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
@lightbulb.command("embed", f"[{plugin.name}] Send an embed.")
@lightbulb.implements(lightbulb.PrefixCommandGroup, lightbulb.SlashCommandGroup)
async def _embed(ctx: lightbulb.Context):
    raise lightbulb.CommandNotFound(invoked_with = ctx.invoked_with)

@_embed.child
@lightbulb.set_help(dedent('''
    - Consider using https://embedbuilder.nadekobot.me/ to make it easier to visualize.
'''))
@lightbulb.add_cooldown(length = 3.0, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.option("raw_embed", "The embed in JSON format.", modifier = helpers.CONSUME_REST_OPTION)
@lightbulb.command("from-json", f"[{plugin.name}] Send an embed from a JSON object.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def embed_from_json(ctx: lightbulb.Context):
    raw_embed: str = ctx.options.raw_embed
    bot: models.MichaelBot = ctx.bot

    raw_embed = raw_embed.strip("```").strip()
    
    try:
        json_embed = json.loads(raw_embed)
        if not isinstance(json_embed, dict):
            await bot.reset_cooldown(ctx)
            raise json.JSONDecodeError("JSON object must be enclosed in `{{}}`.", doc = raw_embed, pos = 0)
        
        embed = bot.entity_factory.deserialize_embed(json_embed)
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
@lightbulb.command("to-json", f"[{plugin.name}] Take the embed from a message and convert it to a JSON object.")
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
        await bot.reset_cooldown(ctx)
        await ctx.respond("There's no embed in this message!", reply = True, mentions_reply = True)
    else:
        for embed in message.embeds:
            d = bot.entity_factory.serialize_embed(embed)[0]
            
            # Might raise message too long error.
            await ctx.respond(f"```{json.dumps(d, indent = 4)}```")

@_embed.child
@lightbulb.set_help(dedent('''
    - This is an alternative to `embed interactive`.
    - Either `title` or `description` must be non-empty.
'''))
@lightbulb.add_cooldown(length = 3.0, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.option("channel", "The channel to send this embed. Default to the current one.", 
    type = hikari.TextableGuildChannel, 
    channel_types = (hikari.ChannelType.GUILD_TEXT,), 
    default = None
)
@lightbulb.option("color", "Your choice of color. Default to green.", autocomplete = True, default = "green")
@lightbulb.option("description", "The description of the embed.", default = None)
@lightbulb.option("title", "The title of the embed.", default = None)
@lightbulb.command("simple", f"[{plugin.name}] Create and send a simple embed. Useful for quick embeds.")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def embed_simple(ctx: lightbulb.Context):
    title = ctx.options.title
    description = ctx.options.description
    color = ctx.options.color
    channel = ctx.options.channel
    bot: models.MichaelBot = ctx.bot

    if not title and not description:
        await bot.reset_cooldown(ctx)
        await ctx.respond("Embed cannot be empty!", reply = True, mentions_reply = True)
    else:
        if color not in models.DefaultColor.available_names:
            color = "green"
        
        embed = hikari.Embed(
            title = title,
            description = description,
            color = models.DefaultColor.get_color(color)
        )

        if channel is None:
            await ctx.respond(embed = embed)
        else:
            await ctx.respond("Sent!")
            await ctx.bot.rest.create_message(channel, embed = embed)
@embed_simple.autocomplete("color")
async def embed_simple_autocomplete(option: hikari.AutocompleteInteractionOption, _interaction: hikari.AutocompleteInteraction):
    if option.value != "":
        return [color for color in models.DefaultColor.available_names if color.startswith(option.value)]
    return models.DefaultColor.available_names[:25]

@_embed.child
@lightbulb.set_help(dedent('''
    - Bot needs to have `Manage Messages`.
    - This is an alternative to `embed simple`.
'''))
@lightbulb.set_max_concurrency(uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.add_cooldown(length = 10.0, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES))
@lightbulb.command("interactive", f"[{plugin.name}] Create a complex embed with visual prompts.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def embed_interactive(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    embed = hikari.Embed(
        title = "Template Embed",
        description = "Choose one of the below options to edit the embed. Any changes will be reflected on this embed."
    )

    available_colors = models.DefaultColor.available_names
    channel = ctx.get_channel()
    timeout = 120
    
    # This is solely to build the button/select, we'll manually manage the interaction
    # because it'll be very complex and littered with abstractions otherwise.
    # TODO: Add more options.
    view = miru.View()
    view.add_item(miru.Select(
        options = (
            miru.SelectOption(label = "Edit Title", value = "edit_title"),
            miru.SelectOption(label = "Edit Description", value = "edit_description"),
            miru.SelectOption(label = "Add Field", value = "add_field"),
            miru.SelectOption(label = "Remove Field", value = "remove_field"),
            miru.SelectOption(label = "Edit Color", value = "edit_color"),
            miru.SelectOption(label = "Toggle Current Timestamp", value = "toggle_timestamp"),
            miru.SelectOption(label = "Edit Destination", value = "edit_destination"),
        )
    ))
    view.add_item(miru.Button(
        style = hikari.ButtonStyle.SECONDARY,
        label = "Toggle Inline",
        custom_id = "toggle_inline",
    ))
    view.add_item(miru.Button(
        style = hikari.ButtonStyle.SECONDARY,
        label = "Export to JSON",
        custom_id = "export",
        emoji = helpers.get_emote(":printer:")
    ))
    view.add_item(miru.Button(
        style = hikari.ButtonStyle.PRIMARY,
        label = "Send",
        custom_id = "send",
        emoji = helpers.get_emote(":arrow_forward:")
    ))
    
    msg = await ctx.respond(f"Destination: {channel.mention}", embed = embed, components = view.build())
    
    def is_valid_interaction(event: hikari.InteractionCreateEvent) -> bool:
        if not isinstance(event.interaction, hikari.ComponentInteraction):
            return False
        
        if event.interaction.member.id != ctx.author.id:
            return False
        
        # Filter select menu.
        if event.interaction.values:
            return event.interaction.values[0] in (
                "edit_title",
                "edit_description",
                "add_field",
                "remove_field",
                "edit_color",
                "toggle_timestamp",
                "edit_destination",
            )
        # Filter buttons.
        return event.interaction.custom_id in ("toggle_inline", "export", "send")
    
    def is_response(event: hikari.GuildMessageCreateEvent):
        msg = event.message
        return msg.author == ctx.author and msg.channel_id == ctx.channel_id
    
    # TODO: Handle case when the edited embed is ill-formed (empty, max capacity, etc.)
    while True:
        try:
            event = await bot.wait_for(hikari.InteractionCreateEvent, timeout = timeout, predicate = is_valid_interaction)
            interaction: hikari.ComponentInteraction = event.interaction
            # Need to force typing despite already type hint. Good job linter.
            assert isinstance(interaction, hikari.ComponentInteraction)
            
            # User selected menu.
            if interaction.values:
                if interaction.values[0] == "edit_title":
                    title_modal = ModalWithCallback("Edit Title", timeout = timeout)
                    title_modal.add_item(miru.TextInput(
                        label = "What's the title?",
                        placeholder = "Submit nothing will clear this field.", 
                        custom_id = "title_prompt",
                        max_length = 256,
                    ))
                    @title_modal.as_callback
                    async def edit_title(context: miru.ModalContext):
                        response: str = context.get_value_by_id("title_prompt")
                        if response.strip('`') != "":
                            embed.title = response
                        else:
                            embed.title = ""
                        
                        await context.edit_response(embed = embed)
                    await title_modal.send(interaction)                        
                elif interaction.values[0] == "edit_description":
                    description_modal = ModalWithCallback("Edit Description", timeout = timeout)
                    description_modal.add_item(miru.TextInput(
                        label = "What's the description?", 
                        style = hikari.TextInputStyle.PARAGRAPH,
                        placeholder = "Submit nothing will clear this field.",
                        custom_id = "description_prompt", 
                    ))
                    @description_modal.as_callback
                    async def edit_description(context: miru.ModalContext):
                        response: str = context.get_value_by_id("description_prompt")
                        embed.description = response
                        
                        await context.edit_response(embed = embed)
                    
                    await description_modal.send(interaction)
                elif interaction.values[0] == "add_field":
                    if len(embed.fields) >= 25:
                        await interaction.create_initial_response(
                            hikari.ResponseType.MESSAGE_CREATE,
                            "An embed can only have up to 25 fields!",
                            flags = hikari.MessageFlag.EPHEMERAL,
                        )
                        continue
                    
                    add_field_modal = ModalWithCallback("Add Field", timeout = timeout)
                    add_field_modal.add_item(miru.TextInput(
                        label = "What's the field's name?",
                        required = True,
                        max_length = 256,
                        custom_id = "add_field_name_prompt",
                    )).add_item(miru.TextInput(
                        label = "What's the field's value?",
                        style = hikari.TextInputStyle.PARAGRAPH,
                        required = True,
                        max_length = 1024,
                        custom_id = "add_field_value_prompt",
                    ))
                    # Modal doesn't have a checkbox option so we can't use it to toggle inline unfortunately.
                    # Inline will need to be set by a separate button and not in this modal.
                    @add_field_modal.as_callback
                    async def add_field(context: miru.ModalContext):
                        response_name: str = context.get_value_by_id("add_field_name_prompt")
                        response_value: str = context.get_value_by_id("add_field_value_prompt")
                        embed.add_field(response_name, response_value)
                        
                        await context.edit_response(embed = embed)
                    
                    await add_field_modal.send(interaction)
                elif interaction.values[0] == "remove_field":
                    if not embed.fields:
                        await interaction.create_initial_response(
                            hikari.ResponseType.MESSAGE_CREATE,
                            "There's no field to remove!",
                            flags = hikari.MessageFlag.EPHEMERAL,
                        )
                        continue
                    
                    def interaction_filter(event: hikari.InteractionCreateEvent):
                        if not isinstance(event.interaction, hikari.ComponentInteraction):
                            return False
                        
                        if event.interaction.member.id != ctx.author.id:
                            return False
                        
                        if not event.interaction.values:
                            return False
                        return event.interaction.custom_id == str(interaction.id)
                        
                    # Since max field of embed is 25, we can use a select menu.
                    remove_field_view = miru.View()
                    remove_field_options = []
                    for index, field in enumerate(embed.fields):
                        remove_field_options.append(miru.SelectOption(
                            label = field.name,
                            value = str(index),
                        ))
                    # We're using interaction's id to make sure it's unique.
                    remove_field_view.add_item(miru.Select(
                        options = remove_field_options,
                        custom_id = f"{interaction.id}",
                        placeholder = "Select a field to remove.",
                    ))
                    await interaction.create_initial_response(
                        hikari.ResponseType.MESSAGE_CREATE,
                        "Which field to remove?",
                        components = remove_field_view.build(),
                        flags = hikari.MessageFlag.EPHEMERAL,
                    )
                    remove_field_event = await bot.wait_for(hikari.InteractionCreateEvent, timeout = timeout, predicate = interaction_filter)
                    remove_field_inter: hikari.ComponentInteraction = remove_field_event.interaction
                    assert remove_field_inter.values
                    
                    if remove_field_inter.values:
                        # Since we use only integers, there's no way this raises ValueError.
                        remove_index = int(remove_field_inter.values[0])
                        embed.remove_field(remove_index)
                    
                    await remove_field_inter.create_initial_response(hikari.ResponseType.MESSAGE_UPDATE)
                    await msg.edit(embed = embed)
                    await interaction.delete_initial_response()
                elif interaction.values[0] == "edit_color":
                    # The prompt for color is too long, so we can't fit it in a modal. Unfortunate.
                    await interaction.create_initial_response(
                        hikari.ResponseType.MESSAGE_CREATE,
                        f"What's the color? You can enter a hex number or one of the following predefined colors: `{', '.join(available_colors)}`",
                        flags = hikari.MessageFlag.EPHEMERAL
                    )

                    try:
                        setter_event = await bot.wait_for(hikari.GuildMessageCreateEvent, timeout = timeout, predicate = is_response)
                        color_content = setter_event.message.content.lower()

                        if color_content in available_colors:
                            embed.color = models.DefaultColor.get_color(color_content)
                        else:
                            try:
                                embed.color = hikari.Color(int(color_content, base = 16))
                            except ValueError:
                                pass
                        
                        await msg.edit(embed = embed)
                        await setter_event.message.delete()
                    except asyncio.TimeoutError:
                        await interaction.edit_initial_response(f"`{interaction.custom_id}` session expired.")
                        await asyncio.sleep(5)
                    await interaction.delete_initial_response()
                elif interaction.values[0] == "toggle_timestamp":
                    if not embed.timestamp:
                        embed.timestamp = dt.datetime.now().astimezone()
                    else:
                        embed.timestamp = None
                    
                    await interaction.create_initial_response(hikari.ResponseType.MESSAGE_UPDATE)
                    await msg.edit(embed = embed)
                elif interaction.values[0] == "edit_destination":
                    # The reason we don't use modal is because it's easier for user to input channel from default Discord messages.
                    # I'll keep this code here just in case Discord change modal input.

                    #async def edit_destination(context: miru.ModalContext):
                    #    response: str = context.get_value_by_id("destination_prompt")
                    #    if response:
                    #        channel = await lightbulb.TextableGuildChannelConverter(ctx).convert(response)
                    #        if channel is None:
                    #            channel = ctx.get_channel()
                    #    
                    #    await context.edit_response(f"Destination: {channel.mention}")
                    #
                    #destination_modal = ModalWithCallback("Edit Destination", callback = edit_destination, timeout = timeout)
                    #destination_modal.add_item(miru.TextInput(
                    #    label = "Which channel to send this embed?",
                    #    placeholder = "Submit nothing will set destination to this channel.",
                    #    custom_id = "destination_prompt",
                    #))
                    #await destination_modal.send(interaction)
                    
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
                        await asyncio.sleep(5)
                    await interaction.delete_initial_response()
            elif interaction.custom_id == "toggle_inline":
                if not embed.fields:
                    await interaction.create_initial_response(
                        hikari.ResponseType.MESSAGE_CREATE,
                        "This button only works when the embed has at least one field.",
                        flags = hikari.MessageFlag.EPHEMERAL,
                    )
                    continue
                
                last_field = embed.fields[-1]
                embed.edit_field(-1, inline = not last_field.is_inline)
                await interaction.create_initial_response(hikari.ResponseType.MESSAGE_UPDATE)
                await msg.edit(embed = embed)
            elif interaction.custom_id == "export":
                d = bot.entity_factory.serialize_embed(embed)[0]
                d_text = json.dumps(str(d), indent = 4)
                if len(d_text) > 2000:
                    await interaction.create_initial_response(
                        hikari.ResponseType.MESSAGE_CREATE,
                        "The content is too large, so I throw them in this file!",
                        attachment = hikari.Bytes(StringIO(d_text), "embed_export.json"),
                        flags = hikari.MessageFlag.EPHEMERAL,
                    )
                else:
                    await interaction.create_initial_response(
                        hikari.ResponseType.MESSAGE_CREATE,
                        f"```{d_text}```",
                        flags = hikari.MessageFlag.EPHEMERAL,
                    )
            elif interaction.custom_id == "send":
                # No need to response to the interaction if we just delete the message.
                await bot.rest.create_message(channel, embed = embed)
                await msg.delete()
                return
        except asyncio.TimeoutError:
            await msg.edit("Session expired.", embeds = None, components = None)
            return

async def do_remind(bot: models.MichaelBot, user_id: int, message: str, when: dt.datetime = None, remind_id: int = None):
    '''Send `user_id` a DM about `message` at time `when`.

    If it's not possible to send the reminder, this function will ignore the reminder. However, if the user can't be found, it'll delete the reminder.

    Warnings
    --------
    This should be created as a `Task` to avoid logic-blocking (the code itself is not async-blocking).

    Parameters
    ----------
    bot : models.MichaelBot
        The bot instance.
    user_id : int
        The user's id to send the reminder to.
    message : str
        The message to remind.
    when : dt.datetime, optional
        The UTC (tz aware) time to send the reminder. If `None`, the message is sent virtually immediately.
    remind_id : int, optional
        The reminder's id to delete once the reminder is sent. Use `None` if the reminder is created in-memory instead of on external storage.
    '''

    if when is not None:
        await helpers.sleep_until(when)
    
    try:
        user = bot.cache.get_user(user_id)
        if user is None:
            user = await bot.rest.fetch_user(user_id)
        
        await user.send(f"Hi there! You told me to remind you about:\n{message}")

        if remind_id is not None:
            async with bot.pool.acquire() as conn:
                await psql.Reminders.delete_reminder(conn, remind_id, user_id)
    except hikari.BadRequestError:
        # Remove reminder if user is not found.
        print(f"User {user_id} doesn't exist. Removing this reminder...")
        async with bot.pool.acquire() as conn:
            await psql.Reminders.delete_reminder(conn, remind_id, user_id)
    except hikari.ForbiddenError:
        # Don't remove reminder if the sending fails, will retry to send on next refresh cycle.
        # Although this most likely to be a block or sth, so maybe remove it once we know what happens to cause this error.

        # This code is to remove reminders that stuck because of ForbiddenError.
        #if when is not None:
        #    current = dt.datetime.now().astimezone()
        #    if (current - when).total_seconds() > 3600 * 24 * 30:
        #        print(f"Reminder {remind_id} for {user_id} is too old. Removing this reminder...")
        #        async with bot.pool.acquire() as conn:
        #            await psql.Reminders.delete_reminder(conn, remind_id, user_id)
        pass
@tasks.task(s = NOTIFY_REFRESH, auto_start = True, pass_app = True, wait_before_execution = True)
async def scan_reminders(bot: models.MichaelBot):
    '''Check for past and future reminders every `NOTIFY_REFRESH` seconds.

    - If there are any past reminders (tried to send, but couldn't due to permissions, disconnect, etc.), it'll try sending them again.
    - If there are any future reminders within `NOTIFY_REFRESH` seconds, it'll create `do_remind()` task to be launched.

    Parameters
    ----------
    bot : models.MichaelBot
        The bot instance.
    '''

    if bot.pool is None: return

    current = dt.datetime.now().astimezone()
    future = current + dt.timedelta(seconds = NOTIFY_REFRESH)

    async with bot.pool.acquire() as conn:
        passed = await psql.Reminders.get_past_reminders(conn, current)
        upcoming = await psql.Reminders.get_reminders(conn, current, future)
    
    for missed_reminder in passed:
        bot.create_task(do_remind(bot, missed_reminder.user_id, missed_reminder.message, None, missed_reminder.remind_id))
    
    for upcoming_reminder in upcoming:
        bot.create_task(do_remind(bot, upcoming_reminder.user_id, upcoming_reminder.message, upcoming_reminder.awake_time, upcoming_reminder.remind_id))

@plugin.command()
@lightbulb.set_help(dedent('''
    - This command only works with subcommands.
'''))
@lightbulb.command("remindme", f"[{plugin.name}] Create a reminder. Make sure your DM is open to the bot.", hidden = True, aliases = ["rmd", "notify", "timer"])
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
@lightbulb.command("create", f"[{plugin.name}] Create a reminder. Make sure your DM is open to the bot.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def remind_create(ctx: lightbulb.Context):
    interval: dt.timedelta = ctx.options.interval
    bot: models.MichaelBot = ctx.bot

    if isinstance(ctx, lightbulb.SlashContext):
        try:
            interval = await converters.IntervalConverter(ctx).convert(ctx.options.interval)
        except Exception as exc:
            raise lightbulb.ConverterFailure("Conversion failed for option interval.", opt = ctx.invoked.options["interval"], raw = ctx.options.interval) from exc

    when: dt.datetime = dt.datetime.now().astimezone() + interval
    if interval.total_seconds() < 60:
        await ctx.respond("The interval is too small. Must be at least 1 minute.", reply = True, mentions_reply = True)
    elif interval.total_seconds() > 30 * 24 * 60 * 60:
        await ctx.respond("The interval is too large. Must be at most 30 days.", reply = True, mentions_reply = True)
    elif interval.total_seconds() < NOTIFY_REFRESH:
        bot.create_task(do_remind(bot, ctx.author.id, ctx.options.message, when))
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
@lightbulb.command("view", f"[{plugin.name}] View all your long reminders.")
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
        
        @builder.set_page_start_formatter
        def start_format(_, __):
            embed = helpers.get_default_embed(
                title = "Reminders",
                description = "",
                author = ctx.author,
                timestamp = dt.datetime.now().astimezone()
            )
            embed.description = "**Format:** `remind_id`. Reminder message - 0h0m\n\n"
            return embed
        
        @builder.set_entry_formatter
        def entry_format(embed: hikari.Embed, _: int, item: psql.Reminders):
            message = item.message
            if len(item.message) > 30:
                message = item.message[:27] + "..."
            
            time_till_awake: dt.timedelta = item.awake_time - dt.datetime.now().astimezone()
            embed.description += f"`{item.remind_id}`. {message} - {humanize.precisedelta(time_till_awake, 'minutes', format = '%0.0f')}\n"
        
        await run_view(builder.build(), ctx)

@remind.child
@lightbulb.set_help(dedent('''
    - Due to optimization, this command won't remove short reminders.
'''))
@lightbulb.add_cooldown(length = 5.0, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.option("remind_id", "The reminder's id. You can find it in `remindme view`.", type = int)
@lightbulb.command("remove", f"[{plugin.name}] Remove a long reminder.")
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
@lightbulb.command("urban", f"[{plugin.name}] Search a term on urbandictionary.")
@lightbulb.implements(lightbulb.PrefixCommand)
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
@lightbulb.command("weather", f"[{plugin.name}] Display weather information for a location.")
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
                embed.color = models.DefaultColor.gold
            else:
                embed.color = models.DefaultColor.dark_blue

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
