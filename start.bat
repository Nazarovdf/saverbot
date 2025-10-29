@echo off
echo Starting Media Downloader Bot...
echo.

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate

if not exist .env (
    echo Warning: .env file not found!
    echo Please create .env file with your BOT_TOKEN
    echo Example: BOT_TOKEN=your_token_here
    pause
    exit
)

echo Installing/Updating requirements...
pip install -r requirements.txt --quiet

echo.
echo Starting bot...
python bot.py

pause
