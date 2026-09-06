@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run-CFG002-BRD001.ps1"
exit /b %ERRORLEVEL%
