# Proposal: Production Release Packaging and GitHub Updates

## Why

CraftLab currently executes directly against a development workspace checkout, requiring developers to invoke local virtual environments, build tools, and live source trees. In a headless production deployment (such as a Linux VPS or dedicated server):
- Running `git pull` on production hosts exposes source control credentials, pulls unverified intermediate commits, and requires development toolchains on the host.
- Building the frontend SPA on production requires Node.js, `npm`, and heavy build dependencies that should not be present in production.
- Upgrading the application without a structured release mechanism risks breaking runtime state if dependency installation fails or if a new version fails to boot, with no automated rollback path.

## What Changes

Introduce an automated production release packaging pipeline and a two-phase atomic update system orchestrated by `craftctl`:

- **Release Packaging & Manifest**: Bundle backend code, precompiled frontend SPA (`frontend_dist`), database migrations, and a signed/checksummed `manifest.json` into a compressed distribution archive (`craftlab-v<version>.tar.gz`) alongside `.sha256` checksums.
- **GitHub Releases Integration**: Equip `craftctl update` with direct GitHub Releases API integration to discover releases, compare semantic versions, and download versioned artifacts.
- **Shared Wheel Cache Strategy (Option C)**: Isolate each release in `releases/<v>/.venv` while sharing wheels in `<CRAFTLAB_HOME>/cache/wheels` for sub-second, network-independent package installations and instant rollbacks.
- **Two-Phase Lifecycle Workflow**:
  - `craftctl update prepare <v>`: Non-disruptive download, extraction, and venv setup while the application continues serving traffic.
  - `craftctl update apply <v>`: Enters maintenance mode, stops backend gracefully, applies database migrations, atomically repoints `current` to the new release, starts backend, and tests `GET /ready`.
- **Automatic Rollback & Self-Healing**: Automatically reverts the release pointer to the previous version, restarts it, and raises diagnostics if `/ready` fails or times out.
- **Release Retention**: Automatically keeps the last 3 versions and prunes older releases to prevent disk bloat.

## Capabilities

### New Capabilities
<!-- None: update workflows extend existing host control capabilities -->

### Modified Capabilities
- `control-system`: Adds release management commands (`update check`, `update prepare`, `update apply`, `rollback`), release directory layout and pointer resolution, shared wheel caching, and maintenance mode controls to `craftctl` and `craftctld`.

## Impact
- **`CraftLab-ctl`**:
  - `craftlab_ctl.core.paths`: Adds `releases_dir`, `cache_dir`, `wheels_dir`, and pointer resolution logic (`current` symlink / pointer file).
  - `craftlab_ctl.plugins.update`: New plugin implementing update lifecycle commands, progress step streaming over WebSocket/CLI, and diagnostic checks.
  - `craftlab_ctl.plugins.lifecycle`: Updates process supervision to execute backend from the active release venv (`current/.venv`).
- **Release Automation**:
  - New release build script `scripts/build_release.py` generating `.tar.gz`, `manifest.json`, and `.sha256` checksums.
