@echo off
cd /d "%~dp0"
python scripts\career_os.py daily --commit --push
pause
