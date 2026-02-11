@echo off
chcp 65001 >nul
echo ========================================
echo TTFD-Cleaner v1.2 - Обновление .exe
echo ========================================
echo.

echo [1/2] Проверка файлов...
if not exist "dist\TTFD-Cleaner.exe" (
    echo [ERROR] Файл dist\TTFD-Cleaner.exe не найден!
    echo Сначала соберите проект: BUILD_GUI.bat
    pause
    exit /b 1
)

echo [OK] Новый .exe найден
echo.

echo [2/2] Копирование файла...
echo ВАЖНО: Закройте TTFD-Cleaner.exe перед продолжением!
echo.
pause

copy /Y "dist\TTFD-Cleaner.exe" "TTFD-Cleaner.exe"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Не удалось скопировать файл!
    echo Возможно, TTFD-Cleaner.exe ещё открыт.
    echo Закройте программу и попробуйте снова.
    pause
    exit /b 1
)

echo.
echo [OK] Файл успешно обновлён!
echo.
echo Теперь можно запустить TTFD-Cleaner.exe
echo.
pause
