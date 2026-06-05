function Get-AnaRepoRoot {
    $scriptDir = Split-Path -Parent $PSCommandPath
    return (Resolve-Path (Join-Path $scriptDir "..\..\..")).Path
}

function Invoke-AnaPython {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Script,

        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]] $ScriptArgs
    )

    $repoRoot = Get-AnaRepoRoot
    $python = Join-Path $repoRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path $python)) {
        $python = "python"
    }

    & $python $Script @ScriptArgs
}

function Normalize-AnaArgs {
    param(
        [string[]] $InputArgs
    )

    $normalized = @()
    for ($i = 0; $i -lt $InputArgs.Count; $i++) {
        $current = $InputArgs[$i]
        $next = $null
        if (($i + 1) -lt $InputArgs.Count) {
            $next = $InputArgs[$i + 1]
        }

        if ($current -match '^(target|region)=\d+$' -and $next -match '^\d+(,\d+)?$') {
            $normalized += "$current,$next"
            $i++
            continue
        }

        $normalized += $current
    }
    return $normalized
}

function ana-health {
    $repoRoot = Get-AnaRepoRoot
    $script = Join-Path $repoRoot "ANA_MAX\dev_artifacts\scripts\ana_mcp_call.py"
    Invoke-AnaPython -Script $script --health
}

function ana-list {
    $repoRoot = Get-AnaRepoRoot
    $script = Join-Path $repoRoot "ANA_MAX\dev_artifacts\scripts\ana_mcp_call.py"
    Invoke-AnaPython -Script $script --list
}

function ana-schema {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Tool
    )
    $repoRoot = Get-AnaRepoRoot
    $script = Join-Path $repoRoot "ANA_MAX\dev_artifacts\scripts\ana_mcp_call.py"
    Invoke-AnaPython -Script $script --schema $Tool
}

function ana-tool {
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string] $Tool,

        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]] $ToolArgs
    )
    $repoRoot = Get-AnaRepoRoot
    $script = Join-Path $repoRoot "ANA_MAX\dev_artifacts\scripts\ana_mcp_call.py"
    $normalized = Normalize-AnaArgs -InputArgs $ToolArgs
    Invoke-AnaPython -Script $script $Tool @normalized
}

function ana-view {
    $repoRoot = Get-AnaRepoRoot
    $script = Join-Path $repoRoot "ANA_MAX\dev_artifacts\scripts\ana_mcp_call.py"
    Invoke-AnaPython -Script $script desktop_control operation=view confirm=true
}

function ana-move {
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [int] $X,

        [Parameter(Mandatory = $true, Position = 1)]
        [int] $Y
    )
    $repoRoot = Get-AnaRepoRoot
    $script = Join-Path $repoRoot "ANA_MAX\dev_artifacts\scripts\ana_mcp_call.py"
    Invoke-AnaPython -Script $script desktop_control operation=move_mouse "x=$X" "y=$Y" confirm=true
}

function ana-windows {
    $repoRoot = Get-AnaRepoRoot
    $script = Join-Path $repoRoot "ANA_MAX\dev_artifacts\scripts\ana_mcp_call.py"
    Invoke-AnaPython -Script $script desktop_capture operation=get_windows
}

function ana-under-hood {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]] $Args
    )
    $repoRoot = Get-AnaRepoRoot
    $script = Join-Path $repoRoot "ANA_MAX\dev_artifacts\scripts\ana_under_hood.py"
    Invoke-AnaPython -Script $script @Args
}

function ana-frida {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]] $Args
    )
    $repoRoot = Get-AnaRepoRoot
    $script = Join-Path $repoRoot "ANA_MAX\dev_artifacts\scripts\ana_frida.py"
    Invoke-AnaPython -Script $script @Args
}

function ana-step {
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string] $Tool,

        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]] $ToolArgs
    )
    $repoRoot = Get-AnaRepoRoot
    $script = Join-Path $repoRoot "ANA_MAX\dev_artifacts\scripts\ana_agent_step.py"
    $normalized = Normalize-AnaArgs -InputArgs $ToolArgs
    Invoke-AnaPython -Script $script $Tool @normalized
}

function ana-smoke {
    param(
        [string] $Text = "ANA MAX PowerShell MCP smoke",

        [switch] $NoLaunch,

        [switch] $CloseAtEnd
    )

    $repoRoot = Get-AnaRepoRoot
    $script = Join-Path $repoRoot "ANA_MAX\dev_artifacts\scripts\ana_desktop_smoke.py"
    $args = @("--text", $Text)
    if ($NoLaunch) {
        $args += "--no-launch"
    }
    if ($CloseAtEnd) {
        $args += "--close-at-end"
    }
    Invoke-AnaPython -Script $script @args
}

