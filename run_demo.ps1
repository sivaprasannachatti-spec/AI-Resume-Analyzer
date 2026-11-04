# One-click demo launcher for interview presentation
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Starting ResuMatch AI Backend & Frontend Demo   " -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Start FastAPI Backend Server on port 8000 in a new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host '=== FastAPI Backend (Port 8000) ===' -ForegroundColor Yellow; uv run uvicorn app:app --reload --port 8000"

# 2. Start Next.js Frontend Server on port 3000 in a new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host '=== Next.js Frontend (Port 3000) ===' -ForegroundColor Cyan; Set-Location frontend; npm run dev"

Write-Host "Servers are launching in background windows..." -ForegroundColor Yellow
Start-Sleep -Seconds 4

# 3. Open browser to the demo app
Start-Process "http://localhost:3000"

Write-Host "Demo is live at http://localhost:3000 !" -ForegroundColor Green
Write-Host "API Docs are live at http://localhost:8000/docs !" -ForegroundColor Cyan
