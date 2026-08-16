$ErrorActionPreference = "Stop"

function Find-Python312 {
    $commands = @("py", "python")
    foreach ($command in $commands) {
        if (Get-Command $command -ErrorAction SilentlyContinue) {
            if ($command -eq "py") {
                try {
                    & py -3.12 -c "import sys; assert sys.version_info[:2] == (3, 12)" 2>$null
                    if ($LASTEXITCODE -eq 0) { return @("py", "-3.12") }
                } catch {}
            } else {
                try {
                    & python -c "import sys; assert sys.version_info[:2] == (3, 12)" 2>$null
                    if ($LASTEXITCODE -eq 0) { return @("python") }
                } catch {}
            }
        }
    }
    return $null
}

$python = Find-Python312
if (-not $python) {
    Write-Host "Python 3.12 belum ditemukan." -ForegroundColor Yellow
    Write-Host "Install Python 3.12 x64 dari https://www.python.org/downloads/release/python-31210/"
    Write-Host "Saat instalasi, aktifkan 'Add python.exe to PATH', lalu jalankan setup.cmd lagi."
    exit 1
}

if (Test-Path ".venv") {
    $venvHealthy = $false
    try {
        & ".\.venv\Scripts\python.exe" -c "import sys; print(sys.executable)" 2>$null | Out-Null
        $venvHealthy = $LASTEXITCODE -eq 0
    } catch {}
    if (-not $venvHealthy) {
        $venvPath = (Resolve-Path ".venv").Path
        $workspace = (Resolve-Path ".").Path
        if (-not $venvPath.StartsWith($workspace, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to remove unsafe venv path: $venvPath"
        }
        Write-Host "Environment .venv lama rusak. Membuat ulang..." -ForegroundColor Yellow
        Remove-Item -LiteralPath $venvPath -Recurse -Force
    }
}

if (-not (Test-Path ".venv")) {
    if ($python.Count -gt 1) {
        & $python[0] @($python[1..($python.Count - 1)]) -m venv .venv
    } else {
        & $python[0] -m venv .venv
    }
}

& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
& ".\.venv\Scripts\python.exe" -m pytest
& ".\.venv\Scripts\python.exe" -c "from aina_companion.startup import ensure_launcher; ensure_launcher()"
Write-Host ""
Write-Host "Mengecek Unity renderer..." -ForegroundColor Cyan
& ".\scripts\find_unity.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python companion tetap dapat dipakai. Pasang Unity Hub lalu jalankan scripts\build_unity_renderer.cmd untuk avatar 3D." -ForegroundColor Yellow
}
Write-Host "Setup selesai. Jalankan 'Launch Aina.vbs' untuk membuka Aina tanpa CMD." -ForegroundColor Green
