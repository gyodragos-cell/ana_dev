Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  ANA MAX + Jules MCP Server - Full System Startup" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/3] Checking Jules MCP Server..." -ForegroundColor Yellow
$julesPath = "C:\Users\billy\Desktop\jules\jules-mcp-server-main"
$julesEnv = Join-Path $julesPath ".env"

if (-not (Test-Path $julesEnv)) {
    Write-Host "[ERROR] .env file not found in Jules MCP Server!" -ForegroundColor Red
    Write-Host "Please edit $julesEnv and add your JULES_API_KEY" -ForegroundColor Yellow
    Write-Host "Get your key from: https://jules.google/settings/api" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if API key is set
$envContent = Get-Content $julesEnv -Raw
if ($envContent -match "JULES_API_KEY=your_jules_api_key_here") {
    Write-Host "[WARNING] JULES_API_KEY is not configured!" -ForegroundColor Red
    Write-Host "Please edit $julesEnv and set your API key" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        exit 1
    }
}

if (-not (Test-Path (Join-Path $julesPath "dist"))) {
    Write-Host "[INFO] Building Jules MCP Server..." -ForegroundColor Yellow
    Set-Location $julesPath
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Build failed!" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host "[OK] Jules MCP Server ready" -ForegroundColor Green
Write-Host ""

Write-Host "[2/3] Starting Jules MCP Server..." -ForegroundColor Yellow
Start-Process cmd -ArgumentList "/k", "cd /d $julesPath && echo Jules MCP Server Running... && node dist\index.js" -WindowStyle Minimized
Start-Sleep -Seconds 3

Write-Host "[OK] Jules MCP Server started" -ForegroundColor Green
Write-Host ""

Write-Host "[3/3] Starting ANA MAX MCP Server..." -ForegroundColor Yellow
$anaPath = "C:\Users\billy\Desktop\ana_dev\ANA_MAX"
Start-Process cmd -ArgumentList "/k", "cd /d $anaPath && echo ANA MAX MCP Server Running... && venv\Scripts\python.exe main.py --port 8765" -WindowStyle Minimized
Start-Sleep -Seconds 3

Write-Host "[OK] ANA MAX MCP Server started" -ForegroundColor Green
Write-Host ""

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  System Ready!" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Services Running:" -ForegroundColor Yellow
Write-Host "    [1] Jules MCP Server (minimized window)" -ForegroundColor White
Write-Host "    [2] ANA MAX MCP Server (port 8765)" -ForegroundColor White
Write-Host ""
Write-Host "  How it works:" -ForegroundColor Yellow
Write-Host "    - ANA can now use Jules tools automatically" -ForegroundColor White
Write-Host "    - When you ask ANA to code, she can delegate to Jules" -ForegroundColor White
Write-Host "    - Jules will create PRs, fix bugs, write tests" -ForegroundColor White
Write-Host ""
Write-Host "  To stop:" -ForegroundColor Yellow
Write-Host "    Close both minimized windows" -ForegroundColor White
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to exit this window (servers keep running)..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
