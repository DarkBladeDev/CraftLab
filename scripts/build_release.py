#!/usr/bin/env python3
"""Build and package CraftLab release distribution archives.

Generates:
- craftlab-v<version>.tar.gz
- craftlab-v<version>.tar.gz.sha256
- manifest.json inside archive
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def compute_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_git_commit(repo_root: Path) -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "unknown"


def build_frontend_bundle(frontend_dir: Path) -> None:
    print(f"[*] Building frontend SPA at {frontend_dir}...")
    # Try npm run build
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    try:
        subprocess.run([npm_cmd, "run", "build"], cwd=frontend_dir, check=True)
    except Exception as e:
        dist_index = frontend_dir / "dist" / "index.html"
        if dist_index.exists():
            print(f"[!] Warning: npm build failed ({e}), but frontend/dist exists. Using existing dist.")
        else:
            raise RuntimeError(f"Failed to build frontend and dist/index.html is missing: {e}")


def copy_backend_files(src_backend: Path, dest_backend: Path) -> None:
    dest_backend.mkdir(parents=True, exist_ok=True)
    
    # Copy main.py
    main_py = src_backend / "main.py"
    if main_py.exists():
        shutil.copy2(main_py, dest_backend / "main.py")
        
    # Copy requirements.txt
    req_txt = src_backend / "requirements.txt"
    if req_txt.exists():
        shutil.copy2(req_txt, dest_backend / "requirements.txt")
        
    # Copy app/
    src_app = src_backend / "app"
    dest_app = dest_backend / "app"
    if src_app.exists():
        shutil.copytree(
            src_app,
            dest_app,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".pytest_cache"),
            dirs_exist_ok=True,
        )

    # Vendor craftlab_ctl package directly into backend so release is hermetic
    src_ctl = src_backend.parent / "CraftLab-ctl" / "src" / "craftlab_ctl"
    if src_ctl.exists():
        dest_ctl = dest_backend / "craftlab_ctl"
        shutil.copytree(
            src_ctl,
            dest_ctl,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
            dirs_exist_ok=True,
        )


def build_release_manifest(
    version: str,
    git_commit: str,
    requires_craftctl: str = ">=0.1.0",
    requires_python: str = ">=3.11",
    database_version: int = 1,
    checksums: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    norm_version = version.lstrip("v")
    return {
        "name": "craftlab",
        "version": norm_version,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_commit,
        "requires_craftctl": requires_craftctl,
        "requires_python": requires_python,
        "database_version": database_version,
        "checksums": checksums or {},
    }


def create_release_package(
    repo_root: Path,
    version: str,
    output_dir: Path,
    skip_frontend_build: bool = False,
    git_commit: Optional[str] = None,
) -> Path:
    norm_version = version.lstrip("v")
    commit = git_commit or get_git_commit(repo_root)
    output_dir.mkdir(parents=True, exist_ok=True)

    frontend_dir = repo_root / "CraftLab-frontend"
    if not frontend_dir.exists():
        frontend_dir = repo_root / "frontend"
    frontend_dist = frontend_dir / "dist"
    if not skip_frontend_build:
        build_frontend_bundle(frontend_dir)
    elif not (frontend_dist / "index.html").exists():
        raise RuntimeError(f"skip_frontend_build was specified, but {frontend_dist / 'index.html'} does not exist.")

    with tempfile.TemporaryDirectory() as tmp_dir:
        staging_dir = Path(tmp_dir) / f"craftlab-v{norm_version}"
        staging_dir.mkdir(parents=True)

        # 1. Backend
        dest_backend = staging_dir / "backend"
        backend_dir = repo_root / "CraftLab-backend"
        if not backend_dir.exists():
            backend_dir = repo_root / "backend"
        copy_backend_files(backend_dir, dest_backend)

        # 2. Frontend dist
        dest_frontend = staging_dir / "frontend_dist"
        shutil.copytree(frontend_dist, dest_frontend, dirs_exist_ok=True)

        # 3. Control Panel Web dist (if present)
        ctl_web_dir = repo_root / "CraftLab-ctl" / "web" / "dist"
        if ctl_web_dir.exists() and (ctl_web_dir / "index.html").exists():
            dest_ctl_web = staging_dir / "ctl_web_dist"
            shutil.copytree(ctl_web_dir, dest_ctl_web, dirs_exist_ok=True)

        # 3. Compute component checksums for manifest
        checksums = {}
        for root, _, files in os.walk(staging_dir):
            for file in sorted(files):
                full_path = Path(root) / file
                rel_path = full_path.relative_to(staging_dir).as_posix()
                checksums[rel_path] = compute_sha256(full_path)

        # 4. Write manifest.json
        manifest_data = build_release_manifest(
            version=norm_version,
            git_commit=commit,
            checksums=checksums,
        )
        manifest_file = staging_dir / "manifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)

        # 5. Archive to tar.gz
        tar_filename = f"craftlab-v{norm_version}.tar.gz"
        tar_path = output_dir / tar_filename
        print(f"[*] Packaging into {tar_path}...")
        with tarfile.open(tar_path, "w:gz") as tar:
            for item in staging_dir.iterdir():
                tar.add(item, arcname=item.name)

        # 6. Generate .sha256 checksum file
        archive_sha = compute_sha256(tar_path)
        sha_file = output_dir / f"{tar_filename}.sha256"
        with open(sha_file, "w", encoding="utf-8") as f:
            f.write(f"{archive_sha}  {tar_filename}\n")

        print(f"[+] Successfully built {tar_filename} (SHA256: {archive_sha[:16]}...)")
        print(f"[+] Checksum written to {sha_file}")

        # 7. Build CraftLab-ctl wheel for companion installation
        ctl_dir = repo_root / "CraftLab-ctl"
        if ctl_dir.exists() and (ctl_dir / "pyproject.toml").exists():
            print("[*] Building companion craftlab-ctl wheel...")
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "wheel", "-w", str(output_dir), "--no-deps", str(ctl_dir)],
                    check=True,
                    capture_output=True,
                )
                wheels_cache = repo_root / "cache" / "wheels"
                if wheels_cache.exists():
                    for whl in output_dir.glob("craftlab_ctl*.whl"):
                        shutil.copy2(whl, wheels_cache / whl.name)
            except Exception as e:
                print(f"[!] Warning: failed to build craftlab-ctl wheel: {e}")

        return tar_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build CraftLab release archive.")
    parser.add_argument("--version", required=True, help="Release version (e.g. 1.0.0 or v1.0.0)")
    parser.add_argument("--output-dir", default="dist/releases", help="Output directory for release archives")
    parser.add_argument("--skip-frontend", action="store_true", help="Skip running npm build (uses existing dist)")
    parser.add_argument("--git-commit", default=None, help="Explicit git commit SHA")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = repo_root / output_dir

    create_release_package(
        repo_root=repo_root,
        version=args.version,
        output_dir=output_dir,
        skip_frontend_build=args.skip_frontend,
        git_commit=args.git_commit,
    )


if __name__ == "__main__":
    main()
