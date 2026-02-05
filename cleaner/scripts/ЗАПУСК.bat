@echo off
chcp 65001 >nul
echo ========================================
echo    TTFD-CLEANER
echo    Безопасный очиститель Windows
echo ========================================
echo.

REM Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден!
    echo.
    echo Установите Python 3.11+ с python.org
    echo.
    pause
    exit /b 1
)

REM Проверка наличия Backend
if not exist "TTFD.Cleaner.Cli.exe" (
    echo [ПРЕДУПРЕЖДЕНИЕ] Backend не найден!
    echo.
    echo Соберите Backend:
    echo   cd Backend
    echo   dotnet publish -c Release -r win-x64 --self-contained true /p:PublishSingleFile=true
    echo   copy bin\Release\net8.0\win-x64\publish\TTFD.Cleaner.Cli.exe ..
    echo.
    pause
    exit /b 1
)

REM Запуск GUI
echo Запуск TTFD-Cleaner...
echo.
python gui.py

if errorlevel 1 (
    echo.
    echo [ОШИБКА] Не удалось запустить GUI
    echo.
    pause
)
