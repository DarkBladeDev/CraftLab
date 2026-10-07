<#
.SYNOPSIS
    Dev Deploy & Runtime Launcher for Minecraft Content Platform (CraftLab)
.DESCRIPTION
    Builds, configures and starts all platform systems locally:
    - Backend: FastAPI + WebSocket Gateway on http://127.0.0.1:8000
    - Frontend: React + Vite Web UI on http://localhost:3000
    - Paper Agent: Builds paper-agent-1.0.0-SNAPSHOT.jar, deploys to live Paper server,
      and starts the Paper 1.21 server in an interactive terminal.
.EXAMPLE
    .\dev.ps1
    .\dev.ps1 -CleanData
    .\dev.ps1 -PaperServerDir "C:\minecraft\paper-1.21"
    .\dev.ps1 -Mode stop
#>

[CmdletBinding()]
param(
    [ValidateSet("all", "server-only", "web-only", "build-jar", "stop", "status")]
    [string]$Mode = "all",

    [string]$PaperServerDir = $env:MCP_PAPER_SERVER_DIR,
    [string]$StartScript = $env:MCP_PAPER_START_SCRIPT,
    [string]$ServerJar = $env:MCP_PAPER_SERVER_JAR,

    [switch]$CleanData,
    [switch]$NoBrowser
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
    Write-Host "[*] Stopping running local dev processes..." -ForegroundColor Yellow
    Get-Process -Name "uvicorn", "node" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] Dev processes stopped." -ForegroundColor Green
    exit 0
}

# 2. Clean-slate Data Reset (if -CleanData requested)
if ($CleanData) {
    Write-Host "[*] Resetting runtime environment and database to pristine state..." -ForegroundColor Yellow
    $DbPath = "$RootDir\..\data\mcp.db"
    if (Test-Path $DbPath) {
        Remove-Item -Path $DbPath -Force -ErrorAction SilentlyContinue
    }
    $OldDbPath = "$RootDir\..\CraftLab-backend\mcp.db"
    if (Test-Path $OldDbPath) {
        Remove-Item -Path $OldDbPath -Force -ErrorAction SilentlyContinue
    }
    
    $PacksDist = "$RootDir\..\data\packs\dist"
    $PacksTmp = "$RootDir\..\data\packs\tmp"
    if (Test-Path $PacksDist) {
        Get-ChildItem -Path $PacksDist -Recurse | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
    }
    if (Test-Path $PacksTmp) {
        Get-ChildItem -Path $PacksTmp -Recurse | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
    }

    # Re-initialize clean tables
    $BackendDir = if (Test-Path "$RootDir\..\CraftLab-backend") { "$RootDir\..\CraftLab-backend" } else { "$RootDir\..\backend" }
    $BackendPython = "$BackendDir\.venv\Scripts\python.exe"
    if (Test-Path $BackendPython) {
        Push-Location $BackendDir
        try {
            & $BackendPython -c "import asyncio; from app.core.database import init_db; asyncio.run(init_db())"
        } finally {
            Pop-Location
        }
    }
    Write-Host "    [OK] Pristine database and pack cache reset complete." -ForegroundColor Green
}

# 3. Build & Deploy Paper Agent JAR
Write-Host "[1/4] Verifying Paper 1.21 Plugin Agent..." -ForegroundColor Cyan
$JarPath = "$RootDir\..\paper-agent\build\libs\paper-agent-1.0.0-SNAPSHOT.jar"

Push-Location "$RootDir\..\paper-agent"
try {
    if (-not (Test-Path $JarPath)) {
        Write-Host "      Building Paper Agent JAR with Gradle..." -ForegroundColor Gray
        .\gradlew.bat build -q
    }
    Write-Host "      [OK] JAR ready: paper-agent\build\libs\paper-agent-1.0.0-SNAPSHOT.jar" -ForegroundColor Green
} finally {
    Pop-Location
}

# Handle deployment to target server if PaperServerDir is provided
$ServerReadyToLaunch = $false
$ServerLaunchCommand = ""

