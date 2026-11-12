$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) { throw 'Chưa có .venv.' }
$ServerRuntimePath = Join-Path $Root 'dist\server.env'
$ServerRuntimeConfig = if (Test-Path -LiteralPath $ServerRuntimePath) {
    [IO.File]::ReadAllText($ServerRuntimePath)
} else {
    $Template = [IO.File]::ReadAllText((Join-Path $Root 'server\.env.example'))
    $SecretBytes = New-Object byte[] 32
    $RandomGenerator = [Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $RandomGenerator.GetBytes($SecretBytes)
    } finally {
        $RandomGenerator.Dispose()
    }
    $GeneratedSecret = ($SecretBytes | ForEach-Object { $_.ToString('x2') }) -join ''
    [Text.RegularExpressions.Regex]::Replace(
        $Template,
        '(?m)^JWT_SECRET=.*$',
        "JWT_SECRET=$GeneratedSecret"
    )
}
Set-Location -LiteralPath $Root
& $Python -m PyInstaller --noconfirm --clean --name AttendanceServer --onefile --paths server --collect-all reportlab --collect-submodules app --add-data 'server\alembic.ini;server' --add-data 'server\alembic;server\alembic' server_launcher.py
& $Python -m PyInstaller --noconfirm --clean --name AttendanceClient --windowed --onefile --paths client client_launcher.py
& $Python -m PyInstaller --noconfirm --clean --name AttendanceAdmin --windowed --onefile --paths client admin_launcher.py
Copy-Item -LiteralPath 'server\.env.example' -Destination 'dist\server.env.example' -Force
Copy-Item -LiteralPath 'client\config.example.json' -Destination 'dist\config.example.json' -Force
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText($ServerRuntimePath, $ServerRuntimeConfig, $Utf8NoBom)
Write-Host 'Đã tạo dist\AttendanceServer.exe, AttendanceClient.exe, AttendanceAdmin.exe'
