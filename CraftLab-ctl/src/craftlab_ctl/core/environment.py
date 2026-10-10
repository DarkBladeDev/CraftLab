import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path
from typing import List, Optional
from craftlab_ctl.core.paths import CtlPaths


def find_venv_python(venv_dir: Path) -> Optional[Path]:
    if sys.platform == "win32":
        candidates = [
            venv_dir / "Scripts" / "python.exe",
            venv_dir / "python.exe",
        ]
    else:
        candidates = [
            venv_dir / "bin" / "python",
            venv_dir / "bin" / "python3",
        ]
    for c in candidates:
        if c.exists():
            return c
    return None


def is_venv_valid(venv_dir: Path) -> bool:
    if not venv_dir.exists() or not venv_dir.is_dir():
        return False
    py = find_venv_python(venv_dir)
    return py is not None and py.exists()


def provision_release_environment(
    paths: CtlPaths,
    release_dir: Path,
    requirements_file: Optional[Path] = None,
    offline_only: bool = False,
    timeout: float = 120.0,
) -> Path:
    """Create an isolated virtual environment inside release_dir using the shared wheel cache.
    
    Returns the path to the newly provisioned python executable.
    """
    venv_dir = release_dir / ".venv"
    if not is_venv_valid(venv_dir):
        # Create virtual environment
        try:
            builder = venv.EnvBuilder(with_pip=True, clear=True)
            builder.create(venv_dir)
        except Exception:
            # Fallback to subprocess invocation
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv_dir)],
                check=True,
                timeout=timeout,
            )

    py_exec = find_venv_python(venv_dir)
    if not py_exec:
        raise RuntimeError(f"Failed to locate python binary in virtual environment at {venv_dir}")

    # Determine requirements.txt location
    req_path = requirements_file
    if not req_path:
        cand1 = release_dir / "backend" / "requirements.txt"
        cand2 = release_dir / "requirements.txt"
        if cand1.exists():
            req_path = cand1
        elif cand2.exists():
            req_path = cand2

    paths.wheels_dir.mkdir(parents=True, exist_ok=True)

    # Sync bundled companion wheels from release_dir/wheels into shared wheel cache
    bundled_wheels_dir = release_dir / "wheels"
    if bundled_wheels_dir.exists():
        for whl in bundled_wheels_dir.glob("*.whl"):
            target_whl = paths.wheels_dir / whl.name
            if not target_whl.exists():
                shutil.copy2(whl, target_whl)

    if req_path and req_path.exists():
        # 1. Attempt fast install using only wheels in cache
        res_cached = subprocess.run(
            [
                str(py_exec),
                "-m",
                "pip",
                "install",
                "--no-index",
                "--find-links",
                str(paths.wheels_dir),
                "-r",
                str(req_path),
            ],
            capture_output=True,
            timeout=timeout,
        )

        if res_cached.returncode != 0 and not offline_only:
            # 2. Download missing wheels to cache
            subprocess.run(
                [
                    str(py_exec),
                    "-m",
                    "pip",
                    "wheel",
                    "-w",
                    str(paths.wheels_dir),
                    "-r",
                    str(req_path),
                ],
                capture_output=True,
                timeout=timeout,
            )
            # 3. Complete installation from wheel cache
            subprocess.run(
                [
                    str(py_exec),
                    "-m",
                    "pip",
                    "install",
                    "--find-links",
                    str(paths.wheels_dir),
                    "-r",
                    str(req_path),
                ],
                check=True,
                capture_output=True,
                timeout=timeout,
            )

    _ensure_companion_packages(paths, py_exec, release_dir=release_dir, offline_only=offline_only, timeout=timeout)

    return py_exec


