import lightbulb
import hikari

import datetime as dt

async def on_shard_connect(event: hikari.ShardConnectedEvent):
    event.app.d.online_at = dt.datetime.now().astimezone()

def load(bot):
    bot.subscribe(hikari.ShardConnectedEvent, on_shard_connect)
def unload(bot):
    bot.unsubscribe(hikari.ShardConnectedEvent, on_shard_connect)
