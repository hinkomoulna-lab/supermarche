$content = Get-Content -Path "C:\Users\MOULNA\Postman\files\store\views.py" -Raw
$oldPatterns = @(
    '(oui/non)',
    '1. ✅ Oui\n2. ❌ Non',
    '1. 📦 Ajouter du stock',
    '1. ➕ Ajouter ce produit',
    'Ajouter les infos du client ? (oui/non)'
)
foreach ($pat in $oldPatterns) {
    $lines = $content -split "`n"
    $found = $false
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match [regex]::Escape($pat)) {
            Write-Host "Remaining '$pat' at line $($i+1): $($lines[$i].Trim().Substring(0, [Math]::Min(100, $lines[$i].Trim().Length)))"
            $found = $true
        }
    }
    if (-not $found) {
        Write-Host "✓ No more '$pat'"
    }
}
