# deploy.ps1
# 1. Exporte toutes les donnees (SQLite -> fixtures/full_data.json)
# 2. Stage tout
# 3. Commit avec un message
# 4. Push vers origin

param(
    [string]$Message = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSCommandPath
Set-Location $root

Write-Host "=== Etape 1 : Export des donnees ===" -ForegroundColor Cyan
python manage.py export_full_data
if ($LASTEXITCODE -ne 0) { throw "Export echoue" }

Write-Host "`n=== Etape 2 : Git add ===" -ForegroundColor Cyan
git add -A

Write-Host "`n=== Etape 3 : Commit ===" -ForegroundColor Cyan
if ($Message -eq "") {
    $date = Get-Date -Format "yyyy-MM-dd HH:mm"
    $Message = "Deploiement du $date"
}
git commit -m "$Message"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Rien a commit ? (pas de modifications)" -ForegroundColor Yellow
}

Write-Host "`n=== Etape 4 : Push ===" -ForegroundColor Cyan
git push
if ($LASTEXITCODE -ne 0) { throw "Push echoue" }

Write-Host "`n=== Deploiement termine ! ===" -ForegroundColor Green
Write-Host "Render va automatiquement rebuild et deployer." -ForegroundColor Cyan