def _ensure_companion_package(
    paths: CtlPaths,
    py_exec: Path,
    import_name: str,
    dist_name: str,
    wheel_glob: str,
    release_dir: Optional[Path] = None,
    src_dir: Optional[Path] = None,
    offline_only: bool = False,
    timeout: float = 120.0,
) -> None:
    # 1. Check if package is already importable
    check_res = subprocess.run(
        [str(py_exec), "-c", f"import {import_name}"],
        capture_output=True,
    )
    if check_res.returncode == 0:
        return

    # 2. Try installing from wheels_dir with --no-deps
    if paths.wheels_dir and paths.wheels_dir.exists():
        res = subprocess.run(
            [
                str(py_exec),
                "-m",
                "pip",
                "install",
                "--no-deps",
                "--no-index",
                "--find-links",
                str(paths.wheels_dir),
                dist_name,
            ],
            capture_output=True,
            timeout=timeout,
        )
        if res.returncode == 0:
            return

        # Direct wheel extraction fallback if pip fails
        whls = sorted(paths.wheels_dir.glob(wheel_glob), reverse=True)
        if whls:
            try:
                import zipfile
                sp_res = subprocess.run(
                    [str(py_exec), "-c", "import site; print(site.getsitepackages()[0])"],
                    capture_output=True,
                    text=True,
                )
                if sp_res.returncode == 0:
                    sp_dir = Path(sp_res.stdout.strip())
                    if sp_dir.exists():
                        with zipfile.ZipFile(whls[0], "r") as z:
                            z.extractall(sp_dir)
                        if subprocess.run([str(py_exec), "-c", f"import {import_name}"], capture_output=True).returncode == 0:
                            return
            except Exception:
                pass

    # 3. If source directory exists (dev / monorepo), build wheel or install
    if src_dir and src_dir.exists() and not offline_only:
        if paths.wheels_dir and paths.wheels_dir.exists():
            subprocess.run(
                [
                    str(py_exec),
                    "-m",
                    "pip",
                    "wheel",
                    "-w",
                    str(paths.wheels_dir),
                    "--no-deps",
                    str(src_dir),
                ],
                capture_output=True,
                timeout=timeout,
            )
            res = subprocess.run(
                [
                    str(py_exec),
                    "-m",
                    "pip",
                    "install",
                    "--no-deps",
                    "--find-links",
                    str(paths.wheels_dir),
                    dist_name,
                ],
                capture_output=True,
                timeout=timeout,
            )
            if res.returncode == 0:
                return

        subprocess.run(
            [str(py_exec), "-m", "pip", "install", "--no-deps", "-e", str(src_dir)],
            capture_output=True,
            timeout=timeout,
        )
        if subprocess.run([str(py_exec), "-c", f"import {import_name}"], capture_output=True).returncode == 0:
            return

    # 4. Fallback: Copy directly from release backend vendored folder into site-packages if available
    if release_dir:
        vendored_src = release_dir / "backend" / import_name
        if not vendored_src.exists():
            vendored_src = release_dir / import_name
        if vendored_src.exists() and vendored_src.is_dir():
            try:
                sp_res = subprocess.run(
                    [str(py_exec), "-c", "import site; print(site.getsitepackages()[0])"],
                    capture_output=True,
                    text=True,
                )
                if sp_res.returncode == 0:
                    sp_dir = Path(sp_res.stdout.strip())
                    if sp_dir.exists():
                        target_sp_pkg = sp_dir / import_name
                        if not target_sp_pkg.exists():
                            shutil.copytree(vendored_src, target_sp_pkg, dirs_exist_ok=True)
            except Exception:
                pass


def _ensure_companion_packages(
    paths: CtlPaths,
    py_exec: Path,
    release_dir: Optional[Path] = None,
    offline_only: bool = False,
    timeout: float = 120.0,
) -> None:
    # Packages in order of dependency: craftlab_security before craftlab_ctl
    packages = [
        {
            "import_name": "craftlab_security",
            "dist_name": "craftlab-security",
            "wheel_glob": "craftlab_security*.whl",
            "src_dir": paths.home / "packages" / "craftlab_security",
        },
        {
            "import_name": "craftlab_ctl",
            "dist_name": "craftlab-ctl",
            "wheel_glob": "craftlab_ctl*.whl",
            "src_dir": paths.home / "CraftLab-ctl",
        },
    ]

    # Discover any extra monorepo packages in paths.home / "packages"
    packages_dir = paths.home / "packages"
    if packages_dir.exists():
        for p in sorted(packages_dir.iterdir()):
            if p.is_dir() and (p / "pyproject.toml").exists():
                pkg_name = p.name.replace("-", "_")
                if not any(item["import_name"] == pkg_name for item in packages):
                    packages.insert(
                        0,
                        {
                            "import_name": pkg_name,
                            "dist_name": p.name,
                            "wheel_glob": f"{pkg_name}*.whl",
                            "src_dir": p,
                        },
                    )

    for pkg_spec in packages:
        _ensure_companion_package(
            paths=paths,
            py_exec=py_exec,
            import_name=pkg_spec["import_name"],
            dist_name=pkg_spec["dist_name"],
            wheel_glob=pkg_spec["wheel_glob"],
            release_dir=release_dir,
            src_dir=pkg_spec["src_dir"],
            offline_only=offline_only,
            timeout=timeout,
        )


def _ensure_craftlab_ctl(
    paths: CtlPaths,
    py_exec: Path,
    offline_only: bool = False,
    timeout: float = 120.0,
) -> None:
    """Backward compatibility alias for _ensure_companion_packages."""
    _ensure_companion_packages(paths, py_exec, offline_only=offline_only, timeout=timeout)
