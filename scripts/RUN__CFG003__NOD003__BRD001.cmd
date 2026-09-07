@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run-CFG003-NOD003-BRD001.ps1"
exit /b %ERRORLEVEL%
