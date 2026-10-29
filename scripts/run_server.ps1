$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) { throw 'Chưa có .venv. Hãy chạy scripts\setup.ps1 trước.' }
Set-Location -LiteralPath (Join-Path $Root 'server')
& $Python -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { throw 'Alembic migration thất bại.' }
Set-Location -LiteralPath $Root
& $Python server_launcher.py
if ($LASTEXITCODE -ne 0) { throw 'Attendance Server dừng với lỗi.' }
