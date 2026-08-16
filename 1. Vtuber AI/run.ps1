$ErrorActionPreference = "Stop"
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "Environment belum siap. Jalankan .\setup.ps1 terlebih dahulu." -ForegroundColor Yellow
    exit 1
}
try {
    & ".\.venv\Scripts\python.exe" -c "import sys; print(sys.executable)" | Out-Null
} catch {
    Write-Host "Environment Python rusak atau Python induknya sudah berpindah. Hapus folder .venv lalu jalankan setup.cmd lagi." -ForegroundColor Yellow
    exit 1
}
if ($LASTEXITCODE -ne 0) {
    Write-Host "Environment Python rusak atau Python induknya sudah berpindah. Hapus folder .venv lalu jalankan setup.cmd lagi." -ForegroundColor Yellow
    exit 1
}
& ".\.venv\Scripts\python.exe" -m aina_companion
