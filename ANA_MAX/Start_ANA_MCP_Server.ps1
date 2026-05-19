$anaPath = $PSScriptRoot
$pythonExe = Join-Path $anaPath "venv\Scripts\python.exe"
$mcpEntry = Join-Path $anaPath "mcp_server.py"

if (-not (Test-Path $pythonExe)) {
    Write-Host "Nu exista python in venv: $pythonExe" -ForegroundColor Red
    Read-Host "Apasa Enter pentru iesire"
    exit 1
}

if (-not (Test-Path $mcpEntry)) {
    Write-Host "Nu exista fisierul: $mcpEntry" -ForegroundColor Red
    Read-Host "Apasa Enter pentru iesire"
    exit 1
}

$cmd = "cd /d `"$anaPath`" && echo ANA MAX MCP Server Running... && `"$pythonExe`" mcp_server.py"
Start-Process -FilePath "cmd.exe" -ArgumentList "/k", $cmd -WindowStyle Minimized

Write-Host "Pornit: ANA MAX MCP Server" -ForegroundColor Green
Write-Host "Deschide clientul tau MCP si conecteaza-te la http://127.0.0.1:8765/mcp" -ForegroundColor Yellow
Write-Host ""
Read-Host "Apasa Enter pentru a inchide acest launcher (serverul ramane pornit)"
