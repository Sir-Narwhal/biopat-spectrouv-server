@echo off
setlocal

rem ------------------------------------------------------------------
rem export-docker-images.bat
rem
rem Builds every image defined in app\Dockerfile (udpparser, opcserver,
rem udphelper), pulls the Redis image used by compose.yaml, and exports
rem each one as a .tar archive into dist\docker-images\ so they can be
rem copied to another machine and loaded with "docker load".
rem
rem Usage:  export-docker-images.bat [version-tag]
rem         (version-tag defaults to "latest", e.g. 1.0.1)
rem ------------------------------------------------------------------

set "TAG=%~1"
if "%TAG%"=="" set "TAG=latest"

set "REPO_ROOT=%~dp0"
set "OUT_DIR=%REPO_ROOT%dist\docker-images"
set "REDIS_IMAGE=redis:7-alpine"

docker version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running or not installed.
    exit /b 1
)

if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"

echo.
echo === Building images from app\Dockerfile (tag: %TAG%) ===
for %%S in (udpparser opcserver udphelper) do (
    echo.
    echo --- Building biopat-spectrouv/%%S:%TAG% ---
    docker build --target %%S -t biopat-spectrouv/%%S:%TAG% "%REPO_ROOT%app"
    if errorlevel 1 (
        echo ERROR: build failed for %%S.
        exit /b 1
    )
)

echo.
echo === Pulling %REDIS_IMAGE% ===
docker pull %REDIS_IMAGE%
if errorlevel 1 (
    echo ERROR: could not pull %REDIS_IMAGE%.
    exit /b 1
)

echo.
echo === Exporting images to %OUT_DIR% ===
for %%S in (udpparser opcserver udphelper) do (
    echo Saving biopat-spectrouv-%%S-%TAG%.tar
    docker save -o "%OUT_DIR%\biopat-spectrouv-%%S-%TAG%.tar" biopat-spectrouv/%%S:%TAG%
    if errorlevel 1 (
        echo ERROR: export failed for %%S.
        exit /b 1
    )
)

echo Saving redis-7-alpine.tar
docker save -o "%OUT_DIR%\redis-7-alpine.tar" %REDIS_IMAGE%
if errorlevel 1 (
    echo ERROR: export failed for %REDIS_IMAGE%.
    exit /b 1
)

echo.
echo Done. Exported archives:
dir /b "%OUT_DIR%\*.tar"
echo.
echo To load them on another machine:
echo     docker load -i ^<file^>.tar

endlocal
