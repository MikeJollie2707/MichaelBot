'''Music Commands'''

import datetime as dt
import itertools as itools
from textwrap import dedent

import hikari
import lavaplayer
import lightbulb

from utils import checks, helpers, models
from utils.converters import IntervalConverter
from utils.models import NodeExtra
from utils.nav import ButtonNavigator, run_view

plugin = lightbulb.Plugin("Music", description = "Music Commands", include_datastore = True)
plugin.d.emote = helpers.get_emote(":musical_note:")
plugin.add_checks(
    checks.is_command_enabled, 
    checks.strict_concurrency, 
    lightbulb.bot_has_guild_permissions(*helpers.COMMAND_STANDARD_PERMISSIONS),
)

MUSIC_EMOTES = {
    "pause": helpers.get_emote(":pause_button:"),
    "play": helpers.get_emote(":arrow_forward:"),
    "skip": helpers.get_emote(":fast_forward:"),
    "stop": helpers.get_emote(":stop_button:"),
    "queue_loop": helpers.get_emote(":repeat:"),
    "single_loop": helpers.get_emote(":repeat_one:"),
    "shuffle": helpers.get_emote(":twisted_rightwards_arrows:"),
    "volume_smol": helpers.get_emote(":sound:"),
    "volume_beeg": helpers.get_emote(":loud_sound:"),
    "queue_clear": helpers.get_emote(":dash:"),
}

def get_yt_thumbnail_endpoint(identifier: str):
    return f"https://img.youtube.com/vi/{identifier}/maxresdefault.jpg"

async def track_start_event(event: lavaplayer.TrackStartEvent):
    bot: models.MichaelBot = plugin.bot

    node = await bot.lavalink.get_guild_node(event.guild_id)
    # We probably don't want to spam the Now Playing when it's only looping one song.
    if node is not None and not node.repeat:
        await bot.rest.create_message(bot.node_extra[event.guild_id].working_channel, f"Now Playing: `{event.track.title}`.")

async def track_end_event(event: lavaplayer.TrackEndEvent):
    bot: models.MichaelBot = plugin.bot
    
    if bot.node_extra.get(event.guild_id) is None:
        return
    
    node = await bot.lavalink.get_guild_node(event.guild_id)
    if node is not None:
        if bot.node_extra[event.guild_id].queue_loop and not node.repeat:
            node.queue.append(event.track)

async def web_socket_closed_event(event: lavaplayer.WebSocketClosedEvent):
    print(event.reason)

# On voice state update the bot will update the lavalink node
@plugin.listener(hikari.VoiceStateUpdateEvent)
async def voice_state_update(event: hikari.VoiceStateUpdateEvent):
    bot: models.MichaelBot = event.app
    await bot.lavalink.raw_voice_state_update(event.guild_id, event.state.user_id, event.state.session_id, event.state.channel_id)

@plugin.listener(hikari.VoiceServerUpdateEvent)
async def voice_server_update(event: hikari.VoiceServerUpdateEvent):
    bot: models.MichaelBot = event.app
    await bot.lavalink.raw_voice_server_update(event.guild_id, event.endpoint, event.token)

@plugin.listener(hikari.ShardReadyEvent)
async def start_lavalink(event: hikari.ShardReadyEvent):
    bot: models.MichaelBot = event.app
    bot.lavalink = lavaplayer.LavalinkClient(
        host = "0.0.0.0",  # Lavalink host
        port = 2333,  # Lavalink port
        password = "youshallnotpass",  # Lavalink password
        user_id = bot.get_me().id
    )
    # Reference: https://github.com/HazemMeqdad/lavaplayer/blob/main/lavaplayer/client.py#L604
    bot.lavalink.event_manager.add_listener(lavaplayer.TrackStartEvent, track_start_event)
    bot.lavalink.event_manager.add_listener(lavaplayer.TrackEndEvent, track_end_event)
    bot.lavalink.event_manager.add_listener(lavaplayer.WebSocketClosedEvent, web_socket_closed_event)

    bot.lavalink.connect()

