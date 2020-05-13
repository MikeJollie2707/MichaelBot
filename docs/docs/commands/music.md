<!-- omit in toc -->
# Music

These are commands that play music in voice channel. It is currently support YouTube, SoundCloud, Twitch, Vimeo and Mixer.

*This category is under beta testing, which means it is highly buggy and unstable.*

*This document is missing many functions/methods due to the complexity. It is currently only shows the commands.*

<!-- omit in toc -->
## Table of Contents

- [connect](#connect)
- [play](#play)
- [now_playing](#nowplaying)

## connect

Connect to a voice channel. If the channel is not specified, it'll attempt to join the current voice channel you're in.

This command is implicitly called if the user invoke [`play`](#play) without the bot inside a voice channel.

**Full Signature:**

```py
@commands.command(aliases = ["join"])
@commands.bot_has_permissions(connect = True, speak = True, add_reactions = True, manage_messages = True, send_messages = True)
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
@commands.bot_has_permissions(connect = True, speak = True, add_reactions = True, manage_messages = True, send_messages = True)
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
@commands.bot_has_permissions(connect = True, speak = True, add_reactions = True, manage_messages = True, send_messages = True)
@commands.cooldown(2, 15, commands.BucketType.user)
async def now_playing(self, ctx):
```

**Simplified Signature:**

```
now_playing
np
```

**Example:** `$np`

**Expected Output:** *an embed with information or reactions*


