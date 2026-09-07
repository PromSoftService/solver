@echo off
setlocal EnableExtensions

call "%~dp0RUN__CFG003__NOD004__BRD001.cmd"
if errorlevel 1 (
  echo NOD004 first pass failed. Retrying incomplete boards once...
  call "%~dp0RUN__CFG003__NOD004__BRD001.cmd" resume
  if errorlevel 1 exit /b %ERRORLEVEL%
)

call "%~dp0RUN__CFG003__NOD005__BRD001.cmd"
if errorlevel 1 (
  echo NOD005 first pass failed. Retrying incomplete boards once...
  call "%~dp0RUN__CFG003__NOD005__BRD001.cmd" resume
  if errorlevel 1 exit /b %ERRORLEVEL%
)

pushd "%~dp0.."
git add .
git diff --cached --quiet
if errorlevel 1 (
  git commit -m "add RNG002 CFG003 NOD004 NOD005 BRD001 datasets"
  if errorlevel 1 (
    popd
    exit /b %ERRORLEVEL%
  )
  git push
  if errorlevel 1 (
    popd
    exit /b %ERRORLEVEL%
  )
) else (
  echo No new files to commit.
)
popd

echo.
echo BOTH STUDIES COMPLETE AND PUSHED.
exit /b 0