function ana-mirror {
    param(
        [switch] $Once,

        [switch] $NoScreenshots,

        [double] $Interval = 2.0,

        [double] $ScreenshotEvery = 10.0
    )

    $repoRoot = Get-AnaRepoRoot
    $script = Join-Path $repoRoot "ANA_MAX\dev_artifacts\scripts\ana_mirror_watch.py"
    $args = @("--interval", "$Interval", "--screenshot-every", "$ScreenshotEvery")
    if ($Once) {
        $args += "--once"
    }
    if ($NoScreenshots) {
        $args += "--no-screenshots"
    }
    Invoke-AnaPython -Script $script @args
}

function ana-lab {
    param(
        [ValidateSet("dev", "lab", "god")]
        [string] $Mode = "lab",

        [double] $Duration = 0,

        [switch] $NoWatchdog,

        [switch] $NoMirror,

        [switch] $NoScreenshots,

        [switch] $Verbose
    )

    $repoRoot = Get-AnaRepoRoot
    $script = Join-Path $repoRoot "ANA_MAX\dev_artifacts\scripts\ana_lab_hub.py"
    $args = @("--mode", $Mode)
    if ($Duration -gt 0) {
        $args += @("--duration", "$Duration")
    }
    if ($NoWatchdog) {
        $args += "--no-watchdog"
    }
    if ($NoMirror) {
        $args += "--no-mirror"
    }
    if ($NoScreenshots) {
        $args += "--no-screenshots"
    }
    if ($Verbose) {
        $args += "--verbose"
    }
    Invoke-AnaPython -Script $script @args
}

function ana-code-map {
    param(
        [ValidateSet("refresh", "query", "stats")]
        [string] $Action = "stats",

        [string] $Query = "",

        [switch] $Force,

        [int] $Limit = 8
    )

    $repoRoot = Get-AnaRepoRoot
    $script = Join-Path $repoRoot "ANA_MAX\dev_artifacts\scripts\ana_code_map.py"
    $args = @($Action)
    if ($Action -eq "query") {
        $args += @("--query", $Query, "--limit", "$Limit")
    }
    if ($Force) {
        $args += "--force"
    }
    Invoke-AnaPython -Script $script @args
}

function ana-binary-map {
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string] $Path,

        [int] $StringsLimit = 20,

        [int] $MaxBytes = 26214400
    )

    $repoRoot = Get-AnaRepoRoot
    $script = Join-Path $repoRoot "ANA_MAX\dev_artifacts\scripts\ana_mcp_call.py"
    Invoke-AnaPython -Script $script binary_map "path=$Path" "strings_limit=$StringsLimit" "max_bytes=$MaxBytes"
}

function ana-trust {
    param(
        [int] $Hours = 1,

        [int] $Limit = 80
    )

    $repoRoot = Get-AnaRepoRoot
    $script = Join-Path $repoRoot "ANA_MAX\dev_artifacts\scripts\ana_mcp_call.py"
    Invoke-AnaPython -Script $script session_audit action=trust "hours=$Hours" "limit=$Limit"
}

function ana-audit {
    param(
        [string] $RunId = "",

        [int] $Hours = 1,

        [int] $Limit = 100
    )

    $repoRoot = Get-AnaRepoRoot
    $script = Join-Path $repoRoot "ANA_MAX\dev_artifacts\scripts\ana_mcp_call.py"
    $args = @("session_audit", "action=generate", "hours=$Hours", "limit=$Limit")
    if ($RunId) {
        $args += "run_id=$RunId"
    }
    Invoke-AnaPython -Script $script @args
}

function ana-input-probe {
    param(
        [ValidateSet("list_authorized", "spec", "execute")]
        [string] $Operation = "list_authorized",

        [string] $TargetProcess = "",

        [ValidateSet("RegisterRawInputDevices", "GetAsyncKeyState", "GetKeyboardState")]
        [string] $ApiName = "RegisterRawInputDevices",

        [int] $Duration = 5,

        [int] $SampleLimit = 100,

        [switch] $Confirm
    )

    $repoRoot = Get-AnaRepoRoot
    $script = Join-Path $repoRoot "ANA_MAX\dev_artifacts\scripts\ana_mcp_call.py"
    $args = @("input_api_probe", "operation=$Operation")
    if ($TargetProcess) {
        $args += "target_process=$TargetProcess"
    }
    $args += @("api_name=$ApiName", "duration=$Duration", "sample_limit=$SampleLimit")
    if ($Confirm) {
        $args += "confirm=true"
    }
    Invoke-AnaPython -Script $script @args
}

Write-Host "ANA MCP PowerShell helpers loaded: ana-health, ana-list, ana-schema, ana-tool, ana-step, ana-view, ana-move, ana-windows, ana-under-hood, ana-frida, ana-smoke, ana-mirror, ana-lab, ana-code-map, ana-binary-map, ana-trust, ana-audit, ana-input-probe"
