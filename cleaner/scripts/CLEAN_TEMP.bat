@echo off
chcp 65001 >nul
echo ========================================
echo TTFD-Cleaner - ОЧИСТКА ВРЕМЕННЫХ ФАЙЛОВ
echo ========================================
echo.

echo Удаление временных файлов сборки...
echo.

REM Удаление папок PyInstaller
if exist "build" (
    echo [OK] Удаление build\
    rmdir /S /Q "build"
)

if exist "dist" (
    echo [OK] Удаление dist\
    rmdir /S /Q "dist"
)

if exist "__pycache__" (
    echo [OK] Удаление __pycache__\
    rmdir /S /Q "__pycache__"
)

REM Удаление .spec файла
if exist "TTFD-Cleaner.spec" (
    echo [OK] Удаление TTFD-Cleaner.spec
    del /F /Q "TTFD-Cleaner.spec"
)

REM Удаление Backend временных файлов
if exist "Backend\bin" (
    echo [OK] Удаление Backend\bin\
    rmdir /S /Q "Backend\bin"
)

if exist "Backend\obj" (
    echo [OK] Удаление Backend\obj\
    rmdir /S /Q "Backend\obj"
)

echo.
echo ========================================
echo [SUCCESS] Очистка завершена!
echo ========================================
echo.
echo Оставлены только:
echo   - TTFD-Cleaner.exe
echo   - TTFD.Cleaner.Cli.exe
echo   - Исходный код
echo.
pause
