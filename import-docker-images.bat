@echo off
setlocal enabledelayedexpansion

rem ------------------------------------------------------------------
rem import-docker-images.bat
rem
rem Loads every .tar image archive produced by export-docker-images.bat
rem into the local Docker engine using "docker load".
rem
rem Usage:  import-docker-images.bat [folder-with-tar-files]
rem         (folder defaults to dist\docker-images next to this script)
rem ------------------------------------------------------------------

set "SRC_DIR=%~1"
if "%SRC_DIR%"=="" set "SRC_DIR=%~dp0dist\docker-images"

docker version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running or not installed.
    exit /b 1
)

if not exist "%SRC_DIR%\" (
    echo ERROR: folder not found: %SRC_DIR%
    exit /b 1
)

dir /b "%SRC_DIR%\*.tar" >nul 2>&1
if errorlevel 1 (
    echo ERROR: no .tar files found in %SRC_DIR%
    exit /b 1
)

echo.
echo === Loading images from %SRC_DIR% ===
set /a LOADED=0
for %%F in ("%SRC_DIR%\*.tar") do (
    echo.
    echo --- Loading %%~nxF ---
    docker load -i "%%F"
    if errorlevel 1 (
        echo ERROR: failed to load %%~nxF
        exit /b 1
    )
    set /a LOADED+=1
)

echo.
echo Done. Loaded !LOADED! archive(s). Images now available:
docker images --filter "reference=biopat-spectrouv/*" --filter "reference=redis:7-alpine"

endlocal
