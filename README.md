# MichaelBot

MichaelBot is a bot written in Python using [discord.py](https://github.com/Rapptz/discord.py).

The reason why this bot exist is because...it's fun, and I like to make one.

Join the [support server](https://discord.gg/jeMeyNw) to get help.

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

- Interactive music menu

![music](./img/music.png)

- Support playlist

![playlist](./img/playlist.png)

- Report and suggest features

![bug](./img/bug.png)

- And the best thing is...all features are free-guaranteed.

  - Features like changing volume in Rythm is absolutely pennyless in this bot (meaning you don't have to pay to use this).

## Limitations

- Not bug-free ie. a lot of bugs.
- No support for multi-server yet.

  - By this, I mean that not all commands and features are guaranteed to work properly on multiple servers.

- Uptime not 24/7.

## Development notes

I would prefer if you don't run the bot yourself. The source here is for educational purpose.

Nevertheless, the step to run this bot is fairly simple:

- Clone this directory.

``` git
git clone https://github.com/MikeJollie2707/MichaelBotPy.git
```

- Go into the `setup` directory, create a token `json` file, name it whatever.

``` json
# Let's say I'm creating a bot.json. Here's what the inside should look like
{
    "token": "<token here>"
}
```

- Go into the `config.json` file, add your bot in the following pattern:

``` json
{
    "TheIndexWithoutSpace":{
        "name": "Undecided if optional or not",
        "version": "Optional",
        "description": "Optional, but recommended",

        "prefix": "Required",
        "token": "The token file you created (bot.json)"
    }
}
```

- To run the bot, run the file `bot.py`.

``` terminal
python3.6 bot.py TheIndexWithoutSpace_in_configjson
```

- To edit categories, look into `categories` folder.
- Do not alter `data` without reasonable reason to do so.

## License

This project is under the [MIT LICENSE](LICENSE).

## Contributing

You can contribute to this bot via:

- Development: I'm doing this all alone, so if I have 1 or more people, that'd be great help.
- Testing: use commands, do actions and report via the `report` command.

Any sort of contributions are highly appreciated.

## TODO

- [ ] Find a database.
  - [ ] Learn PostgreSQL
  - [ ] Split `Logging` into different channels.
  - [ ] Track many stuffs.
- [ ] Debug everything.
  - [x] `Core`
  - [x] `Dev`
  - [x] `Logger`
  - [x] `Moderation`
  - [ ] `Music`
  - [ ] `Server`
  - [ ] `Utility`
  - [ ] `Events`
- [ ] Add `Account Age` to `profile`
- [ ] Update documentation.

## Acknowledgement

This is a special thanks to resources that helped me significantly in developing the bot.

- [Rapptz](https://github.com/Rapptz) (discord.py)
- [discord.py Documentation](https://discordpy.readthedocs.io/en/latest/api.html)
- [Frederikam](https://github.com/Frederikam) (Lavalink)
- [PythonistaGuild](https://github.com/PythonistaGuild) (WaveLink)
- [Music advanced example](https://github.com/PythonistaGuild/Wavelink/blob/master/examples/advanced/advanced.py) (code used in music.py)
- [discord.py Discord support server](https://discord.gg/r3sSKJJ)
- [IssueHunt](https://issuehunt.io/blog/How-to-write-a-Discord-bot-in-Python-5bb1f0e3c556c5005573c508) (the guide I used when I started making the bot)
