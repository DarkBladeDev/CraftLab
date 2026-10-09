---
name: release-versioning
description: Official guidelines, architecture, and operational recipes for managing CraftLab unified monorepo versioning and release automation via scripts/bump_version.py.
---

# CraftLab Release Versioning Specification

This skill documents how versioning works across the **CraftLab** monorepo, specifying when and how AI agents and developers must interact with release versions, and establishing strict safety guardrails.

---

## 1. Unified Monorepo Version Architecture

CraftLab operates under a **lockstep unified versioning model**. All platform sub-ecosystems (Backend FastAPI, Frontend React/Vite, Minecraft Paper Plugin, and Control System Daemon/CLI `craftlab-ctl`) share the exact same Semantic Version number (`MAJOR.MINOR.PATCH`).

Version strings are tracked across **8 key repository manifests**:

| Component | Manifest Path | Ecosystem | Target Pattern / Field |
| :--- | :--- | :--- | :--- |
| **Backend** | `CraftLab-backend/main.py` | Python (FastAPI) | `version="X.Y.Z"` |
| **Frontend** | `CraftLab-frontend/package.json` | Node / TypeScript | `"version": "X.Y.Z"` |
| **Plugin** | `CraftLab-plugin/build.gradle.kts` | Java / Gradle | `version = "X.Y.Z"` |
| **Plugin YAML** | `CraftLab-plugin/src/main/resources/plugin.yml` | Bukkit YAML | `version: X.Y.Z` |
| **Control CLI** | `CraftLab-ctl/pyproject.toml` | Python (Setuptools) | `version = "X.Y.Z"` |
| **Control Module**| `CraftLab-ctl/src/craftlab_ctl/__init__.py` | Python Module | `__version__ = "X.Y.Z"` |
| **Control Web UI**| `CraftLab-ctl/web/package.json` | Node / Vite | `"version": "X.Y.Z"` |
| **Docs Portal** | `docs/metadata.yml` | DarkBladeDev Docs | Index 0 in `versions:` array |

---

## 2. Core Automation Tool: `scripts/bump_version.py`

All version changes must be performed through the official automation script:

```bash
python scripts/bump_version.py [TARGET_VERSION | --patch | --minor | --major | --check] [OPTIONS]
```

The script is built purely with Python's standard library (zero external dependencies) and guarantees atomic updates across all 8 files.

### CLI Flags & Capabilities

* `--check`: Non-destructive diagnostic mode. Scans all manifests, prints an alignment table, and flags version drift without editing disk.
* `--dry-run`: Previews the exact files and lines that would change without writing to disk.
* `--patch`: Increments patch component (e.g., `0.5.2` -> `0.5.3`).
* `--minor`: Increments minor component (e.g., `0.5.2` -> `0.6.0`).
* `--major`: Increments major component (e.g., `0.5.2` -> `1.0.0`).
* `<target_version>`: Sets an explicit version across all files (useful for reconciliation).
* `--changelog "..."`: Release notes text for `docs/metadata.yml` (defaults to a standard placeholder).
* `--commit`: Stages only the modified release manifests and creates `chore(release): bump version to X.Y.Z`.
* `--tag`: Creates an annotated Git tag `vX.Y.Z` pointing to the release commit.
* `--force`: Bypasses git dirty working-tree safety check when using `--commit`.

---

## 3. When to Use (Trigger Scenarios)

Use this workflow only in the following situations:

1. **Preparing a Production Release**:
   When all features, bug fixes, or OpenSpec changes for a milestone are tested and ready to release.
2. **Reconciling Version Drift**:
   When new submodules or documentation manifests lag behind the core platform version.
3. **Pre-release Diagnostics / CI Checks**:
   Running `python scripts/bump_version.py --check` in pull requests or CI to verify that no manifest was edited out-of-sync.
4. **Updating DarkBladeDev Documentation Registry**:
   Registering a new release entry in `docs/metadata.yml` matching the portal content loader schema (`plugin-docs-versioning`).

---

## 4. When NOT to Use (Strict Guardrails & Anti-Patterns)

To prevent accidental releases and repository corruption, strictly adhere to these rules:

### ⛔ NEVER Edit Manifests by Hand
* **Anti-Pattern**: Using search-and-replace or editing individual `package.json`, `main.py`, or `build.gradle.kts` files manually.
* **Why**: Manual edits invariably miss one or more of the 8 files, causing version drift.

### ⛔ NEVER Bump Versions on Intermediate Feature Commits
* **Anti-Pattern**: Bumping the version during everyday feature development, refactors, or bugfix branch commits.
* **Why**: Releases and version bumps represent atomic milestones. Intermediate changes belong in feature branches without modifying the release tag or version.

### ⛔ STRICT RULE: NEVER Run `git push` Automatically
* **Safety Mandate**: Agents must **NEVER** run `git push` or `git push --tags`.
* **Why**: Pushing a `v*` tag triggers GitHub Actions (`.github/workflows/release.yml`) which builds and publishes the production GitHub Release tarballs and plugin JARs. Pushing to remote repositories is exclusively the responsibility of the human operator.

---

## 5. Standard Operational Recipes

### Recipe A: Health & Drift Inspection
Check repository alignment before any release work:
```bash
python scripts/bump_version.py --check
```

### Recipe B: Dry-Run Preview
Simulate a patch bump without touching the filesystem:
```bash
python scripts/bump_version.py --dry-run --patch
```

### Recipe C: Atomic Patch Release with Custom Changelog
Bump patch version, register release notes in docs metadata, and create git commit and tag:
```bash
python scripts/bump_version.py --patch \
  --changelog "Fixed display packet despawn and spatial hitbox clearance." \
  --commit \
  --tag
```

### Recipe D: Aligning / Reconciling Out-of-Sync Manifests
Force all 8 manifests to align to a known baseline (e.g. `0.5.2`):
```bash
python scripts/bump_version.py 0.5.2
```

### Recipe E: Manual Operator Push Step
After verifying git log and git tag locally, the human operator publishes to GitHub:
```bash
git push origin HEAD && git push origin --tags
```
