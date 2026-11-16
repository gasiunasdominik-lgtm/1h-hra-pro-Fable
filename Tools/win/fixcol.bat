@echo off
call "%~dp0_env.bat"
"%UE%\Engine\Binaries\Win64\UnrealEditor.exe" "%PROJ%" -ExecutePythonScript="%~dp0..\fix_collision.py" -unattended -nosplash -log=fixcol.log
