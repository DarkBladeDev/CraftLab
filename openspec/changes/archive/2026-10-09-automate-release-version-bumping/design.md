# Design: Automate Release Version Bumping

## Context

CraftLab components currently define version strings independently across 7 distinct files:
- `CraftLab-backend/main.py`: `FastAPI(..., version="0.5.2")`
- `CraftLab-frontend/package.json`: `"version": "0.5.2"`
- `CraftLab-plugin/build.gradle.kts`: `version = "0.5.2"`
- `CraftLab-plugin/src/main/resources/plugin.yml`: `version: 0.5.2`
- `CraftLab-ctl/pyproject.toml`: `version = "0.3.3"`
- `CraftLab-ctl/src/craftlab_ctl/__init__.py`: `__version__ = "0.3.3"`
- `CraftLab-ctl/web/package.json`: `"version": "1.0.0"`
- `docs/metadata.yml`: `versions:` array (currently latest is `0.3.3`)

See [proposal.md](file:///c:/Users/antua/OneDrive/Documentos/Programming/MISC/MinecraftResourceManager/openspec/changes/automate-release-version-bumping/proposal.md) for background and motivation.

## Goals / Non-Goals

**Goals:**
- Provide a single, zero-dependency Python script (`scripts/bump_version.py`) operable from any shell (PowerShell, Bash, CI).
- Support semantic version increments (`--patch`, `--minor`, `--major`) and explicit versions (`0.6.0`).
- Provide non-destructive repository inspection (`--check`) and dry-run previewing (`--dry-run`).
- Ensure `docs/metadata.yml` is automatically updated according to the DarkBladeDev loader schema (`plugin-docs-versioning`), prepending the new version at `index 0` while preserving comments.
- Provide opt-in Git staging, committing, and tagging (`--commit`, `--tag`).
- Enforce strict safety: never execute `git push`.
- Provide a clear, comprehensive Agent Skill (`.agents/skills/release-versioning/SKILL.md`) in English guiding AI agents and human contributors on how to use the tool and when to avoid manual edits.
- Reconcile existing version drift (`craftlab-ctl` and `docs/metadata.yml`) to the unified baseline `0.5.2`.

**Non-Goals:**
- Automatic `git push` to remote repositories (must remain manual by the human operator).
- Automated PyPI / npm publish directly inside the bump script (releases are published via GitHub Actions when tags are pushed).
- Modifying runtime behavior or server protocol contracts.

## Decisions

### 1. Zero-Dependency Python Script (`scripts/bump_version.py`)
- **Rationale**: Python is already required across the project (backend and `craftlab-ctl`). Relying strictly on Python's standard library (`pathlib`, `re`, `json`, `datetime`, `subprocess`, `argparse`, `sys`) ensures the script runs immediately without activating virtualenvs, installing pip dependencies, or needing Node/npm.
- **Alternatives Considered**:
  - *Custom subprogram inside `craftctl`*: Requires `craftlab-ctl` installed in editable mode and complex bootstrap.
  - *Node/JS script (`npm run bump`)*: Requires `npm` and `node_modules` at repo root, which does not exist in this monorepo.

### 2. Format-Preserving Updates
- **Rationale**: Formats like `docs/metadata.yml` and `build.gradle.kts` contain structured comments and custom layout. Using a generic YAML parser (like PyYAML) strips comments and reorders keys.
- **Approach**:
  - `package.json`: Parsed with `json` or regex preserving 2-space indentation.
  - Python files (`main.py`, `__init__.py`): Targeted regex replacement matching `version="..."` and `__version__ = "..."`.
  - Gradle / Bukkit YAML: Targeted regex matching `version = "..."` and `version: ...`.
  - `docs/metadata.yml`: Targeted insertion directly beneath the `CURRENT VERSION (LATEST)` marker in the `versions:` block, generating the standard schema block without disturbing existing comments.

### 3. Git Automation Safety Boundary
- **Rationale**: Accidental pushes of release tags to GitHub trigger the live `release.yml` GitHub Action workflow, generating real releases prematurely.
- **Decision**:
  - `--commit` stages only the modified manifest files (`git add <files>`) and commits with message `chore(release): bump version to X.Y.Z`.
  - `--tag` creates an annotated tag `git tag -a vX.Y.Z -m "Release vX.Y.Z"`.
  - Pushing to remote is explicitly forbidden in code: no `git push` command is ever executed.

### 4. Dedicated Agent Skill (`release-versioning`)
- **Rationale**: AI agents frequently try to edit versions by guessing paths or modifying single files during feature work.
- **Decision**: Author `.agents/skills/release-versioning/SKILL.md` in English following the Antigravity skill structure with frontmatter, complete file inventory, trigger conditions ("When to Use"), anti-patterns ("When NOT to Use"), and recipes.

## Risks / Trade-offs

- **[Risk] Formatting corruption in `docs/metadata.yml`**
  - *Mitigation*: Unit test and verify regex/template block insertion against the existing `docs/metadata.yml` structure. Verify with `--dry-run` and validate against DarkBladeDev loader expectations.
- **[Risk] Uncommitted working tree when running with `--commit`**
  - *Mitigation*: Script checks `git status --porcelain`. If dirty files outside the manifest list exist, the script refuses to run `--commit` unless `--force` is explicitly provided.
- **[Risk] Malformed SemVer input**
  - *Mitigation*: Strict SemVer regex validation (`MAJOR.MINOR.PATCH[-PRERELEASE]`) before attempting any file writes.

## Migration Plan

1. Create `scripts/bump_version.py` and implement all CLI flags (`--check`, `--dry-run`, `--commit`, `--tag`, `--changelog`, semver increments).
2. Create `.agents/skills/release-versioning/SKILL.md` with comprehensive guidelines.
3. Execute `python scripts/bump_version.py --check` to verify inspection and drift detection.
4. Execute `python scripts/bump_version.py 0.5.2` (reconciliation mode) to align `craftlab-ctl` and `docs/metadata.yml` to the current repository version.
