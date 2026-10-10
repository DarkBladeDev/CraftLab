---
title: craftlab_security Package
description: Canonical security event contract, universal data sanitization, and WAL SQLite audit sink.
sidebar:
  order: 2
  label: craftlab_security
---

# craftlab_security Package

`craftlab_security` is the central security and audit library for the CraftLab monorepo, providing:
1. A **canonical security and audit event contract** shared across FastAPI backend, WebSocket Gateway, and supervisor daemon `craftctld`.
2. A **universal pre-persistence data sanitizer** that eliminates credential leaks and mitigates payload injection and buffer overflow vectors.
3. An **isolated SQLite audit persistence sink (`security-audit.sqlite3`)** operating in WAL mode with dual-path write strategies (synchronous fail-closed for critical events, asynchronous in-memory batch queuing for high-throughput telemetry).
4. A **fail-fast production environment validator** that halts application boot if insecure configurations, disabled authentication, or placeholder root tokens are detected.

---

## Technical Specifications

- **Location:** [`packages/craftlab_security`](https://github.com/DarkBladeDev/CraftLab/tree/main/packages/craftlab_security)
- **Version:** `0.1.0`
- **Type:** Internal shared library (Python 3.11+)
- **Dependencies:** `pydantic >= 2.0.0`

---

## Subsystems & Architecture

### 1. Canonical Event Schema (`models.py`)

Defines Pydantic v2 data models for structured security events.

#### Stable Enumerations
- `Component`: `backend`, `websocket_gateway`, `daemon`
- `EventType`:
  - `HTTP_REQUEST`: `http.request`
  - `AUTH_FAILURE`: `auth.failure`
  - `AUTHZ_DENIED`: `authz.denied`
  - `API_ENUMERATION_DETECTED`: `api.enumeration.detected`
  - `WEBSOCKET_AUTH_FAILURE`: `websocket.auth.failure`
  - `WEBSOCKET_LIMIT_EXCEEDED`: `websocket.limit.exceeded`
  - `WEBSOCKET_CONNECTED`: `websocket.connected`
  - `WEBSOCKET_DISCONNECTED`: `websocket.disconnected`
  - `ADMIN_ACTION`: `admin.action`
  - `DAEMON_OPERATION_FAILED`: `daemon.operation.failed`
  - `SECURITY_ALERT`: `security.alert`
- `Severity`: `INFO`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
- `Outcome`: `SUCCESS`, `DENIED`, `FAILED`, `UNKNOWN`
- `ActorType`: `ANONYMOUS`, `USER`, `AGENT`, `SYSTEM`, `UNKNOWN`
- `TransportType`: `HTTP`, `WS`, `IPC`, `INTERNAL`, `UNKNOWN`

#### Event Model: `SecurityEvent`
Normalized fields:
- `schema_version`: Integer schema version (`1`).
- `event_id`: Unique UUIDv4 generated at point of emission.
- `occurred_at`: UTC timestamp formatted in ISO 8601.
- `component`: Emitting subsystem (`Component`).
- `event_type`: Normalized event classification (`EventType`).
- `severity`: Severity classification (`Severity`).
- `outcome`: Operation result (`Outcome`).
- `actor`: Verified actor identity (`ActorContext(type, id, roles)`).
- `source`: Transport origin metadata (`SourceContext(ip, transport, user_agent)`).
- `request`: Transport request context (`RequestContext(request_id, method, route, status_code)`).
- `target`: Impacted resource entity (`TargetContext(type, id)`).
- `reason_code`: Alphanumeric reason classifier (e.g. `invalid_credentials`, `target_secret_mismatch`).
- `duration_ms`: Optional execution duration in milliseconds.
- `attributes`: Extensible dictionary for sanitized contextual key-values.

---

### 2. Universal Data Sanitizer (`sanitizer.py`)

Guarantees that sensitive data, credentials, and excessive payloads are scrubbed prior to persistence or logging.

#### Sanitization Policies:
1. **Denylist Redaction:**
   - Detects keys matching: `password`, `token`, `secret`, `authorization`, `cookie`, `session`, `credential`, `key`, `access_token`, `refresh_token`, `api_key`, `private_key`.
   - Irreversibly replaces sensitive values with `[REDACTED]`.
2. **String Truncation:**
   - Any attribute string exceeding 512 characters is truncated and marked with `...[TRUNCATED]`.
3. **Nesting Depth Pruning:**
   - Nested dictionary/list depth is constrained to 3 levels; deeper structures are pruned with `[NESTING_TRUNCATED]` to prevent resource exhaustion.
4. **Query String Stripping:**
   - Normalized HTTP request paths automatically strip query strings (e.g. `/api/v1/ws/logs?token=xyz` is scrubbed to `/api/v1/ws/logs`).

---

### 3. SQLite Persistence Sink (`sink.py`)

Stores audit events into an isolated SQLite database file (`data/security-audit.sqlite3`).

#### Design Highlights:
- **Dedicated Database File:** Independent from `mcp.db` (content data) and `auth.db` (user credentials).
- **WAL Journaling:** `PRAGMA journal_mode = WAL` enables concurrent readers without locking writer transactions.
- **Dual-Path Ingestion:**
  - `emit_critical(event)`: Synchronous, fail-closed write path for authentication failures, authorization denials, and administrative mutations.
  - `emit_telemetry(event)`: Asynchronous, memory-bounded queuing (`queue.Queue` of 5,000 items) flushed in batches of 50 items or every 2 seconds for high-frequency connection telemetry.
- **Automated Retention Purge:** `purge_old_events(retention_days=90)` removes records beyond the compliance window.
- **Windows File Handle Safety:** Uses explicit connection closing via context manager `@contextmanager def _connection()` to prevent `WinError 32` file locking errors on Windows environments.
- **Filtered Queries:** `query_events(component, event_type, outcome, actor_id, limit, offset)` backed by composite indices on `occurred_at`, `component`, `event_type`, and `actor_id`.

---

### 4. Production Fail-Fast Validation (`validation.py`)

Enforces secure boot policies in production deployments.

Function: `validate_production_security_environment()`
- Checks environment variables `CRAFTLAB_ENV` or `ENV`.
- When set to `production` or `prod`:
  1. **Disabled Authentication:** Raises `SecurityConfigurationError` if `CRAFTLAB_AUTH_ENABLED == "false"`.
  2. **Default Placeholder Root Tokens:** Raises `SecurityConfigurationError` if `CRAFTLAB_ROOT_TOKEN` equals default placeholder values (`change_me_to_a_secure_root_token`, `root-token`, `admin`, etc.).
- When in `development` or `test`: logs security warnings without halting execution.

---

## Monorepo Integration

### 1. `CraftLab-backend`
- **Boot Lifecycle:** Invokes `validate_production_security_environment()` during FastAPI startup in `main.py`.
- **FastAPI Endpoint Audit:** Shared helper `app.core.security.emit_audit_event()` emits events for login failures (`auth.failure`), administrative operations (`admin.action`), and permission rejections (`authz.denied`).
- **WebSocket Gateway:** `app.gateway.manager.AgentSessionManager` enforces cryptographic secret validation on agent `hello` handshakes via constant-time `secrets.compare_digest`, rejecting invalid agents with code 1008 and recording `websocket.auth.failure`.

### 2. `CraftLab-ctl`
- **Supervisor Boot:** Validates production environment configuration in `DaemonService.start()` and `server/app.py`.
- **Hardened CORS:** Disallows wildcard origins when credentials are enabled.
- **Secure Cookies:** Enforces `Secure=True` for session cookies on HTTPS deployments.
- **Log WebSocket:** Disallows query string credentials on `/api/v1/ws/logs`.
- **Authenticated Identity:** `DaemonService.handle_action` strictly derives caller identity from verified transport socket context (`ipc:{user}`).
- **Dual-Write Logging:** `AuditLogger` writes simultaneously to sanitized `audit.jsonl` and the canonical `SecurityAuditSink`.

---

## Code Examples

### Emitting a Critical Event
```python
from pathlib import Path
from craftlab_security import (
    SecurityAuditSink, SecurityEvent, Component, EventType,
    Severity, Outcome, ActorContext, ActorType, SourceContext, TransportType
)

sink = SecurityAuditSink(Path("data/security-audit.sqlite3"))

event = SecurityEvent(
    component=Component.BACKEND,
    event_type=EventType.AUTH_FAILURE,
    severity=Severity.HIGH,
    outcome=Outcome.DENIED,
    actor=ActorContext(type=ActorType.ANONYMOUS),
    source=SourceContext(ip="203.0.113.195", transport=TransportType.HTTP),
    reason_code="invalid_credentials",
    attributes={"attempted_username": "admin"},
)

sink.emit_critical(event)
```

### Universal Sanitization
```python
from craftlab_security import DataSanitizer

raw_attributes = {
    "username": "developer",
    "password": "SuperSecretPassword123!",
    "nested": {
        "api_key": "raw-secret-token",
        "description": "Standard action"
    }
}

clean_attributes = DataSanitizer.sanitize_dict(raw_attributes)
# clean_attributes["password"] == "[REDACTED]"
# clean_attributes["nested"]["api_key"] == "[REDACTED]"
```

---

## Unit Testing

Unit tests for `craftlab_security` reside under [`packages/craftlab_security/tests/`](https://github.com/DarkBladeDev/CraftLab/tree/main/packages/craftlab_security/tests):

```bash
pytest packages/craftlab_security/tests -v
```
