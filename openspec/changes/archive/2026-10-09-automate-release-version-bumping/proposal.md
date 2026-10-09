# Proposal: Automate Release Version Bumping

## Why

CraftLab is a monorepo spanning multiple ecosystems (FastAPI in Python, Vite/React in TypeScript, Paper plugin in Java/Gradle, and `craftlab-ctl` in Python). Currently, bumping versions for releases requires manually editing 5+ different manifest files across disparate folders and formats (`main.py`, `package.json`, `build.gradle.kts`, `plugin.yml`, `pyproject.toml`, and `docs/metadata.yml`).

This manual process has already led to real version drift across the repository (e.g. CraftLab Core at `0.5.2` while `craftlab-ctl` and `docs/metadata.yml` lagged at `0.3.3`). Furthermore, AI agents and contributors lack clear guidelines and dedicated tooling on how to safely align monorepo versions without accidentally triggering breaking changes or unintentional remote git pushes.

## What Changes

- **Unified Monorepo Versioning**: Formally establish that CraftLab Core (Backend, Frontend, Plugin) and `craftlab-ctl` share a unified version number in lockstep.
- **Standalone Zero-Dependency CLI Tool (`scripts/bump_version.py`)**:
  - Implements semver parsing and increment modes (`--patch`, `--minor`, `--major`, or explicit target version).
  - Inspects current repository state with `--check` to detect version mismatches and drift across all manifests.
  - Supports `--dry-run` to preview exact line changes without touching files on disk.
  - Atomically updates all 7 component manifests:
    1. `CraftLab-backend/main.py` (FastAPI `version` kwarg)
    2. `CraftLab-frontend/package.json` (`version` field)
    3. `CraftLab-plugin/build.gradle.kts` (`version = "..."`)
    4. `CraftLab-plugin/src/main/resources/plugin.yml` (`version: ...`)
    5. `CraftLab-ctl/pyproject.toml` (`version = "..."`)
    6. `CraftLab-ctl/src/craftlab_ctl/__init__.py` (`__version__ = "..."`)
    7. `CraftLab-ctl/web/package.json` (`version` field)
  - Updates `docs/metadata.yml` in compliance with the DarkBladeDev loader specification (`plugin-docs-versioning`), prepending the new version at `index 0` with current date, GitHub release download URL, Minecraft compatibility, and an optional or placeholder changelog.
  - Provides optional Git automation via `--commit` and `--tag` flags (staging only modified manifests, creating a standardized commit `chore(release): bump version to X.Y.Z` and annotated tag `vX.Y.Z`).
  - **STRICT SAFETY GUARDRAIL**: Never runs `git push`. Pushing tags or commits is strictly reserved for the human operator.
- **Dedicated Agent Skill (`.agents/skills/release-versioning/SKILL.md`)**:
  - Documented in English for AI coding agents and human developers.
  - Lists the inventory of all 7 versioned manifests.
  - Details trigger scenarios (when to use: releases, reconciliations, diagnostics) and guardrails (when NOT to use: daily feature commits, manual file editing, auto-pushing).
  - Provides concrete CLI recipes and dry-run verification steps.
- **Initial Version Drift Reconciliation**:
  - Reconcile `craftlab-ctl` (`pyproject.toml`, `__init__.py`) and `docs/metadata.yml` from `0.3.3` to `0.5.2` to establish a clean, consistent baseline.

## Capabilities

### New Capabilities
None. This change introduces developer tooling, automation scripts, and agent documentation without altering runtime platform capabilities.

### Modified Capabilities
None.

## Impact

- **Developer Experience**: Eliminates repetitive manual edits across 7 files and eliminates human error during release prep.
- **Build & CI/CD Pipelines**: Integrates with existing GitHub Action `release.yml` seamlessly since `release.yml` already triggers on `v*` tags created by the tool.
- **Documentation Engine**: Guarantees that `docs/metadata.yml` stays in sync with releases, ensuring the DarkBladeDev documentation portal always reflects current and historical releases accurately.
- **Agent Behavior**: AI agents will discover and use the `release-versioning` skill and `scripts/bump_version.py` instead of performing ad-hoc manual edits.
