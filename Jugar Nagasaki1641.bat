@echo off
setlocal
set "VED=%~dp0game\Nagasaki1641.ved"
set "PLAYER=C:\Program Files\Visionaire Studio 5\visplayer.exe"

if not exist "%PLAYER%" (
  echo No se encuentra el reproductor:
  echo   %PLAYER%
  echo Instala Visionaire Studio 5 o edita este archivo con la ruta correcta.
  pause
  exit /b 1
)
if not exist "%VED%" (
  echo No se encuentra el proyecto:
  echo   %VED%
  pause
  exit /b 1
)

start "" "%PLAYER%" "%VED%"
