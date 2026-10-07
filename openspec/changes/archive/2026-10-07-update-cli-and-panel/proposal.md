# Proposal: Update CLI Commands and Web Administration Panel Integration

## Why

Although `craftlab_ctl.plugins.update` implemented the core logic for GitHub release downloads, SHA256 verification, wheel-cached virtual environment provisioning, and two-phase atomic pointer swaps with automated rollback, there are currently no CLI commands (`craftctl update`, `craftctl rollback`, `craftctl releases`, `craftctl maintenance`) exposed in `craftlab_ctl.cli`, nor are there corresponding HTTP control endpoints or user interface controls in the embedded web dashboard.

As a result, operators and system administrators cannot inspect or trigger updates from either the command line or the web console, preventing practical use of the newly introduced update system in production environments.

## What Changes

1. **CLI Commands Integration (`craftctl`)**:
   - Add `craftctl update` command group with:
     - `craftctl update check [--repo <owner/repo>]`: Check for new versions published on GitHub Releases.
     - `craftctl update prepare <version> [--file <archive_path>] [--repo <owner/repo>]`: Prepare and stage release environment non-disruptively.
     - `craftctl update apply <version> [--timeout <seconds>] [--host <host>] [--port <port>]`: Atomically switch active release with auto-rollback.
     - Shorthand execution: `craftctl update <version>` (executes `prepare` followed by `apply` in sequence with operator confirmation).
   - Add top-level `craftctl rollback [target_version]`: Revert active release pointer to a prior installed release.
   - Add top-level `craftctl releases`: List all locally installed releases, active release pointer, and maintenance state.
   - Add top-level `craftctl maintenance [enable|disable|status] [--message <msg>]`: Inspect or toggle application maintenance mode.
   - Support both daemon-mediated execution (`craftctld` via IPC/HTTP) and fallback direct execution when the daemon is not running.

2. **Control Server REST API Endpoints**:
   - `GET /api/v1/update/check`: Check for newer releases on GitHub.
   - `GET /api/v1/update/releases`: List installed releases, active release version, and maintenance status.
   - `POST /api/v1/update/prepare`: Download, verify checksum, extract, and provision release venv.
   - `POST /api/v1/update/apply`: Atomically apply prepared release with maintenance mode and automated rollback.
   - `POST /api/v1/update/rollback`: Revert to a specified or previous installed release.
   - `GET /api/v1/update/maintenance` & `POST /api/v1/update/maintenance`: Query or toggle maintenance mode.
   - All mutating endpoints enforce RBAC (`admin` / `operator` roles), acquire the daemon operation lock, and write structured records to the audit log.

3. **Daemon Built-in Plugin Registration**:
   - Explicitly register `UpdatePlugin` inside `DaemonService.setup()` alongside `LifecyclePlugin` and `CorePlugin` so that commands and checks are always available regardless of entry point discovery state.

4. **Web Administration Dashboard UI**:
   - Add a dedicated **Releases & Updates** section / card to `Dashboard.tsx`:
     - Active release version badge and installed release versions list.
     - Maintenance status banner/indicator with toggle capability for operators.
     - "Check for Updates" button showing GitHub release info and update availability.
     - "Prepare Release" and "Apply Update" actions with progress feedback and confirmation modals/prompts.
     - "Rollback" action with selection of available prior releases.
   - Extend `api.ts` with typed methods for all update and maintenance API endpoints.

## Capabilities

### New Capabilities
<!-- None: update workflows extend existing host control capabilities -->

### Modified Capabilities
- `control-system`: Updates requirements for CLI command registration, remote control endpoints, and dashboard interface controls for application update lifecycle and release management.

## Impact
- **`CraftLab-ctl` Core & Daemon**:
  - `craftlab_ctl/daemon.py`: Explicitly registers `UpdatePlugin`.
  - `craftlab_ctl/server/app.py`: Adds `/api/v1/update/*` REST routes with RBAC.
  - `craftlab_ctl/cli.py`: Adds `update`, `rollback`, `releases`, and `maintenance` commands with direct and remote execution.
  - `craftlab_ctl/transport/remote.py`: Adds remote client methods for update operations.
- **`CraftLab-ctl` Web UI**:
  - `web/src/api.ts`: Adds update client models and API calls.
  - `web/src/components/Dashboard.tsx`: Adds Releases & Updates dashboard card and interactive update controls.
