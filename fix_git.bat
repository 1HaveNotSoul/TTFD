@echo off
cd /d "%~dp0"
git rebase --abort
git pull --no-rebase
git push
pause
