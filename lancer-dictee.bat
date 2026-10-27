@echo off
cd /d "%~dp0"
py -3.11 arreter-dictee.py
if errorlevel 1 (
    echo Impossible d'arreter une ancienne instance.
    pause
    exit /b 1
)
py -3.11 "%~dp0dictee.py"
pause
