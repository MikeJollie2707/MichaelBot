#!/bin/bash

MICHAEL_DIR="/absolute/path/to/directory"
BOT_INDEX="MichaelBot"

display_help()
{
    echo "Run the Discord bot in a separate terminal."
    echo
    echo "Options:"
    echo "  --help: Display this message."
    echo "  --debug: Run the bot in debug mode."
}

# Deprecated; you can write one yourself if you're not using Docker.
run_lavalink()
{
    #konsole --hold --workdir "$MICHAEL_DIR/lib/Lavalink3.3" -e java -jar Lavalink.jar &  
}

run_bot()
{
    source "$MICHAEL_DIR/venv/bin/activate"
    konsole --hold --workdir "$MICHAEL_DIR" -e python3 -O main.py $BOT_INDEX $1 &
}

case $1 in
    -h|--help)
        display_help
        ;;
    -d|--debug)
        run_bot --debug
        ;;
    "")
        run_bot
        ;;
    *)
        echo "Unknown option"
        ;;
esac
