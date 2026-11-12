$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $Root
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) { python -m venv .venv }
$env:PYTHONUTF8 = '1'
& '.\.venv\Scripts\python.exe' -m pip install --upgrade pip
& '.\.venv\Scripts\python.exe' -m pip install -r server\requirements-dev.txt -r client\requirements.txt
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
Write-Host 'Moi truong du an da san sang.'
