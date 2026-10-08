import os
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

    if req_path and req_path.exists():
        paths.wheels_dir.mkdir(parents=True, exist_ok=True)
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

    _ensure_craftlab_ctl(paths, py_exec, offline_only=offline_only, timeout=timeout)

    return py_exec


def _ensure_craftlab_ctl(
    paths: CtlPaths,
    py_exec: Path,
    offline_only: bool = False,
    timeout: float = 120.0,
) -> None:
    # 1. Check if craftlab_ctl is already importable
    check_res = subprocess.run(
        [str(py_exec), "-c", "import craftlab_ctl"],
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
                "craftlab-ctl",
            ],
            capture_output=True,
            timeout=timeout,
        )
        if res.returncode == 0:
            return

        # Direct wheel extraction fallback if pip fails
        whls = list(paths.wheels_dir.glob("craftlab_ctl*.whl"))
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
                        return
            except Exception:
                pass

    # 3. If source CraftLab-ctl exists (dev / monorepo), build and install
    src_ctl = paths.home / "CraftLab-ctl"
    if src_ctl.exists() and not offline_only:
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
                    str(src_ctl),
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
                    "craftlab-ctl",
                ],
                capture_output=True,
                timeout=timeout,
            )
            if res.returncode == 0:
                return

        subprocess.run(
            [str(py_exec), "-m", "pip", "install", "--no-deps", "-e", str(src_ctl)],
            capture_output=True,
            timeout=timeout,
        )
