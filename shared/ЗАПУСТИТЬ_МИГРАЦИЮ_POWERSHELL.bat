@echo off
chcp 65001 >nul
echo.
echo ═══════════════════════════════════════════════════════════════
echo 🚀 МИГРАЦИЯ ДАННЫХ В UNIFIED DATABASE
echo ═══════════════════════════════════════════════════════════════
echo.
echo 📋 Запуск через PowerShell...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "$env:DATABASE_URL='postgresql://postgres:RVLOGKNYKxNJfcoLiMNJxBgdhCCPspxf@turntable.proxy.rlwy.net:26630/railway'; python migrate_to_unified.py"

echo.
echo ═══════════════════════════════════════════════════════════════
echo.
pause
