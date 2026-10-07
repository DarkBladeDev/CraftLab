# Design: CraftLab Runtime Foundation & Control System

## Context

See `proposal.md` for overall motivation.
CraftLab currently lacks an externalized configuration system, health check endpoints, and an extensible supervisor. Developers start the system via PowerShell scripts that terminate processes globally by name. To enable robust Linux VPS deployments under systemd while preserving local Windows development workflows, this design establishes the application runtime contract and implements the `CraftLab-ctl` package.

## Goals / Non-Goals

**Goals:**
- Provide a unified configuration layer for the backend (`craftlab.toml` + `CRAFTLAB_*` env vars).
- Implement standard `/health` and `/ready` HTTP probe endpoints on the backend.
- Create the standalone `CraftLab-ctl` module with Python package `craftlab_ctl` and `craftctl` executable.
- Implement `craftctld` process supervisor that tracks and manages child processes safely across Linux and Windows without killing unrelated processes.
- Implement an extensible plugin SDK supporting `@command`, `@hook`, and `@check` with dynamic CLI introspection.
- Provide built-in `lifecycle` (`start`, `stop`, `restart`, `status`) and `core` (`daemon`, `doctor`, `plugins`) commands.

**Non-Goals:**
- Full maintenance mode write-gating (deferred to Phase 2 `maintenance-mode`).
- Alembic database migrations and multi-database dialect abstraction (deferred to Phase 3 `portable-db-migrations`).
- Release packaging, tarball artifacts, and remote update pipeline (deferred to Phase 4 `release-artifacts-and-update`).
- Web admin UI panel (deferred to future v2 milestone).
- Direct supervision of the Minecraft Paper server (Paper remains a remote target managed exclusively via the agent adapter).

## Decisions

### 1. Module Layout and Package Identity
- **Choice**: The control system code resides in root directory `CraftLab-ctl/`, using standard `pyproject.toml` with package name `craftlab-ctl` and Python import package `craftlab_ctl`.
- **Rationale**: Keeps control tools independent from the web backend codebase. Consistent with the planned module renaming `CraftLab-{module}` across the repository.
- **Alternatives considered**:
  - Embedding control tools inside `backend/`: Rejected because the supervisor must run independently outside the backend process to survive backend restarts, updates, and crashes.

### 2. Dual-Layer Supervision Model (systemd + craftctld)
- **Choice**: `systemd` in production supervises `craftctld`. `craftctld` in turn supervises the backend process and any auxiliary workers. In local development, `craftctld` runs in the foreground or as a standalone local process.
- **Rationale**: Eliminates environment discrepancy. In both production and dev, `craftctl` interacts with the exact same daemon API and process supervision logic.

```
  Production (Linux VPS)            Local Dev (Windows / Linux)
  +--------------------+            +--------------------+
  |      systemd       |            |   Developer CLI    |
  +---------+----------+            +---------+----------+
            | (supervises)                    | (launches)
            v                                 v
  +------------------------------------------------------+
  |         craftctld (craftlab_ctl daemon)              |
  |  - Tracks child PIDs & process groups                |
  |  - Exposes local control IPC                         |
  |  - Hosts Plugin Registry & Operation Engine          |
  +---------------------------+--------------------------+
                              | (supervises)
                              v
  +------------------------------------------------------+
  |           CraftLab Backend (Uvicorn / FastAPI)        |
  |  - Reads craftlab.toml / CRAFTLAB_*                  |
  |  - Exposes /health & /ready probes                   |
  +------------------------------------------------------+
```

### 3. Local IPC Transport Abstraction
- **Choice**: On Linux, `craftctld` listens on a Unix domain socket at `<CRAFTLAB_HOME>/run/craftctld.sock` with file mode `0660` restricted to the `craftlab` group. On Windows, `craftctld` binds to loopback `127.0.0.1:<port>` with an auto-generated random token stored in `<CRAFTLAB_HOME>/run/craftctld.token` (restricted by file ACLs).
- **Rationale**: Unix sockets provide zero-network local IPC with OS-level user identity verification (`SO_PEERCRED`). Loopback with token files provides portable fallback on Windows without requiring named pipe native bindings.

### 4. Plugin SDK & Dynamic CLI Reflection
- **Choice**: Plugins are registered via Python entry points in `craftlab_ctl.plugins`.
- **Structure**:
  - `Plugin`: Base class with `name`, `sdk_version`, `setup()`, and optional pydantic config.
  - `@command(mutates=bool, danger=Danger, runs_in="daemon"|"local")`: Decorator registering subcommands. Arguments and types are introspected via Python type hints to generate JSON Schema definitions.
  - `@hook(event_name=str, priority=int)`: Event subscriber hook. `before_*` hooks can reject operations via `VetoException`.
  - `@check(check_id=str)`: Environmental health check returning `CheckResult(status=PASS|WARN|FAIL, message=str)`.
- **Dynamic CLI**: The `craftctl` client queries the daemon for available commands and schemas, generating Click/Typer subcommands dynamically at invocation.

### 5. Backend Configuration & Probe Endpoints
- **Choice**: Introduce `backend/app/core/config.py` using Pydantic Settings to parse `craftlab.toml` (via standard `tomllib`) and environment variables prefixed with `CRAFTLAB_`.
- **Endpoints**:
  - `GET /health`: Fast liveness check returning HTTP 200, uptime, and process ID.
  - `GET /ready`: Deep check querying database `SELECT 1` and verifying read/write accessibility of `packs/sources` and `packs/dist`.
- **Signal Handling**: In `backend/main.py`, catch `SIGTERM` and `SIGINT` to trigger FastAPI lifespan shutdown gracefully before closing database engines.

## Risks / Trade-offs

- **[Risk]**: Process termination behavior differs between Linux signals (`SIGTERM`) and Windows processes.
  - **Mitigation**: Use Python `psutil` or `asyncio.subprocess` process groups. On Windows, use `CTRL_BREAK_EVENT` followed by terminating the process tree if unhandled within the timeout.
- **[Risk]**: Dynamic CLI schema querying might incur latency on every CLI run.
  - **Mitigation**: Cache introspected command schemas locally in `<CRAFTLAB_HOME>/run/commands.cache.json` with cache invalidation on daemon restart.
- **[Risk]**: Path resolution discrepancies when `CRAFTLAB_HOME` is omitted.
  - **Mitigation**: Provide robust default path resolution: if `CRAFTLAB_HOME` is not set, resolve paths relative to the project root directory.

## Migration Plan

1. Implement `backend/app/core/config.py` and register `/health` and `/ready` in `backend/main.py`.
2. Scaffold `CraftLab-ctl/` with package configuration and dependencies.
3. Implement `craftlab_ctl.sdk`, daemon process supervisor, and IPC transport.
4. Implement `lifecycle` and `core` plugins (`start`, `stop`, `restart`, `status`, `daemon`, `doctor`).
5. Verify end-to-end operation locally using `craftctl` on Windows.
