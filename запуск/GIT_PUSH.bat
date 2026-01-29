@echo off
chcp 65001 >nul
echo ========================================
echo    GIT PUSH - Загрузка на GitHub
echo ========================================
echo.

REM Проверка статуса
echo [1/4] Проверка изменений...
git status
echo.

REM Добавление всех файлов
echo [2/4] Добавление файлов...
git add .
echo ✓ Файлы добавлены
echo.

REM Запрос комментария
set /p commit_msg="[3/4] Введи описание изменений: "
if "%commit_msg%"=="" set commit_msg=Update files

REM Коммит
echo.
echo Создание коммита...
git commit -m "%commit_msg%"
echo ✓ Коммит создан
echo.

REM Пуш на GitHub
echo [4/4] Загрузка на GitHub...
git push origin main
if errorlevel 1 (
    echo.
    echo ❌ Ошибка! Попробуй: git push origin master
    git push origin master
)
echo.

echo ========================================
echo ✓ Готово! Изменения загружены на GitHub
echo ========================================
echo.
pause
