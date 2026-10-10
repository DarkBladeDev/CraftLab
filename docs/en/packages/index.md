---
title: Shared Packages Architecture
description: Overview, architecture, and registry for CraftLab monorepo shared packages.
sidebar:
  order: 1
  label: Packages Overview
---

# Shared Packages Architecture

CraftLab's monorepo includes standalone shared libraries located at [`packages/`](https://github.com/DarkBladeDev/CraftLab/tree/main/packages). These packages provide modular, reusable domain contracts and services consumed across platform components (`CraftLab-backend`, `CraftLab-ctl`, build tools, and agent runtimes).

---

## Package Registry

| Package | Directory | Version | Status | Description | Documentation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`craftlab_security`** | [`packages/craftlab_security`](https://github.com/DarkBladeDev/CraftLab/tree/main/packages/craftlab_security) | `0.1.0` | **Active** | Canonical security event contract, universal data sanitization, and WAL SQLite audit sink. | [craftlab_security](craftlab-security.md) |

---

## Monorepo Architectural Guidelines

All packages developed under `packages/` must adhere to these foundational principles:

### 1. Zero Circular Dependencies & Loose Coupling
- Shared packages must **never** import internal application modules from `CraftLab-backend`, `CraftLab-ctl`, or `CraftLab-frontend`.
- Packages should depend strictly on the Python standard library or approved lightweight ecosystem libraries (e.g., `pydantic >= 2.0.0`).

### 2. Standard PEP 621 Structure
Each package directory under `packages/<package_name>/` must follow PEP 621 standards:

```text
packages/<package_name>/
├── pyproject.toml              # Build tool configuration (PEP 621)
├── README.md                   # Package overview and quickstart
├── src/
│   └── <package_name>/
│       ├── __init__.py         # Public API exports
│       ├── py.typed            # PEP 561 inline typing marker
│       └── ...                 # Package implementation modules
└── tests/
    ├── __init__.py
    └── test_*.py               # Hermetic unit test suite
```

### 3. Multi-Virtual Environment Provisioning
Because CraftLab maintains dedicated virtual environments (`CraftLab-backend/.venv` and isolated runtime/release environments in `releases/v0.3.0/.venv` / `CraftLab-ctl`), shared packages must be provisioned in editable mode across all target environments:

```bash
pip install -e packages/<package_name>
```

### 4. Hermetic & Isolated Unit Testing
Every package must include comprehensive unit tests under `packages/<package_name>/tests/` that pass in total isolation, without requiring running daemons, network sockets, or active background services.
