$VenvPythonPath = ".\venv\Scripts\python.exe"
$BotIndex = "MichaelBot" # Edit this
$command = "$VenvPythonPath bot.py $BotIndex"
Invoke-Expression $command