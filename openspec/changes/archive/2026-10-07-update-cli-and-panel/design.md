# Design: Update CLI Commands and Web Administration Panel Integration

## Context

See `proposal.md` for motivation.

`craftlab_ctl.plugins.update.UpdatePlugin` provides commands:
- `check`: Queries GitHub Releases API.
- `prepare`: Downloads, verifies SHA256 checksums, extracts `.tar.gz`, and provisions venv via wheel cache.
- `apply`: Puts app into maintenance mode, stops service, swaps pointer, runs readiness checks, auto-rolls back if failed, and prunes older releases.
- `rollback`: Reverts pointer to prior release and starts service.
- `releases`: Lists installed releases and active pointer.
- `maintenance`: Queries or toggles maintenance mode.

However, `DaemonService.setup()` only loads `LifecyclePlugin` and `CorePlugin` by default; `cli.py` has no `update` or `rollback` subcommands; and `app.py` has no `/api/v1/update/*` endpoints.

## Goals / Non-Goals

**Goals:**
- Provide full CLI interface for update operations under `craftctl update`, `craftctl rollback`, `craftctl releases`, and `craftctl maintenance`.
- Support both multi-step updates (`craftctl update prepare` + `craftctl update apply`) and an all-in-one shortcut command `craftctl update run <version>` / `craftctl update <version>`.
- Provide REST endpoints in FastAPI control plane under `/api/v1/update/*` with RBAC authorization and audit logging.
- Provide rich UI in the React SPA dashboard for checking updates, preparing releases, applying updates, rolling back, and toggling maintenance mode.
- Ensure CLI commands function both when `craftctld` is running (via local IPC or remote HTTPS) and in local standalone fallback mode.

**Non-Goals:**
- Creating new update protocols or altering the archive format (`craftlab-v<v>.tar.gz` and `.sha256` remain canonical).
- Automatically applying updates in the background without explicit operator initiation.

## Decisions

### 1. Dual CLI update workflows: granular phases and direct shortcut
- **Rationale**: Production environments benefit from staging updates ahead of maintenance windows (`prepare`), then applying them quickly (`apply`). For development, test, or simple deployments, a single command that runs both sequentially is much more convenient.
- **Implementation**:
  - `craftctl update check`: Queries GitHub.
  - `craftctl update prepare <v>`: Stages release.
  - `craftctl update apply <v>`: Applies staged release.
  - `craftctl update run <v>` / `craftctl update <v>`: Chains prepare and apply in sequence with confirmation.
  - Top-level `craftctl rollback [v]`: Direct rollback command.
  - Top-level `craftctl releases`: Release listing command.
  - Top-level `craftctl maintenance [enable|disable|status]`: Maintenance mode command.
- **Alternatives considered**: Only having two-phase subcommands was rejected based on user requirement for a direct shorthand update command.

### 2. Built-in daemon registration of `UpdatePlugin`
- **Rationale**: Relying solely on `importlib.metadata.entry_points()` can fail when running directly from uninstalled checkouts, dev virtual environments, or specific packaging setups. Core plugins (`LifecyclePlugin`, `CorePlugin`, `UpdatePlugin`) should always be explicitly registered during `DaemonService.setup()`.
- **Implementation**: Call `self.registry.register_plugin(UpdatePlugin())` in `DaemonService.setup()`.

### 3. REST endpoints and Remote Control Client
- **Rationale**: Both the web dashboard and remote CLI invocations (`craftctl --server ... --token ...`) interact with the supervisor daemon over HTTP.
- **Endpoints**:
  - `GET /api/v1/update/check` -> returns check result.
  - `GET /api/v1/update/releases` -> returns installed releases, active release, and maintenance state.
  - `POST /api/v1/update/prepare` -> body: `{ "version": str, "github_repo": Optional[str], "local_file": Optional[str] }`.
  - `POST /api/v1/update/apply` -> body: `{ "version": str, "timeout": int, "host": str, "port": int }`.
  - `POST /api/v1/update/rollback` -> body: `{ "target_version": Optional[str], "timeout": int }`.
  - `GET /api/v1/update/maintenance` & `POST /api/v1/update/maintenance` -> body: `{ "enable": bool, "message": str }`.
- **Authorization**:
  - GET operations allow all authenticated users (viewer, operator, admin).
  - POST operations require `admin` or `operator` role.
  - All mutating operations acquire `daemon_service.lock.acquire(...)` and append an entry to `daemon_service.audit.log`.

### 4. Interactive Dashboard UI Card
- **Rationale**: Administrators should have full visibility into running releases and be able to initiate update workflows without needing terminal access.
- **UI Structure**:
  - A new "Releases & Updates" Card in `Dashboard.tsx`:
    - Shows "Active Release": highlighted badge (`vX.Y.Z` or `dev`).
    - Shows "Maintenance Mode": colored badge with quick toggle button.
    - Shows "Installed Releases": list of versions on disk.
    - "Check for Updates" button: calls GitHub and displays banner with latest tag, release date, and whether an update is available.
    - If newer release or user enters version: "Prepare" button to stage without downtime, and "Apply" button to switch atomically.
    - "Rollback" button: dropdown/button to revert to any installed version with confirmation.
    - Feedback: action loading indicators, success/error banners, and execution logs visible in the live log stream.

## Risks / Trade-offs

- **[Risk] Long-running HTTP requests timing out during download/extraction**
  → *Mitigation*: Set appropriate timeout on remote client and FastAPI client requests (60s+), or use streaming step callbacks where supported.
- **[Risk] Accidental updates during peak traffic**
  → *Mitigation*: Both the CLI shorthand update command and the UI apply buttons will require explicit confirmation before stopping the service and swapping pointers.
- **[Risk] Concurrent mutations**
  → *Mitigation*: All update actions acquire the daemon's `OperationLock`, rejecting conflicting concurrent mutations with `409 Conflict` or lock error.
