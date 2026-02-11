@echo off
chcp 65001 >nul
echo ═══════════════════════════════════════════════════════════════
echo    TTFD-CLEANER v1.5 - УСТАНОВКА БИБЛИОТЕК
echo ═══════════════════════════════════════════════════════════════
echo.
echo Установка библиотек для UI эффектов и извлечения иконок...
echo.

echo [1/2] Установка pywin32 (для извлечения иконок)...
pip install pywin32
if %errorlevel% neq 0 (
    echo [ERROR] Ошибка установки pywin32
    pause
    exit /b 1
)
echo [OK] pywin32 установлен
echo.

echo [2/2] Установка Pillow (для обработки изображений)...
pip install Pillow
if %errorlevel% neq 0 (
    echo [ERROR] Ошибка установки Pillow
    pause
    exit /b 1
)
echo [OK] Pillow установлен
echo.

echo ═══════════════════════════════════════════════════════════════
echo [SUCCESS] Все библиотеки установлены!
echo ═══════════════════════════════════════════════════════════════
echo.
echo УСТАНОВЛЕНО:
echo   ✓ pywin32 - извлечение иконок из .exe файлов
echo   ✓ Pillow - обработка изображений
echo.
echo СЛЕДУЮЩИЙ ШАГ:
echo   Запустите пересборку проекта: .\ПЕРЕСОБРАТЬ.bat
echo.
pause
