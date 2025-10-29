@echo off
del cleanup_all.py
git add .
git commit -m "Final cleanup complete"
git push origin main
del final.bat
