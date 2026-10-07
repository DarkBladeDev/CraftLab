# Tasks

## 1. Identity & Access Management Core

- [x] 1.1 Implement `data/auth.db` SQLite schema initialization (users, roles, sessions) and verify table creation with unit tests.
- [x] 1.2 Implement Argon2id password hashing and constant-time verification utilities and verify hashing/verification test suite.
- [x] 1.3 Implement cryptographic session cookie generation (HttpOnly, SameSite=Lax) and Bearer token parsing and verify token validation tests.
- [x] 1.4 Implement RBAC role permission evaluator (`admin`, `operator`, `creator`, `viewer`) and break-glass root credential handling and verify access control unit tests.

## 2. Supervisor Web Gateway & Remote Daemon

- [x] 2.1 Add `fastapi` and `uvicorn` dependencies to `CraftLab-ctl/pyproject.toml` and verify dependency installation.
- [x] 2.2 Implement embedded FastAPI server within `DaemonService` with auth middleware and `/api/v1/status`, `/api/v1/lifecycle/{action}`, `/api/v1/doctor` endpoints and verify endpoints with `TestClient`.
- [x] 2.3 Implement system telemetry endpoint `/api/v1/metrics` using `psutil` (host CPU/RAM/Disk, child process CPU/RSS) and verify JSON response schema.
- [x] 2.4 Implement child process log ring buffer in `ProcessSupervisor` and WebSocket streaming endpoint `/api/v1/ws/logs` and verify streaming log lines test.
- [x] 2.5 Extend `craftctl` CLI with `--server` and `--token` flags for remote daemon execution and verify remote command invocation.

## 3. Web Admin Dashboard Frontend

- [x] 3.1 Initialize Vite + React frontend project in `CraftLab-ctl/web/` with build scripts and output directory configuration.
- [x] 3.2 Implement Dashboard Login view submitting credentials to `/api/v1/auth/login` and handling session errors.
- [x] 3.3 Implement Dashboard overview views: Process Lifecycle controls, live resource gauges, Doctor diagnostics, and auto-scrolling WebSocket log viewer.
- [x] 3.4 Mount static build output in `craftctld` FastAPI server with SPA client-side route fallback and verify static file serving.

## 4. Main Application Auth & Single Sign-On Integration

- [x] 4.1 Implement shared `data/auth.db` session verification dependency in `backend/` and verify authenticated request handling with test client.
- [x] 4.2 Guard `backend/app/api/` endpoints with RBAC requiring `creator` or `admin` roles and verify 401/403 rejection tests for unauthenticated/unauthorized callers.
- [x] 4.3 Add session login/user indicator in `frontend/` leveraging the shared SSO session cookie.

## 5. Verification & Diagnostics

- [x] 5.1 Implement a `@check` diagnostic in `craftctl doctor` validating `data/auth.db` availability and supervisor web port binding.
- [x] 5.2 Execute test suite across `CraftLab-ctl` and `backend` verifying all unit, integration, and security tests pass.
