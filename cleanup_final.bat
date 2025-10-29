@echo off
del push_fixes.bat
del ENV_FIX_INSTRUCTIONS.txt
del youtube_5463769569.mp4
del yt_audio_5463769569
git add .
git commit -m "Remove temporary files"
git push origin main
del cleanup_final.bat
