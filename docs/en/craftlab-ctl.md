---
title: CraftLab-ctl (Control System & Daemon)
description: Supervisor daemon, craftctl CLI, atomic updates pipeline, and web dashboard guide.
sidebar:
  order: 3
---

# CraftLab-ctl

**CraftLab-ctl** is the supervisor control plane for CraftLab. It consists of the `craftctld` background daemon, the `craftctl` operator CLI, an atomic update engine, and an embedded web control dashboard.

---

## Architecture Overview

```
+---------------------------------------------------------------------------------+
|                                 CRAFTLAB-CTL                                    |
+---------------------------------------------------------------------------------+
|                                                                                 |
|   CLI (craftctl) <-----------> REST / Control Socket <-------> Web Panel (:8443)|
|                                      |                                          |
|                                      v                                          |
|                       Daemon Supervisor (craftctld)                             |
|                                      |                                          |
|         +----------------------------+----------------------------+             |
|         |                            |                            |             |
|         v                            v                            v             |
|  [LifecyclePlugin]             [CorePlugin]                 [UpdatePlugin]      |
|  * Service supervisor          * Health & Doctor            * Releases API      |
|  * Process monitor             * Paths resolution           * Wheel cache       |
|  * Uvicorn / Vite runners      * Config loader              * Rollback manager  |
+---------------------------------------------------------------------------------+
```

---

## Command-Line Interface (`craftctl`)

The `craftctl` executable provides administrative access to service operations:

### Service Lifecycle

| Command | Description |
| :--- | :--- |
| `craftctl status` | Shows current operational status of backend, frontend, and daemon services. |
| `craftctl start` | Boots managed services (backend API and control endpoints). |
| `craftctl stop` | Gracefully shuts down managed platform services. |
| `craftctl restart` | Performs a clean restart of platform services. |

### System Diagnostics

```bash
craftctl doctor
```
Inspects:
- Virtual environment health and Python dependencies.
- Static assets availability (`frontend_dist/index.html` and `ctl_web_dist/index.html`).
- Database connectivity and write permissions.
- Network port availability (`CRAFTLAB_PORT`, control panel port `8443`).

---

## Atomic Update Engine

CraftLab features a zero-downtime, rollback-safe update system orchestrated by `UpdatePlugin`:

```
               [GitHub Releases: DarkBladeDev/CraftLab]
                                  │
                          (craftctl update check)
                                  │
                                  ▼
                        Download craftlab-v*.tar.gz
                                  │
                                  ▼
               Create Isolated Release Venv (/releases/vX.Y.Z)
               Install Wheels from Cache (/cache/wheels)
                                  │
                                  ▼
                     Switch Symlink (/current -> /releases/vX.Y.Z)
                     Restart Managed Services
```

### Update Commands

- **Check for available updates**:
  ```bash
  craftctl update check
  ```
- **Prepare release archive** (downloads and validates checksums without applying):
  ```bash
  craftctl update prepare --version 0.3.3
  ```
- **Apply update** (switches active release and restarts services):
  ```bash
  craftctl update apply --version 0.3.3
  ```
- **Rollback to previous release** (instant restore if an update fails validation):
  ```bash
  craftctl update rollback
  ```

---

## Web Control Dashboard

`craftctld` serves a modern, modular web control dashboard on port `8443` built with React and Tailwind CSS:

- **Categorized Pages**: Top horizontal navigation tabs (`Overview`, `System & Host`, `Lifecycle & Ops`, `Releases & Updates`, `Security & Audit`, `Doctor & Health`, `Terminal & Logs`) organize operational domains while preserving 100% of the screen width for panel grids.
- **Modular Paginated Data Containers**: Powered by a typed declarative TypeScript schema (`PaginatedContainerPreset`) and `<ContainerEngine />` supporting hybrid pagination:
  - **Subviews Mode (`subviews`)**: Internal carousel-style mode switching (metrics summary $\rightarrow$ granular breakdown $\rightarrow$ operational actions) inside a single compact card footprint.
  - **Records Collection Mode (`records`)**: Paginated collection rows (installed releases, audit logs, agents) with next/previous controls without overflowing cards.
  - **Simple Mode (`none`)**: Direct single-surface rendering for wide streams such as the real-time log terminal.
