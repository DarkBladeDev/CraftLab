# Tasks

## 1. Core Security Package (`craftlab_security`)

- [x] 1.1 Implement canonical event schema models with Pydantic v2 in `craftlab_security.models` and verify model validation tests pass
- [x] 1.2 Implement universal data sanitizer in `craftlab_security.sanitizer` with denylist redaction and length/depth truncation, and verify unit tests cover all sensitive keys
- [x] 1.3 Implement SQLite persistence sink in `craftlab_security.sink` supporting WAL mode, dual-path write (fail-closed synchronous and async batched queue), and retention purge, verifying database write tests pass

## 2. Supervisor Daemon and Server Hardening (`CraftLab-ctl`)

- [x] 2.1 Add fail-fast production environment validation checking for disabled auth or placeholder root secrets, and verify boot abort test on default tokens
- [x] 2.2 Configure explicit CORS origin allowlist in `CraftLab-ctl/src/craftlab_ctl/server/app.py` disallowing wildcard origins with credentials, and verify CORS preflight tests
- [x] 2.3 Enforce `Secure` cookie flags in production and eliminate query string token authentication from `/api/v1/ws/logs`, verifying cookie and WebSocket handshake tests
- [x] 2.4 Refactor `DaemonService.handle_action` in `daemon.py` to derive `caller_id` strictly from authenticated transport context and emit sanitized audit events, verifying caller spoofing attempts are discarded

## 3. WebSocket Gateway and Backend Hardening (`CraftLab-backend`)

- [x] 3.1 Implement target secret verification during `hello` handshake in `app/gateway/manager.py` before session registration, verifying unauthenticated agents are rejected with code 1008
- [x] 3.2 Instrument FastAPI endpoints and gateway disconnects with `craftlab_security` to emit canonical authentication and administrative events, verifying event ingestion in SQLite

## 4. End-to-End Verification

- [x] 4.1 Run full backend test suite (`pytest`) and supervisor test suite, verifying all tests pass and `security-audit.sqlite3` records expected events
