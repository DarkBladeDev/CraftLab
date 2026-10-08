---
title: Configuration Reference
description: Complete reference guide for CraftLab environment variables, craftlab.toml, and plugin settings.
sidebar:
  order: 7
---

# Configuration Reference

This page compiles all configuration options across the CraftLab platform, including environment variables (`.env`), daemon configuration (`config/craftlab.toml`), and plugin settings (`config.yml`).

---

## 1. Environment Variables (`.env`)

Used primarily by `CraftLab-backend` and deployment scripts:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `CRAFTLAB_HOST` | `127.0.0.1` | Network IP address to bind FastAPI backend and WebSocket gateway. |
| `CRAFTLAB_PORT` | `8000` | Port for the backend REST API and WebSocket gateway. |
| `CRAFTLAB_SECRET_KEY` | *(Random)* | Secret key used to sign and verify JWT authentication tokens. |
| `CRAFTLAB_GATEWAY_SECRET` | `dev-secret` | Shared secret token required by Paper game servers connecting to `/ws/agent`. |
| `CRAFTLAB_DB_PATH` | `data/mcp.db` | Relative or absolute path to the main SQLite database file. |
| `CRAFTLAB_PACKS_DIR` | `data/packs` | Directory storing raw assets, workspaces, and compiled `.zip` resource packs. |
| `MCP_PAPER_SERVER_DIR` | *(None)* | Optional local Paper server path used by `dev.ps1` for automatic JAR deployment. |
| `MCP_PAPER_START_SCRIPT` | *(Auto-detected)* | Optional script name (e.g. `run.bat` or `start.ps1`) to launch the local Paper server. |
| `MCP_PAPER_SERVER_JAR` | *(Auto-detected)* | Optional Paper server jar filename (e.g. `paper-1.21.1-118.jar`). |

---

## 2. Supervisor Configuration (`config/craftlab.toml`)

Used by `craftctl` and the `craftctld` supervisor daemon:

```toml
[platform]
name = "craftlab"
home_dir = "/opt/craftlab"
current_symlink = "current"

[server]
host = "0.0.0.0"
port = 8443
enable_tls = false

[services.backend]
enabled = true
command = "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
cwd = "backend"
health_endpoint = "http://127.0.0.1:8000/health"

[services.frontend]
enabled = true
serve_static = true
dist_dir = "frontend_dist"

[updates]
github_repo = "DarkBladeDev/CraftLab"
wheel_cache_dir = "cache/wheels"
releases_dir = "releases"
auto_rollback_on_failure = true
```

---

## 3. Paper Plugin Configuration (`plugins/McpAgent/config.yml`)

Located inside the Paper Minecraft server's `plugins/` directory:

```yaml
gateway:
  # WebSocket URL of the CraftLab backend
  url: "ws://127.0.0.1:8000/ws/agent"

  # Unique identifier for this game server instance
  targetId: "local-paper-server"

  # Secret key matching CRAFTLAB_GATEWAY_SECRET on backend
  secret: "dev-secret"

  # Reconnection backoff interval in seconds
  reconnect_delay_seconds: 5

props:
  # Render virtual display entity props via PacketEvents
  enable_packetevents: true

  # Allow players to sit on furniture props by right-clicking
  enable_sit_mechanic: true

packs:
  # Automatically prompt players upon joining the server
  prompt_on_join: true

  # Kick players if they decline a mandatory resource pack
  force_pack: false
```
