@echo off
set "BLENDER=C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"
set "WORK=%~dp0work\Aina_Venara_v6.blend"
if not exist "%WORK%" (
  echo File kerja belum ada. Jalankan build_aina_v1.cmd dahulu.
  pause
  exit /b 1
)
start "" "%BLENDER%" "%WORK%"
