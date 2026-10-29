$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) { throw 'Chưa có .venv.' }
Set-Location -LiteralPath $Root
& $Python -m PyInstaller --noconfirm --clean --name AttendanceServer --onefile --paths server --collect-all reportlab --collect-submodules app --add-data 'server\alembic.ini;server' --add-data 'server\alembic;server\alembic' server_launcher.py
& $Python -m PyInstaller --noconfirm --clean --name AttendanceClient --windowed --onefile --paths client client_launcher.py
& $Python -m PyInstaller --noconfirm --clean --name AttendanceAdmin --windowed --onefile --paths client admin_launcher.py
Copy-Item -LiteralPath 'server\.env.example' -Destination 'dist\server.env.example' -Force
Copy-Item -LiteralPath 'client\config.example.json' -Destination 'dist\config.example.json' -Force
Write-Host 'Đã tạo dist\AttendanceServer.exe, AttendanceClient.exe, AttendanceAdmin.exe'
