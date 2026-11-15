@echo off
call "%~dp0_env.bat"
"%UE%\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" "%PROJ%" -run=ResavePackages -BuildLighting -BuildReflectionCaptures -Quality=Medium -MapsOnly -ProjectOnly -AllowCommandletRendering -Map=Galerie -unattended -log=bake.log
