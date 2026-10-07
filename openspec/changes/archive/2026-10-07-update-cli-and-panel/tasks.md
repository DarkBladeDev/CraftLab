# Tasks

## 1. Control Daemon & API Endpoints

- [x] 1.1 Explicitly register `UpdatePlugin` in `DaemonService.setup()` in `craftlab_ctl/daemon.py` and verify commands appear in plugin registry
- [x] 1.2 Implement `/api/v1/update/*` REST routes (`check`, `releases`, `prepare`, `apply`, `rollback`, `maintenance`) with RBAC and audit logging in `craftlab_ctl/server/app.py`
- [x] 1.3 Implement remote update methods on `RemoteControlClient` in `craftlab_ctl/transport/remote.py`

## 2. CLI Commands Integration

- [x] 2.1 Update command execution engine in `craftlab_ctl/cli.py` to dynamically execute update commands both via daemon and in direct local mode
- [x] 2.2 Add `craftctl update` command group with `check`, `prepare`, `apply`, and shorthand `craftctl update <version>`
- [x] 2.3 Add top-level `craftctl rollback`, `craftctl releases`, and `craftctl maintenance` commands to `craftlab_ctl/cli.py`
- [x] 2.4 Add unit tests for update, rollback, releases, and maintenance commands in `CraftLab-ctl/tests/test_cli.py`

## 3. Web Administration Dashboard UI

- [x] 3.1 Extend API client types and functions in `CraftLab-ctl/web/src/api.ts` for update checking, staging, applying, rollback, and maintenance
- [x] 3.2 Add Releases & Updates management card and action controls in `CraftLab-ctl/web/src/components/Dashboard.tsx`
- [x] 3.3 Compile frontend assets via `npm run build` and verify production bundle compiles cleanly

## 4. Verification and End-to-End Testing

- [x] 4.1 Add test cases covering update REST endpoints in `CraftLab-ctl/tests/test_server.py`
- [x] 4.2 Execute full test suite via `pytest CraftLab-ctl/tests` and verify all tests pass
