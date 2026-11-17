@echo off
cd /d "%~dp0"
echo Dang khoi dong Attendance Server...
start "Attendance Server - LAN" powershell -NoExit -ExecutionPolicy Bypass -Command "& '.\.venv\Scripts\python.exe' server_launcher.py"
timeout /t 2 /nobreak >nul
echo Dang khoi dong Giao dien Nhan vien (Client)...
start "Attendance Client" .\.venv\Scripts\python.exe client_launcher.py

