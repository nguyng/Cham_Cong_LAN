$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) { throw 'Chưa có .venv.' }

$DistPath = Join-Path $Root 'dist_portable'
$WorkPath = Join-Path $Root 'build_portable'
$ServerRuntimePath = Join-Path $DistPath 'AttendanceServer\server.env'
$ClientRuntimePath = Join-Path $DistPath 'AttendanceClient\config.json'
$AdminRuntimePath = Join-Path $DistPath 'AttendanceAdmin\config.json'
$ServerRuntimeConfig = if (Test-Path -LiteralPath $ServerRuntimePath) { [IO.File]::ReadAllText($ServerRuntimePath) } else { $null }
$ClientRuntimeConfig = if (Test-Path -LiteralPath $ClientRuntimePath) { [IO.File]::ReadAllText($ClientRuntimePath) } else { $null }
$AdminRuntimeConfig = if (Test-Path -LiteralPath $AdminRuntimePath) { [IO.File]::ReadAllText($AdminRuntimePath) } else { $null }
Set-Location -LiteralPath $Root

& $Python -m PyInstaller --noconfirm --clean `
    --distpath $DistPath --workpath $WorkPath `
    'packaging\AttendanceServerPortable.spec'
if ($LASTEXITCODE -ne 0) { throw 'Build AttendanceServer portable thất bại.' }

& $Python -m PyInstaller --noconfirm --clean `
    --distpath $DistPath --workpath $WorkPath `
    'packaging\AttendanceClientPortable.spec'
if ($LASTEXITCODE -ne 0) { throw 'Build AttendanceClient portable thất bại.' }

& $Python -m PyInstaller --noconfirm --clean `
    --distpath $DistPath --workpath $WorkPath `
    'packaging\AttendanceAdminPortable.spec'
if ($LASTEXITCODE -ne 0) { throw 'Build AttendanceAdmin portable thất bại.' }

Copy-Item -LiteralPath 'server\.env.example' -Destination "$DistPath\AttendanceServer\server.env.example" -Force
Copy-Item -LiteralPath 'client\config.example.json' -Destination "$DistPath\AttendanceClient\config.example.json" -Force
Copy-Item -LiteralPath 'client\config.example.json' -Destination "$DistPath\AttendanceAdmin\config.example.json" -Force

$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
if ($null -ne $ServerRuntimeConfig) { [IO.File]::WriteAllText($ServerRuntimePath, $ServerRuntimeConfig, $Utf8NoBom) }
if ($null -ne $ClientRuntimeConfig) { [IO.File]::WriteAllText($ClientRuntimePath, $ClientRuntimeConfig, $Utf8NoBom) }
if ($null -ne $AdminRuntimeConfig) { [IO.File]::WriteAllText($AdminRuntimePath, $AdminRuntimeConfig, $Utf8NoBom) }

Write-Host 'Đã tạo ba gói portable trong dist_portable.'
