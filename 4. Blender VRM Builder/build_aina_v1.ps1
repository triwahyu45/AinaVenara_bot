param(
    [string]$InputVrm = (Join-Path $PSScriptRoot '..\2. Aina Venara Model\VRM Draft\Aina_Venara_Base.vrm'),
    [string]$Version = 'v6',
    [string]$Blender = 'C:\Program Files\Blender Foundation\Blender 4.5\blender.exe'
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $Blender)) {
    throw "Blender tidak ditemukan: $Blender"
}
if (-not (Test-Path -LiteralPath $InputVrm)) {
    throw "Base VRM Aina belum ada: $InputVrm`nBuka project VRoid lalu Export as VRM sekali. Jangan gunakan Seed-san."
}
if ((Split-Path -Leaf $InputVrm) -match 'Seed-san') {
    throw 'Seed-san ditolak sebagai base Aina karena membawa artifact robot.'
}

$outputDir = Join-Path $PSScriptRoot 'output'
$workDir = Join-Path $PSScriptRoot 'work'
New-Item -ItemType Directory -Force -Path $outputDir, $workDir | Out-Null
$outputVrm = Join-Path $outputDir "Aina_Venara_$Version.vrm"
$workBlend = Join-Path $workDir "Aina_Venara_$Version.blend"
$script = Join-Path $PSScriptRoot 'scripts\build_aina_v1.py'

Remove-Item -LiteralPath $outputVrm, $workBlend -Force -ErrorAction SilentlyContinue
& $Blender --background --python $script -- --input $InputVrm --output $outputVrm --blend $workBlend
if ($LASTEXITCODE -ne 0) {
    throw "Build gagal dengan exit code $LASTEXITCODE"
}
foreach ($artifact in @($outputVrm, $workBlend)) {
    if (-not (Test-Path -LiteralPath $artifact) -or (Get-Item -LiteralPath $artifact).Length -eq 0) {
        throw "Build gagal: Blender tidak menghasilkan $artifact"
    }
}

powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'validate_output.ps1') -Vrm $outputVrm
if ($LASTEXITCODE -ne 0) {
    throw "Validasi kandidat VRM gagal dengan exit code $LASTEXITCODE"
}
powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'render_previews.ps1') -Blend $workBlend -Version $Version

Write-Host "Kandidat VRM siap: $outputVrm"
Write-Host "File Blender: $workBlend"
Write-Host "Preview: $(Join-Path $outputDir "previews\Aina_Venara_${Version}_contact_sheet.png")"
