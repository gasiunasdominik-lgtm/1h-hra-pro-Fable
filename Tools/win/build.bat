@echo off
call "%~dp0_env.bat"
call "%UE%\Engine\Build\BatchFiles\Build.bat" GalerieEditor Win64 Development -project="%PROJ%" -waitmutex -NoHotReloadFromIDE