if ($PaperServerDir -ne "" -and (Test-Path $PaperServerDir)) {
    Write-Host "      Target Paper Server: $PaperServerDir" -ForegroundColor Cyan
    $PluginsDir = Join-Path $PaperServerDir "plugins"
    if (-not (Test-Path $PluginsDir)) {
        New-Item -ItemType Directory -Path $PluginsDir -Force | Out-Null
    }

    # Deploy JAR
    Copy-Item $JarPath -Destination $PluginsDir -Force
    Write-Host "      [OK] Deployed McpAgent JAR to: $PluginsDir" -ForegroundColor Green

    # Check for PacketEvents dependency
    $PacketEventsJars = Get-ChildItem -Path $PluginsDir -Filter "*packetevents*.jar" -ErrorAction SilentlyContinue
    if (-not $PacketEventsJars) {
        Write-Host "      [WARNING] PacketEvents plugin (*packetevents*.jar) not found in plugins/!" -ForegroundColor Yellow
        Write-Host "                Virtual Display Props require PacketEvents 2.14+ to render." -ForegroundColor Yellow
    } else {
        Write-Host "      [OK] PacketEvents plugin detected in plugins/." -ForegroundColor Green
    }

    # Ensure config.yml exists
    $AgentConfigDir = Join-Path $PluginsDir "McpAgent"
    $AgentConfigFile = Join-Path $AgentConfigDir "config.yml"
    if (-not (Test-Path $AgentConfigFile)) {
        New-Item -ItemType Directory -Path $AgentConfigDir -Force | Out-Null
        $DefaultConfig = @"
gateway:
  url: "ws://127.0.0.1:8000/ws/agent"
  targetId: "local-paper-server"
  secret: "dev-secret"
  reconnectIntervalSeconds: 5
  heartbeatIntervalSeconds: 15
"@
        Set-Content -Path $AgentConfigFile -Value $DefaultConfig -Encoding UTF8
        Write-Host "      [OK] Created default plugins/McpAgent/config.yml" -ForegroundColor Green
    }

    # Determine Server Launch Command
    $ResolvedScript = if ($StartScript -ne "") {
        if (Test-Path (Join-Path $PaperServerDir $StartScript)) {
            Join-Path $PaperServerDir $StartScript
        } elseif (Test-Path $StartScript) {
            $StartScript
        } else {
            $null
        }
    } else {
        $CommonScripts = @("run.bat", "start.bat", "run.ps1", "start.ps1")
        $Found = $null
        foreach ($s in $CommonScripts) {
            $Candidate = Join-Path $PaperServerDir $s
            if (Test-Path $Candidate) {
                $Found = $Candidate
                break
            }
        }
        $Found
    }

    if ($ResolvedScript) {
        $ServerLaunchCommand = "cd '$PaperServerDir'; & '$ResolvedScript'"
        $ServerReadyToLaunch = $true
        Write-Host "      [OK] Server start strategy: Script ('$ResolvedScript')" -ForegroundColor Green
    } else {
        $ResolvedJar = if ($ServerJar -ne "") {
            if (Test-Path (Join-Path $PaperServerDir $ServerJar)) {
                $ServerJar
            } elseif (Test-Path $ServerJar) {
                $ServerJar
            } else {
                $null
            }
        } else {
            $Jars = Get-ChildItem -Path $PaperServerDir -Filter "*.jar" | Where-Object { $_.Name -match "paper|server" }
            if ($Jars) {
                $Jars[0].Name
            } else {
                $null
            }
        }

        if ($ResolvedJar) {
            $ServerLaunchCommand = "cd '$PaperServerDir'; java -Xms2G -Xmx4G -jar '$ResolvedJar' --nogui"
            $ServerReadyToLaunch = $true
            Write-Host "      [OK] Server start strategy: Java JAR ('$ResolvedJar')" -ForegroundColor Green
        } else {
            Write-Host "      [WARNING] Could not detect a startup script or Paper server JAR in '$PaperServerDir'." -ForegroundColor Yellow
            Write-Host "                Define -StartScript (or `$env:MCP_PAPER_START_SCRIPT) or -ServerJar (or `$env:MCP_PAPER_SERVER_JAR)." -ForegroundColor Yellow
        }
    }
} elseif ($PaperServerDir -ne "") {
    Write-Host "      [WARNING] Specified PaperServerDir '$PaperServerDir' does not exist." -ForegroundColor Yellow
} else {
    Write-Host "      [INFO] MCP_PAPER_SERVER_DIR not set. Plugin built but no target Paper server linked." -ForegroundColor Gray
    Write-Host "             Tip: Set `$env:MCP_PAPER_SERVER_DIR = 'C:\path\to\paper-server' to auto-deploy and launch." -ForegroundColor Gray
}

