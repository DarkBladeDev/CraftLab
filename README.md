# CraftLab (Minecraft Content Platform)

A modern web-based content authoring, resource pack pipeline, and fleet release management system for Paper Minecraft servers (1.21.1 – 1.21.11+).

## Monorepo Layout

```
MinecraftResourceManager/
├── CraftLab-backend/                 # FastAPI REST API & WebSocket Agent Gateway
│   ├── app/                          # Domain models, database, pack compiler/merger, RBAC
│   └── tests/                        # Automated unit & E2E integration tests (pytest)
├── CraftLab-frontend/                # React 18 + Vite + Tailwind CSS Web Studio
│   └── src/                          # Visual Item Inspector, Block Studio, Pack Manager
├── CraftLab-ctl/                     # Supervisor Daemon CLI & Control Plane
│   ├── src/craftlab_ctl/             # craftctl CLI, daemon, plugins, update pipeline
│   ├── web/                          # Control Panel Web Dashboard (React + Vite SPA)
│   └── tests/                        # Control system tests & packaging validations
├── CraftLab-plugin/                  # Native Java 21 Paper plugin (Gradle + PacketEvents)
│   └── src/main/java/                # Real-time WebSocket bridge, item adapter, /mcp commands
├── scripts/                          # Automation, packaging, and developer runtime scripts
│   ├── dev.ps1                       # All-in-one local dev deploy & runtime launcher
│   ├── bump_version.py               # Unified lockstep version bumping across all 8 manifests
│   ├── build_release.py              # Production release packaging & tar.gz distribution
│   └── seed_dev_auth.py              # Development RBAC credentials seeder
├── openspec/                         # OpenSpec change management and system specifications
└── .env.example                      # Environment variables template
```

---

## Quickstart (Local Dev Deployment)

To build and start all systems locally in one command:

```powershell
.\scripts\dev.ps1
```

This will automatically:
1. Verify or build the Paper plugin JAR (`CraftLab-plugin/build/libs/CraftLab-plugin-1.0.0-SNAPSHOT.jar`).
2. Verify Python virtual environment in `CraftLab-backend`.
3. Start the **FastAPI Backend & WebSocket Gateway** on `http://127.0.0.1:8000`.
4. Start the **React Web Studio** on `http://localhost:3000`.
5. Open your browser at `http://localhost:3000`.

### Other Execution Modes

- **Backend & Frontend only**:
  ```powershell
  .\scripts\dev.ps1 -Mode web-only
  ```
- **Deploy JAR directly to a Paper server directory & launch server**:
  ```powershell
  .\scripts\dev.ps1 -PaperServerDir "C:\path\to\paper-server"
  ```
- **Clean slate data reset**:
  ```powershell
  .\scripts\dev.ps1 -CleanData
  ```
- **Stop running dev processes**:
  ```powershell
  .\scripts\dev.ps1 -Mode stop
  ```

---

## Control System CLI (`craftctl`) & Control Panel

CraftLab includes `CraftLab-ctl` (`craftctl` CLI and `craftctld` supervisor daemon) to manage runtime services, atomic updates, and health probes:

```powershell
# Check platform health and status
craftctl status

# Service lifecycle
craftctl start
craftctl stop
craftctl restart

# Inspect and apply release updates
craftctl update check
craftctl update apply --version 0.3.0
craftctl update rollback
```

The web control dashboard is served on port `8443` by `craftctld`.

---

## Release & Version Management

CraftLab follows a unified lockstep versioning model across Backend, Frontend, Paper Plugin, `craftlab-ctl`, and docs metadata. Use `scripts/bump_version.py` for all version operations:

```powershell
# Diagnostic check for version alignment across all manifests
python scripts/bump_version.py --check

# Dry-run preview of planned changes
python scripts/bump_version.py --patch --dry-run

# Atomic bump with release notes and git tag (never pushes remotely)
python scripts/bump_version.py --patch --changelog "Feature summary" --commit --tag
```

For AI agents and detailed rules, see the specification at [`.agents/skills/release-versioning/SKILL.md`](.agents/skills/release-versioning/SKILL.md).

---

## Running Automated Tests

* **Backend tests** (78 tests):
  ```powershell
  .\CraftLab-backend\.venv\Scripts\pytest CraftLab-backend\tests
  ```
* **Control plane & supervisor tests** (49 tests):
  ```powershell
  .\CraftLab-backend\.venv\Scripts\pytest CraftLab-ctl\tests
  ```
* **Paper plugin build & tests**:
  ```powershell
  cd CraftLab-plugin
  .\gradlew.bat test
  ```
* **Web studio frontend build**:
  ```powershell
  npm --prefix CraftLab-frontend run build
  ```
* **Control panel web dashboard build**:
  ```powershell
  npm --prefix CraftLab-ctl\web run build
  ```

