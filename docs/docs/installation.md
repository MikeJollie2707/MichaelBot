<!-- omit in toc -->
# Installation

I'd prefer you not to clone this to develop your own bot. The code here is for educational purpose.

Nevertheless, I'll still provide you the installation steps.

<!-- omit in toc -->
## Table of Contents

- [Prerequisite](#prerequisite)
- [Steps](#steps)
    - [Configure](#configure)
    - [Setup database (optional)](#setup-database-optional)
    - [Setup Lavalink (optional)](#setup-lavalink-optional)
    - [Install packages](#install-packages)
    - [Run script](#run-script)

## Prerequisite

- It's recommended that you either use Linux or WSL (no idea what this is, but it sounds like Linux inside Windows). Windows instruction is also here, but some might be incorrect because I rarely use it.
- You need `git` and `python3` (on Windows, it's `py -3`). You should also install `pip` and `virtualenv` under `python3`.
- You need PostgreSQL installed and setup (it's pretty complex, and I'm planning to make this optional).
- Recommend to install latest `java` to run music.

## Steps

### Configure

Clone this directory.

``` git
git clone https://github.com/MikeJollie2707/MichaelBot.git
```

Go into folder `setup` and create a `json` file (here I use `secret.json`).

```json
// secret.json
{
    "token": "bot token",
    "host": "localhost or wherever you host PostgreSQL",
    "port": 5432,
    "user": "username",
    "database": "name of the database",
    "password": "password"
}
```

In `setup`, there should also be a `config.json` file. Open it and fill in necessary information. You can use my bot as the template.

```json
// config.json
{
    "BotIndex": {
        "name": "Undecided if optional or not",
        "version": "Required",
        "description": "Required",
        "prefix": "Required",
        "debug": false,

        "secret": "secret.json"
    }
}
```

### Setup database (optional)

*This is optional, but the features will be limited. The option to not use database is also currently experimental.*

You need to have a database created already. It's usually hosted on port 5432.

Before running the bot first time, you need to find `setupdb.py` and run it once so it can create the tables. You only need to do this once, or every time you change the schema.

### Setup Lavalink (optional)

You need to have the latest `java` installed.

Go into `./lib/Lavalink3.3` and edit `server.port`, `server.address`, and `lavalink.server.password` if needed.

### Install packages

Next, setup a virtual environment and install the required packages.

```terminal
# Linux
python3 -m virtualenv venv
source venv/bin/activate
python3 -m pip install -r requirement.txt

# Windows
py -3 -m virtualenv venv
.\venv\Scripts\activate.bat
pip install -r requirement.txt
```

Finally, run the bot.

```terminal
# Linux
python3 bot.py BotIndex

# Windows
py bot.py BotIndex
```

Note: if you do not setup Lavalink, you need to provide `--nomusic` or `--fastdebug` after `BotIndex`.

### Run script

If you don't like typing `python3 bot.py BotIndex` all the time when you want to start the bot, there's a script `run.sh` (for Linux) and `run.ps1` (for Windows Powershell) for convenience.

For `run.sh`, you can edit `MICHAEL_DIR` to your current directory, and `BOT_INDEX` for the bot's index. Mark it executable, and just double click it the next time you want to run.

- Additionally, for developing purposes, you can provide options when typing in the terminal to run the bot in the state you want. Some options are `--nomusic` (does not load Lavalink and Music cog, which saves time and resources), `--debug` (display debug information), `--fastdebug` (`--nomusic` and `--debug` because you need to wait for a long time for Lavalink to load).

For `run.ps1`, just change the `$BotIndex`, and then open Powershell, run the script using `. ".\run.ps1"`. Current no support for `cmd` because it can be written by yourself.
