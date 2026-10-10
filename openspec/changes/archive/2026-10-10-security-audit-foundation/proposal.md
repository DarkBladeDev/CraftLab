# Proposal: security-audit-foundation

## Why

CraftLab comprises distinct services across FastAPI, the WebSocket Gateway, and the `craftctld` supervisor daemon that can run across isolated processes or hosts. Currently, the platform lacks a unified security audit trail, uses insecure defaults in configuration templates (`.env.example`), permits unauthenticated agent registration on `/ws/agent`, allows `caller_id` spoofing in supervisor actions, and exposes session tokens and cookies to leakage. Establishing a zero-trust security audit baseline and remediating verified vulnerability vectors is essential before any public or production deployment.

## What Changes

- **Security & Audit Foundation Package (`craftlab_security`)**: Introduce a canonical, dependency-light Python contract for versioned security events (`schema_version: 1`), structured actor extraction from transport, and strict pre-persistence sanitization (redacting passwords, tokens, API keys, and session cookies).
- **Dedicated SQLite Audit Persistence**: Establish isolated SQLite storage at `data/security-audit.sqlite3` with WAL mode, optimized query indexes, and dual-path ingestion (fail-closed synchronous write for sensitive administrative actions, bounded asynchronous batching for high-volume network telemetry).
- **Hardened Production Defaults & Fail-Safe Boot**: Require production startup to abort loudly if `CRAFTLAB_AUTH_ENABLED` is false or if `CRAFTLAB_ROOT_KEY` matches default placeholder values.
- **Transport & Web Security Hardening**:
  - Restrict supervisor `craftctld` CORS origins to explicit domains, eliminating wildcards with credentials.
  - Enforce `Secure`, `HttpOnly`, and `SameSite` flags on session cookies in production.
  - Eliminate query-string token authentication on supervisor WebSocket endpoints.
- **Verified Identity in Supervisor Daemon**: Derive `caller_id` strictly from authenticated transport context (verified web session or IPC socket identity), ignoring untrusted client payload values.
- **WebSocket Agent Handshake Authentication**: Enforce pre-registration secret verification in `/ws/agent` during the `hello` message exchange, rejecting unauthorized connections and preventing agent identity spoofing.

## Capabilities

### New Capabilities
- `security-audit`: Canonical security event contract, sanitization rules, and isolated SQLite audit logging with dual-path write persistence.

### Modified Capabilities
- `identity-access-management`: Enforce strict production boot validation (rejecting default secrets/unauthenticated mode), eliminate wildcard CORS credentials, mandate `Secure` session cookies, and eliminate query-string token exposure.
- `agent-protocol`: Mandate target secret authentication during the initial WebSocket handshake before registering agent sessions.

## Impact

- **Backend**: `CraftLab-backend/main.py`, `app/gateway/manager.py`, and `app/core/config.py`.
- **Supervisor**: `CraftLab-ctl/src/craftlab_ctl/daemon.py`, `server/app.py`, and `core/audit.py`.
- **Shared**: Introduction of `craftlab_security` module / package and `data/security-audit.sqlite3`.
- **Configuration**: Hardening checks in `.env.example` and environment loader validation.