@plugin.command()
@lightbulb.add_cooldown(length = 5.0, uses = 1, bucket = lightbulb.GuildBucket)
@lightbulb.option("voice_channel", "The voice channel to join. Default to the VC you're in.", 
    type = hikari.GuildVoiceChannel, 
    channel_types = (hikari.ChannelType.GUILD_VOICE,), 
    default = None
)
@lightbulb.command("join", f"[{plugin.name}] Join a voice channel.", aliases = ["connect"])
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def join(ctx: lightbulb.Context):
    voice_channel = ctx.options.voice_channel
    bot: models.MichaelBot = ctx.bot
    
    if voice_channel is None:
        states = bot.cache.get_voice_states_view_for_guild(ctx.guild_id)
        voice_state = list(itools.filterfalse(lambda i: i.user_id != ctx.author.id, states.values()))
        
        if not voice_state:
            await ctx.respond("You are not in a voice channel.")
            return
        channel_id = voice_state[0].channel_id
    else:
        channel_id = voice_channel.id

    await bot.update_voice_state(ctx.guild_id, channel_id, self_deaf = True)
    
    if bot.node_extra.get(ctx.guild_id) is None:
        bot.node_extra[ctx.guild_id] = NodeExtra()
    # Update working channel.
    bot.node_extra[ctx.guild_id].working_channel = ctx.channel_id

    import asyncio
    # This delay is needed.
    await asyncio.sleep(1)
    connected = bot.cache.get_voice_state(ctx.guild_id, bot.get_me())
    if not connected:
        await ctx.respond(f"Failed to connect to <#{channel_id}>. Maybe check permission?", reply = True, mentions_reply = True)
    else:
        await ctx.respond(f"Joined <#{channel_id}>", reply = True)

