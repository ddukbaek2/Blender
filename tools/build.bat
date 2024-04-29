@echo off

set BLENDERPATH=C:\Program Files\Blender Foundation\Blender 4.0
set PYTHONPATH=%BLENDERPATH%\4.0\python\bin
set PROJECTPATH=%1
set TOOLSPATH=%PROJECTPATH%\tools
set LIBSPATH=%PROJECTPATH%\libs
set BUILDPATH=%PROJECTPATH%\build\bin
set SPECPATH=%PROJECTPATH%\build\spec
set HOOKSPATH=%PROJECTPATH%\hooks

for /f "tokens=1 delims=:" %%a in ("%PYTHONPATH%") do set "PYTHONDRIVE=%%a:"
for /f "tokens=1 delims=:" %%a in ("%BLENDERPATH%") do set "BLENDERDRIVE=%%a:"
for /f "tokens=1 delims=:" %%a in ("%PROJECTPATH%") do set "PROJECTDRIVE=%%a:"

%PYTHONDRIVE%
cd "%PYTHONPATH%"
python.exe --version
python.exe -m pip list
python.exe -m ensurepip --upgrade >nul 2>&1
python.exe -m pip install --upgrade pip >nul 2>&1
python.exe -m pip install --user -r "%TOOLSPATH%\requirements.txt" >nul 2>&1
python.exe -m pip install --user -r "%LIBSPATH%\bpy-4.0.0-cp310-cp310-win_amd64.whl" >nul 2>&1
python.exe -m PyInstaller -F --clean --onefile "%2" --distpath "%BUILDPATH%" --specpath "%SPECPATH%" --additional-hooks-dir="%HOOKSPATH%" --name "%3"