param(
    [Parameter(Mandatory = $true)]
    [string]$RemoteSubnet,
    [ValidateRange(1, 65535)]
    [int]$ServerPort = 8000,
    [ValidateRange(1, 65535)]
    [int]$DiscoveryPort = 37020
)

$ErrorActionPreference = 'Stop'

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Hãy chạy PowerShell bằng quyền Administrator.'
}

$parts = $RemoteSubnet.Split('/')
if ($parts.Count -ne 2) { throw 'RemoteSubnet phải ở dạng CIDR, ví dụ 192.168.1.0/24.' }
$address = [Net.IPAddress]::Parse($parts[0])
$prefix = 0
if (-not [int]::TryParse($parts[1], [ref]$prefix)) { throw 'CIDR prefix không hợp lệ.' }
$maximumPrefix = if ($address.AddressFamily -eq [Net.Sockets.AddressFamily]::InterNetwork) { 32 } else { 128 }
if ($prefix -lt 0 -or $prefix -gt $maximumPrefix) { throw 'CIDR prefix nằm ngoài phạm vi hợp lệ.' }

$rules = @(
    @{ Name = 'LAN Attendance HTTPS'; Protocol = 'TCP'; Port = $ServerPort },
    @{ Name = 'LAN Attendance Discovery'; Protocol = 'UDP'; Port = $DiscoveryPort }
)

foreach ($rule in $rules) {
    $existing = Get-NetFirewallRule -DisplayName $rule.Name -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "Đã tồn tại: $($rule.Name). Không tạo trùng."
        continue
    }
    New-NetFirewallRule `
        -DisplayName $rule.Name `
        -Direction Inbound `
        -Profile Domain,Private `
        -Protocol $rule.Protocol `
        -LocalPort $rule.Port `
        -RemoteAddress $RemoteSubnet `
        -Action Allow | Out-Null
    Write-Host "Đã tạo $($rule.Name): $($rule.Protocol)/$($rule.Port), nguồn $RemoteSubnet"
}

Write-Host 'Hoàn tất. Không có quy tắc Public profile hoặc port-forwarding nào được tạo.'
