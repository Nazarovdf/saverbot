@echo off
git add .
git commit -m "v2.2: Auto cleanup folders, YouTube format fix, Pinterest errors, render.yaml with FFmpeg"
git push origin main
del final_commit.bat
