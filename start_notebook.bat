@echo off
setlocal
set "DIR=%~dp0"
set "FILE=%DIR%index.html"

if not exist "%FILE%" (
  echo 未找到 index.html
  pause
  exit /b 1
)

where msedge >nul 2>nul
if %errorlevel%==0 (
  start "" msedge "%FILE%"
  exit /b 0
)

where chrome >nul 2>nul
if %errorlevel%==0 (
  start "" chrome "%FILE%"
  exit /b 0
)

start "" "%FILE%"
