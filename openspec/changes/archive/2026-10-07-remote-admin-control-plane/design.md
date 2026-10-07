# Design

## Context

CraftLab currently operates with a local supervisor daemon (`craftctld`) communicating over Unix sockets (Linux) or local loopback TCP (Windows). Neither `craftctld` nor the main FastAPI application (`backend/`) has an authentication system or remote management interface. See `proposal.md` for motivation and context.

## Goals / Non-Goals

**Goals:**
- Provide an independent, robust HTTP and WebSocket control server inside `craftctld` that stays alive even when the supervised CraftLab process terminates.
- Build a dedicated, responsive Web Admin Dashboard in `CraftLab-ctl/web/` providing full lifecycle control, diagnostic probing, telemetry, and live log tailing.
- Implement a unified identity service with dedicated `data/auth.db` SQLite storage, Argon2id hashing, and RBAC (`admin`, `operator`, `creator`, `viewer`).
- Enable seamless Single Sign-On (SSO) across CraftLab App and `craftctld` via secure `HttpOnly` session cookies, while offering Bearer token authentication for `craftctl` CLI and CI/CD automation.
- Guarantee break-glass administrative recovery if the identity database becomes damaged or locked.

**Non-Goals:**
- OAuth2/OIDC third-party identity providers (e.g., Google/GitHub login) for this version.
- Distributed cluster multi-node orchestration (this design manages single-host VPS deployments).
- Direct remote administration of Minecraft Paper servers through `craftctld` (the Paper server continues to be managed exclusively via the existing Paper Agent gateway).

## Decisions

### Decision 1: Embedded Web Engine in `craftctld` (FastAPI + Uvicorn)
- **Choice**: Embed an ASGI FastAPI application running on Uvicorn inside `DaemonService` within `CraftLab-ctl`.
- **Rationale**: Reuses the FastAPI and Pydantic ecosystem already familiar to CraftLab contributors. Native support for typed schemas, asynchronous request lifecycles, and WebSockets.
- **Alternatives Considered**:
  - *Proxying via main CraftLab FastAPI*: Rejected because shutting down or upgrading the application would kill the control interface.
  - *Custom low-level asyncio HTTP server*: Rejected due to high implementation complexity and lack of battle-tested WebSocket and routing capabilities.

### Decision 2: Decoupled Web Admin Dashboard (`CraftLab-ctl/web/`)
- **Choice**: Structure the Admin Dashboard as a standalone Vite + React SPA inside `CraftLab-ctl/web/`, compiled into static assets served directly by `craftctld` via FastAPI `StaticFiles`.
- **Rationale**: Completely isolates the control UI from the main CraftLab application frontend. Even if the application frontend undergoes major breaking changes or failed releases, the supervisor console remains functional.
- **Alternatives Considered**:
  - *Hosting `/admin` routes in the main `frontend/`*: Rejected to avoid coupling the management interface with application deployments and rollbacks.

### Decision 3: Dedicated Identity Storage (`data/auth.db`)
- **Choice**: Store user accounts, role mappings, and password hashes in `data/auth.db`, completely separate from `data/mcp.db`.
- **Rationale**: Isolates authentication from content management. Operations such as restoring Minecraft packs, catalogs, or rollbacks of `data/mcp.db` will never revert passwords or delete user accounts.
- **Alternatives Considered**:
  - *Adding `users` table to `data/mcp.db`*: Rejected due to risk of credential loss or reversion during content backup restorations.

### Decision 4: Dual Authentication Model (HttpOnly Cookie + Bearer Token)
- **Choice**: Use HMAC-SHA256 signed session cookies (`HttpOnly`, `SameSite=Lax`, `Secure`) for browser access and `Authorization: Bearer <token>` for API/CLI access.
- **Rationale**:
  - Browsers automatically forward session cookies across HTTP requests and WebSockets (`new WebSocket('/api/v1/ws/logs')`), eliminating manual token passing.
  - Provides a familiar, frictionless login screen for non-programmer team members.
  - Bearer tokens allow automated scripts and `craftctl` CLI to authenticate cleanly.
- **Alternatives Considered**:
  - *Pure Bearer token in localStorage*: Vulnerable to XSS and requires complex WebSocket query parameter authentication workarounds.

### Decision 5: Real-time Log Streaming Multiplexer
- **Choice**: When `craftctld` starts the child process (`ProcessSupervisor`), capture stdout and stderr asynchronously via non-blocking pipes into an in-memory ring buffer (e.g. 1000 lines) and broadcast lines to connected `/api/v1/ws/logs` WebSocket subscribers.
- **Rationale**: Allows immediate visual feedback in the Web Admin Dashboard with backscroll history upon connecting.

### Decision 6: Break-Glass Root Administrative Credential
- **Choice**: Support an optional emergency root credential configured in `craftctl.toml` or `CRAFTLAB_ROOT_KEY`.
- **Rationale**: Ensures that system administrators can never be locked out of the supervisor, even if `data/auth.db` is corrupt or missing.

## Risks / Trade-offs

- **[Risk] Public exposure of supervisor port**: Exposing `craftctld` on public interfaces could attract unauthorized access attempts.
  - *Mitigation*: Enforce mandatory authentication on all non-static routes, rate limit login attempts in memory, and recommend running behind a TLS reverse proxy (Caddy/Nginx) or restricting IP allowlists.
- **[Risk] Memory overhead from log streaming**: High-volume log output could increase memory usage.
  - *Mitigation*: Cap the log ring buffer to a fixed size (e.g., 1000 lines or 5MB) and drop older lines when full.
- **[Risk] Database locking concurrency in SQLite**: Multiple processes reading/writing `data/auth.db`.
  - *Mitigation*: Configure SQLite in WAL (Write-Ahead Logging) mode with busy timeout for fast concurrent reads and writes.

## Migration Plan

1. **Schema Initialization**: Ensure both `craftctld` and `backend` call an idempotent `init_auth_db()` during startup.
2. **First-run Admin Bootstrapping**: If `data/auth.db` contains zero users and no break-glass key is set, `craftctld` logs an initial one-time setup token to stdout for web-based admin account creation.
3. **Backward Compatibility**: Local IPC transport (`run/craftctld.sock` / Windows loopback) remains supported for local `craftctl` commands without requiring manual credentials.
