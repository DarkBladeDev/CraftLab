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

- **Categorized Pages**: Top horizontal navigation tabs (`Overview`, `System & Host`, `Lifecycle & Ops`, `Releases & Updates`, `Doctor & Health`, `Terminal & Logs`) organize operational domains while preserving 100% of the screen width for panel grids.
- **Modular Paginated Data Containers**: Powered by a typed declarative TypeScript schema (`PaginatedContainerPreset`) and `<ContainerEngine />` supporting hybrid pagination:
  - **Subviews Mode (`subviews`)**: Internal carousel-style mode switching (metrics summary $\rightarrow$ granular breakdown $\rightarrow$ operational actions) inside a single compact card footprint.
  - **Records Collection Mode (`records`)**: Paginated collection rows (installed releases, audit logs, agents) with next/previous controls without overflowing cards.
  - **Simple Mode (`none`)**: Direct single-surface rendering for wide streams such as the real-time log terminal.
- **Draggable & Resizable Grid (`DraggableGrid`)**: Native drag-to-reorder via drag handles (`[::]`), dynamic column span resizing (`- / + Cols`), automatic layout persistence in browser `localStorage`, and a one-click "Reset Layout" action.
- **Role-Based Access Control (RBAC)**: Fine-grained role checks (`admin`, `operator`, `viewer`, `is_break_glass`) on input action controls, disabling or locking restricted triggers.

