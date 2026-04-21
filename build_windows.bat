@echo off
setlocal

echo [ClassicFoot] Build Windows iniciado...

set BUILD_VENV=.venv_gui_build

if not exist "%BUILD_VENV%\Scripts\python.exe" (
    python -m venv "%BUILD_VENV%"
)

call "%BUILD_VENV%\Scripts\activate.bat"

python -m pip show pyinstaller >nul 2>&1 || python -m pip install pyinstaller
python -m pip show colorama >nul 2>&1 || python -m pip install -r requirements.txt

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

pyinstaller ^
  --noconfirm ^
  --windowed ^
  --name ClassicFoot ^
  --add-data "data/teams.json;data" ^
  launcher_gui.py

echo.
echo [ClassicFoot] Build concluido.
echo Executavel: %CD%\dist\ClassicFoot\ClassicFoot.exe
