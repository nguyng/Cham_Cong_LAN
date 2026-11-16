$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root '.venv\Scripts\python.exe'
$ServerConfig = Join-Path $Root 'server\.env'
$TaskKill = Join-Path $env:SystemRoot 'System32\taskkill.exe'

if (-not (Test-Path -LiteralPath $Python)) {
    throw 'Chưa có .venv. Hãy chạy .\scripts\setup.ps1 trước.'
}
if (-not (Test-Path -LiteralPath $ServerConfig)) {
    throw 'Chưa có server\.env. Hãy chạy .\scripts\setup.ps1 trước.'
}

function ConvertTo-EncodedCommand([string] $Command) {
    $Bytes = [Text.Encoding]::Unicode.GetBytes($Command)
    return [Convert]::ToBase64String($Bytes)
}

function Stop-ProcessTree($Process) {
    if ($null -eq $Process) { return }
    $Process.Refresh()
    if (-not $Process.HasExited) {
        & $TaskKill /PID $Process.Id /T /F 2>$null | Out-Null
    }
}

$ServerPort = 8000
$PortLine = Get-Content -LiteralPath $ServerConfig |
    Where-Object { $_ -match '^SERVER_PORT\s*=\s*\d+\s*$' } |
    Select-Object -Last 1
if ($PortLine -and $PortLine -match '^SERVER_PORT\s*=\s*(\d+)\s*$') {
    $ServerPort = [int]$Matches[1]
}

$SafeRoot = $Root.Replace("'", "''")
$SafePython = $Python.Replace("'", "''")
$ServerCommand = "Set-Location -LiteralPath '$SafeRoot'; & '$SafePython' server_launcher.py"
$ServerShell = Start-Process powershell.exe -PassThru -ArgumentList @(
    '-NoProfile',
    '-EncodedCommand',
    (ConvertTo-EncodedCommand $ServerCommand)
)

try {
    $Ready = $false
    for ($Attempt = 1; $Attempt -le 60; $Attempt++) {
        $ServerShell.Refresh()
        if ($ServerShell.HasExited) {
            throw 'Server đã dừng trước khi khởi động xong. Hãy xem lỗi trong cửa sổ Server.'
        }
        $Probe = New-Object Net.Sockets.TcpClient
        try {
            $ConnectTask = $Probe.ConnectAsync('127.0.0.1', $ServerPort)
            if ($ConnectTask.Wait(500) -and $Probe.Connected) {
                $Ready = $true
                break
            }
        } catch {
            Start-Sleep -Milliseconds 250
        } finally {
            $Probe.Dispose()
        }
    }
    if (-not $Ready) {
        throw "Server không mở cổng $ServerPort sau thời gian chờ. Hãy xem lỗi trong cửa sổ Server."
    }

    $AdminCommand = "Set-Location -LiteralPath '$SafeRoot'; & '$SafePython' admin_launcher.py"
    $UserCommand = "Set-Location -LiteralPath '$SafeRoot'; & '$SafePython' client_launcher.py"
    $AdminShell = Start-Process powershell.exe -PassThru -ArgumentList @(
        '-NoProfile',
        '-EncodedCommand',
        (ConvertTo-EncodedCommand $AdminCommand)
    )
    $UserShell = Start-Process powershell.exe -PassThru -ArgumentList @(
        '-NoProfile',
        '-EncodedCommand',
        (ConvertTo-EncodedCommand $UserCommand)
    )

    $SafeTaskKill = $TaskKill.Replace("'", "''")
    $WatchCommand = @"
Wait-Process -Id $($ServerShell.Id) -ErrorAction SilentlyContinue
& '$SafeTaskKill' /PID $($AdminShell.Id) /T /F 2>`$null | Out-Null
& '$SafeTaskKill' /PID $($UserShell.Id) /T /F 2>`$null | Out-Null
"@
    Start-Process powershell.exe -WindowStyle Hidden -ArgumentList @(
        '-NoProfile',
        '-EncodedCommand',
        (ConvertTo-EncodedCommand $WatchCommand)
    ) | Out-Null
} catch {
    Stop-ProcessTree $UserShell
    Stop-ProcessTree $AdminShell
    Stop-ProcessTree $ServerShell
    throw
}

Write-Host 'Đã mở Server, Admin và User trong ba cửa sổ riêng.'
Write-Host 'Khi cửa sổ Server đóng, watchdog sẽ dừng hẳn Admin và User.'
