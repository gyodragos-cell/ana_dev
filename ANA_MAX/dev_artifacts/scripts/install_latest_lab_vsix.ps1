param(
    [switch]$Apply,
    [string]$CodeCommand = "code"
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..\..\..")
$PackageJson = Join-Path $RepoRoot "vscode_extension\package.json"

if (-not (Test-Path -LiteralPath $PackageJson)) {
    throw "package.json not found: $PackageJson"
}

$Package = Get-Content -LiteralPath $PackageJson -Raw | ConvertFrom-Json
$Version = [string]$Package.version
$Vsix = Join-Path $RepoRoot ("vscode_extension\ana-codex-cockpit-{0}.vsix" -f $Version)

if (-not (Test-Path -LiteralPath $Vsix)) {
    throw "VSIX not found for version $Version. Run package_cockpit_vsix.py first: $Vsix"
}

$InstallArgs = @("--install-extension", $Vsix, "--force")

Write-Host "ANA MAX lab VSIX: $Vsix"

if (-not $Apply) {
    Write-Host "Dry run only. To install:"
    Write-Host ("  {0} {1}" -f $CodeCommand, ($InstallArgs -join " "))
    Write-Host "After install: Developer: Reload Window, restart ANA MCP, then run Post-Reload Verify, Reload Consistency, and Autonomy Pass."
    exit 0
}

Write-Host "Installing with $CodeCommand..."
& $CodeCommand @InstallArgs
if ($LASTEXITCODE -ne 0) {
    throw "VSIX install failed with exit code $LASTEXITCODE"
}

Write-Host "Install completed."
Write-Host "Next: Developer: Reload Window, restart ANA MCP, then run ANA MAX: Post-Reload Verify, Reload Consistency, and Autonomy Pass."