@plugin.command()
@lightbulb.command("leave", f"[{plugin.name}] Leave the voice channel.", aliases = ["disconnect", 'dc'])
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def leave(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    node = await bot.lavalink.get_guild_node(ctx.guild_id)
    if node is not None:
        bot.node_extra.pop(ctx.guild_id, None)
        await bot.update_voice_state(ctx.guild_id, None)
        await ctx.respond("**Successfully disconnected.**", reply = True)
    else:
        await ctx.respond("Bot is not in a voice channel.", reply = True, mentions_reply = True)

@plugin.command()
@lightbulb.add_cooldown(length = 1.0, uses = 1, bucket = lightbulb.GuildBucket)
@lightbulb.command("np", f"[{plugin.name}] Get info about the current track.", aliases = ["now_playing"])
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def np(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    node = await bot.lavalink.get_guild_node(ctx.guild_id)
    if node is not None:
        if not node.queue:
            await ctx.respond("*cricket noises*", reply = True)
            return

        current_track = node.queue[0]
        # This for some reasons return a second instead of milliseconds.
        ratio = float(current_track.position * 1000) / float(current_track.length)
        # Milliseconds have this format hh:mm:ss.somerandomstuffs, so just split at the first dot.
        current_position = str(dt.timedelta(seconds = current_track.position)).split('.', maxsplit = 1)[0]
        full_duration = str(dt.timedelta(milliseconds = current_track.length)).split('.', maxsplit = 1)[0]
        # We're using c-string here because when the dot is at the beginning and the end,
        # I need to deal with some weird string concat, so no.
        progress_cstring = ['-'] * 30

        # [30, -1) to make sure the dot can appear as the first character
        for i in range(30, -1, -1):
            if i / 30.0 <= ratio:
                progress_cstring[i] = '🔘'
                break
        
        progress_string = ''.join(progress_cstring)
        embed = helpers.get_default_embed(
            title = "Now Playing",
            description = f"""
            [{current_track.title}]({current_track.uri})
            `{progress_string}`
            `{current_position}` / `{full_duration}`

            **Requested by:** {bot.cache.get_user(int(current_track.requester)).mention}
            """,
            author = ctx.author,
            timestamp = dt.datetime.now().astimezone()
        )

        if current_track.source_name == "youtube":
            embed.set_thumbnail(
                get_yt_thumbnail_endpoint(current_track.identifier)
            )
        await ctx.respond(embed = embed, reply = True)
    else:
        await ctx.respond("Bot is not in a voice channel.", reply = True, mentions_reply = True)

@plugin.command()
@lightbulb.add_cooldown(length = 5.0, uses = 5, bucket = lightbulb.GuildBucket)
@lightbulb.option("query", "The query to play (url, name, etc.)", modifier = helpers.CONSUME_REST_OPTION)
@lightbulb.command("play", f"[{plugin.name}] Play the query or add it to the queue.", aliases = ['p'])
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def play(ctx: lightbulb.Context):
    query = ctx.options.query
    bot: models.MichaelBot = ctx.bot

    node = await bot.lavalink.get_guild_node(ctx.guild_id)
    if node is None:
        await join(ctx)
        node = await bot.lavalink.get_guild_node(ctx.guild_id)
        # join() failed somehow, most likely from not joining vc.
        if node is None:
            return
    
    result = await bot.lavalink.auto_search_tracks(query)
    if not result:
        await ctx.respond("Can't find any songs with the query.", reply = True, mentions_reply = True)
        return
    
    if isinstance(result, lavaplayer.PlayList):
        await bot.lavalink.add_to_queue(ctx.guild_id, result.tracks, ctx.author.id)
        await ctx.respond(f"Added playlist `{result.name}` with {len(result.tracks)} tracks to queue.", reply = True)
        return

    await bot.lavalink.play(ctx.guild_id, result[0], ctx.author.id)
    await ctx.respond(f"Added `{result[0].title}` to the queue", reply = True) 

@plugin.command()
@lightbulb.add_cooldown(length = 1.0, uses = 1, bucket = lightbulb.GuildBucket)
@lightbulb.command("pause", f"[{plugin.name}] Toggle pausing the player.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def pause(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    node = await bot.lavalink.get_guild_node(ctx.guild_id)
    if node is not None:
        node.is_pause = not node.is_pause
        await bot.lavalink.pause(ctx.guild_id, node.is_pause)
        if node.is_pause:
            await ctx.respond(f"{MUSIC_EMOTES['pause']} **Paused.**", reply = True)
        else:
            await ctx.respond(f"{MUSIC_EMOTES['play']} **Resumed.**", reply = True)
    else:
        await ctx.respond("Bot is not in a voice channel.", reply = True, mentions_reply = True)

@plugin.command()
@lightbulb.add_cooldown(length = 2.0, uses = 1, bucket = lightbulb.GuildBucket)
@lightbulb.option("track", "Keywords to search. Example: `blend w.`", modifier = helpers.CONSUME_REST_OPTION)
@lightbulb.command("search", f"[{plugin.name}] Search and return 10 relevant results.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def search(ctx: lightbulb.Context):
    track = ctx.options.track
    bot: models.MichaelBot = ctx.bot

    # Ideally the user should provide keywords, but if they provide a link then I'll go with that too.
    results = await bot.lavalink.auto_search_tracks(track)
    if results is None:
        await ctx.respond("Can't find any songs with the keywords provided.", reply = True, mentions_reply = True)
        return
    
    embed = helpers.get_default_embed(
        title = "Top 10 search results",
        description = "",
        timestamp = dt.datetime.now().astimezone(),
        author = ctx.author
    )

    for index, track in enumerate(results[:10]):
        embed.description += f"**{index + 1}.** [{track.title}]({track.uri}) - `{dt.timedelta(milliseconds = track.length)}`\n"
    await ctx.respond(embed = embed, reply = True)

@plugin.command()
@lightbulb.add_cooldown(length = 1.0, uses = 1, bucket = lightbulb.GuildBucket)
@lightbulb.option("position", "Timestamp to jump to.", type = IntervalConverter)
@lightbulb.command("seek", f"[{plugin.name}] Jump to the provided timestamp.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def seek(ctx: lightbulb.Context):
    position = ctx.options.position
    bot: models.MichaelBot = ctx.bot

    if isinstance(ctx, lightbulb.SlashContext):
        try:
            position = await IntervalConverter(ctx).convert(position)
        except Exception as exc:
            raise lightbulb.ConverterFailure("Conversion failed for option position.", opt = ctx.invoked.options["position"], raw = ctx.options.position) from exc
    
    node = await bot.lavalink.get_guild_node(ctx.guild_id)
    if node is not None:
        await bot.lavalink.seek(ctx.guild_id, position.seconds * 1000)
        await ctx.respond(f"{MUSIC_EMOTES['skip']} **Seek to `{position}`.**", reply = True)
    else:
        await ctx.respond("Bot is not in a voice channel.", reply = True, mentions_reply = True)

@plugin.command()
@lightbulb.add_cooldown(length = 1.0, uses = 1, bucket = lightbulb.GuildBucket)
@lightbulb.command("repeat", f"[{plugin.name}] Toggle repeating the track.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def repeat(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    node = await bot.lavalink.get_guild_node(ctx.guild_id)
    if node is not None:
        node.repeat = not node.repeat
        await bot.lavalink.set_guild_node(ctx.guild_id, node)
        if node.repeat:
            await ctx.respond(f"{MUSIC_EMOTES['single_loop']} **Enabled!**", reply = True)
        else:
            await ctx.respond(f"{MUSIC_EMOTES['single_loop']} **Disabled!**", reply = True)
    else:
        await ctx.respond("Bot is not in a voice channel.", reply = True, mentions_reply = True)

@plugin.command()
@lightbulb.set_help(dedent('''
    It's recommended to use the built-in feature `User Volume` instead of this command.
'''))
@lightbulb.add_cooldown(length = 5.0, uses = 1, bucket = lightbulb.GuildBucket)
@lightbulb.option("vol","Volume to set (0-200)", type = int, min_value = 0, max_value = 200)
@lightbulb.command("volume", f"[{plugin.name}] Set the volume of the player.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def volume(ctx: lightbulb.Context):
    vol = ctx.options.vol
    bot: models.MichaelBot = ctx.bot

    if isinstance(ctx, lightbulb.SlashContext):
        vol = int(vol)
    
    node = await bot.lavalink.get_guild_node(ctx.guild_id)
    if node is not None:
        # Force the volume to stay in range.
        vol = min(max(vol, 0), 200)

        await bot.lavalink.volume(ctx.guild_id, vol)
        emote = MUSIC_EMOTES["volume_beeg"] if vol > 100 else MUSIC_EMOTES["volume_smol"]
        await ctx.respond(f"{emote} Set volume to {vol}%", reply = True)
    else:
        await ctx.respond("Bot is not in a voice channel.", reply = True, mentions_reply = True)

@plugin.command()
@lightbulb.add_cooldown(length = 2.0, uses = 1, bucket = lightbulb.GuildBucket)
@lightbulb.command("queue", f"[{plugin.name}] Display the song queue.", aliases = ['q'])
@lightbulb.implements(lightbulb.PrefixCommandGroup, lightbulb.SlashCommandGroup)
async def queue(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    node = await bot.lavalink.get_guild_node(ctx.guild_id)
    if node is not None:
        embed = None
        if len(node.queue) == 0:
            embed = helpers.get_default_embed(
                timestamp = dt.datetime.now().astimezone(),
                author = ctx.author,
            )
            embed.description = "*There are no songs currently in queue.*"
            await ctx.respond(embed = embed, reply = True)
        elif len(node.queue) == 1:
            current_track = node.queue[0]
            embed = helpers.get_default_embed(
                title = f"Queue for {ctx.get_guild().name}",
                timestamp = dt.datetime.now().astimezone(),
                author = ctx.author
            ).add_field(
                name = "Now Playing:",
                value = f"[{current_track.title}]({current_track.uri}) - {dt.timedelta(milliseconds = current_track.length)}",
                inline = False
            )
            await ctx.respond(embed = embed, reply = True)
        else:
            current_track = node.queue[0]
            upcoming = node.queue[1:]

            page_list = []
            text = ""
            embed = None
            for index, track in enumerate(upcoming):
                if index % 5 == 0:
                    embed = helpers.get_default_embed(
                        title = f"Queue for {ctx.get_guild().name}",
                        timestamp = dt.datetime.now().astimezone(),
                        author = ctx.author
                    ).add_field(
                        name = "Now playing:",
                        value = f"[{current_track.title}]({current_track.uri}) - {dt.timedelta(milliseconds = current_track.length)}",
                        inline = False
                    )
                
                text += f"`{index + 1}`. [{track.title}]({track.uri}) - {dt.timedelta(milliseconds = track.length)}\n"

                if index % 5 == 4:
                    embed.add_field(
                        name = "Up Next:",
                        value = text,
                        inline = False
                    )
                    embed.add_field(
                        name = f"{MUSIC_EMOTES['single_loop']}",
                        value = "Yes" if node.repeat else "No",
                        inline = True
                    ).add_field(
                        name = f"{MUSIC_EMOTES['queue_loop']}",
                        value = "Yes" if bot.node_extra[ctx.guild_id].queue_loop else "No",
                        inline = True
                    )
                    page_list.append(embed)
                    text = ""
                    embed = None
            # We're updating text rather than embed every loop, this should be the check instead of embed is None.
            if text != "":
                embed.add_field(
                    name = "Up Next:",
                    value = text,
                    inline = False
                )
                embed.add_field(
                    name = f"{MUSIC_EMOTES['single_loop']}",
                    value = "Yes" if node.repeat else "No",
                    inline = True
                ).add_field(
                    name = f"{MUSIC_EMOTES['queue_loop']}",
                    value = "Yes" if bot.node_extra[ctx.guild_id].queue_loop else "No",
                    inline = True
                )
                page_list.append(embed)
            
            page_nav = ButtonNavigator(pages = page_list, authors = (ctx.author.id, ))
            await run_view(page_nav, ctx)
    else:
        await ctx.respond("Bot is not in a voice channel.", reply = True, mentions_reply = True)

@queue.child
@lightbulb.add_cooldown(length = 2.0, uses = 1, bucket = lightbulb.GuildBucket)
@lightbulb.command("view", f"[{plugin.name}] Display the song queue.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def queue_view(ctx: lightbulb.Context):
    await queue(ctx)

@queue.child
@lightbulb.command("clear", f"[{plugin.name}] Clear the entire queue but the current track.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def queue_clear(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    node = await bot.lavalink.get_guild_node(ctx.guild_id)
    if node is not None:    
        node.queue = [node.queue[0]]
        await bot.lavalink.set_guild_node(ctx.guild_id, node)
        await ctx.respond(f"{MUSIC_EMOTES['queue_clear']} **Queue cleared!**", reply = True)
    else:
        await ctx.respond("Bot is not in a voice channel.", reply = True, mentions_reply = True)

@queue.child
@lightbulb.command("shuffle", f"[{plugin.name}] Shuffle the queue.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def queue_shuffle(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    node = await bot.lavalink.get_guild_node(ctx.guild_id)
    if node is not None:
        await bot.lavalink.shuffle(ctx.guild_id)
        await ctx.respond(f"{MUSIC_EMOTES['shuffle']} **Shuffled!**", reply = True)
    else:
        await ctx.respond("Bot is not in a voice channel.", reply = True, mentions_reply = True)

@queue.child
@lightbulb.command("loop", f"[{plugin.name}] Toggle queue loop.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def queue_loop(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    node = await bot.lavalink.get_guild_node(ctx.guild_id)
    if node is not None:
        fnode = bot.node_extra.get(ctx.guild_id)
        if fnode is None:
            await ctx.respond("Something is wrong, try reconnect the bot to the VC.", reply = True, mentions_reply = True)
            return
        
        fnode.queue_loop = not fnode.queue_loop
        if fnode.queue_loop:
            await ctx.respond(f"{MUSIC_EMOTES['queue_loop']} **Enabled!**", reply = True)
        else:
            await ctx.respond(f"{MUSIC_EMOTES['queue_loop']} **Disabled!**", reply = True)
    else:
        await ctx.respond("Bot is not in a voice channel.", reply = True, mentions_reply = True)

@queue.child
@lightbulb.add_cooldown(length = 5.0, uses = 1, bucket = lightbulb.GuildBucket)
@lightbulb.option("to_index", "The index in the queue where you want the track to be.", type = int)
@lightbulb.option("from_index", "The index in the queue to move.", type = int)
@lightbulb.command("move", f"[{plugin.name}] Move a track in queue to a new order index.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def queue_move(ctx: lightbulb.Context):
    from_index = ctx.options.from_index - 1
    to_index = ctx.options.to_index - 1
    bot: models.MichaelBot = ctx.bot

    node = await bot.lavalink.get_guild_node(ctx.guild_id)
    if node is not None:
        movable_queue = node.queue[1:]
        movable_size = len(movable_queue)
        if from_index < 0 or to_index > movable_size - 1 or to_index < 0 or from_index > movable_size - 1:
            await ctx.respond("Index out of range.", reply = True, mentions_reply = True)
            return
        
        track = movable_queue[from_index]
        # remove() will remove the first instance of the track.
        # It's not clear if two same songs will be considered the same track, so we manually remove with list slicing.
        movable_queue = movable_queue[:from_index] + movable_queue[from_index + 1:]
        movable_queue.insert(to_index, track)

        node.queue = [node.queue[0]] + movable_queue
        await bot.lavalink.set_guild_node(ctx.guild_id, node)
        await ctx.respond(f"**Track** `{track.title}` **moved from {from_index + 1} to {to_index + 1}.**", reply = True)
    else:
        await ctx.respond("Bot is not in a voice channel.", reply = True, mentions_reply = True)

@queue.child
@lightbulb.add_cooldown(length = 5.0, uses = 1, bucket = lightbulb.GuildBucket)
@lightbulb.option("index", "The index in the queue to remove.", type = int)
@lightbulb.command("remove", f"[{plugin.name}] Remove a track in the queue.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def queue_remove(ctx: lightbulb.Context):
    index = ctx.options.index - 1
    bot: models.MichaelBot = ctx.bot

    node = await bot.lavalink.get_guild_node(ctx.guild_id)
    if node is not None:
        removable_queue = node.queue[1:]
        if index < 0 or index > len(removable_queue) - 1:
            await ctx.respond("Index out of range.")
            return
        
        removed_track = removable_queue[index]
        removable_queue = removable_queue[:index] + removable_queue[index + 1:]

        node.queue = [node.queue[0]] + removable_queue
        await bot.lavalink.set_guild_node(ctx.guild_id, node)
        await ctx.respond(f"**Track removed:** `{removed_track.title}`.", reply = True)
    else:
        await ctx.respond("Bot is not in a voice channel.", reply = True, mentions_reply = True)

@plugin.command()
@lightbulb.add_cooldown(length = 2.0, uses = 1, bucket = lightbulb.GuildBucket)
@lightbulb.command("skip", f"[{plugin.name}] Skip the current track.", aliases = ['s'])
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def skip(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    node = await bot.lavalink.get_guild_node(ctx.guild_id)
    if node is not None:
        await bot.lavalink.skip(ctx.guild_id)
        await ctx.respond(f"{MUSIC_EMOTES['skip']} **Skipped!**", reply = True)
    else:
        await ctx.respond("Bot is not in a voice channel.", reply = True, mentions_reply = True)

@plugin.command()
@lightbulb.command("stop", f"[{plugin.name}] Stop the player.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def stop(ctx: lightbulb.Context):
    bot: models.MichaelBot = ctx.bot

    node = await bot.lavalink.get_guild_node(ctx.guild_id)
    if node is not None:
        bot.node_extra[ctx.guild_id].queue_loop = False

        await bot.lavalink.stop(ctx.guild_id)
        await ctx.respond(f"{MUSIC_EMOTES['stop']} **Stopped!**", reply = True)
    else:
        await ctx.respond("Bot is not in a voice channel.", reply = True, mentions_reply = True)

def load(bot: models.MichaelBot):
    bot.add_plugin(plugin)
def unload(bot: models.MichaelBot):
    bot.remove_plugin(plugin)
