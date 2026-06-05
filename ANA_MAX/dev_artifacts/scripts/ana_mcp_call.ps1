param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $ArgsForPython
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonScript = Join-Path $ScriptDir "ana_mcp_call.py"

python $PythonScript @ArgsForPython
exit $LASTEXITCODE
