@echo off
cd /d "%~dp0.."
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\Run-STU001.ps1" %*
exit /b %ERRORLEVEL%
