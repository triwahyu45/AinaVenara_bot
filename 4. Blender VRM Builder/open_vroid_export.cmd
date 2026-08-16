@echo off
set "VROID=C:\Program Files (x86)\Steam\steamapps\common\VRoid Studio\VRoidStudio.exe"
set "PROJECT=%~dp0..\2. Aina Venara Model\Vroid Project\Aina_Venara.vroid"
if not exist "%VROID%" (
  echo VRoid Studio tidak ditemukan: %VROID%
  pause
  exit /b 1
)
start "" "%VROID%" "%PROJECT%"

