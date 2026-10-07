# Tasks

## 1. Backend Runtime Contract & Probes

- [x] 1.1 Implement `backend/app/core/config.py` loading `craftlab.toml`, `CRAFTLAB_*` environment variables, and canonical layout paths (`config/`, `data/`, `run/`, `logs/`); verify configuration loading with unit test.
- [x] 1.2 Update `backend/app/core/database.py` and pack asset paths to resolve database and packs directory from configured paths rather than current working directory; verify path resolution with test.
- [x] 1.3 Implement unauthenticated `GET /health` and `GET /ready` probe endpoints in `backend/main.py`; verify responses with pytest using FastAPI TestClient.
- [x] 1.4 Add OS signal handling (`SIGTERM` / `SIGINT`) in `backend/main.py` lifespan to cleanly close WebSocket sessions and database connections; verify graceful shutdown flow.

## 2. Control System Package & Foundation

- [x] 2.1 Scaffold `CraftLab-ctl/` with `pyproject.toml`, dependencies (`click`, `pydantic`, `psutil`), and package entry points `craftctl` and `craftctld`; verify package installation in development mode.
- [x] 2.2 Implement core domain types and audit logging in `craftlab_ctl.core` (`state/audit.jsonl` writer, operation locking, canonical paths); verify with unit tests.
- [x] 2.3 Implement local IPC transport in `craftlab_ctl.transport` supporting Unix Domain Sockets on Linux and local loopback with token file on Windows; verify bidirectional communication with unit test.

## 3. Extensible Plugin SDK

- [x] 3.1 Implement `Plugin` base class, `@command`, `@hook`, and `@check` decorators in `craftlab_ctl.sdk` with type-hint schema introspection; verify command schema generation with unit test.
- [x] 3.2 Implement plugin loader discovering `craftlab_ctl.plugins` entry points, version validation, and hook event dispatch with veto support; verify plugin registration with unit test.

## 4. Supervisor Engine & Built-in Plugins

- [x] 4.1 Implement `ProcessSupervisor` in `craftlab_ctl.supervisor` tracking child PIDs, managing process groups, and handling graceful stop escalation; verify process lifecycle with unit test.
- [x] 4.2 Implement `lifecycle` plugin providing `start`, `stop`, `restart`, and `status` commands supervising the backend process and waiting on `/ready`; verify lifecycle commands with unit test.
- [x] 4.3 Implement `core` plugin providing `daemon` control, `plugins list`, and `doctor` environmental diagnostics; verify check execution with unit test.

## 5. CLI Client & End-to-End Verification

- [x] 5.1 Implement dynamic `craftctl` CLI client querying daemon schemas and formatting streamed operation step events; verify CLI command parsing with unit test.
- [x] 5.2 Execute end-to-end integration test running `craftctld`, starting backend via `craftctl start`, verifying `craftctl status` and `craftctl doctor`, and stopping via `craftctl stop`.
