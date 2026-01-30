@echo off
chcp 65001 >nul
echo ========================================
echo 🤖 ЗАПУСК DISCORD БОТА ЛОКАЛЬНО
echo ========================================
echo.

REM Проверка .env файла
if not exist .env (
    echo ❌ Файл .env не найден!
    echo 💡 Скопируй .env.example в .env и заполни данными
    pause
    exit /b 1
)

echo ✅ Файл .env найден
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
echo 📦 Проверка зависимостей...
pip show discord.py >nul 2>&1
if errorlevel 1 (
    echo ⚠️ discord.py не установлен
    echo 📥 Установка зависимостей...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Ошибка установки зависимостей!
        pause
        exit /b 1
    )
) else (
    echo ✅ Зависимости установлены
)

echo.
echo ========================================
echo 🚀 ЗАПУСК БОТА
echo ========================================
echo.
echo Выбери режим запуска:
echo.
echo 1. Только бот (без веб-сервера)
echo 2. Бот + Веб-сервер (полный режим)
echo 3. Отмена
echo.
set /p choice="Введи номер (1-3): "

if "%choice%"=="1" (
    echo.
    echo 🤖 Запуск только бота...
    python bot.py
) else if "%choice%"=="2" (
    echo.
    echo ⚠️ ВНИМАНИЕ: В main.py должно быть BOT_ENABLED = True
    echo.
    pause
    echo.
    echo 🚀 Запуск бота + веб-сервера...
    python main.py
) else if "%choice%"=="3" (
    echo.
    echo ❌ Отменено
    pause
    exit /b 0
) else (
    echo.
    echo ❌ Неверный выбор!
    pause
    exit /b 1
)

pause
