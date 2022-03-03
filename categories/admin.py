import lightbulb
import hikari

import utilities.helpers as helpers
from utilities.checks import is_dev

plugin = lightbulb.Plugin("Secret", "Developer-only commands.", include_datastore = True)
plugin.d.emote = helpers.get_emote(":computer:")

plugin.add_checks(is_dev)

@plugin.set_error_handler()
async def on_plugin_error(event: lightbulb.CommandErrorEvent) -> bool:
    exception = event.exception.__cause__ or event.exception

    if isinstance(exception, lightbulb.BotMissingRequiredPermission):
        pass
    elif isinstance(exception, lightbulb.MissingRequiredPermission):
        pass
    elif isinstance(exception, lightbulb.CheckFailure):
        exception.message = "`Author must be a MichaelBot developer`"
    
    return False

@plugin.command()
@lightbulb.option("extension", "The extension to reload.")
@lightbulb.command("reload", "Reload an extension.", hidden = True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def reload(ctx: lightbulb.Context):
    ctx.bot.reload_extensions(ctx.options.extension)
    await ctx.respond(f"Reloaded extension {ctx.options.extension}.", reply = True)
@reload.set_error_handler()
async def reload_error(event: lightbulb.CommandErrorEvent):
    exception = event.exception.__cause__ or event.exception
    if isinstance(exception, lightbulb.ExtensionNotFound):
        await event.context.respond("This extension does not exist.", reply = True, mentions_reply = True)

@plugin.command()
@lightbulb.command("shutdown", "Shut the bot down.", hidden = True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def shutdown(ctx: lightbulb.Context):
    await ctx.respond("Bot shutting down...")
    await ctx.bot.close()

def load(bot):
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
