$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $Root
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Không thể tạo môi trường Python .venv.' }
}
$env:PYTHONUTF8 = '1'
& '.\.venv\Scripts\python.exe' -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'Không thể cập nhật pip.' }
& '.\.venv\Scripts\python.exe' -m pip install -r server\requirements-dev.txt -r client\requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Không thể cài đặt thư viện dự án.' }
$ServerEnvPath = Join-Path $Root 'server\.env'
if (-not (Test-Path -LiteralPath $ServerEnvPath)) {
    $Template = [IO.File]::ReadAllText((Join-Path $Root 'server\.env.example'))
    $SecretBytes = New-Object byte[] 32
    $RandomGenerator = [Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $RandomGenerator.GetBytes($SecretBytes)
    } finally {
        $RandomGenerator.Dispose()
    }
    $GeneratedSecret = ($SecretBytes | ForEach-Object { $_.ToString('x2') }) -join ''
    $ServerConfig = [Text.RegularExpressions.Regex]::Replace(
        $Template,
        '(?m)^JWT_SECRET=.*$',
        "JWT_SECRET=$GeneratedSecret"
    )
    $Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($ServerEnvPath, $ServerConfig, $Utf8NoBom)
    Write-Host 'Da tao server\.env voi JWT secret ngau nhien.'
}
& '.\.venv\Scripts\python.exe' '.\scripts\seed_sample_data.py' --if-empty --skip-backups
if ($LASTEXITCODE -ne 0) { throw 'Không thể khởi tạo dữ liệu lần đầu.' }
Write-Host 'Moi truong du an da san sang.'
