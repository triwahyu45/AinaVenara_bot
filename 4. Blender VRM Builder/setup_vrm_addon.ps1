param(
    [string]$Blender = 'C:\Program Files\Blender Foundation\Blender 4.5\blender.exe'
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $Blender)) {
    throw "Blender tidak ditemukan: $Blender"
}

$downloadDir = Join-Path $PSScriptRoot 'downloads'
New-Item -ItemType Directory -Force -Path $downloadDir | Out-Null

$release = Invoke-RestMethod -Uri 'https://api.github.com/repos/saturday06/VRM-Addon-for-Blender/releases/latest'
$asset = $release.assets |
    Where-Object { $_.name -like 'VRM_Addon_for_Blender-Extension-*.zip' } |
    Select-Object -First 1

if (-not $asset) {
    throw 'Asset extension VRM resmi tidak ditemukan pada release terbaru.'
}

$archive = Join-Path $downloadDir $asset.name
Write-Host "Mengunduh VRM Add-on $($release.tag_name)..."
Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $archive

Write-Host 'Memasang dan mengaktifkan extension VRM...'
$repo = Join-Path $env:APPDATA 'Blender Foundation\Blender\4.5\extensions\user_default'
New-Item -ItemType Directory -Force -Path $repo | Out-Null
& $Blender --command extension install-file --repo user_default -e (Resolve-Path $archive).Path
if ($LASTEXITCODE -ne 0) {
    throw "Instalasi VRM Add-on gagal dengan exit code $LASTEXITCODE"
}

& $Blender --background --python (Join-Path $PSScriptRoot 'scripts\check_vrm_addon.py')
if ($LASTEXITCODE -ne 0) {
    throw 'Instalasi selesai tetapi operator VRM belum dapat dimuat.'
}

Write-Host 'VRM Add-on siap dan operator telah diverifikasi.'
