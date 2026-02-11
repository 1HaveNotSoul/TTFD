@echo off
chcp 65001 >nul
title Тест PostgreSQL подключения

echo ═══════════════════════════════════════════════════════════════
echo 🔍 ТЕСТ ПОДКЛЮЧЕНИЯ К POSTGRESQL
echo ═══════════════════════════════════════════════════════════════
echo.

cd /d "%~dp0"

python test_postgres_connection.py

echo.
echo ═══════════════════════════════════════════════════════════════
echo.
pause
