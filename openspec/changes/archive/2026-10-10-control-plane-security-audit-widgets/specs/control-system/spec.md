# Spec Delta

## ADDED Requirements

### Requirement: Security & Audit Dashboard Domain Navigation
The embedded single-page web administration dashboard SHALL provide a dedicated `"security"` domain tab (`Security & Audit`) within the category tab bar, grouping security posture monitoring, anomaly detection, forensic audit exploration, and incident containment controls into a focused operational view.

#### Scenario: Navigating to the Security & Audit category
- **WHEN** an operator clicks the "Security & Audit" tab in the category bar
- **THEN** the dashboard filters and displays the registered security container presets preserving active layout and grid state

### Requirement: Security Threat Radar Modular Container Preset
The web dashboard container engine SHALL evaluate a declarative `securityThreatRadarPreset` providing real-time security posture telemetry, an anomaly risk index gauge (0% to 100%), authentication failure counters, active quarantine counts, and an emergency lockdown toggle with role-based authorization.

#### Scenario: Viewing threat radar metrics
- **WHEN** the `securityThreatRadarPreset` container renders
- **THEN** it displays the threat score gauge with canonical tone coloring, the current posture status pill, telemetry metrics, and admin-restricted containment toggles

#### Scenario: Non-admin operator attempts lockdown toggle
- **WHEN** a user without the admin role attempts to toggle emergency lockdown mode
- **THEN** the input primitive is disabled and role-based access control prevents action dispatch

### Requirement: Anomaly Monitor and Active Mitigations Preset
The web dashboard container engine SHALL evaluate a declarative `securityAnomalyMonitorPreset` supporting sub-view pagination between a live anomalies view and an active containment view, providing actionable incident cards with one-click containment triggers (IP quarantine with TTL and session revocation).

#### Scenario: Inspecting detected anomaly and executing IP quarantine
- **WHEN** an operator views a detected brute-force alert card and clicks "Quarantine IP"
- **THEN** the action dispatcher submits a quarantine containment request to the control server, registers the IP block, and updates the anomaly status

#### Scenario: Revoking all active sessions from containment view
- **WHEN** an authorized admin operator clicks "Revoke All Active Sessions" in the containment sub-view and confirms the prompt
- **THEN** the action dispatcher invokes the session revocation endpoint, immediately terminating active sessions across the system

### Requirement: Forensic Audit Explorer Container Preset
The web dashboard container engine SHALL evaluate a declarative `securityAuditExplorerPreset` utilizing record pagination (`paginationMode: "records"`) to inspect canonical security events from SQLite audit storage, supporting multi-criteria filtering by severity, component, and outcome, expandable event attribute inspection, and retention purge controls.

#### Scenario: Filtering forensic audit events by severity
- **WHEN** an operator selects "CRITICAL" in the severity filter dropdown
- **THEN** the audit explorer displays only security events with CRITICAL severity ordered chronologically descending

#### Scenario: Inspecting sanitized event attributes
- **WHEN** an operator clicks to inspect a specific security event row
- **THEN** an inspection drawer displays the full sanitized payload including source IP, route, reason code, and duration without exposing sensitive credentials
