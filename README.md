# MichaelBot

## UPDATE

**From Jan 10, 2022, MikeJollie will not be active on this repository for a while.** More information below.

The entire code base of this bot depends on discord.py. However, the library is no longer maintained a while ago (check [here](https://gist.github.com/Rapptz/4a2f62751b9600a31a0d3c78100287f1) for the reasons). Because Discord continues to update, it is inevitable to move on to a different library. Although I can wait until another dpy fork is mature enough to stand its name out, frankly, I don't have any hope.

Besides the end of discord.py, I also need to focus a bit more in real life (university in particular). I don't exactly have the time to work on make huge features like I did last year, so my motivation is somewhat low. Furthermore, there are a lot of ugly codes that I never really get to resolve. Just look how ugly error handling is in `events.py`. How about the code in `db.py`? It looks repetitive, and the fact I have no endpoints for database means I'm probably doing something wrong. Those are the biggest issues, although it doesn't just limit to that. If I stick to this code, I'm working on legacy code with a legacy library on a constant changing platform. Meticulously fixing the issues won't really work either, because it'd requires a huge concentration on the matter, and as I said before, I don't have the motivation for that.

Because of those above reasons, I'll not working on this repository for a while. I'll be working on a rewrite of this bot, which I'll try to make sure it looks cleaner than it is now. These experimental versions *won't* be as complete as MichaelBot. At best, it covers the bare minimum mechanics I used in this project. There are no definite libraries I'm going yet. I might try Pycord (which seems to be somewhat popular?), Hikari, or maybe even try different languages like JavaScript or C++. Since I'll be experimenting different libraries, in the mean time, the `master` branch will not be updated for a while. The `dashboard` branch might still get updated, but it won't take too long before development pauses there too.

I'll put experimental versions' links here over time if I create a new one.

- [MichaelHikari](https://github.com/MikeJollie2707/MichaelHikari) ([Hikari](https://github.com/hikari-py/hikari))

*TLDR: I'm not working on this repository because I need to experiment other alternatives for discord.py. Those alternatives won't be as complete as MichaelBot.*

Okay, now back to the old `README.md`!

MichaelBot is a bot written in Python using [discord.py](https://github.com/Rapptz/discord.py).

The reason why this bot exist is because...it's fun, and I like to make one.

Join the [support server](https://discord.gg/jeMeyNw) to get help.

Alternatively, you may find what you need in the [bot documentation](https://mikejollie2707.github.io/MichaelBot/).

## Features

- Basic information

![info](./img/info.png)

- Interactive help menu

![help](./img/help.png)

- Detailed command description

![help2](./img/help2.png)

- Moderation commands

![mod](./img/kick.png)

- Detailed logging

![log](./img/log.png)

- Fun commands

![fun](./img/fun.png)

- Utility commands

![utility](./img/utility.png)

- Warm welcome messages

![welcome](./img/welcome.png)

- Report and suggest features

![bug](./img/bug.png)

- And the best thing is...all features are free.

## Limitations

- Not bug-free ie. a lot of bugs.
- No support for multi-server yet.
  - By this, I mean that not all commands and features are guaranteed to work properly on multiple servers.

- Uptime not 24/7.

## Development notes

I would prefer if you don't run the bot yourself. The source here is for educational purpose.

Nevertheless, the step to run this bot is [here](docs/docs/installation.md) (it's quite complicated).

## License

This project is under the [MIT LICENSE](LICENSE).

## Contributing

You can contribute to this bot via:

- Development: I'm doing this all alone, so if I have 1 or 2 more people, that'd be great help.
- Testing: use commands, do actions and report via the `report` command.

Any sort of contributions are highly appreciated.

## TODO

- [ ] Find a database.
  - [x] Learn PostgreSQL
  - [ ] Split `Logging` into different channels.
  - [ ] Track many stuffs.
  - [x] Add utility db methods.
  - [x] Add basic currency.
  - [ ] Add some moderation commands.
  - [ ] Add auto-role.
- [ ] Add `Account Age` to `profile`
- [x] Add game commands.
- [ ] Update documentation.

## Resources

These are resources I use for this bot.

- [Rapptz](https://github.com/Rapptz) (discord.py)
- [discord.py Documentation](https://discordpy.readthedocs.io/en/latest/api.html)
- [Frederikam](https://github.com/freyacodes/Lavalink) (Lavalink)
- [PythonistaGuild](https://github.com/PythonistaGuild) (WaveLink)
- [Music advanced example](https://github.com/PythonistaGuild/Wavelink/blob/master/examples/advanced/advanced.py) (code used in music.py)
- [discord.py Discord support server](https://discord.gg/r3sSKJJ)
- [IssueHunt](https://issuehunt.io/blog/How-to-write-a-Discord-bot-in-Python-5bb1f0e3c556c5005573c508) (the guide I used when I started making the bot)
- [The obvious](https://google.com)
