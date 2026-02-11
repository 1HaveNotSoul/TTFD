@echo off
chcp 65001 >nul
title TTFD Telegram Bot

echo ========================================
echo    TTFD Telegram Bot - Запуск
echo ========================================
echo.

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не установлен!
    echo 💡 Установи Python с https://python.org
    pause
    exit /b 1
)

echo ✅ Python установлен
echo.

REM Установка зависимостей
echo 📦 Установка зависимостей...
pip install -r requirements.txt
echo.

REM Запуск бота
echo 🚀 Запуск бота...
echo.
python main.py

pause
