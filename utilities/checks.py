import lightbulb
import hikari

@lightbulb.Check
def is_dev(ctx: lightbulb.Context) -> bool:
    return ctx.author.id in [472832990012243969, 462726152377860109]
