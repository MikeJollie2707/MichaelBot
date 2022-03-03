# 3rd-party imports.
# Import any libraries that are not standard and not your code.
import lightbulb
import hikari

# Standard imports.
# Import std python libraries here.
import datetime as dt

# Utilities
# It's recommended to shorten their names to not include "utilities"
import utilities.helpers as helpers

# Create a category
plugin = lightbulb.Plugin("Category's name", include_datastore = True)
plugin.d.emote = helpers.get_emote("")

# Create a command
# Order of decorator is bottom-up.
@plugin.command()
@lightbulb.add_checks(...)
@lightbulb.option("arg2", "Description", modifier = helpers.CONSUME_REST_OPTION)
@lightbulb.option("arg1", "Description")
@lightbulb.command("Command's name", "Description")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def slash_cmd(ctx : lightbulb.Context):
    # If it is a simple one-line command then it's not worth it to do this,
    # but you should explicitly declare arguments to shorten the ctx.options.
    arg1 = ctx.options.arg1
    arg2 = ctx.options.arg2

    if isinstance(ctx, lightbulb.SlashCommand):
        # Do exclusive stuffs for slash command here.
        pass

    # Do stuffs
    pass

# Load and unload functions; must have.
def load(bot):
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
