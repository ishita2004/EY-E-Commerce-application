@echo off
setlocal
cd /d "%~dp0"
py web_server.py
if errorlevel 1 (
    echo.
    echo The web store did not start. See README.md for setup instructions.
    pause
)
