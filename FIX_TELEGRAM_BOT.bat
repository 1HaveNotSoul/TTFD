@echo off
chcp 65001 >nul
echo Fixing Telegram bot Git issue...

cd /d "%~dp0"

echo Step 1: Remove TTFD-Telegram folder
rmdir /s /q "TTFD-Telegram" 2>nul

echo Step 2: Add telegram-bot to Git
git add telegram-bot/

echo Step 3: Commit
git commit -m "Add Telegram bot v2.1 with tickets and games"

echo Step 4: Push
git push

echo Done!
pause
