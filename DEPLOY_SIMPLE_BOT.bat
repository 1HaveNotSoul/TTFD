@echo off
chcp 65001 >nul
echo ========================================
echo Деплой упрощённого бота
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Добавление файлов...
git add telegram-bot/main.py telegram-bot/main_simple.py telegram-bot/handlers/shop.py ГОТОВО_УПРОЩЁННЫЙ_БОТ_ПЛАТЁЖКА.md

echo [2/3] Коммит...
git commit -m "Упрощён бот - только платёжка, цены 20/20/30 Stars"

echo [3/3] Push на GitHub...
git push

echo.
echo ========================================
echo ✅ Готово! Railway автоматически задеплоит
echo ========================================
pause