- **Draggable & Resizable Grid (`DraggableGrid`)**: Native drag-to-reorder via drag handles (`[::]`), dynamic column span resizing (`- / + Cols`), automatic layout persistence in browser `localStorage`, and a one-click "Reset Layout" action.
- **Role-Based Access Control (RBAC)**: Fine-grained role checks (`admin`, `operator`, `viewer`, `is_break_glass`) on input action controls, disabling or locking restricted triggers.

---

## Security & Audit Control Plane

`CraftLab-ctl` integrates comprehensive threat posture monitoring, proactive heuristic anomaly detection, forensic audit exploration, and instant containment controls.

### Modular Security Presets

The dedicated **Security & Audit** category hosts three specialized container presets:

1. **Security Threat Radar (`securityThreatRadarPreset`)**:
   - **Composite Threat Index**: Real-time 0–100 gauge computed by the anomaly evaluator over a rolling 15-minute sliding window.
   - **Posture Classification**: Color-coded status badge (`NORMAL`, `ELEVATED`, `HIGH`, `CRITICAL`, or `LOCKDOWN`).
   - **Live Telemetry Indicators**: 15-minute failed login counters, 24-hour total events, active quarantine counts, and active anomaly tallies.
   - **Containment Controls**: One-click Emergency Lockdown toggle (restricted to `admin` role) and audit log retention purge.

2. **Anomaly Monitor & Mitigations (`securityAnomalyMonitorPreset`)**:
   - **Heuristic Detection Engine**: Automatically flags brute-force authentication spikes (>5 failures within 60s from the same IP or user), break-glass credential usage, authorization denial spikes, and suspicious route scanning.
   - **Dual Subviews**:
     - *Active Anomalies*: Actionable incident cards displaying anomaly type, description, affected actor/IP, and direct mitigation buttons (**Quarantine IP**, **Dismiss**).
     - *Active Containment*: Real-time list of quarantined IP addresses with remaining TTLs, manual IP quarantine submission form, unquarantine triggers, and an emergency **Revoke All Active Sessions** action.

3. **Forensic Audit Explorer (`securityAuditExplorerPreset`)**:
   - **Canonical SQLite Storage**: Directly queries isolated WAL-mode database (`data/security-audit.sqlite3`) where all events are sanitized prior to persistence.
   - **Records Pagination & Filtering**: Filter events by severity (`CRITICAL`, `HIGH`, `WARN`, `INFO`), emitting component, and outcome (`success`, `failure`, `blocked`).
   - **Attribute Inspector Drawer**: Expand any event to inspect sanitized context (source IP, request path, HTTP status, reason codes) without exposing secrets.

### Security REST API Endpoints

All endpoints require active session authentication under `/api/v1/security/`:

| Endpoint | Method | Role | Description |
| :--- | :--- | :--- | :--- |
| `/api/v1/security/posture` | `GET` | Authenticated | Returns composite threat score, posture status, and counters. |
| `/api/v1/security/anomalies` | `GET` | Authenticated | Lists active detected anomalies. |
| `/api/v1/security/anomalies/dismiss`| `POST` | Operator / Admin | Dismisses an active anomaly alert by ID. |
| `/api/v1/security/events` | `GET` | Authenticated | Paginated query over canonical security audit records. |
| `/api/v1/security/quarantines` | `GET` | Authenticated | Lists active quarantined IP addresses and expiration TTLs. |
| `/api/v1/security/quarantine` | `POST` | Admin | Immediately quarantines an IP address with specified TTL (minutes). |
| `/api/v1/security/unquarantine` | `POST` | Admin | Lifts quarantine from an IP address. |
| `/api/v1/security/revoke-sessions` | `POST` | Admin | Revokes sessions for a specific user or all users across the system. |
| `/api/v1/security/toggle-lockdown` | `POST` | Admin | Toggles emergency lockdown mode (rejects all non-admin access). |
| `/api/v1/security/purge` | `POST` | Admin | Purges audit logs older than specified retention days. |

### Active Containment Middleware

- **IP Quarantine Filter**: The control server middleware checks incoming client IPs against the in-memory and disk-persisted `IpQuarantineManager`. Blocked IPs immediately receive `403 Forbidden` and emit an `authz.denied` audit event.
- **Emergency Lockdown Gate**: When lockdown mode is active, all non-admin authentication attempts are rejected and mutating control endpoints are restricted to authenticated administrators.


