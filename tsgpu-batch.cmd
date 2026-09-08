@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tsgpu-batch.ps1" %*
exit /b %ERRORLEVEL%
