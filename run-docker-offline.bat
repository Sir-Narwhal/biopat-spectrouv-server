@echo off
setlocal

rem ------------------------------------------------------------------
rem run-docker-offline.bat
rem
rem Starts the stack from pre-loaded images (see import-docker-images.bat)
rem using compose.offline.yaml. Nothing is built or pulled, so no internet
rem access is needed.
rem
rem Usage:  run-docker-offline.bat [image-tag]
rem         (tag defaults to "latest"; must match the tag used when
rem          running export-docker-images.bat)
rem ------------------------------------------------------------------

if not "%~1"=="" set "IMAGE_TAG=%~1"

echo Starting services from compose.offline.yaml...
docker compose -f "%~dp0compose.offline.yaml" up -d || exit /b 1

echo Done. Containers running:
docker compose -f "%~dp0compose.offline.yaml" ps

endlocal
