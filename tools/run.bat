@echo off

set BLENDERPATH=C:\Program Files\Blender Foundation\Blender 4.0
set PYTHONPATH=C:\Program Files\Blender Foundation\Blender 4.0\4.0\python\bin
set WORKSPACEPATH=%1
set TOOLSPATH=%WORKSPACEPATH%\tools

C:
cd %PYTHONPATH%
python.exe -m ensurepip --upgrade >nul 2>&1
python.exe -m pip install --upgrade pip >nul 2>&1
python.exe -m pip install --user -r %TOOLSPATH%\requirements.txt >nul 2>&1

C:
cd %BLENDERPATH%
blender.exe --background --python %2 -- %3