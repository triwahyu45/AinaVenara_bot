$hub = "C:\Program Files\Unity Hub\Unity Hub.exe"
$editors = "C:\Program Files\Unity\Hub\Editor"
if (-not (Test-Path -LiteralPath $hub)) {
    Write-Host "Unity Hub belum ditemukan." -ForegroundColor Yellow
    Write-Host "Install dari https://unity.com/download lalu pasang Unity Editor 2022.3 LTS dengan Windows Build Support."
    exit 1
}
if (-not (Test-Path -LiteralPath $editors)) {
    Write-Host "Unity Hub ditemukan, tetapi editor belum ada. Install Unity 2022.3 LTS dan Windows Build Support melalui Hub." -ForegroundColor Yellow
    exit 1
}
$unity = Get-ChildItem -LiteralPath $editors -Directory |
    Where-Object { $_.Name -like "2022.3*" } |
    Sort-Object Name -Descending |
    ForEach-Object { Join-Path $_.FullName "Editor\Unity.exe" } |
    Where-Object { Test-Path -LiteralPath $_ } |
    Select-Object -First 1
if (-not $unity) {
    Write-Host "Unity 2022.3 LTS belum ditemukan. Install melalui Unity Hub." -ForegroundColor Yellow
    exit 1
}
Write-Output $unity