if ($Mode -eq "build-jar") {
    Write-Host "`n[OK] JAR build complete." -ForegroundColor Green
    exit 0
}

# 4. Check Backend setup
Write-Host "`n[2/4] Verifying Backend Environment..." -ForegroundColor Cyan
$BackendDir = if (Test-Path "$RootDir\..\CraftLab-backend") { "$RootDir\..\CraftLab-backend" } else { "$RootDir\..\backend" }
$BackendVenv = "$BackendDir\.venv\Scripts\python.exe"
if (-not (Test-Path $BackendVenv)) {
    Write-Host "      Creating Python venv..." -ForegroundColor Gray
    python -m venv "$BackendDir\.venv"
    & "$BackendDir\.venv\Scripts\pip.exe" install -r "$BackendDir\requirements.txt" -q
}
Write-Host "      [OK] Backend environment ready." -ForegroundColor Green

# 5. Check Frontend setup
Write-Host "`n[3/4] Verifying Frontend Environment..." -ForegroundColor Cyan
$FrontendDir = if (Test-Path "$RootDir\..\CraftLab-frontend") { "$RootDir\..\CraftLab-frontend" } else { "$RootDir\..\frontend" }
if (-not (Test-Path "$FrontendDir\node_modules")) {
    Write-Host "      Installing frontend node_modules..." -ForegroundColor Gray
    Push-Location $FrontendDir
    npm install --silent
    Pop-Location
}
Write-Host "      [OK] Frontend environment ready." -ForegroundColor Green

# 6. Launch Services
Write-Host "`n[4/4] Starting Local Runtime Services ($Mode mode)..." -ForegroundColor Cyan

# A. Start Backend (if Mode in "all", "web-only")
if ($Mode -in @("all", "web-only")) {
    Write-Host "      Starting FastAPI Backend & WebSocket Gateway on port 8000..." -ForegroundColor Gray
    $BackendCmd = "cd '$BackendDir'; .\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle='MCP - Backend & Gateway'; $BackendCmd"
    Start-Sleep -Seconds 2
}

# B. Start Frontend (if Mode in "all", "web-only")
if ($Mode -in @("all", "web-only")) {
    Write-Host "      Starting React + Vite Frontend on port 3000..." -ForegroundColor Gray
    $FrontendCmd = "cd '$FrontendDir'; npm run dev"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle='MCP - Frontend Web UI'; $FrontendCmd"
    Start-Sleep -Seconds 2
}

# C. Start Paper 1.21 Server (if Mode in "all", "server-only" and server ready)
if ($Mode -in @("all", "server-only") -and $ServerReadyToLaunch) {
    Write-Host "      Starting Paper 1.21 Server in dedicated console..." -ForegroundColor Gray
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle='MCP - Paper 1.21 Server'; $ServerLaunchCommand"
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "             ALL SYSTEMS RUNNING LOCALLY!                 " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  * Web Editor Dashboard : http://localhost:3000" -ForegroundColor White
Write-Host "  * REST API & Docs      : http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "  * Agent Gateway (WS)   : ws://127.0.0.1:8000/ws/agent" -ForegroundColor White
if ($ServerReadyToLaunch) {
    Write-Host "  * Paper Server Console : Running in 'MCP - Paper 1.21 Server' window" -ForegroundColor Green
} else {
    Write-Host "  * Target Server Status : Awaiting Paper server connection" -ForegroundColor Yellow
}
Write-Host "  * Compiled Plugin JAR  : paper-agent\build\libs\paper-agent-1.0.0-SNAPSHOT.jar" -ForegroundColor White
Write-Host ""
Write-Host "To stop dev processes later, run: .\dev.ps1 -Mode stop" -ForegroundColor Yellow
Write-Host ""

# Optional: open browser
if (-not $NoBrowser -and $Mode -in @("all", "web-only")) {
    try {
        Start-Process "http://localhost:3000"
    } catch {
    }
}
