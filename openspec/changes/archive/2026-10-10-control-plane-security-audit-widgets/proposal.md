# Proposal

## Why

The CraftLab control plane currently lacks dedicated security and forensic visibility, forcing administrators to rely on low-level logs without proactive anomaly detection or fast-acting containment controls. Introducing dedicated security widgets and active mitigation actions directly into the web dashboard provides operators with instant threat posture awareness and one-click incident response.

## What Changes

- Add a dedicated `"security"` (`Security & Audit`) domain category to the control plane dashboard navigation tab bar.
- Introduce three new declarative modular container presets (with all user-facing and code strings standardized in English):
  - `securityThreatRadarPreset`: Displays live threat index gauge, posture status pill, telemetry counters (failed auths, quarantined IPs), posture recalculation, and emergency lockdown toggle.
  - `securityAnomalyMonitorPreset`: Multi-page container providing real-time detection cards for heuristic triggers (brute-force attacks, break-glass usage, route enumeration) and active containment controls (IP quarantine with TTL, emergency session revocation).
  - `securityAuditExplorerPreset`: Paginated collection container (`paginationMode: "records"`) for querying historical and live events from SQLite WAL storage with multi-criteria filtering (severity, component, outcome), deep inspection drawer, and retention purge triggers.
- Implement proactive heuristic anomaly detection in `craftlab_ctl` server evaluating rolling 15-minute sliding windows over `SecurityAuditSink`.
- Expose authenticated security control REST endpoints in `craftctld` under `/api/v1/security/*` for posture, anomaly feeds, paginated audit records, IP quarantine management, emergency session revocation, and log retention enforcement.
- Integrate quarantine and lockdown middleware enforcement in `craftctld` to reject requests from quarantined source IPs and enforce strict access during lockdown mode.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `control-system`: Extends dashboard category navigation with the `security` domain, registers three new security container presets with declarative input/output primitives, and supports active mitigation dispatch actions with role-based access restrictions.
- `security-audit`: Extends audit storage and sink capabilities with proactive sliding-window anomaly evaluation, HTTP query endpoints, and containment enforcement mechanisms (IP quarantine with TTL, emergency session invalidation, and lockdown mode).

## Impact

- **Backend**: `CraftLab-ctl/src/craftlab_ctl/server/app.py`, `CraftLab-ctl/src/craftlab_ctl/core/audit.py`, `CraftLab-ctl/src/craftlab_ctl/auth/db.py`, and `packages/craftlab_security`.
- **Frontend**: `CraftLab-ctl/web/src/components/containers/presets/` (new presets and index registration), `CraftLab-ctl/web/src/components/Dashboard.tsx`, `CraftLab-ctl/web/src/api.ts`, and `CraftLab-ctl/web/src/types/presets.ts`.
- **APIs**: New authenticated REST routes under `/api/v1/security/` (`posture`, `anomalies`, `events`, `quarantines`, `quarantine`, `unquarantine`, `revoke-sessions`, `toggle-lockdown`, `purge`).
- **Dependencies & DB**: Leverages existing `craftlab_security` SQLite WAL database (`security-audit.sqlite3`) and `auth.sqlite3`; no external third-party dependencies required.
