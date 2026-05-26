# Convenience script: starts backend + frontend in two PowerShell windows.
# Usage:  .\start-dev.ps1
# Prereqs: backend/.env and frontend/.env.local are filled in, deps installed.

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Start-Process powershell -ArgumentList "-NoExit", "-Command",
  "Set-Location '$root\backend'; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8000"

Start-Process powershell -ArgumentList "-NoExit", "-Command",
  "Set-Location '$root\frontend'; npm run dev"

Write-Host "Backend  -> http://localhost:8000  (docs at /docs)"
Write-Host "Frontend -> http://localhost:3000"
