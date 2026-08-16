param(
    [string]$Version = 'v6',
    [int]$Iterations = 12,
    [string]$Python = 'C:\Users\hando\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
)

$ErrorActionPreference = 'Stop'
$blend = Join-Path $PSScriptRoot "work\Aina_Venara_$Version.blend"
$references = Join-Path $PSScriptRoot '..\2. Aina Venara Model\Reff 3D HD Generated Individual'
$output = Join-Path $PSScriptRoot "output\fitting\$Version"
$script = Join-Path $PSScriptRoot 'scripts\fit_model.py'

if (-not (Test-Path -LiteralPath $blend)) {
    throw "Blend kandidat tidak ditemukan: $blend"
}
& $Python $script --blend $blend --reference-root $references --output $output --manifest (Join-Path $PSScriptRoot 'fit_manifest.json') --iterations $Iterations
if ($LASTEXITCODE -ne 0) {
    throw "Fitting pipeline gagal dengan exit code $LASTEXITCODE"
}
Write-Host "Overlay review: $(Join-Path $output 'best\overlay_contact_sheet.png')"
