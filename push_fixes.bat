@echo off
echo Pushing fixes to GitHub...
git add .
git commit -m "Fix: Instagram description button, MP3 extraction, YouTube large files, Admin ID parsing"
git push origin main
pause
