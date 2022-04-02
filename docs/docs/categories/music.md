# Music Category

Music commands.

## `join [voice_channel = None]`

Join a voice channel.

Type: `Prefix Command`, `Slash Command`

Cooldown: 5 seconds after 1 use per guild.

Parameters:

- `voice_channel`: The voice channel to join. Default to the VC you're in.

Aliases: `connect`

## `leave`

Leave the voice channel.

Type: `Prefix Command`, `Slash Command`

Aliases: `dc` (recommended), `disconnect`

## `np`

Get info about the current track.

Type: `Prefix Command`, `Slash Command`

Cooldown: 1 second after 1 use per guild.

Aliases: `now_playing`

## `play <*query>`

Play the query or add it to the queue.

Type: `Prefix Command`, `Slash Command`

Cooldown: 5 seconds after 5 uses per guild.

Parameters:

- `query`: The query to play (url, name, etc.)

Aliases: `p` (recommended)

## `pause`

Toggle pausing the player.

Type: `Prefix Command`, `Slash Command`

c

## `search <*track>`

Search and return 10 relevant results. You can then copy the desired link into `play`.

Type: `Prefix Command`, `Slash Command`

Cooldown: 2 seconds after 1 use per guild.

Parameters:

- `track`: Keywords to search. Example: `blend w`.

## `seek <position>`

Jump to the provided timestamp.

Type: `Prefix Command`, `Slash Command`

Cooldown: 1 second after 1 use per guild.

Parameters:

- `position`: Timestamp to jump to.

## `repeat`

Toggle repeating the track.

Type: `Prefix Command`, `Slash Command`

Cooldown: 1 second after 1 use per guild.

## `volume <vol>`

Set the volume of the player.

Type: `Prefix Command`, `Slash Command`

Cooldown: 5 seconds after 1 use per guild.

Parameters:

- `vol`: Volume to set (0-200).

Additional Info:

- It's recommended to use the built-in feature `User Volume` instead of this command.

## `queue`

Display the song queue.

Type: `Prefix Command`

Cooldown: 2 seconds after 1 use per guild.

Aliases: `q` (recommended)

### `queue view`

Display the song queue. This exists for Slash Commands.

Type: `Prefix Command`, `Slash Command`

Cooldown: 2 seconds after 1 use per guild.

### `queue clear`

Clear the entire queue but the current track.

Type: `Prefix Command`, `Slash Command`

### `queue shuffle`

Shuffle the queue.

Type: `Prefix Command`, `Slash Command`

### `queue loop`

Toggle queue loop.

Type: `Prefix Command`, `Slash Command`

### `queue move <from_index> <to_index>`

Move a track in queue to a new order index.

Type: `Prefix Command`, `Slash Command`

Cooldown: 5 seconds after 1 use per guild.

Parameters:

- `from_index`: The index in the queue to move.
- `to_index`: The index in the queue where you want the track to be.

### `queue remove <index>`

Remove a track in the queue.

Type: `Prefix Command`, `Slash Command`

Cooldown: 5 seconds after 1 use per guild.

Parameters:

- `index`: The index in the queue to remove.

### `skip`

Skip the current track.

Type: `Prefix Command`, `Slash Command`

Cooldown: 2 seconds after 1 use per guild.

Aliases: `s` (recommended)

### `stop`

Stop the player.

Type: `Prefix Command`, `Slash Command`

*Last updated on Apr 1, 2022*
