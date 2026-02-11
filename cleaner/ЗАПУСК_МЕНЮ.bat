@echo off
chcp 65001 >nul
echo ═══════════════════════════════════════════════════════════════
echo    TTFD-CLEANER - ГЛАВНОЕ МЕНЮ
echo ═══════════════════════════════════════════════════════════════
echo.

echo [INFO] Запуск главного меню...
python main_menu.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Ошибка запуска!
    echo.
    echo Возможные причины:
    echo   1. Pillow не установлен - запустите: pip install Pillow
    echo   2. Python не найден в PATH
    echo.
    pause
    exit /b 1
)
