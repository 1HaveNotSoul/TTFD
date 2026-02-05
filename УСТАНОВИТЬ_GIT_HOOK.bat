@echo off
chcp 65001 >nul
echo ═══════════════════════════════════════════════════════════════
echo    УСТАНОВКА GIT HOOK ДЛЯ АВТООБНОВЛЕНИЙ
echo ═══════════════════════════════════════════════════════════════
echo.
echo Этот скрипт установит Git hook который будет:
echo • Автоматически добавлять изменения из коммитов
echo • Обновлять json/auto_update.json
echo • Включать автообновление (enabled: true)
echo.
echo ═══════════════════════════════════════════════════════════════
echo.

REM Проверяем существование папки .git/hooks
if not exist ".git\hooks" (
    echo ❌ Папка .git\hooks не найдена!
    echo    Убедись что ты в корне Git репозитория
    pause
    exit /b 1
)

REM Копируем hook файл
echo 📝 Копирование post-commit hook...
copy /Y ".git\hooks\post-commit" ".git\hooks\post-commit.bak" >nul 2>&1
echo #!/bin/sh > ".git\hooks\post-commit"
echo # Git post-commit hook для автоматического добавления обновлений >> ".git\hooks\post-commit"
echo. >> ".git\hooks\post-commit"
echo # Переходим в папку discord-bot >> ".git\hooks\post-commit"
echo cd discord-bot >> ".git\hooks\post-commit"
echo. >> ".git\hooks\post-commit"
echo # Запускаем обработчик обновлений >> ".git\hooks\post-commit"
echo python git_update_handler.py >> ".git\hooks\post-commit"
echo. >> ".git\hooks\post-commit"
echo # Возвращаемся обратно >> ".git\hooks\post-commit"
echo cd .. >> ".git\hooks\post-commit"

echo ✅ Hook установлен!
echo.
echo ═══════════════════════════════════════════════════════════════
echo    ТЕСТИРОВАНИЕ
echo ═══════════════════════════════════════════════════════════════
echo.
echo Сделай тестовый коммит:
echo.
echo   git add .
echo   git commit -m "feat: тестовое изменение"
echo.
echo После коммита должно появиться:
echo   ✅ Добавлено обновление: тестовое изменение
echo.
echo ═══════════════════════════════════════════════════════════════
echo    ГОТОВО!
echo ═══════════════════════════════════════════════════════════════
echo.
pause
