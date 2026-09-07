@echo off
setlocal EnableExtensions

call "%~dp0RUN__CFG003__NOD006__BRD001.cmd"
if errorlevel 1 (
  echo NOD006 first pass failed. Retrying incomplete boards once...
  call "%~dp0RUN__CFG003__NOD006__BRD001.cmd" resume
  if errorlevel 1 exit /b %ERRORLEVEL%
)

pushd "%~dp0.."
git add -- "datasets/DS__RNG002__CFG003__NOD006__BRD001__RUN-*.csv" "datasets/DS__RNG002__CFG003__NOD006__BRD001__RUN-*.manifest.json"
git diff --cached --quiet
if errorlevel 1 (
  git commit -m "add RNG002 CFG003 NOD006 BRD001 dataset"
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
  echo No new NOD006 dataset files to commit.
)
popd
exit /b 0
