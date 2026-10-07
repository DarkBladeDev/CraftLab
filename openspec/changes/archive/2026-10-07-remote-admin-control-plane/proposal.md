# Proposal

## Why

Operating CraftLab in remote environments (such as a Linux VPS) currently requires direct local shell access or terminal tools, while non-programmer team members (3D modelers, texture artists, server operators) lack an intuitive, safe way to monitor system health, view live logs, and manage application lifecycles. Furthermore, neither the supervisor daemon (`craftctld`) nor the primary CraftLab application currently enforces user authentication or access control, leaving services unprotected when exposed to a network.

Introducing an autonomous remote control plane with an embedded Web Admin Dashboard and a unified, multi-user authentication system (SSO + RBAC) allows non-technical team members to securely access system management without terminal friction, protects the platform over public networks, and ensures supervisory control remains functional even when the main application is offline.

## What Changes

- **Embedded Web Engine in `craftctld`**: Add a FastAPI and Uvicorn HTTP/WebSocket server directly into the supervisor daemon, operating independently of the main CraftLab application.
- **Remote Web Admin Dashboard (`CraftLab-ctl/web/`)**: Build an isolated React/Vite single-page application hosted and served directly by `craftctld` for process lifecycle control, live stdout/stderr log tailing, diagnostic probing, and system metrics.
- **Dedicated Identity Database (`data/auth.db`)**: Implement a decoupled SQLite identity database for user accounts, role definitions, and salted Argon2id password hashes, ensuring content backups or rollbacks of `data/mcp.db` never overwrite credentials.
- **Unified Single Sign-On (SSO) & Dual Auth**: Implement `HttpOnly`, `SameSite=Lax` secure session cookies for seamless browser access across both CraftLab App and `craftctld`, alongside `Authorization: Bearer <token>` support for `craftctl` CLI and CI/CD automation.
- **Role-Based Access Control (RBAC)**: Define clear privilege boundaries (`admin`, `operator`, `creator`, `viewer`), restricting supervisor and server management actions to authorized operational staff.
- **Break-Glass Emergency Recovery**: Provide a bootstrap administrative override credential via configuration/environment to guarantee recovery if the user database is inaccessible or damaged.
- **Remote `craftctl` CLI Connectivity**: Enhance `craftctl` with `--server` and `--token` flags to execute commands against remote daemon endpoints.

## Capabilities

### New Capabilities
- `identity-access-management`: Multi-user authentication, dedicated `data/auth.db` storage, Argon2id password hashing, SSO session cookies, API tokens, and role-based access control (RBAC).

### Modified Capabilities
- `control-system`: Extend the control system to support remote HTTP/WebSocket transport, static Web Admin Dashboard hosting, live process log streaming, and system telemetry probes.

## Impact

- **`CraftLab-ctl`**: Adds `fastapi` and `uvicorn` to dependencies; adds web server daemon runner, authentication middleware, WebSocket handlers, and `CraftLab-ctl/web/` frontend project.
- **`backend`**: Integrates the shared identity and session verification middleware from `data/auth.db` to protect `/api/v1/*` endpoints according to user roles.
- **Storage**: Introduces `data/auth.db` alongside `data/mcp.db` and updates directory initialization.
- **Deployment**: Exposes supervisor port (e.g., `:8443`) or configures reverse proxy routing for `/admin` and `/ws`.
