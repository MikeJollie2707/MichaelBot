import lightbulb
import hikari
import humanize

import datetime as dt
import typing as t
from textwrap import dedent

import utilities.helpers as helpers
from utilities.navigator import ButtonPages

plugin = lightbulb.Plugin("Core", description = "General Commands", include_datastore = True)
plugin.d.emote = helpers.get_emote(":gear:")

@plugin.command()
@lightbulb.command("changelog", "Show 10 latest changes to the bot.")
@lightbulb.implements(lightbulb.PrefixCommandGroup, lightbulb.SlashCommandGroup)
async def changelog_base(ctx: lightbulb.Context):
    '''
    Show 10 latest changes to the bot.
    '''
    await changelog_stable(ctx)

@changelog_base.child
@lightbulb.command("stable", "Show 10 latest changes to the bot.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def changelog_stable(ctx: lightbulb.Context):
    if isinstance(ctx, lightbulb.PrefixContext):
        await ctx.event.message.delete()

    CHANNEL_ID = 644393721512722432
    channel: hikari.GuildTextChannel = ctx.bot.cache.get_guild_channel(CHANNEL_ID)
    if channel is None:
        return await ctx.respond("Seems like I can't retrieve the change logs. You might wanna report this to the developers.", reply = True, mentions_reply = True)
    
    embeds = []
    async for message in channel.fetch_history().limit(10):
        embeds.append(helpers.get_default_embed(
            description = message.content,
            timestamp = dt.datetime.now().astimezone(),
            author = ctx.author
        ))
    pages = ButtonPages(embeds)
    await pages.run(ctx)

@changelog_base.child
@lightbulb.command("development", "Show 10 latest changes to the bot *behind the scenes*.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def changelog_dev(ctx: lightbulb.Context):
    if isinstance(ctx, lightbulb.PrefixContext):
        await ctx.event.message.delete()

    CHANNEL_ID = 759288597500788766
    channel: hikari.GuildTextChannel = ctx.bot.cache.get_guild_channel(CHANNEL_ID)
    if channel is None:
        return await ctx.respond("Seems like I can't retrieve the change logs. You might wanna report this to the developers.")
    
    embeds = []
    async for message in channel.fetch_history().limit(10):
        embeds.append(helpers.get_default_embed(
            description = message.content,
            timestamp = dt.datetime.now().astimezone(),
            author = ctx.author
        ))
    pages = ButtonPages(embeds)
    await pages.run(ctx)

@plugin.command()
@lightbulb.command("info", "Information about the bot.", aliases = ["about"])
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def info(ctx: lightbulb.Context):
    embed = helpers.get_default_embed(
        title = ctx.bot.get_me().username,
        description = ctx.bot.d.description,
        timestamp = dt.datetime.now().astimezone()
    ).add_field(
        name = "Version:",
        value = ctx.bot.d.version,
        inline = False
    ).add_field(
        name = "Team:",
        value = dedent('''
                **Original Owner + Tester:** <@462726152377860109>
                **Developer:** <@472832990012243969>
                **Web Dev (?):** *Hidden*
                '''),
        inline = False
    ).add_field(
        name = "Bot Info:",
        value = dedent('''
                **Language:** Python
                **Created on:** Jan 10, 2022 (originally Nov 13, 2019)
                **Library:** [hikari](https://github.com/hikari-py/hikari), [hikari-lightbulb](https://github.com/tandemdude/hikari-lightbulb), [Lavalink](https://github.com/freyacodes/Lavalink), [lavaplayer](https://github.com/HazemMeqdad/lavaplayer)
                **Source:** [GitHub](https://github.com/MikeJollie2707/MichaelBot \"MichaelBot\")
                '''),
        inline = False
    ).set_thumbnail(ctx.bot.get_me().avatar_url)

    up_time = dt.datetime.now().astimezone() - ctx.bot.d.online_at
    embed.add_field(
        name = "Host Info:",
        value = dedent(f'''
                **Processor:** Intel Core i3-10100 CPU @ 3.60GHz x 8
                **Memory:** 15.6 GiB of RAM
                **Bot Uptime:** {humanize.precisedelta(up_time, "minutes", format = "%0.0f")}
                '''),
        inline = False
    )

    await ctx.respond(embed = embed, reply = True)

@plugin.command()
@lightbulb.option("member", "A Discord Member.", type = hikari.Member, default = None)
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
@lightbulb.option("reason", "The content you're trying to send.", modifier = helpers.CONSUME_REST_OPTION)
@lightbulb.option("type", "The type of report you're making. Either `bug` or `suggest`.")
@lightbulb.command("report", "Report a bug or suggest a feature for the bot. Please be constructive.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def report(ctx: lightbulb.Context):
    report_type = ctx.options.type
    reason = ctx.options.reason

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
            await ctx.bot.rest.create_message(REPORT_CHANNEL, embed = embed)
            await ctx.respond("Report sent successfully! Thank you.", reply = True)
        except hikari.ForbiddenError:
            await ctx.respond("I can't send the report for some reasons. Join the support server and notify them about this, along with whatever you're trying to send.", reply = True, mentions_reply = True)
    else:
        await ctx.respond("`type` argument must be either `bug` or `suggest`.", reply = True, mentions_reply = True)

@plugin.command()
@lightbulb.command("serverinfo", "Information about this server.", aliases = ["server-info"])
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def serverinfo(ctx: lightbulb.Context):
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

def load(bot):
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
