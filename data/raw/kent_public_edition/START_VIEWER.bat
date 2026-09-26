@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto usepython
py -3 viewer.py %*
goto done
:usepython
python viewer.py %*
:done
if errorlevel 1 pause
endlocal
