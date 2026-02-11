@echo off
chcp 65001 >nul
echo ═══════════════════════════════════════════════════════════════
echo    ОРГАНИЗАЦИЯ ПРОЕКТОВ TTFD
echo ═══════════════════════════════════════════════════════════════
echo.

set "SOURCE_DIR=C:\Users\brawl\OneDrive\Desktop\папки"
set "TARGET_DIR=C:\Users\brawl\OneDrive\Desktop\папки\TTFD"

echo [INFO] Копирование проектов в единую структуру...
echo.

REM ═══════════════════════════════════════════════════════════════
REM Website
REM ═══════════════════════════════════════════════════════════════
echo [1/3] Копирование TTFD-Website → website/
if not exist "%TARGET_DIR%\website" mkdir "%TARGET_DIR%\website"

xcopy "%SOURCE_DIR%\TTFD-Website\*" "%TARGET_DIR%\website\" /E /I /Y /EXCLUDE:exclude.txt

REM ═══════════════════════════════════════════════════════════════
REM Discord Bot
REM ═══════════════════════════════════════════════════════════════
echo [2/3] Копирование TTFD-Discord → discord-bot/
if not exist "%TARGET_DIR%\discord-bot" mkdir "%TARGET_DIR%\discord-bot"

xcopy "%SOURCE_DIR%\TTFD-Discord\*" "%TARGET_DIR%\discord-bot\" /E /I /Y /EXCLUDE:exclude.txt

REM ═══════════════════════════════════════════════════════════════
REM Cleaner
REM ═══════════════════════════════════════════════════════════════
echo [3/3] Копирование TTFD-Cleaner → cleaner/
if not exist "%TARGET_DIR%\cleaner" mkdir "%TARGET_DIR%\cleaner"

xcopy "%SOURCE_DIR%\TTFD-Cleaner\*" "%TARGET_DIR%\cleaner\" /E /I /Y /EXCLUDE:exclude.txt

echo.
echo ═══════════════════════════════════════════════════════════════
echo    ✅ ОРГАНИЗАЦИЯ ЗАВЕРШЕНА!
echo ═══════════════════════════════════════════════════════════════
echo.
echo Структура проекта:
echo   TTFD/
echo   ├── website/          (TTFD-Website)
echo   ├── discord-bot/      (TTFD-Discord)
echo   ├── cleaner/          (TTFD-Cleaner)
echo   ├── docs/
echo   ├── README.md
echo   └── .gitignore
echo.
echo Следующие шаги:
echo   1. cd TTFD
echo   2. git init
echo   3. git add .
echo   4. git commit -m "Initial commit"
echo   5. git remote add origin https://github.com/yourusername/TTFD.git
echo   6. git push -u origin main
echo.
pause
