@echo off
chcp 65001 >nul
REM Быстрая загрузка без вопросов

git add .
git commit -m "Quick update"
git push origin main
if errorlevel 1 git push origin master

echo ✓ Загружено на GitHub!
timeout /t 2 >nul
