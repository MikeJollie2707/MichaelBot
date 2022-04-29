$MICHAEL_DIR = $PSScriptRoot
$BOT_INDEX = $args[0]

cd $MICHAEL_DIR
if (!(Test-Path env:VIRTUAL_ENV)) {
    ./venv/Scripts/Activate.ps1
}
python -OO main.py $BOT_INDEX
