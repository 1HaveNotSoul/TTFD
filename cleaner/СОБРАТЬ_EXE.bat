@echo off
chcp 65001 >nul
echo ═══════════════════════════════════════════════════════════════
echo    СБОРКА TTFD-CLEANER MENU В EXE
echo ═══════════════════════════════════════════════════════════════
echo.

echo [1/3] Проверка PyInstaller...
python -c "import PyInstaller" 2>nul
if %errorlevel% neq 0 (
    echo [INFO] PyInstaller не установлен. Устанавливаю...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo [ERROR] Не удалось установить PyInstaller!
        pause
        exit /b 1
    )
)
echo [OK] PyInstaller установлен

echo.
echo [2/3] Сборка EXE файла...
echo [INFO] Это может занять несколько минут...
pyinstaller --clean TTFD-Cleaner-Menu.spec

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Ошибка сборки!
    pause
    exit /b 1
)

echo.
echo [3/3] Проверка результата...
if exist "dist\TTFD-Cleaner-Menu.exe" (
    echo.
    echo ═══════════════════════════════════════════════════════════════
    echo    ✅ СБОРКА ЗАВЕРШЕНА!
    echo ═══════════════════════════════════════════════════════════════
    echo.
    echo Файл создан: dist\TTFD-Cleaner-Menu.exe
    echo.
    echo Для распространения скопируйте:
    echo   - dist\TTFD-Cleaner-Menu.exe
    echo   - TTFD.Cleaner.Cli.exe (если ещё не включён)
    echo   - Config\ (опционально, для сохранения настроек)
    echo.
) else (
    echo [ERROR] EXE файл не найден!
)

pause
