import lightbulb
import hikari
import aiohttp

import datetime as dt
import random
from textwrap import dedent

import utilities.checks as checks
import utilities.helpers as helpers

plugin = lightbulb.Plugin("Fun", description = "Fun Commands", include_datastore = True)
plugin.d.emote = helpers.get_emote(":grin:")
plugin.add_checks(checks.is_command_enabled, lightbulb.bot_has_guild_permissions(*helpers.COMMAND_STANDARD_PERMISSIONS))

@plugin.command()
@lightbulb.command("dice", "Roll a 6-face dice for you.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def dice(ctx: lightbulb.Context):
    await ctx.respond("It's %d :game_die:" % (random.randint(1, 6)), reply = True)

@plugin.command()
@lightbulb.set_help(dedent('''
    r/FoundTheInaAlt
'''))
@lightbulb.add_cooldown(length = 3.0, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.command("dadjoke", "Give you a dad joke.", aliases = ["ina-of-the-mountain-what-is-your-wisdom"])
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def dadjoke(ctx: lightbulb.Context):
    BASE_URL = "https://icanhazdadjoke.com/"
    header = {
        "Accept": "application/json",
        "User-Agent": "MichaelBot (Discord Bot) - https://github.com/MikeJollie2707/"
    }

    resp: aiohttp.ClientResponse = await ctx.bot.d.aio_session.get(BASE_URL, headers = header)
    if resp.status == 200:
        resp_json = await resp.json()
        await ctx.respond(resp_json["joke"], reply = True)
    else:
        await ctx.respond("Oh, no dad jokes. Forgetti beam!", reply = True, mentions_reply = True)

@plugin.command()
@lightbulb.add_cooldown(length = 2.0, uses = 1, bucket = lightbulb.UserBucket)
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
@lightbulb.command("how", "An ultimate measurement to measure everything.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def how(ctx: lightbulb.Context):
    measure_unit = ctx.options.measure_unit
    target = ctx.options.target

    percent_thing = random.randint(0, 100)
    await ctx.respond(f"{target} is `{percent_thing}%` {measure_unit}.", reply = True)

@plugin.command()
@lightbulb.option("text", "Text to mock.", modifier = helpers.CONSUME_REST_OPTION)
@lightbulb.command("mock", "tuRn A teXT INtO MOCk teXt.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def mock(ctx: lightbulb.Context):
    transform = [str.upper, str.lower]
    text = ''.join(random.choice(transform)(c) for c in ctx.options.text)
    if len(text) < 1500:
        await ctx.respond(text, reply = True)
    else:
        try:
            await ctx.author.send(text)
            await ctx.respond("I threw the output into your DM :wink:", reply = True)
        except hikari.ForbiddenError:
            await ctx.respond("The text is too large and I can't send it to your DM for some reasons :(", reply = True, mentions_reply = True)

@plugin.command()
@lightbulb.add_cooldown(length = 2.0, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.option("content", "The string to speak.", modifier = helpers.CONSUME_REST_OPTION)
@lightbulb.command("speak", "Speak the message.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def speak(ctx: lightbulb.Context):
    if isinstance(ctx, lightbulb.PrefixContext):
        await ctx.event.message.delete()
    await ctx.respond(ctx.options.content, tts = True)

@plugin.command()
@lightbulb.set_help(dedent('''
    UwU This c-c-command is an API caww, so don't use i-it too *pounces on you* many times UwU
'''))
@lightbulb.add_cooldown(length = 3.0, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.option("text", "Text to uwuify.", modifier = helpers.CONSUME_REST_OPTION)
@lightbulb.command("uwu", "Turn a text into uwu text.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def uwu(ctx: lightbulb.Context):
    BASE_URL = "https://uwuaas.herokuapp.com/api/"
    resp: aiohttp.ClientResponse = await ctx.bot.d.aio_session.post(BASE_URL, json = {"text": ctx.options.text})
    if resp.status == 200:
        resp_json = await resp.json()
        embed = helpers.get_default_embed(
            description = resp_json["text"],
            author = ctx.author,
            timestamp = dt.datetime.now().astimezone()
        )
        await ctx.respond(embed = embed, reply = True)
    else:
        await ctx.respond("Oh nyo, ★⌒ヽ(˘꒳˘ *) I faiwed *whispers to self* t-to uwu the ÚwÚ text.", reply = True, mentions_reply = True)

def load(bot: lightbulb.BotApp):
    bot.add_plugin(plugin)
def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(plugin)