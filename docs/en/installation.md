---
title: Installation & Getting Started
description: Prerequisites, developer quickstart, and production deployment guide for CraftLab.
sidebar:
  order: 2
---

# Installation & Getting Started

This guide details the prerequisites, local development workflow, and production deployment procedure for CraftLab.

---

## Prerequisites

Before setting up CraftLab, ensure the following software is installed on your host system:

| Component | Minimum Version | Notes |
| :--- | :--- | :--- |
| **Java Development Kit** | JDK 21 (Temurin or OpenJDK) | Required for `CraftLab-plugin` |
| **Python** | 3.11+ | Required for `CraftLab-backend` and `CraftLab-ctl` |
| **Node.js** | 20.x LTS | Required for Web Studio (`CraftLab-frontend`) and Control Web UI |
| **Paper Minecraft Server** | 1.21.1+ | Target game server runtime with Java 21 |
| **PacketEvents** | 2.14.0+ | Required dependency plugin installed on Paper server |

---

## Local Development Quickstart

The fastest way to spin up the complete platform locally is using the bundled PowerShell automation script:

```powershell
.\scripts\dev.ps1
```

### What `dev.ps1` executes automatically:
1. **Compiles the Paper Plugin**: Builds `CraftLab-plugin/build/libs/CraftLab-plugin-1.0.0-SNAPSHOT.jar` using Gradle.
2. **Initializes the Backend**: Validates Python dependencies in `CraftLab-backend\.venv` and ensures the database is initialized.
3. **Launches Backend & WebSocket Gateway**: Starts FastAPI at `http://127.0.0.1:8000`.
4. **Launches Frontend Web Studio**: Starts Vite development server at `http://localhost:3000`.
5. **Opens Web Studio in Browser**: Launches your default browser navigating to `http://localhost:3000`.

### Development Execution Modes

- **Web Services Only** (skip building or deploying plugin JAR):
  ```powershell
  .\scripts\dev.ps1 -Mode web-only
  ```

- **Auto-Deploy to Local Paper Server**:
  ```powershell
  .\scripts\dev.ps1 -PaperServerDir "C:\minecraft\paper-server"
  ```
  *Copies the compiled JAR to `C:\minecraft\paper-server\plugins`, generates default config if missing, and launches Paper in an interactive console.*

- **Clean Reset Environment** (wipes test database and cached packs):
  ```powershell
  .\scripts\dev.ps1 -CleanData
  ```

- **Stop Running Background Processes**:
  ```powershell
  .\scripts\dev.ps1 -Mode stop
  ```

---

## Production Deployment

In a production environment, CraftLab is deployed via official release packages (`craftlab-v<version>.tar.gz`) managed by the `craftctl` supervisor daemon.

### 1. Download & Extract Release

Download the desired release from [GitHub Releases](https://github.com/DarkBladeDev/CraftLab/releases):

```bash
mkdir -p /opt/craftlab
cd /opt/craftlab
tar -xzf craftlab-v0.3.3.tar.gz
```

### 2. Configure Environment

Copy `.env.example` to `.env` and configure your production secrets:

```bash
cp .env.example .env
nano .env
```

Ensure you customize:
- `CRAFTLAB_SECRET_KEY`: A strong random string for JWT authentication tokens.
- `CRAFTLAB_GATEWAY_SECRET`: Shared secret used by game servers connecting via WebSocket.
- `CRAFTLAB_HOST` / `CRAFTLAB_PORT`: Network interface binding (defaults to `127.0.0.1:8000`).

### 3. Initialize Control System (`craftctl`)

Install the companion supervisor wheel:

```bash
pip install craftlab_ctl-0.3.3-py3-none-any.whl
```

Run platform diagnostic to verify setup:

```bash
craftctl doctor
```

Start the platform daemon:

```bash
craftctl start
```

Verify service status:

```bash
craftctl status
```
