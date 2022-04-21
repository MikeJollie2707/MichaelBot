#!/bin/bash

MICHAEL_DIR="/absolute/path/to/directory"
BOT_INDEX="BotIndex"

run_bot()
{
    source "$MICHAEL_DIR/venv/bin/activate"
    konsole --hold --workdir "$MICHAEL_DIR" -e python3 -OO main.py $BOT_INDEX $1 &
}

case $1 in
    "")
        run_bot
        ;;
    *)
        echo "Unknown option"
        ;;
esac
