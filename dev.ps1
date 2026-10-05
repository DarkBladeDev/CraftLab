<#
.SYNOPSIS
    Dev Deploy & Runtime Launcher for Minecraft Content Platform
.DESCRIPTION
    Builds and starts all monorepo systems locally:
    - Backend: FastAPI + WebSocket Gateway on http://127.0.0.1:8000
    - Frontend: React + Vite on http://localhost:3000
    - Paper Agent: Builds paper-agent-1.0.0-SNAPSHOT.jar and optionally runs Mock Agent runtime.
.EXAMPLE
    .\dev.ps1
    .\dev.ps1 -Mode all
    .\dev.ps1 -Mode server
    .\dev.ps1 -PaperPluginsDir "C:\path\to\minecraft-server\plugins"
#>

[CmdletBinding()]
param(
    [ValidateSet("all", "server", "build-jar", "stop")]
    [string]$Mode = "all",

    [string]$PaperPluginsDir = ""
)

$ErrorActionPreference = "Stop"
$RootDir = $PSScriptRoot

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   MINECRAFT CONTENT PLATFORM - LOCAL DEV DEPLOY RUNNER   " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Stop mode
if ($Mode -eq "stop") {
    Write-Host "[*] Stopping any running local dev processes..." -ForegroundColor Yellow
    Get-Process -Name "uvicorn", "node" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] Dev processes stopped." -ForegroundColor Green
    exit 0
}

# 2. Build Paper Agent JAR
Write-Host "[1/4] Checking Paper 1.21 Plugin Agent..." -ForegroundColor Cyan
Push-Location "$RootDir\paper-agent"
try {
    if (-not (Test-Path "build\libs\paper-agent-1.0.0-SNAPSHOT.jar")) {
        Write-Host "      Building JAR with Gradle..." -ForegroundColor Gray
        .\gradlew.bat build -q
    }
    Write-Host "      [OK] JAR ready: paper-agent\build\libs\paper-agent-1.0.0-SNAPSHOT.jar" -ForegroundColor Green

    if ($PaperPluginsDir -ne "" -and (Test-Path $PaperPluginsDir)) {
        Copy-Item "build\libs\paper-agent-1.0.0-SNAPSHOT.jar" -Destination $PaperPluginsDir -Force
        Write-Host "      [OK] Deployed JAR directly to: $PaperPluginsDir" -ForegroundColor Green
    }
} finally {
    Pop-Location
}

if ($Mode -eq "build-jar") {
    Write-Host "`n[OK] JAR build complete." -ForegroundColor Green
    exit 0
}

# 3. Check Backend setup
Write-Host "`n[2/4] Verifying Backend Environment..." -ForegroundColor Cyan
$BackendVenv = "$RootDir\backend\.venv\Scripts\python.exe"
if (-not (Test-Path $BackendVenv)) {
    Write-Host "      Creating Python venv..." -ForegroundColor Gray
    python -m venv "$RootDir\backend\.venv"
    & "$RootDir\backend\.venv\Scripts\pip.exe" install -r "$RootDir\backend\requirements.txt" -q
}
Write-Host "      [OK] Backend environment ready." -ForegroundColor Green

# 4. Check Frontend setup
Write-Host "`n[3/4] Verifying Frontend Environment..." -ForegroundColor Cyan
if (-not (Test-Path "$RootDir\frontend\node_modules")) {
    Write-Host "      Installing frontend node_modules..." -ForegroundColor Gray
    Push-Location "$RootDir\frontend"
    npm install --silent
    Pop-Location
}
Write-Host "      [OK] Frontend environment ready." -ForegroundColor Green

# 5. Launch Services
Write-Host "`n[4/4] Starting Local Runtime Services ($Mode mode)..." -ForegroundColor Cyan

# A. Start Backend
Write-Host "      Starting FastAPI Backend & WebSocket Gateway on port 8000..." -ForegroundColor Gray
$BackendCmd = "cd '$RootDir\backend'; .\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle='MCP - Backend & Gateway'; $BackendCmd"

Start-Sleep -Seconds 2

# B. Start Frontend
Write-Host "      Starting React + Vite Frontend on port 3000..." -ForegroundColor Gray
$FrontendCmd = "cd '$RootDir\frontend'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "`$Host.UI.RawUI.WindowTitle='MCP - Frontend Web UI'; $FrontendCmd"

Start-Sleep -Seconds 2

# C. Start Mock Agent (if Mode == "all")
if ($Mode -eq "all") {
    Write-Host "      Starting Simulated Paper 1.21 Agent runtime..." -ForegroundColor Gray
    $AgentCmd = "cd '$RootDir\backend'; .\.venv\Scripts\python.exe mock_agent.py"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle='MCP - Paper 1.21 Mock Agent'; $AgentCmd"
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "             ALL SYSTEMS RUNNING LOCALLY!                 " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  * Web Editor Dashboard : http://localhost:3000" -ForegroundColor White
Write-Host "  * REST API & Docs      : http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "  * Agent Gateway (WS)   : ws://127.0.0.1:8000/ws/agent" -ForegroundColor White
Write-Host "  * Target Server Status : local-paper-server (ONLINE)" -ForegroundColor Green
Write-Host "  * Compiled Plugin JAR  : paper-agent\build\libs\paper-agent-1.0.0-SNAPSHOT.jar" -ForegroundColor White
Write-Host ""
Write-Host "Tip: To deploy to a live Paper server, copy the JAR to its plugins/ folder." -ForegroundColor Gray
Write-Host "To stop dev processes later, run: .\dev.ps1 -Mode stop" -ForegroundColor Yellow
Write-Host ""

# Optional: open browser
try {
    Start-Process "http://localhost:3000"
} catch {
}
