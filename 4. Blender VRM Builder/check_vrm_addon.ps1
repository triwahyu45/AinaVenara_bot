param(
    [string]$Blender = 'C:\Program Files\Blender Foundation\Blender 4.5\blender.exe'
)

$ErrorActionPreference = 'Stop'
$script = Join-Path $PSScriptRoot 'scripts\check_vrm_addon.py'
& $Blender --background --python $script
if ($LASTEXITCODE -ne 0) {
    throw 'VRM Add-on belum siap. Jalankan setup_vrm_addon.ps1.'
}

