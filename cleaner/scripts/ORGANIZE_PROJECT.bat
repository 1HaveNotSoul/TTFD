@echo off
chcp 65001 >nul
echo ========================================
echo TTFD-Cleaner - ОРГАНИЗАЦИЯ ПРОЕКТА
echo ========================================
echo.

echo Создание папок...
echo.

REM Создание структуры папок
if not exist "docs" mkdir docs
if not exist "scripts" mkdir scripts

echo [OK] Папки созданы
echo.

echo Перемещение файлов...
echo.

REM Перемещение .txt файлов документации в docs
move /Y "*.txt" "docs\" 2>nul

REM Перемещение .md файлов в docs
move /Y "*.md" "docs\" 2>nul

REM Перемещение .bat файлов в scripts (кроме этого)
for %%f in (*.bat) do (
    if not "%%f"=="ORGANIZE_PROJECT.bat" (
        move /Y "%%f" "scripts\" 2>nul
    )
)

REM Возврат важных файлов в корень
if exist "docs\README.md" move /Y "docs\README.md" . 2>nul
if exist "docs\CHANGELOG.txt" move /Y "docs\CHANGELOG.txt" . 2>nul

echo [OK] Файлы перемещены
echo.

echo ========================================
echo [SUCCESS] ОРГАНИЗАЦИЯ ЗАВЕРШЕНА!
echo ========================================
echo.
echo Новая структура:
echo.
echo TTFD-Cleaner\
echo   ├── Backend\           (C# код)
echo   ├── docs\              (Документация .txt/.md)
echo   ├── scripts\           (Батники .bat)
echo   ├── gui.py             (Python GUI)
echo   ├── requirements.txt   (Python зависимости)
echo   ├── README.md          (Главный README)
echo   ├── CHANGELOG.txt      (История изменений)
echo   ├── TTFD-Cleaner.exe   (GUI приложение)
echo   └── TTFD.Cleaner.Cli.exe (Backend CLI)
echo.
pause

REM Перемещение этого батника в scripts
move /Y "ORGANIZE_PROJECT.bat" "scripts\" 2>nul
