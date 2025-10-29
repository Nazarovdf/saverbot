@echo off
echo v2.5: Fix carousel (all photos), Fix MP3 (videodownloader.py algorithm)
git add .
git commit -m "v2.5: Fix carousel to send all photos, Fix MP3 extraction with videodownloader.py algorithm, Add debug logs"
git push origin main
del push_final.bat
