@echo off
chcp 65001 >nul
echo ========================================
echo ПРИМЕНЕНИЕ МИГРАЦИИ: link_codes таблица
echo ========================================
echo.

REM Проверка DATABASE_URL
if "%DATABASE_URL%"=="" (
    echo ❌ DATABASE_URL не установлен!
    echo.
    echo 💡 Установи переменную окружения:
    echo    set DATABASE_URL=postgresql://postgres:password@host:port/database
    echo.
    echo Или используй PowerShell:
    echo    $env:DATABASE_URL='postgresql://postgres:password@host:port/database'
    echo.
    pause
    exit /b 1
)

echo ✅ DATABASE_URL найден
echo.

REM Запуск миграции
echo 🔄 Запуск миграции...
echo.
python apply_link_codes_migration.py

echo.
echo ========================================
pause
