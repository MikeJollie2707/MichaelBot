import lightbulb
import hikari

import random

import utilities.helpers as helpers
import utilities.checks as checks

plugin = lightbulb.Plugin("Fun", description = "Fun Commands", include_datastore = True)
plugin.d.emote = helpers.get_emote(":grin:")
plugin.add_checks(checks.is_command_enabled, lightbulb.bot_has_guild_permissions(*helpers.COMMAND_STANDARD_PERMISSIONS))

@plugin.command()
@lightbulb.command("dice", "Roll a 6-face dice for you.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def dice(ctx: lightbulb.Context):
    await ctx.respond("It's %d :game_die:" % (random.randint(1, 6)), reply = True)

@plugin.command()
@lightbulb.option("content", "The string to repeat.", modifier = helpers.CONSUME_REST_OPTION)
@lightbulb.command("echo", "Echo echo echo echo.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def echo(ctx: lightbulb.Context):
    if isinstance(ctx, lightbulb.PrefixContext):
        await ctx.event.message.delete()
    await ctx.respond(ctx.options.content)

@plugin.command()
@lightbulb.option("target", "The target to measure", modifier = helpers.CONSUME_REST_OPTION)
@lightbulb.option("measure_unit", "The unit to measure")
@lightbulb.command("how", "An ultimate measurement to measure everything except gayness.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def how(ctx: lightbulb.Context):
    measure_unit = ctx.options.measure_unit
    target = ctx.options.target

    percent_thing = random.randint(0, 100)
    await ctx.respond(f"{target} is `{percent_thing}%` {measure_unit}.", reply = True)

@plugin.command()
@lightbulb.option("target", "The target to measure.", modifier = helpers.CONSUME_REST_OPTION)
@lightbulb.command("howgay", "An ultimate measurement of gayness.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def howgay(ctx: lightbulb.Context):
    target = ctx.options.target

    percent_gay = 0
    if "MIKEJOLLIE" in target.upper() or "472832990012243969" in target:
        percent_gay = 0
    elif "STRANGER.COM" in target.upper():
        percent_gay = 100
    else: percent_gay = random.randint(0, 100)

    if percent_gay == 0:
        await ctx.respond(f"Holy moly, the {target} is 100% straight :open_mouth:, zero trace of gayness.", reply = True)
    else:
        await ctx.respond(f"{target} is `{percent_gay}%` gay :rainbow_flag:.", reply = True)

@plugin.command()
@lightbulb.command("ping", "Checks the bot if it's alive")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def ping(ctx: lightbulb.Context):
    latency = ctx.bot.heartbeat_latency
    await ctx.respond(f"Pong! :ping_pong: {format(latency * 1000, '.2f')}ms.", reply = True, mentions_reply = True)

@plugin.command()
@lightbulb.option("content", "The string to speak.", modifier = helpers.CONSUME_REST_OPTION)
@lightbulb.command("speak", "Speak the message.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def speak(ctx: lightbulb.Context):
    if isinstance(ctx, lightbulb.PrefixContext):
        await ctx.event.message.delete()
    await ctx.respond(ctx.options.content, tts = True)

def load(bot):
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)