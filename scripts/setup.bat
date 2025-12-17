@echo off
echo.
echo ======================================================================
echo   ENHANCED LEARNING CURATION SYSTEM - SETUP
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
echo   1. Activate environment: venv\Scripts\activate.bat
echo   2. Run server:          python app.py
echo   3. Open browser:        http://localhost:5000
echo.
echo ======================================================================
pause
