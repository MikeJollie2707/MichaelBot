# API commands are inspired by: https://github.com/kamfretoz/XJ9/tree/main/extensions/utils
import lightbulb
import hikari
import humanize
from lightbulb.ext import tasks

import datetime as dt
from textwrap import dedent

import utils.checks as checks
import utils.converters as converters
import utils.errors as errors
import utils.helpers as helpers
import utils.models as models
import utils.psql as psql
from utils.navigator import ItemListBuilder

NOTIFY_REFRESH = 2 * 60

plugin = lightbulb.Plugin(name = "Utilities", description = "Utility Commands", include_datastore = True)
plugin.d.emote = helpers.get_emote(":gear:")
plugin.add_checks(checks.is_command_enabled, lightbulb.bot_has_guild_permissions(*helpers.COMMAND_STANDARD_PERMISSIONS))

@plugin.command()
@lightbulb.option("member", "A Discord member. Default to you.", type = hikari.Member, default = None)
@lightbulb.command("profile", "Information about yourself or another member.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def profile(ctx: lightbulb.Context):
    member: hikari.Member = ctx.options.member

    if member is None:
        # ctx.author returns a User instead of a Member.
        member = ctx.member
    
    embed = helpers.get_default_embed(
        timestamp = dt.datetime.now().astimezone(),
        author = ctx.author
    ).set_author(
        name = member.username,
        icon = member.avatar_url
    ).add_field(
        name = "Username:",
        value = member.username,
        inline = True
    ).add_field(
        name = "Nickname:",
        value = member.nickname if member.nickname is not None else member.username,
        inline = True
    ).add_field(
        name = "Avatar URL:",
        value = f"[Click here]({member.avatar_url})",
        inline = True
    ).set_thumbnail(
        member.avatar_url
    )

    account_age: str = humanize.precisedelta(dt.datetime.now().astimezone() - member.created_at, format = '%0.0f')
    embed.add_field(name = "Joined Discord for:", value = account_age, inline = False)
    member_age: str = humanize.precisedelta(dt.datetime.now().astimezone() - member.joined_at, format = '%0.0f')
    embed.add_field(name = f"Joined {ctx.get_guild().name} for:", value = member_age, inline = False)

    roles = [helpers.mention(role) for role in member.get_roles()]
    s = " - "
    s = s.join(roles)
    embed.add_field(name = "Roles:", value = s, inline = False)

    await ctx.respond(embed, reply = True)

@plugin.command()
@lightbulb.command("server-info", "Information about this server.", aliases = ["serverinfo"])
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def server_info(ctx: lightbulb.Context):
    guild = ctx.get_guild()
    embed = helpers.get_default_embed(
        description = "**Information about this server.**",
        timestamp = dt.datetime.now().astimezone()
    ).set_thumbnail(guild.icon_url).set_author(name = guild.name, icon = guild.icon_url)

    embed.add_field(
        name = "Name",
        value = guild.name,
        inline = True
    ).add_field(
        name = "Created On",
        value = guild.created_at.strftime("%b %d %Y"),
        inline = True
    ).add_field(
        name = "Owner",
        value = (await guild.fetch_owner()).mention,
        inline = True
    ).add_field(
        name = "Roles",
        value = str(len(guild.get_roles())) + " roles.",
        inline = True
    )

    guild_channel_count = {
        "text": 0,
        "voice": 0,
        "stage": 0,
        "category": 0,
        "news": 0,
    }
    channels = guild.get_channels()
    for channel_id in channels:
        if channels[channel_id].type == hikari.ChannelType.GUILD_TEXT:
            guild_channel_count["text"] += 1
        elif channels[channel_id].type == hikari.ChannelType.GUILD_VOICE:
            guild_channel_count["voice"] += 1
        elif channels[channel_id].type == hikari.ChannelType.GUILD_STAGE:
            guild_channel_count["stage"] += 1
        elif channels[channel_id].type == hikari.ChannelType.GUILD_CATEGORY:
            guild_channel_count["category"] += 1
        elif channels[channel_id].type == hikari.ChannelType.GUILD_NEWS:
            guild_channel_count["news"] += 1
    embed.add_field(
        name = "Channels",
        value = dedent(f'''
                Text Channels: {guild_channel_count["text"]}
                Voice Channels: {guild_channel_count["voice"]}
                Categories: {guild_channel_count["category"]}
                Stage Channels: {guild_channel_count["stage"]}
                News Channels: {guild_channel_count["news"]}
                '''),
        inline = True
    )

    bot_count = 0
    members = guild.get_members()
    for member_id in members:
        if members[member_id].is_bot:
            bot_count += 1
    
    embed.add_field(
        name = "Members Count",
        value = dedent(f'''
                Total: {len(members)}
                Humans: {len(members) - bot_count}
                Bots: {bot_count}
                '''),
        inline = True
    )

    embed.set_footer(f"Server ID: {guild.id}")

    await ctx.respond(embed = embed, reply = True)

@plugin.command()
@lightbulb.option("role", "A Discord role.", type = hikari.Role)
@lightbulb.command("role-info", "Information about a role in this server.", aliases = ["roleinfo"])
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def role_info(ctx: lightbulb.Context):
    role: hikari.Role = ctx.options.role

    embed = hikari.Embed(
        description = "**Information about this role.**",
        color = role.color,
        timestamp = dt.datetime.now().astimezone()
    ).set_author(
        name = ctx.get_guild().name,
        icon = ctx.get_guild().icon_url   
    ).add_field(
        name = "Name",
        value = role.name,
        inline = True
    ).add_field(
        name = "Created On",
        value = role.created_at.strftime("%b %d %Y"),
        inline = True
    ).add_field(
        name = "Color",
        value = f"{role.color.hex_code}",
        inline = True
    )

    special = []
    if role.is_hoisted:
        special.append("`Hoisted`")
    if role.is_mentionable:
        special.append("`Mentionable`")
    if role.is_managed:
        special.append("`Integrated`")
    if role.is_premium_subscriber_role:
        special.append("`Nitro Boost Exclusive`")
    if len(special) > 0:
        embed.add_field(
            name = "Special Perks",
            value = ", ".join(special)
        )
    
    count = 0
    members = ctx.get_guild().get_members()
    for id in members:
        if role in members[id].get_roles():
            count += 1
    
    embed.add_field(
        name = "Members",
        value = f"{count} members."
    )
    embed.set_footer(
        text = f"Role ID: {role.id}"
    )

    await ctx.respond(embed = embed, reply = True)

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
        await user.send("Hi there! You told me to remind you about:\n" + message)

        if remind_id is not None:
            async with bot.pool.acquire() as conn:
                await psql.Reminders.remove_reminder(conn, user.id, remind_id)
    except hikari.ForbiddenError:
        # Don't remove reminder if the sending fails, will retry to send on next refresh cycle.
        pass
@plugin.command()
@lightbulb.set_help(dedent('''
    This command only works with subcommands.
'''))
@lightbulb.command("remindme", "Create a reminder. Make sure your DM is open to the bot.", hidden = True, aliases = ["rmd", "notify", "timer"])
@lightbulb.implements(lightbulb.PrefixCommandGroup, lightbulb.SlashCommandGroup)
async def remind(ctx: lightbulb.Context):
    raise lightbulb.CommandNotFound(invoked_with = ctx.invoked_with)

@remind.child
@lightbulb.set_help(dedent(f'''
    An interval of less than {NOTIFY_REFRESH} seconds is considered to be a "short reminder".
'''))
@lightbulb.add_cooldown(length = 5.0, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.option("message", "The message the bot will send after the interval.", modifier = helpers.CONSUME_REST_OPTION)
@lightbulb.option("interval", "How long until the bot reminds you. Must be between 1 minute and 30 days. Example: 3d2m1s", type = converters.IntervalConverter)
@lightbulb.command("create", "Create a reminder. Make sure your DM is open to the bot.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def remind_create(ctx: lightbulb.Context):
    interval: dt.timedelta = ctx.options.interval
    bot: models.MichaelBot = ctx.bot

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
            await psql.Reminders.add_reminder(conn, ctx.author.id, when, ctx.options.message)
        await ctx.respond(f"I'll remind you about '{ctx.options.message}' in `{humanize.precisedelta(interval, format = '%0.0f')}`.", reply = True)

@remind.child
@lightbulb.set_help(dedent('''
    Due to optimization, this command won't display short reminders.
'''))
@lightbulb.add_cooldown(length = 5.0, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.command("view", "View all your long reminders.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def remind_view(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

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
        def start_format(index, item):
            embed = helpers.get_default_embed(
                title = "Reminders",
                description = "",
                author = ctx.author,
                timestamp = dt.datetime.now().astimezone()
            )
            return embed
        def entry_format(embed, index, item):
            message = item["message"]
            if len(item["message"]) > 30:
                message = item["message"][:27] + "..."
            
            time_till_awake: dt.timedelta = item["awake_time"] - dt.datetime.now().astimezone()
            embed.description += f"{index + 1}. {message} - {humanize.precisedelta(time_till_awake, 'minutes', format = '%0.0f')}\n"
        
        builder.set_page_start_formatter(start_format)
        builder.set_entry_formatter(entry_format)
        await builder.build().run(ctx)

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
        bot.create_task(do_remind(bot, user, missed_reminder["message"], current, missed_reminder["remind_id"]))
    
    for upcoming_reminder in upcoming:
        user = bot.cache.get_user(upcoming_reminder["user_id"])
        bot.create_task(do_remind(bot, user, upcoming_reminder["message"], upcoming_reminder["awake_time"], upcoming_reminder["remind_id"]))

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
            await ctx.respond("Something went wrong.", reply = True, mentions_reply = True)
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
    if api_key is None:
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
                text = f"Powered by: weatherapi.com",
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
                embed.color = models.DefaultColor.gold()
            else:
                embed.color = models.DefaultColor.dark_blue()

            await ctx.respond(embed = embed, reply = True)
        elif resp.status == 400:
            await ctx.respond("City not found.", reply = True, mentions_reply = True)
        else:
            resp_json = await resp.json()
            await ctx.respond(f"Weather API return the following error: `{resp_json['error']['message']}`", reply = True, mentions_reply = True)
            raise errors.CustomAPIFailed(f"Endpoint {BASE_URL + '/current.json'} returned with status {resp.status}. Raw response: {await resp.text()}")

def load(bot: models.MichaelBot):
    bot.add_plugin(plugin)
def unload(bot: models.MichaelBot):
    bot.remove_plugin(plugin)
