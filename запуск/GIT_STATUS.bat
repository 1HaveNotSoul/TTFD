@echo off
chcp 65001 >nul
echo ========================================
echo    GIT STATUS - Проверка изменений
echo ========================================
echo.

git status

echo.
echo ========================================
echo Команды:
echo   GIT_PUSH.bat - загрузить на GitHub
echo   GIT_PULL.bat - скачать с GitHub
echo ========================================
pause
