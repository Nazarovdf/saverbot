@echo off
del final_cleanup.bat
git add .
git commit -m "Remove final_cleanup.bat"
git push origin main
pause
