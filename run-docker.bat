@echo off
setlocal

echo Starting services from compose.yaml...
docker compose up --build -d || exit /b 1

echo Done. Containers running:
docker compose ps

endlocal
