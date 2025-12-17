@echo off
REM Thin wrapper - delegates to organized scripts folder
cd /d "%~dp0"
call scripts\setup.bat %*
