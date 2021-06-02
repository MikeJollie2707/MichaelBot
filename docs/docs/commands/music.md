<!-- omit in toc -->
# Music

*This document is missing many functions/methods due to the complexity. It is currently only shows the commands.*

These are commands that play music in voice channel. It is currently support YouTube, SoundCloud, Twitch, Vimeo and Mixer.

This is recommended for 1-2 people per vc, due to no support in song voting (for example, a skip will skip indeterminately).

<!-- omit in toc -->
## Table of Contents
- [connect](#connect)
- [now_playing](#now_playing)
- [pause](#pause)
- [play](#play)
- [queue](#queue)
    - [queue clear](#queue-clear)
    - [queue loop](#queue-loop)
    - [queue move](#queue-move)
    - [queue remove](#queue-remove)
    - [queue shuffle](#queue-shuffle)
- [repeat](#repeat)
- [resume](#resume)
- [search](#search)
- [seek](#seek)
- [skip](#skip)
- [stop](#stop)
- [volume](#volume)

## connect

Connect to a voice channel. If the channel is not specified, it'll connect to the voice channel you're in.

*This command is implicitly called if the user invoke [`play`](#play) without the bot inside a voice channel.*

**Aliases:** `join`

**Usage:** `<prefix>connect [voice channel]`

**Parameters:**

- `voice channel`: A Discord voice channel. Can be either `ID/name`.

**Cooldown:** 2 seconds per 1 use (guild)

**Example:** `$connect discord-got-talents`

**You need:** None.

**The bot needs:** `Read Message History`, `Send Messages`.

## now_playing

Display the current playing song.

**Aliases:** `np`

**Usage:** `<prefix>now_playing`

**Cooldown:** 3 seconds per 1 use (guild)

**Example:** `$np`

**You need:** None.

**The bot needs:** `Read Message History`, `Send Messages`.

## pause

Toggle pausing the player.

**Usage:** `<prefix>pause`

**Cooldown:** 1 second per 1 use (guild)

**Example:** `$pause`

**You need:** None.

**The bot needs:** `Read Message History`, `Send Messages`.

## play

Play a song from YouTube, SoundCloud, Twitch, Vimeo, and Mixer.

You can provide a link or the song's title/keywords. You can also use a playlist link.

*This command implicitly call [`connect`](#connect) if the user invoke without the bot inside a voice channel.*

**Aliases:** `p`

**Usage:** `<prefix>play <track>`

**Parameters:**

- `track`: The resource to play. This can be either a valid link or keywords in the title.

**Example:** `$play white palace ost`

**You need:** None.

**The bot needs:** `Add Reactions`, `Read Message History`, `Send Messages`.

## queue

Display the song queue.

**Aliases:** `q`

**Usage:** `<prefix>queue`

**Cooldown:** 3 seconds per 1 use (guild)

**Example:** `$queue`

**You need:** None.

**The bot needs:** `Add Reactions`, `Read Message History`, `Send Messages`.

***Subcommands:*** [`clear`](#queue-clear), [`loop`](#queue-loop), [`move`](#queue-move), [`remove`](#queue-remove), [`shuffle`](#queue-shuffle).

### queue clear

Clear queue, but keep the current song playing.

**Usage:** `<prefix>queue clear`

**Cooldown:** 5 seconds per 1 use (guild)

**Example:** `$queue clear`

**You need:** None.

**The bot needs:** `Read Message History`, `Send Messages`.

### queue loop

Toggle queue loop. This will disable single song loop if it is enabled.

**Usage:** `<prefix>queue loop`

**Cooldown:** 5 seconds per 1 use (guild)

**Example:** `$queue loop`

**You need:** None.

**The bot needs:** `Add Reactions`, `Read Message History`, `Send Messages`.

### queue move

Move a song in the queue to a new order index.

**Usage:** `<prefix>queue move <src> <dest>`

**Parameters:**

- `src`: The index of the song you want to move.
- `dest`: The index you want the new song to move to.

**Cooldown:** 5 seconds per 1 use (guild)

**Example:** `$queue move 3 1`

**You need:** None.

**The bot needs:** `Read Message History`, `Send Messages`.

### queue remove

Remove a song from the queue using the order index.

**Usage:** `<prefix>queue remove <index>`

**Parameters:**

- `index`: The index of the song you want to remove.

**Cooldown:** 5 seconds per 1 use (guild)

**Example:** `$queue remove 2`

**You need:** None.

**The bot needs:** `Read Message History`, `Send Messages`.

### queue shuffle

Shuffle the queue.

**Usage:** `<prefix>queue shuffle`

**Cooldown:** 5 seconds per 1 use (guild)

**Example:** `$queue shuffle`

**You need:** None.

**The bot needs:** `Add Reactions`, `Read Message History`, `Send Messages`.

## repeat

Toggle single song looping.

**Usage:** `<prefix>repeat`

**Cooldown:** 3 seconds per 1 use (guild)

**Example:** `$repeat`

**You need:** None.

**The bot needs:** `Add Reactions`, `Read Message History`, `Send Messages`.

## resume

Resume the currently paused song.

**Usage:** `<prefix>resume`

**Example:** `$resume`

**You need:** None.

**The bot needs:** `Read Message History`, `Send Messages`.

## search

Search the input track and return 10 relevant results. You can then copy the link of the one you want into `play`.

**Usage:** `<prefix>search <track>`

**Parameter:**

- `track`: Should be keywords related to the song you want to search.

**Cooldown:** 3 seconds per 1 use (guild)

**Example:** `$search resting grounds`

**You need:** None.

**The bot needs:** `Read Message History`, `Send Messages`.

## seek

Seek to the provided timestamp. If the timestamp exceeds the track's duration, it'll play the next song in queue.

**Usage:** `<prefix>seek <time>`

**Parameter:**

- `time`: A time interval. Should be in the general `hh:mm:ss` format, although `3m` also works (but it looks weird no?).

**Cooldown:** 5 seconds per 1 use (guild)

**Example:** `$seek 3:20`

**You need:** None.

**The bot needs:** `Read Message History`, `Send Messages`.

## skip

Skip the current song.

If single song loop is enabled, the next song will be the same as the current song.

**Aliases:** `s`

**Usage:** `<prefix>skip`

**Example:** `$s`

**You need:** None.

**The bot needs:** `Add Reactions`, `Read Message History`, `Send Messages`.

## stop

Stop the player and clear the queue. It also resets single song loop and queue loop to default, but retains the volume.

**Usage:** `<prefix>stop`

**Cooldown:** 5 seconds per 1 use (guild)

**Example:** `$stop`

**You need:** None.

**The bot needs:** `Read Message History`, `Send Messages`.

## volume

Adjust the player's volume. By default, the player has a volume of 50.

**Aliases:** `vol`

**Usage:** `<prefix>volume <new volume>`

**Parameter:**

- `new volume`: The value you want the volume to be at. It is in the range 0 to 200.

**Cooldown:** 3 seconds per 1 use (guild)

**Example:** `$vol 100`

**You need:** None.

**The bot needs:** `Read Message History`, `Send Messages`.

*This document is last updated on June 1st (PT) by MikeJollie#1067*
