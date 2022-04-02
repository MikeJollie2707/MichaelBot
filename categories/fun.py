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
@lightbulb.add_cooldown(length = 10.0, uses = 1, bucket = lightbulb.UserBucket)
@lightbulb.option("type", "Which copypasta to show. Dig into the bot's code to see available options ;)", modifier = helpers.CONSUME_REST_OPTION)
@lightbulb.command("copypasta", "My favorite copypasta.", hidden = True)
@lightbulb.implements(lightbulb.PrefixCommand)
async def copypasta(ctx: lightbulb.Context):
    option = ctx.options.type

    if option.lower() == "glasses are really versatile":
        await ctx.respond((
            "Glasses are really versatile. First, you can have glasses-wearing girls take them off and suddenly become beautiful,"
            " or have girls wearing glasses flashing those cute grins, or have girls stealing the protagonist's glasses and putting them on like, \"Haha, got your glasses!\""
            " That's just way too cute! Also, boys with glasses! I really like when their glasses have that suspicious looking gleam, and it's amazing how it can look really cool"
            " or just be a joke. I really like how it can fulfill all those abstract needs. Being able to switch up the styles and colors of glasses based on your mood is a lot of fun too!"
            " It's actually so much fun! You have those half rim glasses, or the thick frame glasses, everything! It's like you're enjoying all these kinds of glasses at a buffet."
            " I really want Luna to try some on or Marine to try some on to replace her eyepatch. We really need glasses to become a thing in hololive and start selling them for HoloComi."
            " Don't. You. Think. We. Really. Need. To. Officially. Give. Everyone. Glasses?"
        ), reply = True)
    elif option.lower() == "our lord and savior lightning mcqueen":
        await ctx.respond((
            "Hello, ma'am do you have a minute to talk about our lord and savior Lightning McQueen?! Did you know that Lightning McQueen is the star of several feature films such as Cars,"
            " Cars 2, Cars 3, Planes: Fire and Rescue, Finding Dory, Toy Story 3, Coco and Ralph breaks the internet? As well as other short film such as Master and the Ghostlight, Miss Fritter's Racing Skoool,"
            " Television program such as Cars Toons, Pixar's Popcorn Cars series voiced by none other than Owen Wilson?"
        ), reply = True)
    elif option.lower() == "gnu linux":
        await ctx.respond((
            "I'd just like to interject for a moment. What you're referring to as Linux, is in fact, GNU/Linux, or as I've recently taken to calling it, GNU plus Linux."
            " Linux is not an operating system unto itself, but rather another free component of a fully functioning GNU system made useful by the GNU corelibs,"
            " shell utilities and vital system components comprising a full OS as defined by POSIX.\n"
            
            "Many computer users run a modified version of the GNU system every day, without realizing it."
            " Through a peculiar turn of events, the version of GNU which is widely used today is often called \"Linux\", and many of its users are not aware that it is basically the GNU system,"
            " developed by the GNU Project.\n"

            "There really is a Linux, and these people are using it, but it is just a part of the system they use."
            " Linux is the kernel: the program in the system that allocates the machine's resources to the other programs that you run."
            " The kernel is an essential part of an operating system, but useless by itself; it can only function in the context of a complete operating system."
            " Linux is normally used in combination with the GNU operating system: the whole system is basically GNU with Linux added, or GNU/Linux. "
            " All the so-called \"Linux\" distributions are really distributions of GNU/Linux."
        ), reply = True)
    elif option.lower() == "not gnu linux":
        await ctx.respond((
            "\"I use Linux as my operating system,\" I state proudly to the unkempt, bearded man. He swivels around in his desk chair with a devilish gleam in his eyes,"
            " ready to mansplain with extreme precision. \"Actually\", he says with a grin, \"Linux is just the kernel. You use GNU+Linux!\" I don't miss a beat and reply with a smirk,"
            " \"I use Alpine, a distro that doesn't include the GNU coreutils, or any other GNU code. It's Linux, but it's not GNU+Linux.\"\n"

            "The smile quickly drops from the man's face. His body begins convulsing and he foams at the mouth and drops to the floor with a sickly thud. As he writhes around he screams"
            " \"I-IT WAS COMPILED WITH GCC! THAT MEANS IT'S STILL GNU!\" Coolly, I reply \"If windows was compiled with gcc, would that make it GNU?\""
            " I interrupt his response with \"-and work is being made on the kernel to make it more compiler-agnostic. Even you were correct, you wont be for long.\"\n"

            "With a sickly wheeze, the last of the man's life is ejected from his body. He lies on the floor, cold and limp. I've womansplained him to death."
        ))

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

    async with ctx.bot.d.aio_session.get(BASE_URL, headers = header) as resp:
        if resp.status == 200:
            resp_json = await resp.json()
            await ctx.respond(resp_json["joke"], reply = True)
        else:
            await ctx.respond("Oh, no dad jokes. Forgetti beam!", reply = True, mentions_reply = True)

