$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ana = Join-Path $root "ANA_MAX"
$failed = $false
$started = Get-Date

function Proof-Header($name) {
    Write-Host ""
    Write-Host "============================================================"
    Write-Host $name
    Write-Host "============================================================"
}

function Run-ProofStep($name, $workdir, $command, $arguments) {
    Proof-Header $name
    Push-Location $workdir
    try {
        & $command @arguments
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[FAIL] $name exited with $LASTEXITCODE"
            $script:failed = $true
        } else {
            Write-Host "[PASS] $name"
        }
    } catch {
        Write-Host "[FAIL] $name"
        Write-Host $_
        $script:failed = $true
    } finally {
        Pop-Location
    }
}

Proof-Header "JokerForge Engineer Proof"
Write-Host "Goal: prove that the agent workflow is observable, testable, and local-first."
Write-Host "Root: $root"

Proof-Header "1. Workspace Snapshot"
Push-Location $root
try {
    git status --short --branch
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAIL] git status failed"
        $failed = $true
    } else {
        Write-Host "[PASS] git status available"
    }
} finally {
    Pop-Location
}

Run-ProofStep "2. MCP Tool Inventory" $ana "python" @("test_mcp_tools.py")
Run-ProofStep "3. Authorized Frida Through MCP" $ana "python" @("test_mcp_frida_call.py")
Run-ProofStep "4. Compile Core Surface" $ana "python" @("-m", "compileall", "-q", "main.py", "tools", "mcp_stdio.py", "chat_voice_bridge.py", "desktop_vision_diag.py")
Run-ProofStep "5. Full Quality Gate" $root "powershell" @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ".\RUN_ANA_QUALITY_GATE.ps1")

Proof-Header "Engineer Proof Result"
$elapsed = (Get-Date) - $started
if ($failed) {
    Write-Host "[FAIL] JokerForge engineer proof failed."
    Write-Host ("Elapsed: {0:n1}s" -f $elapsed.TotalSeconds)
    exit 1
}

Write-Host "[PASS] JokerForge engineer proof passed."
Write-Host "What this proved:"
Write-Host "- MCP tools are discoverable."
Write-Host "- Frida runtime diagnostics work through MCP for authorized local testing."
Write-Host "- Core files compile."
Write-Host "- The full quality gate passes."
Write-Host ("Elapsed: {0:n1}s" -f $elapsed.TotalSeconds)
exit 0
