$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) { throw 'Chưa có .venv.' }

$DistPath = Join-Path $Root 'dist_portable'
$WorkPath = Join-Path $Root 'build_portable'
$ServerRuntimePath = Join-Path $DistPath 'AttendanceServer\server.env'
$ClientRuntimePath = Join-Path $DistPath 'AttendanceClient\config.json'
$AdminRuntimePath = Join-Path $DistPath 'AttendanceAdmin\config.json'
$ServerDataPath = Join-Path $DistPath 'AttendanceServer\data'
$ServerBackupPath = Join-Path $DistPath 'AttendanceServer\backups'
$RuntimePreservePath = Join-Path $Root 'build_portable_runtime'
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
$ClientRuntimeConfig = if (Test-Path -LiteralPath $ClientRuntimePath) { [IO.File]::ReadAllText($ClientRuntimePath) } else { $null }
$AdminRuntimeConfig = if (Test-Path -LiteralPath $AdminRuntimePath) { [IO.File]::ReadAllText($AdminRuntimePath) } else { $null }
if (Test-Path -LiteralPath $RuntimePreservePath) {
    Remove-Item -LiteralPath $RuntimePreservePath -Recurse -Force
}
New-Item -ItemType Directory -Path $RuntimePreservePath -Force | Out-Null
if (Test-Path -LiteralPath $ServerDataPath) {
    Copy-Item -LiteralPath $ServerDataPath -Destination (Join-Path $RuntimePreservePath 'data') -Recurse -Force
}
if (Test-Path -LiteralPath $ServerBackupPath) {
    Copy-Item -LiteralPath $ServerBackupPath -Destination (Join-Path $RuntimePreservePath 'backups') -Recurse -Force
}
Set-Location -LiteralPath $Root

& $Python -m PyInstaller --noconfirm --clean `
    --distpath $DistPath --workpath $WorkPath `
    'packaging\AttendanceServerPortable.spec'
$ServerBuildExitCode = $LASTEXITCODE
$ServerPortablePath = Join-Path $DistPath 'AttendanceServer'
if (Test-Path -LiteralPath (Join-Path $RuntimePreservePath 'data')) {
    Copy-Item -LiteralPath (Join-Path $RuntimePreservePath 'data') -Destination $ServerPortablePath -Recurse -Force
}
if (Test-Path -LiteralPath (Join-Path $RuntimePreservePath 'backups')) {
    Copy-Item -LiteralPath (Join-Path $RuntimePreservePath 'backups') -Destination $ServerPortablePath -Recurse -Force
}
Remove-Item -LiteralPath $RuntimePreservePath -Recurse -Force
if ($ServerBuildExitCode -ne 0) { throw 'Build AttendanceServer portable thất bại.' }
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText($ServerRuntimePath, $ServerRuntimeConfig, $Utf8NoBom)

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

if ($null -ne $ClientRuntimeConfig) {
    [IO.File]::WriteAllText($ClientRuntimePath, $ClientRuntimeConfig, $Utf8NoBom)
} else {
    Copy-Item -LiteralPath 'client\config.example.json' -Destination $ClientRuntimePath -Force
}
if ($null -ne $AdminRuntimeConfig) {
    [IO.File]::WriteAllText($AdminRuntimePath, $AdminRuntimeConfig, $Utf8NoBom)
} else {
    Copy-Item -LiteralPath 'client\config.example.json' -Destination $AdminRuntimePath -Force
}

Write-Host 'Đã tạo ba gói portable trong dist_portable.'
