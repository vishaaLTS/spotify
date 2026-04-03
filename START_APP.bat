@echo off
title Spotify Recommendation Engine Launcher
color 0A

echo.
echo  ============================================
echo   Spotify Recommendation Engine
echo  ============================================
echo.
echo  [1/2] Starting Flask server on port 5000...
echo.

:: Start Flask server in a new window that stays open
start "Flask Server" cmd /k "cd /d "%~dp0" && python run_server.py"

:: Wait for Flask to start (12 seconds for model loading)
echo  [*] Waiting for server to load ML models (12 sec)...
timeout /t 12 /nobreak >nul

:: Start the tunnel in a second window
echo  [2/2] Starting public tunnel...
echo.
start "Public Tunnel" cmd /k "echo Connecting to localhost.run... && ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -o ServerAliveCountMax=99999 -R 80:localhost:5000 nokey@localhost.run && pause"

echo.
echo  ============================================
echo.
echo  Your PUBLIC URL will appear in the
echo  "Public Tunnel" window (look for lhr.life).
echo.
echo  Example:  https://xxxxxxxxxxxxxxx.lhr.life
echo.
echo  Local URL: http://localhost:5000
echo.
echo  To STOP: close both windows ^(Flask Server
echo           and Public Tunnel^)
echo.
echo  ============================================
echo.
pause
