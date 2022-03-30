import lightbulb
import hikari
import humanize

import datetime as dt
from textwrap import dedent

import utilities.checks as checks
import utilities.helpers as helpers
import utilities.models as models
from utilities.navigator import ButtonPages

plugin = lightbulb.Plugin("Bot", description = "Bot-related Commands", include_datastore = True)
plugin.d.emote = helpers.get_emote(":robot:")
plugin.add_checks(checks.is_command_enabled, lightbulb.bot_has_guild_permissions(*helpers.COMMAND_STANDARD_PERMISSIONS))

@plugin.command()
@lightbulb.command("changelog", "Show 10 latest changes to the bot.")
@lightbulb.implements(lightbulb.PrefixCommandGroup, lightbulb.SlashCommandGroup)
async def changelog_base(ctx: lightbulb.Context):
    '''
    Show 10 latest changes to the bot.
    '''
    await changelog_stable(ctx)

@changelog_base.child
@lightbulb.command("stable", "Show 10 latest changes to the bot.", inherit_checks = True)
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
@lightbulb.command("development", "Show 10 latest changes to the bot *behind the scenes*.", inherit_checks = True)
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
@lightbulb.command("info", "Show information about the bot.", aliases = ["about"])
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def info(ctx: lightbulb.Context):
    embed = helpers.get_default_embed(
        title = ctx.bot.get_me().username,
        description = ctx.bot.d.bot_info["description"],
        timestamp = dt.datetime.now().astimezone()
    ).add_field(
        name = "Version:",
        value = ctx.bot.d.bot_info["version"],
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
                **Source:** [GitHub](https://github.com/MikeJollie2707/MichaelBot \"MichaelBot\"), [Dashboard](https://github.com/nhxv/discord-bot)
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
@lightbulb.command("ping", "Check the bot if it's alive")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def ping(ctx: lightbulb.Context):
    latency = ctx.bot.heartbeat_latency
    await ctx.respond(f"Pong! :ping_pong: {format(latency * 1000, '.2f')}ms.", reply = True, mentions_reply = True)

@plugin.command()
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_GUILD))
@lightbulb.option("new_prefix", "New prefix", default = None)
@lightbulb.command("prefix", "View or edit the bot prefix for the guild. This only affects Prefix Commands.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def prefix(ctx: lightbulb.Context):
    new_prefix = ctx.options.new_prefix
    guild_dbcache = models.get_guild_cache(ctx.bot, ctx.guild_id)
    
    if new_prefix is None:
        guild_prefix = ctx.bot.d.bot_info["prefix"] if guild_dbcache is None else guild_dbcache.guild_module["prefix"]
        await ctx.respond(f"Current prefix: `{guild_prefix}`", reply = True)
    else:
        async with ctx.bot.d.pool.acquire() as conn:
            async with conn.transaction():
                await guild_dbcache.update_guild_module(conn, ctx.guild_id, "prefix", new_prefix)
        await ctx.respond(f"Successfully set new prefix as `{new_prefix}`.")

@plugin.command()
@lightbulb.option("reason", "The content you're trying to send.", modifier = helpers.CONSUME_REST_OPTION)
@lightbulb.option("type", "The type of report you're making. Either `bug` or `suggest`.", default = "bug")
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

def load(bot: lightbulb.BotApp):
    bot.add_plugin(plugin)
def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(plugin)
