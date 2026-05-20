$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ana = Join-Path $root "ANA_MAX"
$failed = $false

function Step-Header($name) {
    Write-Host ""
    Write-Host "============================================================"
    Write-Host $name
    Write-Host "============================================================"
}

function Run-Step($name, $workdir, $command) {
    Step-Header $name
    Push-Location $workdir
    try {
        Invoke-Expression $command
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

Step-Header "1. Git Status"
Push-Location $root
$status = git status --short
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] git status failed"
    $failed = $true
} elseif ($status) {
    Write-Host $status
    Write-Host "[FAIL] workspace has uncommitted changes"
    $failed = $true
} else {
    Write-Host "[PASS] workspace clean"
}
Pop-Location

Step-Header "2. ASCII Guard"
$asciiFiles = @(
    "SAFE_AGENT_RULES.md",
    "DESKTOP_PROJECT_MAP.md",
    "RUN_ANA_QUALITY_GATE.bat",
    "RUN_ANA_QUALITY_GATE.ps1",
    "ANA_MAX\requirements.txt",
    "ANA_MAX\main.py",
    "ANA_MAX\mcp_stdio.py",
    "ANA_MAX\test_mcp_frida_call.py",
    "ANA_MAX\test_frida.py",
    "ANA_MAX\tools\base.py",
    "ANA_MAX\tools\edge_tts_voice.py",
    "ANA_MAX\tools\live_voice_bridge.py",
    "ANA_MAX\tools\voice_commentary.py",
    "ANA_MAX\tools\voice_integration.py",
    "ANA_MAX\voice_toggle.py",
    "ANA_MAX\chat_voice_bridge.py",
    "ANA_MAX\desktop_vision_diag.py",
    "RUN_CHAT_VOICE_BRIDGE.bat",
    "RUN_DESKTOP_VISION_DIAG.bat"
)

foreach ($relative in $asciiFiles) {
    $path = Join-Path $root $relative
    if (-not (Test-Path $path)) {
        Write-Host "[FAIL] missing $relative"
        $failed = $true
        continue
    }
    $bytes = [System.IO.File]::ReadAllBytes($path)
    $bad = $bytes | Where-Object { $_ -gt 127 } | Select-Object -First 1
    if ($null -ne $bad) {
        Write-Host "[FAIL] non-ASCII bytes in $relative"
        $failed = $true
    } else {
        Write-Host "[PASS] $relative"
    }
}

Run-Step "3. Compile Core Files" $ana "python -m compileall -q main.py tools test_mcp_frida_call.py test_frida.py voice_toggle.py chat_voice_bridge.py desktop_vision_diag.py"
Run-Step "4. ANA Smoke Test" $ana "python main.py --test"
Run-Step "5. MCP Tool List" $ana "python test_mcp_tools.py"
Run-Step "6. Frida Through MCP" $ana "python test_mcp_frida_call.py"

Step-Header "Result"
if ($failed) {
    Write-Host "[FAIL] ANA quality gate failed."
    exit 1
}

Write-Host "[PASS] ANA quality gate passed."
exit 0
