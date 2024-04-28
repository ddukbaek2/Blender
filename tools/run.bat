@echo off

set BLENDERPATH=C:\Program Files\Blender Foundation\Blender 4.0
set PYTHONPATH=C:\Program Files\Blender Foundation\Blender 4.0\4.0\python\bin
set PROJECTPATH=%1
set TOOLSPATH=%PROJECTPATH%\tools
set BUILDPATH=%PROJECTPATH%\build
set SPECPATH=%PROJECTPATH%\spec

for /f "tokens=1 delims=:" %%a in ("%PYTHONPATH%") do set "PYTHONDRIVE=%%a:"
for /f "tokens=1 delims=:" %%a in ("%BLENDERPATH%") do set "BLENDERDRIVE=%%a:"
for /f "tokens=1 delims=:" %%a in ("%PROJECTPATH%") do set "PROJECTDRIVE=%%a:"

%PYTHONDRIVE%
cd %PYTHONPATH%
python.exe --version
python.exe -m ensurepip --upgrade >nul 2>&1
python.exe -m pip install --upgrade pip >nul 2>&1
python.exe -m pip install --user -r %TOOLSPATH%\requirements.txt >nul 2>&1

%BLENDERDRIVE%
cd %BLENDERPATH%
blender.exe --background --python %2 -- %3 %4