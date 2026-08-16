param(
    [string]$Candidate = (Join-Path $PSScriptRoot 'output\Aina_Venara_v6.vrm')
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $Candidate)) {
    throw "Kandidat VRM tidak ditemukan: $Candidate"
}

$models = Join-Path $env:LOCALAPPDATA 'AinaDesktopCompanion\models'
$settingsPath = Join-Path $env:LOCALAPPDATA 'AinaDesktopCompanion\settings.json'
$destination = Join-Path $models (Split-Path -Leaf $Candidate)
New-Item -ItemType Directory -Force -Path $models | Out-Null
Copy-Item -LiteralPath $Candidate -Destination $destination -Force

if (Test-Path -LiteralPath $settingsPath) {
    $settings = Get-Content -Raw -LiteralPath $settingsPath | ConvertFrom-Json
    if (-not $settings.avatar) {
        $settings | Add-Member -MemberType NoteProperty -Name avatar -Value ([pscustomobject]@{})
    }
    $settings.avatar | Add-Member -MemberType NoteProperty -Name model_path -Value $destination -Force
    $settings | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $settingsPath -Encoding UTF8
}

Write-Host "Aina VRM terpasang lokal: $destination"
