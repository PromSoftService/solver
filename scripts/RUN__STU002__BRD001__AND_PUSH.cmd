@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run-STU002.ps1" %*
exit /b %ERRORLEVEL%
