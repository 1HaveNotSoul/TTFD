@echo off
chcp 65001 >nul
echo ═══════════════════════════════════════════════════════════
echo 📋 УСТАНОВКА АВТООБНОВЛЕНИЯ
echo ═══════════════════════════════════════════════════════════
echo.
echo Введите изменения через вертикальную черту ^|
echo Пример: Добавлена команда X ^| Исправлен баг Y ^| Улучшена производительность
echo.
set /p changes="Изменения: "

if "%changes%"=="" (
    echo.
    echo ❌ Изменения не указаны!
    pause
    exit /b
)

echo.
echo 🔄 Установка автообновления...
python -c "import sys; sys.path.insert(0, 'py'); from updates_system import set_auto_update; set_auto_update([c.strip() for c in '%changes%'.split('|')])"

echo.
echo ✅ Автообновление установлено!
echo.
echo 📝 При следующем запуске бота будет отправлено уведомление:
echo %changes%
echo.
echo ═══════════════════════════════════════════════════════════
pause
