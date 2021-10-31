#!/bin/bash

# The project path. Needs to be absolute path if you plan to run on startup.
MICHAEL_DIR="Project directory"
# Bot index in config.json
BOT_INDEX="MichaelBot"

display_help()
{
    echo "Run the Discord bot in a separate terminal."
    echo
    echo "Options:"
    echo "  --help: Display this message."
    echo "  --nomusic: Run the bot without firing up Lavalink server. Also doesn't load Music cog."
    echo "  --debug: Run the bot in debug mode."
    echo "  --fastdebug: Run the bot in debug mode without firing up Lavalink server. Also doesn't load Music cog."
}

run_lavalink()
{
    # I use konsole on KDE Plasma, so you might need to change this a bit.
    # Currently it's spawning another terminal to run the command (after -e, not include &)
    konsole --hold --workdir "$MICHAEL_DIR/lib/Lavalink3.3" -e java -jar Lavalink.jar &
}

run_bot()
{
    source "$MICHAEL_DIR/venv/bin/activate"
    # I use konsole on KDE Plasma, so you might need to change this a bit.
    # Currently it's spawning another terminal to run the command (after -e, not include &)
    konsole --hold --workdir "$MICHAEL_DIR" -e python3 bot.py MichaelBot $1 &
}

case $1 in
    -h|--help)
        display_help
        ;;
    -nm|--nomusic)
        run_bot --nomusic
        ;;
    -d|--debug)
        run_lavalink
        sleep 10
        run_bot --debug
        ;;
    -fd|--fastdebug)
        run_bot --debug
        ;;
    "")
        run_lavalink
        # This is to make sure Lavalink is setup before the bot starts running.
        sleep 10
        run_bot
        ;;
    *)
        echo "Unknown option"
        ;;
esac
