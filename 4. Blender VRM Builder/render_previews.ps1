param(
    [string]$Blend = (Join-Path $PSScriptRoot 'work\Aina_Venara_v1.blend'),
    [string]$Version = 'v1',
    [string]$Blender = 'C:\Program Files\Blender Foundation\Blender 4.5\blender.exe'
)

$ErrorActionPreference = 'Stop'
$previewDir = Join-Path $PSScriptRoot "output\previews\$Version"
New-Item -ItemType Directory -Force -Path $previewDir | Out-Null
$script = Join-Path $PSScriptRoot 'scripts\render_previews.py'
& $Blender --background $Blend --python $script -- --output $previewDir
if ($LASTEXITCODE -ne 0) {
    throw "Render preview gagal dengan exit code $LASTEXITCODE"
}

Add-Type -AssemblyName System.Drawing
$names = @('front', 'left', 'right', 'back', 'face', 'top')
$sheet = New-Object System.Drawing.Bitmap 1536, 1536
$graphics = [System.Drawing.Graphics]::FromImage($sheet)
try {
    $graphics.Clear([System.Drawing.Color]::FromArgb(30, 34, 43))
    for ($index = 0; $index -lt $names.Count; $index++) {
        $imagePath = Join-Path $previewDir "$($names[$index]).png"
        if (-not (Test-Path -LiteralPath $imagePath)) { throw "Preview hilang: $imagePath" }
        $image = [System.Drawing.Image]::FromFile($imagePath)
        try {
            $x = ($index % 3) * 512
            $y = [math]::Floor($index / 3) * 768
            $graphics.DrawImage($image, $x, $y, 512, 768)
        } finally {
            $image.Dispose()
        }
    }
    $sheetPath = Join-Path $PSScriptRoot "output\previews\Aina_Venara_${Version}_contact_sheet.png"
    $sheet.Save($sheetPath, [System.Drawing.Imaging.ImageFormat]::Png)
    Write-Host "Contact sheet siap: $sheetPath"
} finally {
    $graphics.Dispose()
    $sheet.Dispose()
}

