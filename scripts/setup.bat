@echo off
echo.
echo ======================================================================
echo   RFAI (ADVANCED) - SETUP
echo ======================================================================
echo.

python --version

echo.
echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ======================================================================
echo   SETUP COMPLETE!
echo ======================================================================
echo.
echo To start the system:
echo   1. Run:                 run.bat
echo   2. Open:                http://localhost:5000 (or the port you set)
echo.
echo ======================================================================
pause
