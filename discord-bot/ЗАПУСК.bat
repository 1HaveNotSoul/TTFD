@echo off
chcp 65001 >nul
title TTFD Discord Bot
color 0A

echo ╔════════════════════════════════════════╗
echo ║   TTFD Discord Bot                    ║
echo ║   Запуск бота                         ║
echo ╚════════════════════════════════════════╝
echo.

python py/bot.py

pause
