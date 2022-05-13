import lightbulb
import hikari
from lightbulb.ext import tasks
import humanize

import datetime as dt

import utils.checks as checks
import utils.converters as converters
import utils.helpers as helpers
import utils.models as models
import utils.psql as psql

plugin = lightbulb.Plugin(".Experiment", "Sandbox")
plugin.add_checks(checks.is_dev, checks.is_command_enabled, lightbulb.bot_has_guild_permissions(*helpers.COMMAND_STANDARD_PERMISSIONS))

@plugin.command()
@lightbulb.command("test", "test",  hidden = True)
@lightbulb.implements(lightbulb.PrefixCommand)
async def test(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    pass

def load(bot: models.MichaelBot):
    bot.add_plugin(plugin)
    
def unload(bot: models.MichaelBot):
    bot.remove_plugin(plugin)
