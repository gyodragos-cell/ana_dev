Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  GIT STATUS CHECK" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Set-Location "C:\Users\billy\Desktop\ANA_MAX_GitHub_Release"

Write-Host "Git log (last 3 commits):" -ForegroundColor Yellow
git log --oneline -3

Write-Host "`nFiles changed:" -ForegroundColor Yellow
git show --stat HEAD

Write-Host "`nCurrent branch:" -ForegroundColor Yellow
git branch -v

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Next step: git push origin main" -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Cyan
