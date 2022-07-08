import lightbulb
import hikari

from utils import checks, helpers, models, psql

plugin = lightbulb.Plugin("Economy", "Money stuffs", include_datastore = True)
plugin.d.emote = helpers.get_emote(":dollar:")
plugin.add_checks(
    checks.is_db_connected, 
    checks.is_command_enabled, 
    lightbulb.bot_has_guild_permissions(*helpers.COMMAND_STANDARD_PERMISSIONS)
)

@plugin.command()
@lightbulb.command("balance", "View balance", aliases = ["bal"])
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def balance(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    async with bot.pool.acquire() as conn:
        user = await psql.User.get_one(conn, ctx.author.id)
        await ctx.respond(f"You have ${user.balance}.")

@plugin.command()
@lightbulb.add_checks(checks.is_dev)
@lightbulb.option("amount", "Amount to add.", type = int, min_value = 1, max_value = 500)
@lightbulb.command("addmoney", "Add money.")
@lightbulb.implements(lightbulb.PrefixCommand)
async def addmoney(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    async with bot.pool.acquire() as conn:
        await psql.Economy.add_money(conn, ctx.author.id, amount = min(500, max(1, ctx.options.amount)))
    await ctx.respond(f"Added ${ctx.options.amount}.")

@plugin.command()
@lightbulb.command("daily", "Daily")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def daily(ctx: lightbulb.Context):
    raise NotImplementedError

@plugin.command()
@lightbulb.command("market", "Public trades")
@lightbulb.implements(lightbulb.PrefixCommandGroup, lightbulb.SlashCommandGroup)
async def market(ctx: lightbulb.Context):
    raise NotImplementedError

@plugin.command()
@lightbulb.command("trade", "Periodic trade for rarer items.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def trade(ctx: lightbulb.Context):
    raise NotImplementedError

@plugin.command()
@lightbulb.command("barter", "Barter stuff with gold.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def barter(ctx: lightbulb.Context):
    raise NotImplementedError

def load(bot: models.MichaelBot):
    bot.add_plugin(plugin)
def unload(bot: models.MichaelBot):
    bot.remove_plugin(plugin)
