# Installation

All instructions are geared towards Ubuntu (Kubuntu specifically) because that's what I use.

- Instructions for Windows is available, but be aware I don't test them often.

## Prerequisites

- Requires: Python 3.8+ (ideally latest), Git, `pip`, `virtualenv`/`python3-venv` under Python.
- Optional: Lavalink (more information below), Docker (for Lavalink), PostgreSQL (more information below).

## About Lavalink

Lavalink is optional for the bot. If you don't plan to use the music functionality, you can simply edit `main.py` the `EXTENSION` variable to exclude `categories.music`. Then you can completely ignore this section and move on. Otherwise, you'll need to finish setting up Lavalink and get it running.

There are 2 options to host Lavalink: you can host it directly using the `.jar` file or use Docker. I personally switched to Docker recently so I won't tell which one you should go. In either cases, you'll need a file `application.yml` to configure the server. An example is provided in `./lib/Lavalink`. You'll also need Java 13+, which can be downloaded [here](https://adoptopenjdk.net/archive.html?variant=openjdk13&jvmVariant=hotspot) or somewhere else (there are a billion places to download a billion java versions I'm not gonna even bother).

### Running Lavalink (.jar)

- Download [`Lavalink.jar`](https://github.com/freyacodes/Lavalink/releases), or use the one currently in `./lib/Lavalink/`.
- Run `java -jar <path to Lavalink.jar>`. Lavalink server should start running now. By default, it'll run on `localhost:2333` unless you configure it in `application.yml`.

### Running Lavalink (Docker)

This is not tested on Windows.

- Download Docker. [Here](https://docs.docker.com/engine/install/ubuntu/) is the guide for Ubuntu.
- Run `docker pull fredboat/lavalink:master`. This will pull the stable image.
- Run `docker run --name <name> -p <port>:<port> -d -v <path-to-application.yml>:/opt/Lavalink/application.yml fredboat/lavalink:master`, where `<name>` is the name of the process, `<port>` is the port the server is on, and `<path-to-application.yml>` is the absolute path to the config file.
- To stop the process, run `docker stop <name>`.

## About PostgreSQL

PostgreSQL is optional for the bot, but is strongly recommended. Without a database, some features will be missing, such as prefix config, blacklisting, logging, etc. In addition to that, although the code can handle no database scenario on its own, it is not well-tested for such cases, so there might be some edge cases here and there.

This is a pretty fine guide to install PostgreSQL on Ubuntu: https://linuxhint.com/postgresql_installation_guide_ubuntu_20-04/

After installing Postgres, create a database and check the connection info. You'll need this later.

## Build Instructions

The following instructions has been tested with `bash` and `Powershell`. You'll need to replace the `python` command mentioned below with whatever your system has (`python3` or `python3.x` for Linux, `python` for Windows).

1. Clone the repository into the current folder.

```sh
git clone https://github.com/MikeJollie2707/MichaelBot.git .
```

2. Activate virtual environment and install libraries.

```sh
# Linux
python -m pip venv venv
source ./venv/bin/activate
python -m pip install -r requirement.txt

# Windows
# From my experience, / still works, but if it doesn't, use \
python -m pip venv venv
./venv/Scripts/Activate.ps1
# This is important; uvloop is not available on Windows.
python -m pip install -r win_requirement.txt
```

3. Configure the bot.

Inside `./setup`, create a `.json` file. I'll call it `secret.json`.

```json
// secret.json
{
    "token": "Bot token here",
    "host": "localhost",
    "port": 5432,
    "database": "database name",
    "user": "user name",
    "password": "password",
    "weather_api_key": "api key"
}
```

- If you don't have a database and/or `weather_api_key`, leave them as dummy values (`""` and `0`).

Within `./setup`, there's also another file called `config.json`. The file has the following structure:

```json
// config.json
{
    "BotIndex": {
        "version": "Required",
        "description": "Required",
        "prefix": "Required",
        "launch_options": "Optional",
        "default_guilds": [123456],

        "secret": "secret.json"
    }
}
```

- `BotIndex`: the index you'll refer to the bot when you launch it from the terminal. Usually the bot name without space.
- `version`: the bot version. Just fake something up like `69.69beta` if you don't really care about this.
- `description`: the bot's about me. Discord doesn't have a way to retrieve this so this is required for now.
- `prefix`: the bot's default prefix.
- `launch_options`: an optional string to pass into the bot when it launches. This mostly affects terminal logging. Acceptable options are:
    - `-d` or `--debug`: Launch the bot in debug mode. This will set the log level to `DEBUG` but more importantly, it'll apply slash commands to `default_guilds` immediately (no need to wait at most 1 hour). If this is passed, `default_guilds` must also be non-empty.
    - `-q` or `--quiet`: Launch the bot in quiet mode. This will disable terminal logging, but any uncaught exceptions will still spawn in `stderr`.
- `default_guilds`: a list of guilds' ids to apply slash commands immediately. This is required if the bot is launched in debug mode.
- `secret`: the file name that contains your bot's secret like token.

You can view my bot config as an example.

4. (Optional) If you have a database, you'll need to set up the tables beforehand. You only need to do this once.

```sh
python dbsetup.py BotIndex
```

5. Run the bot.

```sh
python -OO main.py BotIndex
```

## What's next?

For personal convenience, I also have a template script to run the bot in different modes. You can check it out at `run.sh` (Kubuntu) or `run.ps1` (Windows). It'll *only* run the bot. You'll need to run Lavalink and PostgreSQL on your own.
