# MichaelBot

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

Nevertheless, the step to run this bot is here (it's quite complicated):

- You only need: `python3`, `virtualenv`, `git`, all at latest version will be good.

- Clone this directory.

``` git
git clone https://github.com/MikeJollie2707/MichaelBot.git
```

- Go into the `setup` directory, create a token `json` file, name it whatever (with no space).

``` json
// bot.json
{
    "token": "<token here>"
}
```

- Also create a db `json` file, again, name it whatever.

```json
// dbexample.json
{
    "host": "localhost, or wherever you host your PostgreSQL",
    "user": "user name",
    "database": "name of the db",
    "password": "password"
}
```

- Go into the `config.json` file, add your bot in the following pattern:

``` json
{
    "TheIndexWithoutSpace": {
        "name": "Undecided if optional or not",
        "version": "Required, for now",
        "description": "Required, for now",
        "prefix": "Required",
        "debug": false,

        "token": "The token file you created (bot.json)",
        "db": "The db file you created (dbexample.json)"
    }
}
// There's example in setup/config.json in case you're confused.
```

- Setup a virtual environment.

``` terminal
# Linux
python3 -m pip virtualenv venv

# Windows
py -3 -m pip virtualenv venv
```

- Activate the environment.

``` terminal
# Linux
source venv/bin/activate

# Windows
# You don't need to do this
```

- Install the requirement packages.

``` terminal
# Linux
python3 -m pip install -r requirement.txt

# Windows
py -3 -m pip install -r requirement.txt
```

- To run the bot, run the file `bot.py`.

``` terminal
# Linux
python3 bot.py TheIndexWithoutSpace

# Windows
# Because somehow py -3 will use the default Python interpreter,
# so for now I only find this will call the virtual Python interpreter.
.\venv\Scripts\python.exe bot.py TheIndexWithoutSpace
```

  - If you're on Linux, you can also mark the `startup.sh` file as executable, edit the absolute path to repo to run it using `./startup.sh`.
  - (EXPERIMENT) If you're on Windows, you can also use `MichaelBot.ps1`, run it in PowerShell and use `. ".\MichaelBot.ps1"` (haven't really tested this yet, but I did do this on a small python file).

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
  - [ ] Add utility db methods.
  - [ ] Add basic currency.
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
