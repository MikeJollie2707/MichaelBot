import lightbulb
import hikari

import utilities.checks as checks
import utilities.helpers as helpers
import utilities.models as models

plugin = lightbulb.Plugin("Experiment", "Sandbox")
plugin.add_checks(checks.is_dev, checks.is_command_enabled, lightbulb.bot_has_guild_permissions(*helpers.COMMAND_STANDARD_PERMISSIONS))

@plugin.command()
@lightbulb.command("test", "test",  hidden = True)
@lightbulb.implements(lightbulb.PrefixCommand)
async def test(ctx: lightbulb.Context):
    raise SyntaxError("Weeeee")

def load(bot: models.MichaelBot):
    bot.add_plugin(plugin)
def unload(bot: models.MichaelBot):
    bot.remove_plugin(plugin)
