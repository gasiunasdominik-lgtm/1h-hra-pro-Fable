@echo off
call "%~dp0_env.bat"
"%UE%\Engine\Binaries\Win64\UnrealEditor.exe" "%PROJ%" -ExecutePythonScript="%~dp0..\fix_materials.py" -unattended -nosplash -log=fix.log
