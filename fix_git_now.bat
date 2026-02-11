@echo off
echo Fixing git...
taskkill /F /IM vim.exe 2>nul
taskkill /F /IM nvim.exe 2>nul
del /F /Q .git\.COMMIT_EDITMSG.swp 2>nul
git rebase --abort 2>nul
git reset --hard origin/main
git pull
echo Done!
pause
