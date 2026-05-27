# Git push script for ANA_MAX GitHub Release
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  PREPARING GITHUB RELEASE" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Set-Location "C:\Users\billy\Desktop\ANA_MAX_GitHub_Release"

Write-Host "[1/5] Checking git status..." -ForegroundColor Yellow
git status --short | Select-Object -First 20

Write-Host "`n[2/5] Adding new files..." -ForegroundColor Yellow
git add core/vector_memory.py
git add core/advanced_swarm.py
git add tools/vector_memory_tool.py
git add tools/swarm_tool.py
git add docs/PROJECT_MAP_AI_GUIDE.md
git add main.py

Write-Host "`n[3/5] Checking what will be committed..." -ForegroundColor Yellow
git status --short

Write-Host "`n[4/5] Ready to commit with message:" -ForegroundColor Yellow
Write-Host "  'feat: Add Ruflo integration - Vector Memory + Swarm (v0.4.0)'" -ForegroundColor White

Write-Host "`n[5/5] Commands to run:" -ForegroundColor Yellow
Write-Host "  git commit -m 'feat: Add Ruflo integration - Vector Memory + Swarm (v0.4.0)'" -ForegroundColor White
Write-Host "  git push origin main" -ForegroundColor White

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  READY FOR PUSH!" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan
