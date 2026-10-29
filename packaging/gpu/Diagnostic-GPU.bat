@echo off
cd /d "%~dp0"
start "" /wait "%~dp0Dictee-GPU.exe" --diagnostic %*
if errorlevel 1 (
    echo Diagnostic en echec. Consultez donnees\diagnostic.json et donnees\dictee-console.log.
) else (
    echo Diagnostic termine. Consultez donnees\diagnostic.json.
)
pause
