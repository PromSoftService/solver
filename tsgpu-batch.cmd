@echo off
setlocal
if "%~3"=="" (
  echo Usage: tsgpu-batch.cmd config.json boards.txt output\
  exit /b 2
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tsgpu-batch.ps1" %*
exit /b %ERRORLEVEL%
