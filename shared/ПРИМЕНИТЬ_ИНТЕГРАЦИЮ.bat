@echo off
chcp 65001 >nul
echo ═══════════════════════════════════════════════════════════════
echo 🚀 ИНТЕГРАЦИЯ ПЛАТФОРМ TTFD
echo ═══════════════════════════════════════════════════════════════
echo.

REM Проверка что мы в правильной папке
if not exist "migration_unified.sql" (
    echo ❌ Ошибка: Запусти этот файл из папки TTFD\shared
    pause
    exit /b 1
)

echo 📋 ШАГ 1: Получение DATABASE_URL из Railway
echo.
echo Открой Railway в браузере:
echo 1. Перейди на https://railway.app
echo 2. Открой проект "Postgres" (с иконкой слона)
echo 3. Вкладка "Variables"
echo 4. Найди переменную DATABASE_URL
echo 5. Скопируй её значение
echo.
echo Вставь DATABASE_URL сюда и нажми Enter:
set /p DATABASE_URL=

if "%DATABASE_URL%"=="" (
    echo ❌ DATABASE_URL не может быть пустым
    pause
    exit /b 1
)

echo.
echo ✅ DATABASE_URL получен
echo.

echo ═══════════════════════════════════════════════════════════════
echo 📝 ШАГ 2: Создание таблиц в Railway PostgreSQL
echo ═══════════════════════════════════════════════════════════════
echo.

echo Выполняю: psql "%DATABASE_URL%" -f migration_unified.sql
echo.

REM Ищем psql в стандартных местах
set PSQL_PATH=
if exist "C:\Program Files\PostgreSQL\18\bin\psql.exe" set PSQL_PATH=C:\Program Files\PostgreSQL\18\bin\psql.exe
if exist "C:\Program Files\PostgreSQL\17\bin\psql.exe" set PSQL_PATH=C:\Program Files\PostgreSQL\17\bin\psql.exe
if exist "C:\Program Files\PostgreSQL\16\bin\psql.exe" set PSQL_PATH=C:\Program Files\PostgreSQL\16\bin\psql.exe
if exist "C:\Program Files\PostgreSQL\15\bin\psql.exe" set PSQL_PATH=C:\Program Files\PostgreSQL\15\bin\psql.exe

if "%PSQL_PATH%"=="" (
    echo ❌ psql не найден
    echo 💡 Добавь PostgreSQL в PATH или укажи путь вручную
    pause
    exit /b 1
)

echo Найден psql: %PSQL_PATH%
echo.

"%PSQL_PATH%" "%DATABASE_URL%" -f migration_unified.sql

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Ошибка создания таблиц
    echo.
    echo 💡 Возможные причины:
    echo    - psql не найден (добавь PostgreSQL в PATH)
    echo    - Неправильный DATABASE_URL
    echo    - Нет доступа к Railway
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ Таблицы созданы успешно!
echo.

echo ═══════════════════════════════════════════════════════════════
echo 📦 ШАГ 3: Миграция данных
echo ═══════════════════════════════════════════════════════════════
echo.

echo Выполняю: python migrate_to_unified.py
echo.

python migrate_to_unified.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Ошибка миграции данных
    echo.
    echo 💡 Проверь что:
    echo    - Python установлен
    echo    - Все зависимости установлены (pip install -r requirements.txt)
    echo    - DATABASE_URL правильный
    echo.
    pause
    exit /b 1
)

echo.
echo ═══════════════════════════════════════════════════════════════
echo ✅ ИНТЕГРАЦИЯ ЗАВЕРШЕНА!
echo ═══════════════════════════════════════════════════════════════
echo.
echo 🎉 Все данные перенесены в unified_users
echo.
echo 📊 Что дальше:
echo    1. Проверь данные в Railway (вкладка Data)
echo    2. Открой TTFD\СЛЕДУЮЩИЕ_ШАГИ_ИНТЕГРАЦИЯ.md
echo    3. Интегрируй код ботов (если нужно)
echo.
echo ═══════════════════════════════════════════════════════════════
pause
