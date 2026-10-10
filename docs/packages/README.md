# CraftLab Monorepo Packages Registry

This directory documents the standalone shared packages developed within the CraftLab monorepo, located at the repository root [`packages/`](../../packages).

As the ecosystem expands, new shared libraries, utility packages, and domain modules will be added under [`packages/`](../../packages) and registered in this directory.

---

## Package Registry

| Package | Directory | Version | Status | Description | Documentation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`craftlab_security`** | [`packages/craftlab_security`](../../packages/craftlab_security) | `0.1.0` | **Active** | Canonical security event contract, universal data sanitization, and WAL-mode SQLite audit sink. | [craftlab-security.md](craftlab-security.md) |

---

## Architectural Guidelines for Packages

All packages developed under [`packages/`](../../packages) must adhere to the following monorepo architectural standards:

### 1. Zero Circular Dependencies & Loose Coupling
- Shared packages must **never** import internal application modules from `CraftLab-backend`, `CraftLab-ctl`, or `CraftLab-frontend`.
- Packages should depend strictly on the Python standard library or approved lightweight ecosystem libraries (e.g., `pydantic >= 2.0.0`).

### 2. Standard Package Structure
Each package directory under `packages/<package_name>/` must follow PEP 621 standards:
```text
packages/<package_name>/
├── pyproject.toml              # Build tool configuration (PEP 621)
├── README.md                   # Package overview and local installation guide
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
Because CraftLab maintains dedicated virtual environments (`CraftLab-backend/.venv` and isolated runtime/release environments in `releases/v0.3.0/.venv` / `CraftLab-ctl`), shared packages must be provisioned in editable mode across all target virtual environments:
```bash
pip install -e packages/<package_name>
```

### 4. Hermetic & Isolated Unit Testing
Every package must include comprehensive unit tests under `packages/<package_name>/tests/` that pass in total isolation, without requiring running daemons, network sockets, or active background services.
