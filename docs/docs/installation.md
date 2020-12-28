<!-- omit in toc -->
# Installation

I'd prefer you not to clone this to develop your own bot. The code here is for educational purpose.

Nevertheless, I'll still provide you the installation steps.

<!-- omit in toc -->
## Table of Contents

- [Prerequisite](#prerequisite)
- [Steps](#steps)
  - [Alternative](#alternative)

## Prerequisite

- It's recommended that you either use Linux or WSL (no idea what this is, but it sounds like Linux inside Windows). Windows instruction is also here, but it might be a bit lengthy.
- You need `git` and `python3` (on Windows, it's `py -3`). You should also install `pip` and `virtualenv` under `python3`. If you don't know how, what's the point of Google?
- You need PostgreSQL installed and setup (it's pretty complex, and I'm planning to make this optional).

## Steps

Clone this directory.

``` git
git clone https://github.com/MikeJollie2707/MichaelBot.git
```

Go into folder `setup` and create two `json` files (here I use `bot.json` and `db.json`) (I'm planning to merge these two files into one).

```json
// bot.json
{
    "token": "bot token"
}
// db.json
{
    "host": "localhost or wherever you host PostgreSQL",
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
        "debug": false, // Optional key.

        "token": "bot.json", // The file contain the token
        "db": "db.json" // The file contain the db info
    }
}
```

Next, setup a virtual environment and install the required packages.

```terminal
# Linux
python3 -m virtualenv venv
source venv/bin/activate
python3 -m pip install -r requirement.txt

# Windows
py -3 -m virtualenv venv
# py -3 will still somehow use the global python interpreter,
# so for now this is the only way
.\venv\Scripts\python.exe -m pip install -r requirement.txt
```

Finally, run the bot.

```terminal
# Linux
python3 bot.py BotIndex

# Windows
.\venv\Scripts\python.exe bot.py BotIndex
```

### Alternative

Alternatively, if you don't like typing `python3 bot.py BotIndex` all the time when you want to start the bot, there's a script `startup.sh` (for Linux) and `run.ps1` (for Windows Powershell) to make life a bit easier.

For `startup.sh`, you can edit `MICHAEL_DIR` to your current directory. An absolute path is needed if you plan to put the file to one of the startup application. Mark it executable, and just double click it the next time you want to run. Remember to change the bot index also (I'm planning to make this more obvious).

For `run.ps1`, just change the `$BotIndex`, and then open Powershell, run the script using `. ".\run.ps1"`
