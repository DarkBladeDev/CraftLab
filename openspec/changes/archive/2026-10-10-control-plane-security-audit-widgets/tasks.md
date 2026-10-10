# Tasks

## 1. Backend Quarantine & Anomaly Detection Engine

- [x] 1.1 Implement `IpQuarantineManager` in `craftlab_ctl` with TTL expiration, state persistence, and check methods; verify with unit tests in `CraftLab-ctl/tests/test_quarantine.py`.
- [x] 1.2 Implement sliding 15-minute heuristic anomaly evaluator over `SecurityAuditSink` (brute-force threshold, break-glass alert, route enumeration, threat index 0-100); verify with unit tests in `CraftLab-ctl/tests/test_anomaly_evaluator.py`.
- [x] 1.3 Add global and user-targeted session revocation methods (`revoke_user_sessions`, `revoke_all_sessions_except`) in `craftlab_ctl.auth.db`; verify with database unit tests.

## 2. Server REST APIs & Middleware Enforcement

- [x] 2.1 Add request quarantine and lockdown check middleware to `app.py` rejecting blacklisted IPs with 403 Forbidden; verify with test client requests.
- [x] 2.2 Expose authenticated telemetry endpoints (`GET /api/v1/security/posture`, `GET /api/v1/security/anomalies`, `GET /api/v1/security/events`, `GET /api/v1/security/quarantines`) in `app.py`; verify with route tests.
- [x] 2.3 Expose admin-restricted active mitigation endpoints (`POST /api/v1/security/quarantine`, `POST /api/v1/security/unquarantine`, `POST /api/v1/security/revoke-sessions`, `POST /api/v1/security/toggle-lockdown`, `POST /api/v1/security/purge`) in `app.py`; verify RBAC enforcement.

## 3. Web API Client & Dashboard Integration

- [x] 3.1 Add TypeScript interfaces (`SecurityPosture`, `SecurityAnomaly`, `SecurityQuarantineEntry`, `SecurityEventRecord`) and API client methods to `CraftLab-ctl/web/src/api.ts`; verify TypeScript compilation.
- [x] 3.2 Update `SUPERVISOR_CATEGORIES` in `CraftLab-ctl/web/src/components/containers/presets/index.ts` to include the `"security"` (`Security & Audit`) domain tab; verify tab rendering.
- [x] 3.3 Update `Dashboard.tsx` to poll security posture and anomaly data, wire security actions into `ContainerActionDispatcher`, and pass security context into containers; verify data flow.

## 4. Modular Security Container Presets

- [x] 4.1 Implement `securityThreatRadarPreset.ts` with threat index gauge, posture status pill, telemetry counters, and emergency lockdown toggle (all strings in English); verify component rendering in container engine.
- [x] 4.2 Implement `securityAnomalyMonitorPreset.tsx` with sub-view pagination (Live Anomalies cards with direct containment buttons vs Active Quarantines list with session purge); verify sub-view switching and action dispatch.
- [x] 4.3 Implement `securityAuditExplorerPreset.tsx` with record pagination (`paginationMode: "records"`), multi-field dropdown filters, sanitized event attribute drawer, and retention purge button; verify table filtering and pagination.
- [x] 4.4 Export and register new presets in `CraftLab-ctl/web/src/components/containers/presets/index.ts` and verify clean build with `npm run build`.

## 5. End-to-End Verification

- [x] 5.1 Run complete backend pytest test suite for `craftlab_ctl` and `craftlab_security`; verify all tests pass.
- [x] 5.2 Validate Vite production build of `CraftLab-ctl/web`; verify clean build and asset generation without TypeScript warnings.
