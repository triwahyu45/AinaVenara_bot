$ErrorActionPreference = "Stop"
$unity = & "$PSScriptRoot\find_unity.ps1"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$project = Resolve-Path "$PSScriptRoot\..\unity\AinaAvatarRenderer"
New-Item -ItemType Directory -Force -Path "$project\Build" | Out-Null
& $unity -batchmode -quit -projectPath $project -executeMethod Aina.Editor.BuildRenderer.BuildWindowsCommandLine -logFile "$project\Build\build.log"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Build gagal. Buka unity\AinaAvatarRenderer\Build\build.log untuk detail." -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host "Renderer selesai: unity\AinaAvatarRenderer\Build\AinaAvatarRenderer.exe" -ForegroundColor Green
