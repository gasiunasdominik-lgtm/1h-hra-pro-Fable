@echo off
rem Kompletni sestaveni: C++ -> import assetu a stavba mapy -> zapeceni svetla (Lightmass) -> spusteni
set UE=C:\Program Files\Epic Games\UE_5.8
call "%UE%\Engine\Build\BatchFiles\Build.bat" GalerieEditor Win64 Development -project="%~dp0Galerie.uproject" -waitmutex || exit /b 1
"%UE%\Engine\Binaries\Win64\UnrealEditor.exe" "%~dp0Galerie.uproject" -ExecutePythonScript="%~dp0Tools\build_level.py" -unattended -nosplash -log=level.log
"%UE%\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" "%~dp0Galerie.uproject" -run=ResavePackages -BuildLighting -BuildReflectionCaptures -Quality=Medium -MapsOnly -ProjectOnly -AllowCommandletRendering -Map=Galerie -unattended -log=bake.log
call "%~dp0HRAT.bat"
