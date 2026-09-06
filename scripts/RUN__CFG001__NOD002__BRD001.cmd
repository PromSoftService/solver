@echo off
setlocal

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run-Study.ps1" ^
  -RangeId "RNG001" ^
  -ConfigId "CFG001" ^
  -DecisionId "NOD002" ^
  -DecisionNode "UTG_CBET" ^
  -BoardSetId "BRD001" ^
  -ConfigPath "configs\CFG001__6M100_UTG-O2p5_BB-C__F_BB-X_UTG-B33_BB-XR60__T-B100-R100__R-B100-R100__V1.json" ^
  -BoardsPath "boards\BRD001__FLOP_UNPAIRED_RAINBOW__ISO286__V1.txt" ^
  -RangeProfilePath "ranges\RNG001__TSGPU020_6M100_UTG-O2p5_BB-C__V1.json" ^
  -UtgRangePath "ranges\RNG001__TSGPU020_6M100_UTG-O2p5_BB-C__V1__UTG.txt" ^
  -BbRangePath "ranges\RNG001__TSGPU020_6M100_UTG-O2p5_BB-C__V1__BB.txt" ^
  -ExpectedBetAmount 18 ^
  -ExpectedRaiseAmount 0 ^
  -MoneyScale 10

exit /b %ERRORLEVEL%
