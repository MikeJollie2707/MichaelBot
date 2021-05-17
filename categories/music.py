import discord
from discord.ext import commands
import wavelink

import datetime as dt
import asyncio
import typing
import re

import utilities.facility as Facility
from templates.navigate import Pages

URL_REG = re.compile(r'https?://(?:www\.)?.+')

class MusicController:
    def __init__(self, bot, guild_id):
        self.bot = bot
        self.guild_id = guild_id
        self.channel = None

        self.next = asyncio.Event()
        self.queue = asyncio.Queue()

        self.volume = 50

        self.is_single_loop = False
        self.is_queue_loop = False
        self.current_track = None

        self.player : wavelink.Player = self.bot.wavelink.get_player(self.guild_id)

        self.bot.loop.create_task(self.controller_loop())

    async def controller_loop(self):
        await self.bot.wait_until_ready()

        #self.player = self.bot.wavelink.get_player(self.guild_id)
        await self.player.set_volume(self.volume)

        while True:
            self.next.clear()

            if not self.is_single_loop:
                self.current_track = await self.queue.get()
            await self.player.play(self.current_track)
            await self.channel.send(f"Now playing: `{self.current_track}`")

            # Blocking await till the song is completed.
            await self.next.wait()
            if self.is_queue_loop:
                await self.queue.put(self.current_track)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emoji = '🎵'

        if not hasattr(bot, "wavelink"):
            self.bot.wavelink = wavelink.Client(bot = self.bot)
        self.controllers : typing.Dict[MusicController] = {}
        
        self.bot.loop.create_task(self.start_nodes())
    
    async def start_nodes(self):
        await self.bot.wait_until_ready()

        # Initiate our nodes. For this example we will use one server.
        # Region should be a discord.py guild.region e.g sydney or us_central (Though this is not technically required)
        node = await self.bot.wavelink.initiate_node(host='0.0.0.0',
                                                     port=2333,
                                                     rest_uri='http://0.0.0.0:2333',
                                                     password='youshallnotpass',
                                                     identifier='TEST',
                                                     region='us_west')

        # Set our node hook callback
        node.set_hook(self.on_event_hook)
    
    async def on_event_hook(self, event):
        """Node hook callback."""
        if isinstance(event, (wavelink.TrackEnd, wavelink.TrackException)):
            controller = self.get_controller(event.player)
            controller.next.set()
        
    def get_controller(self, value: typing.Union[commands.Context, wavelink.Player]) -> MusicController:
        if isinstance(value, commands.Context):
            gid = value.guild.id
        else:
            gid = value.guild_id
        
        if self.controllers.get(gid) is None:
            self.controllers[gid] = MusicController(self.bot, gid)

        return self.controllers[gid]

    @commands.command()
    async def connect(self, ctx, *, voice_channel : discord.VoiceChannel = None):
        if voice_channel is None:
            try:
                voice_channel = ctx.author.voice.channel
            except AttributeError:
                await ctx.reply("No channel to join. Please either specify the channel or join one.")
                return
        
        controller = self.get_controller(ctx)
        controller.channel = ctx.channel
        await ctx.reply(f"Connecting to `{voice_channel}`", mention_author = False)
        await controller.player.connect(voice_channel.id)
    
    @commands.command(aliases = ['p'])
    async def play(self, ctx, *, track):
        tracks = await self.bot.wavelink.get_tracks(f'ytsearch:{track}')

        if tracks is None:
            await ctx.reply("Could not find any songs.")
            return
        
        controller = self.get_controller(ctx)
        if not controller.player.is_connected:
            await ctx.invoke(self.connect)
        await controller.queue.put(tracks[0])

        if not URL_REG.match(track):
            track = f'ytsearch:{track}'
        tracks = await self.bot.wavelink.get_tracks(track)

        if tracks is None:
            await ctx.reply("Could not find any songs.")
            return
        
        if isinstance(tracks, wavelink.TrackPlaylist):
            for track in tracks.tracks:
                track = wavelink.Track(track.id, track.info)
                await controller.queue.put(track)
            await ctx.reply(f"Added the playlist {tracks.data['playlistInfo']['name']} with {len(tracks.tracks)} songs to the queue.", mention_author = False)
        else:
            await controller.queue.put(tracks[0])
            await ctx.reply(f"Added {tracks[0]} to the queue.", mention_author = False)
    
    @commands.command(aliases = ['search'])
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    @commands.cooldown(rate = 1, per = 3.0, type = commands.BucketType.guild)
    async def search(self, ctx, *, track):
        '''
        Search the input track and return 10 results.
        You can then copy the link of the one you want into `play`.

        **Usage:** `{prefix}{command_name} {command_signature}`
        **Cooldown:** 3 seconds per 1 use (guild)
        **Example:** {prefix}{command_name} rickroll

        **You need:** None.
        **I need:** `Read Message History`, `Send Messages`
        '''

        tracks = await self.bot.wavelink.get_tracks(f'ytsearch:{track}')
        if tracks is None:
            await ctx.reply("Could not find any songs.")
            return
        
        embed = Facility.get_default_embed(
            title = "Top 10 search results",
            description = "",
            timestamp = dt.datetime.utcnow(),
            author = ctx.author
        )

        for index, track in enumerate(tracks):
            embed.description += f"**{index + 1}.** [{track.title}]({track.uri}) - {dt.timedelta(milliseconds = track.duration)}\n\n"
            if index == 9:
                break
        
        await ctx.reply(embed = embed, mention_author = False)

    @commands.command()
    async def repeat(self, ctx):
        controller = self.get_controller(ctx)
        controller.is_single_loop = not controller.is_single_loop
        if controller.is_single_loop and not controller.player:
            await ctx.reply("There's nothing to loop.")
            controller.is_single_loop = False
            return
        
        if controller.is_single_loop:
            await ctx.reply("🔂 **Enabled!**", mention_author = False)
        else:
            await ctx.reply("🔂 **Disabled!**", mention_author = False)
    
    @commands.command()
    async def queue(self, ctx):
        controller = self.get_controller(ctx)
        embed = Facility.get_default_embed(timestamp = dt.datetime.utcnow())
        if controller.queue.empty() or controller.player.is_playing == False:
            embed.description = "*There are no songs currently in queue.*"
        else:
            import itertools
            current = controller.current_track
            upcoming = list(itertools.islice(controller.queue._queue, 0, 5))

            embed = Facility.get_default_embed(
                title = f"Queue for {ctx.guild}",
                timestamp = dt.datetime.utcnow(),
                author = ctx.author
            ).add_field(
                name = "Now playing:",
                value = f"[{current.title}]({current.uri}) - {dt.timedelta(milliseconds = current.duration)}",
                inline = False
            )

            text = ""
            for index, track in enumerate(upcoming):
                text += f"`{index + 1}`. [{track.title}]({track.uri}) - {dt.timedelta(milliseconds = track.duration)}\n"
            
            embed.add_field(
                name = "Up Next:",
                value = text,
                inline = False
            )
            embed.set_footer(
                text = embed.footer.text + " | Queue Loop: " + ('✅' if controller.is_queue_loop else '❌'),
                icon_url = embed.footer.icon_url
            )
        
        await ctx.reply(embed = embed, mention_author = False)
    
    @commands.command()
    async def pause(self, ctx):
        controller = self.get_controller(ctx)
        if not controller.player.is_playing:
            await ctx.reply("There's nothing to pause you dummy.")
            return
        if controller.player.paused:
            await controller.player.set_pause(False)
            await ctx.reply("Resumed!", mention_author = False)
        else:
            await controller.player.set_pause(True)
            await ctx.reply("Paused!", mention_author = False)
    
    @commands.command()
    async def resume(self, ctx):
        controller = self.get_controller(ctx)
        if not controller.player.is_playing:
            await ctx.reply("There's nothing to resume from.")
            return
        if controller.player.paused:
            await controller.player.set_pause(False)
            await ctx.reply("Resumed!", mention_author = False)
        else:
            await ctx.reply("Player is not paused.")
    
    @commands.command()
    async def volume(self, ctx, *, new_volume : int):
        controller = self.get_controller(ctx)
        
        new_volume = max(min(new_volume, 200), 0)
        controller.volume = new_volume

        await controller.player.set_volume(new_volume)
        await ctx.reply(f"Set volume to {new_volume}.", mention_author = False)

    @commands.command()
    async def skip(self, ctx):
        controller = self.get_controller(ctx)
        if not controller.player.is_playing:
            await ctx.reply("There are no songs to skip.")
            return
        
        await controller.player.stop()
        await ctx.reply("Skipped!", mention_author = False)

    @commands.command()
    async def stop(self, ctx):
        controller = self.get_controller(ctx)
        if not controller.player.is_playing:
            await ctx.reply("There's nothing to stop.")
            return
        while not controller.queue.empty():
            await controller.queue.get()
        await controller.player.stop()
        
        await ctx.reply("Stopped the player.", mention_author = False)
    
    @commands.command(aliases = ['dc'])
    async def disconnect(self, ctx):
        controller = self.get_controller(ctx)
        while not controller.queue.empty():
            await controller.queue.get()
        await controller.player.stop()
        
        await controller.player.disconnect()

def setup(bot):
    bot.add_cog(Music(bot))