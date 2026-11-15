@echo off
call "%~dp0_env.bat"
"%UE%\Engine\Binaries\Win64\UnrealEditor.exe" "%PROJ%" -ExecutePythonScript="%~dp0..\build_level.py" -unattended -nosplash -log=level.log
