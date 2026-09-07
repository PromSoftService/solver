@echo off
setlocal

if /I "%~1"=="resume" (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run-CFG003-NOD003-BRD001.ps1" -ResumeLatestFailed
) else (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run-CFG003-NOD003-BRD001.ps1"
)

exit /b %ERRORLEVEL%
