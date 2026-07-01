@echo off
title CatchBot Launcher
cd /d "%~dp0CatchBot-v6.2-Modular"

REM --- Find a working Python command (python -> py) ---
where python >nul 2>&1
if %errorlevel%==0 (
    set "PY=python"
) else (
    where py >nul 2>&1
    if %errorlevel%==0 (
        set "PY=py"
    ) else (
        echo.
        echo [ERROR] Python was not found on this system.
        echo Install Python from https://www.python.org/downloads/
        echo and make sure "Add Python to PATH" is checked during install.
        echo.
        pause
        exit /b 1
    )
)

echo Starting CatchBot...
%PY% CatchBot.py %*

REM --- Keep window open so you can read any errors/tracebacks ---
echo.
echo Bot has stopped. Press any key to close this window...
pause >nul
