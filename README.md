# MichaelHikari

MichaelHikari is an experimental repository for [MichaelBot](https://github.com/MikeJollie2707/MichaelBot). Because the development for [discord.py](https://gist.github.com/Rapptz/4a2f62751b9600a31a0d3c78100287f1) stopped a while ago, and even now, I still yet to find a reliable or "good" discord.py forks for my bot. As such, this repository is created to experiment with a new library, [Hikari](https://github.com/hikari-py/hikari), instead.

Hikari provides a very new interface to work with. With a huge documentation and very few basic examples, it's hard to get into. Luckily, the command wrapper for Hikari, [lightbulb](https://github.com/tandemdude/hikari-lightbulb), is extremely similar to discord.ext.commands, so it's an easy place to pick up. The other one, [tanjun](https://github.com/FasterSpeeding/Tanjun), is fairly complicated, so I won't be using it.

## What's New?

Since it's experimental, there won't be any huge commands like economy or moderation. Those requires a database, and porting those over to the new code is too time consuming. As a trade-off, this repository is using application command, which is the official Discord's implementation of command.

This system is pretty complicated, with many things to learn like interactions, components, etc. Really weird, but they're pretty helpful.

## How to Run

The structure should be similar to the old bot, so get rid of some flags and the launch script should be good to go.