@plugin.command()
@lightbulb.command("dice", "Roll a 6-face dice for you.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def dice(ctx: lightbulb.Context):
    await ctx.respond("It's %d :game_die:" % (random.randint(1, 6)), reply = True)

@plugin.command()
@lightbulb.set_help(dedent('''
    Bot needs to have `Manage Messages` permission if used as a Prefix Command.
'''))
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
@lightbulb.add_cooldown(length = 5.0, uses = 1.0, bucket = lightbulb.UserBucket)
@lightbulb.command("pekofy", "Pekofy a message peko.")
@lightbulb.implements(lightbulb.MessageCommand)
async def peko(ctx: lightbulb.Context):
    from utilities.funtext import pekofy

    message: hikari.Message = ctx.options.target
    if message.content != None:
        text = pekofy(message.content)
        await ctx.respond(text, reply = True)
    else:
        await ctx.respond("Oh no, this message doesn't have any text peko.", reply = True, mentions_reply = True)

@plugin.command()
@lightbulb.set_help(dedent('''
    Bot needs to have `Manage Messages` permission if used as a Prefix Command.
'''))
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
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand, lightbulb.MessageCommand)
async def uwu(ctx: lightbulb.Context):
    #BASE_URL = "https://uwuaas.herokuapp.com/api/"
    #async with ctx.bot.d.aio_session.post(BASE_URL, json = {"text": ctx.options.text}) as resp:
    #    if resp.status == 200:
    #        resp_json = await resp.json()
    #        embed = helpers.get_default_embed(
    #            description = resp_json["text"],
    #            author = ctx.author,
    #            timestamp = dt.datetime.now().astimezone()
    #        )
    #        await ctx.respond(embed = embed, reply = True)
    #    else:
    #        await ctx.respond("Oh nyo, ★⌒ヽ(˘꒳˘ *) I faiwed *whispers to self* t-to uwu the ÚwÚ text.", reply = True, mentions_reply = True)
    from utilities.funtext import uwuify

    if isinstance(ctx, lightbulb.MessageContext):
        message: hikari.Message = ctx.options.target
        if message.content != None:
            text = uwuify(message.content)
        else:
            await ctx.respond("Oh nyo, rawr this message doesn't have a-any blushes text. (ꈍᴗꈍ)", reply = True, mentions_reply = True)
    else:
        text = uwuify(ctx.options.text)

    if len(text) > 4000:
        await ctx.respond("Oh nyo, rawr x3 t-the uwu text is too l-long. O-Oopsy.", reply = True, mentions_reply = True)
    else:
        embed = helpers.get_default_embed(
            description = text,
            author = ctx.author,
            timestamp = dt.datetime.now().astimezone()
        )
        await ctx.respond(embed = embed, reply = True)

def load(bot: lightbulb.BotApp):
    bot.add_plugin(plugin)
def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(plugin)