@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"
echo [ClassicFoot] Build Windows iniciado...

if exist ".venv\Scripts\activate.bat" (
  call ".venv\Scripts\activate.bat"
)

python -m pip install --upgrade pip >nul
python -m pip install pyinstaller >nul

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

pyinstaller ^
  --noconfirm ^
  --windowed ^
  --name ClassicFoot ^
  launcher_gui.py

echo.
echo [ClassicFoot] Build concluido.
echo Executavel: %CD%\dist\ClassicFoot\ClassicFoot.exe
endlocal
