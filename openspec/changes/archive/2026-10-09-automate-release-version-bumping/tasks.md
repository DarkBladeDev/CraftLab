# Tasks

## 1. Core Version Bumping CLI Tool (`scripts/bump_version.py`)

- [x] 1.1 Implement SemVer parsing, increment arithmetic (`--patch`, `--minor`, `--major`, explicit version argument), and CLI argument parser using Python standard library (`argparse`, `re`, `pathlib`). Verify with `python scripts/bump_version.py --help`.
- [x] 1.2 Implement repository inspection mode (`--check`) scanning all 7 manifests (`CraftLab-backend/main.py`, `CraftLab-frontend/package.json`, `CraftLab-plugin/build.gradle.kts`, `CraftLab-plugin/src/main/resources/plugin.yml`, `CraftLab-ctl/pyproject.toml`, `CraftLab-ctl/src/craftlab_ctl/__init__.py`, `CraftLab-ctl/web/package.json`) and reporting version consistency. Verify by executing `python scripts/bump_version.py --check` and observing the detected drift.
- [x] 1.3 Implement atomic manifest updates and `--dry-run` diff preview for Python, JSON, Gradle, and Bukkit YAML manifests. Verify with `python scripts/bump_version.py --dry-run --patch`.
- [x] 1.4 Implement `docs/metadata.yml` DarkBladeDev loader integration (prepending version at index 0 under `versions:` with `releaseDate`, `reference`, `downloadUrl`, `changelog`, and `minecraft` array). Verify YAML structure complies with `plugin-docs-versioning`.
- [x] 1.5 Implement Git automation options (`--commit`, `--tag`) with working-tree safety validation, staging only modified release manifests and guaranteeing zero automatic remote pushes. Verify flags and error handling when untracked dirty files are present.

## 2. Agent Skill Documentation

- [x] 2.1 Author `.agents/skills/release-versioning/SKILL.md` in English including YAML frontmatter, 7-manifest inventory, triggers ("When to Use"), guardrails ("When NOT to Use"), and CLI recipes. Verify that file exists and renders properly.

## 3. Monorepo Baseline Reconciliation & End-to-End Verification

- [x] 3.1 Execute `python scripts/bump_version.py 0.5.2` to reconcile `craftlab-ctl` and `docs/metadata.yml` with Core `0.5.2`. Verify that `python scripts/bump_version.py --check` confirms all components are in sync at `0.5.2`.
- [x] 3.2 Execute automated verification runs (backend `pytest`, frontend `npm run build`, plugin `./gradlew test`) to confirm no build regression was introduced.
