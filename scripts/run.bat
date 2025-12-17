@echo off
setlocal

REM One-click runner for the advanced RFAI server
cd /d "%~dp0\.."

if not exist venv\Scripts\python.exe (
	echo Virtual environment not found. Running setup...
	call setup.bat
)

call venv\Scripts\activate.bat

if not defined HOST set HOST=0.0.0.0
if not defined PORT set PORT=5000

echo Starting RFAI on http://%HOST%:%PORT%
python rfai_server.py --host %HOST% --port %PORT%

endlocal
