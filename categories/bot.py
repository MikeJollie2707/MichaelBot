import lightbulb
import hikari
import humanize

import datetime as dt
from textwrap import dedent

import utils.checks as checks
import utils.helpers as helpers
import utils.models as models
from utils.navigator import ButtonPages

plugin = lightbulb.Plugin("Bot", description = "Bot-related Commands", include_datastore = True)
plugin.d.emote = helpers.get_emote(":robot:")
plugin.add_checks(checks.is_command_enabled, lightbulb.bot_has_guild_permissions(*helpers.COMMAND_STANDARD_PERMISSIONS))

@plugin.command()
@lightbulb.set_help(dedent('''
    Bot needs to have `Manage Messages` permission if used as a Prefix Command.
'''))
@lightbulb.add_cooldown(length = 5.0, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.option("option", "Additional options. Valid options are `dev`/`development` and `stable`.", default = "stable")
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
        CHANNEL_ID = 759288597500788766
    elif ctx.options.option.lower() in ("dev", "development"):
        CHANNEL_ID = 644393721512722432
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
    pages = ButtonPages(embeds)
    await pages.run(ctx)

@plugin.command()
@lightbulb.option("name", "Category name or command name. Is case-sensitive.", default = None, modifier = helpers.CONSUME_REST_OPTION)
@lightbulb.command("help", "Get help information for the bot.", aliases = ['h'], auto_defer = True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def help(ctx: lightbulb.Context):
    obj = ctx.options.name
    bot: models.MichaelBot = ctx.bot

    if bot.help_command is None:
        raise NotImplementedError("`help` command class doesn't exist.")
    
    await bot.help_command.send_help(ctx, obj)

@plugin.command()
@lightbulb.command("info", "Show information about the bot.", aliases = ["about"])
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def info(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    embed = helpers.get_default_embed(
        title = bot.get_me().username,
        description = bot.info["description"],
        timestamp = dt.datetime.now().astimezone()
    ).add_field(
        name = "Version:",
        value = bot.info["version"],
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
    ).set_thumbnail(bot.get_me().avatar_url)

    up_time = dt.datetime.now().astimezone() - bot.online_at
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
    Author needs to have `Manage Messages`.
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
    It is recommended to use the `Slash Command` version of this command.
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
            await bot.rest.create_message(REPORT_CHANNEL, embed = embed)
            await ctx.respond("Report sent successfully! Thank you.", reply = True)
        except hikari.ForbiddenError:
            await ctx.respond("I can't send the report for some reasons. Join the support server and notify them about this, along with whatever you're trying to send.", reply = True, mentions_reply = True)
    else:
        await ctx.respond("`type` argument must be either `bug` or `suggest`.", reply = True, mentions_reply = True)

def load(bot: lightbulb.BotApp):
    bot.add_plugin(plugin)
def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(plugin)
