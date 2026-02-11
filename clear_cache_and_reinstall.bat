@echo off
echo Clearing Python cache...
cd /d %~dp0

REM Remove all __pycache__ directories
for /d /r %%i in (__pycache__) do @if exist "%%i" rd /s /q "%%i"

REM Remove all .pyc files
for /r %%i in (*.pyc) do @if exist "%%i" del /q "%%i"

echo.
echo Reinstalling package in editable mode...
python -m pip install -e . --force-reinstall --no-deps

echo.
echo Done! Now restart PyCharm and try again.
pause
