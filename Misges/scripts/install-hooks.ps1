# scripts\install-hooks.ps1
# Copie les hooks git dans .git/hooks/

$repoRoot = Split-Path -Parent $PSScriptRoot
$hooksSource = Join-Path $PSScriptRoot "hooks"
$hooksDest = Join-Path $repoRoot ".git" "hooks"

if (-not (Test-Path $hooksDest)) {
    Write-Host "Erreur : .git/hooks/ introuvable. Es-tu dans le bon dossier ?" -ForegroundColor Red
    exit 1
}

Get-ChildItem -Path $hooksSource -File | ForEach-Object {
    $dest = Join-Path $hooksDest $_.Name
    Copy-Item -Path $_.FullName -Destination $dest -Force
    Write-Host "Installe : $($_.Name)" -ForegroundColor Green
}

Write-Host ""
Write-Host "Hooks installes. Desormais, chaque 'git push' exportera" -ForegroundColor Cyan
Write-Host "automatiquement tes donnees vers fixtures/full_data.json" -ForegroundColor Cyan
Write-Host "avant d'envoyer le code vers Render." -ForegroundColor Cyan
