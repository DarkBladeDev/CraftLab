# Design

## Context

See `proposal.md` for motivation and background. The CraftLab monorepo contains `packages/craftlab_security` with a WAL-mode SQLite audit database (`security-audit.sqlite3`), canonical event models (`SecurityEvent`), and sanitization routines. In `CraftLab-ctl`, the dashboard features a categorized tab bar and modular container engine rendering typed presets (`PaginatedContainerPreset`) via `ContainerEngine`.

Currently, there are no endpoints exposing security audit telemetry to the web client, no category in `SUPERVISOR_CATEGORIES` for security, and no incident containment tools in the browser interface.

## Goals / Non-Goals

**Goals:**
- Provide a dedicated `"security"` domain category tab with shield-alert icon in the supervisor dashboard.
- Implement 3 modular container presets (`securityThreatRadarPreset`, `securityAnomalyMonitorPreset`, `securityAuditExplorerPreset`) conforming to existing container engine primitives.
- Implement an in-process 15-minute sliding window anomaly evaluator querying the SQLite audit sink for brute-force attacks, break-glass usage, and route scanning.
- Expose authenticated `/api/v1/security/*` endpoints for posture, anomaly feeds, paginated audit records, and containment operations.
- Implement active containment enforcement in `craftctld`: dynamic IP quarantine with expiration TTL, targeted/global session revocation, and emergency lockdown mode.
- Standardize 100% of user-facing UI strings (titles, subtitles, metrics, buttons, badges) in English.

**Non-Goals:**
- Heavy distributed SIEM or external telemetry forwarding (e.g. Datadog, Splunk) — all queries run against the local SQLite WAL sink.
- Deep machine learning anomaly models — detection relies on deterministic heuristics and statistical thresholds in a 15-minute sliding window.
- Permanent OS-level firewall mutation (iptables/nftables) — IP quarantine operates at the HTTP/WebSocket application gateway middleware layer.

## Decisions

### Decision 1: Modular Preset Decomposition
- **Choice**: Decompose security operations into 3 focused widgets:
  1. `securityThreatRadarPreset` (Posture, threat index gauge, telemetry counters, lockdown toggle).
  2. `securityAnomalyMonitorPreset` (Sub-view pagination: Live anomaly cards with direct mitigation buttons vs Active quarantines & session purge).
  3. `securityAuditExplorerPreset` (Record pagination: Multi-filter historical and live SQLite audit event table with inspection drawer).
- **Rationale**: Keeps responsibilities clean and prevents UI clutter. Fits neatly into `DraggableGrid` columns.
- **Alternatives Considered**: A single monolith widget with tabs was considered, but it would hide critical threat radar metrics when inspecting records.

### Decision 2: In-Memory Quarantine with Sliding TTL & Middleware Check
- **Choice**: Implement an `IpQuarantineManager` in `craftctld` storing quarantined IPs in memory with timestamp and expiration TTL (e.g. 15m, 1h), evaluated via FastAPI middleware on each request.
- **Rationale**: In-memory hash set checks take sub-millisecond overhead per request, preventing database contention during an attack.
- **Alternatives Considered**: Writing each quarantine check to SQLite on every incoming request would introduce disk contention under traffic spikes.

### Decision 3: 15-Minute Heuristic Anomaly Evaluation
- **Choice**: The anomaly engine queries `SecurityAuditSink.query_events(limit=200)` for events in the last 15 minutes, computing:
  - Brute force: `>5` failed auth events from the same IP or targeting the same user within 60 seconds.
  - Break-glass alert: any event where `actor.type == "break_glass"`.
  - Route enumeration: `>10` 404/403 responses within 2 minutes.
  - Threat score: weighted calculation (0 to 100) based on critical, high, and medium events.
- **Rationale**: Uses existing indexed SQLite columns (`occurred_at`, `event_type`, `source_ip`) without requiring complex background stream processing daemons.

### Decision 4: Centralized REST Security Endpoints & Action Dispatch
- **Choice**: Expose all security APIs under `/api/v1/security/`:
  - `GET /api/v1/security/posture`
  - `GET /api/v1/security/anomalies`
  - `GET /api/v1/security/events` (with query params: `severity`, `component`, `outcome`, `limit`, `offset`)
  - `GET /api/v1/security/quarantines`
  - `POST /api/v1/security/quarantine` (admin)
  - `POST /api/v1/security/unquarantine` (admin)
  - `POST /api/v1/security/revoke-sessions` (admin)
  - `POST /api/v1/security/toggle-lockdown` (admin)
  - `POST /api/v1/security/purge` (admin)
- **Rationale**: Aligns with existing `/api/v1/update/` and `/api/v1/lifecycle/` patterns and maps directly into `actionDispatcher` in `Dashboard.tsx`.

## Risks / Trade-offs

- **[Risk]** Memory reset on daemon restart loses active in-memory IP quarantines.
  → **Mitigation**: Persist quarantine entries as lightweight metadata in `data/security-audit.sqlite3` or state directory, reloading on boot while keeping in-memory cache for request routing.
- **[Risk]** Operators accidentally clicking "Revoke All Sessions" could disconnect legitimate administrators.
  → **Mitigation**: Require explicit confirmation dialogue (`confirmMessage`) and retain the active caller's session when using targeted revocation.
- **[Risk]** High audit event volumes impacting query performance in the web UI.
  → **Mitigation**: Existing indexes on `occurred_at DESC` and `event_type` ensure queries stay sub-5ms; default page size is clamped to 25 records.

## Migration Plan

1. Backend endpoints and `IpQuarantineManager` added without breaking existing `/api/v1/*` routes.
2. Web UI adds `"security"` category and presets without altering existing `system`, `lifecycle`, or `doctor` presets.
3. Zero database schema migrations required: `security-audit.sqlite3` schema already contains all indexed columns required by the explorer and anomaly engine.
