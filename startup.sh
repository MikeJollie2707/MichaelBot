#!/bin/bash

MICHAEL_DIR="absolute/path/to/MichaelBot"
BOT_INDEX="Bot index in config.json"

source "$MICHAEL_DIR/venv/bin/activate"
x-terminal-emulator --hold -e python3 bot.py $BOT_INDEX &