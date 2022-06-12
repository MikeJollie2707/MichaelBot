'''Bot-related Commands.'''

import datetime as dt
import platform
from textwrap import dedent

import hikari
import humanize
import lightbulb
import psutil

from utils import checks, helpers, models
from utils.nav.navigator import ButtonNavigator, run_view

plugin = lightbulb.Plugin("Bot", description = "Bot-related Commands", include_datastore = True)
plugin.d.emote = helpers.get_emote(":robot:")
plugin.add_checks(checks.is_command_enabled, lightbulb.bot_has_guild_permissions(*helpers.COMMAND_STANDARD_PERMISSIONS))

# https://www.thepythoncode.com/article/get-hardware-system-information-python
def get_memory_size(byte: int, /, suffix: str = "B") -> str:
    '''Scale bytes to its proper format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'

    Args:
        byte (int): Number of bytes to convert.
        suffix (str, optional): The unit of the number. Defaults to "B".

    Returns:
        str: A representation of memory size after condensing.
    '''

    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if byte < factor:
            return f"{byte:.2f}{unit}{suffix}"
        byte /= factor

@plugin.command()
@lightbulb.set_help(dedent('''
    - Bot needs to have `Manage Messages` permission if used as a Prefix Command.
'''))
@lightbulb.add_cooldown(length = 5.0, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.option("option", "Additional options. Valid options are `dev`/`development` and `stable`.", choices = ("dev", "development", "stable"), default = "stable")
@lightbulb.command("changelog", "Show 10 latest changes to the bot.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def changelog(ctx: lightbulb.Context):
    '''
    Show 10 latest changes to the bot.
    '''
    
    bot: models.MichaelBot = ctx.bot

    if isinstance(ctx, lightbulb.PrefixContext):
        await ctx.event.message.delete()

    if ctx.options.option.lower() == "stable":
        CHANNEL_ID = 644393721512722432
    elif ctx.options.option.lower() in ("dev", "development"):
        CHANNEL_ID = 759288597500788766
    else:
        return await ctx.respond("`option` argument must be either `dev`, `development`, or `stable`.", reply = True, mentions_reply = True)
    
    channel: hikari.GuildTextChannel = bot.cache.get_guild_channel(CHANNEL_ID)
    if channel is None:
        return await ctx.respond("Seems like I can't retrieve the change logs. You might wanna report this to the developers.", reply = True, mentions_reply = True)
    
    embeds = []
    async for message in channel.fetch_history().limit(10):
        embeds.append(helpers.get_default_embed(
            description = message.content,
            timestamp = dt.datetime.now().astimezone(),
            author = ctx.author
        ))
    page_nav = ButtonNavigator(pages = embeds)
    await run_view(page_nav, ctx)

@plugin.command()
@lightbulb.option("name", "Category name or command name. Is case-sensitive.", autocomplete = True, default = None, modifier = helpers.CONSUME_REST_OPTION)
@lightbulb.command("help", "Get help information for the bot.", aliases = ['h'])
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def _help(ctx: lightbulb.Context):
    obj = ctx.options.name
    bot: models.MichaelBot = ctx.bot

    if bot.help_command is None:
        raise NotImplementedError("`help` command class doesn't exist.")
    
    await bot.help_command.send_help(ctx, obj)

@_help.autocomplete("name")
async def help_name_autocomplete(option: hikari.AutocompleteInteractionOption, interaction: hikari.AutocompleteInteraction):
    # Use dictionary to ensure unique values.
    valid_match = {}
    bot: models.MichaelBot = interaction.app

    def match_algorithm(name: str, input_value: str):
        return input_value in name
        #return name.startswith(input_value)

    for plg_name, _ in bot.plugins.items():
        if match_algorithm(plg_name.lower(), option.value) and not plg_name.startswith('.'):
            # Just dummy value.
            valid_match[plg_name] = True
    
    # Return categories by default.
    if option.value == '':
        return tuple(valid_match.keys())[:25]
    
    for cmd_name, p_cmd in bot.prefix_commands.items():
        if match_algorithm(cmd_name.lower(), option.value) and not p_cmd.hidden:
            valid_match[cmd_name] = True
    for cmd_name, s_cmd in bot.slash_commands.items():
        if match_algorithm(cmd_name.lower(), option.value) and not s_cmd.hidden:
            valid_match[cmd_name] = True
    for cmd_name, m_cmd in bot.message_commands.items():
        if match_algorithm(cmd_name.lower(), option.value) and not m_cmd.hidden:
            valid_match[cmd_name] = True
    for cmd_name, u_cmd in bot.user_commands.items():
        if match_algorithm(cmd_name.lower(), option.value) and not u_cmd.hidden:
            valid_match[cmd_name] = True
    
    # dict.keys() is not subscriptable.
    if len(valid_match.keys()) > 0:
        return tuple(valid_match.keys())[:25]
    
    return []

@plugin.command()
@lightbulb.command("info", "Show information about the bot.", aliases = ["about"])
@lightbulb.implements(lightbulb.PrefixCommandGroup, lightbulb.SlashCommandGroup)
async def info(ctx: lightbulb.Context):
    await info_bot(ctx)

@info.child
@lightbulb.command("bot", "Show information about the bot.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def info_bot(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    embed = helpers.get_default_embed(
        title = bot.get_me().username,
        description = bot.info["description"],
        timestamp = dt.datetime.now().astimezone(),
        author = ctx.author
    ).add_field(
        name = "Version:",
        value = bot.info["version"],
        inline = False
    ).add_field(
        name = "Team:",
        value = dedent('''
                > **Original Owner + Tester:** <@462726152377860109>
                > **Developer:** <@472832990012243969>
                > **Web Dev (?):** *Hidden*
                '''),
        inline = False
    ).add_field(
        name = "Bot Info:",
        value = dedent('''
                > **Language:** Python
                > **Created on:** Jan 10, 2022 (originally Nov 13, 2019)
                > **Library:** [hikari](https://github.com/hikari-py/hikari), [hikari-lightbulb](https://github.com/tandemdude/hikari-lightbulb), [Lavalink](https://github.com/freyacodes/Lavalink), [lavaplayer](https://github.com/HazemMeqdad/lavaplayer)
                > **Source:** [GitHub](https://github.com/MikeJollie2707/MichaelBot \"MichaelBot\"), [Dashboard](https://github.com/nhxv/discord-bot)
                '''),
        inline = False
    ).set_thumbnail(bot.get_me().avatar_url)

    await ctx.respond(embed = embed, reply = True)

@info.child
@lightbulb.command("host", "Show information about the machine hosting the bot.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def info_host(ctx: lightbulb.Context):
    # Reference: https://www.thepythoncode.com/article/get-hardware-system-information-python
    bot: models.MichaelBot = ctx.bot

    system = platform.system()
    processor = ""
    if system == "Linux":
        processor = "Intel Core i3-10100 @ 3.60GHz"
    elif system == "Windows":
        processor = "Intel Core i7-1165G7 @ 2.80GHz"
    boot_duration = dt.datetime.now().astimezone() - dt.datetime.fromtimestamp(psutil.boot_time()).astimezone()
    up_time = dt.datetime.now().astimezone() - bot.online_at
    ram = psutil.virtual_memory()
    swap = psutil.swap_memory()

    embed = helpers.get_default_embed(
        title = bot.get_me().username,
        description = bot.info["description"],
        timestamp = dt.datetime.now().astimezone(),
        author = ctx.author
    ).add_field(
        name = "General Information",
        value = dedent(f'''
            > **System:** {system}
            > **Processor:** {processor}
            > **Boot Duration:** {humanize.precisedelta(boot_duration, "minutes", format = "%0.0f")}
            > **Bot Uptime:** {humanize.precisedelta(up_time, "minutes", format = "%0.0f")}
        ''')
    ).add_field(
        name = "Python Information",
        value = dedent(f'''
            > **Version:** {platform.python_implementation()} {platform.python_version()}
            > **Compiler:** {platform.python_compiler()}
        ''')
    ).add_field(
        name = "CPU Information",
        value = dedent(f'''
            > **Physical Cores:** {psutil.cpu_count(logical = False)}
            > **Total Cores:** {psutil.cpu_count(logical = True)}
            > **Max Frequency:** {psutil.cpu_freq().max / 1000 :.2f}GHz
            > **Min Frequency:** {psutil.cpu_freq().min / 1000 :.2f}GHz
            > **Total CPU Usage:** {psutil.cpu_percent()}%
        ''')
    ).add_field(
        name = "Memory Information",
        value = dedent(f'''
            > **RAM Usage:** {get_memory_size(ram.used)}/{get_memory_size(ram.total)} ({ram.percent}%)
            > **Swap Usage:** {get_memory_size(swap.used)}/{get_memory_size(swap.free)} ({swap.percent}%)
        ''')
    ).set_thumbnail(bot.get_me().avatar_url)

    await ctx.respond(embed = embed, reply = True)

@info.child
@lightbulb.option("member", "A Discord member. Default to yourself.", type = hikari.Member, default = None)
@lightbulb.command("member", "Show information about yourself or another member.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def info_member(ctx: lightbulb.Context):
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

    account_age: str = humanize.precisedelta(dt.datetime.now().astimezone() - member.created_at, minimum_unit = "minutes", format = '%0.0f')
    embed.add_field(name = "Joined Discord for:", value = account_age, inline = False)
    member_age: str = humanize.precisedelta(dt.datetime.now().astimezone() - member.joined_at, minimum_unit = "minutes", format = '%0.0f')
    embed.add_field(name = f"Joined {ctx.get_guild().name} for:", value = member_age, inline = False)

    roles = [helpers.mention(role) for role in member.get_roles()]
    s = " - "
    s = s.join(roles)
    embed.add_field(name = "Roles:", value = s, inline = False)

    await ctx.respond(embed, reply = True)

@info.child
@lightbulb.option("role", "A Discord role.", type = hikari.Role)
@lightbulb.command("role", "Show information about a role.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def info_role(ctx: lightbulb.Context):
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
    for member_id in members:
        if role in members[member_id].get_roles():
            count += 1
    
    embed.add_field(
        name = "Members",
        value = f"{count} members."
    )
    embed.set_footer(
        text = f"Role ID: {role.id}"
    )

    await ctx.respond(embed = embed, reply = True)

@info.child
@lightbulb.command("server", "Information about this server.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def info_server(ctx: lightbulb.Context):
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
        value = f"{len(guild.get_roles())} roles.",
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
@lightbulb.command("ping", "Check the bot if it's alive")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def ping(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    latency = bot.heartbeat_latency
    
    import time
    start = time.perf_counter()
    m = await ctx.respond("Never gonna give you up.", reply = True)
    end = time.perf_counter()

    embed = helpers.get_default_embed(
        description = "Pong! :ping_pong:",
        author = ctx.author,
        timestamp = dt.datetime.now().astimezone()
    )
    embed.add_field(
        name = "Gateway",
        value = f"{latency * 1000:.2f}ms",
        inline = True
    ).add_field(
        name = "REST",
        value = f"{(end - start) * 1000:.2f}ms",
        inline = True
    )
    await m.edit(content = None, embed = embed, mentions_reply = True)

@plugin.command()
@lightbulb.set_help(dedent('''
    - Author needs to have `Manage Messages`.
'''))
@lightbulb.add_checks(checks.is_db_connected, lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_GUILD))
@lightbulb.add_cooldown(length = 5.0, uses = 1, bucket = lightbulb.GuildBucket)
@lightbulb.option("new_prefix", "The new prefix. Should not be longer than 5 characters or contain spaces.", default = None)
@lightbulb.command("prefix", "View or edit the bot prefix for the guild. This only affects Prefix Commands.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def prefix(ctx: lightbulb.Context):
    new_prefix = ctx.options.new_prefix
    bot: models.MichaelBot = ctx.bot

    guild_dbcache = bot.guild_cache.get(ctx.guild_id)
    
    if new_prefix is None:
        guild_prefix = bot.info["prefix"] if guild_dbcache is None else guild_dbcache.guild_module["prefix"]
        await ctx.respond(f"Current prefix: `{guild_prefix}`", reply = True)
    else:
        if len(new_prefix) > 5 or len(new_prefix.split(' ')) > 1:
            await ctx.respond("Invalid prefix.", reply = True, mentions_reply = True)
            return
        async with bot.pool.acquire() as conn:
            async with conn.transaction():
                await guild_dbcache.update_guild_module(conn, ctx.guild_id, "prefix", new_prefix)
        await ctx.respond(f"Successfully set new prefix as `{new_prefix}`.")

@plugin.command()
@lightbulb.set_help(dedent('''
    - It is recommended to use the `Slash Command` version of this command.
'''))
@lightbulb.add_cooldown(length = 5.0, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.option("reason", "The content you're trying to send.", modifier = helpers.CONSUME_REST_OPTION)
@lightbulb.option("type", "The type of report you're making. Either `bug` or `suggest`.", choices = ["bug", "suggest"])
@lightbulb.command("report", "Report a bug or suggest a feature for the bot. Please be constructive.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def report(ctx: lightbulb.Context):
    report_type = ctx.options.type
    reason = ctx.options.reason
    bot: models.MichaelBot = ctx.bot

    REPORT_CHANNEL = 644339079164723201
    if report_type.upper() == "BUG" or report_type.upper() == "SUGGEST":
        embed = helpers.get_default_embed(
            title = report_type.capitalize(),
            description = reason,
            timestamp = dt.datetime.now().astimezone()
        ).set_author(
            name = ctx.author.username,
            icon = ctx.author.avatar_url
        ).set_footer(
            text = f"Sender ID: {ctx.author.id}"
        )

        try:
            msg = await bot.rest.create_message(REPORT_CHANNEL, embed = embed)
            if report_type.upper() == "SUGGEST":
                await bot.rest.add_reaction(msg.channel_id, msg, helpers.get_emote(":thumbs_up:"))
                await bot.rest.add_reaction(msg.channel_id, msg, helpers.get_emote(":thumbs_down:"))
            await ctx.respond("Report sent successfully! Thank you.", reply = True)
        except hikari.ForbiddenError:
            await ctx.respond("I can't send the report for some reasons. Join the support server and notify them about this, along with whatever you're trying to send.", reply = True, mentions_reply = True)
    else:
        await ctx.respond("`type` argument must be either `bug` or `suggest`.", reply = True, mentions_reply = True)

def load(bot: lightbulb.BotApp):
    bot.add_plugin(plugin)
def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(plugin)
