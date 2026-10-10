# Spec Delta

## ADDED Requirements

### Requirement: Proactive Sliding-Window Anomaly Heuristic Evaluation
The security audit system SHALL evaluate canonical security events in a rolling 15-minute sliding window to compute a composite threat index (0 to 100) and detect anomalous patterns including credential brute-force attacks, unauthorized privilege denial spikes, emergency break-glass invocations, and route enumeration scans.

#### Scenario: Detecting brute-force authentication spike
- **WHEN** more than 5 failed authentication events occur from the same source IP or targeting the same user within 60 seconds
- **THEN** the system generates a high-severity anomaly alert identifying the offending source IP and target actor

#### Scenario: Detecting break-glass emergency credential usage
- **WHEN** a security event is ingested with actor type `break_glass`
- **THEN** the system elevates the threat posture to `ELEVATED` or `HIGH` and creates a critical alert for operator review

### Requirement: Authenticated Security Posture and Incident REST APIs
The `craftctld` control server SHALL expose authenticated REST endpoints under `/api/v1/security/` providing posture score summaries (`/posture`), active anomaly alerts (`/anomalies`), paginated audit event queries (`/events`), and active containment status (`/quarantines`).

#### Scenario: Querying threat posture summary
- **WHEN** an authenticated client issues a `GET /api/v1/security/posture` request
- **THEN** the server returns the computed threat index, posture classification (`NORMAL`, `ELEVATED`, `HIGH`, `CRITICAL`, or `LOCKDOWN`), recent failure counts, and active quarantine counts

#### Scenario: Querying paginated audit events with filters
- **WHEN** an authenticated client issues a `GET /api/v1/security/events` request with severity and component query parameters
- **THEN** the server queries the SQLite audit database and returns matching sanitized records with total count and pagination metadata

### Requirement: Active Containment and Quarantine Enforcement
The control server SHALL provide active containment endpoints and middleware enforcement to quarantine offending IP addresses with configurable expiration time-to-live, revoke active operator or user sessions, and toggle an emergency lockdown mode that restricts system access.

#### Scenario: Enforcing IP quarantine on incoming requests
- **WHEN** an incoming HTTP or WebSocket request originates from an IP address in the active quarantine list
- **THEN** the server rejects the request with HTTP 403 Forbidden and emits an `authz.denied` security audit event

#### Scenario: Emergency session revocation
- **WHEN** an administrator issues a `POST /api/v1/security/revoke-sessions` request
- **THEN** all matching sessions are purged from the session database and affected clients are forced to re-authenticate

#### Scenario: Toggling emergency lockdown mode
- **WHEN** an administrator issues a `POST /api/v1/security/toggle-lockdown` request with `enabled: true`
- **THEN** the system enters lockdown mode, rejecting all non-admin authentication attempts and mutating actions
