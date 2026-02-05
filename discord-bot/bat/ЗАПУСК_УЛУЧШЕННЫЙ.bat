@echo off
chcp 65001 >nul
title TTFD Discord Bot - Улучшенная версия
color 0A

echo ╔════════════════════════════════════════╗
echo ║   TTFD Discord Bot - Enhanced         ║
echo ║   Улучшенная версия с slash-командами ║
echo ╚════════════════════════════════════════╝
echo.

cd /d "%~dp0.."
python py/bot.py

pause
