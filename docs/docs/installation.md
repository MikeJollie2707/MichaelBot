<!-- omit in toc -->
# Installation

I'd prefer you not to clone this to develop your own bot. The code here is for educational purpose.

Nevertheless, I'll still provide you the installation steps.

<!-- omit in toc -->
## Table of Contents

- [Prerequisite](#prerequisite)
- [Steps](#steps)
    - [Configure](#configure)
    - [Setup database](#setup-database)
    - [Install packages](#install-packages)
    - [Run script](#run-script)

## Prerequisite

- It's recommended that you either use Linux or WSL (no idea what this is, but it sounds like Linux inside Windows). Windows instruction is also here, but some might be incorrect because I rarely use it.
- You need `git` and `python3` (on Windows, it's `py -3`). You should also install `pip` and `virtualenv` under `python3`.
- You need PostgreSQL installed and setup (it's pretty complex, and I'm planning to make this optional).

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

### Setup database

*Currently this is required. I'm planning to make this optional.*

You need to have a database created already. It's usually hosted on port 5432.

Before running the bot first time, you need to find `setupdb.py` and run it once so it can create the tables. You only need to do this once, or every time you change the schema.

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

### Run script

If you don't like typing `python3 bot.py BotIndex` all the time when you want to start the bot, there's a script `startup.sh` (for Linux) and `run.ps1` (for Windows Powershell) for convenience. Both of them are currently in `setup` folder, although it might change.

For `startup.sh`, you can edit `MICHAEL_DIR` to your current directory, and `BOT_INDEX` for the bot's index. An absolute path is needed if you plan to put the file to one of the startup application. Mark it executable, and just double click it the next time you want to run.

For `run.ps1`, just change the `$BotIndex`, and then open Powershell, run the script using `. ".\run.ps1"`. Current no support for `cmd` because it can be written by yourself.