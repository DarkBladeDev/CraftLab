# Proposal

## Why

CraftLab currently relies on Windows-specific PowerShell developer scripts (`scripts/dev.ps1`) with fragile process termination (`Stop-Process -Force` by process name) and hardcoded paths and configurations, lacking production runtime support, process supervision, health probing, or an extensible operational control interface.
Now that the platform is moving toward Linux VPS production deployment with systemd while maintaining local development compatibility, we need a unified runtime foundation: a standardized application contract (configuration, canonical paths, health/readiness endpoints) and an extensible Python-based control system (`CraftLab-ctl` providing `craftctl` CLI and `craftctld` daemon).

## What Changes

- **External Configuration & Canonical Paths**: Provide unified application configuration loading via `craftlab.toml` and `CRAFTLAB_*` environment variables, standardizing runtime directory structure (`config/`, `data/`, `run/`, `logs/`) and resolving database and resource pack storage paths relative to configured roots rather than current working directory.
- **Application Health & Readiness Probes**: Add `/health` (liveness check) and `/ready` (dependency and database readiness check) REST endpoints to `backend/main.py` with graceful shutdown signal handling.
- **Control System Architecture (`CraftLab-ctl`)**:
  - Implement the `CraftLab-ctl` package (Python import `craftlab_ctl`) with entry-point-driven plugin architecture.
  - Implement `craftctld` process supervisor managing backend child processes via tracked PIDs, process groups, and graceful SIGTERM/CTRL_BREAK termination.
  - Implement lightweight local IPC (Unix domain socket on Linux with filesystem permissions and peer UID auditing; local loopback + security token on Windows).
  - Implement extensible Plugin SDK exposing `@command`, `@hook`, and `@check` decorators with schema generation from type hints.
  - Implement `craftctl` CLI reflecting daemon command schemas dynamically.
  - Provide built-in `lifecycle` plugin (`craftctl start`, `stop`, `restart`, `status`) and `core` commands (`craftctl daemon start|stop|status`, `craftctl doctor`, `craftctl plugins list`).

## Capabilities

### New Capabilities
- `runtime-contract`: Standardizes CraftLab application host configuration loading (`craftlab.toml`), canonical filesystem paths, health and readiness probe endpoints (`/health`, `/ready`), and graceful termination protocol.
- `control-system`: Provides the `craftctl` CLI and `craftctld` process supervisor daemon, local IPC transport, extensible plugin SDK (`@command`, `@hook`, `@check`), process lifecycle management (`start`, `stop`, `restart`, `status`), and environmental diagnostics (`doctor`).

### Modified Capabilities
<!-- None -->

## Impact

- **Backend**: `backend/main.py`, `backend/app/core/database.py`, and application entry points will adopt configuration-driven settings (`CRAFTLAB_*` / `craftlab.toml`) and expose `/health` and `/ready`.
- **New Module**: `CraftLab-ctl/` created with package `craftlab_ctl`, CLI entry points `craftctl` and `craftctld`, and built-in plugins.
- **Developer Workflows**: Developers and operators can launch, inspect, and stop CraftLab services locally and in production via `craftctl` rather than relying on brittle OS-level process killing.
- **Dependencies**: New dependencies for `CraftLab-ctl` (e.g. `click` / `typer`, `pydantic`, `tomli`/`tomllib`, `psutil`).
