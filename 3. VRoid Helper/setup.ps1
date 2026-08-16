$ErrorActionPreference = "Stop"

function Find-Python312 {
    $direct = "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python312\python.exe"
    if (Test-Path -LiteralPath $direct) { return $direct }
    foreach ($command in @("py", "python")) {
        if (Get-Command $command -ErrorAction SilentlyContinue) {
            try {
                if ($command -eq "py") {
                    & py -3.12 -c "import sys; assert sys.version_info[:2] == (3, 12)"
                    if ($LASTEXITCODE -eq 0) { return "py -3.12" }
                } else {
                    & python -c "import sys; assert sys.version_info[:2] == (3, 12)"
                    if ($LASTEXITCODE -eq 0) { return "python" }
                }
            } catch {}
        }
    }
    return $null
}

$python = Find-Python312
if (-not $python) {
    Write-Host "Python 3.12 belum ditemukan. Install Python 3.12 x64 terlebih dahulu." -ForegroundColor Yellow
    exit 1
}
if (-not (Test-Path ".venv")) {
    if ($python -eq "py -3.12") { & py -3.12 -m venv .venv }
    else { & $python -m venv .venv }
}
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
& ".\.venv\Scripts\python.exe" -m pytest -q
Write-Host "Setup selesai. Jalankan 'Launch VRoid Helper.vbs'." -ForegroundColor Green

