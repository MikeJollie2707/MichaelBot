#!/bin/bash

MICHAEL_DIR="absolute/path/to/MichaelBot"

source "$MICHAEL_DIR/venv/bin/activate"
x-terminal-emulator --hold -e python3 bot.py MichaelBot &