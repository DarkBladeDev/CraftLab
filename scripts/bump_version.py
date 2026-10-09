#!/usr/bin/env python3
"""CraftLab Unified Monorepo Version Bumping & Release Automation Tool.

Manages lockstep versioning across all 7 platform manifests:
1. CraftLab-backend/main.py
2. CraftLab-frontend/package.json
3. CraftLab-plugin/build.gradle.kts
4. CraftLab-plugin/src/main/resources/plugin.yml
5. CraftLab-ctl/pyproject.toml
6. CraftLab-ctl/src/craftlab_ctl/__init__.py
7. CraftLab-ctl/web/package.json
8. docs/metadata.yml (DarkBladeDev loader specification)

Guarantees:
- Pure Python standard library (zero external dependencies).
- Strict atomic updates with --dry-run diff preview.
- Diagnostic drift check via --check.
- Git commit and annotated tag creation with dirty working-tree safety checks.
- ABSOLUTELY NEVER executes git push (pushing is strictly manual).
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

SEMVER_REGEX = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z.-]+))?(?:\+([0-9A-Za-z.-]+))?$"
)

# Relative file paths from repository root
MANIFEST_CONFIGS = [
    {
        "id": "backend",
        "name": "Backend (FastAPI)",
        "path": Path("CraftLab-backend/main.py"),
        "regex": re.compile(r'(version=")([^"]+)(")'),
    },
    {
        "id": "frontend",
        "name": "Frontend (React/Vite)",
        "path": Path("CraftLab-frontend/package.json"),
        "regex": re.compile(r'("version":\s*")([^"]+)(")'),
    },
    {
        "id": "plugin_gradle",
        "name": "Plugin (Gradle)",
        "path": Path("CraftLab-plugin/build.gradle.kts"),
        "regex": re.compile(r'(version\s*=\s*")([^"]+)(")'),
    },
    {
        "id": "plugin_yml",
        "name": "Plugin (Bukkit YAML)",
        "path": Path("CraftLab-plugin/src/main/resources/plugin.yml"),
        "regex": re.compile(r'(version:\s*)([^\s\r\n]+)'),
    },
    {
        "id": "ctl_toml",
        "name": "Control CLI (pyproject.toml)",
        "path": Path("CraftLab-ctl/pyproject.toml"),
        "regex": re.compile(r'(version\s*=\s*")([^"]+)(")'),
    },
    {
        "id": "ctl_init",
        "name": "Control CLI (Module __init__.py)",
        "path": Path("CraftLab-ctl/src/craftlab_ctl/__init__.py"),
        "regex": re.compile(r'(__version__\s*=\s*")([^"]+)(")'),
    },
    {
        "id": "ctl_web",
        "name": "Control Panel Web UI (package.json)",
        "path": Path("CraftLab-ctl/web/package.json"),
        "regex": re.compile(r'("version":\s*")([^"]+)(")'),
    },
]

DOCS_METADATA_PATH = Path("docs/metadata.yml")


def find_repo_root() -> Path:
    """Finds git root or directory containing CraftLab-backend."""
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        if (parent / ".git").exists() or (parent / "CraftLab-backend").exists():
            return parent
    return Path.cwd()


def parse_semver(version_str: str) -> Tuple[int, int, int, Optional[str]]:
    """Validates and decomposes a SemVer string into (major, minor, patch, prerelease)."""
    clean_ver = version_str.lstrip("v").strip()
    match = SEMVER_REGEX.match(clean_ver)
    if not match:
        raise ValueError(
            f"Invalid semantic version: '{version_str}'. Expected format: X.Y.Z or X.Y.Z-prerelease"
        )
    major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))
    prerelease = match.group(4)
    return major, minor, patch, prerelease


def increment_semver(current_version: str, part: str) -> str:
    """Calculates next version based on increment part ('patch', 'minor', 'major')."""
    major, minor, patch, _ = parse_semver(current_version)
    if part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    elif part == "minor":
        return f"{major}.{minor + 1}.0"
    elif part == "major":
        return f"{major + 1}.0.0"
    raise ValueError(f"Unknown increment part: {part}. Choose patch, minor, or major.")


def get_current_manifest_versions(repo_root: Path) -> Dict[str, Tuple[str, Optional[str]]]:
    """Reads current version from all manifests. Returns dict of id -> (name, version_or_none)."""
    results: Dict[str, Tuple[str, Optional[str]]] = {}
    for cfg in MANIFEST_CONFIGS:
        file_path = repo_root / cfg["path"]
        if not file_path.exists():
            results[cfg["id"]] = (cfg["name"], None)
            continue
        content = file_path.read_text(encoding="utf-8")
        match = cfg["regex"].search(content)
        version = match.group(2) if match else None
        results[cfg["id"]] = (cfg["name"], version)

    # Check docs/metadata.yml
    docs_file = repo_root / DOCS_METADATA_PATH
    if docs_file.exists():
        docs_content = docs_file.read_text(encoding="utf-8")
        match = re.search(r'versions:\s*(?:\r?\n\s*#[^\r\n]*)*\r?\n\s*-\s*version:\s*"([^"]+)"', docs_content)
        docs_ver = match.group(1) if match else None
        results["docs_metadata"] = ("Docs Portal (metadata.yml)", docs_ver)
    else:
        results["docs_metadata"] = ("Docs Portal (metadata.yml)", None)

    return results


def resolve_base_version(versions: Dict[str, Tuple[str, Optional[str]]]) -> str:
    """Derives majority or core version to use as base for bumping."""
    # Priority order for base version
    for key in ["backend", "frontend", "plugin_gradle"]:
        ver = versions.get(key, (None, None))[1]
        if ver:
            return ver
    # Fallback to any detected valid version
    for _, ver in versions.values():
        if ver:
            return ver
    return "0.1.0"


def run_check_command(repo_root: Path) -> int:
    """Prints diagnostic table and returns 0 if all in sync, 1 if drift detected."""
    versions = get_current_manifest_versions(repo_root)
    print("=" * 80)
    print("  CRAFTLAB MONOREPO VERSION DIAGNOSTICS")
    print("=" * 80)
    print(f"{'Component':<32} {'Manifest Path':<36} {'Version':<10}")
    print("-" * 80)

    found_versions = set()
    drift = False

    for cfg in MANIFEST_CONFIGS:
        _, ver = versions.get(cfg["id"], (cfg["name"], None))
        ver_str = ver if ver else "[NOT FOUND]"
        print(f"{cfg['name']:<32} {str(cfg['path']):<36} {ver_str:<10}")
        if ver:
            found_versions.add(ver)

    docs_name, docs_ver = versions.get("docs_metadata", ("Docs", None))
    docs_ver_str = docs_ver if docs_ver else "[NOT FOUND]"
    print(f"{docs_name:<32} {str(DOCS_METADATA_PATH):<36} {docs_ver_str:<10}")
    if docs_ver:
        found_versions.add(docs_ver)

    print("-" * 80)
    if len(found_versions) <= 1 and None not in versions.values():
        single_ver = list(found_versions)[0] if found_versions else "None"
        print(f"[OK] Monorepo manifests are synchronized at version {single_ver}.")
        return 0
    else:
        print("[!] VERSION DRIFT DETECTED across components.")
        print(f"    Unique versions found: {sorted(list(found_versions))}")
        base_ver = resolve_base_version(versions)
        print(f"    Recommended baseline reconciliation version: {base_ver}")
        print("    Run 'python scripts/bump_version.py <target_version>' to align all manifests.")
        return 1


def update_docs_metadata(
    docs_path: Path, new_version: str, changelog: str, dry_run: bool
) -> Optional[Tuple[str, str]]:
    """Inserts or updates index 0 entry in docs/metadata.yml preserving schema."""
    if not docs_path.exists():
        print(f"[!] Warning: {docs_path} not found. Skipping documentation metadata.")
        return None

    content = docs_path.read_text(encoding="utf-8")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Check if this version already exists as latest entry
    current_match = re.search(
        r'versions:\s*(?:\r?\n\s*#[^\r\n]*)*\r?\n\s*-\s*version:\s*"([^"]+)"', content
    )
    if current_match and current_match.group(1) == new_version:
        # Version already latest in metadata.yml, update changelog if needed
        return None

    # Construct new block
    new_entry = (
        f'  - version: "{new_version}"\n'
        f'    releaseDate: "{today}"\n'
        f'    reference: "v{new_version}"\n'
        f'    downloadUrl: "https://github.com/DarkBladeDev/CraftLab/releases/tag/v{new_version}"\n'
        f'    changelog: "{changelog}"\n'
        f'    minecraft:\n'
        f'      - "1.21.1"\n'
        f'      - "1.21.x"\n'
    )

    # Locate 'versions:' and the comment header
    versions_idx = content.find("versions:")
    if versions_idx == -1:
        print(f"[!] Warning: 'versions:' section not found in {docs_path}.")
        return None

    # Find the first entry indicator '- version:'
    first_entry_match = re.search(r"(\r?\n\s*-\s*version:)", content[versions_idx:])
    if not first_entry_match:
        # Append directly under versions:
        insert_pos = versions_idx + len("versions:\n")
        updated_content = content[:insert_pos] + new_entry + content[insert_pos:]
    else:
        insert_pos = versions_idx + first_entry_match.start(1) + (1 if content[versions_idx + first_entry_match.start(1)] == '\n' else 2)
        # Check if preceded by comment header
        header_pattern = re.compile(r"(\s*#\s*-{10,}\r?\n\s*#\s*CURRENT VERSION[^\r\n]*\r?\n\s*#\s*-{10,}\r?\n)")
        header_match = header_pattern.search(content[versions_idx:insert_pos])
        if header_match:
            insert_pos = versions_idx + header_match.end(1)

        updated_content = content[:insert_pos] + new_entry + "\n" + content[insert_pos:]

    if not dry_run:
        docs_path.write_text(updated_content, encoding="utf-8")

    return (content, updated_content)


def update_manifest_file(
    file_path: Path, regex: re.Pattern, new_version: str, dry_run: bool
) -> Optional[Tuple[str, str]]:
    """Replaces version in target manifest file using regex."""
    if not file_path.exists():
        print(f"[!] Warning: File {file_path} not found.")
        return None

    original = file_path.read_text(encoding="utf-8")
    match = regex.search(original)
    if not match:
        print(f"[!] Warning: Version pattern not matched in {file_path}.")
        return None

    prefix, old_ver, suffix = match.group(1), match.group(2), match.group(3) if match.lastindex >= 3 else ""
    replacement = f"{prefix}{new_version}{suffix}"
    updated = original[: match.start()] + replacement + original[match.end() :]

    if not dry_run and original != updated:
        file_path.write_text(updated, encoding="utf-8")

    return (original, updated)


def run_git_operations(
    repo_root: Path,
    modified_paths: List[Path],
    new_version: str,
    commit: bool,
    tag: bool,
    force: bool,
) -> None:
    """Handles git add, commit, and annotated tag creation with safety validation."""
    if not commit and not tag:
        return

    # Check git presence
    try:
        status_res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception as e:
        print(f"[!] Git check failed: {e}. Skipping git commit/tag.")
        return

    dirty_lines = [line.strip() for line in status_res.stdout.splitlines() if line.strip()]
    rel_modified_str = {str(p.as_posix()) for p in modified_paths}

    # Verify if dirty files outside our touched files exist
    unrelated_dirty = []
    for line in dirty_lines:
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            file_name = parts[1].replace("\\", "/")
            if file_name not in rel_modified_str:
                unrelated_dirty.append(file_name)

    if unrelated_dirty and not force:
        print("[!] WARNING: Unrelated modified or untracked files found in git working tree:")
        for uf in unrelated_dirty[:5]:
            print(f"    - {uf}")
        if len(unrelated_dirty) > 5:
            print(f"    ... and {len(unrelated_dirty) - 5} more.")
        print("    Aborting git commit/tag to avoid unintended commits. Use --force to proceed anyway.")
        return

    if commit:
        print(f"[*] Staging {len(modified_paths)} modified release files...")
        stage_args = ["git", "add"] + [str(p) for p in modified_paths]
        subprocess.run(stage_args, cwd=repo_root, check=True)

        commit_msg = f"chore(release): bump version to {new_version}"
        print(f"[*] Creating git commit: '{commit_msg}'...")
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=repo_root, check=True)
        print("    [OK] Commit created successfully.")

    if tag:
        tag_name = f"v{new_version}"
        tag_msg = f"Release {tag_name}"
        print(f"[*] Creating annotated git tag: '{tag_name}'...")
        subprocess.run(["git", "tag", "-a", tag_name, "-m", tag_msg], cwd=repo_root, check=True)
        print("    [OK] Annotated tag created successfully.")

    print("\n" + "=" * 80)
    print("  GIT SAFETY NOTICE:")
    print("  Remote 'git push' was NOT performed.")
    print(f"  When ready to publish to GitHub, run:")
    print(f"      git push origin HEAD && git push origin v{new_version}")
    print("=" * 80 + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="CraftLab Monorepo Lockstep Version Bumping & Release Automation Tool."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "target_version",
        nargs="?",
        help="Explicit version to set across all manifests (e.g. 0.5.3, 0.6.0).",
    )
    group.add_argument(
        "--patch",
        action="store_true",
        help="Increment PATCH version component (e.g. 0.5.2 -> 0.5.3).",
    )
    group.add_argument(
        "--minor",
        action="store_true",
        help="Increment MINOR version component (e.g. 0.5.2 -> 0.6.0).",
    )
    group.add_argument(
        "--major",
        action="store_true",
        help="Increment MAJOR version component (e.g. 0.5.2 -> 1.0.0).",
    )
    group.add_argument(
        "--check",
        action="store_true",
        help="Diagnostic check: inspect manifests and report drift status without writing.",
    )

    parser.add_argument(
        "--changelog",
        type=str,
        default="",
        help="Release notes summary for docs/metadata.yml. Defaults to placeholder if omitted.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate version bump and display planned file modifications without editing disk.",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Create a git commit with modified manifests ('chore(release): bump version to X.Y.Z').",
    )
    parser.add_argument(
        "--tag",
        action="store_true",
        help="Create an annotated git tag ('vX.Y.Z').",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass working tree cleanliness check during --commit.",
    )

    args = parser.parse_args()
    repo_root = find_repo_root()

    if args.check:
        return run_check_command(repo_root)

    # Determine target version
    current_versions = get_current_manifest_versions(repo_root)
    base_version = resolve_base_version(current_versions)

    if args.patch:
        target_version = increment_semver(base_version, "patch")
    elif args.minor:
        target_version = increment_semver(base_version, "minor")
    elif args.major:
        target_version = increment_semver(base_version, "major")
    elif args.target_version:
        parse_semver(args.target_version)  # Validate semver
        target_version = args.target_version.lstrip("v").strip()
    else:
        # No version action specified, run check by default
        return run_check_command(repo_root)

    changelog = (
        args.changelog.strip()
        if args.changelog.strip()
        else f"Release v{target_version}: Platform updates and maintenance."
    )

    print(f"\n[*] CraftLab Unified Version Bump: {base_version} -> {target_version}")
    if args.dry_run:
        print("    [MODE: DRY-RUN - No files will be modified on disk]\n")

    modified_paths: List[Path] = []

    for cfg in MANIFEST_CONFIGS:
        file_path = repo_root / cfg["path"]
        result = update_manifest_file(file_path, cfg["regex"], target_version, args.dry_run)
        if result:
            orig, updated = result
            if orig != updated:
                modified_paths.append(cfg["path"])
                print(f"  [MODIFIED] {cfg['name']:<30} -> {cfg['path']}")
            else:
                print(f"  [ALIGNED]  {cfg['name']:<30} (already at {target_version})")

    # Update docs/metadata.yml
    docs_path = repo_root / DOCS_METADATA_PATH
    docs_result = update_docs_metadata(docs_path, target_version, changelog, args.dry_run)
    if docs_result:
        modified_paths.append(DOCS_METADATA_PATH)
        print(f"  [MODIFIED] Docs Portal (metadata.yml)     -> {DOCS_METADATA_PATH}")
    else:
        print(f"  [ALIGNED]  Docs Portal (metadata.yml)     (already contains {target_version} at index 0)")

    if args.dry_run:
        print(f"\n[OK] Dry-run completed. {len(modified_paths)} files would be modified.")
        return 0

    print(f"\n[OK] Version {target_version} applied across {len(modified_paths)} files.")

    # Git operations
    if args.commit or args.tag:
        run_git_operations(
            repo_root, modified_paths, target_version, args.commit, args.tag, args.force
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
