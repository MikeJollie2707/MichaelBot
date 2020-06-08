<!-- omit in toc -->
# Music [DEVELOPING]

*This section is labeled as [DEVELOPING], which means the function/command is currently under development and not available for testing.*

*This document is missing many functions/methods due to the complexity. It is currently only shows the commands.*

These are commands that play music in voice channel. It is currently support YouTube, SoundCloud, Twitch, Vimeo and Mixer.

## connect

Connect to a voice channel. If the channel is not specified, it'll attempt to join the current voice channel you're in.

This command is implicitly called if the user invoke [`play`](#play) without the bot inside a voice channel.

**Full Signature:**

```py
@commands.command(aliases = ["join"])
@commands.bot_has_guild_permissions(connect = True, speak = True, add_reactions = True, manage_messages = True, send_messages = True)
async def connect(self, ctx, *, channel : discord.VoiceChannel = None):
```

**Simplified Signature:**

```
connect [voicechannel]
join [voicechannel]
```

**Parameters:**

- `channel`: A Discord voice channel. This can be any of the following form: `<ID/name>`

**Example:** `$connect discord-got-talents`

**Expected Output:** *No output*.

## play

Play the audio provided by the query.

More precisely, it streams the audio, because the bot does not download the video.

This command implicitly call [`connect`](#connect) if the user invoke without the bot insdie a voice channel.

**Full Signature:**

```py
@commands.command(aliases = ['p'])
@commands.bot_has_guild_permissions(connect = True, speak = True, add_reactions = True, manage_messages = True, send_messages = True)
@commands.cooldown(rate = 1, per = 2.0, type = commands.BucketType.user)
async def play(self, ctx, *, query : str):
```

**Simplified Signature:**

```
play <query>
p <query>
```

**Parameters:**

- `query`: The resource to play. This can be any of the following form: `<link/name>`

**Example:** `$play You've been gnomed`

**Expected Output:** *an embed with information or reactions*

## now_playing

Indicate what song is playing.

**Full Signature:**

```py
@commands.command(aliases = ["np"])
@commands.bot_has__guild_permissions(connect = True, speak = True, add_reactions = True, manage_messages = True, send_messages = True)
@commands.cooldown(rate = 2, per = 15.0, type = commands.BucketType.user)
async def now_playing(self, ctx):
```

**Simplified Signature:**

```
now_playing
np
```

**Example:** `$np`

**Expected Output:** *an embed with information or reactions*

## pause

Pause the currently playing song. If there are more than one person in the voice channel, a poll will be created.
The admin/DJ reaction will cancel the vote and in favor of that person.

**Full Signature:**

```py
@commands.command()
@commands.bot_has_guild_permissions(connect = True, speak = True, add_reactions = True, manage_messages = True, send_messages = True)
async def pause(self, ctx):
```

**Simplified Signature:**

```
pause
```

**Example:** `$pause`

**Expected Output:** *a vote*

## resume

Resume the currently paused song. If there are more than one person in the voice channel, a poll will be created.
The admin/DJ reaction will cancel the vote and in favor of that person.

**Full Signature:**

```py
@commands.command()
@commands.bot_has_guild_permissions(connect = True, speak = True, add_reactions = True, manage_messages = True, send_messages = True)
async def resume(self, ctx):
```

**Simplified Signature:**

```
resume
```

**Example:** `$resume`

**Expected Output:** *a vote*

## skip

Skip the current song. If there are more than one person in the voice channel, a poll will be created.
The admin/DJ reaction will cancel the vote and in favor of that person.

**Full Signature:**

```py
@commands.command()
@commands.bot_has_guild_permissions(connect = True, speak = True, add_reactions = True, manage_messages = True, send_messages = True)
async def skip(self, ctx):
```

**Simplified Signature:**

```
skip
```

**Example:** `$skip`

**Expected Output:** *a vote*

## stop

Stop the player, disconnect and clear the queue. If there are more than one person in the voice channel, a poll will be created.
The admin/DJ reaction will cancel the vote and in favor of that person.

**Full Signature:**

```py
@commands.command(aliases = ["dc", "disconnect"])
@commands.cooldown(rate = 1, per = 15.0, type = commands.BucketType.guild)
@commands.bot_has_guild_permissions(connect = True, speak = True, add_reactions = True, manage_messages = True, send_messages = True)
async def stop(self, ctx):
```

**Simplified Signature:**

```
stop
```

**Example:** `$stop`

**Expected Output:** `*a vote, then the bot disconnects*

## volume

Adjust the player's volume.

**Full Signature:**

```py
@commands.command(aliases = ["vol"])
@commands.cooldown(rate = 1, per = 2.0, type = commands.BucketType.guild)
@commands.bot_has_guild_permissions(connect = True, speak = True, add_reactions = True, manage_messages = True, send_messages = True)
async def volume(self, ctx, *, value: int):
```

**Simplified Signature:**

```
volume <value>
```

**Parameter:**

- `value`: The value you want the volume to be at. It is in the range 0 to 1000.

**Example:** `$vol 100`

**Expected Output:** *an embed with verification*

## queue

Retrieve a list of current queued songs.

**Full Signature:**

```py
@commands.command()
@commands.cooldown(rate = 1, per = 10.0, type = commands.BucketType.user)
@commands.bot_has_guild_permissions(connect = True, speak = True, add_reactions = True, manage_messages = True, send_messages = True)
async def queue(self, ctx):
```

**Simplified Signature:**

```
queue
```

**Example:** `$queue`

**Expected Output:** *an embed with songs*

## shuffle

Shuffle the current queue. If there are more than one person in the voice channel, a poll will be created.
The admin/DJ reaction will cancel the vote and in favor of that person.

**Full Signature:**

```py
@commands.command(aliases = ["mix"])
@commands.cooldown(rate = 2, per = 10.0, type = commands.BucketType.user)
@commands.bot_has_guild_permissions(connect = True, speak = True, add_reactions = True, manage_messages = True, send_messages = True)
async def shuffle(self, ctx):
```

**Simplified Signature:**

```
shuffle
```

**Example:** `$shuffle`

**Expected Output:** *a vote*

## repeat

Repeat the currently played song one more time.

**Full Signature:**

```py
@commands.command(aliases = ["loop"])
@commands.bot_has_guild_permissions(connect = True, speak = True, add_reactions = True, manage_messages = True, send_messages = True)
async def repeat(self, ctx):
```

**Simplified Signature:**

```
repeat
```

**Example:** `$repeat`

**Expected Output:** *nothing*

*This document is last updated on May 26th (PT) by MikeJollie#1067*
