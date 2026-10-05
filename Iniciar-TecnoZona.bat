@echo off
setlocal
cd /d "%~dp0"
set "TZ_PYTHON="
if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "TZ_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not defined TZ_PYTHON if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set "TZ_PYTHON=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
if not defined TZ_PYTHON if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "TZ_PYTHON=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not defined TZ_PYTHON if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set "TZ_PYTHON=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if not defined TZ_PYTHON (
  where python >nul 2>nul
  if not errorlevel 1 set "TZ_PYTHON=python"
)
if not defined TZ_PYTHON (
  where py >nul 2>nul
  if not errorlevel 1 set "TZ_PYTHON=py -3"
)
if not defined TZ_PYTHON (
  echo No se encontro Python. Instala Python 3 y vuelve a abrir este archivo.
  echo Descarga oficial: https://www.python.org/downloads/windows/
  pause
  exit /b 1
)
if /I "%TZ_PYTHON%"=="py -3" (
  py -3 local_server.py
) else (
  "%TZ_PYTHON%" local_server.py
)
pause
