@echo off
setlocal
cd /d "%~dp0"
py test.py
if errorlevel 1 (
    echo.
    echo The store did not start. See README.md for setup instructions.
    pause
)
