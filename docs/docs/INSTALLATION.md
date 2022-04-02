# Installation

The instructions are geared towards Ubuntu (Kubuntu specifically) because that's what I use. Windows instruction might or might not work.

## Prerequisites

- Requires: Python 3.8+ (ideally latest), Git, `pip`, `virtualenv` OR `python3-venv` under Python, PostgreSQL (detailed instructions below). All of these can be installed using Google.
- Optional: Lavalink (detailed instructions below), Docker.

## About Lavalink

Lavalink is optional for the bot. If you don't plan to use the music functionality, you can simply remove `categories/music.py` and edit `main.py` a bit to exclude the file. Then you can completely ignore this section and move on. Otherwise, you'll need to finish setting up Lavalink and get it running.

There are 2 options to host Lavalink: you can host it directly using the `.jar` file or use Docker. I personally switched to Docker recently so I won't tell which one you should go. In either cases, you'll need a file `application.yml` to configure the server. An example is provided in `./lib/Lavalink`. You'll also need Java 13+, which can be downloaded [here](https://adoptopenjdk.net/archive.html?variant=openjdk13&jvmVariant=hotspot) or somewhere else (there are a billion places to download a billion java versions I'm not gonna even bother).

### Running Lavalink (.jar)

- Download [`Lavalink.jar`](https://github.com/freyacodes/Lavalink/releases), or use the one currently in `./lib/Lavalink/`.
- Run `java -jar <path to Lavalink.jar>`. Lavalink server should start running now. By default, it'll run on `localhost:2333` unless you configure it in `application.yml`.

### Running Lavalink (Docker)

- Download Docker. [Here](https://docs.docker.com/engine/install/ubuntu/) is the guide for Ubuntu.
- Run `docker pull fredboat/lavalink:master`. This will pull the stable image.
- Run `docker run --name <name> -p <port>:<port> -d -v <path-to-application.yml>:/opt/Lavalink/application.yml fredboat/lavalink:master`, where `<name>` is the name of the process, `<port>` is the port the server is on, and `<path-to-application.yml>` is the absolute path to the config file.
- To stop the process, run `docker stop <name>`.

## About PostgreSQL

As of the time of this writing, database support is very early, so it'll be mandatory to have a database. In the future, it'll be optional.

## Build Instructions

1. Clone the repository.

```sh
git clone https://github.com/MikeJollie2707/MichaelBot.git .
```

2. Activate virtual environment and install libraries.

```sh
python3 -m pip venv venv
source ./venv/bin/activate
python3 -m pip install -r requirement.txt
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
    "password": "password"
}
```

Within `./setup`, there's also another file called `config.json`. The file has the following structure:

```json
// config.json
{
    "BotIndex": {
        "version": "Required",
        "description": "Required",
        "prefix": "Required",
        "debug": false,

        "secret": "secret.json"
    }
}
```

- `BotIndex` is the index you'll refer to the bot when you launch it from the terminal.
- `version` is the bot version. Just fake something up like `69.69beta` if you don't really care about this.
- `description` is the bot's about me. Discord doesn't have a way to retrieve this so this is required for now.
- `prefix` is the bot's prefix.
- `debug` is an optional option to indicate whether the bot is in debug mode or not.
- `secret` contains the file name that contains your bot's secret like token.

1. Run the bot.

```sh
python3 -O main.py BotIndex [OPTIONS]
```

These options include:

- `--debug`: Force switch the bot into debug mode.

## What's next?

For personal convenience, I also have a template script to run the bot in different modes. You can check it out at `run.sh`. It'll *only* run the bot and not Lavalink. You'll need to run that thing separately.
