# Design: Production Release Packaging and GitHub Updates

## Context

See `proposal.md` for background and motivation. CraftLab already defines canonical paths via `CtlPaths` (`config/`, `data/`, `run/`, `logs/`, `state/`), lifecycle probes (`/health`, `/ready`), and process supervision via `ProcessSupervisor` in `CraftLab-ctl`. Currently, `ProcessSupervisor` finds Python in `.venv` relative to the repository root.

This design extends `CtlPaths` and `ProcessSupervisor` to support versioned releases under `<CRAFTLAB_HOME>/releases/<version>/`, a shared wheel cache under `<CRAFTLAB_HOME>/cache/wheels`, and a dedicated `UpdatePlugin` managing two-phase updates and rollback.

## Goals / Non-Goals

**Goals:**
- Provide an automated build script generating hermetic release archives (`craftlab-v<version>.tar.gz`), metadata manifests, and SHA256 checksums.
- Implement `craftctl update check`, `prepare`, `apply`, `rollback`, and `list` subcommands streaming real-time progress steps.
- Isolate runtime virtual environments per release while reusing compiled wheels via `<CRAFTLAB_HOME>/cache/wheels` for sub-second offline provisioning.
- Guarantee zero downtime during the `prepare` phase and bounded downtime with automated rollback during the `apply` phase.
- Support cross-platform pointer resolution (`current` symlink on Linux; symlink or fallback `state/current_release.txt` on Windows).

**Non-Goals:**
- Compiling Python wheels or building frontend assets on production servers.
- Unattended background updates without operator or API invocation.
- Supporting arbitrary remote git repositories in production.

## Decisions

### Decision 1: Shared Wheel Cache Architecture (Option C)
- **Rationale**: Isolating `.venv` inside each release directory (`releases/<version>/.venv`) ensures that rollback to an earlier release never suffers from dependency contamination or half-installed packages. However, re-downloading or compiling wheels over the network during every release is slow and brittle.
- **Implementation**:
  - `craftctld` maintains `<CRAFTLAB_HOME>/cache/wheels`.
  - When `update prepare` provisions a new `.venv`, it invokes `pip install --no-index --find-links <wheels_dir> -r requirements.txt`.
  - For packages not present in the cache, `pip wheel -w <wheels_dir> -r requirements.txt` downloads and caches them once before installing.
- **Alternatives considered**:
  - *Single shared venv*: Rollback cannot guarantee that previously required packages remain intact if downgraded.
  - *Full offline vendoring in tarball*: Makes release archives huge (~150MB+), slowing download and CI uploads.

### Decision 2: Cross-Platform Release Pointer Resolution
- **Rationale**: On POSIX/Linux, swapping directory symlinks atomically using `ln -sfn ... current_tmp && mv -Tf current_tmp current` is instant and standard. On Windows, creating directory symlinks requires elevated administrator rights or Developer Mode.
- **Implementation**:
  - `CtlPaths` checks for a `current` symlink first. If creating a symlink fails with `OSError`, it writes the target version string into `<CRAFTLAB_HOME>/state/current_release.txt`.
  - In production mode, `paths.app_home` resolves to `releases/<version>/` (either dereferenced via symlink or resolved via `state/current_release.txt`). If neither exists, it falls back to development mode (`repo_root`).
- **Alternatives considered**:
  - *Directory junctions on Windows (`mklink /J`)*: Supported without admin privileges, but can have edge cases when moving across volumes or with certain file deletion operations. A lightweight pointer file provides deterministic cross-platform behavior.

### Decision 3: Two-Phase Update Lifecycle Flow
- **Rationale**: Downloading, extracting, and configuring packages takes the majority of update time. Splitting this out keeps downtime during `apply` strictly limited to service stop, database migration, pointer swap, and readiness probe (typically 2-4 seconds).
- **Implementation**:
  - `prepare <version>`:
    1. Query GitHub Releases API (or parse local tarball).
    2. Download `.tar.gz` and `.sha256` into `<CRAFTLAB_HOME>/cache/downloads/`.
    3. Verify SHA256 checksum.
    4. Extract into `releases/<version>/`.
    5. Validate `manifest.json`.
    6. Provision `releases/<version>/.venv` using wheel cache.
  - `apply <version>`:
    1. Verify release `<version>` is already prepared.
    2. Set maintenance mode active (`state/maintenance.json`).
    3. Gracefully stop current backend (`ProcessSupervisor.stop_process`).
    4. Execute database migrations (`alembic upgrade head` or db migration runner using release python).
    5. Atomically repoint `current` to `releases/<version>`.
    6. Start updated backend (`ProcessSupervisor.start_process`).
    7. Poll `GET /ready` until 200 OK or timeout.
    8. If ready: disable maintenance mode, write audit record, prune old releases.
    9. If failed: trigger automated rollback to prior release pointer, restart prior backend, record failure.

### Decision 4: GitHub Releases API Integration
- **Rationale**: Most deployments publish releases on GitHub.
- **Implementation**:
  - `craftctl update check` queries `https://api.github.com/repos/<owner>/<repo>/releases`.
  - Supports configuration in `craftlab.toml` under `[updates]`: `github_repo = "owner/repo"`.
  - Supports optional `GITHUB_TOKEN` environment variable or config setting to avoid unauthenticated API rate limits.

## Risks / Trade-offs

- **[Disk accumulation from releases]** → Mitigation: `RetentionManager` enforces keeping at most 3 releases. After each successful `apply`, older release directories and their `.venv` are deleted.
- **[Database migration incompatibility on rollback]** → Mitigation: Migrations that drop columns or perform destructive data mutations must be separated into multi-phase backwards-compatible migrations. In the event of a startup failure, rollback restores the previous application version, and the audit log records the migration state for operator review.
- **[Network outage during prepare]** → Mitigation: `prepare` is idempotent; failed downloads or partial extractions are cleaned up automatically without affecting the running service.

## Migration Plan

1. Existing development installations continue functioning without changes; when `releases/` is absent, `paths.app_home` defaults to repository root.
2. Production deployments initialize with `craftctl update prepare <v>` followed by `craftctl update apply <v>`.
