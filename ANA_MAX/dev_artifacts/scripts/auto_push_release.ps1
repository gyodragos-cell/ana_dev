# ANA_MAX GitHub Release - Auto Push Script
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  ANA MAX - GIT PUSH SCRIPT" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Set-Location "C:\Users\billy\Desktop\ANA_MAX_GitHub_Release"

Write-Host "[1/4] Git status..." -ForegroundColor Yellow
$status = git status --short
if ($status) {
    Write-Host "Changed files:" -ForegroundColor Yellow
    $status | ForEach-Object { Write-Host "  $_" }
} else {
    Write-Host "  No changes detected" -ForegroundColor Green
}

Write-Host "`n[2/4] Adding files..." -ForegroundColor Yellow
git add -A
Write-Host "  âœ… All files added" -ForegroundColor Green

Write-Host "`n[3/4] Committing..." -ForegroundColor Yellow
git commit -m "fix: Smoke test fixes and Vector Memory improvements

- Fix Vector Memory vocabulary update order
- Fix Unicode encoding for Windows console
- Add comprehensive smoke test (9 checks)
- Add quick smoke test for rapid verification
- Update documentation and requirements
- Fix logging file handle cleanup"

Write-Host "  âœ… Committed" -ForegroundColor Green

Write-Host "`n[4/4] Pushing to GitHub..." -ForegroundColor Yellow
git push origin main

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  PUSH COMPLETE!" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Summary:" -ForegroundColor Yellow
Write-Host "  Repository: ANA_MAX_GitHub_Release" -ForegroundColor White
Write-Host "  Branch: main" -ForegroundColor White
Write-Host "  Version: v0.4.0-beta" -ForegroundColor White
Write-Host "  Tools: 61 (with Ruflo integration)" -ForegroundColor White
Write-Host "`nCheck GitHub: https://github.com/gyodragos-cell/ANA-MAX`n" -ForegroundColor White
