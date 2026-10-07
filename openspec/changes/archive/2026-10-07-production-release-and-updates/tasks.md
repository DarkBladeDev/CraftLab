# Tasks

## 1. Release Packaging Automation

- [x] 1.1 Create `scripts/build_release.py` to compile frontend assets, package backend code, generate `manifest.json`, and produce `craftlab-v<version>.tar.gz` with its companion `.sha256` checksum file
- [x] 1.2 Add tests for archive packaging and manifest metadata schema validation

## 2. Canonical Paths and Release Resolution

- [x] 2.1 Update `CtlPaths` in `craftlab_ctl/core/paths.py` to add `releases_dir`, `cache_dir`, `wheels_dir`, and cross-platform active release pointer resolution
- [x] 2.2 Update `ProcessSupervisor` and `LifecyclePlugin` to launch backend from the active release virtual environment

## 3. Wheel Cache and Environment Provisioning

- [x] 3.1 Implement release virtual environment provisioning engine using `<CRAFTLAB_HOME>/cache/wheels` for fast cached package installation
- [x] 3.2 Add unit tests for venv creation and wheel cache resolution

## 4. Update Plugin Implementation

- [x] 4.1 Implement GitHub Releases HTTP client for release inspection, tag comparison, and asset downloading with SHA256 validation
- [x] 4.2 Implement `craftctl update prepare` command streaming real-time steps over `ctx.step`
- [x] 4.3 Implement `craftctl update apply` command with maintenance mode, graceful shutdown, migration hook, pointer swap, readiness polling, and automated rollback
- [x] 4.4 Implement `craftctl rollback` and release list / retention pruning (retaining latest 3 releases)
- [x] 4.5 Register `UpdatePlugin` in `CraftLab-ctl/pyproject.toml` entry points

## 5. Verification and Integration Tests

- [x] 5.1 Add integration tests covering `update check`, `prepare`, `apply`, simulated startup failure auto-rollback, and release pruning
- [x] 5.2 Run full test suite across `CraftLab-ctl` and verify all checks pass
