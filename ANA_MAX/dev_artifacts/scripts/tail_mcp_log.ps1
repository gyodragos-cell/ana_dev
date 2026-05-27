param(
    [int]$Tail = 40
)

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
$logPath = Join-Path $repoRoot "ANA_MAX\logs\ana_max.log"

if (-not (Test-Path $logPath)) {
    Write-Host "ANA MAX log not found yet: $logPath"
    Write-Host "Start the runtime first, then run this script again."
    exit 1
}

Write-Host "Watching ANA MAX MCP/runtime log:"
Write-Host $logPath
Write-Host ""
Get-Content $logPath -Wait -Tail $Tail

