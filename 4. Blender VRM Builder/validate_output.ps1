param(
    [string]$Vrm = (Join-Path $PSScriptRoot 'output\Aina_Venara_v1.vrm'),
    [string]$Blender = 'C:\Program Files\Blender Foundation\Blender 4.5\blender.exe'
)

$ErrorActionPreference = 'Stop'
$script = Join-Path $PSScriptRoot 'scripts\validate_output.py'
$stamp = Join-Path $env:TEMP 'aina_vrm_validation.ok'
Remove-Item -LiteralPath $stamp -Force -ErrorAction SilentlyContinue
& $Blender --background --python $script -- --input $Vrm --stamp $stamp
if ($LASTEXITCODE -ne 0) {
    throw "Validasi VRM gagal dengan exit code $LASTEXITCODE"
}
if (-not (Test-Path -LiteralPath $stamp)) {
    throw 'Validasi VRM gagal: Blender tidak menghasilkan stamp sukses.'
}
Remove-Item -LiteralPath $stamp -Force
