@echo off
title Kapda Care
cd /d %~dp0kapda_care_backend
call venv\Scripts\activate
start "Kapda Care Backend" cmd /k "python run.py"
timeout /t 3 /nobreak > nul
start "" "%~dp0kapda_care_frontend\index.html"
echo.
echo Kapda Care chal raha hai!
echo Backend:  http://127.0.0.1:5000
echo Frontend: Browser mein khul gaya!
pause