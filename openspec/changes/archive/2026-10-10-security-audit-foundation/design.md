# Design: security-audit-foundation

## Context

CraftLab comprises separate runtimes across FastAPI (`CraftLab-backend`), the supervisor daemon (`CraftLab-ctl`), and connected Minecraft Paper servers (`CraftLab-plugin`). As detailed in [proposal.md](file:///c:/Users/antua/OneDrive/Documentos/Programming/MISC/MinecraftResourceManager/openspec/changes/security-audit-foundation/proposal.md) and [.project/docs/security/SECURITY_ARCHITECTURE.md](file:///c:/Users/antua/OneDrive/Documentos/Programming/MISC/MinecraftResourceManager/.project/docs/security/SECURITY_ARCHITECTURE.md), each runtime exposes distinct endpoints and requires unified audit visibility and hardened transport boundaries.

## Goals / Non-Goals

**Goals:**
- Provide a lightweight, framework-agnostic Python package (`craftlab_security`) containing the canonical event schema, universal sanitizer, and SQLite persistence sink.
- Implement dual-path write persistence in `data/security-audit.sqlite3`: fail-closed synchronous emission for sensitive administrative mutations and bounded asynchronous batching for high-volume network telemetry.
- Enforce fail-fast configuration validation upon production boot to prevent unauthenticated exposure or default credentials.
- Restrict supervisor CORS to explicit origins and enforce `Secure` cookies with zero query-string token leakage.
- Extract supervisor `caller_id` exclusively from transport identity, ignoring client-supplied payload parameters.
- Verify target secrets during WebSocket agent `hello` handshakes in `/ws/agent` before session registration.

**Non-Goals:**
- Automated destructive mitigations (e.g. autonomous IP banning or process termination) in this foundation change.
- Introducing external distributed message brokers (Kafka, RabbitMQ) or distributed databases.
- Replacing existing functional data stores (`data/mcp.db` and `data/auth.db`).

## Decisions

### Decision 1: Shared `craftlab_security` Module Structure
- **Choice**: Structure `craftlab_security` as a zero-dependency (relying strictly on the Python standard library and Pydantic v2) package under `packages/craftlab_security` or as a top-level shared module accessible by both `CraftLab-backend` and `CraftLab-ctl`.
- **Rationale**: Decouples event schemas from FastAPI and SQLAlchemy, ensuring both the CLI supervisor and the web backend can emit conformant events without cyclic dependencies.
- **Alternatives Considered**: Housing the code entirely inside `craftlab_ctl`. Rejected because it would force `CraftLab-backend` to depend on supervisor process management tooling.

### Decision 2: Dual-Path SQLite Write Strategy
- **Choice**: Provide two emission methods in the persistence layer:
  1. `emit_critical(event)`: Executes a direct, synchronous SQLite transaction with `fail-closed` semantics. If the write fails, the calling administrative operation aborts.
  2. `emit_telemetry(event)`: Enqueues the event into an in-memory `asyncio.Queue` (bounded to 5,000 items) drained by a background task writing batches via `executemany` every 250ms or 50 events.
- **Rationale**: Administrative operations demand strict audit durability, whereas high-volume HTTP 404s, scanning traffic, or heartbeats must not block request event loops or provoke SQLite lock contention.
- **Alternatives Considered**: Pure synchronous writes for all events (causes `sqlite3.OperationalError: database is locked` under network bursts) vs pure asynchronous writes (risks losing audit records if a crashing administrative action occurs).

### Decision 3: Transport-Derived Identity in Supervisor Daemon
- **Choice**: Modify `DaemonService.handle_action` in `CraftLab-ctl/src/craftlab_ctl/daemon.py` to discard `payload.get("caller_id")`. The caller identity is derived strictly from the authenticated transport context (`ctx.caller_id` set to `web:{auth.username}` for web sessions or `ipc:{peer_uid}` for local domain sockets).
- **Rationale**: Eliminates client-side identity spoofing where an unprivileged caller could claim to be `root` or `admin`.

### Decision 4: Agent Handshake Secret Verification
- **Choice**: In `CraftLab-backend/app/gateway/manager.py`, update `handle_message` for message type `hello`:
  1. Extract `targetSecret` from payload.
  2. Query `TargetModel` by `targetId`.
  3. Constant-time compare `targetSecret` against `TargetModel.secret`.
  4. If invalid or missing, emit `websocket.auth.failure`, close WebSocket with code 1008 (Policy Violation), and reject session registration.
- **Rationale**: Prevents arbitrary network clients from spoofing Minecraft server targets or receiving deployment payloads.

### Decision 5: Production Configuration Guardrails
- **Choice**: Add an environment validator in backend and ctl startup routines. When `ENV=production` or `CRAFTLAB_ENV=production`:
  - If `CRAFTLAB_AUTH_ENABLED` is false, abort startup with exit code 1.
  - If `CRAFTLAB_ROOT_KEY` equals `change_me_to_a_secure_root_token`, abort startup with exit code 1.
  - In development environments, log prominent warnings without aborting.

## Risks / Trade-offs

- **[Risk] SQLite lock contention on concurrent writes**  
  *Mitigation*: Database is configured with `PRAGMA journal_mode=WAL` and `PRAGMA busy_timeout=5000`. Telemetry traffic uses an asynchronous flusher to minimize write frequency.
- **[Risk] Existing agent connections failing if secret is omitted**  
  *Mitigation*: `CraftLab-plugin` already stores `secret` in its configuration; ensure the payload schema accepts `targetSecret` with backward compatibility in dev mode.
- **[Risk] Legacy audit log disruption in `craftctld`**  
  *Mitigation*: Retain `audit.jsonl` writer alongside SQLite sink during transition phase, applying the universal sanitizer to both.

## Migration Plan

1. Deploy `craftlab_security` models and SQLite schema migration (`data/security-audit.sqlite3`).
2. Update backend and daemon authentication guards and CORS settings.
3. Update agent gateway handshake handler with target secret check.
4. Verify existing test suites (`pytest` for backend, Gradle for plugin, and `craftlab-ctl` tests).
