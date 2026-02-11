@echo off
echo ========================================
echo ПРОВЕРКА СТАТУСА RENDER DEPLOYMENT
echo ========================================
echo.
echo Последние коммиты:
git log --oneline -5
echo.
echo ========================================
echo ИНСТРУКЦИИ:
echo ========================================
echo.
echo 1. Открой Render Dashboard: https://dashboard.render.com
echo 2. Найди свой сервис TTFD
echo 3. Проверь что развернут коммит: 4ffd1f8
echo 4. Если нет - нажми "Manual Deploy" -^> "Deploy latest commit"
echo.
echo 5. Проверь Environment Variables:
echo    - DISCORD_TOKEN (должен быть установлен)
echo    - GUILD_ID (ID твоего Discord сервера)
echo    - SECRET_KEY (любая случайная строка)
echo    - DISCORD_CLIENT_ID (для OAuth)
echo    - DISCORD_CLIENT_SECRET (для OAuth)
echo    - DISCORD_REDIRECT_URI (https://ttfd.onrender.com/auth/discord/callback)
echo.
echo 6. После деплоя подожди 15-30 минут для снятия Discord rate limit
echo.
echo 7. Проверь логи в Render Dashboard на наличие:
echo    - "Бот успешно запущен!"
echo    - "Веб-сервер запущен"
echo.
echo ========================================
pause
