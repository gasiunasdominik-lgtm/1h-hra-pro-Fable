@echo off
call "%~dp0_env.bat"
"%UE%\Engine\Binaries\Win64\UnrealEditor.exe" "%PROJ%" /Game/Maps/Galerie -game -windowed -ResX=1600 -ResY=900 -log=play.log %*
